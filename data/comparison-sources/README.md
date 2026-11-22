Working records for `data/comparison/` (internal; not published on the website).

- `comparative-index-rows.json`: rows read by `tools/ocr/comparative_index_pdf.py` from a third-party printed comparison of the Companies Act 2017 and the Companies Ordinance 1984 (Deloitte Yousuf Adil, "Comparative Index of Sections", 30 pages, supplied by the user from OneDrive `Laws n Regulations/Companies Ordinance and Acts/`). Only section numbers are used; none of its text appears on the site.
- The book's table is in `data/salam/corresponding-provisions.json`.
- The Ordinance's own section headings come from its contents list (`Companies Ordinance 1984 as at 26 Dec 2018.pdf`, same folder).
- Rebuild: `python3 tools/ocr/build_comparison.py data/comparison-sources/comparative-index-rows.json "<Ordinance 1984 PDF>"`.
