#!/usr/bin/env python3
"""P2b analysis: semantic-installation recovery of the weight-space operator vs rank-matched controls.

REUSED (not re-implemented): `scripts/dcs_csi_subspace_analyze.py` -> `arm_key_values` (y_install per
(domain, slot) with the loader-equality assert), `reference_key_set` (option-mass floor key set chosen
ONCE from BASE), `effect_fraction` + `direction_profile('sufficiency')` (ratio-of-means recovery with the
domain bootstrap and degeneracy guard), `rederive.strict_run_dir` (complete-run resolution, duplicate
refusal). The unit is the DOMAIN (keys intersected across arms, then domain means).

Per (codeword, rank r):
  recovery(arm) = mean_d(arm - KO) / mean_d(KO_FULL - KO)              (KO_FULL = whole-state rescue)
  rank test: stat = mean_d(KO_CAND_r - KO) vs the rank+norm-matched family {KO_RAND_r_i, KO_SHUF_r_j};
  KO_NEUT_r (last-row fit, own norm) is reported as a separate position contrast;
  p = (1 + #controls with stat >= candidate) / (N + 1); floor = 1/(N+1).
  preservation: mean_d(BASE_CAND_r - BASE) on y_install, and the option-mass change on the same keys.
Gates (all must hold or the cell is VOID/CANNOT ANSWER): manipulation KO < BASE; whole-state rescue
recovers (FULL > KO); KO_IDENT == KO on every key (identity inert); every operator arm's hooks fired and
the random controls' per-module norms/rank match CAND (read from the sidecars).
"""
import argparse, importlib.util, json, math, os, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
_s = importlib.util.spec_from_file_location("sa", os.path.join(REPO, "scripts/dcs_csi_subspace_analyze.py"))
sa = importlib.util.module_from_spec(_s); sys.modules["sa"] = sa; _s.loader.exec_module(sa)
rederive, lpm = sa.rederive, sa.lpm


def option_mass(run_dir):
    out = {}
    for l in open(os.path.join(run_dir, "results.jsonl")):
        r = json.loads(l)
        if r.get("query_kind") == "semantic_one_word" and r.get("cell") == "C":
            out[(r["domain"], lpm.family_slot(r["family_id"]))] = r["option_mass"]
    return out


def sidecar(run_dir):
    p = os.path.join(run_dir, "p2b_operator.json")
    return json.load(open(p)) if os.path.exists(p) else None


def mean_diff(doms, a, b):
    return sum(a[d] - b[d] for d in doms) / len(doms)


