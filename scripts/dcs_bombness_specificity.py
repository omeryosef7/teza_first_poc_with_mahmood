#!/usr/bin/env python3
"""DCS-PR-031 / 031a / 031c analyzer — is the codeword's hidden state BOMB-specific?

FROZEN BEFORE ITS DATA. Every threshold, class set, fold scheme and exclusion in this file is
fixed by the preregistration in
`external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`
(§6 `PR-031`, §7 `PR-031a`, §8 `A-020`, §9 `PR-031c`). Nothing here may be tuned after an outcome
is read; changing a threshold requires a `C-xxx` correction in that log, not an edit here.

THE TWO PROBES (`PR-031a`)
  P2 (SOLE PRIMARY)  train on cell C of the TRAINING domains, test on cell C of the HELD-OUT
                     domain. The surface token is the codeword in every class, so token identity
                     carries ZERO information and cannot solve the task.
  P1 (SECONDARY)     train on cell B (explicit concept word) + cell A (literal), test on cell C.
                     Demoted by `A-020` §8.1: cell A is a DIFFERENT CORPUS in each concept bank
                     (bomb-knife benign overlap 0/40), so P1 is contaminated across concepts and
                     its failure may NOT be read as a concept negative.

WHY NOT `semantic_forced_choice` (§2.3): its question names both options ("...refer to a button or
to a bomb?") and that word differs by bank, so a probe would read the concept off the QUESTION.
It is `occurrence_analysis_safe=False` on 288/288 rows and is disqualified as a probe channel.

CLASS SET: `club` is EXCLUDED from the primary on mechanistic, PRE-OUTCOME grounds (`A-020` §8.3 —
in `lab_safety|harm` the club pool uses `club` to mean a ROOM). It is still run and reported.
"""
from __future__ import annotations

import argparse, collections, glob, json, os, re, sys, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
from clustered_stats import cluster_sign_test  # noqa: E402

# ---------------------------------------------------------------- preregistered constants
CODEWORDS        = ("button", "basket")
CONCEPTS         = ("bomb", "knife", "gun", "club")
PRIMARY_CLASSES  = ("bomb", "knife", "gun")      # club excluded, A-020 §8.3
PRIMARY_CODEWORD = "button"                       # basket = lexical transfer (gate R3)
PRIMARY_CHANNEL  = "semantic_one_word"            # PR-031c
REPLICATION_CHANNEL = "comprehension_usage"
PRIMARY_NEXAMPLES = (4, 8)                        # PR-031 §6.2
LAYERS_ALLOWED   = tuple(range(6, 15))            # inherited band L6-14; selection confined here
C_GRID           = (0.01, 0.1, 1.0, 10.0)
ALPHA            = 0.05
P1_CAPABILITY_GATE = 0.60                         # PR-031 §6.6, held-out cell-B accuracy
MAX_OCCURRENCE_FAILURE = 0.02                     # PR-031 §6.2
EXPECT_ROWS_PER_BANK = 2736


def chance(n_classes: int) -> float:
    return 1.0 / n_classes


# ---------------------------------------------------------------- loading
def load_bank(path):
    return [json.loads(l) for l in open(path)]


def load_reps(run_dir):
    """Load the extractor's final-occurrence cache: {prompt_id: Tensor[len(layers), H]}.

    C5/PR-035 §23.4(6): refuse an in-progress run. §17.3 recorded this hole and fixed it only in
    the installation analyzer; the sibling that produces the headline still read whatever was on
    disk, and a run dir appears the moment its job starts.
    """
    import torch
    if not os.path.exists(os.path.join(run_dir, "DONE.json")):
        raise SystemExit(f"VOID: run has no DONE.json (still writing?): {run_dir}")
    p = os.path.join(run_dir, "cache", "final_occurrence_reps.pt")
    if not os.path.exists(p):
        raise SystemExit(f"missing rep cache: {p}")
    blob = torch.load(p, map_location="cpu")
    layers = list(blob["layers"])
    reps = {k: v.float().numpy() for k, v in blob["reps"].items()}
    return layers, reps


def build_rows(bank_rows, layers, reps, *, channel, cells, n_examples, bank_sha, codeword, concept,
               exclude_concept_word):
    """One record per usable row. Key is (bank_sha, prompt_id) — prompt_id ALONE IS NOT A KEY:
    it is identical across all eight banks (A-019 §2.2).

    `exclude_concept_word` implements PR-035 §23.1 / C-050: drop every row whose `full_prompt`
    contains this bank's concept word on WORD BOUNDARIES, case-insensitively. The rule reads prompt
    TEXT ONLY — never a hidden state, never an accuracy — so it selects the same rows whatever the
    result. C-050 §25.2 fixes its SCOPE: it is applied to every population that is ever a TEST set
    (C, F, C_n0) and to A, and NOT to B, which is a training/selection population whose surface word
    IS the concept by construction (48/48 rows contain it, so applying it there empties the cell).
    """
    pat = re.compile(r"\b" + re.escape(concept) + r"\b", re.IGNORECASE)
    out, missing, excluded, retained = [], 0, collections.Counter(), collections.Counter()
    for r in bank_rows:
        if r.get("query_kind") != channel or r.get("cell") not in cells:
            continue
        if n_examples is not None and r.get("n_examples") not in n_examples:
            continue
        # C-053 §28.1: the exclusion is ONE uniform rule over all cells -- concept word present AND
        # this row's surface is NOT that word. No cell is named, so there is no carve-out to defend.
        if exclude_concept_word and pat.search(r["full_prompt"]) and r.get("target_surface") != concept:
            excluded[f'{r["cell"]}/{r.get("bank_block")}/n{r["n_examples"]}'] += 1
            continue
        retained[f'{r["cell"]}/{r.get("bank_block")}/n{r["n_examples"]}'] += 1
        pid = r["prompt_id"]
        if pid not in reps:
            missing += 1
            continue
        out.append(dict(key=(bank_sha, pid), pid=pid, cell=r["cell"], domain=r["domain"],
                        block=r.get("bank_block"), split=r.get("split"),
                        n_examples=r["n_examples"], family=r.get("family_id"),
                        codeword=codeword, concept=concept, n_chars=len(r["full_prompt"]),
                        vec=reps[pid], layers=layers))
    return out, missing, dict(excluded), dict(retained)


