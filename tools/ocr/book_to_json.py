"""Convert an instrument from the scanned printed edition (book pages) into data/acts/<id>.json.

usage: python3 tools/ocr/book_to_json.py --vocr <vision_ocr> --scans <scan folder> <id> [<id> ...]
Each id must have an entry in data/salam/conversions.json (book pages, title, number, dates, aliases).

How the page is read:
- each page is OCR'd at 300 dpi in overlapping bands, twice with the band edges moved, plus a second pass over the left margin to
  recover short labels such as "(iv)" that the first pass drops;
- running heads (page number, part and short title), page codes ("E2 16-10-12-19") and the
  publisher's footnotes (set in smaller type, so found by line height) are removed, as are the
  amendment markers in the text; only the instrument's own text is kept;
- the text before regulation/rule 1 is the preamble; "N. Heading.- text" starts a provision;
  CHAPTER/PART lines start a part. Forms and schedules at the end are not converted (noted).
The result is Unverified: a person must check it against the scan (scripts/verify_sheet.py).
"""
import argparse, json, os, re, statistics, subprocess, tempfile
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser()
ap.add_argument("--vocr", required=True)
ap.add_argument("--scans", required=True, help="folder holding the scan PDFs and '_ocr text/page-map.json'")
ap.add_argument("--pages-only", action="store_true", help="only list each instrument's scan pages (for tools/ocr/check_sheet.py)")
ap.add_argument("ids", nargs="+")
a = ap.parse_args()
SC = Path(a.scans)
PM = json.load(open(SC / "_ocr text" / "page-map.json"))
SPEC = {c["id"]: c for c in json.load(open(os.environ.get("BOOK_SPEC") or ROOT / "data/salam/conversions.json"))["instruments"]}

def scan_pdf(ocr_dir_name):
    vol, _, stem = ocr_dir_name.partition(" - ")
    return SC / vol / (stem + ".pdf")

def book_pages(part, lo, hi):
    """Book pages of a part between lo and hi (inclusive), including inserted pages like 162(3)."""
    out = []
    for pg in PM:
        m = re.fullmatch(rf"{part}-(\d+)(?:\((\d+)\))?", pg)
        if m and lo <= int(m.group(1)) <= hi: out.append(((int(m.group(1)), int(m.group(2) or 0)), pg))
    return [pg for _, pg in sorted(out)]

def scans_for(part, lo, hi, hint=None):
    """Scan pages to read, in order: every scan from the first to the last mapped page of the range
    (unnumbered pages in between included), the unnumbered title page just before, and only the
    newest copy of a page that was scanned twice."""
    pages = book_pages(part, lo, hi)
    if SPEC_NOINSERTS: pages = [pg for pg in pages if "(" not in pg]
    if hint:
        pages = [pg for pg in pages if any(hint in l["file"] for l in PM[pg])]
    chosen = {pg: pick([l for l in PM[pg] if not hint or hint in l["file"]]) for pg in pages}
    skip = {(l["file"], l["scan"]) for pg in pages for l in PM[pg] if l is not chosen[pg]}
    mapped = {(l["file"], l["scan"]) for locs in PM.values() for l in locs}
    by_file = {}
    for l in chosen.values(): by_file.setdefault(l["file"], []).append(l["scan"])
    out = []
    files = sorted(by_file)
    for n, f in enumerate(files):
        lo_s, hi_s = min(by_file[f]), max(by_file[f])
        if n == 0:
            k = lo_s - 1
            while k >= 1 and (f, k) not in mapped and lo_s - k <= 2:
                t = (SC / "_ocr text" / f / f"p{k:04d}.txt")
                if t.exists() and t.read_text().strip(): lo_s = k
                k -= 1
        out += [(f, k) for k in range(lo_s, hi_s + 1) if (f, k) not in skip]
    return out, pages

def pick(locs, cache={}):
    """When a page was scanned more than once (old and replacement page), take the newest update code."""
    def code(l):
        key = (l["file"], l["scan"])
        if key not in cache:
            t = (SC / "_ocr text" / l["file"] / f"p{l['scan']:04d}.txt").read_text()
            m = re.search(r"[EB]2\s*(\d{1,3})\s*-", t)
            cache[key] = int(m.group(1)) if m else -1
        return cache[key]
    return max(locs, key=code)

WORDS = set(w.strip().lower() for w in open("/usr/share/dict/words")) if os.path.exists("/usr/share/dict/words") else set()

def quality(t):
    """Share of words (3+ letters) found in the system word list: picks the better reading of a line."""
    ws = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", t)]
    if not ws: return 0.0
    ok = sum(1 for w in ws if w in WORDS or w.rstrip("s") in WORDS or w[:-2] in WORDS or w[:-3] in WORDS)
    return ok / len(ws) + min(len(ws), 12) / 100

def vision(img):
    out = subprocess.run([a.vocr, "--boxes", img], capture_output=True, text=True).stdout
    res = []
    for ln in out.splitlines()[1:]:
        bx, _, t = ln.partition("\t")
        if t.strip(): res.append([*map(float, bx.split()), t.strip()])
    return res

def to_rows(boxes):
    rows = []
    for b in sorted(boxes, key=lambda b: (b[1] + b[3]) / 2):
        yc = (b[1] + b[3]) / 2
        for rr in rows:
            if abs(rr["y"] - yc) < 0.006: rr["parts"].append(b); break
        else: rows.append({"y": yc, "parts": [b]})
    out = []
    for rr in rows:
        ps = sorted(rr["parts"], key=lambda b: b[0])
        out.append({"y": rr["y"], "x": ps[0][0], "h": statistics.median(b[3] - b[1] for b in ps), "text": " ".join(b[4] for b in ps)})
    return out

