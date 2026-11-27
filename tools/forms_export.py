#!/usr/bin/env python3
"""Cut every schedule, annexure and form that is shown as a PDF link into its own PDF and Word file (for downloading and filling in).

usage: <venv with pdf2docx + pymupdf>/bin/python tools/forms_export.py [--pdf-only] [--limit N] [id ...]
For each schedule in data/acts/<id>.json that has a PDF page (`page`, and no inline `text`): its pages run from its first page to
the page before the next schedule starts (at most 30 pages; schedules that start on the same page share them). Output goes to
sources/forms/<id>/<nn>-<title>.pdf and .docx, and sources/forms/index.json maps instrument -> schedule number -> files, which the
build uses to add "PDF" and "Word" links beside each form. The Word files are made from the PDF by pdf2docx: layout is close but not
exact, so the official PDF stays the reference. Existing files are kept (delete them to redo).
Instruments whose PDF is not in sources/pdf/ (too large for git) are read from SCHEDULE_PDF_DIRS (colon-separated).
"""
import fitz, json, os, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sources" / "forms"
PDF_ONLY = "--pdf-only" in sys.argv
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 0
ids = [a for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]
slug = lambda t: re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t.lower())).strip("-")[:60] or "form"


def find_pdf(name):
    p = ROOT / "sources" / "pdf" / name
    if p.exists(): return p
    for d in filter(None, os.environ.get("SCHEDULE_PDF_DIRS", "").split(":")):
        if (Path(d) / name).exists(): return Path(d) / name
    return None


def main():
    man = json.loads((ROOT / "sources/manifest.json").read_text()); man = man if isinstance(man, list) else man.get("instruments", list(man.values()))
    idx_path = OUT / "index.json"; index = json.loads(idx_path.read_text()) if idx_path.exists() else {}
    done = 0
    Conv = None
    if not PDF_ONLY:
        from pdf2docx import Converter as Conv
    for x in man:
        if ids and x["id"] not in ids: continue
        f = ROOT / "data/acts" / f"{x['id']}.json"
        if not f.exists(): continue
        act = json.loads(f.read_text()); sch = act.get("schedules") or []
        todo = [(k, s) for k, s in enumerate(sch) if not s.get("text") and str(s.get("page", "")).isdigit()]
        if not todo: continue
        res = index.setdefault(x["id"], {}); opened = {}
        for k, s in todo:
            src = s.get("pdf") or x.get("file")
            if src not in opened:
                p = find_pdf(src) if src else None
                opened[src] = (p, fitz.open(p) if p else None)
            p, doc = opened[src]
            if not doc: continue
            a = int(s["page"]); n = len(doc)
            starts = sorted({int(q["page"]) for q in sch if str(q.get("page", "")).isdigit() and (q.get("pdf") or x.get("file")) == src})
            later = [q for q in starts if q > a]
            b = max(a, min((later[0] - 1) if later else n, n, a + 29))
            name = f"{k + 1:02d}-{slug(s['title'])}"; d = OUT / x["id"]; d.mkdir(parents=True, exist_ok=True)
            pdf_out = d / f"{name}.pdf"; docx_out = d / f"{name}.docx"
            if not pdf_out.exists():
                new = fitz.open(); new.insert_pdf(doc, from_page=a - 1, to_page=b - 1)
                try: new.subset_fonts()
                except Exception: pass
                new.save(pdf_out, garbage=4, deflate=True); new.close()
            ent = {"pdf": f"{x['id']}/{pdf_out.name}", "pages": b - a + 1}
            if not PDF_ONLY:
                if not docx_out.exists():
                    try:
                        cv = Conv(str(pdf_out)); cv.convert(str(docx_out)); cv.close()
                    except Exception as e:
                        print("  word failed:", x["id"], s["title"], str(e)[:80])
                if docx_out.exists(): ent["docx"] = f"{x['id']}/{docx_out.name}"
            res[str(k + 1)] = ent; done += 1
            if LIMIT and done >= LIMIT: break
        idx_path.parent.mkdir(parents=True, exist_ok=True); idx_path.write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n")
        print(f"{x['id']}: {len(todo)} forms", flush=True)
        if LIMIT and done >= LIMIT: break
    print(done, "forms exported")


main()
