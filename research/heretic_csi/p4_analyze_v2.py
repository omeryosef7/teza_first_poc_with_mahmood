#!/usr/bin/env python3
"""P4 analysis v2 (PREREG_P4_AMENDMENT_1). Candidate KO_TOP8 vs TWO fitted control families:
RAW = KO_RH8RAW_j (random 8-head sets at their own optimum) and NC = KO_RH8NC_j (same head sets refit under the
per-module norm constraint ||dW|| = ||TOP8||). Reuses p2b_analyze helpers (and through it dcs_csi_subspace_analyze).

Decision (per codeword):
  per rank r: p_RAW = rank-p vs RAW, p_NC = rank-p vs NC; p_r = max(p_RAW, p_NC)  (intersection-union test: TOP8 must
  beat BOTH families; valid at level alpha with no cross-family correction).
  Holm over the primary ranks {1,4} on p_r. PASS iff Holm p < 0.05 AND TOP8 recovery CI-lo > 0 AND gates, no VOID.
  If either primary rank is missing, not analyzable, VOID, gate-failed or recovery-degenerate -> "INCOMPLETE FAMILY"
  for every other rank (never a PASS); the invalid rank keeps its own VOID / CANNOT ANSWER verdict.
  Also reported (not the decision): strict Holm over all 4 tests {r1,r4}x{RAW,NC} and its attainable floor.
Factor-file checks (VOID on failure): A is exactly zero outside the declared heads' o_proj columns for TOP8 and every
control; control head sets are disjoint from TOP8; NC per-module norms == TOP8 (1e-3); sidecar norms match the file.
"""
import argparse, json, os, statistics, sys
import hashlib
import torch
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_analyze as pa   # noqa: E402
from p4_head_fit import TOP8, cols   # noqa: E402
sa, rederive, lpm = pa.sa, pa.rederive, pa.lpm
PRIMARY = (1, 4)
DESC = ["KO_TOP8_L6_14", "KO_FULLO", "KO_MLP", "KO_ATTNMLP", "KO_H2", "KO_CELL_L10H2"]


def _sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


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


def sidecar_checks(sc, expected_sha16):
    """Review #4 (1)+(3). sc: arm -> p2b_operator.json sidecar (or None); expected_sha16: arm -> sha16 of the FROZEN factors
    file that arm must have applied. VOID reasons returned for: missing sidecar; hooks never fired (EVERY operator arm,
    INCLUDING TOP8 and the identity arm KO_IDENT -- an identity arm whose hooks never ran proves nothing); applied
    factors file whose sha256 prefix differs from the frozen fit output (a filename match is not enough)."""
    void = []
    for x, s in sc.items():
        if s is None:
            void.append(f"{x}: no sidecar"); continue
        if not s.get("hook_calls"):
            void.append(f"{x}: operator hooks never fired (hook_calls={s.get('hook_calls')})")
        exp = expected_sha16.get(x)
        if exp is None:
            void.append(f"{x}: no expected factors sha registered")
        elif s.get("factors_sha16") != exp:
            void.append(f"{x}: applied factors sha16 {s.get('factors_sha16')} != frozen {exp} ({s.get('factors_file')})")
    return void


MAX_COLLAPSED_FRAC = 0.10


def conservative_rank_p(stat, cand, fam, collapsed):
    """M6 (PREREG_P4_AMENDMENT_6): PRIMARY rank p in which every COLLAPSED control counts as >= the candidate
    (a collapsed readout is never a free win for TOP8). p = (1 + #{controls with stat >= cand OR collapsed})/(n + 1).
    Also returns the plain p and the without-collapsed p for reporting; the conservative p is the larger of the two
    by construction."""
    cs = set(collapsed)
    plain = sum(1 for x in fam if stat[x] >= stat[cand])
    cons = sum(1 for x in fam if (stat[x] >= stat[cand]) or (x in cs))
    n = len(fam)
    fam_ok = [x for x in fam if x not in cs]
    wo = sum(1 for x in fam_ok if stat[x] >= stat[cand])
    return {"rank": 1 + cons, "of": n + 1, "p": (1 + cons) / (n + 1), "floor": 1 / (n + 1), "n_controls": n,
            "n_collapsed_in_family": sum(1 for x in fam if x in cs), "p_plain": (1 + plain) / (n + 1),
            "p_without_collapsed": (1 + wo) / (len(fam_ok) + 1)}


def collapse_void(name, t, n_fam):
    """M6: VOID reason if more than MAX_COLLAPSED_FRAC of a control family has a collapsed readout, else None."""
    if t["n_collapsed_in_family"] > MAX_COLLAPSED_FRAC * n_fam:
        return f"{name} family: {t['n_collapsed_in_family']}/{n_fam} controls collapsed (> {MAX_COLLAPSED_FRAC:.0%})"
    return None


