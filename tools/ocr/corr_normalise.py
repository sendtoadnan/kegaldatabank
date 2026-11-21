"""Normalise the cell-by-cell reading of the corresponding-provisions table (tools/ocr/corr_rows.py).

usage: python3 tools/ocr/corr_normalise.py <cells.json> <out.json>
Merges continuation rows, takes each cell's provision number, checks 2017 numbers against the Act's own section order and
1984 numbers against ascending order, repairs a number only when the sequence leaves one possibility, and lists the rest.
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
cells = json.load(open(sys.argv[1]))
ACT = json.load(open(ROOT / "data/acts/companies-act-2017.json"))
TITLE = {s["no"]: s["title"] for p in ACT["parts"] for s in p["sections"]}; ORDER = {n: k for k, n in enumerate(TITLE)}
NUM = re.compile(r"^[-•\s]*(\d{1,3}[A-Z]{0,3})\s+(.*)$")
def split(t):
    """Provision number = the first token of the form 234 / 234A followed by a word (margin codes such as 'E2 01-20-0' or '-17' come first on some rows)."""
    t = (t or "").strip(" -•")
    tok = t.split()
    for i in range(min(6, len(tok) - 1)):
        if re.fullmatch(r"\d{1,3}[A-Z]{0,3}", tok[i]) and re.match(r"[A-Za-z(\"“]", tok[i + 1]):
            return tok[i], " ".join(tok[i + 1:])
    m = re.match(r"^(\d{1,3})([A-Z][a-z].*)$", t)          # number glued to its title: "496Penalty ..."
    if m: return m.group(1), m.group(2)
    return None, t
rows = []
for c in cells:
    ln, lt = split(c.get("L")); rn, rt = split(c.get("R"))
    if ln is None and rn is None and rows and (lt or rt) and not (c.get("L", "").strip() in ("", "-") and c.get("R", "").strip() in ("", "-")):
        # continuation of the row above
        if lt: rows[-1]["lt"] += " " + lt
        if rt: rows[-1]["rt"] += " " + rt
        continue
    rows.append({"scanPage": c["scanPage"], "printed": c["printed"], "ln": ln, "lt": lt if ln else "", "rn": rn, "rt": rt if rn else "", "lraw": c.get("L", ""), "rraw": c.get("R", "")})
issues = []
# 2017 side: must follow the Act's order
def one_off(a, b): return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1
prev = None
for r in rows:
    if r["ln"] is None: continue
    if prev in ORDER and r["ln"] != prev and ORDER[prev] + 1 < len(ORDER):
        want = list(ORDER)[ORDER[prev] + 1]
        if r["ln"] != want and one_off(r["ln"], want):
            issues.append(f"2017 number {r['ln']!r} read as {want} (page {r['printed']}; follows {prev})"); r["ln"] = want; r["repaired"] = True
    if r["ln"] not in ORDER:
        issues.append(f"2017 number {r['ln']!r} (page {r['printed']}) is not a section of the Act: {r['lraw'][:50]!r}")
    elif prev is not None and ORDER[r["ln"]] != ORDER[prev] + 1 and ORDER[r["ln"]] != ORDER[prev]:
        issues.append(f"2017 order: {prev} then {r['ln']} (page {r['printed']})")
    if r["ln"] in ORDER: prev = r["ln"]
def key(n): m = re.match(r"(\d+)([A-Z]*)", n); return (int(m.group(1)), m.group(2))
# 1984 side: ascending, repair a lone slip
last = None
for i, r in enumerate(rows):
    if r["rn"] is None: continue
    if last is not None and key(r["rn"]) < key(last) and r["rt"]:
        nxt = next((x["rn"] for x in rows[i + 1:] if x["rn"]), None)
        guess = str(key(last)[0] + 1)
        if nxt and key(last)[0] < key(guess)[0] < key(nxt)[0] and len(re.sub(r"\D", "", r["rn"])) < len(re.sub(r"\D", "", last)):
            issues.append(f"1984 number {r['rn']!r} read as {guess} (page {r['printed']}; between {last} and {nxt})"); r["rn"] = guess; r["repaired"] = True
        else:
            issues.append(f"1984 order: {last} then {r['rn']} (page {r['printed']}): {r['rraw'][:50]!r}")
    last = r["rn"]
# 2017 rows whose number the OCR lost: fill from the Act's order when exactly one section is missing between neighbours
for i, r in enumerate(rows):
    if r["ln"] is None and r["lraw"].strip() not in ("", "-") and not r["lt"] and False: pass
out = []
for r in rows:
    if r["ln"] is None and r["rn"] is None: continue
    out.append({"scanPage": r["scanPage"], "printed": r["printed"],
        "act2017": ({"no": r["ln"], "title": TITLE.get(r["ln"], r["lt"])} if r["ln"] else None),
        "ordinance1984": ({"no": r["rn"], "title": r["rt"]} if r["rn"] else None), **({"repaired": True} if r.get("repaired") else {})})
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
have = [r["act2017"]["no"] for r in out if r["act2017"]]
lo, hi = ORDER[have[0]], ORDER[have[-1]]
print(len(out), "rows;", len(have), "with a 2017 provision;", sum(1 for r in out if r["ordinance1984"]), "with a 1984 provision")
for i in issues: print(" -", i)