def ocr_rows(pdf, idx, tmp):
    """Read a page twice (whole page, and four overlapping bands: Vision drops different lines in
    each), keep the better reading of each line, then recover margin labels such as "(iv)"."""
    page = fitz.open(pdf)[idx]
    r = page.rect
    full = os.path.join(tmp, "full.png"); page.get_pixmap(dpi=300, colorspace=fitz.csGRAY).save(full)
    whole = vision(full)
    # the bands are cropped to the text column: the vertical page code and punch holes in the
    # margin make Vision drop the lines beside them
    lw = [b[0] for b in whole if len(b[4]) > 20]
    cx = max(0.0, (min(lw) if lw else 0.0) - 0.015)
    banded, n, ov = [], 4, 0.05
    for k in range(n):
        c0, c1 = k / n, (k + 1) / n
        b0, b1 = max(0, c0 - ov), min(1, c1 + ov)
        img = os.path.join(tmp, f"band{k}.png")
        page.get_pixmap(dpi=300, colorspace=fitz.csGRAY, clip=fitz.Rect(r.x0 + r.width * cx, r.y0 + r.height * b0, r.x1, r.y0 + r.height * b1)).save(img)
        for x0, y0, x1, y1, t in vision(img):
            y0, y1 = b0 + y0 * (b1 - b0), b0 + y1 * (b1 - b0)
            x0, x1 = cx + x0 * (1 - cx), cx + x1 * (1 - cx)
            if c0 <= (y0 + y1) / 2 < c1 or (k == n - 1 and (y0 + y1) / 2 >= c1): banded.append([x0, y0, x1, y1, t])
    if not whole and not banded: return [], 0
    rows_b, rows_w = to_rows(banded), to_rows(whole)
    rows = []
    for rb in rows_b:
        match = [rw for rw in rows_w if abs(rw["y"] - rb["y"]) < 0.006]
        rows.append(max([rb] + match, key=lambda x: (quality(x["text"]), len(x["text"]))))
    def similar(t1, t2):
        a1, a2 = set(re.findall(r"[a-z]{3,}", t1.lower())), set(re.findall(r"[a-z]{3,}", t2.lower()))
        return a1 and a2 and len(a1 & a2) / min(len(a1), len(a2)) >= 0.4
    for rw in rows_w:
        if any(abs(rw["y"] - rb["y"]) < 0.006 for rb in rows_b): continue
        if any(abs(rw["y"] - x["y"]) < 0.02 and similar(rw["text"], x["text"]) for x in rows): continue
        rows.append(rw)
    rows.sort(key=lambda x: x["y"])
    long = [x for x in rows if len(x["text"]) > 20]
    left = min(x["x"] for x in long) if long else min(x["x"] for x in rows)
    # second pass over the label margin
    clip = fitz.Rect(r.x0 + r.width * max(0, left - 0.02), r.y0, r.x0 + r.width * (left + 0.09), r.y1)
    strip = os.path.join(tmp, "strip.png"); page.get_pixmap(dpi=300, clip=clip, colorspace=fitz.csGRAY).save(strip)
    w = clip.width / r.width
    for x0, y0, x1, y1, t in vision(strip):
        if not re.fullmatch(r"\(?[0-9ivxlcA-Za-z]{1,5}\)|\d{1,3}[A-Z]?\.", t): continue
        x0 = max(0, left - 0.02) + x0 * w
        yc = (y0 + y1) / 2
        row = next((x for x in rows if abs(x["y"] - yc) < 0.006), None)
        if row is None:
            rows.append({"y": yc, "x": x0, "h": y1 - y0, "text": t})
        elif not row["text"].startswith(t) and row["x"] > x0 + 0.01:
            row["text"] = t + " " + row["text"]; row["x"] = x0
    rows.sort(key=lambda x: x["y"])
    return rows, left

HEAD_WORDS = re.compile(r"^(Pt\.|Part\s+[IVX]|Company Law|Companies Act, 2017$|Rules & Regulations|[A-ZПШIl1|]{1,4}\s*[-–]\s*\d)|Pt\. [IVX]+, Rules", re.I)
FOOT = re.compile(r"^\s*[EB]2\s*\d|^\s*\d{2}-\d{2}-\d{2,4}\s*$")

def clean_page(rows, short_names):
    if not rows: return []
    body_h = statistics.median(r["h"] for r in rows if len(r["text"]) > 30) if any(len(r["text"]) > 30 for r in rows) else 0.012
    keep, top = [], True
    for i, r in enumerate(rows):
        t = r["text"]
        # the vertical page code in the margin ("E2 13-05-11-2015") lands in front of the line beside it
        t2 = re.sub(r"^\W*(?:[EB]2\s*\d{0,3}\s*[-.]?\s*)?\d{1,2}\s*-\s*\d{1,2}\s*-\s*\d{2,4}\s+(?=\S)", "", t)
        if t2 != t: t = t2; r["text"] = t2
        if top and len(t.strip()) < 3: continue
        if top and len(t) < 70 and re.search(r"\b(Regs?|Rules|Regulations|Ord|Act)\.?,?\s*(19|20)\d\d\.?$", t) and not re.match(r"^\W*\d{1,3}[.,]", t): continue
        t = re.sub(r"^[\W_]+(?=[A-ZПШIl1|]{1,4}\s*[-–]\s*\d)", "", t)
        if re.sub(r"[^a-z]", "", t.lower()) in short_names and len(t) < 90: continue   # running head lower down
        if top and (HEAD_WORDS.search(t) or re.fullmatch(r"(S|R|Reg|Rr|Ss)\.?\s*[\d\- ,A-Z]+|\d{1,3}", t.strip()) or re.sub(r"[^a-z]", "", t.lower()) in short_names and len(t) < 90):
            continue
        top = False
        if re.search(r"Compan(y|ies) Law (&|and) Procedures|Pt\. [IVX]+, Rules", t): continue   # publisher's running heads
        if FOOT.search(t) or re.match(r"^[A-ZПШIl1|]{1,4}\s*[-–]\s*\d{1,4}(\(\d+\))?\s+(Pt\.|Part|Company)", t): continue
        # footnotes: smaller type, starting with a note number
        if r["h"] < body_h * 0.82 and (re.match(r"^\W?\d{1,2}\s?[A-Z]", t) or keep and keep[-1].get("foot")):
            r["foot"] = True
        if r["h"] < body_h * 0.82 and keep and keep[-1].get("foot"): r["foot"] = True
        keep.append(r)
    return [r for r in keep if not r.get("foot")]

