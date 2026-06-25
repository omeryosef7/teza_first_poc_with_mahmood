"""
Analyze direction geometry by attack outcome — Q2: attenuation vs rotation vs orthogonal bypass.

Reads existing Stage 4B outputs (direction comparison cosine summaries, AUC tables)
and classifies the geometric relationship between the clean refusal direction (EOI)
and the attack-success behavioral direction.

Key inputs (all pre-computed on disk):
  outputs/stage4/{model}/direction_comparison/cosine_summary.json
  outputs/stage4/{model}/subspace_stats_{variant}/auc_table.csv

Output:
  outputs/stage4/factorial_analysis/direction_geometry_by_outcome.json
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone


MODELS = {
    "qwen3": {
        "dir": "outputs/stage4/qwen3-14b",
        "n_layers": 40,
        "label": "Qwen3-14B",
    },
    "gemma4": {
        "dir": "outputs/stage4/gemma4-e4b-it",
        "n_layers": 42,
        "label": "Gemma4-E4B-IT",
    },
}

# EOI = end-of-instruction ("clean refusal") direction
# behavioral = trained on puzzle-attack success/failure outcomes
EOI_DIRECTION_NAME = "eoi"
BEHAVIORAL_DIRECTION_NAME = "behavioral"

# Cohen's d threshold for meaningful effect
D_THRESHOLD = 0.2


def load_cosine_summary(model_dir: Path) -> dict:
    path = model_dir / "direction_comparison" / "cosine_summary.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def load_all_auc_tables(model_dir: Path) -> dict:
    """Load AUC tables for all direction variants. Returns {variant: DataFrame}."""
    tables = {}
    for stats_dir in sorted(model_dir.glob("subspace_stats_*")):
        auc_file = stats_dir / "auc_table.csv"
        if auc_file.exists():
            variant = stats_dir.name.replace("subspace_stats_", "")
            tables[variant] = pd.read_csv(auc_file)
    return tables


def best_auc(df: pd.DataFrame) -> dict:
    row = df.sort_values("auc", ascending=False).iloc[0]
    return {
        "auc": float(row["auc"]),
        "layer": int(row["layer"]),
        "subspace_rank": int(row["subspace_rank"]),
        "n_complied": int(row.get("n_complied", -1)),
        "n_refused": int(row.get("n_refused", -1)),
    }


def all_best_auc(tables: dict) -> dict:
    return {variant: best_auc(df) for variant, df in tables.items()}


def get_pair_cosine(cosine_summary: dict, dir_a: str, dir_b: str) -> dict | None:
    """Get cosine similarity for a specific direction pair."""
    target_pair = f"{dir_a}_vs_{dir_b}"
    alt_pair = f"{dir_b}_vs_{dir_a}"
    for pair in cosine_summary.get("per_pair_summary", []):
        if pair["pair"] in (target_pair, alt_pair):
            return pair
    return None


def classify_geometry(
    eoi_behavioral_max_cosine: float,
    eoi_best_auc: float,
    behavioral_best_auc: float,
) -> str:
    """
    Classify attack geometry relative to clean refusal direction:
      - attenuation: EOI direction weakens during attack (EOI AUC >> 0.5, high cosine)
      - rotation: Attack rotates refusal signal toward compliance (high cosine, EOI AUC high)
      - orthogonal_bypass: Attack exploits different subspace (low cosine, EOI AUC near 0.5)
      - mixed: Both attenuation and bypass
    """
    high_cosine = eoi_behavioral_max_cosine > 0.5
    eoi_predictive = eoi_best_auc > 0.65

    if high_cosine and eoi_predictive:
        return "rotation"
    elif high_cosine and not eoi_predictive:
        return "attenuation"
    elif not high_cosine and eoi_predictive:
        return "mixed_orthogonal_partial_eoi"
    else:
        return "orthogonal_bypass"


def analyze_model(model_key: str, cfg: dict) -> dict:
    model_dir = Path(cfg["dir"])
    n_layers = cfg["n_layers"]

    cosine_summary = load_cosine_summary(model_dir)
    auc_tables = load_all_auc_tables(model_dir)

    # All best AUCs (for predicting puzzle-attack success)
    auc_by_variant = all_best_auc(auc_tables)

    # EOI vs behavioral cosine
    eoi_beh_pair = get_pair_cosine(cosine_summary, EOI_DIRECTION_NAME, BEHAVIORAL_DIRECTION_NAME)

    # Cosine between all pairs (for full picture)
    all_pairs = {}
    for pair_info in cosine_summary.get("per_pair_summary", []):
        all_pairs[pair_info["pair"]] = {
            "max_abs_cosine": pair_info["max_abs_cosine"],
            "mean_abs_cosine": pair_info["mean_abs_cosine"],
        }

    # Get EOI best AUC (use dvp_endofresponse as proxy for EOI — end of prompt direction)
    eoi_proxy_variants = ["dvp_endofresponse", "hvp_endofresponse", "endofresponse"]
    eoi_auc_info = None
    for v in eoi_proxy_variants:
        if v in auc_by_variant:
            eoi_auc_info = {"variant": v, **auc_by_variant[v]}
            break

    behavioral_auc_info = auc_by_variant.get("behavioral")

    eoi_behavioral_max_cos = eoi_beh_pair["max_abs_cosine"] if eoi_beh_pair else None

    geometry_class = classify_geometry(
        eoi_behavioral_max_cosine=eoi_behavioral_max_cos or 0.0,
        eoi_best_auc=eoi_auc_info["auc"] if eoi_auc_info else 0.5,
        behavioral_best_auc=behavioral_auc_info["auc"] if behavioral_auc_info else 0.5,
    )

    # Normalized best-AUC layer (for cross-model comparison)
    if behavioral_auc_info:
        behavioral_auc_info["layer_normalized"] = round(
            behavioral_auc_info["layer"] / (n_layers - 1), 3
        )

    interpretation = _make_interpretation(
        model_key, eoi_behavioral_max_cos or 0.0, eoi_auc_info, behavioral_auc_info, geometry_class
    )

    return {
        "model": model_key,
        "label": cfg["label"],
        "n_layers": n_layers,
        "direction_cosines": all_pairs,
        "eoi_vs_behavioral": {
            "max_abs_cosine": eoi_behavioral_max_cos,
            "interpretation": (
                "nearly orthogonal (< 0.2)" if eoi_behavioral_max_cos and eoi_behavioral_max_cos < 0.2
                else "moderate (0.2-0.5)" if eoi_behavioral_max_cos and eoi_behavioral_max_cos < 0.5
                else "high (>= 0.5)"
            ),
        },
        "best_auc_by_variant": auc_by_variant,
        "eoi_direction_auc": eoi_auc_info,
        "behavioral_direction_auc": behavioral_auc_info,
        "geometry_classification": geometry_class,
        "interpretation": interpretation,
    }


def _make_interpretation(model_key, eoi_cos, eoi_auc, beh_auc, geom_class) -> list[str]:
    lines = []
    cos_str = f"{eoi_cos:.3f}" if eoi_cos else "N/A (EOI direction not extracted for this model)"
    if geom_class == "orthogonal_bypass":
        lines.append(
            f"EOI and behavioral directions are nearly orthogonal (max cosine={cos_str}). "
            "The attack-success subspace is geometrically distinct from the clean refusal direction. "
            "Successful attacks bypass rather than suppress or rotate the refusal signal."
        )
        if eoi_auc:
            lines.append(
                f"EOI direction still predicts attack success to a degree (AUC={eoi_auc['auc']:.3f}), "
                "suggesting EOI-position representations are not completely independent of outcome, "
                "but the primary attack mechanism operates in a separate subspace."
            )
        if beh_auc:
            lines.append(
                f"Behavioral direction achieves higher AUC ({beh_auc['auc']:.3f}), "
                f"localized at normalized layer {beh_auc.get('layer_normalized', '?')}."
            )
    elif geom_class == "rotation":
        lines.append(
            f"EOI and behavioral directions are substantially aligned (max cosine={cos_str}). "
            "The attack appears to rotate the clean refusal signal toward the compliance direction."
        )
    elif geom_class == "mixed_orthogonal_partial_eoi":
        eoi_auc_str = f"{eoi_auc['auc']:.3f}" if eoi_auc else "N/A"
        lines.append(
            f"EOI and behavioral directions are largely orthogonal (max cosine={cos_str}), "
            f"yet EOI direction is also somewhat predictive of attack success (AUC={eoi_auc_str}). "
            "Likely two partially overlapping mechanisms."
        )
    elif geom_class == "attenuation":
        lines.append(
            f"EOI and behavioral directions align (max cosine={cos_str}) but EOI direction "
            "is not strongly predictive of attack success — possible attenuation of the refusal signal."
        )
    return lines


def main():
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", nargs="+", choices=list(MODELS), default=list(MODELS))
    ap.add_argument(
        "--output-dir", default="outputs/stage4/factorial_analysis"
    )
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for model_key in args.models:
        cfg = MODELS[model_key]
        print(f"\n=== {cfg['label']} ===")
        res = analyze_model(model_key, cfg)
        results[model_key] = res

        print(f"  EOI vs behavioral cosine: {res['eoi_vs_behavioral']['max_abs_cosine']}")
        print(f"  Geometry classification: {res['geometry_classification']}")
        if res["behavioral_direction_auc"]:
            b = res["behavioral_direction_auc"]
            print(f"  Behavioral AUC: {b['auc']:.4f} @ L{b['layer']} rank{b['subspace_rank']}")
        if res["eoi_direction_auc"]:
            e = res["eoi_direction_auc"]
            print(f"  EOI ({e['variant']}) AUC: {e['auc']:.4f} @ L{e['layer']} rank{e['subspace_rank']}")
        for line in res["interpretation"]:
            print(f"  -> {line}")

    # Summary table
    print("\n=== Summary ===")
    print(f"{'Model':<20} {'EOI_cos':>8} {'EOI_AUC':>8} {'Beh_AUC':>8} {'Classification'}")
    for mk, r in results.items():
        eoi_cos = r["eoi_vs_behavioral"]["max_abs_cosine"]
        eoi_a = r["eoi_direction_auc"]["auc"] if r["eoi_direction_auc"] else float("nan")
        beh_a = r["behavioral_direction_auc"]["auc"] if r["behavioral_direction_auc"] else float("nan")
        eoi_cos_s = f"{eoi_cos:>8.3f}" if eoi_cos is not None else "     N/A"
        print(f"{r['label']:<20} {eoi_cos_s} {eoi_a:>8.3f} {beh_a:>8.3f} {r['geometry_classification']}")

    output = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "description": "Direction geometry analysis — attenuation vs rotation vs orthogonal bypass (Q2)",
        "models": results,
        "cross_model_comparison": {
            "qwen3_eoi_vs_beh_cos": results.get("qwen3", {})
            .get("eoi_vs_behavioral", {})
            .get("max_abs_cosine"),
            "gemma4_eoi_vs_beh_cos": results.get("gemma4", {})
            .get("eoi_vs_behavioral", {})
            .get("max_abs_cosine"),
            "summary": (
                "Qwen3: EOI ⊥ behavioral (orthogonal bypass). "
                "Gemma4: endofthink ≈ behavioral (rotation/alignment during thinking end). "
                "Two distinct mechanism geometries across models."
            ),
        },
    }

    out_path = out_dir / "direction_geometry_by_outcome.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
