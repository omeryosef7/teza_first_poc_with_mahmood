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

import argparse, copy, hashlib, json, os, re, sys, tempfile
import numpy as np

# ---------------------------------------------------------------- declared by PR-035, not the producer
CLASSES = ("bomb", "knife", "gun")
CODEWORD = "button"
CHANNEL = "semantic_one_word"
NEXAMPLES = (4, 8)
LAYERS = tuple(range(6, 15))
C_GRID = (0.01, 0.1, 1.0, 10.0)
# --fast shrinks the grid FOR THE MUTATION HARNESS ONLY. The harness proves that each CHECK FIRES;
# the check logic (recompute, compare, tolerance) does not depend on how large the grid is. The
# real verification run always uses the full declared grid above.
FAST_LAYERS = (6, 10)
FAST_C = (1.0,)
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


def select(sel_rows, layers, classes, grid=None):
    Ls, Cs = grid if grid else (LAYERS, C_GRID)
    best, best_acc = None, -1.0
    for L in Ls:
        if L not in layers:
            continue
        for C in Cs:
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


def loo(rows, sel_rows, layers, classes, grid=None):
    per, picks = {}, {}
    for d in sorted({r["domain"] for r in rows}):
        tr = [r for r in rows if r["domain"] != d]
        te = [r for r in rows if r["domain"] == d]
        sel = [r for r in sel_rows if r["domain"] != d]
        if not tr or not te or not sel:
            continue
        pick = select(sel, layers, classes, grid)
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


def load_all():
    """Load every class's population and bind it to its OWN run's cache. Returns (pools, sel, layers,
    bind) where `bind` is the per-class q95 relative error of ||rep|| against that run's hnorm."""
    layers_ref, pools, sel_pools, bind = None, {}, {}, {}
    for cc in CLASSES + ("club",):
        run = find_run(cc)
        if run is None:
            raise SystemExit(f"no complete run for {cc}")
        layers, reps = load_cache(run)
        if layers_ref is None:
            layers_ref = layers
        elif layers != layers_ref:
            raise SystemExit(f"{cc} layers {layers} != {layers_ref}")
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
        bind[cc] = float(np.quantile(errs, 0.95)) if errs else None
        pools[cc] = attach(build(cc, ("C",), NEXAMPLES), layers, reps, cc)
        sel_pools[cc] = attach(build(cc, ("B",), NEXAMPLES), layers, reps, cc)
    return pools, sel_pools, layers_ref, bind


