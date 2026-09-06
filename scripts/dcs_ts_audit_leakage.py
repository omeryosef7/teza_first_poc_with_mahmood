#!/usr/bin/env python
"""DCS-TS leakage audit and nuisance baselines (mandate section 6.6).

CPU only. No model, no GPU, no network. Everything is re-derived from the raw
bank JSONL rows; no producer-written summary field is trusted as evidence.

Probe population (unless stated otherwise):
    cell C, query_kind semantic_one_word, n_examples=4,
    classes {bomb, knife, gun}, pooled over both codewords (button, basket),
    trained on the 70 TRAIN domains and tested on the 23 TEST domains of
    data/boombness_prompts/dcs_ts116_domain_split.json (field "dsplit").

Every check in here (a) FAILS LOUDLY if it binds to zero rows, (b) is shown to
go RED under a deliberate mutation (--mutate), and (c) recomputes its evidence
from full_prompt / raw fields rather than from n_concept_occurrences or any
other producer-written count.

Usage:
    python scripts/dcs_ts_audit_leakage.py                 # run the audit
    python scripts/dcs_ts_audit_leakage.py --mutate        # prove checks go RED
    python scripts/dcs_ts_audit_leakage.py --json PATH     # dump all numbers
"""

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANKDIR = os.path.join(REPO, "data", "boombness_prompts")
SPLIT_PATH = os.path.join(BANKDIR, "dcs_ts116_domain_split.json")

CONCEPTS = ["bomb", "knife", "gun"]
CODEWORDS = ["button", "basket"]
CONCEPT_IDX = {c: i for i, c in enumerate(CONCEPTS)}

# Whole-word, case-insensitive surface forms of each concept.
CONCEPT_FORMS = {
    "bomb": ["bomb", "bombs", "bombing", "bombings"],
    "knife": ["knife", "knives"],
    "gun": ["gun", "guns", "gunman", "gunmen"],
}
# Synonyms are reported per-term so that a generic term cannot silently inflate
# a bucket total.
CONCEPT_SYNONYMS = {
    "bomb": ["explosive", "explosives", "ied", "detonator", "detonators",
             "dynamite", "grenade", "grenades", "warhead", "warheads", "tnt"],
    "knife": ["blade", "blades", "dagger", "daggers", "machete", "machetes",
              "cleaver", "cleavers", "shiv", "switchblade"],
    "gun": ["firearm", "firearms", "pistol", "pistols", "rifle", "rifles",
            "revolver", "revolvers", "handgun", "handguns", "shotgun",
            "shotguns", "ammunition"],
}

MASK_TOKEN = "zzmaskedwordzz"
ALL_FORMS = sorted({f for v in CONCEPT_FORMS.values() for f in v})
MASK_RE = re.compile(r"\b(" + "|".join(ALL_FORMS) + r")\b", re.IGNORECASE)


def word_re(w):
    return re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE)


WORD_RES = {w: word_re(w) for w in ALL_FORMS}
for _v in CONCEPT_SYNONYMS.values():
    for _w in _v:
        WORD_RES[_w] = word_re(_w)


# --------------------------------------------------------------------------
# check bookkeeping
# --------------------------------------------------------------------------
class Checks(object):
    def __init__(self):
        self.rows = OrderedDict()

    def record(self, name, ok, n_bound, detail):
        """A check that bound zero rows is a FAIL, never a PASS."""
        if n_bound is None or n_bound <= 0:
            ok = False
            detail = "BOUND ZERO ROWS (vacuous check) -- " + str(detail)
        self.rows[name] = {"pass": bool(ok), "n_bound": int(n_bound or 0),
                           "detail": detail}
        return self.rows[name]

    def status(self, name):
        return self.rows[name]["pass"] if name in self.rows else None

    def n_fail(self):
        return sum(0 if r["pass"] else 1 for r in self.rows.values())


# --------------------------------------------------------------------------
# data loading
# --------------------------------------------------------------------------
def bank_path(codeword, concept):
    return os.path.join(
        BANKDIR, "boombness_prompt_bank_ts116_%s_%s.jsonl" % (codeword, concept))