FN = re.compile(r"^\W{0,2}(?:\d{1,2}|['`’‘]|[Il|](?=[A-Z]))\s?(Repealed|Substituted|Inserted|Omitted|Deleted|Added|Words?\b|Sub-|Clause|Proviso|Para|Item|S\.\s?No|Sr\.|Earlier|Regulations?\b|Rules?\b|Explanation|Figures?\b|Comma|Full stop|Renumbered|Amended|The (word|words|figure|figures|comma)|For the|Re-?numbered|Heading|Schedule|Annexure|Form)")
FN2 = re.compile(r"^\W{0,2}(?:\d{1,2}\s?|['`’‘]\s?|(?-i:[il|](?=[A-Z])))[A-Z][\w.()&,'\" -]{0,70}?\b(deleted|substituted|inserted|omitted|added|amended|renumbered|repealed)\b", re.I)
FN3 = re.compile(r"^\W{0,3}(?:Repealed|Substituted|Inserted|Omitted|Deleted|Added|Renumbered)\s+(?:for|by|vide|the)\b")   # a footnote whose marker was read as punctuation
QUOTE_START = re.compile(r"read as\s*(follows|under)|read as\s*$|^follows\s*:", re.I)
QUOTE_END = re.compile(r"[\"”'’]\s*[.;:,]?\s*$")

DROPPED = []

def drop_footnotes(lines):
    """Remove the publisher's footnotes: a block starting "1Substituted…/2Inserted…" runs to the end of
    its page; the old text quoted after "…read as follows" is removed up to its closing quote or the page end."""
    out, mode, page = [], "body", None
    DROPPED.clear()
    for l in lines:
        if l["page"] != page:
            page = l["page"]
            mode = "body"   # footnotes continue at the foot of the next page, never at its top
        t = l["text"]
        if mode == "body" and re.search(r"Before (substitution|omission|deletion|amendment).{0,60}read as", t, re.I):
            mode = "quote"; DROPPED.append(("Q+", l)); continue
        if mode == "body" and (FN.match(t) or FN2.match(t) or FN3.match(t) or re.match(r"^\W{0,3}[A-Z][\w.()&,' -]{0,50}?\b(substituted|inserted|omitted|deleted|added)\s+(by|vide)\s+S\.?\s?R\.?\s?O", t)):
            mode = "fn"
        if mode == "fn" and QUOTE_START.search(t):
            mode = "quote"
            rest = t[QUOTE_START.search(t).end():]
            if re.search(r"[\"“].*[\"”]\s*[.;:,]?\s*$", rest): mode = "fn"
            DROPPED.append(("Q+", l)); continue
        if mode == "quote":
            if QUOTE_END.search(t): mode = "fn"
            DROPPED.append(("Q", l)); continue
        if mode == "fn":
            DROPPED.append(("F", l)); continue
        out.append(l)
    return out

def strip_markers(t):
    t = re.sub(r"\s*Central Depositor(?:y|ies) Compan(?:y|ies)\s+Form\s+I\b", " ", t)   # running head with the form heading beside it
    # a running head caught in the middle of a line: "IV -27 R. 3 Part IV, CDC Rules", "Reg. 12 Part III, Listed Companies"
    t = re.sub(r"\s*(?:[IVX]{1,4}\s*-\s*\d{1,4}\s+)?(?:Reg\.|R\.)\s*\d{1,3}[A-Z]?\s+Part\s+[IVX]+,\s+\S+\s+\S+", " ", t)
    t = re.sub(r"\s*\W?(?:Inserted|Substituted|Omitted|Deleted|Added)\s+by\s+S\.?\s?R\.?\s?O\.?\s*[\dIlD()/\[\] ]+dated\s+[A-Za-z]+\.?\s+\d{1,2},?\s*\d{4}\.?", " ", t)   # unnumbered footnote on a body line
    # the margin's page date code dropped into the middle of a line: "(III of 15-10-2020 2015)"
    t = re.sub(r"(?<!dated)(?<!\bon)(?<!from)(?<!till)(?<!\bto)(?<!before)(?<!after)(?<!\bby)\s(?:[EB]2\s*)?\d{1,2}-\d{1,2}-\d{2,4}(?=\s|$)", "", t)
    # a footnote that landed on a body line: "… 25-04-2024 1Clauses (e) to (g) inserted by SRO 742(I)/2023 dated June 15, 2023."
    t = re.sub(r"\s*(?:\d{2}-\d{2}-\d{4}\s*)?\d{1,2}[A-Z][A-Za-z0-9()&,.\- ]{0,60}?\b(?:inserted|substituted|deleted|omitted|added)\s+by\s+S\.?\s?R\.?\s?O\.?\s*[\dIl()/\[\] ]+(?:dated\s+[A-Za-z]+\.?\s+\d{1,2},?\s*\d{4})?\.?", " ", t)
    t = re.sub(r"(?:\b[A-Z][A-Z0-9.]{0,2}\s*[.:]?\s*)?(?<![\w-])[0-9SOBZ]{2,3}[-.]\s?(?:0[1-9]|[12]\d|3[01])[-.](?:0[1-9]|1[0-2])[-.](?:\d{4}|\d{2})(?![\w-])", " ", t)   # margin page code: update number + date, any OCR form of its "E2" prefix
    t = re.sub(r"\s*\b[EB]2\s*\d{1,3}\s*[-.]\s*\d{1,2}\s*[-.](?!\s*\d)", " ", t)
    t = re.sub(r"\s*\b[EB]2\s*\d{1,3}\s*[-.]\s*\d{1,2}\s*[-.]\s*\d{1,2}(?:[\s\-.:]*\d{1,4}(?::\d)?)?\b", " ", t)
    t = re.sub(r"(?<![\w(])[0-9¹²³*°•']{1,2}\s?(?=\[)", "", t)       # note number before an amendment bracket
    t = re.sub(r"(?<=\s)[a-z](?=\[[a-z])", "", t)                     # note number misread as a letter: "a[six months]"
    return re.sub(r"\s+", " ", t).strip()

