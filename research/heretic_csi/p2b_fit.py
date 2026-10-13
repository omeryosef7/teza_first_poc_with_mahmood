#!/usr/bin/env python3
"""P2b fitting: pair clean/KO captures, select the objective on TRAIN (CV, fitting-side criterion only),
fit the rank sweep + fitted controls, save factors for evaluation and P3 SVD.

Inputs: capture files written by p2b_runner (OPSPEC capture) for the BASE (clean = TARGET) and KO
(knockout = SOURCE) arms of ONE codeword on the TRAIN population.

Pairing: by `ctx_sha16` (the exact token ids of the readout context) -- one clean and one KO record per
prompt. Domain labels come from the KO arm's results.jsonl, row-aligned with the capture records and
VERIFIED row by row (seq_len == bare_len, surface_span_positions == [codeword anchor]); a mismatch is
fatal. Rows not on the TRAIN split are refused (TEST/VALIDATION never enter a fit).

Objective selection (mandate §8): objectives {knn, mse, cos, whiten} x steer_weight {0.3, 1, 3}, scored
by 5-fold DOMAIN-grouped CV at ranks {1, 4, 16} with an objective-NEUTRAL criterion: held-out
`net = gap_closure - preserve_damage` (p2b_operator.gap_closure). The y_install endpoint is NEVER read
here. The winning (objective, steer_weight) is frozen for every rank, codeword and control.

Operators saved per rank r (keys):
  CAND           fit at the codeword row (rel_end -10): SOURCE=KO -> TARGET=clean
  NEUT           same, fit at the last prompt row (rel_end -1; Heretic-native position analogue)
  SHUF{j}        j=0..4: per-prompt random source/target ROLE swap + domain-deranged pairing
  SRC2SRC/TGT2TGT  degenerate fits (source->itself, target->itself): pipeline sanity, expect ΔW = 0
SHUF{j} are rescaled per module to CAND's Frobenius norm (raw norms recorded) so the rank test compares
directions at matched rank, modules, layers, #params, training rows and norm. NEUT keeps its own fitted
norm (see the note at its fit) and is a separate position contrast, not a rank-family member.
PRESERVE set = clean module inputs at the codeword row, the last row and the BASE capture's extra rows.
"""
import argparse, hashlib, importlib.util, json, os, random, sys, time

import torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_operator as po   # noqa: E402

RANKS = [1, 2, 4, 8, 16, 32, 50]
CV_RANKS = [1, 4, 16]
STEER_WS = [0.3, 1.0, 3.0]
N_SHUF = 5


def _load_lpm():
    s = importlib.util.spec_from_file_location("lpm", os.path.join(REPO, "scripts/dcs_cont_layerpos_map.py"))
    m = importlib.util.module_from_spec(s); sys.modules["lpm"] = m; s.loader.exec_module(m)
    return m


def load_pairs(clean_pt, ko_pt, codeword):
    C, K = torch.load(clean_pt, map_location="cpu"), torch.load(ko_pt, map_location="cpu")
    if C["names"] != K["names"]:
        raise SystemExit("clean/KO captures use different module lists")
    rows = [json.loads(l) for l in open(os.path.join(K["run_dir"], "results.jsonl"))]
    if len(rows) != len(K["records"]):
        raise SystemExit(f"KO results rows {len(rows)} != KO capture records {len(K['records'])}")
    lpm = _load_lpm()
    assign = lpm.load_split()
    cmap = {}
    for r in C["records"]:
        h = r["meta"]["ctx_sha16"]
        if h in cmap:
            raise SystemExit(f"duplicate clean ctx {h}")
        cmap[h] = r
    pairs = []
    for rec, row in zip(K["records"], rows):
        m = rec["meta"]
        if row.get("seq_len") != m["bare_len"]:
            raise SystemExit(f"{row['prompt_id']}: seq_len {row.get('seq_len')} != capture bare_len {m['bare_len']}")
        if row.get("surface_span_positions") != [m["anchor"]["abs_pos"]]:
            raise SystemExit(f"{row['prompt_id']}: KO surface row {row.get('surface_span_positions')} "
                             f"!= capture codeword row {m['anchor']['abs_pos']}")
        if not m["anchor"]["matches_codeword"] or m["anchor"]["codeword"] != codeword:
            raise SystemExit(f"{row['prompt_id']}: anchor not on codeword {codeword}")
        if assign.get(row["domain"]) != "train":
            raise SystemExit(f"{row['prompt_id']}: domain {row['domain']} is {assign.get(row['domain'])!r}, not train")
        if m["ctx_sha16"] not in cmap:
            raise SystemExit(f"{row['prompt_id']}: no clean capture with the same context")
        pairs.append({"prompt_id": row["prompt_id"], "domain": row["domain"], "ko": rec,
                      "clean": cmap.pop(m["ctx_sha16"]), "anchor": m["anchor"],
                      "last_token": m["last_token"]})
    if cmap:
        raise SystemExit(f"{len(cmap)} clean captures have no KO partner")
    return pairs, C["names"]


