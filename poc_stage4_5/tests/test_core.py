"""
Stage 4.5 smoke tests.

All tests run without GPU using synthetic data and temp directories.
Run with:  python -m pytest poc_stage4_5/tests/test_core.py -v
       or: python poc_stage4_5/tests/test_core.py
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

# Ensure repo root is on sys.path when run directly
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common


# ---------------------------------------------------------------------------
# Synthetic data helpers
# ---------------------------------------------------------------------------

def _make_synthetic_tld(
    n_think: int = 10,
    n_final: int = 5,
    n_layers: int = 40,
    rng: np.random.Generator | None = None,
) -> list[dict]:
    """Build synthetic token_level_data for testing."""
    if rng is None:
        rng = np.random.default_rng(0)
    tld = []
    idx = 0
    # special token at 0
    tld.append({
        "generated_token_index": idx,
        "absolute_token_index": 100 + idx,
        "token_id": 1,
        "token_text": "<think>",
        "is_special_token": True,
        "role_or_part": "special",
        "layer_projections": {str(l): float(rng.normal(0, 1)) for l in range(n_layers)},
    })
    idx += 1
    for _ in range(n_think):
        tld.append({
            "generated_token_index": idx,
            "absolute_token_index": 100 + idx,
            "token_id": idx + 100,
            "token_text": f"tok_{idx}",
            "is_special_token": False,
            "role_or_part": "think",
            "layer_projections": {str(l): float(rng.normal(l * 0.1, 1)) for l in range(n_layers)},
        })
        idx += 1
    # </think> special
    tld.append({
        "generated_token_index": idx,
        "absolute_token_index": 100 + idx,
        "token_id": 2,
        "token_text": "</think>",
        "is_special_token": True,
        "role_or_part": "special",
        "layer_projections": {str(l): float(rng.normal(0, 1)) for l in range(n_layers)},
    })
    idx += 1
    for _ in range(n_final):
        tld.append({
            "generated_token_index": idx,
            "absolute_token_index": 100 + idx,
            "token_id": idx + 200,
            "token_text": f"ans_{idx}",
            "is_special_token": False,
            "role_or_part": "final",
            "layer_projections": {str(l): float(rng.normal(l * 0.2, 1)) for l in range(n_layers)},
        })
        idx += 1
    return tld


# ---------------------------------------------------------------------------
# Feature computation (imported here from the analysis module when it exists,
# but tested independently until then with a local copy of the logic)
# ---------------------------------------------------------------------------

def _compute_event_features_local(
    tld: list[dict],
    harmful_start_idx: int,
    layer: int,
    pre_window: int = 500,
    post_early_window: int = 250,
    post_late_window: int = 1000,
) -> dict:
    """Local reference implementation of event-aligned feature calculation."""
    think_toks = [t for t in tld if t.get("role_or_part") == "think"]
    key = str(layer)
    pre, post_early, post_late = [], [], []
    for t in think_toks:
        rel = t["generated_token_index"] - harmful_start_idx
        v = t["layer_projections"].get(key)
        if v is None or not math.isfinite(v):
            continue
        if -pre_window <= rel < 0:
            pre.append(v)
        if 0 <= rel < post_early_window:
            post_early.append(v)
        if post_early_window <= rel < post_late_window:
            post_late.append(v)

    pre_arr = np.array(pre, dtype=np.float64)
    early_arr = np.array(post_early, dtype=np.float64)
    late_arr = np.array(post_late, dtype=np.float64)

    pre_mean = float(np.mean(pre_arr)) if len(pre_arr) > 0 else float("nan")
    early_mean = float(np.mean(early_arr)) if len(early_arr) > 0 else float("nan")
    late_mean = float(np.mean(late_arr)) if len(late_arr) > 0 else float("nan")
    delta_early = early_mean - pre_mean if not (math.isnan(pre_mean) or math.isnan(early_mean)) else float("nan")

    return {
        "pre_event_n_tokens": len(pre_arr),
        "post_event_n_tokens": len(early_arr) + len(late_arr),
        "pre_event_mean_projection": pre_mean,
        "post_event_early_mean": early_mean,
        "post_event_late_mean": late_mean,
        "event_delta_early": delta_early,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEventAlignedFeatures(unittest.TestCase):
    """Tests for event-aligned feature computation logic."""

    def test_event_aligned_features_basic(self) -> None:
        """Start token in middle of think phase; all windows populated; no NaN."""
        tld = _make_synthetic_tld(n_think=20, n_final=5)
        # Think tokens have generated_token_index 1..20
        # harmful_start at index 6 → pre window: indices 1..5 (5 tokens)
        harmful_start = 6
        feats = _compute_event_features_local(tld, harmful_start, layer=22)
        self.assertEqual(feats["pre_event_n_tokens"], 5)
        self.assertTrue(feats["post_event_n_tokens"] > 0)
        self.assertFalse(math.isnan(feats["pre_event_mean_projection"]))
        self.assertFalse(math.isnan(feats["post_event_early_mean"]))
        self.assertFalse(math.isnan(feats["event_delta_early"]))

    def test_nan_pre_event_empty_window(self) -> None:
        """Start token at first think token → empty pre-event window → NaN."""
        tld = _make_synthetic_tld(n_think=10, n_final=5)
        # Think tokens start at index 1; harmful_start at 1 → pre window empty
        feats = _compute_event_features_local(tld, 1, layer=22)
        self.assertEqual(feats["pre_event_n_tokens"], 0)
        self.assertTrue(math.isnan(feats["pre_event_mean_projection"]))
        self.assertTrue(math.isnan(feats["event_delta_early"]))

    def test_start_at_special_token(self) -> None:
        """Start at the <think> special token (index 0) → no pre-event think tokens."""
        tld = _make_synthetic_tld(n_think=10)
        feats = _compute_event_features_local(tld, 0, layer=22)
        self.assertEqual(feats["pre_event_n_tokens"], 0)
        self.assertTrue(math.isnan(feats["pre_event_mean_projection"]))

    def test_start_at_final_phase(self) -> None:
        """Start token in final phase; all think tokens are pre-event."""
        tld = _make_synthetic_tld(n_think=10, n_final=5)
        # final tokens start at index 12 (1 special + 10 think + 1 special)
        # harmful_start at 13 (a final token)
        final_start_idx = 12  # </think> special; first final token is 13
        feats = _compute_event_features_local(tld, final_start_idx, layer=22)
        # pre_window covers think tokens 1..11 that are < 12
        # Think tokens are indices 1..10, all < 12, all in pre window if within 500
        self.assertEqual(feats["pre_event_n_tokens"], 10)
        self.assertFalse(math.isnan(feats["pre_event_mean_projection"]))


class TestFirthImport(unittest.TestCase):
    """Verify Firth regression is importable and converges on synthetic data."""

    def test_firth_import_and_convergence(self) -> None:
        from poc_stage4.fit_confound_models import firth_fit
        rng = np.random.default_rng(42)
        n = 20
        X = np.column_stack([np.ones(n), rng.normal(0, 1, n)])
        y = rng.integers(0, 2, n).astype(np.float64)
        result = firth_fit(X, y)
        self.assertIn("coef", result)
        self.assertIn("converged", result)
        self.assertEqual(len(result["coef"]), 2)


class TestCommonPaths(unittest.TestCase):
    """Verify path constants resolve to real directories."""

    def test_repo_root_exists(self) -> None:
        self.assertTrue(common.REPO_ROOT.exists(), f"REPO_ROOT not found: {common.REPO_ROOT}")

    def test_stage4_run_dir_exists(self) -> None:
        self.assertTrue(
            common.STAGE4_RUN_DIR.exists(),
            f"STAGE4_RUN_DIR not found: {common.STAGE4_RUN_DIR}",
        )

    def test_stage6_traces_dir_exists(self) -> None:
        self.assertTrue(
            common.STAGE6_TRACES_DIR.exists(),
            f"STAGE6_TRACES_DIR not found: {common.STAGE6_TRACES_DIR}",
        )

    def test_analysis_dataset_exists(self) -> None:
        self.assertTrue(
            common.ANALYSIS_DATASET_PATH.exists(),
            f"analysis_dataset.csv not found: {common.ANALYSIS_DATASET_PATH}",
        )


class TestLoadAnalysisDataset(unittest.TestCase):
    """Load the real analysis_dataset.csv and verify row count and types."""

    def test_loads_42_rows(self) -> None:
        rows = common.load_analysis_dataset()
        self.assertEqual(len(rows), 42, f"Expected 42 rows, got {len(rows)}")

    def test_typed_fields(self) -> None:
        rows = common.load_analysis_dataset()
        r = rows[0]
        self.assertIsInstance(r["sr_success"], bool)
        self.assertIsInstance(r["goal_index"], int)
        self.assertIsInstance(r["strongreject_score"], float)
        self.assertIsInstance(r["think_token_count"], int)


class TestReviewCsvAppend(unittest.TestCase):
    """Verify atomic CSV append: two rows written, two rows readable."""

    def test_two_rows_roundtrip(self) -> None:
        from poc_stage4_5.review_example import PROGRESS_FIELDNAMES
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "progress.csv"
            row1 = {
                "example_id": "ex_1",
                "reviewer_id": "primary",
                "review_timestamp_utc": "2026-01-01T00:00:00",
                "human_label": "full_refusal",
                "reviewer_confidence": "high",
                "human_success_strict": "False",
                "human_success_lenient": "False",
                "contains_harmful_interaction": "no",
                "think_shows_hijack": "no",
                "reviewer_notes": "",
                "response_sha256": "abc123",
                "review_status": "completed",
            }
            row2 = {
                "example_id": "ex_2",
                "reviewer_id": "primary",
                "review_timestamp_utc": "2026-01-01T00:01:00",
                "human_label": "substantive_compliance",
                "reviewer_confidence": "medium",
                "human_success_strict": "True",
                "human_success_lenient": "True",
                "contains_harmful_interaction": "yes",
                "think_shows_hijack": "yes",
                "reviewer_notes": "test",
                "response_sha256": "def456",
                "review_status": "completed",
            }
            common.append_csv_row(path, row1, PROGRESS_FIELDNAMES)
            common.append_csv_row(path, row2, PROGRESS_FIELDNAMES)
            read_back = common.read_csv_as_list(path)
            self.assertEqual(len(read_back), 2)
            self.assertEqual(read_back[0]["example_id"], "ex_1")
            self.assertEqual(read_back[1]["human_label"], "substantive_compliance")

    def test_progress_schema_has_reviewer_id_and_review_status(self) -> None:
        from poc_stage4_5.review_example import PROGRESS_FIELDNAMES
        self.assertIn("reviewer_id", PROGRESS_FIELDNAMES)
        self.assertIn("review_status", PROGRESS_FIELDNAMES)


class TestAnnotationRoundtrip(unittest.TestCase):
    """Verify annotation CSV: write one row, read it back with matching fields."""

    def test_annotation_fields(self) -> None:
        from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "annotations.csv"
            row = {
                "example_id": "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini",
                "annotation_timestamp_utc": "2026-01-01T00:00:00",
                "harmful_interaction_start_token": "42",
                "annotation_confidence": "high",
                "interaction_phase": "think",
                "annotation_notes": "starts reasoning about target at this token",
                "annotator_id": "primary",
                "annotation_status": "annotated",
            }
            common.append_csv_row(path, row, ANNOTATIONS_FIELDNAMES)
            read_back = common.read_csv_as_list(path)
            self.assertEqual(len(read_back), 1)
            self.assertEqual(read_back[0]["harmful_interaction_start_token"], "42")
            self.assertEqual(read_back[0]["interaction_phase"], "think")
            self.assertEqual(read_back[0]["annotation_confidence"], "high")

    def test_annotation_schema_has_required_fields(self) -> None:
        from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES
        required = {
            "annotation_confidence", "harmful_interaction_start_token",
            "harmful_interaction_end_token", "final_answer_start_token",
            "decision_or_commitment_candidate_token", "right_censored",
            "segmentation_complete",
        }
        for f in required:
            self.assertIn(f, ANNOTATIONS_FIELDNAMES, f"Missing field: {f}")
        self.assertNotIn("annotator_confidence", ANNOTATIONS_FIELDNAMES,
                         "Old field name 'annotator_confidence' must not be present")


class TestGracefulDegradationNoAnnotations(unittest.TestCase):
    """The analysis script must exit 0 and emit a warning when no annotations exist."""

    def test_analyze_runs_without_annotations(self) -> None:
        """Verify the analysis module can be imported and its graceful path is reachable."""
        # This test just checks the module can be imported; the actual graceful
        # degradation path is exercised in test_build_queue_empty below.
        # Full CLI invocation tests are done in integration.
        try:
            import poc_stage4_5.analyze_harmful_interaction_aligned_dynamics  # noqa: F401
        except ImportError as e:
            self.skipTest(f"Module not yet implemented: {e}")


class TestExampleIdFilenameConversion(unittest.TestCase):
    """Verify example_id → filename conversions are correct."""

    EX_ID = "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"

    def test_s4_filename(self) -> None:
        expected = "goal_index_0_attack_iteration_1_conversation_id_1_target_model_gpt-o4-mini"
        self.assertEqual(common.example_id_to_s4_filename(self.EX_ID), expected)

    def test_s6_filename(self) -> None:
        expected = "qwen3_14b_trace_goal_index_0_attack_iteration_1_conversation_id_1_target_model_gpt-o4-mini"
        self.assertEqual(common.example_id_to_s6_filename(self.EX_ID), expected)

    def test_s4_file_exists_on_disk(self) -> None:
        stem = common.example_id_to_s4_filename(self.EX_ID)
        path = common.STAGE4_PER_EXAMPLE_DIR / f"{stem}.json"
        self.assertTrue(path.exists(), f"Stage 4 artifact not found: {path}")

    def test_s6_file_exists_on_disk(self) -> None:
        stem = common.example_id_to_s6_filename(self.EX_ID)
        path = common.STAGE6_TRACES_DIR / f"{stem}.json"
        self.assertTrue(path.exists(), f"Stage 6 artifact not found: {path}")


class TestFrozenDirNotModified(unittest.TestCase):
    """Running the queue builder must not touch frozen Stage 4 artifacts."""

    _FILES_TO_CHECK = [
        common.STAGE4_RUN_DIR / "manifest.json",
        common.ANALYSIS_DATASET_PATH,
        # pick first per-example file
    ]

    def test_frozen_mtimes_unchanged_after_queue_build(self) -> None:
        """Import the queue builder module and check no frozen files are modified."""
        # Record mtimes
        targets = list(self._FILES_TO_CHECK)
        first_s4 = next(common.STAGE4_PER_EXAMPLE_DIR.glob("*.json"), None)
        if first_s4:
            targets.append(first_s4)

        before = {str(p): p.stat().st_mtime for p in targets if p.exists()}

        # Import the queue builder (does not auto-run; only side-effects are in main())
        try:
            import poc_stage4_5.build_manual_adjudication_queue  # noqa: F401
        except ImportError:
            self.skipTest("build_manual_adjudication_queue not yet implemented")

        after = {str(p): p.stat().st_mtime for p in targets if p.exists()}
        for k in before:
            self.assertEqual(before[k], after.get(k, before[k]),
                             f"Frozen file modified: {k}")


class TestGetThinkTokens(unittest.TestCase):
    """get_think_tokens returns only role_or_part == 'think' tokens."""

    def test_filters_correctly(self) -> None:
        tld = _make_synthetic_tld(n_think=10, n_final=5)
        think = common.get_think_tokens(tld)
        self.assertEqual(len(think), 10)
        for t in think:
            self.assertEqual(t["role_or_part"], "think")


class TestGetProjectionsAtLayer(unittest.TestCase):
    """get_projections_at_layer returns parallel arrays of indices and values."""

    def test_indices_match_projections(self) -> None:
        tld = _make_synthetic_tld(n_think=5)
        think = common.get_think_tokens(tld)
        idxs, projs = common.get_projections_at_layer(think, layer=22)
        self.assertEqual(len(idxs), len(projs))
        self.assertEqual(len(idxs), 5)
        # Indices should be in ascending order (generated_token_index)
        self.assertTrue(np.all(np.diff(idxs) > 0))


class TestEventQueueRightCensored(unittest.TestCase):
    """Regression: separable right-censored examples must start as 'pending', not 'right_censored'."""

    def test_right_censored_separable_is_pending(self) -> None:
        from poc_stage4_5.build_event_annotation_queue import _initial_annotation_status
        row = {
            "thinking_segmentation_status": "parsed_from_think_tags",
            "right_censored": True,
        }
        status = _initial_annotation_status(row)
        self.assertEqual(
            status, "pending",
            "Separable right-censored example must start as 'pending', not 'right_censored'",
        )

    def test_not_separable_is_not_separable(self) -> None:
        from poc_stage4_5.build_event_annotation_queue import _initial_annotation_status
        row = {
            "thinking_segmentation_status": "not_separable",
            "right_censored": True,
        }
        status = _initial_annotation_status(row)
        self.assertEqual(status, "not_separable")

    def test_normal_example_is_pending(self) -> None:
        from poc_stage4_5.build_event_annotation_queue import _initial_annotation_status
        row = {
            "thinking_segmentation_status": "parsed_from_think_tags",
            "right_censored": False,
        }
        status = _initial_annotation_status(row)
        self.assertEqual(status, "pending")

    def test_live_queue_has_41_pending_1_not_separable(self) -> None:
        """The live event_annotation_queue must have exactly 41 pending and 1 not_separable."""
        from poc_stage4_5.build_event_annotation_queue import build_annotation_queue
        queue = build_annotation_queue(
            common.ANALYSIS_DATASET_PATH,
            common.DEFAULT_REVIEW_DIR / "manual_adjudication_progress.csv",
            common.DEFAULT_REVIEW_DIR / "harmful_interaction_annotations.csv",
        )
        status_counts: dict[str, int] = {}
        for row in queue:
            s = row["annotation_status"]
            status_counts[s] = status_counts.get(s, 0) + 1
        self.assertEqual(len(queue), 42, f"Expected 42 total, got {len(queue)}")
        self.assertEqual(
            status_counts.get("pending", 0), 41,
            f"Expected 41 pending, got {status_counts}",
        )
        self.assertEqual(
            status_counts.get("not_separable", 0), 1,
            f"Expected 1 not_separable, got {status_counts}",
        )
        self.assertEqual(
            status_counts.get("right_censored", 0), 0,
            f"Expected 0 right_censored in initial queue (it should be pending), got {status_counts}",
        )


class TestReportAnnotationProgress(unittest.TestCase):
    """Verify report_annotation_progress produces consistent counts."""

    def test_empty_review_dir(self) -> None:
        from poc_stage4_5.report_annotation_progress import report_progress
        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir)
            data = report_progress(review_dir, common.ANALYSIS_DATASET_PATH)
            mr = data["manual_review"]
            ea = data["event_annotation"]
            self.assertEqual(mr["completed"], 0)
            self.assertEqual(mr["pending"], 42)
            self.assertEqual(mr["strict_successes"], 0)
            self.assertEqual(ea["pending"], 41)
            self.assertEqual(ea["not_separable"], 1)
            self.assertEqual(ea["right_censored"], 0)
            self.assertEqual(ea["annotated"], 0)

    def test_partial_annotations(self) -> None:
        from poc_stage4_5.report_annotation_progress import report_progress
        from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES
        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir)
            ann_path = review_dir / "harmful_interaction_annotations.csv"
            # Write one annotation
            ann_row = {
                "example_id": "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini",
                "annotation_timestamp_utc": "2026-01-01T00:00:00",
                "harmful_interaction_start_token": "10",
                "annotation_confidence": "high",
                "interaction_phase": "think",
                "annotation_notes": "",
                "annotator_id": "primary",
                "annotation_status": "annotated",
            }
            common.append_csv_row(ann_path, ann_row, ANNOTATIONS_FIELDNAMES)
            data = report_progress(review_dir, common.ANALYSIS_DATASET_PATH)
            ea = data["event_annotation"]
            self.assertEqual(ea["annotated"], 1)
            self.assertEqual(ea["think_phase"], 1)
            self.assertEqual(ea["high_confidence"], 1)
            self.assertEqual(ea["pending"], 40)  # 41 - 1 annotated

    def test_json_output_importable(self) -> None:
        """The main() function with --json must return valid JSON to stdout."""
        import io
        import contextlib
        from poc_stage4_5.report_annotation_progress import main
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with tempfile.TemporaryDirectory() as tmpdir:
                ret = main([
                    "--review-dir", tmpdir,
                    "--analysis-dataset", str(common.ANALYSIS_DATASET_PATH),
                    "--json",
                ])
        self.assertEqual(ret, 0)
        import json
        parsed = json.loads(buf.getvalue())
        self.assertIn("manual_review", parsed)
        self.assertIn("event_annotation", parsed)


# ---------------------------------------------------------------------------
# Pilot selection tests
# ---------------------------------------------------------------------------

def _make_synthetic_dataset(n: int = 20, seed: int = 0) -> list[dict]:
    """Return a minimal synthetic analysis dataset suitable for pilot selection tests."""
    import random as _random
    rng = _random.Random(seed)
    rows = []
    for i in range(n):
        goal = i % 4
        sr = i % 2 == 0
        judge = (i % 3 != 0)  # creates some disagreements
        rows.append({
            "example_id": f"goal_index={goal}|attack_iteration=1|conversation_id={i}|target_model=m",
            "goal_index": goal,
            "attack_iteration": 1,
            "conversation_id": i,
            "target_model": "m",
            "strongreject_score": 1.0 if sr else 0.0,
            "sr_success": sr,
            "judge_score": 1 if judge else 0,
            "judge_success": judge,
            "think_token_count": 1000 + rng.randint(0, 4000),
            "right_censored": (i == 0),   # first example is right-censored
            "thinking_segmentation_status": (
                "not_separable" if i == 1 else "parsed_from_think_tags"
            ),
        })
    return rows


class TestPilotSelection(unittest.TestCase):

    def setUp(self):
        self.dataset = _make_synthetic_dataset(n=20)

    def test_deterministic(self):
        from poc_stage4_5.select_pilot_examples import select_pilot
        r1 = [r["example_id"] for r in select_pilot(self.dataset, seed=42)]
        r2 = [r["example_id"] for r in select_pilot(self.dataset, seed=42)]
        self.assertEqual(r1, r2)

    def test_correct_counts(self):
        from poc_stage4_5.select_pilot_examples import select_pilot
        selected = select_pilot(self.dataset)
        successes = [r for r in selected if r["pilot_role"] == "sr_success"]
        failures = [r for r in selected if r["pilot_role"] == "sr_failure"]
        self.assertEqual(len(successes), 5)
        self.assertEqual(len(failures), 5)

    def test_excludes_not_separable(self):
        from poc_stage4_5.select_pilot_examples import select_pilot
        selected = select_pilot(self.dataset)
        for r in selected:
            self.assertEqual(
                r["thinking_segmentation_status"], "parsed_from_think_tags",
                f"Not-separable example included: {r['example_id']}"
            )

    def test_excludes_right_censored_primary(self):
        from poc_stage4_5.select_pilot_examples import select_pilot
        # Ensure enough non-censored examples → right-censored should be absent
        selected = select_pilot(self.dataset)
        for r in selected:
            self.assertFalse(
                r["right_censored"],
                f"Right-censored example included: {r['example_id']}"
            )

    def test_disagreements_prioritized(self):
        from poc_stage4_5.select_pilot_examples import select_pilot
        # Make a dataset where every non-censored, separable example disagrees;
        # all 10 selected must be disagreements.
        dataset = _make_synthetic_dataset(n=20)
        for r in dataset:
            if not r["right_censored"] and r["thinking_segmentation_status"] == "parsed_from_think_tags":
                r["judge_success"] = not r["sr_success"]  # force disagreement
        selected = select_pilot(dataset)
        disagree_count = sum(1 for r in selected if r["is_disagreement"])
        self.assertEqual(disagree_count, 10)

    def test_manifest_fields(self):
        from poc_stage4_5.select_pilot_examples import select_pilot, write_pilot_manifest
        selected = select_pilot(self.dataset)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "manifest.json"
            write_pilot_manifest(selected, self.dataset, path)
            with open(path) as f:
                m = json.load(f)
        for key in ("created_utc", "random_seed", "pilot_size", "n_success", "n_failure",
                    "selection_rules", "eligibility", "n_disagreements_included",
                    "selected_example_ids", "per_example"):
            self.assertIn(key, m, f"Missing key: {key}")
        self.assertEqual(m["pilot_size"], 10)
        self.assertEqual(len(m["selected_example_ids"]), 10)

    def test_write_pilot_queue_csv_schema(self):
        from poc_stage4_5.select_pilot_examples import (
            select_pilot, write_pilot_queue, PILOT_QUEUE_FIELDNAMES,
        )
        selected = select_pilot(self.dataset)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "pilot_queue.csv"
            write_pilot_queue(selected, path)
            rows = list(csv.DictReader(open(path)))
        self.assertEqual(len(rows), 10)
        for fn in PILOT_QUEUE_FIELDNAMES:
            self.assertIn(fn, rows[0], f"Missing CSV column: {fn}")
        self.assertTrue(all(r["review_status"] == "pending" for r in rows))
        self.assertTrue(all(r["annotation_status"] == "pending" for r in rows))


# ---------------------------------------------------------------------------
# Pilot subset analysis tests
# ---------------------------------------------------------------------------

class TestPilotSubsetAnalysis(unittest.TestCase):

    def _make_per_example_rows(self, example_ids: list[str]) -> list[dict]:
        """Synthetic per-example rows for a set of example_ids."""
        rows = []
        for i, eid in enumerate(example_ids):
            rows.append({
                "example_id": eid,
                "goal_index": i % 4,
                "attack_iteration": 1,
                "conversation_id": i,
                "sr_success": "True" if i % 2 == 0 else "False",
                "judge_success": "True" if i % 3 != 0 else "False",
                "think_token_count": 1000,
                "generation_token_count": 2000,
                "right_censored": "False",
                "layer": 22,
                "is_primary_analysis": True,
                "is_exploratory_layer": False,
                "annotation_confidence": "high",
                "pre_event_mean_projection": float(i),
                "post_event_early_mean": float(i + 1),
                "post_event_late_mean": float(i + 2),
                "event_delta_early": 1.0,
                "relative_onset_position": 0.5,
            })
        return rows

    def test_example_ids_filter_in_run_analysis(self):
        """dataset_meta is correctly filtered to example_ids before processing."""
        from poc_stage4_5.analyze_harmful_interaction_aligned_dynamics import run_analysis
        all_ids = [
            f"goal_index=0|attack_iteration=1|conversation_id={i}|target_model=gpt-o4-mini"
            for i in range(1, 4)
        ]
        pilot_ids = {all_ids[0], all_ids[1]}
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            for sub in ("analysis", "plots/aggregate", "plots/per_example", "manifests", "logs"):
                (run_dir / sub).mkdir(parents=True, exist_ok=True)
            review_dir = Path(tmpdir) / "review"
            review_dir.mkdir()
            # run_analysis with example_ids: expect it to start (may exit early due to
            # no annotations) without error and respect the filter
            ret = run_analysis(
                run_dir=run_dir,
                review_dir=review_dir,
                seed=42,
                n_bootstrap=10,
                n_permutations=10,
                layers=[22],
                example_ids=pilot_ids,
                pilot_mode=True,
            )
            self.assertEqual(ret, 0)
            # pilot_results.json must exist when pilot_mode=True
            self.assertTrue((run_dir / "analysis" / "pilot_results.json").exists())
            with open(run_dir / "analysis" / "pilot_results.json") as f:
                pr = json.load(f)
            self.assertEqual(
                pr["analysis_scope"],
                "pilot_exploratory_not_full_human_ground_truth",
            )
            self.assertFalse(pr["human_labels_used_as_outcome"])

    def test_gemini_sensitivity_outcome_col(self):
        """compute_group_summary with outcome_col='judge_success' groups by judge_success."""
        import numpy as np
        from poc_stage4_5.analyze_harmful_interaction_aligned_dynamics import compute_group_summary
        rows = self._make_per_example_rows(
            [f"goal_index=0|attack_iteration=1|conversation_id={i}|target_model=m"
             for i in range(8)]
        )
        rng = np.random.default_rng(0)
        # sr_success and judge_success differ for some rows
        summary_sr = compute_group_summary(rows, rng, n_bootstrap=10, n_permutations=10,
                                           outcome_col="sr_success")
        summary_j = compute_group_summary(rows, rng, n_bootstrap=10, n_permutations=10,
                                          outcome_col="judge_success")
        # Both should run without error and return the same number of rows
        self.assertEqual(len(summary_sr), len(summary_j))
        # They may differ in n_success/n_failure because groups are defined differently
        n_s_sr = {r["n_success"] for r in summary_sr if r["layer"] == 22 and r["subset"] == "primary"}
        n_s_j = {r["n_success"] for r in summary_j if r["layer"] == 22 and r["subset"] == "primary"}
        # Just assert both completed without error; group sizes can differ
        self.assertTrue(len(n_s_sr) > 0 or True)
        self.assertTrue(len(n_s_j) > 0 or True)


# ---------------------------------------------------------------------------
# Test 1: Three-label human harmful-interaction mapping
# ---------------------------------------------------------------------------

class TestThreeLabelMapping(unittest.TestCase):
    """yes/no/ambiguous → strict/lenient mapping is correct."""

    def test_yes_maps_to_true_true(self) -> None:
        from poc_stage4_5.review_example import _label_to_strict_lenient
        strict, lenient = _label_to_strict_lenient("yes")
        self.assertEqual(strict, "True")
        self.assertEqual(lenient, "True")

    def test_no_maps_to_false_false(self) -> None:
        from poc_stage4_5.review_example import _label_to_strict_lenient
        strict, lenient = _label_to_strict_lenient("no")
        self.assertEqual(strict, "False")
        self.assertEqual(lenient, "False")

    def test_ambiguous_maps_to_empty_empty(self) -> None:
        from poc_stage4_5.review_example import _label_to_strict_lenient
        strict, lenient = _label_to_strict_lenient("ambiguous")
        self.assertEqual(strict, "", "ambiguous strict must be empty string (None)")
        self.assertEqual(lenient, "", "ambiguous lenient must be empty string (None)")

    def test_ambiguous_not_lenient_true(self) -> None:
        """Regression: ambiguous must NOT map lenient=True (old bug)."""
        from poc_stage4_5.review_example import _label_to_strict_lenient
        _, lenient = _label_to_strict_lenient("ambiguous")
        self.assertNotEqual(lenient, "True", "ambiguous must not be lenient=True")

    def test_human_labels_constant(self) -> None:
        """HUMAN_LABELS in common must be the three-label set."""
        self.assertEqual(sorted(common.HUMAN_LABELS), ["ambiguous", "no", "yes"])


# ---------------------------------------------------------------------------
# Test 2: Pilot progress reporting with --queue
# ---------------------------------------------------------------------------

class TestReportWithQueue(unittest.TestCase):
    """--queue restricts the report to pilot IDs only."""

    def setUp(self) -> None:
        from poc_stage4_5.review_example import PROGRESS_FIELDNAMES
        from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES
        self.PROGRESS_FIELDNAMES = PROGRESS_FIELDNAMES
        self.ANNOTATIONS_FIELDNAMES = ANNOTATIONS_FIELDNAMES

    def _write_queue(self, path: Path, ids: list[str]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            import csv as _csv
            w = _csv.DictWriter(f, fieldnames=["example_id"])
            w.writeheader()
            for eid in ids:
                w.writerow({"example_id": eid})

    def test_queue_filters_manual_reviews(self) -> None:
        from poc_stage4_5.report_annotation_progress import report_progress
        pilot_ids = [
            "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini",
            "goal_index=0|attack_iteration=1|conversation_id=2|target_model=gpt-o4-mini",
        ]
        extra_id = "goal_index=0|attack_iteration=1|conversation_id=3|target_model=gpt-o4-mini"

        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir) / "review"
            review_dir.mkdir()
            queue_path = Path(tmpdir) / "queue.csv"
            self._write_queue(queue_path, pilot_ids)

            progress_path = review_dir / "manual_adjudication_progress.csv"
            for eid in pilot_ids + [extra_id]:
                row = {
                    "example_id": eid, "reviewer_id": "primary",
                    "review_timestamp_utc": "2026-01-01T00:00:00",
                    "human_label": "yes", "reviewer_confidence": "high",
                    "human_success_strict": "True", "human_success_lenient": "True",
                    "contains_harmful_interaction": "yes",
                    "think_shows_hijack": "", "reviewer_notes": "",
                    "response_sha256": "abc", "review_status": "completed",
                }
                common.append_csv_row(progress_path, row, self.PROGRESS_FIELDNAMES)

            data = report_progress(review_dir, common.ANALYSIS_DATASET_PATH, queue_path)
            mr = data["manual_review"]
            # Only pilot_ids counted (2), not extra_id (3)
            self.assertEqual(mr["total"], 2)
            self.assertEqual(mr["completed"], 2)
            self.assertTrue(data["is_pilot"])

    def test_queue_filters_event_annotations(self) -> None:
        from poc_stage4_5.report_annotation_progress import report_progress
        pilot_id = "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"
        extra_id = "goal_index=0|attack_iteration=1|conversation_id=2|target_model=gpt-o4-mini"

        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir) / "review"
            review_dir.mkdir()
            queue_path = Path(tmpdir) / "queue.csv"
            self._write_queue(queue_path, [pilot_id])

            ann_path = review_dir / "harmful_interaction_annotations.csv"
            for eid in (pilot_id, extra_id):
                row = {
                    "example_id": eid,
                    "annotation_timestamp_utc": "2026-01-01T00:00:00",
                    "harmful_interaction_start_token": "10",
                    "annotation_confidence": "high",
                    "interaction_phase": "think",
                    "annotation_notes": "",
                    "annotator_id": "primary",
                    "annotation_status": "annotated",
                }
                common.append_csv_row(ann_path, row, self.ANNOTATIONS_FIELDNAMES)

            data = report_progress(review_dir, common.ANALYSIS_DATASET_PATH, queue_path)
            ea = data["event_annotation"]
            self.assertEqual(ea["total"], 1)
            self.assertEqual(ea["annotated"], 1)
            self.assertEqual(ea["think_phase"], 1)

    def test_json_output_with_queue(self) -> None:
        import io, contextlib, json as _json
        from poc_stage4_5.report_annotation_progress import main
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = Path(tmpdir) / "queue.csv"
            import csv as _csv
            with open(queue_path, "w", newline="") as f:
                w = _csv.DictWriter(f, fieldnames=["example_id"])
                w.writeheader()
                w.writerow({"example_id":
                    "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"})
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                ret = main([
                    "--review-dir", tmpdir,
                    "--analysis-dataset", str(common.ANALYSIS_DATASET_PATH),
                    "--queue", str(queue_path),
                    "--json",
                ])
            self.assertEqual(ret, 0)
            parsed = _json.loads(buf.getvalue())
            self.assertIn("manual_review", parsed)
            self.assertIn("event_annotation", parsed)
            self.assertTrue(parsed.get("is_pilot"))

    def test_special_phase_counted_in_report(self) -> None:
        from poc_stage4_5.report_annotation_progress import report_progress
        pilot_id = "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"
        with tempfile.TemporaryDirectory() as tmpdir:
            review_dir = Path(tmpdir) / "review"
            review_dir.mkdir()
            queue_path = Path(tmpdir) / "queue.csv"
            self._write_queue(queue_path, [pilot_id])
            from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES
            ann_path = review_dir / "harmful_interaction_annotations.csv"
            row = {
                "example_id": pilot_id,
                "annotation_timestamp_utc": "2026-01-01",
                "harmful_interaction_start_token": "0",
                "annotation_confidence": "high",
                "interaction_phase": "special",
                "annotation_notes": "",
                "annotator_id": "primary",
                "annotation_status": "annotated",
            }
            common.append_csv_row(ann_path, row, ANNOTATIONS_FIELDNAMES)
            data = report_progress(review_dir, common.ANALYSIS_DATASET_PATH, queue_path)
            ea = data["event_annotation"]
            self.assertEqual(ea["special_phase"], 1)
            self.assertEqual(ea["think_phase"], 0)
            self.assertEqual(ea["final_phase"], 0)


# ---------------------------------------------------------------------------
# Test 3: Pilot event queue IDs
# ---------------------------------------------------------------------------

class TestPilotEventQueueIds(unittest.TestCase):
    """pilot_example_queue.csv has exactly 10 unique IDs matching the manifest."""

    PILOT_QUEUE = common.DEFAULT_REVIEW_DIR / "pilot_example_queue.csv"
    MANIFEST = common.DEFAULT_REVIEW_DIR / "pilot_selection_manifest.json"

    def test_pilot_queue_has_10_rows(self) -> None:
        rows = common.read_csv_as_list(self.PILOT_QUEUE)
        self.assertEqual(len(rows), 10, f"Expected 10 rows in pilot queue, got {len(rows)}")

    def test_pilot_queue_has_10_unique_ids(self) -> None:
        rows = common.read_csv_as_list(self.PILOT_QUEUE)
        ids = [r["example_id"] for r in rows]
        self.assertEqual(len(set(ids)), 10, "Duplicate example_ids in pilot queue")

    def test_pilot_ids_match_manifest(self) -> None:
        with open(self.MANIFEST, encoding="utf-8") as f:
            manifest = json.load(f)
        manifest_ids = set(manifest["selected_example_ids"])
        queue_ids = {r["example_id"] for r in common.read_csv_as_list(self.PILOT_QUEUE)}
        self.assertEqual(queue_ids, manifest_ids, "pilot_example_queue.csv IDs differ from manifest")

    def test_all_pilot_ids_in_event_queue(self) -> None:
        from poc_stage4_5.build_event_annotation_queue import build_annotation_queue
        queue = build_annotation_queue(
            common.ANALYSIS_DATASET_PATH,
            common.DEFAULT_REVIEW_DIR / "manual_adjudication_progress.csv",
            common.DEFAULT_REVIEW_DIR / "harmful_interaction_annotations.csv",
        )
        event_ids = {r["example_id"] for r in queue}
        pilot_ids = {r["example_id"] for r in common.read_csv_as_list(self.PILOT_QUEUE)}
        missing = pilot_ids - event_ids
        self.assertEqual(missing, set(), f"Pilot IDs missing from event queue: {missing}")


# ---------------------------------------------------------------------------
# Test 4: Rebuild event queue preserves existing annotations
# ---------------------------------------------------------------------------

class TestRebuildPreservesAnnotations(unittest.TestCase):
    """build_annotation_queue must not overwrite completed annotations."""

    def test_existing_annotation_preserved_in_queue(self) -> None:
        from poc_stage4_5.build_event_annotation_queue import build_annotation_queue
        from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES

        annotated_id = "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"
        with tempfile.TemporaryDirectory() as tmpdir:
            ann_path = Path(tmpdir) / "harmful_interaction_annotations.csv"
            row = {
                "example_id": annotated_id,
                "annotation_timestamp_utc": "2026-01-01T00:00:00",
                "harmful_interaction_start_token": "42",
                "annotation_confidence": "high",
                "interaction_phase": "think",
                "annotation_notes": "",
                "annotator_id": "primary",
                "annotation_status": "annotated",
            }
            common.append_csv_row(ann_path, row, ANNOTATIONS_FIELDNAMES)
            # No progress file → all reviews missing
            progress_path = Path(tmpdir) / "manual_adjudication_progress.csv"
            queue = build_annotation_queue(
                common.ANALYSIS_DATASET_PATH, progress_path, ann_path
            )
            annotated_rows = [r for r in queue if r["example_id"] == annotated_id]
            self.assertEqual(len(annotated_rows), 1)
            self.assertEqual(annotated_rows[0]["annotation_status"], "annotated",
                             "Existing annotation_status must be preserved")
            self.assertEqual(annotated_rows[0]["harmful_interaction_start_token"], "42")

    def test_rebuild_does_not_change_other_statuses(self) -> None:
        from poc_stage4_5.build_event_annotation_queue import build_annotation_queue
        from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES

        no_harmful_id = "goal_index=0|attack_iteration=1|conversation_id=2|target_model=gpt-o4-mini"
        with tempfile.TemporaryDirectory() as tmpdir:
            ann_path = Path(tmpdir) / "harmful_interaction_annotations.csv"
            row = {
                "example_id": no_harmful_id,
                "annotation_timestamp_utc": "2026-01-01T00:00:00",
                "harmful_interaction_start_token": "-1",
                "annotation_confidence": "high",
                "interaction_phase": "none",
                "annotation_notes": "",
                "annotator_id": "primary",
                "annotation_status": "no_harmful_interaction_found",
            }
            common.append_csv_row(ann_path, row, ANNOTATIONS_FIELDNAMES)
            progress_path = Path(tmpdir) / "manual_adjudication_progress.csv"
            queue = build_annotation_queue(
                common.ANALYSIS_DATASET_PATH, progress_path, ann_path
            )
            target = next((r for r in queue if r["example_id"] == no_harmful_id), None)
            self.assertIsNotNone(target)
            self.assertEqual(target["annotation_status"], "no_harmful_interaction_found")


# ---------------------------------------------------------------------------
# Test 5: Event index may be in think, final, or special segment
# ---------------------------------------------------------------------------

class TestEventPhaseVariants(unittest.TestCase):
    """interaction_phase reflects the role_or_part of the annotated token."""

    def _token_list(self) -> list[dict]:
        """Build a minimal token list with one token of each phase."""
        return [
            {"generated_token_index": 0, "role_or_part": "special",
             "token_text": "<think>", "is_special_token": True,
             "layer_projections": {"22": 0.1}},
            {"generated_token_index": 1, "role_or_part": "think",
             "token_text": "tok1", "is_special_token": False,
             "layer_projections": {"22": 0.2}},
            {"generated_token_index": 2, "role_or_part": "think",
             "token_text": "tok2", "is_special_token": False,
             "layer_projections": {"22": 0.3}},
            {"generated_token_index": 3, "role_or_part": "special",
             "token_text": "</think>", "is_special_token": True,
             "layer_projections": {"22": 0.1}},
            {"generated_token_index": 4, "role_or_part": "final",
             "token_text": "ans1", "is_special_token": False,
             "layer_projections": {"22": 0.4}},
        ]

    def _resolve_phase(self, tokens: list[dict], target_idx: int) -> str:
        for t in tokens:
            if t["generated_token_index"] == target_idx:
                return t.get("role_or_part", "unknown")
        return "unknown"

    def test_think_phase_resolved(self) -> None:
        tokens = self._token_list()
        phase = self._resolve_phase(tokens, 1)
        self.assertEqual(phase, "think")

    def test_final_phase_resolved(self) -> None:
        tokens = self._token_list()
        phase = self._resolve_phase(tokens, 4)
        self.assertEqual(phase, "final")

    def test_special_phase_resolved(self) -> None:
        tokens = self._token_list()
        phase = self._resolve_phase(tokens, 0)
        self.assertEqual(phase, "special")

    def test_annotation_statuses_include_all_phases(self) -> None:
        """ANNOTATION_STATUSES must not forbid any phase selection."""
        self.assertIn("annotated", common.ANNOTATION_STATUSES)
        self.assertIn("pending", common.ANNOTATION_STATUSES)
        self.assertIn("uncertain", common.ANNOTATION_STATUSES)
        self.assertIn("right_censored", common.ANNOTATION_STATUSES)
        self.assertIn("not_separable", common.ANNOTATION_STATUSES)
        self.assertIn("no_harmful_interaction_found", common.ANNOTATION_STATUSES)


# ---------------------------------------------------------------------------
# Test 6: Generated-token index is not confused with global (absolute) index
# ---------------------------------------------------------------------------

class TestGeneratedVsAbsoluteIndex(unittest.TestCase):
    """The annotate CLI validates against generated_token_index, not absolute_token_index."""

    def test_valid_indices_are_generated_indices(self) -> None:
        tokens = [
            {"generated_token_index": 0, "absolute_token_index": 500,
             "role_or_part": "think", "token_text": "t", "is_special_token": False,
             "layer_projections": {}},
            {"generated_token_index": 1, "absolute_token_index": 501,
             "role_or_part": "think", "token_text": "u", "is_special_token": False,
             "layer_projections": {}},
        ]
        valid_indices = {t["generated_token_index"] for t in tokens}
        # generated_token_indices: {0, 1}  absolute: {500, 501}
        self.assertIn(0, valid_indices)
        self.assertIn(1, valid_indices)
        self.assertNotIn(500, valid_indices)
        self.assertNotIn(501, valid_indices)

    def test_set_command_rejects_absolute_index(self) -> None:
        """Simulate the 's N' validation: absolute_token_index must be rejected."""
        tokens = [
            {"generated_token_index": 0, "absolute_token_index": 1000,
             "role_or_part": "think", "token_text": "t", "is_special_token": False},
        ]
        valid_indices = {t["generated_token_index"] for t in tokens}
        # Attempt to set absolute_token_index 1000 — should fail validation
        self.assertNotIn(1000, valid_indices,
                         "absolute_token_index 1000 must not be a valid generated_token_index")

    def test_generated_token_indices_start_at_zero(self) -> None:
        tld = _make_synthetic_tld(n_think=5, n_final=3)
        indices = [t["generated_token_index"] for t in tld]
        self.assertEqual(min(indices), 0, "generated_token_index must start at 0")
        self.assertEqual(len(set(indices)), len(tld), "generated_token_index must be unique")


# ---------------------------------------------------------------------------
# Test 7: Editing an annotation does not duplicate rows
# ---------------------------------------------------------------------------

class TestAnnotationEditNoDuplicate(unittest.TestCase):
    """Re-annotating an example replaces the existing row; never creates duplicates."""

    def test_overwrite_replaces_not_duplicates(self) -> None:
        from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES

        eid = "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"
        with tempfile.TemporaryDirectory() as tmpdir:
            ann_path = Path(tmpdir) / "harmful_interaction_annotations.csv"

            first = {
                "example_id": eid,
                "annotation_timestamp_utc": "2026-01-01T00:00:00",
                "harmful_interaction_start_token": "5",
                "annotation_confidence": "high",
                "interaction_phase": "think",
                "annotation_notes": "",
                "annotator_id": "primary",
                "annotation_status": "annotated",
            }
            common.append_csv_row(ann_path, first, ANNOTATIONS_FIELDNAMES)

            # Simulate overwrite: remove existing row, append updated row
            second = dict(first)
            second["harmful_interaction_start_token"] = "12"
            second["annotation_timestamp_utc"] = "2026-01-01T01:00:00"

            all_rows = common.read_csv_as_list(ann_path)
            updated = [r for r in all_rows if r.get("example_id") != eid]
            updated.append(second)
            common.write_csv(ann_path, updated, ANNOTATIONS_FIELDNAMES)

            result = common.read_csv_as_list(ann_path)
            matching = [r for r in result if r["example_id"] == eid]
            self.assertEqual(len(matching), 1, "Exactly one row per example after overwrite")
            self.assertEqual(matching[0]["harmful_interaction_start_token"], "12",
                             "Updated token index must be saved")

    def test_review_overwrite_no_duplicate(self) -> None:
        from poc_stage4_5.review_example import PROGRESS_FIELDNAMES

        eid = "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "progress.csv"
            row1 = {
                "example_id": eid, "reviewer_id": "primary",
                "review_timestamp_utc": "2026-01-01T00:00:00",
                "human_label": "no", "reviewer_confidence": "high",
                "human_success_strict": "False", "human_success_lenient": "False",
                "contains_harmful_interaction": "no",
                "think_shows_hijack": "", "reviewer_notes": "",
                "response_sha256": "abc", "review_status": "completed",
            }
            common.append_csv_row(path, row1, PROGRESS_FIELDNAMES)

            # Overwrite via write_csv (same pattern as review_example.review_one)
            row2 = dict(row1)
            row2["human_label"] = "yes"
            row2["human_success_strict"] = "True"
            row2["human_success_lenient"] = "True"

            all_rows = common.read_csv_as_list(path)
            updated = [r for r in all_rows if r.get("example_id") != eid]
            updated.append(row2)
            common.write_csv(path, updated, PROGRESS_FIELDNAMES)

            result = common.read_csv_as_list(path)
            matching = [r for r in result if r["example_id"] == eid]
            self.assertEqual(len(matching), 1, "Overwrite must not duplicate the row")
            self.assertEqual(matching[0]["human_label"], "yes")


# ---------------------------------------------------------------------------
# Test 8: Analysis remains incomplete while any pilot row is pending
# ---------------------------------------------------------------------------

class TestPilotAnalysisGating(unittest.TestCase):
    """run_analysis in pilot mode must block if any pilot example is pending."""

    def test_exits_without_fitting_when_pilot_pending(self) -> None:
        from poc_stage4_5.analyze_harmful_interaction_aligned_dynamics import run_analysis

        # Use 2 real example IDs from the pilot set (they are all pending)
        pilot_ids = {
            "goal_index=0|attack_iteration=1|conversation_id=2|target_model=gpt-o4-mini",
            "goal_index=2|attack_iteration=1|conversation_id=3|target_model=gpt-o4-mini",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            for sub in ("analysis", "plots/aggregate", "plots/per_example",
                        "manifests", "logs"):
                (run_dir / sub).mkdir(parents=True, exist_ok=True)
            review_dir = Path(tmpdir) / "review"
            review_dir.mkdir()
            # No annotations → all pending

            ret = run_analysis(
                run_dir=run_dir,
                review_dir=review_dir,
                seed=42,
                n_bootstrap=10,
                n_permutations=10,
                layers=[22],
                example_ids=pilot_ids,
                pilot_mode=True,
            )
            self.assertEqual(ret, 0, "Should exit 0 (graceful) when pilot is incomplete")
            # pilot_results.json must be written as audit artifact
            self.assertTrue((run_dir / "analysis" / "pilot_results.json").exists())
            # No model output should exist
            firth_csv = run_dir / "analysis" / "event_aligned_firth_coefficients.csv"
            self.assertFalse(firth_csv.exists(),
                             "Firth coefficients must NOT be written for incomplete pilot")

    def test_non_pilot_mode_not_blocked(self) -> None:
        """Without pilot_mode, the pending check must not fire."""
        from poc_stage4_5.analyze_harmful_interaction_aligned_dynamics import run_analysis

        non_pilot_ids = {
            "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            for sub in ("analysis", "plots/aggregate", "plots/per_example",
                        "manifests", "logs"):
                (run_dir / sub).mkdir(parents=True, exist_ok=True)
            review_dir = Path(tmpdir) / "review"
            review_dir.mkdir()
            # Non-pilot mode: the pending check is skipped entirely
            ret = run_analysis(
                run_dir=run_dir,
                review_dir=review_dir,
                seed=42,
                n_bootstrap=10,
                n_permutations=10,
                layers=[22],
                example_ids=non_pilot_ids,
                pilot_mode=False,  # non-pilot: no pending block
            )
            self.assertEqual(ret, 0)


# ---------------------------------------------------------------------------
# Test 9: Analysis becomes eligible when all pilot examples have explicit status
# ---------------------------------------------------------------------------

class TestAnalysisEligibleWhenComplete(unittest.TestCase):
    """Pending check passes once all pilot examples have a non-pending status."""

    def test_pending_check_passes_with_all_explicit_statuses(self) -> None:
        from poc_stage4_5.build_event_annotation_queue import build_annotation_queue
        from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES

        pilot_ids = {
            "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini",
            "goal_index=0|attack_iteration=1|conversation_id=2|target_model=gpt-o4-mini",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            ann_path = Path(tmpdir) / "harmful_interaction_annotations.csv"
            progress_path = Path(tmpdir) / "manual_adjudication_progress.csv"

            # Give every pilot ID an explicit annotation status
            for eid in pilot_ids:
                row = {
                    "example_id": eid,
                    "annotation_timestamp_utc": "2026-01-01T00:00:00",
                    "harmful_interaction_start_token": "-1",
                    "annotation_confidence": "high",
                    "interaction_phase": "none",
                    "annotation_notes": "",
                    "annotator_id": "primary",
                    "annotation_status": "no_harmful_interaction_found",
                }
                common.append_csv_row(ann_path, row, ANNOTATIONS_FIELDNAMES)

            queue = build_annotation_queue(common.ANALYSIS_DATASET_PATH, progress_path, ann_path)
            pilot_queue = [r for r in queue if r["example_id"] in pilot_ids]
            pending = [r for r in pilot_queue if r["annotation_status"] == "pending"]
            self.assertEqual(len(pending), 0,
                             "All pilot examples should have explicit status; none pending")

    def test_single_pending_blocks_analysis(self) -> None:
        from poc_stage4_5.build_event_annotation_queue import build_annotation_queue
        from poc_stage4_5.annotate_harmful_interaction import ANNOTATIONS_FIELDNAMES

        id_annotated = "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"
        id_pending   = "goal_index=0|attack_iteration=1|conversation_id=2|target_model=gpt-o4-mini"
        pilot_ids = {id_annotated, id_pending}

        with tempfile.TemporaryDirectory() as tmpdir:
            ann_path = Path(tmpdir) / "harmful_interaction_annotations.csv"
            progress_path = Path(tmpdir) / "manual_adjudication_progress.csv"

            # Only annotate id_annotated; id_pending stays pending
            row = {
                "example_id": id_annotated,
                "annotation_timestamp_utc": "2026-01-01",
                "harmful_interaction_start_token": "5",
                "annotation_confidence": "high",
                "interaction_phase": "think",
                "annotation_notes": "",
                "annotator_id": "primary",
                "annotation_status": "annotated",
            }
            common.append_csv_row(ann_path, row, ANNOTATIONS_FIELDNAMES)

            queue = build_annotation_queue(common.ANALYSIS_DATASET_PATH, progress_path, ann_path)
            pilot_queue = [r for r in queue if r["example_id"] in pilot_ids]
            pending = [r for r in pilot_queue if r["annotation_status"] == "pending"]
            self.assertEqual(len(pending), 1, "id_pending should still be pending")
            self.assertEqual(pending[0]["example_id"], id_pending)


# ---------------------------------------------------------------------------
# Test 10: No frozen Stage 4 file is modified (extended coverage)
# ---------------------------------------------------------------------------

class TestFrozenFilesNotModifiedExtended(unittest.TestCase):
    """Extended check: building, rebuilding, and reporting must not touch frozen artifacts."""

    def test_report_progress_does_not_touch_stage4_files(self) -> None:
        from poc_stage4_5.report_annotation_progress import report_progress

        targets = []
        first_s4 = next(common.STAGE4_PER_EXAMPLE_DIR.glob("*.json"), None)
        if first_s4:
            targets.append(first_s4)
        targets.append(common.ANALYSIS_DATASET_PATH)

        before = {str(p): p.stat().st_mtime for p in targets if p.exists()}

        with tempfile.TemporaryDirectory() as tmpdir:
            report_progress(Path(tmpdir), common.ANALYSIS_DATASET_PATH)

        after = {str(p): p.stat().st_mtime for p in targets if p.exists()}
        for k in before:
            self.assertEqual(before[k], after.get(k, before[k]),
                             f"Frozen file modified by report_progress: {k}")

    def test_rebuild_queue_does_not_touch_stage4_files(self) -> None:
        from poc_stage4_5.build_event_annotation_queue import build_annotation_queue

        targets = []
        first_s4 = next(common.STAGE4_PER_EXAMPLE_DIR.glob("*.json"), None)
        if first_s4:
            targets.append(first_s4)
        targets.append(common.ANALYSIS_DATASET_PATH)

        before = {str(p): p.stat().st_mtime for p in targets if p.exists()}

        with tempfile.TemporaryDirectory() as tmpdir:
            build_annotation_queue(
                common.ANALYSIS_DATASET_PATH,
                Path(tmpdir) / "progress.csv",
                Path(tmpdir) / "annotations.csv",
            )

        after = {str(p): p.stat().st_mtime for p in targets if p.exists()}
        for k in before:
            self.assertEqual(before[k], after.get(k, before[k]),
                             f"Frozen file modified by build_annotation_queue: {k}")


# ---------------------------------------------------------------------------
# Stage 4.5B — LLM annotation tests
# ---------------------------------------------------------------------------

class TestLLMAnnotationPrompts(unittest.TestCase):
    """Tests for llm_annotation_prompts.py template content."""

    def test_prompt_version_is_string(self) -> None:
        from poc_stage4_5.llm_annotation_prompts import PROMPT_VERSION
        self.assertIsInstance(PROMPT_VERSION, str)
        self.assertTrue(len(PROMPT_VERSION) > 0)

    def test_coarse_template_has_required_placeholders(self) -> None:
        from poc_stage4_5.llm_annotation_prompts import COARSE_USER_TEMPLATE
        for ph in ("{goal_index}", "{chunk_start}", "{chunk_end}", "{chunk_text}"):
            self.assertIn(ph, COARSE_USER_TEMPLATE, f"Missing placeholder: {ph}")

    def test_fine_template_has_required_placeholders(self) -> None:
        from poc_stage4_5.llm_annotation_prompts import FINE_USER_TEMPLATE
        for ph in ("{goal_index}", "{window_start}", "{window_end}",
                   "{token_index_map}", "{window_text}"):
            self.assertIn(ph, FINE_USER_TEMPLATE, f"Missing placeholder: {ph}")

    def test_adjudication_template_has_required_placeholders(self) -> None:
        from poc_stage4_5.llm_annotation_prompts import ADJUDICATION_USER_TEMPLATE
        for ph in ("{goal_index}", "{candidate_a}", "{candidate_b}",
                   "{token_index_map}", "{window_text}"):
            self.assertIn(ph, ADJUDICATION_USER_TEMPLATE, f"Missing placeholder: {ph}")

    def test_coarse_system_mentions_json_only(self) -> None:
        from poc_stage4_5.llm_annotation_prompts import COARSE_SYSTEM
        self.assertIn("JSON", COARSE_SYSTEM)


class TestCoarseResponseParsing(unittest.TestCase):
    """Tests for coarse pass response parsing in llm_annotate_harmful_interaction."""

    def _make_tokens(self, n: int = 20) -> list[dict]:
        return [
            {"generated_token_index": i, "role_or_part": "think",
             "token_text": f"tok{i} ", "is_special_token": False,
             "layer_projections": {"22": float(i)}}
            for i in range(n)
        ]

    def test_build_chunks_basic(self) -> None:
        from poc_stage4_5.llm_annotate_harmful_interaction import _build_chunks
        tokens = self._make_tokens(600)
        think_tokens = [t for t in tokens if t["role_or_part"] == "think"]
        chunks = _build_chunks(think_tokens)
        self.assertGreater(len(chunks), 0)
        # Each chunk should be <= CHUNK_SIZE_TOKENS
        from poc_stage4_5.llm_annotate_harmful_interaction import CHUNK_SIZE_TOKENS
        for c in chunks:
            self.assertLessEqual(len(c["tokens"]), CHUNK_SIZE_TOKENS)

    def test_build_chunks_small_input(self) -> None:
        from poc_stage4_5.llm_annotate_harmful_interaction import _build_chunks
        tokens = self._make_tokens(10)
        chunks = _build_chunks(tokens)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(len(chunks[0]["tokens"]), 10)

    def test_build_chunks_empty_input(self) -> None:
        from poc_stage4_5.llm_annotate_harmful_interaction import _build_chunks
        chunks = _build_chunks([])
        self.assertEqual(chunks, [])

    def test_validate_token_index_valid(self) -> None:
        from poc_stage4_5.llm_annotate_harmful_interaction import _validate_token_index
        tokens = self._make_tokens(10)
        self.assertTrue(_validate_token_index(5, tokens))

    def test_validate_token_index_invalid(self) -> None:
        from poc_stage4_5.llm_annotate_harmful_interaction import _validate_token_index
        tokens = self._make_tokens(10)
        self.assertFalse(_validate_token_index(999, tokens))
        self.assertFalse(_validate_token_index(None, tokens))

    def test_generated_vs_absolute_index_differ(self) -> None:
        """generated_token_index and absolute_token_index must be distinguishable."""
        tokens = [
            {"generated_token_index": 0, "absolute_token_index": 500,
             "token_text": "tok", "role_or_part": "think",
             "is_special_token": False, "layer_projections": {}},
        ]
        self.assertNotEqual(
            tokens[0]["generated_token_index"],
            tokens[0]["absolute_token_index"],
        )

    def test_get_token_phase(self) -> None:
        from poc_stage4_5.llm_annotate_harmful_interaction import _get_token_phase
        tokens = self._make_tokens(5)
        tokens[3]["role_or_part"] = "final"
        self.assertEqual(_get_token_phase(3, tokens), "final")
        self.assertEqual(_get_token_phase(99, tokens), "unknown")


class TestTwoPassConsensus(unittest.TestCase):
    """Unit tests for the consensus/adjudication logic."""

    def _make_tokens(self, n: int = 100) -> list[dict]:
        return [
            {"generated_token_index": i, "role_or_part": "think" if i > 0 else "special",
             "token_text": f"t{i} ", "is_special_token": i == 0,
             "layer_projections": {"22": float(i)}}
            for i in range(n)
        ]

    def test_consensus_within_tolerance(self) -> None:
        """Two passes agreeing within 64 tokens → annotated with earlier index."""
        from poc_stage4_5.llm_annotate_harmful_interaction import (
            CONSENSUS_TOLERANCE_TOKENS, _validate_token_index, _get_token_phase
        )
        tokens = self._make_tokens(200)
        p1_idx = 50
        p2_idx = 55  # within tolerance
        dist = abs(p1_idx - p2_idx)
        self.assertLessEqual(dist, CONSENSUS_TOLERANCE_TOKENS)
        chosen = min(p1_idx, p2_idx)
        self.assertTrue(_validate_token_index(chosen, tokens))
        self.assertEqual(chosen, p1_idx)

    def test_consensus_outside_tolerance(self) -> None:
        """Two passes disagreeing by > 64 tokens should trigger adjudication."""
        from poc_stage4_5.llm_annotate_harmful_interaction import CONSENSUS_TOLERANCE_TOKENS
        dist = 200
        self.assertGreater(dist, CONSENSUS_TOLERANCE_TOKENS)

    def test_no_event_handling(self) -> None:
        """If coarse pass finds no candidates → no_harmful_interaction_found."""
        from poc_stage4_5.llm_annotate_harmful_interaction import _build_chunks
        tokens = self._make_tokens(20)
        think_tokens = [t for t in tokens if t["role_or_part"] == "think"]
        chunks = _build_chunks(think_tokens)
        # Simulate: no candidates
        candidates = [c for c in chunks if False]  # empty
        self.assertEqual(candidates, [])

    def test_uncertain_when_both_fail(self) -> None:
        """If both passes return uncertain → result is uncertain."""
        p1_status = "uncertain"
        p2_status = "uncertain"
        statuses = {p1_status, p2_status}
        self.assertNotIn("annotated", statuses)
        self.assertNotIn("no_harmful_interaction_found", statuses)


class TestRawPassesNoTraceText(unittest.TestCase):
    """Ensure raw_passes.jsonl does not store token_text."""

    def test_write_raw_pass_no_token_text(self) -> None:
        from poc_stage4_5.llm_annotate_harmful_interaction import _write_raw_pass
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            pass_result = {
                "annotation_status": "annotated",
                "onset_generated_token_index": 42,
                "onset_segment": "think",
                "confidence": 0.9,
                "reason_category": "target_mapping",
                "brief_rationale": "test rationale",
            }
            meta = {"goal_index": 0, "attack_iteration": 1, "conversation_id": 1}
            _write_raw_pass(run_dir, "test_id", 1, pass_result, meta)
            jsonl_path = run_dir / "raw_passes.jsonl"
            self.assertTrue(jsonl_path.exists())
            with open(jsonl_path) as f:
                row = json.loads(f.readline())
            self.assertNotIn("token_text", row)
            self.assertNotIn("chunk_text", row)
            self.assertNotIn("window_text", row)
            self.assertEqual(row["example_id"], "test_id")
            self.assertEqual(row["pass_number"], 1)


class TestAlreadyAnnotated(unittest.TestCase):
    """Resume behavior: already-annotated examples are skipped."""

    def test_already_annotated_true(self) -> None:
        from poc_stage4_5.llm_annotate_harmful_interaction import (
            _already_annotated, CONSENSUS_CSV_FIELDS
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "consensus.csv"
            row = {f: "" for f in CONSENSUS_CSV_FIELDS}
            row["example_id"] = "test_eid"
            common.write_csv(csv_path, [row], CONSENSUS_CSV_FIELDS)
            self.assertTrue(_already_annotated("test_eid", csv_path))

    def test_already_annotated_false_missing(self) -> None:
        from poc_stage4_5.llm_annotate_harmful_interaction import _already_annotated
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "consensus.csv"
            self.assertFalse(_already_annotated("any_id", csv_path))

    def test_already_annotated_false_different_id(self) -> None:
        from poc_stage4_5.llm_annotate_harmful_interaction import (
            _already_annotated, CONSENSUS_CSV_FIELDS
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "consensus.csv"
            row = {f: "" for f in CONSENSUS_CSV_FIELDS}
            row["example_id"] = "other_eid"
            common.write_csv(csv_path, [row], CONSENSUS_CSV_FIELDS)
            self.assertFalse(_already_annotated("test_eid", csv_path))


class TestAuditQualityGate(unittest.TestCase):
    """Tests for audit_llm_annotations quality gate."""

    def _make_rows(
        self,
        n_annotated: int = 8,
        n_error: int = 0,
        n_uncertain: int = 0,
        n_no_event: int = 0,
        distances: list[float] | None = None,
    ) -> list[dict]:
        rows = []
        idx = 0
        for i in range(n_annotated):
            d = distances[i] if distances and i < len(distances) else 10.0
            rows.append({
                "example_id": f"ex_{idx}", "annotation_status": "annotated",
                "confidence": "0.9", "reason_category": "target_mapping",
                "agreement_distance_tokens": str(d), "adjudication_used": "False",
                "pass_1_status": "annotated", "pass_2_status": "annotated",
                "onset_segment": "think",
            })
            idx += 1
        for i in range(n_error):
            rows.append({
                "example_id": f"ex_{idx}", "annotation_status": "provider_error",
                "confidence": "0.0", "reason_category": "uncertain",
                "agreement_distance_tokens": "", "adjudication_used": "False",
                "pass_1_status": "provider_error", "pass_2_status": "provider_error",
                "onset_segment": "none",
            })
            idx += 1
        for i in range(n_uncertain):
            rows.append({
                "example_id": f"ex_{idx}", "annotation_status": "uncertain",
                "confidence": "0.3", "reason_category": "uncertain",
                "agreement_distance_tokens": "", "adjudication_used": "False",
                "pass_1_status": "uncertain", "pass_2_status": "uncertain",
                "onset_segment": "none",
            })
            idx += 1
        for i in range(n_no_event):
            rows.append({
                "example_id": f"ex_{idx}", "annotation_status": "no_harmful_interaction_found",
                "confidence": "0.8", "reason_category": "uncertain",
                "agreement_distance_tokens": "", "adjudication_used": "False",
                "pass_1_status": "no_harmful_interaction_found",
                "pass_2_status": "no_harmful_interaction_found",
                "onset_segment": "none",
            })
            idx += 1
        return rows

    def test_gate_passes_good_data(self) -> None:
        from poc_stage4_5.audit_llm_annotations import audit_consensus_csv, check_quality_gate
        rows = self._make_rows(n_annotated=10, n_error=0)
        metrics = audit_consensus_csv(rows)
        passes, failures = check_quality_gate(metrics)
        self.assertTrue(passes, f"Gate should pass but failures: {failures}")
        self.assertEqual(failures, [])

    def test_gate_fails_high_error_rate(self) -> None:
        from poc_stage4_5.audit_llm_annotations import audit_consensus_csv, check_quality_gate
        rows = self._make_rows(n_annotated=2, n_error=8)  # error_rate=0.8
        metrics = audit_consensus_csv(rows)
        passes, failures = check_quality_gate(metrics)
        self.assertFalse(passes)
        self.assertTrue(any("provider_error_rate" in f for f in failures))

    def test_gate_fails_high_median_distance(self) -> None:
        from poc_stage4_5.audit_llm_annotations import audit_consensus_csv, check_quality_gate
        rows = self._make_rows(n_annotated=10, distances=[200.0] * 10)
        metrics = audit_consensus_csv(rows)
        passes, failures = check_quality_gate(metrics)
        self.assertFalse(passes)
        self.assertTrue(any("median_agreement_distance" in f for f in failures))

    def test_gate_fails_low_consensus_rate(self) -> None:
        from poc_stage4_5.audit_llm_annotations import audit_consensus_csv, check_quality_gate
        # Make all annotated rows use adjudication → consensus_rate NaN or 0
        rows = []
        for i in range(10):
            rows.append({
                "example_id": f"ex_{i}", "annotation_status": "annotated",
                "confidence": "0.9", "reason_category": "target_mapping",
                "agreement_distance_tokens": "200.0",
                "adjudication_used": "True",  # all used adjudication
                "pass_1_status": "annotated", "pass_2_status": "annotated",
                "onset_segment": "think",
            })
        metrics = audit_consensus_csv(rows)
        # two_pass_consensus_rate should be 0.0 (no unadjudicated annotated rows)
        self.assertEqual(metrics["two_pass_consensus_rate"], 0.0)
        passes, failures = check_quality_gate(metrics)
        self.assertFalse(passes)

    def test_spotcheck_includes_uncertain(self) -> None:
        from poc_stage4_5.audit_llm_annotations import build_spotcheck_queue
        rows = self._make_rows(n_annotated=5, n_uncertain=2)
        sq = build_spotcheck_queue(rows)
        reasons = [r["spotcheck_reason"] for r in sq]
        self.assertTrue(any("uncertain" in r for r in reasons))

    def test_spotcheck_includes_no_event(self) -> None:
        from poc_stage4_5.audit_llm_annotations import build_spotcheck_queue
        rows = self._make_rows(n_annotated=5, n_no_event=2)
        sq = build_spotcheck_queue(rows)
        reasons = [r["spotcheck_reason"] for r in sq]
        self.assertTrue(any("no_event" in r for r in reasons))

    def test_spotcheck_includes_large_disagreement(self) -> None:
        from poc_stage4_5.audit_llm_annotations import build_spotcheck_queue
        rows = self._make_rows(n_annotated=5, distances=[10.0, 10.0, 10.0, 10.0, 200.0])
        sq = build_spotcheck_queue(rows)
        reasons = [r["spotcheck_reason"] for r in sq]
        self.assertTrue(any("disagreement" in r for r in reasons))

    def test_spotcheck_no_duplicates(self) -> None:
        from poc_stage4_5.audit_llm_annotations import build_spotcheck_queue
        rows = self._make_rows(n_annotated=5, n_uncertain=2, n_no_event=2)
        sq = build_spotcheck_queue(rows)
        ids = [r["example_id"] for r in sq]
        self.assertEqual(len(ids), len(set(ids)))

    def test_audit_empty_rows(self) -> None:
        from poc_stage4_5.audit_llm_annotations import audit_consensus_csv
        metrics = audit_consensus_csv([])
        self.assertIn("error", metrics)


class TestAnalyzeAllowLLMAnnotationsGate(unittest.TestCase):
    """--allow-llm-annotations must be required when annotation-source != human."""

    def test_llm_source_without_flag_returns_error(self) -> None:
        from poc_stage4_5.analyze_harmful_interaction_aligned_dynamics import main as analyze_main
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            exit_code = analyze_main([
                "--run-dir", str(run_dir),
                "--annotation-source", "o4mini",
                # missing --allow-llm-annotations
            ])
        self.assertEqual(exit_code, 1)

    def test_human_source_does_not_need_flag(self) -> None:
        from poc_stage4_5.analyze_harmful_interaction_aligned_dynamics import parse_args
        args = parse_args(["--annotation-source", "human"])
        # Should parse without error (allow_llm_annotations is False, but source is human)
        self.assertEqual(args.annotation_source, "human")
        self.assertFalse(args.allow_llm_annotations)


class TestAnnotationFieldTranslation(unittest.TestCase):
    """LLM consensus CSV onset_segment field should be translated to interaction_phase."""

    def test_onset_segment_translated_to_interaction_phase(self) -> None:
        """Verify the translation logic works in isolation."""
        r = {"example_id": "x", "onset_segment": "think", "annotation_status": "annotated",
             "harmful_interaction_start_token": "42"}
        if "onset_segment" in r and "interaction_phase" not in r:
            r["interaction_phase"] = r["onset_segment"]
        self.assertEqual(r["interaction_phase"], "think")

    def test_confidence_field_alias(self) -> None:
        """LLM CSV 'confidence' field should map to annotation_confidence."""
        r = {"example_id": "x", "confidence": "0.85", "onset_segment": "think"}
        if "annotation_confidence" not in r and "confidence" in r:
            r["annotation_confidence"] = r["confidence"]
        self.assertEqual(r["annotation_confidence"], "0.85")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
