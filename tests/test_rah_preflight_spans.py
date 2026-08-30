"""RAH-C-005: the token-span resolver must use OVERLAP, not containment.

A BPE tokenizer emits the leading space as part of the word token, so a word at [870,876) is
carried by a token spanning [869,876). A containment test finds nothing. This file pins the rule
and proves the guard can still fail.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import rah_preflight_transport as pf  # noqa: E402


def test_leading_space_token_is_resolved():
    """The real failing case: ' poison' spans [869,876) for a word at [870,876)."""
    offsets = [(860, 869), (869, 876), (876, 877)]
    assert pf.token_index_covering(offsets, 870, 876) == 1


def test_MUTANT_containment_semantics_would_have_failed():
    """Executed proof that the OLD rule was broken on the same input."""
    offsets = [(860, 869), (869, 876), (876, 877)]
    old_hits = [k for k, (a, b) in enumerate(offsets) if a >= 870 and b <= 876 and b > a]
    assert old_hits == [], "the old containment rule should find nothing here"


def test_multi_subtoken_word_returns_the_LAST_piece():
    offsets = [(860, 869), (869, 872), (872, 876), (876, 877)]
    assert pf.token_index_covering(offsets, 870, 876) == 2


def test_no_overlap_still_raises():
    with pytest.raises(ValueError):
        pf.token_index_covering([(0, 5), (5, 10)], 20, 26)


def test_zero_width_tokens_are_ignored():
    offsets = [(869, 869), (869, 876)]
    assert pf.token_index_covering(offsets, 870, 876) == 1


class _Tok:
    def __init__(self, m): self.m = m
    def decode(self, ids): return self.m[ids[0]]


def test_assert_token_is_part_of_accepts_a_real_piece():
    assert pf.assert_token_is_part_of(_Tok({7: " poison"}), [7], 0, "poison", "x") == "poison"


def test_MUTANT_assert_token_is_part_of_REJECTS_a_wrong_token():
    with pytest.raises(SystemExit):
        pf.assert_token_is_part_of(_Tok({7: " lantern"}), [7], 0, "poison", "x")
