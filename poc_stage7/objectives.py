from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from poc_stage5.data_loading import iter_jsonl, validate_jsonl_path


OBJECTIVE_FIELDS = (
    "objective_judge_only",
    "objective_strongreject_only",
    "objective_refusal_suppression",
    "objective_refusal_preservation",
    "objective_hybrid",
)

REGION_FIELDS = ("final_token", "last_8", "last_32")


@dataclass(frozen=True)
class ObjectiveParameters:
    lambda_refusal: float = 1.0
    lambda_preserve: float = 1.0
    alpha: float = 1.0
    beta: float = 1.0
    delta: float = 1.0


@dataclass(frozen=True)
class Stage7Config:
    stage5_jsonl: Path
    stage6_jsonl: Path | None
    output_jsonl: Path
    summary_json: Path
    regions: tuple[str, ...]
    hidden_state_index: int
    objective_parameters: ObjectiveParameters
    overwrite: bool


def parse_regions(value: str) -> tuple[str, ...]:
    regions = [part.strip() for part in value.split(",") if part.strip()]
    if not regions:
        raise ValueError("regions must contain at least one token region.")
    invalid = [region for region in regions if region not in REGION_FIELDS]
    if invalid:
        raise ValueError(f"Unsupported region(s): {invalid}. Supported regions: {list(REGION_FIELDS)}")
    return tuple(regions)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            return str(value)
    return value


def _tmp_path(path: Path) -> Path:
    return path.with_name(path.name + ".tmp")


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(path)
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    tmp_path.replace(path)


def _write_jsonl_row(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(_json_safe(row), ensure_ascii=False) + "\n")


def _coerce_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return None


def _mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return statistics.fmean(items) if items else None


def _std(values: Iterable[float]) -> float | None:
    items = list(values)
    if len(items) < 2:
        return None
    return statistics.stdev(items)


def _median(values: Iterable[float]) -> float | None:
    items = list(values)
    return statistics.median(items) if items else None


def _pearson(xs: Iterable[float], ys: Iterable[float]) -> float | None:
    x_values = list(xs)
    y_values = list(ys)
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return None
    x_mean = statistics.fmean(x_values)
    y_mean = statistics.fmean(y_values)
    x_diffs = [value - x_mean for value in x_values]
    y_diffs = [value - y_mean for value in y_values]
    denominator = math.sqrt(sum(diff * diff for diff in x_diffs) * sum(diff * diff for diff in y_diffs))
    if denominator == 0:
        return None
    return sum(x * y for x, y in zip(x_diffs, y_diffs)) / denominator


def _check_outputs(config: Stage7Config) -> None:
    paths = [config.output_jsonl, config.summary_json]
    existing = [path for path in paths if path.exists()]
    if existing and not config.overwrite:
        formatted = "\n".join(f"- {path}" for path in existing)
        raise FileExistsError(f"Output file(s) already exist. Use --overwrite to replace them:\n{formatted}")


def validate_stage5_row(row: dict[str, Any], *, hidden_state_index: int, regions: tuple[str, ...]) -> bool:
    if row.get("sequence_type") != "prompt_only":
        return False
    if _coerce_int(row.get("hidden_state_index")) != hidden_state_index:
        return False
    region = row.get("region") or row.get("token_region")
    if region not in regions:
        return False
    return _coerce_float(row.get("projection_mean")) is not None


def _coerce_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_judge_score(value: Any) -> float | None:
    raw = _coerce_float(value)
    if raw is None:
        return None
    if 0.0 <= raw <= 1.0:
        return raw
    if 1.0 <= raw <= 10.0:
        return (raw - 1.0) / 9.0
    return None


def normalize_strongreject_score(value: Any) -> float | None:
    raw = _coerce_float(value)
    if raw is None:
        return None
    if 0.0 <= raw <= 1.0:
        return raw
    if 1.0 <= raw <= 10.0:
        return raw / 10.0
    return None


def build_behavioral_score_fields(row: dict[str, Any]) -> dict[str, Any]:
    judge_raw = _coerce_float(row.get("judge_score"))
    strongreject_raw = _coerce_float(row.get("strongreject_score"))
    judge_normalized = normalize_judge_score(judge_raw)
    strongreject_normalized = normalize_strongreject_score(strongreject_raw)

    if judge_normalized is not None:
        source = "judge"
        raw_value = judge_raw
        normalized_value = judge_normalized
    elif strongreject_normalized is not None:
        source = "strongreject"
        raw_value = strongreject_raw
        normalized_value = strongreject_normalized
    else:
        source = None
        raw_value = None
        normalized_value = None

    return {
        "judge_score": judge_raw,
        "judge_score_raw": judge_raw,
        "judge_score_normalized": judge_normalized,
        "strongreject_score": strongreject_raw,
        "strongreject_score_raw": strongreject_raw,
        "strongreject_score_normalized": strongreject_normalized,
        "behavioral_score_raw": raw_value,
        "behavioral_score_normalized": normalized_value,
        "behavioral_score": normalized_value,
        "behavioral_score_source": source,
        "behavioral_score_scale": "0-1 normalized",
    }


