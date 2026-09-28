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
import argparse, importlib.util, json, math, os, random, re, statistics, sys

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
    ap.add_argument("--min-rows", type=int, default=3,
                    help="refuse if any domain retains fewer than this many rows under the floor "
                         "(R42-C1/S-561: equal-domain weighting gives a 1-row domain full weight)")
    ap.add_argument("--B", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20260922)
    ap.add_argument("--ci", type=float, default=0.95)
    # R42-M4/F6 (S-564). --out was OPTIONAL and no artefact was ever written, so the intervals
    # S-559/S-561/S-562 rest on lived only in a terminal and then only in the log. The census's own
    # --out is required=True and its S-549 comment states the rule: "A sensitivity whose floor lives
    # only in a terminal has exactly that defect."
    ap.add_argument("--out", required=True,
                    help="artefact path; REQUIRED (R42-M4). Written atomically via w4.")
    # R42-M3 (S-564). This reader called strict_run_dir with no slurm filter, while the census's
    # frozen read passes --require-slurm-job <VALIDATION_JOB_IDS>. rederive's own R8-B1 note records
    # why that matters: when exactly one directory survived the completeness check the filters never
    # ran, so a lone directory from the WRONG allocation was returned (the S-104b near-miss).
    ap.add_argument("--require-slurm-job", default=None,
                    help="comma-separated slurm job id(s) every arm dir must belong to (R42-M3)")
    a = ap.parse_args()

    # R42-M5 (S-562). Every interval used to be printed AND serialized under the literal key
    # "ci95" whatever --ci said. Reproduced: `--ci 0.50` printed
    # "SINGLE_02 -7.0% [-13.8,-0.4] / movement ci95 EXCLUDES 0" -- the published reading for that arm
    # is INCLUDES 0. A one-character typo produced a wrong-but-plausible publishable line whose only
    # label was the false string "ci95". The label is now derived from the value, so it cannot lie.
    CIL = "ci%g" % round(a.ci * 100)

    if a.floor <= 0.0:
        sys.exit("REFUSING: --floor must be > 0; the control branch IS floor 0 and is run here "
                 "unconditionally. A 'paired' comparison of a floor against itself is vacuous.")

    arms = [s for s in a.arms.split(",") if s]
    need = [a.base_arm] + arms + ([a.anchor_arm] if a.anchor_arm else [])
    jobs = a.require_slurm_job.split(",") if a.require_slurm_job else None
    dirs = {}
    for arm in sorted(set(need)):
        dirs[arm] = rederive.strict_run_dir("%s_%s" % (a.tag_prefix, arm), a.expect_n,
                                            row_file="results.jsonl", allow_short=a.allow_short,
                                            require_slurm_jobs=jobs)

    # ---- R42-M3: ARM IDENTITY, from each arm's OWN record, not from its directory name ------------
    # The census asserts every arm against its recorded `knockout_heads` because S-246 measured that a
    # 1-head arm's DOSE is indistinguishable from the all-32 arm's -- so a dose that looks right
    # certifies nothing. This reader resolved arms by TAG NAME ALONE, which means a directory called
    # `..._SINGLE_19` produced by a config that knocked out a different head would have been published
    # as SINGLE_19, inside a tool whose whole purpose is checking another tool's numbers.
    # For SINGLE_<hh> the expected set is derivable from the arm name with no prereg; for the
    # set-valued arms it is not, so their record is REQUIRED TO EXIST and is written into the artefact
    # rather than silently trusted (R20-6: a check whose PASS is consistent with reading nothing is
    # not a check).
    identity = {}
    for arm, d in sorted(dirs.items()):
        got = census.recorded_heads(d)
        if got is None:
            sys.exit("REFUSING: arm %s (%s) has NO knockout_heads field, so its identity cannot be "
                     "asserted from its own record. Absence is not a value. (R42-M3/S-564)"
                     % (arm, os.path.basename(d)))
        if arm == a.base_arm:
            # ⚠ S-564, caught on my OWN artefact before it shipped. `recorded_heads` maps an EMPTY
            # knockout_heads to the string "ALL" (S-292), and the base arm's field IS empty -- so
            # recording `got` verbatim publishes "HD_BASE": "ALL", which reads as "the clean reference
            # knocked out all 32 heads", the exact opposite of the truth. That is the ACTIVELY
            # CONCEALS defect R30-A/S-332 fixed in the census, reintroduced here by reusing its helper
            # without its interpretation. The base arm must carry NO head list, and is recorded as
            # what it is.
            if got not in (None, "ALL", [], ""):
                sys.exit("REFUSING: base arm %s records knockout_heads=%r -- a base arm carrying an "
                         "intervention flag is not a clean reference. (R30-A/S-564)" % (arm, got))
            identity[arm] = "EMPTY -- no intervention flag (the helper's 'ALL' means EMPTY here, S-292)"
            continue
        identity[arm] = got
        m = re.match(r"^SINGLE_(\d+)$", arm)
        if m:
            want = [int(m.group(1))]
            if got != want:
                sys.exit("REFUSING: arm %s records knockout_heads=%r, not %r. The directory name says "
                         "one head and the run's own config says another -- resolving arms by tag "
                         "name alone is how that gets published. (R42-M3/S-564)" % (arm, got, want))
    print("[identity] %d arms asserted from their own knockout_heads (%d SINGLE_* name-checked)"
          % (len(identity), sum(1 for k in identity if re.match(r"^SINGLE_\d+$", k))))

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

    # ---- R42-C1/F1, S-561, S-562: PER-DOMAIN RETENTION, DISCLOSED --------------------------------
    # The domain-SET check above is what licensed the sentence "both floors are computed over the
    # SAME 23 domains". That is true of the SET and conceals the thinning: on the published csi5 run
    # the floor takes domains from a uniform 10 rows to 1..10, and `freight_yard` keeps ONE row which
    # equal-domain weighting then hands 1/23 of the estimate. S-561 found that by leave-one-out three
    # entries after the numbers were published. `by_domain` returns the per-domain SLOT SET precisely
    # so this cannot happen silently (its R15-3 docstring) and the first version of this file threw it
    # away with `[0]`. It is now printed and serialized, and a domain thinned below --min-rows refuses.
    inst_f, _, _ = w4.lpm.load_installation(dirs[a.reference], keep_keys=keep)
    inst_c, _, _ = w4.lpm.load_installation(dirs[a.reference], keep_keys=None)
    rpd = {}
    for (d, _s) in inst_f:
        rpd[d] = rpd.get(d, 0) + 1
    hist = {}
    for v in rpd.values():
        hist[v] = hist.get(v, 0) + 1
    thin = sorted((v, d) for d, v in rpd.items())[:3]
    print("[retention] rows per domain on %s: min %d, median %.1f, histogram %s"
          % (a.reference, min(rpd.values()),
             statistics.median(sorted(rpd.values())), dict(sorted(hist.items()))))
    print("[retention] thinnest: %s" % ", ".join("%s=%d" % (d, v) for v, d in thin))
    if min(rpd.values()) < a.min_rows:
        sys.exit("REFUSING: domain %r retains %d row(s) under floor %g, below --min-rows %d. E "
                 "weights every domain EQUALLY regardless of rows retained, so that domain's mean "
                 "is one row carrying 1/%d of the estimate. Measured on csi5: freight_yard's single "
                 "row carried 37.8%% of the anchor's floor effect and its removal took the anchor's "
                 "movement from +35.1%% to -0.2%%. Pass --min-rows 1 to proceed deliberately. "
                 "(R42-C1/S-561/S-562)"
                 % (thin[0][1], thin[0][0], a.floor, a.min_rows, len(doms)))

    # ---- the SLOT-POOLED counterfactual, which is NOT post hoc -----------------------------------
    # At floor 0.0 every domain has the same row count, so domain-equal and slot-pooled averaging are
    # IDENTICAL BY CONSTRUCTION. Their divergence at any floor > 0 is therefore an exact decomposition
    # of "readout-validity effect" vs "re-weighting artefact" over the FULL preregistered population --
    # no domain dropped, nothing post hoc. Measured on csi5 floor 0.05: HD_BOTK's movement is +35.1%
    # domain-equal and -7.5% pooled, i.e. THE SIGN REVERSES, and it is the only arm of seven that does.
    raw = {arm: {"c": w4.lpm.load_installation(dirs[arm], keep_keys=None)[0],
                 "f": w4.lpm.load_installation(dirs[arm], keep_keys=keep)[0]} for arm in dirs}

    def pooled(arm, br):
        A, B = raw[arm][br], raw[a.base_arm][br]
        ks = [k for k in A if k[0] in dc and k in B]
        return statistics.fmean([float(A[k]) - float(B[k]) for k in ks])

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
            # R42-m9: a quantile taken from fewer than B draws is not the interval it claims to be.
            if len(xs) != a.B:
                sys.exit("REFUSING: statistic %r on arm %s has %d of %d draws -- replicates were "
                         "silently dropped, so this interval is conditional on something the label "
                         "does not state. (R42-m9/S-562)" % (k, arm, len(xs), a.B))
            res[arm][k] = {"point": point[arm][k], CIL: [w4.pct(xs, lo_q), w4.pct(xs, hi_q)],
                           "n_draws": len(xs)}

    print("\n[paired] |E| MOVEMENT under the floor, %s from a PAIRED bootstrap (B=%d seed=%d)"
          % (CIL, a.B, a.seed))
    print("   %-11s %-22s %-24s %s"
          % ("arm", "|E| ctrl -> |E| floor", "delta (%s)" % CIL, "pct (%s)" % CIL))
    for arm in arms:
        r = res[arm]
        if "pct" not in r:
            sys.exit("REFUSING: arm %s has no percentage movement because its CONTROL |E| is "
                     "identically 0 -- that happens when --arms contains the base arm %r, whose "
                     "difference against itself is 0 in every domain. Naming the symptom "
                     "(KeyError: 'pct') instead of the cause is the S-295 defect. (R42-M6/S-562)"
                     % (arm, a.base_arm))
        p = r["pct"]
        print("   %-11s %.6f -> %.6f  %+.6f [%+.6f,%+.6f]  %+.1f%% [%+.1f,%+.1f]"
              % (arm, point[arm]["abs_ctrl"], point[arm]["abs_flr"],
                 r["delta_abs"]["point"], r["delta_abs"][CIL][0], r["delta_abs"][CIL][1],
                 p["point"], p[CIL][0], p[CIL][1]))
        excl = (r["delta_abs"][CIL][1] < 0) or (r["delta_abs"][CIL][0] > 0)
        print("   %-11s movement %s %s 0" % ("", CIL, "EXCLUDES" if excl else "INCLUDES"))

    print("\n[decomp] DOMAIN-EQUAL vs SLOT-POOLED |E| (identical at floor 0.0 BY CONSTRUCTION, so "
          "any divergence here is re-weighting, not readout validity)")
    print("   %-11s %-30s %-30s %s" % ("arm", "equal-weight ctrl -> floor", "pooled ctrl -> floor",
                                       "sign"))
    for arm in arms:
        ec, ef = abs(point[arm]["abs_ctrl"]), abs(point[arm]["abs_flr"])
        pc, pf = abs(pooled(arm, "c")), abs(pooled(arm, "f"))
        rev = (ef - ec) * (pf - pc) < 0
        print("   %-11s %.6f -> %.6f (%+6.1f%%)    %.6f -> %.6f (%+6.1f%%)   %s"
              % (arm, ec, ef, 100.0 * (ef - ec) / ec if ec else float("nan"),
                 pc, pf, 100.0 * (pf - pc) / pc if pc else float("nan"),
                 "REVERSES" if rev else "same"))
        res[arm]["pooled"] = {"abs_ctrl": pc, "abs_flr": pf,
                              "pct": (100.0 * (pf - pc) / pc) if pc else None,
                              "sign_reverses_vs_domain_equal": bool(rev)}

    if a.anchor_arm:
        print("\n[paired] MARGIN over the anchor |E(%s)| at floor %.2f -- the anchor is EFFECT-BUILT "
              "and NO prereg froze it (S-556)." % (a.anchor_arm, a.floor))
        if not any(res[arm].get("margin_flr") for arm in arms):
            sys.exit("REFUSING: no arm has a margin, because the anchor %r has |E| identically 0 in "
                     "every draw. Printing a MARGIN section with no rows and exiting 0 tells a "
                     "reader the margins were computed and were unremarkable. (R42-M7/S-562)"
                     % a.anchor_arm)
        for arm in arms:
            m = res[arm].get("margin_flr")
            if not m:
                continue
            if arm == a.anchor_arm:
                # 1.0 by construction, with a degenerate [1,1] interval. Printing "above" or
                # "below" here states a comparison that does not exist.
                verdict = "THE ANCHOR ITSELF -- 1.0 by construction, not a measurement"
            elif m[CIL][0] <= 1.0 <= m[CIL][1]:
                verdict = "STRADDLES 1.0 -- clears or fails is UNDECIDED"
            elif m[CIL][0] > 1.0:
                verdict = "above 1.0"
            else:
                verdict = "below 1.0"
            print("   %-11s margin %.3fx  %s [%.3f, %.3f]   %s"
                  % (arm, m["point"], CIL, m[CIL][0], m[CIL][1], verdict))

    blob = {"schema": "dcs_csi_census_floor_paired/1", "tag_prefix": a.tag_prefix,
            "floor": a.floor, "reference": a.reference, "base_arm": a.base_arm,
            "anchor_arm": a.anchor_arm, "n_domains": len(doms), "B": a.B, "seed": a.seed,
            "ci": a.ci, "n_rows_in_reference": n_ref, "n_keys_retained": n_kept,
            "frac_retained": round(float(n_kept) / n_ref, 6),
            "run_dirs": {k: os.path.basename(v) for k, v in sorted(dirs.items())},
            "reference_run_dir": os.path.basename(dirs[a.reference]),
            "require_slurm_job": a.require_slurm_job,
            "arm_identity_from_own_knockout_heads": {k: v for k, v in sorted(identity.items())},
            "domains": doms,
            "rows_per_domain": dict(sorted(rpd.items())),
            "rows_per_domain_histogram": {str(k): v for k, v in sorted(hist.items())},
            "min_rows_per_domain": min(rpd.values()), "min_rows_required": a.min_rows,
            "WHY_ROWS_PER_DOMAIN_IS_RECORDED": ("the domain SET is unchanged while the domains are "
                                                "THINNED; equal-domain weighting gives a 1-row "
                                                "domain the same weight as a 10-row one (S-561)"),
            "ci_level": a.ci,
            "PAIRED": ("the domain vector is resampled ONCE per replicate and BOTH floors are "
                       "evaluated on that resample; the floor row set is a SUBSET of the control's, "
                       "so the marginal ci95s in the two census artefacts are NOT a valid "
                       "comparison of the difference"),
            "NO_PREREGISTERED_BAR": ("PR-CSI-012 declares no DETECTABILITY block and no `layers`; "
                                     "this family froze effects-with-intervals and NO threshold, so "
                                     "nothing here clears or fails a preregistered bar"),
            "NO_VERDICT": True, "results": res}
    w4.atomic_write_json(a.out, blob)
    print("\n[wrote] %s" % a.out)


if __name__ == "__main__":
    main()