def provenance_void(r, jobs, gpus):
    """L7 (PREREG_P4_AMENDMENT_6 addendum): all arms of a rank must come from exactly ONE slurm job and ONE GPU type, and
    both fields must be RECORDED (a missing/None RUNMETA field can no longer satisfy the rule vacuously)."""
    v = []
    if None in jobs or None in gpus or "" in jobs or "" in gpus:
        v.append(f"rank {r}: RUNMETA missing slurm_job_id and/or gpu on some arm (jobs={sorted(map(str, jobs))}, gpus={sorted(map(str, gpus))})")
    if len(jobs) != 1 or len(gpus) != 1:
        v.append(f"rank {r}: arms come from {len(jobs)} jobs / GPU types {sorted(map(str, gpus))} -- must be one job, one GPU")
    return v


def analyze_rank_safe(fn, r):
    """L6 (addendum): a per-rank failure never crashes the script and never reads like a null.
    SystemExit from the strict run-dir/integrity checks => 'NOT ANALYZABLE (data integrity, not a null)';
    any other exception => 'NOT ANALYZABLE (internal error, not a null)'. Either way the row has no p_IUT, so the other
    primary rank becomes INCOMPLETE (never PASS)."""
    try:
        return fn()
    except SystemExit as e:
        return {"rank": r, "verdict": f"NOT ANALYZABLE (data integrity, not a null): {str(e)[:300]}"}
    except Exception as e:   # noqa: BLE001
        return {"rank": r, "verdict": f"NOT ANALYZABLE (internal error, not a null): {type(e).__name__}: {str(e)[:300]}"}


def split_label(split, codeword):
    """M7: every verdict carries the split and the codeword's confirmatory role (output labelling only)."""
    sp = "TRAIN-K4 (in-sample)" if split == "train" else "VALIDATION"
    role = ("primary codeword; basket VALIDATION Holm over {1,4} is the SOLE confirmatory test" if codeword == "basket"
            else "SECONDARY transfer, DESCRIPTIVE (no cross-codeword correction)")
    return f"[{sp}; {role}] "


def analyze_rank(a, r, assign):
    live = ["BASE", "KO", "KO_FULL", "KO_IDENT"]
    rp = f"{a.prefix}_r{r}"
    raw = [f"KO_RH8RAW_{j}" for j in range(a.n_rh8)]
    nc = [f"KO_RH8NC_{j}" for j in range(a.n_rh8)]
    cand, bc = "KO_TOP8", "BASE_TOP8"
    rk = [cand, bc] + DESC + raw + nc
    # liveness is run INSIDE each rank job (prefix <prefix>_r<R>), so every arm of a rank comes from one job / one GPU
    dirs = {x: rederive.strict_run_dir(f"{rp}_{x}", a.expect_n, row_file="results.jsonl", allow_short=a.allow_short) for x in live + rk}
    jobs = {json.load(open(os.path.join(d, "RUNMETA.json"))).get("slurm_job_id") for d in dirs.values()}
    gpus = {json.load(open(os.path.join(d, "RUNMETA.json"))).get("gpu") for d in dirs.values()}
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
    void += provenance_void(r, jobs, gpus)
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
    sha_p4 = _sha16(fp)
    ident_fp = os.path.join(a.p2b_factors_dir, f"factors_{a.codeword}_r1.pt")   # p2b_emit liveness KO_IDENT source
    expected = {x: sha_p4 for x in sc if x != "KO_IDENT"}
    expected["KO_IDENT"] = _sha16(ident_fp)
    void += sidecar_checks(sc, expected)
    manip = pa.mean_diff(doms, by["KO"], by["BASE"]); full = pa.mean_diff(doms, by["KO_FULL"], by["KO"])
    gates = {"manipulation_KO_minus_BASE": round(manip, 5), "manipulation_ok": manip < 0,
             "full_rescue_FULL_minus_KO": round(full, 5), "instrument_ok": full > 0, "identity_max_abs_dy": ident}
    prof = sa.direction_profile("sufficiency")
    scored = [cand] + DESC + raw + nc
    rec = {x: sa.effect_fraction(prof, doms, by["KO_FULL"], by["KO"], by[x], a.n_boot, 20261014, 0.01) for x in [cand] + DESC}
    stat = {x: pa.mean_diff(doms, by[x], by["KO"]) for x in scored}
    t_raw = conservative_rank_p(stat, cand, raw, collapsed)
    t_nc = conservative_rank_p(stat, cand, nc, collapsed)
    for nm, t, fam_ in (("RAW", t_raw, raw), ("NC", t_nc, nc)):
        msg = collapse_void(nm, t, len(fam_))
        if msg:
            void.append(msg)
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
            "collapsed_controls": [x for x in collapsed if x in raw + nc],
            "descriptive": {x: {"stat": round(stat[x], 5), "recovery": rec[x]} for x in DESC},
            "decomposition": decomp, "control_stats": {x: round(stat[x], 5) for x in raw + nc},
            "preservation": {"BASE_TOP8_minus_BASE_y": round(pa.mean_diff(doms, by[bc], by["BASE"]), 5)},
            "raw_norms_total": {k: (sum(v ** 2 for v in n.values()) ** 0.5 if n else None) for k, n in raw_norms.items()},
            "run_dirs": {x: os.path.basename(d) for x, d in dirs.items()}}


