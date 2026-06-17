from __future__ import annotations

"""
Stage 4A2-subspace: select top-K intervention-validated refusal directions and save
them as a multi-direction subspace tensor.

DIFFERENCE FROM select_refusal_direction_interventions.py (Stage 4A2 / single direction):
  Stage 4A2: selects the single best (position, layer) candidate → direction.pt  shape [d_model]
  This script: selects top-K best survivors              → direction_subspace.pt shape [K, d_model]

The same intervention filters apply (KL threshold, refusal induction, layer pruning).
After filtering, K survivors ranked by lowest harmful_ablation_refusal_score are kept.

SUBSPACE ABLATION FORMULA (for downstream use):
    coefficients = h @ directions.T          # [batch, seq, K]
    h' = h - coefficients @ directions       # [batch, seq, d_model]
This projects out all K direction components simultaneously.

INPUTS:
  Reads from an existing Stage 4A1 output directory (candidate_directions.pt + metadata).
  Re-runs intervention evaluation (same as Stage 4A2) or reads existing scores if --resume.

OUTPUTS (to --output-dir, default: outputs/stage4/<model-slug>/direction_subspace/):
  direction_subspace.pt              [K, d_model] stacked unit-norm direction vectors
  direction_subspace_metadata.json   per-direction origins (position, layer, scores)
  intervention_candidate_scores.json full per-candidate evaluation (same format as 4A2)
"""

import argparse
import sys
from pathlib import Path
from typing import Any

DEFAULT_K = 5

ARTIFACT_VERSION = "stage4a2_subspace_v1"
STAGE_NAME = "stage4a2_subspace"


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y"}


def _parse_csv_strings(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [s.strip() for s in value.split(",") if s.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 4A2-subspace: select top-K intervention-validated refusal directions "
            "and save as direction_subspace.pt of shape [K, d_model]."
        )
    )
    parser.add_argument(
        "--model-family", default="qwen3", choices=["qwen3", "gemma4"],
        help="Model family. Controls the HF loader. Default: qwen3.",
    )
    parser.add_argument("--input-dir", default=None,
                        help=("Stage 4A1 output directory containing candidate_directions.pt. "
                              "Default: outputs/stage4/<model-slug>/refusal_direction/"))
    parser.add_argument("--output-dir", default=None,
                        help=("Where to write direction_subspace.pt and metadata. "
                              "Default: outputs/stage4/<model-slug>/direction_subspace/"))
    parser.add_argument(
        "--model-name", default=None,
        help="HF model name or path. Default: inferred from --model-family.",
    )
    parser.add_argument("--k", type=int, default=DEFAULT_K,
                        help=f"Number of directions to keep in the subspace. Default: {DEFAULT_K}")
    parser.add_argument("--enable-thinking", default="false",
                        help="Whether to use Qwen3 thinking mode when evaluating candidates.")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--num-harmful-val", type=int, default=32)
    parser.add_argument("--num-harmless-val", type=int, default=32)
    parser.add_argument("--validation-seed", type=int, default=42)
    parser.add_argument("--kl-threshold", type=float, default=0.1)
    parser.add_argument("--induce-refusal-threshold", type=float, default=0.0)
    parser.add_argument("--prune-layer-percentage", type=float, default=0.2)
    parser.add_argument("--no-layer-pruning", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="Evaluate only top-5 candidates by projection score (quick smoke test).")
    parser.add_argument("--refusal-token-strings", default="I,As")
    parser.add_argument("--resume", action="store_true",
                        help="Resume candidate evaluation from checkpoint.")
    parser.add_argument("--checkpoint-dir",
                        help="Directory for resumable candidate checkpoints.")
    parser.add_argument("--no-progress", action="store_true")
    return parser


