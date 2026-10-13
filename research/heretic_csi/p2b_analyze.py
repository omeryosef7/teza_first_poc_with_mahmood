#!/usr/bin/env python3
"""P2b analysis: semantic-installation recovery of the weight-space operator vs rank-matched controls.

REUSED (not re-implemented): `scripts/dcs_csi_subspace_analyze.py` -> `arm_key_values` (y_install per
(domain, slot) with the loader-equality assert), `reference_key_set` (option-mass key set chosen ONCE from
BASE), `effect_fraction` + `direction_profile('sufficiency')` (ratio-of-means recovery, domain bootstrap,
degeneracy guard), `rederive.strict_run_dir` (complete-run resolution, duplicate refusal). Unit = DOMAIN.

Per (codeword, rank r), on keys common to all arms:
  recovery(arm) = mean_d(arm - KO) / mean_d(KO_FULL - KO)                (KO_FULL = whole-state rescue)
  rank test: stat = mean_d(KO_CAND_r - KO) vs the norm+rank-matched family
             {KO_RAND_r_i, KO_SHUF_r_j, KO_DER_r_j};  p = (1 + #controls >= candidate)/(N + 1).
  PASS RULE (PREREG + AMENDMENT 2026-10-14): only at the PRIMARY ranks {1,4}; Holm over those two ranks
    of the codeword; PASS iff Holm-adjusted p < 0.05 AND recovery CI lower bound > 0 AND all gates hold.
    Other ranks are DESCRIPTIVE (rank p reported, never a pass/fail).
  SECONDARY (AMENDMENT 2): KO_CWONLY_r vs its codeword-row-only family (KO_CWRAND/KO_CWDER), Holm over
    {1,4}, pass = Holm p < 0.05 AND CWONLY recovery CI-lo > 0; any claim needs VALIDATION replication.
  position contrast (norm-matched by construction, DESCRIPTIVE): KO_CWONLY_r (CAND only at the codeword row) vs
    KO_ATLAST_r (CAND only at the last prompt row); KO_NEUT_r (fit at the last row, OWN norm) descriptive.
  decomposition: d logp_concept and d logp_codeword (arm - KO), domain means.
  preservation: BASE_CAND_r - BASE on y_install and option mass.
Gates: manipulation KO < BASE; FULL > KO; KO_IDENT == KO on every key; hooks fired; controls' per-module
norm/rank == CAND; readout NOT COLLAPSED (median option mass >= floor) on BASE, KO, KO_FULL, KO_IDENT and
the candidate (VOID otherwise); collapsed CONTROLS are listed and a sensitivity rank test without them is
reported; KO_CAPOP_r (if present) must replay KO_CAND_r (|dy| <= 1e-4 on every key).
"""
import argparse, importlib.util, json, math, os, statistics, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
_s = importlib.util.spec_from_file_location("sa", os.path.join(REPO, "scripts/dcs_csi_subspace_analyze.py"))
sa = importlib.util.module_from_spec(_s); sys.modules["sa"] = sa; _s.loader.exec_module(sa)
rederive, lpm = sa.rederive, sa.lpm
PRIMARY_RANKS = (1, 4)


def row_fields(run_dir):
    """(domain, slot) -> {option_mass, logp_concept, logp_codeword} for cell C semantic_one_word."""
    out = {}
    for l in open(os.path.join(run_dir, "results.jsonl")):
        r = json.loads(l)
        if r.get("query_kind") == "semantic_one_word" and r.get("cell") == "C":
            out[(r["domain"], lpm.family_slot(r["family_id"]))] = {
                "option_mass": r["option_mass"], "lc": r["logp_concept"], "lk": r["logp_codeword"]}
    return out


def sidecar(run_dir):
    p = os.path.join(run_dir, "p2b_operator.json")
    return json.load(open(p)) if os.path.exists(p) else None


def dmeans(keys, f):
    g = {}
    for k in keys:
        g.setdefault(k[0], []).append(f(k))
    return {d: sum(v) / len(v) for d, v in g.items()}


def mean_diff(doms, a, b):
    return sum(a[d] - b[d] for d in doms) / len(doms)


