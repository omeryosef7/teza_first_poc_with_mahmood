"""analyze_g9.py — plan §9: the 3-predictor model  ASR ~ boombness + role + refusalness.

The sprint has quoted boombness-vs-ASR (G2) and boombness-vs-refusalness (G2 mediation) but never
fitted the three together, which is what §9 actually asks for. This does that, and it REFUSES to
report a role coefficient when role is not identified.

WHY THE REFUSAL EXISTS. In this prompt bank `role_style` is perfectly collinear with `bank_block`:
every non-plain style lives in block `role_style`, and its families have ZERO overlap with the
families used for `plain`. So "role" and "which families were used" are the same variable, and a
role coefficient is a family-set coefficient wearing a role label. The raw contrast looks
substantial and would be easy to report as a finding -- non-plain ASR 0.067 vs plain 0.237 -- but
nothing in the design separates it from the family swap. This is the same failure that produced
retraction #6, where a role effect was quoted from a comparison whose two sides shared no families.

So `role_identified` is computed, not assumed, and the role term is fitted only if it passes.

Positions are matched: `d_surface` and `refusalness` must be read at the SAME token, because the
position 2x2 showed the comparison between them inverts with position. Run once per position.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys
from typing import Dict, List, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl, require_done  # noqa: E402


# ---------------------------------------------------------------------------- least squares --- #
def ols(X: List[List[float]], y: List[float]):
    """Plain normal-equations OLS with a Gaussian-elimination solve. Returns (beta, r2, resid)."""
    n, k = len(X), len(X[0])
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    # augmented elimination with partial pivoting
    M = [row[:] + [Xty[a]] for a, row in enumerate(XtX)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-12:
            raise ValueError("singular design matrix — a predictor is collinear")
        M[c], M[p] = M[p], M[c]
        for r in range(k):
            if r == c:
                continue
            f = M[r][c] / M[c][c]
            for cc in range(c, k + 1):
                M[r][cc] -= f * M[c][cc]
    beta = [M[a][k] / M[a][a] for a in range(k)]
    fit = [sum(beta[a] * X[i][a] for a in range(k)) for i in range(n)]
    resid = [y[i] - fit[i] for i in range(n)]
    ybar = sum(y) / n
    sst = sum((v - ybar) ** 2 for v in y)
    sse = sum(r * r for r in resid)
    return beta, (1 - sse / sst if sst > 0 else float("nan")), resid


def cr1_se(X, resid, clusters, beta_len):
    """Cluster-robust (CR1) standard errors, clustering on `clusters` — same estimator as G2."""
    n, k = len(X), beta_len
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    inv = _inv(XtX)
    by = collections.defaultdict(list)
    for i, g in enumerate(clusters):
        by[g].append(i)
    G = len(by)
    meat = [[0.0] * k for _ in range(k)]
    for g, idx in by.items():
        s = [sum(X[i][a] * resid[i] for i in idx) for a in range(k)]
        for a in range(k):
            for b in range(k):
                meat[a][b] += s[a] * s[b]
    c = (G / max(G - 1, 1)) * ((n - 1) / max(n - k, 1))
    V = [[c * sum(inv[a][x] * meat[x][z] * inv[z][b] for x in range(k) for z in range(k))
          for b in range(k)] for a in range(k)]
    return [math.sqrt(V[a][a]) if V[a][a] > 0 else float("nan") for a in range(k)], G


def _inv(A):
    k = len(A)
    M = [A[r][:] + [1.0 if c == r else 0.0 for c in range(k)] for r in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-12:
            raise ValueError("singular")
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        M[c] = [v / pv for v in M[c]]
        for r in range(k):
            if r != c:
                f = M[r][c]
                M[r] = [M[r][j] - f * M[c][j] for j in range(2 * k)]
    return [row[k:] for row in M]


def z(xs: Sequence[float]) -> List[float]:
    m = sum(xs) / len(xs)
    s = math.sqrt(sum((v - m) ** 2 for v in xs) / max(len(xs) - 1, 1)) or 1.0
    return [(v - m) / s for v in xs]


def norm_cdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def t_sf_2sided(t: float, df: int) -> float:
    """Two-sided Student-t tail. Audit 10 finding 1: g9 originally used a NORMAL reference with
    G=6 clusters, which is badly anticonservative and disagreed with analyze_g2.py:283 (t, df=G-1).
    That inflated the reported significance by up to 37 orders of magnitude -- the joint refusalness
    term was published as p<1e-4 when the repo's own standard gives 9.9e-4."""
    from analyze_g8 import t_sf          # verified against 5 published critical values
    return t_sf(abs(t), df)


