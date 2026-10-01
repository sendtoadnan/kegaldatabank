# Content guide

This guide is for the editors who load and maintain the law. The website's value rests on one promise: **the text is exactly what the Gazette says, and the reader can see when it was last checked.**

## 1. Instrument file format

Each Act, Ordinance, Rules or Regulations is one JSON file in `data/acts/`, named `<id>.json`.

```json
{
  "id": "sales-tax-act-1990",
  "title": "Sales Tax Act, 1990",
  "number": "Act No. VII of 1990",
  "type": "act",
  "unit": "Section",
  "parent": null,
  "categories": ["tax"],
  "aliases": ["STA", "STA 1990", "Sales Tax Act"],
  "enacted": "1990-11-01",
  "lastAmended": "2026-06-30",
  "status": "in-force",
  "source": { "name": "Federal Board of Revenue", "url": "https://www.fbr.gov.pk" },
  "verification": {
    "status": "verified",
    "against": "Consolidated text as amended by the Finance Act, 2026 (Gazette of Pakistan, Extraordinary)",
    "verifiedBy": "A. Editor",
    "verifiedOn": "2026-07-05"
  },
  "preamble": "An Act to consolidate and amend the law relating to the levy of sales tax.",
  "parts": [
    {
      "heading": "Chapter I — Preliminary",
      "sections": [
        {
          "no": "1",
          "title": "Short title, extent and commencement",
          "text": ["(1) ...", "(2) ...", ">(a) clause", ">>(i) sub-clause"],
          "notes": ["Substituted by the Finance Act, 2026."]
        }
      ]
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `type` | `act`, `ordinance`, `rules`, `regulations`, `order` or `notification` |
| `unit` | What provisions are called in citations: `Section`, `Rule`, `Regulation`, `Article`, `Paragraph` |
| `parent` | For subordinate legislation, the `id` of the Act it is made under. It then appears under that Act. |
| `aliases` | Short names readers type in search, e.g. `ITO`, `CA 2017`. These power the direct jump (`s 111 ITO`). |
| `text` | One string per paragraph. Start with `>` to indent a clause one level, `>>` for two levels. |
| `notes` | Editor notes. Shown beneath the provision. |
| `fn` | Amendment footnotes from the source, keyed to `{fn:key}` markers in `text`. |
| `page` | Page of the source PDF where the provision is printed. |
| `sourcePdf`, `amendedUpToLabel`, `caution`, `sourceNotes` | Source edition details shown on the instrument page. |
| `verification` | `unverified` (with an optional `note`) or `verified` (requires `against`, `verifiedBy`, `verifiedOn`). |

## 2. Loading a law from an official PDF (recommended)

Consolidated editions published by FBR and SECP are converted with `scripts/extract_pdf.py`, which reads the PDF's layout (font sizes, bold headings, superscripts) rather than plain text. It:

- finds each provision from its bold number and heading, including inserted (`[3A.`) and omitted (`[33A. ***]`) provisions;
- turns amendment superscripts into `{fn:<page>-<number>}` markers and attaches the footnote text to the provision (`"fn": [{"n": "28-142", "text": "Substituted for seventeen vide ..."}]`), including FBR's chapter endnotes ("LEGAL REFERENCE") when `"endnotes": true`;
- records the PDF page of every provision, so the site can link to the official page;
- lists schedules and annexures with their PDF page instead of reflowing their tables.

Steps:

1. Put the PDF in `sources/pdf/` and add an entry to `sources/manifest.json` (id, file, title, number, type, unit, categories, parent, "amended up to" date, source, and any `caution`).
2. `pip install pymupdf`, then `python3 scripts/extract_pdf.py <id>`. The report compares the result with the PDF's own contents list.
3. `python3 scripts/check_sequence.py` must show no gaps or duplicates; `npm test` enforces the same.
4. Spot-check provisions against the PDF (the **PDF p.** button on each provision opens the right page).
5. Items that are mostly tables (fee schedules, classification grids) are added with `"pdfOnly": true` and shown as the official PDF.

Per-document options in the manifest: `bodyStartPage` / `bodyEndPage` (skip contents pages without dot leaders; stop before forms), `stopAtSchedule: false` (for rules with inline "Schedule" headings), `untitledProvisions: true` (provisions numbered without headings), `endnotes: true` (notes gathered at chapter ends).

Further options, used for the FBR Income Tax Ordinance and Rules:

| Option | Use |
|---|---|
| `tocPages: [first, last]` | Read a contents list laid out in columns (no dot leaders) for the completeness report. |
| `omittedFromToc: true` | Add provisions the contents list shows as omitted or renumbered but the body prints only as a bare `N[ ]` marker. |
| `omittedFromNotes: true` | Add provisions known only from a note such as "Rule 35 omitted by SRO …". |
| `plainNumberProvisions: ["6", "7"]` | Provisions printed with a regular-weight number and no heading (checked by hand). |
| `numberingGaps: [54, …]` | Numbers the edition does not print at all; explain them in `sourceNotes`. The tests accept only documented gaps. |
| `refSizeRatio` | Largest size of an amendment marker set without the superscript flag, relative to body text (default 0.75). |
| `notesPerPage: true` | Note numbers restart on every page: never borrow a note from an earlier page. |
| `footnoteRule: 144` | Split notes at the footnote separator rule of this width (Word's 2-inch rule), for editions whose notes vary in size. |
| `headerBand: 135` | Drop running headers: lines above this height that recur on other pages. |
| `nestedHeadings: true` | Keep "Chapter III …" and the "Part I …" heading under it together. |
| `schedules: [{title, page}]` | List the schedules and their PDF pages yourself when the edition's headings cannot be detected. |
| `noteMaxSize: 10` | Largest font size of footnote text, for editions whose body text varies in size from page to page. |
| `annexInline: true` | Annexures printed between chapters: an annexure ends at the next chapter heading or the next provision in sequence. |
| `lowercaseContinues: true` | Double-spaced editions: a new paragraph needs a clause label, "Provided"/"Explanation", or a finished sentence before it. |
| `imageProvisions: [{no, title, page, pages}]` | Provisions printed only as scanned images: listed with their contents-list heading and a pointer to the PDF pages. No text is invented. |
| `plainHeadings: true` | Accept "CHAPTER I" / "PART II" labels printed in regular weight (Pakistan Code editions). |
| `spaceGaps: true` | Insert the space between adjacent font runs that are visibly apart but carry no space character. |
| `pdfUrl`, `remotePdf: true` | Link the regulator's own PDF instead of republishing it (for very large editions). The extractor downloads it when it is not in `sources/pdf/`. |

A note found on a schedule page is kept only when a provision cites its marker, and a repeated marker may borrow a note from at most 15 pages back. The report also counts `unlinkedMarkers` (amendment markers whose note was not captured; the site marks them and points to the PDF page) and `notesFromEarlierPages`.

## 3. Loading a law from plain text

1. **Get the authoritative text.** Use the Gazette or the regulator's consolidated version (SECP, FBR, SBP, FMU, Pakistan Code).
2. **Convert.** Copy the PDF text into a `.txt` file and run the importer:
   ```bash
   npm run import -- act.txt --id <id> --title "<Title>" --number "<Act No.>" --type act --category <category> > data/acts/<id>.json
   ```
   The importer detects `PART`/`CHAPTER` headings and provisions written as `12. Heading.—(1) Text`, and indents `(a)` and `(i)` clauses.
3. **Proof-read.** PDF extraction breaks lines, drops dashes and confuses `(i)` (letter) and `(i)` (roman). Compare every provision line by line.
4. **Complete metadata:** dates, source, aliases, and amendment notes.
5. **Verify.** A second person checks the file against the source, then sets `verification.status` to `verified` with their name and date.
6. **Test and publish:** `npm test`, then push. The website rebuilds automatically.

## 4. Keeping the law current

- After each **Finance Act**, **SRO** or **amendment Act**, update the affected provisions, add a note (`"Substituted by the Finance Act, 2026, s. 5"`), update `lastAmended`, and re-verify.
- Never edit a verified file without re-verifying it. Updating the text means updating `verifiedBy` and `verifiedOn` too.
- Keep repealed instruments with `"status": "repealed"`; they remain citable for past transactions.

## 5. Rules the validator enforces

`npm run validate` fails the build if an instrument has missing fields, an unknown category or type, a duplicate provision number, a missing parent, a malformed date, or a `verified` status without who/when/against.
