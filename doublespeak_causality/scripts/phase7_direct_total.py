#!/usr/bin/env python3
"""Phase 7 (path mediation, focused): for each Phase-5 candidate head, decompose its causal
necessity into a DIRECT-to-logit path vs a downstream-MEDIATED path, on the ClearHarm split.

direct_frac = DIRECT / TOTAL separates a readout-proximal OUTPUT head (frac ~ 1: its z change
reaches the logit through the residual skip alone) from a CARRY head (frac << 1: most of its
effect is recomputed by downstream heads/MLPs). This resolves the Phase-5 proximity caveat on
the L14-18 candidates (are they genuine mid-band carry, or just near-unembedding output heads?).

Reuses 50_path_patching's freeze primitives verbatim:
  TOTAL[S]  = m_clean - M(sender head z <- BENIGN at the answer pos; everything recomputes)
  DIRECT[S] = m_clean - M(freeze ALL heads+MLPs to clean-DS, inject sender=BENIGN)  [skip-path only]
Metric M = logit_diff(concept - codeword) at the last position (same as 48/49/50). clean = DS.
Controls: self-swap sender (DS's own z -> TOTAL and DIRECT both ~ 0).

Usage:
  python scripts/phase7_direct_total.py --bench data/bench/bench_curated.json \
      --heads L14H4,L14H5,L15H4,L15H8,L15H11,L17H27,L18H16,L18H20,L21H10,L30H15,L31H0 --n-prompts 4
"""
from __future__ import annotations
import argparse, importlib.util, json, os, sys, time
from contextlib import ExitStack
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc

# reuse the freeze primitives + clean-capture from 50_path_patching verbatim
_spec = importlib.util.spec_from_file_location("pp50", os.path.join(DC, "50_path_patching.py"))
pp50 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pp50)


def _single_id(tok, word):
    return tok.encode(" " + word, add_special_tokens=False)[0]


FC_PREFIX = "Choose one label only and answer with just that label."
def fc_question(cw, co):
    return (f'{FC_PREFIX} In the text above, does the word "{cw}" refer to "{co}" or to "{cw}"?')
def demo_block_of(p, marker="\n\nDo not reason, just "):
    return p.rsplit(marker, 1)[0] if marker in p else p