LABEL = re.compile(r"^(\(\s*(?:[a-z]{1,2}|[ivxlc]{1,6}|\d{1,3}[a-zA-Z]?|[A-Z])\s*\)|Explanation|Provided|\d{1,3}[A-Z]?\.\s)")
PROV = re.compile(r"^[\"“\[]?(\d{1,3}[A-Z]{0,2})[.,]\s*([A-Z\[][^\n]{1,200}?)\s*(?:[.,:]\s*[-–—_]+|(?<=[a-z])[-–—](?=\s*(?:\(1\)|$))|\.(?=\s*\(\d)|\.(?=\s*\d?\[?\(1\)))\s*(.*)$")

INFERRED = {}

def infer_missing_numbers(lines, sid):
    """Restore a heading's number the OCR dropped, only when the numbering has a gap and the number of
    unnumbered heading-shaped lines in that gap is exactly the number of missing provisions. Each
    inference is recorded (data/salam/inferred-headings.json) for the person checking the text."""
    NUM = re.compile(r"^[\[\W]{0,3}(\d{1,3})[.,]\s*[A-Z\[]")
    SHAPE = re.compile(r"[.,:]\s*[-–—_]")
    HEADLESS = re.compile(r"^[\[\W]{0,2}([A-Z][^.:;\d]{3,90}?)\s*[.,:]\s*[-–—_]+\s*(?:\(1\)|\(a\)|[A-Z(\[])")
    seq, last = [], 0
    for i, l in enumerate(lines):
        m = NUM.match(l["text"])
        if m and SHAPE.search(l["text"][:130]):
            n = int(m.group(1))
            if last < n <= last + 8: seq.append((i, n)); last = n
    cand = [i for i, l in enumerate(lines) if HEADLESS.match(l["text"]) and not NUM.match(l["text"])
            and not re.match(r"^\W*(Explanation|Provided|Illustration|Note|Following|Chapter|Part)\b", l["text"])]
    anchors = [(-1, 0)] + seq
    done = []
    for (i1, a), (i2, b) in zip(anchors, seq):
        gap = b - a - 1
        if gap <= 0: continue
        inside = [c for c in cand if i1 < c < i2]
        if len(inside) == gap:
            for k, c in enumerate(inside):
                lines[c]["text"] = f"{a + 1 + k}. " + lines[c]["text"].lstrip("[ ")
                done.append({"number": a + 1 + k, "page": lines[c]["page"], "line": lines[c]["text"][:70]})
    if done:
        INFERRED[sid] = done
        print(f"  {sid}: restored {len(done)} dropped heading number(s): {[d['number'] for d in done]}")

CODES = {}

