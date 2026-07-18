"""
Build a CoT-aligned manifest for experiment 5A (GCG CoT-prefix targeting).

Key insight: with enable_thinking=True, Qwen3's chat template ends with
<|im_start|>assistant\n and the model generates <think> as its FIRST token.
The current GCG target ("Sure, here is...") is placed right after the suffix,
misaligned with actual generation where <think>...thinking...</think> comes first.

This script produces an extended safe_target_prefix that includes the full
thinking-to-response sequence:
    <think>
    {COT_TEXT}
    </think>

    Sure, here is {original_target_tail}

Usage:
    python -m poc_stage_gcg_early.build_cot_target_manifest \\
        --input  outputs/stage_gcg_full/advbench_manifest_v1.jsonl \\
        --output outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl \\
        [--cot-text "I can help with this."]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_DEFAULT_INPUT = _REPO_ROOT / "outputs" / "stage_gcg_full" / "advbench_manifest_v1.jsonl"
_DEFAULT_OUTPUT = _REPO_ROOT / "outputs" / "stage_gcg_full" / "advbench_cot_target_manifest.jsonl"

# Generic compliance-signaling CoT text. Kept short to reduce target length
# (fewer tokens → easier to optimize). Must sound like Qwen3 is willing to help.
_DEFAULT_COT_TEXT = "Okay, I can help with this request."


def _build_cot_target(original_prefix: str, cot_text: str) -> str:
    """
    Wrap original_prefix in a full CoT-aligned target sequence.

    The original prefix is typically: "Sure, here is <task description>"
    We strip the leading "Sure, here is" and rebuild so the target becomes:
        <think>
        {cot_text}
        </think>

        Sure, here is {remainder}

    If the original prefix does not start with "Sure, here is", we use it as-is
    after the </think> block (preceded by a newline).
    """
    prefix = original_prefix.strip()

    # Normalise: "Sure, here is" and variations
    for lead in ("Sure, here is ", "Sure, here's ", "Sure, here are "):
        if prefix.lower().startswith(lead.lower()):
            remainder = prefix[len(lead):]
            return f"<think>\n{cot_text}\n</think>\n\nSure, here is {remainder}"

    # Fallback: keep original as response content
    return f"<think>\n{cot_text}\n</think>\n\n{prefix}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CoT-aligned GCG manifest (5A)")
    parser.add_argument("--input", type=Path, default=_DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--cot-text", type=str, default=_DEFAULT_COT_TEXT,
                        help="CoT thinking text to insert between <think> and </think>")
    parser.add_argument("--split", type=str, default=None,
                        help="Filter to this split only (default: include all splits)")
    parser.add_argument("--model-family", type=str, default=None,
                        help="Sprint 2 Track 3: override the 'model' field on output rows (e.g. "
                             "'deepseek_r1'). Default None = keep whatever the input rows already "
                             "have (backward compatible with existing callers).")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input manifest not found: {args.input}", flush=True)
        sys.exit(1)

    rows = [json.loads(l) for l in args.input.read_text().splitlines() if l.strip()]
    if args.split:
        rows = [r for r in rows if r.get("split") == args.split]

    print(f"[build_cot_manifest] Loaded {len(rows)} rows from {args.input}", flush=True)
    print(f"[build_cot_manifest] CoT text: {repr(args.cot_text)}", flush=True)

    out_rows = []
    for r in rows:
        orig = r.get("safe_target_prefix", "")
        new_target = _build_cot_target(orig, args.cot_text)
        out_r = dict(r)
        out_r["safe_target_prefix"] = new_target
        if args.model_family is not None:
            out_r["model"] = args.model_family
        out_r["cot_target"] = True
        out_r["cot_text"] = args.cot_text
        out_r["original_safe_target_prefix"] = orig
        out_rows.append(out_r)
        print(f"  {r['task_id']}: {repr(orig[:40])} -> {repr(new_target[:80])}", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        for row in out_rows:
            f.write(json.dumps(row) + "\n")

    sha = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(".sha256").write_text(sha + "\n")

    print(f"\n[build_cot_manifest] Written {len(out_rows)} rows to {args.output}", flush=True)
    print(f"[build_cot_manifest] SHA256: {sha}", flush=True)


if __name__ == "__main__":
    main()
