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
ap.add_argument("ids", nargs="+")
a = ap.parse_args()
SC = Path(a.scans)
PM = json.load(open(SC / "_ocr text" / "page-map.json"))
SPEC = {c["id"]: c for c in json.load(open(ROOT / "data/salam/conversions.json"))["instruments"]}

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

def scans_for(part, lo, hi):
    """Scan pages to read, in order: every scan from the first to the last mapped page of the range
    (unnumbered pages in between included), the unnumbered title page just before, and only the
    newest copy of a page that was scanned twice."""
    pages = book_pages(part, lo, hi)
    chosen = {pg: pick(PM[pg]) for pg in pages}
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
    banded, n, ov = [], 4, 0.05
    for k in range(n):
        c0, c1 = k / n, (k + 1) / n
        b0, b1 = max(0, c0 - ov), min(1, c1 + ov)
        img = os.path.join(tmp, f"band{k}.png")
        page.get_pixmap(dpi=300, colorspace=fitz.csGRAY, clip=fitz.Rect(r.x0, r.y0 + r.height * b0, r.x1, r.y0 + r.height * b1)).save(img)
        for x0, y0, x1, y1, t in vision(img):
            y0, y1 = b0 + y0 * (b1 - b0), b0 + y1 * (b1 - b0)
            if c0 <= (y0 + y1) / 2 < c1 or (k == n - 1 and (y0 + y1) / 2 >= c1): banded.append([x0, y0, x1, y1, t])
    if not whole and not banded: return [], 0
    rows_b, rows_w = to_rows(banded), to_rows(whole)
    rows = []
    for rb in rows_b:
        match = [rw for rw in rows_w if abs(rw["y"] - rb["y"]) < 0.006]
        rows.append(max([rb] + match, key=lambda x: (quality(x["text"]), len(x["text"]))))
    for rw in rows_w:
        if not any(abs(rw["y"] - rb["y"]) < 0.006 for rb in rows_b): rows.append(rw)
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
        if top and (HEAD_WORDS.search(t) or re.fullmatch(r"(S|R|Reg|Rr|Ss)\.?\s*[\d\- ,A-Z]+|\d{1,3}", t.strip()) or re.sub(r"[^a-z]", "", t.lower()) in short_names and len(t) < 90):
            continue
        top = False
        if FOOT.search(t) or re.match(r"^[A-ZПШIl1|]{1,4}\s*[-–]\s*\d{1,4}(\(\d+\))?\s+(Pt\.|Part|Company)", t): continue
        # footnotes: smaller type, starting with a note number
        if r["h"] < body_h * 0.82 and (re.match(r"^\W?\d{1,2}\s?[A-Z]", t) or keep and keep[-1].get("foot")):
            r["foot"] = True
        if r["h"] < body_h * 0.82 and keep and keep[-1].get("foot"): r["foot"] = True
        keep.append(r)
    return [r for r in keep if not r.get("foot")]

FN = re.compile(r"^\W{0,2}\d{1,2}\s?(Repealed|Substituted|Inserted|Omitted|Deleted|Added|Words?\b|Sub-|Clause|Proviso|Para|Item|S\.\s?No|Sr\.|Earlier|Regulations?\b|Rules?\b|Explanation|Figures?\b|Comma|Full stop|Renumbered|Amended|The (word|words|figure|figures|comma)|For the|Re-?numbered|Heading|Schedule|Annexure|Form)")
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
        if mode == "body" and FN.match(t):
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
    t = re.sub(r"(?<![\w(])[0-9¹²³*°•']{1,2}\s?(?=\[)", "", t)       # note number before an amendment bracket
    return re.sub(r"\s+", " ", t).strip()

LABEL = re.compile(r"^(\(\s*(?:[a-z]{1,2}|[ivxlc]{1,6}|\d{1,3}[a-zA-Z]?|[A-Z])\s*\)|Explanation|Provided|\d{1,3}[A-Z]?\.\s)")
PROV = re.compile(r"^[\"“]?(\d{1,3}[A-Z]{0,2})[.,]\s*([A-Z\[][^\n]{1,200}?)\s*(?:[.:]\s*[-–—_]+|\.(?=\s*\(\d)|\.(?=\s*\d?\[?\(1\)))\s*(.*)$")

