# Legal Databank (kegaldatabank)

An online reference library of **bare acts and the rules and regulations made under them**, for legal counsel, corporate lawyers, tax practitioners and AML/CFT compliance professionals.

The aim is simple: open a statute, find the provision, and quote it with authority in seconds, on any device, even offline.

## What it does today

| Feature | Detail |
|---|---|
| **Library by practice area** | Corporate & Securities, Taxation, AML/CFT (add more in `data/catalog.json`). Rules and regulations are listed under their parent Act. |
| **Clean bare-act reading** | Serif text, proper clause indentation, Parts/Chapters, sticky and filterable contents. Light and dark mode. |
| **One-click citation** | **Cite** copies a formal citation, e.g. *Section 111 of the Income Tax Ordinance, 2001 (Ordinance No. XLIX of 2001)*. **Quote** copies the full provision text plus citation. **Link** copies a permanent link to the provision. |
| **Search** | Full-text search across every instrument, with exact phrases in `"quotes"`, filters by practice area and instrument type, and highlighted snippets. Tick **Amendment notes (footnotes)** to search the notes too; a note result opens the provision with that note highlighted. |
| **Direct jump** | Type `s 111 ITO`, `section 3 AMLA`, `CA 2017 204` or `rule 1 ITR` to go straight to the provision. |
| **My shelf** | Save provisions for a matter and copy all their citations at once. |
| **Verification status** | Every instrument is marked **Verified** (checked against a named official source, by whom and when) or **Unverified**. |
| **Offline and installable** | Works as a Progressive Web App: install it on a phone or desktop; search and every instrument you have opened keep working without a connection. |
| **Print / PDF** | Print-optimised statute layout. |
| **Official PDF on every provision** | **PDF p.** opens the source PDF at the exact page, for checking before quoting. |
| **Amendment notes** | Superscript markers link to the source's amendment footnotes (which Finance Act or S.R.O. changed what). **Show amendment notes** on an instrument page opens every note at once (remembered on that device). |
| **Sources and updates** | The **Sources** page compares each law's edition with the latest edition on the regulator's website (checked weekly; `npm run check-updates` runs it by hand) and links to the page to check. |
| **PDF importer** | `scripts/extract_pdf.py` converts FBR/SECP consolidated PDFs, with completeness checks against their contents lists. |

## What is in the library

Converted from the official FBR and SECP consolidated editions (all marked **Unverified** until checked against the Gazette):

| Area | Instruments |
|---|---|
| Taxation | Income Tax Ordinance 2001 (to 30.06.2026), Income Tax Rules 2002 (to 15.09.2026), Sales Tax Act 1990 (to 30.06.2026), Sales Tax Rules 2006 (to 31.07.2026), Federal Excise Act 2005 (to 30.06.2026), Federal Excise Rules 2005 (to 16.09.2026), Customs Act 1969 (to 30.06.2026), Benami Transactions (Prohibition) Act 2017 (Pakistan Code, as enacted) |
| Corporate | Companies Act 2017 (SECP edition to 18.08.2022), Companies Regulations 2024 (to 25.07.2025), Third Schedule (to 29.12.2025), Seventh Schedule (to 10.11.2025), S.R.O. 239(I)/2024 |
| Insurance | Insurance Ordinance 2000 (SECP edition to Nov 2011), Insurance Rules 2017 (to 03.03.2025), Takaful Rules 2012 (to 22.10.2015) |
| AML/CFT | Anti-Money Laundering Act 2010 (FMU edition to Sept 2020), SECP AML/CFT/CPF Regulations 2020 (to 03.07.2026) |

Every provision links to the page of the official PDF it came from, and amendment footnotes are attached to the provision they belong to.


## Quick start

Requires Node.js 18 or newer. There are no other dependencies.

```bash
npm test          # validate data, build, and test importer
npm run serve     # build and preview at http://localhost:8080
npm run build     # produce the static site in dist/
```

## Publishing the website

The build output in `dist/` is a plain static website. It is fast and cheap to host, and it scales to any number of readers.

- **Netlify** (recommended): connect this repository; `netlify.toml` is already configured. Add your own domain (for example `legaldatabank.pk`) in the Netlify dashboard.
- **GitHub Pages / Cloudflare Pages / any web host:** upload the contents of `dist/`.

## Adding a law

1. Copy the text of the Act from the official PDF into a `.txt` file.
2. Convert it to a draft:
   ```bash
   npm run import -- act.txt --id sales-tax-act-1990 --title "Sales Tax Act, 1990" \
     --number "Act No. VII of 1990" --type act --category tax > data/acts/sales-tax-act-1990.json
   ```
3. Proof-read the JSON against the Gazette, fill in the dates, source and aliases, then mark it verified.
4. Run `npm test` and publish.

Full details are in [docs/CONTENT_GUIDE.md](docs/CONTENT_GUIDE.md).

## Project layout

```
data/catalog.json        site name and practice areas
data/acts/*.json         one file per Act, Ordinance, Rules or Regulations
scripts/build.mjs        static site generator  -> dist/
scripts/extract_pdf.py   official PDF -> library JSON (with amendment notes and page links)
scripts/check_sequence.py numbering gap / duplicate report
scripts/import-text.mjs  plain statute text -> draft JSON
sources/manifest.json    metadata for each source PDF
sources/pdf/             the official source PDFs (published at /sources/<id>.pdf)
scripts/validate.mjs     content rules check
src/assets/              styles, client script, icon
src/sw.template.js       offline service worker
test/                    automated tests
docs/                    content guide and product roadmap
```

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the plan: point-in-time versions and amendment tracking, SROs and circulars, case-law links, subscriber accounts, and AI-assisted research that answers only from cited provisions.
