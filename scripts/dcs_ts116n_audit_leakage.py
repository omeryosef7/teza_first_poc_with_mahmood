#!/usr/bin/env python
"""DCS gate G5: leakage audit and nuisance baselines on the ts116n bank.

CPU only. No model, no GPU, no network, no SLURM. Every number is re-derived
from the raw bank JSONL rows; no producer-written summary field is trusted as
evidence (n_concept_occurrences is RECOUNTED and the recount is cross-checked).

Why this file exists separately from scripts/dcs_ts_audit_leakage.py: the
previous bank family (ts116) drew the harm pool with the concept word already
replaced by the codeword, so when a harm SENTENCE was shared across concepts
the three arms were byte-identical and every baseline was pinned to 1/3 by
arithmetic (C-074). ts116n generates the harm pool PER CONCEPT, so cell C now
DIFFERS across concepts by construction (G2: 115/115 domains). Consequently the
old script's load-bearing assertions (cell-C byte identity, Bayes bound == 1/3,
mask gap == 0 as evidence of no leak) are FALSE HERE BY DESIGN and are replaced.

Probe population (preregistration configs/dcs_ts_pr046.json):
    field `cell` == "C"   (NOT condition == "natural_doublespeak": A-039)
    query_kind == "semantic_one_word", n_examples == 4,
    classes {bomb, knife, gun}, pooled over both codewords (button, basket),
    train = the 69 ANALYSED train domains, test = the 23 test domains of
    data/boombness_prompts/dcs_ts116_domain_split.json (field "dsplit").
    Validation is never touched.
    Domain "restaurant_kitchen" is a preregistered prompt-only exclusion and is
    dropped from EVERYTHING: 115 analysed domains = 69 train / 23 val / 23 test.

Discipline enforced here:
  * a check that binds zero rows is a FAIL, never a PASS;
  * every check is demonstrated RED under a deliberate mutation (--mutate);
  * splits are domain-grouped and the disjointness assertion is itself mutated.

Usage:
    python scripts/dcs_ts116n_audit_leakage.py
    python scripts/dcs_ts116n_audit_leakage.py --mutate
    python scripts/dcs_ts116n_audit_leakage.py --json PATH
"""

import argparse
import hashlib
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
PREREG_PATH = os.path.join(REPO, "configs", "dcs_ts_pr046.json")

BANK_FAMILY = os.environ.get("BANK_TAG", "ts116n")   # env-selected so the SAME audit code runs on ts116n and ts116m; a second copy is a second place to drift
CONCEPTS = ["bomb", "knife", "gun"]
CODEWORDS = ["button", "basket"]
CONCEPT_IDX = {c: i for i, c in enumerate(CONCEPTS)}
CHANCE3 = 1.0 / 3.0

# preregistered prompt-only exclusion (configs/dcs_ts_pr046.json)
EXCLUDED_DOMAINS = {"restaurant_kitchen"}

CONCEPT_FORMS = {
    "bomb": ["bomb", "bombs", "bombing", "bombings"],
    "knife": ["knife", "knives"],
    "gun": ["gun", "guns", "gunman", "gunmen"],
}
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

# ---- hand-specified surface features (task item 4) -----------------------
# The hedge list is EXACTLY the one measured in the preregistration's
# _register_asymmetry block, so the baseline tests the published asymmetry.
HEDGE_PATTERNS = OrderedDict([
    ("resembl", re.compile(r"resembl\w*", re.IGNORECASE)),
    ("simulat", re.compile(r"simulat\w*", re.IGNORECASE)),
    ("drill", re.compile(r"\bdrills?\b", re.IGNORECASE)),
    ("false_alarm", re.compile(r"false alarm", re.IGNORECASE)),
    ("looks_like", re.compile(r"look(s|ed|ing)? like", re.IGNORECASE)),
])
PUNCT_CHARS = [",", ".", ";", ":", "-", "'", '"', "(", "?"]
_WORD_RE = re.compile(r"[A-Za-z']+")
_SENT_SPLIT = re.compile(r"[.!?]+\s|\n")


def sha16_of_rows(path):
    """bank_rows_sha16 in the repository's canonical spelling
    (src/boombness/common.py:rows_sha16): sha256 over the per-row prompt_sha16
    values, ordered by prompt_id, joined with '|'. Recomputed here from the raw
    rows rather than read from the producer's *_meta.json."""
    pairs = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                pairs.append((str(r["prompt_id"]), str(r["prompt_sha16"])))
    pairs.sort(key=lambda kv: kv[0])
    return hashlib.sha256("|".join(v for _, v in pairs).encode()).hexdigest()[:16]


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

    def n_fail(self):
        return sum(0 if r["pass"] else 1 for r in self.rows.values())


# --------------------------------------------------------------------------
def bank_path(codeword, concept):
    return os.path.join(
        BANKDIR, "boombness_prompt_bank_%s_%s_%s.jsonl"
        % (BANK_FAMILY, codeword, concept))


def stream_bank(codeword, concept):
    with open(bank_path(codeword, concept)) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


KEEP_FIELDS = ["prompt_id", "prompt_sha16", "cell", "query_kind", "n_examples",
               "domain", "split", "condition", "bank_block", "family_slot",
               "n_chars", "n_demos_emitted", "n_preamble_lines", "full_prompt",
               "demo_block", "concept", "codeword", "target_semantic",
               "n_concept_occurrences", "demo_pool_domain"]

