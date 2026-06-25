"""
Analyze trajectory divergence point — Q3: when in the reasoning trajectory do
successful attacks diverge from failures?

Reads existing Stage 4B trajectory bin analysis outputs and identifies:
  - Earliest bin (normalized thinking-progress position) where success/failure diverge
  - Stability of the effect across the thinking trajectory
  - Pattern classification: early_stable / late_onset / progressive / no_divergence

Key inputs (pre-computed on disk):
  outputs/stage4/{model}/trajectory_bin_analysis_{variant}/bin_effect_size.csv

Output:
  outputs/stage4/factorial_analysis/trajectory_divergence_summary.json
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone


MODELS = {
    "qwen3": {
        "dir": "outputs/stage4/qwen3-14b",
        "n_layers": 40,
        "label": "Qwen3-14B",
    },
    "gemma4": {
        "dir": "outputs/stage4/gemma4-e4b-it",
        "n_layers": 42,
        "label": "Gemma4-E4B-IT",
    },
}

# Minimum |Cohen's d| to count a bin as diverged
DIVERGENCE_THRESHOLD = 0.10

# Cohen's d thresholds
D_SMALL = 0.20
D_MEDIUM = 0.50
D_LARGE = 0.80


def classify_pattern(effect_sizes: list[float], threshold: float = DIVERGENCE_THRESHOLD) -> str:
    """
    Classify the divergence pattern from a list of per-bin Cohen's d values.
    Bins are ordered from bin 0 (5%) to bin 9 (95%).
    """
    sig = [abs(d) >= threshold for d in effect_sizes]
    n = len(sig)
    if not any(sig):
        return "no_divergence"

    first_sig = next(i for i, s in enumerate(sig) if s)

    # Fraction of significant bins
    frac_sig = sum(sig) / n
    # Check if effect is increasing in the second half vs first half
    mid = n // 2
    mean_first = np.mean(np.abs(effect_sizes[:mid]))
    mean_second = np.mean(np.abs(effect_sizes[mid:]))

    if first_sig == 0 and frac_sig >= 0.7:
        return "early_stable"
    elif first_sig == 0 and frac_sig < 0.7:
        return "early_unstable"
    elif first_sig >= mid and mean_second > mean_first * 1.3:
        return "late_onset"
    elif mean_second > mean_first * 1.3:
        return "progressive"
    else:
        return "mid_onset"


def analyze_variant(model_dir: Path, variant: str, n_layers: int) -> dict | None:
    bin_csv = model_dir / f"trajectory_bin_analysis_{variant}" / "bin_effect_size.csv"
    if not bin_csv.exists():
        return None

    df = pd.read_csv(bin_csv)
    if df.empty:
        return None

    results_by_layer_rank = {}
    for (layer, rank), grp in df.groupby(["layer", "subspace_rank"]):
        grp_sorted = grp.sort_values("bin")
        ds = grp_sorted["cohens_d"].tolist()
        norm_pos = grp_sorted["normalized_position"].tolist()
        sig = [abs(d) >= DIVERGENCE_THRESHOLD for d in ds]

        first_sig_bin = next((i for i, s in enumerate(sig) if s), None)
        first_sig_pos = norm_pos[first_sig_bin] if first_sig_bin is not None else None
        pattern = classify_pattern(ds)

        results_by_layer_rank[f"L{layer}_rank{rank}"] = {
            "layer": int(layer),
            "layer_normalized": round(layer / (n_layers - 1), 3),
            "subspace_rank": int(rank),
            "effect_sizes": [round(d, 4) for d in ds],
            "normalized_positions": [round(p, 2) for p in norm_pos],
            "first_significant_bin": first_sig_bin,
            "first_significant_position": round(first_sig_pos, 2) if first_sig_pos is not None else None,
            "pattern": pattern,
            "max_abs_d": round(max(abs(d) for d in ds), 4),
            "mean_abs_d": round(np.mean(np.abs(ds)), 4),
        }

    # Find the best (highest max_abs_d) layer × rank combination
    best_key = max(
        results_by_layer_rank,
        key=lambda k: results_by_layer_rank[k]["max_abs_d"],
    )
    best = results_by_layer_rank[best_key]

    # Build per-bin summary table for best layer × rank
    bin_table = []
    for i, (d, pos) in enumerate(zip(best["effect_sizes"], best["normalized_positions"])):
        bin_table.append({
            "bin": i,
            "normalized_position": pos,
            "cohens_d": d,
            "significant": abs(d) >= DIVERGENCE_THRESHOLD,
        })

    return {
        "variant": variant,
        "best_layer_rank": best_key,
        "best_layer": best["layer"],
        "best_layer_normalized": best["layer_normalized"],
        "best_subspace_rank": best["subspace_rank"],
        "best_max_abs_d": best["max_abs_d"],
        "best_mean_abs_d": best["mean_abs_d"],
        "best_pattern": best["pattern"],
        "best_first_significant_position": best["first_significant_position"],
        "best_bin_trajectory": bin_table,
        "all_layer_ranks": results_by_layer_rank,
    }


def make_interpretation(model_key: str, variant_results: dict) -> list[str]:
    lines = []
    beh = variant_results.get("behavioral")
    if beh is None:
        return ["Behavioral trajectory bin analysis not available for this model."]

    pos = beh["best_first_significant_position"]
    pattern = beh["best_pattern"]
    max_d = beh["best_max_abs_d"]
    mean_d = beh["best_mean_abs_d"]
    layer_norm = beh["best_layer_normalized"]

    if pattern == "early_stable":
        lines.append(
            f"Divergence present from the VERY START of thinking "
            f"(first significant position: {pos*100:.0f}% through thinking). "
            f"Effect is stable throughout the reasoning trajectory "
            f"(max |d|={max_d:.3f}, mean |d|={mean_d:.3f}). "
            f"Best layer: {beh['best_layer']} (normalized: {layer_norm:.2f}). "
            "This rules out a late critical transition — the attack's representational "
            "effect is established from the beginning of extended thinking."
        )
    elif pattern == "late_onset":
        lines.append(
            f"Divergence LATE in the reasoning trajectory (first significant: {pos*100:.0f}%). "
            f"Suggests a critical transition or decision point late in thinking. "
            f"Max |d|={max_d:.3f} at best layer {beh['best_layer']}."
        )
    elif pattern == "progressive":
        lines.append(
            f"Progressive divergence — effect grows throughout thinking. "
            f"First significant at {pos*100:.0f}%, strengthens to max |d|={max_d:.3f}. "
            "Suggests cumulative reasoning entanglement."
        )
    elif pattern == "no_divergence":
        lines.append(
            f"No significant divergence detected (threshold |d| >= {DIVERGENCE_THRESHOLD}). "
            f"Behavioral subspace does not separate success/failure in trajectory bins."
        )
    else:
        lines.append(
            f"Pattern: {pattern}. First significant at {pos*100:.0f}% if pos else 'none'. "
            f"Max |d|={max_d:.3f}."
        )

    return lines


def analyze_model(model_key: str, cfg: dict, threshold: float = DIVERGENCE_THRESHOLD) -> dict:
    model_dir = Path(cfg["dir"])
    n_layers = cfg["n_layers"]

    # Analyze all available trajectory variants
    variant_results = {}
    for traj_dir in sorted(model_dir.glob("trajectory_bin_analysis_*")):
        variant = traj_dir.name.replace("trajectory_bin_analysis_", "")
        result = analyze_variant(model_dir, variant, n_layers)
        if result is not None:
            variant_results[variant] = result
            print(f"  {variant}: best={result['best_layer_rank']} "
                  f"max_d={result['best_max_abs_d']:.3f} "
                  f"pattern={result['best_pattern']} "
                  f"first_sig={result['best_first_significant_position']}")

    if not variant_results:
        print(f"  No trajectory bin analysis found for {cfg['label']}")

    return {
        "model": model_key,
        "label": cfg["label"],
        "n_layers": n_layers,
        "variants_available": list(variant_results.keys()),
        "variants": variant_results,
        "interpretation": make_interpretation(model_key, variant_results),
    }


def main():
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", nargs="+", choices=list(MODELS), default=list(MODELS))
    ap.add_argument("--output-dir", default="outputs/stage4/factorial_analysis")
    ap.add_argument("--threshold", type=float, default=DIVERGENCE_THRESHOLD,
                    help=f"Minimum |Cohen's d| to count as significant (default: {DIVERGENCE_THRESHOLD})")
    args = ap.parse_args()

    threshold = args.threshold
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}
    for model_key in args.models:
        cfg = MODELS[model_key]
        print(f"\n=== {cfg['label']} ===")
        res = analyze_model(model_key, cfg, threshold=threshold)
        all_results[model_key] = res

        print(f"  Variants found: {res['variants_available']}")
        for line in res["interpretation"]:
            print(f"  -> {line}")

    output = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "description": "Trajectory divergence analysis — where in reasoning do attacks separate from failures (Q3)",
        "divergence_threshold": threshold,
        "models": all_results,
        "cross_model_summary": _cross_model_summary(all_results),
    }

    out_path = out_dir / "trajectory_divergence_summary.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nSaved: {out_path}")


def _cross_model_summary(results: dict) -> dict:
    summary = {}
    for mk, r in results.items():
        beh = r["variants"].get("behavioral")
        if beh:
            summary[mk] = {
                "pattern": beh["best_pattern"],
                "first_significant_position_pct": (
                    round(beh["best_first_significant_position"] * 100, 0)
                    if beh["best_first_significant_position"] is not None else None
                ),
                "max_abs_d": beh["best_max_abs_d"],
                "mean_abs_d": beh["best_mean_abs_d"],
                "best_layer_normalized": beh["best_layer_normalized"],
            }
        else:
            summary[mk] = {"pattern": "not_computed"}
    return summary


if __name__ == "__main__":
    main()
