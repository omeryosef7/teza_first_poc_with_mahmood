"""Generic matplotlib plotting infrastructure for a research analysis pipeline.

Domain-agnostic array plotting helpers. Every public function takes an
``out_path``, saves a PNG (dpi=150, tight bbox) and returns the path.
Nothing is ever shown interactively (headless Agg backend).
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# Colorblind-friendly qualitative palette (Okabe-Ito).
_PALETTE: list[str] = [
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # bluish green
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
    "#000000",  # black
]


def _color(i: int) -> str:
    """Return a palette color, cycling if the index exceeds the palette length."""
    return _PALETTE[i % len(_PALETTE)]


def vline_annotate(
    ax: "matplotlib.axes.Axes",
    x: float,
    label: str = "",
    color: str = "#555555",
) -> "matplotlib.axes.Axes":
    """Draw a vertical dashed line at ``x`` with an optional text label.

    Useful for marking an onset/refusal layer on a trajectory plot.

    Args:
        ax: Axes to draw on.
        x: X position of the vertical line.
        label: Optional text label placed near the top of the line.
        color: Line/label color.

    Returns:
        The same Axes, for chaining.
    """
    ax.axvline(x=x, linestyle="--", linewidth=1.2, color=color, alpha=0.8, zorder=1)
    if label:
        ymin, ymax = ax.get_ylim()
        ax.text(
            x,
            ymax,
            f" {label}",
            color=color,
            va="top",
            ha="left",
            fontsize=8,
            rotation=90,
        )
    return ax


def layer_trajectory(
    layers: list[float],
    series: dict[str, list[float]],
    out_path: str,
    title: str = "",
    ylabel: str = "value",
    ci: dict[str, tuple[list, list]] | None = None,
) -> str:
    """Line plot of each named series versus layer.

    Args:
        layers: X-axis values (e.g. layer indices), shared by all series.
        series: Mapping of series name -> y-values (same length as ``layers``).
        out_path: Destination PNG path.
        title: Plot title.
        ylabel: Y-axis label.
        ci: Optional mapping of series name -> (lo, hi) arrays; when present a
            shaded confidence band is drawn between ``lo`` and ``hi``.

    Returns:
        ``out_path``.
    """
    x = np.asarray(layers, dtype=float)
    fig, ax = plt.subplots(figsize=(6.4, 4.0))

    for i, (name, ys) in enumerate(series.items()):
        color = _color(i)
        y = np.asarray(ys, dtype=float)
        ax.plot(x, y, label=name, color=color, linewidth=1.8, marker="o", markersize=3)
        if ci is not None and name in ci:
            lo, hi = ci[name]
            ax.fill_between(
                x,
                np.asarray(lo, dtype=float),
                np.asarray(hi, dtype=float),
                color=color,
                alpha=0.18,
                linewidth=0,
            )

    ax.set_xlabel("layer")
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(fontsize=8, framealpha=0.9)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def layer_metric_heatmap(
    matrix: list[list[float]],
    row_labels: list[str],
    col_labels: list[str],
    out_path: str,
    title: str = "",
    cbar_label: str = "",
) -> str:
    """Heatmap of a 2-D matrix with tick labels and a colorbar.

    Args:
        matrix: 2-D array-like of shape ``[rows, cols]``.
        row_labels: Labels for each row (y-axis).
        col_labels: Labels for each column (x-axis).
        out_path: Destination PNG path.
        title: Plot title.
        cbar_label: Label for the colorbar.

    Returns:
        ``out_path``.
    """
    m = np.asarray(matrix, dtype=float)
    n_rows, n_cols = m.shape

    fig, ax = plt.subplots(
        figsize=(max(4.0, 0.5 * n_cols + 2.0), max(3.0, 0.4 * n_rows + 1.5))
    )
    im = ax.imshow(m, aspect="auto", cmap="viridis")

    ax.set_xticks(np.arange(n_cols))
    ax.set_yticks(np.arange(n_rows))
    ax.set_xticklabels(col_labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(row_labels, fontsize=8)

    cbar = fig.colorbar(im, ax=ax)
    if cbar_label:
        cbar.set_label(cbar_label, fontsize=9)
    if title:
        ax.set_title(title)

    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def grouped_bars(
    categories: list[str],
    group_values: dict[str, list[float]],
    out_path: str,
    title: str = "",
    ylabel: str = "",
) -> str:
    """Grouped bar chart across categories.

    Args:
        categories: X-axis category labels.
        group_values: Mapping of group name -> per-category values (each list
            the same length as ``categories``).
        out_path: Destination PNG path.
        title: Plot title.
        ylabel: Y-axis label.

    Returns:
        ``out_path``.
    """
    n_cats = len(categories)
    n_groups = max(1, len(group_values))
    x = np.arange(n_cats, dtype=float)
    total_width = 0.8
    bar_width = total_width / n_groups

    fig, ax = plt.subplots(figsize=(max(6.4, 0.9 * n_cats + 1.5), 4.0))

    for i, (name, vals) in enumerate(group_values.items()):
        offset = (i - (n_groups - 1) / 2.0) * bar_width
        ax.bar(
            x + offset,
            np.asarray(vals, dtype=float),
            width=bar_width,
            label=name,
            color=_color(i),
            edgecolor="white",
            linewidth=0.5,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=8)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(True, axis="y", linestyle=":", alpha=0.5)
    ax.legend(fontsize=8, framealpha=0.9)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


if __name__ == "__main__":
    import os

    rng = np.random.default_rng(0)
    out_dir = "/tmp"

    # 1. layer_trajectory (with CI bands).
    layers = list(range(12))
    base_a = np.cumsum(rng.normal(0, 0.3, size=12))
    base_b = np.cumsum(rng.normal(0, 0.3, size=12))
    traj_series = {"series_a": base_a.tolist(), "series_b": base_b.tolist()}
    traj_ci = {
        "series_a": ((base_a - 0.5).tolist(), (base_a + 0.5).tolist()),
        "series_b": ((base_b - 0.4).tolist(), (base_b + 0.4).tolist()),
    }
    p1 = layer_trajectory(
        layers,
        traj_series,
        os.path.join(out_dir, "test_layer_trajectory.png"),
        title="Synthetic trajectory",
        ylabel="metric",
        ci=traj_ci,
    )
    print(f"{p1} PASS")

    # 2. layer_metric_heatmap.
    mat = rng.random((6, 8))
    p2 = layer_metric_heatmap(
        mat,
        row_labels=[f"row{i}" for i in range(6)],
        col_labels=[f"col{j}" for j in range(8)],
        out_path=os.path.join(out_dir, "test_layer_metric_heatmap.png"),
        title="Synthetic heatmap",
        cbar_label="score",
    )
    print(f"{p2} PASS")

    # 3. grouped_bars.
    cats = ["cat_a", "cat_b", "cat_c", "cat_d"]
    groups = {
        "g1": rng.random(4).tolist(),
        "g2": rng.random(4).tolist(),
        "g3": rng.random(4).tolist(),
    }
    p3 = grouped_bars(
        cats,
        groups,
        os.path.join(out_dir, "test_grouped_bars.png"),
        title="Synthetic grouped bars",
        ylabel="value",
    )
    print(f"{p3} PASS")

    # 4. vline_annotate (exercised on a fresh trajectory figure).
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.plot(layers, base_a, color=_color(0))
    vline_annotate(ax, x=5, label="onset")
    p4 = os.path.join(out_dir, "test_vline_annotate.png")
    fig.savefig(p4, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"{p4} PASS")
