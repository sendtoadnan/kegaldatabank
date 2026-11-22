"""Hand-guided build of the Prudential Regulations for NBFCs from the saved cleaned lines of the older (Dec 2021) scan.

usage: python3 tools/ocr/prudential_build.py <lines file> <out json> [<spec json>]
The generic converter cannot read these regulations: numbering restarts in each Part, and a table and an inserted circular
sit inside Part III. This script cuts the lines by the Part and regulation headings found by hand (line numbers below refer to
the saved lines file) and writes data/acts/prudential-regulations-nbfc.json. Provision numbers are "<Part>.<regulation>".
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
lines = [l.split("\t", 2) for l in Path(sys.argv[1]).read_text().splitlines()]
T = [l[2] for l in lines]
N = len(T)

def clean(rng):
    out = []
    for t in rng:
        t = t.strip()
        if out and out[-1] == t and len(t) >= 4: continue
        if re.fullmatch(r"\(\d\)( \(\d\))+", t) or re.match(r"^SECP Cir\. ?\d+ of 20\S+ Part V", t): continue
        if not t or t == "•" or t == "Regulations for NBFCs" or re.fullmatch(r"[Vv][\s.\-_]*[0-9lI]{1,3}", t): continue
        if re.match(r"^Prudential Regulations for (NBFC|Non-Banking)", t) and len(t) < 70: continue
        if re.match(r"^Part\s*[IVX]+,\s*Reg", t): continue
        out.append(t)
    # a bare label line followed by its own full line
    res = []
    for i, t in enumerate(out):
        if re.fullmatch(r"\(?[0-9a-z]{1,4}\)", t) and i + 1 < len(out) and out[i + 1].startswith(t): continue
        if res and res[-1] == t and len(t) < 90 and not re.match(r"^\(", t) is None and False: continue
        res.append(t)
    return res

ROMAN = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"}
NUMBERED = False
def paras(rng):
    ps = []; ctx = None
    for t in rng:
        if re.match(r"^['`]?\[?Regulation 8 of Section B", t):
            ps.append("Regulation 8 of Section B of Part II of the Prudential Regulations for NBFCs"); continue
        if NUMBERED and re.match(r"^\d{1,2}\. [A-Z]", t): ps.append(t); continue
        if t.startswith("*"): ps.append(t); continue
        m2 = re.match(r"^([a-z])\)\s+(.*)", t)
        if m2: ps.append(f">({m2.group(1)}) {m2.group(2)}"); continue
        if re.match(r"^[ivx]+\.\s", t): ps.append(">>" + t); continue
        m = re.match(r"^\(?(\d+|[a-z]{1,4})\)\s*", t) if re.match(r"^\(", t) else None
        if m:
            lab = m.group(1)
            if lab.isdigit(): pre = ""; ctx = None
            else:
                nxt = (ctx or "")
                roman = lab in ROMAN and not (lab == "i" and ctx == "h") and not (lab == "v" and ctx == "u")
                pre = ">>" if roman and ctx else ">"
                if not roman: ctx = lab
            ps.append(pre + t)
        elif re.match(r"^(Provided|Explanation|Notes?:|Illustration)", t) or re.match(r"^\d+\. [A-Z]", t) and False:
            ps.append(t)
        elif ps and not re.search(r"[.;:]\s*$", ps[-1]) or (ps and re.match(r"^[a-z(,]", t)):
            ps[-1] += " " + t
        elif ps and len(ps[-1]) and ps[-1][-1] in ".;:" and not re.match(r"^[A-Z(\"'0-9]", t):
            ps[-1] += " " + t
        elif ps and ps[-1].endswith((".", ";", ":")) :
            ps.append(t)
        else:
            ps.append(t)
    return ps

def tidy(ps):
    out = []
    for p in ps:
        p = re.sub(r"^(>*)['`’‘]\s?\[", r"\1", p)
        p = re.sub(r"^(>*)\[", r"\1", p)
        if p.count("]") > p.count("["): p = re.sub(r"\]\s*$", "", p) if p.rstrip().endswith("]") else p
        p = re.sub(r"\s+", " ", p).strip().replace("NBFC thall", "NBFC shall")
        if p: out.append(p)
    return out

def sec(no, title, a, b, first=None, drop=()):
    rng = clean([t for i, t in enumerate(T[a:b], a) if i not in drop])
    if first is not None and rng: rng[0] = first
    return {"no": no, "title": title, "text": tidy(paras(rng))}

spec = json.load(open(sys.argv[3] if len(sys.argv) > 3 else ROOT / "tools/ocr/prudential_spec.json"))
parts = []
for P in spec["parts"]:
    secs = []
    for s in P["sections"]:
        a, b = s["lines"]
        first = s.get("first")
        seg = clean([t for t in T[a - 1:b - 1]])
        if s.get("skip"):                     # (from, to) 1-based file line ranges replaced by a note
            skip = s["skip"]
            keep = [t for i, t in enumerate(T[a - 1:b - 1], a) if not (skip[0] <= i < skip[1])]
            seg = clean(keep)
            ins = clean(T[skip[1] - 1:skip[1]])
        if s.get("heading", True):
            for k in range(min(3, len(seg))):
                if ".-" in seg[k]:
                    seg = [seg[k].split(".-", 1)[1].strip()] + seg[k + 1:]; break
        NUMBERED = bool(s.get("numbered"))
        ps = paras(seg)
        if s.get("prefix"): ps.insert(0, s["prefix"])
        if ps and ps[0].startswith("Definitions. "): ps[0] = ps[0][len("Definitions. "):]
        ps = tidy(ps)
        if s.get("skip"):
            k = s["noteAt"] if "noteAt" in s else next((i for i, p in enumerate(ps) if p.startswith("Notes:")), len(ps))
            TB = json.load(open(ROOT / "tools/ocr/prudential_tables.json")).get(s["no"])
            ps[k:k] = TB if TB else [s["note"]]
            if TB and s["no"] == "E.5": ps = [p for p in ps if not p.startswith("*This specific provision will be in addition") or p in TB]
            elif TB: pass
        secs.append({"no": s["no"], "title": s["title"], "text": ps})
    parts.append({"heading": P["heading"], "sections": secs})
Path(sys.argv[2]).write_text(json.dumps(parts, indent=1, ensure_ascii=False))
print(sum(len(p["sections"]) for p in parts), "provisions")
