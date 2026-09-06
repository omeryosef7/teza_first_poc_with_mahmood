#!/usr/bin/env python3
"""DCS thesis-scale POWER ANALYSIS -- run BEFORE any GPU spend (mandate section 20).

CPU only. No model, no network, no GPU. Reads only:
  data/boombness_prompts/boombness_prompt_bank_ts116_{button,basket}_{bomb,knife,gun}.jsonl
  data/boombness_prompts/dcs_ts116_domain_split.json
  outputs/boombness/dcs_analysis/dcs_bombness_specificity{,_rerun}.json   (OLD 6-domain record)

Writes nothing. Prints a deterministic numbers block to stdout.

THE DESIGN UNDER TEST
  flagship confirmatory test: 3-way concept probe {bomb,knife,gun}
  cell C, query_kind=semantic_one_word, n_examples=4
  train on 70 TRAIN domains, hyperparameters chosen on 23 VALIDATION domains,
  evaluated on 23 untouched TEST domains. Independence unit = DOMAIN. Chance = 1/3.

DISCIPLINE (this repo has shipped four verifier harnesses whose checks passed over empty sets)
  * every check binds to a counted set and RAISES if the count is zero;
  * `--selftest` demonstrates every check going RED under a deliberate mutation;
  * every empirical number is re-derived from raw bank rows or raw per-domain
    accuracies, never from a producer-written summary field.

usage:
  python scripts/dcs_ts_power.py --all
  python scripts/dcs_ts_power.py --selftest
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK_DIR = os.path.join(REPO, "data", "boombness_prompts")
CODEWORDS = ("button", "basket")
CONCEPTS = ("bomb", "knife", "gun")
SPLIT_MANIFEST = os.path.join(BANK_DIR, "dcs_ts116_domain_split.json")
OLD_SPEC = [
    os.path.join(REPO, "outputs", "boombness", "dcs_analysis", "dcs_bombness_specificity.json"),
    os.path.join(REPO, "outputs", "boombness", "dcs_analysis", "dcs_bombness_specificity_rerun.json"),
]

# The flagship cell selector. `cell` in these banks is the single letter "C";
# the long form "natural_doublespeak" lives in `condition`. Getting this wrong
# silently binds ZERO rows -- which is exactly mutation M_CELL below.
FLAGSHIP = dict(cell="C", query_kind="semantic_one_word", n_examples=4)

CHANCE_3WAY = 1.0 / 3.0


# --------------------------------------------------------------------------- utilities
class ZeroBinding(RuntimeError):
    """Raised whenever a check would evaluate over an empty set."""


def require_nonempty(n, what):
    if n == 0:
        raise ZeroBinding(f"CHECK BOUND TO ZERO ROWS: {what}")
    return n


def bank_path(codeword, concept):
    return os.path.join(BANK_DIR, f"boombness_prompt_bank_ts116_{codeword}_{concept}.jsonl")


def load_flagship_rows(codeword, concept, selector=None):
    """Re-derive the flagship cell from RAW bank rows. Never from _meta.json."""
    sel = dict(FLAGSHIP if selector is None else selector)
    out = []
    with open(bank_path(codeword, concept)) as fh:
        for line in fh:
            r = json.loads(line)
            if all(r.get(k) == v for k, v in sel.items()):
                out.append(r)
    return out


def clopper_pearson(k, n, alpha=0.05):
    lo = 0.0 if k == 0 else stats.beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.isf(alpha / 2, k + 1, n - k)
    return float(lo), float(hi)


def perm_p(obs, null_stats, naive=False):
    """The ONLY defensible permutation p estimator: (1 + #{null >= obs}) / (B + 1).

    Its attainable floor is 1/(B+1) -- 1/201 = 0.004975124378109453 at B=200, which is
    precisely the previous phase's headline p. `naive=True` is mutation M_NAIVEP.
    """
    null = np.asarray(null_stats, dtype=float)
    B = require_nonempty(null.size, "permutation null is empty")
    ge = int(np.sum(null >= obs - 1e-12))
    return (ge / B) if naive else (1.0 + ge) / (B + 1.0)


def perm_floor(B, naive=False):
    return 0.0 if naive else 1.0 / (B + 1.0)


def sign_floor_two_sided(n, one_sided=False):
    """Smallest p an exact binomial sign test at p0=0.5 can return with n domains."""
    if n <= 0:
        raise ZeroBinding("sign test with n=0 domains")
    p = 0.5 ** n
    return p if one_sided else min(1.0, 2.0 * p)


def sign_floor_bruteforce(n, one_sided=False):
    """Independent re-derivation by exhaustive enumeration of all 2^n sign patterns."""
    if n > 22:
        raise ValueError("brute force only for n<=22")
    total = 1 << n
    cnt = 0
    for mask in range(total):
        k = bin(mask).count("1")
        if k == n:                      # the most extreme outcome
            cnt += 1
    one = cnt / total
    return one if one_sided else min(1.0, 2.0 * one)


def t_power(n, delta, sd, alpha=0.05, two_sided=True, drop_beta=False):
    """Power of the one-sample t-test of H0: mean = chance, at true mean offset `delta`."""
    if n < 2:
        return float("nan")
    df = n - 1
    nc = delta / (sd / math.sqrt(n))
    a = alpha / 2 if two_sided else alpha
    tcrit = stats.t.isf(a, df)
    pw = stats.nct.sf(tcrit, df, nc)
    if two_sided:
        pw += stats.nct.cdf(-tcrit, df, nc)
    if not np.isfinite(pw):
        # scipy's noncentral t underflows at large noncentrality; the normal
        # approximation is exact to >6 decimals in that regime. Never emit NaN.
        pw = float(stats.norm.sf(tcrit - nc) + (stats.norm.cdf(-tcrit - nc) if two_sided else 0.0))
    return float(min(1.0, max(0.0, pw)))


def t_mde(n, sd, alpha=0.05, power=0.80, drop_beta=False):
    """Minimum detectable mean offset above chance. drop_beta=True is mutation M_NOBETA."""
    if drop_beta:                       # deliberately wrong: ignores the type-II term
        return float(stats.t.isf(alpha / 2, n - 1) * sd / math.sqrt(n))
    lo, hi = 1e-6, 10.0 * sd + 1.0
    f = lambda d: t_power(n, d, sd, alpha) - power
    if f(hi) < 0:
        return float("nan")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return float(0.5 * (lo + hi))


def binom_test_two_sided(k, n, p0):
    return float(stats.binomtest(k, n, p0, alternative="two-sided").pvalue)


def sign_power(n, pi, pi0=0.5, alpha=0.05):
    """Exact power of the two-sided sign test at true per-domain success prob `pi`."""
    ks = np.arange(n + 1)
    rej = np.array([binom_test_two_sided(int(k), n, pi0) <= alpha for k in ks])
    pmf = stats.binom.pmf(ks, n, pi)
    return float(pmf[rej].sum())


def sign_mde(n, pi0=0.5, alpha=0.05, power=0.80):
    for pi in np.arange(pi0, 1.0 + 1e-9, 0.001):
        if sign_power(n, float(pi), pi0, alpha) >= power:
            return float(pi)
    return float("nan")


# --------------------------------------------------------------------------- section 0
def section0_bind():
    """Bind the flagship cell in all six banks, from raw rows. Reports exact counts."""
    manifest = json.load(open(SPLIT_MANIFEST))
    assign = manifest["assign"]
    require_nonempty(len(assign), "split manifest `assign`")
    dsplit_counts = Counter(assign.values())

    per_bank = {}
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            rows = load_flagship_rows(cw, cc)
            require_nonempty(len(rows), f"flagship cell in {cw}_{cc}")
            pd = Counter(r["domain"] for r in rows)
            per_bank[f"{cw}_{cc}"] = dict(
                n_rows=len(rows),
                n_domains=len(pd),
                rows_per_domain=sorted(set(pd.values())),
                bank_blocks=sorted(set(r["bank_block"] for r in rows)),
                within_split=dict(Counter(r["split"] for r in rows)),
                domains_covered_by_manifest=sum(1 for d in pd if d in assign),
            )
    # rows the flagship 3-way probe actually gets, per domain
    m_one_codeword = 3 * per_bank["button_bomb"]["rows_per_domain"][0]
    m_two_codewords = 2 * m_one_codeword
    return dict(manifest=dict(field=manifest["field_name"], seed=manifest["seed"],
                              sha16=manifest["manifest_sha16"],
                              dsplit=dict(dsplit_counts)),
                per_bank=per_bank,
                rows_per_domain_per_concept=per_bank["button_bomb"]["rows_per_domain"][0],
                m_test_rows_per_domain_1cw=m_one_codeword,
                m_test_rows_per_domain_2cw=m_two_codewords)


# --------------------------------------------------------------------------- section 1
def section1_floors(n_test=23):
    perm = {}
    for B in (200, 1000, 2000, 10000):
        fl = perm_floor(B)
        perm[B] = dict(floor=fl,
                       mc_se_at_p05=math.sqrt(0.05 * 0.95 / B),
                       mc_se_at_p005=math.sqrt(0.005 * 0.995 / B),
                       rel_se_at_p005=math.sqrt(0.005 * 0.995 / B) / 0.005,
                       floor_below_alpha=fl < 0.05,
                       # a p is a MEASURED TAIL only if it is not the floor; the
                       # smallest measured (non-floor) value is 2/(B+1)
                       smallest_measured=2.0 / (B + 1.0))
    sign = {}
    for n in (6, 12, 23, 38, 116):
        sign[n] = dict(floor_two_sided=sign_floor_two_sided(n),
                       floor_one_sided=sign_floor_two_sided(n, one_sided=True),
                       n_distinct_p_values=n + 1)
    # exhaustive exchangeability space of the GROUP permutation (3! relabels per domain)
    space = {n: 6.0 ** n for n in (6, 12, 23, 38, 116)}
    # degenerate "global relabel" mass that C-058/PR-039 had to condition away
    glob = {n: 6.0 / 6.0 ** n for n in (6, 12, 23, 38, 116)}
    glob2 = {n: 2.0 / 2.0 ** n for n in (6, 12, 23, 38, 116)}   # 2-class contrasts
    return dict(perm=perm, sign=sign, perm_space=space,
                global_relabel_mass_k3=glob, global_relabel_mass_k2=glob2,
                headline_floor_B200=perm_floor(200))


# --------------------------------------------------------------------------- section 2
def load_old_per_domain():
    """Re-derive the OLD 6-domain per-domain accuracies from the raw artifacts.

    These are the ONLY empirical per-domain accuracies in the record. They come from the
    UNALIGNED 6-domain banks (948/1008 cell-C rows differed across concepts), so they are
    an ASSUMPTION about the new banks, not a measurement of them.
    """
    out = {}
    for path in OLD_SPEC:
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        for key in ("P2_primary", "P2_basket_lexical_transfer"):
            pd = d.get(key, {}).get("per_domain")
            if pd:
                out.setdefault(key, {})[os.path.basename(path)] = dict(pd)
    require_nonempty(len(out), "OLD 6-domain per-domain accuracies")
    return out


def infer_denominator(accs, max_m=400):
    """Recover the per-domain row count m from the accuracies' common denominator."""
    for m in range(2, max_m + 1):
        if all(abs(a * m - round(a * m)) < 1e-9 for a in accs):
            return m
    return None


def section2_mde(old, m_new_1cw, m_new_2cw):
    prim = old["P2_primary"]["dcs_bombness_specificity.json"]
    accs = np.array([prim[k] for k in sorted(prim)], dtype=float)
    require_nonempty(accs.size, "old P2_primary per-domain accuracies")
    m_old = infer_denominator(accs.tolist())
    mean = float(accs.mean())
    sd_obs = float(accs.std(ddof=1))
    # variance decomposition: observed spread = true between-domain spread + binomial noise
    within = float(np.mean(accs * (1 - accs) / m_old)) if m_old else float("nan")
    sd_between2 = max(0.0, sd_obs ** 2 - within)
    sd_between = math.sqrt(sd_between2)

    lex = old["P2_basket_lexical_transfer"]["dcs_bombness_specificity.json"]
    lex_a = np.array([lex[k] for k in sorted(lex)], dtype=float)

    def projected_sd(m, p=mean):
        return math.sqrt(sd_between2 + p * (1 - p) / m)

    # The SD itself is estimated from SIX domains. Its own 95% CI (chi-square, df=5) is wide,
    # and the upper end is what a power claim has to survive.
    df_old = accs.size - 1
    sd_lo = sd_obs * math.sqrt(df_old / stats.chi2.isf(0.025, df_old))
    sd_hi = sd_obs * math.sqrt(df_old / stats.chi2.isf(0.975, df_old))
    sd_grid = [0.05, 0.10, round(sd_obs, 4), 0.15, 0.20, 0.25, round(sd_hi, 4), 1.0 / 3.0]
    mde23 = {sd: t_mde(23, sd) for sd in sd_grid}
    return dict(
        old_primary=dict(per_domain={k: prim[k] for k in sorted(prim)}, mean=mean,
                         sd_sample=sd_obs, m_rows_per_domain=m_old,
                         binomial_within_var=within,
                         sd_between_domain_est=sd_between,
                         mean_check_vs_published=abs(mean - 0.7485380116959064)),
        old_lexical_transfer=dict(mean=float(lex_a.mean()), sd_sample=float(lex_a.std(ddof=1)),
                                  per_domain={k: lex[k] for k in sorted(lex)}),
        projected_sd_new_1cw=projected_sd(m_new_1cw),
        projected_sd_new_2cw=projected_sd(m_new_2cw),
        m_new_1cw=m_new_1cw, m_new_2cw=m_new_2cw,
        mde_n23=mde23,
        sd_uncertainty=dict(df=df_old, sd_point=sd_obs, sd_ci95_lo=sd_lo, sd_ci95_hi=sd_hi,
                            mde_n23_at_sd_ci95_hi=t_mde(23, sd_hi),
                            mde_n29_at_sd_ci95_hi=t_mde(29, sd_hi),
                            mde_n58_at_sd_ci95_hi=t_mde(58, sd_hi),
                            note="chi-square CI for a SD estimated from 6 domains; the upper "
                                 "end is the honest planning value"),
        distribution_free=dict(
            sd_max_on_unit_interval=0.5,
            sd_max_on_chance_to_one=(1.0 - CHANCE_3WAY) / 2.0,
            mde_n23_at_sd_max=t_mde(23, (1.0 - CHANCE_3WAY) / 2.0),
            note="values confined to [1/3,1] have sample SD <= (1-1/3)/2 = 1/3",
        ),
        sign_test=dict(k_needed_n23=min(k for k in range(24)
                                        if k > 11.5 and binom_test_two_sided(k, 23, 0.5) <= 0.05),
                       mde_pi_n23=sign_mde(23), mde_pi_n6=sign_mde(6),
                       mde_pi_n29=sign_mde(29), mde_pi_n38=sign_mde(38)),
    )


# --------------------------------------------------------------------------- section 3
def section3_curves(sd_list, n_list=(6, 12, 23, 29, 38, 58, 116),
                    deltas=(0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40)):
    curves = {}
    for sd in sd_list:
        for n in n_list:
            for d in deltas:
                curves[(round(sd, 4), n, d)] = t_power(n, d, sd)
    mde = {(round(sd, 4), n): t_mde(n, sd) for sd in sd_list for n in n_list}
    return dict(power=curves, mde=mde, n_list=list(n_list), deltas=list(deltas),
                sd_list=[round(s, 4) for s in sd_list])


# --------------------------------------------------------------------------- section 4
def section4_icc(old_block, m_1cw, m_2cw, rows_by_domain_feature):
    accs = np.array(list(old_block["per_domain"].values()), dtype=float)
    m_old = old_block["m_rows_per_domain"]
    pbar = float(accs.mean())
    sd_between2 = old_block["sd_between_domain_est"] ** 2
    total_var_indicator = pbar * (1 - pbar)
    icc_correct = sd_between2 / total_var_indicator if total_var_indicator > 0 else float("nan")

    def deff(m, icc):
        return 1.0 + (m - 1) * icc

    tab = {}
    for m, n_dom, tag in ((m_old, 6, "old 6-domain design"),
                          (m_1cw, 23, "new, 1 codeword"),
                          (m_2cw, 23, "new, 2 codewords"),
                          (m_2cw, 116, "new, 2 codewords, all domains")):
        D = deff(m, icc_correct)
        N = m * n_dom
        tab[tag] = dict(m_rows_per_domain=m, n_domains=n_dom, n_rows=N,
                        deff=D, n_eff=N / D, icc=icc_correct,
                        z_inflation_if_rows_treated_iid=math.sqrt(D))
    # what a row-level p LOOKS like when the honest domain-level p is 0.05 / 0.01
    D = deff(m_2cw, icc_correct)
    overstate = {}
    for p_true in (0.05, 0.01, 0.001):
        z = stats.norm.isf(p_true / 2)
        overstate[p_true] = float(2 * stats.norm.sf(z * math.sqrt(D)))
    return dict(icc_correctness_indicator=icc_correct, table=tab,
                row_level_p_when_domain_p_is=overstate,
                text_feature_icc=rows_by_domain_feature)


def measure_text_icc(feature="n_chars"):
    """Empirical one-way-ANOVA ICC of an INPUT-SURFACE feature over domains, from raw rows.

    This is not the ICC of the neural readout (that is UNKNOWN before extraction). It is a
    measurement of how much of the *stimulus* variance in the flagship cell is between-domain,
    which lower-bounds how domain-locked anything computed from these prompts can be.
    """
    vals = defaultdict(list)
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            for r in load_flagship_rows(cw, cc):
                v = r.get(feature)
                if isinstance(v, (int, float)):
                    vals[r["domain"]].append(float(v))
    require_nonempty(len(vals), f"text feature `{feature}` over domains")
    groups = [np.array(v) for v in vals.values()]
    ns = np.array([g.size for g in groups])
    require_nonempty(int(ns.sum()), f"rows carrying `{feature}`")
    k = len(groups)
    grand = float(np.concatenate(groups).mean())
    ssb = float(sum(g.size * (g.mean() - grand) ** 2 for g in groups))
    ssw = float(sum(((g - g.mean()) ** 2).sum() for g in groups))
    dfb, dfw = k - 1, int(ns.sum()) - k
    msb, msw = ssb / dfb, (ssw / dfw if dfw > 0 else 0.0)
    m0 = (ns.sum() - (ns ** 2).sum() / ns.sum()) / (k - 1)
    sb2 = max(0.0, (msb - msw) / m0)
    if (sb2 + msw) <= 0:
        return dict(feature=feature, n_domains=k, n_rows=int(ns.sum()),
                    rows_per_domain=sorted(set(ns.tolist())), msb=msb, msw=msw,
                    icc=None,
                    note="feature is CONSTANT across all rows -- zero total variance, "
                         "ICC undefined (this is a fact about the bank, not a failure)")
    icc = sb2 / (sb2 + msw)
    return dict(feature=feature, n_domains=k, n_rows=int(ns.sum()),
                rows_per_domain=sorted(set(ns.tolist())), msb=msb, msw=msw,
                icc=float(icc), note="")


# --------------------------------------------------------------------------- section 5
def hanley_mcneil_se(auc, n1, n2):
    q1 = auc / (2 - auc)
    q2 = 2 * auc ** 2 / (1 + auc)
    return math.sqrt((auc * (1 - auc) + (n1 - 1) * (q1 - auc ** 2) + (n2 - 1) * (q2 - auc ** 2))
                     / (n1 * n2))


def section5_secondary(rows_per_domain_per_concept):
    n_per_class = rows_per_domain_per_concept              # 1 codeword
    auc_se = {a: hanley_mcneil_se(a, n_per_class, n_per_class) for a in (0.60, 0.70, 0.80, 0.90)}
    auc_se2 = {a: hanley_mcneil_se(a, 2 * n_per_class, 2 * n_per_class)
               for a in (0.60, 0.70, 0.80, 0.90)}
    # domain-mean AUROC vs 0.5, one-sample t at n=23
    sd_grid = [0.05, 0.08, 0.10, 0.15, 0.20]
    mde_auc = {sd: 0.5 + t_mde(23, sd) for sd in sd_grid}
    # paired patching: per-domain paired difference, n=23
    dz_mde = {n: t_mde(n, 1.0) for n in (6, 12, 23, 29, 38, 58, 116)}   # MDE in SD units = dz
    wilcoxon_floor = {n: min(1.0, 2.0 / (2.0 ** n)) for n in (6, 12, 23, 29, 38)}
    return dict(auroc_within_domain_se_1cw=auc_se, auroc_within_domain_se_2cw=auc_se2,
                n_per_class_per_domain_1cw=n_per_class,
                mde_domain_mean_auroc_n23=mde_auc,
                paired_dz_mde=dz_mde, wilcoxon_signed_rank_floor=wilcoxon_floor)


# --------------------------------------------------------------------------- section 6
def simulate_pipeline(n_domains=116, n_train=70, n_val=23, n_test=23,
                      n_per_concept=10, dim=8, n_layers=12, tau_domain=1.0, tau_group=1.2,
                      c_grid=(0.03, 0.3, 3.0), n_perm=200, rng=None,
                      perm_unit="group", arms=("validation", "test")):
    """One replicate of the FULL flagship pipeline on PURE-NOISE features.

    No concept signal exists anywhere. Features carry a domain random effect (shared by every
    row of a domain at every layer) and a (layer, domain, concept) group random effect --
    the nuisance structure the real banks have, since all 10 rows of one concept in one domain
    share a demonstration pool.

    The selection space is the REAL one: n_layers x |c_grid| candidates. Both arms are scored
    from the SAME fitted candidates, so the validation-vs-test comparison is paired.
    A correctly calibrated pipeline must reject at ~alpha.
    """
    rng = rng or np.random.default_rng(0)
    doms = np.arange(n_domains)
    rng.shuffle(doms)
    tr = doms[:n_train]
    va = doms[n_train:n_train + n_val]
    te = doms[n_train + n_val:n_train + n_val + n_test]
    require_nonempty(te.size, "simulated test domains")

    n_rows = n_domains * 3 * n_per_concept
    y = np.tile(np.repeat(np.arange(3), n_per_concept), n_domains)
    g = np.repeat(np.arange(n_domains), 3 * n_per_concept)
    u = rng.normal(0, tau_domain, size=(n_domains, dim))
    Xs = []
    for _L in range(n_layers):
        v = rng.normal(0, tau_group, size=(n_domains, 3, dim))
        base = u[g] + v[g, y] + rng.normal(0, 1.0, size=(n_rows, dim))
        Xs.append(base)

    mtr, mva, mte = np.isin(g, tr), np.isin(g, va), np.isin(g, te)
    require_nonempty(int(mtr.sum()), "simulated train rows")
    require_nonempty(int(mte.sum()), "simulated test rows")

    def per_domain_acc(pred, ytrue, gg, ds):
        accs = []
        for d in ds:
            sel = gg == d
            if sel.sum() == 0:
                raise ZeroBinding(f"test domain {d} bound zero rows")
            accs.append(float((pred[sel] == ytrue[sel]).mean()))
        return np.array(accs)

    cands = {}
    for L in range(n_layers):
        X = Xs[L]
        mu, sd = X[mtr].mean(0), X[mtr].std(0)
        sd[sd < 1e-8] = 1.0
        Z = (X - mu) / sd
        for C in c_grid:
            clf = LogisticRegression(C=C, max_iter=1000)
            clf.fit(Z[mtr], y[mtr])
            pv = clf.predict(Z[mva]); pt = clf.predict(Z[mte])
            cands[(L, C)] = dict(
                val=float(per_domain_acc(pv, y[mva], g[mva], va).mean()),
                test_pred=pt,
                test=float(per_domain_acc(pt, y[mte], g[mte], te).mean()))
    require_nonempty(len(cands), "candidate (layer, C) grid")

    y_te, g_te = y[mte], g[mte]
    out = {}
    for arm in arms:
        key = "val" if arm == "validation" else "test"
        star = max(cands, key=lambda k: cands[k][key])
        pred_te = cands[star]["test_pred"]
        obs_pd = per_domain_acc(pred_te, y_te, g_te, te)
        obs = float(obs_pd.mean())
        null = np.empty(n_perm)
        for b in range(n_perm):
            if perm_unit == "group":
                y_perm = y_te.copy()
                for d in te:
                    sel = g_te == d
                    mapping = rng.permutation(3)
                    y_perm[sel] = mapping[y_te[sel]]
            elif perm_unit == "row":   # mutation M_ROWPERM: ignores intra-domain correlation
                y_perm = rng.permutation(y_te)
            else:
                raise ValueError(perm_unit)
            null[b] = per_domain_acc(pred_te, y_perm, g_te, te).mean()
        out[arm] = dict(p=perm_p(obs, null), obs=obs, cand=star,
                        n_candidates=len(cands),
                        frac_domains_above_chance=float((obs_pd > CHANCE_3WAY).mean()))
    return out


def section6_fpr(reps=200, n_perm=200, seed=20260907, arms=("validation", "test"),
                 perm_unit="group", n_test=23, **kw):
    rng = np.random.default_rng(seed)
    acc = {a: dict(p=[], obs=[], above=[]) for a in arms}
    ncand = None
    for _ in range(reps):
        r = simulate_pipeline(rng=rng, n_perm=n_perm, perm_unit=perm_unit,
                              n_test=n_test, arms=arms, **kw)
        for a in arms:
            acc[a]["p"].append(r[a]["p"]); acc[a]["obs"].append(r[a]["obs"])
            acc[a]["above"].append(r[a]["frac_domains_above_chance"])
            ncand = r[a]["n_candidates"]
    out = {}
    for a in arms:
        ps = np.array(acc[a]["p"])
        require_nonempty(ps.size, f"FPR arm {a}")
        k = int((ps <= 0.05).sum())
        lo, hi = clopper_pearson(k, reps)
        out[a] = dict(reps=reps, n_perm=n_perm, n_candidates=ncand, n_test_domains=n_test,
                      perm_unit=perm_unit, n_reject=k, fpr=k / reps, ci95=(lo, hi),
                      covers_nominal=(lo <= 0.05 <= hi),
                      median_p=float(np.median(ps)),
                      null_mean_obs_acc=float(np.mean(acc[a]["obs"])),
                      pi0_frac_domains_above_chance=float(np.mean(acc[a]["above"])))
    if "validation" in out and "test" in out:
        base = out["validation"]["fpr"]
        out["inflation_test_over_validation"] = (out["test"]["fpr"] / base if base > 0
                                                 else float("inf"))
    return out


# --------------------------------------------------------------------------- checks
def run_checks(mutation=None, fast=False):
    """Every check returns (name, ok, detail). Each binds to a counted set.

    Mutations (each must turn its check RED):
      M_CELL     select the flagship cell with the long-form condition string -> 0 rows
      M_NAIVEP   permutation p = #{>=obs}/B          -> floor becomes 0
      M_ONESIDED sign-test floor reported one-sided  -> mismatches brute force
      M_NOBETA   MDE drops the type-II term          -> realised power ~0.5, not 0.80
      M_NOICC    ICC forced to 0                     -> design effect 1, n_eff = N
      M_TESTSEL  hyperparameter chosen on TEST       -> FPR far above nominal 0.05
      M_ROWPERM  row-level permutation null          -> FPR far above nominal 0.05
    """
    res = []

    # K1 -- the flagship cell binds, in all six banks, to a counted set
    try:
        sel = dict(FLAGSHIP)
        if mutation == "M_CELL":
            sel["cell"] = "natural_doublespeak"
        counts = {}
        for cw in CODEWORDS:
            for cc in CONCEPTS:
                rows = load_flagship_rows(cw, cc, sel)
                require_nonempty(len(rows), f"flagship cell {cw}_{cc}")
                pdc = Counter(r["domain"] for r in rows)
                counts[f"{cw}_{cc}"] = (len(rows), len(pdc), tuple(sorted(set(pdc.values()))))
        ok = all(v == (1160, 116, (10,)) for v in counts.values())
        res.append(("K1 flagship_binding", ok, f"6 banks -> {sorted(set(counts.values()))}"))
    except ZeroBinding as e:
        res.append(("K1 flagship_binding", False, f"ZeroBinding: {e}"))

    # K2 -- the permutation floor is 1/(B+1) and an unbeatable observation hits it exactly
    naive = mutation == "M_NAIVEP"
    detail = []
    ok2 = True
    for B in (200, 1000, 2000, 10000):
        null = np.zeros(B)
        p = perm_p(1e9, null, naive=naive)      # observation no permutation can reach
        want = perm_floor(B, naive=False)
        detail.append(f"B={B}: p={p:.12g} want={want:.12g}")
        ok2 &= abs(p - want) < 1e-15
    ok2 &= abs(perm_floor(200) - 0.004975124378109453) < 1e-15
    res.append(("K2 perm_floor_is_1_over_Bplus1", ok2, "; ".join(detail)))

    # K3 -- sign-test floor, re-derived by exhaustive enumeration
    one = mutation == "M_ONESIDED"
    ok3, d3 = True, []
    for n in (6, 12, 20):
        got = sign_floor_two_sided(n, one_sided=one)
        want = sign_floor_bruteforce(n, one_sided=False)
        ok3 &= abs(got - want) < 1e-15
        d3.append(f"n={n}: {got:.10g} vs bruteforce {want:.10g}")
    ok3 &= sign_floor_two_sided(6) > 0.005     # n=6 sign test CANNOT produce p=0.005
    res.append(("K3 sign_floor_matches_bruteforce", ok3, "; ".join(d3)))

    # K4 -- the analytic MDE really delivers 0.80 power in simulation
    rng = np.random.default_rng(7)
    n, sd = 23, 0.10
    d = t_mde(n, sd, drop_beta=(mutation == "M_NOBETA"))
    R = 4000 if fast else 20000
    hits = 0
    for _ in range(R):
        x = rng.normal(d, sd, size=n)
        t = x.mean() / (x.std(ddof=1) / math.sqrt(n))
        hits += int(abs(t) > stats.t.isf(0.025, n - 1))
    pw = hits / R
    ok4 = 0.775 <= pw <= 0.825
    res.append(("K4 mde_delivers_80pct_power", ok4, f"MDE={d:.5f} simulated power={pw:.4f} (R={R})"))

    # K5 -- design effect strictly exceeds 1 and n_eff is strictly below N
    old = load_old_per_domain()
    prim = old["P2_primary"]["dcs_bombness_specificity.json"]
    accs = np.array([prim[k] for k in sorted(prim)])
    require_nonempty(accs.size, "old per-domain accuracies for ICC")
    m_old = infer_denominator(accs.tolist())
    within = float(np.mean(accs * (1 - accs) / m_old))
    sb2 = max(0.0, float(accs.var(ddof=1)) - within)
    pbar = float(accs.mean())
    icc = 0.0 if mutation == "M_NOICC" else sb2 / (pbar * (1 - pbar))
    m, ndom = 60, 23
    D = 1 + (m - 1) * icc
    ok5 = (icc > 0) and (D > 1.0) and (m * ndom / D < m * ndom)
    res.append(("K5 icc_positive_and_deff_gt_1", ok5,
                f"icc={icc:.6f} deff(m=60)={D:.4f} n_eff={m*ndom/D:.1f} of N={m*ndom}"))

    # K6 -- pipeline FPR at nominal 0.05 (small rep count in selftest)
    reps = 120 if fast else 200
    arm = "test" if mutation == "M_TESTSEL" else "validation"
    pu = "row" if mutation == "M_ROWPERM" else "group"
    fpr = section6_fpr(reps=reps, n_perm=200, arms=(arm,), perm_unit=pu)[arm]
    ok6 = fpr["covers_nominal"]
    res.append(("K6 pipeline_fpr_covers_nominal_0.05", ok6,
                f"arm={arm} perm={pu} fpr={fpr['fpr']:.4f} CI95=({fpr['ci95'][0]:.4f},{fpr['ci95'][1]:.4f}) reps={reps}"))
    return res


def selftest():
    print("=" * 78)
    print("SELFTEST -- every check must be GREEN unmutated and RED under its mutation")
    print("=" * 78)
    base = run_checks(None, fast=True)
    print("\n[baseline, no mutation]")
    allok = True
    for name, ok, det in base:
        print(f"  {'GREEN' if ok else 'RED  '}  {name}  --  {det}")
        allok &= ok
    if not allok:
        print("\nFAIL: baseline is not all-GREEN.")
        return 1

    targets = {"M_CELL": "K1 flagship_binding",
               "M_NAIVEP": "K2 perm_floor_is_1_over_Bplus1",
               "M_ONESIDED": "K3 sign_floor_matches_bruteforce",
               "M_NOBETA": "K4 mde_delivers_80pct_power",
               "M_NOICC": "K5 icc_positive_and_deff_gt_1",
               "M_TESTSEL": "K6 pipeline_fpr_covers_nominal_0.05",
               "M_ROWPERM": "K6 pipeline_fpr_covers_nominal_0.05"}
    verdict = True
    for mut, target in targets.items():
        got = dict((n, (ok, d)) for n, ok, d in run_checks(mut, fast=True))
        ok, det = got[target]
        flipped = not ok
        verdict &= flipped
        print(f"\n[mutation {mut}] target {target}")
        print(f"  {'RED   (correct)' if flipped else 'GREEN (WRONG -- check cannot fail)'}  --  {det}")
    print("\n" + "=" * 78)
    print("SELFTEST VERDICT:", "PASS -- every check is falsifiable" if verdict
          else "FAIL -- at least one check cannot fail")
    return 0 if verdict else 1


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--nperm", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20260907)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.all:
        ap.error("pass --all or --selftest")

    np.set_printoptions(precision=6, suppress=True)

    print("#" * 78)
    print("# SECTION 0 -- BINDING (counts re-derived from raw bank rows)")
    print("#" * 78)
    s0 = section0_bind()
    print(json.dumps(s0, indent=2, sort_keys=True))

    print("\n" + "#" * 78)
    print("# SECTION 1 -- ATTAINABLE p-FLOORS at n_test = 23")
    print("#" * 78)
    s1 = section1_floors()
    print(json.dumps(s1, indent=2, sort_keys=True, default=float))

    print("\n" + "#" * 78)
    print("# SECTION 2 -- MDE")
    print("#" * 78)
    old = load_old_per_domain()
    s2 = section2_mde(old, s0["m_test_rows_per_domain_1cw"], s0["m_test_rows_per_domain_2cw"])
    print(json.dumps(s2, indent=2, sort_keys=True, default=float))

    print("\n" + "#" * 78)
    print("# SECTION 3 -- POWER CURVES")
    print("#" * 78)
    sd_list = [0.08, 0.10, s2["projected_sd_new_2cw"], s2["projected_sd_new_1cw"],
               s2["old_primary"]["sd_sample"], 0.20, 0.25,
               s2["sd_uncertainty"]["sd_ci95_hi"]]
    s3 = section3_curves(sorted(set(round(x, 4) for x in sd_list)))
    print("  power(n, delta) by SD:")
    for sd in s3["sd_list"]:
        print(f"  SD={sd}")
        hdr = "    n  " + "  ".join(f"d={d:.2f}" for d in s3["deltas"]) + "   MDE"
        print(hdr)
        for n in s3["n_list"]:
            row = "  ".join(f"{s3['power'][(sd, n, d)]:6.3f}" for d in s3["deltas"])
            print(f"    {n:3d}  {row}   {s3['mde'][(sd, n)]:.4f}")

    print("\n" + "#" * 78)
    print("# SECTION 4 -- ICC AND THE ROW-LEVEL TEMPTATION")
    print("#" * 78)
    txt = [measure_text_icc(f) for f in ("n_chars", "n_target_occurrences", "n_preamble_lines", "n_demos_emitted")]
    s4 = section4_icc(s2["old_primary"], s0["m_test_rows_per_domain_1cw"],
                      s0["m_test_rows_per_domain_2cw"], txt)
    print(json.dumps(s4, indent=2, sort_keys=True, default=float))

    print("\n" + "#" * 78)
    print("# SECTION 5 -- AUROC AND PAIRED PATCHING")
    print("#" * 78)
    s5 = section5_secondary(s0["rows_per_domain_per_concept"])
    print(json.dumps(s5, indent=2, sort_keys=True, default=float))

    print("\n" + "#" * 78)
    print(f"# SECTION 6 -- FALSE-POSITIVE CALIBRATION ON PURE NOISE (reps={a.reps})")
    print("#" * 78)
    s6 = section6_fpr(reps=a.reps, n_perm=a.nperm, seed=a.seed)
    print(json.dumps(s6, indent=2, sort_keys=True, default=float))
    print("\n  [diagnostic] row-level permutation instead of group permutation:")
    s6r = section6_fpr(reps=max(60, a.reps // 3), n_perm=a.nperm, seed=a.seed,
                       arms=("validation",), perm_unit="row")
    print(json.dumps(s6r, indent=2, sort_keys=True, default=float))
    print("\n  [diagnostic] n_test = 6 domains, validation-selected, group permutation:")
    s6n6 = section6_fpr(reps=max(60, a.reps // 3), n_perm=a.nperm, seed=a.seed,
                        arms=("validation",), n_test=6)
    print(json.dumps(s6n6, indent=2, sort_keys=True, default=float))


if __name__ == "__main__":
    main()
