"""
50_path_patching.py — NEXT6 D4: sender->receiver PATH PATCHING on the per-head z channel.

Tests whether the NEXT5 mid-band heads (L7-14, peak L9) form a DIRECTED sender->receiver circuit
vs merely parallel contributors. Contrast identical to 48/49: clean=DOUBLESPEAK, corrupt=matched
NEUTRAL_CODEWORD, metric M = logit_diff(concept-codeword) at the final position.

LINEARITY LEVER: o_proj(z)=z@W_o is linear and z is the per-head concat, so overwriting the o_proj
INPUT of a layer with cached CLEAN z FREEZES that whole attention sublayer's residual contribution
to its clean value, and swapping ONLY the sender head's block to corrupt injects exactly the
sender's isolated delta with zero leakage. MLPs frozen by overwriting their output with cached clean.

Per sender S=(L_S,h_S):
  TOTAL[S]  = single-head true patch (== 49's true delta; nothing frozen).
  DIRECT[S] = freeze ALL heads+MLPs to clean, set sender=corrupt -> S's direct-to-logits path.
  EDGE[S->R]= path through receiver R=(L_R,h_R), L_R>L_S: run 3a freezes-all-clean, sets sender=
              corrupt, and CAPTURES R's recomputed z (before the freeze-overwrite); run 3b patches
              ONLY R with that captured z and lets everything downstream recompute -> M - m_clean.
Reconstruction: TOTAL[S] ~= DIRECT[S] + sum_R EDGE[S->R] (exact in the linear toy; recon_tol on-model).
Parallel-contributors <=> median(direct_frac=DIRECT/TOTAL) ~1 and edges ~0; directed circuit <=>
some upstream sender has direct_frac << 1 with concentrated edge(s) to mid-band receivers.

Scalars only; no prompt text / completions persisted.

Run (GPU, L40S):
  python 50_path_patching.py --bench data/pair_benchmark/pair_carrot_bomb.json \
      --from-head-attr outputs/head_attr_<...>/head_attribution.json --lo 7 --hi 14 --topn 8
"""
import os, sys, json, time, argparse, importlib.util
from contextlib import ExitStack
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ds_common as dc
import pair_common as pc

_spec = importlib.util.spec_from_file_location("atp48", os.path.join(HERE, "48_attribution_patching.py"))
atp48 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(atp48)
_spec2 = importlib.util.spec_from_file_location("ha49", os.path.join(HERE, "49_head_attribution.py"))
ha49 = importlib.util.module_from_spec(_spec2); _spec2.loader.exec_module(ha49)


class FreezeAllHeadsExcept:
    """o_proj forward_pre_hook on every layer: overwrite ALL heads' z with cached clean z; at the
    sender layer set head h_S at sender positions to corrupt; at the receiver layer CAPTURE head
    h_R's recomputed z at positions BEFORE the overwrite. Freezes every attention sublayer to clean
    except the injected sender delta."""

    def __init__(self, model, z_clean, sender=None, receiver_capture=None):
        self.layers = dc._get_layers(model)
        self.n_heads, self.head_dim = pc._attn_head_dims(model)
        self.z_clean = z_clean                      # {L: [seq, H, hd] on device}
        self.sender = sender                        # (L_S, h_S, positions, corrupt_vecs[P,hd])
        self.receiver = receiver_capture            # (L_R, h_R, positions, out_dict)
        self._handles = []

    def _pre(self, li):
        def f(module, args):
            z = args[0]
            b, seq, hh = z.shape
            zr = z.view(b, seq, self.n_heads, self.head_dim).clone()
            if self.receiver is not None and li == self.receiver[0]:
                _, h_R, pos, out = self.receiver
                out["z"] = zr[0, pos, h_R, :].detach().clone()   # capture recomputed BEFORE freeze
            zr[0, :, :, :] = self.z_clean[li].to(zr.dtype)        # freeze all heads/all positions
            if self.sender is not None and li == self.sender[0]:
                _, h_S, pos, vecs = self.sender
                for i, p in enumerate(pos):
                    zr[0, p, h_S, :] = vecs[i].to(zr.dtype)
            return (zr.view(b, seq, hh),) + tuple(args[1:])
        return f

    def __enter__(self):
        for li, layer in enumerate(self.layers):
            self._handles.append(layer.self_attn.o_proj.register_forward_pre_hook(self._pre(li)))
        return self

    def __exit__(self, *e):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


class FreezeMLP:
    """Overwrite every layer.mlp output with cached clean mlp output (freeze MLP contribution)."""

    def __init__(self, model, mlp_clean):
        self.layers = dc._get_layers(model)
        self.mlp_clean = mlp_clean                  # {L: [seq, hidden] on device}
        self._handles = []

    def _hook(self, li):
        def f(module, inp, out):
            is_t = isinstance(out, tuple)
            h = out[0] if is_t else out
            hc = self.mlp_clean[li].to(h.dtype).unsqueeze(0)      # [1, seq, hidden]
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


