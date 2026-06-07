"""
Stage 4 — Refusal Direction Dynamics Analysis
==============================================
Loads all 42 per-example token dynamics files and produces four thesis figures:

  Figure 1  Layer-22 projection trajectory (think → final phase),
            success vs. failure, with ±1σ band.

  Figure 2  Layer-by-layer discrimination: mean(success) − mean(failure)
            during think phase and final phase separately.

  Figure 3  Per-phase summary box plots (think vs. final) at layer 22.

  Figure 4  Example heatmaps (layer × token) for one clear success
            and one clear failure.

Run:
    conda activate poc_stage2
    python -m poc_stage4.plot_refusal_dynamics
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE        = Path("outputs/stage4/token_dynamics/full_20260604_101929")
OUT_DIR     = BASE / "plots_analysis"
LAYER       = 22          # primary analysis layer (best separation score)
N_BINS      = 80          # bins for normalized-position trajectory
SUCCESS_THR = 0.5         # strongreject_score threshold for "attack succeeded"
SMOOTH_W    = 5           # smoothing kernel width for trajectory plots (bins)
DPI         = 150

COLORS = {
    "success_think": "#d62728",   # red
    "failure_think": "#1f77b4",   # blue
    "success_final": "#ff7f0e",   # orange
    "failure_final": "#17becf",   # cyan
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_examples(base: Path) -> list[dict]:
    examples = []
    for f in sorted((base / "per_example").glob("*.json")):
        d = json.loads(f.read_text())
        # pre-index tokens by role
        think_toks = [t for t in d["token_level_data"] if t["role_or_part"] == "think"]
        final_toks = [t for t in d["token_level_data"] if t["role_or_part"] == "final"]
        d["_think"] = think_toks
        d["_final"] = final_toks
        d["_success"] = d.get("strongreject_score", 0.0) >= SUCCESS_THR
        examples.append(d)
    return examples


def proj_series(toks: list[dict], layer: int) -> list[float]:
    key = str(layer)
    return [t["layer_projections"][key] for t in toks if t["layer_projections"].get(key) is not None]


# ---------------------------------------------------------------------------
# Helper: binned mean ± std over normalized position [0, 1]
# ---------------------------------------------------------------------------

def binned_stats(
    examples: list[dict],
    phase: str,       # "think" or "final"
    layer: int,
    n_bins: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (bin_centres, means, stds) using normalised position within phase."""
    bins: list[list[float]] = [[] for _ in range(n_bins)]
    for ex in examples:
        toks = ex[f"_{phase}"]
        vals = proj_series(toks, layer)
        if not vals:
            continue
        n = len(vals)
        for i, v in enumerate(vals):
            b = min(int(i / n * n_bins), n_bins - 1)
            bins[b].append(v)
    centres = (np.arange(n_bins) + 0.5) / n_bins
    means = np.array([np.nanmean(b) if b else np.nan for b in bins])
    stds  = np.array([np.nanstd(b)  if b else np.nan for b in bins])
    return centres, means, stds


def smooth(arr: np.ndarray, w: int) -> np.ndarray:
    if w <= 1:
        return arr
    kernel = np.ones(w) / w
    return np.convolve(arr, kernel, mode="same")


# ---------------------------------------------------------------------------
# Figure 1: Layer-22 trajectory (think + final phase)
# ---------------------------------------------------------------------------

