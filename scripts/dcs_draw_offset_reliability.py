#!/usr/bin/env python3
"""DCS-PR-030: is the between-control spread a STABLE PROPERTY OF THE DRAW, or noise?

WHY THIS GATES PR-029. R-075 measured a between-control sd of 0.0783 and PR-029 is buying 24 more
draws to divide it by sqrt(K). That arithmetic is only valid if the 0.0783 is a real per-draw
OFFSET. If most of it is within-arm sampling noise or judge noise, then adding draws does not shrink
the thing that matters and the K ladder is mis-specified -- 55 GPU-h spent on the wrong quantity.
The phase has quoted 0.0295 -> 0.0586 -> 0.0783 as if each were pure draw heterogeneity, and has
never subtracted the row and judge floors.

THREE MEASUREMENTS, all CPU, all on data already on disk:

(a) SPLIT-HALF RELIABILITY. Split the 116 domains in half; compute each arm's ASR on each half;
    correlate half-A against half-B ACROSS ARMS (unit = arm). Spearman-Brown corrects the
    half-length attenuation. Repeated over many random splits: report the DISTRIBUTION, never one
    estimate (R-051/`one-estimate-is-not-stability`). Null by permuting arm labels.

(b) VARIANCE DECOMPOSITION of the observed between-arm variance into
      draw offset  +  within-arm sampling  +  judge instability
    Sampling is computed WITH the design effect from the measured domain ICC -- rows cluster by
    domain, so p(1-p)/n understates it. Judge variance is taken from R-074's re-judge of the SAME
    generations (5 arms, byte-identical text), which is the only empirical judge floor available;
    the sd of the per-arm ASR CHANGE is sqrt(2)x the per-judging sd, so it is halved in variance.

⛔ DECLARED BEFORE LOOKING (PR-030):
   * SB-corrected median rho >= 0.70 AND draw-offset fraction >= 0.50  => the offset is REAL, the
     K ladder is well specified, PR-029 proceeds.
   * median rho < 0.50 with a permutation CI containing zero AND draw fraction < 0.50 => NO stable
     draw-level quantity: stop buying draws, PR-029 is cancelled, and R-063's arm-level calibration
     loses its footing.
   * anything between => INDETERMINATE, reported as such, PR-029 continues but the K ladder stops
     at 32 regardless of outcome.
"""
import argparse, glob, importlib.util, json, math, os, random, statistics as st, sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("cdt", os.path.join(REPO, "scripts/cds_domain_test.py"))
cdt = importlib.util.module_from_spec(_s); _s.loader.exec_module(cdt)


def newest(pat):
    d = sorted(x for x in glob.glob(os.path.join(REPO, pat)) if os.path.isfile(x + "/DONE.json"))
    return d[-1] if d else None


def spearman(xs, ys):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0]*len(v); i = 0
        while i < len(o):
            j = i
            while j+1 < len(o) and v[o[j+1]] == v[o[i]]: j += 1
            a = (i+j)/2.0 + 1.0
            for k in range(i, j+1): r[o[k]] = a
            i = j+1
        return r
    rx, ry = rank(xs), rank(ys)
    mx, my = st.fmean(rx), st.fmean(ry)
    num = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    dx = sum((a-mx)**2 for a in rx)**0.5; dy = sum((b-my)**2 for b in ry)**0.5
    return num/(dx*dy) if dx > 0 and dy > 0 else 0.0


