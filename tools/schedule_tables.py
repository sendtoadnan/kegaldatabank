#!/usr/bin/env python3
"""Show table-dominant schedules as real tables (inline text) instead of a bare PDF link, words taken from the official PDF.

usage: python3 tools/schedule_tables.py [--apply] [--refresh] [--min 0.6] [--span 12] [--err 0.01] [id ...]   (--refresh redoes schedules this tool converted before)
For each schedule that is a PDF page link (schedules[].page, no text), read its PDF pages (first page to the page before the
next schedule). The schedule is converted when ruled tables hold at least --min (default 0.6) of the words on those pages,
it spans at most 12 pages, and the words of the rows plus the text around them match the page's words (page margins
excluded) to within 1%. Forms and boxed annexures stay PDF links. `page` stays, so the schedule keeps its "PDF p.N" link.
After --apply: python3 scripts/extract_schedule_text.py <id> (no double search hits), npm run build, make_vectors, npm test.
"""
import fitz, json, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_tables import find_tables, row_strings

ROOT = Path(__file__).resolve().parent.parent
W = lambda s: re.findall(r"[^\W_]+", s.lower())
APPLY = "--apply" in sys.argv
REFRESH = "--refresh" in sys.argv
arg = lambda k, d: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
MIN, SPAN, ERR = arg("--min", 0.6), int(arg("--span", 12)), arg("--err", 0.01)
ids = [a for a in sys.argv[1:] if not a.startswith("--") and not re.fullmatch(r"[\d.]+", a)]


NORM = lambda t: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t.lower())).strip()


def heading_y(pg, title):
    """y of the line where this schedule starts on its first page (title or its first words), or None."""
    want = {NORM(title), NORM(re.sub(r"^form\s+", "", title, flags=re.I)), NORM(title.split("—")[0])} - {""}
    for b in pg.get_text("dict")["blocks"]:
        if b.get("type") != 0: continue
        for ln in b["lines"]:
            t = NORM("".join(s["text"] for s in ln["spans"])); t2 = re.sub(r"^\d+ ", "", t)
            if any(t.startswith(w) or t2.startswith(w) for w in want): return ln["bbox"][1] - 1
    return None


def furniture(txt, y0, y1, H):
    """Page numbers, "Page 3 of 52" and running heads ending in a rule of underscores are not law text."""
    t = txt.strip()
    if re.fullmatch(r"\d{1,4}", t) and (y1 > 0.9 * H or y0 < 0.08 * H): return True
    if re.fullmatch(r"(?i)page\s+\d+\s+of\s+\d+", t): return True
    return bool(re.search(r"_{6,}", t)) and y1 < 0.12 * H and len(t.split()) <= 12


def page_items(pg, ymin=0):
    """Paragraphs and tables of one page in reading order, margins excluded: [(y, 'p'|'t', payload)]"""
    H = pg.rect.height
    tabs = find_tables(pg, strict=True)
    inside = lambda b: any(t["x0"] - 2 <= b[0] and b[2] <= t["x1"] + 2 and t["y0"] - 2 <= b[1] and b[3] <= t["y1"] + 2 for t in tabs)
    items = [(t["y0"], "t", row_strings(t["rows"])) for t in tabs]
    paras = []
    for b in pg.get_text("dict")["blocks"]:
        if b.get("type") != 0 or inside(b["bbox"]): continue
        for ln in b["lines"]:
            txt = re.sub(r"\s+", " ", "".join(s["text"] for s in ln["spans"])).strip()
            if not txt or inside(ln["bbox"]) or furniture(txt, ln["bbox"][1], ln["bbox"][3], H): continue
            y0, y1 = ln["bbox"][1], ln["bbox"][3]
            if y1 < 0.055 * H or y0 > 0.945 * H or y0 < ymin: continue                       # running head, page number, footer
            paras.append((y0, y1, txt))
    paras.sort()
    cur = None
    for y0, y1, txt in paras:
        if cur and y0 - cur[1] < 0.9 * (y1 - y0) + 2 and not re.match(r"^(\(?\w{1,4}[.)]|\d{1,3}\.)\s", txt):
            cur[1] = y1; cur[2] += " " + txt
        else:
            if cur: items.append((cur[0], "p", [cur[2]]))
            cur = [y0, y1, txt]
    if cur: items.append((cur[0], "p", [cur[2]]))
    items.sort(key=lambda i: i[0])
    return items, tabs


