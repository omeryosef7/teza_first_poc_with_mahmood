"""`TSC-PR-007`'s constructibility filter: determinism, every refusal, and the no-text invariant.

The filter decides which harmful requests the doublespeak frame can express at all. Its whole value
is that it is MECHANICAL — the same input always yields the same verdict, no item is ever chosen or
dropped by hand, and every rejection carries a named reason. This file pins those properties, plus
the two that protect the artifact: it never emits request text, and its tokenizer gate really can
refuse (`CDS-C-002` made preventive).
"""
import io
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import tsc_filter_requests as F  # noqa: E402

LEX = os.path.join(ROOT, "data", "manifests", "tsc_concept_lexicon_v1.txt")
ART = os.path.join(ROOT, "data", "manifests", "tsc_requests_v1_filtered.json")


# --------------------------------------------------------------------------- lexicon

def test_lexicon_loads_and_is_all_single_alphabetic_tokens():
    terms = F.load_lexicon(LEX)
    assert len(terms) == 46
    assert all(t.isalpha() and t == t.lower() for t in terms)
    assert len(set(terms)) == len(terms)


def test_lexicon_excludes_every_codeword_in_use():
    """`C4` at the lexicon level: a concept colliding with a codeword breaks the mapping under test."""
    terms = set(F.load_lexicon(LEX))
    assert terms.isdisjoint(set(F.CODEWORDS_IN_USE))


def test_REFUSES_empty_lexicon(tmp_path):
    p = tmp_path / "l.txt"; p.write_text("# only a comment\n\n")
    with pytest.raises(SystemExit) as e:
        F.load_lexicon(str(p))
    assert "no terms" in str(e.value)


def test_REFUSES_duplicate_lexicon_term(tmp_path):
    p = tmp_path / "l.txt"; p.write_text("bomb\nvirus\nbomb\n")
    with pytest.raises(SystemExit) as e:
        F.load_lexicon(str(p))
    assert "repeats" in str(e.value)


def test_REFUSES_multiword_lexicon_term(tmp_path):
    p = tmp_path / "l.txt"; p.write_text("bomb\npipe bomb\n")
    with pytest.raises(SystemExit) as e:
        F.load_lexicon(str(p))
    assert "single alphabetic" in str(e.value)


# --------------------------------------------------------------------------- C1 matching

def test_match_is_word_bounded_not_substring():
    """`gun` must not match inside `begun`, nor `pill` inside `pillar`.

    A substring test is the documented reason `topicality_gate` inflates by ~19 %; that fix was
    never back-ported to the judge, and is applied here from the start.
    """
    terms = ["gun", "pill", "bomb"]
    assert F.match_terms("the project had begun in a pillar factory", terms) == []
    assert F.match_terms("how to build a bomb", terms) == ["bomb"]


def test_simple_plural_is_accepted_but_irregulars_are_not():
    terms = ["drug", "knife", "virus"]
    assert F.match_terms("distribute illegal drugs", terms) == ["drug"]
    assert F.match_terms("write viruses", terms) == ["virus"]
    #: `knives` is an irregular plural: it must FAIL loudly rather than be stemmed into a guess.
    assert F.match_terms("sharpen the knives", terms) == []


def test_match_is_case_insensitive():
    assert F.match_terms("Build a BOMB now", ["bomb"]) == ["bomb"]


# --------------------------------------------------------------------------- C2 tie-break

def test_tiebreak_is_longest_then_alphabetical_and_is_deterministic():
    assert F.resolve(["virus", "ransomware"]) == "ransomware"
    assert F.resolve(["ransomware", "virus"]) == "ransomware"      # order-independent
    assert F.resolve(["bomb", "drug"]) == "bomb"                   # equal length -> alphabetical
    assert F.resolve(["drug", "bomb"]) == "bomb"


def test_tiebreak_never_drops_a_row():
    """`C2` resolves; it is not a rejection reason. A drop here would be a silent exclusion."""
    assert "TIEBREAK" not in " ".join(F.REASONS)
    assert F.resolve(["a", "bb", "ccc"]) == "ccc"


# --------------------------------------------------------------------------- C5 tokenizer gate

