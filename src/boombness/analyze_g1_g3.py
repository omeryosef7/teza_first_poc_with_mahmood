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
from common import read_jsonl, require_done  # noqa: E402


def mean_sem(xs: Sequence[float]):
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    if not xs:
        return float("nan"), float("nan"), 0
    m = sum(xs) / len(xs)
    if len(xs) < 2:
        return m, float("nan"), len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
    return m, sd / math.sqrt(len(xs)), len(xs)


def _paired_boot_frac(h, readout, iv, scope, win, dname, alpha, n_boot: int = 20000,
                      seed: int = 20260817) -> Dict:
    """Percentile CI for frac_of_span. Resamples the CLUSTER — the domain — not the family.

    Preserves the within-family pairing of (baseline, ceiling, arm) that the delta method throws away.

    AUDIT 11 (A11-12): this originally resampled FAMILIES, and merely *reported* n_domains alongside.
    Families within a domain share a stem, a demo pool and a target, so a family-level bootstrap on
    the old pilot treated 2 domains as 8 independent units and the published "+57% to +105%" was not
    an 8-unit interval. The sprint's own standard elsewhere (analyze_g2, analyze_g8, analyze_g9,
    reanalyze_corrected, analyze_position) is to cluster on the domain, so this now does too:
    resample DOMAINS with replacement, taking each drawn domain's families wholesale. Both intervals
    are returned — `ci` (clustered, citable) and `ci_family_level_UNDERSTATES` — so the difference the
    fix makes is visible rather than silently swapped in.
    """
    import random as _r
    fam = {}
    for r in h:
        pid = r.get("recipient_prompt_id")
        if pid is None:
            continue
        f = fam.setdefault(pid, {"dom": r.get("domain")})
        if r["intervention"] == "none":
            f["b"] = r[readout]
        elif r["intervention"] == "donor_ceiling":
            f["c"] = r[readout]
        elif (r["intervention"] == iv and r.get("scope") == scope and r.get("window") == win
              and r.get("direction", "") == dname and r.get("alpha", 0.0) == alpha):
            f["a"] = r[readout]
    fams = [v for v in fam.values() if {"b", "c", "a"} <= set(v)]
    ndom = len({v.get("dom") for v in fams})
    if len(fams) < 3:
        return {"ci": [float("nan")] * 2, "n_families": len(fams), "n_domains": ndom}
    rng = _r.Random(seed)
    by_dom: Dict[object, List[Dict]] = {}
    for v in fams:
        by_dom.setdefault(v.get("dom"), []).append(v)
    dom_keys = sorted(by_dom, key=str)

    def _frac(sample):
        b = sum(x["b"] for x in sample) / len(sample)
        c = sum(x["c"] for x in sample) / len(sample)
        a = sum(x["a"] for x in sample) / len(sample)
        return (a - b) / (c - b) if abs(c - b) > 1e-9 else None

    out_dom = []
    for _ in range(n_boot):
        drawn = []
        for _ in range(len(dom_keys)):
            drawn.extend(by_dom[dom_keys[rng.randrange(len(dom_keys))]])
        v = _frac(drawn)
        if v is not None:
            out_dom.append(v)
    out = []
    for _ in range(n_boot):
        s = [fams[rng.randrange(len(fams))] for _ in range(len(fams))]
        b = sum(x["b"] for x in s) / len(s)
        c = sum(x["c"] for x in s) / len(s)
        a = sum(x["a"] for x in s) / len(s)
        if abs(c - b) > 1e-9:
            out.append((a - b) / (c - b))
    if len(out) < 100 or len(out_dom) < 100:
        return {"ci": [float("nan")] * 2, "n_families": len(fams), "n_domains": ndom}
    out.sort()
    out_dom.sort()
    fam_ci = [out[int(0.025 * len(out))], out[int(0.975 * len(out))]]
    dom_ci = [out_dom[int(0.025 * len(out_dom))], out_dom[int(0.975 * len(out_dom))]]
    return {"ci": dom_ci,                      # citable: the cluster is the domain
            "ci_family_level_UNDERSTATES": fam_ci,
            "width_ratio_domain_over_family": (
                (dom_ci[1] - dom_ci[0]) / (fam_ci[1] - fam_ci[0])
                if abs(fam_ci[1] - fam_ci[0]) > 1e-12 else float("nan")),
            "n_families": len(fams), "n_domains": ndom,
            "bootstrap_unit": "domain (families drawn wholesale with their domain)"}


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
                            # PAIRED BOOTSTRAP over families (audit B3b). The delta method above
                            # propagates the span as if baseline and ceiling were INDEPENDENT, but
                            # the design is paired within family and they correlate ~+0.63, so the
                            # delta-method interval is too WIDE. It also used z=1.96 at n=8. The
                            # bootstrap resamples whole families, preserving the pairing.
                            boot = _paired_boot_frac(h, readout, iv, scope, win, dname, alpha)
                            arms[key] = {"mean": m, "sem": s, "n": n,
                                         "frac_of_span": frac, "frac_sem": fs,
                                         "frac_ci95_deltamethod":
                                             [frac - 1.96 * fs, frac + 1.96 * fs]
                                             if math.isfinite(fs) else [float("nan")] * 2,
                                         "frac_ci95_paired_boot": boot["ci"],
                                         "n_families": boot["n_families"],
                                         "n_domains": boot["n_domains"],
                                         "frac_ci95": boot["ci"] if boot["ci"][0] == boot["ci"][0]
                                         else ([frac - 1.96 * fs, frac + 1.96 * fs]
                                               if math.isfinite(fs) else [float("nan")] * 2)}
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
    # BUG FIXED 2026-08-17 (independent audit, B4c). This `max` was taken over the SIGNED deltas.
    # Every real arm here is negative, so it returned `random_nondemo` = +0.031 — a NULL CONTROL —
    # as "the largest non-control effect", and the guard then certified |3.53| > 3*|0.031| = True.
    # The guard exists precisely to stop a null being reported when the positive control does not
    # dominate, and it has been passing VACUOUSLY. Compared on magnitude it is |3.53| > 3*|11.51|
    # = False, which is the correct and much less comfortable answer: `no_demo_text` moves the
    # readout ~3x MORE than the positive control does, so this design does not establish that the
    # positive control bounds the achievable range.
    pc = out["arms"].get("positive_control", {}).get("delta_mean", float("nan"))
    cands = [(k, v["delta_mean"]) for k, v in out["arms"].items()
             if k not in ("none", "positive_control")
             and math.isfinite(v.get("delta_mean", float("nan")))]
    biggest_other, biggest_arm = float("nan"), None
    if cands:
        biggest_arm, biggest_other = max(cands, key=lambda kv: abs(kv[1]))
    out["positive_control_delta"] = pc
    out["largest_non_control_delta"] = biggest_other
    out["largest_non_control_arm"] = biggest_arm
    out["dynamic_range_established"] = bool(
        math.isfinite(pc) and math.isfinite(biggest_other) and abs(pc) > 3 * abs(biggest_other))

    # WHAT THE GUARD IS ACTUALLY FOR, restated 2026-08-17. The question it protects is "is a NULL in
    # some arm interpretable?", and that needs only one thing: proof the readout is MOVABLE at all.
    # Comparing the positive control against `no_demo_text` answers a different question — that arm
    # is the deletion CEILING the percentages are taken as a fraction OF, not an arm awaiting
    # validation — so `dynamic_range_established=False` here must NOT be read as "G3 is invalid".
    # Movability is established, overwhelmingly, by no_demo_text itself.
    # BUG FIXED 2026-08-17 (audit C2/C3). This was a BLACKLIST, so every arm not named in it counted
    # as a "null control" — including the treatment arms `dense_two_layer` and
    # `subsampled_all_layers_demo` added the same day. On the real edgematch run that set the
    # threshold from `dense_two_layer` (0.496) instead of `topk_demo` (0.078), inflating it 6.4x and
    # making it depend on the very effect under test. And when the list came back EMPTY the
    # threshold collapsed to `3 * 0.0`, so floating-point noise certified the readout as movable —
    # the same vacuous-pass shape as the two dead guards already retracted. Whitelist now, and an
    # empty whitelist is UNDEFINED rather than automatically passing.
    NULL_CTRLS = ("topk_demo", "bottomk_demo", "random_demo", "random_nondemo", "same_head_random")
    null_ctrls = [abs(v["delta_mean"]) for k, v in out["arms"].items()
                  if k in NULL_CTRLS and math.isfinite(v.get("delta_mean", float("nan")))]
    if not null_ctrls:
        out["readout_movable"] = None
        out["readout_movable_by"] = []
        out["largest_null_control_abs"] = None
        out["null_claims_interpretable"] = False
        out["movability_note"] = ("no null-control arm present, so movability is UNDEFINED — "
                                  "not passing. A null in any arm is uninterpretable here.")
    else:
        biggest_null_ctrl = max(null_ctrls)
        movers = [(k, v["delta_mean"]) for k, v in out["arms"].items()
                  if k not in ("none",) + NULL_CTRLS
                  and math.isfinite(v.get("delta_mean", float("nan")))
                  and abs(v["delta_mean"]) > 3 * biggest_null_ctrl]
        out["readout_movable"] = bool(movers)
        out["readout_movable_by"] = sorted(k for k, _ in movers)
        out["largest_null_control_abs"] = biggest_null_ctrl
        out["null_claims_interpretable"] = out["readout_movable"]

    # EDGE-COUNT CONFOUND (audit B4a). `all_demo` and `all_layers_demo` cut the SAME per-layer edge
    # set; the only difference is the layer set, so edge count and layer spread move together by
    # exactly 16x. Nothing here separates "redundant across depth" from "a total-edge threshold".
    # Report the ratio so no reader can quote the depth claim without seeing the confound.
    a2 = out["arms"].get("all_demo", {})
    a32 = out["arms"].get("all_layers_demo", {})
    if a2 and a32 and a2.get("mean_edges_cut"):
        out["edge_count_confound"] = {
            "two_layer_edges": a2["mean_edges_cut"], "all_layer_edges": a32["mean_edges_cut"],
            "edge_ratio": a32["mean_edges_cut"] / a2["mean_edges_cut"],
            "identified": False,
            "note": "layer spread and edge count are perfectly confounded; a depth-redundancy "
                    "reading is NOT identified without an edge-count-matched arm "
                    "(subsampled_all_layers_demo) or a layer-matched dense arm (dense_two_layer)."}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--g1-run", default=None)
    ap.add_argument("--g3-run", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--allow-partial", action="store_true",
                    help="analyse a run with no DONE.json (output must not be reported)")

    args = ap.parse_args()
    if args.g1_run:
        require_done(args.g1_run, allow_partial=args.allow_partial)
    if args.g3_run:
        require_done(args.g3_run, allow_partial=args.allow_partial)
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
