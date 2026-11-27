#!/usr/bin/env python3
"""Indent runs of dotted list items ("i.", "ii.", "a.") that follow a lead-in ending in ":" or ":-" (words unchanged).
usage: python3 tools/indent_dotted.py [--apply]"""
import json, glob, re, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = re.compile(r'^((?:\{fn:[^}]*\})?\[?)(([ivx]{1,5})|([a-z]))\.\s')
LEAD = re.compile(r':\s*[-–—]?\s*$')
tot = 0
for f in sorted(glob.glob(ROOT + "/data/acts/*.json")):
    raw = open(f).read(); d = json.loads(raw); k = 0
    for p in d["parts"]:
        for s in p["sections"]:
            T = s["text"]; inrun = False; prev_lead = False
            for i, t in enumerate(T):
                top = not t.startswith((">", "|"))
                if top and R.match(t) and (inrun or prev_lead):
                    T[i] = ">" + t; k += 1; inrun = True
                else:
                    if not (top and R.match(t)): inrun = False if not t.startswith(">") else inrun
                    if top: prev_lead = bool(LEAD.search(t)) or bool(re.match(r"^\(\d+\)", t) and False)
    if k:
        tot += k; print(os.path.basename(f), k)
        if "--apply" in sys.argv:
            ind = 1 if raw.startswith('{\n "') else 2
            open(f, "w").write(json.dumps(d, ensure_ascii=False, indent=ind) + ("\n" if raw.endswith("\n") else ""))
print(tot, "indented" + ("" if "--apply" in sys.argv else " (dry run)"))
