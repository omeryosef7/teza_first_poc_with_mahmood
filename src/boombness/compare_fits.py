"""compare_fits.py — E12: is `d_surface` a CONCEPT-surface direction, or a bomb-detector?

THE QUESTION E6 COULD NOT ASK. E6 changed the codeword (`carrot` -> `button`) and held the concept,
so it tests whether the direction is a *carrot*-detector. `d_surface` is named for the claim that it
carries **concept surface identity**, and that claim can only be tested by changing the **concept**.

THE TEST NEEDS NO GENERATION AND NO JUDGE. Fit `d_surface` twice by the same 2x2 estimator -- once on
carrot<->bomb, once on carrot<->knife -- and take the per-layer cosine. Interpretation:

  * cos near 1  -> one direction, independent of which concept the codeword stands for. That is what
                   "concept-surface direction" would mean, and it would make every carrot<->bomb
                   result a statement about the mechanism rather than about bombs.
  * cos near 0  -> two different directions that happen to share an estimator. The sprint's results
                   would then be about `bomb` specifically, and the name `d_surface` would be
                   overclaiming.

WHAT IT CANNOT SETTLE. A high cosine shows the fitted directions agree; it does not show either is
causal -- that is the ablation experiment, and it is separate. And the sign convention of a
diff-of-means is fixed by cell order, which is identical in both fits, so a negative cosine would be
a real disagreement rather than a bookkeeping artifact.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import population_block  # noqa: E402


def _load(fit_dir: str):
    p = os.path.join(fit_dir, "directions_fit_dev.pt")
    if not os.path.exists(p):
        p = os.path.join(fit_dir, "directions_fit_heldout.pt")
    import torch
    return p, torch.load(p, map_location="cpu", weights_only=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fit-a", required=True, help="e.g. the carrot<->bomb fit")
    ap.add_argument("--fit-b", required=True, help="e.g. the carrot<->knife fit")
    ap.add_argument("--label-a", default="bomb")
    ap.add_argument("--label-b", default="knife")
    ap.add_argument("--directions", default="d_surface,d_context,d_naive")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import torch
    pa, A = _load(sorted(glob.glob(args.fit_a))[-1])
    pb, B = _load(sorted(glob.glob(args.fit_b))[-1])
    out = {"fit_a": os.path.abspath(pa), "fit_b": os.path.abspath(pb),
           "label_a": args.label_a, "label_b": args.label_b,
           "question": "does d_surface survive a change of CONCEPT (E12)?",
           "population_a": population_block(None, model=str((A.get("meta") or {}).get("model"))),
           "population_b": population_block(None, model=str((B.get("meta") or {}).get("model"))),
           "cosines": {}}
    for name in args.directions.split(","):
        if name not in A or name not in B:
            continue
        per = {}
        for L in sorted(set(A[name]) & set(B[name])):
            u, v = A[name][L].float(), B[name][L].float()
            per[str(L)] = float(torch.dot(u, v) / (u.norm() * v.norm()))
        if per:
            vals = list(per.values())
            out["cosines"][name] = {"by_layer": per, "n_layers": len(vals),
                                    "mean": sum(vals) / len(vals),
                                    "min": min(vals), "max": max(vals)}
    out["provenance"] = {"argv": sys.argv,
                         "git_commit": subprocess.run(["git", "rev-parse", "HEAD"],
                                                      capture_output=True, text=True).stdout.strip()}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    for name, c in out["cosines"].items():
        print(f"  {name:12s} n_layers={c['n_layers']:>3d}  mean cos={c['mean']:+.4f}  "
              f"range [{c['min']:+.4f}, {c['max']:+.4f}]")
    print(f"[compare_fits] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
