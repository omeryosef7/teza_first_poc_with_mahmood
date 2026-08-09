#!/usr/bin/env python3
"""Paired statistics aggregator for the Gate-7 v3 attack-objective matrix (NEXT sprint).

The eval driver (26_eval_p9_gcg_heldout_asr.py) emits POINT ASR only. This script adds the
inferential layer the plan requires (§1 statistics): per-arm ASR + Wilson CI, and for every
mechanism-vs-control arm PAIR (aligned by task_id on the SAME split), a paired bootstrap CI on
ΔASR, an exact McNemar test on the paired binary outcomes, and across-seed aggregation
(mean ASR + between-seed spread). Reads ONLY scalar fields from FREE_GENERATION_RESULTS.jsonl
(task_id, strongreject_is_success, strongreject_score, finish_reason) — never the generation text.

Usage:
  python scripts/analyze_gate7_matrix.py --glob 'outputs/stage_gcg_full/phase9b_v3_*' \
      --split test --out reports/GATE7_V3_MATRIX_STATS.json
  # or explicit dirs:
  python scripts/analyze_gate7_matrix.py --dirs dirA dirB ... --split test
"""
import argparse, glob, json, math, os, re, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - half) / d, (c + half) / d)


def load_rows(run_dir, split):
    """Return {task_id: (is_success:int, score:float, finish:str)} for rows in `split`.
    Reads only scalar fields; ignores generation_text entirely."""
    f = os.path.join(run_dir, "FREE_GENERATION_RESULTS.jsonl")
    out = {}
    if not os.path.exists(f):
        return out
    for line in open(f):
        try:
            r = json.loads(line)
        except Exception:
            continue
        # split may not be stored per-row; caller filters by the eval summary's split instead.
        tid = r.get("task_id")
        succ = r.get("strongreject_is_success")
        if tid is None or succ is None:
            continue
        out[tid] = (int(bool(succ)), r.get("strongreject_score"), r.get("finish_reason"))
    return out


