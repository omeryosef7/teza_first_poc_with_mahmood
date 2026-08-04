#!/usr/bin/env python3
"""Representational grounding of the BEHAV-REFUSAL result: does Doublespeak actually SUPPRESS the
refusal-axis signal in the hidden state (vs a direct harmful request)? The behavioral experiments
showed refusal ablation reproduces/undoes Doublespeak; if that is the mechanism, then at the decision
position DS's residual should sit LOWER on the refusal axis than direct-harmful — closer to a benign
request. Forward-only (no generation, no judge), so it runs on all examples cheaply.

Readout: project the last-PROMPT-token residual (the position that decides the first generated token)
onto the validated per-layer refusal direction, for three matched conditions per item:
  direct   — plain harmful request (refusal expected → HIGH projection)
  doublespeak — the jailbreak
  neutral  — codeword-substituted, NO demos (benign-ish → LOW projection)
Per-layer refusal dirs: outputs/refusal_alllayers/refusal_direction_llama_L{k}.pt lives in
hidden_states[k+1] (post-block-k). Control: a norm-matched random direction (no condition gap expected).
Paired stat: direct − doublespeak per item, bootstrap CI per layer. Reuses build_conditions +
forward_hidden_states.

Usage: python scripts/phase_refusal_projection.py --bench data/behavioral/beh_clearharm.json \
  --refusal-dir outputs/refusal_alllayers --n 0
"""
from __future__ import annotations
import argparse, json, os, sys, time, glob
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--refusal-dir", default=os.path.join(DC, "outputs", "refusal_alllayers"))
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--splits", default="train,test")
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed); rng = np.random.default_rng(args.seed)
    lm = dc.load_model(args.model); dev = lm.model.device; L = lm.num_layers
    # per-layer refusal dir k -> unit vector, indexed by the hidden_states row it lives in (k+1)
    refdir = {}
    for k in range(L):
        p = os.path.join(args.refusal_dir, f"refusal_direction_llama_L{k}.pt")
        if os.path.exists(p):
            v = torch.load(p, map_location="cpu").float().flatten()
            refdir[k + 1] = v / (v.norm() + 1e-8)
    rows_hs = sorted(refdir)                                  # hidden_states indices with a dir
    rand = {h: pc.norm_matched_random(refdir[h], 1, args.seed + h)[0] for h in rows_hs}  # per-layer seed (audit: independent draws)
    rand = {h: rand[h] / (rand[h].norm() + 1e-8) for h in rows_hs}
    print(f"[refproj] {len(rows_hs)} per-layer refusal dirs (hs rows {rows_hs[0]}..{rows_hs[-1]})", flush=True)

    data = json.load(open(args.bench)); items = data["items"] if isinstance(data, dict) else data
    cohort = (data.get("_meta", {}) if isinstance(data, dict) else {}).get("cohort", os.path.basename(args.bench))
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(DC, "outputs", f"refproj_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True); fh = open(os.path.join(out_dir, "raw.jsonl"), "w")

    @torch.no_grad()
    def proj_last(text):
        fwd = dc.forward_hidden_states(lm, text)
        hs = fwd["hidden_states"]                              # tuple[L+1] [1,seq,H]
        out_ref, out_rnd = {}, {}
        for h in rows_hs:
            vec = hs[h][0, -1, :].float().cpu()
            out_ref[h] = float(torch.dot(vec, refdir[h]))
            out_rnd[h] = float(torch.dot(vec, rand[h]))
        return out_ref, out_rnd

    for split in splits:
        cand = [it for it in items if it.get("split") == split]
        if args.n: cand = cand[: args.n]
        for it in cand:
            hw, cw = it["harmful_word"], it["codeword"]
            instr = it["harmful_instruction"]
            if hw not in instr: instr = f"Give detailed step-by-step instructions to make a {hw}."
            demos = it["demos"] if isinstance(it["demos"], str) else "\n".join(it["demos"])
            conds = dc.build_conditions(instr, hw, cw, demos)
            rec = {"id": it.get("id"), "split": split, "cohort": cohort}
            for name, raw in [("direct", conds.direct), ("neutral", conds.neutral), ("doublespeak", conds.doublespeak)]:
                t = dc.apply_template(lm.tokenizer, raw, add_generation_prompt=True)
                pr, rn = proj_last(t)
                rec[name] = pr; rec[f"{name}_rand"] = rn
            fh.write(json.dumps(rec) + "\n"); fh.flush()
    fh.close()

    allr = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    rng2 = np.random.default_rng(0)
    def ci(v):
        a = np.array(v, float)
        if len(a) == 0: return [None, None, None]
        b = [rng2.choice(a, len(a), replace=True).mean() for _ in range(2000)]
        return [round(float(a.mean()), 4), round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]
    summ = {}
    for split in splits:
        sr = [r for r in allr if r["split"] == split]
        if not sr: continue
        perlayer = {}
        for h in rows_hs:
            hk = str(h)
            md = {c: round(float(np.mean([r[c][hk] for r in sr])), 4) for c in ("direct", "neutral", "doublespeak")}
            # paired direct - doublespeak (refusal suppression by DS) and its random-dir control
            d_ds = ci([r["direct"][hk] - r["doublespeak"][hk] for r in sr])
            d_ds_rand = ci([r["direct_rand"][hk] - r["doublespeak_rand"][hk] for r in sr])
            perlayer[h] = {"mean": md, "direct_minus_ds": d_ds, "direct_minus_ds_RANDCTRL": d_ds_rand}
        # locate the layer of max suppression (direct-ds) for a headline
        best = max(rows_hs, key=lambda h: perlayer[h]["direct_minus_ds"][0])
        summ[split] = {"n": len(sr), "max_suppression_hs_row": best,
                       "max_suppression": perlayer[best]["direct_minus_ds"],
                       "per_layer": {str(h): perlayer[h] for h in rows_hs}}
    json.dump({"cohort": cohort, "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[refproj] {len(allr)} rows -> {out_dir}", flush=True)
    for sp, s in summ.items():
        b = s["max_suppression_hs_row"]
        print(f"  [{sp}] n={s['n']} max refusal-suppression (direct-ds) at hs[{b}] (~L{b-1}) = {s['max_suppression']}", flush=True)
        for h in [rows_hs[len(rows_hs)//4], rows_hs[len(rows_hs)//2], b, rows_hs[-2]]:
            m = s["per_layer"][str(h)]
            print(f"     hs[{h}] mean direct={m['mean']['direct']} ds={m['mean']['doublespeak']} neutral={m['mean']['neutral']} | d-ds={m['direct_minus_ds']} rand={m['direct_minus_ds_RANDCTRL']}", flush=True)


if __name__ == "__main__":
    main()
