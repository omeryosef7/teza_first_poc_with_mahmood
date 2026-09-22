"""Does the SINGLE-HEAD rank reader compute the right answer, and does it refuse what it must?

Ground truth is constructed, so the rank, p and verdict are known before the tool runs. Rows are REAL
230-row rows with logp_concept shifted by a per-arm constant.
⛔ NOTHING HERE IS A SCIENTIFIC RESULT. It is a unit test of arithmetic and of five refusals.
"""
import glob, json, os, shutil, subprocess, sys, tempfile

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SCORE = os.path.join(REPO, "outputs", "boombness", "score_behavior")
STAMP = "20260922_000000_555555"
PRE = "csi6_selftest_single"
PREREG = os.path.join(REPO, "configs", "dcs_csi_pr013_button_head_replication.json")
DOSE = 2016


def build(src, arm, shift, heads, base=False, ko=False, force_heads=None):
    tag = "%s_%s" % (PRE, arm)
    dst = os.path.join(SCORE, "%s_%s" % (tag, STAMP))
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    cfg_p = os.path.join(dst, "config.json"); cfg = json.load(open(cfg_p))
    args = cfg.get("args", cfg); args["tag"], args["arm"] = tag, arm
    if base:
        args.pop("knockout_heads", None); dose = 0
    elif ko:
        args["knockout_heads"] = ""; dose = DOSE
    else:
        rec = force_heads if force_heads is not None else heads
        args["knockout_heads"] = "" if rec == "ALL" else ",".join(str(h) for h in rec)
        dose = DOSE * len(heads)
    json.dump(cfg, open(cfg_p, "w"), indent=2)
    rp = os.path.join(dst, "results.jsonl")
    rows = [json.loads(l) for l in open(rp)]
    for r in rows:
        r["arm"] = arm
        r["logp_concept"] = float(r["logp_concept"]) + shift
        r["hook_n_prefill_edits"] = dose; r["hook_n_edits"] = dose
        r["hook_n_decode_edits"] = 0; r["hook_liveness_violations"] = None
    with open(rp, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    d = json.load(open(os.path.join(dst, "DONE.json"))); d["run_id"] = "%s_%s" % (tag, STAMP)
    json.dump(d, open(os.path.join(dst, "DONE.json"), "w"), indent=2)
    return dst


def run(out, prereg=PREREG):
    return subprocess.run([sys.executable, "scripts/dcs_csi_head_single_rank.py", "--prereg", prereg,
                           "--tag-prefix", PRE, "--split", "validation", "--expect-n", "230",
                           "--B", "500", "--out", out], cwd=REPO, capture_output=True, text=True)


def main():
    pr = json.load(open(PREREG)); hs = pr["head_sets"]
    base, ko = pr["base_arms"]
    ctrls = sorted(k for k in hs if k.startswith(pr["control_prefix"]))
    src = sorted(glob.glob(os.path.join(SCORE, "csi5_census_basket_validation_HD_BASE_*")))
    if len(src) != 1:
        sys.exit("need exactly one 230-row source; got %d" % len(src))
    src = src[0]
    tmp = tempfile.mkdtemp(prefix="single_selftest_")
    fails = []

    def lay(cand_shift, ctrl_shifts=None):
        build(src, base, 0.0, None, base=True)
        build(src, ko, -2.0, None, ko=True)
        build(src, "BT_SINGLE", cand_shift, hs["BT_SINGLE"])
        for i, c in enumerate(ctrls):
            sh = (ctrl_shifts or {}).get(c, -0.05 - 0.001 * i)
            build(src, c, sh, hs[c])

    try:
        # A -- candidate strongest -> rank 1 of 21, p = floor, REPLICATES
        lay(-1.2)
        p = run(os.path.join(tmp, "a.json"))
        out = p.stdout + p.stderr
        if p.returncode != 0:
            fails.append("A: refused a well-formed family: %s" % out.strip().splitlines()[-1][:140])
        else:
            j = json.load(open(os.path.join(tmp, "a.json")))
            R = j["RANK"]
            if R["rank"] != 1 or abs(R["p"] - 1.0 / 21) > 1e-12:
                fails.append("A: rank %s p %s, expected 1 and 1/21" % (R["rank"], R["p"]))
            if j["VERDICT"] != "REPLICATES":
                fails.append("A: verdict %r" % j["VERDICT"])
            if j["GATE_0"]["BT_SINGLE"]["dose_is_diagnostic_of_identity"] is not False:
                fails.append("A: a 1-head arm's dose was called identity-diagnostic (S-246 says no)")
            if j["GATE_0"][ko]["dose_is_diagnostic_of_identity"] is not False:
                fails.append("A: BT_KO's dose (2016) collides with the singletons and is not diagnostic")
            print("[selftest] A ok: rank %d of %d, p=%.6f, %s"
                  % (R["rank"], R["of"], R["p"], j["VERDICT"]))

        # B -- ONE control beats the candidate -> rank 2, p = 2/21, DOES NOT REPLICATE
        lay(-1.2, {ctrls[5]: -2.5})
        p = run(os.path.join(tmp, "b.json"))
        if p.returncode != 0:
            fails.append("B: refused: %s" % (p.stdout + p.stderr).strip().splitlines()[-1][:140])
        else:
            R = json.load(open(os.path.join(tmp, "b.json")))["RANK"]
            if R["rank"] != 2 or abs(R["p"] - 2.0 / 21) > 1e-12:
                fails.append("B: rank %s p %s, expected 2 and 2/21" % (R["rank"], R["p"]))
            else:
                print("[selftest] B ok: one stronger control -> rank 2 of 21, p=%.6f (does not clear)"
                      % R["p"])

        # C -- GATE 1 fails (the all-32 knockout does not lower installation)
        build(src, ko, +2.0, None, ko=True)
        p = run(os.path.join(tmp, "c.json"))
        out = p.stdout + p.stderr
        if p.returncode == 0:
            fails.append("C: ⛔ reported a candidate although GATE 1 failed")
        elif "CANNOT ANSWER: GATE 1" not in out:
            fails.append("C: refused for the wrong reason: %s" % out.strip().splitlines()[-1][:140])
        else:
            j = json.load(open(os.path.join(tmp, "c.json")))
            if "RANK" in j:
                fails.append("C: a RANK was written despite GATE 1 failing")
            else:
                print("[selftest] C ok: GATE 1 fails -> CANNOT ANSWER, no rank written")
        build(src, ko, -2.0, None, ko=True)                       # restore

        # D -- THE S-246 COLLISION on a CONTROL, with a perfectly legal dose
        build(src, ctrls[3], -0.05, hs[ctrls[3]], force_heads="ALL")
        p = run(os.path.join(tmp, "d.json"))
        out = p.stdout + p.stderr
        if p.returncode == 0:
            fails.append("D: ⛔ a control recording ALL 32 heads was ACCEPTED -- the S-246 collision")
        elif "S-246 COLLISION" not in out:
            fails.append("D: refused, but not by the identity check: %s"
                         % out.strip().splitlines()[-1][:140])
        else:
            print("[selftest] D ok: the S-246 collision is CAUGHT on a control arm")
        build(src, ctrls[3], -0.05 - 0.003, hs[ctrls[3]])          # restore

        # E -- mirror refusals
        p = run(os.path.join(tmp, "e1.json"),
                prereg=os.path.join(REPO, "configs", "dcs_csi_pr012_head_census_basket.json"))
        if p.returncode == 0 or "NO_RANK_TEST" not in (p.stdout + p.stderr):
            fails.append("E1: a CENSUS prereg was not refused")
        else:
            print("[selftest] E1 ok: a CENSUS prereg is refused")
        p = run(os.path.join(tmp, "e2.json"),
                prereg=os.path.join(REPO, "configs", "dcs_csi_pr011_head_all32_controls_basket.json"))
        if p.returncode == 0 or "no BT_SINGLE" not in (p.stdout + p.stderr):
            fails.append("E2: a K-head SUBSET prereg was not refused by name")
        else:
            print("[selftest] E2 ok: a K-head subset prereg is refused (that is W4's family)")

        # G -- R22 AMENDMENT 1: a POSITIVE candidate that still ranks 1 must NOT be a replication.
        #      Before the amendment this printed "E(BT_SINGLE) = +0.016024 ... rank 1 of 21 ...
        #      VERDICT: REPLICATES" -- a sign-flipped result certified, with GATE 1 passing because
        #      BT_KO is a different arm.
        lay(+0.30, {c: +0.60 + 0.01 * i for i, c in enumerate(ctrls)})
        p = run(os.path.join(tmp, "g.json"))
        if p.returncode != 0:
            fails.append("G: refused: %s" % (p.stdout + p.stderr).strip().splitlines()[-1][:140])
        else:
            j = json.load(open(os.path.join(tmp, "g.json")))
            if j["RANK"]["rank"] != 1:
                fails.append("G: fixture wrong -- expected the candidate to rank 1, got %s"
                             % j["RANK"]["rank"])
            elif j["VERDICT"].startswith("REPLICATES"):
                fails.append("G: ⛔ a POSITIVE candidate effect (%+.6f) at rank 1 was certified as "
                             "REPLICATES -- the sign clause is not enforced"
                             % j["E"]["BT_SINGLE"])
            elif j["RANK"].get("candidate_E_is_negative") is not False:
                fails.append("G: candidate_E_is_negative not reported as False")
            else:
                print("[selftest] G ok (R22 sign clause): rank 1 with E = %+.6f -> %s"
                      % (j["E"]["BT_SINGLE"], j["VERDICT"][:60]))

        # F -- TIE: a control EXACTLY equal to the candidate must count AGAINST it -> rank 2
        lay(-1.2, {ctrls[7]: -1.2})
        p = run(os.path.join(tmp, "f.json"))
        if p.returncode != 0:
            fails.append("F: refused: %s" % (p.stdout + p.stderr).strip().splitlines()[-1][:140])
        else:
            R = json.load(open(os.path.join(tmp, "f.json")))["RANK"]
            if R["rank"] != 2 or R["n_ties"] != 1:
                fails.append("F: a tie gave rank %s (ties=%s); ties must count AGAINST the candidate"
                             % (R["rank"], R["n_ties"]))
            else:
                print("[selftest] F ok: an exact tie counts AGAINST the candidate -> rank 2, p=%.6f"
                      % R["p"])
    finally:
        removed = 0
        for d in sorted(glob.glob(os.path.join(SCORE, PRE + "_*"))):
            shutil.rmtree(d, ignore_errors=True); removed += 1
        residue = len(glob.glob(os.path.join(SCORE, PRE + "_*")))
        shutil.rmtree(tmp, ignore_errors=True)
        print("[selftest] cleanup: removed %d | residue %d" % (removed, residue))
        if residue:
            fails.append("cleanup left %d dirs behind" % residue)

    print()
    if fails:
        for f in fails:
            print("FAIL: %s" % f)
        print("SELFTEST FAILED (%d)" % len(fails)); return 1
    print("SELFTEST PASSED"); return 0


if __name__ == "__main__":
    sys.exit(main())
