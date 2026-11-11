"""Map book pages (e.g. AI-162(82)) to OCR'd scan pages, from each page's running head.

usage: python3 tools/ocr/page_map.py <_ocr text folder> <out.json>
Also records the section/rule shown in the running head ("S. 225", "R. 7").
"""
import json, re, sys
from pathlib import Path
HEAD = re.compile(r"^\s*(AI|A1|Al|AL|I|II|III|IV|V|VA|VI|VII)\s*[-–]\s*(\d{1,4}[A-Z]?(?:\s*\(\s*[\dA-Z.]+\s*\))?)", re.M)
SEC = re.compile(r"\b(S|R|Reg)\s*\.\s*(\d{1,3}[A-Z]?)\b")
out = {}
for d in sorted(Path(sys.argv[1]).iterdir()):
    if not d.is_dir(): continue
    for f in sorted(d.glob("p[0-9][0-9][0-9][0-9].txt")):
        lines = f.read_text().splitlines()[:6]
        top = "\n".join(lines)
        m = HEAD.search(top)
        if not m: continue
        part = {"A1": "AI", "Al": "AI", "AL": "AI"}.get(m.group(1), m.group(1))
        pg = part + "-" + re.sub(r"\s", "", m.group(2))
        s = SEC.search(top)
        out.setdefault(pg, []).append({"file": d.name, "scan": int(f.stem[1:]), "head": s.group(0).replace(" ", "") if s else None})
json.dump(out, open(sys.argv[2], "w"), indent=0)
print(len(out), "book pages mapped")
