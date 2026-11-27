"""Parse the State Bank's Foreign Exchange Manual chapters (PDF text layer) into parts of numbered paragraphs.

usage: python3 tools/fe_manual.py <folder with Chapter-N.pdf> <out.json> [--report]
Each chapter is a part; each numbered paragraph (a bold "12.  Title." line and what follows) is a provision numbered
"<chapter>.<n>" (12A, 12B ... as printed). Paragraphs are found from the chapter's own bold headings, not from its printed
contents list (which is out of date in some chapters), and the two are compared in the report.

Layout read from the PDF: left margin and size tell sub-paragraphs "(i)", "(a)" and "(i)" under "(a)" apart (written to the
text as ">" levels), footnotes (small type at the foot of the page) become the paragraph's amendment notes, superscript
numbers in the text become {fn:page-n} markers, and page numbers and running headers are dropped.
"""
import fitz, re, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_tables import find_tables, row_strings, clean_cell

SMALL = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with", "etc"}


def title_case(s):
    out = []
    for i, w in enumerate(s.split()):
        lw = w.lower()
        out.append(lw if (i and lw in SMALL) else (w if re.search(r"[a-z]", w) and w != w.upper() else lw[:1].upper() + lw[1:]))
    return " ".join(out)


def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())


def page_lines(doc):
    """Lines of every page, with lines of one row (a number and its title are often separate lines) joined.
    Each line: page, x, y, size (of ordinary text), bold, text (superscripts as \x01n\x02), ph (page height)."""
    raw = []; tabs = {}
    for pno, pg in enumerate(doc):
        for b in pg.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                spans = [s for s in l["spans"] if s["text"].strip()]
                if spans: raw.append((pno, pg.rect.height, l["bbox"][0], l["bbox"][1], spans))
        tabs[pno] = find_tables(pg)
    sizes = {}
    for _, _, _, _, sp in raw:
        for s in sp: sizes[round(s["size"], 1)] = sizes.get(round(s["size"], 1), 0) + len(s["text"])
    body = max(sizes, key=sizes.get)
    rows = []
    for pno, ph, x, y, sp in sorted(raw, key=lambda r: (r[0], round(r[3] / 3), r[2])):
        if rows and rows[-1]["page"] == pno and abs(rows[-1]["y"] - y) <= 3.5 and x > rows[-1]["x"]:
            rows[-1]["spans"] += sp
        else:
            rows.append({"page": pno, "ph": ph, "x": x, "y": y, "spans": list(sp)})
    out = []
    for r in rows:
        text = ""; pv = None
        for s in r["spans"]:
            t = s["text"]
            if pv is not None and s["bbox"][0] - pv["bbox"][2] > 1.5 and not pv["text"].endswith(" ") and not t.startswith(" "): text += " "
            pv = s
            if s["size"] <= body * 0.72 and re.fullmatch(r"\s*\d{1,2}\s*|\s*(st|nd|rd|th)\s*", t):
                t = f"\x01{t.strip()}\x02"
            text += t
        text = re.sub(r"\s+", " ", text).strip()
        norm_spans = [s for s in r["spans"] if s["size"] > body * 0.72]
        size = max((s["size"] for s in norm_spans), default=body * 0.6)
        sm = size < body * 0.93
        out.append({"page": r["page"], "ph": r["ph"], "x": r["x"], "y": r["y"], "size": size, "small": sm, "body": body,
                    "bold": bool(norm_spans) and all(s["flags"] & 16 for s in norm_spans if len(s["text"].strip()) > 1) and any(len(s["text"].strip()) > 1 for s in norm_spans),
                    "text": text})
    res = []; done = set()
    for l in out:
        hit = next((t for t in tabs.get(l["page"], []) if t["x0"] - 3 <= l["x"] <= t["x1"] + 3 and t["y0"] - 2 <= l["y"] + 4 <= t["y1"] + 2), None)
        if hit is None: res.append(l); continue
        if id(hit) not in done:
            done.add(id(hit))
            res.append({"page": l["page"], "ph": l["ph"], "x": hit["x0"], "y": hit["y0"], "size": body, "small": False, "body": body, "bold": False, "text": "\x00TABLE", "table": hit["rows"]})
    return res


def split_page_furniture(lines):
    body = []; foots = {}
    for l in lines:
        t = re.sub(r"^\x01(\d{1,2})\x02\s*", r"\1 ", l["text"]) if l["small"] else l["text"]
        if re.fullmatch(r"\d{1,3}", t) and l["y"] > l["ph"] * 0.88: continue          # page number
        if l["small"] and l["y"] > l["ph"] * 0.55 and (re.match(r"^\d{1,2}\b", t) or (l["page"] in foots)):
            m = re.match(r"^(\d{1,2})\b\s*(.*)$", t)
            if m and (l["page"] not in foots or int(m.group(1)) == int(foots[l["page"]][-1][0]) + 1 or not re.match(r"^[a-z]", m.group(2))):
                foots.setdefault(l["page"], []).append([m.group(1), m.group(2)])
            else:
                foots[l["page"]][-1][1] += " " + t
            continue
        body.append(l)
    return body, foots


