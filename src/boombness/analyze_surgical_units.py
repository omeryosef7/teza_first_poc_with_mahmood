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
import os
import statistics as st
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_g8 import cluster_mean_ci  # noqa: E402
from common import read_jsonl, REPO_ROOT as REPO  # noqa: E402

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
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
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
    flags = {k: (ca.get(k), cb.get(k)) for k in ("layers", "topk")}
    differ = {k: v for k, v in flags.items() if v[0] != v[1]}
    if differ and arm != "all_layers_demo":
        return {"error": f"runs differ on {sorted(differ)} and arm {arm!r} is sensitive to them; "
                         f"only all_layers_demo ignores --layers/--topk", "n": len(pids),
                "config_diff": differ}

    # -- guard: identical baselines, else this is not a pairing -----------------------------
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
    base, eff, _ = load(run_dir, arm)
    pids = sorted(set(base) & set(eff))
    vals = [float(eff[p][READOUT]) - float(base[p][READOUT]) for p in pids]
    sem = st.stdev(vals) / len(vals) ** 0.5 if len(vals) > 1 else None
    return {"n": len(pids), "mean": st.mean(vals) if vals else None, "sem": sem,
            "baseline_fingerprint": base_fingerprint(base, pids)}


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
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                     capture_output=True, text=True).stdout.strip(),
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
        print(f"  {label}: ref {e['reference']['tag']} mean={e['reference']['mean']:+.4f}")
        for k, c in e["contrasts"].items():
            if "error" in c:
                print(f"     {k:34s} REFUSED: {c['error']}")
            else:
                print(f"     {k:34s} paired={c['paired_mean']:+.4f} t={c['paired_t']:+.2f} "
                      f"sign={c['n_positive']}/{c['n']} clustered p={c['clustered']['p_vs_0']}")


if __name__ == "__main__":
    main()
