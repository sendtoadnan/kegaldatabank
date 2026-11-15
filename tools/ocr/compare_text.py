"""Compare a library instrument with the book's version of it, provision by provision.

usage: python3 tools/ocr/compare_text.py <library id> <converted json>
Prints provisions only in one of them and those whose wording differs (word-level similarity),
with a short view of what changed. Library footnote markers {fn:..} and the ">" list marker are ignored.
"""
import difflib, json, re, sys
FN = re.compile(r"\{fn:[^}]+\}")
def words(sec):
    t = " ".join(sec["text"]); t = FN.sub("", t).replace(">", " ")
    t = re.sub(r"[\[\]“”\"'’‘]", "", t).lower()
    return re.findall(r"[a-z0-9]+", t)
def load(p):
    a = json.load(open(p)); d = {}
    for pt in a["parts"]:
        for s in pt["sections"]: d[s["no"]] = s
    return a, d
lib, L = load(f"data/acts/{sys.argv[1]}.json")
bk, B = load(sys.argv[2])
print(f"library {len(L)} provisions, book {len(B)}")
print("only in library:", [n for n in L if n not in B])
print("only in book:   ", [n for n in B if n not in L])
rows = []
for n in L:
    if n not in B: continue
    a, b = words(L[n]), words(B[n])
    r = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() if a and b else (1.0 if not a and not b else 0.0)
    rows.append((r, n, len(a), len(b)))
rows.sort()
print("most different (similarity, provision, words lib/book):")
for r, n, la, lb in rows[:40]: print(f"  {r:.2f}  {n:6} {L[n]['title'][:44]:44} {la}/{lb}")
print("provisions >= 0.97 similar:", sum(1 for r, *_ in rows if r >= 0.97), "of", len(rows))
