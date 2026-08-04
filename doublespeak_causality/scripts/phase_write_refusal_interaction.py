#!/usr/bin/env python3
"""Are the demos' TWO effects — concept-remap and refusal-suppression — causally INDEPENDENT, or does
the L8-11 concept WRITE cause the refusal suppression? Both onset in the same L8-11 band (projection),
so this is the key coupling question. Forward-only test: ablate the concept write (zero L8-11 mlp_out at
the DEMO codeword positions, exactly as BEHAV-WRITE), then measure the REFUSAL-axis projection at the
decision token. If DS's refusal suppression PERSISTS under write-ablation (refusal proj stays low, ≈ ds_base
≪ direct) → the two are INDEPENDENT (demos suppress refusal via a path other than the concept write, which
explains why concept-write ablation left ASR unchanged while refusal is the behavioral locus). If it REVERSES
(refusal proj rises toward direct) → the write CAUSES the suppression.

Conditions per item: direct (harmful, high refusal ref) · ds_base · ds_writeabl (DS + L8-11 demo-write
zeroed). Readout: last-prompt-token residual · per-layer refusal dir (as phase_refusal_projection).
Positive control: p_concept FC readout under write-ablation must DROP (confirms the write ablation fired).
Reuses pc.ComponentOutSwap (prefill write-zero) + dc.forward_hidden_states + per-layer refusal dirs.

Usage: python scripts/phase_write_refusal_interaction.py --bench data/behavioral/beh_clearharm.json \
  --refusal-dir outputs/refusal_alllayers --write-layers 8-11 --n 0
"""
from __future__ import annotations
import argparse, json, os, sys, time
from contextlib import ExitStack
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc

FC_PREFIX = "Choose one label only and answer with just that label."
def fc_question(cw, co):
    return f'{FC_PREFIX} In the text above, does the word "{cw}" refer to "{co}" or to "{cw}"?'
