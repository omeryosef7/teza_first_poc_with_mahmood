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

import argparse, collections, glob, json, os, sys
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
    """Load the extractor's final-occurrence cache: {prompt_id: Tensor[len(layers), H]}."""
    import torch
    p = os.path.join(run_dir, "cache", "final_occurrence_reps.pt")
    if not os.path.exists(p):
        raise SystemExit(f"missing rep cache: {p}")
    blob = torch.load(p, map_location="cpu")
    layers = list(blob["layers"])
    reps = {k: v.float().numpy() for k, v in blob["reps"].items()}
    return layers, reps


def build_rows(bank_rows, layers, reps, *, channel, cells, n_examples, bank_sha, codeword, concept):
    """One record per usable row. Key is (bank_sha, prompt_id) — prompt_id ALONE IS NOT A KEY:
    it is identical across all eight banks (A-019 §2.2)."""
    out, missing = [], 0
    for r in bank_rows:
        if r.get("query_kind") != channel or r.get("cell") not in cells:
            continue
        if n_examples is not None and r.get("n_examples") not in n_examples:
            continue
        pid = r["prompt_id"]
        if pid not in reps:
            missing += 1
            continue
        out.append(dict(key=(bank_sha, pid), pid=pid, cell=r["cell"], domain=r["domain"],
                        block=r.get("bank_block"), split=r.get("split"),
                        n_examples=r["n_examples"], family=r.get("family_id"),
                        codeword=codeword, concept=concept, n_chars=len(r["full_prompt"]),
                        vec=reps[pid], layers=layers))
    return out, missing


def X_at(rows, layer, layers):
    j = layers.index(layer)
    return np.stack([r["vec"][j] for r in rows])


