#!/usr/bin/env python3
"""Extract the text of schedules, annexures and forms from the official PDFs, for search.

    python3 scripts/extract_schedule_text.py            # every instrument that has a PDF in sources/pdf/
    python3 scripts/extract_schedule_text.py <id> ...
    SCHEDULE_PDF_DIRS="<folder>" python3 scripts/extract_schedule_text.py income-tax-rules-2002   # PDF too large for git

Schedules are shown on the site as links into the official PDF, so their words were invisible to
search. This writes data/schedule-text/<id>.json: for each schedule listed in data/acts/<id>.json,
the words on its PDF pages (from its first page to the page before the next schedule), plus, for
instruments that exist only as a PDF (`pdfOnly`), the words of the whole PDF. The build adds them to the
search index and to the filter box on the instrument page, always linking back to the PDF page.
Re-run after re-extracting an instrument or changing its PDF.
"""
import json
import os
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "schedule-text"


def clean(text):
    text = text.replace("­", "")                 # soft hyphens
    text = re.sub(r"-\n(?=[a-z])", "", text)           # words broken across lines
    return re.sub(r"\s+", " ", text).strip()


def extract_own_pdfs(act):
    """Schedules that are separate PDFs of their own (schedules[].pdf), e.g. the Foreign Exchange Manual's appendices."""
    sch = act.get("schedules") or []
    out = [None] * len(sch)
    for f in sorted({x["pdf"] for x in sch if x.get("pdf")}):
        path = ROOT / "sources" / "pdf" / f
        if not path.exists():
            continue
        doc = fitz.open(path)
        n = len(doc)
        ks = sorted((k for k in range(len(sch)) if sch[k].get("pdf") == f), key=lambda k: (sch[k]["page"], k))
        starts = sorted({sch[k]["page"] for k in ks})
        seen = set()
        for k in ks:
            start = sch[k]["page"]
            if start in seen:
                out[k] = {"title": sch[k]["title"], "page": start, "pdf": f, "text": ""}
                continue
            seen.add(start)
            later = [p for p in starts if p > start]
            end = max(start, min((later[0] - 1) if later else n, n))
            out[k] = {"title": sch[k]["title"], "page": start, "pdf": f,
                      "text": clean(" ".join(doc[i - 1].get_text() for i in range(start, end + 1)))}
    out = [x for x in out if x]
    return {"id": act["id"], "pdfOnly": False, "schedules": out} if out else None


def extract(act):
    if any(x.get("pdf") for x in act.get("schedules") or []):
        return extract_own_pdfs(act)
    pdf = act.get("sourcePdf")
    path = ROOT / "sources" / "pdf" / pdf if pdf else None
    if pdf and (not path or not path.exists()):
        # PDFs too large for git (remotePdf) can be found in folders named in SCHEDULE_PDF_DIRS (colon-separated)
        for d in filter(None, os.environ.get("SCHEDULE_PDF_DIRS", "").split(":")):
            if (Path(d) / pdf).exists():
                path = Path(d) / pdf
                break
    if not path or not path.exists():
        return None
    doc = fitz.open(path)
    n = len(doc)
    if act.get("pdfOnly"):
        text = clean(" ".join(doc[i].get_text() for i in range(n)))
        return {"id": act["id"], "pdfOnly": True, "schedules": [{"title": act["title"], "page": 1, "text": text}]}
    sch = act.get("schedules") or []
    if not sch:
        return None
    order = sorted(range(len(sch)), key=lambda k: (sch[k]["page"], k))
    starts = sorted({sch[k]["page"] for k in order})
    out = [None] * len(sch)
    seen = set()
    for k in order:
        start = sch[k]["page"]
        if start in seen:                              # two schedules on one page: the first carries the text
            out[k] = {"title": sch[k]["title"], "page": start, "text": ""}
            continue
        seen.add(start)
        later = [p for p in starts if p > start]
        end = (later[0] - 1) if later else n
        end = max(start, min(end, n))
        text = clean(" ".join(doc[i - 1].get_text() for i in range(start, end + 1)))
        out[k] = {"title": sch[k]["title"], "page": start, "text": text}
    return {"id": act["id"], "pdfOnly": False, "schedules": out}


def main():
    ids = sys.argv[1:]
    acts = sorted((ROOT / "data" / "acts").glob("*.json"))
    OUT.mkdir(parents=True, exist_ok=True)
    total = words = 0
    for f in acts:
        act = json.loads(f.read_text())
        if ids and act["id"] not in ids:
            continue
        res = extract(act)
        if not res:
            continue
        w = sum(len(s["text"].split()) for s in res["schedules"])
        if not w:                                      # a scan with no text layer: nothing to search
            print(f"{act['id']}: no text layer, skipped")
            continue
        (OUT / f"{act['id']}.json").write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")))
        total += 1
        words += w
        print(f"{act['id']}: {len(res['schedules'])} schedule(s), {w} words")
    print(f"{total} instrument(s), {words} words")


if __name__ == "__main__":
    main()
