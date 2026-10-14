#!/usr/bin/env python3
"""P4 analysis v2 (PREREG_P4_AMENDMENT_1). Candidate KO_TOP8 vs TWO fitted control families:
RAW = KO_RH8RAW_j (random 8-head sets at their own optimum) and NC = KO_RH8NC_j (same head sets refit under the
per-module norm constraint ||dW|| = ||TOP8||). Reuses p2b_analyze helpers (and through it dcs_csi_subspace_analyze).

Decision (per codeword):
  per rank r: p_RAW = rank-p vs RAW, p_NC = rank-p vs NC; p_r = max(p_RAW, p_NC)  (intersection-union test: TOP8 must
  beat BOTH families; valid at level alpha with no cross-family correction).
  Holm over the primary ranks {1,4} on p_r. PASS iff Holm p < 0.05 AND TOP8 recovery CI-lo > 0 AND gates, no VOID.
  If either primary rank is missing / not analyzable -> "INCOMPLETE FAMILY" for every rank (never a PASS).
  Also reported (not the decision): strict Holm over all 4 tests {r1,r4}x{RAW,NC} and its attainable floor.
Factor-file checks (VOID on failure): A is exactly zero outside the declared heads' o_proj columns for TOP8 and every
control; control head sets are disjoint from TOP8; NC per-module norms == TOP8 (1e-3); sidecar norms match the file.
"""
import argparse, json, os, statistics, sys
import torch
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_analyze as pa   # noqa: E402
from p4_head_fit import TOP8, cols   # noqa: E402
sa, rederive, lpm = pa.sa, pa.rederive, pa.lpm
PRIMARY = (1, 4)
DESC = ["KO_TOP8_L6_14", "KO_FULLO", "KO_MLP", "KO_ATTNMLP", "KO_H2", "KO_CELL_L10H2"]


def factor_checks(fp, n_rh8):
    ops = torch.load(fp, map_location="cpu")["operators"]
    bad = []

    def zero_outside(key, heads):
        keep = set(cols(heads).tolist())
        mask = torch.tensor([i not in keep for i in range(4096)])
        for n, (A, B) in ops[key]["factors"].items():
            if float(A[:, mask].abs().max()) != 0.0:
                bad.append(f"{key}:{n} A nonzero outside heads {heads}")
    zero_outside("TOP8", TOP8)
    import p2b_operator as po
    tn = {n: po.fro_norm(A, B) for n, (A, B) in ops["TOP8"]["factors"].items()}
    for fam in ("RAW", "NC"):
        for j in range(n_rh8):
            k = f"RH8{fam}_{j}"
            hs = ops[k]["meta"]["heads"]
            if set(hs) & set(TOP8):
                bad.append(f"{k}: heads {hs} overlap TOP8")
            zero_outside(k, hs)
            if fam == "NC":
                for n, (A, B) in ops[k]["factors"].items():
                    if abs(po.fro_norm(A, B) - tn[n]) > 1e-3 * max(tn[n], 1e-12):
                        bad.append(f"{k}:{n} norm not matched to TOP8")
    return bad, {k: ops[k]["meta"].get("raw_fro") for k in ops}


