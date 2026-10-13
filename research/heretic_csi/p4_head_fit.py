#!/usr/bin/env python3
"""P4: HEAD-RESTRICTED weight operator (fit side, CPU). Additive module: reuses p2b_fit.load_pairs/build and
p2b_operator.fit_factored/gap_closure UNCHANGED, with F2's frozen objective (freeze_pooled.json: mse, steer 0.3).

Llama o_proj input = concatenation of the 32 QUERY-head outputs: LlamaAttention computes
attn_output [b, heads, q, head_dim] -> .transpose(1, 2) -> .reshape(*input_shape, -1) -> o_proj, so head h owns
input columns [128h, 128h+128). GQA (repeat_kv, 4 query heads per KV head) acts before this and does not change
the column layout. The CSI knockout's `heads=` index is the same query-head index (ScopedAttentionKnockout uses
num_attention_heads). A head-restricted operator is ΔW = B @ A with A zero outside the chosen heads' columns:
implemented by fitting on the restricted input columns and embedding A back into 4096 columns with zeros.

Variants per rank r (all on o_proj/down_proj of layers 6-18 = the P2b fit layers; heads tied across layers like
the CSI head knockout):
  TOP8      o_proj, A restricted to the inherited 8-head set [19,17,23,6,13,2,24,28] (D32, basket)
  RH8_j     o_proj, A restricted to a seeded random 8-head set drawn from the 24 NON-TOP8 heads (disjoint),
            fitted with the same objective, then RESCALED per module to TOP8's Frobenius norm (fitted, norm-,
            rank-, layer-, #param-matched control family); raw norms recorded
  FULLO     o_proj, all 32 heads
  MLP       down_proj only
  ATTNMLP   o_proj + down_proj (refit here so all variants share the identical fit procedure)
  H2        o_proj, head 2 only (D34/D36; descriptive)
  CELL_L10H2  o_proj of layer 10 only, head 2 only (D36 cell; descriptive)
Fitting-side diagnostics only (in-sample gap closure, and 5-fold domain-grouped TRAIN CV for TOP8 vs the first
--cv-nrh RH8 sets). y_install is never read here.
Output: <out-dir>/factors_p4_<cw>_r<r>.pt in F2's factors format ({"operators": {KEY: {"factors", "meta"}}}),
so p2b_runner's `op:<file>:<KEY>` OPSPEC applies them unchanged; plus p4_fit_<cw>.json.
"""
import argparse, hashlib, json, os, random, sys, time
import torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_operator as po   # noqa: E402
import p2b_fit as pf        # noqa: E402

TOP8 = [19, 17, 23, 6, 13, 2, 24, 28]
HD, NH = 128, 32
NON_TOP8 = [h for h in range(NH) if h not in TOP8]


def cols(heads):
    return torch.cat([torch.arange(h * HD, (h + 1) * HD) for h in sorted(heads)])


def restrict(m: po.PairedIO, c):
    return po.PairedIO(m.name, m.s_in[:, c], m.s_out, m.t_in[:, c], m.t_out, m.p_in[:, c])


def embed(fac, c, full_in):
    out = {}
    for n, (A, B) in fac.items():
        Af = torch.zeros(A.shape[0], full_in, dtype=A.dtype)
        Af[:, c] = A
        out[n] = (Af, B)
    return out


def fit_variant(mods, cfg, heads=None):
    """mods: PairedIO list; heads: None (all columns) or list of query heads (o_proj modules only)."""
    if heads is None:
        return po.fit_factored(mods, cfg)
    c = cols(heads)
    fac = po.fit_factored([restrict(m, c) for m in mods], cfg)
    return embed(fac, c, mods[0].s_in.shape[1])


