#!/usr/bin/env python3
"""P4 analysis: head-restricted operator (KO_TOP8) vs the fitted random-8-head family (KO_RH8_j, rescaled per
module to TOP8's norm). REUSES p2b_analyze helpers (row_fields, sidecar, dmeans, mean_diff, rank_p, holm, decide)
and, through it, dcs_csi_subspace_analyze (arm_key_values, reference_key_set, effect_fraction,
direction_profile, rederive.strict_run_dir). Unit = domain. PASS rule identical to P2b's decide():
Holm over the PRIMARY ranks {1,4} of the codeword, PASS iff Holm p < 0.05 AND TOP8 recovery CI-lo > 0 AND gates;
VOID on: collapsed readout of BASE/KO/KO_FULL/KO_IDENT/TOP8, KO_IDENT != KO, hooks never applied, any RH8 control
not norm-matched (1e-3) to TOP8 per module or rank-mismatched. Descriptive: FULLO, MLP, ATTNMLP, H2, CELL_L10H2
recovery; TOP8/FULLO recovery ratio; preservation BASE_TOP8 - BASE; logp decomposition."""
import argparse, json, os, statistics, sys
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_analyze as pa   # noqa: E402
sa, rederive, lpm = pa.sa, pa.rederive, pa.lpm
DESC = ["KO_FULLO", "KO_MLP", "KO_ATTNMLP", "KO_H2", "KO_CELL_L10H2"]


