"""
Pareto frontier analysis for Stage GCG-Early.

Reads PARETO_CANDIDATES.jsonl and ITERATION_LOG.jsonl from a run directory
and produces:
  - RESULTS_SUMMARY.md with trajectory statistics and best candidates

For Stage 3 (task-only, lambda_repr=0): repr_loss is always 0; the Pareto
front collapses to the best-task-loss candidate. Full 2D Pareto analysis
is used from Stage 6 onward when lambda_repr > 0.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def load_iteration_log(run_dir: Path) -> List[dict]:
    path = Path(run_dir) / "ITERATION_LOG.jsonl"
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_pareto_candidates(run_dir: Path) -> List[dict]:
    path = Path(run_dir) / "PARETO_CANDIDATES.jsonl"
    rows = []
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _is_dominated(candidate: dict, others: List[dict]) -> bool:
    """Return True if candidate is dominated by at least one entry in others."""
    for o in others:
        if (o["task_loss"] <= candidate["task_loss"] and
                o["repr_loss"] <= candidate["repr_loss"] and
                (o["task_loss"] < candidate["task_loss"] or
                 o["repr_loss"] < candidate["repr_loss"])):
            return True
    return False


def compute_pareto_frontier(candidates: List[dict]) -> List[dict]:
    """Return the non-dominated subset of candidates (minimizing task_loss and repr_loss)."""
    frontier = []
    for cand in candidates:
        if not _is_dominated(cand, candidates):
            frontier.append(cand)
    return sorted(frontier, key=lambda x: x["task_loss"])


def analyze_pareto(run_dir: Path, output_subdir: str = "analysis") -> None:
    """
    Full Pareto analysis. Writes RESULTS_SUMMARY.md into run_dir.

    Works for both task-only (Stage 3) and repr-objective runs (Stage 6+).
    For task-only runs, repr_loss is 0 everywhere and the Pareto front
    collapses to the single best-task-loss candidate.
    """
    run_dir = Path(run_dir)
    rows = load_iteration_log(run_dir)
    if not rows:
        print(f"[analyze] No iteration log rows in {run_dir}")
        return

    pareto_rows = load_pareto_candidates(run_dir)

    # Trajectory statistics
    steps = [r["step"] for r in rows]
    task_losses = [r["task_loss"] for r in rows]
    repr_losses = [r["repr_loss"] for r in rows]
    total_losses = [r["total_loss"] for r in rows]
    wall_times = [r.get("wall_time_sec", 0.0) for r in rows]

    best_task_idx = task_losses.index(min(task_losses))
    best_total_idx = total_losses.index(min(total_losses))
    best_task_row = rows[best_task_idx]
    best_total_row = rows[best_total_idx]

    # Pareto frontier from logged pareto_rows (deduplicated by step)
    seen_steps = set()
    unique_pareto = []
    for p in pareto_rows:
        if p["step"] not in seen_steps:
            seen_steps.add(p["step"])
            unique_pareto.append(p)
    frontier = compute_pareto_frontier(unique_pareto) if unique_pareto else []

    # Load config for context
    config_path = run_dir / "CONFIG.json"
    config_info = {}
    if config_path.exists():
        try:
            config_info = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Compute per-step timing stats
    avg_step_sec = sum(wall_times) / len(wall_times) if wall_times else 0.0
    total_runtime_min = sum(wall_times) / 60.0

    # Whether this is task-only (Stage 3) or repr-objective run
    lambda_repr = float((config_info.get("objective") or {}).get("lambda_repr", 0.0))
    lambda_kl = float((config_info.get("objective") or {}).get("lambda_kl", 0.0))
    is_task_only = (lambda_repr == 0.0 and lambda_kl == 0.0)

    # Write RESULTS_SUMMARY.md
    lines = [
        f"# GCG Optimization Results: {run_dir.name}",
        f"",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}  ",
        f"**Run directory:** `{run_dir}`  ",
        f"**Stage:** {'Task-only (lambda_repr=0, lambda_kl=0)' if is_task_only else f'Repr objective (lambda_repr={lambda_repr}, lambda_kl={lambda_kl})'}",
        f"",
        f"---",
        f"",
        f"## Trajectory Summary",
        f"",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Steps completed | {len(rows)} |",
        f"| task_loss step 0 | {task_losses[0]:.4f} |",
        f"| task_loss final | {task_losses[-1]:.4f} |",
        f"| task_loss best | {min(task_losses):.4f} (step {best_task_idx}) |",
        f"| repr_loss step 0 | {repr_losses[0]:.4f} |",
        f"| repr_loss final | {repr_losses[-1]:.4f} |",
        f"| repr_loss best | {min(repr_losses):.4f} |",
        f"| avg step time | {avg_step_sec:.1f}s |",
        f"| total runtime | {total_runtime_min:.1f} min |",
        f"",
    ]

    # Validation gate check (Stage 3)
    task_decreased = min(task_losses) < task_losses[0]
    lines += [
        f"## Stage 3 Validation Gate",
        f"",
        f"| Check | Result |",
        f"|---|---|",
        f"| task_loss decreased from step 0 | {'PASS' if task_decreased else 'FAIL'} |",
        f"| best task_loss < initial | {'%.4f < %.4f' % (min(task_losses), task_losses[0]) if task_decreased else 'NO'} |",
        f"",
    ]

    # Best candidates
    lines += [
        f"## Best Candidates",
        f"",
        f"**By task_loss (step {best_task_idx}):**",
        f"- task_loss={best_task_row['task_loss']:.4f}",
        f"- repr_loss={best_task_row['repr_loss']:.4f}",
        f"- suffix=`{best_task_row.get('suffix_str', '')[:80]}`",
        f"- suffix_ids={best_task_row.get('suffix_ids', [])[:16]}",
        f"",
    ]

    if not is_task_only:
        lines += [
            f"**By total_loss (step {best_total_idx}):**",
            f"- task_loss={best_total_row['task_loss']:.4f}",
            f"- repr_loss={best_total_row['repr_loss']:.4f}",
            f"- suffix=`{best_total_row.get('suffix_str', '')[:80]}`",
            f"",
        ]

    # Pareto frontier
    if frontier and not is_task_only:
        lines += [
            f"## Pareto Frontier ({len(frontier)} candidates)",
            f"",
            f"| Step | task_loss | repr_loss | suffix (first 40 chars) |",
            f"|---|---|---|---|",
        ]
        for p in frontier[:20]:
            lines.append(
                f"| {p['step']} | {p['task_loss']:.4f} | {p['repr_loss']:.4f} "
                f"| `{str(p.get('suffix_str', ''))[:40]}` |"
            )
        lines.append("")

    # Config summary
    gcg_cfg = config_info.get("gcg") or {}
    obj_cfg = config_info.get("objective") or {}
    lines += [
        f"## Run Configuration",
        f"",
        f"| Parameter | Value |",
        f"|---|---|",
        f"| model | `{config_info.get('model_name_or_path', 'unknown')}` |",
        f"| suffix_length | {gcg_cfg.get('suffix_length', '?')} |",
        f"| batch_size | {gcg_cfg.get('batch_size', '?')} |",
        f"| topk | {gcg_cfg.get('topk', '?')} |",
        f"| n_steps | {gcg_cfg.get('n_steps', '?')} |",
        f"| seed | {gcg_cfg.get('seed', '?')} |",
        f"| lambda_repr | {obj_cfg.get('lambda_repr', 0.0)} |",
        f"| lambda_kl | {obj_cfg.get('lambda_kl', 0.0)} |",
        f"| repr_metric | {obj_cfg.get('repr_metric', 'cosine')} |",
        f"| selection_mode | {obj_cfg.get('selection_mode', 'weighted')} |",
        f"",
    ]

    summary_path = run_dir / "RESULTS_SUMMARY.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[analyze] Written {summary_path}")

    # Print quick summary to stdout
    print_iteration_summary(run_dir)


def print_iteration_summary(run_dir: Path) -> None:
    """Print a quick summary of optimization progress (no GPU needed)."""
    rows = load_iteration_log(run_dir)
    if not rows:
        print(f"[analyze] No iteration log rows in {run_dir}")
        return
    first = rows[0]
    last = rows[-1]
    best_task = min(r["task_loss"] for r in rows)
    best_repr = min(r["repr_loss"] for r in rows)
    print(f"[analyze] {len(rows)} steps logged")
    print(f"  step 0      task_loss={first['task_loss']:.4f}  repr_loss={first['repr_loss']:.4f}")
    print(f"  step {last['step']:4d}   task_loss={last['task_loss']:.4f}  repr_loss={last['repr_loss']:.4f}")
    print(f"  best task_loss={best_task:.4f}  best repr_loss={best_repr:.4f}")
    decreased = best_task < first["task_loss"]
    print(f"  Stage 3 gate (task_loss decreased): {'PASS' if decreased else 'FAIL'}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    if args.summary_only:
        print_iteration_summary(Path(args.run_dir))
    else:
        analyze_pareto(Path(args.run_dir))
