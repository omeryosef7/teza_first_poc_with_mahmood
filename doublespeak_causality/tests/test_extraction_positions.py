"""Regression test for the extraction position reconciliation (execution log E12,
bug class B9). The corpus `codeword_occurrences_templated` spans are in CHAT-TEMPLATED
space and are DOUBLESPEAK-specific; extraction must chat-template the raw prompt and
anchor only doublespeak against the corpus span. Uses the real Llama tokenizer; skips
if it is not cached locally (no network)."""
import os, sys, types
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

CORPUS = os.path.join(HERE, "..", "data", "splits", "clearharm_doublespeak_v3.json")


@pytest.fixture(scope="module")
def tok():
    try:
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
    except Exception as e:
        pytest.skip(f"Llama tokenizer unavailable offline: {e}")


def test_doublespeak_positions_match_corpus_spans(tok):
    import ds_common as dc
    from src.probes import probe_dataset as pdset, activation_extraction as ae
    lm = types.SimpleNamespace(tokenizer=tok)
    corpus = pdset.load_corpus(CORPUS)
    items = pdset.build_items(corpus, conditions=("doublespeak", "benign", "neutral"),
                              cohort="clearharm")[:36]
    # must not raise; doublespeak anchored to corpus spans, benign/neutral resolved
    n_ds, n_other = ae.preflight_positions(lm, corpus, items, n_check=36)
    assert n_ds >= 8 and n_other >= 8


def test_raw_prompt_would_fail_anchor(tok):
    """Guard the reconciliation itself: WITHOUT templating, the doublespeak codeword
    lands at a different index than the corpus span (i.e. the bug the preflight caught).
    This proves the anchor is load-bearing, not vacuous."""
    import ds_common as dc, pair_common as pc
    from src.probes import probe_dataset as pdset
    lm = types.SimpleNamespace(tokenizer=tok)
    corpus = pdset.load_corpus(CORPUS)
    items = [it for it in pdset.build_items(corpus, conditions=("doublespeak",),
             cohort="clearharm")[:6]]
    ex_by = {str(e["example_id"]): e for e in corpus["examples"]}
    mism = 0
    for it in items:
        raw = ex_by[it.example_id][it.prompt_field]           # RAW, un-templated
        pos = pc.resolve_positions(lm, raw, it.codeword)
        exp = it.query_span()[1] - 1
        if pos.codeword_last != exp:
            mism += 1
    assert mism >= 1  # raw prompt does NOT match the templated corpus span
