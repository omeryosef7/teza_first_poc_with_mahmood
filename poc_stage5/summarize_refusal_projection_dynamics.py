from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from poc_stage5.data_loading import iter_jsonl, validate_jsonl_path


GROUP_FIELDS = ("condition", "sequence_type", "hidden_state_index", "region")
SUMMARY_FIELDS = (
    "count",
    "projection_mean_mean",
    "projection_mean_std",
    "projection_mean_median",
    "projection_final_mean",
    "projection_final_std",
    "projection_abs_mean_mean",
    "success_rate",
    "mean_strongreject_score",
    "mean_judge_score",
)
CSV_FIELDS = (*GROUP_FIELDS, *SUMMARY_FIELDS, "success_projection_mean", "failure_projection_mean", "success_minus_failure_projection_mean")


@dataclass(frozen=True)
class SummarizeConfig:
    input_jsonl: Path
    output_json: Path
    output_csv: Path | None
    overwrite: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate Stage 5 refusal-projection JSONL rows into compact summary files."
    )
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def validate_config(args: argparse.Namespace) -> SummarizeConfig:
    input_jsonl = validate_jsonl_path(args.input_jsonl)
    return SummarizeConfig(
        input_jsonl=input_jsonl,
        output_json=Path(args.output_json),
        output_csv=Path(args.output_csv) if args.output_csv else None,
        overwrite=bool(args.overwrite),
    )


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


def _check_outputs(config: SummarizeConfig) -> None:
    paths = [config.output_json]
    if config.output_csv is not None:
        paths.append(config.output_csv)
    existing = [path for path in paths if path.exists()]
    if existing and not config.overwrite:
        formatted = "\n".join(f"- {path}" for path in existing)
        raise FileExistsError(f"Output file(s) already exist. Use --overwrite to replace them:\n{formatted}")


def _tmp_path(path: Path) -> Path:
    return path.with_name(path.name + ".tmp")


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(path)
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    tmp_path.replace(path)


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
    if isinstance(value, (int, float)) and not isinstance(value, bool):
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


def _group_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row.get(field) for field in GROUP_FIELDS)


def _display_group(key: tuple[Any, ...]) -> dict[str, Any]:
    return {field: value for field, value in zip(GROUP_FIELDS, key)}


def _aggregate_group(key: tuple[Any, ...], rows: list[dict[str, Any]]) -> dict[str, Any]:
    projection_means = [value for row in rows if (value := _coerce_float(row.get("projection_mean"))) is not None]
    projection_finals = [value for row in rows if (value := _coerce_float(row.get("projection_final"))) is not None]
    projection_abs_means = [value for row in rows if (value := _coerce_float(row.get("projection_abs_mean"))) is not None]
    strongreject_scores = [value for row in rows if (value := _coerce_float(row.get("strongreject_score"))) is not None]
    judge_scores = [value for row in rows if (value := _coerce_float(row.get("judge_score"))) is not None]
    success_values = [value for row in rows if (value := _coerce_bool(row.get("is_success"))) is not None]

    successful_means = [
        projection
        for row in rows
        if _coerce_bool(row.get("is_success")) is True
        if (projection := _coerce_float(row.get("projection_mean"))) is not None
    ]
    failed_means = [
        projection
        for row in rows
        if _coerce_bool(row.get("is_success")) is False
        if (projection := _coerce_float(row.get("projection_mean"))) is not None
    ]
    success_projection_mean = _mean(successful_means)
    failure_projection_mean = _mean(failed_means)

    return {
        **_display_group(key),
        "count": len(rows),
        "projection_mean_mean": _mean(projection_means),
        "projection_mean_std": _std(projection_means),
        "projection_mean_median": _median(projection_means),
        "projection_final_mean": _mean(projection_finals),
        "projection_final_std": _std(projection_finals),
        "projection_abs_mean_mean": _mean(projection_abs_means),
        "success_rate": _mean([1.0 if value else 0.0 for value in success_values]),
        "mean_strongreject_score": _mean(strongreject_scores),
        "mean_judge_score": _mean(judge_scores),
        "success_count": len(successful_means),
        "failure_count": len(failed_means),
        "success_projection_mean": success_projection_mean,
        "failure_projection_mean": failure_projection_mean,
        "success_minus_failure_projection_mean": (
            success_projection_mean - failure_projection_mean
            if success_projection_mean is not None and failure_projection_mean is not None
            else None
        ),
    }


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(_group_key(row), []).append(row)
    return [
        _aggregate_group(key, group_rows)
        for key, group_rows in sorted(groups.items(), key=lambda item: tuple(str(part) for part in item[0]))
    ]


def _write_csv(path: Path, groups: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(path)
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CSV_FIELDS), extrasaction="ignore")
        writer.writeheader()
        for group in groups:
            writer.writerow(_json_safe(group))
    tmp_path.replace(path)


def run_summary(config: SummarizeConfig) -> dict[str, Any]:
    _check_outputs(config)
    start_time = _utc_now()
    rows = list(iter_jsonl(config.input_jsonl))
    groups = summarize_rows(rows)
    payload = {
        "stage": 5,
        "summary_type": "refusal_projection_dynamics_aggregate",
        "input_jsonl": str(config.input_jsonl),
        "output_json": str(config.output_json),
        "output_csv": str(config.output_csv) if config.output_csv is not None else None,
        "num_input_rows": len(rows),
        "num_groups": len(groups),
        "group_fields": list(GROUP_FIELDS),
        "metrics": list(SUMMARY_FIELDS),
        "groups": groups,
        "config": _json_safe(asdict(config)),
        "start_time": start_time,
        "end_time": _utc_now(),
    }
    _atomic_write_json(config.output_json, payload)
    if config.output_csv is not None:
        _write_csv(config.output_csv, groups)
    return payload


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = validate_config(args)
        payload = run_summary(config)
        print(json.dumps(_json_safe(payload), indent=2, ensure_ascii=False))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
