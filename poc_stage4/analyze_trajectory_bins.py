"""
Stage 4 utility: per-bin effect size from trajectory.csv.

Reads trajectory.csv from the Stage 4C stats output and computes, for each
(bin, layer, rank), the Cohen's d effect size between complied and refused groups.

Scientific question: "At what point during the model's thinking does the
refusal direction signal first diverge between jailbreak successes and failures?"

If the signal appears in bin 0 (first 10% of thinking), the attack exploits
an early representational difference — possibly established at the `<think>` token.
If it appears late (bins 7–9), the attack works by gradually corrupting the direction
during extended reasoning.

Output: outputs/stage4/qwen3-14b/trajectory_bin_analysis_{variant}/
  bin_effect_size.csv          Cohen's d per (bin, layer, rank)
  summary.json                 first-significant-bin per (layer, rank)
  plots/effect_size_{layer}_{rank}.png
  plots/effect_size_heatmap.png
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys

import numpy as np


def cohens_d(mean1: float, std1: float, n1: int,
             mean2: float, std2: float, n2: int) -> float:
    pooled_var = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2)
    pooled_std = math.sqrt(max(pooled_var, 1e-12))
    return (mean1 - mean2) / pooled_std


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="behavioral", choices=["behavioral", "endofthink"])
    parser.add_argument("--base-dir", default="outputs/stage4/qwen3-14b")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--effect-threshold", type=float, default=0.2,
                        help="Cohen's d threshold to call a bin 'significant'. Default: 0.2")
    args = parser.parse_args()

    base = pathlib.Path(args.base_dir)
    stats_dir = base / f"subspace_stats_{args.variant}"
    traj_path = stats_dir / "trajectory.csv"
    if not traj_path.exists():
        print(f"ERROR: {traj_path} not found. Run Stage 4C stats first.", file=sys.stderr)
        sys.exit(1)

    output_dir = pathlib.Path(args.output_dir) if args.output_dir else (
        base / f"trajectory_bin_analysis_{args.variant}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "plots").mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # Load trajectory.csv
    # ------------------------------------------------------------------
    rows = []
    with open(traj_path) as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "bin": int(r["bin"]),
                "normalized_position": float(r["normalized_position"]),
                "layer": int(r["layer"]),
                "subspace_rank": int(r["subspace_rank"]),
                "group": r["group"],
                "n_examples": int(r["n_examples"]),
                "mean_proj": float(r["mean_proj"]),
                "std_proj": float(r["std_proj"]),
            })

    # Group by (bin, layer, rank)
    from collections import defaultdict
    by_key: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        key = (r["bin"], r["layer"], r["subspace_rank"])
        by_key[key][r["group"]] = r

    # ------------------------------------------------------------------
    # Compute Cohen's d per (bin, layer, rank)
    # ------------------------------------------------------------------
    effect_rows = []
    for (bin_idx, layer, rank), groups in sorted(by_key.items()):
        c = groups.get("complied")
        r = groups.get("refused")
        if c is None or r is None:
            continue
        d = cohens_d(
            c["mean_proj"], c["std_proj"], c["n_examples"],
            r["mean_proj"], r["std_proj"], r["n_examples"],
        )
        effect_rows.append({
            "bin": bin_idx,
            "normalized_position": c["normalized_position"],
            "layer": layer,
            "subspace_rank": rank,
            "mean_complied": round(c["mean_proj"], 6),
            "mean_refused": round(r["mean_proj"], 6),
            "mean_diff": round(c["mean_proj"] - r["mean_proj"], 6),
            "cohens_d": round(d, 6),
        })

    csv_path = output_dir / "bin_effect_size.csv"
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(effect_rows[0].keys()))
        w.writeheader()
        w.writerows(effect_rows)
    print(f"[traj_bins] Wrote {len(effect_rows)} rows to {csv_path}")

    # ------------------------------------------------------------------
    # Summary: first bin where |d| >= threshold per (layer, rank)
    # ------------------------------------------------------------------
    # Also find the (layer, rank) with max effect and report onset there
    from collections import defaultdict as dd2
    by_lr: dict[tuple, list] = dd2(list)
    for r in effect_rows:
        by_lr[(r["layer"], r["subspace_rank"])].append(r)

    # Sort by bin
    for k in by_lr:
        by_lr[k].sort(key=lambda x: x["bin"])

    summary_rows = []
    for (layer, rank), bin_rows in sorted(by_lr.items()):
        max_d = max(abs(r["cohens_d"]) for r in bin_rows)
        first_sig_bin = next(
            (r["bin"] for r in bin_rows if abs(r["cohens_d"]) >= args.effect_threshold),
            None,
        )
        first_sig_pos = next(
            (r["normalized_position"] for r in bin_rows if abs(r["cohens_d"]) >= args.effect_threshold),
            None,
        )
        summary_rows.append({
            "layer": layer,
            "subspace_rank": rank,
            "max_cohens_d": round(max_d, 4),
            "first_significant_bin": first_sig_bin,
            "first_significant_normalized_position": round(first_sig_pos, 3) if first_sig_pos else None,
        })

    summary_rows.sort(key=lambda x: -x["max_cohens_d"])

    summary = {
        "variant": args.variant,
        "effect_threshold": args.effect_threshold,
        "n_bins": len(set(r["bin"] for r in effect_rows)),
        "top5_by_max_d": summary_rows[:5],
        "all": summary_rows,
    }

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"[traj_bins] Summary written to {summary_path}")

    print("\n=== Top 5 (layer, rank) by max Cohen's d ===")
    for row in summary_rows[:5]:
        onset = f"bin {row['first_significant_bin']} (pos {row['first_significant_normalized_position']})" \
                if row["first_significant_bin"] is not None else "never"
        print(f"  layer={row['layer']}, rank={row['subspace_rank']}: "
              f"max_d={row['max_cohens_d']:.3f}, first_sig={onset}")

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Line plot for top 5 (layer, rank) pairs
        top5 = summary_rows[:5]
        bins_all = sorted(set(r["bin"] for r in effect_rows))
        n_pos = len(bins_all)
        fig, ax = plt.subplots(figsize=(10, 4))
        for row in top5:
            layer, rank = row["layer"], row["subspace_rank"]
            bin_rows_lr = sorted(by_lr[(layer, rank)], key=lambda x: x["bin"])
            xs = [r["normalized_position"] for r in bin_rows_lr]
            ys = [r["cohens_d"] for r in bin_rows_lr]
            ax.plot(xs, ys, marker="o", markersize=4, label=f"L{layer} r{rank}")
        ax.axhline(args.effect_threshold, color="gray", linestyle="--", linewidth=0.8, label=f"d={args.effect_threshold}")
        ax.axhline(-args.effect_threshold, color="gray", linestyle="--", linewidth=0.8)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_xlabel("Normalized thinking position (0=start, 1=</think>)")
        ax.set_ylabel("Cohen's d (complied − refused)")
        ax.set_title(f"Effect size trajectory by thinking position [{args.variant}]")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        line_path = output_dir / "plots" / "effect_size_trajectory.png"
        plt.savefig(line_path, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"[traj_bins] Line plot saved to {line_path}")

        # Mean diff trajectory (absolute projection difference, not standardized)
        fig, ax = plt.subplots(figsize=(10, 4))
        for row in top5:
            layer, rank = row["layer"], row["subspace_rank"]
            bin_rows_lr = sorted(by_lr[(layer, rank)], key=lambda x: x["bin"])
            xs = [r["normalized_position"] for r in bin_rows_lr]
            ys = [r["mean_diff"] for r in bin_rows_lr]
            ax.plot(xs, ys, marker="o", markersize=4, label=f"L{layer} r{rank}")
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_xlabel("Normalized thinking position")
        ax.set_ylabel("Mean projection: complied − refused")
        ax.set_title(f"Mean projection difference trajectory [{args.variant}]")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        diff_path = output_dir / "plots" / "mean_diff_trajectory.png"
        plt.savefig(diff_path, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"[traj_bins] Mean diff plot saved to {diff_path}")

    except Exception as e:
        print(f"[traj_bins] Plot error (non-fatal): {e}", file=sys.stderr)

    print("[traj_bins] Done.")


if __name__ == "__main__":
    main()
