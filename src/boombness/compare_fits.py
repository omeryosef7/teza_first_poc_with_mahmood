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


def git_commit_safe() -> str:
    """Provenance that cannot kill the analysis. Added 2026-08-22 after two crashes.

    `git rev-parse HEAD` raises FileNotFoundError on the batch nodes -- they have no git binary --
    and callers invoke it INSIDE the literal that builds the output dict, so the run dies before
    writing anything and the artifact on disk silently keeps its previous contents while `sacct`
    says FAILED. A stale file that reads as current is the worst failure mode available, and it
    happened twice: to analyze_qwen3_decomposition.py, then to analyze_dissociation.py after only
    the first was fixed and its siblings left alone.

    The SLURM wrappers export BOOMB_GIT_COMMIT from the submitting host, so real provenance is
    preserved; absent that this degrades to an explicit marker rather than to silence.
    """
    import os as _os
    import subprocess as _sp
    env = _os.environ.get("BOOMB_GIT_COMMIT")
    if env:
        return env.strip()
    try:
        _kw = {"capture_output": True, "text": True}
        _repo = globals().get("REPO")
        if _repo:
            _kw["cwd"] = _repo
        r = _sp.run(["git", "rev-parse", "HEAD"], **_kw)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
        return f"unavailable:git_rc_{r.returncode}"
    except (FileNotFoundError, OSError) as exc:
        return f"unavailable:{type(exc).__name__}"


def git_dirty_safe(*args) -> object:
    """Companion for the `git status --porcelain` dirty-flag calls. Never raises."""
    import subprocess as _sp
    try:
        _kw = {"capture_output": True, "text": True}
        _repo = globals().get("REPO")
        if _repo:
            _kw["cwd"] = _repo
        return bool(_sp.run(["git", "status", "--porcelain", *args], **_kw).stdout.strip())
    except (FileNotFoundError, OSError):
        return None



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
    # THE CEILING IS PART OF THE NUMBER. A cross-concept cosine of 0.61 means nothing until you know
    # what the SAME concept scores against itself: if the estimator were noisy, 0.61 might BE
    # agreement. Each fit dir carries a dev and a heldout direction fitted on disjoint families, so
    # the within-concept cosine is the noise ceiling and it costs nothing to compute. (Same lesson as
    # E6's knockout, where a +0.1 delta was meaningless until read against a -17 deletion ceiling.)
    def _within(fit_glob, name):
        import torch as _t
        d = sorted(glob.glob(fit_glob))[-1]
        try:
            a = _t.load(os.path.join(d, "directions_fit_dev.pt"), map_location="cpu", weights_only=False)
            b = _t.load(os.path.join(d, "directions_fit_heldout.pt"), map_location="cpu", weights_only=False)
        except Exception:
            return None
        if name not in a or name not in b:
            return None
        v = []
        for L in sorted(set(a[name]) & set(b[name])):
            u, w = a[name][L].float(), b[name][L].float()
            v.append(float(torch.dot(u, w) / (u.norm() * w.norm())))
        return {"mean": sum(v) / len(v), "min": min(v), "max": max(v), "n_layers": len(v)} if v else None

    for name in list(out["cosines"]):
        out["cosines"][name]["within_concept_ceiling"] = {
            args.label_a: _within(args.fit_a, name),
            args.label_b: _within(args.fit_b, name)}
        ceil = [c["mean"] for c in out["cosines"][name]["within_concept_ceiling"].values() if c]
        if ceil:
            out["cosines"][name]["across_over_ceiling"] = out["cosines"][name]["mean"] / (sum(ceil) / len(ceil))

    out["provenance"] = {"argv": sys.argv,
                         "git_commit": git_commit_safe()}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    for name, c in out["cosines"].items():
        cl = c.get("within_concept_ceiling") or {}
        cs = " ".join(f"{k}={v['mean']:+.4f}" for k, v in cl.items() if v)
        print(f"  {name:12s} across={c['mean']:+.4f} [{c['min']:+.4f},{c['max']:+.4f}]   "
              f"within-concept ceiling: {cs}   ratio={c.get('across_over_ceiling', float('nan')):.3f}")
    print(f"[compare_fits] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
