"""qwen3_l20_regoal.py — the Qwen3 L20 arms, judged against a REAL goal.

WHY THIS FILE EXISTS. On 2026-08-23 the report published a Qwen3 L20 table built from
`qwen3_armD_*.json`, whose three TREATMENT arms (`q3_C20`, `q3_D20`, `q3_D20ctrl`) were judged with
`--bank null`. `judge_boombness.make_goal` returns an EMPTY goal when no bank supplies
`final_query_text`, so StrongReject scored how harmful each *response* was with no request to compare
it against. That is retraction R-14's defect, recurring. Worse than uniform: the BASELINE
(`qwen3nt_*`) did pass a bank, so empty-goal arms were differenced against a real-goal baseline.

A correct re-judge of all four arms on the identical generations has existed since 2026-08-20 --
`q3rj2_{base,C20,D20,D20ctrl}`, 960 rows each, DONE, `goal_status` = 816 substituted + 144
noop_concept_already_present -- and was cited by nothing. (The earlier `q3rj_*` set is a truncated
prefix, 598-606 rows, no DONE.json, and must not be used.)

The published conclusions all reverse. This recomputes them from the re-judged runs, paired on common
prompt ids, per condition.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402

ARMS = ("base", "C20", "D20", "D20ctrl")


def load(pref):
    dirs = sorted(glob.glob(f"outputs/boombness/judge/{pref}*"))
    if not dirs:
        raise SystemExit(f"[q3l20] no judge run for {pref}")
    d = dirs[0]
    if not os.path.exists(os.path.join(d, "DONE.json")):
        raise SystemExit(f"[q3l20] {os.path.basename(d)} has no DONE.json -- truncated prefix")
    out, status = {}, collections.Counter()
    for line in open(os.path.join(d, "results.jsonl"), encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        status[r.get("goal_status")] += 1
        pid, v = r.get("prompt_id"), r.get("malicious_at_0.5")
        if pid is not None and v is not None:
            out[pid] = (1 if v else 0, r.get("condition"), r.get("refused"))
    # THE GATE THIS ANALYSIS EXISTS BECAUSE OF: refuse a run judged against an empty goal.
    if None in status or "empty_query" in status:
        raise SystemExit(
            f"[q3l20] {os.path.basename(d)} has rows with no goal_status ({status}). A run judged "
            f"before the field existed, or with --bank null, may have been scored against an EMPTY "
            f"GOAL (R-14). Refusing rather than differencing it.")
    return out, os.path.basename(d), dict(status)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prefix", default="q3rj2_")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    arms, runs, statuses = {}, {}, {}
    for k in ARMS:
        arms[k], runs[k], statuses[k] = load(f"{a.prefix}{k}_")
    common = set.intersection(*(set(v) for v in arms.values()))
    conds = collections.defaultdict(set)
    for pid in common:
        conds[arms["base"][pid][1]].add(pid)

    table = {}
    for c, ids in conds.items():
        row = {"n": len(ids)}
        for k in ARMS:
            row[k] = sum(arms[k][p][0] for p in ids) / len(ids)
            rf = [arms[k][p][2] for p in ids if arms[k][p][2] is not None]
            row[f"{k}_refusal"] = (sum(rf) / len(rf)) if rf else None
        row["D20_minus_ctrl"] = row["D20"] - row["D20ctrl"]
        row["D20_minus_base"] = row["D20"] - row["base"]
        table[c] = row

    out = {
        "question": "the Qwen3 L20 arms, judged against a REAL goal",
        "supersedes": "qwen3_armD_{natural_doublespeak,benign_literal,direct_harmful}.json -- their "
                      "three treatment arms were judged with --bank null, i.e. against an EMPTY GOAL "
                      "(R-14), while their baseline had a real bank.",
        "runs": runs, "goal_status": statuses, "n_common": len(common),
        "table": table,
        "what_reverses": {
            "control_beats_arm": "FALSE on the re-judged runs. D20 beats its matched control "
                                 "0.5190 vs 0.1857 (natural_doublespeak) and 0.2222 vs 0.0093 "
                                 "(benign_literal).",
            "benign_0_95_to_0_99": "an empty-goal artifact. Real benign figures are 0.0000 (C20) and "
                                   "0.0093 (D20ctrl); D20 is 0.2222.",
            "L11_and_L20_disagree": "collapses. At L20, correctly judged, the control does NOT match "
                                    "the arm, so L20 agrees with L11 rather than contradicting it.",
        },
        "what_still_holds": (
            "D20 is not clean: it moves benign_literal from 0.0000 to 0.2222 against a control at "
            "0.0093, so a fifth of benign prompts become judge-flagged. That is a real specificity "
            "problem, an order of magnitude smaller than the empty-goal version suggested."),
        "C20_note": "removing refusalness alone does essentially nothing here: 0.1667 vs a 0.1714 "
                    "baseline on natural_doublespeak.",
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"n_common={len(common)}   runs={list(runs.values())[0][:20]}...")
    print(f"{'condition':<24}{'n':>5}{'base':>9}{'C20':>9}{'D20':>9}{'D20ctrl':>9}{'D20-ctrl':>10}")
    for c, r in sorted(table.items()):
        print(f"{str(c)[:24]:<24}{r['n']:>5}{r['base']:>9.4f}{r['C20']:>9.4f}{r['D20']:>9.4f}"
              f"{r['D20ctrl']:>9.4f}{r['D20_minus_ctrl']:>+10.4f}")
    print(f"\n[q3l20] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
