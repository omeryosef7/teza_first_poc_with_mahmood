"""GPU-free tests for the Phase-5 per-example patch-spec builder (plan §9).

The B9-critical logic: the vector artifact rows are ordered by example_ids, and a
patch MUST be looked up by example id, never by a corpus enumeration index. These
tests assert the row alignment, sign convention, band filtering, and the missing-id
guard.

Run:  python -m pytest doublespeak_causality/tests/test_phase5_patch_spec.py -q
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from src.probes import phase5_patch_spec as ps  # noqa: E402


def _artifact():
    # 3 examples, 2 layers, distinctive per-example/per-layer/per-arm vectors so a
    # wrong row or layer is detectable by value.
    ids = ["ex_A", "ex_B", "ex_C"]
    layers = [8, 9]
    d = 4
    arms = {}
    for a_i, arm in enumerate(ps.VALID_ARMS):
        arms[arm] = {}
        for L in layers:
            M = np.zeros((3, d), dtype=np.float32)
            for r in range(3):
                # encode (arm, layer, row) into the vector for exact checks
                M[r, 0] = a_i
                M[r, 1] = L
                M[r, 2] = r
            arms[arm][L] = M
    return {"example_ids": ids, "layers": layers, "arms": arms}


def test_row_lookup_by_id_not_position():
    art = _artifact()
    assert ps.example_row_index(art, "ex_A") == 0
    assert ps.example_row_index(art, "ex_C") == 2
    # spec for ex_B / arm 'bomb' must carry row-index 1 in slot 2 of each vector
    spec = ps.arm_patch_spec(art, "bomb", "ex_B", sign=-1)
    for e in spec:
        assert e["vector"][2] == 1        # row 1 == ex_B
        assert e["mode"] == "add" and e["alpha"] == -1.0


def test_missing_id_raises():
    art = _artifact()
    with pytest.raises(KeyError):
        ps.example_row_index(art, "ex_ZZZ")
    with pytest.raises(KeyError):
        ps.arm_patch_spec(art, "bomb", "ex_ZZZ")


def test_sign_and_arm_and_layer_encoding():
    art = _artifact()
    # sufficiency add (+1) on the 'remainder' arm at layer 9 only
    spec = ps.arm_patch_spec(art, "remainder", "ex_A", band=[9], sign=+1)
    assert len(spec) == 1
    e = spec[0]
    assert e["layer"] == 9
    assert e["alpha"] == +1.0
    assert e["vector"][0] == ps.VALID_ARMS.index("remainder")  # arm encoded
    assert e["vector"][1] == 9                                  # layer encoded
    assert e["vector"][2] == 0                                  # row 0 == ex_A


def test_band_filters_to_available_layers():
    art = _artifact()
    spec = ps.arm_patch_spec(art, "full", "ex_A", band=[8, 9, 99], sign=-1)
    assert sorted(e["layer"] for e in spec) == [8, 9]   # 99 absent → dropped


def test_invalid_arm_and_sign():
    art = _artifact()
    with pytest.raises(ValueError):
        ps.arm_patch_spec(art, "not_an_arm", "ex_A")
    with pytest.raises(ValueError):
        ps.arm_patch_spec(art, "full", "ex_A", sign=2)


def test_spec_norm_positive():
    art = _artifact()
    spec = ps.arm_patch_spec(art, "bomb", "ex_C")
    assert ps.spec_norm(spec) > 0
