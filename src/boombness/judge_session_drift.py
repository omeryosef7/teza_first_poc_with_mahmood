"""judge_session_drift.py — how much does the SAME text score differently in different judge sessions,
and is any layer's in-subspace verdict inside that noise?

WHY THIS EXISTS.

`insubspace_null_by_layer.json` reports, per layer, an arm delta and the largest in-subspace control
delta, and the report claimed on that basis that "the arm exceeds every in-subspace control at all four
layers". Every one of those deltas is `arm_ASR - baseline_ASR`. What was never checked is that the arm,
the controls and the baseline were **judged in different sessions**: at L6 the 20 controls span FIVE
judging sessions (20260821_124554 / _162827 / _173739, 20260822_163302 / _165021) and all are
differenced against a baseline judged in a SIXTH (abg_base, 20260819).

If the judge drifts between sessions, that drift lands directly in every cross-session delta. This
measures the drift the only way that is airtight: the same generation directory, judged repeatedly.
Byte-identical text, so any difference is the judge.

WHAT IT DOES NOT DO. It does not re-run the null with session-matched baselines -- that is impossible
from current data, because the of-4 and of-12 control sessions have no baseline of their own. It
measures the noise floor and reports which layers' margins sit inside it. Fixing the null requires
re-judging the controls with a baseline in each session.

Numeric fields only (`malicious_at_0.5`); no generation or judge text is read or emitted.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402


def gens_of(d: str):
    try:
        a = json.load(open(os.path.join(d, "config.json")))
        a = a.get("args", a)
        g = str(a.get("gens") or "").rstrip("/")
        if not g:
            return None
        return os.path.basename(os.path.dirname(g) if g.endswith("gens.jsonl") else g)
    except Exception:
        return None


def asr(d: str):
    n = k = 0
    ids = {}
    try:
        for line in open(os.path.join(d, "results.jsonl"), encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            v = r.get("malicious_at_0.5")
            if v is None:
                continue
            n += 1
            k += 1 if v else 0
            pid = r.get("prompt_id")
            if pid is not None:
                ids[pid] = 1 if v else 0
    except OSError:
        return None, 0, {}
    return (k / n if n else None), n, ids


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge-glob", default="outputs/boombness/judge/*base*")
    ap.add_argument("--null", default="outputs/boombness/insubspace_null_by_layer.json")
    ap.add_argument("--min-coverage", type=float, default=0.9,
                    help="keep judgings with >= this fraction of the best row count for the same "
                         "generations; declared, not tuned -- see the comment on v2")
    ap.add_argument("--min-sessions", type=int, default=2,
                    help="a gens dir needs at least this many judgings to estimate drift")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    by = defaultdict(list)
    excluded = []
    for d in sorted(glob.glob(a.judge_glob)):
        if not os.path.isdir(d):
            continue
        v, n, ids = asr(d)
        if v is None:
            continue
        g = gens_of(d)
        m = re.search(r"_(\d{8}_\d{6})_\d+$", os.path.basename(d))
        rec = {"session": m.group(1) if m else "?", "judge": os.path.basename(d),
               "asr": v, "n": n, "done": os.path.exists(os.path.join(d, "DONE.json")),
               "_ids": ids}
        by[g].append(rec)

    # v4 (2026-08-23, audit #14): DONE.json, not a coverage fraction -- and INTERSECT the ids.
    #
    # v1 dropped anything under 400 absolute rows, calling it "truncated". False: ClearHarm's bank IS
    # 179 rows.
    #
    # v2 dropped anything below the max n for the same generations. That removed `ab_base` at 483/495
    # and I rejected it for the stated reason that 483/495 is "a complete run missing 12 rows, NOT an
    # in-flight one".
    #
    # THAT REASON WAS FACTUALLY WRONG, and audit #14 caught it. `ab_base_20260819_002240` has no
    # DONE.json, no summary.json and no metadata.json -- the three files the judge writes only on
    # completion -- and its 12 missing rows are exactly positions 483-494 of the run order, a
    # contiguous tail. It is a killed job. Worse, NONE of the 12 dropped rows is malicious, so the
    # truncation inflates that pass's ASR by +0.0016 with no judge involvement at all, and it was
    # supplying the MAXIMUM that set the whole drift figure.
    #
    # So: require DONE.json (the same test `insubspace_null_test._rows` already applies -- this script
    # was the second of two code paths that must agree, and it did not), and compare passes on the
    # INTERSECTION of their prompt ids, so a denominator difference can never masquerade as drift.
    for g, v in list(by.items()):
        keep, drop = [], []
        for r in v:
            (keep if r.get("done") else drop).append(r)
        for r in drop:
            excluded.append({**r, "gens": g,
                             "why": "no DONE.json: a truncated prefix, not a session. Its ASR is "
                                    "computed over a different denominator and cannot be differenced "
                                    "against complete passes."})
        by[g] = keep

    groups = []
    for g, v in sorted(by.items()):
        if len(v) < a.min_sessions:
            continue
        v.sort(key=lambda r: r["session"])
        # SAME POPULATION OR IT IS NOT DRIFT. Intersect the prompt ids across passes before scoring,
        # so "the judge moved" can never be a different denominator wearing the same name.
        common = set.intersection(*(set(r["_ids"]) for r in v)) if v else set()
        if not common:
            for r in v:
                r.pop("_ids", None)
            continue          # nothing scoreable in common: not a drift estimate
        for r in v:
            r["asr_common"] = (sum(r["_ids"][i] for i in common) / len(common)) if common else None
            r.pop("_ids", None)
        lo = min(r["asr_common"] for r in v)
        hi = max(r["asr_common"] for r in v)
        groups.append({"gens": g, "n_sessions": len(v), "n_common": len(common),
                       "asr_min": lo, "asr_max": hi, "drift": hi - lo,
                       "scored_on": "intersection of prompt ids across passes", "passes": v})

    # The AdvBench baseline is the one the in-subspace null differences against.
    ab = max((gp for gp in groups), key=lambda gp: gp["n_sessions"], default=None)
    drift = ab["drift"] if ab else None

    layers = []
    if drift is not None and os.path.exists(a.null):
        nd = json.load(open(a.null))
        for L, lay in sorted(nd.get("layers", {}).items(),
                             key=lambda kv: int(str(kv[0]).lstrip("L"))):
            arm = (lay.get("arm") or {}).get("delta")
            mx = lay.get("max_control_delta")
            # use the artifact's OWN margin field rather than recomputing it, so this cannot
            # silently disagree with the number the null already publishes.
            margin = lay.get("margin_over_max_control")
            if arm is None or mx is None or margin is None:
                continue
            layers.append({
                "layer": int(str(L).lstrip("L")), "arm_delta": arm, "max_control_delta": mx,
                "margin": margin,
                "margin_over_drift": (margin / drift) if drift else None,
                "inside_session_noise": bool(margin < 2 * drift),
            })

    out = {
        "question": "is any layer's 'arm exceeds every in-subspace control' margin inside "
                    "judge-session noise?",
        "method": "same generation directory judged in >1 session; byte-identical text, so any ASR "
                  "difference is the judge. Partial runs excluded -- truncation is not drift.",
        "advbench_baseline_drift": drift,
        "min_coverage": a.min_coverage,
        "coverage_rule_history": (
            "v1 excluded <400 absolute rows (wrong: ClearHarm's bank is 179). v2 excluded anything "
            "below the max n for the same generations, which dropped ab_base at 483/495 = 97.6% -- "
            "the highest-ASR run in the group -- collapsing drift 0.0057->0.0020 and flipping L6. "
            "v3 keeps >= min_coverage of the best. Recorded because the rule moved the headline."),
        "drift_groups": groups,
        "excluded_partial_runs": excluded,
        "layers": layers,
        "verdict": (
            "Margins below 2x the drift cannot be distinguished from judging-session assignment. "
            "This does NOT prove those layers are null; it proves the comparison as computed is not "
            "session-controlled and must not be reported as 'the arm exceeds every control'."),
        "what_would_fix_it": (
            "re-judge every control with a baseline judged in the SAME session, and difference within "
            "session. Not possible from current data: the of-4 and of-12 control sessions have no "
            "baseline of their own."),
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"AdvBench baseline judged in {ab['n_sessions'] if ab else 0} sessions "
          f"(byte-identical generations)")
    if ab:
        print(f"   scored on {ab['n_common']} common prompt ids")
        for r in ab["passes"]:
            print(f"   {r['session']}  {r['judge'][:34]:36s} ASR={r['asr_common']:.4f}  n={r['n']}")
        print(f"   -> session drift = {drift:.4f}")
    for e in excluded:
        print(f"   [excluded] {e['judge'][:34]:36s} {e['why']}")
    print(f"\n{'layer':>6}{'arm':>10}{'maxctrl':>10}{'margin':>10}{'margin/drift':>14}   verdict")
    for l in layers:
        print(f"{l['layer']:>6}{l['arm_delta']:>10.4f}{l['max_control_delta']:>10.4f}"
              f"{l['margin']:>10.4f}{l['margin_over_drift']:>14.2f}   "
              f"{'INSIDE session noise' if l['inside_session_noise'] else 'survives'}")
    print(f"\n[drift] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
