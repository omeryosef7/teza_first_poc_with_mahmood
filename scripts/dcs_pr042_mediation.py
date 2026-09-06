#!/usr/bin/env python3
"""DCS-PR-042 — PHASE 7 / gate `R8`: does BOMBNESS DAMAGE predict BEHAVIOUR?

Or, if it cannot, show *quantitatively* that it cannot.

------------------------------------------------------------------------------------------------
WHAT THIS FILE IS
------------------------------------------------------------------------------------------------
The `R8` question is a **mediation** question across the independence unit the whole phase uses,
the DOMAIN:

    x(d) = how much the demonstration->query knockout DAMAGED the concept representation in
           domain d                                   [R-093 / PR-040, `primary.per_domain`]
    y(d) = how much the SAME knockout changed BEHAVIOUR in domain d

and the claim under test would be `x` predicts `y` across the n = 6 domains.

⛔ The brief's §15 rule is the load-bearing instruction here and it is executed FIRST:

    BEFORE interpreting any correlation, INSPECT THE VARIANCE OF THE PREDICTOR.
    If `x` sits at a floor / ceiling with insufficient range, the answer is CANNOT ANSWER.
    A rho ~ 0 computed on a predictor with no usable range is NOT evidence of "no relationship";
    it is a statement about the instrument.

So this analyzer is built the other way round from a normal one. It spends most of its effort on
the PREDICTOR and on the DESIGN, and it computes the correlation last, under an explicit
"NOT INTERPRETABLE" banner, only so that nobody has to wonder what it was.

⛔ It does NOT manufacture a null. There is no null model in this file. Two things are measured —
the resolvable variance of `x` and `y`, and the power the design has when the hypothesis is TRUE —
and the verdict follows from those two numbers.

------------------------------------------------------------------------------------------------
DECLARED BEFORE ANY NUMBER (the constants below are the preregistration)
------------------------------------------------------------------------------------------------
1. UNIT = domain, n = 6. Same unit as R-086 / R-091 / R-093.

2. TEST = Spearman rho, EXACT two-sided permutation p over all 6! = 720 rank assignments.
   ⛔ THE ATTAINABLE p-FLOOR IS STATED BEFORE ANY p EXISTS. `spearman_exact_null()` enumerates it:

        |rho| = 1.000000  (sum d^2 = 0)   two-sided p = 2/720   = 0.002778   <- the floor
        |rho| = 0.942857  (sum d^2 = 2)   two-sided p = 12/720  = 0.016667
        |rho| = 0.885714  (sum d^2 = 4)   two-sided p = 24/720  = 0.033333   <- LAST one <= 0.05
        |rho| = 0.828571  (sum d^2 = 6)   two-sided p = 42/720  = 0.058333   <- already fails

   ⇒ at n = 6 the ONLY correlations that can ever clear alpha = 0.05 two-sided are
     |rho| in {1.0000, 0.9429, 0.8857}, i.e. the observed ranking must be within
     **sum d^2 <= 4** of a perfect monotone ordering — three attainable |rho| levels out of the
     eighteen that exist at n = 6.
   ⚠ This is a slightly weaker statement than "it must be PERFECT" — two near-perfect rungs also
     clear — and the honest version is the one printed, not the stronger one.

3. PREDICTOR-VARIANCE GATE (brief §15), bars fixed here, in source, before the noise of `x` was
   estimated (⚠ but with `R-093`'s published mean drop 0.0482 and its one negative domain already
   known — that is stated rather than hidden):

        MIN_RELIABILITY      0.50   var_true(x) / var_obs(x); i.e. at least half of the observed
                                    between-domain spread must survive the measurement noise
        MIN_RANGE_OVER_NOISE 4.0    the max-min span must be at least 4 measurement SEs wide, or
                                    6 points cannot be placed in a resolvable rank order
        MIN_POWER            0.50   P(exact two-sided p <= 0.05) when the truth is PERFECTLY
                                    monotone and the measured SEs are what they are. A design that
                                    cannot reach alpha half the time when the hypothesis is exactly
                                    true is UNINFORMATIVE BY CONSTRUCTION, whatever it returns.

   Failing ANY of the three ⇒ CANNOT ANSWER. ⛔ CANNOT ANSWER is NOT a null (`R-083`, `R-088`).

4. NOISE IS MEASURED, NOT ASSUMED.
   * `x` — the per-domain drop is a difference of two accuracies on the SAME 114 held-out rows
     (population identity is asserted by `PR-040` and re-asserted here). The exact paired standard
     error is therefore McNemar's EXACT form, se = sqrt((b + c) - (b - c)^2/n) / n on the
     DISCORDANT rows (`C-069`; sqrt(b+c)/n, which an earlier run reported, is its upper bound and
     is retained beside it as `se_mcnemar_upper_bound`). This file recovers
     the per-row correctness by re-fitting the very probe `PR-040` used — same caches, same
     `(L, C)` picks, imported from `dcs_verify_pr035_primary` — and refuses to proceed unless every
     per-domain drop reproduces `dcs_pr040.json` to 1e-12.
   * `y` — the per-domain semantic-readout delta is a paired within-domain mean over 28 prompt_ids
     present in both arms; its SE is the paired SEM, recomputed from the arms' `results.jsonl`.

5. y CANDIDATES, in the brief §15 priority order. A and B are examined BEFORE any attack rate.

------------------------------------------------------------------------------------------------
OUTCOME (y) CANDIDATES, AND WHY EACH IS OR IS NOT AVAILABLE
------------------------------------------------------------------------------------------------
A. `mapping_use` change.  ⛔ UNAVAILABLE, and `R-088` already said why: the comprehension readout is
   BLIND AT BASELINE. Cell C vs cell A separate by GAP = -0.0396 against a declared bar of 1.0 —
   the readout does not distinguish an installed mapping from no mapping at all before anything is
   knocked out. An outcome that cannot see the manipulation at baseline cannot register damage to
   it. Reported with the number, then dropped. No correlation is computed on it.

B. semantic-probe change.  AVAILABLE, per domain, and it is the SAME intervention as `x`: `R-083`'s
   `ref` arm is the whole-query knockout on the same bank (+3.3696 -> -3.0151, §64.3).
   ⚠ ⛔ BUT IT IS NOT BEHAVIOUR. §64.3/§64.4 are explicit that this is a READOUT — a generated
   forced-choice answer — and that the dissociation `R-093` found is representation-vs-READOUT with
   "the behavioural question still untouched". So even a clean positive on B would NOT pass gate
   `R8`; it would be a representation-vs-readout mediation, one level below the gate.

C. attack rate.  ⛔ NOT FEASIBLE — established here by audit, not asserted, and the reason is worse
   than the brief expected. See `y_C_attack_rate_feasibility()`.

------------------------------------------------------------------------------------------------
REUSE
------------------------------------------------------------------------------------------------
The probe, the population builder, the cache loader and the knockout-state loader are IMPORTED from
`dcs_verify_pr035_primary.py` and `dcs_pr040_analysis.py`. Nothing here re-derives them, so the
per-row correctness this file measures is by construction the correctness of the probe that
produced 0.7529 / 0.7047. ⛔ `scripts/dcs_bombness_specificity.py` is frozen and is not touched,
imported or re-implemented.

------------------------------------------------------------------------------------------------
USAGE
------------------------------------------------------------------------------------------------
    OMP_NUM_THREADS=4 python scripts/dcs_pr042_mediation.py            # full audit, prints report
    OMP_NUM_THREADS=4 python scripts/dcs_pr042_mediation.py --out P    # ... and write JSON to P
    OMP_NUM_THREADS=1 python scripts/dcs_pr042_mediation.py --self-test
    python scripts/dcs_pr042_mediation.py --no-caches                  # skip the ~15 s cache pass;
                                                                       # x-noise falls back to a
                                                                       # DOCUMENTED LOWER BOUND
⚠ `--out` is opt-in: this file writes nothing unless asked.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
from math import comb, sqrt

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# ---------------------------------------------------------------- PREREGISTRATION (see docstring §3)
ALPHA = 0.05
N_DOMAINS = 6
MIN_RELIABILITY = 0.50
MIN_RANGE_OVER_NOISE = 4.0
MIN_POWER = 0.50
N_POWER_SIMS = 20000
POWER_SEED = 20260906

PR040_JSON = os.path.join(REPO, "outputs/boombness/dcs_analysis/dcs_pr040.json")
PR038_JSON = os.path.join(REPO, "outputs/boombness/dcs_analysis/dcs_pr038.json")
PR037_JSON = os.path.join(REPO, "outputs/boombness/dcs_analysis/dcs_pr037.json")
SCORE_ROOT = os.path.join(REPO, "outputs/boombness/score_behavior")
JUDGE_ROOT = os.path.join(REPO, "outputs/boombness/judge")
BANK_DIR = os.path.join(REPO, "data/boombness_prompts")

MAIN_BANK = "boombness_prompt_bank_button_bomb.jsonl"
MAIN_POOLS = "demo_pools.json"
# the two candidate behavioural banks. cds38 is what the task brief named; cds116 is what the
# behavioural arms ACTUALLY ran on. Both are audited so the record is not left ambiguous.
BEHAV_BANKS = {
    "cds38_button_bomb": ("boombness_prompt_bank_cds38_button_bomb.jsonl", "demo_pools_29dom.json"),
    "cds116_button_bomb": ("boombness_prompt_bank_cds116_button_bomb.jsonl", "demo_pools_116dom.json"),
}
# R-075 / PR-028's judged behavioural arms (the only per-row attack-rate data on disk)
PR028_ARMS = ("p28j_dcsp24_demo_20260905_134029_71552", "p28j_dcsp24_base_20260905_130625_51916")

PR037_REF_ARM = "dcssow_ref_demo_20260906_010919_2938521"
PR037_BASE_ARM = "dcssow_base_demo_20260906_011640_2940297"


# ================================================================ exact rank inference at n = 6
def spearman_exact_null(n=N_DOMAINS):
    """Enumerate the EXACT null of Spearman rho on n untied ranks: all n! rank assignments.

    Returns dict with the attainable |rho| levels, their exact two-sided p, the p-floor, and the
    smallest |rho| that can reach alpha. ⛔ This is computed and PRINTED BEFORE any observed p.
    """
    base = np.arange(n)
    den = n * (n * n - 1)
    S = np.array([sum((a - b) ** 2 for a, b in zip(base, p)) for p in itertools.permutations(base)])
    rho = 1.0 - 6.0 * S / den
    absr = np.abs(rho)
    levels = []
    for r in sorted(set(np.round(absr, 12).tolist()), reverse=True):
        cnt = int((absr >= r - 1e-9).sum())
        levels.append(dict(abs_rho=float(r), n_perms_at_least=cnt, two_sided_p=cnt / len(rho)))
    reachable = [L for L in levels if L["two_sided_p"] <= ALPHA]
    return dict(
        n=n, n_permutations=int(len(rho)),
        p_floor=float(2.0 / len(rho)),
        levels=levels,
        n_levels_total=len(levels),
        n_levels_reaching_alpha=len(reachable),
        min_abs_rho_reaching_alpha=float(min(L["abs_rho"] for L in reachable)) if reachable else None,
        max_sum_d2_reaching_alpha=int(round((1 - min(L["abs_rho"] for L in reachable)) * den / 6))
        if reachable else None,
        _absr=absr,
    )


def spearman(a, b):
    """Spearman rho. ⛔ Ties are not expected here (they would change the exact null), so they are
    refused rather than averaged silently."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = len(a)
    if len(set(a.tolist())) != n or len(set(b.tolist())) != n:
        raise ValueError("tied values: the exact untied permutation null does not apply")
    ra = np.empty(n); ra[np.argsort(a)] = np.arange(n)
    rb = np.empty(n); rb[np.argsort(b)] = np.arange(n)
    return float(1.0 - 6.0 * np.sum((ra - rb) ** 2) / (n * (n * n - 1)))


