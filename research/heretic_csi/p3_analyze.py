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
  Sanity (review #7, both enforced -> VOID on failure):
    (a) REEXP reproduces the frozen CAND: against the P2b VALIDATION reference arms (--ref-prefix, e.g.
        hcsi_p2b_basket_val: <ref>_KO and <ref>_KO_CAND_r<R>) on the SAME rows (common keys) and the SAME GPU type
        (RUNMETA 'gpu' must match, else VOID: cannot verify): |stat(REEXP) - stat_ref(KO_CAND)| <= STAT_TOL (1e-3) and
        max per-key |y_REEXP - y_ref_CAND| <= ROW_TOL (1e-2); the P3 job's own KO must equal the reference KO per key
        within KO_TOL (1e-6) (same GPU type => the frozen readout is bit-exact).
    (b) every operator arm's sidecar factors_sha16 equals the sha16 of the file it must apply: the trunc file for
        REEXP/TOPk/TOPkN/DROPi and the RAND controls; fac/factors_<cw>_r1.pt for KO_IDENT.
  Other gates: KO < BASE, FULL > KO, KO_IDENT == KO, hooks fired, collapse screen.
  WORDING (review #7): the truncation null is RANDOM norm-matched edits only (CAND already beats those); TOP1/TOP2
  keep most of the dW norm; DROP losses are confounded with norm loss. Any k* must be stated 'vs random edits only;
  not vs fitted controls; norm-confounded for DROP'. ALL P3 results are DESCRIPTIVE (parent P2b
  basket r4 PASS is marginal: Holm 0.0488, LODO-fragile)."""
import argparse, hashlib, json, os, random, statistics, sys
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


STAT_TOL, ROW_TOL, KO_TOL = 1e-3, 1e-2, 1e-6


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def sidecar_sha_checks(sc, expected):
    """sc: arm -> sidecar dict or None; expected: arm -> sha16. VOID reasons (missing sidecar, hooks never fired,
    unregistered arm, sha mismatch)."""
    v = []
    for x, s in sc.items():
        if s is None:
            v.append(f"{x}: no sidecar"); continue
        if not s.get("hook_calls"):
            v.append(f"{x}: hooks never fired")
        if x not in expected:
            v.append(f"{x}: no expected sha registered")
        elif s.get("factors_sha16") != expected[x]:
            v.append(f"{x}: factors sha16 {s.get('factors_sha16')} != expected {expected[x]}")
    return v


def reexp_check(keys, y_reexp, y_ko, y_ref_cand, y_ref_ko, gpu_p3, gpu_ref):
    """keys: common row keys (domain, slot). y_*: key -> y_install. Returns (result dict, void list)."""
    void = []
    if gpu_p3 != gpu_ref:
        return {"gpu_p3": gpu_p3, "gpu_ref": gpu_ref}, [f"REEXP check: GPU type differs ({gpu_p3} vs {gpu_ref}) -- cannot verify"]
    ko_dev = max(abs(y_ko[k] - y_ref_ko[k]) for k in keys)
    row_dev = max(abs(y_reexp[k] - y_ref_cand[k]) for k in keys)
    doms = sorted({k[0] for k in keys})
    dm = lambda y: {d: sum(y[k] for k in keys if k[0] == d) / sum(1 for k in keys if k[0] == d) for d in doms}  # noqa: E731
    a, b, c, e = dm(y_reexp), dm(y_ko), dm(y_ref_cand), dm(y_ref_ko)
    st_p3 = sum(a[d] - b[d] for d in doms) / len(doms)
    st_ref = sum(c[d] - e[d] for d in doms) / len(doms)
    res = {"n_keys": len(keys), "gpu": gpu_p3, "KO_vs_refKO_max_abs_dy": ko_dev, "REEXP_vs_refCAND_max_abs_dy": row_dev,
           "stat_REEXP": st_p3, "stat_ref_CAND": st_ref, "abs_stat_diff": abs(st_p3 - st_ref),
           "tolerances": {"stat": STAT_TOL, "row": ROW_TOL, "ko": KO_TOL}}
    if ko_dev > KO_TOL:
        void.append(f"REEXP check: own KO != reference KO (max |dy| {ko_dev:.3g} > {KO_TOL})")
    if row_dev > ROW_TOL:
        void.append(f"REEXP check: per-row |y_REEXP - y_refCAND| {row_dev:.3g} > {ROW_TOL}")
    if abs(st_p3 - st_ref) > STAT_TOL:
        void.append(f"REEXP check: |stat diff| {abs(st_p3 - st_ref):.3g} > {STAT_TOL}")
    return res, void


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
    ap.add_argument("--ref-prefix", required=True, help="P2b VALIDATION prefix holding <ref>_KO and <ref>_KO_CAND_r<R>")
    ap.add_argument("--ref-expect-n", type=int, default=None)
    ap.add_argument("--p2b-factors-dir", default=os.path.join(REPO, "outputs/heretic_csi/p2b/prod/fac"))
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
    sc = {x: pa.sidecar(dirs[x]) for x in arms if x not in ("BASE", "KO", "KO_FULL")}
    tsha = sha16(a.trunc_file)
    expected = {x: tsha for x in sc if x != "KO_IDENT"}
    expected["KO_IDENT"] = sha16(os.path.join(a.p2b_factors_dir, f"factors_{a.codeword}_r1.pt"))
    void += sidecar_sha_checks(sc, expected)
    # REEXP reproduces the frozen CAND (P2b VALIDATION reference arms; same rows, same GPU type)
    ren = a.ref_expect_n or a.expect_n
    rdir = {x: rederive.strict_run_dir(f"{a.ref_prefix}_{x}", ren, row_file="results.jsonl", allow_short=a.allow_short)
            for x in ("KO", f"KO_CAND_r{a.rank}")}
    rkv = {x: sa.arm_key_values(d, assign, a.split)[0] for x, d in rdir.items()}
    rk = common & set(rkv["KO"]) & set(rkv[f"KO_CAND_r{a.rank}"])
    gpu = lambda d: json.load(open(os.path.join(d, "RUNMETA.json"))).get("gpu")   # noqa: E731
    reexp, rv = reexp_check(rk, kv["KO_REEXP"], kv["KO"], rkv[f"KO_CAND_r{a.rank}"], rkv["KO"],
                            gpu(dirs["KO_REEXP"]), gpu(rdir[f"KO_CAND_r{a.rank}"]))
    void += rv
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
           "gates": gates, "void": void, "flags": flags, "reexp_check": reexp,
           "wording": "k* (if any) is vs RANDOM norm-matched edits only; NOT vs fitted controls; DROP losses are norm-confounded", "stat": {k: round(v, 5) for k, v in stat.items() if "RAND" not in k},
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
