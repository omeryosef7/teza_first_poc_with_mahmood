#!/usr/bin/env python3
"""Export the TRAIN-ONLY installation axis (and its matched controls) for the Phase-1 subspace rescue.

WHAT THIS PRODUCES. A single `.pt` holding an orthonormal basis per NAMED candidate, plus full
provenance, to be consumed by `score_behavior.py --rescue-basis`. Candidates:

  cand_rank1        rank-1 ridge direction  (the installation axis)
  cand_pls{r}       rank-r PLS1 subspace with EXPLICIT deflation, r = 1..--max-rank
  ctrl_orth         a direction orthogonal to cand_rank1                (same-norm control)
  ctrl_random{i}    i.i.d. Gaussian directions                          (control DISTRIBUTION)
  ctrl_shuffled{j}  the identical ridge fit on DOMAIN-PRESERVING shuffled labels

WHY THE CONTROLS LIVE IN THE SAME FILE. They must be built from the same rows, the same split, the
same centring and the same fit as the candidate. A control assembled later by different code is a
control that differs from the candidate in more ways than the one under test.

TRAIN ONLY, ENFORCED. The fit population is the TRAIN split minus EXCLUDED_DOMAINS. The script
REFUSES if any validation or test domain reaches the fit, and refuses if the corpus contains test
rows at all. Layer/rank selection is nested inside TRAIN (leave-one-domain-out), never on
VALIDATION and never on TEST.

TWO CANDIDATE FAMILIES, DELIBERATELY. `--fit-prompt semantic` fits on the semantic_one_word
forward -- the SAME forward the Phase-1 intervention acts on, which is the representation the
causal claim is about, but which shares a forward pass with the readout and is therefore NOT a
clean observational claim. `--fit-prompt behavioral` fits on the behavioural forward, which is the
non-circular lineage the existing Q1 probe used, and asks whether that axis TRANSFERS. Both are
frozen before VALIDATION; VALIDATION adjudicates between them (plan section 4.2). Neither is
selected on TEST.

SITE. The site is NOT re-searched: it is frozen to the prior winner (`--site`, default rel-6) so
this script adds no new multiple-comparison burden. Only the LAYER and the RANK are selected, on
TRAIN, and both selections are recorded with their full grids.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import statistics
import sys

import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAM = 100.0                                   # the phase's fixed ridge; not retuned per site
PLATEAU = [16, 18, 20, 22, 24, 26, 28, 30, 31]


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s)
    sys.modules[mod] = m
    s.loader.exec_module(m)
    return m


# ------------------------------------------------------------------------------ feature assembly
def build(lpm, mp, rows, inst, sites_all, layers_all, keep, site, layer, cell="C"):
    """Within-domain-centred features and labels at one (site, layer, cell).

    Identical construction to `dcs_cont_qprobe.build` (slice-before-float from the mmap'd store,
    complete-ABCE slots only, within-domain centring of BOTH X and y, duplicate-key refusal), so
    the axis is fit on exactly the population the query-probe result was measured on.
    """
    si = sites_all.index(site)
    li = layers_all.index(layer)
    byk = {}
    for r in rows:
        if r["domain"] not in keep:
            continue
        t = mp["reps"].get(r["prompt_id"])
        if t is None:
            continue
        k = ((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])
        if k in byk:
            raise SystemExit("duplicate key %r -- silent channel substitution" % (k,))
        byk[k] = t[si, li].float()
    comp = [k for k in sorted({k for k, _ in byk}) if all((k, c) in byk for c in "ABCE")]
    comp = [k for k in comp if k in inst]
    doms = sorted({d for d, _ in comp})
    xs, ys, dof, keys = [], [], [], []
    for d in doms:
        ks = [k for k in comp if k[0] == d]
        V = torch.stack([byk[(k, cell)] for k in ks], 0)
        xs.append(V - V.mean(0, keepdim=True))
        yv = [inst[k] for k in ks]
        m = statistics.mean(yv)
        ys += [v - m for v in yv]
        dof += [d] * len(ks)
        keys += ks
    if not xs:
        raise SystemExit("build() bound ZERO rows for site=%r layer=%r -- missing != empty"
                         % (site, layer))
    return (torch.cat(xs, 0).double(), torch.tensor(ys, dtype=torch.float64), dof, doms, keys)


# --------------------------------------------------------------------------------------- fitting
def ridge_w(X, y, lam=LAM):
    """Primal ridge weight via the dual: w = X^T (XX^T + lam I)^-1 y.

    The dual is used because n (rows) is ~700 and hidden is 4096, so the n-by-n solve is both
    cheaper and better conditioned than the 4096-by-4096 one.
    """
    K = X @ X.T
    al = torch.linalg.solve(K + lam * torch.eye(len(y), dtype=torch.float64), y)
    return X.T @ al


def loo_rho(lpm, X, y, dof, doms, lam=LAM):
    """Leave-one-DOMAIN-out Spearman. The independence unit is the domain, so the fold is too."""
    K = X @ X.T
    pred = [0.0] * len(y)
    for d in doms:
        te = [i for i, x in enumerate(dof) if x == d]
        tr = [i for i, x in enumerate(dof) if x != d]
        ti, ei = torch.tensor(tr), torch.tensor(te)
        al = torch.linalg.solve(K[ti][:, ti] + lam * torch.eye(len(tr), dtype=torch.float64), y[ti])
        p = K[ei][:, ti] @ al
        for j, i in enumerate(te):
            pred[i] = float(p[j])
    return lpm.spearman(pred, y.tolist()), pred


def pls1(X, y, r):
    """PLS1 (NIPALS) returning the rank-r weight matrix [r, hidden], WITH DEFLATION.

    Deflation is the whole point and is called out here because this phase has already shipped a
    'one-dimensional' claim that was wrong precisely because the components were never deflated:
    without deflating X, every component collapses onto the same direction and 'rank r' is rank 1
    wearing a hat.
    """
    Xr = X.clone()
    yr = y.clone()
    W = []
    for _ in range(r):
        w = Xr.T @ yr
        n = w.norm()
        if float(n) < 1e-12:
            break
        w = w / n
        t = Xr @ w
        tt = float(t @ t)
        if tt < 1e-18:
            break
        p = (Xr.T @ t) / tt
        Xr = Xr - torch.outer(t, p)
        yr = yr - (float(t @ yr) / tt) * t
        W.append(w)
    if not W:
        raise SystemExit("pls1 produced no components")
    return torch.stack(W, 0)


def subspace_loo_rho(lpm, X, y, dof, doms, r):
    """LOO-by-domain score of a rank-r PLS subspace: fit PLS + an OLS head inside each fold."""
    pred = [0.0] * len(y)
    for d in doms:
        te = [i for i, x in enumerate(dof) if x == d]
        tr = [i for i, x in enumerate(dof) if x != d]
        ti, ei = torch.tensor(tr), torch.tensor(te)
        W = pls1(X[ti], y[ti], r)                       # [r, hidden], fit on the fold ONLY
        Ztr, Zte = X[ti] @ W.T, X[ei] @ W.T
        beta = torch.linalg.lstsq(Ztr, y[ti].unsqueeze(1)).solution.squeeze(1)
        p = Zte @ beta
        for j, i in enumerate(te):
            pred[i] = float(p[j])
    return lpm.spearman(pred, y.tolist())


def shuffled_y(y, dof, doms, seed):
    """Permute labels WITHIN domain, preserving each domain's label multiset.

    A global shuffle would also destroy the between-domain structure, and a candidate fit on that
    is an easier straw man than the one we need: the controls must be as strong as the candidate
    in every respect except the label-feature association being tested.
    """
    g = torch.Generator().manual_seed(seed)
    yp = y.clone()
    for d in doms:
        idx = [i for i, x in enumerate(dof) if x == d]
        pm = torch.randperm(len(idx), generator=g)
        for j, i in enumerate(idx):
            yp[i] = y[idx[pm[j]]]
    return yp


def sha16(t: torch.Tensor) -> str:
    return hashlib.sha256(t.to(torch.float64).contiguous().numpy().tobytes()).hexdigest()[:16]


# ------------------------------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--corpus", required=True, help="extract_boombness run dir (states)")
    ap.add_argument("--readout", required=True, help="score_behavior run dir (y_install)")
    ap.add_argument("--fit-prompt", required=True, choices=("semantic", "behavioral"),
                    help="which forward the corpus is from; recorded in provenance AND checked "
                         "against the corpus rows. 'semantic' opts in to a semantic corpus, which "
                         "the shared loader refuses by default -- legitimate ONLY because this "
                         "fit's output is a direction to intervene along, never a predictive "
                         "claim. A rho from a semantic fit MUST NOT be reported as prediction.")
    ap.add_argument("--site", default="rel-6", help="FROZEN prior winner; not re-searched here")
    ap.add_argument("--max-rank", type=int, default=5)
    ap.add_argument("--n-random", type=int, default=8)
    ap.add_argument("--n-shuffled", type=int, default=5)
    ap.add_argument("--rank-controls", default="",
                    help="comma list of ranks needing matched controls, e.g. '5'. For each, emits "
                         "random rank-r subspaces and rank-r PLS fits on shuffled labels. Without "
                         "these a rank-r candidate has no comparator at its own rank and its "
                         "advantage over rank 1 is confounded with dose (DCS-CSI-048).")
    ap.add_argument("--n-random-rank", type=int, default=6)
    ap.add_argument("--n-shuffled-rank", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20260915)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    assign = lpm.load_split()
    EX = set(lpm.EXCLUDED_DOMAINS)
    TR = {d for d, v in assign.items() if v == "train"} - EX
    VA = {d for d, v in assign.items() if v == "validation"} - EX
    TE = {d for d, v in assign.items() if v == "test"}
    if not TR:
        raise SystemExit("REFUSING: empty TRAIN split")

    inst, n_inst, kinds = lpm.load_installation(os.path.join(REPO, a.readout))
    # Opt in to a semantic corpus ONLY when the caller declared --fit-prompt semantic. The
    # justification is written out in lpm.load_corpus: this fit's output is a direction to
    # INTERVENE along, not a predictive claim. `--fit-prompt` is itself checked against the
    # corpus below, so this cannot be used to smuggle a semantic corpus in under a behavioural
    # label.
    _allow = ("semantic_one_word",) if a.fit_prompt == "semantic" else ("behavioral",)
    mp, rows, csha = lpm.load_corpus(os.path.join(REPO, a.corpus), mmap=True,
                                     allow_query_kinds=_allow)
    rsha, rsrc = lpm.readout_bank_sha(os.path.join(REPO, a.readout))
    if rsha != csha:
        raise SystemExit("REFUSING: corpus bank_sha %s != readout bank_sha %s (%s) -- a mismatched "
                         "pair would pool codewords silently" % (csha, rsha, rsrc))
    # REVIEW M1. `--fit-prompt` was a free-text LABEL written into the artifact's provenance and
    # never checked against the corpus it describes. An artifact that misdescribes its own fit
    # population is worse than no provenance. Derive the truth from the rows and refuse a mismatch.
    qks = {r.get("query_kind") for r in rows}
    if len(qks) != 1:
        raise SystemExit("REFUSING: corpus mixes query kinds %s" % sorted(qks))
    actual = "semantic" if list(qks)[0] == "semantic_one_word" else list(qks)[0]
    if actual != a.fit_prompt:
        raise SystemExit("REFUSING: --fit-prompt %r but the corpus carries query_kind %r. The "
                         "artifact's provenance must not be able to misdescribe its own fit "
                         "population." % (a.fit_prompt, list(qks)[0]))
    # The 2x2 design means the corpus legitimately carries BOTH surfaces: cells A/C put the
    # codeword in the surface slot, cells B/E put the concept there. So the check is not "every
    # row is the codeword" -- that refused a correct corpus on the first attempt (job 896396) --
    # but "the cell this fit actually uses carries the codeword". Cell C is that cell.
    cws_C = {r.get("target_surface") for r in rows
             if r.get("cell") == "C" and r.get("target_surface")}
    if cws_C and cws_C != {a.codeword}:
        raise SystemExit("REFUSING: --codeword %r but the corpus's cell-C rows carry "
                         "target_surface %s" % (a.codeword, sorted(cws_C)))
    corpus_doms = {r["domain"] for r in rows}
    leak = sorted(d for d in corpus_doms if assign.get(d) == "test")
    if leak:
        raise SystemExit("REFUSING: corpus contains TEST domains: %s" % leak[:5])

    sites_all = list(mp["sites"])
    layers_all = list(mp["layers"])
    if a.site not in sites_all:
        raise SystemExit("REFUSING: site %r not captured (have %s)" % (a.site, sites_all))
    layers = [L for L in PLATEAU if L in layers_all]
    if not layers:
        raise SystemExit("REFUSING: no plateau layer captured (have %s)" % layers_all)

    # ---- TRAIN-only fit population, with the disjointness assertions stated as refusals --------
    fit_doms = sorted(corpus_doms & TR)
    if not fit_doms:
        raise SystemExit("REFUSING: no TRAIN domain in this corpus")
    bad = [d for d in fit_doms if d in VA or d in TE or d in EX]
    if bad:
        raise SystemExit("REFUSING: fit population is contaminated: %s" % bad[:5])

    out = {"schema": "dcs_csi_axis/1", "codeword": a.codeword, "fit_prompt": a.fit_prompt,
           "corpus": a.corpus, "readout": a.readout, "bank_sha16": csha,
           "site": a.site, "lambda": LAM, "seed": a.seed,
           "installation_rows": n_inst, "installation_channels_present": kinds,
           "split_manifest": os.path.relpath(lpm.SPLIT_MANIFEST, REPO),
           "excluded_domains": sorted(EX),
           "fit_population": {"split": "train", "n_domains": len(fit_doms), "domains": fit_doms,
                              # REVIEW M4: a short, row-portable fingerprint of the exact fit
                              # population, so a scoring run can record WHICH domains the axis saw
                              # and an analysis can detect in-sample scoring without trusting a
                              # stdout line that nobody kept.
                              "domains_sha16": hashlib.sha256(
                                  "|".join(fit_doms).encode()).hexdigest()[:16]},
           "held_out_validation_domains": sorted(corpus_doms & VA),
           "layer_grid": layers, "train_loo_rho_by_layer": {}}

    # ---- LAYER selection, nested in TRAIN ------------------------------------------------------
    best = None
    for L in layers:
        X, y, dof, doms, _ = build(lpm, mp, rows, inst, sites_all, layers_all, set(fit_doms), a.site, L)
        rho, _ = loo_rho(lpm, X, y, dof, doms)
        out["train_loo_rho_by_layer"]["L%d" % L] = round(rho, 4)
        print("  L%-3d  train LOO rho = %+.4f   (%d rows / %d domains)" % (L, rho, len(y), len(doms)))
        if best is None or rho > best[1]:
            best = (L, rho)
    layer, train_rho = best
    if a.force_layer:
        # FORCE THE LAYER (DCS-CSI-073). The candidate's layer must match the layer the CAUSAL
        # evidence was measured at: the position map, KO_FULL and every position arm ran at L20.
        # Taking this axis's own argmax and then WRITING it at L20 would trip review M2's
        # layer-mismatch refusal, and rightly so -- a basis fit at one layer written at another is a
        # different experiment. Overriding that guard would be the wrong fix; fitting AT the layer
        # is the right one, and the artifact then records `selected_layer` honestly.
        if a.force_layer not in layers:
            raise SystemExit("REFUSING: --force-layer %d not among the captured plateau layers %s"
                             % (a.force_layer, layers))
        print("[force-layer] argmax was L%d (rho=%+.4f); forcing L%d (rho=%+.4f) to match the layer "
              "the causal position map was measured at"
              % (layer, train_rho, a.force_layer, out["train_loo_rho_by_layer"]["L%d" % a.force_layer]))
        layer = a.force_layer
        train_rho = out["train_loo_rho_by_layer"]["L%d" % layer]
        out["layer_forced"] = True
        out["layer_argmax_not_used"] = best[0]
    print("\n[TRAIN] selected layer L%d  rho_loo=%+.4f  (site %s FROZEN, not searched)"
          % (layer, train_rho, a.site))

    X, y, dof, doms, keys = build(lpm, mp, rows, inst, sites_all, layers_all,
                                  set(fit_doms), a.site, layer)
    out["selected_layer"] = layer
    out["train_loo_rho_at_selected_layer"] = round(train_rho, 4)
    out["n_fit_rows"] = len(y)
    out["n_fit_domains"] = len(doms)
    out["hidden_dim"] = int(X.shape[1])

    bases = {}

    # ---- rank-1 candidate ----------------------------------------------------------------------
    w = ridge_w(X, y)
    bases["cand_rank1"] = (w / w.norm()).unsqueeze(0)

    # ---- rank-r PLS candidates, with nested-TRAIN rank selection -------------------------------
    out["train_loo_rho_by_rank"] = {}
    for r in range(1, a.max_rank + 1):
        try:
            rho_r = subspace_loo_rho(lpm, X, y, dof, doms, r)
        except SystemExit:
            break
        out["train_loo_rho_by_rank"]["r%d" % r] = round(rho_r, 4)
        bases["cand_pls%d" % r] = pls1(X, y, r)
        print("  PLS r=%d  train LOO rho = %+.4f" % (r, rho_r))
    if out["train_loo_rho_by_rank"]:
        br = max(out["train_loo_rho_by_rank"], key=lambda k: out["train_loo_rho_by_rank"][k])
        out["selected_rank"] = int(br[1:])
        out["selected_rank_train_rho"] = out["train_loo_rho_by_rank"][br]
        print("\n[TRAIN] selected rank %s (rho=%+.4f). NOTE: a rank chosen on TRAIN is a "
              "candidate, not a finding; VALIDATION adjudicates."
              % (br, out["selected_rank_train_rho"]))

    # ---- controls -------------------------------------------------------------------------------
    g = torch.Generator().manual_seed(a.seed)
    w1 = bases["cand_rank1"][0]
    v = torch.randn(X.shape[1], generator=g, dtype=torch.float64)
    v = v - (v @ w1) * w1
    bases["ctrl_orth"] = (v / v.norm()).unsqueeze(0)
    for i in range(a.n_random):
        u = torch.randn(X.shape[1], generator=g, dtype=torch.float64)
        bases["ctrl_random%d" % i] = (u / u.norm()).unsqueeze(0)
    shuf_rho = {}
    for j in range(a.n_shuffled):
        yp = shuffled_y(y, dof, doms, a.seed + 1000 + j)
        ws = ridge_w(X, yp)
        bases["ctrl_shuffled%d" % j] = (ws / ws.norm()).unsqueeze(0)
        shuf_rho["ctrl_shuffled%d" % j] = round(loo_rho(lpm, X, yp, dof, doms)[0], 4)

    # ---- RANK-MATCHED controls (DCS-CSI-048) ---------------------------------------------------
    # The frozen control set is entirely RANK 1, so a rank-r candidate has nothing to be compared
    # against at its own rank: its advantage over the rank-1 axis is confounded with DOSE, because a
    # rank-r subspace captures ~sqrt(r/d) of any vector before any information enters. These supply
    # the missing comparator at each requested rank: a RANDOM rank-r subspace (pure geometry) and a
    # rank-r PLS fit on DOMAIN-PRESERVING SHUFFLED labels (same fitting procedure, same
    # dimensionality, no real label-feature association).
    for R in [int(x) for x in a.rank_controls.split(",") if x.strip()]:
        for i in range(a.n_random_rank):
            M = torch.randn(R, X.shape[1], generator=g, dtype=torch.float64)
            bases["ctrl_random_r%d_%d" % (R, i)] = torch.linalg.qr(M.T)[0].T.contiguous()
        for j in range(a.n_shuffled_rank):
            yp = shuffled_y(y, dof, doms, a.seed + 5000 + 100 * R + j)
            bases["ctrl_shuffled_pls%d_%d" % (R, j)] = pls1(X, yp, R)
    out["shuffled_control_train_loo_rho"] = shuf_rho
    print("\n[controls] shuffled-label TRAIN LOO rho (should sit near 0): %s"
          % json.dumps(shuf_rho))

    # ---- geometry of the controls relative to the candidate, recorded ---------------------------
    cos = {}
    for k, B in bases.items():
        if k == "cand_rank1":
            continue
        cos[k] = round(float((B @ w1).abs().max()), 4)
    out["max_abs_cosine_with_cand_rank1"] = cos
    if cos.get("ctrl_orth", 1.0) > 1e-9:
        raise SystemExit("REFUSING: ctrl_orth is not orthogonal to the candidate (cos=%g)"
                         % cos["ctrl_orth"])

    out["bases"] = {k: {"rank": int(B.shape[0]), "sha16": sha16(B)} for k, B in bases.items()}
    torch.save({"meta": out, "bases": {k: B.to(torch.float32) for k, B in bases.items()}},
               os.path.join(REPO, a.out))
    json.dump(out, open(os.path.join(REPO, a.out.replace(".pt", ".json")), "w"), indent=1)
    print("\nwrote %s  (%d bases)" % (a.out, len(bases)))
    print("     %s" % a.out.replace(".pt", ".json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