def convert(spec):
    global CODES
    if spec.get("scanFrom"):     # Volume II: chosen by scan range (its page numbers are irregular)
        scans, pages = [(spec["file"], k) for k in range(spec["scanFrom"], spec["scanTo"] + 1)], []
    else:
        scans, pages = scans_for(spec["part"], spec["from"], spec["to"], spec.get("fileHint"))
    if not scans: raise SystemExit(f"{spec['id']}: no book pages found")
    where = {(l["file"], l["scan"]): pg for pg in pages for l in PM[pg]}
    saved = Path(os.environ["BOOK_LINES"]) / (spec["id"] + ".lines.txt") if os.environ.get("BOOK_LINES") else None
    if saved and saved.exists():
        # re-parse from the cleaned lines a previous run saved (BOOK_DEBUG): no OCR, takes seconds
        CODES = {}
        lines = []
        for ln in saved.read_text().splitlines():
            pg, x, t = ln.split("\t", 2); lines.append({"page": pg, "x": float(x), "text": t})
        lines = drop_footnotes(lines)      # re-apply, in case the filter improved since the lines were saved
        if os.environ.get("BOOK_LINES_OUT"):   # the filtered lines, for tools/ocr/guided_rebuild.py
            Path(os.environ["BOOK_LINES_OUT"], spec["id"] + ".filtered.lines.txt").write_text("\n".join(f'{l["page"]}\t{l["x"]:.3f}\t{l["text"]}' for l in lines))
    else:
        got = []
        with tempfile.TemporaryDirectory() as tmp:
            for f, k in scans: got.append(((f, k),) + ocr_rows(scan_pdf(f), k - 1, tmp))
        # running heads: short lines that recur among the first rows of the instrument's pages
        from collections import Counter
        norm = lambda t: re.sub(r"[^a-z]", "", t.lower())
        tops = Counter(n for _, rows, _ in got for n in {norm(r["text"]) for r in rows[:4] if len(r["text"]) < 90} if len(n) > 6)
        heads = [n for n, c in tops.items() if c >= 2] + [norm(h) for h in spec.get("runningHeads", [])]
        lines = []; CODES = {}
        for n, ((f, k), rows, left) in enumerate(got):
            pg = where.get((f, k), f"scan {k}")
            # circulars filed after the instrument: their pages carry "Circulars" in the running head
            if n > 2 and any(re.search(r"\bCirculars?\b", r["text"]) and len(r["text"]) < 90 for r in rows[:4]): break
            mc = re.search(r"\b[EB]2\s*(\d{1,3})\s*[-.]", " ".join(r["text"] for r in rows))
            CODES[pg] = int(mc.group(1)) if mc else -1          # the page's update number (newer = larger)
            for r in clean_page(rows, heads):
                lines.append({"page": pg, "x": r["x"] - left, "text": r["text"]})
        lines = drop_footnotes(lines)
    if os.environ.get("BOOK_DEBUG"):
        Path(os.environ["BOOK_DEBUG"], spec["id"] + ".dropped.txt").write_text("\n".join(f'{k}\t{l["page"]}\t{l["text"]}' for k, l in DROPPED))
        Path(os.environ["BOOK_DEBUG"], spec["id"] + ".lines.txt").write_text("\n".join(f'{l["page"]}\t{l["x"]:.3f}\t{l["text"]}' for l in lines))
    # start at the S.R.O. recital / title, stop at the end marker
    start = next((i for i, l in enumerate(lines) if re.search(spec.get("startAt", r"S\.\s*R\.\s*O\.|In exercise|^An Act to |^WHEREAS|The following Act of"), l["text"])), 0)
    lines = lines[start:]
    pos, prev = [], None
    for l in lines:
        pos.append(0 if l["page"] != prev else pos[-1] + 1); prev = l["page"]
    stop = spec.get("stopAt", r"^[\W\d]{0,4}([A-Za-z]{1,5}\.?[\s-]*)?(FORMS?|Forms?|ANNEXURES?|Annexures?|SCHEDULES?|Schedules?|APPENDI(?:X|CES)|Appendi(?:x|ces))(?:[A-Z]\b|\b)[\s\-–—.:]*([A-Z0-9IVX]{1,5}[A-Z0-9\-]{0,4})?\.?$")
    end = next((i for i, l in enumerate(lines) if re.search(stop, l["text"].strip()) and len(l["text"]) < 40 and (pos[i] <= 3 or l["x"] > 0.2)), len(lines))
    first_prov = next((i for i, l in enumerate(lines) if re.match(r"^1[.,]\s*[A-Z]", l["text"])), 10**9)   # none found: the number was lost, do not cut at the recital
    for i, l in enumerate(lines[:end]):
        if i > first_prov and pos[i] <= 6 and (re.match(r"^[\[(]?\s*See\s+(regulation|rule|section|sub-regulation)", l["text"], re.I)
                                               or re.match(r"^(Notification No\.\s*)?S\.?\s*R\.?\s*O\.?\s*\d{1,4}\s*\(I\).{0,30}dated", l["text"])):
            end = i - pos[i]; break
    if os.environ.get("BOOK_TRACE"): print(f"  trace {spec['id']}: start {start}, end {end}, kept {len(lines[:end])} of {len(lines)} lines; stopped at: {lines[end]['text'][:60] if end < len(lines) else '(none)'}")
    global REST
    REST = lines[end:]
    lines = lines[:end]
    infer_missing_numbers(lines, spec["id"])
    # paragraphs
    merged, k = [], 0
    while k < len(lines):
        if re.fullmatch(r"\W{0,2}\d{1,3}[A-Z]?[.,]", lines[k]["text"].strip()) and k + 1 < len(lines) and re.match(r"^[A-Z]", lines[k + 1]["text"]):
            lines[k + 1]["text"] = lines[k]["text"].strip() + " " + lines[k + 1]["text"]; k += 1; continue
        merged.append(lines[k]); k += 1
    lines = merged
    paras, last_no = [], 0
    fixes = spec.get("headingFixes", {})   # {"line start as read": "as printed"}, each confirmed against the scan
    for l in lines:
        t = re.sub(r"^[Il|](?=\d[.,]\s*[A-Z])", "1", l["text"])
        t = re.sub(r"\s*[•·]+\s*$", "", t)                                                              # stray bullet at the end of a line
        t = re.sub(r"^[0-9¹²³*'+°•<il]{0,2}[\[(|](?=\d{1,3}[A-Z]?[.,]\s*[A-Z])", "[", t)
        t = re.sub(r"^[0-9¹²³*'<il]{0,2}[\[(](\d{1,3}[A-Z]?)[\])]\s*[.,]\s*(?=[A-Z])", r"[\1. ", t)       # "2[18]. / 2[18). / 1(24). Pledging…" -> "[18. Pledging…" (marker, then number closed by ] or ))
        t = re.sub(r"^(\W{0,3}\d{1,3}[A-Z]?[.,])\s*[•·*]\s*(?=[A-Z])", r"\1 ", t)                  # "8. •Procedure where…" -> "8. Procedure where…"
        t = re.sub(r"^[•·*]\s*(?=\d{1,3}[A-Z]?[.,]\s*[A-Z])", "", t)                                   # "• 26. Refusal…"   # "2[19. Mode of payment.-" (substituted provision)
        for old, new in fixes.items():
            if t.startswith(old): t = new + t[len(old):]
        l["text"] = t
        mnum = re.match(r"^[\"“\[]?(\d{1,3})[.,]\s*[A-Z]", t)
        looks_heading = bool(mnum) and len(t.split("-")[0].split()) <= 16 and not re.search(r"\b(shall|may|must|should|will)\b", re.split(r"[.:;]\s*[-–—_]|[:;]", t, 1)[0])
        if mnum and looks_heading and last_no < int(mnum.group(1)) <= last_no + 3:
            last_no = int(mnum.group(1)); paras.append({"page": l["page"], "text": t}); continue
        ends = not paras or re.search(r"([.:;\-–—\]\"”)]|\band|\bor)\s*$", paras[-1]["text"].rstrip()) or paras[-1]["text"].isupper()
        new = (not paras or PROV.match(t) or re.match(r"^[\"“]?\d{1,3}[A-Z]{0,2}[.,]\s*[A-Z]", t) and ends or t.isupper() and len(t) > 12 or LABEL.match(t) and ends or re.match(r"^(CHAPTER|PART)\b", t)
               or l["x"] > 0.035 and ends)
        if new: paras.append({"page": l["page"], "text": t})
        else: paras[-1]["text"] = (paras[-1]["text"][:-1] if re.search(r"[a-z]-$", paras[-1]["text"]) else paras[-1]["text"] + " ") + t
    preamble, parts, cur, sec, skipping = [], [], None, None, False
    for p in paras:
        t = strip_markers(p["text"])
        if re.match(r"^(CHAPTER|PART)\s+[IVXL\d]+", t) and len(t) < 120:
            h = re.sub(r"\b([IVXL]+)\b", lambda m: m.group(1).upper(), t.title()) if t.isupper() else t
            cur = {"heading": re.sub(r"\b(Ii|Iii|Iv|Vi|Vii|Viii|Ix|Xi|Xii)\b", lambda m: m.group(1).upper(), h), "sections": []}; parts.append(cur); continue
        m = PROV.match(t)
        if not m:
            m2 = PROV2.match(t)
            jump_ok = bool(spec.get("allowJump")) and sec is not None and int(re.match(r"\d+", m2.group(1)).group()) > int(re.match(r"\d+", sec["no"]).group()) if m2 else False
            if m2 and len(m2.group(2).split()) <= 14 and not re.match(r"(Where|If|In case|Subject to|Notwithstanding|Provided|Any person who|No person shall)\b", m2.group(2)) and (sec is not None and (_expected(sec["no"], m2.group(1)) or jump_ok) or sec is None and m2.group(1) == "1"): m = m2
        if not m and sec is not None and spec.get("untitledProvisions"):
            m3 = re.match(r"^[\"“\[]?(\d{1,3}[A-Z]?)[.,]\s+()([A-Z].{40,})$", t)
            if m3 and _expected(sec["no"], m3.group(1)): m = m3
        no = m.group(1) if m else None
        if m and sec is not None and not _next(sec["no"], no) and len(no) >= 2 and no[1:].isdigit() and _next(sec["no"], no[1:]):
            no = no[1:]                      # a note marker glued to the number: "17. Requirements" is 7
        if m and (sec is None and int(re.match(r"\d+", no).group()) <= 3 or sec and (_next(sec["no"], no) or (spec.get("allowJump") and int(re.match(r"\d+", no).group()) > int(re.match(r"\d+", sec["no"]).group())))):
            if cur is None: cur = {"heading": spec.get("unit", "Regulation") + "s", "sections": []}; parts.append(cur)
            sec = {"no": no, "title": m.group(2).strip(), "text": [m.group(3).strip()] if m.group(3).strip() else [], "bookPage": p["page"]}
            cur["sections"].append(sec); skipping = False; continue
        if m and sec is not None:
            # the same provision again: a superseded page and its replacement were both scanned
            words = lambda x: set(re.findall(r"[a-z]{4,}", x.lower()))
            old = next(((pt, k) for pt in parts for k, z in enumerate(pt["sections"]) if z["no"] == no and words(z["title"]) and len(words(z["title"]) & words(m.group(2))) / len(words(z["title"])) >= 0.5), None)
            if old:
                pt, k = old
                if CODES.get(p["page"], -1) > CODES.get(pt["sections"][k]["bookPage"], -1):
                    del pt["sections"][k:]
                    for later in parts[parts.index(pt) + 1:]: later["sections"].clear()
                    cur = pt
                    sec = {"no": no, "title": m.group(2).strip(), "text": [m.group(3).strip()] if m.group(3).strip() else [], "bookPage": p["page"]}
                    cur["sections"].append(sec); skipping = False
                else: skipping = True
                continue
        if skipping: continue
        if sec is None: preamble.append(t)
        else:
            if cur and not cur["sections"] and parts and len(parts) > 1 and not sec: pass
            sec["text"].append((">" if re.match(r"^\(\s*[a-z]{1,4}\s*\)", t) else "") + t)
    for part in parts:
        for s in part["sections"]:
            s["text"] = [x for k, x in enumerate(s["text"]) if x and (k == 0 or x != s["text"][k - 1])]
    return preamble, [p for p in parts if p["sections"]]


