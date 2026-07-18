"""
Build CoT anchor manifests targeting different positions within the thinking block.

The standard CoT manifest uses: <think>\nOkay, I can help with this request.\n</think>\n\n{response}
This script creates variants that target earlier (or no) positions in the thinking block,
testing whether the precise anchor point within the CoT affects GCG optimization success.

Research motivation:
  - All Gemma4 GCG runs give 0% ASR despite λ=0.3 refusal-direction suppression.
  - Hypothesis: refusal is embedded *in* the thinking content. Bypassing or shortening
    the thinking target may let the optimizer find compliant suffixes more easily.
  - For Qwen3: ablation to understand how much of the CoT target is needed.

Variants:
  empty_think  <think>\n</think>\n\n{response}            — empty CoT, force immediate response
  tok1         <think>\nO                                  — just first token of thinking
  tok5         <think>\nOkay, I can help with             — first ~5 thinking tokens (no close tag)
  nocot        {response}                                  — no thinking block at all
               (for Qwen3, use advbench_manifest_v1.jsonl directly instead)

Usage:
  python scripts/build_cot_anchor_manifests.py \\
      --input outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl \\
      --model-family qwen3 \\
      --variants empty_think tok5 tok1 \\
      --output-dir outputs/stage_gcg_full/

  python scripts/build_cot_anchor_manifests.py \\
      --input outputs/stage_gcg_full/advbench_gemma4_cot_manifest_v2.jsonl \\
      --model-family gemma4 \\
      --variants empty_think tok5 tok1 \\
      --output-dir outputs/stage_gcg_full/

Output files (in --output-dir):
  {input_stem}_anchor_{variant}.jsonl

Submission examples after running this script:
  BASE=outputs/stage_gcg_full

  # Gemma4 empty-think + λ=0.3 + L31 (most promising for 0%-ASR Gemma4):
  sbatch --export=ALL,\\
    MANIFEST=${BASE}/advbench_gemma4_cot_manifest_v2_anchor_empty_think.jsonl,\\
    RUN_DIR=${BASE}/gcg_full_gemma4_9g_emptythink_L31 \\
    slurm_scripts/run_gcg_full_9g_gemma4.slurm

  # Qwen3 no-CoT + λ=0.3 (fills ablation gap — λ=0.3 without CoT, never tested):
  sbatch --export=ALL,\\
    MANIFEST=${BASE}/advbench_manifest_v1.jsonl,\\
    RUN_DIR=${BASE}/gcg_full_qwen3_9g_nocot_lambda03 \\
    slurm_scripts/run_gcg_full_9g_qwen3.slurm

  # Qwen3 empty-think + λ=0.3:
  sbatch --export=ALL,\\
    MANIFEST=${BASE}/advbench_cot_target_manifest_anchor_empty_think.jsonl,\\
    RUN_DIR=${BASE}/gcg_full_qwen3_9g_emptythink_lambda03 \\
    slurm_scripts/run_gcg_full_9g_qwen3.slurm
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

QWEN3_THINK_START = "<think>\n"
QWEN3_THINK_END = "\n</think>\n\n"
GEMMA4_THINK_START = "<|channel>thought\n"
GEMMA4_THINK_END = "\n<channel|>"

TOK5_TEXT = "Okay, I can help with"  # ~5 tokens; matches thinking start in standard manifests
TOK1_TEXT = "O"                       # single char ≈ first token


def modify_prefix(prefix: str, variant: str, model_family: str) -> str:
    if model_family == "qwen3":
        think_start = QWEN3_THINK_START
        think_end = QWEN3_THINK_END
    else:
        think_start = GEMMA4_THINK_START
        think_end = "\n<channel|>"  # no trailing \n\n here; Gemma4 has it in rest

    # Extract response part (after the closing tag)
    if variant in ("empty_think",):
        # Find the end of thinking block
        inner_end = prefix.find(think_end)
        if inner_end == -1:
            # No closing tag found — prefix is already inside thinking; can't make empty_think
            return prefix
        rest_after_thinking = prefix[inner_end + len(think_end):]
        if model_family == "qwen3":
            return f"{think_start}{think_end}{rest_after_thinking}"
        else:
            # Gemma4: think_end is "\n<channel|>"; response follows with "\n\n"
            return f"{think_start}{think_end}{rest_after_thinking}"

    elif variant == "tok5":
        return f"{think_start}{TOK5_TEXT}"

    elif variant == "tok1":
        return f"{think_start}{TOK1_TEXT}"

    elif variant == "nocot":
        # Strip everything up to and including the closing thinking tag
        inner_end = prefix.find(think_end)
        if inner_end == -1:
            return prefix
        rest = prefix[inner_end + len(think_end):]
        if model_family == "gemma4" and rest.startswith("\n\n"):
            rest = rest[2:]  # strip the leading \n\n that follows <channel|>
        return rest

    else:
        raise ValueError(f"Unknown variant: {variant}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CoT anchor manifests at different positions")
    parser.add_argument("--input", required=True, help="Source CoT manifest .jsonl")
    parser.add_argument("--model-family", choices=["qwen3", "gemma4"], required=True)
    parser.add_argument(
        "--variants", nargs="+",
        default=["empty_think", "tok5", "tok1"],
        choices=["empty_think", "tok5", "tok1", "nocot"],
        help="Which anchor variants to generate",
    )
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    src = Path(args.input)
    entries = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]
    print(f"Loaded {len(entries)} entries from {src}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = src.stem  # e.g. "advbench_cot_target_manifest"

    for variant in args.variants:
        modified = []
        for entry in entries:
            new_entry = dict(entry)
            try:
                new_entry["safe_target_prefix"] = modify_prefix(
                    entry["safe_target_prefix"], variant, args.model_family
                )
            except Exception as e:
                print(f"  WARNING {entry.get('task_id','?')}: {e}")
            new_entry["_anchor_variant"] = variant
            modified.append(new_entry)

        out_path = out_dir / f"{stem}_anchor_{variant}.jsonl"
        out_path.write_text("\n".join(json.dumps(e) for e in modified) + "\n")
        sample = modified[0]["safe_target_prefix"]
        print(f"  [{variant}] {len(modified)} entries → {out_path.name}")
        print(f"    sample: {repr(sample[:100])}")

    print("Done.")


if __name__ == "__main__":
    main()
