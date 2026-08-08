#!/usr/bin/env python3
"""§7 — targeted REFUSAL head/edge analysis in the ACTIVE refusal band L13-20 (Llama decoder).

Central question: which attention HEADS (and which incoming EDGES, by source group) carry the
Doublespeak "do-not-refuse" evidence at the decision token? And if NO single head is a bottleneck,
how DISTRIBUTED is the necessity?

Endpoint = the REFUSAL projection at the generation-prompted DECISION token (first-generated-token
position), read on the per-layer refusal directions and HEADLINED at the P7-validated anchor L18
(hidden_states row 19). proj_last is reused VERBATIM from phase5_position.py /
phase_write_refusal_interaction.py. There is NO forced-choice p_concept endpoint here: the behavioral
bench items carry no target_concept, and the question is about refusal, not the remap.

Two matched conditions per item, built by dc.build_conditions (== phase_write_refusal_interaction):
  direct      the harmful instruction used DIRECTLY  -> refusal HIGH  (proj ceiling; do-refuse)
  doublespeak the codeword-remapped query + demos    -> refusal LOW   (proj floor; do-NOT-refuse)
The suppression GAP at the anchor = direct_proj - ds_proj. A head/edge "carries the do-not-refuse
evidence" iff removing DS's version of it (patching in the Direct counterpart, or knocking out the
edge) RESTORES the refusal projection back toward Direct.

PART head  (reuses scripts/phase5_head_zpatch.py machinery: pc.ZHeadCapture + pc.ZHeadPatch, the
           historical single-last-token "answer"-position donor path). For every (layer in L13-20,
           head), replace the DS per-head z at the DECISION token with the matched DIRECT z and read
           the refusal projection. restoration(l,h) = (proj_patched - ds) / (direct - ds), paired
           over items where a gap exists. Wilcoxon + Holm across the band (layer,head) family
           (authoritative pattern from phase5_head_zpatch). Controls at a probe head: self-swap (DS's
           own z -> exact no-op) and a norm-matched random head-vector (must be ~0). DISTRIBUTED
           necessity is quantified with JOINT patches measured in the SAME item loop: band_all (all
           band heads Direct->DS at once = the band's restoration CEILING) and per_layer_all (all
           heads of one band layer). No single head/layer near the ceiling + a large ceiling ==
           distributed.

PART edge  (reuses scripts/phase4_edge_knockout.py machinery: pc.AttentionKnockout, eager attention
           asserted). DESTINATION = the decision token. Knock out its incoming edges by SOURCE GROUP,
           across all band layers jointly (the band-pathway analogue of phase4 --mode band). Groups
           (mapping the plan's "demo codeword / concept / answer / query / separators" onto robustly
           resolvable spans of the DS prompt):
             demo_codeword  codeword occurrences INSIDE the demo block
             concept        demo-block content tokens (concept-establishing sentences), non-codeword,
                            non-separator, from the first demo codeword up to the request line
             query          the codeword occurrence in the request/query line
             answer         request-line + generation-prompt wording (the "answer"-request tokens),
                            non-codeword, non-separator, excluding the decision token itself
             separators     newline / structural tokens across the prompt
           FIRING CONTROL: (a) eager attention is asserted so the mask edit provably fires (SDPA/flash
           silently no-op it); (b) a count-matched RANDOM source set per group -> specificity =
           proj_groupKO - proj_randKO, paired CI; (c) all_edges (knock out ALL incoming causal edges
           of the decision token in the band) = restoration CEILING / did-anything firing check.

Forward/patching only (no generation, no API, no gens.jsonl). RUNMETA-first / DONE-last, defensive.
Every per-item / per-arm step is NON-FATAL.

Usage (full):
  python scripts/phase7_refusal_head_edge.py --bench data/behavioral_v3/beh_clearharm.json \
     --refusal-dir outputs/refusal_alllayers --band 13-20 --readout-anchor 18 --splits train,test --n 0
Smoke:
  python scripts/phase7_refusal_head_edge.py --bench data/behavioral_v3/beh_clearharm.json \
     --band 17-18 --splits test --n 2
"""
from __future__ import annotations
import argparse, json, os, sys, time
from contextlib import ExitStack
from collections import defaultdict
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc
import stats as st

