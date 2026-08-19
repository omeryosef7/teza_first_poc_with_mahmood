"""R-18 power block: slot 3 must give demonstrations DISJOINT from slot 0.

The existing `families` block uses slots 1 and 2, which OVERLAP slot 0 at n_examples 4 and 8 —
that is why its 72 rows are pseudo-replicated and had to be dropped from G2's clean estimate.
`_take` returns pool[(slot*3 + i) % 20], so slot k is disjoint from slot 0 exactly when
3k >= n and 3k + n <= 20. These tests pin that arithmetic and the block that relies on it.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
import prompt_families as pf  # noqa: E402

POOL = 20


def idx(slot, n, pool=POOL):
    return {(slot * 3 + i) % pool for i in range(n)}


def test_take_matches_the_index_formula_this_reasoning_depends_on():
    """If `_take` ever stops being `pool[(slot*3+i) % len]`, every disjointness claim below is void."""
    pool = list(range(POOL))
    for slot in (0, 1, 2, 3, 5):
        for n in (1, 2, 4, 8):
            assert set(pf._take(pool, n, slot)) == idx(slot, n), (slot, n)


def test_slot3_is_disjoint_from_slot0_at_every_n_the_power_block_uses():
    for n in (1, 2, 4, 8):
        assert not (idx(0, n) & idx(3, n)), f"slot3 overlaps slot0 at n={n}"


def test_slots_1_and_2_OVERLAP_slot0_which_is_why_they_are_excluded():
    """The negative case. If this ever passes cleanly, the `families` block was fine and R-18's
    pseudo-replication finding would need revisiting."""
    assert idx(0, 4) & idx(1, 4), "slot1 should overlap slot0 at n=4"
    assert idx(0, 8) & idx(2, 8), "slot2 should overlap slot0 at n=8"


def test_slot3_is_NOT_disjoint_at_n16_which_is_why_the_block_omits_it():
    assert idx(0, 16) & idx(3, 16), "n=16 cannot be disjoint on a 20-sentence pool"


def test_the_power_block_exists_and_uses_only_the_safe_levels():
    specs = pf.bank_specs(sorted(pf.DOMAINS), preset="main") if hasattr(pf, "bank_specs") else None
    src = open(os.path.join(ROOT, "src", "boombness", "prompt_families.py")).read()
    assert "core2x2_slot3" in src
    i = src.index("core2x2_slot3")
    block = src[i:i + 400]
    assert "slots=[3]" in block
    assert "n_examples=[1, 2, 4, 8]" in block
    assert "16" not in block.split("n_examples=[1, 2, 4, 8]")[1][:40]
