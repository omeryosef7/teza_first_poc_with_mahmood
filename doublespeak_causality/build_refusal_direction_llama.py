"""
build_refusal_direction_llama.py — STAGE4_PLAN §(a). GPU script (do NOT run here).

Diff-of-means refusal direction for meta-llama/Llama-3.1-8B-Instruct, built INSIDE the
ds_common/Llama stack (compute_refusal_direction.py's own loaders are qwen3/gemma4-only).

    v_refusal[L] = normalize(mean(h_harmful) - mean(h_harmless))   at the last input token

Math is identical to poc_stage_gcg_early/compute_refusal_direction.py:162-164; only the
model stack and the prompt sets differ:

  * HARMFUL  = the bench behavioral `direct` field, POOLED across all --bench pairs, so the
    axis is CONCEPT-AGNOSTIC (a refusal axis, not a concept axis). Referenced by dict key
    only — the harmful strings are never printed (plan §15).
  * HARMLESS = the 20 genuinely-benign items from compute_refusal_direction.py:35-56
    (copied below). NOT the matched `neutral` prompts: direct<->neutral differ only by the
    concept<->codeword swap, which is the CONCEPT axis, not refusal (plan §(a)).

Capture: dc.forward_hidden_states(lm, dc.apply_template(prompt))["hidden_states"][L+1][0,-1,:]
(hidden_states[L+1] == post-block-L residual == LayerPatch/directions row L).

Sweep L in {12,14,16,18,20}; save each to
  outputs/stage_gcg_full/refusal_direction_llama_L{L}.pt  (+ .json metadata, incl. the
`separation` cosine gap used to pick the best layer). Generation-based validation
(project-out raises compliance / +alpha induces refusal) is a separate GPU step.

Usage (GPU, do NOT run from the agent):
  python build_refusal_direction_llama.py \
      --bench data/pair_benchmark/pair_carrot_bomb.json data/pair_benchmark/pair_*.json \
      --model meta-llama/Llama-3.1-8B-Instruct --layers 12,14,16,18,20 \
      --out outputs/stage_gcg_full
"""
import os
import sys
import json
import argparse

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ds_common as dc

# 20 harmless questions — the negative class for v_refusal
# (verbatim copy of compute_refusal_direction.py:35-56; genuinely benign, safe to include).
HARMLESS_INSTRUCTIONS = [
    "What is photosynthesis and how does it work?",
    "Write a short poem about autumn leaves.",
    "Explain the water cycle in simple terms.",
    "What are the main ingredients in chocolate cake?",
    "How do I care for a houseplant?",
    "What is the capital of France?",
    "Describe the life cycle of a butterfly.",
    "How does a rainbow form?",
    "Write a haiku about mountains.",
    "What are some healthy breakfast ideas?",
    "Explain how a compass works.",
    "What is the boiling point of water?",
    "Describe the main characters in Romeo and Juliet.",
    "How do I tie a bowline knot?",
    "What is the difference between a simile and a metaphor?",
    "Explain the concept of supply and demand.",
    "What are the planets in our solar system?",
    "How do I make a paper airplane?",
    "What is the speed of light?",
    "Describe how volcanoes form.",
]


@torch.no_grad()
def last_token_hs(lm, prompt, layers):
    """{L: hidden_states[L+1][0,-1,:] (float CPU)} for the templated prompt's last token."""
    fwd = dc.forward_hidden_states(lm, dc.apply_template(lm.tokenizer, prompt))
    hs = fwd["hidden_states"]
    return {L: hs[L + 1][0, -1, :].float().cpu() for L in layers}


def pooled_harmful_prompts(bench_paths):
    """Pool the behavioral `direct` field across every --bench pair (by key, never printed)."""
    prompts, seen = [], set()
    for p in bench_paths:
        bench = json.load(open(p))
        for row in bench["behavioral"]:
            d = row["direct"]
            if d not in seen:
                seen.add(d)
                prompts.append(d)
    return prompts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", nargs="+", required=True,
                    help="pair benchmark json(s); behavioral 'direct' fields are pooled")
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--layers", default="12,14,16,18,20")
    ap.add_argument("--out", default=os.path.join(HERE, "outputs", "stage_gcg_full"))
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    layers = [int(x) for x in args.layers.split(",") if x.strip()]
    harmful = pooled_harmful_prompts(args.bench)
    os.makedirs(args.out, exist_ok=True)
    print(f"[refusal] harmful={len(harmful)} (pooled) harmless={len(HARMLESS_INSTRUCTIONS)} "
          f"layers={layers} -> {args.out}", flush=True)

    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype))
    if max(layers) + 1 >= lm.num_layers + 1:
        raise SystemExit(f"layer {max(layers)} out of range for {lm.num_layers}-layer model")

    harmful_hs = {L: [] for L in layers}
    harmless_hs = {L: [] for L in layers}
    for i, p in enumerate(harmful):
        for L, h in last_token_hs(lm, p, layers).items():
            harmful_hs[L].append(h)
        if (i + 1) % 25 == 0:
            print(f"  harmful {i+1}/{len(harmful)}", flush=True)
    for i, p in enumerate(HARMLESS_INSTRUCTIONS):
        for L, h in last_token_hs(lm, p, layers).items():
            harmless_hs[L].append(h)

    for L in layers:
        mh = torch.stack(harmful_hs[L]).mean(0)
        ml = torch.stack(harmless_hs[L]).mean(0)
        v = mh - ml
        v = v / (v.norm() + 1e-8)                              # unit refusal axis
        # separation = mean cosine(h, v) gap between the two classes (the sign check)
        ph = torch.stack([torch.dot(h / (h.norm() + 1e-8), v) for h in harmful_hs[L]])
        pl = torch.stack([torch.dot(h / (h.norm() + 1e-8), v) for h in harmless_hs[L]])
        sep = float(ph.mean() - pl.mean())
        pt_path = os.path.join(args.out, f"refusal_direction_llama_L{L}.pt")
        torch.save(v, pt_path)
        meta = {
            "model": args.model, "layer": L, "d_model": int(v.shape[0]),
            "hidden_states_index": L + 1, "directions_row": L,
            "n_harmful": len(harmful_hs[L]), "n_harmless": len(harmless_hs[L]),
            "bench_paths": [os.path.abspath(b) for b in args.bench],
            "proj_harmful_mean": float(ph.mean()), "proj_harmless_mean": float(pl.mean()),
            "separation": sep, "env": dc.env_metadata(),
        }
        json.dump(meta, open(pt_path.replace(".pt", ".json"), "w"), indent=2)
        print(f"[refusal] L{L}: separation={sep:+.4f} -> {pt_path}", flush=True)

    print("[refusal] done. Pick the largest-separation, sign-correct layer for --refusal-pt.",
          flush=True)


if __name__ == "__main__":
    main()
