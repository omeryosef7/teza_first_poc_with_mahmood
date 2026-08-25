"""Knockout liveness on the FORWARD-ONLY READOUT path (correction C-6).

THE DEFECT. `record_knockout_row` was called in exactly one place: inside the `behavioral` branch,
after `dc.generate`. The two forward-only readout branches -- `_semantic` and `_comprehension`,
which is what `--query-kinds semantic_one_word` scores -- ledgered NOTHING. The hook was applied
(both readouts run inside the `contextlib.ExitStack` that entered the intervention contexts), it
edited the mask, and then the run reported `knock_live["n_rows"] == 0` and `assert_knockout_live`
voided it in 20 seconds:

    "REFUSING: knockout liveness has zero rows -- the run generated nothing, so the mask was never
     observed to fire. This is not a pass."

THE GATE WAS RIGHT. An intervention nobody observed is not an intervention anybody may report, and
the fix is emphatically NOT to exempt the readout path. It is to (a) ledger it, through the SAME
accumulator, and (b) judge it against the SAME mode contract, reduced only where the absence of a
decode step makes a counter unreachable -- with `n_prefill_forward` added as the proof-of-life
counter that replaces it. Without that addition the "reduction" would be an exemption: a hook that
was never entered at all would be indistinguishable from one that was correctly scoped and had
nothing to edit. `test_a_DEAD_hook_still_FAILS_on_the_readout_path` is the test that pins this, and
`test_dead_and_scoped_empty_are_DISTINGUISHABLE` pins that the two cases are told apart.

STRUCTURAL LIMITS. A forward-only readout has no decode step, so `decode_only` (which edits nothing
at prefill) and `response_query_only` (which, stripped of its decode half, edits exactly the rows
`query_prefill_only` edits, and would therefore be filed under a name that misdescribes it) are
REFUSED, at argument time, before the model is loaded. `legacy_all_query`, `query_prefill_only` and
`demo_processing_only` are measurable and are admitted. Which is which is DERIVED here from the
hook's own row resolver, never restated: see `readout_liveness_contract`.

Nothing in this file re-types a per-mode liveness rule. Every verdict comes from the shipped
`sb.record_knockout_row` / `sb.knockout_liveness_summary` / `sb.assert_knockout_live`, and every
mode list comes from `pair_common`, which is what makes these tests go red on a mutated
implementation instead of green on a restated one.

Run:  python -m pytest tests/test_readout_liveness.py -q
"""
import ast
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "boombness", "score_behavior.py")

DEMO = [11, 12, 13, 14, 15]
PROT = {40, 41, 42, 43}


def _pc():
    from common import pair
    return pair()


def _src():
    return open(SRC).read()


def _main_fn():
    """The `main` FunctionDef of score_behavior, for structural assertions about the loop."""
    tree = ast.parse(_src())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "main")
    return fn


# --------------------------------------------------------------------------- #
# fake per-row hook counters. A FORWARD-ONLY readout: exactly one prefill forward
# per row and NO decode forward at all -- which is the whole difficulty.
# --------------------------------------------------------------------------- #
def _readout_stats(prefill_edits=500, prefill_forward=1, decode_edits=0, decode_forward=0):
    return {"n_forward": prefill_forward + decode_forward,
            "n_prefill_forward": prefill_forward, "n_decode_forward": decode_forward,
            "n_edits": prefill_edits + decode_edits,
            "n_prefill_edits": prefill_edits, "n_decode_edits": decode_edits}


def _gen_stats(prefill_edits=500, decode_edits=192, prefill_forward=1, decode_forward=192):
    """The GENERATION path's counters, for the unchanged-behaviour tests."""
    return _readout_stats(prefill_edits, prefill_forward, decode_edits, decode_forward)


