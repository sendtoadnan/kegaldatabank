# Keeping the law PDFs in one folder

The official PDFs live in three places: the Google Drive folder **Paklegaldatabank** (which Claude
can read), your **OneDrive** folder **Pak Legal Data Bank** (synced to your Mac), and this
repository's `sources/pdf/` (what the website is built from). `scripts/sync_folders.py` compares
them and gathers the newest edition of each law into one **Unified** folder on OneDrive.

## How the pieces connect

```
 You download from FBR / SECP / FMU ──► OneDrive "Pak Legal Data Bank" (your working folder)
                                              │
                    python3 scripts/sync_folders.py  (on your Mac)
                                              │
                                              ▼
                          OneDrive "Pak Legal Data Bank/Unified"   ◄── newest edition of each law
                                              │  --mirror
                                              ▼
                          Google Drive "Paklegaldatabank/Unified"  ──► Claude reads it ──► pull request on GitHub
                                                                                      ──► website
```

Claude cannot reach OneDrive from its cloud session, so Google Drive is the bridge: the script
copies the unified folder there, Claude picks the files up, converts them and opens a pull request.

## Run it

You need Python 3 and, for reading the editions printed on the PDFs, PyMuPDF
(`python3 -m pip install pymupdf`). In a terminal, from your copy of this repository:

```sh
python3 scripts/sync_folders.py \
  --from "$HOME/Library/CloudStorage/GoogleDrive-<your Google account>/My Drive/Paklegaldatabank" \
  --from "$HOME/Library/CloudStorage/OneDrive-Personal/Pak Legal Data Bank" \
  --from sources/pdf \
  --to   "$HOME/Library/CloudStorage/OneDrive-Personal/Pak Legal Data Bank/Unified" \
  --scaffold companies-act-2017
```

This only prints the plan. Check it, then run the same command with `--apply`, and add
`--mirror "$HOME/Library/CloudStorage/GoogleDrive-<your Google account>/My Drive/Paklegaldatabank/Unified"`
to pass the result to Claude. (Finder shows the exact folder names under *Locations*; drag a folder
into the terminal to paste its path.)

## What it does

- Reads every PDF in the `--from` folders (and their sub-folders). Identical files are counted once.
- Works out **which law** each PDF is: the file name recorded in `sources/manifest.json`, the same
  bytes as the library's copy, the law's title in the file name, or the title on its first pages.
- Works out **which edition**: the "amended / updated up to" date printed on the PDF's first pages,
  otherwise the date in its file name. When renamed copies of the same file carry different dates it
  says so.
- Copies the newest edition of each law to `Unified/<practice area>/<law>/`, older ones to
  `<law>/Older editions/`, and anything it cannot identify to `Unified/_To sort/`. File names start
  with the edition date. Nothing is moved or deleted.
- Marks each law **NEWER than the library**, **same as the library** or **older than the library**
  and writes everything to `Unified/unified-index.csv`. A law marked NEWER is one to update on the
  website: tell Claude, or follow `docs/CONTENT_GUIDE.md`.
- `--scaffold companies-act-2017` creates a folder for each rule, regulation and notification in the
  Companies Act 2017 register, named by section (for example
  `s.199 - Companies (Investment in Associated Companies or Associated Undertakings) Regulations, 2017`),
  so you can drop each PDF where it belongs.
