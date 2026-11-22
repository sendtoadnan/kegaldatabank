# Pages missing from the scanned book

Resolved 21 Nov 2026 from the older (Dec 2021) scan in OneDrive `Laws n Regulations/SA Salam`: Private Funds Regulations, Structuring of Debt Securities Regulations, Collateral Management Companies Regulations 2019 and the Stock Exchanges Demutualization Regulations (removed from the table below). The Demutualization **Act**, section 6-7 page (IV-148), is missing from both scans: the older scan has only the reverse side of that sheet.

Pages that the scans of the user's binders lack, found 16 Nov 2026 while converting. Each blocks the instrument named, because law text is cut where the page should be. Please scan these pages (or the whole instrument again) into the same folders; the converter then finishes them (`python3 tools/ocr/book_to_json.py …`, entries in `data/salam/conversions.json`).

| Instrument | Volume | Missing pages | What is lost |
|---|---|---|---|
| Voluntary Pension System Rules, 2005 | Volume I Part III | pages III-49 and III-84 (first and last page) | rules 11, 23, 31 and 41 not found |
| Securities Brokers (Licensing and Operations) Regulations, 2016 | Volume I Part III | pages III-287 and III-296 | text is cut mid-regulation where these pages should be |
| Clearing House (Licensing and Operations) Regulations, 2016 | Volume I Part III | pages III-343 to III-348 (six NBFC pages V-343 to V-348 are filed in their place) | regulations 4 to 9 are on these pages |
| Securities Exchanges (Licensing and Operations) Regulations, 2016 | Volume I Part III | page III-371 | regulation 17 is on this page |
| Modaraba Regulations, 2021 | Volume I Part III | pages III-1102, III-1103 and III-1138 | regulations 7 to 9 and 22 |
| Stock Exchanges (Corporatisation, Demutualization and Integration) Act, 2012 | Volume II Part IV | page IV-148 | sections 6 and 7 |
| Non-Banking Finance Companies and Notified Entities Regulations, 2008 | Volume II Part VA | the page(s) between book pages VA-14 and VA-15 | regulations 3 to 9(1)(a) (text jumps from the end of regulation 2 to the middle of regulation 9) |

Also: the Volume II NBFC Rules 2003 lack book pages V-17 to V-56 (task 67), and Volume II Part 2 (Modaraba, Competition, Credit Rating, Anti-Money Laundering) has not been scanned (task 61). The six NBFC pages V-343 to V-348 filed inside the Clearing House Regulations in Volume I belong in Volume II Part V (Miscellaneous Circulars).