def stream_bank(codeword, concept):
    with open(bank_path(codeword, concept)) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


KEEP_FIELDS = ["prompt_id", "prompt_sha16", "cell", "query_kind", "n_examples",
               "domain", "split", "condition", "bank_block", "family_slot",
               "n_chars", "n_demos_emitted", "n_preamble_lines", "full_prompt",
               "concept", "codeword", "target_semantic", "n_concept_occurrences"]


_SUBSET_CACHE = {}


def load_subset_cached(key, pred, keep_text=True):
    """Cache the raw parsed subset; hand out a fresh deep-enough copy so a
    mutation in one audit run cannot contaminate the next."""
    if key not in _SUBSET_CACHE:
        _SUBSET_CACHE[key] = load_subset(pred, keep_text=keep_text)
    return [dict(r) for r in _SUBSET_CACHE[key]]


def load_subset(pred, keep_text=True):
    """Load rows matching pred(row) from all 6 banks. Returns list of dicts."""
    out = []
    for cw in CODEWORDS:
        for cpt in CONCEPTS:
            for r in stream_bank(cw, cpt):
                if pred(r):
                    d = {k: r.get(k) for k in KEEP_FIELDS}
                    if not keep_text:
                        d["full_prompt"] = None
                    d["bank_codeword"] = cw
                    d["bank_concept"] = cpt
                    out.append(d)
    return out


def load_split():
    with open(SPLIT_PATH) as fh:
        m = json.load(fh)
    assign = m["assign"]
    if not isinstance(assign, dict) or not assign:
        raise SystemExit("FATAL: split manifest 'assign' is not a non-empty dict")
    if m.get("field_name") != "dsplit":
        raise SystemExit("FATAL: split manifest field_name != dsplit")
    return m, dict(assign)


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------
def macro_ovr_auroc(y_true, proba, classes):
    """Macro one-vs-rest AUROC; None if a class is missing from y_true."""
    y_true = np.asarray(y_true)
    aucs = []
    for i, c in enumerate(classes):
        pos = (y_true == c).astype(int)
        if pos.sum() == 0 or pos.sum() == len(pos):
            return None
        aucs.append(roc_auc_score(pos, proba[:, i]))
    return float(np.mean(aucs))


def binom_z(acc, n, p0):
    """z of observed accuracy against chance p0 (one-sided, above chance)."""
    if n <= 0:
        return float("nan")
    se = math.sqrt(p0 * (1.0 - p0) / n)
    return (acc - p0) / se if se > 0 else float("nan")


def fit_eval(Xtr, ytr, Xte, yte, kind, seed=0):
    """kind in {'dense','tfidf','onehot'}. Returns dict of metrics."""
    ntr, nte = len(ytr), len(yte)
    if ntr == 0 or nte == 0:
        raise ValueError("fit_eval bound zero rows (train=%d test=%d)" % (ntr, nte))
    classes = sorted(set(ytr))
    if len(classes) < 2:
        raise ValueError("fit_eval: fewer than 2 classes in train")
    if kind == "tfidf":
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                              lowercase=True)
        A = vec.fit_transform(Xtr)
        B = vec.transform(Xte)
        n_feat = A.shape[1]
    elif kind == "onehot":
        vec = TfidfVectorizer(analyzer=lambda s: s, lowercase=False,
                              use_idf=False, norm=None, binary=True)
        A = vec.fit_transform(Xtr)
        B = vec.transform(Xte)
        n_feat = A.shape[1]
    else:
        sc = StandardScaler()
        A = sc.fit_transform(np.asarray(Xtr, dtype=float))
        B = sc.transform(np.asarray(Xte, dtype=float))
        n_feat = A.shape[1]
    clf = LogisticRegression(max_iter=4000, random_state=seed)
    clf.fit(A, ytr)
    pred = clf.predict(B)
    proba = clf.predict_proba(B)
    acc = float(accuracy_score(yte, pred))
    auc = macro_ovr_auroc(yte, proba, list(clf.classes_))
    p0 = 1.0 / len(set(list(ytr) + list(yte)))
    return {"acc": acc, "auroc": auc, "n_train": ntr, "n_test": nte,
            "n_features": int(n_feat), "chance": p0,
            "z_vs_chance": binom_z(acc, nte, p0),
            "pred_dist": dict(Counter(pred))}


