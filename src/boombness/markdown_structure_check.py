"""markdown_structure_check.py — do the deliverables' tables actually render?

WHY. On 2026-08-22 an ad-hoc scan found three broken tables, one of them the **retraction registry** —
the table the report's own header calls *authoritative*. It had a 4-column header over rows carrying 3
cells (22 of 24), so `status` and `why` merged and the `why` column rendered empty for every row a
reader would check. The other two were rows I had broken myself that same session: a gate row missing
its trailing pipe, and a row containing an unescaped `|cos|`.

None of the existing guards could see any of it. `retraction_sweep` reads text, `canonical_figures`
reads numbers, `verify_report_numbers` reads numbers; nothing checked whether a reader would SEE the
cell a number sits in. A figure that renders into the wrong column is as misleading as a wrong figure,
and cheaper to introduce -- one unescaped pipe.

DELIBERATELY NARROW. This checks cell counts against the header, and that a table has a separator row.
It does not lint prose, headings, or links. A pipe inside inline code (`a|b`) still counts as a
separator in most renderers, so it is counted here too -- escaping it is the fix, which is what the
report now does for `\\|cos\\|`.
"""
from __future__ import annotations

import argparse
import re
import sys

DELIVERABLES = [
    "reports/boombness_objective_sprint_report.md",
    "reports/boombness_objective_sprint_short_update.md",
    "docs/BOOMBNESS_SPRINT_PROGRESS.md",
    "docs/BOOMBNESS_CONTINUATION_LOG.md",
]
SEP = re.compile(r"^\s*\|[-: |]+\|\s*$")
CELL = re.compile(r"(?<!\\)\|")


def check(path):
    """Also flags a RUN OF PIPE LINES WITH NO SEPARATOR (audit #11).

    The docstring promised this and the code did not do it: `check()` only entered a table when it saw
    a separator, so a pipe-run without one was invisible. The live cost was four §0 gate rows --
    including the FINAL outcome label -- rendering as a run-on paragraph of pipe characters while this
    guard printed "76 tables, 0 problems". Restoring that table's header immediately exposed a 4-cell
    row the guard had never been able to see.

    Also whitespace-tolerant now (`lines[i].startswith("|")` skipped indented tables entirely, leaving
    three live tables unexamined), matching `retraction_sweep`'s `stripped.startswith("|")`.
    """
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except OSError:
        return [], 0
    problems, n_tables, i = [], 0, 0
    while i < len(lines) - 1:
        s_i = lines[i].strip()
        if s_i.startswith("|") and SEP.match(lines[i + 1] or ""):
            n_tables += 1
            hdr = len(CELL.findall(lines[i])) - 1
            sep = len(CELL.findall(lines[i + 1])) - 1
            if sep != hdr:
                problems.append((i + 2, f"separator has {sep} cells, header has {hdr}"))
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                c = len(CELL.findall(lines[j])) - 1
                if c != hdr:
                    problems.append((j + 1, f"row has {c} cells, header has {hdr}"
                                            f" :: {lines[j][:70]}"))
                j += 1
            i = j
        elif s_i.startswith("|") and not SEP.match(lines[i + 1] or ""):
            # a pipe-run with no separator: renders as prose, not a table
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            if j - i >= 2:                      # two or more consecutive pipe lines
                problems.append((i + 1, f"{j - i} consecutive pipe lines with NO separator row — "
                                        f"renders as prose, not a table :: {lines[i][:60]}"))
            i = j
        else:
            i += 1
    return problems, n_tables


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paths", nargs="*", default=DELIVERABLES)
    args = ap.parse_args()
    total = 0
    for p in args.paths:
        probs, n = check(p)
        total += len(probs)
        print(f"  {p:52s} {n:3d} tables, {len(probs)} problem(s)")
        for ln, msg in probs[:10]:
            print(f"      line {ln}: {msg}")
    if total:
        print(f"\n[md-structure] {total} table cell-count problem(s) — a figure in the wrong column "
              f"misleads as much as a wrong figure")
        return 1
    print("\n[md-structure] every table's rows match its header")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