def perm_p_within_cluster(xcols, y, clusters, target_idx, n_perm=2000, seed=20260818):
    """Within-cluster permutation of the target predictor, holding the others fixed.

    analyze_g2.py marks its within-domain permutation p as the citable one because a CR1 sandwich on
    6 clusters is itself unreliable. g9 had no such check; this supplies it so the two scripts make
    inference the same way.
    """
    import random
    rng = random.Random(seed)
    n = len(y)
    def fit_t(cols):
        X = [[1.0] + [c[i] for c in cols] for i in range(n)]
        beta, _, resid = ols(X, y)
        se, _ = cr1_se(X, resid, clusters, len(beta))
        j = target_idx + 1
        return abs(beta[j] / se[j]) if se[j] and not math.isnan(se[j]) else 0.0
    obs = fit_t(xcols)
    by = collections.defaultdict(list)
    for i, g in enumerate(clusters):
        by[g].append(i)
    hits = 0
    for _ in range(n_perm):
        permuted = list(xcols[target_idx])
        for idx in by.values():
            vals = [permuted[i] for i in idx]
            rng.shuffle(vals)
            for i, v in zip(idx, vals):
                permuted[i] = v
        cols = list(xcols); cols[target_idx] = permuted
        if fit_t(cols) >= obs:
            hits += 1
    return (hits + 1) / (n_perm + 1)


