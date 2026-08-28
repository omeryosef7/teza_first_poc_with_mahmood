"""The at-risk count must refuse a window measured on a different population.

WHY. This sprint produced FOUR corrections with one shape -- a scale quoted away from the
population it was measured on:

    C-33      a threshold carried across n as a rate
    5.18.1    the >=0.667 screen applied at n=18, where critical_k is 14
    5.20      a Qwen3-measured perturbation window applied to Llama banks (2.7x too large)
    5.20.1    then ONE Llama window (main, 0.4616) applied to ticket_bomb (0.3202, 1.4x)

The last two are what `margin_exposure` guards. Documentation did not stop instances 3 and 4 --
instance 4 happened one tick AFTER writing down "the scale must be named", and in the same
analysis that corrected instance 3. So the guard is a hard refusal.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import margin_exposure as me  # noqa: E402


def _run(tmp, name, model, bank, rows, *, bank_sha=None, launch_model=None, commit="c0"):
    """`launch_model` is what --model was given as (None = omitted); `model` is what RESOLVED."""
    d = tmp / name
    d.mkdir()
    (d / "config.json").write_text(json.dumps({"args": {"model": launch_model,
                                                        "bank": f"/x/{bank}"}}))
    (d / "metadata.json").write_text(json.dumps({
        "model": model, "model_revision_resolved_commit": commit,
        "bank_rows_sha16": bank_sha if bank_sha is not None else "sha_" + bank}))
    with open(d / "results.jsonl", "w") as fh:
        for i, margin in enumerate(rows):
            fh.write(json.dumps({"prompt_id": f"p{i}", "query_kind": "semantic_forced_choice",
                                 "logp_concept": margin, "logp_codeword": 0.0}) + "\n")
    return str(d)


@pytest.fixture
def pair(tmp_path):
    """Two runs, same population, differing slightly -- a measurable window."""
    a = _run(tmp_path, "a", "llama", "main.jsonl", [5.0, 3.0, 0.20, -2.0, -4.0])
    b = _run(tmp_path, "b", "llama", "main.jsonl", [5.1, 3.1, -0.10, -2.1, -4.1])
    return a, b


def test_window_carries_its_provenance(pair):
    w = me.measure_window(*pair)
    assert w["provenance"] == {"model": "llama", "model_commit": "c0",
                               "bank_rows_sha16": "sha_main.jsonl"}
    assert w["scale_max"] == pytest.approx(0.30, abs=1e-9)
    assert w["n_verdict_flips"] == 1          # the 0.20 row crosses zero


def test_at_risk_REFUSES_a_window_from_another_MODEL(pair, tmp_path):
    """5.20's error: a Qwen3 window applied to a Llama bank."""
    w = me.measure_window(*pair)
    other = _run(tmp_path, "qwen", "qwen3", "main.jsonl", [5.0, 1.0, 0.5])
    with pytest.raises(me.BorrowedScaleError, match="BORROWED SCALE"):
        me.exposure(other, w, "batch16-vs-batch1")


def test_at_risk_REFUSES_a_window_from_another_BANK(pair, tmp_path):
    """5.20.1's error: main's window applied to the ticket_bomb bank. SAME model."""
    w = me.measure_window(*pair)
    other = _run(tmp_path, "tb", "llama", "ticket_bomb.jsonl", [5.0, 1.0, 0.5])
    with pytest.raises(me.BorrowedScaleError, match="BORROWED SCALE"):
        me.exposure(other, w, "batch16-vs-batch1")


def test_a_window_cannot_be_MEASURED_across_two_populations(tmp_path):
    a = _run(tmp_path, "a2", "llama", "main.jsonl", [5.0, 1.0])
    b = _run(tmp_path, "b2", "llama", "ticket_bomb.jsonl", [5.1, 1.1])
    with pytest.raises(me.BorrowedScaleError, match="different populations"):
        me.measure_window(a, b)


def test_scale_name_is_REQUIRED(pair):
    """A bare at-risk count invites the carry-over: at-risk of WHAT."""
    w = me.measure_window(*pair)
    for bad in ("", "   "):
        with pytest.raises(me.BorrowedScaleError, match="at-risk of WHAT"):
            me.exposure(pair[0], w, bad)


def test_matching_provenance_is_accepted_and_reports_both_numbers(pair):
    w = me.measure_window(*pair)
    e = me.exposure(pair[0], w, "batch16-vs-batch1")
    assert e["n"] == 5 and e["wins"] == 3
    assert e["median_abs_margin"] == pytest.approx(3.0)
    assert e["at_risk"] == 1                      # only |0.20| < 0.30
    assert e["at_risk_that_are_wins"] == 1
    assert e["at_risk_that_are_losses"] == 0