def compute_baseline_rows(rows: list[dict[str, Any]], *, hidden_state_index: int, regions: tuple[str, ...]) -> dict[tuple[Any, ...], dict[str, Any]]:
    grouped_all: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    grouped_failed: dict[tuple[Any, ...], list[float]] = defaultdict(list)

    for row in rows:
        region = row.get("region") or row.get("token_region")
        key = (row.get("condition"), region, hidden_state_index)
        projection = _coerce_float(row.get("projection_mean"))
        if projection is None or region not in regions:
            continue
        grouped_all[key].append(projection)
        if _coerce_bool(row.get("is_success")) is False:
            grouped_failed[key].append(projection)

    baselines: dict[tuple[Any, ...], dict[str, Any]] = {}
    for key, all_values in grouped_all.items():
        failed_values = grouped_failed.get(key, [])
        if failed_values:
            baselines[key] = {
                "baseline_projection": _mean(failed_values),
                "baseline_source": "failed_mean",
                "failed_row_count": len(failed_values),
                "group_row_count": len(all_values),
            }
        else:
            baselines[key] = {
                "baseline_projection": _mean(all_values),
                "baseline_source": "group_mean",
                "failed_row_count": 0,
                "group_row_count": len(all_values),
            }
    return baselines


def compute_objectives(
    *,
    behavioral_score: float | None,
    strongreject_score: float | None,
    projection_value: float | None,
    baseline_projection: float | None,
    params: ObjectiveParameters,
) -> dict[str, float | None]:
    if behavioral_score is None or projection_value is None:
        return {field: None for field in OBJECTIVE_FIELDS}
    baseline_delta = None if baseline_projection is None else abs(projection_value - baseline_projection)
    return {
        "objective_judge_only": behavioral_score,
        "objective_strongreject_only": strongreject_score,
        "objective_refusal_suppression": behavioral_score - params.lambda_refusal * projection_value,
        "objective_refusal_preservation": (
            None if baseline_delta is None else behavioral_score - params.lambda_preserve * baseline_delta
        ),
        "objective_hybrid": (
            None
            if baseline_delta is None
            else params.alpha * behavioral_score - params.beta * projection_value - params.delta * baseline_delta
        ),
    }


def build_objective_row(
    row: dict[str, Any],
    *,
    baseline_info: dict[str, Any],
    params: ObjectiveParameters,
) -> dict[str, Any]:
    projection_value = _coerce_float(row.get("projection_mean"))
    scores = build_behavioral_score_fields(row)
    behavioral_score = scores["behavioral_score_normalized"]
    objectives = compute_objectives(
        behavioral_score=behavioral_score,
        strongreject_score=scores["strongreject_score_normalized"],
        projection_value=projection_value,
        baseline_projection=baseline_info.get("baseline_projection"),
        params=params,
    )

    return {
        "stage": 7,
        "example_id": row.get("example_id"),
        "goal_index": _coerce_int(row.get("goal_index")),
        "condition": row.get("condition"),
        "region": row.get("region") or row.get("token_region"),
        "hidden_state_index": _coerce_int(row.get("hidden_state_index")),
        "is_success": _coerce_bool(row.get("is_success")),
        "projection_value": projection_value,
        "baseline_projection": baseline_info.get("baseline_projection"),
        "baseline_source": baseline_info.get("baseline_source"),
        **scores,
        **asdict(params),
        **objectives,
    }