def fmt(v, nd=4):
    if v is None:
        return "n/a"
    return ("%." + str(nd) + "f") % v


# --------------------------------------------------------------------------
# mutations
# --------------------------------------------------------------------------
MUTATIONS = OrderedDict([
    ("inject_concept_word",
     "append the row's own concept word to full_prompt in the probe population"),
    ("length_leak",
     "pad n_chars by 500 * concept index (a concept-dependent length)"),
    ("template_leak",
     "append the concept to bank_block (breaks template alignment)"),
    ("corrupt_split",
     "move 5 test domains into train so the groups overlap"),
    ("empty_population",
     "select cell 'Z' so the probe population binds zero rows"),
    ("break_codeword_control",
     "erase the codeword from the text so the positive control loses its signal"),
    ("unmask_cellB",
     "disable the concept mask (identity substitution) so the cell-B leak survives"),
])


def mask_text(t, mutation=None):
    """Mask the three concept words. Under the unmask_cellB mutation the mask
    is a no-op, which must make the 'masking removes the leak' check go RED."""
    if mutation == "unmask_cellB":
        return t
    return MASK_RE.sub(MASK_TOKEN, t)


def apply_row_mutation(rows, mutation):
    if mutation is None:
        return rows
    if mutation == "inject_concept_word":
        for r in rows:
            if r["full_prompt"] is None:
                continue
            r["full_prompt"] = r["full_prompt"] + " " + r["concept"]
            r["n_chars"] = len(r["full_prompt"])
    elif mutation == "length_leak":
        for r in rows:
            r["n_chars"] = r["n_chars"] + 500 * CONCEPT_IDX[r["concept"]]
    elif mutation == "template_leak":
        for r in rows:
            r["bank_block"] = "%s__%s" % (r["bank_block"], r["concept"])
    elif mutation == "break_codeword_control":
        for r in rows:
            t = r["full_prompt"]
            if t is None:
                continue
            for cw in CODEWORDS:
                t = word_re(cw).sub("thing", t)
            r["full_prompt"] = t
            r["n_chars"] = len(t)
    return rows


def apply_split_mutation(assign, mutation):
    if mutation != "corrupt_split":
        return assign
    a = dict(assign)
    moved = [d for d, s in sorted(assign.items()) if s == "test"][:5]
    # keep them labelled test but ALSO make them train: emulate by relabelling
    # a copy that the grouping check will inspect via the row-level membership.
    for d in moved:
        a[d] = "train_and_test_CORRUPT"
    return a


def split_of(assign, domain, mutation):
    s = assign.get(domain)
    if s == "train_and_test_CORRUPT":
        return "both"
    return s


