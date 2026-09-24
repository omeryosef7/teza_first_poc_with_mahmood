#!/usr/bin/env python
"""§22 DESIGN MAP for a CSI CELL-CENSUS family -- the floors, and what they do and do not fix.

TAKES --prereg. Despite the filename it is not PR-CSI-018-specific; the filename is kept because
S-332 and S-347/S-348 cite this path (R26 chain of custody).

⚠⚠ READ THIS BEFORE TRUSTING ANY NUMBER BELOW THE FLOORS BLOCK.
This file originally scored permutations against the PREDICTION vector. The reader
(scripts/dcs_csi_pr016_argmax_test.py) scores them against the OBSERVED ARGMAX vector, and the two
coincide ONLY at M = K. S-352 established that, and S-353 established the consequence: because
p_perm depends on WHERE the misses land, NO map over match counts is exact, and 34 outcomes with
identical M and identical M_unique were exhibited that differ in verdict.

So this file's OUTCOME MAP and ADMISSION MAP are UPPER BOUNDS, not the reader's verdicts, and they
are labelled as such at the point of printing. Its FLOORS block IS exact -- floors are evaluated at
M = K, where the two statistics agree.

WHAT IT PRODUCED THAT WAS WITHDRAWN. S-332 used this file to claim that for PR-CSI-018 "only 5 of
64 outcome patterns certify, and every one requires both unique-layer heads". S-352 WITHDREW that:
it was computed under the wrong statistic. PR-CSI-018's own READ is unaffected -- its permutation p
is identical under both statistics for its observed outcome, and it gated on the conditional.

WHAT IS EXACT AND USABLE:
  * the three p-value FLOORS, by brute-force enumeration cross-checked against the closed form
    (the script REFUSES if they disagree);
  * how ADMISSION moves K_unique and the permutation space -- that is combinatorics on the
    prediction multiset and does not involve the observation at all.

⛔ WHAT THIS IS NOT. It is not power. Power under the reader's statistic requires a Monte Carlo over
   (match pattern x miss landing) and lives in the prereg's POWER_BY_SEEDED_MONTE_CARLO block
   (S-354). It reads no arm and no endpoint.

--with-bars additionally RE-DERIVES a family's per-head bars from the landed arms of the family its
prereg names as the reference, reusing w4.by_domain (the sole endpoint definition) and the S-311
rule verbatim. Those families are already read and published; this spends nothing.
"""
import argparse, importlib.util, json, math, os, statistics, sys
from itertools import combinations, permutations, product
from math import comb

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREREG = os.path.join(REPO, "configs/dcs_csi_pr018_cell_census_button_nonL14.json")
NLAYERS = 9
P = 1.0 / NLAYERS


def binom_ge(K, M):
    """P(Binom(K, 1/9) >= M). K=0 is the vacuous case and is 1.0, not an error."""
    if K == 0:
        return 1.0
    return sum(comb(K, m) * P ** m * (1 - P) ** (K - m) for m in range(M, K + 1))


def assignments(layers):
    """The DISTINCT assignments of a prediction multiset -- enumerated, not a closed form."""
    return sorted(set(permutations(sorted(layers))))


def perm_p(pred, adm, M, obs=None):
    """⚠ S-358. THIS USED TO SCORE PERMUTATIONS AGAINST THE PREDICTION VECTOR. The reader
    (scripts/dcs_csi_pr016_argmax_test.py) scores them against the OBSERVED ARGMAX VECTOR, and the
    two coincide ONLY at M = K (S-352). Every number this file printed below M = K was therefore a
    different statistic from the one that decides a read -- which is how S-332's "only 5 of 64
    outcome patterns certify" came to be published and then withdrawn in S-352.

    `obs` is now REQUIRED for any honest answer. With obs=None this returns the OLD quantity and
    says so, because callers that cannot supply an observation cannot have the real one."""
    ass = assignments([pred[h] for h in adm])
    if not ass:
        return 1.0
    target = tuple(obs) if obs is not None else tuple(pred[h] for h in adm)
    return sum(1 for a in ass
               if sum(1 for i in range(len(target)) if a[i] == target[i]) >= M) / float(len(ass))


def k_unique(pred, adm):
    lay = [pred[h] for h in adm]
    return [h for h in adm if lay.count(pred[h]) == 1]