class ZHeadPatchMulti:
    """Per-position variant of pc.ZHeadPatch: patch head h with vecs[i] at positions[i]."""

    def __init__(self, model, layer_idx, head, positions, vecs):
        self.o_proj = dc._get_layers(model)[layer_idx].self_attn.o_proj
        self.n_heads, self.head_dim = pc._attn_head_dims(model)
        self.head, self.positions, self.vecs = head, list(positions), vecs
        self._h = None

    def _pre(self, module, args):
        z = args[0]; b, seq, hh = z.shape
        zr = z.view(b, seq, self.n_heads, self.head_dim).clone()
        for i, p in enumerate(self.positions):
            if 0 <= p < seq:
                zr[0, p, self.head, :] = self.vecs[i].to(zr.dtype)
        return (zr.view(b, seq, hh),) + tuple(args[1:])

    def __enter__(self):
        self._h = self.o_proj.register_forward_pre_hook(self._pre); return self

    def __exit__(self, *e):
        if self._h: self._h.remove(); self._h = None
        return False


@torch.no_grad()
def capture_clean_all(lm, text, metric, n_layers):
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
    out = lm.model(**tok, return_dict=True)
    m_clean = float(metric(out).detach())
    for h in handles:
        h.remove()
    dev = lm.model.device
    return ({L: zc[L].to(dev) for L in zc}, {L: mc[L].to(dev) for L in mc}, m_clean)


