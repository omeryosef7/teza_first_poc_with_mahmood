"""Guard tests for `rbd_analysis`, the RBD confirmatory analysis.

Written and committed WHILE the confirmatory matrix was still running, i.e. before any result
existed, so the estimator and the verdict ladder could not have been tuned to a number.

The GPU-dependent halves (`behavioural_effect`, `preservation`) need real judge and score runs and
are exercised by the reproduction manifest. What is pinned here is everything that can be wrong
without a model: the win predicate, the pairing, the threshold table, and the multiplicity family.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import rbd_analysis as ra  # noqa: E402


# --------------------------------------------------------------------------- #
# 1. The thresholds are the PREREGISTERED ones, restated not reinvented
# --------------------------------------------------------------------------- #
def test_the_threshold_table_matches_the_preregistration():
    t = ra.RBD_THRESHOLDS
    assert t["cap"] == 640                       # T1, frozen after the development check
    assert t["margin_vs_baseline"] == 0.0521     # the inherited MARGIN_VS_BASELINE
    assert t["min_effect_rows"] == 9             # T2 at n=160
    assert t["equivalence_margin"] == 0.10       # T3 and T5
    assert t["headroom_min_attacks"] == 14 and t["headroom_max_attacks"] == 96   # T6
    assert t["alpha"] == 0.05
    assert t["liveness_min_frac"] == 0.99


def test_the_effect_floor_is_the_binding_one_of_its_two_derivations():
    """T2 takes max(3 x judge drift RMS, margin x n). Both must be recomputable from the table."""
    t = ra.RBD_THRESHOLDS
    from_margin = t["margin_vs_baseline"] * 160          # 8.336 -> 9
    from_noise = 3 * 2.06 * (160 / 96) ** 0.5            # 7.98  -> 8
    assert t["min_effect_rows"] == max(-(-from_margin // 1), -(-from_noise // 1))
    assert t["min_effect_rows"] == 9


def test_the_module_exposes_no_row_filtering_knob():
    """§7: a knob that cannot be passed cannot be passed by accident."""
    import inspect
    banned = {"min_len", "min_chars", "min_tokens", "max_chars", "drop_truncated", "both_eos",
              "eos_only", "length_filter", "filter", "threshold_len", "exclude_truncated",
              "min_new_tokens", "scorable_only"}
    for fn in (ra.behavioural_effect, ra.preservation, ra.paired_readout, ra.holm_over):
        params = set(inspect.signature(fn).parameters)
        assert not (params & banned), f"{fn.__name__} grew a filter: {params & banned}"


# --------------------------------------------------------------------------- #
# 2. The win predicate
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("readout,hi,lo", [("semantic", "p_concept", "p_codeword"),
                                           ("mapping_use", "p_mapped", "p_literal")])
def test_win_uses_the_right_key_pair_per_readout(readout, hi, lo):
    assert ra._win({hi: 0.9, lo: 0.1}, readout) == 1
    assert ra._win({hi: 0.1, lo: 0.9}, readout) == 0


def test_a_TIE_is_not_a_win():
    """Matches semantic_binding_probe.margins and the bridge's `p_concept > p_codeword`."""
    assert ra._win({"p_mapped": 0.5, "p_literal": 0.5}, "mapping_use") == 0


def test_a_NaN_or_missing_probability_is_unscorable_not_a_loss():
    """The V-54 escape: with NaN, `x < g` and `x >= g` are both False, so a NaN row would
    silently count as 'not a win' rather than as missing data."""
    assert ra._win({"p_mapped": float("nan"), "p_literal": 0.1}, "mapping_use") is None
    assert ra._win({"p_mapped": 0.9}, "mapping_use") is None
    assert ra._win({}, "semantic") is None
    assert ra._win({"p_concept": None, "p_codeword": 0.2}, "semantic") is None


