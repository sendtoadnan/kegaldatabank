# Task tracker

The one list of everything to do for the Legal Databank. Claude reads it at the start of every session and updates it before the session ends: new tasks are added with the next number, finished ones are marked Done with the date, and nothing is deleted.

- **Owner:** *You* (the user: browser downloads from SECP, decisions, merging on GitHub, checking text) or *Claude* (scripts, data, website, pull requests).
- **Status:** *Pending* · *Waiting* (blocked on the other owner) · *Done* · *Deferred* (put off by the user).

Last updated: 1 November 2026.

## Open

| # | Task | Owner | Status | Notes |
|---|---|---|---|---|
| 12 | Merge PR #25 on github.com (one Netlify deploy) | You | Pending | https://github.com/sendtoadnan/kegaldatabank/pull/25 — all work since 4 Oct 2026 |
| 13 | After the merge: switch to `main`, pull, delete the branch | Claude | Waiting | Waits on 12; say "pull" |
| 14 | Delete five empty folders in `Unified/Corporate & Securities` | You | Pending | Old S.R.O. 464, Companies (Court) Rules, Debt Securities Trustees, Public Offering, Share Registrars folders (Claude's safety check blocks folder removal) |
| 15 | Work through the Companies Act sections still marked "To identify" | Claude | Waiting | Two passes done 1 Nov 2026 (56 → 17). 9 more are marked "Set in each order" (no instrument expected). The 17 left: 86, 104, 162, 188, 216, 258, 337, 341, 362, 376, 396, 440, 454, 456, 457, 459, 467. Revisit when new SECP material arrives |
| 16 | Download S.R.O. 1336(I)/2025 (IFRS 17 date extension) and screenshot the S.R.O. 1715(I)/2023 listing | You | Pending | Section 225/228 entry |
| 17 | Download SECP Circular 15 of 2017 (exemption from NTN requirement) | You | Pending | Section 153 entry is from the search index only |
| 18 | Screenshot SECP's listings of Circulars 7 and 21 of 2025 | You | Pending | PDFs already saved |
| 19 | Employees Contributory Funds Regulations "updated – July 2019" | You | Pending | SECP's page shows a 0.00 KB file (screenshot 1 Nov 2026); get the amending S.R.O.s listed 26/04/2019 and 26/07/2019, or ask SECP |
| 20 | Listed Companies (Buy-back of Shares) Regulations 2019 with the 2022 amendments | You | Pending | From CLAUDE.md state (October 2026) |
| 21 | Official consolidated PDF of the Public Sector Companies (Corporate Governance) Rules 2013 as amended to 2019 | You | Pending | Amending S.R.O. 715(I)/2019 is saved; only a Word file of the rules |
| 22 | Screenshot of the SECP listing of S.R.O. 1300(I)/2018 | You | Pending | |
| 23 | PDFs of the repealed instruments in the register | You | Pending | e.g. Companies (E-Voting) Regulations 2016, cost record orders |
| 24 | Screenshot of the SECP listing of the Companies (Asset Backed Securitization) Rules 1999 | You | Pending | PDF saved (updated to 14 Apr 2022) |
| 25 | Check the text of Unverified instruments against their PDFs | You | Pending | Nine Companies Act instruments of 4 Oct 2026 and S.R.O. 464(I)/2024. Claude makes checklists (`python3 scripts/verify_sheet.py --unverified`) and records the result (`mark_verified.py`) |
| 26 | Add the Easy Exit amendment S.R.O.s (2015, 314/2016, 456/2016) to the register's Easy Exit Regulations entry | Claude | Pending | PDFs in `_To sort`; two are scans |
| 27 | Decide which other laws in `_To sort` to add to the library | You | Pending | NBFC Rules 2003, VPS Rules (S.R.O. 298(I)/2024), Centralized KYC Organization Rules 2017, Search and Seizure Rules 2019, Clearing Houses Rules 2005, Secured Transactions Registry Rules 2019, Companies (Issue of Capital) Rules 1996, General Provisions and Forms Rules 1985 (Word only) |
| 28 | Tidy `_To sort`: remove the duplicate Secured Transactions Registry Rules copy and the Competition Commission registrar regulations (wrong download) | You | Pending | |
| 29 | Look at the results of the first weekly update check (Monday 2 Nov 2026) | Claude | Pending | `data/update-check.json`; the workflow pushes to `main`, which deploys |
| 30 | Investor Education and Awareness Fund rules | You | Waiting | Only draft rules found so far |
| 36 | If SECP lists regulations or forms for voluntary winding up (declaration of solvency, statement to creditors, final meeting report), download them | You | Pending | Sections 351, 357, 359, 369 are linked to the Court Rules 1997 only as the nearest provision |
| 37 | Check the matching of the 115 Court Rules 1997 forms to Companies Act 2017 sections | You | Pending | Page `acts/companies-act-2017/forms-court-rules-1997.html`; matched by subject, each to be confirmed |
| 40 | Get the notification of 2 August 2024 under section 37 of the SECP Act naming the court for Companies Act offences (S.R.O. number, text) | You | Pending | Section 482. The Sindh High Court order of 6 Sep 2024 citing it is saved; the notification itself is still needed. An unofficial summary you saved mentions an S.R.O. of 26 Dec 2017 and the Ministry of Law and Justice: unconfirmed |
| 43 | Download the Panel of Provisional Managers and Official Liquidators Regulations 2019 from SECP's Regulations page, with a listing screenshot | You | Pending | Section 315; found only through a KPMG copy and news reports |
| 31 | Modaraba Rules 1981, CRC Rules 2019 and S.R.O. 243/2024 | You | Deferred | Deferred by the user (Oct 2026); PDFs now in `_To sort` |

## Done

| # | Task | Owner | Done on | Notes |
|---|---|---|---|---|
| 1 | Publish the work held back during the Netlify deploy limit | Claude | 1 Nov 2026 | PR #21, merged |
| 2 | Turn the weekly regulator-website check back on | Claude | 1 Nov 2026 | `gh workflow enable` |
| 3 | Sections to identify, batch 1 (ss.5–132) | Claude | 1 Nov 2026 | ss.17, 53, 54, 132 linked |
| 4 | Sections to identify, batch 2 (ss.153–258) | Claude | 1 Nov 2026 | ss.153, 225, 228 linked |
| 5 | Read the first SECP downloads; add S.R.O. 464(I)/2024 to the library | Claude | 1 Nov 2026 | Listing screenshot recorded the same day |
| 6 | Show instruments made under other laws ("Other law" badge) | Claude | 1 Nov 2026 | Court Rules 1997, Debt Securities Trustees, Public Offering, Share Registrars Regulations |
| 7 | Combine all open PRs into one to save Netlify deploys | Claude | 1 Nov 2026 | #22–#24 closed into #25 |
| 8 | Search terms per law, Search guide page, "Laws and rules" in search results | Claude | 1 Nov 2026 | `data/search-terms.json` |
| 9 | Search matches words from their start ("gst" no longer finds "amongst") | Claude | 1 Nov 2026 | |
| 10 | Sections to identify, batch 3 (ss.264–341) | Claude | 1 Nov 2026 | ss.317, 320, 339 linked to the Court Rules 1997 |
| 11 | Read the second round of downloads | Claude | 1 Nov 2026 | Circulars 7 and 21 of 2025, ABS Rules 1999, S.R.O. 715(I)/2019, EPF Rules 2016 (repealed), S.R.O. 1715(I)/2023 confirmed; files moved to the `s.<section> - <title>` folders |
| 32 | Download the panel of liquidators register and panel of mediators | You | 1 Nov 2026 | Lists only; filed under s.315 and s.276 |
| 33 | Download S.R.O. 1715(I)/2023 (IFRS 17) and screenshot S.R.O. 464 and the ECF "updated" page | You | 1 Nov 2026 | |
| 34 | Create this tracker | Claude | 1 Nov 2026 | |
| 38 | Match every Court Rules 1997 form (framed under the 1984 Ordinance) to the Companies Act 2017 | Claude | 1 Nov 2026 | 115 forms on a new page; compromise forms 19–21 have no counterpart (the Commission now sanctions compromises) |
| 42 | Read the third round of downloads | Claude | 1 Nov 2026 | Sindh High Court order (s.482), Offences in Respect of Banks (Special Courts) Ordinance 1984 (two copies), an unofficial summary (not used as a source); filed under s.482. S.R.O. 1715 PDF and screenshots filed |
| 44 | Second pass over the remaining sections | Claude | 1 Nov 2026 | s.187 (PSC Rules 2013, rule 5(2)) and s.315 (Panel Regulations 2019, to confirm) linked; 9 sections marked "Set in each order"; 17 left |
| 41 | Sections to identify, batch 6 (ss.472–506) — last unsearched sections | Claude | 1 Nov 2026 | ss.472, 506 (Companies Regulations 2024, regs. 94 and 30) and 482 (s.37 SECP Act notification, to confirm) linked; 474, 475, 484 set in each order |
| 39 | Sections to identify, batch 5 (ss.423–470) | Claude | 1 Nov 2026 | ss.423, 446 (447), 461, 470 linked; 440, 454, 456, 457, 459, 467 left open |
| 35 | Sections to identify, batch 4 (ss.351–420) | Claude | 1 Nov 2026 | ss.351, 357, 359, 369, 415, 416 linked to the Court Rules 1997; 362, 376, 396, 420 left open |
