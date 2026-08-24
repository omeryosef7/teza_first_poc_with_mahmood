"""Tests for src/boombness/semantic_binding_probe.py (plan §5.1). Pure CPU, no model weights.

The instrument is new, so there is no pre-fix revision to pin. The project rule ("every fix ships
with a test that demonstrably fails under the pre-fix behaviour") is honoured the only way it can
be here: each guard is paired IN-PROCESS with the NAIVE implementation it replaces — the obvious
one-liner a reader would otherwise write — and the test asserts that the naive version produces the
defective answer while the module refuses or corrects it. The four naive baselines are

  naive pairing        a list comprehension that FILTERS unusable probe rows away, so a probe set
                       that lost a third of its rows is indistinguishable from one that lost none
  naive option ids     `tok(" " + word)["input_ids"][0]`, which silently returns a FIRST SUBTOKEN
                       for a multi-token word (the `carrot` -> `car` bug signals.readout_ids exists
                       for) and makes the two sides of the margin different kinds of number
  naive argmax         `max(lp, key=lp.get)`, which awards a forced choice on an exact TIE by dict
                       order
  naive exact match    `top1_id == primary_id`, which scores the model's own preferred spelling
                       (' Bomb') as a miss

No prompt, demonstration or completion text appears in this file: the synthetic bank uses opaque
placeholder strings, and every assertion is on ids, counts and scalars.
"""
from __future__ import annotations

import json
import math
import os
import sys

import pytest
import torch

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))

import semantic_binding_probe as sbp        # noqa: E402
import signals as sg                        # noqa: E402
import score_behavior as sb                 # noqa: E402  (the REAL readout, not a copy)
from common import FailureLedger            # noqa: E402

REAL_BANK = os.path.join(REPO, "data", "boombness_prompts", "boombness_prompt_bank.jsonl")


# --------------------------------------------------------------------------- #
# A tiny tokenizer that reproduces the tokenization facts the module is built around
# --------------------------------------------------------------------------- #
PIECES = [
    " bomb", "bomb", " Bomb", "Bomb",          # concept: single token in every variant
    " carrot", "car", "rot", " Car", "Car",    # codeword: only the leading-space form is whole
    " knife", "knife", " gun", "gun", " club", "club",
    " gren", "gren", "ade", " Gren", "Gren",   # 'grenade': multi-token in EVERY variant
    " tulip", "tulip",
    "Answer", ":", " ", "X",
]
PIECE_ID = {p: i for i, p in enumerate(PIECES)}
VOCAB = len(PIECES)


class FakeTok:
    """Greedy longest-match tokenizer over PIECES; unknown characters map to 'X'."""

    pad_token_id = PIECE_ID["X"]
    eos_token_id = PIECE_ID["X"]

    def __call__(self, s, add_special_tokens=False, return_offsets_mapping=False):
        ids, offs, i = [], [], 0
        while i < len(s):
            for L in range(min(12, len(s) - i), 0, -1):
                if s[i:i + L] in PIECE_ID:
                    ids.append(PIECE_ID[s[i:i + L]])
                    offs.append((i, i + L))
                    i += L
                    break
            else:
                ids.append(PIECE_ID["X"])
                offs.append((i, i + 1))
                i += 1
        out = {"input_ids": ids}
        if return_offsets_mapping:
            out["offset_mapping"] = offs
        return out

    def decode(self, ids):
        return "".join(PIECES[int(i)] for i in ids)


class _Out:
    def __init__(self, logits):
        self.logits = logits


class FakeModel:
    device = "cpu"

    def __init__(self, last_logits):
        self._last = torch.tensor(last_logits, dtype=torch.float32)

    def __call__(self, input_ids=None, attention_mask=None, use_cache=False):
        b, t = input_ids.shape
        lg = torch.full((b, t, VOCAB), -20.0)
        lg[:, -1, :] = self._last
        return _Out(lg)


class FakeLM:
    def __init__(self, last_logits):
        self.tokenizer = FakeTok()
        self.model = FakeModel(last_logits)


@pytest.fixture
def tok():
    return FakeTok()


# --------------------------------------------------------------------------- #
# 1. Option-set construction
# --------------------------------------------------------------------------- #
def test_option_set_is_intended_plus_literal_plus_other_concepts():
    w = sbp.option_words("carrot", "bomb", ("bomb", "knife", "gun", "club"))
    assert list(w) == ["concept", "codeword_literal", "other_knife", "other_gun", "other_club"]
    assert w["concept"] == "bomb" and w["codeword_literal"] == "carrot"
    # the intended concept is never ALSO a distractor, however the pool is written
    assert sum(1 for v in w.values() if v == "bomb") == 1


