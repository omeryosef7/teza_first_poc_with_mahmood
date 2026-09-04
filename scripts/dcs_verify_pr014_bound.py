#!/usr/bin/env python
"""dcs_verify_pr014_bound.py -- the audit `scripts/dcs_pr014_bound.py` must pass before any of its
numbers are quoted.

WHY IT EXISTS. `PR-014`'s verdict will be a p-value from a hand-written exact McNemar plus a
row-flipping bound whose *assignment rule* I wrote myself (`DCS-033`). Neither is covered by any
existing guard, and the phase has already been bitten twice by a statistic that returned a
plausible number for the wrong reason (`C-017`, `R-040`).

CHECK 4 IS THE IMPORTANT ONE. `DCS-C-030` found that `PR-014` labelled the refusal-adjusted end
"maximally hostile" when it is arithmetically the FAVOURABLE end. That correction is prose, and
prose does not stop the mistake recurring. Check 4 turns it into an ASSERTION: over randomised
inputs, `bounded_delta <= face_delta` must ALWAYS hold. If a future edit ever makes the adjusted
end hostile, this fails loudly instead of a report quietly claiming robustness.

Run: python scripts/dcs_verify_pr014_bound.py    (exit 0 = pass; scipy optional)
"""
from __future__ import annotations
import importlib.util, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def synth(rnd, n=380, base_ref=150):
    """A KO-3 arm with NO refusals (R-026) and a control that INDUCES them (C-023)."""
    ko, ctrl = {}, {}
    for i in range(n):
        pid = f"p{i:04d}"
        ko[pid] = {"attack": int(rnd.random() < 0.31), "refused": 0,
                   "domain": f"d{i % 38}", "sha": None}
        ref = int(rnd.random() < (base_ref + rnd.randint(30, 50)) / n)
        ctrl[pid] = {"attack": 0 if ref else int(rnd.random() < 0.40), "refused": ref,
                     "domain": f"d{i % 38}", "sha": None}
    return ko, ctrl


