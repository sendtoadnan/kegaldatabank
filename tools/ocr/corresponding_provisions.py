"""Read the table of corresponding provisions (Companies Act 2017 against Companies Ordinance 1984) from boxed OCR.

usage: python3 tools/ocr/corresponding_provisions.py <boxes folder> <out.json> <page:printed-page> ...
Each page is a two-column table (2017 left, 1984 right). A row's entries start with a provision number (e.g. 234A);
a right-hand entry pairs with the left-hand entry it lines up with; unmatched entries mean "no counterpart".
Internal working record (data/salam/); the website shows only the section correspondences, in our own layout.
"""
import json, re, sys
from pathlib import Path
folder = Path(sys.argv[1]); out = Path(sys.argv[2]); pages = sys.argv[3:]
START = re.compile(r"^(\d{1,3}[A-Z]{0,3})\s+(?=\S)")
def lines(p):
    rows = []
    for ln in (folder / f"p{int(p):04d}.boxes.tsv").read_text().splitlines():
        try: box, text = ln.split("\t", 1)
        except ValueError: continue
        x0, y0, x1, y1 = map(float, box.split())
        rows.append((x0, y0, x1, y1, text.strip()))
    return sorted(rows, key=lambda r: (r[1], r[0]))
def geometry(rows):
    """Column split and first body line from the two 'Section / Provision & Title' header lines (scans sit a little differently on each page)."""
    h = [r for r in rows if "Provision" in r[4] and "Title" in r[4]]
    if len(h) >= 2:
        h.sort(key=lambda r: r[0]); return (h[0][2] + h[-1][0]) / 2, min(r[3] for r in h) - 0.002
    return 0.53, 0.095
def merge(rows, split):
    merged = []
    for col in (True, False):
        part = sorted([r for r in rows if (r[0] < split) == col], key=lambda r: ((r[1] + r[3]) / 2, r[0]))
        cur = None
        for r in part:
            yc = (r[1] + r[3]) / 2
            if cur and abs(yc - cur["yc"]) < 0.006 and r[0] >= cur["x0"]:
                cur["t"] += " " + r[4]; cur["x1"] = max(cur["x1"], r[2]); cur["y0"] = min(cur["y0"], r[1]); cur["y1"] = max(cur["y1"], r[3])
            else:
                if cur: merged.append((cur["x0"], cur["y0"], cur["x1"], cur["y1"], cur["t"]))
                cur = {"x0": r[0], "y0": r[1], "x1": r[2], "y1": r[3], "t": r[4], "yc": yc}
        if cur: merged.append((cur["x0"], cur["y0"], cur["x1"], cur["y1"], cur["t"]))
    return sorted(merged, key=lambda r: (r[1], r[0]))
def entries(rows, left):
    split, top = geometry(rows)
    rows = merge(rows, split)
    out, cur = [], None
    for x0, y0, x1, y1, t in rows:
        if (x0 < split) != left or y0 < top or not t or re.search(r"Provision & Title|Companies Ordinance, 1984|Companies Act, 2017$|Corresponding Provisions", t): continue
        m = START.match(t)
        if m and (cur is None or y0 - cur["y0"] > 0.006):
            if cur: out.append(cur)
            cur = {"no": m.group(1), "title": t[m.end():], "y0": y0, "y1": y1}
        elif cur:
            cur["title"] += " " + t; cur["y1"] = max(cur["y1"], y1)
    if cur: out.append(cur)
    return out
result = []
for spec in pages:
    p, printed = spec.split(":")
    rows = lines(p); L = entries(rows, True); R = entries(rows, False)
    used = set(); page = {"scanPage": int(p), "printed": printed, "rows": []}
    owner = {}
    for k, r in enumerate(R):
        near = sorted(((abs(r["y0"] - l["y0"]), i) for i, l in enumerate(L) if abs(r["y0"] - l["y0"]) <= 0.008))
        if near: owner[k] = near[0][1]; continue
        inside = [i for i, l in enumerate(L) if l["y0"] <= r["y0"] <= l["y1"] - 0.004]
        if inside: owner[k] = inside[-1]
    for i, l in enumerate(L):
        match = [k for k in sorted(owner) if owner[k] == i]
        for k in match: used.add(k)
        page["rows"].append({"act2017": {"no": l["no"], "title": l["title"].strip()}, "ordinance1984": [{"no": R[k]["no"], "title": R[k]["title"].strip()} for k in match], "y": round(l["y0"], 3)})
    for k, r in enumerate(R):
        if k not in used: page["rows"].append({"act2017": None, "ordinance1984": [{"no": r["no"], "title": r["title"].strip()}], "y": round(r["y0"], 3)})
    page["rows"].sort(key=lambda r: r["y"])
    result.append(page)
ACT = json.load(open(Path(__file__).resolve().parents[2] / "data/acts/companies-act-2017.json"))
SECS = [(x["no"], x["title"]) for pt in ACT["parts"] for x in pt["sections"]]
ORDER = {n: k for k, (n, _) in enumerate(SECS)}
for page in result:
    rows = page["rows"]
    for k in range(len(rows) - 1):
        pass
    have = [r["act2017"]["no"] for r in rows if r["act2017"]]
    if not have: continue
    lo, hi = ORDER.get(have[0]), ORDER.get(have[-1])
    if lo is None or hi is None: continue
    missing = [n for n, _ in SECS[lo:hi + 1] if n not in have]
    for n in missing:
        # between the left rows that surround it in the Act's order, take the unpaired right-hand rows
        before = [r for r in rows if r["act2017"] and ORDER.get(r["act2017"]["no"], -1) < ORDER[n]]
        after = [r for r in rows if r["act2017"] and ORDER.get(r["act2017"]["no"], 10**9) > ORDER[n]]
        if not before or not after: continue
        y0, y1 = before[-1]["y"], after[0]["y"]
        cand = [r for r in rows if not r["act2017"] and y0 < r["y"] < y1]
        entry = {"act2017": {"no": n, "title": dict(SECS)[n], "filledFromActSequence": True}, "ordinance1984": [], "y": round((y0 + y1) / 2, 3)}
        if len(cand) == 1 and len(missing) == 1 or len(cand) == len(missing) and missing.index(n) < len(cand):
            c = cand[missing.index(n)] if len(cand) == len(missing) else cand[0]
            entry["ordinance1984"] = c["ordinance1984"]; entry["y"] = c["y"]; rows.remove(c)
        rows.append(entry)
    rows.sort(key=lambda r: r["y"])
out.write_text(json.dumps(result, ensure_ascii=False, indent=1))
n = sum(len(p["rows"]) for p in result); print(n, "rows from", len(result), "pages ->", out)
