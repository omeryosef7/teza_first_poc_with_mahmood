"""
Stage 4.8 — Build Gemma4 factorial replication prompts (conditions A, D, E, F).

For each of the 4 selected Gemma4 source prompts:
  A — full attack_prompt (identity copy), enable_thinking=True
  D — bare harmful goal text only (direct harmful request), enable_thinking=True
  E — full attack_prompt, enable_thinking=False
  F — length-matched benign wrapper (harmless prompts concatenated), enable_thinking=True

Token counting uses the Gemma4 tokenizer (CPU, no GPU required).
The tokenizer is loaded once from the HF hub (fast, ~1 min if cached).

Output:
  outputs/stage4_8_gemma/replication_prompts.jsonl  (4 × 4 = 16 rows)
  outputs/stage4_8_gemma/replication_prompts_audit.json

Usage:
  python -m poc_stage4_8.build_gemma4_replication_prompts
      [--source-manifest outputs/stage4_8_gemma/source_prompt_selection_manifest.json]
      [--output-dir outputs/stage4_8_gemma]
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

_SOURCE_MANIFEST = _REPO_ROOT / "outputs" / "stage4_8_gemma" / "source_prompt_selection_manifest.json"
_OUTPUT_DIR = _REPO_ROOT / "outputs" / "stage4_8_gemma"
_MODEL_NAME = "google/gemma-4-E4B-it"
_CONDITIONS = ["A", "D", "E", "F"]
_ENABLE_THINKING = {"A": True, "D": True, "E": False, "F": True}


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
    """Concatenate harmless prompts until approximately matching target_token_count.

    Returns (text, actual_token_count, length_match_ratio).
    """
    # Use a deterministic hash of source_id to select a starting offset
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


def build_prompts(
    source_manifest_path: Path,
    output_dir: Path,
) -> list[dict]:
    print("Loading source manifest...")
    with open(source_manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    selected = manifest["selected"]
    print(f"Loading Gemma4 tokenizer from {_MODEL_NAME} ...")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        _MODEL_NAME,
        trust_remote_code=True,
    )
    print("Tokenizer loaded.")

    print("Loading harmless prompts for condition F...")
    harmless_prompts = _load_harmless_prompts()
    print(f"Loaded {len(harmless_prompts)} harmless prompts.")

    rows: list[dict] = []

    for source in selected:
        source_example_id = source["source_example_id"]
        goal_index = source["goal_index"]
        attack_prompt = source["attack_prompt"]
        goal_text = source["goal"]

        source_token_count = _count_tokens(tokenizer, attack_prompt)
        source_sha256 = _sha256(attack_prompt)

        print(f"\nProcessing goal={goal_index} source_id={source_example_id}")
        print(f"  attack_prompt: {source_token_count} tokens, {len(attack_prompt)} chars")

        for condition in _CONDITIONS:
            enable_thinking = _ENABLE_THINKING[condition]

            if condition == "A":
                user_msg = attack_prompt
                transformation_method = "identity_copy"
                benign_wrapper_source_ids = []
            elif condition == "D":
                user_msg = goal_text
                transformation_method = "deletion_only_bare_goal"
                benign_wrapper_source_ids = []
            elif condition == "E":
                user_msg = attack_prompt
                transformation_method = "identity_copy_thinking_disabled"
                benign_wrapper_source_ids = []
            elif condition == "F":
                user_msg, _, _ = _build_benign_length_match(
                    tokenizer, source_token_count, harmless_prompts, source_example_id
                )
                transformation_method = "benign_wrapper_length_matched"
                benign_wrapper_source_ids = []  # could enumerate if needed
            else:
                raise ValueError(f"Unknown condition: {condition}")

            transformed_token_count = _count_tokens(tokenizer, user_msg)
            length_match_ratio = (
                transformed_token_count / source_token_count
                if source_token_count > 0
                else 1.0
            )

            row = {
                "source_example_id": source_example_id,
                "goal_index": goal_index,
                "condition": condition,
                "enable_thinking": enable_thinking,
                "transformation_method": transformation_method,
                "source_prompt_tokens": source_token_count,
                "transformed_prompt_tokens": transformed_token_count,
                "length_match_ratio": round(length_match_ratio, 4),
                "source_prompt_sha256": source_sha256,
                "transformed_prompt_sha256": _sha256(user_msg),
                "user_message_text": user_msg,
                "_user_message_text": user_msg,  # mirror field used by runner
                "_enable_thinking": enable_thinking,
                "_source_example_id": source_example_id,
                "model_family": "gemma4",
                "goal": goal_text,
            }
            rows.append(row)
            print(
                f"  cond={condition}: {transformed_token_count} tokens "
                f"ratio={length_match_ratio:.2f} "
                f"enable_thinking={enable_thinking}"
            )

    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", default=str(_SOURCE_MANIFEST))
    parser.add_argument("--output-dir", default=str(_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = build_prompts(
        source_manifest_path=Path(args.source_manifest),
        output_dir=output_dir,
    )

    # Validate
    assert len(rows) == 16, f"Expected 16 rows (4 sources × 4 conditions), got {len(rows)}"
    conditions_seen = set(r["condition"] for r in rows)
    assert conditions_seen == {"A", "D", "E", "F"}, f"Missing conditions: {conditions_seen}"

    out_path = output_dir / "replication_prompts.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    audit = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "n_rows": len(rows),
        "conditions": sorted(conditions_seen),
        "goals": sorted(set(str(r["goal_index"]) for r in rows)),
        "per_condition_token_counts": {
            cond: [r["transformed_prompt_tokens"] for r in rows if r["condition"] == cond]
            for cond in _CONDITIONS
        },
    }
    audit_path = output_dir / "replication_prompts_audit.json"
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    print(f"\nWrote {len(rows)} rows to {out_path}")
    print(f"Audit → {audit_path}")


if __name__ == "__main__":
    main()
