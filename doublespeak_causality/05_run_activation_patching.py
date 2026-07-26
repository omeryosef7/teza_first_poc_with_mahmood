"""
05_run_activation_patching.py — Stage 2 (plan §9): the first CAUSAL experiment.

Necessity (§9.1): take the Doublespeak forward and, at layer L / codeword position,
REPLACE the Doublespeak activation with the matched Neutral activation. If the
harmful semantic interpretation is *necessary*, this should reduce it.

Sufficiency (§9.2): take the Neutral forward and patch IN the Direct (or Doublespeak)
activation at layer L / codeword position. If sufficient, harmful interpretation
should appear.

Semantic readout (self-contained, composes with the intervention hook): during the
patched forward we capture hidden states and apply the model's own final-norm+lm_head
(logit lens, via vendored LogitLens.project_to_vocab) at the codeword and following
positions, reading P(harmful_token) vs P(codeword_token). We sweep ALL layers.

Controls (§9.3): identity patch (DS<-DS must reproduce baseline == α=0 sanity),
norm-matched RANDOM-vector patch, and cross patches. Behavioral generation is done
only at the single most-effective layer (plan §5.5 start-small; keeps the sweep cheap).

Deterministic. Numbers only to stdout (plan §5.12). Writes JSON + registry-friendly summary.

Run (after Stage-1 sane), on L40S:
  python 05_run_activation_patching.py --model meta-llama/Llama-3.1-8B-Instruct \
      --data data/seed_concepts.json --templated
"""
import os
import sys
import json
import time
import argparse

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
from mech_interp import LogitLens  # vendored (reuse final-norm + lm_head)


def token_id(tokenizer, word):
    ids = tokenizer.encode(f" {word}", add_special_tokens=False) or \
          tokenizer.encode(word, add_special_tokens=False)
    return ids[-1]


@torch.no_grad()
def logit_lens_probs(lens, hidden_last_layer, positions, harm_id, code_id):
    """Given the final-layer hidden [1,seq,H], return P(harm)/P(code) at positions."""
    out = {}
    for name, p in positions.items():
        if p is None:
            continue
        h = hidden_last_layer[0, p, :].unsqueeze(0)
        logits = lens.project_to_vocab(h)            # [1, vocab]
        probs = torch.softmax(logits.float(), dim=-1)[0]
        out[name] = {"p_harm": float(probs[harm_id]), "p_code": float(probs[code_id])}
    return out


@torch.no_grad()
def forward_with_patch(lm, text, layer, pos, vector, mode="replace", alpha=1.0):
    """One forward, optionally patched at (layer, pos); returns final-layer hidden."""
    tok = lm.tokenizer(text, return_tensors="pt").to(lm.model.device)
    if vector is None and mode != "none":
        mode = "none"
    if mode == "none":
        out = lm.model(**tok, output_hidden_states=True)
    else:
        with dc.LayerPatch(lm.model, layer, [pos], vector=vector, mode=mode, alpha=alpha):
            out = lm.model(**tok, output_hidden_states=True)
    return out.hidden_states[-1], tok["input_ids"][0].tolist()


