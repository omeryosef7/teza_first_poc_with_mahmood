"""analyze_condition_profile.py — per-condition paired arm-minus-control profile, with inference.

WHY THIS EXISTS
---------------
The report's "SECOND CAUSAL RESULT" argues from a cross-condition profile: the effect is
"~0 on every benign condition and ~+0.056 on every harmful one", called a "clean split".
That table shipped **six deltas and zero p-values**, while the Qwen3 table printed directly
beside it carried `p_cl` on every cell and annotated two of them "(n.s.)".

Discounting the Qwen3 cells that fail a test the Llama cells were never given is an asymmetric
evidential standard, and it is load-bearing: the whole claim "harm-general, not doublespeak-specific"
rests on three harmful cells being alike and three benign cells being ~0.

This script gives both models the same test: paired by `prompt_id`, differenced arm - control,
aggregated to DOMAIN cluster means, t(G-1) on the cluster means. Same estimator the sprint uses
elsewhere (`analyze_g8.cluster_mean_ci`), reused rather than reimplemented.

REUSE: cluster_mean_ci / t_sf from analyze_g8 (scipy-backed since T4); RunDir/FailureLedger from common.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_g8 import cluster_mean_ci  # noqa: E402
from common import read_jsonl  # noqa: E402

SCORE = "strongreject_score"


def load(run_dir: str) -> Dict[str, dict]:
    """prompt_id -> row. Refuses on duplicate ids rather than silently keeping the last."""
    rows = read_jsonl(os.path.join(run_dir, "results.jsonl"))
    out: Dict[str, dict] = {}
    dupes = 0
    for r in rows:
        pid = r.get("prompt_id")
        if pid is None:
            continue
        if pid in out:
            dupes += 1
        out[pid] = r
    if dupes:
        raise SystemExit(f"[profile] {run_dir}: {dupes} duplicate prompt_id -- pairing is ambiguous")
    return out


def profile(arm: Dict[str, dict], ctrl: Dict[str, dict], label: str) -> dict:
    common = sorted(set(arm) & set(ctrl))
    dropped = {"arm_only": len(set(arm) - set(ctrl)), "ctrl_only": len(set(ctrl) - set(arm))}
    by_cond: Dict[str, Dict[str, List[float]]] = collections.defaultdict(lambda: collections.defaultdict(list))
    judge_bad = 0
    for pid in common:
        a, c = arm[pid], ctrl[pid]
        if a.get("judge_status") != "ok" or c.get("judge_status") != "ok":
            judge_bad += 1
            continue
        if a.get(SCORE) is None or c.get(SCORE) is None:
            judge_bad += 1
            continue
        cond = a.get("condition")
        dom = a.get("domain")
        by_cond[cond][dom].append(float(a[SCORE]) - float(c[SCORE]))

    cells = {}
    for cond, byd in sorted(by_cond.items()):
        n = sum(len(v) for v in byd.values())
        st = cluster_mean_ci({k: v for k, v in byd.items() if v})
        cells[cond] = {
            "n_pairs": n, "n_domains": st["n_clusters"],
            "delta": st["mean"], "se": st["se"],
            "ci95_domain_clustered": st["ci"],
            "p_cl": st["p_vs_0"],
            "degenerate": st.get("degenerate", False),
            "degenerate_reason": st.get("degenerate_reason"),
        }
    return {
        "label": label, "n_common": len(common), "dropped_unpaired": dropped,
        "dropped_judge_not_ok": judge_bad, "conditions": cells,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, help="judge run dir for the intervention arm")
    ap.add_argument("--control", required=True, help="judge run dir for its matched control")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    res = profile(load(a.arm), load(a.control), a.label)
    res["runs"] = {"arm": os.path.abspath(a.arm), "control": os.path.abspath(a.control)}
    res["estimator"] = ("paired by prompt_id, differenced arm-control, aggregated to DOMAIN "
                        "cluster means, t(G-1) on the cluster means (analyze_g8.cluster_mean_ci)")
    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                                    text=True).stdout.strip())
    except Exception:
        git, dirty = None, None
    res["provenance"] = {"argv": sys.argv, "git_commit": git, "git_dirty": dirty,
                         "python": sys.executable}

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1)

    print(f"[profile] {a.label}  n_common={res['n_common']}  "
          f"unpaired={res['dropped_unpaired']}  judge_not_ok={res['dropped_judge_not_ok']}")
    print(f"{'condition':<26}{'delta':>10}{'p_cl':>10}{'G':>4}{'n':>6}   ci95")
    for cond, c in res["conditions"].items():
        ci = c["ci95_domain_clustered"]
        cis = "degenerate: " + str(c["degenerate_reason"]) if ci is None else \
            "[%+.4f, %+.4f]" % (ci[0], ci[1])
        p = c["p_cl"]
        star = "" if p is None else ("  ***" if p < 0.01 else "  *" if p < 0.05 else "  n.s.")
        print("%-26s%+10.4f%10s%4s%6d   %s%s" % (
            cond, c["delta"], "n/a" if p is None else "%.4f" % p,
            c["n_domains"], c["n_pairs"], cis, star))
    print(f"[profile] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
