#!/usr/bin/env python3
"""
Phase 6 — Per-prompt trajectory analysis.

Generates four plots per example (full generation, early-think zoom,
late-think zoom, think-to-final transition) and per-example/per-layer
quantitative summaries.

Projection values are onto the *provisional harmful-versus-harmless contrast
direction* (diagnostic only, not causally validated).

Offline CPU-only.  Does not load model weights, does not require GPU or Slurm,
and does not modify any Stage 4 or Stage 6 artifacts.
"""

import argparse
import csv
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ─── Paths ───────────────────────────────────────────────────────────────────

BASE_DIR       = Path("outputs/stage4/token_dynamics/full_20260604_101929")
PER_EXAMPLE_DIR = BASE_DIR / "per_example"
ANALYSIS_DIR    = BASE_DIR / "analysis"
PLOT_DIR        = BASE_DIR / "plots_analysis_v2" / "per_prompt"
ANALYSIS_DATASET_PATH = ANALYSIS_DIR / "analysis_dataset.csv"

# ─── Constants ────────────────────────────────────────────────────────────────

SCRIPT_VERSION          = "per_prompt_trajectories_v1"
SELECTED_LAYERS_DEFAULT = [13, 16, 22, 26, 30, 38, 39]
PRIMARY_LAYER           = 22       # pre-specified from Stage 4A1
EXPLORATORY_LAYERS      = {38}     # post-hoc; largest g in one normalized-progress cell

# Wong (2011) colorblind-safe palette
LAYER_COLORS: dict[int, str] = {
    13: "#0072B2",   # blue
    16: "#56B4E9",   # sky blue
    22: "#009E73",   # bluish green — primary
    26: "#E69F00",   # orange
    30: "#D55E00",   # vermillion
    38: "#CC79A7",   # reddish purple — exploratory
    39: "#000000",   # black
}
FALLBACK_COLORS = ["#0072B2", "#56B4E9", "#009E73", "#E69F00",
                   "#D55E00", "#CC79A7", "#000000"]

THINK_BG   = "#E3F2FD"   # light blue
FINAL_BG   = "#FFF8E1"   # light amber
UNKNOWN_BG = "#F5F5F5"   # light grey for not-separable

SMOOTHING_THRESHOLD = 2000   # apply rolling mean when generation > this many tokens
TRANSITION_HALF     = 500    # tokens each side of </think>
EARLY_WINDOW        = 2000
LATE_WINDOW         = 2000

RANDOM_SEED = 42

# ─── Utilities ────────────────────────────────────────────────────────────────

def safe_id(example_id: str) -> str:
    return example_id.replace("=", "_").replace("|", "_").replace("/", "_")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def coerce_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes")


def coerce_int(val, default=None):
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return default


def coerce_float(val, default=None):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def rolling_mean(arr: np.ndarray, w: int) -> np.ndarray:
    if w <= 1 or len(arr) < w:
        return arr.copy()
    kernel = np.ones(w) / w
    return np.convolve(arr, kernel, mode="same")


def get_color(layer: int, selected: list) -> str:
    if layer in LAYER_COLORS:
        return LAYER_COLORS[layer]
    idx = selected.index(layer) if layer in selected else 0
    return FALLBACK_COLORS[idx % len(FALLBACK_COLORS)]


def layer_label(layer: int) -> str:
    tag = ""
    if layer == PRIMARY_LAYER:
        tag = " [primary]"
    elif layer in EXPLORATORY_LAYERS:
        tag = " [exploratory]"
    return f"L{layer}{tag}"


def get_line_style(layer: int) -> dict:
    return {
        "color": get_color(layer, SELECTED_LAYERS_DEFAULT),
        "lw":    2.5 if layer == PRIMARY_LAYER else 1.1,
        "ls":    "--" if layer == PRIMARY_LAYER else "-",
        "alpha": 0.90 if layer == PRIMARY_LAYER else 0.75,
    }

# ─── Data loading ─────────────────────────────────────────────────────────────

def load_analysis_dataset(path: Path) -> dict:
    """Return dict keyed by example_id with typed fields."""
    result = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            eid = row["example_id"]
            result[eid] = {
                "example_id":                   eid,
                "goal_index":                   coerce_int(row["goal_index"]),
                "attack_iteration":             coerce_int(row["attack_iteration"]),
                "conversation_id":              coerce_int(row["conversation_id"]),
                "target_model":                 row["target_model"],
                "strongreject_score":           coerce_float(row["strongreject_score"]),
                "sr_success":                   coerce_bool(row["sr_success"]),
                "judge_score":                  coerce_float(row["judge_score"]),
                "judge_success":                coerce_bool(row["judge_success"]),
                "prompt_token_count":           coerce_int(row["prompt_token_count"]),
                "generation_token_count":       coerce_int(row["generation_token_count"]),
                "think_token_count":            coerce_int(row["think_token_count"]),
                "final_token_count":            coerce_int(row["final_token_count"]),
                "generation_finish_reason":     row["generation_finish_reason"],
                "thinking_segmentation_status": row["thinking_segmentation_status"],
                "right_censored":               coerce_bool(row["right_censored"]),
                "usable_for_think_analysis":    coerce_bool(row["usable_for_think_analysis"]),
            }
    return result

