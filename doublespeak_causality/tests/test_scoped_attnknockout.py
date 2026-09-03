"""
GPU-free synthetic tests for pair_common.ScopedAttentionKnockout — the five-mode QUERY-ROW
decomposition of AllQueryAttentionKnockout.

WHY THIS FILE EXISTS. `AllQueryAttentionKnockout` blocks the demonstration keys from EVERY query
row, so a positive result cannot localise the dependence: the demo tokens' own self-processing,
the final-query rows at prefill and the generated rows at decode are all cut in one edit. The
five modes split that edit. Two consequences are load-bearing and are tested here rather than
assumed:

  1. `legacy_all_query` MUST produce a byte-identical mask to `AllQueryAttentionKnockout` at
     prefill AND at every decode step. That identity is the ONLY bridge between the committed
     all-query knockout artifacts and any scoped number; if it breaks, the scoped modes are being
     compared against a baseline that no longer exists.
  2. `query_prefill_only` and `demo_processing_only` make ZERO decode edits BY DESIGN. The global
     "n_decode_edits == 0 => the run is void" gate that protects the all-query hook would reject
     them as dead hooks. The gate must therefore be per-mode and must read the same table the hook
     is written against (LIVENESS_REQUIREMENT / LIVENESS_MUST_BE_ZERO), which is what
     `scoped_liveness_violations` is for — the tests call the REAL gate, they do not restate it.

The ToyModel / _prefill_mask / _decode_mask / _run harness is imported from
test_allquery_attnknockout rather than re-implemented, and the ~6 properties already covered there
for the all-query hook (sdpa footgun, batch>1, key-beyond-cache, key-set correctness, prefill and
decode liveness) are not repeated per-mode: what is re-tested here is only what the MODE SPLIT can
break — which query rows, which keys, which half of the computation, and the coordinate algebra.

Run:  python -m pytest doublespeak_causality/tests/test_scoped_attnknockout.py -q
"""
import os
import sys

import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pair_common import (  # noqa: E402
    AllQueryAttentionKnockout,
    LIVENESS_MUST_BE_ZERO,
    LIVENESS_REQUIREMENT,
    SCOPED_KNOCKOUT_MODES,
    ScopedAttentionKnockout,
    resolve_scoped_query_rows,
    scoped_liveness_violations,
)
from test_allquery_attnknockout import (  # noqa: E402  (harness reuse, deliberately not re-written)
    MIN,
    ToyModel,
    _decode_mask,
    _prefill_mask,
    _run,
)

# --------------------------------------------------------------------------- #
# One fixed synthetic prompt layout, used by most tests.
#   0,1      chat template / BOS
#   2..5     DEMONSTRATION block
#   6,7      template filler
#   8..11    FINAL-QUERY span (the request + the generation header)
# --------------------------------------------------------------------------- #
SEQ = 12
DEMO = frozenset({2, 3, 4, 5})
QSPAN = frozenset({8, 9, 10, 11})
KEYS = [2, 3]          # a subset of the demo block, so "which keys" is falsifiable
# ONE row inside QSPAN: the final `target_surface` occurrence for `target_surface_row_only`.
# Deliberately NOT the last row of the query span -- if it were, this scope and a "last row"
# bug would be indistinguishable in every test below.
SURFACE = frozenset({9})


def _cells_changed(seen, base):
    """{(head, query_row, key_col)} where the hook actually altered the caller's mask."""
    diff = (seen != base).nonzero()
    return {(int(r[1]), int(r[2]), int(r[3])) for r in diff}


def _rows_changed(seen, base):
    return {q for _h, q, _k in _cells_changed(seen, base)}


def _keys_changed(seen, base):
    return {k for _h, _q, k in _cells_changed(seen, base)}


def _scoped(model, mode, keys=KEYS, layers=(0,), **kw):
    kw.setdefault("query_span", QSPAN)
    kw.setdefault("demo_span", DEMO)
    kw.setdefault("surface_span", SURFACE)
    return ScopedAttentionKnockout(model, list(layers), blocked_keys=list(keys), mode=mode, **kw)