REST = []
SCHED_HEAD = re.compile(r"^[\W\d]{0,3}(THE\s+)?(([A-Z]+)\s+)?(SCHEDULES?|ANNEXURES?|APPENDIX|APPENDICES|FORMS?)\b", re.I)
def _sched_key(title):
    m = re.search(r"\b(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)?\s*(SCHEDULE|ANNEXURE|APPENDIX|FORM)(?:\s*[-–]?\s*No\.?)?(?:[\s-]+(?:[IVX]{1,4}|[A-Z]|\d{1,2})(?![A-Za-z]))?", title, re.I)
    return re.sub(r"[^a-z0-9]", "", m.group(0).lower()) if m else re.sub(r"[^a-z0-9]", "", title.lower())[:20]
def schedule_sections(rest):
    """The schedules, annexures and forms printed after the last provision, as [{title, text}] (text read as it comes: tables and blanks are simplified).
    Where a schedule was printed twice (a page and its later replacement) only the newest version is kept."""
    rows = []
    for l in rest:
        t = strip_markers(l["text"]).strip()
        if re.match(r"^Following is the text of", t) or re.match(r"^Misc(ellaneous|\.)\s+(Notes|Notifications|Circulars)", t, re.I): break
        if re.search(r"\b(Part|Pt\.?)\s+[IVX]+[,.]\s", t) and len(t) < 50: continue            # running head
        if t and not (rows and rows[-1][0] == t and len(t) < 90): rows.append((t, l["page"]))
    out, cur = [], None
    k = 0
    while k < len(rows):
        t, pg = rows[k]
        if SCHED_HEAD.match(t) and len(t) < 46 and not re.search(r"[a-z]{3,}.*\b(shall|may|is|are)\b", t):
            title = t.strip(" .-\"[")
            while k + 1 < len(rows) and (re.match(r"^[\[(]\s*[Ss]ee\b", rows[k + 1][0]) or (rows[k + 1][0].isupper() and len(rows[k + 1][0]) < 60 and not SCHED_HEAD.match(rows[k + 1][0]) and len(title) < 90)):
                title += " " + rows[k + 1][0].strip(); k += 1
            cur = {"title": title, "text": [], "pages": {pg}}; out.append(cur)
        else:
            if cur is None: cur = {"title": "Schedules, annexures and forms (as printed)", "text": [], "pages": set()}; out.append(cur)
            cur["pages"].add(pg)
            lab = re.match(r"^\(\s*([a-z]{1,4}|\d{1,2})\s*\)", t)
            prev = cur["text"][-1] if cur["text"] else ""
            joins = prev and not re.search(r"[.:;\]\")]\s*$", prev) and re.match(r"^[a-z,(]", t) and not lab
            if joins: cur["text"][-1] = prev + " " + t
            else: cur["text"].append((">" if lab and not lab.group(1).isdigit() else "") + t)
        k += 1
    best = {}
    for x in out:
        if not x["text"]: continue
        key = _sched_key(x["title"]); x["code"] = max((CODES.get(pg, -1) for pg in x["pages"]), default=-1)
        old = best.get(key)
        if old is None or (x["code"], len(x["text"])) > (old["code"], len(old["text"])): best[key] = x
    keep = {id(v) for v in best.values()}
    return [{"title": x["title"], "text": x["text"]} for x in out if id(x) in keep]

