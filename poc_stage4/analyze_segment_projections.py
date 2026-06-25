"""Segment-level projection analysis (CPU-only, P5a-preliminary).

Uses existing Stage 4B per_example_stats.csv to compare behavioral direction
projections across token segments (thinking, answer, other/prompt) by
attack mechanism.

Scientific question: Where in the token sequence does the attack signal live?
Is the behavioral direction projection elevated during thinking (suggesting
the attack corrupts the thinking phase representation) or in the answer
(suggesting the direction merely tracks compliance)?

No new GPU runs required — reads from existing subspace_stats_behavioral outputs.

Outputs:
    outputs/stage4/factorial_analysis/segment_projections_qwen3.json
    outputs/stage4/factorial_analysis/segment_projections_gemma4.json
    docs/SEGMENT_PROJECTION_ANALYSIS.md

Usage:
    python -m poc_stage4.analyze_segment_projections
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).parent.parent
_OUT_DIR = _REPO_ROOT / "outputs" / "stage4" / "factorial_analysis"

# Best behavioral layer+rank per model
_MODEL_CONFIGS = {
    "qwen3": {
        "stats_dir": "outputs/stage4/qwen3-14b/subspace_stats_behavioral",
        "best_layer": 26,
        "best_rank": 3,
        "mech_model_family": "qwen3",
        "n_layers": 48,
    },
    "gemma4": {
        "stats_dir": "outputs/stage4/gemma4-e4b-it/subspace_stats_behavioral",
        "best_layer": 17,
        "best_rank": 4,
        "mech_model_family": "gemma4",
        "n_layers": 46,
    },
}

_MECHANISM_ORDER = [
    "pure_cot_hijack",
    "puzzle_dep_only",
    "target_easy",
    "universally_resistant",
    "incomplete_factorial",
]


def _load_mechanism_map(mech_family: str) -> dict[str, str]:
    """Return {source_example_id: mechanism} for a given model family."""
    path = _REPO_ROOT / "outputs" / "stage4" / "mechanism_classification.jsonl"
    out: dict[str, str] = {}
    for line in path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("model_family") == mech_family:
            out[r["source_example_id"]] = r.get("mechanism", "unknown")
    return out


def _mean(vals: list[float]) -> Optional[float]:
    return sum(vals) / len(vals) if vals else None


def _std(vals: list[float]) -> Optional[float]:
    if len(vals) < 2:
        return None
    m = _mean(vals)
    return (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5


def analyze_model(model_key: str) -> dict:
    cfg = _MODEL_CONFIGS[model_key]
    stats_path = _REPO_ROOT / cfg["stats_dir"] / "per_example_stats.csv"
    if not stats_path.exists():
        return {"error": f"per_example_stats.csv not found at {stats_path}"}

    mech_map = _load_mechanism_map(cfg["mech_model_family"])
    best_layer = cfg["best_layer"]
    best_rank = cfg["best_rank"]

    # Parse CSV manually (no pandas required)
    lines = stats_path.read_text().strip().split("\n")
    header = lines[0].split(",")
    col = {h: i for i, h in enumerate(header)}

    # Collect per-(mechanism, segment) projections at best layer/rank
    # Also collect per-(example, segment) for individual analysis
    by_mech_seg: dict[tuple, list[float]] = defaultdict(list)
    per_example: dict[str, dict[str, float]] = defaultdict(dict)

    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) < len(header):
            continue
        pid = parts[col["prompt_id"]]
        try:
            layer = int(parts[col["layer"]])
            rank = int(parts[col["subspace_rank"]])
        except ValueError:
            continue
        if layer != best_layer or rank != best_rank:
            continue
        segment = parts[col["segment"]]
        try:
            mean_proj = float(parts[col["mean_proj"]])
        except ValueError:
            continue
        mech = mech_map.get(pid, "unknown")
        by_mech_seg[(mech, segment)].append(mean_proj)
        per_example[pid][segment] = mean_proj

    segments = ["thinking", "answer", "other"]

    # Per-mechanism, per-segment stats
    per_mech: dict[str, dict] = {}
    for mech in _MECHANISM_ORDER + ["unknown"]:
        mech_data: dict[str, dict] = {}
        for seg in segments:
            vals = by_mech_seg.get((mech, seg), [])
            m = _mean(vals)
            s = _std(vals)
            mech_data[seg] = {
                "n": len(vals),
                "mean": round(m, 4) if m is not None else None,
                "std": round(s, 4) if s is not None else None,
            }
        # Thinking-to-answer delta (negative = answer proj drops vs thinking)
        t_vals = by_mech_seg.get((mech, "thinking"), [])
        a_vals = by_mech_seg.get((mech, "answer"), [])
        if t_vals and a_vals:
            # Per-example delta where both segments are available
            t_by_id = {pid: v for pid, v in per_example.items()
                       if mech_map.get(pid) == mech and "thinking" in per_example[pid]}
            deltas = [per_example[pid]["thinking"] - per_example[pid].get("answer", 0)
                      for pid in t_by_id if "answer" in per_example[pid]]
            mech_data["thinking_minus_answer"] = {
                "n": len(deltas),
                "mean": round(_mean(deltas), 4) if deltas else None,
                "std": round(_std(deltas), 4) if deltas else None,
            }
        per_mech[mech] = mech_data

    # Per pure_cot_hijack example breakdown
    pure_ids = [pid for pid, m in mech_map.items() if m == "pure_cot_hijack"]
    per_example_pure = {
        pid: per_example.get(pid, {}) for pid in sorted(pure_ids)
        if pid in per_example
    }

    return {
        "model": model_key,
        "best_layer": best_layer,
        "best_rank": best_rank,
        "n_examples_total": len(set(
            pid for pid, _ in [(p, s) for (p, s) in by_mech_seg.keys()]
        )),
        "per_mechanism": per_mech,
        "pure_cot_hijack_per_example": per_example_pure,
    }


def write_doc(qwen3_res: dict, gemma4_res: dict) -> Path:
    docs_dir = _REPO_ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)
    out_path = docs_dir / "SEGMENT_PROJECTION_ANALYSIS.md"

    def fmt(v) -> str:
        return f"{v:.3f}" if v is not None else "—"

    def mech_row(mech: str, res: dict) -> str:
        d = res.get("per_mechanism", {}).get(mech, {})
        t = d.get("thinking", {})
        a = d.get("answer", {})
        o = d.get("other", {})
        delta = d.get("thinking_minus_answer", {})
        return (f"| {mech:<25} | {t.get('n', 0):>4} | {fmt(t.get('mean'))} ± {fmt(t.get('std'))} "
                f"| {fmt(a.get('mean'))} ± {fmt(a.get('std'))} "
                f"| {fmt(o.get('mean'))} ± {fmt(o.get('std'))} "
                f"| {fmt(delta.get('mean'))} |")

    q_l = qwen3_res.get("best_layer", "?")
    q_r = qwen3_res.get("best_rank", "?")
    g_l = gemma4_res.get("best_layer", "?")
    g_r = gemma4_res.get("best_rank", "?")

    content = f"""# Segment Projection Analysis (P5a-preliminary)

