#!/usr/bin/env python3
"""§4 — DISTINGUISH REFUSAL "CARRY" (storage/mediated) FROM "READOUT" (direct/skip-path) for the
refusal-suppression circuit. The refusal-circuit analogue of the concept-circuit direct-vs-total
mediation (phase7_direct_total.py, which found the concept effect ~75-83% mediated).

For each candidate refusal-carry head (the §7 L13-20 heads that restore decision-token refusal when
patched Direct->DS), decompose its causal effect on the decision-token refusal PROJECTION into:
  TOTAL[S]  = M(patch head S's decision-token z <- DIRECT ; everything downstream recomputes) - M(DS)
  DIRECT[S] = M(freeze ALL heads+MLPs to clean-DS, inject head S = DIRECT) - M(DS)   [skip-path only]
  direct_frac = DIRECT / TOTAL   (~1 => readout-proximal OUTPUT head whose z reaches the readout via
                                   the residual skip; <<1 => CARRY head, effect recomputed downstream)
  mediated_frac = 1 - direct_frac
Metric M = <resid@(rlayer+1, last-token), unit refusal direction> (decision-token refusal projection,
the validated readout used in §3/§7/§23). clean = DS (refusal SUPPRESSED, LOW proj); donor = DIRECT
(refusal HIGH). The decision token is the LAST prompt token, which is aligned between DS and DIRECT
(both end at the same decision point), so the cross-condition z-swap is well-posed WITHOUT needing to
align the demo tokens (which DIRECT lacks). This is the B(carry)-vs-C(readout) separation; the A
(demo-origin) sub-question needs the position-aligned demo analysis of §5 and is out of scope here.

Reuses the VALIDATED freeze primitives verbatim: pp50.capture_clean_all (z/mlp capture),
pp50.FreezeAllHeadsExcept, pp50.FreezeMLP, pc.ZHeadPatch, pc.ZHeadCapture. Sanity gates copied from
phase7_direct_total.py: direct_frac is trusted only if (a) freeze-all-clean + clean-sender reproduces
M(DS) [freeze consistency] and (b) the self-swap (patch DS's own z) is a no-op.

Usage:
  python scripts/phase4_refusal_mediation.py --bench data/behavioral_v3/beh_clearharm.json \
    --refusal-pt outputs/stage_gcg_full/refusal_direction_llama_L18.pt \
    --heads L16H4,L13H18,L16H10,L13H11,L13H9,L15H7 --splits test --n 0
"""
from __future__ import annotations
import argparse, importlib.util, json, os, sys, time, re
from contextlib import ExitStack
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc

# reuse the freeze primitives + clean-capture from 50_path_patching verbatim
_spec = importlib.util.spec_from_file_location("pp50", os.path.join(DC, "50_path_patching.py"))
pp50 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(pp50)

def _noop(*a, **k): return {}
write_runmeta = getattr(dc, "write_runmeta", None) or _noop
write_done = getattr(dc, "write_done", None) or _noop


