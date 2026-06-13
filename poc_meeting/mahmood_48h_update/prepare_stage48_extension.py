#!/usr/bin/env python3
"""
Task 3, Step 1 — Prepare Stage 4.8 extension plan and manifest.

Creates a new extension manifest and plan docs for 60 additional stochastic
generations targeting goals 0 and 2 (intermediate success probability) with
seeds 106–115. Does NOT run any model inference.

Usage:
    python -m poc_meeting.mahmood_48h_update.prepare_stage48_extension \
        --output-dir outputs/meeting/mahmood_48h_update_<TIMESTAMP>
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

TARGET_GOALS = ["0", "2"]
EXTENSION_SEEDS = list(range(106, 116))  # 106..115
CONDITIONS = ["A", "D", "F"]

# Exact model params from Stage 4.8
MODEL_PARAMS = {
    "model_name_or_path": "Qwen/Qwen3-14B",
    "model_revision": "40c069824f4251a91eefaf281ebe4c544efd3e18",
    "do_sample": True,
    "temperature": 0.7,
    "top_p": 0.95,
    "max_new_tokens": 32768,
    "enable_thinking": True,
}


def _read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    rows = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    log.warning("JSONL parse error: %s", e)
    return rows


def _read_csv(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def load_original_manifest(s48_dir: Path) -> list[dict]:
    """Load original Stage 4.8 manifest to extract source_example_ids."""
    manifest_path = _REPO_ROOT / "outputs/stage4_8/repeated_generation_manifest.jsonl"
    rows = _read_jsonl(manifest_path)
    if not rows:
        log.warning("Manifest not found at %s, trying run dir", manifest_path)
        for candidate in [s48_dir / "manifest.json", s48_dir / "manifest.jsonl"]:
            if candidate.exists():
                rows = _read_jsonl(candidate)
                if rows:
                    break
    return rows


def get_source_examples_for_goals(manifest_rows: list[dict], target_goals: list[str]) -> dict[str, dict]:
    """
    Extract one source_example_id per goal (the one used in Stage 4.8 condition A).
    Returns {goal_index_str: manifest_entry} for each target goal.
    """
    by_goal: dict[str, dict] = {}
    for r in manifest_rows:
        gi = str(r.get("goal_index", ""))
        cond = r.get("condition", "")
        if gi in target_goals and cond == "A" and gi not in by_goal:
            by_goal[gi] = r
    return by_goal


def build_extension_manifest(source_examples: dict[str, dict]) -> list[dict]:
    """Build extension manifest rows for target goals × conditions × new seeds."""
    rows = []
    for gi, src in source_examples.items():
        src_id = src.get("source_example_id", src.get("run_id", ""))
        selection_stratum = src.get("selection_stratum", "")
        for cond in CONDITIONS:
            # Find transformation_method for this condition from original manifest
            transformation_method = "identity_copy"
            if cond == "F":
                transformation_method = "benign_length_matched_wrapper"
            elif cond == "D":
                transformation_method = "puzzle_removal"
            for seed in EXTENSION_SEEDS:
                run_id = f"{src_id.replace('|', '__')}__cond_{cond}__seed_{seed}"
                row = {
                    "run_id": run_id,
                    "source_example_id": src_id,
                    "goal_index": gi,
                    "condition": cond,
                    "seed": seed,
                    "enable_thinking": MODEL_PARAMS["enable_thinking"],
                    "model_name_or_path": MODEL_PARAMS["model_name_or_path"],
                    "model_revision": MODEL_PARAMS["model_revision"],
                    "do_sample": MODEL_PARAMS["do_sample"],
                    "temperature": MODEL_PARAMS["temperature"],
                    "top_p": MODEL_PARAMS["top_p"],
                    "max_new_tokens": MODEL_PARAMS["max_new_tokens"],
                    "selection_stratum": selection_stratum,
                    "transformation_method": transformation_method,
                    "source_prompt_sha256": src.get("source_prompt_sha256", ""),
                    "transformed_prompt_sha256": src.get("transformed_prompt_sha256", ""),
                    "source_prompt_tokens": src.get("source_prompt_tokens", ""),
                    "status": "planned",
                }
                rows.append(row)
    return rows


def write_extension_plan_md(
    source_examples: dict[str, dict],
    n_planned: int,
    ext_run_dir: Path,
    out_path: Path,
) -> None:
    lines = [
        "# Stage 4.8 Extension Plan",
        f"\n_Generated: {datetime.utcnow().isoformat()}Z_",
        "",
        "## Rationale",
        "",
        "The original Stage 4.8 run (60 generations: 4 goals × 3 conditions × 5 seeds)",
        "produced only 3 matched-outcome cells (cells with ≥1 success AND ≥1 failure).",
        "The threshold for behavior-conditioned direction extraction is 4 matched cells.",
        "",
        "Goals 0 and 2 showed intermediate success probability (0 < success_rate < 1 in at",
        "least one condition), making them the best candidates for producing matched cells",
        "with more seeds.",
        "",
        "## Extension Parameters",
        "",
        f"- **Target goals:** {', '.join(TARGET_GOALS)}",
        f"- **Conditions:** {', '.join(CONDITIONS)}",
        f"- **New seeds:** {EXTENSION_SEEDS[0]}–{EXTENSION_SEEDS[-1]}",
        f"- **Total new generations:** {n_planned}",
        "  (2 goals × 3 conditions × 10 seeds = 60)",
        "",
        "## Model Configuration (unchanged from original)",
        "",
        f"- Model: `{MODEL_PARAMS['model_name_or_path']}`",
        f"- Revision: `{MODEL_PARAMS['model_revision']}`",
        f"- `do_sample=True`, `temperature={MODEL_PARAMS['temperature']}`, `top_p={MODEL_PARAMS['top_p']}`",
        f"- `max_new_tokens={MODEL_PARAMS['max_new_tokens']}`, `enable_thinking=True`",
        "",
        "## Source Examples Selected",
        "",
        "| Goal | Source Example ID | Selection Stratum |",
        "|------|-----------------|------------------|",
    ]
    for gi, src in sorted(source_examples.items()):
        src_id = src.get("source_example_id", src.get("run_id", ""))
        stratum = src.get("selection_stratum", "unknown")
        lines.append(f"| {gi} | `{src_id}` | {stratum} |")

    lines += [
        "",
        "## Extension Run Directory",
        "",
        f"`{ext_run_dir}`",
        "",
        "## SLURM Command",
        "",
        "```bash",
        "# Submit extension job (2 goals as SLURM array tasks 0 and 2)",
        f"MANIFEST=\"{_REPO_ROOT}/outputs/stage4_8/runs/$(basename {ext_run_dir})/extension_manifest.jsonl\"",
        f"RUN_DIR=\"{ext_run_dir}\"",
        "sbatch \\",
        "  --array=0,2 \\",
        "  --export=ALL,RUN_DIR=\"$RUN_DIR\",MANIFEST=\"$MANIFEST\" \\",
        "  slurm_scripts/stage4_8_repeated_generations_array.slurm",
        "```",
        "",
        "> **Note:** The existing `run_repeated_generations.py` script is resume-safe.",
        "> It skips any run_id already present in `run_summary.jsonl`.",
        "> Point it at the extension manifest and the extension run dir.",
        "",
        "## After Running",
        "",
        "Run `analyze_stage48_extension.py` to combine original + extension and check threshold:",
        "```bash",
        "python -m poc_meeting.mahmood_48h_update.analyze_stage48_extension \\",
        f"    --output-dir {out_path.parent}",
        "```",
        "",
        "## Safety Constraints",
        "",
        "- Do NOT alter harmful target text in the prompts.",
        "- Prompts are referenced by source_example_id only; not printed in logs.",
        "- Output artifacts must not include raw harmful target text.",
    ]
    out_path.write_text("\n".join(lines))
    log.info("Wrote %s", out_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--s48-dir", type=Path,
                        default=_REPO_ROOT / "outputs/stage4_8/runs/run_array_20260611_0109")
    args = parser.parse_args(argv)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Load original manifest
    log.info("Loading original Stage 4.8 manifest...")
    manifest_rows = load_original_manifest(args.s48_dir)
    log.info("  Loaded %d manifest rows", len(manifest_rows))

    # Get source examples for target goals
    source_examples = get_source_examples_for_goals(manifest_rows, TARGET_GOALS)
    log.info("Source examples for goals %s: %d found", TARGET_GOALS, len(source_examples))

    if not source_examples:
        log.error("No source examples found for target goals. Check manifest path.")
        # Create minimal plan anyway
        source_examples = {g: {"goal_index": g, "source_example_id": f"goal_{g}_unknown",
                                "selection_stratum": "unknown"} for g in TARGET_GOALS}

    # Build extension manifest
    ext_rows = build_extension_manifest(source_examples)
    n_planned = len(ext_rows)
    log.info("Built extension manifest: %d planned generations", n_planned)

    # Create extension run dir
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    ext_run_dir = _REPO_ROOT / f"outputs/stage4_8/runs/run_array_extension_{ts}"
    ext_run_dir.mkdir(parents=True, exist_ok=True)
    log.info("Created extension run dir: %s", ext_run_dir)

    # Write extension manifest JSONL
    manifest_path = ext_run_dir / "extension_manifest.jsonl"
    with open(manifest_path, "w") as f:
        for r in ext_rows:
            f.write(json.dumps(r) + "\n")
    log.info("Wrote %s (%d entries)", manifest_path, n_planned)

    # Write status placeholder
    status = {
        "created_utc": datetime.utcnow().isoformat() + "Z",
        "planned": n_planned,
        "completed": 0,
        "threshold_target": 4,
        "current_matched_cells": 3,
        "target_goals": TARGET_GOALS,
        "extension_seeds": EXTENSION_SEEDS,
        "conditions": CONDITIONS,
        "status": "planned_not_started",
    }
    (ext_run_dir / "status.json").write_text(json.dumps(status, indent=2))

    # Write batch summary CSV
    batch_path = out / "stage48_extension_batch_summary.csv"
    fieldnames = ["goal_index", "source_example_id", "condition", "seed",
                  "transformation_method", "selection_stratum", "status"]
    with open(batch_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(ext_rows)
    log.info("Wrote %s", batch_path)

    # Write extension status JSON to output dir
    status_path = out / "stage48_extension_status.json"
    status_path.write_text(json.dumps(status, indent=2))
    log.info("Wrote %s", status_path)

    # Write extension plan MD
    plan_path = out / "stage48_extension_plan.md"
    write_extension_plan_md(source_examples, n_planned, ext_run_dir, plan_path)

    log.info("Extension plan ready. Run dir: %s", ext_run_dir)
    log.info("Submit with SLURM as described in stage48_extension_plan.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
