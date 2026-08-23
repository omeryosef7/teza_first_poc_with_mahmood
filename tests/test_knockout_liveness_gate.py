"""The knockout liveness gate, the demo-span resolver, and the realized-dose values — all of which
had ZERO test coverage until an adversarial review pointed it out (2026-08-23, finding M4).

WHY THIS FILE IS EMBARRASSING AND NECESSARY. The liveness gate is the single guard protecting the
whole Phase 2 experiment from the prefill-only failure: a knockout that silently switches off during
decoding still emits rows, still reports n_edges_cut, still exits 0, and produces "the knockout does
not change ASR" — a statement about a hook rather than a model. Three independent reviewers mutated
the gate (`if _fl < 0.0`), the span resolver (`pos = [i+1 ...]`), and the dose formula
(`frac * alpha`), and **all 44 tests stayed green in every case**. A guard with no test is the FM1
dead-guard shape, and this one was guarding against the FM1 dead-guard shape.

The gate was also inline in `main()`, which is *why* it was untestable. It is now
`knockout_liveness_summary` + `assert_knockout_live`, and this file tests them.

Run:  python -m pytest tests/test_knockout_liveness_gate.py -q
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))


def _live(n_rows, n_live, edits=None, forwards=None, demo=None):
    return {
        "n_rows": n_rows,
        "n_rows_decode_live": n_live,
        "decode_edits": edits if edits is not None else [42] * n_rows,
        "decode_forwards": forwards if forwards is not None else [10] * n_rows,
        "n_demo_positions": demo if demo is not None else [14] * n_rows,
    }


# --------------------------------------------------------------------------- #
# the gate
# --------------------------------------------------------------------------- #
def test_gate_passes_when_every_row_fired():
    import score_behavior as sb
    s = sb.knockout_liveness_summary(_live(96, 96), "eager")
    assert s["frac_rows_decode_live"] == 1.0
    assert sb.assert_knockout_live(s) is True


def test_gate_REFUSES_when_the_knockout_never_fired_at_decode():
    """THE CASE THE WHOLE PHASE DEPENDS ON: the prefill-only failure."""
    import score_behavior as sb
    s = sb.knockout_liveness_summary(_live(96, 0, edits=[0] * 96), "eager")
    assert s["frac_rows_decode_live"] == 0.0
    with pytest.raises(SystemExit, match="prefill-only"):
        sb.assert_knockout_live(s)


def test_gate_REFUSES_at_two_percent_dead_rows():
    """The threshold is 0.99, so 2 dead rows in 96 must fail. Mutating it to 0.0 turns this red."""
    import score_behavior as sb
    s = sb.knockout_liveness_summary(_live(96, 94), "eager")
    assert s["frac_rows_decode_live"] < sb.KNOCKOUT_MIN_LIVE_FRAC
    with pytest.raises(SystemExit):
        sb.assert_knockout_live(s)


def test_gate_REFUSES_a_run_with_no_rows_rather_than_passing_vacuously():
    """n_rows == 0 is how a vacuous guard passes. It must be a failure."""
    import score_behavior as sb
    s = sb.knockout_liveness_summary(_live(0, 0, edits=[], forwards=[], demo=[]), "eager")
    with pytest.raises(SystemExit, match="zero rows"):
        sb.assert_knockout_live(s)


def test_gate_threshold_is_actually_consulted():
    """Directly pins the constant: a gate whose threshold is unread is not a gate."""
    import score_behavior as sb
    assert 0.9 < sb.KNOCKOUT_MIN_LIVE_FRAC <= 1.0
    just_under = _live(1000, int(sb.KNOCKOUT_MIN_LIVE_FRAC * 1000) - 1)
    with pytest.raises(SystemExit):
        sb.assert_knockout_live(sb.knockout_liveness_summary(just_under, "eager"))


def test_summary_reports_the_attention_implementation():
    """A knockout under sdpa is void; the summary must say which kernel ran."""
    import score_behavior as sb
    assert sb.knockout_liveness_summary(_live(4, 4), "eager")["attn_implementation"] == "eager"
    assert sb.knockout_liveness_summary(_live(4, 4), "sdpa")["attn_implementation"] == "sdpa"


# --------------------------------------------------------------------------- #
# the demo-span resolver
# --------------------------------------------------------------------------- #
class _FakeTok:
    """Whitespace tokenizer with real offset mappings — enough to pin the span arithmetic."""

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        offs, i = [], 0
        for w in text.split(" "):
            if w:
                offs.append((i, i + len(w)))
            i += len(w) + 1
        out = {"input_ids": list(range(len(offs)))}
        if return_offsets_mapping:
            out["offset_mapping"] = offs
        return out


def test_demo_key_positions_finds_the_block_and_only_the_block():
    import score_behavior as sb
    templated = "SYS HEAD aa bb cc dd QUERY tail"
    row = {"demo_block": "aa bb cc dd", "final_query_text": "QUERY tail"}
    pos, why = sb.demo_key_positions(_FakeTok(), row, templated)
    assert why is None
    assert pos == [2, 3, 4, 5], pos          # exactly the four demo words
    # mutating the resolver to pos=[i+1...] shifts this and the test goes red


def test_demo_key_positions_reports_a_reason_rather_than_guessing():
    import score_behavior as sb
    tok = _FakeTok()
    assert sb.demo_key_positions(tok, {"demo_block": ""}, "a b c")[1] == "no_demo_block"
    assert sb.demo_key_positions(tok, {"demo_block": "zz"}, "a b c")[1] == \
        "demo_block_not_found_in_templated"


def test_query_span_is_excluded_from_the_control_pool():
    """M1: the control must never block the request the model is asked to answer."""
    import score_behavior as sb
    templated = "SYS HEAD aa bb cc dd QUERY tail"
    row = {"demo_block": "aa bb cc dd", "final_query_text": "QUERY tail"}
    tok = _FakeTok()
    dk, _ = sb.demo_key_positions(tok, row, templated)
    prot = sb.query_span_positions(tok, row, templated, dk)
    assert prot, "the query span must be found"
    assert prot.isdisjoint(set(dk)), "protected span must not overlap the demo block"
    assert 6 in prot and 7 in prot, prot          # QUERY and tail


def test_control_REFUSES_rather_than_eating_the_request():
    """The measured failure: |demo| grows to 106 while the non-demo pool stays ~53."""
    import score_behavior as sb
    dk = list(range(10, 40))                      # 30 demo keys
    protected = set(range(40, 60))                # the request
    with pytest.raises(sb.InfeasibleControl):
        sb.knockout_key_set("nondemo_random", dk, 62, 1, protected=protected)


def test_control_is_disjoint_from_both_the_demo_block_and_the_request():
    import score_behavior as sb
    dk = list(range(10, 16))
    protected = set(range(40, 60))
    got = sb.knockout_key_set("nondemo_random", dk, 62, 20260823, protected=protected)
    assert len(got) == len(dk)
    assert not (set(got) & set(dk))
    assert not (set(got) & protected), "the control blocked part of the request"


def test_infeasible_control_is_a_normal_exception_not_SystemExit():
    """SystemExit is a BaseException: it escaped `except Exception` and killed the run mid-file,
    leaving a partial, judgeable gens.jsonl with no DONE.json."""
    import score_behavior as sb
    assert issubclass(sb.InfeasibleControl, Exception)
    assert not issubclass(sb.InfeasibleControl, SystemExit)


# --------------------------------------------------------------------------- #
# realized dose, read from the CODE PATH rather than restated
# --------------------------------------------------------------------------- #
def test_realized_dose_is_read_from_the_code_path_not_restated_here():
    """tests/test_realized_dose.py re-types the formulas, so mutating the source left it green.

    This CALLS score_behavior.realized_dose_record, so a drift in the source turns it red. An
    earlier draft of this test regex-parsed the source instead and broke on the comma inside
    max(frac, 0.0) -- parsing code to test code is its own bug class, so the function was extracted.
    """
    import score_behavior as sb
    frac = 0.820443
    r = sb.realized_dose_record(frac, 0.08)
    assert math.isclose(r["realized_variance_frac_removed"], 0.126020, rel_tol=1e-4)
    assert math.isclose(r["realized_norm_frac_removed"], 0.072463, rel_tol=1e-4)
    r30 = sb.realized_dose_record(frac, 0.30)
    assert math.isclose(r30["realized_variance_frac_removed"], 0.418426, rel_tol=1e-4)
    assert math.isclose(r30["realized_norm_frac_removed"], 0.271735, rel_tol=1e-4)
    # at alpha=1 the two metrics coincide up to the square root -- the accident that hid C-2
    r1 = sb.realized_dose_record(frac, 1.0)
    assert math.isclose(r1["realized_variance_frac_removed"], frac, rel_tol=1e-12)
    assert math.isclose(r1["realized_norm_frac_removed"], math.sqrt(frac), rel_tol=1e-12)


def test_the_dose_metrics_disagree_below_alpha_one():
    """If this stops holding, C-2's warning no longer applies and the ladder is uninformative."""
    import score_behavior as sb
    frac = 0.820443
    ratios = [sb.realized_dose_record(frac, a)["realized_variance_frac_removed"] /
              sb.realized_dose_record(frac, a)["realized_norm_frac_removed"]
              for a in (0.05, 0.1, 0.3, 0.6, 1.0)]
    assert ratios == sorted(ratios, reverse=True), ratios
    assert ratios[0] > 1.5 * ratios[-1]