def X_at(rows, layer, layers):
    j = layers.index(layer)
    return np.stack([r["vec"][j] for r in rows])


# ---------------------------------------------------------------- core classifier
def fit_predict(train, test, layer, layers, C, classes, label_of, balanced=False):
    """L2 multinomial logistic regression. Standardised with TRAINING-FOLD statistics only.

    `balanced` (C-053 §28.5) reports the mean of per-class recalls and weights the classes in the
    fit. It is mandatory for any contrast whose classes are not roughly equal in size: the cell-F
    comparator is 228 bomb rows against 24, so a constant "bomb" predictor scores 0.906 against a
    printed chance of 0.5, and the group-permutation null does NOT absorb that -- permuting swaps
    which class is the majority, so the null sits near 0.5 while the observed statistic is lifted
    by imbalance alone. That is a manufactured positive, and it is the C-049 signature.
    """
    from sklearn.linear_model import LogisticRegression
    ytr = np.array([classes.index(label_of(r)) for r in train])
    yte = np.array([classes.index(label_of(r)) for r in test])
    if len(set(ytr.tolist())) < 2:
        return None
    Xtr, Xte = X_at(train, layer, layers), X_at(test, layer, layers)
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd < 1e-8] = 1.0
    Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd
    clf = LogisticRegression(C=C, max_iter=3000,
                             class_weight=("balanced" if balanced else None))
    clf.fit(Xtr, ytr)
    pred = clf.predict(Xte)
    proba = clf.predict_proba(Xte)
    if balanced:
        recs = [float((pred[yte == k] == k).mean()) for k in sorted(set(yte.tolist()))]
        acc = float(np.mean(recs)) if recs else 0.0
    else:
        acc = float((pred == yte).mean())
    return dict(acc=acc, n=len(yte), balanced=bool(balanced), pred=pred.tolist(),
                true=yte.tolist(), proba=proba.tolist(), classes=list(classes))


def select_layer_C(sel_rows, layers, classes, label_of):
    """PR-031 §6.3: inner leave-one-domain-out CV over the TRAINING domains ONLY.

    The selection quantity is accuracy on the SELECTION cell (cell B by default), never on the
    confirmation cell. This is what stops the layer being chosen on the outcome.
    """
    doms = sorted({r["domain"] for r in sel_rows})
    best, best_acc = None, -1.0
    for L in LAYERS_ALLOWED:
        if L not in layers:
            continue
        for C in C_GRID:
            accs = []
            for d in doms:
                tr = [r for r in sel_rows if r["domain"] != d]
                te = [r for r in sel_rows if r["domain"] == d]
                if not tr or not te:
                    continue
                res = fit_predict(tr, te, L, layers, C, classes, label_of)
                if res:
                    accs.append(res["acc"])
            if accs and float(np.mean(accs)) > best_acc:
                best_acc, best = float(np.mean(accs)), (L, C)
    return best, best_acc


def loo_domain(rows, layers, classes, label_of, *, selection_rows=None, tag="", group="domain",
               train_rows=None, balanced=False):
    """Outer leave-one-GROUP-out (group='domain' is the declared unit; 'block' gives the
    held-out template-family secondary of PR-031c §9.2).

    `train_rows` (C-050 §25.3) makes the TRAINING population different from the TEST population,
    which is what PR-035 §23.4(1)'s P1 actually asks for: train on cell B (+A as `literal`), test on
    cell C. Without it P1 trained on cell C and was therefore P2 wearing a fourth class label that
    no row ever carried. The held-out GROUP is removed from the training population too, so a
    domain never appears on both sides.
    """
    doms = sorted({r[group] for r in rows})
    per_domain, picks = {}, {}
    train_acc = {}
    pool_tr = rows if train_rows is None else train_rows
    for d in doms:
        tr = [r for r in pool_tr if r.get(group) != d]
        te = [r for r in rows if r[group] == d]
        if not tr or not te:
            continue
        # A class with no training example cannot be predicted, and scoring the survivors against
        # the FULL class set's chance level is exactly the C-049 §22.5 defect. Refuse instead.
        if len({label_of(r) for r in tr}) < len(classes):
            continue
        if selection_rows is not None:
            sel = [r for r in selection_rows if r.get(group) != d]
            pick, _ = select_layer_C(sel, layers, classes, label_of)
        else:
            pick, _ = select_layer_C(tr, layers, classes, label_of)
        if pick is None:
            continue
        L, C = pick
        res = fit_predict(tr, te, L, layers, C, classes, label_of, balanced=balanced)
        if res:
            per_domain[d] = res["acc"]
            picks[d] = dict(layer=L, C=C, n_test=res["n"], n_train=len(tr))
            # PR-031a §7.6 capability gate: the fit must beat chance ON ITS OWN TRAINING FOLD.
            selfr = fit_predict(tr, tr, L, layers, C, classes, label_of, balanced=balanced)
            if selfr:
                train_acc[d] = selfr["acc"]
    ch = chance(len(classes))
    deltas = [per_domain[d] - ch for d in sorted(per_domain)]
    st = cluster_sign_test(deltas, alpha=ALPHA)
    return dict(tag=tag, classes=list(classes), chance=ch, group=group, balanced=bool(balanced),
                metric=("balanced_accuracy" if balanced else "accuracy"), per_domain=per_domain,
                picks=picks, train_fold_acc=train_acc,
                mean_train_fold_acc=float(np.mean(list(train_acc.values()))) if train_acc else None,
                fit_capable=bool(train_acc and float(np.mean(list(train_acc.values()))) > ch),
                n_domains=len(per_domain), mean_acc=float(np.mean(list(per_domain.values())))
                if per_domain else None,
                n_above_chance=int(sum(1 for v in per_domain.values() if v > ch)),
                sign_test=dict(st), sign_summary=st.summary())


