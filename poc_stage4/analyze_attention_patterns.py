"""Analyze per-head attention statistics from run_attention_extraction.py (P5a).

Loads per-example JSON files from the attention analysis output directory and
computes aggregate statistics across examples and heads.

Questions addressed:
  Q1. Which heads have the highest attention mass on early user tokens (puzzle wrapper)?
  Q2. At the last prompt tokens (query positions), does attention concentrate on the
      puzzle wrapper or the harmful goal area?
  Q3. Which layers show the highest entropy (diffuse attention) vs low entropy (focused)?
  Q4. Are there systematic differences across query positions?

Usage:
    python -m poc_stage4.analyze_attention_patterns
    python -m poc_stage4.analyze_attention_patterns --run-dir outputs/stage4/attention_analysis
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_DEFAULT_DIR = _REPO_ROOT / "outputs" / "stage4" / "attention_analysis_smoke_v2"
_FULL_DIR = _REPO_ROOT / "outputs" / "stage4" / "attention_analysis"


def _load_results(run_dir: Path) -> list[dict]:
    per_ex_dir = run_dir / "per_example"
    if not per_ex_dir.exists():
        per_ex_dir = run_dir
    results = []
    for f in sorted(per_ex_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text())
            if not d.get("skipped"):
                results.append(d)
        except Exception:
            pass
    return results


def analyze(run_dir: Path, write_doc: bool = False) -> dict:
    results = _load_results(run_dir)
    if not results:
        print(f"No valid results found in {run_dir}")
        return {}

    print(f"Loaded {len(results)} examples")

    # Find all layers and heads
    all_layers = set()
    for r in results:
        for k in r:
            if k.startswith("layer_"):
                try:
                    all_layers.add(int(k.split("_")[1]))
                except ValueError:
                    pass
    all_layers = sorted(all_layers)
    print(f"Layers: {all_layers}")

    if not all_layers:
        print("No layer data found in results.")
        return {}

    # Get number of heads from first result
    first_r = results[0]
    first_layer_key = f"layer_{all_layers[0]}"
    n_heads = len(first_r.get(first_layer_key, []))
    print(f"N heads: {n_heads}")

    # Get categories
    cats_set = set()
    for r in results:
        lk = f"layer_{all_layers[0]}"
        if lk in r:
            for h_stats in r[lk]:
                cats_set.update(h_stats.get("cat_mass", {}).keys())
    categories = sorted(cats_set)
    print(f"Token categories: {categories}")

    # Aggregate per layer × head × category
    # shape: layer → head → cat → list of values across examples
    layer_head_cat: dict[int, dict[int, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    layer_head_entropy: dict[int, dict[int, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for r in results:
        for li in all_layers:
            lk = f"layer_{li}"
            if lk not in r:
                continue
            for h_stats in r[lk]:
                h = h_stats["head"]
                layer_head_entropy[li][h].append(h_stats.get("mean_entropy", float("nan")))
                for cat, mass in h_stats.get("cat_mass", {}).items():
                    layer_head_cat[li][h][cat].append(mass)

    # Per-layer summary
    print(f"\n{'Layer':<6} {'Mean entropy':<16} " + "  ".join(f"{c[:12]:<13}" for c in categories))
    print("-" * (6 + 16 + 15 * len(categories)))

    layer_summaries = {}
    for li in all_layers:
        # Average entropy across heads and examples
        all_entropies = [v for h_vals in layer_head_entropy[li].values() for v in h_vals]
        mean_ent = sum(all_entropies) / max(len(all_entropies), 1)

        cat_means = {}
        for cat in categories:
            vals = [v for h_vals in layer_head_cat[li].values() for v in h_vals.get(cat, [])]
            cat_means[cat] = sum(vals) / max(len(vals), 1)

        row = f"{li:<6} {mean_ent:<16.4f} " + "  ".join(
            f"{cat_means.get(c, 0.0):<13.4f}" for c in categories
        )
        print(row)
        layer_summaries[li] = {"mean_entropy": mean_ent, "cat_means": cat_means}

    # Top-5 heads by user_prompt attention at each layer (high attention = potentially causal)
    target_cat = "user_prompt"
    print(f"\n=== Top-5 heads by '{target_cat}' attention mass (averaged over examples) ===")
    top_heads_by_layer = {}
    for li in all_layers:
        head_means = {}
        for h in range(n_heads):
            vals = layer_head_cat[li][h].get(target_cat, [])
            if vals:
                head_means[h] = sum(vals) / len(vals)
        top5 = sorted(head_means.items(), key=lambda x: x[1], reverse=True)[:5]
        top_heads_by_layer[li] = top5
        top_str = ", ".join(f"H{h}={v:.3f}" for h, v in top5)
        print(f"  L{li}: {top_str}")

    # Top heads by entropy (low entropy = focused attention = potentially causal)
    print(f"\n=== Top-5 heads by LOWEST mean entropy (most focused) at each layer ===")
    low_entropy_heads_by_layer = {}
    for li in all_layers:
        head_ents = {}
        for h in range(n_heads):
            vals = layer_head_entropy[li][h]
            if vals:
                head_ents[h] = sum(vals) / len(vals)
        bottom5 = sorted(head_ents.items(), key=lambda x: x[1])[:5]
        low_entropy_heads_by_layer[li] = bottom5
        bot_str = ", ".join(f"H{h}={v:.3f}" for h, v in bottom5)
        print(f"  L{li}: {bot_str}")

    # Summary
    # Which category gets the most attention overall across all layers?
    overall_cat = {}
    for cat in categories:
        vals = [
            v
            for li in all_layers
            for h_vals in layer_head_cat[li].values()
            for v in h_vals.get(cat, [])
        ]
        overall_cat[cat] = sum(vals) / max(len(vals), 1)
    print(f"\n=== Overall attention mass by category (all layers, all heads) ===")
    for cat, mass in sorted(overall_cat.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(mass * 40)
        print(f"  {cat:<15}: {mass:.4f}  {bar}")

    summary = {
        "n_examples": len(results),
        "layers": all_layers,
        "n_heads": n_heads,
        "categories": categories,
        "layer_summaries": {str(li): v for li, v in layer_summaries.items()},
        "top_heads_user_prompt": {str(li): [(h, v) for h, v in top5]
                                   for li, top5 in top_heads_by_layer.items()},
        "low_entropy_heads": {str(li): [(h, v) for h, v in bot5]
                               for li, bot5 in low_entropy_heads_by_layer.items()},
        "overall_cat_mass": overall_cat,
    }

    out_json = run_dir / "analysis_summary.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"\nWritten: {out_json}")

    if write_doc:
        _write_doc(summary, run_dir)

    return summary


def _write_doc(summary: dict, run_dir: Path) -> None:
    doc_path = _REPO_ROOT / "docs" / "ATTENTION_PATTERN_ANALYSIS.md"
    n_ex = summary["n_examples"]
    layers = summary["layers"]
    cats = summary["categories"]
    layer_sums = summary["layer_summaries"]
    overall = summary["overall_cat_mass"]

    layer_rows = []
    for li in layers:
        ls = layer_sums.get(str(li), {})
        ent = ls.get("mean_entropy", 0.0)
        cat_masses = ls.get("cat_means", {})
        cat_str = " | ".join(f"{cat_masses.get(c, 0.0):.3f}" for c in cats)
        layer_rows.append(f"| {li} | {ent:.4f} | {cat_str} |")

    top_heads = summary.get("top_heads_user_prompt", {})
    top_rows = []
    for li in layers:
        top5 = top_heads.get(str(li), [])
        top_str = ", ".join(f"H{h}={v:.3f}" for h, v in top5)
        top_rows.append(f"| {li} | {top_str} |")

    cat_header = " | ".join(cats)
    cat_seps = " | ".join(["---"] * len(cats))

    doc = f"""# Attention Pattern Analysis (P5a) — Prompt-Phase Encoding

