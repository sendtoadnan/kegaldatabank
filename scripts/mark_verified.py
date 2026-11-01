#!/usr/bin/env python3
"""Record that a person has checked an instrument against its official source.

    python3 scripts/mark_verified.py companies-postal-ballot-regulations-2018 \
        --by "Abdullah" --against "SECP PDF of S.R.O. 254(I)/2018 as amended up to 20 March 2025"

Sets verification to verified with the name, the source checked and today's date (or --on YYYY-MM-DD).
Only run it after every provision on the checklist (scripts/verify_sheet.py) has been ticked.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("id")
ap.add_argument("--by", required=True, help="name of the person who checked it")
ap.add_argument("--against", required=True, help="the official source checked, e.g. the SECP PDF and its edition")
ap.add_argument("--on", default=date.today().isoformat(), help="date checked (YYYY-MM-DD)")
a = ap.parse_args()
if not re.fullmatch(r"\d{4}-\d\d-\d\d", a.on):
    ap.error("--on must be YYYY-MM-DD")
path = ROOT / "data" / "acts" / f"{a.id}.json"
if not path.exists():
    raise SystemExit(f"Unknown instrument: {a.id}")
act = json.loads(path.read_text())
act["verification"] = {"status": "verified", "against": a.against, "verifiedBy": a.by, "verifiedOn": a.on}
path.write_text(json.dumps(act, ensure_ascii=False, indent=1) + "\n")
print(f"{act['title']}: verified by {a.by} on {a.on} against {a.against}")
print("Run npm test, then commit and open a pull request.")
