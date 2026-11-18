"""Clean OCR slips in instruments converted from the printed edition, with an independent reading as the check.

usage: python3 tools/ocr/fix_ocr_slips.py --scans <scans folder> [--apply]
1. Cyrillic look-alike letters inside Latin text ("(с)" for "(c)") are mapped to the Latin letter.
2. A rare word not in the dictionary (e.g. "specitied") is replaced by the dictionary word it was read from, ONLY
   when the first-pass OCR of the same pages (an independent reading) contains that word in the same context.
3. A paragraph that is mostly unknown words is replaced by the first-pass reading of the same passage when that
   reading is clean (>= 92% known words) and about as long; otherwise it is left and listed.
Every change is written to data/salam/ocr-corrections.json (instrument, provision, before, after, how). Without --apply
nothing is changed. The instruments stay Unverified.
"""
import collections, difflib, glob, json, os, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
args = sys.argv[1:]; SC = Path(args[args.index("--scans") + 1]); APPLY = "--apply" in args
HOMO = {"а":"a","в":"b","с":"c","е":"e","і":"i","ї":"i","ј":"j","к":"k","м":"m","н":"h","о":"o","р":"p","ѕ":"s","т":"t","у":"y","х":"x",
        "А":"A","В":"B","С":"C","Е":"E","І":"I","К":"K","М":"M","Н":"H","О":"O","Р":"P","Т":"T","Х":"X","Ү":"Y","ү":"y"}
words = set(w.strip().lower() for w in open("/usr/share/dict/words"))
FN = re.compile(r"\{fn:[^}]+\}")
def known(w):
    w = w.lower(); return (w in words or w.rstrip("s") in words or w[:-2] in words or w[:-3] in words or w[:-1] in words
                           or (w.endswith("ies") and w[:-3] + "y" in words))
book = [c["id"] for c in json.load(open(ROOT / "data/salam/conversions.json"))["instruments"] if not c.get("hold")]
lib = collections.Counter()
for f in glob.glob(str(ROOT / "data/acts/*.json")):
    if os.path.basename(f)[:-5] in book: continue
    a = json.load(open(f))
    for p in a["parts"]:
        for s in p["sections"]:
            for w in re.findall(r"[A-Za-z]{3,}", FN.sub("", s["title"] + " " + " ".join(s["text"]))): lib[w.lower()] += 1
vocab = set(w for w, c in lib.items() if c >= 5) | words
log = []
def first_pass(i):
    pf = ROOT / "data/salam/pages" / f"{i}.json"
    if not pf.exists(): return ""
    return " ".join((SC / "_ocr text" / p["file"] / f"p{p['scan']:04d}.txt").read_text() for p in json.load(open(pf))["scans"]
                    if (SC / "_ocr text" / p["file"] / f"p{p['scan']:04d}.txt").exists())
def norm(t): return re.sub(r"\s+", " ", t)
counts = collections.Counter()
for i in book:
    f = ROOT / "data/acts" / f"{i}.json"
    if not f.exists(): continue
    act = json.load(open(f)); raw = norm(first_pass(i)); rawl = raw.lower(); changed = False
    allw = collections.Counter(w.lower() for p in act["parts"] for s in p["sections"] for t in s["text"] for w in re.findall(r"[A-Za-z]{3,}", FN.sub("", t)))
    for part in act["parts"]:
        for s in part["sections"]:
            for k, t in enumerate(s["text"]):
                new = t
                # 1. look-alike letters
                if re.search(r"[Ѐ-ӿ]", new):
                    new2 = "".join(HOMO.get(ch, ch) for ch in new)
                    if new2 != new: log.append({"id": i, "no": s["no"], "how": "look-alike letters", "before": new[:90], "after": new2[:90]}); counts["homoglyph"] += 1; new = new2
                # 2. rare unknown words confirmed by the independent reading
                for m in list(re.finditer(r"[A-Za-z]{4,}", FN.sub("", new))):
                    w = m.group(0)
                    if known(w) or lib[w.lower()] >= 3 or allw[w.lower()] > 2: continue
                    cands = [c for c in difflib.get_close_matches(w.lower(), vocab, n=4, cutoff=0.8) if c != w.lower() and abs(len(c) - len(w)) <= 2 and c[0] == w.lower()[0]]
                    pre = norm(FN.sub("", new[max(0, m.start() - 40):m.start()])).split()[-1:] ; post = norm(FN.sub("", new[m.end():m.end() + 40])).split()[:1]
                    for c in cands:
                        ctx = " ".join([x.lower() for x in pre] + [c] + [x.lower() for x in post])
                        if len(ctx.split()) >= 2 and ctx in rawl:
                            fixed = re.sub(rf"\b{re.escape(w)}\b", c if w.islower() else c.capitalize() if w[0].isupper() else c, new, count=1)
                            log.append({"id": i, "no": s["no"], "how": "confirmed by the independent reading", "before": w, "after": fixed[m.start():m.start() + len(c) + 1].strip()[:40]}); counts["word"] += 1; new = fixed; break
                # 3. garbled paragraph
                ws = re.findall(r"[A-Za-z]{3,}", FN.sub("", new))
                if len(ws) >= 6 and sum(1 for w in ws if not known(w) and lib[w.lower()] < 3) / len(ws) >= 0.15:
                    key = [w.lower() for w in ws if known(w)]
                    if len(key) >= 6:
                        a1, a2 = key[:3], key[-3:]
                        i1 = rawl.find(" ".join(a1)); i2 = rawl.find(" ".join(a2), i1 + 1) if i1 >= 0 else -1
                        if i1 >= 0 and i2 > i1:
                            cand = raw[i1:i2 + len(" ".join(a2))]
                            cw = re.findall(r"[A-Za-z]{3,}", cand)
                            if cw and sum(1 for w in cw if known(w) or lib[w.lower()] >= 3) / len(cw) >= 0.92 and 0.7 <= len(cand) / max(1, len(new)) <= 1.4:
                                prefix = re.match(r"^(>*)", new).group(1)
                                log.append({"id": i, "no": s["no"], "how": "garbled paragraph replaced by the clean independent reading", "before": new[:110], "after": cand[:110]}); counts["paragraph"] += 1; new = prefix + cand
                if new != t: s["text"][k] = new; changed = True
    if changed and APPLY: json.dump(act, open(f, "w"), indent=2, ensure_ascii=False)
print(dict(counts), "changes", "(applied)" if APPLY else "(dry run)")
for l in log[:70]: print(f"  {l['id'][:30]:30} {l['no']:>4} {l['how'][:22]:22} {l['before'][:48]!r} -> {l['after'][:48]!r}")
if APPLY:
    p = ROOT / "data/salam/ocr-corrections.json"; old = json.load(open(p)) if p.exists() else []
    json.dump(old + log, open(p, "w"), indent=1, ensure_ascii=False)
