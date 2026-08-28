"""`main_fcslots` adds multi-slot forced choice WITHOUT changing what any existing preset generates.

WHY THE PRESET EXISTS. §12.9 decomposed the power gap and found the binding lever was not domains
but ROWS PER DOMAIN: `n_eff = k·m / (1 + (m−1)·ICC)` reaches `k/ICC` only as m → ∞, and forced
choice existed at exactly ONE slot, so the single-slot arm sat at n_eff 100 against a ceiling of 130.
The extra rows need no new prose — the 20-sentence pools already admit them.

WHY IT IS DERIVED. Adding forced choice to `core2x2_slot3`'s `query_kinds` would have been the
one-line edit, and it would silently change what `main` generates — the C-10 shape this repo has
been bitten by twice, and the reason `main_ne12` derives rather than mutates. These tests pin both
halves: the new rows are really there, and nothing else moved.

SLOT 0 IS EXCLUDED, AND A GUARD FOUND THAT. The first version emitted slot 0 in every dose block,
which `core2x2` already provides, duplicating 304 prompt_ids (38 domains × 2 splits × 4 doses). The
dedup dropped them from `natural_doublespeak` ONLY, leaving the four 2×2 cells covering different
family sets, and `--strict` refused the bank and wrote nothing. `test_fcslots_excludes_slot_zero`
is that bug, pinned.
"""

from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import prompt_families as pf  # noqa: E402

DOMS = ["d%d" % i for i in range(6)]


def _fc_blocks(preset):
    return [b for b in pf._blocks(preset, DOMS) if b["name"].startswith("fcslots_")]


def test_main_has_no_fcslots_blocks():
    """The derivation must leave `main` alone; every canonical bank regenerates from it."""
    assert _fc_blocks("main") == []


def test_fcslots_leaves_every_main_block_byte_identical():
    """Derived, not copied-and-edited: the shared blocks must be the same objects' content."""
    base = pf._blocks("main", DOMS)
    derived = [b for b in pf._blocks("main_fcslots", DOMS) if not b["name"].startswith("fcslots_")]
    assert derived == base, "main_fcslots altered a block it inherits from main"


def test_fcslots_adds_one_block_per_dose():
    names = sorted(b["name"] for b in _fc_blocks("main_fcslots"))
    assert names == ["fcslots_n1", "fcslots_n2", "fcslots_n4", "fcslots_n8"], (
        "one block per dose is required: the disjoint slot set depends on n, so a single block "
        "with one `slots` list would reuse n=8's two slots at every dose")


def test_fcslots_excludes_slot_zero():
    """The bug `--strict` caught: core2x2 already emits forced choice at slot 0 for every dose."""
    for b in _fc_blocks("main_fcslots"):
        assert 0 not in b["slots"], (
            f"{b['name']} includes slot 0, which core2x2 already provides — this duplicated 304 "
            "prompt_ids and unbalanced the 2x2 across conditions")


def test_fcslots_slot_counts_match_the_disjoint_sets():
    """20 at n=1, 7 at n=2, 4 at n=4, 2 at n=8 — minus slot 0, which core2x2 supplies."""
    expected = {"fcslots_n1": 19, "fcslots_n2": 6, "fcslots_n4": 3, "fcslots_n8": 1}
    got = {b["name"]: len(b["slots"]) for b in _fc_blocks("main_fcslots")}
    assert got == expected, f"slot counts {got} do not match the disjoint sets {expected}"


def test_the_slots_really_are_pairwise_disjoint_at_their_dose():
    """Verified against `_take` itself, not against the arithmetic that chose them."""
    pool = [f"S{i}" for i in range(20)]
    for b in _fc_blocks("main_fcslots"):
        n = b["n_examples"][0]
        sets = {s: set(pf._take(pool, n, s)) for s in [0] + list(b["slots"])}  # 0 = core2x2's
        for a in sets:
            for c in sets:
                if a < c:
                    assert not (sets[a] & sets[c]), (
                        f"{b['name']}: slots {a} and {c} share demonstrations at n={n}")


def test_fcslots_blocks_are_forced_choice_and_attack_arm_only():
    """natural_doublespeak only: the estimand is a within-attack-arm ICC and forms no 2x2 contrast.

    Emitting all four conditions would quadruple the bank for rows no analysis reads.
    """
    for b in _fc_blocks("main_fcslots"):
        assert b["query_kinds"] == ["semantic_forced_choice"]
        assert b["conditions"] == ["natural_doublespeak"]


def test_total_rows_per_domain_is_the_pool_maximum():
    """33 slot-doses per split — 1 from core2x2 plus the block's own, at each dose."""
    per_split = sum(1 + len(b["slots"]) for b in _fc_blocks("main_fcslots"))
    assert per_split == 33, f"{per_split} slot-doses per split; the 20-sentence pools admit 33"
    assert per_split * len(pf.SPLITS) == 66, "66 rows per domain is the measured design"


def test_fcslots_is_selectable_from_the_cli():
    out = subprocess.run([sys.executable,
                          os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                       "src", "boombness", "prompt_families.py"), "--help"],
                         capture_output=True, text=True).stdout
    assert "main_fcslots" in out, "the preset is unreachable from the command line"
