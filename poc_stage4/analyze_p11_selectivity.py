"""analyze_p11_selectivity.py

Analyzes the P11 controlled-patching selectivity pilot results.

Reads outputs/stage4/p11_controlled_patching/run_*/results.jsonl and computes:
  - Per-condition ASR (attack success rate) across sources × layers
  - Control pass/fail summary (identity, sham must preserve attack)
  - Specificity assessment: does random/harmless/mean also suppress?
  - Sufficiency: does a_to_d (patching D with A activations) make D succeed?
  - Layer × condition heatmap values

Writes: docs/P11_SELECTIVITY_AND_SUFFICIENCY_RESULTS.md
        outputs/stage4/p11_controlled_patching/selectivity_summary.json

Usage:
    python -m poc_stage4.analyze_p11_selectivity [--run-dir <path>] [--partial]

  --partial: allow analysis on incomplete results (less than full n×layers×conditions)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

_REPO = Path(__file__).parent.parent
_DEFAULT_BASE = _REPO / "outputs" / "stage4" / "p11_controlled_patching"
_DOCS = _REPO / "docs"

# Expected conditions (order matters for display)
_CONDITION_GROUPS = {
    "primary": ["patch_D_full"],
    "null_controls": ["identity", "sham"],
    "specificity_controls": ["random_norm", "harmless", "mean_activation", "a_cross_source"],
    "cross_conditions": ["d_cross_source"],
    "sufficiency": ["a_to_d"],
    "baselines": ["baseline_A", "baseline_D"],
}
_ALL_CONDITIONS = (
    ["baseline_A", "baseline_D", "patch_D_full", "identity", "sham"]
    + ["a_cross_source", "d_cross_source", "random_norm", "harmless", "mean_activation", "a_to_d"]
)

# For the "attack suppressed" interpretation: after patching, attack goes from True→False
# For a_to_d (sufficiency): after patching D with A activations, attack goes from False→True
_INTERPRETATION = {
    "patch_D_full": "suppresses_if_false",     # should be False (causal claim)
    "identity":     "preserves_if_true",        # should be True (control)
    "sham":         "preserves_if_true",        # should be True (control)
    "random_norm":  "no_suppress_if_true",      # should be True (not specific)
    "harmless":     "no_suppress_if_true",      # should be True (not specific)
    "mean_activation": "no_suppress_if_true",   # should be True (not specific)
    "a_cross_source": "no_suppress_if_true",    # should be True (own-goal A doesn't suppress)
    "d_cross_source": "suppresses_if_false",    # should be False (other D also suppresses)
    "a_to_d":       "sufficiency_if_true",      # D with A activations — does it now succeed?
}


def load_results(run_dir: Path) -> list[dict]:
    path = run_dir / "results.jsonl"
    if not path.exists():
        return []
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def compute_asr_table(rows: list[dict]) -> dict:
    """Compute per-condition per-layer ASR."""
    # {(condition, layer): [success, success, ...]}
    data: dict[tuple, list[bool]] = defaultdict(list)
    for r in rows:
        cond = r.get("condition", "")
        layer = r.get("layer_patched")
        success = r.get("sr_success", False)
        data[(cond, layer)].append(bool(success))

    asr_table: dict[tuple, dict] = {}
    for (cond, layer), successes in data.items():
        n = len(successes)
        asr = sum(successes) / n if n > 0 else None
        asr_table[(cond, layer)] = {"n": n, "asr": asr, "successes": sum(successes)}
    return asr_table


def classify_condition_result(cond: str, asr: float | None, n: int) -> str:
    """Human-readable interpretation of a condition's ASR."""
    if asr is None or n == 0:
        return "NO DATA"
    interp = _INTERPRETATION.get(cond, "")
    if interp == "suppresses_if_false":
        return "SUPPRESSED ✓" if asr < 0.3 else ("PARTIAL" if asr < 0.7 else "NO EFFECT")
    elif interp == "preserves_if_true":
        return "CONTROL PASS ✓" if asr >= 0.7 else "CONTROL FAIL ✗"
    elif interp == "no_suppress_if_true":
        return "SPECIFIC ✓" if asr >= 0.7 else "NONSPECIFIC ✗"
    elif interp == "sufficiency_if_true":
        return "SUFFICIENT ✓" if asr >= 0.5 else "NOT SUFFICIENT"
    return f"ASR={asr:.2f}"


