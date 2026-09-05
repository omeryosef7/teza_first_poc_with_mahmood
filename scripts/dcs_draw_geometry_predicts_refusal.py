#!/usr/bin/env python3
"""DCS: is a control draw's REFUSAL LOAD predictable from its GEOMETRY? (feasibility, exploratory)

WHY. `R-061` measured the binding constraint on the behavioural half: the dose-matched controls
induce refusal (+35/+133/+200), refusal suppresses attack, and the between-control spread EXCEEDS
the effect -- so which control you draw decides the p-value. `C-023` showed a control matched on
OBSERVED refusal is post-hoc selection. A control matched on PREDICTED refusal is not, but needs a
predictor, which `B-007` was thought to block. `R-066` closed `B-007` on behavioural arms: every
row carries the drawn positions verbatim. This asks the prior question -- is there anything to
predict? -- before any GPU is spent on a design.

⛔ THE POOLED WITHIN-PROMPT TEST IS CONFOUNDED WITH ARM IDENTITY, and is reported here only as the
quantity that misled me. With k draws there are only k independent refusal loads; the three PR-024
arms refuse at 23.9 / 15.4 / 29.7 %, and each arm's rows share one seed, so ANY feature that differs
between arms inherits that gap and reaches the permutation floor at n = 3480 rows. THE ARM IS THE
INDEPENDENT UNIT. The primary is therefore the WITHIN-ARM correlation plus sign consistency across
arms; the pooled figure is printed with a CONFOUNDED label and no verdict attached.

DEGENERATE FEATURES ARE NOT NULL RESULTS. A feature can be constant inside an arm (`min_dist_to_query`
has ONE distinct value across all 1160 rows of `dcsp24_d3`), and a rho of exactly 0.0000 there means
"no variance to correlate", not "no effect". Any feature whose within-arm sd is ~0 is reported as
DEGENERATE and excluded from the sign test rather than counted as a null.

THE ESTIMAND IS WITHIN-PROMPT. A control draw is chosen with the prompt set held fixed, so the
question is whether geometry moves refusal FOR A GIVEN PROMPT, not whether hard prompts get refused
(they do, and that variance is not ours to exploit). Both the statistic and the null are therefore
conditioned on `prompt_id`:

  * statistic -- Spearman rho between prompt-demeaned feature and prompt-demeaned `refused`;
  * null -- permute the ARM LABEL within each prompt. Under "geometry is irrelevant" the draws a
    prompt received are exchangeable, so this is the exact null for the question asked.

SELF-CHECK. The script refuses to report without first calibrating its own null on label-shuffled
data: a test that cannot fail is not evidence (this phase has had three instruments fail their own
audit -- `A-012`, `C-034`, `C-040`).

EXPLORATORY. Nothing here licenses a design. A predicted-refusal control needs its own
preregistration with out-of-sample (held-out arm) validation.
"""
import argparse, glob, json, os, random, statistics as st, sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def spearman(xs, ys):
    """Tie-aware Spearman via Pearson on ranks (scipy is not a dependency of this repo path)."""
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    mx, my = st.fmean(rx), st.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    return (num / (dx * dy)) if dx > 0 and dy > 0 else 0.0


def features(pos, demo_lo, demo_hi, q_lo, q_hi, seq_len):
    """Geometry of ONE draw. Every feature is a property of the MASK, computable before any
    generation -- nothing here may depend on the completion, or the control becomes post-hoc."""
    n = len(pos)
    if n == 0 or seq_len <= 0:
        return None
    p = sorted(pos)
    runs = 1 + sum(1 for a, b in zip(p, p[1:]) if b != a + 1)
    before = sum(1 for x in p if x < demo_lo)
    between = sum(1 for x in p if demo_hi < x < q_lo)
    return {
        "frac_before_demo": before / n,
        "frac_between_demo_and_query": between / n,
        "mean_norm_position": st.fmean(x / seq_len for x in p),
        "frac_first_quarter": sum(1 for x in p if x < 0.25 * seq_len) / n,
        "min_dist_to_query": min((q_lo - x) for x in p if x < q_lo) if any(x < q_lo for x in p) else 0,
        "n_runs_norm": runs / n,
        "spread_norm": (max(p) - min(p)) / seq_len,
    }