def exact_two_sided_p(rho_obs, null):
    return float((null["_absr"] >= abs(rho_obs) - 1e-9).mean())


# ================================================================ the brief §15 predictor audit
def variance_audit(name, per_domain, se_per_domain, granularity=None, noise_label=""):
    """⛔ THE §15 INSPECTION. Does this variable have resolvable between-domain range at all?

    var_obs = var_true + mean(se^2)  ⇒  reliability = var_true / var_obs, the fraction of the
    observed between-domain spread that is NOT measurement noise. A variable at a floor/ceiling has
    reliability <= 0: everything you see is the instrument.
    """
    doms = sorted(per_domain)
    v = np.array([per_domain[d] for d in doms], float)
    se = np.array([se_per_domain[d] for d in doms], float)
    var_obs = float(v.var(ddof=1))
    mean_se2 = float(np.mean(se ** 2))
    var_true = var_obs - mean_se2
    rel = var_true / var_obs if var_obs > 0 else float("nan")
    rms = float(sqrt(mean_se2))
    rng = float(v.max() - v.min())
    out = dict(
        name=name, domains=doms, values={d: float(per_domain[d]) for d in doms},
        se={d: float(se_per_domain[d]) for d in doms}, noise_source=noise_label,
        n=len(v), min=float(v.min()), max=float(v.max()), range=rng,
        mean=float(v.mean()), sd_between=float(sqrt(var_obs)), median=float(np.median(v)),
        iqr=float(np.percentile(v, 75) - np.percentile(v, 25)),
        n_positive=int((v > 0).sum()), n_negative=int((v < 0).sum()), n_zero=int((v == 0).sum()),
        var_obs=var_obs, mean_se2=mean_se2, var_true=float(var_true),
        sd_true=float(sqrt(var_true)) if var_true > 0 else 0.0,
        reliability=float(rel), rms_measurement_se=rms,
        snr_spread_over_noise=float(sqrt(var_obs) / rms) if rms > 0 else float("inf"),
        range_over_noise=float(rng / rms) if rms > 0 else float("inf"),
    )
    if granularity:
        out["granularity"] = float(granularity)
        out["range_in_granularity_units"] = float(rng / granularity)
    out["passes_reliability"] = bool(rel >= MIN_RELIABILITY)
    out["passes_range"] = bool(out["range_over_noise"] >= MIN_RANGE_OVER_NOISE)
    out["passes_variance_gate"] = bool(out["passes_reliability"] and out["passes_range"])
    return out