def build_selectivity_verdict(asr_table: dict) -> dict:
    """Summarize whether selectivity criteria are met."""
    # Average across layers for each condition
    cond_asr: dict[str, list[float]] = defaultdict(list)
    for (cond, layer), vals in asr_table.items():
        if layer is None:
            continue  # baselines
        if vals["asr"] is not None:
            cond_asr[cond].append(vals["asr"])

    avg_asr = {c: (sum(v) / len(v)) if v else None for c, v in cond_asr.items()}

    # Baselines (no layer)
    baseline_A_asr = None
    baseline_D_asr = None
    for (cond, layer), vals in asr_table.items():
        if layer is None:
            if cond == "baseline_A":
                baseline_A_asr = vals["asr"]
            elif cond == "baseline_D":
                baseline_D_asr = vals["asr"]

    # Criteria for P11 selectivity (all must hold)
    criteria = {}
    criteria["patch_D_full_suppresses"] = avg_asr.get("patch_D_full") is not None and avg_asr["patch_D_full"] < 0.3
    criteria["identity_preserves"] = avg_asr.get("identity") is not None and avg_asr["identity"] >= 0.7
    criteria["sham_preserves"] = avg_asr.get("sham") is not None and avg_asr["sham"] >= 0.7
    criteria["random_norm_doesnt_suppress"] = avg_asr.get("random_norm") is not None and avg_asr["random_norm"] >= 0.7
    criteria["harmless_doesnt_suppress"] = avg_asr.get("harmless") is not None and avg_asr["harmless"] >= 0.7
    criteria["mean_doesnt_suppress"] = avg_asr.get("mean_activation") is not None and avg_asr["mean_activation"] >= 0.7
    # a_cross_source: if condition never ran (no cross-source partner), mark N/A
    a_cross_asr = avg_asr.get("a_cross_source")
    if a_cross_asr is None:
        criteria["a_cross_doesnt_suppress"] = None  # N/A — no cross-source partner available
    else:
        criteria["a_cross_doesnt_suppress"] = a_cross_asr >= 0.7

    n_met = sum(1 for v in criteria.values() if v is True)
    n_total = sum(1 for v in criteria.values() if v is not None)

    verdict = "SELECTIVITY_ESTABLISHED" if n_met == n_total else (
        "PARTIAL" if n_met >= n_total - 1 else "SELECTIVITY_UNRESOLVED"
    )

    return {
        "baseline_A_asr": baseline_A_asr,
        "baseline_D_asr": baseline_D_asr,
        "per_condition_avg_asr": avg_asr,
        "criteria": criteria,
        "criteria_met": n_met,
        "criteria_total": n_total,
        "verdict": verdict,
    }


