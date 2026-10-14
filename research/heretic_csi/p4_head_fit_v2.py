#!/usr/bin/env python3
"""P4 v2 (PREREG_P4_AMENDMENT_1): head-restricted weight operator with TWO control families.

Why v2 (adversarial review #2, CRITICAL-1): v1 fitted each random-8-head control (RH8) at its own optimum and then
RESCALED it per module to TOP8's Frobenius norm. TOP8 needs ~1.8-2.3x the norm of an all-head fit, so the rescale
pushed the controls far off their optimum (in-sample net, button r1 RH8_0: 0.621 raw -> 0.147 rescaled vs TOP8
0.622) -- a structural advantage for TOP8. v1 (p4_head_fit.py) is kept unchanged for provenance; its jobs were
cancelled before any factors were saved.

Families per rank r (all on self_attn.o_proj, layers 6-18, A zero outside the chosen query heads' columns):
  RH8RAW_j  random 8-head set (from the 24 non-TOP8 heads, seed 4000+100r+j), fitted at its OWN optimum (no norm
            constraint) -- same procedure as TOP8; norms differ and are reported.
  RH8NC_j   the same head set, REFIT under a per-module Frobenius-norm EQUALITY constraint ||B A||_F = ||TOP8||_F
            (per module): reparametrisation dW = c * B A / ||B A||_F, L-BFGS on (A, B), initialised at the
            RH8RAW_j optimum (= exactly v1's rescaled point), so it can only improve on the post-hoc rescale.
Candidate TOP8 at its own optimum. Descriptive: TOP8_L6_14 (TOP8 heads, o_proj L6-14 only = the band on which the
heads were nominated), FULLO, MLP, ATTNMLP, H2, CELL_L10H2.
Objective = P2b's frozen one (freeze_pooled.json). Fitting side only; y_install never read.
--mode fit  : all operators -> factors_p4v2_<cw>_r<R>.pt (+ p4v2_fit_<cw>_r<R>.json); saved BEFORE any optional extra
--mode cv   : 5-fold domain-grouped TRAIN CV, held-out net for TOP8 vs RH8RAW_0..cv_nrh-1 and RH8NC_0..cv_nrh-1
"""
import argparse, hashlib, json, os, random, sys, time
import torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_operator as po   # noqa: E402
import p2b_fit as pf        # noqa: E402
from p4_head_fit import TOP8, NON_TOP8, cols, restrict, embed, gc_all   # noqa: E402


def rh8_heads(r, j):
    return sorted(random.Random(4000 + 100 * r + j).sample(NON_TOP8, 8))


def fit_normc(mods, cfg, init, target):
    """Refit factored operators under ||B@A||_F == target[name] per module (equality, via reparametrisation)."""
    dev = cfg.device
    st, params = {}, []
    for m in mods:
        A0, B0 = init[m.name]
        A = A0.clone().float().to(dev).requires_grad_(True)
        B = B0.clone().float().to(dev).requires_grad_(True)
        params += [A, B]
        gap2, st0, inv_std = po._norms(m, cfg, dev)
        st[m.name] = dict(A=A, B=B, c=float(target[m.name]), s_in=m.s_in.to(dev).float(), s_out=m.s_out.to(dev).float(),
                          t_out=m.t_out.to(dev).float(), p_in=m.p_in.to(dev).float(), gap2=gap2, st0=st0, inv_std=inv_std)
    opt = torch.optim.LBFGS(params, lr=1.0, max_iter=cfg.lbfgs_max_iter, history_size=10, line_search_fn="strong_wolfe")

    def scale(s):
        n = torch.sqrt(torch.clamp(torch.trace((s["A"] @ s["A"].t()) @ (s["B"].t() @ s["B"])), min=1e-24))
        return s["c"] / n

    def closure():
        opt.zero_grad()
        tot = torch.zeros((), device=dev)
        for s in st.values():
            k = scale(s)
            new_s = s["s_out"] + k * po._delta(s["s_in"], s["A"], s["B"])
            preserve = ((k * po._delta(s["p_in"], s["A"], s["B"])) ** 2).sum(1).mean() / s["gap2"]
            steer = po._steer(cfg, new_s, s["t_out"], s["s_out"], s["inv_std"]) / s["st0"]
            tot = tot + cfg.preserve_weight * preserve + cfg.steer_weight * steer
        tot.backward()
        return tot

    for _ in range(cfg.n_steps):
        opt.step(closure)
    out = {}
    with torch.no_grad():
        for n, s in st.items():
            out[n] = (s["A"].detach().cpu(), (scale(s) * s["B"]).detach().cpu())
    return out


