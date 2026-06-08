"""
Stage 4.5 — Phase 4: Per-prompt and aggregate event-aligned trajectory plots.

Generates:
  Per-example (4 plots each):
    <id>_full_with_event.png         — full generation trajectory with event marker
    <id>_event_window.png            — relative-position window -500 to +1000
    <id>_layer_heatmap.png           — all-layers heatmap centered at event onset
    <id>_outcome_comparison.png      — pre/post projection comparison for this goal

  Aggregate (10 plots):
    layer22_aligned_by_sr_success.png
    layer22_aligned_by_judge_success.png
    layer22_aligned_by_adjudicated_strict.png
    layer22_aligned_by_adjudicated_lenient.png
    success_minus_failure_heatmap.png
    coverage_plot.png
    pre_event_vs_event_delta_scatter.png
    projection_vs_think_length.png
    leave_one_goal_out_effect.png
    stream_sensitivity_plot.png

Usage:
  python -m poc_stage4_5.plot_harmful_interaction_aligned_trajectories \\
      --run-dir <RUNDIR> [--review-dir <REVIEWDIR>]
"""
from __future__ import annotations

import argparse
import math
import sys
import warnings
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------

COLOR_SUCCESS = "#0072B2"
COLOR_FAILURE = "#D55E00"
COLOR_EVENT = "#CC0000"
COLOR_FINAL = "#009E73"

# Layer colors (colorblind-safe)
LAYER_COLORS = {
    13: "#0072B2",   # blue
    16: "#56B4E9",   # sky blue
    22: "#009E73",   # green (primary)
    26: "#E69F00",   # orange
    30: "#F0E442",   # yellow
    38: "#CC79A7",   # purple-pink (exploratory)
    39: "#999999",   # grey
}

SMOOTHING_WINDOW = 50  # rolling mean window (tokens)
SELECTED_LAYERS = common.SELECTED_LAYERS
PRIMARY_LAYER = common.PRIMARY_LAYER

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rolling_mean(vals: np.ndarray, window: int) -> np.ndarray:
    if len(vals) < window:
        return vals.copy()
    kernel = np.ones(window) / window
    return np.convolve(vals, kernel, mode="same")


def _safe_label(example_id: str) -> str:
    return example_id.replace("|", "_").replace("=", "_").replace("/", "_")


def _load_per_example_for_plotting(
    example_id: str,
    layers: list[int] = SELECTED_LAYERS,
) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Return {layer: (generated_token_indices, projections)} for think tokens only."""
    try:
        artifact = common.load_stage4_per_example(example_id)
    except FileNotFoundError:
        return {}
    tld = artifact.get("token_level_data", [])
    think_toks = common.get_think_tokens(tld)
    result = {}
    for layer in layers:
        idxs, projs = common.get_projections_at_layer(think_toks, layer)
        if len(idxs) > 0:
            result[layer] = (idxs, projs)
    return result


def _load_all_tokens_for_heatmap(
    example_id: str,
    layers: list[int],
    harmful_start: int,
    pre_window: int = 500,
    post_window: int = 1000,
) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Return {layer: (rel_indices, projections)} in event window for all think tokens."""
    try:
        artifact = common.load_stage4_per_example(example_id)
    except FileNotFoundError:
        return {}
    tld = artifact.get("token_level_data", [])
    think_toks = common.get_think_tokens(tld)
    result = {}
    for layer in layers:
        rel, proj = [], []
        for t in think_toks:
            r = t["generated_token_index"] - harmful_start
            if -pre_window <= r <= post_window:
                v = t["layer_projections"].get(str(layer))
                if v is not None and math.isfinite(v):
                    rel.append(r)
                    proj.append(v)
        if rel:
            result[layer] = (np.array(rel), np.array(proj))
    return result


# ---------------------------------------------------------------------------
# Per-example Plot A: full trajectory with event marker
# ---------------------------------------------------------------------------

