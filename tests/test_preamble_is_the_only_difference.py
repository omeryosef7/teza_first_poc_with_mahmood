"""The preamble banks must differ from d10 by the preamble and NOTHING else.

WHY (R-52, verified 2026-08-26). R-52 concluded that adding neutral context *causes* the attack to
weaken -- baseline ASR 0.1562 (d10) -> 0.0625 (preamble 12) -> 0.0437 (preamble 10). That causal
attribution is only sound if the banks are otherwise identical. It was asserted before it was
checked; this checks it, and pins it so a future regeneration cannot quietly invalidate the claim.

Measured at the time of writing, on the 200 behavioural natural_doublespeak core rows:
`full_prompt(longpre10) == preamble + "\\n\\n" + full_prompt(d10)` on 200/200, with `demo_block`,
`final_query_text`, `demo_valence`, `n_examples`, `domain` and `family_slot` identical on 200/200.

Skips if a bank is absent, so it guards a working tree rather than a checkout.
"""

from __future__ import annotations

import json
import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "boombness_prompts")
CORE_BLOCKS = ("core2x2", "core2x2_slot3")


def _load(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        pytest.skip(f"{name} not present")
    with open(p) as fh:
        return {r["prompt_id"]: r for r in map(json.loads, fh)}


def _core_behavioural(a, b):
    return [p for p in sorted(set(a) & set(b))
            if a[p].get("query_kind") == "behavioral"
            and a[p].get("condition") == "natural_doublespeak"
            and a[p].get("bank_block") in CORE_BLOCKS]


@pytest.mark.parametrize("bank", ["boombness_prompt_bank_longpre.jsonl",
                                  "boombness_prompt_bank_longpre10.jsonl"])
def test_full_prompt_is_exactly_preamble_plus_the_d10_prompt(bank):
    """The one relationship the causal attribution depends on."""
    a, b = _load("boombness_prompt_bank_d10.jsonl"), _load(bank)
    ids = _core_behavioural(a, b)
    assert ids, "no shared behavioural core rows to compare"
    bad = [p for p in ids
           if b[p]["full_prompt"] != (b[p].get("preamble") or "") + "\n\n" + a[p]["full_prompt"]]
    assert not bad, (
        f"{bank}: {len(bad)} of {len(ids)} rows are not d10's prompt with a preamble prepended — "
        f"R-52 attributes the ASR drop to the preamble alone, and that requires this to hold")


@pytest.mark.parametrize("bank", ["boombness_prompt_bank_longpre.jsonl",
                                  "boombness_prompt_bank_longpre10.jsonl"])
@pytest.mark.parametrize("field", ["demo_block", "final_query_text", "demo_valence",
                                   "n_examples", "domain", "family_slot"])
def test_every_other_design_field_is_untouched(bank, field):
    a, b = _load("boombness_prompt_bank_d10.jsonl"), _load(bank)
    ids = _core_behavioural(a, b)
    bad = [p for p in ids if a[p].get(field) != b[p].get(field)]
    assert not bad, f"{bank}: {field} differs on {len(bad)}/{len(ids)} rows — not a clean contrast"


def test_the_two_preamble_banks_differ_only_in_length():
    """longpre12 vs longpre10 is the comparison R-51/R-52 read as 'preamble length'."""
    b12, b10 = (_load("boombness_prompt_bank_longpre.jsonl"),
                _load("boombness_prompt_bank_longpre10.jsonl"))
    ids = _core_behavioural(b12, b10)
    assert all(b12[p].get("demo_block") == b10[p].get("demo_block") for p in ids)
    lens = {(len((b12[p].get("preamble") or "").split("\n")),
             len((b10[p].get("preamble") or "").split("\n"))) for p in ids}
    assert lens == {(12, 10)}, f"expected every row to be 12 vs 10 preamble lines, got {lens}"
