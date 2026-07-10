"""
Build a Gemma4 CoT-aligned manifest for experiment 6B.

Analogous to build_cot_target_manifest.py (5A for Qwen3), but uses Gemma4's
thinking channel format: <|channel>thought\n...\n<channel|>\n\n{response}

Key insight: 4C got 0% ASR because the teacher-forced target "Sure, here is..."
is misaligned — Gemma4 with enable_thinking=True generates <|channel>thought\n
as its FIRST tokens. Extending the target to include the thinking channel prefix
aligns the GCG loss with what the model actually generates.

Gemma4 thinking format (verified from generations):
  <|channel>thought\n{thinking}\n<channel|>\n\n{response}

Usage:
    python -m poc_stage_gcg_early.build_gemma4_cot_target_manifest \\
        --input  outputs/stage_gcg_full/advbench_gemma4_manifest_v1.jsonl \\
        --output outputs/stage_gcg_full/advbench_gemma4_cot_manifest.jsonl \\
        [--cot-text "Okay, I can help with this request."]
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
_DEFAULT_OUTPUT = _REPO_ROOT / "outputs" / "stage_gcg_full" / "advbench_gemma4_cot_manifest.jsonl"

# Short compliant-sounding thinking text. Gemma4 thinking blocks are typically long,
# but we use a short one to minimize target length (fewer tokens → easier to optimize).
_DEFAULT_COT_TEXT = "Okay, I can help with this request."


def _build_gemma4_cot_target(original_prefix: str, cot_text: str) -> str:
    """
    Wrap original_prefix in Gemma4's thinking channel format.

    Format: <|channel>thought\n{cot_text}\n<channel|>\n\n{response}

    The <|channel> and <channel|> are Gemma4 special tokens (IDs 100 and 101).
    """
    prefix = original_prefix.strip()

    for lead in ("Sure, here is ", "Sure, here's ", "Sure, here are "):
        if prefix.lower().startswith(lead.lower()):
            remainder = prefix[len(lead):]
            return f"<|channel>thought\n{cot_text}\n<channel|>\n\nSure, here is {remainder}"

    # Fallback: keep original as response content after thinking block
    return f"<|channel>thought\n{cot_text}\n<channel|>\n\n{prefix}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Gemma4 CoT-aligned GCG manifest (6B)")
    parser.add_argument("--input", type=Path, default=_DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--cot-text", type=str, default=_DEFAULT_COT_TEXT,
                        help="Thinking text inside <|channel>thought block")
    parser.add_argument("--split", type=str, default=None,
                        help="Filter to this split only (default: include all splits)")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input manifest not found: {args.input}", flush=True)
        print("Run first: python -m poc_stage_gcg_early.build_advbench_manifest --model gemma4", flush=True)
        sys.exit(1)

    rows = [json.loads(l) for l in args.input.read_text().splitlines() if l.strip()]
    if args.split:
        rows = [r for r in rows if r.get("split") == args.split]

    print(f"[build_gemma4_cot_manifest] Loaded {len(rows)} rows from {args.input}", flush=True)
    print(f"[build_gemma4_cot_manifest] CoT text: {repr(args.cot_text)}", flush=True)

    out_rows = []
    for r in rows:
        orig = r.get("safe_target_prefix", "")
        new_target = _build_gemma4_cot_target(orig, args.cot_text)
        out_r = dict(r)
        out_r["safe_target_prefix"] = new_target
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

    print(f"\n[build_gemma4_cot_manifest] Written {len(out_rows)} rows to {args.output}", flush=True)
    print(f"[build_gemma4_cot_manifest] SHA256: {sha}", flush=True)
    print(f"[build_gemma4_cot_manifest] Sample target: {repr(out_rows[0]['safe_target_prefix'][:120])}", flush=True)


if __name__ == "__main__":
    main()