def shuffle_plan(pairs, idx, seed):
    """(perm, swap): per-prompt role swap (p=0.5) and a DOMAIN DERANGEMENT of the pairing -- the target
    of prompt i comes from a prompt in a different domain."""
    rng = random.Random(seed)
    swap = [rng.random() < 0.5 for _ in idx]
    perm = list(idx)
    for _ in range(1000):
        rng.shuffle(perm)
        if all(pairs[i]["domain"] != pairs[j]["domain"] for i, j in zip(idx, perm)):
            return perm, swap
    raise SystemExit("could not build a domain derangement")


def build(pairs, names, idx, pos, shuffle_seed=None):
    """PairedIO per module for prompts `idx` at fit position `pos` ('cw' or 'last')."""
    perm, swap = (list(idx), [False] * len(idx)) if shuffle_seed is None else shuffle_plan(pairs, idx, shuffle_seed)
    out = []
    for n in names:
        s_in, s_out, t_in, t_out, p_in = [], [], [], [], []
        for k, (i, j) in enumerate(zip(idx, perm)):
            src, tgt = pairs[i]["ko"]["acts"][n][pos], pairs[j]["clean"]["acts"][n][pos]
            if swap[k]:
                src, tgt = pairs[i]["clean"]["acts"][n][pos], pairs[j]["ko"]["acts"][n][pos]
            s_in.append(src[0]); s_out.append(src[1]); t_in.append(tgt[0]); t_out.append(tgt[1])
        for i in idx:   # PRESERVE set: clean states at cw, last and every extra row; never shuffled
            for tag, (xin, _) in pairs[i]["clean"]["acts"][n].items():
                p_in.append(xin)
        st = lambda L: torch.stack(L).float()   # noqa: E731
        out.append(po.PairedIO(n, st(s_in), st(s_out), st(t_in), st(t_out), st(p_in)))
    return out


def degenerate(mods, which):
    """SRC2SRC: target := source; TGT2TGT: source := target."""
    o = []
    for m in mods:
        if which == "SRC2SRC":
            o.append(po.PairedIO(m.name, m.s_in, m.s_out, m.s_in, m.s_out, m.p_in))
        else:
            o.append(po.PairedIO(m.name, m.t_in, m.t_out, m.t_in, m.t_out, m.p_in))
    return o


