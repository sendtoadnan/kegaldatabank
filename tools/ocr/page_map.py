"""Map book pages (e.g. AI-162(82)) to OCR'd scan pages, from each page's running head.

usage: python3 tools/ocr/page_map.py <_ocr text folder> <out.json>
Also records the section/rule shown in the running head ("S. 225", "R. 7").
"""
import json, re, sys
from pathlib import Path
HEAD = re.compile(r"^\s*(AI|A1|Al|AL|I|II|III|IV|V|VA|VI|VII)\s*[-–]\s*(\d{1,4}[A-Z]?(?:\s*\(\s*[\dA-Z.]+\s*\))?)", re.M)
SEC = re.compile(r"\b(S|R|Reg)\s*\.\s*(\d{1,3}[A-Z]?)\b")
out, fixed = {}, 0
def plain(pg):
    m = re.fullmatch(r"([A-Z]+)-(\d+)", pg or ""); return (m.group(1), int(m.group(2))) if m else None
for d in sorted(Path(sys.argv[1]).iterdir()):
    if not d.is_dir(): continue
    seq = []
    for f in sorted(d.glob("p[0-9][0-9][0-9][0-9].txt")):
        lines = f.read_text().splitlines()[:8]
        top = "\n".join(lines)
        norm = "\n".join(re.sub(r"^[\s|•.]+", "", l) for l in lines)
        norm = re.sub(r"(?m)^[IlШП1|]{3}(?=\s*[-–]\s*\d)", "III", norm)
        norm = re.sub(r"(?m)^(?:ШII|ШI|ПI|IlI|lII|IIl|Ill|lll|I1I|1II|II1)(?=\s*[-–]\s*\d)", "III", norm)
        m = HEAD.search(norm)
        s = SEC.search(top)
        pg = None
        if m:
            part = {"A1": "AI", "Al": "AI", "AL": "AI"}.get(m.group(1), m.group(1))
            pg = part + "-" + re.sub(r"\s", "", m.group(2))
        seq.append([f, pg, s.group(0).replace(" ", "") if s else None, bool(top.strip())])
    # a part that is a misreading of the file's main part (II/I for III) takes the main part
    from collections import Counter
    main = Counter(x[1].split("-")[0] for x in seq if x[1]).most_common(1)
    main = main[0][0] if main else None
    for x in seq:
        if x[1] and main and x[1].split("-")[0] != main and x[1].split("-")[0] in ("I", "II", "III") and main in ("II", "III") and len(x[1].split("-")[0]) < len(main):
            x[1] = main + "-" + x[1].split("-", 1)[1]; fixed += 1
    # repair from sequence: a text page between X-n and X-(n+2) is X-(n+1)
    for i in range(1, len(seq) - 1):
        a_, b_ = plain(seq[i - 1][1]), plain(seq[i + 1][1])
        if not (a_ and b_ and a_[0] == b_[0] and b_[1] == a_[1] + 2 and seq[i][3]): continue
        want = f"{a_[0]}-{a_[1] + 1}"
        if seq[i][1] != want and not re.search(r"\(", seq[i][1] or ""):
            seq[i][1] = want; fixed += 1
    # longer gaps: k text pages between X-a and X-(a+k+1) take the numbers in order
    anchors = [i for i, x in enumerate(seq) if plain(x[1])]
    for i, j in zip(anchors, anchors[1:]):
        a_, b_ = plain(seq[i][1]), plain(seq[j][1])
        mid = [k for k in range(i + 1, j) if seq[k][3]]
        if a_[0] == b_[0] and b_[1] - a_[1] - 1 == len(mid) and mid and all(not plain(seq[k][1]) or plain(seq[k][1]) != (a_[0], a_[1] + n + 1) for n, k in enumerate(mid)):
            if all(seq[k][1] is None or re.fullmatch(r"[A-Z]+-\d+", seq[k][1] or "") for k in mid):
                for n, k in enumerate(mid): seq[k][1] = f"{a_[0]}-{a_[1] + n + 1}"; fixed += 1
    for f, pg, head, _ in seq:
        if pg: out.setdefault(pg, []).append({"file": d.name, "scan": int(f.stem[1:]), "head": head})
json.dump(out, open(sys.argv[2], "w"), indent=0)
print(len(out), "book pages mapped;", fixed, "running heads repaired from sequence")
