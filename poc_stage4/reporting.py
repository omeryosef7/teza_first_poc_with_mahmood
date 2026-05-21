from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Any

from poc_stage4.schemas import INTERVENTION_SELECTED, make_json_safe, read_json, utc_now, write_json


STAGE4C_ARTIFACT_VERSION = "stage4c_v1"
DEBUG_SCIENTIFIC_STATUS = "debug_only_not_final_evidence"


@dataclass(frozen=True)
class Stage4ReportConfig:
    model_name: str
    refusal_direction_dir: Path
    refusal_dampening_dir: Path
    output_dir: Path
    allow_debug_inputs: bool
    skip_plots: bool


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL on line {line_number} in {path}: {exc}") from exc
    return rows


def _read_required_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required {label}: {path}")
    return read_json(path)


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    return read_json(path) if path.exists() else None


def _load_inputs(config: Stage4ReportConfig) -> dict[str, Any]:
    direction_dir = config.refusal_direction_dir
    dampening_dir = config.refusal_dampening_dir

    per_example_path = dampening_dir / "per_example_refusal_components.jsonl"
    if not per_example_path.exists():
        raise FileNotFoundError(f"Missing required Stage 4B per-example JSONL: {per_example_path}")

    return {
        "selected_direction": _read_required_json(direction_dir / "selected_direction.json", "selected direction metadata"),
        "candidate_metadata": _read_required_json(direction_dir / "candidate_metadata.json", "Stage 4A1 candidate metadata"),
        "intervention_metrics": _read_optional_json(direction_dir / "intervention_selection_metrics.json"),
        "intervention_scores": _read_optional_json(direction_dir / "intervention_candidate_scores.json"),
        "dampening_summary": _read_required_json(dampening_dir / "refusal_dampening_summary.json", "Stage 4B summary"),
        "per_example_rows": read_jsonl(per_example_path),
        "paths": {
            "selected_direction": str(direction_dir / "selected_direction.json"),
            "candidate_metadata": str(direction_dir / "candidate_metadata.json"),
            "intervention_selection_metrics": str(direction_dir / "intervention_selection_metrics.json"),
            "intervention_candidate_scores": str(direction_dir / "intervention_candidate_scores.json"),
            "refusal_dampening_summary": str(dampening_dir / "refusal_dampening_summary.json"),
            "per_example_refusal_components": str(per_example_path),
        },
    }


def _report_status(inputs: dict[str, Any]) -> tuple[str, list[str]]:
    warnings: list[str] = []
    selected_direction = inputs["selected_direction"]
    dampening_summary = inputs["dampening_summary"]
    intervention_metrics = inputs.get("intervention_metrics")

    if selected_direction.get("selection_status") != INTERVENTION_SELECTED:
        warnings.append(
            "Selected direction is not intervention_selected; report is debug/preliminary."
        )
    if intervention_metrics and intervention_metrics.get("selection_status") != INTERVENTION_SELECTED:
        warnings.append(
            "Stage 4A2 intervention metrics are not intervention_selected; selection may be smoke/debug only."
        )
    if bool(dampening_summary.get("debug_only_run")):
        warnings.append("Stage 4B summary has debug_only_run=true.")
    if dampening_summary.get("scientific_status") == DEBUG_SCIENTIFIC_STATUS:
        warnings.append("Stage 4B scientific_status is debug_only_not_final_evidence.")

    status = "debug_preliminary" if warnings else "final_scientific"
    return status, warnings


def _candidate_count(shape: list[Any] | None) -> int | None:
    if not shape or len(shape) < 2:
        return None
    return int(shape[0]) * int(shape[1])


def _condition_summary_from_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values_by_condition: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.get("condition") is None or row.get("refusal_component") is None:
            continue
        values_by_condition[str(row["condition"])].append(float(row["refusal_component"]))

    ordered_conditions = ["direct_harmful", "hijacked_medium", "hijacked_long"]
    output: list[dict[str, Any]] = []
    for condition in ordered_conditions:
        values = values_by_condition.get(condition, [])
        output.append(
            {
                "condition": condition,
                "mean": float(mean(values)) if values else None,
                "median": float(median(values)) if values else None,
                "count": len(values),
            }
        )
    return output


