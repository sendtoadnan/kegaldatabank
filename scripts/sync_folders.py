#!/usr/bin/env python3
"""Compare law PDFs kept in several folders and gather the newest edition of each into one folder.

Run it on the computer where Google Drive and OneDrive are synced, for example on a Mac:

    python3 scripts/sync_folders.py \
        --from "~/Library/CloudStorage/GoogleDrive-<you>/My Drive/Paklegaldatabank" \
        --from "~/Library/CloudStorage/OneDrive-Personal/Pak Legal Data Bank" \
        --to   "~/Library/CloudStorage/OneDrive-Personal/Pak Legal Data Bank/Unified"

Nothing is written until you add --apply; without it the script only prints what it would do.
Files are only ever copied, never moved or deleted.

For each PDF the script works out which law it is (by the file names recorded in
sources/manifest.json, then the law's title in the file name, then the title on the first pages)
and which edition (the "updated / amended up to" date in the file name or on the first pages).
The newest edition of each law goes to <to>/<practice area>/<law>/, older editions to
<law>/Older editions/, and files it cannot place to <to>/_To sort/. It writes
<to>/unified-index.csv listing every file, where it came from and whether it is newer than the
edition in the website's library.

--mirror <folder> also copies the unified folder into another folder, such as the Google Drive
folder Claude reads, so the same files reach the library. --scaffold companies-act-2017 creates
one folder per section-wise instrument in data/related/companies-act-2017.json, ready for you to
drop the PDFs into.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def _month(name):
    return MONTHS.index(name[:3].lower()) + 1 if name[:3].lower() in MONTHS else 0


def dates_in(text):
    """Dates such as 30.06.2026, 30-06-2026, 18-Aug-2022, 30th June, 2026, March 3, 2025 (as YYYY-MM-DD)."""
    t = re.sub(r"\s+", " ", text)
    out = []
    for d, m, y in re.findall(r"\b(\d{1,2})[.\-/](\d{1,2})[.\-/](20\d\d)\b", t):
        if 1 <= int(m) <= 12 and 1 <= int(d) <= 31:
            out.append(f"{y}-{int(m):02d}-{int(d):02d}")
    for d, mon, y in re.findall(r"\b(\d{1,2})(?:st|nd|rd|th)?[ \-]+([A-Za-z]{3,9})\.?,?[ \-]+(20\d\d)\b", t, re.I):
        if _month(mon):
            out.append(f"{y}-{_month(mon):02d}-{int(d):02d}")
    for mon, d, y in re.findall(r"\b([A-Za-z]{3,9})\.? (\d{1,2})(?:st|nd|rd|th)?,? (20\d\d)\b", t, re.I):
        if _month(mon):
            out.append(f"{y}-{_month(mon):02d}-{int(d):02d}")
    if not out:
        # month and year only ("upto Sep. 2020"): the last day of that month
        for mon, y in re.findall(r"\b([A-Za-z]{3,9})\.?,? (20\d\d)\b", t, re.I):
            if _month(mon):
                m = _month(mon)
                out.append(f"{y}-{m:02d}-{(date(int(y) + m // 12, m % 12 + 1, 1) - date.resolution).day:02d}")
    return out


def edition_in_name(name):
    """The edition date in a file name such as ...-updated-as-of-march-3-2025.pdf or ...upto30.06.2026.pdf."""
    stem = Path(name).stem.replace("_", " ")
    return max(dates_in(stem) + dates_in(re.sub(r"[-.]+", " ", stem)), default=None)


EDITION_WORDS = r"(?:updated|amended|as amended|as on|as of|up ?to|upto|till)"


def edition_in_text(text):
    """The newest date that follows words such as "updated up to" or "amended up to"."""
    found = []
    for m in re.finditer(r"(?=(" + EDITION_WORDS + r".{0,40}))", re.sub(r"\s+", " ", text), re.I):
        found += dates_in(m.group(1))
    return max(found) if found else None


def letters(s):
    return re.sub(r"[^a-z]", "", s.lower())


def load_library():
    manifest = json.loads((ROOT / "sources" / "manifest.json").read_text())
    catalog = json.loads((ROOT / "data" / "catalog.json").read_text())
    areas = {c["id"]: c["name"] for c in catalog.get("categories", [])}
    laws = []
    for e in manifest:
        title = e["title"]
        core = re.sub(r",?\s*\(?\d{4}\)?$", "", title)  # "Income Tax Ordinance, 2001" -> "Income Tax Ordinance"
        laws.append(
            {
                "id": e["id"],
                "title": title,
                "year": (re.search(r"(1[89]|20)\d\d", title) or [None])[0],
                "keys": {letters(core)} | {letters(a) for a in e.get("aliases", []) if len(letters(a)) > 6},
                "file": e.get("file"),
                "edition": e.get("amendedUpTo") or e.get("enacted"),
                "area": areas.get((e.get("categories") or [None])[0], "Other"),
            }
        )
    # Rules, regulations and notifications recorded in data/related/<act>.json that are not in the
    # library yet: their PDFs go to <act>/Rules, regulations and notifications/<sections - title>/.
    by_id = {l["id"]: l for l in laws}
    for f in sorted((ROOT / "data" / "related").glob("*.json")):
        reg = json.loads(f.read_text())
        act = by_id.get(reg["act"])
        for i in reg["instruments"]:
            if i.get("library") or i["status"] == "repealed":
                continue
            core = re.sub(r",?\s*\(?\d{4}\)?$", "", re.sub(r"\s+—.*$", "", i["title"]))
            laws.append(
                {
                    "id": f"{reg['act']}:{letters(i['title'])[:40]}",
                    "title": i["title"],
                    "year": (re.search(r"(1[89]|20)\d\d", i["title"]) or [None])[0],
                    "keys": {letters(core)} if len(letters(core)) > 12 else set(),
                    "file": None,
                    "edition": None,
                    "area": act["area"] if act else "Other",
                    "folder": [act["title"] if act else reg["act"], "Rules, regulations and notifications", instrument_folder(i)],
                }
            )
    return laws


def instrument_folder(i):
    secs = ", ".join(f"s.{s}" for s in i.get("sections", [])) or "section to confirm"
    return f"{secs} - {i['title']}"


def first_pages_text(path, pages=2):
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            return ""
    try:
        with pymupdf.open(path) as doc:
            return " ".join(doc[i].get_text() for i in range(min(pages, len(doc))))
    except Exception:
        return ""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def identify(path, laws, known_hashes):
    """(law, edition, how) for a PDF; law is None when it cannot be placed."""
    name = path.name
    stem = path.stem
    digest = sha256(path)
    text = None
    law = next((l for l in laws if l["file"] == name), None)
    how = "file name in manifest" if law else None
    if not law and digest in known_hashes:
        law, how = known_hashes[digest], "same file as the library's"
    if not law:
        flat = letters(stem)
        hits = [l for l in laws if any(k and k in flat for k in l["keys"]) and (not l["year"] or l["year"] in stem)]
        if len(hits) == 1:
            law, how = hits[0], "title in file name"
    if not law:
        text = first_pages_text(path)
        flat = letters(text[:4000])
        hits = [l for l in laws if any(k and k in flat for k in l["keys"]) and (not l["year"] or l["year"] in text[:4000])]
        hits.sort(key=lambda l: flat.find(min(l["keys"], key=lambda k: flat.find(k) if k in flat else 1 << 30)))
        if hits:
            law, how = hits[0], "title on first page"
    # The PDF's own cover ("amended up to 30th June, 2026") beats a file name, which may have been renamed.
    if text is None:
        text = first_pages_text(path)
    edition = edition_in_text(text)
    if not edition and known_hashes.get(digest) is law:
        edition = law["edition"]
    return law, edition, how, digest


def safe(s):
    return re.sub(r'[\\/:*?"<>|]+', "-", s).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="sources", action="append", default=[], help="a folder to read PDFs from (repeat for each)")
    ap.add_argument("--to", required=True, help="the unified folder")
    ap.add_argument("--mirror", help="also copy the unified folder here (for example the Google Drive folder Claude reads)")
    ap.add_argument("--scaffold", help="create section-wise folders for the instruments made under this act id")
    ap.add_argument("--apply", action="store_true", help="copy files; without it nothing is written")
    a = ap.parse_args()

    laws = load_library()
    by_id = {l["id"]: l for l in laws}
    known = {}
    pdf_dir = ROOT / "sources" / "pdf"
    for l in laws:
        if l["file"] and (pdf_dir / l["file"]).exists():
            known[sha256(pdf_dir / l["file"])] = l
    to = Path(os.path.expanduser(a.to))

    rows, seen = [], {}
    for src in a.sources:
        src = Path(os.path.expanduser(src))
        if not src.is_dir():
            sys.exit(f"Not a folder: {src}")
        for p in sorted(src.rglob("*.pdf")):
            if to in p.parents:
                continue  # skip what an earlier run already gathered
            law, edition, how, digest = identify(p, laws, known)
            if digest in seen:
                seen[digest]["copies"].append(str(p))
                seen[digest]["names"].append(edition_in_name(p.name))
                continue
            row = {"path": p, "law": law, "edition": edition, "how": how, "digest": digest, "copies": [], "names": [edition_in_name(p.name)]}
            seen[digest] = row
            rows.append(row)

    # Without a date on the PDF itself, fall back to the date in its file name(s).
    for r in rows:
        if not r["edition"]:
            names = sorted({n for n in r["names"] if n})
            r["edition"] = names[-1] if names else None
            r["names_disagree"] = len(names) > 1
            if names:
                r["how"] = (r["how"] or "") + "; edition from file name"
    plan = []
    for law_id in sorted({r["law"]["id"] for r in rows if r["law"]}):
        law = by_id[law_id]
        mine = sorted((r for r in rows if r["law"] and r["law"]["id"] == law_id), key=lambda r: r["edition"] or "", reverse=True)
        folder = to / safe(law["area"]) / Path(*map(safe, law.get("folder") or [law["title"]]))
        for i, r in enumerate(mine):
            dest = folder / ("" if i == 0 else "Older editions") / f"{r['edition'] or 'undated'} - {r['path'].name}"
            if i == 0 and law.get("folder"):
                verdict = "not in the library yet: ask Claude to add it"
            elif i == 0:
                verdict = (
                    "NEWER than the library" if r["edition"] and law["edition"] and r["edition"] > law["edition"]
                    else "same as the library" if r["edition"] == law["edition"]
                    else "older than the library" if r["edition"] and law["edition"]
                    else "edition not found: check by hand"
                )
            else:
                verdict = "older copy"
            if r.get("names_disagree"):
                verdict += "; copies are named with different editions: check by hand"
            plan.append((r, dest, law, verdict))
    for r in rows:
        if not r["law"]:
            plan.append((r, to / "_To sort" / r["path"].name, None, "could not identify"))

    print(f"{len(rows)} distinct PDF(s) found; {sum(len(r['copies']) for r in rows)} duplicate copies skipped.\n")
    for r, dest, law, verdict in plan:
        lib = f" (library: {law['edition']})" if law and law["edition"] else ""
        print(f"[{verdict}] {law['title'] if law else '?'}{lib}\n    {r['path']}\n    -> {dest.relative_to(to)}")

    if a.scaffold:
        reg = json.loads((ROOT / "data" / "related" / f"{a.scaffold}.json").read_text())
        act = by_id.get(a.scaffold)
        base = to / safe(act["area"] if act else "Other") / safe(act["title"] if act else a.scaffold) / "Rules, regulations and notifications"
        print(f"\nSection-wise folders under {base.relative_to(to)}:")
        for i in reg["instruments"]:
            if i["status"] == "repealed":
                continue
            print(f"    {safe(instrument_folder(i))}")
            if a.apply:
                (base / safe(instrument_folder(i))).mkdir(parents=True, exist_ok=True)

    if not a.apply:
        print("\nNothing copied. Add --apply to copy the files.")
        return

    for r, dest, law, verdict in plan:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(r["path"], dest)
    to.mkdir(parents=True, exist_ok=True)
    with open(to / "unified-index.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["law", "library id", "edition", "library edition", "status", "file in unified folder", "copied from", "other copies", "identified by", "sha256"])
        for r, dest, law, verdict in plan:
            w.writerow([law["title"] if law else "", law["id"] if law else "", r["edition"] or "", law["edition"] if law else "", verdict,
                        str(dest.relative_to(to)), str(r["path"]), "; ".join(r["copies"]), r["how"] or "", r["digest"]])
    print(f"\nCopied into {to} and wrote unified-index.csv ({date.today().isoformat()}).")
    if a.mirror:
        mirror = Path(os.path.expanduser(a.mirror))
        shutil.copytree(to, mirror, dirs_exist_ok=True)
        print(f"Mirrored the unified folder to {mirror}.")


if __name__ == "__main__":
    main()