def test_option_set_order_is_stable_and_extras_append():
    a = sbp.option_words("carrot", "bomb", ("club", "gun", "knife", "bomb"), extra=("tulip",))
    assert list(a) == ["concept", "codeword_literal", "other_club", "other_gun", "other_knife",
                       "extra_tulip"]
    assert sbp.option_words("carrot", "bomb") == sbp.option_words("carrot", "bomb")


def test_option_set_refuses_degenerate_inputs():
    with pytest.raises(sbp.ProbeSetError):
        sbp.option_words("bomb", "bomb")                       # literal == mapped reading
    with pytest.raises(sbp.ProbeSetError):
        sbp.option_words("", "bomb")
    with pytest.raises(sbp.ProbeSetError):
        sbp.option_words("carrot", "bomb", ("bomb",))          # no distractor concept left


def test_answer_variants_are_built_identically_for_every_option():
    v = sbp.option_answer_variants(sbp.option_words("carrot", "bomb"))
    assert len({len(x) for x in v.values()}) == 1, "asymmetric variant counts bias logsumexp"


# --------------------------------------------------------------------------- #
# 2. The single-token refusal
# --------------------------------------------------------------------------- #
def test_multi_token_option_is_refused_loudly_and_names_the_option(tok):
    words = sbp.option_words("carrot", "grenade", ("grenade", "bomb", "knife"))
    with pytest.raises(sbp.ProbeSetError) as e:
        sbp.validate_option_tokens(tok, words)
    msg = str(e.value)
    assert "concept" in msg and "grenade" in msg


def test_naive_first_subtoken_ids_accept_what_the_gate_refuses(tok):
    """RED/GREEN: the naive id construction returns ids for the very option set the gate rejects."""
    words = sbp.option_words("carrot", "grenade", ("grenade", "bomb", "knife"))
    naive = {n: [tok(" " + w)["input_ids"][0]] for n, w in words.items()}
    assert all(len(v) == 1 for v in naive.values())               # naive: no complaint at all
    assert tok.decode(naive["concept"]).strip() != "grenade"      # ... and it is a FIRST SUBTOKEN
    with pytest.raises(sbp.ProbeSetError):
        sbp.validate_option_tokens(tok, words)


def test_valid_option_set_passes_and_yields_one_id_per_option(tok):
    words = sbp.option_words("carrot", "bomb")
    meta = sbp.validate_option_tokens(tok, words)
    groups = sbp.option_id_groups(meta)
    assert set(groups) == set(words)
    assert all(len(v) == 1 for v in groups.values()), "arms must be exactly symmetric"
    assert len({v[0] for v in groups.values()}) == len(groups), "ids must be disjoint"
    assert groups["concept"] == [PIECE_ID[" bomb"]]
    assert groups["codeword_literal"] == [PIECE_ID[" carrot"]]


def test_options_sharing_a_readout_id_are_refused(tok):
    with pytest.raises(sbp.ProbeSetError) as e:
        sbp.validate_option_tokens(tok, {"concept": "bomb", "codeword_literal": "carrot",
                                         "other_dup": "bomb"})
    assert "share readout id" in str(e.value)


# --------------------------------------------------------------------------- #
# 3. Margin arithmetic on hand-built logits, through the REAL readout
# --------------------------------------------------------------------------- #
def _readout(tok, last_logits, answer_prefix="Answer:"):
    words = sbp.option_words("carrot", "bomb")
    meta = sbp.validate_option_tokens(tok, words)
    groups = sbp.option_id_groups(meta)
    lm = FakeLM(last_logits)
    r = sb.next_token_readout(lm, "X", groups, answer_prefix=answer_prefix)
    return words, meta, groups, r


def _logits(**by_word):
    """Hand-built next-token logits. Everything that is not an option sits on 'X' with a LARGE
    logit, so `option_mass` stays realistically small — the condition score_behavior records
    because a margin inside a 1e-5 tail is an ordering, not a decision."""
    v = [-30.0] * VOCAB
    v[PIECE_ID["X"]] = 12.0
    for w, x in by_word.items():
        v[PIECE_ID[" " + w]] = x
    return v


