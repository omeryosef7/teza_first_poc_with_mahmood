"""
Stage 4.9 — Build replication prompts (A/D/E/F) for goals 4–10 extended factorial.

Reads the source_prompts manifest JSON (from select_all_goals_source_prompts.py)
and generates condition-transformed user messages:
  A — full attack_prompt, enable_thinking=True
  D — bare harmful goal text only, enable_thinking=True
  E — full attack_prompt, enable_thinking=False
  F — length-matched benign wrapper (harmless prompts concatenated), enable_thinking=True

Token counting uses the model tokenizer (CPU, no GPU required).

Output (per model):
  outputs/stage4_8_extended/{model}_replication_prompts_goals4_10.jsonl
  outputs/stage4_8_extended/{model}_replication_prompts_goals4_10_audit.json

Usage:
  python -m poc_stage4_8.build_extended_replication_prompts
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
        "model_name": "Qwen/Qwen3-14B",
        "conditions": ["A", "D", "E", "F"],
        "enable_thinking": {"A": True, "D": True, "E": False, "F": True},
        "seeds": [101, 102, 103],
    },
    "gemma4": {
        "model_name": "google/gemma-4-E4B-it",
        "conditions": ["A", "D", "E", "F"],
        "enable_thinking": {"A": True, "D": True, "E": False, "F": True},
        "seeds": [101, 102, 103],
    },
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _count_tokens(tokenizer, text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


def _load_harmless_prompts() -> list[str]:
    from poc_stage4.default_prompts import load_prompt_sets
    _, harmless_train, _ = load_prompt_sets(num_harmful=16, num_harmless=200, seed=42)
    return harmless_train


def _build_benign_length_match(
    tokenizer,
    target_token_count: int,
    harmless_prompts: list[str],
    source_example_id: str,
) -> tuple[str, int, float]:
    offset = int(_sha256(source_example_id)[:8], 16) % len(harmless_prompts)
    rotated = harmless_prompts[offset:] + harmless_prompts[:offset]

    chunks: list[str] = []
    current_tokens = 0
    for prompt in rotated:
        prompt_tokens = _count_tokens(tokenizer, prompt)
        if current_tokens + prompt_tokens > target_token_count * 1.1 and chunks:
            break
        chunks.append(prompt)
        current_tokens += prompt_tokens
        if current_tokens >= target_token_count * 0.9:
            break

    if not chunks:
        chunks = [rotated[0]]
        current_tokens = _count_tokens(tokenizer, chunks[0])

    text = "\n\n".join(chunks)
    ratio = current_tokens / target_token_count if target_token_count > 0 else 1.0
    return text, current_tokens, ratio


def build_prompts_for_model(
    model_key: str,
    source_dir: Path,
    output_dir: Path,
) -> list[dict]:
    goals_tag = "goals4_10"
    manifest_path = source_dir / f"{model_key}_source_prompts_{goals_tag}_manifest.json"
    if not manifest_path.exists():
        print(f"  Manifest not found: {manifest_path}")
        return []

    manifest = json.loads(manifest_path.read_text())
    selected = manifest["selected"]
    cfg = _MODEL_CONFIGS[model_key]
    conditions = cfg["conditions"]
    enable_thinking_map = cfg["enable_thinking"]
    model_name = cfg["model_name"]

    print(f"  Loading tokenizer for {model_name} ...")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    print(f"  Tokenizer loaded. {len(selected)} source prompts.")

    print(f"  Loading harmless prompts for condition F ...")
    harmless_prompts = _load_harmless_prompts()

    rows: list[dict] = []

    for source in selected:
        source_id = source["source_example_id"]
        goal_index = source["goal_index"]
        attack_prompt = source.get("attack_prompt", "")
        goal_text = source.get("goal", "")

        if not attack_prompt:
            print(f"  WARNING: empty attack_prompt for {source_id}, skipping")
            continue
        if not goal_text:
            print(f"  WARNING: empty goal for {source_id}")

        source_token_count = _count_tokens(tokenizer, attack_prompt)
        source_sha256 = _sha256(attack_prompt)

        print(f"\n  goal={goal_index} {source_id[-30:]}")
        print(f"    attack_prompt: {source_token_count} tokens, {len(attack_prompt)} chars")

        for condition in conditions:
            enable_thinking = enable_thinking_map[condition]

            if condition == "A":
                user_msg = attack_prompt
                transformation_method = "identity_copy"
            elif condition == "D":
                user_msg = goal_text
                transformation_method = "deletion_only_bare_goal"
            elif condition == "E":
                user_msg = attack_prompt
                transformation_method = "identity_copy_thinking_disabled"
            elif condition == "F":
                user_msg, _, _ = _build_benign_length_match(
                    tokenizer, source_token_count, harmless_prompts, source_id
                )
                transformation_method = "benign_wrapper_length_matched"
            else:
                raise ValueError(f"Unknown condition: {condition}")

            transformed_token_count = _count_tokens(tokenizer, user_msg)
            length_match_ratio = (
                transformed_token_count / source_token_count
                if source_token_count > 0
                else 1.0
            )

            row = {
                "source_example_id": source_id,
                "goal_index": goal_index,
                "condition": condition,
                "model_family": model_key,
                "enable_thinking": enable_thinking,
                "transformation_method": transformation_method,
                "source_prompt_tokens": source_token_count,
                "transformed_prompt_tokens": transformed_token_count,
                "length_match_ratio": round(length_match_ratio, 4),
                "source_prompt_sha256": source_sha256,
                "transformed_prompt_sha256": _sha256(user_msg),
                "user_message_text": user_msg,
                "_user_message_text": user_msg,
                "_enable_thinking": enable_thinking,
                "_source_example_id": source_id,
                "goal": goal_text,
            }
            rows.append(row)
            print(
                f"    cond={condition}: {transformed_token_count} tokens "
                f"ratio={length_match_ratio:.2f} "
                f"enable_thinking={enable_thinking}"
            )

    out_jsonl = output_dir / f"{model_key}_replication_prompts_{goals_tag}.jsonl"
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    print(f"\n  Saved {len(rows)} rows → {out_jsonl}")

    audit = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "model_family": model_key,
        "n_sources": len(selected),
        "n_rows": len(rows),
        "conditions": conditions,
        "goals": sorted(set(r["goal_index"] for r in rows)),
        "per_condition_token_counts": {
            cond: [r["transformed_prompt_tokens"] for r in rows if r["condition"] == cond]
            for cond in conditions
        },
    }
    out_audit = output_dir / f"{model_key}_replication_prompts_{goals_tag}_audit.json"
    out_audit.write_text(json.dumps(audit, indent=2))
    print(f"  Audit → {out_audit}")

    return rows


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
        build_prompts_for_model(model_key, source_dir, output_dir)


if __name__ == "__main__":
    main()
