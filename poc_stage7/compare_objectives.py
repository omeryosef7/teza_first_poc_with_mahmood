from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from poc_stage5.data_loading import validate_jsonl_path

from poc_stage7.objectives import (
    ObjectiveParameters,
    Stage7Config,
    parse_regions,
    run_stage7_comparison,
    write_stage7_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute offline Stage 7 objective comparisons from Stage 5 projection rows."
    )
    parser.add_argument("--stage5-jsonl", required=True)
    parser.add_argument("--stage6-jsonl")
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--regions", default="final_token,last_8,last_32")
    parser.add_argument("--hidden-state-index", type=int, default=40)
    parser.add_argument("--lambda-refusal", type=float, default=1.0)
    parser.add_argument("--lambda-preserve", type=float, default=1.0)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--delta", type=float, default=1.0)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def validate_config(args: argparse.Namespace) -> Stage7Config:
    stage5_jsonl = validate_jsonl_path(args.stage5_jsonl)
    stage6_jsonl = validate_jsonl_path(args.stage6_jsonl) if args.stage6_jsonl else None
    return Stage7Config(
        stage5_jsonl=stage5_jsonl,
        stage6_jsonl=stage6_jsonl,
        output_jsonl=Path(args.output_jsonl),
        summary_json=Path(args.summary_json),
        regions=parse_regions(str(args.regions)),
        hidden_state_index=int(args.hidden_state_index),
        objective_parameters=ObjectiveParameters(
            lambda_refusal=float(args.lambda_refusal),
            lambda_preserve=float(args.lambda_preserve),
            alpha=float(args.alpha),
            beta=float(args.beta),
            delta=float(args.delta),
        ),
        overwrite=bool(args.overwrite),
    )


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = validate_config(args)
        output_rows, summary = run_stage7_comparison(config)
        write_stage7_outputs(output_rows, config, summary)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
