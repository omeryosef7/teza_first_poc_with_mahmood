#!/usr/bin/env python3
"""ASYMMETRY SPRINT — PHASE 1: token -> activation reachability geometry (plan §5).

Central question: is the causally-validated refusal direction actually ACCESSIBLE from
suffix-token perturbations, or does it lie outside the subspace suffix tokens can control?

Three measurements at one base point (a doublespeak prompt + a 16-token suffix, built with
the GCG span builder so placement/tokenization are byte-identical to the optimizer):

  §5.2 JACOBIAN    For target direction v and target residual h (row `hs_row`, position p):
                   g(v) = d<h, v> / dE_suffix  in R^{suffix_len x d_model}  (= J^T v).
                   Report ||J^T v|| for v in {refusal, concept, N norm-matched randoms,
                   foreign-mechanism}, and the per-suffix-position profile ||g_j(v)||.

  §5.3 FINITE-DIFF For real vocabulary substitutions at suffix position j:
                   predicted  D<h,v> = <g_j(v), e_new - e_old>
                   actual     D<h,v> = <h(sub) - h(base), v>
                   -> Pearson r, OLS slope, sign agreement. GATE B.

  §5.4 SUBSPACE    Accumulate the second-moment matrix C = sum_s dh_s dh_s^T over those
                   real substitutions -> eigenvectors of C are the right singular vectors
                   of the Dh matrix -> rank-r basis U_r of the EMPIRICAL LOCAL
                   TOKEN-REACHABLE SUBSPACE. R(v) = ||U_r^T v||^2 / ||v||^2.
                   Null for an isotropic unit v is r / d_model.

  §5.5 COHERENCE   Per-prompt g(v) saved to grads.npz so a CPU analysis can measure
                   cross-prompt cosine / eigenspectrum (shared vs prompt-specific route).

POSITION CONVENTIONS (docs/ASYMMETRY_SPRINT_EXECUTION_LOG.md E0.3 — load-bearing):
  * `decision`    = last token of the templated prompt (after the assistant header). Where
                    the refusal direction was FITTED (build_refusal_direction_llama.py:83)
                    and where the mech-validity readout measures it. PRIMARY.
  * `last_suffix` = last suffix token, inside the user turn. What the GCG objective reads
                    (gcg_optimizer.py:687). SECONDARY — quantifies the fit/use mismatch (D2).
  * Layer off-by-one: a direction file labelled L{k} was fitted at hidden_states[k+1]. This
                    script takes FIT layers on the CLI and adds +1 internally; both numbers
                    are asserted and written to meta.json.

SAFETY: emits scalars / tensors only. Never writes prompt or suffix text.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # $DC
ROOT = os.path.dirname(HERE)                                          # $ROOT
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402
import torch  # noqa: E402

import ds_common as dc  # noqa: E402
import pair_common as pc  # noqa: E402
from poc_stage_gcg_early.suffix_token_manager import (  # noqa: E402
    build_suffix_spans,
    make_init_suffix,
)


# --------------------------------------------------------------------------- #
# Directions
# --------------------------------------------------------------------------- #

def load_unit(path):
    v = torch.load(path, map_location="cpu", weights_only=True).float().flatten()
    return v / (v.norm() + 1e-8)


def build_directions(args, hidden_size, device):
    """-> {hs_row: {'names': [...], 'kinds': [...], 'V': Tensor[n_dirs, d] (unit norm)}}

    All directions are UNIT norm so ||J^T v|| is directly comparable (plan §3.8).
    """
    acc = {}

    def add(row, name, kind, vec):
        d = acc.setdefault(row, {"names": [], "kinds": [], "vecs": []})
        d["names"].append(name)
        d["kinds"].append(kind)
        d["vecs"].append(vec)

    for k in [int(x) for x in args.refusal_fit_layers.split(",") if x != ""]:
        p = os.path.join(args.refusal_dir, f"refusal_direction_llama_L{k}.pt")
        if not os.path.exists(p):
            raise FileNotFoundError(f"refusal direction not found: {p}")
        v = load_unit(p)
        assert v.numel() == hidden_size, f"refusal L{k} dim {v.numel()} != {hidden_size}"
        add(k + 1, f"refusal_L{k}", "mechanism", v)

    if args.concept_npz and os.path.exists(args.concept_npz):
        cnpz = np.load(args.concept_npz)["concept"]
        for k in [int(x) for x in args.concept_fit_layers.split(",") if x != ""]:
            v = torch.tensor(np.asarray(cnpz[k]), dtype=torch.float32).flatten()
            assert v.numel() == hidden_size, f"concept L{k} dim {v.numel()} != {hidden_size}"
            add(k + 1, f"concept_L{k}", "mechanism", v / (v.norm() + 1e-8))

    unit = torch.ones(hidden_size) / float(hidden_size) ** 0.5
    for row in list(acc.keys()):
        R = pc.norm_matched_random(unit, args.n_random, seed=args.random_seed + row)
        for i in range(args.n_random):
            add(row, f"random{i:03d}", "random", R[i])

    if args.cross_mechanism:
        base_rows = sorted(acc.keys())
        snapshot = {r: [(n, k, v) for n, k, v in
                        zip(acc[r]["names"], acc[r]["kinds"], acc[r]["vecs"])
                        if k == "mechanism"] for r in base_rows}
        for row in base_rows:
            for other in base_rows:
                if other == row:
                    continue
                for nm, _, vv in snapshot[other]:
                    add(row, f"foreign::{nm}", "foreign", vv)

    out = {}
    for row, d in acc.items():
        V = torch.stack(d["vecs"]).to(device=device, dtype=torch.float32)
        V = V / (V.norm(dim=1, keepdim=True) + 1e-8)
        out[row] = {"names": d["names"], "kinds": d["kinds"], "V": V}
    return out


# --------------------------------------------------------------------------- #
# Base point (reuses the GCG span builder verbatim)
# --------------------------------------------------------------------------- #

def make_base(tokenizer, item, suffix_str, suffix_ids, placement, model_family,
              enable_thinking):
    """Prompt-only ids + suffix span + the two target positions.

    The teacher-forced target continuation is dropped: it lies AFTER every position we
    read and causal attention makes it irrelevant there, so `decision` == last index.
    """
    spans = build_suffix_spans(
        tokenizer, model_family, enable_thinking,
        item["instruction"], suffix_str, item["safe_target_prefix"],
        suffix_ids_override=suffix_ids, suffix_placement=placement,
    )
    ids = spans.input_ids[: spans.target_slice.start].clone()
    sl = spans.suffix_slice
    assert sl.stop <= ids.numel(), "suffix span falls outside the prompt-only ids"
    assert ids[sl].tolist() == list(suffix_ids), "suffix ids not where build_suffix_spans said"
    return ids, sl, {"decision": ids.numel() - 1, "last_suffix": sl.stop - 1}


# --------------------------------------------------------------------------- #
# §5.2 Jacobian
# --------------------------------------------------------------------------- #

def jacobian_for_prompt(model, embed_w, ids, suffix_slice, positions, rows, dirs,
                        device, grad_chunk=16):
    """One forward; then J^T v for every direction via chunked batched autograd.

    -> {(pos_name, hs_row): {'g': Tensor[n_dirs, suffix_len, d] cpu fp32,
                             'norm': [n_dirs], 'pos_norm': [n_dirs, suffix_len],
                             'base_proj': [n_dirs], 'h_norm': float}}
    """
    ids = ids.to(device)
    with torch.no_grad():
        full = embed_w[ids].unsqueeze(0)                              # [1, seq, d]
    suf = full[:, suffix_slice, :].clone().detach().to(torch.float32).requires_grad_(True)
    combined = torch.cat([
        full[:, : suffix_slice.start, :].to(torch.float32),
        suf,
        full[:, suffix_slice.stop:, :].to(torch.float32),
    ], dim=1).to(embed_w.dtype)

    out = model(inputs_embeds=combined, output_hidden_states=True)
    hs = out.hidden_states

    res = {}
    for pos_name, p in positions.items():
        for row in rows:
            h = hs[row][0, p, :].to(torch.float32)                    # in graph
            V = dirs[row]["V"]                                        # [n_dirs, d] unit
            with torch.no_grad():
                base_proj = (V @ h.detach()).cpu().numpy()
                h_norm = float(h.detach().norm())
            gs = []
            for s in range(0, V.shape[0], grad_chunk):
                chunk = V[s: s + grad_chunk]
                try:
                    (gc,) = torch.autograd.grad(
                        h, suf, grad_outputs=chunk, retain_graph=True,
                        is_grads_batched=True)                        # [c, 1, L, d]
                    gs.append(gc.squeeze(1).detach().to(torch.float32).cpu())
                except Exception:                                     # vmap fallback
                    for i in range(chunk.shape[0]):
                        (gi,) = torch.autograd.grad(
                            (h * chunk[i]).sum(), suf, retain_graph=True)
                        gs.append(gi.squeeze(0).detach().to(torch.float32).cpu()[None])
            g = torch.cat(gs, dim=0)                                  # [n_dirs, L, d]
            res[(pos_name, row)] = {
                "g": g,
                "norm": g.flatten(1).norm(dim=1).numpy(),
                "pos_norm": g.norm(dim=2).numpy(),
                "base_proj": base_proj,
                "h_norm": h_norm,
            }
    del out, hs, combined, suf, full
    return res


# --------------------------------------------------------------------------- #
# §5.3 / §5.4 real token substitutions
# --------------------------------------------------------------------------- #

def candidate_token_pool(tokenizer, n, seed):
    """Fixed pool of 'ordinary' vocabulary tokens (no specials, ascii-renderable)."""
    rng = np.random.default_rng(seed)
    special = set(int(x) for x in (tokenizer.all_special_ids or []))
    ok = []
    for tid in range(int(tokenizer.vocab_size)):
        if tid in special:
            continue
        s = tokenizer.convert_ids_to_tokens(tid)
        if not s:
            continue
        t = s.replace("Ġ", " ").replace("Ċ", "\n")
        if not t.strip():
            continue
        try:
            t.encode("ascii")
        except UnicodeEncodeError:
            continue
        ok.append(tid)
    ok = np.array(ok)
    return sorted(int(x) for x in ok[rng.choice(len(ok), size=min(n, len(ok)), replace=False)])


@torch.no_grad()
def substitution_pass(model, ids, suffix_slice, positions, rows, sub_positions,
                      cand_tokens, device, batch_size=16):
    """Yield (j, tok_old, tok_new, {(pos,row): dh_gpu[d]}) for every real substitution."""
    ids = ids.to(device)
    o0 = model(input_ids=ids.unsqueeze(0), output_hidden_states=True)
    base = {(pn, r): o0.hidden_states[r][0, p, :].to(torch.float32).clone()
            for pn, p in positions.items() for r in rows}
    del o0

    jobs = [(j, t) for j in sub_positions for t in cand_tokens
            if t != int(ids[suffix_slice.start + j])]
    for s in range(0, len(jobs), batch_size):
        chunk = jobs[s: s + batch_size]
        batch = ids.unsqueeze(0).repeat(len(chunk), 1)
        for bi, (j, t) in enumerate(chunk):
            batch[bi, suffix_slice.start + j] = t
        o = model(input_ids=batch, output_hidden_states=True)
        for bi, (j, t) in enumerate(chunk):
            dh = {(pn, r): o.hidden_states[r][bi, p, :].to(torch.float32) - base[(pn, r)]
                  for pn, p in positions.items() for r in rows}
            yield j, int(ids[suffix_slice.start + j]), int(t), dh
        del o
    del base


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--model-family", default="llama")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="train")
    ap.add_argument("--n-max", type=int, default=40, help=">=20 required by plan §3.4")
    ap.add_argument("--suffix-length", type=int, default=16)
    ap.add_argument("--suffix-placement", default="user")
    ap.add_argument("--enable-thinking", default="false")
    ap.add_argument("--refusal-dir", default=os.path.join(HERE, "outputs/refusal_alllayers"))
    ap.add_argument("--refusal-fit-layers", default="18")
    ap.add_argument("--concept-npz",
                    default=os.path.join(HERE, "outputs/unified_directions/clearharm.npz"))
    ap.add_argument("--concept-fit-layers", default="9")
    ap.add_argument("--n-random", type=int, default=100, help="plan §3.8: >=50, prefer 100")
    ap.add_argument("--random-seed", type=int, default=42)
    ap.add_argument("--cross-mechanism", action="store_true", default=True)
    ap.add_argument("--no-cross-mechanism", dest="cross_mechanism", action="store_false")
    ap.add_argument("--quantize", default=None)
    ap.add_argument("--grad-chunk", type=int, default=16)
    ap.add_argument("--do-subs", action="store_true", default=True)
    ap.add_argument("--no-subs", dest="do_subs", action="store_false")
    ap.add_argument("--n-sub-tokens", type=int, default=24)
    ap.add_argument("--sub-batch", type=int, default=16)
    ap.add_argument("--fd-random-stride", type=int, default=10,
                    help="keep every Nth random direction in the FD arrays")
    ap.add_argument("--save-grads", action="store_true", default=True)
    ap.add_argument("--n-grad-random", type=int, default=8)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    if args.smoke:
        args.n_max, args.n_random, args.n_sub_tokens = 2, 4, 3

    t0 = time.time()
    os.makedirs(args.out_dir, exist_ok=True)
    dc.set_seed(args.random_seed)
    enable_thinking = dc.parse_enable_thinking(args.enable_thinking)

    lm = dc.load_model(args.model, quantize=args.quantize)
    model, tokenizer = lm.model, lm.tokenizer
    device = next(model.parameters()).device
    embed_w = model.get_input_embeddings().weight
    d_model = lm.hidden_size

    fit_ref = [int(x) for x in args.refusal_fit_layers.split(",") if x != ""]
    fit_con = ([int(x) for x in args.concept_fit_layers.split(",") if x != ""]
               if (args.concept_npz and os.path.exists(args.concept_npz)) else [])
    rows = sorted({k + 1 for k in fit_ref} | {k + 1 for k in fit_con})
    for r in rows:
        assert 1 <= r <= lm.num_layers, f"hs row {r} out of range for {lm.num_layers} layers"
    print(f"[cfg] fit_layers refusal={fit_ref} concept={fit_con} -> "
          f"hidden_states_index rows={rows}  (+1 off-by-one applied HERE)", flush=True)

    dirs = build_directions(args, d_model, device)
    for r in rows:
        assert r in dirs, f"no directions for hs row {r}"
        kinds = dirs[r]["kinds"]
        print(f"[dirs] hs_row={r} n={len(kinds)} "
              f"{ {k: kinds.count(k) for k in sorted(set(kinds))} }", flush=True)

    suffix_str, suffix_ids = make_init_suffix(args.suffix_length, tokenizer)
    assert len(suffix_ids) == args.suffix_length, \
        f"init suffix produced {len(suffix_ids)} tokens, want {args.suffix_length}"

    items = [json.loads(l) for l in open(args.manifest)]
    items = [it for it in items if it.get("split") == args.split]
    seen, uniq = set(), []
    for it in items:                                   # plan §3.4: unique examples only
        if it["task_id"] in seen:
            continue
        seen.add(it["task_id"])
        uniq.append(it)
    items = uniq[: args.n_max]
    assert len(items) >= (2 if args.smoke else 20), \
        f"plan §3.4 requires >=20 unique examples, got {len(items)}"
    print(f"[data] split={args.split} n_unique={len(items)}", flush=True)

    cand_tokens = candidate_token_pool(tokenizer, args.n_sub_tokens, args.random_seed)
    cells = [(pn, r) for pn in ("decision", "last_suffix") for r in rows]

    # second-moment accumulators for the empirical token-reachable subspace (§5.4)
    C = {c: torch.zeros(d_model, d_model, dtype=torch.float32, device=device) for c in cells}
    n_sub = {c: 0 for c in cells}
    per_prompt_spec = {c: [] for c in cells}

    # FD arrays, per cell: which direction indices we keep
    fd_keep = {}
    for r in rows:
        kinds = dirs[r]["kinds"]
        keep = [i for i, k in enumerate(kinds) if k in ("mechanism", "foreign")]
        keep += [i for i, k in enumerate(kinds) if k == "random"][:: args.fd_random_stride]
        fd_keep[r] = sorted(set(keep))
    fd = {c: {"pred": [], "actual": [], "j": [], "prompt": []} for c in cells}

    jac_rows = []
    grad_store = {}

    for i, it in enumerate(items):
        ids, sl, positions = make_base(tokenizer, it, suffix_str, suffix_ids,
                                       args.suffix_placement, args.model_family,
                                       enable_thinking)
        if i == 0:
            print(f"[base] seq_len={ids.numel()} suffix_slice=({sl.start},{sl.stop}) "
                  f"positions={positions}", flush=True)

        J = jacobian_for_prompt(model, embed_w, ids, sl, positions, rows, dirs, device,
                                grad_chunk=args.grad_chunk)

        for (pos_name, row), d in J.items():
            names, kinds = dirs[row]["names"], dirs[row]["kinds"]
            for k, nm in enumerate(names):
                jac_rows.append({
                    "task_id": it["task_id"], "pos": pos_name, "hs_row": row,
                    "dir": nm, "kind": kinds[k],
                    "grad_norm": float(d["norm"][k]),
                    "base_proj": float(d["base_proj"][k]),
                    "h_norm": d["h_norm"],
                    "pos_profile": [float(x) for x in d["pos_norm"][k]],
                })
            if args.save_grads:
                keep = [k for k, kd in enumerate(kinds) if kd in ("mechanism", "foreign")]
                keep += [k for k, kd in enumerate(kinds) if kd == "random"][: args.n_grad_random]
                grad_store[f"G|{it['task_id']}|{pos_name}|hs{row}"] = \
                    d["g"][keep].numpy().astype(np.float16)
                grad_store[f"N|{pos_name}|hs{row}"] = np.array([names[k] for k in keep])

        if args.do_subs:
            blocks = {c: [] for c in cells}
            emb_cache = {}
            for j, t_old, t_new, dh in substitution_pass(
                    model, ids, sl, positions, rows, list(range(args.suffix_length)),
                    cand_tokens, device, args.sub_batch):
                key = (t_old, t_new)
                if key not in emb_cache:
                    with torch.no_grad():
                        emb_cache[key] = (embed_w[t_new].to(torch.float32)
                                          - embed_w[t_old].to(torch.float32)).cpu()
                de = emb_cache[key]                                    # [d] cpu fp32
                for c in cells:
                    v = dh[c]                                          # [d] gpu fp32
                    blocks[c].append(v)
                    keep = fd_keep[c[1]]
                    with torch.no_grad():
                        actual = (dirs[c[1]]["V"][keep] @ v).cpu().numpy()
                    pred = (J[c]["g"][keep, j, :] @ de).numpy()
                    fd[c]["pred"].append(pred)
                    fd[c]["actual"].append(actual)
                    fd[c]["j"].append(j)
                    fd[c]["prompt"].append(i)
                if len(blocks[cells[0]]) >= 256:
                    for c in cells:
                        B = torch.stack(blocks[c])                     # [b, d]
                        C[c] += B.T @ B
                        n_sub[c] += B.shape[0]
                        per_prompt_spec[c].append(
                            torch.linalg.svdvals(B).cpu().numpy()[:32])
                        blocks[c] = []
            for c in cells:
                if blocks[c]:
                    B = torch.stack(blocks[c])
                    C[c] += B.T @ B
                    n_sub[c] += B.shape[0]
                    per_prompt_spec[c].append(torch.linalg.svdvals(B).cpu().numpy()[:32])
                    blocks[c] = []
            del blocks, emb_cache

        del J
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"[prompt {i+1}/{len(items)}] {it['task_id']} ({time.time()-t0:.0f}s)", flush=True)

    # ------------------------- §5.4 subspace -------------------------
    subspace = {}
    for c in cells:
        if n_sub[c] < 8:
            continue
        pos_name, row = c
        evals, evecs = torch.linalg.eigh(C[c].double())                # ascending
        evals = torch.flip(evals, [0]).clamp(min=0)
        evecs = torch.flip(evecs, [1])                                 # columns = basis
        sv = torch.sqrt(evals)
        total = float(evals.sum()) or 1.0
        V = dirs[row]["V"].to(torch.float64)                           # [n_dirs, d] unit
        # coords of each direction in the eigenbasis, cumulative from the top
        coord2 = (V @ evecs) ** 2                                      # [n_dirs, d]
        cum = torch.cumsum(coord2, dim=1)
        entry = {"n_substitutions": int(n_sub[c]),
                 "singular_values": [float(x) for x in sv[:128]],
                 "explained_variance_ratio": [float(x) for x in (evals[:128] / total)],
                 "R": {}}
        for r_rank in [1, 2, 4, 8, 16, 32, 64, 128, 256]:
            if r_rank > d_model:
                continue
            col = cum[:, r_rank - 1]
            entry["R"][str(r_rank)] = {nm: float(col[k])
                                       for k, nm in enumerate(dirs[row]["names"])}
            entry["R"][str(r_rank)]["__null_isotropic__"] = r_rank / d_model
        subspace[f"{pos_name}|hs{row}"] = entry
        del evals, evecs, coord2, cum

    # ------------------------- write -------------------------
    meta = {
        "phase": "P1_reachability", "model": args.model, "split": args.split,
        "n_items": len(items), "task_ids": [it["task_id"] for it in items],
        "suffix_length": args.suffix_length, "suffix_placement": args.suffix_placement,
        "fit_layers_refusal": fit_ref, "fit_layers_concept": fit_con,
        "hidden_states_index_rows": rows,
        "off_by_one_note": "direction file L{k} fitted at hidden_states[k+1]; +1 applied here",
        "n_random": args.n_random, "random_seed": args.random_seed,
        "n_sub_tokens": args.n_sub_tokens, "candidate_token_ids": cand_tokens,
        "n_substitutions_per_cell": {f"{p}|hs{r}": int(n_sub[(p, r)]) for p, r in cells},
        "positions": {
            "decision": "last token of templated prompt (refusal fit + readout position)",
            "last_suffix": "last suffix token (the position the GCG objective reads)"},
        "quantize": args.quantize, "elapsed_s": time.time() - t0,
    }
    meta.update(lm.meta())
    json.dump(meta, open(os.path.join(args.out_dir, "meta.json"), "w"), indent=2)

    with open(os.path.join(args.out_dir, "jacobian.jsonl"), "w") as fh:
        for r in jac_rows:
            fh.write(json.dumps(r) + "\n")
    json.dump(subspace, open(os.path.join(args.out_dir, "subspace.json"), "w"), indent=2)

    fd_out = {}
    for c in cells:
        if not fd[c]["pred"]:
            continue
        tag = f"{c[0]}|hs{c[1]}"
        fd_out[f"pred|{tag}"] = np.stack(fd[c]["pred"]).astype(np.float32)
        fd_out[f"actual|{tag}"] = np.stack(fd[c]["actual"]).astype(np.float32)
        fd_out[f"j|{tag}"] = np.array(fd[c]["j"], dtype=np.int32)
        fd_out[f"prompt|{tag}"] = np.array(fd[c]["prompt"], dtype=np.int32)
        fd_out[f"names|{tag}"] = np.array([dirs[c[1]]["names"][k] for k in fd_keep[c[1]]])
        fd_out[f"kinds|{tag}"] = np.array([dirs[c[1]]["kinds"][k] for k in fd_keep[c[1]]])
    if fd_out:
        np.savez_compressed(os.path.join(args.out_dir, "fd.npz"), **fd_out)
    if grad_store:
        np.savez_compressed(os.path.join(args.out_dir, "grads.npz"), **grad_store)
    if any(per_prompt_spec[c] for c in cells):
        np.savez_compressed(
            os.path.join(args.out_dir, "block_spectra.npz"),
            **{f"{p}|hs{r}": np.stack(per_prompt_spec[(p, r)])
               for p, r in cells if per_prompt_spec[(p, r)]})

    dc.write_runmeta(args.out_dir, args=args, extra=meta)
    dc.write_done(args.out_dir, rows_written=len(jac_rows))
    print(f"[out] {args.out_dir}  jac={len(jac_rows)} subspace_cells={len(subspace)} "
          f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
