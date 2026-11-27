#!/usr/bin/env python3
"""Make a Word copy of a form PDF without pdf2docx: its tables become Word tables, its text Word paragraphs, page by page
(landscape pages stay landscape). Scanned pages (no text layer) are read by OCR (macOS Vision, scripts/ocr_pdf.swift compiled to
a binary) and written as paragraphs; those copies are marked "ocr" in sources/forms/index.json and must be checked against the PDF.

usage: <venv>/bin/python tools/forms_word.py --ocr <binary> [<id>:<n> ...]     (default: the forms that have no Word file yet)
Needs pymupdf (1.23.x) and python-docx. A copy is kept only when it carries at least 90% of the PDF's words (text layer) or 20+ words (OCR).
"""
import fitz, json, re, subprocess, sys, tempfile, zipfile
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_tables import find_tables
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Emu

ROOT = Path(__file__).resolve().parent.parent; F = ROOT / "sources" / "forms"
W = lambda s: re.findall(r"[^\W_]+", s.lower())
CLEAN = lambda s: re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]", "", s)
OCR = sys.argv[sys.argv.index("--ocr") + 1] if "--ocr" in sys.argv else None


def page_items(pg):
    """Tables and paragraphs of one page, in reading order: [(y, 'p', text, size, bold, centred) | (y, 't', rows)]"""
    Wd = pg.rect.width; tabs = find_tables(pg, strict=False)
    inside = lambda b: any(t["x0"] - 3 <= b[0] and b[2] <= t["x1"] + 3 and t["y0"] - 3 <= b[1] and b[3] <= t["y1"] + 3 for t in tabs)
    items = [(t["y0"], "t", t["rows"]) for t in tabs]; lines = []
    for b in pg.get_text("dict")["blocks"]:
        if b.get("type") != 0: continue
        for ln in b["lines"]:
            sp = [s for s in ln["spans"] if s["text"].strip()]
            txt = re.sub(r"\s+", " ", "".join(s["text"] for s in ln["spans"])).strip()
            if not txt or not sp or inside(ln["bbox"]): continue
            x0, y0, x1, y1 = ln["bbox"]
            lines.append((y0, y1, x0, x1, txt, sp[0]["size"], bool(sp[0]["flags"] & 16)))
    lines.sort(); cur = None
    for y0, y1, x0, x1, txt, size, bold in lines:
        if cur and abs(y0 - cur["y0"]) < 0.4 * size:                       # same visual line (text in two boxes)
            cur["txt"] += " " + txt; cur["x1"] = max(cur["x1"], x1); continue
        if cur and y0 - cur["y1"] < 0.7 * size and not re.match(r"^(\(\w{1,4}\)|\d{1,3}\.)", txt) and abs(size - cur["size"]) < 0.5 and abs((cur["x0"] + cur["x1"]) / 2 - Wd / 2) > 0.03 * Wd:
            cur["txt"] += " " + txt; cur["y1"] = y1; cur["x1"] = max(cur["x1"], x1); continue
        if cur: items.append((cur["y0"], "p", cur["txt"], cur["size"], cur["bold"], cur["c"]))
        cur = {"y0": y0, "y1": y1, "x0": x0, "x1": x1, "txt": txt, "size": size, "bold": bold, "c": False}
        cur["c"] = abs((x0 + x1) / 2 - Wd / 2) < 0.03 * Wd and (x1 - x0) < 0.8 * Wd
    if cur: items.append((cur["y0"], "p", cur["txt"], cur["size"], cur["bold"], cur["c"]))
    items.sort(key=lambda i: i[0])
    return items


def ocr_lines(pdf):
    out = Path(tempfile.mkstemp(suffix=".txt")[1])
    subprocess.run([OCR, str(pdf), str(out)], capture_output=True, timeout=900)
    pages = re.split(r"<<<page \d+>>>", out.read_text()); out.unlink(missing_ok=True)
    return [[l.strip() for l in p.splitlines() if l.strip()] for p in pages if p.strip()]


def build(pdf, out):
    src = fitz.open(pdf); doc = Document(); ocr = False; first = True
    pages_ocr = None
    for n, pg in enumerate(src):
        sec = doc.sections[0] if first else doc.add_section(WD_SECTION.NEW_PAGE)
        sec.page_width, sec.page_height = Emu(int(pg.rect.width * 12700)), Emu(int(pg.rect.height * 12700))
        sec.orientation = WD_ORIENT.LANDSCAPE if pg.rect.width > pg.rect.height else WD_ORIENT.PORTRAIT
        for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, m, Pt(36))
        first = False
        if len(W(pg.get_text())) < 8:                                    # no text layer: read the picture
            if not OCR: raise SystemExit("scanned page and no --ocr binary")
            if pages_ocr is None: pages_ocr = ocr_lines(pdf)
            ocr = True; para = None
            for line in (pages_ocr[n] if n < len(pages_ocr) else []):
                if para is not None and not re.search(r"[.:;)]$", para.text) and line[:1].islower(): para.add_run(" " + CLEAN(line))
                else: para = doc.add_paragraph(CLEAN(line))
            continue
        for it in page_items(pg):
            if it[1] == "p":
                _, _, txt, size, bold, centre = it
                p = doc.add_paragraph(); r = p.add_run(CLEAN(txt)); r.font.size = Pt(max(7, min(round(size), 16))); r.bold = bold
                p.paragraph_format.space_after = Pt(3)
                if centre: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                rows = it[2]; cols = max(len(r) for r in rows)
                t = doc.add_table(rows=len(rows), cols=cols); t.style = "Table Grid"
                for i, r in enumerate(rows):
                    for j in range(cols):
                        c = t.cell(i, j); c.text = ""; run = c.paragraphs[0].add_run(CLEAN(r[j]) if j < len(r) else ""); run.font.size = Pt(8)
                doc.add_paragraph()
    doc.save(out)
    return ocr


def words_of(docx_path):
    return Counter(W(" ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", zipfile.ZipFile(docx_path).read("word/document.xml").decode("utf8")))))


def main():
    idx = json.loads((F / "index.json").read_text())
    want = [a for a in sys.argv[1:] if ":" in a and not a.startswith("--")]
    todo = [(i, k) for i, fs in idx.items() for k, f in fs.items() if (a := f"{i}:{k}") in want or (not want and "docx" not in f)]
    for iid, k in todo:
        f = idx[iid][k]; pdf = F / f["pdf"]; out = pdf.with_suffix(".docx")
        try: ocr = build(pdf, out)
        except Exception as e:
            print("FAILED", iid, k, str(e)[:80]); continue
        a = Counter(w for pg in fitz.open(pdf) for w in W(pg.get_text())); b = words_of(out)
        cov = 1 - (sum((a - b).values()) / sum(a.values())) if sum(a.values()) else 0
        ok = (sum(b.values()) >= 20) if ocr else (cov >= 0.9)
        print(f"{iid}:{k} {out.name} words {sum(a.values())} -> {sum(b.values())}, coverage {cov:.0%}{' OCR' if ocr else ''}: {'kept' if ok else 'REJECTED'}")
        if ok:
            f["docx"] = f"{iid}/{out.name}"
            if ocr: f["docxNote"] = "ocr"
        else: out.unlink(missing_ok=True)
    (F / "index.json").write_text(json.dumps(idx, indent=1, ensure_ascii=False) + "\n")


main()