def run(lm, bench, args):
    pair = bench["pair"]; concept, codeword = pair["concept"], pair["codeword"]
    nh, hd = pc._attn_head_dims(lm.model)
    clean_row, corr_row = atp48._select_pair_rows(bench, args.readout, args.split)
    clean_text = dc.apply_template(lm.tokenizer, clean_row["prompt"])
    corr_text = dc.apply_template(lm.tokenizer, corr_row["prompt"])
    n_layers = lm.num_layers
    positions, mapping, diag = atp48.build_alignment(lm, clean_text, corr_text, codeword)
    metric = atp48.make_metric(lm, concept, codeword, args.metric)

    z_clean, mlp_clean, m_clean = capture_clean_all(lm, clean_text, metric, n_layers)
    corr_z = ha49.capture_z(lm, corr_text, list(range(n_layers)))
    seqlen = z_clean[0].shape[0]
    corr_al = ha49.align_z(corr_z, seqlen, mapping, list(range(n_layers)))     # {L: [seq, hidden]}
    corr_dev = {L: v.to(lm.model.device).view(-1, nh, hd) for L, v in corr_al.items()}

    def clean_fwd():
        tok = lm.tokenizer(clean_text, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
        return lm.model(**tok, return_dict=True)

    # --- select heads: from head_attribution.json (top-N by sum|AtP| in [lo,hi]) or --heads ---
    if args.heads:
        heads = [tuple(int(x) for x in hs.split(":")) for hs in args.heads.split(",") if hs.strip()]
    else:
        ha = json.load(open(args.from_head_attr))
        cells = [(int(h["layer"]), int(h["head"]), h["sum_abs_atp"]) for h in ha["top_heads"]
                 if args.lo <= int(h["layer"]) <= args.hi]
        cells.sort(key=lambda c: c[2], reverse=True)
        heads = [(L, h) for L, h, _ in cells[:args.topn]]
    heads = sorted(set(heads))

    def corr_vecs(L, h):
        return [corr_dev[L][p, h] for p in positions]

    @torch.no_grad()
    def total_effect(L, h):
        # true single-head patch, nothing frozen (== 49's true delta), per-position
        with ZHeadPatchMulti(lm.model, L, h, positions, corr_vecs(L, h)):
            return float(metric(clean_fwd()).detach()) - m_clean

    @torch.no_grad()
    def direct_effect(L, h):
        with ExitStack() as s:
            s.enter_context(FreezeAllHeadsExcept(lm.model, z_clean, sender=(L, h, positions, corr_vecs(L, h))))
            s.enter_context(FreezeMLP(lm.model, mlp_clean))
            return float(metric(clean_fwd()).detach()) - m_clean

    @torch.no_grad()
    def edge_effect(L_S, h_S, L_R, h_R):
        out = {}
        with ExitStack() as s:
            s.enter_context(FreezeAllHeadsExcept(lm.model, z_clean,
                             sender=(L_S, h_S, positions, corr_vecs(L_S, h_S)),
                             receiver_capture=(L_R, h_R, positions, out)))
            s.enter_context(FreezeMLP(lm.model, mlp_clean))
            clean_fwd()                                     # run 3a: fills out['z'] = [P, hd]
        z_R = [out["z"][i] for i in range(len(positions))]
        with ZHeadPatchMulti(lm.model, L_R, h_R, positions, z_R):
            return float(metric(clean_fwd()).detach()) - m_clean

    TOTAL, DIRECT, EDGES = {}, {}, []
    for (L, h) in heads:
        TOTAL[(L, h)] = total_effect(L, h)
        DIRECT[(L, h)] = direct_effect(L, h)
    for (L_S, h_S) in heads:
        for (L_R, h_R) in heads:
            if L_R > L_S:
                EDGES.append({"L_S": L_S, "h_S": h_S, "L_R": L_R, "h_R": h_R,
                              "edge": round(edge_effect(L_S, h_S, L_R, h_R), 5)})

    # reconstruction + science
    rel_errs, direct_fracs, per_sender = [], [], []
    for (L, h) in heads:
        tot, dr = TOTAL[(L, h)], DIRECT[(L, h)]
        esum = sum(e["edge"] for e in EDGES if e["L_S"] == L and e["h_S"] == h)
        recon = dr + esum
        rel = abs(tot - recon) / (abs(tot) + 1e-6)
        rel_errs.append(rel)
        frac = (dr / tot) if abs(tot) > 1e-4 else None
        if frac is not None:
            direct_fracs.append(frac)
        per_sender.append({"L": L, "h": h, "total": round(tot, 5), "direct": round(dr, 5),
                           "edge_sum": round(esum, 5), "recon": round(recon, 5),
                           "rel_err": round(rel, 4), "direct_frac": (round(frac, 4) if frac is not None else None)})
    import statistics
    med_rel = float(statistics.median(rel_errs)) if rel_errs else None
    recon_ok = bool(med_rel is not None and med_rel <= args.recon_tol)
    parallel_score = float(statistics.median(direct_fracs)) if direct_fracs else None
    strongest = max(EDGES, key=lambda e: abs(e["edge"])) if EDGES else None

    return {"concept": concept, "codeword": codeword, "readout": args.readout, "split": args.split,
            "metric": args.metric, "n_layers": n_layers, "n_heads": nh, "alignment": diag,
            "m_clean": round(m_clean, 5), "heads": [list(x) for x in heads],
            "per_sender": per_sender, "edges": EDGES,
            "median_rel_err": (round(med_rel, 4) if med_rel is not None else None),
            "recon_ok": recon_ok, "recon_tol": args.recon_tol,
            "parallel_score_median_direct_frac": (round(parallel_score, 4) if parallel_score is not None else None),
            "strongest_edge": strongest,
            "verdict": ("PARALLEL (direct_frac~1, edges small)" if (parallel_score is not None and parallel_score >= 0.85)
                        else "DIRECTED-evidence (some sender routes through receivers)" if recon_ok
                        else "UNTRUSTWORTHY (recon gate failed; report TOTAL/DIRECT only)")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--readout", default="forced_choice")
    ap.add_argument("--split", default="heldout")
    ap.add_argument("--metric", default="logit_diff", choices=["logit_diff", "p_concept"])
    ap.add_argument("--heads", default="", help='explicit "L:h,L:h"; else use --from-head-attr')
    ap.add_argument("--from-head-attr", default="")
    ap.add_argument("--lo", type=int, default=7)
    ap.add_argument("--hi", type=int, default=14)
    ap.add_argument("--topn", type=int, default=8)
    ap.add_argument("--recon-tol", type=float, default=0.15)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    if not args.heads and not args.from_head_attr:
        raise SystemExit("provide --heads or --from-head-attr")

    dc.set_seed(args.seed)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model)
    res = run(lm, bench, args); res["model"] = args.model; res["meta"] = lm.meta()
    tag = args.model.split("/")[-1]; uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"path_patch_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    json.dump(res, open(os.path.join(out_dir, "path_patching.json"), "w"), indent=2)
    print(f"[path_patch] m_clean={res['m_clean']} heads={len(res['heads'])} edges={len(res['edges'])}")
    print(f"  median_rel_err={res['median_rel_err']} recon_ok={res['recon_ok']} "
          f"parallel_score={res['parallel_score_median_direct_frac']}")
    print(f"  verdict: {res['verdict']}")
    if res["strongest_edge"]:
        e = res["strongest_edge"]; print(f"  strongest edge L{e['L_S']}h{e['h_S']}->L{e['L_R']}h{e['h_R']} = {e['edge']}")
    print(f"[path_patch] -> {out_dir}")


if __name__ == "__main__":
    main()
