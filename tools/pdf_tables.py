"""Shared helpers to turn ruled PDF tables into table rows for the library (see docs/CONTENT_GUIDE.md).

A table is stored as a run of paragraph strings: "|!Head|Head|Head" (header row), "|a|b|c" (row), "|Caption" (a row with one
filled cell). Used by tools/fe_manual.py (chapter PDFs) and tools/add_tables.py (instruments already in data/acts)."""
import re


def clean_cell(c):
    return re.sub(r"\s+", " ", (c or "").replace("|", "/")).strip()


def find_tables(pg, strict=False):
    """Ruled tables on a page as {x0, y0, y1, x1, rows}: empty rows and columns dropped, cells joined onto one line."""
    out = []
    try: found = pg.find_tables().tables
    except Exception: return out
    for t in found:
        rows = [[clean_cell(c) for c in r] for r in t.extract()]
        rows = [r for r in rows if any(r)]
        if len(rows) < 2: continue
        keep = [j for j in range(max(len(r) for r in rows)) if any(j < len(r) and r[j] for r in rows)]
        rows = [[r[j] if j < len(r) else "" for j in keep] for r in rows]
        if len(keep) < 2 or sum(1 for r in rows for c in r if c) < 4: continue
        if strict:      # law-text PDFs: ruled layout boxes and margin notes also look like tables, so keep only tabular ones
            cells = [c for r in rows for c in r if c]
            full = sum(1 for r in rows if sum(1 for c in r if c) >= 2)
            if len(cells) < 0.5 * len(rows) * len(keep) or full < 2 or full < 0.6 * len(rows): continue
            if sum(len(c.split()) for c in cells) / len(cells) > 18: continue
        x0, y0, x1, y1 = t.bbox
        out.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "rows": rows})
    return out


def row_strings(rows):
    """Table rows as paragraph strings: "|a|b|c", the header row as "|!a|b|c"; a row with one filled cell is a caption."""
    num = lambda c: bool(re.fullmatch(r"[-+()\d.,%/ ]+", c))
    head = next((i for i, r in enumerate(rows[:3]) if sum(1 for c in r if c) >= 2 and not any(num(c) for c in r if c)), None)
    out = []
    for i, r in enumerate(rows):
        filled = [c for c in r if c]
        cells = filled if len(filled) == 1 and i != head else r
        out.append("|" + ("!" if i == head else "") + "|".join(cells))
    return out
