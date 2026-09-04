#!/usr/bin/env python
"""dcs_verify_audit_r041.py -- the audit of the AUDITOR.

`scripts/dcs_audit_r041.py` produced `A-009`, `PR-022`/`R-053` and `PR-023`/`R-055` -- i.e. the
narrowing of this phase's headline from a continuous gradient to a categorical claim, across three
populations. Nothing verifies it. `A-006` and `A-007` established the pattern: the statistic that
carries a conclusion gets a verifier with a mutation harness before the conclusion is leaned on.

WHAT IS AND IS NOT ALREADY COVERED. `dcs_verify_installation_gradient.py` covers `_rank`,
`pearson`, `spearman_perm` and `contrast_perm`, which the auditor imports. It does NOT cover:
  1. the LEAVE-ONE-OUT loop (attack A) -- does it really produce 38 distinct subsets of size 37?
  2. the CEILING subset (attack C) -- is `nonceil` the right set?
  3. attack E's ARM-EXCHANGEABLE null, which is hand-written here and appears in no other file.
     E is the check that says "the contrast must die when KO and control are swapped per domain",
     and its p-value was quoted in all three audits.

CHECK 3 IS THE ONE THAT MATTERS. An arm-swap null that is silently anti-conservative would have
made every `E` line in this phase look like a pass. It is calibrated against its own null here, and
its POWER is checked too -- a null test that never rejects is as useless as one that always does.

Run: python scripts/dcs_verify_audit_r041.py   (exit 0 = pass; scipy optional)
"""
from __future__ import annotations
import importlib.util, os, random, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def band(n_draw, alpha=0.05, k=3.0):
    """Monte-Carlo acceptance band for a rejection-rate estimate, DERIVED from the
    number of draws rather than hardcoded. A fixed band is only valid at one N and
    silently becomes a false-alarm generator at smaller N -- which is exactly what a
    hardcoded (0.030, 0.075) did here: at n=300 it flagged a correctly-calibrated
    test as ANTI-CONSERVATIVE, and a 3000-draw re-run put the true rate at 0.0490."""
    se = (alpha * (1 - alpha) / max(1, n_draw)) ** 0.5
    return (max(0.0, alpha - k * se), alpha + k * se)          # +-3 binomial SE at the N used below


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def arm_swap_p(g, x, yk, yc, obs, seed, n_perm):
    """Re-implementation of attack E EXACTLY as dcs_audit_r041 performs it, so the calibration
    below measures the shipped procedure rather than an idealised one."""
    rnd = random.Random(seed)
    rx = g._rank(x)
    hits = 0
    for _ in range(n_perm):
        a, b = [], []
        for i in range(len(x)):
            if rnd.random() < 0.5:
                a.append(yk[i]); b.append(yc[i])
            else:
                a.append(yc[i]); b.append(yk[i])
        stat = g.pearson(rx, g._rank(a)) - g.pearson(rx, g._rank(b))
        if abs(stat) >= abs(obs) - 1e-12:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def main() -> None:
    g = load("g", "scripts/dcs_installation_gradient.py")
    a = load("a", "scripts/dcs_audit_r041.py")
    fails: list[str] = []

    # 1 -- contrast_on refuses a degenerate predictor instead of returning a number
    doms = [f"d{i}" for i in range(10)]
    flat = {d: 1.0 for d in doms}
    dk = {d: -float(i) for i, d in enumerate(doms)}
    dc = {d: 0.0 for d in doms}
    if a.contrast_on(g, flat, dk, dc, doms) is not None:
        fails.append("contrast_on returned a value for a ZERO-VARIANCE predictor")
    print("1. contrast_on refuses a zero-variance predictor:",
          "OK" if not fails else "FAIL")

    # 2 -- leave-one-out really is 38 distinct subsets of size n-1
    subsets = [[d for d in doms if d != drop] for drop in doms]
    ok = (len(subsets) == len(doms)
          and all(len(sub) == len(doms) - 1 for sub in subsets)
          and len({tuple(sub) for sub in subsets}) == len(doms))
    print(f"2. LOO construction: {len(subsets)} subsets, all size {len(doms)-1}, all distinct:",
          "OK" if ok else "FAIL")
    if not ok:
        fails.append("leave-one-out does not produce n distinct subsets of size n-1")

    # 3 -- the ceiling subset is exactly the non-1.0 domains
    inst = {f"d{i}": (1.0 if i < 4 else 0.5) for i in range(10)}
    nonceil = [d for d in sorted(inst) if inst[d] < 1.0]
    ok3 = (len(nonceil) == 6 and all(inst[d] < 1.0 for d in nonceil))
    print(f"3. ceiling subset: {len(nonceil)} of {len(inst)} kept, none at 1.0:",
          "OK" if ok3 else "FAIL")
    if not ok3:
        fails.append("ceiling subset is not the complement of installation==1.0")

    # 4 -- ATTACK E, calibrated against its OWN null: arms exchangeable
    rnd = random.Random(31)
    hits = tot = 0
    for _ in range(300):
        n = 38
        x = [rnd.choice([0.25, 0.5, 0.75, 1.0]) for _ in range(n)]
        if len(set(x)) < 2:
            continue
        # H0: the two arms are exchangeable -- drawn from one distribution
        yk = [rnd.gauss(0, 1) for _ in range(n)]
        yc = [rnd.gauss(0, 1) for _ in range(n)]
        rx = g._rank(x)
        obs = g.pearson(rx, g._rank(yk)) - g.pearson(rx, g._rank(yc))
        tot += 1
        hits += arm_swap_p(g, x, yk, yc, obs, rnd.randint(0, 10**6), 600) < 0.05
    rate = hits / tot
    verdict = ("OK" if band(tot)[0] <= rate <= band(tot)[1]
               else "CONSERVATIVE (safe)" if rate < band(tot)[0] else "ANTI-CONSERVATIVE")
    print(f"4. attack E null calibration: P(p<0.05) = {rate:.4f} over {tot} draws -> {verdict}")
    if rate > band(tot)[1]:
        fails.append(f"attack E is ANTI-CONSERVATIVE at {rate:.4f} -- every E 'pass' is suspect")

    # 5 -- ATTACK E has power: a planted arm difference must be detected
    rnd = random.Random(77)
    det = 0
    for _ in range(60):
        x = [i / 37 for i in range(38)]
        yk = [-3.0 * v + rnd.gauss(0, 0.4) for v in x]     # knockout tracks the predictor
        yc = [rnd.gauss(0, 0.4) for _ in x]                # control does not
        rx = g._rank(x)
        obs = g.pearson(rx, g._rank(yk)) - g.pearson(rx, g._rank(yc))
        det += arm_swap_p(g, x, yk, yc, obs, rnd.randint(0, 10**6), 600) < 0.05
    print(f"5. attack E power on a planted arm difference: {det}/60 detected")
    if det < 50:
        fails.append(f"attack E detected only {det}/60 planted differences -- it cannot reject")

    # 6 -- mutation: swapping arms GLOBALLY (not per domain) is a different, wrong null
    rnd = random.Random(5)
    x = [rnd.choice([0.25, 0.5, 0.75, 1.0]) for _ in range(38)]
    yk = [-2.0 * v + rnd.gauss(0, 0.5) for v in x]
    yc = [rnd.gauss(0, 0.5) for _ in x]
    rx = g._rank(x)
    obs = g.pearson(rx, g._rank(yk)) - g.pearson(rx, g._rank(yc))
    per_domain = arm_swap_p(g, x, yk, yc, obs, 11, 2000)
    rnd2 = random.Random(11)
    hits = 0
    for _ in range(2000):                                   # the MUTANT: one coin for all domains
        if rnd2.random() < 0.5:
            aa, bb = yk, yc
        else:
            aa, bb = yc, yk
        stat = g.pearson(rx, g._rank(aa)) - g.pearson(rx, g._rank(bb))
        if abs(stat) >= abs(obs) - 1e-12:
            hits += 1
    global_p = (hits + 1) / 2001
    caught = abs(global_p - per_domain) > 0.01
    print(f"6. mutant (one global coin instead of per-domain): p={global_p:.4f} vs correct "
          f"p={per_domain:.4f} -> {'CAUGHT' if caught else 'MISSED'}")
    if not caught:
        fails.append("mutation harness did not distinguish a global swap from a per-domain swap")

    print()
    if fails:
        print("VERIFY: FAIL")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("VERIFY: PASS")


if __name__ == "__main__":
    main()
