import json, os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
G2 = os.path.join(HERE, "..", "p6_g2.py")
IDS = [(f"p{dom}_{i}", f"d{dom}") for dom in range(20) for i in range(5)]


def build(root, cw, job, shifts, bank_cw=None, drop=0):
    """20 domains x 5 rows; shifts = {arm: logit offset}. bank_cw != cw simulates a wrong-bank run; drop removes rows."""
    os.makedirs(os.path.join(root, "outputs/heretic_csi/p6"), exist_ok=True)
    os.makedirs(os.path.join(root, "reports/heretic_csi"), exist_ok=True)
    os.makedirs(os.path.join(root, "data/boombness_prompts"), exist_ok=True)
    os.makedirs(os.path.join(root, "runargs/heretic_csi/p6"), exist_ok=True)
    json.dump({"codeword": cw, "status": "G3_PASS"}, open(os.path.join(root, f"outputs/heretic_csi/p6/stage0_{cw}.json"), "w"))
    with open(os.path.join(root, f"data/boombness_prompts/boombness_prompt_bank_ts116m_{cw}_bomb.jsonl"), "w") as f:
        for pid, dom in IDS:
            f.write(json.dumps({"prompt_id": pid, "domain": dom, "query_kind": "semantic_one_word", "condition": "natural_doublespeak",
                                "n_examples": 4, "bank_block": "cds_n4_sow"}) + "\n")
    open(os.path.join(root, f"runargs/heretic_csi/p6/exclude_{cw}_bomb_sow_train.txt"), "w").write("# none\n")
    for arm, off in shifts.items():
        d = os.path.join(root, f"outputs/boombness/score_behavior/hcsi_p6g2_{cw}_{arm}_20261015_010203_{1000 + len(arm)}")
        os.makedirs(d, exist_ok=True)
        json.dump({"slurm_job_id": job, "argv": f"--bank data/boombness_prompts/boombness_prompt_bank_ts116m_{bank_cw or cw}_bomb.jsonl"},
                  open(os.path.join(d, "RUNMETA.json"), "w"))
        open(os.path.join(d, "DONE.json"), "w").write("{}")
        with open(os.path.join(d, "results.jsonl"), "w") as f:
            for j, (pid, dom) in enumerate(IDS):
                if arm == "KO" and j < drop:
                    continue
                base = ((int(dom[1:]) * 7 + j % 5 * 3) % 11 - 5) / 5.0
                f.write(json.dumps({"prompt_id": pid, "domain": dom, "logp_concept": base + off, "logp_codeword": 0.0}) + "\n")


def run(shifts, **kw):
    with tempfile.TemporaryDirectory() as t:
        build(t, "zz", "77", shifts, **kw)
        out = subprocess.run([sys.executable, G2, "zz", "--job", "77"], env={**os.environ, "P6_REPO": t}, capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        res = json.loads(out.stdout)
        man = json.load(open(os.path.join(t, "outputs/heretic_csi/p6/stage0_zz.json")))
        assert man["g2_status"] == res["G2"] and man["g2"]["G2"] == res["G2"] and os.path.exists(os.path.join(t, "reports/heretic_csi/hcsi_p6_g2_zz.json"))
        return res


LIVE = {"BASE": 1.0, "KO": -1.0, "KO_SELF": -1.0, "KO_FULL": 0.5}


def test_live_passes():
    r = run(LIVE)
    assert r["G2"] == "PASS" and r["KO_SELF_minus_KO"]["point"] == 0 and r["n_paired_rows"] == 100 and not r["errors"]


def test_dead_knockout_fails():
    assert run({"BASE": 1.0, "KO": 1.0, "KO_SELF": 1.0, "KO_FULL": 1.5})["G2"] == "FAIL"


def test_no_rescue_fails():
    assert run({"BASE": 1.0, "KO": -1.0, "KO_SELF": -1.0, "KO_FULL": -1.0})["G2"] == "FAIL"


def test_wrong_bank_is_error():
    r = run(LIVE, bank_cw="lamp")
    assert r["G2"] == "ERROR" and any("codeword_guard" in e for e in r["errors"])


def test_missing_rows_is_error():
    r = run(LIVE, drop=3)
    assert r["G2"] == "ERROR" and any("KO: scored 97 rows" in e for e in r["errors"])


def test_ko_glob_does_not_match_ko_full():
    pat = re.compile(r"^hcsi_p6g2_zz_KO_\d{8}_\d{6}_\d+$")
    assert pat.match("hcsi_p6g2_zz_KO_20261015_010203_1") and not pat.match("hcsi_p6g2_zz_KO_FULL_20261015_010203_1")