def summarize_objective_rows(
    rows: list[dict[str, Any]],
    *,
    stage5_jsonl: Path | None = None,
    stage6_jsonl: Path | None = None,
    regions: tuple[str, ...],
    hidden_state_index: int,
    params: ObjectiveParameters,
    baseline_fallback_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    regions = tuple(regions)
    numeric_rows = [row for row in rows if _coerce_float(row.get("projection_value")) is not None]

    def objective_values(name: str, subset: list[dict[str, Any]] | None = None) -> list[float]:
        selected = numeric_rows if subset is None else subset
        values = []
        for row in selected:
            value = _coerce_float(row.get(name))
            if value is not None:
                values.append(value)
        return values

    by_success = {True: [], False: [], None: []}
    for row in numeric_rows:
        by_success[_coerce_bool(row.get("is_success"))].append(row)

    objective_means = {name: _mean(objective_values(name)) for name in OBJECTIVE_FIELDS}
    objective_means_by_success = {
        str(success): {name: _mean(objective_values(name, subset=rows_subset)) for name in OBJECTIVE_FIELDS}
        for success, rows_subset in by_success.items()
        if rows_subset
    }
    objective_success_minus_failure = {}
    for name in OBJECTIVE_FIELDS:
        success_mean = _mean(objective_values(name, by_success[True]))
        failure_mean = _mean(objective_values(name, by_success[False]))
        objective_success_minus_failure[name] = (
            success_mean - failure_mean if success_mean is not None and failure_mean is not None else None
        )

    region_summaries: list[dict[str, Any]] = []
    for region in regions:
        region_rows = [row for row in numeric_rows if row.get("region") == region]
        success_rows = [row for row in region_rows if _coerce_bool(row.get("is_success")) is True]
        failure_rows = [row for row in region_rows if _coerce_bool(row.get("is_success")) is False]
        summary = {
            "region": region,
            "count": len(region_rows),
            "success_count": len(success_rows),
            "failure_count": len(failure_rows),
            "mean_projection_value": _mean(_coerce_float(row.get("projection_value")) for row in region_rows if _coerce_float(row.get("projection_value")) is not None),
            "mean_behavioral_score": _mean(_coerce_float(row.get("behavioral_score")) for row in region_rows if _coerce_float(row.get("behavioral_score")) is not None),
            "baseline_failed_mean_count": sum(1 for row in region_rows if row.get("baseline_source") == "failed_mean"),
            "baseline_group_mean_count": sum(1 for row in region_rows if row.get("baseline_source") == "group_mean"),
            "objective_means": {name: _mean(objective_values(name, subset=region_rows)) for name in OBJECTIVE_FIELDS},
            "objective_means_success": {name: _mean(objective_values(name, subset=success_rows)) for name in OBJECTIVE_FIELDS},
            "objective_means_failure": {name: _mean(objective_values(name, subset=failure_rows)) for name in OBJECTIVE_FIELDS},
            "objective_success_minus_failure": {
                name: (
                    _mean(objective_values(name, subset=success_rows))
                    - _mean(objective_values(name, subset=failure_rows))
                    if _mean(objective_values(name, subset=success_rows)) is not None
                    and _mean(objective_values(name, subset=failure_rows)) is not None
                    else None
                )
                for name in OBJECTIVE_FIELDS
            },
        }
        region_summaries.append(summary)

    projection_behavioral_pairs = [
        (
            _coerce_float(row.get("projection_value")),
            _coerce_float(row.get("behavioral_score")),
        )
        for row in numeric_rows
    ]
    projection_behavioral_pairs = [pair for pair in projection_behavioral_pairs if pair[0] is not None and pair[1] is not None]

    diagnostics = {
        "projection_behavioral_pearson": _pearson(
            [pair[0] for pair in projection_behavioral_pairs],
            [pair[1] for pair in projection_behavioral_pairs],
        ),
        "objective_success_pearson": {
            name: _pearson(
                [
                    1.0 if success_value else 0.0
                    for success_value, objective_value in (
                        (
                            _coerce_bool(row.get("is_success")),
                            _coerce_float(row.get(name)),
                        )
                        for row in numeric_rows
                    )
                    if success_value is not None and objective_value is not None
                ],
                [
                    objective_value
                    for success_value, objective_value in (
                        (
                            _coerce_bool(row.get("is_success")),
                            _coerce_float(row.get(name)),
                        )
                        for row in numeric_rows
                    )
                    if success_value is not None and objective_value is not None
                ],
            )
            for name in OBJECTIVE_FIELDS
        },
        "region_ranking_by_hybrid": [
            {"region": item["region"], "mean_objective_hybrid": item["objective_means"]["objective_hybrid"]}
            for item in sorted(
                region_summaries,
                key=lambda item: (
                    item["objective_means"].get("objective_hybrid") is None,
                    -(item["objective_means"].get("objective_hybrid") or 0.0),
                    item["region"],
                ),
            )
        ],
    }

    return {
        "stage": 7,
        "summary_type": "objective_comparison",
        "rows_read_stage5": None,
        "rows_read_stage6": None if stage6_jsonl is None else 0,
        "objective_rows_written": len(numeric_rows),
        "regions": list(regions),
        "hidden_state_index": hidden_state_index,
        "objective_parameters": _json_safe(asdict(params)),
        "behavioral_score_scale": {
            "judge_score_raw_scale": "1-10 or 0-1 depending on source row",
            "judge_score_normalization": "normalize to 0-1 using (score - 1) / 9 for 1-10 rows; passthrough for 0-1 rows",
            "strongreject_score_raw_scale": "0-1 in current outputs; passthrough when already 0-1, divide by 10 if 0-10 rows appear",
            "behavioral_score_definition": "use normalized judge score when available, otherwise normalized strongreject score",
        },
        "success_count": len(by_success[True]),
        "failure_count": len(by_success[False]),
        "unknown_success_count": len(by_success[None]),
        "baseline_fallback_counts": baseline_fallback_counts or {},
        "overall_means": {
            "projection_value": _mean(value for value in objective_values("projection_value")),
            "behavioral_score": _mean(value for value in objective_values("behavioral_score")),
            **objective_means,
        },
        "overall_means_by_success": objective_means_by_success,
        "success_minus_failure": objective_success_minus_failure,
        "region_summaries": region_summaries,
        "diagnostics": diagnostics,
        "stage5_jsonl": str(stage5_jsonl) if stage5_jsonl is not None else None,
        "stage6_jsonl": str(stage6_jsonl) if stage6_jsonl is not None else None,
        "output_jsonl": None,
        "summary_json": None,
        "generated_utc": _utc_now(),
    }


def load_stage5_rows(config: Stage7Config) -> list[dict[str, Any]]:
    return [row for row in iter_jsonl(config.stage5_jsonl)]


def load_stage6_row_count(stage6_jsonl: Path | None) -> int | None:
    if stage6_jsonl is None:
        return None
    return sum(1 for _row in iter_jsonl(stage6_jsonl))


def run_stage7_comparison(config: Stage7Config) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    _check_outputs(config)
    stage5_rows = load_stage5_rows(config)
    filtered_rows = [
        row
        for row in stage5_rows
        if validate_stage5_row(row, hidden_state_index=config.hidden_state_index, regions=config.regions)
    ]
    baseline_map = compute_baseline_rows(
        filtered_rows,
        hidden_state_index=config.hidden_state_index,
        regions=config.regions,
    )
    output_rows: list[dict[str, Any]] = []
    for row in filtered_rows:
        region = row.get("region") or row.get("token_region")
        baseline_info = baseline_map.get(
            (row.get("condition"), region, config.hidden_state_index),
            {
                "baseline_projection": _coerce_float(row.get("projection_mean")),
                "baseline_source": "row_mean_fallback",
                "failed_row_count": 0,
                "group_row_count": 1,
            },
        )
        output_rows.append(build_objective_row(row, baseline_info=baseline_info, params=config.objective_parameters))

    baseline_fallback_counts = {"failed_mean": 0, "group_mean": 0, "row_mean_fallback": 0}
    for row in output_rows:
        source = row.get("baseline_source")
        if source in baseline_fallback_counts:
            baseline_fallback_counts[source] += 1

    stage6_rows_read = load_stage6_row_count(config.stage6_jsonl)
    summary = summarize_objective_rows(
        output_rows,
        stage5_jsonl=config.stage5_jsonl,
        stage6_jsonl=config.stage6_jsonl,
        regions=config.regions,
        hidden_state_index=config.hidden_state_index,
        params=config.objective_parameters,
        baseline_fallback_counts=baseline_fallback_counts,
    )
    summary["rows_read_stage5"] = len(stage5_rows)
    summary["rows_read_stage6"] = stage6_rows_read
    summary["objective_rows_written"] = len(output_rows)
    summary["filtered_stage5_rows"] = len(filtered_rows)
    summary["filtered_stage5_row_ids"] = [row.get("example_id") for row in filtered_rows[:3]]
    return output_rows, summary


def write_stage7_outputs(output_rows: list[dict[str, Any]], config: Stage7Config, summary: dict[str, Any]) -> None:
    config.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with config.output_jsonl.with_name(config.output_jsonl.name + ".tmp").open("w", encoding="utf-8") as handle:
        for row in output_rows:
            _write_jsonl_row(handle, row)
    config.output_jsonl.with_name(config.output_jsonl.name + ".tmp").replace(config.output_jsonl)
    summary["output_jsonl"] = str(config.output_jsonl)
    summary["summary_json"] = str(config.summary_json)
    _atomic_write_json(config.summary_json, summary)
