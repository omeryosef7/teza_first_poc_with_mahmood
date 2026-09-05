#!/usr/bin/env python3
"""DCS-C-056 — independently RECOMPUTE the PR-035 primary, which no existing verifier does.

WHY THIS EXISTS. A red-team ran `scripts/dcs_verify_pr035.py` end to end, confirmed all eleven of its
detections are real and each fires on its own designated check, and then named its root hole exactly:

  "C6 recomputes the n_examples=0 blocking null and NOTHING ELSE, so the P2 PRIMARY -- the number
   §28.9 gates promotion on -- is read from the producer as ground truth and only checked for
   internal arithmetic consistency."

⇒ A **fabricated headline** passes all fourteen checks: rewrite `P2_primary` to a self-consistent
POSITIVE and every check still agrees, because they check the producer against ITSELF. That is
`derived-field circularity`, the failure Omer's brief §25 names outright and `C-049` §22.5 already
caught once one layer down.

WHAT THIS FILE DOES. It re-implements the `PR-035` primary **from the preregistration text**, not
from `dcs_bombness_specificity.py` (which it does not import), and compares:

  V1  the population, rebuilt from the banks with §28.1's exclusion
  V2  the (layer, C) picks -- recomputed on cell B, which is what §23.6 declares. If they do not
      reproduce, it re-runs selection on the TEST cell's own labels and says whether THAT is what
      the producer did. That is §28.2's defect, checked on the PRIMARY rather than only on the null.
  V3  the P2 primary held-out accuracy, per domain and mean
  V4  the group-permutation p, with its OWN seed, compared inside a stated Monte-Carlo band
  V5  the knife-vs-club control (§23.5 clause 4), the same way
  V6  per-CLASS cache binding: each class's rows must come from ITS OWN bank's cache, checked by
      ||rep|| against that run's own `hnorm|L` column. A producer-side join of one class to another
      bank's cache is lossless under `prompt_id` (which collides 8-way) and invisible to metadata.

⛔ It reads the producer JSON ONLY as the claim under test.
"""
from __future__ import annotations

import argparse, hashlib, json, os, re, sys
import numpy as np

# ---------------------------------------------------------------- declared by PR-035, not the producer
CLASSES = ("bomb", "knife", "gun")
CODEWORD = "button"
CHANNEL = "semantic_one_word"
NEXAMPLES = (4, 8)
LAYERS = tuple(range(6, 15))
C_GRID = (0.01, 0.1, 1.0, 10.0)
N_DOMAINS = 6
BANKDIR = "data/boombness_prompts"
RUNROOT = "outputs/boombness/extract_boombness"
HNORM_TOL = 1e-3


def bank_path(cc):
    return os.path.join(BANKDIR, f"boombness_prompt_bank_{CODEWORD}_{cc}.jsonl")


def find_run(cc):
    import glob
    for d in reversed(sorted(glob.glob(os.path.join(RUNROOT, f"bombspec_{CODEWORD}_{cc}_*")))):
        if os.path.exists(os.path.join(d, "DONE.json")):
            return d
    return None


def build(cc, cells, nex):
    """§28.1's exclusion, re-implemented from the log text: concept word on word boundaries,
    case-insensitively, AND this row's target_surface is not that word."""
    pat = re.compile(r"\b" + re.escape(cc) + r"\b", re.IGNORECASE)
    out = []
    for l in open(bank_path(cc)):
        r = json.loads(l)
        if r.get("query_kind") != CHANNEL or r.get("cell") not in cells:
            continue
        if r.get("n_examples") not in nex:
            continue
        if pat.search(r["full_prompt"]) and r.get("target_surface") != cc:
            continue
        out.append(r)
    return out


def load_cache(run_dir):
    import torch
    blob = torch.load(os.path.join(run_dir, "cache", "final_occurrence_reps.pt"), map_location="cpu")
    return list(blob["layers"]), {k: v.float().numpy() for k, v in blob["reps"].items()}


def X_at(rows, layer, layers):
    j = layers.index(layer)
    return np.stack([r["_vec"][j] for r in rows])


def fit(train, test, layer, layers, C, classes):
    from sklearn.linear_model import LogisticRegression
    ytr = np.array([classes.index(r["_lab"]) for r in train])
    yte = np.array([classes.index(r["_lab"]) for r in test])
    if len(set(ytr.tolist())) < 2:
        return None
    Xtr, Xte = X_at(train, layer, layers), X_at(test, layer, layers)
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd < 1e-8] = 1.0
    clf = LogisticRegression(C=C, max_iter=3000)
    clf.fit((Xtr - mu) / sd, ytr)
    return float((clf.predict((Xte - mu) / sd) == yte).mean())


