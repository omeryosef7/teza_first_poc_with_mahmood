#!/usr/bin/env python3
"""Structural check for external_md/DCS_SESSION_TRACKER_20260904.md.

Written after re-implementing the same check inline ~15 times in one session and having it produce
a FALSE POSITIVE on the 16th: a cell containing an escaped pipe (`\\|rho\\|`) renders correctly in
GitHub-flavoured markdown but has extra raw `|` characters, so a naive count calls the row ragged.

Checks:
  * exactly two tables (the main log and the Live table);
  * each table has exactly one header separator;
  * every row in a table has the same cell count, counting ESCAPED pipes as content, not delimiters.

Exit 0 if the file is structurally sound, 1 otherwise. Usage: python3 scripts/dcs_check_tracker.py
"""
import re, sys, os

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "external_md", "DCS_SESSION_TRACKER_20260904.md")


def cells(line):
    """Split a markdown table row, treating `\\|` as literal content rather than a delimiter."""
    masked = line.replace(r"\|", "\0")
    return [c.replace("\0", r"\|") for c in masked.strip().strip("|").split("|")]


def main():
    lines = open(PATH).read().splitlines()
    blocks, cur = [], []
    for l in lines:
        if l.lstrip().startswith("|"):
            cur.append(l)
        elif cur:
            blocks.append(cur); cur = []
    if cur:
        blocks.append(cur)

    ok = True
    if len(blocks) != 2:
        print(f"FAIL: expected 2 tables, found {len(blocks)}"); ok = False
    for i, b in enumerate(blocks):
        widths = {len(cells(r)) for r in b}
        seps = [r for r in b if set(r.strip()) <= set("|- ")]
        if len(widths) != 1:
            print(f"FAIL: table {i} ragged, cell counts {sorted(widths)}")
            for r in b:
                if len(cells(r)) != max(widths, key=lambda w: sum(len(cells(x)) == w for x in b)):
                    print(f"    {len(cells(r))} cells: {r[:90]}")
            ok = False
        if len(seps) != 1:
            print(f"FAIL: table {i} has {len(seps)} header separators, expected 1"); ok = False
        if ok:
            print(f"table {i}: {len(b) - 2} rows, {widths.pop()} columns, 1 separator  OK")
    print("TRACKER STRUCTURE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