_SUBSET_CACHE = {}


def load_subset_cached(key, pred, keep_text=True):
    if key not in _SUBSET_CACHE:
        _SUBSET_CACHE[key] = load_subset(pred, keep_text=keep_text)
    return [dict(r) for r in _SUBSET_CACHE[key]]


def load_subset(pred, keep_text=True):
    """Load rows matching pred(row) from all 6 banks. restaurant_kitchen is
    dropped here so no downstream path can reintroduce it."""
    out = []
    n_excluded = 0
    for cw in CODEWORDS:
        for cpt in CONCEPTS:
            for r in stream_bank(cw, cpt):
                if not pred(r):
                    continue
                if r["domain"] in EXCLUDED_DOMAINS:
                    n_excluded += 1
                    continue
                d = {k: r.get(k) for k in KEEP_FIELDS}
                if not keep_text:
                    d["full_prompt"] = None
                    d["demo_block"] = None
                d["bank_codeword"] = cw
                d["bank_concept"] = cpt
                out.append(d)
    out_meta = {"n_excluded_rows": n_excluded}
    for r in out:
        r["_excl"] = n_excluded
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


def load_prereg():
    with open(PREREG_PATH) as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
def macro_ovr_auroc(y_true, proba, classes):
    y_true = np.asarray(y_true)
    aucs = []
    for i, c in enumerate(classes):
        pos = (y_true == c).astype(int)
        if pos.sum() == 0 or pos.sum() == len(pos):
            return None
        aucs.append(roc_auc_score(pos, proba[:, i]))
    return float(np.mean(aucs))


def binom_z(acc, n, p0):
    if n <= 0:
        return float("nan")
    se = math.sqrt(p0 * (1.0 - p0) / n)
    return (acc - p0) / se if se > 0 else float("nan")


def fit_eval(Xtr, ytr, Xte, yte, kind, groups_te=None, seed=0):
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
    dom_acc = None
    if groups_te is not None:
        per = defaultdict(list)
        for g, p, t in zip(groups_te, pred, yte):
            per[g].append(1.0 if p == t else 0.0)
        dom_acc = float(np.mean([np.mean(v) for v in per.values()]))
    # per-class OvR AUROC
    per_class = {}
    for i, c in enumerate(list(clf.classes_)):
        pos = (np.asarray(yte) == c).astype(int)
        if 0 < pos.sum() < len(pos):
            per_class[str(c)] = float(roc_auc_score(pos, proba[:, i]))
    return {"acc": acc, "auroc": auc, "domain_mean_acc": dom_acc,
            "per_class_auroc": per_class,
            "n_train": ntr, "n_test": nte,
            "n_features": int(n_feat), "chance": p0,
            "z_vs_chance": binom_z(acc, nte, p0),
            "confusion": {"%s->%s" % (t, p): n for (t, p), n
                          in Counter(zip(yte, pred)).items()},
            "pred_dist": dict(Counter(pred))}


def fmt(v, nd=4):
    if v is None:
        return "n/a"
    if isinstance(v, float) and math.isnan(v):
        return "nan"
    return ("%." + str(nd) + "f") % v


# --------------------------------------------------------------------------
# surface feature extractors
# --------------------------------------------------------------------------
def hedge_features(t):
    return [float(len(p.findall(t))) for p in HEDGE_PATTERNS.values()]


def register_features(t):
    sents = [s for s in _SENT_SPLIT.split(t) if s.strip()]
    n_sent = max(len(sents), 1)
    mean_sent_chars = float(np.mean([len(s) for s in sents])) if sents else 0.0
    words = _WORD_RE.findall(t.lower())
    n_words = max(len(words), 1)
    ttr = len(set(words)) / float(n_words)
    feats = [mean_sent_chars, float(n_sent), float(len(words)), ttr,
             float(np.mean([len(w) for w in words])) if words else 0.0]
    feats += [float(t.count(c)) for c in PUNCT_CHARS]
    feats += [float(sum(ch.isdigit() for ch in t)),
              float(sum(ch.isupper() for ch in t))]
    return feats


# --------------------------------------------------------------------------
MUTATIONS = OrderedDict([
    ("inject_concept_word",
     "append the row's own concept word to full_prompt in the probe population"),
    ("length_leak",
     "pad n_chars by 500 * concept index (a concept-dependent length)"),
    ("template_leak",
     "append the concept to bank_block (breaks template alignment)"),
    ("corrupt_split",
     "put 5 test domains into train as well, so the groups overlap"),
    ("empty_population",
     "select cell 'Z' so the probe population binds zero rows"),
    ("break_codeword_control",
     "erase the codeword from the text so the positive control loses its signal"),
    ("unmask_cellB",
     "disable the concept mask so the cell-B leak survives masking"),
    ("hedge_leak",
     "append 'resembling a device' once per concept index to cell-A text"),
    ("plant_shared_sentence",
     "copy one train-domain demo sentence into every test-domain demo block"),
    ("reintroduce_excluded_domain",
     "stop excluding restaurant_kitchen"),
])


def mask_text(t, mutation=None):
    if mutation == "unmask_cellB":
        return t
    return MASK_RE.sub(MASK_TOKEN, t)


