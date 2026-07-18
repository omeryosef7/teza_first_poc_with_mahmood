"""
Build a 520-behavior Gemma4 empty-think manifest for Track 10A.

Takes the base 520-behavior AdvBench manifest and wraps each safe_target_prefix
in Gemma4's empty thinking channel format:
  <|channel>thought\n<channel|>\n\n{response}

This bypasses the refusal-encoding thinking step (9G-G-EmptyThink finding: 2.7% ASR).
The 9G optimization was on 25 behaviors; 10A scales that suffix to all 520.

Usage:
    python scripts/build_gemma4_emptythink_full520_manifest.py
    # or with explicit args:
    python scripts/build_gemma4_emptythink_full520_manifest.py \
        --input outputs/stage_gcg_full/advbench_full520_manifest.jsonl \
        --output outputs/stage_gcg_full/advbench_gemma4_emptythink_full520_manifest.jsonl
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

_DEFAULT_INPUT = _REPO_ROOT / "outputs" / "stage_gcg_full" / "advbench_full520_manifest.jsonl"
_DEFAULT_OUTPUT = _REPO_ROOT / "outputs" / "stage_gcg_full" / "advbench_gemma4_emptythink_full520_manifest.jsonl"


def _build_gemma4_emptythink_target(original_prefix: str) -> str:
    """
    Wrap original_prefix in Gemma4 empty-think format.
    Empty thinking block means no refusal reasoning — suffix forces straight to response.
    """
    prefix = original_prefix.strip()
    for lead in ("Sure, here is ", "Sure, here's ", "Sure, here are "):
        if prefix.lower().startswith(lead.lower()):
            remainder = prefix[len(lead):]
            return f"<|channel>thought\n<channel|>\n\nSure, here is {remainder}"
    return f"<|channel>thought\n<channel|>\n\n{prefix}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Gemma4 empty-think 520-behavior manifest (10A)")
    parser.add_argument("--input", type=Path, default=_DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input not found: {args.input}", flush=True)
        sys.exit(1)

    rows = [json.loads(l) for l in args.input.read_text().splitlines() if l.strip()]
    print(f"[build_gemma4_emptythink_full520] Loaded {len(rows)} rows from {args.input}", flush=True)

    out_rows = []
    for r in rows:
        orig = r.get("safe_target_prefix", "")
        new_target = _build_gemma4_emptythink_target(orig)
        out_r = dict(r)
        out_r["safe_target_prefix"] = new_target
        out_r["original_safe_target_prefix"] = orig
        out_r["cot_target"] = True
        out_r["empty_think"] = True
        out_r["model"] = "gemma4"
        out_r["enable_thinking"] = True
        out_rows.append(out_r)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        for row in out_rows:
            f.write(json.dumps(row) + "\n")

    sha = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(".sha256").write_text(sha + "\n")

    print(f"[build_gemma4_emptythink_full520] Written {len(out_rows)} rows to {args.output}", flush=True)
    print(f"[build_gemma4_emptythink_full520] SHA256: {sha}", flush=True)
    print(f"[build_gemma4_emptythink_full520] Sample: {repr(out_rows[0]['safe_target_prefix'][:120])}", flush=True)
    print(f"[build_gemma4_emptythink_full520] Task IDs: {out_rows[0]['task_id']} ... {out_rows[-1]['task_id']}", flush=True)


if __name__ == "__main__":
    main()
