"""
tests/test_repr_toctou.py — positive control for 47_repr_toctou.analyze_rows (NEXT3 §T3).

CPU-only, no model, no harmful text. Builds synthetic per-item L18-refusal-projection rows with
KNOWN early/late/baseline values and asserts the reducer recovers the early-late paired estimand,
pairs on pid within a pair, pools per-item diffs ACROSS pairs, and reports the random control ~0.

Run:  python doublespeak_causality/tests/test_repr_toctou.py
      pytest doublespeak_causality/tests/test_repr_toctou.py -q
"""
import os
import sys
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
DSC = os.path.dirname(HERE)
sys.path.insert(0, DSC)

_spec = importlib.util.spec_from_file_location("m47", os.path.join(DSC, "47_repr_toctou.py"))
m47 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m47)

N = 12


def _rows_one_pair(pair="bomb", early_gain=0.30, late_gain=0.05, rand_gain=0.0,
                   base=1.0, jitter=0.0, n=N):
    """Per-item rows for one pair. proj = base + gain (+ optional per-item jitter, cancels in diffs
    only for the early-late estimand which subtracts two arms of the SAME item)."""
    rows = []
    for i in range(n):
        b = base + (jitter * i)
        rows.append({"pid": f"{pair}_p{i}", "pair": pair, "timing": "baseline", "arm": "main", "proj": b})
        rows.append({"pid": f"{pair}_p{i}", "pair": pair, "timing": "early", "arm": "main", "proj": b + early_gain})
        rows.append({"pid": f"{pair}_p{i}", "pair": pair, "timing": "late", "arm": "main", "proj": b + late_gain})
        rows.append({"pid": f"{pair}_p{i}", "pair": pair, "timing": "mid", "arm": "main", "proj": b + 0.5 * (early_gain + late_gain)})
        # norm-matched random control arm (must be ~0 install effect)
        rows.append({"pid": f"{pair}_p{i}", "pair": pair, "timing": "early", "arm": "rand", "proj": b + rand_gain})
        rows.append({"pid": f"{pair}_p{i}", "pair": pair, "timing": "late", "arm": "rand", "proj": b + rand_gain})
        rows.append({"pid": f"{pair}_p{i}", "pair": pair, "timing": "mid", "arm": "rand", "proj": b + rand_gain})
    return rows


def test_early_vs_late_estimand():
    res = m47.analyze_rows(_rows_one_pair(early_gain=0.30, late_gain=0.05))
    evl = res["pairs"]["bomb"]["early_vs_late"]
    assert abs(evl["effect"] - 0.25) < 1e-9, evl["effect"]      # 0.30 - 0.05
    assert evl["n"] == N
    # install effect per timing vs baseline
    assert abs(res["pairs"]["bomb"]["install_effect"]["early"]["effect"] - 0.30) < 1e-9
    assert abs(res["pairs"]["bomb"]["install_effect"]["late"]["effect"] - 0.05) < 1e-9


def test_random_control_is_zero():
    res = m47.analyze_rows(_rows_one_pair(rand_gain=0.0))
    assert abs(res["pairs"]["bomb"]["random_effect"]["early"]["effect"]) < 1e-9
    # install-above-random recovers the full concept gain (0.30 - 0.0)
    assert abs(res["pairs"]["bomb"]["install_above_random"]["early"]["effect"] - 0.30) < 1e-9


def test_jitter_cancels_in_paired_estimand():
    # per-item baseline varies, but early-late subtracts two arms of the SAME item -> exact
    res = m47.analyze_rows(_rows_one_pair(early_gain=0.40, late_gain=0.10, jitter=0.7))
    evl = res["pairs"]["bomb"]["early_vs_late"]
    assert abs(evl["effect"] - 0.30) < 1e-9, evl["effect"]


def test_pooling_across_pairs_and_generalization():
    rows = (_rows_one_pair("bomb", early_gain=0.30, late_gain=0.05)
            + _rows_one_pair("grenade", early_gain=0.20, late_gain=0.02)
            + _rows_one_pair("chlorine", early_gain=0.25, late_gain=0.10))
    res = m47.analyze_rows(rows)
    # pooled early-late = mean of all 3*N per-item diffs = mean(0.25, 0.18, 0.15)
    pev = res["pooled"]["early_vs_late"]
    assert pev["n"] == 3 * N
    assert abs(pev["effect"] - (0.25 + 0.18 + 0.15) / 3.0) < 1e-5, pev["effect"]  # effect rounded to 6dp
    assert res["pooled"]["early_gt_late_all_pairs"] is True
    assert res["pooled"]["generalizes"] is True     # all pairs positive + pooled lo>0 (zero-variance CI)


def test_non_generalization_flagged():
    # one pair has late > early -> not all-pairs-positive -> generalizes False
    rows = (_rows_one_pair("bomb", early_gain=0.30, late_gain=0.05)
            + _rows_one_pair("grenade", early_gain=0.02, late_gain=0.20))  # reversed
    res = m47.analyze_rows(rows)
    assert res["pairs"]["grenade"]["early_vs_late"]["effect"] < 0
    assert res["pooled"]["early_gt_late_all_pairs"] is False
    assert res["pooled"]["generalizes"] is False


def test_pairs_paired_on_pid_not_crossed():
    # two pairs share pid SUFFIXES but distinct keys; reducer must not cross pairs
    res = m47.analyze_rows(_rows_one_pair("bomb", early_gain=0.30, late_gain=0.05)
                           + _rows_one_pair("grenade", early_gain=0.20, late_gain=0.02))
    assert res["pairs"]["bomb"]["early_vs_late"]["n"] == N
    assert res["pairs"]["grenade"]["early_vs_late"]["n"] == N


TESTS = [test_early_vs_late_estimand, test_random_control_is_zero,
         test_jitter_cancels_in_paired_estimand, test_pooling_across_pairs_and_generalization,
         test_non_generalization_flagged, test_pairs_paired_on_pid_not_crossed]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS)-fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