def run_item(lm, lens, it, templated, seed):
    demos = "\n".join(it["demos"]) if isinstance(it["demos"], list) else it["demos"]
    cond = dc.build_conditions(it["harmful_instruction"], it["harmful_word"],
                               it["codeword"], demos)
    harm_id = token_id(lm.tokenizer, it["harmful_word"])
    code_id = token_id(lm.tokenizer, it["codeword"])

    def render(name):
        raw = getattr(cond, name)
        return dc.apply_template(lm.tokenizer, raw) if templated else raw

    ds_text, neu_text, dir_text = render("doublespeak"), render("neutral"), render("direct")

    # Source activations (per-layer, codeword position) from clean forwards.
    ds_cap = dc.capture_target_reps(lm, ds_text, it["codeword"])
    neu_cap = dc.capture_target_reps(lm, neu_text, it["codeword"])
    dir_cap = dc.capture_target_reps(lm, dir_text, it["harmful_word"])
    ds_pos = ds_cap["positions"]["codeword_last"]
    neu_pos = neu_cap["positions"]["codeword_last"]

    # Baselines (no patch).
    ds_hidden, ds_ids = forward_with_patch(lm, ds_text, 0, ds_pos, None, mode="none")
    neu_hidden, neu_ids = forward_with_patch(lm, neu_text, 0, neu_pos, None, mode="none")
    ds_positions = {"codeword_last": ds_pos,
                    "following": ds_cap["positions"]["following"]}
    neu_positions = {"codeword_last": neu_pos,
                     "following": neu_cap["positions"]["following"]}
    base_ds = logit_lens_probs(lens, ds_hidden, ds_positions, harm_id, code_id)
    base_neu = logit_lens_probs(lens, neu_hidden, neu_positions, harm_id, code_id)

    n_layers = lm.num_layers
    gen = torch.Generator().manual_seed(seed)
    randvec = torch.randn(lm.hidden_size, generator=gen)

    results = {"id": it["id"], "harm_id": harm_id, "code_id": code_id,
               "baseline_ds": base_ds, "baseline_neutral": base_neu,
               "necessity": [], "sufficiency": [], "control_identity": [],
               "control_random": []}

    for L in range(n_layers):
        # source rows: hidden_states index = layer+1 (0 = embedding)
        neu_vec = neu_cap["reps"]["codeword_last"][L + 1].to(lm.model.device)
        ds_vec = ds_cap["reps"]["codeword_last"][L + 1].to(lm.model.device)
        dir_vec = dir_cap["reps"]["codeword_last"][L + 1].to(lm.model.device)
        rand_scaled = (randvec / randvec.norm() * ds_vec.float().norm()).to(lm.model.device)

        # Necessity: DS forward, replace DS-codeword activation with Neutral's.
        h, _ = forward_with_patch(lm, ds_text, L, ds_pos, neu_vec, mode="replace")
        results["necessity"].append({"layer": L,
            **{f"cw_{k}": v for k, v in logit_lens_probs(lens, h, {"cw": ds_pos}, harm_id, code_id)["cw"].items()}})

        # Sufficiency: Neutral forward, patch IN the Direct activation.
        h, _ = forward_with_patch(lm, neu_text, L, neu_pos, dir_vec, mode="replace")
        results["sufficiency"].append({"layer": L,
            **{f"cw_{k}": v for k, v in logit_lens_probs(lens, h, {"cw": neu_pos}, harm_id, code_id)["cw"].items()}})

        # Control identity: DS<-DS must reproduce baseline (α=0-equivalent sanity).
        h, _ = forward_with_patch(lm, ds_text, L, ds_pos, ds_vec, mode="replace")
        results["control_identity"].append({"layer": L,
            **{f"cw_{k}": v for k, v in logit_lens_probs(lens, h, {"cw": ds_pos}, harm_id, code_id)["cw"].items()}})

        # Control random: Neutral<-norm-matched random (should NOT create harm meaning).
        h, _ = forward_with_patch(lm, neu_text, L, neu_pos, rand_scaled, mode="replace")
        results["control_random"].append({"layer": L,
            **{f"cw_{k}": v for k, v in logit_lens_probs(lens, h, {"cw": neu_pos}, harm_id, code_id)["cw"].items()}})

    # Sanity: identity control must match baseline DS codeword prob within tol.
    id_ok = all(abs(r["cw_p_harm"] - base_ds["codeword_last"]["p_harm"]) < 1e-3
                for r in results["control_identity"])
    results["identity_reproduces_baseline"] = bool(id_ok)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(__file__),
                                                   "data", "seed_concepts.json"))
    ap.add_argument("--templated", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "outputs",
        f"stage2_patching_{args.model.split('/')[-1]}_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    lm = dc.load_model(args.model)
    lens = LogitLens(lm.model, lm.tokenizer)
    data = json.load(open(args.data))
    report = {"model": args.model, "meta": lm.meta(), "templated": args.templated,
              "items": []}
    for it in data["items"]:
        r = run_item(lm, lens, it, args.templated, args.seed)
        report["items"].append(r)
        # console: numbers only
        nec = r["necessity"]; suf = r["sufficiency"]
        base = r["baseline_ds"]["codeword_last"]["p_harm"]
        # layer of max necessity effect = biggest drop in P(harm) vs baseline
        drop = [(base - x["cw_p_harm"], x["layer"]) for x in nec]
        best = max(drop)
        rise = [(x["cw_p_harm"], x["layer"]) for x in suf]
        bests = max(rise)
        print(f"[{r['id']}] identity_ok={r['identity_reproduces_baseline']} "
              f"baseDS_pharm={base:.3f} | necessity best drop {best[0]:+.3f}@L{best[1]} "
              f"| sufficiency best pharm {bests[0]:.3f}@L{bests[1]}")

    report["status"] = "COMPLETE"
    with open(os.path.join(out_dir, "stage2_results.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[stage2] -> {out_dir}")


if __name__ == "__main__":
    main()
