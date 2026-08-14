"""GPU-free test for the Gate-1 orchestration (plan §5.4). Synthetic multi-split
activations with a planted signal at one layer -> Gate 1 PASSES; controls at chance;
a no-signal dataset -> Gate 1 FAILS."""
import json, os, sys
import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from src.probes import gate1_eval as g1  # noqa: E402


def _synth_run(n_per_split=40, L=4, P=2, H=24, signal=2.0, seed=0, carrot_in_dev=True):
    rng = np.random.default_rng(seed)
    acts, items = [], []
    ex = 0
    for split, n in (("train", n_per_split), ("dev", n_per_split // 2), ("test", n_per_split // 2)):
        for k in range(n):
            gid = f"{split}{ex}"; ex += 1
            base = rng.standard_normal((L, P, H))
            xp = base + 0.5 * rng.standard_normal((L, P, H)); xp[1, 0, 0] += signal  # signal L1,codeword_last
            xn = base + 0.5 * rng.standard_normal((L, P, H)); xn[1, 0, 0] -= signal
            cw = "carrot" if (split == "dev" and carrot_in_dev and k < 6) else f"cw{split}{k}"
            for blk, lab, cond in ((xp, 1, "doublespeak"), (xn, 0, "benign")):
                acts.append(blk)
                items.append({"example_id": gid, "label": lab, "condition": cond,
                              "split": split, "codeword": cw, "codeword_token_id": 100 + (k % 7),
                              "codeword_last_idx": 30 + (k % 5), "seq_len": 60 + (k % 5),
                              "normalized_concept": f"c{split}{k}"})
    return np.stack(acts).astype(np.float32), items


def test_gate1_passes_on_signal():
    acts, items = _synth_run(seed=1)
    res = g1.evaluate(items, acts, position="codeword_last", n_boot=300)
    assert res["selected_layer"] == 1
    assert res["holdout_auc"] > 0.8
    assert res["verdict"] == "PASS"
    # controls must be well below the probe
    assert res["max_control_auc"] < res["holdout_auc"] - 0.10
    # carrot transfer evaluated and healthy
    assert res["transfer"] is not None and res["transfer"]["carrot_auc"] > 0.6


def test_gate1_fails_on_no_signal():
    acts, items = _synth_run(seed=2, signal=0.0)
    res = g1.evaluate(items, acts, position="codeword_last", n_boot=300)
    assert res["verdict"] == "FAIL"
    assert res["holdout_auc"] < 0.70


def test_position_length_controls_present():
    acts, items = _synth_run(seed=3)
    res = g1.evaluate(items, acts, n_boot=200)
    for k in ("label_shuffle", "random_direction", "position_only", "length_only", "token_identity"):
        assert k in res["controls"]
