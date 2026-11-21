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
FNRE = re.compile(r"\{fn:[^}]+\}")
def _tk(t): return re.findall(r"[a-z0-9]+", re.sub(r"[\[\]“”\"'’‘>]", "", FNRE.sub("", t).lower()))
def _grams(w, n=5): return [" ".join(w[k:k + n]) for k in range(max(0, len(w) - n + 1))]
# leads from tools/ocr/structure_check.py (docs/STRUCTURE_CHECK.md): {(instrument, provision): [lead, ...]}
LEADS = {}
_sc = ROOT / "docs/STRUCTURE_CHECK.md"
if _sc.exists():
    for ln in _sc.read_text().splitlines():
        c = [x.strip() for x in ln.strip("|").split(" | ")]
        if len(c) >= 3 and c[0] and not c[0].startswith(("Instrument", "---", "#")) and "`" not in c[0]:
            LEADS.setdefault((c[0], c[1]), []).append(c[2])
index = []
for i in a.ids:
    act = json.load(open(ROOT / "data/acts" / f"{i}.json")); pages = json.load(open(ROOT / "data/salam/pages" / f"{i}.json"))["scans"]
    _raw = " ".join((Path(a.scans) / "_ocr text" / p["file"] / f"p{p['scan']:04d}.txt").read_text() for p in pages if (Path(a.scans) / "_ocr text" / p["file"] / f"p{p['scan']:04d}.txt").exists())
    _have = set(_grams(_tk(_raw)))
    out = ROOT / "verification" / i; out.mkdir(parents=True, exist_ok=True)
    imgs = []
    for n, p in enumerate(pages):
        vol, _, stem = p["file"].partition(" - ")
        fitz.open(Path(a.scans) / vol / (stem + ".pdf"))[p["scan"] - 1].get_pixmap(dpi=110).save(out / f"p{n:03d}.png")
        imgs.append(f'<figure><figcaption>Book page {html.escape(p["bookPage"] or "(unnumbered)")}</figcaption><img src="p{n:03d}.png" loading="lazy"></figure>')
    rows = [f'<p class="pre">{html.escape(act.get("preamble",""))}</p>']; nflag = 0
    for part in act["parts"]:
        rows.append(f'<h3>{html.escape(part["heading"])}</h3>')
        for s in part["sections"]:
            body = "".join(f'<p class="{"ind" if t.startswith(">") else ""}">{html.escape(t.lstrip(">"))}</p>' for t in s["text"])
            g = _grams(_tk(s["title"] + " " + " ".join(s["text"]))); agree = (sum(1 for x in g if x in _have) / len(g)) if len(g) >= 8 else None
            flags = []
            if agree is not None and agree < 0.85: flags.append(f"second reading agrees only {agree*100:.0f}%: look here first")
            for ld in LEADS.get((i, s["no"]), [])[:3]: flags.append(ld)
            flag = "".join(f'<span class="flag">{html.escape(x)}</span>' for x in flags)
            nflag += len(flags)
            rows.append(f'<section><label><input type="checkbox" data-no="{s["no"]}"> <b>{s["no"]}. {html.escape(s["title"])}</b></label>{flag}{body}<textarea data-no="{s["no"]}" placeholder="Errors in {s["no"]} (what the scan says)"></textarea></section>')
    (out / "index.html").write_text(f'''<!doctype html><meta charset="utf-8"><title>Check: {html.escape(act["title"])}</title>
<style>body{{margin:0;font:15px/1.5 Georgia,serif;display:grid;grid-template-columns:1fr 1fr;height:100vh}}
.col{{overflow:auto;padding:12px}}img{{width:100%;border:1px solid #ccc}}figcaption{{font:12px sans-serif;color:#555}}
.flag{{display:inline-block;margin:0 0 0 8px;padding:0 6px;border-radius:6px;background:#fde7b0;font:11px sans-serif}}.ind{{margin-left:2em}}section{{border-bottom:1px solid #ddd;padding:6px 0}}textarea{{width:100%;height:2.4em}}
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
    index.append((nflag, i, act["title"], sum(len(p["sections"]) for p in act["parts"])))
    print(out / "index.html")
# keep one record per instrument across runs (the index lists every check page, not only the ones made in this run)
_ij = ROOT / "verification" / "index.json"
_old = json.load(open(_ij)) if _ij.exists() else {}
for _w, _i, _t, _n in index: _old[_i] = [_w, _t, _n]
json.dump(_old, open(_ij, "w"), ensure_ascii=False, indent=0)
index = sorted(([v[0], k, v[1], v[2]] for k, v in _old.items() if (ROOT / "verification" / k / "index.html").exists()), reverse=True)
(ROOT / "verification" / "index.html").write_text("<!doctype html><meta charset=utf-8><title>Check pages</title><style>body{font:15px/1.6 Georgia,serif;max-width:900px;margin:20px auto}td,th{padding:3px 10px;text-align:left}</style><h1>Instruments to check, most warnings first</h1><p>Tick each provision on its page; your ticks are saved in the browser. The warnings come from a second reading of the scan and a structure check, so they say where to look first, not what is wrong.</p><table><tr><th>Instrument</th><th>Provisions</th><th>Warnings</th></tr>" + "".join(f'<tr><td><a href="{i}/index.html">{html.escape(t)}</a></td><td>{n}</td><td>{w}</td></tr>' for w, i, t, n in index) + "</table>")
print("index:", ROOT / "verification" / "index.html")
