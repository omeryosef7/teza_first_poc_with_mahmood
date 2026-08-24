"""Tests for demo_deletion_control (Phase 2C, plan §7).

Three things have to be true of this control, and each is tested against a case it must FAIL:
  1. the transformation removes the demo block AND NOTHING ELSE  -- checked by hash, not eyeball;
  2. the row's identity survives the transformation;
  3. the diversity guard REFUSES an arm that collapsed, and it decides that on TEXT HASHES --
     not on lengths (the uniq_frac defect) and not on source-row identity (the --demo-deleted
     defect). Both blind spots are exercised as MUTANTS of the real `_diversity_key`: with either
     mutation installed, a test in this file goes red.

No prompt text is printed or asserted on; every comparison is a hash comparison.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "boombness")
sys.path.insert(0, SRC)

import demo_deletion_control as D  # noqa: E402

BANK = os.path.join(ROOT, "data", "boombness_prompts", "boombness_prompt_bank.jsonl")


def _row(pid, demo, query="QQ", prefix="PRE:", suffix=":POST", **kw):
    r = {"prompt_id": pid, "family_id": "f1", "domain": "dom", "n_examples": 4,
         "query_kind": "behavioral", "condition": "natural_doublespeak",
         "bank_block": "core2x2", "demo_block": demo,
         "final_query_text": query,
         "full_prompt": prefix + demo + suffix, "prompt_sha16": "deadbeefdeadbeef"}
    r.update(kw)
    return r


# --------------------------------------------------------------------------- #
# 1. removes the demo block and nothing else
# --------------------------------------------------------------------------- #
def test_deletion_removes_demo_block_and_nothing_else():
    row = _row("p0", "DEMO-A-DEMO")
    rec = D.delete_demonstrations(row)
    prefix, suffix = "PRE:", ":POST"
    # the surrounding structure survives BYTE-FOR-BYTE (compared by hash)
    assert rec["prefix_sha16"] == D.sha16(prefix)
    assert rec["suffix_sha16"] == D.sha16(suffix)
    # the transformed prompt is exactly prefix+suffix ...
    assert rec["deleted_prompt_sha16"] == D.sha16(prefix + suffix)
    # ... and re-inserting the demo block reconstructs the ORIGINAL prompt exactly
    assert D.sha16(prefix + row["demo_block"] + suffix) == rec["source_prompt_sha16"]
    assert rec["n_chars_removed"] == len(row["demo_block"])
    assert rec["n_chars_source"] - rec["n_chars_deleted"] == rec["n_chars_removed"]
    # text is never carried into the on-disk record shape
    assert "deleted_prompt" in rec and rec["deleted_prompt"] == prefix + suffix


def test_deletion_preserves_row_identity():
    row = _row("p7", "DEMO", family_id="fam9", domain="chem", n_examples=8)
    rec = D.delete_demonstrations(row)
    assert rec["prompt_id"] == "p7"
    assert rec["family_id"] == "fam9"
    assert rec["domain"] == "chem"
    assert rec["n_examples"] == 8
    for k in D.IDENTITY_FIELDS:
        assert k in rec


@pytest.mark.parametrize("row,frag", [
    (_row("a", ""), "no_demo_block"),
    (_row("b", "NOT-PRESENT", prefix="PRE:", suffix=":POST") | {"full_prompt": "PRE::POST"},
     "demo_block_not_in_full_prompt"),
    (_row("c", "X") | {"full_prompt": "AXBXC"}, "demo_block_not_unique_in_prompt"),
    (_row("d", "WHOLE") | {"full_prompt": "WHOLE"}, "empty_after_deletion"),
])
def test_untransformable_rows_raise_rather_than_skip(row, frag):
    with pytest.raises(ValueError) as e:
        D.delete_demonstrations(row)
    assert frag in str(e.value)


def test_failures_are_booked_on_the_ledger_not_dropped():
    rows = [_row("ok1", "D1"), _row("bad", ""), _row("ok2", "D22")]
    led = D.FailureLedger()
    recs = D.transform_rows(rows, ledger=led)
    assert len(recs) == 2
    assert led.attempted == 3 and led.n_failed == 1
    assert "deletion:no_demo_block" in led.failures


# --------------------------------------------------------------------------- #
# 2. the diversity guard
# --------------------------------------------------------------------------- #
def _recs(rows):
    return D.transform_rows(rows, ledger=D.FailureLedger())


def _collapsed_rows(n=20):
    """n distinct SOURCE rows whose transformed prompts are all identical -- the real defect."""
    return [_row(f"p{i}", f"DEMO-{i}-{'x' * i}") for i in range(n)]


def _diverse_rows(n=20):
    return [_row(f"p{i}", f"DEMO-{i}", prefix=f"PRE{i}:", suffix=f":POST{i}") for i in range(n)]


def test_guard_refuses_a_collapsed_arm():
    rep = D.diversity_report(_recs(_collapsed_rows(20)))
    assert rep["n_distinct_transformed_prompts"] == 1
    assert rep["n_distinct_source_prompts"] == 20      # the trap: 20 distinct SOURCE prompts
    with pytest.raises(D.DeletionControlRefusal):
        D.check_diversity(rep)


def test_guard_passes_a_genuinely_diverse_arm():
    rep = D.diversity_report(_recs(_diverse_rows(20)))
    v = D.check_diversity(rep)
    assert v["passed"] and v["n_distinct_observed"] == 20


def test_guard_boundary_is_the_preregistered_threshold():
    # 20 rows, 18 distinct transformed prompts == ceil(0.90*20): the last passing configuration.
    rows = _diverse_rows(18) + [_row("dupA", "DEMO-0", prefix="PRE0:", suffix=":POST0"),
                                _row("dupB", "DEMO-1", prefix="PRE1:", suffix=":POST1")]
    rep = D.diversity_report(_recs(rows))
    assert rep["n_distinct_transformed_prompts"] == 18
    assert D.check_diversity(rep)["passed"]
    # one more duplicate (17/20) is below the floor and must be REFUSED
    rows2 = _diverse_rows(17) + [_row(f"dup{i}", f"DEMO-{i}", prefix=f"PRE{i}:", suffix=f":POST{i}")
                                 for i in range(3)]
    rep2 = D.diversity_report(_recs(rows2))
    assert rep2["n_distinct_transformed_prompts"] == 17
    with pytest.raises(D.DeletionControlRefusal):
        D.check_diversity(rep2)


def test_guard_cannot_be_switched_off():
    rep = D.diversity_report(_recs(_collapsed_rows(20)))
    for frac in (0.0, -1.0):
        with pytest.raises(D.DeletionControlRefusal):
            D.check_diversity(rep, min_distinct_frac=frac)


def test_artifact_carries_the_transformed_prompt_hashes():
    rep = D.diversity_report(_recs(_diverse_rows(5)))
    counts = rep["transformed_prompt_sha16_counts"]
    assert len(counts) == 5 and sum(counts.values()) == 5
    assert all(len(h) == 16 for h in counts)
    assert rep["diversity_measured_on"] == "sha16(transformed_prompt_text)"


# --------------------------------------------------------------------------- #
# 3. MUTATION TESTS: diversity is on hashes, not lengths, not source identity
# --------------------------------------------------------------------------- #
def test_mutant_length_key_would_refuse_a_genuinely_diverse_arm(monkeypatch):
    """MUTANT A -- key on LENGTH (the uniq_frac defect). Same-length, different-TEXT prompts.

    Real implementation: 20 distinct prompts, guard PASSES. Install the length key and the same
    assertion goes red (1 distinct 'prompt', guard refuses). Distinct text is not distinct length.
    """
    rows = [_row(f"p{i}", "DEMO", prefix=f"PR{i:02d}:", suffix=f":PO{i:02d}") for i in range(20)]
    recs = _recs(rows)
    assert len({r["n_chars_deleted"] for r in recs}) == 1          # all the same LENGTH
    assert D.check_diversity(D.diversity_report(recs))["passed"]   # real key: fine

    monkeypatch.setattr(D, "_diversity_key", lambda rec: str(len(rec["deleted_prompt"])))
    with pytest.raises(D.DeletionControlRefusal):
        D.check_diversity(D.diversity_report(recs))                # mutant: red


def test_mutant_source_identity_key_would_pass_a_collapsed_arm(monkeypatch):
    """MUTANT B -- key on the SOURCE prompt (the --demo-deleted defect), which is what made the
    old arm look healthy: 96 distinct source rows, 1 distinct transformed prompt.

    Real implementation REFUSES; the mutant PASSES a one-draw ceiling.
    """
    recs = _recs(_collapsed_rows(20))
    with pytest.raises(D.DeletionControlRefusal):
        D.check_diversity(D.diversity_report(recs))                # real key: refuses

    monkeypatch.setattr(D, "_diversity_key", lambda rec: rec["source_prompt_sha16"])
    assert D.check_diversity(D.diversity_report(recs))["passed"]   # mutant: false green


# --------------------------------------------------------------------------- #
# 4. the finding about the REAL bank (read-only; nothing is written)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not os.path.exists(BANK), reason="committed bank not present")
def test_real_bank_canonical_population_cannot_support_a_deletion_ceiling():
    rows = D.select_canonical(D.read_jsonl(BANK))
    assert len(rows) == 96
    census = D.bank_diversity_census(rows)
    assert census["n_distinct_full_prompt"] == 96
    assert census["n_distinct_demo_block"] == 96
    assert census["n_distinct_final_query_text"] == 1     # the old arm's source field
    recs = D.transform_rows(rows, ledger=D.FailureLedger())
    assert len(recs) == 96
    rep = D.diversity_report(recs)
    assert rep["n_distinct_transformed_prompts"] == 1     # THE FINDING
    assert rep["n_distinct_prefixes"] == 1 and rep["n_distinct_suffixes"] == 1
    with pytest.raises(D.DeletionControlRefusal):
        D.check_diversity(rep)


@pytest.mark.skipif(not os.path.exists(BANK), reason="committed bank not present")
def test_cli_aborts_on_the_real_bank_and_writes_an_auditable_artifact(tmp_path):
    out = str(tmp_path / "runs")
    rc = D.main(["--bank", BANK, "--out-root", out, "--tag", "t"])
    assert rc == 2                                        # abort, not a ceiling
    runs = []
    for dirpath, _dirnames, filenames in os.walk(out):
        if "summary.json" in filenames:
            runs.append(dirpath)
    assert len(runs) == 1
    rd = runs[0]
    assert os.path.exists(os.path.join(rd, "ABORTED.json"))
    assert not os.path.exists(os.path.join(rd, "DONE.json"))
    summ = json.load(open(os.path.join(rd, "summary.json")))
    div = summ["diversity"]
    assert div["n_distinct_transformed_prompts"] == 1
    # the hashes are IN the artifact, so the diversity claim is auditable later
    assert sum(div["transformed_prompt_sha16_counts"].values()) == 96
    assert summ["diversity_verdict"]["passed"] is False
    rows = [json.loads(l) for l in open(os.path.join(rd, "results.jsonl")) if l.strip()]
    assert len(rows) == 96
    assert all("deleted_prompt" not in r for r in rows)   # hashes on disk, never prompt text
    assert all(r["deleted_prompt_sha16"] == rows[0]["deleted_prompt_sha16"] for r in rows)