def apply_row_mutation(rows, mutation, is_cellA=False):
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
    elif mutation == "hedge_leak" and is_cellA:
        for r in rows:
            if r["full_prompt"] is None:
                continue
            r["full_prompt"] = (r["full_prompt"]
                                + " resembling a device." * CONCEPT_IDX[r["concept"]])
            r["n_chars"] = len(r["full_prompt"])
    return rows


def apply_split_mutation(assign, mutation):
    if mutation != "corrupt_split":
        return assign
    a = dict(assign)
    for d in [d for d, s in sorted(assign.items()) if s == "test"][:5]:
        a[d] = "train_and_test_CORRUPT"
    return a


def split_of(assign, domain):
    s = assign.get(domain)
    return "both" if s == "train_and_test_CORRUPT" else s


# --------------------------------------------------------------------------
def run_audit(mutation=None, verbose=True, occurrence_table=True):
    out = {"mutation": mutation, "bank_family": BANK_FAMILY}
    ck = Checks()
    prereg = load_prereg()
    manifest, assign = load_split()
    assign = apply_split_mutation(assign, mutation)

    global EXCLUDED_DOMAINS
    saved_excl = set(EXCLUDED_DOMAINS)
    if mutation == "reintroduce_excluded_domain":
        EXCLUDED_DOMAINS = set()
        _SUBSET_CACHE.clear()
    try:
        return _run_audit_inner(out, ck, prereg, manifest, assign, mutation,
                                verbose, occurrence_table)
    finally:
        if mutation == "reintroduce_excluded_domain":
            EXCLUDED_DOMAINS = saved_excl
            _SUBSET_CACHE.clear()


