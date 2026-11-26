#!/usr/bin/env python3
"""Check each SECP notice's title and number against its own PDF's first page and correct what the file name got wrong.

usage: python3 scripts/refine_notices.py [--apply] [--ocr <compiled scripts/ocr_pdf.swift>]
SECP's file names are often mashed together or carry another instrument's number. The PDF's own heading is the better
source: a notification's own number is the "S.R.O. N(I)/YYYY.-" right after its date line; a direction or circular says
"DIRECTION NO. N OF YYYY". When the file name disagrees (beyond a one-digit text-recognition slip) the PDF's number is used
in the title and number; glued words ("2017requirements") are separated; a bare title ("Direction 1 of 2025") gets the PDF's
"Subject:". Search text that is unreadable (font-encoding junk) is re-read by OCR. Prints every change; writes with --apply.
"""
import json, re, sys, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = ["notifications", "circulars", "directives", "guidelines"]
OCR = sys.argv[sys.argv.index("--ocr") + 1] if "--ocr" in sys.argv else None
APPLY = "--apply" in sys.argv

OWN_SRO = re.compile(r"S\.?\s*R\.?\s*O\.?\s*(?:No\.?\s*)?(\d{1,4})\s*\(?\s*[I1l]\s*\)?\s*/\s*(\d{4})\s*\.?\s*[-–—]")
OWN_DIR = re.compile(r"\b(DIRECTION|DIRECTIVE|CIRCULAR)\s+NO\.?\s*(\d{1,3})\s*(?:OF|/)\s*(\d{4})")
TITLE_SRO = re.compile(r"S\.R\.O\.\s*(?:No\.?\s*)?(\d{1,4})\s*(?:\(I\)\s*/\s*|of\s+)(\d{4})")
TITLE_DIR = re.compile(r"\b(Direction|Directive|Directives|Circular)s?\s*(?:No\.?)?\s*(\d{1,3})\s*(?:of|/)\s*(\d{4})", re.I)


def near(a, b):                     # one-digit slip of text recognition
    if len(a) != len(b): return abs(len(a) - len(b)) == 1 and (a in b or b in a)
    return sum(x != y for x, y in zip(a, b)) <= 1


def garbled(t): return bool(t) and sum(1 for c in t if ord(c) < 32 and c not in "\n\t") / len(t) > 0.05


def ocr(pdf):
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "o.txt"
        subprocess.run([OCR, str(pdf), str(out), "1", "2"], capture_output=True, timeout=300)
        return re.sub(r"\s+", " ", re.sub(r"<<<page \d+>>>", " ", out.read_text())).strip()[:3000] if out.exists() else ""


def main():
    changes = []
    for kind in KINDS:
        ip = ROOT / "data/notices" / f"secp-{kind}.json"; tp = ROOT / "data/notices-text" / f"secp-{kind}.json"
        d = json.loads(ip.read_text()); tx = json.loads(tp.read_text())
        for it in d["items"]:
            text = re.sub(r"\s+", " ", tx.get(it["id"], ""))
            old = (it["title"], it.get("number", ""))
            if garbled(text) and OCR:
                new = ocr(ROOT / "sources/pdf" / it["file"])
                if new: tx[it["id"]] = new; text = new; changes.append((kind, it["title"], "search text re-read by OCR"))
            head = text[:700]
            title = re.sub(r"(\d{4})(?=[a-z]{3})", r"\1 ", it["title"])
            number = it.get("number", "")
            check = ""
            m = OWN_SRO.search(head)
            if m:
                pn, py = str(int(m.group(1))), m.group(2)
                t = TITLE_SRO.search(title)
                if not number and not re.search(r"S\.?R\.?O", title): number = f"S.R.O. {pn}(I)/{py}"
                elif t and not (t.group(2) == py and (str(int(t.group(1))) == pn or near(str(int(t.group(1))), pn))):
                    check = f"The PDF's first page reads S.R.O. {pn}(I)/{py}; the file name gave {t.group(1)}/{t.group(2)}."     # shown, not guessed
            else:
                m = OWN_DIR.search(text[:900])
                t = TITLE_DIR.search(title)
                if m and t:
                    pn, py = str(int(m.group(2))), m.group(3)
                    if not (str(int(t.group(2))) == pn and t.group(3) == py) and m.group(1).lower()[:4] == t.group(1).lower()[:4] and not re.search(r"Amend|Licensing and Allied", title):
                        check = f"The PDF's first page reads {m.group(1).title()} No. {pn} of {py}; the file name gave {int(t.group(2))} of {t.group(3)}."
            sub = re.search(r"Subject\s*:?\s*(.{12,200}?)(?=\s(?:Reference|Ref\b|Dear|In exercise|The Securities|Sir|Madam|Please|Date|This |It is|Further)|\.\s|$)", text[:1800])
            if sub and re.fullmatch(r"(Direction|Directive|Directives|Cir|Circular)\b[\w\s.]{0,40}", title) and len(title) < 45:
                s_ = re.sub(r"\s+\d$", "", re.sub(r"\s+", " ", sub.group(1))).strip(" .:-_")
                if s_.isupper(): s_ = s_.title()
                if len(s_) > 10 and "_" not in s_ and len(s_) < 150: title = f"{title}: {s_}"
            if check: it["check"] = check
            else: it.pop("check", None)
            if (title, number) != old:
                changes.append((kind, old[0] + (f" [{old[1]}]" if old[1] else ""), title + (f" [{number}]" if number else "")))
                it["title"] = title; it["number"] = number
        if APPLY:
            ip.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n"); tp.write_text(json.dumps(tx, ensure_ascii=False, separators=(",", ":")))
    for c in changes: print(" | ".join(c))
    print(len(changes), "changes" + (" (written)" if APPLY else " (dry run)"))


main()
