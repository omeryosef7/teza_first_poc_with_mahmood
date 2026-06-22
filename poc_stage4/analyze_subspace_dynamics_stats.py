from __future__ import annotations

"""
Stage 4 — statistical analysis of subspace token dynamics.

Reads token_level_metrics.jsonl produced by analyze_token_dynamics_subspace.py
and computes per-example segment statistics, AUC per direction, and normalized
trajectory comparisons between complied (qwen_run_success=True) vs refused examples.

Designed to handle very large files (hundreds of millions of rows) via streaming:
never loads the full token_level_metrics.jsonl into memory; accumulates per-example
running statistics as it reads.

INPUTS:
  --token-dynamics-dir   Directory produced by analyze_token_dynamics_subspace.py
                         Must contain: token_level_metrics.jsonl, per_prompt_metrics.jsonl,
                         manifest.json
  --variant-name         Short label for this pipeline variant (behavioral | endofthink).
                         Used in plot titles and output filenames.
  --output-dir           Where to write all results.
  --n-bins               Number of bins for normalized-progress trajectory (default: 10).
  --focus-layers         Comma-separated layer indices to focus on (default: the K subspace
                         layers from manifest). "all" = all layers in the data.

OUTPUTS (in --output-dir):
  per_example_stats.csv        one row per (example × layer × rank × segment):
                                 columns: prompt_id, qwen_run_success, strongreject_score,
                                 layer, subspace_rank, segment, n_tokens,
                                 mean_proj, std_proj, final_proj, max_proj, min_proj
  auc_table.csv                AUC(mean_thinking_proj, qwen_run_success) for each (layer, rank)
  trajectory.csv               mean projection per (bin × layer × rank × group), thinking only
  summary.json                 top-line results: best AUC, group counts, layer/rank selection
  plots/auc_heatmap.png        AUC as a heat-map: rows=ranks, cols=layers
  plots/trajectory_rank{k}.png mean projection trajectory during thinking, complied vs refused
  plots/boxplot_thinking.png   box plots of mean thinking projection per rank (best layer)
  plots/segment_comparison.png thinking vs answer mean projection by group per rank
"""

import argparse
import collections
import json
import math
import pathlib
import sys
from typing import Any

SEGMENT_THINKING = "thinking"
SEGMENT_ANSWER = "answer"
SEGMENT_OTHER = "other"


# ---------------------------------------------------------------------------
# Row-level segment mapping
# ---------------------------------------------------------------------------

def _map_segment(role_or_part: str | None) -> str:
    if role_or_part is None:
        return SEGMENT_OTHER
    r = str(role_or_part).lower()
    if "think" in r:
        return SEGMENT_THINKING
    if r in ("answer", "response", "assistant"):
        return SEGMENT_ANSWER
    return SEGMENT_OTHER


# ---------------------------------------------------------------------------
# Streaming accumulation
# ---------------------------------------------------------------------------

class RunningStats:
    """Accumulate mean, variance (Welford), min, max, last value."""
    __slots__ = ("n", "mean", "_m2", "vmin", "vmax", "last")

    def __init__(self) -> None:
        self.n = 0
        self.mean = 0.0
        self._m2 = 0.0
        self.vmin = math.inf
        self.vmax = -math.inf
        self.last = float("nan")

    def update(self, x: float) -> None:
        if x is None or not math.isfinite(x):
            return
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        self._m2 += delta * (x - self.mean)
        if x < self.vmin:
            self.vmin = x
        if x > self.vmax:
            self.vmax = x
        self.last = x

    @property
    def std(self) -> float:
        if self.n < 2:
            return float("nan")
        return math.sqrt(self._m2 / (self.n - 1))

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_tokens": self.n,
            "mean_proj": round(self.mean, 6),
            "std_proj": round(self.std, 6),
            "final_proj": round(self.last, 6),
            "max_proj": round(self.vmax, 6) if math.isfinite(self.vmax) else None,
            "min_proj": round(self.vmin, 6) if math.isfinite(self.vmin) else None,
        }


def _read_manifest(dyn_dir: pathlib.Path) -> dict[str, Any]:
    p = dyn_dir / "manifest.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _subspace_layers_from_manifest(manifest: dict[str, Any]) -> list[int] | None:
    """Return the K subspace layers listed in the manifest, if available.
    Returns None when directions use layer=-1 (spans all layers — no layer filter)."""
    directions = manifest.get("subspace_directions", [])
    if not directions:
        return None
    layers = sorted({int(d["layer"]) for d in directions if "layer" in d})
    # layer == -1 means the direction is a global (all-layer) PCA direction
    if set(layers) == {-1}:
        return None
    return layers


