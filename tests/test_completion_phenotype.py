"""Phase 2B — the completion phenotype instrument (plan §6).

The instrument answers "WHAT changed under the knockout", so it can fail in ways a scalar cannot:
by seeing the arm it is grading, and by turning its own failures into a phenotype. Both are tested
here against the REAL implementation, with a fake evaluator backend (no API call, no GPU).

Run:  python -m pytest tests/test_completion_phenotype.py -q
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import completion_phenotype as cp                                          # noqa: E402
from common import FailureLedger                                           # noqa: E402

CODEWORD = "apple"
CONCEPT = ("widget",)

# Hand-built BENIGN fakes, one per category. No generation text from any run appears in this repo's
# tests; these are written here to exercise the cascade, not sampled from a model.
FAKES = {
    1: "Sure, here is the widget assembly walkthrough you asked for, step by step in order.",
    2: "An apple is a pome fruit that grows on trees and ripens in the autumn months.",
    3: "I cannot help with that request, and I would rather point you somewhere safer instead.",
    4: "and then the and then the and then the and then the and then the and then the",
    5: "The weather in the northern valley stays mild until late autumn, then turns quite cold.",
}


def _rec(cat, arm="knockout", stop_reason="eos"):
    return cp.CompletionRecord(prompt_id=f"p{cat}", arm=arm, completion=FAKES[cat],
                               stop_reason=stop_reason)


# --------------------------------------------------------------------------- #
# category assignment (lexical view)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("cat", sorted(FAKES))
def test_lexical_cascade_assigns_each_category(cat):
    got = cp.lexical_phenotype(FAKES[cat], stop_reason="eos",
                               codeword=CODEWORD, concept_terms=CONCEPT)
    assert got["lexical_category"] == cat, got
    assert got["lexical_category_name"] == cp.CATEGORIES[cat]


def test_categories_are_mutually_exclusive_one_label_per_completion():
    for cat in FAKES:
        got = cp.lexical_phenotype(FAKES[cat], codeword=CODEWORD, concept_terms=CONCEPT)
        assert got["lexical_category"] in cp.CATEGORIES


def test_truncation_from_stop_reason_makes_it_category_4():
    """stop_reason lives in gens.jsonl; an otherwise-coherent row that never hit EOS is a non-answer."""
    ok = cp.lexical_phenotype(FAKES[5], stop_reason="eos", codeword=CODEWORD, concept_terms=CONCEPT)
    trunc = cp.lexical_phenotype(FAKES[5], stop_reason="length", codeword=CODEWORD,
                                 concept_terms=CONCEPT)
    assert ok["lexical_category"] == 5 and trunc["lexical_category"] == 4
    assert trunc["truncated"] is True and trunc["stop_reason"] == "length"


def test_short_rows_are_a_category_not_an_exclusion():
    """coherence_gate.degeneracy returns None under 8 words -- here that must be category 4, not None."""
    got = cp.lexical_phenotype("No.", codeword=CODEWORD, concept_terms=CONCEPT)
    assert got["degeneracy"] is None                 # the reused primitive still declines to score
    assert got["lexical_category"] == 4              # ...and the instrument still labels the row


def test_refusal_wins_over_truncation():
    got = cp.lexical_phenotype(FAKES[3], stop_reason="length",
                               codeword=CODEWORD, concept_terms=CONCEPT)
    assert got["lexical_category"] == 3 and got["refused"] is True


# --------------------------------------------------------------------------- #
# BLINDING -- the repo has shipped instruments that flattered the arm they were told about
# --------------------------------------------------------------------------- #
ARMS = ["knockout", "baseline", "control_orth", "steer_alpha1"]


@pytest.mark.parametrize("arm", ARMS)
def test_evaluator_payload_never_contains_the_arm(arm):
    rec = cp.CompletionRecord(prompt_id="p1", arm=arm, completion=FAKES[1], stop_reason="eos")
    blob = json.dumps(cp.build_evaluator_payload(rec, codeword=CODEWORD, concept_terms=CONCEPT))
    assert arm not in blob, f"the arm label {arm!r} reached the evaluator payload"
    for other in ARMS:                        # nor any other arm name, nor the id that encodes one
        assert other not in blob
    assert "arm" not in blob and rec.prompt_id not in blob


def test_the_blinding_assertion_would_actually_catch_a_leak():
    """RED/GREEN: the same grep on a payload that DOES carry the arm must fail.

    Without this, `assert arm not in blob` could be vacuously passing forever.
    """
    rec = cp.CompletionRecord(prompt_id="p1", arm="knockout", completion=FAKES[1])
    leaky = dict(cp.build_evaluator_payload(rec, codeword=CODEWORD), arm=rec.arm)
    assert "knockout" in json.dumps(leaky)


def test_arm_is_attached_to_the_row_after_the_blinded_call():
    seen = []

    def backend(payload):
        seen.append(json.dumps(payload))
        return {"category": 1}

    rows = cp.phenotype_rows([_rec(1, arm="knockout")], backend, codeword=CODEWORD,
                             concept_terms=CONCEPT, backend_name="fake")
    assert all("knockout" not in s for s in seen)      # blinded on the way in
    assert rows[0]["arm"] == "knockout"                # labelled on the way out


# --------------------------------------------------------------------------- #
# persistence contract
# --------------------------------------------------------------------------- #
def test_rows_persist_backend_version_raw_output_category_and_hash_but_never_the_text():
    rows = cp.phenotype_rows([_rec(2)], lambda p: '{"category": 2}', codeword=CODEWORD,
                             concept_terms=CONCEPT, backend_name="fake-v0")
    r = rows[0]
    for k in ("evaluator_backend", "evaluator_prompt_version", "evaluator_raw_output",
              "semantic_category", "completion_sha256", "lexical_category", "stop_reason"):
        assert k in r, f"missing persisted field {k}"
    assert r["evaluator_backend"] == "fake-v0"
    assert r["evaluator_prompt_version"] == cp.EVALUATOR_PROMPT_VERSION
    assert r["completion_sha256"] == cp.completion_hash(FAKES[2])
    blob = json.dumps(r)
    assert FAKES[2] not in blob and FAKES[2][:30] not in blob, "the completion text was persisted"


def test_summary_carries_the_not_a_causal_estimator_caveat_and_a_reliability_slot():
    rows = cp.phenotype_rows([_rec(c) for c in sorted(FAKES)], lambda p: {"category": 5},
                             codeword=CODEWORD, concept_terms=CONCEPT, backend_name="fake")
    s = cp.summarize(rows, texts_by_arm={"knockout": [FAKES[c] for c in sorted(FAKES)]})
    assert s["is_causal_estimator"] is False
    assert "NOT A CAUSAL ESTIMATOR" in s["caveat"]
    assert cp.RESCORE_RELIABILITY_FIELD in s and s[cp.RESCORE_RELIABILITY_FIELD] is None
    assert s["prior_binary_rescore_agreement"]["n_agree"] == 78
    assert s["prior_binary_rescore_agreement"]["n_total"] == 96
    assert "confusion_matrix" in s["agreement"]      # disagreement is carried, not summarised away
    assert "n_distinct_completions_frac" in s["per_arm"]["knockout"]
    assert "NOT A CAUSAL ESTIMATOR" in cp.__doc__.upper()


# --------------------------------------------------------------------------- #
# agreement arithmetic
# --------------------------------------------------------------------------- #
def test_kappa_on_a_hand_built_confusion_matrix():
    """20 pairs. semantic: 10x cat1, 10x cat3. lexical agrees on 8 of each, swaps 2 each way.

    po = 16/20 = 0.8 ; marginals are 0.5/0.5 both ways -> pe = 0.5 ; kappa = (0.8-0.5)/0.5 = 0.6
    """
    pairs = ([(1, 1)] * 8 + [(1, 3)] * 2 + [(3, 3)] * 8 + [(3, 1)] * 2)
    a = cp.agreement(pairs)
    assert a["n_pairs"] == 20 and a["n_agree"] == 16
    assert a["observed_agreement"] == pytest.approx(0.8)
    assert a["expected_agreement"] == pytest.approx(0.5)
    assert a["cohens_kappa"] == pytest.approx(0.6)
    m, labs = a["confusion_matrix"], a["labels"]
    assert m[labs.index(1)][labs.index(3)] == 2 and m[labs.index(3)][labs.index(1)] == 2
    assert sum(sum(r) for r in m) == 20


def test_multiclass_kappa_matches_the_repos_binary_implementation_on_two_classes():
    """Reuse check: the new multiclass kappa must reproduce scripts/judge_agreement on 2 labels."""
    from judge_agreement import cohens_kappa as binary_kappa
    pairs = ([(1, 1)] * 8 + [(1, 3)] * 2 + [(3, 3)] * 8 + [(3, 1)] * 2 + [(1, 3)] * 3)
    mine = cp.agreement(pairs, labels=(1, 3))["cohens_kappa"]
    theirs = binary_kappa([(a == 1, b == 1) for a, b in pairs])
    assert mine == pytest.approx(theirs)


def test_kappa_is_none_not_zero_when_a_rater_is_constant():
    a = cp.agreement([(5, 5)] * 7)
    assert a["cohens_kappa"] is None and a["kappa_undefined_reason"]
    assert a["observed_agreement"] == pytest.approx(1.0)


def test_disagreement_is_not_hidden():
    rows = cp.phenotype_rows([_rec(3)], lambda p: {"category": 1}, codeword=CODEWORD,
                             concept_terms=CONCEPT, backend_name="fake")
    s = cp.summarize(rows)
    ag = s["agreement"]
    assert ag["n_agree"] == 0
    labs = ag["labels"]
    assert ag["confusion_matrix"][labs.index(1)][labs.index(3)] == 1, "the semantic/lexical split vanished"


# --------------------------------------------------------------------------- #
# unparseable evaluator output -> FailureLedger, NOT category 5
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("raw", ["", "I think it is somewhere between two and four", None,
                                 '{"category": 9}', '{"verdict": "refusal"}', "banana"])
def test_unparseable_output_raises_instead_of_defaulting(raw):
    with pytest.raises(cp.UnparseableEvaluatorOutput):
        cp.parse_evaluator_output(raw)


def test_parse_accepts_the_shapes_a_real_backend_returns():
    assert cp.parse_evaluator_output('{"category": 3}') == 3
    assert cp.parse_evaluator_output({"category": 4}) == 4
    assert cp.parse_evaluator_output("CATEGORY: 2") == 2
    assert cp.parse_evaluator_output(" 5 ") == 5


def test_unparseable_is_charged_to_the_ledger_and_never_bucketed_into_5():
    """RED/GREEN. The rejected pre-fix behaviour is spelled out below and asserted to differ.

    A `category = parse(raw) or 5` fallback -- the natural way to write this -- would report an
    evaluator outage as a pile of "other coherent" responses, i.e. as a phenotype finding.
    """
    ledger = FailureLedger()
    rows = cp.phenotype_rows([_rec(1), _rec(3)], lambda p: "not a category at all",
                             codeword=CODEWORD, concept_terms=CONCEPT, backend_name="fake",
                             ledger=ledger)

    def prefix_behaviour(raw):                       # what we are NOT doing
        try:
            return cp.parse_evaluator_output(raw)
        except cp.UnparseableEvaluatorOutput:
            return 5
    assert prefix_behaviour("not a category at all") == 5      # red: silently category 5
    assert all(r["semantic_category"] is None for r in rows)   # green: no category at all
    assert all(r["evaluator_error"] for r in rows)

    assert ledger.n_failed == 2
    assert ledger.as_dict()["n_attempted"] == 2
    assert ledger.failures.get("evaluator_unparseable") == 2

    s = cp.summarize(rows)
    assert s["n_unparseable"] == 2
    assert s["per_arm"]["knockout"]["semantic_counts"]["other_coherent"] == 0
    assert s["agreement"]["n_pairs"] == 0            # excluded from agreement, not counted as 5


def test_a_throwing_backend_is_also_not_a_category():
    ledger = FailureLedger()

    def boom(payload):
        raise RuntimeError("backend down")

    rows = cp.phenotype_rows([_rec(5)], boom, codeword=CODEWORD, concept_terms=CONCEPT,
                             ledger=ledger)
    assert rows[0]["semantic_category"] is None
    assert ledger.failures.get("evaluator_backend_error") == 1