# --------------------------------------------------------------------------- #
# MANDATORY 1 — the bridge to every committed all-query result
# --------------------------------------------------------------------------- #
def test_legacy_mode_is_byte_identical_to_AllQueryAttentionKnockout():
    """Same inputs -> torch.equal masks at prefill and at EVERY decode step, all layers.

    If this goes red, every scoped number is being compared against a baseline that is no longer
    the one the committed knockout artifacts were produced with.
    """
    keys = [2, 3, 5, 99]                      # 99 is beyond the cache: exercises the skip path too
    n_steps = 5

    def _collect(ctx_factory, stats):
        model = ToyModel(n_layers=3, n_heads=4)
        out = []
        with ctx_factory(model, stats):
            out.append([m.clone() for m in _run(model, _prefill_mask(SEQ, heads=1), seq=SEQ)])
            for step in range(n_steps):
                out.append([m.clone() for m in _run(model, _decode_mask(SEQ + step, heads=1), seq=1)])
        return out

    s_old, s_new = {}, {}
    old = _collect(lambda m, s: AllQueryAttentionKnockout(m, [0, 2], blocked_keys=keys, stats=s),
                   s_old)
    new = _collect(lambda m, s: ScopedAttentionKnockout(m, [0, 2], blocked_keys=keys,
                                                        mode="legacy_all_query", stats=s), s_new)
    assert len(old) == len(new) == n_steps + 1
    for step, (a, b) in enumerate(zip(old, new)):
        for li, (ma, mb) in enumerate(zip(a, b)):
            assert (ma is None) == (mb is None), f"step {step} layer {li}: one hook saw no mask"
            if ma is not None:
                assert torch.equal(ma, mb), (
                    f"legacy_all_query diverged from AllQueryAttentionKnockout at step {step}, "
                    f"layer {li}: {int((ma != mb).sum())} cells differ")

    # Stats: every key the OLD class defines must match exactly. The scoped class defines strictly
    # MORE keys (it must, to make a per-mode gate possible); those are listed, not asserted equal.
    overlap = set(s_old) & set(s_new)
    assert overlap == set(s_old), "the scoped class dropped an all-query stats key"
    for k in sorted(overlap):
        assert s_old[k] == s_new[k], f"stats['{k}'] diverged: {s_old[k]} vs {s_new[k]}"
    extra = set(s_new) - set(s_old)
    # UPDATED 2026-09-02 (DCS phase): +n_surface_span_positions, +surface_span_positions for the
    # `target_surface_row_only` scope. Both are pure ARTIFACT fields recording which rows the
    # surgical scope was handed; neither is read by the mask algebra, which is why the
    # byte-identity of `legacy_all_query` above is unaffected. Asserted exactly on purpose: a
    # stats key appearing without anyone deciding it should is how an artifact schema drifts away
    # from the readers that parse it.
    assert extra == {"n_prefill_edits", "n_query_rows_edited", "n_keys_masked", "mode",
                     "n_blocked_keys", "n_query_span_positions", "n_demo_span_positions",
                     "query_span_bounds", "demo_span_bounds", "liveness_required",
                     "liveness_must_be_zero",
                     "n_surface_span_positions", "surface_span_positions"}, (
        f"the set of NEW stats keys changed: {sorted(extra)}; update this list deliberately")
    assert s_new["n_edits"] == s_new["n_prefill_edits"] + s_new["n_decode_edits"]


# --------------------------------------------------------------------------- #
# MANDATORY 2 — the two modes that are allowed to be silent at decode
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("mode", ["query_prefill_only", "demo_processing_only"])
def test_prefill_only_modes_make_zero_decode_edits(mode):
    model = ToyModel(n_layers=1)
    stats = {}
    with _scoped(model, mode, stats=stats) as ko:
        _run(model, _prefill_mask(SEQ), seq=SEQ)
        for step in range(4):
            seen = _run(model, _decode_mask(SEQ + step), seq=1)[0]
            assert not (seen == MIN).any(), f"{mode} edited a decode-step mask"
    assert stats["n_decode_forward"] == 4, "the hook must still SEE the decode steps"
    assert stats["n_decode_edits"] == 0
    assert stats["n_prefill_edits"] > 0, "…and must be alive at prefill, or the arm is a no-op"
    assert ko.liveness_violations() == []


