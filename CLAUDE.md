# Legal Databank — notes for Claude

Static PWA of Pakistani bare acts, rules and regulations, converted from regulators' official PDFs.
Deployed by Netlify from `main`; every change goes through a branch and a pull request.

## Layout
- `sources/manifest.json` — one entry per instrument: source PDF, edition (`amendedUpTo`), extraction options, `watch` (regulator page to check).
- `sources/pdf/` — official PDFs (the ITR 2002 PDF is too large for git: `remotePdf`/`pdfUrl`).
- `scripts/extract_pdf.py` — PDF → `data/acts/<id>.json` (PyMuPDF). Options are documented in `docs/CONTENT_GUIDE.md`.
- `scripts/build.mjs` — builds `dist/` (pages, search indexes, Sources page, service worker). `scripts/lib.mjs` validates.
- `scripts/related.mjs` + `data/related/companies-act-2017.json` — register of rules/regulations/notifications under the Companies Act 2017, by section; shown under each section and on `acts/companies-act-2017/related.html`.
- `data/manual-checks.json` + `sources/evidence/` — hand checks of SECP listings with screenshots (shown on the Sources page).
- `scripts/check_updates.mjs` — compares editions with regulator websites (weekly GitHub workflow). `--saved <folder>` reads listing pages saved from a browser.
- `scripts/sync_folders.py` — gathers the newest edition of each PDF from Google Drive, OneDrive and `sources/pdf` into one OneDrive "Unified" folder (`docs/FOLDER_SYNC.md`).

## Commands
- `npm test` (must pass before any PR), `npm run validate`, `npm run build`, `npm run serve` (http://localhost:8080)
- `python3 scripts/extract_pdf.py <id>` then `python3 scripts/check_sequence.py` to check numbering
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

## State (October 2026)
- 19 instruments; all up to date with the regulators per the 4 Oct 2026 checks (SECP by screenshot).
- Companies (Related Party Transactions) Regulations 2018 added from S.R.O. 1194(I)/2018 and verified by Abdullah on 4 Oct 2026. Re-extracting resets `verification` to unverified, so re-verify after any re-extraction.
- Next: add the in-force Companies Act 2017 instruments in the register without a `library` id (s.199 investment in associated companies, s.83 further issue of shares, postal ballot, s.88 buy-back, s.242–243 dividends, then the rest), then the 84 sections still marked "To identify" on `acts/companies-act-2017/related.html`.
- SECP blocks automated access even from the user's Mac (Cloudflare check): the user downloads each issued edition in the browser and saves it with a screenshot of the listing in the section's Unified folder. Check the PDF is not a draft for comments (S.R.O. 768(I)/2018 was).
- Deferred by the user: Modaraba Rules 1981, CRC Rules 2019 and SRO 243/2024.
