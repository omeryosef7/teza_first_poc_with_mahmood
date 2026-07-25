"""§16/§31.3-B (Claude ext) — build the Phi-4-mini-reasoning mechanistic extraction manifest.

Mirrors the DeepSeek §16-B pipeline: turns the existing Phi-4 CoT-Hijacking ATTACK outputs
(`outputs/phase4_hf_local/phase4_cot_hf_microsoft_Phi-4-mini-reasoning_dev25.jsonl`) into a §9 extraction
manifest so run_ae_generation + replay_hidden_states can regenerate + capture residual streams for the
attack-success (D) vs attack-failure (C) groups. Emits the manifest + an extraction_tuples.txt
(goal_index:condition) for the array launcher. Reuses the manifest row schema used by qwen3/deepseek.

Usage:
  python scripts/build_phi4_mechanistic_manifest.py \
    --attack outputs/phase4_hf_local/phase4_cot_hf_microsoft_Phi-4-mini-reasoning_dev25.jsonl \
    --out-dir outputs/phase_phi4_cot
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _as_bool(v):
    return v is True or str(v).strip().lower() == "true"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--attack", required=True)
    ap.add_argument("--out-dir", default="outputs/phase_phi4_cot")
    ap.add_argument("--model", default="phi4", help="model family key (row_key prefix + 'model' field)")
    ap.add_argument("--model-name", default="microsoft/Phi-4-mini-reasoning")
    ap.add_argument("--source-tag", default=None, help="'source' field; default '<model>_cot_hijacking'")
    ap.add_argument("--base-seed", type=int, default=201)
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.attack) if l.strip()]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / f"{args.model}_mechanistic_manifest.jsonl"
    tuples = set()
    n_c = n_d = 0
    with open(manifest_path, "w") as fh:
        for i, r in enumerate(rows):
            success = _as_bool(r.get("is_success"))
            cond = "D" if success else "C"
            gi = int(r["goal_index"])
            src_id = r["task_id"]
            conv = r.get("conversation_id", "1")
            # row_key mirrors the deepseek convention: {model}|{goal_index}|{cond}|{source}|cot{conv}|{seed}
            seed = args.base_seed + i  # deterministic, unique per manifest row
            row_key = f"{args.model}|{gi}|{cond}|{src_id}|cot{conv}|{seed}"
            manifest_row = {
                "row_key": row_key,
                "model": args.model,
                "model_name_or_path": args.model_name,
                "model_revision": "main",
                "goal_index": gi,
                "goal": r["goal"],
                "task_id": src_id,
                "condition": cond,
                "seed": seed,
                "enable_thinking": True,
                "user_message_text": r["attack_prompt"],  # the CoT-Hijacking attack prompt (what Phi-4 answers)
                "success_label": success,                  # ORIGINAL gemini-judge label (re-scored later by StrongREJECT)
                "source": args.source_tag or f"{args.model}_cot_hijacking",
            }
            fh.write(json.dumps(manifest_row, ensure_ascii=False) + "\n")
            tuples.add((gi, cond))
            n_c += cond == "C"
            n_d += cond == "D"

    tuples_path = out_dir / "extraction_tuples.txt"
    with open(tuples_path, "w") as fh:
        for gi, cond in sorted(tuples):
            fh.write(f"{gi}:{cond}\n")

    print(f"[phi4-manifest] {len(rows)} rows -> {manifest_path} (C={n_c} D={n_d})")
    print(f"[phi4-manifest] {len(tuples)} tuples -> {tuples_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
