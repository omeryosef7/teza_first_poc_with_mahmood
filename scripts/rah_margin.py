#!/usr/bin/env python
"""rah_margin.py -- derive the Track-A equivalence margin from the nuisance ensemble.

WHY A NUISANCE ENSEMBLE AND NOT "REPEATABILITY" (`RAH-DR-002` F5). The receiver is a single
deterministic greedy forward, so its run-to-run repeatability is float jitter of order 1e-6. An
equivalence margin derived from that would sit far below the rule-of-three floor `3/n` (0.0375 at
n = 80), and `paired_equivalence` would return `UNRESOLVABLE_AT_THIS_N` for EVERY possible dataset --
`EQUIVALENT` would be unreachable by construction. The margin must instead be the size of the
movement the design considers IRRELEVANT.

THE ENSEMBLE. Option ORDER (4 rotations, mapped concept in each of the 4 slots) x receiver WORDING
(2 paraphrases with identical geometry) = 8 variants, run on BASE donors only. The producing run
(`rah_transport_assay.py --nuisance-ensemble`) restricts its live arms to `("base",)` and asserts
that no intervened arm is constructed, so the run that fixes the margin is structurally incapable of
seeing the effect the margin will later judge.

WHAT IS COMPUTED
  * `s_accuracy`  -- the 95th percentile of |acc(variant a) - acc(variant b)| over all variant PAIRS,
                     where acc is the fraction of families whose argmax label is the mapped concept.
                     This is the aggregate-level nuisance spread, on the same scale as the estimand.
  * `s_margin`    -- the same statistic on the harm-matched margin, for the continuous companion.
  * `family_disagreement` -- the fraction of (family, variant-pair) cells whose BINARY outcome
                     differs. Reported as a diagnostic; it is NOT the margin, because a per-family
                     binary difference is 0 or 1 and its 95th percentile is degenerate.

THE MARGIN. `margin = max(0.10, s_accuracy)`. 0.10 is the repository's own precedent (the RBD
sprint's T3/T5 equivalence margin) and acts as a floor so that an unusually quiet ensemble cannot
produce a margin so small that equivalence becomes unreachable.

Usage:
  python scripts/rah_margin.py --out outputs/boombness/rah_margin/rah_margin.json
"""
from __future__ import annotations
import argparse
import collections
import glob
import itertools
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TA_DIR = os.path.join(ROOT, "outputs/boombness/rah_transport")
SCHEMA = "RAH_MARGIN/1"
FLOOR = 0.10          # the repository's own T3/T5 precedent


def pct(vals, q):
    """Percentile by the nearest-rank method. No numpy; exact and auditable."""
    if not vals:
        return float("nan")
    xs = sorted(vals)
    k = max(0, min(len(xs) - 1, int(round(q * (len(xs) - 1)))))
    return xs[k]


def load_runs(pattern):
    out = []
    for d in sorted(glob.glob(os.path.join(TA_DIR, pattern))):
        mp, rp = os.path.join(d, "meta.json"), os.path.join(d, "rows.jsonl")
        if not (os.path.exists(mp) and os.path.exists(rp)):
            continue
        m = json.load(open(mp))
        if not m.get("nuisance_ensemble"):
            raise SystemExit("REFUSING: %s is not a nuisance-ensemble run; the margin may only be "
                             "derived from a run that constructed no intervened arm" % d)
        if list(m.get("live_arms") or []) != ["base"]:
            raise SystemExit("REFUSING: %s has live_arms=%r, expected ['base']"
                             % (d, m.get("live_arms")))
        rows = [json.loads(l) for l in open(rp) if l.strip()]
        out.append({"dir": os.path.basename(d), "meta": m, "rows": rows})
    return out