def plot_full_with_event(
    example_id: str,
    meta: dict,
    ann: dict | None,
    output_path: Path,
    layers: list[int] = SELECTED_LAYERS,
) -> None:
    fig, ax = plt.subplots(figsize=(14, 5))
    layer_data = _load_per_example_for_plotting(example_id, layers)

    for layer in layers:
        if layer not in layer_data:
            continue
        idxs, projs = layer_data[layer]
        color = LAYER_COLORS.get(layer, "#888888")
        lw = 2.5 if layer == PRIMARY_LAYER else 1.0
        alpha = 0.9 if layer == PRIMARY_LAYER else 0.5
        label = f"L{layer}" + (" (provisional)" if layer == PRIMARY_LAYER else "")
        if layer in common.EXPLORATORY_LAYERS:
            label += " [expl]"
        ax.plot(idxs, projs, color=color, linewidth=lw, alpha=alpha, label=label)

    if ann and ann.get("annotation_status") == "annotated":
        start = int(ann["harmful_interaction_start_token"])
        ax.axvline(x=start, color=COLOR_EVENT, linewidth=2, linestyle="--",
                   label=f"Harmful onset (t={start})")
        ax.axvline(x=int(meta.get("think_token_count", 0)),
                   color=COLOR_FINAL, linewidth=1.5, linestyle=":",
                   label="Final answer start")
    elif meta.get("right_censored"):
        ax.text(0.98, 0.98, "RIGHT-CENSORED", transform=ax.transAxes,
                ha="right", va="top", color="red", fontsize=10, fontweight="bold")
    elif meta.get("thinking_segmentation_status") != "parsed_from_think_tags":
        ax.text(0.98, 0.98, "NOT SEPARABLE", transform=ax.transAxes,
                ha="right", va="top", color="red", fontsize=10, fontweight="bold")

    sr = float(meta.get("strongreject_score", 0))
    judge = meta.get("judge_score", "?")
    human_lbl = ann.get("human_label", "?") if ann else "not reviewed"
    think_len = meta.get("think_token_count", "?")
    finish = meta.get("generation_finish_reason", meta.get("finish_reason", "?"))

    title = (
        f"{example_id}\n"
        f"SR={sr:.2f} | Gemini={judge} | Human={human_lbl} | "
        f"think_len={think_len} | finish={finish}"
    )
    ax.set_title(title, fontsize=8, wrap=True)
    ax.set_xlabel("Generated token index")
    ax.set_ylabel("Projection onto provisional direction")
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Per-example Plot B: event window
# ---------------------------------------------------------------------------

def plot_event_window(
    example_id: str,
    meta: dict,
    ann: dict | None,
    output_path: Path,
    pre_window: int = 500,
    post_window: int = 1000,
    layers: list[int] = SELECTED_LAYERS,
) -> None:
    if not ann or ann.get("annotation_status") != "annotated":
        return  # cannot center without annotation

    harmful_start = int(ann["harmful_interaction_start_token"])
    fig, ax = plt.subplots(figsize=(14, 5))

    layer_data = _load_all_tokens_for_heatmap(
        example_id, layers, harmful_start, pre_window, post_window
    )

    for layer in layers:
        if layer not in layer_data:
            continue
        rel_idxs, projs = layer_data[layer]
        color = LAYER_COLORS.get(layer, "#888888")
        lw = 2.5 if layer == PRIMARY_LAYER else 1.0
        alpha = 0.9 if layer == PRIMARY_LAYER else 0.4
        label = f"L{layer}" + (" (provisional)" if layer == PRIMARY_LAYER else "")

        # Sort by relative index
        order = np.argsort(rel_idxs)
        rel_s = rel_idxs[order]
        proj_s = projs[order]

        ax.plot(rel_s, proj_s, color=color, linewidth=lw * 0.6, alpha=alpha * 0.4)
        if len(proj_s) >= SMOOTHING_WINDOW:
            smooth = _rolling_mean(proj_s, SMOOTHING_WINDOW)
            ax.plot(rel_s, smooth, color=color, linewidth=lw, alpha=alpha, label=label)
        else:
            ax.plot(rel_s, proj_s, color=color, linewidth=lw, alpha=alpha, label=label)

    ax.axvline(x=0, color=COLOR_EVENT, linewidth=2.0, linestyle="--",
               label="Harmful onset (t=0)")
    ax.axvspan(-pre_window, 0, alpha=0.05, color="red", label="Pre-event window")
    ax.axvspan(0, post_window, alpha=0.05, color="blue", label="Post-event window")

    phase = ann.get("interaction_phase", "?")
    conf = ann.get("annotation_confidence", "?")
    title = (
        f"{example_id} — Event window [{-pre_window}, +{post_window}]\n"
        f"onset_phase={phase} | confidence={conf} | smoothing={SMOOTHING_WINDOW} tokens"
    )
    ax.set_title(title, fontsize=8)
    ax.set_xlabel(f"Relative token position (0 = harmful onset)")
    ax.set_ylabel("Projection")
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Per-example Plot C: layer heatmap
# ---------------------------------------------------------------------------

