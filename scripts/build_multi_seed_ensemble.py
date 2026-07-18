"""
Build a per-behavior best-seed ensemble from multiple GCG optimization runs.

For each training behavior, picks the suffix from whichever seed achieved the
lowest final task_loss. Writes a merged FINAL_CANDIDATES.jsonl and a fake
CONFIG.json so the result can be passed to run_gcg_full_free_generation.slurm.

Usage:
    python scripts/build_multi_seed_ensemble.py \
        --source-dirs \
            outputs/stage_gcg_full/gcg_full_qwen3_cot_target \
            outputs/stage_gcg_full/gcg_full_qwen3_7b_seed43 \
            outputs/stage_gcg_full/gcg_full_qwen3_7b_seed44 \
            outputs/stage_gcg_full/gcg_full_qwen3_7b_seed45 \
        --output-dir outputs/stage_gcg_full/gcg_full_qwen3_9f_ensemble \
        --manifest outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl

The output directory can then be evaluated with:
    sbatch --export=ALL,RUN_DIR=<output-dir>,MANIFEST=<cot-manifest> \
           slurm_scripts/run_gcg_full_free_generation.slurm
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Optional


def load_final_candidates(run_dir: Path) -> list[dict]:
    """Load FINAL_CANDIDATES.jsonl from a run directory."""
    path = run_dir / "FINAL_CANDIDATES.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"FINAL_CANDIDATES.jsonl not found in {run_dir}")
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def load_iteration_log(run_dir: Path) -> list[dict]:
    """Load ITERATION_LOG.jsonl from a run directory."""
    path = run_dir / "ITERATION_LOG.jsonl"
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def get_final_task_loss_by_behavior(run_dir: Path) -> dict[str, float]:
    """
    Extract final task_loss per behavior from ITERATION_LOG.

    Returns mapping from task_id → final task_loss (lowest seen across all steps).
    Falls back to reading FINAL_CANDIDATES if log is missing.
    """
    log = load_iteration_log(run_dir)
    if not log:
        # Fall back: use task_loss from FINAL_CANDIDATES
        candidates = load_final_candidates(run_dir)
        return {c["task_id"]: c.get("task_loss", float("inf")) for c in candidates}

    # For each task_id, find the minimum task_loss across all logged steps
    best: dict[str, float] = {}
    for row in log:
        task_id = row.get("task_id", "")
        loss = row.get("task_loss", float("inf"))
        if task_id and loss < best.get(task_id, float("inf")):
            best[task_id] = loss
    return best


def main() -> None:
    parser = argparse.ArgumentParser(description="Build per-behavior best-seed ensemble")
    parser.add_argument(
        "--source-dirs", nargs="+", required=True,
        help="List of run directories (one per seed) to draw candidates from"
    )
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory to write the ensemble FINAL_CANDIDATES.jsonl and CONFIG.json"
    )
    parser.add_argument(
        "--manifest", default=None,
        help="Manifest path to embed in the output CONFIG.json (for free-gen eval)"
    )
    parser.add_argument(
        "--selection-criterion", default="task_loss",
        choices=["task_loss", "strongreject_score"],
        help="Criterion for selecting the best seed per behavior (default: task_loss)"
    )
    args = parser.parse_args()

    source_dirs = [Path(d) for d in args.source_dirs]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Building ensemble from {len(source_dirs)} source runs:")
    for d in source_dirs:
        print(f"  {d}")

    # --- Load candidates and per-behavior scores from each run ---
    run_candidates: dict[str, list[dict]] = {}   # run_dir_name → list of candidates
    run_task_losses: dict[str, dict[str, float]] = {}  # run_dir_name → {task_id: loss}
    all_task_ids: set[str] = set()

    for src in source_dirs:
        name = src.name
        candidates = load_final_candidates(src)
        run_candidates[name] = candidates
        run_task_losses[name] = get_final_task_loss_by_behavior(src)
        all_task_ids.update(c["task_id"] for c in candidates)
        print(f"  {name}: {len(candidates)} candidates, "
              f"{len(run_task_losses[name])} task_ids in log")

    # --- Per task_id: find the best source run ---
    ensemble_candidates: list[dict] = []
    selection_log: list[dict] = []

    for task_id in sorted(all_task_ids):
        best_loss = float("inf")
        best_run: Optional[str] = None
        best_cand: Optional[dict] = None

        for src in source_dirs:
            name = src.name
            loss = run_task_losses[name].get(task_id, float("inf"))
            candidates_for_task = [
                c for c in run_candidates[name] if c.get("task_id") == task_id
            ]
            if not candidates_for_task:
                continue
            if loss < best_loss:
                best_loss = loss
                best_run = name
                best_cand = candidates_for_task[0]

        if best_cand is not None:
            best_cand = dict(best_cand)
            best_cand["_ensemble_source_run"] = best_run
            best_cand["_ensemble_task_loss"] = best_loss
            ensemble_candidates.append(best_cand)
            selection_log.append({
                "task_id": task_id,
                "selected_run": best_run,
                "task_loss": best_loss,
            })

    print(f"\nEnsemble: {len(ensemble_candidates)} candidates selected "
          f"from {len(source_dirs)} runs")

    # Count how many times each run was selected
    from collections import Counter
    run_counts = Counter(s["selected_run"] for s in selection_log)
    print("Selections per run:")
    for run, count in sorted(run_counts.items(), key=lambda x: -x[1]):
        print(f"  {run}: {count}")

    # --- Write output ---
    candidates_path = output_dir / "FINAL_CANDIDATES.jsonl"
    with open(candidates_path, "w") as f:
        for cand in ensemble_candidates:
            f.write(json.dumps(cand) + "\n")
    print(f"\nWrote {len(ensemble_candidates)} candidates to {candidates_path}")

    # Write selection log
    log_path = output_dir / "ENSEMBLE_SELECTION_LOG.jsonl"
    with open(log_path, "w") as f:
        for entry in selection_log:
            f.write(json.dumps(entry) + "\n")
    print(f"Wrote selection log to {log_path}")

    # Copy CONFIG.json from the first source run and patch manifest path if given
    src_config_path = source_dirs[0] / "CONFIG.json"
    if src_config_path.exists():
        config = json.loads(src_config_path.read_text())
        config["run_id"] = output_dir.name
        config["output_dir"] = str(output_dir)
        if args.manifest:
            config["manifest_path"] = args.manifest
        config["_ensemble_source_runs"] = [d.name for d in source_dirs]
        out_config = output_dir / "CONFIG.json"
        out_config.write_text(json.dumps(config, indent=2, sort_keys=True))
        print(f"Wrote CONFIG.json to {out_config}")
    else:
        print(f"WARNING: No CONFIG.json found in {source_dirs[0]}, skipping")

    print("\nTo evaluate ensemble:")
    manifest_arg = args.manifest or "<path-to-cot-manifest>"
    print(f"  sbatch --export=ALL,RUN_DIR={output_dir},MANIFEST={manifest_arg} "
          "slurm_scripts/run_gcg_full_free_generation.slurm")


if __name__ == "__main__":
    main()