def test_margins_equal_raw_logit_differences(tok):
    words, meta, groups, r = _readout(tok, _logits(bomb=5.0, carrot=2.0, knife=1.0,
                                                   gun=0.5, club=0.25))
    m = sbp.margins(r, list(words))
    assert m["margin_vs_codeword_literal"] == pytest.approx(3.0, abs=1e-4)
    assert m["margin_vs_best_distractor"] == pytest.approx(3.0, abs=1e-4)
    assert m["best_distractor"] == "codeword_literal"
    assert m["margin_vs_best_other_concept"] == pytest.approx(4.0, abs=1e-4)
    assert m["best_other_concept"] == "other_knife"
    assert m["forced_choice_correct"] is True and m["argmax_tie"] is False
    assert m["n_options"] == 5


def test_p_intended_within_options_renormalises_over_the_option_set(tok):
    vals = dict(bomb=5.0, carrot=2.0, knife=1.0, gun=0.5, club=0.25)
    words, meta, groups, r = _readout(tok, _logits(**vals))
    m = sbp.margins(r, list(words))
    expect = float(torch.softmax(torch.tensor(list(vals.values())), 0)[0])
    assert m["p_intended_within_options"] == pytest.approx(expect, rel=1e-5)
    # and it is NOT the raw next-token probability: option_mass is far below 1
    assert r["option_mass"] < 1.0
    assert m["p_intended_within_options"] > r["p_concept"]


def test_margin_goes_negative_when_the_literal_reading_wins(tok):
    words, meta, groups, r = _readout(tok, _logits(bomb=1.0, carrot=9.0, knife=0.0,
                                                   gun=0.0, club=0.0))
    m = sbp.margins(r, list(words))
    assert m["margin_vs_codeword_literal"] == pytest.approx(-8.0, abs=1e-4)
    assert m["argmax_option"] == "codeword_literal"
    assert m["forced_choice_correct"] is False


def test_an_exact_tie_is_not_a_forced_choice_win(tok):
    """RED/GREEN: `max(lp, key=lp.get)` hands the win to whichever option the dict lists first."""
    words, meta, groups, r = _readout(tok, _logits(bomb=3.0, carrot=3.0, knife=0.0,
                                                   gun=0.0, club=0.0))
    lp = {n: r[f"logp_{n}"] for n in words}
    assert max(lp, key=lp.get) == "concept"            # naive: a tie scores as success
    m = sbp.margins(r, list(words))
    assert m["argmax_tie"] is True
    assert m["forced_choice_correct"] is False
    assert m["margin_vs_best_distractor"] == pytest.approx(0.0, abs=1e-5)


def test_margins_refuse_a_partial_option_set(tok):
    words, meta, groups, r = _readout(tok, _logits(bomb=1.0, carrot=0.0))
    with pytest.raises(sbp.ProbeSetError):
        sbp.margins(r, list(words) + ["other_missing"])
    with pytest.raises(sbp.ProbeSetError):
        sbp.margins(r, ["codeword_literal", "other_knife"])      # intended absent


# --------------------------------------------------------------------------- #
# 4. Exact one-word scoring
# --------------------------------------------------------------------------- #
def test_exact_match_accepts_every_whole_word_spelling(tok):
    meta = sbp.validate_option_tokens(tok, sbp.option_words("carrot", "bomb"))
    for piece in (" bomb", "bomb", " Bomb", "Bomb"):
        assert sbp.exact_one_word(meta["concept"], PIECE_ID[piece]) is True


def test_naive_primary_id_match_misses_the_models_preferred_spelling(tok):
    """RED/GREEN: the model's argmax is ' Bomb'; a primary-id equality test calls that a miss."""
    meta = sbp.validate_option_tokens(tok, sbp.option_words("carrot", "bomb"))
    top1 = PIECE_ID[" Bomb"]
    assert (top1 == meta["concept"]["primary_id"]) is False      # naive verdict: wrong
    assert sbp.exact_one_word(meta["concept"], top1) is True     # ours: right


def test_exact_match_rejects_a_first_subtoken_and_other_options(tok):
    meta = sbp.validate_option_tokens(tok, sbp.option_words("carrot", "bomb"))
    assert sbp.exact_one_word(meta["concept"], PIECE_ID[" Car"]) is False
    assert sbp.exact_one_word(meta["concept"], PIECE_ID[" carrot"]) is False
    assert sbp.option_of_top1(meta, PIECE_ID[" Car"]) is None     # a subtoken is nobody's answer
    assert sbp.option_of_top1(meta, PIECE_ID[" carrot"]) == "codeword_literal"
    assert sbp.option_of_top1(meta, PIECE_ID[" knife"]) == "other_knife"


