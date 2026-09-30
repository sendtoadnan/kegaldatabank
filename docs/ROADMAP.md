# Product roadmap

## Recommended medium

**A website that installs as an app (Progressive Web App)**, which is what this repository builds.

- One product serves desktop (where drafting happens), mobile (court corridors, client meetings), and offline reading.
- No app-store approval, and no separate Android/iOS codebases.
- Static pages load instantly, are indexed by Google (people searching "section 111 ITO" land on you), and cost almost nothing to host.
- A native app and a Word add-in can come later, reusing the same data.

## Phase 1: Foundation (built)

- Library by practice area; rules and regulations nested under their parent Act
- Clean reading layout, contents, print/PDF, dark mode
- One-click Cite / Quote / Link, and My shelf
- Full-text search, phrase search, direct jump (`s 111 ITO`)
- Verification status on every instrument
- Offline and installable
- Importer from official PDF text, validator, automated tests, CI

## Phase 2: Content at scale (next 1–3 months)

The value of the product is the content. Suggested first corpus for corporate, tax and AML practice:

- **Corporate:** Companies Act 2017; Companies (General Provisions and Forms) Regulations 2018; Listed Companies (Code of Corporate Governance) Regulations 2019; Securities Act 2015; SECP Act 1997; Limited Liability Partnership Act 2017; Partnership Act 1932; Contract Act 1872.
- **Tax:** Income Tax Ordinance 2001 and Income Tax Rules 2002; Sales Tax Act 1990 and Sales Tax Rules 2006; Federal Excise Act 2005; Customs Act 1969; provincial sales tax on services laws; Finance Acts.
- **AML/CFT:** Anti-Money Laundering Act 2010 and its regulations; Anti-Terrorism Act 1997; United Nations (Security Council) Act 1948 and SROs; SECP, SBP and FMU AML/CFT regulations and guidelines.

Also in this phase:

- **Point-in-time versions:** show a provision "as on" any date, with every amendment traced to its Finance Act or SRO. This is essential for tax litigation, where the law as it stood in the relevant tax year governs.
- **Cross-references:** automatic links wherever a provision mentions "section 120".
- **Definitions pop-ups:** hover a defined term to see its definition clause.
- **SROs, circulars and notifications** linked to the provisions they affect.

## Phase 3: Professional platform (3–6 months)

- **Accounts and subscriptions:** free public bare acts; paid tiers for annotations, versions and alerts.
- **Server search** (PostgreSQL full-text or Meilisearch) once the corpus grows past a few hundred instruments.
- **Amendment alerts** by email or WhatsApp for the laws a user follows.
- **Case-law notes** under each section: leading judgments of the Supreme Court, High Courts and Appellate Tribunal Inland Revenue, with citations.
- **Team shelves** so a firm can share research on a matter.
- **Word add-in** to insert a quotation and citation straight into an opinion.

## Phase 4: AI-assisted research

- Plain-language questions ("time limit to amend an assessment") answered **only from provisions in the library**, with each statement linked to the exact section it came from, so counsel can check the source before relying on it.
- Comparison of a provision across tax years.
- Drafting help that cites its authority.

## Trust and legal points

- Primary legislation published by the Government is generally free to reproduce, but check the terms of any **consolidated or annotated** text you copy from commercial publishers. Build from the Gazette and official regulator sources.
- Show the verification status and the "as amended up to" date everywhere; that is what makes a quotation safe to use.
- Keep a clear disclaimer that the service is a research aid, not legal advice.
