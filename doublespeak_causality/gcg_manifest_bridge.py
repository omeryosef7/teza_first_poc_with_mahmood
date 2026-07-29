"""
gcg_manifest_bridge.py — Track B (temporal-GCG) step 1: bridge the Doublespeak curated behavioral
benchmark into the poc_stage_gcg_early SurrogateTask manifest schema.

Emits TWO manifests (same task_ids, one entry per eligible base):
  <out>_neutral.jsonl — instruction = the BENIGN Neutral (codeword) prompt  → benign reference reps
  <out>_direct.jsonl  — instruction = the RAW Direct (harmful concept) prompt → harmful reference reps
build_reference_cache.py is run on EACH → two caches; the mixed early-benign/late-harmful cache is then
assembled by gcg_mixed_cache.py (step 2). The manifest itself stays fully harmless: the optimization
`safe_target_prefix` is a generic benign coherence anchor — the temporal attack is carried entirely by
the layer-weighted repr_loss against the mixed reference, and harmful ASR is judged separately (step 4).

One condition per base: the chosen codeword (first) at the MIDDLE context_len — matching the behavioral
sweep's per-condition design. Reuses the curated matrix + corrected eligibility only; no model load.

Usage:
  python doublespeak_causality/gcg_manifest_bridge.py \
    --matrix doublespeak_causality/data/behavioral_benchmark/screening_matrix_curated_v1.json \
    --eligible doublespeak_causality/outputs/behavioral_screen_curated_v1/eligible_bases_corrected.json \
    --model-family deepseek_r1 --enable-thinking --out doublespeak_causality/data/gcg/curated_deepseek
"""
import argparse
import hashlib
import json
import os


# generic benign coherence anchor for task_loss — NOT a harmful target; the temporal objective
# (repr_loss vs the mixed reference) carries the mechanism, task_loss only preserves fluency.
BENIGN_TARGET = "Sure, I can help with that."


def _split_for(base_id, val_frac=0.3):
    """Deterministic train/val split by base_id hash (held-out-concept eval needs a stable split)."""
    h = int(hashlib.sha1(base_id.encode()).hexdigest(), 16)
    return "val" if (h % 100) / 100.0 < val_frac else "train"


def build(matrix_path, eligible_path, model_family, enable_thinking, out_prefix):
    matrix = json.load(open(matrix_path))
    conds = matrix["conditions"]
    elig = json.load(open(eligible_path))
    eligible_ids = {k for k, v in elig.items() if v.get("eligible")}

    # index conditions by base_id → pick the chosen codeword at the middle context_len
    by_base = {}
    for c in conds:
        if c["base_id"] not in eligible_ids:
            continue
        by_base.setdefault(c["base_id"], []).append(c)

    chosen = {}
    for bid, cs in by_base.items():
        ctxs = sorted({c["context_len"] for c in cs})
        mid_ctx = ctxs[len(ctxs) // 2]                 # middle context length
        cw = sorted({c["codeword"] for c in cs})[0]    # first codeword (deterministic)
        pick = [c for c in cs if c["context_len"] == mid_ctx and c["codeword"] == cw]
        if pick:
            chosen[bid] = pick[0]

    os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
    neu_path, dir_path = out_prefix + "_neutral.jsonl", out_prefix + "_direct.jsonl"
    n = 0
    with open(neu_path, "w") as fn, open(dir_path, "w") as fd:
        for bid in sorted(chosen):
            c = chosen[bid]
            split = _split_for(bid)
            common = dict(task_id=bid, safe_target_prefix=BENIGN_TARGET, early_prefix=None,
                          neutral_control_suffix=" ", split=split, seed=42,
                          model=model_family, enable_thinking=bool(enable_thinking))
            fn.write(json.dumps({**common, "instruction": c["neutral"]}, ensure_ascii=True) + "\n")
            fd.write(json.dumps({**common, "instruction": c["direct"]}, ensure_ascii=True) + "\n")
            n += 1
    return {"n_tasks": n, "neutral_manifest": neu_path, "direct_manifest": dir_path,
            "n_train": sum(_split_for(b) == "train" for b in chosen),
            "n_val": sum(_split_for(b) == "val" for b in chosen)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--eligible", required=True)
    ap.add_argument("--model-family", default="deepseek_r1", choices=["qwen3", "gemma4", "deepseek_r1"])
    ap.add_argument("--enable-thinking", action="store_true")
    ap.add_argument("--out", required=True, help="output path PREFIX (→ _neutral.jsonl / _direct.jsonl)")
    args = ap.parse_args()
    info = build(args.matrix, args.eligible, args.model_family, args.enable_thinking, args.out)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