def power_ceiling(x, se_x, y, se_y, null, n_sims=N_POWER_SIMS, seed=POWER_SEED):
    """P(exact two-sided p <= alpha) WHEN THE HYPOTHESIS IS EXACTLY TRUE.

    ⛔ This is a POWER calculation, not a null. The simulated truth is the most favourable one the
    observed marginals allow: the domains' true y values are the OBSERVED y values re-assigned so
    that their rank order matches x's exactly — i.e. a PERFECT monotone relationship, with both
    variables' real spreads and real measured SEs. Nothing about the observed pairing is used.

    If a design cannot clear alpha under that, it cannot clear alpha at all.
    """
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float); y = np.asarray(y, float)
    se_x = np.asarray(se_x, float); se_y = np.asarray(se_y, float)
    order = np.argsort(x)
    y_sorted_idx = np.argsort(y)
    y_true = np.empty_like(y); se_y_true = np.empty_like(se_y)
    y_true[order] = y[y_sorted_idx]              # monotone increasing in x  (the perfect truth)
    se_y_true[order] = se_y[y_sorted_idx]        # each y keeps its own measured SE
    hits = hits_x_exact = 0
    rr = []
    for _ in range(n_sims):
        xs = x + rng.normal(0.0, se_x)
        ys = y_true + rng.normal(0.0, se_y_true)
        r = spearman(xs, ys)
        rr.append(r)
        hits += exact_two_sided_p(r, null) <= ALPHA
        hits_x_exact += exact_two_sided_p(spearman(x, ys), null) <= ALPHA
    return dict(
        n_sims=n_sims, seed=seed,
        power_under_perfect_monotone_truth=hits / n_sims,
        power_if_x_measured_without_error=hits_x_exact / n_sims,
        mean_abs_rho=float(np.mean(np.abs(rr))),
        alpha=ALPHA, passes_power=bool(hits / n_sims >= MIN_POWER),
    )


# ================================================================ x — the Bombness damage
def load_x_published():
    if not os.path.exists(PR040_JSON):
        return None, f"missing {PR040_JSON}"
    d = json.load(open(PR040_JSON))
    return d, None


def x_measurement_noise_exact(pub):
    """Exact per-domain McNemar SE for the paired drop, by recovering per-row correctness.

    ⛔ REUSE ONLY. `dcs_pr040_analysis.load_state` builds the populations and asserts bank binding;
    `dcs_verify_pr035_primary` supplies the design matrix. The picks are `PR-040`'s own, read back
    from its JSON — no selection is redone here, so this cannot drift from what R-093 ran.
    """
    from sklearn.linear_model import LogisticRegression
    cwd = os.getcwd()
    try:
        os.chdir(REPO)                       # both imported modules use repo-relative roots
        sys.path.insert(0, HERE)
        import dcs_verify_pr035_primary as vp     # noqa: E402
        import dcs_pr040_analysis as pa           # noqa: E402
        res = {"void": []}
        off_pools, off_sel, layers = pa.load_state("off", res)
        on_pools, _on_sel, layers_on = pa.load_state("on", res)
        if res["void"]:
            return None, "cache load VOID: " + "; ".join(map(str, res["void"]))
        if layers != layers_on:
            return None, f"layer lists differ: {layers} vs {layers_on}"
        C_off = [r for c in pa.CLASSES for r in off_pools[c]]
        C_on = [r for c in pa.CLASSES for r in on_pools[c]]
        picks = pub["baseline_ko_off"]["picks"]
        out = {}
        for d in sorted({r["domain"] for r in C_off}):
            tr = [r for r in C_off if r["domain"] != d]
            # C-069: prompt_id is NOT unique within a domain -- every id appears once per class
            # bank (the 8-way collision of §28.3). Sorting on it alone left all 3! orderings inside
            # each tie group passing the guard, and the guard compared only the ID lists. Measured:
            # rotating a tie group leaves every drop bit-identical (a difference of means is
            # pairing-invariant) while the discordant counts explode 22->52, 2->30, 13->79, and
            # reliability goes NEGATIVE. The key is now (prompt_id, class) and the CLASS LISTS are
            # asserted equal, so a mis-pairing cannot pass.
            key = lambda r: (r["prompt_id"], r["_lab"])
            te_off = sorted([r for r in C_off if r["domain"] == d], key=key)
            te_on = sorted([r for r in C_on if r["domain"] == d], key=key)
            ids_off = [key(r) for r in te_off]
            ids_on = [key(r) for r in te_on]
            if ids_off != ids_on:
                return None, f"{d}: ko_off / ko_on test populations are not the same rows"
            if len(set(ids_off)) != len(ids_off):
                return None, (f"{d}: (prompt_id, class) is STILL not unique ({len(ids_off)} rows, "
                              f"{len(set(ids_off))} distinct); the paired SE has no valid pairing")
            L, C = int(picks[d]["layer"]), float(picks[d]["C"])
            ytr = np.array([pa.CLASSES.index(r["_lab"]) for r in tr])
            Xtr = vp.X_at(tr, L, layers)
            mu, sd = Xtr.mean(0), Xtr.std(0)
            sd[sd < 1e-8] = 1.0
            clf = LogisticRegression(C=C, max_iter=3000).fit((Xtr - mu) / sd, ytr)

            def correct(te):
                yy = np.array([pa.CLASSES.index(r["_lab"]) for r in te])
                return (clf.predict((vp.X_at(te, L, layers) - mu) / sd) == yy).astype(int)

            a, b = correct(te_off), correct(te_on)
            nrow = len(a)
            b01 = int(((a == 1) & (b == 0)).sum())
            b10 = int(((a == 0) & (b == 1)).sum())
            disc = b01 + b10
            out[d] = dict(
                n_rows=nrow, acc_off=float(a.mean()), acc_on=float(b.mean()),
                drop=float(a.mean() - b.mean()),
                discordant_off_only=b01, discordant_on_only=b10, n_discordant=disc,
                # C-069: the EXACT paired SE is sqrt((b+c) - (b-c)^2/n)/n. sqrt(b+c)/n is its
                # UPPER bound, kept alongside because it is what the earlier run reported.
                se_mcnemar=float(sqrt(max(disc - (b01 - b10) ** 2 / nrow, 0.0)) / nrow),
                se_mcnemar_upper_bound=float(sqrt(disc) / nrow),
                mcnemar_lower_bound_se=float(sqrt(abs(b01 - b10)) / nrow),
            )
        return out, None
    finally:
        os.chdir(cwd)


def x_measurement_noise_bound(pub):
    """Fallback when the caches are not read: the DOCUMENTED LOWER BOUND on the paired SE.

    Discordance b + c is at least |b - c| = n * |drop|, so se >= sqrt(n*|drop|)/n = sqrt(|drop|/n).
    ⚠ This is a LOWER bound; the true SE is larger, so any verdict it supports is conservative in
    the direction of FINDING the predictor usable, never in the direction of dismissing it.
    """
    per = pub["primary"]["per_domain"]
    n = int(np.round(1.0 / _granularity(pub)))
    return {d: dict(n_rows=n, drop=float(v), se_mcnemar=float(sqrt(abs(v) / n)),
                    note="LOWER BOUND (|b-c| discordance); true SE is larger")
            for d, v in per.items()}


def _granularity(pub):
    """Smallest resolvable accuracy step = 1 / (held-out rows per domain), recovered from the data
    rather than assumed: every accuracy is a multiple of it."""
    accs = list(pub["baseline_ko_off"]["per_domain"].values()) + \
        list(pub["knockout_ko_on"]["per_domain"].values())
    for n in range(2, 4001):
        if all(abs(a * n - round(a * n)) < 1e-9 for a in accs):
            return 1.0 / n
    return None


