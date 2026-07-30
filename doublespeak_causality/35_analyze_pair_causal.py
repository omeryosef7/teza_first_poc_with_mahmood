"""
35_analyze_pair_causal.py — CAUSAL_CORE_PLAN §4.5, §5, §7, §14 (S5-S7, S9, S10). CPU-only.

Turn intervention raw rows into the plan's required statistics:

  * paired causal effect per arm, vs the per-prompt IDENTITY baseline
        effect = p_concept(arm) - p_concept(identity)
    with paired-bootstrap CIs (stats.paired_bootstrap_ci, house constants).

  * the CONTROL DISTRIBUTION (§5), not a single control seed: every `rand_*` arm is
    pooled into a distribution and the concept-specific arm is reported as a percentile
    and a z-score within it. A concept-specific effect only counts if it exceeds the
    matched-perturbation distribution.

  * the dose-response / reversibility check (§4.5): effect vs signed alpha per layer,
    with monotonicity (Spearman) and the plan's causal quantity
        J_causal = P(target | do(+d)) - P(target | do(-d)).

  * MULTIPLE-COMPARISON CORRECTION over the layer x alpha grid (§14) via
    stats.holm_bonferroni on paired permutation p-values. The prior sprint reported
    per-window CIs with no correction; this wires it in deliberately.

  * the causal ATTACK WINDOW (§16.11): the contiguous layer band whose corrected effect
    is significant, reported against the canonical early/mid/late definition.

Usage:
  python 35_analyze_pair_causal.py --interv-dir outputs/pair_interv_layer_scan_... \
      [--interv-dir ...] --out outputs/pair_causal_analysis.json
"""
import os
import sys
import json
import math
import argparse
import importlib.util
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))
N_BOOT, SEED = 10000, 0
METRIC = "p_concept"


