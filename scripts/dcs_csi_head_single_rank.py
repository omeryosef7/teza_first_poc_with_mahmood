"""The PRIMARY reader for PR-CSI-013 -- ONE head against 20 arbitrary single heads, on `button`.

WHY A NEW FILE. S-252 measured that W4 cannot read this family and made it refuse by name: W4 hard-codes
HD_BASE/HD_KO/HD_TOPK/HD_BOTK, and its REPORTABLE_AS describes "K head INDICES ... carry at least half of
the A1 knockout's effect" -- language about a K-head SUBSET. PR-CSI-013's candidate is BT_SINGLE, ONE
head. Bending W4 would mean either renaming this family's arms to borrow a tool (hiding what is being
tested) or loosening the assertions that protect D32/D33. This file is ADDITIVE: nothing W4 does changes.

WHAT IT SHARES, DELIBERATELY. W4's `by_domain` (hence `load_installation`, the SOLE definition of
y_install and its concept-free channel filter), its `liveness`, `boot_mean`, `pct` and
`atomic_write_json`; `dcs_csi_rederive_patch.strict_run_dir`; and the census reader's `recorded_heads`.
No endpoint, resampler or run-resolver is re-implemented.

⚠ THE DOSE IDENTITY IS BLIND ON EVERY INTERVENED ARM HERE. BT_SINGLE and all 20 BT_CTRL_* are ONE-head
arms and record 2016 prefill edits -- exactly what the all-32 BT_KO records (S-246). On PR-CSI-012 only
the singletons collided; here the WHOLE RANK FAMILY does. Arm identity is therefore asserted from each
run's own `knockout_heads`, and the report says `dose_is_diagnostic_of_identity: false` on every such arm.

DIRECTION: NECESSITY. These arms REMOVE a head from a clean forward, so stronger = MORE NEGATIVE and the
reference is BT_BASE. The rank is over the candidate and the 20 controls -- 21 members, attainable floor
1/21 = 0.047619, and rank 1 is the only certifying outcome at alpha = 0.05.
"""
import argparse, importlib.util, json, os, random, statistics, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


w4 = _load("w4", os.path.join(REPO, "scripts", "dcs_csi_head_analyze.py"))
census = _load("census", os.path.join(REPO, "scripts", "dcs_csi_head_census.py"))
rederive = _load("rederive", os.path.join(REPO, "scripts", "dcs_csi_rederive_patch.py"))

