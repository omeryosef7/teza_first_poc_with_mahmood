#!/usr/bin/env python3
"""P3 analysis (PREREG_P3_TRUNC.json): SVD truncation sufficiency + single-component removal of the frozen P2b CAND
operator, on the population of the P3 job (VALIDATION). All arms incl. liveness come from ONE job (prefix
hcsi_p3_<cw>_r<R>_<split>). Reuses p2b_analyze helpers. Unit = domain.

  stat(x) = mean_d(x - KO);  recovery(x) = effect_fraction(sufficiency) vs KO_FULL (whole-state rescue)
  TRUNCATION SUFFICIENCY, k in {1,2} (k < R): rank of KO_TOPk among its rank-k per-module-norm-matched random controls
     KO_RAND_TOPk_* -> p_k = (1+#ctrl >= TOPk)/(N+1); Holm over k. retention_k = stat(TOPk)/stat(REEXP), domain
     bootstrap 95% CI. Minimal sufficient learned subspace k* = smallest k with Holm p < 0.05 AND retention CI-lo >= 0.5;
     if none -> 'no k <= 2 retains the effect specifically'.
  TOPkN (renormed to the full per-module norm) vs KO_RAND_TOPkN_*: descriptive.
  REMOVAL (necessity of component i): loss_i = stat(REEXP) - stat(DROPi), domain-bootstrap CI; frac_i = loss_i/stat(REEXP).
  Sanity: REEXP must reproduce the frozen CAND (checked via sidecar factors and |stat(REEXP)-stat(KO_CAND_ref)| if given);
  gates KO < BASE, FULL > KO, KO_IDENT == KO, hooks fired, collapse screen. ALL P3 results are DESCRIPTIVE (parent P2b
  basket r4 PASS is marginal: Holm 0.0488, LODO-fragile)."""
import argparse, json, os, random, statistics, sys
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_analyze as pa   # noqa: E402
sa, rederive, lpm = pa.sa, pa.rederive, pa.lpm


def boot_ratio(doms, num, den, n=5000, seed=20261015):
    """domain-bootstrap CI of mean_d(num)/mean_d(den) (num/den: dict domain -> value)."""
    rng = random.Random(seed); vals = []
    for _ in range(n):
        s = [rng.choice(doms) for _ in doms]
        d = sum(den[x] for x in s)
        if abs(d) > 1e-12:
            vals.append(sum(num[x] for x in s) / d)
    vals.sort()
    pt = sum(num[x] for x in doms) / sum(den[x] for x in doms)
    return {"point": pt, "ci95": [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]], "n_boot_ok": len(vals)}


def boot_mean(doms, f, n=5000, seed=20261015):
    rng = random.Random(seed); vals = []
    for _ in range(n):
        s = [rng.choice(doms) for _ in doms]
        vals.append(sum(f[x] for x in s) / len(s))
    vals.sort()
    return {"point": sum(f[x] for x in doms) / len(doms), "ci95": [vals[int(0.025 * n)], vals[int(0.975 * n) - 1]]}


