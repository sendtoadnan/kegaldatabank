"""Rebuild an instrument's text from the book, guided by the library's own provisions, and show old against new.

usage: python3 tools/ocr/guided_rebuild.py <library id> <filtered lines file> <scan pdf folder> --out <folder> [--pages "<file>:<scan>-<scan>" ...]
Needs the lines saved by `BOOK_LINES_OUT` (tools/ocr/book_to_json.py). For each library provision (number and title)
the heading is found in the book's lines, in order; the words up to the next heading become the new text.
Writes <out>/<id>.draft.json (the library's structure with new text only where the wording differs) and
<out>/index.html (old and new side by side, changed words marked) for a person to check before anything is replaced.
A provision is "unchanged" when the two wordings are at least 97% alike (the rest being OCR differences);
low similarity usually means a real amendment, but can also mean the segment was cut wrongly: those are flagged.
"""
import difflib, html, json, re, sys
from pathlib import Path

FN = re.compile(r"\{fn:[^}]+\}")
args = sys.argv[1:]
out = Path(args[args.index("--out") + 1]); out.mkdir(parents=True, exist_ok=True)
lib_id, lines_file = args[0], args[1]
act = json.load(open(f"data/acts/{lib_id}.json"))
secs = [(p, s) for p in act["parts"] for s in p["sections"]]
L = [ln.split("\t", 2) for ln in open(lines_file).read().splitlines()]

def toks(t):
    t = FN.sub("", t).replace(">", " ")
    t = re.sub(r"[\[\]“”\"'’‘]", "", t).lower()
    return re.findall(r"[a-z0-9]+", t)

# 1. find each heading, in order
heads, pos = [], 0
for p, s in secs:
    want = [w for w in toks(s["title"]) if len(w) > 2][:3]; no = re.escape(s["no"]); found = None
    for k in range(pos, len(L)):
        t = L[k][2]
        if not re.match(rf"^\W{{0,5}}\d?\W?{no}\s*[.,:]?\s*\W{{0,3}}[A-Za-z\[]", t) and not re.match(rf"^\W{{0,5}}{no}\b", t): continue
        head = " ".join(toks(" ".join(x[2] for x in L[k:k + 2]))[:14])
        if want and all(w in head for w in want): found = k; break
    heads.append(found)
    if found is not None: pos = found + 1
missing = [s["no"] for (p, s), h in zip(secs, heads) if h is None]
print(f"{len(secs)} library provisions; heading not found for {missing}")

# 2. where the last provision ends: the first schedule, form or annexure heading
STOP = re.compile(r"^[\W\d]{0,4}(?:[A-Za-z]{1,5}\.?[\s-]*)?(?:FORMS?|Forms?|ANNEXURES?|Annexures?|SCHEDULES?|Schedules?|APPENDI(?:X|CES)|Appendi(?:x|ces))\b[\s\-–—.:]*[A-Z0-9IVX\-]{0,8}\.?$")
last_head = max(h for h in heads if h is not None)
end_all = next((k for k in range(last_head + 1, len(L)) if STOP.match(L[k][2].strip()) and len(L[k][2]) < 40), len(L))

# 3. text of a segment -> paragraphs in the library's style
LABEL = re.compile(r"^(\(\s*(?:[a-z]{1,2}|[ivxlc]{1,6}|\d{1,3}[a-zA-Z]?|[A-Z])\s*\)|Explanation|Provided)")
NOTE_SENT = re.compile(r"[¡!'\"“]?\s*(?:Words?|Clauses?|Sub-?clauses?|Proviso|Provisos|Regulation|Explanation|Figures?|Brackets?|Item)\b[^.]{0,260}?\b(?:omitted|inserted|substituted|deleted|added)\b[•·\s]*(?:by|vide)\s+S\.?\s?R\.?\s?O\.?[^.]{0,40}?dated[^.]{0,30}?\d{4}\.?")
def clean(t):
    t = NOTE_SENT.sub(" ", t)
    t = re.sub(r"(?<![\w(])[0-9¹²³*'+°•]{1,2}\s?(?=\[)", "", t)           # note number before an amendment bracket
    t = re.sub(r"(?<=\s)\d{1,2}(?=[a-z])", "", t)                          # note number glued to a word: "6securities"
    t = re.sub(r"\s*\b[EB]2\s*\d{1,3}\s*[-.]\s*\d{1,2}\s*[-.]\s*\d{1,2}(?:[\s\-.:]*\d{1,4})?\b", " ", t)   # page code
    return re.sub(r"\s+", " ", t).strip()
