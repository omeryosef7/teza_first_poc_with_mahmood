"""check_all.py — run every deliverable guard, and fail if any of them fails.

WHY. Five guards now exist, each added after a failure it would have caught:

  retraction_sweep          a retracted claim resurfacing in a live document
  canonical_figures         a headline figure drifting between the two deliverables
  verify_report_numbers     a quoted number no longer matching its committed artifact
  markdown_structure_check  a cell rendering in the wrong column
  pvalue_hygiene_check      a small p quoted without its design's attainable floor
  plan_coverage_check       a plan section silently dropped from the report

Until now I ran them as an ad-hoc shell loop, by hand, once per tick -- and on at least one tick ran
four of the five. A guard you have to remember to run is a guard you will eventually not run, which is
the same class of problem as a rule applied only where an auditor pointed. One entry point, one exit
code.

Exit 0 only if EVERY guard passes. Deliberately no `--skip`: a guard worth disabling is worth deleting,
and a guard that is failing is the moment you most want the build red.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

GUARDS = [
    ("retraction_sweep", [sys.executable, os.path.join(HERE, "retraction_sweep.py")],
     "a retracted claim resurfacing in a live document"),
    ("canonical_figures", [sys.executable, os.path.join(HERE, "canonical_figures.py")],
     "a headline figure drifting between deliverables"),
    ("verify_report_numbers",
     [sys.executable, os.path.join(ROOT, "scripts", "verify_report_numbers.py")],
     "a quoted number no longer matching its artifact"),
    ("markdown_structure_check", [sys.executable, os.path.join(HERE, "markdown_structure_check.py")],
     "a cell rendering in the wrong column"),
    ("pvalue_hygiene_check", [sys.executable, os.path.join(HERE, "pvalue_hygiene_check.py")],
     "a small p quoted without its design's floor"),
    ("plan_coverage_check", [sys.executable, os.path.join(HERE, "plan_coverage_check.py")],
     "a plan section silently dropped from the report"),
    ("ledger_propagation_check",
     [sys.executable, os.path.join(HERE, "ledger_propagation_check.py")],
     "a correction written in the plan and never reaching the claim ledger"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true", help="print each guard's full output")
    args = ap.parse_args()
    failed = []
    print(f"  {'guard':26s} {'exit':>5s}  guards against")
    for name, cmd, why in GUARDS:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        mark = "ok" if r.returncode == 0 else "FAIL"
        print(f"  {name:26s} {r.returncode:5d}  {why}" + ("" if r.returncode == 0 else "   <-- " + mark))
        if r.returncode != 0:
            failed.append(name)
            # ⛔ This printed the last 6 non-empty lines (audit #11). `retraction_sweep` prints its
            # FINDINGS first and a 4-line essay about heuristics last, so the tail showed the essay and
            # zero findings -- observed directly on three planted mutations. Prefer lines that look
            # like findings; fall back to the tail only if none match.
            out = [l for l in (r.stdout or "").split("\n") if l.strip()]
            findings = [l for l in out if re.search(
                r"UNQUALIFIED|PROBLEM|FAIL|MISMATCH|NOT QUOTED|NOT COMMITTED|STILL ASSERTED|"
                r"row has|separator|cells|REFUSING", l)]
            for l in (findings[:6] if findings else out[-6:]):
                print(f"        {l[:150]}")
        elif args.verbose:
            print((r.stdout or "").rstrip())
    if failed:
        print(f"\n[check-all] {len(failed)} of {len(GUARDS)} guards FAILED: {', '.join(failed)}")
        return 1
    print(f"\n[check-all] all {len(GUARDS)} deliverable guards pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