def test_unmeasured_top1_is_none_not_false(tok):
    meta = sbp.validate_option_tokens(tok, sbp.option_words("carrot", "bomb"))
    assert sbp.exact_one_word(meta["concept"], None) is None
    assert sbp.option_of_top1(meta, None) is None


# --------------------------------------------------------------------------- #
# 5. Pairing and the failure ledger
# --------------------------------------------------------------------------- #
def _row(kind, cond="natural_doublespeak", stem="d|dev|slot0|n4|none|consistent|near|plain",
         demo="DEMO-BLOCK-1", pid=None, **kw):
    r = {"prompt_id": pid or f"{kind}-{cond}-{stem}", "prompt_sha16": "0" * 16,
         "family_id": f"{stem}|{kind}", "query_kind": kind, "condition": cond,
         "demo_block": demo, "codeword": "carrot", "concept": "bomb",
         "target_surface": "carrot", "target_semantic": "bomb", "split": "dev",
         "cell": "C", "domain": "d", "n_examples": 4, "full_prompt": "PROMPT"}
    r.update(kw)
    return r


def test_missing_demo_block_is_a_ledger_failure_not_a_silent_drop():
    probe = _row("semantic_one_word")
    del probe["demo_block"]
    rows = [_row("behavioral"), probe]
    led = FailureLedger()
    pairs = sbp.build_probe_set(rows, ("semantic_one_word",), ledger=led)
    assert pairs == []
    assert led.attempted == 1 and led.succeeded == 0
    assert led.failures == {"missing_demo_block": 1}
    assert led.as_dict()["failure_example_ids"]["missing_demo_block"] == [probe["prompt_id"]]


def test_empty_demo_block_is_charged_because_the_probe_is_unanswerable():
    rows = [_row("behavioral", demo="   "), _row("semantic_one_word", demo="   ")]
    led = FailureLedger()
    assert sbp.build_probe_set(rows, ("semantic_one_word",), ledger=led) == []
    assert led.failures == {"empty_demo_block": 1}
    led2 = FailureLedger()
    kept = sbp.build_probe_set(rows, ("semantic_one_word",), ledger=led2, require_demos=False)
    assert len(kept) == 1 and led2.n_failed == 0


def test_demo_block_mismatch_is_charged_because_the_pair_is_not_matched():
    rows = [_row("behavioral", demo="DEMO-BLOCK-1"),
            _row("semantic_one_word", demo="DEMO-BLOCK-2")]
    led = FailureLedger()
    assert sbp.build_probe_set(rows, ("semantic_one_word",), ledger=led) == []
    assert led.failures == {"demo_block_mismatch": 1}


def test_probe_without_a_behavioural_twin_is_charged():
    led = FailureLedger()
    assert sbp.build_probe_set([_row("semantic_one_word")], ("semantic_one_word",),
                               ledger=led) == []
    assert led.failures == {"no_behavioral_partner": 1}


def test_naive_filter_pairing_loses_rows_without_saying_so():
    """RED/GREEN: the obvious comprehension drops all three defective rows and reports nothing."""
    rows = [_row("behavioral"),
            _row("semantic_one_word", pid="p_ok"),
            _row("semantic_one_word", demo="   ", pid="p_empty"),
            _row("semantic_one_word", demo="OTHER", pid="p_mismatch"),
            _row("semantic_one_word", cond="benign_literal", pid="p_orphan")]
    naive = [r for r in rows
             if r["query_kind"] == "semantic_one_word" and (r.get("demo_block") or "").strip()]
    assert len(naive) == 3                       # naive: 3 rows out, no statement of the loss
    led = FailureLedger()
    kept = sbp.build_probe_set(rows, ("semantic_one_word",), ledger=led)
    assert len(kept) == 1
    assert led.n_failed == 3
    assert len(kept) + led.n_failed == len(sbp.probe_rows(rows, ("semantic_one_word",)))
    assert set(led.failures) == {"empty_demo_block", "demo_block_mismatch",
                                 "no_behavioral_partner"}


def test_family_stem_refuses_a_family_id_that_does_not_end_in_the_query_kind():
    bad = _row("semantic_one_word")
    bad["family_id"] = "d|dev|slot0|n4|none|consistent|near|plain|behavioral"
    with pytest.raises(sbp.ProbeSetError):
        sbp.family_stem(bad)


def test_ambiguous_behavioural_twin_is_refused_not_arbitrarily_chosen():
    rows = [_row("behavioral", pid="b1"), _row("behavioral", pid="b2")]
    with pytest.raises(sbp.ProbeSetError):
        sbp.build_probe_set(rows, ("semantic_one_word",), ledger=FailureLedger())


