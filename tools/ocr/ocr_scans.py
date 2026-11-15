"""OCR image-only scan PDFs page by page with Apple Vision (tools/ocr/vision_ocr.swift).

usage: python3 tools/ocr/ocr_scans.py --vocr <compiled vision_ocr> --out <text folder> [--pages 0-39] file.pdf ...
Writes <out>/<pdf stem>/p0001.txt ... (1-based page numbers); pages already done are skipped.
"""
import argparse, os, subprocess, sys, tempfile
from pathlib import Path
import fitz

ap = argparse.ArgumentParser()
ap.add_argument("--vocr", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--pages", help="0-based range a-b")
ap.add_argument("--dpi", type=int, default=200)
ap.add_argument("pdfs", nargs="+")
a = ap.parse_args()

for pdf in a.pdfs:
    d = fitz.open(pdf)
    rel = Path(pdf).parent.name + " - " + Path(pdf).stem
    dest = Path(a.out) / rel
    dest.mkdir(parents=True, exist_ok=True)
    lo, hi = (map(int, a.pages.split("-")) if a.pages else (0, len(d) - 1))
    todo = [i for i in range(lo, min(hi, len(d) - 1) + 1) if not (dest / f"p{i+1:04d}.txt").exists()]
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(0, len(todo), 20):
            batch = todo[k:k + 20]
            imgs = []
            for i in batch:
                f = os.path.join(tmp, f"p{i+1:04d}.png")
                d[i].get_pixmap(dpi=a.dpi, colorspace=fitz.csGRAY).save(f)
                imgs.append(f)
            out = subprocess.run([a.vocr, *imgs], capture_output=True, text=True).stdout
            for chunk in out.split("=== ")[1:]:
                head, _, body = chunk.partition("\n")
                (dest / (Path(head).stem + ".txt")).write_text(body)
            for f in imgs: os.remove(f)
            print(f"{rel}: {batch[-1]+1}/{len(d)}", file=sys.stderr, flush=True)
