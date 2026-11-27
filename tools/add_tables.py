#!/usr/bin/env python3
"""Turn tables already in an instrument's text into real tables, without changing any words.

usage: python3 tools/add_tables.py <id> [<id> ...] [--apply] [--all]
For each ruled table the PDF has (strict filter: tabular, not margin notes or boxes), the table's words must appear as one
unbroken run of whole paragraphs of a provision, in the same order; only then are those paragraphs replaced by the table's
rows. Tables whose words do not line up (read in another order, mixed with other text, footnote marks inside) are listed
and left as text. Dry run unless --apply. Re-run `npm run build` afterwards (the AI search vectors use the same words, so
`cd tools/ai && node make_vectors.mjs` only has to redo the changed passages).
"""
import fitz, re, sys, json
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_tables import find_tables, row_strings

ROOT = Path(__file__).resolve().parent.parent
W = lambda s: re.findall(r"[^\W_]+", re.sub(r"\{fn:[^}]*\}", "", s).lower())


def process(iid, apply):
    man = json.loads((ROOT / "sources/manifest.json").read_text())
    man = man if isinstance(man, list) else man.get("instruments", list(man.values()))
    x = next((i for i in man if i["id"] == iid), None)
    path = ROOT / "data/acts" / f"{iid}.json"
    if not x or not x.get("file") or not path.exists() or not (ROOT / "sources/pdf" / x["file"]).exists(): return None
    act = json.loads(path.read_text())
    doc = fitz.open(ROOT / "sources/pdf" / x["file"])
    secs = [s for p in act["parts"] for s in p["sections"]]
    allwords = lambda: Counter(w for s in secs for q in s["text"] for w in W(q))
    before = allwords()
    done = skipped = 0; notes = []
    for pno, pg in enumerate(doc):
        for t in find_tables(pg, strict=True):
            words = [w for r in t["rows"] for c in r for w in W(c)]
            if len(words) < 6: continue
            hit = None
            for s in secs:
                if s.get("page") and abs(s["page"] - (pno + 1)) > 2: continue
                paras = s["text"]
                toks = []                                   # (word, paragraph, start, end) over the whole provision
                for pi, q in enumerate(paras):
                    if q.startswith("|"): toks.append(("|", pi, 0, 0)); continue
                    masked = re.sub(r"\{fn:[^}]*\}", lambda m: " " * len(m.group()), q)
                    toks += [(m.group().lower(), pi, m.start(), m.end()) for m in re.finditer(r"[^\W_]+", masked)]
                tw = [t_[0] for t_ in toks]
                for a0 in range(len(tw) - len(words) + 1):
                    if tw[a0] == words[0] and tw[a0:a0 + len(words)] == words:
                        hit = (s, toks[a0], toks[a0 + len(words) - 1]); break
                if not hit and len(tw) >= len(words):        # same words in another reading order (cells read column by column)
                    need = Counter(words); n = len(words); win = Counter(tw[:n])
                    for a0 in range(len(tw) - n + 1):
                        if a0: win[tw[a0 - 1]] -= 1; win[tw[a0 + n - 1]] += 1
                        if tw[a0] in need and tw[a0 + n - 1] in need and not (need - win) and not (win - need):
                            hit = (s, toks[a0], toks[a0 + n - 1]); break
                if hit: break
            if hit:
                s, ta, tb = hit
                paras = s["text"]; ia, ib = ta[1], tb[1]
                if "{fn:" in paras[ia][ta[2]:] and ia == ib and "{fn:" in paras[ia][ta[2]:tb[3]]: hit = None
                elif any("{fn:" in paras[k] for k in range(ia + 1, ib)) or "{fn:" in paras[ia][ta[2]:] and ia != ib or "{fn:" in paras[ib][:tb[3]] and ia != ib: hit = None
            if hit:
                lvl = lambda q: re.match(r">*", q).group()
                new = []
                pre = paras[ia][:ta[2]].strip()
                if pre.strip(">"): new.append(pre)
                new += row_strings(t["rows"])
                suf = paras[ib][tb[3]:].strip()
                if suf: new.append(lvl(paras[ib]) + suf if not suf.startswith(">") else suf)
                s["text"][ia:ib + 1] = new; done += 1
            else:
                skipped += 1; notes.append(f"p.{pno + 1} {len(t['rows'])}x{len(t['rows'][0])} {t['rows'][0][0][:30]!r}")
    if allwords() != before: raise SystemExit(f"{iid}: words changed, nothing written")        # safety: only layout may change
    if apply and done: path.write_text(json.dumps(act, indent=1, ensure_ascii=False) + "\n")
    return done, skipped, notes


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; apply = "--apply" in sys.argv
    if "--all" in sys.argv: args = [p.stem for p in sorted((ROOT / "data/acts").glob("*.json"))]
    tot = 0
    for iid in args:
        r = process(iid, apply)
        if r and (r[0] or r[1]):
            tot += r[0]; print(f"{iid}: converted {r[0]}, left as text {r[1]}" + ("" if r[0] + r[1] > 6 else "  " + "; ".join(r[2])))
    print("tables converted:", tot, "(applied)" if apply else "(dry run)")