def heading_of(l, margin):
    if l["x"] > margin + 14: return None
    m = re.match(r"^(\d{1,2}[A-Z]{0,2})\.\s*(.*)$", l["text"]) or (re.match(r"^(\d{1,2}[A-Z]{0,2})\s+(\D.*)$", l["text"]) if l["bold"] else None)
    if not m: return None
    if l["bold"] or re.fullmatch(r"\(?Omitted\)?\.?", m.group(2).strip()): return m.group(1), m.group(2)
    return None


def base(n): return int(re.match(r"\d+", n).group())


def label_of(t):
    """Leading list label: "(i)", "i)", "a)", "(a)", "aa)", "i." or "1."; returns (label, length of the label and its space)."""
    m = re.match(r"^\(([a-z]{1,4}|\d{1,2})\)\s*", t) or re.match(r"^([a-z]{1,4}|\d{1,2})\)\s+", t) \
        or re.match(r"^((?:i{1,3}|iv|v|vi{1,3}|ix|x))\.\s+", t) or re.match(r"^(\d{1,2})\.\s+(?=[A-Z(])", t)
    return (m.group(1), m.end()) if m else (None, 0)


ROMAN = ["", "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx"]


def kind_of(v, vals):
    if v.isdigit(): return "num"
    if len(v) > 1 and len(set(v)) == 1 and v[0] not in "ivx": return "dletter"
    if re.fullmatch(r"[ivx]+", v):
        last = vals.get("letter")
        if len(v) == 1 and last and len(last) == 1 and ord(last) + 1 == ord(v): return "letter"      # (h) then (i)
        return "roman"
    return "letter"


