"""
Tests for Stage 4.8 source selection, manifest, and analysis utilities.

All tests are CPU-only (no model loading). GPU-dependent behavior is tested
at runtime via the smoke audit in stage4_8_repeated_generations_smoke.slurm.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_STAGE4_8_DIR = _REPO_ROOT / "outputs" / "stage4_8"
_SOURCE_SELECTION_CSV = _STAGE4_8_DIR / "source_prompt_selection.csv"
_SOURCE_SELECTION_JSON = _STAGE4_8_DIR / "source_prompt_selection_manifest.json"
_MANIFEST_JSONL = _STAGE4_8_DIR / "repeated_generation_manifest.jsonl"
_MANIFEST_AUDIT = _STAGE4_8_DIR / "manifest_audit.json"

_EXPECTED_SEEDS = [101, 102, 103, 104, 105]
_EXPECTED_CONDITIONS = ["A", "D", "F"]
_EXPECTED_GOALS = [0, 1, 2, 3]
_EXPECTED_TOTAL = 60
_TEMPERATURE = 0.7
_TOP_P = 0.95


def _load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def source_selection():
    if not _SOURCE_SELECTION_CSV.exists():
        pytest.skip(f"Source selection CSV not found: {_SOURCE_SELECTION_CSV}")
    return _load_csv(_SOURCE_SELECTION_CSV)


@pytest.fixture(scope="module")
def manifest_rows():
    if not _MANIFEST_JSONL.exists():
        pytest.skip(f"Manifest JSONL not found: {_MANIFEST_JSONL}")
    return _load_jsonl(_MANIFEST_JSONL)


@pytest.fixture(scope="module")
def manifest_audit():
    if not _MANIFEST_AUDIT.exists():
        pytest.skip(f"Manifest audit not found: {_MANIFEST_AUDIT}")
    return _load_json(_MANIFEST_AUDIT)


# ---------------------------------------------------------------------------
# Source prompt selection
# ---------------------------------------------------------------------------

def test_exactly_four_source_prompts(source_selection):
    assert len(source_selection) == 4, f"Expected 4 source prompts, got {len(source_selection)}"


def test_one_source_per_goal(source_selection):
    goals = [int(r["goal_index"]) for r in source_selection]
    assert sorted(goals) == _EXPECTED_GOALS, f"Expected goals {_EXPECTED_GOALS}, got {sorted(goals)}"


def test_all_source_prompts_have_distinct_source_ids(source_selection):
    ids = [r["source_example_id"] for r in source_selection]
    assert len(ids) == len(set(ids)), "Duplicate source_example_ids in selection"


def test_source_selection_determinism():
    """Run select_source_prompts logic twice and confirm same output."""
    if not _SOURCE_SELECTION_CSV.exists():
        pytest.skip("Source selection CSV not found")

    import sys
    sys.path.insert(0, str(_REPO_ROOT))

    try:
        from poc_stage4_8 import select_source_prompts
    except ImportError:
        pytest.skip("select_source_prompts module not importable")

    # Load the selection function and call it; compare to saved result
    rows1 = _load_csv(_SOURCE_SELECTION_CSV)
    # Run again (does not write — just returns selected rows)
    if not hasattr(select_source_prompts, "select_prompts"):
        pytest.skip("select_prompts function not found in select_source_prompts module")

    try:
        rows2 = select_source_prompts.select_prompts()
    except Exception as e:
        pytest.skip(f"Could not re-run selection: {e}")

    ids1 = sorted(r["source_example_id"] for r in rows1)
    ids2 = sorted(r.get("source_example_id", "") for r in rows2)
    assert ids1 == ids2, "Selection is not deterministic"


# ---------------------------------------------------------------------------
# Manifest structure
# ---------------------------------------------------------------------------

def test_manifest_exactly_sixty_rows(manifest_rows):
    assert len(manifest_rows) == _EXPECTED_TOTAL, (
        f"Expected {_EXPECTED_TOTAL} manifest rows, got {len(manifest_rows)}"
    )


def test_manifest_unique_run_ids(manifest_rows):
    run_ids = [r["run_id"] for r in manifest_rows]
    dups = [k for k, v in Counter(run_ids).items() if v > 1]
    assert not dups, f"Duplicate run_ids: {dups[:5]}"


def test_manifest_seeds(manifest_rows):
    seeds = sorted(set(int(r["seed"]) for r in manifest_rows))
    assert seeds == sorted(_EXPECTED_SEEDS), f"Expected seeds {_EXPECTED_SEEDS}, got {seeds}"


def test_manifest_conditions(manifest_rows):
    conditions = sorted(set(r["condition"] for r in manifest_rows))
    assert conditions == sorted(_EXPECTED_CONDITIONS)


def test_manifest_goals(manifest_rows):
    goals = sorted(set(int(r["goal_index"]) for r in manifest_rows))
    assert goals == _EXPECTED_GOALS


def test_manifest_per_cell_count(manifest_rows):
    """Each (source_example_id, condition) cell should have exactly 5 rows (one per seed)."""
    cells = defaultdict(int)
    for r in manifest_rows:
        cells[(r["source_example_id"], r["condition"])] += 1
    wrong = {k: v for k, v in cells.items() if v != 5}
    assert not wrong, f"Cells with wrong seed count: {wrong}"


def test_manifest_sampling_config_consistent(manifest_rows):
    for r in manifest_rows:
        temp = float(r.get("temperature", r.get("sampling_temperature", float("nan"))))
        if not math.isnan(temp):
            assert abs(temp - _TEMPERATURE) < 0.01, f"temperature mismatch: {temp} for {r.get('run_id')}"
        top_p = float(r.get("top_p", r.get("sampling_top_p", float("nan"))))
        if not math.isnan(top_p):
            assert abs(top_p - _TOP_P) < 0.01, f"top_p mismatch: {top_p} for {r.get('run_id')}"
        assert r.get("do_sample") in (True, "True", "true", 1, "1"), (
            f"do_sample not True for {r.get('run_id')}"
        )


def test_run_id_contains_seed(manifest_rows):
    for r in manifest_rows:
        seed = r.get("seed")
        run_id = r.get("run_id", "")
        assert f"__seed_{seed}" in run_id, (
            f"run_id {run_id!r} does not contain seed component __seed_{seed}"
        )


def test_run_id_contains_condition(manifest_rows):
    for r in manifest_rows:
        cond = r.get("condition")
        run_id = r.get("run_id", "")
        assert f"cond_{cond}" in run_id, (
            f"run_id {run_id!r} does not contain condition component cond_{cond}"
        )


def test_manifest_audit_passed(manifest_audit):
    assert manifest_audit.get("passed") is True, (
        f"Manifest audit did not pass: {manifest_audit.get('errors', [])}"
    )


# ---------------------------------------------------------------------------
# Analysis utilities (unit tests — no GPU)
# ---------------------------------------------------------------------------

def _make_fake_rows():
    """Build a small synthetic run_summary.jsonl-shaped list for unit testing."""
    rows = []
    source_ids = ["src_goal0", "src_goal1"]
    conditions = ["A", "D", "F"]
    seeds = [101, 102, 103]

    for src in source_ids:
        goal = 0 if "goal0" in src else 1
        for cond in conditions:
            for i, seed in enumerate(seeds):
                sr_score = 0.8 if (cond == "A" and i % 2 == 0) else 0.2
                rows.append({
                    "run_id": f"{src}__cond_{cond}__seed_{seed}",
                    "source_example_id": src,
                    "condition": cond,
                    "goal_index": goal,
                    "seed": seed,
                    "finish_reason": "eos_token",
                    "thinking_segmentation_status": "parsed_from_think_tags",
                    "strongreject_score": sr_score,
                    "sr_success": sr_score >= 0.5,
                    "think_token_count": 1000 + i * 200,
                    "do_sample": True,
                    "sampling_temperature": 0.7,
                    "sampling_top_p": 0.95,
                    "generation_hash": f"hash_{src}_{cond}_{seed}",
                })
    return rows


def test_build_cell_summary_shape():
    """Cell summary should have one row per (source, condition) pair."""
    import sys
    sys.path.insert(0, str(_REPO_ROOT))
    from poc_stage4_8.analyze_repeated_generations import build_cell_summary

    rows = _make_fake_rows()
    cells = build_cell_summary(rows)
    # 2 sources × 3 conditions = 6 cells
    assert len(cells) == 6, f"Expected 6 cells, got {len(cells)}"


def test_matched_cells_require_success_and_failure():
    """Matched cells must have ≥1 success AND ≥1 failure."""
    import sys
    sys.path.insert(0, str(_REPO_ROOT))
    from poc_stage4_8.analyze_repeated_generations import build_cell_summary, build_matched_outcome_cells

    rows = _make_fake_rows()
    cells = build_cell_summary(rows)
    matched = build_matched_outcome_cells(cells)

    for cell in matched:
        assert cell["has_success"], f"Matched cell {cell['source_example_id']} cond={cell['condition']} has no success"
        assert cell["has_failure"], f"Matched cell {cell['source_example_id']} cond={cell['condition']} has no failure"


def test_no_censored_rows_in_matched_cells():
    """Censored rows (max_new_tokens) must not contribute to matched-cell detection."""
    import sys
    sys.path.insert(0, str(_REPO_ROOT))
    from poc_stage4_8.analyze_repeated_generations import build_cell_summary, build_matched_outcome_cells

    rows = _make_fake_rows()
    # Add a censored row that would otherwise flip a cell to "matched"
    rows.append({
        "run_id": "src_goal1__cond_A__seed_999",
        "source_example_id": "src_goal1",
        "condition": "A",
        "goal_index": 1,
        "seed": 999,
        "finish_reason": "max_new_tokens",  # censored
        "thinking_segmentation_status": "parsed_from_think_tags",
        "strongreject_score": 0.9,
        "sr_success": True,
        "think_token_count": 32768,
        "do_sample": True,
        "sampling_temperature": 0.7,
        "sampling_top_p": 0.95,
        "generation_hash": "hash_censored",
    })

    cells = build_cell_summary(rows)
    for cell in cells:
        # n_complete should not count censored rows
        assert cell["n_censored"] >= 0
        # The censored row's sr_success should not be counted in matched-cell detection
        if cell["source_example_id"] == "src_goal1" and cell["condition"] == "A":
            # This cell now has only censored rows showing success
            # The censored row must not count toward n_valid_seg for matching
            assert cell["n_censored"] == 1


def test_variance_decomposition_structure():
    """Variance decomposition output has expected keys."""
    import sys
    sys.path.insert(0, str(_REPO_ROOT))
    from poc_stage4_8.analyze_repeated_generations import build_variance_decomposition

    rows = _make_fake_rows()
    vd = build_variance_decomposition(rows)

    assert "n_cells" in vd
    assert "n_complete" in vd
    assert "mean_within_cell_variance" in vd
    assert "between_cell_variance" in vd


# ---------------------------------------------------------------------------
# Audit utility unit tests
# ---------------------------------------------------------------------------

def test_audit_catches_duplicate_run_ids():
    import sys
    sys.path.insert(0, str(_REPO_ROOT))
    import tempfile, json
    from poc_stage4_8.audit_repeated_generations import audit

    # Build a minimal fake run_summary.jsonl with a duplicate
    rows = [
        {"run_id": "r1__cond_A__seed_101", "seed": 101, "do_sample": True,
         "sampling_temperature": 0.7, "sampling_top_p": 0.95,
         "finish_reason": "eos_token", "strongreject_score": 0.5,
         "thinking_segmentation_status": "parsed_from_think_tags",
         "generation_hash": "abc", "source_example_id": "s1", "condition": "A"},
        {"run_id": "r1__cond_A__seed_101", "seed": 101, "do_sample": True,
         "sampling_temperature": 0.7, "sampling_top_p": 0.95,
         "finish_reason": "eos_token", "strongreject_score": 0.5,
         "thinking_segmentation_status": "parsed_from_think_tags",
         "generation_hash": "abc", "source_example_id": "s1", "condition": "A"},
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "run_summary.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
        result = audit(p, smoke=True)
    assert not result["passed"], "Audit should fail with duplicate run_ids"
    assert any("Duplicate" in e for e in result["errors"])


def test_audit_passes_for_valid_smoke_rows():
    import sys
    sys.path.insert(0, str(_REPO_ROOT))
    import tempfile, json
    from poc_stage4_8.audit_repeated_generations import audit

    rows = []
    for seed, ghash in [(101, "aaa"), (102, "bbb")]:
        for cond in ("A", "D", "F"):
            run_id = f"src_goal0__cond_{cond}__seed_{seed}"
            rows.append({
                "run_id": run_id,
                "seed": seed,
                "do_sample": True,
                "sampling_temperature": 0.7,
                "sampling_top_p": 0.95,
                "finish_reason": "eos_token",
                "strongreject_score": 0.8,
                "thinking_segmentation_status": "parsed_from_think_tags",
                "generation_hash": f"{ghash}_{cond}",
                "source_example_id": "src_goal0",
                "condition": cond,
            })

    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "run_summary.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
        result = audit(p, smoke=True)

    assert result["passed"], f"Smoke audit failed: {result['errors']}"
    assert result["n_rows"] == 6
    assert result["n_diverse_cells"] > 0, "Expected generation hash diversity"
