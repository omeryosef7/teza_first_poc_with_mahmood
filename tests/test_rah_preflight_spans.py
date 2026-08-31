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


def test_pr002_fewshot_forms_name_no_candidate_and_are_two_hop():
    """`RAH2-PR-002`: the few-shot forms must constrain the slot WITHOUT printing a candidate.

    Text-level, so it needs no tokenizer. The geometry half (patch at the probe, read 2 tokens
    later at ` ->`) is asserted through `patch_at`/`read_at` rather than by tokenizing.
    """
    labels = ["poison", "lantern", "missile", "candle"]
    forms = pf.fewshot_receiver_forms(*labels, "widget")
    by = {f["name"]: f for f in forms}
    assert set(by) == {"id07_tmpl", "fc_probe_last", "fewshot_cat", "fewshot_syn"}
    for name in ("fewshot_cat", "fewshot_syn"):
        f = by[name]
        assert pf.names_any_candidate(f["body"], labels) == [], name
        assert (f["patch_at"], f["read_at"], f["templated"]) == ("probe", "final", False), name
        assert f["body"].endswith('"widget" ->'), name
        assert f["body"].count("\n") == 3, name        # three demonstrated pairs, then the probe
    # the reference extremes are carried through UNCHANGED from the frozen grid
    grid = {f["name"]: f for f in pf.receiver_forms(*labels, "widget")}
    for name in ("id07_tmpl", "fc_probe_last"):
        assert by[name] == grid[name], name


def test_pr002_exemplars_are_disjoint_from_the_candidate_vocabularies():
    """No exemplar may BE a candidate. (First-token collision needs a tokenizer and is checked in
    the run itself by `exemplar_candidate_collisions`; this is the text-level floor.)"""
    for labels in (["poison", "lantern", "missile", "candle"],
                   ["bomb", "carrot", "knife", "ticket"]):
        assert not (set(pf.EXEMPLAR_WORDS) & set(labels))