def _sid(tok, w): return tok.encode(" " + w, add_special_tokens=False)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--refusal-dir", default=os.path.join(DC, "outputs", "refusal_alllayers"))
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--write-layers", default="8-11")
    ap.add_argument("--splits", default="train,test")
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    lm = dc.load_model(args.model); dev = lm.model.device; L = lm.num_layers; H = lm.hidden_size
    a, b = args.write_layers.split("-"); wlayers = list(range(int(a), int(b) + 1))
    refdir = {}
    for k in range(L):
        p = os.path.join(args.refusal_dir, f"refusal_direction_llama_L{k}.pt")
        if os.path.exists(p):
            v = torch.load(p, map_location="cpu").float().flatten(); refdir[k + 1] = v / (v.norm() + 1e-8)
    rows_hs = sorted(refdir)
    data = json.load(open(args.bench)); items = data["items"] if isinstance(data, dict) else data
    cohort = (data.get("_meta", {}) if isinstance(data, dict) else {}).get("cohort", os.path.basename(args.bench))
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(DC, "outputs", f"write_refusal_intx_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True); fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[intx] cohort={cohort} write_layers={wlayers} refusal_rows={rows_hs[0]}..{rows_hs[-1]} -> {out_dir}", flush=True)

    @torch.no_grad()
    def proj_last(templated, ctx=()):
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        with ExitStack() as st:
            for c in ctx: st.enter_context(c)
            out = lm.model(**tok, output_hidden_states=True, return_dict=True)
        hs = out.hidden_states
        return {h: float(torch.dot(hs[h][0, -1, :].float().cpu(), refdir[h])) for h in rows_hs}

    @torch.no_grad()
    def fc_pconcept(demo_block, cw, co, ctx=()):
        # positive control: does write-ablation drop the concept readout?
        t = dc.apply_template(lm.tokenizer, demo_block + "\n\n" + fc_question(cw, co))
        tok = lm.tokenizer(t, return_tensors="pt", add_special_tokens=False).to(dev)
        cid, kid = _sid(lm.tokenizer, co), _sid(lm.tokenizer, cw)
        if cid == kid: return None
        with ExitStack() as st:
            for c in ctx: st.enter_context(c)
            out = lm.model(**tok, return_dict=True)
        p = torch.softmax(out.logits[0, -1, :].float(), -1)
        pc_, pk_ = float(p[cid]), float(p[kid]); return pc_ / (pc_ + pk_ + 1e-12)

    for split in splits:
        cand = [it for it in items if it.get("split") == split]
        if args.n: cand = cand[: args.n]
        for it in cand:
            hw, cw = it["harmful_word"], it["codeword"]
            instr = it["harmful_instruction"]
            if hw not in instr: instr = f"Give detailed step-by-step instructions to make a {hw}."
            demos = it["demos"] if isinstance(it["demos"], str) else "\n".join(it["demos"])
            conds = dc.build_conditions(instr, hw, cw, demos)
            co = it.get("target_concept", hw)                    # concept name for FC control (fallback hw)
            direct_t = dc.apply_template(lm.tokenizer, conds.direct, add_generation_prompt=True)
            ds_t = dc.apply_template(lm.tokenizer, conds.doublespeak, add_generation_prompt=True)
            # DEMO codeword positions in the DS prompt (exclude the final/query occurrence) — BEHAV-WRITE recipe
            hit = dc.find_word_occurrences_in_text(lm.tokenizer, ds_t, cw)
            plen = len(lm.tokenizer(ds_t, add_special_tokens=False)["input_ids"])
            all_cw = sorted({li for li in hit.last_idx if 0 <= li < plen})
            if len(all_cw) < 2: continue
            cw_pos = all_cw[:-1]
            src = {l: torch.zeros(len(cw_pos), H, device=dev, dtype=torch.float32) for l in wlayers}
            wctx = [pc.ComponentOutSwap(lm.model, cw_pos, src, "mlp_out")]
            rec = {"id": it.get("id"), "split": split, "cohort": cohort, "n_cw_pos": len(cw_pos),
                   "direct": proj_last(direct_t), "ds_base": proj_last(ds_t),
                   "ds_writeabl": proj_last(ds_t, wctx)}
            # positive control: FC p_concept DS vs DS+writeabl (demo block only, codeword substituted)
            demo_block = conds.doublespeak.rsplit("\n\nDo not reason, just", 1)[0]
            assert demo_block != conds.doublespeak, "rsplit sentinel not found — non-default instruction_prefix?"
            pc_base = fc_pconcept(demo_block, cw, co); pc_wabl = fc_pconcept(demo_block, cw, co, wctx)
            rec["pconcept_ds"] = pc_base; rec["pconcept_writeabl"] = pc_wabl
            fh.write(json.dumps(rec) + "\n"); fh.flush()
    fh.close()

    allr = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    rng = np.random.default_rng(0)
    def ci(v):
        a = np.array([x for x in v if x is not None], float)
        if len(a) == 0: return [None, None, None]
        bs = [rng.choice(a, len(a), replace=True).mean() for _ in range(2000)]
        return [round(float(a.mean()), 4), round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]
    summ = {}
    for split in splits:
        sr = [r for r in allr if r["split"] == split]
        if not sr: continue
        perlayer = {}
        for h in rows_hs:
            hk = str(h)
            md = {c: round(float(np.mean([r[c][hk] for r in sr])), 4) for c in ("direct", "ds_base", "ds_writeabl")}
            # does write-ablation MOVE the refusal projection? (ds_writeabl - ds_base); and how far toward direct?
            d_move = ci([r["ds_writeabl"][hk] - r["ds_base"][hk] for r in sr])
            gap = md["direct"] - md["ds_base"]
            frac_restored = round((md["ds_writeabl"] - md["ds_base"]) / gap, 3) if abs(gap) > 1e-6 else None
            perlayer[h] = {"mean": md, "writeabl_minus_dsbase": d_move, "frac_of_direct_gap_restored": frac_restored}
        pcb = [r["pconcept_ds"] for r in sr if r.get("pconcept_ds") is not None]
        pcw = [r["pconcept_writeabl"] for r in sr if r.get("pconcept_writeabl") is not None]
        summ[split] = {"n": len(sr),
                       "pconcept_control": {"ds": round(float(np.mean(pcb)), 4) if pcb else None,
                                            "writeabl": round(float(np.mean(pcw)), 4) if pcw else None,
                                            "drop_ci": ci([r["pconcept_ds"] - r["pconcept_writeabl"] for r in sr
                                                           if r.get("pconcept_ds") is not None and r.get("pconcept_writeabl") is not None])},
                       "per_layer": {str(h): perlayer[h] for h in rows_hs}}
    json.dump({"cohort": cohort, "write_layers": wlayers, "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[intx] {len(allr)} rows -> {out_dir}", flush=True)
    for sp, s in summ.items():
        pc_ = s["pconcept_control"]
        print(f"  [{sp}] n={s['n']} p_concept CONTROL: ds={pc_['ds']} writeabl={pc_['writeabl']} drop_ci={pc_['drop_ci']} (want drop>0 = ablation fired)", flush=True)
        for h in [rows_hs[len(rows_hs)//2], rows_hs[-2], rows_hs[-1]]:
            m = s["per_layer"][str(h)]
            print(f"     hs[{h}] refusal: direct={m['mean']['direct']} ds={m['mean']['ds_base']} ds_writeabl={m['mean']['ds_writeabl']} | Δ(writeabl-ds)={m['writeabl_minus_dsbase']} frac_gap_restored={m['frac_of_direct_gap_restored']}", flush=True)


if __name__ == "__main__":
    main()
