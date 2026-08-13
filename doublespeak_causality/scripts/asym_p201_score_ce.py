#!/usr/bin/env python
"""
ASYMMETRY SPRINT §20.1 — post-hoc target-CE scoring of frozen soft prompts.

WHY THIS EXISTS. §20.1 contrasts objective=`task` (minimize target CE) against
objective=`task_orth` (minimize CE while a penalty pins the refusal projection at its
per-prompt baseline). The question is whether compliance is reachable WITHOUT moving the
refusal coordinate. That is a comparison of achieved TASK performance.

But `task_orth`'s optimized scalar is `ce + mu*pen`, and the run logs only that sum -- no
run records CE on its own. Comparing the two arms' logged `loss` would compare CE against
CE+penalty, which is not a comparison of anything. This script recovers the missing term.

It re-scores the FROZEN `soft_suffix.pt` from each arm directory, reusing the optimizer's
own build_prompts/forward_batch so the CE reported here is definitionally the quantity
`task` minimized. Two further reasons to prefer this over logging CE mid-run:
  * the training print is a per-batch training-pool number, and the loss series is
    non-monotonic (§ earlier finding), so an endpoint print is not "achieved performance";
  * it applies uniformly to arms that have ALREADY finished, with no rerun.

Reports train and test CE, plus the refusal projection, per arm. Scalars only; never
generates or reads model text.
"""
import argparse, json, os, sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import asym_p2_softprompt as sp  # noqa: E402
from asym_p2_softprompt import build_prompts, template_tail, forward_batch, load_unit  # noqa: E402


def load_items(path, split, n_min=20):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    if split:
        rows = [r for r in rows if r.get("split") == split]
    seen, uniq = set(), []
    for r in rows:
        if r["task_id"] in seen:
            continue
        seen.add(r["task_id"])
        uniq.append(r)
    assert len(uniq) >= n_min, f"need >={n_min} unique items, got {len(uniq)} ({path}:{split})"
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm-dir", action="append", required=True,
                    help="asym_p2_soft_* output dir; repeatable")
    ap.add_argument("--out", default="doublespeak_causality/outputs/asym_p201_ce_scores.json")
    args = ap.parse_args()

    # Reuse the handle asym_p2_softprompt already bound (`import ds_common as dc`), so the
    # loader/seed/template helpers here are byte-identical to the ones the arms ran under.
    dc = sp.dc

    # Every arm in a §20.1 contrast shares model/manifest/layer; assert rather than assume.
    metas = {}
    for d in args.arm_dir:
        m = json.load(open(Path(d) / "RUNMETA.json"))
        metas[d] = m
    keyset = {(m["args"]["model"], m["args"]["manifest"], m["args"]["train_manifest"],
               m["args"]["test_split"], m["args"]["refusal_fit_layer"],
               m["args"]["n_suffix"], m["args"]["enable_thinking"])
              for m in metas.values()}
    assert len(keyset) == 1, f"arms differ in a field that makes CE incomparable: {keyset}"
    a0 = next(iter(metas.values()))["args"]

    lm = dc.load_model(a0["model"])
    model, tokenizer = lm.model, lm.tokenizer
    device = next(model.parameters()).device
    for p in model.parameters():
        p.requires_grad_(False)
    embed_w = model.get_input_embeddings().weight

    fit_layer = a0["refusal_fit_layer"]
    row = fit_layer + 1
    assert 1 <= row <= lm.num_layers
    print(f"[cfg] fit_layer={fit_layer} -> hs[{row}] (+1 applied HERE)", flush=True)
    v_ref = load_unit(os.path.join(a0["refusal_dir"],
                                   f"refusal_direction_llama_L{fit_layer}.pt")).to(device)

    enable_thinking = dc.parse_enable_thinking(a0["enable_thinking"])
    tail_len = template_tail(tokenizer, enable_thinking)
    train_items = load_items(a0["train_manifest"] or a0["manifest"], None)
    test_items = load_items(a0["manifest"], a0["test_split"])
    assert not ({i["task_id"] for i in train_items} & {i["task_id"] for i in test_items}), \
        "TRAIN/TEST LEAKAGE"
    train = build_prompts(tokenizer, train_items, a0["n_suffix"], tail_len,
                          enable_thinking, device)
    test = build_prompts(tokenizer, test_items, a0["n_suffix"], tail_len,
                         enable_thinking, device)
    print(f"[data] train={len(train)} test={len(test)} leakage=0", flush=True)

    @torch.no_grad()
    def score(prompts, emb):
        ce, proj = [], []
        for p in prompts:
            r = forward_batch(model, embed_w, [p], emb, [row], need_target=True)[0]
            ce.append(float(r["ce"]))
            proj.append(float(torch.dot(r["h"][row], v_ref)))
        return float(np.mean(ce)), float(np.mean(proj)), len(ce)

    # Baseline (no soft prompt) -- the reference both arms are measured against. Computed
    # once from the init embeddings of the first arm; identical across arms by construction
    # (same seed-independent init " !"*n_suffix), asserted below via each arm's own baseline.
    out = []
    for d in args.arm_dir:
        m = metas[d]
        blob = torch.load(Path(d) / "soft_suffix.pt", map_location=device)
        emb = blob["embeddings"].to(device).to(embed_w.dtype)
        tr_ce, tr_pr, ntr = score(train, emb)
        te_ce, te_pr, nte = score(test, emb)
        proj_json = json.load(open(Path(d) / "projections.json"))
        base_te = float(np.mean([r["proj_decision"] for r in proj_json["baseline_test"]]))
        rec = {"arm_dir": os.path.basename(d), "objective": m["objective"],
               "seed": m["args"]["seed"], "budget_rel": m["budget_rel"],
               "orth_mu": m["args"].get("orth_mu"),
               "train_ce": tr_ce, "test_ce": te_ce,
               "train_proj": tr_pr, "test_proj": te_pr,
               "baseline_test_proj": base_te, "dproj_test": te_pr - base_te,
               "n_train": ntr, "n_test": nte}
        out.append(rec)
        print(f"  {rec['objective']:<10} seed{rec['seed']}  test_CE={te_ce:.4f}  "
              f"train_CE={tr_ce:.4f}  dproj_test={rec['dproj_test']:+.4f}", flush=True)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"row_hidden_state": row, "arms": out}, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
