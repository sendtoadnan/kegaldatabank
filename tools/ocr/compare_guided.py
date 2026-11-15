"""Compare a library instrument with the book's text, guided by the library's own provisions.

usage: python3 tools/ocr/compare_guided.py <library id> <lines file> [--show NO ...]
The lines file is the converter's cleaned-lines debug output (BOOK_DEBUG=<dir>, <id>.lines.txt).
For each library provision (number + title) the heading is looked for in the book's lines, in order;
the words up to the next heading are compared with the library's words. Prints the provisions whose
wording differs and, with --show, the inserted/deleted words of those provisions.
"""
import difflib, json, re, sys

FN = re.compile(r"\{fn:[^}]+\}")
args = sys.argv[1:]
show = []
if "--show" in args:
    i = args.index("--show"); show = args[i + 1:]; args = args[:i]
lib_id, lines_file = args[0], args[1]
act = json.load(open(f"data/acts/{lib_id}.json"))
secs = [s for p in act["parts"] for s in p["sections"]]
L = [ln.split("\t", 2) for ln in open(lines_file).read().splitlines()]
def toks(t):
    t = FN.sub("", t).replace(">", " ")
    t = re.sub(r"[\[\]“”\"'’‘]", "", t).lower()
    return re.findall(r"[a-z0-9]+", t)
def key(title):
    return [w for w in toks(title) if len(w) > 2][:3]
heads, pos = [], 0
for s in secs:
    want = key(s["title"]); no = re.escape(s["no"])
    found = None
    for k in range(pos, len(L)):
        t = L[k][2]
        if not re.match(rf"^\W{{0,5}}\d?\W?{no}\s*[.,:]?\s*\W{{0,3}}[A-Za-z\[]", t) and not re.match(rf"^\W{{0,5}}{no}\b", t): continue
        head = " ".join(toks(" ".join(x[2] for x in L[k:k + 2]))[:14])
        if want and all(w in head for w in want):
            found = k; break
    heads.append(found)
    if found is not None: pos = found + 1
missing = [s["no"] for s, h in zip(secs, heads) if h is None]
print(f"{len(secs)} library provisions; heading not found in the book for: {missing}")
rows = []
for idx, s in enumerate(secs):
    h = heads[idx]
    if h is None: continue
    nxt = next((heads[j] for j in range(idx + 1, len(secs)) if heads[j] is not None), len(L))
    book = toks(" ".join(x[2] for x in L[h:nxt]))
    lib = toks(s["title"] + " " + " ".join(s["text"]))
    r = difflib.SequenceMatcher(None, lib, book, autojunk=False).ratio()
    rows.append((r, s["no"], s["title"], len(lib), len(book), lib, book))
rows.sort(key=lambda x: x[0])
print("provision | similarity | words library/book")
for r, no, title, a, b, _, _ in rows:
    print(f"  {no:5} {r:.2f}  {a:5}/{b:<5} {title[:48]}")
for r, no, title, a, b, lib, book in rows:
    if no in show:
        print(f"\n===== {no} {title}")
        sm = difflib.SequenceMatcher(None, lib, book, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal": continue
            print(f"  {op:7} library: {' '.join(lib[i1:i2])[:200]!r}   book: {' '.join(book[j1:j2])[:200]!r}")