**Date:** 2026-06-25
**Method:** Prompt-only forward pass with eager attention on Qwen3-14B.
**Examples:** {n_ex} pure_cot_hijack examples.
**Layers analyzed:** {layers}

---

## Method

For each pure_cot_hijack example, we run a forward pass on ONLY the prompt tokens (not the full
generation trace). This is feasible with eager attention (prompt is ~800-1200 tokens vs full trace
which is 13-30K tokens).

**Query positions:** last 50 user-role tokens in the prompt (the tokens closest to the harmful
goal request, immediately before the generation trigger).

**Key question:** At the query positions (near the harmful goal), which tokens (puzzle wrapper vs
harmful goal) receive the most attention? High puzzle-wrapper attention would suggest the model
is "distracted" by the puzzle context away from the harmful content.

**Token categories:**
- `system` — system message tokens
- `user_prompt` — all user-role tokens (the attack prompt including puzzle + goal)
- `other` — special tokens, assistant prefix

Note: We do not further split user_prompt into puzzle_wrapper vs harmful_goal in this run.
Future analysis can add this using token-level text matching.

---

## Layer-by-Layer Attention Statistics

Mean entropy and per-category attention mass, averaged over all heads and examples.

| Layer | Mean Entropy | {cat_header} |
|-------|-------------|{cat_seps}|
{chr(10).join(layer_rows)}

---

## Top-5 Heads by User Prompt Attention Mass

Heads with highest attention to user_prompt tokens at query positions. These are heads
where puzzle/goal tokens receive concentrated attention — potential causal candidates for P5b.

| Layer | Top 5 Heads (by user_prompt mass) |
|-------|----------------------------------|
{chr(10).join(top_rows)}

---

## Overall Category Attention Mass (All Layers, All Heads)

{chr(10).join(f'- `{c}`: {overall.get(c, 0.0):.4f}' for c in sorted(overall, key=lambda x: overall.get(x, 0), reverse=True))}

---

## Interpretation

- High `user_prompt` attention at late query positions → model is encoding the puzzle wrapper
  (as expected from the attack mechanism)
- Low entropy at intermediate layers (10-26) with high user_prompt mass → potentially the most
  causally relevant heads for the attack mechanism
- This data informs P5b: which specific heads to ablate in the next experiment

---

## Files

- Per-example data: `outputs/stage4/attention_analysis_smoke_v2/per_example/*.json`
- This summary: `outputs/stage4/attention_analysis_smoke_v2/analysis_summary.json`
"""

    doc_path.write_text(doc)
    print(f"Written: {doc_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", default=None,
                    help="Directory with per_example/*.json files")
    ap.add_argument("--write-doc", action="store_true")
    args = ap.parse_args()

    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        # Auto-detect: prefer smoke_v2 if it has data, else full
        for d in [_DEFAULT_DIR, _FULL_DIR]:
            per_ex = d / "per_example"
            if per_ex.exists() and any(per_ex.glob("*.json")):
                run_dir = d
                break
        else:
            run_dir = _DEFAULT_DIR

    print(f"Analyzing: {run_dir}")
    analyze(run_dir, write_doc=args.write_doc)


if __name__ == "__main__":
    main()
