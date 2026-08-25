"""The committed prompt banks must regenerate BYTE-IDENTICALLY from their own pools files.

WHY THIS TEST EXISTS (C-10, 2026-08-25). `prompt_families._blocks()` read the module-level
`demo_pools.DOMAINS` constant while `build_demo_block()` indexes the pools dict it is handed.
Growing that constant from 6 domains to 10 for Phase 4B therefore made the generator ask a
6-domain pools file for a 10-domain domain list, and the CANONICAL bank behind every result in
the sprint stopped regenerating at all:

    KeyError: 'warehouse_logistics|benign'

Nothing in the suite noticed, because every other test builds a synthetic bank. The failure was
found only because an unrelated strictness test happened to shell out to the generator. What
should have caught it is this: a bank generator whose output depends on a module constant rather
than on its input is not reproducible, and Section 19's reproduction manifest is exactly the
claim that these commands still work.

Asserting the SHA rather than "it exits 0" is the point. A generator that runs and emits a
subtly different bank is the failure mode that would silently invalidate every joined artifact,
since runs join to the bank by `prompt_id`.
"""

from __future__ import annotations

import hashlib
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
DATA = REPO / "data" / "boombness_prompts"

CASES = [
    ("demo_pools.json", "boombness_prompt_bank.jsonl", 336),
    ("demo_pools_d10.json", "boombness_prompt_bank_d10.jsonl", 560),
]


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("pools_name,bank_name,n_families", CASES)
def test_bank_regenerates_byte_identically(tmp_path, pools_name, bank_name, n_families):
    pools, bank = DATA / pools_name, DATA / bank_name
    if not pools.exists() or not bank.exists():
        pytest.skip(f"{pools_name} or {bank_name} not present")
    out = tmp_path / bank_name
    r = subprocess.run(
        [sys.executable, str(REPO / "src" / "boombness" / "prompt_families.py"),
         "--pools", str(pools), "--preset", "main", "--codeword", "carrot", "--concept", "bomb",
         "--seed", "20260825", "--strict", "--out", str(out)],
        cwd=REPO, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, f"generator failed for {pools_name}:\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}"
    assert f"families checked={n_families} violations=0" in r.stdout, r.stdout[-2000:]
    assert _sha(out) == _sha(bank), (
        f"{bank_name} did NOT regenerate byte-identically from {pools_name}. Every run joins to "
        f"this bank by prompt_id, so a changed bank silently invalidates joined artifacts.")


def test_the_two_banks_are_actually_different():
    """Guards the guard: if both cases pointed at one bank the test above would pass vacuously."""
    a, b = DATA / "boombness_prompt_bank.jsonl", DATA / "boombness_prompt_bank_d10.jsonl"
    if not (a.exists() and b.exists()):
        pytest.skip("banks not present")
    assert _sha(a) != _sha(b)
