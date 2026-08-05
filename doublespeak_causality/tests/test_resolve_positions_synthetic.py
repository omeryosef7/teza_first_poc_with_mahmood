"""
GPU-free synthetic tests for pair_common.resolve_positions (plan §P0 / §0.9 — untested
primitives). No model, no tokenizer download, no GPU, deterministic.

resolve_positions has TWO paths and only the first is exercised by the model-backed tests
in tests/test_localization.py (which skip when the tokenizer is not downloaded):

  * STRICT path   — ds_common.find_word_occurrences (token-id matching over the
                    standalone + carrier-derived tokenization variants);
  * FALLBACK path — ds_common.find_word_occurrences_in_text (character-offset matching),
                    taken ONLY when the strict finder raised ValueError.

Both are driven here by a tiny deterministic greedy longest-match ToyTokenizer with real
character offsets, so the two paths can be forced independently and their token indices
checked exactly. The fallback vocab reproduces the DeepSeek-shaped failure documented in
ds_common: the codeword's first character is FUSED into the preceding token ("a z" +
"ebra"), so no standalone variant matches and only offsets can localize it.

Asserts:
  (a) strict path: codeword_all / codeword_last / following / final_prompt / seq_len;
  (b) multi-token words: codeword_last is the LAST subtoken, not the first;
  (c) multiple occurrences: codeword_all lists all of them, codeword_last is the LAST;
  (d) `following` is None when the codeword ends the prompt; final_prompt == seq_len-1;
  (e) fallback path: strict really raises, the fallback resolves, and codeword_last still
      ends the word (while first_idx points at the fused token — documented);
  (f) a word that is absent raises ValueError out of BOTH paths (never silently wrong);
  (g) PairPositions.get / as_dict, including first_generated == final_prompt;
  (h) XFAIL (defect found here): the SLOW-tokenizer branch of the fallback (offsets
      rebuilt by cumulative decoding) is dead code — ds_common.py:468 dereferences an
      unbound `enc` and raises UnboundLocalError. See the xfail reason string.

Run:  python -m pytest doublespeak_causality/tests/test_resolve_positions_synthetic.py -q
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import ds_common as dc  # noqa: E402
from pair_common import resolve_positions  # noqa: E402


# --------------------------------------------------------------------------- #
# Toy tokenizer: greedy longest-match over an explicit vocab, exact offsets.
# Mimics the small slice of the HF tokenizer API that ds_common actually uses:
#   tok(text, add_special_tokens=..., return_offsets_mapping=...) -> dict
#   tok.encode(text, add_special_tokens=False) -> List[int]
#   tok.decode(ids, skip_special_tokens=...) -> str
# --------------------------------------------------------------------------- #
class ToyTokenizer:
    def __init__(self, vocab):
        self.pieces = sorted(set(vocab), key=len, reverse=True)
        self._ids = {}
        self._inv = {}
        for p in sorted(set(vocab)):
            self._id_of(p)

    def _id_of(self, piece):
        if piece not in self._ids:
            i = 100 + len(self._ids)
            self._ids[piece] = i
            self._inv[i] = piece
        return self._ids[piece]

    def _segment(self, text):
        out, i = [], 0
        while i < len(text):
            for p in self.pieces:
                if p and text.startswith(p, i):
                    out.append((p, i, i + len(p)))
                    i += len(p)
                    break
            else:                                   # unknown char -> its own token
                out.append((text[i], i, i + 1))
                i += 1
        return out

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False,
                 **kw):
        seg = self._segment(text)
        out = {"input_ids": [self._id_of(p) for p, _, _ in seg]}
        if return_offsets_mapping:
            out["offset_mapping"] = [(a, b) for _, a, b in seg]
        return out

    def encode(self, text, add_special_tokens=False, **kw):
        return self(text)["input_ids"]

    def decode(self, ids, skip_special_tokens=False):
        if isinstance(ids, int):
            ids = [ids]
        return "".join(self._inv[int(i)] for i in ids)


class ToyLM:
    """resolve_positions only touches lm.tokenizer."""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer


# vocab where " carrot" is a single token both standalone and in context -> STRICT path
STRICT_VOCAB = ["Alice", " ate", " a", " carrot", " today", "carrot", "The", " ", ".",
                "\n", ",", "(", ")"]
# multi-subtoken word -> STRICT path, last_idx must be the FINAL subtoken
MULTI_VOCAB = ["A", " tale", " of", " defe", "nes", "tration", "defe", " today", " ", ".",
               "\n", ",", "(", ")"]
# DeepSeek-shaped fusion: "a z" | "ebra" in context, but " zebra"/"zebra" standalone
# -> strict id matching CANNOT find it, only character offsets can -> FALLBACK path
FUSED_VOCAB = ["The", " saw", "a z", "ebra", " here", " zebra", "zebra", " ", ".", "\n",
               ",", "(", ")"]


# --------------------------------------------------------------------------- #
# toy-tokenizer sanity (a broken fixture would make every assertion below vacuous)
# --------------------------------------------------------------------------- #
def test_toy_tokenizer_offsets_are_exact_and_roundtrip():
    tok = ToyTokenizer(STRICT_VOCAB)
    text = "Alice ate a carrot today"
    enc = tok(text, return_offsets_mapping=True)
    assert tok.decode(enc["input_ids"]) == text
    for i, (a, b) in enumerate(enc["offset_mapping"]):
        assert tok.decode([enc["input_ids"][i]]) == text[a:b]
    assert dc._offsets_are_sane(enc["offset_mapping"], len(text))


# --------------------------------------------------------------------------- #
# (a)-(d) STRICT id-matching path
# --------------------------------------------------------------------------- #
def test_strict_path_single_occurrence():
    tok = ToyTokenizer(STRICT_VOCAB)
    lm = ToyLM(tok)
    text = "Alice ate a carrot today"
    ids = tok(text)["input_ids"]
    assert len(ids) == 5, tok.decode(ids)
    pos = resolve_positions(lm, text, "carrot")
    assert pos.codeword_all == [3], pos.codeword_all
    assert pos.codeword_last == 3
    assert pos.following == 4, "the token right after the codeword"
    assert pos.final_prompt == 4 and pos.seq_len == 5
    assert tok.decode([ids[pos.codeword_last]]).strip() == "carrot"


def test_strict_path_is_used_not_the_fallback():
    """Guard the branch: the strict finder must SUCCEED here (else the test above would
    silently be testing the offset fallback instead)."""
    tok = ToyTokenizer(STRICT_VOCAB)
    ids = tok("Alice ate a carrot today")["input_ids"]
    hit = dc.find_word_occurrences(tok, ids, "carrot")       # must not raise
    assert hit.last_idx == [3]


def test_strict_path_multi_token_word_last_subtoken():
    tok = ToyTokenizer(MULTI_VOCAB)
    lm = ToyLM(tok)
    text = "A tale of defenestration today"
    ids = tok(text)["input_ids"]
    assert len(ids) == 7, tok.decode(ids)
    hit = dc.find_word_occurrences(tok, ids, "defenestration")
    assert hit.spans == [(3, 6)], hit.spans          # " defe" | "nes" | "tration"
    pos = resolve_positions(lm, text, "defenestration")
    assert pos.codeword_last == 5, "must be the LAST subtoken, not the first"
    assert tok.decode([ids[pos.codeword_last]]) == "tration"
    assert pos.following == 6 and pos.final_prompt == 6 and pos.seq_len == 7


def test_strict_path_multiple_occurrences_last_wins():
    tok = ToyTokenizer(STRICT_VOCAB)
    lm = ToyLM(tok)
    text = "Alice ate a carrot today. The carrot."
    pos = resolve_positions(lm, text, "carrot")
    assert len(pos.codeword_all) == 2, pos.codeword_all
    assert pos.codeword_all == sorted(pos.codeword_all), "occurrences in token order"
    assert pos.codeword_last == pos.codeword_all[-1], "codeword_last is the LAST one"


def test_following_is_none_when_codeword_ends_the_prompt():
    tok = ToyTokenizer(STRICT_VOCAB)
    lm = ToyLM(tok)
    text = "Alice ate a carrot"
    pos = resolve_positions(lm, text, "carrot")
    assert pos.seq_len == 4 and pos.codeword_last == 3
    assert pos.following is None, "no token after the codeword -> following is None"
    assert pos.final_prompt == 3


def test_final_prompt_is_always_last_index():
    tok = ToyTokenizer(STRICT_VOCAB)
    lm = ToyLM(tok)
    for text in ("Alice ate a carrot today", "Alice ate a carrot", "The carrot."):
        pos = resolve_positions(lm, text, "carrot")
        assert pos.final_prompt == pos.seq_len - 1


def test_no_special_tokens_are_added():
    """resolve_positions must tokenize with add_special_tokens=False so indices line up
    with generation (the BOS-doubling bug in PAPER_REPRODUCTION_NOTES)."""
    tok = ToyTokenizer(STRICT_VOCAB)
    lm = ToyLM(tok)
    text = "Alice ate a carrot today"
    pos = resolve_positions(lm, text, "carrot")
    assert pos.seq_len == len(tok(text, add_special_tokens=False)["input_ids"])


# --------------------------------------------------------------------------- #
# (e) FALLBACK offset-finder path
# --------------------------------------------------------------------------- #
def test_strict_path_really_fails_on_the_fused_vocab():
    """Precondition for the fallback test: id matching cannot find the fused codeword."""
    tok = ToyTokenizer(FUSED_VOCAB)
    text = "The saw a zebra here"
    ids = tok(text)["input_ids"]
    assert tok.decode(ids) == text
    assert [tok.decode([i]) for i in ids] == ["The", " saw", " ", "a z", "ebra", " here"]
    with pytest.raises(ValueError):
        dc.find_word_occurrences(tok, ids, "zebra")


def test_fallback_offset_path_resolves_correct_indices():
    tok = ToyTokenizer(FUSED_VOCAB)
    lm = ToyLM(tok)
    text = "The saw a zebra here"
    pos = resolve_positions(lm, text, "zebra")           # must NOT raise
    assert pos.codeword_last == 4, pos.as_dict()
    assert tok.decode([tok(text)["input_ids"][pos.codeword_last]]) == "ebra"
    assert pos.following == 5 and pos.final_prompt == 5 and pos.seq_len == 6


def test_fallback_span_includes_the_fused_leading_token_documented():
    """DOCUMENTED BEHAVIOUR: because the tokenizer fused the preceding character into the
    codeword's first token, the offset span STARTS at that fused token ("a z"). Consumers
    must use `codeword_last` (which correctly ends the word); `codeword_all`/first_idx may
    cover one extra character of context. Same caveat as ds_common's suffix fallback."""
    tok = ToyTokenizer(FUSED_VOCAB)
    hit = dc.find_word_occurrences_in_text(tok, "The saw a zebra here", "zebra",
                                           add_special_tokens=False)
    assert hit.spans == [(3, 5)], hit.spans
    assert tok.decode(hit.subtoken_ids) == "a zebra", "span carries the fused 'a '"
    assert "zebra".endswith(tok.decode([hit.subtoken_ids[-1]]).strip()), \
        "the LAST subtoken still ends the word"