def analyse(run):
    m, rows = run["meta"], run["rows"]
    concept = rows[0]["concept"]
    base = [r for r in rows if r["arm"] == "base"]
    by_variant = collections.defaultdict(dict)      # variant -> family -> row
    for r in base:
        by_variant[r["variant_key"]][r["family_id"]] = r
    variants = sorted(by_variant)
    fams = sorted(set(f for v in variants for f in by_variant[v]))
    # every variant must cover every family, or the pairs are not comparable
    missing = [(v, f) for v in variants for f in fams if f not in by_variant[v]]
    if missing:
        raise SystemExit("REFUSING: %d (variant, family) cells missing in %s" % (len(missing),
                                                                                run["dir"]))
    acc = {v: sum(1 for f in fams if by_variant[v][f]["argmax_label"] == concept) / len(fams)
           for v in variants}
    mar = {v: sum(by_variant[v][f]["margin_harm_matched"] for f in fams) / len(fams)
           for v in variants}
    pairs = list(itertools.combinations(variants, 2))
    d_acc = [abs(acc[a] - acc[b]) for a, b in pairs]
    d_mar = [abs(mar[a] - mar[b]) for a, b in pairs]
    disagree = []
    for a, b in pairs:
        n_diff = sum(1 for f in fams
                     if (by_variant[a][f]["argmax_label"] == concept)
                     != (by_variant[b][f]["argmax_label"] == concept))
        disagree.append(n_diff / len(fams))
    return {"dir": run["dir"], "model": m["model"], "bank": os.path.basename(m["bank"]),
            "concept": concept, "n_families": len(fams), "n_variants": len(variants),
            "variants": variants, "n_variant_pairs": len(pairs),
            "accuracy_by_variant": acc, "mean_margin_by_variant": mar,
            "s_accuracy_p95": pct(d_acc, 0.95), "s_accuracy_max": max(d_acc) if d_acc else 0.0,
            "s_margin_p95": pct(d_mar, 0.95), "s_margin_max": max(d_mar) if d_mar else 0.0,
            "family_disagreement_p95": pct(disagree, 0.95),
            "family_disagreement_mean": sum(disagree) / len(disagree) if disagree else 0.0}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pattern", default="nuis_*")
    ap.add_argument("--out", default="outputs/boombness/rah_margin/rah_margin.json")
    a = ap.parse_args()
    runs = load_runs(a.pattern)
    if not runs:
        raise SystemExit("no nuisance-ensemble runs matching %r" % a.pattern)
    per = [analyse(r) for r in runs]

    print("%-34s %-32s %5s %4s %10s %10s %10s" %
          ("run", "model", "fams", "var", "s_acc_p95", "s_acc_max", "disagree"))
    for p in per:
        print("%-34s %-32s %5d %4d %10.4f %10.4f %10.4f" %
              (p["dir"][:34], p["model"], p["n_families"], p["n_variants"],
               p["s_accuracy_p95"], p["s_accuracy_max"], p["family_disagreement_mean"]))
        print("     accuracy by variant: " +
              " ".join("%s=%.3f" % (v.replace("fc_probe_last", "fc"), p["accuracy_by_variant"][v])
                       for v in p["variants"]))

    # THE MARGIN takes the WORST (largest) nuisance spread across models -- a margin that holds on
    # one model and not the other is not a margin.
    s_acc = max(p["s_accuracy_p95"] for p in per)
    s_mar = max(p["s_margin_p95"] for p in per)
    margin = max(FLOOR, s_acc)
    n_min = min(p["n_families"] for p in per)
    rule_of_three = 3.0 / n_min
    print("\ns_accuracy (p95, worst model) = %.4f" % s_acc)
    print("floor (repo T3/T5 precedent)  = %.4f" % FLOOR)
    print("=> MARGIN                     = %.4f" % margin)
    print("rule-of-three at n=%d         = %.4f  -> equivalence is %s at this n"
          % (n_min, rule_of_three,
             "ATTAINABLE" if rule_of_three < margin else "UNREACHABLE"))

    out = {"schema": SCHEMA, "floor": FLOOR,
           "s_accuracy_p95_worst_model": s_acc, "s_margin_p95_worst_model": s_mar,
           "MARGIN": margin, "n_families_min": n_min, "rule_of_three": rule_of_three,
           "equivalence_attainable_at_this_n": bool(rule_of_three < margin),
           "derivation": "95th percentile of |accuracy(a) - accuracy(b)| over all pairs of "
                         "nuisance variants (option order x receiver wording), on BASE donors "
                         "only, worst model; floored at the repository's own 0.10 precedent",
           "per_run": per}
    os.makedirs(os.path.dirname(os.path.join(ROOT, a.out)), exist_ok=True)
    with open(os.path.join(ROOT, a.out), "w") as f:
        json.dump(out, f, indent=1)
    print("\n-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