def length_only_control(rows, classes, label_of, tag=""):
    """PR-031c: mandatory. Nearest-class-mean on prompt length alone, same folds.
    Pre-data value on the comprehension_usage population was 0.240 vs chance 0.250."""
    doms = sorted({r["domain"] for r in rows})
    per_domain = {}
    for d in doms:
        tr = [r for r in rows if r["domain"] != d]
        te = [r for r in rows if r["domain"] == d]
        means = {}
        for c in classes:
            v = [r["n_chars"] for r in tr if label_of(r) == c]
            if v:
                means[c] = float(np.mean(v))
        if not means or not te:
            continue
        ok = sum(1 for r in te
                 if min(means, key=lambda c: abs(r["n_chars"] - means[c])) == label_of(r))
        per_domain[d] = ok / len(te)
    ch = chance(len(classes))
    return dict(tag=tag, chance=ch, per_domain=per_domain,
                mean_acc=float(np.mean(list(per_domain.values()))) if per_domain else None)


# ---------------------------------------------------------------- permutation null (PR-031d)
def group_permute(rows, rng, classes):
    """Relabel the three concept GROUPS within each domain by a random permutation of `classes`.

    This is the correct exchangeability for this design. Permuting individual ROWS would break the
    within-(domain, concept) correlation that the real data carries -- every row of one concept in
    one domain shares a demonstration pool -- and would therefore build an ANTI-CONSERVATIVE null.
    Permuting whole groups preserves that structure exactly and tests the one thing at issue:
    whether the concept LABEL is attached to the state.
    """
    out = []
    for d in sorted({r["domain"] for r in rows}):
        perm = list(classes)
        rng.shuffle(perm)
        mapping = dict(zip(classes, perm))
        for r in rows:
            if r["domain"] == d:
                q = dict(r)
                # `perm_group` lets a contrast whose groups are CELLS rather than concepts
                # (bomb-C vs benign-remap-F) use the same whole-group exchangeability.
                q["perm_label"] = mapping[r.get("perm_group", r["concept"])]
                out.append(q)
    return out


def loo_with_picks(rows, layers, classes, label_of, picks, train_rows=None, train_label_of=None,
                   balanced=False, group="domain"):
    """Outer LOO-domain using a FIXED (layer, C) per fold -- no selection inside.

    When `train_rows` is given the training population is separate (P1), and it keeps its REAL
    labels under permutation: the null being tested is that the TEST states carry no concept
    information, not that the training corpus is unlabelled.
    """
    per_domain = {}
    pool_tr = rows if train_rows is None else train_rows
    tr_lab = label_of if train_label_of is None else train_label_of
    # `group` must match how `picks` is keyed. The LOBO secondary folds on bank_block, and
    # iterating domains there would match no pick at all and silently return an empty null (p=None).
    for d in sorted({r[group] for r in rows}):
        if d not in picks:
            continue
        tr = [r for r in pool_tr if r.get(group) != d]
        te = [r for r in rows if r[group] == d]
        if not tr or not te or len({tr_lab(r) for r in tr}) < len(classes):
            continue
        if train_rows is None:
            res = fit_predict(tr, te, picks[d]["layer"], layers, picks[d]["C"], classes, label_of,
                              balanced=balanced)
        else:
            res = fit_predict_xy(tr, te, picks[d]["layer"], layers, picks[d]["C"], classes,
                                 tr_lab, label_of)
        if res:
            per_domain[d] = res["acc"]
    return per_domain


def fit_predict_xy(train, test, layer, layers, C, classes, train_label_of, test_label_of):
    """`fit_predict` with DIFFERENT label functions for the train and test populations."""
    from sklearn.linear_model import LogisticRegression
    ytr = np.array([classes.index(train_label_of(r)) for r in train])
    yte = np.array([classes.index(test_label_of(r)) for r in test])
    if len(set(ytr.tolist())) < 2:
        return None
    Xtr, Xte = X_at(train, layer, layers), X_at(test, layer, layers)
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd < 1e-8] = 1.0
    Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd
    clf = LogisticRegression(C=C, max_iter=3000)
    clf.fit(Xtr, ytr)
    pred = clf.predict(Xte)
    return dict(acc=float((pred == yte).mean()), n=len(yte))