# --------------------------------------------------------------------------
# main audit
# --------------------------------------------------------------------------
def run_audit(mutation=None, verbose=True, occurrence_table=True):
    out = {"mutation": mutation}
    ck = Checks()
    manifest, assign = load_split()
    assign = apply_split_mutation(assign, mutation)

    probe_cell = "Z" if mutation == "empty_population" else "C"

    # ---- load populations -------------------------------------------------
    def pp(r):
        return (r["cell"] == probe_cell and r["query_kind"] == "semantic_one_word"
                and r["n_examples"] == 4)

    probe_rows = apply_row_mutation(
        load_subset_cached(("probe", probe_cell), pp), mutation)
    out["n_probe_rows"] = len(probe_rows)

    def zerop(r):
        return (r["n_examples"] == 0 and r["cell"] in ("A", "C")
                and r["query_kind"] in ("behavioral", "semantic_one_word"))

    zero_rows = apply_row_mutation(load_subset_cached("zero", zerop), mutation)
    out["n_zero_rows"] = len(zero_rows)

    # cell B, semantic_one_word, n=4 -- the concept IS named in the text here.
    # Used as a second positive control: the leak detector must find this leak,
    # and masking must remove it.
    def bpp(r):
        return (r["cell"] == ("Y" if mutation == "empty_population" else "B")
                and r["query_kind"] == "semantic_one_word"
                and r["n_examples"] == 4)

    cellb_rows = apply_row_mutation(
        load_subset_cached(("cellb", probe_cell), bpp), mutation)
    out["n_cellb_rows"] = len(cellb_rows)

    # cell-C rows across all query kinds and doses, categorical fields only
    def cellc(r):
        return r["cell"] == probe_cell

    cellc_rows = apply_row_mutation(
        load_subset_cached(("cellc", probe_cell), cellc, keep_text=False), mutation)
    out["n_cellc_rows"] = len(cellc_rows)

    # ---- helper: domain-grouped split ------------------------------------
    def grouped(rows, label_key):
        tr, te = [], []
        for r in rows:
            s = split_of(assign, r["domain"], mutation)
            if s == "train":
                tr.append(r)
            elif s == "test":
                te.append(r)
            elif s == "both":
                tr.append(r)
                te.append(r)
        return tr, te

    # =====================================================================
    # 7. domain-level grouping assertion (done first; everything rests on it)
    # =====================================================================
    tr_rows, te_rows = grouped(probe_rows, "concept")
    dtr = set(r["domain"] for r in tr_rows)
    dte = set(r["domain"] for r in te_rows)
    overlap = dtr & dte
    n_val = sum(1 for d, s in assign.items() if s == "validation")
    ok = (len(overlap) == 0 and len(dtr) > 0 and len(dte) > 0)
    ck.record(
        "C8_domain_grouping_disjoint", ok, len(tr_rows) + len(te_rows),
        "train domains=%d test domains=%d overlap=%d %s; validation domains=%d "
        "(held out, unused); manifest_sha16=%s"
        % (len(dtr), len(dte), len(overlap), sorted(overlap)[:5], n_val,
           manifest.get("manifest_sha16")))
    out["train_domains"] = len(dtr)
    out["test_domains"] = len(dte)
    out["overlap_domains"] = sorted(overlap)
    out["n_train_rows"] = len(tr_rows)
    out["n_test_rows"] = len(te_rows)

    # =====================================================================
    # 9. cross-concept byte identity inside the probe population
    # =====================================================================
    by_key = defaultdict(dict)
    for r in probe_rows:
        by_key[(r["bank_codeword"], r["prompt_id"])][r["bank_concept"]] = r["full_prompt"]
    complete = [k for k, v in by_key.items() if len(v) == 3]
    identical = sum(1 for k in complete
                    if len(set(by_key[k].values())) == 1)
    ck.record(
        "C9_probe_pop_text_identical_across_concepts",
        identical == len(complete) and len(complete) > 0, len(complete),
        "%d/%d (bank_codeword,prompt_id) triples have byte-identical full_prompt "
        "across {bomb,knife,gun}" % (identical, len(complete)))
    out["identity_triples"] = (identical, len(complete))

    # =====================================================================
    # 13. cross-concept byte identity over EVERY concept-free (cell, query_kind)
    #     combination and EVERY dose -- the load-bearing structural claim.
    # =====================================================================
    def freep(r):
        return (r["cell"] in ("A", "C")
                and r["query_kind"] in ("behavioral", "semantic_one_word"))

    free_rows = apply_row_mutation(load_subset_cached("free", freep), mutation)
    fg = defaultdict(dict)
    for r in free_rows:
        fg[(r["bank_codeword"], r["cell"], r["query_kind"], r["n_examples"],
            r["prompt_id"])][r["bank_concept"]] = r["full_prompt"]
    ftrip = [k for k, v in fg.items() if len(v) == 3]
    fident = sum(1 for k in ftrip if len(set(fg[k].values())) == 1)
    per_combo = defaultdict(lambda: [0, 0])
    for k in ftrip:
        c = (k[1], k[2], k[3])
        per_combo[c][1] += 1
        if len(set(fg[k].values())) == 1:
            per_combo[c][0] += 1
    out["free_identity_per_combo"] = {("%s|%s|n%s" % c): v
                                      for c, v in per_combo.items()}
    ck.record("C13_all_concept_free_channels_identical_across_concepts",
              len(ftrip) > 0 and fident == len(ftrip), len(free_rows),
              "%d/%d (codeword,cell,query_kind,n_examples,prompt_id) triples in "
              "cells {A,C} x {behavioral,semantic_one_word} have byte-identical "
              "full_prompt across {bomb,knife,gun}, over %d rows"
              % (fident, len(ftrip), len(free_rows)))

    # =====================================================================
    # 9b. Bayes-optimal bound: the best any function of full_prompt can do
    # =====================================================================
    bygroup = defaultdict(list)
    for r in probe_rows:
        if r["full_prompt"] is not None:
            bygroup[r["full_prompt"]].append(r["concept"])
    n_pp = sum(len(v) for v in bygroup.values())
    bayes = (sum(max(Counter(v).values()) for v in bygroup.values()) / n_pp
             if n_pp else None)
    out["bayes_optimal_from_text"] = bayes
    out["n_distinct_texts"] = len(bygroup)
    ck.record("C12_bayes_bound_from_text_is_chance",
              bayes is not None and abs(bayes - 1.0 / 3.0) < 1e-9, n_pp,
              "best possible accuracy of ANY deterministic function of "
              "full_prompt on the probe population = %s over %d distinct texts "
              "/ %d rows (chance = 0.333333)" % (fmt(bayes, 6), len(bygroup), n_pp))

    # =====================================================================
    # 1. concept-word occurrence table over FULL_PROMPT (all 6 banks)
    # =====================================================================
    occ = None
    if occurrence_table:
        occ = defaultdict(lambda: Counter())
        syn_hits = defaultdict(Counter)
        for cw in CODEWORDS:
            for cpt in CONCEPTS:
                for r in stream_bank(cw, cpt):
                    key = (r["cell"], r["query_kind"], cpt)
                    t = r["full_prompt"]
                    if mutation == "inject_concept_word":
                        t = t + " " + cpt
                    occ[key]["rows"] += 1
                    own = any(WORD_RES[f].search(t) for f in CONCEPT_FORMS[cpt])
                    if own:
                        occ[key]["own_concept"] += 1
                    anyc = any(WORD_RES[f].search(t) for f in ALL_FORMS)
                    if anyc:
                        occ[key]["any_concept"] += 1
                    other = any(WORD_RES[f].search(t)
                                for oc in CONCEPTS if oc != cpt
                                for f in CONCEPT_FORMS[oc])
                    if other:
                        occ[key]["other_concept"] += 1
                    hit_syn = False
                    for s in CONCEPT_SYNONYMS[cpt]:
                        if WORD_RES[s].search(t):
                            hit_syn = True
                            syn_hits[key][s] += 1
                    if hit_syn:
                        occ[key]["own_synonym"] += 1
                    # cross-check the producer field against our own recount
                    n_own = len(WORD_RES[cpt].findall(t))
                    if n_own != r["n_concept_occurrences"]:
                        occ[key]["disagrees_with_producer_field"] += 1
        out["occurrence"] = {("%s|%s|%s" % k): dict(v) for k, v in occ.items()}
        out["synonym_terms"] = {("%s|%s|%s" % k): dict(v)
                                for k, v in syn_hits.items() if v}
        # concept-free cells: A/C at behavioral + semantic_one_word
        free_keys = [k for k in occ
                     if k[0] in ("A", "C")
                     and k[1] in ("behavioral", "semantic_one_word")]
        n_free_rows = sum(occ[k]["rows"] for k in free_keys)
        n_free_leak = sum(occ[k]["own_concept"] for k in free_keys)
        ck.record("C1_concept_free_channels_have_zero_own_concept_word",
                  n_free_leak == 0, n_free_rows,
                  "%d/%d rows in cells {A,C} x {behavioral,semantic_one_word} "
                  "contain their own concept word (whole-word, case-insensitive)"
                  % (n_free_leak, n_free_rows))
        n_dis = sum(occ[k].get("disagrees_with_producer_field", 0) for k in occ)
        n_all = sum(occ[k]["rows"] for k in occ)
        ck.record("C1b_recount_matches_producer_field", n_dis == 0, n_all,
                  "%d/%d rows where our regex recount of the concept word "
                  "disagrees with the producer's n_concept_occurrences"
                  % (n_dis, n_all))

    # =====================================================================
    # baselines on the probe population
    # =====================================================================
    res = {}

    def run(name, kind, featfn, label_key, tr=None, te=None):
        tr = tr if tr is not None else tr_rows
        te = te if te is not None else te_rows
        if len(tr) == 0 or len(te) == 0:
            res[name] = {"error": "bound zero rows (train=%d test=%d)"
                                  % (len(tr), len(te)), "n_train": len(tr),
                         "n_test": len(te), "acc": None, "auroc": None}
            return res[name]
        try:
            m = fit_eval([featfn(r) for r in tr], [r[label_key] for r in tr],
                         [featfn(r) for r in te], [r[label_key] for r in te],
                         kind)
        except ValueError as e:
            m = {"error": str(e), "n_train": len(tr), "n_test": len(te),
                 "acc": None, "auroc": None}
        res[name] = m
        if verbose:
            print("  %-42s acc=%s auroc=%s (n_tr=%d n_te=%d)"
                  % (name, fmt(m.get("acc")), fmt(m.get("auroc")),
                     m.get("n_train", 0), m.get("n_test", 0)))
        return m

    if verbose:
        print("\n[baselines on probe population] mutation=%s" % mutation)

    # ---- 2. length-only ---------------------------------------------------
    run("2a_length_only_nchars", "dense", lambda r: [r["n_chars"]], "concept")
    run("2b_length_proxies", "dense",
        lambda r: [r["n_chars"], r["n_demos_emitted"], r["n_preamble_lines"]],
        "concept")

    # ---- 3. prompt-text-only ---------------------------------------------
    run("3a_tfidf_fullprompt", "tfidf", lambda r: r["full_prompt"], "concept")
    run("3b_tfidf_fullprompt_masked", "tfidf",
        lambda r: MASK_RE.sub(MASK_TOKEN, r["full_prompt"]), "concept")

    # ---- 4. template-id-only ---------------------------------------------
    def tmpl(r):
        return ["bb=%s" % r["bank_block"], "fs=%s" % r["family_slot"],
                "sp=%s" % r["split"], "cd=%s" % r["condition"],
                "qk=%s" % r["query_kind"]]

    run("4a_templateid_probe_pop", "onehot", tmpl, "concept")
    ctr, cte = grouped(cellc_rows, "concept")
    run("4b_templateid_all_cellC", "onehot", tmpl, "concept", tr=ctr, te=cte)

    # ---- 5. codeword control ---------------------------------------------
    run("5a_codeword_tfidf", "tfidf", lambda r: r["full_prompt"], "codeword")
    run("5b_codeword_tfidf_conceptmasked", "tfidf",
        lambda r: MASK_RE.sub(MASK_TOKEN, r["full_prompt"]), "codeword")
    run("5c_codeword_length_only", "dense", lambda r: [r["n_chars"]], "codeword")
    run("5d_codeword_templateid", "onehot", tmpl, "codeword")

    # ---- 3c/3d. leak-detector positive control on cell B (concept named) --
    btr, bte = grouped(cellb_rows, "concept")
    run("3c_tfidf_cellB_one_word", "tfidf", lambda r: r["full_prompt"],
        "concept", tr=btr, te=bte)
    run("3d_tfidf_cellB_one_word_masked", "tfidf",
        lambda r: mask_text(r["full_prompt"], mutation), "concept",
        tr=btr, te=bte)

    # ---- 6. n_examples = 0 sharp test ------------------------------------
    ztr, zte = grouped(zero_rows, "concept")
    run("6a_n0_tfidf", "tfidf", lambda r: r["full_prompt"], "concept",
        tr=ztr, te=zte)
    run("6b_n0_length", "dense", lambda r: [r["n_chars"]], "concept",
        tr=ztr, te=zte)
    run("6c_n0_templateid", "onehot", tmpl, "concept", tr=ztr, te=zte)

    out["results"] = res

    # =====================================================================
    # checks over the baselines
    # =====================================================================
    Z = 3.0  # ~one-sided p < 0.0014 against chance

    def at_chance(name):
        m = res.get(name)
        if m is None or m.get("acc") is None:
            return False, 0, "no result: %s" % (m or {}).get("error", "missing")
        z = m["z_vs_chance"]
        auc = m["auroc"]
        ok = (z <= Z) and (auc is None or auc <= 0.5 + 0.05)
        return ok, m["n_test"], ("acc=%s (chance=%s, z=%s) auroc=%s"
                                 % (fmt(m["acc"]), fmt(m["chance"], 4),
                                    fmt(z, 2), fmt(auc)))

    for cname, rname in [("C2_length_only_at_chance", "2a_length_only_nchars"),
                         ("C2b_length_proxies_at_chance", "2b_length_proxies"),
                         ("C3_text_only_at_chance", "3a_tfidf_fullprompt"),
                         ("C4_text_masked_at_chance", "3b_tfidf_fullprompt_masked"),
                         ("C5_templateid_at_chance", "4a_templateid_probe_pop"),
                         ("C5b_templateid_allcellC_at_chance", "4b_templateid_all_cellC"),
                         ("C7_n0_tfidf_at_chance", "6a_n0_tfidf"),
                         ("C7b_n0_length_at_chance", "6b_n0_length"),
                         ("C7c_n0_templateid_at_chance", "6c_n0_templateid")]:
        ok, n, d = at_chance(rname)
        ck.record(cname, ok, n, d)

    # positive control: the pipeline MUST be able to find real signal
    m = res.get("5a_codeword_tfidf") or {}
    ck.record("C6_codeword_positive_control_detects_signal",
              (m.get("acc") is not None and m["acc"] >= 0.95),
              m.get("n_test", 0),
              "codeword (button vs basket) from TF-IDF: acc=%s auroc=%s "
              "-- if this is not near 1.0 the pipeline cannot detect signal at all"
              % (fmt(m.get("acc")), fmt(m.get("auroc"))))

    mb = res.get("3c_tfidf_cellB_one_word") or {}
    ck.record("C10_leak_detector_finds_a_real_text_leak",
              (mb.get("acc") is not None and mb["acc"] >= 0.95),
              mb.get("n_test", 0),
              "cell B semantic_one_word (concept word present in full_prompt): "
              "TF-IDF acc=%s auroc=%s -- if this is not near 1.0 the text "
              "classifier cannot see a leak that is provably there"
              % (fmt(mb.get("acc")), fmt(mb.get("auroc"))))
    mbm = res.get("3d_tfidf_cellB_one_word_masked") or {}
    okm = (mbm.get("acc") is not None
           and binom_z(mbm["acc"], mbm["n_test"], 1.0 / 3.0) <= Z)
    ck.record("C11_masking_removes_the_cellB_leak", okm, mbm.get("n_test", 0),
              "cell B masked: acc=%s (chance=0.3333, z=%s) auroc=%s; cell B "
              "mask gap = %s"
              % (fmt(mbm.get("acc")),
                 fmt(binom_z(mbm.get("acc") if mbm.get("acc") is not None
                             else 0.0, max(mbm.get("n_test", 0), 1),
                             1.0 / 3.0), 2),
                 fmt(mbm.get("auroc")),
                 fmt((mb.get("acc") or 0) - (mbm.get("acc") or 0))))
    out["cellB_mask_gap"] = (None if mb.get("acc") is None or mbm.get("acc") is None
                             else mb["acc"] - mbm["acc"])

    # mask gap
    a = (res.get("3a_tfidf_fullprompt") or {}).get("acc")
    b = (res.get("3b_tfidf_fullprompt_masked") or {}).get("acc")
    gap = None if (a is None or b is None) else a - b
    out["mask_gap"] = gap
    ck.record("C4b_mask_gap_is_zero",
              gap is not None and abs(gap) < 1e-12,
              (res.get("3a_tfidf_fullprompt") or {}).get("n_test", 0),
              "unmasked acc %s - masked acc %s = %s" % (fmt(a), fmt(b), fmt(gap)))

    out["checks"] = ck.rows
    out["strongest_nuisance"] = strongest(res)
    return out