def main() -> None:
    b = load("bnd", "scripts/dcs_pr014_bound.py")
    cds = load("cds", "scripts/cds_domain_test.py")
    two = cds._binom_cdf_two_sided
    fails: list[str] = []

    # 1 -- exact McNemar against scipy, and its degenerate cases
    a = {"x": {"attack": 1, "refused": 0}, "y": {"attack": 0, "refused": 0},
         "z": {"attack": 1, "refused": 0}}
    c = {"x": {"attack": 0, "refused": 0}, "y": {"attack": 1, "refused": 0},
         "z": {"attack": 1, "refused": 0}}
    r = b.mcnemar(a, c, two)
    if (r["ko_only"], r["ctrl_only"], r["n_discordant"]) != (1, 1, 2):
        fails.append(f"discordant bookkeeping wrong: {r}")
    if abs(r["mcnemar_p"] - 1.0) > 1e-12:
        fails.append(f"1-vs-1 discordant should give p=1.0, got {r['mcnemar_p']}")
    print("1. McNemar bookkeeping / degenerate case OK" if not fails else "1. FAIL")

    try:
        from scipy.stats import binomtest
        rnd, worst = random.Random(4), 0.0
        for _ in range(200):
            n = rnd.randint(5, 300)
            ko = {f"p{i}": {"attack": rnd.randint(0, 1), "refused": 0} for i in range(n)}
            ct = {f"p{i}": {"attack": rnd.randint(0, 1), "refused": 0} for i in range(n)}
            r = b.mcnemar(ko, ct, two)
            if r["n_discordant"]:
                ref = binomtest(min(r["ko_only"], r["ctrl_only"]),
                                r["n_discordant"], 0.5).pvalue
                worst = max(worst, abs(r["mcnemar_p"] - min(1.0, ref)))
        print(f"2. vs scipy binomtest over 200 random tables: worst |diff| = {worst:.2e}")
        if worst > 1e-9:
            fails.append(f"McNemar p disagrees with scipy by {worst:.2e}")
    except ImportError:
        print("2. vs scipy: SKIPPED (scipy not installed)")

    # 3 -- the flip rule obeys its own eligibility and preference contract
    rnd = random.Random(9)
    for _ in range(200):
        ko, ct = synth(rnd)
        n_flip = rnd.randint(0, 80)
        out, book = b.apply_bound(ko, ct, n_flip)
        elig = [p for p in ct if ct[p]["refused"] and not ct[p]["attack"]]
        flipped = [p for p in ct if out[p]["attack"] and not ct[p]["attack"]]
        if len(flipped) != min(n_flip, len(elig)):
            fails.append(f"flipped {len(flipped)}, expected {min(n_flip, len(elig))}")
            break
        if any(p not in elig for p in flipped):
            fails.append("flipped a row that was not eligible (not refused, or already attacking)")
            break
        hostile = [p for p in elig if ko[p]["attack"]]
        used_h = [p for p in flipped if p in hostile]
        if len(used_h) != min(len(flipped), len(hostile)):
            fails.append("hostile-first preference violated: a non-discordant row was flipped "
                         "while a discordant one remained")
            break
        if ct[flipped[0]]["refused"] == 0 if flipped else False:
            fails.append("flipped a non-refused row")
            break
    print("3. flip rule: eligibility + hostile-first preference OK" if not any(
        "flip" in f or "hostile" in f for f in fails) else "3. FAIL")

    # 4 -- DCS-C-030 AS AN ASSERTION: the adjusted end can never be the hostile one
    rnd = random.Random(21)
    viol = 0
    for _ in range(300):
        ko, ct = synth(rnd)
        induced = sum(r["refused"] for r in ct.values()) - 150
        bounded, _ = b.apply_bound(ko, ct, induced)
        face = b.mcnemar(ko, ct, two)["delta_attacks"]
        adj = b.mcnemar(ko, bounded, two)["delta_attacks"]
        viol += (adj > face)
    print(f"4. C-030 invariant  bounded_delta <= face_delta: {300 - viol}/300 hold")
    if viol:
        fails.append(f"C-030 invariant VIOLATED on {viol}/300 draws -- the adjusted end became "
                     "hostile, which the report's wording assumes is impossible")

    # 5 -- mutation harness: three plausible miswrites must all be caught
    caught = 0
    ko, ct = synth(random.Random(77))
    good, _ = b.apply_bound(ko, ct, 40)
    n_good = sum(good[p]["attack"] for p in good)
    # (a) ignore eligibility entirely
    m_a = {p: dict(r) for p, r in ct.items()}
    for p in sorted(m_a)[:40]:
        m_a[p]["attack"] = 1
    caught += (sum(r["attack"] for r in m_a.values()) != n_good)
    # (b) flip in reverse (least hostile first)
    elig = [p for p in sorted(ct) if ct[p]["refused"] and not ct[p]["attack"]]
    m_b = {p: dict(r) for p, r in ct.items()}
    for p in [q for q in elig if not ko[q]["attack"]][:40]:
        m_b[p]["attack"] = 1
    caught += (b.mcnemar(ko, m_b, two)["n_discordant"]
               != b.mcnemar(ko, good, two)["n_discordant"])
    # (c) add attacks to the KNOCKOUT instead of the control
    m_c = {p: dict(r) for p, r in ko.items()}
    for p in sorted(m_c)[:40]:
        m_c[p]["attack"] = 1
    caught += (b.mcnemar(m_c, ct, two)["delta_attacks"]
               > b.mcnemar(ko, good, two)["delta_attacks"])
    print(f"5. mutation harness: {caught}/3 broken variants CAUGHT")
    if caught < 3:
        fails.append(f"mutation harness caught only {caught}/3")

    print()
    if fails:
        print("VERIFY: FAIL")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("VERIFY: PASS")


if __name__ == "__main__":
    main()
