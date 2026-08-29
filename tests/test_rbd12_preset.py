"""Guard tests for the RBD confirmatory preset and Readout B (`mapping_use_forced_choice`).

RBD sprint, 2026-08-29. Readout B is the safe deterministic mapping-use assay: demonstrations
install CODEWORD = CONCEPT, and the query asks a benign storage-location question whose correct
answer differs between the codeword's own referent and the installed concept. Neither answer is
harmful, so the outcome cannot co-vary with harm -- which is the confound that retracted the prior
phase's mapping-usage result (BC-R-27).

What is pinned here, and why each matters:

1.  the preset emits ALL THREE readouts on EVERY family stem -- this is the fix for BC-C-24, where
    only `core2x2` carried forced choice and 396 of 468 behavioural stems had no probe side;
2.  `slots` is exactly the DISJOINT set at this dose, re-derived from `floor(20/n)` rather than
    retyped -- a third slot at n=8 would emit rows sharing demonstrations, the failure G2 was
    retracted for;
3.  a pair with no Readout-B option entry is REFUSED, not silently rendered with empty options;
4.  every option word is single-token-with-leading-space on BOTH primary models, asserted against
    the committed screen artifact rather than against a comment;
5.  `main` does not gain the new query kind.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import prompt_families as pf  # noqa: E402

POOLS = os.path.join(ROOT, "data", "boombness_prompts",
                     "demo_pools_lantern_poison_rbd12.json")
SCREEN = os.path.join(ROOT, "outputs", "boombness", "rbd_readout_b_option_screen.json")

QK = "mapping_use_forced_choice"


@pytest.fixture(scope="module")
def bank():
    if not os.path.exists(POOLS):
        pytest.skip(f"pools file absent: {POOLS}")
    pools = json.load(open(POOLS))["pools"]
    rows, meta = pf.generate_bank(pools, "lantern", "poison", preset="rbd12", seed=20260829)
    return rows, meta


# --------------------------------------------------------------------------- #
# 1. Preset shape
# --------------------------------------------------------------------------- #
def test_rbd12_is_a_single_block_with_the_three_readouts():
    blocks = pf._blocks("rbd12", ["a", "b"])
    assert len(blocks) == 1
    b = blocks[0]
    assert b["query_kinds"] == ["behavioral", "semantic_forced_choice", QK]
    assert b["n_examples"] == [8]
    assert sorted(b["conditions"]) == sorted(pf.CORE_2X2)
    assert list(b["splits"]) == list(pf.SPLITS)


def test_slots_are_exactly_the_disjoint_set_at_this_dose():
    """Re-derived from the pool arithmetic, NOT retyped from the preset.

    `_take` starts at (slot*3) % len(pool) and covers n consecutive indices, so two slots are
    disjoint iff their index sets do not intersect. A third slot at n=8 would share
    demonstrations with rows already emitted -- the failure G2 was retracted for.
    """
    b = pf._blocks("rbd12", ["a"])[0]
    n = b["n_examples"][0]
    per_split = 20  # a 20-sentence per-split pool; see prompt_families:78-89
    assert per_split // n == 2, "this test's premise moved; re-derive the disjoint count"

    pool = [f"s{i}" for i in range(per_split)]
    chosen = b["slots"]
    assert len(chosen) == per_split // n, "preset must use every disjoint slot and no more"
    sets = [set(pf._take(pool, n, s)) for s in chosen]
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            assert not (sets[i] & sets[j]), f"slots {chosen[i]} and {chosen[j]} share demos"
    # anti-vacuity: a slot outside the chosen set MUST overlap, or "disjoint" means nothing here
    extra = set(pf._take(pool, n, 1))
    assert extra & sets[0], "the disjointness test is vacuous if every slot is disjoint"


def test_main_does_not_gain_the_new_query_kind():
    for b in pf._blocks("main", list(pf.DOMAINS)):
        assert QK not in b["query_kinds"], f"block {b['name']} would change the canonical bank"


# --------------------------------------------------------------------------- #
# 2. The C-24 fix: every stem carries every readout
# --------------------------------------------------------------------------- #
def _stem(r):
    return r["family_id"].rpartition("|")[0]


def test_EVERY_family_stem_carries_all_three_readouts(bank):
    rows, _ = bank
    by_stem = {}
    for r in rows:
        by_stem.setdefault(_stem(r), set()).add(r["query_kind"])
    assert by_stem, "no rows generated"
    # Anti-vacuity, derived rather than hardcoded: a stem is (domain, split, slot) -- family_id
    # does NOT carry the condition, so one stem spans all four 2x2 cells. With 2 splits and the 2
    # disjoint slots at n=8 that is exactly 4 stems per domain.
    n_domains = len({r["domain"] for r in rows})
    assert n_domains >= 10, f"too few domains ({n_domains}) for this assertion to mean anything"
    assert len(by_stem) == n_domains * len(pf.SPLITS) * 2, \
        f"expected {n_domains * len(pf.SPLITS) * 2} stems, got {len(by_stem)}"
    missing = {s: sorted({"behavioral", "semantic_forced_choice", QK} - k)
               for s, k in by_stem.items() if len(k) != 3}
    assert not missing, f"{len(missing)} stems lack a readout side (this is the C-24 defect)"


def test_the_three_readouts_are_exactly_balanced(bank):
    rows, meta = bank
    counts = meta["by_query_kind"]
    assert counts["behavioral"] == counts["semantic_forced_choice"] == counts[QK]
    assert counts[QK] > 0


def test_conditions_are_balanced_and_the_2x2_has_no_violations(bank):
    rows, meta = bank
    vals = set(meta["by_condition"].values())
    assert len(vals) == 1, f"condition imbalance: {meta['by_condition']}"
    assert meta["n_alignment_violations"] == 0
    assert meta["n_2x2_families_checked"] > 0
    assert meta["n_duplicate_prompt_id_rows_dropped"] == 0


# --------------------------------------------------------------------------- #
# 3. Readout B rows are well formed
# --------------------------------------------------------------------------- #
def test_readout_b_rows_name_both_options_and_the_target_once(bank):
    rows, _ = bank
    mu = [r for r in rows if r["query_kind"] == QK]
    assert len(mu) > 0
    opts = pf.MAPPING_USE_OPTIONS[("lantern", "poison")]
    for r in mu:
        q = r["final_query_text"]
        assert opts["literal"] in q and opts["mapped"] in q
        assert q.count(r["target_surface"]) == 1, "target surface must appear exactly once"
        assert r["occurrence_analysis_safe"] is True


def test_readout_b_target_surface_follows_the_condition(bank):
    rows, _ = bank
    mu = [r for r in rows if r["query_kind"] == QK]
    for r in mu:
        expected = "lantern" if r["condition"] in ("natural_doublespeak", "benign_literal") \
            else "poison"
        assert r["target_surface"] == expected, r["condition"]


# --------------------------------------------------------------------------- #
# 4. Refusal (executed mutation of the input, not of the code)
# --------------------------------------------------------------------------- #
def test_REFUSES_a_pair_with_no_readout_b_options():
    """An unregistered pair must raise, not render 'in a  or in a '."""
    assert ("marble", "virus") not in pf.MAPPING_USE_OPTIONS
    ax = pf.Axes(domain="hospital_supply", split="dev", condition="natural_doublespeak",
                 n_examples=8, strength="none", consistency="consistent",
                 example_position="near", role_style="plain", query_kind=QK, family_slot=0)
    pools = json.load(open(POOLS))["pools"] if os.path.exists(POOLS) else None
    if pools is None:
        pytest.skip("pools file absent")
    with pytest.raises(KeyError) as e:
        pf.build_prompt(pools, ax, "marble", "virus")
    assert "MAPPING_USE_OPTIONS" in str(e.value)


def test_a_registered_pair_does_NOT_raise():
    """Isolation control -- otherwise the refusal test could pass for the wrong reason."""
    if not os.path.exists(POOLS):
        pytest.skip("pools file absent")
    pools = json.load(open(POOLS))["pools"]
    ax = pf.Axes(domain="hospital_supply", split="dev", condition="natural_doublespeak",
                 n_examples=8, strength="none", consistency="consistent",
                 example_position="near", role_style="plain", query_kind=QK, family_slot=0)
    r = pf.build_prompt(pools, ax, "lantern", "poison")
    assert "shed" in r["final_query_text"] and "cabinet" in r["final_query_text"]


# --------------------------------------------------------------------------- #
# 5. Every option word is single-token on BOTH models (committed evidence)
# --------------------------------------------------------------------------- #
def test_every_option_word_is_single_token_on_both_models():
    """Asserted against the committed screen artifact, not against a comment.

    `signals.readout_ids` refuses unless ' word' is exactly one token, so a two-token option would
    make the readout unanswerable -- the documented `" codeword"` -> ['cod','ew','ord'] casualty.
    """
    assert os.path.exists(SCREEN), f"missing screen artifact {SCREEN}"
    scr = json.load(open(SCREEN))
    assert len(scr["models"]) == 2

    needed = set()
    for (cw, cn), o in pf.MAPPING_USE_OPTIONS.items():
        needed.update([cw, cn, o["literal"], o["mapped"]])
    assert len(needed) >= 6, "too few words for this assertion to mean anything"

    for m in scr["models"]:
        per = scr["per_model"][m]
        uncovered = sorted(needed - set(per))
        assert not uncovered, f"{m}: screen does not cover {uncovered}"
        bad = sorted(w for w in needed if not per[w]["space_single"])
        assert not bad, f"{m}: not single-token with a leading space: {bad}"


def test_the_screen_artifact_is_not_vacuous():
    """It must actually record token ids, not just booleans someone could have typed."""
    scr = json.load(open(SCREEN))
    for m in scr["models"]:
        for w, rec in scr["per_model"][m].items():
            assert isinstance(rec["space_ids"], list) and rec["space_ids"]
            assert rec["space_single"] == (len(rec["space_ids"]) == 1), w


# --------------------------------------------------------------------------- #
# 8. Readout-B option articles (RBD-R-015, found by reviewing my own new code)
# --------------------------------------------------------------------------- #
def test_every_registered_option_word_is_consonant_initial():
    """The template hardcodes `in a {OPT}`, so a vowel-initial option emits `a attic`.

    Same class as RBD-R-004, and the exact-word-swap guard is structurally blind to it: the
    options do not vary by condition, so the ungrammaticality would be IDENTICAL in all four
    cells and survive masking.
    """
    assert pf.MAPPING_USE_OPTIONS, "no options registered"
    for (cw, cn), o in pf.MAPPING_USE_OPTIONS.items():
        pf._assert_option_articles_ok(o, cw, cn)          # must not raise
        for role, w in o.items():
            assert w[:1].lower() not in "aeiou", f"{cw}|{cn} {role}={w}"


def test_REFUSES_a_vowel_initial_option_word():
    with pytest.raises(ValueError) as e:
        pf._assert_option_articles_ok({"literal": "attic", "mapped": "bunker"}, "x", "y")
    assert "vowel-initial" in str(e.value)
    assert "a attic" in str(e.value)


def test_the_article_guard_is_WIRED_into_build_prompt(monkeypatch):
    """Testing the helper is not testing the guard. Bend the table and drive the real path."""
    if not os.path.exists(POOLS):
        pytest.skip("pools file absent")
    pools = json.load(open(POOLS))["pools"]
    ax = pf.Axes(domain="hospital_supply", split="dev", condition="natural_doublespeak",
                 n_examples=8, strength="none", consistency="consistent",
                 example_position="near", role_style="plain", query_kind=QK, family_slot=0)
    bent = dict(pf.MAPPING_USE_OPTIONS)
    bent[("lantern", "poison")] = {"literal": "attic", "mapped": "cabinet"}
    monkeypatch.setattr(pf, "MAPPING_USE_OPTIONS", bent)
    with pytest.raises(ValueError) as e:
        pf.build_prompt(pools, ax, "lantern", "poison")
    assert "vowel-initial" in str(e.value)


def test_the_wiring_test_is_not_vacuous():
    """Unbent, the same call must succeed -- otherwise the raise proves nothing."""
    if not os.path.exists(POOLS):
        pytest.skip("pools file absent")
    pools = json.load(open(POOLS))["pools"]
    ax = pf.Axes(domain="hospital_supply", split="dev", condition="natural_doublespeak",
                 n_examples=8, strength="none", consistency="consistent",
                 example_position="near", role_style="plain", query_kind=QK, family_slot=0)
    r = pf.build_prompt(pools, ax, "lantern", "poison")
    assert "in a shed" in r["final_query_text"]


def test_REFUSES_a_PARTIAL_options_entry():
    """F7 (RBD-DR-002): `{"literal": "shed"}` rendered `in a shed or in a ?` and was SCORED.

    A missing key is not in `opts.items()`, so the vowel scan could not see it, and `_opts is not
    None` meant the KeyError never fired either. Presence must be checked explicitly.
    """
    for bad in ({"literal": "shed"}, {"mapped": "cabinet"}, {"literal": "shed", "mapped": ""},
                {"literal": "  ", "mapped": "cabinet"}):
        with pytest.raises(ValueError) as e:
            pf._assert_option_articles_ok(bad, "x", "y")
        assert "missing or empty" in str(e.value)


def test_REFUSES_an_unknown_options_key():
    with pytest.raises(ValueError) as e:
        pf._assert_option_articles_ok(
            {"literal": "shed", "mapped": "cabinet", "typo": "x"}, "x", "y")
    assert "unknown" in str(e.value)


def test_a_PARTIAL_entry_is_refused_through_the_REAL_build_path(monkeypatch):
    if not os.path.exists(POOLS):
        pytest.skip("pools file absent")
    pools = json.load(open(POOLS))["pools"]
    ax = pf.Axes(domain="hospital_supply", split="dev", condition="natural_doublespeak",
                 n_examples=8, strength="none", consistency="consistent",
                 example_position="near", role_style="plain", query_kind=QK, family_slot=0)
    bent = dict(pf.MAPPING_USE_OPTIONS)
    bent[("lantern", "poison")] = {"literal": "shed"}
    monkeypatch.setattr(pf, "MAPPING_USE_OPTIONS", bent)
    with pytest.raises(ValueError) as e:
        pf.build_prompt(pools, ax, "lantern", "poison")
    assert "missing or empty" in str(e.value)