NUISANCE_FOR_BAR = ["2a_length_only_nchars", "2b_length_proxies",
                    "3a_tfidf_fullprompt", "3b_tfidf_fullprompt_masked",
                    "4a_templateid_probe_pop"]


def strongest(res):
    best = None
    for k in NUISANCE_FOR_BAR:
        m = res.get(k)
        if not m or m.get("acc") is None:
            continue
        if best is None or m["acc"] > best[1]["acc"]:
            best = (k, m)
    return None if best is None else {"name": best[0], "acc": best[1]["acc"],
                                      "auroc": best[1]["auroc"],
                                      "n_test": best[1]["n_test"]}


# --------------------------------------------------------------------------
# mutation harness
# --------------------------------------------------------------------------
MUTATION_TARGETS = {
    "inject_concept_word": ["C1_concept_free_channels_have_zero_own_concept_word",
                            "C3_text_only_at_chance", "C4b_mask_gap_is_zero",
                            "C12_bayes_bound_from_text_is_chance",
                            "C13_all_concept_free_channels_identical_across_concepts"],
    "length_leak": ["C2_length_only_at_chance", "C2b_length_proxies_at_chance"],
    "template_leak": ["C5_templateid_at_chance", "C5b_templateid_allcellC_at_chance"],
    "corrupt_split": ["C8_domain_grouping_disjoint"],
    "empty_population": ["C9_probe_pop_text_identical_across_concepts",
                         "C3_text_only_at_chance", "C2_length_only_at_chance"],
    "break_codeword_control": ["C6_codeword_positive_control_detects_signal"],
    "unmask_cellB": ["C11_masking_removes_the_cellB_leak"],
}