def parse_heads(spec):
    heads = []
    for tok in spec.split(","):
        tok = tok.strip()
        if not tok: continue
        m = re.match(r"[Ll](\d+)[Hh](\d+)$", tok)
        if not m: raise SystemExit(f"bad head spec {tok!r}; want L<layer>H<head>")
        heads.append((int(m.group(1)), int(m.group(2))))
    return sorted(set(heads))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--refusal-pt", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--heads", default="L16H4,L13H18,L16H10,L13H11,L13H9,L15H7",
                    help="§7 top refusal-carry heads by restore-frac (default = §7 test top-6)")
    ap.add_argument("--splits", default="test")
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rel-tol", type=float, default=0.15,
                    help="trust gate: freeze/self-swap dev must be <= rel_tol * |gap| (gap=proj_direct-proj_DS)")
    ap.add_argument("--enable-thinking", default="default")
    args = ap.parse_args()
    et = dc.parse_enable_thinking(args.enable_thinking)
    dc.set_seed(args.seed)
    heads = parse_heads(args.heads)

    lm = dc.load_model(args.model); dev = lm.model.device; L = lm.num_layers
    nh, hd = pc._attn_head_dims(lm.model)
    v_ref = torch.load(args.refusal_pt).float().flatten()
    u = (v_ref / (v_ref.norm() + 1e-8)).cpu()
    rlayer = int(json.load(open(args.refusal_pt.replace(".pt", ".json"))).get("layer", 18))

    data = json.load(open(args.bench)); items = data["items"] if isinstance(data, dict) else data
    cohort = (data.get("_meta", {}) if isinstance(data, dict) else {}).get("cohort", os.path.basename(args.bench))
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(DC, "outputs", f"refusal_mediation_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    write_runmeta(out_dir, args, extra={"phase": "refusal_mediation", "cohort": cohort,
                                        "heads": args.heads, "rlayer": rlayer})
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[refmed] cohort={cohort} refusal_L{rlayer} heads={heads} -> {out_dir}", flush=True)

    def templ(raw):
        return dc.apply_template(lm.tokenizer, raw, add_generation_prompt=True, enable_thinking=et)

    def tok_of(text):
        return lm.tokenizer(text, return_tensors="pt", add_special_tokens=False).to(dev)

    @torch.no_grad()
    def proj(tok, ctxs=()):
        with ExitStack() as st:
            for c in ctxs: st.enter_context(c)
            out = lm.model(**tok, output_hidden_states=True, return_dict=True)
        v = out.hidden_states[rlayer + 1][0, -1, :].float().cpu()
        return float(torch.dot(v, u))

    @torch.no_grad()
    def capture_z_last(text):
        """{L: [n_heads, head_dim]} per-head z at the LAST (decision) token of `text`."""
        t = tok_of(text); last = t["input_ids"].shape[1] - 1
        with pc.ZHeadCapture(lm.model, list(range(L))) as cap:
            lm.model(**t, return_dict=True)
        return {l: cap.acts[l][0, last].detach().float().view(nh, hd).to(dev) for l in range(L)}

    dummy = lambda out: torch.tensor(0.0)   # z/mlp capture is metric-independent; m_clean computed via proj()

    for split in splits:
        cand = [it for it in items if it.get("split") == split]
        if args.n: cand = cand[: args.n]
        for it in cand:
            hw, cw = it["harmful_word"], it["codeword"]
            instr = it["harmful_instruction"]
            if hw not in instr: instr = f"Give detailed step-by-step instructions to make a {hw}."
            demos = it["demos"] if isinstance(it["demos"], str) else "\n".join(it["demos"])
            conds = dc.build_conditions(instr, hw, cw, demos)
            ds_text, direct_text = templ(conds.doublespeak), templ(conds.direct)
            ds_t = tok_of(ds_text); ds_last = ds_t["input_ids"].shape[1] - 1

            # clean = DS: freeze-state capture (reused verbatim) + refusal proj (LOW)
            z_clean, mlp_clean, _ = pp50.capture_clean_all(lm, ds_text, dummy, L)
            m_clean = proj(ds_t)                       # DS decision-token refusal proj (suppressed)
            m_direct = proj(tok_of(direct_text))       # DIRECT proj (refusal engaged) — ceiling
            donor_z = capture_z_last(direct_text)      # DIRECT per-head decision-token z
            gap = m_direct - m_clean                   # >0: how much refusal DS suppressed vs DIRECT

            for (ls, hs) in heads:
                donor = donor_z[ls][hs]                 # [head_dim] from DIRECT decision token
                self_v = z_clean[ls][ds_last, hs]       # DS own z at decision (self-swap control)
                m_tot = proj(ds_t, [pc.ZHeadPatch(lm.model, ls, hs, [ds_last], donor)])
                m_dir = proj(ds_t, [pp50.FreezeAllHeadsExcept(lm.model, z_clean,
                                        sender=(ls, hs, [ds_last], [donor])),
                                    pp50.FreezeMLP(lm.model, mlp_clean)])
                m_tot_self = proj(ds_t, [pc.ZHeadPatch(lm.model, ls, hs, [ds_last], self_v)])
                m_dir_self = proj(ds_t, [pp50.FreezeAllHeadsExcept(lm.model, z_clean,
                                             sender=(ls, hs, [ds_last], [self_v])),
                                         pp50.FreezeMLP(lm.model, mlp_clean)])
                fh.write(json.dumps({"id": it.get("id"), "split": split, "cohort": cohort,
                                     "layer": ls, "head": hs, "m_clean": round(m_clean, 4),
                                     "m_direct": round(m_direct, 4), "gap": round(gap, 4),
                                     "TOTAL": round(m_tot - m_clean, 4), "DIRECT": round(m_dir - m_clean, 4),
                                     "m_frozen_clean": round(m_dir_self, 4),
                                     "TOTAL_self": round(m_tot_self - m_clean, 4)}) + "\n"); fh.flush()
    fh.close()

    rows = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    summ = {}
    for split in splits:
        sr = [r for r in rows if r["split"] == split]
        if not sr: continue
        gaps = np.array([r["gap"] for r in sr]); med_gap = float(np.median(np.abs(gaps))) if sr else 0.0
        tol = max(0.1, args.rel_tol * med_gap)
        per = {}
        for (ls, hs) in heads:
            hr = [r for r in sr if r["layer"] == ls and r["head"] == hs]
            if not hr: continue
            tot = np.array([r["TOTAL"] for r in hr]); dr = np.array([r["DIRECT"] for r in hr])
            selfdev = float(np.max(np.abs([r["TOTAL_self"] for r in hr])))
            frz = float(np.median([abs(r["m_frozen_clean"] - r["m_clean"]) for r in hr]))
            trustworthy = (frz <= tol) and (selfdev <= tol)
            mask = np.abs(tot) > max(0.1, 0.1 * med_gap)   # only decompose heads with a real TOTAL effect
            fracs = (dr[mask] / tot[mask]) if mask.any() else np.array([])
            per[f"L{ls}H{hs}"] = {
                "n": len(hr), "mean_TOTAL": round(float(tot.mean()), 4), "mean_DIRECT": round(float(dr.mean()), 4),
                "median_direct_frac": (round(float(np.median(fracs)), 3) if fracs.size and trustworthy else None),
                "median_mediated_frac": (round(float(1 - np.median(fracs)), 3) if fracs.size and trustworthy else None),
                "trustworthy": bool(trustworthy), "n_frac": int(mask.sum()),
                "selfswap_max_dev": round(selfdev, 4), "freeze_consistency_dev": round(frz, 4), "tol": round(tol, 4),
            }
        summ[split] = {"n_items": len(set(r["id"] for r in sr)), "median_gap": round(med_gap, 4), "heads": per}
    json.dump({"cohort": cohort, "refusal_layer": rlayer, "heads": args.heads, "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    write_done(out_dir, rows_written=len(rows), extra={"phase": "refusal_mediation"})
    print(f"[refmed] {len(rows)} rows -> {out_dir}", flush=True)
    for split, s in summ.items():
        print(f"  [{split}] n_items={s['n_items']} median_gap={s['median_gap']}", flush=True)
        for h, d in s["heads"].items():
            print(f"    {h}: TOTAL={d['mean_TOTAL']} DIRECT={d['mean_DIRECT']} "
                  f"direct_frac={d['median_direct_frac']} mediated_frac={d['median_mediated_frac']} "
                  f"trust={d['trustworthy']} (selfdev={d['selfswap_max_dev']} freezedev={d['freeze_consistency_dev']})", flush=True)


if __name__ == "__main__":
    main()