def _goal_delta_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_goal: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if row.get("goal_index") is None or row.get("condition") is None:
            continue
        by_goal[int(row["goal_index"])][str(row["condition"])] = row

    output: list[dict[str, Any]] = []
    for goal_index in sorted(by_goal):
        condition_rows = by_goal[goal_index]
        direct = condition_rows.get("direct_harmful", {}).get("refusal_component")
        medium = condition_rows.get("hijacked_medium", {}).get("refusal_component")
        long = condition_rows.get("hijacked_long", {}).get("refusal_component")
        direct_f = float(direct) if direct is not None else None
        medium_f = float(medium) if medium is not None else None
        long_f = float(long) if long is not None else None
        output.append(
            {
                "goal_index": goal_index,
                "direct_harmful": direct_f,
                "hijacked_medium": medium_f,
                "hijacked_long": long_f,
                "delta_medium": medium_f - direct_f if direct_f is not None and medium_f is not None else None,
                "delta_long": long_f - direct_f if direct_f is not None and long_f is not None else None,
                "hijacked_medium_equals_long": bool(
                    condition_rows.get("hijacked_medium", {}).get(
                        "hijacked_medium_equals_long",
                        condition_rows.get("hijacked_long", {}).get("hijacked_medium_equals_long", False),
                    )
                ),
            }
        )
    return output


def _build_payload(config: Stage4ReportConfig, inputs: dict[str, Any], outputs: dict[str, str]) -> dict[str, Any]:
    selected_direction = inputs["selected_direction"]
    candidate_metadata = inputs["candidate_metadata"]
    intervention_metrics = inputs.get("intervention_metrics") or {}
    intervention_scores = inputs.get("intervention_scores") or {}
    dampening_summary = inputs["dampening_summary"]
    per_example_rows = inputs["per_example_rows"]

    report_status, warnings = _report_status(inputs)
    if report_status != "final_scientific" and not config.allow_debug_inputs:
        formatted = "\n".join(f"- {warning}" for warning in warnings)
        raise RuntimeError(
            "Stage 4C refused to build a report from debug/preliminary inputs. "
            "Pass --allow-debug-inputs only for debug reports.\n" + formatted
        )

    candidate_shape = candidate_metadata.get("candidate_tensor_shape") or selected_direction.get("candidate_tensor_shape")
    condition_rows = _condition_summary_from_rows(per_example_rows)
    goal_rows = _goal_delta_rows(per_example_rows)

    selection_status = selected_direction.get("selection_status")
    if intervention_metrics.get("selection_status"):
        selection_status = intervention_metrics.get("selection_status")

    return {
        "artifact_version": STAGE4C_ARTIFACT_VERSION,
        "stage": "stage4c_qwen_mechanistic_report",
        "timestamp_utc": utc_now(),
        "model_name": config.model_name,
        "report_status": report_status,
        "allow_debug_inputs": config.allow_debug_inputs,
        "debug_or_preliminary": report_status != "final_scientific",
        "warnings": warnings,
        "debug_warning": (
            "DEBUG/PRELIMINARY REPORT: inputs are not final scientific evidence."
            if report_status != "final_scientific"
            else None
        ),
        "inputs": inputs["paths"],
        "stage4a1_candidate_summary": {
            "candidate_tensor_shape": candidate_shape,
            "num_candidates": _candidate_count(candidate_shape),
            "positions": candidate_metadata.get("positions"),
            "layers": candidate_metadata.get("layers"),
            "num_layers": candidate_metadata.get("num_layers"),
        },
        "stage4a2_selection_summary": {
            "selection_status": selection_status,
            "selected_position": selected_direction.get("selected_position")
            if selected_direction.get("selected_position") is not None
            else intervention_metrics.get("selected_position"),
            "selected_layer": selected_direction.get("selected_layer")
            if selected_direction.get("selected_layer") is not None
            else intervention_metrics.get("selected_layer"),
            "num_candidates_evaluated": intervention_metrics.get(
                "num_candidates_evaluated",
                intervention_scores.get("num_candidates_evaluated"),
            ),
            "num_candidates_surviving_filters": intervention_metrics.get(
                "num_candidates_surviving_filters",
                intervention_scores.get("num_candidates_surviving_filters"),
            ),
        },
        "stage4b_dampening_summary": {
            "number_of_goals": dampening_summary.get("number_of_goals"),
            "mean_refusal_component_by_condition": dampening_summary.get("mean_refusal_component_by_condition"),
            "median_refusal_component_by_condition": dampening_summary.get("median_refusal_component_by_condition"),
            "mean_delta_medium": dampening_summary.get("mean_delta_medium"),
            "mean_delta_long": dampening_summary.get("mean_delta_long"),
            "fraction_negative_delta_medium": dampening_summary.get("fraction_negative_delta_medium"),
            "fraction_negative_delta_long": dampening_summary.get("fraction_negative_delta_long"),
            "scientific_status": dampening_summary.get("scientific_status"),
            "debug_only_run": dampening_summary.get("debug_only_run"),
        },
        "condition_rows": condition_rows,
        "goal_delta_rows": goal_rows,
        "interpretation": {
            "negative_delta": "negative delta means refusal-direction dampening",
            "debug_caveat": (
                "This report cannot be used as final evidence unless report_status is final_scientific."
                if report_status != "final_scientific"
                else None
            ),
        },
        "outputs": outputs,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: make_json_safe(row.get(field)) for field in fieldnames})