# --------------------------------------------------------------------------- #
# MANDATORY 3 — decode_only must not touch prefill at all
# --------------------------------------------------------------------------- #
def test_decode_only_leaves_prefill_mask_untouched():
    model = ToyModel(n_layers=1)
    base = _prefill_mask(SEQ)
    stats = {}
    with _scoped(model, "decode_only", stats=stats) as ko:
        seen = _run(model, base, seq=SEQ)[0]
        assert torch.equal(seen, base), (
            "decode_only modified the prefill mask; the unhooked baseline must survive verbatim")
        dec = _run(model, _decode_mask(SEQ), seq=1)[0]
    assert stats["n_prefill_forward"] == 1 and stats["n_prefill_edits"] == 0
    assert stats["n_decode_edits"] > 0
    assert _keys_changed(dec, _decode_mask(SEQ)) == set(KEYS)
    assert ko.liveness_violations() == []


# --------------------------------------------------------------------------- #
# DISJOINTNESS — the decomposition is a decomposition, not two views of one thing
# --------------------------------------------------------------------------- #
def test_prefill_query_and_demo_modes_edit_disjoint_rows_inside_legacy():
    base = _prefill_mask(SEQ)
    rows = {}
    for mode in ("query_prefill_only", "demo_processing_only", "legacy_all_query"):
        model = ToyModel(n_layers=1)
        with _scoped(model, mode):
            rows[mode] = _rows_changed(_run(model, base, seq=SEQ)[0], base)
    a, b, legacy = (rows["query_prefill_only"], rows["demo_processing_only"],
                    rows["legacy_all_query"])
    assert a and b, "both halves must actually edit something or disjointness is vacuous"
    assert a.isdisjoint(b), f"scoped modes overlap on rows {sorted(a & b)}"
    assert (a | b) <= legacy, f"rows {sorted((a | b) - legacy)} are outside the legacy edit"
    assert (a | b) < legacy, "the union must be a STRICT subset (legacy also edits filler rows)"


# --------------------------------------------------------------------------- #
# Per-mode: exactly which rows, exactly which keys, and nothing else
# --------------------------------------------------------------------------- #
def test_query_prefill_only_edits_exactly_the_final_query_rows():
    model = ToyModel(n_layers=1)
    base = _prefill_mask(SEQ)
    with _scoped(model, "query_prefill_only"):
        seen = _run(model, base, seq=SEQ)[0]
    assert _cells_changed(seen, base) == {(0, q, k) for q in (8, 9, 10, 11) for k in (2, 3)}


def test_demo_processing_only_edits_exactly_the_in_block_rows_and_obeys_causality():
    """Rows inside the demo block only, and row r never gains a block on a key it cannot see."""
    model = ToyModel(n_layers=1)
    base = _prefill_mask(SEQ)
    with _scoped(model, "demo_processing_only"):
        seen = _run(model, base, seq=SEQ)[0]
    # rows 2..5 x keys {2,3}, minus (2,3) which is causally masked already (row 2 cannot see key 3)
    assert _cells_changed(seen, base) == {(0, 2, 2), (0, 3, 2), (0, 3, 3),
                                          (0, 4, 2), (0, 4, 3), (0, 5, 2), (0, 5, 3)}


def test_response_query_only_is_query_rows_at_prefill_and_all_rows_at_decode():
    model = ToyModel(n_layers=1)
    base = _prefill_mask(SEQ)
    stats = {}
    with _scoped(model, "response_query_only", stats=stats) as ko:
        pre = _run(model, base, seq=SEQ)[0]
        dec = [_run(model, _decode_mask(SEQ + s), seq=1)[0] for s in range(3)]
    assert _cells_changed(pre, base) == {(0, q, k) for q in (8, 9, 10, 11) for k in (2, 3)}
    for s, m in enumerate(dec):
        assert _keys_changed(m, _decode_mask(SEQ + s)) == set(KEYS), f"decode step {s}"
    assert stats["n_prefill_edits"] > 0 and stats["n_decode_edits"] > 0
    assert ko.liveness_violations() == []


def test_legacy_edits_every_causally_eligible_row_at_prefill():
    model = ToyModel(n_layers=1)
    base = _prefill_mask(SEQ)
    with _scoped(model, "legacy_all_query"):
        seen = _run(model, base, seq=SEQ)[0]
    assert _cells_changed(seen, base) == {(0, q, k) for k in (2, 3) for q in range(k, SEQ)}


