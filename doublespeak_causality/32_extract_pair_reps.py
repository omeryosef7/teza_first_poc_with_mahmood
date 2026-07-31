"""
32_extract_pair_reps.py — CAUSAL_CORE_PLAN §16.5 (S3).

Extract the fixed-pair representations across ALL layers x token positions x components,
for every condition and both splits. This is the substrate for the causal directions
(§16.6) and every intervention sweep (§4).

Three artefacts, sized so the exhaustive map fits on disk:

  means.npz            per-(condition, split, component, position) MEAN over prompts,
                       [n_layers, hidden] float32 — this is what the mean-difference
                       directions d_Direct / d_DS are built from. Tiny.
  per_prompt.npz       per-prompt resid_post at the codeword position,
                       [n_rows, n_layers, hidden] float16 — needed for PCA subspaces,
                       cross-fitting and paired statistics. ~0.8 GB for 800 rows.
  subsample.npz        per-prompt vectors for ALL components x positions on a
                       deterministic subsample, [n_sub, n_comp, n_pos, n_layers, hidden]
                       float16 — lets the component/position comparison carry error bars
                       without storing the full cube.

Layer indexing: arrays are indexed by 0-indexed BLOCK L (n_layers rows), matching
LayerPatch(layer_idx=L). ds_common's hidden_states[L+1] is the same object.

Usage:
  python 32_extract_pair_reps.py --bench data/pair_benchmark/pair_carrot_bomb.json
"""
import os
import sys
import json
import time
import argparse

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
import pair_common as pc

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--components", default=",".join(pc.COMPONENTS))
    ap.add_argument("--positions", default=",".join(pc.POSITIONS))
    ap.add_argument("--readout", default="one_word",
                    help="restrict to ONE readout template so the prompt suffix is "
                         "constant and conditions stay matched (default: one_word)")
    ap.add_argument("--subsample", type=int, default=64,
                    help="rows kept in the full component x position cube")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--enable-thinking", default="default",
                    choices=["default", "true", "false"],
                    help="Qwen3-style thinking toggle; 'default' => model default (Llama path "
                         "unchanged, kwarg not passed)")
    args = ap.parse_args()

    dc.set_seed(args.seed)
    think = dc.parse_enable_thinking(args.enable_thinking)
    comps = [c.strip() for c in args.components.split(",") if c.strip()]
    poss = [p.strip() for p in args.positions.split(",") if p.strip()]

    bench = json.load(open(args.bench))
    rows = [r for r in bench["semantic"] if r["readout"] == args.readout]
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit(f"no rows for readout={args.readout!r}")

    lm = dc.load_model(args.model)
    L, H = lm.num_layers, lm.hidden_size
    tag = args.model.split("/")[-1]
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root,
                           f"pair_reps_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"[reps] model={tag} L={L} H={H} rows={len(rows)} comps={comps} pos={poss}")
    print(f"[reps] -> {out_dir}")

    # deterministic subsample (stratified by condition so every condition is represented)
    by_cond = {}
    for i, r in enumerate(rows):
        by_cond.setdefault(r["condition"], []).append(i)
    per_cond = max(1, args.subsample // max(1, len(by_cond)))
    sub_idx = sorted(i for c in sorted(by_cond) for i in by_cond[c][:per_cond])
    sub_set = set(sub_idx)

    sums, counts = {}, {}
    per_prompt = np.zeros((len(rows), L, H), dtype=np.float16)
    sub_cube = np.full((len(sub_idx), len(comps), len(poss), L, H), np.nan,
                       dtype=np.float16)
    sub_pos = {i: k for k, i in enumerate(sub_idx)}
    meta_rows, n_missing = [], 0

    for i, r in enumerate(rows):
        templated = dc.apply_template(lm.tokenizer, r["prompt"], enable_thinking=think)
        cap = pc.capture_components(lm, templated, r["probe_word"], comps, poss)
        got = cap["position_names"]
        reps = cap["reps"]                       # {comp: [L, n_got, H]}

        for ci, c in enumerate(comps):
            for pi, p in enumerate(poss):
                if p not in got:
                    n_missing += 1
                    continue
                v = reps[c][:, got.index(p), :]  # [L, H] float32 CPU
                key = f"{r['condition']}|{r['split']}|{c}|{p}"
                if key not in sums:
                    sums[key] = torch.zeros(L, H, dtype=torch.float64)
                    counts[key] = 0
                sums[key] += v.double()
                counts[key] += 1
                if c == "resid_post" and p == "codeword_last":
                    per_prompt[i] = v.to(torch.float16).numpy()
                if i in sub_set:
                    sub_cube[sub_pos[i], ci, pi] = v.to(torch.float16).numpy()

        meta_rows.append({"row": i, "sid": r["sid"], "condition": r["condition"],
                          "split": r["split"], "demo_style": r["demo_style"],
                          "n_demos": r["n_demos"], "readout": r["readout"],
                          "probe_word": r["probe_word"],
                          "positions": cap["positions"], "position_names": got})
        if (i + 1) % 50 == 0:
            print(f"  [reps] {i + 1}/{len(rows)}")

    np.savez_compressed(
        os.path.join(out_dir, "means.npz"),
        **{k: (sums[k] / counts[k]).float().numpy() for k in sums},
        **{f"__count__{k}": np.array(counts[k]) for k in counts})
    np.savez(os.path.join(out_dir, "per_prompt.npz"), resid_post_codeword=per_prompt)
    np.savez(os.path.join(out_dir, "subsample.npz"), cube=sub_cube,
             rows=np.array(sub_idx))

    summary = {
        "model": lm.meta(), "pair": bench["pair"], "bench": os.path.abspath(args.bench),
        "bench_meta": bench["_meta"], "plan": "CAUSAL_CORE_PLAN §16.5 (S3)",
        "n_layers": L, "hidden": H, "components": comps, "positions": poss,
        "readout": args.readout, "n_rows": len(rows),
        "n_missing_position_cells": n_missing,
        "subsample_rows": sub_idx,
        "cell_counts": {k: int(v) for k, v in counts.items()},
        "rows": meta_rows, "status": "COMPLETE",
    }
    with open(os.path.join(out_dir, "reps_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(f"[reps] cells={len(counts)} missing_position_cells={n_missing} -> {out_dir}")


if __name__ == "__main__":
    main()
