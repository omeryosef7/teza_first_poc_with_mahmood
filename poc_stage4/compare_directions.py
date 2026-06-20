"""
Stage 4 utility: compare refusal directions across extraction positions.

Loads candidate_directions.pt from:
  - EOI (prompt-end, before thinking)        outputs/stage4/qwen3-14b/refusal_direction/
  - StartOfThink (<think> token)             outputs/stage4/qwen3-14b/refusal_direction_startofthink/
  - EndOfThink (</think> token)              outputs/stage4/qwen3-14b/refusal_direction_endofthink/
  - Behavioral (complied vs refused outcome) outputs/stage4/qwen3-14b/refusal_direction_behavioral/

For each pair and each layer: cosine similarity.
Also prints selected-direction cosine similarity for the key pairs.

Output: outputs/stage4/qwen3-14b/direction_comparison/
  cosine_similarity_by_layer.csv
  cosine_summary.json
  plots/cosine_heatmap.png
  plots/cosine_by_layer.png
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

import numpy as np


def _load_candidate_directions(base: pathlib.Path, name: str) -> np.ndarray | None:
    """Load candidate_directions.pt and return [n_positions, n_layers, d_model] as numpy."""
    import torch
    p = base / name / "candidate_directions.pt"
    if not p.exists():
        return None
    t = torch.load(p, map_location="cpu", weights_only=False)
    return t.numpy().astype(np.float32)


def _load_selected_direction(base: pathlib.Path, name: str) -> np.ndarray | None:
    """Load direction.pt — shape [d_model]."""
    import torch
    p = base / name / "direction.pt"
    if not p.exists():
        return None
    t = torch.load(p, map_location="cpu", weights_only=False)
    return t.numpy().astype(np.float32)


def _load_selected_meta(base: pathlib.Path, name: str) -> dict:
    p = base / name / "selected_direction.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-dir",
        default="outputs/stage4/qwen3-14b",
        help="Base directory containing direction subdirs.",
    )
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    base = pathlib.Path(args.base_dir)
    output_dir = pathlib.Path(args.output_dir) if args.output_dir else base / "direction_comparison"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "plots").mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # Available directions
    # ------------------------------------------------------------------
    SOURCES = {
        "eoi": "refusal_direction",
        "startofthink": "refusal_direction_startofthink",
        "endofthink": "refusal_direction_endofthink",
        "behavioral": "refusal_direction_behavioral",
    }

    metas: dict[str, dict] = {}
    candidates: dict[str, np.ndarray] = {}
    selected: dict[str, np.ndarray] = {}
    best_layer: dict[str, int] = {}

    for key, subdir in SOURCES.items():
        cand = _load_candidate_directions(base, subdir)
        sel = _load_selected_direction(base, subdir)
        meta = _load_selected_meta(base, subdir)
        if cand is None:
            print(f"[compare] MISSING: {subdir} — skipping.", file=sys.stderr)
            continue
        candidates[key] = cand
        metas[key] = meta
        if sel is not None:
            selected[key] = sel
        layer_key = meta.get("selected_layer")
        if layer_key is not None:
            best_layer[key] = int(layer_key)

    print(f"[compare] Loaded directions: {list(candidates.keys())}")
    for k, v in candidates.items():
        print(f"  {k}: candidate shape={v.shape}, best_layer={best_layer.get(k)}")

    if len(candidates) < 2:
        print("[compare] Need at least 2 direction sets to compare. Exiting.")
        sys.exit(0)

    keys = list(candidates.keys())
    n_layers = candidates[keys[0]].shape[1]

    # For EOI, use the best position index (position_index from meta)
    eoi_pos_idx = 0
    if "eoi" in metas:
        eoi_pos_idx = int(metas["eoi"].get("selected_position_index", 0))

    def get_layer_dir(key: str, layer: int) -> np.ndarray:
        cand = candidates[key]
        pos_idx = eoi_pos_idx if key == "eoi" else 0
        return cand[pos_idx, layer, :]

    # ------------------------------------------------------------------
    # Per-layer cosine similarity for all pairs
    # ------------------------------------------------------------------
    pairs = [(keys[i], keys[j]) for i in range(len(keys)) for j in range(i + 1, len(keys))]
    rows = []
    for layer in range(n_layers):
        for ka, kb in pairs:
            da = get_layer_dir(ka, layer)
            db = get_layer_dir(kb, layer)
            sim = cosine(da, db)
            rows.append({
                "layer": layer,
                "pair": f"{ka}_vs_{kb}",
                "cosine_similarity": round(float(sim), 6) if not math.isnan(sim) else None,
            })

    import csv
    csv_path = output_dir / "cosine_similarity_by_layer.csv"
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["layer", "pair", "cosine_similarity"])
        w.writeheader()
        w.writerows(rows)
    print(f"[compare] Wrote {len(rows)} rows to {csv_path}")

    # ------------------------------------------------------------------
    # Summary: cosine at best layer + between selected direction vectors
    # ------------------------------------------------------------------
    summary: dict = {
        "available_directions": keys,
        "per_pair_at_best_layers": [],
        "selected_direction_cosines": [],
        "per_pair_summary": [],
    }

    for ka, kb in pairs:
        sims = [r["cosine_similarity"] for r in rows if r["pair"] == f"{ka}_vs_{kb}" and r["cosine_similarity"] is not None]
        if not sims:
            continue
        a_best = best_layer.get(ka)
        b_best = best_layer.get(kb)
        sim_at_a_best = cosine(get_layer_dir(ka, a_best), get_layer_dir(kb, a_best)) if a_best is not None else None
        sim_at_b_best = cosine(get_layer_dir(ka, b_best), get_layer_dir(kb, b_best)) if b_best is not None else None
        max_sim = float(np.nanmax(sims))
        argmax_layer = [r["layer"] for r in rows if r["pair"] == f"{ka}_vs_{kb}" and r["cosine_similarity"] == max_sim]
        summary["per_pair_at_best_layers"].append({
            "pair": f"{ka}_vs_{kb}",
            "sim_at_{ka}_best_layer": round(sim_at_a_best, 4) if sim_at_a_best is not None else None,
            "sim_at_{kb}_best_layer": round(sim_at_b_best, 4) if sim_at_b_best is not None else None,
            "max_cosine_over_layers": round(max_sim, 4),
            "argmax_layer": argmax_layer[0] if argmax_layer else None,
        })
        if ka in selected and kb in selected:
            sim_sel = cosine(selected[ka], selected[kb])
            summary["selected_direction_cosines"].append({
                "pair": f"{ka}_vs_{kb}",
                "cosine": round(float(sim_sel), 4),
                "ka_layer": best_layer.get(ka),
                "kb_layer": best_layer.get(kb),
            })
        summary["per_pair_summary"].append({
            "pair": f"{ka}_vs_{kb}",
            "mean_abs_cosine": round(float(np.mean(np.abs(sims))), 4),
            "max_abs_cosine": round(float(np.max(np.abs(sims))), 4),
            "min_abs_cosine": round(float(np.min(np.abs(sims))), 4),
        })

    summary_path = output_dir / "cosine_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"[compare] Summary written to {summary_path}")

    # Print key results
    print("\n=== Selected-direction cosine similarities ===")
    for entry in summary["selected_direction_cosines"]:
        print(f"  {entry['pair']}: cosine={entry['cosine']:.4f}  (layers {entry['ka_layer']} vs {entry['kb_layer']})")

    print("\n=== Per-pair cosine at best layers ===")
    for entry in summary["per_pair_at_best_layers"]:
        print(f"  {entry['pair']}: max_layer_cosine={entry['max_cosine_over_layers']:.4f} @ layer {entry['argmax_layer']}")

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Heatmap: pairs × layers
        pair_labels = [p["pair"] for p in summary["per_pair_summary"]]
        matrix = np.full((len(pairs), n_layers), np.nan)
        for ri, r in enumerate(rows):
            pair_idx = next((i for i, p in enumerate(pairs) if f"{p[0]}_vs_{p[1]}" == r["pair"]), None)
            if pair_idx is not None and r["cosine_similarity"] is not None:
                matrix[pair_idx, r["layer"]] = r["cosine_similarity"]

        fig, ax = plt.subplots(figsize=(14, max(3, len(pairs) * 1.2)))
        im = ax.imshow(matrix, aspect="auto", vmin=-1, vmax=1, cmap="RdBu_r")
        ax.set_yticks(range(len(pairs)))
        ax.set_yticklabels(pair_labels, fontsize=8)
        ax.set_xlabel("Layer")
        ax.set_title("Cosine similarity between direction pairs, per layer")
        plt.colorbar(im, ax=ax, label="Cosine similarity")
        plt.tight_layout()
        heatmap_path = output_dir / "plots" / "cosine_heatmap.png"
        plt.savefig(heatmap_path, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"[compare] Heatmap saved to {heatmap_path}")

        # Line plot: cosine per layer for each pair
        fig, ax = plt.subplots(figsize=(12, 4))
        for pair_idx, (ka, kb) in enumerate(pairs):
            pair_key = f"{ka}_vs_{kb}"
            pair_sims = [r["cosine_similarity"] if r["cosine_similarity"] is not None else np.nan
                         for r in rows if r["pair"] == pair_key]
            ax.plot(range(n_layers), pair_sims, label=pair_key, marker=".", markersize=3)
        ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
        ax.set_xlabel("Layer")
        ax.set_ylabel("Cosine similarity")
        ax.set_title("Direction cosine similarity per layer")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        line_path = output_dir / "plots" / "cosine_by_layer.png"
        plt.savefig(line_path, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"[compare] Line plot saved to {line_path}")

    except Exception as e:
        print(f"[compare] Plot error (non-fatal): {e}", file=sys.stderr)

    print("[compare] Done.")


if __name__ == "__main__":
    main()
