"""
Stage 1 — Build A/D/E/G manifests for the paired early-token expansion study.

Reads the canonical 220-row dataset `outputs/hijacking_baseline_gpt-o4-mini_1_11.jsonl`
(11 goal_index values x 20 attack_iterations each) and builds, per model
(qwen3, gemma4):

  Condition A — attack_prompt as-is, thinking ON  : 220 sources x 3 seeds = 660 rows
  Condition E — attack_prompt as-is, thinking OFF : 220 sources x 3 seeds = 660 rows
  Condition D — bare `goal` text, thinking ON      : 11 goals x 3 seeds   =  33 rows
  Condition G — bare `goal` text, thinking OFF     : 11 goals x 3 seeds   =  33 rows

Total = 1386 rows/model, 2772 rows across both models.

D/G sizing note (per approved plan): bare-goal text is identical across all 20
attack_iterations of a goal, so D/G use ONE canonical representative source per
goal_index rather than one per puzzle variant (which would 10x-inflate D/G for
no informational gain). The canonical representative for goal_index=gi is the
row with the lexicographically smallest (attack_iteration, conversation_id) in
the canonical dataset; its `source_example_id` is reused verbatim for D/G rows
of that goal (so D/G rows remain traceable to one real canonical row, rather
than a synthetic id). This is documented again in
docs/SLURM_AND_MODEL_AUDIT.md.

row_key = f"{model}|{goal_index}|{source_example_id}|{condition}|{seed}"

Output layout:
  outputs/stage_ae_early_token_expansion/full_<TIMESTAMP>/
    manifests/qwen3_ae_manifest.jsonl
    manifests/gemma4_ae_manifest.jsonl
    manifests/full_manifest.csv
    manifests/canonical_sources.csv
    config/resolved_run_config.json

Usage:
  python -m poc_stage_ae.build_ae_manifest [--timestamp YYYYMMDD_HHMMSS] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_CANONICAL_DATASET = _REPO_ROOT / "outputs" / "hijacking_baseline_gpt-o4-mini_1_11.jsonl"
_CANONICAL_SHA256 = "243e4cd1008f4d9beb4f33aa5a3da460b5fa25635db1fa633e6dda70ebf3b304"
_OUTPUT_BASE = _REPO_ROOT / "outputs" / "stage_ae_early_token_expansion"

_SEEDS = [201, 202, 203]
_AE_CONDITIONS = ["A", "E"]     # full attack_prompt, thinking on/off
_DG_CONDITIONS = ["D", "G"]     # bare goal text, thinking on/off
_ENABLE_THINKING = {"A": True, "D": True, "E": False, "G": False}
_TRANSFORMATION_METHOD = {
    "A": "identity_copy",
    "E": "identity_copy_thinking_disabled",
    "D": "deletion_only_bare_goal",
    "G": "deletion_only_bare_goal_thinking_disabled",
}

_MODEL_CONFIGS: dict[str, dict[str, Any]] = {
    "qwen3": {
        "model_name": "Qwen/Qwen3-14B",
        "model_revision": "40c069824f4251a91eefaf281ebe4c544efd3e18",
        "n_layers": 40,
        "d_model": 5120,
    },
    "gemma4": {
        "model_name": "google/gemma-4-E4B-it",
        "model_revision": None,
        "n_layers": 42,
        "d_model": 2560,
    },
}

_EXPECTED_ROWS_PER_MODEL = 1386
_EXPECTED_ROWS_TOTAL = 2772


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _source_example_id(row: dict) -> str:
    gi = row["goal_index"]
    ai = row["attack_iteration"]
    ci = row["conversation_id"]
    tm = row.get("target_model", "gpt-o4-mini")
    return f"goal_index={gi}|attack_iteration={ai}|conversation_id={ci}|target_model={tm}"


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(_REPO_ROOT),
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def _select_canonical_representatives(rows: list[dict]) -> dict[int, dict]:
    """One canonical representative row per goal_index: smallest (attack_iteration, conversation_id)."""
    by_goal: dict[int, list[dict]] = {}
    for r in rows:
        by_goal.setdefault(int(r["goal_index"]), []).append(r)
    reps: dict[int, dict] = {}
    for gi, grp in by_goal.items():
        grp_sorted = sorted(grp, key=lambda r: (int(r["attack_iteration"]), int(r["conversation_id"])))
        reps[gi] = grp_sorted[0]
    return reps


def build_manifest_for_model(
    model_key: str,
    canonical_rows: list[dict],
    canonical_reps: dict[int, dict],
) -> list[dict]:
    cfg = _MODEL_CONFIGS[model_key]
    manifest_rows: list[dict] = []

    # A / E — all 220 canonical sources x 3 seeds
    for row in canonical_rows:
        gi = int(row["goal_index"])
        sid = _source_example_id(row)
        attack_prompt = row["attack_prompt"]
        goal_text = row["goal"]
        for condition in _AE_CONDITIONS:
            for seed in _SEEDS:
                manifest_rows.append({
                    "row_key": f"{model_key}|{gi}|{sid}|{condition}|{seed}",
                    "model": model_key,
                    "model_name_or_path": cfg["model_name"],
                    "model_revision": cfg["model_revision"],
                    "goal_index": gi,
                    "goal": goal_text,
                    "source_example_id": sid,
                    "attack_iteration": row["attack_iteration"],
                    "conversation_id": row["conversation_id"],
                    "condition": condition,
                    "seed": seed,
                    "enable_thinking": _ENABLE_THINKING[condition],
                    "user_message_text": attack_prompt,
                    "transformation_method": _TRANSFORMATION_METHOD[condition],
                    "is_canonical_representative_row": False,
                })

    # D / G — one canonical representative per goal_index x 3 seeds
    for gi, rep_row in sorted(canonical_reps.items()):
        sid = _source_example_id(rep_row)
        goal_text = rep_row["goal"]
        for condition in _DG_CONDITIONS:
            for seed in _SEEDS:
                manifest_rows.append({
                    "row_key": f"{model_key}|{gi}|{sid}|{condition}|{seed}",
                    "model": model_key,
                    "model_name_or_path": cfg["model_name"],
                    "model_revision": cfg["model_revision"],
                    "goal_index": gi,
                    "goal": goal_text,
                    "source_example_id": sid,
                    "attack_iteration": rep_row["attack_iteration"],
                    "conversation_id": rep_row["conversation_id"],
                    "condition": condition,
                    "seed": seed,
                    "enable_thinking": _ENABLE_THINKING[condition],
                    "user_message_text": goal_text,
                    "transformation_method": _TRANSFORMATION_METHOD[condition],
                    "is_canonical_representative_row": True,
                })

    return manifest_rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", type=str, default=None,
                     help="Override run timestamp (format YYYYMMDD_HHMMSS). Default: generated now.")
    ap.add_argument("--dry-run", action="store_true", default=False,
                     help="Build in memory and validate counts but do not write files.")
    args = ap.parse_args(argv)

    if not _CANONICAL_DATASET.exists():
        print(f"ERROR: canonical dataset not found: {_CANONICAL_DATASET}", file=sys.stderr)
        return 1

    actual_sha256 = _sha256_file(_CANONICAL_DATASET)
    if actual_sha256 != _CANONICAL_SHA256:
        print(
            f"ERROR: canonical dataset sha256 mismatch.\n"
            f"  expected: {_CANONICAL_SHA256}\n"
            f"  actual:   {actual_sha256}\n"
            f"Refusing to build manifests from a changed/unexpected source file.",
            file=sys.stderr,
        )
        return 1

    canonical_rows = _load_jsonl(_CANONICAL_DATASET)
    if len(canonical_rows) != 220:
        print(f"ERROR: expected 220 canonical rows, found {len(canonical_rows)}", file=sys.stderr)
        return 1

    goal_indices = sorted(set(int(r["goal_index"]) for r in canonical_rows))
    if len(goal_indices) != 11:
        print(f"ERROR: expected 11 unique goal_index values, found {len(goal_indices)}: {goal_indices}", file=sys.stderr)
        return 1

    canonical_reps = _select_canonical_representatives(canonical_rows)
    assert len(canonical_reps) == 11, f"Expected 11 canonical representatives, got {len(canonical_reps)}"

    timestamp = args.timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = _OUTPUT_BASE / f"full_{timestamp}"
    manifests_dir = run_dir / "manifests"
    config_dir = run_dir / "config"

    all_rows_by_model: dict[str, list[dict]] = {}
    full_rows: list[dict] = []

    for model_key in ("qwen3", "gemma4"):
        rows = build_manifest_for_model(model_key, canonical_rows, canonical_reps)

        # --- hard assertions: exact counts, zero duplicate row_keys ---
        if len(rows) != _EXPECTED_ROWS_PER_MODEL:
            print(
                f"ERROR: {model_key} manifest has {len(rows)} rows, expected {_EXPECTED_ROWS_PER_MODEL}",
                file=sys.stderr,
            )
            return 1
        row_keys = [r["row_key"] for r in rows]
        if len(row_keys) != len(set(row_keys)):
            dupes = {k for k in row_keys if row_keys.count(k) > 1}
            print(f"ERROR: {model_key} manifest has duplicate row_keys: {sorted(dupes)[:10]}", file=sys.stderr)
            return 1

        n_a = sum(1 for r in rows if r["condition"] == "A")
        n_e = sum(1 for r in rows if r["condition"] == "E")
        n_d = sum(1 for r in rows if r["condition"] == "D")
        n_g = sum(1 for r in rows if r["condition"] == "G")
        assert n_a == 660, f"{model_key} A count = {n_a}, expected 660"
        assert n_e == 660, f"{model_key} E count = {n_e}, expected 660"
        assert n_d == 33, f"{model_key} D count = {n_d}, expected 33"
        assert n_g == 33, f"{model_key} G count = {n_g}, expected 33"

        all_rows_by_model[model_key] = rows
        full_rows.extend(rows)
        print(f"[{model_key}] {len(rows)} rows (A={n_a} E={n_e} D={n_d} G={n_g}) — OK")

    if len(full_rows) != _EXPECTED_ROWS_TOTAL:
        print(f"ERROR: combined manifest has {len(full_rows)} rows, expected {_EXPECTED_ROWS_TOTAL}", file=sys.stderr)
        return 1
    all_row_keys = [r["row_key"] for r in full_rows]
    if len(all_row_keys) != len(set(all_row_keys)):
        print("ERROR: duplicate row_keys across combined manifest", file=sys.stderr)
        return 1

    print(f"\nAll hard assertions passed: {_EXPECTED_ROWS_PER_MODEL}/model, {_EXPECTED_ROWS_TOTAL} total, 0 duplicate row_keys.")
    print(f"TIMESTAMP={timestamp}")

    if args.dry_run:
        print("[--dry-run] Skipping file writes.")
        return 0

    # --- write manifests ---
    for model_key, rows in all_rows_by_model.items():
        _write_jsonl(manifests_dir / f"{model_key}_ae_manifest.jsonl", rows)

    # full_manifest.csv (both models combined)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = list(full_rows[0].keys())
    with open(manifests_dir / "full_manifest.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in full_rows:
            writer.writerow(row)

    # canonical_sources.csv
    with open(manifests_dir / "canonical_sources.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "canonical_dataset_path", "canonical_dataset_sha256", "n_rows",
            "goal_index", "source_example_id", "attack_iteration", "conversation_id",
            "is_dg_canonical_representative",
        ])
        rep_sids = {_source_example_id(r) for r in canonical_reps.values()}
        for row in canonical_rows:
            sid = _source_example_id(row)
            writer.writerow([
                str(_CANONICAL_DATASET.relative_to(_REPO_ROOT)),
                _CANONICAL_SHA256,
                len(canonical_rows),
                row["goal_index"],
                sid,
                row["attack_iteration"],
                row["conversation_id"],
                sid in rep_sids,
            ])

    # config/resolved_run_config.json
    resolved_config = {
        "timestamp": timestamp,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "canonical_dataset_path": str(_CANONICAL_DATASET.relative_to(_REPO_ROOT)),
        "canonical_dataset_sha256": _CANONICAL_SHA256,
        "n_canonical_rows": len(canonical_rows),
        "n_goal_indices": len(goal_indices),
        "goal_indices": goal_indices,
        "seeds": _SEEDS,
        "conditions": {
            "A": {"prompt_source": "attack_prompt", "enable_thinking": True, "n_rows_per_model": 660},
            "E": {"prompt_source": "attack_prompt", "enable_thinking": False, "n_rows_per_model": 660},
            "D": {"prompt_source": "bare_goal", "enable_thinking": True, "n_rows_per_model": 33},
            "G": {"prompt_source": "bare_goal", "enable_thinking": False, "n_rows_per_model": 33},
        },
        "dg_canonical_representative_rule": (
            "one row per goal_index: smallest (attack_iteration, conversation_id) tuple "
            "in the canonical dataset; its source_example_id is reused for D/G rows"
        ),
        "models": _MODEL_CONFIGS,
        "expected_rows_per_model": _EXPECTED_ROWS_PER_MODEL,
        "expected_rows_total": _EXPECTED_ROWS_TOTAL,
        "run_dir": str(run_dir.relative_to(_REPO_ROOT)),
        "manifests": {
            "qwen3": str((manifests_dir / "qwen3_ae_manifest.jsonl").relative_to(_REPO_ROOT)),
            "gemma4": str((manifests_dir / "gemma4_ae_manifest.jsonl").relative_to(_REPO_ROOT)),
            "full_csv": str((manifests_dir / "full_manifest.csv").relative_to(_REPO_ROOT)),
            "canonical_sources_csv": str((manifests_dir / "canonical_sources.csv").relative_to(_REPO_ROOT)),
        },
    }
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(config_dir / "resolved_run_config.json", "w", encoding="utf-8") as f:
        json.dump(resolved_config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nRUN_DIR={run_dir}")
    print(f"Wrote manifests to {manifests_dir}")
    print(f"Wrote config to {config_dir / 'resolved_run_config.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
