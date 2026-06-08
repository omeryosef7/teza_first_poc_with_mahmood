"""
Shared constants, path helpers, and loading utilities for Stage 4.5.

Re-exports key utilities from poc_stage4 to give Stage 4.5 scripts a single
import point without duplicating frozen code.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Re-exports from poc_stage4 (do not copy implementation here)
# ---------------------------------------------------------------------------

from poc_stage4.run_state import (  # noqa: F401
    atomic_write_json,
    append_jsonl,
    read_jsonl_rows,
    log_progress,
)
from poc_stage4.schemas import (  # noqa: F401
    utc_now,
    make_json_safe,
    write_json,
    read_json,
)
from poc_stage4.fit_confound_models import (  # noqa: F401
    firth_fit,
    fit_model,
    loo_predict,
    compute_metrics,
    permutation_test_projection,
)
from poc_stage4.analyze_fixed_windows import (  # noqa: F401
    hedges_g,
    bootstrap_ci_mean_diff,
    permutation_test_mean_diff,
    compute_group_stats,
    window_stats,
    extract_think_projections,
)

# ---------------------------------------------------------------------------
# Canonical path constants
# ---------------------------------------------------------------------------

REPO_ROOT: Path = Path(__file__).resolve().parent.parent

STAGE4_RUN_DIR: Path = (
    REPO_ROOT / "outputs" / "stage4" / "token_dynamics" / "full_20260604_101929"
)
STAGE4_PER_EXAMPLE_DIR: Path = STAGE4_RUN_DIR / "per_example"
STAGE4_ANALYSIS_DIR: Path = STAGE4_RUN_DIR / "analysis"

STAGE6_TRACES_DIR: Path = REPO_ROOT / "outputs" / "stage6" / "all_traces_full"

ANALYSIS_DATASET_PATH: Path = STAGE4_ANALYSIS_DIR / "analysis_dataset.csv"

DEFAULT_REVIEW_DIR: Path = REPO_ROOT / "review"
DEFAULT_OUTPUT_BASE: Path = (
    REPO_ROOT / "outputs" / "stage4_5" / "harmful_interaction_alignment"
)

# ---------------------------------------------------------------------------
# Human label taxonomy
# ---------------------------------------------------------------------------

HUMAN_LABELS: list[str] = [
    "full_refusal",
    "partial_refusal_with_unsafe_leakage",
    "irrelevant_or_nonresponsive",
    "superficial_harmful_mention",
    "substantive_compliance",
    "highly_actionable_compliance",
    "truncated_or_invalid",
    "uncertain",
]

STRICT_SUCCESS_LABELS: frozenset[str] = frozenset(
    {"substantive_compliance", "highly_actionable_compliance"}
)
LENIENT_SUCCESS_LABELS: frozenset[str] = frozenset(
    {
        "partial_refusal_with_unsafe_leakage",
        "substantive_compliance",
        "highly_actionable_compliance",
    }
)

# Annotation queue status values
ANNOTATION_STATUSES: list[str] = [
    "pending",
    "annotated",
    "no_harmful_interaction_found",
    "not_separable",
    "right_censored",
    "uncertain",
]

# Layers used in this sprint
PRIMARY_LAYER: int = 22
SELECTED_LAYERS: list[int] = [13, 16, 22, 26, 30, 38, 39]
EXPLORATORY_LAYERS: frozenset[int] = frozenset({13, 16, 38})
ALL_LAYERS: list[int] = list(range(40))

# ---------------------------------------------------------------------------
# Filename conversion helpers
# ---------------------------------------------------------------------------

# Example ID format:
#   "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"
# Stage 4 per-example filename stem:
#   "goal_index_0_attack_iteration_1_conversation_id_1_target_model_gpt-o4-mini"
# Stage 6 trace filename:
#   "qwen3_14b_trace_goal_index_0_attack_iteration_1_conversation_id_1_target_model_gpt-o4-mini.json"


def example_id_to_s4_filename(example_id: str) -> str:
    """Convert example_id to Stage 4 per-example filename (without .json extension)."""
    return (
        example_id
        .replace("goal_index=", "goal_index_")
        .replace("|attack_iteration=", "_attack_iteration_")
        .replace("|conversation_id=", "_conversation_id_")
        .replace("|target_model=", "_target_model_")
    )


def example_id_to_s6_filename(example_id: str) -> str:
    """Convert example_id to Stage 6 trace filename (without .json extension)."""
    return "qwen3_14b_trace_" + example_id_to_s4_filename(example_id)


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_analysis_dataset(path: Path | str | None = None) -> list[dict[str, Any]]:
    """Load analysis_dataset.csv and return typed list of dicts."""
    if path is None:
        path = ANALYSIS_DATASET_PATH
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["sr_success"] = r["sr_success"] == "True"
        r["judge_success"] = r["judge_success"] == "True"
        r["right_censored"] = r["right_censored"] == "True"
        r["usable_for_think_analysis"] = r["usable_for_think_analysis"] == "True"
        r["strongreject_score"] = float(r["strongreject_score"])
        r["think_token_count"] = int(r["think_token_count"])
        r["goal_index"] = int(r["goal_index"])
        r["attack_iteration"] = int(r["attack_iteration"])
        r["conversation_id"] = int(r["conversation_id"])
    return rows


def load_stage4_per_example(
    example_id_or_path: str | Path,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Load a Stage 4 per-example JSON artifact.

    Accepts an absolute path or an example_id string.  When given an
    example_id, resolves against base_dir (defaults to STAGE4_PER_EXAMPLE_DIR).
    """
    p = Path(example_id_or_path)
    if p.is_absolute() and p.exists():
        path = p
    else:
        bd = base_dir or STAGE4_PER_EXAMPLE_DIR
        stem = example_id_to_s4_filename(str(example_id_or_path))
        path = Path(bd) / f"{stem}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_stage6_trace(
    example_id_or_path: str | Path,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Load a Stage 6 full trace JSON artifact."""
    p = Path(example_id_or_path)
    if p.is_absolute() and p.exists():
        path = p
    else:
        bd = base_dir or STAGE6_TRACES_DIR
        stem = example_id_to_s6_filename(str(example_id_or_path))
        path = Path(bd) / f"{stem}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Token-level helpers
# ---------------------------------------------------------------------------

def get_think_tokens(token_level_data: list[dict]) -> list[dict]:
    """Return only tokens with role_or_part == 'think'."""
    return [t for t in token_level_data if t.get("role_or_part") == "think"]


def get_all_generated_tokens(token_level_data: list[dict]) -> list[dict]:
    """Return all generated tokens (excludes nothing — think, final, special)."""
    return list(token_level_data)


def get_projections_at_layer(
    token_level_data: list[dict],
    layer: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (generated_token_indices, projections) for the given layer.

    Skips tokens where the projection is None or non-finite.
    """
    indices: list[int] = []
    projections: list[float] = []
    key = str(layer)
    for tok in token_level_data:
        val = tok["layer_projections"].get(key)
        if val is not None and math.isfinite(val):
            indices.append(tok["generated_token_index"])
            projections.append(val)
    return np.array(indices, dtype=np.int64), np.array(projections, dtype=np.float64)


def rank_biserial(
    a: np.ndarray,
    b: np.ndarray,
    u_statistic: float,
) -> float:
    """Rank-biserial correlation from Mann-Whitney U statistic."""
    n_a, n_b = len(a), len(b)
    if n_a == 0 or n_b == 0:
        return float("nan")
    return 1.0 - 2.0 * u_statistic / (n_a * n_b)


# ---------------------------------------------------------------------------
# CSV utilities
# ---------------------------------------------------------------------------

def safe_float(v: Any) -> float:
    """Return float or NaN for None / non-finite strings."""
    if v is None:
        return float("nan")
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def write_csv(path: Path | str, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    """Write rows as CSV with an explicit fieldnames order."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def append_csv_row(path: Path | str, row: dict[str, Any], fieldnames: list[str]) -> None:
    """Append one row to a CSV; writes header if file does not exist."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerow(row)


def read_csv_as_list(path: Path | str) -> list[dict[str, str]]:
    """Read a CSV and return list of dicts (all string values)."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