def _format_value(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _markdown_report(payload: dict[str, Any]) -> str:
    a1 = payload["stage4a1_candidate_summary"]
    a2 = payload["stage4a2_selection_summary"]
    b = payload["stage4b_dampening_summary"]
    lines = [
        "# Stage 4 Qwen3 Mechanistic Report",
        "",
        f"- Model: `{payload['model_name']}`",
        f"- Report status: `{payload['report_status']}`",
    ]
    if payload.get("debug_warning"):
        lines += ["", f"**Warning:** {payload['debug_warning']}"]
    if payload["warnings"]:
        lines += ["", "## Warnings"]
        lines += [f"- {warning}" for warning in payload["warnings"]]

    lines += [
        "",
        "## Stage 4A1 Candidate Summary",
        "",
        f"- Candidate tensor shape: `{a1.get('candidate_tensor_shape')}`",
        f"- Number of candidates: {_format_value(a1.get('num_candidates'))}",
        f"- Positions: `{a1.get('positions')}`",
        f"- Number of layers: {_format_value(a1.get('num_layers'))}",
        "",
        "## Stage 4A2 Selection Summary",
        "",
        f"- Selection status: `{a2.get('selection_status')}`",
        f"- Selected position: {_format_value(a2.get('selected_position'))}",
        f"- Selected layer: {_format_value(a2.get('selected_layer'))}",
        f"- Candidates evaluated: {_format_value(a2.get('num_candidates_evaluated'))}",
        f"- Candidates surviving filters: {_format_value(a2.get('num_candidates_surviving_filters'))}",
        "",
        "## Stage 4B Dampening Summary",
        "",
        f"- Number of goals: {_format_value(b.get('number_of_goals'))}",
        f"- Mean delta medium: {_format_value(b.get('mean_delta_medium'))}",
        f"- Mean delta long: {_format_value(b.get('mean_delta_long'))}",
        f"- Fraction negative delta medium: {_format_value(b.get('fraction_negative_delta_medium'))}",
        f"- Fraction negative delta long: {_format_value(b.get('fraction_negative_delta_long'))}",
        "",
        "### Refusal Component By Condition",
        "",
        "| Condition | Mean | Median | Count |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in payload["condition_rows"]:
        lines.append(
            f"| `{row['condition']}` | {_format_value(row['mean'])} | "
            f"{_format_value(row['median'])} | {_format_value(row['count'])} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- Negative delta means refusal-direction dampening: "
        "`hijacked_component - direct_harmful_component < 0`.",
    ]
    if payload["report_status"] != "final_scientific":
        lines.append("- This report is debug/preliminary and cannot be used as final scientific evidence.")
    return "\n".join(lines) + "\n"


def _write_plots(output_dir: Path, condition_rows: list[dict[str, Any]], goal_rows: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        return {"plots_written": [], "plots_skipped_reason": f"matplotlib unavailable: {exc}"}

    plots_written: list[str] = []

    condition_path = output_dir / "refusal_component_by_condition.png"
    labels = [str(row["condition"]) for row in condition_rows]
    means = [row["mean"] if row["mean"] is not None else 0.0 for row in condition_rows]
    plt.figure(figsize=(8, 4))
    plt.bar(labels, means)
    plt.ylabel("Mean refusal component")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(condition_path)
    plt.close()
    plots_written.append(str(condition_path))

    delta_path = output_dir / "dampening_delta_by_goal.png"
    goal_labels = [str(row["goal_index"]) for row in goal_rows]
    delta_medium = [row["delta_medium"] if row["delta_medium"] is not None else 0.0 for row in goal_rows]
    delta_long = [row["delta_long"] if row["delta_long"] is not None else 0.0 for row in goal_rows]
    x_values = list(range(len(goal_rows)))
    plt.figure(figsize=(8, 4))
    plt.bar([value - 0.2 for value in x_values], delta_medium, width=0.4, label="medium")
    plt.bar([value + 0.2 for value in x_values], delta_long, width=0.4, label="long")
    plt.axhline(0.0, color="black", linewidth=0.8)
    plt.ylabel("Delta vs direct harmful")
    plt.xlabel("Goal index")
    plt.xticks(x_values, goal_labels)
    plt.legend()
    plt.tight_layout()
    plt.savefig(delta_path)
    plt.close()
    plots_written.append(str(delta_path))

    return {"plots_written": plots_written, "plots_skipped_reason": None}


def build_stage4_report(config: Stage4ReportConfig) -> dict[str, Any]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "json": str(config.output_dir / "stage4_qwen_report.json"),
        "markdown": str(config.output_dir / "stage4_qwen_report.md"),
        "condition_csv": str(config.output_dir / "refusal_components_by_condition.csv"),
        "goal_delta_csv": str(config.output_dir / "refusal_dampening_by_goal.csv"),
    }
    inputs = _load_inputs(config)
    payload = _build_payload(config, inputs, output_paths)

    _write_csv(
        config.output_dir / "refusal_components_by_condition.csv",
        payload["condition_rows"],
        ["condition", "mean", "median", "count"],
    )
    _write_csv(
        config.output_dir / "refusal_dampening_by_goal.csv",
        payload["goal_delta_rows"],
        [
            "goal_index",
            "direct_harmful",
            "hijacked_medium",
            "hijacked_long",
            "delta_medium",
            "delta_long",
            "hijacked_medium_equals_long",
        ],
    )

    if config.skip_plots:
        plot_metadata = {"plots_written": [], "plots_skipped_reason": "--skip-plots was passed"}
    else:
        plot_metadata = _write_plots(config.output_dir, payload["condition_rows"], payload["goal_delta_rows"])
    payload["plot_metadata"] = plot_metadata
    payload["outputs"]["plots"] = plot_metadata["plots_written"]

    (config.output_dir / "stage4_qwen_report.md").write_text(_markdown_report(payload), encoding="utf-8")
    write_json(config.output_dir / "stage4_qwen_report.json", payload)
    return payload