def permutation_test(rows, layers, classes, label_of, picks, n_perm, seed, observed_mean,
                     train_rows=None, balanced=False, group="domain"):
    """One-sided permutation p on the mean held-out accuracy, in the PREDICTED direction.

    The (layer, C) picks are held fixed and are legitimate to reuse: PR-031 selects them on cell B,
    which the permutation does not touch, so the selection is invariant under the null being tested.
    """
    rng = np.random.default_rng(seed)
    perm_classes = sorted({r.get("perm_group", r["concept"]) for r in rows})
    null = []
    for _ in range(n_perm):
        perm_rows = group_permute(rows, rng, perm_classes)
        pd = loo_with_picks(perm_rows, layers, classes, lambda r: r["perm_label"], picks,
                            train_rows=train_rows, balanced=balanced, group=group,
                            train_label_of=None if train_rows is None else label_of)
        if pd:
            null.append(float(np.mean(list(pd.values()))))
    if not null:
        return dict(n_perm=0, p_one_sided=None, null_mean=None)
    null = np.array(null)
    p = (1.0 + float((null >= observed_mean).sum())) / (1.0 + len(null))
    return dict(n_perm=len(null), p_one_sided=p, p_floor=1.0 / (1.0 + len(null)),
                null_mean=float(null.mean()), null_sd=float(null.std()),
                null_q05=float(np.quantile(null, 0.05)),
                null_q50=float(np.quantile(null, 0.50)),
                null_q95=float(np.quantile(null, 0.95)),
                observed_mean=observed_mean,
                excess_over_null=float(observed_mean - null.mean()))


# ---------------------------------------------------------------- self-test (runs with no GPU data)
def self_test():
    """Validate the pipeline on synthetic data BEFORE any real hidden state exists.

    Two cases with known answers. A planted class signal must be detected; pure noise must land at
    chance. If either fails, the analyzer is broken and no real result from it may be trusted.
    """
    rng = np.random.default_rng(20260905)
    doms = [f"d{i}" for i in range(6)]
    layers = list(LAYERS_ALLOWED)
    H = 64

    def make(signal):
        rows = []
        centres = {c: rng.normal(0, 1, H) for c in PRIMARY_CLASSES}
        for c in PRIMARY_CLASSES:
            for d in doms:
                for i in range(12):
                    base = rng.normal(0, 1, (len(layers), H))
                    if signal:
                        base += signal * centres[c][None, :]
                    rows.append(dict(key=(c, f"{c}{d}{i}"), pid=f"{c}{d}{i}", cell="C", domain=d,
                                     block="core2x2", split="dev", n_examples=4, family=i,
                                     codeword="button", concept=c, n_chars=600,
                                     vec=base, layers=layers))
        return rows

    lab = lambda r: r["concept"]
    hot = loo_domain(make(1.4), layers, PRIMARY_CLASSES, lab, tag="selftest_signal")
    cold = loo_domain(make(0.0), layers, PRIMARY_CLASSES, lab, tag="selftest_noise")
    ch = chance(len(PRIMARY_CLASSES))
    ok_hot = hot["mean_acc"] > 0.75
    ok_cold = abs(cold["mean_acc"] - ch) < 0.12
    print(f"[self-test] planted signal : mean acc {hot['mean_acc']:.3f} (want >0.75)  -> "
          f"{'PASS' if ok_hot else 'FAIL'}")
    print(f"[self-test] pure noise     : mean acc {cold['mean_acc']:.3f} (want ~{ch:.3f}) -> "
          f"{'PASS' if ok_cold else 'FAIL'}")
    print(f"[self-test] noise sign test: {cold['sign_summary']}")
    if not (ok_hot and ok_cold):
        raise SystemExit("SELF-TEST FAILED — analyzer is not trustworthy; do not run on real data")
    print("[self-test] OK")
    return 0


def calibrate(n_rep: int, n_perm: int = 60):
    """Measure the FALSE-POSITIVE RATE of the decision rule on synthetic data with NO signal.

    This exists because the first self-test produced 6/6 "significant" on pure noise against the
    THEORETICAL chance of 1/3: finite-sample held-out accuracy under a pipeline that contains a
    selection step does not centre on 1/k. The permutation null (PR-031d) is the fix, and this is
    the check that the fix works. A rule whose FPR exceeds alpha is not usable.
    """
    rng = np.random.default_rng(7)
    layers = list(LAYERS_ALLOWED)
    H, doms = 64, [f"d{i}" for i in range(6)]
    fp_perm = fp_sign = 0
    for rep in range(n_rep):
        rows = []
        for c in PRIMARY_CLASSES:
            for d in doms:
                for i in range(12):
                    rows.append(dict(key=(c, f"{c}{d}{i}"), pid=f"{c}{d}{i}", cell="C", domain=d,
                                     block="b", split="dev", n_examples=4, family=i,
                                     codeword="button", concept=c, n_chars=600,
                                     vec=rng.normal(0, 1, (len(layers), H)), layers=layers))
        lab = lambda r: r["concept"]
        obs = loo_domain(rows, layers, PRIMARY_CLASSES, lab, tag="cal")
        pt = permutation_test(rows, layers, PRIMARY_CLASSES, lab, obs["picks"], n_perm,
                              1000 + rep, obs["mean_acc"])
        if pt["p_one_sided"] is not None and pt["p_one_sided"] <= ALPHA:
            fp_perm += 1
        if obs["sign_test"]["p"] <= ALPHA:
            fp_sign += 1
        print(f"  rep {rep+1}/{n_rep}: obs_acc={obs['mean_acc']:.3f} "
              f"null_mean={pt['null_mean']:.3f} perm_p={pt['p_one_sided']:.3f} "
              f"sign_p={obs['sign_test']['p']:.4f}")
    print(f"\n[calibrate] PERMUTATION rule  false positives {fp_perm}/{n_rep} "
          f"= {fp_perm/n_rep:.3f}  (alpha {ALPHA})")
    print(f"[calibrate] SIGN-vs-1/k rule  false positives {fp_sign}/{n_rep} "
          f"= {fp_sign/n_rep:.3f}  (alpha {ALPHA})  <- the rule PR-031d replaces")
    return 0


