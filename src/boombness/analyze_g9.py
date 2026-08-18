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

--------------------------------------------------------------------------------------------------
THREE DEFECTS FIXED 2026-08-18.

T5 -- ESTIMAND PAIRING. Each term carried `beta` (the POOLED coefficient) and, beside it,
`p_within_domain_perm`, which is a permutation p for a DIFFERENT quantity: the permutation demeans
the target predictor and y WITHIN CLUSTER first. Adjacent keys, no distinguishing label, so every
reader attached the p to the pooled beta. The same defect was found in analyze_g2.py and
analyze_g64.py in the same audit, and in g2 the gap is a factor of 2.6 on real data. Every term now
reports BOTH point estimates -- `beta_pooled` and `beta_within_domain` -- each p key names its own
estimand (`p_cr1_pooled_beta`, `p_perm_within_domain_beta`), and `p_estimand_*` names the quantity
each p tests. Naming follows analyze_g64.py so the three scripts agree. NOTHING WAS PROMOTED OR
DEMOTED; only the pairing became legible.

PLAN SECTION 9 DECISION QUESTION 5 ("does it hold when controlling for number of examples?") had
never been answered anywhere in the sprint. `n_examples` was used ONLY as a FILTER (--min-examples),
never as a regressor, even though it plausibly drives BOTH boombness (more demonstrations = more
codeword evidence in context) and ASR (a dose-response the report itself measures in section 8). So
the published rho=+0.307 was unguarded against a dose-response confound. `n_examples` now enters as
a regressor on the log2 (per-doubling) scale analyze_g8 uses, with the SAME CR1 sandwich and the
SAME within-domain permutation as every other term, plus the rank-partial correlation of boombness
with ASR controlling for it (pooled and within-domain, reusing analyze_g64's estimators). The
before -> after for every affected coefficient is written to `n_examples_control` in the artifact,
and the verdict is computed from those numbers rather than asserted.

ROLE IDENTIFIABILITY WAS UNFALSIFIABLE. The gate tested family overlap on the RAW `family_id`, and
`family_id` EMBEDS THE STYLE NAME -- so the overlap is 0 by construction, for every bank, forever.
The gate would have refused even on a perfectly crossed design; a gate that cannot pass is not
evidence. It now masks the style token out of `family_id` before intersecting, reusing
`analyze_g11.stem()` (which was written for exactly this and already established that the demo block
and final query text are byte-identical across styles). On this bank the repair FLIPS the verdict:
raw overlap 0 for every style pair, style-masked overlap 6 for every style pair -- the design IS
crossed, 6 content stems x 6 styles = 36 rows over 6 domains.

The `shares_block_with_reference` clause needed the same repair one level up: `bank_block` is
`role_style` for all five styles and never `role_style` for `plain`, i.e. the block label is a
deterministic relabelling of the style, so requiring a shared block is requiring the impossible --
the same unfalsifiability, wearing a different column name. The clause is therefore waived, and ONLY
waived, when the block label is verified to carry no information beyond the style (every block
involved is style-pure). Family-set disjointness remains fatal on its own, which is the direction
audit 10 finding 5b established.

Identification is not a licence to fit on the whole sample: a role dummy fitted over all rows
compares 6 styled prompts against 204 reference prompts of DIFFERENT content, which is precisely the
family-set-swap coefficient this gate exists to refuse (retraction #6). The role model is therefore
fitted on the CROSSED SUBSET only -- the rows whose masked content stem appears under both the style
and the reference.
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
# REUSE, NOT REIMPLEMENT (standing project rule). `stem` is analyze_g11's style-masking helper --
# the exact operation the role gate needed and did not have. The rank estimators come from
# analyze_g64, which is also where the `rho_pooled` / `rho_within_domain` naming is defined, so the
# n_examples partials reported here are literally the same estimator as section 6.4's.
from analyze_g11 import stem  # noqa: E402
from analyze_g64 import (spearman, rank_partial, rho_within_domain,  # noqa: E402
                         rank_partial_within_domain, perm_p_partial)


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


def demean_within(v, clusters):
    """Subtract each cluster's mean. Required before any within-cluster statistic.

    Extracted from inside perm_p_within_cluster by audit T5: while it lived as a local closure the
    permutation could demean but the REPORTED point estimate could not, which is how a pooled beta
    came to sit beside a within-cluster p.
    """
    by = collections.defaultdict(list)
    for i, g in enumerate(clusters):
        by[g].append(i)
    out = list(v)
    for idx in by.values():
        m = sum(out[i] for i in idx) / len(idx)
        for i in idx:
            out[i] -= m
    return out


def within_cluster_beta(xcols, y, clusters, target_idx):
    """The POINT ESTIMATE that `perm_p_within_cluster(..., target_idx)` is a p-value for.

    Same footing as the permutation, to the letter: the target column and y are demeaned within
    cluster, the other columns are left as they are, and the coefficient on the target column is
    returned. Any other definition would recreate the T5 mismatch in the opposite direction.
    """
    cols = [(demean_within(c, clusters) if k == target_idx else c) for k, c in enumerate(xcols)]
    yy = demean_within(y, clusters)
    n = len(yy)
    X = [[1.0] + [c[i] for c in cols] for i in range(n)]
    beta, _, _ = ols(X, yy)
    return beta[target_idx + 1]


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
    # AUDIT 2026-08-18: permuting within cluster while fitting on the RAW vectors leaves the
    # between-cluster component in the statistic, so the null is not centred and the quantity is
    # not the within-domain one the name promises (analyze_g2.py:284, audit A3 - same bug).
    # Demean the target predictor and y within cluster first.
    by = collections.defaultdict(list)
    for i, g in enumerate(clusters):
        by[g].append(i)
    # `demean_within` is the module-level helper (audit T5) so that the permutation and the
    # reported point estimate `within_cluster_beta` cannot drift apart.
    xcols = [(demean_within(c, clusters) if k == target_idx else c) for k, c in enumerate(xcols)]
    y = demean_within(y, clusters)
    obs = fit_t(xcols)
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
    byfam_raw: Dict[object, set] = collections.defaultdict(set)
    byblock: Dict[object, set] = collections.defaultdict(set)
    blocks_by_style_stem: Dict[tuple, set] = collections.defaultdict(set)
    for p_ in keys:
        r = meta[p_]
        st = r.get("role_style")
        blocks_by_style_stem[(st, stem(r.get("family_id"), st))].add(r.get("bank_block"))
        # THE STYLE TOKEN MUST BE MASKED OUT BEFORE INTERSECTING (audit T5 sibling finding,
        # 2026-08-18). `family_id` CONTAINS the style name, so intersecting raw family_ids across
        # two styles is guaranteed to return the empty set no matter how the bank was built. The
        # gate therefore could never pass, and an assertion that cannot fail is not evidence. Both
        # numbers are reported: the masked overlap is the one that decides, the raw one is kept so
        # the defect stays visible in the artifact.
        byfam[st].add(stem(r.get("family_id"), st))
        byfam_raw[st].add(r.get("family_id"))
        byblock[st].add(r.get("bank_block"))
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
        shared_stems = byfam[s] & byfam[ref]
        overlap = len(shared_stems)                          # style-masked content stems
        overlap_raw = len(byfam_raw[s] & byfam_raw[ref])     # the old, always-0 test
        # BOTH remaining clauses are evaluated ON THE CROSSED CELLS, not on the whole sample: the
        # contrast that gets fitted lives there, and the reference arm's other 198 rows are not part
        # of it. Evaluating `shares_block` over all of `plain` mixed in five blocks that the crossed
        # cells never touch.
        blk_s = set().union(*[blocks_by_style_stem[(s, c)] for c in shared_stems]) if shared_stems \
            else set()
        blk_ref = set().union(*[blocks_by_style_stem[(ref, c)] for c in shared_stems]) \
            if shared_stems else set()
        shares_block = bool(blk_s & blk_ref)
        # Is `bank_block` anything other than a second name for `role_style` here? If each arm of
        # the crossed contrast sits in exactly ONE block, the block label is a deterministic
        # relabelling of the style, so "share a block" is a second condition that can never be met
        # -- the same unfalsifiability as the raw family_id test, one column over. On this bank that
        # is what happens: the styled arm is entirely `role_style` and its matched reference rows
        # are entirely `core2x2`. The clause is waived ONLY when that is verified and the
        # verification is recorded. Family-set disjointness stays fatal on its own (audit 10
        # finding 5b): the waiver never applies to `overlap == 0`.
        block_is_relabel_of_style = (len(blk_s) == 1 and len(blk_ref) == 1)
        ok = overlap > 0 and (shares_block or block_is_relabel_of_style)
        why = []
        if overlap == 0:
            why.append("zero family overlap with the reference AFTER masking the style token out "
                       "of family_id (role really is a family-set swap here)")
        if overlap > 0 and not shares_block and not block_is_relabel_of_style:
            why.append("no bank_block shared with the reference, and bank_block is NOT a pure "
                       "relabelling of role_style, so block carries information the style does not")
        reason = "identified"
        if ok and not shares_block:
            reason = ("identified on style-masked content stems; the shares-block clause was "
                      "WAIVED because every bank_block involved is style-pure, i.e. the block "
                      "label carries no information beyond the style itself")
        per_style[str(s)] = {"n": counts[str(s)],
                             "family_overlap_with_reference": overlap,
                             "family_overlap_raw_family_id": overlap_raw,
                             "overlap_test": "stem(family_id, role_style) -- style token masked",
                             "shares_block_with_reference": shares_block,
                             "block_is_relabel_of_style": block_is_relabel_of_style,
                             "blocks": sorted(str(b) for b in byblock[s]),
                             "blocks_on_crossed_cells": sorted(str(b) for b in blk_s),
                             "reference_blocks_on_crossed_cells":
                                 sorted(str(b) for b in blk_ref),
                             "n_crossed_rows": sum(
                                 1 for q in keys
                                 if str(meta[q].get("role_style")) in (str(s), str(ref))
                                 and stem(meta[q].get("family_id"),
                                          meta[q].get("role_style")) in shared_stems),
                             "identified": ok, "reason": reason if ok else "; ".join(why)}

    ident_styles = [k for k, v in per_style.items() if v["identified"]]
    return {
        "reference_style": str(ref), "styles": [str(s) for s in styles], "n_by_style": counts,
        "per_style": per_style, "identified_styles": ident_styles,
        "identified": bool(ident_styles),
        "reason": ("identified for: " + ", ".join(ident_styles)) if ident_styles else
                  ("no role style is identified against the reference "
                   f"{ref!r}: " + "; ".join(sorted({v['reason'] for v in per_style.values()}))),
    }


def crossed_subset(meta: Dict[str, dict], keys: List[str], ident: Dict) -> List[str]:
    """Rows on which the identified role contrast is actually a WITHIN-CONTENT contrast.

    Identification is a statement about a subset, not about the sample. Five styles of 6 prompts
    each are crossed with the reference on 6 content stems; the reference ALSO contains 198 rows of
    entirely different content. A role dummy fitted over all 234 rows would compare 6 styled prompts
    against 204 mostly-unrelated ones -- the family-set-swap coefficient this whole gate exists to
    refuse (retraction #6). So the role model is fitted here, on the crossed cells only.
    """
    ref = ident.get("reference_style")
    ident_styles = set(ident.get("identified_styles") or [])
    if not ident_styles:
        return []
    by_style_stems: Dict[str, set] = collections.defaultdict(set)
    for p_ in keys:
        st = meta[p_].get("role_style")
        by_style_stems[str(st)].add(stem(meta[p_].get("family_id"), st))
    shared = set(by_style_stems.get(str(ref), set()))
    for st in ident_styles:
        shared &= by_style_stems.get(st, set())
    if not shared:
        return []
    keep = []
    for p_ in keys:
        st = str(meta[p_].get("role_style"))
        if (st == str(ref) or st in ident_styles) and \
                stem(meta[p_].get("family_id"), meta[p_].get("role_style")) in shared:
            keep.append(p_)
    return keep


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
    crossed = crossed_subset(meta, keys, ident)
    crossed_idx = [i for i, p in enumerate(keys) if p in set(crossed)]

    print(f"[G9] arm={args.arm} position={args.position} n={len(keys)} clusters={nG}")
    print(f"[G9] role identified? {ident['identified']} — {ident['reason'][:160]}")
    if ident["identified"]:
        print(f"[G9] crossed subset for the role fit: n={len(crossed_idx)} rows, "
              f"{len(set(clusters[i] for i in crossed_idx))} clusters")

    # ---- n_examples as a REGRESSOR, not just a filter (plan §9 decision question 5) --------- #
    # It was ONLY ever a filter here (--min-examples), yet it is the most obvious common cause of
    # both regressor and outcome in this design, so the boombness coefficient was unguarded against
    # a dose-response confound. log2 = the per-doubling scale analyze_g8 reports comprehension on.
    nex_raw = [float(meta[p].get("n_examples") or 0) for p in keys]
    nex_levels = sorted(set(nex_raw))
    nex_usable = len(nex_levels) >= 2
    nex_scale = ("log2(n_examples)" if min(nex_raw) > 0 else "log2(1+n_examples)")
    if nex_usable:
        nlog = [math.log2(v) if min(nex_raw) > 0 else math.log2(1.0 + v) for v in nex_raw]
        xn, xn_lin = z(nlog), z(nex_raw)
    print(f"[G9] n_examples levels={ [int(v) for v in nex_levels] } scale={nex_scale} "
          f"usable_as_regressor={nex_usable}")

    models = {}
    all_rows = list(range(len(keys)))
    # spec = (name, columns, labels, ROWS). The row set is part of the spec because the role model
    # is estimable only on the crossed cells (see crossed_subset).
    specs = [("boombness_only", [xb], ["boombness"], all_rows),
             ("refusalness_only", [xr], ["refusalness"], all_rows),
             ("boombness+refusalness", [xb, xr], ["boombness", "refusalness"], all_rows)]
    if nex_usable:
        specs += [
            ("n_examples_only", [xn], ["n_examples"], all_rows),
            ("boombness+n_examples", [xb, xn], ["boombness", "n_examples"], all_rows),
            ("boombness+refusalness+n_examples", [xb, xr, xn],
             ["boombness", "refusalness", "n_examples"], all_rows),
            # scale sensitivity: the confound verdict must not hinge on log2 vs linear
            ("boombness+refusalness+n_examples_linear", [xb, xr, xn_lin],
             ["boombness", "refusalness", "n_examples_linear"], all_rows),
        ]

    role_names: List[str] = []
    if ident["identified"] and len(crossed_idx) >= 12:
        # ONLY the styles that individually passed, and ONLY on the crossed rows, so an
        # unidentified stratum cannot leak into the reference category or into the content.
        sub = crossed_idx
        cols = [[xb[i] for i in sub]]
        labels = ["boombness"]
        for st in ident["identified_styles"]:
            cols.append([1.0 if str(meta[keys[i]].get("role_style")) == st else 0.0 for i in sub])
            labels.append(f"role[{st}]")
            role_names.append(f"role[{st}]")
        cols.append([xr[i] for i in sub])
        labels.append("refusalness")
        specs.append(("boombness+role+refusalness (crossed subset)", cols, labels, sub))
    elif ident["identified"]:
        print(f"[G9] role identified but only {len(crossed_idx)} crossed rows — NOT fitted")

    for name, cols, labels, rows in specs:
        yv = [y[i] for i in rows]
        cl = [clusters[i] for i in rows]
        # columns are given in the spec's own index space when the spec carries a subset
        cc = cols if len(cols[0]) == len(rows) else [[c[i] for i in rows] for c in cols]
        X = [[1.0] + [c[j] for c in cc] for j in range(len(rows))]
        try:
            beta, r2, resid = ols(X, yv)
        except ValueError as e:
            models[name] = {"error": str(e)}
            continue
        se, G = cr1_se(X, resid, cl, len(beta))
        k = len(beta)
        # A CR1 meat matrix is a sum of G rank-1 terms, so with G <= k it is rank deficient and the
        # standard errors are not estimates of anything. Suppress the p rather than print a number
        # that looks like inference (the crossed role model is exactly this case: G=6, k=8).
        cr1_ok = G > k
        terms = {}
        for a, lab in enumerate(["intercept"] + labels):
            t = beta[a] / se[a] if se[a] and not math.isnan(se[a]) else float("nan")
            terms[lab] = {
                # T5: `beta_pooled` is the POOLED coefficient and `p_cr1_pooled_beta` is its p.
                # The permutation p added below tests `beta_within_domain`, a different quantity.
                "beta_pooled": beta[a], "se_cr1": se[a], "t": t if not math.isnan(t) else None,
                # t(G-1), NOT normal -- see t_sf_2sided. `p_cr1_normal_ANTICONSERVATIVE` is kept
                # only so the superseded value is visible next to the correct one.
                "p_cr1_pooled_beta": (t_sf_2sided(t, max(G - 1, 1))
                                      if (cr1_ok and not math.isnan(t)) else None),
                "p_estimand_cr1": "beta_pooled",
                "p_cr1_normal_ANTICONSERVATIVE": (math.erfc(abs(t) / math.sqrt(2))
                                                  if (cr1_ok and not math.isnan(t)) else None),
                "reference": f"t(df={max(G-1,1)})",
                "cr1_rank_deficient": (not cr1_ok),
                "cr1_suppressed_reason": (None if cr1_ok else
                                          f"G={G} clusters <= k={k} parameters: the CR1 meat "
                                          f"matrix is rank deficient, so no p is reported")}
        models[name] = {"r2": r2, "n": len(rows), "n_clusters": G, "n_params": k,
                        "cr1_rank_deficient": (not cr1_ok), "terms": terms}
        shown = "  ".join(f"{kk}={v['beta_pooled']:+.4f}(p={v['p_cr1_pooled_beta']:.4f})"
                          for kk, v in terms.items()
                          if kk != "intercept" and v["p_cr1_pooled_beta"] is not None)
        if not shown:
            shown = "  ".join(f"{kk}={v['beta_pooled']:+.4f}(p suppressed)"
                              for kk, v in terms.items() if kk != "intercept")
        print(f"  {name:44s} n={len(rows):>4d} R2={r2:.4f}  " + shown)

    # within-domain permutation, the inference analyze_g2 marks as citable, on the joint models.
    # T5: this p belongs to `beta_within_domain`, which is now computed and stored beside it.
    for mname, labs, cols in (
            ("boombness+refusalness", ["boombness", "refusalness"], [xb, xr]),
            ("boombness+refusalness+n_examples",
             ["boombness", "refusalness", "n_examples"], [xb, xr, xn] if nex_usable else None)):
        if cols is None or mname not in models or "error" in models[mname]:
            continue
        for i, lab in enumerate(labs):
            bw = within_cluster_beta(cols, y, clusters, i)
            pp = perm_p_within_cluster(cols, y, clusters, i)
            t = models[mname]["terms"][lab]
            t["beta_within_domain"] = bw
            t["p_perm_within_domain_beta"] = pp
            t["p_estimand_perm"] = "beta_within_domain"
            t["estimand_note"] = (
                "beta_pooled and beta_within_domain are DIFFERENT quantities. "
                "p_perm_within_domain_beta is a p-value for beta_within_domain ONLY; "
                "p_cr1_pooled_beta is the one that belongs to beta_pooled.")
            print(f"  perm[{mname} :: {lab}] beta_pooled={t['beta_pooled']:+.4f} "
                  f"beta_within_domain={bw:+.4f}  within-domain p={pp:.4f}")

    # incremental R2 — what each predictor adds over the other
    inc = {}
    if "boombness+refusalness" in models and "error" not in models["boombness+refusalness"]:
        j = models["boombness+refusalness"]["r2"]
        inc["refusalness_over_boombness"] = j - models["boombness_only"]["r2"]
        inc["boombness_over_refusalness"] = j - models["refusalness_only"]["r2"]
        print(f"  incremental R2: boombness adds {inc['boombness_over_refusalness']:+.4f} over "
              f"refusalness; refusalness adds {inc['refusalness_over_boombness']:+.4f} over boombness")
    if nex_usable and "boombness+refusalness+n_examples" in models:
        j3 = models["boombness+refusalness+n_examples"]["r2"]
        inc["n_examples_over_boombness+refusalness"] = j3 - models["boombness+refusalness"]["r2"]
        inc["boombness_over_refusalness+n_examples"] = (
            j3 - models["n_examples_only"]["r2"] if "n_examples_only" in models else None)
        print(f"  incremental R2: n_examples adds "
              f"{inc['n_examples_over_boombness+refusalness']:+.4f} over boombness+refusalness")

    # ---- §9 Q5 ANSWERED: before -> after, computed, not asserted --------------------------- #
    nex_control = {"answered": bool(nex_usable), "scale": nex_scale,
                   "levels": [int(v) for v in nex_levels]}
    if nex_usable and "boombness+refusalness+n_examples" in models \
            and "error" not in models["boombness+refusalness+n_examples"]:
        b0 = models["boombness+refusalness"]["terms"]["boombness"]
        b1 = models["boombness+refusalness+n_examples"]["terms"]["boombness"]
        r0 = models["boombness+refusalness"]["terms"]["refusalness"]
        r1 = models["boombness+refusalness+n_examples"]["terms"]["refusalness"]
        lin = models.get("boombness+refusalness+n_examples_linear", {}).get("terms", {})
        doms = clusters
        xb_raw = [bmb[p] for p in keys]
        # the same rank estimators section 6.4 uses, so the two sections are comparable
        nex_control.update({
            "boombness_before": {k2: b0.get(k2) for k2 in
                                 ("beta_pooled", "p_cr1_pooled_beta", "beta_within_domain",
                                  "p_perm_within_domain_beta")},
            "boombness_after": {k2: b1.get(k2) for k2 in
                                ("beta_pooled", "p_cr1_pooled_beta", "beta_within_domain",
                                 "p_perm_within_domain_beta")},
            "refusalness_before": {k2: r0.get(k2) for k2 in
                                   ("beta_pooled", "p_cr1_pooled_beta", "beta_within_domain",
                                    "p_perm_within_domain_beta")},
            "refusalness_after": {k2: r1.get(k2) for k2 in
                                  ("beta_pooled", "p_cr1_pooled_beta", "beta_within_domain",
                                   "p_perm_within_domain_beta")},
            "boombness_beta_retained_fraction_pooled":
                (b1["beta_pooled"] / b0["beta_pooled"]) if b0["beta_pooled"] else None,
            "boombness_beta_pooled_linear_scale":
                (lin.get("boombness") or {}).get("beta_pooled"),
            "rho_boombness_vs_n_examples_pooled": spearman(xb_raw, nex_raw),
            "rho_boombness_vs_n_examples_within_domain": rho_within_domain(xb_raw, nex_raw, doms),
            "rho_n_examples_vs_asr_pooled": spearman(nex_raw, y),
            "rho_n_examples_vs_asr_within_domain": rho_within_domain(nex_raw, y, doms),
            "rho_boombness_vs_asr_pooled": spearman(xb_raw, y),
            "rho_partial_n_examples_pooled": rank_partial(xb_raw, y, nex_raw),
            "rho_partial_n_examples_within_domain":
                rank_partial_within_domain(xb_raw, y, nex_raw, doms),
            "p_perm_within_domain_partial": perm_p_partial(xb_raw, y, nex_raw, doms),
            "p_estimand_partial": "rho_partial_n_examples_within_domain",
        })
        keep_frac = nex_control["boombness_beta_retained_fraction_pooled"]
        pa = b1.get("p_perm_within_domain_beta")
        pb = b0.get("p_perm_within_domain_beta")
        if keep_frac is None:
            verdict = "boombness coefficient is zero before the control; nothing to attenuate"
        elif keep_frac < 0.5 or (pb is not None and pa is not None and pb < 0.05 <= pa):
            verdict = ("COLLAPSES: controlling for the number of demonstrations removes most of the "
                       "boombness coefficient — the §9 boombness->ASR relation is substantially a "
                       "dose-response effect of demonstration count")
        elif keep_frac > 1.2:
            verdict = ("SURVIVES, AND GROWS: controlling for the number of demonstrations makes the "
                       "boombness coefficient LARGER, i.e. n_examples was acting as a suppressor, "
                       "not a confound, for this predictor")
        elif keep_frac < 0.8:
            verdict = ("ATTENUATES but survives: part of the boombness->ASR relation is demonstration "
                       "count, the rest is not")
        else:
            verdict = ("SURVIVES: the boombness coefficient is essentially unchanged when the number "
                       "of demonstrations is controlled")
        nex_control["verdict"] = verdict
        print(f"[G9] §9 Q5 (control for n_examples): boombness beta {b0['beta_pooled']:+.4f} -> "
              f"{b1['beta_pooled']:+.4f} (retains {keep_frac:.2f} of it); within-domain "
              f"{b0.get('beta_within_domain'):+.4f} -> {b1.get('beta_within_domain'):+.4f}; "
              f"perm p {pb} -> {pa}")
        print(f"[G9] §9 Q5 VERDICT: {verdict}")
    else:
        nex_control["verdict"] = ("NOT ANSWERED: n_examples has fewer than two levels in the "
                                 "analysed sample (check --min-examples)")

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

    # PROVENANCE (2026-08-18). This artifact recorded its three input directories but NOT its argv,
    # so the flags that decide the numbers -- --boombness-col, --refusalness-col, --min-examples,
    # --cluster-by -- were recoverable only because they happen to be echoed as separate keys, and
    # nothing recorded which commit produced the file. analyze_g64.py had the identical gap and it
    # was fixed there in this same audit; recording argv is the standing rule.
    import subprocess as _sp

    def _git(*a):
        try:
            return _sp.check_output(["git", *a], stderr=_sp.DEVNULL).decode().strip()
        except Exception:
            return None

    out = {
        "plan_section": "9", "arm": args.arm, "position": args.position,
        "outcome": "strongreject_score (continuous [0,1], NOT binary ASR@0.5)",
        "min_examples": args.min_examples,
        "inference": "CR1 sandwich, t(G-1) reference, plus within-domain permutation",
        "provenance": {"argv": sys.argv, "git_commit": _git("rev-parse", "HEAD"),
                       "git_dirty": bool(_git("status", "--porcelain")),
                       "python": sys.executable},
        "judge": os.path.abspath(args.judge), "extract": os.path.abspath(args.extract),
        "refusalness": os.path.abspath(args.refusalness),
        "boombness_col": args.boombness_col, "refusalness_col": args.refusalness_col,
        "cluster_by": args.cluster_by, "n": len(keys), "n_clusters": nG,
        "role_identifiability": ident, "models": models, "incremental_r2": inc,
        "n_examples_control": nex_control,
        "role_fit_rows": {"n_crossed": len(crossed_idx),
                          "n_clusters_crossed": len(set(clusters[i] for i in crossed_idx)),
                          "fitted_on": ("crossed subset only" if role_names else "not fitted"),
                          "why": ("a role dummy fitted over all rows compares the styled prompts "
                                  "against reference prompts of different content, which is the "
                                  "family-set swap the gate exists to refuse (retraction #6)")},
        "role_descriptive_only": raw_role,
        "estimand_note": (
            "Every term reports TWO point estimates. `beta_pooled` is the coefficient in the fitted "
            "model; `beta_within_domain` is the coefficient after demeaning that predictor and the "
            "outcome within cluster. `p_cr1_pooled_beta` belongs to the FIRST, "
            "`p_perm_within_domain_beta` to the SECOND. Before 2026-08-18 only `beta` and "
            "`p_within_domain_perm` were emitted, side by side, and the p was read as the p of the "
            "beta beside it (audit T5, same defect as analyze_g2.py and analyze_g64.py)."),
        "keys_renamed_2026_08_18": {"beta": "beta_pooled", "p_cr1": "p_cr1_pooled_beta",
                                    "p_within_domain_perm": "p_perm_within_domain_beta"},
        "caveat": (
            "Role is NOT in the fitted model when role_identifiability.identified is false. The "
            "descriptive role means are a family-set contrast, not a role effect, and must not be "
            "reported as one (this is the retraction-#6 failure mode). When it IS identified the "
            "role terms are fitted on the crossed subset only, and with G <= k the CR1 p-values "
            "are suppressed rather than reported: the omnibus style test on this same crossed "
            "design is analyze_g11.py's job and already exists."),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[G9] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
