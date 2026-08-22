"""null_ceiling_session_check.py — is the in-subspace null's CEILING a judging-session artifact?

WHY. The dense null reports, per layer, an arm delta and the largest control delta, and the whole
"the arm exceeds every control" claim is a comparison against that ceiling. `judge_session_drift.py`
showed the judge moves ~2.8 prompts in 495 between sessions. If the controls that SET the ceiling all
come from one judging session, the ceiling is partly a property of that session rather than of any
direction -- and at L6 the arm-vs-ceiling margin is only 4 prompts, so a session offset of 2-3 prompts
is decisive.

This does not assume a bias exists. It measures whether the ceiling is concentrated: per layer it
reports each control's delta in PROMPTS, groups by judging session, and asks (a) which session supplies
the maximum, (b) how far that session's mean sits from the other sessions', and (c) whether that
session has a baseline of its own or is being differenced against a baseline from elsewhere.

WHAT IT CANNOT SEPARATE. Session is confounded with WHICH ANGLES were judged in it -- the sweeps were
submitted in waves, and a wave is both a set of angles and a session. So a session mean differing from
another is not proof of judge drift; it could be a real property of those angles. That confound is
stated in the artifact, not resolved by it. The fix is to re-judge a few angles across sessions, which
no committed data supports yet.

Numeric/categorical only.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import insubspace_null_test as M  # noqa: E402
from unanalysed_inventory import git_commit_safe  # noqa: E402

N_ROWS = 495


def asr_of(pattern):
    tot = k = 0
    dirs = sorted(glob.glob(pattern))
    for d in dirs:
        f = os.path.join(d, "results.jsonl")
        if not os.path.exists(f):
            continue
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            v = r.get("malicious_at_0.5")
            if v is None:
                continue
            tot += 1
            k += 1 if v else 0
    return ((k / tot) if tot else None), tot, [os.path.basename(x) for x in dirs]


def sess_of(name):
    m = re.search(r"_(\d{8}_\d{6})_\d+$", name)
    return m.group(1) if m else "?"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--layers", default="6,8,10,12")
    ap.add_argument("--n-angles", type=int, default=24)
    ap.add_argument("--baseline", default="outputs/boombness/judge/abg_base_*")
    ap.add_argument("--dense", default="outputs/boombness/insubspace_null_dense20.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    base, _, _ = asr_of(a.baseline)
    dense = json.load(open(a.dense))["layers"]
    sessions_with_base = {sess_of(os.path.basename(d))
                          for d in glob.glob("outputs/boombness/judge/*base*")
                          if os.path.isdir(d)}

    out_layers = {}
    for L in [int(x) for x in a.layers.split(",")]:
        ctrls = []
        for k in range(a.n_angles):
            v, n, dirs = asr_of(M.angle_glob(L, k, a.n_angles))
            if v is None or not n:
                continue
            ctrls.append({"k_of_24": k, "asr": v, "n": n,
                          "delta_prompts": round((v - base) * N_ROWS),
                          "session": sess_of(dirs[0]), "run": dirs[0]})
        if not ctrls:
            continue
        arm = (dense.get(f"L{L}", {}).get("arm") or {}).get("delta")
        arm_p = round(arm * N_ROWS) if arm is not None else None
        by = {}
        for c in ctrls:
            by.setdefault(c["session"], []).append(c["delta_prompts"])
        stats = {s: {"n": len(v), "mean_prompts": sum(v) / len(v), "max_prompts": max(v),
                     "has_own_baseline": s in sessions_with_base}
                 for s, v in by.items()}
        top = max(ctrls, key=lambda c: c["delta_prompts"])
        ceiling = top["delta_prompts"]
        setters = [c for c in ctrls if c["delta_prompts"] == ceiling]
        setter_sessions = sorted({c["session"] for c in setters})
        others = [v for s, st in stats.items() if s not in setter_sessions for v in by[s]]
        gap = (min(stats[s]["mean_prompts"] for s in setter_sessions)
               - (sum(others) / len(others))) if others else None
        # TWO BOUNDS ON THE NOISE, because neither alone is honest.
        #   lower: baseline drift, 2.8 prompts -- pure judge noise, measured on byte-identical text.
        #   upper: the spread of per-session MEAN control deltas -- judge noise PLUS whatever is
        #          really different about the angles judged in that wave. It over-states noise.
        # A margin below the upper bound is not safe; a margin above it is. Sessions contributing a
        # single control are excluded from the spread: one run's mean is that run, not a session.
        multi = {s: st for s, st in stats.items() if st["n"] >= 2}
        spread = (max(st["mean_prompts"] for st in multi.values())
                  - min(st["mean_prompts"] for st in multi.values())) if len(multi) >= 2 else None
        out_layers[f"L{L}"] = {
            "session_mean_spread_prompts": spread,
            "n_sessions_with_2plus_controls": len(multi),
            "noise_bounds_prompts": {"lower_baseline_drift": 2.8, "upper_session_spread": spread},
            "margin_exceeds_upper_bound": (None if spread is None or arm_p is None
                                           else (arm_p - ceiling) > spread),
            "arm_delta_prompts": arm_p, "ceiling_prompts": ceiling,
            "margin_prompts": (arm_p - ceiling) if arm_p is not None else None,
            "ceiling_set_by_sessions": setter_sessions,
            "n_controls_at_ceiling": len(setters),
            "ceiling_sessions_have_own_baseline": {s: (s in sessions_with_base)
                                                   for s in setter_sessions},
            "ceiling_session_mean_minus_others_prompts": gap,
            "per_session": stats, "controls": sorted(ctrls, key=lambda c: -c["delta_prompts"]),
        }

    out = {
        "question": "is the null's ceiling concentrated in one judging session, and does that session "
                    "have a baseline of its own?",
        "baseline_asr": base, "baseline_pattern": a.baseline, "n_rows": N_ROWS,
        "judge_drift_prompts": 2.8,
        "CONFOUND_NOT_RESOLVED": (
            "session is confounded with WHICH ANGLES were judged in it -- the sweeps were submitted in "
            "waves, and a wave is both a set of angles and a session. A session mean differing from "
            "another is therefore NOT proof of judge drift; it could be a real property of those "
            "angles. Separating them needs the same angles judged in two sessions, which no committed "
            "data supports."),
        "layers": out_layers,
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"baseline {base:.4f} = {base*N_ROWS:.0f}/{N_ROWS}   judge drift ~2.8 prompts\n")
    for L, v in out_layers.items():
        print(f"{L}: arm {v['arm_delta_prompts']}p   ceiling {v['ceiling_prompts']}p   "
              f"margin {v['margin_prompts']}p")
        print(f"   ceiling set by {v['n_controls_at_ceiling']} control(s) in session(s) "
              f"{v['ceiling_set_by_sessions']}  own_baseline={list(v['ceiling_sessions_have_own_baseline'].values())}")
        sp = v.get("session_mean_spread_prompts")
        if isinstance(sp, float):
            print(f"   session-mean spread {sp:.1f}p (n>=2 sessions)  -> margin "
                  f"{'EXCEEDS' if v['margin_exceeds_upper_bound'] else 'INSIDE'} the upper noise bound")
        g = v["ceiling_session_mean_minus_others_prompts"]
        if isinstance(g, float):
            print(f"   that session's mean is {g:+.1f} prompts vs the other sessions")
        for s, st in sorted(v["per_session"].items()):
            print(f"      {s}  n={st['n']:<3} mean={st['mean_prompts']:+.1f}p  max={st['max_prompts']:+d}p"
                  f"  own_base={st['has_own_baseline']}")
        print()
    print(f"[null-ceiling] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
