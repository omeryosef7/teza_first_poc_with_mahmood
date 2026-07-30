"""
21_extract_behavioral_features.py — Phase 5 / Workstream E (plan §9.1). Compute mechanistic
temporal features per DS prompt and pair them with the BEHAVIORAL label (DS_MALICIOUS), so we can
later test whether the "benign-early / harmful-late" signature PREDICTS behavioral jailbreak success
(Claim E / Level 4). Forward-passes only (no generation/judging) — fast + preemption-safe.

Direction: harmful direction d[l] per layer = mean over TRAIN conditions of (Direct_rep − Neutral_rep)
at the codeword/concept position (a validated contextual-harm axis; train-only to avoid leakage).
Alignment at layer l for a DS prompt = cos( DS_rep[l] − Neutral_rep[l], d[l] ) — how far the codeword
has moved toward the harmful concept, along the harmful axis.

Features (per condition): early/mid/late mean alignment, early→late change, onset layer (first layer
alignment≥thr), peak alignment, argmax layer, AUC (mean over layers), and the raw per-layer trajectory.

Responsible handling (§17): reads harmful prompt text (main loop / SLURM only); outputs scalars only.

Run (SLURM, bf16, L40S): see slurm/run_features.sh
  python 21_extract_behavioral_features.py --matrix ... --screen-dir ... --model ...
"""
import os
import sys
import json
import time
import argparse
import importlib.util

import numpy as np  # C9 FIX (NEXT_CAUSAL_SPRINT S0): persist raw movement vectors for per-fold axis in 22
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ds_common as dc
_spec = importlib.util.spec_from_file_location("v18", os.path.join(HERE, "18_run_behavioral_necessity.py"))
v18 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v18)
capture_reps_for_gen = v18.capture_reps_for_gen


