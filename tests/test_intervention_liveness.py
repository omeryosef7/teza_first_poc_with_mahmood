"""`fired: true` is not `mattered: true` — and this must catch the case that proves it.

C-20: a rescue arm reported `fired: true` and `n_positions_written: 28` for a patch that wrote the
value already present, and three published claims cited it as a specificity control. Liveness told
the truth; the truth was narrower than the question. This module compares GENERATIONS, and these
tests pin that it separates the two failure modes a liveness block cannot:

    hook fires, changes computation, no behavioural effect  -> real DISSOCIATION
    hook fires, changes NOTHING,     no behavioural effect  -> NO-OP ARM
"""

from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import intervention_liveness as il  # noqa: E402


def _mk(tmp_path, name, texts):
    d = tmp_path / name
    d.mkdir(parents=True)
    with open(d / "gens.jsonl", "w") as fh:
        for i, t in enumerate(texts):
            fh.write(json.dumps({"prompt_id": f"p{i}", "generation": t}) + "\n")
    return str(d)


def test_an_arm_that_changes_every_generation_passes(tmp_path):
    c = _mk(tmp_path, "ctrl", ["a"] * 10)
    a = _mk(tmp_path, "arm", [f"b{i}" for i in range(10)])
    r = il.generation_divergence(a, c, "live")
    assert r["n_differing"] == 10 and r["frac_differing"] == 1.0
    assert r["is_noop_arm"] is False
    il.assert_changed_generations(r)


def test_a_NOOP_ARM_is_caught(tmp_path):
    """The C-20 shape: identical generations. A liveness block would still say fired: true."""
    c = _mk(tmp_path, "ctrl", ["same"] * 10)
    a = _mk(tmp_path, "arm", ["same"] * 10)
    r = il.generation_divergence(a, c, "c20_shape")
    assert r["n_differing"] == 0 and r["frac_differing"] == 0.0
    assert r["is_noop_arm"] is True
    assert r["diagnosis"]["verdict"] == "NOOP_ARM"
    with pytest.raises(il.NoOpArmError, match="NOOP_ARM"):
        il.assert_changed_generations(r)


def test_a_SMALL_but_real_arm_is_WARNED_not_refused(tmp_path):
    """The predicate correction. A first draft refused anything under 0.10, but that threshold was
    calibrated on broad-span masks only. A single-position patch or a rarely-triggered intervention
    can legitimately touch 1 row in 20, and refusing it would look authoritative while being wrong."""
    c = _mk(tmp_path, "ctrl", ["same"] * 20)
    a = _mk(tmp_path, "arm", ["diff"] + ["same"] * 19)
    r = il.generation_divergence(a, c, "barely")
    assert r["n_differing"] == 1
    assert r["diagnosis"]["verdict"] == "SMALL_BUT_REAL"
    assert r["diagnosis"]["refuse"] is False
    il.assert_changed_generations(r)          # must NOT raise


def test_the_refusal_predicate_is_EXACT_zero():
    """Exact zero needs no calibration: under greedy decoding only a bit-identical computation
    lands there. Any positive threshold would have to be tuned, and tuning is what went wrong."""
    assert il.ZERO_DIVERGENCE == 0.0
    assert il.diagnose(0.0)["refuse"] is True
    assert il.diagnose(1e-9)["refuse"] is False        # anything above zero is not a refusal
    assert il.diagnose(0.05)["refuse"] is False


def test_fired_flag_separates_a_dead_hook_from_a_C20_noop():
    """Divergence alone under-determines the diagnosis; only the middle case is the bug."""
    assert il.diagnose(0.0, fired=False)["verdict"] == "HOOK_NEVER_RAN"
    assert il.diagnose(0.0, fired=True)["verdict"] == "NOOP_ARM"
    assert "wrote the value already present" in il.diagnose(0.0, fired=True)["reading"]
    assert il.diagnose(0.03, fired=True)["verdict"] == "SMALL_BUT_REAL"
    # both zero cases still refuse -- the distinction is the DIAGNOSIS, not the gate
    assert il.diagnose(0.0, fired=False)["refuse"] is True
    assert il.diagnose(0.0, fired=True)["refuse"] is True


def test_disjoint_populations_are_refused_not_scored_as_zero(tmp_path):
    """No shared prompt_ids means nothing was compared — that must not read as 'no change'."""
    c = _mk(tmp_path, "ctrl", ["a"] * 3)
    a = tmp_path / "arm2"
    a.mkdir()
    with open(a / "gens.jsonl", "w") as fh:
        for i in range(3):
            fh.write(json.dumps({"prompt_id": f"z{i}", "generation": "a"}) + "\n")
    r = il.generation_divergence(str(a), c, "disjoint")
    assert r["n_common"] == 0
    with pytest.raises(il.NoOpArmError, match="NO_COMPARISON"):
        il.assert_changed_generations(r)


def test_only_common_prompt_ids_are_compared(tmp_path):
    c = _mk(tmp_path, "ctrl", ["a"] * 5)
    a = _mk(tmp_path, "arm", ["b"] * 3)
    r = il.generation_divergence(a, c, "partial")
    assert r["n_common"] == 3 and r["n_arm_rows"] == 3 and r["n_control_rows"] == 5


def test_no_generation_text_is_emitted(tmp_path):
    c = _mk(tmp_path, "ctrl", ["SECRETCONTROLTEXT"] * 4)
    a = _mk(tmp_path, "arm", ["SECRETARMTEXT"] * 4)
    blob = str(il.generation_divergence(a, c, "x"))
    assert "SECRET" not in blob


def test_whitespace_difference_counts_as_a_change(tmp_path):
    """Hashing is exact by design: a hook that changes only spacing DID change the computation."""
    c = _mk(tmp_path, "ctrl", ["a b"] * 4)
    a = _mk(tmp_path, "arm", ["a  b"] * 4)
    assert il.generation_divergence(a, c, "ws")["frac_differing"] == 1.0
