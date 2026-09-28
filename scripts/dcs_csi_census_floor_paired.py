#!/usr/bin/env python3
"""PAIRED bootstrap on the DIFFERENCE between two option-mass floors, for ONE census family.

WHY THIS EXISTS AND WHY IT IS NOT THE CENSUS (S-559). The census
(`scripts/dcs_csi_head_census.py`) computes, for each arm, E and a domain-clustered bootstrap ci95
-- at ONE option-mass floor per invocation. S-558 compared the point estimates of two such runs
(floor 0.0 vs 0.05) and reported percentage movements with NO interval, which is the defect S-558
itself recorded as not-established.

Reaching for the two artefacts' MARGINAL ci95s would be the WRONG repair. Both floors are computed
over the SAME 23 validation domains, and the floor-0.05 row set is a strict SUBSET of the floor-0.0
row set, so the two estimates are strongly positively correlated. Two overlapping marginal intervals
say nothing about whether the DIFFERENCE excludes zero -- the comparison has to be paired, resampling
the domain vector ONCE per replicate and evaluating BOTH floors on that same resample.

WHAT IT SHARES. Every quantity that must mean the same thing as the census means the same thing here
because it is the SAME CODE: `w4.by_domain` (hence the sole `load_installation`), the census's own
`_option_mass_keys`, `rederive.strict_run_dir`, and `w4.pct` for the quantiles. E is re-derived here
rather than read from the artefacts, so the point estimates this script prints are an independent
check on S-558's table rather than a restatement of it.

WHAT IT DOES NOT DO. It freezes nothing, ranks nothing and emits no verdict: PR-CSI-012 declares NO
detectability block and NO `layers` at all, so this family HAS no preregistered bar to clear. The
`--anchor-arm` ratio is reported because D34 is written against an effect-built anchor that no prereg
froze (S-556); putting an interval on that ratio does not make it preregistered.
"""
import argparse, importlib.util, json, math, os, random, statistics, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


