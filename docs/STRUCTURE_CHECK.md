# Structure check of the converted instruments

`python3 tools/ocr/structure_check.py`: places where the text's own structure suggests the OCR dropped a line (a gap in a list of labels, unbalanced brackets, a reference past the last provision). Leads to re-read against the scan, not proof of error.

307 leads in 38 instruments.

| Instrument | Provision | Lead | Text |
|---|---|---|---|
| listed-companies-buy-back-regulations-2019 | 2 | list jumps from (b) to (e): (c) may be missing | >(e) "public announcement" means an announcement made by the purchasin |
| listed-companies-buy-back-regulations-2019 | 4 | list jumps from (3) to (5): (4) may be missing | (5) The authorized officer shall, within fifteen days of the closing o |
| listed-companies-buy-back-regulations-2019 | 6 | list jumps from (b) to (d): (c) may be missing | >(d) the purchasing company shall ensure that sufficient funds are ava |
| listed-companies-buy-back-regulations-2019 | 6 | list jumps from (d) to (f): (e) may be missing | >(f) The shares purchased on daily basis shall be placed in the blocke |
| listed-companies-buy-back-regulations-2019 | 10 | list jumps from (b) to (f): (c) may be missing | >(f) submit to the Commission and the securities exchange, the publish |
| listed-companies-buy-back-regulations-2019 | 13 | unbalanced round brackets (3 open, 2 closed) | >(b) 2(Sell the treasury shares to its employees under section 83A of  |
| employees-contributory-funds-investment-regulations-2018 | 2 | list jumps from (b) to (d): (c) may be missing | >(d) "Fund" means a provident fund or any other contributory retiremen |
| employees-contributory-funds-investment-regulations-2018 | 3 | unbalanced round brackets (4 open, 3 closed) | (9) Total investment, at the time of making investment in any single e |
| public-sector-companies-cg-rules-2013 | 2 | unbalanced round brackets (2 open, 1 closed) | managerial nature; [(f) "Act" means the Companies Act, 2017 (XIX of 20 |
| public-sector-companies-cg-rules-2013 | 2 | list jumps from (e) to (g): (f) may be missing | >(g) "Public Sector Company" means a company, whether public or privat |
| public-sector-companies-cg-rules-2013 | 3 | list jumps from (3) to (5): (4) may be missing | (5) No Person shall be elected or nominated as a director of more than |
| public-sector-companies-cg-rules-2013 | 3A | unbalanced round brackets (2 open, 1 closed) | (1) A director, once appointed or elected under 6(section 161 or secti |
| public-sector-companies-cg-rules-2013 | 3A | list jumps from (1) to (3): (2) may be missing | (3) A director nominated by the Government shall hold office in accord |
| public-sector-companies-cg-rules-2013 | 5 | list jumps from (a) to (c): (b) may be missing | >(c) the identification and monitoring of the principal risks and |
| public-sector-companies-cg-rules-2013 | 5 | list jumps from (1) to (8): (2) may be missing | (8) Any service delivered or goods sold by a Public Sector Company as  |
| public-sector-companies-cg-rules-2013 | 7 | list jumps from (g) to (j): (h) may be missing | >(j) Policies related to the award of contracts and purchase and sale  |
| public-sector-companies-cg-rules-2013 | 17 | list jumps from (6) to (viii): (vii) may be missing | >(viii) shareholders holding five percent or more voting rights in the |
| public-sector-companies-cg-rules-2013 | 21 | list jumps from (a) to (c): (b) may be missing | >(c) review of quarterly, half-yearly and annual financial statements  |
| public-sector-companies-cg-rules-2013 | 21 | list jumps from (f) to (h): (g) may be missing | >(h) consideration of major findings of internal investigations and |
| public-sector-companies-cg-rules-2013 | 21 | list jumps from (n) to (p): (o) may be missing | >(p) consideration of any ether issue or matter as may be assigned by  |
| public-sector-companies-cg-rules-2013 | 21 | list jumps from (1) to (7): (2) may be missing | (7) The audit committee shall be responsible for managing the relation |
| foreign-companies-regulations-2018 | 2 | list jumps from (2) to (iv): (iii) may be missing | >(iv) "Commission" means the Securities and Exchange Commission of Pak |
| foreign-companies-regulations-2018 | 6 | unbalanced round brackets (2 open, 1 closed) | Provided that the registrar may refuse to register the documents for i |
| foreign-companies-regulations-2018 | 12 | list jumps from (2) to (iv): (iii) may be missing | >(iv) in case of manual application, it shall be in printed form setti |
| companies-independent-directors-regulations-2018 | 3 | unbalanced round brackets (0 open, 1 closed) | h) educational and professional qualifications; |
| companies-independent-directors-regulations-2018 | 3 | unbalanced round brackets (0 open, 1 closed) | i) experience or expertise or specialized skill; |
| companies-independent-directors-regulations-2018 | 3 | unbalanced round brackets (0 open, 1 closed) | j) region/city in which the professional is serving currently; |
| companies-independent-directors-regulations-2018 | 3 | unbalanced round brackets (0 open, 1 closed) | k) list of companies in which directorship is / was held; |
| companies-independent-directors-regulations-2018 | 3 | unbalanced round brackets (1 open, 2 closed) | I) nature of directorship held (executive, non-executive, independent) |
| companies-independent-directors-regulations-2018 | 3 | unbalanced round brackets (1 open, 2 closed) | m) details of directors' training program (DTP) attended or exemption  |
| companies-independent-directors-regulations-2018 | 4 | unbalanced round brackets (0 open, 1 closed) | i) either holds at least a graduate degree from a university recognize |
| companies-independent-directors-regulations-2018 | 4 | unbalanced round brackets (0 open, 1 closed) | a) established in Pakistan, governed under a special enactment of the  |
| companies-independent-directors-regulations-2018 | 4 | unbalanced round brackets (0 open, 1 closed) | b) established outside Pakistan and established under a special enactm |
| companies-independent-directors-regulations-2018 | 4 | unbalanced round brackets (0 open, 1 closed) | ii) has at least five years of relevant experience in one or more of t |
| companies-independent-directors-regulations-2018 | 4 | unbalanced round brackets (1 open, 3 closed) | a) Name of Director b) CNIC/Passport No. (if available) |
| companies-independent-directors-regulations-2018 | 4 | unbalanced round brackets (1 open, 3 closed) | c) Year of completion of DTP d) Email address (if available) |
| companies-easy-exit-regulations-2014 | 1 | list jumps from (a) to (c): (b) may be missing | >(c) foreign companies; |
| companies-easy-exit-regulations-2014 | 3 | unbalanced round brackets (3 open, 4 closed) | 1(3) Where an application received under sub-regulation (1), is made b |
| companies-mediation-conciliation-regulations-2018 | 10 | list jumps from (1) to (iii): (ii) may be missing | >(iii) he shall hold the mediation and conciliation at the place decid |
| share-registrars-balloters-regulations-2017 | 2 | list jumps from (3) to (vi): (iv) may be missing | >(vi) resolution of investors' complaints; and |
| share-registrars-balloters-regulations-2017 | 9 | list jumps from (d) to (f): (e) may be missing | >(f) to maintain record of the allotment, transfer and transmission of |
| share-registrars-balloters-regulations-2017 | 10 | list jumps from (u) to (w): (v) may be missing | >(w) give to the Commission under section 73 of the Act. notice of cea |
| share-registrars-balloters-regulations-2017 | 15 | list jumps from (i) to (k): (j) may be missing | >(k) detail of unclaimed dividend and undelivered securities; |
| share-registrars-balloters-regulations-2017 | 15 | list jumps from (k) to (m): (l) may be missing | >(m): such other records as may be required by the Commission to be ma |
| auditors-reporting-obligations-regulations-2018 | 2 | unbalanced round brackets (4 open, 3 closed) | >(vii) "review report" means a report given by the auditor of a compan |
| auditors-reporting-obligations-regulations-2018 | 2 | list jumps from (7) to (x): (viii) may be missing | >(x) "Futures Broker" for the purpose of these regulations shall have  |
| auditors-reporting-obligations-regulations-2018 | 2 | unbalanced round brackets (2 open, 1 closed) | >(x) "Futures Broker" for the purpose of these regulations shall have  |
| auditors-reporting-obligations-regulations-2018 | 3 | refers to regulation 23, but the instrument ends at 8 | (3) The auditor of an insurer registered under the Insurance Ordinance |
| listed-companies-takeovers-regulations-2017 | 6 | list jumps from (a) to (c): (b) may be missing | >(c) starts raising funds; or |
| listed-companies-takeovers-regulations-2017 | 13 | list jumps from (a) to (c): (b) may be missing | >(c) the weighted average share price of target company on the securit |
| listed-companies-takeovers-regulations-2017 | 21 | unbalanced round brackets (2 open, 1 closed) | >(e) the time period for making the public announcement of [public] of |
| listed-companies-takeovers-regulations-2017 | 22 | list jumps from (a) to (c): (b) may be missing | >(c) the acquirer has been declared by a Court of competent jurisdicti |
| listed-companies-takeovers-regulations-2017 | 26 | list jumps from (b) to (d): (c) may be missing | >(d) ensure that firm arrangements for funds and money have been made  |
| listed-companies-takeovers-regulations-2017 | 26 | list jumps from (e) to (g): (f) may be missing | >(g) ensure that the contents of the public announcement and [public]  |
| sukuk-privately-placed-regulations-2017 | 2 | list jumps from (e) to (g): (f) may be missing | >(g) "Qualified Institutional Buyer (QIB)" means any institution that  |
| companies-deposit-rules-1987 | 2 | list jumps from (b) to (d): (c) may be missing | >(d) "form" means a form annexed to these rules; |
| companies-deposit-rules-1987 | 3 | unbalanced round brackets (0 open, 1 closed) | [G) amount received by way 'of security or an advance from any purchas |
| companies-deposit-rules-1987 | 3 | list jumps from (i) to (k): (j) may be missing | >(k) amount received from an employee by way of security deposit or |
| companies-deposit-rules-1987 | 5 | unbalanced round brackets (1 open, 2 closed) | >(c) it contains a promise for a gift or reward or some unusual incent |
| companies-deposit-rules-1987 | 7 | list jumps from (a) to (c): (b) may be missing | >(c) Where a public company intends to accept deposits without issuing |
| opportunity-of-hearing-regulations-2016 | 3 | list jumps from (3) to (v): (iv) may be missing | >(v) date, place and time of hearing and deadline within which the wri |
| opportunity-of-hearing-regulations-2016 | 3 | list jumps from (6) to (viii): (vii) may be missing | >(viii) Any other relevant information. |
| voluntary-winding-up-obligations-regulations-2016 | 4 | list jumps from (d) to (f): (e) may be missing | >(f) Any other matter relating to protection of interest of the custom |
| voluntary-winding-up-obligations-regulations-2016 | 5 | list jumps from (2) to (4): (3) may be missing | (4) the central depository shall, on receipt of the resolution or as s |
| convertible-debt-right-offer-regulations-2022 | 2 | list jumps from (2) to (iv): (iii) may be missing | >(iv) "listed company" means a public limited company whose shares are |
| convertible-debt-right-offer-regulations-2022 | 3 | list jumps from (10) to (xii): (xi) may be missing | >(xii). letter of offer shall state number of convertible debt securit |
| convertible-debt-right-offer-regulations-2022 | 4 | list jumps from (1) to (iii): (ii) may be missing | >(iii) the company shall obtain prior requisite approval under section |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (1 open, 2 closed) | a) "Act" means the Securities Act, 2015 (Act No. III of 2015); |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (2 open, 3 closed) | [b) "Close relative" means the spouse(s), lineal ascendant(s) and |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (1 open, 2 closed) | c) "Commission" means the Securities and Exchange Commission of Pakist |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | [ca) "head of research" means a person, by whatever name called, who i |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | [da) "individual" means any natural person granted a certificate of re |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | db) "persons associated with research' analyst" includes any officer,  |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | dc) "target date" means a date on which the predicted future price of  |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (1 open, 2 closed) | dd) "target price" means a predicted future price of a specific listed |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | interactive electronic forum, electronic communication and social medi |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 2 closed) | Provided that one-to-one calls to a single client shall not be conside |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | i). comments on general trends in the securities market; |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | ii). commentaries on economic, political or market conditions; |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | iii). periodic reports or other communications prepared for unit holde |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | iv). internal communications that are not given to current or |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | v). communications that constitute offer documents or prospectus that  |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | vi). statistical summaries of financial data of the companies; |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | vii). general commentary relating to the past performance of a sector  |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 2 closed) | viii). any other communication which the Commission may specify from t |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | i). making 'buy/sell/hold' recommendation; |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | iv). providing opinion to influence buy/sell/hold decisions; |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | v). recommending a portfolio that includes listed securities; |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 1 closed) | vi). providing trading signals based on technical analysis; or |
| research-analyst-regulations-2015 | 2 | unbalanced round brackets (0 open, 4 closed) | vii). any other service as specified by the Commission;] [i) "subject  |
| joint-inspection-regulations-2015 | 2 | list jumps from (i) to (k): (j) may be missing | >(k) "Days" wherever used means calendar days; |
| joint-inspection-regulations-2015 | 2 | list jumps from (n) to (p): (o) may be missing | >(p) "Inspection Report" means the Inspection Report submitted by the  |
| joint-inspection-regulations-2015 | 2 | list jumps from (u) to (w): (v) may be missing | >(w) "Non-Broker Clearing Member" shall have the same meaning as ascri |
| joint-inspection-regulations-2015 | 2 | list jumps from (5) to (x): (vi) may be missing | >(x) "Ordinance" means Securities and Exchange Ordinance, 1969; |
| joint-inspection-regulations-2015 | 2 | list jumps from (w) to (y): (x) may be missing | >(y) "Oversight Committee" means a Committee constituted under these r |
| joint-inspection-regulations-2015 | 14 | list jumps from (3) to (5): (4) may be missing | (5) The Oversight Committee shall issue Inspection notice at least sev |
| joint-inspection-regulations-2015 | 19 | list jumps from (e) to (g): (f) may be missing | >(g) ensure timely execution of the quarterly Inspection plan during i |
| joint-inspection-regulations-2015 | 19 | list jumps from (k) to (m): (l) may be missing | >(m) provide its comments, if any, on observations / recommendations g |
| joint-inspection-regulations-2015 | 19 | list jumps from (u) to (w): (v) may be missing | >(w) form sub-committee(s) for performing any role or functions relati |
| joint-inspection-regulations-2015 | 19 | list jumps from (5) to (x): (vi) may be missing | >(x) submit status report to the Commission on joint inspection on qua |
| joint-inspection-regulations-2015 | 19 | list jumps from (w) to (y): (x) may be missing | >(y) ensure confidentiality of available data, information/details per |
| joint-inspection-regulations-2015 | 21 | list jumps from (2) to (4): (3) may be missing | (4) Where the inspector/Inspection Team appointed under these Regulati |
| credit-rating-companies-regulations-2016 | 2 | list jumps from (e) to (h): (f) may be missing | >(h) "promoter or sponsor" means a person who has made an application  |
| credit-rating-companies-regulations-2016 | 2 | list jumps from (i) to (k): (j) may be missing | >(k) "Un-solicited Ratings" means a rating not initiated at the reques |
| credit-rating-companies-regulations-2016 | 4 | list jumps from (a) to (c): (b) may be missing | >(c) meets the financial resources requirement provided under these re |
| credit-rating-companies-regulations-2016 | 6 | list jumps from (d) to (g): (e) may be missing | >(g) all persons subject to fit and proper criteria shall submit an af |
| credit-rating-companies-regulations-2016 | 10 | list jumps from (1) to (iii): (ii) may be missing | >(iii) a licensed securities exchange; or |
| credit-rating-companies-regulations-2016 | 10 | list jumps from (4) to (6): (5) may be missing | (6) A proposed director, chairman or chief executive of the credit rat |
| credit-rating-companies-regulations-2016 | 10 | list jumps from (e) to (g): (f) may be missing | >(g) make unsubstantiated claims, in order to induce customers, about  |
| credit-rating-companies-regulations-2016 | 10 | unbalanced round brackets (6 open, 7 closed) | >(iii) both the credit rating companies (existing and newly engaged) s |
| credit-rating-companies-regulations-2016 | 11 | list jumps from (a) to (c): (b) may be missing | >(c) employ analysts who meet the fit and proper criteria annexed as A |
| credit-rating-companies-regulations-2016 | 11 | list jumps from (f) to (h): (g) may be missing | >(h) ensure that the criterion for constitution of the rating committe |
| credit-rating-companies-regulations-2016 | 11 | list jumps from (i) to (m): (j) may be missing | >(m) engage with the issuer and the debt securities trustee, to remain |
| credit-rating-companies-regulations-2016 | 11 | list jumps from (k) to (m): (l) may be missing | >(m) promptly investigate, in the event of a misconduct or a breach of |
| credit-rating-companies-regulations-2016 | 11 | list jumps from (d) to (f): (e) may be missing | >(f) ensure that the members of rating committee including external me |
| credit-rating-companies-regulations-2016 | 11 | list jumps from (n) to (p): (o) may be missing | >(p) ensure that record of all ratings whether active, withdrawn or ma |
| credit-rating-companies-regulations-2016 | 12 | list jumps from (b) to (d): (c) may be missing | >(d) The chairman of the board of directors of a credit rating company |
| credit-rating-companies-regulations-2016 | 12 | list jumps from (i) to (k): (j) may be missing | >(k) the analysts and members of the rating committee including the ex |
| credit-rating-companies-regulations-2016 | 14 | list jumps from (7) to (x): (viii) may be missing | >(x) a statement by the analysts that rating is just an opinion about  |
| credit-rating-companies-regulations-2016 | 17 | list jumps from (a) to (c): (b) may be missing | >(c) initiate immediate review of the outstanding rating upon becoming |
| credit-rating-companies-regulations-2016 | 21 | list jumps from (2) to (iv): (iii) may be missing | >(iv) minutes of the meetings of the rating committee, deliberations a |
| credit-rating-companies-regulations-2016 | 26 | unbalanced round brackets (3 open, 4 closed) | (1) Save as provided in Regulation 26(2), the Credit Rating Companies  |
| securities-futures-advisers-regulations-2017 | 2 | unbalanced round brackets (2 open, 1 closed) | [(c) "Futures Act" means the Futures Market Act, 2016 (as amended or |
| securities-futures-advisers-regulations-2017 | 2 | list jumps from (f) to (j): (g) may be missing | >(j) "Futures Adviser" means a person, who- |
| securities-futures-advisers-regulations-2017 | 2 | list jumps from (b) to (k): (c) may be missing | >(k) "Securities Adviser" means a person, who- |
| securities-futures-advisers-regulations-2017 | 3 | unbalanced round brackets (4 open, 3 closed) | i(Provided that in terms of section 2(liii)(III) of the Securities Act |
| securities-futures-advisers-regulations-2017 | 3 | list jumps from (b) to (f): (c) may be missing | >(f) the NBFC shall be subject to disciplinary action under the Securi |
| securities-futures-advisers-regulations-2017 | 4 | list jumps from (a) to (c): (b) may be missing | >(c) Such other company as may be notified by the Commission [; or] [( |
| securities-futures-advisers-regulations-2017 | 4 | list jumps from (a) to (c): (b) may be missing | >(c) it, its sponsors, directors and senior management officers shall  |
| securities-futures-advisers-regulations-2017 | 4 | list jumps from (c) to (f): (d) may be missing | >(f) it meets the financial resource requirements as specified in thes |
| securities-futures-advisers-regulations-2017 | 10 | unbalanced round brackets (1 open, 2 closed) | (3) The Commission may cancel the licence granted to a securities advi |
| securities-futures-advisers-regulations-2017 | 11 | unbalanced round brackets (0 open, 1 closed) | a) it does not'make unsubstantiated claims, in order to induce custome |
| securities-futures-advisers-regulations-2017 | 11 | unbalanced round brackets (0 open, 1 closed) | b) it does not get involved in unfair competitive practices, nor shall |
| securities-futures-advisers-regulations-2017 | 11 | unbalanced round brackets (0 open, 1 closed) | c) it does not publish, circulate or distribute any advertisement or a |
| securities-futures-advisers-regulations-2017 | 11 | unbalanced round brackets (0 open, 1 closed) | d) any advertisement is written in dear language and is not such which |
| securities-futures-advisers-regulations-2017 | 11 | unbalanced round brackets (0 open, 1 closed) | e) it does not make any exaggerated statements regarding its capabilit |
| securities-futures-advisers-regulations-2017 | 11 | unbalanced round brackets (0 open, 1 closed) | f) it does not willfully make false statements or conceal any material |
| securities-futures-advisers-regulations-2017 | 11 | unbalanced round brackets (0 open, 1 closed) | g) it maintains principle of integrity in seeking business. |
| securities-futures-advisers-regulations-2017 | 12 | unbalanced round brackets (0 open, 1 closed) | i) Name of the customer and the securities adviser or futures adviser; |
| securities-futures-advisers-regulations-2017 | 12 | unbalanced round brackets (0 open, 1 closed) | ii) Terms and conditions on which the securities or futures advisory s |
| securities-futures-advisers-regulations-2017 | 12 | unbalanced round brackets (0 open, 1 closed) | iii) Affiliations. with other licenced persons and intermediaries in t |
| securities-futures-advisers-regulations-2017 | 12 | unbalanced round brackets (0 open, 1 closed) | iv) Conditions, under which agreement may be altered, terminated and |
| securities-futures-advisers-regulations-2017 | 12 | unbalanced round brackets (0 open, 1 closed) | a) Voluntary/mandatory termination, by the securities adviser or |
| securities-futures-advisers-regulations-2017 | 12 | unbalanced round brackets (0 open, 1 closed) | •b) Voluntary/mandatory termination by the customer; and |
| securities-futures-advisers-regulations-2017 | 12 | unbalanced round brackets (0 open, 1 closed) | v) liability of the securities adviser or futures adviser in connectio |
| securities-futures-advisers-regulations-2017 | 12 | unbalanced round brackets (0 open, 1 closed) | vi) Quantum and manner of fees payable by the customer. |
| securities-futures-advisers-regulations-2017 | 15 | unbalanced round brackets (1 open, 0 closed) | (f information provided by customers and their risk assessment is upda |
| securities-futures-advisers-regulations-2017 | 16 | unbalanced round brackets (2 open, 1 closed) | "((f) It acts diligently and carefully in providing any advice and its |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | a) on introduction to a prospective customer, disclose that the securi |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | b) maintain high standards of integrity,promptitude, fairness and act  |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | c) in case of a securities adviser providing advice in respect of CIS, |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | i) not involve either directly or indirectly in the mis-selling of CIS |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | ii) only deal in units at the unit price quoted by the respective AMC  |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | iii) avoid making negative statements about any AMC or CIS, NPF and en |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | iv) provide full and latest information of schemes to customers in the |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | v) avoid commission-driven malpractices such as encouraging over- |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | vi) adhere to these regulations and any other regulations, circulars o |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | d) in case of a securities adviser providing advice in respect of CIS/ |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (2 open, 3 closed) | >(vi) the tax implications (if any). o/?[e) in case securities adviser |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | f) unless it complies with the applicable framework for research analy |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | g) ensure that any performance reporting/presentation is accompanied b |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | h) ensure compliance with all legal and regulatory requirements applic |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | i) have and employ effectively appropriate resources and procedures wh |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | j) in case of a company engaged in other regulated activities as well, |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | k) ensure that channels of communications are properly documented and |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | 1) maintain complete file of each customer and not change any detail p |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | m) ensure that the Commission is informed, without undue delay, of ser |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | n) put in place a mechanism for proper and timely handling of any cust |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | 0) determine the true identity of the prospective customer before exte |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | q) remain in compliance with the licensing requirements at all times a |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | r) ensure that any written or electronic communication or corresponden |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | s) shall ensure that fees charged to the customers are fair and reason |
| securities-futures-advisers-regulations-2017 | 18 | unbalanced round brackets (0 open, 1 closed) | t) submit any document, report or information as and when required by  |
| securities-futures-advisers-regulations-2017 | 18 | list jumps from (6) to (x): (vii) may be missing | >(x) in case distribution services are provided through digital means, |
| securities-futures-advisers-regulations-2017 | 18 | list jumps from (u) to (y): (v) may be missing | >(y) in case any services are provided through digital means, ensure t |
| securities-futures-advisers-regulations-2017 | 20 | unbalanced round brackets (0 open, 1 closed) | a) All written agreements entered into by the securities adviser or fu |
| securities-futures-advisers-regulations-2017 | 20 | unbalanced round brackets (0 open, 1 closed) | b) Know Your Client records of the customer; |
| securities-futures-advisers-regulations-2017 | 20 | unbalanced round brackets (0 open, 1 closed) | c) Risk profiling and risk assessment of the customer; |
| securities-futures-advisers-regulations-2017 | 20 | unbalanced round brackets (0 open, 1 closed) | d) Rationale for arriving at investment advice and assessment of its s |
| securities-futures-advisers-regulations-2017 | 20 | unbalanced round brackets (0 open, 1 closed) | e) A register or record containing list of the customers, the date of  |
| securities-futures-advisers-regulations-2017 | 20 | unbalanced round brackets (0 open, 1 closed) | f) Records of trading in securities and futures contracts by the secur |
| securities-futures-advisers-regulations-2017 | 21 | unbalanced round brackets (1 open, 2 closed) | (1) In case of a company, a securities adviser [and/) or futures advis |
| securities-futures-advisers-regulations-2017 | 22 | unbalanced round brackets (0 open, 1 closed) | In case of company, a securities adviser [and/] or futures adviser sha |
| public-offering-regulated-securities-licensing-regulations-2017 | 2 | list jumps from (a) to (c): (b) may be missing | >(c) block the bid money and subscription money in the respective acco |
| public-offering-regulated-securities-licensing-regulations-2017 | 2 | list jumps from (2) to (vi): (iii) may be missing | >(vi) "form" means a form annexed to these Regulations; |
| public-offering-regulated-securities-licensing-regulations-2017 | 6 | list jumps from (d) to (f): (e) may be missing | >(f) |
| public-offering-regulated-securities-licensing-regulations-2017 | 6 | list jumps from (f) to (j): (g) may be missing | >(j) any other matter as is deemed necessary by the Commission. |
| public-offering-regulated-securities-licensing-regulations-2017 | 9 | unbalanced round brackets (2 open, 1 closed) | A banker to an issue, consultant to the issue, Debt Securities Trustee |
| public-offering-regulated-securities-licensing-regulations-2017 | 12 | unbalanced round brackets (2 open, 1 closed) | Provided that a scheduled bank already licensed as an underwriter or a |
| centralized-kyc-organization-rules-2017 | 9 | list jumps from (b) to (d): (c) may be missing | >(d) perform independent verification process for KYC information prov |
| centralized-kyc-organization-rules-2017 | 9 | list jumps from (h) to (j): (i) may be missing | >(j) ensure safeguards for maintaining data privacy for and prevent un |
| centralized-kyc-organization-rules-2017 | 9 | list jumps from (5) to (vii): (vi) may be missing | >(vii) actions to be taken by the centralized KYC organization in case |
| centralized-kyc-organization-rules-2017 | 9 | list jumps from (9) to (xi): (x) may be missing | >(xi) responsibilities and obligations for authorized intermediaries; |
| customer-compensation-fund-rules-2017 | 8 | list jumps from (3) to (5): (4) may be missing | (5) The appointment of a trustee may be cancelled in case he becomes n |
| centralized-customer-protection-compensation-fund-regulations-2017 | 2 | unbalanced round brackets (5 open, 4 closed) | >(b) "demutualization regulations" means the Stock Exchanges (Corporat |
| centralized-customer-protection-compensation-fund-regulations-2017 | 6 | list jumps from (1) to (3): (2) may be missing | (3) If the total amount of admitted claims is less than the amount rea |
| cmc-regulations-2017 | 2 | list jumps from (c) to (e): (d) may be missing | >(e) "Commission" means the Securities and Exchange Commission of Paki |
| cmc-regulations-2017 | 2 | list jumps from (h) to (j): (i) may be missing | >(j) "NBFC Rules" means the Non-Banking Finance Companies (Establishme |
| cmc-regulations-2017 | 2 | unbalanced round brackets (2 open, 1 closed) | >(i) means produce of farmers, arising from agriculture (including ani |
| cmc-regulations-2017 | 2 | unbalanced round brackets (0 open, 1 closed) | farming plantation products), or from any other activity or service wh |
| cmc-regulations-2017 | 5 | list jumps from (b) to (d): (c) may be missing | >(d) maintain high standard of integrity and fairness in discharging i |
| cmc-regulations-2017 | 5 | list jumps from (1) to (iii): (ii) may be missing | >(iii) the Warehouse is equipped with all the necessary equipment and |
| cmc-regulations-2017 | 24 | list jumps from (k) to (m): (l) may be missing | >(m) date and signature of the Warehouse Operator or his authorized ag |
| futures-exchanges-regulations-2017 | 5 | unbalanced round brackets (0 open, 1 closed) | g) have documented business continuity plan including a disaster recov |
| futures-exchanges-regulations-2017 | 5 | list jumps from (f) to (h): (g) may be missing | >(h) continuously improve the quality and efficiency of its systems an |
| futures-exchanges-regulations-2017 | 5 | list jumps from (1) to (iii): (ii) may be missing | >(iii) effective surveillance capability to inter alia monitor positio |
| futures-exchanges-regulations-2017 | 5 | list jumps from (3) to (v): (iv) may be missing | >(v) submit a plan for segregation of commercial and regulatory functi |
| futures-exchanges-regulations-2017 | 5 | list jumps from (u) to (w): (v) may be missing | >(w) constitute a nomination committee, chaired by an independent dire |
| futures-exchanges-regulations-2017 | 5 | list jumps from (5) to (x): (vi) may be missing | >(x) prescribe a code of conduct for its employees and ensure complian |
| futures-exchanges-regulations-2017 | 5 | list jumps from (w) to (y): (x) may be missing | (y) not undertake any business other than the business of establishing |
| futures-exchanges-regulations-2017 | 12 | list jumps from (d) to (f): (e) may be missing | >(f) monitor the redressal of disputes, complaints or grievances arisi |
| futures-exchanges-regulations-2017 | 13 | unbalanced round brackets (1 open, 2 closed) | (4) The risk committee shall be responsible for the following: *it see |
| futures-exchanges-regulations-2017 | 13 | unbalanced round brackets (0 open, 1 closed) | b) ensuring that the risk management system has the tools to identify  |
| futures-exchanges-regulations-2017 | 13 | unbalanced round brackets (0 open, 1 closed) | d) ensuring that the risk management function has the capacity to obta |
| futures-exchanges-regulations-2017 | 13 | unbalanced round brackets (0 open, 1 closed) | e) conducting or arranging to conduct studies, research, or analyses w |
| futures-exchanges-regulations-2017 | 13 | unbalanced round brackets (0 open, 1 closed) | f) formulating policies and procedures to ensure continuous adequacy o |
| futures-exchanges-regulations-2017 | 13 | unbalanced round brackets (0 open, 1 closed) | g) formulating policies for ensuring that a full validation of risk ma |
| futures-exchanges-regulations-2017 | 13 | unbalanced round brackets (0 open, 1 closed) | h) to meet at least once in each quarter to review adequacy of risk ma |
| futures-exchanges-regulations-2017 | 13 | unbalanced round brackets (1 open, 2 closed) | i) to submit its recommendation(s) to the board of directors together  |
| futures-exchanges-regulations-2017 | 16 | list jumps from (2) to (4): (3) may be missing | (4) The futures exchange shall be fully liable and accountable for the |
| futures-exchanges-regulations-2017 | 19 | list jumps from (4) to (6): (5) may be missing | (6) Where an auditor resigns or is removed by the futures exchange, a  |
| futures-exchanges-regulations-2017 | 22 | list jumps from (3) to (v): (iv) may be missing | >(v) maintain record of balances of each futures broker and customer,  |
| bond-pricing-agency-rules-2017 | 5 | list jumps from (1) to (C): (B) may be missing | (C) he has or has had within the last three years a material business  |
| bond-pricing-agency-rules-2017 | 5 | list jumps from (h) to (j): (i) may be missing | >(j) it complies with any other conditions as may be notified by the C |
| bond-pricing-agency-rules-2017 | 9 | list jumps from (2) to (4): (3) may be missing | (4) A bond pricing agency whose application for renewal of licence is  |
| bond-pricing-agency-rules-2017 | 10 | list jumps from (1) to (iii): (ii) may be missing | >(iii) it must undertake to disclose, to the extent possible, the broa |
| bond-pricing-agency-rules-2017 | 10 | list jumps from (3) to (v): (iv) may be missing | >(v) not provide false or misleading information to the Commission; |
| bond-pricing-agency-rules-2017 | 10 | list jumps from (u) to (w): (v) may be missing | >(w) develop andsupport an ongoing market pricing review process that  |
| bond-pricing-agency-rules-2017 | 10 | list jumps from (5) to (x): (vi) may be missing | >(x) follow the code of corporate governance applicable on listed comp |
| bond-pricing-agency-rules-2017 | 10 | list jumps from (w) to (z): (x) may be missing | >(z) make adequate disclosures on its website, maintained and updated  |
| bond-pricing-agency-rules-2017 | 10 | list jumps from (7) to (ix): (viii) may be missing | >(ix) any other information as may be required by the Commission |
| llp-regulations-2018 | 14 | list jumps from (1) to (vi): (ii) may be missing | >(vi) Usual residential address (vii) Email address (viii) Date on whi |
| llp-regulations-2018 | 14 | list jumps from (6) to (xi): (vii) may be missing | >(xi). Any other information incidental to or relevant to enable the L |
| llp-regulations-2018 | 14 | list jumps from (3) to (5): (4) may be missing | (5) Every LLP required to maintain a register of ultimate beneficial o |
| llp-regulations-2018 | 18 | list jumps from (1) to (3): (2) may be missing | (3) The partners of a limited liability partnership may remove an audi |
| credit-suretyship-rules-2018 | 2 | list jumps from (d) to (f): (e) may be missing | >(f) "net exposure" under a guarantee means the guaranteed aggregate a |
| credit-suretyship-rules-2018 | 2 | unbalanced round brackets (2 open, 1 closed) | >(h) "Ordinance" means the Insurance Ordinance, 2000 (Ordinance No. |
| futures-brokers-regulations-2018 | 2 | list jumps from (d) to (f): (e) may be missing | >(f) "financail** instrument" shall have the same meaning as defined i |
| futures-brokers-regulations-2018 | 2 | list jumps from (c) to (o): (d) may be missing | >(o) "unique identification number (UIN)" means the unique identificat |
| futures-brokers-regulations-2018 | 4 | unbalanced round brackets (1 open, 0 closed) | i[Provided that a person holding a valid license to act as a Securitie |
| futures-brokers-regulations-2018 | 4 | unbalanced round brackets (0 open, 1 closed) | Operations) Regulations, 2016 may apply for license as a futures broke |
| futures-brokers-regulations-2018 | 4 | list jumps from (i) to (m): (j) may be missing | >(m) it meets the financial resource requirements specified in these r |
| futures-brokers-regulations-2018 | 6 | list jumps from (d) to (f): (e) may be missing | >(f) the past track record of regulatory compliance of the applicant,  |
| futures-brokers-regulations-2018 | 7 | list jumps from (2) to (7): (3) may be missing | (7) The net worth of a futures broker shall be calculated as total ass |
| futures-brokers-regulations-2018 | 16 | list jumps from (o) to (r): (p) may be missing | >(r) comply with the requirements prescribed by the futures exchange f |
| futures-brokers-regulations-2018 | 16 | list jumps from (1) to (3): (2) may be missing | (3) 3) A tutures broker shall which govern trading or investmen' in fu |
| futures-brokers-regulations-2018 | 16 | unbalanced round brackets (1 open, 2 closed) | (3) 3) A tutures broker shall which govern trading or investmen' in fu |
| futures-brokers-regulations-2018 | 21 | list jumps from (d) to (f): (e) may be missing | >(f) the price and total consideration; |
| futures-brokers-regulations-2018 | 26 | list jumps from (3) to (6): (4) may be missing | (6) A futures broker shall keep records of: |
| futures-brokers-regulations-2018 | 27 | list jumps from (1) to (3): (2) may be missing | (3) The compliance officer shall immediately report any non-compliance |
| futures-brokers-regulations-2018 | 29 | list jumps from (b) to (d): (c) may be missing | >(d) ledgers (or other comparable records) reflecting futures contract |
| futures-brokers-regulations-2018 | 29 | list jumps from (i) to (k): (j) may be missing | >(k) record of the time, date, and complete particulars of instruction |
| futures-brokers-regulations-2018 | 29 | list jumps from (1) to (6): (2) may be missing | (6) A futures broker shall intimate to the futures exchange and the Co |
| secured-transactions-registry-regulations-2020 | 4 | unbalanced round brackets (0 open, 1 closed) | a) information provided by the user under regulation 3; and |
| secured-transactions-registry-regulations-2020 | 4 | unbalanced round brackets (0 open, 1 closed) | b) history of all transactions made on behalf of the account, includin |
| secured-transactions-registry-regulations-2020 | 14 | list jumps from (1) to (3): (2) may be missing | (3), the register shall be available online for filings and searches 2 |
| oversight-regulations-accountants-2020 | 2 | unbalanced round brackets (1 open, 2 closed) | (1) For the purpose of this regulation: 1) In this Regulations, unless |
| oversight-regulations-accountants-2020 | 2 | unbalanced round brackets (0 open, 1 closed) | i) "Act" means Anti-Money Laundering Act, 2010. |
| oversight-regulations-accountants-2020 | 2 | unbalanced round brackets (0 open, 2 closed) | ii) The words and expression used but not defined in these regulations |
| oversight-regulations-accountants-2020 | 2 | unbalanced round brackets (0 open, 1 closed) | proprietor) or in partnership with chartered accountants. |
| oversight-regulations-accountants-2020 | 2 | unbalanced round brackets (5 open, 9 closed) | ii) Practicing as a "Management Consultant". 3) "Oversight Body" means |
| oversight-regulations-accountants-2020 | 2 | unbalanced round brackets (1 open, 2 closed) | i) Institute of Chartered Accountants of Pakistan (ICAP) |
| oversight-regulations-accountants-2020 | 2 | unbalanced round brackets (1 open, 2 closed) | ii) Institute of Cost and Management Accountants of Pakistan (ICMAP) |
| oversight-regulations-accountants-2020 | 3 | list jumps from (a) to (c): (b) may be missing | >(c) base the frequency and intensity of its on-site, off-site supervi |
| oversight-regulations-accountants-2020 | 3 | unbalanced round brackets (1 open, 2 closed) | its outreach activities on the risk profiles identified under clause ( |
| oversight-regulations-accountants-2020 | 3 | unbalanced round brackets (0 open, 2 closed) | i) Risk assessment, mitigation and applications of a risk- based appro |
| oversight-regulations-accountants-2020 | 3 | unbalanced round brackets (1 open, 8 closed) | a. Requirements to identify and verify customers, beneficial owners b. |
| oversight-regulations-accountants-2020 | 3 | unbalanced round brackets (1 open, 2 closed) | xi) Any other item as notified in the Act (b) apply suitable market en |
| oversight-regulations-accountants-2020 | 3 | list jumps from (a) to (c): (b) may be missing | >(c) provide adequate resources with the appropriate qualifications, i |
| oversight-regulations-accountants-2020 | 3 | list jumps from (e) to (g): (f) may be missing | >(g) apply effective, proportionate and dissuasive sanctions to its re |
| reinsurance-brokers-regulations-2021 | 14 | list jumps from (a) to (c): (b) may be missing | >(c) it has not commenced the business within six months of being gran |
| securities-managers-regulations-2024 | 10 | list jumps from (b) to (d): (c) may be missing | >(d) - it does not make unsubstantiated claims or exaggerated statemen |
| securities-managers-regulations-2024 | 10 | list jumps from (d) to (f): (e) may be missing | >(f) it does not get involved in unfair competitive practices, nor sha |
| securities-managers-regulations-2024 | 11 | unbalanced round brackets (2 open, 1 closed) | >(b) natúre and scope of services to be provided including functions,  |
| securities-managers-regulations-2024 | 11 | unbalanced round brackets (0 open, 1 closed) | discretionary management of portfolic to be given separately) with spe |
| securities-managers-regulations-2024 | 11 | list jumps from (f) to (h): (g) may be missing | >(h) details of the cuştodian arrangement after taking prior consent f |
| securities-managers-regulations-2024 | 11 | list jumps from (1) to (3): (2) may be missing | (3) Any change in terms of the agreement shall only be incorporated th |
| securities-managers-regulations-2024 | 14 | list jumps from (1) to (11): (2) may be missing | (11) price rigging or manipulation of securities; |
| securities-managers-regulations-2024 | 14 | list jumps from (1) to (iii): (ii) may be missing | >(iii) passing of price sensitive information to securities brokers an |
| securities-managers-regulations-2024 | 14 | list jumps from (u) to (w): (v) may be missing | >(w) not assume, issue or offer any type of guarantee to any of the ex |
| securities-managers-regulations-2024 | 14 | list jumps from (3) to (x): (iv) may be missing | >(x) ensure that any performance reporting / presentation is accompani |
| securities-managers-regulations-2024 | 14 | list jumps from (w) to (y): (x) may be missing | >(y) maintain complete file of each customer and not change any detail |
| securities-managers-regulations-2024 | 15 | list jumps from (a) to (c): (b) may be missing | >(c) appoint a separate head for its portfolio management business and |
| securities-managers-regulations-2024 | 16 | list jumps from (a) to (c): (b) may be missing | >(c) neither profit nor seek to profit from confidential information,  |
| securities-managers-regulations-2024 | 19 | list jumps from (h) to (j): (i) may be missing | >(j) placing or executing any order to purchase or sell any security; |
| securities-managers-regulations-2024 | 23 | list jumps from (2) to (4): (3) may be missing | (4) The compliance officer shall prepare monthly compliance reports wh |
| securities-exchange-rules-1971 | 2 | list jumps from (c) to (e): (d) may be missing | >(e) "officer" in relation to an issuer includes managing agents, mana |
| securities-exchange-rules-1971 | 3 | list jumps from (a) to (c): (b) may be missing | >(c) A member shall cease to be a member if, at any time, (i) he cease |
| securities-exchange-rules-1971 | 3 | unbalanced round brackets (1 open, 0 closed) | Provided further that, in the case of firm, the amount of the net capi |
| leveraged-markets-pledging-rules-2011 | 6 | list jumps from (a) to (c): (b) may be missing | >(c) the Commission determines that cancellation of registration will  |
| leveraged-markets-pledging-rules-2011 | 8 | list jumps from (1) to (11): (2) may be missing | (11) it is not in default of any payment obligations under the regulat |
| leveraged-markets-pledging-rules-2011 | 9 | list jumps from (e) to (t): (f) may be missing | >(t) in case the applicant is a company, a copy of the latest audited  |
| leveraged-markets-pledging-rules-2011 | 29 | list jumps from (1) to (iii): (ii) may be missing | >(iii) a shareholder who is barred from selling such securities; or |
| leveraged-markets-pledging-rules-2011 | 33 | unbalanced round brackets (3 open, 2 closed) | >(d) the options available to a client in respect of various financing |
| corporate-rehabilitation-act-2018 | 7 | list jumps from (e) to (g): (f) may be missing | >(g) particulars of shareholders, directors and key management of the  |
| corporate-rehabilitation-act-2018 | 23 | list jumps from (g) to (j): (h) may be missing | >(j) unless the Court makes orders otherwise, furnish such information |
| commercial-papers-regulations-2013 | 2 | list jumps from (d) to (f): (e) may be missing | >(f) "DFI" means a development financial institution as notified by th |
| commercial-papers-regulations-2013 | 2 | list jumps from (p) to (r): (q) may be missing | >(r) "subordinated loan" means the unsecured loan which does not requi |
| commercial-papers-regulations-2013 | 2 | unbalanced round brackets (3 open, 4 closed) | (2) All words and expressions used but not defined in these Regulation |
| commercial-papers-regulations-2013 | 3 | list jumps from (b) to (e): (c) may be missing | >(e) it has no overdue loans or defaults in the report obtained from t |
| commercial-papers-regulations-2013 | 10 | list jumps from (3) to (6): (4) may be missing | (6) The issuer shali intimate in writing to all [aforesaid] subscriber |
| commercial-papers-regulations-2013 | 12 | list jumps from (3) to (v): (iv) may be missing | >(v) detailed provisions on rollover, if any. |
| commercial-papers-regulations-2013 | 12 | list jumps from (a) to (d): (b) may be missing | >(d) ensure that the issuer has met all the requirements as prescribed |
| corporate-restructuring-companies-rules-2019 | 3 | list jumps from (7) to (9): (8) may be missing | (9) The order of refusal to grant a licence shall be communicated to t |
| corporate-restructuring-companies-rules-2019 | 7 | list jumps from (a) to (c): (b) may be missing | >(c) he has been or is adjudged insolvent by a court of law; (d) he is |
| corporate-restructuring-companies-rules-2019 | 7 | list jumps from (c) to (e): (d) may be missing | >(e) he, being a member, absents himself from three consecutive meetin |
| corporate-restructuring-companies-rules-2019 | 8 | list jumps from (b) to (d): (c) may be missing | >(d) collect and maintain record of proceedings and decisions; |
