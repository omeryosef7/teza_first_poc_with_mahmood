#!/usr/bin/env python3
"""Every headline statistic of this phase that currently exists ONLY in prose. `REVIEW-3`.

WHY THIS FILE EXISTS. Six times now a number has been computed inline, reported in the log, and
found later to live in no script and no artifact -- `C8` (entry 037's rho = 0.5260/0.4206),
`REVIEW-3` on `ENTRY 047`'s basket Q1b/Q1d, and `REVIEW-3` on `S-009`'s concentration ratio. Each
time the number was *correct*; each time it was **unre-runnable**, which is the complaint. Rather
than fix them one at a time and produce a seventh, this computes all of them, asserts the
invariants that would have caught the defects they hid, and writes one artifact.

WHAT IT COMPUTES
  1. THE CONCENTRATION RATIO (`S-009`). Residualising `v_lex(bomb)` against span{knife, gun}
     removes what the three axes SHARE. The question is whether the Doublespeak shift CONCENTRATES
     in what survives or is spread uniformly, which is a ratio of ratios:
         (projection retained) / (axis retained)
     1.0 means uniform -- no preference at all for the part knife and gun cannot express. This is
     the corrected form of the "90.8%" that `S-002` claimed, `C-208b` withdrew as a specificity
     statement and `C-215`/C4 showed is a 9.2% REDUCTION in comparable units.

  2. THE PAIRED Q1 CONTRASTS FOR BOTH CODEWORDS on the concept-present channel, reported with BOTH
     denominators. `ENTRY 047` printed basket's Q1b as +0.0522 -- a 113-domain mean -- beside a
     42-domain sign test. Over the 42 domains that actually moved it is 0.1405. Both are true and
     they answer different questions; printing one beside the other's p-value is not.

  3. THE C3 INVARIANT THAT WAS MISSING. `B1 = H + I` is ALGEBRAICALLY VACUOUS -- it holds for any
     direction whatsoever -- which is exactly why it held at 3.09e-08 for the entire period the
     decomposition was using the wrong (in-sample) axis. The check that would have caught `C3` is
     `interaction_decomposition.B1 == metrics.B1`, comparing the decomposition against the
     independently-computed candidate. That is asserted here, over the full 2 x 9 x 9 grid.

USAGE
  python scripts/dcs_succ_phase_statistics.py
  python scripts/dcs_succ_phase_statistics.py --selftest
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import random
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from dcs_succ_concept_presence import concept_hits          # noqa: E402  frozen lexicon

CONCEPTS = ("bomb", "knife", "gun")
PEAK = {"button": 12, "basket": 11}
EXCLUDED = ("restaurant_kitchen", "school_campus", "subway_station")


class Refusal(RuntimeError):
    pass


def one_done(pattern):
    ds = [d for d in sorted(glob.glob(pattern)) if os.path.exists(os.path.join(d, "DONE.json"))]
    if len(ds) != 1:
        raise Refusal("%d completed runs match %s" % (len(ds), pattern))
    return ds[0]


def sign_test(k, n):
    if n == 0:
        return 1.0, 1.0
    k = max(k, n - k)
    t = sum(math.comb(n, i) for i in range(k, n + 1))
    return min(1.0, 2.0 * t / 2 ** n), min(1.0, 2.0 / 2 ** n)


def boot(v, B=10000, seed=20260910):
    rg = random.Random(seed)
    n = len(v)
    ms = sorted(sum(v[rg.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return ms[int(0.025 * B)], ms[int(0.975 * B)]


def concentration(cand, cw, L):
    """(projection retained, axis retained, ratio) for the bomb shift on the bomb axis."""
    b = cand["by_codeword"][cw]
    m = b["metrics"]["B1|L%d|shift_bomb|ref_bomb" % L]["mean_gap_units"]
    cell = b["residual_axis_3x3"]["L%d" % L]["table"]["shift_bomb|resid_ref_bomb"]
    proj_ret = cell["mean_in_FULL_gap_units"] / m
    axis_ret = cell["frac_of_axis_orthogonal_to_the_other_two"]
    return proj_ret, axis_ret, proj_ret / axis_ret


def c3_invariant(cand):
    """The check that WOULD have caught C3, over the whole grid. Vacuous identities do not count."""
    worst, n = 0.0, 0
    for cw, b in cand["by_codeword"].items():
        for Lk, dec in b["interaction_decomposition"].items():
            L = int(Lk[1:])
            for sc in CONCEPTS:
                for rc in CONCEPTS:
                    a = dec["shift_%s|ref_%s" % (sc, rc)]["B1"]
                    key = "B1|L%d|shift_%s|ref_%s" % (L, sc, rc)
                    if key not in b["metrics"]:
                        raise Refusal("no independent B1 for %s" % key)
                    worst = max(worst, abs(a - b["metrics"][key]["mean_gap_units"]))
                    n += 1
    return worst, n


def arm_rows(arm, gp, jp):
    j = one_done(os.path.join(REPO, "outputs/boombness/judge/%s%s_*" % (jp, arm)))
    g = one_done(os.path.join(REPO, "outputs/boombness/score_behavior/%s%s_*" % (gp, arm)))
    for label, d in (("generation", g), ("judge", j)):
        mp = os.path.join(d, "metadata.json")
        if not os.path.exists(mp):
            raise Refusal("%s run %s has no metadata.json" % (label, os.path.basename(d)))
    gs = json.load(open(os.path.join(g, "metadata.json"), encoding="utf-8")).get("bank_file_sha16")
    js = json.load(open(os.path.join(j, "metadata.json"), encoding="utf-8")).get("bank_file_sha16")
    if gs is None or gs != js:
        raise Refusal("arm %s: generation bank %r != judge bank %r (the banks share prompt_id "
                      "exactly, so nothing downstream would notice)" % (arm, gs, js))
    G = {json.loads(l)["prompt_id"]: json.loads(l)
         for l in open(os.path.join(g, "gens.jsonl"), encoding="utf-8")}
    out = collections.defaultdict(list)
    for line in open(os.path.join(j, "results.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        out[r["domain"]].append(bool(r.get("malicious_at_0.5"))
                                and bool(concept_hits(G[r["prompt_id"]]["generation"])))
    return {k: sum(v) / len(v) for k, v in out.items()}, gs


def paired(x, y):
    doms = sorted(set(x) & set(y))
    d = [x[k] - y[k] for k in doms]
    nz = [v for v in d if v != 0]
    k = sum(1 for v in nz if v > 0)
    p, fl = sign_test(k, len(nz))
    return {"n_domains_all": len(doms),
            "mean_delta_over_ALL_domains": statistics.mean(d),
            "ci95_over_ALL_domains": boot(d),
            "n_domains_informative": len(nz),
            "n_ties": len(doms) - len(nz),
            "mean_delta_over_INFORMATIVE_domains": statistics.mean(nz) if nz else float("nan"),
            "n_positive": k, "sign_p": p, "sign_p_floor": fl,
            "_both_denominators": "the sign test's n is the INFORMATIVE count; a mean over ALL "
                                  "domains printed beside it answers a different question. "
                                  "ENTRY 047 printed only the first."}


def selftest() -> int:
    ok = True

    def chk(n, c):
        nonlocal ok
        print("  %-54s %s" % (n, "PASS" if c else "FAIL"))
        ok = ok and bool(c)

    p, f = sign_test(42, 42)
    chk("sign test 42/42 is at its floor", abs(p - f) < 1e-15)
    chk("sign test on zero informative domains is 1.0", sign_test(0, 0)[0] == 1.0)
    x = {"a": 0.3, "b": 0.2, "c": 0.1}
    y = {"a": 0.1, "b": 0.2, "c": 0.0}
    r = paired(x, y)
    chk("ties are excluded from the sign test n", r["n_domains_informative"] == 2
        and r["n_ties"] == 1)
    chk("the two denominators differ and both are reported",
        abs(r["mean_delta_over_ALL_domains"] - 0.1) < 1e-12
        and abs(r["mean_delta_over_INFORMATIVE_domains"] - 0.15) < 1e-12)
    chk("concentration of 1.0 means uniform", abs((0.5 / 0.5) - 1.0) < 1e-12)
    try:
        one_done(os.path.join(REPO, "outputs/__nope__*"))
        chk("one_done refuses", False)
    except Refusal:
        chk("one_done refuses", True)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "outputs/dcs_succ/phase_statistics.json"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("=== selftest ===")
        return selftest()

    cand = json.load(open(os.path.join(REPO, "outputs/dcs_succ/bombness_candidates_train.json"),
                          encoding="utf-8"))
    res = {"_label": "phase statistics that previously existed only in prose (REVIEW-3)",
           "concentration_ratio": {}, "c3_invariant": {}, "paired_Q1": {}}

    for cw, L in PEAK.items():
        pr_, ax_, ratio = concentration(cand, cw, L)
        res["concentration_ratio"]["%s_L%d" % (cw, L)] = {
            "projection_retained": pr_, "axis_retained": ax_, "concentration_ratio": ratio,
            "_reading": "1.0 = the shift is spread uniformly over the axis, with no preference "
                        "for the part knife and gun cannot express"}
        print("concentration %-8s L%-2d  projection %.4f / axis %.4f = %.4f"
              % (cw, L, pr_, ax_, ratio))

    worst, n = c3_invariant(cand)
    res["c3_invariant"] = {"max_abs_difference": worst, "n_cells_checked": n,
                           "_why": "B1 = H + I is vacuous (true for any direction). This compares "
                                   "the decomposition's B1 against the independently computed "
                                   "candidate, which is the check that would have caught C3."}
    print("C3 invariant: decomposition B1 vs metrics B1, max |diff| = %.3g over %d cells"
          % (worst, n))
    if worst > 1e-12:
        raise Refusal("the decomposition and the candidate disagree by %g -- C3 is live again"
                      % worst)

    for cw, gp, jp in (("button", "tsb66_", "tsb66j_"), ("basket", "tsb66b_", "tsb66bj_")):
        try:
            c4, sha4 = arm_rows("C_n4", gp, jp)
            c0, _ = arm_rows("C_n0", gp, jp)
            b4, _ = arm_rows("B_n4", gp, jp)
        except Refusal as e:
            res["paired_Q1"][cw] = {"status": "REFUSED: %s" % e}
            print("%-7s REFUSED: %s" % (cw, e))
            continue
        res["paired_Q1"][cw] = {"bank_file_sha16": sha4,
                                "Q1b_Cdose4_minus_Cdose0": paired(c4, c0),
                                "Q1d_Cdose4_minus_Bdose4": paired(c4, b4)}
        for k in ("Q1b_Cdose4_minus_Cdose0", "Q1d_Cdose4_minus_Bdose4"):
            r = res["paired_Q1"][cw][k]
            print("%-7s %-26s all-domain mean %+.4f | informative mean %+.4f (%d of %d, %d ties) "
                  "| %d pos, p=%.3g (floor %.3g)"
                  % (cw, k, r["mean_delta_over_ALL_domains"],
                     r["mean_delta_over_INFORMATIVE_domains"], r["n_domains_informative"],
                     r["n_domains_all"], r["n_ties"], r["n_positive"], r["sign_p"],
                     r["sign_p_floor"]))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        raise SystemExit(2)
