"""
Stage 4.9 — Build the generation manifest for goals 4–10 extended factorial.

Reads replication_prompts JSONL and creates the JSONL manifest for
run_repeated_generations.py.

Excludes condition A (reused from Stage 6 — no regeneration needed).
Generates D, E, F only: 14 sources × 3 conditions × 3 seeds = 126 rows.

Output:
  outputs/stage4_8_extended/{model}_manifest_goals4_10.jsonl
  outputs/stage4_8_extended/{model}_manifest_goals4_10_audit.json

Usage:
  python -m poc_stage4_8.build_extended_manifest
      [--model qwen3|gemma4|both]
      [--source-dir outputs/stage4_8_extended]
      [--output-dir outputs/stage4_8_extended]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SOURCE_DIR = _REPO_ROOT / "outputs" / "stage4_8_extended"
_OUTPUT_DIR = _REPO_ROOT / "outputs" / "stage4_8_extended"

_MODEL_CONFIGS = {
    "qwen3": {
        "model_name_or_path": "Qwen/Qwen3-14B",
        "model_revision": "40c069824f4251a91eefaf281ebe4c544efd3e18",
        "model_family": "qwen3",
        "conditions": ["D", "E", "F"],  # A reused from Stage 6
        "seeds": [101, 102, 103],
        "do_sample": True,
        "temperature": 0.7,
        "top_p": 0.95,
        "max_new_tokens": 32768,
    },
    "gemma4": {
        "model_name_or_path": "google/gemma-4-E4B-it",
        "model_revision": None,
        "model_family": "gemma4",
        "conditions": ["D", "E", "F"],  # A reused from Stage 6
        "seeds": [101, 102, 103],
        "do_sample": True,
        "temperature": 0.7,
        "top_p": 0.95,
        "max_new_tokens": 32768,
    },
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_manifest(
    model_key: str,
    source_dir: Path,
    output_dir: Path,
) -> list[dict]:
    goals_tag = "goals4_10"
    prompts_path = source_dir / f"{model_key}_replication_prompts_{goals_tag}.jsonl"
    if not prompts_path.exists():
        print(f"  Replication prompts not found: {prompts_path}")
        return []

    all_prompts = [
        json.loads(l) for l in prompts_path.read_text().strip().split("\n") if l.strip()
    ]
    cfg = _MODEL_CONFIGS[model_key]
    target_conditions = set(cfg["conditions"])

    # Filter to D/E/F only
    prompts = [p for p in all_prompts if p["condition"] in target_conditions]
    print(f"  {len(prompts)} prompt rows (D/E/F) from {len(all_prompts)} total")

    manifest_rows: list[dict] = []

    for p in prompts:
        source_id = p["source_example_id"]
        condition = p["condition"]
        goal_index = p["goal_index"]
        user_msg = p.get("user_message_text", "") or p.get("_user_message_text", "")
        enable_thinking = p.get("enable_thinking", True)
        goal_text = p.get("goal", "")

        if not user_msg:
            print(f"  WARNING: empty user_message for {source_id} cond={condition}")
            continue

        prompt_hash = _sha256(user_msg)

        for seed in cfg["seeds"]:
            safe_source_id = source_id.replace("|", "__")
            run_id = f"{safe_source_id}__cond_{condition}__seed_{seed}"

            row = {
                "run_id": run_id,
                "source_example_id": source_id,
                "goal_index": goal_index,
                "condition": condition,
                "seed": seed,
                "model_name_or_path": cfg["model_name_or_path"],
                "model_revision": cfg["model_revision"],
                "model_family": model_key,
                "enable_thinking": enable_thinking,
                "do_sample": cfg["do_sample"],
                "temperature": cfg["temperature"],
                "top_p": cfg["top_p"],
                "max_new_tokens": cfg["max_new_tokens"],
                "user_message_text": user_msg,
                "prompt_sha256": prompt_hash,
                "goal": goal_text,
            }
            manifest_rows.append(row)

    out_jsonl = output_dir / f"{model_key}_manifest_{goals_tag}.jsonl"
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for row in manifest_rows:
            f.write(json.dumps(row) + "\n")
    print(f"  Saved {len(manifest_rows)} manifest rows → {out_jsonl}")

    # Verify expected count: 14 sources × 3 conditions × 3 seeds = 126
    expected = 14 * 3 * 3
    if len(manifest_rows) != expected:
        print(f"  WARNING: expected {expected} rows, got {len(manifest_rows)}")
    else:
        print(f"  Row count OK: {len(manifest_rows)} = 14 sources × 3 conditions × 3 seeds")

    audit = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "model_family": model_key,
        "n_rows": len(manifest_rows),
        "conditions": sorted(target_conditions),
        "seeds": cfg["seeds"],
        "goals": sorted(set(r["goal_index"] for r in manifest_rows)),
        "model_name_or_path": cfg["model_name_or_path"],
        "per_condition_n": {
            c: sum(1 for r in manifest_rows if r["condition"] == c)
            for c in target_conditions
        },
    }
    out_audit = output_dir / f"{model_key}_manifest_{goals_tag}_audit.json"
    out_audit.write_text(json.dumps(audit, indent=2))
    print(f"  Audit → {out_audit}")

    return manifest_rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="both", choices=["qwen3", "gemma4", "both"])
    ap.add_argument("--source-dir", default=str(_SOURCE_DIR))
    ap.add_argument("--output-dir", default=str(_OUTPUT_DIR))
    args = ap.parse_args()

    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    models = ["qwen3", "gemma4"] if args.model == "both" else [args.model]
    for model_key in models:
        print(f"\n=== {model_key.upper()} ===")
        build_manifest(model_key, source_dir, output_dir)


if __name__ == "__main__":
    main()
