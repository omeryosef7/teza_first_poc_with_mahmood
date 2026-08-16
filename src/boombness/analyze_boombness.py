"""analyze_boombness.py — plan §6.4 (metric comparison) and §7 (token- vs prompt-level).

Pure CPU. Consumes an `extract_boombness` run directory and produces the plan's required
tables and figures. Nothing here re-runs the model, so metric definitions can be revised
without spending GPU time.

WHAT IT ANSWERS
  §7.1  token level   — boombness[occurrence i, layer L] per condition; does the FINAL
                        (query) occurrence become more concept-like than the earlier demo
                        occurrences, and in which layers?
  §7.2  prompt level  — the candidate aggregations, each scored on how well it SEPARATES
                        the doublespeak arm from its matched benign-literal control
                        (the prompt-level quantity §9 will regress ASR on).
  §6.4  metrics       — logit-lens vs each direction projection, correlated with each other
                        and with the design factors (n_examples, condition, role_style).

THE SANITY CHECK THAT MUST PASS FIRST
By construction `d_surface` points from codeword to concept, so on the FITTING contrast the
concept-surface cells (B, E) must score higher than the codeword-surface cells (A, C). If they
do not, the direction is not measuring what its name says and every downstream number is void.
`--strict` makes that a non-zero exit rather than a footnote.

Figures use matplotlib only (seaborn is not installed in poc_stage2) and are written to the
run's plots/ directory.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

CELL_ORDER = ["A", "C", "E", "B"]
CELL_LABEL = {"A": "A benign_literal", "C": "C natural_doublespeak",
              "E": "E concept_in_benign_ctx", "B": "B direct_harmful",
              "D": "D direct_codeword", "F": "F benign_remap"}
CODEWORD_CELLS = {"A", "C", "D", "F"}
CONCEPT_CELLS = {"B", "E"}


# --------------------------------------------------------------------------- #
# small stats helpers (scipy is available but these keep the output self-describing)
# --------------------------------------------------------------------------- #
def mean(xs: Sequence[float]) -> float:
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    return sum(xs) / len(xs) if xs else float("nan")


def sem(xs: Sequence[float]) -> float:
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    if len(xs) < 2:
        return float("nan")
    m = sum(xs) / len(xs)
    v = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(v / len(xs))


def cohens_d(a: Sequence[float], b: Sequence[float]) -> float:
    a = [x for x in a if x is not None and math.isfinite(x)]
    b = [x for x in b if x is not None and math.isfinite(x)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    ma, mb = mean(a), mean(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    sp = math.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / (len(a) + len(b) - 2))
    return (ma - mb) / sp if sp > 1e-12 else float("nan")


def spearman(x: Sequence[float], y: Sequence[float]) -> Tuple[float, int]:
    pairs = [(a, b) for a, b in zip(x, y)
             if a is not None and b is not None and math.isfinite(a) and math.isfinite(b)]
    if len(pairs) < 3:
        return float("nan"), len(pairs)
    try:
        from scipy.stats import spearmanr
        r = spearmanr([p[0] for p in pairs], [p[1] for p in pairs])
        return float(r.statistic), len(pairs)
    except Exception:
        return float("nan"), len(pairs)


# --------------------------------------------------------------------------- #
# column discovery
# --------------------------------------------------------------------------- #
COL_RE = re.compile(r"^(?P<metric>[a-z_]+)\|L(?P<layer>\d+)\|(?P<stat>\w+)$")


def discover_columns(rows: List[Dict]) -> Dict[str, List[int]]:
    """Map "<metric>|<stat>" -> sorted layers present."""
    found: Dict[str, set] = collections.defaultdict(set)
    for r in rows[:200]:
        for k in r:
            m = COL_RE.match(k)
            if m:
                found[f"{m['metric']}|{m['stat']}"].add(int(m["layer"]))
    return {k: sorted(v) for k, v in sorted(found.items())}


def col(metric_stat: str, layer: int) -> str:
    metric, stat = metric_stat.split("|")
    return f"{metric}|L{layer}|{stat}"


# --------------------------------------------------------------------------- #
# §6.4 sanity: does d_surface separate concept-surface from codeword-surface cells?
# --------------------------------------------------------------------------- #
def direction_sanity(rows: List[Dict], metric_stat: str, layers: Sequence[int]) -> Dict:
    final = [r for r in rows if r.get("is_final_occurrence")]
    out = {}
    for L in layers:
        c = col(metric_stat, L)
        concept = [r[c] for r in final if r["cell"] in CONCEPT_CELLS and c in r]
        code = [r[c] for r in final if r["cell"] in CODEWORD_CELLS and c in r]
        out[L] = {"mean_concept_surface": mean(concept), "mean_codeword_surface": mean(code),
                  "delta": mean(concept) - mean(code), "d": cohens_d(concept, code),
                  "n_concept": len(concept), "n_codeword": len(code)}
    ok_layers = [L for L, v in out.items() if v["delta"] > 0]
    return {"per_layer": out, "n_layers_positive": len(ok_layers),
            "n_layers": len(layers),
            "best_layer": max(out, key=lambda L: out[L]["d"] if math.isfinite(out[L]["d"]) else -9e9)
            if out else None}


# --------------------------------------------------------------------------- #
# §7.1 token-level dynamics
# --------------------------------------------------------------------------- #
def occurrence_by_layer(rows: List[Dict], metric_stat: str, layers: Sequence[int],
                        condition: str, max_occ: int = 17) -> Dict[int, Dict[int, float]]:
    """{occurrence_index: {layer: mean metric}} for one condition."""
    acc: Dict[Tuple[int, int], List[float]] = collections.defaultdict(list)
    for r in rows:
        if r["condition"] != condition:
            continue
        oi = r["occurrence_index"]
        if oi >= max_occ:
            continue
        for L in layers:
            c = col(metric_stat, L)
            if c in r:
                acc[(oi, L)].append(r[c])
    out: Dict[int, Dict[int, float]] = collections.defaultdict(dict)
    for (oi, L), vs in acc.items():
        out[oi][L] = mean(vs)
    return dict(out)


def final_vs_earlier(rows: List[Dict], metric_stat: str, layers: Sequence[int],
                     condition: str) -> Dict[int, Dict]:
    """Plan §7.1 key question: is the FINAL (query) occurrence more concept-like than the
    demo occurrences of the SAME prompt? Paired within prompt, so prompt-level variation
    cannot manufacture the effect."""
    out = {}
    for L in layers:
        c = col(metric_stat, L)
        by_prompt: Dict[str, Dict[str, List[float]]] = collections.defaultdict(
            lambda: {"final": [], "earlier": []})
        for r in rows:
            if r["condition"] != condition or c not in r:
                continue
            if r["n_occurrences"] < 2:
                continue
            by_prompt[r["prompt_id"]]["final" if r["is_final_occurrence"] else "earlier"].append(r[c])
        deltas = []
        for _, d in by_prompt.items():
            if d["final"] and d["earlier"]:
                deltas.append(mean(d["final"]) - mean(d["earlier"]))
        out[L] = {"mean_delta_final_minus_earlier": mean(deltas), "sem": sem(deltas),
                  "n_prompts": len(deltas),
                  "frac_positive": (sum(1 for x in deltas if x > 0) / len(deltas)) if deltas else float("nan")}
    return out


# --------------------------------------------------------------------------- #
# §7.2 prompt-level aggregations
# --------------------------------------------------------------------------- #
def prompt_level(rows: List[Dict], metric_stat: str, layers: Sequence[int],
                 mid: Optional[Sequence[int]] = None,
                 late: Optional[Sequence[int]] = None) -> Dict[str, Dict[str, float]]:
    """{prompt_id: {aggregation_name: value}} — the plan §7.2 candidate list."""
    n_layers = max(layers) + 1 if layers else 0
    mid = list(mid) if mid is not None else [L for L in layers if n_layers // 4 <= L < 3 * n_layers // 4]
    late = list(late) if late is not None else [L for L in layers if L >= 3 * n_layers // 4]
    by_prompt: Dict[str, List[Dict]] = collections.defaultdict(list)
    for r in rows:
        by_prompt[r["prompt_id"]].append(r)

    out: Dict[str, Dict[str, float]] = {}
    for pid, rs in by_prompt.items():
        finals = [r for r in rs if r.get("is_final_occurrence")]
        if not finals:
            continue
        f = finals[0]
        fvals = {L: f[col(metric_stat, L)] for L in layers if col(metric_stat, L) in f}
        allvals = [r[col(metric_stat, L)] for r in rs for L in layers if col(metric_stat, L) in r]
        if not fvals:
            continue
        best_L = max(fvals, key=lambda L: fvals[L])
        out[pid] = {
            "final_best_layer_value": fvals[best_L],
            "final_best_layer": best_L,
            "final_mid_mean": mean([fvals[L] for L in mid if L in fvals]),
            "final_late_mean": mean([fvals[L] for L in late if L in fvals]),
            "final_layer_auc": mean(list(fvals.values())),          # AUC over layers, normalized
            "max_over_all_tokens_layers": max(allvals) if allvals else float("nan"),
            "mean_over_all_tokens_layers": mean(allvals),
        }
    return out


def separation_by_aggregation(prompt_vals: Dict[str, Dict[str, float]],
                              meta: Dict[str, Dict]) -> Dict[str, Dict[str, float]]:
    """How well does each aggregation separate C (doublespeak) from its A control?"""
    aggs = sorted({k for v in prompt_vals.values() for k in v} - {"final_best_layer"})
    out = {}
    for a in aggs:
        c = [v[a] for p, v in prompt_vals.items() if meta.get(p, {}).get("cell") == "C" and a in v]
        b = [v[a] for p, v in prompt_vals.items() if meta.get(p, {}).get("cell") == "A" and a in v]
        out[a] = {"mean_C": mean(c), "mean_A": mean(b), "delta": mean(c) - mean(b),
                  "cohens_d": cohens_d(c, b), "n_C": len(c), "n_A": len(b)}
    return out


# --------------------------------------------------------------------------- #
# plots
# --------------------------------------------------------------------------- #
def plot_layer_curves(rows: List[Dict], metric_stat: str, layers: Sequence[int],
                      path: str, title: str) -> None:
    final = [r for r in rows if r.get("is_final_occurrence")]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for cell in CELL_ORDER:
        ys, es = [], []
        for L in layers:
            c = col(metric_stat, L)
            vs = [r[c] for r in final if r["cell"] == cell and c in r]
            ys.append(mean(vs)); es.append(sem(vs))
        if not any(math.isfinite(y) for y in ys):
            continue
        ax.plot(list(layers), ys, marker="o", ms=3, lw=1.6, label=CELL_LABEL[cell])
        ax.fill_between(list(layers), [y - e for y, e in zip(ys, es)],
                        [y + e for y, e in zip(ys, es)], alpha=0.15)
    ax.axhline(0, color="0.6", lw=0.8, ls="--")
    ax.set_xlabel("block layer L  (hidden_states[L+1])")
    ax.set_ylabel(metric_stat)
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)


def plot_occurrence_heatmap(grid: Dict[int, Dict[int, float]], layers: Sequence[int],
                            path: str, title: str) -> None:
    occ = sorted(grid)
    if not occ:
        return
    import numpy as np
    M = np.full((len(layers), len(occ)), np.nan)
    for j, o in enumerate(occ):
        for i, L in enumerate(layers):
            v = grid[o].get(L)
            if v is not None and math.isfinite(v):
                M[i, j] = v
    fig, ax = plt.subplots(figsize=(max(4.5, 0.45 * len(occ) + 2), 4.6))
    vmax = np.nanmax(np.abs(M)) if np.isfinite(M).any() else 1.0
    im = ax.imshow(M, aspect="auto", origin="lower", cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                   extent=[-0.5, len(occ) - 0.5, min(layers) - 0.5, max(layers) + 0.5])
    ax.set_xticks(range(len(occ)))
    ax.set_xticklabels([("query" if o == occ[-1] else str(o)) for o in occ], fontsize=7)
    ax.set_xlabel("target occurrence index (last = final query)")
    ax.set_ylabel("block layer L")
    ax.set_title(title, fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.85)
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)


def plot_vs_n_examples(rows: List[Dict], metric_stat: str, layer: int, path: str,
                       title: str) -> None:
    final = [r for r in rows if r.get("is_final_occurrence")]
    c = col(metric_stat, layer)
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for cell in CELL_ORDER:
        ns = sorted({r["n_examples"] for r in final if r["cell"] == cell})
        ys = [mean([r[c] for r in final if r["cell"] == cell and r["n_examples"] == n and c in r])
              for n in ns]
        es = [sem([r[c] for r in final if r["cell"] == cell and r["n_examples"] == n and c in r])
              for n in ns]
        if ns:
            ax.errorbar(ns, ys, yerr=es, marker="o", ms=4, lw=1.6, capsize=3,
                        label=CELL_LABEL[cell])
    ax.set_xlabel("n_examples (demonstrations)")
    ax.set_ylabel(f"{metric_stat} @ L{layer}")
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, help="extract_boombness run directory")
    ap.add_argument("--metric", default="d_surface|cos",
                    help='"<metric>|<stat>", e.g. d_surface|cos, d_naive|proj, ll|boombness')
    ap.add_argument("--out", default=None, help="default = <run>/analysis")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if the d_surface sanity check fails")
    args = ap.parse_args()

    rows = read_jsonl(os.path.join(args.run, "results.jsonl"))
    if not rows:
        raise SystemExit(f"no results.jsonl rows under {args.run}")
    outdir = args.out or os.path.join(args.run, "analysis")
    plots = os.path.join(outdir, "plots")
    os.makedirs(plots, exist_ok=True)

    cols = discover_columns(rows)
    print(f"[analyze] {len(rows)} occurrence-rows; metric columns available:")
    for k, ls in cols.items():
        print(f"  {k:24s} layers {ls[0]}..{ls[-1]} (n={len(ls)})")
    if args.metric not in cols:
        raise SystemExit(f"--metric {args.metric!r} not in results; available: {sorted(cols)}")
    layers = cols[args.metric]

    meta = {r["prompt_id"]: r for r in rows if r.get("is_final_occurrence")}
    report: Dict[str, object] = {
        "run": os.path.abspath(args.run), "metric": args.metric,
        "layers": layers, "n_occurrence_rows": len(rows),
        "n_prompts": len(meta),
        "columns_available": cols,
        "conditions": dict(collections.Counter(r["condition"] for r in rows)),
    }

    # -- sanity ------------------------------------------------------------- #
    san = direction_sanity(rows, args.metric, layers)
    report["direction_sanity"] = san
    print(f"[analyze] d_surface sanity: {san['n_layers_positive']}/{san['n_layers']} layers "
          f"have concept-surface > codeword-surface; best layer L{san['best_layer']} "
          f"(d={san['per_layer'][san['best_layer']]['d']:.2f})" if san["best_layer"] is not None
          else "[analyze] sanity: no layers")

    # -- §7.1 token level --------------------------------------------------- #
    tok = {}
    for cond in ("natural_doublespeak", "benign_literal", "direct_harmful", "concept_in_benign_ctx"):
        grid = occurrence_by_layer(rows, args.metric, layers, cond)
        if grid:
            plot_occurrence_heatmap(
                grid, layers, os.path.join(plots, f"occurrence_x_layer_{cond}.png"),
                f"{args.metric} — occurrence x layer — {cond}")
        tok[cond] = {"final_vs_earlier": final_vs_earlier(rows, args.metric, layers, cond)}
    report["token_level"] = tok

    # -- §7.2 prompt level -------------------------------------------------- #
    pv = prompt_level(rows, args.metric, layers)
    sep = separation_by_aggregation(pv, meta)
    report["prompt_level_separation_C_vs_A"] = sep
    best_agg = max(sep, key=lambda a: sep[a]["cohens_d"] if math.isfinite(sep[a]["cohens_d"]) else -9e9) \
        if sep else None
    report["best_prompt_aggregation"] = best_agg
    print(f"[analyze] best prompt-level aggregation for C-vs-A separation: {best_agg} "
          f"(d={sep[best_agg]['cohens_d']:.2f})" if best_agg else "[analyze] no aggregation")

    with open(os.path.join(outdir, "prompt_level_boombness.json"), "w") as f:
        json.dump({p: {**v, **{k: meta[p][k] for k in
                               ("condition", "cell", "domain", "split", "n_examples",
                                "strength", "consistency", "example_position", "role_style",
                                "query_kind", "bank_block")}}
                   for p, v in pv.items() if p in meta}, f, indent=2)

    # -- §6.4 metric comparison --------------------------------------------- #
    comp = {}
    best_L = san["best_layer"]
    if best_L is not None:
        finals = [r for r in rows if r.get("is_final_occurrence")]
        ref = [r.get(col(args.metric, best_L)) for r in finals]
        for other in cols:
            if other == args.metric:
                continue
            oL = min(cols[other], key=lambda L: abs(L - best_L))
            r_s, n = spearman(ref, [r.get(col(other, oL)) for r in finals])
            comp[f"{other}@L{oL}"] = {"spearman_vs_metric": r_s, "n": n}
        r_n, n_n = spearman([r["n_examples"] for r in finals], ref)
        comp["n_examples"] = {"spearman_vs_metric": r_n, "n": n_n}
    report["metric_comparison"] = comp

    # -- plots -------------------------------------------------------------- #
    plot_layer_curves(rows, args.metric, layers, os.path.join(plots, "metric_by_layer.png"),
                      f"{args.metric} at the final (query) occurrence, by 2x2 cell")
    if best_L is not None:
        plot_vs_n_examples(rows, args.metric, best_L,
                           os.path.join(plots, "metric_vs_n_examples.png"),
                           f"{args.metric} @ L{best_L} vs number of demonstrations")

    with open(os.path.join(outdir, "analysis_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[analyze] -> {outdir}")

    if args.strict and san["n_layers_positive"] < 0.5 * max(1, san["n_layers"]):
        print("[analyze] STRICT FAIL: d_surface does not separate concept from codeword "
              "surfaces in a majority of layers — the direction is not measuring what it claims.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
