"""Analyze results from run_head_ablation.py (P5b Attention Head Ablation).

Reads results.jsonl from head ablation runs and identifies which heads
(if any) causally mediate the CoT hijacking attack.

Decision gate:
  - Single-head ablation ASR < 0.5 → that head is causally necessary
  - Only multi-head combos work → mechanism distributed across heads
  - All ASR ≈ 1.0 → attention heads not causally sufficient

Usage:
    python -m poc_stage4.analyze_head_ablation [--run-dir outputs/stage4/head_ablation]
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_DEFAULT_DIR = _REPO_ROOT / "outputs" / "stage4" / "head_ablation"


def _mcnemar_midp(b: int, c: int) -> float:
    from math import comb
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p_total = 0.0
    for i in range(0, k + 1):
        p_i = comb(n, i) * (0.5 ** n)
        p_total += (0.5 * p_i) if i == k else p_i
    return min(1.0, 2 * p_total)


# elapsed_s is retained as diagnostic metadata only — never used to override the judge label.
# The timing-based override (_COMPLIANCE_ELAPSED_THRESHOLD_S) was removed as scientifically
# invalid: long generation time is not evidence of compliance. Use raw sr_success only.

def _timing_correct_success(r: dict) -> bool:
    """Return raw keyword-based judge label. elapsed_s is ignored."""
    return bool(r.get("sr_success", False))


def _load_results(run_dir: Path) -> list[dict]:
    results = []
    for sub in sorted(run_dir.iterdir()):
        if not sub.is_dir():
            continue
        f = sub / "results.jsonl"
        if not f.exists():
            continue
        for line in f.read_text().strip().split("\n"):
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return results


def analyze(run_dir: Path, write_doc: bool = False) -> dict:
    results = _load_results(run_dir)
    if not results:
        print(f"No results found in {run_dir}")
        return {}

    print(f"Loaded {len(results)} result rows")

    # Group by source_example_id
    by_example: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        sid = r.get("source_example_id", "")
        cond = r.get("condition", "")
        by_example[sid][cond] = r

    examples = sorted(by_example.keys())
    print(f"{len(examples)} unique examples")

    all_conds = sorted({c for e in by_example.values() for c in e.keys()})
    single_head_conds = [c for c in all_conds if c.startswith("zero_head_")]
    multi_head_conds = [c for c in all_conds if c.startswith("zero_all_")]
    print(f"Single-head conditions: {single_head_conds}")
    print(f"Multi-head conditions: {multi_head_conds}")

    # Per-condition stats
    print(f"\n{'Condition':<35} {'n':>5} {'n_success':>10} {'ASR':>7} {'note'}")
    print("-" * 70)

    per_condition = {}
    for cond in all_conds:
        rows = [by_example[sid][cond] for sid in examples if cond in by_example[sid]]
        n = len(rows)
        n_success = sum(1 for r in rows if _timing_correct_success(r))
        asr = n_success / n if n > 0 else float("nan")
        per_condition[cond] = {"n": n, "n_success": n_success, "asr": round(asr, 4)}

        note = ""
        if cond == "baseline":
            note = "(no ablation; attack should succeed)"
        elif cond.startswith("zero_head_") or cond.startswith("zero_all_"):
            note = "← CAUSAL!" if asr < 0.5 else "still complying"

        print(f"{cond:<35} {n:>5} {n_success:>10} {asr:>7.3f}  {note}")

    # McNemar vs baseline
    paired_tests = {}
    intervention_conds = single_head_conds + multi_head_conds
    if "baseline" in all_conds and intervention_conds:
        print(f"\n{'Condition (vs baseline)':<35} {'b':>5} {'c':>5} {'p':>8}")
        for cond in intervention_conds:
            paired = [sid for sid in examples
                      if "baseline" in by_example[sid] and cond in by_example[sid]]
            b = sum(1 for sid in paired
                    if by_example[sid]["baseline"].get("sr_success")
                    and not by_example[sid][cond].get("sr_success"))
            c = sum(1 for sid in paired
                    if not by_example[sid]["baseline"].get("sr_success")
                    and by_example[sid][cond].get("sr_success"))
            p = _mcnemar_midp(b, c)
            paired_tests[f"baseline_vs_{cond}"] = {
                "n_paired": len(paired), "b": b, "c": c,
                "p_mcnemar_midp": round(p, 6)
            }
            print(f"{cond:<35} {b:>5} {c:>5} {p:>8.4f}")

    # Decision
    causal_heads = [
        cond for cond in single_head_conds
        if per_condition.get(cond, {}).get("asr", 1.0) < 0.5
    ]
    causal_combos = [
        cond for cond in multi_head_conds
        if per_condition.get(cond, {}).get("asr", 1.0) < 0.5
    ]

    if causal_heads:
        decision = f"CAUSAL HEADS: {causal_heads}. Single-head ablation restores refusal."
    elif causal_combos:
        min_asr_single = min(
            (per_condition.get(c, {}).get("asr", 1.0) for c in single_head_conds), default=1.0
        )
        decision = (f"DISTRIBUTED: No single head is causal (min single-head ASR={min_asr_single:.3f}). "
                    f"Multi-head combos ARE causal: {causal_combos}. "
                    f"Mechanism distributed across multiple heads.")
    else:
        min_asr = min(
            (per_condition.get(c, {}).get("asr", 1.0)
             for c in single_head_conds + multi_head_conds), default=1.0
        )
        decision = (f"NON-CAUSAL: All head ablations show ASR≈1.0 (min={min_asr:.3f}). "
                    f"Attention heads not causally sufficient for CoT hijacking.")

    print(f"\n=== Decision ===")
    print(f"  {decision}")

    summary = {
        "n_examples": len(examples),
        "conditions": all_conds,
        "per_condition": per_condition,
        "paired_mcnemar": paired_tests,
        "causal_single_heads": causal_heads,
        "causal_combos": causal_combos,
        "decision": decision,
    }

    out_json = run_dir / "analysis_summary.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"\nWritten: {out_json}")

    if write_doc:
        _write_doc(summary)

    return summary


def _write_doc(summary: dict) -> None:
    doc_path = _REPO_ROOT / "docs" / "HEAD_ABLATION_RESULTS.md"
    n_ex = summary["n_examples"]
    per_cond = summary["per_condition"]
    decision = summary["decision"]
    causal = summary.get("causal_single_heads", [])
    combos = summary.get("causal_combos", [])
    paired = summary.get("paired_mcnemar", {})

    rows = []
    for cond, stats in per_cond.items():
        asr = stats.get("asr", float("nan"))
        n = stats.get("n", 0)
        flag = " ✓ CAUSAL" if asr < 0.5 else ""
        rows.append(f"| `{cond}` | {n} | {stats.get('n_success', 0)} | {asr:.3f}{flag} |")

    paired_rows = []
    for test_key, ts in paired.items():
        cond = test_key.replace("baseline_vs_", "")
        p = ts.get("p_mcnemar_midp", 1.0)
        flag = " ✓" if p < 0.05 else ""
        paired_rows.append(f"| `{cond}` | {ts['b']} | {ts['c']} | {p:.4f}{flag} |")

    baseline_asr = per_cond.get("baseline", {}).get("asr", 1.0)

    doc = f"""# Head Ablation Results (P5b) — Attention Mechanism Test

