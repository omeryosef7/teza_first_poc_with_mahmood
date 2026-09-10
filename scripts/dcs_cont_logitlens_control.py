#!/usr/bin/env python3
"""N_logitlens: is a map cell reading a REPRESENTATION, or the model's own output pipeline?

Continuation mandate sections 12 and 18. THE CONTROL THAT GATES CONT-ENTRY 011.

WHY IT IS THE DECISIVE CONTROL HERE
-----------------------------------
The strongest interaction cells in `layerpos_train_button_bomb.json` sit at `rel-4` and `rel-6` --
the very end of the prompt -- in layers 26-31. That is exactly where the next-token distribution is
assembled. The behavioural prompt never poses the semantic question, so predicting `y_install`
there is CROSS-PROMPT rather than circular; but "cross-prompt, therefore not the output pipeline"
is an argument, and this turns it into a measurement.

WHAT IT COMPUTES
----------------
The logit lens: take the captured hidden state, apply the model's FINAL RMSNorm, and dot it with the
unembedding rows for the concept and codeword tokens only -- four rows of `lm_head`, not the whole
128256-row matrix, which is what makes this cheap:

    ll(h) = logsumexp_j <norm(h), W[concept_j]>  -  logsumexp_k <norm(h), W[codeword_k]>

read on the DOUBLESPEAK cell (C) and averaged to the domain. Then, per (site, layer):

    rho_map      = the map's leave-one-out score vs y_install          (already reported)
    rho_ll       = the logit-lens estimate vs y_install                (this file)
    rho_partial  = rho_map with rho_ll partialled out, on ranks

A cell whose `rho_partial` collapses toward zero is reading the output pipeline, not a separate
representation. A cell that keeps its correlation after the model's own next-token estimate is
removed is the only kind that can be promoted.

DISCIPLINE
  * TRAIN only. EXPLORATORY. Token ids are frozen in this file and were not chosen by looking at
    which ones correlated with anything.
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "lpm", os.path.join(REPO, "scripts", "dcs_cont_layerpos_map.py"))
lpm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lpm)

#: Frozen. Read out of tokenizer.json's vocab for the PINNED revision 0e9e39f2, and cross-checked
#: against the smoke capture provenance, which decoded id 3215 as ' button' at the codeword site.
CONCEPT_IDS = (13054, 33909)      # ' bomb', ' Bomb'
CODEWORD_IDS = (3215, 6739)       # ' button', ' Button'
RMS_EPS = 1e-5


def load_unembed(snapshot_glob: str):
    """The final RMSNorm weight and the four unembedding rows. Nothing else is read."""
    from safetensors import safe_open
    snaps = glob.glob(snapshot_glob)
    if not snaps:
        raise lpm.Refusal("no model snapshot matched %r" % snapshot_glob)
    snap = snaps[0]
    idx = json.load(open(os.path.join(snap, "model.safetensors.index.json")))["weight_map"]
    need = {}
    for key in ("model.norm.weight", "lm_head.weight"):
        if key not in idx:
            raise lpm.Refusal("%s absent from the weight map; tied embeddings are not handled"
                              % key)
        need.setdefault(idx[key], []).append(key)
    norm_w = None
    rows = {}
    for shard, keys in need.items():
        with safe_open(os.path.join(snap, shard), framework="pt") as f:
            for key in keys:
                if key == "model.norm.weight":
                    norm_w = f.get_tensor(key).float()
                else:
                    sl = f.get_slice(key)
                    for tid in list(CONCEPT_IDS) + list(CODEWORD_IDS):
                        rows[tid] = sl[tid:tid + 1, :][0].float()
    if norm_w is None or len(rows) != 4:
        raise lpm.Refusal("failed to read the norm weight or the four unembedding rows")
    return norm_w, rows, snap


def rank(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db) if da > 0 and db > 0 else 0.0


def partial_spearman(x, y, z):
    """Spearman(x, y) with z partialled out: Pearson correlation of the rank residuals."""
    rx, ry, rz = rank(x), rank(y), rank(z)
    rxy, rxz, ryz = pearson(rx, ry), pearson(rx, rz), pearson(ry, rz)
    den = math.sqrt(max(0.0, (1 - rxz ** 2) * (1 - ryz ** 2)))
    return (rxy - rxz * ryz) / den if den > 1e-12 else float("nan")


def main() -> int:
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--beh-run", required=True)
    ap.add_argument("--readout-run", required=True)
    ap.add_argument("--map", required=True, help="the layerpos map JSON to control")
    ap.add_argument("--snapshot-glob",
                    default="/home/sharifm/students/matanbentov/hub/"
                            "models--meta-llama--Llama-3.1-8B-Instruct/snapshots/*/")
    ap.add_argument("--split", default="train", choices=["train", "validation"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    norm_w, urows, snap = load_unembed(a.snapshot_glob)
    print("[ll] unembedding rows read from %s" % os.path.basename(snap.rstrip("/")))
    W_c = torch.stack([urows[t] for t in CONCEPT_IDS], 0)      # [2, d]
    W_k = torch.stack([urows[t] for t in CODEWORD_IDS], 0)

    assign = lpm.load_split()
    inst, _, _ = lpm.load_installation(os.path.join(REPO, a.readout_run))
    mp, rows, bank_sha = lpm.load_corpus(os.path.join(REPO, a.beh_run))
    ro_sha, ro_src = lpm.readout_bank_sha(os.path.join(REPO, a.readout_run))
    if ro_sha != bank_sha:
        raise lpm.Refusal("BANK MISMATCH corpus %s vs readout %s" % (bank_sha, ro_sha))
    sites, layers = list(mp["sites"]), list(mp["layers"])
    keep = {d for d, s in assign.items() if s == a.split} - set(lpm.EXCLUDED_DOMAINS)

    # cell C states only: the logit lens asks what the DOUBLESPEAK prompt is about to say.
    byk = {}
    for r in rows:
        if r["domain"] not in keep or r["cell"] != "C":
            continue
        t = mp["reps"].get(r["prompt_id"])
        if t is None:
            raise lpm.Refusal("row %r has no stack" % r["prompt_id"])
        byk[(r["domain"], lpm.family_slot(r["family_id"]))] = t.float()
    doms = sorted({d for d, _ in byk})
    ys = [sum(inst[k] for k in byk if k[0] == d) / max(1, len([k for k in byk if k[0] == d]))
          for d in doms]
    n = len(doms)
    print("[ll] %d cell-C keys over %d domains (split=%s)" % (len(byk), n, a.split))

    themap = json.load(open(os.path.join(REPO, a.map), encoding="utf-8"))
    if themap.get("bank_file_sha16") != bank_sha:
        raise lpm.Refusal("the map was computed on bank %s, corpus is %s"
                          % (themap.get("bank_file_sha16"), bank_sha))

    yt = torch.tensor(ys, dtype=torch.float32)
    out = {"schema": "dcs_cont_logitlens_control/1", "status": "EXPLORATORY",
           "beh_run": a.beh_run, "map": a.map, "split": a.split, "n_domains": n,
           "bank_file_sha16": bank_sha,
           "concept_ids": list(CONCEPT_IDS), "codeword_ids": list(CODEWORD_IDS),
           "read_on_cell": "C", "cells": {}}

    for si, site in enumerate(sites):
        for li, L in enumerate(layers):
            per_dom = []
            for d in doms:
                ks = [k for k in byk if k[0] == d]
                v = sum(byk[k][si, li] for k in ks) / len(ks)
                h = v / torch.sqrt((v * v).mean() + RMS_EPS) * norm_w
                lc = torch.logsumexp(W_c @ h, 0)
                lk = torch.logsumexp(W_k @ h, 0)
                per_dom.append(float(lc - lk))
            key = "%s|L%d" % (site, L)
            rho_ll = lpm.spearman(per_dom, ys)
            cell = {"rho_logitlens": rho_ll, "mean_ll": sum(per_dom) / n}
            for cname in themap["map"]:
                mc = themap["map"][cname].get(key)
                if mc is None:
                    continue
                # recompute the map's LOO scores so the partial uses the SAME per-domain vector
                cell.setdefault("by_contrast", {})[cname] = {"rho_map": mc["rho_loo"]}
            out["cells"][key] = cell

    # partial correlations need the map's per-domain scores; recompute them here for cell-C-based
    # contrasts using the same construction the map uses.
    byall = {}
    for r in rows:
        if r["domain"] not in keep:
            continue
        t = mp["reps"].get(r["prompt_id"])
        byall[((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])] = t.float()
    keys = sorted({k for (k, _) in byall})
    complete = [k for k in keys if all((k, c) in byall for c in ("A", "B", "C", "E"))]
    con = {"interaction": {}, "C_minus_B_LEXICAL": {}, "E_minus_A_LEXICAL": {},
           "token_main_effect_LEXICAL": {}}
    for d in doms:
        ks = [k for k in complete if k[0] == d]
        cb = sum((byall[(k, "C")] - byall[(k, "B")]) for k in ks) / len(ks)
        ea = sum((byall[(k, "E")] - byall[(k, "A")]) for k in ks) / len(ks)
        con["C_minus_B_LEXICAL"][d] = cb
        con["E_minus_A_LEXICAL"][d] = ea
        con["interaction"][d] = cb + ea
        con["token_main_effect_LEXICAL"][d] = cb - ea

    # ---- partial correlations: rho_map with the model's own next-token estimate removed ----
    for si, site in enumerate(sites):
        for li, L in enumerate(layers):
            key = "%s|L%d" % (site, L)
            lls = []
            for d in doms:
                ks = [k for k in byk if k[0] == d]
                v = sum(byk[k][si, li] for k in ks) / len(ks)
                h = v / torch.sqrt((v * v).mean() + RMS_EPS) * norm_w
                lls.append(float(torch.logsumexp(W_c @ h, 0) - torch.logsumexp(W_k @ h, 0)))
            for cname, cv in con.items():
                X = torch.stack([cv[d][si, li] for d in doms], 0)
                sc = [float(v) for v in lpm.loo_scores(X, yt)]
                pr = partial_spearman(sc, ys, lls)
                out["cells"][key].setdefault("by_contrast", {}).setdefault(cname, {})
                out["cells"][key]["by_contrast"][cname]["rho_partial_given_logitlens"] = pr
    op = os.path.join(REPO, a.out)
    os.makedirs(os.path.dirname(op), exist_ok=True)
    json.dump(out, open(op, "w", encoding="utf-8"), indent=1)
    print("[ll] wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lpm.Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        raise SystemExit(2)