@pytest.mark.parametrize("mode", list(SCOPED_KNOCKOUT_MODES))
def test_no_mode_ever_blocks_a_key_outside_blocked_keys(mode):
    model = ToyModel(n_layers=1)
    base = _prefill_mask(SEQ)
    with _scoped(model, mode):
        pre = _run(model, base, seq=SEQ)[0]
        dec = _run(model, _decode_mask(SEQ), seq=1)[0]
    assert _keys_changed(pre, base) <= set(KEYS)
    assert _keys_changed(dec, _decode_mask(SEQ)) <= set(KEYS)


# --------------------------------------------------------------------------- #
# Several generated tokens, and several prompt / demo geometries
# --------------------------------------------------------------------------- #
# n_keys_masked = keys masked at prefill + keys masked on each of the 6 decode steps. Written out
# per mode because a tautological "== itself" assert here would be a DEAD guard: it cannot go red.
@pytest.mark.parametrize("mode,expect_decode,exp_keys_masked", [
    ("legacy_all_query", True, 2 + 6 * 2),      # both keys at prefill, both on every step
    ("decode_only", True, 0 + 6 * 2),           # prefill contributes nothing
    ("response_query_only", True, 2 + 6 * 2),
    ("query_prefill_only", False, 2),           # prefill only
    ("demo_processing_only", False, 2),
])
def test_behaviour_is_stable_across_six_generated_tokens(mode, expect_decode, exp_keys_masked):
    model = ToyModel(n_layers=1)
    stats = {}
    with _scoped(model, mode, stats=stats):
        _run(model, _prefill_mask(SEQ), seq=SEQ)
        for step in range(6):
            m = _run(model, _decode_mask(SEQ + step), seq=1)[0]
            got = _keys_changed(m, _decode_mask(SEQ + step))
            assert got == (set(KEYS) if expect_decode else set()), (
                f"{mode} decode step {step}: keys {sorted(got)}")
    assert stats["n_decode_forward"] == 6
    assert stats["n_keys_masked"] == exp_keys_masked
    if expect_decode:
        assert stats["n_decode_edits"] == 6 * len(KEYS), "one row x one head x two keys per step"
    else:
        assert stats["n_decode_edits"] == 0


@pytest.mark.parametrize("seq,demo,qspan,exp_query_rows,exp_demo_rows", [
    # short prompt, 2-token demo, 2-token query span
    (7, {1, 2}, {5, 6}, {5, 6}, {1, 2}),
    # long prompt, long demo, single-token query span
    (20, {3, 4, 5, 6, 7, 8, 9}, {19}, {19}, {3, 4, 5, 6, 7, 8, 9}),
    # demo adjacent to the query span
    (10, {4, 5}, {6, 7, 8, 9}, {6, 7, 8, 9}, {4, 5}),
])
def test_row_selection_follows_the_spans_at_several_lengths(seq, demo, qspan,
                                                            exp_query_rows, exp_demo_rows):
    """Expected row sets are written out LITERALLY (no formula), so a resolver bug cannot hide."""
    base = _prefill_mask(seq)
    keys = sorted(demo)[:1]                    # first demo token: visible to every listed row
    got = {}
    for mode in ("query_prefill_only", "demo_processing_only"):
        model = ToyModel(n_layers=1)
        with ScopedAttentionKnockout(model, [0], blocked_keys=keys, mode=mode,
                                     query_span=qspan, demo_span=demo):
            got[mode] = _rows_changed(_run(model, base, seq=seq)[0], base)
    assert got["query_prefill_only"] == exp_query_rows
    assert got["demo_processing_only"] == exp_demo_rows


# --------------------------------------------------------------------------- #
# COORDINATE ALGEBRA — absolute vs cache-local, in both axes
# --------------------------------------------------------------------------- #
def test_key_columns_are_absolute_not_cache_local_at_decode():
    """kp indexes am[..., kp] directly. A `kp - past` mix-up would land on a DIFFERENT column."""
    past, kp = 9, 2
    model = ToyModel(n_layers=1)
    base = _decode_mask(past)                  # [1, 1, 1, 10]
    with _scoped(model, "decode_only", keys=[kp]):
        seen = _run(model, base, seq=1)[0]
    assert _keys_changed(seen, base) == {kp}
    wrong = (kp - past) % base.shape[3]        # where a cache-local read would write (column 3)
    assert wrong != kp
    assert seen[0, 0, 0, wrong] == 0, "an absolute-vs-cache-local key mix-up masked column %d" % wrong


