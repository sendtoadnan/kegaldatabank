#!/usr/bin/env python3
"""Add Appendix III of the Foreign Exchange Manual (the State Bank's notifications under the FERA 1947) as inline schedules.

usage: python3 tools/fe_appendix3.py <saved SBP page: sbp_fem__Appendix-III-notifications.html>
The State Bank publishes Appendix III as a web page, not a PDF (sbp.org.pk/laws-regulations/notifications-issued-by-the-state-bank-
of-pakistan-under-foreign-exchange-regulation-act-1947-vii-of-1947), saved from the browser on 27 Nov 2026. Each of its 36
notifications becomes one schedule (text only, tables as "|" rows), placed after Appendix II. Words are the page's own.
"""
import json, re, sys
from html.parser import HTMLParser
from pathlib import Path

class P(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True); s.items = []; s.cur = None; s.buf = ""; s.tag = None
        s.row = None; s.cell = None; s.rowhead = False; s.intable = False; s.nav = True
    def flush(s):
        t = re.sub(r"\s+", " ", s.buf).strip(); s.buf = ""
        return t
    def handle_starttag(s, tag, a):
        if tag == "h3": s.tag = "h3"; s.nav = False; s.buf = ""
        elif tag in ("h6", "h5") and not s.nav: s.tag = "h6"; s.buf = ""
        elif tag == "p" and not s.nav and not s.intable: s.tag = "p"; s.buf = ""
        elif tag == "li" and not s.nav: s.tag = "li"; s.buf = ""
        elif tag == "table": s.intable = True; s.rows = []
        elif tag == "tr": s.row = []; s.rowhead = False
        elif tag in ("td", "th"): s.cell = ""; s.rowhead = s.rowhead or tag == "th"
        elif tag == "br":
            if s.cell is not None: s.cell += " "
            else: s.buf += "\n" if s.tag == "h3" else " "
    def handle_data(s, d):
        if s.cell is not None: s.cell += d
        elif s.tag: s.buf += d
    def handle_endtag(s, tag):
        if tag == "h3":
            lines = [re.sub(r"\s+", " ", x).strip() for x in s.buf.split("\n") if x.strip()]; s.tag = None
            if s.cur is not None and not re.match(r"(?i)appendix", lines[0]):      # a second notification printed under the same number
                s.cur["text"].append(" ".join(lines))
            else:
                s.cur = {"head": lines, "subject": "", "text": []}; s.items.append(s.cur)
        elif tag == "h6" and s.cur is not None: s.cur["subject"] = s.flush(); s.tag = None
        elif tag in ("p", "li") and s.tag in ("p", "li") and s.cur is not None:
            t = s.flush(); s.tag = None
            if t: s.cur["text"].append(t)
        elif tag in ("td", "th") and s.row is not None: s.row.append(re.sub(r"\s+", " ", s.cell).strip().replace("|", "/")); s.cell = None
        elif tag == "tr" and s.row is not None:
            if any(s.row): s.rows.append(("|!" if s.rowhead else "|") + "|".join(s.row))
            s.row = None
        elif tag == "table":
            s.intable = False
            if s.cur is not None: s.cur["text"].extend(s.rows)

p = P(); p.feed(Path(sys.argv[1]).read_text()); items = p.items
sch = []
for it in items:
    head = it["head"]                                   # APPENDIX III - n / NOTIFICATION NO. ... / DATED ...
    n = re.search(r"[-–—]\s*(\d+)", head[0]).group(1)
    ref = " ".join(head[1:]).replace(" ,", ",").strip(" .")
    title = f"Appendix III-{n} — {ref}" + (f" — {it['subject'].rstrip('.')}" if it["subject"] else "")
    if not it["text"]: print("EMPTY", n)
    sch.append({"title": title, "text": it["text"]})
f = Path(__file__).resolve().parent.parent / "data/acts/foreign-exchange-manual.json"
raw = f.read_text(); d = json.loads(raw)
d["schedules"] = [s for s in d["schedules"] if not s["title"].startswith("Appendix III")]
i = max(k for k, s in enumerate(d["schedules"]) if s["title"].startswith("Appendix II ")) + 1
d["schedules"][i:i] = sch
f.write_text(json.dumps(d, ensure_ascii=False, indent=1 if raw.startswith('{\n "') else 2) + ("\n" if raw.endswith("\n") else ""))
print(len(sch), "notifications;", sum(len(s["text"]) for s in sch), "paragraphs;", sum(1 for s in sch for t in s["text"] if t.startswith("|")), "table rows")
for s in sch[:3] + sch[-2:]: print(s["title"], "|", s["text"][:1][0][:80] if s["text"] else "")
