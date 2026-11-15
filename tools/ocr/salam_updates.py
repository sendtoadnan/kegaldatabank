"""Extract the update history from the OCR'd update letters and "Note from the Author" pages.

usage: python3 tools/ocr/salam_updates.py <volume label> <out.json> <page.txt> ...
Facts only (update number, date, book page, S.R.O.s / circulars named, repealed or amended);
the publisher's wording stays in the OCR text in OneDrive.
"""
import json, re, sys
MON = "January February March April May June July August September October November December".split()
UPD = re.compile(r"(\d+)(?:st|nd|rd|th)\s*Update\s*-\s*([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})")
NOTE = re.compile(r"complete the\s*(\d+)\s*(?:st|nd|rd|th)\s*update", re.I)
ITEM = re.compile(r"On page\s+([A-Z]{1,4}\s*-\s*[0-9()., ]+?)(?:\s+onwards)?\s*,\s*(.+?)(?=\n\s*\d{1,2}\s*\.\s*\n|\n\s*\d{1,2}\s*\.\s|Suggestions,|\Z)", re.S)
SRO = re.compile(r"SRO\s*(\d{1,4})\s*\(?[1IlLT\[\]D()]*\)?\s*/\s*(\d{4})")
CIRC = re.compile(r"Circular\s*(?:No\.?\s*)?(\d{1,3})\s*of\s*(\d{4})", re.I)

label, dest, files = sys.argv[1], sys.argv[2], sorted(sys.argv[3:])
dates, notes, cur = {}, {}, None
for f in files:
    t = open(f).read()
    m = UPD.search(t)
    if m and m.group(2)[:3].title() in [x[:3] for x in MON]:
        mo = [x[:3] for x in MON].index(m.group(2)[:3].title()) + 1
        dates[int(m.group(1))] = f"{m.group(4)}-{mo:02d}-{int(m.group(3)):02d}"
    n = NOTE.search(t)
    if n: cur = int(n.group(1)); notes.setdefault(cur, "")
    if cur is not None and not m: notes[cur] += "\n" + t
updates = []
for u in sorted(notes, reverse=True):
    items = []
    for pg, body in ITEM.findall(notes[u]):
        body = " ".join(body.split())
        kind = "repealed" if re.search(r"repealed", body, re.I) else "amended" if re.search(r"amended|substituted|added|omitted|inserted", body, re.I) else "reproduced" if "reproduced" in body.lower() else "changed"
        items.append({"page": re.sub(r"\s+", "", pg).rstrip(",."), "kind": kind,
                      "sros": sorted({f"{int(a)}(I)/{b}" for a, b in SRO.findall(body)}),
                      "circulars": sorted({f"{int(a)} of {b}" for a, b in CIRC.findall(body)})})
    updates.append({"update": u, "date": dates.get(u), "items": items})
json.dump({"source": "S.A. Salam, Complete Company Law and Procedures", "volume": label, "index": "Update letters and Notes from the Author (facts only)", "updates": updates}, open(dest, "w"), indent=1)
print(len(updates), "updates;", sum(len(x["items"]) for x in updates), "items;", sum(1 for x in updates if not x["date"]), "without date")