# ------------------------------------------------------------------ role identifiability --- #
def role_identifiability(meta: Dict[str, dict], keys: List[str]) -> Dict:
    """Can a role coefficient mean anything here? Decided PER STYLE, not globally.

    AUDIT 10 FINDING 5 rewrote this. The first version had four defects, none of which changed the
    reported numbers (both artifacts came out `identified: false`) but any of which could have:

      * it decided identification GLOBALLY and then added a dummy for EVERY style, so one
        overlapping style could admit a second style whose families are disjoint -- i.e. it would
        fit precisely the family-set-swap coefficient this gate exists to refuse;
      * it used OR (`shared_block or overlap>0`). Family disjointness is fatal on its own and
        block-sharing does not repair it, so the two conditions must BOTH hold. `block_pure` --
        the variable encoding "role == block" from the docstring -- was computed and never used;
      * with no `plain` style the reference fell to `styles[0]` alphabetically, which could report
        an identified contrast as unidentified;
      * `sorted(byfam)` raised TypeError if any row had `role_style = None`, and a single-style
        input returned a `reason` asserting a collinearity that was never tested.
    """
    byfam: Dict[object, set] = collections.defaultdict(set)
    byblock: Dict[object, set] = collections.defaultdict(set)
    for p_ in keys:
        r = meta[p_]
        byfam[r.get("role_style")].add(r.get("family_id"))
        byblock[r.get("role_style")].add(r.get("bank_block"))
    # None-safe ordering (finding 5d): missing role_style sorts as the empty string
    styles = sorted(byfam, key=lambda v: (v is None, str(v)))
    counts = {str(s): sum(1 for p_ in keys if meta[p_].get("role_style") == s) for s in styles}

    if len(styles) < 2:
        return {"reference_style": (str(styles[0]) if styles else None), "styles": [str(s) for s in styles],
                "n_by_style": counts, "per_style": {}, "identified_styles": [], "identified": False,
                "reason": f"only {len(styles)} role style present; no contrast exists to identify."}

    # reference = the largest stratum, not alphabetical (finding 5c)
    ref = max(styles, key=lambda s: counts[str(s)])

    per_style = {}
    for s in styles:
        if s == ref:
            continue
        overlap = len(byfam[s] & byfam[ref])
        shares_block = bool(byblock[s] & byblock[ref])
        ok = overlap > 0 and shares_block          # AND, not OR (finding 5b)
        why = []
        if overlap == 0:
            why.append("zero family overlap with the reference (role is a family-set swap)")
        if not shares_block:
            why.append("no bank_block shared with the reference (role is collinear with block)")
        per_style[str(s)] = {"n": counts[str(s)], "family_overlap_with_reference": overlap,
                             "shares_block_with_reference": shares_block,
                             "blocks": sorted(str(b) for b in byblock[s]),
                             "identified": ok, "reason": "identified" if ok else "; ".join(why)}

    ident_styles = [k for k, v in per_style.items() if v["identified"]]
    return {
        "reference_style": str(ref), "styles": [str(s) for s in styles], "n_by_style": counts,
        "per_style": per_style, "identified_styles": ident_styles,
        "identified": bool(ident_styles),
        "reason": ("identified for: " + ", ".join(ident_styles)) if ident_styles else
                  ("no role style is identified against the reference "
                   f"{ref!r}: " + "; ".join(sorted({v['reason'] for v in per_style.values()}))),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge", required=True)
    ap.add_argument("--extract", required=True)
    ap.add_argument("--refusalness", required=True)
    ap.add_argument("--arm", default="natural_doublespeak")
    ap.add_argument("--boombness-col", default="d_surface|L12|proj")
    ap.add_argument("--refusalness-col", default="refusalness|L20|proj")
    ap.add_argument("--position", required=True, choices=["codeword_last", "last"],
                    help="asserted readout position; BOTH inputs must have been read here")
    ap.add_argument("--cluster-by", default="domain")
    ap.add_argument("--min-examples", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    for d in (args.judge, args.extract, args.refusalness):
        require_done(d)

    J = read_jsonl(os.path.join(args.judge, "results.jsonl"))
    E = read_jsonl(os.path.join(args.extract, "results.jsonl"))
    R = read_jsonl(os.path.join(args.refusalness, "results.jsonl"))

    # ---- position guard: refuse unless BOTH sides demonstrably read where we claim -------- #
    def pos_of(rows, name):
        seen = collections.Counter(r.get("readout_position") for r in rows)
        if set(seen) - {args.position}:
            raise SystemExit(
                f"[G9] {name} rows carry readout_position {dict(seen)} but --position "
                f"{args.position} was asserted. The position 2x2 showed the boombness/refusalness "
                "comparison INVERTS with position, so a mixed-footing fit is not interpretable.")
        return dict(seen)

    # AUDIT 10 FINDING 2: this is the CONTINUOUS strongreject score in [0,1], not a binary ASR
    # indicator. The fitted intercept equals mean(score)=0.1806, not ASR@0.5=0.219. R^2 below is
    # therefore R^2 of the continuous score. `outcome` is recorded in the artifact so no reader has
    # to infer it.
    asr = {r["prompt_id"]: r["strongreject_score"] for r in J
           if r.get("strongreject_score") is not None and r.get("condition") == args.arm}
    meta = {r["prompt_id"]: r for r in J if r["prompt_id"] in asr}

    erows = [r for r in E if r.get("is_final_occurrence") and r["prompt_id"] in asr]
    rrows = [r for r in R if r["prompt_id"] in asr]
    # AUDIT 10 FINDING 3: the extract rows do NOT carry `readout_position` (extract_boombness.py
    # emits token_pos/seq_len instead), so the original `if any(...)` gate never fired on that side
    # and the docstring's "BOTH inputs" promise was decorative. Guard on what extract DOES emit,
    # and fall back to the run-level config, so a mixed-footing fit cannot pass silently -- that is
    # the failure that produced g2_analysis_MIXED_FOOTING_SUPERSEDED.json.
    ecfg = json.load(open(os.path.join(args.extract, "config.json")))
    epos = (ecfg.get("args", ecfg) or {}).get("position")
    if epos != args.position:
        raise SystemExit(f"[G9] extract run was configured with position={epos!r} but "
                         f"--position {args.position} was asserted")
    n_checked = 0
    for r in erows:
        if r.get("token_pos") is None or r.get("seq_len") is None:
            continue
        n_checked += 1
        if args.position == "last" and r["token_pos"] != r["seq_len"] - 1:
            raise SystemExit(f"[G9] extract row {r['prompt_id']} has token_pos={r['token_pos']} "
                             f"but seq_len-1={r['seq_len']-1}; --position last is not satisfied")
        if args.position == "codeword_last" and r["token_pos"] == r["seq_len"] - 1:
            raise SystemExit(f"[G9] extract row {r['prompt_id']} reads the FINAL token while "
                             f"--position codeword_last was asserted")
    if n_checked == 0:
        raise SystemExit("[G9] no extract row carries token_pos/seq_len — the position claim cannot "
                         "be verified, and an unverifiable position is exactly what the phantom-cell "
                         "bug looked like. Refusing.")
    print(f"[G9] position guard: verified {n_checked} extract rows at {args.position}")
    if any("readout_position" in r for r in rrows):
        pos_of([r for r in rrows if "readout_position" in r], "refusalness")
    else:
        rcfg = json.load(open(os.path.join(args.refusalness, "config.json")))
        rpos = (rcfg.get("args", rcfg) or {}).get("position")
        if rpos != args.position:
            raise SystemExit(f"[G9] refusalness run position={rpos!r} != {args.position}")

    qk = collections.Counter(r.get("query_kind") for r in erows)
    if set(qk) - {"behavioral"}:
        raise SystemExit(f"[G9] representation came from query kinds {dict(qk)}; must be behavioral")

    bmb = {r["prompt_id"]: r[args.boombness_col] for r in erows if args.boombness_col in r}
    rfs = {r["prompt_id"]: r[args.refusalness_col] for r in rrows if args.refusalness_col in r}

    keys = [p for p in asr if p in bmb and p in rfs
            and (meta[p].get("n_examples") or 0) >= args.min_examples]
    keys.sort()
    if len(keys) < 30:
        raise SystemExit(f"[G9] only {len(keys)} joined rows — not enough to fit")

    y = [asr[p] for p in keys]
    xb, xr = z([bmb[p] for p in keys]), z([rfs[p] for p in keys])
    clusters = [meta[p].get(args.cluster_by) for p in keys]
    nG = len(set(clusters))
    if nG < 3:
        raise SystemExit(f"[G9] {nG} clusters — CR1 is not trustworthy below 3")

    ident = role_identifiability(meta, keys)

    print(f"[G9] arm={args.arm} position={args.position} n={len(keys)} clusters={nG}")
    print(f"[G9] role identified? {ident['identified']} — {ident['reason'][:100]}")

    models = {}
    specs = [("boombness_only", [xb], ["boombness"]),
             ("refusalness_only", [xr], ["refusalness"]),
             ("boombness+refusalness", [xb, xr], ["boombness", "refusalness"])]

    role_terms: List[List[float]] = []
    role_names: List[str] = []
    if ident["identified"]:
        # ONLY the styles that individually passed; rows of unidentified styles are dropped so an
        # unidentified stratum cannot leak into the reference category either.
        for s in ident["identified_styles"]:
            role_terms.append([1.0 if str(meta[p].get("role_style")) == s else 0.0 for p in keys])
            role_names.append(f"role[{s}]")
        specs.append(("boombness+role+refusalness", [xb] + role_terms + [xr],
                      ["boombness"] + role_names + ["refusalness"]))

    for name, cols, labels in specs:
        X = [[1.0] + [c[i] for c in cols] for i in range(len(keys))]
        try:
            beta, r2, resid = ols(X, y)
        except ValueError as e:
            models[name] = {"error": str(e)}
            continue
        se, G = cr1_se(X, resid, clusters, len(beta))
        terms = {}
        for a, lab in enumerate(["intercept"] + labels):
            t = beta[a] / se[a] if se[a] and not math.isnan(se[a]) else float("nan")
            terms[lab] = {
                "beta": beta[a], "se_cr1": se[a], "t": t if not math.isnan(t) else None,
                # t(G-1), NOT normal -- see t_sf_2sided. `p_cr1_normal_ANTICONSERVATIVE` is kept
                # only so the superseded value is visible next to the correct one.
                "p_cr1": (t_sf_2sided(t, max(G - 1, 1)) if not math.isnan(t) else None),
                "p_cr1_normal_ANTICONSERVATIVE": (math.erfc(abs(t) / math.sqrt(2))
                                                  if not math.isnan(t) else None),
                "reference": f"t(df={max(G-1,1)})"}
        models[name] = {"r2": r2, "n": len(keys), "n_clusters": G, "terms": terms}
        print(f"  {name:28s} R2={r2:.4f}  " + "  ".join(
            f"{k}={v['beta']:+.4f}(p={v['p_cr1']:.4f})" for k, v in terms.items()
            if k != "intercept" and v["p_cr1"] is not None))

    # within-domain permutation on the JOINT model, the inference analyze_g2 marks as citable
    if "boombness+refusalness" in models and "error" not in models["boombness+refusalness"]:
        for i, lab in enumerate(["boombness", "refusalness"]):
            pp = perm_p_within_cluster([xb, xr], y, clusters, i)
            models["boombness+refusalness"]["terms"][lab]["p_within_domain_perm"] = pp
            print(f"  perm[{lab}] within-domain p = {pp:.4f}")

    # incremental R2 — what each predictor adds over the other
    inc = {}
    if "boombness+refusalness" in models and "error" not in models["boombness+refusalness"]:
        j = models["boombness+refusalness"]["r2"]
        inc["refusalness_over_boombness"] = j - models["boombness_only"]["r2"]
        inc["boombness_over_refusalness"] = j - models["refusalness_only"]["r2"]
        print(f"  incremental R2: boombness adds {inc['boombness_over_refusalness']:+.4f} over "
              f"refusalness; refusalness adds {inc['refusalness_over_boombness']:+.4f} over boombness")

    # The raw role contrast, reported as DESCRIPTIVE only when role is not identified.
    raw_role = {}
    if not ident["identified"]:
        ref = ident["reference_style"]
        for s in ident["styles"]:
            sub = [asr[p] for p in keys if meta[p].get("role_style") == s]
            if sub:
                raw_role[s] = {"n": len(sub), "mean_score": sum(sub) / len(sub),
                               "asr_at_0.5": sum(1 for v in sub if v >= 0.5) / len(sub)}
        print(f"  role NOT fitted. Descriptive only: " +
              ", ".join(f"{s} n={v['n']} ASR={v['asr_at_0.5']:.3f}" for s, v in raw_role.items()))

    out = {
        "plan_section": "9", "arm": args.arm, "position": args.position,
        "outcome": "strongreject_score (continuous [0,1], NOT binary ASR@0.5)",
        "min_examples": args.min_examples,
        "inference": "CR1 sandwich, t(G-1) reference, plus within-domain permutation",
        "judge": os.path.abspath(args.judge), "extract": os.path.abspath(args.extract),
        "refusalness": os.path.abspath(args.refusalness),
        "boombness_col": args.boombness_col, "refusalness_col": args.refusalness_col,
        "cluster_by": args.cluster_by, "n": len(keys), "n_clusters": nG,
        "role_identifiability": ident, "models": models, "incremental_r2": inc,
        "role_descriptive_only": raw_role,
        "caveat": (
            "Role is NOT in the fitted model when role_identifiability.identified is false. The "
            "descriptive role means are a family-set contrast, not a role effect, and must not be "
            "reported as one (this is the retraction-#6 failure mode)."),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[G9] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
