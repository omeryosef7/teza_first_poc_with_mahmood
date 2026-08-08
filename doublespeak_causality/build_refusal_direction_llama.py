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
import importlib.util
from contextlib import ExitStack

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
def last_token_hs(lm, prompt, layers, enable_thinking=None):
    """{L: hidden_states[L+1][0,-1,:] (float CPU)} for the templated prompt's last token.

    enable_thinking (Phase 7 / thinking sprint): None -> model default (Llama path byte-identical);
    False -> pass explicitly so a thinking model (Qwen3) renders an empty <think></think> instead of
    a live <think> control token before the readout, keeping the last-token residual consistent."""
    fwd = dc.forward_hidden_states(
        lm, dc.apply_template(lm.tokenizer, prompt, enable_thinking=enable_thinking))
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


# --------------------------------------------------------------------------- #
# Generation-based validation (the NON-tautological sign check)
# --------------------------------------------------------------------------- #
def _load_v18():
    """Import 18_run_behavioral_necessity.py by path (numeric filename -> importlib idiom,
    identical to 45_toctou_factorial.py / 19). Reuses its validated judge primitives."""
    spec = importlib.util.spec_from_file_location(
        "v18", os.path.join(HERE, "18_run_behavioral_necessity.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def behavioral_field(bench_paths, field, n):
    """First-n unique behavioral `field` prompts, pooled across benches (by key; never printed)."""
    prompts, seen = [], set()
    for p in bench_paths:
        bench = json.load(open(p))
        for row in bench["behavioral"]:
            v = row[field]
            if v not in seen:
                seen.add(v)
                prompts.append(v)
    return prompts[:n] if n else prompts


@torch.no_grad()
def _gen_completion(lm, templated_text, ctx_managers, max_new_tokens):
    """Greedy generation on already-templated text under a stack of context managers
    (AllPositionProjectOut / LayerPatch). add_special_tokens=False mirrors patched_generate
    (single BOS). Returns the decoded completion STRING (never persisted)."""
    tok = lm.tokenizer(templated_text, return_tensors="pt",
                       add_special_tokens=False).to(lm.model.device)
    in_len = tok["input_ids"].shape[1]
    with ExitStack() as stack:
        for cm in ctx_managers:
            stack.enter_context(cm)
        out = lm.model.generate(**tok, max_new_tokens=max_new_tokens, do_sample=False,
                                eos_token_id=lm.eos_token_ids,
                                pad_token_id=lm.tokenizer.pad_token_id)
    return lm.tokenizer.decode(out[0][in_len:], skip_special_tokens=True)


def validate_layer(lm, pc, kw_refusal, L, v, harmful_prompts, neutral_prompts,
                   induce_alpha, max_new_tokens, enable_thinking=None):
    """Sign-correctness of v_refusal[L] by GENERATION (scalars only; no completions kept).

      ABLATE arm (harmful `direct`): project v out at EVERY position/timestep on EVERY
        layer (pair_common.AllPositionProjectOutMultiLayer, the standard Arditi et al.
        directional ablation) -> should LOWER refusal / raise compliance. This measures
        the SAME multi-layer ablation the TOCTOU factorial applies, not a single-layer
        projection at L. INDUCE below stays single-layer (add at the source layer L),
        since induction only needs the axis written where it was fit.
        ablate_gain = refusal_rate_baseline_harmful - refusal_rate_ablated   (want > 0)
      INDUCE arm (benign `neutral`): ADD +alpha*v at all prompt positions of layer L
        (ds_common.LayerPatch mode="add") -> should RAISE refusal.
        induce_gain = refusal_rate_added - refusal_rate_baseline_neutral      (want > 0)
      score = ablate_gain + induce_gain.
    """
    vv = v.float().to(lm.model.device)
    all_layers = list(range(lm.num_layers))

    b_h = a_h = 0
    for p in harmful_prompts:
        t = dc.apply_template(lm.tokenizer, p, enable_thinking=enable_thinking)
        base = _gen_completion(lm, t, [], max_new_tokens)
        abl = _gen_completion(
            lm, t, [pc.AllPositionProjectOutMultiLayer(lm.model, all_layers, vv, 1.0)],
            max_new_tokens)
        b_h += int(kw_refusal(base))
        a_h += int(kw_refusal(abl))
    n_h = max(len(harmful_prompts), 1)
    rr_base_harmful = b_h / n_h
    rr_ablated = a_h / n_h
    ablate_gain = rr_base_harmful - rr_ablated

    add_vec = induce_alpha * vv
    b_n = i_n = 0
    for p in neutral_prompts:
        t = dc.apply_template(lm.tokenizer, p, enable_thinking=enable_thinking)
        in_len = lm.tokenizer(t, add_special_tokens=False,
                              return_tensors="pt")["input_ids"].shape[1]
        base = _gen_completion(lm, t, [], max_new_tokens)
        add = _gen_completion(
            lm, t, [dc.LayerPatch(lm.model, L, list(range(in_len)),
                                  vector=add_vec, mode="add")], max_new_tokens)
        b_n += int(kw_refusal(base))
        i_n += int(kw_refusal(add))
    n_n = max(len(neutral_prompts), 1)
    rr_base_neutral = b_n / n_n
    rr_added = i_n / n_n
    induce_gain = rr_added - rr_base_neutral

    return {
        "layer": L,
        "ablation_scope": "all_layers", "induce_scope": "single_layer",
        "n_harmful": len(harmful_prompts), "n_neutral": len(neutral_prompts),
        "induce_alpha": induce_alpha, "max_new_tokens": max_new_tokens,
        "refusal_rate_baseline_harmful": round(rr_base_harmful, 4),
        "refusal_rate_ablated": round(rr_ablated, 4),
        "ablate_gain": round(ablate_gain, 4),
        "refusal_rate_baseline_neutral": round(rr_base_neutral, 4),
        "refusal_rate_added": round(rr_added, 4),
        "induce_gain": round(induce_gain, 4),
        "score": round(ablate_gain + induce_gain, 4),
        "both_gains_positive": bool(ablate_gain > 0 and induce_gain > 0),
    }


def run_validation(args, lm, layers, vecs, metas):
    """Validate every built layer by generation, stamp meta['validation'], and write
    the top-level SELECTED.json naming the best sign-correct layer (max score, both gains>0)."""
    pc = __import__("pair_common")
    kw_refusal = _load_v18().kw_refusal
    harmful = behavioral_field(args.bench, "direct", args.val_n_items)
    neutral = behavioral_field(args.bench, "neutral", args.val_n_items)
    print(f"[validate] harmful={len(harmful)} neutral={len(neutral)} "
          f"alpha={args.induce_alpha} max_new_tokens={args.val_max_new_tokens}", flush=True)

    enable_thinking = dc.parse_enable_thinking(getattr(args, "enable_thinking", None))
    for L in layers:
        val = validate_layer(lm, pc, kw_refusal, L, vecs[L], harmful, neutral,
                             args.induce_alpha, args.val_max_new_tokens,
                             enable_thinking=enable_thinking)
        metas[L][0]["validation"] = val
        print(f"[validate] L{L}: ablate_gain={val['ablate_gain']:+.3f} "
              f"induce_gain={val['induce_gain']:+.3f} score={val['score']:+.3f} "
              f"valid={val['both_gains_positive']}", flush=True)

    selected, best_score = None, None
    for L in layers:
        val = metas[L][0]["validation"]
        if val["both_gains_positive"] and (best_score is None or val["score"] > best_score):
            best_score, selected = val["score"], L

    sel = {
        "criterion": "max(ablate_gain + induce_gain) subject to both gains > 0",
        "model": args.model, "layers_tested": layers,
        "any_valid": selected is not None,
        "selected_layer": selected,
        "selected_pt": os.path.abspath(metas[selected][1]) if selected is not None else None,
        "selected_json": os.path.abspath(metas[selected][1].replace(".pt", ".json"))
        if selected is not None else None,
        "score": best_score,
        "per_layer": {str(L): metas[L][0]["validation"] for L in layers},
        "env": dc.env_metadata(),
    }
    sel_path = os.path.join(args.out, "refusal_direction_llama_SELECTED.json")
    json.dump(sel, open(sel_path, "w"), indent=2)
    if selected is None:
        print("[validate] NO layer passed (both gains > 0). SELECTED.selected_layer=null.",
              flush=True)
    else:
        print(f"[validate] SELECTED layer L{selected} (score={best_score:+.3f}) "
              f"-> {metas[selected][1]}", flush=True)
    print(f"[validate] wrote {sel_path}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", nargs="+", required=True,
                    help="pair benchmark json(s); behavioral 'direct' fields are pooled")
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--layers", default="12,14,16,18,20")
    ap.add_argument("--out", default=os.path.join(HERE, "outputs", "stage_gcg_full"))
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--validate", action="store_true",
                    help="after building, validate each layer by GENERATION (non-tautological "
                         "sign check) and write refusal_direction_llama_SELECTED.json")
    ap.add_argument("--val-n-items", type=int, default=15,
                    help="#behavioral direct/neutral prompts per validation arm")
    ap.add_argument("--val-max-new-tokens", type=int, default=64,
                    help="generation length during validation (small = fast)")
    ap.add_argument("--induce-alpha", type=float, default=8.0,
                    help="dose for the +alpha*v_refusal induce arm (v is unit-norm)")
    ap.add_argument("--enable-thinking", default=None,
                    help="default/true/false (dc.parse_enable_thinking). Llama: leave 'default' "
                         "(byte-identical). Qwen3: pass 'false' so the fit/validation last-token "
                         "readout is not preceded by a live <think> control token.")
    args = ap.parse_args()

    dc.set_seed(args.seed)
    enable_thinking = dc.parse_enable_thinking(args.enable_thinking)
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
        for L, h in last_token_hs(lm, p, layers, enable_thinking=enable_thinking).items():
            harmful_hs[L].append(h)
        if (i + 1) % 25 == 0:
            print(f"  harmful {i+1}/{len(harmful)}", flush=True)
    for i, p in enumerate(HARMLESS_INSTRUCTIONS):
        for L, h in last_token_hs(lm, p, layers, enable_thinking=enable_thinking).items():
            harmless_hs[L].append(h)

    vecs, metas = {}, {}                       # {L: v}, {L: (meta, pt_path)}
    for L in layers:
        mh = torch.stack(harmful_hs[L]).mean(0)
        ml = torch.stack(harmless_hs[L]).mean(0)
        v = mh - ml
        v = v / (v.norm() + 1e-8)                              # unit refusal axis
        # separation = mean cosine(h, v) gap between the two classes (TAUTOLOGICAL: >=0 by
        # construction — kept for continuity, but validation is the real sign check).
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
            "separation": sep, "enable_thinking": enable_thinking, "env": dc.env_metadata(),
        }
        vecs[L], metas[L] = v, (meta, pt_path)
        print(f"[refusal] L{L}: separation={sep:+.4f} -> {pt_path}", flush=True)

    # Generation-based validation (adds meta['validation'] + writes SELECTED.json) BEFORE the
    # json dump, so each layer's .json carries its validation result.
    if args.validate:
        run_validation(args, lm, layers, vecs, metas)

    for L in layers:
        meta, pt_path = metas[L]
        json.dump(meta, open(pt_path.replace(".pt", ".json"), "w"), indent=2)

    if args.validate:
        print("[refusal] done. Use refusal_direction_llama_SELECTED.json (selected_pt) "
              "for --refusal-pt.", flush=True)
    else:
        print("[refusal] done. Re-run with --validate to sign-check + select a layer.",
              flush=True)


if __name__ == "__main__":
    main()
