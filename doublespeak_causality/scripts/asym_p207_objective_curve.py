#!/usr/bin/env python
"""
ASYMMETRY SPRINT §20.7 — compute-scaling curve in OBJECTIVE space.

§20.7 asks how attack strength scales with optimization compute. Its stated endpoint is ASR vs
log(steps) -- which §20.8 showed is the endpoint this design has ~0.05 power on. The optimization
objective (GCG task loss) is continuous, paired per-prompt, and free of judge noise, so the
objective-space curve is available now and is far better powered.

It answers a strictly narrower question than ASR: how far the OPTIMIZER gets, not whether the
model complies. Given §20.1's objective-vs-behaviour dissociation, that distinction is the point,
not a caveat to gloss -- an objective-space curve that keeps improving does NOT imply ASR keeps
improving.

Endpoint: best-so-far task_loss (the loss series is non-monotonic -- established earlier in the
sprint -- so the endpoint value is not "achieved performance"). Paired by task_id across budgets.

Scalars only; never reads suffix or generation text.
"""
import argparse, glob, json
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

def patterns(arm):
    """`_pp_` immediately after the arm name marks the 200-step (untagged) budget, so the
    200 glob cannot accidentally match the s5/s600 dirs."""
    return {5: f"asym_p75_{arm}_s5_pp_*seed{{seed}}",
            200: f"asym_p75_{arm}_pp_*seed{{seed}}",
            600: f"asym_p75_{arm}_s600_pp_*seed{{seed}}"}


def best_losses(pattern, require_steps=None):
    """-> {task_id: best-so-far task_loss} for runs that actually completed."""
    out = {}
    for d in glob.glob(f"outputs/stage_gcg_perprompt/{pattern}"):
        p = Path(d)
        if not (p / "FINAL_CANDIDATES.jsonl").exists():
            continue                      # incomplete run -- never score a partial optimization
        il = p / "ITERATION_LOG.jsonl"
        if not il.exists():
            continue
        rows = [json.loads(l) for l in open(il) if l.strip()]
        if not rows:
            continue
        if {r.get("n_train_tasks") for r in rows} != {1}:
            raise SystemExit(f"{p.name}: n_train_tasks != 1 -- not a per-prompt run")
        if require_steps and len(rows) < require_steps:
            continue
        losses = [r["task_loss"] for r in rows if r.get("task_loss") is not None]
        if not losses:
            continue
        # task_id is the run_id segment between the arm tag and the trailing _seedNN
        tid = "_".join(p.name.split("_pp_")[1].split("_")[:-1])
        out[tid] = min(losses)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--arm", default="vanilla",
                    choices=["vanilla", "mechanism", "matched_random"])
    ap.add_argument("--budgets", default="5,200,600",
                    help="comma list; omit 600 to analyse only completed budgets at full n")
    ap.add_argument("--min-paired", type=int, default=10)
    ap.add_argument("--out", default="doublespeak_causality/outputs/asym_p207_objective_curve.json")
    args = ap.parse_args()

    want = [int(x) for x in args.budgets.split(",")]
    PAT = patterns(args.arm)
    per_budget = {b: best_losses(PAT[b].format(seed=args.seed), require_steps=b) for b in want}
    for b, d in per_budget.items():
        print(f"  budget {b:>4} steps: {len(d)} completed prompts")

    # Pair on the intersection so every budget is compared on the SAME prompts.
    common = sorted(set.intersection(*(set(d) for d in per_budget.values())))
    # "Interim" is a fact about the data, not a constant: the 5/200-step arms are complete, so the
    # widest budget's count is the corpus size for this split, and the read is final exactly when
    # every budget reaches it. Hardcoding interim=True mislabels the completed read as provisional.
    n_expected = max(len(d) for d in per_budget.values())
    interim = len(common) < n_expected
    print(f"\n  paired on {len(common)} prompts present at ALL budgets"
          + (f" of {n_expected} (some arm still running; INTERIM subset)" if interim
             else f" -- FULL coverage ({n_expected}/{n_expected}), this read is FINAL"))
    if len(common) < args.min_paired:
        raise SystemExit("too few paired prompts to report")

    rows, budgets = [], sorted(per_budget)
    for b in budgets:
        v = np.array([per_budget[b][t] for t in common])
        rows.append({"steps": b, "n": len(v), "mean_best_loss": float(v.mean()),
                     "sd": float(v.std())})
        print(f"    {b:>4} steps: mean best task_loss = {v.mean():.4f} (sd {v.std():.4f})")

    print("\n  paired contrasts (Wilcoxon signed-rank, same prompts):")
    contrasts = []
    for i in range(len(budgets) - 1):
        for j in range(i + 1, len(budgets)):
            a, bb = budgets[i], budgets[j]
            va = np.array([per_budget[a][t] for t in common])
            vb = np.array([per_budget[bb][t] for t in common])
            p = float(wilcoxon(va, vb).pvalue)
            d = float((vb - va).mean())
            nimp = int((vb < va).sum())
            contrasts.append({"from": a, "to": bb, "mean_delta": d, "p": p,
                              "n_improved": nimp, "n": len(common)})
            print(f"    {a:>4} -> {bb:<4}  mean d = {d:+.4f}  improved {nimp}/{len(common)}  p = {p:.2e}")

    # log-linear fit: is the gain still accruing, or saturating?
    x = np.log([r["steps"] for r in rows]); y = np.array([r["mean_best_loss"] for r in rows])
    slope, intercept = np.polyfit(x, y, 1)
    print(f"\n  log-linear fit: best_loss = {intercept:.4f} {slope:+.4f}*ln(steps)")
    for tgt in (2000, 10000):
        print(f"    extrapolated best_loss at {tgt:>5} steps: {intercept + slope*np.log(tgt):.4f}")
    print("  NOTE: extrapolation assumes no saturation and is descriptive only; "
          "an objective-space gain does NOT imply an ASR gain (§20.1).")

    Path(args.out).write_text(json.dumps(
        {"seed": args.seed, "arm": args.arm, "n_paired": len(common),
         "n_expected": n_expected, "interim": interim,
         "per_budget": rows, "contrasts": contrasts,
         "logfit": {"slope": float(slope), "intercept": float(intercept)}}, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