def test_pairing_carries_the_identity_needed_for_a_matched_intervention():
    rows = [_row("behavioral", pid="b"), _row("semantic_one_word", pid="s")]
    pairs = sbp.build_probe_set(rows, ("semantic_one_word",), ledger=FailureLedger())
    rec = sbp.probe_record(pairs[0], sbp.option_words("carrot", "bomb"),
                           {"concept": [1]}, arm="base")
    assert rec["probe_prompt_id"] == "s" and rec["behavioral_prompt_id"] == "b"
    assert rec["demo_block_sha16"] == pairs[0]["demo_sha16"]
    assert rec["probe_tests_binding"] is True
    # a probe that asks about the concept word ITSELF tests no binding and must say so
    rows2 = [_row("behavioral", pid="b2"),
             _row("semantic_one_word", pid="s2", target_surface="bomb")]
    p2 = sbp.build_probe_set(rows2, ("semantic_one_word",), ledger=FailureLedger())[0]
    assert sbp.probe_record(p2, sbp.option_words("carrot", "bomb"), {}, "base"
                            )["probe_tests_binding"] is False


# --------------------------------------------------------------------------- #
# 6. The committed bank: every probe row is accounted for
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not os.path.exists(REAL_BANK), reason="committed bank not present")
def test_every_probe_row_of_the_committed_bank_is_paired_or_charged():
    rows = [json.loads(l) for l in open(REAL_BANK)]
    n_probe = sum(1 for r in rows if r.get("query_kind") in sbp.PROBE_KINDS)
    assert len(sbp.probe_rows(rows, sbp.PROBE_KINDS)) == n_probe
    led = FailureLedger()
    pairs = sbp.build_probe_set(rows, sbp.PROBE_KINDS, ledger=led)
    assert led.n_failed + len(pairs) == n_probe, "a probe row was neither paired nor charged"
    assert pairs, "the committed bank must yield probe pairs"
    assert set(led.failures) <= {"empty_demo_block"}, led.failures
    assert all(p["demo_sha16"] == sbp.demo_sha16(p["behavioral"]) for p in pairs)
    assert all(p["probe"]["condition"] == p["behavioral"]["condition"] for p in pairs)
    assert len({p["probe"]["prompt_id"] for p in pairs}) == len(pairs)


# --------------------------------------------------------------------------- #
# 7. main(): artifact through the RunDir / FailureLedger contract
# --------------------------------------------------------------------------- #
def _tiny_bank(path):
    rows = []
    for i, cond in enumerate(("natural_doublespeak", "benign_literal")):
        stem = f"d{i}|dev|slot0|n4|none|consistent|near|plain"
        rows.append(_row("behavioral", cond=cond, stem=stem, pid=f"b{i}"))
        rows.append(_row("semantic_one_word", cond=cond, stem=stem, pid=f"s{i}"))
    # one probe whose demonstrations are empty -> must appear in the ledger, not vanish
    stem = "d9|dev|slot0|n0|none|consistent|near|plain"
    rows.append(_row("behavioral", stem=stem, demo="", pid="b9"))
    rows.append(_row("semantic_one_word", stem=stem, demo="", pid="s9"))
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return path


def test_main_dry_run_writes_a_ledgered_artifact(tmp_path):
    bank = _tiny_bank(str(tmp_path / "bank.jsonl"))
    rc = sbp.main(["--bank", bank, "--dry-run", "--allow-untokenized",
                   "--probe-kinds", "semantic_one_word",
                   "--out-root", str(tmp_path / "out"), "--tag", "t"])
    assert rc == 0
    runs = list((tmp_path / "out" / "semantic_binding_probe").iterdir())
    assert len(runs) == 1
    run = runs[0]
    res = [json.loads(l) for l in open(run / "results.jsonl")]
    assert len(res) == 2
    assert {r["probe_prompt_id"] for r in res} == {"s0", "s1"}
    assert all(r["behavioral_prompt_id"].startswith("b") for r in res)
    assert all(r["single_token_validated"] is False for r in res)   # no tokenizer was given
    summ = json.load(open(run / "summary.json"))
    assert summ["failures"]["n_attempted"] == 3
    assert summ["failures"]["failure_reasons"] == {"empty_demo_block": 1}
    assert summ["failures"]["n_succeeded"] == 2 and summ["n_result_rows"] == 2
    assert summ["by_group"]["ALL"]["n"] == 2
    assert summ["dry_run"] is True and summ["single_token_validated"] is False
    assert os.path.exists(run / "DONE.json") and os.path.exists(run / "metadata.json")
    meta = json.load(open(run / "metadata.json"))
    assert meta["bank_file_sha16"] and meta["n_pairs"] == 2


