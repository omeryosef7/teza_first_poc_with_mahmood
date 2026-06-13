"""
PIL-based figure generation for the RL experiment.

No matplotlib dependency. Uses PIL.ImageDraw for all plots.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from poc_rl_loop.rl_l22_diagnostic import L22DiagnosticResult

def _ascii(s: str) -> str:
    return s.encode("latin-1", "replace").decode("latin-1")


_W, _H = 900, 500
_MARGIN = 60
_BG = (255, 255, 255)
_BLACK = (0, 0, 0)
_GREY = (180, 180, 180)
_PALETTE = {
    "cost_asr":         (70, 130, 180),   # steel blue
    "cost_mechanistic": (60, 179, 113),   # medium sea green
    "cost_l22_deflect": (205, 92, 92),    # indian red
}
_ACTION_COLORS = {"A": (70, 130, 180), "D": (60, 179, 113), "F": (205, 92, 92), "E": (255, 165, 0)}


def _draw_axes(draw: "ImageDraw.Draw", x0, y0, x1, y1, xlabel="", ylabel=""):
    draw.line([(x0, y0), (x0, y1)], fill=_BLACK, width=2)
    draw.line([(x0, y1), (x1, y1)], fill=_BLACK, width=2)
    if xlabel:
        draw.text(((x0 + x1) // 2, y1 + 20), _ascii(xlabel), fill=_BLACK)
    if ylabel:
        draw.text((5, (y0 + y1) // 2), _ascii(ylabel), fill=_BLACK)


def _smooth(vals: list[float], window: int = 20) -> list[float]:
    out = []
    for i in range(len(vals)):
        lo = max(0, i - window + 1)
        out.append(sum(vals[lo:i+1]) / (i - lo + 1))
    return out


def generate_reward_curve(
    traces_by_variant: dict[str, list[dict]],
    out_path: Path,
) -> None:
    """Smoothed cumulative-mean reward curve for all 3 variants on one plot."""
    if not _PIL_OK:
        return
    img = Image.new("RGB", (_W, _H), _BG)
    draw = ImageDraw.Draw(img)

    title = _ascii("RL Reward Curve (smoothed mean reward per episode)")
    draw.text((20, 12), title, fill=_BLACK)

    x0, y0, x1, y1 = _MARGIN, _MARGIN + 30, _W - 30, _H - 50
    _draw_axes(draw, x0, y0, x1, y1, xlabel="Episode", ylabel="Mean reward")

    # Determine y range
    all_vals = []
    smoothed_by_variant: dict[str, list[float]] = {}
    for var, trace in traces_by_variant.items():
        rewards = [r["reward_total"] for r in trace]
        cum_means = [sum(rewards[:i+1]) / (i+1) for i in range(len(rewards))]
        smoothed = _smooth(cum_means, window=20)
        smoothed_by_variant[var] = smoothed
        all_vals.extend(smoothed)

    if not all_vals:
        img.save(str(out_path))
        return

    y_min = min(all_vals) - 0.05
    y_max = max(all_vals) + 0.05
    y_range = y_max - y_min if y_max > y_min else 1.0

    # Draw zero line
    if y_min < 0 < y_max:
        zy = int(y1 - (0 - y_min) / y_range * (y1 - y0))
        draw.line([(x0, zy), (x1, zy)], fill=_GREY, width=1)

    # Plot each variant
    legend_y = y0
    for var, smoothed in smoothed_by_variant.items():
        color = _PALETTE.get(var, _BLACK)
        n = len(smoothed)
        if n < 2:
            continue
        pts = []
        for i, v in enumerate(smoothed):
            px = int(x0 + (i / (n - 1)) * (x1 - x0))
            py = int(y1 - (v - y_min) / y_range * (y1 - y0))
            pts.append((px, py))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=color, width=2)

        # Legend
        draw.rectangle([x1 - 140, legend_y, x1 - 120, legend_y + 10], fill=color)
        draw.text((x1 - 115, legend_y), var, fill=_BLACK)
        legend_y += 20

    # Y-axis ticks
    for v in [y_min, (y_min + y_max) / 2, y_max]:
        py = int(y1 - (v - y_min) / y_range * (y1 - y0))
        draw.line([(x0 - 4, py), (x0, py)], fill=_BLACK)
        draw.text((2, py - 6), f"{v:.2f}", fill=_BLACK)

    img.save(str(out_path))


def generate_policy_convergence(
    trace: list[dict],
    variant: str,
    out_path: Path,
) -> None:
    """P(A), P(D), P(F), P(E) over episodes for one variant."""
    if not _PIL_OK:
        return
    img = Image.new("RGB", (_W, _H), _BG)
    draw = ImageDraw.Draw(img)
    draw.text((20, 12), _ascii(f"Policy Convergence - {variant}"), fill=_BLACK)

    x0, y0, x1, y1 = _MARGIN, _MARGIN + 30, _W - 30, _H - 50
    _draw_axes(draw, x0, y0, x1, y1, xlabel="Episode", ylabel="P(condition)")

    n = len(trace)
    if n < 2:
        img.save(str(out_path))
        return

    legend_y = y0
    for action in ["A", "D", "F", "E"]:
        vals = [r[f"prob_{action}"] for r in trace]
        smoothed = _smooth(vals, window=20)
        color = _ACTION_COLORS[action]
        pts = []
        for i, v in enumerate(smoothed):
            px = int(x0 + (i / (n - 1)) * (x1 - x0))
            py = int(y1 - v * (y1 - y0))
            pts.append((px, py))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=color, width=2)
        draw.rectangle([x1 - 140, legend_y, x1 - 120, legend_y + 10], fill=color)
        draw.text((x1 - 115, legend_y), f"P({action})", fill=_BLACK)
        legend_y += 20

    # Y ticks
    for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
        py = int(y1 - v * (y1 - y0))
        draw.line([(x0 - 4, py), (x0, py)], fill=_BLACK)
        draw.text((2, py - 6), f"{v:.2f}", fill=_BLACK)

    img.save(str(out_path))


def generate_l22_diagnostic_bar(
    diagnostics_by_variant: dict[str, L22DiagnosticResult],
    out_path: Path,
) -> None:
    """Bar chart: mean L22 for success vs failure episodes, per variant."""
    if not _PIL_OK:
        return
    img = Image.new("RGB", (_W, _H), _BG)
    draw = ImageDraw.Draw(img)
    draw.text((20, 12), "L22 Projection: Success vs Failure Episodes (diagnostic)", fill=_BLACK)
    draw.text((20, 30), _ascii("(provisional harmful-vs-harmless contrast direction, Layer 22)"), fill=(100, 100, 100))

    x0, y0, x1, y1 = _MARGIN, _MARGIN + 50, _W - 30, _H - 60

    variants_with_data = {
        v: d for v, d in diagnostics_by_variant.items()
        if d.mean_l22_success is not None and d.mean_l22_failure is not None
    }
    if not variants_with_data:
        draw.text((200, 250), "No L22 data available for diagnostic.", fill=_BLACK)
        img.save(str(out_path))
        return

    all_vals = []
    for d in variants_with_data.values():
        all_vals.extend([d.mean_l22_success, d.mean_l22_failure])
    y_min = min(all_vals) - 0.5
    y_max = max(all_vals) + 0.5
    y_range = y_max - y_min

    n_groups = len(variants_with_data)
    group_w = (x1 - x0) // (n_groups + 1)
    bar_w = group_w // 4

    _draw_axes(draw, x0, y0, x1, y1)

    for gi, (var, diag) in enumerate(variants_with_data.items()):
        gx = x0 + (gi + 1) * group_w
        color = _PALETTE.get(var, _BLACK)

        for bi, (val, label) in enumerate([(diag.mean_l22_success, "success"), (diag.mean_l22_failure, "failure")]):
            bx = gx + bi * (bar_w + 4)
            bar_h = int((val - y_min) / y_range * (y1 - y0))
            fill = color if label == "success" else _lighten(color)
            draw.rectangle([bx, y1 - bar_h, bx + bar_w, y1], fill=fill, outline=_BLACK)
            draw.text((bx, y1 + 3), label[:3], fill=_BLACK)

        draw.text((gx - 10, y1 + 18), var[:14], fill=_BLACK)

    # Y ticks
    for v in [y_min, (y_min + y_max) / 2, y_max]:
        py = int(y1 - (v - y_min) / y_range * (y1 - y0))
        draw.line([(x0 - 4, py), (x0, py)], fill=_BLACK)
        draw.text((2, py - 6), f"{v:.1f}", fill=_BLACK)

    draw.text((x1 - 200, y0 + 5), "blue=success  grey=failure", fill=_BLACK)

    img.save(str(out_path))


def _lighten(color: tuple, factor: float = 0.5) -> tuple:
    return tuple(min(255, int(c + (255 - c) * factor)) for c in color)
