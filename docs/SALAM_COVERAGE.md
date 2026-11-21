# S.A. Salam coverage check

## Progress benchmark (2026-11-21)

- **Instruments in the book's contents that are now in the library: 74 of 114 = 65%** (all Unverified; the book is the source).
- Of what has been scanned (98 instruments): 76%.
- The book's notification index: 174 of 406 numbers appear in our data = 43%.
- Pages read (OCR): 3,898 of the pages you scanned; Volume II Part 2 (Parts VI to IX) is not scanned, and about 85 pages inside scanned parts are missing (21 listed, plus most of the NBFC Rules 2003) from the binders (`docs/SCAN_GAPS.md`).
- Verified against a scan by a person: 0 of the instruments taken from the book (task 64).

What is left:

- not scanned yet (Volume II Part 2): 16
- scanned, not yet converted: 11
- scanned but blocked (pages missing from the scan, or needs converter work): 7
- repealed, not yet added (to add marked repealed): 6

Re-run `python3 tools/ocr/salam_coverage.py` to refresh these figures.

Made by `python3 tools/ocr/salam_coverage.py` from the book's contents and update history (`data/salam/`).
The book is a trusted source (CLAUDE.md, 12 Nov 2026). "Later changes" means the book's update notes record an amendment, new S.R.O. or circular on that instrument's pages after our edition date: check each before re-converting.

## Book has later changes (6)

| Book page | Instrument | Library | Our edition | Last change in book |
|---|---|---|---|---|
| AI-1 | Companies Act, 2017 | companies-act-2017 | 2022-08-18 | 2026-06-20 |
| III-413 | Public Offering Regulations, 2017 | public-offering-regulations-2017 | 2021-09-15 | 2026-05-25 |
| III-1151 | Shariah Governance Regulations, 2023 | shariah-governance-regulations-2023 | 2023-09-14 | 2023-09-18 |
| III-1187 | Unlisted Companies (Buy-Back of Shares) Regulations, 2023 — *Repealed by S.R.O. 210(I)/2024* | unlisted-companies-buy-back-regulations-2023 | 2023-10-12 | 2024-02-12 |
| I-1 | Futures Market Act, 2016 | futures-market-act-2016 | 2016-04-09 | 2024-06-05 |
| V-11 | Non-Banking Finance Companies (Establishment and Regulation) Rules, 2003 | nbfc-rules-2003 | 2023-09-14 | 2025-07-31 |

## Not in library (40)

