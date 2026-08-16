"""analyze_g1_g3.py — the G1 (§5) and G3 (§10) tables, committed and reproducible.

WHY THIS EXISTS. The G2 table was computed in a shell heredoc, was wrong in four ways, and its
headline verdict inverted once the audit forced it into a script. G1 and G3 were produced the same
ad-hoc way, so they carry the same risk. This script regenerates both from their run dirs, and adds
the two things the tick-16 audit said they were missing:

  * G1's effects are quoted as a PERCENTAGE OF A SPAN whose endpoints (baseline and donor ceiling)
    are estimated from the same n=8 families. That denominator is noisy and the percentage inherits
    it. Here the span uncertainty is PROPAGATED and the percentage is reported with an interval,
    not as a point estimate.

  * G3's positive control was supposed to establish that the readout CAN move. It moved the readout
    LESS than the arm it was meant to validate (-0.086 vs +0.117 for `all_demo`), so it establishes
    no dynamic range at all — a null against it is uninterpretable. This script reports the
    positive control's effect ALONGSIDE every arm and refuses to call anything a null when the
    positive control is not clearly larger than the arms.

Prints the tables and writes JSON, so every quoted number traces to a command.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl  # noqa: E402


def mean_sem(xs: Sequence[float]):
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    if not xs:
        return float("nan"), float("nan"), 0
    m = sum(xs) / len(xs)
    if len(xs) < 2:
        return m, float("nan"), len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
    return m, sd / math.sqrt(len(xs)), len(xs)


def g1(run: str, readout: str = "semantic_logodds") -> Dict:
    rows = read_jsonl(os.path.join(run, "results.jsonl"))
    out: Dict[str, object] = {"run": os.path.abspath(run), "readout": readout, "pairs": {}}
    for pair in sorted({r["pair"] for r in rows}):
        h = [r for r in rows if r["pair"] == pair]
        b_m, b_s, b_n = mean_sem([r[readout] for r in h if r["intervention"] == "none"])
        c_m, c_s, c_n = mean_sem([r[readout] for r in h if r["intervention"] == "donor_ceiling"])
        span = c_m - b_m
        # Propagate the span's own uncertainty into every percentage (independent endpoints).
        span_sem = math.sqrt((b_s ** 2) + (c_s ** 2)) if math.isfinite(b_s) and math.isfinite(c_s) else float("nan")
        sw = [r[readout] for r in h if r["intervention"] == "self_swap_noop_check"]
        base_by_pid = {r["recipient_prompt_id"]: r[readout] for r in h if r["intervention"] == "none"}
        sw_max = max((abs(r[readout] - base_by_pid.get(r["recipient_prompt_id"], r[readout]))
                      for r in h if r["intervention"] == "self_swap_noop_check"), default=float("nan"))

        arms = {}
        for iv in ("transplant", "add"):
            for scope in sorted({r.get("scope") for r in h if r["intervention"] == iv}):
                for win in sorted({r.get("window") for r in h if r["intervention"] == iv
                                   and r.get("scope") == scope}):
                    sel = [r for r in h if r["intervention"] == iv and r.get("scope") == scope
                           and r.get("window") == win]
                    for dname in sorted({r.get("direction", "") for r in sel}):
                        for alpha in sorted({r.get("alpha", 0.0) for r in sel
                                             if r.get("direction", "") == dname}):
                            ss = [r for r in sel if r.get("direction", "") == dname
                                  and r.get("alpha", 0.0) == alpha]
                            m, s, n = mean_sem([r[readout] for r in ss])
                            if not n:
                                continue
                            frac = (m - b_m) / span if abs(span) > 1e-9 else float("nan")
                            # delta method for frac = (m - b)/(c - b)
                            if all(map(math.isfinite, (s, b_s, span_sem))) and abs(span) > 1e-9:
                                fs = abs(frac) * math.sqrt(
                                    ((s ** 2 + b_s ** 2) / max((m - b_m) ** 2, 1e-12))
                                    + (span_sem ** 2) / (span ** 2))
                            else:
                                fs = float("nan")
                            key = f"{iv}|{scope}|{win}" + (f"|{dname}|a={alpha}" if dname else "")
                            arms[key] = {"mean": m, "sem": s, "n": n,
                                         "frac_of_span": frac, "frac_sem": fs,
                                         "frac_ci95": [frac - 1.96 * fs, frac + 1.96 * fs]
                                         if math.isfinite(fs) else [float("nan")] * 2}
        out["pairs"][pair] = {
            "baseline": {"mean": b_m, "sem": b_s, "n": b_n},
            "donor_ceiling": {"mean": c_m, "sem": c_s, "n": c_n},
            "span": span, "span_sem": span_sem,
            "self_swap_max_abs_delta": sw_max,
            "arms": arms,
        }
    return out


def g3(run: str, readout: str = "semantic_logodds") -> Dict:
    rows = read_jsonl(os.path.join(run, "results.jsonl"))
    base = {r["prompt_id"]: r[readout] for r in rows if r["arm"] == "none"}
    out: Dict[str, object] = {"run": os.path.abspath(run), "readout": readout, "arms": {}}
    for arm in sorted({r["arm"] for r in rows}):
        ss = [r for r in rows if r["arm"] == arm]
        d = [r[readout] - base[r["prompt_id"]] for r in ss if r["prompt_id"] in base]
        m, s, n = mean_sem(d)
        ec, _, _ = mean_sem([r.get("n_edges_cut", 0) for r in ss])
        out["arms"][arm] = {"delta_mean": m, "delta_sem": s, "n": n, "mean_edges_cut": ec}
    pc = out["arms"].get("positive_control", {}).get("delta_mean", float("nan"))
    biggest_other = max((v["delta_mean"] for k, v in out["arms"].items()
                         if k not in ("none", "positive_control")
                         and math.isfinite(v.get("delta_mean", float("nan")))), default=float("nan"))
    out["positive_control_delta"] = pc
    out["largest_non_control_delta"] = biggest_other
    out["dynamic_range_established"] = bool(
        math.isfinite(pc) and math.isfinite(biggest_other) and abs(pc) > 3 * abs(biggest_other))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--g1-run", default=None)
    ap.add_argument("--g3-run", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    report: Dict[str, object] = {}

    if args.g1_run:
        r = g1(args.g1_run)
        report["G1"] = r
        for pair, d in r["pairs"].items():
            print(f"\n=== G1 pair={pair}  baseline {d['baseline']['mean']:+.3f}"
                  f" (n={d['baseline']['n']})  ceiling {d['donor_ceiling']['mean']:+.3f}"
                  f"  span {d['span']:+.3f} ± {d['span_sem']:.3f} ===")
            print(f"  self-swap max |Δ| = {d['self_swap_max_abs_delta']:.2e} (must be ~0)")
            print(f"  {'arm':44s} {'mean':>9s} {'% of span':>11s} {'95% CI on %':>22s}")
            for k, v in sorted(d["arms"].items(), key=lambda kv: -abs(kv[1]["frac_of_span"])):
                lo, hi = v["frac_ci95"]
                print(f"  {k:44s} {v['mean']:>+9.3f} {100*v['frac_of_span']:>10.1f}% "
                      f"{f'[{100*lo:+.0f}%, {100*hi:+.0f}%]':>22s}")

    if args.g3_run:
        r = g3(args.g3_run)
        report["G3"] = r
        print(f"\n=== G3 {os.path.basename(args.g3_run)} ===")
        print(f"  {'arm':20s} {'Δ readout':>12s} {'sem':>8s} {'edges':>8s}")
        for k, v in sorted(r["arms"].items(), key=lambda kv: -abs(kv[1]["delta_mean"])):
            print(f"  {k:20s} {v['delta_mean']:>+12.3f} {v['delta_sem']:>8.3f} {v['mean_edges_cut']:>8.0f}")
        print(f"\n  positive control Δ = {r['positive_control_delta']:+.3f}; "
              f"largest other arm Δ = {r['largest_non_control_delta']:+.3f}")
        if not r["dynamic_range_established"]:
            print("  ** NO DYNAMIC RANGE ESTABLISHED ** The positive control does not dominate the "
                  "arms it is meant to validate, so a null in any arm is UNINTERPRETABLE: the "
                  "readout has not been shown to be movable by an intervention of this kind. "
                  "G3 must not be reported as a null until a control with real dynamic range "
                  "(e.g. removing the demonstrations from the prompt entirely) is added.")
        else:
            print("  dynamic range OK: the positive control dominates the other arms.")

    out = args.out or "g1_g3_analysis.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
