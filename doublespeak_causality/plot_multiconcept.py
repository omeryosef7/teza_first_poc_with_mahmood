"""plot_multiconcept.py — visualize aggregated multi-concept causal results.

Consumes three JSONs produced by the doublespeak-causality pipeline and writes
four PNGs using the generic helpers in ``plots.py``:

  1. per-concept hijack strength         -> multiconcept_hijack_strength.png
  2. timing (peak layer) per concept     -> multiconcept_timing.png
  3. necessity vs sufficiency per concept -> multiconcept_necsuff.png
  4. emergence overlay (mean trajectory) -> multiconcept_emergence_overlay.png

Inputs
------
--agg        JSON written by ``aggregate_multiconcept.py`` (per-concept summary).
--emergence  JSON from ``11_emergence_trajectory.py`` (per-item p_harm_by_layer).
--necsuff    JSON from ``07_patchscope_readout.py`` (per-item nec/suff sweeps).

The ``--agg`` file is the authoritative source for the per-concept scalars used
by plots 1-3. Because the exact agg schema is flexible, each metric falls back
to being recomputed from the emergence/necsuff JSONs when the agg file is
absent or missing that field (see ``_per_concept_metrics``).

All plotting is delegated to ``plots.py`` (headless Agg backend set there).
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

# plots.py already sets matplotlib to the Agg backend on import; import it first
# so no interactive backend is ever selected. Guard with an explicit fallback.
try:
    import plots  # type: ignore
except Exception:  # pragma: no cover - defensive backend fallback
    import matplotlib

    matplotlib.use("Agg")
    import plots  # type: ignore


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _load_json(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    with open(path, "r") as fh:
        return json.load(fh)


def concept_of(item_id: str) -> str:
    """Return the concept for an item id ``"<concept>_<codeword>"``.

    The codeword is the final underscore-separated token; everything before it
    is the concept. ``"bomb_mirror" -> "bomb"``, ``"nerve_agent_muffin" ->
    "nerve_agent"``. Ids without an underscore map to themselves.
    """
    return item_id.rsplit("_", 1)[0] if "_" in item_id else item_id


def _argmax(values: List[float]) -> int:
    best_i, best_v = 0, float("-inf")
    for i, v in enumerate(values):
        if v is not None and v > best_v:
            best_i, best_v = i, float(v)
    return best_i


def _mean(values: List[float]) -> float:
    vals = [float(v) for v in values if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


# --------------------------------------------------------------------------- #
# per-concept metric extraction (agg preferred, JSON-derived fallback)
# --------------------------------------------------------------------------- #
def _agg_concept_table(agg: Optional[dict]) -> Dict[str, Dict[str, float]]:
    """Normalize the agg JSON into ``{concept: {metric: value}}``.

    Accepts either ``{"per_concept": {concept: {...}}}`` or
    ``{"concepts": [{"concept": name, ...}, ...]}``. Unknown shapes yield {}.
    """
    if not agg:
        return {}
    table: Dict[str, Dict[str, float]] = {}
    pc = agg.get("per_concept")
    if isinstance(pc, dict):
        for name, entry in pc.items():
            if isinstance(entry, dict):
                table[str(name)] = dict(entry)
        return table
    lst = agg.get("concepts")
    if isinstance(lst, list):
        for entry in lst:
            if isinstance(entry, dict) and "concept" in entry:
                table[str(entry["concept"])] = {
                    k: v for k, v in entry.items() if k != "concept"
                }
    return table


def _first(entry: Dict[str, Any], keys: Tuple[str, ...]) -> Optional[float]:
    for k in keys:
        if k in entry and entry[k] is not None:
            try:
                return float(entry[k])
            except (TypeError, ValueError):
                return None
    return None


def _per_concept_metrics(
    agg: Optional[dict],
    emergence: Optional[dict],
    necsuff: Optional[dict],
) -> Tuple[List[str], Dict[str, Dict[str, float]]]:
    """Build per-concept metrics, preferring agg fields, else recomputing.

    Returns ``(concepts_sorted, {concept: {metric: value}})`` with metrics:
    ``mean_ds_strength, direct_peak_layer, doublespeak_peak_layer,
    necessity_frac, suff_ds, suff_direct``.
    """
    agg_table = _agg_concept_table(agg)

    # --- recompute-from-raw tables (used as fallback per metric) --------------
    emg_by_concept: Dict[str, Dict[str, List[float]]] = defaultdict(
        lambda: {"ds_strength": [], "direct_peak": [], "ds_peak": []}
    )
    if emergence:
        for it in emergence.get("items", []):
            p = it.get("p_harm_by_layer", {})
            direct = p.get("direct") or []
            neutral = p.get("neutral") or []
            ds = p.get("doublespeak") or []
            c = concept_of(str(it.get("id", "")))
            if ds:
                strength = max(ds) - (max(neutral) if neutral else 0.0)
                emg_by_concept[c]["ds_strength"].append(strength)
                emg_by_concept[c]["ds_peak"].append(float(_argmax(ds)))
            if direct:
                emg_by_concept[c]["direct_peak"].append(float(_argmax(direct)))

    ns_by_concept: Dict[str, Dict[str, List[float]]] = defaultdict(
        lambda: {"necessity_frac": [], "suff_ds": [], "suff_direct": []}
    )
    if necsuff:
        for it in necsuff.get("items", []):
            c = concept_of(str(it.get("id", "")))
            base_ds = (it.get("baseline_ds_patchscope") or {}).get("p_harm", 0.0)
            nec = it.get("necessity") or []
            # necessity_frac: fraction of swept layers where patching the clean
            # activation into the DS run reduces p_harm below the DS baseline.
            if nec:
                drops = sum(
                    1 for e in nec if float(e.get("p_harm", 0.0)) < float(base_ds)
                )
                ns_by_concept[c]["necessity_frac"].append(drops / len(nec))
            suff = it.get("sufficiency") or []
            if suff:
                ns_by_concept[c]["suff_direct"].append(
                    max(float(e.get("p_harm", 0.0)) for e in suff)
                )
            suff_ds = it.get("sufficiency_ds") or []
            if suff_ds:
                ns_by_concept[c]["suff_ds"].append(
                    max(float(e.get("p_harm", 0.0)) for e in suff_ds)
                )

    # --- union of concepts across all sources --------------------------------
    concepts = sorted(
        set(agg_table) | set(emg_by_concept) | set(ns_by_concept)
    )

    out: Dict[str, Dict[str, float]] = {}
    for c in concepts:
        a = agg_table.get(c, {})
        emg = emg_by_concept.get(c, {})
        ns = ns_by_concept.get(c, {})
        out[c] = {
            "mean_ds_strength": _first(a, ("mean_ds_strength", "ds_strength"))
            or _mean(emg.get("ds_strength", [])),
            "direct_peak_layer": _first(a, ("direct_peak_layer", "direct_peak"))
            if _first(a, ("direct_peak_layer", "direct_peak")) is not None
            else _mean(emg.get("direct_peak", [])),
            "doublespeak_peak_layer": _first(
                a, ("doublespeak_peak_layer", "ds_peak_layer", "ds_peak")
            )
            if _first(a, ("doublespeak_peak_layer", "ds_peak_layer", "ds_peak"))
            is not None
            else _mean(emg.get("ds_peak", [])),
            "necessity_frac": _first(a, ("necessity_frac",))
            if _first(a, ("necessity_frac",)) is not None
            else _mean(ns.get("necessity_frac", [])),
            "suff_ds": _first(a, ("suff_ds", "sufficiency_ds"))
            if _first(a, ("suff_ds", "sufficiency_ds")) is not None
            else _mean(ns.get("suff_ds", [])),
            "suff_direct": _first(a, ("suff_direct", "sufficiency"))
            if _first(a, ("suff_direct", "sufficiency")) is not None
            else _mean(ns.get("suff_direct", [])),
        }
    return concepts, out


# --------------------------------------------------------------------------- #
# the four plots
# --------------------------------------------------------------------------- #
def plot_hijack_strength(
    concepts: List[str],
    metrics: Dict[str, Dict[str, float]],
    outdir: str,
) -> str:
    out = os.path.join(outdir, "multiconcept_hijack_strength.png")
    return plots.grouped_bars(
        concepts,
        {"mean ds_strength": [metrics[c]["mean_ds_strength"] for c in concepts]},
        out,
        title="Per-concept hijack strength",
        ylabel="mean p_harm(DS) - p_harm(neutral)",
    )


def plot_timing(
    concepts: List[str],
    metrics: Dict[str, Dict[str, float]],
    outdir: str,
) -> str:
    out = os.path.join(outdir, "multiconcept_timing.png")
    return plots.grouped_bars(
        concepts,
        {
            "Direct peak layer": [metrics[c]["direct_peak_layer"] for c in concepts],
            "Doublespeak peak layer": [
                metrics[c]["doublespeak_peak_layer"] for c in concepts
            ],
        },
        out,
        title="Per-concept emergence timing",
        ylabel="peak layer",
    )


def plot_necsuff(
    concepts: List[str],
    metrics: Dict[str, Dict[str, float]],
    outdir: str,
) -> str:
    out = os.path.join(outdir, "multiconcept_necsuff.png")
    return plots.grouped_bars(
        concepts,
        {
            "necessity_frac": [metrics[c]["necessity_frac"] for c in concepts],
            "suff(DS)": [metrics[c]["suff_ds"] for c in concepts],
            "suff(Direct)": [metrics[c]["suff_direct"] for c in concepts],
        },
        out,
        title="Per-concept necessity vs sufficiency",
        ylabel="fraction / p_harm",
    )


def plot_emergence_overlay(emergence: dict, outdir: str) -> str:
    """Mean p_harm trajectory over all (hijacker) items in the emergence JSON."""
    out = os.path.join(outdir, "multiconcept_emergence_overlay.png")
    items = emergence.get("items", [])
    num_layers = int(
        emergence.get("num_layers")
        or (
            len(items[0]["p_harm_by_layer"]["direct"])
            if items
            else 0
        )
    )
    layers = list(range(num_layers))

    means: Dict[str, List[float]] = {}
    for cond, label in (
        ("direct", "Direct(mean)"),
        ("doublespeak", "Doublespeak(mean)"),
        ("neutral", "Neutral(mean)"),
    ):
        stacked = [
            it["p_harm_by_layer"][cond]
            for it in items
            if cond in it.get("p_harm_by_layer", {})
            and len(it["p_harm_by_layer"][cond]) == num_layers
        ]
        if stacked:
            means[label] = [
                sum(series[L] for series in stacked) / len(stacked)
                for L in range(num_layers)
            ]
        else:
            means[label] = [0.0] * num_layers

    return plots.layer_trajectory(
        layers,
        means,
        out,
        title="Emergence overlay (mean over hijacker items)",
        ylabel="p_harm",
    )


# --------------------------------------------------------------------------- #
# orchestration
# --------------------------------------------------------------------------- #
def run_all(
    agg_path: Optional[str],
    emergence_path: Optional[str],
    necsuff_path: Optional[str],
    outdir: str,
) -> Dict[str, str]:
    os.makedirs(outdir, exist_ok=True)
    agg = _load_json(agg_path)
    emergence = _load_json(emergence_path)
    necsuff = _load_json(necsuff_path)

    concepts, metrics = _per_concept_metrics(agg, emergence, necsuff)

    paths: Dict[str, str] = {}
    if concepts:
        paths["hijack_strength"] = plot_hijack_strength(concepts, metrics, outdir)
        paths["timing"] = plot_timing(concepts, metrics, outdir)
        paths["necsuff"] = plot_necsuff(concepts, metrics, outdir)
    if emergence and emergence.get("items"):
        paths["emergence_overlay"] = plot_emergence_overlay(emergence, outdir)
    return paths


def main() -> None:
    ap = argparse.ArgumentParser(description="Plot multi-concept causal results.")
    ap.add_argument("--agg", default=None, help="aggregate_multiconcept.py JSON")
    ap.add_argument("--emergence", default=None, help="11_emergence_trajectory.py JSON")
    ap.add_argument("--necsuff", default=None, help="07_patchscope_readout.py JSON")
    ap.add_argument("--outdir", required=True, help="output directory for PNGs")
    args = ap.parse_args()

    paths = run_all(args.agg, args.emergence, args.necsuff, args.outdir)
    for name, p in paths.items():
        print(f"{name}: {p}")


if __name__ == "__main__":
    main()