w4 = _load("w4", os.path.join(REPO, "scripts", "dcs_csi_head_analyze.py"))
rederive = _load("rederive", os.path.join(REPO, "scripts", "dcs_csi_rederive_patch.py"))
census = _load("census", os.path.join(REPO, "scripts", "dcs_csi_head_census.py"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--base-arm", default="HD_BASE")
    ap.add_argument("--arms", required=True, help="comma-separated arms to compare")
    ap.add_argument("--anchor-arm", default=None,
                    help="arm whose |E| D34 uses as its (never-preregistered, effect-built) anchor")
    ap.add_argument("--floor", type=float, default=0.05)
    ap.add_argument("--reference", required=True, help="arm the floor's key set is built from")
    ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--B", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20260922)
    ap.add_argument("--ci", type=float, default=0.95)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.floor <= 0.0:
        sys.exit("REFUSING: --floor must be > 0; the control branch IS floor 0 and is run here "
                 "unconditionally. A 'paired' comparison of a floor against itself is vacuous.")

    arms = [s for s in a.arms.split(",") if s]
    need = [a.base_arm] + arms + ([a.anchor_arm] if a.anchor_arm else [])
    dirs = {}
    for arm in sorted(set(need)):
        dirs[arm] = rederive.strict_run_dir("%s_%s" % (a.tag_prefix, arm), a.expect_n,
                                            row_file="results.jsonl", allow_short=a.allow_short)

    if a.reference not in dirs:
        sys.exit("REFUSING: --reference %r is not among the arms this run loads (%s). The key set "
                 "must come from an arm this script actually reads, or the floor is keyed on "
                 "something unverified. (PR-CSI-025 VOID 7: BASE arms are NOT uniformly named.)"
                 % (a.reference, ",".join(sorted(dirs))))
    keep, n_ref, n_kept = census._option_mass_keys(dirs[a.reference], a.floor)
    if not keep:
        sys.exit("REFUSING: floor %g retains ZERO keys from %s." % (a.floor, a.reference))
    print("[floor] %.3f on %s: %d of %d rows retained (%.4f)"
          % (a.floor, a.reference, n_kept, n_ref, float(n_kept) / n_ref))

    # BOTH branches, from the same dirs, differing ONLY in keep_keys.
    ctrl = {arm: w4.by_domain(dirs[arm], keep_keys=None)[0] for arm in dirs}
    flr = {arm: w4.by_domain(dirs[arm], keep_keys=keep)[0] for arm in dirs}

    dc = set.intersection(*(set(v) for v in ctrl.values()))
    df = set.intersection(*(set(v) for v in flr.values()))
    if dc != df:
        sys.exit("REFUSING: the floor changes the DOMAIN set (%d -> %d; lost %s). A paired bootstrap "
                 "over a domain vector that is not the same vector is not paired."
                 % (len(dc), len(df), sorted(dc - df)[:5]))
    doms = sorted(dc)
    print("[paired] domains common to every arm under BOTH floors = %d" % len(doms))

    def vec(branch, arm):
        return [branch[arm][d] - branch[a.base_arm][d] for d in doms]

    V = {arm: {"ctrl": vec(ctrl, arm), "flr": vec(flr, arm)} for arm in set(arms) | set(
        [a.anchor_arm] if a.anchor_arm else [])}

    def stats_on(idx):
        """Every statistic, evaluated on ONE shared resample of the domain vector."""
        out = {}
        for arm, v in V.items():
            ec = statistics.fmean([v["ctrl"][i] for i in idx])
            ef = statistics.fmean([v["flr"][i] for i in idx])
            out[arm] = {"E_ctrl": ec, "E_flr": ef, "abs_ctrl": abs(ec), "abs_flr": abs(ef)}
        for arm in out:
            d = out[arm]
            d["delta_abs"] = d["abs_flr"] - d["abs_ctrl"]
            d["pct"] = (100.0 * d["delta_abs"] / d["abs_ctrl"]) if d["abs_ctrl"] else None
            if a.anchor_arm:
                an = out[a.anchor_arm]["abs_flr"]
                d["margin_flr"] = (d["abs_flr"] / an) if an else None
        return out

    n = len(doms)
    point = stats_on(list(range(n)))
    rng = random.Random(a.seed)
    draws = {arm: {} for arm in V}
    for _ in range(a.B):
        idx = [rng.randrange(n) for _ in range(n)]
        s = stats_on(idx)
        for arm in V:
            for k, val in s[arm].items():
                if val is not None:
                    draws[arm].setdefault(k, []).append(val)

    lo_q, hi_q = (1 - a.ci) / 2.0, 1 - (1 - a.ci) / 2.0
    res = {}
    for arm in V:
        res[arm] = {}
        for k, xs in draws[arm].items():
            res[arm][k] = {"point": point[arm][k],
                           "ci95": [w4.pct(xs, lo_q), w4.pct(xs, hi_q)],
                           "n_draws": len(xs)}

    print("\n[paired] |E| MOVEMENT under the floor, ci95 from a PAIRED bootstrap (B=%d seed=%d)"
          % (a.B, a.seed))
    print("   %-11s %-22s %-24s %s" % ("arm", "|E| ctrl -> |E| floor", "delta (ci95)", "pct (ci95)"))
    for arm in arms:
        r = res[arm]
        p = r["pct"]
        print("   %-11s %.6f -> %.6f  %+.6f [%+.6f,%+.6f]  %+.1f%% [%+.1f,%+.1f]"
              % (arm, point[arm]["abs_ctrl"], point[arm]["abs_flr"],
                 r["delta_abs"]["point"], r["delta_abs"]["ci95"][0], r["delta_abs"]["ci95"][1],
                 p["point"], p["ci95"][0], p["ci95"][1]))
        excl = (r["delta_abs"]["ci95"][1] < 0) or (r["delta_abs"]["ci95"][0] > 0)
        print("   %-11s movement ci95 %s 0" % ("", "EXCLUDES" if excl else "INCLUDES"))

    if a.anchor_arm:
        print("\n[paired] MARGIN over the anchor |E(%s)| at floor %.2f -- the anchor is EFFECT-BUILT "
              "and NO prereg froze it (S-556)." % (a.anchor_arm, a.floor))
        for arm in arms:
            m = res[arm].get("margin_flr")
            if not m:
                continue
            if arm == a.anchor_arm:
                # 1.0 by construction, with a degenerate [1,1] interval. Printing "above" or
                # "below" here states a comparison that does not exist.
                verdict = "THE ANCHOR ITSELF -- 1.0 by construction, not a measurement"
            elif m["ci95"][0] < 1.0 < m["ci95"][1]:
                verdict = "STRADDLES 1.0 -- clears or fails is UNDECIDED"
            elif m["ci95"][0] > 1.0:
                verdict = "above 1.0"
            else:
                verdict = "below 1.0"
            print("   %-11s margin %.3fx  ci95 [%.3f, %.3f]   %s"
                  % (arm, m["point"], m["ci95"][0], m["ci95"][1], verdict))

    blob = {"schema": "dcs_csi_census_floor_paired/1", "tag_prefix": a.tag_prefix,
            "floor": a.floor, "reference": a.reference, "base_arm": a.base_arm,
            "anchor_arm": a.anchor_arm, "n_domains": len(doms), "B": a.B, "seed": a.seed,
            "ci": a.ci, "n_rows_in_reference": n_ref, "n_keys_retained": n_kept,
            "frac_retained": round(float(n_kept) / n_ref, 6),
            "PAIRED": ("the domain vector is resampled ONCE per replicate and BOTH floors are "
                       "evaluated on that resample; the floor row set is a SUBSET of the control's, "
                       "so the marginal ci95s in the two census artefacts are NOT a valid "
                       "comparison of the difference"),
            "NO_PREREGISTERED_BAR": ("PR-CSI-012 declares no DETECTABILITY block and no `layers`; "
                                     "this family froze effects-with-intervals and NO threshold, so "
                                     "nothing here clears or fails a preregistered bar"),
            "NO_VERDICT": True, "results": res}
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(blob, fh, indent=1, sort_keys=True)
        print("\n[wrote] %s" % a.out)


if __name__ == "__main__":
    main()