def plot_layer_heatmap(
    example_id: str,
    ann: dict | None,
    output_path: Path,
    pre_window: int = 500,
    post_window: int = 1000,
    all_layers: list[int] | None = None,
) -> None:
    if not ann or ann.get("annotation_status") != "annotated":
        return

    if all_layers is None:
        all_layers = common.ALL_LAYERS

    harmful_start = int(ann["harmful_interaction_start_token"])
    layer_data = _load_all_tokens_for_heatmap(
        example_id, all_layers, harmful_start, pre_window, post_window
    )
    if not layer_data:
        return

    # Interpolate onto common relative-position grid
    rel_min, rel_max = -pre_window, post_window
    n_bins = 200
    rel_grid = np.linspace(rel_min, rel_max, n_bins)
    heatmap = np.full((len(all_layers), n_bins), float("nan"))

    for li, layer in enumerate(all_layers):
        if layer not in layer_data:
            continue
        rel_idxs, projs = layer_data[layer]
        # Simple nearest-neighbor fill
        order = np.argsort(rel_idxs)
        rel_s = rel_idxs[order].astype(float)
        proj_s = projs[order]
        for j, rg in enumerate(rel_grid):
            diffs = np.abs(rel_s - rg)
            nearest = int(np.argmin(diffs))
            if diffs[nearest] <= (rel_max - rel_min) / n_bins * 2:
                heatmap[li, j] = proj_s[nearest]

    fig, ax = plt.subplots(figsize=(14, 8))
    im = ax.imshow(
        heatmap,
        aspect="auto",
        extent=[rel_min, rel_max, -0.5, len(all_layers) - 0.5],
        origin="lower",
        cmap="RdBu_r",
    )
    ax.axvline(x=0, color="black", linewidth=2.0, linestyle="--", label="Harmful onset")
    ax.set_xlabel("Relative token position")
    ax.set_ylabel("Layer")
    ax.set_title(f"{example_id}\nLayer heatmap (unnormalized), centered at harmful onset")
    plt.colorbar(im, ax=ax, label="Projection")
    ax.legend(fontsize=8)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Per-example Plot D: pre/post comparison for this example's goal peers
# ---------------------------------------------------------------------------