def valid(x):
    """A primary rank may enter Holm only if its test is valid: present, no VOID, gates hold, recovery estimable
    (review #3 finding 3: a VOID / gate-failed / CANNOT-ANSWER rank must count as MISSING, never contribute its p)."""
    return ("p_IUT" in x and not x.get("void") and x["gates"]["manipulation_ok"] and x["gates"]["instrument_ok"]
            and x["recovery_TOP8"].get("status") == "ok")


def finalize(rows, label=""):
    """Holm over the primary ranks on p_IUT. INCOMPLETE FAMILY (never PASS) for every rank unless EVERY primary rank
    is present AND valid (review #2 HIGH-2 + review #3 finding 3). Invalid ranks keep their own VOID / CANNOT ANSWER
    verdict from decide()."""
    have = {x["rank"]: x for x in rows if "p_IUT" in x}
    complete = all(r in have and valid(have[r]) for r in PRIMARY)
    hadj = pa.holm({r: have[r]["p_IUT"] for r in PRIMARY}) if complete else {}
    strict = None
    if complete:
        strict = pa.holm({f"{r}:{f}": have[r][f"rank_test_{f}"]["p"] for r in PRIMARY for f in ("RAW", "NC")})
    for x in rows:
        if "p_IUT" not in x:
            continue
        ok = x["gates"]["manipulation_ok"] and x["gates"]["instrument_ok"]
        if not valid(x):
            x["verdict"] = label + pa.decide(x["primary"], ok, x["void"], 1.0, x["recovery_TOP8"])
            continue
        if not complete:
            bad = sorted(r for r in PRIMARY if not (r in have and valid(have[r])))
            x["verdict"] = label + "INCOMPLETE FAMILY (primary ranks missing or invalid: %s) -- no verdict" % bad
            continue
        x["holm_p"] = hadj[x["rank"]]
        x["strict_holm4_p"] = {k: v for k, v in strict.items() if k.startswith(f"{x['rank']}:")}
        x["strict_holm4_floor"] = 4 / (x["rank_test_RAW"]["n_controls"] + 1)
        x["verdict"] = label + pa.decide(x["primary"], ok, x["void"], x["holm_p"], x["recovery_TOP8"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True); ap.add_argument("--prefix", required=True, help="hcsi_p4v2_<cw>_<split>")
    ap.add_argument("--split", default="train", choices=("train", "validation"))
    ap.add_argument("--expect-n", type=int, required=True); ap.add_argument("--ranks", default="1,4")
    ap.add_argument("--n-rh8", type=int, default=60); ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--option-mass-floor", type=float, default=0.05); ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--factors-dir", default=os.path.join(REPO, "outputs/heretic_csi/p2b/prod/p4"))
    ap.add_argument("--p2b-factors-dir", default=os.path.join(REPO, "outputs/heretic_csi/p2b/prod/fac"), help="source of the KO_IDENT liveness arm")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assign = lpm.load_split()
    rows = []
    for r in [int(x) for x in a.ranks.split(",") if x]:
        rows.append(analyze_rank_safe(lambda r=r: analyze_rank(a, r, assign), r))
    finalize(rows, split_label(a.split, a.codeword))
    for x in rows:
        print(json.dumps({k: x.get(k) for k in ("rank", "verdict", "stat_TOP8_minus_KO", "p_IUT", "holm_p", "strict_holm4_p")}, default=str), flush=True)
    json.dump({"codeword": a.codeword, "prefix": a.prefix, "split": a.split, "expect_n": a.expect_n, "rows": rows,
               "decision_rule": "IUT max(p_RAW,p_NC) per rank, Holm over ranks {1,4}; INCOMPLETE if a primary rank is missing"},
              open(a.out, "w"), indent=1, default=str)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
