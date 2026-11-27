"""Catalogue the SECP notifications, circulars, directives and guidelines the editor saved from secp.gov.pk.

usage: python3 scripts/build_notices.py <folder with secp__<kind>__*.pdf> [--ocr <path to the compiled scripts/ocr_pdf.swift>]
For each kind it keeps one copy of each distinct PDF (identical files are listed once; error pages saved as .bin, trashed files and
non-PDF files are skipped), copies it to sources/pdf/notices/secp/<kind>/, and writes
  data/notices/secp-<kind>.json       title, number, date, pages, size per file
  data/notices-text/secp-<kind>.json  the first ~3,000 characters of each PDF's own text, used only for search
Titles are SECP's own file names made readable; number and date are read from the title or the first page. Nothing is shown
from OCR except as search words; a scan with no text layer is read with Apple Vision (first two pages) for that purpose only.
"""
import fitz, hashlib, json, os, re, subprocess, sys, shutil, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]).expanduser()
OCR = sys.argv[sys.argv.index("--ocr") + 1] if "--ocr" in sys.argv else None
KINDS = {"notifications": "Notifications", "circulars": "Circulars", "directives": "Directives", "guidelines": "Guidelines"}
MONTHS = "january february march april may june july august september october november december".split()
ACR = {"sro": "S.R.O.", "secp": "SECP", "aml": "AML", "cft": "CFT", "nbfc": "NBFC", "nbfcs": "NBFCs", "cdc": "CDC", "reit": "REIT", "ipo": "IPO", "llp": "LLP", "llps": "LLPs",
       "kyc": "KYC", "faqs": "FAQs", "faq": "FAQ", "ifrs": "IFRS", "ias": "IAS", "tfcs": "TFCs", "ccg": "CCG", "psx": "PSX", "pmex": "PMEX", "ncpl": "NCCPL", "nccpl": "NCCPL",
       "sdrc": "SDRC", "ntn": "NTN", "fbr": "FBR", "fmu": "FMU", "sbp": "SBP", "ca": "CA", "ifrs": "IFRS", "pkr": "PKR", "us": "US", "uk": "UK", "icap": "ICAP", "icmap": "ICMAP", "bc": "BC"}
SMALL = {"of", "the", "to", "in", "and", "for", "on", "by", "under", "a", "an", "or", "with", "from", "at", "as"}


def slug_of(name, kind):
    s = re.sub(r"^secp__" + kind + r"__", "", name)
    return re.sub(r"\.pdf$", "", s, flags=re.I)


def humanise(slug):
    s = re.sub(r"%[0-9a-f]{2}", " ", slug.lower())
    s = re.sub(r"\bs-r-o\b", "sro", s)
    s = re.sub(r"\bsro-?(\d+)-?i-?(\d{4})\b", r"sro \1(i)/\2", s)
    s = re.sub(r"\bsro-?(\d+)i-?(\d{4})\b", r"sro \1(i)/\2", s)
    s = re.sub(r"\b(\d+)i(\d{4})\b", r"\1(i)/\2", s)
    s = re.sub(r"\bsro-?(\d+)\b", r"sro \1", s)
    s = re.sub(r"(?<=\d)-(?=\d{4}\b)", " ", s)
    words = [w for w in re.split(r"[-_\s]+", s) if w]
    out = []
    for i, w in enumerate(words):
        m = re.match(r"^(\d+)\(i\)/(\d{4})$", w)
        if m: out.append(f"{m.group(1)}(I)/{m.group(2)}"); continue
        if w in ACR: out.append(ACR[w]); continue
        if i and w in SMALL: out.append(w); continue
        out.append(w.capitalize() if not w.isdigit() else w)
    t = " ".join(out)
    return re.sub(r"\s+", " ", t).strip()


def number_of(title, text):
    m = re.search(r"S\.R\.O\.\s*(?:No\.?\s*)?(\d+)\s*\(I\)\s*/\s*(\d{4})", title) or re.search(r"S\.R\.O\.\s*(\d+)\s*of\s*(\d{4})", title)
    if m: return f"S.R.O. {m.group(1)}(I)/{m.group(2)}"
    m = re.search(r"Circular\s*(?:No\.?)?\s*(\d+)\s*of\s*(\d{4})", title, re.I)
    if m: return f"Circular {int(m.group(1))} of {m.group(2)}"
    m = re.search(r"S\.?\s?R\.?\s?O\.?\s*(?:No\.?\s*)?(\d{1,4})\s*\(\s*I\s*\)\s*/?\s*(\d{4})", text[:2500])
    if m: return f"S.R.O. {m.group(1)}(I)/{m.group(2)}"
    return ""