def _readout_summary(scope, stats, n_rows=96):
    """Build the summary exactly the way main() does on the readout path: through the SHIPPED
    accumulator, so a drift in the per-row rule turns these red rather than leaving them green."""
    import score_behavior as sb
    live = sb.new_knockout_live()
    for _ in range(n_rows):
        sb.record_knockout_row(live, scope, dict(stats), n_demo_positions=len(DEMO), readout=True)
    return live, sb.knockout_liveness_summary(live, "eager", scope=scope, readout=True)


def _measurable():
    """The modes `readout_liveness_contract` admits -- asked of the code, not listed here."""
    import score_behavior as sb
    out = []
    for m in _pc().SCOPED_KNOCKOUT_MODES:
        try:
            sb.readout_liveness_contract(m, ["semantic_one_word"])
        except SystemExit:
            continue
        out.append(m)
    return out


# --------------------------------------------------------------------------- #
# 0. THE FACT ESTABLISHED IN STEP 1: the readouts run INSIDE the intervention
# --------------------------------------------------------------------------- #
def test_the_readouts_run_INSIDE_the_intervention_contexts():
    """If they did not, every forward-only "intervention" ever produced was a baseline.

    Pinned structurally: the `_semantic` / `_comprehension` calls must be nested inside the `with
    contextlib.ExitStack()` block that enters the contexts `make_intervention` built.
    """
    withs = [n for n in ast.walk(_main_fn())
             if isinstance(n, ast.With)
             and "ExitStack" in (ast.get_source_segment(_src(), n.items[0].context_expr) or "")]
    assert withs, "the ExitStack that enters the intervention contexts is gone from main()"
    inside = "\n".join(ast.get_source_segment(_src(), b) for w in withs for b in w.body)
    assert "st.enter_context(c)" in inside, "the contexts are no longer entered in that block"
    for call in ("_semantic(templated)", "_comprehension(templated)"):
        assert call in inside, \
            (f"{call} is NOT inside the intervention ExitStack -- the forward-only readout would "
             f"be running UNHOOKED, i.e. as a baseline filed under an intervention's name")


# --------------------------------------------------------------------------- #
# 1. the readout path LEDGERS, and a live prefill-scoped hook PASSES the gate
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("scope", ["query_prefill_only", "demo_processing_only",
                                   "legacy_all_query"])
def test_a_prefill_scoped_readout_ledgers_rows_and_PASSES(scope):
    """THE CASE THAT DIED IN 20 SECONDS. Zero decode edits is CORRECT here: there is no decode."""
    import score_behavior as sb
    live, s = _readout_summary(scope, _readout_stats(prefill_edits=500))
    assert live["n_rows"] == 96, "the readout path ledgered nothing -- this is the C-6 defect"
    assert s["n_rows"] == 96
    assert s["liveness_readout_only"] is True
    assert s["frac_rows_scope_live"] == 1.0
    assert s["total_decode_edits"] == 0, "a forward-only readout cannot have decode edits"
    assert sb.assert_knockout_live(s) is True


def test_the_readout_branches_actually_call_the_shipped_accumulator():
    """`n_rows` can only move if the branches ledger. Deleting either call turns this red."""
    src = _src()
    fn = next(n for n in ast.walk(_main_fn())
              if isinstance(n, ast.FunctionDef) and n.name == "_readout_knock_fields")
    body = ast.get_source_segment(src, fn)
    assert "record_knockout_row(" in body and "readout=True" in body, \
        "the readout ledger no longer goes through record_knockout_row -- a second accounting path"
    dispatch = [n for n in ast.walk(_main_fn())
                if isinstance(n, ast.If)
                and 'row["query_kind"]' in (ast.get_source_segment(src, n.test) or "")]
    assert dispatch, "the query_kind dispatch is gone from main()"
    seen = sum((ast.get_source_segment(src, n) or "").count("_readout_knock_fields(")
               for n in dispatch)
    assert seen >= 2, ("the semantic and comprehension branches do not both ledger the hook; "
                       f"found {seen} call(s)")