def test_query_rows_are_matched_in_absolute_coordinates_not_chunk_local():
    """Chunked forward: n_q=3, kv_len=10 -> past=7, so chunk rows 0,1,2 ARE absolute 7,8,9.

    Case A: the span holds the ABSOLUTE positions -> all three rows edited.
    Case B: the span holds the chunk-LOCAL indices 0,1,2 -> nothing may be edited.
    A `r in span` implementation (instead of `past + r in span`) inverts both answers, so this
    pair pins the algebra from both sides.
    """
    n_q, kv = 3, 10
    past = kv - n_q
    dtype = torch.float32
    base = torch.zeros(1, 1, n_q, kv, dtype=dtype)
    for r in range(n_q):
        for k in range(past + r + 1, kv):
            base[0, 0, r, k] = torch.finfo(dtype).min

    def _rows_for(span):
        model = ToyModel(n_layers=1)
        with ScopedAttentionKnockout(model, [0], blocked_keys=[2], mode="query_prefill_only",
                                     query_span=span, demo_span=DEMO):
            x = torch.zeros(1, n_q, 8)
            model(x, attention_mask=base)
            return _rows_changed(model.model.layers[0].self_attn.seen, base)

    assert _rows_for({7, 8, 9}) == {0, 1, 2}, "absolute span did not reach the chunk rows"
    assert _rows_for({0, 1, 2}) == set(), "chunk-local indices were treated as absolute positions"


# --------------------------------------------------------------------------- #
# Layer / head selectivity for the SCOPED path (the legacy path inherits the tested one)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("mode", list(SCOPED_KNOCKOUT_MODES))
def test_only_selected_layers_are_modified_and_handles_are_removed(mode):
    model = ToyModel(n_layers=3)
    base = _prefill_mask(SEQ)
    with _scoped(model, mode, layers=(1,)):
        pre = _run(model, base, seq=SEQ)
        dec = _run(model, _decode_mask(SEQ), seq=1)
    for li in (0, 2):
        assert torch.equal(pre[li], base), f"layer {li} was modified at prefill by {mode}"
        assert not (dec[li] == MIN).any(), f"layer {li} was modified at decode by {mode}"
    assert (not torch.equal(pre[1], base)) or bool((dec[1] == MIN).any()), (
        f"{mode} edited nothing at all on its own layer")
    after = _run(model, _prefill_mask(SEQ), seq=SEQ)
    assert torch.equal(after[1], base), "handle was not removed on __exit__"


@pytest.mark.parametrize("mode,seq,mask", [("query_prefill_only", SEQ, "prefill"),
                                           ("demo_processing_only", SEQ, "prefill"),
                                           ("response_query_only", SEQ, "prefill"),
                                           ("decode_only", 1, "decode"),
                                           ("legacy_all_query", 1, "decode")])
def test_head_subset_touches_only_those_heads(mode, seq, mask):
    model = ToyModel(n_heads=4)
    base = _prefill_mask(SEQ, heads=1) if mask == "prefill" else _decode_mask(SEQ, heads=1)
    with _scoped(model, mode, heads=[2]):
        seen = _run(model, base, seq=seq)[0]
    assert seen.shape[1] == 4, "head axis was not expanded"
    edited = {h for h, _q, _k in _cells_changed(seen, base.expand(-1, 4, -1, -1))}
    assert edited == {2}, f"{mode} edited heads {sorted(edited)}, expected only head 2"


@pytest.mark.parametrize("mode", list(SCOPED_KNOCKOUT_MODES))
def test_callers_mask_is_never_mutated(mode):
    model = ToyModel(n_layers=1)
    for mk in (_prefill_mask(SEQ), _decode_mask(SEQ)):
        before = mk.clone()
        with _scoped(model, mode):
            _run(model, mk, seq=mk.shape[2])
        assert torch.equal(mk, before), f"{mode} mutated the caller's mask in place"