def page_words(pg, ymin=0):
    H = pg.rect.height
    return Counter(w for b in pg.get_text("dict")["blocks"] if b.get("type") == 0 for ln in b["lines"] if not furniture("".join(s["text"] for s in ln["spans"]), ln["bbox"][1], ln["bbox"][3], H)
                   if not (ln["bbox"][3] < 0.055 * H or ln["bbox"][1] > 0.945 * H or ln["bbox"][1] < ymin) for w in W("".join(s["text"] for s in ln["spans"])))


def convert(doc, start, end, title=""):
    got, want, tw, paras = Counter(), Counter(), 0, []
    for n in range(start, end + 1):
        pg = doc[n - 1]; ymin = 0
        if n == start and title:
            ymin = heading_y(pg, title)
            if ymin is None: return paras, 0, 1                       # cannot tell where the schedule starts on its page
        items, tabs = page_items(pg, ymin); want += page_words(pg, ymin)
        for _, kind, rows in items:
            if kind == "t":                       # a row with a cell over 50 words is a layout box holding text, not table cells: keep it as a paragraph
                rows = [(re.sub(r"\s+", " ", " ".join(c for c in r.lstrip("|!").split("|") if c))
                         if any(len(W(c)) > 50 for c in r.lstrip("|!").split("|")) else r) for r in rows]
            for r in rows: got.update(W(r))
            if kind == "t": tw += sum(len(W(r)) for r in rows if r.startswith("|"))
            paras += rows
    total = sum(want.values()) or 1
    miss = sum((want - got).values()) + sum((got - want).values())
    return paras, tw / total, miss / total


def main():
    man = json.loads((ROOT / "sources/manifest.json").read_text()); man = man if isinstance(man, list) else man.get("instruments", list(man.values()))
    tot = 0
    for x in man:
        if ids and x["id"] not in ids: continue
        f = ROOT / "data/acts" / f"{x['id']}.json"; pdf = ROOT / "sources/pdf" / (x.get("file") or "")
        if not f.exists() or not x.get("file") or not pdf.exists(): continue
        raw = f.read_text(); act = json.loads(raw); sch = act.get("schedules") or []
        if not sch or any(s.get("pdf") for s in sch): continue
        doc = fitz.open(pdf); n = len(doc)
        starts = sorted({int(s["page"]) for s in sch if str(s.get("page", "")).isdigit()})   # (several schedules on one page: left as PDF links)
        done = 0; changed = False
        for s in sch:
            if REFRESH and s.get("text") and s.get("page"): s.pop("text"); changed = True      # redo what this tool made earlier (only it writes text together with a page)
            if s.get("text") or not str(s.get("page", "")).isdigit(): continue
            a = int(s["page"]); later = [p for p in starts if p > a]; b = min((later[0] - 1) if later else n, n); b = max(a, b)
            if b - a + 1 > SPAN or sum(1 for q in sch if str(q.get("page", "")) == str(a)) > 1: continue
            try: paras, share, err = convert(doc, a, b, s["title"])
            except Exception as e: continue
            blanks = sum(1 for p in paras if re.search(r"_{4,}|\.{6,}|…{3,}", p))
            if blanks >= 6 or (blanks and len(paras) <= 12): continue                                         # a form to be filled in: keep the PDF
            if share >= MIN and err <= ERR and any(p.startswith("|") for p in paras):
                s["text"] = paras; done += 1
        if done or changed:
            tot += done; print(f"{x['id']}: {done} of {len(sch)} schedules converted")
            if APPLY: f.write_text(json.dumps(act, ensure_ascii=False, indent=1 if raw.startswith('{\n "') else 2) + ("\n" if raw.endswith("\n") else ""))
    print(tot, "schedules converted" + ("" if APPLY else " (dry run)"))

main()