def _load_per_prompt(dyn_dir: pathlib.Path) -> dict[str, dict[str, Any]]:
    """prompt_id → {qwen_run_success, strongreject_score, judge_score, generation_length}"""
    p = dyn_dir / "per_prompt_metrics.jsonl"
    out: dict[str, dict[str, Any]] = {}
    if not p.exists():
        return out
    with p.open() as fh:
        for line in fh:
            row = json.loads(line)
            pid = row.get("prompt_id") or row.get("example_id") or ""
            out[pid] = {
                "qwen_run_success": row.get("qwen_run_success"),
                "strongreject_score": row.get("strongreject_score"),
                "judge_score": row.get("judge_score"),
                "generation_token_count": row.get("generation_token_count"),
            }
    return out


def _stream_per_example_stats(
    per_example_dir: pathlib.Path,
    focus_layers: set[int] | None,
) -> list[dict[str, Any]]:
    """
    Stream per_example/*.json files produced by analyze_token_dynamics_subspace.py.

    Each file contains token_level_data: a list of per-token dicts with
    layer_projections[str(layer)] = [rank0_proj, rank1_proj, ...].

    For each (prompt_id, layer, subspace_rank, segment):
      accumulate RunningStats over projection values.

    Also tracks per-example thinking token positions for trajectory binning.

    Returns:
      (per_example_stats rows, thinking_series)
    """
    # Key: (prompt_id, layer, rank, segment) → RunningStats
    seg_stats: dict[tuple[str, int, int, str], RunningStats] = {}
    # Key: prompt_id → {(layer, rank) → list of (tok_idx_within_thinking, proj_val)}
    thinking_series: dict[str, dict[tuple[int, int], list[tuple[int, float]]]] = {}
    # Metadata from top-level of per_example JSON
    prompt_meta: dict[str, dict[str, Any]] = {}
    # Track thinking token counter per (prompt_id, layer, rank) — resets per file
    thinking_counter: dict[tuple[str, int, int], int] = {}

    for json_path in sorted(per_example_dir.glob("*.json")):
        try:
            artifact = json.loads(json_path.read_text())
        except Exception:
            continue

        pid = artifact.get("prompt_id", json_path.stem)
        if pid not in prompt_meta:
            prompt_meta[pid] = {
                "qwen_run_success": artifact.get("qwen_run_success"),
                "strongreject_score": artifact.get("strongreject_score"),
                "judge_score": artifact.get("judge_score"),
            }

        for tok_row in artifact.get("token_level_data", []):
            role = tok_row.get("role_or_part")
            segment = _map_segment(role)
            for layer_str, projections in tok_row.get("layer_projections", {}).items():
                layer = int(layer_str)
                if focus_layers is not None and layer not in focus_layers:
                    continue
                for rank, proj in enumerate(projections):
                    if proj is None or not math.isfinite(float(proj)):
                        continue
                    proj = float(proj)

                    key = (pid, layer, rank, segment)
                    if key not in seg_stats:
                        seg_stats[key] = RunningStats()
                    seg_stats[key].update(proj)

                    if segment == SEGMENT_THINKING:
                        tk = (pid, layer, rank)
                        if tk not in thinking_counter:
                            thinking_counter[tk] = 0
                        tok_idx = thinking_counter[tk]
                        thinking_counter[tk] += 1
                        thinking_series.setdefault(pid, {}).setdefault(
                            (layer, rank), []
                        ).append((tok_idx, proj))

    # Flatten into rows
    rows: list[dict[str, Any]] = []
    for (pid, layer, rank, segment), stats in seg_stats.items():
        meta = prompt_meta.get(pid, {})
        rows.append({
            "prompt_id": pid,
            "qwen_run_success": meta.get("qwen_run_success"),
            "strongreject_score": meta.get("strongreject_score"),
            "judge_score": meta.get("judge_score"),
            "layer": layer,
            "subspace_rank": rank,
            "segment": segment,
            **stats.to_dict(),
        })

    return rows, thinking_series


