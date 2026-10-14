#!/usr/bin/env python3
"""P6 DEV-set draw — the deterministic function frozen in configs/heretic_csi/PREREG_P6.json.

Applied AFTER Stage-0 covariates exist (installer strength needs the Stage-0 readout) and BEFORE any rescue run.
Inputs: Zipf per codeword (frozen now) and TRAIN installer strength (C−A, semantic_one_word, n4) per G1–G3 survivor.
  1. Frequency tertiles are FROZEN NOW over the 20 untouched codewords: sort by (zipf, word), split 7/7/6
     (low/mid/high) — independent of which codewords later survive.
  2. Installer strength: above/below the MEDIAN of the surviving untouched codewords (ties -> 'below').
  3. Cells = tertile x strength (6). rng = random.Random(20261013); cell order = rng.sample(sorted cells); take the
     first 5 cells; from each, draw one codeword uniformly (rng.choice over the cell's sorted members). An empty cell
     is skipped and the next cell in the order is used; if fewer than 5 cells are non-empty, the remaining slots
     are FILLED by rng.choice over the sorted not-yet-drawn survivors (same rng stream) — always exactly 5.
  4. DEV = ['candle'] + those 5. CONFIRMATION = remaining surviving untouched codewords.
basket/button are contaminated DEV points (never confirmation); envelope and carrot are excluded (see prereg).
"""
from __future__ import annotations
import random

SEED = 20261013
ZIPF = {"lamp": 4.05, "kettle": 3.54, "pencil": 3.95, "ladder": 4.03, "blanket": 4.07, "bucket": 4.07,
        "pillow": 3.96, "saddle": 3.73, "wagon": 3.9, "cushion": 3.58, "curtain": 3.86, "bottle": 4.57,
        "jacket": 4.32, "ribbon": 3.81, "sponge": 3.59, "whistle": 3.88, "yogurt": 3.63, "banana": 4.0,
        "chair": 4.69, "balloon": 3.9}


def tertiles(zipf=ZIPF):
    order = sorted(zipf, key=lambda w: (zipf[w], w))
    return {w: ("low" if i < 7 else "mid" if i < 14 else "high") for i, w in enumerate(order)}


def draw(install_strength: dict, survivors: list, seed: int = SEED):
    """install_strength: {codeword: TRAIN C-A}; survivors: G1–G3-surviving UNTOUCHED codewords."""
    surv = sorted(w for w in survivors if w in ZIPF)
    if len(surv) < 5:
        raise SystemExit(f"only {len(surv)} surviving untouched codewords — DEV draw impossible; see prereg")
    vals = sorted(install_strength[w] for w in surv)
    m = len(vals)
    med = vals[m // 2] if m % 2 else 0.5 * (vals[m // 2 - 1] + vals[m // 2])
    tert = tertiles()
    cells = {}
    for w in surv:
        cells.setdefault((tert[w], "above" if install_strength[w] > med else "below"), []).append(w)
    rng = random.Random(seed)
    all_cells = sorted((t, s) for t in ("low", "mid", "high") for s in ("above", "below"))
    order = rng.sample(all_cells, len(all_cells))
    dev = []
    for c in order:
        if len(dev) == 5:
            break
        members = sorted(cells.get(c, []))
        if members:
            dev.append(rng.choice(members))
    # FILL RULE (review #3 finding 8; PREREG_P6_AMENDMENT_1): if fewer than 5 cells were non-empty, fill the
    # remaining slots deterministically from the not-yet-drawn survivors with the SAME rng stream,
    # rng.choice over the sorted remainder, until 5 are drawn (always possible since len(surv) >= 5).
    n_fill = 0
    while len(dev) < 5:
        rest = sorted(w for w in surv if w not in dev)
        dev.append(rng.choice(rest)); n_fill += 1
    conf = [w for w in surv if w not in dev]
    return {"dev": ["candle"] + dev, "confirmation": conf, "median_strength": med,
            "n_fill": n_fill, "cells": {f"{k[0]}|{k[1]}": v for k, v in sorted(cells.items())}, "cell_order": [f"{a}|{b}" for a, b in order]}