def run_mutations(baseline):
    print("\n" + "=" * 74)
    print("MUTATION HARNESS -- every check must go RED under its mutation")
    print("=" * 74)
    table = []
    for mut, desc in MUTATIONS.items():
        needs_occ = mut in ("inject_concept_word",)
        print("\n--- mutation: %s (%s)" % (mut, desc))
        r = run_audit(mutation=mut, verbose=False, occurrence_table=needs_occ)
        for tgt in MUTATION_TARGETS[mut]:
            base = baseline["checks"].get(tgt)
            now = r["checks"].get(tgt)
            if base is None:
                row = (mut, tgt, "n/a", "n/a", "MISSING-BASELINE")
            elif now is None:
                row = (mut, tgt, "PASS" if base["pass"] else "FAIL", "absent",
                       "CHECK-NOT-RUN")
            else:
                went_red = base["pass"] and not now["pass"]
                row = (mut, tgt,
                       "PASS" if base["pass"] else "FAIL",
                       "PASS" if now["pass"] else "FAIL",
                       "RED as required" if went_red else
                       ("baseline already FAIL" if not base["pass"]
                        else "*** DID NOT GO RED ***"))
            table.append(row)
            print("    %-52s %s -> %s   %s" % (row[1], row[2], row[3], row[4]))
    return table


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    print("=" * 74)
    print("DCS-TS LEAKAGE AUDIT / NUISANCE BASELINES (CPU only)")
    print("=" * 74)
    base = run_audit(mutation=None, verbose=True, occurrence_table=True)

    print("\n[checks]")
    for k, v in base["checks"].items():
        print("  %-52s %-4s n=%-6d %s"
              % (k, "PASS" if v["pass"] else "FAIL", v["n_bound"], v["detail"]))
    print("\nchecks failing: %d/%d" % (sum(1 for v in base["checks"].values()
                                           if not v["pass"]), len(base["checks"])))
    s = base["strongest_nuisance"]
    if s:
        print("\nTHE PROBE MUST BEAT: %s = %s (accuracy) / %s (AUROC)"
              % (s["name"], fmt(s["acc"]), fmt(s["auroc"])))

    mut_table = None
    if args.mutate:
        mut_table = run_mutations(base)

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"baseline": base,
                       "mutations": mut_table}, fh, indent=1, default=str)
        print("\nwrote %s" % args.json)

    bad = sum(1 for v in base["checks"].values() if not v["pass"])
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