def test_EVERY_scoring_branch_of_the_dispatch_ledgers_the_hook():
    """THE GENERAL INVARIANT, not just the two branches known to have been broken.

    Any branch of the query_kind dispatch that writes a row must also fold that row into the
    liveness accumulator. C-6 was exactly one branch doing the first and not the second, and a
    sixth query kind added tomorrow would repeat it silently -- the run would simply report fewer
    rows than it scored, and `frac_rows_scope_live` would describe a subset nobody declared.
    """
    src = _src()
    dispatch = [n for n in ast.walk(_main_fn())
                if isinstance(n, ast.If)
                and 'row["query_kind"]' in (ast.get_source_segment(src, n.test) or "")]
    assert dispatch, "the query_kind dispatch is gone from main()"
    unledgered = []
    for node in dispatch:
        seg = "\n".join(ast.get_source_segment(src, b) or "" for b in node.body)
        if "run.log_row(" not in seg:
            continue
        if "record_knockout_row(" not in seg and "_readout_knock_fields(" not in seg:
            unledgered.append((ast.get_source_segment(src, node.test) or "")[:80])
    assert not unledgered, \
        f"branch(es) score a row without ledgering the hook -- this is the C-6 defect: {unledgered}"


def test_ONE_accounting_path_only():
    """record_knockout_row stays the single place a row is folded into the accumulator."""
    src = _src()
    body = "\n".join(l for l in src.splitlines()
                     if 'knock_live["n_rows"] +=' in l or 'knock_live["n_rows"] =' in l)
    assert body.count("+=") == 1, \
        "n_rows is incremented in more than one place -- a second accounting path was added"


# --------------------------------------------------------------------------- #
# 2. modes that NEED a decode step refuse, naming the query kind
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("scope", ["decode_only", "response_query_only"])
def test_a_decode_scoped_mode_REFUSES_on_a_forward_only_readout(scope):
    import score_behavior as sb
    with pytest.raises(SystemExit) as e:
        sb.readout_liveness_contract(scope, ["semantic_one_word"])
    msg = str(e.value)
    assert "semantic_one_word" in msg, "the refusal does not name the query kind that caused it"
    assert scope in msg


def test_the_response_query_refusal_names_the_mode_to_use_instead():
    """Its readout reduction IS query_prefill_only; filing it under its own name misdescribes it."""
    import score_behavior as sb
    with pytest.raises(SystemExit, match="query_prefill_only"):
        sb.readout_liveness_contract("response_query_only", ["comprehension_usage"])


@pytest.mark.parametrize("scope", ["decode_only", "response_query_only"])
def test_an_unsatisfiable_mode_cannot_sneak_through_the_row_recorder(scope):
    """Not just the argument-time guard: the per-row path refuses too, so no vacuous pass."""
    import score_behavior as sb
    live = sb.new_knockout_live()
    with pytest.raises(SystemExit):
        sb.record_knockout_row(live, scope, _readout_stats(), readout=True)


def test_the_refusal_happens_at_ARGUMENT_TIME_before_the_model_loads():
    """A 20-second death after a model load is the failure this correction is about."""
    src = _src()
    i = src.index("_rreq, _rzero = readout_liveness_contract(_knock_scope")
    j = src.index("lm = dc.load_model(")
    assert i < j, "the readout feasibility check moved after the model load"
    assert "REFUSING" in src[src.index("_readout_kinds and _decode_kinds"):
                             src.index("_readout_kinds and _decode_kinds") + 400], \
        "mixing readout and generating kinds under one knockout no longer refuses"


# --------------------------------------------------------------------------- #
# 3. A DEAD HOOK STILL FAILS. The test that proves the path was not exempted.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("scope", ["query_prefill_only", "demo_processing_only",
                                   "legacy_all_query"])
