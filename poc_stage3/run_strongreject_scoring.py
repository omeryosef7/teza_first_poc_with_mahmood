from __future__ import annotations

import argparse
import sys
from pathlib import Path

from poc_stage3.strongreject_scoring import (
    DEFAULT_EVALUATOR,
    DEFAULT_STRONGREJECT_THRESHOLD,
    ScoringRunConfig,
    run_scoring_pipeline,
    validate_scored_rows,
    write_json,
    write_jsonl,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score Stage 2 hijacking outputs with StrongREJECT and write separate artifacts."
    )
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--evaluator", default=DEFAULT_EVALUATOR)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--only-successful-hijacking-rows", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--threshold", type=float, default=DEFAULT_STRONGREJECT_THRESHOLD)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = ScoringRunConfig(
        input_jsonl=Path(args.input_jsonl),
        output_jsonl=Path(args.output_jsonl),
        summary_json=Path(args.summary_json),
        evaluator=args.evaluator,
        threshold=args.threshold,
        max_rows=args.max_rows,
        only_successful_hijacking_rows=args.only_successful_hijacking_rows,
        resume=args.resume,
        sleep_seconds=args.sleep_seconds,
        overwrite=args.overwrite,
    )

    try:
        scored_rows, summary = run_scoring_pipeline(config)
        validate_scored_rows(scored_rows, threshold=config.threshold)
        write_jsonl(config.output_jsonl, scored_rows)
        write_json(config.summary_json, summary)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Wrote scored JSONL: {config.output_jsonl}")
    print(f"Wrote summary JSON: {config.summary_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())