# looser heading endings ("Title: text", "Title. Text", "Title- Text", "Title - (1)"), used only for the
# number expected next
PROV2 = re.compile(r"^[\"“\[]?(\d{1,3}[A-Z]{0,2})[.,]\s*([A-Z][^.:;\n]{2,110}?)\s*(?:[.:,]|\s[-–—]|[-–—])\s+(?=[A-Z(\[\d])(.*)$")

def _expected(prev, nxt):
    a, b = re.match(r"(\d+)([A-Z]*)", prev), re.match(r"(\d+)([A-Z]*)", nxt)
    return int(b.group(1)) == int(a.group(1)) + 1 and not b.group(2)

def _next(prev, nxt):
    """Accept the next provision number (2 after 1, 5A after 5, 6 after 5A) — guards against cross-references."""
    def key(n):
        m = re.match(r"(\d+)([A-Z]*)", n); return int(m.group(1)), m.group(2)
    (p, ps), (n, ns) = key(prev), key(nxt)
    return (p < n <= p + 8 and ns in ("", "A")) or (n == p and ns > ps)

def add_to_manifest(spec):
    """Append a manifest entry (no PDF: the text comes from the printed edition) unless one exists."""
    mp = ROOT / "sources/manifest.json"
    txt = mp.read_text()
    if any(e["id"] == spec["id"] for e in json.loads(txt)): return
    e = {"id": spec["id"], "title": spec["title"], "number": spec.get("number", ""), "type": spec["type"], "unit": spec["unit"]}
    if spec.get("parent"): e["parent"] = spec["parent"]
    e["categories"] = spec.get("categories", ["corporate"]); e["aliases"] = spec.get("aliases", [])
    if spec.get("enacted"): e["enacted"] = spec["enacted"]
    e["textFrom"] = "printed-edition"
    e["source"] = {"name": f"Gazette of Pakistan, {spec.get('number', '')}".strip(", "), "url": spec.get("sourceUrl", "https://www.secp.gov.pk")}
    e["amendedUpTo"] = spec["amendedUpTo"]; e["amendedUpToLabel"] = spec["amendedUpToLabel"]
    if spec.get("caution"): e["caution"] = spec["caution"]
    if spec.get("status"): e["status"] = spec["status"]
    e["watch"] = spec.get("watch", {"page": "https://www.secp.gov.pk/laws/regulations/", "manual": True})
    block = "\n".join("  " + ln for ln in json.dumps(e, indent=2, ensure_ascii=False).splitlines())
    mp.write_text(txt.rstrip()[:-1].rstrip() + ",\n" + block + "\n]\n")

