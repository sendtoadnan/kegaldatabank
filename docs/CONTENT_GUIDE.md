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
| `notes` | Amendment history, footnotes, editor notes. Shown beneath the provision. |
| `verification` | `unverified` (with an optional `note`) or `verified` (requires `against`, `verifiedBy`, `verifiedOn`). |

## 2. Loading a new law

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

## 3. Keeping the law current

- After each **Finance Act**, **SRO** or **amendment Act**, update the affected provisions, add a note (`"Substituted by the Finance Act, 2026, s. 5"`), update `lastAmended`, and re-verify.
- Never edit a verified file without re-verifying it. Updating the text means updating `verifiedBy` and `verifiedOn` too.
- Keep repealed instruments with `"status": "repealed"`; they remain citable for past transactions.

## 4. Rules the validator enforces

`npm run validate` fails the build if an instrument has missing fields, an unknown category or type, a duplicate provision number, a missing parent, a malformed date, or a `verified` status without who/when/against.
