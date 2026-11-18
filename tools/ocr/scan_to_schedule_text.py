"""Make a scan-only instrument searchable: OCR text of each PDF page -> data/schedule-text/<id>.json.

usage: python3 tools/ocr/scan_to_schedule_text.py <id> <ocr folder from ocr_scans.py>
One entry per PDF page ("Scanned page N"), so search results link to that page of the official PDF.
The OCR text is for finding the page only; it is not shown as the law's text and is not used for AI passages.
Re-run after replacing the PDF (and ocr_scans.py again). Apple Vision: see tools/ocr/ocr_scans.py.
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
i, folder = sys.argv[1], Path(sys.argv[2])
sub = [d for d in folder.iterdir() if d.is_dir()][0] if not list(folder.glob("p*.txt")) else folder
out = []
for f in sorted(sub.glob("p*.txt")):
    n = int(f.stem[1:])
    t = re.sub(r"\s+", " ", f.read_text()).strip()
    if t: out.append({"title": f"Scanned page {n}", "page": n, "text": t})
(ROOT / "data/schedule-text" / f"{i}.json").write_text(json.dumps({"id": i, "pdfOnly": True, "schedules": out}, ensure_ascii=False, separators=(",", ":")))
print(i, len(out), "pages,", sum(len(x["text"].split()) for x in out), "words")
