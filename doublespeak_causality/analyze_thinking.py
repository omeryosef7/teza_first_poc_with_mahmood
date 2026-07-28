"""
analyze_thinking.py — Phase 7 (Level 6): paired thinking-ON vs thinking-OFF behavioral comparison.
Consumes the two Qwen3 screen dirs' `per_condition_corrected.json` (produced by analyze_screen.py, which
recomputes the fixed refusal-language classify). Matches conditions by (base_id, codeword, context_len)
and compares:
  - DS outcome distribution (MALICIOUS/REJECTED/BENIGN) thinking vs non-thinking;
  - Direct refusal rate, Neutral benign rate, base eligibility, clean-success rate;
  - the PAIRED transition matrix (nothink DS outcome → think DS outcome) — does reasoning flip outcomes?
Tests plan §11.6 hypotheses (thinking amplifies attack / improves safety / shifts location).

Benign scalar analysis (reads corrected labels; no harmful text). CPU-only.

Usage: python analyze_thinking.py --think-dir <screen dir> --nothink-dir <screen dir>
"""
import os
import sys
import json
import argparse
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats


def load_pc(d):
    p = os.path.join(d, "per_condition_corrected.json")
    if not os.path.exists(p):
        raise SystemExit(f"missing {p} — run analyze_screen.py --screen-dir {d} first")
    return {(r["base_id"], r["codeword"], r["context_len"]): r for r in json.load(open(p))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--think-dir", required=True)
    ap.add_argument("--nothink-dir", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    th, no = load_pc(args.think_dir), load_pc(args.nothink_dir)
    keys = sorted(set(th) & set(no))  # matched conditions
    print(f"[thinking] matched conditions: {len(keys)}")

    def rates(pc, ks):
        ds = Counter(pc[k]["ds_cat"] for k in ks)
        drefused = sum(1 for k in ks if pc[k]["direct_cat"] == "REJECTED") / len(ks)
        nbenign = sum(1 for k in ks if pc[k]["neutral_cat"] == "BENIGN") / len(ks)
        dsmal = ds.get("MALICIOUS", 0) / len(ks)
        dsrej = ds.get("REJECTED", 0) / len(ks)
        return {"ds_dist": dict(ds), "direct_refused_rate": round(drefused, 3),
                "neutral_benign_rate": round(nbenign, 3),
                "ds_malicious_rate": round(dsmal, 3), "ds_rejected_rate": round(dsrej, 3)}

    r_th, r_no = rates(th, keys), rates(no, keys)
    print(f"[thinking] NON-THINKING: {r_no}")
    print(f"[thinking] THINKING    : {r_th}")

    # paired transitions of the DS outcome (nothink -> think)
    trans = Counter(f"{no[k]['ds_cat']}->{th[k]['ds_cat']}" for k in keys)
    # paired CIs on the key rate differences (think - nothink), per-condition indicators
    def paired_ci(fn):
        x = [float(fn(th[k])) for k in keys]; y = [float(fn(no[k])) for k in keys]
        r = stats.paired_bootstrap_ci(x, y, n_boot=10000, seed=0)
        return {"mean": round(r["mean_diff"], 3), "lo": round(r["lo"], 3),
                "hi": round(r["hi"], 3), "ci_reliable": r["ci_reliable"]}
    d_mal = paired_ci(lambda r: r["ds_cat"] == "MALICIOUS")
    d_rej = paired_ci(lambda r: r["ds_cat"] == "REJECTED")
    d_dref = paired_ci(lambda r: r["direct_cat"] == "REJECTED")

    print(f"[thinking] Δ(think−nothink) DS malicious = {d_mal['mean']} [{d_mal['lo']},{d_mal['hi']}]")
    print(f"[thinking] Δ DS rejected            = {d_rej['mean']} [{d_rej['lo']},{d_rej['hi']}]")
    print(f"[thinking] Δ Direct refused         = {d_dref['mean']} [{d_dref['lo']},{d_dref['hi']}]")
    print(f"[thinking] DS transitions (nothink->think): {dict(trans)}")

    out = {"n_matched": len(keys), "nonthinking": r_no, "thinking": r_th,
           "delta_ds_malicious": d_mal, "delta_ds_rejected": d_rej, "delta_direct_refused": d_dref,
           "ds_transitions": dict(trans)}
    path = args.out or os.path.join(args.think_dir, "thinking_comparison.json")
    json.dump(out, open(path, "w"), indent=2)
    print(f"[thinking] -> {path}")


if __name__ == "__main__":
    main()