# --------------------------------------------------------------------------- #
# The gate the consumer imports, and the fail-loud constructor
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("mode", list(SCOPED_KNOCKOUT_MODES))
def test_real_gate_passes_a_correct_run_and_the_tables_cover_every_mode(mode):
    model = ToyModel(n_layers=1)
    stats = {}
    with _scoped(model, mode, stats=stats) as ko:
        _run(model, _prefill_mask(SEQ), seq=SEQ)
        _run(model, _decode_mask(SEQ), seq=1)
    assert set(LIVENESS_REQUIREMENT) == set(SCOPED_KNOCKOUT_MODES) == set(LIVENESS_MUST_BE_ZERO)
    assert scoped_liveness_violations(mode, stats) == [] == ko.liveness_violations()
    assert stats["mode"] == mode
    assert stats["liveness_required"] == list(LIVENESS_REQUIREMENT[mode])
    for key in LIVENESS_REQUIREMENT[mode]:
        assert stats[key] > 0
    for key in LIVENESS_MUST_BE_ZERO[mode]:
        assert stats[key] == 0


@pytest.mark.parametrize("mode", list(SCOPED_KNOCKOUT_MODES))
def test_gate_rejects_a_dead_hook_and_a_leaked_scope(mode):
    """A null is only reportable if the counters this mode DECLARES are satisfied."""
    dead = {k: 0 for k in ("n_prefill_edits", "n_decode_edits")}
    assert scoped_liveness_violations(mode, dead), f"{mode}: an all-zero run must be rejected"
    leaked = {"n_prefill_edits": 5, "n_decode_edits": 5}
    assert bool(scoped_liveness_violations(mode, leaked)) == bool(LIVENESS_MUST_BE_ZERO[mode])


def test_span_resolver_returns_none_all_rows_vs_empty_no_rows():
    """None ('every row') and frozenset() ('no rows') are different answers, never interchangeable."""
    assert resolve_scoped_query_rows("legacy_all_query", True, None, None) is None
    assert resolve_scoped_query_rows("legacy_all_query", False, None, None) is None
    assert resolve_scoped_query_rows("decode_only", True, QSPAN, DEMO) is None
    assert resolve_scoped_query_rows("decode_only", False, QSPAN, DEMO) == frozenset()
    assert resolve_scoped_query_rows("response_query_only", True, QSPAN, DEMO) is None
    assert resolve_scoped_query_rows("response_query_only", False, QSPAN, DEMO) == QSPAN
    assert resolve_scoped_query_rows("query_prefill_only", False, QSPAN, DEMO) == QSPAN
    assert resolve_scoped_query_rows("query_prefill_only", True, QSPAN, DEMO) == frozenset()
    assert resolve_scoped_query_rows("demo_processing_only", False, QSPAN, DEMO) == DEMO
    assert resolve_scoped_query_rows("demo_processing_only", True, QSPAN, DEMO) == frozenset()
    with pytest.raises(ValueError):
        resolve_scoped_query_rows("all_query", False, QSPAN, DEMO)


def test_missing_or_empty_span_raises_instead_of_scoring_a_silent_no_op():
    model = ToyModel(n_layers=1)
    for mode in ("query_prefill_only", "response_query_only"):
        with pytest.raises(ValueError, match="query_span"):
            ScopedAttentionKnockout(model, [0], blocked_keys=KEYS, mode=mode, demo_span=DEMO)
        with pytest.raises(ValueError, match="query_span"):
            ScopedAttentionKnockout(model, [0], blocked_keys=KEYS, mode=mode, query_span=set(),
                                    demo_span=DEMO)
    with pytest.raises(ValueError, match="demo_span"):
        ScopedAttentionKnockout(model, [0], blocked_keys=KEYS, mode="demo_processing_only",
                                query_span=QSPAN)
    with pytest.raises(ValueError, match="mode"):
        ScopedAttentionKnockout(model, [0], blocked_keys=KEYS, mode="prefill_only",
                                query_span=QSPAN, demo_span=DEMO)


