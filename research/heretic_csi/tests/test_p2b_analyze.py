"""PASS-rule tests for p2b_analyze (review 2026-10-14 #2). CPU only; imports the frozen analyzer helpers."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import p2b_analyze as pa   # noqa: E402

OK = {"status": "ok", "point": 0.2, "ci95": [0.05, 0.35]}
NEG = {"status": "ok", "point": -0.1, "ci95": [-0.3, -0.02]}


def test_candidate_less_damaging_than_controls_but_negative_recovery_does_not_pass():
    # rank p tiny (candidate above every control because controls DAMAGE installation) but recovery < 0
    stat = {"C": -0.01, **{f"R{i}": -0.05 for i in range(81)}}
    rp = pa.rank_p(stat, "C", [f"R{i}" for i in range(81)])
    assert rp["rank"] == 1 and rp["p"] < 0.05
    v = pa.decide(True, True, [], pa.holm({1: rp["p"], 4: 0.5})[1], NEG)
    assert v.startswith("DOES NOT PASS") and "CI lower bound" in v


def test_pass_requires_holm_and_ci():
    assert pa.decide(True, True, [], 0.02, OK).startswith("PASS")
    assert pa.decide(True, True, [], 0.06, OK).startswith("DOES NOT PASS")
    assert pa.decide(False, True, [], 0.001, OK).startswith("DESCRIPTIVE")
    assert pa.decide(True, True, ["x"], 0.001, OK).startswith("VOID")
    assert pa.decide(True, False, [], 0.001, OK).startswith("CANNOT ANSWER")


def test_holm_and_ties():
    h = pa.holm({1: 0.0122, 4: 0.03})
    assert abs(h[1] - 0.0244) < 1e-12 and abs(h[4] - 0.03) < 1e-12
    stat = {"C": 0.1, "a": 0.1, "b": 0.0}
    assert pa.rank_p(stat, "C", ["a", "b"])["rank"] == 2      # ties count AGAINST the candidate