| Book page | Instrument | Library | Our edition | Last change in book |
|---|---|---|---|---|
| II-1 | Companies (General Provisions and Forms) Regulations, 2018 |  |  | 2024-07-15 |
| III-20(1) | Companies (Buy-back of Shares) Rules, 1999 |  |  |  |
| III-20(5) | Companies (Rehabilitation of Sick Industrial Units) Rules, 1999 |  |  |  |
| III-21 | SECP (Appellate Bench Procedure) Rules, 2003 |  |  |  |
| III-49 | Voluntary Pension System Rules, 2005 |  |  | 2024-02-22 |
| III-85 | Group Companies Registration Regulations, 2008 — *Repealed by S.R.O. 210(I)/2024* |  |  | 2024-02-12 |
| III-249 | Central Depository Regulations, 2016 |  |  | 2023-08-10 |
| III-281 | Securities Brokers (Licensing and Operations) Regulations, 2016 |  |  | 2024-04-08 |
| III-341 | Clearing House (Licensing and Operations) Regulations, 2016 |  |  | 2023-08-10 |
| III-359 | Securities Exchanges (Licensing and Operations) Regulations, 2016 |  |  | 2023-08-10 |
| III-489 | Companies (Incorporation) Regulations, 2017 — *Repealed by S.R.O. 210(I)/2024* |  |  | 2024-02-12 |
| III-511 | Intermediaries (Registration) Regulations, 2017 — *Repealed by S.R.O. 210(I)/2024* |  |  |  |
| III-611 | Shariah Advisors Regulations, 2017 — *Repealed by S.R.O. 1314(I)/2023* |  |  |  |
| III-649 | Companies (Registration Offices) Regulations, 2018 |  |  | 2024-02-12 |
| III-765 | Associations with Charitable and Not for Profit Objects Regulations, 2018 — *Repealed by S.R.O. 210(I)/2024* |  |  | 2024-02-12 |
| III-889 | Shariah Governance Regulations, 2018 — *Repealed by S.R.O. 1314(I)/2023* |  |  |  |
| III-1093 | Modaraba Regulations, 2021 |  |  | 2024-01-24 |
| II-1 | SECP: Constitution |  |  |  |
| II-5 | SECP: Regulations, Rules and Procedures |  |  |  |
| III-39 | Corporate Social Responsibility Voluntary Guidelines, 2013 |  |  |  |
| IX-67 | Anti-Money Laundering (Amendment) Act, 2015 |  |  |  |
| V-89 | Prudential Regulations for Non-Banking Finance Companies |  |  |  |
| V-117 | Prudential Regulations for Consumer Finance by NBFCs |  |  |  |
| V-127 | Miscellaneous circulars etc. (NBFCs) |  |  | 2026-06-20 |
| VA-1 | Non-Banking Finance Companies and Notified Entities Regulations, 2008 |  |  | 2025-08-01 |
| VI-19 | Modaraba Companies and Modaraba Rules, 1981 |  |  |  |
| VI-79 | Prudential Regulations for Modarabas |  |  | 2022-01-31 |
| VII-1 | Competition Act, 2010 |  |  |  |
| VII-31 | Competition Commission (Conduct of Business) Regulations, 2007 |  |  |  |
| VII-39 | Competition Commission (Investment and Expenditures) Regulations, 2007 |  |  |  |
| VII-45 | Competition Commission (General Enforcement) Regulations, 2007 |  |  |  |
| VII-71 | Competition Commission (Leniency) Regulations, 2019 |  |  | 2019-06-19 |
| VII-77 | Competition Commission (Merger Control) Regulations, 2016 |  |  | 2024-03-18 |
| VII-100(1) | Competition Commission (Reward Payment to Informants) Regulations, 2014 |  |  |  |
| VII-100(5) | Competition Commission (Exemption) Regulations, 2020 |  |  | 2022-01-31 |
| VII-101 | Competition Commission (Appeal) Rules, 2007 |  |  |  |
| VII-119 | Competition Commission (Conduct of Investigating Officers) Rules, 2007 |  |  |  |
| VII-123 | Competition Commission (Extension in Exemption) Rules, 2007 |  |  |  |
| VII-132A | Competition Appellate Tribunal Rules, 2015 |  |  |  |
| VII-139 | Competition Commission (Collection of Fees and Charges) Rules, 2009 |  |  |  |

## No later change recorded (68)

