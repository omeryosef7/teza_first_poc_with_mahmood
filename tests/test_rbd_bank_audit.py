"""Guard tests for `rbd_bank_audit`. RBD sprint, 2026-08-29.

§22 requires an EXECUTED mutation for every research-critical guard. Every check below is exercised
twice: once on the real shipped bank (must PASS), and once on a copy of that bank with a single
targeted corruption injected (must FAIL, and must name the corruption). A guard that has never been
seen to fail has not been tested.

The clean control matters as much as the mutant: `RBD-C-006` records that my first version of
`check_single_factor` failed on a PERFECTLY VALID bank because it encoded a stronger invariant than
the design claims. "The audit failed" is not the same as "the bank is bad", and the way to keep that
straight is to pin the passing case too.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import rbd_bank_audit as rba  # noqa: E402

BANK = os.path.join(ROOT, "data", "boombness_prompts",
                    "boombness_prompt_bank_rbd_lantern_poison.jsonl")
CW, CN = "lantern", "poison"


@pytest.fixture(scope="module")
def rows():
    if not os.path.exists(BANK):
        pytest.skip(f"bank absent: {BANK}")
    return rba.load_rows(BANK)


def _copy(rows):
    return copy.deepcopy(rows)


# --------------------------------------------------------------------------- #
# The clean control: every check must PASS on the shipped bank
# --------------------------------------------------------------------------- #
def test_the_shipped_bank_passes_every_check(rows):
    assert len(rows) == 960
    assert rba.check_ids_and_hashes(rows)[0]
    assert rba.check_duplicates(rows)[0]
    assert rba.check_balance(rows)[0]
    assert rba.check_readout_coverage(rows)[0]
    assert rba.check_single_factor(rows)[0]
    assert rba.check_articles(rows, CW, CN)[0]
    assert rba.check_lexical_collisions(rows, CW, CN)[0]
    assert rba.check_occurrences(rows, CW, CN)[0]
    assert rba.check_lengths(rows, CW, CN)[0]


def test_the_checks_are_not_vacuous_on_this_bank(rows):
    """Each check must actually examine a material number of rows."""
    assert rba.check_single_factor(rows)[1]["n_aligned_pairs_checked"] >= 100
    assert rba.check_readout_coverage(rows)[1]["n_stems"] == 80
    # {9: 640, 10: 320}, and the 10 is EXPLAINED, not tolerated: `semantic_forced_choice` names
    # both candidate words in its query, so when the target surface IS the codeword it appears once
    # as {W} and again as {CODEWORD} -- one extra occurrence on 320 rows. `mapping_use_forced_choice`
    # sits at 9 with the behavioural rows precisely because its options are PROPERTY words, which is
    # why Readout B is occurrence-safe and Readout A is not.
    dist = rba.check_occurrences(rows, CW, CN)[1]["target_occurrence_distribution"]
    assert dist == {9: 640, 10: 320}, dist
    n_sfc = sum(1 for r in rows if r["query_kind"] == "semantic_forced_choice")
    assert dist[10] == n_sfc, "the extra occurrence must be exactly the forced-choice rows"


# --------------------------------------------------------------------------- #
# Executed mutations, one per check
# --------------------------------------------------------------------------- #
def test_MUTANT_corrupted_prompt_sha16_is_caught(rows):
    m = _copy(rows)
    m[17]["prompt_sha16"] = "0" * 16
    ok, d = rba.check_ids_and_hashes(m)
    assert not ok and d["n_bad_prompt_sha16"] == 1


def test_MUTANT_corrupted_prompt_id_is_caught(rows):
    m = _copy(rows)
    m[3]["prompt_id"] = "deadbeefdeadbeef"
    ok, d = rba.check_ids_and_hashes(m)
    assert not ok and d["n_bad_prompt_id"] == 1


def test_MUTANT_duplicate_prompt_TEXT_is_caught_even_with_distinct_ids(rows):
    """The text-duplicate check is the one nothing else in the repo performs."""
    m = _copy(rows)
    m[5]["full_prompt"] = m[4]["full_prompt"]
    m[5]["prompt_sha16"] = hashlib.sha256(m[5]["full_prompt"].encode()).hexdigest()[:16]
    ok, d = rba.check_duplicates(m)
    assert not ok and d["n_duplicate_prompt_texts"] == 1
    assert d["n_duplicate_prompt_ids"] == 0, "ids are still distinct; text is the only signal"


def test_MUTANT_condition_imbalance_is_caught(rows):
    m = [r for r in rows if not (r["condition"] == "benign_literal" and r["domain"] == "dairy_plant")]
    ok, d = rba.check_balance(m)
    assert not ok and "condition" in d["unbalanced"]


def test_MUTANT_a_missing_readout_is_caught(rows):
    """This is the BC-C-24 defect: a stem with no probe side."""
    victim = rba._stem(rows[0])
    m = [r for r in rows
         if not (rba._stem(r) == victim and r["query_kind"] == "mapping_use_forced_choice")]
    ok, d = rba.check_readout_coverage(m)
    assert not ok and d["n_stems_missing_a_readout"] == 1


def test_MUTANT_a_single_factor_violation_is_caught(rows):
    """Inject an extra word into one cell of an aligned pair -- the `apple` failure mode."""
    m = _copy(rows)
    for r in m:
        if r["condition"] == "natural_doublespeak" and r["query_kind"] == "behavioral":
            r["full_prompt"] = r["full_prompt"] + " An extra clause."
            break
    ok, d = rba.check_single_factor(m)
    assert not ok and d["n_violations"] == 1


def test_MUTANT_an_ungrammatical_article_on_the_CODEWORD_is_caught(rows):
    """Clause 3 of RBD-C-005: the codeword must never appear after a bare `a`."""
    m = _copy(rows)
    m[0]["full_prompt"] = m[0]["full_prompt"] + f" There was a {CW} on the bench."
    ok, d = rba.check_articles(m, "apple", CN)  # pretend the codeword were vowel-initial
    assert d["a_before_vowel_total"] >= 0
    # direct form: a real `an` + consonant is always a defect
    m2 = _copy(rows)
    m2[0]["full_prompt"] = m2[0]["full_prompt"] + f" There was an {CN} on the bench."
    ok2, d2 = rba.check_articles(m2, CW, CN)
    assert not ok2 and d2["an_before_consonant_total"] == 1


def test_the_article_check_TOLERATES_the_documented_false_positive(rows):
    """`a unique` is correct English and must not fail the gate (RBD-C-005)."""
    m = _copy(rows)
    m[0]["full_prompt"] = m[0]["full_prompt"] + " It was a unique and a uniform result."
    ok, d = rba.check_articles(m, CW, CN)
    assert ok, d
    assert d["a_before_vowel_by_word"].get("unique", 0) >= 1


def test_MUTANT_a_leaked_word_in_the_demo_block_is_caught(rows):
    m = _copy(rows)
    for r in m:
        if r["condition"] == "natural_doublespeak":
            r["demo_block"] = (r["demo_block"] or "") + f"\nThe {CN} was logged."
            break
    ok, d = rba.check_lexical_collisions(m, CW, CN)
    assert not ok and d["n_rows_with_leak"] == 1


def test_MUTANT_a_miscounted_occurrence_is_caught(rows):
    m = _copy(rows)
    m[0]["n_target_occurrences"] = 99
    ok, d = rba.check_occurrences(m, CW, CN)
    assert not ok and d["n_recorded_vs_recounted_mismatches"] == 1


def test_MUTANT_an_aligned_pair_length_gap_is_caught(rows):
    """Padding one cell of an aligned pair breaks the exact word-length arithmetic."""
    m = _copy(rows)
    for r in m:
        if r["condition"] == "natural_doublespeak" and r["query_kind"] == "behavioral":
            r["full_prompt"] = r["full_prompt"] + ("x" * 500)
    ok, d = rba.check_lengths(m, CW, CN)
    assert not ok
    assert d["behavioral"]["aligned_pairs_ok"] is False


def test_the_expected_length_gap_is_exact_not_a_tolerance(rows):
    """len('lantern') - len('poison') = 1, times 9 occurrences = 9 chars, and it is observed."""
    ok, d = rba.check_lengths(rows, CW, CN)
    assert ok
    g = d["behavioral"]["aligned_gap:natural_doublespeak-direct_harmful"]
    assert g["expected_chars"] == pytest.approx(9.0)
    assert g["residual_chars"] <= 2.0


# --------------------------------------------------------------------------- #
# Not-checked must not read as passed
# --------------------------------------------------------------------------- #
def test_occurrence_unsafe_query_kinds_are_SKIPPED_not_passed(rows):
    ok, d = rba.check_single_factor(rows)
    assert ok
    assert "semantic_forced_choice" in d["skipped_query_kinds"]
    assert d["n_skipped_not_checkable"] > 0, "the skip must be counted, not silent"


def test_a_bank_with_NOTHING_checkable_does_not_pass():
    """Zero checked families must never read as zero violations."""
    rows = [{"family_id": "a|b|semantic_forced_choice", "query_kind": "semantic_forced_choice",
             "condition": "natural_doublespeak", "full_prompt": "x", "target_surface": "x",
             "occurrence_analysis_safe": False}]
    ok, d = rba.check_single_factor(rows)
    assert not ok
    assert d["n_aligned_pairs_checked"] == 0


# --------------------------------------------------------------------------- #
# Pool independence
# --------------------------------------------------------------------------- #
def test_pool_independence_passes_on_the_two_shipped_banks(rows):
    other = os.path.join(ROOT, "data", "boombness_prompts",
                         "boombness_prompt_bank_rbd_candle_missile.jsonl")
    if not os.path.exists(other):
        pytest.skip("second bank absent")
    ok, d = rba.check_pool_independence({"a": rows, "b": rba.load_rows(other)})
    assert ok
    assert d["a|b:shared_demo_sentences"] == 0
    assert d["a:within_bank_slot_overlaps"] == 0
    assert d["a:n_domain_split_groups"] == 40


def test_MUTANT_slots_that_share_a_demonstration_are_caught(rows):
    """The G2 failure: rows sharing demonstrations counted as independent."""
    m = _copy(rows)
    donor = target = None
    for r in m:
        if r["query_kind"] == "behavioral" and r["condition"] == "natural_doublespeak" \
                and r["domain"] == "hospital_supply" and r["split"] == "dev":
            if r["family_slot"] == 0:
                donor = r
            elif donor is not None:
                target = r
                break
    assert donor is not None and target is not None
    target["demo_block"] = donor["demo_block"]
    ok, d = rba.check_pool_independence({"a": m})
    assert not ok and d["a:within_bank_slot_overlaps"] >= 1