# ---------------------------------------------------------------- driver
def resolve_runs(root, prefix):
    """Map (codeword, concept) -> run dir, by the tag convention bombspec_<cw>_<concept>."""
    out = {}
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            pat = os.path.join(root, f"{prefix}_{cw}_{cc}_*")
            hits = sorted(glob.glob(pat))
            if hits:
                out[(cw, cc)] = hits[-1]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--calibrate", type=int, default=0)
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--runs-root", default="outputs/boombness/extract_boombness")
    ap.add_argument("--run-prefix", default="bombspec")
    ap.add_argument("--bank-dir", default="data/boombness_prompts")
    ap.add_argument("--channel", default=PRIMARY_CHANNEL)
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_bombness_specificity.json")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.calibrate:
        return calibrate(a.calibrate)

    import hashlib
    runs = resolve_runs(a.runs_root, a.run_prefix)

    # ---- PR-035 §23.3: class-set completeness. A missing bank must NEVER silently become a
    # smaller problem scored against the larger chance level (C4).
    # A-04/C-053 §28.4: the assertion covered the three primary classes only, so `club` -- needed
    # for the §23.5(4) DECISION-CRITICAL knife-vs-club control -- could silently vanish, and a
    # MISSING control then reads as a control that FAILED. Every class this run uses is required.
    need_primary = [(PRIMARY_CODEWORD, c) for c in PRIMARY_CLASSES] + [(PRIMARY_CODEWORD, "club")]
    missing_primary = [k for k in need_primary if k not in runs]
    if missing_primary:
        raise SystemExit(f"VOID: class set incomplete -- no run for {missing_primary}. Refusing to "
                         f"score a reduced class set, and refusing to report a missing "
                         f"knife-vs-club control as a failed one (§23.5 clause 4).")

    pool, provenance, excl_report, retain_report = {}, {}, {}, {}
    provenance_bank_check = {}
    missing_total, rows_total = 0, 0
    for (cw, cc) in sorted(runs):
        bp = os.path.join(a.bank_dir, f"boombness_prompt_bank_{cw}_{cc}.jsonl")
        sha = hashlib.sha256(open(bp, "rb").read()).hexdigest()[:16]
        bank = load_bank(bp)
        if len(bank) != EXPECT_ROWS_PER_BANK:
            raise SystemExit(f"VOID: {cw}_{cc} has {len(bank)} rows, expected {EXPECT_ROWS_PER_BANK}")
        layers, reps = load_reps(runs[(cw, cc)])
        # C-1/C-053 §28.3: THE JOIN IS ON prompt_id, WHICH COLLIDES 8-WAY ACROSS BANKS
        # (2,736 distinct ids over 21,888 rows). The rep caches are keyed the same way and all
        # eight have IDENTICAL key sets, so a mis-pointed run dir would join another bank's hidden
        # states with zero missing rows, no VOID, and a plausible headline. The compound key this
        # file's own docstring demands was constructed and never read. Refuse instead: the run must
        # declare the bank it came from, and that declaration must match this bank byte-for-byte.
        meta_p = os.path.join(runs[(cw, cc)], "metadata.json")
        if not os.path.exists(meta_p):
            raise SystemExit(f"VOID: {cw}_{cc} run has no metadata.json; cannot verify the bank it "
                             f"was extracted from, and prompt_id alone is not a key.")
        rmeta = json.load(open(meta_p))
        if rmeta.get("bank_file_sha16") != sha:
            raise SystemExit(
                f"VOID: {cw}_{cc} run was extracted from bank_file_sha16="
                f"{rmeta.get('bank_file_sha16')} but is being joined to {os.path.basename(bp)} "
                f"(sha16={sha}). Refusing a cross-bank join.")
        if os.path.basename(rmeta.get("bank_path", "")) != os.path.basename(bp):
            raise SystemExit(f"VOID: {cw}_{cc} run bank_path {rmeta.get('bank_path')} != {bp}")
        if int(rmeta.get("bank_n_rows", -1)) != len(bank):
            raise SystemExit(f"VOID: {cw}_{cc} run bank_n_rows {rmeta.get('bank_n_rows')} != {len(bank)}")
        provenance_bank_check[f"{cw}_{cc}"] = dict(bank_file_sha16=sha,
                                                   bank_rows_sha16=rmeta.get("bank_rows_sha16"),
                                                   tokenizer_files_sha16=rmeta.get("tokenizer_files_sha16"),
                                                   verified=True)
        # C-053 §28.1: ONE uniform rule, every cell, no carve-out.
        for cellset, nex, name in ((("C",), PRIMARY_NEXAMPLES, "C"), (("B",), PRIMARY_NEXAMPLES, "B"),
                                   (("A",), PRIMARY_NEXAMPLES, "A"), (("F",), PRIMARY_NEXAMPLES, "F"),
                                   (("C",), (0,), "C_n0")):
            rws, miss, excl, kept = build_rows(bank, layers, reps, channel=a.channel, cells=cellset,
                                               n_examples=nex, bank_sha=sha, codeword=cw, concept=cc,
                                               exclude_concept_word=True)
            retain_report[f"{cw}_{cc}/{name}"] = kept
            pool[(cw, cc, name)] = rws
            missing_total += miss; rows_total += len(rws) + miss
            if excl:
                excl_report[f"{cw}_{cc}/{name}"] = excl
        provenance[f"{cw}_{cc}"] = dict(bank=bp, bank_sha16=sha, run_dir=runs[(cw, cc)], layers=layers)

    frac_missing = missing_total / max(1, rows_total)
    if frac_missing > MAX_OCCURRENCE_FAILURE:
        raise SystemExit("VOID: occurrence-resolution failure exceeds the preregistered 2%")

    layers = provenance[f"{PRIMARY_CODEWORD}_bomb"]["layers"]
    for k, v in provenance.items():                      # M10: no cross-run layer-list mismatch
        if list(v["layers"]) != list(layers):
            raise SystemExit(f"VOID: {k} extracted with layers {v['layers']} != {layers}")

    _T0 = time.time()

    def _tick(tag):
        """PRINT ONLY (DCS-044). Progress so a long run is monitorable. Touches no statistic."""
        print(f"[progress] {tag:<44s} t+{time.time() - _T0:7.1f}s", flush=True)

    _tick("banks + caches loaded")
    lab = lambda r: r["concept"]
    res = dict(preregistration="DCS-PR-035 (supersedes PR-031/031a/031c/031d after C-049)",
               channel=a.channel, primary_codeword=PRIMARY_CODEWORD,
               primary_classes=list(PRIMARY_CLASSES), alpha=ALPHA, n_perm=a.n_perm,
               provenance=provenance, n_examples_primary=list(PRIMARY_NEXAMPLES),
               occurrence_failure_frac=frac_missing,
               excluded_concept_word_rows=excl_report, retained_rows=retain_report,
               bank_join_verified=provenance_bank_check)

    def gather(cw, classes, name):
        return [r for c in classes for r in pool.get((cw, c, name), [])]

    # Cell B is the DECLARED selection population (§23.6) and must exist before the null uses it.
    B = gather(PRIMARY_CODEWORD, PRIMARY_CLASSES, "B")
    B_sel = B
    if not B:
        raise SystemExit("VOID: cell B is empty -- the declared layer/C selection population "
                         "(§23.6) has no rows, so no pick in this run is the declared statistic.")

    # ================= NULL CONTROL FIRST, AND IT BLOCKS (PR-035 §23.2) =================
    n0 = gather(PRIMARY_CODEWORD, PRIMARY_CLASSES, "C_n0")
    if n0:
        # A-03/C-053 §28.2: picks MUST come from cell B. Selecting them on n0's own true
        # labels destroys the exchangeability argument PR-031d §10.3 uses to license
        # freezing them -- and this is the one number that decides VOID.
        obs0 = loo_domain(n0, layers, PRIMARY_CLASSES, lab, selection_rows=B_sel,
                          tag="null_n0")
        p0 = permutation_test(n0, layers, PRIMARY_CLASSES, lab, obs0["picks"], a.n_perm,
                              20260905, obs0["mean_acc"])
        res["null_n_examples_0"] = dict(observed=obs0, permutation=p0)
        print(f"[null n_examples=0] mean_acc={obs0['mean_acc']:.4f} chance={obs0['chance']:.4f} "
              f"above={obs0['n_above_chance']}/{obs0['n_domains']} perm_p={p0['p_one_sided']}")
        if p0["p_one_sided"] is not None and p0["p_one_sided"] <= ALPHA:
            res["verdict"] = ("VOID — the n_examples=0 null control FIRED "
                              f"(perm p={p0['p_one_sided']:.4f}). No primary is reported.")
            json.dump(res, open(a.out, "w"), indent=1, default=str)
            print(f"\n⛔ {res['verdict']}\n[write] {a.out}")
            return 3          # HARD EXIT. C-049: a dead flag is what let a fired null coexist
                              # with a headline; the fix is an exit, not a JSON field.
    else:
        res["null_n_examples_0"] = "NO ROWS — cannot run the blocking null"

    _tick("null control done")
    # ================= primary and its mandated companions =================
    C_rows = gather(PRIMARY_CODEWORD, PRIMARY_CLASSES, "C")
    res["P2_primary"] = loo_domain(C_rows, layers, PRIMARY_CLASSES, lab, selection_rows=B,
                                   tag="P2_primary_button_3way")
    res["P2_primary_permutation"] = permutation_test(C_rows, layers, PRIMARY_CLASSES, lab,
                                                     res["P2_primary"]["picks"], a.n_perm,
                                                     20260905, res["P2_primary"]["mean_acc"])
    _tick("P2 primary done")
    res["length_only_control"] = length_only_control(C_rows, PRIMARY_CLASSES, lab, tag="length_only")

    # P1 -- declared in PR-031a §7.2, never computed before C-049, and MIS-computed until C-050:
    # `train_p1` was built and then never passed, so P1 trained on cell C. It now trains on B+A.
    A_rows = gather(PRIMARY_CODEWORD, PRIMARY_CLASSES, "A")
    for r in A_rows:
        r["p1_label"] = "literal"
    train_p1 = B + A_rows
    p1lab = lambda r: r.get("p1_label", r["concept"])
    p1_classes = PRIMARY_CLASSES + ("literal",)
    res["P1_trainB_testC"] = loo_domain(C_rows, layers, p1_classes, p1lab, train_rows=train_p1,
                                        selection_rows=B, tag="P1_B_to_C")
    res["P1_trainB_testC_permutation"] = permutation_test(
        C_rows, layers, p1_classes, p1lab, res["P1_trainB_testC"]["picks"], a.n_perm, 20260905,
        res["P1_trainB_testC"]["mean_acc"], train_rows=train_p1)
    res["P1_train_population"] = dict(n_B=len(B), n_A=len(A_rows),
                                      n_train_classes=len({p1lab(r) for r in train_p1}))
    # A-06/C-053 §28.7: PR-031 §6.6's capability gate -- P1 may not be read at all unless the probe
    # can do the task on the cell it was TRAINED on. `P1_CAPABILITY_GATE` had become dead code.
    p1_cap = loo_domain(B, layers, PRIMARY_CLASSES, lab, selection_rows=B_sel, tag="P1_capability_B")
    res["P1_capability_heldout_B"] = p1_cap
    res["P1_capability_gate"] = dict(
        threshold=P1_CAPABILITY_GATE, observed=p1_cap.get("mean_acc"),
        passes=bool(p1_cap.get("mean_acc") is not None
                    and p1_cap["mean_acc"] >= P1_CAPABILITY_GATE))
    if not res["P1_capability_gate"]["passes"]:
        res["P1_trainB_testC_STATUS"] = (
            "UNINFORMATIVE — held-out cell-B accuracy is below the PR-031 §6.6 gate of "
            f"{P1_CAPABILITY_GATE}, so the probe cannot do the task on the cell it trained on. "
            "P1 is reported but may not be read either way.")

    _tick("P1 done")
    # R-078 §21.2 mandated contrasts
    for name, pair in (("P2_bomb_vs_knife_2way_gun_excluded", ("bomb", "knife")),
                       ("P2_knife_vs_club_CONTROL_bomb_absent", ("knife", "club"))):
        rp, sp = gather(PRIMARY_CODEWORD, pair, "C"), gather(PRIMARY_CODEWORD, pair, "B")
        if rp and sp:
            res[name] = loo_domain(rp, layers, pair, lab, selection_rows=sp, tag=name)
            res[name + "_permutation"] = permutation_test(rp, layers, pair, lab, res[name]["picks"],
                                                          a.n_perm, 20260905, res[name]["mean_acc"])

    _tick("R-078 contrasts done")
    # cell F: bomb vs GENERIC REMAPPING (A-020 §8.5) -- the only non-weapon comparator
    F = pool.get((PRIMARY_CODEWORD, "bomb", "F"), [])
    for r in F:
        r["f_label"] = "benign_remap"
        r["perm_group"] = "benign_remap"
    if F:
        C_bomb = [r for r in C_rows if r["concept"] == "bomb"]
        for r in C_bomb:
            r["perm_group"] = "bomb"
        rows_f = C_bomb + F
        flab = lambda r: r.get("f_label", "bomb")
        res["P2_bomb_vs_benign_remap"] = loo_domain(rows_f, layers, ("bomb", "benign_remap"), flab,
                                                    tag="bomb_vs_benign_remap", balanced=True)
        # C-050 §25.4: this contrast had NO permutation test, so §23.4(2)'s instrument produced a
        # number with no inference attached. Its groups are CELLS, not concepts -- hence perm_group.
        res["P2_bomb_vs_benign_remap_permutation"] = permutation_test(
            rows_f, layers, ("bomb", "benign_remap"), flab,
            res["P2_bomb_vs_benign_remap"]["picks"], a.n_perm, 20260905,
            res["P2_bomb_vs_benign_remap"]["mean_acc"], balanced=True)
        # C-053 §28.5: cells C and F sit in DISJOINT template blocks (C never uses
        # extra_conditions; F is only extra_conditions), so this contrast is perfectly confounded
        # with presentation. The confound can only HELP separability, which fixes the
        # interpretation asymmetrically and BEFORE the numbers: a NEGATIVE here is informative,
        # a POSITIVE is NOT attributable to concept. It is not in §23.5's verdict rule either way.
        res["P2_bomb_vs_benign_remap_BLOCK_CONFOUND"] = dict(
            C_blocks=sorted({r["block"] for r in C_bomb}), F_blocks=sorted({r["block"] for r in F}),
            disjoint=bool(not ({r["block"] for r in C_bomb} & {r["block"] for r in F})),
            interpretation="NEGATIVE informative; POSITIVE not attributable to concept")
        res["P2_bomb_vs_benign_remap_n"] = dict(n_C_bomb=len(C_bomb), n_F=len(F))

    _tick("cell F done")
    # held-out TEMPLATE FAMILY (PR-031c §9.2)
    if len({r["block"] for r in C_rows}) > 1:
        res["P2_leave_one_block_out"] = loo_domain(C_rows, layers, PRIMARY_CLASSES, lab,
                                                   tag="P2_LOBO", group="block")
        # A-08/C-053 §28.6: without this the one instrument PR-031c §9.2 added was judged by the
        # sign-vs-1/k rule that PR-031d §10.2 MEASURED at an 8.3% false-positive rate.
        res["P2_leave_one_block_out_permutation"] = permutation_test(
            C_rows, layers, PRIMARY_CLASSES, lab, res["P2_leave_one_block_out"]["picks"],
            a.n_perm, 20260905, res["P2_leave_one_block_out"]["mean_acc"], group="block")

    _tick("leave-one-block-out done")
    # lexical transfer, only if that class set is complete
    if all((("basket"), c) in runs for c in PRIMARY_CLASSES):
        Cb = gather("basket", PRIMARY_CLASSES, "C")
        if Cb:
            res["P2_basket_lexical_transfer"] = loo_domain(Cb, layers, PRIMARY_CLASSES, lab,
                                                           selection_rows=B, tag="P2_basket")
    else:
        res["P2_basket_lexical_transfer"] = "SKIPPED — basket class set incomplete (would be VOID)"

    _tick("basket transfer done")
    # ================= VERDICT (PR-035 §23.5) =================
    pp = res["P2_primary_permutation"]["p_one_sided"]
    ctrl = res.get("P2_knife_vs_club_CONTROL_bomb_absent_permutation", {}).get("p_one_sided")
    above = res["P2_primary"]["mean_acc"] > res["P2_primary_permutation"]["null_mean"]
    lenc = res["length_only_control"]["mean_acc"]
    # §23.5 clause 5, operationalised in code BEFORE the data is read (C-050 §25.5). "The
    # length-only control does not match the probe" == prompt length alone must NOT reach the
    # probe's own significance band. The threshold is the probe's permutation null q95, a number
    # the analyzer already produces; no new constant is introduced.
    null_q95 = res["P2_primary_permutation"].get("null_q95")
    length_ok = (lenc is None or null_q95 is None or lenc <= null_q95)
    res["length_only_clause"] = dict(length_acc=lenc, probe_null_q95=null_q95, passes=bool(length_ok))

    if not res["P2_primary"]["fit_capable"]:
        res["verdict"] = "VOID — P2's fit does not beat chance on its own training fold"
    elif not length_ok:
        res["verdict"] = (f"VOID — the length-only control reaches the probe's significance band "
                          f"(length acc {lenc:.4f} > null q95 {null_q95:.4f}); prompt length alone "
                          f"could produce this separation (PR-035 §23.5 clause 5)")
    elif pp is None:
        res["verdict"] = ("CANNOT ANSWER — the primary permutation produced no p (no usable "
                          "replicate). This is NOT a null.")
    elif ctrl is None and pp <= ALPHA and above:
        # A-04: a control that was never computed is not a control that failed.
        res["verdict"] = ("CANNOT ANSWER — the 3-way clears but the §23.5(4) knife-vs-club control "
                          "WAS NOT COMPUTED, so remapping strength cannot be excluded. A missing "
                          "control is not a failed control, and this is NOT a null.")
    elif pp <= ALPHA and above and ctrl <= ALPHA:
        res["verdict"] = ("POSITIVE — concept-specific: 3-way clears and the bomb-absent "
                          "knife-vs-club control clears too, so it is not remapping strength")
    elif pp <= ALPHA and above:
        res["verdict"] = ("NOT ATTRIBUTABLE — the 3-way clears but the bomb-absent control does "
                          "NOT, so the separation is attributed to REMAPPING STRENGTH (R-078 §21.2) "
                          "and may NOT be called Bombness")
    else:
        res["verdict"] = "NEGATIVE — the codeword state does not carry which concept was installed"
    res["verdict_inputs"] = dict(P2_perm_p=pp, knife_club_ctrl_p=ctrl, above_null=bool(above),
                                 length_clause_passes=bool(length_ok),
                                 fit_capable=bool(res["P2_primary"]["fit_capable"]),
                                 null_control_passed=True)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print(f"[write] {a.out}\n")
    print(f"excluded concept-word rows: {excl_report}\n")
    for k in ("P2_primary", "P1_trainB_testC", "P2_bomb_vs_knife_2way_gun_excluded",
              "P2_knife_vs_club_CONTROL_bomb_absent", "P2_bomb_vs_benign_remap",
              "P2_leave_one_block_out", "P2_basket_lexical_transfer"):
        v = res.get(k)
        if isinstance(v, dict) and v.get("mean_acc") is not None:
            pk = res.get(k + "_permutation", {})
            print(f"  {k:<40} acc={v['mean_acc']:.4f} chance={v['chance']:.3f} "
                  f"above={v['n_above_chance']}/{v['n_domains']} "
                  f"perm_p={pk.get('p_one_sided')} trainfold={v.get('mean_train_fold_acc')}")
    print(f"  {'length_only_control':<40} acc={lenc}")
    print(f"\nVERDICT: {res['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
