"""Regression test: `prompt_families.py --strict` must leave NOTHING at the target path.

THE FAILURE THIS PINS DOWN. The generator used to write the bank and its `_meta.json` to their
FINAL paths and only afterwards run the alignment report, so a --strict failure still left a
violating bank plus a meta file describing it as legitimate on disk. Every downstream step that
keys off file existence rather than exit status then consumed a bank the generator had rejected --
the mechanism behind the discarded `arrow` banks. Validation must therefore happen BEFORE the bank
becomes available as an output.

This uses the REAL code path, not a monkeypatched one: the `smoke` preset with a concept word that
occurs incidentally in the demo pools produces genuine `check_alignment` violations, because the
concept->codeword substitution rewrites those incidental occurrences and the exact-word-swap
invariant then fails. No prompt text is involved -- the fixture is command-line scalars only.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(REPO, "src", "boombness", "prompt_families.py")

# `smoke` is the cheapest preset; "was" occurs incidentally in the pools, so the 2x2 exact-swap
# invariant is genuinely violated for several families.
VIOLATING_ARGS = ["--preset", "smoke", "--concept", "was"]
CLEAN_ARGS = ["--preset", "smoke"]


def _run(out_path, extra):
    return subprocess.run([sys.executable, GEN, "--out", out_path] + extra,
                          capture_output=True, text=True, cwd=REPO)


def _paths(tmp_path):
    out = str(tmp_path / "bank.jsonl")
    return out, out.replace(".jsonl", "_meta.json")


def test_violating_input_really_violates(tmp_path):
    """Guard the fixture itself: without --strict this input reports >0 violations."""
    out, meta = _paths(tmp_path)
    r = _run(out, CLEAN_ARGS + ["--concept", "was"])
    assert r.returncode == 0, r.stderr
    assert json.load(open(meta))["stats"]["n_alignment_violations"] > 0


def test_strict_violation_writes_nothing(tmp_path):
    out, meta = _paths(tmp_path)
    r = _run(out, VIOLATING_ARGS + ["--strict"])
    assert r.returncode == 1, f"expected exit 1, got {r.returncode}\n{r.stdout}\n{r.stderr}"
    assert not os.path.exists(out), "a rejected bank was left at the target path"
    assert not os.path.exists(meta), "a meta file describing a rejected bank was left on disk"
    leftovers = glob.glob(out + ".tmp.*") + glob.glob(meta + ".tmp.*")
    assert leftovers == [], f"temporary files left behind: {leftovers}"
    assert "REFUSING" in r.stderr


def test_strict_violation_does_not_clobber_an_existing_bank(tmp_path):
    """A failed --strict run must not truncate whatever was already at the target path."""
    out, meta = _paths(tmp_path)
    assert _run(out, CLEAN_ARGS).returncode == 0
    before = (open(out).read(), open(meta).read())
    assert _run(out, VIOLATING_ARGS + ["--strict"]).returncode == 1
    assert (open(out).read(), open(meta).read()) == before


def test_clean_strict_run_writes_both_files(tmp_path):
    out, meta = _paths(tmp_path)
    r = _run(out, CLEAN_ARGS + ["--strict"])
    assert r.returncode == 0, r.stderr
    assert os.path.exists(out) and os.path.exists(meta)
    assert glob.glob(out + ".tmp.*") == [] and glob.glob(meta + ".tmp.*") == []
    assert json.load(open(meta))["stats"]["n_alignment_violations"] == 0


def test_non_strict_violation_still_writes_both_files(tmp_path):
    """Backward compatibility: existing recipes without --strict are unchanged."""
    out, meta = _paths(tmp_path)
    r = _run(out, VIOLATING_ARGS)
    assert r.returncode == 0, r.stderr
    assert os.path.exists(out) and os.path.exists(meta)
    assert glob.glob(out + ".tmp.*") == [] and glob.glob(meta + ".tmp.*") == []
    with open(out) as f:
        assert sum(1 for _ in f) > 0