def fig_trajectory(success: list[dict], failure: list[dict], out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=False)
    fig.suptitle(
        f"Refusal Direction Projection — Layer {LAYER} — Trajectory by Phase\n"
        f"(n={len(success)} success, n={len(failure)} failure; "
        f"StrongREJECT ≥ {SUCCESS_THR})",
        fontsize=12, y=1.01,
    )

    for ax, phase, title in zip(
        axes,
        ["think", "final"],
        ["Thinking Phase (CoT)", "Final Answer Phase"],
    ):
        for group, label, base_color, fill_color in [
            (success, f"Success (n={len(success)})", COLORS["success_think" if phase=="think" else "success_final"], "#ffcccc" if "success" in COLORS["success_think"] else "#ffe0cc"),
            (failure, f"Failure (n={len(failure)})", COLORS["failure_think" if phase=="think" else "failure_final"], "#cce0ff"),
        ]:
            grp_has_phase = [ex for ex in group if ex[f"_{phase}"]]
            if not grp_has_phase:
                continue
            centres, means, stds = binned_stats(grp_has_phase, phase, LAYER, N_BINS)
            sm = smooth(means, SMOOTH_W)
            ss = smooth(stds, SMOOTH_W)

            x_pct = centres * 100
            ax.plot(x_pct, sm, color=base_color, linewidth=2, label=label)
            ax.fill_between(x_pct, sm - ss, sm + ss, color=base_color, alpha=0.18)

        ax.set_xlabel("Relative position within phase (%)", fontsize=11)
        ax.set_ylabel(f"Layer-{LAYER} refusal direction projection", fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 100)

    plt.tight_layout()
    path = out / "fig1_layer22_trajectory.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Figure 2: Layer-by-layer discrimination
# ---------------------------------------------------------------------------

def layer_mean(examples: list[dict], phase: str, layer: int) -> float:
    vals = []
    for ex in examples:
        toks = ex[f"_{phase}"]
        vals.extend(proj_series(toks, layer))
    return float(np.nanmean(vals)) if vals else float("nan")


def fig_layer_discrimination(
    success: list[dict], failure: list[dict], out: Path, n_layers: int = 40
) -> None:
    layers = list(range(n_layers))

    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
    fig.suptitle(
        "Layer-by-Layer Refusal Direction Projection  —  Mean per Group\n"
        f"(n={len(success)} success, n={len(failure)} failure)",
        fontsize=12, y=1.01,
    )

    for ax, phase, title in zip(
        axes,
        ["think", "final"],
        ["Thinking Phase (CoT)", "Final Answer Phase"],
    ):
        s_means = [layer_mean(success, phase, li) for li in layers]
        f_means = [layer_mean(failure, phase, li) for li in layers]

        ax.plot(layers, s_means, color=COLORS["success_think"], lw=2,
                marker="o", markersize=3, label=f"Success (n={len(success)})")
        ax.plot(layers, f_means, color=COLORS["failure_think"], lw=2,
                marker="o", markersize=3, label=f"Failure (n={len(failure)})")
        ax.axvline(LAYER, color="gray", linestyle="--", alpha=0.6, label=f"Layer {LAYER} (selected)")

        # Shade the gap
        s_arr = np.array(s_means)
        f_arr = np.array(f_means)
        ax.fill_between(layers, f_arr, s_arr,
                        where=s_arr > f_arr, color=COLORS["success_think"], alpha=0.12)
        ax.fill_between(layers, f_arr, s_arr,
                        where=s_arr <= f_arr, color=COLORS["failure_think"], alpha=0.12)

        ax.set_xlabel("Layer index", fontsize=11)
        ax.set_ylabel("Mean refusal direction projection", fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, n_layers - 1)

    plt.tight_layout()
    path = out / "fig2_layer_discrimination.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Figure 3: Box plots — per-example phase mean at layer 22
# ---------------------------------------------------------------------------