def date_of(title, text):
    for src in (title, text[:2500]):
        m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?[\s,.-]+(" + "|".join(MONTHS) + r")[a-z]*[\s,.-]+(\d{4})", src, re.I)
        if m:
            d, mo, y = int(m.group(1)), MONTHS.index(m.group(2).lower()) + 1, int(m.group(3))
            if 1 <= d <= 31 and 1990 <= y <= 2027: return f"{y:04d}-{mo:02d}-{d:02d}"
        m = re.search(r"(" + "|".join(MONTHS) + r")[a-z]*[\s,.-]+(\d{1,2})(?:st|nd|rd|th)?[\s,.-]+(\d{4})", src, re.I)
        if m:
            d, mo, y = int(m.group(2)), MONTHS.index(m.group(1).lower()) + 1, int(m.group(3))
            if 1 <= d <= 31 and 1990 <= y <= 2027: return f"{y:04d}-{mo:02d}-{d:02d}"
    return ""


def year_of(title, number, date):
    if date: return int(date[:4])
    m = re.search(r"(19|20)\d{2}", number or "") or re.search(r"\b(19|20)\d{2}\b", title)
    return int(m.group(0)) if m else 0


def clean(t):
    return re.sub(r"\s+", " ", t.replace("\xad", "")).strip()


def read(path, pages_text_limit=3000):
    try:
        doc = fitz.open(path)
    except Exception:
        return None
    n = len(doc); txt = ""
    for p in doc:
        txt += " " + p.get_text()
        if len(txt) > pages_text_limit * 2: break
    return n, clean(txt)


def ocr_first_pages(path):
    if not OCR: return ""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "o.txt"
        subprocess.run([OCR, str(path), str(out), "1", "2"], capture_output=True, timeout=300)
        return clean(re.sub(r"<<<page \d+>>>", " ", out.read_text())) if out.exists() else ""


def one(args):
    kind, f, dest_dir = args
    path = SRC / f
    r = read(path)
    if r is None: return None
    pages, text = r
    ocr = False
    if len(text) < 80:
        text = ocr_first_pages(path); ocr = bool(text)
    slug = slug_of(f, kind)
    clean_name = re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9._-]", "-", slug.lower())).strip("-") + ".pdf"
    shutil.copy(path, dest_dir / clean_name)
    title = humanise(slug)
    number = number_of(title, text); date = date_of(title, text)
    return {"id": f"{kind}-{clean_name[:-4]}"[:120], "file": f"notices/secp/{kind}/{clean_name}", "title": title, "number": number, "date": date,
            "year": year_of(title, number, date), "pages": pages, "bytes": path.stat().st_size, "textFrom": "ocr" if ocr else ("pdf" if text else "none")}, text[:3000]


def main():
    for kind, label in KINDS.items():
        names = sorted(f for f in os.listdir(SRC) if f.startswith(f"secp__{kind}__") and f.lower().endswith(".pdf") and "trashed" not in f)
        seen = {}
        for f in names:
            h = hashlib.sha256((SRC / f).read_bytes()).hexdigest()
            if h not in seen or len(f) < len(seen[h]): seen[h] = f
        dest = ROOT / "sources" / "pdf" / "notices" / "secp" / kind
        if dest.exists(): shutil.rmtree(dest)
        dest.mkdir(parents=True)
        with ThreadPoolExecutor(6) as ex:
            res = [r for r in ex.map(one, [(kind, f, dest) for f in sorted(seen.values())]) if r]
        items = sorted((r[0] for r in res), key=lambda x: (-(x["date"] or f'{x["year"]:04d}-00-00' and 0) if False else 0, x["title"]))
        texts = {r[0]["id"]: r[1] for r in res if r[1]}
        ids = set(); 
        for it in items:
            base = it["id"]; k = 2
            while it["id"] in ids: it["id"] = f"{base}-{k}"; k += 1
            ids.add(it["id"])
        texts = {it["id"]: t for it, t in ((r[0], r[1]) for r in res) if t}
        (ROOT / "data" / "notices").mkdir(exist_ok=True); (ROOT / "data" / "notices-text").mkdir(exist_ok=True)
        (ROOT / "data" / "notices" / f"secp-{kind}.json").write_text(json.dumps({"regulator": "Securities and Exchange Commission of Pakistan", "kind": kind, "label": label, "items": items}, ensure_ascii=False, indent=1) + "\n")
        (ROOT / "data" / "notices-text" / f"secp-{kind}.json").write_text(json.dumps(texts, ensure_ascii=False, separators=(",", ":")))
        print(kind, len(items), "items;", sum(1 for i in items if i["number"]), "numbered;", sum(1 for i in items if i["date"]), "dated;", sum(1 for i in items if i["textFrom"] == "none"), "no text")


main()