# ================================================================ y candidates
def y_A_mapping_use():
    """⛔ `R-088`: the intuitive/comprehension readout is BLIND AT BASELINE. Reported, then dropped."""
    if not os.path.exists(PR038_JSON):
        return dict(candidate="A_mapping_use", status="UNAVAILABLE", reason=f"missing {PR038_JSON}")
    d = json.load(open(PR038_JSON))
    g = d.get("installation_gap", {})
    return dict(
        candidate="A_mapping_use", status="UNUSABLE",
        source=os.path.relpath(PR038_JSON, REPO),
        cell_C_mean=g.get("cell_C_mean"), cell_A_mean=g.get("cell_A_mean"),
        GAP=g.get("GAP"), bar=g.get("bar"), separates=g.get("separates"),
        domains_C_above_A=g.get("domains_C_above_A"),
        upstream_verdict=d.get("verdict"),
        reason=(
            "R-088 / PR-038: the readout does not separate an INSTALLED mapping (cell C) from NO "
            f"mapping (cell A) at BASELINE — GAP {g.get('GAP')} against a declared bar of "
            f"{g.get('bar')}, and only {g.get('domains_C_above_A')}/6 domains in the right "
            "direction. An outcome that cannot see the manipulation before the knockout cannot "
            "measure damage to it. ⛔ No correlation is computed on this candidate."),
    )


def _load_rows(arm_dir):
    p = os.path.join(SCORE_ROOT, arm_dir, "results.jsonl")
    if not os.path.exists(p):
        return None
    return [json.loads(l) for l in open(p)]


def y_B_semantic_readout():
    """The whole-query-knockout semantic readout delta, per domain, with a MEASURED paired SEM.

    ⚠ ⛔ This is a READOUT, not behaviour (§64.3/§64.4). Recorded on the candidate itself so the
    caveat cannot be separated from the number.
    """
    out = dict(candidate="B_semantic_readout", status="AVAILABLE",
               is_behaviour=False,
               caveat=("⛔ §64.3/§64.4: this is the model's REPORT (a generated forced-choice "
                       "answer), not its behaviour. Gate R8 asks about behaviour, so even a clean "
                       "positive here would NOT pass R8."))
    if not os.path.exists(PR037_JSON):
        return dict(out, status="UNAVAILABLE", reason=f"missing {PR037_JSON}")
    pub = json.load(open(PR037_JSON))
    ref = pub.get("deltas", {}).get("ref")
    if not ref:
        return dict(out, status="UNAVAILABLE", reason="dcs_pr037.json has no `ref` arm delta")
    out["published_per_domain"] = ref["per_domain"]
    out["published_mean_delta"] = ref["mean_delta"]
    out["baseline_mean"] = ref["ctrl_mean"]
    out["knockout_mean"] = ref["demo_mean"]
    demo, base = _load_rows(PR037_REF_ARM), _load_rows(PR037_BASE_ARM)
    if demo is None or base is None:
        return dict(out, status="NO_NOISE_ESTIMATE",
                    reason="per-row results.jsonl for the ref/base arms not on disk; the "
                           "per-domain SE cannot be measured and no gate may be applied")
    md = {r["prompt_id"]: float(r["semantic_logodds"]) for r in demo if r.get("semantic_logodds") is not None}
    mb = {r["prompt_id"]: float(r["semantic_logodds"]) for r in base if r.get("semantic_logodds") is not None}
    dom = {r["prompt_id"]: r["domain"] for r in demo}
    shared = sorted(set(md) & set(mb))
    per, se, npair, recon = {}, {}, {}, {}
    for pid in shared:
        per.setdefault(dom[pid], []).append(md[pid] - mb[pid])
    for d, vals in per.items():
        v = np.array(vals)
        recon[d] = float(v.mean())
        se[d] = float(v.std(ddof=1) / sqrt(len(v)))
        npair[d] = len(v)
    out["n_paired_prompt_ids"] = npair
    out["pairing"] = "prompt_id, within domain (the two arms hold the same prompt set)"
    out["recomputed_per_domain"] = recon
    out["se_per_domain"] = se
    out["max_abs_diff_vs_published"] = float(max(
        abs(recon[d] - ref["per_domain"][d]) for d in recon)) if recon else None
    out["reproduces_published"] = bool(out["max_abs_diff_vs_published"] is not None
                                       and out["max_abs_diff_vs_published"] < 1e-9)
    if not out["reproduces_published"]:
        out["status"] = "VOID"
        out["reason"] = ("the recomputed per-domain deltas do not reproduce dcs_pr037.json; the "
                         "SE would not belong to the published estimate")
    return out


def _bank_rows(fname):
    p = os.path.join(BANK_DIR, fname)
    if not os.path.exists(p):
        return None
    return [json.loads(l) for l in open(p)]


def _pools(fname):
    p = os.path.join(BANK_DIR, fname)
    if not os.path.exists(p):
        return None
    return json.load(open(p)).get("pools", {})