def test_a_DEAD_hook_still_FAILS_on_the_readout_path(scope):
    """Zero prefill edits AND zero prefill forwards: the hook was never entered at all."""
    import score_behavior as sb
    bad = sb.readout_liveness_violations(scope, _readout_stats(prefill_edits=0, prefill_forward=0))
    assert bad, f"a completely dead hook was judged LIVE under {scope} on the readout path"
    assert any("n_prefill_forward" in b for b in bad), \
        "the readout contract does not consult the one counter that proves the hook ran"
    _live, s = _readout_summary(scope, _readout_stats(prefill_edits=0, prefill_forward=0))
    assert s["frac_rows_scope_live"] == 0.0
    with pytest.raises(SystemExit, match="liveness contract"):
        sb.assert_knockout_live(s)


@pytest.mark.parametrize("scope", ["query_prefill_only", "demo_processing_only",
                                   "legacy_all_query"])
def test_dead_and_scoped_empty_are_DISTINGUISHABLE(scope):
    """"Never fired" and "ran, correctly scoped, edited nothing" are different diagnoses.

    Both fail -- neither is reportable -- but the violation strings must say which happened, and
    the discriminator on this path is `n_prefill_forward`.
    """
    import score_behavior as sb
    dead = sb.readout_liveness_violations(scope, _readout_stats(prefill_edits=0, prefill_forward=0))
    empty = sb.readout_liveness_violations(scope, _readout_stats(prefill_edits=0, prefill_forward=1))
    assert dead and empty, "one of the two failure modes is being passed"
    assert set(dead) != set(empty), "a dead hook and an empty scope are reported identically"
    assert any("n_prefill_forward" in b for b in dead)
    assert not any("n_prefill_forward" in b for b in empty)


def test_a_readout_summary_without_a_per_mode_verdict_is_REFUSED():
    """On this path the decode counters are 0 by construction, so a summary with no per-mode
    verdict carries no evidence of liveness whatsoever and must not pass on its silence."""
    import score_behavior as sb
    _live, s = _readout_summary("query_prefill_only", _readout_stats())
    s = dict(s)
    s["frac_rows_scope_live"] = None
    with pytest.raises(SystemExit, match="no per-mode verdict"):
        sb.assert_knockout_live(s)


def test_zero_rows_is_still_void_on_the_readout_path():
    import score_behavior as sb
    live, s = _readout_summary("query_prefill_only", _readout_stats(), n_rows=0)
    assert s["n_rows"] == 0
    with pytest.raises(SystemExit, match="zero rows"):
        sb.assert_knockout_live(s)


def test_a_readout_row_that_somehow_edited_at_DECODE_is_a_violation():
    """It cannot happen on this path -- which is exactly why it must be reported if it does."""
    import score_behavior as sb
    bad = sb.readout_liveness_violations("query_prefill_only",
                                         _readout_stats(prefill_edits=500, decode_edits=7))
    assert any("n_decode_edits" in b for b in bad)


# --------------------------------------------------------------------------- #
# 4. the contract is DERIVED from pair_common, and every counter in it is consulted
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("scope", ["query_prefill_only", "demo_processing_only",
                                   "legacy_all_query"])
def test_the_readout_contract_is_the_mode_contract_minus_the_unreachable_counter(scope):
    import score_behavior as sb
    pc = _pc()
    req, zero = sb.readout_liveness_contract(scope)
    assert set(req) == (set(pc.LIVENESS_REQUIREMENT[scope]) - {"n_decode_edits"}) \
        | {"n_prefill_forward"}, "the readout requirement is not the mode's own, reduced"
    assert set(zero) == set(pc.LIVENESS_MUST_BE_ZERO[scope]) | {"n_decode_edits"}


@pytest.mark.parametrize("scope", ["query_prefill_only", "demo_processing_only",
                                   "legacy_all_query"])
