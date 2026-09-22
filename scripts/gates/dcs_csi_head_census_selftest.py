"""Does the CENSUS reader compute the right answer, and does it catch the S-246 COLLISION?

Ground truth is constructed, so every E is known before the tool runs. Rows are real rows with
logp_concept shifted by a per-arm constant.
⛔ NOTHING HERE IS A SCIENTIFIC RESULT. It is a unit test of arithmetic and of two refusals.

The case that matters: S-246 measured that a SINGLETON records the same prefill-edit count as HD_KO
(2016), so the dose check cannot tell them apart. Case D below builds a singleton whose config records
ALL 32 heads while its dose reads a perfectly legal 2016, and REQUIRES the reader to refuse it. If that
case ever passes, a mis-specified singleton can be read as one head carrying the entire effect.
"""
import glob, json, os, shutil, subprocess, sys, tempfile

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SCORE = os.path.join(REPO, "outputs", "boombness", "score_behavior")
STAMP = "20260922_000000_777777"
PRE = "csi5_selftest_census"
PREREG = os.path.join(REPO, "configs", "dcs_csi_pr012_head_census_basket.json")
DOSE = 2016


def build(src, arm, shift, heads, base=False, force_heads=None, force_dose=None):
    """heads = the prereg's list for this arm (None for HD_BASE/HD_KO).
    force_heads / force_dose let a case LIE about itself, to prove the reader catches it."""
    tag = "%s_%s" % (PRE, arm)
    dst = os.path.join(SCORE, "%s_%s" % (tag, STAMP))
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    cfg_p = os.path.join(dst, "config.json"); cfg = json.load(open(cfg_p))
    args = cfg.get("args", cfg)
    args["tag"], args["arm"] = tag, arm
    if base:
        args.pop("knockout_heads", None)
    elif arm == "HD_KO":
        args["knockout_heads"] = ""                       # omitted flag == all 32
    else:
        rec = force_heads if force_heads is not None else heads
        args["knockout_heads"] = "" if rec == "ALL" else ",".join(str(h) for h in rec)
    json.dump(cfg, open(cfg_p, "w"), indent=2)
    dose = 0 if base else (DOSE if arm == "HD_KO" else DOSE * len(heads))
    if force_dose is not None:
        dose = force_dose
    rp = os.path.join(dst, "results.jsonl")
    rows = [json.loads(l) for l in open(rp)]
    for r in rows:
        r["arm"] = arm
        r["logp_concept"] = float(r["logp_concept"]) + shift
        r["hook_n_prefill_edits"] = dose
        r["hook_n_edits"] = dose
        r["hook_n_decode_edits"] = 0
        r["hook_liveness_violations"] = None
    with open(rp, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    d = json.load(open(os.path.join(dst, "DONE.json"))); d["run_id"] = "%s_%s" % (tag, STAMP)
    json.dump(d, open(os.path.join(dst, "DONE.json"), "w"), indent=2)
    return dst


def run(out, extra=()):
    cmd = [sys.executable, "scripts/dcs_csi_head_census.py", "--prereg", PREREG,
           "--tag-prefix", PRE, "--split", "validation", "--expect-n", "24",
           "--B", "500", "--out", out] + list(extra)
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=1800)