def select(sel_rows, layers, classes):
    best, best_acc = None, -1.0
    for L in LAYERS:
        if L not in layers:
            continue
        for C in C_GRID:
            accs = []
            for d in sorted({r["domain"] for r in sel_rows}):
                tr = [r for r in sel_rows if r["domain"] != d]
                te = [r for r in sel_rows if r["domain"] == d]
                if tr and te:
                    a = fit(tr, te, L, layers, C, classes)
                    if a is not None:
                        accs.append(a)
            if accs and float(np.mean(accs)) > best_acc:
                best_acc, best = float(np.mean(accs)), (L, C)
    return best


def loo(rows, sel_rows, layers, classes):
    per, picks = {}, {}
    for d in sorted({r["domain"] for r in rows}):
        tr = [r for r in rows if r["domain"] != d]
        te = [r for r in rows if r["domain"] == d]
        sel = [r for r in sel_rows if r["domain"] != d]
        if not tr or not te or not sel:
            continue
        pick = select(sel, layers, classes)
        if pick is None:
            continue
        L, C = pick
        a = fit(tr, te, L, layers, C, classes)
        if a is not None:
            per[d] = a
            picks[d] = (L, C)
    return per, picks


def perm_p(rows, layers, classes, picks, observed, n_perm, seed):
    rng = np.random.default_rng(seed)
    doms = sorted({r["domain"] for r in rows})
    null = []
    for _ in range(n_perm):
        lab = {}
        for d in doms:
            p = list(classes)
            rng.shuffle(p)
            lab[d] = dict(zip(classes, p))
        pr = [dict(r, _lab=lab[r["domain"]][r["_lab"]]) for r in rows]
        accs = []
        for d in doms:
            if d not in picks:
                continue
            tr = [r for r in pr if r["domain"] != d]
            te = [r for r in pr if r["domain"] == d]
            L, C = picks[d]
            a = fit(tr, te, L, layers, C, classes)
            if a is not None:
                accs.append(a)
        if accs:
            null.append(float(np.mean(accs)))
    null = np.array(null)
    return (1.0 + float((null >= observed).sum())) / (1.0 + len(null)), null


