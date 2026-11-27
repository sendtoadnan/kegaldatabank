"""Add the Foreign Exchange Manual's appendices (separate PDFs on the State Bank's website) to data/acts/foreign-exchange-manual.json.

usage: python3 tools/fe_appendices.py "<folder with the SBP files>"
Copies each appendix PDF into sources/pdf/ and lists it under `schedules` with its own `pdf` file, so the instrument page links
to it and search finds its words (then run scripts/extract_schedule_text.py foreign-exchange-manual). Appendix V (the forms) is
listed form by form: a form starts on the page whose heading reads "APP. V <n>". No text is typed or corrected.
"""
import fitz, json, re, shutil, sys
from pathlib import Path
SRC = Path(sys.argv[1]); ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "foreign-exchange-manual-appendix-ii.pdf": "sbp_fem__Appendix-II-foreign-exchange-manual.pdf",
    "foreign-exchange-manual-appendix-iv-authorized-dealers.pdf": "sbp_fem__FE04_Appx1-foreign-exchange-manual.pdf",
    "foreign-exchange-manual-authorized-hotels.pdf": "sbp_fem__List-Auth-Hotels.pdf",
    "foreign-exchange-manual-appendix-v-forms.pdf": "sbp_fem__List-Appendices-V-foreign-exchange-manual.pdf",
}
for dst, src in FILES.items():
    shutil.copy(SRC / src, ROOT / "sources" / "pdf" / dst)
sch = [
    {"title": "Appendix II — Notifications issued by the Federal Government under the Foreign Exchange Regulation Act, 1947", "page": 1, "pdf": "foreign-exchange-manual-appendix-ii.pdf"},
    {"title": "Appendix IV — List of Authorized Dealers", "page": 1, "pdf": "foreign-exchange-manual-appendix-iv-authorized-dealers.pdf"},
    {"title": "List of Authorized Hotels", "page": 1, "pdf": "foreign-exchange-manual-authorized-hotels.pdf"},
]
doc = fitz.open(ROOT / "sources" / "pdf" / "foreign-exchange-manual-appendix-v-forms.pdf"); last = None
for i, p in enumerate(doc):
    m = re.match(r"(?:Annexure to )?APP\.? ?V[ .]*(\d+[A-Z]?)\b", " ".join(p.get_text().split()))
    if m and m.group(1) != last:
        sch.append({"title": f"Appendix V — Form {m.group(1)}", "page": i + 1, "pdf": "foreign-exchange-manual-appendix-v-forms.pdf"})
        last = m.group(1)
f = ROOT / "data" / "acts" / "foreign-exchange-manual.json"
raw = f.read_text(); d = json.loads(raw)
d["schedules"] = sch
f.write_text(json.dumps(d, ensure_ascii=False, indent=1 if raw.startswith('{\n "') else 2) + ("\n" if raw.endswith("\n") else ""))
print(len(sch), "appendix entries")
