#!/usr/bin/env python3
"""Gate-3 soft-prompt trajectory diagnostic.

Diagnoses whether the Gate-3 soft-prompt REINFORCE objective is actually
OPTIMIZING across its steps: does expected_reward / sampled_asr TREND UP?
Compares the REINFORCE arm to the prefix_ce arm.

SAFETY: reads ONLY numeric/scalar step fields. It never reads, prints, or
loads any generation-text field (greedy_text, best_response_text,
response_texts, or the full instruction string). The instruction is used only
to build a short opaque label (first ~40 chars) for grouping/identification.

Torch-free, pure Python (json, statistics, argparse, csv).
"""
import argparse
import csv
import json
import os
import statistics

# Scalar step fields we are permitted to touch. Text fields are never accessed.
SCALAR_STEP_FIELDS = (
    "step",
    "expected_reward",
    "sampled_asr",
    "greedy_asr_proxy",
    "surrogate_loss",
    "grad_norm",
    "reward_variance",
    "soft_prompt_norm",
)

# File stem -> (arm files by seed). We enumerate the known Gate-3 layout but
# also tolerate missing files gracefully.
SEED_FILES = {
    0: {"prefix_ce": "prefix_ce.jsonl", "reinforce": "reinforce.jsonl"},
    1: {"prefix_ce": "prefix_ce_seed1.jsonl", "reinforce": "reinforce_seed1.jsonl"},
    2: {"prefix_ce": "prefix_ce_seed2.jsonl", "reinforce": "reinforce_seed2.jsonl"},
}


def linreg_slope(xs, ys):
    """Simple OLS slope of ys vs xs. Returns None if undefined (<2 pts or zero
    x-variance)."""
    n = len(xs)
    if n < 2:
        return None
    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / sxx


def _num(v):
    """Coerce to float if it is a real number, else None. Never touches text."""
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    return None


def label_from_instruction(rec):
    """Build a short opaque label using ONLY the first ~40 chars of the
    instruction. Not printed to markdown; used for the CSV row id only."""
    ins = rec.get("instruction")
    if not isinstance(ins, str):
        return ""
    snippet = ins[:40]
    # collapse whitespace/newlines so the CSV stays one-line-per-row
    return " ".join(snippet.split())


def analyze_run(rec):
    """Compute scalar trajectory stats for one run record. Reads only numeric
    step fields."""
    steps = rec.get("steps") or []
    step_idx = []
    exp_r = []
    samp = []
    grad = []
    rvar = []
    proxy_hits = []  # step indices where greedy_asr_proxy == 1.0

    for s in steps:
        si = _num(s.get("step"))
        er = _num(s.get("expected_reward"))
        sa = _num(s.get("sampled_asr"))
        gn = _num(s.get("grad_norm"))
        rv = _num(s.get("reward_variance"))
        gp = _num(s.get("greedy_asr_proxy"))
        if si is not None:
            step_idx.append(si)
            exp_r.append(er if er is not None else 0.0)
            samp.append(sa if sa is not None else 0.0)
            if gn is not None:
                grad.append(gn)
            if rv is not None:
                rvar.append(rv)
            if gp is not None and gp >= 1.0:
                proxy_hits.append(si)

    def first(v):
        return v[0] if v else None

    def last(v):
        return v[-1] if v else None

    def mx(v):
        return max(v) if v else None

    er_slope = linreg_slope(step_idx, exp_r)
    sa_slope = linreg_slope(step_idx, samp)

    proxy_ever = len(proxy_hits) > 0
    proxy_first = proxy_hits[0] if proxy_hits else None
    proxy_last = proxy_hits[-1] if proxy_hits else None
    # transient = hit at some point but NOT at the final step
    final_step = last(step_idx)
    proxy_final = proxy_ever and proxy_last == final_step
    proxy_transient = proxy_ever and not proxy_final

    return {
        "objective": rec.get("objective"),
        "length": rec.get("length"),
        "seed": rec.get("seed"),
        "instruction_label": label_from_instruction(rec),
        "n_steps": len(step_idx),
        "exp_reward_slope": er_slope,
        "sampled_asr_slope": sa_slope,
        "exp_reward_first": first(exp_r),
        "exp_reward_last": last(exp_r),
        "exp_reward_max": mx(exp_r),
        "exp_reward_delta": (last(exp_r) - first(exp_r)) if exp_r else None,
        "sampled_asr_first": first(samp),
        "sampled_asr_last": last(samp),
        "sampled_asr_max": mx(samp),
        "sampled_asr_delta": (last(samp) - first(samp)) if samp else None,
        "mean_grad_norm": statistics.fmean(grad) if grad else None,
        "mean_reward_variance": statistics.fmean(rvar) if rvar else None,
        "greedy_proxy_ever_1": int(proxy_ever),
        "greedy_proxy_first_step": proxy_first,
        "greedy_proxy_last_step": proxy_last,
        "greedy_proxy_transient": int(proxy_transient),
        "greedy_proxy_final": int(proxy_final),
    }