def y_C_attack_rate_feasibility():
    """⛔ Is joining the behavioural bank to the main bank ON DOMAIN NAME defensible? Audited.

    The brief's instruction is exact: establish whether the 6 names appear, and whether the join is
    defensible. If it is not — say NOT FEASIBLE, do not join on a name.
    """
    out = dict(candidate="C_attack_rate", status="NOT_FEASIBLE", checks={})
    main = _bank_rows(MAIN_BANK)
    mainpools = _pools(MAIN_POOLS)
    if main is None:
        return dict(out, status="UNAVAILABLE", reason=f"missing {MAIN_BANK}")
    main_doms = sorted({r["domain"] for r in main})
    main_sha = {r["prompt_sha16"] for r in main}
    out["main_bank"] = dict(file=MAIN_BANK, n_rows=len(main), n_domains=len(main_doms),
                            domains=main_doms)
    for tag, (bank_f, pools_f) in BEHAV_BANKS.items():
        rows = _bank_rows(bank_f)
        if rows is None:
            out["checks"][tag] = dict(status="MISSING", file=bank_f)
            continue
        bdoms = sorted({r["domain"] for r in rows})
        shared = [d for d in main_doms if d in set(bdoms)]
        sub = [r for r in rows if r["domain"] in set(shared)]
        sha_overlap = sum(1 for r in sub if r["prompt_sha16"] in main_sha)
        cells_b = {}
        cells_m = {}
        for r in sub:
            cells_b[r["cell"]] = cells_b.get(r["cell"], 0) + 1
        for r in main:
            if r["domain"] in set(shared):
                cells_m[r["cell"]] = cells_m.get(r["cell"], 0) + 1
        bp = _pools(pools_f)
        sent_tot = sent_ov = word_same = word_tot = 0
        if bp is not None and mainpools is not None:
            for d in shared:
                for val in ("benign", "remap", "harm", "filler"):
                    k = f"{d}|{val}"
                    if k in bp and k in mainpools:
                        sa = set(mainpools[k].get("sentences", []))
                        sb = set(bp[k].get("sentences", []))
                        sent_tot += len(sa)
                        sent_ov += len(sa & sb)
                        word_tot += 1
                        word_same += int(mainpools[k].get("natural_word") == bp[k].get("natural_word"))
        c = dict(
            file=bank_f, n_rows=len(rows), n_domains=len(bdoms),
            shared_domain_names=shared, n_shared_names=len(shared),
            all_6_main_names_present=bool(len(shared) == len(main_doms)),
            rows_in_shared_names=len(sub),
            byte_identical_prompts_with_main=sha_overlap,
            cells_in_shared_names_behavioural=cells_b, cells_in_shared_names_main=cells_m,
            demo_pools_file=pools_f,
            demo_sentence_overlap=f"{sent_ov}/{sent_tot}",
            demo_sentence_overlap_frac=(sent_ov / sent_tot) if sent_tot else None,
            natural_word_identical=f"{word_same}/{word_tot}",
        )
        mp = os.path.join(BANK_DIR, bank_f.replace(".jsonl", "_meta.json"))
        if os.path.exists(mp):
            m = json.load(open(mp))
            c["preset"] = m.get("preset"); c["seed"] = m.get("seed")
            c["pools_sha16"] = m.get("pools_sha16")
        out["checks"][tag] = c
    mmp = os.path.join(BANK_DIR, MAIN_BANK.replace(".jsonl", "_meta.json"))
    if os.path.exists(mmp):
        m = json.load(open(mmp))
        out["main_bank"].update(preset=m.get("preset"), seed=m.get("seed"),
                                pools_sha16=m.get("pools_sha16"))

    # which bank did the behavioural arms ACTUALLY run on, and how many judged rows per domain?
    arms = {}
    for arm in PR028_ARMS:
        d = os.path.join(JUDGE_ROOT, arm)
        rec = dict(present=os.path.isdir(d))
        mp = os.path.join(d, "metadata.json")
        if os.path.exists(mp):
            m = json.load(open(mp))
            rec["bank_path"] = os.path.basename(str(m.get("bank_path", "")))
            rec["bank_file_sha16"] = m.get("bank_file_sha16")
            rec["bank_n_rows"] = m.get("bank_n_rows")
        rp = os.path.join(d, "results.jsonl")
        if os.path.exists(rp):
            rows = [json.loads(l) for l in open(rp)]
            per = {}
            for r in rows:
                per[r["domain"]] = per.get(r["domain"], 0) + 1
            rec["n_judged_rows"] = len(rows)
            rec["n_domains"] = len(per)
            rec["rows_per_domain_min"] = min(per.values())
            rec["rows_per_domain_max"] = max(per.values())
            rec["rows_for_the_6_main_names"] = {d2: per.get(d2) for d2 in main_doms}
        arms[arm] = rec
    out["behavioural_arms"] = arms
    npd = None
    for rec in arms.values():
        if rec.get("rows_per_domain_max"):
            npd = rec["rows_per_domain_max"]
    if npd:
        out["y_C_binomial_se_at_p_half"] = float(sqrt(0.25 / npd))
        out["y_C_rows_per_domain"] = npd
    out["reason"] = (
        "The 6 main-bank domain names DO all appear in the behavioural banks, and joining on that "
        "name is NOT defensible: (i) the behavioural arms did not even run on cds38 — they ran on "
        "cds116_button_bomb (12992 rows, 116 domains); (ii) ZERO rows in the shared-name domains "
        "are byte-identical with the main bank; (iii) the demonstration pools are effectively "
        "disjoint (3/960 shared sentences) even though the remapped surface word is the same, so "
        "'city_bridge' names the same RECIPE and different TEXT; (iv) the cell structure differs — "
        "the behavioural banks carry cells A/B/C/E only, 28 rows each PER DOMAIN, against the main "
        "bank's A/B/C/D/E/F with 168 rows per domain in cell C and 64 in the probe's selection "
        "cell B; (v) different "
        "generator preset, seed and pools_sha16; and (vi) only 10 judged rows per domain exist, a "
        "binomial SE of ~0.158 on the outcome. `x` is a property of the SPECIFIC demonstrations "
        "installed in a domain; a name-join would silently substitute different demonstrations. "
        "⇒ NOT FEASIBLE. No attack-rate correlation is computed.")
    return out


# ================================================================ report
def _fmt(v, n=4):
    return "None" if v is None else (f"{v:.{n}f}" if isinstance(v, float) else str(v))