def test_resolved_spans_are_recorded_in_stats_so_a_null_is_interpretable():
    model = ToyModel(n_layers=1)
    stats = {}
    with _scoped(model, "query_prefill_only", stats=stats):
        _run(model, _prefill_mask(SEQ), seq=SEQ)
    assert stats["n_query_span_positions"] == len(QSPAN)
    assert stats["n_demo_span_positions"] == len(DEMO)
    assert stats["query_span_bounds"] == [min(QSPAN), max(QSPAN)]
    assert stats["demo_span_bounds"] == [min(DEMO), max(DEMO)]
    assert stats["n_blocked_keys"] == len(KEYS)
    assert stats["n_query_rows_edited"] == len(QSPAN)
    assert stats["n_keys_masked"] == len(KEYS)


# --------------------------------------------------------------------------- #
# DCS PHASE (2026-09-02) — `target_surface_row_only`, the surgical KO-1/KO-2 scope
#
# This scope's entire scientific claim is "ONLY the final target-surface occurrence stopped
# seeing the demonstrations". Every failure mode that would quietly turn it into a different
# experiment is asserted here, because a scope that has silently widened produces a LARGER
# effect and reads as a stronger result -- the direction of error that never gets questioned.
# --------------------------------------------------------------------------- #
def test_target_surface_row_only_edits_exactly_the_surface_rows_at_prefill():
    """The rows edited are EXACTLY SURFACE -- not the query span, not the last row."""
    model = ToyModel(n_layers=1)
    base = _prefill_mask(SEQ)
    with _scoped(model, "target_surface_row_only"):
        seen = _run(model, base, seq=SEQ)[0]
    assert _cells_changed(seen, base) == {(0, 9, 2), (0, 9, 3)}
    assert _rows_changed(seen, base) == set(SURFACE)
    # STRICT subset of the wider query scope: if these were equal, two rungs of the ladder would
    # be the same experiment wearing two names, and a null at the narrow scope would be
    # uninterpretable.
    model2 = ToyModel(n_layers=1)
    with _scoped(model2, "query_prefill_only"):
        wide = _rows_changed(_run(model2, base, seq=SEQ)[0], base)
    assert set(SURFACE) < wide, f"{sorted(SURFACE)} not a strict subset of {sorted(wide)}"


def test_target_surface_row_only_makes_zero_decode_edits():
    """Prefill-only BY DESIGN; the per-mode gate must agree, not a global n_decode_edits>0 gate."""
    model = ToyModel(n_layers=1)
    stats = {}
    with _scoped(model, "target_surface_row_only", stats=stats) as ko:
        _run(model, _prefill_mask(SEQ), seq=SEQ)
        for s in range(3):
            dec = _run(model, _decode_mask(SEQ + s), seq=1)[0]
            assert _cells_changed(dec, _decode_mask(SEQ + s)) == set(), f"decode step {s} edited"
    assert stats["n_prefill_edits"] > 0
    assert stats["n_decode_edits"] == 0
    assert ko.liveness_violations() == []
    assert scoped_liveness_violations("target_surface_row_only", stats) == []


def test_target_surface_row_only_dose_is_smaller_than_every_wider_scope():
    """Dose ordering is a property of the ladder, and dose-matched controls depend on it."""
    base = _prefill_mask(SEQ)
    doses = {}
    for mode in ("target_surface_row_only", "query_prefill_only", "legacy_all_query"):
        model = ToyModel(n_layers=1)
        stats = {}
        with _scoped(model, mode, stats=stats):
            _run(model, base, seq=SEQ)
        doses[mode] = stats["n_prefill_edits"]
    assert 0 < doses["target_surface_row_only"] < doses["query_prefill_only"] \
        <= doses["legacy_all_query"], doses


def test_target_surface_row_only_refuses_an_empty_span():
    """An empty span would be a no-op knockout that scores as a clean null. It must RAISE."""
    m = ToyModel(SEQ)
    for bad in (None, frozenset()):
        with pytest.raises(ValueError, match="surface_span"):
            ScopedAttentionKnockout(m, [0], blocked_keys=KEYS,
                                    mode="target_surface_row_only",
                                    query_span=QSPAN, demo_span=DEMO, surface_span=bad)


