#!/usr/bin/env python3
"""Aggregate the Gate-3 soft-prompt REINFORCE-vs-Prefix-CE confirmatory runs across seeds.

Reads ONLY the scalar ASR fields of each run-record (never the generation text) and
produces the honest FINAL-step REINFORCE-vs-Prefix-CE comparison, per-seed and pooled.

IMPORTANT METRIC CAVEAT (see docs/SPRINT_COMPLETION_EXECUTION_LOG.md Iter 32): the
soft-prompt runner generated with max_new_tokens=256, which for a thinking model
truncates every generation mid-`<think>` (no generation reaches `</think>`). So these
ASRs are a 256-token IN-THINK PROXY scored by StrongREJECT, NOT a delivered-content
harm rate. This aggregator reports that proxy comparison; the Gate-3 decision is
triangulated against the delivered-content Gate-1 evals (discrete GCG/MAC = 0/3 at
2048 tokens on these same instructions). Do not read the absolute numbers as harm rates.

Inputs (JSONL, one run-record per line; MISSING files are skipped, never fabricated):
  outputs/phase_d_soft_prompt_gate3_conf/{prefix_ce,reinforce}.jsonl                (seed 0)
  outputs/phase_d_soft_prompt_gate3_conf/{prefix_ce,reinforce}_seed{1,2}.jsonl      (seeds 1,2)

Each record keyed by (instruction, length, seed, objective); scalar fields used:
  final_sampled_asr, final_greedy_asr, best_sampled_asr, best_greedy_asr.

Usage:
  python3 scripts/aggregate_gate3.py [--conf-dir DIR] [--out-csv PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any, Optional

SCALAR_FIELDS = (
    "final_sampled_asr",
    "final_greedy_asr",
    "best_sampled_asr",
    "best_greedy_asr",
)
DEFAULT_CONF_DIR = "outputs/phase_d_soft_prompt_gate3_conf"
DEFAULT_OUT_CSV = "results/GATE3_SEED_AGGREGATE.csv"


def _arm_files(conf_dir: Path) -> list[tuple[int, str, Path]]:
    """(seed, objective, path) for every arm/seed file that COULD exist."""
    specs = [
        (0, "prefix_ce", conf_dir / "prefix_ce.jsonl"),
        (0, "reinforce", conf_dir / "reinforce.jsonl"),
    ]
    for seed in (1, 2):
        specs.append((seed, "prefix_ce", conf_dir / f"prefix_ce_seed{seed}.jsonl"))
        specs.append((seed, "reinforce", conf_dir / f"reinforce_seed{seed}.jsonl"))
    return specs


def load_records(conf_dir: Path) -> tuple[dict, list, list]:
    """Return (records keyed by (instr,length,seed,objective), present_files, absent_files).

    Only scalar fields are read from each record (generation text is never touched).
    """
    records: dict[tuple[str, int, int, str], dict[str, Any]] = {}
    present: list[str] = []
    absent: list[str] = []
    for seed, obj, path in _arm_files(conf_dir):
        if not path.exists() or path.stat().st_size == 0:
            absent.append(path.name)
            continue
        n_rows = 0
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                key = (str(r["instruction"]), int(r["length"]), int(r.get("seed", seed)), obj)
                records[key] = {f: r.get(f) for f in SCALAR_FIELDS}
                n_rows += 1
        if n_rows:
            present.append(f"{path.name} ({n_rows} rows)")
        else:
            absent.append(path.name)
    return records, present, absent


def _num(x: Any) -> float:
    return float(x) if x is not None else 0.0


def per_instruction_seed(records: dict) -> list[dict]:
    """One row per (instruction, seed): best-over-length FINAL-step ASR per arm + verdict."""
    instrs = sorted({k[0] for k in records})
    seeds = sorted({k[2] for k in records})
    rows: list[dict] = []
    for ins in instrs:
        for seed in seeds:
            def best_over_len(obj: str, field: str) -> Optional[float]:
                vals = [
                    _num(records[(ins, L, seed, obj)][field])
                    for L in (5, 20)
                    if (ins, L, seed, obj) in records
                ]
                return max(vals) if vals else None

            p_s = best_over_len("prefix_ce", "final_sampled_asr")
            r_s = best_over_len("reinforce", "final_sampled_asr")
            if p_s is None or r_s is None:
                continue  # need both arms present for this (instr, seed)
            p_g = best_over_len("prefix_ce", "final_greedy_asr")
            r_g = best_over_len("reinforce", "final_greedy_asr")
            verdict = "R>P" if r_s > p_s else ("P>R" if p_s > r_s else "tie")
            rows.append(
                {
                    "instruction": ins[:60],
                    "seed": seed,
                    "prefix_ce_final_sampled": p_s,
                    "reinforce_final_sampled": r_s,
                    "prefix_ce_final_greedy": p_g,
                    "reinforce_final_greedy": r_g,
                    "verdict_sampled": verdict,
                }
            )
    return rows


def summarize(rows: list[dict]) -> dict:
    """Per-seed tally + pooled means + between-seed spread of each arm's mean."""
    seeds = sorted({row["seed"] for row in rows})
    per_seed = {}
    for seed in seeds:
        srows = [row for row in rows if row["seed"] == seed]
        tally = {"R>P": 0, "tie": 0, "P>R": 0}
        for row in srows:
            tally[row["verdict_sampled"]] += 1
        per_seed[seed] = {
            "tally": tally,
            "n_instructions": len(srows),
            "mean_prefix_ce": (
                statistics.mean(r["prefix_ce_final_sampled"] for r in srows) if srows else 0.0
            ),
            "mean_reinforce": (
                statistics.mean(r["reinforce_final_sampled"] for r in srows) if srows else 0.0
            ),
        }
    # per-instruction consistency across seeds
    instrs = sorted({row["instruction"] for row in rows})
    consistency = {}
    for ins in instrs:
        irows = [row for row in rows if row["instruction"] == ins]
        t = {"R>P": 0, "tie": 0, "P>R": 0}
        for row in irows:
            t[row["verdict_sampled"]] += 1
        consistency[ins] = t
    seed_means_p = [per_seed[s]["mean_prefix_ce"] for s in seeds]
    seed_means_r = [per_seed[s]["mean_reinforce"] for s in seeds]
    return {
        "seeds": seeds,
        "per_seed": per_seed,
        "consistency": consistency,
        "grand_mean_prefix_ce": statistics.mean(seed_means_p) if seed_means_p else 0.0,
        "grand_mean_reinforce": statistics.mean(seed_means_r) if seed_means_r else 0.0,
        "between_seed_std_prefix_ce": statistics.pstdev(seed_means_p) if len(seed_means_p) > 1 else 0.0,
        "between_seed_std_reinforce": statistics.pstdev(seed_means_r) if len(seed_means_r) > 1 else 0.0,
    }


