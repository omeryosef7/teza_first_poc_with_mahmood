"""Phase 10 (plan §14.2): prospective behavioral power for the second corpus.

Paired (McNemar) design: each prompt is scored base vs intervention, so the test is
on the discordant pairs (b = base-success -> arm-fail, c = base-fail -> arm-success).
Power depends on the discordant RATE p_disc = (b+c)/n and the true marginal effect
delta = (c-b)/n = ASR change. We estimate p_disc from PRIOR experiments (scalar
score fields only — never generation text) and report:

  * required n for >=80% power at delta = 0.10 and 0.15;
  * the minimum detectable effect at a given corpus n (e.g. the AdvBench test split).

Simulation-based (exact McNemar binomial per replicate), so no formula approximation
error. Deterministic given --seed.

    # discordant rate from a prior paired run (reads only *_score fields):
    python scripts/phase10_power_analysis.py --from-run <phase4_run_dir> \
        --base-field base_score --arm-field refusal_ablate_score --corpus-n 40
    # or supply p_disc directly:
    python scripts/phase10_power_analysis.py --p-disc 0.30 --corpus-n 40
"""
from __future__ import annotations
import argparse
import glob
import json
import os

import numpy as np
from scipy import stats


def mcnemar_exact_p(b, c):
    """Two-sided exact McNemar (binomial) on the discordant counts."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = 2.0 * stats.binom.cdf(k, n, 0.5)
    return min(1.0, p)


def power_at(n, p_disc, delta, n_rep=4000, alpha=0.05, seed=0):
    """Monte-Carlo power for detecting marginal effect `delta` with discordant rate
    `p_disc` in n paired items. p_c = (p_disc+delta)/2, p_b = (p_disc-delta)/2."""
    p_c = (p_disc + delta) / 2.0
    p_b = (p_disc - delta) / 2.0
    if p_b < 0 or p_c < 0 or (p_b + p_c) > 1:
        return float("nan")
    rng = np.random.default_rng(seed)
    # each item: 0=concordant, 1=discordant-up(c), 2=discordant-down(b)
    probs = [1 - p_disc, p_c, p_b]
    hits = 0
    for _ in range(n_rep):
        draw = rng.choice(3, size=n, p=probs)
        c = int(np.sum(draw == 1))
        b = int(np.sum(draw == 2))
        if mcnemar_exact_p(b, c) < alpha:
            hits += 1
    return hits / n_rep


def required_n(p_disc, delta, target=0.80, seed=0, nmax=2000):
    for n in range(10, nmax + 1, 5):
        if power_at(n, p_disc, delta, seed=seed) >= target:
            return n
    return None


def min_detectable_delta(n, p_disc, target=0.80, seed=0):
    lo, hi = 0.0, min(p_disc, 1.0)
    best = None
    for _ in range(24):
        mid = (lo + hi) / 2
        if power_at(n, p_disc, mid, seed=seed) >= target:
            best = mid
            hi = mid
        else:
            lo = mid
    return best


def p_disc_from_run(run_dir, base_field, arm_field, thr=0.5):
    f = glob.glob(os.path.join(run_dir, "raw.jsonl"))
    if not f:
        raise FileNotFoundError(f"no raw.jsonl in {run_dir}")
    b = c = n = 0
    for line in open(f[0]):
        r = json.loads(line)
        bs, as_ = r.get(base_field), r.get(arm_field)
        if bs is None or as_ is None:
            continue
        bb = 1 if bs >= thr else 0
        aa = 1 if as_ >= thr else 0
        if bb == 1 and aa == 0:
            b += 1
        elif bb == 0 and aa == 1:
            c += 1
        n += 1
    return (b + c) / n if n else 0.0, b, c, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p-disc", type=float, default=None, help="discordant rate (b+c)/n")
    ap.add_argument("--from-run", default=None, help="phase4/5 run dir to estimate p_disc from")
    ap.add_argument("--base-field", default="base_score")
    ap.add_argument("--arm-field", default="refusal_ablate_score")
    ap.add_argument("--corpus-n", type=int, default=40, help="available paired n on the new corpus")
    ap.add_argument("--seed", type=int, default=20260815)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.from_run:
        p_disc, b, c, n = p_disc_from_run(args.from_run, args.base_field, args.arm_field)
        src = f"{os.path.basename(args.from_run)} ({args.arm_field}): b={b} c={c} n={n}"
    elif args.p_disc is not None:
        p_disc, src = args.p_disc, f"supplied --p-disc {args.p_disc}"
    else:
        # empirical default from the clearharm refusal-ablation arm (strong lever)
        p_disc, src = 0.30, "default 0.30 (prior refusal-arm discordant rate)"

    print(f"Phase-10 power analysis | p_disc={p_disc:.3f} | source: {src}")
    res = {"p_disc": p_disc, "source": src, "required_n": {}, "corpus_n": args.corpus_n}
    for delta in (0.10, 0.15, 0.20):
        n_req = required_n(p_disc, delta, seed=args.seed)
        res["required_n"][f"{delta:.2f}"] = n_req
        print(f"  ΔASR {delta:.2f}: n for 80% power = {n_req if n_req else '>2000'}")
    mdd = min_detectable_delta(args.corpus_n, p_disc, seed=args.seed)
    res["min_detectable_delta_at_corpus_n"] = mdd
    pw10 = power_at(args.corpus_n, p_disc, 0.10, seed=args.seed)
    res["power_at_corpus_n_delta0.10"] = pw10
    mdd_s = f"{mdd:.3f}" if mdd is not None else ">p_disc (unreachable at this n)"
    print(f"  at corpus n={args.corpus_n}: min detectable ΔASR (80% power) = "
          f"{mdd_s}; power at ΔASR=0.10 = {pw10:.2f}")
    if args.out:
        d = os.path.dirname(args.out)
        if d:
            os.makedirs(d, exist_ok=True)
        json.dump(res, open(args.out, "w"), indent=2)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
