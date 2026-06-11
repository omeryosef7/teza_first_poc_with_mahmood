"""
Tests for Stage 4.7 canonicalization output.

Validates the canonical_per_run_results.csv and related audit files
produced by poc_stage4_7/audit_and_canonicalize_results.py.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_RUN_DIR = _REPO_ROOT / "outputs" / "stage4_7" / "runs" / "run_array_20260610_1442"
_ANALYSIS_DIR = _RUN_DIR / "analysis"
_CANONICAL_CSV = _ANALYSIS_DIR / "canonical_per_run_results.csv"
_INTEGRITY_JSON = _ANALYSIS_DIR / "stage4_7_integrity_audit.json"
_CENSORING_CSV = _ANALYSIS_DIR / "censoring_audit.csv"


def _load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def canonical_rows():
    if not _CANONICAL_CSV.exists():
        pytest.skip(f"Canonical CSV not found: {_CANONICAL_CSV}")
    return _load_csv(_CANONICAL_CSV)


@pytest.fixture(scope="module")
def integrity_audit():
    if not _INTEGRITY_JSON.exists():
        pytest.skip(f"Integrity audit not found: {_INTEGRITY_JSON}")
    return _load_json(_INTEGRITY_JSON)


@pytest.fixture(scope="module")
def censoring_rows():
    if not _CENSORING_CSV.exists():
        pytest.skip(f"Censoring audit CSV not found: {_CENSORING_CSV}")
    return _load_csv(_CENSORING_CSV)


# ---------------------------------------------------------------------------
# Row count and uniqueness
# ---------------------------------------------------------------------------

def test_canonical_row_count(canonical_rows):
    assert len(canonical_rows) == 48, f"Expected 48 rows, got {len(canonical_rows)}"


def test_no_duplicate_source_condition_pairs(canonical_rows):
    pairs = [(r["source_example_id"], r["condition"]) for r in canonical_rows]
    assert len(pairs) == len(set(pairs)), "Duplicate (source_example_id, condition) pairs found"


def test_twelve_source_prompts(canonical_rows):
    sources = set(r["source_example_id"] for r in canonical_rows)
    assert len(sources) == 12, f"Expected 12 unique source prompts, got {len(sources)}"


def test_four_conditions_per_prompt(canonical_rows):
    from collections import Counter
    cond_count = Counter(
        r["source_example_id"] for r in canonical_rows
    )
    assert all(v == 4 for v in cond_count.values()), (
        "Some source prompts do not have exactly 4 condition rows"
    )


# ---------------------------------------------------------------------------
# Censoring columns
# ---------------------------------------------------------------------------

def test_exactly_five_censored_rows(canonical_rows):
    censored = [r for r in canonical_rows if r.get("is_censored", "").lower() in ("true", "1")]
    assert len(censored) == 5, f"Expected 5 censored rows, got {len(censored)}"


def test_complete_case_null_for_censored(canonical_rows):
    for r in canonical_rows:
        is_censored = r.get("is_censored", "").lower() in ("true", "1")
        cc = r.get("sr_success_complete_case", "")
        if is_censored:
            assert cc in ("", "None", "null", None), (
                f"sr_success_complete_case should be NULL for censored row {r.get('source_example_id')}"
                f" cond={r.get('condition')}, got {cc!r}"
            )


def test_legacy_matches_sr_success(canonical_rows):
    for r in canonical_rows:
        legacy = r.get("sr_success_legacy", "")
        sr = r.get("sr_success", "")
        # Both should be the same non-null value (legacy never converts to NULL)
        if legacy not in ("", "None", "null", None) and sr not in ("", "None", "null", None):
            assert str(legacy).lower() == str(sr).lower(), (
                f"sr_success_legacy != sr_success for {r.get('source_example_id')} cond={r.get('condition')}"
            )


# ---------------------------------------------------------------------------
# Integrity audit JSON
# ---------------------------------------------------------------------------

def test_integrity_audit_passed(integrity_audit):
    assert integrity_audit.get("passed") is True, (
        f"Integrity audit did not pass: {integrity_audit.get('errors', [])}"
    )


def test_integrity_audit_row_count(integrity_audit):
    assert integrity_audit.get("n_rows") == 48


def test_integrity_audit_censored_count(integrity_audit):
    n_censored = integrity_audit.get("n_censored", 0)
    assert n_censored == 5, f"Expected 5 censored, got {n_censored}"


# ---------------------------------------------------------------------------
# Censoring audit CSV
# ---------------------------------------------------------------------------

def test_censoring_audit_has_five_rows(censoring_rows):
    assert len(censoring_rows) == 5, f"Expected 5 censoring audit rows, got {len(censoring_rows)}"


def test_censoring_audit_conditions(censoring_rows):
    """All censored rows should come from conditions D, E, or F (not A)."""
    for r in censoring_rows:
        assert r.get("condition") in ("D", "E", "F"), (
            f"Unexpected censored condition: {r.get('condition')}"
        )


# ---------------------------------------------------------------------------
# Condition distribution
# ---------------------------------------------------------------------------

def test_all_four_conditions_present(canonical_rows):
    conds = set(r["condition"] for r in canonical_rows)
    assert conds == {"A", "D", "F", "E"}, f"Unexpected conditions: {conds}"


def test_twelve_rows_per_condition(canonical_rows):
    from collections import Counter
    counts = Counter(r["condition"] for r in canonical_rows)
    for cond in ("A", "D", "F", "E"):
        assert counts[cond] == 12, f"Condition {cond}: expected 12, got {counts[cond]}"
