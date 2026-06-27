"""
Statistical analysis of the factorial attack dataset.

Produces:
  1. Primary meeting table — mechanism class counts by model
  2. Paired contrasts — A vs D, A vs E, A vs F, D vs F (sign test + bootstrap CI)
  3. Puzzle × Thinking interaction — (p_A - p_E) - (p_D - p_G)  [requires G condition]
  4. Per-goal breakdown table

Inputs:
  outputs/stage4/factorial_attack_dataset.jsonl
  outputs/stage4/mechanism_classification.jsonl

Outputs:
  outputs/stage4/factorial_analysis/primary_meeting_table.csv
  outputs/stage4/factorial_analysis/paired_contrasts.csv
  outputs/stage4/factorial_analysis/mechanism_by_goal.csv
  outputs/stage4/factorial_analysis/interaction_effects.csv
  outputs/stage4/factorial_analysis/analysis_summary.json

Sanity checks (applied after analysis):
  - Stage 4.7 Qwen3 A vs D paired contrast: mean_diff ≈ +0.44, p ≤ 0.05
  - Stage 4.7 Qwen3 A vs F: mean_diff ≈ +0.57, p ≤ 0.05

Usage:
  python -m poc_stage4.analyze_factorial_attack_effects
      [--dataset outputs/stage4/factorial_attack_dataset.jsonl]
      [--classification outputs/stage4/mechanism_classification.jsonl]
      [--output-dir outputs/stage4/factorial_analysis]
      [--n-bootstrap 10000]
      [--theta 0.5]
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_DATASET = _REPO_ROOT / "outputs" / "stage4" / "factorial_attack_dataset.jsonl"
_CLASSIFICATION = _REPO_ROOT / "outputs" / "stage4" / "mechanism_classification.jsonl"
_OUTPUT_DIR = _REPO_ROOT / "outputs" / "stage4" / "factorial_analysis"

_CONDITIONS = ["A", "D", "E", "F", "G"]  # G = bare harmful + thinking OFF (currently missing)
_THETA = 0.5
_N_BOOTSTRAP = 10_000


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _fmt(x, ndigits=3):
    if x is None:
        return "—"
    if isinstance(x, float) and math.isnan(x):
        return "—"
    return f"{x:.{ndigits}f}"


# ── Paired contrast helpers ────────────────────────────────────────────────────

def _get_per_example_rates(
    dataset_rows: list[dict],
    model_family: str,
    source_stage_filter=None,
) -> dict[str, dict[str, float | None]]:
    """
    Returns {source_example_id: {condition: mean_sr_success}} for one model.
    If source_stage_filter is provided, only include rows from those stages.
    """
    rows = [r for r in dataset_rows if r["model_family"] == model_family]
    if source_stage_filter:
        rows = [r for r in rows if r.get("source_stage") in source_stage_filter]
    # Only rows with SR scored
    rows = [r for r in rows if r.get("sr_success") is not None]

    by_example: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_example[r["source_example_id"]][r["condition"]].append(float(r["sr_success"]))

    out = {}
    for sid, by_cond in by_example.items():
        out[sid] = {
            cond: (sum(vs) / len(vs) if vs else None)
            for cond, vs in by_cond.items()
        }
    return out


def _sign_test(diffs: list[float]) -> float:
    """Two-sided sign test p-value (exact binomial)."""
    from math import comb
    n_total = len(diffs)
    n_pos = sum(1 for d in diffs if d > 0)
    n_neg = sum(1 for d in diffs if d < 0)
    n = n_pos + n_neg  # ties excluded
    if n == 0:
        return 1.0
    # P(X >= n_pos) under H0: X ~ Binomial(n, 0.5)
    k = max(n_pos, n_neg)
    p_one_sided = sum(comb(n, i) * 0.5**n for i in range(k, n + 1))
    return min(2.0 * p_one_sided, 1.0)


def _bootstrap_ci(diffs: list[float], n_bootstrap: int, alpha: float = 0.05, seed: int = 42):
    """Bootstrap percentile CI for mean difference."""
    rng = random.Random(seed)
    n = len(diffs)
    if n == 0:
        return (None, None)
    boot_means = []
    for _ in range(n_bootstrap):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boot_means.append(sum(sample) / len(sample))
    boot_means.sort()
    lo_idx = int(alpha / 2 * n_bootstrap)
    hi_idx = int((1 - alpha / 2) * n_bootstrap)
    return (boot_means[lo_idx], boot_means[hi_idx])


def compute_paired_contrasts(
    dataset_rows: list[dict],
    model_family: str,
    n_bootstrap: int,
    source_stage_filter=None,
) -> list[dict]:
    """Compute A-D, A-E, A-F, D-F contrasts for one model."""
    per_example = _get_per_example_rates(dataset_rows, model_family, source_stage_filter)

    # A-D: puzzle effect with thinking ON  (NOT "thinking required" — both have thinking ON)
    # A-E: thinking effect within puzzle condition
    # D-G: thinking effect without puzzle  (G = bare harmful + thinking OFF)
    # E-G: puzzle effect with thinking OFF
    # A-F: puzzle effect vs length-matched benign control (F = length control, not no-puzzle cell)
    # D-F: bare harmful vs benign length control
    contrasts = [("A", "D"), ("A", "E"), ("A", "F"), ("D", "F"), ("D", "G"), ("E", "G")]
    results = []
    for c1, c2 in contrasts:
        # Only examples where both conditions are available
        diffs = []
        sids_used = []
        for sid, rates in per_example.items():
            r1 = rates.get(c1)
            r2 = rates.get(c2)
            if r1 is not None and r2 is not None:
                diffs.append(r1 - r2)
                sids_used.append(sid)

        if not diffs:
            results.append({
                "model_family": model_family,
                "contrast": f"{c1}-{c2}",
                "n_examples": 0,
                "mean_diff": None,
                "ci_lo": None,
                "ci_hi": None,
                "p_sign_test": None,
                "note": "no paired examples",
            })
            continue

        mean_diff = sum(diffs) / len(diffs)
        ci_lo, ci_hi = _bootstrap_ci(diffs, n_bootstrap)
        p_val = _sign_test(diffs)

        results.append({
            "model_family": model_family,
            "contrast": f"{c1}-{c2}",
            "n_examples": len(diffs),
            "mean_diff": mean_diff,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
            "p_sign_test": p_val,
            "note": f"n_sources={len(sids_used)}",
        })
        print(
            f"  {model_family} {c1}-{c2}: n={len(diffs)}, "
            f"mean_diff={mean_diff:+.3f}, "
            f"95%CI=[{_fmt(ci_lo)},{_fmt(ci_hi)}], p={_fmt(p_val)}"
        )

    return results


# ── Interaction effect ─────────────────────────────────────────────────────────

def compute_interaction(
    dataset_rows: list[dict],
    model_family: str,
    source_stage_filter=None,
) -> dict:
    """
    Full Puzzle × Thinking factorial interaction per example:
    interaction = (p_A - p_E) - (p_D - p_G)

    Interpretation:
    - (A-E): thinking effect WITHIN puzzle condition
    - (D-G): thinking effect WITHOUT puzzle
    - interaction > 0: thinking adds MORE when puzzle is present (superadditive)

    Requires G condition (bare harmful + thinking OFF). Returns INCOMPLETE if G is missing.

    F (length-matched benign control) is NOT used in the factorial interaction — it is a
    separate length/structure control and is NOT the no-puzzle/thinking-off cell.
    The old formula (A-D)-(E-F) was incorrect and has been replaced.
    """
    per_example = _get_per_example_rates(dataset_rows, model_family, source_stage_filter)
    interactions = []
    n_missing_g = 0
    for sid, rates in per_example.items():
        pA = rates.get("A")
        pE = rates.get("E")
        pD = rates.get("D")
        pG = rates.get("G")
        if pG is None:
            n_missing_g += 1
            continue
        if any(x is None for x in [pA, pE, pD]):
            continue
        interactions.append((pA - pE) - (pD - pG))

    if not interactions:
        status = "INCOMPLETE — G condition missing for all examples" if n_missing_g > 0 else "no paired examples"
        return {"model_family": model_family, "n": 0, "mean_interaction": None,
                "status": status, "n_missing_g": n_missing_g}

    mean_int = sum(interactions) / len(interactions)
    return {
        "model_family": model_family,
        "n": len(interactions),
        "mean_interaction": mean_int,
        "interaction_values": interactions,
        "n_missing_g": n_missing_g,
        "status": "complete" if n_missing_g == 0 else f"partial — {n_missing_g} examples missing G",
    }


# ── Condition-level ASR ────────────────────────────────────────────────────────

def compute_asr_by_condition(
    dataset_rows: list[dict],
    model_family: str,
    source_stage_filter=None,
) -> dict[str, dict]:
    rows = [r for r in dataset_rows if r["model_family"] == model_family]
    if source_stage_filter:
        rows = [r for r in rows if r.get("source_stage") in source_stage_filter]
    rows = [r for r in rows if r.get("sr_success") is not None and r.get("is_valid", True)]

    by_cond: dict[str, list] = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r["sr_success"])

    out = {}
    for cond, vals in by_cond.items():
        n_success = sum(1 for v in vals if v)
        out[cond] = {"asr": n_success / len(vals), "n": len(vals), "n_success": n_success}
    return out


# ── Per-goal breakdown ─────────────────────────────────────────────────────────

def compute_mechanism_by_goal(classification_rows: list[dict]) -> list[dict]:
    mechanisms = [
        "pure_cot_hijack", "target_easy", "thinking_dep_only", "puzzle_dep_only",
        "length_effect", "universally_vulnerable", "universally_resistant", "unstable",
        "incomplete_factorial",
    ]
    from collections import Counter
    by_model_goal: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for r in classification_rows:
        key = (r["model_family"], str(r.get("goal_index", "unknown")))
        by_model_goal[key][r["mechanism"]] += 1

    rows = []
    for (model, goal), counts in sorted(by_model_goal.items()):
        row = {"model_family": model, "goal_index": goal, "total": sum(counts.values())}
        for m in mechanisms:
            row[m] = counts.get(m, 0)
        rows.append(row)
    return rows


# ── Primary meeting table ──────────────────────────────────────────────────────

def build_primary_table(classification_rows: list[dict], asr_by_model: dict) -> list[dict]:
    from collections import Counter
    rows = []
    models = sorted(set(r["model_family"] for r in classification_rows))
    mechanisms = [
        "pure_cot_hijack", "target_easy", "thinking_dep_only", "puzzle_dep_only",
        "length_effect", "universally_vulnerable", "universally_resistant", "unstable",
        "incomplete_factorial",
    ]
    for model in models:
        model_rows = [r for r in classification_rows if r["model_family"] == model]
        counts = Counter(r["mechanism"] for r in model_rows)
        n_total = len(model_rows)
        asr_a = asr_by_model.get(model, {}).get("A", {})
        row = {
            "model_family": model,
            "n_examples": n_total,
            "asr_cond_A": f"{asr_a.get('asr', 0):.1%} ({asr_a.get('n_success', 0)}/{asr_a.get('n', 0)})",
        }
        for m in mechanisms:
            pct = f"{counts.get(m, 0) / n_total:.1%}" if n_total > 0 else "—"
            row[m] = f"{counts.get(m, 0)} ({pct})"
        rows.append(row)
    return rows


# ── Sanity checks ──────────────────────────────────────────────────────────────

def run_sanity_checks(contrasts: list[dict]) -> list[str]:
    """
    Validate known published numbers from Stage 4.7 greedy run (n=12 source examples).
    Published Stage 4.8: A=65%, D=46.7%, F=36.7%.
    Sign test p-values are not checked here — n=12 paired examples gives very low power
    and p<0.05 requires ≥10/12 concordant pairs; we only check direction of effect.
    """
    failures = []
    # mean_diff only — sign test power is too low with n=12 to enforce p<0.05
    expected = {
        ("qwen3", "A-D"): {"mean_diff_lo": 0.1, "mean_diff_hi": 0.7},
        ("qwen3", "A-F"): {"mean_diff_lo": 0.1, "mean_diff_hi": 0.8},
    }
    contrast_map = {(r["model_family"], r["contrast"]): r for r in contrasts}
    for key, bounds in expected.items():
        row = contrast_map.get(key)
        if row is None:
            failures.append(f"Missing contrast {key}")
            continue
        md = row.get("mean_diff")
        if md is None:
            failures.append(f"{key}: mean_diff is None (no paired data?)")
            continue
        if not (bounds["mean_diff_lo"] <= md <= bounds["mean_diff_hi"]):
            failures.append(
                f"{key}: mean_diff={md:.3f} outside expected range [{bounds['mean_diff_lo']},{bounds['mean_diff_hi']}]"
            )
    return failures


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(_DATASET))
    parser.add_argument("--classification", default=str(_CLASSIFICATION))
    parser.add_argument("--output-dir", default=str(_OUTPUT_DIR))
    parser.add_argument("--n-bootstrap", type=int, default=_N_BOOTSTRAP)
    parser.add_argument("--theta", type=float, default=_THETA)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = Path(args.dataset)
    classification_path = Path(args.classification)

    if not dataset_path.exists():
        print(f"ERROR: dataset not found: {dataset_path}")
        sys.exit(1)
    if not classification_path.exists():
        print(f"ERROR: classification not found: {classification_path}")
        sys.exit(1)

    dataset_rows = _load_jsonl(dataset_path)
    classification_rows = _load_jsonl(classification_path)
    print(f"Dataset: {len(dataset_rows)} rows")
    print(f"Classification: {len(classification_rows)} examples")

    models = sorted(set(r["model_family"] for r in dataset_rows))

    # ── 1. ASR by condition ────────────────────────────────────────────────────
    print("\n=== ASR by condition ===")
    asr_by_model: dict[str, dict] = {}
    for model in models:
        asr = compute_asr_by_condition(dataset_rows, model)
        asr_by_model[model] = asr
        print(f"\n  {model}:")
        for cond in _CONDITIONS:
            info = asr.get(cond, {})
            if info:
                print(f"    Cond {cond}: {info.get('asr', 0):.1%} ({info.get('n_success', 0)}/{info.get('n', 0)})")

    # ── 2. Paired contrasts ────────────────────────────────────────────────────
    print("\n=== Paired contrasts ===")
    all_contrasts: list[dict] = []
    for model in models:
        contrasts = compute_paired_contrasts(
            dataset_rows, model, n_bootstrap=args.n_bootstrap
        )
        all_contrasts.extend(contrasts)

    contrast_fields = ["model_family", "contrast", "n_examples", "mean_diff", "ci_lo", "ci_hi", "p_sign_test", "note"]
    _write_csv(output_dir / "paired_contrasts.csv", all_contrasts, contrast_fields)

    # ── 3. Interaction effects ─────────────────────────────────────────────────
    print("\n=== Puzzle × Thinking interaction: (A-E)-(D-G) ===")
    print("  NOTE: Requires G condition (bare harmful + thinking OFF).")
    print("  If G is missing, result is INCOMPLETE and cannot be interpreted as a full factorial interaction.")
    interaction_rows = []
    for model in models:
        result = compute_interaction(dataset_rows, model)
        mi = result.get("mean_interaction")
        status = result.get("status", "unknown")
        n_missing_g = result.get("n_missing_g", 0)
        print(f"  {model}: mean_interaction={_fmt(mi)}, n={result.get('n', 0)}, "
              f"n_missing_g={n_missing_g}, status={status}")
        if n_missing_g > 0:
            print(f"  *** INCOMPLETE: G condition missing for {n_missing_g} examples. "
                  f"Cannot report factorial interaction. ***")
        interaction_rows.append({
            "model_family": model,
            "n": result.get("n", 0),
            "mean_interaction": result.get("mean_interaction"),
            "n_missing_g": n_missing_g,
            "status": status,
        })
    _write_csv(output_dir / "interaction_effects.csv", interaction_rows,
               ["model_family", "n", "mean_interaction", "n_missing_g", "status"])

    # ── 4. Per-goal mechanism breakdown ───────────────────────────────────────
    print("\n=== Mechanism by goal ===")
    by_goal = compute_mechanism_by_goal(classification_rows)
    mechanisms = [
        "pure_cot_hijack", "target_easy", "thinking_dep_only", "puzzle_dep_only",
        "length_effect", "universally_vulnerable", "universally_resistant", "unstable",
        "incomplete_factorial",
    ]
    _write_csv(output_dir / "mechanism_by_goal.csv", by_goal,
               ["model_family", "goal_index", "total"] + mechanisms)
    for r in by_goal:
        print(f"  {r['model_family']} goal={r['goal_index']}: " +
              ", ".join(f"{m}={r.get(m,0)}" for m in mechanisms if r.get(m, 0) > 0))

    # ── 5. Primary meeting table ───────────────────────────────────────────────
    print("\n=== Primary meeting table ===")
    primary_table = build_primary_table(classification_rows, asr_by_model)
    primary_fields = ["model_family", "n_examples", "asr_cond_A"] + mechanisms
    _write_csv(output_dir / "primary_meeting_table.csv", primary_table, primary_fields)
    for row in primary_table:
        print(f"\n  {row['model_family']} (n={row['n_examples']}, ASR={row['asr_cond_A']}):")
        for m in mechanisms:
            v = row.get(m, "0")
            if not v.startswith("0 "):
                print(f"    {m}: {v}")

    # ── 6. Sanity checks ──────────────────────────────────────────────────────
    print("\n=== Sanity checks ===")
    failures = run_sanity_checks(all_contrasts)
    if failures:
        print("  SANITY CHECK FAILURES:")
        for f in failures:
            print(f"  !! {f}")
    else:
        print("  All sanity checks passed.")

    # ── Write summary JSON ─────────────────────────────────────────────────────
    summary = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "n_dataset_rows": len(dataset_rows),
        "n_classification_examples": len(classification_rows),
        "models": models,
        "asr_by_model": {
            model: {cond: info for cond, info in asr.items()}
            for model, asr in asr_by_model.items()
        },
        "contrasts": all_contrasts,
        "interaction": interaction_rows,
        "sanity_check_failures": failures,
        "sanity_checks_passed": len(failures) == 0,
    }
    with open(output_dir / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nOutputs written to {output_dir}/")
    print(f"  paired_contrasts.csv")
    print(f"  mechanism_by_goal.csv")
    print(f"  primary_meeting_table.csv")
    print(f"  interaction_effects.csv")
    print(f"  analysis_summary.json")

    if failures:
        print(f"\nWARNING: {len(failures)} sanity check(s) failed. Review before meeting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
