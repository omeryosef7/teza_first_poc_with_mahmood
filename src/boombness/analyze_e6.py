"""analyze_e6.py — plan §14 / E6: does the attention-edge result hold for a SECOND codeword?

E6 replaces `carrot` with `button` (concept unchanged) and re-runs the §10 knockout arms with
directions still fitted on the CARROT bank. It therefore asks one question: is `d_surface` a
carrot-detector, or does it carry something that survives a change of codeword?

READ THE CEILING FIRST. Every knockout number below must be read against the two reference arms the
module provides, because a delta of +0.1 means nothing without knowing the range:

  * `no_demo_text`  — delete the demonstration text outright. This is the TRUE ceiling.
  * `positive_control` — the hook firing at full strength. If this does not move, the knockout is
    not firing at all and every "no effect" is a statement about the hook, not about attention.

Written after the 2026-08-20 audit found two numbers of mine living only in shell heredocs. Every
number this file prints is written to its `--out` artifact with provenance.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import statistics as st
import subprocess
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl  # noqa: E402

CEILING = ("no_demo_text", "positive_control")


def arm_deltas(run_dir: str) -> Dict[str, Dict]:
    rows = list(read_jsonl(os.path.join(run_dir, "results.jsonl")))
    by: Dict[str, Dict[str, float]] = collections.defaultdict(dict)
    for r in rows:
        if r.get("semantic_logodds") is None:
            continue
        by[r["prompt_id"]][r["arm"]] = r["semantic_logodds"]
    out = {}
    for a in sorted({x for v in by.values() for x in v} - {"none"}):
        d = [v[a] - v["none"] for v in by.values() if a in v and "none" in v]
        if not d:
            continue
        sd = st.stdev(d) if len(d) > 1 else 0.0
        out[a] = {"mean": st.mean(d), "sem": sd / (len(d) ** 0.5) if d else None, "n": len(d)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="outputs/boombness/surgical_knockout")
    ap.add_argument("--pattern", action="append", required=True,
                    metavar="MODEL:SCOPE:GLOB",
                    help="e.g. llama:first_codeword:btn_firstcw_*  (repeatable)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    res: Dict[str, Dict] = {}
    runs: Dict[str, str] = {}
    for spec in args.pattern:
        model, scope, pat = spec.split(":", 2)
        hits = sorted(glob.glob(os.path.join(args.root, pat)))
        if not hits:
            raise SystemExit(f"[e6] no run matching {pat!r}")
        d = hits[-1]
        summ = json.load(open(os.path.join(d, "summary.json")))
        gate = str(summ.get("option_mass_gate"))
        if not gate.startswith("PASS"):
            raise SystemExit(
                f"[e6] REFUSING: {os.path.basename(d)} did not pass its option-mass gate ({gate}). "
                "A knockout delta computed on a tail readout is not evidence.")
        runs[f"{model}/{scope}"] = os.path.abspath(d)
        res.setdefault(model, {})[scope] = arm_deltas(d)

    # the verdict is a RATIO to the ceiling, not a raw delta
    verdict = {}
    for model, scopes in res.items():
        any_scope = next(iter(scopes.values()))
        ceil = any_scope.get("no_demo_text", {}).get("mean")
        pos = any_scope.get("positive_control", {}).get("mean")
        knock = [(s, a, v["mean"]) for s, arms in scopes.items() for a, v in arms.items()
                 if a not in CEILING]
        biggest = max(knock, key=lambda t: abs(t[2])) if knock else None
        verdict[model] = {
            "ceiling_no_demo_text": ceil,
            "positive_control": pos,
            "positive_control_frac_of_ceiling": (pos / ceil) if (ceil and pos) else None,
            "largest_knockout_arm": {"scope": biggest[0], "arm": biggest[1],
                                     "mean": biggest[2],
                                     "frac_of_ceiling": abs(biggest[2] / ceil) if ceil else None}
            if biggest else None,
            "signs_by_scope_all_demo": {s: (arms.get("all_demo", {}).get("mean"))
                                        for s, arms in scopes.items()},
        }

    out = {"plan_section": "14 / E6", "codeword": "button", "concept": "bomb",
           "directions_fitted_on": "the CARROT bank — E6 tests transfer, not refitting",
           "runs": runs, "deltas_vs_none": res, "verdict": verdict,
           "provenance": {"argv": sys.argv,
                          "git_commit": subprocess.run(["git", "rev-parse", "HEAD"],
                                                       capture_output=True, text=True).stdout.strip()}}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)

    for model, v in verdict.items():
        print(f"[e6] {model}: ceiling(no_demo_text)={v['ceiling_no_demo_text']:+.3f}  "
              f"positive_control={v['positive_control']:+.3f} "
              f"({100*v['positive_control_frac_of_ceiling']:.1f}% of ceiling)")
        b = v["largest_knockout_arm"]
        print(f"       largest knockout arm: {b['arm']} @ {b['scope']} = {b['mean']:+.4f} "
              f"= {100*b['frac_of_ceiling']:.2f}% of the ceiling")
        print(f"       all_demo by scope: " +
              "  ".join(f"{s}={m:+.4f}" for s, m in v["signs_by_scope_all_demo"].items()))
    print(f"[e6] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