def run_subspace_selection(
    *,
    input_dir: Path,
    output_dir: Path,
    model_name: str,
    model_family: str,
    k: int,
    enable_thinking: bool,
    batch_size: int,
    num_harmful_val: int,
    num_harmless_val: int,
    validation_seed: int,
    kl_threshold: float,
    induce_refusal_threshold: float,
    prune_layer_percentage: float | None,
    dry_run: bool,
    refusal_token_strings: list[str] | None,
    resume: bool,
    checkpoint_dir: Path | None,
    no_progress: bool,
) -> dict[str, Any]:
    import torch

    from poc_stage4.intervention_selection import (
        InterventionSelectionConfig,
        all_candidate_indices,
        evaluate_candidates,
        load_candidate_directions,
        load_stage4a2_validation_prompts,
        resolve_refusal_tokens,
        top_k_candidate_indices,
    )
    from poc_stage4.model_family_utils import load_model_by_family
    from poc_stage4.run_state import log_progress
    from poc_stage4.schemas import read_json, utc_now, write_json

    progress_enabled = not no_progress
    output_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir = checkpoint_dir or (output_dir / "checkpoints" / "subspace_selection")
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    log_progress(STAGE_NAME, "Loading model", enabled=progress_enabled, model=model_name,
                 model_family=model_family)
    model_base = load_model_by_family(model_name, model_family)

    candidate_metadata = read_json(input_dir / "candidate_metadata.json")
    candidate_directions = load_candidate_directions(input_dir, candidate_metadata)
    positions = [int(p) for p in candidate_metadata["positions"]]

    # Build the same config object that intervention_selection expects (for shared utilities)
    config = InterventionSelectionConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        model_name=model_name,
        enable_thinking=enable_thinking,
        batch_size=batch_size,
        num_harmful_val=num_harmful_val,
        num_harmless_val=num_harmless_val,
        validation_seed=validation_seed,
        kl_threshold=kl_threshold,
        induce_refusal_threshold=induce_refusal_threshold,
        prune_layer_percentage=prune_layer_percentage,
        top_k_projection=5 if dry_run else None,
        dry_run=dry_run,
        use_stage4a1_heldout_validation=False,
        refusal_token_strings=refusal_token_strings,
        refusal_token_ids=None,
        resume=resume,
        checkpoint_dir=ckpt_dir,
        no_progress=no_progress,
    )

    if dry_run:
        candidate_indices = top_k_candidate_indices(input_dir, k=5)
    else:
        candidate_indices = all_candidate_indices(positions, model_base.num_layers)

    log_progress(
        STAGE_NAME,
        "Prepared candidate list",
        enabled=progress_enabled,
        candidates=len(candidate_indices),
        dry_run=dry_run,
    )

    harmful_val, harmless_val, val_metadata = load_stage4a2_validation_prompts(config, candidate_metadata)
    refusal_meta = resolve_refusal_tokens(
        model_base,
        refusal_token_strings=refusal_token_strings,
        refusal_token_ids=None,
    )
    refusal_token_ids = [int(tid) for tid in refusal_meta["refusal_token_ids"]]

    rows, baseline_summary = evaluate_candidates(
        model_base=model_base,
        candidate_directions=candidate_directions,
        candidate_indices=candidate_indices,
        harmful_validation_prompts=harmful_val,
        harmless_validation_prompts=harmless_val,
        refusal_token_ids=refusal_token_ids,
        config=config,
        checkpoint_dir=ckpt_dir,
    )

    # Save full candidate scores (same schema as Stage 4A2 for compatibility)
    write_json(output_dir / "intervention_candidate_scores.json", {
        "artifact_version": ARTIFACT_VERSION,
        "stage": "stage4a2_subspace_candidate_scores",
        "timestamp_utc": utc_now(),
        "source_variant": "select_direction_subspace",
        "k_requested": k,
        "input_dir": str(input_dir),
        "candidates": rows,
        **baseline_summary,
        **val_metadata,
        **refusal_meta,
    })

    survivors = [row for row in rows if bool(row.get("passes_filters"))]
    if not survivors:
        raise RuntimeError(
            f"No candidates survived filters (KL≤{kl_threshold}, "
            f"steering≥{induce_refusal_threshold}). "
            f"Cannot build a {k}-direction subspace. "
            "Try --no-layer-pruning or loosening thresholds."
        )

    # Sort by ascending harmful_ablation_refusal_score (lower = better at removing refusal)
    survivors_sorted = sorted(survivors, key=lambda r: float(r["harmful_ablation_refusal_score"]))
    selected = survivors_sorted[:k]
    k_actual = len(selected)
    if k_actual < k:
        log_progress(
            STAGE_NAME,
            f"Only {k_actual} survivors available (requested K={k}); using all {k_actual}.",
            enabled=progress_enabled,
        )

    # Build [K, d_model] subspace tensor (unit-normalized)
    direction_vectors = []
    direction_meta_list = []
    for rank, row in enumerate(selected):
        pos_idx = int(row["position_index"])
        layer = int(row["layer"])
        vec = candidate_directions[pos_idx, layer].detach().cpu().float()
        original_norm = float(vec.norm().item())
        if original_norm > 1e-12:
            vec = vec / original_norm
        direction_vectors.append(vec)
        direction_meta_list.append({
            "subspace_rank": rank,
            "position_index": pos_idx,
            "position": int(row["position"]),
            "layer": layer,
            "harmful_ablation_refusal_score": float(row["harmful_ablation_refusal_score"]),
            "harmless_steering_refusal_score": float(row["harmless_steering_refusal_score"]),
            "harmless_ablation_kl_divergence": float(row["harmless_ablation_kl_divergence"]),
            "original_candidate_norm": original_norm,
        })

    subspace = torch.stack(direction_vectors, dim=0)  # [K, d_model]
    torch.save(subspace, output_dir / "direction_subspace.pt")
    log_progress(
        STAGE_NAME,
        "Saved direction_subspace.pt",
        enabled=progress_enabled,
        shape=list(subspace.shape),
    )

    metadata: dict[str, Any] = {
        "artifact_version": ARTIFACT_VERSION,
        "stage": "stage4a2_subspace_refusal_direction_selection",
        "timestamp_utc": utc_now(),
        "source_variant": "select_direction_subspace",
        "source_stage4a1_dir": str(input_dir),
        "output_dir": str(output_dir),
        "model_name": model_name,
        "model_family": model_family,
        "k_requested": k,
        "k_actual": k_actual,
        "subspace_shape": list(subspace.shape),
        "selection_criterion": (
            "top_k_lowest_harmful_ablation_refusal_score_after_kl_and_steering_and_layer_filters"
        ),
        "kl_threshold": kl_threshold,
        "induce_refusal_threshold": induce_refusal_threshold,
        "prune_layer_percentage": prune_layer_percentage,
        "enable_thinking": enable_thinking,
        "num_candidates_evaluated": len(rows),
        "num_survivors": len(survivors),
        "dry_run": dry_run,
        "directions": direction_meta_list,
        **baseline_summary,
    }
    write_json(output_dir / "direction_subspace_metadata.json", metadata)

    log_progress(
        STAGE_NAME,
        "Finished subspace selection",
        enabled=progress_enabled,
        k_actual=k_actual,
        output_dir=str(output_dir),
    )
    return metadata


