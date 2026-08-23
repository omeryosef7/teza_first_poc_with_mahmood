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

UPGRADED 2026-08-23 AFTER IT MISSED TWO MIS-ATTRIBUTIONS. Filename-presence was too weak. Audit #17
found Q5 attributing `p 0.658` -- which belongs to `g2_analysis_cwpos_CLEAN` -- to the *retracted*
`g2_analysis_cwpos`, and Q5b naming the retracted `g9_three_predictor_lastpos` while every figure in
its table came from `..._lastpos_CLEAN`. Both answers named *a* file, so both scored "sourced", and the
check reported 0 flagged. Naming a file is not sourcing a number.

So each quoted figure is now checked against the artifacts THAT ANSWER NAMES. A figure found in none of
them is reported -- either the citation is wrong or the figure is unsourced, and both are worth a look.
The corpus-wide float-collision problem does not arise here, because the search space is the handful of
files the answer itself points at rather than all ~200.

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


def _values(path):
    """Every float in an artifact, rendered at 3 and 4 decimals, sign dropped."""
    def walk(o, out, d=0):
        if d > 7:
            return
        if isinstance(o, dict):
            for v in o.values():
                walk(v, out, d + 1)
        elif isinstance(o, list):
            for v in o[:6000]:
                walk(v, out, d + 1)
        elif isinstance(o, float) and 1e-6 < abs(o) < 1e6:
            out.add(f"{abs(o):.4f}")
            out.add(f"{abs(o):.3f}")
    s = set()
    try:
        walk(json.load(open(path)), s)
    except Exception:
        pass
    return s


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
        # Do the quoted figures actually occur in the artifacts this answer names?
        named_vals = set()
        for nm in named:
            for cand in (f"outputs/boombness/{nm}", *glob.glob(f"outputs/boombness/*/{nm}")):
                if os.path.exists(cand):
                    named_vals |= _values(cand)
                    break
        missing = sorted(f for f in figs
                         if f"{float(f):.4f}" not in named_vals and f"{float(f):.3f}" not in named_vals)
        rows.append({
            "answer": m.group(1), "title": m.group(2).strip(),
            "artifacts_named": named, "n_distinct_figures_quoted": len(figs),
            "figures_not_found_in_named_artifacts": missing,
            "n_figures_unaccounted": len(missing),
            "verdict": ("no figures quoted -- nothing to source" if not figs
                        else "QUOTES FIGURES BUT NAMES NO ARTIFACT" if not named
                        else "sourced" if not missing
                        else f"NAMES AN ARTIFACT BUT {len(missing)} FIGURE(S) ARE NOT IN IT"),
        })

    flagged = [r for r in rows
               if r["verdict"].startswith("QUOTES") or r["verdict"].startswith("NAMES")]
    out = {
        "question": "does each §19 answer name the committed artifact its numbers come from?",
        "why_not_number_matching": (
            "two earlier versions tried to infer provenance from numeric coverage. v1 called nearly "
            "everything traceable including Q2, which traces to nothing; v2's permutation null came "
            "out at ~0.90 for every answer, random figures scoring as well as real ones. With ~200 "
            "artifacts holding tens of thousands of floats, numeric coverage carries no information."),
        # WHAT THE HITS ACTUALLY ARE, triaged 2026-08-23 on the first run of the upgraded check.
        # Several categories are unaccounted BY CONSTRUCTION and always will be, so a bare count
        # over-reads. Recorded here so a NEW hit stands out against a known set.
        "hit_triage": {
            "Q5 0.0832 / 0.572":
                "GENUINE. The core2x2 pair is in no artifact -- _CLEAN is built with "
                "--require-bank-block core2x2,extra_conditions,role_style,families -> n=90 and holds "
                "no core2x2-only subset. This is the hit audit #17 found and the reason for the "
                "upgrade.",
            "Q8 0.175 / 0.972":
                "BENIGN. These are the RETRACTED F and p (R-6), quoted in the answer precisely as "
                "withdrawn. A retracted figure should not be in the live artifact.",
            "Q4 0.0625 / 0.125":
                "BENIGN. Dose parameters (gap-unit gains), not measurements.",
            "Q3b 0.031 / 0.315":
                "BENIGN. 2/2^6 = 0.031 is the six-domain cluster floor; 0.315 is the option mass of "
                "the gate-passing runs. Both are context, not results.",
            "Q2 0.004": "BENIGN. A threshold in 'all p < 0.004'.",
            "Q9 0.4524 etc / Q10 eight figures":
                "PARTIAL. These answers quote figures from MORE sources than they name -- Q9's "
                "topical separation comes from the Qwen3 regoal recompute, Q10's bank figures from "
                "the §12 discussion. Not wrong, under-cited.",
        },
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
