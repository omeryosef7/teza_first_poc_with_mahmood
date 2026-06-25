"""
Stage 4.9 — Select source prompts for goals 4–10 (and optionally extend goals 0–3).

Reads factorial_attack_dataset.jsonl (condition A, model_family=qwen3 or gemma4)
for the target goals, then selects 2 source prompts per goal using the interest-score
criterion: prefer examples nearest to SR=0.5 (most intermediate); if all binary
(0 or 1), select 1 success + 1 failure per goal.

Maps selected source_example_ids back to Stage 6 trace files to extract formatted
prompts and metadata.

Outputs:
  outputs/stage4_8_extended/qwen3_source_prompts_goals4_10.csv
  outputs/stage4_8_extended/gemma4_source_prompts_goals4_10.csv

Usage:
  python -m poc_stage4_8.select_all_goals_source_prompts
      [--goals 4,5,6,7,8,9,10]
      [--model qwen3|gemma4|both]
      [--n-per-goal 2]
      [--output-dir outputs/stage4_8_extended]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_FACTORIAL_DATASET = _REPO_ROOT / "outputs" / "stage4" / "factorial_attack_dataset.jsonl"
_STAGE6_QWEN = _REPO_ROOT / "outputs" / "stage6" / "all_traces_full_1_11"
_STAGE6_GEMMA = _REPO_ROOT / "outputs" / "stage6" / "gemma_traces_full_1_11_eos_fixed"
_OUTPUT_DIR = _REPO_ROOT / "outputs" / "stage4_8_extended"

_QWEN_FNAME_RE = re.compile(
    r"qwen3_14b_trace_goal_index_(\d+)_attack_iteration_(\d+)_conversation_id_(\d+)"
)
_GEMMA_FNAME_RE = re.compile(
    r"gemma_4_e4b_it_trace_goal_index_(\d+)_attack_iteration_(\d+)_conversation_id_(\d+)"
)

DEFAULT_GOALS = [4, 5, 6, 7, 8, 9, 10]
N_PER_GOAL = 2


def _f(x, default: float = float("nan")) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _interest_score(sr_score: float) -> float:
    if math.isnan(sr_score):
        return 1.0
    return abs(sr_score - 0.5)


def load_factorial_condition_a(model_family: str, goals: list[int]) -> dict[int, list[dict]]:
    """Return {goal_index: [rows]} for condition A, deduplicated by source_example_id."""
    rows = [
        json.loads(l)
        for l in _FACTORIAL_DATASET.read_text().strip().split("\n")
        if l.strip()
    ]
    by_goal: dict[int, dict[str, dict]] = {g: {} for g in goals}
    for r in rows:
        if r.get("model_family") != model_family:
            continue
        if r.get("condition") != "A":
            continue
        g = r.get("goal_index")
        if g not in goals:
            continue
        sid = r["source_example_id"]
        # Keep row with best (most intermediate) SR score
        if sid not in by_goal[g]:
            by_goal[g][sid] = r
        else:
            existing = _interest_score(_f(by_goal[g][sid].get("strongreject_score")))
            new = _interest_score(_f(r.get("strongreject_score")))
            if new < existing:
                by_goal[g][sid] = r
    return {g: list(v.values()) for g, v in by_goal.items()}


def select_per_goal(candidates: list[dict], n: int) -> list[dict]:
    """Select n source prompts per goal using interest-score criterion."""
    # Sort by interest score (ascending = most interesting first)
    by_interest = sorted(
        candidates,
        key=lambda r: (_interest_score(_f(r.get("strongreject_score"))), r.get("source_example_id", "")),
    )

    # If all scores are binary, pick 1 success + 1 failure (if both available)
    scores = [_f(r.get("strongreject_score")) for r in candidates]
    successes = [r for r in candidates if _f(r.get("strongreject_score")) >= 0.5]
    failures = [r for r in candidates if _f(r.get("strongreject_score")) < 0.5]
    all_binary = all(s in (0.0, 1.0) for s in scores if not math.isnan(s))

    if all_binary and n >= 2 and successes and failures:
        # Sort each group by conversation_id for determinism
        best_success = sorted(successes, key=lambda r: r.get("source_example_id", ""))[0]
        best_failure = sorted(failures, key=lambda r: r.get("source_example_id", ""))[0]
        selected = [best_success, best_failure][:n]
    else:
        selected = by_interest[:n]

    return selected


def build_stage6_index(traces_dir: Path, fname_re: re.Pattern) -> dict[str, Path]:
    """Build a lookup from source_example_id to trace Path."""
    idx = {}
    for f in traces_dir.glob("*.json"):
        m = fname_re.search(f.name)
        if not m:
            continue
        g, ai, cid = int(m.group(1)), int(m.group(2)), int(m.group(3))
        sid = f"goal_index={g}|attack_iteration={ai}|conversation_id={cid}|target_model=gpt-o4-mini"
        idx[sid] = f
    return idx


def extract_fields_from_trace(trace_path: Path, model_family: str) -> dict:
    """Return relevant fields from a Stage 6 trace."""
    d = json.loads(trace_path.read_text())
    sr = d.get("strongreject_result", {})

    # formatted prompt (full)
    formatted_prompt = None
    for field in ("saved_formatted_prompt", "formatted_prompt", "prompt_text"):
        v = d.get(field)
        if v and isinstance(v, str) and len(v) > 20:
            formatted_prompt = v
            break
    if formatted_prompt is None:
        toks = d.get("prompt_token_strings")
        if toks and isinstance(toks, list):
            formatted_prompt = "".join(toks)

    # attack_prompt (user message content for condition A)
    attack_prompt = sr.get("attack_prompt", "") or ""

    # goal (bare harmful request for condition D)
    goal_text = sr.get("goal", "") or ""

    # think_token_count from think_text
    think_text = d.get("think_text", "") or ""
    think_token_count = len(think_text.split()) if think_text else None

    return {
        "formatted_prompt": formatted_prompt or "",
        "attack_prompt": attack_prompt,
        "goal": goal_text,
        "think_token_count": think_token_count,
        "finish_reason": d.get("generation_finish_reason", "unknown"),
        "seg_status": d.get("thinking_segmentation_status", "unknown"),
    }


def run_selection(
    model_family: str,
    goals: list[int],
    n_per_goal: int,
    stage6_dir: Path,
    fname_re: re.Pattern,
    output_dir: Path,
) -> list[dict]:
    by_goal = load_factorial_condition_a(model_family, goals)

    # Build Stage 6 trace index
    print(f"  Building {model_family} trace index from {stage6_dir} …")
    trace_idx = build_stage6_index(stage6_dir, fname_re)
    print(f"  Found {len(trace_idx)} Stage 6 traces")

    selected_rows = []
    for g in sorted(goals):
        cands = by_goal[g]
        if not cands:
            print(f"  goal {g}: NO CANDIDATES")
            continue

        chosen = select_per_goal(cands, n_per_goal)
        print(f"  goal {g}: {len(cands)} candidates → {len(chosen)} selected")

        for r in chosen:
            sid = r["source_example_id"]
            trace_path = trace_idx.get(sid)
            if trace_path is None:
                print(f"    WARNING: trace not found for {sid}")
                trace_fields = {
                    "formatted_prompt": "", "attack_prompt": "",
                    "goal": "", "think_token_count": None,
                    "finish_reason": r.get("finish_reason", "unknown"),
                    "seg_status": r.get("thinking_segmentation_status", "unknown"),
                }
            else:
                trace_fields = extract_fields_from_trace(trace_path, model_family)
                if not trace_fields["formatted_prompt"]:
                    print(f"    WARNING: could not extract prompt from {trace_path.name}")
                if not trace_fields["attack_prompt"]:
                    print(f"    WARNING: no attack_prompt in strongreject_result for {trace_path.name}")

            # Parse goal / attack_iter / conv_id from source_example_id
            parts = dict(p.split("=", 1) for p in sid.split("|"))
            row = {
                "goal_index": g,
                "source_example_id": sid,
                "attack_iteration": int(parts.get("attack_iteration", -1)),
                "conversation_id": int(parts.get("conversation_id", -1)),
                "sr_success": r.get("sr_success"),
                "strongreject_score": r.get("strongreject_score"),
                "think_token_count": trace_fields["think_token_count"],
                "finish_reason": trace_fields["finish_reason"],
                "thinking_segmentation_status": trace_fields["seg_status"],
                "source_stage": r.get("source_stage", f"stage6_{model_family}"),
                "formatted_prompt": trace_fields["formatted_prompt"],
                "attack_prompt": trace_fields["attack_prompt"],
                "goal": trace_fields["goal"],
            }
            selected_rows.append(row)
            sr_val = r.get('strongreject_score')
            print(
                f"    → {sid}  sr={sr_val:.2f}  "
                f"success={r.get('sr_success')}  "
                f"attack_prompt={len(trace_fields['attack_prompt'])}chars  "
                f"goal={trace_fields['goal'][:40]!r}"
            )

    # Save CSV (without large text fields to keep it readable)
    model_tag = model_family
    goals_tag = f"goals{min(goals)}_{max(goals)}"
    out_csv = output_dir / f"{model_tag}_source_prompts_{goals_tag}.csv"
    fieldnames = [
        "goal_index", "source_example_id", "attack_iteration", "conversation_id",
        "sr_success", "strongreject_score", "think_token_count", "finish_reason",
        "thinking_segmentation_status", "source_stage",
    ]
    csv_rows = [{k: r[k] for k in fieldnames} for r in selected_rows]
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(csv_rows)
    print(f"\n  Saved {len(selected_rows)} rows (CSV) → {out_csv}")

    # Save manifest JSON (includes full attack_prompt + goal for manifest building)
    out_manifest = output_dir / f"{model_tag}_source_prompts_{goals_tag}_manifest.json"
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "model_family": model_family,
        "goals": goals,
        "n_per_goal": n_per_goal,
        "n_selected": len(selected_rows),
        "output_csv": str(out_csv.relative_to(_REPO_ROOT)),
        "selected": [
            {
                "source_example_id": r["source_example_id"],
                "goal_index": r["goal_index"],
                "attack_prompt": r["attack_prompt"],
                "goal": r["goal"],
                "sr_score": r.get("strongreject_score"),
                "trace_path": "",
            }
            for r in selected_rows
        ],
    }
    out_manifest.write_text(json.dumps(manifest, indent=2))
    print(f"  Saved manifest → {out_manifest}")

    return selected_rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--goals", default=",".join(str(g) for g in DEFAULT_GOALS),
                    help="Comma-separated goal indices (default: 4,5,6,7,8,9,10)")
    ap.add_argument("--model", default="both", choices=["qwen3", "gemma4", "both"])
    ap.add_argument("--n-per-goal", type=int, default=N_PER_GOAL)
    ap.add_argument("--output-dir", default=str(_OUTPUT_DIR))
    args = ap.parse_args()

    goals = [int(g.strip()) for g in args.goals.split(",")]
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    models = ["qwen3", "gemma4"] if args.model == "both" else [args.model]

    for model in models:
        print(f"\n=== {model.upper()} goals {goals} ===")
        stage6_dir = _STAGE6_QWEN if model == "qwen3" else _STAGE6_GEMMA
        fname_re = _QWEN_FNAME_RE if model == "qwen3" else _GEMMA_FNAME_RE

        if not stage6_dir.exists():
            print(f"  WARNING: {stage6_dir} not found, skipping")
            continue

        run_selection(
            model_family=model,
            goals=goals,
            n_per_goal=args.n_per_goal,
            stage6_dir=stage6_dir,
            fname_re=fname_re,
            output_dir=out_dir,
        )


if __name__ == "__main__":
    main()
