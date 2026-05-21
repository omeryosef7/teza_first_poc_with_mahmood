from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from poc_stage5.data_loading import count_jsonl_rows, validate_jsonl_path


@dataclass(frozen=True)
class SummarizeConfig:
    input_jsonl: Path
    summary_json: Path | None
    no_progress: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 5 skeleton: validate refusal-projection JSONL summary inputs "
            "without writing artifacts."
        )
    )
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--summary-json")
    parser.add_argument("--no-progress", action="store_true")
    return parser


def validate_config(args: argparse.Namespace) -> SummarizeConfig:
    input_jsonl = validate_jsonl_path(args.input_jsonl)
    return SummarizeConfig(
        input_jsonl=input_jsonl,
        summary_json=Path(args.summary_json) if args.summary_json else None,
        no_progress=bool(args.no_progress),
    )


def _json_safe_config(config: SummarizeConfig) -> dict[str, Any]:
    payload = asdict(config)
    payload["input_jsonl"] = str(payload["input_jsonl"])
    if payload["summary_json"] is not None:
        payload["summary_json"] = str(payload["summary_json"])
    return payload


def print_planned_summary(config: SummarizeConfig) -> None:
    payload = {
        "stage": "stage5_refusal_projection_dynamics_summary_skeleton",
        "status": "validated_input_only_no_summary_written",
        "config": _json_safe_config(config),
        "validated_input_rows_counted": count_jsonl_rows(config.input_jsonl),
        "todos": [
            "validate Stage 5 projection row schema",
            "aggregate projections by example, layer, and token region",
            "write summary JSON",
        ],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = validate_config(args)
        print_planned_summary(config)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