def test_fallback_finds_every_occurrence():
    tok = ToyTokenizer(FUSED_VOCAB)
    lm = ToyLM(tok)
    text = "The saw a zebra here.\nThe saw a zebra here"
    pos = resolve_positions(lm, text, "zebra")
    assert len(pos.codeword_all) == 2, pos.codeword_all
    assert pos.codeword_last == pos.codeword_all[-1]


# --------------------------------------------------------------------------- #
# (f) absent word: loud failure from both paths
# --------------------------------------------------------------------------- #
def test_absent_word_raises_from_strict_and_fallback():
    tok = ToyTokenizer(STRICT_VOCAB)
    lm = ToyLM(tok)
    with pytest.raises(ValueError):
        resolve_positions(lm, "Alice ate a carrot today", "kettle")


def test_substring_inside_a_longer_word_is_not_a_match_in_the_fallback():
    """The offset finder requires a left word boundary, so 'zebra' inside 'wzebra' must
    not resolve (it would silently analyse the wrong token)."""
    tok = ToyTokenizer(FUSED_VOCAB)
    with pytest.raises(ValueError):
        dc.find_word_occurrences_in_text(tok, "The saw wzebra here", "zebra",
                                         add_special_tokens=False)


class NoOffsetToyTokenizer(ToyTokenizer):
    """A SLOW tokenizer: raises TypeError on return_offsets_mapping, like HF slow
    tokenizers. ds_common then rebuilds offsets by cumulative decoding
    (_offsets_by_decode) -- the DeepSeek path."""

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False,
                 **kw):
        if return_offsets_mapping:
            raise TypeError("slow tokenizer: offsets unavailable")
        return super().__call__(text, add_special_tokens=add_special_tokens)


