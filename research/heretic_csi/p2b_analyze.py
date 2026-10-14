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


def arm_config(run_dir):
    return json.load(open(os.path.join(run_dir, "config.json")))["args"]


def run_prov(run_dir):
    m = json.load(open(os.path.join(run_dir, "metadata.json")))
    return {"job": str(m.get("slurm_job_id")), "host": m.get("hostname"), "gpu": m.get("gpu")}


def overlap_violations(provs, overlap_files):
    """AMENDMENT 5: a cell whose arms come from >1 host needs, for every host pair, an OVERLAP_OK file whose
    pairs cover that host pair (p2b_overlap_check.py). Same-host different jobs are treated as one host."""
    out, hosts = [], sorted({p["host"] for p in provs.values()})
    gpus = sorted({p["gpu"] for p in provs.values()})
    if gpus != ["NVIDIA RTX A5000"]:
        out.append(f"arms ran on GPUs {gpus}; the preregistered hardware is NVIDIA RTX A5000 only")
    covered = set()
    for f in overlap_files:
        d = json.load(open(f))
        if d.get("verdict") != "OVERLAP_OK":
            continue
        for pr in d["pairs"]:
            covered.add(frozenset((pr["orig"]["host"], pr["overlap"]["host"])))
    for i, h1 in enumerate(hosts):
        for h2 in hosts[i + 1:]:
            if frozenset((h1, h2)) not in covered:
                out.append(f"cell mixes hosts {h1} and {h2} without an OVERLAP_OK check covering them")
    return out


def expected_excl(cw, split):
    return {"train": f"runargs/heretic_csi/exclude_{cw}_K4.txt",
            "validation": f"runargs/dcs_cont/exclude_{cw}_bomb_sow_validation.txt"}[split]


def config_violations(dirs, cw, excl):
    """VOID messages for arms whose run config is not this codeword's bank / the expected population file /
    eager / bf16 (review #4 b)."""
    out = []
    for x, d in dirs.items():
        c = arm_config(d)
        if f"_ts116m_{cw}_bomb" not in (c.get("bank") or ""):
            out.append(f"{x}: bank {c.get('bank')!r} is not codeword {cw!r}")
        if c.get("exclude_prompt_ids") != excl:
            out.append(f"{x}: exclude file {c.get('exclude_prompt_ids')!r} != expected {excl!r}")
        if c.get("attn_impl") != "eager" or c.get("dtype") != "bfloat16":
            out.append(f"{x}: attn/dtype {c.get('attn_impl')}/{c.get('dtype')} != eager/bfloat16")
    return out


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
    if "ci95" not in rec:
        return "CANNOT ANSWER (recovery has no CI)"
    ci_lo = rec["ci95"][0]
    if holm_p < 0.05 and ci_lo > 0:
        return "PASS (Holm p=%.4g, recovery %.3f CI [%.3f, %.3f])" % (holm_p, rec["point"], ci_lo, rec["ci95"][1])
    why = []
    if holm_p >= 0.05:
        why.append("Holm p=%.4g >= 0.05" % holm_p)
    if ci_lo <= 0:
        why.append("recovery CI lower bound %.3f <= 0" % ci_lo)
    return "DOES NOT PASS (" + "; ".join(why) + ")"


def _boot_diff(doms, a_, b_, n_boot, seed):
    """Domain-bootstrap CI of mean_d(a - b) (paired by domain)."""
    import random as _r
    rng = _r.Random(seed)
    diffs = [a_[d] - b_[d] for d in doms]
    pt = sum(diffs) / len(diffs)
    bs = sorted(sum(diffs[rng.randrange(len(diffs))] for _ in diffs) / len(diffs) for _ in range(n_boot))
    return {"point": round(pt, 5), "ci95": [round(bs[int(0.025 * n_boot)], 5), round(bs[int(0.975 * n_boot) - 1], 5)]}


def _norm_rank_check(sc, cand, arms, tol=1e-3):
    """VOID messages for arms whose per-module norm or rank differs from CAND's."""
    out, cn = [], sc[cand]["module_fro"]
    for x in arms:
        s = sc.get(x)
        if s is None:
            out.append(f"{x}: no p2b_operator.json sidecar"); continue
        if not s.get("hook_calls"):
            out.append(f"{x}: operator hooks never applied")
        mf = s.get("module_fro") or {}
        bad = [n for n in cn if n not in mf or abs(mf[n] - cn[n]) > tol * max(cn[n], 1e-12)]
        if bad:
            out.append(f"{x}: per-module norm not matched to CAND on {len(bad)} modules")
        if s.get("rank") != sc[cand].get("rank"):
            out.append(f"{x}: rank {s.get('rank')} != CAND rank {sc[cand].get('rank')}")
    return out


