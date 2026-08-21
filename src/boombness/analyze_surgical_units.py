"""analyze_surgical_units.py -- plan §9 deliverable: the demo-scope contrasts, as an ARTIFACT.

WHY THIS EXISTS. Review #3 finding R3-3: the Phase G headline contrasts existed in no committed
file -- they had been computed ad hoc and quoted from a commit message. `analyze_g1_g3.py` emits
per-run arm means (`g3_*.json`) but never the CONTRAST between two runs, which is the estimand the
result is actually about. This script is that missing producer.

THE ESTIMAND, AND WHY IT IS PAIRED. Two `surgical_knockout` runs that differ only in `--demo-scope`
score the SAME prompts and, because the `none` arm performs no intervention, carry BIT-IDENTICAL
baselines. So the arms are exactly pairable and the right quantity is the per-prompt difference of
differences

    d_p = [effect(scope A) - base]_p  -  [effect(scope B) - base]_p

aggregated to DOMAIN clusters (`cluster_mean_ci`, G-1 df). Review #3 found the earlier write-up had
quoted two independent sems where this paired test was available and far tighter. The script
VERIFIES the baseline identity rather than assuming it, and refuses the contrast if it fails --
non-identical baselines mean the two runs are not the same experiment and the pairing is a fiction.

WHAT IT WILL NOT DO. Only `all_layers_demo` is comparable across runs that differ in `--layers` or
`--topk`: that arm ignores both flags, every other arm does not (`positive_control` is +0.2583 in one
committed run and -4.6579 in another for exactly this reason). The script reads `--layers`/`--topk`
out of each run's own config and REFUSES a cross-run contrast on any other arm when they differ.

REUSE: cluster_mean_ci (analyze_g8), read_jsonl/REPO_ROOT (common).
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import math
import os
import statistics as st
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_g8 import cluster_mean_ci  # noqa: E402
from common import read_jsonl, REPO_ROOT as REPO  # noqa: E402


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


READOUT = "semantic_logodds"
BASE_ARM = "none"


def resolve(tag_or_dir: str) -> str:
    if os.path.isdir(tag_or_dir):
        return tag_or_dir
    hits = sorted(glob.glob(os.path.join(REPO, "outputs/boombness/surgical_knockout",
                                         f"{tag_or_dir}_*")))
    hits = [h for h in hits if os.path.exists(os.path.join(h, "results.jsonl"))]
    if not hits:
        raise SystemExit(f"[units] no completed surgical_knockout run for tag {tag_or_dir!r}")
    return hits[-1]


def load(run_dir: str, arm: str) -> Tuple[Dict[str, dict], Dict[str, dict], dict]:
    base, eff = {}, {}
    for r in read_jsonl(os.path.join(run_dir, "results.jsonl")):
        if r.get("arm") == BASE_ARM:
            base[r["prompt_id"]] = r
        elif r.get("arm") == arm:
            eff[r["prompt_id"]] = r
    cfg_path = os.path.join(run_dir, "config.json")
    raw = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
    # `RunDir` writes the CLI under config["args"], not at the top level. The first version read
    # `cfg.get("layers")` from the top level, which is absent in all 49 committed runs -- so the
    # comparability guard below compared None to None, never fired, and the artifact recorded
    # `"config": {"layers": null, "topk": null}` for runs that all used 8,12,18,24 / 16. A guard
    # that cannot fail is not a guard (review #4).
    cfg = dict(raw.get("args", {})) if isinstance(raw.get("args"), dict) else {}
    return base, eff, cfg


def base_fingerprint(base: Dict[str, dict], pids: List[str]) -> str:
    h = hashlib.sha256()
    for p in pids:
        h.update(p.encode())
        h.update(repr(round(float(base[p][READOUT]), 9)).encode())
    return h.hexdigest()[:16]


def contrast(a_dir: str, b_dir: str, arm: str) -> dict:
    ba, ea, ca = load(a_dir, arm)
    bb, eb, cb = load(b_dir, arm)
    pids = sorted(set(ea) & set(eb) & set(ba) & set(bb))
    if not pids:
        return {"error": "no shared prompt_id", "n": 0}

    # -- guard: the two runs must be comparable on this arm ---------------------------------
    # Flags compared: the two that change which edges an arm cuts, PLUS the ones that change what
    # experiment it is. Review #4's point stands even where no shipped contrast is affected -- the
    # only cross-run check here was one float comparison on one derived scalar, and bank, model,
    # dtype, fit_dir, query_kind, condition and seed were all unchecked.
    SENSITIVE = ("layers", "topk")
    IDENTITY = ("bank", "model", "dtype", "fit_dir", "query_kind", "condition", "seed", "dst")
    flags = {k: (ca.get(k), cb.get(k)) for k in SENSITIVE + IDENTITY}
    if not ca or not cb:
        return {"error": "one run has no config.json/args block; comparability is unverifiable",
                "n": len(pids)}
    id_differ = {k: flags[k] for k in IDENTITY if flags[k][0] != flags[k][1]}
    if id_differ:
        return {"error": f"the two runs are not the same experiment: they differ on "
                         f"{sorted(id_differ)}", "n": len(pids), "config_diff": id_differ}
    differ = {k: flags[k] for k in SENSITIVE if flags[k][0] != flags[k][1]}
    if differ and arm != "all_layers_demo":
        return {"error": f"runs differ on {sorted(differ)} and arm {arm!r} is sensitive to them; "
                         f"only all_layers_demo ignores --layers/--topk", "n": len(pids),
                "config_diff": differ}

    # -- guard: identical baselines, else this is not a pairing -----------------------------
    # NON-FINITE FIRST. `nan > 1e-9` is False, so a NaN baseline sailed through this guard and then
    # crashed inside cluster_mean_ci's stdev -- reproduced on the Qwen3 run, whose readout logits
    # are non-finite on 19 of 20 shared prompts. Refuse it here, by name (review #4).
    nonfinite = [p for p in pids
                 if not (math.isfinite(float(ba[p][READOUT])) and math.isfinite(float(bb[p][READOUT]))
                         and math.isfinite(float(ea[p][READOUT])) and math.isfinite(float(eb[p][READOUT])))]
    if nonfinite:
        return {"error": f"{len(nonfinite)} of {len(pids)} shared prompts have a NON-FINITE "
                         f"{READOUT} in at least one run; a contrast over them is meaningless",
                "n": len(pids), "n_nonfinite": len(nonfinite),
                "example_prompt_ids": nonfinite[:3]}
    worst = max(abs(float(ba[p][READOUT]) - float(bb[p][READOUT])) for p in pids)
    if worst > 1e-9:
        return {"error": f"baselines are NOT identical (max |diff| = {worst:.3e}); the two runs are "
                         f"not the same experiment and cannot be paired", "n": len(pids)}

    d = {p: (float(ea[p][READOUT]) - float(ba[p][READOUT]))
            - (float(eb[p][READOUT]) - float(bb[p][READOUT])) for p in pids}
    vals = [d[p] for p in pids]
    by_cl: Dict[str, List[float]] = collections.defaultdict(list)
    for p in pids:
        by_cl[str(ba[p].get("domain"))].append(d[p])
    cl = cluster_mean_ci(dict(by_cl), n_effective=len(pids))
    sem = st.stdev(vals) / len(vals) ** 0.5 if len(vals) > 1 else None
    return {
        "n": len(pids),
        "baselines_identical": True,
        "baseline_fingerprint": base_fingerprint(ba, pids),
        "paired_mean": st.mean(vals),
        "paired_sem": sem,
        "paired_t": (st.mean(vals) / sem) if sem else None,
        "n_positive": sum(1 for v in vals if v > 0),
        "n_negative": sum(1 for v in vals if v < 0),
        "clustered": cl,
        "config": {"layers": ca.get("layers"), "topk": ca.get("topk")},
    }


def arm_mean(run_dir: str, arm: str) -> dict:
    """Per-run mean effect. Non-finite rows are DROPPED AND COUNTED, never averaged in.

    `contrast()` grew a non-finite guard after review #4; this function ran first and had none, so
    a run with NaN readout logits (the Qwen3 knockout: 19 of 20 rows) crashed here before the guard
    could speak. Dropping is right for a per-run summary -- unlike a contrast, a mean over the
    finite subset is still a statement about that subset -- but only if the count is reported.
    """
    base, eff, _ = load(run_dir, arm)
    pids = sorted(set(base) & set(eff))
    ok = [p for p in pids
          if math.isfinite(float(base[p][READOUT])) and math.isfinite(float(eff[p][READOUT]))]
    vals = [float(eff[p][READOUT]) - float(base[p][READOUT]) for p in ok]
    sem = st.stdev(vals) / len(vals) ** 0.5 if len(vals) > 1 else None
    return {"n": len(ok), "n_shared_prompts": len(pids),
            "n_dropped_nonfinite": len(pids) - len(ok),
            "mean": st.mean(vals) if vals else None, "sem": sem,
            "reportable": len(pids) > 0 and len(ok) == len(pids),
            "baseline_fingerprint": base_fingerprint(base, ok)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", action="append", default=[], metavar="LABEL=REF:A,B,C",
                    help="repeatable. LABEL names a codeword/bank family; A,B,C are run tags or "
                         "dirs; REF is the tag every other one is contrasted AGAINST.")
    ap.add_argument("--arm", default="all_layers_demo")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = {
        "script": "src/boombness/analyze_surgical_units.py",
        "plan_section": "§9 -- surgical units, demo-scope contrasts",
        "arm": args.arm,
        "readout": READOUT,
        "estimand": "paired per-prompt difference-of-differences vs the reference scope, "
                    "aggregated to DOMAIN clusters (G-1 df); baseline identity verified",
        "git_commit": git_commit_safe(),
        "sets": {},
    }
    for spec in args.set:
        label, rest = spec.split("=", 1)
        ref, others = rest.split(":", 1)
        tags = [t for t in others.split(",") if t]
        ref_dir = resolve(ref)
        entry = {"reference": {"tag": ref, "run": ref_dir, **arm_mean(ref_dir, args.arm)},
                 "arms": {}, "contrasts": {}}
        for t in tags:
            d = resolve(t)
            entry["arms"][t] = {"run": d, **arm_mean(d, args.arm)}
            entry["contrasts"][f"{ref} - {t}"] = contrast(ref_dir, d, args.arm)
        out["sets"][label] = entry

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"[units] wrote {args.out}")
    for label, e in out["sets"].items():
        m = e["reference"]["mean"]
        drop = e["reference"].get("n_dropped_nonfinite", 0)
        print(f"  {label}: ref {e['reference']['tag']} "
              f"mean={'n/a' if m is None else format(m, '+.4f')}"
              + (f"  [DROPPED {drop} non-finite]" if drop else ""))
        for k, c in e["contrasts"].items():
            if "error" in c:
                print(f"     {k:34s} REFUSED: {c['error']}")
            else:
                print(f"     {k:34s} paired={c['paired_mean']:+.4f} t={c['paired_t']:+.2f} "
                      f"sign={c['n_positive']}/{c['n']} clustered p={c['clustered']['p_vs_0']}")


if __name__ == "__main__":
    main()
