"""Read a two-column comparative index (Companies Act 2017 | Companies Ordinance 1984) from a PDF with a text layer.

usage: python3 tools/ocr/comparative_index_pdf.py <index.pdf> <out.json> [first-page last-page]
Columns are found from the words' x positions (Act number | Act heading | Ordinance number | Ordinance heading); a row starts where either
side has a number or a "No provision" note, and both sides' lines are assigned to the row they sit under.
Internal working record (data/salam/ is for the book; this is a second, independent source supplied by the user).
"""
import json, re, sys
import fitz
pdf, out = sys.argv[1], sys.argv[2]
first = int(sys.argv[3]) if len(sys.argv) > 3 else 3; last = int(sys.argv[4]) if len(sys.argv) > 4 else None
d = fitz.open(pdf); last = last or len(d) - 1
NUM = re.compile(r"^\d{1,3}[A-Z]{0,3}(\(\d+\))?$")
def lines(words, side):
    ws = [w for w in words if (w[0] < 325) == (side == "L")]
    ws.sort(key=lambda w: (round(w[1] / 3), w[0])); res = []
    for w in ws:
        y = w[1]
        if res and abs(res[-1]["y"] - y) < 2.5: res[-1]["w"].append(w)
        else: res.append({"y": y, "w": [w]})
    return res
rows = []
for pn in range(first - 1, last):
    words = [w for w in d[pn].get_text("words") if 45 < w[1] < 745]
    L, R = lines(words, "L"), lines(words, "R")
    def split(line, side):
        ws = sorted(line["w"], key=lambda w: w[0]); num = None; rest = ws
        lo, hi = (0, 110) if side == "L" else (325, 372)
        if ws and lo <= ws[0][0] < hi and NUM.match(ws[0][4]): num = ws[0][4]; rest = ws[1:]
        return num, " ".join(w[4] for w in rest)
    ent = []
    for side, ls in (("L", L), ("R", R)):
        for ln in ls:
            n, t = split(ln, side)
            if ln["w"][0][4] in ("Section", "Comparative", "Index") and ln["y"] < 75: continue
            ent.append({"side": side, "y": ln["y"], "n": n, "t": t})
    starts = sorted({round(e["y"]) for e in ent if e["n"] or re.match(r"^(No provision|No separate provision|No corresponding)", e["t"])})
    page = {s: {"L": {"n": None, "t": ""}, "R": {"n": [], "t": ""}} for s in starts}
    for e in sorted(ent, key=lambda e: e["y"]):
        s = max([x for x in starts if x <= e["y"] + 2.0] or [starts[0]])
        cell = page[s][e["side"]]
        if e["side"] == "L":
            if e["n"] and cell["n"] is None: cell["n"] = e["n"]
            cell["t"] = (cell["t"] + " " + e["t"]).strip()
        else:
            if e["n"]: cell["n"].append(e["n"])
            cell["t"] = (cell["t"] + " " + e["t"]).strip()
    for s in starts: rows.append({"page": pn + 1, "y": s, "act": page[s]["L"], "ordinance": page[s]["R"]})
json.dump(rows, open(out, "w"), ensure_ascii=False, indent=1)
print(len(rows), "rows from pages", first, "to", last)
