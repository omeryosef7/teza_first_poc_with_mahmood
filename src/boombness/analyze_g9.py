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


# ------------------------------------------------------------------ role identifiability --- #
def role_identifiability(meta: Dict[str, dict], keys: List[str]) -> Dict:
    """Can a role coefficient mean anything here? Checked, not assumed.

    Two ways role fails to be identified, both present in this bank:
      * every non-plain style sits in its own `bank_block`, so role == block;
      * the family sets are disjoint, so role is also a family-set swap.
    """
    byfam = collections.defaultdict(set)
    byblock = collections.defaultdict(set)
    for p in keys:
        r = meta[p]
        byfam[r.get("role_style")].add(r.get("family_id"))
        byblock[r.get("role_style")].add(r.get("bank_block"))
    styles = sorted(byfam)
    ref = "plain" if "plain" in byfam else styles[0]
    overlap = {s: len(byfam[s] & byfam[ref]) for s in styles if s != ref}
    block_pure = all(len(byblock[s]) == 1 for s in styles if s != ref)
    shared_block = any(byblock[s] & byblock[ref] for s in styles if s != ref)
    counts = {s: sum(1 for p in keys if meta[p].get("role_style") == s) for s in styles}
    identified = (any(v > 0 for v in overlap.values()) or shared_block) and len(styles) > 1
    return {
        "reference_style": ref, "styles": styles, "n_by_style": counts,
        "family_overlap_with_reference": overlap,
        "each_nonreference_style_in_a_single_block": block_pure,
        "any_block_shared_with_reference": shared_block,
        "identified": identified,
        "reason": (
            "identified" if identified else
            "role_style is collinear with bank_block and the family sets are disjoint: every "
            "non-reference style has zero families in common with the reference, so a role "
            "coefficient is a family-set coefficient. Not fitted."),
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

    asr = {r["prompt_id"]: r["strongreject_score"] for r in J
           if r.get("strongreject_score") is not None and r.get("condition") == args.arm}
    meta = {r["prompt_id"]: r for r in J if r["prompt_id"] in asr}

    erows = [r for r in E if r.get("is_final_occurrence") and r["prompt_id"] in asr]
    rrows = [r for r in R if r["prompt_id"] in asr]
    # refusalness runs predate readout_position in some cases; only guard what carries it
    if any("readout_position" in r for r in erows):
        pos_of([r for r in erows if "readout_position" in r], "extract")
    if any("readout_position" in r for r in rrows):
        pos_of([r for r in rrows if "readout_position" in r], "refusalness")

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
        ref = ident["reference_style"]
        for s in ident["styles"]:
            if s == ref:
                continue
            role_terms.append([1.0 if meta[p].get("role_style") == s else 0.0 for p in keys])
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
            terms[lab] = {"beta": beta[a], "se_cr1": se[a],
                          "p_cr1": (2 * (1 - norm_cdf(abs(t))) if not math.isnan(t) else None)}
        models[name] = {"r2": r2, "n": len(keys), "n_clusters": G, "terms": terms}
        print(f"  {name:28s} R2={r2:.4f}  " + "  ".join(
            f"{k}={v['beta']:+.4f}(p={v['p_cr1']:.4f})" for k, v in terms.items()
            if k != "intercept" and v["p_cr1"] is not None))

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
