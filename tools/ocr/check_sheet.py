"""Side-by-side check page for text converted from the scans: scan pages on the left, our text on the right.

usage: python3 tools/ocr/check_sheet.py --scans <scans folder> <id> ...   (after book_to_json.py --pages-only)
Writes verification/<id>/index.html with page images (not committed). Tick each provision that matches,
note errors, then "Copy notes" and paste them to Claude.
"""
import argparse, html, json, re
from pathlib import Path
import fitz
ROOT = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser(); ap.add_argument("--scans", required=True); ap.add_argument("ids", nargs="+"); a = ap.parse_args()
for i in a.ids:
    act = json.load(open(ROOT / "data/acts" / f"{i}.json")); pages = json.load(open(ROOT / "data/salam/pages" / f"{i}.json"))["scans"]
    out = ROOT / "verification" / i; out.mkdir(parents=True, exist_ok=True)
    imgs = []
    for n, p in enumerate(pages):
        vol, _, stem = p["file"].partition(" - ")
        fitz.open(Path(a.scans) / vol / (stem + ".pdf"))[p["scan"] - 1].get_pixmap(dpi=110).save(out / f"p{n:03d}.png")
        imgs.append(f'<figure><figcaption>Book page {html.escape(p["bookPage"] or "(unnumbered)")}</figcaption><img src="p{n:03d}.png" loading="lazy"></figure>')
    rows = [f'<p class="pre">{html.escape(act.get("preamble",""))}</p>']
    for part in act["parts"]:
        rows.append(f'<h3>{html.escape(part["heading"])}</h3>')
        for s in part["sections"]:
            body = "".join(f'<p class="{"ind" if t.startswith(">") else ""}">{html.escape(t.lstrip(">"))}</p>' for t in s["text"])
            rows.append(f'<section><label><input type="checkbox" data-no="{s["no"]}"> <b>{s["no"]}. {html.escape(s["title"])}</b></label>{body}<textarea data-no="{s["no"]}" placeholder="Errors in {s["no"]} (what the scan says)"></textarea></section>')
    (out / "index.html").write_text(f'''<!doctype html><meta charset="utf-8"><title>Check: {html.escape(act["title"])}</title>
<style>body{{margin:0;font:15px/1.5 Georgia,serif;display:grid;grid-template-columns:1fr 1fr;height:100vh}}
.col{{overflow:auto;padding:12px}}img{{width:100%;border:1px solid #ccc}}figcaption{{font:12px sans-serif;color:#555}}
.ind{{margin-left:2em}}section{{border-bottom:1px solid #ddd;padding:6px 0}}textarea{{width:100%;height:2.4em}}
header{{grid-column:1/3;padding:6px 12px;background:#f3f0e6;font-family:sans-serif}}body{{grid-template-rows:auto 1fr}}</style>
<header><b>{html.escape(act["title"])}</b> — tick each provision whose text matches the scan; write any differences in its box. <button onclick="copyNotes()">Copy notes</button> <span id="st"></span></header>
<div class="col">{"".join(imgs)}</div><div class="col">{"".join(rows)}</div>
<script>
const K="chk-{i}";const s=JSON.parse(localStorage.getItem(K)||"{{}}");
document.querySelectorAll("[data-no]").forEach(e=>{{const k=e.type+e.dataset.no;if(s[k]!==undefined){{e.type==="checkbox"?e.checked=s[k]:e.value=s[k]}}
e.addEventListener("input",()=>{{s[k]=e.type==="checkbox"?e.checked:e.value;localStorage.setItem(K,JSON.stringify(s))}})}});
function copyNotes(){{let t="Check of {i}\\n";document.querySelectorAll("section").forEach(x=>{{const c=x.querySelector("input"),n=x.querySelector("textarea");
t+=c.dataset.no+": "+(c.checked?"OK":"not ticked")+(n.value?" — "+n.value:"")+"\\n"}});navigator.clipboard.writeText(t);document.getElementById("st").textContent="Copied"}}
</script>''')
    print(out / "index.html")