def _cos(a, b):
    a = a.float(); b = b.float()
    return float(torch.dot(a, b) / (a.norm() * b.norm() + 1e-8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", default=os.path.join(HERE, "data", "behavioral_benchmark",
                                                     "screening_matrix_curated_v1.json"))
    ap.add_argument("--screen-dir", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--train-frac", type=float, default=0.5, help="fraction of items for the direction")
    ap.add_argument("--onset-thresh", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir or os.path.join(HERE, "outputs", f"features_{args.model.split('/')[-1]}_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype))
    conds = json.load(open(args.matrix))["conditions"]
    labels = {(r["base_id"], r["codeword"], r["context_len"]): r["triplet_label"]
              for r in json.load(open(os.path.join(args.screen_dir, "per_condition_corrected.json")))}

    # --- pass 1: capture DS/Neutral/Direct codeword-rep trajectories (CPU float32) ---
    recs = []
    for i, c in enumerate(conds):
        cw, concept = c["codeword"], c["concept"]
        key = (c["base_id"], c["codeword"], c["context_len"])
        lab = labels.get(key)
        if lab is None:
            continue
        ds = capture_reps_for_gen(lm, dc.apply_template(lm.tokenizer, c["doublespeak"]), cw)
        neu = capture_reps_for_gen(lm, dc.apply_template(lm.tokenizer, c["neutral"]), cw)
        dire = capture_reps_for_gen(lm, dc.apply_template(lm.tokenizer, c["direct"]), concept)
        if ds["reps"] is None or neu["reps"] is None or dire["reps"] is None:
            continue
        recs.append({"key": key, "concept": concept, "codeword": cw, "context_len": c["context_len"],
                     "label": lab, "ds_malicious": int(lab == "DS_MALICIOUS"),
                     "ds": ds["reps"], "neu": neu["reps"], "dire": dire["reps"]})
        if (i + 1) % 40 == 0:
            print(f"  captured {i+1}/{len(conds)}", flush=True)
    print(f"[features] captured {len(recs)} conditions", flush=True)

    n_layers = lm.num_layers
    # --- train split (for the harmful direction only) ---
    idx = list(range(len(recs)))
    import random
    random.Random(args.seed).shuffle(idx)
    n_train = int(len(idx) * args.train_frac)
    train_ids = set(idx[:n_train])
    # harmful direction per layer L (0-indexed block output → reps index L+1): mean(Direct−Neutral)
    dvec = []
    for L in range(n_layers):
        diffs = [recs[j]["dire"][L + 1] - recs[j]["neu"][L + 1] for j in train_ids]
        d = torch.stack(diffs, 0).mean(0)
        dvec.append(d / (d.norm() + 1e-8))

    # early/mid/late layer bands (0-indexed)
    t = n_layers // 3
    early, mid, late = range(0, t), range(t, 2 * t), range(2 * t, n_layers)

    rows = []
    # C9 FIX (NEXT_CAUSAL_SPRINT S0): collect raw per-row movement vectors (row order == "rows") so 22
    # can rebuild the harmful axis inside each concept CV fold from training concepts only (no leak).
    ds_move_all, dir_move_all = [], []
    for j, r in enumerate(recs):
        # alignment[L] = cos(DS_rep − Neutral_rep, d[L]) at layer L
        align = [_cos(r["ds"][L + 1] - r["neu"][L + 1], dvec[L]) for L in range(n_layers)]
        # C9 FIX (NEXT_CAUSAL_SPRINT S0): stash the raw DS- and Direct-movement (relative to Neutral)
        # vectors per layer; these are exactly what feeds dvec + alignment, enabling per-fold refit in 22.
        ds_move_all.append(torch.stack([r["ds"][L + 1] - r["neu"][L + 1] for L in range(n_layers)], 0).float().cpu().numpy())
        dir_move_all.append(torch.stack([r["dire"][L + 1] - r["neu"][L + 1] for L in range(n_layers)], 0).float().cpu().numpy())
        e = sum(align[L] for L in early) / len(early)
        m = sum(align[L] for L in mid) / len(mid)
        la = sum(align[L] for L in late) / len(late)
        onset = next((L for L in range(n_layers) if align[L] >= args.onset_thresh), -1)
        peak = max(align); argmax = int(max(range(n_layers), key=lambda L: align[L]))
        rows.append({"key": list(r["key"]), "concept": r["concept"], "codeword": r["codeword"],
                     "context_len": r["context_len"], "label": r["label"],
                     "ds_malicious": r["ds_malicious"], "in_train": int(j in train_ids),
                     "feat": {"early_align": e, "mid_align": m, "late_align": la,
                              "early_to_late": la - e, "onset_layer": onset,
                              "peak_align": peak, "argmax_layer": argmax,
                              "auc_align": sum(align) / n_layers},
                     "trajectory": align})

    # C9 FIX (NEXT_CAUSAL_SPRINT S0): write raw movement vectors alongside features.json so the
    # held-out-concept AUC in 22 can fit its harmful axis per fold (training concepts only).
    raw_name = "features_raw.npz"
    np.savez_compressed(os.path.join(out_dir, raw_name),
                        ds_move=np.stack(ds_move_all, 0), dir_move=np.stack(dir_move_all, 0))

    out = {"model": args.model, "meta": lm.meta(), "n": len(rows), "n_layers": n_layers,
           "bands": {"early": list(early), "mid": list(mid), "late": list(late)},
           "raw_npz": raw_name, "onset_thresh": args.onset_thresh,  # C9 FIX (NEXT_CAUSAL_SPRINT S0)
           "train_frac": args.train_frac, "n_train": n_train,
           "n_ds_malicious": sum(r["ds_malicious"] for r in rows),
           "rows": rows, "generated_at": time.strftime("%FT%T")}
    with open(os.path.join(out_dir, "features.json"), "w") as f:
        json.dump(out, f, indent=2)
    # quick console: mean features by outcome (benign scalars only)
    import statistics as st
    pos = [r for r in rows if r["ds_malicious"]]; neg = [r for r in rows if not r["ds_malicious"]]
    for name in ("early_align", "late_align", "early_to_late", "onset_layer"):
        mp = st.mean(r["feat"][name] for r in pos) if pos else float("nan")
        mn = st.mean(r["feat"][name] for r in neg) if neg else float("nan")
        print(f"  {name:14s} DS_MALICIOUS={mp:.3f}  other={mn:.3f}")
    print(f"[features] {len(rows)} rows ({out['n_ds_malicious']} DS_MALICIOUS) -> {out_dir}")


if __name__ == "__main__":
    main()