def main() -> int:
    args = build_parser().parse_args()

    from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY, DEFAULT_MODEL_SLUG_BY_FAMILY
    model_family: str = args.model_family
    if args.model_name is None:
        args.model_name = DEFAULT_MODEL_BY_FAMILY[model_family]
    slug = DEFAULT_MODEL_SLUG_BY_FAMILY[model_family]
    if args.input_dir is None:
        args.input_dir = f"outputs/stage4/{slug}/refusal_direction"
    if args.output_dir is None:
        args.output_dir = f"outputs/stage4/{slug}/direction_subspace"

    enable_thinking = _parse_bool(args.enable_thinking)
    refusal_token_strings = _parse_csv_strings(args.refusal_token_strings)

    try:
        metrics = run_subspace_selection(
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir),
            model_name=args.model_name,
            model_family=model_family,
            k=args.k,
            enable_thinking=enable_thinking,
            batch_size=args.batch_size,
            num_harmful_val=args.num_harmful_val,
            num_harmless_val=args.num_harmless_val,
            validation_seed=args.validation_seed,
            kl_threshold=args.kl_threshold,
            induce_refusal_threshold=args.induce_refusal_threshold,
            prune_layer_percentage=None if args.no_layer_pruning else args.prune_layer_percentage,
            dry_run=bool(args.dry_run),
            refusal_token_strings=refusal_token_strings,
            resume=bool(args.resume),
            checkpoint_dir=Path(args.checkpoint_dir) if args.checkpoint_dir else None,
            no_progress=bool(args.no_progress),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out_dir = Path(args.output_dir)
    print(f"Wrote direction_subspace.pt shape {metrics['subspace_shape']}: {out_dir / 'direction_subspace.pt'}")
    print(f"Wrote direction_subspace_metadata.json: {out_dir / 'direction_subspace_metadata.json'}")
    print(f"Directions selected: {metrics['k_actual']} of {metrics['k_requested']} requested")
    for d in metrics["directions"]:
        print(
            f"  rank {d['subspace_rank']}: "
            f"layer={d['layer']} pos={d['position']} "
            f"harmful_ablation={d['harmful_ablation_refusal_score']:.4f} "
            f"steering={d['harmless_steering_refusal_score']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