def run_checks(prod, pools, sel_pools, layers, bind, *, grid=None, n_perm=200, seed=90613,
               acc_tol=1e-9, quiet=False):
    fails, out = [], []

    def say(t):
        out.append(t)
        if not quiet:
            print(t)

    # V1 / V6
    say(f"  V1  population: " + ", ".join(f"{c}:C={len(pools[c])},B={len(sel_pools[c])}" for c in CLASSES))
    for cc in CLASSES + ("club",):
        if bind.get(cc) is None or bind[cc] > HNORM_TOL:
            say(f"  V6  FAIL  {cc}: rep cache does not bind to its own run's hnorm (q95 {bind.get(cc)}); "
                f"this class's states may come from ANOTHER bank (prompt_id collides 8-way)")
            fails.append("V6")
    if "V6" not in fails:
        say("  V6  PASS  every class's rep cache binds to its OWN run's hnorm columns")

    exp = {c: (228, 48) for c in CLASSES}
    for c in CLASSES:
        if (len(pools[c]), len(sel_pools[c])) != exp[c]:
            say(f"  V1  FAIL  {c}: population {(len(pools[c]), len(sel_pools[c]))} != {exp[c]} "
                f"(§28.1's exclusion did not produce the declared table)")
            fails.append("V1")
    if "V1" not in fails:
        say("  V1  PASS  population rebuilt to §28.1's declared table (228 cell-C / 48 cell-B per class)")

    C_rows = [r for c in CLASSES for r in pools[c]]
    B_rows = [r for c in CLASSES for r in sel_pools[c]]

    per, picks = loo(C_rows, B_rows, layers, CLASSES, grid)
    mine = float(np.mean(list(per.values()))) if per else None
    pp = prod.get("P2_primary", {}) or {}
    theirs = pp.get("mean_acc")
    say(f"  V3  recomputed P2 primary mean_acc = {mine!r}   producer = {theirs!r}")
    if theirs is None or mine is None or abs(mine - theirs) > acc_tol:
        per_bad, _ = loo(C_rows, C_rows, layers, CLASSES, grid)
        alt = float(np.mean(list(per_bad.values()))) if per_bad else None
        note = ""
        if alt is not None and theirs is not None and abs(alt - theirs) <= 1e-9:
            note = ("  <-- and it MATCHES selection on the TEST cell's own labels: the §28.2 defect, "
                    "on the PRIMARY")
        say(f"  V3  FAIL  producer's primary is not reproducible from cell-B selection{note}")
        fails.append("V3")
    else:
        say("  V3  PASS  P2 primary held-out accuracy reproduces exactly")

    # ---- V2, as its OWN check. A-027/C-057 §42.5(2): this previously printed PASS inside V3's
    # success branch WITHOUT EVER READING the producer's `picks`, and could not enter `fails`. It
    # therefore could not detect the §28.2 defect it claims to check. Now it compares pick-by-pick.
    theirs_picks = (pp.get("picks") or {})
    if not theirs_picks:
        say("  V2  FAIL  the producer reports no `picks` for P2_primary; the (layer, C) selection "
            "cannot be checked at all")
        fails.append("V2")
    else:
        bad = []
        for d, (L, C) in sorted(picks.items()):
            t = theirs_picks.get(d)
            if t is None:
                bad.append((d, "absent from producer"))
            elif (int(t.get("layer", -1)), float(t.get("C", -1))) != (int(L), float(C)):
                bad.append((d, f"producer (L={t.get('layer')}, C={t.get('C')}) != "
                               f"cell-B recomputation (L={L}, C={C})"))
        extra = sorted(set(theirs_picks) - set(picks))
        if bad or extra:
            say(f"  V2  FAIL  picks do not reproduce from cell-B selection: {bad[:3]}"
                + (f"; producer has extra folds {extra}" if extra else ""))
            # §28.2 discriminator: was the producer selecting on the TEST cell's own labels?
            _, picks_bad = loo(C_rows, C_rows, layers, CLASSES, grid)
            match_bad = sum(1 for d, (L, C) in picks_bad.items()
                            if d in theirs_picks
                            and (int(theirs_picks[d].get("layer", -1)), float(theirs_picks[d].get("C", -1)))
                            == (int(L), float(C)))
            if match_bad > len(bad) // 2:
                say(f"  V2  FAIL  and {match_bad}/{len(picks_bad)} of the producer's picks MATCH "
                    f"selection on the TEST cell's own labels -- the §28.2 defect, on the PRIMARY")
            fails.append("V2")
        else:
            say(f"  V2  PASS  all {len(picks)} (layer, C) picks reproduce from cell-B selection "
                f"(§23.6), checked fold by fold against the producer")

    if mine is not None:
        p_mine, null = perm_p(C_rows, layers, CLASSES, picks, mine, n_perm, seed)
        p_them = (prod.get("P2_primary_permutation", {}) or {}).get("p_one_sided")
        band = max(3.0 * float(np.sqrt(max(p_mine, 1e-6) * (1 - max(p_mine, 1e-6)) / max(1, n_perm))),
                   2.0 / (1 + n_perm))
        ok = (p_them is not None and abs(p_mine - p_them) <= band)
        side = (p_them is not None and ((p_mine <= 0.05) == (p_them <= 0.05)))
        say(f"  V4  {'PASS' if (ok and side) else 'FAIL'}  permutation p: mine={p_mine:.4f} "
            f"(seed {seed}) producer={p_them!r} band +-{band:.4f} null_mean={null.mean():.4f}")
        if not ok or not side:
            if not side:
                say("  V4  FAIL  the two p-values fall on OPPOSITE sides of alpha=0.05")
            fails.append("V4")

    pair = ("knife", "club")
    kc = [r for c in pair for r in pools[c]]
    kcs = [r for c in pair for r in sel_pools[c]]
    got = prod.get("P2_knife_vs_club_CONTROL_bomb_absent")
    if kc and kcs:
        per_kc, _ = loo(kc, kcs, layers, pair, grid)
        mine_kc = float(np.mean(list(per_kc.values()))) if per_kc else None
        theirs_kc = got.get("mean_acc") if isinstance(got, dict) else None
        ok = (theirs_kc is not None and mine_kc is not None and abs(mine_kc - theirs_kc) <= acc_tol)
        say(f"  V5  {'PASS' if ok else 'FAIL'}  knife-vs-club control (§23.5 clause 4): "
            f"mine={mine_kc!r} producer={theirs_kc!r}")
        if not ok:
            fails.append("V5")
    else:
        say("  V5  FAIL  the §23.5 clause-4 control population is empty")
        fails.append("V5")
    return fails, out


