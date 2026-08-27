"""bank_leakage_probe.py — can the CELL LABEL be predicted from the surface text alone?

WHY. The sprint brief's Phase 1 warns against topic leakage: "do not compare a farm-storage carrot
prompt to a city-bridge bomb prompt and call the difference boombness". `prompt_families.py` claims
to have solved this by construction (the core 2x2 is an exact word swap) and `check_alignment`
asserts it AT GENERATION TIME. This module asks the different question: does the invariant hold on
the bank files AS SHIPPED, and is it strong enough to carry `d_surface`?

THE DECISIVE TEST IS DETERMINISTIC, NOT A CLASSIFIER.
`d_surface = 1/2[(B - C) + (E - A)]`. Read off `CONDITIONS`:

    A benign_literal        demo benign, demo surface codeword, query codeword
    C natural_doublespeak   demo harm,   demo surface codeword, query codeword
    E concept_in_benign_ctx demo benign, demo surface concept,  query concept
    B direct_harmful        demo harm,   demo surface concept,  query concept

Both differences in `d_surface` hold VALENCE FIXED and swap only the target word. So if the design
is what it claims, then after masking every occurrence of the codeword and of the concept:

    masked(B) == masked(C)  byte for byte,  and  masked(E) == masked(A)

If that holds, `d_surface` cannot be carrying topic, domain or valence — there is no other lexical
difference left for it to carry. If it fails anywhere, `d_surface` is contaminated and the sprint
needs to know exactly where. A byte-equality test is far stronger evidence than any classifier
accuracy, and unlike an accuracy it cannot be argued with.

The classifier is therefore used only for the factors the design explicitly does NOT match. The
`prompt_families.py` docstring is candid about this: "NOT matchable: the valence factor's
predicates. A doublespeak demo only teaches carrot=bomb if it carries predicates only a bomb
affords". So `d_context = 1/2[(C - A) + (B - E)]` is EXPECTED to be lexically predictable, and
measuring how predictable makes the asymmetry between the two directions quantitative rather than
asserted. A dependency-free multinomial Naive Bayes is used (scikit-learn is not installed here),
with folds split BY FAMILY so the classifier can never memorise a family it is then tested on.

Also audits the vowel-article bug that killed `arrow` as a concept ("a arrow", 528 ungrammatical
rows, R-AZ). A masked-identity test is structurally BLIND to that class, because masking makes both
arms identical exactly where the article disagreement lives.

Reads prompt text. Emits COUNTS AND IDS ONLY — never a prompt, never a fragment, not even a diff.
Run in the MAIN loop or a SLURM/CPU job, NEVER in a subagent.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import re
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, FailureLedger, RunDir, read_jsonl  # noqa: E402

SCHEMA = "BANK_LEAKAGE_PROBE/1"
MASK = "W"

CORE = ("benign_literal", "direct_harmful", "natural_doublespeak", "concept_in_benign_ctx")
#: The two contrasts making up d_surface. Each holds valence fixed and swaps only the target word.
D_SURFACE_PAIRS = (("direct_harmful", "natural_doublespeak"),      # B vs C, valence = harm
                   ("concept_in_benign_ctx", "benign_literal"))    # E vs A, valence = benign
#: The two making up d_context. These change valence and are NOT expected to be identical.
D_CONTEXT_PAIRS = (("natural_doublespeak", "benign_literal"),      # C vs A
                   ("direct_harmful", "concept_in_benign_ctx"))    # B vs E

VOWELS = "aeiouAEIOU"


def mask_targets(text: str, codeword: str, concept: str) -> str:
    """Replace every occurrence of either target word with one opaque token.

    Word-boundary anchored and longest-first, so `bomb` inside `bombard` is not masked and a
    concept that is a prefix of the codeword cannot be half-masked.

    CASE-INSENSITIVE, and that was a bug once. The first draft matched case-sensitively, so a
    sentence-initial `Basket` / `Knife` survived masking and the pair compared unequal. It reported
    11 of 24 banks as leaking `d_surface` -- every knife bank plus the long-preamble ones -- and
    the "violations" turned out to be exactly {Knife: 8, Basket: 8}: the swap had happened
    correctly and only the capitalised form was left behind. A masking bug that manufactures
    alignment violations is worse than no probe at all, so the case-fold is deliberate and
    `capitalisation_audit` below covers what it gives up.
    """
    out = text
    for w in sorted({codeword, concept}, key=len, reverse=True):
        if w:
            out = re.sub(r"\b" + re.escape(w) + r"\b", MASK, out, flags=re.IGNORECASE)
    return out


def capitalisation_audit(byc: Dict[str, Dict], cw: str, cn: str,
                         field: str = "full_prompt") -> List[str]:
    """What the case-insensitive mask gives up: a REAL case mismatch between the two arms.

    Masking case-insensitively would hide a bank where one arm writes `Basket` and the other
    `knife` at the same position. That is a genuine alignment defect (it changes tokenization),
    so the capitalisation PATTERN of the target occurrences is compared separately.
    """
    def pattern(txt: str) -> List[bool]:
        pats = []
        for w in sorted({cw, cn}, key=len, reverse=True):
            if not w:
                continue
            for m in re.finditer(r"\b" + re.escape(w) + r"\b", txt, flags=re.IGNORECASE):
                pats.append(m.group(0)[:1].isupper())
        return pats

    bad = []
    for hi, lo in D_SURFACE_PAIRS:
        if hi in byc and lo in byc:
            if pattern(byc[hi].get(field) or "") != pattern(byc[lo].get(field) or ""):
                bad.append(f"{hi}|{lo}")
    return bad


def _family_stem(row: Dict) -> str:
    """The family key WITHOUT its condition, so the four cells of one family group together."""
    return "|".join(str(row.get(k)) for k in
                    ("domain", "split", "family_slot", "n_examples", "strength", "consistency",
                     "example_position", "role_style", "query_kind", "bank_block"))


def masked_identity_audit(rows: List[Dict], field: str = "full_prompt") -> Dict[str, Any]:
    """For every complete family, check the d_surface pairs are byte-identical after masking."""
    fams: Dict[str, Dict[str, Dict]] = collections.defaultdict(dict)
    for r in rows:
        fams[_family_stem(r)][r.get("condition")] = r

    pairs = {f"{hi}|{lo}": {"checked": 0, "identical": 0, "violations": []}
             for hi, lo in D_SURFACE_PAIRS}
    ctx = {f"{hi}|{lo}": {"checked": 0, "identical": 0} for hi, lo in D_CONTEXT_PAIRS}
    cap_mismatch: collections.Counter = collections.Counter()
    n_complete = 0

    for stem, byc in fams.items():
        if not all(c in byc for c in CORE):
            continue
        n_complete += 1
        cw = byc["benign_literal"].get("codeword") or ""
        cn = byc["benign_literal"].get("concept") or ""
        m = {c: mask_targets(r.get(field) or "", cw, cn) for c, r in byc.items()}
        for k in capitalisation_audit(byc, cw, cn, field):
            cap_mismatch[k] += 1
        for hi, lo in D_SURFACE_PAIRS:
            k = f"{hi}|{lo}"
            pairs[k]["checked"] += 1
            if m[hi] == m[lo]:
                pairs[k]["identical"] += 1
            elif len(pairs[k]["violations"]) < 20:
                # IDS AND LENGTHS ONLY. Never the text, never a diff of the text.
                pairs[k]["violations"].append(
                    {"family_stem": stem, "prompt_id_hi": byc[hi].get("prompt_id"),
                     "prompt_id_lo": byc[lo].get("prompt_id"),
                     "masked_len_hi": len(m[hi]), "masked_len_lo": len(m[lo])})
        for hi, lo in D_CONTEXT_PAIRS:
            k = f"{hi}|{lo}"
            ctx[k]["checked"] += 1
            ctx[k]["identical"] += int(m[hi] == m[lo])

    for v in pairs.values():
        v["identical_frac"] = (v["identical"] / v["checked"]) if v["checked"] else None
        v["n_violations"] = v["checked"] - v["identical"]
    for v in ctx.values():
        v["identical_frac"] = (v["identical"] / v["checked"]) if v["checked"] else None

    clean = bool(pairs) and all(v["checked"] > 0 and v["identical"] == v["checked"]
                                for v in pairs.values())
    return {"field": field, "n_complete_families": n_complete,
            "d_surface_pairs": pairs, "d_context_pairs": ctx,
            "d_surface_is_lexically_clean": clean,
            "capitalisation_mismatch_families": dict(cap_mismatch),
            "n_capitalisation_mismatches": sum(cap_mismatch.values()),
            "INTERPRETATION": (
                "d_surface_is_lexically_clean=true means that after masking both target words the "
                "two contrasts making up d_surface are BYTE-IDENTICAL, so d_surface cannot be "
                "carrying topic, domain or valence: no other lexical difference remains. The "
                "d_context pairs are EXPECTED to differ (the valence predicates are not matchable "
                "by construction) and are reported as the contrast, not as a defect.")}


def _tok(t: str) -> List[str]:
    return re.findall(r"[a-z']+", t.lower())


class NaiveBayes:
    """Multinomial NB with Laplace smoothing. About 30 lines; scikit-learn is not installed here."""

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.logprior: Dict[str, float] = {}
        self.loglik: Dict[str, Dict[str, float]] = {}
        self.default: Dict[str, float] = {}

    def fit(self, docs: List[List[str]], labels: List[str]) -> "NaiveBayes":
        by: Dict[str, List[List[str]]] = collections.defaultdict(list)
        for d, y in zip(docs, labels):
            by[y].append(d)
        n = len(docs)
        vocab = {w for d in docs for w in d}
        V = max(1, len(vocab))
        for y, ds in by.items():
            self.logprior[y] = math.log(len(ds) / n)
            cnt = collections.Counter(w for d in ds for w in d)
            tot = sum(cnt.values()) + self.alpha * V
            self.loglik[y] = {w: math.log((cnt[w] + self.alpha) / tot) for w in vocab}
            self.default[y] = math.log(self.alpha / tot)
        return self

    def predict(self, doc: List[str]) -> str:
        best, bs = None, -1e18
        for y in self.logprior:
            s = self.logprior[y] + sum(self.loglik[y].get(w, self.default[y]) for w in doc)
            if s > bs:
                best, bs = y, s
        return best


def grouped_cv(rows: List[Dict], target: str, field: str = "full_prompt",
               n_folds: int = 5, mask: bool = True) -> Dict[str, Any]:
    """Predict `target` from text, with folds split BY FAMILY so no family is train AND test."""
    docs, ys, groups = [], [], []
    for r in rows:
        if r.get(target) is None:
            continue
        t = r.get(field) or ""
        if mask:
            t = mask_targets(t, r.get("codeword") or "", r.get("concept") or "")
        docs.append(_tok(t))
        ys.append(str(r[target]))
        groups.append(_family_stem(r))
    if not docs:
        return {"n": 0, "accuracy": None, "majority_baseline": None}
    uniq = sorted(set(groups))
    fold_of = {g: i % n_folds for i, g in enumerate(uniq)}
    correct = 0
    for f in range(n_folds):
        tr = [i for i in range(len(docs)) if fold_of[groups[i]] != f]
        te = [i for i in range(len(docs)) if fold_of[groups[i]] == f]
        if not tr or not te or len({ys[i] for i in tr}) < 2:
            continue
        nb = NaiveBayes().fit([docs[i] for i in tr], [ys[i] for i in tr])
        correct += sum(1 for i in te if nb.predict(docs[i]) == ys[i])
    maj = collections.Counter(ys).most_common(1)[0][1] / len(ys)
    acc = correct / len(docs)
    return {"n": len(docs), "n_classes": len(set(ys)), "n_family_groups": len(uniq),
            "accuracy": acc, "majority_baseline": maj, "lift_over_majority": acc - maj,
            "masked": mask}


def article_audit(rows: List[Dict], field: str = "full_prompt") -> Dict[str, Any]:
    """`a arrow` / `an bomb` — the class a masked-identity test is structurally blind to."""
    bad_a: collections.Counter = collections.Counter()
    bad_an: collections.Counter = collections.Counter()
    for r in rows:
        for m in re.finditer(r"\b(a|an)\s+([A-Za-z]+)", r.get(field) or ""):
            art, w = m.group(1).lower(), m.group(2)
            if art == "a" and w[0] in VOWELS:
                bad_a[w.lower()] += 1
            elif art == "an" and w[0] not in VOWELS:
                bad_an[w.lower()] += 1
    return {"n_rows": len(rows),
            "a_before_vowel": {"total": sum(bad_a.values()),
                               "by_word": dict(bad_a.most_common(10))},
            "an_before_consonant": {"total": sum(bad_an.values()),
                                    "by_word": dict(bad_an.most_common(10))},
            "NOTE": ("R-AZ rejected `arrow` as a concept over 528 ungrammatical `a arrow` rows. "
                     "Masking hides this class, because both arms mask to the same token exactly "
                     "where the article disagreement lives.")}


def audit_bank(path: str) -> Dict[str, Any]:
    rows = read_jsonl(path)
    core = [r for r in rows if r.get("bank_block") in ("core2x2", "core2x2_slot3")
            and r.get("condition") in CORE]
    return {
        "bank": os.path.basename(path), "n_rows": len(rows), "n_core_2x2_rows": len(core),
        "masked_identity": masked_identity_audit(core),
        "classifier": {
            # THE ONE THAT MATTERS: with the target masked, can text still say which SURFACE arm a
            # row is? Under the design it cannot, because the texts are identical.
            "query_surface_masked": grouped_cv(core, "query_surface", mask=True),
            # The contrast: valence IS lexically encoded, by construction and by admission.
            "demo_valence_masked": grouped_cv(core, "demo_valence", mask=True),
            # Sanity check on the instrument. Unmasked, surface is trivially predictable; if this
            # is NOT high then the masking or the tokenizer is broken, not the bank.
            "query_surface_unmasked": grouped_cv(core, "query_surface", mask=False),
            "domain_masked": grouped_cv(core, "domain", mask=True),
        },
        "grammar": article_audit(rows),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bank", action="append", default=[],
                    help="bank .jsonl; repeat. Default: every boombness_prompt_bank*.jsonl")
    ap.add_argument("--tag", default="leak")
    args = ap.parse_args()

    banks = args.bank or sorted(glob.glob(os.path.join(DATA_DIR, "boombness_prompt_bank*.jsonl")))
    ledger = FailureLedger()
    run = RunDir("bank_leakage_probe", args, tag=args.tag)
    results = []
    for b in banks:
        r = audit_bank(b)
        results.append(r)
        run.log_row(r)
        mi = r["masked_identity"]
        ok = mi["d_surface_is_lexically_clean"]
        if ok:
            ledger.ok()
        else:
            ledger.fail("d_surface_not_lexically_clean", r["bank"])
        cls = r["classifier"]["query_surface_masked"]
        gram = (r["grammar"]["a_before_vowel"]["total"]
                + r["grammar"]["an_before_consonant"]["total"])
        print(f"  {r['bank'][:40]:40s} core={r['n_core_2x2_rows']:5d} "
              f"fams={mi['n_complete_families']:4d} clean={ok} "
              f"surf_masked_acc={cls['accuracy']} (maj {cls['majority_baseline']}) "
              f"bad_articles={gram}")

    n_clean = sum(1 for r in results if r["masked_identity"]["d_surface_is_lexically_clean"])
    out = {"schema": SCHEMA, "n_banks": len(results), "n_banks_d_surface_clean": n_clean,
           "banks": results,
           "VERDICT_NOTE": (
               "d_surface_is_lexically_clean is the decisive result. It is a BYTE-EQUALITY test, "
               "not a classifier accuracy, so it cannot be argued with: if it holds, the "
               "d_surface contrast has no lexical content beyond the masked target word and the "
               "brief's topic-leakage concern does not apply to it. The classifier numbers are "
               "secondary and exist to quantify the factors the design openly does not match.")}
    p = os.path.join(run.path, "bank_leakage_probe.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    run.finish(summary={"n_banks": len(results), "n_banks_d_surface_clean": n_clean}, ledger=ledger)
    print(f"[leak] wrote {p}  ({n_clean}/{len(results)} banks lexically clean for d_surface)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
