"""empty_goal_leakage_check.py — which artifacts rest on runs judged against an EMPTY GOAL?

THE DEFECT CLASS. `judge_boombness.make_goal` builds the request a completion is scored against from
the bank's `final_query_text`. When no bank is passed (`--bank null`) and the gens carry no
`final_query_text`, it returns an EMPTY goal, and StrongReject then rates how harmful the *response*
is with nothing to compare it to. Scores still look plausible because they track refusal rate. This is
retraction R-14.

WHY A SCANNER AND NOT A PATTERN. R-14 was policed by a `retraction_sweep` rule that matched ClearHarm's
specific numbers. So when the identical defect appeared in the Qwen3 L20 arms, the sweep ran clean and
the report published it — and `unwritten_findings_check`, knowing only ClearHarm was retracted, offered
the tainted Qwen3 artifacts up as findings that *should* be written. A guard tied to figures cannot
generalise to the next instance of its own defect. This one is tied to the data.

THE TEST, which is mechanical:
  a run is EMPTY-GOAL if every row lacks `goal_status` (it predates the field, added 2026-08-19)
  AND its judge config has `bank: null` — so no bank could have supplied the request.
Runs that predate the field but DID pass a bank recover a real goal through the join and are clean;
"field absent" alone is not evidence, which is why both conditions are required.

Then: every artifact citing an empty-goal run is flagged, and separately whether the deliverables
quote that artifact's numbers — because an unquoted tainted artifact is a hazard, and a quoted one is
a live defect.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402

DELIVERABLES = ("reports/boombness_objective_sprint_report.md",
                "reports/boombness_objective_sprint_short_update.md")
#: index/meta artifacts that legitimately enumerate every run, tainted ones included
INDEXES = ("unanalysed_inventory.json", "unanalysed_triage.json", "judge_session_drift.json",
           "shard_citation_check.json", "unwritten_findings_check.json",
           "empty_goal_leakage_check.json", "replicate_noise.json", "population_index.json")


def classify(d):
    """(is_empty_goal, reason). Requires BOTH no goal_status anywhere AND bank: null."""
    f = os.path.join(d, "results.jsonl")
    if not os.path.exists(f):
        return False, "no results.jsonl"
    seen_status = False
    n = 0
    for line in open(f, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        n += 1
        if r.get("goal_status") is not None:
            seen_status = True
            break
    if seen_status:
        return False, "has goal_status"
    try:
        a = json.load(open(os.path.join(d, "config.json")))
        a = a.get("args", a)
    except Exception:
        return False, "unreadable config"
    if a.get("bank"):
        return False, "no goal_status field (pre-2026-08-19) but a bank WAS passed: goal recovered"
    return True, f"no goal_status on any of {n} rows AND bank is null: goal was EMPTY"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    empty, clean_pre = [], []
    for d in sorted(glob.glob("outputs/boombness/judge/*")):
        if not os.path.isdir(d):
            continue
        bad, why = classify(d)
        if bad:
            empty.append({"run": os.path.basename(d), "why": why})
        elif why.startswith("no goal_status field"):
            clean_pre.append(os.path.basename(d))

    names = {e["run"] for e in empty}
    text = ""
    for p in DELIVERABLES:
        try:
            text += io.open(p, encoding="utf-8").read()
        except OSError:
            pass

    flagged = []
    for p in sorted(glob.glob("outputs/boombness/*.json")):
        b = os.path.basename(p)
        if b in INDEXES:
            continue
        try:
            blob = open(p, encoding="utf-8").read()
        except OSError:
            continue
        cited = sorted(n for n in names if n in blob)
        if not cited:
            continue
        flagged.append({
            "artifact": b,
            "empty_goal_runs_cited": cited,
            "artifact_named_in_a_deliverable": (b in text or b.replace(".json", "") in text),
        })

    live = [f for f in flagged if f["artifact_named_in_a_deliverable"]]
    out = {
        "question": "which committed artifacts rest on judge runs scored against an EMPTY GOAL (R-14)?",
        "test": "a run is empty-goal iff NO row carries `goal_status` (the field postdates it) AND its "
                "judge config has `bank: null`. Pre-field runs that DID pass a bank recover the goal "
                "through the join and are clean -- 'field absent' alone is not evidence.",
        "why_not_a_figure_pattern": (
            "R-14 was policed by a retraction_sweep rule matching ClearHarm's specific numbers, so the "
            "identical defect in the Qwen3 L20 arms passed clean and was published. A guard tied to "
            "figures cannot generalise to the next instance of its own defect."),
        "n_empty_goal_runs": len(empty),
        "empty_goal_runs": empty,
        "n_prefield_but_banked_and_therefore_clean": len(clean_pre),
        "n_artifacts_resting_on_them": len(flagged),
        "artifacts": flagged,
        "LIVE_in_a_deliverable": live,
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"empty-goal judge runs: {len(empty)}")
    print(f"pre-field but banked (clean): {len(clean_pre)}")
    print(f"artifacts resting on an empty-goal run: {len(flagged)}")
    for f_ in flagged:
        mark = "LIVE IN DELIVERABLE" if f_["artifact_named_in_a_deliverable"] else "not quoted"
        print(f"   {f_['artifact'][:46]:48s} {len(f_['empty_goal_runs_cited'])} run(s)  [{mark}]")
    print(f"\n*** LIVE defects: {len(live)} ***")
    print(f"\n[empty-goal] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