def analyze_rank(a, r, assign):
    rand = [f"KO_RAND_r{r}_{i}" for i in range(a.nrand)]
    shuf = [f"KO_SHUF_r{r}_{j}" for j in range(a.nshuf)]
    der = [f"KO_DER_r{r}_{j}" for j in range(a.nder)]
    cand, bcand = f"KO_CAND_r{r}", f"BASE_CAND_r{r}"
    cwonly = f"KO_CWONLY_r{r}"
    pos_arms = [cwonly, f"KO_ATLAST_r{r}", f"KO_NEUT_r{r}"]
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
    # THREE VOID LISTS (review #2, finding 10): shared failures void both tests; primary-only and
    # secondary-only failures void only their own test.
    void_shared, void, void_secondary, flags = [], [], [], []
    om_med = {x: statistics.median(rf[x][k]["option_mass"] for k in common) for x in arms}
    collapsed = sorted(x for x in arms if om_med[x] < a.option_mass_floor)
    for x in collapsed:
        msg = f"{x}: readout collapsed (median option mass {om_med[x]:.2e})"
        if x in live:
            void_shared.append(msg)
        elif x == cand:
            void.append(msg)
        elif x == cwonly:
            void_secondary.append(msg)
        else:
            flags.append(msg)
    ident_dev = max(abs(kv["KO_IDENT"][k] - kv["KO"][k]) for k in common)
    if ident_dev > 1e-9:
        void_shared.append(f"KO_IDENT differs from KO (max |dy|={ident_dev:.3g})")
    if capop:
        rep = max(abs(kv[capop[0]][k] - kv[cand][k]) for k in common)
        if rep > 1e-4:
            void.append(f"{capop[0]} does not replay {cand} (max |dy|={rep:.3g})")
    sc = {x: sidecar(dirs[x]) for x in arms if x not in ("BASE", "KO", "KO_FULL")}
    if sc.get("KO_IDENT") is None:
        void_shared.append("KO_IDENT: no p2b_operator.json sidecar")
    elif not sc["KO_IDENT"].get("hook_calls"):
        void_shared.append("KO_IDENT: identity hooks never fired (an untested identity gate)")
    if sc.get(cand) is None:
        raise SystemExit(f"{cand}: no sidecar -- cannot read CAND norms")
    if not sc[cand].get("hook_calls"):
        void.append(f"{cand}: operator hooks never fired")
    provs = {x: run_prov(d) for x, d in dirs.items()}
    excl = a.expect_excl or expected_excl(a.codeword, a.split)
    void_shared += config_violations({x: dirs[x] for x in live}, a.codeword, excl)
    void += config_violations({x: dirs[x] for x in arms if x not in live}, a.codeword, excl)
    for x in [bcand] + pos_arms + capop:
        s = sc.get(x)
        target = void_secondary if x == cwonly else (void if x in capop + [bcand] else flags)
        if s is None:
            target.append(f"{x}: no p2b_operator.json sidecar")
        elif not s.get("hook_calls"):
            target.append(f"{x}: operator hooks never applied")
    void += _norm_rank_check(sc, cand, fam)
    for x in pos_arms[:2]:
        flags.append(f"{x}: applied at tokens {(sc.get(x) or {}).get('positions_tokens')}")
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
    # raw/CAND norm ratio of the FITTED controls (review #2 finding 4): from the fit meta, no GPU needed
    cn = sc[cand]["module_fro"]
    raw_ratio = {}
    for x in shuf + der:
        rawf = ((sc.get(x) or {}).get("fit_meta") or {}).get("raw_fro")
        if rawf:
            raw_ratio[x] = round(sum(rawf.values()) / sum(cn.values()), 4)
    out = {"rank": r, "primary": r in PRIMARY_RANKS, "n_keys": len(common), "n_domains": len(doms),
           "gates": gates, "void_shared": void_shared, "void": void, "void_secondary": void_secondary,
           "flags": flags,
           "recovery_CAND": rec[cand], "stat_CAND_minus_KO": round(stat[cand], 5),
           "rank_test": rank_p(stat, cand, fam),
           "rank_test_without_collapsed_controls": rank_p(stat, cand, fam_ok),
           "rank_test_random_only": rank_p(stat, cand, rand),
           "rank_test_DER_only": rank_p(stat, cand, der), "rank_test_SHUF_only": rank_p(stat, cand, shuf),
           "fitted_control_raw_over_CAND_norm": raw_ratio,
           "position": {x: {"stat": round(stat[x], 5), "recovery": rec[x],
                            "total_fro": sum((sc.get(x) or {}).get("module_fro", {}).values())} for x in pos_arms},
           "position_contrast_CWONLY_minus_ATLAST": round(stat[pos_arms[0]] - stat[pos_arms[1]], 5),
           "decomposition": decomp,
           "control_stats": {x: round(stat[x], 5) for x in fam},
           "control_recovery_mean": sum(rec[x].get("point", 0.0) for x in fam) / len(fam),
           "cand_total_fro": sum(cn.values()), "cand_n_params": sc[cand].get("n_params"),
           "cand_fit_meta": sc[cand].get("fit_meta"), "code_sha256": sc[cand].get("code_sha256"),
           "run_dirs": {x: os.path.basename(d) for x, d in dirs.items()}}
    pres_om = [rf[bcand][k]["option_mass"] - rf["BASE"][k]["option_mass"] for k in common]
    out["preservation"] = {"BASE_CAND_minus_BASE_y": round(mean_diff(doms, by[bcand], by["BASE"]), 5),
                           "mean_option_mass_change": round(sum(pres_om) / len(pres_om), 5)}
    # ---------------- SECONDARY (CWONLY vs codeword-row-only family): isolated from the primary ----------------
    cwfam = [f"KO_CWRAND_r{r}_{i}" for i in range(a.cw_nrand)] + [f"KO_CWDER_r{r}_{j}" for j in range(a.cw_nder)]
    out["rank_test_CWONLY_vs_cw_family"] = None
    if cwfam:
        try:
            cwd = {x: rederive.strict_run_dir(f"{a.prefix}_{x}", a.expect_n, row_file="results.jsonl",
                                              allow_short=a.allow_short) for x in cwfam}
            cwkv = {x: sa.arm_key_values(cwd[x], assign, a.split)[0] for x in cwfam}
            cwrf = {x: row_fields(cwd[x]) for x in cwfam}
            ck = common & set.intersection(*[set(v) for v in cwkv.values()])
            if ck != common:
                flags.append(f"CW family drops {len(common) - len(ck)} keys; secondary test on {len(ck)} keys")
            cw_om = {x: statistics.median(cwrf[x][k]["option_mass"] for k in ck) for x in cwfam}
            cw_coll = sorted(x for x in cwfam if cw_om[x] < a.option_mass_floor)
            for x in cw_coll:
                flags.append(f"{x}: readout collapsed (median option mass {cw_om[x]:.2e})")
            cwsc = {x: sidecar(cwd[x]) for x in cwfam}
            void_secondary += config_violations(cwd, a.codeword, excl)
            out["run_dirs_cw_family"] = {x: os.path.basename(d) for x, d in cwd.items()}
            provs.update({x: run_prov(d) for x, d in cwd.items()})
            void_secondary += _norm_rank_check({**cwsc, cand: sc[cand]}, cand, cwfam)
            cby = {x: dmeans(ck, lambda k, x=x: cwkv[x][k]) for x in cwfam}
            for x in ("KO", "KO_FULL", cwonly):
                cby[x] = dmeans(ck, lambda k, x=x: kv[x][k])
            cd = sorted(cby["KO"])
            cstat = {x: mean_diff(cd, cby[x], cby["KO"]) for x in cwfam + [cwonly]}
            out["rank_test_CWONLY_vs_cw_family"] = rank_p(cstat, cwonly, cwfam)
            out["rank_test_CWONLY_without_collapsed_controls"] = rank_p(cstat, cwonly, [x for x in cwfam if x not in cw_coll])
            # recovery on the SAME keys as the secondary rank test (review #2: was on primary keys)
            out["recovery_CWONLY_secondary"] = sa.effect_fraction(prof, cd, cby["KO_FULL"], cby["KO"], cby[cwonly],
                                                                  a.n_boot, 20261014, 0.01)
            out["n_keys_secondary"] = len(ck)
        except SystemExit as e:
            void_secondary.append(f"CW family not analyzable: {str(e)[:200]}")
    # ---------------- ADD-ON comparators (amendment 3; DESCRIPTIVE) ----------------
    if a.addon:
        try:
            ad = {}
            mb = {"KO_MEANBIAS": "KO_MEANBIAS", "KO_CWMEANBIAS": "KO_CWMEANBIAS", "BASE_MEANBIAS": "BASE_MEANBIAS"}
            raw = [f"KO_DERRAW_r{r}_{j}" for j in range(a.nder)] + [f"KO_SHUFRAW_r{r}_{j}" for j in range(a.nshuf)]
            adarms = list(mb) + raw
            add = {x: rederive.strict_run_dir(f"{a.prefix}_{x}", a.expect_n, row_file="results.jsonl",
                                              allow_short=a.allow_short) for x in adarms}
            akv = {x: sa.arm_key_values(add[x], assign, a.split)[0] for x in adarms}
            ak = common & set.intersection(*[set(v) for v in akv.values()])
            abyk = {x: dmeans(ak, lambda k, x=x: akv[x][k]) for x in adarms}
            for x in ["KO", "KO_FULL", "BASE", cand, cwonly] + fam:
                abyk[x] = dmeans(ak, lambda k, x=x: kv[x][k])
            ad_d = sorted(abyk["KO"])
            arf = {x: row_fields(add[x]) for x in adarms}
            ad["n_keys"] = len(ak)
            ad["median_option_mass"] = {x: statistics.median(arf[x][k]["option_mass"] for k in ak) for x in adarms}
            for x in ("KO_MEANBIAS", "KO_CWMEANBIAS"):
                ad[x] = {"stat": round(mean_diff(ad_d, abyk[x], abyk["KO"]), 5),
                         "recovery": sa.effect_fraction(prof, ad_d, abyk["KO_FULL"], abyk["KO"], abyk[x], a.n_boot, 20261014, 0.01)}
            ad["BASE_MEANBIAS_minus_BASE_y"] = round(mean_diff(ad_d, abyk["BASE_MEANBIAS"], abyk["BASE"]), 5)
            ad["CAND_minus_MEANBIAS"] = _boot_diff(ad_d, abyk[cand], abyk["KO_MEANBIAS"], a.n_boot, 7)
            ad["CWONLY_minus_CWMEANBIAS"] = _boot_diff(ad_d, abyk[cwonly], abyk["KO_CWMEANBIAS"], a.n_boot, 8)
            rstat = {x: mean_diff(ad_d, abyk[x], abyk["KO"]) for x in raw + [cand]}
            ad["rank_test_DER_raw_norm"] = rank_p(rstat, cand, raw[:a.nder])
            ad["rank_test_SHUF_raw_norm"] = rank_p(rstat, cand, raw[a.nder:])
            asc = {x: sidecar(add[x]) for x in adarms}
            # VOIDs on the add-on path (review #3 finding 6): collapse + hooks; MEANBIAS collapse suspends wording
            ad["void"] = []
            for x in adarms:
                if ad["median_option_mass"][x] < a.option_mass_floor and x != "BASE_MEANBIAS":
                    ad["void"].append(f"{x}: readout collapsed (median option mass {ad['median_option_mass'][x]:.2e})")
                if asc[x] is None or not asc[x].get("hook_calls"):
                    ad["void"].append(f"{x}: hooks never applied / no sidecar")
            ad["void"] += config_violations(add, a.codeword, excl)
            ad["run_dirs"] = {x: os.path.basename(d) for x, d in add.items()}
            ad["arm_provenance"] = {x: run_prov(d) for x, d in add.items()}
            # add-on arms get their OWN overlap gate (vs the liveness arms' hosts) -> add-on VOID only
            ad["void"] += overlap_violations({**{x: provs[x] for x in live}, **ad["arm_provenance"]}, a.overlap)
            ad["BASE_MEANBIAS_collapsed"] = ad["median_option_mass"]["BASE_MEANBIAS"] < a.option_mass_floor
            ad["raw_arms_total_fro"] = {x: round(sum((asc[x] or {}).get("module_fro", {}).values()), 4) for x in raw}
            ad["meanbias_sidecars"] = {x: {k: (asc[x] or {}).get(k) for k in ("kind", "where", "hook_calls", "bias_total_norm")}
                                       for x in mb}
            mb_void = [v for v in ad["void"] if "MEANBIAS" in v]
            ad["input_conditional_wording_eligible_on_this_split"] = bool(
                a.split == "validation" and not mb_void and ad["CAND_minus_MEANBIAS"]["ci95"][0] > 0 and
                _boot_diff(ad_d, abyk[cand], abyk["KO_CWMEANBIAS"], a.n_boot, 9)["ci95"][0] > 0)
            ad["CAND_minus_CWMEANBIAS"] = _boot_diff(ad_d, abyk[cand], abyk["KO_CWMEANBIAS"], a.n_boot, 9)
            ad["wording_rule"] = ("only ever True on split=validation; 'input-conditional' requires CAND beats BOTH KO_MEANBIAS and KO_CWMEANBIAS (CI-lo>0) on "
                                  "VALIDATION, and is suspended if either comparator is VOID/collapsed (amendment 4)")
            out["addon"] = ad
        except SystemExit as e:
            out["addon"] = {"status": f"NOT ANALYZABLE: {str(e)[:200]}"}
    # ---------------- AMENDMENT 6: norm-matched mean-gap bias (DESCRIPTIVE ONLY; never unlocks wording) --------
    if a.addon_nm:
        try:
            nm = [f"KO_MEANBIAS_NM_r{r}", f"BASE_MEANBIAS_NM_r{r}"]
            nd = {x: rederive.strict_run_dir(f"{a.prefix}_{x}", a.expect_n, row_file="results.jsonl",
                                             allow_short=a.allow_short) for x in nm}
            nkv = {x: sa.arm_key_values(nd[x], assign, a.split)[0] for x in nm}
            nrf = {x: row_fields(nd[x]) for x in nm}
            nk = common & set.intersection(*[set(v) for v in nkv.values()])
            nby = {x: dmeans(nk, lambda k, x=x: nkv[x][k]) for x in nm}
            for x in ("KO", "KO_FULL", "BASE", cand):
                nby[x] = dmeans(nk, lambda k, x=x: kv[x][k])
            ndd = sorted(nby["KO"])
            nsc = {x: sidecar(nd[x]) for x in nm}
            nprov = {x: run_prov(d) for x, d in nd.items()}
            res = {"n_keys": len(nk), "void": [], "run_dirs": {x: os.path.basename(d) for x, d in nd.items()},
                   "arm_provenance": nprov,
                   "median_option_mass": {x: statistics.median(nrf[x][k]["option_mass"] for k in nk) for x in nm},
                   "bias_total_norm": {x: (nsc[x] or {}).get("bias_total_norm") for x in nm},
                   "never_unlocks_wording": True}
            res["void"] += config_violations(nd, a.codeword, excl)
            res["void"] += overlap_violations({**{x: provs[x] for x in live}, **nprov}, a.overlap)
            for x in nm:
                if res["median_option_mass"][x] < a.option_mass_floor:
                    res["void" if x.startswith("KO_") else "damage_flags"] = res.get("void" if x.startswith("KO_") else "damage_flags", []) + [
                        f"{x}: readout collapsed (median option mass {res['median_option_mass'][x]:.2e})"]
                if nsc[x] is None or not nsc[x].get("hook_calls"):
                    res["void"].append(f"{x}: hooks never applied / no sidecar")
            res["KO_MEANBIAS_NM"] = {"stat": round(mean_diff(ndd, nby[nm[0]], nby["KO"]), 5),
                                     "recovery": sa.effect_fraction(prof, ndd, nby["KO_FULL"], nby["KO"], nby[nm[0]], a.n_boot, 20261014, 0.01)}
            res["BASE_MEANBIAS_NM_minus_BASE_y"] = round(mean_diff(ndd, nby[nm[1]], nby["BASE"]), 5)
            res["CAND_minus_MEANBIAS_NM"] = _boot_diff(ndd, nby[cand], nby[nm[0]], a.n_boot, 11)
            out["addon_nm"] = res
        except SystemExit as e:
            out["addon_nm"] = {"status": f"NOT ANALYZABLE: {str(e)[:200]}"}
    out["arm_provenance"] = provs
    out["jobs"] = sorted({p["job"] for p in provs.values() if p})
    ov = overlap_violations({k: v for k, v in provs.items() if v}, a.overlap)
    out["void_shared"] += ov
    return out