def parse_heads(spec):
    # separator-agnostic (comma / underscore / space) so SLURM --export can avoid commas,
    # which it silently truncates.
    import re
    return [(int(l), int(h)) for l, h in re.findall(r"[Ll](\d+)[Hh](\d+)", spec)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--heads", required=True, help="comma list like L14H5,L15H8,...")
    ap.add_argument("--n-prompts", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(0)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model)
    L = lm.num_layers
    dev = lm.model.device
    cohort = bench.get("_meta", {}).get("cohort", "?")
    heads = parse_heads(args.heads)

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_by_split = {sp: [r for r in rows if r["condition"] == "DOUBLESPEAK" and r["split"] == sp] for sp in splits}

    ts = time.strftime("%Y%m%d_%H%M%S")
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase7_directtotal_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[p7] cohort={cohort} heads={args.heads} -> {out_dir}")

    def fc_tok(raw, cw, co):
        templated = dc.apply_template(lm.tokenizer, demo_block_of(raw) + "\n\n" + fc_question(cw, co))
        return lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)

    @torch.no_grad()
    def logit_diff_last(cid, kid):
        return lambda out: out.logits[0, -1, cid] - out.logits[0, -1, kid]

    @torch.no_grad()
    def run_metric(tok, cid, kid, ctxs=()):
        with ExitStack() as st:
            for c in ctxs:
                st.enter_context(c)
            out = lm.model(**tok, return_dict=True)
        return float(out.logits[0, -1, cid] - out.logits[0, -1, kid])

    @torch.no_grad()
    def capture_benign_z(tok):
        """{L: [n_heads, head_dim]} benign per-head z at benign's LAST position."""
        nh, hd = pc._attn_head_dims(lm.model)
        last = tok["input_ids"].shape[1] - 1
        with pc.ZHeadCapture(lm.model, list(range(L))) as cap:
            lm.model(**tok, return_dict=True)
        return {l: cap.acts[l][0, last].view(nh, hd).float().to(dev) for l in range(L)}

    for split in splits:
        cand = sorted(ds_by_split.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts:
            cand = cand[: args.n_prompts]
        for r in cand:
            concept, codeword = r["target_concept"], r["codeword"]
            cid, kid = _single_id(lm.tokenizer, concept), _single_id(lm.tokenizer, codeword)
            brow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            if brow is None:
                continue
            ds_t = fc_tok(r["prompt"], codeword, concept)
            b_t = fc_tok(brow["prompt"], codeword, concept)
            ds_last = ds_t["input_ids"].shape[1] - 1
            metric = logit_diff_last(cid, kid)
            z_clean, mlp_clean, m_clean = pp50.capture_clean_all(lm, dc.apply_template(
                lm.tokenizer, demo_block_of(r["prompt"]) + "\n\n" + fc_question(codeword, concept)), metric, L)
            benign_z = capture_benign_z(b_t)
            for (ls, hs) in heads:
                donor = benign_z[ls][hs]                          # [head_dim]
                self_v = z_clean[ls][ds_last, hs]                 # DS own z at answer (self-swap)
                # TOTAL: recompute everything
                m_tot = run_metric(ds_t, cid, kid, [pc.ZHeadPatch(lm.model, ls, hs, [ds_last], donor)])
                # DIRECT: freeze all heads (clean DS z) + all MLPs (clean DS), inject sender=benign
                m_dir = run_metric(ds_t, cid, kid,
                                   [pp50.FreezeAllHeadsExcept(lm.model, z_clean,
                                        sender=(ls, hs, [ds_last], [donor])),
                                    pp50.FreezeMLP(lm.model, mlp_clean)])
                # self-swap control (sender = DS own z): TOTAL_self, DIRECT_self ~ 0
                m_tot_self = run_metric(ds_t, cid, kid, [pc.ZHeadPatch(lm.model, ls, hs, [ds_last], self_v)])
                m_dir_self = run_metric(ds_t, cid, kid,
                                        [pp50.FreezeAllHeadsExcept(lm.model, z_clean,
                                             sender=(ls, hs, [ds_last], [self_v])),
                                         pp50.FreezeMLP(lm.model, mlp_clean)])
                fh.write(json.dumps({"sid": r["sid"], "split": split, "cohort": cohort,
                                     "layer": ls, "head": hs, "m_clean": m_clean,
                                     "TOTAL": m_clean - m_tot, "DIRECT": m_clean - m_dir,
                                     "m_frozen_clean": m_dir_self,  # freeze-consistency: ~ m_clean
                                     "TOTAL_self": m_clean - m_tot_self}) + "\n")
    fh.close()

    rows = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    summ = {}
    for split in splits:
        sr = [r for r in rows if r["split"] == split]
        per = {}
        for (ls, hs) in heads:
            hr = [r for r in sr if r["layer"] == ls and r["head"] == hs]
            if not hr:
                continue
            tot = np.array([r["TOTAL"] for r in hr]); dr = np.array([r["DIRECT"] for r in hr])
            selfdev = float(np.max(np.abs([r["TOTAL_self"] for r in hr]))) if hr else None
            frz = float(np.median([abs(r["m_frozen_clean"] - r["m_clean"]) for r in hr]))
            # SANITY GATE (audit findings 14/15): direct_frac is only trustworthy if the freeze
            # machinery reproduces m_clean (freeze-all-clean + clean sender) AND the self-swap is a
            # no-op. If either dev is large the freeze/patch is compromised -> null out direct_frac.
            TOL = 0.05
            trustworthy = (frz <= TOL) and (selfdev is not None and selfdev <= TOL)
            mask = np.abs(tot) > 0.05
            fracs = (dr[mask] / tot[mask]) if mask.any() else np.array([])
            per[f"L{ls}H{hs}"] = {
                "n": len(hr), "mean_TOTAL": round(float(tot.mean()), 4),
                "mean_DIRECT": round(float(dr.mean()), 4),
                "median_direct_frac": (round(float(np.median(fracs)), 3) if fracs.size and trustworthy else None),
                "trustworthy": bool(trustworthy),
                "n_frac": int(mask.sum()), "selfswap_max_dev": round(selfdev, 5) if selfdev is not None else None,
                "freeze_consistency_dev": round(frz, 4),
            }
        summ[split] = per
    json.dump({"cohort": cohort, "heads": args.heads, "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[p7] {len(rows)} rows -> {out_dir}")
    for split, per in summ.items():
        print(f"  [{split}]")
        for h, s in per.items():
            print(f"    {h}: TOTAL={s['mean_TOTAL']} DIRECT={s['mean_DIRECT']} "
                  f"direct_frac={s['median_direct_frac']} trust={s['trustworthy']} (n_frac={s['n_frac']}) "
                  f"selfdev={s['selfswap_max_dev']} freezedev={s['freeze_consistency_dev']}")


if __name__ == "__main__":
    main()