def analyze_rank(a, r, assign):
    rand = [f"KO_RAND_r{r}_{i}" for i in range(a.nrand)]
    shuf = [f"KO_SHUF_r{r}_{j}" for j in range(a.nshuf)]
    neut = [f"KO_NEUT_r{r}"]
    cand, bcand = f"KO_CAND_r{r}", f"BASE_CAND_r{r}"
    arms = ["BASE", "KO", "KO_FULL", "KO_IDENT", cand, bcand] + neut + shuf + rand
    dirs = {}
    for arm in arms:
        tag = f"{a.prefix}_{arm}"
        dirs[arm] = rederive.strict_run_dir(tag, a.expect_n, row_file="results.jsonl", allow_short=a.allow_short)
    keep = sa.reference_key_set(dirs["BASE"], a.option_mass_floor) if a.option_mass_floor > 0 else None
    kv = {x: sa.arm_key_values(dirs[x], assign, a.split)[0] for x in arms}
    common = set.intersection(*[set(v) for v in kv.values()])
    if keep is not None:
        common &= keep
    by = {}
    for x in arms:
        g = {}
        for k in common:
            g.setdefault(k[0], []).append(kv[x][k])
        by[x] = {d: sum(v) / len(v) for d, v in g.items()}
    doms = sorted(by["BASE"])
    void = []
    ident_dev = max(abs(kv["KO_IDENT"][k] - kv["KO"][k]) for k in common)
    if ident_dev > 1e-9:
        void.append(f"KO_IDENT differs from KO (max |dy|={ident_dev:.3g}) -- identity operator not inert")
    sc = {x: sidecar(dirs[x]) for x in arms if x not in ("BASE", "KO", "KO_FULL")}
    for x, s in sc.items():
        if s is None:
            void.append(f"{x}: no p2b_operator.json sidecar"); continue
        if x != "KO_IDENT" and not s.get("hook_calls"):
            void.append(f"{x}: operator hooks never fired")
    cn = sc[cand]["module_fro"] if sc.get(cand) else {}
    for x in rand + shuf:
        s = sc.get(x)
        if s and cn:
            bad = [n for n in cn if abs(s["module_fro"][n] - cn[n]) > 1e-3 * max(cn[n], 1e-12)]
            if bad:
                void.append(f"{x}: per-module norm not matched to CAND on {len(bad)} modules")
            if s.get("rank") != sc[cand].get("rank"):
                void.append(f"{x}: rank {s.get('rank')} != CAND rank {sc[cand].get('rank')}")
    manip = mean_diff(doms, by["KO"], by["BASE"])
    full = mean_diff(doms, by["KO_FULL"], by["KO"])
    prof = sa.direction_profile("sufficiency")
    rec = {x: sa.effect_fraction(prof, doms, by["KO_FULL"], by["KO"], by[x], a.n_boot, 20261013, 0.01)
           for x in [cand] + neut + shuf + rand}
    stat = {x: mean_diff(doms, by[x], by["KO"]) for x in [cand] + neut + shuf + rand}
    fam = shuf + rand          # NEUT is a raw-norm position control, NOT a rank-family member

    def rank_p(family):
        better = sum(1 for x in family if stat[x] >= stat[cand])
        return {"rank": 1 + better, "of": len(family) + 1, "p": (1 + better) / (len(family) + 1),
                "floor": 1 / (len(family) + 1)}
    om_b, om_bc = option_mass(dirs["BASE"]), option_mass(dirs[bcand])
    pres_om = [om_bc[k] - om_b[k] for k in common if k in om_b and k in om_bc]
    rp = rank_p(fam)
    gates = {"manipulation_KO_minus_BASE": round(manip, 5), "manipulation_ok": manip < 0,
             "full_rescue_FULL_minus_KO": round(full, 5), "instrument_ok": full > 0,
             "identity_max_abs_dy": ident_dev}
    ok = not void and gates["manipulation_ok"] and gates["instrument_ok"]
    verdict = ("VOID: " + "; ".join(void)) if void else (
        "CANNOT ANSWER (instrument)" if not ok else
        ("PASS" if rp["p"] < 0.05 else "DOES NOT PASS") + f" rank {rp['rank']}/{rp['of']} p={rp['p']:.4g} floor={rp['floor']:.4g}")
    return {"rank": r, "n_keys": len(common), "n_domains": len(doms), "gates": gates, "void": void,
            "recovery_CAND": rec[cand], "recovery_NEUT": rec[neut[0]],
            "recovery_controls_mean": sum(rec[x].get("point", float("nan")) for x in shuf + rand) / len(shuf + rand),
            "stat_CAND_minus_KO": round(stat[cand], 5),
            "rank_test_full_family": rp, "rank_test_random_only": rank_p(rand),
            "rank_test_fitted_only": rank_p(shuf),
            "NEUT_minus_CAND_stat": round(stat[neut[0]] - stat[cand], 5),
            "NEUT_total_fro_achieved": sum(sc[neut[0]]["module_fro"].values()) if sc.get(neut[0]) else None,
            "control_stats": {x: round(stat[x], 5) for x in fam},
            "preservation": {"BASE_CAND_minus_BASE_y": round(mean_diff(doms, by[bcand], by["BASE"]), 5),
                             "mean_option_mass_change": round(sum(pres_om) / max(1, len(pres_om)), 5),
                             "hook_mean_last_pos_delta_norm": sc[bcand].get("mean_last_pos_delta_norm") if sc.get(bcand) else None},
            "cand_total_fro": sum(cn.values()) if cn else None,
            "cand_n_params": sc[cand].get("n_params") if sc.get(cand) else None,
            "cand_fit_meta": sc[cand].get("fit_meta") if sc.get(cand) else None,
            "verdict": verdict, "run_dirs": {x: os.path.basename(d) for x, d in dirs.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--split", default="train", choices=("train", "validation"))
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--ranks", required=True)
    ap.add_argument("--nrand", type=int, default=46)
    ap.add_argument("--nshuf", type=int, default=5)
    ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--option-mass-floor", type=float, default=0.05)
    ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assign = lpm.load_split()
    rows = []
    for r in [int(x) for x in a.ranks.split(",") if x]:
        try:
            res = analyze_rank(a, r, assign)
        except SystemExit as e:
            res = {"rank": r, "verdict": f"NOT ANALYZABLE: {str(e)[:300]}"}
        rows.append(res)
        print(json.dumps({k: res.get(k) for k in ("rank", "verdict", "stat_CAND_minus_KO", "recovery_CAND",
                                                  "preservation", "cand_total_fro")}, default=str), flush=True)
    json.dump({"codeword": a.codeword, "prefix": a.prefix, "split": a.split, "expect_n": a.expect_n,
               "rows": rows}, open(a.out, "w"), indent=1, default=str)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
