"""
Minimal PIL-based plotting utilities for environments without matplotlib.
Used to generate required figures when matplotlib is not available.
"""

from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional, Tuple


def _get_font(size=14):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_bar_chart(
    data: Dict[str, float],
    title: str,
    xlabel: str,
    ylabel: str,
    output_path: str,
    width: int = 700,
    height: int = 450,
    colors: Optional[Dict[str, Tuple]] = None,
    subtitle: str = "",
    y_max: Optional[float] = None,
):
    """Draw a simple bar chart with PIL and save to PNG."""
    IMG_W, IMG_H = width, height
    MARGIN_LEFT, MARGIN_RIGHT = 80, 30
    MARGIN_TOP, MARGIN_BOTTOM = 80, 80
    BAR_AREA_W = IMG_W - MARGIN_LEFT - MARGIN_RIGHT
    BAR_AREA_H = IMG_H - MARGIN_TOP - MARGIN_BOTTOM

    img = Image.new("RGB", (IMG_W, IMG_H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_title = _get_font(13)
    font_label = _get_font(11)
    font_tick = _get_font(10)

    default_colors = {
        "A": (76, 175, 80), "D": (33, 150, 243),
        "F": (255, 152, 0), "E": (156, 39, 176),
    }
    if colors is None:
        colors = {}

    keys = list(data.keys())
    vals = list(data.values())
    if not keys:
        return

    max_val = y_max if y_max is not None else (max(vals) * 1.25 if vals else 1.0)
    if max_val == 0:
        max_val = 1.0

    bar_w = BAR_AREA_W // len(keys)
    bar_padding = max(4, bar_w // 6)

    # Draw title
    draw.text((IMG_W // 2, 12), title, fill=(30, 30, 30), font=font_title, anchor="mt")
    if subtitle:
        draw.text((IMG_W // 2, 30), subtitle, fill=(100, 100, 100), font=_get_font(9), anchor="mt")

    # Draw axes
    ax_x0 = MARGIN_LEFT
    ax_y0 = MARGIN_TOP
    ax_x1 = IMG_W - MARGIN_RIGHT
    ax_y1 = IMG_H - MARGIN_BOTTOM
    draw.line([(ax_x0, ax_y1), (ax_x1, ax_y1)], fill=(80, 80, 80), width=2)
    draw.line([(ax_x0, ax_y0), (ax_x0, ax_y1)], fill=(80, 80, 80), width=2)

    # Y-axis ticks (5 ticks)
    for i in range(6):
        y_val = max_val * i / 5
        y_pix = ax_y1 - int(BAR_AREA_H * y_val / max_val)
        draw.line([(ax_x0 - 4, y_pix), (ax_x0, y_pix)], fill=(80, 80, 80), width=1)
        draw.text((ax_x0 - 6, y_pix), f"{y_val:.2f}", fill=(60, 60, 60),
                  font=font_tick, anchor="rm")

    # Bars
    for i, (key, val) in enumerate(zip(keys, vals)):
        x_center = ax_x0 + i * bar_w + bar_w // 2
        bar_h = int(BAR_AREA_H * val / max_val)
        x0 = x_center - bar_w // 2 + bar_padding
        x1 = x_center + bar_w // 2 - bar_padding
        y0 = ax_y1 - bar_h
        y1 = ax_y1

        # Color
        c = colors.get(key, default_colors.get(key, (100, 149, 237)))
        draw.rectangle([(x0, y0), (x1, y1)], fill=c, outline=(255, 255, 255), width=1)

        # Value label on top of bar
        draw.text((x_center, y0 - 2), f"{val:.3f}", fill=(30, 30, 30),
                  font=_get_font(9), anchor="mb")

        # X tick label
        draw.text((x_center, ax_y1 + 8), key, fill=(60, 60, 60),
                  font=font_tick, anchor="mt")

    # Axis labels
    draw.text((IMG_W // 2, IMG_H - 15), xlabel, fill=(60, 60, 60),
              font=font_label, anchor="mt")
    # Y-label (rotated text isn't easy with PIL; just write it vertically character by character)
    for j, ch in enumerate(ylabel):
        draw.text((10, MARGIN_TOP + BAR_AREA_H // 2 - len(ylabel) * 7 + j * 14),
                  ch, fill=(60, 60, 60), font=_get_font(10))

    img.save(output_path)


def draw_grouped_bar_chart(
    groups: Dict[str, Dict[str, float]],
    title: str,
    xlabel: str,
    ylabel: str,
    output_path: str,
    width: int = 900,
    height: int = 500,
    subtitle: str = "",
):
    """Draw grouped bar chart (groups of bars, each group is one main category)."""
    IMG_W, IMG_H = width, height
    MARGIN_LEFT, MARGIN_RIGHT = 90, 30
    MARGIN_TOP, MARGIN_BOTTOM = 90, 90
    BAR_AREA_W = IMG_W - MARGIN_LEFT - MARGIN_RIGHT
    BAR_AREA_H = IMG_H - MARGIN_TOP - MARGIN_BOTTOM

    img = Image.new("RGB", (IMG_W, IMG_H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = _get_font(12)
    font_label = _get_font(10)
    font_tick = _get_font(9)

    group_names = list(groups.keys())
    if not group_names:
        return
    sub_keys = list(next(iter(groups.values())).keys())

    all_vals = [v for g in groups.values() for v in g.values()]
    max_val = max(all_vals) * 1.3 if all_vals else 1.0

    group_w = BAR_AREA_W // len(group_names)
    bar_w = (group_w - 10) // len(sub_keys)
    bar_pad = max(2, bar_w // 8)

    palette = [
        (76, 175, 80), (33, 150, 243), (255, 152, 0), (156, 39, 176),
        (244, 67, 54), (0, 188, 212), (139, 195, 74), (255, 87, 34),
    ]

    ax_x0 = MARGIN_LEFT
    ax_y0 = MARGIN_TOP
    ax_x1 = IMG_W - MARGIN_RIGHT
    ax_y1 = IMG_H - MARGIN_BOTTOM

    # Title
    draw.text((10, 10), title, fill=(30, 30, 30), font=font_title)
    if subtitle:
        draw.text((IMG_W // 2, 28), subtitle, fill=(100, 100, 100),
                  font=_get_font(9), anchor="mt")

    # Axes
    draw.line([(ax_x0, ax_y1), (ax_x1, ax_y1)], fill=(80, 80, 80), width=2)
    draw.line([(ax_x0, ax_y0), (ax_x0, ax_y1)], fill=(80, 80, 80), width=2)

    # Y ticks
    for i in range(6):
        y_val = max_val * i / 5
        y_pix = ax_y1 - int(BAR_AREA_H * y_val / max_val)
        draw.line([(ax_x0 - 4, y_pix), (ax_x0, y_pix)], fill=(80, 80, 80), width=1)
        draw.text((ax_x0 - 6, y_pix), f"{y_val:.2f}", fill=(60, 60, 60),
                  font=font_tick, anchor="rm")

    # Bars
    for gi, (grp_name, sub_data) in enumerate(groups.items()):
        grp_x0 = ax_x0 + gi * group_w + 5
        grp_cx = ax_x0 + gi * group_w + group_w // 2
        draw.text((grp_cx, ax_y1 + 8), grp_name, fill=(60, 60, 60),
                  font=font_tick, anchor="mt")

        for si, sub_key in enumerate(sub_keys):
            val = sub_data.get(sub_key, 0.0)
            c = palette[si % len(palette)]
            bx0 = grp_x0 + si * bar_w + bar_pad
            bx1 = grp_x0 + (si + 1) * bar_w - bar_pad
            bar_h = int(BAR_AREA_H * val / max_val) if max_val > 0 else 0
            by0 = ax_y1 - bar_h
            by1 = ax_y1
            draw.rectangle([(bx0, by0), (bx1, by1)], fill=c, outline=(255, 255, 255), width=1)

    # Legend
    leg_x = ax_x0
    leg_y = IMG_H - MARGIN_BOTTOM + 35
    for si, sub_key in enumerate(sub_keys):
        c = palette[si % len(palette)]
        draw.rectangle([(leg_x, leg_y), (leg_x + 14, leg_y + 12)], fill=c)
        draw.text((leg_x + 18, leg_y), sub_key, fill=(50, 50, 50), font=font_tick)
        leg_x += 100

    # Axis labels
    draw.text((IMG_W // 2, IMG_H - 8), xlabel, fill=(60, 60, 60), font=font_label, anchor="mt")

    img.save(output_path)


def draw_heatmap(
    matrix: List[List[float]],
    row_labels: List[str],
    col_labels: List[str],
    title: str,
    output_path: str,
    width: int = 800,
    height: int = 600,
    colormap: str = "blues",
    annotation_format: str = ".2f",
):
    """Draw a simple heatmap with PIL."""
    IMG_W, IMG_H = width, height
    MARGIN_LEFT, MARGIN_RIGHT = 120, 30
    MARGIN_TOP, MARGIN_BOTTOM = 80, 120
    CELL_W = (IMG_W - MARGIN_LEFT - MARGIN_RIGHT) // max(len(col_labels), 1)
    CELL_H = (IMG_H - MARGIN_TOP - MARGIN_BOTTOM) // max(len(row_labels), 1)

    all_vals = [v for row in matrix for v in row if v is not None]
    v_min = min(all_vals) if all_vals else 0.0
    v_max = max(all_vals) if all_vals else 1.0
    v_range = v_max - v_min if v_max != v_min else 1.0

    img = Image.new("RGB", (IMG_W, IMG_H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = _get_font(12)
    font_cell = _get_font(9)
    font_label = _get_font(10)
    font_axis = _get_font(9)

    def val_to_color(val):
        t = (val - v_min) / v_range
        if colormap == "blues":
            r = int(220 - t * 180)
            g = int(230 - t * 160)
            b = int(255)
        elif colormap == "reds":
            r = 255
            g = int(220 - t * 180)
            b = int(220 - t * 200)
        else:
            v = int(255 - t * 200)
            r, g, b = v, v, 255
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    def text_color_for_bg(bg):
        lum = 0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]
        return (0, 0, 0) if lum > 128 else (255, 255, 255)

    draw.text((10, 10), title, fill=(30, 30, 30), font=font_title)

    for ri, row_vals in enumerate(matrix):
        for ci, val in enumerate(row_vals):
            if val is None:
                continue
            cx0 = MARGIN_LEFT + ci * CELL_W
            cy0 = MARGIN_TOP + ri * CELL_H
            cx1 = cx0 + CELL_W
            cy1 = cy0 + CELL_H
            bg = val_to_color(val)
            draw.rectangle([(cx0, cy0), (cx1, cy1)], fill=bg, outline=(200, 200, 200), width=1)
            txt = format(val, annotation_format)
            tc = text_color_for_bg(bg)
            draw.text(((cx0 + cx1) // 2, (cy0 + cy1) // 2), txt, fill=tc,
                      font=font_cell, anchor="mm")

    # Column labels (rotated chars)
    for ci, col_lbl in enumerate(col_labels):
        cx = MARGIN_LEFT + ci * CELL_W + CELL_W // 2
        for j, ch in enumerate(col_lbl):
            draw.text((cx, MARGIN_TOP - 8 - (len(col_lbl) - 1 - j) * 9), ch,
                      fill=(50, 50, 50), font=_get_font(8), anchor="mm")

    # Row labels
    for ri, row_lbl in enumerate(row_labels):
        cy = MARGIN_TOP + ri * CELL_H + CELL_H // 2
        draw.text((MARGIN_LEFT - 6, cy), row_lbl, fill=(50, 50, 50),
                  font=font_axis, anchor="rm")

    img.save(output_path)
