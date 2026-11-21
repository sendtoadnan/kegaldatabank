"""Build data/comparison/companies-ordinance-1984.json from three inputs:
  1. the book's table of corresponding provisions (data/salam/corresponding-provisions.json; 2017 ss.221-267, 415-515 held),
  2. a second printed comparison with a text layer (rows from tools/ocr/comparative_index_pdf.py; all sections),
  3. the Ordinance's own contents list (headings), from its PDF.

usage: python3 tools/ocr/build_comparison.py <comparative-index rows.json> <Ordinance 1984 PDF>
Where both sources cover a section and agree, it is shown plainly; where they differ, the book's pairing is shown with the other source's
beside it ("differs"); elsewhere the second source alone is used. Nothing is guessed.
"""
import collections, json, re, sys
from pathlib import Path
import fitz
ROOT = Path(__file__).resolve().parents[2]
rows = json.load(open(sys.argv[1])); pdf = sys.argv[2]
ACT = json.load(open(ROOT / "data/acts/companies-act-2017.json")); ORDER = [s["no"] for p in ACT["parts"] for s in p["sections"]]
def key(n): m = re.match(r"(\d+)(.*)", n); return (int(m.group(1)), re.sub(r"\(.*", "", m.group(2)))
# second source -> pairs
dl = collections.OrderedDict(); prev = None
for r in rows:
    a, o, at = r["act"]["n"], r["ordinance"]["n"], r["act"]["t"]
    if a: dl.setdefault(a, []); dl[a] += o; prev = a
    elif re.match(r"^(No provision|No separate|No corresponding)", at): pass
    elif prev and o: dl[prev] += o
# the Ordinance's headings from its contents pages
d = fitz.open(pdf); lines = []
for pn in range(0, 24):
    t = d[pn].get_text()
    if "CONTENTS" in t.upper() or re.search(r"\n\d{1,3}[A-Z]?\.\s*\n", t): lines += [l.strip() for l in t.split("\n")]
heads, cur, buf = {}, None, []
def flush():
    global cur, buf
    if cur and buf and cur not in heads: heads[cur] = re.sub(r"\s+", " ", " ".join(buf)).strip(" .")
    cur, buf = None, []
for l in lines:
    m = re.match(r"^(\d{1,3}[A-Z]{0,3})\.$", l)
    if m: flush(); cur = m.group(1); continue
    if cur is None: continue
    if re.fullmatch(r"\d{1,3}", l): flush(); continue
    if l: buf.append(l)
flush()
book = json.load(open(ROOT / "data/salam/corresponding-provisions.json"))
bk = collections.OrderedDict()
for r in book["rows"]:
    if r["act2017"]:
        bk.setdefault(r["act2017"], [])
        if r["ordinance1984"] and r["ordinance1984"] not in bk[r["act2017"]]: bk[r["act2017"]].append(r["ordinance1984"])
base = lambda n: re.sub(r"\(.*", "", n)
pairs, diff = [], 0
for a in ORDER:
    b, s = bk.get(a), dl.get(a)
    s = sorted(dict.fromkeys(base(x) for x in s), key=key) if s is not None else None
    if b is not None and s is not None:
        if set(b) == set(s): pairs.append({"a": a, "o": s, "src": "both"})
        else: pairs.append({"a": a, "o": sorted(b, key=key), "alt": s, "src": "differs"}); diff += 1
    elif s is not None: pairs.append({"a": a, "o": s, "src": "index"})
    elif b is not None: pairs.append({"a": a, "o": sorted(b, key=key), "src": "book"})
used = {x for p in pairs for x in p["o"] + p.get("alt", [])}
unmatched = [n for n in sorted(heads, key=key) if n not in used]
titles = {n: heads[n] for n in used if n in heads}
out = {"act": "companies-act-2017", "otherTitle": "Companies Ordinance, 1984",
 "_about": "For each section of the Companies Act, 2017, the section of the Companies Ordinance, 1984 that deals with the same matter, read from two printed comparisons (where they differ, both are shown); the Ordinance's section headings are from its own contents list. The Ordinance was repealed by the Act, except Part VIIIA. A dash means the Ordinance has no counterpart (the section of the Act is new).",
 "status": "unverified", "coverage": [["1", ORDER[-1]]], "sources": "both = the two comparisons agree; differs = they differ (book first, other beside it); index = one comparison only (the book's pages are not held for these sections).",
 "missing": "Sections 60A, 83A, 123A and 458A (added by later amendments) are not in either comparison.",
 "titles": titles, "pairs": pairs, "unmatchedOrdinance": unmatched}
json.dump(out, open(ROOT / "data/comparison/companies-ordinance-1984.json", "w"), ensure_ascii=False, indent=1)
c = collections.Counter(p["src"] for p in pairs)
print(len(pairs), "sections:", dict(c), "| ordinance headings:", len(heads), "| not matched to any section:", len(unmatched))