def domain_folds(pairs, k=5, seed=20261013):
    doms = sorted({p["domain"] for p in pairs})
    random.Random(seed).shuffle(doms)
    return [[i for i, p in enumerate(pairs) if p["domain"] in set(doms[f::k])] for f in range(k)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", required=True)
    ap.add_argument("--ko", required=True)
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--ranks", default=",".join(map(str, RANKS)))
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--freeze", default=None, help="objective:steer_w to skip CV (e.g. reuse basket's frozen choice)")
    ap.add_argument("--n-steps", type=int, default=15)
    ap.add_argument("--cv-only", action="store_true", help="write cv_<cw>.json and stop (pooled freeze across codewords)")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    pairs, names = load_pairs(a.clean, a.ko, a.codeword)
    doms = sorted({p["domain"] for p in pairs})
    print(f"[fit] {a.codeword}: {len(pairs)} paired prompts, {len(doms)} train domains, {len(names)} modules", flush=True)
    allidx = list(range(len(pairs)))
    prov = {"codeword": a.codeword, "n_pairs": len(pairs), "n_domains": len(doms), "modules": names,
            "clean_capture": a.clean, "ko_capture": a.ko,
            "anchors": [{"prompt_id": p["prompt_id"], "domain": p["domain"], **p["anchor"],
                         "last_token": p["last_token"]} for p in pairs]}

    # ---------------- objective selection (TRAIN CV, fitting-side criterion) ----------------
    if a.freeze:
        obj, w = a.freeze.split(":"); w = float(w)
        cv = {"frozen_from_cli": a.freeze}
    else:
        folds = [f for f in domain_folds(pairs) if f]
        acc = {}
        for fi, f in enumerate(folds):          # build each fold's tensors ONCE (they are large)
            fs = set(f)
            tr_m = build(pairs, names, [i for i in allidx if i not in fs], "cw")
            te_m = build(pairs, names, f, "cw")
            for obj in po.OBJECTIVES:
                for w in STEER_WS:
                    for r in CV_RANKS:
                        cfg = po.FitCfg(rank=r, objective=obj, steer_weight=w, n_steps=a.n_steps, device=a.device)
                        fac = po.fit_factored(tr_m, cfg)
                        acc.setdefault(f"{obj}:{w}", []).append(po.gap_closure(te_m, fac, a.device))
            print(f"[cv] fold {fi + 1}/{len(folds)} done ({time.time() - t0:.0f}s)", flush=True)
            del tr_m, te_m
        cv = {}
        for key, nets in acc.items():
            cv[key] = {k: sum(x[k] for x in nets) / len(nets) for k in nets[0]}
            cv[key]["n_fold_rank_fits"] = len(nets)
            print(f"[cv] {key:12s} {cv[key]}", flush=True)
        best = max(cv, key=lambda k: cv[k]["net"])
        obj, w = best.split(":"); w = float(w)
        print(f"[cv] FROZEN objective={obj} steer_weight={w}", flush=True)
    frozen = {"objective": obj, "steer_weight": w, "preserve_weight": 1.0, "n_steps": a.n_steps}
    json.dump({"cv": cv, "frozen": frozen, "criterion": "held-out net = gap_closure - preserve_damage, "
               "5-fold domain-grouped CV, mean over ranks %s" % CV_RANKS},
              open(os.path.join(a.out_dir, f"cv_{a.codeword}.json"), "w"), indent=1)

    if a.cv_only:
        print("CV_ONLY_DONE", a.codeword, flush=True)
        return
    # ---------------- rank sweep + fitted controls (all TRAIN rows) ----------------
    full_cw = build(pairs, names, allidx, "cw")
    full_last = build(pairs, names, allidx, "last")
    summary = {"frozen": frozen, "ranks": {}}
    for r in [int(x) for x in a.ranks.split(",")]:
        cfg = po.FitCfg(rank=r, objective=obj, steer_weight=w, n_steps=a.n_steps, device=a.device)
        ops = {}
        cand = po.fit_factored(full_cw, cfg)
        cn = {n: po.fro_norm(A, B) for n, (A, B) in cand.items()}
        ops["CAND"] = {"factors": cand, "meta": {"fit": "codeword_row", "raw_fro": cn,
                                                 "train_fit": po.gap_closure(full_cw, cand, a.device)}}
        # NEUT is NOT norm-matched: the last row's clean-vs-KO gap is small, so its natural ΔW is small,
        # and inflating it to CAND's norm collapsed the readout in the smoke (option mass 8e-5, job
        # 1022701). It is a POSITION control at its own fitted norm, reported outside the rank family.
        neut = po.fit_factored(full_last, cfg)
        ops["NEUT"] = {"factors": neut,
                       "meta": {"fit": "last_row (rel_end -1), raw norm (not norm-matched)",
                                "raw_fro": {n: po.fro_norm(A, B) for n, (A, B) in neut.items()}}}
        for j in range(N_SHUF):
            sh = po.fit_factored(build(pairs, names, allidx, "cw", shuffle_seed=1000 * r + j), cfg)
            ops[f"SHUF{j}"] = {"factors": po.rescale_to(sh, cn),
                               "meta": {"fit": "role-swap + domain-deranged pairing", "seed": 1000 * r + j,
                                        "raw_fro": {n: po.fro_norm(A, B) for n, (A, B) in sh.items()},
                                        "norm_matched_to": "CAND"}}
        for which in ("SRC2SRC", "TGT2TGT"):
            dg = po.fit_factored(degenerate(full_cw, which), cfg)
            ops[which] = {"factors": dg, "meta": {"fit": which, "raw_fro": {n: po.fro_norm(A, B) for n, (A, B) in dg.items()}}}
        for k, v in ops.items():
            v["meta"].update(rank=r, objective=obj, steer_weight=w, codeword=a.codeword,
                             n_params=int(sum(A.numel() + B.numel() for A, B in v["factors"].values())),
                             numerical_rank={n: po.numerical_rank(A, B) for n, (A, B) in list(v["factors"].items())[:2]})
        path = os.path.join(a.out_dir, f"factors_{a.codeword}_r{r}.pt")
        torch.save({"operators": ops, "provenance": {k: v for k, v in prov.items() if k != "anchors"}}, path)
        summary["ranks"][r] = {k: {"total_fro": sum(v["meta"]["raw_fro"].values()), "train_fit": v["meta"].get("train_fit")}
                               for k, v in ops.items()}
        print(f"[fit] r={r} saved {path} CAND fit={ops['CAND']['meta']['train_fit']} "
              f"|CAND|={sum(cn.values()):.4g} |SRC2SRC|={summary['ranks'][r]['SRC2SRC']['total_fro']:.3g} "
              f"({time.time()-t0:.0f}s)", flush=True)
    json.dump(prov, open(os.path.join(a.out_dir, f"anchors_{a.codeword}.json"), "w"))
    json.dump(summary, open(os.path.join(a.out_dir, f"fit_summary_{a.codeword}.json"), "w"), indent=1)
    print("FIT_DONE", a.codeword, flush=True)


if __name__ == "__main__":
    main()