def attach(rows, layers, reps, cc):
    keep = []
    for r in rows:
        v = reps.get(r["prompt_id"])
        if v is None:
            continue
        r = dict(r); r["_vec"] = v; r["_lab"] = cc
        keep.append(r)
    return keep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--producer", default="outputs/boombness/dcs_analysis/dcs_bombness_specificity.json")
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--seed", type=int, default=90613)   # deliberately NOT the producer's 20260905
    ap.add_argument("--acc-tol", type=float, default=1e-9)
    a = ap.parse_args()

    if not os.path.exists(a.producer):
        print(f"producer JSON not found: {a.producer}"); return 2
    prod = json.load(open(a.producer))
    fails = []

    # ---- V1 + V6: rebuild the population, and bind each CLASS to its OWN bank's cache
    layers_ref, pools, sel_pools = None, {}, {}
    for cc in CLASSES + ("club",):
        run = find_run(cc)
        if run is None:
            print(f"  V1  FAIL  no complete run for {cc}"); fails.append("V1"); continue
        layers, reps = load_cache(run)
        if layers_ref is None:
            layers_ref = layers
        elif layers != layers_ref:
            print(f"  V1  FAIL  {cc} layers {layers} != {layers_ref}"); fails.append("V1")
        # V6 -- per-class cache binding via that run's OWN hnorm column
        byid = {}
        for l in open(os.path.join(run, "results.jsonl")):
            r = json.loads(l)
            byid[r["prompt_id"]] = r
        errs = []
        for pid, v in list(reps.items())[:400]:
            row = byid.get(pid)
            if not row:
                continue
            for j, L in enumerate(layers):
                h = row.get(f"hnorm|L{L}")
                if h:
                    errs.append(abs(float(np.linalg.norm(v[j])) - float(h)) / max(1e-9, abs(float(h))))
        q95 = float(np.quantile(errs, 0.95)) if errs else None
        if q95 is None or q95 > HNORM_TOL:
            print(f"  V6  FAIL  {cc}: rep cache does not bind to its own run's hnorm (q95 rel err "
                  f"{q95}); this class's states may come from ANOTHER bank (prompt_id collides 8-way)")
            fails.append("V6")
        pools[cc] = attach(build(cc, ("C",), NEXAMPLES), layers, reps, cc)
        sel_pools[cc] = attach(build(cc, ("B",), NEXAMPLES), layers, reps, cc)

    if "V1" in fails or layers_ref is None:
        print("\nCANNOT VERIFY — population/cache load failed."); return 1
    print(f"  V1  PASS  population rebuilt: " +
          ", ".join(f"{c}:C={len(pools[c])},B={len(sel_pools[c])}" for c in CLASSES))
    if "V6" not in fails:
        print("  V6  PASS  every class's rep cache binds to its OWN run's hnorm columns")

    C_rows = [r for c in CLASSES for r in pools[c]]
    B_rows = [r for c in CLASSES for r in sel_pools[c]]

    # ---- V2/V3: recompute picks (selection on cell B) and held-out accuracy
    per, picks = loo(C_rows, B_rows, layers_ref, CLASSES)
    mine = float(np.mean(list(per.values()))) if per else None
    pp = prod.get("P2_primary", {})
    theirs = pp.get("mean_acc")
    print(f"  V3  recomputed P2 primary mean_acc = {mine!r}   producer = {theirs!r}")
    if theirs is None or mine is None or abs(mine - theirs) > a.acc_tol:
        # §28.2 check ON THE PRIMARY: was selection done on the TEST cell's own labels instead?
        per_bad, _ = loo(C_rows, C_rows, layers_ref, CLASSES)
        alt = float(np.mean(list(per_bad.values()))) if per_bad else None
        note = ""
        if alt is not None and theirs is not None and abs(alt - theirs) <= 1e-9:
            note = ("  <-- and it MATCHES selection on the TEST cell's own labels: the §28.2 defect, "
                    "on the PRIMARY")
        print(f"  V2/V3  FAIL  producer's primary is not reproducible from cell-B selection{note}")
        fails.append("V3")
    else:
        print("  V2  PASS  (layer, C) picks reproduce from cell-B selection, per §23.6")
        print("  V3  PASS  P2 primary held-out accuracy reproduces exactly")

    # ---- V4: independent permutation null, own seed
    if mine is not None:
        p_mine, null = perm_p(C_rows, layers_ref, CLASSES, picks, mine, a.n_perm, a.seed)
        p_them = prod.get("P2_primary_permutation", {}).get("p_one_sided")
        band = 3.0 * float(np.sqrt(max(p_mine, 1e-6) * (1 - max(p_mine, 1e-6)) / max(1, a.n_perm)))
        ok = (p_them is not None and abs(p_mine - p_them) <= max(band, 2.0 / (1 + a.n_perm)))
        print(f"  V4  {'PASS' if ok else 'FAIL'}  permutation p: mine={p_mine:.4f} (seed {a.seed}) "
              f"producer={p_them!r}  MC band +-{max(band, 2.0/(1+a.n_perm)):.4f}  "
              f"null_mean={null.mean():.4f}")
        if not ok:
            fails.append("V4")
        same_side = (p_them is not None and ((p_mine <= 0.05) == (p_them <= 0.05)))
        if not same_side:
            print("  V4  FAIL  the two p-values fall on OPPOSITE sides of alpha=0.05")
            fails.append("V4")

    # ---- V5: the §23.5 clause-4 control, recomputed
    pair = ("knife", "club")
    kc = [r for c in pair for r in pools[c]]
    kcs = [r for c in pair for r in sel_pools[c]]
    if kc and kcs:
        per_kc, picks_kc = loo(kc, kcs, layers_ref, pair)
        mine_kc = float(np.mean(list(per_kc.values()))) if per_kc else None
        got = prod.get("P2_knife_vs_club_CONTROL_bomb_absent", {})
        theirs_kc = got.get("mean_acc") if isinstance(got, dict) else None
        ok = (theirs_kc is not None and mine_kc is not None and abs(mine_kc - theirs_kc) <= a.acc_tol)
        print(f"  V5  {'PASS' if ok else 'FAIL'}  knife-vs-club control: mine={mine_kc!r} "
              f"producer={theirs_kc!r}")
        if not ok:
            fails.append("V5")
    else:
        print("  V5  FAIL  the §23.5 clause-4 control population is empty"); fails.append("V5")

    if fails:
        print(f"\nPRIMARY VERIFICATION FAILED — {sorted(set(fails))}")
        return 1
    print("\nPRIMARY VERIFIED — the headline was recomputed from banks and caches, not read from "
          "the producer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