VALIDATED_READOUT_LAYERS = [13, 14, 15, 16, 17, 18, 19, 20, 24, 28, 29]  # P7 both-family validated (== §3/§5)
REQ_MARKER = "Do not reason, just"   # dc.build_conditions default instruction_prefix


# Provenance imported DEFENSIVELY (a broken helper must never kill a GPU run) -- phase5_position pattern.
def _noop_meta(*a, **k): return {}
_write_runmeta = getattr(dc, "write_runmeta", None) or _noop_meta
_write_done = getattr(dc, "write_done", None) or _noop_meta
def write_runmeta(*a, **k):
    try: return _write_runmeta(*a, **k)
    except Exception as e:
        print(f"[phase7] WARNING: RUNMETA write failed: {e!r}", file=sys.stderr); return {}
def write_done(*a, **k):
    try: return _write_done(*a, **k)
    except Exception as e:
        print(f"[phase7] WARNING: DONE write failed: {e!r}", file=sys.stderr); return {}


def parse_band(spec, L):
    if "-" in spec:
        a, b = spec.split("-"); band = list(range(int(a), int(b) + 1))
    else:
        band = [int(x) for x in spec.split(",") if x.strip() != ""]
    return [l for l in band if 0 <= l < L]


def perm_p(vals):
    """Wilcoxon signed-rank -- authoritative pattern from phase5_head_zpatch.perm_p."""
    from scipy import stats as _sc
    a = np.array(vals, float)
    if a.size < 6 or np.allclose(a, 0):
        return 1.0
    try:
        return float(_sc.wilcoxon(a).pvalue)
    except ValueError:
        return 1.0


