#!/usr/bin/env python3
"""Per-example, end-relative anchor-position location for the CSI codeword / axis sites.

WHY THIS EXISTS. Heretic's ARA captures module I/O at the LAST prefill position
(`model.py:665-666`, `[:, -1, :]`). Our strongest causal site is the *codeword row* (end-relative
offset -10) and the axis site (-6) in the query, NOT the last token. This module locates those
positions per example so a position-aware ARA plugin can anchor its objective there.

PROVENANCE (reused convention, not reinvented). The end-relative convention
    absolute_position = len(input_ids) + rel_end            (rel_end < 0)
and the finding that ABSOLUTE indices are VOID -- a frozen absolute index matches the intended token
in only 0/2300 triples, spread 9.36 +/- 5.90 tokens -- are from
`src/boombness/score_behavior.py` (`parse_rel_end_rows`, `surface_span_from_rel_end`,
`rel_end_of_positions`, and the `token_map._absolute_indices_are_void` note). Constants: codeword row
rel_end=-10, axis site rel_end=-6 (SUMMARY_2026-09-02_TO_09-26.md §12). This module re-expresses that
convention for the Heretic env and adds a LOUD codeword-decode self-check, because the plan requires:
"Fail loudly if token selection is ambiguous."

This module depends only on a HuggingFace tokenizer; it is env-agnostic (works in both poc_stage2 and
heretic_csi) and needs no GPU.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Optional, Sequence, Dict, Any

# CSI frozen end-relative sites (SUMMARY §12 / §1.2).
REL_END_CODEWORD_ROW = -10
REL_END_AXIS_SITE = -6


class AmbiguousPosition(Exception):
    """Raised when the intended anchor token cannot be identified unambiguously."""


@dataclass
class AnchorInfo:
    """Full provenance for one example's anchor (plan §7: save all of this)."""
    rel_end: int
    abs_pos: int                 # position in the UNPADDED input_ids
    seq_len: int                 # unpadded length
    token_id: int
    decoded_token: str
    codeword: str
    codeword_primary_id: int
    codeword_is_single_token: bool
    matches_codeword: bool
    abs_pos_padded: Optional[int] = None   # position in the left-padded batch row, if applicable
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def leading_space_id(tokenizer, word: str) -> int:
    """The single-token id of ' word' (leading space), enforcing single-token.

    Mirrors signals.readout_ids' primary_id: the space-prefixed form is the one that appears after
    'Answer:' and inside running text. Raises if ' word' is not a single token (then a logit-lens /
    position readout on it is ill-defined and the caller must decide explicitly).
    """
    ids = tokenizer(" " + word, add_special_tokens=False)["input_ids"]
    if len(ids) != 1:
        raise AmbiguousPosition(
            f"' {word}' tokenizes to {len(ids)} tokens "
            f"{[tokenizer.decode([i]) for i in ids]}, not 1 -- decide explicitly how to score a "
            f"multi-token codeword before using it as an anchor.")
    return ids[0]


def rel_end_to_abs(rel_end: int, seq_len: int) -> int:
    """pos = seq_len + rel_end, with bounds checking (reused convention, score_behavior.py:380)."""
    if rel_end >= 0:
        raise ValueError(f"rel_end must be negative (end-relative); got {rel_end}")
    pos = seq_len + rel_end
    if not (0 <= pos < seq_len):
        raise ValueError(f"rel_end {rel_end} resolves to position {pos} outside sequence length {seq_len}")
    return pos


def _as_id_list(input_ids) -> List[int]:
    try:
        import torch
        if isinstance(input_ids, torch.Tensor):
            if input_ids.dim() != 1:
                raise ValueError(f"expected 1-D input_ids, got shape {tuple(input_ids.shape)}")
            return [int(x) for x in input_ids.tolist()]
    except ImportError:
        pass
    return [int(x) for x in input_ids]


