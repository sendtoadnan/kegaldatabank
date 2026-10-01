#!/usr/bin/env python3
"""Report numbering gaps, duplicates and out-of-order provisions in extracted instruments."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check(path):
    act = json.loads(Path(path).read_text())
    nos = [s["no"] for p in act["parts"] for s in p["sections"]]
    base = [int(re.match(r"\d+", n).group()) for n in nos if re.match(r"\d+", n)]
    dups = sorted({n for n in nos if "-" in n})
    backwards = [(nos[i - 1], nos[i]) for i in range(1, len(nos)) if re.match(r"\d+", nos[i]) and re.match(r"\d+", nos[i - 1])
                 and int(re.match(r"\d+", nos[i]).group()) < int(re.match(r"\d+", nos[i - 1]).group())]
    present = set(base)
    gaps = [n for n in range(1, max(base) + 1) if n not in present] if base else []
    return {"id": act["id"], "count": len(nos), "max": max(base) if base else 0, "gaps": gaps[:40],
            "duplicates": dups[:20], "backwards": backwards[:10]}


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(str(p) for p in (ROOT / "data" / "acts").glob("*.json"))
    for f in files:
        a = json.loads(Path(f).read_text())
        if a.get("pdfOnly") or not a["parts"]:
            continue
        print(json.dumps(check(f)))