# ─── Token helpers ─────────────────────────────────────────────────────────────

def extract_by_role(tld: list, roles: set, layer: int
                    ) -> tuple[np.ndarray, np.ndarray]:
    """Return (generated_token_indices, projections) for given roles and layer."""
    lk = str(layer)
    idx_list, prj_list = [], []
    for t in tld:
        if t["role_or_part"] in roles:
            v = t["layer_projections"].get(lk)
            if v is not None:
                idx_list.append(t["generated_token_index"])
                prj_list.append(v)
    return (np.asarray(idx_list, dtype=np.int32),
            np.asarray(prj_list, dtype=np.float64))


def find_transition_gen_idx(tld: list) -> int | None:
    """generated_token_index of the </think> special token, or None."""
    for t in tld:
        if t.get("token_text") == "</think>":
            return t["generated_token_index"]
    return None


def get_think_gidx_list(tld: list) -> list[int]:
    return [t["generated_token_index"] for t in tld if t["role_or_part"] == "think"]

# ─── Statistics ───────────────────────────────────────────────────────────────

def safe_mean(arr: np.ndarray, a: int = 0, b: int | None = None) -> float | None:
    sub = arr[a:b]
    return float(np.mean(sub)) if len(sub) > 0 else None


def safe_std(arr: np.ndarray) -> float | None:
    if len(arr) < 2:
        return None
    return float(np.std(arr, ddof=1))


def safe_slope(idx: np.ndarray, prj: np.ndarray) -> float | None:
    if len(idx) < 2:
        return None
    try:
        return float(np.polyfit(idx.astype(float), prj, 1)[0])
    except Exception:
        return None


def compute_layer_stats(tld: list, layer: int, seg_status: str) -> dict:
    """All required statistics for one layer × example."""
    separable = (seg_status == "parsed_from_think_tags")

    think_idx, think_prj = extract_by_role(tld, {"think"}, layer)
    final_idx, final_prj = extract_by_role(tld, {"final"}, layer)
    all_roles = {"think", "final", "assistant"}
    all_idx, all_prj = extract_by_role(tld, all_roles, layer)
    trans_gi = find_transition_gen_idx(tld)

    stats: dict = {
        "full_generation_mean":  safe_mean(all_prj),
        "full_generation_slope": safe_slope(all_idx, all_prj),
        "final_mean":            safe_mean(final_prj) if len(final_prj) > 0 else None,
    }

    if separable and len(think_prj) > 0:
        n = len(think_prj)
        stats.update({
            "think_mean":       float(np.mean(think_prj)),
            "think_std":        safe_std(think_prj),
            "early_500_mean":   safe_mean(think_prj, 0, min(500, n)),
            "early_1000_mean":  safe_mean(think_prj, 0, min(1000, n)),
            "early_2000_mean":  safe_mean(think_prj, 0, min(2000, n)),
            "late_2000_mean":   safe_mean(think_prj, max(0, n - 2000)),
            "late_1000_mean":   safe_mean(think_prj, max(0, n - 1000)),
            "late_500_mean":    safe_mean(think_prj, max(0, n - 500)),
        })
    else:
        for k in ("think_mean", "think_std", "early_500_mean", "early_1000_mean",
                  "early_2000_mean", "late_2000_mean", "late_1000_mean", "late_500_mean"):
            stats[k] = None

    if separable and trans_gi is not None:
        n_pre  = min(TRANSITION_HALF, len(think_prj))
        n_post = min(TRANSITION_HALF, len(final_prj))
        pre_m  = safe_mean(think_prj, len(think_prj) - n_pre) if n_pre > 0 else None
        post_m = safe_mean(final_prj, 0, n_post) if n_post > 0 else None
        stats["transition_pre500_mean"]  = pre_m
        stats["transition_post500_mean"] = post_m
        stats["transition_change"] = (
            post_m - pre_m if (pre_m is not None and post_m is not None) else None
        )
    else:
        stats["transition_pre500_mean"]  = None
        stats["transition_post500_mean"] = None
        stats["transition_change"]       = None

    return stats

# ─── Plot helpers ─────────────────────────────────────────────────────────────

