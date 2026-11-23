"""Parse the State Bank's Foreign Exchange Manual chapters (PDF text layer) into parts of numbered paragraphs.

usage: python3 tools/fe_manual.py <folder with Chapter-N.pdf> <out.json> [--report]
Each chapter is a part; each numbered paragraph ("1. Title." and its text) is a provision numbered "<chapter>.<n>".
The chapter's own contents list (when it has one) is used to confirm paragraph numbers and titles; the Appendices,
Annexures and forms (separate files) are not read here.
"""
import fitz, re, sys, json
from pathlib import Path
R = Path(sys.argv[1]); OUT = sys.argv[2]
def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())
def page_lines(ch):
    d = fitz.open(R / f"Chapter-{ch}.pdf"); out = []
    for p in d:
        L = [re.sub(r"\s+", " ", l).strip() for l in p.get_text().split("\n")]
        k = 0
        while k < len(L) and not L[k]: k += 1
        if k < len(L) and re.fullmatch(r"\d{1,3}", L[k]): L[k] = ""        # page number at the top
        L = [l for l in L if l]
        if L and re.fullmatch(r"(Chapter|CHAPTER)?\s*\d{1,2}\s*[-–]?\s*\d{0,3}", L[-1]) and len(L[-1]) < 8: L = L[:-1]
        out += L
    return out
ITEM = re.compile(r"^(\d{1,2}[A-Z]{0,2})\.?\s*(.*)$")
def base(n): return int(re.match(r"\d+", n).group())
def suffix(n): return re.sub(r"^\d+", "", n)
def expected(prev, n):
    if prev is None: return n == "1"
    bp, sp = base(prev), suffix(prev); bn, sn = base(n), suffix(n)
    return (bn == bp + 1 and sn == "") or (bn == bp and sn and (len(sn) == len(sp) and ord(sn[-1]) == ord(sp[-1]) + 1 or (not sp and sn == "A")))
def chapter(ch):
    L = page_lines(ch)
    i = 0; title = []
    while i < len(L) and not (re.match(r"^1\.?(\s|$)", L[i]) and not L[i].lower().startswith("1. contents")):
        if not re.match(r"^Contents", L[i], re.I): title.append(L[i])
        i += 1
    contents = []; prev = None; cur = None
    while i < len(L):
        m = ITEM.match(L[i])
        if m and expected(prev, m.group(1)) and (m.group(2) or L[i].rstrip().endswith(".")):
            prev = m.group(1); cur = [prev, m.group(2)]; contents.append(cur)
        elif m and m.group(1) == "1" and contents and prev not in (None, "1") and len(contents) > 1: break
        elif cur is not None and (not m or not expected(prev, m.group(1))) and (cur[1] == "" or not cur[1].endswith(".")) and not re.match(r"^Part[- ]", L[i]): cur[1] = (cur[1] + " " + L[i]).strip()
        elif cur is not None and (not m or not expected(prev, m.group(1))): pass          # group headings such as "Part-A" or a continued title line
        else: break
        i += 1
    return title, contents, L, i
def parse(ch):
    title, contents, L, b = chapter(ch)
    heads = []; k = b; miss = []
    for no, ttl in contents:
        want = norm(ttl)[:10]; found = None; j = k
        while j < len(L):
            m = ITEM.match(L[j])
            if m and m.group(1) == no and (norm(m.group(2) + " " + " ".join(L[j + 1:j + 3]))[:60].find(want) in (0, 1, 2, 3, 4, 5) or want in norm(m.group(2) + " " + " ".join(L[j + 1:j + 3]))[:40]):
                found = j; break
            j += 1
        if found is None:                                   # title not matched: take the next line that is just the number
            j = k
            while j < len(L):
                m = ITEM.match(L[j])
                if m and m.group(1) == no and not m.group(2): found = j; break
                j += 1
        if found is None: miss.append(no); heads.append(None)
        else: heads.append(found); k = found + 1
    secs = []; valid = [h for h in heads if h is not None]
    for idx, (no, ttl) in enumerate(contents):
        h = heads[idx]
        if h is None: continue
        nxt = next((x for x in heads[idx + 1:] if x is not None), len(L))
        m = ITEM.match(L[h]); first = m.group(2).strip(); body = L[h + 1:nxt]
        # drop the title when it was repeated at the start of the body
        tn = norm(ttl)
        joined = first
        while body and len(norm(joined)) < len(tn) and norm(joined + " " + body[0]) and tn.startswith(norm(joined + " " + body[0])[:len(tn)]):
            joined += " " + body.pop(0)
        if norm(joined).startswith(tn[:25]) and len(norm(joined)) <= len(tn) + 2: first = ""
        elif norm(first).startswith(tn[:25]): first = first[len(ttl):].strip() if first.startswith(ttl) else first
        else: first = first if not (len(norm(first)) < len(tn) and tn.startswith(norm(first))) else ""
        lines = ([first] if first else []) + body
        paras = []
        for l in lines:
            lab = re.match(r"^\(([a-z]{1,4}|[ivx]+|\d{1,2})\)\s", l)
            if lab or not paras: paras.append((">" if lab and re.match(r"^\([a-z]\)", l) and not re.match(r"^\((i|v|x)\)", l) else "") + l)
            else: paras[-1] += " " + l
        secs.append({"no": f"{ch}.{no}", "title": ttl.rstrip("."), "text": paras or [ttl]})
    return " ".join(title), contents, secs, miss
parts = []; rep = []
for ch in range(1, 23):
    t, c, s, miss = parse(ch)
    parts.append({"heading": f"Chapter {ch} — {t.title()}" if t else f"Chapter {ch}", "sections": s})
    rep.append((ch, t[:40], len(c), len(s), miss))
json.dump(parts, open(OUT, "w"), indent=1, ensure_ascii=False)
for r in rep: print(r)