def test_main_dry_run_without_a_tokenizer_refuses_by_default(tmp_path):
    bank = _tiny_bank(str(tmp_path / "bank.jsonl"))
    with pytest.raises(SystemExit):
        sbp.main(["--bank", bank, "--dry-run", "--probe-kinds", "semantic_one_word",
                  "--out-root", str(tmp_path / "out2"), "--tag", "t"])
    run = list((tmp_path / "out2" / "semantic_binding_probe").iterdir())[0]
    assert os.path.exists(run / "ABORTED.json")
    assert not os.path.exists(run / "DONE.json")


def test_main_rejects_an_unknown_probe_kind(tmp_path):
    bank = _tiny_bank(str(tmp_path / "bank.jsonl"))
    with pytest.raises(SystemExit):
        sbp.main(["--bank", bank, "--dry-run", "--allow-untokenized",
                  "--probe-kinds", "goal_topicality",
                  "--out-root", str(tmp_path / "out3"), "--tag", "t"])


def test_limit_truncates_before_pairing_so_the_counts_still_add_up():
    rows = [_row("behavioral", pid="b"), _row("semantic_one_word", pid="p_ok"),
            _row("semantic_one_word", demo="   ", pid="p_empty",
                 stem="d2|dev|slot0|n0|none|consistent|near|plain"),
            _row("behavioral", demo="   ", pid="b2",
                 stem="d2|dev|slot0|n0|none|consistent|near|plain")]
    cand = sbp.probe_rows(rows, ("semantic_one_word",), limit=1)
    assert len(cand) == 1
    led = FailureLedger()
    pairs = sbp.build_probe_set(rows, ("semantic_one_word",), ledger=led, limit=1)
    assert len(pairs) + led.n_failed == len(cand)


# --------------------------------------------------------------------------- #
# 8. score_pair: the measurement half, driven by hand-built logits
# --------------------------------------------------------------------------- #
class _FakeDS:
    @staticmethod
    def apply_template(tokenizer, prompt, enable_thinking=None):
        return prompt


def test_score_pair_reports_margins_exact_match_and_the_demo_span(monkeypatch, tok):
    monkeypatch.setattr(sbp, "ds", lambda: _FakeDS)
    rows = [_row("behavioral", pid="b", full_prompt="DEMO-BLOCK-1 X"),
            _row("semantic_one_word", pid="s", full_prompt="DEMO-BLOCK-1 X")]
    pair = sbp.build_probe_set(rows, ("semantic_one_word",), ledger=FailureLedger())[0]
    words = sbp.option_words("carrot", "bomb")
    meta = sbp.validate_option_tokens(tok, words)
    groups = sbp.option_id_groups(meta)
    lm = FakeLM(_logits(bomb=5.0, carrot=2.0, knife=1.0, gun=0.5, club=0.25))
    lm.tokenizer = tok
    out = sbp.score_pair(lm, pair, meta, words, groups, readout="primary")
    assert out["n_demo_key_positions"] > 0
    assert out["primary_margin_vs_codeword_literal"] == pytest.approx(3.0, abs=1e-4)
    assert out["primary_forced_choice_correct"] is True
    assert out["exact_one_word_correct"] is False       # the argmax token is not the concept
    assert out["top1_option"] is None
    assert out["option_mass"] < 0.01                    # the honest tail warning is recorded


def test_score_pair_refuses_a_row_whose_demo_block_is_not_in_the_prompt(monkeypatch, tok):
    monkeypatch.setattr(sbp, "ds", lambda: _FakeDS)
    rows = [_row("behavioral", pid="b", full_prompt="X"),
            _row("semantic_one_word", pid="s", full_prompt="X")]
    pair = sbp.build_probe_set(rows, ("semantic_one_word",), ledger=FailureLedger())[0]
    words = sbp.option_words("carrot", "bomb")
    meta = sbp.validate_option_tokens(tok, words)
    lm = FakeLM(_logits(bomb=1.0))
    lm.tokenizer = tok
    with pytest.raises(sbp.ProbeSetError) as e:
        sbp.score_pair(lm, pair, meta, words, sbp.option_id_groups(meta), readout="primary")
    assert "demo_span_" in str(e.value)