def verdict(pred, adm, matched):
    """The frozen rule, applied. Returns (weakest, label, parts)."""
    K, M = len(adm), len(matched)
    uq = k_unique(pred, adm)
    Mu = len([h for h in matched if h in uq])
    b = binom_ge(K, M)
    c = binom_ge(len(uq), Mu)
    pp = perm_p(pred, adm, M)
    w = max(b, c, pp)
    spans = len({pred[h] for h in matched}) > 1
    if M > 0 and not spans:
        lab = "CANNOT ANSWER (spanning)"
    elif w <= 0.05:
        lab = "CERTIFIES"
    elif M >= 3:
        lab = "FAILURE"
    else:
        lab = "no claim"
    return w, lab, {"binomial": b, "conditional": c, "permutation": pp, "K": K, "M": M, "Mu": Mu}


def load_predictions(path):
    pr = json.load(open(path))
    ph = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    pred = {int(h): int(str(b["screen_predicted_layer"]).lstrip("L")) for h, b in ph.items()}
    return pr, pred, ph


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", default=PREREG)
    ap.add_argument("--with-bars", action="store_true",
                    help="also re-derive PR-013's per-head bars from its landed arms")
    a = ap.parse_args()

    pr, pred, ph = load_predictions(a.prereg)
    heads = sorted(pred)
    ms = [pred[h] for h in heads]
    uq = k_unique(pred, heads)

    print("=" * 96)
    print("CSI CELL-CENSUS DESIGN MAP   prereg=%s   K=%d heads" % (pr["id"], len(heads)))
    print("=" * 96)
    print("heads              : %s" % heads)
    print("predicted layers   : %s" % {h: "L%d" % pred[h] for h in heads})
    print("multiset           : %s  over %d distinct layers"
          % (sorted("L%d" % x for x in ms), len(set(ms))))
    print("unique-layer heads : %s  -> K_unique = %d" % (uq, len(uq)))

    ass = assignments(ms)
    print("\nFLOORS, by enumeration")
    import collections as _c
    _mult = _c.Counter(ms)
    _closed = math.factorial(len(ms))
    for _v in _mult.values():
        _closed //= math.factorial(_v)
    print("   distinct assignments   : %d   (closed form %d!/%s = %d)"
          % (len(ass), len(ms),
             "*".join("%d!" % v for v in sorted(_mult.values(), reverse=True)), _closed))
    if _closed != len(ass):
        sys.exit("REFUSING: closed form %d != enumeration %d" % (_closed, len(ass)))
    print("   permutation floor      : %.12f" % (1.0 / len(ass)))
    print("   binomial   floor (K=%d) : %.12e" % (len(heads), binom_ge(len(heads), len(heads))))
    print("   conditional floor      : %.12f  (over the %d unique-layer heads)"
          % (binom_ge(len(uq), len(uq)), len(uq)))
    w, lab, _ = verdict(pred, heads, heads)
    print("   WEAKEST on a perfect %d/%d : %.12f -> %s" % (len(heads), len(heads), w, lab))

    print("\n" + "=" * 96)
    print("⚠ OUTCOME MAP -- UPPER BOUND ONLY, NOT THE READER'S VERDICT (S-353).")
    print("   Under the reader's statistic p_perm depends on WHERE the misses land, so NO map over")
    print("   match counts is exact: S-353 exhibited 34 outcomes with identical M and M_unique that")
    print("   differ in verdict. The rows below use obs = the predictions for matched heads and the")
    print("   PREDICTION vector elsewhere, i.e. the OLD statistic, and are therefore a BOUND.")
    print("   The exact necessary conditions are M >= 3 AND M_unique >= 3 (necessary, NOT")
    print("   sufficient); power is in the prereg's POWER_BY_SEEDED_MONTE_CARLO block.")
    print("=" * 96)
    print("%-26s %2s %2s  %-11s %-11s %-11s %-11s %s"
          % ("matching heads", "M", "Mu", "binomial", "conditional", "permutation",
             "WEAKEST", "verdict"))
    print("-" * 104)
    cert = []
    for mask in product([1, 0], repeat=len(heads)):
        matched = [heads[i] for i in range(len(heads)) if mask[i]]
        w, lab, parts = verdict(pred, heads, matched)
        if lab == "CERTIFIES":
            cert.append(matched)
        if len(matched) >= 4:
            print("%-26s %2d %2d  %-11.3e %-11.6f %-11.6f %-11.6f %s"
                  % (",".join("h%d" % h for h in matched), parts["M"], parts["Mu"],
                     parts["binomial"], parts["conditional"], parts["permutation"], w, lab))
    print("\noutcome patterns that CERTIFY: %d of %d" % (len(cert), 2 ** len(heads)))
    print("minimum M among them          : %d" % min(len(c) for c in cert))
    print("ALL certifying patterns contain BOTH unique heads %s : %s"
          % (uq, all(set(uq) <= set(c) for c in cert)))

    print("\n" + "=" * 96)
    print("ADMISSION MAP -- admission is recomputed live from each HD_<h> arm, so K_unique MOVES")
    print("=" * 96)
    print("%-26s %2s %7s %7s  %-12s %-12s %s"
          % ("admitted", "K", "K_uniq", "n_perm", "cond floor", "perm floor", "perfect-result verdict"))
    print("-" * 104)
    for r in range(len(heads), 1, -1):
        feas = 0
        subs = list(combinations(heads, r))
        for adm in subs:
            w, lab, parts = verdict(pred, adm, list(adm))
            if lab == "CERTIFIES":
                feas += 1
            if r >= 5:
                print("%-26s %2d %7d %7d  %-12.6f %-12.6f %s"
                      % (",".join("h%d" % h for h in adm), r, len(k_unique(pred, adm)),
                         len(assignments([pred[h] for h in adm])),
                         binom_ge(len(k_unique(pred, adm)), len(k_unique(pred, adm))),
                         1.0 / len(assignments([pred[h] for h in adm])), lab))
        print("   K=%d : %d of %d admission subsets certify on a PERFECT result" % (r, feas, len(subs)))

    if a.with_bars:
        witness_bars(pr, ph)
    return 0