def _valid_primary(x):
    """A primary rank enters Holm with its real p ONLY if its primary read is valid (review #3 finding 3)."""
    g = x["gates"]
    return (not x["void_shared"] and not x["void"] and g["manipulation_ok"] and g["instrument_ok"]
            and x["recovery_CAND"].get("status") == "ok" and "ci95" in x["recovery_CAND"])


def _valid_secondary(x):
    g = x["gates"]
    rec = x.get("recovery_CWONLY_secondary") or {}
    return (x.get("rank_test_CWONLY_vs_cw_family") is not None and not x["void_shared"] and not x["void_secondary"]
            and g["manipulation_ok"] and g["instrument_ok"] and rec.get("status") == "ok" and "ci95" in rec)


def _neutral(v):
    """Re-word an embedded verdict so an INCOMPLETE string never contains the substring 'PASS' (review #4 b)."""
    return v.replace("DOES NOT PASS", "would-not-pass").replace("PASS", "would-pass")


def finalize(rows):
    """Holm + verdicts for one codeword's rows. A primary rank that is absent, NOT ANALYZABLE, VOID (shared or
    primary), gate-failed or CANNOT ANSWER enters Holm as p=1 (m stays 2), and every other rank's verdict becomes
    INCOMPLETE FAMILY -- never a PASS at a p adjusted over a family with an invalid member (reviews #2 #2, #3 #3).
    Same rule for the secondary family (shared VOIDs, e.g. KO_IDENT != KO, invalidate both)."""
    analysed = [x for x in rows if "rank_test" in x]
    prim_have = {x["rank"]: x["rank_test"]["p"] for x in analysed if x["primary"] and _valid_primary(x)}
    sec_have = {x["rank"]: x["rank_test_CWONLY_vs_cw_family"]["p"] for x in analysed
                if x["primary"] and _valid_secondary(x)}
    hadj = holm({r: prim_have.get(r, 1.0) for r in PRIMARY_RANKS})
    sadj = holm({r: sec_have.get(r, 1.0) for r in PRIMARY_RANKS})
    prim_missing = sorted(set(PRIMARY_RANKS) - set(prim_have))
    sec_missing = sorted(set(PRIMARY_RANKS) - set(sec_have))
    for x in analysed:
        ok = x["gates"]["manipulation_ok"] and x["gates"]["instrument_ok"]
        x["holm_p"] = hadj.get(x["rank"]) if x["primary"] else None
        v = decide(x["primary"], ok, x["void_shared"] + x["void"], x["holm_p"] if x["primary"] else 1.0,
                   x["recovery_CAND"])
        if x["primary"] and prim_missing and not v.startswith(("VOID", "CANNOT")):
            v = ("INCOMPLETE FAMILY (primary ranks %s missing / not analyzable / VOID / CANNOT ANSWER; Holm treats "
                 "them as p=1): %s" % (prim_missing, _neutral(v)))
        x["verdict"] = v
        x["holm_family_valid_ranks"] = sorted(prim_have)
        if x["primary"] and (x.get("rank_test_CWONLY_vs_cw_family") or x["void_secondary"]):
            x["holm_p_secondary_CWONLY"] = sadj.get(x["rank"])
            vs = decide(True, ok, x["void_shared"] + x["void_secondary"], sadj.get(x["rank"], 1.0),
                        x.get("recovery_CWONLY_secondary") or {"status": "missing"})
            if sec_missing and not vs.startswith(("VOID", "CANNOT")):
                vs = "INCOMPLETE FAMILY (secondary ranks %s missing/invalid): %s" % (sec_missing, _neutral(vs))
            x["verdict_secondary_CWONLY"] = vs + " [SECONDARY; requires VALIDATION replication with the frozen operator]"
    return rows


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
    ap.add_argument("--addon-nm", action="store_true", help="amendment-6 descriptive MEANBIAS_NM arms (never unlock wording)")
    ap.add_argument("--addon", action="store_true", help="amendment-3 comparators: MEANBIAS arms + raw-norm DER/SHUF")
    ap.add_argument("--expect-excl", default=None, help="expected --exclude-prompt-ids of every arm (default from --split)")
    ap.add_argument("--overlap", default="", help="comma list of p2b_overlap_check JSONs (AMENDMENT 5)")
    ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--option-mass-floor", type=float, default=0.05)
    ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    a.overlap = [f for f in a.overlap.split(",") if f]
    assign = lpm.load_split()
    rows = []
    for r in [int(x) for x in a.ranks.split(",") if x]:
        try:
            rows.append(analyze_rank(a, r, assign))
        except SystemExit as e:
            rows.append({"rank": r, "verdict": f"NOT ANALYZABLE: {str(e)[:300]}"})
    finalize(rows)
    for x in rows:
        print(json.dumps({k: x.get(k) for k in ("rank", "verdict", "verdict_secondary_CWONLY", "stat_CAND_minus_KO",
                                                "recovery_CAND", "rank_test", "holm_p", "preservation")}, default=str), flush=True)
    json.dump({"codeword": a.codeword, "prefix": a.prefix, "split": a.split, "expect_n": a.expect_n,
               "rows": rows}, open(a.out, "w"), indent=1, default=str)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