# REGRESSION GUARD (defect found by this test, fixed 2026-08-05).
# find_word_occurrences_in_text ended with a stray `ids = enc["input_ids"]`. When the
# tokenizer cannot supply offsets (slow tokenizers, e.g. DeepSeek) but _offsets_by_decode
# DOES reconstruct them, `enc` is unbound -> UnboundLocalError, killing exactly the branch
# the reconstruction was written for. Worse, when `enc` WAS bound but failed the sanity
# check, its input_ids could differ in length from the ids the spans were computed
# against, silently mis-slicing subtoken_ids. Fix: the line was deleted (ds_common.py).
# This test was xfail(strict=False) until the fix landed.
def test_slow_tokenizer_decode_reconstructed_offsets_path():
    tok = NoOffsetToyTokenizer(FUSED_VOCAB)
    text = "The saw a zebra here"
    # sanity: the decode-based reconstruction itself works
    offs, full = dc._offsets_by_decode(tok, tok(text)["input_ids"], text)
    assert offs is not None and full == text
    hit = dc.find_word_occurrences_in_text(tok, text, "zebra", add_special_tokens=False)
    assert hit.last_idx == [4]


# --------------------------------------------------------------------------- #
# (g) PairPositions accessors
# --------------------------------------------------------------------------- #
def test_pairpositions_get_and_as_dict():
    tok = ToyTokenizer(STRICT_VOCAB)
    lm = ToyLM(tok)
    pos = resolve_positions(lm, "Alice ate a carrot today", "carrot")
    assert pos.get("first_generated") == pos.final_prompt, \
        "the first generated token is produced FROM final_prompt"
    assert pos.get("codeword_last") == pos.codeword_last
    assert pos.get("following") == pos.following
    assert pos.get("nonexistent") is None
    d = pos.as_dict()
    assert set(d) == {"codeword_all", "codeword_last", "following", "final_prompt",
                      "seq_len"}
    assert all(isinstance(v, (int, list)) for v in d.values() if v is not None)


def test_all_positions_are_in_range():
    tok = ToyTokenizer(STRICT_VOCAB)
    lm = ToyLM(tok)
    pos = resolve_positions(lm, "Alice ate a carrot today. The carrot.", "carrot")
    for p in pos.codeword_all + [pos.codeword_last, pos.final_prompt]:
        assert 0 <= p < pos.seq_len, (p, pos.seq_len)
    assert pos.following is None or 0 <= pos.following < pos.seq_len


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
