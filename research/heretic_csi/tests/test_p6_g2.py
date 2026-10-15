import json, math, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
G2 = os.path.join(HERE, "..", "p6_g2.py")


def build(root, cw, job, shifts):
    """shifts = {arm: logit offset}; 20 domains x 5 rows; KO lowers y, FULL restores (unless overridden)."""
    os.makedirs(os.path.join(root, "outputs/heretic_csi/p6"), exist_ok=True)
    json.dump({"codeword": cw, "status": "G3_PASS"}, open(os.path.join(root, f"outputs/heretic_csi/p6/stage0_{cw}.json"), "w"))
    for arm, off in shifts.items():
        d = os.path.join(root, f"outputs/boombness/score_behavior/hcsi_p6g2_{cw}_{arm}_20261015_010203_{1000 + len(arm)}")
        os.makedirs(d, exist_ok=True)
        json.dump({"slurm_job_id": job}, open(os.path.join(d, "RUNMETA.json"), "w")); open(os.path.join(d, "DONE.json"), "w").write("{}")
        with open(os.path.join(d, "results.jsonl"), "w") as f:
            for dom in range(20):
                for i in range(5):
                    base = ((dom * 7 + i * 3) % 11 - 5) / 5.0
                    f.write(json.dumps({"prompt_id": f"p{dom}_{i}", "domain": f"d{dom}", "logp_concept": base + off, "logp_codeword": 0.0}) + "\n")


def run(shifts):
    with tempfile.TemporaryDirectory() as t:
        build(t, "zz", "77", shifts)
        out = subprocess.run([sys.executable, G2, "zz", "--job", "77"], env={**os.environ, "P6_REPO": t}, capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        return json.loads(out.stdout)


def test_live_passes():
    r = run({"BASE": 1.0, "KO": -1.0, "KO_SELF": -1.0, "KO_FULL": 0.5})
    assert r["G2"] == "PASS" and r["KO_SELF_minus_KO"]["point"] == 0 and r["n_paired_rows"] == 100


def test_dead_knockout_fails():
    assert run({"BASE": 1.0, "KO": 1.0, "KO_SELF": 1.0, "KO_FULL": 1.5})["G2"] == "FAIL"


def test_no_rescue_fails():
    assert run({"BASE": 1.0, "KO": -1.0, "KO_SELF": -1.0, "KO_FULL": -1.0})["G2"] == "FAIL"


def test_ko_glob_does_not_match_ko_full():
    import re
    pat = re.compile(r"^hcsi_p6g2_zz_KO_\d{8}_\d{6}_\d+$")
    assert pat.match("hcsi_p6g2_zz_KO_20261015_010203_1") and not pat.match("hcsi_p6g2_zz_KO_FULL_20261015_010203_1")