def rank_p(stat, cand, family):
    fam = [x for x in family if x in stat]
    better = sum(1 for x in fam if stat[x] >= stat[cand])
    return {"rank": 1 + better, "of": len(fam) + 1, "p": (1 + better) / (len(fam) + 1),
            "floor": 1 / (len(fam) + 1), "n_controls": len(fam)}


def holm(pvals):
    """Holm step-down adjusted p-values for a dict name -> p."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, adj, run = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        adj[k] = run
    return adj


def decide(primary, gates_ok, void, holm_p, rec):
    """The PASS rule, in one place (tested). rec = effect_fraction dict for the candidate."""
    if void:
        return "VOID: " + "; ".join(void)
    if not gates_ok:
        return "CANNOT ANSWER (instrument gates)"
    if rec.get("status") != "ok":
        return "CANNOT ANSWER (recovery: %s)" % rec.get("reason", rec.get("status"))
    if not primary:
        return "DESCRIPTIVE (not a confirmatory cell)"
    ci_lo = rec["ci95"][0]
    if holm_p < 0.05 and ci_lo > 0:
        return "PASS (Holm p=%.4g, recovery %.3f CI [%.3f, %.3f])" % (holm_p, rec["point"], ci_lo, rec["ci95"][1])
    why = []
    if holm_p >= 0.05:
        why.append("Holm p=%.4g >= 0.05" % holm_p)
    if ci_lo <= 0:
        why.append("recovery CI lower bound %.3f <= 0" % ci_lo)
    return "DOES NOT PASS (" + "; ".join(why) + ")"


def analyze_rank(a, r, assign):
    rand = [f"KO_RAND_r{r}_{i}" for i in range(a.nrand)]
    shuf = [f"KO_SHUF_r{r}_{j}" for j in range(a.nshuf)]
    der = [f"KO_DER_r{r}_{j}" for j in range(a.nder)]
    cand, bcand = f"KO_CAND_r{r}", f"BASE_CAND_r{r}"
    pos_arms = [f"KO_CWONLY_r{r}", f"KO_ATLAST_r{r}", f"KO_NEUT_r{r}"]
    capop = [f"KO_CAPOP_r{r}"] if a.capop else []
    live = ["BASE", "KO", "KO_FULL", "KO_IDENT"]
    fam = rand + shuf + der
    arms = live + [cand, bcand] + pos_arms + capop + fam
    dirs = {x: rederive.strict_run_dir(f"{a.prefix}_{x}", a.expect_n, row_file="results.jsonl",
                                       allow_short=a.allow_short) for x in arms}
    keep = sa.reference_key_set(dirs["BASE"], a.option_mass_floor) if a.option_mass_floor > 0 else None
    kv = {x: sa.arm_key_values(dirs[x], assign, a.split)[0] for x in arms}
    rf = {x: row_fields(dirs[x]) for x in arms}
    common = set.intersection(*[set(v) for v in kv.values()])
    if keep is not None:
        common &= keep
    by = {x: dmeans(common, lambda k, x=x: kv[x][k]) for x in arms}
    doms = sorted(by["BASE"])
    void, flags = [], []
    # ---- readout collapse screen on EVERY arm (review #3)
    om_med = {x: statistics.median(rf[x][k]["option_mass"] for k in common) for x in arms}
    collapsed = sorted(x for x in arms if om_med[x] < a.option_mass_floor)
    for x in collapsed:
        (void if x in live + [cand] else flags).append(f"{x}: readout collapsed (median option mass {om_med[x]:.2e})")
    # ---- identity / replay
    ident_dev = max(abs(kv["KO_IDENT"][k] - kv["KO"][k]) for k in common)
    if ident_dev > 1e-9:
        void.append(f"KO_IDENT differs from KO (max |dy|={ident_dev:.3g})")
    if capop:
        rep = max(abs(kv[capop[0]][k] - kv[cand][k]) for k in common)
        if rep > 1e-4:
            void.append(f"{capop[0]} does not replay {cand} (max |dy|={rep:.3g})")
    # ---- sidecars: fired, norms, ranks
    sc = {x: sidecar(dirs[x]) for x in arms if x not in ("BASE", "KO", "KO_FULL")}
    for x, s in sc.items():
        if s is None:
            void.append(f"{x}: no p2b_operator.json sidecar"); continue
        if x != "KO_IDENT" and not s.get("hook_calls"):
            void.append(f"{x}: operator hooks never applied")
    cn = sc[cand]["module_fro"]
    for x in fam:
        s = sc[x]
        bad = [n for n in cn if abs(s["module_fro"][n] - cn[n]) > 1e-3 * max(cn[n], 1e-12)]
        if bad:
            void.append(f"{x}: per-module norm not matched to CAND on {len(bad)} modules")
        if s.get("rank") != sc[cand].get("rank"):
            void.append(f"{x}: rank {s.get('rank')} != CAND rank {sc[cand].get('rank')}")
    for x in pos_arms[:2]:
        flags.append(f"{x}: applied at tokens {sc[x].get('positions_tokens')}")
    # ---- statistics
    manip = mean_diff(doms, by["KO"], by["BASE"])
    full = mean_diff(doms, by["KO_FULL"], by["KO"])
    gates = {"manipulation_KO_minus_BASE": round(manip, 5), "manipulation_ok": manip < 0,
             "full_rescue_FULL_minus_KO": round(full, 5), "instrument_ok": full > 0,
             "identity_max_abs_dy": ident_dev,
             "median_option_mass": {x: om_med[x] for x in live + [cand, bcand] + pos_arms}}
    prof = sa.direction_profile("sufficiency")
    scored = [cand] + pos_arms + fam
    rec = {x: sa.effect_fraction(prof, doms, by["KO_FULL"], by["KO"], by[x], a.n_boot, 20261014, 0.01)
           for x in scored}
    stat = {x: mean_diff(doms, by[x], by["KO"]) for x in scored}
    decomp = {}
    for x in [cand] + pos_arms:
        dc = dmeans(common, lambda k, x=x: rf[x][k]["lc"] - rf["KO"][k]["lc"])
        dk = dmeans(common, lambda k, x=x: rf[x][k]["lk"] - rf["KO"][k]["lk"])
        decomp[x] = {"d_logp_concept": round(sum(dc.values()) / len(dc), 4),
                     "d_logp_codeword": round(sum(dk.values()) / len(dk), 4)}
    fam_ok = [x for x in fam if x not in collapsed]
    cwfam = [f"KO_CWRAND_r{r}_{i}" for i in range(a.cw_nrand)] + [f"KO_CWDER_r{r}_{j}" for j in range(a.cw_nder)]
    cw_test = None
    if cwfam:
        cwd = {x: rederive.strict_run_dir(f"{a.prefix}_{x}", a.expect_n, row_file="results.jsonl",
                                          allow_short=a.allow_short) for x in cwfam}
        cwkv = {x: sa.arm_key_values(cwd[x], assign, a.split)[0] for x in cwfam}
        ck = common & set.intersection(*[set(v) for v in cwkv.values()])
        if ck != common:
            flags.append(f"CW family drops {len(common) - len(ck)} keys; CWONLY test on {len(ck)} keys")
        cby = {x: dmeans(ck, lambda k, x=x: cwkv[x][k]) for x in cwfam}
        cko = dmeans(ck, lambda k: kv["KO"][k]); cc = dmeans(ck, lambda k: kv[pos_arms[0]][k])
        cd = sorted(cko)
        cstat = {x: mean_diff(cd, cby[x], cko) for x in cwfam}
        cstat[pos_arms[0]] = mean_diff(cd, cc, cko)
        for x in cwfam:
            if sidecar(cwd[x]) is None or not sidecar(cwd[x]).get("hook_calls"):
                void.append(f"{x}: hooks never applied")
        cw_test = rank_p(cstat, pos_arms[0], cwfam)
    pres_om = [rf[bcand][k]["option_mass"] - rf["BASE"][k]["option_mass"] for k in common]
    return {"rank": r, "primary": r in PRIMARY_RANKS, "n_keys": len(common), "n_domains": len(doms),
            "gates": gates, "void": void, "flags": flags,
            "recovery_CAND": rec[cand], "stat_CAND_minus_KO": round(stat[cand], 5),
            "rank_test": rank_p(stat, cand, fam),
            "rank_test_without_collapsed_controls": rank_p(stat, cand, fam_ok),
            "rank_test_random_only": rank_p(stat, cand, rand),
            "rank_test_DER_only": rank_p(stat, cand, der), "rank_test_SHUF_only": rank_p(stat, cand, shuf),
            "position": {x: {"stat": round(stat[x], 5), "recovery": rec[x],
                             "total_fro": sum(sc[x]["module_fro"].values())} for x in pos_arms},
            "rank_test_CWONLY_vs_cw_family": cw_test,
            "position_contrast_CWONLY_minus_ATLAST": round(stat[pos_arms[0]] - stat[pos_arms[1]], 5),
            "decomposition": decomp,
            "control_stats": {x: round(stat[x], 5) for x in fam},
            "control_recovery_mean": sum(rec[x].get("point", 0.0) for x in fam) / len(fam),
            "preservation": {"BASE_CAND_minus_BASE_y": round(mean_diff(doms, by[bcand], by["BASE"]), 5),
                             "mean_option_mass_change": round(sum(pres_om) / len(pres_om), 5)},
            "cand_total_fro": sum(cn.values()), "cand_n_params": sc[cand].get("n_params"),
            "cand_fit_meta": sc[cand].get("fit_meta"), "code_sha256": sc[cand].get("code_sha256"),
            "run_dirs": {x: os.path.basename(d) for x, d in dirs.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--split", default="train", choices=("train", "validation"))
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--ranks", required=True)
    ap.add_argument("--nrand", type=int, required=True)
    ap.add_argument("--nshuf", type=int, default=5)
    ap.add_argument("--nder", type=int, required=True)
    ap.add_argument("--capop", action="store_true")
    ap.add_argument("--cw-nrand", type=int, default=0)
    ap.add_argument("--cw-nder", type=int, default=0)
    ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--option-mass-floor", type=float, default=0.05)
    ap.add_argument("--n-boot", type=int, default=5000)
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
    hadj = holm(prim) if prim else {}
    for x in rows:
        if "rank_test" not in x:
            continue
        x["holm_p"] = hadj.get(x["rank"])
        x["holm_family"] = sorted(prim)
        if x["primary"] and set(prim) != set(PRIMARY_RANKS):
            x["flags"].append("Holm family incomplete in this call (%s); rerun with both primary ranks" % sorted(prim))
        ok = x["gates"]["manipulation_ok"] and x["gates"]["instrument_ok"]
        x["verdict"] = decide(x["primary"], ok, x["void"],
                              x["holm_p"] if x["holm_p"] is not None else 1.0, x["recovery_CAND"])
    # SECONDARY (PREREG AMENDMENT 2): KO_CWONLY_r vs its codeword-row-only RAND+DER family, Holm over {1,4}
    sec = {x["rank"]: x["rank_test_CWONLY_vs_cw_family"]["p"] for x in rows
           if x.get("primary") and x.get("rank_test_CWONLY_vs_cw_family")}
    sadj = holm(sec) if sec else {}
    for x in rows:
        if "rank_test" not in x:
            continue
        if x.get("rank_test_CWONLY_vs_cw_family"):
            ok = x["gates"]["manipulation_ok"] and x["gates"]["instrument_ok"]
            x["holm_p_secondary_CWONLY"] = sadj.get(x["rank"])
            x["verdict_secondary_CWONLY"] = decide(
                x["primary"], ok, x["void"], sadj.get(x["rank"], 1.0),
                x["position"][f"KO_CWONLY_r{x['rank']}"]["recovery"]) + \
                " [SECONDARY; requires VALIDATION replication with the frozen operator before any claim]"
        print(json.dumps({k: x.get(k) for k in ("rank", "verdict", "verdict_secondary_CWONLY", "stat_CAND_minus_KO", "recovery_CAND",
                                                "rank_test", "holm_p", "preservation")}, default=str), flush=True)
    json.dump({"codeword": a.codeword, "prefix": a.prefix, "split": a.split, "expect_n": a.expect_n,
               "rows": rows}, open(a.out, "w"), indent=1, default=str)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