def _load_numeric(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


layer_windows = _load_numeric("beh_necessity", "18_run_behavioral_necessity.py").layer_windows


def _ci(x, y):
    """House CI wrapper (same shape analyze_behavioral_causality.py emits)."""
    d = st.paired_bootstrap_ci(x, y, n_boot=N_BOOT, seed=SEED)
    return {"mean": round(d["mean_diff"], 5), "lo": round(d["lo"], 5),
            "hi": round(d["hi"], 5), "n": d["n"],
            "ci_reliable": d["ci_reliable"], "degenerate": d["degenerate"]}


def spearman(x, y):
    """Rank correlation without scipy (stats.py is deliberately scipy-free)."""
    if len(x) < 3:
        return float("nan")
    rx, ry = st._average_ranks(np.asarray(x, float)), st._average_ranks(np.asarray(y, float))
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    den = math.sqrt(float((rx ** 2).sum()) * float((ry ** 2).sum()))
    return float("nan") if den == 0 else float((rx * ry).sum() / den)


def load_rows(dirs):
    rows = []
    for d in dirs:
        p = os.path.join(d, "interv_raw.jsonl")
        if not os.path.exists(p):
            print(f"[analyze] WARNING no interv_raw.jsonl in {d}")
            continue
        for line in open(p):
            r = json.loads(line)
            r["_dir"] = os.path.basename(d.rstrip("/"))
            rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interv-dir", action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--metric", default=METRIC)
    ap.add_argument("--alpha-level", type=float, default=0.05)
    args = ap.parse_args()

    rows = load_rows(args.interv_dir)
    if not rows:
        raise SystemExit("no rows")
    metric = args.metric

    # identity baseline per (dir, sid, site) — deterministic ordering everywhere
    base = {}
    for r in rows:
        if r["arm"] == "identity":
            base[(r["_dir"], r["sid"], r.get("site"))] = r[metric]

    def paired(sel):
        """Return (arm_values, identity_values) paired on prompt, sorted for determinism."""
        xs, ys, keys = [], [], []
        for r in rows:
            if r["arm"] == "identity" or not sel(r):
                continue
            b = base.get((r["_dir"], r["sid"], r.get("site")))
            if b is None or r[metric] is None:
                continue
            keys.append((r["_dir"], r["sid"], str(r.get("site")), str(r.get("layer")),
                         str(r.get("alpha")), str(r.get("group"))))
            xs.append(r[metric])
            ys.append(b)
        order = sorted(range(len(keys)), key=lambda i: keys[i])
        return [xs[i] for i in order], [ys[i] for i in order]

    # ------------------------------------------------------------------ #
    # 1. per-arm effect at each (layer|group, alpha, site)
    # ------------------------------------------------------------------ #
    cells = defaultdict(list)
    for r in rows:
        if r["arm"] == "identity":
            continue
        cells[(r["arm"], str(r.get("layer")), str(r.get("group")),
               str(r.get("alpha")), str(r.get("site")))].append(r)

    per_cell = {}
    for key, rs in sorted(cells.items()):
        arm, layer, group, alpha, site = key
        x, y = paired(lambda r, k=key: (r["arm"], str(r.get("layer")),
                                        str(r.get("group")), str(r.get("alpha")),
                                        str(r.get("site"))) == k)
        if len(x) < 2:
            continue
        ci = _ci(x, y)
        perm = st.permutation_test_paired(x, y, n_perm=2000, seed=SEED)
        per_cell["|".join(key)] = {
            "arm": arm, "layer": layer, "group": group, "alpha": alpha, "site": site,
            "n": ci["n"], "effect": ci["mean"], "lo": ci["lo"], "hi": ci["hi"],
            "ci_reliable": ci["ci_reliable"], "degenerate": ci["degenerate"],
            "p_raw": round(perm["p"], 6),
            "mean_arm": round(float(np.mean(x)), 5),
            "mean_identity": round(float(np.mean(y)), 5),
        }

    # ------------------------------------------------------------------ #
    # 2. multiple-comparison correction (§14)
    # ------------------------------------------------------------------ #
    # Holm is applied over the FULL JOINT family of non-random concept cells — every
    # (arm × site × window/layer × alpha) tested in this run, pooled — NOT per-arm. This is
    # the STRICTER choice (larger m ⇒ harsher threshold): it can only suppress a genuine
    # effect, never manufacture a false one, so a cell that clears it (e.g. d_Direct) is
    # significant under an even more conservative bar than the plan's per-arm grid. Stated
    # explicitly here because the docstring above (§14) describes the per-arm grid.
    concept_keys = [k for k, v in per_cell.items() if not v["arm"].startswith("rand_")]
    if concept_keys:
        adj = st.holm_bonferroni([per_cell[k]["p_raw"] for k in sorted(concept_keys)])
        for k, pa in zip(sorted(concept_keys), adj):
            per_cell[k]["p_holm"] = round(float(pa), 6)
            per_cell[k]["significant_corrected"] = bool(pa < args.alpha_level)

    # ------------------------------------------------------------------ #
    # 3. control DISTRIBUTION per (layer, GROUP, alpha, site) — plan §5
    # ------------------------------------------------------------------ #
    # The bucket key MUST include `group`. In window mode every arm has layer=None and the
    # window is carried in `group` (early/mid/late), so keying on (layer, alpha, site) alone
    # collapses all three windows into one bucket: their random controls get pooled (n=180
    # instead of ~60 per window) and, worse, concept_arms is keyed by arm-name so the three
    # windows of each concept arm overwrite each other and only ONE window (the last) is ever
    # compared to controls — the strongest (late) d_Direct effect was never checked against a
    # control distribution. Including `group` compares each window's concept arm only against
    # controls injected over the SAME window. (Bug found in the 2026-07-30 adversarial review;
    # per_cell CIs and the top-line dissociation were already correct.)
    control_dist = {}
    for (layer, group, alpha, site) in sorted(
            {(v["layer"], v["group"], v["alpha"], v["site"]) for v in per_cell.values()}):
        ctrl = [v["effect"] for v in per_cell.values()
                if v["arm"].startswith("rand_") and v["layer"] == layer
                and v["group"] == group and v["alpha"] == alpha and v["site"] == site]
        if len(ctrl) < 3:
            continue
        arr = np.asarray(ctrl, float)
        sd = float(arr.std(ddof=1))
        # A control distribution with (near) zero spread makes z meaningless: dividing by
        # sd+1e-9 produced z values of ~1e7 in the first layer scan, which look decisive
        # and mean nothing. Report z only when the control distribution actually has
        # spread AND enough draws; otherwise report None and rely on the percentile /
        # exceeds-all comparison. Plan §5 wants the DISTRIBUTION, not a spurious z.
        sd_usable = sd > 1e-6 and len(ctrl) >= 8
        entry = {"n_controls": len(ctrl), "sd_usable_for_z": sd_usable,
                 "mean": round(float(arr.mean()), 5), "sd": round(sd, 8),
                 "min": round(float(arr.min()), 5), "max": round(float(arr.max()), 5),
                 "q05": round(float(np.quantile(arr, 0.05)), 5),
                 "q95": round(float(np.quantile(arr, 0.95)), 5),
                 "by_family": {}}
        for fam in ("rand_norm_matched", "rand_orthogonal", "rand_in_pca_subspace"):
            f = [v["effect"] for v in per_cell.values()
                 if v["arm"].startswith(fam) and v["layer"] == layer
                 and v["group"] == group and v["alpha"] == alpha and v["site"] == site]
            if f:
                entry["by_family"][fam] = {"n": len(f), "mean": round(float(np.mean(f)), 5),
                                           "max": round(float(np.max(f)), 5)}
        entry["concept_arms"] = {}
        for v in per_cell.values():
            if v["arm"].startswith("rand_") or v["layer"] != layer \
                    or v["group"] != group or v["alpha"] != alpha or v["site"] != site:
                continue
            eff = v["effect"]
            pct = float((arr < eff).mean())
            entry["concept_arms"][v["arm"]] = {
                "effect": eff, "percentile_in_controls": round(pct, 4),
                "z_vs_controls": (round(float((eff - arr.mean()) / sd), 3)
                                  if sd_usable else None),
                "exceeds_all_controls": bool(eff > arr.max()),
                # "exceeds all controls" is only evidence if the effect is also
                # materially non-zero; a +0.0001 effect beating a control set that is
                # identically 0.0 is arithmetic, not a causal result.
                "materially_nonzero": bool(abs(eff) >= 0.01),
            }
        control_dist[f"{layer}|{group}|{alpha}|{site}"] = entry

    # ------------------------------------------------------------------ #
    # 4. dose-response, reversibility, J_causal (§4.5, §7)
    # ------------------------------------------------------------------ #
    dose = {}
    for arm in sorted({v["arm"] for v in per_cell.values() if not v["arm"].startswith("rand_")}):
        for site in sorted({v["site"] for v in per_cell.values()}):
            for layer in sorted({v["layer"] for v in per_cell.values()}):
                pts = [(float(v["alpha"]), v["effect"]) for v in per_cell.values()
                       if v["arm"] == arm and v["site"] == site and v["layer"] == layer
                       and v["alpha"] not in ("None",)]
                if len(pts) < 3:
                    continue
                pts.sort()
                a = [p[0] for p in pts]
                e = [p[1] for p in pts]
                pos = [e[i] for i, v in enumerate(a) if v > 0]
                neg = [e[i] for i, v in enumerate(a) if v < 0]
                # Baseline level for this cell — needed to tell "not reversible" apart from
                # "cannot go down". On NEUTRAL_CODEWORD prompts the concept probability is
                # already ~0, so a negative alpha has no room to reduce it and the
                # negative arm is identically 0 BY CONSTRUCTION. Reporting that as
                # `reversible: False` would read as a failed reversibility test when in
                # fact the test is uninformative in that direction. Downward control has to
                # be measured where the score is HIGH — i.e. by projecting the direction
                # OUT of a DOUBLESPEAK prompt (the `projout_*` arms).
                base_lvl = [v["mean_identity"] for v in per_cell.values()
                            if v["arm"] == arm and v["site"] == site and v["layer"] == layer]
                b0 = float(np.mean(base_lvl)) if base_lvl else float("nan")
                floor_limited = bool(neg and b0 < 0.01 and max(abs(x) for x in neg) < 0.01)
                dose[f"{arm}|{layer}|{site}"] = {
                    "alphas": a, "effects": e, "baseline_level": round(b0, 5),
                    "spearman_alpha_effect": round(spearman(a, e), 4),
                    "J_causal": (round(float(np.mean(pos)) - float(np.mean(neg)), 5)
                                 if pos and neg else None),
                    "monotone_positive_alpha": bool(len(pos) >= 3
                                                    and spearman([v for v in a if v > 0],
                                                                 pos) > 0.7),
                    "floor_limited_downward": floor_limited,
                    "reversible": (None if floor_limited else
                                   bool(pos and neg and np.mean(pos) > 0 > np.mean(neg))),
                }

    # ------------------------------------------------------------------ #
    # 5. causal attack window (§16.11)
    # ------------------------------------------------------------------ #
    n_layers = max((int(v["layer"]) for v in per_cell.values()
                    if v["layer"] not in ("None",)), default=-1) + 1
    attack_window = {}
    if n_layers > 0:
        wins = layer_windows(n_layers)
        for arm in sorted({v["arm"] for v in per_cell.values()
                           if not v["arm"].startswith("rand_")}):
            per_layer = {}
            for v in per_cell.values():
                if v["arm"] != arm or v["layer"] == "None":
                    continue
                per_layer.setdefault(int(v["layer"]), []).append(v["effect"])
            if not per_layer:
                continue
            means = {l: float(np.mean(e)) for l, e in per_layer.items()}
            sig = sorted(int(v["layer"]) for v in per_cell.values()
                         if v["arm"] == arm and v["layer"] != "None"
                         and v.get("significant_corrected"))
            attack_window[arm] = {
                "per_layer_mean_effect": {str(l): round(means[l], 5)
                                          for l in sorted(means)},
                "argmax_layer": int(max(means, key=means.get)),
                "max_effect": round(max(means.values()), 5),
                "significant_layers_corrected": sig,
                "window_hits": {w: sorted(set(sig) & set(v)) for w, v in wins.items()},
            }
        attack_window["_windows_def"] = {k: list(v) for k, v in wins.items()}

    out = {
        "plan": "CAUSAL_CORE_PLAN §4.5/§5/§7/§14 (S5-S7, S9, S10)",
        "interv_dirs": [os.path.abspath(d) for d in args.interv_dir],
        "metric": metric, "alpha_level": args.alpha_level,
        "n_rows": len(rows), "n_cells": len(per_cell),
        "n_layers_seen": n_layers,
        "per_cell": per_cell, "control_distribution": control_dist,
        "dose_response": dose, "attack_window": attack_window,
        "status": "COMPLETE",
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)

    print(f"[analyze] {len(rows)} rows, {len(per_cell)} cells -> {args.out}")
    for arm, aw in sorted(attack_window.items()):
        if arm.startswith("_"):
            continue
        print(f"  {arm:22} peak L{aw['argmax_layer']} eff={aw['max_effect']:+.4f} "
              f"sig_layers(Holm)={aw['significant_layers_corrected'][:8]}")
    shown = 0
    for k, v in sorted(control_dist.items()):
        for arm, c in sorted(v["concept_arms"].items()):
            # only report a control comparison that is BOTH beyond every control and
            # materially non-zero (see materially_nonzero above)
            if c["exceeds_all_controls"] and c["materially_nonzero"]:
                z = c["z_vs_controls"]
                print(f"  [ctrl] {k} {arm}: eff={c['effect']:+.4f} "
                      f"z={'n/a' if z is None else f'{z:+.2f}'} "
                      f"EXCEEDS all {v['n_controls']} controls")
                shown += 1
    if not shown:
        print("  [ctrl] no arm both exceeds its control distribution AND is materially "
              "non-zero (|effect| >= 0.01)")


if __name__ == "__main__":
    main()