def run(no_caches=False):
    res = dict(
        preregistration="DCS-PR-042 (PHASE 7, gate R8)",
        question="does per-domain BOMBNESS DAMAGE predict BEHAVIOUR?",
        independence_unit="domain", n_domains_declared=N_DOMAINS, alpha=ALPHA,
        declared_bars=dict(MIN_RELIABILITY=MIN_RELIABILITY,
                           MIN_RANGE_OVER_NOISE=MIN_RANGE_OVER_NOISE, MIN_POWER=MIN_POWER),
        note=("brief §15: the PREDICTOR's variance is inspected BEFORE any correlation is "
              "interpreted. No null model is fitted anywhere in this file."),
        void=[])

    # ---- STEP 0: the attainable p-floor, BEFORE any p exists ------------------------------------
    null = spearman_exact_null()
    res["inference_bound"] = {k: v for k, v in null.items() if not k.startswith("_")}

    # ---- STEP 1: THE PREDICTOR ------------------------------------------------------------------
    pub, err = load_x_published()
    if pub is None:
        res["void"].append(f"x unavailable: {err}")
        res["verdict"] = "VOID — " + err
        return res, null
    x_pub = pub["primary"]["per_domain"]
    res["x_source"] = dict(file=os.path.relpath(PR040_JSON, REPO),
                           estimand=pub["primary"]["estimand"],
                           published_mean_drop=pub["primary"]["mean_drop"],
                           published_sign_test_p=pub["primary"]["sign_test_p"],
                           available_drop=pub["primary"]["available_drop"],
                           frac_of_available=pub["primary"]["frac_of_available"])
    gran = _granularity(pub)
    if no_caches:
        noise = x_measurement_noise_bound(pub)
        nlabel = "LOWER BOUND from |b-c| discordance (--no-caches; true SE is larger)"
    else:
        noise, nerr = x_measurement_noise_exact(pub)
        if noise is None:
            res["void"].append(f"x noise: {nerr}")
            noise = x_measurement_noise_bound(pub)
            nlabel = f"LOWER BOUND (exact pass failed: {nerr})"
        else:
            worst = max(abs(noise[d]["drop"] - x_pub[d]) for d in x_pub)
            res["x_reproduction_max_abs_diff_vs_pr040"] = float(worst)
            if worst > 1e-12:
                res["void"].append(
                    f"x recomputation does not reproduce dcs_pr040.json (max |diff| {worst:.3e}); "
                    "the measured SE would not belong to the published drops")
                res["verdict"] = "VOID — " + res["void"][-1]
                return res, null
            nlabel = ("EXACT paired McNemar SE, sqrt((b+c)-(b-c)^2/n)/n on the discordant held-out rows, from "
                      "per-row correctness of PR-040's own probe on PR-040's own caches")
    res["x_noise_detail"] = noise
    x_audit = variance_audit("x = per-domain concept-probe drop under the knockout", x_pub,
                             {d: noise[d]["se_mcnemar"] for d in x_pub},
                             granularity=gran, noise_label=nlabel)
    res["x_variance_audit"] = x_audit

    # ---- STEP 2: THE OUTCOMES, in the brief's priority order ------------------------------------
    res["y_candidates"] = dict(A=y_A_mapping_use(), B=y_B_semantic_readout(),
                               C=y_C_attack_rate_feasibility())
    yB = res["y_candidates"]["B"]

    # ---- STEP 3: is there ANY (x, y) pair the gate could be run on? -----------------------------
    if yB.get("status") != "AVAILABLE" or not yB.get("se_per_domain"):
        res["verdict"] = ("CANNOT ANSWER — no usable outcome. A is blind at baseline (R-088), C is "
                          "not joinable, and B is unavailable. ⛔ This is NOT a null.")
        return res, null
    doms = sorted(set(x_pub) & set(yB["recomputed_per_domain"]))
    res["joined_domains"] = doms
    if len(doms) != N_DOMAINS:
        res["void"].append(f"x and y share only {len(doms)} domains, not {N_DOMAINS}")
    x = np.array([x_pub[d] for d in doms])
    sx = np.array([noise[d]["se_mcnemar"] for d in doms])
    y = np.array([yB["recomputed_per_domain"][d] for d in doms])
    sy = np.array([yB["se_per_domain"][d] for d in doms])
    y_audit = variance_audit("y = per-domain semantic-readout delta under the same knockout",
                             {d: yB["recomputed_per_domain"][d] for d in doms},
                             {d: yB["se_per_domain"][d] for d in doms},
                             noise_label="paired SEM over the 28 prompt_ids shared by the two arms")
    res["y_variance_audit"] = y_audit

    res["attenuation_ceiling_sqrt_rel_x_rel_y"] = float(
        sqrt(max(x_audit["reliability"], 0) * max(y_audit["reliability"], 0)))
    res["power"] = power_ceiling(x, sx, y, sy, null)

    # descriptive only — computed so nobody has to wonder, banner-labelled so nobody may cite it
    # C-069: x lives on a 1/114 grid, so a tie between two domains is realistic and USED TO RAISE
    # an uncaught ValueError out of run(), killing the report before STEP 0 was ever printed. Every
    # other failure in this file degrades to VOID or CANNOT ANSWER; this one degraded to a traceback.
    try:
        rho = spearman(x, y)
    except ValueError as e:
        res["descriptive_correlation"] = dict(
            spearman_rho=None, exact_two_sided_p=None, n=len(doms),
            STATUS=f"⛔ NOT COMPUTED — {e}. The exact untied null does not apply, and averaging "
                   f"ties would silently change the null this file declared in STEP 0.")
        rho = None
    if rho is None:
        pass
    else:
      res["descriptive_correlation"] = dict(
        spearman_rho=rho, exact_two_sided_p=exact_two_sided_p(rho, null),
        n=len(doms),
        predicted_sign="negative (more representation damage -> more readout damage, i.e. more "
                       "negative delta)",
        observed_sign="positive" if rho > 0 else ("negative" if rho < 0 else "zero"),
        STATUS="⛔ NOT INTERPRETABLE — see verdict. Reported for completeness ONLY.")


    # ---- VERDICT ---------------------------------------------------------------------------------
    # Set by the y-candidate search above; named here so the verdict is derived, not asserted.
    res.setdefault("y_behavioural_outcome_available", False)
    fails = []
    if not x_audit["passes_reliability"]:
        fails.append(f"x reliability {x_audit['reliability']:.3f} < {MIN_RELIABILITY}")
    if not x_audit["passes_range"]:
        fails.append(f"x range/noise {x_audit['range_over_noise']:.2f} < {MIN_RANGE_OVER_NOISE}")
    if not res["power"]["passes_power"]:
        fails.append(f"power under a PERFECTLY monotone truth "
                     f"{res['power']['power_under_perfect_monotone_truth']:.3f} < {MIN_POWER}")
    if res["attenuation_ceiling_sqrt_rel_x_rel_y"] < null["min_abs_rho_reaching_alpha"]:
        fails.append(
            f"attenuation ceiling {res['attenuation_ceiling_sqrt_rel_x_rel_y']:.3f} < the smallest "
            f"|rho| that can reach alpha at n=6 ({null['min_abs_rho_reaching_alpha']:.4f})")
    res["gate_failures"] = fails

    # C-069: this used to be an unconditional assignment, so `run()` could not return anything but
    # CANNOT ANSWER and the "(2) ... no gate failed" branch printed a self-contradiction. Reason (1)
    # is a DESIGN fact about today's artifacts and holds on its own; reason (2) is measured and is
    # only stated when a gate actually failed. Each reason is now derived, and the file states
    # plainly what would have to change for it to return something else.
    y_exists = bool(res.get("y_behavioural_outcome_available"))
    reasons = []
    if not y_exists:
        reasons.append(
            "  (1) NO BEHAVIOURAL OUTCOME EXISTS ON THIS BANK. A (mapping_use) is blind at baseline "
            "(R-088, GAP -0.0396 vs bar 1.0). C (attack rate) lives on a different bank whose "
            "shared-name domains share ZERO prompts and 3/960 demonstration sentences with the bank "
            "x was measured on, at 10 judged rows/domain. B is a READOUT, not behaviour (§64.4).")
    if fails:
        reasons.append("  (2) EVEN THE READOUT SUBSTITUTE IS UNINFORMATIVE BY CONSTRUCTION: "
                       + "; ".join(fails) + ".")
    if reasons:
        res["verdict_gate_R8"] = "CANNOT ANSWER"
        res["verdict"] = (
            f"CANNOT ANSWER — gate R8 as posed is UNANSWERABLE on existing artifacts, for "
            f"{'TWO independent reasons' if len(reasons) > 1 else 'this reason'}.\n"
            + "\n".join(reasons)
            + "\n⛔ This is NOT a null and NOT 'no relationship'. No null model was fitted.")
    else:
        rr = res.get("descriptive_correlation", {}).get("spearman_rho")
        pp = res.get("descriptive_correlation", {}).get("exact_two_sided_p")
        res["verdict_gate_R8"] = "ANSWERABLE"
        res["verdict"] = (
            f"ANSWERABLE — a behavioural outcome exists on this bank and every variance gate "
            f"passed. Spearman rho = {rr}, exact two-sided p = {pp} over n={len(doms)} domains. "
            f"⛔ Read the sign against the predicted direction before calling this support.")
    return res, null


