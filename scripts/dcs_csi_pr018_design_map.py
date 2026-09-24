#!/usr/bin/env python
"""§22 DESIGN MAP for PR-CSI-018 -- what outcomes this family CAN and CANNOT certify.

WHY THIS AND NOT `dcs_csi_head_power.py` OR `dcs_csi_rank_power_sweep.py`. Those analyse RANK tests
(a candidate's rank among n controls, floor 1/(n+1)) on the behavioural endpoint. PR-CSI-018's
primary is nothing of the kind: it is an ARGMAX-AGREEMENT count adjudicated by the WEAKEST of THREE
p-values -- a binomial, a conditional binomial over the unique-layer heads, and a permutation over
distinct assignments of the prediction multiset. No existing script computes any of them. This is
the same reason `dcs_csi_head_power.py` gives for its own existence: different test, nothing
reusable.

WHAT IT ANSWERS, ALL OF IT BEFORE THE READ AND FROM THE FROZEN PREREG ALONE.
  * the three p-value FLOORS, by brute-force enumeration rather than a closed form taken on trust;
  * WHICH outcome patterns certify -- the answer is 5 of 64, and every one of them requires BOTH
    unique-layer heads (11 and 29) to match, because the conditional p runs over those two alone
    and can therefore take only the values 0.012346, 0.209877 and 1.0;
  * how ADMISSION moves the statistic. The prereg defines the conditional over heads unique AMONG
    THE ADMITTED, so dropping a head CHANGES which layers are unique. Dropping a TIE head (6, 20,
    24 or 27) RAISES K_unique from 2 to 3 and strengthens the conditional floor to 0.001372;
    dropping a UNIQUE head (11 or 29) drops it to 1 and the family cannot certify at all.
  * the admission FLOOR: at K<=3 admitted, NO outcome certifies, however perfect.

⛔ WHAT THIS IS NOT. It is not power. It computes no effect size and assumes no noise model; it maps
   the preregistered DECISION RULE over its own outcome space. It is arithmetic on the prereg, which
   is why it can be run -- and is being run -- while the family is still on the GPU. It reads no arm
   and no endpoint.

⛔ IT CHANGES NOTHING. The rule stands exactly as frozen. The point of computing this BEFORE the
   read is that "5 of 6 matched but the family FAILED" is a foreseeable outcome, and recording that
   it is a FAILURE under the frozen rule -- now, with no numbers in hand -- is what stops it being
   argued about afterwards.

--with-bars additionally RE-DERIVES PR-CSI-013's six per-head bars from that family's own landed
arms, reusing w4.by_domain (the sole endpoint definition) and the S-311 rule verbatim, to witness
the |E|/bar table the frozen read prints. PR-013 is already read and published; this spends nothing.
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


def perm_p(pred, adm, M):
    truth = tuple(pred[h] for h in adm)
    ass = assignments([pred[h] for h in adm])
    if not ass:
        return 1.0
    hits = lambda a: sum(1 for i in range(len(truth)) if a[i] == truth[i])
    return sum(1 for a in ass if hits(a) >= M) / float(len(ass))


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
    print("PR-CSI-018 DESIGN MAP   prereg=%s" % pr["id"])
    print("=" * 96)
    print("heads              : %s" % heads)
    print("predicted layers   : %s" % {h: "L%d" % pred[h] for h in heads})
    print("multiset           : %s  over %d distinct layers"
          % (sorted("L%d" % x for x in ms), len(set(ms))))
    print("unique-layer heads : %s  -> K_unique = %d" % (uq, len(uq)))

    ass = assignments(ms)
    print("\nFLOORS, by enumeration")
    print("   distinct assignments   : %d   (closed form 6!/(2!2!) = %d)"
          % (len(ass), math.factorial(6) // 4))
    print("   permutation floor      : %.12f" % (1.0 / len(ass)))
    print("   binomial   floor (K=6) : %.12e" % binom_ge(6, 6))
    print("   conditional floor      : %.12f  (over the %d unique-layer heads)"
          % (binom_ge(len(uq), len(uq)), len(uq)))
    w, lab, _ = verdict(pred, heads, heads)
    print("   WEAKEST on a perfect 6/6 : %.12f -> %s" % (w, lab))

    print("\n" + "=" * 96)
    print("OUTCOME MAP -- every match pattern at full admission (M >= 4 shown)")
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