def test_target_surface_row_only_refuses_a_span_outside_the_query():
    """A surface span resolved against a DIFFERENT tokenization lands outside the query span.

    That is the ~9-token-shift bug class this repo has hit before: the run still completes and
    still reports edits, but it answers a different question. Refuse at construction.
    """
    m = ToyModel(SEQ)
    with pytest.raises(ValueError, match="not contained in query_span"):
        ScopedAttentionKnockout(m, [0], blocked_keys=KEYS, mode="target_surface_row_only",
                                query_span=QSPAN, demo_span=DEMO,
                                surface_span=frozenset({3}))   # inside the DEMO block, not the query


def test_target_surface_row_only_span_resolver_matches_the_hook():
    """The gate, the hook and the consumer must all read ONE definition of the row set."""
    assert resolve_scoped_query_rows("target_surface_row_only", False, QSPAN, DEMO, SURFACE) == SURFACE
    assert resolve_scoped_query_rows("target_surface_row_only", True, QSPAN, DEMO, SURFACE) == frozenset()
    # a caller that forgets the new argument gets "edit nothing", never "edit everything"
    assert resolve_scoped_query_rows("target_surface_row_only", False, QSPAN, DEMO) == frozenset()


# --------------------------------------------------------------------------- #
# DCS PHASE (2026-09-03) -- `prompt_last_row_only`, the KO-4 rung
#
# This scope exists to separate "retrieved at the readout row" from "retrieved across the query
# span". Its whole value is that it is a STRICT SUBSET of query_prefill_only and DISJOINT from
# target_surface_row_only wherever the codeword is not the last token -- if either property fails
# the three rungs are not separable and the ladder answers nothing.
# --------------------------------------------------------------------------- #
def test_prompt_last_row_only_edits_exactly_the_final_query_row():
    model = ToyModel(n_layers=1)
    base = _prefill_mask(SEQ)
    with _scoped(model, "prompt_last_row_only"):
        seen = _run(model, base, seq=SEQ)[0]
    assert _rows_changed(seen, base) == {max(QSPAN)}
    assert _cells_changed(seen, base) == {(0, 11, 2), (0, 11, 3)}


def test_prompt_last_row_only_is_derived_from_query_span_not_a_new_argument():
    """It must be computable from the span the consumer already resolves, or the two can disagree."""
    assert resolve_scoped_query_rows("prompt_last_row_only", False, QSPAN, DEMO) == frozenset({11})
    assert resolve_scoped_query_rows("prompt_last_row_only", True, QSPAN, DEMO) == frozenset()
    # a narrower query span moves the row -- proving it is derived, not hard-coded
    assert resolve_scoped_query_rows("prompt_last_row_only", False, frozenset({5, 6}), DEMO) \
        == frozenset({6})
    # no span -> edit nothing, never edit everything
    assert resolve_scoped_query_rows("prompt_last_row_only", False, frozenset(), DEMO) == frozenset()


def test_the_three_rungs_are_separable():
    """codeword row / last row / whole span must be a strict, disjoint-where-it-matters ladder."""
    base = _prefill_mask(SEQ)
    rows = {}
    for mode in ("target_surface_row_only", "prompt_last_row_only", "query_prefill_only"):
        model = ToyModel(n_layers=1)
        with _scoped(model, mode):
            rows[mode] = _rows_changed(_run(model, base, seq=SEQ)[0], base)
    surf, last, wide = (rows["target_surface_row_only"], rows["prompt_last_row_only"],
                        rows["query_prefill_only"])
    assert surf < wide and last < wide, "each narrow rung must be a STRICT subset of the wide one"
    assert surf.isdisjoint(last), (
        f"the codeword row {sorted(surf)} and the last row {sorted(last)} overlap; with SURFACE "
        f"deliberately not the final query token these rungs must be disjoint or they answer the "
        f"same question")
    assert surf | last < wide, "their union must still be strictly inside the query span"


def test_prompt_last_row_only_makes_zero_decode_edits():
    model = ToyModel(n_layers=1)
    stats = {}
    with _scoped(model, "prompt_last_row_only", stats=stats) as ko:
        _run(model, _prefill_mask(SEQ), seq=SEQ)
        for s in range(3):
            _run(model, _decode_mask(SEQ + s), seq=1)
    assert stats["n_prefill_edits"] > 0 and stats["n_decode_edits"] == 0
    assert ko.liveness_violations() == []
