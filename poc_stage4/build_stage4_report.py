from __future__ import annotations

import argparse
import sys
from pathlib import Path


DEFAULT_QWEN3_MODEL = "Qwen/Qwen3-14B"
DEFAULT_REFUSAL_DIRECTION_DIR = Path("outputs/stage4/qwen3-14b/refusal_direction")
DEFAULT_REFUSAL_DAMPENING_DIR = Path("outputs/stage4/qwen3-14b/refusal_dampening")
DEFAULT_OUTPUT_DIR = Path("outputs/stage4/qwen3-14b/report")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage 4C: build a Qwen3-only mechanistic report from Stage 4 artifacts."
    )
    parser.add_argument("--model-name", default=DEFAULT_QWEN3_MODEL)
    parser.add_argument("--refusal-direction-dir", default=str(DEFAULT_REFUSAL_DIRECTION_DIR))
    parser.add_argument("--refusal-dampening-dir", default=str(DEFAULT_REFUSAL_DAMPENING_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--allow-debug-inputs",
        action="store_true",
        help="Allow provisional/debug Stage 4 inputs and mark the report as preliminary.",
    )
    parser.add_argument("--skip-plots", action="store_true", help="Skip optional matplotlib plot generation.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        from poc_stage4.reporting import Stage4ReportConfig, build_stage4_report

        config = Stage4ReportConfig(
            model_name=args.model_name,
            refusal_direction_dir=Path(args.refusal_direction_dir),
            refusal_dampening_dir=Path(args.refusal_dampening_dir),
            output_dir=Path(args.output_dir),
            allow_debug_inputs=bool(args.allow_debug_inputs),
            skip_plots=bool(args.skip_plots),
        )
        report = build_stage4_report(config)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Wrote Stage 4C report JSON to: {config.output_dir / 'stage4_qwen_report.json'}")
    print(f"Wrote Stage 4C report Markdown to: {config.output_dir / 'stage4_qwen_report.md'}")
    print(f"Report status: {report['report_status']}")
    if report.get("debug_warning"):
        print(report["debug_warning"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