def main():
    pr = json.load(open(PREREG)); hs = pr["head_sets"]
    src = sorted(glob.glob(os.path.join(SCORE, "csi3_w3_basket_W3_HD_8_*")))
    if len(src) != 1:
        sys.exit("need exactly one source run; got %d" % len(src))
    src = src[0]

    # GROUND TRUTH. Negative shift -> lower y_install -> negative E. Head 2's singleton is made the
    # strongest so the expected ordering is known; every other singleton is distinct and weaker.
    shifts = {"HD_BASE": 0.0, "HD_KO": -2.0, "HD_TOPK": -1.2, "HD_BOTK": -0.05}
    for h in range(32):
        shifts["SINGLE_%02d" % h] = -0.90 if h == 2 else -(0.02 + 0.005 * h)
    for i, k in enumerate(sorted(k for k in hs if k.startswith("LOO_"))):
        shifts[k] = -1.00 - 0.01 * i
    made, fails = [], []
    try:
        for arm, sh in shifts.items():
            made.append(build(src, arm, sh, hs.get(arm), base=(arm == "HD_BASE")))
        out = os.path.join(tempfile.gettempdir(), "selftest_census.json")

        # ---- CASE A: a well-formed family must PASS and recover the ordering ----
        p = run(out)
        print((p.stdout or "")[-1800:] + (p.stderr or ""))
        if p.returncode != 0:
            fails.append("A: a well-formed census family was REFUSED (rc=%d)" % p.returncode)
        else:
            j = json.load(open(out))
            E = j["E"]
            singles = sorted((k for k in E if k.startswith("SINGLE_")), key=lambda k: E[k])
            if singles[0] != "SINGLE_02":
                fails.append("A: strongest singleton is %s, ground truth is SINGLE_02" % singles[0])
            if not (E["HD_KO"] < E["HD_TOPK"] < E["SINGLE_02"] < 0):
                fails.append("A: anchor ordering wrong: KO %.4f TOPK %.4f S02 %.4f"
                             % (E["HD_KO"], E["HD_TOPK"], E["SINGLE_02"]))
            if j.get("NO_RANK_TEST") is not True or "rank" in json.dumps(j).lower().split('"loo')[0][:0] or False:
                fails.append("A: NO_RANK_TEST not asserted in the output")
            idd = j["GATE_0_and_identity"]["per_arm"]["SINGLE_02"]
            if idd.get("dose_is_diagnostic_of_identity") is not False:
                fails.append("A: a SINGLETON's dose was reported as identity-diagnostic -- S-246 says "
                             "it collides with HD_KO and is NOT")
            if json.load(open(out))["GATE_0_and_identity"]["per_arm"]["HD_TOPK"][
                    "dose_is_diagnostic_of_identity"] is not True:
                fails.append("A: an 8-head arm's dose should still be identity-diagnostic")
            print("[selftest] A ok: strongest singleton = %s, E = %+.6f" % (singles[0], E[singles[0]]))

        # ---- CASE D: THE S-246 COLLISION. A singleton that records ALL 32 heads, with a LEGAL dose ----
        build(src, "SINGLE_07", shifts["SINGLE_07"], hs["SINGLE_07"],
              force_heads="ALL", force_dose=DOSE)
        p = run(out + ".d")
        blob = (p.stdout or "") + (p.stderr or "")
        if p.returncode == 0:
            fails.append("D: ⛔ A SINGLETON RECORDING ALL 32 HEADS WAS ACCEPTED. This is exactly the "
                         "S-246 false positive: it would read as one head carrying the whole effect.")
        elif "S-246 COLLISION" not in blob:
            fails.append("D: refused, but not by the identity check -- message was: %s"
                         % blob.strip().splitlines()[-1][:160])
        else:
            print("[selftest] D ok: the S-246 collision is CAUGHT -- %s"
                  % [l for l in blob.splitlines() if "S-246 COLLISION" in l][0].strip()[:150])
        build(src, "SINGLE_07", shifts["SINGLE_07"], hs["SINGLE_07"])          # restore

        # ---- CASE E: a WRONG head list with the RIGHT dose must be refused ----
        build(src, "SINGLE_09", shifts["SINGLE_09"], hs["SINGLE_09"], force_heads=[31])
        p = run(out + ".e")
        blob = (p.stdout or "") + (p.stderr or "")
        if p.returncode == 0:
            fails.append("E: an arm whose recorded heads were [31] but preregistered [9] was ACCEPTED")
        elif "!= prereg" not in blob:
            fails.append("E: refused for the wrong reason: %s" % blob.strip().splitlines()[-1][:160])
        else:
            print("[selftest] E ok: a mismatched head list is refused")
        build(src, "SINGLE_09", shifts["SINGLE_09"], hs["SINGLE_09"])          # restore

        # ---- CASE F: the mirror refusal -- a RANK prereg must be refused by this reader ----
        p = subprocess.run([sys.executable, "scripts/dcs_csi_head_census.py",
                            "--prereg", os.path.join(REPO, "configs",
                                                     "dcs_csi_pr011_head_all32_controls_basket.json"),
                            "--tag-prefix", PRE, "--split", "validation", "--expect-n", "24",
                            "--out", out + ".f"], cwd=REPO, capture_output=True, text=True)
        if p.returncode == 0 or "does not declare NO_RANK_TEST" not in (p.stdout or "") + (p.stderr or ""):
            fails.append("F: the census reader did not refuse a RANK-TEST preregistration")
        else:
            print("[selftest] F ok: a RANK prereg is refused by the census reader")
    finally:
        removed = 0
        for d in sorted(glob.glob(os.path.join(SCORE, PRE + "_*"))):
            shutil.rmtree(d, ignore_errors=True); removed += 1
        residue = len(glob.glob(os.path.join(SCORE, PRE + "_*")))
        print("[selftest] cleanup: removed %d | residue %d" % (removed, residue))
        if residue:
            fails.append("cleanup left %d dirs behind" % residue)

    print()
    if fails:
        for f in fails:
            print("FAIL: %s" % f)
        print("SELFTEST FAILED (%d)" % len(fails))
        return 1
    print("SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
