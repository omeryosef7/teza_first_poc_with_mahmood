"""analyze_dissociation.py -- turn the L8/L31 double-dissociation table into a committed artifact.

WHY THIS EXISTS. Review #8 audited the Sprint Final Report against the artifacts and found that
finding 4's double-dissociation numbers (`unembed_refusal` L31 +0.1031 / L8 -0.0082; the 3-D cell
span L31 -0.0108 / L8 +0.0287; `d_surface` L31 -0.0041 / L8 +0.0278) existed ONLY in the markdown.
Generations and judge runs were on disk; no analysis JSON aggregated them. That is precisely the
defect this sprint retracted twice already (R3-3, and the 0.5414 token-level figure), so the fix is
to emit the artifact rather than to soften the claim.

NOT a re-run: the same judge rows that backed the markdown table are re-aggregated here through the
shared estimator, so agreement with the published numbers is a check on my offline arithmetic.

ESTIMAND. Identical to analyze_control_recheck.py -- paired per prompt against the SAME baseline,
aggregated to domain clusters (G-1 df). Reuses that module's `load`/`paired`/`paired_diff` verbatim
so these numbers are directly comparable to the committed re-check table.

SCOPE / WHAT THIS CANNOT SHOW. A dissociation is a pattern across four cells, and only the four
per-cell estimates are tested here. "Significant at L31 and null at L8" is NOT a test of the
interaction; the depth x direction contrast is what would license the word "dissociation", so it is
computed explicitly (`interaction`) and the verdict keys off IT, not off the two marginal p-values.
This is the same difference-of-two-significances error the sprint flagged in review #4.

SAFETY: judge scalars only; never opens gens.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess

from analyze_control_recheck import REPO, load, paired, paired_diff, intervention_of


def git_commit_safe() -> str:
    """Provenance that cannot kill the analysis. Added 2026-08-22 after two crashes.

    `git rev-parse HEAD` raises FileNotFoundError on the batch nodes -- they have no git binary --
    and every caller invoked it INSIDE the literal that builds the output dict. So the run died
    before writing anything, and the artifact on disk silently kept its previous contents while
    `sacct` said FAILED. A stale file that reads as current is the worst possible failure mode, and
    it happened twice: once to analyze_qwen3_decomposition.py, then to analyze_dissociation.py after
    I fixed only the first and left its 25 siblings.

    The SLURM wrappers export BOOMB_GIT_COMMIT from the submitting host, so real provenance is
    preserved; absent that, this degrades to an explicit marker rather than to silence.
    """
    import os as _os
    import subprocess as _sp
    env = _os.environ.get("BOOMB_GIT_COMMIT")
    if env:
        return env.strip()
    try:
        r = _sp.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
        return f"unavailable:git_rc_{r.returncode}"
    except (FileNotFoundError, OSError) as exc:
        return f"unavailable:{type(exc).__name__}"


FIELDS = ("strongreject_score", "malicious_at_0.5")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--arm", action="append", default=[], metavar="NAME@LAYER=dir1,dir2",
                    help="repeatable; NAME@LAYER identifies the cell, dirs are judge shards")
    ap.add_argument("--interaction", action="append", default=[], metavar="NAME_A:NAME_B",
                    help="repeatable; paired depth x direction contrast between two named cells")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    base = load([a.baseline])
    n_base = len(base)
    if n_base == 0:
        raise SystemExit("[dissoc] baseline has no judged rows")

    cells, provenance = {}, {}
    for spec in a.arm:
        name, _, dirs = spec.partition("=")
        shards = [d for d in dirs.split(",") if d]
        if not shards:
            raise SystemExit(f"[dissoc] no judge dirs for {name}")
        rows = load(shards, expect=n_base)
        iv = intervention_of(shards[0])
        cells[name] = {
            "intervention": iv,
            "judge_dirs": shards,
            **{f: paired(base, rows, f) for f in FIELDS},
        }
        provenance[name] = rows

    inter = {}
    for spec in a.interaction:
        x, _, y = spec.partition(":")
        if x not in provenance or y not in provenance:
            raise SystemExit(f"[dissoc] interaction {spec} names an arm that was not loaded")
        inter[spec] = {
            "meaning": f"({x} - baseline) - ({y} - baseline), paired per prompt; baseline cancels",
            **{f: paired_diff(base, provenance[x], provenance[y], f) for f in FIELDS},
        }

    out = {
        "script": "src/boombness/analyze_dissociation.py",
        "purpose": "commit the L8/L31 double-dissociation cells that review #8 found were "
                   "markdown-only, and test the interaction rather than two marginal p-values",
        "estimand": "paired per prompt vs the same baseline, domain-clustered (G-1 df); identical "
                    "to analyze_control_recheck.py",
        "caveat": "a significant cell plus a null cell is NOT a dissociation; read `interaction`",
        "git_commit": git_commit_safe(),
        "baseline": a.baseline,
        "n_baseline_rows": n_base,
        "cells": cells,
        "interaction": inter,
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[dissoc] wrote {a.out}")
    for n, v in cells.items():
        s = v["strongreject_score"]
        print(f"  {n:24s} {s['delta_cluster_mean']:+.4f}  p {s['p_cl']:.4f}")
    for n, v in inter.items():
        s = v["strongreject_score"]
        print(f"  INTERACTION {n:20s} {s['delta_cluster_mean']:+.4f}  p {s['p_cl']:.4f}")


if __name__ == "__main__":
    main()
