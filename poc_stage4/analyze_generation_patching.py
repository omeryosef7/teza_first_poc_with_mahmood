"""Analyze results from run_generation_phase_patching.py (P14).

Reads results.jsonl from generation-phase patching runs. Determines
whether patching during thinking or answer generation phases breaks attacks.

Decision gate:
  gen_thinking_L{l} ASR < 0.5 → thinking phase mediates the attack at layer l
  gen_answer_L{l} ASR < 0.5 → answer phase mediates the attack at layer l
  Both ASR ≈ 1.0 → generation-phase mechanism not at tested layers/phases

Usage:
    python -m poc_stage4.analyze_generation_patching [--run-dir ...]
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_DEFAULT_DIR = _REPO_ROOT / "outputs" / "stage4" / "p14_gen_phase_patch"


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
        print(f"No results found in {run_dir}")
        return {}

    print(f"Loaded {len(results)} result rows")

    by_example: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        sid = r.get("source_example_id", "")
        cond = r.get("condition", "")
        by_example[sid][cond] = r

    examples = sorted(by_example.keys())
    all_conds = sorted({c for e in by_example.values() for c in e.keys()})
    patch_conds = [c for c in all_conds if c.startswith("gen_")]

    print(f"{len(examples)} examples, {len(all_conds)} conditions")
    print(f"\n{'Condition':<40} {'n':>5} {'n_success':>10} {'ASR':>7}")
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
            note = "(no patch)"
        elif asr < 0.5:
            note = "← CAUSAL!"
        print(f"{cond:<40} {n:>5} {n_success:>10} {asr:>7.3f}  {note}")

    # McNemar vs baseline
    paired_tests = {}
    if "baseline" in all_conds:
        print(f"\n{'Condition (vs baseline)':<40} {'b':>5} {'c':>5} {'p':>8}")
        for cond in patch_conds:
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
            print(f"{cond:<40} {b:>5} {c:>5} {p:>8.4f}")

    causal = [c for c in patch_conds if per_condition.get(c, {}).get("asr", 1.0) < 0.5]
    min_asr = min((per_condition.get(c, {}).get("asr", 1.0) for c in patch_conds), default=1.0)

    if causal:
        # Separate thinking vs answer causal conditions
        think_causal = [c for c in causal if "think" in c]
        answer_causal = [c for c in causal if "answer" in c]
        if think_causal and not answer_causal:
            decision = (f"THINKING MEDIATES: patching during thinking (not answer) breaks attack. "
                        f"Causal conditions: {think_causal}")
        elif answer_causal and not think_causal:
            decision = (f"ANSWER-PHASE CAUSAL: patching during answer phase breaks attack. "
                        f"Causal: {answer_causal}")
        else:
            decision = f"MULTIPLE PHASES CAUSAL: {causal}"
    else:
        decision = (f"NON-CAUSAL: all generation-phase patches show ASR≈1.0 (min={min_asr:.3f}). "
                    f"Mechanism is not in single-layer hidden states during generation.")

    print(f"\n=== Decision ===")
    print(f"  {decision}")

    summary = {
        "n_examples": len(examples),
        "conditions": all_conds,
        "per_condition": per_condition,
        "paired_mcnemar": paired_tests,
        "causal_conditions": causal,
        "decision": decision,
    }

    out_json = run_dir / "analysis_summary.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"\nWritten: {out_json}")

    if write_doc:
        _write_doc(summary, run_dir)

    return summary


def _write_doc(summary: dict, run_dir: Path) -> None:
    doc_path = _REPO_ROOT / "docs" / "GEN_PHASE_PATCHING_RESULTS.md"
    n_ex = summary["n_examples"]
    per_cond = summary["per_condition"]
    decision = summary["decision"]
    causal = summary.get("causal_conditions", [])

    rows = []
    for cond, stats in sorted(per_cond.items()):
        asr = stats.get("asr", float("nan"))
        flag = " ✓ CAUSAL" if asr < 0.5 else ""
        rows.append(f"| `{cond}` | {stats['n']} | {stats['n_success']} | {asr:.3f}{flag} |")

    baseline_asr = per_cond.get("baseline", {}).get("asr", float("nan"))

    doc = f"""# Generation-Phase Activation Patching (P14)

**Date:** 2026-06-25  
**Method:** Replace last-position D-condition hidden state at layer L during A-prompt generation.  
**Examples:** {n_ex} pure_cot_hijack examples (Qwen3-14B).

---

## Motivation

P6 (prefill-phase patching) showed NON-CAUSAL results: replacing activations during prompt
processing (last 26 positions) does not break the attack. This experiment tests whether the
causal mechanism operates during the GENERATION phase (thinking or answer).

The dual-pathway hypothesis from P1 analysis shows both prompt-phase AND thinking-phase
projections predict attack success independently. If thinking-phase patching breaks the
attack, it confirms that the thinking phase mediates (not just correlates with) success.

---

## Results

Baseline ASR: {baseline_asr:.3f}

| Condition | n | n_success | ASR |
|-----------|---|-----------|-----|
{chr(10).join(rows)}

---

## Decision

**{decision}**

---

## Interpretation

{'### Causal conditions found: ' + ', '.join(causal) if causal else '### No causal generation-phase conditions found'}

{'Patching during the thinking phase disrupts the attack mechanism, confirming that ' +
 'the thinking tokens mediate attack success (not just correlate with it).' if any('think' in c for c in causal) else
 'Patching during answer generation disrupts the attack, confirming compliance commitment in the answer phase.' if any('answer' in c for c in causal) else
 'No generation-phase patching breaks the attack. Combined with P6 (prefill non-causal), ' +
 'this suggests the mechanism is fundamentally distributed or operates through multi-layer ' +
 'non-linear interactions that cannot be interrupted by single-layer hidden-state replacement.'}

---

## Files

- Results: `{run_dir}/results.jsonl`
- Analysis: `{run_dir}/analysis_summary.json`
- Related: `docs/MECHANISM_SYNTHESIS.md`
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
        print(f"Run dir not found: {run_dir}")
        return

    analyze(run_dir, write_doc=args.write_doc)


if __name__ == "__main__":
    main()