**Date:** 2026-06-25
**Method:** Zero specific attention head outputs (o_proj input zero-masking) on Qwen3-14B.
**Examples:** {n_ex} pure_cot_hijack examples.

---

## Motivation

P4 and P4b showed that linear residual-stream ABLATION (project-out) is non-causal for the
CoT hijacking attack. P5a identified attention heads with high user_prompt attention at late
prompt layers. P5b tests whether zeroing those specific heads restores refusal.

**Key question:** Is any attention head causally necessary for the puzzle wrapper to succeed?

**Candidate heads** (from P5a, high user_prompt mass + low entropy):
- L10/H33: user_prompt=0.961, L10/H2: entropy=0.282
- L10/H19: user_prompt=0.925, L10/H4: entropy=0.293
- L26/H31: user_prompt=0.912, L26/H29: entropy=1.045
- L35/H25: entropy=0.460, L35/H37: entropy=0.465

---

## Results

| Condition | n | n_success | ASR |
|-----------|---|-----------|-----|
{chr(10).join(rows)}

---

## McNemar Tests (vs baseline)

| Condition | b | c | p (mid-p) |
|-----------|---|---|----------|
{chr(10).join(paired_rows) if paired_rows else "*(not computed)*"}

---

## Decision

**{decision}**

Baseline ASR: {baseline_asr:.3f}

{'### Causal heads identified: ' + ', '.join(causal) if causal else ''}
{'### Causal combos identified: ' + ', '.join(combos) if combos else ''}

---

## Interpretation

{'Zeroing head(s) ' + ', '.join(causal) + ' restores refusal → these heads are causally necessary for the attack.' if causal else 'No attention heads are causally necessary → the mechanism is not reducible to specific head outputs.'}

This {'supports' if causal else 'contradicts'} the attention-pathway hypothesis. The next step is:
{'- P5c: Multi-head ablation sweeps to find minimal causal sets' if causal else '- P6: Activation patching (full residual stream replacement) to test if mechanism is in residual stream'}
{'- P5c: Test head ablation during generation phase (not just prefill)' if causal else '- Consider non-linear or multi-layer interaction mechanisms'}

---

## Files

- Per-example data: `outputs/stage4/head_ablation/run_*/results.jsonl`
- Analysis: `outputs/stage4/head_ablation/analysis_summary.json`
"""

    doc_path.write_text(doc)
    print(f"Written: {doc_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", default=str(_DEFAULT_DIR))
    ap.add_argument("--output-json", default=None)
    ap.add_argument("--write-doc", action="store_true")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Run dir not found: {run_dir}")
        return

    summary = analyze(run_dir, write_doc=args.write_doc)

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
