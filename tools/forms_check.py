#!/usr/bin/env python3
"""Check the per-form PDF and Word files made by tools/forms_export.py; with --fix, drop the Word file where it is not a fair copy.

usage: <venv with pdf2docx + pymupdf>/bin/python tools/forms_check.py [--fix]
Every PDF must open and have the recorded page count. A Word file must open as a valid .docx and carry at least 85% of the words
on the PDF's pages (counting text in boxes too). Scanned pages get an OCR copy from tools/forms_word.py, marked "ocr" and skipped here. --fix deletes the Word
files that fail and removes them from sources/forms/index.json, so the site offers the PDF only for those forms.
"""
import fitz, json, re, sys, zipfile
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; F = ROOT / "sources" / "forms"
W = lambda s: re.findall(r"[^\W_]+", s.lower())
idx = json.loads((F / "index.json").read_text()); bad = []; n = 0
for iid, forms in idx.items():
    for k, f in forms.items():
        n += 1
        try:
            doc = fitz.open(F / f["pdf"]); assert len(doc) == f["pages"], "page count"
            a = Counter(w for pg in doc for w in W(pg.get_text()))
        except Exception as e:
            print("PDF problem:", iid, k, e); continue
        if "docx" not in f or f.get("docxNote") == "ocr": continue         # (OCR copies of scans have no text layer to compare with)
        try:
            zipfile.ZipFile(F / f["docx"]).testzip()
            b = Counter(W(" ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", zipfile.ZipFile(F / f["docx"]).read("word/document.xml").decode("utf8")))))
            tot = sum(a.values()); miss = sum((a - b).values()) / tot if tot else 1
            ok = tot > 0 and miss <= 0.15
        except Exception as e:
            ok = False; miss = 1
        if not ok: bad.append((iid, k, f, round(miss, 2)))
print(n, "forms;", len(bad), "Word files not a fair copy")
for iid, k, f, m in bad:
    print("  ", iid, k, f["docx"], m)
    if "--fix" in sys.argv:
        (F / f["docx"]).unlink(missing_ok=True); f.pop("docx")
if "--fix" in sys.argv: (F / "index.json").write_text(json.dumps(idx, indent=1, ensure_ascii=False) + "\n")
