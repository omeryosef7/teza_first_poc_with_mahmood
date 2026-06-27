"""
Build condition-G manifests for goals 4-10 (Qwen3 and Gemma4).

Condition G = bare harmful goal + thinking DISABLED.
Reads D rows from the goals 4-10 generation manifests (which include
user_message_text) and creates paired G rows with the same
(source_example_id, seed, goal_index) tuples.

Outputs:
  outputs/stage4_8_extended/repeated_generation_manifest_cond_g_qwen3_goals4_10.jsonl
  outputs/stage4_8_extended/repeated_generation_manifest_cond_g_gemma4_goals4_10.jsonl

Usage:
  python -m poc_stage4_8.build_manifest_cond_g_goals4_10
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_QWEN3_MANIFEST = _REPO_ROOT / "outputs" / "stage4_8_extended" / "qwen3_manifest_goals4_10.jsonl"
_GEMMA4_MANIFEST = _REPO_ROOT / "outputs" / "stage4_8_extended" / "gemma4_manifest_goals4_10.jsonl"
_QWEN3_OUT = _REPO_ROOT / "outputs" / "stage4_8_extended" / "repeated_generation_manifest_cond_g_qwen3_goals4_10.jsonl"
_GEMMA4_OUT = _REPO_ROOT / "outputs" / "stage4_8_extended" / "repeated_generation_manifest_cond_g_gemma4_goals4_10.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _build_g_rows(manifest_path: Path, model_family: str) -> tuple[list[dict], list[str]]:
    """Build G condition rows from D rows in an existing goals 4-10 manifest."""
    rows = _load_jsonl(manifest_path)
    d_rows = [r for r in rows if r.get("condition") == "D"]
    if not d_rows:
        return [], [f"No D rows found in {manifest_path}"]

    g_rows = []
    errors = []
    for r in d_rows:
        sid = r.get("source_example_id", "")
        seed = r.get("seed")
        goal_index = r.get("goal_index")
        user_message = r.get("user_message_text", "")
        if not user_message:
            errors.append(f"Missing user_message_text for {sid} seed={seed}")
            continue

        safe_sid = sid.replace("|", "__")
        run_id = f"{safe_sid}__cond_G__seed_{seed}"
        prompt_hash = r.get("prompt_sha256") or r.get("prompt_hash", "")

        g_row = {
            "run_id": run_id,
            "source_example_id": sid,
            "goal_index": goal_index,
            "condition": "G",
            "seed": seed,
            "enable_thinking": False,
            "model_family": r.get("model_family", model_family),
            "model_name_or_path": r.get("model_name_or_path", ""),
            "do_sample": r.get("do_sample", True),
            "temperature": r.get("temperature", 0.7),
            "top_p": r.get("top_p", 0.95),
            "max_new_tokens": r.get("max_new_tokens", 32768),
            "prompt_hash": prompt_hash,
            "user_message_text": user_message,
        }
        if r.get("model_revision"):
            g_row["model_revision"] = r["model_revision"]
        g_rows.append(g_row)

    return g_rows, errors


def main() -> None:
    for manifest_path, out_path, model_family in [
        (_QWEN3_MANIFEST, _QWEN3_OUT, "qwen3"),
        (_GEMMA4_MANIFEST, _GEMMA4_OUT, "gemma4"),
    ]:
        if not manifest_path.exists():
            print(f"ERROR: manifest not found: {manifest_path}")
            sys.exit(1)

        g_rows, errors = _build_g_rows(manifest_path, model_family)
        if errors:
            print(f"ERRORS for {model_family}:")
            for e in errors:
                print(f"  {e}")
            sys.exit(1)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for row in g_rows:
                f.write(json.dumps(row) + "\n")

        goals = sorted(set(r["goal_index"] for r in g_rows))
        seeds = sorted(set(r["seed"] for r in g_rows))
        print(f"{model_family}: wrote {len(g_rows)} G rows → {out_path}")
        print(f"  goals: {goals}, seeds: {seeds}")

    print("\nDone. Next: submit SLURM jobs:")
    print("  sbatch slurm_scripts/stage4_8_cond_g_goals4_10_qwen3.slurm")
    print("  sbatch slurm_scripts/stage4_8_cond_g_goals4_10_gemma4.slurm")


if __name__ == "__main__":
    main()