CHAP = re.compile(r"^\W{0,3}CHAPTER\s+[IVXL]+\b|^\W{0,3}Chapter\s+[IVXL]+\b", re.I)
def level_of(label, st):
    """Nesting as the library writes it: (1) none, (a) one >, (i) two >>, (A) three >>>."""
    m = re.match(r"^\(\s*([A-Za-z0-9]+)\s*\)", label)
    if not m: return 0
    x = m.group(1)
    if x.isdigit() or re.fullmatch(r"\d+[a-z]", x): st["letter"] = None; return 0
    if x.isupper() and not re.fullmatch(r"[IVX]+", x): return 3
    if re.fullmatch(r"[a-z]", x) and (st.get("letter") is None or ord(x) == ord(st["letter"]) + 1): st["letter"] = x; return 1
    if re.fullmatch(r"[ivx]+", x): return 2
    if re.fullmatch(r"[a-z]{1,2}", x): st["letter"] = x[0]; return 1
    return 1
def paragraphs(seg):
    paras, skip = [], 0
    seg2 = []
    for i, t in enumerate(seg):                                  # chapter headings belong to the part, not the provision
        if skip: skip -= 1; continue
        if CHAP.match(t):
            skip = 1 if i + 1 < len(seg) and len(seg[i + 1]) < 70 and not re.search(r"[.;:]$", seg[i + 1]) else 0
            continue
        seg2.append(t)
    seg = seg2
    for t in seg:
        ends = not paras or re.search(r"([.:;\-–—\]\"”)]|\band|\bor)\s*$", paras[-1])
        if not paras or (LABEL.match(t) and ends): paras.append(t)
        else: paras[-1] = (paras[-1][:-1] if re.search(r"[a-z]-$", paras[-1]) else paras[-1] + " ") + t
    st, out = {}, []
    for x in paras:
        c = clean(x)
        if c: out.append(">" * level_of(c, st) + c)
    return out
def strip_heading(text, s):
    """Remove "N. Title.-" from the start of the first paragraph."""
    words = [re.escape(w) for w in re.findall(r"[A-Za-z0-9]+", re.sub(r"\{fn:[^}]+\}|\[|\]", "", s["title"]))][:12]
    rx = r"^\W{0,4}" + re.escape(s["no"]) + r"\W{0,3}\s*\W{0,3}" + r"\W{0,6}".join(words) + r"[\W_]{0,8}"
    new = re.sub(rx, "", text, count=1, flags=re.I)
    if new != text: return new
    # the title itself was amended: cut up to the first ".-" within the heading's length
    new = re.sub(r"^\W{0,4}" + re.escape(s["no"]) + r"[.,]\s*.{3,140}?[.:]\s*[-–—_]+\s*", "", text, count=1)
    return new if new != text else re.sub(r"^\W{0,4}" + re.escape(s["no"]) + r"[.,]\s*", "", text, count=1)

