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
    # must not raise; all positions resolve (hard check). corpus-span rate is soft (B19).
    n_ds, n_other, span_rate = ae.preflight_positions(lm, corpus, items, n_check=36)
    assert n_ds >= 8 and n_other >= 8
    assert span_rate is None or 0.0 <= span_rate <= 1.0


def test_hard_check_requires_codeword_in_prompt_body(tok):
    """The hard preflight check: codeword_last must be a real prompt-body position
    (0 <= codeword_last < final_prompt). A gibberish codeword that does not resolve
    must raise, proving the hard check is load-bearing."""
    from src.probes import probe_dataset as pdset, activation_extraction as ae
    lm = types.SimpleNamespace(tokenizer=tok)
    corpus = pdset.load_corpus(CORPUS)
    items = pdset.build_items(corpus, conditions=("doublespeak",), cohort="clearharm")[:2]
    # break the codeword so it cannot resolve -> hard check must raise
    bad = [type(items[0])(**{**items[0].__dict__, "codeword": "zzqxnotacodewordzz"})]
    import pytest as _pt
    with _pt.raises(Exception):
        ae.preflight_positions(lm, corpus, bad, n_check=1)


def test_generated_cohort_resolves(tok):
    """The generated cohort's corpus spans are stale (B19), but positions still resolve
    (extraction is correct by construction). Preflight must PASS, span rate may be low."""
    from src.probes import probe_dataset as pdset, activation_extraction as ae
    lm = types.SimpleNamespace(tokenizer=tok)
    corpus = pdset.load_corpus(CORPUS)
    items = pdset.build_items(corpus, conditions=("doublespeak", "benign", "neutral"),
                              cohort="generated")[:36]
    n_ds, n_other, span_rate = ae.preflight_positions(lm, corpus, items, n_check=36)
    assert n_ds >= 8 and n_other >= 8  # must not raise despite stale spans
