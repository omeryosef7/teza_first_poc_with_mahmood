#!/usr/bin/env python3
"""DCS-C-061 v2 — calibrate the null AS PR-035 ACTUALLY USES IT.

v1 (`dcs_null_calibration.py`) called `loo_domain` with NO `selection_rows`, so its picks were
grid-searched on the TEST population's own labels. That is the C-057 §28.2 defect, not the procedure
`PR-035` runs: every contrast that matters passes `selection_rows` (`:657` for the two 2-class
contrasts, `:597` for the primary), so the picks come from cell `B` and are independent of the test
labels — which is exactly the exchangeability that licenses freezing them (`PR-031d` §10.3).

v1's numbers are therefore a measurement of THE DEFECT, not of the design. They are still useful, and
are reported here as the `no_selection` arm, because they quantify what C-057 warned about.

Four arms per class-count, all on the same synthetic data with the same seeds:

  selection=cellB,  null=ORIGINAL    <- what PR-035 actually did. THE NUMBER THAT DECIDES.
  selection=cellB,  null=EXCLUDING   <- PR-039's proposed fix
  selection=testset,null=ORIGINAL    <- the §28.2 defect, i.e. v1
  selection=testset,null=EXCLUDING

Measured on PURE NOISE (false-positive rate; must be <= alpha) and on a PLANTED SIGNAL (power).
"""
import sys, os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import dcs_bombness_specificity as M

NREP, NPERM, H = 100, 100, 32
DOMS = [f"d{i}" for i in range(6)]
LAYERS = list(M.LAYERS_ALLOWED)
ALPHA = 0.05


def group_permute_ORIGINAL(rows, rng, classes):
    """The null exactly as it stood at 40bcc969, before PR-039."""
    out = []
    for d in sorted({r["domain"] for r in rows}):
        perm = list(classes)
        rng.shuffle(perm)
        mapping = dict(zip(classes, perm))
        for r in rows:
            if r["domain"] == d:
                q = dict(r)
                q["perm_label"] = mapping[r.get("perm_group", r["concept"])]
                out.append(q)
    return out


def perm_p(rows, classes, picks, obs, seed, gp):
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(NPERM):
        pd = M.loo_with_picks(gp(rows, rng, list(classes)), LAYERS, classes,
                              lambda r: r["perm_label"], picks)
        if pd:
            null.append(float(np.mean(list(pd.values()))))
    null = np.array(null)
    return (1.0 + float((null >= obs).sum())) / (1.0 + len(null))


def make(rng, classes, sep, n_per=12):
    rows = []
    for d in DOMS:
        for ci, c in enumerate(classes):
            for _ in range(n_per):
                v = rng.normal(0, 1, (len(LAYERS), H))
                v[:, 0] += sep * ci                      # signal lives in one coordinate
                rows.append(dict(domain=d, concept=c, cell="C", block="b", split="s",
                                 n_examples=4, family=None, codeword="x", n_chars=100,
                                 layers=LAYERS, vec=v))
    return rows


def main():
    lab = lambda r: r["concept"]
    for classes in (("a", "b"), ("a", "b", "c")):
        for sep, what in ((0.0, "PURE NOISE  (FPR must be <= 0.05)"),
                          (1.2, "PLANTED SIGNAL  (power)")):
            acc = {k: [] for k in ("B_orig", "B_excl", "T_orig", "T_excl")}
            for rep in range(NREP):
                rng = np.random.default_rng(5000 + rep)
                C = make(rng, classes, sep)                 # the test population
                B = make(rng, classes, sep, n_per=4)        # an INDEPENDENT selection population
                oB = M.loo_domain(C, LAYERS, classes, lab, selection_rows=B, tag="c")
                oT = M.loo_domain(C, LAYERS, classes, lab, tag="c")
                if oB["mean_acc"] is None or oT["mean_acc"] is None:
                    continue
                acc["B_orig"].append(perm_p(C, classes, oB["picks"], oB["mean_acc"], 7, group_permute_ORIGINAL))
                acc["B_excl"].append(perm_p(C, classes, oB["picks"], oB["mean_acc"], 7, M.group_permute))
                acc["T_orig"].append(perm_p(C, classes, oT["picks"], oT["mean_acc"], 7, group_permute_ORIGINAL))
                acc["T_excl"].append(perm_p(C, classes, oT["picks"], oT["mean_acc"], 7, M.group_permute))
            print(f"\n{len(classes)}-class  {what}   (n={len(acc['B_orig'])} reps, n_perm={NPERM})")
            for k, desc in (("B_orig", "selection=cellB   null=ORIGINAL   <- WHAT PR-035 DID"),
                            ("B_excl", "selection=cellB   null=EXCLUDING  <- PR-039's fix"),
                            ("T_orig", "selection=TESTSET null=ORIGINAL   <- the §28.2 defect (v1)"),
                            ("T_excl", "selection=TESTSET null=EXCLUDING")):
                ps = acc[k]
                if not ps:
                    continue
                rate = sum(1 for p in ps if p <= ALPHA) / len(ps)
                print(f"   {desc:52s} rate={rate:.3f}  median p={np.median(ps):.3f}  min={min(ps):.4f}")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
