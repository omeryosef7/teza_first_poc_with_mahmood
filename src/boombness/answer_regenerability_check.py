"""answer_regenerability_check.py — does each §19 answer NAME the artifact its numbers come from?

THE RULE. Every number in this report must be regenerable by a committed script from a committed
artifact. §19 answers the plan's eleven questions directly, so it is where an untraceable figure does
the most damage.

TWO FAILED APPROACHES FIRST, recorded because the failure is the point.

v1 asked "do this answer's numbers appear in some artifact?" and reported nearly every answer traceable
-- including **Q2**, which had been established by hand the day before to trace to nothing. Its best
match for almost every answer was one per-layer summary holding 32 layers x 6 metrics x 4 roles of
floats. An artifact that large matches any set of 3-4 decimal numbers by chance.

v2 scored that coverage against a permutation null of random figure sets. The null median came out at
**~0.90 for every answer** -- random figures score as well as real ones. With ~200 artifacts holding
tens of thousands of floats, numeric coverage carries no information at either end, so v2 flagged
everything, including answers verified by hand to be exactly traceable.

The lesson is not "tune the threshold". It is that **number-matching cannot establish provenance in
this corpus**, and two versions of a check that cannot go red -- or cannot go green -- are two versions
too many. `unwritten_findings_check` v1 failed the same way.

WHAT THIS DOES INSTEAD. A deterministic question with a checkable answer: does the answer's text name a
committed artifact? That is the provenance link the rule actually asks for, it cannot saturate, and it
is how every answer written since 2026-08-22 is already sourced.

WHAT A MISS MEANS. Q11 is advice and Q6 quotes no figures -- both legitimately name nothing. A miss
matters when an answer quotes specific numbers and points at nothing, which is Q2's exact situation:
its figures were searched for by hand across every artifact and found in none.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402

REPORT = "reports/boombness_objective_sprint_report.md"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    text = io.open(REPORT, encoding="utf-8").read()
    i = text.index("## §19 — the eleven questions, answered directly")
    j = text.index("\n## ", i + 10)
    sec = text[i:j]
    arts = {os.path.basename(p) for p in
            glob.glob("outputs/boombness/*.json") + glob.glob("outputs/boombness/*/*.json")}

    hits = list(re.finditer(r"\n\*\*(\d+[a-z]?)\. ([^*\n]{5,120})\*\*", sec))
    rows = []
    for k, m in enumerate(hits):
        end = hits[k + 1].start() if k + 1 < len(hits) else len(sec)
        body = sec[m.end():end]
        named = sorted({x for x in arts if x.replace(".json", "") in body})
        figs = sorted({g for g in re.findall(r"(?<![\w.])(\d+\.\d{3,4})(?![\d])", body)
                       if not g.endswith("000")})
        rows.append({
            "answer": m.group(1), "title": m.group(2).strip(),
            "artifacts_named": named, "n_distinct_figures_quoted": len(figs),
            "verdict": ("sourced" if named
                        else "no figures quoted -- nothing to source" if not figs
                        else "QUOTES FIGURES BUT NAMES NO ARTIFACT"),
        })

    flagged = [r for r in rows if r["verdict"].startswith("QUOTES")]
    out = {
        "question": "does each §19 answer name the committed artifact its numbers come from?",
        "why_not_number_matching": (
            "two earlier versions tried to infer provenance from numeric coverage. v1 called nearly "
            "everything traceable including Q2, which traces to nothing; v2's permutation null came "
            "out at ~0.90 for every answer, random figures scoring as well as real ones. With ~200 "
            "artifacts holding tens of thousands of floats, numeric coverage carries no information."),
        "n_answers": len(rows), "n_flagged": len(flagged),
        "flagged": flagged, "all": rows,
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"{'ans':<5}{'figs':>5}  {'artifacts named':<50}verdict")
    for r in rows:
        nm = ", ".join(x.replace(".json", "") for x in r["artifacts_named"])[:48] or "-"
        print(f"{r['answer']:<5}{r['n_distinct_figures_quoted']:>5}  {nm:<50}{r['verdict']}")
    print(f"\nflagged: {len(flagged)}")
    print(f"\n[answer-sourcing] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
