from __future__ import annotations

import argparse
import sys
from pathlib import Path

from poc_stage4.extract_refusal_direction import parse_bool


DEFAULT_QWEN3_MODEL = "Qwen/Qwen3-14B"
DEFAULT_INPUT_DIR = Path("outputs/stage4/qwen3-14b/refusal_direction")


def _parse_csv_ints(value: str | None) -> list[int] | None:
    if value is None or not value.strip():
        return None
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _parse_csv_strings(value: str | None) -> list[str] | None:
    if value is None or not value.strip():
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage 4A2: intervention-based Qwen3 refusal-direction selection."
    )
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--model-name", default=DEFAULT_QWEN3_MODEL)
    parser.add_argument("--enable-thinking", type=parse_bool, default=False)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--num-harmful-val", type=int, default=32)
    parser.add_argument("--num-harmless-val", type=int, default=32)
    parser.add_argument("--validation-seed", type=int, default=42)
    parser.add_argument("--kl-threshold", type=float, default=0.1)
    parser.add_argument("--induce-refusal-threshold", type=float, default=0.0)
    parser.add_argument("--prune-layer-percentage", type=float, default=0.2)
    parser.add_argument("--no-layer-pruning", action="store_true")
    parser.add_argument("--top-k-projection", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--use-stage4a1-heldout-validation", action="store_true")
    parser.add_argument("--refusal-token-strings", default="I,As")
    parser.add_argument("--refusal-token-ids")
    parser.add_argument("--resume", action="store_true", help="Resume Stage 4A2 from candidate checkpoints.")
    parser.add_argument("--checkpoint-dir", help="Directory for Stage 4A2 resumable checkpoints.")
    parser.add_argument("--no-progress", action="store_true", help="Disable tqdm/progress logging.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        from poc_stage4.intervention_selection import InterventionSelectionConfig, run_intervention_selection
        from poc_stage4.qwen3_model import load_qwen3_model

        config = InterventionSelectionConfig(
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir),
            model_name=args.model_name,
            enable_thinking=bool(args.enable_thinking),
            batch_size=args.batch_size,
            num_harmful_val=args.num_harmful_val,
            num_harmless_val=args.num_harmless_val,
            validation_seed=args.validation_seed,
            kl_threshold=args.kl_threshold,
            induce_refusal_threshold=args.induce_refusal_threshold,
            prune_layer_percentage=None if args.no_layer_pruning else args.prune_layer_percentage,
            top_k_projection=args.top_k_projection,
            dry_run=bool(args.dry_run),
            use_stage4a1_heldout_validation=bool(args.use_stage4a1_heldout_validation),
            refusal_token_strings=_parse_csv_strings(args.refusal_token_strings),
            refusal_token_ids=_parse_csv_ints(args.refusal_token_ids),
            resume=bool(args.resume),
            checkpoint_dir=Path(args.checkpoint_dir) if args.checkpoint_dir else None,
            no_progress=bool(args.no_progress),
        )
        from poc_stage4.run_state import log_progress

        log_progress("stage4a2", "Loading Qwen3 model", enabled=not config.no_progress, model=config.model_name)
        model_base = load_qwen3_model(config.model_name)
        metrics = run_intervention_selection(config=config, model_base=model_base)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Wrote intervention candidate scores to: {config.output_dir / 'intervention_candidate_scores.json'}")
    print(f"Wrote intervention metrics to: {config.output_dir / 'intervention_selection_metrics.json'}")
    print(f"Selection status: {metrics['selection_status']}")
    if metrics.get("selection_status") == "intervention_selected":
        print(f"Updated final direction.pt and selected_direction.json in: {config.output_dir}")
        print(f"Selected position: {metrics.get('selected_position')}")
        print(f"Selected layer: {metrics.get('selected_layer')}")
    else:
        print("Smoke mode did not overwrite direction.pt or selected_direction.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
