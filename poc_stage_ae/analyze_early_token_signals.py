"""
Stage 9b — Per-position/per-layer separability of attack success from early
hidden states, per model/condition.

Answers: is attack success (StrongREJECT) already visible in the first few
generated tokens, and how does that separability evolve across layers?

Evaluation is grouped leave-one-goal-out (LOGO) across the 11 goal_index
groups, NOT in-sample AUC — a classifier fit on 10 goals is scored on the
held-out goal's rows only, and the reported AUC pools out-of-fold scores
across all 11 folds. This avoids the goal-identity shortcut a model could
otherwise exploit (rows from the same goal share surface features).

The "classifier" is a Fisher-style mean-difference direction (success-mean
minus failure-mean hidden state, per position/layer), computed once per fold
from closed-form per-goal class sums so the O(goals) tensor pass is done only
twice (once to accumulate sums, once to score) regardless of how many folds/
positions/layers are evaluated.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch


MODEL_DIR_NAME = {"qwen3": "qwen", "gemma4": "gemma"}


def _label_map(scores_path: Path, condition: str) -> dict[str, bool]:
    labels: dict[str, bool] = {}
    with scores_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("condition") != condition or r.get("generation_status") != "ok":
                continue
            v = r.get("strongreject_is_success")
            if v is not None:
                labels[r["row_key"]] = bool(v)
    return labels


def _goal_shards(hidden_dir: Path, model: str, condition: str) -> list[int]:
    goals = []
    for meta_path in sorted(hidden_dir.glob(f"{model}_{condition}_goal*_metadata.parquet")):
        stem = meta_path.stem.removesuffix("_metadata")
        goal_str = stem.rsplit("goal", 1)[-1]
        goals.append(int(goal_str))
    return sorted(goals)


def _load_goal(hidden_dir: Path, model: str, condition: str, goal: int):
    meta = pd.read_parquet(hidden_dir / f"{model}_{condition}_goal{goal}_metadata.parquet")
    tensor_path = hidden_dir / f"{model}_{condition}_goal{goal}.pt"
    tensor = torch.load(tensor_path, map_location="cpu")
    return meta, tensor


def _rowkey_labels(meta: pd.DataFrame, labels: dict[str, bool]) -> np.ndarray:
    row_keys = meta.drop_duplicates("row_key").sort_values("row_offset")["row_key"].tolist()
    return np.array([labels.get(rk) for rk in row_keys], dtype=object)


def _auc_from_scores(scores: np.ndarray, y: np.ndarray) -> float | None:
    mask = np.array([v is not None for v in y])
    scores, y = scores[mask], np.array([bool(v) for v in y[mask]])
    n_pos, n_neg = y.sum(), (~y).sum()
    if n_pos == 0 or n_neg == 0:
        return None
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1)
    # average ranks for ties
    sorted_scores = scores[order]
    i = 0
    while i < len(sorted_scores):
        j = i
        while j + 1 < len(sorted_scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        if j > i:
            avg_rank = ranks[order[i:j + 1]].mean()
            ranks[order[i:j + 1]] = avg_rank
        i = j + 1
    sum_ranks_pos = ranks[y].sum()
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
    return float(auc)


def analyze_condition(hidden_dir: Path, model: str, condition: str, labels: dict[str, bool]) -> pd.DataFrame:
    goals = _goal_shards(hidden_dir, model, condition)
    if not goals:
        return pd.DataFrame()

    per_goal_meta = {}
    per_goal_tensor = {}
    per_goal_y = {}
    position_names = None
    n_layers = None
    for g in goals:
        meta, tensor = _load_goal(hidden_dir, model, condition, g)
        per_goal_meta[g] = meta
        per_goal_tensor[g] = tensor
        per_goal_y[g] = _rowkey_labels(meta, labels)
        pos_order = meta.drop_duplicates("position_name").sort_values("position_offset")
        if position_names is None:
            position_names = pos_order["position_name"].tolist()
            n_layers = int(meta["layer_count"].iloc[0])

    d_model = next(iter(per_goal_tensor.values())).shape[-1]
    n_pos = len(position_names)

    sum_pos = {g: np.zeros((n_pos, n_layers, d_model), dtype=np.float64) for g in goals}
    sum_neg = {g: np.zeros((n_pos, n_layers, d_model), dtype=np.float64) for g in goals}
    cnt_pos = {g: 0 for g in goals}
    cnt_neg = {g: 0 for g in goals}

    for g in goals:
        t = per_goal_tensor[g].to(torch.float32).numpy()
        y = per_goal_y[g]
        for row_idx, label in enumerate(y):
            if label is None:
                continue
            if label:
                sum_pos[g] += t[row_idx]
                cnt_pos[g] += 1
            else:
                sum_neg[g] += t[row_idx]
                cnt_neg[g] += 1

    total_sum_pos = sum(sum_pos.values())
    total_sum_neg = sum(sum_neg.values())
    total_cnt_pos = sum(cnt_pos.values())
    total_cnt_neg = sum(cnt_neg.values())

    pooled_scores = {(p, l): [] for p in range(n_pos) for l in range(n_layers)}
    pooled_labels = {(p, l): [] for p in range(n_pos) for l in range(n_layers)}

    applicable_by_pos = {}
    for pos_idx, pos_name in enumerate(position_names):
        applicable_by_pos[pos_idx] = bool(
            per_goal_meta[goals[0]].loc[
                per_goal_meta[goals[0]]["position_name"] == pos_name, "position_applicable"
            ].iloc[0]
        )

    for g in goals:
        train_cnt_pos = total_cnt_pos - cnt_pos[g]
        train_cnt_neg = total_cnt_neg - cnt_neg[g]
        if train_cnt_pos == 0 or train_cnt_neg == 0:
            continue
        train_mean_pos = (total_sum_pos - sum_pos[g]) / train_cnt_pos
        train_mean_neg = (total_sum_neg - sum_neg[g]) / train_cnt_neg
        direction = train_mean_pos - train_mean_neg  # (n_pos, n_layers, d_model)

        t = per_goal_tensor[g].to(torch.float32).numpy()
        y = per_goal_y[g]
        for pos_idx in range(n_pos):
            if not applicable_by_pos[pos_idx]:
                continue
            for layer_idx in range(n_layers):
                dvec = direction[pos_idx, layer_idx]
                norm = np.linalg.norm(dvec)
                if norm == 0:
                    continue
                dvec = dvec / norm
                proj = t[:, pos_idx, layer_idx, :] @ dvec
                for row_idx, label in enumerate(y):
                    if label is None:
                        continue
                    pooled_scores[(pos_idx, layer_idx)].append(proj[row_idx])
                    pooled_labels[(pos_idx, layer_idx)].append(label)

    records = []
    for pos_idx, pos_name in enumerate(position_names):
        if not applicable_by_pos[pos_idx]:
            continue
        for layer_idx in range(n_layers):
            scores = np.array(pooled_scores[(pos_idx, layer_idx)])
            ys = np.array(pooled_labels[(pos_idx, layer_idx)], dtype=object)
            if len(scores) == 0:
                continue
            auc = _auc_from_scores(scores, ys)
            records.append({
                "model": model, "condition": condition, "position_name": pos_name,
                "position_index": pos_idx, "layer_index": layer_idx,
                "n_layers_total": n_layers,
                "normalized_depth": layer_idx / (n_layers - 1) if n_layers > 1 else 0.0,
                "n_rows_pooled": len(scores),
                "logo_auc": auc,
            })
    return pd.DataFrame.from_records(records)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=["qwen3", "gemma4"])
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--conditions", nargs="+", default=["A", "E"])
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    model_dir = MODEL_DIR_NAME[args.model]
    hidden_dir = run_dir / model_dir / "hidden_states" / "shards"
    scores_path = run_dir / model_dir / "scoring" / f"{args.model}_scores.jsonl"
    out_dir = run_dir / model_dir / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_frames = []
    for condition in args.conditions:
        labels = _label_map(scores_path, condition)
        print(f"[{args.model}/{condition}] {len(labels)} labeled rows")
        df = analyze_condition(hidden_dir, args.model, condition, labels)
        if df.empty:
            print(f"[{args.model}/{condition}] no hidden-state shards found, skipping")
            continue
        all_frames.append(df)

    if not all_frames:
        print("No conditions produced results — nothing written.")
        return

    combined = pd.concat(all_frames, ignore_index=True)
    out_csv = out_dir / "early_token_separability.csv"
    combined.to_csv(out_csv, index=False)
    print(f"Wrote {len(combined)} (position, layer, condition) rows to {out_csv}")

    top = (
        combined.sort_values("logo_auc", ascending=False)
        .groupby("condition")
        .head(5)
    )
    print("Top-5 (position, layer) by LOGO AUC per condition:")
    print(top[["condition", "position_name", "layer_index", "normalized_depth", "logo_auc"]].to_string(index=False))

    early_positions = ["prefill_last", "startofthink", "think_content_1", "answer_content_1"]
    early = combined[combined["position_name"].isin(early_positions)]
    early_summary = (
        early.groupby(["condition", "position_name"])["logo_auc"]
        .agg(["mean", "max", "count"])
        .reset_index()
    )
    early_summary.to_csv(out_dir / "early_position_summary.csv", index=False)
    print("Early-position AUC summary (mean/max across layers):")
    print(early_summary.to_string(index=False))


if __name__ == "__main__":
    main()
