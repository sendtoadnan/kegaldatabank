"""OCR chosen pages keeping each line's position (for indexes and tables).

usage: python3 tools/ocr/ocr_boxes.py --vocr <vision_ocr> --out <text folder> file.pdf 87,88,89-91
Writes <out>/<pdf parent> - <stem>/p0087.boxes.tsv: x0 y0 x1 y1 (0-1, top-left origin) TAB text.
"""
import argparse, os, subprocess, tempfile
from pathlib import Path
import fitz

ap = argparse.ArgumentParser()
ap.add_argument("--vocr", required=True); ap.add_argument("--out", required=True)
ap.add_argument("pdf"); ap.add_argument("pages")
a = ap.parse_args()
pages = []
for part in a.pages.split(","):
    lo, _, hi = part.partition("-"); pages += range(int(lo), int(hi or lo) + 1)
d = fitz.open(a.pdf)
dest = Path(a.out) / (Path(a.pdf).parent.name + " - " + Path(a.pdf).stem); dest.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    imgs = []
    for p in pages:
        f = os.path.join(tmp, f"p{p:04d}.png"); d[p - 1].get_pixmap(dpi=250, colorspace=fitz.csGRAY).save(f); imgs.append(f)
    for k in range(0, len(imgs), 20):
        out = subprocess.run([a.vocr, "--boxes", *imgs[k:k+20]], capture_output=True, text=True).stdout
        for chunk in out.split("=== ")[1:]:
            head, _, body = chunk.partition("\n")
            (dest / (Path(head).stem + ".boxes.tsv")).write_text(body)
print(len(imgs), "pages")
