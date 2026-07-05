"""
Stage 9c — Cross-model join of Qwen3-14B and Gemma4-E4B-it Stage 9a/9b results.

Joins the paired A/E taxonomy deltas by goal_index|condition (models share the
same 11 canonical goals) and the per-position/per-layer LOGO-AUC separability
tables by (condition, position_name, normalized_depth) — layers are compared
by normalized depth (layer_index / (n_layers-1)) since Qwen3 (41 layers) and
Gemma4 (43 layers) have different absolute depths.

This is a descriptive cross-model comparison only: agreement/divergence in
*which* goals or *which* early positions carry a success signal, not a claim
that either model's mechanism causes the other's behavior.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


MODEL_DIR_NAME = {"qwen3": "qwen", "gemma4": "gemma"}


def _load_paired_summary(run_dir: Path, model: str) -> dict:
    path = run_dir / MODEL_DIR_NAME[model] / "analysis" / "paired_ae_summary.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _load_separability(run_dir: Path, model: str) -> pd.DataFrame:
    path = run_dir / MODEL_DIR_NAME[model] / "analysis" / "early_token_separability.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _cross_model_paired_deltas(run_dir: Path, models: list[str]) -> pd.DataFrame:
    rows = []
    for model in models:
        csv_path = run_dir / MODEL_DIR_NAME[model] / "analysis" / "paired_A_vs_E_deltas.csv"
        if not csv_path.exists():
            continue
        df = pd.read_csv(csv_path)
        df["model"] = model
        rows.append(df)
    if not rows:
        return pd.DataFrame()
    combined = pd.concat(rows, ignore_index=True)
    pivot = combined.pivot_table(
        index=["field", "goal_index"], columns="model", values="delta"
    ).reset_index()
    if set(models).issubset(pivot.columns):
        pivot["cross_model_agree_sign"] = (
            (pivot[models[0]] > 0) == (pivot[models[1]] > 0)
        )
    return pivot


def _cross_model_separability(run_dir: Path, models: list[str], depth_bins: int = 10) -> pd.DataFrame:
    frames = []
    for model in models:
        df = _load_separability(run_dir, model)
        if df.empty:
            continue
        df = df.copy()
        df["depth_bin"] = (df["normalized_depth"] * depth_bins).round().astype(int)
        frames.append(df)
    if len(frames) < 2:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    grouped = (
        combined.groupby(["model", "condition", "position_name", "depth_bin"])["logo_auc"]
        .mean()
        .reset_index()
    )
    pivot = grouped.pivot_table(
        index=["condition", "position_name", "depth_bin"], columns="model", values="logo_auc"
    ).reset_index()
    return pivot


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--models", nargs="+", default=["qwen3", "gemma4"])
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    out_dir = run_dir / "combined_analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries = {m: _load_paired_summary(run_dir, m) for m in args.models}
    missing = [m for m, s in summaries.items() if not s]
    if missing:
        print(f"WARNING: missing per-model paired_ae_summary.json for: {missing} "
              f"— run analyze_paired_ae.py for those models first.")

    paired_cross = _cross_model_paired_deltas(run_dir, args.models)
    if not paired_cross.empty:
        paired_cross.to_csv(out_dir / "cross_model_paired_A_vs_E_deltas.csv", index=False)
        print(f"Wrote {len(paired_cross)} rows to cross_model_paired_A_vs_E_deltas.csv")
        if "cross_model_agree_sign" in paired_cross.columns:
            success_rows = paired_cross[paired_cross["field"] == "strongreject_is_success"]
            if not success_rows.empty:
                agree_rate = success_rows["cross_model_agree_sign"].mean()
                print(f"strongreject_is_success: cross-model sign agreement rate "
                      f"across goals = {agree_rate:.2f} ({len(success_rows)} goals)")

    sep_cross = _cross_model_separability(run_dir, args.models)
    if not sep_cross.empty:
        sep_cross.to_csv(out_dir / "cross_model_early_token_separability.csv", index=False)
        print(f"Wrote {len(sep_cross)} rows to cross_model_early_token_separability.csv")
        early_bins = sep_cross[sep_cross["depth_bin"] <= 2]
        print("Early-depth-bin (0-2) LOGO-AUC by position, both models:")
        print(early_bins.to_string(index=False))
    else:
        print("Insufficient per-model separability tables to build cross-model comparison "
              "(run analyze_early_token_signals.py for each model first).")

    report = {
        "models": args.models,
        "paired_summaries": summaries,
        "cross_model_paired_rows": len(paired_cross),
        "cross_model_separability_rows": len(sep_cross),
    }
    with (out_dir / "cross_model_summary.json").open("w") as f:
        json.dump(report, f, indent=2)
    print(f"Wrote combined summary to {out_dir / 'cross_model_summary.json'}")


if __name__ == "__main__":
    main()