def _run_audit_inner(out, ck, prereg, manifest, assign, mutation, verbose,
                     occurrence_table):
    probe_cell = "Z" if mutation == "empty_population" else "C"
    excl_tag = "noexcl" if mutation == "reintroduce_excluded_domain" else "excl"

    # ---- populations ------------------------------------------------------
    def pp(r):
        return (r["cell"] == probe_cell and r["query_kind"] == "semantic_one_word"
                and r["n_examples"] == 4)

    probe_rows = apply_row_mutation(
        load_subset_cached(("probe", probe_cell, excl_tag), pp), mutation)
    out["n_probe_rows"] = len(probe_rows)

    def zerop(r):
        return (r["cell"] == probe_cell and r["n_examples"] == 0
                and r["query_kind"] == "semantic_one_word")

    zero_rows = apply_row_mutation(
        load_subset_cached(("zero", probe_cell, excl_tag), zerop), mutation)
    out["n_zero_rows"] = len(zero_rows)

    def bpp(r):
        return (r["cell"] == ("Y" if mutation == "empty_population" else "B")
                and r["query_kind"] == "semantic_one_word"
                and r["n_examples"] == 4)

    cellb_rows = apply_row_mutation(
        load_subset_cached(("cellb", probe_cell, excl_tag), bpp), mutation)
    out["n_cellb_rows"] = len(cellb_rows)

    # cell A n=4 semantic_one_word: byte-identical across concepts by G3.
    # This is the NEGATIVE-CONTROL population: any baseline run on it must be
    # exactly at chance, which is what makes the length/hedge mutations RED.
    def ap(r):
        return (r["cell"] == ("Y" if mutation == "empty_population" else "A")
                and r["query_kind"] == "semantic_one_word"
                and r["n_examples"] == 4)

    cellA_rows = apply_row_mutation(
        load_subset_cached(("cellA", probe_cell, excl_tag), ap), mutation,
        is_cellA=True)
    out["n_cellA_rows"] = len(cellA_rows)

    def cellc(r):
        return r["cell"] == probe_cell

    cellc_rows = apply_row_mutation(
        load_subset_cached(("cellc", probe_cell, excl_tag), cellc, keep_text=False),
        mutation)
    out["n_cellc_rows"] = len(cellc_rows)

    # ---- domain-grouped split ---------------------------------------------
    def grouped(rows):
        tr, te = [], []
        for r in rows:
            s = split_of(assign, r["domain"])
            if s == "train":
                tr.append(r)
            elif s == "test":
                te.append(r)
            elif s == "both":
                tr.append(r)
                te.append(r)
        return tr, te

    tr_rows, te_rows = grouped(probe_rows)
    dtr = set(r["domain"] for r in tr_rows)
    dte = set(r["domain"] for r in te_rows)
    overlap = dtr & dte
    n_val_dom = len(set(d for d, s in assign.items()
                        if s == "validation" and d not in EXCLUDED_DOMAINS))
    ck.record(
        "G5_07_domain_grouping_disjoint",
        len(overlap) == 0 and len(dtr) > 0 and len(dte) > 0,
        len(tr_rows) + len(te_rows),
        "train domains=%d test domains=%d overlap=%d %s; validation domains=%d "
        "(held out, never read); manifest_sha16=%s"
        % (len(dtr), len(dte), len(overlap), sorted(overlap)[:5], n_val_dom,
           manifest.get("manifest_sha16")))
    out.update({"train_domains": len(dtr), "test_domains": len(dte),
                "overlap_domains": sorted(overlap),
                "n_train_rows": len(tr_rows), "n_test_rows": len(te_rows),
                "n_validation_domains": n_val_dom})

    # ---- exclusion is actually applied ------------------------------------
    n_rk = sum(1 for r in probe_rows if r["domain"] in ("restaurant_kitchen",))
    all_dom = set(r["domain"] for r in probe_rows)
    ck.record("G5_00_excluded_domain_absent_and_population_is_115",
              n_rk == 0 and len(all_dom) == 115, len(probe_rows),
              "restaurant_kitchen rows in probe population=%d (must be 0); "
              "distinct domains=%d (must be 115); train/val/test = %d/%d/%d"
              % (n_rk, len(all_dom), len(dtr), n_val_dom, len(dte)))

    # ---- bank identity -----------------------------------------------------
    if mutation is None:
        sha_ok, sha_detail = True, []
        for cw in CODEWORDS:
            for cpt in CONCEPTS:
                key = "%s_%s" % (cw, cpt)
                want = prereg["population"]["banks"][key]["bank_rows_sha16"]
                got = sha16_of_rows(bank_path(cw, cpt))
                sha_detail.append("%s %s%s" % (key, got, "" if got == want
                                               else " != prereg %s" % want))
                sha_ok = sha_ok and (got == want)
        ck.record("G5_bank_rows_sha16_matches_preregistration", sha_ok, 6,
                  "; ".join(sha_detail))
        out["bank_sha16"] = sha_detail

    # =====================================================================
    # 1. CONCEPT-WORD OCCURRENCE TABLE over full_prompt
    # =====================================================================
    if occurrence_table:
        occ = defaultdict(Counter)
        syn_hits = defaultdict(Counter)
        for cw in CODEWORDS:
            for cpt in CONCEPTS:
                for r in stream_bank(cw, cpt):
                    if r["domain"] in EXCLUDED_DOMAINS:
                        continue
                    key = (r["cell"], r["query_kind"], cpt)
                    t = r["full_prompt"]
                    if (mutation == "inject_concept_word"
                            and r["cell"] == "C"
                            and r["query_kind"] == "semantic_one_word"
                            and r["n_examples"] == 4):
                        t = t + " " + cpt
                    occ[key]["rows"] += 1
                    if any(WORD_RES[f].search(t) for f in CONCEPT_FORMS[cpt]):
                        occ[key]["own_concept"] += 1
                    if any(WORD_RES[f].search(t) for f in ALL_FORMS):
                        occ[key]["any_concept"] += 1
                    if any(WORD_RES[f].search(t) for oc in CONCEPTS if oc != cpt
                           for f in CONCEPT_FORMS[oc]):
                        occ[key]["other_concept"] += 1
                    hit_syn = False
                    for s in CONCEPT_SYNONYMS[cpt]:
                        if WORD_RES[s].search(t):
                            hit_syn = True
                            syn_hits[key][s] += 1
                    if hit_syn:
                        occ[key]["own_synonym"] += 1
                    if len(WORD_RES[cpt].findall(t)) != r["n_concept_occurrences"]:
                        occ[key]["disagrees_with_producer_field"] += 1
        out["occurrence"] = {("%s|%s|%s" % k): dict(v) for k, v in occ.items()}
        out["synonym_terms"] = {("%s|%s|%s" % k): dict(v)
                                for k, v in syn_hits.items() if v}

        prim = [k for k in occ if k[0] == "C" and k[1] == "semantic_one_word"]
        n_prim = sum(occ[k]["rows"] for k in prim)
        n_prim_own = sum(occ[k]["own_concept"] for k in prim)
        n_prim_any = sum(occ[k]["any_concept"] for k in prim)
        ck.record("G5_01_primary_channel_zero_own_and_any_concept_word",
                  n_prim_own == 0 and n_prim_any == 0, n_prim,
                  "cell C x semantic_one_word (all doses): own-concept rows=%d/%d, "
                  "ANY-concept rows=%d/%d. Non-zero => the probe population is "
                  "CONTAMINATED and the probe can read a printed word."
                  % (n_prim_own, n_prim, n_prim_any, n_prim))
        out["primary_channel_occ"] = {"rows": n_prim, "own": n_prim_own,
                                      "any": n_prim_any}
        # per-concept, so a clean arm cannot be hidden behind a dirty one and so
        # the mutation harness has arms that are GREEN at baseline to turn red.
        for cpt in CONCEPTS:
            k = ("C", "semantic_one_word", cpt)
            v = occ.get(k, Counter())
            ck.record("G5_01_%s_primary_channel_zero_concept_word" % cpt,
                      v.get("own_concept", 0) == 0 and v.get("any_concept", 0) == 0,
                      v.get("rows", 0),
                      "cell C x semantic_one_word x %s: own=%d any=%d of %d rows"
                      % (cpt, v.get("own_concept", 0), v.get("any_concept", 0),
                         v.get("rows", 0)))

        n_dis = sum(occ[k].get("disagrees_with_producer_field", 0) for k in occ)
        n_all = sum(occ[k]["rows"] for k in occ)
        ck.record("G5_01b_recount_matches_producer_field", n_dis == 0, n_all,
                  "%d/%d rows where our own regex recount of the concept word "
                  "disagrees with the producer-written n_concept_occurrences"
                  % (n_dis, n_all))

    # ---- enumerate the contaminated probe rows, by domain and split --------
    contam = defaultdict(int)
    contam_sent = set()
    for r in probe_rows:
        t = r["full_prompt"]
        if t is None:
            continue
        if any(WORD_RES[f].search(t) for f in CONCEPT_FORMS[r["concept"]]):
            contam[(r["concept"], r["domain"], split_of(assign, r["domain"]),
                    r["bank_codeword"])] += 1
            for ln in (r["demo_block"] or "").split("\n"):
                if any(WORD_RES[f].search(ln) for f in CONCEPT_FORMS[r["concept"]]):
                    contam_sent.add(ln.strip())
    out["contaminated_probe_rows"] = {"|".join(map(str, k)): v
                                      for k, v in sorted(contam.items())}
    out["contaminated_sentences"] = sorted(contam_sent)
    n_contam = sum(contam.values())
    n_contam_test = sum(v for k, v in contam.items() if k[2] == "test")
    ck.record("G5_01d_probe_population_n4_is_concept_word_free",
              n_contam == 0, len(probe_rows),
              "%d/%d n_examples=4 probe rows print their own concept word "
              "(%d of them in TEST domains), across %d distinct demo sentences"
              % (n_contam, len(probe_rows), n_contam_test, len(contam_sent)))
    out["n_contaminated_probe_rows"] = n_contam
    out["n_contaminated_probe_rows_test"] = n_contam_test

    # ---- descriptive: the register asymmetry, re-derived from BANK ROWS ----
    desc = {}
    for cpt in CONCEPTS:
        rows = [r for r in probe_rows if r["concept"] == cpt]
        sents = []
        for r in rows:
            sents += [x.strip() for x in (r["demo_block"] or "").split("\n")
                      if x.strip()]
        usents = sorted(set(sents))
        nh = sum(1 for x in usents
                 if any(p_.search(x) for p_ in HEDGE_PATTERNS.values()))
        desc[cpt] = {
            "n_rows": len(rows),
            "mean_n_chars": float(np.mean([r["n_chars"] for r in rows])) if rows else None,
            "sd_n_chars": float(np.std([r["n_chars"] for r in rows])) if rows else None,
            "n_distinct_demo_sentences": len(usents),
            "hedged_sentences": nh,
            "hedged_pct": 100.0 * nh / len(usents) if usents else None,
            "mean_sentence_chars": float(np.mean([len(x) for x in usents])) if usents else None,
            "distinct_n_demos_emitted": sorted(set(r["n_demos_emitted"] for r in rows)),
            "distinct_n_preamble_lines": sorted(set(r["n_preamble_lines"] for r in rows)),
        }
    out["register_descriptives"] = desc

    # =====================================================================
    # baseline runner
    # =====================================================================
    res = {}

    def run(name, kind, featfn, label_key, tr=None, te=None):
        tr = tr if tr is not None else tr_rows
        te = te if te is not None else te_rows
        if len(tr) == 0 or len(te) == 0:
            res[name] = {"error": "bound zero rows (train=%d test=%d)"
                                  % (len(tr), len(te)),
                         "n_train": len(tr), "n_test": len(te),
                         "acc": None, "auroc": None}
            return res[name]
        try:
            m = fit_eval([featfn(r) for r in tr], [r[label_key] for r in tr],
                         [featfn(r) for r in te], [r[label_key] for r in te],
                         kind, groups_te=[r["domain"] for r in te])
        except ValueError as e:
            m = {"error": str(e), "n_train": len(tr), "n_test": len(te),
                 "acc": None, "auroc": None}
        res[name] = m
        if verbose:
            print("  %-44s acc=%s dom=%s auroc=%s (n_tr=%d n_te=%d)"
                  % (name, fmt(m.get("acc")), fmt(m.get("domain_mean_acc")),
                     fmt(m.get("auroc")), m.get("n_train", 0), m.get("n_test", 0)))
        return m

    if verbose:
        print("\n[nuisance baselines] mutation=%s" % mutation)

    atr, ate = grouped(cellA_rows)
    btr, bte = grouped(cellb_rows)
    ztr, zte = grouped(zero_rows)
    ctr, cte = grouped(cellc_rows)

    # ---- 2. N4 LENGTH-ONLY -------------------------------------------------
    run("N4a_length_only_nchars", "dense", lambda r: [r["n_chars"]], "concept")
    run("N4b_length_plus_structure", "dense",
        lambda r: [r["n_chars"], r["n_demos_emitted"], r["n_preamble_lines"]],
        "concept")
    run("N4c_length_only_cellA_control", "dense", lambda r: [r["n_chars"]],
        "concept", tr=atr, te=ate)

    # ---- 3. N5 PROMPT-TEXT-ONLY TF-IDF ------------------------------------
    run("N5a_tfidf_fullprompt", "tfidf", lambda r: r["full_prompt"], "concept")
    run("N5b_tfidf_fullprompt_conceptmasked", "tfidf",
        lambda r: mask_text(r["full_prompt"], mutation), "concept")
    run("N5c_tfidf_demoblock_conceptmasked", "tfidf",
        lambda r: mask_text(r["demo_block"] or "", mutation), "concept")
    run("N5d_tfidf_cellA_control", "tfidf", lambda r: r["full_prompt"],
        "concept", tr=atr, te=ate)

    # ---- 4. HEDGE-ONLY and REGISTER-ONLY ----------------------------------
    run("H1_hedge_only_fullprompt", "dense",
        lambda r: hedge_features(r["full_prompt"]), "concept")
    run("H2_register_only_fullprompt", "dense",
        lambda r: register_features(r["full_prompt"]), "concept")
    run("H3_hedge_plus_register", "dense",
        lambda r: hedge_features(r["full_prompt"])
        + register_features(r["full_prompt"]), "concept")
    run("H4_hedge_plus_register_cellA_control", "dense",
        lambda r: hedge_features(r["full_prompt"])
        + register_features(r["full_prompt"]), "concept", tr=atr, te=ate)

    # ---- 5. N6 TEMPLATE-ID-ONLY -------------------------------------------
    def tmpl(r):
        return ["bb=%s" % r["bank_block"], "fs=%s" % r["family_slot"],
                "sp=%s" % r["split"], "cd=%s" % r["condition"],
                "qk=%s" % r["query_kind"]]

    run("N6a_templateid_probe_pop", "onehot", tmpl, "concept")
    run("N6b_templateid_all_cellC", "onehot", tmpl, "concept", tr=ctr, te=cte)

    # ---- N7 codeword positive control -------------------------------------
    run("N7a_codeword_tfidf", "tfidf", lambda r: r["full_prompt"], "codeword")
    run("N7b_codeword_length_only", "dense", lambda r: [r["n_chars"]], "codeword")

    # ---- leak-detector positive control on cell B -------------------------
    run("L1_tfidf_cellB", "tfidf", lambda r: r["full_prompt"], "concept",
        tr=btr, te=bte)
    run("L2_tfidf_cellB_masked", "tfidf",
        lambda r: mask_text(r["full_prompt"], mutation), "concept",
        tr=btr, te=bte)

    # ---- 6. N1 n_examples = 0 SHARP TEST ----------------------------------
    run("N1a_n0_tfidf", "tfidf", lambda r: r["full_prompt"], "concept",
        tr=ztr, te=zte)
    run("N1b_n0_length", "dense", lambda r: [r["n_chars"]], "concept",
        tr=ztr, te=zte)
    run("N1c_n0_hedge_register", "dense",
        lambda r: hedge_features(r["full_prompt"])
        + register_features(r["full_prompt"]), "concept", tr=ztr, te=zte)
    run("N1d_n0_templateid", "onehot", tmpl, "concept", tr=ztr, te=zte)
    out["n_zero_train_rows"] = len(ztr)
    out["n_zero_test_rows"] = len(zte)

    # =====================================================================
    # 8. CROSS-DOMAIN SENTENCE LEAKAGE
    # =====================================================================
    def sents_of(r):
        return [s.strip() for s in (r["demo_block"] or "").split("\n") if s.strip()]

    train_sent = defaultdict(set)      # sentence -> set of train domains
    for r in tr_rows:
        for s in sents_of(r):
            train_sent[s].add(r["domain"])
    planted = None
    if mutation == "plant_shared_sentence" and train_sent:
        planted = sorted(train_sent)[0]
    n_leak_rows, leaked_sent = 0, set()
    for r in te_rows:
        ss = sents_of(r)
        if planted is not None:
            ss = ss + [planted]
        hit = [s for s in ss if s in train_sent
               and any(d != r["domain"] for d in train_sent[s])]
        if hit:
            n_leak_rows += 1
            leaked_sent.update(hit)
    test_sent = set()
    for r in te_rows:
        test_sent.update(sents_of(r))
    if planted is not None:
        test_sent.add(planted)
    ck.record("G5_08_no_cross_domain_sentence_leakage",
              n_leak_rows == 0, len(te_rows),
              "%d/%d TEST rows share at least one verbatim demo sentence with a "
              "DIFFERENT-domain TRAIN row; %d distinct leaked sentences out of "
              "%d distinct test-domain demo sentences (%d distinct train "
              "sentences). Previous bank: 72/3864 rows."
              % (n_leak_rows, len(te_rows), len(leaked_sent), len(test_sent),
                 len(train_sent)))
    ck.record("G5_08b_sentence_leakage_is_not_wholesale",
              n_leak_rows < 0.5 * max(len(te_rows), 1), len(te_rows),
              "%d/%d TEST rows carry a train-domain sentence; a rate at or above "
              "50%% would mean the demo pools are shared across the split rather "
              "than drawn per domain" % (n_leak_rows, len(te_rows)))
    out["sentence_leak"] = {"test_rows_with_leak": n_leak_rows,
                            "n_test_rows": len(te_rows),
                            "distinct_leaked_sentences": len(leaked_sent),
                            "distinct_test_sentences": len(test_sent),
                            "distinct_train_sentences": len(train_sent),
                            "examples": sorted(leaked_sent)[:5]}

    # =====================================================================
    # checks over the baselines
    # =====================================================================
    Z = 3.0     # one-sided p ~ 0.0013 against chance

    def verdict(name):
        m = res.get(name)
        if m is None or m.get("acc") is None:
            return False, 0, "no result: %s" % (m or {}).get("error", "missing")
        z, auc = m["z_vs_chance"], m["auroc"]
        ok = (z <= Z) and (auc is None or auc <= 0.55)
        return ok, m["n_test"], ("acc=%s domain_mean_acc=%s (chance=%s, z=%s) "
                                 "auroc=%s" % (fmt(m["acc"]),
                                               fmt(m.get("domain_mean_acc")),
                                               fmt(m["chance"]), fmt(z, 2),
                                               fmt(auc)))

    # MUST-PASS-BY-CONSTRUCTION checks
    for cname, rname in [
            ("G5_06_N6_templateid_at_chance", "N6a_templateid_probe_pop"),
            ("G5_06b_N6_templateid_all_cellC_at_chance", "N6b_templateid_all_cellC"),
            ("G5_09_N1_n0_tfidf_at_chance", "N1a_n0_tfidf"),
            ("G5_09b_N1_n0_length_at_chance", "N1b_n0_length"),
            ("G5_09c_N1_n0_hedge_register_at_chance", "N1c_n0_hedge_register"),
            ("G5_09d_N1_n0_templateid_at_chance", "N1d_n0_templateid"),
            ("G5_10_cellA_control_text_at_chance", "N5d_tfidf_cellA_control"),
            ("G5_10b_cellA_control_length_at_chance", "N4c_length_only_cellA_control"),
            ("G5_10c_cellA_control_hedge_register_at_chance",
             "H4_hedge_plus_register_cellA_control")]:
        ok, n, d = verdict(rname)
        ck.record(cname, ok, n, d)

    # MEASUREMENT checks: these MAY legitimately be RED on ts116n; the number,
    # not the colour, is the deliverable. They are recorded so the report cannot
    # quietly omit an above-chance nuisance baseline.
    for cname, rname in [("G5_02_N4_length_only_at_chance", "N4a_length_only_nchars"),
                         ("G5_02b_N4_length_plus_structure_at_chance",
                          "N4b_length_plus_structure"),
                         ("G5_03_N5_text_masked_at_chance",
                          "N5b_tfidf_fullprompt_conceptmasked"),
                         ("G5_04_hedge_only_at_chance", "H1_hedge_only_fullprompt"),
                         ("G5_04b_register_only_at_chance", "H2_register_only_fullprompt")]:
        ok, n, d = verdict(rname)
        ck.record(cname, ok, n, "MEASUREMENT (may be RED by design on ts116n) -- " + d)

    m = res.get("N7a_codeword_tfidf") or {}
    ck.record("G5_11_codeword_positive_control_detects_signal",
              m.get("acc") is not None and m["acc"] >= 0.95, m.get("n_test", 0),
              "codeword (button vs basket) from TF-IDF: acc=%s auroc=%s -- if this "
              "is not near 1.0 the pipeline cannot detect signal at all"
              % (fmt(m.get("acc")), fmt(m.get("auroc"))))

    mb = res.get("L1_tfidf_cellB") or {}
    ck.record("G5_12_leak_detector_finds_a_real_text_leak",
              mb.get("acc") is not None and mb["acc"] >= 0.95, mb.get("n_test", 0),
              "cell B semantic_one_word (concept word IS printed): TF-IDF acc=%s "
              "auroc=%s" % (fmt(mb.get("acc")), fmt(mb.get("auroc"))))
    mbm = res.get("L2_tfidf_cellB_masked") or {}
    gapB = (None if mb.get("acc") is None or mbm.get("acc") is None
            else mb["acc"] - mbm["acc"])
    # STRUCTURAL: the masker must actually delete the printed word. Its residual
    # accuracy is NOT the test -- on ts116n the cell-B predicates still carry the
    # register asymmetry, so masked accuracy stays high for a legitimate reason.
    n_b_masked_leftover = sum(
        1 for r in cellb_rows
        if r["full_prompt"] is not None
        and any(WORD_RES[f].search(mask_text(r["full_prompt"], mutation))
                for f in ALL_FORMS))
    ck.record("G5_13_masker_deletes_every_printed_concept_word",
              n_b_masked_leftover == 0, len(cellb_rows),
              "%d/%d cell-B rows still contain a concept word AFTER masking "
              "(must be 0). Unmasked cell-B acc=%s -> masked acc=%s, gap=%s: the "
              "residual is the register/predicate channel, not the printed word."
              % (n_b_masked_leftover, len(cellb_rows), fmt(mb.get("acc")),
                 fmt(mbm.get("acc")), fmt(gapB)))
    out["cellB_mask_gap"] = gapB
    out["cellB_masked_leftover"] = n_b_masked_leftover

    a = (res.get("N5a_tfidf_fullprompt") or {}).get("acc")
    b = (res.get("N5b_tfidf_fullprompt_conceptmasked") or {}).get("acc")
    out["probe_mask_gap"] = None if (a is None or b is None) else a - b
    ck.record("G5_05_probe_mask_gap_is_zero",
              out["probe_mask_gap"] is not None
              and abs(out["probe_mask_gap"]) < 1e-12,
              (res.get("N5a_tfidf_fullprompt") or {}).get("n_test", 0),
              "unmasked %s - masked %s = %s. Concept-word masking is a near-"
              "no-op on the primary channel (only the rows named by check 01d "
              "print a concept word at all), so the MASKED number is the honest "
              "text bar and a large gap would mean a word-level leak."
              % (fmt(a), fmt(b), fmt(out["probe_mask_gap"])))

    out["results"] = res
    out["checks"] = ck.rows
    out["strongest_nuisance"] = strongest(res)
    return out


