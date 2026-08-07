#!/usr/bin/env python3
"""§3 (Master Plan V2) — Refusal-suppression causal localization at the DECISION TOKEN.

Where can the Doublespeak-suppressed refusal state be OVERWRITTEN to restore refusal? For each
(layer L, component C in {resid_pre, attn_out, mlp_out, resid_post}), replace the DS prompt's
DECISION-TOKEN (last-position) activation with the matched DIRECT-harmful donor's decision-token
activation, then read the refusal-direction projection at the validated readout rows. Restoration =
proj(patched) - proj(ds_base); frac = restoration / (direct - ds_base).

The decision token is position -1 in BOTH prompts (both end with the same query + generation prompt),
so the Direct donor is a clean matched counterfactual (§0.4). This localizes the §4C behavioral READOUT
/ carry of the suppression and directly sets up §22 (timing) and §23 (counterfactual decision-state
patch). Demo-ORIGIN positions have no matched activation donor and are handled by §5 (demo content),
NOT here — see PREREG_REFUSAL_SUPPRESSION_LOCALIZATION.md addendum.

Endpoint: representational (refusal projection). Behavioral confirmation of any passing (L,C) cell is a
separate arm (generation under the same decision-token patch). Readout direction: validated per-layer
refusal directions (P7 set {L13-20,24,28,29}); anchor L18. NEVER L9.

Controls (§0.4): self-swap (donor = DS's own decision-token value -> must reproduce ds_base exactly,
max|dev| gate) and the firing/movability control (a late-layer resid_post patch from Direct must move
the readout far toward direct). Specificity (norm-matched random donor) is added in analysis.

Usage:
  python scripts/phase_refusal_suppression_localize.py --bench <beh_clearharm.json> \
     --refusal-dir outputs/refusal_alllayers --readout-anchor 18 --donors direct,self --n 0
Smoke: --n 2  (self-swap max|dev| must be ~0; firing control must move the anchor readout).
"""
from __future__ import annotations
import argparse, json, os, sys, time
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc

