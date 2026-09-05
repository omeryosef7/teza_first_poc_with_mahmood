#!/usr/bin/env python3
"""DCS-A-014: adversarial audit of `dcs_draw_geometry_predicts_refusal.py` (the R-067 analyzer).

R-067 returned NO USABLE WITHIN-ARM SIGNAL. That verdict is only worth having if the instrument
COULD have returned the opposite. This mutates the DATA (never the analyzer) and asserts the
analyzer changes its mind in the direction the mutation implies. A guard that never fires is not
evidence -- three instruments have failed their own audit this phase (A-012, C-034, C-040).

M1 planted signal      -- a feature perfectly ranked with refusal INSIDE every arm must come out
                          sign-consistent. If it does not, the null verdict is vacuous.
M2 planted anti-signal -- the same with the sign flipped, to prove the direction is read, not assumed.
M3 constant feature    -- a feature with one value inside one arm must be flagged DEGENERATE and
                          excluded, never scored 0.0 and counted as a null (this is exactly what
                          min_dist_to_query does in d3).
M4 pure noise          -- a random feature must NOT come out sign-consistent across arms.
M5 null calibration    -- shuffling the outcome must leave the calibration near its nominal rate.
"""
import importlib.util, random, statistics as st, sys
from collections import defaultdict

spec = importlib.util.spec_from_file_location("g", "scripts/dcs_draw_geometry_predicts_refusal.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

ARMS = [("dcsp24_d1", "p24j_dcsp24_d1"), ("dcsp24_d2", "p24j_dcsp24_d2"),
        ("dcsp24_d3", "p24j_dcsp24_d3")]


def load_all():
    rows = []
    for s, j in ARMS:
        got, _, _ = g.load(f"outputs/boombness/score_behavior/{s}_*",
                           f"outputs/boombness/judge/{j}_*")
        for r in got:
            r["_arm"] = s
        rows += got
    return rows


def within_arm_rhos(rows, feat, base):
    """Exactly the analyzer's primary: within arm, residualised on baseline refusal."""
    by = defaultdict(list)
    for r in rows:
        by[r["_arm"]].append(r)
    out = {}
    for arm, ar in by.items():
        xs = [r[feat] for r in ar]
        ys = [r["refused"] - base.get(r["prompt_id"], 0.0) for r in ar]
        degenerate = st.pstdev(xs) < 1e-9 or len(set(round(x, 9) for x in xs)) < 3
        out[arm] = None if degenerate else g.spearman(xs, ys)
    return out


def consistent(rhos):
    v = [x for x in rhos.values() if x is not None]
    return len(v) == len(rhos) and (all(x > 0 for x in v) or all(x < 0 for x in v))


def main():
    rows = load_all()
    base = {}
    import glob, json, os
    bj = sorted(x for x in glob.glob("outputs/boombness/judge/p24j_dcsp24_base_*")
                if os.path.isfile(x + "/DONE.json"))[-1]
    for line in open(bj + "/results.jsonl"):
        r = json.loads(line)
        base[r["prompt_id"]] = float(r["refused"])
    rng = random.Random(20260905)
    results = []

    # M1 / M2 -- plant a feature that IS the (residualised) outcome, +/- .
    for name, sign in (("M1 planted signal (+)", 1.0), ("M2 planted anti-signal (-)", -1.0)):
        for r in rows:
            r["_planted"] = sign * (r["refused"] - base.get(r["prompt_id"], 0.0)) \
                            + rng.gauss(0, 0.01)
        rh = within_arm_rhos(rows, "_planted", base)
        v = [x for x in rh.values() if x is not None]
        ok = consistent(rh) and all((x > 0) == (sign > 0) for x in v)
        results.append((name, ok, "  ".join(f"{x:+.3f}" for x in v)))

    # M3 -- a feature that is constant inside ONE arm must be excluded, not scored.
    for r in rows:
        r["_const"] = 1.0 if r["_arm"] == "dcsp24_d3" else rng.random()
    rh = within_arm_rhos(rows, "_const", base)
    ok = rh["dcsp24_d3"] is None and not consistent(rh)
    results.append(("M3 constant-in-one-arm -> DEGENERATE", ok,
                    f"d3={rh['dcsp24_d3']}  consistent={consistent(rh)}"))

    # M4 -- pure noise must not read as consistent.
    # THE ACCEPTANCE BAND IS DERIVED FROM k AND THE TRIAL COUNT, NEVER HARDCODED. A fixed
    # threshold is only valid at one k -- that is C-034, which produced a false ANTI-CONSERVATIVE
    # flag from a band written for a different N. With k arms, P(all k rhos share a sign) = 2/2^k,
    # so at k=3 a QUARTER of pure-noise features look "consistent" by construction.
    n_trials = 20
    p_chance = 2 / 2 ** len(ARMS)
    mu = n_trials * p_chance
    sd = (n_trials * p_chance * (1 - p_chance)) ** 0.5
    hi = mu + 3 * sd
    n_cons = 0
    for t in range(n_trials):
        for r in rows:
            r["_noise"] = rng.random()
        n_cons += consistent(within_arm_rhos(rows, "_noise", base))
    ok = n_cons <= hi
    results.append((f"M4 noise consistency ~ chance (k={len(ARMS)})", ok,
                    f"{n_cons}/{n_trials} consistent; chance={p_chance:.2f} => "
                    f"expect {mu:.1f}, allow <={hi:.1f}"))

    # M5 -- null calibration on a shuffled outcome stays near nominal.
    sh = [dict(r) for r in rows]
    vals = [r["refused"] for r in sh]
    rng.shuffle(vals)
    for r, v in zip(sh, vals):
        r["refused"] = v
    feats = [k for k in rows[0] if k not in ("prompt_id", "refused", "_arm") and not k.startswith("_")]
    false_rej = sum(1 for f in feats
                    if g.perm_p(sh, f, g.within_prompt_rho(sh, f)[0], 200, 7) < 0.05)
    ok = false_rej <= 3
    results.append(("M5 null calibration on shuffled outcome", ok,
                    f"{false_rej}/{len(feats)} reject at 0.05 (expect ~{0.05*len(feats):.1f})"))

    print(f"{'mutation':44s} {'result':8s} detail")
    for name, ok, detail in results:
        print(f"{name:44s} {'PASS' if ok else 'FAIL':8s} {detail}")
    n_ok = sum(1 for _, ok, _ in results if ok)
    print(f"\nA-014: {n_ok}/{len(results)} mutations behaved as required")
    if n_ok != len(results):
        print("\n=> The R-067 verdict is NOT trustworthy until these are explained.")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
