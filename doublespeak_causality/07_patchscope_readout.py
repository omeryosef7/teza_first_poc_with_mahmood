"""
07_patchscope_readout.py — P3 refinement (plan §9, RQ2): necessity + sufficiency
measured with the PATCHSCOPES readout (concept meaning), not in-context logit lens
(next-token). Fixes the readout limitation found in 05 (sufficiency null was an
artifact of measuring next-token prediction).

Method: patch at layer L (source forward), then read the codeword representation at
a fixed LATE readout layer R and decode it with Patchscopes — inject that rep into
an identity inspection prompt ("cat->cat; 1124->1124; hello->hello; ?") at layer R
and read P(harmful) vs P(codeword) for the next token. This asks "what concept is
this representation", the paper's question.

  * Necessity(L): DS forward with DS<-Neutral patch at L; read patchscope P(harm) at R.
    If patching at L reduces the downstream harm meaning, layer L is necessary.
  * Sufficiency(L): Neutral forward with Neutral<-Direct patch at L; read patchscope
    P(harm) at R. If it induces harm meaning, layer L injection is sufficient.
Controls: identity (DS<-DS), random norm-matched. Baselines: unpatched DS / Neutral.

Deterministic, numbers only (plan §5.12). Sweeps patch layers L in [0, R].

Run: python 07_patchscope_readout.py --model meta-llama/Llama-3.1-8B-Instruct \
     --data data/seed_concepts_gpt4omini.json --templated
"""
import os
import sys
import json
import time
import argparse

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc

# Repetition-style inspection prompt: patch the rep at the final token and read
# whether the model repeats the concept. The vendored "cat->cat; ...; ?" arrow
# prompt FAILS its positive control on Llama-3.1-8B (a clean "virus" rep decodes to
# P~0.001); this repeat prompt passes it (clean/Direct "virus" -> P~0.67-0.72),
# verified in logs/diag_readout_eng.log & diag_readout2.log.
INSPECTION_PROMPT = "hello hello\nworld world\ncat cat\nX"


def token_id(tokenizer, word):
    ids = tokenizer.encode(f" {word}", add_special_tokens=False) or \
          tokenizer.encode(word, add_special_tokens=False)
    return ids[-1]


class PatchscopeDecoder:
    """Decode an arbitrary hidden vector: inject it at (inspect_layer, '?') into the
    inspection prompt and read the next-token probability of target words. Reuses the
    LayerPatch hook; the inspection prompt is tokenized once."""

    def __init__(self, lm, inspection_prompt=INSPECTION_PROMPT):
        self.lm = lm
        tok = lm.tokenizer(inspection_prompt, return_tensors="pt").to(lm.model.device)
        self.inputs = tok
        # Patch at the FINAL token of the repetition prompt (the slot the model
        # should fill by "repeating" the injected concept).
        self.q_pos = tok["input_ids"].shape[1] - 1

    @torch.no_grad()
    def decode(self, vector, inspect_layer, harm_id, code_id):
        with dc.LayerPatch(self.lm.model, inspect_layer, [self.q_pos], vector=vector,
                           mode="replace"):
            out = self.lm.model(**self.inputs)
        probs = torch.softmax(out.logits[0, self.q_pos, :].float(), dim=-1)
        return float(probs[harm_id]), float(probs[code_id])


@torch.no_grad()
def patched_codeword_rep(lm, text, patch_layer, patch_pos, vector, readout_layer,
                         mode="replace"):
    """Run `text` with an optional patch at patch_layer/patch_pos, return the codeword
    representation at readout_layer (index readout_layer+1 in hidden_states)."""
    tok = lm.tokenizer(text, return_tensors="pt").to(lm.model.device)
    if vector is None:
        out = lm.model(**tok, output_hidden_states=True)
    else:
        with dc.LayerPatch(lm.model, patch_layer, [patch_pos], vector=vector, mode=mode):
            out = lm.model(**tok, output_hidden_states=True)
    return out.hidden_states[readout_layer + 1][0, patch_pos, :]