def anchor_from_rel_end(
    input_ids,
    tokenizer,
    codeword: str,
    rel_end: int = REL_END_CODEWORD_ROW,
    *,
    require_codeword_match: bool = True,
) -> AnchorInfo:
    """Resolve an end-relative anchor and LOUDLY self-validate it.

    input_ids: 1-D UNPADDED ids for one example (list or 1-D tensor).
    require_codeword_match: when True (the default for the codeword row), the decoded token at the
      resolved position MUST equal the codeword (case/space-insensitive) or AmbiguousPosition is
      raised -- this is the self-check that catches a mis-templated prompt or an off-by-one.
    """
    ids = _as_id_list(input_ids)
    seq_len = len(ids)
    abs_pos = rel_end_to_abs(rel_end, seq_len)
    tok_id = ids[abs_pos]
    decoded = tokenizer.decode([tok_id])
    # codeword single-token check (independent of position)
    try:
        prim = leading_space_id(tokenizer, codeword)
        single = True
    except AmbiguousPosition:
        prim = -1
        single = False
    matches = decoded.strip().casefold() == codeword.casefold()
    if require_codeword_match and not matches:
        raise AmbiguousPosition(
            f"codeword-row self-check FAILED: rel_end={rel_end} -> abs_pos={abs_pos} "
            f"(seq_len={seq_len}) decodes to {decoded!r} (id {tok_id}), not codeword {codeword!r}. "
            f"Refusing to anchor on a wrong token.")
    return AnchorInfo(
        rel_end=rel_end, abs_pos=abs_pos, seq_len=seq_len, token_id=tok_id,
        decoded_token=decoded, codeword=codeword, codeword_primary_id=prim,
        codeword_is_single_token=single, matches_codeword=matches,
        note="require_codeword_match" if require_codeword_match else "no-match-required (e.g. axis site)",
    )


def find_codeword_positions(input_ids, tokenizer, codeword: str) -> List[int]:
    """All positions whose id equals the leading-space codeword id (a robustness locator).

    Independent of the end-relative constant: used to CROSS-CHECK rel_end=-10 against where the
    codeword token actually sits, and to flag ambiguity (multiple query-side occurrences).
    """
    ids = _as_id_list(input_ids)
    prim = leading_space_id(tokenizer, codeword)
    return [i for i, t in enumerate(ids) if t == prim]


def anchor_in_padded_row(
    padded_ids,
    attention_mask,
    tokenizer,
    codeword: str,
    rel_end: int = REL_END_CODEWORD_ROW,
    *,
    require_codeword_match: bool = True,
) -> AnchorInfo:
    """Resolve the anchor for ONE row of a LEFT-padded batch (Heretic forces left padding).

    With left padding, the real tokens occupy the LAST `unpadded_len` positions. We locate the
    anchor on the unpadded ids, then shift by the pad length to get the padded index. Fails loudly
    if the mask is right-padded (interior gaps) rather than left-padded.
    """
    ids = _as_id_list(padded_ids)
    mask = _as_id_list(attention_mask)
    if len(ids) != len(mask):
        raise ValueError(f"ids/mask length mismatch: {len(ids)} vs {len(mask)}")
    n = sum(1 for m in mask if m)
    pad_len = len(ids) - n
    # verify LEFT padding: all pad positions are the first (len-n), all real tokens are last n
    if any(mask[i] for i in range(pad_len)) or not all(mask[i] for i in range(pad_len, len(ids))):
        raise AmbiguousPosition(
            "attention_mask is not cleanly LEFT-padded; refusing to compute a padded anchor "
            "(Heretic uses left padding -- a right-padded or interior-gap mask means a bug upstream).")
    real_ids = ids[pad_len:]
    info = anchor_from_rel_end(real_ids, tokenizer, codeword, rel_end,
                               require_codeword_match=require_codeword_match)
    info.abs_pos_padded = info.abs_pos + pad_len
    return info