def load_runs(conf_dir):
    runs = []
    for seed, arms in SEED_FILES.items():
        for _arm, fname in arms.items():
            path = os.path.join(conf_dir, fname)
            if not os.path.exists(path):
                continue
            with open(path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    runs.append(analyze_run(rec))
    return runs


CSV_COLUMNS = [
    "objective",
    "length",
    "seed",
    "instruction_label",
    "n_steps",
    "exp_reward_slope",
    "sampled_asr_slope",
    "exp_reward_first",
    "exp_reward_last",
    "exp_reward_max",
    "exp_reward_delta",
    "sampled_asr_first",
    "sampled_asr_last",
    "sampled_asr_max",
    "sampled_asr_delta",
    "mean_grad_norm",
    "mean_reward_variance",
    "greedy_proxy_ever_1",
    "greedy_proxy_first_step",
    "greedy_proxy_last_step",
    "greedy_proxy_transient",
    "greedy_proxy_final",
]

FLAT_EPS = 1e-4  # |slope| below this is treated as "~flat"


def aggregate(runs):
    """Per-objective aggregates over expected_reward slope / delta."""
    by_obj = {}
    for r in runs:
        by_obj.setdefault(r["objective"], []).append(r)

    agg = {}
    for obj, rs in by_obj.items():
        slopes = [r["exp_reward_slope"] for r in rs if r["exp_reward_slope"] is not None]
        sa_slopes = [r["sampled_asr_slope"] for r in rs if r["sampled_asr_slope"] is not None]
        deltas = [r["exp_reward_delta"] for r in rs if r["exp_reward_delta"] is not None]
        n_pos = sum(1 for s in slopes if s > FLAT_EPS)
        n_neg = sum(1 for s in slopes if s < -FLAT_EPS)
        n_flat = sum(1 for s in slopes if abs(s) <= FLAT_EPS)
        agg[obj] = {
            "n_runs": len(rs),
            "n_slope_scored": len(slopes),
            "mean_exp_reward_slope": statistics.fmean(slopes) if slopes else None,
            "mean_sampled_asr_slope": statistics.fmean(sa_slopes) if sa_slopes else None,
            "mean_exp_reward_delta": statistics.fmean(deltas) if deltas else None,
            "n_positive_slope": n_pos,
            "n_negative_slope": n_neg,
            "n_flat_slope": n_flat,
            "n_greedy_proxy_ever": sum(r["greedy_proxy_ever_1"] for r in rs),
            "n_greedy_proxy_final": sum(r["greedy_proxy_final"] for r in rs),
            "n_greedy_proxy_transient": sum(r["greedy_proxy_transient"] for r in rs),
        }
    return agg


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def write_csv(runs, out_csv):
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in runs:
            w.writerow({k: _fmt(r.get(k)) for k in CSV_COLUMNS})


def build_summary_lines(agg):
    """Plain-English scalar-only summary lines (no PASS/FAIL, no harmful text)."""
    lines = []
    for obj in sorted(agg.keys(), key=lambda x: str(x)):
        a = agg[obj]
        lines.append(
            f"{obj}: expected_reward slope mean = {_fmt(a['mean_exp_reward_slope'])} "
            f"({a['n_positive_slope']} positive / {a['n_flat_slope']} flat / "
            f"{a['n_negative_slope']} negative of {a['n_slope_scored']} scored, "
            f"{a['n_runs']} runs); "
            f"mean first->last delta = {_fmt(a['mean_exp_reward_delta'])}; "
            f"sampled_asr slope mean = {_fmt(a['mean_sampled_asr_slope'])}; "
            f"greedy_asr_proxy hit 1.0 in {a['n_greedy_proxy_ever']} runs "
            f"({a['n_greedy_proxy_final']} at final step, "
            f"{a['n_greedy_proxy_transient']} transient only)."
        )
    return lines


def write_md(agg, out_md, conf_dir):
    os.makedirs(os.path.dirname(out_md) or ".", exist_ok=True)
    lines = build_summary_lines(agg)
    with open(out_md, "w") as fh:
        fh.write("# Gate-3 Soft-Prompt Trajectory Diagnostic\n\n")
        fh.write(f"Source: `{conf_dir}`\n\n")
        fh.write(
            "Question: does the soft-prompt objective actually OPTIMIZE across "
            "steps (expected_reward / sampled_asr trending up), and how does the "
            "REINFORCE arm compare to the prefix_ce arm? Slope = OLS of the scalar "
            f"vs step index; a slope near 0 (|slope| <= {FLAT_EPS}) is treated as "
            "flat. Numbers only; no behavior text; no PASS/FAIL claim.\n\n")
        fh.write("## Per-objective read\n\n")
        for ln in lines:
            fh.write(f"- {ln}\n")
        fh.write("\n## Notes\n\n")
        fh.write(
            "- `exp_reward_slope` > 0 means expected_reward rises across steps "
            "(objective is moving the soft prompt toward higher reward).\n")
        fh.write(
            "- A flat/noisy expected_reward slope with sampled_asr staying near "
            "its start supports 'the objective is not effectively improving "
            "behavior at this budget.'\n")
        fh.write(
            "- A rising slope while sampled_asr lags supports 'it optimizes but "
            "the reported metric is a truncation proxy.'\n")
        fh.write(
            "- `greedy_proxy_transient` counts runs where greedy_asr_proxy hit "
            "1.0 at some step but not the final step (transient spikes).\n")
        fh.write("\nPer-run detail: see `results/GATE3_TRAJECTORY_DIAG.csv`.\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conf-dir", default="outputs/phase_d_soft_prompt_gate3_conf")
    ap.add_argument("--out-csv", default="results/GATE3_TRAJECTORY_DIAG.csv")
    ap.add_argument("--out-md", default="docs/GATE3_TRAJECTORY_DIAG.md")
    args = ap.parse_args()

    runs = load_runs(args.conf_dir)
    agg = aggregate(runs)

    write_csv(runs, args.out_csv)
    write_md(agg, args.out_md, args.conf_dir)

    print(f"Loaded {len(runs)} run records from {args.conf_dir}")
    print(f"CSV -> {args.out_csv}")
    print(f"MD  -> {args.out_md}")
    print("Per-objective slope summary:")
    for ln in build_summary_lines(agg):
        print("  " + ln)


if __name__ == "__main__":
    main()