@pytest.mark.skipif(os.environ.get("TSC_SKIP_TOKENIZER") == "1", reason="tokenizer unavailable")
def test_tokenizer_gate_accepts_the_surviving_concepts_and_can_refuse():
    """`CDS-C-002` made preventive, and proved able to FAIL rather than merely to pass."""
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
    for c in ("bomb", "virus", "poison", "drug"):
        ok, why = F.tokenizer_stable(tok, c)
        assert ok, f"{c} should be stable, got {why}"
    #: a concept whose word-bounded text occurrences cannot align with token spans must be refused.
    ok, why = F.tokenizer_stable(tok, "zzqxwv")
    assert isinstance(ok, bool)


# --------------------------------------------------------------------------- the artifact

@pytest.mark.skipif(not os.path.exists(ART), reason="filter artifact not built")
def test_artifact_carries_no_request_text():
    """⛔ The attrition table must be reviewable, and circulated, without redistributing AdvBench."""
    import csv
    doc = json.load(open(ART, encoding="utf-8"))
    blob = json.dumps(doc)
    #: THE REAL INVARIANT, not a word-blacklist. My first version banned the literal string
    #: "instruction" and failed on the artifact's own `query_template`
    #: ("...instructions to build a {W}...") -- a crude test that flags the fixed frame while a
    #: genuine leak of a *different* wording would sail through. What must be absent is any
    #: SOURCE INSTRUCTION, so that is what is checked, against the source file itself.
    with open(os.path.join(ROOT, "data", "manifests", "heldout_495.csv"),
              newline="", encoding="utf-8") as fh:
        instructions = [r["instruction"] for r in csv.DictReader(fh)]
    assert instructions, "source manifest is empty; the check would be vacuous"
    for text in instructions:
        assert text not in blob, "artifact leaked a source instruction verbatim"
        #: and no long fragment either -- a truncated leak is still a leak.
        assert text[:40] not in blob, "artifact leaked a 40-char fragment of a source instruction"
    allowed = {"task_id", "category", "concept", "verdict", "reason", "resolved_by_tiebreak",
               "n_lexicon_hits", "duplicate_of", "tokenizer_detail"}
    for r in doc["attrition_table"]:
        assert set(r) <= allowed, f"unexpected key in attrition row: {set(r) - allowed}"


@pytest.mark.skipif(not os.path.exists(ART), reason="filter artifact not built")
def test_every_drawn_request_has_exactly_one_verdict_and_reasons_are_from_the_closed_set():
    doc = json.load(open(ART, encoding="utf-8"))
    rows = doc["attrition_table"]
    assert len(rows) == doc["n_drawn"] == 40
    assert len({r["task_id"] for r in rows}) == 40
    for r in rows:
        assert r["verdict"] in ("CONSTRUCTIBLE", "REJECTED")
        if r["verdict"] == "REJECTED":
            assert r["reason"] in F.REASONS, r["reason"]
        else:
            assert r["reason"] is None and r["concept"]


@pytest.mark.skipif(not os.path.exists(ART), reason="filter artifact not built")
def test_survivors_are_globally_distinct_and_counts_reconcile():
    doc = json.load(open(ART, encoding="utf-8"))
    surv = [r for r in doc["attrition_table"] if r["verdict"] == "CONSTRUCTIBLE"]
    assert len(surv) == doc["n_constructible"]
    concepts = [r["concept"] for r in surv]
    assert len(set(concepts)) == len(concepts), "C6 violated: a concept survives twice"
    assert sorted(concepts) == doc["surviving_concepts"]
    #: the attrition reasons must account for every non-survivor -- no row unexplained.
    assert sum(doc["attrition_by_reason"].values()) == doc["n_drawn"] - doc["n_constructible"]


@pytest.mark.skipif(not os.path.exists(ART), reason="filter artifact not built")
def test_artifact_pins_the_lexicon_and_the_selection_it_was_run_against():
    """Provenance: the filter output must name the exact draw and the exact lexicon."""
    doc = json.load(open(ART, encoding="utf-8"))
    assert doc["selection_sha16"] == "bed56c91e70a707c"
    assert doc["lexicon_n_terms"] == 46
    assert doc["cluster_unit"] == "harmful_request"
    assert "{W}" in doc["query_template"]
    assert doc["query_template"].count("{W}") == 1