**Method:** CPU-only analysis using existing Stage 4B `per_example_stats.csv`.
Projections are mean signed projections onto the behavioral refusal direction
at the best layer+rank per model during each token segment.

- **Qwen3-14B:** L{q_l}/rank{q_r} behavioral direction
- **Gemma4-E4B-IT:** L{g_l}/rank{g_r} behavioral direction

A **positive projection** means the residual stream representation is more
aligned with the refusal direction (expected for refused responses).
A **negative** or near-zero projection during thinking suggests the attack
has suppressed the refusal signal.

---

## Qwen3-14B: Projection by Mechanism and Segment

| Mechanism                 |    n | Thinking (mean±std) | Answer (mean±std) | Prompt/Other | Thinking−Answer |
|---------------------------|------|---------------------|-------------------|--------------|-----------------|
"""
    for mech in _MECHANISM_ORDER:
        content += mech_row(mech, qwen3_res) + "\n"

    content += f"""
---

## Gemma4-E4B-IT: Projection by Mechanism and Segment

| Mechanism                 |    n | Thinking (mean±std) | Answer (mean±std) | Prompt/Other | Thinking−Answer |
|---------------------------|------|---------------------|-------------------|--------------|-----------------|
"""
    for mech in _MECHANISM_ORDER:
        content += mech_row(mech, gemma4_res) + "\n"

    content += f"""