def convert(spec):
    scans, pages = scans_for(spec["part"], spec["from"], spec["to"])
    if not scans: raise SystemExit(f"{spec['id']}: no book pages found")
    where = {(l["file"], l["scan"]): pg for pg in pages for l in PM[pg]}
    got = []
    with tempfile.TemporaryDirectory() as tmp:
        for f, k in scans: got.append(((f, k),) + ocr_rows(scan_pdf(f), k - 1, tmp))
    # running heads: short lines that recur among the first rows of the instrument's pages
    from collections import Counter
    norm = lambda t: re.sub(r"[^a-z]", "", t.lower())
    tops = Counter(n for _, rows, _ in got for n in {norm(r["text"]) for r in rows[:4] if len(r["text"]) < 90} if len(n) > 6)
    heads = [n for n, c in tops.items() if c >= 2] + [norm(h) for h in spec.get("runningHeads", [])]
    lines = []
    for (f, k), rows, left in got:
        for r in clean_page(rows, heads):
            lines.append({"page": where.get((f, k), f"scan {k}"), "x": r["x"] - left, "text": r["text"]})
    lines = drop_footnotes(lines)
    if os.environ.get("BOOK_DEBUG"):
        Path(os.environ["BOOK_DEBUG"], spec["id"] + ".dropped.txt").write_text("\n".join(f'{k}\t{l["page"]}\t{l["text"]}' for k, l in DROPPED))
        Path(os.environ["BOOK_DEBUG"], spec["id"] + ".lines.txt").write_text("\n".join(f'{l["page"]}\t{l["x"]:.3f}\t{l["text"]}' for l in lines))
    # start at the S.R.O. recital / title, stop at the end marker
    start = next((i for i, l in enumerate(lines) if re.search(spec.get("startAt", r"S\.\s*R\.\s*O\.|In exercise"), l["text"])), 0)
    lines = lines[start:]
    pos, prev = [], None
    for l in lines:
        pos.append(0 if l["page"] != prev else pos[-1] + 1); prev = l["page"]
    stop = spec.get("stopAt", r"^(\w{1,5}\.\s*)?(FORMS?|Forms?|ANNEXURES?|Annexures?|SCHEDULES?|Schedules?)\b[\s\-–—.:]*([A-Z0-9IVX]{1,5}[A-Z0-9\-]{0,4})?\.?$")
    end = next((i for i, l in enumerate(lines) if re.search(stop, l["text"].strip()) and len(l["text"]) < 40 and pos[i] <= 3), len(lines))
    lines = lines[:end]
    # paragraphs
    paras = []
    for l in lines:
        t = l["text"]
        ends = not paras or re.search(r"([.:;\-–—\]\"”)]|\band|\bor)\s*$", paras[-1]["text"].rstrip()) or paras[-1]["text"].isupper()
        new = (not paras or PROV.match(t) or re.match(r"^[\"“]?\d{1,3}[A-Z]{0,2}[.,]\s*[A-Z]", t) and ends or t.isupper() and len(t) > 12 or LABEL.match(t) and ends or re.match(r"^(CHAPTER|PART)\b", t)
               or l["x"] > 0.035 and ends)
        if new: paras.append({"page": l["page"], "text": t})
        else: paras[-1]["text"] = (paras[-1]["text"][:-1] if re.search(r"[a-z]-$", paras[-1]["text"]) else paras[-1]["text"] + " ") + t
    preamble, parts, cur, sec = [], [], None, None
    for p in paras:
        t = strip_markers(p["text"])
        if re.match(r"^(CHAPTER|PART)\s+[IVXL\d]+", t) and len(t) < 120:
            cur = {"heading": t.title() if t.isupper() else t, "sections": []}; parts.append(cur); continue
        m = PROV.match(t)
        if m and (sec is None and int(re.match(r"\d+", m.group(1)).group()) <= 3 or sec and _next(sec["no"], m.group(1))):
            if cur is None: cur = {"heading": spec.get("unit", "Regulation") + "s", "sections": []}; parts.append(cur)
            sec = {"no": m.group(1), "title": m.group(2).strip(), "text": [m.group(3).strip()] if m.group(3).strip() else [], "bookPage": p["page"]}
            cur["sections"].append(sec); continue
        if sec is None: preamble.append(t)
        else:
            if cur and not cur["sections"] and parts and len(parts) > 1 and not sec: pass
            sec["text"].append((">" if re.match(r"^\(\s*[a-z]{1,4}\s*\)", t) else "") + t)
    for part in parts:
        for s in part["sections"]:
            s["text"] = [x for x in s["text"] if x]
    return preamble, [p for p in parts if p["sections"]]

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
    e["watch"] = spec.get("watch", {"page": "https://www.secp.gov.pk/laws/regulations/", "manual": True})
    block = "\n".join("  " + ln for ln in json.dumps(e, indent=2, ensure_ascii=False).splitlines())
    mp.write_text(txt.rstrip()[:-1].rstrip() + ",\n" + block + "\n]\n")

for i in a.ids:
    spec = SPEC[i]
    preamble, parts = convert(spec)
    pages = {s.pop("bookPage") for p in parts for s in p["sections"]}
    m = re.search(r"S\.\s*R\.\s*O\.?\s*(?:No\.?\s*)?(\d{1,4})\s*\(I\)\s*/\s*(\d{2,4})(?:,?\s*(?:dated|Islamabad,?\s*the)\s*([A-Za-z]+\.?\s+\d{1,2},?\s*\d{4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s*\d{4}))?", " ".join(preamble))
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
        "source": {"name": spec.get("sourceName", f"Gazette of Pakistan, {spec.get('number', '')}".strip(", ")), "url": spec.get("sourceUrl", "https://www.secp.gov.pk")},
        "verification": {"status": "unverified", "note": f"Text converted from a printed consolidated edition updated to {spec['amendedUpToLabel']} and read by machine; not yet checked against the Gazette or SECP's copy. Check before quoting."},
        "preamble": " ".join(preamble),
        "parts": parts, "schedules": [],
        "frontNotes": spec.get("frontNotes", []),
    }
    json.dump(act, open(ROOT / "data/acts" / f"{i}.json", "w"), indent=2, ensure_ascii=False)
    add_to_manifest(spec)
    nums = [s["no"] for p in parts for s in p["sections"]]
    print(f"{i}: {nsec} provisions ({nums[0] if nums else '-'}..{nums[-1] if nums else '-'}), {len(parts)} part(s), book pages {spec['part']}-{spec['from']}..{spec['to']}")
