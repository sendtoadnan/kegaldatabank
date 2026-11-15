"""Find the notifications and circulars printed within the Companies Act part (book pages AI-…).

usage: python3 tools/ocr/act_inserts.py <_ocr text folder> <out.json> [<with-text.json>]
Each item: subject heading, reference (S.R.O. / SECP circular / other), date, book page, and the
sections of the Act its text cites (section 510, the general power to make directions, is listed
separately as it applies to almost all of them).
"""
import json, re, sys
from pathlib import Path
B = Path(sys.argv[1])
pm = json.load(open(B / "page-map.json"))
MON = "january february march april may june july august september october november december".split()
pages = []  # (book page, text) in book order for Part AI
for pg, locs in pm.items():
    if not pg.startswith("AI-"): continue
    loc = locs[-1]
    t = (B / loc["file"] / f"p{loc['scan']:04d}.txt").read_text()
    m = re.match(r"AI-(\d+)(?:\((\d+)\))?", pg)
    pages.append(((int(m.group(1)), int(m.group(2) or 0)), pg, t))
pages.sort()
ITEM = re.compile(r"([A-Z][^\n]{3,200}?(?:\n[^\n]{0,200}?){0,3}?)\.\s*[-–—]\s*Following is the\s+text of\s+(.{3,160}?)\s+dated\s+([A-Za-z]+)\.?\s*(\d{1,2})\s*,?\s*(\d{4})", re.S)
items = []
for _, pg, t in pages:
    body = "\n".join(l for l in t.splitlines()[3:] if not re.match(r"^E2\s|^B2", l))
    for m in ITEM.finditer(body):
        head = " ".join(m.group(1).split())
        head = re.split(r"(?<=[”\"])\s+|\.\s{1,}(?=[A-Z])", head)[-1]
        ref = " ".join(m.group(2).split())
        mon = m.group(3)[:3].lower()
        mo = next((i + 1 for i, x in enumerate(MON) if x.startswith(mon)), None)
        items.append({"page": pg, "heading": head, "ref": ref, "date": f"{m.group(5)}-{mo:02d}-{int(m.group(4)):02d}" if mo else None, "start": m.end(), "pagetext": body})
# text of each item runs to the next item (same page) or the end of the page plus following insert pages
out = []
for k, it in enumerate(items):
    nxt = items[k + 1] if k + 1 < len(items) else None
    if nxt and nxt["page"] == it["page"]: txt = it["pagetext"][it["start"]:nxt["start"]]
    else:
        txt = it["pagetext"][it["start"]:]
        idx = [p for _, p, _ in pages].index(it["page"])
        for _, p, t in pages[idx + 1: idx + 4]:
            if nxt and p == nxt["page"]: txt += "\n" + t.split("Following is the")[0]; break
            txt += "\n" + t
    secs = re.findall(r"(?:section|sections|Section)\s+(\d{1,3}[A-Z]?)", txt)
    secs += re.findall(r"of section\s+(\d{1,3}[A-Z]?)", txt)
    cited = sorted({s for s in secs if s != "510"}, key=lambda s: int(re.match(r"\d+", s).group()))
    r = it["ref"]
    kind = "notification" if re.search(r"S\.?\s*R\.?\s*O", r, re.I) else "circular" if re.search(r"SECP.{0,20}Circular|Circular", r, re.I) and "ICAP" not in r else "icap" if "ICAP" in r or "Institute" in r else "other"
    srom = re.search(r"(\d{1,4})\s*\(?[1IlLT\[\]D()]*\)?\s*/\s*(\d{4})", r); cm = re.search(r"(\d{1,3})\s*of\s*(\d{4})", r)
    number = f"S.R.O. {int(srom.group(1))}(I)/{srom.group(2)}" if kind == "notification" and srom else f"Circular No. {int(cm.group(1))} of {cm.group(2)}" if cm else r
    out.append({"page": it["page"], "heading": it["heading"], "kind": kind, "number": number, "ref": r, "date": it["date"],
                "sections": cited, "uses510": "510" in secs, "chars": len(txt), "text": txt})
if len(sys.argv) > 3:  # full text (law text, OCR) kept outside the repository
    json.dump(out, open(sys.argv[3], "w"), indent=1)
for o in out: o.pop("text")
json.dump(out, open(sys.argv[2], "w"), indent=1)
from collections import Counter
print(len(out), Counter(o["kind"] for o in out), "no section:", sum(1 for o in out if not o["sections"]))
