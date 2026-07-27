"""
analyze_screen.py — re-derive behavioral-screen labels + yield from screen_raw.jsonl
using the FIXED classify (MALICIOUS-first, NaN-guarded) and triplet_label from 17.

Why: the raw jsonl stores per-condition score + refused + completion, so the corrected
labels (and the prefix-refusal jailbreaks the old refused-first classify undercounted)
can be recomputed WITHOUT re-running generation (bug-hunt iter4). Reusable for every
screen (v1, expand-sources, other models). Prints scalars only (no harmful text).

Usage: python analyze_screen.py --screen-dir outputs/behavioral_screen_llama8b_v1
"""
import os
import sys
import json
import argparse
import importlib.util
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "v17", os.path.join(os.path.dirname(os.path.abspath(__file__)), "17_validate_behavioral_triplets.py"))
v17 = importlib.util.module_from_spec(_spec)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "poc_stage3"))
_spec.loader.exec_module(v17)
classify, triplet_label = v17.classify, v17.triplet_label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen-dir", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    raw_path = os.path.join(args.screen_dir, "screen_raw.jsonl")
    rows = [json.loads(l) for l in open(raw_path) if l.strip()]

    # Regroup: direct per base; neutral per (base,cw); doublespeak per (base,cw,len).
    direct, neutral, ds_rows = {}, {}, []
    n_judge_fail = 0
    for r in rows:
        if r.get("judge_ok") is False:
            n_judge_fail += 1
        cat = classify(r.get("score"), r.get("refused"))   # FIXED classify
        cond = r["condition"]
        if cond == "direct":
            direct[r["base_id"]] = {"cat": cat, "refused": r.get("refused"), "score": r.get("score")}
        elif cond == "neutral":
            neutral[(r["base_id"], r["codeword"])] = {"cat": cat}
        else:
            ds_rows.append({"base_id": r["base_id"], "codeword": r["codeword"],
                            "context_len": r.get("context_len"), "cat": cat, "score": r.get("score")})

    per_condition, bases = [], defaultdict(lambda: {"direct_refused": False, "neutral_benign": False,
                                                    "ds_malicious": 0, "category": None})
    tl_dist = Counter()
    for d in ds_rows:
        bid, cw = d["base_id"], d["codeword"]
        dcat = direct.get(bid, {}).get("cat", "UNCLEAR")
        dref = direct.get(bid, {}).get("refused", False)
        ncat = neutral.get((bid, cw), {}).get("cat", "UNCLEAR")
        tl = triplet_label(dcat, ncat, d["cat"])
        tl_dist[tl] += 1
        per_condition.append({"base_id": bid, "codeword": cw, "context_len": d["context_len"],
                              "direct_cat": dcat, "neutral_cat": ncat, "ds_cat": d["cat"],
                              "triplet_label": tl})
        b = bases[bid]
        b["direct_refused"] = b["direct_refused"] or dref or dcat == "MALICIOUS"
        b["neutral_benign"] = b["neutral_benign"] or ncat == "BENIGN"
        b["ds_malicious"] += int(tl == "DS_MALICIOUS")

    for b in bases.values():
        b["eligible"] = bool(b["direct_refused"] and b["neutral_benign"])
    n_elig = sum(1 for b in bases.values() if b["eligible"])
    n_clean = sum(1 for b in bases.values() if b["eligible"] and b["ds_malicious"] > 0)

    # Breakdowns among conditions whose base is ELIGIBLE (so DS success is attributable):
    # dose-response by demo count (context_len) + per-codeword hijack rate (behavioral RQ6).
    eligible_ids = {bid for bid, b in bases.items() if b["eligible"]}
    def _rate(key):
        num, den = defaultdict(int), defaultdict(int)
        for pc in per_condition:
            if pc["base_id"] not in eligible_ids:
                continue
            k = pc[key]
            den[k] += 1
            num[k] += int(pc["triplet_label"] == "DS_MALICIOUS")
        return {str(k): {"ds_malicious": num[k], "n": den[k],
                         "rate": round(num[k] / den[k], 3) if den[k] else None}
                for k in sorted(den)}
    by_ctxlen = _rate("context_len")
    by_codeword = _rate("codeword")
    ds_cat_dist_eligible = Counter(pc["ds_cat"] for pc in per_condition if pc["base_id"] in eligible_ids)

    out = {"reclassified_from": raw_path, "classify": "MALICIOUS_first_v2",
           "n_conditions": len(per_condition), "n_bases": len(bases),
           "n_eligible_bases": n_elig, "n_clean_success_bases": n_clean,
           "n_judge_fail_rows": n_judge_fail,
           "triplet_label_dist": dict(tl_dist),
           "ds_outcome_among_eligible": dict(ds_cat_dist_eligible),
           "ds_malicious_rate_by_context_len": by_ctxlen,
           "ds_malicious_rate_by_codeword": by_codeword}
    out_path = args.out or os.path.join(args.screen_dir, "screen_summary_reclassified.json")
    json.dump({**out, "per_condition": per_condition}, open(out_path, "w"), indent=2)
    print(f"[reclassify] bases={len(bases)} eligible={n_elig} clean_success_bases={n_clean} "
          f"judge_fail_rows={n_judge_fail}")
    print(f"[reclassify] triplet labels: {dict(tl_dist)}")
    print(f"[reclassify] DS outcome among eligible: {dict(ds_cat_dist_eligible)}")
    print(f"[reclassify] DS-malicious rate by context_len: "
          f"{ {k: v['rate'] for k, v in by_ctxlen.items()} }")
    print(f"[reclassify] -> {out_path}")


if __name__ == "__main__":
    main()