NUISANCE_FOR_BAR = ["N4a_length_only_nchars", "N4b_length_plus_structure",
                    "N5a_tfidf_fullprompt", "N5b_tfidf_fullprompt_conceptmasked",
                    "N5c_tfidf_demoblock_conceptmasked",
                    "H1_hedge_only_fullprompt", "H2_register_only_fullprompt",
                    "H3_hedge_plus_register", "N6a_templateid_probe_pop"]


def strongest(res):
    best = None
    for k in NUISANCE_FOR_BAR:
        m = res.get(k)
        if not m or m.get("acc") is None:
            continue
        if best is None or m["acc"] > best[1]["acc"]:
            best = (k, m)
    return None if best is None else {
        "name": best[0], "acc": best[1]["acc"], "auroc": best[1]["auroc"],
        "domain_mean_acc": best[1].get("domain_mean_acc"),
        "n_test": best[1]["n_test"]}


# --------------------------------------------------------------------------
MUTATION_TARGETS = {
    "inject_concept_word": ["G5_01_bomb_primary_channel_zero_concept_word",
                            "G5_01_gun_primary_channel_zero_concept_word",
                            "G5_05_probe_mask_gap_is_zero"],
    "length_leak": ["G5_10b_cellA_control_length_at_chance"],
    "template_leak": ["G5_06_N6_templateid_at_chance",
                      "G5_06b_N6_templateid_all_cellC_at_chance"],
    "corrupt_split": ["G5_07_domain_grouping_disjoint"],
    "empty_population": ["G5_00_excluded_domain_absent_and_population_is_115",
                         "G5_06_N6_templateid_at_chance",
                         "G5_08b_sentence_leakage_is_not_wholesale",
                         "G5_10_cellA_control_text_at_chance"],
    "break_codeword_control": ["G5_11_codeword_positive_control_detects_signal"],
    "unmask_cellB": ["G5_13_masker_deletes_every_printed_concept_word"],
    "hedge_leak": ["G5_10c_cellA_control_hedge_register_at_chance"],
    "plant_shared_sentence": ["G5_08b_sentence_leakage_is_not_wholesale"],
    "reintroduce_excluded_domain":
        ["G5_00_excluded_domain_absent_and_population_is_115"],
}