| Book page | Instrument | Library | Our edition | Last change in book |
|---|---|---|---|---|
| II-41 | Companies Regulations, 2024 | companies-regulations-2024 | 2025-07-25 | 2025-07-25 |
| III-1 | Companies (Appointment of Legal Adviser) Rules, 1975 | companies-legal-adviser-rules-1975 | 2026-06-20 |  |
| III-5 | Companies (Invitation and Acceptance of Deposit) Rules, 1987 | companies-deposit-rules-1987 | 2026-06-20 |  |
| III-13 | Companies (Management by Administrator) Rules, 1993 | companies-management-by-administrator-rules-1993 | 2026-06-20 |  |
| III-117 | Public Sector Companies (Corporate Governance) Rules, 2013 | public-sector-companies-cg-rules-2013 | 2026-06-20 |  |
| III-139 | Companies (Easy Exit) Regulations, 2014 | companies-easy-exit-regulations-2014 | 2026-06-20 |  |
| III-147 | Sukuk (Privately Placed) Regulations, 2017 | sukuk-privately-placed-regulations-2017 | 2026-06-20 |  |
| III-157 | Companies (Investment in Associated Companies or Associated Undertakings) Regulations, 2017 | companies-investment-associated-regulations-2017 | 2017-12-06 |  |
| III-177 | Research Analyst Regulations, 2015 | research-analyst-regulations-2015 | 2026-06-20 | 2026-01-02 |
| III-183 | Joint Inspection Regulations, 2015 | joint-inspection-regulations-2015 | 2026-06-20 |  |
| III-213 | Reporting and Disclosure Regulations, 2015 | reporting-disclosure-regulations-2015 | 2026-06-20 |  |
| III-223 | Private Funds Regulations, 2015 | private-funds-regulations-2015 | 2021-12-31 |  |
| III-269 | Opportunity of Hearing Regulations, 2016 | opportunity-of-hearing-regulations-2016 | 2026-06-20 |  |
| III-273 | Obligations under Voluntary Winding-up Regulations, 2016 | voluntary-winding-up-obligations-regulations-2016 | 2026-06-20 |  |
| III-279 | Insider Information Regulations, 2016 | insider-information-regulations-2016 | 2026-06-20 |  |
| III-309 | Credit Rating Companies Regulations, 2016 | credit-rating-companies-regulations-2016 | 2026-06-20 | 2023-12-22 |
| III-373 | Structuring of Debt Securities Regulations, 2020 | structuring-debt-securities-regulations-2020 | 2021-12-31 |  |
| III-383 | Share Registrars and Balloters Regulations, 2017 | share-registrars-balloters-regulations-2017 | 2026-06-20 |  |
| III-393 | Securities and Futures Advisers (Licensing and Operations) Regulations, 2017 | securities-futures-advisers-regulations-2017 | 2026-06-20 | 2023-06-15 |
| III-407 | Public Offering (Regulated Securities Licensing) Regulations, 2017 | public-offering-regulated-securities-licensing-regulations-2017 | 2026-06-20 | 2025-08-06 |
| III-439 | Private Placement of Securities Rules, 2017 | private-placement-rules-2017 | 2026-06-20 |  |
| III-443 | Centralized KYC Organization Rules, 2017 | centralized-kyc-organization-rules-2017 | 2026-06-20 |  |
| III-451 | Customer Compensation Fund (Establishment and Operation) Rules, 2017 | customer-compensation-fund-rules-2017 | 2026-06-20 |  |
| III-455 | Centralized Customer Protection Compensation Fund Regulations, 2017 | centralized-customer-protection-compensation-fund-regulations-2017 | 2026-06-20 |  |
| III-459 | CMC (Establishment and Operation) Regulations, 2017 | cmc-regulations-2017 | 2026-06-20 |  |
| III-473 | Futures Exchanges (Licensing and Operations) Regulations, 2017 | futures-exchanges-regulations-2017 | 2026-06-20 | 2023-11-17 |
| III-529 | Listed Companies (Substantial Acquisition of Voting Shares and Takeovers) Regulations, 2017 | listed-companies-takeovers-regulations-2017 | 2026-06-20 | 2024-01-24 |
| III-561 | Unclaimed Shares and Other Instruments and Undistributed Assets Regulations, 2017 | unclaimed-shares-regulations-2017 | 2017-10-06 |  |
| III-569 | Bond Pricing Agency Rules, 2017 | bond-pricing-agency-rules-2017 | 2026-06-20 |  |
| III-603 | Companies (Distribution of Dividends) Regulations, 2017 | companies-distribution-of-dividends-regulations-2017 | 2022-06-16 |  |
| III-629 | Listed Companies (Code of Corporate Governance) Regulations, 2019 | listed-companies-ccg-regulations-2019 | 2025-03-20 | 2024-09-10 |
| III-671 | Companies (Mediation and Conciliation) Regulations, 2018 | companies-mediation-conciliation-regulations-2018 | 2026-06-20 |  |
| III-679 | Companies (Postal Ballot) Regulations, 2018 | companies-postal-ballot-regulations-2018 | 2025-03-20 |  |
| III-687 | Companies (Manner and Selection of Independent Directors) Regulations, 2018 | companies-independent-directors-regulations-2018 | 2026-06-20 |  |
| III-691 | Auditors (Reporting Obligations) Regulations, 2018 | auditors-reporting-obligations-regulations-2018 | 2026-06-20 | 2024-04-01 |
| III-727 | Limited Liability Partnership Regulations, 2018 | llp-regulations-2018 | 2026-06-20 |  |
| III-753 | Credit and Suretyship (Conduct of Business) Rules, 2018 | credit-suretyship-rules-2018 | 2026-06-20 | 2022-07-05 |
| III-759 | Employees Contributory Funds (Investment in Listed Securities) Regulations, 2018 | employees-contributory-funds-investment-regulations-2018 | 2026-06-20 |  |
| III-793 | SECP (Anti Money Laundering and Countering Financing of Terrorism) Regulations, 2020 | secp-aml-cft-cpf-regulations-2020 | 2026-07-03 | 2023-09-21 |
| III-813 | Futures Brokers (Licensing and Operations) Regulations, 2018 | futures-brokers-regulations-2018 | 2026-06-20 | 2025-12-12 |
| III-857 | Companies (Related Party Transactions and Maintenance of Related Records) Regulations, 2018 | companies-rpt-regulations-2018 | 2018-10-02 |  |
| III-863 | Foreign Companies Regulations, 2018 | foreign-companies-regulations-2018 | 2026-06-20 | 2023-05-03 |
| III-919 | Companies (Further Issue of Shares) Regulations, 2020 | companies-further-issue-of-shares-regulations-2020 | 2026-01-13 | 2026-01-13 |
| III-953 | Listed Companies (Buy-back of Shares) Regulations, 2019 | listed-companies-buy-back-regulations-2019 | 2026-06-20 | 2022-09-06 |
| III-975 | Search and Seizure Rules, 2019 | secp-search-seizure-rules-2019 | 2019-07-01 |  |
| III-985 | Collateral Management Companies Regulations, 2019 | collateral-management-companies-regulations-2019 | 2021-12-31 |  |
| III-1011 | Corporate Restructuring Companies Rules, 2019 | corporate-restructuring-companies-rules-2019 | 2026-06-20 | 2024-02-20 |
| III-1025 | Panel of Provisional Managers and Official Liquidators Regulations, 2019 | panel-provisional-managers-liquidators-regulations-2019 | 2026-06-20 |  |
| III-1033 | Corporate Rehabilitation Regulations, 2019 | corporate-rehabilitation-regulations-2019 | 2026-06-20 |  |
| III-1043 | Secured Transactions Registry Regulations, 2020 | secured-transactions-registry-regulations-2020 | 2026-06-20 |  |
| III-1051 | Professional Clearing Members Regulations, 2020 | professional-clearing-members-regulations-2020 | 2026-06-20 |  |
| III-1067 | Oversight Regulations for Self-Regulatory Bodies of Accountants, 2020 | oversight-regulations-accountants-2020 | 2026-06-20 |  |
| III-1070(1) | Companies (Maintenance and Audit of Cost Accounts) Regulations, 2020 | companies-cost-accounts-regulations-2020 | 2020-12-14 |  |
| III-1071 | Securities and Exchange Commission (Reinsurance Brokers) Regulations, 2021 | reinsurance-brokers-regulations-2021 | 2026-06-20 |  |
| III-1143 | Issuance of Convertible Debt Securities through Right Offer Regulations, 2022 | convertible-debt-right-offer-regulations-2022 | 2026-06-20 | 2022-09-21 |
| III-1189 | Securities Managers (Licensing and Operations) Regulations, 2024 | securities-managers-regulations-2024 | 2026-06-20 | 2024-11-06 |
| I-29 | Securities and Exchange Rules, 1971 | securities-exchange-rules-1971 | 2026-06-20 |  |
| I-49 | Securities and Exchange Commission of Pakistan Act, 1997 | secp-act-1997 | 2016-12-31 |  |
| I-83 | Securities (Leveraged Markets and Pledging) Rules, 2011 | leveraged-markets-pledging-rules-2011 | 2026-06-20 |  |
| I-111 | Securities Act, 2015 | securities-act-2015 | 2015-05-18 |  |
| I-241 | Corporate Rehabilitation Act, 2018 | corporate-rehabilitation-act-2018 | 2026-06-20 |  |
| III-69 | Issue of Commercial Papers Regulations, 2013 | commercial-papers-regulations-2013 | 2026-06-20 |  |
| IV-1 | Central Depositories Act, 1997 | central-depositories-act-1997 | 1997-06-10 |  |
| IV-27 | Central Depository Companies (Establishment and Regulation) Rules, 1996 | cdc-establishment-regulation-rules-1996 | 2026-06-20 |  |
| IV-141 | Stock Exchanges (Corporatisation, Demutualization and Integration) Act, 2012 | stock-exchanges-demutualization-regulations-2012 | 2021-12-31 |  |
| IV-161 | Stock Exchanges (Corporatisation, Demutualization and Integration) Regulations, 2012 | stock-exchanges-demutualization-regulations-2012 | 2021-12-31 |  |
| IX-1 | Anti-Money Laundering Act, 2010 | aml-act-2010 | 2020-09-30 |  |
| VI-1 | Modaraba Companies and Modaraba (Floatation and Control) Ordinance, 1980 | modaraba-ordinance-1980 | 2012-12-31 |  |