def test_bound_flips_only_rows_that_can_HURT_the_claim(pair, tmp_path):
    """At-risk rows already lying the wrong way can only help; counting them is self-adversarial."""
    w = me.measure_window(*pair)
    # baseline: one at-risk WIN (0.20). arm: one at-risk LOSS (-0.10).
    b = me.adversarial_bound(pair[0], pair[1], w, "batch16-vs-batch1", "preserved")
    # attacking 'preserved' pushes baseline UP via its at-risk LOSSES (it has none) and the arm
    # DOWN via its at-risk WINS (it has none) -> nothing moves.
    assert b["observed"] == {"baseline": 3, "arm": 2, "delta": -1}
    assert b["adversarial"]["baseline"] == 3
    assert b["adversarial"]["arm"] == 2

    c = me.adversarial_bound(pair[0], pair[1], w, "batch16-vs-batch1", "collapse")
    # attacking 'collapse' pushes baseline DOWN via its at-risk WINS (the 0.20 row) and the arm
    # UP via its at-risk LOSSES (the -0.10 row)
    assert c["adversarial"]["baseline"] == 2
    assert c["adversarial"]["arm"] == 3


def test_bound_rejects_an_unknown_claim(pair):
    w = me.measure_window(*pair)
    with pytest.raises(ValueError, match="preserved.*collapse"):
        me.adversarial_bound(pair[0], pair[1], w, "s", "unchanged")


def test_margin_is_the_difference_not_either_logp(tmp_path):
    """The decision statistic is the margin; both logps are free to sit at any scale."""
    d = _run(tmp_path, "m", "llama", "main.jsonl", [])
    with open(os.path.join(d, "results.jsonl"), "w") as fh:
        fh.write(json.dumps({"prompt_id": "z", "query_kind": "semantic_forced_choice",
                             "logp_concept": -0.006, "logp_codeword": -5.256}) + "\n")
    assert me.margins(d)["z"] == pytest.approx(5.250)


def test_rows_of_other_query_kinds_are_ignored(tmp_path):
    d = _run(tmp_path, "q", "llama", "main.jsonl", [1.0])
    with open(os.path.join(d, "results.jsonl"), "a") as fh:
        fh.write(json.dumps({"prompt_id": "other", "query_kind": "comprehension_usage",
                             "logp_concept": 9.0, "logp_codeword": 0.0}) + "\n")
    assert list(me.margins(d)) == ["p0"]


def test_launch_style_does_NOT_change_provenance(tmp_path):
    """The bug a peer found: --model omitted vs passed made an identical model refuse itself.

    This is the failure that mattered most, because the pair it refused is the pair that
    MEASURED the window which caught the borrowed-scale error in the first place. A guard that
    refuses the work that detects its own target bug suppresses corrections.
    """
    a = _run(tmp_path, "la", "meta-llama/Llama-3.1-8B-Instruct", "tb.jsonl",
             [5.0, 1.0], launch_model=None)                                  # --model omitted
    b = _run(tmp_path, "lb", "meta-llama/Llama-3.1-8B-Instruct", "tb.jsonl",
             [5.1, 1.1], launch_model="meta-llama/Llama-3.1-8B-Instruct")    # --model passed
    w = me.measure_window(a, b)                     # must NOT raise
    assert w["provenance"]["model"] == "meta-llama/Llama-3.1-8B-Instruct"
    assert me.exposure(a, w, "batch16-vs-batch1")["at_risk"] >= 0


def test_same_basename_different_CONTENT_is_refused(tmp_path):
    """The quiet failure of the old basename check: a false ACCEPT rather than a false refusal."""
    a = _run(tmp_path, "ca", "llama", "bank.jsonl", [5.0, 1.0], bank_sha="AAAA")
    b = _run(tmp_path, "cb", "llama", "bank.jsonl", [5.0, 1.0], bank_sha="BBBB")
    with pytest.raises(me.BorrowedScaleError, match="different populations"):
        me.measure_window(a, b)


def test_different_WEIGHTS_commit_is_refused(tmp_path):
    """Same model name, different resolved weights, is a different population."""
    a = _run(tmp_path, "wa", "llama", "bank.jsonl", [5.0, 1.0], commit="aaa")
    b = _run(tmp_path, "wb", "llama", "bank.jsonl", [5.0, 1.0], commit="bbb")
    with pytest.raises(me.BorrowedScaleError, match="different populations"):
        me.measure_window(a, b)


def test_missing_hash_falls_back_but_LABELS_itself(tmp_path):
    """A path-based identity must never be mistaken for a content-addressed one."""
    d = tmp_path / "nohash"; d.mkdir()
    (d / "config.json").write_text(json.dumps({"args": {"model": "m", "bank": "/x/b.jsonl"}}))
    (d / "results.jsonl").write_text("")
    assert me._provenance(str(d))["bank_rows_sha16"] == "basename:b.jsonl"
