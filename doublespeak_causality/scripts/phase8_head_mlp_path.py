#!/usr/bin/env python3
"""phase8_head_mlp_path.py -- §8 full head->MLP PATH PATCHING (the P5 backlog).

EXTENDS the proven head->head path patcher (../50_path_patching.py) to head->MLP RECEIVERS.
The head->head engine (50) already showed whether mid-band heads route through OTHER heads;
this asks the complementary question the plan reserves for §8: does a sender head route its
isolated contribution through an MLP WRITE/SUPPRESSION receiver on its way to the endpoint?

Two families (same engine, different endpoint + clean/corrupt contrast):

  8.1 concept  -- senders = candidate retrieval heads (L7-14, from 49's head_attribution.json
                  or --sender-heads); receivers = the L8-13 MLP write band; endpoint = p_concept
                  at the final position. clean=DOUBLESPEAK, corrupt=NEUTRAL_CODEWORD (the demo
                  effect), identical contrast to 48/49/50 on data/pair_benchmark/pair_*.json.

  8.2 refusal  -- senders = demo-processing heads; receivers = the refusal-SUPPRESSION MLP band
                  (default L8-17); endpoint = decision-token REFUSAL projection at L18 (project
                  hidden_states[refusal_layer+1] at the last prompt token onto the validated
                  per-layer refusal direction refusal_direction_llama_L{refusal_layer}.pt).
                  clean=DOUBLESPEAK, corrupt=NEUTRAL (default; --corrupt-cond direct available),
                  built per behavioral item with ds_common.build_conditions.

PATH-PATCHING MECHANICS (reuse 50's linearity lever verbatim; o_proj(z)=z@W_o is linear, so
overwriting the o_proj INPUT of a layer with cached CLEAN z FREEZES that whole attention sublayer
to clean, and swapping ONLY the sender head's block to corrupt injects exactly the sender's
isolated delta with zero leakage; MLPs frozen by overwriting their output with cached clean).

Per sender S=(L_S,h_S) and receiver MLP R=L_R (L_R > L_S, L_R <= endpoint layer):
  TOTAL[S]        = single-head true patch, nothing frozen (== 49's true delta at THIS endpoint).
  DIRECT[S]       = freeze ALL heads+MLPs to clean, set sender=corrupt -> S's direct-to-endpoint.
  EDGE[S->R_mlp]  = run 3a: freeze-all-clean + sender=corrupt, and CAPTURE R's MLP output
                    RECOMPUTED on the sender-perturbed residual (before its freeze-overwrite);
                    run 3b: patch ONLY R's MLP output with that captured value on an otherwise
                    CLEAN run and let everything downstream recompute -> endpoint - m_clean.
                    (Exactly 50's head->head EDGE with the receiver being an MLP, not a head.)

SPECIFICITY (the science gate -- an edge is only real if it clears these):
  * self donor      -- patch R's MLP with its OWN clean value (must be ~0: locality no-op).
  * random sender   -- a random head OUTSIDE the candidate set, matched sender band.
  * random receiver -- a random MLP layer OUTSIDE the write band.
  * matched path    -- a matched NON-candidate head (same layer as a candidate) -> candidate R.

RECONSTRUCTION (optional, --recon-full): TOTAL[S] ~= DIRECT[S] + sum_R EDGE[S->R_mlp]
                    + sum_R' EDGE[S->R'_head] (head edges among the sender set, reusing the same
                    freeze machinery). Reported as median rel-err with a recon gate.

DELIVERABLE: a sparse graph if the per-sender edge mass concentrates on a few receivers AND clears
controls; otherwise the full distributed sender x receiver path matrix. Both are always emitted;
the verdict picks. Scalars only -- no prompt text / completions persisted.

FORWARD/PATCHING job (no generation): the >=23GB GPU allowlist applies (see slurm wrapper).

Run (GPU):
  # 8.1 concept
  python scripts/phase8_head_mlp_path.py --family concept \
      --bench data/pair_benchmark/pair_carrot_bomb.json \
      --from-head-attr outputs/head_attr_<...>/head_attribution.json \
      --lo 7 --hi 14 --topn 6 --mlp-lo 8 --mlp-hi 13 --metric p_concept
  # 8.2 refusal
  python scripts/phase8_head_mlp_path.py --family refusal \
      --bench data/behavioral_v3/beh_clearharm.json \
      --from-head-attr outputs/head_attr_<...>/head_attribution.json \
      --lo 7 --hi 14 --topn 6 --mlp-lo 8 --mlp-hi 17 --refusal-layer 18 --split test --item-idx 0
Smoke: --topn 2 --mlp-lo <a> --mlp-hi <a+1> --rand-senders 1 --rand-receivers 1 --item-idx 0
"""
from __future__ import annotations
import os, sys, json, time, argparse, importlib.util, statistics
from contextlib import ExitStack
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))          # .../doublespeak_causality/scripts
DC = os.path.dirname(HERE)                                  # .../doublespeak_causality
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(DC, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


atp48 = _load("atp48", "48_attribution_patching.py")
ha49 = _load("ha49", "49_head_attribution.py")
p50 = _load("pp50", "50_path_patching.py")                 # reuse the proven head->head engine

# proven, reused verbatim from 50 (linearity lever + per-position z primitives)
FreezeAllHeadsExcept = p50.FreezeAllHeadsExcept
ZHeadPatchMulti = p50.ZHeadPatchMulti


# --------------------------------------------------------------------------- #
# New receiver-side primitives: MLP freeze-with-capture + MLP-output patch
# --------------------------------------------------------------------------- #
class FreezeMLPCapture:
    """Like 50.FreezeMLP (overwrite every layer.mlp output with cached clean output), but at the
    receiver layer CAPTURE the RECOMPUTED mlp output at `positions` BEFORE the clean-overwrite.
    In run 3a, upstream heads/MLPs are all frozen to clean except the sender head, so the receiver
    MLP's input residual = clean + the sender's isolated delta; the captured output is thus the
    sender-derived contribution to that MLP (with zero leakage from any other head/MLP)."""

    def __init__(self, model, mlp_clean, receiver_capture=None):
        self.layers = dc._get_layers(model)
        self.mlp_clean = mlp_clean                          # {L: [seq, hidden] on device}
        self.receiver = receiver_capture                    # (L_R, positions, out_dict) or None
        self._handles = []

    def _hook(self, li):
        def f(module, inp, out):
            is_t = isinstance(out, tuple)
            h = out[0] if is_t else out
            if self.receiver is not None and li == self.receiver[0]:
                _, pos, od = self.receiver
                od["mlp"] = h.detach()[0, pos, :].float().clone()   # [P, hidden], BEFORE overwrite
            hc = self.mlp_clean[li].to(h.dtype).unsqueeze(0)        # [1, seq, hidden]
            return (hc,) + tuple(out[1:]) if is_t else hc
        return f

    def __enter__(self):
        for li, layer in enumerate(self.layers):
            self._handles.append(layer.mlp.register_forward_hook(self._hook(li)))
        return self

    def __exit__(self, *e):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


class MLPOutPatch:
    """forward_hook on ONE layer.mlp: overwrite its output at `positions` with `vecs[i]` ([P, hidden]).
    Nothing else frozen -> downstream recomputes with only this MLP's output changed (run 3b)."""

    def __init__(self, model, layer_idx, positions, vecs):
        self.mlp = dc._get_layers(model)[layer_idx].mlp
        self.positions = list(positions)
        self.vecs = vecs                                    # [P, hidden] tensor
        self._h = None

    def _hook(self, module, inp, out):
        is_t = isinstance(out, tuple)
        h = out[0] if is_t else out
        h = h.clone()
        seq = h.shape[1]
        for i, p in enumerate(self.positions):
            if 0 <= p < seq:
                h[0, p, :] = self.vecs[i].to(h.dtype)
        return (h,) + tuple(out[1:]) if is_t else h

    def __enter__(self):
        self._h = self.mlp.register_forward_hook(self._hook); return self

    def __exit__(self, *e):
        if self._h:
            self._h.remove(); self._h = None
        return False


@torch.no_grad()
def capture_clean_all(lm, text, metric, need_hs):
    """Cache clean per-head z {L:[seq,H,hd]}, clean mlp outputs {L:[seq,hidden]}, and m_clean.
    Mirrors 50.capture_clean_all but requests output_hidden_states when the endpoint needs it
    (refusal readout reads a hidden_states row; concept reads next-token logits)."""
    tok = lm.tokenizer(text, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
    layers = dc._get_layers(lm.model)
    nh, hd = pc._attn_head_dims(lm.model)
    zc, mc, handles = {}, {}, []

    def zhook(li):
        def f(module, args):
            zc[li] = args[0].detach()[0].float().view(-1, nh, hd)
            return None
        return f

    def mhook(li):
        def f(module, inp, out):
            h = out[0] if isinstance(out, tuple) else out
            mc[li] = h.detach()[0].float()
            return None
        return f

    for li, layer in enumerate(layers):
        handles.append(layer.self_attn.o_proj.register_forward_pre_hook(zhook(li)))
        handles.append(layer.mlp.register_forward_hook(mhook(li)))
    out = lm.model(**tok, output_hidden_states=need_hs, return_dict=True)
    m_clean = float(metric(out).detach())
    for h in handles:
        h.remove()
    dev = lm.model.device
    return ({L: zc[L].to(dev) for L in zc}, {L: mc[L].to(dev) for L in mc}, m_clean)


# --------------------------------------------------------------------------- #
# Family setup: clean/corrupt texts, alignment, endpoint metric
# --------------------------------------------------------------------------- #
def _select_behav_item(bench, split, item_idx):
    items = bench["items"] if isinstance(bench, dict) else bench
    if split:
        items = [r for r in items if r.get("split") == split]
    if not items:
        raise ValueError(f"no behavioral items for split={split!r}")
    if item_idx < 0 or item_idx >= len(items):
        raise ValueError(f"item-idx {item_idx} out of range (0..{len(items) - 1})")
    return items[item_idx]


def setup_concept(lm, bench, args, et):
    pair = bench["pair"]; concept, codeword = pair["concept"], pair["codeword"]
    clean_row, corr_row = atp48._select_pair_rows(bench, args.readout, args.split)
    clean_text = dc.apply_template(lm.tokenizer, clean_row["prompt"], enable_thinking=et)
    corr_text = dc.apply_template(lm.tokenizer, corr_row["prompt"], enable_thinking=et)
    positions, mapping, diag = atp48.build_alignment(lm, clean_text, corr_text, codeword)
    metric = atp48.make_metric(lm, concept, codeword, args.metric)
    endpoint = {"kind": "concept", "metric": args.metric, "layer": lm.num_layers,
                "concept": concept, "codeword": codeword}
    return dict(clean_text=clean_text, corr_text=corr_text, positions=positions, mapping=mapping,
                diag=diag, metric=metric, need_hs=False, endpoint=endpoint,
                receiver_max_layer=lm.num_layers - 1)


def setup_refusal(lm, bench, args, et):
    item = _select_behav_item(bench, args.split, args.item_idx)
    cond = dc.build_conditions(item["harmful_instruction"], item["harmful_word"],
                               item["codeword"], item["demos"])
    codeword = item["codeword"]
    clean_raw = cond.doublespeak                                    # demos installed
    corr_raw = cond.neutral if args.corrupt_cond == "neutral" else cond.direct
    clean_text = dc.apply_template(lm.tokenizer, clean_raw, enable_thinking=et)
    corr_text = dc.apply_template(lm.tokenizer, corr_raw, enable_thinking=et)
    # align on the shared readout suffix (+ codeword sites when the corrupt has the codeword)
    positions, mapping, diag = atp48.build_alignment(lm, clean_text, corr_text, codeword)
    # refusal direction at the readout layer (file L{k}.pt lives in hidden_states[k+1])
    rp = os.path.join(args.refusal_dir, f"refusal_direction_llama_L{args.refusal_layer}.pt")
    if not os.path.exists(rp):
        raise FileNotFoundError(f"refusal direction not found: {rp}")
    refdir = torch.load(rp, map_location="cpu").float().flatten()
    refdir = (refdir / (refdir.norm() + 1e-8)).to(lm.model.device)
    hs_row = args.refusal_layer + 1                                 # hidden_states index
    dec_pos = len(lm.tokenizer(clean_text, add_special_tokens=False)["input_ids"]) - 1

    def metric(out):
        h = out.hidden_states[hs_row][0, dec_pos, :].float()        # decision-token residual
        return torch.dot(h, refdir)                                 # refusal-axis projection

    endpoint = {"kind": "refusal", "refusal_layer": args.refusal_layer, "hs_row": hs_row,
                "dec_pos": dec_pos, "corrupt_cond": args.corrupt_cond, "item_id": item.get("id")}
    return dict(clean_text=clean_text, corr_text=corr_text, positions=positions, mapping=mapping,
                diag=diag, metric=metric, need_hs=True, endpoint=endpoint,
                receiver_max_layer=args.refusal_layer)


# --------------------------------------------------------------------------- #
# Head / MLP selection
# --------------------------------------------------------------------------- #
def pick_sender_heads(args):
    if args.sender_heads:
        heads = [tuple(int(x) for x in hs.split(":")) for hs in args.sender_heads.split(",") if hs.strip()]
    elif args.from_head_attr:
        ha = json.load(open(args.from_head_attr))
        cells = [(int(h["layer"]), int(h["head"]), h["sum_abs_atp"]) for h in ha["top_heads"]
                 if args.lo <= int(h["layer"]) <= args.hi]
        cells.sort(key=lambda c: c[2], reverse=True)
        heads = [(L, h) for L, h, _ in cells[: args.topn]]
    else:
        raise SystemExit("provide --sender-heads or --from-head-attr")
    return sorted(set(heads))


def pick_receiver_mlps(args, receiver_max_layer):
    if args.receiver_mlps:
        rec = [int(x) for x in args.receiver_mlps.split(",") if x.strip()]
    else:
        rec = list(range(args.mlp_lo, args.mlp_hi + 1))
    return sorted({L for L in rec if 0 <= L <= receiver_max_layer})


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
def run(lm, bench, args):
    et = dc.parse_enable_thinking(args.enable_thinking)
    ctx = setup_concept(lm, bench, args, et) if args.family == "concept" \
        else setup_refusal(lm, bench, args, et)
    clean_text, corr_text = ctx["clean_text"], ctx["corr_text"]
    positions, mapping = ctx["positions"], ctx["mapping"]
    metric, need_hs = ctx["metric"], ctx["need_hs"]
    if not positions:
        raise ValueError("no token-aligned positions between clean and corrupt prompts")
    nh, hd = pc._attn_head_dims(lm.model)
    n_layers = lm.num_layers

    z_clean, mlp_clean, m_clean = capture_clean_all(lm, clean_text, metric, need_hs)
    seqlen = z_clean[0].shape[0]
    corr_z = ha49.capture_z(lm, corr_text, list(range(n_layers)))
    corr_al = ha49.align_z(corr_z, seqlen, mapping, list(range(n_layers)))
    corr_dev = {L: v.to(lm.model.device).view(-1, nh, hd) for L, v in corr_al.items()}

    def clean_fwd():
        tok = lm.tokenizer(clean_text, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
        return lm.model(**tok, output_hidden_states=need_hs, return_dict=True)

    def corr_vecs(L, h):
        return [corr_dev[L][p, h] for p in positions]

    @torch.no_grad()
    def total_effect(L, h):
        with ZHeadPatchMulti(lm.model, L, h, positions, corr_vecs(L, h)):
            return float(metric(clean_fwd()).detach()) - m_clean

    @torch.no_grad()
    def direct_effect(L, h):
        with ExitStack() as s:
            s.enter_context(FreezeAllHeadsExcept(lm.model, z_clean, sender=(L, h, positions, corr_vecs(L, h))))
            s.enter_context(FreezeMLPCapture(lm.model, mlp_clean))
            return float(metric(clean_fwd()).detach()) - m_clean

    @torch.no_grad()
    def edge_mlp(L_S, h_S, L_R, donor="sender"):
        """head sender -> MLP receiver edge. donor='self' => patch receiver with its OWN clean
        value (locality no-op control, must be ~0)."""
        if donor == "self":
            vecs = mlp_clean[L_R][positions]                        # [P, hidden]
        else:
            out = {}
            with ExitStack() as s:
                s.enter_context(FreezeAllHeadsExcept(lm.model, z_clean,
                                 sender=(L_S, h_S, positions, corr_vecs(L_S, h_S))))
                s.enter_context(FreezeMLPCapture(lm.model, mlp_clean,
                                 receiver_capture=(L_R, positions, out)))
                clean_fwd()                                         # run 3a fills out['mlp']
            vecs = out["mlp"]                                       # [P, hidden]
        with MLPOutPatch(lm.model, L_R, positions, vecs):          # run 3b
            return float(metric(clean_fwd()).detach()) - m_clean

    @torch.no_grad()
    def edge_head(L_S, h_S, L_R, h_R):
        """head sender -> head receiver edge (reused for reconstruction only, --recon-full)."""
        out = {}
        with ExitStack() as s:
            s.enter_context(FreezeAllHeadsExcept(lm.model, z_clean,
                             sender=(L_S, h_S, positions, corr_vecs(L_S, h_S)),
                             receiver_capture=(L_R, h_R, positions, out)))
            s.enter_context(FreezeMLPCapture(lm.model, mlp_clean))
            clean_fwd()
        z_R = [out["z"][i] for i in range(len(positions))]
        with ZHeadPatchMulti(lm.model, L_R, h_R, positions, z_R):
            return float(metric(clean_fwd()).detach()) - m_clean

    # ---- candidate senders + receivers ----
    senders = pick_sender_heads(args)
    receivers = [L_R for L_R in pick_receiver_mlps(args, ctx["receiver_max_layer"])]
    if not senders:
        raise SystemExit("no sender heads selected")
    if not receivers:
        raise SystemExit("no receiver MLPs selected")

    TOTAL, DIRECT = {}, {}
    for (L, h) in senders:
        TOTAL[(L, h)] = total_effect(L, h)
        DIRECT[(L, h)] = direct_effect(L, h)

    # ---- candidate head->MLP path matrix (L_R > L_S) + self-donor null per receiver ----
    mlp_edges, self_null = [], {}
    for (L_S, h_S) in senders:
        for L_R in receivers:
            if L_R > L_S:
                e = edge_mlp(L_S, h_S, L_R, donor="sender")
                mlp_edges.append({"L_S": L_S, "h_S": h_S, "L_R": L_R, "edge": round(e, 5)})
    for L_R in receivers:                                            # donor==clean-self, no-op
        self_null[L_R] = round(edge_mlp(receivers[0], 0, L_R, donor="self"), 6)

    # ---- specificity controls ----
    rng = np.random.default_rng(args.seed)
    cand_set = set(senders)
    sender_layers = sorted({L for L, _ in senders})
    band_lo, band_hi = min(sender_layers), max(sender_layers)
    # random senders: heads in the sender band NOT in the candidate set
    pool = [(L, h) for L in range(band_lo, band_hi + 1) for h in range(nh) if (L, h) not in cand_set]
    rng.shuffle(pool)
    rand_senders = pool[: args.rand_senders]
    # random receivers: MLP layers OUTSIDE the write band, still valid (> some sender, <= endpoint)
    rec_set = set(receivers)
    off_band = [L for L in range(band_hi + 1, ctx["receiver_max_layer"] + 1) if L not in rec_set]
    rng.shuffle(off_band)
    rand_receivers = off_band[: args.rand_receivers]
    # matched non-candidate path: a non-candidate head at the SAME layer as each candidate -> cand R
    matched_heads = []
    for (L, h) in senders:
        alt = [hh for hh in range(nh) if (L, hh) not in cand_set]
        if alt:
            matched_heads.append((L, int(rng.choice(alt))))
    matched_heads = sorted(set(matched_heads))[: max(1, args.rand_senders)]

    def edges_for(sender_list, receiver_list):
        out = []
        for (L_S, h_S) in sender_list:
            for L_R in receiver_list:
                if L_R > L_S:
                    out.append({"L_S": L_S, "h_S": h_S, "L_R": L_R,
                                "edge": round(edge_mlp(L_S, h_S, L_R, donor="sender"), 5)})
        return out

    ctrl_rand_sender = edges_for(rand_senders, receivers)
    ctrl_rand_receiver = edges_for(senders, rand_receivers)
    ctrl_matched = edges_for(matched_heads, receivers)

    # ---- reconstruction (optional): DIRECT + mlp-edges + head-edges among the sender set ----
    per_sender, rel_errs = [], []
    head_edges = []
    if args.recon_full:
        for (L_S, h_S) in senders:
            for (L_R, h_R) in senders:
                if L_R > L_S:
                    head_edges.append({"L_S": L_S, "h_S": h_S, "L_R": L_R, "h_R": h_R,
                                       "edge": round(edge_head(L_S, h_S, L_R, h_R), 5)})
    for (L, h) in senders:
        tot, dr = TOTAL[(L, h)], DIRECT[(L, h)]
        mlp_sum = sum(e["edge"] for e in mlp_edges if e["L_S"] == L and e["h_S"] == h)
        head_sum = sum(e["edge"] for e in head_edges if e["L_S"] == L and e["h_S"] == h)
        rec = {"L": L, "h": h, "total": round(tot, 5), "direct": round(dr, 5),
               "mlp_edge_sum": round(mlp_sum, 5)}
        if args.recon_full:
            recon = dr + mlp_sum + head_sum
            rel = abs(tot - recon) / (abs(tot) + 1e-6)
            rel_errs.append(rel)
            rec.update({"head_edge_sum": round(head_sum, 5), "recon": round(recon, 5),
                        "rel_err": round(rel, 4)})
        # concentration: is this sender's MLP-edge mass on a few receivers?
        mags = sorted((abs(e["edge"]) for e in mlp_edges if e["L_S"] == L and e["h_S"] == h), reverse=True)
        tmass = sum(mags)
        rec["top_edge_frac"] = round(mags[0] / tmass, 4) if tmass > 1e-9 else None
        per_sender.append(rec)

    med_rel = float(statistics.median(rel_errs)) if rel_errs else None
    recon_ok = bool(med_rel is not None and med_rel <= args.recon_tol) if args.recon_full else None

    def med_abs(edges):
        v = [abs(e["edge"]) for e in edges]
        return float(statistics.median(v)) if v else None

    cand_med = med_abs(mlp_edges)
    ctrl_med = med_abs(ctrl_rand_sender + ctrl_rand_receiver + ctrl_matched)
    self_max = max((abs(v) for v in self_null.values()), default=0.0)
    strongest = max(mlp_edges, key=lambda e: abs(e["edge"])) if mlp_edges else None
    # sparse if per-sender edge mass concentrates AND candidate edges clear controls + self-null
    top_fracs = [r["top_edge_frac"] for r in per_sender if r["top_edge_frac"] is not None]
    med_top_frac = float(statistics.median(top_fracs)) if top_fracs else None
    specific = bool(cand_med is not None and (ctrl_med is None or cand_med >= 2.0 * (ctrl_med + 1e-9))
                    and cand_med >= 5.0 * (self_max + 1e-9))
    sparse = bool(specific and med_top_frac is not None and med_top_frac >= 0.6)
    if not specific:
        verdict = "NO-PATH (candidate head->MLP edges do not clear controls/self-null)"
    elif sparse:
        verdict = "SPARSE-GRAPH (few receivers carry each sender; edges clear controls)"
    else:
        verdict = "DISTRIBUTED-PATH-MATRIX (edges specific but spread across receivers)"

    return {
        "family": args.family, "endpoint": ctx["endpoint"], "alignment": ctx["diag"],
        "n_layers": n_layers, "n_heads": nh, "m_clean": round(m_clean, 5),
        "senders": [list(x) for x in senders], "receiver_mlps": receivers,
        "per_sender": per_sender, "mlp_edges": mlp_edges, "self_donor_null": self_null,
        "controls": {"rand_senders": [list(x) for x in rand_senders],
                     "rand_receivers": rand_receivers,
                     "matched_heads": [list(x) for x in matched_heads],
                     "rand_sender_edges": ctrl_rand_sender,
                     "rand_receiver_edges": ctrl_rand_receiver,
                     "matched_path_edges": ctrl_matched},
        "recon_full": bool(args.recon_full), "head_edges": head_edges,
        "median_rel_err": (round(med_rel, 4) if med_rel is not None else None),
        "recon_ok": recon_ok, "recon_tol": args.recon_tol,
        "candidate_median_abs_edge": (round(cand_med, 5) if cand_med is not None else None),
        "control_median_abs_edge": (round(ctrl_med, 5) if ctrl_med is not None else None),
        "self_donor_max_abs": round(self_max, 6),
        "median_top_edge_frac": (round(med_top_frac, 4) if med_top_frac is not None else None),
        "specific": specific, "sparse": sparse, "strongest_edge": strongest,
        "verdict": verdict,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=["concept", "refusal"])
    ap.add_argument("--bench", required=True, help="pair_*.json (concept) or beh_*.json (refusal)")
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    # concept endpoint
    ap.add_argument("--readout", default="forced_choice")
    ap.add_argument("--split", default="", help="concept: pair split (default heldout); refusal: item split")
    ap.add_argument("--metric", default="p_concept", choices=["logit_diff", "p_concept"],
                    help="concept endpoint (§8.1 endpoint = p_concept)")
    # refusal endpoint
    ap.add_argument("--refusal-dir", default=os.path.join(DC, "outputs", "refusal_alllayers"))
    ap.add_argument("--refusal-layer", type=int, default=18, help="decision-token refusal readout layer")
    ap.add_argument("--corrupt-cond", default="neutral", choices=["neutral", "direct"])
    ap.add_argument("--item-idx", type=int, default=0, help="refusal: which behavioral item (within split)")
    # senders
    ap.add_argument("--sender-heads", default="", help='explicit "L:h,L:h"; else --from-head-attr')
    ap.add_argument("--from-head-attr", default="")
    ap.add_argument("--lo", type=int, default=7)
    ap.add_argument("--hi", type=int, default=14)
    ap.add_argument("--topn", type=int, default=6)
    # receivers
    ap.add_argument("--receiver-mlps", default="", help='explicit "L,L,L"; else --mlp-lo/--mlp-hi')
    ap.add_argument("--mlp-lo", type=int, default=8)
    ap.add_argument("--mlp-hi", type=int, default=13)
    # controls / recon
    ap.add_argument("--rand-senders", type=int, default=2)
    ap.add_argument("--rand-receivers", type=int, default=2)
    ap.add_argument("--recon-full", action="store_true", help="also compute head-edges for a recon gate")
    ap.add_argument("--recon-tol", type=float, default=0.20)
    ap.add_argument("--enable-thinking", default="default", help="Qwen3 thinking: default|true|false")
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    if args.family == "concept" and not args.split:
        args.split = "heldout"
    if args.family == "refusal" and not args.split:
        args.split = "test"

    dc.set_seed(args.seed)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model)

    tag = args.model.split("/")[-1]; uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase8_hmpath_{args.family}_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    # RUNMETA-first (defensive provenance) ; DONE-last
    try:
        dc.write_runmeta(out_dir, args=vars(args), extra={"phase": "phase8_head_mlp_path_v1",
                         "family": args.family, "model": args.model})
    except Exception:
        pass

    res = run(lm, bench, args)
    res["model"] = args.model
    try:
        res["meta"] = lm.meta()
    except Exception:
        res["meta"] = {}
    json.dump(res, open(os.path.join(out_dir, "phase8_head_mlp_path.json"), "w"), indent=2)

    print(f"[phase8-hmpath:{args.family}] m_clean={res['m_clean']} senders={len(res['senders'])} "
          f"receivers={len(res['receiver_mlps'])} mlp_edges={len(res['mlp_edges'])}")
    print(f"  cand_med_abs_edge={res['candidate_median_abs_edge']} "
          f"ctrl_med_abs_edge={res['control_median_abs_edge']} self_null_max={res['self_donor_max_abs']}")
    print(f"  specific={res['specific']} sparse={res['sparse']} "
          f"median_top_edge_frac={res['median_top_edge_frac']} recon_ok={res['recon_ok']}")
    if res["strongest_edge"]:
        e = res["strongest_edge"]
        print(f"  strongest edge L{e['L_S']}h{e['h_S']} -> MLP L{e['L_R']} = {e['edge']}")
    print(f"  verdict: {res['verdict']}")
    try:
        dc.write_done(out_dir, rows_written=len(res["mlp_edges"]))
    except Exception:
        pass
    print(f"[phase8-hmpath] -> {out_dir}")


if __name__ == "__main__":
    main()
