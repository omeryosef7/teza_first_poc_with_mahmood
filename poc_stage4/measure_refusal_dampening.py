from __future__ import annotations

import argparse
import sys
from pathlib import Path

from poc_stage4.extract_refusal_direction import parse_bool
from poc_stage4.refusal_dampening_measurement import DEFAULT_STAGE2_JSONL, DampeningConfig


DEFAULT_DIRECTION_DIR = Path("outputs/stage4/qwen3-14b/refusal_direction")
DEFAULT_OUTPUT_DIR = Path("outputs/stage4/qwen3-14b/refusal_dampening")
DEFAULT_QWEN3_MODEL = "Qwen/Qwen3-14B"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 4B: measure refusal-direction components for direct harmful and "
            "CoT-hijacked prompts. Requires an intervention-selected direction by default."
        )
    )
    parser.add_argument("--model-name", default=DEFAULT_QWEN3_MODEL)
    parser.add_argument("--direction-dir", default=str(DEFAULT_DIRECTION_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--stage2-jsonl", default=str(DEFAULT_STAGE2_JSONL))
    parser.add_argument("--enable-thinking", type=parse_bool, default=False)
    parser.add_argument("--num-goals", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-provisional-direction", action="store_true")
    parser.add_argument("--batch-size", type=int, default=1)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        from poc_stage4.direction_loader import load_direction
        from poc_stage4.qwen3_model import load_qwen3_model
        from poc_stage4.refusal_dampening_measurement import run_refusal_dampening_measurement

        num_goals = args.num_goals
        if num_goals is None:
            num_goals = 2 if args.dry_run else 30

        config = DampeningConfig(
            model_name=args.model_name,
            direction_dir=Path(args.direction_dir),
            output_dir=Path(args.output_dir),
            stage2_jsonl=Path(args.stage2_jsonl),
            enable_thinking=bool(args.enable_thinking),
            num_goals=num_goals,
            dry_run=bool(args.dry_run),
            allow_provisional_direction=bool(args.allow_provisional_direction),
            batch_size=args.batch_size,
        )

        loaded_direction = load_direction(
            config.direction_dir,
            allow_provisional_direction=config.allow_provisional_direction,
        )
        model_base = load_qwen3_model(config.model_name)
        summary = run_refusal_dampening_measurement(
            config=config,
            model_base=model_base,
            loaded_direction=loaded_direction,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Wrote per-example rows to: {config.output_dir / 'per_example_refusal_components.jsonl'}")
    print(f"Wrote summary to: {config.output_dir / 'refusal_dampening_summary.json'}")
    print(f"Measured goals: {summary['number_of_goals']}")
    print("Reminder: negative delta means refusal-direction dampening.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