def write_csv(rows: list[dict], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "instruction",
        "seed",
        "prefix_ce_final_sampled",
        "reinforce_final_sampled",
        "prefix_ce_final_greedy",
        "reinforce_final_greedy",
        "verdict_sampled",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def format_summary(present: list[str], absent: list[str], rows: list[dict], summ: dict) -> str:
    lines = ["=== Gate-3 seed aggregate (256-token IN-THINK PROXY metric — NOT delivered harm) ==="]
    lines.append(f"present files: {present or '(none)'}")
    lines.append(f"absent/empty : {absent or '(none)'}")
    if not rows:
        lines.append("No paired (instruction, seed) rows yet — nothing to aggregate.")
        return "\n".join(lines)
    lines.append("")
    for seed in summ["seeds"]:
        ps = summ["per_seed"][seed]
        t = ps["tally"]
        lines.append(
            f"seed {seed}: R>P {t['R>P']}/{ps['n_instructions']}, tie {t['tie']}, P>R {t['P>R']} "
            f"| mean final_sampled  prefix_ce={ps['mean_prefix_ce']:.3f}  reinforce={ps['mean_reinforce']:.3f}"
        )
    lines.append("")
    lines.append(
        f"GRAND mean final_sampled: prefix_ce={summ['grand_mean_prefix_ce']:.3f} "
        f"(±{summ['between_seed_std_prefix_ce']:.3f}) | "
        f"reinforce={summ['grand_mean_reinforce']:.3f} (±{summ['between_seed_std_reinforce']:.3f})"
    )
    total_rgt = sum(summ["per_seed"][s]["tally"]["R>P"] for s in summ["seeds"])
    total_pgt = sum(summ["per_seed"][s]["tally"]["P>R"] for s in summ["seeds"])
    total = sum(summ["per_seed"][s]["n_instructions"] for s in summ["seeds"])
    lines.append(
        f"VERDICT (proxy): REINFORCE>Prefix-CE on {total_rgt}/{total} (instr×seed), "
        f"Prefix-CE>REINFORCE on {total_pgt}/{total}, tie on {total - total_rgt - total_pgt}/{total}."
    )
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Aggregate Gate-3 seed runs (scalar ASR only).")
    ap.add_argument("--conf-dir", default=DEFAULT_CONF_DIR)
    ap.add_argument("--out-csv", default=DEFAULT_OUT_CSV)
    args = ap.parse_args(argv)

    conf_dir = Path(args.conf_dir)
    records, present, absent = load_records(conf_dir)
    rows = per_instruction_seed(records)
    summ = summarize(rows) if rows else {}
    if rows:
        write_csv(rows, Path(args.out_csv))
    print(format_summary(present, absent, rows, summ))
    if rows:
        print(f"\nCSV -> {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
