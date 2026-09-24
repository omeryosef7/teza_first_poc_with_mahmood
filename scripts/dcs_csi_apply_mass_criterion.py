#!/usr/bin/env python
"""Apply S-325's FROZEN attention-mass criterion to a `retrieval_strength.py` run.

WHY THIS SCRIPT EXISTS. S-337 applied the criterion from a scratch file. The criterion decides
whether an entire family may be preregistered, and a decision of that weight must be reproducible
from the repository rather than from a temporary file -- the same provenance gap S-302 records for
a witness taken inside a job, and the one S-331 closed for the instrument's launcher.

THE CRITERION, QUOTED FROM S-325 AND NOT PARAPHRASED:

    measure, per row, in band 6-14 at the readout position:
       m_d = demo-block mass ; m_c = the STRICT, PROTECTED nondemo_matched_d1 draw's mass
    report   the median ratio rho = m_c / m_d, AND the per-row count of rows with m_d > m_c
             (C-CONT-019's own statistic was a per-row count, not a mean, and it must stay one)

    rho >= 1.0 and m_d > m_c on < 50% of rows  ->  the family may run as a CONFIRMATORY source test
    rho <= 1.0 and m_d > m_c on > 50% of rows  ->  the family may run ONLY as a REFUTATION test
    mixed / straddling                          ->  CANNOT ANSWER: the direction is not established
                                                    and no source-side family is licensed either way

⚠ THE CRITERION NAMES d1. d2 and d3 are printed as robustness and are NOT the quantity the branches
  are evaluated on. S-338 built a primary statistic on the MEAN of the three and R31-A showed the
  rationale REVERSES for d2 (rho 0.809), so the distinction is not pedantry.

⚠ CODEWORDS ARE NEVER POOLED (PART I 3.3). Pass one run at a time; each is evaluated separately and
  agreement between them is a second observation, not a doubling of n.

🔴 SEED PROVENANCE IS CHECKED, NOT ASSUMED. S-339: `retrieval_strength.py` passed a PRE-STRIDED seed
   to `knockout_key_set`, which strides it again, so the instrument measured draws at strides 2/4/6
   while the arms use 1/2/3 -- one of the three was a real arm's draw under the wrong label and two
   belonged to no arm at all. The numbers were still a valid estimate of the distribution, but the
   claim that they were "the draws the real arms make" was false. This script prints, for every run,
   the draw seed the arms WOULD use and the seed the run RECORDS, and marks any mismatch.
"""
import argparse, json, os, statistics, sys, collections

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMARY_DRAW = "nondemo_matched_d1"          # the criterion names d1
ROBUSTNESS = ("nondemo_matched_d2", "nondemo_matched_d3")
STRIDE = 7919777                             # score_behavior.NONDEMO_DRAW_SEED_STRIDE


def arm_draw_seed(run_seed, idx):
    """The seed a REAL ARM's draw `idx` uses: nondemo_draw_seed(run_seed, idx)."""
    return int(run_seed) + int(idx) * STRIDE


def load(run):
    rows = [json.loads(l) for l in open(os.path.join(run, "retrieval.jsonl"))]
    cfg = json.load(open(os.path.join(run, "config.json")))
    done = json.load(open(os.path.join(run, "DONE.json")))
    meta = {}
    mp = os.path.join(run, "metadata.json")
    if os.path.exists(mp):
        meta = json.load(open(mp))
    return rows, cfg, done, meta


