import json, math, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
DRV = os.path.join(HERE, "..", "p6_dev_draw_driver.py")
sys.path.insert(0, os.path.join(HERE, ".."))
import p6_dev_draw  # noqa: E402


def setup(root, override=None):
    os.makedirs(os.path.join(root, "outputs/heretic_csi/p6"), exist_ok=True); os.makedirs(os.path.join(root, "configs/heretic_csi"), exist_ok=True)
    for i, cw in enumerate(sorted(p6_dev_draw.ZIPF)):
        m = {"g3_status": "PASS", "g1_status": "PASS", "g2_status": "PASS", "g1": {"install_strength_C_minus_A": 0.1 + 0.03 * i}}
        if override and cw in override:
            m.update(override[cw])
        json.dump(m, open(os.path.join(root, f"outputs/heretic_csi/p6/stage0_{cw}.json"), "w"))


def run(root, *args):
    return subprocess.run([sys.executable, DRV, *args], env={**os.environ, "P6_REPO": root}, capture_output=True, text=True)


def test_refuses_undecided_g2():
    with tempfile.TemporaryDirectory() as t:
        setup(t, {"lamp": {"g2_status": "UNDECIDED"}})
        r = run(t); assert r.returncode == 2 and "lamp: g2_status=UNDECIDED" in r.stdout
        assert not os.path.exists(os.path.join(t, "configs/heretic_csi/P6_DEV_DRAW.json"))


def test_refuses_nan_strength():
    with tempfile.TemporaryDirectory() as t:
        setup(t, {"kettle": {"g1": {"install_strength_C_minus_A": float("nan")}}})
        assert run(t).returncode == 2


def test_g3_fail_needs_no_g1_g2_and_draws_once():
    with tempfile.TemporaryDirectory() as t:
        setup(t, {"lamp": {"g3_status": "FAIL", "g1_status": "NOT_APPLICABLE_G3_FAIL", "g2_status": "NOT_APPLICABLE_G3_FAIL", "g1": None},
                  "chair": {"g1_status": "FAIL", "g2_status": "UNDECIDED"}})
        assert run(t, "--check").returncode == 0 and not os.path.exists(os.path.join(t, "configs/heretic_csi/P6_DEV_DRAW.json"))
        r = run(t); assert r.returncode == 0, r.stdout + r.stderr
        d = json.load(open(os.path.join(t, "configs/heretic_csi/P6_DEV_DRAW.json")))
        assert d["n_survivors"] == 18 and len(d["draw"]["dev"]) == 5 and "lamp" not in d["draw"]["dev"] + d["draw"]["confirmation"]
        assert len(d["manifest_sha256"]) == 20
        assert run(t).returncode == 3  # never re-drawn
