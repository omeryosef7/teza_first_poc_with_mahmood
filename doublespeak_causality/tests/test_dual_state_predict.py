"""GPU-free test for Phase-3 dual-state prediction (plan §7.3). Synthetic rows where
Refusalness predicts the outcome and Bombness does not -> the nested comparison must
recover B(refusalness) >> A(bombness) and 'both over refusalness' ~ 0."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from src.probes import dual_state_predict as dsp  # noqa: E402


def _rows(n=180, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        split = "train" if i % 5 < 3 else ("dev" if i % 5 == 3 else "test")
        refusal = rng.normal()               # the true driver
        p = 1 / (1 + np.exp(3 * refusal))    # high refusal -> low success
        y = int(rng.random() < p)
        bomb = rng.normal()                  # uninformative
        rows.append({"example_id": f"e{i}", "split": split, "y": y,
                     "ds_score": float(y), "bombness": bomb, "refusalness": refusal})
    return rows


def test_refusalness_beats_bombness():
    res = dsp.run(_rows(), n_boot=500)
    m = res["models"]
    assert m["B_refusalness"]["auc"] > 0.75
    assert m["A_bombness"]["auc"] < 0.70
    assert res["nested_delta_auc"]["refusalness_over_bombness"] > 0.1
    # adding bombness to refusalness should not help much
    assert res["nested_delta_auc"]["both_over_refusalness"] < 0.1


def test_quantile_and_ci_shapes():
    res = dsp.run(_rows(seed=1), n_boot=300)
    assert len(res["quantile_success"]["by_refusalness"]) == 5
    ci = res["univariate_holdout_auc_ci95"]
    assert ci is not None and len(ci["refusalness_minus_bombness"]) == 2
