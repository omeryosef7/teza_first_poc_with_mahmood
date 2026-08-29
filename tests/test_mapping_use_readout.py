"""Guard tests for the Readout-B scoring path in `score_behavior`. RBD sprint, 2026-08-29.

Readout B (`mapping_use_forced_choice`) is scored by exactly the same machinery as the other two
forward-only readouts -- `signals.string_option_readout` over a two-option variant set -- so what
needs testing is not the scorer but the WIRING: that the kind is a member of the forward-only
family, that the liveness contract covers it, that the answer set comes from the bank rather than
from a table that can drift from it, and that a bank which disagrees with itself is refused.

The scoring itself needs a model, so it is exercised by the GPU smoke gate, not here.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import score_behavior as sb  # noqa: E402

BANK = os.path.join(ROOT, "data", "boombness_prompts",
                    "boombness_prompt_bank_rbd_lantern_poison.jsonl")
QK = "mapping_use_forced_choice"


@pytest.fixture(scope="module")
def bank_rows():
    if not os.path.exists(BANK):
        pytest.skip(f"bank absent: {BANK}")
    with open(BANK) as f:
        return [json.loads(line) for line in f if line.strip()]


def _rows(*option_sets, kind=QK):
    return [{"query_kind": kind, "mapping_use_options": o} for o in option_sets]


# --------------------------------------------------------------------------- #
# 1. Membership and liveness wiring
# --------------------------------------------------------------------------- #
def test_the_kind_is_in_the_forward_only_family():
    """Membership is what makes liveness enforced rather than skipped.

    `READOUT_QUERY_KINDS` drives `_readout_only`, the mixed-kinds refusal, and the pre-flight
    `readout_liveness_contract` call. A forward-only kind left out of it would run with the
    DECODE contract, which it can never satisfy.
    """
    assert QK in sb.READOUT_QUERY_KINDS
    assert sb.MAPPING_USE_KIND == QK


@pytest.mark.parametrize("scope", ["demo_processing_only", "legacy_all_query",
                                   "query_prefill_only"])
def test_the_liveness_contract_covers_the_new_kind_on_the_admitted_scopes(scope):
    contract = sb.readout_liveness_contract(scope, (QK,))
    assert contract is not None


@pytest.mark.parametrize("scope", ["response_query_only", "decode_only"])
def test_the_contract_still_REFUSES_the_scopes_it_always_refused(scope):
    """Readout B must not widen what the forward-only path accepts.

    `response_query_only` stripped of its decode half edits exactly the rows
    `query_prefill_only` edits, so the run would be filed under a misdescribing name; `decode_only`
    resolves to no prefill rows at all. Both are refused BEFORE the model loads.
    """
    with pytest.raises(SystemExit):
        sb.readout_liveness_contract(scope, (QK,))


# --------------------------------------------------------------------------- #
# 2. The answer set comes from the bank
# --------------------------------------------------------------------------- #
def test_the_options_are_read_from_the_real_shipped_bank(bank_rows):
    opts = sb.resolve_mapping_use_options(bank_rows)
    assert opts == {"literal": "shed", "mapped": "cabinet"}
    mu = [r for r in bank_rows if r["query_kind"] == QK]
    assert len(mu) == 320, "too few rows for this to mean anything"
    assert all(r.get("mapping_use_options") == opts for r in mu)


def test_rows_that_are_not_readout_B_do_not_carry_the_key(bank_rows):
    """A conditional field: no existing bank grows a key, and no other kind is scorable as B."""
    other = [r for r in bank_rows if r["query_kind"] != QK]
    assert len(other) == 640
    assert not any("mapping_use_options" in r for r in other)


def test_a_bank_with_no_readout_B_rows_returns_None():
    assert sb.resolve_mapping_use_options([{"query_kind": "behavioral"}]) is None
    assert sb.resolve_mapping_use_options([]) is None


# --------------------------------------------------------------------------- #
# 3. Refusals -- a bank that disagrees with itself is not scored
# --------------------------------------------------------------------------- #
def test_REFUSES_two_distinct_option_sets():
    """The answer set is built once and applied to every row; picking one silently is the bug."""
    with pytest.raises(ValueError) as e:
        sb.resolve_mapping_use_options(_rows({"literal": "shed", "mapped": "cabinet"},
                                             {"literal": "cupboard", "mapped": "bunker"}))
    assert "distinct option sets" in str(e.value)


@pytest.mark.parametrize("bad", [
    {"literal": "shed"},
    {"mapped": "cabinet"},
    {"literal": "shed", "mapped": ""},
    {"literal": "   ", "mapped": "cabinet"},
    {},
])
def test_REFUSES_a_missing_or_empty_option(bad):
    with pytest.raises(ValueError) as e:
        sb.resolve_mapping_use_options(_rows(bad))
    assert "missing or empty" in str(e.value)


def test_REFUSES_an_unknown_option_key():
    with pytest.raises(ValueError) as e:
        sb.resolve_mapping_use_options(_rows({"literal": "shed", "mapped": "cabinet",
                                              "typo": "x"}))
    assert "unknown key" in str(e.value)


def test_REFUSES_a_forced_choice_between_a_word_and_itself():
    with pytest.raises(ValueError) as e:
        sb.resolve_mapping_use_options(_rows({"literal": "shed", "mapped": "shed"}))
    assert "same word" in str(e.value)


def test_a_row_missing_the_key_entirely_is_REFUSED_not_defaulted():
    """`.get(...) or {}` must not read as 'no options needed' for a kind that needs them."""
    with pytest.raises(ValueError):
        sb.resolve_mapping_use_options([{"query_kind": QK}])


# --------------------------------------------------------------------------- #
# 4. The single-pair-per-bank assumption, which was never checked before
# --------------------------------------------------------------------------- #
def test_the_shipped_bank_carries_exactly_one_lexical_pair(bank_rows):
    pairs = {(r["codeword"], r["concept"]) for r in bank_rows}
    assert pairs == {("lantern", "poison")}


def test_the_two_shipped_banks_carry_DIFFERENT_pairs(bank_rows):
    other = os.path.join(ROOT, "data", "boombness_prompts",
                         "boombness_prompt_bank_rbd_candle_missile.jsonl")
    if not os.path.exists(other):
        pytest.skip("second bank absent")
    with open(other) as f:
        rows2 = [json.loads(line) for line in f if line.strip()]
    p1 = {(r["codeword"], r["concept"]) for r in bank_rows}
    p2 = {(r["codeword"], r["concept"]) for r in rows2}
    assert p1 == {("lantern", "poison")} and p2 == {("candle", "missile")}
    assert not (p1 & p2), "H2 needs the two pairs to be disjoint on both axes"
    assert sb.resolve_mapping_use_options(rows2) == {"literal": "cupboard", "mapped": "bunker"}
