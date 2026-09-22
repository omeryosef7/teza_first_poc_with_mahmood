"""Prove the PR-CSI-013 freezer executes S-248's rule correctly -- BOTH BRANCHES -- before the census
exists. Synthetic census reports only; ⛔ NOTHING HERE IS A SCIENTIFIC RESULT.

Synthetic files are written to a scratch dir and NEVER to reports/ (S-224: a dry run once overwrote a
tracked, committed report; `git checkout` restored it only because it happened to be committed).
"""
import json, os, subprocess, sys, tempfile

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
TOOL = "scripts/gates/dcs_csi_pr013_freeze.py"


def census(strong_head, strong_E, ci, botk=-0.0126):
    E, CI = {}, {}
    for h in range(32):
        k = "SINGLE_%02d" % h
        E[k] = strong_E if h == strong_head else -(0.001 + 0.0002 * h)
        CI[k] = ci if h == strong_head else [E[k] - 0.0005, E[k] + 0.0005]
    E["HD_BOTK"], CI["HD_BOTK"] = botk, [botk - 0.004, botk + 0.004]
    E["HD_KO"], E["HD_TOPK"] = -0.2270, -0.1960
    CI["HD_KO"], CI["HD_TOPK"] = [-0.276, -0.179], [-0.243, -0.153]
    return {"schema": "dcs_csi_head_census/1", "prereg_id": "PR-CSI-012",
            "NO_RANK_TEST": True, "E": E, "ci95": CI}


def run(obj, tmp, name, check=True):
    p = os.path.join(tmp, name)
    json.dump(obj, open(p, "w"), indent=2)
    cmd = [sys.executable, TOOL, "--census", p, "--out", os.path.join(tmp, "pr013.json")]
    if check:
        cmd.append("--check")
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


def main():
    tmp = tempfile.mkdtemp(prefix="pr013_selftest_")
    fails = []

    # A -- GO branch. SINGLE_14 strongest, |E| well above |HD_BOTK|, ci excludes 0.
    p = run(census(14, -0.0850, [-0.1100, -0.0600]), tmp, "go.json")
    out = p.stdout + p.stderr
    if p.returncode != 0:
        fails.append("A: GO branch refused: %s" % out.strip().splitlines()[-1][:140])
    else:
        if "h* = 14" not in out:
            fails.append("A: nominated the wrong head: %s" % out.splitlines()[0][:140])
        if "GATE: GO" not in out:
            fails.append("A: Rule 2 did not report GO")
        print("[selftest] A ok (GO): %s" % [l for l in out.splitlines() if "RULE 1" in l][0].strip())

    # B -- NO-GO: every singleton weaker than HD_BOTK.
    p = run(census(14, -0.0050, [-0.0070, -0.0030]), tmp, "nogo_small.json")
    out = p.stdout + p.stderr
    if p.returncode == 0:
        fails.append("B: ⛔ emitted a prereg although |E(SINGLE_h*)| < |E(HD_BOTK)| -- Rule 2(b) is "
                     "not being enforced and PR-013 would be fishing")
    elif "MUST NOT LAUNCH" not in out:
        fails.append("B: refused for the wrong reason: %s" % out.strip().splitlines()[-1][:140])
    else:
        print("[selftest] B ok (NO-GO on magnitude): stopped as preregistered")

    # C -- NO-GO: large enough, but the ci95 straddles 0.
    p = run(census(14, -0.0850, [-0.1800, +0.0100]), tmp, "nogo_ci.json")
    out = p.stdout + p.stderr
    if p.returncode == 0:
        fails.append("C: ⛔ emitted a prereg although the ci95 includes 0")
    elif "MUST NOT LAUNCH" not in out:
        fails.append("C: refused for the wrong reason: %s" % out.strip().splitlines()[-1][:140])
    else:
        print("[selftest] C ok (NO-GO on ci95 straddling 0)")

    # D -- tie-break: two heads with IDENTICAL E; the more negative ci LOWER bound must win.
    c = census(14, -0.0850, [-0.1100, -0.0600])
    c["E"]["SINGLE_03"] = -0.0850
    c["ci95"]["SINGLE_03"] = [-0.0900, -0.0800]        # lower bound LESS negative than head 14's
    p = run(c, tmp, "tie.json")
    out = p.stdout + p.stderr
    if "h* = 14" not in out:
        fails.append("D: tie broken the wrong way -- head 14's ci lower bound (-0.1100) is more "
                     "negative than head 3's (-0.0900): %s" % out.splitlines()[0][:140])
    else:
        print("[selftest] D ok: tie broken by the more negative ci95 lower bound")

    # E -- the emitted family: 24 arms, 20 DISTINCT controls, h* excluded, floor exact.
    p = run(census(14, -0.0850, [-0.1100, -0.0600]), tmp, "emit.json", check=False)
    if p.returncode != 0:
        fails.append("E: emit failed: %s" % (p.stdout + p.stderr).strip().splitlines()[-1][:140])
    else:
        pr = json.load(open(os.path.join(tmp, "pr013.json")))
        hs = pr["head_sets"]
        ctrl = [hs["BT_CTRL_%02d" % i][0] for i in range(20)]
        if pr["n_arms_per_split"] != 23:
            fails.append("E: %d arms, expected 23 (BT_BASE + BT_KO + BT_SINGLE + 20)"
                         % pr["n_arms_per_split"])
        if len(set(ctrl)) != 20:
            fails.append("E: controls not distinct: %s" % ctrl)
        if 14 in ctrl:
            fails.append("E: ⛔ h* entered its own control family")
        if abs(pr["attainable_floor"]["floor_p"] - 1.0 / 21) > 1e-12:
            fails.append("E: floor is %r, not 1/21 exactly" % pr["attainable_floor"]["floor_p"])
        if hs["BT_SINGLE"] != [14]:
            fails.append("E: BT_SINGLE is %s, expected [14]" % hs["BT_SINGLE"])
        print("[selftest] E ok: 23 arms, 20 distinct controls %s, h* excluded, floor 1/21 exact"
              % (ctrl[:6] + ["..."]))

    # F -- DETERMINISM: the same census must emit the same controls, twice.
    p2 = run(census(14, -0.0850, [-0.1100, -0.0600]), tmp, "emit2.json", check=False)
    pr2 = json.load(open(os.path.join(tmp, "pr013.json")))
    if pr2["head_sets"] != pr["head_sets"]:
        fails.append("F: the draw is NOT deterministic across runs")
    else:
        print("[selftest] F ok: the control draw is deterministic")

    import shutil; shutil.rmtree(tmp, ignore_errors=True)
    print()
    if fails:
        for f in fails:
            print("FAIL: %s" % f)
        print("SELFTEST FAILED (%d)" % len(fails)); return 1
    print("SELFTEST PASSED"); return 0


if __name__ == "__main__":
    sys.exit(main())
