"""Read a multi-column table by OCR'ing each column strip separately (the page-wide OCR mixes the columns).

usage: python3 tools/ocr/table_columns.py --vocr <vision_ocr> <pdf> <spec.json> <out.json>
spec: list of {"page": n (1-based), "y": [y0, y1] (0-1), "cols": [x0, x1, x2, ...]} per table page, in reading order.
Writes {"cols": [[text lines of column 1 across all pages], ...]} for hand-guided row splitting.
"""
import json, os, subprocess, sys, tempfile
import fitz
vocr, pdf, spec, out = sys.argv[2], sys.argv[3], json.load(open(sys.argv[4])), sys.argv[5]
d = fitz.open(pdf)
ncol = len(spec[0]["cols"]) - 1
cols = [[] for _ in range(ncol)]
with tempfile.TemporaryDirectory() as tmp:
    for s in spec:
        p = d[s["page"] - 1]; r = p.rect
        for c in range(ncol):
            clip = fitz.Rect(r.width * s["cols"][c], r.height * s["y"][0], r.width * s["cols"][c + 1], r.height * s["y"][1])
            f = os.path.join(tmp, f"{s['page']}_{c}.png")
            p.get_pixmap(dpi=300, clip=clip, colorspace=fitz.csGRAY).save(f)
            txt = subprocess.run([vocr, f], capture_output=True, text=True).stdout
            cols[c].append({"page": s["page"], "text": [l for l in txt.split("\n")[1:] if l.strip()]})
json.dump({"cols": cols}, open(out, "w"), indent=1, ensure_ascii=False)