def run_item(lm, dec, it, templated, readout_layer, seed):
    demos = "\n".join(it["demos"]) if isinstance(it["demos"], list) else it["demos"]
    cond = dc.build_conditions(it["harmful_instruction"], it["harmful_word"],
                               it["codeword"], demos)
    render = lambda n: (dc.apply_template(lm.tokenizer, getattr(cond, n))
                        if templated else getattr(cond, n))
    ds_text, neu_text, dir_text = render("doublespeak"), render("neutral"), render("direct")
    harm_id = token_id(lm.tokenizer, it["harmful_word"])
    code_id = token_id(lm.tokenizer, it["codeword"])

    ds_cap = dc.capture_target_reps(lm, ds_text, it["codeword"])
    neu_cap = dc.capture_target_reps(lm, neu_text, it["codeword"])
    dir_cap = dc.capture_target_reps(lm, dir_text, it["harmful_word"])
    ds_pos = ds_cap["positions"]["codeword_last"]
    neu_pos = neu_cap["positions"]["codeword_last"]
    R = readout_layer

    # baselines: patchscope P(harm) of the unpatched DS / Neutral codeword rep at R
    ds_repR = ds_cap["reps"]["codeword_last"][R + 1].to(lm.model.device)
    neu_repR = neu_cap["reps"]["codeword_last"][R + 1].to(lm.model.device)
    base_ds_ph, base_ds_pc = dec.decode(ds_repR, R, harm_id, code_id)
    base_neu_ph, base_neu_pc = dec.decode(neu_repR, R, harm_id, code_id)
    # F4 (iter11): record the Patchscopes POSITIVE CONTROL in-run — a clean Direct harm-word
    # rep at the readout layer must decode to high P(harm). If it doesn't, the readout (not the
    # mechanism) is the cause and this item's necessity/sufficiency numbers are floor-bound.
    dir_repR = dir_cap["reps"]["codeword_last"][R + 1].to(lm.model.device)
    base_dir_ph, base_dir_pc = dec.decode(dir_repR, R, harm_id, code_id)
    # Direct decodes EARLY, so reading its rep at the late layer R is ~0 by design — the WRONG
    # positive control. Correct control: does a clean Direct concept rep, taken from ANY layer and
    # read at R, decode to high P(harm)? Scan layers, take max (this is the readout-soundness test).
    reps_all = dir_cap["reps"]["codeword_last"]
    pos_ctrl_max = max(dec.decode(reps_all[l].to(lm.model.device), R, harm_id, code_id)[0]
                       for l in range(len(reps_all)))

    gen = torch.Generator().manual_seed(seed)
    randvec = torch.randn(lm.hidden_size, generator=gen)

    res = {"id": it["id"], "readout_layer": R,
           "baseline_ds_patchscope": {"p_harm": base_ds_ph, "p_code": base_ds_pc},
           "baseline_neutral_patchscope": {"p_harm": base_neu_ph, "p_code": base_neu_pc},
           "baseline_direct_patchscope": {"p_harm": base_dir_ph, "p_code": base_dir_pc},
           "positive_control_max": pos_ctrl_max,
           "positive_control_ok": bool(pos_ctrl_max > 0.1 and base_neu_ph < pos_ctrl_max),
           "necessity": [], "sufficiency": [], "sufficiency_ds": [],
           # F1 (iter11): norm-matched sufficiency controls to rule out a MAGNITUDE confound in
           # the DS>Direct claim — inject Direct rescaled to ‖ds_vec‖, and a ds-norm RANDOM vector
           # into the Neutral forward. DS>Direct is a direction/meaning effect only if it survives.
           "sufficiency_direct_dsnorm": [], "control_random_neutral": [],
           "control_identity": [], "control_random": []}

    # C1 FIX (NEXT_CAUSAL_SPRINT S0): patch layer L must be STRICTLY below the readout
    # layer R. LayerPatch at L edits the post-block-L residual == hidden_states[L+1];
    # the readout reads hidden_states[R+1]. At L==R the patch overwrites the readout
    # vector itself (zero propagation), which floored necessity/sufficiency at the
    # observational DS-Neutral gap and inflated false positives. Enforce L <= R-1.
    for L in dc.patch_layer_sweep(R):            # L in [0, R-1]: at least one block of propagation
        neu_vec = neu_cap["reps"]["codeword_last"][L + 1].to(lm.model.device)
        ds_vec = ds_cap["reps"]["codeword_last"][L + 1].to(lm.model.device)
        dir_vec = dir_cap["reps"]["codeword_last"][L + 1].to(lm.model.device)
        rscale = float(ds_vec.float().norm()) / float(randvec.norm())
        rand_vec = (randvec * rscale).to(lm.model.device)

        # Necessity: DS forward, DS<-Neutral at L, read patchscope at R
        rep = patched_codeword_rep(lm, ds_text, L, ds_pos, neu_vec, R)
        ph, pc = dec.decode(rep, R, harm_id, code_id)
        res["necessity"].append({"layer": L, "p_harm": ph, "p_code": pc})

        # Sufficiency: Neutral forward, Neutral<-Direct at L (harmful concept's own,
        # early-structured rep; expected NOT sufficient).
        rep = patched_codeword_rep(lm, neu_text, L, neu_pos, dir_vec, R)
        ph, pc = dec.decode(rep, R, harm_id, code_id)
        res["sufficiency"].append({"layer": L, "p_harm": ph, "p_code": pc})

        # Sufficiency via the HIJACKED DS rep (late-structured; expected sufficient at mid).
        rep = patched_codeword_rep(lm, neu_text, L, neu_pos, ds_vec, R)
        ph, pc = dec.decode(rep, R, harm_id, code_id)
        res["sufficiency_ds"].append({"layer": L, "p_harm": ph, "p_code": pc})

        # F1 norm-matched control: Direct rescaled to ‖ds_vec‖ injected into Neutral. If
        # sufficiency_ds still > this, DS>Direct is NOT a pure magnitude effect. Record both norms.
        dsn = float(ds_vec.float().norm()); dirn = float(dir_vec.float().norm())
        dir_dsnorm = (dir_vec * (dsn / (dirn + 1e-8))).to(lm.model.device)
        rep = patched_codeword_rep(lm, neu_text, L, neu_pos, dir_dsnorm, R)
        ph, pc = dec.decode(rep, R, harm_id, code_id)
        res["sufficiency_direct_dsnorm"].append({"layer": L, "p_harm": ph, "p_code": pc,
                                                 "ds_norm": dsn, "dir_norm": dirn})

        # F1 norm-matched RANDOM control on the Neutral forward (rand_vec is already ds-norm):
        # a ds-norm random direction into Neutral should NOT create harm meaning.
        rep = patched_codeword_rep(lm, neu_text, L, neu_pos, rand_vec, R)
        ph, pc = dec.decode(rep, R, harm_id, code_id)
        res["control_random_neutral"].append({"layer": L, "p_harm": ph, "p_code": pc})

        # identity control (DS<-DS) and random control (DS<-random)
        rep = patched_codeword_rep(lm, ds_text, L, ds_pos, ds_vec, R)
        ph, pc = dec.decode(rep, R, harm_id, code_id)
        res["control_identity"].append({"layer": L, "p_harm": ph, "p_code": pc})

        rep = patched_codeword_rep(lm, ds_text, L, ds_pos, rand_vec, R)
        ph, pc = dec.decode(rep, R, harm_id, code_id)
        res["control_random"].append({"layer": L, "p_harm": ph, "p_code": pc})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(__file__), "data",
                                                   "seed_concepts_gpt4omini.json"))
    ap.add_argument("--templated", action="store_true")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--readout-layer", type=int, default=None,
                    help="default = num_layers-4 (late)")
    ap.add_argument("--only", default=None, help="comma list of item ids to run")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "outputs", f"stage2b_patchscope_{args.model.split('/')[-1]}_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype))
    dec = PatchscopeDecoder(lm)
    R = args.readout_layer if args.readout_layer is not None else lm.num_layers - 4
    data = json.load(open(args.data))
    items = data["items"]
    if args.only:
        keep = set(args.only.split(","))
        items = [it for it in items if it["id"] in keep]

    report = {"model": args.model, "meta": lm.meta(), "templated": args.templated,
              "readout_layer": R, "items": []}
    for it in items:
        r = run_item(lm, dec, it, args.templated, R, args.seed)
        report["items"].append(r)
        nec = r["necessity"]; suf = r["sufficiency"]; sufds = r["sufficiency_ds"]
        bph = r["baseline_ds_patchscope"]["p_harm"]
        max_nec_drop = max(bph - x["p_harm"] for x in nec)
        max_suf = max(x["p_harm"] for x in suf)
        max_sufds = max(x["p_harm"] for x in sufds)
        print(f"[{r['id']}] R={R} baseDS={bph:.3f} baseNeu={r['baseline_neutral_patchscope']['p_harm']:.3f} "
              f"| necessity drop={max_nec_drop:.3f} | suff(Direct)={max_suf:.3f} | suff(DS)={max_sufds:.3f}")

    report["status"] = "COMPLETE"
    with open(os.path.join(out_dir, "stage2b_results.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[stage2b-patchscope] -> {out_dir}")


if __name__ == "__main__":
    main()
