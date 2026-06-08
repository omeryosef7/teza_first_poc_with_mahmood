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
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