def make_suptitle(meta: dict, extra: str = "") -> str:
    g   = meta.get("goal_index", "?")
    ai  = meta.get("attack_iteration", "?")
    ci  = meta.get("conversation_id", "?")
    sr  = meta.get("strongreject_score", "?")
    srs = "SUCCESS" if meta.get("sr_success") else "FAILURE"
    js  = meta.get("judge_score", "?")
    jss = "SUCCESS" if meta.get("judge_success") else "FAILURE"
    ntk = meta.get("think_token_count", "?")
    nfk = meta.get("final_token_count", "?")
    fin = meta.get("generation_finish_reason", "?")
    cen = "RIGHT-CENSORED" if meta.get("right_censored") else "complete"
    seg = meta.get("thinking_segmentation_status", "?")
    line1 = (f"Goal {g} | Iter {ai} | Conv {ci}  "
             f"SR={sr} ({srs})  Gemini={js} ({jss})")
    line2 = (f"Think={ntk} tok | Final={nfk} tok | "
             f"finish={fin} | {cen} | seg={seg}")
    return f"{line1}\n{line2}" + (f"\n{extra}" if extra else "")


def make_placeholder(msg: str, suptitle: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.text(0.5, 0.5, msg, ha="center", va="center", fontsize=12,
            transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.6", fc="#FFECB3", ec="#F9A825", lw=2))
    ax.set_axis_off()
    fig.suptitle(suptitle, fontsize=8, wrap=True)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def add_censored_annotation(ax) -> None:
    ax.text(0.99, 0.02, "RIGHT-CENSORED AT MAX_NEW_TOKENS",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8, color="darkred", style="italic")


def add_legend(ax, selected: list) -> None:
    handles, labels = ax.get_legend_handles_labels()
    # Put primary layer first
    order = []
    for i, lbl in enumerate(labels):
        if "[primary]" in lbl:
            order.insert(0, i)
        else:
            order.append(i)
    ax.legend([handles[i] for i in order],
              [labels[i] for i in order],
              fontsize=7, ncol=min(4, len(selected)), loc="best")

# ─── Plot A: full generation trajectory ───────────────────────────────────────

def plot_full(tld: list, meta: dict, selected: list, out: Path) -> None:
    seg       = meta.get("thinking_segmentation_status", "")
    separable = (seg == "parsed_from_think_tags")
    trans_gi  = find_transition_gen_idx(tld)

    # Choose smoothing window
    total_n = len(tld)
    smooth  = total_n > SMOOTHING_THRESHOLD
    w       = max(1, total_n // 500) if smooth else 1

    fig, ax = plt.subplots(figsize=(16, 5))
    x_max = 0

    for layer in selected:
        idx_a, prj_a = extract_by_role(tld, {"think", "final", "assistant"}, layer)
        if len(idx_a) == 0:
            continue
        x_max = max(x_max, int(idx_a[-1]))
        disp  = rolling_mean(prj_a, w) if smooth else prj_a
        ax.plot(idx_a, disp, label=layer_label(layer), **get_line_style(layer))

    # Phase shading
    if separable and trans_gi is not None:
        ax.axvspan(0, trans_gi, color=THINK_BG, alpha=0.35, zorder=0)
        ax.axvspan(trans_gi, x_max + 1, color=FINAL_BG, alpha=0.35, zorder=0)
        ax.axvline(x=trans_gi, color="#333333", ls=":", lw=1.5,
                   alpha=0.85, label="</think>")
    else:
        ax.axvspan(0, x_max + 1, color=UNKNOWN_BG, alpha=0.4, zorder=0)
        ax.text(0.5, 0.97,
                "THINK/FINAL SEGMENTATION UNAVAILABLE",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=11, color="darkred", fontweight="bold")

    if meta.get("right_censored"):
        add_censored_annotation(ax)

    smooth_note = f" — rolling mean w={w}" if smooth else ""
    ax.set_xlabel(f"Generated token index{smooth_note}")
    ax.set_ylabel("Projection (provisional direction)")
    ax.set_title("Full generation trajectory — all selected layers", fontsize=9)
    add_legend(ax, selected)

    extra = "THINK/FINAL SEGMENTATION UNAVAILABLE" if not separable else ""
    fig.suptitle(make_suptitle(meta, extra), fontsize=8.5, y=1.03)
    fig.tight_layout()
    fig.savefig(out, dpi=110, bbox_inches="tight")
    plt.close(fig)

# ─── Plot B: early think zoom ─────────────────────────────────────────────────

def plot_early(tld: list, meta: dict, selected: list, out: Path) -> None:
    seg       = meta.get("thinking_segmentation_status", "")
    separable = (seg == "parsed_from_think_tags")

    if not separable:
        make_placeholder(
            "THINK/FINAL SEGMENTATION UNAVAILABLE\n"
            "Early-think zoom not generated.",
            make_suptitle(meta), out)
        return

    think_gidx = get_think_gidx_list(tld)
    n_think    = len(think_gidx)
    actual_win = min(EARLY_WINDOW, n_think)

    # Marker positions (actual generated_token_index of 500th / 1000th think token)
    markers = {}
    for k in (500, 1000):
        if n_think >= k:
            markers[k] = think_gidx[k - 1]

    fig, ax = plt.subplots(figsize=(12, 4.5))

    for layer in selected:
        idx_t, prj_t = extract_by_role(tld, {"think"}, layer)
        if len(idx_t) == 0:
            continue
        end = min(actual_win, len(idx_t))
        ax.plot(idx_t[:end], prj_t[:end],
                label=layer_label(layer), **get_line_style(layer))

    for k, x_pos in markers.items():
        ax.axvline(x=x_pos, color="#777777", ls="--", lw=0.8, alpha=0.7)
        ax.text(x_pos, 1.0, f" {k}", transform=ax.get_xaxis_transform(),
                fontsize=7, color="#555555", va="bottom", rotation=90)

    ax.axvspan(0 if not think_gidx else think_gidx[0],
               (0 if not think_gidx else think_gidx[actual_win - 1]) + 1,
               color=THINK_BG, alpha=0.35, zorder=0)

    if meta.get("right_censored"):
        add_censored_annotation(ax)

    ax.set_xlabel("Generated token index (think phase)")
    ax.set_ylabel("Projection (provisional direction)")
    ax.set_title(
        f"Early think zoom — first {actual_win} of {n_think} thinking tokens "
        f"| dashed markers: 500-tok / 1000-tok Phase 2 window boundaries",
        fontsize=8.5)
    add_legend(ax, selected)
    fig.suptitle(make_suptitle(meta), fontsize=8.5, y=1.03)
    fig.tight_layout()
    fig.savefig(out, dpi=110, bbox_inches="tight")
    plt.close(fig)

# ─── Plot C: late think zoom ──────────────────────────────────────────────────

def plot_late(tld: list, meta: dict, selected: list, out: Path) -> None:
    seg       = meta.get("thinking_segmentation_status", "")
    separable = (seg == "parsed_from_think_tags")

    if not separable:
        make_placeholder(
            "THINK/FINAL SEGMENTATION UNAVAILABLE\n"
            "Late-think zoom not generated.",
            make_suptitle(meta), out)
        return

    think_gidx = get_think_gidx_list(tld)
    n_think    = len(think_gidx)
    actual_win = min(LATE_WINDOW, n_think)
    start_i    = max(0, n_think - actual_win)

    x_start = think_gidx[start_i] if think_gidx else 0
    x_end   = think_gidx[-1]      if think_gidx else 0

    fig, ax = plt.subplots(figsize=(12, 4.5))

    for layer in selected:
        idx_t, prj_t = extract_by_role(tld, {"think"}, layer)
        if len(idx_t) == 0:
            continue
        s = max(0, len(idx_t) - actual_win)
        ax.plot(idx_t[s:], prj_t[s:],
                label=layer_label(layer), **get_line_style(layer))

    ax.axvspan(x_start, x_end + 1, color=THINK_BG, alpha=0.35, zorder=0)

    if meta.get("right_censored"):
        add_censored_annotation(ax)

    ax.set_xlabel("Generated token index (think phase, absolute)")
    ax.set_ylabel("Projection (provisional direction)")
    ax.set_title(
        f"Late think zoom — last {actual_win} of {n_think} thinking tokens "
        f"(token index {x_start}–{x_end})",
        fontsize=8.5)
    add_legend(ax, selected)
    fig.suptitle(make_suptitle(meta), fontsize=8.5, y=1.03)
    fig.tight_layout()
    fig.savefig(out, dpi=110, bbox_inches="tight")
    plt.close(fig)

# ─── Plot D: think-to-final transition ───────────────────────────────────────

def plot_transition(tld: list, meta: dict, selected: list, out: Path) -> None:
    seg       = meta.get("thinking_segmentation_status", "")
    separable = (seg == "parsed_from_think_tags")
    trans_gi  = find_transition_gen_idx(tld)

    if not separable or trans_gi is None:
        make_placeholder(
            "THINK/FINAL SEGMENTATION UNAVAILABLE\n"
            "Transition plot not generated.",
            make_suptitle(meta), out)
        return

    fig, ax = plt.subplots(figsize=(12, 4.5))

    for layer in selected:
        idx_t, prj_t = extract_by_role(tld, {"think"}, layer)
        idx_f, prj_f = extract_by_role(tld, {"final"}, layer)
        n_pre  = min(TRANSITION_HALF, len(idx_t))
        n_post = min(TRANSITION_HALF, len(idx_f))
        seg_idx  = np.concatenate([idx_t[-n_pre:], idx_f[:n_post]])
        seg_prj  = np.concatenate([prj_t[-n_pre:], prj_f[:n_post]])
        if len(seg_idx) == 0:
            continue
        ax.plot(seg_idx, seg_prj, label=layer_label(layer), **get_line_style(layer))

    lo = trans_gi - TRANSITION_HALF
    hi = trans_gi + TRANSITION_HALF
    ax.axvspan(lo, trans_gi, color=THINK_BG, alpha=0.4, zorder=0)
    ax.axvspan(trans_gi, hi, color=FINAL_BG, alpha=0.4, zorder=0)
    ax.axvline(x=trans_gi, color="#333333", ls=":", lw=2.0, alpha=0.9, label="</think>")

    if meta.get("right_censored"):
        add_censored_annotation(ax)

    ax.set_xlabel("Generated token index (absolute)")
    ax.set_ylabel("Projection (provisional direction)")
    ax.set_title(
        f"Think-to-final transition — ±{TRANSITION_HALF} tokens around "
        f"</think> at index {trans_gi}",
        fontsize=8.5)
    add_legend(ax, selected)
    fig.suptitle(make_suptitle(meta), fontsize=8.5, y=1.03)
    fig.tight_layout()
    fig.savefig(out, dpi=110, bbox_inches="tight")
    plt.close(fig)

# ─── Canonical examples ───────────────────────────────────────────────────────

def _sort_key(r: dict) -> tuple:
    return (
        coerce_int(r.get("goal_index"), 99),
        coerce_int(r.get("attack_iteration"), 99),
        coerce_int(r.get("conversation_id"), 99),
    )


def identify_canonical(summary_rows: list) -> dict:
    def pick(candidates):
        """Tie-break only by (goal_index, attack_iteration, conversation_id)."""
        return min(candidates, key=_sort_key) if candidates else None

    def first_by(rows, primary_key_fn):
        """Sort rows by (primary_key_fn(r), _sort_key(r)); return first or None."""
        if not rows:
            return None
        return sorted(rows, key=lambda r: (primary_key_fn(r), _sort_key(r)))[0]

    success = [r for r in summary_rows if r["sr_success"]]
    failure = [r for r in summary_rows if not r["sr_success"]]

    # Among successes, find max sr score
    max_sr = max((float(r["strongreject_score"]) for r in success), default=None)
    top_sr = [r for r in success if float(r["strongreject_score"]) == max_sr] if max_sr is not None else []

    # Among failures, filter those with think analysis
    fail_think = [r for r in failure
                  if coerce_int(r.get("think_token_count"), 0) > 0]

    def entry(r, label, rule):
        if r is None:
            return {"example_id": None, "label": label, "rule": rule,
                    "note": "no matching example found"}
        return {
            "example_id":                   r["example_id"],
            "label":                        label,
            "rule":                         rule,
            "goal_index":                   r.get("goal_index"),
            "attack_iteration":             r.get("attack_iteration"),
            "conversation_id":              r.get("conversation_id"),
            "strongreject_score":           r.get("strongreject_score"),
            "sr_success":                   r.get("sr_success"),
            "judge_score":                  r.get("judge_score"),
            "judge_success":                r.get("judge_success"),
            "think_token_count":            r.get("think_token_count"),
            "generation_token_count":       r.get("generation_token_count"),
            "right_censored":               r.get("right_censored"),
            "thinking_segmentation_status": r.get("thinking_segmentation_status"),
        }

    # Primary sort key determines the intended ranking; _sort_key breaks ties.
    c1 = first_by(top_sr,    lambda r:  coerce_int(r.get("think_token_count"), 999999))
    c2 = first_by(top_sr,    lambda r: -coerce_int(r.get("think_token_count"), 0))
    c3 = first_by(fail_think, lambda r:  coerce_int(r.get("think_token_count"), 999999))
    c4 = first_by(failure,    lambda r: -coerce_int(r.get("think_token_count"), 0))
    c5 = pick([r for r in summary_rows if r.get("judge_success") and not r["sr_success"]])
    c6 = pick([r for r in summary_rows
               if r.get("right_censored") and
               r.get("thinking_segmentation_status") == "parsed_from_think_tags"])
    c7 = pick([r for r in summary_rows
               if r.get("thinking_segmentation_status") == "not_separable"])

    return {
        "tie_breaking_rule":
            "among ties: sort by (goal_index, attack_iteration, conversation_id) ascending",
        "random_seed": RANDOM_SEED,
        "examples": [
            entry(c1, "success_high_sr_short_think",
                  "max sr_score among successes; then min think_token_count"),
            entry(c2, "success_high_sr_long_think",
                  "max sr_score among successes; then max think_token_count"),
            entry(c3, "failure_shortest_think",
                  "min think_token_count among failures with valid think segmentation"),
            entry(c4, "failure_longest_think",
                  "max think_token_count among failures"),
            entry(c5, "evaluator_disagreement_gemini_pos_sr_neg",
                  "judge_success=True and sr_success=False"),
            entry(c6, "right_censored_parsed",
                  "right_censored=True and thinking_segmentation_status=parsed_from_think_tags"),
            entry(c7, "not_separable",
                  "thinking_segmentation_status=not_separable"),
        ],
    }

# ─── Plot index Markdown ──────────────────────────────────────────────────────

def write_plot_index(summary_rows: list, out: Path) -> None:
    def rel(p):
        try:
            return os.path.relpath(p, start=str(out.parent))
        except ValueError:
            return p

    goals = sorted({r["goal_index"] for r in summary_rows},
                   key=lambda x: coerce_int(x, 99))
    lines = [
        "# Per-Prompt Trajectory Plot Index\n\n",
        "Generated by `poc_stage4/plot_per_prompt_trajectories.py`.\n",
        "Projection is onto the *provisional harmful-versus-harmless contrast direction* "
        "(diagnostic only; not causally validated).\n\n",
        f"Selected layers: {SELECTED_LAYERS_DEFAULT}. "
        f"Layer {PRIMARY_LAYER} is the pre-specified primary layer. "
        f"Layer {sorted(EXPLORATORY_LAYERS)} marked exploratory.\n\n",
    ]
    for goal in goals:
        rows_g = sorted(
            [r for r in summary_rows if r["goal_index"] == goal],
            key=lambda r: (_sort_key(r)[1], _sort_key(r)[2])
        )
        lines.append(f"## Goal {goal}\n\n")
        lines.append(
            "| iter | conv | SR score | SR | Gemini | judge | "
            "gen tok | think tok | seg | cens | full | early | late | trans |\n"
        )
        lines.append(
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        )
        for r in rows_g:
            srs = "✓" if r.get("sr_success") else "✗"
            jss = "✓" if r.get("judge_success") else "✗"
            seg = r.get("thinking_segmentation_status", "?")
            seg_short = "parsed" if seg == "parsed_from_think_tags" else seg
            cen = "YES" if r.get("right_censored") else "no"
            lines.append(
                f"| {r.get('attack_iteration','?')} "
                f"| {r.get('conversation_id','?')} "
                f"| {r.get('strongreject_score','?')} "
                f"| {srs} "
                f"| {r.get('judge_score','?')} "
                f"| {jss} "
                f"| {r.get('generation_token_count','?')} "
                f"| {r.get('think_token_count','?')} "
                f"| {seg_short} "
                f"| {cen} "
                f"| [full]({rel(r['full_plot_path'])}) "
                f"| [early]({rel(r['early_plot_path'])}) "
                f"| [late]({rel(r['late_plot_path'])}) "
                f"| [trans]({rel(r['transition_plot_path'])}) |\n"
            )
        lines.append("\n")

    with open(out, "w") as f:
        f.writelines(lines)

# ─── Summary CSV writers ──────────────────────────────────────────────────────

_SUMMARY_FIELDS = [
    "example_id", "goal_index", "attack_iteration", "conversation_id",
    "strongreject_score", "sr_success", "judge_score", "judge_success",
    "prompt_token_count", "generation_token_count", "think_token_count",
    "final_token_count", "generation_finish_reason", "thinking_segmentation_status",
    "right_censored", "think_start_index", "think_end_index",
    "final_start_index", "final_end_index", "transition_boundary_index",
    "selected_layers", "full_plot_path", "early_plot_path",
    "late_plot_path", "transition_plot_path", "warnings",
]

_LAYER_FIELDS = [
    "example_id", "goal_index", "attack_iteration", "conversation_id", "layer",
    "think_mean", "think_std", "early_500_mean", "early_1000_mean", "early_2000_mean",
    "late_500_mean", "late_1000_mean", "late_2000_mean", "final_mean",
    "transition_pre500_mean", "transition_post500_mean", "transition_change",
    "full_generation_mean", "full_generation_slope",
]


def write_csv(rows: list, fields: list, path: Path) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

# ─── Main processing loop ─────────────────────────────────────────────────────

def process_all(selected: list) -> None:
    ensure_dir(ANALYSIS_DIR)
    ensure_dir(PLOT_DIR)

    dataset = load_analysis_dataset(ANALYSIS_DATASET_PATH)
    print(f"[p6] Loaded {len(dataset)} rows from analysis_dataset.csv")

    per_example_files = sorted(PER_EXAMPLE_DIR.glob("*.json"))
    print(f"[p6] Found {len(per_example_files)} per-example JSON files")
    print(f"[p6] Selected layers: {selected}")

    summary_rows     = []
    layer_stat_rows  = []
    reversal_notes   = []

    for json_path in per_example_files:
        with open(json_path) as f:
            data = json.load(f)

        prompt_id = data["prompt_id"]
        meta      = dataset.get(prompt_id)
        if meta is None:
            print(f"  WARNING: no dataset row for {prompt_id} — skipping")
            continue

        seg_status = data.get("thinking_segmentation_status", "unknown")
        tld        = data["token_level_data"]
        separable  = (seg_status == "parsed_from_think_tags")
        sid        = safe_id(prompt_id)

        # Token boundary indices
        think_tokens = [t for t in tld if t["role_or_part"] == "think"]
        final_tokens = [t for t in tld if t["role_or_part"] == "final"]
        trans_gi     = find_transition_gen_idx(tld)

        think_start = think_tokens[0]["generated_token_index"]  if think_tokens else None
        think_end   = think_tokens[-1]["generated_token_index"] if think_tokens else None
        final_start = final_tokens[0]["generated_token_index"]  if final_tokens else None
        final_end   = final_tokens[-1]["generated_token_index"] if final_tokens else None

        # Output paths
        full_p  = PLOT_DIR / f"{sid}__full.png"
        early_p = PLOT_DIR / f"{sid}__early_think.png"
        late_p  = PLOT_DIR / f"{sid}__late_think.png"
        trans_p = PLOT_DIR / f"{sid}__transition.png"

        print(f"  [p6] goal={meta['goal_index']} iter={meta['attack_iteration']} "
              f"conv={meta['conversation_id']}  seg={seg_status}  "
              f"N={len(tld)}", flush=True)

        # Generate four plots
        plot_full(tld, meta, selected, full_p)
        plot_early(tld, meta, selected, early_p)
        plot_late(tld, meta, selected, late_p)
        plot_transition(tld, meta, selected, trans_p)

        # Qualitative reversal check (layer 22 only, if separable)
        row_warn = []
        if seg_status == "not_separable":
            row_warn.append("not_separable: think/final stats null")

        if separable and len(think_tokens) >= 1 and len(final_tokens) >= 1:
            _, think_prj22 = extract_by_role(tld, {"think"}, 22)
            _, final_prj22 = extract_by_role(tld, {"final"}, 22)
            if len(think_prj22) > 0 and len(final_prj22) > 0:
                late_think_m = float(np.mean(think_prj22[-min(200, len(think_prj22)):]))
                early_final_m = float(np.mean(final_prj22[:min(200, len(final_prj22))]))
                if (late_think_m > 0) != (early_final_m > 0):
                    note = (f"L22 sign reversal at </think>: "
                            f"late_think={late_think_m:.3f}, early_final={early_final_m:.3f}")
                    row_warn.append(note)
                    reversal_notes.append(f"{prompt_id}: {note}")
                delta = early_final_m - late_think_m
                if abs(delta) > 2.0:
                    note = (f"L22 large drop at transition: "
                            f"Δ={delta:.3f}")
                    row_warn.append(note)

        # Per-layer statistics
        for layer in selected:
            stats = compute_layer_stats(tld, layer, seg_status)
            layer_stat_rows.append({
                "example_id":      prompt_id,
                "goal_index":      meta["goal_index"],
                "attack_iteration":meta["attack_iteration"],
                "conversation_id": meta["conversation_id"],
                "layer":           layer,
                **stats,
            })

        # Summary row
        summary_rows.append({
            "example_id":                   prompt_id,
            "goal_index":                   meta["goal_index"],
            "attack_iteration":             meta["attack_iteration"],
            "conversation_id":              meta["conversation_id"],
            "strongreject_score":           meta["strongreject_score"],
            "sr_success":                   meta["sr_success"],
            "judge_score":                  meta["judge_score"],
            "judge_success":                meta["judge_success"],
            "prompt_token_count":           meta["prompt_token_count"],
            "generation_token_count":       meta["generation_token_count"],
            "think_token_count":            meta["think_token_count"],
            "final_token_count":            meta["final_token_count"],
            "generation_finish_reason":     meta["generation_finish_reason"],
            "thinking_segmentation_status": seg_status,
            "right_censored":               meta["right_censored"],
            "think_start_index":            think_start,
            "think_end_index":              think_end,
            "final_start_index":            final_start,
            "final_end_index":              final_end,
            "transition_boundary_index":    trans_gi,
            "selected_layers":              str(selected),
            "full_plot_path":               str(full_p),
            "early_plot_path":              str(early_p),
            "late_plot_path":               str(late_p),
            "transition_plot_path":         str(trans_p),
            "warnings":                     "; ".join(row_warn),
        })

    # ── Write outputs ─────────────────────────────────────────────────────────

    summary_path    = ANALYSIS_DIR / "per_prompt_trajectory_summary.csv"
    layer_stat_path = ANALYSIS_DIR / "per_prompt_layer_summary.csv"
    canon_path      = ANALYSIS_DIR / "canonical_examples.json"
    index_path      = ANALYSIS_DIR / "per_prompt_plot_index.md"
    manifest_path   = ANALYSIS_DIR / "per_prompt_trajectory_manifest.json"

    write_csv(summary_rows, _SUMMARY_FIELDS, summary_path)
    print(f"\n[p6] {len(summary_rows)} rows → {summary_path}")

    write_csv(layer_stat_rows, _LAYER_FIELDS, layer_stat_path)
    print(f"[p6] {len(layer_stat_rows)} rows → {layer_stat_path}")

    canon = identify_canonical(summary_rows)
    with open(canon_path, "w") as f:
        json.dump(canon, f, indent=2, default=str)
    print(f"[p6] canonical examples → {canon_path}")

    write_plot_index(summary_rows, index_path)
    print(f"[p6] plot index → {index_path}")

    n_full  = sum(1 for r in summary_rows if Path(r["full_plot_path"]).exists())
    n_early = sum(1 for r in summary_rows if Path(r["early_plot_path"]).exists())
    n_late  = sum(1 for r in summary_rows if Path(r["late_plot_path"]).exists())
    n_trans = sum(1 for r in summary_rows if Path(r["transition_plot_path"]).exists())

    manifest = {
        "script_version":               SCRIPT_VERSION,
        "input_per_example_dir":        str(PER_EXAMPLE_DIR),
        "input_analysis_dataset":       str(ANALYSIS_DATASET_PATH),
        "output_plot_dir":              str(PLOT_DIR),
        "output_summary_csv":           str(summary_path),
        "output_layer_summary_csv":     str(layer_stat_path),
        "selected_layers":              selected,
        "primary_layer":                PRIMARY_LAYER,
        "exploratory_layers":           sorted(EXPLORATORY_LAYERS),
        "primary_outcome":              "sr_success = strongreject_score >= 0.5",
        "secondary_outcome":            "judge_success = judge_score == 10",
        "projection_direction_note":    "provisional harmful-versus-harmless contrast direction; "
                                        "diagnostic only; not causally validated",
        "n_examples_processed":         len(summary_rows),
        "n_full_plots":                 n_full,
        "n_early_plots":                n_early,
        "n_late_plots":                 n_late,
        "n_transition_plots":           n_trans,
        "smoothing_rule":               (
            f"Full trajectory: rolling mean window = max(1, N//500) "
            f"when N_generated_tokens > {SMOOTHING_THRESHOLD}. "
            "Zoom plots: no smoothing. "
            "Raw values stored in per-example JSONs."),
        "treatment_censored":           "included; annotated RIGHT-CENSORED AT MAX_NEW_TOKENS",
        "treatment_not_separable":      (
            "Full plot shows assistant-role tokens; "
            "zoom and transition plots are placeholder images with annotation"),
        "qualitative_reversal_notes":   reversal_notes,
        "python_version":               platform.python_version(),
        "numpy_version":                np.__version__,
        "matplotlib_version":           matplotlib.__version__,
        "created_utc":                  datetime.now(timezone.utc).isoformat(),
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[p6] manifest → {manifest_path}")

    # ── Validation ────────────────────────────────────────────────────────────

    print("\n[p6] ── VALIDATION ──────────────────────────────────────────────")
    n_dup = len(summary_rows) - len({r["example_id"] for r in summary_rows})
    not_sep_rows = [r for r in summary_rows
                    if r["thinking_segmentation_status"] == "not_separable"]
    cens_rows    = [r for r in summary_rows if r.get("right_censored")]

    ok = True
    def chk(label, cond, note=""):
        nonlocal ok
        status = "OK" if cond else "FAIL"
        if not cond:
            ok = False
        print(f"  [{status}] {label}" + (f" — {note}" if note else ""))

    chk("examples in summary = 42",   len(summary_rows) == 42,   f"got {len(summary_rows)}")
    chk("no duplicate example IDs",   n_dup == 0,                f"got {n_dup} duplicates")
    chk("full plots = 42",            n_full == 42,              f"got {n_full}")
    chk("early plots = 42",           n_early == 42,             f"got {n_early} (incl. placeholder)")
    chk("late plots = 42",            n_late == 42,              f"got {n_late} (incl. placeholder)")
    chk("transition plots = 42",      n_trans == 42,             f"got {n_trans} (incl. placeholder)")
    chk("not-separable examples = 1", len(not_sep_rows) == 1,    f"got {len(not_sep_rows)}")
    chk("right-censored examples = 2", len(cens_rows) == 2,      f"got {len(cens_rows)}")
    chk("not-separable has no think_start",
        all(r["think_start_index"] is None for r in not_sep_rows))
    chk("layer summary rows = 42×layers",
        len(layer_stat_rows) == 42 * len(selected),
        f"got {len(layer_stat_rows)}, expected {42*len(selected)}")

    if not_sep_rows:
        print(f"  Not-separable: {not_sep_rows[0]['example_id']}")
    for r in cens_rows:
        print(f"  Right-censored: {r['example_id']}")
    if reversal_notes:
        print(f"  L22 sign/large reversals at </think>: {len(reversal_notes)} examples")
        for n in reversal_notes:
            print(f"    {n}")
    else:
        print("  No L22 sign reversals at </think> detected.")

    print(f"\n[p6] Overall validation: {'PASSED' if ok else 'FAILED'}")
    return summary_rows, canon, reversal_notes


def main():
    ap = argparse.ArgumentParser(
        description="Phase 6: per-prompt trajectory analysis")
    ap.add_argument(
        "--layers", type=int, nargs="+", default=SELECTED_LAYERS_DEFAULT,
        help=f"Layers to plot (default: {SELECTED_LAYERS_DEFAULT})")
    args = ap.parse_args()
    selected = sorted(set(args.layers))
    process_all(selected)


if __name__ == "__main__":
    main()
