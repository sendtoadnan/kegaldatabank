"""Find passages that the independent first-pass reading has but our converted text lacks.

usage: python3 tools/ocr/missing_runs.py --scans <scans folder> [<id> ...]
For each instrument, the first-pass OCR of its pages is compared word by word with our text: a word is "covered" when a
five-word sequence around it occurs in our text. A run of 14 or more uncovered words is printed with its context, unless it
looks like a footnote (SRO, dated, substituted, inserted ...), a running head, a form or schedule (anything after the
instrument's last provision is ignored). Leads for re-reading the scan, not proof of loss. Writes docs/MISSING_RUNS.md.
"""
import json, re, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
args = sys.argv[1:]; SC = Path(args[args.index("--scans") + 1]); ids = [a for a in args if not a.startswith("--") and a != str(SC)]
FN = re.compile(r"\{fn:[^}]+\}")
conv = [c for c in json.load(open(ROOT / "data/salam/conversions.json"))["instruments"] if not c.get("hold")]
if ids: conv = [c for c in conv if c["id"] in ids]
NOTE = re.compile(r"\b(S\.?R\.?O|dated|substituted|inserted|omitted|deleted|notification|before (omission|substitution)|read as follows|Company Law|Rules & Regulations|Pt\.|III - |E2 |Part [IVX]+,|Form[- ]|Schedule|Annex|Specimen|Particulars of)\b", re.I)
def tk(t): return re.findall(r"[a-z0-9]+", re.sub(r"[\[\]“”\"'’‘>]", "", t.lower()))
out = ["# Passages in the independent reading that our text lacks", "", "`python3 tools/ocr/missing_runs.py --scans <folder>`: runs of 14+ words present in the independent first-pass reading but not in our text, outside footnotes and forms. Leads to re-read against the scan; many are footnotes quoting old wording or running heads.", ""]
total = 0; per = {}
for c in conv:
    i = c["id"]; pf = ROOT / "data/salam/pages" / f"{i}.json"; f = ROOT / "data/acts" / f"{i}.json"
    if not pf.exists() or not f.exists(): continue
    raw_pages = []
    for p in json.load(open(pf))["scans"]:
        tf = SC / "_ocr text" / p["file"] / f"p{p['scan']:04d}.txt"
        if tf.exists(): raw_pages.append(tf.read_text())
    raw = re.sub(r"\s+", " ", " ".join(raw_pages))
    act = json.load(open(f))
    ours = tk(" ".join(t for pt in act["parts"] for s in pt["sections"] for t in [s["title"]] + s["text"]) + " " + act.get("preamble", ""))
    grams = set(" ".join(ours[k:k + 5]) for k in range(len(ours) - 4))
    words = tk(raw); n = len(words)
    cov = [False] * n
    for k in range(n - 4):
        if " ".join(words[k:k + 5]) in grams:
            for j in range(k, k + 5): cov[j] = True
    # the instrument's text ends at its last provision: ignore the first-pass text after its final words
    tail = " ".join(ours[-6:]); endpos = " ".join(words).rfind(tail)
    limit = n
    if endpos > 0: limit = len(" ".join(words)[:endpos + len(tail)].split())
    k = 0; found = []
    while k < limit:
        if not cov[k]:
            j = k
            while j < limit and not cov[j]: j += 1
            if j - k >= 14:
                run = " ".join(words[k:j]); ctx = " ".join(words[max(0, k - 6):k]) + " [[" + run[:260] + ("…" if len(run) > 260 else "") + "]] " + " ".join(words[j:j + 5])
                rawrun = raw  # footnote cue test on the original wording around the run
                if not NOTE.search(run) and not NOTE.search(" ".join(words[max(0, k - 8):k])): found.append((j - k, ctx))
            k = j
        else: k += 1
    per[i] = len(found); total += len(found)
    if found:
        out += [f"## {act['title']} (`{i}`): {len(found)}", ""]
        for ln, ctx in found[:15]: out.append(f"- ({ln} words) {ctx}")
        out.append("")
Path(ROOT / "docs/MISSING_RUNS.md").write_text("\n".join(out) + "\n")
print(total, "runs;", {k: v for k, v in sorted(per.items(), key=lambda kv: -kv[1]) if v}.items().__len__(), "instruments")
print(sorted(per.items(), key=lambda kv: -kv[1])[:12])
