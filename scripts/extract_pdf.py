#!/usr/bin/env python3
"""Extract a consolidated statute PDF (FBR / SECP style) into the library's JSON format.

Uses font size, weight and superscript flags from the PDF, not plain text, so that:
  * running headers, footers and page numbers are dropped,
  * amendment footnotes are separated from the body and attached to the provision
    that cites them (the in-text marker becomes {fn:N}),
  * provisions start at a bold "12A." number followed by a bold heading,
  * PART / CHAPTER headings and SCHEDULES become parts.

Usage:
  python3 scripts/extract_pdf.py <manifest-entry-id>          # one document
  python3 scripts/extract_pdf.py --all                        # every manifest entry
Writes data/acts/<id>.json and prints a completeness report against the PDF's own
table of contents. Requires PyMuPDF (pip install pymupdf).
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "sources" / "manifest.json"

NUM_RE = re.compile(r"^\d+[A-Z]{0,4}\.$")
HEADING_RE = re.compile(r"^(PART|CHAPTER|Chapter|Part)[\s\-–—]*([IVXLC]+|\d+[A-Z]?)\b", re.I)
SCHEDULE_RE = re.compile(r"^\[?\s*(THE\s+)?([A-Z]+(-[A-Z]+)?\s+)?SCHEDULE\b", re.I)
ANNEX_RE = re.compile(r"^\[?\s*(ANNEX(URE)?|Annex(ure)?|APPENDIX|Appendix)\b[\s\-–—]*[A-Z0-9IVX]{0,6}\s*\]?$")
LEADERS = re.compile(r"\.{5,}|…{2,}")
CLAUSE_RE = re.compile(r"^\[*\s*\(([0-9]+[A-Z]*|[a-z]{1,3}|[A-Z]{1,3})\)")
ROMAN = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii", "xiv", "xv",
         "xvi", "xvii", "xviii", "xix", "xx", "xxi", "xxii", "xxiii", "xxiv", "xxv"}


def norm_space(s):
    return re.sub(r"\s+", " ", s).strip()


class Line:
    __slots__ = ("page", "y", "x", "spans", "size", "kp")

    def __init__(self, page, y, x, spans, kp=None):
        self.page, self.y, self.x, self.spans = page, y, x, spans
        self.kp = kp if kp is not None else str(page + 1)
        sizes = [s["size"] for s in spans if s["text"].strip()]
        self.size = max(sizes) if sizes else 0

    @property
    def text(self):
        return "".join(s["text"] for s in self.spans)


def load_lines(doc):
    """Return lines per page, merging PyMuPDF lines that share a baseline."""
    pages = []
    for pno, page in enumerate(doc):
        raw = []
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                spans = [s for s in l["spans"] if s["text"]]
                if spans and any(s["text"].strip() for s in spans):
                    raw.append(spans)
        # group spans into visual lines by vertical centre
        items = []
        for spans in raw:
            for s in spans:
                cy = (s["bbox"][1] + s["bbox"][3]) / 2
                items.append((cy, s["bbox"][0], s))
        items.sort(key=lambda t: (round(t[0]), t[1]))
        lines = []
        for cy, x, s in items:
            if lines and abs(lines[-1][0] - cy) <= max(3.0, s["size"] * 0.45):
                lines[-1][1].append(s)
            else:
                lines.append([cy, [s]])
        out = []
        for cy, spans in lines:
            spans.sort(key=lambda s: s["bbox"][0])
            out.append(Line(pno, cy, spans[0]["bbox"][0], spans))
        pages.append(out)
    return pages


def body_size(pages):
    c = Counter()
    for lines in pages:
        for l in lines:
            for s in l.spans:
                c[round(s["size"])] += len(s["text"].strip())
    return c.most_common(1)[0][0]


def running_lines(pages):
    """Header/footer texts: lines at page extremes whose digit-normalised text repeats."""
    c = Counter()
    for lines in pages:
        for l in lines[:2] + lines[-2:]:
            c[re.sub(r"\d+", "#", norm_space(l.text))] += 1
    limit = max(3, len(pages) * 0.25)
    return {k for k, v in c.items() if v >= limit}


def is_small(s, bs):
    return s["size"] <= bs * 0.8


def is_ref(s, bs):
    t = s["text"].strip()
    return bool(re.fullmatch(r"\d{1,4}[a-z]?(\s*[,&]\s*\d{1,4}[a-z]?)*\[?", t)) and (s["flags"] & 1 or s["size"] <= bs * 0.75)


def refs(s, kp):
    t = s["text"].strip()
    tail = "[" if t.endswith("[") else ""
    return "".join("{fn:%s-%s}" % (kp, n.strip()) for n in re.split(r"[,&]", t.rstrip("["))) + tail


def is_bold(s):
    return bool(s["flags"] & 16) or "Bold" in s["font"]


def split_footnotes(lines, bs):
    """Split one page's lines into (body, footnotes).

    Footnotes are the unbroken block of small-text lines at the bottom of the page.
    Returns footnotes as [(num|None, text)]; None marks a continuation from the previous page.
    """
    def small(l):
        spans = [s for s in l.spans if s["text"].strip()]
        return bool(spans) and all(s["size"] < bs - 0.4 for s in spans)

    start = len(lines)
    while start > 0 and small(lines[start - 1]):
        start -= 1
    # a block that does not start with a numbered note and is only one short line is body text
    block = lines[start:]
    if not block:
        return lines, []
    notes = []
    for l in block:
        spans = [s for s in l.spans if s["text"].strip()]
        if spans and is_ref(spans[0], bs) and len(spans) > 1 and "," not in spans[0]["text"]:
            idx = l.spans.index(spans[0])
            notes.append([spans[0]["text"].strip(), norm_space("".join(s["text"] for s in l.spans[idx + 1:]))])
        elif spans and re.fullmatch(r"\d{1,4}", spans[0]["text"].strip()) and len(spans) > 1 and spans[0]["size"] < spans[1]["size"]:
            idx = l.spans.index(spans[0])
            notes.append([spans[0]["text"].strip(), norm_space("".join(s["text"] for s in l.spans[idx + 1:]))])
        elif re.match(r"^\s*(\d{1,4}[a-z]?)\.\s+\S", l.text):
            mm = re.match(r"^\s*(\d{1,4}[a-z]?)\.\s+(.*)$", l.text)
            notes.append([mm.group(1), norm_space(mm.group(2))])
        elif notes:
            notes[-1][1] = norm_space(notes[-1][1] + " " + l.text)
        else:
            notes.append([None, norm_space(l.text)])
    # split notes that swallowed "20. Substituted ..." style successors in the same line
    out = []
    for num, text in notes:
        pieces = re.split(r"(?<=[.”\]])\s+(\d{1,4}[a-z]?)\.\s+(?=[A-Z])", text)
        out.append([num, pieces[0]])
        for k in range(1, len(pieces) - 1, 2):
            if num and re.fullmatch(r"\d+", num) and re.fullmatch(r"\d+", pieces[k]) and not (0 < int(pieces[k]) - int(num) <= 15):
                out[-1][1] += " %s. %s" % (pieces[k], pieces[k + 1])
                continue
            out.append([pieces[k], pieces[k + 1]])
            num = pieces[k] if re.fullmatch(r"\d+", pieces[k]) else num
    return lines[:start], out


def line_text(l, bs):
    """Body text of a line with footnote references rendered as {fn:N}."""
    out = []
    for s in l.spans:
        t = s["text"]
        if is_ref(s, bs):
            if out and re.search(r"[\w.,;:)\]]$", out[-1]):
                out.append(" ")
            out.append(refs(s, l.kp))
        elif s["flags"] & 1 and s["size"] <= bs * 0.8:
            out.append(t.strip())  # ordinal suffixes such as "st", "th"
        else:
            out.append(t)
    return re.sub(r"[ \t]+", " ", "".join(out)).strip()


def section_start(l, bs, untitled=False):
    """If the line begins a provision, return (number, heading, lead, rest_of_line)."""
    spans = [s for s in l.spans if s["text"].strip()]
    i = 0
    lead = ""
    while i < len(spans) and (is_ref(spans[i], bs) or spans[i]["text"].strip() in ("[", "[[", "“", "[“", "\"", "{")):
        lead += refs(spans[i], l.kp) if is_ref(spans[i], bs) else spans[i]["text"].strip()
        i += 1
    if i >= len(spans) or LEADERS.search(l.text):
        return None
    first = spans[i]["text"].strip()
    m = re.match(r"^([\[“\"{\s]*)(\d+[A-Z]{0,4})(\.?)\s*(.*)$", first)
    if not m:
        return None
    lead += m.group(1)
    number, dot, tail = m.group(2), m.group(3), m.group(4)
    if spans[i]["size"] < bs - 1.5:
        return None
    num_bold = is_bold(spans[i])
    j = i + 1
    if not dot:
        if tail.startswith("."):
            dot, tail = ".", tail[1:].strip()
        elif j < len(spans) and spans[j]["text"].strip().startswith("."):
            dot = "."
            tail = spans[j]["text"].strip()[1:].strip()
            j += 1
    if not dot:
        nxt = spans[j]["text"].strip() if j < len(spans) else ""
        if tail.startswith("*") or re.match(r"^OMITTED\b|^Omitted\b", tail):
            dot = "."
        elif num_bold and re.match(r"^[A-Z][^.]{3,150}\.?\s*[-–—]", tail):
            dot = "."
        elif num_bold and not tail and nxt and (is_bold(spans[j]) and nxt.lstrip("“\"[")[:1].isupper()):
            dot = "."
        else:
            return None
    nxt_t = spans[j]["text"].strip() if j < len(spans) else ""
    omitted = tail.startswith("*") or re.match(r"^\[?\s*Omitted\b", tail, re.I) is not None or (
        not tail and (nxt_t.startswith("***") or re.match(r"^\[?\s*Omitted\b", nxt_t, re.I) is not None))
    head_parts = [tail] if tail and not omitted else []
    head_bold = False
    while j < len(spans) and not omitted and (is_bold(spans[j]) or is_ref(spans[j], bs) or spans[j]["text"].strip() in ("[", "“")):
        if is_ref(spans[j], bs):
            head_parts.append(refs(spans[j], l.kp))
        elif not is_bold(spans[j]):
            lead += spans[j]["text"].strip()
        else:
            head_parts.append(spans[j]["text"])
            head_bold = head_bold or bool(spans[j]["text"].strip())
        j += 1
    if omitted:
        rest_spans = spans[i + 1:]
        rest = norm_space(tail + " " + line_text(Line(l.page, l.y, l.x, rest_spans, l.kp), bs)) if rest_spans else tail
        return number, "[Omitted]", lead, rest
    if tail and not num_bold and not head_bold:
        # "12. Heading.- text" wholly in regular type: accept only if it looks like "Heading.—"
        if not re.match(r"^[A-Z][^.]{2,150}\.?\s*[-–—]{1,2}", tail):
            if untitled and lead.endswith("[") and tail[:1].isupper():
                return number, "", lead, tail + (" " + line_text(Line(l.page, l.y, l.x, spans[j:], l.kp), bs) if j < len(spans) else "")
            return None
    elif not (num_bold or head_bold):
        return None
    heading = norm_space("".join(head_parts))
    if not heading:
        if untitled and num_bold and j < len(spans):
            return number, "", lead, line_text(Line(l.page, l.y, l.x, spans[j:], l.kp), bs)
        return None
    if not head_bold and not num_bold:
        pass
    rest = line_text(Line(l.page, l.y, l.x, spans[j:], l.kp), bs) if j < len(spans) else ""
    # Split "Heading.— text" at the heading delimiter (a dash after a full stop, a spaced dash, or an em dash).
    mm = re.match(r"^(.{2,200}?)(\.\s*[-–—―−]{1,2}|\s[–—―−]{1,2}(?=\s|\()|—|―|\.\s*$)(.*)$", heading)
    if mm and (mm.group(3).strip() or not head_bold):
        heading, rest = mm.group(1), norm_space(mm.group(3) + " " + rest)
    return number, heading, lead, rest


def clean_heading(h):
    h = re.sub(r"^[\s\-–—―“\"]+", "", h.strip())
    h = re.sub(r"[\s.\-–—―−:]+$", "", h)
    return h.strip()


def clause_level(text, prev_letter):
    m = CLAUSE_RE.match(re.sub(r"^(\{fn:[^}]+\})+", "", text))
    if not m:
        return None, prev_letter
    lab = m.group(1)
    if lab[0].isdigit():
        return 0, None
    if lab.islower():
        if lab in ROMAN and not (lab == "i" and prev_letter == "h") and not (lab == "v" and prev_letter == "u") \
                and not (lab == "x" and prev_letter == "w"):
            return 2, prev_letter
        return 1, lab
    return 3, prev_letter


def tidy_title(t, text):
    t = norm_space(re.sub(r"\{fn:[^}]+\}", " ", t))
    t = re.sub(r"(?<=[A-Za-z,])\[", " [", t)
    core = t.strip("[]*. ")
    first = re.sub(r"\{fn:[^}]+\}", "", text[0] if text else "").strip("[ ]")
    if not core and (not first or re.match(r"^(\*+|omitted)", first, re.I)):
        return "[Omitted]"
    if t.startswith("[") and t.count("[") > t.count("]"):
        t = t[1:]
    if t.endswith("]") and t.count("]") > t.count("["):
        t = t[:-1]
    t = re.sub(r"\s*\[$", "", t)
    return t.strip()


def new_page_guard(prev_y):
    return prev_y is None


def parts_have_sections(parts):
    return any(p["sections"] for p in parts)


def base_record(entry, parts, preamble, schedules):
    act = {
        "id": entry["id"],
        "title": entry["title"],
        "number": entry["number"],
        "type": entry["type"],
        "unit": entry.get("unit", "Section"),
        **({"parent": entry["parent"]} if entry.get("parent") else {}),
        "categories": entry["categories"],
        "aliases": entry.get("aliases", []),
        "enacted": entry.get("enacted"),
        "lastAmended": entry.get("amendedUpTo"),
        "amendedUpToLabel": entry.get("amendedUpToLabel"),
        "status": entry.get("status", "in-force"),
        "source": entry["source"],
        "sourcePdf": entry["file"],
        "verification": {
            "status": "unverified",
            "note": ("Text machine-extracted from the %s consolidated edition%s. Check against the Gazette before quoting."
                     if not entry.get("pdfOnly") else "Official %s PDF shown as published%s. Check against the Gazette before quoting.") % (
                entry["source"]["name"], (" updated to " + entry["amendedUpToLabel"]) if entry.get("amendedUpToLabel") else ""),
        },
        "preamble": preamble,
        "parts": parts,
    }
    for k in ("caution", "summary", "pdfOnly", "sourceNotes"):
        if entry.get(k):
            act[k] = entry[k]
    if schedules:
        act["schedules"] = schedules
    return {k: v for k, v in act.items() if v is not None}


def extract(entry):
    pdf = ROOT / "sources" / "pdf" / entry["file"]
    doc = pymupdf.open(pdf)
    if entry.get("pdfOnly"):
        return base_record(entry, [], "", []), {"id": entry["id"], "pages": len(doc), "pdfOnly": True}
    pages = load_lines(doc)
    bs = body_size(pages)
    running = running_lines(pages)
    endnotes = {}
    all_notes = []
    endnote_cut = {}
    if entry.get("endnotes"):
        block = 0
        in_notes = False
        for pno, lines in enumerate(pages):
            content = [l for l in lines if re.sub(r"\d+", "#", norm_space(l.text)) not in running]
            chars = sum(len(x["text"].strip()) for l in content for x in l.spans)
            small = sum(len(x["text"].strip()) for l in content for x in l.spans if x["size"] < bs - 1)
            mostly_small = chars > 80 and small / max(chars, 1) > 0.6
            cut = None
            if in_notes and not mostly_small:
                in_notes = False
                block += 1
            if not in_notes:
                for idx, l in enumerate(lines):
                    if re.fullmatch(r"LEGAL REFERENCES?", norm_space(l.text).upper()):
                        cut = idx
                        in_notes = True
                        break
            else:
                cut = 0
            kp = "n%d" % block
            for l in lines:
                l.kp = kp
            if cut is None:
                continue
            endnote_cut[pno] = cut
            notes_lines = [l for l in lines[cut:] if re.sub(r"\d+", "#", norm_space(l.text)) not in running
                           and not re.fullmatch(r"LEGAL REFERENCES?", norm_space(l.text).upper())]
            min_x = min((l.x for l in notes_lines), default=0)
            cur = None
            for l in notes_lines:
                t = norm_space(l.text)
                mm = re.match(r"^(\d{1,4}[a-z]?)\s*\.?\s*(.*)$", t)
                if mm and l.x <= min_x + 6:
                    cur = "%s-%s" % (kp, mm.group(1))
                    endnotes[cur] = mm.group(2)
                elif cur:
                    endnotes[cur] = norm_space(endnotes[cur] + " " + t)

    skip_before = entry.get("bodyStartPage", 1) - 1
    stop_after = entry.get("bodyEndPage")

    parts = []
    part = None
    section = None
    toc_numbers = []
    pending_heading = None  # (kind, label) waiting for its title line
    in_schedule = False
    schedules = []
    sched_hits = []
    last_no = [None]
    heading_open = [False]
    preamble = []
    last_notes = None
    prev_letter = None
    para_gap = None

    def new_part(heading):
        nonlocal part
        part = {"heading": heading, "sections": []}
        parts.append(part)

    for pno, lines in enumerate(pages):
        page_text = "\n".join(l.text for l in lines)
        leader_lines = sum(1 for l in lines if LEADERS.search(l.text))
        is_toc = leader_lines >= 3 or (lines and leader_lines / max(1, len(lines)) > 0.2)
        if is_toc:
            for l in lines:
                m = re.match(r"^\s*(\d+[A-Z]{0,4})\.", l.text)
                if m:
                    toc_numbers.append(m.group(1))
            if pno >= skip_before and not parts:
                continue
        if pno < skip_before or (stop_after and pno >= stop_after) or endnote_cut.get(pno) == 0:
            continue
        if pno in endnote_cut:
            lines = lines[:endnote_cut[pno]]
        body, notes = split_footnotes(
            [l for l in lines if re.sub(r"\d+", "#", norm_space(l.text)) not in running], bs)

        # attach footnotes: a note is kept on whichever provision references it
        page_notes = {}
        for num, text in notes:
            if num is None and last_notes is not None and last_notes:
                last_notes[-1]["text"] = norm_space(last_notes[-1]["text"] + " " + text)
            elif num:
                page_notes["%s-%s" % (lines[0].kp if lines else pno + 1, num)] = text
                all_notes.append((pno + 1, num, text))

        prev_y = None
        carry = None
        for l in body:
            if carry is not None:
                l = Line(l.page, l.y, carry.x, carry.spans + l.spans, l.kp)
                carry = None
            if re.fullmatch(r"\[?\d+[A-Z]{0,4}\.?", norm_space(re.sub(r"\{fn:[^}]+\}", "", line_text(l, bs)))) and any(
                    is_bold(x) for x in l.spans if x["text"].strip()) and not in_schedule:
                carry = l
                continue
            text = line_text(l, bs)
            if not text:
                continue
            bold_line = all(is_bold(s) or not s["text"].strip() or is_ref(s, bs) for s in l.spans)
            plain = norm_space(re.sub(r"\{fn:[^}]+\}", "", text))

            # Part / chapter / schedule headings (bold, short)
            if bold_line and len(plain) < 90 and HEADING_RE.match(plain.lstrip("[")) and not in_schedule:
                hm = HEADING_RE.match(plain.lstrip("["))
                kind = hm.group(0)
                label = hm.group(1).capitalize() + " " + hm.group(2).upper()
                rest = plain.lstrip("[")[len(kind):].strip(" .-–—:")
                new_part(label + (" — " + rest.title() if rest else ""))
                pending_heading = None if rest else part
                section = None
                prev_y = l.y
                continue
            if (entry.get("stopAtSchedule", True) and bold_line and len(plain) < 120 and SCHEDULE_RE.match(plain.lstrip("[")) and parts) or (
                    parts and body.index(l) < 4 and len(plain) < 60 and ANNEX_RE.match(plain)):
                # Schedules are mostly tables: record where each starts and link to the PDF page.
                in_schedule = True
                title = re.sub(r"^the\s+", "", norm_space(plain.strip("[]“”\"' ")), flags=re.I).title()
                if title.endswith("Schedule") or ANNEX_RE.match(plain):
                    sched_hits.append((title, pno + 1))
                section = None
                pending_heading = None
                prev_y = l.y
                continue
            if in_schedule:
                continue
            if pending_heading is not None and bold_line and plain.isupper() and len(plain) < 150:
                sep = " — " if "—" not in pending_heading["heading"] else " "
                pending_heading["heading"] += sep + plain.title()
                prev_y = l.y
                continue
            pending_heading = None

            st = None if in_schedule else section_start(l, bs, entry.get("untitledProvisions", False))
            if st:
                base = int(re.match(r"\d+", st[0]).group())
                prev_no = last_no[0]
                prev_base = int(re.match(r"\d+", prev_no).group()) if prev_no and re.match(r"\d+", prev_no) else 0
                if (base < prev_base or (prev_no == st[0]) or base > prev_base + 25
                        or (prev_no is None and base > 5)
                        or (st[1] == "" and base not in (prev_base, prev_base + 1))):
                    st = None
            if st:
                number, heading, lead, rest = st
                if part is None:
                    new_part("Preliminary")
                section = {"no": number, "title": clean_heading(re.sub(r"\{fn:[^}]+\}", "", heading)), "page": pno + 1, "text": [], "fn": []}
                hrefs = re.findall(r"\{fn:([^}]+)\}", lead + heading)
                first = (lead + " " + rest).strip() if rest or lead else ""
                first = re.sub(r"^[\s.\-–—―:]+", "", first)
                first = re.sub(r"^((?:\{fn:[^}]+\})*\[*)\s*[.\-–—―:]+\s*", r"\1", first)
                if hrefs:
                    first = "".join("{fn:%s}" % r for r in hrefs if "{fn:%s}" % r not in first) + first
                section["text"].append(first)
                heading_open[0] = not first.strip() or bool(re.fullmatch(r"(\{fn:[^}]+\})*\[*", first.strip()))
                part["sections"].append(section)
                last_no[0] = number
                prev_letter = None
                prev_y = l.y
                continue

            if section is None:
                if not is_toc and (preamble or re.match(r"^(WHEREAS|Whereas)\b", plain)):
                    preamble.append(plain)
                prev_y = l.y
                continue

            if heading_open[0]:
                heading_open[0] = False
                bold_prefix = []
                spans_nz = [x for x in l.spans if x["text"].strip()]
                k = 0
                while k < len(spans_nz) and (is_bold(spans_nz[k]) or is_ref(spans_nz[k], bs) or spans_nz[k]["text"].strip() in ("[", "]")):
                    bold_prefix.append(refs(spans_nz[k], l.kp) if is_ref(spans_nz[k], bs) else spans_nz[k]["text"])
                    k += 1
                cont = norm_space("".join(bold_prefix))
                if cont and k > 0:
                    mm = re.match(r"^(.*?)(\.\s*[-–—―−]{1,2}|\s[–—―−]{1,2}(?=\s|\()|—|―|\.\s*$)(.*)$", cont)
                    extra_text = ""
                    if mm:
                        cont, extra_text = mm.group(1), mm.group(3)
                    section["title"] = clean_heading(norm_space(section["title"] + " " + re.sub(r"\{fn:[^}]+\}", "", cont)))
                    rest_text = norm_space(extra_text + " " + line_text(Line(l.page, l.y, l.x, spans_nz[k:], l.kp), bs)) if k < len(spans_nz) else extra_text
                    rest_text = re.sub(r"^[\s.\-–—―−:]+", "", rest_text)
                    section["text"][-1] = norm_space(section["text"][-1] + " " + rest_text) if section["text"] else rest_text
                    prev_y = l.y
                    continue
            # paragraph break: vertical gap or a clause label at line start
            gap = (l.y - prev_y) if prev_y is not None else 0
            if gap > 0 and (para_gap is None or gap < para_gap):
                para_gap = max(gap, bs * 1.05)
            level, prev_letter_new = clause_level(text, prev_letter)
            prev_txt = section["text"][-1] if section["text"] else ""
            prev_open = bool(prev_txt) and bool(re.search(r"[A-Za-z0-9,]\s*$", re.sub(r"\{fn:[^}]+\}$", "", prev_txt))) \
                and not re.search(r"(\band|\bor|\bnamely)\s*,?\s*$", prev_txt)
            big_gap = gap < 0 or gap > (para_gap or bs * 1.2) * 1.45
            if new_page_guard(prev_y) and prev_open and level is None:
                big_gap = False
            new_page = prev_y is None
            starts_para = (
                (new_page and not prev_open) or (not new_page and big_gap)
                or (level is not None and not prev_open)
                or re.match(r"^\[?(Provided|Explanation|Illustration)", plain)
            )
            if level is not None:
                prev_letter = prev_letter_new
            if starts_para or not section["text"] or not section["text"][-1]:
                marker = ">" * (level or 0)
                if section["text"] and section["text"][-1] == "":
                    section["text"][-1] = marker + text
                else:
                    section["text"].append(marker + text)
            else:
                last = section["text"][-1]
                joiner = "" if last.endswith("-") and not last.endswith(" -") else " "
                section["text"][-1] = (last[:-1] if joiner == "" else last) + joiner + text
            prev_y = l.y

        # footnotes referenced on this page go to the provision that cites them (keys are page-unique)
        if page_notes:
            recent = [x for p in parts for x in p["sections"]][-40:]
            for key, text in page_notes.items():
                marker = "{fn:%s}" % key
                target = next((x for x in reversed(recent) if marker in x["title"] or any(marker in t for t in x["text"])), None)
                if target is None:
                    target = section or (recent[-1] if recent else None)
                if target is not None:
                    target["fn"].append({"n": key, "text": text})
                    last_notes = target["fn"]

    if endnotes:
        for p in parts:
            for x in p["sections"]:
                have = {f["n"] for f in x["fn"]}
                for key in dict.fromkeys(re.findall(r"\{fn:([^}]+)\}", x["title"] + " " + " ".join(x["text"]))):
                    if key in endnotes and key not in have:
                        x["fn"].append({"n": key, "text": endnotes[key]})

    # markers that repeat an earlier footnote number: use the nearest earlier note with that number
    if all_notes and not entry.get("endnotes"):
        for p in parts:
            for x in p["sections"]:
                have = {f["n"] for f in x["fn"]}
                for key in dict.fromkeys(re.findall(r"\{fn:([^}]+)\}", x["title"] + " " + " ".join(x["text"]))):
                    if key in have or "-" not in key:
                        continue
                    pg, num = key.split("-", 1)
                    if not pg.isdigit():
                        continue
                    cands = [(q, t) for q, n, t in all_notes if n == num and q <= int(pg)]
                    if cands:
                        x["fn"].append({"n": key, "text": max(cands)[1]})

    # tidy
    for p in parts:
        for s in p["sections"]:
            s["title"] = tidy_title(s["title"], s["text"])
            s["text"] = [norm_space(t) if not t.startswith(">") else ">" * (len(t) - len(t.lstrip(">"))) + norm_space(t.lstrip(">")) for t in s["text"] if norm_space(t.lstrip(">"))]
            if not s["text"]:
                s["text"] = ["[No text in source.]"]
            if not s["fn"]:
                del s["fn"]
    parts = [p for p in parts if p["sections"]]

    # de-duplicate provision numbers (e.g. the same number reused inside a schedule)
    seen = Counter()
    for p in parts:
        for s in p["sections"]:
            seen[s["no"]] += 1
            if seen[s["no"]] > 1:
                s["no"] = "%s-%d" % (s["no"], seen[s["no"]])

    per_page = Counter(pg for _, pg in sched_hits)
    index_pages = {pg for pg, c in per_page.items() if c >= 3}
    last = 0
    for title in dict.fromkeys(t for t, _ in sched_hits):
        pages_for = [pg for t, pg in sched_hits if t == title]
        good = [pg for pg in pages_for if pg >= last] or pages_for
        schedules.append({"title": title, "page": good[0]})
        last = good[0]
    pre_text = re.split(r"\s\[?(?:Chapter|CHAPTER|PART|Part)[\s\-–—]*(?:[IVXLC]+|\d+)\b", norm_space(" ".join(preamble)))[0] if preamble else ""
    pre = entry.get("preamble") or (pre_text if len(pre_text) < 700 else "")
    act = base_record(entry, parts, pre, schedules)

    got = [s["no"] for p in parts for s in p["sections"] if not s["no"].startswith("Sch-")]
    toc = list(dict.fromkeys(toc_numbers))
    missing = [n for n in toc if n not in got]
    extra = [n for n in got if toc and n not in toc and "-" not in n]
    report = {
        "id": entry["id"],
        "pages": len(pages),
        "provisions": len(got),
        "toc": len(toc),
        "missing": missing,
        "extra": extra,
        "footnotes": sum(len(s.get("fn", [])) for p in parts for s in p["sections"]),
        "schedules": [x["title"] for x in schedules],
    }
    return act, report


def main():
    manifest = json.loads(MANIFEST.read_text())
    ids = [e["id"] for e in manifest] if "--all" in sys.argv else [a for a in sys.argv[1:] if not a.startswith("--")]
    for e in manifest:
        if e["id"] not in ids:
            continue
        act, rep = extract(e)
        (ROOT / "data" / "acts" / (e["id"] + ".json")).write_text(json.dumps(act, ensure_ascii=False, indent=1) + "\n")
        print(json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
