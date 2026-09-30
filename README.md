# Legal Databank (kegaldatabank)

An online reference library of **bare acts and the rules and regulations made under them**, for legal counsel, corporate lawyers, tax practitioners and AML/CFT compliance professionals.

The aim is simple: open a statute, find the provision, and quote it with authority in seconds, on any device, even offline.

## What it does today

| Feature | Detail |
|---|---|
| **Library by practice area** | Corporate & Securities, Taxation, AML/CFT (add more in `data/catalog.json`). Rules and regulations are listed under their parent Act. |
| **Clean bare-act reading** | Serif text, proper clause indentation, Parts/Chapters, sticky and filterable contents. Light and dark mode. |
| **One-click citation** | **Cite** copies a formal citation, e.g. *Section 111 of the Income Tax Ordinance, 2001 (Ordinance No. XLIX of 2001)*. **Quote** copies the full provision text plus citation. **Link** copies a permanent link to the provision. |
| **Search** | Full-text search across every instrument, with exact phrases in `"quotes"`, filters by practice area and instrument type, and highlighted snippets. |
| **Direct jump** | Type `s 111 ITO`, `section 3 AMLA`, `CA 2017 204` or `rule 1 ITR` to go straight to the provision. |
| **My shelf** | Save provisions for a matter and copy all their citations at once. |
| **Verification status** | Every instrument is marked **Verified** (checked against a named official source, by whom and when) or **Unverified**. |
| **Offline and installable** | Works as a Progressive Web App: install it on a phone or desktop, and read the whole library without a connection. |
| **Print / PDF** | Print-optimised statute layout. |
| **Import tool** | Converts statute text copied from an official PDF into the library format. |

> **Important:** the seed content in `data/acts/` is a *demonstration extract* for five Pakistani instruments. It is marked **Unverified** and must be replaced with text checked against the Gazette before anyone relies on it. See [docs/CONTENT_GUIDE.md](docs/CONTENT_GUIDE.md).

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
scripts/import-text.mjs  statute text -> draft JSON
scripts/validate.mjs     content rules check
src/assets/              styles, client script, icon
src/sw.template.js       offline service worker
test/                    automated tests
docs/                    content guide and product roadmap
```

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the plan: point-in-time versions and amendment tracking, SROs and circulars, case-law links, subscriber accounts, and AI-assisted research that answers only from cited provisions.