COMPONENTS = ["resid_pre", "attn_out", "mlp_out", "resid_post"]
VALIDATED_READOUT_LAYERS = [13, 14, 15, 16, 17, 18, 19, 20, 24, 28, 29]  # P7 both-family validated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--refusal-dir", default=os.path.join(DC, "outputs", "refusal_alllayers"))
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--readout-anchor", type=int, default=18, help="validated readout layer to headline (hs row = L+1)")
    ap.add_argument("--components", default=",".join(COMPONENTS))
    ap.add_argument("--donors", default="direct,self", help="subset of {direct,neutral,self}")
    ap.add_argument("--layers", default="", help="comma list or A-B range; empty = all")
    ap.add_argument("--splits", default="train,test")
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    lm = dc.load_model(args.model); dev = lm.model.device; L = lm.num_layers; H = lm.hidden_size
    comps = [c.strip() for c in args.components.split(",") if c.strip()]
    donors = [d.strip() for d in args.donors.split(",") if d.strip()]
    if args.layers.strip():
        if "-" in args.layers and "," not in args.layers:
            a, b = args.layers.split("-"); layers = list(range(int(a), int(b) + 1))
        else:
            layers = [int(x) for x in args.layers.split(",") if x.strip() != ""]
    else:
        layers = list(range(L))

    # validated per-layer refusal directions; hs row h corresponds to post-block layer h-1
    refdir = {}
    for k in range(L):
        p = os.path.join(args.refusal_dir, f"refusal_direction_llama_L{k}.pt")
        if os.path.exists(p):
            v = torch.load(p, map_location="cpu").float().flatten(); refdir[k + 1] = v / (v.norm() + 1e-8)
    read_rows = sorted(h for h in refdir if (h - 1) in VALIDATED_READOUT_LAYERS)
    anchor_row = args.readout_anchor + 1
    assert anchor_row in read_rows, f"anchor L{args.readout_anchor} (row {anchor_row}) not in validated readout rows {read_rows}"

    data = json.load(open(args.bench)); items = data["items"] if isinstance(data, dict) else data
    cohort = (data.get("_meta", {}) if isinstance(data, dict) else {}).get("cohort", os.path.basename(args.bench))
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(DC, "outputs", f"refsuploc_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    try:
        dc.write_runmeta(out_dir, args=vars(args), extra={"phase": "refusal_suppression_localize_v1",
                         "components": comps, "donors": donors, "readout_anchor": args.readout_anchor,
                         "validated_readout_rows": read_rows, "model": args.model})
    except Exception:
        pass
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[refsuploc] cohort={cohort} comps={comps} donors={donors} layers={layers[0]}..{layers[-1]} "
          f"anchor=L{args.readout_anchor} read_rows={read_rows} -> {out_dir}", flush=True)

    @torch.no_grad()
    def proj_last(templated, patch=None):
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        if patch is None:
            out = lm.model(**tok, output_hidden_states=True, return_dict=True)
        else:
            with patch:
                out = lm.model(**tok, output_hidden_states=True, return_dict=True)
        hs = out.hidden_states
        return {h: float(torch.dot(hs[h][0, -1, :].float().cpu(), refdir[h])) for h in read_rows}

    @torch.no_grad()
    def capture_dec(templated):
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        plen = tok["input_ids"].shape[1]; dec = plen - 1
        with pc.ComponentCapture(lm, comps, [dec]) as cap:
            lm.model(**tok)
        return cap.stacked(), plen  # {comp: [n_layers, 1, H]}

    for split in splits:
        cand = [it for it in items if it.get("split") == split]
        if args.n: cand = cand[: args.n]
        for it in cand:
            hw, cw = it["harmful_word"], it["codeword"]
            instr = it["harmful_instruction"]
            if hw not in instr: instr = f"Give detailed step-by-step instructions to make a {hw}."
            demos = it["demos"] if isinstance(it["demos"], str) else "\n".join(it["demos"])
            conds = dc.build_conditions(instr, hw, cw, demos)
            direct_t = dc.apply_template(lm.tokenizer, conds.direct, add_generation_prompt=True)
            ds_t = dc.apply_template(lm.tokenizer, conds.doublespeak, add_generation_prompt=True)
            neutral_t = dc.apply_template(lm.tokenizer, conds.neutral, add_generation_prompt=True)

            base = {"direct": proj_last(direct_t), "ds_base": proj_last(ds_t), "neutral": proj_last(neutral_t)}
            donor_cap = {}
            if "direct" in donors: donor_cap["direct"], _ = capture_dec(direct_t)
            if "neutral" in donors: donor_cap["neutral"], _ = capture_dec(neutral_t)
            ds_cap, ds_plen = capture_dec(ds_t)
            if "self" in donors: donor_cap["self"] = ds_cap
            dec_ds = ds_plen - 1

            rec = {"id": it.get("id"), "split": split, "cohort": cohort, "base": base, "patched": {}}
            for C in comps:
                for donor in donors:
                    cap = donor_cap[donor]  # {comp: [n_layers,1,H]}
                    for Lp in layers:
                        vec = cap[C][Lp, 0, :].to(dev)
                        patch = pc.SubmodulePatch(lm.model, Lp, C, [dec_ds], vector=vec, mode="replace")
                        pr = proj_last(ds_t, patch)
                        rec["patched"][f"{C}|{donor}|L{Lp}"] = {str(h): round(pr[h], 5) for h in read_rows}
            fh.write(json.dumps(rec) + "\n"); fh.flush()
    fh.close()

    # ---- analysis: restoration at the anchor readout row, per (component, layer, donor) ----
    allr = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    rng = np.random.default_rng(0)
    def ci(v):
        a = np.array([x for x in v if x is not None], float)
        if len(a) == 0: return [None, None, None]
        bs = [rng.choice(a, len(a), replace=True).mean() for _ in range(2000)]
        return [round(float(a.mean()), 4), round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]
    ar = str(anchor_row)
    summ = {}
    selfswap_max = 0.0
    for split in splits:
        sr = [r for r in allr if r["split"] == split]
        if not sr: continue
        gap = [r["base"]["direct"][ar] - r["base"]["ds_base"][ar] for r in sr]
        cell = {}
        for C in comps:
            for donor in donors:
                for Lp in layers:
                    key = f"{C}|{donor}|L{Lp}"
                    rest = [r["patched"][key][ar] - r["base"]["ds_base"][ar] for r in sr]
                    frac = [(r["patched"][key][ar] - r["base"]["ds_base"][ar]) /
                            (r["base"]["direct"][ar] - r["base"]["ds_base"][ar])
                            for r in sr if abs(r["base"]["direct"][ar] - r["base"]["ds_base"][ar]) > 1e-6]
                    cell[key] = {"restore_ci": ci(rest), "frac_mean": round(float(np.mean(frac)), 4) if frac else None}
                    if donor == "self":
                        selfswap_max = max(selfswap_max, max(abs(x) for x in rest) if rest else 0.0)
        summ[split] = {"n": len(sr), "anchor_row": anchor_row, "direct_minus_ds_gap_mean": round(float(np.mean(gap)), 4),
                       "cells": cell}
    out = {"cohort": cohort, "components": comps, "donors": donors, "layers": layers,
           "readout_anchor": args.readout_anchor, "validated_readout_rows": read_rows,
           "selfswap_max_abs_restore": round(selfswap_max, 6), "by_split": summ}
    json.dump(out, open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    try:
        dc.write_done(out_dir, rows_written=len(allr))
    except Exception:
        pass

    print(f"[refsuploc] {len(allr)} rows -> {out_dir}", flush=True)
    print(f"  SELF-SWAP max|restore| = {selfswap_max:.2e} (locality gate, want ~0)", flush=True)
    for sp, s in summ.items():
        gap = s["direct_minus_ds_gap_mean"]
        print(f"  [{sp}] n={s['n']} (direct-ds) refusal gap at L{args.readout_anchor} = {gap:+.3f}", flush=True)
        # firing control + top restoring cells (direct donor)
        direct_cells = {k: v for k, v in s["cells"].items() if "|direct|" in k and v["frac_mean"] is not None}
        top = sorted(direct_cells.items(), key=lambda kv: -kv[1]["frac_mean"])[:6]
        for k, v in top:
            print(f"     {k:>22}  restore={v['restore_ci']}  frac_of_gap={v['frac_mean']}", flush=True)


if __name__ == "__main__":
    main()