def test_every_counter_the_readout_contract_declares_is_actually_consulted(scope):
    """A declared counter that no verdict reads is decoration. Each one is probed against the
    SHIPPED evaluator, so a contract list and a gate that drift apart turn this red."""
    import score_behavior as sb
    req, zero = sb.readout_liveness_contract(scope)
    healthy = _readout_stats(prefill_edits=500, prefill_forward=1)
    assert sb.readout_liveness_violations(scope, healthy) == []
    for key in req:
        probe = {**healthy, key: 0}
        assert any(key in b for b in sb.readout_liveness_violations(scope, probe)), \
            f"{key} is declared required but zeroing it changes no verdict"
    for key in zero:
        probe = {**healthy, key: 3}
        assert any(key in b for b in sb.readout_liveness_violations(scope, probe)), \
            f"{key} is declared must-be-zero but setting it changes no verdict"


def test_which_modes_are_measurable_is_derived_not_listed():
    """The admitted set must be exactly the three prefill-measurable modes -- computed by the
    shipped code from the hook's own resolver, not from a name list in score_behavior."""
    import score_behavior as sb
    assert sorted(_measurable()) == sorted(["legacy_all_query", "query_prefill_only",
                                            "demo_processing_only"])
    src = ast.get_source_segment(_src(), next(
        n for n in ast.walk(ast.parse(_src()))
        if isinstance(n, ast.FunctionDef) and n.name == "readout_liveness_contract"))
    assert "resolve_scoped_query_rows" in src, \
        "the satisfiability decision no longer consults the hook's own row resolver"
    assert "LIVENESS_REQUIREMENT" in src, "the contract is no longer derived from pair_common"


# --------------------------------------------------------------------------- #
# 5. THE GENERATION PATH IS UNCHANGED
# --------------------------------------------------------------------------- #
def _gen_summary(scope, stats, n_rows=96):
    import score_behavior as sb
    live = sb.new_knockout_live()
    for _ in range(n_rows):
        sb.record_knockout_row(live, scope, dict(stats), n_demo_positions=len(DEMO))
    return sb.knockout_liveness_summary(live, "eager", scope=scope)


@pytest.mark.parametrize("scope", ["legacy_all_query", "response_query_only"])
def test_generation_path_still_PASSES_a_live_decode_hook(scope):
    import score_behavior as sb
    s = _gen_summary(scope, _gen_stats())
    assert s["liveness_readout_only"] is False
    assert s["liveness_required"] == list(_pc().LIVENESS_REQUIREMENT[scope]), \
        "the generation path is no longer judged on the mode's own, unreduced contract"
    assert sb.assert_knockout_live(s) is True


@pytest.mark.parametrize("scope", ["legacy_all_query", "response_query_only", "decode_only"])
def test_generation_path_still_REFUSES_the_prefill_only_failure(scope):
    """THE FAILURE THE WHOLE GATE EXISTS FOR. If the readout reduction leaked into the default
    path, a decode hook that silently died would now pass on its prefill edits."""
    import score_behavior as sb
    s = _gen_summary(scope, _gen_stats(decode_edits=0, decode_forward=192))
    with pytest.raises(SystemExit):
        sb.assert_knockout_live(s)


def test_the_generation_branch_does_not_use_the_readout_contract():
    """`readout=True` must appear only on the forward-only path."""
    src = _src()
    i = src.index("ks, _bad = record_knockout_row(knock_live, _knock_scope, knock_stats,")
    call = src[i:i + 300]
    assert "readout=True" not in call, \
        "the GENERATION path is now judged on the reduced readout contract -- decode liveness lost"


def test_a_pre_readout_summary_is_still_judged_the_old_way():
    """A summary written before this correction has no `liveness_readout_only` key at all; it must
    read as the generation contract, never as an exemption."""
    import score_behavior as sb
    s = _gen_summary("legacy_all_query", _gen_stats(decode_edits=0))
    s = {k: v for k, v in s.items() if k != "liveness_readout_only"}
    with pytest.raises(SystemExit, match="n_decode_edits==0"):
        sb.assert_knockout_live(s)