def analyze_rank(a, r, assign):
    live = ["BASE", "KO", "KO_FULL", "KO_IDENT"]
    rp = f"{a.prefix}_r{r}"
    raw = [f"KO_RH8RAW_{j}" for j in range(a.n_rh8)]
    nc = [f"KO_RH8NC_{j}" for j in range(a.n_rh8)]
    cand, bc = "KO_TOP8", "BASE_TOP8"
    rk = [cand, bc] + DESC + raw + nc
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
    fp = os.path.join(a.factors_dir, f"factors_p4v2_{a.codeword}_r{r}.pt")
    fb, raw_norms = factor_checks(fp, a.n_rh8)
    void += fb
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
        if s.get("factors_sha16") and x != "KO_IDENT" and os.path.basename(s.get("factors_file", "")) != os.path.basename(fp):
            void.append(f"{x}: applied factors from {s.get('factors_file')} not {fp}")
    manip = pa.mean_diff(doms, by["KO"], by["BASE"]); full = pa.mean_diff(doms, by["KO_FULL"], by["KO"])
    gates = {"manipulation_KO_minus_BASE": round(manip, 5), "manipulation_ok": manip < 0,
             "full_rescue_FULL_minus_KO": round(full, 5), "instrument_ok": full > 0, "identity_max_abs_dy": ident}
    prof = sa.direction_profile("sufficiency")
    scored = [cand] + DESC + raw + nc
    rec = {x: sa.effect_fraction(prof, doms, by["KO_FULL"], by["KO"], by[x], a.n_boot, 20261014, 0.01) for x in [cand] + DESC}
    stat = {x: pa.mean_diff(doms, by[x], by["KO"]) for x in scored}
    t_raw, t_nc = pa.rank_p(stat, cand, raw), pa.rank_p(stat, cand, nc)
    decomp = {}
    for x in [cand] + DESC:
        dc = pa.dmeans(common, lambda k, x=x: rf[x][k]["lc"] - rf["KO"][k]["lc"])
        dk = pa.dmeans(common, lambda k, x=x: rf[x][k]["lk"] - rf["KO"][k]["lk"])
        decomp[x] = {"d_logp_concept": round(sum(dc.values()) / len(dc), 4), "d_logp_codeword": round(sum(dk.values()) / len(dk), 4)}
    return {"rank": r, "primary": r in PRIMARY, "n_keys": len(common), "n_domains": len(doms), "gates": gates,
            "void": void, "flags": flags, "recovery_TOP8": rec[cand], "stat_TOP8_minus_KO": round(stat[cand], 5),
            "rank_test_RAW": t_raw, "rank_test_NC": t_nc, "p_IUT": max(t_raw["p"], t_nc["p"]),
            "rank_test_RAW_without_collapsed": pa.rank_p(stat, cand, [x for x in raw if x not in collapsed]),
            "rank_test_NC_without_collapsed": pa.rank_p(stat, cand, [x for x in nc if x not in collapsed]),
            "descriptive": {x: {"stat": round(stat[x], 5), "recovery": rec[x]} for x in DESC},
            "decomposition": decomp, "control_stats": {x: round(stat[x], 5) for x in raw + nc},
            "preservation": {"BASE_TOP8_minus_BASE_y": round(pa.mean_diff(doms, by[bc], by["BASE"]), 5)},
            "raw_norms_total": {k: (sum(v ** 2 for v in n.values()) ** 0.5 if n else None) for k, n in raw_norms.items()},
            "run_dirs": {x: os.path.basename(d) for x, d in dirs.items()}}


def finalize(rows):
    """Holm over the primary ranks on p_IUT; INCOMPLETE if any primary rank is missing (review #2, HIGH-2)."""
    have = {x["rank"]: x for x in rows if "p_IUT" in x}
    complete = all(r in have for r in PRIMARY)
    hadj = pa.holm({r: have[r]["p_IUT"] for r in PRIMARY}) if complete else {}
    strict = None
    if complete:
        strict = pa.holm({f"{r}:{f}": have[r][f"rank_test_{f}"]["p"] for r in PRIMARY for f in ("RAW", "NC")})
    for x in rows:
        if "p_IUT" not in x:
            continue
        if not complete:
            x["verdict"] = "INCOMPLETE FAMILY (primary ranks present: %s; need %s) -- no verdict" % (sorted(have), list(PRIMARY))
            continue
        x["holm_p"] = hadj[x["rank"]]
        x["strict_holm4_p"] = {k: v for k, v in strict.items() if k.startswith(f"{x['rank']}:")}
        x["strict_holm4_floor"] = 4 / (x["rank_test_RAW"]["n_controls"] + 1)
        ok = x["gates"]["manipulation_ok"] and x["gates"]["instrument_ok"]
        x["verdict"] = pa.decide(x["primary"], ok, x["void"], x["holm_p"], x["recovery_TOP8"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True); ap.add_argument("--prefix", required=True, help="hcsi_p4v2_<cw>_<split>")
    ap.add_argument("--split", default="train", choices=("train", "validation"))
    ap.add_argument("--expect-n", type=int, required=True); ap.add_argument("--ranks", default="1,4")
    ap.add_argument("--n-rh8", type=int, default=60); ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--option-mass-floor", type=float, default=0.05); ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--factors-dir", default=os.path.join(REPO, "outputs/heretic_csi/p2b/prod/p4"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assign = lpm.load_split()
    rows = []
    for r in [int(x) for x in a.ranks.split(",") if x]:
        try:
            rows.append(analyze_rank(a, r, assign))
        except SystemExit as e:
            rows.append({"rank": r, "verdict": f"NOT ANALYZABLE: {str(e)[:300]}"})
    finalize(rows)
    for x in rows:
        print(json.dumps({k: x.get(k) for k in ("rank", "verdict", "stat_TOP8_minus_KO", "p_IUT", "holm_p", "strict_holm4_p")}, default=str), flush=True)
    json.dump({"codeword": a.codeword, "prefix": a.prefix, "split": a.split, "expect_n": a.expect_n, "rows": rows,
               "decision_rule": "IUT max(p_RAW,p_NC) per rank, Holm over ranks {1,4}; INCOMPLETE if a primary rank is missing"},
              open(a.out, "w"), indent=1, default=str)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