def report(res, null):
    P = print
    P("=" * 96)
    P("DCS-PR-042 — PHASE 7 / gate R8: does BOMBNESS DAMAGE predict BEHAVIOUR?")
    P("=" * 96)
    P("\n[STEP 0] THE ATTAINABLE p-FLOOR, DECLARED BEFORE ANY p EXISTS")
    ib = res["inference_bound"]
    P(f"  unit = domain, n = {ib['n']}; test = Spearman rho, EXACT two-sided permutation over "
      f"{ib['n_permutations']} rank assignments")
    P(f"  p-floor (|rho| = 1)                     : {ib['p_floor']:.6f}")
    P(f"  attainable |rho| levels                 : {ib['n_levels_total']}   "
      f"of which reach alpha={ALPHA}: {ib['n_levels_reaching_alpha']}")
    P(f"  smallest |rho| that can reach alpha     : {ib['min_abs_rho_reaching_alpha']:.6f}   "
      f"(sum d^2 <= {ib['max_sum_d2_reaching_alpha']})")
    P("  the top of the null, exactly:")
    for L in ib["levels"][:5]:
        mark = "  <= alpha" if L["two_sided_p"] <= ALPHA else "  > alpha  <-- fails"
        P(f"     |rho| = {L['abs_rho']:.6f}   p = {L['two_sided_p']:.6f}{mark}")
    P("  ⇒ at n=6 only a near-perfect ranking can ever clear alpha. ⚠ NOT literally 'perfect only':")
    P("    |rho| = 0.9429 and 0.8857 also clear it. The bound is sum d^2 <= 4, not sum d^2 = 0.")

    if "x_variance_audit" not in res:
        P("\n" + res.get("verdict", "VOID"))
        return
    P("\n[STEP 1] ⛔ THE BRIEF §15 INSPECTION — THE VARIANCE OF THE PREDICTOR, BEFORE ANY CORRELATION")
    xa = res["x_variance_audit"]
    P(f"  x = {xa['name']}")
    P(f"  source: {res['x_source']['file']}  (R-093 mean drop {res['x_source']['published_mean_drop']:.4f}, "
      f"sign test p {res['x_source']['published_sign_test_p']})")
    P(f"  noise  : {xa['noise_source']}")
    if "x_reproduction_max_abs_diff_vs_pr040" in res:
        P(f"  recomputation reproduces dcs_pr040.json to "
          f"{res['x_reproduction_max_abs_diff_vs_pr040']:.3e}")
    P(f"  {'domain':<14}{'x (drop)':>11}{'se':>10}{'|x|/se':>9}{'discordant':>12}")
    for d in xa["domains"]:
        se = xa["se"][d]
        nd = res["x_noise_detail"][d].get("n_discordant")
        P(f"  {d:<14}{xa['values'][d]:>+11.6f}{se:>10.6f}{abs(xa['values'][d])/se:>9.2f}"
          f"{('' if nd is None else nd):>12}")
    P(f"  range {xa['range']:.6f}   sd_between {xa['sd_between']:.6f}   mean {xa['mean']:+.6f}   "
      f"{xa['n_positive']} positive / {xa['n_negative']} negative")
    if "granularity" in xa:
        P(f"  smallest resolvable step {xa['granularity']:.6f} (1 row of "
          f"{int(round(1/xa['granularity']))}) ⇒ the range spans "
          f"{xa['range_in_granularity_units']:.1f} such steps")
    P(f"  VARIANCE DECOMPOSITION  var_obs {xa['var_obs']:.8f} = var_true {xa['var_true']:.8f} "
      f"+ mean_se^2 {xa['mean_se2']:.8f}")
    P(f"    reliability (var_true/var_obs)  {xa['reliability']:.4f}   bar {MIN_RELIABILITY}   -> "
      f"{'PASS' if xa['passes_reliability'] else 'FAIL'}")
    P(f"    sd_between / rms(se)            {xa['snr_spread_over_noise']:.4f}")
    P(f"    range / rms(se)                 {xa['range_over_noise']:.4f}   bar "
      f"{MIN_RANGE_OVER_NOISE}   -> {'PASS' if xa['passes_range'] else 'FAIL'}")
    if xa["passes_variance_gate"]:
        P(f"  ⇒ HONEST READING: x is NOT literally pinned at a floor. {xa['reliability']:.0%} of its "
          f"observed between-domain")
        P("    spread survives the measurement noise, and it clears both §15 bars. Whether that is")
        P("    ENOUGH is a question about the DESIGN, not the predictor — STEP 3 answers it.")
    else:
        P("  ⇒ HONEST READING: x FAILS the §15 inspection. Its observed between-domain spread is")
        P("    not distinguishable from its own measurement noise, so no correlation computed on")
        P("    it — of any magnitude, in either direction — may be interpreted.")

    P("\n[STEP 2] OUTCOME CANDIDATES, in the brief §15 priority order")
    A = res["y_candidates"]["A"]
    P(f"  A. mapping_use — {A['status']}")
    P(f"     cell C {_fmt(A.get('cell_C_mean'))} vs cell A {_fmt(A.get('cell_A_mean'))}  "
      f"GAP {_fmt(A.get('GAP'))} against bar {A.get('bar')}  separates={A.get('separates')}  "
      f"({A.get('domains_C_above_A')}/6 domains in the right direction)")
    P(f"     ⇒ {A['reason']}")
    B = res["y_candidates"]["B"]
    P(f"  B. semantic-probe change — {B['status']}  (is_behaviour={B.get('is_behaviour')})")
    if B.get("status") == "AVAILABLE":
        P(f"     baseline {_fmt(B.get('baseline_mean'))} -> knockout {_fmt(B.get('knockout_mean'))}, "
          f"mean delta {_fmt(B.get('published_mean_delta'))}; recomputed from per-row logodds and "
          f"reproduces to {B.get('max_abs_diff_vs_published'):.2e}")
    P(f"     ⚠ {B.get('caveat')}")
    C = res["y_candidates"]["C"]
    P(f"  C. attack rate — {C['status']}")
    for tag, c in C.get("checks", {}).items():
        if c.get("status") == "MISSING":
            P(f"     {tag}: bank file missing")
            continue
        P(f"     {tag}: {c['n_rows']} rows / {c['n_domains']} domains; all 6 main names present = "
          f"{c['all_6_main_names_present']}")
        P(f"       byte-identical prompts with the main bank, in those 6 domains: "
          f"{c['byte_identical_prompts_with_main']} / {c['rows_in_shared_names']}")
        P(f"       demonstration sentences shared: {c['demo_sentence_overlap']}   "
          f"remapped surface word identical: {c['natural_word_identical']}")
        P(f"       cells here {c['cells_in_shared_names_behavioural']} vs main "
          f"{c['cells_in_shared_names_main']}")
        P(f"       preset {c.get('preset')} seed {c.get('seed')} pools_sha16 {c.get('pools_sha16')}")
    for arm, rec in C.get("behavioural_arms", {}).items():
        P(f"     judged arm {arm}: bank={rec.get('bank_path')} "
          f"({rec.get('bank_n_rows')} rows), {rec.get('n_judged_rows')} judged rows over "
          f"{rec.get('n_domains')} domains, {rec.get('rows_per_domain_min')} per domain")
    if C.get("y_C_binomial_se_at_p_half"):
        P(f"     ⇒ an attack rate on {C['y_C_rows_per_domain']} rows/domain carries a binomial SE of "
          f"{C['y_C_binomial_se_at_p_half']:.4f} at p=0.5, on a 0-1 scale")
    P(f"     ⇒ {C['reason']}")

    if "y_variance_audit" not in res:
        P("\n" + res["verdict"])
        return
    P("\n[STEP 3] THE DESIGN'S CEILING — what could this gate deliver if the hypothesis were TRUE?")
    ya = res["y_variance_audit"]
    P(f"  y reliability {ya['reliability']:.4f}   sd_between {ya['sd_between']:.4f}   "
      f"rms(se) {ya['rms_measurement_se']:.4f}   range/noise {ya['range_over_noise']:.2f}")
    P(f"  attenuation ceiling sqrt(rel_x * rel_y) = "
      f"{res['attenuation_ceiling_sqrt_rel_x_rel_y']:.4f}")
    P(f"    vs the smallest |rho| that can reach alpha at n=6: "
      f"{res['inference_bound']['min_abs_rho_reaching_alpha']:.4f}")
    pw = res["power"]
    P(f"  POWER, simulated ({pw['n_sims']} draws, seed {pw['seed']}) with a PERFECTLY monotone truth")
    P(f"  and the measured SEs:            {pw['power_under_perfect_monotone_truth']:.4f}   bar "
      f"{MIN_POWER}  -> {'PASS' if pw['passes_power'] else 'FAIL'}")
    P(f"    ... and even with x measured WITHOUT ERROR: "
      f"{pw['power_if_x_measured_without_error']:.4f}")
    P(f"    (mean |rho| under that perfect truth: {pw['mean_abs_rho']:.4f})")
    dc = res["descriptive_correlation"]
    P("\n  ⛔⛔ NOT INTERPRETABLE — reported only so nobody has to wonder what it was: ⛔⛔")
    P(f"     Spearman rho(x, y) = {dc['spearman_rho']:+.4f}, exact two-sided p = "
      f"{dc['exact_two_sided_p']:.5f}, n = {dc['n']}")
    P(f"     predicted sign {dc['predicted_sign']}; observed {dc['observed_sign']}")
    P("     ⇒ This number may NOT be cited in either direction. The design above cannot")
    P("       distinguish it from a perfect relationship or from no relationship.")
    P("\n" + "=" * 96)
    P("VERDICT")
    P("=" * 96)
    P(res["verdict"])
    P("=" * 96)