SPEC_NOINSERTS = False
for i in a.ids:
    spec = SPEC[i]
    SPEC_NOINSERTS = bool(spec.get("excludeInserts"))
    if a.pages_only:
        if spec.get("scanFrom"): sc, pgs = [(spec["file"], k) for k in range(spec["scanFrom"], spec["scanTo"] + 1)], []
        else: sc, pgs = scans_for(spec["part"], spec["from"], spec["to"], spec.get("fileHint"))
        where = {(l["file"], l["scan"]): pg for pg in pgs for l in PM[pg]}
        out = ROOT / "data/salam/pages"; out.mkdir(exist_ok=True)
        json.dump({"id": i, "scans": [{"file": f, "scan": k, "bookPage": where.get((f, k))} for f, k in sc]}, open(out / f"{i}.json", "w"), indent=1)
        print(i, len(sc), "scan pages"); continue
    preamble, parts = convert(spec)
    if os.environ.get("BOOK_SCHEDULES"):
        sched = schedule_sections(REST)
        f = ROOT / "data/acts" / f"{i}.json"
        d0 = json.load(open(f))
        d0["schedules"] = [x for x in d0.get("schedules", []) if not x.get("text")] + sched
        if sched: d0["schedulesNote"] = "Schedules, annexures and forms are given as text read from the printed edition; the layout of tables and blanks is simplified, so consult the printed form where its layout matters. Unverified."
        else: d0.pop("schedulesNote", None)
        json.dump(d0, open(f, "w"), indent=2, ensure_ascii=False)
        print(i, len(sched), "schedules/forms,", sum(len(x["text"]) for x in sched), "paragraphs"); continue
    pages = {s.pop("bookPage") for p in parts for s in p["sections"]}
    if spec.get("titleFromText") and parts and parts[0]["sections"]:
        first = " ".join(parts[0]["sections"][0]["text"][:1])
        mt = re.search(r"(?:may|shall)\s+be\s+called\s+(?:as\s+)?(?:the\s+)?[\"“]?(.+?\d{4})", first)
        if mt: spec["title"] = re.sub(r"\.\s*(\d{4})$", r", \1", re.sub(r"\s+", " ", mt.group(1)).strip(" \"”[]"))
    m = re.search(r"S\.\s*R\.\s*O\.?\s*(?:No\.?\s*)?(\d{1,4})\s*\(I\)\s*/\s*(\d{2,4})(?:,?\s*(?:dated|Islamabad,?\s*the)\s*([A-Za-z]+\.?\s+\d{1,2},?\s*\d{4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s*\d{4}))?", " ".join(preamble))
    ma = re.search(r"\b(Act|Ordinance)\s+No\.?\s*([IVXLC]+)\s+of\s+(\d{4})", " ".join(preamble), re.I)
    if ma and not spec.get("number") and spec["type"] in ("act", "ordinance"):
        spec["number"] = f"{ma.group(1).title()} No. {ma.group(2).upper()} of {ma.group(3)}"
    if m and not spec.get("number"):
        y = m.group(2) if len(m.group(2)) == 4 else ("19" if int(m.group(2)) > 50 else "20") + m.group(2)
        spec["number"] = f"S.R.O. {int(m.group(1))}(I)/{y}"
    if m and m.group(3) and not spec.get("enacted"):
        from datetime import datetime
        d = re.sub(r"(st|nd|rd|th)\b|,|\.", "", m.group(3)).split()
        for fmt in ("%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y"):
            try: spec["enacted"] = datetime.strptime(" ".join(d), fmt).strftime("%Y-%m-%d"); break
            except ValueError: pass
    nsec = sum(len(p["sections"]) for p in parts)
    act = {
        "id": i, "title": spec["title"], "number": spec.get("number", ""), "type": spec["type"], "unit": spec["unit"],
        **({"parent": spec["parent"]} if spec.get("parent") else {}),
        "categories": spec.get("categories", ["corporate"]), "aliases": spec.get("aliases", []),
        **({"enacted": spec["enacted"]} if spec.get("enacted") else {}),
        "lastAmended": spec["amendedUpTo"], "amendedUpToLabel": spec["amendedUpToLabel"],
        "status": spec.get("status", "in-force"),
        **({"caution": spec["caution"]} if spec.get("caution") else {}),
        "source": {"name": spec.get("sourceName", f"Gazette of Pakistan, {spec.get('number', '')}".strip(", ")), "url": spec.get("sourceUrl", "https://www.secp.gov.pk")},
        "verification": {"status": "unverified", "note": f"Text converted from a printed consolidated edition updated to {spec['amendedUpToLabel']} and read by machine; not yet checked against the Gazette or SECP's copy. Check before quoting."},
        "preamble": " ".join(preamble),
        "parts": parts, "schedules": [],
        "frontNotes": spec.get("frontNotes", []),
    }
    out_dir = Path(os.environ["BOOK_OUT"]) if os.environ.get("BOOK_OUT") else ROOT / "data/acts"   # BOOK_OUT: compare-only run, library untouched
    json.dump(act, open(out_dir / f"{i}.json", "w"), indent=2, ensure_ascii=False)
    if not os.environ.get("BOOK_OUT"): add_to_manifest(spec)
    nums = [s["no"] for p in parts for s in p["sections"]]
    if INFERRED and os.environ.get("BOOK_OUT") is None:
        f = ROOT / "data/salam/inferred-headings.json"
        d0 = json.load(open(f)) if f.exists() else {}
        d0.update(INFERRED); json.dump(d0, open(f, "w"), indent=1)
    print(f"{i}: {nsec} provisions ({nums[0] if nums else '-'}..{nums[-1] if nums else '-'}), {len(parts)} part(s), {('scans ' + str(spec['scanFrom']) + '..' + str(spec['scanTo'])) if spec.get('scanFrom') else 'book pages ' + spec['part'] + '-' + str(spec['from']) + '..' + str(spec['to'])}")
