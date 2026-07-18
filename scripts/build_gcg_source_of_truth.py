#!/usr/bin/env python3
"""Deterministic source-of-truth aggregator for the GCG Phase 4-7 pipeline.

Reads ONLY raw artifacts (CONFIG.json, RESULTS_SUMMARY.md, ITERATION_LOG.jsonl,
FREE_GENERATION_RESULTS*.jsonl) under outputs/stage_gcg_full/ -- never the
docs/*.md summaries -- and emits:
  outputs/stage_gcg_full/GCG_PHASE4_7_SOURCE_OF_TRUTH.csv
  docs/GCG_PHASE4_7_SOURCE_OF_TRUTH.md

Rerunnable and deterministic: same inputs always produce the same output.
"""
import json
import re
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Env overrides let the SAME aggregator emit a separate v2 (fixed-optimizer) table
# without touching the v1 defaults. See docs/GCG_BUGFIX_RERUN_PLAN.md.
#   GCG_BASE=outputs/stage_gcg_full_v2_userfix GCG_SOT_CSV=..._v2.csv GCG_SOT_MD=..._v2.md
BASE = ROOT / os.environ.get("GCG_BASE", "outputs/stage_gcg_full")

# (row_id, model, phase_label, run_dir, seeded_results_file, unseeded_results_file)
RUNS = [
    ("standard_gcg_qwen3", "qwen3-14b", "Standard GCG (task-only-ish, lambda_repr=1)", "gcg_full_qwen3_weighted", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("4A_cot_disabled", "qwen3-14b", "4A: CoT disabled", "gcg_full_qwen3_cot_disabled", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("4B_lambda0", "qwen3-14b", "4B: lambda_repr=0 (task-only)", "gcg_full_qwen3_lambda0", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("4C_gemma4_weighted", "gemma4-e4b-it", "4C: Gemma4 standard GCG", "gcg_full_gemma4_weighted", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("4E_qwen3_to_gemma4_transfer", "qwen3->gemma4", "4E: cross-model text transfer", "gcg_full_qwen3_to_gemma4_transfer", "FREE_GENERATION_RESULTS.jsonl", None),
    ("4F_full520_eval", "qwen3-14b", "4F: standard suffix on full 520", "gcg_full_qwen3_full520_eval", "FREE_GENERATION_RESULTS.jsonl", None),
    ("5A_cot_target", "qwen3-14b", "5A: CoT-prefix targeting", "gcg_full_qwen3_cot_target", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("5B_cot_repr", "qwen3-14b", "5B: repr loss at CoT position", "gcg_full_qwen3_5b_cot_repr", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("5C_quick_asr", "qwen3-14b", "5C: quick-ASR candidate selection", "gcg_full_qwen3_5c_quick_asr", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("6A_Q_refusal_dir", "qwen3-14b", "6A-Q: standard target + refusal-dir loss", "gcg_full_qwen3_6a_refusal_dir", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("6A_G_refusal_dir", "gemma4-e4b-it", "6A-G: standard target + refusal-dir loss", "gcg_full_gemma4_6a_refusal_dir", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("6B_gemma4_cot_target", "gemma4-e4b-it", "6B: Gemma4 CoT-aligned target (no refusal-dir)", "gcg_full_gemma4_6b_cot_target", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("6C_cot_refusal", "qwen3-14b", "6C: CoT-prefix target + refusal-dir loss", "gcg_full_qwen3_6c_cot_refusal", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("7A_full520_seeded", "qwen3-14b", "7A: 5A suffix on all 520, seeds 42/43/44", "gcg_full_qwen3_7a_5a_full520", "FREE_GENERATION_RESULTS.jsonl", None),
    ("7A_full520_unseeded", "qwen3-14b", "7A: 5A suffix on all 520, seeds 100/200/300 (held-out)", "gcg_full_qwen3_7a_5a_full520", None, "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("7B_seed43", "qwen3-14b", "7B: optimization seed 43 (CoT-target)", "gcg_full_qwen3_7b_seed43", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("7B_seed44", "qwen3-14b", "7B: optimization seed 44 (CoT-target)", "gcg_full_qwen3_7b_seed44", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("7B_seed45", "qwen3-14b", "7B: optimization seed 45 (CoT-target)", "gcg_full_qwen3_7b_seed45", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("7C_gemma4_nothink", "gemma4-e4b-it", "7C: Gemma4, thinking disabled", "gcg_full_gemma4_7c_nothink", "FREE_GENERATION_RESULTS.jsonl", "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"),
    ("8_rd_layer20", "qwen3-14b", "Phase 8: refusal-dir sweep, layer=20/lambda=1.0", "gcg_full_qwen3_8_rd_layer20", "FREE_GENERATION_RESULTS.jsonl", None),
    ("8_rd_layer30", "qwen3-14b", "Phase 8: refusal-dir sweep, layer=30/lambda=1.0", "gcg_full_qwen3_8_rd_layer30", "FREE_GENERATION_RESULTS.jsonl", None),
    ("8_rd_lambda03", "qwen3-14b", "Phase 8: refusal-dir sweep, layer=25/lambda=0.3", "gcg_full_qwen3_8_rd_lambda03", "FREE_GENERATION_RESULTS.jsonl", None),
    ("8_rd_lambda3", "qwen3-14b", "Phase 8: refusal-dir sweep, layer=25/lambda=3.0", "gcg_full_qwen3_8_rd_lambda3", "FREE_GENERATION_RESULTS.jsonl", None),
    ("sprint2_8_rd_lambda03_seed43", "qwen3-14b", "Sprint2 Track0: layer=25/lambda=0.3, seed=43 replication", "gcg_full_qwen3_8_rd_lambda03_seed43", "FREE_GENERATION_RESULTS.jsonl", None),
    ("sprint2_track1_gemma4_v2", "gemma4-e4b-it", "Sprint2 Track1: Gemma4 CoT-prefix target v2, 800 steps", "gcg_full_gemma4_6b2_cot_target_v2", "FREE_GENERATION_RESULTS.jsonl", None),
    ("sprint2_track3_deepseek_std", "deepseek_r1-7b", "Sprint2 Track3: DeepSeek-R1-Distill-Qwen-7B, standard target", "gcg_full_deepseek_r1_7b_weighted", "FREE_GENERATION_RESULTS.jsonl", None),
    ("sprint2_track3_deepseek_cot", "deepseek_r1-7b", "Sprint2 Track3: DeepSeek-R1-Distill-Qwen-7B, CoT-prefix target", "gcg_full_deepseek_r1_7b_cot_target", "FREE_GENERATION_RESULTS.jsonl", None),
    ("sprint2_track4_suflen35", "qwen3-14b", "Sprint2 Track4: suffix_length=35 ablation (CoT-prefix target)", "gcg_full_qwen3_track4_suflen35_cot_target", "FREE_GENERATION_RESULTS.jsonl", None),
]


def read_json(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception as e:
        return {"__error__": str(e)}


def parse_results_summary(p: Path):
    """Extract key metrics from RESULTS_SUMMARY.md via regex (no doc trust needed -- this IS a raw artifact)."""
    out = {}
    if not p.exists():
        return out
    text = p.read_text()

    def grab(pattern, cast=float):
        m = re.search(pattern, text)
        return cast(m.group(1)) if m else None

    out["steps_completed"] = grab(r"\|\s*Steps completed\s*\|\s*(\d+)\s*\|", int)
    out["task_loss_step0"] = grab(r"\|\s*task_loss step 0\s*\|\s*([\d.]+)\s*\|")
    out["task_loss_final"] = grab(r"\|\s*task_loss final\s*\|\s*([\d.]+)\s*\|")
    m = re.search(r"\|\s*task_loss best\s*\|\s*([\d.]+)\s*\(step (\d+)\)\s*\|", text)
    if m:
        out["task_loss_best"] = float(m.group(1))
        out["task_loss_best_step"] = int(m.group(2))
    out["repr_loss_step0"] = grab(r"\|\s*repr_loss step 0\s*\|\s*([\d.]+)\s*\|")
    out["repr_loss_final"] = grab(r"\|\s*repr_loss final\s*\|\s*([\d.]+)\s*\|")
    return out


def dedup_iteration_log(p: Path):
    """Return (n_raw_rows, n_distinct_steps, best_row_by_task_loss, last_row) using max-step-index tie-break for dup rows."""
    if not p.exists():
        return None
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    n_raw = len(rows)
    by_step = {}
    for r in rows:
        by_step[r["step"]] = r  # last occurrence wins (later duplicate = later resumed log)
    distinct = sorted(by_step.values(), key=lambda r: r["step"])
    best = min(distinct, key=lambda r: r["task_loss"])
    last = distinct[-1]
    return {
        "n_raw_rows": n_raw,
        "n_distinct_steps": len(distinct),
        "has_duplicates": n_raw != len(distinct),
        "best_task_loss_dedup": best["task_loss"],
        "best_step_dedup": best["step"],
        "best_refusal_dir_loss": best.get("refusal_dir_loss"),
        "final_refusal_dir_loss": last.get("refusal_dir_loss"),
        "step0_refusal_dir_loss": distinct[0].get("refusal_dir_loss"),
    }


def analyze_free_gen(p: Path):
    if p is None or not p.exists():
        return None
    n = 0
    by_cond = {}
    seeds = {}
    task_ids = set()
    status_ok = 0
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        n += 1
        cond = r.get("condition_label")
        d = by_cond.setdefault(cond, {"n": 0, "succ": 0, "sr_sum": 0.0, "sr_n": 0})
        d["n"] += 1
        if r.get("strongreject_is_success"):
            d["succ"] += 1
        sr = r.get("strongreject_score")
        if sr is not None:
            d["sr_sum"] += sr
            d["sr_n"] += 1
        s = r.get("seed")
        seeds[s] = seeds.get(s, 0) + 1
        task_ids.add(r.get("task_id"))
        if r.get("status") == "ok":
            status_ok += 1
    cond_summary = {}
    for cond, d in by_cond.items():
        cond_summary[cond] = {
            "n": d["n"],
            "successes": d["succ"],
            "asr": round(d["succ"] / d["n"], 4) if d["n"] else None,
            "mean_strongreject_score": round(d["sr_sum"] / d["sr_n"], 4) if d["sr_n"] else None,
        }
    return {
        "n_rows": n,
        "n_status_ok": status_ok,
        "n_distinct_task_ids": len(task_ids),
        "seeds_present": dict(sorted(seeds.items(), key=lambda kv: (kv[0] is None, kv[0]))),
        "by_condition": cond_summary,
    }


def main():
    all_rows = []
    detail = {}
    for row_id, model, label, run_dir, seeded_file, unseeded_file in RUNS:
        d = BASE / run_dir
        config = read_json(d / "CONFIG.json") or {}
        results_summary = parse_results_summary(d / "RESULTS_SUMMARY.md")
        iter_log = dedup_iteration_log(d / "ITERATION_LOG.jsonl")
        seeded = analyze_free_gen(d / seeded_file) if seeded_file else None
        unseeded = analyze_free_gen(d / unseeded_file) if unseeded_file else None

        gcg = config.get("gcg", {})
        obj = config.get("objective", {})
        manifest_path = config.get("manifest_path", "")
        manifest_name = Path(manifest_path).name if manifest_path else ""

        opt_cond = None
        if seeded and seeded["by_condition"]:
            for c in seeded["by_condition"]:
                if c and "optimized" in c:
                    opt_cond = c
                    break

        row = {
            "row_id": row_id,
            "label": label,
            "model": model,
            "run_dir": f"outputs/stage_gcg_full/{run_dir}",
            "manifest": manifest_name,
            "n_behaviors_in_manifest": None,  # filled below if manifest readable
            "optimization_seed": gcg.get("seed"),
            "suffix_length": gcg.get("suffix_length"),
            "n_steps_configured": gcg.get("n_steps"),
            "n_steps_completed_raw": results_summary.get("steps_completed"),
            "n_steps_distinct_dedup": iter_log["n_distinct_steps"] if iter_log else None,
            "iteration_log_has_duplicate_steps": iter_log["has_duplicates"] if iter_log else None,
            "lambda_repr": obj.get("lambda_repr"),
            "lambda_refusal_dir": obj.get("lambda_refusal_dir"),
            "refusal_dir_layer": config.get("refusal_dir_layer") or obj.get("refusal_dir_layer"),
            "task_loss_step0": results_summary.get("task_loss_step0"),
            "task_loss_final": results_summary.get("task_loss_final"),
            "task_loss_best": results_summary.get("task_loss_best"),
            "task_loss_best_step": results_summary.get("task_loss_best_step"),
            "task_loss_best_dedup_crosscheck": iter_log["best_task_loss_dedup"] if iter_log else None,
            "refusal_dir_loss_step0": iter_log["step0_refusal_dir_loss"] if iter_log else None,
            "refusal_dir_loss_best": iter_log["best_refusal_dir_loss"] if iter_log else None,
            "refusal_dir_loss_final": iter_log["final_refusal_dir_loss"] if iter_log else None,
            "seeded_n_rows": seeded["n_rows"] if seeded else None,
            "seeded_n_distinct_behaviors": seeded["n_distinct_task_ids"] if seeded else None,
            "seeded_seeds_present": seeded["seeds_present"] if seeded else None,
            "seeded_optimized_condition_label": opt_cond,
            "seeded_optimized_asr": seeded["by_condition"].get(opt_cond, {}).get("asr") if (seeded and opt_cond) else None,
            "seeded_optimized_successes": seeded["by_condition"].get(opt_cond, {}).get("successes") if (seeded and opt_cond) else None,
            "seeded_optimized_n": seeded["by_condition"].get(opt_cond, {}).get("n") if (seeded and opt_cond) else None,
            "seeded_neutral_asr": seeded["by_condition"].get("neutral_control", {}).get("asr") if seeded else None,
            "seeded_task_only_asr": seeded["by_condition"].get("task_only", {}).get("asr") if seeded else None,
            "seeded_random_spaces_asr": seeded["by_condition"].get("random_spaces", {}).get("asr") if seeded else None,
            "unseeded_n_rows": unseeded["n_rows"] if unseeded else None,
            "unseeded_n_distinct_behaviors": unseeded["n_distinct_task_ids"] if unseeded else None,
            "unseeded_seeds_present": unseeded["seeds_present"] if unseeded else None,
            "unseeded_optimized_asr": unseeded["by_condition"].get(opt_cond or "optimized_weighted", {}).get("asr") if unseeded else None,
            "unseeded_optimized_successes": unseeded["by_condition"].get(opt_cond or "optimized_weighted", {}).get("successes") if unseeded else None,
            "unseeded_optimized_n": unseeded["by_condition"].get(opt_cond or "optimized_weighted", {}).get("n") if unseeded else None,
            "unseeded_neutral_asr": unseeded["by_condition"].get("neutral_control", {}).get("asr") if unseeded else None,
        }

        manifest_full_path = ROOT / manifest_path.replace(str(ROOT) + "/", "") if manifest_path else None
        if manifest_path:
            mp = Path(manifest_path)
            if not mp.is_absolute():
                mp = ROOT / manifest_path
            if mp.exists():
                row["n_behaviors_in_manifest"] = sum(1 for _ in mp.open())

        all_rows.append(row)
        detail[row_id] = {
            "config": config,
            "results_summary_parsed": results_summary,
            "iteration_log": iter_log,
            "seeded_free_gen": seeded,
            "unseeded_free_gen": unseeded,
        }

    # --- write CSV ---
    csv_path = BASE / os.environ.get("GCG_SOT_CSV", "GCG_PHASE4_7_SOURCE_OF_TRUTH.csv")
    fieldnames = list(all_rows[0].keys())
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in all_rows:
            rr = dict(r)
            for k, v in rr.items():
                if isinstance(v, dict):
                    rr[k] = json.dumps(v, sort_keys=True)
            w.writerow(rr)
    print(f"Wrote {csv_path} ({len(all_rows)} rows)")

    # --- write detail JSON (for downstream scripts / audit report, not a deliverable itself) ---
    detail_path = BASE / "GCG_PHASE4_7_SOURCE_OF_TRUTH_DETAIL.json"
    with open(detail_path, "w") as f:
        json.dump(detail, f, indent=2, default=str)
    print(f"Wrote {detail_path}")

    # --- write markdown ---
    md_path = ROOT / "docs" / os.environ.get("GCG_SOT_MD", "GCG_PHASE4_7_SOURCE_OF_TRUTH.md")
    lines = []
    lines.append("# GCG Phase 4-7 Source-of-Truth Table")
    lines.append("")
    lines.append("**Generated by:** `scripts/build_gcg_source_of_truth.py` (deterministic, reads only raw artifacts: `CONFIG.json`, `RESULTS_SUMMARY.md`, `ITERATION_LOG.jsonl`, `FREE_GENERATION_RESULTS*.jsonl`).")
    lines.append("")
    lines.append("Rerun with: `python3 scripts/build_gcg_source_of_truth.py`")
    lines.append("")
    lines.append("Full detail (per-step, per-condition) is in `outputs/stage_gcg_full/GCG_PHASE4_7_SOURCE_OF_TRUTH_DETAIL.json` and the raw CSV `outputs/stage_gcg_full/GCG_PHASE4_7_SOURCE_OF_TRUTH.csv`. Every number in `docs/GCG_FINDINGS_SYNTHESIS.md` and the presentation should trace back to a row here.")
    lines.append("")
    lines.append("## Definitions")
    lines.append("")
    lines.append("- **optimization seed** (`gcg.seed`): controls GCG's random suffix initialization and search trajectory -- a different value produces a *different optimized suffix*.")
    lines.append("- **generation seed** (`seed` field in FREE_GENERATION_RESULTS rows): controls stochastic sampling during free generation for a *fixed, already-optimized* suffix. Seeds 42/43/44 are the \"training/development\" generation seeds (used during optimization-time evaluation); seeds 100/200/300 are held-out (\"unseen\") generation seeds, used only in `*_UNSEEDED.jsonl` files.")
    lines.append("- **task_loss**: summed teacher-forced cross-entropy over the target string across all behaviors in the optimization manifest (NOT per-token, NOT per-behavior averaged) -- see `task_loss_best / n_behaviors_in_manifest` for a rough per-behavior figure; per-token normalization additionally requires dividing by each target's token count, which varies by target string and is not currently logged per-behavior in `ITERATION_LOG.jsonl`, so exact per-token CE is NOT computed by this script (flagged as a limitation).")
    lines.append("- **ASR (attack success rate)**: `successes / n` where `success = strongreject_is_success` (StrongREJECT-rubric boolean) for a given `condition_label`.")
    lines.append("- **uplift**: optimized-condition ASR minus a baseline condition's ASR (neutral_control, task_only, or random_spaces), in percentage points (pp), i.e. `100*(asr_opt - asr_baseline)`.")
    lines.append("- **iteration_log_has_duplicate_steps**: True means `ITERATION_LOG.jsonl` contains more rows than distinct `step` values (job-restart artifact); `n_steps_completed_raw` (as printed in `RESULTS_SUMMARY.md`) is a raw line count and can therefore exceed the true configured `n_steps` -- always prefer `n_steps_distinct_dedup`.")
    lines.append("")
    lines.append("## Table")
    lines.append("")
    key_cols = ["row_id", "model", "manifest", "n_behaviors_in_manifest", "optimization_seed",
                "n_steps_distinct_dedup", "iteration_log_has_duplicate_steps", "lambda_repr", "lambda_refusal_dir",
                "task_loss_best", "task_loss_best_step", "refusal_dir_loss_best",
                "seeded_n_rows", "seeded_optimized_asr", "seeded_neutral_asr",
                "unseeded_n_rows", "unseeded_n_distinct_behaviors", "unseeded_optimized_asr", "unseeded_neutral_asr"]
    lines.append("| " + " | ".join(key_cols) + " |")
    lines.append("|" + "---|" * len(key_cols))
    for r in all_rows:
        vals = []
        for c in key_cols:
            v = r.get(c)
            if isinstance(v, dict):
                v = ", ".join(f"{k}:{n}" for k, n in v.items())
            vals.append("" if v is None else str(v))
        lines.append("| " + " | ".join(vals) + " |")
    lines.append("")
    lines.append("Full column set (43 columns) is in the CSV; this table shows the columns most load-bearing for headline claims.")
    md_path.write_text("\n".join(lines) + "\n")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