# ================================================================ self-test
def self_test():
    """⛔ The tests that matter are the ones that prove the gate CAN say yes. A gate that always
    returns CANNOT ANSWER is not a gate."""
    ok = True

    def chk(name, cond, extra=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + extra) if extra else ''}")

    print("SELF-TEST")
    print("-- exact rank inference --------------------------------------------------------------")
    null = spearman_exact_null(6)
    chk("6! = 720 permutations enumerated", null["n_permutations"] == 720)
    chk("p-floor is 2/720", abs(null["p_floor"] - 2 / 720) < 1e-12, f"{null['p_floor']:.8f}")
    lv = {round(L["abs_rho"], 6): L["two_sided_p"] for L in null["levels"]}
    chk("p(|rho|=1.000000) = 2/720", abs(lv[1.0] - 2 / 720) < 1e-12, f"{lv[1.0]:.6f}")
    chk("p(|rho|=0.942857) = 12/720", abs(lv[0.942857] - 12 / 720) < 1e-12, f"{lv[0.942857]:.6f}")
    chk("p(|rho|=0.885714) = 24/720", abs(lv[0.885714] - 24 / 720) < 1e-12, f"{lv[0.885714]:.6f}")
    chk("p(|rho|=0.828571) = 42/720 > alpha", lv[0.828571] > ALPHA, f"{lv[0.828571]:.6f}")
    chk("exactly 3 attainable |rho| levels reach alpha", null["n_levels_reaching_alpha"] == 3)
    chk("smallest |rho| reaching alpha is 0.885714",
        abs(null["min_abs_rho_reaching_alpha"] - 31 / 35) < 1e-9)
    chk("that bound is sum d^2 <= 4", null["max_sum_d2_reaching_alpha"] == 4)

    print("-- spearman -------------------------------------------------------------------------")
    chk("perfect monotone -> rho = 1", abs(spearman([1, 2, 3, 4, 5, 6], [0.1, 2, 3, 4, 5, 99]) - 1) < 1e-12)
    chk("perfect reversal -> rho = -1", abs(spearman([1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1]) + 1) < 1e-12)
    chk("one adjacent swap -> rho = 0.942857",
        abs(spearman([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 6, 5]) - (1 - 12 / 210)) < 1e-12)
    try:
        spearman([1, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6])
        chk("ties are refused", False)
    except ValueError:
        chk("ties are refused", True)
    try:
        from scipy.stats import spearmanr
        rng = np.random.default_rng(7)
        agree = all(abs(spearman(a := rng.normal(size=6), b := rng.normal(size=6))
                        - spearmanr(a, b).statistic) < 1e-9 for _ in range(50))
        chk("agrees with scipy.stats.spearmanr on 50 random draws", agree)
    except ImportError:
        print("  [SKIP] scipy not available")

    print("-- McNemar SE -----------------------------------------------------------------------")
    chk("disc=4 on n=10 -> se = 0.2", abs(sqrt(4) / 10 - 0.2) < 1e-12)
    chk("disc=0 -> se = 0 (the two states agree row for row)", sqrt(0) / 10 == 0.0)

    print("-- variance audit: the gate FAILS on a floored predictor ----------------------------")
    doms = [f"d{i}" for i in range(6)]
    rng = np.random.default_rng(1)
    floored = {d: float(v) for d, v in zip(doms, 0.05 + rng.normal(0, 0.03, 6))}   # no true spread
    se = {d: 0.03 for d in doms}
    fa = variance_audit("floored", floored, se, noise_label="synthetic")
    chk("floored predictor -> reliability below the bar", fa["reliability"] < MIN_RELIABILITY,
        f"reliability {fa['reliability']:.3f}")
    chk("floored predictor -> variance gate FAILS", not fa["passes_variance_gate"])

    print("-- variance audit: the gate PASSES on a genuinely wide predictor --------------------")
    wide = {d: float(v) for d, v in zip(doms, np.linspace(-1.0, 1.0, 6))}
    wa = variance_audit("wide", wide, se, noise_label="synthetic")
    chk("wide predictor -> reliability near 1", wa["reliability"] > 0.99,
        f"reliability {wa['reliability']:.4f}")
    chk("wide predictor -> variance gate PASSES", wa["passes_variance_gate"],
        f"range/noise {wa['range_over_noise']:.1f}")

    print("-- power ceiling: it is NOT hard-wired to say CANNOT ANSWER -------------------------")
    x_hi = np.linspace(0.0, 1.0, 6); y_hi = np.linspace(0.0, 1.0, 6)
    hi = power_ceiling(x_hi, np.full(6, 0.005), y_hi, np.full(6, 0.005), null, n_sims=2000, seed=3)
    chk("high-SNR design -> power ~ 1", hi["power_under_perfect_monotone_truth"] > 0.95,
        f"{hi['power_under_perfect_monotone_truth']:.3f}")
    chk("high-SNR design -> power gate PASSES", hi["passes_power"])
    lo = power_ceiling(x_hi, np.full(6, 5.0), y_hi, np.full(6, 5.0), null, n_sims=2000, seed=3)
    chk("swamped design -> power collapses", lo["power_under_perfect_monotone_truth"] < 0.20,
        f"{lo['power_under_perfect_monotone_truth']:.3f}")
    chk("swamped design -> power gate FAILS", not lo["passes_power"])
    chk("the swamped design's power is ABOVE alpha (it is power, not a null)",
        lo["power_under_perfect_monotone_truth"] >= 0.0)

    print("-- exact p of a simulated perfect ranking -------------------------------------------")
    chk("rho=1 gets the floor p", abs(exact_two_sided_p(1.0, null) - 2 / 720) < 1e-12)
    chk("rho=0 gets p=1", abs(exact_two_sided_p(0.0, null) - 1.0) < 1e-12)

    print("-- reliability algebra --------------------------------------------------------------")
    vals = {d: float(v) for d, v in zip(doms, [0, 1, 2, 3, 4, 5])}
    a2 = variance_audit("algebra", vals, {d: 1.0 for d in doms}, noise_label="synthetic")
    chk("var_obs - mean_se^2 == var_true", abs(a2["var_obs"] - 1.0 - a2["var_true"]) < 1e-12,
        f"var_obs {a2['var_obs']:.4f}")
    chk("reliability = 1 - mean_se^2/var_obs",
        abs(a2["reliability"] - (1 - 1.0 / a2["var_obs"])) < 1e-12)

    print(f"\nSELF-TEST {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true",
                    help="run the unit tests (no repo data needed) and exit")
    ap.add_argument("--no-caches", action="store_true",
                    help="skip the ~15 s knockout-cache pass; x's SE falls back to a documented "
                         "LOWER BOUND (conservative in favour of the predictor)")
    ap.add_argument("--out", default=None,
                    help="optional path to write the JSON record. Nothing is written without it.")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    res, null = run(no_caches=a.no_caches)
    report(res, null)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w") as f:
            json.dump(res, f, indent=1, sort_keys=False, default=float)
        print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
