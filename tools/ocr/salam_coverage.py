"""Compare the S.A. Salam indexes (data/salam/) with the library and write docs/SALAM_COVERAGE.md.

usage: python3 tools/ocr/salam_coverage.py
For each instrument in the book: is it in the library, our edition date, and the latest change the
book's update history records on its pages (so whether the book is newer).
"""
import json, re
from pathlib import Path
R = Path(__file__).resolve().parents[2]
lib = json.load(open(R / "sources/manifest.json"))
STOP = {"the","of","and","for","in","regulations","regulation","rules","rule","reg","secp","companies","company","securities","exchange","commission","pakistan","act","ordinance"}
def toks(s): return {w for w in re.findall(r"[a-z]+|\d{4}", s.lower().replace("&", "and")) if w not in STOP}
def yr(s): y = re.findall(r"\d{4}", s); return y[-1] if y else None
def match(title):
    best = (0, None)
    for l in lib:
        a, b = toks(title), toks(l["title"])
        j = len(a & b) / max(1, len(a | b))
        if yr(title) and yr(l["title"]) and yr(title) != yr(l["title"]): j *= 0.4
        best = max(best, (j, l), key=lambda z: z[0])
    return best[1] if best[0] > 0.6 else None
def pkey(pg):
    m = re.match(r"([A-Z]+)-(\d+)(?:\((\d+)\))?", pg or "")
    return (m.group(1), int(m.group(2)), int(m.group(3) or 0)) if m else None

rows, lines = [], []
for v in ("vol1", "vol2"):
    contents = json.load(open(R / f"data/salam/{v}-contents.json"))
    updates = json.load(open(R / f"data/salam/{v}-updates.json"))["updates"]
    items = [i for i in contents["items"] if pkey(i["page"])]
    items.sort(key=lambda i: pkey(i["page"]))
    for k, it in enumerate(items):
        lo = pkey(it["page"]); hi = pkey(items[k + 1]["page"]) if k + 1 < len(items) and items[k + 1]["part"] == it["part"] else (lo[0], 10**6, 0)
        changes = [(u["date"], u["update"], c) for u in updates for c in u["items"] if pkey(c["page"]) and lo <= pkey(c["page"]) < hi]
        l = match(it["title"])
        last = max((c[0] for c in changes), default=None)
        ours = l.get("amendedUpTo") if l else None
        if not l: verdict = "not in library"
        elif last and ours and last > ours: verdict = "book has later changes"
        else: verdict = "no later change recorded"
        rows.append({"volume": contents["volume"], "page": it["page"], "title": it["title"], "status": it.get("status"),
                     "library": l["id"] if l else None, "ourEdition": ours, "lastChangeInBook": last,
                     "changes": [{"date": d, "update": u, **c} for d, u, c in sorted(changes, key=lambda z: z[0] or "", reverse=True)], "verdict": verdict})
json.dump(rows, open(R / "data/salam/coverage.json", "w"), indent=1)

out = ["# S.A. Salam coverage check", "",
       "Made by `python3 tools/ocr/salam_coverage.py` from the book's contents and update history (`data/salam/`).",
       "The book is a trusted source (CLAUDE.md, 12 Nov 2026). \"Later changes\" means the book's update notes record an amendment, new S.R.O. or circular on that instrument's pages after our edition date: check each before re-converting.", ""]
for verdict in ("book has later changes", "not in library", "no later change recorded"):
    sel = [r for r in rows if r["verdict"] == verdict]
    out += [f"## {verdict.capitalize()} ({len(sel)})", "", "| Book page | Instrument | Library | Our edition | Last change in book |", "|---|---|---|---|---|"]
    for r in sel:
        t = r["title"] + (f" — *{r['status']}*" if r["status"] else "")
        out.append(f"| {r['page']} | {t} | {r['library'] or ''} | {r['ourEdition'] or ''} | {r['lastChangeInBook'] or ''} |")
    out.append("")
(R / "docs/SALAM_COVERAGE.md").write_text("\n".join(out))
from collections import Counter
print(Counter(r["verdict"] for r in rows))
