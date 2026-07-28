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
    """Per-CONDITION (base_id, codeword, context_len) paired CI, PER WINDOW (from the arm name).
    Fixes an audit bug where keying on (base,cw) only collapsed the 3 context_len replicates to 1
    (last-wins) and mixed windows. context_len may be absent in pre-iter18 raw → falls back to a
    (base,cw)-collapsed key for those runs (unavoidable without context_len in the log)."""
    rows = [json.loads(l) for l in open(os.path.join(suf_dir, "sufficiency_raw.jsonl"))]
    key = lambda r: (r["base_id"], r["codeword"], r.get("context_len"))
    benign = {key(r) for r in rows if r["arm"] == "baseline_neutral" and r["cat"] == "BENIGN"}
    by_win = defaultdict(lambda: {"ds": {}, "di": {}})
    for r in rows:
        for pfx, side in (("suff_DS_", "ds"), ("suff_Direct_", "di")):
            if r["arm"].startswith(pfx):
                by_win[r["arm"][len(pfx):]][side][key(r)] = r
    out = {}
    for win, d in by_win.items():
        x_ds, x_dir = [], []
        # sorted → deterministic CI (set iteration order is hash-randomized per process)
        for k in sorted(benign, key=lambda t: tuple(str(v) for v in t)):  # per-condition, baseline-BENIGN
            if k in d["ds"] and k in d["di"]:
                x_ds.append(float(d["ds"][k]["cat"] == "MALICIOUS"))
                x_dir.append(float(d["di"][k]["cat"] == "MALICIOUS"))
        if x_ds:
            out[win] = {"n_base_benign": len(x_ds),
                        "suff_DS_rate": _ci(x_ds), "suff_Direct_rate": _ci(x_dir),
                        "DS_minus_Direct": _ci(x_ds, x_dir)}
    return out


def timing_cis(suf_dirs):
    """Headline TOCTOU refusal gradient, reproducibly from raw (no hand-computed numbers).
    Direct-injection REFUSAL indicator (cat==REJECTED) per-CONDITION (base,cw,context_len), among
    baseline-BENIGN, paired across the early/mid/late window dirs. Returns per-window refusal rate +
    paired early−late / early−mid / mid−late deltas with bootstrap CIs on the conditions common to
    both windows of each pair."""
    # window -> {condition_key: refused(0/1)} for Direct injection on baseline-benign conditions
    win_ref = {}
    for d in suf_dirs:
        rows = [json.loads(l) for l in open(os.path.join(d, "sufficiency_raw.jsonl"))]
        key = lambda r: (r["base_id"], r["codeword"], r.get("context_len"))
        benign = {key(r) for r in rows if r["arm"] == "baseline_neutral" and r["cat"] == "BENIGN"}
        for r in rows:
            if r["arm"].startswith("suff_Direct_") and key(r) in benign:
                win_ref.setdefault(r["arm"][len("suff_Direct_"):], {})[key(r)] = float(r["cat"] == "REJECTED")
    if not win_ref:
        return {}
    order = {"early": 0, "mid": 1, "late": 2}
    wins = sorted(win_ref, key=lambda w: order.get(w, 9))
    out = {"per_window_refusal": {w: _ci([win_ref[w][k] for k in sorted(win_ref[w],
                                          key=lambda t: tuple(str(v) for v in t))]) for w in wins}}
    for a, b in (("early", "late"), ("early", "mid"), ("mid", "late")):
        if a in win_ref and b in win_ref:
            common = sorted(set(win_ref[a]) & set(win_ref[b]), key=lambda t: tuple(str(v) for v in t))
            if common:
                out[f"{a}_minus_{b}_refusal"] = _ci([win_ref[a][k] for k in common],
                                                     [win_ref[b][k] for k in common])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--necessity-dir", default=None)
    ap.add_argument("--sufficiency-dir", action="append", default=[],
                    help="repeatable: one per window-sweep job")
    ap.add_argument("--timing-dir", action="append", default=[],
                    help="repeatable early/mid/late sufficiency dirs → reproducible TOCTOU refusal gradient")
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
    if args.timing_dir:
        result["timing"] = timing_cis(args.timing_dir)
        t = result["timing"]
        print("[timing] TOCTOU refusal gradient (Direct-injection, per-condition, baseline-benign):")
        for w, r in t.get("per_window_refusal", {}).items():
            print(f"  refusal[{w:5s}] = {r['mean']} [{r['lo']},{r['hi']}] (n={r['n']})")
        for k in ("early_minus_late_refusal", "early_minus_mid_refusal", "mid_minus_late_refusal"):
            if k in t:
                r = t[k]; print(f"  {k:26s} = {r['mean']} [{r['lo']},{r['hi']}] (n={r['n']})")
    if args.out:
        json.dump(result, open(args.out, "w"), indent=2)
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