# ---------------------------------------------------------------------------
# AUC computation (no sklearn)
# ---------------------------------------------------------------------------

def _auc_mann_whitney(y_scores: list[float], y_labels: list[bool]) -> float:
    """Compute AUROC via Mann-Whitney U statistic."""
    pos = [s for s, l in zip(y_scores, y_labels) if l]
    neg = [s for s, l in zip(y_scores, y_labels) if not l]
    if not pos or not neg:
        return float("nan")
    n_pos, n_neg = len(pos), len(neg)
    u = sum(1.0 if p > n else (0.5 if p == n else 0.0) for p in pos for n in neg)
    return u / (n_pos * n_neg)


def _mann_whitney_p(y_scores: list[float], y_labels: list[bool]) -> float:
    """Approximate p-value for Mann-Whitney U (normal approximation, two-sided)."""
    try:
        from scipy.stats import mannwhitneyu
        pos = [s for s, l in zip(y_scores, y_labels) if l]
        neg = [s for s, l in zip(y_scores, y_labels) if not l]
        if not pos or not neg:
            return float("nan")
        _, p = mannwhitneyu(pos, neg, alternative="two-sided")
        return float(p)
    except ImportError:
        return float("nan")


def compute_auc_table(
    per_example_stats: list[dict[str, Any]],
    segment: str = SEGMENT_THINKING,
) -> list[dict[str, Any]]:
    """
    For each (layer, rank): AUC of mean_proj vs qwen_run_success.
    Rows with qwen_run_success=None are excluded.
    """
    # Group by (layer, rank) → list of (mean_proj, label)
    grouped: dict[tuple[int, int], list[tuple[float, bool]]] = collections.defaultdict(list)
    for row in per_example_stats:
        if row["segment"] != segment:
            continue
        label = row.get("qwen_run_success")
        if label is None:
            continue
        grouped[(row["layer"], row["subspace_rank"])].append(
            (row["mean_proj"], bool(label))
        )

    results = []
    for (layer, rank), pairs in sorted(grouped.items()):
        scores = [p[0] for p in pairs]
        labels = [p[1] for p in pairs]
        auc = _auc_mann_whitney(scores, labels)
        # Flip if < 0.5 (direction might be negated)
        auc_best = max(auc, 1 - auc) if not math.isnan(auc) else float("nan")
        p_val = _mann_whitney_p(scores, labels)
        n_pos = sum(labels)
        n_neg = len(labels) - n_pos
        results.append({
            "layer": layer,
            "subspace_rank": rank,
            "n_complied": n_pos,
            "n_refused": n_neg,
            "auc_raw": round(auc, 4),
            "auc": round(auc_best, 4),
            "p_value": round(p_val, 4) if not math.isnan(p_val) else None,
        })

    return sorted(results, key=lambda r: -r["auc"])


# ---------------------------------------------------------------------------
# Trajectory binning
# ---------------------------------------------------------------------------

def compute_trajectory(
    thinking_series: dict[str, dict[tuple[int, int], list[tuple[int, float]]]],
    per_prompt_meta: dict[str, dict[str, Any]],
    n_bins: int = 10,
    focus_layers: set[int] | None = None,
    focus_ranks: set[int] | None = None,
) -> list[dict[str, Any]]:
    """
    Bin each example's thinking projection series into n_bins position bins.
    Return mean per (bin, layer, rank, group).
    """
    # Accumulate: (bin, layer, rank, group) → RunningStats
    bin_stats: dict[tuple[int, int, int, str], RunningStats] = {}

    for pid, lr_map in thinking_series.items():
        meta = per_prompt_meta.get(pid, {})
        label = meta.get("qwen_run_success")
        group = "complied" if label is True else ("refused" if label is False else "unknown")

        for (layer, rank), series in lr_map.items():
            if focus_layers is not None and layer not in focus_layers:
                continue
            if focus_ranks is not None and rank not in focus_ranks:
                continue
            if not series:
                continue

            n = len(series)
            for tok_idx, proj in series:
                # bin index 0..n_bins-1
                bin_idx = min(int(tok_idx * n_bins / n), n_bins - 1)
                key = (bin_idx, layer, rank, group)
                if key not in bin_stats:
                    bin_stats[key] = RunningStats()
                bin_stats[key].update(proj)

    rows = []
    for (bin_idx, layer, rank, group), stats in sorted(bin_stats.items()):
        rows.append({
            "bin": bin_idx,
            "normalized_position": round((bin_idx + 0.5) / n_bins, 3),
            "layer": layer,
            "subspace_rank": rank,
            "group": group,
            "n_examples": stats.n,
            "mean_proj": round(stats.mean, 6),
            "std_proj": round(stats.std, 6),
        })
    return rows