def report(run, alpha_rows=0.50):
    rows, cfg, done, meta = load(run)
    print("=" * 96)
    print("RUN   %s" % os.path.basename(run))
    print("      rows=%d  status=%s  seed=%s" % (len(rows), done.get("status"), cfg.get("seed")))
    print("=" * 96)

    if done.get("status") != "ok":
        sys.exit("REFUSING: DONE.json status is %r, not 'ok'. (S-325)" % done.get("status"))

    # --- premises, checked rather than assumed -------------------------------------------------
    infeas = [r for r in rows if r.get("strict_protected_infeasible")]
    badn = [r for r in rows
            if r["strict_protected_n_keys"][PRIMARY_DRAW] != r["n_demo_keys"]]
    print("  rows with an INFEASIBLE strict draw   : %d" % len(infeas))
    print("  rows where d1 key count != demo count : %d" % len(badn))
    if infeas or badn:
        sys.exit("REFUSING: the count-match the comparison presupposes does not hold on every row. "
                 "A ratio of masses between sets of different size is not the quantity S-325 froze.")

    # --- seed provenance ------------------------------------------------------------------------
    seeds = (meta.get("knockout_feasibility") or {}).get("control_draw_seeds")
    want = {("nondemo_matched_d%d" % i): arm_draw_seed(cfg.get("seed", 0), i) for i in (1, 2, 3)}
    print("\n  SEED PROVENANCE (S-339): the seed a real ARM uses vs what this run recorded")
    if not seeds:
        print("    ⚠ the run records no control_draw_seeds; provenance CANNOT be verified here")
    else:
        for nm in sorted(want):
            got = (seeds or {}).get(nm)
            ok = (got is not None and int(got) == want[nm])
            print("    %-20s arm would use %-12d run recorded %-12s %s"
                  % (nm, want[nm], got, "OK" if ok else "*** MISMATCH -- see S-339 ***"))

    # --- THE CRITERION --------------------------------------------------------------------------
    md = [r["demo_mass_band"] for r in rows]
    mc = [r["strict_protected_mass_band"][PRIMARY_DRAW] for r in rows]
    ratios = [c / m for c, m in zip(mc, md) if m > 0]
    n_gt = sum(1 for c, m in zip(mc, md) if m > c)
    frac = n_gt / float(len(rows))
    rho = statistics.median(ratios)

    print("\n  m_d (demo-block mass, band)     median %.6f" % statistics.median(md))
    print("  m_c (STRICT PROTECTED %s) median %.6f" % (PRIMARY_DRAW, statistics.median(mc)))
    print("\n  >>> rho = median(m_c / m_d)     = %.6f" % rho)
    print("  >>> rows with m_d > m_c         = %d of %d  (%.1f%%)" % (n_gt, len(rows), 100 * frac))

    conf = (rho >= 1.0) and (frac < alpha_rows)
    refu = (rho <= 1.0) and (frac > alpha_rows)
    if conf and not refu:
        verdict = "CONFIRMATORY source test is LICENSED"
    elif refu and not conf:
        verdict = "REFUTATION test ONLY"
    else:
        verdict = "CANNOT ANSWER -- mixed/straddling; NO source-side family is licensed either way"
    print("\n  branch A (rho >= 1.0 AND m_d>m_c on < 50%%) : %s" % conf)
    print("  branch B (rho <= 1.0 AND m_d>m_c on > 50%%) : %s" % refu)
    print("  >>> FROZEN VERDICT: %s" % verdict)

    # --- robustness, explicitly NOT the criterion -----------------------------------------------
    print("\n  [robustness, NOT the criterion -- S-325 names d1]")
    for nm in ROBUSTNESS:
        c2 = [r["strict_protected_mass_band"][nm] for r in rows]
        print("     %-20s rho=%.6f   m_d>m_c on %.1f%% of rows"
              % (nm, statistics.median([c / m for c, m in zip(c2, md) if m > 0]),
                 100.0 * sum(1 for c, m in zip(c2, md) if m > c) / len(rows)))

    # --- domain unit, supplementary ---------------------------------------------------------------
    bd = collections.defaultdict(list)
    for r in rows:
        if r["demo_mass_band"] > 0:
            bd[r["domain"]].append(r["strict_protected_mass_band"][PRIMARY_DRAW]
                                   / r["demo_mass_band"])
    dm = {k: statistics.median(v) for k, v in bd.items()}
    print("\n  [supplementary, DOMAIN unit -- the criterion is frozen PER ROW] n_domains=%d" % len(dm))
    print("     median over domain medians = %.6f ; domains with rho<1 = %d of %d"
          % (statistics.median(list(dm.values())),
             sum(1 for v in dm.values() if v < 1.0), len(dm)))

    # --- the legacy field AM-40 quoted, for contrast ----------------------------------------------
    ref = [r["ctrl_mass_band_REFERENCE_ONLY"] for r in rows
           if r.get("ctrl_mass_band_REFERENCE_ONLY") is not None]
    if ref:
        print("\n  [context] ctrl_mass_band_REFERENCE_ONLY (UNPROTECTED pool -- the field whose own")
        print("            name says REFERENCE ONLY, and which AM-40 quoted as if it were the control):")
        print("     median ratio vs m_d = %.4f"
              % statistics.median([c / m for c, m in zip(ref, md) if m > 0]))
    return {"run": os.path.basename(run), "rho": rho, "frac_md_gt_mc": frac,
            "n_rows": len(rows), "verdict": verdict}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True,
                    help="a retrieval_strength run dir; repeat for several (never pooled)")
    ap.add_argument("--out", default=None, help="optional JSON summary path")
    a = ap.parse_args()
    out = [report(r) for r in a.run]
    if a.out:
        with open(a.out, "w") as fh:
            json.dump({"schema": "dcs_csi_mass_criterion/1",
                       "criterion": "S-325, applied to %s" % PRIMARY_DRAW,
                       "runs": out}, fh, indent=2)
        print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