# ---------------------------------------------------------------- core classifier
def fit_predict(train, test, layer, layers, C, classes, label_of):
    """L2 multinomial logistic regression. Standardised with TRAINING-FOLD statistics only."""
    from sklearn.linear_model import LogisticRegression
    ytr = np.array([classes.index(label_of(r)) for r in train])
    yte = np.array([classes.index(label_of(r)) for r in test])
    if len(set(ytr.tolist())) < 2:
        return None
    Xtr, Xte = X_at(train, layer, layers), X_at(test, layer, layers)
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd < 1e-8] = 1.0
    Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd
    clf = LogisticRegression(C=C, max_iter=3000)  # sklearn>=1.5: multinomial is the default for lbfgs
    clf.fit(Xtr, ytr)
    pred = clf.predict(Xte)
    proba = clf.predict_proba(Xte)
    return dict(acc=float((pred == yte).mean()), n=len(yte), pred=pred.tolist(),
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


def loo_domain(rows, layers, classes, label_of, *, selection_rows=None, tag=""):
    """Outer leave-one-domain-out. Returns per-domain held-out accuracy + the chosen (layer, C)."""
    doms = sorted({r["domain"] for r in rows})
    per_domain, picks = {}, {}
    for d in doms:
        tr = [r for r in rows if r["domain"] != d]
        te = [r for r in rows if r["domain"] == d]
        if not tr or not te:
            continue
        if selection_rows is not None:
            sel = [r for r in selection_rows if r["domain"] != d]
            pick, _ = select_layer_C(sel, layers, classes, label_of)
        else:
            pick, _ = select_layer_C(tr, layers, classes, label_of)
        if pick is None:
            continue
        L, C = pick
        res = fit_predict(tr, te, L, layers, C, classes, label_of)
        if res:
            per_domain[d] = res["acc"]
            picks[d] = dict(layer=L, C=C, n_test=res["n"], n_train=len(tr))
    ch = chance(len(classes))
    deltas = [per_domain[d] - ch for d in sorted(per_domain)]
    st = cluster_sign_test(deltas, alpha=ALPHA)
    return dict(tag=tag, classes=list(classes), chance=ch, per_domain=per_domain, picks=picks,
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
                q["perm_label"] = mapping[r["concept"]]
                out.append(q)
    return out


def loo_with_picks(rows, layers, classes, label_of, picks):
    """Outer LOO-domain using a FIXED (layer, C) per fold -- no selection inside."""
    per_domain = {}
    for d in sorted({r["domain"] for r in rows}):
        if d not in picks:
            continue
        tr = [r for r in rows if r["domain"] != d]
        te = [r for r in rows if r["domain"] == d]
        if not tr or not te:
            continue
        res = fit_predict(tr, te, picks[d]["layer"], layers, picks[d]["C"], classes, label_of)
        if res:
            per_domain[d] = res["acc"]
    return per_domain


def permutation_test(rows, layers, classes, label_of, picks, n_perm, seed, observed_mean):
    """One-sided permutation p on the mean held-out accuracy, in the PREDICTED direction.

    The (layer, C) picks are held fixed and are legitimate to reuse: PR-031 selects them on cell B,
    which the permutation does not touch, so the selection is invariant under the null being tested.
    """
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(n_perm):
        perm_rows = group_permute(rows, rng, list(classes))
        pd = loo_with_picks(perm_rows, layers, classes, lambda r: r["perm_label"], picks)
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
    ap.add_argument("--calibrate", type=int, default=0,
                    help="run N synthetic null replicates and report the decision rule's false-positive rate")
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
    need = [(cw, cc) for cw in CODEWORDS for cc in CONCEPTS]
    have = [k for k in need if k in runs]
    print(f"[load] {len(have)}/{len(need)} run dirs found")

    pool, provenance, missing_total, rows_total = {}, {}, 0, 0
    for (cw, cc) in have:
        bp = os.path.join(a.bank_dir, f"boombness_prompt_bank_{cw}_{cc}.jsonl")
        sha = hashlib.sha256(open(bp, "rb").read()).hexdigest()[:16]
        bank = load_bank(bp)
        if len(bank) != EXPECT_ROWS_PER_BANK:
            raise SystemExit(f"VOID: {cw}_{cc} has {len(bank)} rows, expected {EXPECT_ROWS_PER_BANK}")
        layers, reps = load_reps(runs[(cw, cc)])
        for cellset, nex, name in ((("C",), PRIMARY_NEXAMPLES, "C"),
                                   (("B",), PRIMARY_NEXAMPLES, "B"),
                                   (("A",), PRIMARY_NEXAMPLES, "A"),
                                   (("C",), (0,), "C_n0")):
            rws, miss = build_rows(bank, layers, reps, channel=a.channel, cells=cellset,
                                   n_examples=nex, bank_sha=sha, codeword=cw, concept=cc)
            pool[(cw, cc, name)] = rws
            missing_total += miss
            rows_total += len(rws) + miss
        provenance[f"{cw}_{cc}"] = dict(bank=bp, bank_sha16=sha, run_dir=runs[(cw, cc)],
                                        layers=layers)

    frac_missing = missing_total / max(1, rows_total)
    print(f"[load] occurrence/rep resolution failures: {missing_total}/{rows_total} "
          f"= {frac_missing:.4f} (VOID threshold {MAX_OCCURRENCE_FAILURE})")
    if frac_missing > MAX_OCCURRENCE_FAILURE:
        raise SystemExit("VOID: occurrence-resolution failure exceeds the preregistered 2%")

    layers = provenance[f"{PRIMARY_CODEWORD}_bomb"]["layers"]
    lab = lambda r: r["concept"]
    res = dict(preregistration="DCS-PR-031/031a/031c", channel=a.channel,
               primary_codeword=PRIMARY_CODEWORD, primary_classes=list(PRIMARY_CLASSES),
               alpha=ALPHA, provenance=provenance,
               n_examples_primary=list(PRIMARY_NEXAMPLES),
               occurrence_failure_frac=frac_missing)

    def gather(cw, classes, name):
        return [r for c in classes for r in pool.get((cw, c, name), [])]

    # ---- NULL CONTROL FIRST (PR-031a §7.5): at n_examples=0 the C rows are byte-identical
    n0 = gather(PRIMARY_CODEWORD, PRIMARY_CLASSES, "C_n0")
    if n0:
        res["null_n_examples_0"] = loo_domain(n0, layers, PRIMARY_CLASSES, lab, tag="null_n0")
        ch = chance(len(PRIMARY_CLASSES))
        res["null_n_examples_0"]["VOIDS_RUN"] = bool(
            res["null_n_examples_0"]["mean_acc"] is not None
            and res["null_n_examples_0"]["mean_acc"] > ch + 0.15)

    # ---- P1 capability gate (PR-031 §6.6): held-out cell-B accuracy
    B = gather(PRIMARY_CODEWORD, PRIMARY_CLASSES, "B")
    res["p1_capability_gate"] = loo_domain(B, layers, PRIMARY_CLASSES, lab, tag="cellB_capability")
    res["p1_capability_gate"]["threshold"] = P1_CAPABILITY_GATE
    res["p1_capability_gate"]["passed"] = bool(
        res["p1_capability_gate"]["mean_acc"] is not None
        and res["p1_capability_gate"]["mean_acc"] >= P1_CAPABILITY_GATE)

    # ---- P2 PRIMARY: train C(train domains) -> test C(held-out domain); layer picked on cell B
    C_rows = gather(PRIMARY_CODEWORD, PRIMARY_CLASSES, "C")
    res["P2_primary"] = loo_domain(C_rows, layers, PRIMARY_CLASSES, lab,
                                   selection_rows=B, tag="P2_primary_button_3way")
    # PR-031d: the PRIMARY inference is the group-permutation null, not the theoretical 1/3.
    res["P2_primary_permutation"] = permutation_test(
        C_rows, layers, PRIMARY_CLASSES, lab, res["P2_primary"]["picks"],
        a.n_perm, 20260905, res["P2_primary"]["mean_acc"])
    res["P2_secondary_selfselected"] = loo_domain(C_rows, layers, PRIMARY_CLASSES, lab,
                                                  tag="P2_layer_selected_within_C")
    res["length_only_control"] = length_only_control(C_rows, PRIMARY_CLASSES, lab,
                                                     tag="length_only_button_3way")

    # ---- secondaries: club included (4-way), lexical transfer to basket
    four = PRIMARY_CLASSES + ("club",)
    C4 = gather(PRIMARY_CODEWORD, four, "C")
    if C4:
        res["P2_with_club_4way"] = loo_domain(C4, layers, four, lab, tag="P2_with_club")
    Cb = gather("basket", PRIMARY_CLASSES, "C")
    if Cb:
        res["P2_basket_lexical_transfer"] = loo_domain(Cb, layers, PRIMARY_CLASSES, lab,
                                                       selection_rows=B, tag="P2_basket")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=str)
    print(f"[write] {a.out}")
    for k in ("null_n_examples_0", "p1_capability_gate", "P2_primary",
              "P2_with_club_4way", "P2_basket_lexical_transfer"):
        if k in res and res[k].get("mean_acc") is not None:
            print(f"  {k:<32} mean_acc={res[k]['mean_acc']:.3f} chance={res[k]['chance']:.3f} "
                  f"above={res[k]['n_above_chance']}/{res[k]['n_domains']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
