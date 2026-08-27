"""`main_ne12` adds the n_examples=12 cell WITHOUT changing what any existing preset generates.

The sprint brief asks for a demonstration-count sweep over {0,1,2,4,8,12}. `12` occurs in zero rows
in zero banks, because `N_EXAMPLES` is `(0,1,2,4,8,16)`.

The tempting fix is to append 12 to `N_EXAMPLES`. It is consumed at exactly one site — the `main`
preset's core2x2 block — so that edit silently changes what `main` generates, and
`test_bank_regenerates_byte_identically.py` would go red for every canonical bank while no bank file
was ever touched. This repo has already been bitten by that exact shape (C-10: `DOMAINS` grew from 6
to 10 and the canonical carrot bank stopped regenerating from its own pools).

So `main_ne12` DERIVES from `main` and widens one field. These tests pin both halves of that: the
new cell is really there, and nothing else moved.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import prompt_families as pf  # noqa: E402


def test_the_canonical_constant_is_untouched():
    """If this fails, someone edited N_EXAMPLES and every canonical bank_rows_sha16 changed meaning."""
    assert pf.N_EXAMPLES == (0, 1, 2, 4, 8, 16)


def test_main_still_has_no_12_cell():
    for b in pf._blocks("main"):
        assert 12 not in b["n_examples"], f"block {b.get('name')} grew a 12 cell"


def test_ne12_adds_exactly_the_12_cell_to_core2x2():
    core = [b for b in pf._blocks("main_ne12") if b.get("name") == "core2x2"]
    assert len(core) == 1
    assert core[0]["n_examples"] == [0, 1, 2, 4, 8, 12, 16]


def test_ne12_differs_from_main_ONLY_in_n_examples():
    """The whole point of deriving rather than copying. Any other drift is a silent design change."""
    a, b = pf._blocks("main"), pf._blocks("main_ne12")
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert x.get("name") == y.get("name")
        for k in set(x) | set(y):
            if k == "n_examples":
                continue
            assert x.get(k) == y.get(k), f"block {x.get('name')} field {k} drifted: {x.get(k)} vs {y.get(k)}"


def test_ne12_is_derived_not_copied():
    """A copy would not track a later change to `main`. Prove it derives by mutating `main`'s source
    of truth and checking `main_ne12` follows."""
    orig = pf.N_EXAMPLES
    try:
        pf.N_EXAMPLES = (0, 4)
        core = [b for b in pf._blocks("main_ne12") if b.get("name") == "core2x2"][0]
        assert core["n_examples"] == [0, 4, 12], "main_ne12 did not follow main — it is a copy"
    finally:
        pf.N_EXAMPLES = orig


def test_ne12_is_selectable_from_the_cli():
    import argparse
    src = open(os.path.join(ROOT, "src", "boombness", "prompt_families.py")).read()
    assert '"main_ne12"' in src
    i = src.index('--preset')
    assert "main_ne12" in src[i:i + 400], "main_ne12 is not in the --preset choices list"