def icc_oneway(by_domain):
    groups = [v for v in by_domain.values() if len(v) > 1]
    if not groups: return 0.0
    k = len(groups); m = st.fmean(len(g) for g in groups)
    gm = st.fmean(x for g in groups for x in g)
    msb = sum(len(g)*(st.fmean(g)-gm)**2 for g in groups)/(k-1) if k > 1 else 0.0
    within = [ (x-st.fmean(g))**2 for g in groups for x in g ]
    dfw = sum(len(g) for g in groups) - k
    msw = sum(within)/dfw if dfw > 0 else 0.0
    if msb + msw == 0: return 0.0
    return max(0.0, (msb-msw)/(msb+(m-1)*msw))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", nargs="+", default=[
        "p28j_dcsp24_d1", "p28j_dcsp24_d2", "p28j_dcsp24_d3",
        "p28j_dcsp28_s20260905_d1", "p28j_dcsp28_s20260905_d2", "p28j_dcsp28_s20260905_d3",
        "p28j_dcsp28_s20260906_d1", "p28j_dcsp28_s20260906_d2"])
    ap.add_argument("--n-splits", type=int, default=400)
    ap.add_argument("--seed", type=int, default=20260905)
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_draw_offset_reliability.json")
    a = ap.parse_args()

    arms = {}
    for tag in a.controls:
        d = newest(f"outputs/boombness/judge/{tag}_*")
        if not d: sys.exit(f"missing judged arm {tag}")
        rows = cdt.load_arm(d)
        by = defaultdict(list)
        for pid, r in rows.items(): by[r["domain"]].append(r["attack"])
        arms[tag] = by
    doms = sorted(set.intersection(*[set(b) for b in arms.values()]))
    K = len(arms)
    print(f"K={K} control arms, {len(doms)} common domains")
    asr = {t: st.fmean(x for d_ in doms for x in arms[t][d_]) for t in arms}
    obs_sd = st.stdev(asr.values())
    print(f"between-arm ASR sd = {obs_sd:.4f}  (R-075 reported 0.0783)")

    # ---- (a) split-half reliability -------------------------------------------------------
    rng = random.Random(a.seed)
    rhos, null = [], []
    for _ in range(a.n_splits):
        sh = doms[:]; rng.shuffle(sh)
        A, B = sh[:len(sh)//2], sh[len(sh)//2:]
        xa = [st.fmean(x for d_ in A for x in arms[t][d_]) for t in arms]
        xb = [st.fmean(x for d_ in B for x in arms[t][d_]) for t in arms]
        r = spearman(xa, xb)
        rhos.append(2*r/(1+r) if r > -1 else -1.0)          # Spearman-Brown
        yb = xb[:]; rng.shuffle(yb)
        rn = spearman(xa, yb); null.append(2*rn/(1+rn) if rn > -1 else -1.0)
    rhos.sort(); null.sort()
    med = rhos[len(rhos)//2]
    lo, hi = rhos[int(0.025*len(rhos))], rhos[int(0.975*len(rhos))]
    nlo, nhi = null[int(0.025*len(null))], null[int(0.975*len(null))]
    print(f"\n(a) SPLIT-HALF, {a.n_splits} splits, Spearman-Brown corrected, unit = arm")
    print(f"    median rho = {med:+.3f}   95% band [{lo:+.3f}, {hi:+.3f}]")
    print(f"    permuted null median {null[len(null)//2]:+.3f}, band [{nlo:+.3f}, {nhi:+.3f}]")

    # ---- (b) variance decomposition -------------------------------------------------------
    pooled = defaultdict(list)
    for t in arms:
        for d_ in doms: pooled[(t, d_)] = arms[t][d_]
    icc = st.fmean([icc_oneway({d_: arms[t][d_] for d_ in doms}) for t in arms])
    m = st.fmean(len(arms[list(arms)[0]][d_]) for d_ in doms)
    n_rows = sum(len(arms[list(arms)[0]][d_]) for d_ in doms)
    p = st.fmean(asr.values())
    deff = 1 + (m-1)*icc
    var_sampling = p*(1-p)/n_rows*deff
    jd = os.path.join(REPO, "outputs/boombness/dcs_analysis/dcs_judge_drift_p24j_p28j.json")
    var_judge = float("nan")
    if os.path.exists(jd):
        ch = [r["d_asr"] for r in json.load(open(jd))["per_arm"]]
        var_judge = (st.stdev(ch)**2)/2.0          # sd of a CHANGE is sqrt(2)x per-judging sd
    var_obs = obs_sd**2
    var_draw = var_obs - var_sampling - (0 if math.isnan(var_judge) else var_judge)
    print(f"\n(b) VARIANCE DECOMPOSITION of the between-arm variance ({var_obs:.6f})")
    print(f"    mean ICC over arms {icc:.4f}, m={m:.1f} rows/domain => design effect {deff:.2f}")
    print(f"    within-arm sampling : {var_sampling:.6f}  ({100*var_sampling/var_obs:5.1f}%)")
    print(f"    judge instability   : {var_judge:.6f}  ({100*var_judge/var_obs:5.1f}%)  [from R-074]")
    print(f"    DRAW OFFSET         : {var_draw:.6f}  ({100*var_draw/var_obs:5.1f}%)")
    frac = var_draw/var_obs

    # ---- verdict (thresholds frozen in PR-030) --------------------------------------------
    if med >= 0.70 and frac >= 0.50:
        v = "REAL DRAW OFFSET -- the K ladder is well specified; PR-029 proceeds."
    elif med < 0.50 and lo <= nhi and frac < 0.50:
        v = "NO STABLE DRAW-LEVEL QUANTITY -- stop buying draws; PR-029 should be cancelled."
    else:
        v = "INDETERMINATE -- PR-029 continues, but the K ladder stops at 32 regardless."
    print(f"\nVERDICT: {v}")
    os.makedirs(os.path.join(REPO, os.path.dirname(a.out)), exist_ok=True)
    json.dump({"K": K, "n_domains": len(doms), "between_arm_sd": obs_sd,
               "split_half": {"median": med, "ci": [lo, hi], "null_ci": [nlo, nhi],
                              "n_splits": a.n_splits},
               "variance": {"observed": var_obs, "sampling": var_sampling, "judge": var_judge,
                            "draw": var_draw, "draw_fraction": frac, "icc": icc, "deff": deff},
               "verdict": v}, open(os.path.join(REPO, a.out), "w"), indent=1)
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