def plot_outcome_comparison(
    example_id: str,
    meta: dict,
    per_example_feat_rows: list[dict],
    output_path: Path,
    layer: int = PRIMARY_LAYER,
) -> None:
    goal = int(meta.get("goal_index", -1))
    goal_rows = [r for r in per_example_feat_rows
                 if int(r.get("layer", -1)) == layer
                 and int(r.get("goal_index", -1)) == goal
                 and r.get("is_primary_analysis") is True]

    if len(goal_rows) < 2:
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, feat, label in zip(
        axes,
        ["pre_event_mean_projection", "post_event_early_mean"],
        ["Pre-event mean projection", "Post-event early mean projection"],
    ):
        success_vals = [float(r[feat]) for r in goal_rows
                         if str(r.get("sr_success")) == "True"
                         and r[feat] not in ("", None)
                         and not math.isnan(float(r[feat]))]
        failure_vals = [float(r[feat]) for r in goal_rows
                         if str(r.get("sr_success")) == "False"
                         and r[feat] not in ("", None)
                         and not math.isnan(float(r[feat]))]

        for i, (vals, color, lbl) in enumerate([
            (success_vals, COLOR_SUCCESS, f"SR success (n={len(success_vals)})"),
            (failure_vals, COLOR_FAILURE, f"SR failure (n={len(failure_vals)})"),
        ]):
            if vals:
                ax.scatter([i] * len(vals), vals, color=color, alpha=0.7, zorder=5, label=lbl)
                ax.boxplot(vals, positions=[i], widths=0.3, notch=False,
                            patch_artist=True,
                            boxprops=dict(facecolor=color, alpha=0.3))

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["SR Success", "SR Failure"])
        ax.set_ylabel("Projection")
        ax.set_title(f"Goal {goal}: {label}\nL{layer} (provisional)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Highlight current example
        cur_val = next(
            (float(r[feat]) for r in goal_rows
             if r["example_id"] == example_id
             and r[feat] not in ("", None)
             and not math.isnan(float(r[feat]))),
            None,
        )
        if cur_val is not None:
            x_pos = 0 if str(meta.get("sr_success")) == "True" else 1
            ax.scatter([x_pos], [cur_val], marker="*", s=200, color="gold",
                        zorder=10, label="This example")

    fig.suptitle(f"{example_id}\nGoal-peer comparison at Layer {layer}", fontsize=9)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Aggregate plots
# ---------------------------------------------------------------------------

def _load_group_trajectories(
    per_example_feat_rows: list[dict],
    annotations: dict[str, dict],
    layer: int,
    outcome_col: str,
    pre_window: int = 500,
    post_window: int = 1000,
    n_rel_bins: int = 150,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute mean ± bootstrap SEM trajectories for success/failure groups."""
    rel_grid = np.linspace(-pre_window, post_window, n_rel_bins)
    success_traj, failure_traj = [], []

    for r in per_example_feat_rows:
        if int(r.get("layer", -1)) != layer:
            continue
        if not r.get("is_primary_analysis"):
            continue
        eid = r["example_id"]
        ann = annotations.get(eid)
        if not ann or ann.get("annotation_status") != "annotated":
            continue
        try:
            harmful_start = int(ann["harmful_interaction_start_token"])
        except (ValueError, TypeError):
            continue

        # Load raw projection trace
        try:
            artifact = common.load_stage4_per_example(eid)
        except FileNotFoundError:
            continue
        think_toks = common.get_think_tokens(artifact.get("token_level_data", []))
        if not think_toks:
            continue

        rel_arr, proj_arr = [], []
        for t in think_toks:
            rel = t["generated_token_index"] - harmful_start
            if -pre_window <= rel <= post_window:
                v = t["layer_projections"].get(str(layer))
                if v is not None and math.isfinite(v):
                    rel_arr.append(rel)
                    proj_arr.append(v)

        if not rel_arr:
            continue

        # Interpolate onto grid
        rel_np = np.array(rel_arr, dtype=np.float64)
        proj_np = np.array(proj_arr, dtype=np.float64)
        order = np.argsort(rel_np)
        interp = np.interp(rel_grid, rel_np[order], proj_np[order],
                           left=float("nan"), right=float("nan"))

        outcome_val = str(r.get(outcome_col, ""))
        if outcome_val == "True":
            success_traj.append(interp)
        elif outcome_val == "False":
            failure_traj.append(interp)

    if not success_traj and not failure_traj:
        return rel_grid, np.array([]), np.array([]), np.array([]), np.array([])

    def _group_stats(trajs: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        if not trajs:
            return np.full(n_rel_bins, float("nan")), np.full(n_rel_bins, float("nan"))
        mat = np.array(trajs)  # shape: (n_examples, n_rel_bins)
        means = np.nanmean(mat, axis=0)
        # Bootstrap SEM
        n = mat.shape[0]
        sem = np.nanstd(mat, axis=0, ddof=1) / np.sqrt(n) if n > 1 else np.zeros(n_rel_bins)
        return means, sem

    s_mean, s_sem = _group_stats(success_traj)
    f_mean, f_sem = _group_stats(failure_traj)
    return rel_grid, s_mean, s_sem, f_mean, f_sem


def plot_aggregate_aligned_trajectories(
    per_example_feat_rows: list[dict],
    annotations: dict[str, dict],
    layer: int,
    outcome_col: str,
    outcome_label: str,
    output_path: Path,
    n_success: int = 0,
    n_failure: int = 0,
) -> None:
    rel_grid, s_mean, s_sem, f_mean, f_sem = _load_group_trajectories(
        per_example_feat_rows, annotations, layer, outcome_col
    )

    fig, ax = plt.subplots(figsize=(12, 5))
    if len(s_mean) > 0 and not np.all(np.isnan(s_mean)):
        ax.plot(rel_grid, s_mean, color=COLOR_SUCCESS, linewidth=2.0,
                label=f"SR Success (n={n_success})")
        ax.fill_between(rel_grid, s_mean - s_sem, s_mean + s_sem,
                         color=COLOR_SUCCESS, alpha=0.2)
    if len(f_mean) > 0 and not np.all(np.isnan(f_mean)):
        ax.plot(rel_grid, f_mean, color=COLOR_FAILURE, linewidth=2.0,
                label=f"SR Failure (n={n_failure})")
        ax.fill_between(rel_grid, f_mean - f_sem, f_mean + f_sem,
                         color=COLOR_FAILURE, alpha=0.2)

    ax.axvline(x=0, color=COLOR_EVENT, linewidth=2.0, linestyle="--",
               label="Harmful onset (t=0)")
    ax.axvspan(-500, 0, alpha=0.04, color="red")
    ax.axvspan(0, 1000, alpha=0.04, color="blue")
    ax.set_xlabel("Relative token position")
    ax.set_ylabel("Mean projection (provisional direction)")
    ax.set_title(
        f"Layer {layer} — Event-aligned trajectories by {outcome_label}\n"
        f"[Shaded: ±1 bootstrap SEM; direction = provisional diagnostic only]"
    )
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_coverage(
    per_example_feat_rows: list[dict],
    annotations: dict[str, dict],
    output_path: Path,
    layer: int = PRIMARY_LAYER,
    pre_window: int = 500,
    post_window: int = 1000,
) -> None:
    n_rel_bins = 151
    rel_grid = np.linspace(-pre_window, post_window, n_rel_bins)
    counts = np.zeros(n_rel_bins, dtype=int)

    for r in per_example_feat_rows:
        if int(r.get("layer", -1)) != layer or not r.get("is_primary_analysis"):
            continue
        eid = r["example_id"]
        ann = annotations.get(eid)
        if not ann or ann.get("annotation_status") != "annotated":
            continue
        try:
            harmful_start = int(ann["harmful_interaction_start_token"])
        except (ValueError, TypeError):
            continue
        try:
            artifact = common.load_stage4_per_example(eid)
        except FileNotFoundError:
            continue
        think_toks = common.get_think_tokens(artifact.get("token_level_data", []))
        covered_rels = {t["generated_token_index"] - harmful_start for t in think_toks
                         if -pre_window <= t["generated_token_index"] - harmful_start <= post_window}
        for j, rg in enumerate(rel_grid):
            if any(abs(cr - rg) <= (post_window + pre_window) / n_rel_bins for cr in covered_rels):
                counts[j] += 1

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(rel_grid, counts, color="#333333", linewidth=1.5)
    ax.axvline(x=0, color=COLOR_EVENT, linewidth=2.0, linestyle="--")
    ax.fill_between(rel_grid, 0, counts, alpha=0.3, color="steelblue")
    ax.set_xlabel("Relative token position")
    ax.set_ylabel("Number of examples contributing")
    ax.set_title("Coverage: examples contributing at each relative token position")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_success_minus_failure_heatmap(
    per_example_feat_rows: list[dict],
    annotations: dict[str, dict],
    output_path: Path,
    layers: list[int] = SELECTED_LAYERS,
    pre_window: int = 500,
    post_window: int = 1000,
) -> None:
    n_rel_bins = 100
    rel_grid = np.linspace(-pre_window, post_window, n_rel_bins)
    heatmap = np.full((len(layers), n_rel_bins), float("nan"))

    for li, layer in enumerate(layers):
        _, s_mean, _, f_mean, _ = _load_group_trajectories(
            per_example_feat_rows, annotations, layer, "sr_success",
            pre_window=pre_window, post_window=post_window, n_rel_bins=n_rel_bins,
        )
        if len(s_mean) > 0 and len(f_mean) > 0:
            diff = np.where(np.isnan(s_mean) | np.isnan(f_mean), float("nan"), s_mean - f_mean)
            heatmap[li, :] = diff

    fig, ax = plt.subplots(figsize=(12, 6))
    vmax = np.nanmax(np.abs(heatmap)) if not np.all(np.isnan(heatmap)) else 1.0
    im = ax.imshow(
        heatmap,
        aspect="auto",
        extent=[-pre_window, post_window, -0.5, len(layers) - 0.5],
        origin="lower",
        cmap="RdBu_r",
        vmin=-vmax,
        vmax=vmax,
    )
    ax.axvline(x=0, color="black", linewidth=2.0, linestyle="--")
    ax.set_yticks(range(len(layers)))
    ax.set_yticklabels([f"L{l}" + (" *" if l == PRIMARY_LAYER else "") for l in layers])
    ax.set_xlabel("Relative token position")
    ax.set_title("Success minus failure: mean projection difference\n(L22* = provisional diagnostic layer)")
    plt.colorbar(im, ax=ax, label="Success − Failure (projection)")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_scatter_pre_vs_delta(
    per_example_feat_rows: list[dict],
    output_path: Path,
    layer: int = PRIMARY_LAYER,
) -> None:
    eligible = [r for r in per_example_feat_rows
                if int(r.get("layer", -1)) == layer
                and r.get("is_primary_analysis") is True]

    pre_vals = [float(r["pre_event_mean_projection"]) for r in eligible
                 if r.get("pre_event_mean_projection") not in ("", None)
                 and not math.isnan(float(r["pre_event_mean_projection"]))]
    delta_vals = [float(r["event_delta_early"]) for r in eligible
                   if r.get("event_delta_early") not in ("", None)
                   and not math.isnan(float(r["event_delta_early"]))]
    colors = [COLOR_SUCCESS if str(r.get("sr_success")) == "True" else COLOR_FAILURE
               for r in eligible
               if r.get("pre_event_mean_projection") not in ("", None)
               and not math.isnan(float(r.get("pre_event_mean_projection") or "nan"))
               and not math.isnan(float(r.get("event_delta_early") or "nan"))]

    n = min(len(pre_vals), len(delta_vals), len(colors))
    if n == 0:
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(pre_vals[:n], delta_vals[:n], c=colors[:n], alpha=0.7, s=60, zorder=5)

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color=COLOR_SUCCESS, label="SR success"),
        Patch(color=COLOR_FAILURE, label="SR failure"),
    ], fontsize=9)
    ax.axhline(y=0, color="grey", linewidth=1.0, linestyle="--")
    ax.axvline(x=0, color="grey", linewidth=1.0, linestyle="--")
    ax.set_xlabel(f"Pre-event mean projection (L{layer}, provisional)")
    ax.set_ylabel(f"Event delta early (L{layer})")
    ax.set_title(f"Pre-event projection vs. event delta\nLayer {layer} (provisional direction)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_projection_vs_think_length(
    per_example_feat_rows: list[dict],
    output_path: Path,
    layer: int = PRIMARY_LAYER,
) -> None:
    eligible = [r for r in per_example_feat_rows
                if int(r.get("layer", -1)) == layer
                and r.get("is_primary_analysis") is True]

    think_lens = [int(r["think_token_count"]) for r in eligible
                   if r.get("post_event_early_mean") not in ("", None)
                   and not math.isnan(float(r.get("post_event_early_mean") or "nan"))]
    projs = [float(r["post_event_early_mean"]) for r in eligible
              if r.get("post_event_early_mean") not in ("", None)
              and not math.isnan(float(r.get("post_event_early_mean") or "nan"))]
    colors = [COLOR_SUCCESS if str(r.get("sr_success")) == "True" else COLOR_FAILURE
               for r in eligible
               if r.get("post_event_early_mean") not in ("", None)
               and not math.isnan(float(r.get("post_event_early_mean") or "nan"))]

    n = min(len(think_lens), len(projs), len(colors))
    if n == 0:
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(think_lens[:n], projs[:n], c=colors[:n], alpha=0.7, s=60, zorder=5)
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color=COLOR_SUCCESS, label="SR success"),
        Patch(color=COLOR_FAILURE, label="SR failure"),
    ], fontsize=9)
    ax.set_xlabel("Think token count")
    ax.set_ylabel(f"Post-event early mean projection (L{layer}, provisional)")
    ax.set_title(f"Projection vs. thinking length\nLayer {layer} (provisional direction)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_logo_effect(logo_rows: list[dict], output_path: Path) -> None:
    if not logo_rows:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    goals = [int(r["excluded_goal"]) for r in logo_rows]
    g_vals = [float(r.get("hedges_g", "nan")) for r in logo_rows]
    ax.bar(goals, g_vals, color="#0072B2", alpha=0.7)
    ax.axhline(y=0, color="grey", linewidth=1.0)
    ax.set_xlabel("Excluded goal")
    ax.set_ylabel("Hedges' g (post_event_early_mean)")
    ax.set_title("Leave-one-goal-out: effect size when each goal excluded\n(post-event early mean, L22)")
    ax.set_xticks(goals)
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_stream_sensitivity(stream_rows: list[dict], output_path: Path) -> None:
    if not stream_rows:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    convs = [int(r["excluded_stream"]) for r in stream_rows]
    g_vals = [float(r.get("hedges_g", "nan")) for r in stream_rows]
    ax.bar(range(len(convs)), g_vals, color="#D55E00", alpha=0.7)
    ax.axhline(y=0, color="grey", linewidth=1.0)
    ax.set_xticks(range(len(convs)))
    ax.set_xticklabels([f"excl conv {c}" for c in convs], rotation=45, ha="right")
    ax.set_ylabel("Hedges' g (post_event_early_mean)")
    ax.set_title("Stream sensitivity: effect size when each conversation excluded")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def generate_all_plots(run_dir: Path, review_dir: Path) -> int:
    """Load analysis outputs and generate all plots."""
    per_example_csv = run_dir / "analysis" / "event_aligned_per_example.csv"
    if not per_example_csv.exists():
        print(f"ERROR: {per_example_csv} not found. Run analysis first.", file=sys.stderr)
        return 1

    per_example_feat_rows = common.read_csv_as_list(per_example_csv)
    if not per_example_feat_rows:
        print("No per-example feature rows found; skipping plots.", file=sys.stderr)
        return 0

    # Convert types
    for r in per_example_feat_rows:
        r["is_primary_analysis"] = r.get("is_primary_analysis") == "True"
        for k in ["goal_index", "attack_iteration", "conversation_id",
                   "think_token_count", "layer", "harmful_interaction_start_token"]:
            try:
                r[k] = int(r[k]) if r.get(k) not in ("", None) else 0
            except (ValueError, TypeError):
                r[k] = 0
        for k in ["pre_event_mean_projection", "post_event_early_mean", "event_delta_early",
                   "relative_onset_position", "hedges_g", "strongreject_score"]:
            try:
                r[k] = float(r[k]) if r.get(k) not in ("", None) else float("nan")
            except (ValueError, TypeError):
                r[k] = float("nan")

    # Load annotations
    annotations_path = review_dir / "harmful_interaction_annotations.csv"
    annotations: dict[str, dict] = {}
    if annotations_path.exists():
        for row in common.read_csv_as_list(annotations_path):
            eid = row.get("example_id")
            if eid:
                annotations[eid] = row

    # Load metadata
    dataset_meta = common.load_analysis_dataset()
    meta_map = {r["example_id"]: r for r in dataset_meta}

    # Load review progress
    progress_path = review_dir / "manual_adjudication_progress.csv"
    reviews: dict[str, dict] = {}
    if progress_path.exists():
        for row in common.read_csv_as_list(progress_path):
            eid = row.get("example_id")
            if eid:
                reviews[eid] = row

    plots_per = run_dir / "plots" / "per_example"
    plots_agg = run_dir / "plots" / "aggregate"
    plots_per.mkdir(parents=True, exist_ok=True)
    plots_agg.mkdir(parents=True, exist_ok=True)

    n_per_plots = 0
    annotated_eids = [r["example_id"] for r in per_example_feat_rows
                       if r.get("layer") == PRIMARY_LAYER
                       and r.get("is_primary_analysis")]

    print(f"Generating per-example plots for {len(annotated_eids)} examples...")
    for eid in annotated_eids:
        meta = meta_map.get(eid, {})
        ann = annotations.get(eid)
        review = reviews.get(eid)
        if review:
            meta["human_label"] = review.get("human_label", "")

        safe_id = _safe_label(eid)

        plot_full_with_event(eid, meta, ann,
                              plots_per / f"{safe_id}_full_with_event.png")
        plot_event_window(eid, meta, ann,
                           plots_per / f"{safe_id}_event_window.png")
        plot_layer_heatmap(eid, ann,
                            plots_per / f"{safe_id}_layer_heatmap.png")
        plot_outcome_comparison(eid, meta, per_example_feat_rows,
                                 plots_per / f"{safe_id}_outcome_comparison.png")
        n_per_plots += 4

    print(f"Generated {n_per_plots} per-example plots.")

    # Count outcomes
    n_sr_s = sum(1 for r in per_example_feat_rows
                  if r.get("layer") == PRIMARY_LAYER and r.get("is_primary_analysis")
                  and str(r.get("sr_success")) == "True")
    n_sr_f = sum(1 for r in per_example_feat_rows
                  if r.get("layer") == PRIMARY_LAYER and r.get("is_primary_analysis")
                  and str(r.get("sr_success")) == "False")

    print("Generating aggregate plots...")

    # 1–4: aligned trajectories by outcome
    for out_col, out_lbl, fname in [
        ("sr_success", "StrongREJECT", "layer22_aligned_by_sr_success.png"),
        ("judge_success", "Gemini judge", "layer22_aligned_by_judge_success.png"),
        ("human_success_strict", "Adjudicated strict", "layer22_aligned_by_adjudicated_strict.png"),
        ("human_success_lenient", "Adjudicated lenient", "layer22_aligned_by_adjudicated_lenient.png"),
    ]:
        plot_aggregate_aligned_trajectories(
            per_example_feat_rows, annotations, PRIMARY_LAYER, out_col, out_lbl,
            plots_agg / fname, n_success=n_sr_s, n_failure=n_sr_f,
        )

    # 5: heatmap
    plot_success_minus_failure_heatmap(
        per_example_feat_rows, annotations, plots_agg / "success_minus_failure_heatmap.png"
    )

    # 6: coverage
    plot_coverage(
        per_example_feat_rows, annotations, plots_agg / "coverage_plot.png"
    )

    # 7: scatter
    plot_scatter_pre_vs_delta(
        per_example_feat_rows, plots_agg / "pre_event_vs_event_delta_scatter.png"
    )

    # 8: think length
    plot_projection_vs_think_length(
        per_example_feat_rows, plots_agg / "projection_vs_think_length.png"
    )

    # 9: LOGO
    logo_csv = run_dir / "analysis" / "leave_one_goal_out.csv"
    if logo_csv.exists():
        logo_rows = [
            {**r, "hedges_g": float(r.get("hedges_g", "nan") or "nan"),
             "excluded_goal": int(r.get("excluded_goal", 0))}
            for r in common.read_csv_as_list(logo_csv)
        ]
        plot_logo_effect(logo_rows, plots_agg / "leave_one_goal_out_effect.png")

    # 10: stream sensitivity
    stream_csv = run_dir / "analysis" / "stream_sensitivity.csv"
    if stream_csv.exists():
        stream_rows = [
            {**r, "hedges_g": float(r.get("hedges_g", "nan") or "nan"),
             "excluded_stream": int(r.get("excluded_stream", 0))}
            for r in common.read_csv_as_list(stream_csv)
        ]
        plot_stream_sensitivity(stream_rows, plots_agg / "stream_sensitivity_plot.png")

    agg_plots = list(plots_agg.glob("*.png"))
    print(f"Generated {len(agg_plots)} aggregate plots.")
    print(f"Plots complete: {run_dir / 'plots'}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stage 4.5 event-aligned trajectory plots.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Run directory containing analysis/ outputs.",
    )
    p.add_argument(
        "--review-dir",
        type=Path,
        default=common.DEFAULT_REVIEW_DIR,
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.run_dir.exists():
        print(f"ERROR: run-dir does not exist: {args.run_dir}", file=sys.stderr)
        return 1
    return generate_all_plots(args.run_dir, args.review_dir)


if __name__ == "__main__":
    sys.exit(main())
