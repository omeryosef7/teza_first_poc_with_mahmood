"""Analyze results from run_block_ablation.py (P16 MLP vs Attention Block Ablation).

Decision gate:
  zero_attn_L{l} ASR < 0.5 → attention sublayer at layer l is causally necessary
  zero_mlp_L{l} ASR < 0.5 → MLP sublayer at layer l is causally necessary
  All ASR ≈ 1.0 → mechanism is not localized to any single sublayer

Usage:
    python -m poc_stage4.analyze_block_ablation [--run-dir ...]
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_DEFAULT_DIR = _REPO_ROOT / "outputs" / "stage4" / "p16_block_ablation"


def _mcnemar_midp(b: int, c: int) -> float:
    from math import comb
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p_total = 0.0
    for i in range(k + 1):
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
    direct = run_dir / "results.jsonl"
    if direct.exists():
        for line in direct.read_text().splitlines():
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return results
    for sub in sorted(run_dir.iterdir()):
        f = sub / "results.jsonl"
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return results


def analyze(run_dir: Path, write_doc: bool = False) -> dict:
    results = _load_results(run_dir)
    if not results:
        print(f"No results in {run_dir}")
        return {}

    print(f"Loaded {len(results)} rows")

    by_example: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        sid = r.get("source_example_id", "")
        cond = r.get("condition", "")
        by_example[sid][cond] = r

    examples = sorted(by_example.keys())
    all_conds = sorted({c for e in by_example.values() for c in e.keys()})
    ablation_conds = [c for c in all_conds if c.startswith("zero_")]

    print(f"{len(examples)} examples, conditions: {all_conds}")
    print(f"\n{'Condition':<35} {'n':>5} {'n_suc':>7} {'ASR':>7}")
    print("-" * 60)

    per_condition = {}
    for cond in all_conds:
        rows = [by_example[sid][cond] for sid in examples if cond in by_example[sid]]
        n = len(rows)
        n_suc = sum(1 for r in rows if _timing_correct_success(r))
        asr = n_suc / n if n > 0 else float("nan")
        per_condition[cond] = {"n": n, "n_success": n_suc, "asr": round(asr, 4)}
        flag = " ← CAUSAL!" if asr < 0.5 else ""
        note = "(no ablation)" if cond == "baseline" else flag
        print(f"{cond:<35} {n:>5} {n_suc:>7} {asr:>7.3f}  {note}")

    paired_tests = {}
    if "baseline" in all_conds and ablation_conds:
        print(f"\n{'Condition (vs baseline)':<35} {'b':>5} {'c':>5} {'p':>8}")
        for cond in ablation_conds:
            paired = [sid for sid in examples
                      if "baseline" in by_example[sid] and cond in by_example[sid]]
            b = sum(1 for sid in paired
                    if by_example[sid]["baseline"].get("sr_success")
                    and not by_example[sid][cond].get("sr_success"))
            c_val = sum(1 for sid in paired
                        if not by_example[sid]["baseline"].get("sr_success")
                        and by_example[sid][cond].get("sr_success"))
            p = _mcnemar_midp(b, c_val)
            paired_tests[f"baseline_vs_{cond}"] = {
                "n_paired": len(paired), "b": b, "c": c_val,
                "p_mcnemar_midp": round(p, 6)
            }
            print(f"{cond:<35} {b:>5} {c_val:>5} {p:>8.4f}")

    # Decision
    causal = [c for c in ablation_conds if per_condition.get(c, {}).get("asr", 1.0) < 0.5]
    causal_attn = [c for c in causal if "attn" in c]
    causal_mlp = [c for c in causal if "mlp" in c]
    min_asr = min((per_condition.get(c, {}).get("asr", 1.0) for c in ablation_conds), default=1.0)

    if causal_attn and causal_mlp:
        decision = f"BOTH ATTN AND MLP CAUSAL: {causal}"
    elif causal_attn:
        decision = f"ATTENTION SUBLAYER CAUSAL: {causal_attn}. MLP sublayer not causal."
    elif causal_mlp:
        decision = f"MLP SUBLAYER CAUSAL: {causal_mlp}. Attention sublayer not causal."
    else:
        decision = (f"NON-CAUSAL: all block ablations show ASR≈1.0 (min={min_asr:.3f}). "
                    f"Mechanism not localized to any single sublayer.")

    print(f"\n=== Decision ===\n  {decision}")

    summary = {
        "n_examples": len(examples),
        "conditions": all_conds,
        "per_condition": per_condition,
        "paired_mcnemar": paired_tests,
        "causal_attn": causal_attn,
        "causal_mlp": causal_mlp,
        "decision": decision,
    }

    out_json = run_dir / "analysis_summary.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"\nWritten: {out_json}")

    if write_doc:
        _write_doc(summary, run_dir)

    return summary


def _write_doc(summary: dict, run_dir: Path) -> None:
    doc_path = _REPO_ROOT / "docs" / "BLOCK_ABLATION_RESULTS.md"
    n_ex = summary["n_examples"]
    per_cond = summary["per_condition"]
    decision = summary["decision"]

    rows = []
    for cond, stats in sorted(per_cond.items()):
        asr = stats.get("asr", float("nan"))
        flag = " ✓ CAUSAL" if asr < 0.5 else ""
        rows.append(f"| `{cond}` | {stats['n']} | {stats['n_success']} | {asr:.3f}{flag} |")

    doc = f"""# MLP vs Attention Block Ablation (P16)

**Date:** 2026-06-25  
**Method:** Zero entire attention sublayer OR MLP sublayer output at specific layers.  
**Examples:** {n_ex} pure_cot_hijack examples (Qwen3-14B).

---

## Motivation

P5b showed individual attention heads (H33, H2, H4) at L10 are NON-CAUSAL. P16 tests
whether the ENTIRE attention or MLP computation at key layers is causally necessary.
A coarser but more powerful intervention: if any component at these layers matters,
this will detect it.

P6 showed residual stream patching (end-aligned) is non-causal. P11 tests full-range.
P16 complements by removing the sublayer output entirely rather than patching inputs.

---

## Results

| Condition | n | n_success | ASR |
|-----------|---|-----------|-----|
{chr(10).join(rows)}

---

## Decision

**{decision}**

---

## Interpretation

{'The attack mechanism does NOT require the attention or MLP sublayers at the tested layers. ' +
 'This strongly suggests the mechanism operates through cross-layer circuit interactions ' +
 'rather than any localized sublayer computation.' if 'NON-CAUSAL' in decision else
 'A sublayer ablation breaks the attack — mechanism found at the sublayer level.'}

Together with:
- P4/P4b: residual stream direction ablation NON-CAUSAL
- P5b: individual head ablation NON-CAUSAL  
- P6: residual stream patching (end-aligned) NON-CAUSAL
- P11: full-range patching — see results
- P14: generation-phase injection — see results

The CoT hijacking attack mechanism is remarkably robust to targeted interventions.

---

## Files
- Results: `{run_dir}/results.jsonl`
- Analysis: `{run_dir}/analysis_summary.json`
"""
    doc_path.write_text(doc)
    print(f"Written: {doc_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", default=str(_DEFAULT_DIR))
    ap.add_argument("--write-doc", action="store_true")
    args = ap.parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Not found: {run_dir}")
        return
    analyze(run_dir, write_doc=args.write_doc)


if __name__ == "__main__":
    main()
