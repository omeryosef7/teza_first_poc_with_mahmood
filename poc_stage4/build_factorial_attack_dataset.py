"""
Build a unified factorial attack dataset by consolidating all condition data
across models, stages, and seeds into a single JSONL file.

Input sources:
  1. Stage 4.7 Qwen3  — outputs/stage4_7/runs/run_array_20260610_1442/run_summary.jsonl
                         (48 rows, A/D/E/F, greedy seed=0)
  2. Stage 4.8 Qwen3  — outputs/stage4_8/runs/run_combined_all_goals/run_summary.jsonl
                         (180 rows, A/D/F, stochastic)
  3. Stage 4.8 cond-E — outputs/stage4_8/runs/run_cond_e_*/run_summary.jsonl
                         (20 rows, E, stochastic)
  4. Stage 6 Qwen3    — outputs/stage6/all_traces_full_1_11/   (220 traces, cond A)
  5. Stage 6 Gemma4   — outputs/stage6/gemma_traces_full_1_11_eos_fixed/ (220 traces, cond A)
  6. Stage 4.8 Gemma4 — outputs/stage4_8_gemma/runs/run_*/run_summary.jsonl
                         (48 rows, A/D/E/F, stochastic)

Output schema (one row per generation):
  model_family, source_example_id, goal_index, condition, seed, do_sample,
  enable_thinking, sr_success, strongreject_score, think_token_count,
  finish_reason, thinking_segmentation_status, source_stage, is_valid

Usage:
  python -m poc_stage4.build_factorial_attack_dataset
      [--output-dir outputs/stage4]
      [--stage47-run-dir outputs/stage4_7/runs/run_array_20260610_1442]
      [--stage48-run-dir outputs/stage4_8/runs/run_combined_all_goals]
      [--cond-e-run-dir outputs/stage4_8/runs/run_cond_e_<TS>]   # auto-discover if omitted
      [--gemma-run-dir outputs/stage4_8_gemma/runs/run_<TS>]    # auto-discover if omitted
      [--include-stage6]   # include 220-example A-only traces (default: True)
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_STAGE47_RUN = _REPO_ROOT / "outputs" / "stage4_7" / "runs" / "run_array_20260610_1442"
_STAGE48_RUN = _REPO_ROOT / "outputs" / "stage4_8" / "runs" / "run_combined_all_goals"
_STAGE6_QWEN = _REPO_ROOT / "outputs" / "stage6" / "all_traces_full_1_11"
_STAGE6_GEMMA = _REPO_ROOT / "outputs" / "stage6" / "gemma_traces_full_1_11_eos_fixed"

_GEMMA_FNAME_RE = re.compile(
    r"gemma_4_e4b_it_trace_goal_index_(\d+)_attack_iteration_(\d+)_conversation_id_(\d+)_target_model_(.+)\.json$"
)
_QWEN_FNAME_RE = re.compile(
    r"qwen3_14b_trace_goal_index_(\d+)_attack_iteration_(\d+)_conversation_id_(\d+)_target_model_(.+)\.json$"
)


def _f(x, default=None):
    if x is None:
        return default
    try:
        v = float(x)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return default


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _auto_discover_run_dir(parent: Path, pattern: str) -> Path | None:
    """Find the most recently modified subdirectory matching pattern."""
    matches = sorted(parent.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def _discover_all_run_dirs(parent: Path, pattern: str) -> list[Path]:
    """Find ALL subdirectories matching pattern (SLURM array tasks write to separate dirs)."""
    return sorted(parent.glob(pattern), key=lambda p: p.stat().st_mtime)


def _make_row(
    model_family: str,
    source_example_id: str,
    goal_index,
    condition: str,
    seed,
    do_sample: bool,
    enable_thinking: bool,
    sr_success,
    strongreject_score,
    think_token_count,
    finish_reason: str,
    thinking_segmentation_status: str,
    source_stage: str,
) -> dict:
    # Condition E (thinking disabled): not_present / no_thought_channel are expected
    if not enable_thinking:
        valid_seg = thinking_segmentation_status in (
            "not_present", "no_thought_channel", "parsed_from_think_tags",
        )
    else:
        valid_seg = thinking_segmentation_status in (
            "parsed_from_think_tags",
            "parsed_from_thought_channel",
        )
    is_valid = valid_seg and finish_reason != "error"
    return {
        "model_family": model_family,
        "source_example_id": source_example_id,
        "goal_index": int(goal_index) if goal_index is not None else None,
        "condition": condition,
        "seed": int(seed) if seed is not None else None,
        "do_sample": do_sample,
        "enable_thinking": enable_thinking,
        "sr_success": bool(sr_success) if sr_success is not None else None,
        "strongreject_score": _f(strongreject_score),
        "think_token_count": int(think_token_count) if think_token_count is not None else None,
        "finish_reason": finish_reason,
        "thinking_segmentation_status": thinking_segmentation_status,
        "source_stage": source_stage,
        "is_valid": is_valid,
        "is_censored": finish_reason == "max_new_tokens",
    }


def load_stage47_qwen3(run_dir: Path) -> list[dict]:
    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        print(f"  WARNING: {summary_path} not found, skipping stage4_7")
        return []
    rows = _load_jsonl(summary_path)
    out = []
    for r in rows:
        sr = r.get("sr_success")
        if sr is None:
            sr = r.get("strongreject_is_success")
        out.append(_make_row(
            model_family="qwen3",
            source_example_id=r["source_example_id"],
            goal_index=r.get("goal_index"),
            condition=r["condition"],
            seed=r.get("seed", 0),
            do_sample=bool(r.get("do_sample", False)),
            enable_thinking=bool(r.get("enable_thinking", True)),
            sr_success=sr,
            strongreject_score=r.get("strongreject_score"),
            think_token_count=r.get("think_token_count"),
            finish_reason=r.get("finish_reason", ""),
            thinking_segmentation_status=r.get("thinking_segmentation_status", ""),
            source_stage="stage4_7",
        ))
    print(f"  stage4_7: {len(out)} rows")
    return out


def load_stage48_qwen3(run_dir: Path, source_stage: str = "stage4_8") -> list[dict]:
    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        print(f"  WARNING: {summary_path} not found, skipping {source_stage}")
        return []
    rows = _load_jsonl(summary_path)
    out = []
    for r in rows:
        sr = r.get("sr_success")
        if sr is None:
            sr = r.get("strongreject_is_success")
        out.append(_make_row(
            model_family="qwen3",
            source_example_id=r["source_example_id"],
            goal_index=r.get("goal_index"),
            condition=r["condition"],
            seed=r.get("seed"),
            do_sample=bool(r.get("do_sample", True)),
            enable_thinking=bool(r.get("enable_thinking", True)),
            sr_success=sr,
            strongreject_score=r.get("strongreject_score"),
            think_token_count=r.get("think_token_count"),
            finish_reason=r.get("finish_reason", ""),
            thinking_segmentation_status=r.get("thinking_segmentation_status", ""),
            source_stage=source_stage,
        ))
    print(f"  {source_stage}: {len(out)} rows")
    return out


def load_stage6_qwen3(traces_dir: Path) -> list[dict]:
    if not traces_dir.exists():
        print(f"  WARNING: {traces_dir} not found, skipping stage6_qwen3")
        return []
    out = []
    pattern = str(traces_dir / "*.json")
    for p in sorted(glob.glob(pattern)):
        fname = Path(p).name
        if fname == "batch_summary.json":
            continue
        try:
            with open(p, encoding="utf-8") as f:
                trace = json.load(f)
        except Exception as e:
            print(f"  SKIP {fname}: {e}")
            continue

        sr_result = trace.get("strongreject_result", {})
        if not isinstance(sr_result, dict):
            sr_result = {}
        sr_score = _f(sr_result.get("strongreject_score"))
        sr_success = bool(sr_score is not None and sr_score >= 0.5)

        # Parse source_example_id from filename or from sr_result
        m = _QWEN_FNAME_RE.search(fname)
        if m:
            gi, ai, ci, tm = m.group(1), m.group(2), m.group(3), m.group(4)
        else:
            gi = str(sr_result.get("goal_index", ""))
            ai = str(sr_result.get("attack_iteration", ""))
            ci = str(sr_result.get("conversation_id", ""))
            tm = sr_result.get("target_model", "gpt-o4-mini")

        source_id = f"goal_index={gi}|attack_iteration={ai}|conversation_id={ci}|target_model={tm}"

        out.append(_make_row(
            model_family="qwen3",
            source_example_id=source_id,
            goal_index=gi,
            condition="A",
            seed=None,
            do_sample=True,
            enable_thinking=True,
            sr_success=sr_success,
            strongreject_score=sr_score,
            think_token_count=trace.get("think_token_count"),
            finish_reason=trace.get("generation_finish_reason", ""),
            thinking_segmentation_status=trace.get("thinking_segmentation_status", ""),
            source_stage="stage6_qwen3",
        ))
    print(f"  stage6_qwen3: {len(out)} traces")
    return out


def load_stage6_gemma4(traces_dir: Path) -> list[dict]:
    if not traces_dir.exists():
        print(f"  WARNING: {traces_dir} not found, skipping stage6_gemma4")
        return []
    out = []
    pattern = str(traces_dir / "gemma_4_e4b_it_trace_*.json")
    for p in sorted(glob.glob(pattern)):
        fname = Path(p).name
        m = _GEMMA_FNAME_RE.search(fname)
        if not m:
            continue
        gi, ai, ci, tm = m.group(1), m.group(2), m.group(3), m.group(4)
        source_id = f"goal_index={gi}|attack_iteration={ai}|conversation_id={ci}|target_model={tm}"

        try:
            with open(p, encoding="utf-8") as f:
                trace = json.load(f)
        except Exception as e:
            print(f"  SKIP {fname}: {e}")
            continue

        sr_result = trace.get("strongreject_result", {})
        if not isinstance(sr_result, dict):
            sr_result = {}
        sr_score = _f(sr_result.get("strongreject_score"))
        sr_success = bool(sr_score is not None and sr_score >= 0.5)

        gen_config = trace.get("generation_config", {}) or {}
        think_tok = None
        think_text = trace.get("think_text")
        if think_text:
            think_tok = len(think_text.split())  # approximate; actual tokenization not needed here

        out.append(_make_row(
            model_family="gemma4",
            source_example_id=source_id,
            goal_index=gi,
            condition="A",
            seed=None,
            do_sample=bool(gen_config.get("do_sample", True)),
            enable_thinking=True,
            sr_success=sr_success,
            strongreject_score=sr_score,
            think_token_count=think_tok,
            finish_reason=trace.get("generation_finish_reason", ""),
            thinking_segmentation_status=trace.get("thinking_segmentation_status", ""),
            source_stage="stage6_gemma4",
        ))
    print(f"  stage6_gemma4: {len(out)} traces")
    return out


def load_stage48_gemma4(run_dir: Path) -> list[dict]:
    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        print(f"  WARNING: {summary_path} not found, skipping stage4_8_gemma")
        return []
    rows = _load_jsonl(summary_path)
    out = []
    for r in rows:
        sr = r.get("sr_success")
        if sr is None:
            sr = r.get("strongreject_is_success")
        out.append(_make_row(
            model_family="gemma4",
            source_example_id=r["source_example_id"],
            goal_index=r.get("goal_index"),
            condition=r["condition"],
            seed=r.get("seed"),
            do_sample=bool(r.get("do_sample", True)),
            enable_thinking=bool(r.get("enable_thinking", True)),
            sr_success=sr,
            strongreject_score=r.get("strongreject_score"),
            think_token_count=r.get("think_token_count"),
            finish_reason=r.get("finish_reason", ""),
            thinking_segmentation_status=r.get("thinking_segmentation_status", ""),
            source_stage="stage4_8_gemma",
        ))
    print(f"  stage4_8_gemma: {len(out)} rows")
    return out


def deduplicate(rows: list[dict]) -> list[dict]:
    """Keep the row with the most recent source_stage for each (model, source_id, condition, seed)."""
    # Priority: later stages override earlier ones
    stage_priority = {
        "stage6_qwen3": 0,
        "stage6_gemma4": 0,
        "stage4_7": 1,
        "stage4_8": 2,
        "stage4_8_cond_e": 2,
        "stage4_8_gemma": 2,
        "stage4_9_qwen3": 3,
        "stage4_9_gemma4": 3,
    }
    seen: dict[tuple, dict] = {}
    for row in rows:
        key = (
            row["model_family"],
            row["source_example_id"],
            row["condition"],
            row["seed"],
        )
        if key not in seen:
            seen[key] = row
        else:
            existing_prio = stage_priority.get(seen[key]["source_stage"], 0)
            new_prio = stage_priority.get(row["source_stage"], 0)
            if new_prio > existing_prio:
                seen[key] = row
    return list(seen.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(_REPO_ROOT / "outputs" / "stage4"))
    parser.add_argument("--stage47-run-dir", default=str(_STAGE47_RUN))
    parser.add_argument("--stage48-run-dir", default=str(_STAGE48_RUN))
    parser.add_argument("--cond-e-run-dir", default=None,
                        help="Path to run_cond_e_* dir; auto-discovers latest if omitted")
    parser.add_argument("--gemma-run-dir", default=None,
                        help="Path to Gemma4 run dir; auto-discovers latest if omitted")
    parser.add_argument("--no-stage6", action="store_true", default=False)
    parser.add_argument("--stage49-qwen3-dir", default=None,
                        help="Consolidated Qwen3 goals 4-10 run dir (has run_summary.jsonl)")
    parser.add_argument("--stage49-gemma4-dir", default=None,
                        help="Consolidated Gemma4 goals 4-10 run dir (has run_summary.jsonl)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Auto-discover run dirs if not specified
    # cond-E: SLURM array tasks each write to their own dir — collect ALL of them
    cond_e_dirs: list[Path] = []
    if args.cond_e_run_dir:
        cond_e_dirs = [Path(args.cond_e_run_dir)]
    else:
        cond_e_dirs = _discover_all_run_dirs(
            _REPO_ROOT / "outputs" / "stage4_8" / "runs", "run_cond_e_*"
        )

    gemma_run_dir = Path(args.gemma_run_dir) if args.gemma_run_dir else _auto_discover_run_dir(
        _REPO_ROOT / "outputs" / "stage4_8_gemma" / "runs", "run_[0-9]*"
    )

    print("Building factorial attack dataset...")
    print(f"  Stage 4.7 Qwen3:   {args.stage47_run_dir}")
    print(f"  Stage 4.8 Qwen3:   {args.stage48_run_dir}")
    print(f"  Stage 4.8 cond-E:  {[str(d) for d in cond_e_dirs]}")
    print(f"  Stage 4.8 Gemma4:  {gemma_run_dir}")
    print(f"  Stage 6 Qwen3:     {_STAGE6_QWEN}")
    print(f"  Stage 6 Gemma4:    {_STAGE6_GEMMA}")
    print()

    all_rows: list[dict] = []
    all_rows.extend(load_stage47_qwen3(Path(args.stage47_run_dir)))
    all_rows.extend(load_stage48_qwen3(Path(args.stage48_run_dir), source_stage="stage4_8"))
    if cond_e_dirs:
        for d in cond_e_dirs:
            if d.exists():
                all_rows.extend(load_stage48_qwen3(d, source_stage="stage4_8_cond_e"))
    else:
        print("  WARNING: no cond-E run dirs found; condition E missing for Qwen3 stochastic")
    if not args.no_stage6:
        all_rows.extend(load_stage6_qwen3(_STAGE6_QWEN))
        all_rows.extend(load_stage6_gemma4(_STAGE6_GEMMA))
    if gemma_run_dir and gemma_run_dir.exists():
        all_rows.extend(load_stage48_gemma4(gemma_run_dir))
    else:
        print(f"  WARNING: Gemma4 run dir not found ({gemma_run_dir}); Gemma4 factorial data will be missing")

    # Stage 4.9 extended (goals 4-10 D/E/F)
    if args.stage49_qwen3_dir:
        p = Path(args.stage49_qwen3_dir)
        if p.exists():
            all_rows.extend(load_stage48_qwen3(p, source_stage="stage4_9_qwen3"))
        else:
            print(f"  WARNING: --stage49-qwen3-dir not found ({p})")
    if args.stage49_gemma4_dir:
        p = Path(args.stage49_gemma4_dir)
        if p.exists():
            all_rows.extend(load_stage48_gemma4(p))
        else:
            print(f"  WARNING: --stage49-gemma4-dir not found ({p})")

    print(f"\nTotal rows before dedup: {len(all_rows)}")
    all_rows = deduplicate(all_rows)
    print(f"Total rows after dedup:  {len(all_rows)}")

    # Summary stats
    from collections import Counter
    by_model = Counter(r["model_family"] for r in all_rows)
    by_cond = Counter(r["condition"] for r in all_rows)
    valid_count = sum(1 for r in all_rows if r["is_valid"])
    sr_known = [r for r in all_rows if r["sr_success"] is not None]
    sr_success = sum(1 for r in sr_known if r["sr_success"])

    print(f"  By model:     {dict(by_model)}")
    print(f"  By condition: {dict(by_cond)}")
    print(f"  Valid rows:   {valid_count}/{len(all_rows)}")
    print(f"  SR scored:    {len(sr_known)}, successes: {sr_success}")

    # Write output
    out_path = output_dir / "factorial_attack_dataset.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for row in all_rows:
            f.write(json.dumps(row) + "\n")

    audit = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "n_rows": len(all_rows),
        "by_model": dict(by_model),
        "by_condition": dict(by_cond),
        "n_valid": valid_count,
        "n_sr_scored": len(sr_known),
        "n_sr_success": sr_success,
        "sources": {
            "stage4_7": args.stage47_run_dir,
            "stage4_8": args.stage48_run_dir,
            "stage4_8_cond_e": [str(d) for d in cond_e_dirs],
            "stage4_8_gemma": str(gemma_run_dir),
            "stage6_qwen3": str(_STAGE6_QWEN),
            "stage6_gemma4": str(_STAGE6_GEMMA),
        },
    }
    audit_path = output_dir / "factorial_dataset_audit.json"
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    print(f"\nWrote {len(all_rows)} rows to {out_path}")
    print(f"Audit → {audit_path}")


if __name__ == "__main__":
    main()
