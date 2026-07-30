"""
tests/test_toctou_analysis.py — positive control for 45_toctou_factorial.analyze_rows
(STAGE4 §(e)). CPU-only, no model, no harmful text. Modeled on test_transplant_mediation.py.

Builds synthetic rows with KNOWN per-cell P(MALICIOUS) and asserts the reducer recovers the
hand-computed concept_effect / refusal_gain / INTERACTION exactly, pairs on item, and
excludes EMPTY cells from the estimand denominators (C8 lesson).

Run:  python doublespeak_causality/tests/test_toctou_analysis.py
      pytest doublespeak_causality/tests/test_toctou_analysis.py -q
"""
import os
import sys
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
DSC = os.path.dirname(HERE)
sys.path.insert(0, DSC)

_spec = importlib.util.spec_from_file_location("m45", os.path.join(DSC, "45_toctou_factorial.py"))
m45 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m45)

N = 10
# per-cell MALICIOUS threshold: item index < thr => MALICIOUS, else BENIGN.
THR = {("A", None): 0, ("C", None): 0,
       ("B", "early"): 2, ("B", "mid"): 2, ("B", "late"): 3,
       ("D", "early"): 7, ("D", "mid"): 5, ("D", "late"): 4}


def _cat(cell, timing, i):
    return "MALICIOUS" if i < THR[(cell, timing)] else "BENIGN"


def _rows(n=N, empty_cell=None):
    rows = []
    for i in range(n):
        for (cell, timing), _ in THR.items():
            cat = "EMPTY" if (cell, timing) == empty_cell and i == n - 1 else _cat(cell, timing, i)
            rows.append({"pid": f"p{i}", "cell": cell, "timing": timing, "arm": "main",
                         "cat": cat, "p_concept": 0.1, "p_codeword": 0.2})
        # a control row that must be IGNORED by the reducer (arm != main)
        rows.append({"pid": f"p{i}", "cell": "B", "timing": "early", "arm": "concept_rand",
                     "cat": "MALICIOUS", "p_concept": 0.9, "p_codeword": 0.05})
    return rows


def _mal(res, est, t):
    return res["outcomes"]["MALICIOUS"][est][t]


def test_concept_effects_match_hand_computed():
    res = m45.analyze_rows(_rows())
    assert abs(_mal(res, "concept_effect_noablate", "early")["effect"] - 0.2) < 1e-9
    assert abs(_mal(res, "concept_effect_noablate", "late")["effect"] - 0.3) < 1e-9
    assert abs(_mal(res, "concept_effect_ablate", "early")["effect"] - 0.7) < 1e-9
    assert abs(_mal(res, "concept_effect_ablate", "late")["effect"] - 0.4) < 1e-9
    for t in ("early", "late"):
        assert _mal(res, "concept_effect_noablate", t)["n"] == N


def test_refusal_gain_and_interaction():
    res = m45.analyze_rows(_rows())
    assert abs(_mal(res, "refusal_gain", "early")["effect"] - 0.5) < 1e-9
    assert abs(_mal(res, "refusal_gain", "late")["effect"] - 0.1) < 1e-9
    inter = res["outcomes"]["MALICIOUS"]["INTERACTION"]
    assert abs(inter["effect"] - 0.4) < 1e-9, f"INTERACTION {inter['effect']}"
    assert inter["n"] == N


def test_control_rows_ignored():
    # The concept_rand rows would push B_early to all-MALICIOUS if not filtered.
    res = m45.analyze_rows(_rows())
    assert res["per_cell_malicious_rate"]["B_early"]["malicious_rate"] == 0.2


def test_empty_cell_excluded_from_estimand():
    # item p9 has EMPTY in D_early -> excluded from the INTERACTION pairing (needs all cells).
    res = m45.analyze_rows(_rows(empty_cell=("D", "early")))
    inter = res["outcomes"]["MALICIOUS"]["INTERACTION"]
    assert inter["n"] == N - 1, f"EMPTY item must be dropped, n={inter['n']}"
    # concept_effect_ablate(early) also loses that item (D_early undefined)
    assert _mal(res, "concept_effect_ablate", "early")["n"] == N - 1
    # but a timing that does NOT involve the empty cell keeps all items
    assert _mal(res, "concept_effect_ablate", "late")["n"] == N


TESTS = [test_concept_effects_match_hand_computed, test_refusal_gain_and_interaction,
         test_control_rows_ignored, test_empty_cell_excluded_from_estimand]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS)-fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
