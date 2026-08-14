"""GPU-free tests for the contextual-identity ("Bombness") probe dataset builder
(role-confusion sprint, plan §5.2 / Appendix A).

Covers the things that would silently corrupt every downstream probe number:
  * split discipline (codeword + concept disjointness, CARROT held out of train,
    BOMB absent) -- the exact confounds upstream's split did NOT control (A9.1);
  * the matched positive/negative pairing (same codeword, different binding);
  * single-token codewords and precomputed query-position availability.

Run:  python -m pytest doublespeak_causality/tests/test_probe_dataset.py -q
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, "..")
sys.path.insert(0, PKG)

from src.probes import probe_dataset as pd  # noqa: E402

CORPUS = os.path.join(PKG, "data", "splits", "clearharm_doublespeak_v3.json")


@pytest.fixture(scope="module")
def items():
    corpus = pd.load_corpus(CORPUS)
    return pd.build_items(corpus)


def test_all_conditions_and_counts(items):
    # 324 examples x 3 binding conditions = 972 items
    assert len(items) == 972
    lab = pd.labelled_pairs(items)
    assert len(lab) == 648  # 324 examples x {doublespeak, benign}
    pos = [it for it in lab if it.label == 1]
    neg = [it for it in lab if it.label == 0]
    assert len(pos) == len(neg) == 324


def test_matched_pairs_same_codeword_different_binding(items):
    """The core design invariant: within one example, the positive (doublespeak) and
    negative (benign) items share the SAME surface codeword. So the surface token
    carries no label information within a matched pair (token-identity control)."""
    by_ex = {}
    for it in pd.labelled_pairs(items):
        by_ex.setdefault(it.example_id, {})[it.label] = it
    assert by_ex, "no labelled pairs"
    for ex_id, pair in by_ex.items():
        assert set(pair) == {0, 1}, f"{ex_id} missing a class"
        assert pair[0].codeword == pair[1].codeword, f"{ex_id} codeword differs across binding"
        assert pair[0].condition != pair[1].condition
        # pair is keyed by label: label 1 = doublespeak (positive), 0 = benign.
        # The codeword string is identical across the pair; only the binding differs.
        assert pair[1].condition == "doublespeak" and pair[0].condition == "benign"


def test_split_discipline_enforced(items):
    # Must not raise: disjoint codewords/concepts, CARROT out of train, BOMB absent.
    stats = pd.assert_split_discipline(items)
    assert set(stats) == {"train", "dev", "test"}
    assert stats["train"]["n_codewords"] == 104
    assert stats["dev"]["n_codewords"] == 60
    assert stats["test"]["n_codewords"] == 60


def test_carrot_in_dev_not_train_bomb_absent(items):
    st = pd.split_stats(items)
    assert "carrot" in st["dev"]["_codewords"]
    assert "carrot" not in st["train"]["_codewords"]
    assert "carrot" not in st["test"]["_codewords"]
    allcw = st["train"]["_codewords"] | st["dev"]["_codewords"] | st["test"]["_codewords"]
    assert "bomb" not in allcw


def test_split_discipline_catches_leak(items):
    """The guard must actually fire on a planted leak, not just pass vacuously."""
    train_like = [it for it in items if it.split == "train"][:1]
    dev_like = [it for it in items if it.split == "dev"]
    # force a dev item to share a train codeword
    victim = dev_like[0]
    leaked = pd.ProbeItem(**{**victim.__dict__, "codeword": train_like[0].codeword})
    poisoned = [it for it in items if it is not victim] + [leaked]
    with pytest.raises(AssertionError, match="leak"):
        pd.assert_split_discipline(poisoned)


def test_single_token_and_query_position(items):
    for it in items:
        assert it.single_token, f"{it.example_id} not single-token"
        assert it.codeword_token_id is not None
        # every binding condition contains the codeword at least once, so a query
        # (last-occurrence) span is always available for position-anchored probing.
        assert it.n_codeword_occurrences >= 1
        assert it.query_span() is not None
        s, e = it.query_span()
        assert 0 <= s < e


def test_direct_condition_excluded_by_default(items):
    # `direct` has no codeword; it must not appear among codeword-position items.
    assert all(it.condition != "direct" for it in items)
