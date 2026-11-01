# Legal Databank — notes for Claude

Static PWA of Pakistani bare acts, rules and regulations, converted from regulators' official PDFs.
Deployed by Netlify from `main`; every change goes through a branch and a pull request.

## Layout
- `sources/manifest.json` — one entry per instrument: source PDF, edition (`amendedUpTo`), extraction options, `watch` (regulator page to check).
- `sources/pdf/` — official PDFs (the ITR 2002 PDF is too large for git: `remotePdf`/`pdfUrl`).
- `scripts/extract_pdf.py` — PDF → `data/acts/<id>.json` (PyMuPDF). Options are documented in `docs/CONTENT_GUIDE.md`.
- `scripts/build.mjs` — builds `dist/` (pages, search indexes, Sources page, service worker). `scripts/lib.mjs` validates.
- `scripts/related.mjs` + `data/related/companies-act-2017.json` — register of rules/regulations/notifications under the Companies Act 2017, by section; shown under each section and on `acts/companies-act-2017/related.html`.
- `data/search-terms.json` — everyday words and topics per instrument (whole instruments only, never sections); with the manifest's `aliases` they appear on each instrument page ("Also found by"), on `search-guide.html`, and as "Laws and rules" above search results.
- `data/manual-checks.json` + `sources/evidence/` — hand checks of SECP listings with screenshots (shown on the Sources page).
- `scripts/check_updates.mjs` — compares editions with regulator websites (weekly GitHub workflow). `--saved <folder>` reads listing pages saved from a browser.
- `scripts/sync_folders.py` — gathers the newest edition of each PDF from Google Drive, OneDrive and `sources/pdf` into one OneDrive "Unified" folder (`docs/FOLDER_SYNC.md`).

## Commands
- `npm test` (must pass before any PR), `npm run validate`, `npm run build`, `npm run serve` (http://localhost:8080)
- `python3 scripts/extract_pdf.py <id>` then `python3 scripts/check_sequence.py` to check numbering
- `python3 scripts/verify_sheet.py <id>` (or `--unverified`) makes a checklist in `verification/` for a person to check the text against the PDF; then `python3 scripts/mark_verified.py <id> --by "Name" --against "SECP PDF of …"`
- `npm run check-updates -- --json data/update-check.json` (add `--saved <folder>` for SECP pages saved from the browser)
- `python3 scripts/sync_folders.py --from <Google Drive folder> --from <OneDrive folder> --from sources/pdf --to <OneDrive>/Unified` (add `--apply`; dry run otherwise)

## Working locally (the user's Mac) vs the cloud session
The project normally runs locally: repo in `~/Documents/kegaldatabank`, Claude Code started with `claude` in that folder. Setup steps are in `docs/LOCAL_SETUP.md`.

| | Local session (preferred) | Cloud session (claude.ai/code) |
|---|---|---|
| Files | Whole Mac, incl. OneDrive (`~/Library/CloudStorage/OneDrive-Personal/Pak Legal Data Bank`, add with `/add-dir`) and Google Drive | Only GitHub and the Google Drive connector |
| Internet | User's own connection: FBR, FMU, Pakistan Code and usually SECP listing pages load | Restricted; SECP blocked; OneDrive not allowed |
| Saving | On disk; push to GitHub via `gh` (logged in as sendtoadnan) | Must push before the container is reclaimed |
| Cost | Same model usage either way | Same model usage either way |

Local-only abilities to use:
- Read the OneDrive working folder directly; run `scripts/sync_folders.py` on it (no Google Drive bridge needed).
- Run `npm run check-updates` from the user's connection; if SECP still refuses, ask the user to save the listing pages from their browser and use `--saved`.
- Preview the site with `npm run serve` (http://localhost:8080).
- Open PRs with `gh pr create`; the user merges on github.com.
- Keep the git repo outside OneDrive/iCloud (sync corrupts `.git`); PDFs and working papers stay in OneDrive.

Daily routine for the user: `cd ~/Documents/kegaldatabank && git pull && claude`.

## Rules
- Text comes only from the regulator's official PDF; never type or "fix" law text from memory. Mark editions Unverified until a person checks them.
- After re-extracting, confirm the section count is unchanged and review the diff of `data/acts/<id>.json`.
- SECP's website blocks automated access. Do not try to get round it: use the user's browser (saved pages, screenshots), a search engine's index (record `"found": {"how": "search-index"}`), or ask SECP.
- Anything found through search or memory is recorded with what still needs confirming (`confirm`), never as fact.
- The user's credit is limited: prefer running the scripts over reading large files, keep sessions focused, and batch new PDFs.

## State (November 2026)
- **Tasks: `docs/TODO.md` is the one task list (owner You/Claude, status Pending/Waiting/Done/Deferred). Read it at the start of every session, add new tasks with the next number, mark finished ones Done with the date, never delete rows, and update it before the session ends.**
- 30 instruments; all up to date with the regulators per the 4 Oct 2026 checks (SECP by screenshot). Nine Companies Act regulations/notifications added on 4 Oct 2026 are Unverified. S.R.O. 464(I)/2024 (s.17(2), subscription money) added on 1 Nov 2026, Unverified.
- Companies (Related Party Transactions) Regulations 2018 added from S.R.O. 1194(I)/2018 and verified by Abdullah on 4 Oct 2026. Re-extracting resets `verification` to unverified, so re-verify after any re-extraction (restore it with `git checkout` when the text did not change).
- Instruments made under another law (e.g. Securities Act 2015, Companies Ordinance 1984) that do what a Companies Act section leaves to be specified go in the register with `madeUnder` (shown as "Other law"), the basis taken from their recital.
- Repealed instruments are kept for cases about past periods: add them to the library with `"status": "repealed"` and a `caution` naming what repealed them (e.g. Unlisted Companies (Buy-Back of Shares) Regulations 2023), and list predecessors named in repeal provisions in the register with `replacedBy`.
- Still needed from SECP (user's browser): Employees Contributory Funds Regulations "updated – July 2019"; Listed Companies (Buy-back of Shares) Regulations 2019 with the 2022 amendments; an official PDF of the Public Sector Companies (Corporate Governance) Rules 2013 as amended to 2019; a listing screenshot for S.R.O. 1300(I)/2018. Investor Education and Awareness Fund: only draft rules found. PDFs of the repealed instruments in the register.
- Next: the 41 sections still marked "To identify" (56 before 1 Nov 2026) on `acts/companies-act-2017/related.html` (linked from the Act page as "Sections still to identify").
- SECP blocks automated access even from the user's Mac (Cloudflare check): the user downloads each issued edition in the browser and saves it with a screenshot of the listing in the section's Unified folder. Check the PDF is not a draft for comments (S.R.O. 768(I)/2018 was).
- Deferred by the user: Modaraba Rules 1981, CRC Rules 2019 and SRO 243/2024.
