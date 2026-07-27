"""
analyze_behavioral_causality.py — paired bootstrap CIs on the behavioral necessity/sufficiency
effects (plan §13). Reads the label-level raw jsonl (no harmful text used — only cat labels) and
reuses stats.paired_bootstrap_ci (n-guarded). Benign scalar analysis; main-loop only.

Necessity (per window, among baseline-MALICIOUS items):
  - flip rate Δ = P(patched != MALICIOUS), with CI
  - necessity − random  = paired CI of (flip_nec − flip_rand)   [specificity vs matched random]
  - necessity − identity = paired CI of (flip_nec − flip_identity)
Sufficiency (per window, among baseline-BENIGN items):
  - DS − Direct = paired CI of (1[suff_DS==MAL] − 1[suff_Direct==MAL])

Usage: python analyze_behavioral_causality.py --necessity-dir <dir> --sufficiency-dir <dir> [...]
"""
import os
import sys
import json
import argparse
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats


def _ci(x, y=None):
    """Bootstrap CI: one-sample mean of x if y is None, else paired mean(x-y)."""
    if y is None:
        y = [0.0] * len(x)
    r = stats.paired_bootstrap_ci(x, y, n_boot=10000, seed=0)
    return {"mean": round(r["mean_diff"], 3), "lo": round(r["lo"], 3),
            "hi": round(r["hi"], 3), "n": r["n"], "ci_reliable": r["ci_reliable"]}


def necessity_cis(nec_dir):
    rows = [json.loads(l) for l in open(os.path.join(nec_dir, "necessity_raw.jsonl"))]
    # group necessity_{window} rows (they carry cat/id_cat/rand_cat/base_mal)
    by_win = defaultdict(list)
    for r in rows:
        if r["arm"].startswith("necessity_") and r.get("base_mal"):
            win = r["arm"][len("necessity_"):]
            by_win[win].append(r)
    out = {}
    for win, rs in by_win.items():
        flip_nec = [float(r["cat"] != "MALICIOUS") for r in rs]
        flip_id = [float(r["id_cat"] != "MALICIOUS") for r in rs]
        flip_rand = [float(r["rand_cat"] != "MALICIOUS") for r in rs]
        out[win] = {
            "n_base_mal": len(rs),
            "delta_necessity": _ci(flip_nec),
            "necessity_minus_random": _ci(flip_nec, flip_rand),
            "necessity_minus_identity": _ci(flip_nec, flip_id),
        }
    return out


def sufficiency_cis(suf_dir):
    rows = [json.loads(l) for l in open(os.path.join(suf_dir, "sufficiency_raw.jsonl"))]
    # baseline-benign set per (base_id, codeword)
    benign = {(r["base_id"], r["codeword"]) for r in rows
              if r["arm"] == "baseline_neutral" and r["cat"] == "BENIGN"}
    ds = {(r["base_id"], r["codeword"]): r for r in rows if r["arm"].startswith("suff_DS_")}
    di = {(r["base_id"], r["codeword"]): r for r in rows if r["arm"].startswith("suff_Direct_")}
    win = next((r["arm"][len("suff_DS_"):] for r in rows if r["arm"].startswith("suff_DS_")), "?")
    x_ds, x_dir = [], []
    for k in benign:
        if k in ds and k in di:
            x_ds.append(float(ds[k]["cat"] == "MALICIOUS"))
            x_dir.append(float(di[k]["cat"] == "MALICIOUS"))
    return {win: {"n_base_benign": len(x_ds),
                  "suff_DS_rate": _ci(x_ds), "suff_Direct_rate": _ci(x_dir),
                  "DS_minus_Direct": _ci(x_ds, x_dir)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--necessity-dir", default=None)
    ap.add_argument("--sufficiency-dir", action="append", default=[],
                    help="repeatable: one per window-sweep job")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    result = {}
    if args.necessity_dir:
        result["necessity"] = necessity_cis(args.necessity_dir)
        print("[necessity] per-window CIs (among baseline-malicious):")
        for w, r in result["necessity"].items():
            print(f"  {w:16s} Δ={r['delta_necessity']['mean']} "
                  f"[{r['delta_necessity']['lo']},{r['delta_necessity']['hi']}] | "
                  f"nec−rand={r['necessity_minus_random']['mean']} "
                  f"[{r['necessity_minus_random']['lo']},{r['necessity_minus_random']['hi']}]")
    suff = {}
    for d in args.sufficiency_dir:
        suff.update(sufficiency_cis(d))
    if suff:
        result["sufficiency"] = suff
        print("[sufficiency] per-window DS vs Direct (among baseline-benign):")
        for w, r in suff.items():
            print(f"  {w:16s} DS={r['suff_DS_rate']['mean']} Direct={r['suff_Direct_rate']['mean']} "
                  f"DS−Direct={r['DS_minus_Direct']['mean']} "
                  f"[{r['DS_minus_Direct']['lo']},{r['DS_minus_Direct']['hi']}] (n={r['n_base_benign']})")
    if args.out:
        json.dump(result, open(args.out, "w"), indent=2)
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
