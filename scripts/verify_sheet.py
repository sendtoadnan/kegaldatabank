#!/usr/bin/env python3
"""Make a printable checklist for verifying an instrument against its official PDF.

    python3 scripts/verify_sheet.py companies-postal-ballot-regulations-2018
    python3 scripts/verify_sheet.py --unverified            # one sheet per unverified instrument

Writes verification/<id>.html (not committed). Open it in a browser next to the PDF: each row gives
the provision, the PDF page (click to open the PDF there), its first and last words and how many
amendment notes it carries. Tick each row once the text matches, then record the result with
scripts/mark_verified.py.
"""
import argparse
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FN = re.compile(r"\{fn:[^}]+\}")


def clean(p):
    return re.sub(r"\s+", " ", FN.sub("", re.sub(r"^>+", "", p))).strip()


def words(text, n, last=False):
    w = text.split()
    if len(w) <= n:
        return text
    return ("… " + " ".join(w[-n:])) if last else (" ".join(w[:n]) + " …")


def sheet(act):
    pdf = ROOT / "sources" / "pdf" / act["sourcePdf"] if act.get("sourcePdf") else None
    pdf_url = act.get("sourcePdfUrl") or (pdf.as_uri() if pdf and pdf.exists() else "")
    rows = []
    n = 0
    for part in act["parts"]:
        rows.append(f'<tr class="part"><td colspan="6">{html.escape(clean(part.get("heading") or ""))}</td></tr>')
        for s in part["sections"]:
            n += 1
            text = clean(" ".join(s["text"]))
            page = s.get("page")
            link = f'<a href="{html.escape(pdf_url)}#page={page}" target="pdf">p.{page}</a>' if pdf_url and page else (f"p.{page}" if page else "")
            rows.append(
                "<tr>"
                f'<td><input type="checkbox"></td><td class="no">{html.escape(str(s["no"]))}</td>'
                f'<td>{html.escape(clean(s.get("title") or ""))}<div class="w">{html.escape(words(text, 12))}</div>'
                f'<div class="w">{html.escape(words(text, 12, last=True))}</div></td>'
                f"<td>{link}</td><td>{len(s.get('fn') or [])}</td><td class=\"note\"></td></tr>"
            )
    title = html.escape(act["title"])
    return f"""<!doctype html><meta charset="utf-8"><title>Verify: {title}</title>
<style>
body{{font:14px/1.4 -apple-system,Helvetica,Arial,sans-serif;margin:24px;color:#111}}
h1{{font-size:20px;margin:0 0 4px}} p{{margin:4px 0}}
table{{border-collapse:collapse;width:100%;margin-top:12px}} td,th{{border:1px solid #ccc;padding:6px;vertical-align:top}}
th{{background:#f3f3f3;text-align:left}} .part td{{background:#eef3fa;font-weight:600}}
.no{{white-space:nowrap;font-weight:600}} .w{{color:#555;font-size:12px}} .note{{width:18%}}
@media print{{a{{color:#111;text-decoration:none}}}}
</style>
<h1>Verification checklist: {title}</h1>
<p>Source PDF: {html.escape(act.get("sourcePdf") or act.get("sourcePdfUrl") or "—")} · Edition: {html.escape(act.get("amendedUpToLabel") or act.get("enacted") or "not stated")} · {n} provisions · Sheet made {date.today().isoformat()}</p>
<p>For each row, open the PDF at the page shown and check the heading, the first and last words, every sub-clause in between,
and the amendment notes. Tick the row when it matches; write what differs in the last column.</p>
<p>When every row is ticked: <code>python3 scripts/mark_verified.py {html.escape(act["id"])} --by "Your name" --against "SECP PDF of …"</code></p>
<table><tr><th>✓</th><th>No.</th><th>Heading, first and last words</th><th>PDF</th><th>Notes</th><th>Differences</th></tr>
{''.join(rows)}</table>
<p style="margin-top:16px">Checked by: ____________________ &nbsp; Date: ____________</p>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--unverified", action="store_true", help="every instrument with text that is not yet verified")
    a = ap.parse_args()
    acts = {p.stem: json.loads(p.read_text()) for p in sorted((ROOT / "data" / "acts").glob("*.json"))}
    ids = a.ids or [i for i, x in acts.items() if a.unverified and x["verification"]["status"] != "verified" and x["parts"]]
    if not ids:
        ap.error("name an instrument id or use --unverified")
    out = ROOT / "verification"
    out.mkdir(exist_ok=True)
    for i in ids:
        if i not in acts:
            raise SystemExit(f"Unknown instrument: {i}")
        (out / f"{i}.html").write_text(sheet(acts[i]))
        print(f"verification/{i}.html")


if __name__ == "__main__":
    main()
