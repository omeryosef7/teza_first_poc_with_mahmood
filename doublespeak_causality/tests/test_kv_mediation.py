"""
tests/test_kv_mediation.py — positive control for 44_kv_mediation.py's reducer (S3,
NEXT_CAUSAL_SPRINT). CPU-only, no model. Mirrors tests/test_transplant_mediation.py.

Builds synthetic per-(prompt, window, cell) rows with KNOWN p_concept, then checks the
reducer recovers the hand-computed estimands exactly:
  ReRead_test   = mean(C1 - C3)
  DE_via_demoKV = mean(C2 - C4)
  INT_2x2       = mean((C1-C3) - (C2-C4))
  faithfulness  = mean(C1_selfswap - C1) == 0
  random_control= mean(C1 - random_control)

Run:  python doublespeak_causality/tests/test_kv_mediation.py
      pytest doublespeak_causality/tests/test_kv_mediation.py
"""
import os
import sys
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
DSC = os.path.dirname(HERE)
sys.path.insert(0, DSC)


def _load_kv():
    spec = importlib.util.spec_from_file_location(
        "kv_mediation", os.path.join(DSC, "44_kv_mediation.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


GROUP = "mid"
N_ITEMS = 10                                        # >= MIN_N so CIs are reliable

# Per-item cell values, chosen so every paired difference is an EXACT constant:
#   C1 - C3 = 0.60 ;  C2 - C4 = 0.20 ;  INT = 0.40 ;  selfswap - C1 = 0 ;  C1 - rand = 0.01
def _cell(cell, i):
    base = 0.01 * i                                 # per-item offset, differences it out
    return {"C1": 0.80 + base, "C2": 0.30 + base, "C3": 0.20 + base,
            "C4": 0.10 + base, "C1_selfswap": 0.80 + base,
            "random_control": 0.79 + base}[cell]


def _rows():
    rows = []
    for i in range(N_ITEMS):
        readout = f"probe{i}"                        # encodes the item key
        for cell in ("C1", "C2", "C3", "C4", "C1_selfswap", "random_control"):
            v = _cell(cell, i)
            rows.append({"sid": f"DOUBLESPEAK|dev|s|4|{readout}",
                         "condition": "DOUBLESPEAK", "split": "dev", "demo_style": "s",
                         "n_demos": 4, "readout": readout, "window": GROUP, "cell": cell,
                         "p_concept": v, "p_codeword": 1 - v, "ps_concept": v,
                         "ps_codeword": 1 - v})
    return rows


def _eff(res, name):
    return res["estimands"][f"{name}|{GROUP}"]["effect"]


def test_estimands_match_hand_computed():
    res = _load_kv().analyze_rows(_rows(), "p_concept")
    exp = {"ReRead_test": 0.60, "DE_via_demoKV": 0.20, "INT_2x2": 0.40,
           "faithfulness": 0.00, "random_control": 0.01}
    for name, e in exp.items():
        got = _eff(res, name)
        assert abs(got - e) < 1e-9, f"{name}: expected {e}, got {got}"
        assert res["estimands"][f"{name}|{GROUP}"]["n"] == N_ITEMS


def test_faithfulness_selfswap_is_zero():
    res = _load_kv().analyze_rows(_rows(), "p_concept")
    f = res["estimands"][f"faithfulness|{GROUP}"]
    assert abs(f["effect"]) < 1e-12, "C1_selfswap must equal C1 (faithfulness == 0)"
    assert res["verdicts"][GROUP]["faithful_selfswap"] is True


def test_verdicts_directional():
    res = _load_kv().analyze_rows(_rows(), "p_concept")
    v = res["verdicts"][GROUP]
    assert v["reread_dependent_on_demoKV"] is True   # ReRead 0.60 >= 0.05
    assert v["demoKV_carries_concept"] is True        # DE 0.20 >= 0.05
    assert v["random_control_inert"] is True          # |0.01| < 0.05


def test_patchscope_metric_also_reduces():
    res = _load_kv().analyze_rows(_rows(), "ps_concept")
    assert abs(_eff(res, "ReRead_test") - 0.60) < 1e-9
    assert abs(_eff(res, "INT_2x2") - 0.40) < 1e-9


def test_patchscope_gate_argmax_and_threshold():
    g = _load_kv().patchscope_gate
    # argmax layer, its value, and pass/fail on the 0.1 positive-control threshold
    best, mx, ok = g([0.01, 0.02, 0.55, 0.30])
    assert best == 2 and abs(mx - 0.55) < 1e-12 and ok is True
    # all below threshold -> control FAILS but argmax still returned
    best, mx, ok = g([0.01, 0.09, 0.05])
    assert best == 1 and abs(mx - 0.09) < 1e-12 and ok is False
    # empty scores -> safe default, not usable
    assert g([]) == (0, 0.0, False)
    # exactly at the threshold is NOT a pass (strict >)
    assert g([0.1])[2] is False


TESTS = [test_estimands_match_hand_computed, test_faithfulness_selfswap_is_zero,
         test_verdicts_directional, test_patchscope_metric_also_reduces,
         test_patchscope_gate_argmax_and_threshold]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS) - fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
