#!/usr/bin/env python3
"""EXPLORATORY layer x position map on TRAIN. Continuation mandate sections 8, 9, 13, 16, 18.

WHAT THIS ANSWERS THAT THE SUCCESSOR SPRINT COULD NOT
-----------------------------------------------------
Every ts116m extraction on disk was `--position codeword_last --layers 6..14`: ONE site, nine
layers, and that site is the one the full-state transplant already returned a null at. This reads
the DR-069 multi-position corpus (20 sites x 19 layers) and asks, for every (site, layer):

    does the paired, REGISTER-MATCHED contrast at this site predict concept-free semantic
    installation across domains, better than the floors we have already measured?

THREE THINGS THAT ARE NOT THE OBVIOUS IMPLEMENTATION, AND WHY
-------------------------------------------------------------
1. THE CONTRASTS ARE `C - B` AND `E - A`, NEVER `C - A`.
   Measured on 70 train domains x 700 matched family pairs: the bank's surface partition is by
   DEMONSTRATION VALENCE, not by codeword -- {A,E} share the benign sentence pool and {B,C} share
   the harm pool, with n_tokens and harm-vocabulary density equal TO THE DIGIT within each pair.
   So C is a surface twin of B, not of A. `C - A` is register-confounded (a surface-only
   classifier separates the matched pair); `C - B` and `E - A` are each register-matched, and
   their difference is the token x context interaction.

2. THE PREDICTOR IS READ ON THE BEHAVIOURAL PROMPT, THE TARGET ON THE SEMANTIC ONE.
   `y_install` IS the next token after the semantic prompt's question, so a representation read
   near the end of that prompt at a late layer is the answer, not a representation of it. The
   behavioural prompt never poses the question. The two row sets match 1160/1160 on
   (domain, family_slot).

3. EVERY DIRECTION IS LEAVE-ONE-DOMAIN-OUT.
   A domain never contributes to the direction it is scored against.

DISCIPLINE
  * TRAIN domains only. The corpus itself contains no test rows (`--only-split train,validation`),
    so test cannot be read here even by mistake; validation is present but is refused unless
    --split validation is passed explicitly, and selection must not use it.
  * EXPLORATORY. No p-value printed here may be promoted to a confirmatory claim.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT_MANIFEST = os.path.join(REPO, "data", "boombness_prompts", "dcs_ts116_domain_split.json")
EXCLUDED_DOMAINS = ("restaurant_kitchen", "school_campus", "subway_station")


class Refusal(RuntimeError):
    pass


def family_slot(family_id: str) -> str:
    """Everything except the DOMAIN (first field) and the QUERY_KIND (last field).

    D-001 is the precedent: dropping the bank's dev/heldout field made `dev|slot0` and
    `heldout|slot0` the same key and silently halved the data. The query_kind field is the one
    that legitimately differs between the behavioural predictor and the semantic target, which is
    exactly why it is the one dropped.
    """
    parts = family_id.split("|")
    if len(parts) < 3:
        raise Refusal("family_id %r has too few fields to carry a slot" % family_id)
    return "|".join(parts[1:-1])


def load_split():
    with open(SPLIT_MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)["assign"]


def load_installation(run_dir: str):
    """(domain, slot) -> concept_binary_prob, from the CONCEPT-FREE one-word channel only.

    Mandate section 4 forbids defining the target from the forced-choice channel, which supplies
    the option set and therefore names the answer. That run directory contains BOTH channels, so
    the filter is load-bearing, not cosmetic.
    """
    path = os.path.join(run_dir, "results.jsonl")
    if not os.path.exists(path):
        raise Refusal("no results.jsonl under %r" % run_dir)
    out, n_seen, kinds = {}, 0, set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            kinds.add(r.get("query_kind"))
            if r.get("query_kind") != "semantic_one_word":
                continue
            if r.get("cell") != "C":
                continue
            lc, lk = r.get("logp_concept"), r.get("logp_codeword")
            if lc is None or lk is None:
                raise Refusal("row %r has no logp_concept/logp_codeword; missing != zero"
                              % r.get("prompt_id"))
            m = max(lc, lk)
            p = math.exp(lc - m) / (math.exp(lc - m) + math.exp(lk - m))
            out[(r["domain"], family_slot(r["family_id"]))] = p
            n_seen += 1
    if not out:
        raise Refusal("installation selection bound ZERO rows (channels present: %s)"
                      % sorted(kinds))
    return out, n_seen, sorted(kinds)


def load_corpus(run_dir: str):
    import torch
    mp_path = os.path.join(run_dir, "cache", "multiposition_reps.pt")
    if not os.path.exists(mp_path):
        raise Refusal("no multiposition_reps.pt under %r" % run_dir)
    if not os.path.exists(os.path.join(run_dir, "DONE.json")):
        raise Refusal("%r has no DONE.json; an unfinished run is not a corpus" % run_dir)
    mp = torch.load(mp_path, weights_only=False)
    rows = [json.loads(l) for l in open(os.path.join(run_dir, "results.jsonl"), encoding="utf-8")]
    shas = {r.get("bank_file_sha16") for r in rows}
    if len(shas) != 1:
        raise Refusal("run %r mixes bank_file_sha16 %s" % (run_dir, shas))
    return mp, rows, shas.pop()


def loo_scores(X, yv):
    """LOO covariance-direction scores for one cell. `X` is [n, d]; `yv` is [n] or [B, n].

    y-bar is recomputed WITHOUT the held-out domain (see the note at the call site).
    Returns [n] or [B, n].
    """
    import torch
    single = (yv.dim() == 1)
    Y = yv.unsqueeze(0) if single else yv
    B, n = Y.shape
    sum_xy = Y @ X                       # [B, d]
    sum_x = X.sum(0)                     # [d]
    sum_y = Y.sum(1)                     # [B]
    ybar_i = (sum_y.unsqueeze(1) - Y) / (n - 1)                     # [B, n]
    V = (sum_xy.unsqueeze(1) - X.unsqueeze(0) * Y.unsqueeze(2)) \
        - (sum_x.view(1, 1, -1) - X.unsqueeze(0)) * ybar_i.unsqueeze(2)   # [B, n, d]
    num = (X.unsqueeze(0) * V).sum(2)                                # [B, n]
    den = V.norm(dim=2).clamp_min(1e-12)
    out = num / den
    return out.squeeze(0) if single else out


def spearman(xs, ys):
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
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return num / (dx * dy) if dx > 0 and dy > 0 else 0.0


def main() -> int:
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--beh-run", required=True, help="behavioural multi-position run dir")
    ap.add_argument("--readout-run", required=True, help="the concept-free readout run dir")
    ap.add_argument("--split", default="train", choices=["train", "validation"],
                    help="DISCOVERY is train. validation is for SELECTION only and must not be "
                         "used to search.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20260910)
    a = ap.parse_args()

    assign = load_split()
    inst, n_inst_rows, kinds = load_installation(os.path.join(REPO, a.readout_run))
    mp, rows, bank_sha = load_corpus(os.path.join(REPO, a.beh_run))
    sites, layers = list(mp["sites"]), list(mp["layers"])
    print("[map] corpus %s" % a.beh_run)
    print("[map]   bank_file_sha16=%s sites=%d layers=%d rows=%d"
          % (bank_sha, len(sites), len(layers), len(rows)))
    print("[map]   installation: %d rows from channels %s" % (n_inst_rows, kinds))

    # ---- per (domain, slot) cell vectors ------------------------------------------------ #
    keep = {d for d, s in assign.items() if s == a.split} - set(EXCLUDED_DOMAINS)
    by_key = {}
    for r in rows:
        if r["domain"] not in keep:
            continue
        k = (r["domain"], family_slot(r["family_id"]))
        cell = r["cell"]
        if (k, cell) in by_key:
            raise Refusal("key %r cell %s binds two rows" % (k, cell))
        t = mp["reps"].get(r["prompt_id"])
        if t is None:
            raise Refusal("row %r has no multi-position stack" % r["prompt_id"])
        by_key[(k, cell)] = t.float()
    keys = sorted({k for (k, _) in by_key})
    complete = [k for k in keys if all((k, c) in by_key for c in ("A", "B", "C", "E"))]
    if not complete:
        raise Refusal("no (domain, slot) key has all four cells")
    print("[map]   %d complete 4-cell keys over %d domains (split=%s)"
          % (len(complete), len({d for d, _ in complete}), a.split))

    missing_y = [k for k in complete if k not in inst]
    if missing_y:
        raise Refusal("%d keys have a representation but NO installation target, e.g. %r"
                      % (len(missing_y), missing_y[:3]))

    domains = sorted({d for d, _ in complete})
    # per-domain target and per-domain contrast tensors [n_sites, n_layers, d]
    y = {}
    contrasts = {"C_minus_B": {}, "E_minus_A": {}, "interaction": {}, "C_minus_A_CONFOUNDED": {}}
    for dom in domains:
        ks = [k for k in complete if k[0] == dom]
        y[dom] = sum(inst[k] for k in ks) / len(ks)
        cb = sum((by_key[(k, "C")] - by_key[(k, "B")]) for k in ks) / len(ks)
        ea = sum((by_key[(k, "E")] - by_key[(k, "A")]) for k in ks) / len(ks)
        ca = sum((by_key[(k, "C")] - by_key[(k, "A")]) for k in ks) / len(ks)
        contrasts["C_minus_B"][dom] = cb
        contrasts["E_minus_A"][dom] = ea
        contrasts["interaction"][dom] = cb - ea
        contrasts["C_minus_A_CONFOUNDED"][dom] = ca

    n = len(domains)
    ys = [y[d] for d in domains]
    ybar = sum(ys) / n
    print("[map]   y_install over %d domains: mean %.4f min %.4f max %.4f"
          % (n, ybar, min(ys), max(ys)))

    cell_X = {}
    yt = torch.tensor(ys, dtype=torch.float32)

    result = {"schema": "dcs_cont_layerpos_map/1", "status": "EXPLORATORY",
              "beh_run": a.beh_run, "readout_run": a.readout_run, "split": a.split,
              "bank_file_sha16": bank_sha, "n_domains": n, "domains": domains,
              "sites": sites, "layers": layers,
              "y_install": {d: y[d] for d in domains},
              "contrast_note": ("C_minus_B and E_minus_A are register-matched; "
                                "C_minus_A_CONFOUNDED is reported ONLY as the confounded "
                                "comparator and must never be quoted as a result"),
              "map": {}}

    for cname, cvecs in contrasts.items():
        result["map"][cname] = {}
        for si, site in enumerate(sites):
            for li, L in enumerate(layers):
                X = torch.stack([cvecs[d][si, li] for d in domains], dim=0)
                cell_X["%s|%s|L%d" % (cname, site, L)] = X
                # LEAVE-ONE-DOMAIN-OUT covariance direction, scored on the held-out domain.
                # y-bar is recomputed WITHOUT the held-out domain; centring on the full-sample
                # mean lets domain i influence its own direction through y-bar. Measured over 200
                # null draws at n=67, d=4096 that leak is immaterial (mean rho -0.0134 leaky vs
                # -0.0141 fixed, both within noise of zero) -- it is removed because it is cheap
                # to remove, NOT because it was producing a wrong number.
                scores = [float(v) for v in loo_scores(X, yt)]
                rho = spearman(scores, ys)
                norms = [float(x.norm()) for x in X]
                result["map"][cname]["%s|L%d" % (site, L)] = {
                    "rho_loo": rho,
                    "mean_norm": sum(norms) / n,
                    "n_domains": n,
                }
    # ---- FAMILY-WISE PERMUTATION NULL ---------------------------------------------------- #
    # WHY THIS IS NOT OPTIONAL. This map has 4 contrasts x 20 sites x 19 layers = 1520 cells, each
    # a leave-one-out rho fitted in 4096 dimensions on 67 domains. Measured null sd of a SINGLE
    # cell is ~0.160, so the LARGEST of 1520 pure-noise cells lands near |rho| ~ 0.64 -- BIGGER
    # than this project's headline installation->ASR correlation. Reporting "the best cell in the
    # map" without this null would manufacture a discovery with near-certainty. The permutation
    # also handles the correlation between adjacent layers and sites, which a Bonferroni-style
    # count would not.
    g = torch.Generator().manual_seed(a.seed)
    Yperm = torch.stack([yt[torch.randperm(n, generator=g)] for _ in range(a.n_perm)], dim=0)
    per_family_max = {c: [] for c in contrasts}
    global_max = None
    for cname in contrasts:
        fam = None
        for key, X in cell_X.items():
            if not key.startswith(cname + "|"):
                continue
            S = loo_scores(X, Yperm)                       # [B, n]
            r = torch.tensor([abs(spearman([float(v) for v in S[b]], ys))
                              for b in range(a.n_perm)])
            fam = r if fam is None else torch.maximum(fam, r)
        per_family_max[cname] = fam
        global_max = fam.clone() if global_max is None else torch.maximum(global_max, fam)
    def pct(t, q):
        return float(t.sort().values[min(len(t) - 1, int(q * len(t)))])
    result["permutation_null"] = {
        "n_perm": a.n_perm, "seed": a.seed,
        "unit_shuffled": "domain label of y_install",
        "note": ("threshold a cell must EXCEED to be reportable; the family-wise max over a map "
                 "of pure noise, not a per-cell p-value"),
        "global": {"p50": pct(global_max, .50), "p95": pct(global_max, .95),
                   "p99": pct(global_max, .99), "max": float(global_max.max())},
        "per_contrast": {c: {"p50": pct(v, .50), "p95": pct(v, .95), "p99": pct(v, .99)}
                         for c, v in per_family_max.items()},
    }
    thr = result["permutation_null"]["global"]["p95"]
    n_exceed = 0
    for cname in result["map"]:
        for key, cell in result["map"][cname].items():
            cell["exceeds_fwer95"] = bool(abs(cell["rho_loo"]) > thr)
            n_exceed += int(cell["exceeds_fwer95"])
    result["permutation_null"]["n_cells"] = sum(len(v) for v in result["map"].values())
    result["permutation_null"]["n_cells_exceeding_fwer95"] = n_exceed

    out = os.path.join(REPO, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    print("[map] wrote %s" % a.out)

    pn = result["permutation_null"]
    print("[map] FAMILY-WISE NULL over %d permutations, %d cells:" % (pn["n_perm"], pn["n_cells"]))
    print("      max |rho| from PURE NOISE  p50=%.4f  p95=%.4f  p99=%.4f"
          % (pn["global"]["p50"], pn["global"]["p95"], pn["global"]["p99"]))
    print("      cells exceeding the p95 threshold: %d/%d"
          % (pn["n_cells_exceeding_fwer95"], pn["n_cells"]))
    for cname in ("C_minus_B", "E_minus_A", "interaction", "C_minus_A_CONFOUNDED"):
        best = sorted(result["map"][cname].items(), key=lambda kv: -abs(kv[1]["rho_loo"]))[:6]
        print("  %-22s top |rho_loo|: %s"
              % (cname, ", ".join("%s=%.4f" % (k, v["rho_loo"]) for k, v in best)))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        raise SystemExit(2)
