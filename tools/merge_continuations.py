#!/usr/bin/env python3
"""Join wrapped lines that were stored as separate paragraphs (words unchanged).

usage: python3 tools/merge_continuations.py [--apply] [--sample N] [id ...]

A paragraph is a continuation when it starts in lower case (and is not a list label such as "i." or "(a)")
and the paragraph before it is not a table row and does not end a sentence (. ; : ? !).
It is appended to the earlier paragraph with one space, which keeps that paragraph's indent level.
Refuses to write when the words of an instrument would change.
"""
import json, re, sys, glob, os
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = "--apply" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]
SAMPLE = int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0
LABEL = re.compile(r"^(\(?[a-z]{1,4}[.)]+|[a-z]\.)\s")
END = re.compile(r"[.;:?!]['\"”’)\]]*\s*$|:\s*[-–—]\s*$")

def merge(paras):
    out, n = [], 0
    for t in paras:
        body = t.lstrip(">")
        if out and body[:1].islower() and not LABEL.match(body) and not t.startswith("|") and not out[-1].startswith("|") \
           and not END.search(out[-1]) and out[-1].strip():
            out[-1] = out[-1].rstrip() + ("" if out[-1].rstrip().endswith("-") else " ") + body.strip(); n += 1
        else: out.append(t)
    return out, n

def words(d):
    c = Counter()
    for p in d.get("parts", []):
        for s in p.get("sections", []):
            for t in s.get("text", []): c.update(re.findall(r"[^\W_]+", re.sub(r"\{fn:[^}]*\}", "", t)))
    for s in d.get("schedules", []):
        for t in s.get("text", []) if isinstance(s.get("text"), list) else []: c.update(re.findall(r"[^\W_]+", re.sub(r"\{fn:[^}]*\}", "", t)))
    return c

total = 0
for f in sorted(glob.glob(os.path.join(ROOT, "data/acts/*.json"))):
    iid = os.path.basename(f)[:-5]
    if args and iid not in args: continue
    raw = open(f).read(); d = json.loads(raw); before = words(d); k = 0; shown = 0
    for p in d.get("parts", []):
        for s in p.get("sections", []):
            if s.get("text"):
                old = s["text"]; s["text"], n = merge(old); k += n
                if n and shown < SAMPLE:
                    for a, b in zip(old, old[1:]):
                        if b.lstrip(">")[:1].islower() and not LABEL.match(b.lstrip(">")) and not END.search(a) and not a.startswith("|"):
                            print("   ", s.get("no"), repr(a[-50:]), "+", repr(b[:50])); shown += 1; break
    for s in d.get("schedules", []):
        if isinstance(s.get("text"), list) and s["text"]:
            s["text"], n = merge(s["text"]); k += n
    if not k: continue
    if words(d) != before: print("WORDS CHANGED", iid); continue
    total += k; print(f"{iid}: {k} joined")
    if APPLY:
        ind = 1 if raw.startswith('{\n "') else 2
        open(f, "w").write(json.dumps(d, ensure_ascii=False, indent=ind) + ("\n" if raw.endswith("\n") else ""))
print(total, "joined" + ("" if APPLY else " (dry run)"))
