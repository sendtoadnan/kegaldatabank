# Where to look first when checking the converted instruments

Made by `python3 tools/ocr/cross_check.py --scans <scans folder>` on 2026-11-19. For each provision: the share of its five-word sequences that an independent, lower-resolution reading of the same scan pages also contains. Low = the two readings disagree there, so check that provision against the scan first. This is a guide to where mistakes are likely, not a verification: every instrument stays Unverified until a person checks it (task 64).

| Instrument | Agreement | Provisions below 85% (check these first) |
|---|---|---|
| Access to Insider Information Regulations, 2016 (`insider-information-regulations-2016`) | 65% | 2 (58%) |
| Companies (Easy Exit) Regulations, 2014 (`companies-easy-exit-regulations-2014`) | 84% | 4 (76%), 3 (84%) |
| Centralized Customer Protection Compensation Fund Regulations, Fund Regulations, 2017 (`centralized-customer-protection-compensation-fund-regulations-2017`) | 85% | 7 (72%), 6 (73%) |
| Companies (Mediation and Conciliation) Regulations, 2018 (`companies-mediation-conciliation-regulations-2018`) | 85% | 8 (81%), 9 (81%), 10 (81%), 12 (82%), 3 (82%), 11 (82%), 4 (84%) |
| Companies (Manner and Selection of Independent Directors) Regulations, 2018 (`companies-independent-directors-regulations-2018`) | 86% | 4 (82%) |
| Companies (Management by Administrator) Rules, 1993 (`companies-management-by-administrator-rules-1993`) | 86% | 4 (44%), 6 (47%), 12 (83%) |
| Bond Pricing Agency Rules, 2017 (`bond-pricing-agency-rules-2017`) | 87% | 11 (73%), 13 (74%), 5 (79%), 9 (81%), 7 (84%), 10 (85%) |
| Credit Rating Companies Regulations, 2016 (`credit-rating-companies-regulations-2016`) | 88% | 17 (65%), 2 (78%), 15 (84%), 13 (85%) |
| Sukuk (Privately Placed) Regulations, 2017 (`sukuk-privately-placed-regulations-2017`) | 88% | 2 (74%), 12 (82%), 9 (82%) |
| Listed Companies (Substantial Acquisition of Voting Shares and Takeovers) Regulations, 2017 (`listed-companies-takeovers-regulations-2017`) | 88% | 10 (5%), 23 (40%), 1 (58%), 7 (80%), 24 (80%), 19 (80%), 30 (83%) |
| Credit and Suretyship (Conduct of Business) Rules, 2018 (`credit-suretyship-rules-2018`) | 88% | 3A (72%), 3B (76%), 4 (80%) |
| Oversight Regulations for Self-Regulatory Bodies of Accountants, 2020 (`oversight-regulations-accountants-2020`) | 88% | 2 (84%) |
| Futures Exchanges (Licensing & Operations) Regulations, 2017 (`futures-exchanges-regulations-2017`) | 89% | 18 (80%), 2 (80%), 14 (81%), 6 (84%) |
| Joint Inspection Regulations, 2015 (`joint-inspection-regulations-2015`) | 89% | 4 (74%), 10 (77%), 5 (80%), 6 (82%) |
| Issue of Commercial Papers Regulations, 2013 (`commercial-papers-regulations-2013`) | 89% | 18 (43%), 10 (84%) |
| Futures Brokers (Licensing and Operations) Regulations, 2018 (`futures-brokers-regulations-2018`) | 89% | 18 (67%), 5 (73%), 4A (78%), 32 (79%), 27 (80%), 4 (84%), 14 (84%) |
| Listed Companies (Buy-back of Shares) Regulations, 2019 (`listed-companies-buy-back-regulations-2019`) | 89% | 8 (70%), 2 (74%), 3 (83%), 12 (83%) |
| Public Offering (Regulated Securities Activities Licensing) Regulations, 2017 (`public-offering-regulated-securities-licensing-regulations-2017`) | 89% | 3 (65%), 11 (83%) |
| Employees Contributory Funds (Investment in Listed Securities) Regulations, 2018 (`employees-contributory-funds-investment-regulations-2018`) | 89% | 6 (83%) |
| Centralized Know Your Customer (KYC) Organization Rules, 2017 (`centralized-kyc-organization-rules-2017`) | 90% | 6 (81%), 9 (81%), 13 (84%), 14 (84%) |
| Corporate Rehabilitation Regulations, 2019 (`corporate-rehabilitation-regulations-2019`) | 90% | 3 (74%) |
| Share Registrars and Balloters Regulations, 2017 (`share-registrars-balloters-regulations-2017`) | 90% | 4 (80%) |
| Public Sector Companies (Corporate Governance) Rules, 2013 (`public-sector-companies-cg-rules-2013`) | 90% | 6 (83%), 3A (84%), 16 (84%) |
| Panel of Provisional Managers and Official Liquidators Regulations, 2019 (`panel-provisional-managers-liquidators-regulations-2019`) | 90% | 6 (83%) |
| Securities Managers (Licensing and Operations) Regulations, 2024 (`securities-managers-regulations-2024`) | 90% | 25 (78%), 10 (81%), 14 (85%) |
| Limited Liability Partnership Regulations, 2018 (`llp-regulations-2018`) | 90% | 30 (25%), 4 (58%), 10 (65%), 1 (69%), 12 (75%), 18 (81%), 19 (82%), 16 (83%), 2 (85%) |
| Reporting and Disclosure (of Shareholding by Directors, Executive Officers and Substantial Shareholders in Listed Companies) Regulations, 2015 (`reporting-disclosure-regulations-2015`) | 90% | 2 (75%) |
| Corporate Restructuring Companies Rules, 2019 (`corporate-restructuring-companies-rules-2019`) | 91% | 11 (56%) |
| Professional Clearing Members Regulations, 2020 (`professional-clearing-members-regulations-2020`) | 91% | 19 (43%), 18 (73%), 14 (79%), 11 (85%) |
| Central Depository Companies (Establishment and Regulation) Rules, 1996 (`cdc-establishment-regulation-rules-1996`) | 91% | 1 (83%) |
| Securities and Futures Advisers (licensing and Operations) Regulations, 2017 (`securities-futures-advisers-regulations-2017`) | 91% | 21 (68%), 15 (80%) |
| Private Placement of Securities Rules, 2017 (`private-placement-rules-2017`) | 91% | 3 (72%) |
| Opportunity of Hearing Regulations, 2016 (`opportunity-of-hearing-regulations-2016`) | 91% | 2 (62%) |
| Companies (Appointment of Legal Adviser) Rules, 1975 (`companies-legal-adviser-rules-1975`) | 92% | none |
| Securities and Exchange Commission (Reinsurance Brokers) Regulations, 2021 (`reinsurance-brokers-regulations-2021`) | 92% | 20 (60%), 2 (83%) |
| Collateral Management Companies (Establishment & Operations) Regulations, 2017 (`cmc-regulations-2017`) | 92% | 10 (75%), 19 (80%), 14 (82%), 2 (83%) |
| Foreign Companies Regulations, 2018 (`foreign-companies-regulations-2018`) | 92% | 6 (63%), 14 (79%) |
| Issuance of Convertible Debt Securities through Right Offer Regulations, 2022 (`convertible-debt-right-offer-regulations-2022`) | 92% | none |
| Customers Compensation Fund (Establishment and Operation) Rules, 2017 (`customer-compensation-fund-rules-2017`) | 92% | 4 (73%) |
| Research Analyst Regulations, 2015 (`research-analyst-regulations-2015`) | 92% | 11 (80%), 12 (80%), 2C (83%) |
| Securities and Exchange Rules, 1971 (`securities-exchange-rules-1971`) | 93% | 6 (77%), 16 (81%) |
| Obligations under Voluntary Winding-up Regulations, 2016 (`voluntary-winding-up-obligations-regulations-2016`) | 93% | none |
| Secured Transactions Registry Regulations, 2020 (`secured-transactions-registry-regulations-2020`) | 93% | 14 (50%), 6 (82%) |
| Auditors (Reporting Obligations) Regulations, 2018 (`auditors-reporting-obligations-regulations-2018`) | 94% | none |
| Corporate Rehabilitation Act, 2018 (`corporate-rehabilitation-act-2018`) | 94% | 26 (78%), 42 (82%) |
| Securities (Leveraged Markets and Pledging) Rules, 2011 (`leveraged-markets-pledging-rules-2011`) | 95% | 1 (73%), 21 (80%) |
| Companies (Invitation and Acceptance of Deposit) Rules, 1987 (`companies-deposit-rules-1987`) | 97% | none |