rows, draft = [], json.loads(json.dumps(act))
dsecs = [s for p in draft["parts"] for s in p["sections"]]
for idx, ((p, s), h) in enumerate(zip(secs, heads)):
    old = [FN.sub("", t) for t in s["text"]]
    if h is None:
        rows.append({"no": s["no"], "title": s["title"], "status": "heading not found", "sim": 0, "old": old, "new": [], "diff": "", "pages": []}); continue
    nxt = next((heads[j] for j in range(idx + 1, len(secs)) if heads[j] is not None), end_all)
    nxt = min(nxt, end_all)
    seg = [x[2] for x in L[h:nxt]]
    pages = list(dict.fromkeys(x[0] for x in L[h:nxt]))
    paras = paragraphs(seg)
    if paras: paras[0] = strip_heading(paras[0].lstrip(">"), s)
    paras = [x for x in paras if x]
    a, b = toks(" ".join(old)), toks(" ".join(paras))
    sim = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() if a and b else 0
    # word-level diff of the plain wording, marked for the page
    ow, nw = " ".join(old).split(), " ".join(paras).split()
    sm = difflib.SequenceMatcher(None, [w.lower() for w in ow], [w.lower() for w in nw], autojunk=False)
    parts = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal": parts.append(html.escape(" ".join(nw[j1:j2])))
        else:
            if i2 > i1: parts.append(f'<del>{html.escape(" ".join(ow[i1:i2]))}</del>')
            if j2 > j1: parts.append(f'<ins>{html.escape(" ".join(nw[j1:j2]))}</ins>')
    status = "unchanged" if sim >= 0.97 else ("changed" if sim >= 0.45 else "check: segment may be cut wrongly")
    rows.append({"no": s["no"], "title": s["title"], "status": status, "sim": sim, "old": old, "new": paras, "diff": " ".join(parts), "pages": pages})
    if status == "changed": dsecs[idx]["text"] = paras          # only genuinely different provisions take the new wording
json.dump(draft, open(out / f"{lib_id}.draft.json", "w"), indent=2, ensure_ascii=False)
json.dump([{k: v for k, v in r.items() if k != "diff"} for r in rows], open(out / f"{lib_id}.rows.json", "w"), indent=1, ensure_ascii=False)

# 4. the page for a person to check
by = {"unchanged": 0, "changed": 0}
for r in rows: by[r["status"]] = by.get(r["status"], 0) + 1
body = []
for r in rows:
    cls = {"unchanged": "same", "changed": "chg"}.get(r["status"], "chk")
    new = "".join(f"<p>{html.escape(x)}</p>" for x in r["new"]) or "<p><em>(nothing found)</em></p>"
    old = "".join(f"<p>{html.escape(x)}</p>" for x in r["old"])
    pg = " ".join(f'<a href="pages/{re.sub(r"[^A-Za-z0-9]+", "_", x)}.jpg" target="_blank">{html.escape(x)}</a>' for x in r["pages"])
    body.append(f'<section class="{cls}"><p class="pg">Book pages: {pg}</p><h3>{html.escape(r["no"])}. {html.escape(r["title"])} <small>{r["status"]} · similarity {r["sim"]:.2f}</small></h3>'
                f'<details {"open" if cls != "same" else ""}><summary>Changes marked (<del>old</del> / <ins>new</ins>)</summary><div class="diff">{r["diff"]}</div></details>'
                f'<div class="cols"><div><h4>Library now (SECP copy to 15 Sep 2021)</h4>{old}</div><div><h4>New (from the printed edition to 20 June 2026)</h4>{new}</div></div></section>')
(out / "index.html").write_text(f'''<!doctype html><meta charset="utf-8"><title>Update check: {html.escape(act["title"])}</title>
<style>body{{font:15px/1.5 Georgia,serif;max-width:1200px;margin:0 auto;padding:12px}}del{{background:#fbd5d5;text-decoration:line-through}}ins{{background:#cdeccd;text-decoration:none}}
section{{border:1px solid #ccc;border-radius:8px;margin:10px 0;padding:8px 12px}}.same{{opacity:.6}}.chk{{border-color:#c33}}.chg{{border-color:#393}}small{{font:12px sans-serif;color:#555}}
.pg{{font:12px sans-serif;float:right;margin:0}}.cols{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.diff{{padding:6px;background:#fafafa}}h4{{font:13px sans-serif;margin:6px 0}}header{{font:14px sans-serif}}</style>
<header><h1>{html.escape(act["title"])}: library against the printed edition</h1>
<p>{len(rows)} provisions: <b>{by.get("unchanged",0)}</b> unchanged, <b>{by.get("changed",0)}</b> changed, <b>{len(rows)-by.get("unchanged",0)-by.get("changed",0)}</b> to check. Nothing has replaced the library's text. Green borders: wording differs and looks like a real amendment. Red borders: the new text could not be matched cleanly (check against the scan). OCR slips appear as small word differences.</p></header>
{"".join(body)}''')
print({k: v for k, v in by.items()}, "->", out / "index.html")