def gc_all(all_mods, fac):
    """gap closure pooled over ALL 26 modules (unedited modules contribute their full gap)."""
    num = den = dmg = 0.0
    for m in all_mods:
        s_in, s_out, t_out, p_in = m.s_in.float(), m.s_out.float(), m.t_out.float(), m.p_in.float()
        g = float(((s_out - t_out) ** 2).sum()); den += g
        if m.name in fac:
            A, B = (x.float() for x in fac[m.name])
            num += float(((s_out + (s_in @ A.t()) @ B.t() - t_out) ** 2).sum())
            dmg += float((((p_in @ A.t()) @ B.t()) ** 2).sum()) * (s_in.shape[0] / max(1, p_in.shape[0]))
        else:
            num += g
    return {"gap_closure_all26": 1 - num / den, "preserve_damage_all26": dmg / den, "net_all26": (1 - num / den) - dmg / den}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--ranks", default="1,4")
    ap.add_argument("--n-rh8", type=int, default=60)
    ap.add_argument("--cv-nrh", type=int, default=20)
    ap.add_argument("--out-dir", default=os.path.join(REPO, "outputs/heretic_csi/p2b/prod/p4"))
    ap.add_argument("--n-steps", type=int, default=15)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    fz = json.load(open(os.path.join(REPO, "outputs/heretic_csi/p2b/prod/fac/freeze_pooled.json")))["frozen"]
    obj, w = fz.split(":"); w = float(w)
    cap = os.path.join(REPO, "outputs/heretic_csi/p2b/prod/cap")
    pairs, names = pf.load_pairs(f"{cap}/cap_{a.codeword}_BASE.pt", f"{cap}/cap_{a.codeword}_KO.pt", a.codeword)
    allidx = list(range(len(pairs)))
    print(f"[p4] {a.codeword}: {len(pairs)} pairs, {len({p['domain'] for p in pairs})} domains, frozen {obj}:{w} "
          f"({time.time()-t0:.0f}s)", flush=True)
    full = pf.build(pairs, names, allidx, "cw")
    O = [m for m in full if m.name.endswith("o_proj")]
    M = [m for m in full if m.name.endswith("down_proj")]
    L10 = [m for m in O if m.name == "L10.o_proj"]
    code = {f: hashlib.sha256(open(os.path.join(REPO, "research/heretic_csi", f), "rb").read()).hexdigest()
            for f in ("p4_head_fit.py", "p2b_fit.py", "p2b_operator.py")}
    summ = {"codeword": a.codeword, "frozen_objective": fz, "top8": TOP8, "code_sha256": code,
            "n_pairs": len(pairs), "ranks": {}}
    for r in [int(x) for x in a.ranks.split(",")]:
        cfg = po.FitCfg(rank=r, objective=obj, steer_weight=w, n_steps=a.n_steps)
        ops, diag = {}, {}

        def add(key, fac, mods_for_gc, meta):
            ops[key] = {"factors": fac, "meta": {**meta, "raw_fro": {n: po.fro_norm(A, B) for n, (A, B) in fac.items()}}}
            d = po.gap_closure(mods_for_gc, fac); d.update(gc_all(full, fac))
            d["total_fro"] = sum(v ** 2 for v in ops[key]["meta"]["raw_fro"].values()) ** 0.5
            diag[key] = d
            print(f"[p4] r{r} {key:11s} {json.dumps({k: round(v, 4) for k, v in d.items()})} ({time.time()-t0:.0f}s)", flush=True)

        top = fit_variant(O, cfg, TOP8); add("TOP8", top, O, {"heads": TOP8, "modules": "o_proj L6-18"})
        tn = {n: po.fro_norm(A, B) for n, (A, B) in top.items()}
        add("FULLO", fit_variant(O, cfg), O, {"heads": "all", "modules": "o_proj L6-18"})
        add("MLP", fit_variant(M, cfg), M, {"modules": "down_proj L6-18"})
        add("ATTNMLP", fit_variant(full, cfg), full, {"modules": "o_proj+down_proj L6-18 (refit; same as P2b CAND procedure)"})
        add("H2", fit_variant(O, cfg, [2]), O, {"heads": [2], "modules": "o_proj L6-18", "role": "descriptive"})
        add("CELL_L10H2", fit_variant(L10, cfg, [2]), L10, {"heads": [2], "modules": "o_proj L10 only", "role": "descriptive"})
        rh_raw = []
        for j in range(a.n_rh8):
            hs = sorted(random.Random(4000 + 100 * r + j).sample(NON_TOP8, 8))
            f = fit_variant(O, cfg, hs)
            raw = po.gap_closure(O, f)
            fr = po.rescale_to(f, tn)
            ops[f"RH8_{j}"] = {"factors": fr, "meta": {"heads": hs, "seed": 4000 + 100 * r + j,
                                                      "raw_fro": {n: po.fro_norm(A, B) for n, (A, B) in f.items()},
                                                      "rescaled_to": "TOP8 per-module Frobenius norm", "raw_fit": raw}}
            d = po.gap_closure(O, fr); d["raw_unscaled"] = raw; d["heads"] = hs
            diag[f"RH8_{j}"] = d
            rh_raw.append(raw["net"])
            if j % 10 == 0:
                print(f"[p4] r{r} RH8_{j} heads={hs} rescaled_net={d['net']:.4f} raw_net={raw['net']:.4f} ({time.time()-t0:.0f}s)", flush=True)
        # norm-match sanity
        for j in range(a.n_rh8):
            for n, (A, B) in ops[f"RH8_{j}"]["factors"].items():
                if abs(po.fro_norm(A, B) - tn[n]) > 1e-6 * max(1.0, tn[n]):
                    raise SystemExit(f"norm match failed RH8_{j} {n}")
        top_net = diag["TOP8"]["net"]
        rh_scaled = [diag[f"RH8_{j}"]["net"] for j in range(a.n_rh8)]
        diag["_summary"] = {"TOP8_net": top_net,
                            "TOP8_rank_among_RH8_rescaled": 1 + sum(x >= top_net for x in rh_scaled),
                            "TOP8_rank_among_RH8_raw": 1 + sum(x >= top_net for x in rh_raw),
                            "n_rh8": a.n_rh8, "note": "IN-SAMPLE fitting-side net (gap_closure - preserve_damage) "
                            "on o_proj modules; not an endpoint, not a test."}
        fp = os.path.join(a.out_dir, f"factors_p4_{a.codeword}_r{r}.pt")
        torch.save({"operators": ops, "provenance": {"codeword": a.codeword, "rank": r, "code_sha256": code,
                                                     "frozen_objective": fz, "top8": TOP8}}, fp)
        summ["ranks"][str(r)] = {"factors": os.path.relpath(fp, REPO), "diag": diag}
        json.dump(summ, open(os.path.join(a.out_dir, f"p4_fit_{a.codeword}.json"), "w"), indent=1)
        print(f"[p4] r{r} FACTORS_SAVED {fp}", flush=True)
        # TRAIN 5-fold domain-grouped CV: TOP8 vs first cv_nrh RH8 sets (raw, unscaled fits)
        folds = [f for f in pf.domain_folds(pairs) if f]
        cv = {"TOP8": [], **{f"RH8_{j}": [] for j in range(a.cv_nrh)}}
        for fi, fo in enumerate(folds):
            fs = set(fo)
            tr = [m for m in pf.build(pairs, names, [i for i in allidx if i not in fs], "cw") if m.name.endswith("o_proj")]
            te = [m for m in pf.build(pairs, names, fo, "cw") if m.name.endswith("o_proj")]
            cv["TOP8"].append(po.gap_closure(te, fit_variant(tr, cfg, TOP8))["net"])
            for j in range(a.cv_nrh):
                hs = ops[f"RH8_{j}"]["meta"]["heads"]
                cv[f"RH8_{j}"].append(po.gap_closure(te, fit_variant(tr, cfg, hs))["net"])
            print(f"[p4] r{r} CV fold {fi+1}/{len(folds)} ({time.time()-t0:.0f}s)", flush=True)
            del tr, te
        cvm = {k: sum(v) / len(v) for k, v in cv.items()}
        diag["_cv"] = {"heldout_net_mean": cvm,
                       "TOP8_rank_among_RH8": 1 + sum(cvm[f"RH8_{j}"] >= cvm["TOP8"] for j in range(a.cv_nrh)),
                       "n": a.cv_nrh, "note": "TRAIN 5-fold domain-grouped held-out fitting-side net; raw (unscaled) fits"}
        print(f"[p4] r{r} CV TOP8 {cvm['TOP8']:.4f} rank {diag['_cv']['TOP8_rank_among_RH8']}/{a.cv_nrh+1}", flush=True)
        summ["ranks"][str(r)] = {"factors": os.path.relpath(fp, REPO), "diag": diag}
        json.dump(summ, open(os.path.join(a.out_dir, f"p4_fit_{a.codeword}.json"), "w"), indent=1)
    print("P4_FIT_DONE", a.codeword, f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
