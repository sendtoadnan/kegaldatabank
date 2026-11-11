"""Parse the OCR'd chronological index of notifications (column halves) into JSON.

usage: python3 tools/ocr/salam_notifications.py <volume label> <out.json> <page.boxes.tsv> ...
(from tools/ocr/ocr_boxes.py; each S.R.O. is paired with the page reference on its row)
Each entry: S.R.O. number, date, book page. Duplicates (old and replacement index pages) are merged.
"""
import json, re, sys
from datetime import datetime

MONTHS = {m[:3].lower(): i for i, m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"], 1)}
SRO = re.compile(r"(\d{1,4})\s*\(?\s*[1IlLT\[\]D()]*\s*\)?\s*/\s*(\d{4})\s+dated\s+([A-Za-z]+)\.?\s+([0-9OБ]{1,2})\s*,?\s*(\d{4})")
PAGE = re.compile(r"^[-\s]*([A-Za-zПШБ1I]{1,4})\s*-\s*([0-9OБ]+(?:\s*\([^)]*\))?(?:\s*,\s*\d+)?)")

def part(s):
    s = s.replace("П", "II").replace("Ш", "III").replace("Б", "6").upper()
    s = re.sub(r"^A[1IL]$", "AI", s)
    if s.startswith("A"): return "AI"
    s = s.replace("1", "I").replace("L", "I").replace("T", "I")
    return s if s in ("I", "II", "III", "IV", "V", "VA", "VI", "VII", "VIII", "IX", "X") else s

def fix_page(pg):
    """Repair OCR slips in the part prefix: Vol I has parts AI, II (to about page 100) and III."""
    pre, _, rest = pg.partition("-")
    pre = pre.replace("H", "I")
    if re.fullmatch(r"I{3,}", pre) or pre == "I": pre = "III"
    n = re.match(r"\d+", rest)
    if pre == "II" and n and int(n.group()) > 110: pre = "III"
    return f"{pre}-{rest}"

def num(s): return s.replace("O", "0").replace("Б", "6")

def parse(lines):
    items = []
    for ln in lines:
        box, _, text = ln.partition("\t")
        if not text: continue
        x0, y0, x1, y1 = map(float, box.split())
        items.append((x0, (y0 + y1) / 2, x1, text.strip()))
    out = []
    for x0, yc, x1, text in items:
        m = SRO.search(text)
        if not m: continue
        n, y, mon, d, dy = m.groups()
        mo = MONTHS.get(mon[:3].lower())
        entry = {"sro": f"{int(n)}(I)/{y}", "date": f"{dy}-{mo:02d}-{int(num(d)):02d}" if mo else None, "page": None}
        rest = text[m.end():].strip()
        cands = [(0, rest)] if rest else []
        cands += sorted((abs(c[1] - yc), c[3]) for c in items
                        if c[0] > x1 - 0.03 and c[0] < x1 + 0.15 and abs(c[1] - yc) < 0.012 and not SRO.search(c[3]))
        for _, c in cands:
            p = PAGE.match(c)
            if p:
                entry["page"] = fix_page(f"{part(p.group(1))}-{num(p.group(2)).replace(' ', '')}"); break
        out.append(entry)
    return out

label, dest, files = sys.argv[1], sys.argv[2], sys.argv[3:]
seen = {}
for f in files:
    for e in parse(open(f).read().splitlines()):
        key = (e["sro"], e["page"])
        if key not in seen or (e["date"] and not seen[key]["date"]): seen[key] = e
# drop page-less duplicates when the same S.R.O. has a page elsewhere
have = {e["sro"] for e in seen.values() if e["page"]}
rows = [e for e in seen.values() if e["page"] or e["sro"] not in have]
rows.sort(key=lambda e: (e["date"] or "9999", e["sro"]))
json.dump({"source": "S.A. Salam, Complete Company Law and Procedures", "volume": label, "index": "Chronological list of notifications", "entries": rows}, open(dest, "w"), indent=1)
print(len(rows), "entries;", sum(1 for e in rows if not e["page"]), "without page;", sum(1 for e in rows if not e["date"]), "without date")