def write_markdown(run_dir: Path, rows: list[dict], asr_table: dict, verdict: dict, partial: bool) -> str:
    layers = sorted(set(r["layer_patched"] for r in rows if r.get("layer_patched") is not None))
    sources = sorted(set(r["source_example_id"] for r in rows))
    n_rows = len(rows)

    lines = ["# P11 Selectivity and Sufficiency Results"]
    lines.append("")
    if partial:
        lines.append("> **NOTE: PARTIAL RESULTS** — pilot still running or incomplete.")
        lines.append("")
    lines.append(f"**Run:** `{run_dir.name}`  ")
    lines.append(f"**Rows analyzed:** {n_rows}  ")
    lines.append(f"**Sources:** {len(sources)}  ")
    lines.append(f"**Layers tested:** {layers}  ")
    lines.append(f"**Verdict:** `{verdict['verdict']}` ({verdict['criteria_met']}/{verdict['criteria_total']} criteria met)")
    lines.append("")

    lines.append("## Baseline Success Rates")
    bA = verdict["baseline_A_asr"]
    bD = verdict["baseline_D_asr"]
    lines.append(f"- **baseline_A:** ASR = {bA:.2f}" if bA is not None else "- **baseline_A:** no data")
    lines.append(f"- **baseline_D:** ASR = {bD:.2f}" if bD is not None else "- **baseline_D:** no data")
    lines.append("")

    lines.append("## Per-Condition ASR by Layer")
    lines.append("")
    # Table header
    header = "| Condition | Group | " + " | ".join(f"L{l}" for l in layers) + " | Avg | Verdict |"
    sep = "|---|---|" + "---|" * (len(layers) + 2)
    lines.append(header)
    lines.append(sep)

    def group_for(cond):
        for g, conds in _CONDITION_GROUPS.items():
            if cond in conds:
                return g
        return ""

    avg_asr = verdict["per_condition_avg_asr"]
    for cond in _ALL_CONDITIONS:
        if cond in ("baseline_A", "baseline_D"):
            continue
        cells = []
        for li in layers:
            v = asr_table.get((cond, li))
            if v is None or v["asr"] is None:
                cells.append(" — ")
            else:
                cells.append(f"{v['asr']:.2f}(n={v['n']})")
        avga = avg_asr.get(cond)
        avg_str = f"{avga:.2f}" if avga is not None else "—"
        result_str = classify_condition_result(cond, avga, sum(v["n"] for (c, l), v in asr_table.items() if c == cond and l is not None) if cond in avg_asr else 0)
        row = f"| {cond} | {group_for(cond)} | " + " | ".join(cells) + f" | {avg_str} | {result_str} |"
        lines.append(row)
    lines.append("")

    lines.append("## Selectivity Criteria")
    lines.append("")
    for criterion, met in verdict["criteria"].items():
        mark = "✅" if met else "❌"
        lines.append(f"- {mark} `{criterion}`")
    lines.append("")

    lines.append("## Interpretation")
    v_str = verdict["verdict"]
    if v_str == "SELECTIVITY_ESTABLISHED":
        lines.append(
            "All selectivity criteria met. The suppression at L3–L22 is specific to "
            "replacing A-context activations with D-context activations: own-activation "
            "patching (identity), hook overhead (sham), random noise, harmless activations, "
            "and A activations from different sources all fail to suppress the attack."
        )
    elif v_str == "PARTIAL":
        lines.append(
            "Most selectivity criteria met but not all. See criteria table above for "
            "which conditions failed. Interpret P11 causal localization claim cautiously."
        )
    else:
        lines.append(
            "Selectivity unresolved. Either too few examples, or controls show that the "
            "suppression is not specific to D-context activations."
        )
    lines.append("")
    lines.append("## Sufficiency (a_to_d)")
    a2d_asr = avg_asr.get("a_to_d")
    if a2d_asr is not None:
        lines.append(
            f"Patching D prompt with A-context activations: ASR = {a2d_asr:.2f}. "
            + ("A activations are **sufficient** to cause D to succeed." if a2d_asr >= 0.5
               else "A activations alone are **not sufficient** to make D succeed (patching is necessary but not sufficient).")
        )
    else:
        lines.append("a_to_d condition not yet run or no data.")
    lines.append("")
    lines.append(f"*Generated by `poc_stage4/analyze_p11_selectivity.py` — {'partial results' if partial else 'complete'}.*")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", type=Path, help="Path to specific run directory")
    ap.add_argument("--partial", action="store_true", help="Allow analysis on incomplete results")
    args = ap.parse_args()

    if args.run_dir:
        run_dir = args.run_dir
    else:
        runs = sorted(_DEFAULT_BASE.glob("run_*"))
        if not runs:
            print("No run directories found under", _DEFAULT_BASE)
            sys.exit(1)
        run_dir = runs[-1]

    print(f"Analyzing: {run_dir}")
    rows = load_results(run_dir)
    if not rows:
        print("No results found in", run_dir / "results.jsonl")
        sys.exit(1)

    print(f"Loaded {len(rows)} rows")

    conditions_seen = set(r["condition"] for r in rows)
    layers_seen = sorted(set(r["layer_patched"] for r in rows if r.get("layer_patched") is not None))
    sources_seen = set(r["source_example_id"] for r in rows)
    print(f"Conditions: {conditions_seen}")
    print(f"Layers: {layers_seen}")
    print(f"Sources: {len(sources_seen)}")

    asr_table = compute_asr_table(rows)
    verdict = build_selectivity_verdict(asr_table)

    print(f"\nVerdict: {verdict['verdict']}")
    print(f"Criteria met: {verdict['criteria_met']}/{verdict['criteria_total']}")
    for c, v in verdict["criteria"].items():
        mark = "✅" if v else "❌" if v is not None else "—"
        asr = verdict["per_condition_avg_asr"].get(c.split("_")[0] if "_" in c else c)
        print(f"  {mark} {c}")
    print(f"\nPer-condition avg ASR:")
    for cond, asr in sorted(verdict["per_condition_avg_asr"].items()):
        print(f"  {cond:25s}: {asr:.2f}" if asr is not None else f"  {cond:25s}: —")

    partial = args.partial or len(conditions_seen) < len(_ALL_CONDITIONS) - 2

    md = write_markdown(run_dir, rows, asr_table, verdict, partial)

    out_doc = _DOCS / "P11_SELECTIVITY_AND_SUFFICIENCY_RESULTS.md"
    out_doc.write_text(md)
    print(f"\nMarkdown written to {out_doc}")

    out_json = run_dir / "selectivity_summary.json"
    with out_json.open("w") as f:
        json.dump({
            "run_dir": str(run_dir),
            "n_rows": len(rows),
            "n_sources": len(sources_seen),
            "layers": layers_seen,
            "asr_table": {f"{cond}__L{layer}": vals for (cond, layer), vals in asr_table.items()},
            "verdict": verdict,
            "partial": partial,
        }, f, indent=2)
    print(f"JSON written to {out_json}")


if __name__ == "__main__":
    main()
