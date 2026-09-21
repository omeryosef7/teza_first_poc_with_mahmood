"""Does W4 compute the RIGHT ANSWER when the gates pass? The dry run only proved it refuses.

Ground truth is constructed here, so the expected rank, E and F are known exactly before the
analyser runs. Rows are real rows with logp_concept SHIFTED by a per-arm constant -- the shift is
synthetic and is the point: an estimator is tested against an answer you already know.
⛔ NOTHING HERE IS A SCIENTIFIC RESULT. It is a unit test of arithmetic.
"""
import json, math, os, shutil, subprocess, sys, glob, tempfile

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SCORE = os.path.join(REPO, "outputs", "boombness", "score_behavior")
STAMP = "20260921_000000_888888"
PRE = "csi3_selftest_head"
PREREG = os.path.join(REPO, "configs", "dcs_csi_pr010_head_causal_basket.json")


def build(src, arm, shift, base_arm):
    tag = "%s_%s" % (PRE, arm)
    dst = os.path.join(SCORE, "%s_%s" % (tag, STAMP))
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    cfg_p = os.path.join(dst, "config.json"); cfg = json.load(open(cfg_p))
    (cfg.get("args", cfg))["tag"] = tag; (cfg.get("args", cfg))["arm"] = arm
    json.dump(cfg, open(cfg_p, "w"), indent=2)
    rp = os.path.join(dst, "results.jsonl")
    rows = [json.loads(l) for l in open(rp)]
    for r in rows:
        r["arm"] = arm
        r["logp_concept"] = float(r["logp_concept"]) + shift
        # GATE 0 wants BASE unintervened and every other arm live in prefill only.
        if base_arm:
            r["hook_n_prefill_edits"] = 0; r["hook_n_edits"] = 0
        else:
            r["hook_n_prefill_edits"] = 2016 if arm == "HD_KO" else 2016 * 8
        r["hook_n_decode_edits"] = 0
        r["hook_liveness_violations"] = None
    with open(rp, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    d = json.load(open(os.path.join(dst, "DONE.json"))); d["run_id"] = "%s_%s" % (tag, STAMP)
    json.dump(d, open(os.path.join(dst, "DONE.json"), "w"), indent=2)
    return dst


def main():
    pr = json.load(open(PREREG))
    ctrls = sorted(k for k in pr["head_sets"] if k.startswith("HD_RAND"))
    src = sorted(glob.glob(os.path.join(SCORE, "csi3_w3_basket_W3_HD_8_*")))
    if len(src) != 1:
        sys.exit("need exactly one source run; got %d" % len(src))
    src = src[0]

    # GROUND TRUTH: shifts in log-odds. Negative shift -> lower y_install -> negative E.
    # HD_TOPK is made the STRONGEST (most negative) so the expected rank is 1 of 21.
    shifts = {"HD_BASE": 0.0, "HD_KO": -2.0, "HD_TOPK": -1.2, "HD_BOTK": -0.05}
    for i, c in enumerate(ctrls):
        shifts[c] = -0.10 - 0.01 * i          # all weaker than HD_TOPK, all distinct
    made = []
    try:
        for arm, sh in shifts.items():
            made.append(build(src, arm, sh, arm == "HD_BASE"))
        out = os.path.join(tempfile.gettempdir(), "selftest_head.json")
        cmd = [sys.executable, "scripts/dcs_csi_head_analyze.py", "--prereg", PREREG,
               "--tag-prefix", PRE, "--split", "validation", "--expect-n", "24",
               "--B", "2000", "--out", out]
        p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=900)
        print((p.stdout or "") + (p.stderr or ""))
        if p.returncode != 0:
            return 1
        r = json.load(open(out))
        fails = []

        def chk(ok, label, detail=""):
            print("  %-4s %-52s %s" % ("PASS" if ok else "FAIL", label, detail))
            if not ok:
                fails.append(label)

        print("GROUND-TRUTH CHECKS (the answer was known before the analyser ran)")
        chk(r["GATE_0_liveness"]["pass"], "GATE 0 passes on well-formed liveness")
        chk(r["REALISED_DOSE"]["pass"], "the realised-dose identity passes at ratio K=8")
        chk(r["GATE_1_positive_control"]["pass"], "GATE 1 passes (E(HD_KO) clearly negative)",
            "E=%.5f ci %s" % (r["E"]["HD_KO"], [round(x, 4) for x in r["ci95"]["HD_KO"]]))
        chk(r["rank_test"]["rank"] == 1, "HD_TOPK ranks 1 (it was BUILT strongest)",
            "rank %d of %d" % (r["rank_test"]["rank"], r["rank_test"]["of"]))
        chk(r["rank_test"]["of"] == 21, "the family is 21 = 20 controls + candidate")
        chk(abs(r["rank_test"]["p"] - r["rank_test"]["attainable_floor"]) < 1e-9,
            "rank 1 gives p == the attainable floor", "p=%.6f floor=%.6f"
            % (r["rank_test"]["p"], r["rank_test"]["attainable_floor"]))
        chk(r["E"]["HD_KO"] < r["E"]["HD_TOPK"] < r["E"]["HD_BOTK"] < 0,
            "E ordering matches the constructed shifts")
        # F is a RATIO OF MEANS, not the ratio of the shifts; check it is sane and bracketed
        chk(r["F"] is not None and 0 < r["F"] < 1, "F is a fraction of the ceiling",
            "F=%.4f ci %s" % (r["F"], r["F_ci95"]))
        chk(r["F_ci95"] is not None and not (r["F_ci95"][0] <= 0 <= r["F_ci95"][1]),
            "F's ci95 excludes 0")
        exp = "WE FOUND (part of) THE WRITER" if (r["F"] or 0) >= 0.5 else "PARTIALLY LOCALISED"
        chk(r["VERDICT"] == exp, "the verdict matches the branch the numbers select",
            "%r" % r["VERDICT"])
        chk(r["TRAIN_CAVEAT"] is None, "no TRAIN caveat on a validation run")
        print()
        print("SELFTEST %s" % ("PASSED" if not fails else "FAILED: " + "; ".join(fails)))
        return 1 if fails else 0
    finally:
        n = 0
        for d in made:
            try:
                shutil.rmtree(d); n += 1
            except OSError as e:
                print("CLEANUP FAILED %s: %r" % (d, e), file=sys.stderr)
        left = glob.glob(os.path.join(SCORE, "csi3_selftest_*"))
        print("[selftest] cleanup: removed %d of %d | residue %d" % (n, len(made), len(left)))


if __name__ == "__main__":
    raise SystemExit(main())
