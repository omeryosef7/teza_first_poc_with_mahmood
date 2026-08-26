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
    # Anchor on the block DEFINITION, not on any mention of the name. The `main_longctx` preset
    # (R-45) refers to "core2x2_slot3" by name when overriding its filler, and it appears earlier
    # in the file, so `src.index("core2x2_slot3")` used to land on that reference and inspect the
    # wrong 400 characters. A guard that cannot tell a definition from a mention breaks the moment
    # anyone names the block anywhere else.
    assert 'dict(name="core2x2_slot3"' in src, "the core2x2_slot3 block definition is gone"
    i = src.index('dict(name="core2x2_slot3"')
    block = src[i:i + 400]
    assert "slots=[3]" in block
    assert "n_examples=[1, 2, 4, 8]" in block
    assert "16" not in block.split("n_examples=[1, 2, 4, 8]")[1][:40]


# --------------------------------------------------------------------------- #
# PHASE D (plan §6). The whole preset rests on one arithmetic claim: the ten slots in
# `PHASE_D_SLOTS_N2` give PAIRWISE DISJOINT demonstration sets at n_examples=2, which is what
# turns "120 behavioral rows per level" into "120 INDEPENDENT FAMILIES per level". G2 was
# retracted for exactly the difference between those two sentences, so it is pinned here rather
# than left to a comment.
# --------------------------------------------------------------------------- #
def test_phase_d_slots_are_pairwise_disjoint_at_n2():
    slots = pf.PHASE_D_SLOTS_N2
    assert len(slots) == 10, "120 rows/level = 6 domains x 2 splits x 10 slots; ten is load-bearing"
    assert len(set(slots)) == 10, "a repeated slot is the same family counted twice"
    sets = {s: idx(s, 2) for s in slots}
    for a in slots:
        for b in slots:
            if a < b:
                assert not (sets[a] & sets[b]), \
                    f"slots {a} and {b} share demonstrations {sets[a] & sets[b]} at n=2"


def test_phase_d_slots_exhaust_the_pool_which_is_why_ten_is_the_ceiling():
    """The ten sets cover all 20 sentences exactly once -- so an 11th disjoint slot cannot exist."""
    covered = set()
    for s in pf.PHASE_D_SLOTS_N2:
        covered |= idx(s, 2)
    assert covered == set(range(POOL))


def test_phase_d_slots_are_NOT_disjoint_at_n4_which_is_why_n_examples_is_fixed_at_2():
    """Pins the reason the demonstration-COUNT factor is not swept: at n=4 only 5 slots fit."""
    overlaps = [(a, b) for a in pf.PHASE_D_SLOTS_N2 for b in pf.PHASE_D_SLOTS_N2
                if a < b and (idx(a, 4) & idx(b, 4))]
    assert overlaps, "if these became disjoint at n=4 the preset should be widened"


def test_phase_d_preset_uses_only_those_slots_and_only_n2():
    blocks = pf._blocks("phase_d")
    assert blocks, "phase_d preset is missing"
    for b in blocks:
        assert b["n_examples"] == [2], f"{b['name']} sweeps n_examples; that breaks independence"
        assert list(b["slots"]) == list(pf.PHASE_D_SLOTS_N2), f"{b['name']} uses other slots"
        assert b["query_kinds"] == ["behavioral"], f"{b['name']} mixes query kinds"
        assert b.get("filler_near") is True, \
            f"{b['name']} would leave the `near` arm ~390 chars shorter than far/distributed"


def test_phase_d_baseline_level_is_emitted_exactly_once():
    """Three duplicate baselines would be dropped by the prompt_id dedup and would make the
    per-condition drop counts asymmetric, tripping the violation check for a spurious reason."""
    base = [b for b in pf._blocks("phase_d")
            if "none" in b["strengths"] and "consistent" in b["consistencies"]
            and "near" in b["positions"] and "plain" in b["role_styles"]]
    assert len(base) == 1, f"the (none, consistent, near, plain) cell is in {len(base)} blocks"
    assert base[0]["name"] == "phase_d_base"
    assert list(base[0]["conditions"]) == list(pf.CORE_2X2), \
        "the baseline block must carry the full 2x2 or NOTHING in phase_d is alignment-checked"


def test_filler_near_defaults_off_so_every_committed_bank_is_unchanged():
    """`bank_rows_sha16` of the main bank is joined on by every extraction artifact in the repo."""
    import inspect
    sig = inspect.signature(pf.build_prompt)
    assert sig.parameters["filler_near"].default is False
    for b in pf._blocks("main") + pf._blocks("pilot") + pf._blocks("smoke"):
        assert not b.get("filler_near"), f"{b['name']} would rewrite committed prompts"