---

## Pure CoT Hijack — Per-Example Breakdown (Qwen3-14B, L{q_l}/rank{q_r})

| Example ID (abbreviated)                        | Thinking | Answer | Other |
|------------------------------------------------|----------|--------|-------|
"""
    for pid, segs in qwen3_res.get("pure_cot_hijack_per_example", {}).items():
        short = pid[:60]
        t = fmt(segs.get("thinking"))
        a = fmt(segs.get("answer"))
        o = fmt(segs.get("other"))
        content += f"| {short:<50} | {t:>8} | {a:>6} | {o:>5} |\n"

    content += f"""
---

## Interpretation

### What this tells us

1. **Where the attack signal lives:**
   - If `thinking` projections are HIGHER for `pure_cot_hijack` than other
     mechanisms → attack activates refusal-like representations during
     thinking (surprising — model "knows" it shouldn't comply but does)
   - If `thinking` projections are LOWER → attack suppresses refusal during CoT
   - If `answer` projections differ → the compliance direction differs at output

2. **Thinking−Answer delta:**
   - Positive = thinking has higher refusal signal than answer
     → refusal signal drops between thinking and answer (attack "overwrites" answer phase)
   - Negative = answer has higher refusal signal
     → unexpected (model becoming more reluctant after writing answer)

3. **Causal interpretation:**
   - These are representational, not causal. Consistent with P4 finding that
     ablating the direction doesn't change ASR.
   - High projection during thinking with ASR=1.0 would support the interpretation
     that the model's "refusal circuitry" is active but downstream suppressed.

---

*Generated: 2026-06-25*
*Source: Stage 4B `per_example_stats.csv`*
*Script: `poc_stage4/analyze_segment_projections.py`*
"""
    out_path.write_text(content)
    return out_path


def main():
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Segment Projection Analysis ===")

    qwen3_res = analyze_model("qwen3")
    g_path = _REPO_ROOT / _MODEL_CONFIGS["gemma4"]["stats_dir"] / "per_example_stats.csv"
    if g_path.exists():
        gemma4_res = analyze_model("gemma4")
    else:
        print(f"  WARNING: Gemma4 stats not found at {g_path}; skipping")
        gemma4_res = {"model": "gemma4", "error": f"stats not found: {g_path}"}

    # Write JSONs
    qw_out = _OUT_DIR / "segment_projections_qwen3.json"
    qw_out.write_text(json.dumps(qwen3_res, indent=2))
    print(f"Written: {qw_out}")

    g4_out = _OUT_DIR / "segment_projections_gemma4.json"
    g4_out.write_text(json.dumps(gemma4_res, indent=2))
    print(f"Written: {g4_out}")

    # Print summary
    print()
    for model_key, res in [("Qwen3", qwen3_res), ("Gemma4", gemma4_res)]:
        if "error" in res:
            print(f"{model_key}: ERROR — {res['error']}")
            continue
        print(f"{model_key} (L{res['best_layer']}/rank{res['best_rank']}):")
        for mech in _MECHANISM_ORDER:
            d = res.get("per_mechanism", {}).get(mech, {})
            t = d.get("thinking", {})
            a = d.get("answer", {})
            delta = d.get("thinking_minus_answer", {})
            if t.get("n", 0) == 0:
                continue
            t_mean = t.get('mean') or 0.0
            t_std = t.get('std') or 0.0
            a_mean = a.get('mean') or 0.0
            a_std = a.get('std') or 0.0
            d_mean = delta.get('mean') or 0.0
            print(f"  {mech:<25} thinking={t_mean:.3f}±{t_std:.3f}  "
                  f"answer={a_mean:.3f}±{a_std:.3f}  "
                  f"T-A delta={d_mean:.3f}")
        print()

    # Write doc
    if "error" not in qwen3_res:
        doc_path = write_doc(qwen3_res, gemma4_res)
        print(f"Written: {doc_path}")


if __name__ == "__main__":
    main()