def fig_boxplots(success: list[dict], failure: list[dict], out: Path) -> None:
    def phase_mean(ex: dict, phase: str) -> float | None:
        vals = proj_series(ex[f"_{phase}"], LAYER)
        return float(np.mean(vals)) if vals else None

    data: dict[str, list[float]] = {
        "S think": [v for ex in success if (v := phase_mean(ex, "think")) is not None],
        "F think": [v for ex in failure if (v := phase_mean(ex, "think")) is not None],
        "S final": [v for ex in success if (v := phase_mean(ex, "final")) is not None],
        "F final": [v for ex in failure if (v := phase_mean(ex, "final")) is not None],
    }

    fig, ax = plt.subplots(figsize=(8, 5))

    colors = [
        COLORS["success_think"], COLORS["failure_think"],
        COLORS["success_final"], COLORS["failure_final"],
    ]
    labels = [
        f"Success\nThink (n={len(data['S think'])})",
        f"Failure\nThink (n={len(data['F think'])})",
        f"Success\nFinal (n={len(data['S final'])})",
        f"Failure\nFinal (n={len(data['F final'])})",
    ]

    bps = ax.boxplot(
        list(data.values()),
        patch_artist=True,
        widths=0.55,
        medianprops=dict(color="black", linewidth=2),
    )
    for patch, color in zip(bps["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)

    # Overlay individual points with jitter
    for i, (vals, color) in enumerate(zip(data.values(), colors), start=1):
        jitter = np.random.default_rng(42).uniform(-0.18, 0.18, size=len(vals))
        ax.scatter(np.full(len(vals), i) + jitter, vals,
                   color=color, s=18, alpha=0.7, zorder=5)

    ax.set_xticks(range(1, 5))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel(f"Mean layer-{LAYER} refusal direction projection", fontsize=11)
    ax.set_title(
        f"Per-Example Mean Projection at Layer {LAYER} by Phase and Outcome\n"
        f"(StrongREJECT ≥ {SUCCESS_THR} = success)",
        fontsize=12,
    )
    ax.grid(True, axis="y", alpha=0.3)

    # Add significance markers
    for (x1, x2), color in [((1, 2), "#888888"), ((3, 4), "#888888")]:
        y_max = max(max(list(data.values())[x1-1]), max(list(data.values())[x2-1])) * 1.05
        ax.plot([x1, x1, x2, x2], [y_max*0.98, y_max, y_max, y_max*0.98], lw=1.2, color=color)

    plt.tight_layout()
    path = out / "fig3_boxplots_phase_mean.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Figure 4: Heatmaps (layer × token) for best success + best failure
# ---------------------------------------------------------------------------

def fig_heatmaps(success: list[dict], failure: list[dict], out: Path, n_layers: int = 40) -> None:
    # Pick example with highest SR score as canonical success,
    # example with 0.0 SR and longest think phase as canonical failure
    best_success = max(success, key=lambda e: e.get("strongreject_score", 0))
    best_failure = max(
        [ex for ex in failure if ex["_think"]],
        key=lambda e: len(e["_think"]),
    )

    MAX_TOKS = 600   # subsample for readability

    fig, axes = plt.subplots(2, 1, figsize=(14, 9))
    titles = [
        f"SUCCESS  (SR={best_success['strongreject_score']:.2f})  "
        f"{best_success['prompt_id'].replace('|', ' | ')}",
        f"FAILURE  (SR={best_failure['strongreject_score']:.2f})  "
        f"{best_failure['prompt_id'].replace('|', ' | ')}",
    ]

    for ax, ex, title in zip(axes, [best_success, best_failure], titles):
        toks = ex["token_level_data"]

        # Subsample evenly if needed
        if len(toks) > MAX_TOKS:
            idx = np.linspace(0, len(toks) - 1, MAX_TOKS, dtype=int)
            toks_sub = [toks[i] for i in idx]
        else:
            toks_sub = toks

        n_toks = len(toks_sub)
        mat = np.full((n_layers, n_toks), np.nan)
        for col, tok in enumerate(toks_sub):
            for li in range(n_layers):
                v = tok["layer_projections"].get(str(li))
                if v is not None:
                    mat[li, col] = v

        # Color limits: symmetric around median for visual clarity
        med = np.nanmedian(mat)
        span = np.nanpercentile(np.abs(mat - med), 95)
        vmin, vmax = med - span, med + span

        im = ax.imshow(mat, aspect="auto", origin="lower",
                       cmap="RdBu_r", vmin=vmin, vmax=vmax,
                       interpolation="nearest")
        plt.colorbar(im, ax=ax, label="Refusal direction projection", shrink=0.8)

        # Mark phase boundaries
        think_end = sum(1 for t in toks_sub if t["role_or_part"] in ("special", "think"))
        ax.axvline(think_end, color="black", linestyle="--", linewidth=1.5,
                   label="think→final boundary")

        # Mark layer 22
        ax.axhline(LAYER, color="yellow", linestyle="--", linewidth=1.2,
                   label=f"Layer {LAYER} (selected)")

        ax.set_xlabel(
            f"Token index ({'subsampled to ' + str(MAX_TOKS) if len(ex['token_level_data']) > MAX_TOKS else 'full sequence'})",
            fontsize=10,
        )
        ax.set_ylabel("Layer", fontsize=10)
        ax.set_title(title, fontsize=10, wrap=True)
        ax.legend(loc="upper right", fontsize=9)

    fig.suptitle(
        "Refusal Direction Projection Heatmap (Layer × Token)\n"
        "Canonical success vs. failure example",
        fontsize=12,
    )
    plt.tight_layout()
    path = out / "fig4_heatmaps.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Figure 5: Think-phase refusal score vs. final-phase refusal score (scatter)
# ---------------------------------------------------------------------------

def fig_scatter(examples: list[dict], out: Path) -> None:
    xs, ys, colors, labels = [], [], [], []
    for ex in examples:
        think_vals = proj_series(ex["_think"], LAYER)
        final_vals = proj_series(ex["_final"], LAYER)
        if not think_vals or not final_vals:
            continue
        xs.append(float(np.mean(think_vals)))
        ys.append(float(np.mean(final_vals)))
        colors.append(COLORS["success_think"] if ex["_success"] else COLORS["failure_think"])
        labels.append("success" if ex["_success"] else "failure")

    fig, ax = plt.subplots(figsize=(7, 6))
    for x, y, c, lbl in zip(xs, ys, colors, labels):
        ax.scatter(x, y, color=c, s=55, alpha=0.8, zorder=5)

    # Legend proxies
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["success_think"],
               markersize=10, label=f"Success (n={labels.count('success')})"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["failure_think"],
               markersize=10, label=f"Failure (n={labels.count('failure')})"),
    ]
    ax.legend(handles=legend_elements, fontsize=11)

    # Diagonal: think ≈ final
    lim = [min(xs + ys) - 0.3, max(xs + ys) + 0.3]
    ax.plot(lim, lim, "k--", alpha=0.3, lw=1, label="think = final")

    ax.set_xlabel(f"Mean layer-{LAYER} projection during THINK phase", fontsize=11)
    ax.set_ylabel(f"Mean layer-{LAYER} projection during FINAL phase", fontsize=11)
    ax.set_title(
        f"Think vs. Final Refusal Projection at Layer {LAYER}\n"
        "Each point = one attack example",
        fontsize=12,
    )
    ax.grid(True, alpha=0.3)

    # Compute simple correlation
    r = float(np.corrcoef(xs, ys)[0, 1])
    ax.text(0.05, 0.92, f"Pearson r = {r:.3f}", transform=ax.transAxes, fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

    plt.tight_layout()
    path = out / "fig5_scatter_think_vs_final.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Figure 6: Per-example SR score vs. layer-22 mean projection (think phase)
# ---------------------------------------------------------------------------

def fig_sr_vs_projection(examples: list[dict], out: Path) -> None:
    xs, ys = [], []
    for ex in examples:
        vals = proj_series(ex["_think"], LAYER)
        if not vals:
            continue
        xs.append(float(ex.get("strongreject_score", 0.0)))
        ys.append(float(np.mean(vals)))

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(xs, ys, s=55, alpha=0.8, color=[
        COLORS["success_think"] if x >= SUCCESS_THR else COLORS["failure_think"]
        for x in xs
    ], zorder=5)

    # Trend line
    z = np.polyfit(xs, ys, 1)
    p = np.poly1d(z)
    xline = np.linspace(min(xs), max(xs), 100)
    ax.plot(xline, p(xline), "k--", lw=1.5, alpha=0.5, label="Linear trend")
    ax.axvline(SUCCESS_THR, color="gray", linestyle=":", lw=1.5, label=f"Success threshold ({SUCCESS_THR})")

    r = float(np.corrcoef(xs, ys)[0, 1])
    ax.text(0.05, 0.92, f"Pearson r = {r:.3f}", transform=ax.transAxes, fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

    ax.set_xlabel("StrongREJECT score (0=safe, 1=violated)", fontsize=11)
    ax.set_ylabel(f"Mean layer-{LAYER} projection during THINK phase", fontsize=11)
    ax.set_title(
        f"Attack Severity vs. Refusal Signal (Layer {LAYER}, Think Phase)\n"
        "Higher SR score = more successful attack",
        fontsize=12,
    )
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = out / "fig6_sr_vs_think_projection.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Text summary
# ---------------------------------------------------------------------------

def print_summary(examples: list[dict]) -> None:
    success = [e for e in examples if e["_success"]]
    failure = [e for e in examples if not e["_success"]]

    print("\n=== Summary Statistics ===")
    print(f"Total examples:  {len(examples)}")
    print(f"Success (SR≥{SUCCESS_THR}): {len(success)}")
    print(f"Failure (SR<{SUCCESS_THR}): {len(failure)}")

    for phase in ["think", "final"]:
        print(f"\n  Layer {LAYER} — {phase.upper()} phase:")
        for group, name in [(success, "success"), (failure, "failure")]:
            vals = []
            for ex in group:
                vals.extend(proj_series(ex[f"_{phase}"], LAYER))
            if vals:
                print(f"    {name}: mean={np.mean(vals):.4f}  std={np.std(vals):.4f}  "
                      f"n_tokens={len(vals)}")

    # Per-example means
    print(f"\n  Per-example mean at layer {LAYER} — THINK phase:")
    s_means = [np.mean(proj_series(ex["_think"], LAYER))
               for ex in success if proj_series(ex["_think"], LAYER)]
    f_means = [np.mean(proj_series(ex["_think"], LAYER))
               for ex in failure if proj_series(ex["_think"], LAYER)]
    if s_means and f_means:
        print(f"    success: mean={np.mean(s_means):.4f}  std={np.std(s_means):.4f}")
        print(f"    failure: mean={np.mean(f_means):.4f}  std={np.std(f_means):.4f}")
        try:
            from scipy.stats import mannwhitneyu, ttest_ind
            u, p_mw = mannwhitneyu(s_means, f_means, alternative="two-sided")
            t, p_t = ttest_ind(s_means, f_means)
            print(f"    Mann-Whitney U={u:.1f}  p={p_mw:.4f}")
            print(f"    t-test t={t:.3f}  p={p_t:.4f}")
        except ImportError:
            pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUT_DIR}")

    print("Loading 42 per-example files...")
    examples = load_examples(BASE)
    print(f"  Loaded {len(examples)} examples")

    success = [e for e in examples if e["_success"]]
    failure = [e for e in examples if not e["_success"]]
    print(f"  Success: {len(success)}   Failure: {len(failure)}")

    print_summary(examples)

    print("\nGenerating figures...")
    fig_trajectory(success, failure, OUT_DIR)
    fig_layer_discrimination(success, failure, OUT_DIR)
    fig_boxplots(success, failure, OUT_DIR)
    fig_heatmaps(success, failure, OUT_DIR)
    fig_scatter(examples, OUT_DIR)
    fig_sr_vs_projection(examples, OUT_DIR)

    print(f"\nAll figures saved to {OUT_DIR}/")
    print("Files:")
    for f in sorted(OUT_DIR.glob("*.png")):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