def load(score_glob, judge_glob):
    """Join judged `refused` to the score arm's persisted draw geometry, on prompt_id."""
    def newest_done(g):
        d = sorted(x for x in glob.glob(os.path.join(REPO, g)) if os.path.isfile(x + "/DONE.json"))
        return d[-1] if d else None
    sd, jd = newest_done(score_glob), newest_done(judge_glob)
    if not sd or not jd:
        return None, None, None
    refused = {}
    for line in open(jd + "/results.jsonl"):
        r = json.loads(line)
        refused[r["prompt_id"]] = bool(r["refused"])
    rows = []
    for line in open(sd + "/results.jsonl"):
        r = json.loads(line)
        cd = r.get("control_draw")
        if not cd:
            sys.exit(f"{os.path.basename(sd)} carries no per-row control_draw -- readout arm? (R-066)")
        rec = list(cd.values())[0]
        dlo, dhi = r["demo_span_bounds"]
        qlo, qhi = r["query_span_bounds"]
        f = features(rec["positions"], dlo, dhi, qlo, qhi, r["seq_len"])
        pid = r["prompt_id"]
        if f is None or pid not in refused:
            continue
        rows.append({"prompt_id": pid, "refused": float(refused[pid]), **f})
    return rows, os.path.basename(sd), os.path.basename(jd)


def within_prompt_rho(rows, feat):
    """Demean feature and outcome by prompt, then correlate the residuals."""
    fm, om = defaultdict(list), defaultdict(list)
    for r in rows:
        fm[r["prompt_id"]].append(r[feat])
        om[r["prompt_id"]].append(r["refused"])
    xs, ys = [], []
    for pid in fm:
        if len(fm[pid]) < 2:
            continue                      # a prompt seen in one arm carries no within-information
        mf, mo = st.fmean(fm[pid]), st.fmean(om[pid])
        xs += [v - mf for v in fm[pid]]
        ys += [v - mo for v in om[pid]]
    return (spearman(xs, ys), len(xs)) if xs else (0.0, 0)


