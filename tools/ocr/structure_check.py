"""Find places where a line of law text was probably dropped by the OCR, from the text's own structure.

usage: python3 tools/ocr/structure_check.py [<id> ...]    (default: every instrument converted from the printed edition)
Reports, per provision: a gap in a list of labels ((a), (b), (d); (i), (ii), (iv); (1), (3)); a paragraph with unbalanced
round brackets; a cross-reference to a provision number that the instrument does not have. Writes docs/STRUCTURE_CHECK.md.
These are leads for a person (or for re-reading the scan), not proof of an error: lists can skip on purpose (omitted items).
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
FN = re.compile(r"\{fn:[^}]+\}")
ids = sys.argv[1:] or [c["id"] for c in json.load(open(ROOT / "data/salam/conversions.json"))["instruments"] if not c.get("hold")]
ROMAN = {"i":1,"ii":2,"iii":3,"iv":4,"v":5,"vi":6,"vii":7,"viii":8,"ix":9,"x":10,"xi":11,"xii":12,"xiii":13,"xiv":14,"xv":15,"xvi":16,"xvii":17,"xviii":18,"xix":19,"xx":20}
LAB = re.compile(r"^>*\[?\(\s*([A-Za-z0-9]{1,6})\s*\)")
def kind(x, prev):
    if x.isdigit(): return "digit", int(x)
    if x in ROMAN and not (len(x) == 1 and prev.get("alpha") and ord(x) == ord(prev["alpha"]) + 1 and x not in "xv"): return "roman", ROMAN[x]
    if re.fullmatch(r"[a-z]", x): return "alpha", ord(x) - 96
    if re.fullmatch(r"[A-Z]", x): return "upper", ord(x) - 64
    return None, None
report = []; total = 0
for i in ids:
    f = ROOT / "data/acts" / f"{i}.json"
    if not f.exists(): continue
    act = json.load(open(f)); nums = {s["no"] for p in act["parts"] for s in p["sections"]}
    maxn = max([int(re.match(r"\d+", n).group()) for n in nums] or [0])
    for part in act["parts"]:
        for s in part["sections"]:
            last = {}; prevalpha = {}
            for k, t in enumerate(s["text"]):
                tt = FN.sub("", t)
                m = LAB.match(tt)
                if m:
                    lab = m.group(1); kd, v = kind(lab, {"alpha": prevalpha.get("c")})
                    if kd:
                        if kd == "alpha": prevalpha["c"] = lab
                        lv = last.get(kd)
                        if lv is not None and v > lv + 1 and not (kd == "roman" and lv == 0):
                            missing = (str(lv + 1) if kd == "digit" else chr(96 + lv + 1) if kd == "alpha" else chr(64 + lv + 1) if kd == "upper"
                                       else next((r for r, n in ROMAN.items() if n == lv + 1), "?"))
                            report.append((i, s["no"], f"list jumps from ({chr(96+lv) if kd=='alpha' else lv}) to ({lab}): ({missing}) may be missing", tt[:70])); total += 1
                        if lv is None or v >= lv or v == 1: last[kd] = v
                        if kd in ("digit", "alpha") and v == 1: last = {kd: 1}
                if tt.count("(") != tt.count(")") and len(tt) > 40:
                    report.append((i, s["no"], f"unbalanced round brackets ({tt.count('(')} open, {tt.count(')')} closed)", tt[:70])); total += 1
                for r in re.findall(r"\bregulations?\s+(\d{1,3})\b(?![^.]{0,25}\b(?:of the Act|of the Companies|of the Ordinance|of the Securities))", tt):
                    if int(r) > maxn + 3 and maxn > 3 and act["unit"] == "Regulation":
                        report.append((i, s["no"], f"refers to regulation {r}, but the instrument ends at {maxn}", tt[:70])); total += 1
out = ["# Structure check of the converted instruments", "",
       "`python3 tools/ocr/structure_check.py`: places where the text's own structure suggests the OCR dropped a line (a gap in a list of labels, unbalanced brackets, a reference past the last provision). Leads to re-read against the scan, not proof of error.", "",
       f"{total} leads in {len(set(r[0] for r in report))} instruments.", "", "| Instrument | Provision | Lead | Text |", "|---|---|---|---|"]
for r in report: out.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3].replace('|','/')} |")
(ROOT / "docs/STRUCTURE_CHECK.md").write_text("\n".join(out) + "\n")
import collections
c = collections.Counter(r[0] for r in report); print(total, "leads; per instrument:", c.most_common(12))
