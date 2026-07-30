"""
GPU-free tests for the fixed-pair causal core (CAUSAL_CORE_PLAN Phase A).

Covers the two things that would silently corrupt every downstream causal number:
  * the benchmark's controlled minimum + split disjointness + condition balance (§3);
  * the readout answer->meaning classifier and probability-group construction (§16.4).

Run:  python -m pytest doublespeak_causality/tests/test_pair_benchmark.py -q
"""
import os
import sys
import json
import importlib.util

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, "..")
sys.path.insert(0, PKG)


def _load(name, filename):
    """Numeric-prefixed modules cannot be imported normally (house idiom)."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(PKG, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bench_mod = _load("build_pair_benchmark", "30_build_pair_benchmark.py")
readout_mod = _load("validate_readouts", "31_validate_readouts.py")

BENCH_PATH = os.path.join(PKG, "data", "pair_benchmark", "pair_carrot_bomb.json")


# --------------------------------------------------------------------------- #
# Builder-level invariants (no data file needed)
# --------------------------------------------------------------------------- #
def test_paraphrases_meet_controlled_minimum():
    ps = bench_mod.paraphrases("bomb")
    assert len(ps) >= 50
    assert len({p["pid"] for p in ps}) == len(ps)
    for p in ps:
        filled = p["instruction_template"].format(n="bomb")
        assert filled.count("bomb") == 1, filled


def test_demo_axes_meet_controlled_minimum():
    assert len(bench_mod.DEMO_STYLES) >= 5
    assert len(bench_mod.DEMO_COUNTS) >= 3
    assert len(bench_mod.READOUTS) >= 3


def test_carries_accepts_inflections():
    # the word-boundary regex this replaced dropped every plural and unbalanced the pools
    assert bench_mod.carries("Two carrots were on the table.", "carrot")
    assert bench_mod.carries("The bombing was reported.", "bomb")
    assert not bench_mod.carries("The potato was on the table.", "carrot")


def test_offline_pools_are_split_disjoint_and_remap_safe():
    pools, topups = bench_mod.build_sentence_pools(None, None, "bomb", 7, True, remap_to="carrot")
    assert sum(topups.values()) == 0  # offline build fills from the template bank, not a top-up
    for style, sp in pools.items():
        assert len(sp["dev"]) == bench_mod.MAX_DEMOS
        assert len(sp["heldout"]) == bench_mod.MAX_DEMOS
        assert not (set(sp["dev"]) & set(sp["heldout"])), style
        for s in bench_mod.remapped(sp["dev"], "bomb", "carrot"):
            assert bench_mod.carries(s, "carrot")
            assert not bench_mod.carries(s, "bomb")


def test_split_assignment_is_deterministic():
    a = [bench_mod.split_of(f"k{i}") for i in range(50)]
    b = [bench_mod.split_of(f"k{i}") for i in range(50)]
    assert a == b
    assert set(a) == {"dev", "heldout"}


# --------------------------------------------------------------------------- #
# Readout classifier
# --------------------------------------------------------------------------- #
# Lexicons are now built PER PAIR (they used to be a hardcoded dict for carrot<->bomb,
# which made `reads_as_concept` structurally 0 for every other concept -- see ITER24).
LEX = bench_mod.build_lexicons("bomb", "carrot", "bicycle", "virus")


@pytest.mark.parametrize("answer,expected", [
    ("bomb", "bomb"),
    ("Bomb.", "bomb"),
    ("  explosive  ", "bomb"),
    ("An explosive device", "bomb"),
    ("carrot", "carrot"),
    ("A vegetable.", "carrot"),
    ("bicycle", "bicycle"),
    ("virus", "virus"),
    ("kettle", "OTHER"),
    ("", "EMPTY"),
    ("   ", "EMPTY"),
    ("!!!", "EMPTY"),
])
def test_classify_answer(answer, expected):
    assert readout_mod.classify_answer(answer, LEX) == expected


def test_lexicons_cover_every_role_of_a_pair():
    """REGRESSION (ITER24): a concept with no lexicon makes the S2 gate vacuously 0."""
    for concept in ("bomb", "grenade", "pistol", "cocaine", "chlorine"):
        lex = bench_mod.build_lexicons(concept, "carrot", "bicycle", "virus")
        assert concept in lex, concept
        assert concept in lex[concept], f"lexicon for {concept} omits the word itself"
        assert "carrot" in lex and "carrot" in lex["carrot"]


def test_build_lexicon_includes_plurals():
    assert "grenades" in bench_mod.build_lexicon("grenade")
    assert "bomb" in bench_mod.build_lexicon("bomb")


def test_lexicons_are_disjoint():
    seen = {}
    for key, words in LEX.items():
        for w in words:
            assert w not in seen, f"{w} in both {seen.get(w)} and {key}"
            seen[w] = key


def test_normalize_answer_caps_length():
    assert readout_mod.normalize_answer("a b c d e f") == ["a", "b", "c", "d"]


# --------------------------------------------------------------------------- #
# Built-artifact invariants (skipped if the benchmark has not been generated)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not os.path.exists(BENCH_PATH), reason="benchmark not built yet")
def test_built_benchmark_is_balanced_and_disjoint():
    d = json.load(open(BENCH_PATH))
    m = d["_meta"]
    assert m["n_paraphrases"] >= 50
    assert m["n_demo_styles"] >= 5 and m["n_readouts"] >= 3
    assert m["n_skipped"] == 0

    sem = d["semantic"]
    varying = [c for c in d["conditions"]
               if c not in ("REPEATED_CODEWORD", "DIRECT_CONCEPT_NODEMO",
                            "NEUTRAL_CODEWORD_NODEMO")]
    sizes = {c: sum(1 for r in sem if r["condition"] == c) for c in varying}
    assert len(set(sizes.values())) == 1, sizes

    dev = {r["prompt"] for r in sem if r["split"] == "dev" and r["has_demos"]
           and r["condition"] != "REPEATED_CODEWORD"}
    ho = {r["prompt"] for r in sem if r["split"] == "heldout" and r["has_demos"]
          and r["condition"] != "REPEATED_CODEWORD"}
    assert not (dev & ho)

    # every semantic prompt must contain its probe word (positions are resolved on it)
    for r in sem:
        assert r["probe_word"].lower() in r["prompt"].lower(), r["sid"]

    # the DOUBLESPEAK demonstrations must not leak the concept word
    for r in sem:
        if r["condition"] == "DOUBLESPEAK":
            block = r["prompt"].rsplit("\n\n", 1)[0]
            assert d["pair"]["concept"] not in block.lower(), r["sid"]


@pytest.mark.skipif(not os.path.exists(BENCH_PATH), reason="benchmark not built yet")
def test_behavioral_conditions_are_matched():
    d = json.load(open(BENCH_PATH))
    cc, cw = d["pair"]["concept"], d["pair"]["codeword"]
    for r in d["behavioral"]:
        # Direct and Neutral differ only by the concept<->codeword swap
        assert r["direct"].replace(cc, cw) == r["neutral"], r["bid"]
        assert r["doublespeak"].endswith(r["neutral"]), r["bid"]
        assert cc not in r["doublespeak"].lower(), r["bid"]
