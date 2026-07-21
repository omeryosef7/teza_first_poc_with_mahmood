#!/usr/bin/env python3
"""Phase 3 (RESEARCH_PLAN_DISTILLING_JAILBREAKS.md sec 7) discrete-trigger optimization
driver, built on TROPT recipes (no optimizer logic reimplemented):

  --optimizer gcg     -> tropt.recipe_hub.gcg__zou2023        (PrefillCELoss, GCG)   B1/B2
  --optimizer mac     -> tropt.recipe_hub.mac__wang2024       (GCGPlus/MAC)          B3/B5
  --optimizer gcg_hij -> tropt.recipe_hub.gcg_hij__bentov2025 (GCG + AttentionEnhLoss) Phase-8 §12.4

Loads the target model ONCE (LMHFModel) and reuses it across all behaviors via the
recipe's model_obj= arg (avoids reloading Qwen3-14B per behavior). Reads behaviors from
our split manifests (data/manifests/*.csv). Resume-safe: skips task_ids already in the
output triggers.jsonl.

Thinking-model target (SKILL §7 / our prior 5A): prepend a think block to the affirmative
target so the optimizer chases a position the model actually writes to.

MUST run under the TROPT venv:
  TROPT/.venv/bin/python scripts/phase3_tropt_optimize.py \
      --model-name Qwen/Qwen3-14B --optimizer gcg --target-style empty_think \
      --manifest data/manifests/dev_train_20.csv --out-dir outputs/phase3_tropt/gcg_qwen3
Smoke on a tiny model first: --model-name google/gemma-3-270m-it --limit 1
  (gcg/gcg_hij hardcode steps; for a fast step-limited smoke use --optimizer mac --num-steps 5)
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def code_commit() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                       text=True).strip()
    except Exception:
        return "unknown"


def build_target(style: str, affirm: str) -> str:
    if style == "affirm":
        return affirm
    if style == "empty_think":
        return "<think>\n\n</think>\n\n" + affirm
    if style == "nonempty_think":
        return "<think>\nOkay, I can help with this request.\n</think>\n\n" + affirm
    raise ValueError(f"unknown target-style {style}")


def load_behaviors(manifest: Path):
    rows = []
    with open(manifest) as f:
        for r in csv.DictReader(f):
            rows.append((r["task_id"], r["category"], r["instruction"], r["target_prefix"]))
    return rows


def done_task_ids(out_jsonl: Path):
    done = set()
    if out_jsonl.exists():
        with open(out_jsonl) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        done.add(json.loads(line)["task_id"])
                    except Exception:
                        pass
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-name", default="Qwen/Qwen3-14B")
    ap.add_argument("--optimizer", choices=["gcg", "mac", "gcg_hij"], default="gcg")
    ap.add_argument("--target-style", choices=["affirm", "empty_think", "nonempty_think"],
                    default="empty_think")
    ap.add_argument("--manifest", default="data/manifests/dev_train_20.csv")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--num-steps", type=int, default=0,
                    help="MAC only (gcg/gcg_hij hardcode steps); 0=recipe default")
    ap.add_argument("--limit", type=int, default=0, help="first N behaviors; 0=all")
    args = ap.parse_args()

    # Import TROPT lazily so --help works without the venv.
    from tropt.model.huggingface.lm import LMHFModel
    from tropt.recipe_hub import gcg__zou2023, mac__wang2024
    from tropt.recipe_hub import gcg_hij__bentov2025

    behaviors = load_behaviors(ROOT / args.manifest)
    if args.limit:
        behaviors = behaviors[: args.limit]

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = out_dir / "triggers.jsonl"
    done = done_task_ids(out_jsonl)

    # Attention-based recipe requires eager attention + no prefix cache (SKILL §7).
    if args.optimizer == "gcg_hij":
        model = LMHFModel(model_name=args.model_name, use_eager_attention=True,
                          use_prefix_cache=False)
    else:
        model = LMHFModel(model_name=args.model_name, use_prefix_cache=True)

    commit = code_commit()
    n_done = 0
    for task_id, category, instruction, affirm in behaviors:
        if task_id in done:
            continue
        template = f"{instruction} {{{{OPTIMIZED_TRIGGER}}}}"
        target = build_target(args.target_style, affirm)
        t0 = time.time()
        if args.optimizer == "gcg":
            # gcg__zou2023 has no num_steps arg (hardcoded 500); --num-steps ignored here.
            result = gcg__zou2023(instruction=template, target_response=target,
                                  model_obj=model)
        elif args.optimizer == "mac":
            kw = {"num_steps": args.num_steps} if args.num_steps else {}
            result = mac__wang2024(instruction=template, target_response=target,
                                   model_obj=model, **kw)
        else:  # gcg_hij (no num_steps arg)
            result = gcg_hij__bentov2025(instruction=template, target_output=target,
                                         model_obj=model)
        row = {
            "task_id": task_id,
            "category": category,
            "instruction": instruction,
            "template": template,
            "target": target,
            "optimizer": args.optimizer,
            "target_style": args.target_style,
            "model": args.model_name,
            "best_trigger_str": result.best_trigger_str,
            "best_loss": float(result.best_loss),
            "runtime_s": round(time.time() - t0, 1),
            "code_commit": commit,
        }
        with open(out_jsonl, "a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        n_done += 1
        print(f"[phase3] {task_id} opt={args.optimizer} loss={row['best_loss']:.4f} "
              f"trigger={result.best_trigger_str!r} ({row['runtime_s']}s)", flush=True)

    print(f"[phase3] wrote {n_done} new triggers to {out_jsonl} "
          f"(skipped {len(done)} already done)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
