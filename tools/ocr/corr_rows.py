"""Corresponding-provisions table, read cell by cell: find the printed row rules in the gutter between the two columns,
cut each row's left (2017) and right (1984) cell, OCR the cells with Apple Vision, write rows to a JSON file.

usage: python3 tools/ocr/corr_rows.py --vocr <vision_ocr> --pdf <FILE [1].pdf> --out <rows.json> <scan page:printed page> ...
A cell that is only a dash prints no text: "no counterpart". Cells are numbered with the provision number first (e.g. 234A).
Internal working record; the site shows only the section correspondences.
"""
import argparse, json, os, re, statistics, subprocess, tempfile
import fitz
ap = argparse.ArgumentParser(); ap.add_argument("--vocr", required=True); ap.add_argument("--pdf", required=True); ap.add_argument("--out", required=True); ap.add_argument("--boxes", required=True, help="folder with pNNNN.boxes.tsv from ocr_boxes.py (for the column headings)")
ap.add_argument("pages", nargs="+"); a = ap.parse_args()
d = fitz.open(a.pdf)
def geom(p):
    """Column edges from the text lines themselves (headings can be overprinted): left edge, gutter, right edge, first body line."""
    f = [x for x in __import__("glob").glob(os.path.join(a.boxes, "**", f"p{p:04d}.boxes.tsv"), recursive=True)][0]
    rows = []
    for ln in open(f).read().splitlines():
        box, _, t = ln.partition("\t")
        try: x0, y0, x1, y1 = map(float, box.split())
        except ValueError: continue
        rows.append((x0, y0, x1, y1, t))
    hdr = [r for r in rows if "Provision" in r[4] and "Title" in r[4]]
    ytop = (min(r[3] for r in hdr) if hdr else 0.09)
    num = [r for r in rows if r[1] > ytop and re.match(r"^\d{1,3}[A-Z]{0,2} [A-Za-z]", r[4])]     # numbered lines: their starts give clean column edges
    xs0 = sorted(r[0] for r in num)
    gap = max(range(len(xs0) - 1), key=lambda k: xs0[k + 1] - xs0[k])
    cut = (xs0[gap] + xs0[gap + 1]) / 2
    left = [r for r in num if r[0] < cut]; right = [r for r in num if r[0] >= cut]
    xl = min(r[0] for r in left) - 0.012; xs = min(r[0] for r in right) - 0.014; xr = max(r[2] for r in right) + 0.015
    return xl, xs, xr, ytop
def rules_for(pg, gl, gs):
    pix = pg.get_pixmap(dpi=150, colorspace=fitz.csGRAY); W, H = pix.width, pix.height; s = pix.samples
    # the gutter between the columns holds only the row rules; find it from the page's column headers
    gx0, gx1 = int(W * (gs - 0.014)), int(W * (gs + 0.014))
    gp = [sum(s[y * W + gx0:y * W + gx1]) / (gx1 - gx0) for y in range(H)]
    bg = statistics.median(gp); dark = [y for y, v in enumerate(gp) if v < bg - 12]
    cl = []
    for y in dark:
        if cl and y - cl[-1][-1] <= 3: cl[-1].append(y)
        else: cl.append([y])
    ys = [sum(c) / len(c) / H for c in cl]
    out = []
    for y in ys:
        if not out or y - out[-1] > 0.012: out.append(y)
    return out
res = []
with tempfile.TemporaryDirectory() as tmp:
    jobs = []
    for spec in a.pages:
        p, printed = spec.split(":"); pg = d[int(p) - 1]; r = pg.rect
        xl, xs, xr, ytop = geom(int(p))
        ys = [y for y in rules_for(pg, xl, xs) if y > ytop + 0.002]
        # last row ends where the text ends
        ys = [y for y in ys if y < 0.95]
        if ys and ys[0] - (ytop + 0.004) > 0.012: ys.insert(0, ytop + 0.004)      # the first row sits between the heading and the first printed rule
        for k in range(len(ys) - 1):
            top, bot = ys[k], ys[k + 1]
            if bot - top < 0.012: continue
            for side, (xa, xb) in (("L", (xl, xs - 0.014)), ("R", (xs - 0.014, xr))):
                clip = fitz.Rect(r.width * xa, r.height * (top + 0.001), r.width * xb, r.height * (bot - 0.001))
                f = os.path.join(tmp, f"p{int(p):04d}_{k:03d}_{side}.png"); pg.get_pixmap(dpi=250, clip=clip, colorspace=fitz.csGRAY).save(f)
                jobs.append((int(p), printed, k, side, f, round(top, 4)))
    texts = {}
    files = [j[4] for j in jobs]
    def ordered(body):
        """Words in reading order: justified lines come out of the OCR as fragments, so sort by line (y) then x."""
        frags = []
        for ln in body.splitlines():
            try: box, t = ln.split("\t", 1)
            except ValueError: continue
            x0, y0, x1, y1 = map(float, box.split()); frags.append([x0, (y0 + y1) / 2, y1 - y0, t.strip()])
        frags.sort(key=lambda f: f[1]); lines = []
        for f in frags:
            if lines and abs(f[1] - lines[-1][0]) < 0.5 * max(f[2], 0.02): lines[-1][1].append(f)
            else: lines.append([f[1], [f]])
        return re.sub(r"\s+", " ", " ".join(" ".join(g[3] for g in sorted(l[1], key=lambda g: g[0])) for l in lines)).strip()
    for i in range(0, len(files), 40):
        out = subprocess.run([a.vocr, "--boxes", *files[i:i + 40]], capture_output=True, text=True).stdout
        for chunk in out.split("=== ")[1:]:
            head, _, body = chunk.partition("\n"); texts[head.strip()] = ordered(body)
    rows = {}
    for p, printed, k, side, f, top in jobs:
        rows.setdefault((p, printed, k), {"scanPage": p, "printed": printed, "row": k, "y": top})[side] = texts.get(f, "")
    res = [rows[k] for k in sorted(rows)]
json.dump(res, open(a.out, "w"), ensure_ascii=False, indent=1)
print(len(res), "rows ->", a.out)