def run_mutations(baseline):
    print("\n" + "=" * 78)
    print("MUTATION HARNESS -- every check must go RED under its mutation")
    print("=" * 78)
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
                row = (mut, tgt, "PASS" if base["pass"] else "FAIL",
                       "PASS" if now["pass"] else "FAIL",
                       "RED as required" if went_red
                       else ("baseline already FAIL" if not base["pass"]
                             else "*** DID NOT GO RED ***"))
            table.append(row)
            print("    %-56s %s -> %s   %s" % (row[1], row[2], row[3], row[4]))
    return table


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    print("=" * 78)
    print("DCS GATE G5 -- LEAKAGE AUDIT / NUISANCE BASELINES on %s (CPU only)"
          % BANK_FAMILY)
    print("=" * 78)
    base = run_audit(mutation=None, verbose=True, occurrence_table=True)

    print("\n[occurrence table] cell | query_kind | concept "
          "-> rows / own-concept / any-concept / other-concept / own-synonym")
    for k in sorted(base.get("occurrence", {})):
        v = base["occurrence"][k]
        print("  %-40s rows=%-6d own=%-6d any=%-6d other=%-6d syn=%-6d"
              % (k, v.get("rows", 0), v.get("own_concept", 0),
                 v.get("any_concept", 0), v.get("other_concept", 0),
                 v.get("own_synonym", 0)))

    print("\n[checks]")
    for k, v in base["checks"].items():
        print("  %-56s %-4s n=%-7d %s"
              % (k, "PASS" if v["pass"] else "FAIL", v["n_bound"], v["detail"]))
    nf = sum(1 for v in base["checks"].values() if not v["pass"])
    print("\nchecks failing: %d/%d" % (nf, len(base["checks"])))

    s = base["strongest_nuisance"]
    if s:
        print("\nTHE PROBE MUST BEAT: %s = %s / %s"
              % (s["name"], fmt(s["acc"]), fmt(s["auroc"])))
    n4 = max([base["results"][k]["acc"] for k in
              ("N4a_length_only_nchars", "N4b_length_plus_structure")
              if base["results"].get(k, {}).get("acc") is not None] or [None])
    if n4 is not None:
        trig = n4 >= 0.40
        print("N4 VERDICT: best length-only accuracy = %s (chance 0.3333) -- "
              "length-matching rule %s" % (fmt(n4),
                                           "TRIGGERED" if trig else "NOT triggered"))

    mut_table = None
    if args.mutate:
        mut_table = run_mutations(base)

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"baseline": base, "mutations": mut_table}, fh, indent=1,
                      default=str)
        print("\nwrote %s" % args.json)

    # exit non-zero only on a MUST-PASS-BY-CONSTRUCTION failure
    must = [k for k, v in base["checks"].items()
            if not v["pass"] and "MEASUREMENT" not in v["detail"]]
    if must:
        print("\nSTRUCTURAL CHECK FAILURES: %s" % must)
    sys.exit(1 if must else 0)


if __name__ == "__main__":
    main()
