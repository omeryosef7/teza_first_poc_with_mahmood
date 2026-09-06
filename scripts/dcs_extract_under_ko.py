"""dcs_extract_under_ko.py — the GATE-R5 CAPTURE BRIDGE (DCS `B-021` / `Q-005`, plan §53).

WHAT THIS IS, IN ONE SENTENCE
    It writes a `cache/final_occurrence_reps.pt` in EXACTLY the format the FROZEN `PR-035`
    analyzer (`scripts/dcs_bombness_specificity.py`) already consumes, but captured while a
    demonstration→query ATTENTION KNOCKOUT is LIVE. Nothing else. It fits no directions, computes
    no probe, and reports no accuracy: the frozen probe procedure is then applied UNCHANGED —
    train on BASELINE cell `B`, test on KNOCKED-OUT cell `C`.

WHY IT EXISTS (plan §53.1). `extract_boombness.py` persists multi-layer hidden states and has no
`--intervene`; `score_behavior.py` applies the knockout and persists only `hnorm|L*` NORMS, and a
norm cannot train a probe. The two capabilities have never met. §54.3 is the consequence: `R-086`
is a DECODABILITY result and gate `R5` — does `KO-3` destroy it? — is NOT RUN.

⛔ THIS FILE REIMPLEMENTS NOTHING. Every load-bearing piece is imported from the file that owns it:

  capture site + layer convention   extract_boombness.resolve_occurrences / forward_hidden
                                    (block L == hidden_states[L+1]; hidden_states[0] == embeddings)
  which KEYS are blocked            score_behavior.demo_key_positions + knockout_key_set("demo_all")
  which QUERY span is protected     score_behavior.query_span_positions
  the HOOK itself                   score_behavior.make_intervention -> pair_common
                                    .AllQueryAttentionKnockout, the class EVERY committed knockout
                                    artifact was produced with (score_behavior.py:1035-1037)
  the LIVENESS gate                 score_behavior.new_knockout_live / record_knockout_row /
                                    knockout_liveness_summary / assert_knockout_live
  the run contract                  common.RunDir (config/metadata/results/summary/DONE.json)

SCOPE IS SELECTABLE (`--knockout-scope`), AND THE DEFAULT IS STILL `legacy_all_query`.
`AllQueryAttentionKnockout` blocks attention onto the demonstration keys from EVERY query row.
This capture is a SINGLE FORWARD PASS — there is no decode step at all — so "every query row" is
exactly "every prefill row", which is the whole-query `KO-3` scope for a forward-only readout, and
that is the scope that produced `R-093`. ⛔ THE DEFAULT PATH IS UNCHANGED: on `legacy_all_query`
this file still constructs the SAME `pc.AllQueryAttentionKnockout` object (the branch lives in
`score_behavior.make_intervention:1035`, not here), still gates it with the SAME legacy closed form,
and adds not one extra tokenization pass.

⛔ WHY A SECOND SCOPE EXISTS AT ALL. Gate `R6` needs `KO-1` = `target_surface_row_only`: block only
the rows of the FINAL `target_surface` occurrence in the query from reading the demonstrations,
rather than the whole query. Plan §13 needs the SAME scope where `target_surface` is the CONCEPT
word (cells `B`/`E`) instead of the codeword (cells `A`/`C`/`D`/`F`) — and `target_surface` is ONE
bank field that already holds both, so one scope, one code path and one dose serve both
(pair_common.py:620-632). ⛔ Nothing is re-implemented for it: the row set is
`score_behavior.target_surface_positions`, the hook is `pc.ScopedAttentionKnockout`, and the
liveness contract is `pc.LIVENESS_REQUIREMENT` / `LIVENESS_MUST_BE_ZERO` as reduced by
`score_behavior.readout_liveness_contract`.

⛔ A SCOPE THAT CANNOT FIRE ON THIS PATH IS REFUSED AT ARGUMENT TIME, never discovered as a null.
`decode_only` edits literally nothing without a decode step, and `response_query_only`, stripped of
its decode half, edits exactly the rows `query_prefill_only` edits — i.e. it would file this run
under a name that misdescribes the intervention. Both refusals come from
`score_behavior.readout_liveness_contract`, which asks the hook's OWN row resolver rather than
consulting a list of mode names kept here.

⛔ THE FAILURE THIS FILE IS MOST AFRAID OF is a mask that never fires. A silent no-op writes a cache
that looks perfect, is not knocked out at all, and would be read as "the knockout does not destroy
the signal" — the strongest possible wrong answer. The repo has been bitten by exactly this
(`C-047`; and `AttentionKnockout` vs `AllQueryAttentionKnockout`, pair_common.py:495-536). So:

  * `attn_implementation='eager'` is FORCED whenever the knockout is live, and re-checked on the
    loaded config. Under SDPA/flash a custom additive mask is discarded silently.
  * EVERY row is checked against an EXACT, CLOSED-FORM prediction of how many mask cells the key
    set implies (`expected_prefill_edit_rows` below), not merely against "> 0". A hook that fired
    on the wrong rows, on a truncated key set, or at a subset of the band, fails here.
  * the per-row verdict is `score_behavior.record_knockout_row(..., readout=True)` — the SAME
    accumulator the committed forward-only readout runs use — and the run-level verdict is
    `assert_knockout_live`, called BEFORE `finish()`. A run that cannot prove liveness aborts and
    writes ABORTED.json, so no analyzer will ever read it (they require DONE.json).

⛔ ROWS WITH NO DEMONSTRATION BLOCK (`n_examples == 0`) CANNOT BE KNOCKED OUT and are LEDGERED AND
SKIPPED, never captured un-hooked. Mixing hooked and un-hooked vectors into one cache under one
run name is the same silent-no-op failure wearing a different hat. The consequence is declared:
the `C_n0` blocking-null cell is EMPTY in a knocked-out run, by construction and on purpose.

Responsible handling: no generation, no prompt text in results.jsonl beyond the single decoded
token at the capture position (which is the provenance answer to "which token did you read?").
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from typing import Dict, List, Optional, Sequence

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_BOOMB = os.path.join(_REPO, "src", "boombness")
if _BOOMB not in sys.path:
    sys.path.insert(0, _BOOMB)          # importing `common` also bootstraps doublespeak_causality/

import torch                                                                  # noqa: E402

from common import DATA_DIR, FailureLedger, RunDir, ds, pair, read_jsonl, seed_everything  # noqa: E402
import signals as sg                                                          # noqa: E402
from ds_common import parse_enable_thinking as dc_parse_thinking              # noqa: E402
import extract_boombness as eb                                                # noqa: E402
import score_behavior as sb                                                   # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")

#: `PR-035` band. Kept as a default, never as an assumption: it is echoed and bounds-checked
#: against the loaded model's depth (score_behavior.py:1700 records why — a band copied from a
#: model of a different depth is the silent-weaker-knockout bug, and no exception can catch it).
DEFAULT_BAND = "6-14"

#: The DEFAULT scope, and the ONLY scope every committed run of this file (`R-093` included) has
#: used. Imported from `score_behavior` rather than typed here, so the two cannot drift.
LEGACY_SCOPE = sb.DEFAULT_KNOCKOUT_SCOPE            # == "legacy_all_query"

#: Kept as an alias because `R-093`'s artifacts and this file's own history name it. Same object.
KNOCKOUT_SCOPE = LEGACY_SCOPE

#: `query_last_k_rows` takes its row set VERBATIM from the consumer (score_behavior's
#: `--knockout-last-k`), not from any span resolvable here. Growing a second, silently-different
#: definition of "last K" in this file is exactly how two scopes with one name diverge, so it is
#: refused with a pointer to the script that owns it.
SCOPES_NOT_SUPPORTED_HERE = ("query_last_k_rows",)

#: The scope that needs `target_surface` rows. Named once; `resolve_row_spans` and the argument
#: validation both read this rather than repeating the string.
SURFACE_SCOPE = "target_surface_row_only"


# --------------------------------------------------------------------------- #
# Two pure functions, so the self-test can drive the REAL ones
# --------------------------------------------------------------------------- #
def pick_layer_rows(hs: torch.Tensor, layers: Sequence[int], pos: int) -> torch.Tensor:
    """`[len(layers), H]` at token `pos`, under the house layer convention.

    THE OFF-BY-ONE IS THE WHOLE FUNCTION. `hs[0]` is the EMBEDDING; block `L` is `hs[L+1]`
    (extract_boombness.py:21, sg.LAYER_CONVENTION). Get it wrong and every layer of the cache is
    shifted by one while every shape, every norm and every downstream accuracy stays plausible.
    Written as one testable function rather than inline, so `--self-test` can prove the shift on a
    tensor whose contents encode their own index.

    Byte-for-byte the expression extract_boombness.stage_score caches with (`hs[L + 1, pos, :]`),
    stacked in the same order and halved the same way — that identity is what makes the frozen
    analyzer able to consume this file's output without knowing it exists.
    """
    return torch.stack([hs[L + 1, pos, :] for L in layers], dim=0)


def expected_prefill_edit_rows(blocked_keys: Sequence[int], seq_len: int,
                               allowed_rows: Optional[frozenset] = None) -> int:
    """How many (query row, key) cells the knockout MUST edit on ONE prefill pass.

    Derived from the hook's own index algebra (pair_common.py:562-574 legacy, 850-878 scoped),
    not guessed:

        past = kv_len - n_q = 0 at prefill, so n_q == kv_len == seq_len;
        for each blocked key kp < kv_len the first causally-legal query row is lo = max(0, kp),
        and every row from lo onward is a CANDIDATE.

    `allowed_rows is None` is the LEGACY (`legacy_all_query`) case: every candidate row is edited,
    so the count is `sum(seq_len - kp)`. ⛔ That branch is byte-for-byte the arithmetic this
    function had before `--knockout-scope` existed, and it is what the default path still uses.

    `allowed_rows` is the SCOPED case: `ScopedAttentionKnockout` keeps only the candidates whose
    ABSOLUTE position is in the resolver's row set (`rows = [r for r in range(lo, n_q) if
    (past + r) in allowed]`), so the count is `sum_kp |{r in allowed_rows : kp <= r < seq_len}|`.
    ⛔ THIS IS AN EXACT CLOSED FORM, NOT A WEAKENED FALLBACK — the same per-key, per-row algebra,
    with the row filter the hook itself applies, and `--self-test` checks it against the REAL hook's
    own counter on a synthetic mask rather than against a second copy of this arithmetic.

    The hook multiplies that by the mask's head dimension and accumulates over the band, so the
    observed counter is `len(band) * head_mult * this`. `head_mult` is INFERRED from the first row
    (it is 1 for a broadcast [1,1,q,k] eager mask and n_heads for an expanded one) and then held
    FIXED and asserted on every later row — inferring it per row would make the check unfalsifiable.

    THIS IS THE DIFFERENCE BETWEEN A LIVENESS CHECK AND A LIVENESS GATE. `n_edits > 0` passes for a
    hook that fired on one layer, on one key, on one row. This does not.
    """
    n = int(seq_len)
    if allowed_rows is None:
        return int(sum(n - int(kp) for kp in blocked_keys if 0 <= int(kp) < n))
    rows = sorted(int(r) for r in allowed_rows if 0 <= int(r) < n)
    return int(sum(sum(1 for r in rows if r >= int(kp))
                   for kp in blocked_keys if 0 <= int(kp) < n))


def scoped_prefill_rows(pc, scope: str, seq_len: int, query_span, demo_span, surface_span):
    """Which ABSOLUTE query rows `scope` may edit on THIS file's ONE prefill forward, or None.

    ⛔ ASKED OF THE HOOK'S OWN RESOLVER. `pc.resolve_scoped_query_rows(scope, is_decode=False, ...)`
    is the exact call `ScopedAttentionKnockout._pre` makes, so the prediction below cannot drift
    from the mode it is predicting — which is the whole reason a scoped liveness gate is possible
    at all. `None` means "every row" (legacy) and is passed straight through; an EMPTY set means
    "this scope edits nothing on this row", which is a no-op knockout and must never be captured.
    """
    allowed = pc.resolve_scoped_query_rows(scope, False, query_span, demo_span, surface_span)
    if allowed is None:
        return None
    return frozenset(int(r) for r in allowed if 0 <= int(r) < int(seq_len))


def expected_prefill_edits_for_scope(pc, scope: str, blocked_keys: Sequence[int], seq_len: int, *,
                                     query_span=None, demo_span=None, surface_span=None):
    """`(expected_cells, form_tag, legacy_cells, allowed_rows)` for ONE row under `scope`.

    ⛔ THE LEGACY CLOSED FORM IS STILL THE ONE APPLIED WHEN THE SCOPE IS LEGACY, and it is applied
    UNCONDITIONALLY there: `legacy_all_query` returns `expected_prefill_edit_rows(keys, seq_len)`
    with `allowed_rows=None`, tagged `legacy_closed_form`, and the resolver is additionally
    asserted to have answered "every row". That assertion is not decoration — if a future edit made
    the legacy scope resolve to a row SET, the default path would silently become a scoped one and
    `R-093`'s reproduction would quietly stop being a reproduction.

    `legacy_cells` is returned for EVERY scope, including the scoped ones, because it is the
    denominator of the one check that survives a total failure of this arithmetic: a scope that
    claims to be surgical must edit strictly fewer cells than the whole-query knockout would
    (`assert_scope_narrows`).
    """
    legacy = expected_prefill_edit_rows(blocked_keys, seq_len)
    allowed = scoped_prefill_rows(pc, scope, seq_len, query_span, demo_span, surface_span)
    if scope == LEGACY_SCOPE:
        if allowed is not None:
            raise RuntimeError(
                f"scope {scope!r} resolved to an explicit row set {sorted(allowed)[:8]}... instead "
                f"of the all-rows sentinel None. The DEFAULT path would no longer be the path "
                f"`R-093` ran; refusing rather than re-gating it under a different closed form.")
        return legacy, "legacy_closed_form", legacy, None
    if allowed is None:
        raise RuntimeError(
            f"scope {scope!r} resolved to the ALL-ROWS sentinel, i.e. to `legacy_all_query`'s row "
            f"set. A scoped arm whose rows are every row is the legacy knockout filed under a "
            f"surgical name; refusing.")
    return (expected_prefill_edit_rows(blocked_keys, seq_len, allowed_rows=allowed),
            "scoped_closed_form", legacy, allowed)


def assert_scope_narrows(scope: str, expected_rows: int, legacy_rows: int, prompt_id: str) -> None:
    """A non-legacy scope must imply MORE THAN ZERO and STRICTLY FEWER cells than legacy would.

    ⛔ DELIBERATELY REDUNDANT with the exact closed form. `assert_row_edits` compares the hook's
    counter against `expected_rows`; if the scope silently degraded to `legacy_all_query`, BOTH the
    prediction and the counter would move together and that comparison would still pass. This is
    the check that does not: it is stated in terms of what the scope CLAIMS about itself, and it
    reads the two predictions against each other rather than a prediction against a counter.
    """
    if scope == LEGACY_SCOPE:
        return
    if expected_rows <= 0:
        raise RuntimeError(f"{prompt_id}: scope {scope!r} resolves to ZERO editable mask cells "
                           f"(legacy would edit {legacy_rows}); a no-op knockout must never be "
                           f"captured — it scores as a perfectly clean null.")
    if expected_rows >= legacy_rows:
        raise RuntimeError(f"{prompt_id}: scope {scope!r} implies {expected_rows} mask cells but "
                           f"`legacy_all_query` implies {legacy_rows}. A SURGICAL scope that does "
                           f"not narrow the edit is the whole-query knockout under another name.")


def assert_row_edits(stats: Dict, *, n_band_layers: int, expected_rows: int, head_mult: Optional[int],
                     prompt_id: str, legal_head_mults: Optional[tuple] = None) -> int:
    """Check ONE row's hook counters against the closed form; return the head multiplier.

    `expected_rows` is whichever closed form the run's SCOPE selected
    (`expected_prefill_edits_for_scope`): the legacy `sum(seq_len - kp)` on `legacy_all_query`, the
    row-filtered `sum_kp |{r in allowed : kp <= r}|` on a scoped one. The arithmetic below — one
    forward per band layer, a whole multiple of `n_band_layers x expected_rows`, a head multiplier
    fixed by row 0 — is IDENTICAL either way, which is the point of deriving the scoped form
    exactly instead of falling back to a ">0" check on the scoped path.

    Raises RuntimeError (not SystemExit) so the caller decides whether one bad row aborts the run
    or is charged to the ledger — SystemExit is a BaseException and would sail past a per-row
    `except Exception`, which is the failure mode `knockout_key_set`'s own comment records.
    """
    ks = sb.knockout_row_stats(stats)
    pf = int(ks.get("n_prefill_forward", 0))
    df = int(ks.get("n_decode_forward", 0))
    pe = int(ks.get("n_prefill_edits", 0))
    de = int(ks.get("n_decode_edits", 0))
    if pf != n_band_layers:
        raise RuntimeError(f"{prompt_id}: hook entered at prefill {pf} times, expected exactly "
                           f"{n_band_layers} (one per band layer, one forward). A band layer whose "
                           f"hook never fired is a partial knockout reported as a whole one.")
    if df or de:
        raise RuntimeError(f"{prompt_id}: this is a SINGLE-FORWARD capture, but the hook recorded "
                           f"n_decode_forward={df} n_decode_edits={de}. Something generated.")
    if expected_rows <= 0:
        raise RuntimeError(f"{prompt_id}: the key set and the knockout SCOPE together imply ZERO "
                           f"editable mask cells; a no-op knockout must never be captured.")
    if pe <= 0:
        raise RuntimeError(f"{prompt_id}: THE MASK NEVER FIRED (n_prefill_edits=0) while "
                           f"{expected_rows} cells x {n_band_layers} layers were implied by the "
                           f"key set and the scope. This is the silent no-op (C-047); refusing.")
    denom = n_band_layers * expected_rows
    if pe % denom:
        raise RuntimeError(f"{prompt_id}: n_prefill_edits={pe} is not a whole multiple of "
                           f"{n_band_layers} layers x {expected_rows} implied cells; the hook did "
                           f"not edit the rows the key set and the scope imply.")
    got = pe // denom
    # C-071 (H-8): the multiplier used to be INFERRED from row 0 and never BOUNDED, so any row set
    # whose scoped/legacy ratio happens to be constant absorbed a silently-widened mask into `got`
    # and the run completed clean -- an adversarial review drove a WHOLE-QUERY knockout to a valid
    # DONE.json under the `target_surface_row_only` name, with the only trace a `mask_head_mult` of
    # 47 that nothing read. The eager 4-D mask is either broadcast [1,1,q,k] (multiplier 1) or
    # expanded per head (multiplier n_heads); nothing else is a legal shape.
    if legal_head_mults and got not in legal_head_mults:
        raise RuntimeError(
            f"{prompt_id}: mask head multiplier {got} is not a legal mask shape "
            f"(expected one of {legal_head_mults}: 1 for a broadcast [1,1,q,k] eager mask, "
            f"n_heads for an expanded one). A multiplier outside that set means the edited cell "
            f"count does not decompose as layers x implied-rows x heads, i.e. the mask edited "
            f"rows the declared scope does not imply. Refusing to capture this row.")
    if head_mult is not None and got != head_mult:
        raise RuntimeError(f"{prompt_id}: mask head multiplier changed mid-run ({got} vs "
                           f"{head_mult}); the mask shape is not stable and the counter no longer "
                           f"means what row 0 established it means.")
    return got


# --------------------------------------------------------------------------- #
# The capture
# --------------------------------------------------------------------------- #
def select_rows(rows: List[Dict], smoke: int, limit: int, knockout: bool) -> List[Dict]:
    """The prompt set this process will attempt, in BANK ORDER.

    `--smoke N` picks rows that CAN carry the knockout (non-empty `demo_block`) — and it does so
    WHETHER OR NOT the knockout is live, deliberately. Two reasons, and the second is the one that
    matters: a pre-flight over N rows that all skip is a pre-flight of nothing; and the smoke's
    other job is the THREE-WAY comparison (committed baseline / local `--no-knockout` / local
    knocked-out), which is only a comparison if all three ran the SAME prompts. A `--no-knockout`
    smoke over a different row set would answer "does it reproduce" and "did it change" about two
    different populations, which is not an answer.

    `knockout` is still taken, and still selects the fallback: with no demo-block rows in range
    (e.g. a bank slice that is all `n_examples == 0`) a knocked-out run must select nothing and say
    so, while a baseline run may legitimately proceed on what is there.
    """
    out = list(rows)
    if limit:
        out = out[:limit]
    if smoke:
        pool = [r for r in out if (r.get("demo_block") or "")]
        if not pool and not knockout:
            pool = out
        out = pool[:smoke]
    return out


def resolve_row_spans(dc, tok, row, args, scope: Optional[str]):
    """Everything the knockout needs for ONE row, off ONE templating of it.

    Returns `(occ, demo_keys, query_span, surface_span, reason)`. `occ` is
    `extract_boombness.resolve_occurrences`' 5-tuple, or None when even that failed; `reason` is
    None on success and otherwise the ledger string, prefixed by which resolution step failed.

    `scope is None` is the BASELINE (`--no-knockout`) path: it resolves occurrences and NOTHING
    else, so a baseline capture still never calls `demo_key_positions` — exactly as before.

    ⛔ ONE RESOLVER, TWO CALLERS. The scoped pre-flight and the capture loop both call this, so the
    population the pre-flight cleared IS the population the loop runs, by construction rather than
    by two functions agreeing. And every span comes off the SAME `templated` string: a second
    templating path can disagree with the first (enable_thinking, specials) and the mask would then
    cut an arbitrary window while every downstream number still looked healthy
    (score_behavior.py:744 records that failure).
    """
    try:
        occ = eb.resolve_occurrences(dc, tok, row, enable_thinking=args._enable_thinking)
    except ValueError as e:
        return None, [], None, None, f"resolve:{e}"
    if scope is None:
        return occ, [], None, None, None
    templated = occ[0]
    dk, why = sb.demo_key_positions(tok, row, templated)
    if why:
        return occ, [], None, None, f"demokeys:{why}"
    prot = sb.query_span_positions(tok, row, templated, dk)
    surf = None
    if scope == SURFACE_SCOPE:
        pos, swhy = sb.target_surface_positions(tok, row, templated, prot)
        if swhy:
            return occ, dk, prot, None, f"surfacespan:{swhy}"
        surf = frozenset(int(p) for p in pos)
        # ⛔ THE HOOK REFUSES A SURFACE SPAN THAT LEAKS OUTSIDE THE QUERY SPAN — and it refuses it
        # in its CONSTRUCTOR, which this file calls inside the per-row `try`, where the refusal
        # would arrive as a quiet ledger entry and a shrunken population.
        # `target_surface_positions` only requires the occurrence's LAST subtoken to be inside the
        # query span (score_behavior.py:784-791, and for good reason there), so a LEADING subtoken
        # can sit outside it. Checked here, where it is a pre-flight refusal instead.
        if prot and not surf <= frozenset(int(p) for p in prot):
            return occ, dk, prot, surf, "surfacespan:not_contained_in_query_span"
    if scope != LEGACY_SCOPE and sb.scoped_span_is_dead(scope, prot, dk, surf):
        return occ, dk, prot, surf, f"scopespan:{scope}_resolves_to_no_query_rows"
    return occ, dk, prot, surf, None


def scoped_preflight(dc, tok, rows, args, scope, run, ledger) -> Dict:
    """REFUSE BEFORE CAPTURING ANYTHING if any selected row cannot carry this scope.

    ⛔ ONLY RUNS FOR A NON-LEGACY SCOPE, so the default path costs not one extra tokenization and
    stays exactly the run `R-093` produced.

    This is `score_behavior.py:1840-1920`'s pre-flight, in this file's smaller vocabulary and for
    the same reason it exists there: a scoped mode whose rows resolve to nothing on some rows is a
    no-op knockout on those rows, and dropping them instead is a SILENTLY SHRUNKEN population —
    which for gate `R6` would change the held-out test set that the paired sign test is computed
    over. The `n_examples == 0` rows are the ONE declared exception (module docstring): they have
    no demonstrations to block under any scope, and they are skipped in the legacy path too.
    """
    feas = {"n_rows": len(rows), "scope": scope, "resolve_error": 0, "no_demo_block": 0,
            "dead_scope_span": 0, "ok": 0, "surface_span_sizes": {}}
    bad: List = []
    sizes: Dict[int, int] = collections.defaultdict(int)
    for row in rows:
        occ, dk, prot, surf, why = resolve_row_spans(dc, tok, row, args, scope)
        if occ is None:
            # A row that cannot even be templated fails identically with and without the knockout;
            # it is the legacy path's own ledgered skip, not a statement about this scope.
            feas["resolve_error"] += 1
            continue
        if why and why.startswith("demokeys:"):
            feas["no_demo_block"] += 1
            continue
        if why:
            feas["dead_scope_span"] += 1
            bad.append((row.get("prompt_id"), why))
            continue
        feas["ok"] += 1
        sizes[len(surf) if surf else 0] += 1
    feas["surface_span_sizes"] = {str(k): v for k, v in sorted(sizes.items())}
    run.note(knockout_feasibility=feas)
    print(f"[ko-extract] SCOPE PRE-FLIGHT ({scope}): {feas}", flush=True)
    if bad:
        # ABORTED.json, not a bare exit: a run directory that stops without a verdict is the one
        # artifact shape an analyzer can mistake for an interrupted-but-fine run.
        run.abort(f"scope_preflight_dead_span: {len(bad)} rows cannot carry {scope!r}",
                  ledger=ledger)
        raise SystemExit(
            f"REFUSING before capturing anything: {len(bad)} of {feas['n_rows']} selected rows "
            f"cannot carry scope {scope!r} (first 5: {bad[:5]}). Capturing the rest would write a "
            f"cache over a SILENTLY SHRUNKEN population, and the held-out sign test downstream is "
            f"computed over exactly that population. Fix the scope or the bank slice — do NOT "
            f"rescope to the feasible rows.")
    return feas


def capture(lm, dc, pc, rows, layers, band, run, ledger, args) -> Dict:
    tok = lm.tokenizer
    knockout = not args.no_knockout
    scope = args.knockout_scope if knockout else None
    spec = ({"direction": args.arm, "mode": "attn_knockout", "layers": list(band), "alpha": 1.0}
            if knockout else None)
    knock_live = sb.new_knockout_live() if knockout else None
    cache: Dict[str, torch.Tensor] = {}
    head_mult: Optional[int] = None
    # C-071 (H-8): the only legal mask shapes for the eager 4-D path. Read from the MODEL's
    # own config rather than restated, so it cannot drift from the architecture in use; if
    # the field is absent the bound is simply not applied (the mid-run stability check at
    # assert_row_edits still holds), because a guessed n_heads would be worse than none.
    _nh = getattr(getattr(lm.model, "config", None), "num_attention_heads", None)
    legal_head_mults = (1, int(_nh)) if isinstance(_nh, int) and _nh > 0 else None
    n_ok = 0
    n_keys_hist: List[int] = []
    skip_reasons: Dict[str, int] = collections.defaultdict(int)
    diag = {}
    exp_forms: Dict[str, int] = collections.defaultdict(int)
    surf_hist: List[int] = []

    if knockout and scope != LEGACY_SCOPE:
        scoped_preflight(dc, tok, rows, args, scope, run, ledger)

    for row in rows:
        pid = row["prompt_id"]
        occ, dk, prot, surf, why = resolve_row_spans(dc, tok, row, args, scope)
        if occ is None:
            ledger.fail(why, pid)
            skip_reasons[why.split(":")[1]] += 1
            continue
        templated, ids, last, following, n_sub = occ
        if args.position != "last" and not last:
            ledger.fail(f"capture:no_occurrence_at_position:{args.position}", pid)
            skip_reasons["no_occurrence_at_position"] += 1
            continue

        keys: List[int] = []
        stats = None
        exp_rows = 0
        exp_form = None
        exp_legacy = 0
        if why and why.startswith("demokeys:"):
            # `no_demo_block` is the n_examples == 0 rows. DECLARED, LEDGERED, SKIPPED — see
            # the module docstring. Capturing them un-hooked would put un-knocked-out vectors
            # into a cache whose name says every vector in it is knocked out.
            ledger.fail(why, pid)
            skip_reasons[why.split(":")[1]] += 1
            if args.on_no_demo_block == "fail":
                raise SystemExit(f"REFUSING: {pid} has no usable demonstration block ({why}) "
                                 f"and --on-no-demo-block=fail")
            continue
        if why:
            # A SCOPED span that does not resolve. `scoped_preflight` already refused the run if
            # any selected row was in this state, so arriving here means the two disagreed — which
            # is itself a reason to write no cache at all.
            run.abort(f"scoped_span_unresolvable_after_preflight: {pid}: {why}", ledger=ledger)
            raise SystemExit(f"REFUSING (run aborted, no DONE.json): {pid}: {why} — the scope "
                             f"pre-flight cleared this row and the capture loop did not.")
        if knockout:
            keys = sb.knockout_key_set(args.arm, dk, len(ids), args.seed, protected=prot)
            if not keys:
                ledger.fail("keys:empty_key_set", pid)
                skip_reasons["empty_key_set"] += 1
                continue
            try:
                exp_rows, exp_form, exp_legacy, _allowed = expected_prefill_edits_for_scope(
                    pc, scope, keys, len(ids),
                    query_span=prot, demo_span=dk, surface_span=surf)
                assert_scope_narrows(scope, exp_rows, exp_legacy, pid)
            except RuntimeError as e:
                run.abort(f"scope_prediction_failure: {e}", ledger=ledger)
                raise SystemExit(f"REFUSING (run aborted, no DONE.json): {e}")
            exp_forms[exp_form] += 1
            surf_hist.append(len(surf) if surf else 0)
            stats = {}

        try:
            if knockout:
                # ⛔ `surface_span` MUST be forwarded with the scope. Dropping it demotes
                # `target_surface_row_only` to a no-op (the resolver answers "edit nothing"), and
                # the hook refuses an empty required span in its constructor PRECISELY so that
                # shows up as a crash rather than as a clean null (score_behavior.py:1038-1041).
                ctxs = sb.make_intervention(dc, pc, lm, spec, None, control_seed=args.seed,
                                            demo_keys=dk, seq_len=len(ids), knock_stats=stats,
                                            protected=prot, knock_heads=None,
                                            knock_scope=scope, surface_span=surf)
                if not ctxs:
                    raise RuntimeError("make_intervention produced NO hooks for an attn_knockout "
                                       "spec; the forward would be an un-knocked-out baseline "
                                       "captured under a knockout run name.")
                import contextlib
                with contextlib.ExitStack() as st:
                    for c in ctxs:
                        st.enter_context(c)
                    hs = eb.forward_hidden(lm, ids, _diag=diag)
                head_mult = assert_row_edits(stats, n_band_layers=len(band),
                                             expected_rows=exp_rows, head_mult=head_mult,
                                             prompt_id=pid,
                                             legal_head_mults=legal_head_mults)
                ks, bad = sb.record_knockout_row(knock_live, scope, stats,
                                                 n_demo_positions=len(dk), readout=True)
                if bad:
                    raise RuntimeError(f"{pid}: liveness contract violated: {bad}")
            else:
                hs = eb.forward_hidden(lm, ids, _diag=diag)
                ks = {}
        except RuntimeError as e:
            # A liveness failure is NOT a row to skip past. One row whose mask did not fire means
            # the wiring is wrong for every row, and a shrunken-but-clean cache is precisely the
            # artifact that gets read as a result. Abort the whole run.
            run.abort(f"knockout_liveness_row_failure: {e}", ledger=ledger)
            raise SystemExit(f"REFUSING (run aborted, no DONE.json): {e}")

        pos = (len(ids) - 1) if args.position == "last" else last[-1]
        # The SAME self-check extract_boombness makes on every row (the phantom-cell guard).
        if args.position == "codeword_last" and pos not in last:
            raise SystemExit(f"{pid}: capture index {pos} is not a codeword occurrence")
        if args.position == "last" and pos != len(ids) - 1:
            raise SystemExit(f"{pid}: capture index {pos} != seq_len-1")

        vec = pick_layer_rows(hs, layers, pos)
        cache[pid] = vec.half()

        rec: Dict[str, object] = {
            "prompt_id": pid, "prompt_sha16": row.get("prompt_sha16"),
            "family_id": row.get("family_id"), "cell": row.get("cell"),
            "domain": row.get("domain"), "split": row.get("split"),
            "condition": row.get("condition"), "bank_block": row.get("bank_block"),
            "query_kind": row.get("query_kind"), "n_examples": row.get("n_examples"),
            "strength": row.get("strength"), "consistency": row.get("consistency"),
            "target_surface": row.get("target_surface"),
            # ---- capture provenance: WHERE was this vector read from? ----------------------- #
            "position": args.position, "token_pos": int(pos), "seq_len": len(ids),
            "token_text": tok.decode([ids[pos]]),
            "n_occurrences": len(last), "n_subtokens": (n_sub[-1] if n_sub else None),
            "layer_convention": sg.LAYER_CONVENTION, "layers": list(layers),
            # ---- knockout provenance: WHAT was blocked, and did it fire? -------------------- #
            "ko_applied": bool(knockout), "arm": (args.arm if knockout else None),
            "knockout_scope": scope,
            "band": (list(band) if knockout else None),
            "band_str": (args.band if knockout else None),
            "seed": int(args.seed),
            "n_demo_keys": len(dk), "n_blocked_keys": len(keys),
            "demo_key_min": (min(dk) if dk else None), "demo_key_max": (max(dk) if dk else None),
            "blocked_key_min": (min(keys) if keys else None),
            "blocked_key_max": (max(keys) if keys else None),
            "n_query_span_positions": (len(prot) if prot else 0),
            # The surgical scope's rows go in the artifact IN FULL, not as a count: "which rows
            # did you actually cut" is the first question anyone will ask of a scoped null, and a
            # `target_surface` occurrence is small enough to record exactly (pair_common.py:832).
            "n_surface_span_positions": (len(surf) if surf else 0),
            "surface_span_positions": (sorted(surf) if surf else None),
            "expected_prefill_edit_rows": int(exp_rows),
            # WHICH closed form gated this row, and what the WHOLE-QUERY knockout would have
            # edited. Recorded per row so `legacy_closed_form` on every row of a default run is
            # checkable from the artifact alone, not only from this file.
            "expected_prefill_edit_rows_form": exp_form,
            "expected_prefill_edit_rows_legacy": int(exp_legacy),
            "mask_head_mult": (int(head_mult) if head_mult else None),
            "hook_n_forward": int(ks.get("n_forward", 0)) if ks else 0,
            "hook_n_prefill_forward": int(ks.get("n_prefill_forward", 0)) if ks else 0,
            "hook_n_decode_forward": int(ks.get("n_decode_forward", 0)) if ks else 0,
            "hook_n_edits": int(ks.get("n_edits", 0)) if ks else 0,
            "hook_n_prefill_edits": int(ks.get("n_prefill_edits", 0)) if ks else 0,
            "hook_n_decode_edits": int(ks.get("n_decode_edits", 0)) if ks else 0,
            "hook_liveness_readout_only": bool(knockout),
            "bank_file_sha16": args._bank_file_sha16,
        }
        # `hnorm|L*`, the SAME column name extract_boombness writes. `dcs_verify_pr035_primary`'s
        # V6 binds a rep cache to its own run by comparing ||rep|| against these, so writing them
        # is what lets an independent verifier prove this cache is not another bank's.
        for j, L in enumerate(layers):
            rec[f"hnorm|L{L}"] = float(vec[j].float().norm())
        run.log_row(rec)
        n_keys_hist.append(len(keys))
        ledger.ok()
        n_ok += 1
        if n_ok % 100 == 0:
            print(f"[ko-extract] {n_ok}/{len(rows)} captured", flush=True)

    if cache:
        os.makedirs(run.cache, exist_ok=True)
        # ⛔ BYTE-FOR-BYTE THE EXTRACTOR'S PAYLOAD (extract_boombness.py:729). Any extra key is
        # fine; a missing or renamed one silently breaks `load_reps` in the FROZEN analyzer, which
        # this file is not allowed to edit.
        torch.save({"layers": list(layers), "layer_convention": sg.LAYER_CONVENTION,
                    "position": args.position, "dtype": "float16", "reps": cache},
                   os.path.join(run.cache, "final_occurrence_reps.pt"))
        print(f"[ko-extract] cached {len(cache)} rep stacks -> {run.cache}/"
              f"final_occurrence_reps.pt")

    out: Dict[str, object] = {
        "n_rows_attempted": len(rows), "n_rows_captured": n_ok, "n_cached": len(cache),
        "skip_reasons": dict(skip_reasons),
        "knockout_applied": bool(knockout),
        "arm": (args.arm if knockout else None),
        "knockout_scope": scope,
        "expected_prefill_edit_rows_forms": dict(exp_forms),
        "median_n_surface_span_positions": (sorted(surf_hist)[len(surf_hist) // 2]
                                            if surf_hist else 0),
        "band": (list(band) if knockout else None),
        "mask_head_mult": head_mult,
        "median_n_blocked_keys": (sorted(n_keys_hist)[len(n_keys_hist) // 2] if n_keys_hist else 0),
        "layer_convention": sg.LAYER_CONVENTION,
        "last_layer_tied_vs_raw_relnorm": diag.get("last_layer_tied_vs_raw_relnorm"),
    }
    if knockout:
        # THE RUN-LEVEL GATE. `assert_knockout_live` raises SystemExit unless the mask demonstrably
        # fired where THIS scope says it must, on >= 99% of rows, and n_rows == 0 is a FAILURE.
        ksum = sb.knockout_liveness_summary(knock_live, "eager", scope=scope, readout=True)
        out["knockout_liveness"] = ksum
        sb.assert_knockout_live(ksum)
        # ⛔ AND THE PER-ROW GATE MUST HAVE BEEN THE ONE THIS SCOPE DECLARES. `assert_knockout_live`
        # reads the accumulator; this reads which closed form actually gated every row, so a run
        # whose scope said `target_surface_row_only` while every row was gated by the whole-query
        # form (or the reverse) cannot reach `finish()`.
        _want_form = "legacy_closed_form" if scope == LEGACY_SCOPE else "scoped_closed_form"
        if set(exp_forms) != {_want_form}:
            raise SystemExit(f"REFUSING: scope {scope!r} must gate EVERY row with "
                             f"{_want_form!r}, but the rows were gated by {dict(exp_forms)}.")
        print(f"[ko-extract] LIVENESS OK: {ksum['n_rows']} rows, "
              f"frac_rows_scope_live={ksum['frac_rows_scope_live']}, "
              f"total_prefill_edits={ksum['total_prefill_edits']}, "
              f"median_prefill_edits={ksum['median_prefill_edits']}, "
              f"total_decode_edits={ksum['total_decode_edits']}")
    return out


# --------------------------------------------------------------------------- #
# The two mandated sanity comparisons, computed in-process and persisted
# --------------------------------------------------------------------------- #
def compare_to_cache(run_cache_path: str, ref_run_dir: str) -> Dict:
    """||rep|| and full-vector agreement against a reference run's cache, per (prompt, layer).

    Two questions, one function:
      * with the knockout DISABLED, does this capture REPRODUCE the committed baseline? If it does
        not, the capture site or the layer convention is wrong and nothing downstream is readable.
      * with the knockout ENABLED, how many (prompt, layer) pairs actually CHANGED, and by how
        much? "It ran" is not evidence that it did anything.
    """
    ref_p = os.path.join(ref_run_dir, "cache", "final_occurrence_reps.pt")
    if not os.path.exists(ref_p):
        return {"error": f"no reference cache at {ref_p}"}
    a = torch.load(run_cache_path, map_location="cpu")
    b = torch.load(ref_p, map_location="cpu")
    if list(a["layers"]) != list(b["layers"]):
        return {"error": f"layer sets differ: {a['layers']} vs {b['layers']}"}
    if a.get("position") != b.get("position"):
        return {"error": f"positions differ: {a.get('position')} vs {b.get('position')}"}
    shared = sorted(set(a["reps"]) & set(b["reps"]))
    if not shared:
        return {"error": "no shared prompt_ids"}
    nl = len(a["layers"])
    import numpy as np

    def _agree(shift: int):
        """||rep||, vector and cosine agreement with the reference read `shift` layers over."""
        rn, rv, cs, changed, changed_big = [], [], [], 0, 0
        for pid in shared:
            x, y = a["reps"][pid].float(), b["reps"][pid].float()
            for j in range(nl):
                k = j + shift
                if not (0 <= k < nl):
                    continue
                ny = float(y[k].norm())
                rn.append(abs(float(x[j].norm()) - ny) / max(1e-9, ny))
                d = float((x[j] - y[k]).norm()) / max(1e-9, ny)
                rv.append(d)
                cs.append(float(torch.nn.functional.cosine_similarity(x[j], y[k], dim=0)))
                changed += int(d > 1e-3)
                changed_big += int(d > 1e-1)
        rn, rv, cs = np.array(rn), np.array(rv), np.array(cs)
        return {
            "n_pairs": int(rn.size),
            # TWO THRESHOLDS, BECAUSE ONE IS NOT ENOUGH. bf16 on two different GPU architectures
            # already disagrees by ~1.4% per element, so `> 1e-3` reads 1.0 even for a PERFECT
            # reproduction and can only ever be evidence of arithmetic, not of an intervention.
            # `> 1e-1` is the one that separates "the knockout changed the state" from "the kernels
            # rounded differently". Quote the cosine and the magnitudes, never the 1e-3 fraction.
            "frac_pairs_changed_gt_1e-1": float(changed_big) / float(rn.size),
            "relnorm_of_norm_max": float(rn.max()), "relnorm_of_norm_median": float(np.median(rn)),
            "relnorm_of_norm_q95": float(np.quantile(rn, 0.95)),
            "relnorm_of_vector_max": float(rv.max()), "relnorm_of_vector_median": float(np.median(rv)),
            "relnorm_of_vector_q95": float(np.quantile(rv, 0.95)),
            "cos_min": float(cs.min()), "cos_median": float(np.median(cs)),
            "cos_max": float(cs.max()),
            "frac_pairs_changed_gt_1e-3": float(changed) / float(rn.size),
        }

    out = {
        "reference_run": ref_run_dir,
        "n_shared_prompts": len(shared),
        "n_prompts_only_here": len(set(a["reps"]) - set(b["reps"])),
        "n_prompts_only_reference": len(set(b["reps"]) - set(a["reps"])),
    }
    out.update(_agree(0))
    # ⛔ THE OFF-BY-ONE CONTROL, AND IT IS THE POINT OF THIS FUNCTION. "max relative error 0.003"
    # is only evidence that the capture site is right if a WRONG capture site would have produced a
    # visibly worse number. Reading the reference one block over is the exact mistake the layer
    # convention exists to prevent (block L == hidden_states[L+1]), so it is measured rather than
    # argued: agreement at shift 0 must beat shift +/-1 by a wide margin, or the match at shift 0
    # is not informative about the convention at all.
    out["offbyone_control"] = {"shift_plus1": _agree(1), "shift_minus1": _agree(-1)}
    out["offbyone_verdict"] = (
        "PASS: shift 0 agrees far better than shift +/-1"
        if out["cos_median"] > max(out["offbyone_control"]["shift_plus1"]["cos_median"],
                                   out["offbyone_control"]["shift_minus1"]["cos_median"]) + 0.01
        else "INCONCLUSIVE: shift 0 is not clearly better than a one-block shift; this comparison "
             "cannot certify the layer convention")
    return out


# --------------------------------------------------------------------------- #
# --self-test: no GPU, no bank, no model
# --------------------------------------------------------------------------- #
def self_test() -> int:
    """Drive the REAL functions this file's correctness rests on, on CPU, with no bank.

    Each check is written so that BREAKING the thing it guards makes it fail — the repo's standing
    complaint about its own guards (a threshold mutated to `< 0.0` once left 44 tests green).
    """
    import types
    ok, fail = [], []

    def check(name, cond, detail=""):
        (ok if cond else fail).append(f"{name}{(' — ' + detail) if detail else ''}")

    # ---- T1  the layer convention, on a tensor that encodes its own index ------------------- #
    n_blocks, seq, H = 6, 4, 3
    hs = torch.stack([torch.full((seq, H), float(i)) for i in range(n_blocks + 1)], dim=0)
    got = pick_layer_rows(hs, [0, 2, 5], pos=1)
    check("T1 layer convention block L == hidden_states[L+1]",
          got.shape == (3, H) and [float(g[0]) for g in got] == [1.0, 3.0, 6.0],
          f"got {[float(g[0]) for g in got]}, want [1.0, 3.0, 6.0]")
    check("T1b convention string matches signals.LAYER_CONVENTION",
          "L+1" in sg.LAYER_CONVENTION or "hidden_states[L+1]" in sg.LAYER_CONVENTION,
          sg.LAYER_CONVENTION)

    # ---- T2  the key set is the demo block, deduplicated and sorted ------------------------- #
    keys = sb.knockout_key_set("demo_all", [9, 3, 5, 3], 20, 1234, protected={11, 12})
    check("T2 knockout_key_set('demo_all') == sorted(set(demo_keys))", keys == [3, 5, 9], str(keys))

    # ---- T3  the closed form vs the ACTUAL hook, on a synthetic 4-D mask -------------------- #
    pc = pair()
    stub_layers = [types.SimpleNamespace() for _ in range(4)]
    stub = types.SimpleNamespace(model=types.SimpleNamespace(layers=stub_layers),
                                 config=types.SimpleNamespace(num_attention_heads=8))
    S, blocked = 10, [2, 3, 7]
    stats: Dict[str, int] = {}
    hook = pc.AllQueryAttentionKnockout(stub, [0, 1], blocked_keys=blocked, heads=None, stats=stats)
    am = torch.zeros(1, 1, S, S)
    _, kw = hook._pre(None, (), {"attention_mask": am})
    # `AllQueryAttentionKnockout` writes no `n_prefill_edits`; score_behavior.knockout_row_stats
    # DERIVES it from `n_edits - n_decode_edits`, and that derivation is the one the gate reads.
    ks3 = sb.knockout_row_stats(stats)
    pred = expected_prefill_edit_rows(blocked, S)
    check("T3 expected_prefill_edit_rows matches the hook's own counter",
          ks3["n_prefill_edits"] == pred and pred == (10 - 2) + (10 - 3) + (10 - 7),
          f"hook={ks3['n_prefill_edits']} predicted={pred}")
    edited = kw["attention_mask"]
    mv = torch.finfo(am.dtype).min
    check("T3b the mask really was written (blocked cells are -inf, causal cells only)",
          bool((edited[0, 0, 2:, 2] == mv).all()) and bool(edited[0, 0, 0, 2] == 0.0) and
          bool((edited[0, 0, :, 4] == 0.0).all()),
          "blocked column not masked from its first causal row onward")

    # ---- T4  assert_row_edits FIRES on a dead hook, a partial band, and a wrong count -------- #
    dead = {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
            "n_edits": 0, "n_decode_edits": 0}
    try:
        assert_row_edits(dead, n_band_layers=2, expected_rows=pred, head_mult=None, prompt_id="x")
        check("T4 dead mask is refused", False, "assert_row_edits ACCEPTED n_prefill_edits == 0")
    except RuntimeError as e:
        check("T4 dead mask is refused", "MASK NEVER FIRED" in str(e))
    partial = {"n_forward": 1, "n_prefill_forward": 1, "n_decode_forward": 0,
               "n_edits": pred, "n_decode_edits": 0}
    try:
        assert_row_edits(partial, n_band_layers=2, expected_rows=pred, head_mult=None, prompt_id="x")
        check("T4b a band layer whose hook never fired is refused", False, "accepted 1 of 2 layers")
    except RuntimeError as e:
        check("T4b a band layer whose hook never fired is refused", "band layer" in str(e))
    wrong = {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
             "n_edits": 2 * pred - 1, "n_decode_edits": 0}
    try:
        assert_row_edits(wrong, n_band_layers=2, expected_rows=pred, head_mult=None, prompt_id="x")
        check("T4c an edit count the key set does not imply is refused", False, "accepted")
    except RuntimeError as e:
        check("T4c an edit count the key set does not imply is refused", "whole multiple" in str(e))
    good = {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
            "n_edits": 2 * pred, "n_decode_edits": 0}
    check("T4d a correct row passes and reports head_mult == 1",
          assert_row_edits(good, n_band_layers=2, expected_rows=pred, head_mult=None,
                           prompt_id="x") == 1)
    decoded = {"n_forward": 3, "n_prefill_forward": 2, "n_decode_forward": 1,
               "n_edits": 2 * pred + 5, "n_decode_edits": 5}
    try:
        assert_row_edits(decoded, n_band_layers=2, expected_rows=pred, head_mult=1, prompt_id="x")
        check("T4e a decode step in a forward-only capture is refused", False, "accepted")
    except RuntimeError as e:
        check("T4e a decode step in a forward-only capture is refused", "SINGLE-FORWARD" in str(e))

    # ---- T5  the run-level gate: score_behavior's own accumulator and assertion -------------- #
    live = sb.new_knockout_live()
    for _ in range(4):
        sb.record_knockout_row(live, KNOCKOUT_SCOPE,
                               {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
                                "n_edits": 2 * pred, "n_decode_edits": 0},
                               n_demo_positions=3, readout=True)
    s_ok = sb.knockout_liveness_summary(live, "eager", scope=KNOCKOUT_SCOPE, readout=True)
    check("T5 a live forward-only run passes assert_knockout_live",
          sb.assert_knockout_live(s_ok) is True and s_ok["frac_rows_scope_live"] == 1.0,
          json.dumps({k: s_ok[k] for k in ("n_rows", "frac_rows_scope_live", "total_prefill_edits")}))
    dead_live = sb.new_knockout_live()
    for _ in range(4):
        sb.record_knockout_row(dead_live, KNOCKOUT_SCOPE,
                               {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
                                "n_edits": 0, "n_decode_edits": 0},
                               n_demo_positions=3, readout=True)
    s_dead = sb.knockout_liveness_summary(dead_live, "eager", scope=KNOCKOUT_SCOPE, readout=True)
    try:
        sb.assert_knockout_live(s_dead)
        check("T5b a run whose mask never fired is REFUSED", False, "assert_knockout_live passed")
    except SystemExit:
        check("T5b a run whose mask never fired is REFUSED", True)
    empty = sb.knockout_liveness_summary(sb.new_knockout_live(), "eager",
                                         scope=KNOCKOUT_SCOPE, readout=True)
    try:
        sb.assert_knockout_live(empty)
        check("T5c a run with zero rows is REFUSED", False, "zero rows passed")
    except SystemExit:
        check("T5c a run with zero rows is REFUSED", True)

    # ---- T6  the cache payload has exactly the keys the FROZEN analyzer reads ---------------- #
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "final_occurrence_reps.pt")
        torch.save({"layers": [6, 7], "layer_convention": sg.LAYER_CONVENTION,
                    "position": "codeword_last", "dtype": "float16",
                    "reps": {"a": torch.zeros(2, 4).half()}}, p)
        blob = torch.load(p, map_location="cpu")
        check("T6 cache payload keys match extract_boombness.py:729",
              set(blob) == {"layers", "layer_convention", "position", "dtype", "reps"},
              str(sorted(blob)))
        q = os.path.join(td, "ref")
        os.makedirs(os.path.join(q, "cache"))
        torch.save({"layers": [6, 7], "layer_convention": sg.LAYER_CONVENTION,
                    "position": "codeword_last", "dtype": "float16",
                    "reps": {"a": torch.zeros(2, 4).half(), "b": torch.ones(2, 4).half()}},
                   os.path.join(q, "cache", "final_occurrence_reps.pt"))
        cmp_ = compare_to_cache(p, q)
        check("T6b compare_to_cache reports identical states as identical",
              cmp_["relnorm_of_vector_max"] == 0.0 and cmp_["frac_pairs_changed_gt_1e-3"] == 0.0
              and cmp_["n_prompts_only_reference"] == 1, json.dumps(cmp_))
        # T6c: the off-by-one control must FIRE on a cache that really is shifted by one block.
        r2 = os.path.join(td, "ref2")
        os.makedirs(os.path.join(r2, "cache"))
        base = torch.stack([torch.randn(8) * (i + 1) for i in range(3)])
        torch.save({"layers": [6, 7, 8], "layer_convention": sg.LAYER_CONVENTION,
                    "position": "codeword_last", "dtype": "float16",
                    "reps": {"a": base.half()}}, os.path.join(r2, "cache",
                                                              "final_occurrence_reps.pt"))
        shifted = os.path.join(td, "shifted.pt")
        torch.save({"layers": [6, 7, 8], "layer_convention": sg.LAYER_CONVENTION,
                    "position": "codeword_last", "dtype": "float16",
                    "reps": {"a": torch.stack([base[1], base[2], base[0]]).half()}}, shifted)
        good = compare_to_cache(os.path.join(r2, "cache", "final_occurrence_reps.pt"), r2)
        bad_ = compare_to_cache(shifted, r2)
        check("T6c the off-by-one control PASSES on an aligned cache",
              good["offbyone_verdict"].startswith("PASS"), good["offbyone_verdict"])
        check("T6d the off-by-one control REFUSES a cache shifted by one block",
              bad_["offbyone_verdict"].startswith("INCONCLUSIVE"), bad_["offbyone_verdict"])

    # ---- T8  --knockout-scope: the SCOPED closed form, and the gate that must still fire ---- #
    #
    # ⛔ WHICH GATE THIS FILE USES FOR THE SCOPED PATH, STATED PLAINLY: the EXACT closed form, not
    # the weaker ">0 and < legacy" fallback. `ScopedAttentionKnockout` filters the legacy
    # candidate rows through `resolve_scoped_query_rows`, so the cell count is
    # `sum_kp |{r in allowed : kp <= r < seq_len}|` — derived, and checked HERE against the REAL
    # hook's own counter rather than against a second copy of the arithmetic. The ">0 and strictly
    # less than legacy" check is kept ON TOP (`assert_scope_narrows`), because it is the only one
    # that still fires if the scope silently degraded to `legacy_all_query` — then the prediction
    # and the counter would move together and the exact form would agree with itself.
    S8, blocked8 = 10, [2, 3, 7]
    q8, surf8 = frozenset({5, 6, 8, 9}), frozenset({8, 9})
    legacy8 = expected_prefill_edit_rows(blocked8, S8)
    check("T8 the generalised form REDUCES to the legacy one on the all-rows set",
          expected_prefill_edit_rows(blocked8, S8, allowed_rows=frozenset(range(S8))) == legacy8
          and legacy8 == (10 - 2) + (10 - 3) + (10 - 7), f"legacy={legacy8}")

    st8: Dict[str, int] = {}
    hook8 = pc.ScopedAttentionKnockout(stub, [0, 1], blocked_keys=blocked8,
                                       mode=SURFACE_SCOPE, query_span=q8, demo_span=frozenset(),
                                       heads=None, stats=st8, surface_span=surf8)
    _, _ = hook8._pre(None, (), {"attention_mask": torch.zeros(1, 1, S8, S8)})
    ks8 = sb.knockout_row_stats(st8)
    pred8 = expected_prefill_edit_rows(blocked8, S8, allowed_rows=surf8)
    check("T8b the SCOPED closed form matches the REAL ScopedAttentionKnockout counter",
          ks8["n_prefill_edits"] == pred8 and pred8 == 6,
          f"hook={ks8['n_prefill_edits']} predicted={pred8}")

    e_l, f_l, l_l, a_l = expected_prefill_edits_for_scope(pc, LEGACY_SCOPE, blocked8, S8,
                                                          query_span=q8, demo_span=frozenset(),
                                                          surface_span=surf8)
    check("T8c the LEGACY closed form is STILL the one applied when scope == legacy_all_query",
          f_l == "legacy_closed_form" and a_l is None and e_l == l_l == legacy8,
          f"form={f_l} expected={e_l} legacy={l_l} allowed={a_l}")
    e_s, f_s, l_s, a_s = expected_prefill_edits_for_scope(pc, SURFACE_SCOPE, blocked8, S8,
                                                          query_span=q8, demo_span=frozenset(),
                                                          surface_span=surf8)
    check("T8d the scoped form is used for target_surface_row_only and edits STRICTLY fewer cells",
          f_s == "scoped_closed_form" and e_s == pred8 and l_s == legacy8 and 0 < e_s < l_s
          and a_s == surf8, f"form={f_s} expected={e_s} legacy={l_s}")

    # ---- T8e  THE NEW SCOPE'S ZERO-ROW CASE MUST FIRE ---------------------------------------- #
    # The surface occurrence sits BEFORE every demonstration key, so causality leaves the scope no
    # row to cut: the span resolves (it is non-empty, so `scoped_span_is_dead` is False and the
    # hook's constructor is satisfied) and the mask still edits NOTHING. That is the silent no-op
    # in its scoped disguise, and it must be refused rather than captured.
    S9, blocked9 = 10, [7, 8]
    q9, surf9 = frozenset({5, 6}), frozenset({5})
    st9: Dict[str, int] = {}
    hook9 = pc.ScopedAttentionKnockout(stub, [0], blocked_keys=blocked9, mode=SURFACE_SCOPE,
                                       query_span=q9, demo_span=frozenset(), heads=None,
                                       stats=st9, surface_span=surf9)
    _, _ = hook9._pre(None, (), {"attention_mask": torch.zeros(1, 1, S9, S9)})
    ks9 = sb.knockout_row_stats(st9)
    pred9 = expected_prefill_edit_rows(blocked9, S9, allowed_rows=surf9)
    check("T8e the scoped mask really CAN edit zero rows, and the closed form predicts it",
          ks9["n_prefill_edits"] == 0 and pred9 == 0
          and not sb.scoped_span_is_dead(SURFACE_SCOPE, q9, frozenset(), surf9),
          f"hook={ks9['n_prefill_edits']} predicted={pred9}")
    try:
        assert_row_edits({"n_forward": 1, "n_prefill_forward": 1, "n_decode_forward": 0,
                          "n_edits": 0, "n_decode_edits": 0},
                         n_band_layers=1, expected_rows=pred9, head_mult=None, prompt_id="z")
        check("T8f a scoped mask that edits ZERO rows is REFUSED", False, "assert_row_edits passed")
    except RuntimeError as e:
        check("T8f a scoped mask that edits ZERO rows is REFUSED",
              "ZERO editable mask cells" in str(e), str(e)[:80])
    try:
        assert_scope_narrows(SURFACE_SCOPE, pred9, expected_prefill_edit_rows(blocked9, S9), "z")
        check("T8g assert_scope_narrows refuses a scope that resolves to no cells", False,
              "accepted 0 cells")
    except RuntimeError as e:
        check("T8g assert_scope_narrows refuses a scope that resolves to no cells",
              "ZERO editable mask cells" in str(e))
    try:
        assert_scope_narrows(SURFACE_SCOPE, legacy8, legacy8, "z")
        check("T8h a 'surgical' scope that did NOT narrow is refused", False, "accepted")
    except RuntimeError as e:
        check("T8h a 'surgical' scope that did NOT narrow is refused", "not narrow" in str(e))
    check("T8i assert_scope_narrows is a NO-OP on the legacy scope (default path untouched)",
          assert_scope_narrows(LEGACY_SCOPE, legacy8, legacy8, "z") is None)

    # ---- T8j  the run-level gate, on the SCOPED contract -------------------------------------- #
    live8 = sb.new_knockout_live()
    for _ in range(4):
        sb.record_knockout_row(live8, SURFACE_SCOPE,
                               {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
                                "n_edits": 2 * pred8, "n_decode_edits": 0},
                               n_demo_positions=3, readout=True)
    s8_ok = sb.knockout_liveness_summary(live8, "eager", scope=SURFACE_SCOPE, readout=True)
    check("T8j a live target_surface_row_only run passes assert_knockout_live on ITS contract",
          sb.assert_knockout_live(s8_ok) is True and s8_ok["frac_rows_scope_live"] == 1.0,
          json.dumps({k: s8_ok[k] for k in ("n_rows", "frac_rows_scope_live",
                                            "total_prefill_edits")}))
    leak = sb.new_knockout_live()
    for _ in range(4):
        sb.record_knockout_row(leak, SURFACE_SCOPE,
                               {"n_forward": 3, "n_prefill_forward": 2, "n_decode_forward": 1,
                                "n_edits": 2 * pred8 + 3, "n_decode_edits": 3},
                               n_demo_positions=3, readout=True)
    s8_leak = sb.knockout_liveness_summary(leak, "eager", scope=SURFACE_SCOPE, readout=True)
    try:
        sb.assert_knockout_live(s8_leak)
        check("T8k a scoped run that leaked decode edits is REFUSED", False, "leak passed")
    except SystemExit:
        check("T8k a scoped run that leaked decode edits is REFUSED", True)

    # ---- T8l  the empty span is a CRASH, not a clean null ------------------------------------ #
    try:
        pc.ScopedAttentionKnockout(stub, [0], blocked_keys=blocked8, mode=SURFACE_SCOPE,
                                   query_span=q8, demo_span=frozenset(), heads=None, stats={},
                                   surface_span=None)
        check("T8l dropping surface_span is refused by the hook, not silently demoted", False,
              "constructed with surface_span=None")
    except ValueError as e:
        check("T8l dropping surface_span is refused by the hook, not silently demoted",
              "no-op knockout" in str(e))

    # ---- T8m  scopes this forward-only path cannot satisfy are refused at argument time ------- #
    for _bad_scope, _why in (("decode_only", "edits nothing without a decode step"),
                             ("response_query_only", "would perform query_prefill_only")):
        try:
            sb.readout_liveness_contract(_bad_scope)
            check(f"T8m {_bad_scope} is refused ({_why})", False, "contract returned")
        except SystemExit:
            check(f"T8m {_bad_scope} is refused ({_why})", True)
    check("T8n target_surface_row_only IS satisfiable here, and on the reduced contract",
          sb.readout_liveness_contract(SURFACE_SCOPE) ==
          (("n_prefill_edits", "n_prefill_forward"), ("n_decode_edits",)),
          str(sb.readout_liveness_contract(SURFACE_SCOPE)))

    # ---- T7  row selection ------------------------------------------------------------------ #
    rws = [{"prompt_id": f"p{i}", "demo_block": ("" if i % 2 else "D")} for i in range(10)]
    sel = select_rows(rws, smoke=3, limit=0, knockout=True)
    check("T7 --smoke picks rows that CAN carry the knockout",
          [r["prompt_id"] for r in sel] == ["p0", "p2", "p4"], str([r["prompt_id"] for r in sel]))
    check("T7b --smoke picks the SAME rows with and without the knockout (comparability)",
          [r["prompt_id"] for r in select_rows(rws, 3, 0, False)] == ["p0", "p2", "p4"],
          str([r["prompt_id"] for r in select_rows(rws, 3, 0, False)]))
    nodemo = [{"prompt_id": f"q{i}", "demo_block": ""} for i in range(4)]
    check("T7c a knocked-out smoke over demo-less rows selects NOTHING (and main() refuses)",
          select_rows(nodemo, 2, 0, True) == [] and len(select_rows(nodemo, 2, 0, False)) == 2)

    print("\n".join(f"  PASS  {t}" for t in ok))
    if fail:
        print("\n".join(f"  FAIL  {t}" for t in fail))
        print(f"SELF-TEST FAILED: {len(fail)} of {len(ok) + len(fail)}")
        return 1
    print(f"SELF-TEST PASSED: {len(ok)}/{len(ok)} checks")
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true",
                    help="run every CPU-checkable guard in this file; no GPU, no bank, no model")
    # --- mirrors extract_boombness where they overlap ------------------------------------- #
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--layers", default="6,7,8,9,10,11,12,13,14",
                    help="'all' or a comma list of BLOCK indices (PR-035 used 6..14)")
    ap.add_argument("--position", default="codeword_last", choices=["codeword_last", "last"])
    ap.add_argument("--model", default=None, help="default = ds_common.PRIMARY_MODEL")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--seed", type=int, default=20260905)
    ap.add_argument("--tag", default="bombspecko",
                    help="run-dir tag. Keep it DISTINCT from `bombspec`: the frozen analyzer and "
                         "the verifier resolve baseline runs by globbing `bombspec_<cw>_<cc>_*`, "
                         "and a knocked-out run answering that glob would silently replace the "
                         "baseline it is meant to be compared against.")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--enable-thinking", default=None, choices=[None, "true", "false"])
    # --- this file's own ------------------------------------------------------------------- #
    ap.add_argument("--band", default=DEFAULT_BAND,
                    help="attention-knockout band as lo-hi BLOCK indices (default 6-14)")
    ap.add_argument("--arm", default="demo_all",
                    help=f"knockout arm; known: {sb.KNOCKOUT_ARMS}")
    ap.add_argument("--knockout-scope", default=LEGACY_SCOPE,
                    choices=list(pair().SCOPED_KNOCKOUT_MODES),
                    help="WHICH QUERY ROWS are blocked from reading the demonstration keys. "
                         f"Default {LEGACY_SCOPE!r} = every query row = the scope that produced "
                         "R-093, and on that default this file constructs the same "
                         "AllQueryAttentionKnockout object and applies the same legacy closed-form "
                         "liveness gate it always did. 'target_surface_row_only' is gate R6's KO-1: "
                         "only the rows of the FINAL target_surface occurrence in the query (the "
                         "CODEWORD in cells A/C/D/F, the CONCEPT word in cells B/E — one scope, one "
                         "dose, both experiments). Scopes with no prefill rows, or whose prefill "
                         "half duplicates another mode, are refused at argument time.")
    ap.add_argument("--attn-impl", default="eager", choices=["eager", "sdpa"],
                    help="FORCED to eager whenever the knockout is live: under SDPA the additive "
                         "mask edit is discarded and the knockout is a silent no-op. `sdpa` is "
                         "accepted ONLY with --no-knockout, as a baseline-parity diagnostic.")
    ap.add_argument("--no-knockout", action="store_true",
                    help="capture with NO hooks. This is the baseline-reproduction control: it "
                         "must reproduce the committed extract_boombness cache.")
    ap.add_argument("--on-no-demo-block", default="skip", choices=["skip", "fail"],
                    help="n_examples==0 rows have no demonstrations to knock out. Default: ledger "
                         "and skip (they are ABSENT from the cache, by design).")
    ap.add_argument("--smoke", type=int, default=0,
                    help="run only N prompts (that can carry the knockout), as a pre-flight")
    ap.add_argument("--compare-baseline", default="",
                    help="an extract_boombness run dir; its cache is compared against this run's, "
                         "per (prompt, layer), and the numbers are written to summary.json")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    knockout = not args.no_knockout
    scope = args.knockout_scope
    if knockout:
        if scope in SCOPES_NOT_SUPPORTED_HERE:
            raise SystemExit(
                f"REFUSING: --knockout-scope {scope!r} takes its row set verbatim from the "
                f"consumer, and score_behavior.py owns that definition (--knockout-last-k). "
                f"Adding a second 'last K' here would be a second definition of K.")
        # ⛔ THE ARGUMENT-TIME REFUSAL, AND IT IS NOT THIS FILE'S OPINION. `readout_liveness_contract`
        # asks the hook's OWN row resolver whether the mode can fire at all on a path with no
        # decode step, and refuses `decode_only` (edits nothing here) and `response_query_only`
        # (stripped of its decode half it performs `query_prefill_only` under another name). It
        # also returns the reduced contract this run will be judged on, which is printed below.
        _req, _zero = sb.readout_liveness_contract(scope)
    elif scope != LEGACY_SCOPE:
        raise SystemExit(
            f"REFUSING: --no-knockout with --knockout-scope {scope!r}. The baseline capture applies "
            f"no hook at all, so a run naming a scope it never performed is exactly the artifact "
            f"that gets read three weeks later as evidence that it did. Drop one of the two flags.")
    if knockout and args.attn_impl != "eager":
        raise SystemExit("REFUSING: --attn-impl sdpa with the knockout live. Under SDPA the custom "
                         "mask is discarded silently and the run would be an un-knocked-out "
                         "baseline filed under a knockout name.")
    attn_impl = "eager" if knockout else args.attn_impl
    args._enable_thinking = dc_parse_thinking(args.enable_thinking)
    seed_everything(args.seed)

    dc, pc = ds(), pair()
    all_rows = read_jsonl(args.bank)
    rows = select_rows(all_rows, args.smoke, args.limit, knockout)
    if not rows:
        raise SystemExit(f"no rows selected from {args.bank}")

    run = RunDir("extract_boombness", args, tag=args.tag, want_cache=True)
    ledger = FailureLedger()
    model_id = args.model or dc.PRIMARY_MODEL
    lm = dc.load_model(model_id, dtype=getattr(torch, args.dtype), attn_implementation=attn_impl)
    # RE-CHECK ON THE LOADED CONFIG, not on the string we asked for (score_behavior.py:1634). A
    # transformers version that silently substitutes an implementation must fail here.
    if knockout and getattr(getattr(lm.model, "config", None), "_attn_implementation",
                            "eager") != "eager":
        raise SystemExit("REFUSING: the model did not load with attn_implementation='eager'; the "
                         "mask edit would be discarded silently.")

    run.note_bank(args.bank)
    run.note_model(lm.model_id, revision=lm.revision, dtype=str(lm.dtype),
                   attn_implementation=attn_impl, num_layers=lm.num_layers,
                   hidden_size=lm.hidden_size, tokenizer_obj=lm.tokenizer, model_obj=lm.model)
    args._bank_file_sha16 = run._extra_meta.get("bank_file_sha16")

    layers = (list(range(lm.num_layers)) if args.layers == "all"
              else [int(x) for x in args.layers.split(",") if x.strip() != ""])
    lo, hi = (int(x) for x in args.band.split("-"))
    band = list(range(lo, hi + 1))
    # BAND RANGE CHECK AND ECHO (score_behavior.py:1700's finding S3): a band copied from a model
    # of a different depth fails SILENTLY as a weaker knockout, and no exception can catch that.
    if not (0 <= lo <= hi):
        raise SystemExit(f"REFUSING: malformed --band {args.band!r} (need 0 <= lo <= hi)")
    if hi >= lm.num_layers:
        raise SystemExit(f"REFUSING: --band {args.band!r} addresses block {hi} but {model_id} has "
                         f"only {lm.num_layers} blocks (0-{lm.num_layers - 1}).")
    if max(layers) >= lm.num_layers:
        raise SystemExit(f"REFUSING: --layers asks for block {max(layers)} of {lm.num_layers}")
    if knockout and args.arm not in sb.KNOCKOUT_ARMS:
        raise SystemExit(f"REFUSING: unknown arm {args.arm!r}; known: {sb.KNOCKOUT_ARMS}")

    print(f"[ko-extract] model={lm.model_id} blocks={lm.num_layers} hidden={lm.hidden_size} "
          f"attn={attn_impl}")
    print(f"[ko-extract] capture layers={layers} position={args.position}")
    if knockout:
        print(f"[ko-extract] KNOCKOUT LIVE: arm={args.arm} scope={scope} "
              f"band {args.band} -> blocks {lo}..{hi} of {lm.num_layers} "
              f"({hi - lo + 1} blocks, depth {lo / lm.num_layers:.3f}-"
              f"{(hi + 1) / lm.num_layers:.3f}); liveness required > 0: "
              f"{list(pc.LIVENESS_REQUIREMENT[scope])}, required == 0: "
              f"{list(pc.LIVENESS_MUST_BE_ZERO[scope])}", flush=True)
        # The FORWARD-ONLY reduction of that contract is what rows are actually judged on here, so
        # it is printed too rather than left to be inferred from the mode table.
        print(f"[ko-extract] forward-only readout contract for {scope}: required > 0 {list(_req)}, "
              f"required == 0 {list(_zero)}; per-row closed form: "
              f"{'legacy' if scope == LEGACY_SCOPE else 'scoped'}", flush=True)
    else:
        print("[ko-extract] KNOCKOUT DISABLED (--no-knockout): baseline-reproduction control",
              flush=True)

    # `band` / `arm` are recorded as None on a baseline pass rather than echoing their argparse
    # defaults: a metadata block that names an arm and a band a run never applied is exactly the
    # kind of artifact that gets read three weeks later as evidence that it did.
    run.note(layers=layers, band=(band if knockout else None),
             band_str=(args.band if knockout else None), arm=(args.arm if knockout else None),
             knockout_applied=knockout, knockout_scope=(scope if knockout else None),
             position=args.position, attn_implementation=attn_impl,
             n_bank_rows_used=len(rows), smoke=int(args.smoke or 0),
             layer_convention=sg.LAYER_CONVENTION)

    summary = {"model": lm.model_id, "n_bank_rows": len(all_rows),
               "n_bank_rows_used": len(rows), "layers": layers, "position": args.position,
               "attn_implementation": attn_impl, "activation_dtype": str(lm.dtype),
               "bank_file_sha16": run._extra_meta.get("bank_file_sha16"),
               "bank_rows_sha16": run._extra_meta.get("bank_rows_sha16"),
               "bank_n_rows": run._extra_meta.get("bank_n_rows")}
    summary.update(capture(lm, dc, pc, rows, layers, band, run, ledger, args))

    if args.compare_baseline:
        cp = os.path.join(run.cache, "final_occurrence_reps.pt")
        if os.path.exists(cp):
            cmp_ = compare_to_cache(cp, args.compare_baseline)
            summary["baseline_comparison"] = cmp_
            print("[ko-extract] baseline comparison: " + json.dumps(cmp_, indent=2))

    run.finish(summary=summary, ledger=ledger)
    print(f"[ko-extract] -> {run.path}")
    print(f"[ko-extract] failures: {ledger.as_dict()['failure_reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