def minimal_k(tests):
    """tests: k -> {'holm_p', 'retention': {'ci95': [lo, hi]}} ; returns smallest qualifying k or None."""
    ok = [k for k in sorted(tests) if tests[k]["holm_p"] < 0.05 and tests[k]["retention"]["ci95"][0] >= 0.5]
    return ok[0] if ok else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True); ap.add_argument("--rank", type=int, required=True)
    ap.add_argument("--split", default="validation", choices=("train", "validation"))
    ap.add_argument("--expect-n", type=int, required=True); ap.add_argument("--nrand", type=int, default=40)
    ap.add_argument("--nrand-n", type=int, default=20); ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--option-mass-floor", type=float, default=0.05); ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--trunc-file", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import torch
    ops = torch.load(a.trunc_file, map_location="cpu")["operators"]
    pfx = f"hcsi_p3_{a.codeword}_r{a.rank}_{'validation' if a.split == 'validation' else 'train_k4'}"
    ks = sorted(int(k[3:]) for k in ops if k.startswith("TOP") and not k.endswith("N"))
    drops = sorted(int(k[4:]) for k in ops if k.startswith("DROP"))
    live = ["BASE", "KO", "KO_FULL", "KO_IDENT"]
    arms = live + ["KO_REEXP"] + [f"KO_TOP{k}" for k in ks] + [f"KO_TOP{k}N" for k in ks] + [f"KO_DROP{i}" for i in drops]
    arms += [f"KO_RAND_TOP{k}_{i}" for k in ks for i in range(a.nrand)] + [f"KO_RAND_TOP{k}N_{i}" for k in ks for i in range(a.nrand_n)]
    assign = lpm.load_split()
    dirs = {x: rederive.strict_run_dir(f"{pfx}_{x}", a.expect_n, row_file="results.jsonl", allow_short=a.allow_short) for x in arms}
    keep = sa.reference_key_set(dirs["BASE"], a.option_mass_floor)
    kv = {x: sa.arm_key_values(dirs[x], assign, a.split)[0] for x in arms}
    rf = {x: pa.row_fields(dirs[x]) for x in arms}
    common = set.intersection(*[set(v) for v in kv.values()]) & keep
    by = {x: pa.dmeans(common, lambda k, x=x: kv[x][k]) for x in arms}
    doms = sorted(by["BASE"])
    void, flags = [], []
    om = {x: statistics.median(rf[x][k]["option_mass"] for k in common) for x in arms}
    for x in arms:
        if om[x] < a.option_mass_floor:
            (void if x in live + ["KO_REEXP"] else flags).append(f"{x}: readout collapsed ({om[x]:.2e})")
    ident = max(abs(kv["KO_IDENT"][k] - kv["KO"][k]) for k in common)
    if ident > 1e-9:
        void.append(f"KO_IDENT != KO (max |dy| {ident:.3g})")
    for x in arms:
        if x in ("BASE", "KO", "KO_FULL"):
            continue
        s = pa.sidecar(dirs[x])
        if s is None or not s.get("hook_calls"):
            void.append(f"{x}: hooks never fired / no sidecar")
    manip = pa.mean_diff(doms, by["KO"], by["BASE"]); full = pa.mean_diff(doms, by["KO_FULL"], by["KO"])
    gates = {"KO_minus_BASE": manip, "FULL_minus_KO": full, "ok": manip < 0 and full > 0}
    stat = {x: pa.mean_diff(doms, by[x], by["KO"]) for x in arms if x not in live}
    eff = {x: {d: by[x][d] - by["KO"][d] for d in doms} for x in arms if x not in live}
    prof = sa.direction_profile("sufficiency")
    rec = {x: sa.effect_fraction(prof, doms, by["KO_FULL"], by["KO"], by[x], a.n_boot, 20261015, 0.01)
           for x in ["KO_REEXP"] + [f"KO_TOP{k}" for k in ks] + [f"KO_TOP{k}N" for k in ks] + [f"KO_DROP{i}" for i in drops]}
    tests = {}
    for k in ks:
        t = pa.rank_p(stat, f"KO_TOP{k}", [f"KO_RAND_TOP{k}_{i}" for i in range(a.nrand)])
        tn = pa.rank_p(stat, f"KO_TOP{k}N", [f"KO_RAND_TOP{k}N_{i}" for i in range(a.nrand_n)])
        tests[k] = {"rank_test": t, "rank_test_renormed_descriptive": tn,
                    "retention": boot_ratio(doms, eff[f"KO_TOP{k}"], eff["KO_REEXP"], a.n_boot),
                    "retention_renormed": boot_ratio(doms, eff[f"KO_TOP{k}N"], eff["KO_REEXP"], a.n_boot)}
    hadj = pa.holm({k: tests[k]["rank_test"]["p"] for k in ks}) if ks else {}
    for k in ks:
        tests[k]["holm_p"] = hadj[k]
    removal = {i: {"loss": boot_mean(doms, {d: eff["KO_REEXP"][d] - eff[f"KO_DROP{i}"][d] for d in doms}, a.n_boot),
                   "frac_of_REEXP": stat["KO_REEXP"] and (stat["KO_REEXP"] - stat[f"KO_DROP{i}"]) / stat["KO_REEXP"]} for i in drops}
    valid = not void and gates["ok"]
    k_star = minimal_k(tests) if valid else None
    res = {"codeword": a.codeword, "rank": a.rank, "split": a.split, "prefix": pfx, "n_keys": len(common), "n_domains": len(doms),
           "gates": gates, "void": void, "flags": flags, "stat": {k: round(v, 5) for k, v in stat.items() if "RAND" not in k},
           "recovery": rec, "truncation_tests": tests, "removal": removal,
           "minimal_sufficient_k": k_star if valid else "VOID/CANNOT ANSWER",
           "label": "DESCRIPTIVE (parent P2b basket r4 VALIDATION PASS is marginal; PREREG_P3_TRUNC.json)",
           "run_dirs": {x: os.path.basename(d) for x, d in dirs.items() if "RAND" not in x}}
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print(json.dumps({"minimal_sufficient_k": res["minimal_sufficient_k"], "void": void,
                      "tests": {k: {"p": v["rank_test"]["p"], "holm": v["holm_p"], "ret": v["retention"]} for k, v in tests.items()},
                      "removal": {i: v["frac_of_REEXP"] for i, v in removal.items()}}, default=str, indent=1))


if __name__ == "__main__":
    main()
