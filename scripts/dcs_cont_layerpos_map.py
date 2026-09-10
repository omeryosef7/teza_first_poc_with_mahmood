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


def readout_bank_sha(run_dir: str):
    """The readout run's bank sha, read from metadata.json because its ROWS do not carry one.

    The log declared the join key as `(bank_file_sha16, domain, family_slot)`. That key was NOT
    constructible: readout rows have no `bank_file_sha16` field, so nothing was checking the bank
    at all. A `basket_*` readout joins every TRAIN key of a `button` corpus silently -- the only
    structurally differing keys live in `school_campus`, a domain the analyzer drops before it
    would notice -- swapping the target's mean from 0.678 to 0.045 and violating the
    never-pool-button-and-basket rule. REVIEW-1/T0-4.
    """
    for name in ("metadata.json", "config.json", "summary.json", "RUNMETA.json"):
        p = os.path.join(run_dir, name)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            blob = json.load(fh)
        for k in ("bank_file_sha16", "bank_sha16", "rows_sha16"):
            if isinstance(blob, dict) and blob.get(k):
                return str(blob[k]), "%s:%s" % (name, k)
        args = blob.get("args") if isinstance(blob, dict) else None
        if isinstance(args, dict) and args.get("bank"):
            import hashlib
            bp = args["bank"]
            if not os.path.isabs(bp):
                bp = os.path.join(REPO, bp)
            if os.path.exists(bp):
                h = hashlib.sha256(open(bp, "rb").read()).hexdigest()[:16]
                return h, "%s:args.bank(hashed)" % name
    raise Refusal("cannot establish the readout run's bank identity from %r; the join key the "
                  "log declares is not constructible without it" % run_dir)


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
            k = (r["domain"], family_slot(r["family_id"]))
            if k in out:
                # The corpus loader refuses on exactly this condition. Without the same refusal
                # here, weakening the semantic_one_word filter above would substitute the
                # forbidden forced-choice channel SILENTLY, last-row-in-file-order winning.
                raise Refusal("installation key %r binds two rows (query_kind=%r); the "
                              "concept-free channel filter is the only thing keeping the "
                              "forced-choice channel out, so a duplicate here is a silent "
                              "channel substitution" % (k, r.get("query_kind")))
            out[k] = p
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
    # ⛔ EVERY CHEAP REFUSAL RUNS BEFORE THE EXPENSIVE LOAD. multiposition_reps.pt is ~12 GB over
    # NFS and takes ~30 minutes to read; rejecting a one-word mistake in the run name should not
    # cost that. results.jsonl answers every identity question on its own.
    rows = [json.loads(l) for l in open(os.path.join(run_dir, "results.jsonl"), encoding="utf-8")]
    shas = {r.get("bank_file_sha16") for r in rows}
    if len(shas) != 1:
        raise Refusal("run %r mixes bank_file_sha16 %s" % (run_dir, shas))
    # ⛔ THE CORPUS MUST PROVE WHICH POPULATION IT IS. Two sibling corpora now exist one word
    # apart in the directory name -- cont1_behavioral_* and cont1_semantic_one_word_* -- with
    # identical row counts, cells, domains, sites and layers. Passing the semantic one here would
    # reinstate exactly the output-adjacency circularity CONT-ENTRY 002 exists to forbid, and
    # nothing printed would show it. REVIEW-1/T0-4.
    qks = {r.get("query_kind") for r in rows}
    if qks != {"behavioral"}:
        raise Refusal("the predictor corpus must be the BEHAVIOURAL population; %r carries "
                      "query_kind %s. The semantic prompt's next token IS the target, so a "
                      "representation read there predicts it circularly." % (run_dir, sorted(qks)))
    doses = {r.get("n_examples") for r in rows}
    if doses != {4}:
        raise Refusal("corpus %r carries doses %s; this analysis is dose 4 only"
                      % (run_dir, sorted(doses)))
    mp = torch.load(mp_path, weights_only=False)
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
    ro_sha, ro_src = readout_bank_sha(os.path.join(REPO, a.readout_run))
    if ro_sha != bank_sha:
        raise Refusal("BANK MISMATCH: corpus bank_file_sha16=%s but readout bank=%s (from %s). "
                      "Predictor and target must come from the same bank; button and basket are "
                      "never pooled." % (bank_sha, ro_sha, ro_src))
    print("[map]   bank agreement: corpus %s == readout %s (%s)" % (bank_sha, ro_sha, ro_src))
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
    # NAMING IS LOAD-BEARING HERE. C = (harm demos, surface ` button`) and B = (harm demos,
    # surface ` bomb`), so `C - B` is register-matched AND a pure lexical token swap; `E - A` is
    # the same swap in the OPPOSITE polarity under benign demos (measured cos(mean C-B, mean E-A)
    # = -0.87). Being register-matched does not make a contrast concept-informative, and a cell
    # that fires on `C_minus_B` is reporting `button` vs `bomb`, not installation.
    #
    # THE SIGN. Verified symbolically: (C-A)-(B-E) = (C-B)+(E-A) = -A-B+C+E is the interaction;
    # (C-B)-(E-A) = A-B+C-E = (C+A)-(B+E) is TWICE THE SURFACE MAIN EFFECT. This file previously
    # computed `cb - ea` under the name `interaction` -- the log's prose (CONT-ENTRY 003) and the
    # frozen convention in dcs_succ_bombness_candidates.py:449 were both right; only the code
    # disagreed. REVIEW-1/T0-2. The main effect is now reported under its own name rather than
    # deleted, because it is the confound this map most needs to print.
    contrasts = {"interaction": {}, "C_minus_B_LEXICAL": {}, "E_minus_A_LEXICAL": {},
                 "token_main_effect_LEXICAL": {}, "C_minus_A_CONFOUNDED": {}}
    for dom in domains:
        ks = [k for k in complete if k[0] == dom]
        y[dom] = sum(inst[k] for k in ks) / len(ks)
        cb = sum((by_key[(k, "C")] - by_key[(k, "B")]) for k in ks) / len(ks)
        ea = sum((by_key[(k, "E")] - by_key[(k, "A")]) for k in ks) / len(ks)
        ca = sum((by_key[(k, "C")] - by_key[(k, "A")]) for k in ks) / len(ks)
        contrasts["C_minus_B_LEXICAL"][dom] = cb
        contrasts["E_minus_A_LEXICAL"][dom] = ea
        contrasts["interaction"][dom] = cb + ea            # (C-B)+(E-A) == (C-A)-(B-E)
        contrasts["token_main_effect_LEXICAL"][dom] = cb - ea   # == (C+A)-(B+E), 2x main effect
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
              "bank_file_sha16": bank_sha, "readout_bank_sha16": ro_sha,
              "readout_bank_sha_source": ro_src,
              "corpus_query_kind": "behavioral", "corpus_dose": 4, "n_domains": n, "domains": domains,
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
    # The confounded comparator is EXCLUDED from the family-wise maximum. It may never be quoted
    # as a result, so letting its 380 cells inflate the threshold would tax the three reportable
    # families for a family that cannot report anything. REVIEW-1/S7.
    REPORTABLE = tuple(c for c in contrasts if c != "C_minus_A_CONFOUNDED")
    for cname in contrasts:
        fam = None
        for key, X in cell_X.items():
            if not key.startswith(cname + "|"):
                continue
            S = loo_scores(X, Yperm)                       # [B, n]
            # ⛔ SCORE AGAINST THE PERMUTED LABELS, NOT `ys`. The statistic is "fit a LOO
            # direction to labels L, then correlate the resulting scores WITH L". A null draw
            # must therefore recompute BOTH halves under the same permutation. Fitting on
            # Yperm[b] and correlating against the true ys prices in the map's multiplicity but
            # NONE of the fit-and-score optimism -- REVIEW-1/CODE-01 measured the consequence at
            # the real dimensions: the gate fired on pure noise in 4 of 8 datasets against a
            # nominal 5%, and the claimed p95 (0.401) sat at the MEAN of the true H0 maximum
            # (0.395). It also inflated to p95=0.97 once a real signal was present, masking the
            # rest of the map. The corrected form flagged 0 of 28 pure-noise datasets.
            r = torch.tensor([abs(spearman([float(v) for v in S[b]],
                                           [float(z) for z in Yperm[b]]))
                              for b in range(a.n_perm)])
            fam = r if fam is None else torch.maximum(fam, r)
        per_family_max[cname] = fam
        if cname in REPORTABLE:
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
    result["permutation_null"]["reportable_families"] = list(REPORTABLE)
    result["permutation_null"]["excluded_from_family_max"] = ["C_minus_A_CONFOUNDED"]
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
    for cname in ("interaction", "C_minus_B_LEXICAL", "E_minus_A_LEXICAL",
                  "token_main_effect_LEXICAL", "C_minus_A_CONFOUNDED"):
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