def chapter(doc, ch):
    lines = page_lines(doc)
    body, foots = split_page_furniture(lines)
    bsize = lines[0]["body"] if lines else 11
    xs = sorted(l["x"] for l in body if l["size"] >= bsize * 0.95 and len(l["text"]) > 40)
    margin = xs[len(xs) // 8] if xs else 62
    # running header on every page: "CHAPTER n" and the chapter title in capitals
    head = [l for l in body if l["y"] < 135 and (re.fullmatch(r"(?i)chapter\s*\d+", l["text"]) or (l["bold"] and l["text"].isupper() and not re.match(r"^\d", l["text"])))]
    title = " ".join(l["text"] for l in head if l["page"] == min(h["page"] for h in head) and not re.match(r"(?i)chapter", l["text"])) if head else ""
    hid = {id(l) for l in head}
    body = [l for l in body if id(l) not in hid and not re.fullmatch(r"(?i)contents", l["text"])]
    heads = [(i, heading_of(l, margin)) for i, l in enumerate(body)]
    heads = [(i, h) for i, h in heads if h]
    good = []; prev = 0
    for i, h in heads:                                  # numbers must rise; a bold "1." inside the text is not a heading
        b = base(h[0])
        if (not good and b == 1) or (good and (b > prev or (b == prev and len(h[0]) > len(str(b)) and h[0] != good[-1][1][0]))):
            good.append((i, h)); prev = b
    # "Part-A" group headings (bold, centred) split the chapter into parts
    partmarks = [(i, l["text"]) for i, l in enumerate(body) if l["bold"] and re.match(r"^Part[- ]\w", l["text"]) and l["x"] > margin + 60]
    partmarks = [(i, t) for i, t in partmarks if good and i > good[0][0]]
    secs = []; contents = []
    for k, (i, (no, first)) in enumerate(good):
        end = good[k + 1][0] if k + 1 < len(good) else len(body)
        stop = [pi for pi, _ in partmarks if i < pi < end]
        if stop: end = stop[0]
        ttl_parts = [first] if first else []
        j = i + 1
        while j < end and body[j]["bold"] and not label_of(body[j]["text"])[0] and body[j]["page"] == body[i]["page"] and body[j]["y"] - body[j - 1]["y"] < bsize * 1.9 and not re.match(r"^\d{1,2}[A-Z]{0,2}\.", body[j]["text"]):
            ttl_parts.append(body[j]["text"]); j += 1
        ttl = re.sub(r"\s+", " ", " ".join(ttl_parts)).strip()
        paras = []; stack = []; vals = {}; fnotes = []
        cur = None; prevl = None
        for l in body[j:end]:
            if l.get("table"):
                paras.append({"rows": l["table"]}); cur = None; prevl = l
                continue
            t = l["text"]
            def fnrep(m):
                n = m.group(1)
                if not n.isdigit(): return n + ""
                text = next((x[1] for x in foots.get(l["page"], []) if x[0] == n), None)
                if text is None: return n
                key = f"{l['page'] + 1}-{n}"
                if not any(f["n"] == key for f in fnotes): fnotes.append({"n": key, "text": text.strip()})
                return "{fn:%s}" % key
            t = re.sub(r"\x01([^\x02]*)\x02", fnrep, t)
            lab, end_lab = label_of(t)
            gap = (l["y"] - prevl["y"] > bsize * 1.6 and l["page"] == prevl["page"]) if prevl else True
            newpage = prevl is not None and l["page"] != prevl["page"]
            prevl = l
            ended = cur is not None and re.search(r"[.:;)\]]\s*(\{fn:[^}]*\}\s*)*$", cur["t"])
            if lab and (cur is None or gap or newpage or ended):
                kind = kind_of(lab, vals)
                if kind == "roman":
                    if lab == "i" and "roman" in stack and stack[-1] != "roman": kind = "roman" + str(len(stack))
                    elif lab in ROMAN[1:]:                       # "(ii)" continues the roman list whose last label was "(i)"
                        prevlab = ROMAN[ROMAN.index(lab) - 1]
                        cand = [k for k in stack if k.startswith("roman") and vals.get(k) == prevlab]
                        if cand: kind = cand[-1]
                if kind in stack:
                    d = stack.index(kind); stack = stack[:d + 1]
                else:
                    stack.append(kind); d = len(stack) - 1
                vals[kind] = lab
                for kk in [k2 for k2 in vals if k2 not in stack]: vals.pop(kk)
                cur = {"lvl": min(d, 3), "t": f"({lab}) " + t[end_lab:].strip()}
                paras.append(cur)
            elif cur is None:
                cur = {"lvl": 0, "t": t}; paras.append(cur)
            elif (gap or newpage) and ended and t[:1].isupper() and not (newpage and not gap and l["y"] > l["ph"] * 0.2):
                cur = {"lvl": 0 if l["x"] <= margin + 20 else cur["lvl"], "t": t}; paras.append(cur)
            else:
                cur["t"] += " " + t
        text = []
        for p in paras:
            if "rows" in p:
                text += row_strings(p["rows"]); continue
            q = re.sub(r"\s+", " ", p["t"]).strip()
            q = re.sub(r"\s+([,.;:])", r"\1", q)
            if q: text.append(">" * p["lvl"] + q)
        ttl = re.sub(r"\x01([^\x02]*)\x02", r"", ttl).rstrip(". ").strip()
        sec = {"no": f"{ch}.{no}", "title": ttl, "text": text or [ttl or "Omitted"]}
        if fnotes: sec["fn"] = fnotes
        sec["_pos"] = i
        secs.append(sec)
    return title, partmarks, secs, body


def main():
    R = Path(sys.argv[1]); OUT = sys.argv[2]
    parts = []
    for ch in range(1, 23):
        doc = fitz.open(R / f"Chapter-{ch}.pdf")
        t, pm, s, body = chapter(doc, ch)
        got = [x["no"].split(".", 1)[1] for x in s]
        gaps = []
        for a_, b_ in zip(got, got[1:]):
            if base(b_) > base(a_) + 1: gaps.append(f"{a_}->{b_}")
        print(ch, t[:40], "| paragraphs", len(s), "| last", got[-1] if got else None, "| gaps", gaps, "| parts", [x[1][:20] for x in pm])
        base_head = f"Chapter {ch} — {title_case(t)}" if t else f"Chapter {ch}"
        if not pm:
            for x in s: x.pop("_pos")
            parts.append({"heading": base_head, "sections": s}); continue
        groups = {}
        order = []
        for x in s:
            pk = max([m for m in pm if m[0] < x["_pos"]], key=lambda m: m[0], default=None)
            key = pk[0] if pk else -1
            if key not in groups: groups[key] = []; order.append((key, pk))
            groups[key].append(x)
        for key, pk in order:
            sub = ""
            if pk:
                j = pk[0] + 1; sp = []
                while j < len(body) and body[j]["bold"] and not re.match(r"^\d{1,2}[A-Z]{0,2}\.", body[j]["text"]) and len(sp) < 3: sp.append(body[j]["text"]); j += 1
                sub = re.sub(r"\s+", " ", " ".join(sp)).strip()
            for x in groups[key]: x.pop("_pos")
            parts.append({"heading": base_head + ((" — " + re.sub(r"^Part[- ]", "Part ", pk[1]) + (": " + sub if sub else "")) if pk else ""), "sections": groups[key]})
    json.dump(parts, open(OUT, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__": main()