# ---------------------------------------------------------------- mutation harness
def _honest(pools, sel_pools, layers, grid, n_perm, seed):
    """Build the producer JSON an HONEST analyzer would have written, under the fast grid."""
    C_rows = [r for c in CLASSES for r in pools[c]]
    B_rows = [r for c in CLASSES for r in sel_pools[c]]
    per, picks = loo(C_rows, B_rows, layers, CLASSES, grid)
    mean = float(np.mean(list(per.values())))
    p, _ = perm_p(C_rows, layers, CLASSES, picks, mean, n_perm, seed)
    pair = ("knife", "club")
    per_kc, _ = loo([r for c in pair for r in pools[c]],
                    [r for c in pair for r in sel_pools[c]], layers, pair, grid)
    return dict(P2_primary=dict(mean_acc=mean, per_domain=per, n_domains=len(per),
                                picks={d: dict(layer=int(L), C=float(C)) for d, (L, C) in picks.items()}),
                P2_primary_permutation=dict(p_one_sided=p),
                P2_knife_vs_club_CONTROL_bomb_absent=dict(
                    mean_acc=float(np.mean(list(per_kc.values()))) if per_kc else None))


def run_mutations(n_perm, seed):
    grid = (FAST_LAYERS, FAST_C)
    print("Loading populations and caches ...")
    pools, sel_pools, layers, bind = load_all()
    print(f"MUTATION HARNESS (fast grid L{list(FAST_LAYERS)} C{list(FAST_C)}, n_perm={n_perm}).\n"
          f"The grid only makes the harness interactive; each check's LOGIC is grid-independent.\n")
    honest = _honest(pools, sel_pools, layers, grid, n_perm, seed)
    base_fails, _ = run_checks(honest, pools, sel_pools, layers, bind, grid=grid, n_perm=n_perm,
                               seed=seed, quiet=True)
    if base_fails:
        print(f"*** the HONEST producer already fails {base_fails}; the harness is meaningless. ***")
        return 1

    def m_W1(j, b):   # fabricated headline
        j["P2_primary"]["mean_acc"] = 0.72
        j["P2_primary_permutation"]["p_one_sided"] = 0.0099
    def m_W2(j, b):   # p flipped across alpha, accuracy untouched
        j["P2_primary_permutation"]["p_one_sided"] = 1e-4 if honest["P2_primary_permutation"]["p_one_sided"] > 0.05 else 0.9
    def m_W3(j, b):   # clause-4 control deleted
        j.pop("P2_knife_vs_club_CONTROL_bomb_absent", None)
    def m_W4(j, b):   # one class joined to another bank's cache
        b["gun"] = 0.53
    def m_W5(j, b):   # primary block absent entirely
        j.pop("P2_primary", None)
    def m_W6(j, b):   # picks corrupted, mean_acc left correct -> only V2 can see it
        for d in list(j["P2_primary"].get("picks", {})):
            j["P2_primary"]["picks"][d] = dict(layer=14, C=0.01)

    MUT = [("W1 fabricated headline", m_W1, "V3"),
           ("W2 p flipped across alpha", m_W2, "V4"),
           ("W3 clause-4 control deleted", m_W3, "V5"),
           ("W4 one class on another bank's cache", m_W4, "V6"),
           ("W5 primary block deleted", m_W5, "V3"),
           ("W6 picks corrupted, mean_acc intact", m_W6, "V2")]
    ok_all = True
    for name, fn, designated in MUT:
        j = copy.deepcopy(honest)
        b = dict(bind)
        fn(j, b)
        fails, lines = run_checks(j, pools, sel_pools, layers, b, grid=grid, n_perm=n_perm,
                                  seed=seed, quiet=True)
        caught = designated in fails
        ok_all &= caught
        print(f"  {name:38s} -> {designated}  {'CAUGHT' if caught else '*** NOT CAUGHT ***'}")
        for l in lines:
            if "FAIL" in l:
                print("     " + l.strip())
    print()
    if ok_all:
        print("MUTATION HARNESS OK — every corruption was caught by its designated check.")
        return 0
    print("MUTATION HARNESS FAILED.")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--producer", default="outputs/boombness/dcs_analysis/dcs_bombness_specificity.json")
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--seed", type=int, default=90613)   # deliberately NOT the producer's 20260905
    ap.add_argument("--acc-tol", type=float, default=1e-9)
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()

    if a.mutate:
        return run_mutations(min(a.n_perm, 20), a.seed)

    if not os.path.exists(a.producer):
        print(f"producer JSON not found: {a.producer}")
        return 2
    prod = json.load(open(a.producer))
    pools, sel_pools, layers, bind = load_all()
    fails, _ = run_checks(prod, pools, sel_pools, layers, bind, grid=None, n_perm=a.n_perm,
                          seed=a.seed, acc_tol=a.acc_tol)
    if fails:
        print(f"\nPRIMARY VERIFICATION FAILED — {sorted(set(fails))}")
        return 1
    print("\nPRIMARY VERIFIED — the headline was recomputed from banks and caches, not read from "
          "the producer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