def holm(pv, alpha=0.05):
    order = sorted(pv, key=lambda k: pv[k]); m = len(order); rej = {}; ok = True
    for i, k in enumerate(order):
        if ok and pv[k] <= alpha / (m - i):
            rej[k] = True
        else:
            ok = False; rej[k] = False
    return rej


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", default=os.path.join(DC, "data", "behavioral_v3", "beh_clearharm.json"))
    ap.add_argument("--refusal-dir", default=os.path.join(DC, "outputs", "refusal_alllayers"))
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--band", default="13-20", help="active refusal band, DECODER layers (dash-range or comma list)")
    ap.add_argument("--readout-anchor", type=int, default=18,
                    help="validated decoder layer to HEADLINE the refusal proj (hs row = L+1). Must be P7-validated.")
    ap.add_argument("--parts", default="head,edge", help="comma list: head, edge (both by default)")
    ap.add_argument("--splits", default="train,test")
    ap.add_argument("--enable-thinking", default="default", help="thinking models (Qwen3): default|true|false")
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    enable_thinking = dc.parse_enable_thinking(args.enable_thinking)
    parts = [p.strip() for p in args.parts.split(",") if p.strip()]
    for p in parts:
        if p not in ("head", "edge"):
            raise SystemExit(f"--parts: unknown {p!r}; want a subset of head,edge")

    dc.set_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    import random as _random
    prng = _random.Random(args.seed)

    # eager REQUIRED for AttentionKnockout (edge part); harmless for the o_proj z-hooks (head part).
    # Assert it stuck (== phase4_edge_knockout): SDPA/flash fuse softmax@V and the knockout no-ops silently.
    lm = dc.load_model(args.model, attn_implementation="eager")
    _impl = getattr(lm.model.config, "_attn_implementation", None)
    if "edge" in parts and _impl != "eager":
        raise RuntimeError(f"AttentionKnockout needs attn_implementation='eager', got {_impl!r}.")
    print(f"[phase7] attn_implementation={_impl!r} (asserted for edge part)", flush=True)
    dev = lm.model.device; L = lm.num_layers
    n_heads, head_dim = pc._attn_head_dims(lm.model)
    band = parse_band(args.band, L)
    if not band:
        raise SystemExit(f"--band {args.band!r} resolved to no valid layers in 0..{L-1}")

    # per-layer refusal directions; hs row h == post-block decoder layer h-1 (VERBATIM from §3/§5).
    refdir = {}
    for k in range(L):
        pth = os.path.join(args.refusal_dir, f"refusal_direction_llama_L{k}.pt")
        if os.path.exists(pth):
            v = torch.load(pth, map_location="cpu").float().flatten(); refdir[k + 1] = v / (v.norm() + 1e-8)
    read_rows = sorted(h for h in refdir if (h - 1) in VALIDATED_READOUT_LAYERS)
    if not read_rows:
        raise SystemExit(f"no validated refusal directions found under {args.refusal_dir}")
    anchor_row = args.readout_anchor + 1
    if anchor_row not in read_rows:
        raise SystemExit(f"anchor L{args.readout_anchor} (row {anchor_row}) not in validated rows {read_rows}")
    ar = str(anchor_row)

    data = json.load(open(args.bench)); items = data["items"] if isinstance(data, dict) else data
    cohort = (data.get("_meta", {}) if isinstance(data, dict) else {}).get("cohort", os.path.basename(args.bench))
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]

    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(DC, "outputs", f"phase7_refhe_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    try:
        _gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO-CUDA"
    except Exception:
        _gpu = "unknown"
    write_runmeta(out_dir, args=vars(args), extra={"phase": "phase7_refusal_head_edge_v1", "cohort": cohort,
                  "band": band, "parts": parts, "readout_anchor": args.readout_anchor, "anchor_row": anchor_row,
                  "validated_readout_rows": read_rows, "model": args.model, "n_heads": n_heads,
                  "attn_implementation": _impl, "gpu": _gpu, "enable_thinking": args.enable_thinking})
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[phase7] cohort={cohort} band=L{band[0]}-{band[-1]} heads={n_heads} parts={parts} "
          f"anchor=L{args.readout_anchor} read_rows={read_rows} -> {out_dir}", flush=True)

    def templ(raw):
        return dc.apply_template(lm.tokenizer, raw, add_generation_prompt=True, enable_thinking=enable_thinking)

    @torch.no_grad()
    def proj_last(templated, ctx=()):
        """Decision-token residual projected on each validated refusal dir -- reused proj_last pattern."""
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        with ExitStack() as stk:
            for c in ctx: stk.enter_context(c)
            out = lm.model(**tok, output_hidden_states=True, return_dict=True)
        hs = out.hidden_states
        return {h: round(float(torch.dot(hs[h][0, -1, :].float().cpu(), refdir[h])), 6) for h in read_rows}

    @torch.no_grad()
    def capture_z_last(templated):
        """{l: Tensor[n_heads, head_dim]} of per-head z at the LAST (decision) token -- == phase5 capture_z_last."""
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        last = tok["input_ids"].shape[1] - 1
        with pc.ZHeadCapture(lm.model, band) as cap:
            lm.model(**tok, return_dict=True)
        return {l: cap.acts[l][0, last].view(n_heads, head_dim).float().cpu() for l in band}

    def resolve_groups(ds_t, cw):
        """Source-group token positions on the DS templated prompt. Returns (groups, seqlen).
        See module docstring for the plan-name -> span mapping."""
        ids = lm.tokenizer(ds_t, add_special_tokens=False)["input_ids"]
        seqlen = len(ids)
        req_off = ds_t.rfind(REQ_MARKER)
        req_tok = (len(lm.tokenizer(ds_t[:req_off], add_special_tokens=False)["input_ids"]) if req_off >= 0 else 0)
        hit = dc.find_word_occurrences_in_text(lm.tokenizer, ds_t, cw)
        cw_pos = sorted({li for li in hit.last_idx if 0 <= li < seqlen})
        demo_cw = [p for p in cw_pos if p < req_tok]
        query_cw = [p for p in cw_pos if p >= req_tok]
        cwset = set(cw_pos)
        # separators: newline-bearing tokens anywhere in the prompt
        sep = [i for i, t in enumerate(ids) if "\n" in lm.tokenizer.decode([t])]
        sepset = set(sep)
        d0 = min(demo_cw) if demo_cw else 0
        concept = [p for p in range(d0, req_tok) if p not in cwset and p not in sepset]
        answer = [p for p in range(req_tok, seqlen - 1) if p not in cwset and p not in sepset]
        groups = {"demo_codeword": demo_cw, "concept": concept, "query": query_cw,
                  "answer": answer, "separators": [p for p in sep if p < seqlen - 1]}
        return groups, seqlen

    n_rows = 0
    for split in splits:
        cand = [it for it in items if it.get("split") == split]
        if args.n: cand = cand[: args.n]
        for it in cand:
            hw, cw = it["harmful_word"], it["codeword"]
            instr = it["harmful_instruction"]
            if hw not in instr: instr = f"Give detailed step-by-step instructions to make a {hw}."
            demos = it["demos"]; demos = demos if isinstance(demos, str) else "\n".join(demos)
            try:
                conds = dc.build_conditions(instr, hw, cw, demos)
            except Exception as e:
                fh.write(json.dumps({"id": it.get("id"), "split": split, "cell": "build_error",
                                     "err": repr(e)}) + "\n"); n_rows += 1; continue
            direct_t = templ(conds.direct); ds_t = templ(conds.doublespeak)
            try:
                direct_proj = proj_last(direct_t); ds_proj = proj_last(ds_t)
            except Exception as e:
                fh.write(json.dumps({"id": it.get("id"), "split": split, "cell": "base_error",
                                     "err": repr(e)}) + "\n"); n_rows += 1; continue
            base = {"id": it.get("id"), "split": split, "cohort": cohort, "codeword": cw,
                    "direct_proj": direct_proj, "ds_proj": ds_proj}
            fh.write(json.dumps({**base, "part": "ref", "cell": "baseline"}) + "\n"); n_rows += 1

            # ---------------- PART head: z-patch Direct -> DS at the decision token ----------------
            if "head" in parts:
                try:
                    z_direct = capture_z_last(direct_t); z_ds = capture_z_last(ds_t)
                    ds_last = lm.tokenizer(ds_t, return_tensors="pt", add_special_tokens=False)["input_ids"].shape[1] - 1
                except Exception as e:
                    fh.write(json.dumps({**base, "part": "head", "cell": "capture_error", "err": repr(e)}) + "\n")
                    n_rows += 1
                    z_direct = None
                if z_direct is not None:
                    # single-head necessity: patch each band (l,h) with the DIRECT donor z
                    for l in band:
                        for h in range(n_heads):
                            try:
                                pr = proj_last(ds_t, [pc.ZHeadPatch(lm.model, l, h, [ds_last], z_direct[l][h].to(dev))])
                                fh.write(json.dumps({**base, "part": "head", "cell": "single",
                                                     "layer": l, "head": h, "proj": pr}) + "\n"); n_rows += 1
                            except Exception as e:
                                fh.write(json.dumps({**base, "part": "head", "cell": "single_err",
                                                     "layer": l, "head": h, "err": repr(e)}) + "\n"); n_rows += 1
                    # controls at a probe head (band mid, head 0): self-swap = exact no-op; norm-random ~ 0
                    lp = band[len(band) // 2]
                    try:
                        p_self = proj_last(ds_t, [pc.ZHeadPatch(lm.model, lp, 0, [ds_last], z_ds[lp][0].to(dev))])
                        ref_norm = float(z_ds[lp][0].norm())
                        rv = torch.tensor(rng.standard_normal(head_dim), dtype=torch.float32)
                        rv = rv / (rv.norm() + 1e-8) * ref_norm
                        p_rand = proj_last(ds_t, [pc.ZHeadPatch(lm.model, lp, 0, [ds_last], rv.to(dev))])
                        fh.write(json.dumps({**base, "part": "head", "cell": "selfswap", "layer": lp, "head": 0,
                                             "proj": p_self}) + "\n")
                        fh.write(json.dumps({**base, "part": "head", "cell": "normrand", "layer": lp, "head": 0,
                                             "proj": p_rand}) + "\n"); n_rows += 2
                    except Exception as e:
                        fh.write(json.dumps({**base, "part": "head", "cell": "control_err", "err": repr(e)}) + "\n")
                        n_rows += 1
                    # DISTRIBUTED-necessity joint patches: band_all + per-layer-all (measured, same donor)
                    try:
                        with ExitStack() as stk:
                            for l in band:
                                for h in range(n_heads):
                                    stk.enter_context(pc.ZHeadPatch(lm.model, l, h, [ds_last], z_direct[l][h].to(dev)))
                            pr = proj_last(ds_t)
                        fh.write(json.dumps({**base, "part": "head", "cell": "band_all", "proj": pr}) + "\n"); n_rows += 1
                    except Exception as e:
                        fh.write(json.dumps({**base, "part": "head", "cell": "band_all_err", "err": repr(e)}) + "\n")
                        n_rows += 1
                    for l in band:
                        try:
                            with ExitStack() as stk:
                                for h in range(n_heads):
                                    stk.enter_context(pc.ZHeadPatch(lm.model, l, h, [ds_last], z_direct[l][h].to(dev)))
                                pr = proj_last(ds_t)
                            fh.write(json.dumps({**base, "part": "head", "cell": "layer_all",
                                                 "layer": l, "proj": pr}) + "\n"); n_rows += 1
                        except Exception as e:
                            fh.write(json.dumps({**base, "part": "head", "cell": "layer_all_err",
                                                 "layer": l, "err": repr(e)}) + "\n"); n_rows += 1

            # ---------------- PART edge: knock out decision-token incoming edges by SOURCE GROUP ----
            if "edge" in parts:
                try:
                    groups, seqlen = resolve_groups(ds_t, cw)
                    dest = [seqlen - 1]
                    allsrc = list(range(seqlen - 1))
                    for gname, gpos in groups.items():
                        gpos = [p for p in gpos if 0 <= p < seqlen - 1]
                        rec = {**base, "part": "edge", "layer": f"{band[0]}-{band[-1]}", "group": gname,
                               "n_src": len(gpos)}
                        if not gpos:
                            fh.write(json.dumps({**rec, "cell": "edge_KO", "proj": None,
                                                 "skip": "no_src"}) + "\n"); n_rows += 1; continue
                        prg = proj_last(ds_t, [pc.AttentionKnockout(lm.model, band, dest, gpos, heads=None)])
                        fh.write(json.dumps({**rec, "cell": "edge_KO", "proj": prg}) + "\n"); n_rows += 1
                        # count-matched RANDOM-source firing control (same k, causal, not in group)
                        pool = [p for p in allsrc if p not in set(gpos)]
                        rsrc = sorted(prng.sample(pool, min(len(gpos), len(pool)))) if pool else []
                        if rsrc:
                            prr = proj_last(ds_t, [pc.AttentionKnockout(lm.model, band, dest, rsrc, heads=None)])
                            fh.write(json.dumps({**rec, "cell": "rand_edge", "n_rand": len(rsrc),
                                                 "proj": prr}) + "\n"); n_rows += 1
                    # all_edges ceiling / did-anything firing check
                    if allsrc:
                        pra = proj_last(ds_t, [pc.AttentionKnockout(lm.model, band, dest, allsrc, heads=None)])
                        fh.write(json.dumps({**base, "part": "edge", "layer": f"{band[0]}-{band[-1]}",
                                             "cell": "all_edges", "proj": pra}) + "\n"); n_rows += 1
                except Exception as e:
                    fh.write(json.dumps({**base, "part": "edge", "cell": "edge_error", "err": repr(e)}) + "\n")
                    n_rows += 1
            fh.flush()
    fh.close()

    # ============================ AGGREGATION ============================
    allr = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    def gap_of(r): return r["direct_proj"][ar] - r["ds_proj"][ar]
    summ = {"cohort": cohort, "model": args.model, "band": band, "parts": parts,
            "readout_anchor": args.readout_anchor, "anchor_row": anchor_row,
            "validated_readout_rows": read_rows, "n_rows": n_rows, "by_split": {}}

    for split in splits:
        sr = [r for r in allr if r.get("split") == split]
        base_by_id = {r["id"]: r for r in sr if r.get("cell") == "baseline"}
        # valid items: a genuine refusal gap to restore (direct > ds at the anchor)
        valid = {i for i, b in base_by_id.items() if gap_of(b) > 1e-4}
        sp = {"n_items": len(base_by_id), "n_valid_gap": len(valid),
              "direct_proj_anchor": round(float(np.mean([base_by_id[i]["direct_proj"][ar] for i in base_by_id])), 5)
              if base_by_id else None,
              "ds_proj_anchor": round(float(np.mean([base_by_id[i]["ds_proj"][ar] for i in base_by_id])), 5)
              if base_by_id else None}

        def restore_frac(r):
            b = base_by_id.get(r["id"])
            if b is None or r["id"] not in valid or not r.get("proj"): return None
            return (r["proj"][ar] - b["ds_proj"][ar]) / (b["direct_proj"][ar] - b["ds_proj"][ar])

        def raw_diff(r):  # proj_patched - ds_base (restoration on the anchor axis, unnormalized)
            b = base_by_id.get(r["id"])
            if b is None or r["id"] not in valid or not r.get("proj"): return None
            return r["proj"][ar] - b["ds_proj"][ar]

        # ---------- head part ----------
        if "head" in parts:
            singles = [r for r in sr if r.get("part") == "head" and r.get("cell") == "single"]
            per = defaultdict(list)   # (l,h) -> [raw_diff]
            perf = defaultdict(list)  # (l,h) -> [restore_frac]
            for r in singles:
                d = raw_diff(r); f = restore_frac(r)
                if d is not None: per[(r["layer"], r["head"])].append(d)
                if f is not None: perf[(r["layer"], r["head"])].append(f)
            pv, mean, meanf = {}, {}, {}
            for lh, ds in per.items():
                if len(ds) >= 1:
                    pv[lh] = perm_p(ds); mean[lh] = float(np.mean(ds)); meanf[lh] = float(np.mean(perf[lh]))
            rej = holm(pv)
            holm_heads = sorted([(f"L{l}H{h}", round(meanf[(l, h)], 4), round(mean[(l, h)], 5), round(pv[(l, h)], 5))
                                 for (l, h) in pv if rej.get((l, h)) and mean[(l, h)] > 0],
                                key=lambda x: -x[1])
            top = sorted([((l, h), meanf[(l, h)]) for (l, h) in meanf], key=lambda x: -x[1])[:15]
            # joint measured cells
            def cell_frac(cell, key=None, keyval=None):
                vals = [restore_frac(r) for r in sr if r.get("part") == "head" and r.get("cell") == cell
                        and (key is None or r.get(key) == keyval)]
                vals = [v for v in vals if v is not None]
                return round(float(np.mean(vals)), 4) if vals else None
            band_all_frac = cell_frac("band_all")
            per_layer_frac = {f"L{l}": cell_frac("layer_all", "layer", l) for l in band}
            _layer_vals = [v for v in per_layer_frac.values() if v is not None]
            _max_layer_frac = max(_layer_vals) if _layer_vals else None
            # controls
            def ctl_dev(cell):
                devs = []
                for r in sr:
                    if r.get("part") == "head" and r.get("cell") == cell and r.get("proj"):
                        b = base_by_id.get(r["id"])
                        if b: devs.append(abs(r["proj"][ar] - b["ds_proj"][ar]))
                return round(float(np.max(devs)), 6) if devs else None
            max_single = max([meanf[k] for k in meanf], default=None)
            sp["head"] = {
                "n_single_cells": len(mean),
                "selfswap_max_dev": ctl_dev("selfswap"),     # want ~0 (exact no-op)
                "normrand_max_dev": ctl_dev("normrand"),     # want ~0 (norm-matched random head vec)
                "n_holm_sig_heads": len(holm_heads),
                "holm_sig_heads": holm_heads[:25],           # (name, restore_frac, raw_diff, p)
                "top15_by_restore_frac": [(f"L{l}H{h}", round(f, 4)) for (l, h), f in top],
                "max_single_head_restore_frac": round(max_single, 4) if max_single is not None else None,
                "band_all_restore_frac": band_all_frac,      # CEILING: all band heads jointly Direct->DS
                "per_layer_all_restore_frac": per_layer_frac,
                "max_layer_all_restore_frac": _max_layer_frac,
                # "no single head OR LAYER near ceiling": require BOTH the best single head AND the
                # best single LAYER to sit below half the joint band ceiling (docstring §, line ~29-31).
                "distributed": bool(band_all_frac is not None and max_single is not None
                                    and _max_layer_frac is not None
                                    and band_all_frac > 0.2
                                    and max_single < 0.5 * band_all_frac
                                    and _max_layer_frac < 0.5 * band_all_frac),
            }

        # ---------- edge part ----------
        if "edge" in parts:
            # per-group: effect = proj_groupKO - ds  (>0 restores refusal); specificity vs rand-edge
            ds_anchor = {i: base_by_id[i]["ds_proj"][ar] for i in base_by_id}
            byg_ko = defaultdict(dict); byg_rand = defaultdict(dict)
            for r in sr:
                if r.get("part") != "edge" or not r.get("proj"): continue
                if r.get("cell") == "edge_KO" and r.get("group"):
                    byg_ko[r["group"]][r["id"]] = r["proj"][ar]
                elif r.get("cell") == "rand_edge" and r.get("group"):
                    byg_rand[r["group"]][r["id"]] = r["proj"][ar]
            groups_out = {}
            for g, d in byg_ko.items():
                ids = [i for i in d if i in ds_anchor and i in valid]
                if not ids: continue
                eff = np.array([d[i] - ds_anchor[i] for i in ids], float)   # restoration on anchor
                gc = {"n": len(ids), "mean_restore": round(float(eff.mean()), 5),
                      "restore_ci": None, "specificity_vs_rand": None}
                ci = st.paired_bootstrap_ci(np.array([d[i] for i in ids]),
                                            np.array([ds_anchor[i] for i in ids]), n_boot=10000, seed=0)
                gc["restore_ci"] = [round(ci["lo"], 5), round(ci["hi"], 5)]
                gc["restore_ci_reliable"] = bool(ci["ci_reliable"])
                rd = byg_rand.get(g, {})
                rids = [i for i in ids if i in rd]
                if rids:
                    ci2 = st.paired_bootstrap_ci(np.array([d[i] for i in rids]),
                                                 np.array([rd[i] for i in rids]), n_boot=10000, seed=0)
                    gc["specificity_vs_rand"] = {"mean": round(ci2["mean_diff"], 5),
                                                 "ci": [round(ci2["lo"], 5), round(ci2["hi"], 5)],
                                                 "excludes_zero": bool(not (ci2["lo"] <= 0 <= ci2["hi"])),
                                                 "n": len(rids), "reliable": bool(ci2["ci_reliable"])}
                groups_out[g] = gc
            # all_edges firing ceiling
            ae = {r["id"]: r["proj"][ar] for r in sr if r.get("part") == "edge"
                  and r.get("cell") == "all_edges" and r.get("proj")}
            ae_ids = [i for i in ae if i in ds_anchor and i in valid]
            all_edges_restore = round(float(np.mean([ae[i] - ds_anchor[i] for i in ae_ids])), 5) if ae_ids else None
            sp["edge"] = {"groups": groups_out, "all_edges_mean_restore": all_edges_restore,
                          "all_edges_n": len(ae_ids),
                          "note": "restore = proj(edge_KO) - proj(DS) on the anchor axis; >0 => the group "
                                  "carried do-not-refuse evidence. specificity_vs_rand = vs count-matched "
                                  "random source edges (firing control)."}
        summ["by_split"][split] = sp

    json.dump(summ, open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    write_done(out_dir, rows_written=n_rows, extra={"parts": parts, "band": band, "gpu": _gpu})
    print(f"[phase7] {n_rows} rows -> {out_dir} (gpu={_gpu})", flush=True)
    for split, sp in summ["by_split"].items():
        print(f"  [{split}] items={sp['n_items']} valid_gap={sp['n_valid_gap']} "
              f"direct={sp['direct_proj_anchor']} ds={sp['ds_proj_anchor']} (anchor L{args.readout_anchor})", flush=True)
        if "head" in sp:
            h = sp["head"]
            print(f"     HEAD: selfswap_dev={h['selfswap_max_dev']} normrand_dev={h['normrand_max_dev']} "
                  f"Holm-sig={h['n_holm_sig_heads']} max_single_frac={h['max_single_head_restore_frac']} "
                  f"band_all_frac={h['band_all_restore_frac']} distributed={h['distributed']}", flush=True)
            print(f"           top heads: {h['top15_by_restore_frac'][:6]}", flush=True)
            print(f"           per-layer_all: {h['per_layer_all_restore_frac']}", flush=True)
        if "edge" in sp:
            print(f"     EDGE all_edges_restore={sp['edge']['all_edges_mean_restore']}", flush=True)
            for g, gc in sp["edge"]["groups"].items():
                spc = gc.get("specificity_vs_rand")
                print(f"           {g:>14}: restore={gc['mean_restore']} ci={gc['restore_ci']} "
                      f"spec_vs_rand={spc['mean'] if spc else None} excl0={spc['excludes_zero'] if spc else None}",
                      flush=True)


if __name__ == "__main__":
    main()