def witness_bars(pr, ph):
    """Re-derive PR-013's per-head bar and |E|/bar from its OWN landed arms (S-311 rule)."""
    def _load(mod, path):
        spec = importlib.util.spec_from_file_location(mod, path)
        m = importlib.util.module_from_spec(spec)
        sys.modules[mod] = m
        spec.loader.exec_module(m)
        return m

    rederive = _load("rederive", os.path.join(REPO, "scripts", "dcs_csi_rederive_patch.py"))
    census = _load("census", os.path.join(REPO, "scripts", "dcs_csi_head_census.py"))
    w4 = census.w4
    TAG, EXPECT_N, JOB, Z = "csi6_btnhead_button_validation", 230, ["919531"], 1.96

    pr013 = json.load(open(os.path.join(
        REPO, "configs/dcs_csi_pr013_button_head_replication.json")))
    base = pr013["base_arms"][0]
    refs = {int(h): b["pr013_whole_head_REFERENCE"] for h, b in ph.items()}

    need = [base] + [refs[h]["pr013_arm"] for h in sorted(refs)]
    per = {}
    for arm in need:
        d = rederive.strict_run_dir("%s_%s" % (TAG, arm), EXPECT_N,
                                    row_file="results.jsonl", require_slurm_jobs=JOB)
        per[arm] = w4.by_domain(d)[0]
    doms = sorted(set.intersection(*(set(per[x]) for x in need)))

    print("\n" + "=" * 96)
    print("BAR WITNESS -- PR-013's per-head bar re-derived from its own arms (n_dom=%d)" % len(doms))
    print("=" * 96)
    print("%-5s %-13s %13s %13s %10s %10s %8s"
          % ("head", "pr013 arm", "E (derived)", "E (prereg ref)", "|diff|", "bar", "|E|/bar"))
    print("-" * 88)
    for h in sorted(refs):
        arm = refs[h]["pr013_arm"]
        d = [per[arm][x] - per[base][x] for x in doms]
        E, sd = statistics.fmean(d), statistics.stdev(d)
        bar = Z * sd / math.sqrt(len(doms))
        print("%-5d %-13s %+13.8f %+13.8f %10.2e %10.6f %8.4f"
              % (h, arm, E, float(refs[h]["E"]), abs(E - float(refs[h]["E"])), bar, abs(E) / bar))
    print("\nadmission slack over the preregistered ratio 1.5, smallest first:")
    rows = []
    for h in sorted(refs):
        arm = refs[h]["pr013_arm"]
        d = [per[arm][x] - per[base][x] for x in doms]
        E, sd = statistics.fmean(d), statistics.stdev(d)
        rows.append((abs(E) / (Z * sd / math.sqrt(len(doms))), h))
    for ratio, h in sorted(rows):
        print("   head %-3d ratio %.4f   slack %+.4f (%+.1f%%)   predicts L%s"
              % (h, ratio, ratio - 1.5, 100.0 * (ratio - 1.5) / 1.5,
                 ph[str(h)]["screen_predicted_layer"]))


if __name__ == "__main__":
    sys.exit(main())