def analyze_rank(a, r, assign):
    live = ["BASE", "KO", "KO_FULL", "KO_IDENT"]
    rp = f"{a.prefix}_r{r}"
    fam = [f"KO_RH8_{j}" for j in range(a.n_rh8)]
    cand, bc = "KO_TOP8", "BASE_TOP8"
    rk = [cand, bc] + DESC + fam
    dirs = {x: rederive.strict_run_dir(f"{a.prefix}_{x}", a.expect_n, row_file="results.jsonl", allow_short=a.allow_short) for x in live}
    dirs.update({x: rederive.strict_run_dir(f"{rp}_{x}", a.expect_n, row_file="results.jsonl", allow_short=a.allow_short) for x in rk})
    arms = live + rk
    keep = sa.reference_key_set(dirs["BASE"], a.option_mass_floor) if a.option_mass_floor > 0 else None
    kv = {x: sa.arm_key_values(dirs[x], assign, a.split)[0] for x in arms}
    rf = {x: pa.row_fields(dirs[x]) for x in arms}
    common = set.intersection(*[set(v) for v in kv.values()])
    if keep is not None:
        common &= keep
    by = {x: pa.dmeans(common, lambda k, x=x: kv[x][k]) for x in arms}
    doms = sorted(by["BASE"])
    void, flags = [], []
    om = {x: statistics.median(rf[x][k]["option_mass"] for k in common) for x in arms}
    collapsed = sorted(x for x in arms if om[x] < a.option_mass_floor)
    for x in collapsed:
        (void if x in live + [cand] else flags).append(f"{x}: readout collapsed (median option mass {om[x]:.2e})")
    ident = max(abs(kv["KO_IDENT"][k] - kv["KO"][k]) for k in common)
    if ident > 1e-9:
        void.append(f"KO_IDENT differs from KO (max |dy|={ident:.3g})")
    sc = {x: pa.sidecar(dirs[x]) for x in arms if x not in ("BASE", "KO", "KO_FULL")}
    for x, s in sc.items():
        if s is None:
            void.append(f"{x}: no sidecar"); continue
        if x != "KO_IDENT" and not s.get("hook_calls"):
            void.append(f"{x}: operator hooks never applied")
    cn = sc[cand]["module_fro"]
    for x in fam:
        s = sc[x]
        if set(s["module_fro"]) != set(cn):
            void.append(f"{x}: module set differs from TOP8"); continue
        if any(abs(s["module_fro"][n] - cn[n]) > 1e-3 * max(cn[n], 1e-12) for n in cn):
            void.append(f"{x}: per-module norm not matched to TOP8")
        if s.get("rank") != sc[cand].get("rank"):
            void.append(f"{x}: rank mismatch")
    manip = pa.mean_diff(doms, by["KO"], by["BASE"]); full = pa.mean_diff(doms, by["KO_FULL"], by["KO"])
    gates = {"manipulation_KO_minus_BASE": round(manip, 5), "manipulation_ok": manip < 0,
             "full_rescue_FULL_minus_KO": round(full, 5), "instrument_ok": full > 0, "identity_max_abs_dy": ident,
             "median_option_mass": {x: om[x] for x in live + [cand, bc] + DESC}}
    prof = sa.direction_profile("sufficiency")
    scored = [cand] + DESC + fam
    rec = {x: sa.effect_fraction(prof, doms, by["KO_FULL"], by["KO"], by[x], a.n_boot, 20261014, 0.01) for x in scored}
    stat = {x: pa.mean_diff(doms, by[x], by["KO"]) for x in scored}
    decomp = {}
    for x in [cand] + DESC:
        dc = pa.dmeans(common, lambda k, x=x: rf[x][k]["lc"] - rf["KO"][k]["lc"])
        dk = pa.dmeans(common, lambda k, x=x: rf[x][k]["lk"] - rf["KO"][k]["lk"])
        decomp[x] = {"d_logp_concept": round(sum(dc.values()) / len(dc), 4), "d_logp_codeword": round(sum(dk.values()) / len(dk), 4)}
    fam_ok = [x for x in fam if x not in collapsed]
    fo = rec["KO_FULLO"].get("point")
    return {"rank": r, "primary": r in (1, 4), "n_keys": len(common), "n_domains": len(doms), "gates": gates,
            "void": void, "flags": flags, "recovery_TOP8": rec[cand], "stat_TOP8_minus_KO": round(stat[cand], 5),
            "rank_test": pa.rank_p(stat, cand, fam), "rank_test_without_collapsed_controls": pa.rank_p(stat, cand, fam_ok),
            "descriptive": {x: {"stat": round(stat[x], 5), "recovery": rec[x], "total_fro": sum(sc[x]["module_fro"].values())} for x in DESC},
            "TOP8_over_FULLO_recovery": (rec[cand].get("point") / fo) if fo else None,
            "decomposition": decomp, "control_stats": {x: round(stat[x], 5) for x in fam},
            "preservation": {"BASE_TOP8_minus_BASE_y": round(pa.mean_diff(doms, by[bc], by["BASE"]), 5)},
            "top8_total_fro": sum(cn.values()), "run_dirs": {x: os.path.basename(d) for x, d in dirs.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True); ap.add_argument("--prefix", required=True, help="hcsi_p4_<cw>_<split>")
    ap.add_argument("--split", default="train", choices=("train", "validation"))
    ap.add_argument("--expect-n", type=int, required=True); ap.add_argument("--ranks", default="1,4")
    ap.add_argument("--n-rh8", type=int, default=60); ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--option-mass-floor", type=float, default=0.05); ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assign = lpm.load_split()
    rows = []
    for r in [int(x) for x in a.ranks.split(",") if x]:
        try:
            rows.append(analyze_rank(a, r, assign))
        except SystemExit as e:
            rows.append({"rank": r, "verdict": f"NOT ANALYZABLE: {str(e)[:300]}"})
    prim = {x["rank"]: x["rank_test"]["p"] for x in rows if x.get("primary") and "rank_test" in x}
    hadj = pa.holm(prim) if prim else {}
    complete = set(prim) == {1, 4}     # review #2 HIGH-2: Holm over an incomplete family must never PASS
    for x in rows:
        if "rank_test" not in x:
            continue
        if not complete:
            x["verdict"] = "INCOMPLETE FAMILY (primary ranks present: %s; need [1, 4]) -- no verdict" % sorted(prim)
            continue
        x["holm_p"] = hadj.get(x["rank"]); x["holm_family"] = sorted(prim)
        ok = x["gates"]["manipulation_ok"] and x["gates"]["instrument_ok"]
        x["verdict"] = pa.decide(x["primary"], ok, x["void"], x["holm_p"] if x["holm_p"] is not None else 1.0, x["recovery_TOP8"])
        print(json.dumps({k: x.get(k) for k in ("rank", "verdict", "stat_TOP8_minus_KO", "rank_test", "holm_p", "TOP8_over_FULLO_recovery")}, default=str), flush=True)
    json.dump({"codeword": a.codeword, "prefix": a.prefix, "split": a.split, "expect_n": a.expect_n, "rows": rows},
              open(a.out, "w"), indent=1, default=str)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
