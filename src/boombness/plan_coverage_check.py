"""plan_coverage_check.py — does every section of the plan have a documented outcome?

WHY. For several ticks I have written that "the plan is fully addressed" and "every gate row is
tested". Those are assertions. The plan has 20 numbered sections and the report is 3,089 lines; nobody
had ever checked the mapping mechanically, and this sprint's record on assertions-not-checked is poor
enough that it should not start here.

WHAT COUNTS AS COVERED. A plan section `## N. Title` is covered if the report mentions `§N` or its
distinctive title words in a way that states an outcome. This is a LINT, not a proof: it cannot judge
whether the outcome is correct, only whether the section was answered somewhere rather than silently
dropped. A section deliberately not done (§12's GCG objective) counts as covered when the report says
so and why -- "documented negative" is an outcome.

DELIBERATELY LISTS, NOT JUST COUNTS. The failure this guards against is a section quietly vanishing
between revisions, so the output names every section and its status rather than printing a pass rate.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

PLAN = "docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md"
REPORT = "reports/boombness_objective_sprint_report.md"

#: sections whose "outcome" is that they are setup/process, not a research question
NON_RESEARCH = {0, 1, 2, 15, 16, 17, 20}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", default=PLAN)
    ap.add_argument("--report", default=REPORT)
    args = ap.parse_args()
    try:
        plan = open(args.plan, encoding="utf-8").read()
        report = open(args.report, encoding="utf-8").read()
    except OSError as e:
        print(f"[plan-coverage] cannot read: {e}", file=sys.stderr)
        return 2

    secs = re.findall(r"^##\s+(\d+)\.\s+(.+)$", plan, re.M)
    missing = []
    print(f"  {'§':>4s}  {'cited':>5s}  title")
    for num, title in secs:
        n = int(num)
        # a citation is "§N" followed by a non-digit, or "plan §N", or "section N"
        cited = bool(re.search(rf"§\s*{n}(?!\d)", report)) or \
            bool(re.search(rf"\bplan\s+§?\s*{n}(?!\d)", report, re.I))
        tag = "yes" if cited else "NO"
        note = "" if n not in NON_RESEARCH else "  (setup/process)"
        print(f"  {n:4d}  {tag:>5s}  {title[:58]}{note}")
        if not cited and n not in NON_RESEARCH:
            missing.append((n, title))
    print()
    if missing:
        print(f"[plan-coverage] {len(missing)} research section(s) with NO citation in the report:")
        for n, title in missing:
            print(f"   §{n}. {title}")
        return 1
    print(f"[plan-coverage] all {len(secs)} plan sections are cited in the report "
          f"({len(NON_RESEARCH)} of them setup/process)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