def mcnemar_exact(b, c):
    """Exact two-sided McNemar p on discordant counts b, c (binomial n=b+c, p=0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    from math import comb
    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def paired_bootstrap_delta(a, b, task_ids, n_boot=10000, seed=1234):
    """Paired bootstrap CI on mean(a) - mean(b) over shared task_ids. a,b: {tid:0/1}."""
    import random
    rng = random.Random(seed)
    xs = [(a[t], b[t]) for t in task_ids]
    n = len(xs)
    if n == 0:
        return (float("nan"), (float("nan"), float("nan")))
    point = sum(x[0] - x[1] for x in xs) / n
    deltas = []
    for _ in range(n_boot):
        s = 0
        for _ in range(n):
            x = xs[rng.randrange(n)]
            s += x[0] - x[1]
        deltas.append(s / n)
    deltas.sort()
    lo = deltas[int(0.025 * n_boot)]
    hi = deltas[int(0.975 * n_boot)]
    return (point, (lo, hi))


def parse_meta(run_dir):
    """Extract arm slug + seed from the run-dir name."""
    base = os.path.basename(run_dir.rstrip("/"))
    m = re.search(r"seed(\d+)", base)
    seed = int(m.group(1)) if m else None
    slug = re.sub(r"_seed\d+$", "", base)
    return slug, seed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=None)
    ap.add_argument("--dirs", nargs="*", default=None)
    ap.add_argument("--split", default="test", help="informational label; filtering is by summary")
    ap.add_argument("--pairs", nargs="*", default=None,
                    help="explicit 'armslugA:armslugB' comparisons; default = auto refusal-vs-rand")
    ap.add_argument("--out", default=os.path.join(HERE, "reports/GATE7_V3_MATRIX_STATS.json"))
    args = ap.parse_args()

    run_dirs = args.dirs or sorted(glob.glob(args.glob)) if (args.dirs or args.glob) else []
    run_dirs = [d for d in run_dirs if os.path.isdir(d)]
    if not run_dirs:
        print("[stats] no run dirs matched"); return

    # per-run summary + rows
    per_run = {}
    for d in run_dirs:
        slug, seed = parse_meta(d)
        summ = {}
        sp = os.path.join(d, "p9_heldout_asr_summary.json")
        if os.path.exists(sp):
            summ = json.load(open(sp))
        rows = load_rows(d, args.split)
        per_run[d] = {"slug": slug, "seed": seed, "summary": summ, "rows": rows}

    # aggregate per slug across seeds
    by_slug = collections.defaultdict(list)
    for d, info in per_run.items():
        by_slug[info["slug"]].append(d)

    arms = {}
    for slug, dirs in sorted(by_slug.items()):
        seed_asrs = []
        for d in dirs:
            rows = per_run[d]["rows"]
            n = len(rows); k = sum(v[0] for v in rows.values())
            asr = k / n if n else float("nan")
            lo, hi = wilson_ci(k, n)
            seed_asrs.append({"dir": os.path.basename(d), "seed": per_run[d]["seed"],
                              "n": n, "k": k, "asr": asr, "wilson95": [lo, hi],
                              "refusal_rate": per_run[d]["summary"].get("refusal_rate"),
                              "empty_rate": per_run[d]["summary"].get("empty_rate")})
        mean_asr = sum(s["asr"] for s in seed_asrs) / len(seed_asrs) if seed_asrs else float("nan")
        arms[slug] = {"n_seeds": len(seed_asrs), "mean_asr": mean_asr,
                      "per_seed": seed_asrs,
                      "asr_spread": (max(s["asr"] for s in seed_asrs) - min(s["asr"] for s in seed_asrs))
                      if seed_asrs else float("nan")}

    # auto pairs: any slug containing 'refusal_down'/'jacobian'/'concept' vs its 'rand' counterpart
    pairs = []
    if args.pairs:
        for p in args.pairs:
            a, b = p.split(":"); pairs.append((a, b))
    else:
        slugs = list(arms.keys())
        for s in slugs:
            if "rand" in s:
                continue
            # find a rand sibling sharing the layer token
            m = re.search(r"L(\d+)", s)
            lay = m.group(1) if m else None
            for t in slugs:
                if "rand" in t and (lay is None or ("L" + lay) in t):
                    pairs.append((s, t))

    pair_stats = []
    for a_slug, b_slug in pairs:
        # match seeds present in both
        a_dirs = {per_run[d]["seed"]: d for d in by_slug.get(a_slug, [])}
        b_dirs = {per_run[d]["seed"]: d for d in by_slug.get(b_slug, [])}
        common_seeds = sorted(set(a_dirs) & set(b_dirs))
        per_seed = []
        for sd in common_seeds:
            ra = {t: v[0] for t, v in per_run[a_dirs[sd]]["rows"].items()}
            rb = {t: v[0] for t, v in per_run[b_dirs[sd]]["rows"].items()}
            common = sorted(set(ra) & set(rb))
            b_disc = sum(1 for t in common if ra[t] == 1 and rb[t] == 0)
            c_disc = sum(1 for t in common if ra[t] == 0 and rb[t] == 1)
            point, (lo, hi) = paired_bootstrap_delta(ra, rb, common)
            per_seed.append({"seed": sd, "n_paired": len(common),
                             "delta_asr": point, "boot95": [lo, hi],
                             "mcnemar_b": b_disc, "mcnemar_c": c_disc,
                             "mcnemar_p": mcnemar_exact(b_disc, c_disc)})
        pair_stats.append({"arm": a_slug, "control": b_slug, "seeds": common_seeds,
                           "per_seed": per_seed})

    result = {"split": args.split, "n_runs": len(run_dirs), "arms": arms, "pairs": pair_stats}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(result, open(args.out, "w"), indent=2)

    # scalar console report
    print(f"[stats] split={args.split} runs={len(run_dirs)}")
    for slug, a in sorted(arms.items()):
        print(f"  {slug:55s} seeds={a['n_seeds']} mean_asr={a['mean_asr']:.3f} spread={a['asr_spread']:.3f}")
    for ps in pair_stats:
        print(f"  PAIR {ps['arm']} vs {ps['control']}:")
        for s in ps["per_seed"]:
            print(f"    seed{s['seed']} dASR={s['delta_asr']:+.3f} "
                  f"boot95=[{s['boot95'][0]:+.3f},{s['boot95'][1]:+.3f}] "
                  f"McNemar b={s['mcnemar_b']} c={s['mcnemar_c']} p={s['mcnemar_p']:.4f}")
    print(f"[out] {args.out}")


if __name__ == "__main__":
    main()