# ---------------------------------------------------------------------------
# CSV writing (no pandas needed)
# ---------------------------------------------------------------------------

def _write_csv(path: pathlib.Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("")
        return
    keys = list(rows[0].keys())
    lines = [",".join(keys)]
    for row in rows:
        lines.append(",".join("" if v is None else str(v) for v in (row[k] for k in keys)))
    path.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def _plot_auc_heatmap(
    auc_table: list[dict[str, Any]],
    plots_dir: pathlib.Path,
    variant_name: str,
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return

    if not auc_table:
        return

    layers = sorted({r["layer"] for r in auc_table})
    ranks = sorted({r["subspace_rank"] for r in auc_table})
    data = np.full((len(ranks), len(layers)), float("nan"))
    for r in auc_table:
        ri = ranks.index(r["subspace_rank"])
        li = layers.index(r["layer"])
        data[ri, li] = r["auc"]

    fig, ax = plt.subplots(figsize=(max(8, len(layers) * 0.4), max(4, len(ranks) * 0.8)))
    im = ax.imshow(data, aspect="auto", vmin=0.5, vmax=1.0, cmap="RdBu_r")
    ax.set_xticks(range(len(layers)))
    ax.set_xticklabels(layers, fontsize=6, rotation=90)
    ax.set_yticks(range(len(ranks)))
    ax.set_yticklabels([f"rank {r}" for r in ranks], fontsize=8)
    ax.set_xlabel("Layer")
    ax.set_ylabel("Subspace rank")
    ax.set_title(f"AUC (mean thinking proj vs qwen_run_success)\nVariant: {variant_name}")
    fig.colorbar(im, ax=ax, label="AUC")
    fig.tight_layout()
    plots_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(plots_dir / "auc_heatmap.png", dpi=120)
    plt.close(fig)


def _plot_trajectory(
    trajectory: list[dict[str, Any]],
    plots_dir: pathlib.Path,
    variant_name: str,
    focus_layers: list[int],
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    if not trajectory:
        return

    ranks = sorted({r["subspace_rank"] for r in trajectory})
    colors = {"complied": "#0072B2", "refused": "#D55E00", "unknown": "gray"}

    for rank in ranks:
        fig, ax = plt.subplots(figsize=(10, 4))
        groups = sorted({r["group"] for r in trajectory if r["subspace_rank"] == rank})
        for layer in focus_layers:
            for group in groups:
                pts = sorted(
                    [r for r in trajectory
                     if r["subspace_rank"] == rank and r["layer"] == layer and r["group"] == group],
                    key=lambda r: r["bin"],
                )
                if not pts:
                    continue
                x = [p["normalized_position"] for p in pts]
                y = [p["mean_proj"] for p in pts]
                n = pts[0]["n_examples"] if pts else "?"
                ax.plot(
                    x, y,
                    label=f"L{layer} {group} (n≈{n})",
                    color=colors.get(group, "gray"),
                    linewidth=1.5,
                    linestyle="-" if group == "complied" else "--",
                )
        ax.axhline(0, color="black", linewidth=0.5, linestyle=":")
        ax.set_xlabel("Normalized thinking progress (0=start, 1=end)")
        ax.set_ylabel("Mean projection")
        ax.set_title(f"Subspace rank {rank} — thinking trajectory\nVariant: {variant_name}")
        ax.legend(fontsize=7, ncol=2)
        fig.tight_layout()
        plots_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(plots_dir / f"trajectory_rank{rank}.png", dpi=120)
        plt.close(fig)


def _plot_boxplot_thinking(
    per_example_stats: list[dict[str, Any]],
    best_layer: int,
    plots_dir: pathlib.Path,
    variant_name: str,
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    thinking_rows = [
        r for r in per_example_stats
        if r["segment"] == SEGMENT_THINKING
        and r["layer"] == best_layer
        and r.get("qwen_run_success") is not None
    ]
    if not thinking_rows:
        return

    ranks = sorted({r["subspace_rank"] for r in thinking_rows})
    fig, axes = plt.subplots(1, len(ranks), figsize=(4 * len(ranks), 5), squeeze=False)

    for col, rank in enumerate(ranks):
        ax = axes[0][col]
        rows_rank = [r for r in thinking_rows if r["subspace_rank"] == rank]
        complied = [r["mean_proj"] for r in rows_rank if r["qwen_run_success"] is True]
        refused = [r["mean_proj"] for r in rows_rank if r["qwen_run_success"] is False]
        bplot = ax.boxplot(
            [complied, refused],
            tick_labels=[f"complied\n(n={len(complied)})", f"refused\n(n={len(refused)})"],
            patch_artist=True,
        )
        box_colors = ["#0072B2", "#D55E00"]
        for box, color in zip(bplot["boxes"], box_colors):
            box.set_facecolor(color)
            box.set_alpha(0.5)
        ax.axhline(0, color="black", linewidth=0.5, linestyle=":")
        ax.set_title(f"rank {rank} (layer {best_layer})", fontsize=9)
        ax.set_ylabel("Mean thinking projection")

    fig.suptitle(f"Thinking projection by outcome — {variant_name}", fontsize=10)
    fig.tight_layout()
    plots_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(plots_dir / "boxplot_thinking.png", dpi=120)
    plt.close(fig)


def _plot_segment_comparison(
    per_example_stats: list[dict[str, Any]],
    best_layer: int,
    best_rank: int,
    plots_dir: pathlib.Path,
    variant_name: str,
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return

    segments = [SEGMENT_THINKING, SEGMENT_ANSWER]
    groups = ["complied", "refused"]
    colors = {"complied": "#0072B2", "refused": "#D55E00"}

    data: dict[tuple[str, str], list[float]] = {
        (seg, grp): [] for seg in segments for grp in groups
    }
    for row in per_example_stats:
        if row["layer"] != best_layer or row["subspace_rank"] != best_rank:
            continue
        if row["segment"] not in segments:
            continue
        label = row.get("qwen_run_success")
        if label is None:
            continue
        grp = "complied" if label else "refused"
        data[(row["segment"], grp)].append(row["mean_proj"])

    x = np.arange(len(segments))
    width = 0.3
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, grp in enumerate(groups):
        means = [
            (sum(data[(seg, grp)]) / len(data[(seg, grp)])) if data[(seg, grp)] else float("nan")
            for seg in segments
        ]
        stds = []
        for seg in segments:
            vals = data[(seg, grp)]
            if len(vals) > 1:
                m = sum(vals) / len(vals)
                stds.append(math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) / math.sqrt(len(vals)))
            else:
                stds.append(0.0)
        ax.bar(x + i * width, means, width, label=grp, color=colors[grp], alpha=0.7, yerr=stds, capsize=4)

    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(segments)
    ax.axhline(0, color="black", linewidth=0.5, linestyle=":")
    ax.set_ylabel("Mean projection (±SE)")
    ax.set_title(
        f"Thinking vs Answer projection — {variant_name}\n"
        f"Layer {best_layer}, rank {best_rank}"
    )
    ax.legend()
    fig.tight_layout()
    plots_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(plots_dir / "segment_comparison.png", dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Statistical analysis of subspace token dynamics output."
    )
    p.add_argument("--token-dynamics-dir", required=True,
                   help="Directory produced by analyze_token_dynamics_subspace.py")
    p.add_argument("--variant-name", default="unknown",
                   help="Short label (behavioral | endofthink) for plot titles")
    p.add_argument("--output-dir", required=True,
                   help="Where to write all analysis outputs")
    p.add_argument("--n-bins", type=int, default=10,
                   help="Bins for normalized-progress trajectory (default: 10)")
    p.add_argument("--focus-layers", default=None,
                   help='Comma-separated layer indices to analyse. '
                        'Default: subspace layers from manifest. "all" = all.')
    p.add_argument("--no-plots", action="store_true",
                   help="Skip generating plots (useful for quick runs)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    dyn_dir = pathlib.Path(args.token_dynamics_dir)
    out_dir = pathlib.Path(args.output_dir)
    plots_dir = out_dir / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    per_example_dir = dyn_dir / "per_example"
    if not per_example_dir.exists() or not any(per_example_dir.glob("*.json")):
        print(f"ERROR: no per_example/*.json found in {dyn_dir}", file=sys.stderr)
        sys.exit(1)

    manifest = _read_manifest(dyn_dir)
    per_prompt_meta = _load_per_prompt(dyn_dir)

    # Resolve focus_layers
    focus_layers: set[int] | None = None
    if args.focus_layers and args.focus_layers.strip().lower() != "all":
        focus_layers = {int(x.strip()) for x in args.focus_layers.split(",") if x.strip()}
    elif args.focus_layers is None:
        # Default: subspace layers from manifest
        subspace_layers = _subspace_layers_from_manifest(manifest)
        if subspace_layers:
            focus_layers = set(subspace_layers)

    n_files = len(list(per_example_dir.glob("*.json")))
    print(f"[analyze_subspace_stats] variant={args.variant_name}", flush=True)
    print(f"[analyze_subspace_stats] focus_layers={sorted(focus_layers) if focus_layers else 'all'}", flush=True)
    print(f"[analyze_subspace_stats] Streaming {n_files} per_example JSON files ...", flush=True)

    per_example_stats, thinking_series = _stream_per_example_stats(per_example_dir, focus_layers)

    n_examples = len({r["prompt_id"] for r in per_example_stats})
    print(f"[analyze_subspace_stats] {n_examples} examples, {len(per_example_stats)} stat rows", flush=True)

    # Write per_example_stats.csv
    _write_csv(out_dir / "per_example_stats.csv", per_example_stats)
    print(f"[analyze_subspace_stats] Wrote per_example_stats.csv ({len(per_example_stats)} rows)", flush=True)

    # AUC table
    auc_table = compute_auc_table(per_example_stats, segment=SEGMENT_THINKING)
    _write_csv(out_dir / "auc_table.csv", auc_table)
    if auc_table:
        best = auc_table[0]
        print(
            f"[analyze_subspace_stats] Best AUC: {best['auc']:.4f} "
            f"(layer={best['layer']}, rank={best['subspace_rank']}, p={best['p_value']})",
            flush=True,
        )

    # Trajectory
    focus_ranks: set[int] | None = None
    trajectory = compute_trajectory(
        thinking_series, per_prompt_meta,
        n_bins=args.n_bins,
        focus_layers=focus_layers,
        focus_ranks=focus_ranks,
    )
    _write_csv(out_dir / "trajectory.csv", trajectory)
    print(f"[analyze_subspace_stats] Wrote trajectory.csv ({len(trajectory)} rows)", flush=True)

    # Group counts
    labels = {r["prompt_id"]: r["qwen_run_success"]
              for r in per_example_stats if "qwen_run_success" in r}
    n_complied = sum(1 for v in labels.values() if v is True)
    n_refused = sum(1 for v in labels.values() if v is False)

    # Summary
    summary = {
        "variant_name": args.variant_name,
        "token_dynamics_dir": str(dyn_dir),
        "n_examples": n_examples,
        "n_complied": n_complied,
        "n_refused": n_refused,
        "focus_layers": sorted(focus_layers) if focus_layers else "all",
        "n_bins": args.n_bins,
        "auc_table_top5": auc_table[:5],
        "best_auc": auc_table[0] if auc_table else None,
        "manifest_subspace_k": manifest.get("subspace_k"),
        "manifest_subspace_directions": manifest.get("subspace_directions"),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"[analyze_subspace_stats] Wrote summary.json", flush=True)

    if not args.no_plots:
        best_layer = auc_table[0]["layer"] if auc_table else (
            sorted(focus_layers)[0] if focus_layers else 0
        )
        best_rank = auc_table[0]["subspace_rank"] if auc_table else 0
        focus_layer_list = sorted(focus_layers) if focus_layers else []

        print("[analyze_subspace_stats] Generating plots ...", flush=True)
        _plot_auc_heatmap(auc_table, plots_dir, args.variant_name)
        _plot_trajectory(trajectory, plots_dir, args.variant_name, focus_layer_list)
        _plot_boxplot_thinking(per_example_stats, best_layer, plots_dir, args.variant_name)
        _plot_segment_comparison(
            per_example_stats, best_layer, best_rank, plots_dir, args.variant_name
        )
        print(f"[analyze_subspace_stats] Plots written to {plots_dir}", flush=True)

    print("[analyze_subspace_stats] Done.", flush=True)


if __name__ == "__main__":
    main()
