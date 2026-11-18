"""Rank the converted instruments and provisions by how well they agree with an independent reading of the scan.

usage: python3 tools/ocr/cross_check.py --scans <scans folder> [<id> ...]   (default: every instrument in data/salam/conversions.json that is published)
The converter reads each page twice (whole page, and bands) and merges them. The first-pass OCR in `_ocr text/`
is a third, independent reading at a lower resolution. For each provision, the share of its five-word sequences
that also occur in that first-pass text of the same pages is the "agreement". Low agreement means one of the two
readings went wrong there, so a person should look at that provision first. It is NOT a verification: the
instrument stays Unverified until a person checks it against the scan (scripts/mark_verified.py).
Writes docs/CHECK_PRIORITY.md.
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
args = sys.argv[1:]
SC = Path(args[args.index("--scans") + 1]); ids = [a for a in args if not a.startswith("--") and a != str(SC)]
conv = [c for c in json.load(open(ROOT / "data/salam/conversions.json"))["instruments"] if not c.get("hold")]
if ids: conv = [c for c in conv if c["id"] in ids]
FN = re.compile(r"\{fn:[^}]+\}")
def toks(t):
    t = FN.sub("", t).replace(">", " ")
    return re.findall(r"[a-z0-9]+", re.sub(r"[\[\]“”\"'’‘]", "", t.lower()))
def grams(w, n=5): return [" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))]
results = []
for c in conv:
    pf = ROOT / "data/salam/pages" / f"{c['id']}.json"
    f = ROOT / "data/acts" / f"{c['id']}.json"
    if not pf.exists() or not f.exists(): continue
    pages = json.load(open(pf))["scans"]
    raw = []
    for p in pages:
        tf = SC / "_ocr text" / p["file"] / f"p{p['scan']:04d}.txt"
        if tf.exists(): raw.append(tf.read_text())
    have = set(grams(toks(" ".join(raw))))
    act = json.load(open(f)); rows = []; tot = ok = 0
    for part in act["parts"]:
        for s in part["sections"]:
            g = grams(toks(s["title"] + " " + " ".join(s["text"])))
            if not g: continue
            hit = sum(1 for x in g if x in have)
            rows.append((hit / len(g), s["no"], s["title"], len(g))); tot += len(g); ok += hit
    results.append((ok / tot if tot else 1, c["id"], act["title"], rows, tot))
results.sort()
out = ["# Where to look first when checking the converted instruments", "",
       "Made by `python3 tools/ocr/cross_check.py --scans <scans folder>` on " + str(__import__('datetime').date.today()) + ". For each provision: the share of its five-word sequences that an independent, lower-resolution reading of the same scan pages also contains. Low = the two readings disagree there, so check that provision against the scan first. This is a guide to where mistakes are likely, not a verification: every instrument stays Unverified until a person checks it (task 64).", "",
       "| Instrument | Agreement | Provisions below 85% (check these first) |", "|---|---|---|"]
for score, i, title, rows, tot in results:
    low = sorted([r for r in rows if r[0] < 0.85 and r[3] >= 8])
    names = ", ".join(f"{r[1]} ({r[0]*100:.0f}%)" for r in low[:12]) + (" …" if len(low) > 12 else "")
    out.append(f"| {title} (`{i}`) | {score*100:.0f}% | {names or 'none'} |")
Path(ROOT / "docs/CHECK_PRIORITY.md").write_text("\n".join(out) + "\n")
print(f"{len(results)} instruments; lowest agreement:")
for score, i, title, rows, tot in results[:8]: print(f"  {score*100:.0f}%  {i}")
print("highest:", f"{results[-1][0]*100:.0f}% {results[-1][1]}")