def fit_heads(O, cfg, heads):
    c = cols(heads)
    R = [restrict(m, c) for m in O]
    return R, c, po.fit_factored(R, cfg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--rank", type=int, required=True)
    ap.add_argument("--mode", choices=("fit", "cv"), default="fit")
    ap.add_argument("--n-rh8", type=int, default=60)
    ap.add_argument("--cv-nrh", type=int, default=20)
    ap.add_argument("--n-steps", type=int, default=15)
    ap.add_argument("--out-dir", default=os.path.join(REPO, "outputs/heretic_csi/p2b/prod/p4"))
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    fz = json.load(open(os.path.join(REPO, "outputs/heretic_csi/p2b/prod/fac/freeze_pooled.json")))["frozen"]
    obj, w = fz.split(":"); w = float(w)
    cfg = po.FitCfg(rank=a.rank, objective=obj, steer_weight=w, n_steps=a.n_steps)
    cap = os.path.join(REPO, "outputs/heretic_csi/p2b/prod/cap")
    pairs, names = pf.load_pairs(f"{cap}/cap_{a.codeword}_BASE.pt", f"{cap}/cap_{a.codeword}_KO.pt", a.codeword)
    allidx = list(range(len(pairs)))
    code = {f: hashlib.sha256(open(os.path.join(REPO, "research/heretic_csi", f), "rb").read()).hexdigest()
            for f in ("p4_head_fit_v2.py", "p4_head_fit.py", "p2b_fit.py", "p2b_operator.py")}
    print(f"[p4v2] {a.codeword} r{a.rank} mode={a.mode}: {len(pairs)} pairs, frozen {fz} code={json.dumps(code)} ({time.time()-t0:.0f}s)", flush=True)
    tag = f"{a.codeword}_r{a.rank}"
    if a.mode == "cv":
        res = {"TOP8": [], **{f"RH8RAW_{j}": [] for j in range(a.cv_nrh)}, **{f"RH8NC_{j}": [] for j in range(a.cv_nrh)}}
        for fi, fo in enumerate([f for f in pf.domain_folds(pairs) if f]):
            fs = set(fo)
            tr = [m for m in pf.build(pairs, names, [i for i in allidx if i not in fs], "cw") if m.name.endswith("o_proj")]
            te = [m for m in pf.build(pairs, names, fo, "cw") if m.name.endswith("o_proj")]
            Rt, c, ft = fit_heads(tr, cfg, TOP8)
            tn = {n: po.fro_norm(A, B) for n, (A, B) in ft.items()}
            res["TOP8"].append(po.gap_closure(te, embed(ft, c, 4096))["net"])
            for j in range(a.cv_nrh):
                Rj, cj, fj = fit_heads(tr, cfg, rh8_heads(a.rank, j))
                res[f"RH8RAW_{j}"].append(po.gap_closure(te, embed(fj, cj, 4096))["net"])
                fn = fit_normc(Rj, cfg, fj, tn)
                res[f"RH8NC_{j}"].append(po.gap_closure(te, embed(fn, cj, 4096))["net"])
            print(f"[p4v2] CV fold {fi+1} ({time.time()-t0:.0f}s)", flush=True)
            del tr, te
        m = {k: sum(v) / len(v) for k, v in res.items()}
        out = {"codeword": a.codeword, "rank": a.rank, "code_sha256": code, "heldout_net_mean": m,
               "TOP8_rank_among_RAW": 1 + sum(m[f"RH8RAW_{j}"] >= m["TOP8"] for j in range(a.cv_nrh)),
               "TOP8_rank_among_NC": 1 + sum(m[f"RH8NC_{j}"] >= m["TOP8"] for j in range(a.cv_nrh)),
               "n": a.cv_nrh, "note": "TRAIN 5-fold domain-grouped held-out fitting-side net (gap_closure - preserve_damage), o_proj modules"}
        json.dump(out, open(os.path.join(a.out_dir, f"p4v2_cv_{tag}.json"), "w"), indent=1)
        print(f"[p4v2] CV TOP8 {m['TOP8']:.4f} rank RAW {out['TOP8_rank_among_RAW']}/{a.cv_nrh+1} NC {out['TOP8_rank_among_NC']}/{a.cv_nrh+1}")
        print("P4V2_CV_DONE", tag, flush=True)
        return
    full = pf.build(pairs, names, allidx, "cw")
    O = [m for m in full if m.name.endswith("o_proj")]
    M = [m for m in full if m.name.endswith("down_proj")]
    O14 = [m for m in O if int(m.name.split(".")[0][1:]) <= 14]
    L10 = [m for m in O if m.name == "L10.o_proj"]
    ops, diag = {}, {}

    def add(key, fac, mods_for_gc, meta):
        ops[key] = {"factors": fac, "meta": {**meta, "raw_fro": {n: po.fro_norm(A, B) for n, (A, B) in fac.items()}}}
        d = po.gap_closure(mods_for_gc, fac); d.update(gc_all(full, fac))
        d["total_fro"] = sum(v ** 2 for v in ops[key]["meta"]["raw_fro"].values()) ** 0.5
        diag[key] = d
        print(f"[p4v2] {key:12s} {json.dumps({k: round(v, 4) for k, v in d.items()})} ({time.time()-t0:.0f}s)", flush=True)

    _, c8, f8 = fit_heads(O, cfg, TOP8)
    top = embed(f8, c8, 4096)
    add("TOP8", top, O, {"heads": TOP8, "modules": "o_proj L6-18", "role": "candidate"})
    tn = {n: po.fro_norm(A, B) for n, (A, B) in top.items()}
    _, c14, f14 = fit_heads(O14, cfg, TOP8)
    add("TOP8_L6_14", embed(f14, c14, 4096), O14, {"heads": TOP8, "modules": "o_proj L6-14 (nomination band)", "role": "descriptive"})
    add("FULLO", po.fit_factored(O, cfg), O, {"heads": "all", "modules": "o_proj L6-18", "role": "descriptive"})
    add("MLP", po.fit_factored(M, cfg), M, {"modules": "down_proj L6-18", "role": "descriptive"})
    add("ATTNMLP", po.fit_factored(full, cfg), full, {"modules": "o_proj+down_proj L6-18", "role": "descriptive"})
    _, ch2, fh2 = fit_heads(O, cfg, [2])
    add("H2", embed(fh2, ch2, 4096), O, {"heads": [2], "modules": "o_proj L6-18", "role": "descriptive"})
    _, cc, fc = fit_heads(L10, cfg, [2])
    add("CELL_L10H2", embed(fc, cc, 4096), L10, {"heads": [2], "modules": "o_proj L10", "role": "descriptive"})
    for j in range(a.n_rh8):
        hs = rh8_heads(a.rank, j)
        Rj, cj, fj = fit_heads(O, cfg, hs)
        meta = {"heads": hs, "seed": 4000 + 100 * a.rank + j}
        add(f"RH8RAW_{j}", embed(fj, cj, 4096), O, {**meta, "family": "RAW (own optimum)"})
        fn = fit_normc(Rj, cfg, fj, tn)
        resc = po.gap_closure(O, embed(po.rescale_to(fj, tn), cj, 4096))
        add(f"RH8NC_{j}", embed(fn, cj, 4096), O, {**meta, "family": "NC (refit, per-module norm == TOP8)",
                                                  "v1_style_rescaled_net": resc["net"]})
        diag[f"RH8NC_{j}"]["v1_style_rescaled_net"] = resc["net"]
        for n, (A, B) in ops[f"RH8NC_{j}"]["factors"].items():
            if abs(po.fro_norm(A, B) - tn[n]) > 1e-4 * max(1.0, tn[n]):
                raise SystemExit(f"NC norm constraint violated RH8NC_{j} {n}: {po.fro_norm(A, B)} vs {tn[n]}")
    raw = [diag[f"RH8RAW_{j}"]["net"] for j in range(a.n_rh8)]
    nc = [diag[f"RH8NC_{j}"]["net"] for j in range(a.n_rh8)]
    rf = [diag[f"RH8RAW_{j}"]["total_fro"] for j in range(a.n_rh8)]
    diag["_summary"] = {"TOP8_net": diag["TOP8"]["net"], "TOP8_total_fro": diag["TOP8"]["total_fro"],
                        "TOP8_rank_among_RAW": 1 + sum(x >= diag["TOP8"]["net"] for x in raw),
                        "TOP8_rank_among_NC": 1 + sum(x >= diag["TOP8"]["net"] for x in nc),
                        "RAW_net_min_med_max": [min(raw), sorted(raw)[len(raw) // 2], max(raw)],
                        "NC_net_min_med_max": [min(nc), sorted(nc)[len(nc) // 2], max(nc)],
                        "RAW_total_fro_min_med_max": [min(rf), sorted(rf)[len(rf) // 2], max(rf)],
                        "note": "IN-SAMPLE fitting-side net on o_proj modules; not an endpoint, not a test"}
    fp = os.path.join(a.out_dir, f"factors_p4v2_{tag}.pt")
    torch.save({"operators": ops, "provenance": {"codeword": a.codeword, "rank": a.rank, "code_sha256": code,
                                                 "frozen_objective": fz, "top8": TOP8, "version": "v2 (PREREG_P4_AMENDMENT_1)"}}, fp)
    json.dump({"codeword": a.codeword, "rank": a.rank, "factors": os.path.relpath(fp, REPO), "code_sha256": code, "diag": diag},
              open(os.path.join(a.out_dir, f"p4v2_fit_{tag}.json"), "w"), indent=1)
    print(f"[p4v2] SUMMARY {json.dumps(diag['_summary'])}", flush=True)
    print("P4V2_FIT_DONE", fp, f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