DOSE_UNIT = census.DOSE_UNIT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--split", required=True, choices=["train", "validation", "test"])
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--require-slurm-job", default=None)
    ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--B", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20260922)
    ap.add_argument("--ci", type=float, default=0.95)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    pr = json.load(open(a.prereg))
    # ---- the mirror guards. This tool reads a SINGLE-HEAD rank family and nothing else. ----
    if pr.get("NO_RANK_TEST"):
        sys.exit("REFUSING: prereg %r declares NO_RANK_TEST -- it is a CENSUS. Use "
                 "scripts/dcs_csi_head_census.py. (S-255)" % pr.get("id"))
    cand = "BT_SINGLE"
    if cand not in pr["head_sets"]:
        sys.exit("REFUSING: prereg %r has no %s -- this reader is for the SINGLE-HEAD family only; a "
                 "K-head subset family is W4's (scripts/dcs_csi_head_analyze.py). (S-255)"
                 % (pr["id"], cand))
    if len(pr["head_sets"][cand]) != 1:
        sys.exit("REFUSING: %s carries %d heads; this reader's reporting language is about ONE head. "
                 "(S-255)" % (cand, len(pr["head_sets"][cand])))
    if pr["split"] != a.split:
        sys.exit("REFUSING: prereg says split %r, invoked with %r" % (pr["split"], a.split))

    hs = pr["head_sets"]
    base, ko = pr["base_arms"]
    cprefix = pr["control_prefix"]
    controls = sorted(k for k in hs if k.startswith(cprefix))
    if len(controls) != pr["n_controls"]:
        sys.exit("REFUSING: control family is %d arms, the prereg says %d"
                 % (len(controls), pr["n_controls"]))
    if cand in controls:
        sys.exit("REFUSING: the candidate entered its own control family")
    h_star = hs[cand][0]
    if any(h_star in hs[c] for c in controls):
        sys.exit("REFUSING: head %d (the candidate) appears in a control arm" % h_star)
    arms = [base, ko] + [cand] + controls
    if len(arms) != pr["n_arms_per_split"]:
        sys.exit("REFUSING: resolved %d arms, prereg declares %d"
                 % (len(arms), pr["n_arms_per_split"]))
    jobs = a.require_slurm_job.split(",") if a.require_slurm_job else None

    dirs, per, live, slots = {}, {}, {}, {}
    for arm in arms:
        d = rederive.strict_run_dir("%s_%s" % (a.tag_prefix, arm), a.expect_n,
                                    row_file="results.jsonl", allow_short=a.allow_short,
                                    require_slurm_jobs=jobs)
        dirs[arm] = d
        per[arm], slots[arm], _, _ = w4.by_domain(d)
        live[arm] = w4.liveness(d)

    doms = sorted(set.intersection(*(set(v) for v in per.values())))
    print("[single] arms = %d | domains common to ALL arms = %d | expect-n = %d | split = %s | "
          "codeword = %s" % (len(arms), len(doms), a.expect_n, a.split, pr["codeword"]))
    if not doms:
        sys.exit("VACUOUS: no domain is present in every arm")
    ragged = {arm: sorted(set(per[arm]) - set(doms)) for arm in arms if set(per[arm]) - set(doms)}
    if ragged:
        sys.exit("REFUSING: arms disagree on their domain sets: %s"
                 % {k: v[:4] for k, v in list(ragged.items())[:4]})
    ref = slots[arms[0]]
    for arm in arms[1:]:
        bad = {d for d in doms if slots[arm].get(d) != ref.get(d)}
        if bad:
            sys.exit("REFUSING: arm %s binds different SLOTS from %s in %d domain(s) (e.g. %s)"
                     % (arm, arms[0], len(bad), sorted(bad)[:3]))
    want_dom = pr["population"]["%s_domains" % a.split]
    want_n = pr["population"]["%s_expect_n" % a.split]
    on_protocol = (a.expect_n == want_n)
    if on_protocol and len(doms) != want_dom:
        sys.exit("REFUSING: %d domains analysed but %s preregisters %d for %s"
                 % (len(doms), pr["id"], want_dom, a.split))
    if not on_protocol:
        print("[single] OFF-PROTOCOL: --expect-n %d != the preregistered %d; the domain count is NOT "
              "binding and NOTHING HERE IS A RESULT." % (a.expect_n, want_n))

    # ---- GATE 0: liveness + ARM IDENTITY (the only identity check that works here, S-246) ----
    g0 = {}
    for arm in arms:
        L = live[arm]
        k = 0 if arm == base else (32 if arm == ko else len(hs[arm]))
        want = 0 if arm == base else (DOSE_UNIT if arm == ko else DOSE_UNIT * k)
        got = None if arm == base else census.recorded_heads(dirs[arm])
        if arm == base:
            ok_id, why = True, "not intervened"
        elif arm == ko:
            ok_id = (got == "ALL"); why = "ALL 32" if ok_id else "expected ALL, got %r" % (got,)
        elif got is None:
            ok_id, why = False, "NO knockout_heads recorded -- CANNOT VERIFY (absence is not a value)"
        elif got == "ALL":
            ok_id, why = False, ("records ALL 32 but the prereg says %s -- S-246 COLLISION: the dose "
                                 "check would have passed" % (hs[arm],))
        else:
            ok_id = (list(got) == list(hs[arm]))
            why = "matches prereg" if ok_id else "got %s != %s" % (got, hs[arm])
        g0[arm] = {"n_rows": L["n_rows"], "violations": L["violations"],
                   "total_decode_edits": L["total_decode_edits"],
                   "median_prefill_edits": L["median_prefill_edits"],
                   "expected_median_prefill_edits": want,
                   "dose_is_diagnostic_of_identity": want not in (DOSE_UNIT,),
                   "identity": why,
                   "pass": bool(L["violations"] == {} and L["total_decode_edits"] == 0
                                and L["median_prefill_edits"] == want and ok_id)}
    failed = sorted(k for k, v in g0.items() if not v["pass"])
    if failed:
        for k in failed:
            print("  GATE 0 FAIL %-12s dose %s want %s | %s" % (k, g0[k]["median_prefill_edits"],
                  g0[k]["expected_median_prefill_edits"], g0[k]["identity"]))
        sys.exit("CANNOT ANSWER: GATE 0 failed on %d arm(s): %s" % (len(failed), failed))
    print("[single] GATE 0 PASS on all %d arms | identity from each run's own knockout_heads "
          "(the dose is NOT diagnostic on any 1-head arm -- S-246)" % len(arms))

    # ---- effects ----
    rng = random.Random(a.seed)
    lo_q, hi_q = (1 - a.ci) / 2.0, 1 - (1 - a.ci) / 2.0
    E, CI = {}, {}
    for arm in arms:
        if arm == base:
            continue
        d = [per[arm][x] - per[base][x] for x in doms]
        E[arm] = statistics.fmean(d)
        bs = w4.boot_mean(d, a.B, rng)
        CI[arm] = [w4.pct(bs, lo_q), w4.pct(bs, hi_q)]

    # ---- GATE 1: the positive control must fire ----
    gate1 = {"pass": bool(E[ko] < 0 and CI[ko][1] < 0), "E": E[ko], "ci95": CI[ko]}
    print("[single] GATE 1 %s | E(%s) = %+.6f ci95 [%+.6f, %+.6f]"
          % ("PASS" if gate1["pass"] else "FAIL", ko, E[ko], CI[ko][0], CI[ko][1]))
    if not gate1["pass"]:
        w4.atomic_write_json(a.out, {"schema": "dcs_csi_head_single_rank/1", "prereg_id": pr["id"],
                                     "VERDICT": "CANNOT ANSWER", "GATE_1": gate1,
                                     "GATE_0": g0, "E": E, "ci95": CI, "n_domains": len(doms)})
        sys.exit("CANNOT ANSWER: GATE 1 failed -- the all-32 knockout does not lower installation on "
                 "this codeword, so a single-head result is not interpretable. The candidate is NOT "
                 "reported.")

    # ---- the rank: candidate against the 20 controls. NECESSITY -> more negative is stronger. ----
    fam = [cand] + controls
    vals = {k: E[k] for k in fam}
    better = sum(1 for k in controls if vals[k] < vals[cand])
    ties = sum(1 for k in controls if vals[k] == vals[cand])
    rank = better + 1                      # ties count AGAINST the candidate is handled below
    rank_with_ties = better + ties + 1
    n_fam = len(fam)
    p = rank_with_ties / float(n_fam)
    floor = 1.0 / n_fam
    print("\n[single] head %d vs %d arbitrary single heads on %s"
          % (h_star, len(controls), pr["codeword"]))
    print("[single] E(%s) = %+.6f ci95 [%+.6f, %+.6f]" % (cand, E[cand], CI[cand][0], CI[cand][1]))
    top = sorted(controls, key=lambda k: vals[k])[:3]
    print("[single] three strongest controls: %s"
          % ["%s(head %d) %+.6f" % (k, hs[k][0], vals[k]) for k in top])
    print("[single] rank %d of %d | p = %.6f | FLOOR = %.6f"
          % (rank_with_ties, n_fam, p, floor))

    verdict = ("REPLICATES" if rank_with_ties == 1 else "DOES NOT REPLICATE AT RANK 1")
    print("[single] VERDICT: %s" % verdict)

    out = {
        "schema": "dcs_csi_head_single_rank/1",
        "prereg": a.prereg, "prereg_id": pr["id"], "codeword": pr["codeword"],
        "split": a.split, "tag_prefix": a.tag_prefix, "expect_n": a.expect_n,
        "n_domains": len(doms), "ON_PROTOCOL": on_protocol, "B": a.B, "seed": a.seed, "ci": a.ci,
        "h_star": h_star, "E": {k: round(v, 8) for k, v in E.items()},
        "ci95": {k: [round(v[0], 8), round(v[1], 8)] for k, v in CI.items()},
        "GATE_0": g0, "GATE_1": gate1,
        "RANK": {"candidate": cand, "head": h_star, "rank": rank_with_ties, "of": n_fam,
                 "p": p, "p_display": "%.6f" % p, "attainable_floor": floor,
                 "n_controls_strictly_better": better, "n_ties": ties,
                 "tie_convention": "ties count AGAINST the candidate (>=), so a tie cannot certify",
                 "floor_note": "rank 1 of %d gives p = the floor = %.6f and is the ONLY certifying "
                               "outcome at alpha = 0.05; rank 2 gives %.6f and does not clear it. "
                               "The p is reported WITH its floor, always."
                               % (n_fam, floor, 2.0 / n_fam)},
        "VERDICT": verdict,
        "REPORTABLE_AS":
            ("head %d, selected on BASKET by a rule frozen before the PR-CSI-012 census existed, is "
             "rank %d of %d against %d arbitrary single heads on the %s codeword (p = %.6f, floor "
             "%.6f). This is a SINGLE-HEAD replication across CODEWORDS. It is NOT a claim that head "
             "%d is 'the writer', and it says NOTHING about the other 31 heads on %s."
             % (h_star, rank_with_ties, n_fam, len(controls), pr["codeword"], p, floor, h_star,
                pr["codeword"])),
        "CANNOT_DO": pr["WHAT_THIS_CANNOT_DO"],
        "DOSE_IDENTITY_IS_BLIND_HERE": pr["DOSE_IDENTITY_IS_BLIND_HERE"],
        "INDEPENDENT_PATH": "scripts/dcs_csi_rederive_subspace.py --direction necessity shares no code "
                            "with this file and already parameterises --candidate/--controls, so it "
                            "reads this family unchanged (S-254).",
    }
    n = w4.atomic_write_json(a.out, out)
    print("[single] wrote+verified %s (%d bytes)" % (a.out, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