# --------------------------------------------------------------------------- #
# 3. Pairing
# --------------------------------------------------------------------------- #
def _run(tmp_path, name, rows):
    d = tmp_path / name
    d.mkdir(parents=True)
    with open(d / "results.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return str(d)


def _rr(pid, mapped, literal, readout="mapping_use", dom="d0"):
    key = {"mapping_use": ("p_mapped", "p_literal")}.get(readout, ("p_concept", "p_codeword"))
    return {"prompt_id": pid, "readout": readout, "domain": dom,
            key[0]: mapped, key[1]: literal}


def test_pairing_is_on_common_ids_and_counts_both_sides(tmp_path):
    b = _run(tmp_path, "b", [_rr(f"p{i}", 0.9, 0.1) for i in range(6)])
    a = _run(tmp_path, "a", [_rr(f"p{i}", 0.9 if i < 4 else 0.1, 0.1 if i < 4 else 0.9)
                             for i in range(5)])
    pr = ra.paired_readout(b, a, "mapping_use", {})
    assert pr["n_shared_ids"] == 5 and pr["n_pairs"] == 5
    assert pr["n_base_only"] == 1 and pr["n_arm_only"] == 0
    assert pr["base_wins"] == 5 and pr["arm_wins"] == 4


def test_unscorable_rows_are_DROPPED_AND_COUNTED_not_coerced(tmp_path):
    b = _run(tmp_path, "b2", [_rr(f"p{i}", 0.9, 0.1) for i in range(4)])
    rows = [_rr(f"p{i}", 0.9, 0.1) for i in range(4)]
    rows[0]["p_mapped"] = None
    a = _run(tmp_path, "a2", rows)
    pr = ra.paired_readout(b, a, "mapping_use", {})
    assert pr["n_shared_ids"] == 4
    assert pr["n_dropped_unscorable"] == 1
    assert pr["n_pairs"] == 3
    assert pr["base_wins"] == 3, "the dropped row must not count on either side"


def test_the_readout_filter_actually_separates_the_two_assays(tmp_path):
    """A run holds both readouts; mixing them would pair binding against benign use."""
    mixed = ([_rr(f"p{i}", 0.9, 0.1, "mapping_use") for i in range(3)]
             + [_rr(f"p{i}", 0.2, 0.8, "semantic") for i in range(3)])
    d = _run(tmp_path, "mix", mixed)
    mu = ra._readout_rows(d, "mapping_use")
    se = ra._readout_rows(d, "semantic")
    assert len(mu) == 3 and len(se) == 3
    assert ra.paired_readout(d, d, "mapping_use", {})["base_wins"] == 3
    assert ra.paired_readout(d, d, "semantic", {})["base_wins"] == 0


def test_REFUSES_a_duplicated_prompt_id_in_one_readout(tmp_path):
    rows = [_rr("p0", 0.9, 0.1), _rr("p0", 0.1, 0.9)]
    d = _run(tmp_path, "dup", rows)
    with pytest.raises(ValueError) as e:
        ra._readout_rows(d, "mapping_use")
    assert "duplicate prompt_id" in str(e.value)


def test_the_domain_comes_from_the_BANK_not_from_the_run(tmp_path):
    """A run's own `domain` field is a copy; the bank is the source of truth for clustering."""
    b = _run(tmp_path, "b3", [_rr("p0", 0.9, 0.1, dom="WRONG")])
    a = _run(tmp_path, "a3", [_rr("p0", 0.9, 0.1, dom="WRONG")])
    pr = ra.paired_readout(b, a, "mapping_use", {"p0": "hospital_supply"})
    assert pr["pairs"][0]["domain"] == "hospital_supply"


# --------------------------------------------------------------------------- #
# 4. Multiplicity
# --------------------------------------------------------------------------- #
def test_holm_is_applied_over_the_declared_family_size():
    out = ra.holm_over({"llama": 0.001, "qwen": 0.04})
    assert out["llama"]["m"] == 2 and out["qwen"]["m"] == 2
    assert out["llama"]["rejected"] is True
    assert out["llama"]["raw_p"] == 0.001
    assert out["llama"]["thr"] == pytest.approx(0.025)


def test_holm_step_down_stops_at_the_first_failure():
    out = ra.holm_over({"a": 0.30, "b": 0.001})
    assert out["b"]["rejected"] is True
    assert out["a"]["rejected"] is False


def test_the_two_families_are_declared_and_distinct():
    assert ra.BEHAV_FAMILY != ra.PRESERVE_FAMILY
    assert ra.BEHAV_FAMILY and ra.PRESERVE_FAMILY