def perm_p(rows, feat, observed, n_perm, seed):
    """Permute the ARM LABEL within prompt: under the null the draws a prompt got are exchangeable."""
    rng = random.Random(seed)
    by = defaultdict(list)
    for r in rows:
        by[r["prompt_id"]].append(r)
    ge = 0
    for _ in range(n_perm):
        shuffled = []
        for pid, group in by.items():
            feats = [g[feat] for g in group]
            rng.shuffle(feats)
            shuffled += [{"prompt_id": pid, feat: f, "refused": g["refused"]}
                         for f, g in zip(feats, group)]
        r, _ = within_prompt_rho(shuffled, feat)
        ge += abs(r) >= abs(observed) - 1e-12
    return (ge + 1) / (n_perm + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+",
                    default=["dcsp24_d1:p24j_dcsp24_d1", "dcsp24_d2:p24j_dcsp24_d2",
                             "dcsp24_d3:p24j_dcsp24_d3"])
    ap.add_argument("--n-perm", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260905)
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_draw_geometry_refusal.json")
    a = ap.parse_args()

    rows, prov = [], []
    for spec in a.arms:
        s, j = spec.split(":", 1)
        got, sd, jd = load(f"outputs/boombness/score_behavior/{s}_*",
                           f"outputs/boombness/judge/{j}_*")
        if got is None:
            print(f"  SKIP {spec}: no finished pair"); continue
        for r in got:
            r["_arm"] = s
        rows += got
        prov.append({"spec": spec, "score_dir": sd, "judge_dir": jd, "n_rows": len(got),
                     "refused": sum(r["refused"] for r in got)})
        print(f"  {spec:28s} n={len(got):5d}  refused={int(sum(r['refused'] for r in got))}")
    if len(prov) < 2:
        sys.exit("need at least two arms for a within-prompt contrast")

    feats = [k for k in rows[0] if k not in ("prompt_id", "refused", "_arm")]

    # --- SELF-CHECK: the null must not reject on data with the signal destroyed -------------
    rng = random.Random(a.seed ^ 0x5EED)
    shuffled = [dict(r) for r in rows]
    vals = [r["refused"] for r in shuffled]
    rng.shuffle(vals)
    for r, v in zip(shuffled, vals):
        r["refused"] = v
    cal = []
    for f in feats:
        obs, _ = within_prompt_rho(shuffled, f)
        cal.append(perm_p(shuffled, f, obs, 300, a.seed))
    n_false = sum(1 for p in cal if p < 0.05)
    print(f"\nNULL CALIBRATION (outcome shuffled, {len(feats)} features): "
          f"{n_false} reject at 0.05 (expect ~{0.05*len(feats):.1f})")
    if n_false > 3:
        sys.exit("ABORT: the test rejects on data with no signal -- the instrument is broken")

    print(f"\nWITHIN-PROMPT geometry -> refusal   ({a.n_perm} within-prompt permutations)")
    out = []
    for f in feats:
        rho, n = within_prompt_rho(rows, f)
        p = perm_p(rows, f, rho, a.n_perm, a.seed)
        out.append({"feature": f, "rho_within": rho, "n_residuals": n, "p_perm": p})
        print(f"  {f:30s} rho={rho:+.4f}  p={p:.4f}  n={n}")

    # ---- PRIMARY: within-arm, residualised on prompt difficulty, arm as the unit -----------
    base = {}
    bj = sorted(x for x in glob.glob(os.path.join(REPO, "outputs/boombness/judge/p24j_dcsp24_base_*"))
                if os.path.isfile(x + "/DONE.json"))
    if bj:
        for line in open(bj[-1] + "/results.jsonl"):
            r = json.loads(line)
            base[r["prompt_id"]] = float(r["refused"])
    by_arm = defaultdict(list)
    for r in rows:
        by_arm[r["_arm"]].append(r)
    print(f"\nPRIMARY -- WITHIN-ARM (arm is the independent unit, k={len(by_arm)})")
    within, degen = {}, defaultdict(list)
    for arm, ar in sorted(by_arm.items()):
        ys = [r["refused"] - base.get(r["prompt_id"], 0.0) for r in ar]
        within[arm] = {}
        for f in feats:
            xs = [r[f] for r in ar]
            sd = st.pstdev(xs)
            if sd < 1e-9 or len(set(round(x, 9) for x in xs)) < 3:
                degen[f].append(arm)
                within[arm][f] = None
            else:
                within[arm][f] = spearman(xs, ys)
        shown = "  ".join(f"{(within[arm][f] if within[arm][f] is not None else float('nan')):+.3f}"
                          for f in feats)
        print(f"  {arm:14s} n={len(ar):5d} {shown}")

    print(f"\n  sign consistency across the {len(by_arm)} arms "
          f"(attainable sign-test floor = {2/2**len(by_arm):.4f}):")
    sign_ok = []
    for f in feats:
        v = [within[a][f] for a in within if within[a][f] is not None]
        if f in degen:
            print(f"    {f:30s} DEGENERATE in {','.join(degen[f])} -- excluded, NOT a null")
            continue
        cons = len(v) == len(by_arm) and (all(x > 0 for x in v) or all(x < 0 for x in v))
        sign_ok.append((f, cons, st.fmean(v)))
        print(f"    {f:30s} {'  '.join(f'{x:+.3f}' for x in v)}  consistent={cons}  mean={st.fmean(v):+.3f}")
    n_cons = sum(1 for _, c, _ in sign_ok if c)
    print(f"\n  {n_cons}/{len(sign_ok)} non-degenerate features sign-consistent across all {len(by_arm)} arms")

    best = min(out, key=lambda d: d["p_perm"])
    floor = 1.0 / (a.n_perm + 1)
    bonf = 0.05 / len(feats)
    # The verdict comes from the WITHIN-ARM primary, never from the confounded pooled test.
    verdict = ("WITHIN-ARM SIGNAL" if n_cons >= 1 and len(by_arm) >= 6
               else "NO USABLE WITHIN-ARM SIGNAL (pooled result is an ARM-LEVEL ARTIFACT)")
    print(f"\n  [pooled test is CONFOUNDED -- no verdict drawn from it] "
          f"p-floor={floor:.5f}, Bonferroni={bonf:.4f} over {len(feats)} features; "
          f"best {best['feature']} rho={best['rho_within']:+.4f} p={best['p_perm']:.4f}")
    print(f"\n  VERDICT (EXPLORATORY, feasibility only): {verdict}")
    if len(by_arm) < 6:
        print(f"  ⚠ k={len(by_arm)} arms: the sign test cannot reach 0.05 "
              f"(floor {2/2**len(by_arm):.3f}). Re-run at k=8 once PR-028 is judged.")

    os.makedirs(os.path.join(REPO, os.path.dirname(a.out)), exist_ok=True)
    json.dump({"provenance": prov, "pooled_CONFOUNDED": out,
               "within_arm": {a: within[a] for a in within},
               "degenerate_features": {f: degen[f] for f in degen},
               "n_sign_consistent": n_cons, "k_arms": len(by_arm),
               "sign_test_floor": 2 / 2 ** len(by_arm), "features": out, "n_perm": a.n_perm, "seed": a.seed,
               "p_floor": floor, "bonferroni_alpha": bonf, "verdict": verdict,
               "null_calibration_false_rejects": n_false,
               "note": "EXPLORATORY feasibility. Does not license a design; a predicted-refusal "
                       "control needs its own preregistration with held-out-arm validation."},
              open(os.path.join(REPO, a.out), "w"), indent=1)
    print(f"\n-> {a.out}")


if __name__ == "__main__":
    main()
