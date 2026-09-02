"""--knockout-scope: the flag must reach BOTH hook paths, and the liveness gate must be per-mode.

WHAT IS BEING PROTECTED. `AllQueryAttentionKnockout` blocks the demonstration keys from EVERY query
row, so a positive result cannot say WHERE the dependence lives. `pair_common.ScopedAttentionKnockout`
splits that one edit into five addressable modes. Wiring it into score_behavior has two silent
failure modes, and they point in opposite directions:

  1. THE SCOPE DOES NOT REACH THE HOOK. The run is filed as, say, `demo_processing_only` and
     actually performs the full all-query knockout -- a LARGER intervention reported under the
     smaller arm's name. `make_intervention`'s composed recursion has dropped a threaded argument
     twice historically (`control_seed`, then `demo_keys`), each time producing a "control" that
     was not one, so the composed path is pinned separately from the single-spec path here.

  2. THE LIVENESS GATE IS MADE MODE-BLIND. `query_prefill_only` and `demo_processing_only` make
     ZERO decode edits BY DEFINITION. Under the old global rule ("decode edits on >= 99% of rows or
     the run is void") they abort for working correctly. The tempting fix -- "pass if EITHER counter
     fired" -- is strictly worse than no gate at all: it lets a genuinely dead decode hook pass on
     its prefill edits, which is the exact prefill-only failure the gate was written for. So the
     gate asserts THIS MODE's required counters are > 0 and its forbidden counters are exactly 0,
     reading `pair_common.LIVENESS_REQUIREMENT` / `LIVENESS_MUST_BE_ZERO` rather than restating
     them, and the two directions are tested separately below.

Nothing in this file re-types a liveness rule or a span: every assertion calls the shipped code
(`sb.record_knockout_row`, `sb.knockout_liveness_summary`, `sb.assert_knockout_live`,
`pc.LIVENESS_REQUIREMENT`), which is what makes it go red when the implementation drifts.

Run:  python -m pytest tests/test_scoped_knockout_wiring.py -q
"""
import inspect
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "boombness", "score_behavior.py")


# --------------------------------------------------------------------------- #
# fakes -- deliberately mirroring the REAL constructor signatures (asserted below)
# --------------------------------------------------------------------------- #
class _FakeAllQuery:
    """pair_common.AllQueryAttentionKnockout. It has no scope: it IS the legacy scope."""
    kind = "all_query"

    def __init__(self, model, layer_idxs, blocked_keys=None, heads=None, stats=None):
        self.layers = list(layer_idxs)
        self.blocked_keys = list(blocked_keys or [])
        self.heads, self.stats = heads, stats
        self.mode = "legacy_all_query"


class _FakeScoped:
    """pair_common.ScopedAttentionKnockout.

    `mode` DEFAULTS to legacy_all_query exactly as the real class does -- that default is what makes
    the "drop `mode=` from the call" mutation detectable instead of a TypeError.
    """
    kind = "scoped"

    def __init__(self, model, layer_idxs, blocked_keys=None, mode="legacy_all_query",
                 query_span=None, demo_span=None, heads=None, stats=None, surface_span=None):
        self.layers = list(layer_idxs)
        self.blocked_keys = list(blocked_keys or [])
        self.mode = mode
        self.query_span = None if query_span is None else set(query_span)
        self.demo_span = None if demo_span is None else set(demo_span)
        # DCS 2026-09-02: the surgical scope's destination rows. Mirrored here because a fake that
        # accepts fewer arguments than the real class turns a dropped argument into a TypeError in
        # the tests and a SILENT no-op in production -- the wrong way round.
        self.surface_span = None if surface_span is None else set(surface_span)
        self.heads, self.stats = heads, stats


class _PC:
    def __init__(self):
        self.made = []

    def AllQueryAttentionKnockout(self, model, layers, blocked_keys=None, heads=None, stats=None):
        k = _FakeAllQuery(model, layers, blocked_keys, heads, stats)
        self.made.append(k)
        return k

    def ScopedAttentionKnockout(self, model, layers, blocked_keys=None, mode="legacy_all_query",
                                query_span=None, demo_span=None, heads=None, stats=None,
                                surface_span=None):
        k = _FakeScoped(model, layers, blocked_keys, mode, query_span, demo_span, heads, stats,
                        surface_span)
        self.made.append(k)
        return k

    def AllPositionProjectOut(self, *a, **k):
        return object()


class _LM:
    model = types.SimpleNamespace(config=types.SimpleNamespace(hidden_size=16,
                                                               num_attention_heads=40))


DEMO = [11, 12, 13, 14, 15]
PROT = {40, 41, 42, 43}
SEQ_LEN = 64
SCOPED = ("query_prefill_only", "decode_only", "response_query_only", "demo_processing_only")


def _pc_module():
    from common import pair
    return pair()


def _knock(pc, scope, spec=None, **kw):
    import score_behavior as sb
    spec = spec or {"direction": "demo_all", "mode": "attn_knockout", "layers": [8], "alpha": 1.0}
    return sb.make_intervention(None, pc, _LM(), spec, None, control_seed=20260823,
                                demo_keys=DEMO, seq_len=SEQ_LEN, knock_stats={}, protected=PROT,
                                knock_scope=scope, **kw)


# --------------------------------------------------------------------------- #
# 1. the flag reaches the hook -- single spec
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("scope", SCOPED)
def test_scope_reaches_the_hook_on_the_single_spec_path(scope):
    """MUTATION TARGET: drop `mode=knock_scope` from the ScopedAttentionKnockout call.

    The real class then falls back to legacy_all_query and the run performs the FULL all-query
    knockout while being filed under the scoped arm's name.
    """
    pc = _PC()
    _knock(pc, scope)
    assert len(pc.made) == 1 and pc.made[0].kind == "scoped", \
        "a non-legacy scope must build the SCOPED hook, not the all-query one"
    assert pc.made[0].mode == scope, (
        f"--knockout-scope {scope} did not reach the hook (got {pc.made[0].mode!r}); the arm would "
        f"perform a different, larger intervention than its name claims")


@pytest.mark.parametrize("scope", SCOPED)
def test_both_spans_reach_the_hook_because_a_missing_one_is_a_no_op(scope):
    """A mode given no span degrades to a knockout that edits nothing and scores as a clean null.

    query_span and demo_span are passed SEPARATELY from blocked_keys on purpose: a control arm's
    keys are neither the demonstration block nor the query span.
    """
    pc = _PC()
    _knock(pc, scope)
    k = pc.made[0]
    assert k.query_span == set(PROT), "the final-query span did not reach the hook"
    assert k.demo_span == set(DEMO), "the demonstration span did not reach the hook"
    assert k.blocked_keys == DEMO, "the key set changed"


def test_a_control_arms_keys_are_not_its_spans():
    """The reason the spans are separate arguments, pinned so nobody 'simplifies' it away."""
    pc = _PC()
    spec = {"direction": "nondemo_random", "mode": "attn_knockout", "layers": [8], "alpha": 1.0}
    _knock(pc, "response_query_only", spec=spec)
    k = pc.made[0]
    assert set(k.blocked_keys).isdisjoint(set(DEMO)), "the control drew inside the demo block"
    assert k.demo_span == set(DEMO), "demo_span must still be the DEMO block, not the arm's keys"
    assert k.query_span == set(PROT)


# --------------------------------------------------------------------------- #
# 2. the flag reaches the hook -- composed recursion (dropped twice historically)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("scope", SCOPED)
def test_scope_reaches_every_leg_of_a_composed_arm(scope):
    """MUTATION TARGET: drop `knock_scope=knock_scope` from the recursion line."""
    pc = _PC()
    spec = {"composed": [
        {"direction": "demo_all", "mode": "attn_knockout", "layers": [8], "alpha": 1.0},
        {"direction": "demo_all", "mode": "attn_knockout", "layers": [9], "alpha": 1.0}]}
    _knock(pc, scope, spec=spec)
    assert [k.mode for k in pc.made] == [scope, scope], (
        "the composed recursion dropped knock_scope on a leg -- the same one-of-two-paths failure "
        "that hit control_seed and demo_keys")
    assert [k.kind for k in pc.made] == ["scoped", "scoped"]


def test_a_composed_arm_still_carries_heads_and_keys_alongside_the_scope():
    """The scope must not have displaced an existing passenger on that line."""
    import torch  # noqa: F401
    pc = _PC()
    spec = {"composed": [
        {"direction": "d_surface", "mode": "project_out", "layers": [14], "alpha": 1.0},
        {"direction": "demo_all", "mode": "attn_knockout", "layers": [8], "alpha": 1.0}]}
    import score_behavior as sb
    payload = {"d_surface": {14: torch.ones(16)}, "gap": {"d_surface": {14: 1.0}}}
    ctxs = sb.make_intervention(None, pc, _LM(), spec, payload, control_seed=20260823,
                                demo_keys=DEMO, seq_len=SEQ_LEN, knock_stats={}, protected=PROT,
                                knock_heads=[22], knock_scope="decode_only")
    assert len(ctxs) == 2
    assert pc.made[0].mode == "decode_only" and pc.made[0].heads == [22]
    assert pc.made[0].blocked_keys == DEMO


# --------------------------------------------------------------------------- #
# 3. the default is unchanged -- every existing arm keeps the legacy hook
# --------------------------------------------------------------------------- #
def test_the_default_scope_is_the_first_mode_of_the_hooks_own_table():
    import score_behavior as sb
    pc = _pc_module()
    assert sb.DEFAULT_KNOCKOUT_SCOPE == "legacy_all_query"
    assert sb.DEFAULT_KNOCKOUT_SCOPE in pc.SCOPED_KNOCKOUT_MODES, \
        "the default names a mode the hook does not implement"


@pytest.mark.parametrize("arm", ("demo_all", "nondemo_random", "allpast"))
def test_default_is_byte_identical_for_every_existing_arm(arm):
    """Every committed Phase 2-4 artifact was produced by AllQueryAttentionKnockout. The flag's
    default must still construct THAT object -- not an equivalent one -- and pass it the same keys.
    """
    import score_behavior as sb
    assert arm in sb.KNOCKOUT_ARMS
    pc_default, pc_explicit = _PC(), _PC()
    spec = {"direction": arm, "mode": "attn_knockout", "layers": [8], "alpha": 1.0}
    sb.make_intervention(None, pc_default, _LM(), spec, None, control_seed=20260823,
                         demo_keys=DEMO, seq_len=SEQ_LEN, knock_stats={}, protected=PROT)
    _knock(pc_explicit, sb.DEFAULT_KNOCKOUT_SCOPE, spec=spec)
    assert pc_default.made[0].kind == "all_query", \
        "the default no longer builds AllQueryAttentionKnockout; every existing recipe re-scoped"
    assert pc_explicit.made[0].kind == "all_query", \
        "passing the default scope explicitly must be the same run as passing nothing"
    assert pc_default.made[0].blocked_keys == pc_explicit.made[0].blocked_keys == \
        sb.knockout_key_set(arm, DEMO, SEQ_LEN, 20260823, protected=PROT)
    assert pc_default.made[0].heads is None, "the default head selection changed"


def test_the_wiring_matches_the_real_constructor_signature():
    """The fakes above are only evidence if the real class takes these keywords under these names.

    A rename in pair_common would otherwise leave this file green while every scoped run died
    inside the per-row try as a ledger failure.
    """
    pc = _pc_module()
    p = inspect.signature(pc.ScopedAttentionKnockout.__init__).parameters
    for kw in ("blocked_keys", "mode", "query_span", "demo_span", "heads", "stats",
               "surface_span"):
        assert kw in p, f"ScopedAttentionKnockout no longer takes {kw!r}"
    assert p["mode"].default == "legacy_all_query", \
        "the real class's default mode changed; the fake no longer mirrors it"


# --------------------------------------------------------------------------- #
# 4. argument-time refusals -- a flag that reaches nothing must never run
# --------------------------------------------------------------------------- #
def _src():
    return open(SRC).read()


def test_the_flag_exists_and_is_validated_against_the_hooks_own_mode_tuple():
    src = _src()
    assert '"--knockout-scope"' in src, "the flag is gone"
    assert "pc.SCOPED_KNOCKOUT_MODES" in src, \
        "the mode list is not read from pair_common; a restated list is free to drift"
    i = src.index("_knock_scope not in pc.SCOPED_KNOCKOUT_MODES")
    assert "REFUSING" in src[i:i + 300], "an unknown scope no longer refuses at argument time"


def test_scope_without_intervene_refuses():
    """Mirrors --knockout-heads: the flag only reaches attn_knockout arms, so with no --intervene
    it would silently do nothing and the run would be filed under a scoped name."""
    src = _src()
    key = "_knock_scope != DEFAULT_KNOCKOUT_SCOPE and not args.intervene"
    assert key in src, "the no-intervene guard for --knockout-scope is gone"
    assert "REFUSING" in src[src.index(key):src.index(key) + 300]


def test_scope_without_an_attn_knockout_spec_refuses():
    src = _src()
    i = src.index('"[score] REFUSING: --knockout-scope given but no attn_knockout ')
    assert 'sp["mode"] == "attn_knockout"' in src[max(0, i - 300):i], \
        "the guard no longer checks the specs for an attn_knockout arm"


def test_the_scope_is_echoed_and_persisted():
    """A scoped run that does not say which rows it edited, or which counters it was judged on, is
    unauditable -- and a number that exists only in a log line is not evidence."""
    src = _src()
    assert "knockout scope:" in src, "the scope is not echoed"
    assert 'base["knockout_scope"]' in src, "the scope is not on every row"
    assert '{**spec, "knockout_scope": _knock_scope}' in src, \
        "the scope is not in summary.json's intervention block"
    for field in ("query_span_bounds", "demo_span_bounds", "n_query_span_positions",
                  "hook_n_prefill_edits", "hook_liveness_violations"):
        assert field in src, f"the artifact no longer records {field}"


# --------------------------------------------------------------------------- #
# 5. the MODE-AWARE liveness gate
# --------------------------------------------------------------------------- #
def _stats(prefill_edits, decode_edits, prefill_forward=1, decode_forward=40):
    """One row's hook counters, in the hook's own key names."""
    return {"n_forward": prefill_forward + decode_forward,
            "n_prefill_forward": prefill_forward, "n_decode_forward": decode_forward,
            "n_edits": prefill_edits + decode_edits,
            "n_prefill_edits": prefill_edits, "n_decode_edits": decode_edits}


def _summary(scope, stats, n_rows=96, attn_impl="eager"):
    """Build the summary the way main() does: through the SHIPPED accumulator, so a drift in the
    per-row liveness rule turns these tests red instead of leaving them green on a restated rule."""
    import score_behavior as sb
    live = sb.new_knockout_live()
    for _ in range(n_rows):
        sb.record_knockout_row(live, scope, dict(stats), n_demo_positions=len(DEMO))
    return sb.knockout_liveness_summary(live, attn_impl, scope=scope)


def test_gate_PASSES_a_prefill_only_mode_that_makes_zero_decode_edits():
    """THE MODE-AWARENESS CASE. Zero decode edits is CORRECT here; the old global rule aborted it."""
    import score_behavior as sb
    s = _summary("query_prefill_only", _stats(prefill_edits=500, decode_edits=0))
    assert s["frac_rows_decode_live"] == 0.0, \
        "fixture broken: this mode must make no decode edits at all"
    assert s["frac_rows_scope_live"] == 1.0
    assert sb.assert_knockout_live(s) is True, \
        "the gate aborted a mode that is silent at decode BY DEFINITION"


def test_gate_PASSES_demo_processing_only_which_is_also_decode_silent():
    import score_behavior as sb
    s = _summary("demo_processing_only", _stats(prefill_edits=120, decode_edits=0))
    assert s["frac_rows_decode_live"] == 0.0
    assert sb.assert_knockout_live(s) is True


def test_gate_STILL_REFUSES_a_decode_scoped_mode_whose_decode_edits_are_zero():
    """THE IMPORTANT ONE. `decode_only` with a dead decode hook, and PLENTY of prefill edits.

    MUTATION TARGET: loosen the gate to "either counter fired". This fixture then passes on its
    prefill edits alone -- which is precisely the prefill-only failure the liveness gate exists to
    catch, dressed up as a scoped arm.
    """
    import score_behavior as sb
    s = _summary("decode_only", _stats(prefill_edits=500, decode_edits=0))
    assert s["frac_rows_scope_live"] == 0.0
    with pytest.raises(SystemExit) as e:
        sb.assert_knockout_live(s)
    assert "decode_only" in str(e.value)


def test_gate_STILL_REFUSES_the_classic_prefill_only_failure_under_the_legacy_scope():
    """The historical case, now with prefill edits present so an 'either counter' gate would pass."""
    import score_behavior as sb
    s = _summary("legacy_all_query", _stats(prefill_edits=500, decode_edits=0))
    with pytest.raises(SystemExit, match="prefill-only|legacy_all_query"):
        sb.assert_knockout_live(s)


def test_gate_REFUSES_a_scope_that_LEAKED_into_the_half_it_must_not_touch():
    """MUST_BE_ZERO is not decoration: a prefill-only mode that edits at decode is secretly a
    LARGER intervention than the one being reported."""
    import score_behavior as sb
    s = _summary("query_prefill_only", _stats(prefill_edits=500, decode_edits=7))
    assert s["frac_rows_scope_live"] == 0.0
    with pytest.raises(SystemExit):
        sb.assert_knockout_live(s)
    assert any("n_decode_edits" in k for k in s["scope_violations"]), s["scope_violations"]


@pytest.mark.parametrize("scope", ("legacy_all_query",) + SCOPED)
def test_every_mode_is_judged_on_exactly_the_counters_its_own_table_declares(scope):
    """Table-driven against pair_common, both directions, for all five modes.

    A mode passes when every REQUIRED counter fired and every FORBIDDEN one is zero; zeroing any
    single required counter must refuse. Nothing here restates which counters those are.
    """
    import score_behavior as sb
    pc = _pc_module()
    req = pc.LIVENESS_REQUIREMENT[scope]
    zero = pc.LIVENESS_MUST_BE_ZERO[scope]
    alive = {"n_prefill_edits": 500 if "n_prefill_edits" not in zero else 0,
             "n_decode_edits": 500 if "n_decode_edits" not in zero else 0}
    s = _summary(scope, _stats(alive["n_prefill_edits"], alive["n_decode_edits"]))
    assert sb.assert_knockout_live(s) is True, f"{scope} rejected a healthy run"
    for counter in req:
        dead = dict(alive)
        dead[counter] = 0
        with pytest.raises(SystemExit):
            sb.assert_knockout_live(
                _summary(scope, _stats(dead["n_prefill_edits"], dead["n_decode_edits"])))


def test_the_summary_records_the_scope_and_the_contract_it_was_judged_on():
    import score_behavior as sb
    pc = _pc_module()
    s = _summary("response_query_only", _stats(500, 500))
    assert s["knockout_scope"] == "response_query_only"
    assert s["liveness_required"] == list(pc.LIVENESS_REQUIREMENT["response_query_only"])
    assert s["liveness_must_be_zero"] == list(pc.LIVENESS_MUST_BE_ZERO["response_query_only"])
    assert s["total_prefill_edits"] == 96 * 500 and s["total_decode_edits"] == 96 * 500
    # and the legacy fields are untouched, so every committed reader still works
    assert s["frac_rows_decode_live"] == 1.0 and s["attn_implementation"] == "eager"


def test_gate_REFUSES_a_scoped_summary_carrying_no_per_mode_verdict():
    """A pre-scope summary has decode information only. It cannot judge a scoped mode, and the
    absence must refuse rather than fall through to a decode rule the mode never had to satisfy."""
    import score_behavior as sb
    s = sb.knockout_liveness_summary(
        {"n_rows": 96, "n_rows_decode_live": 96, "decode_edits": [42] * 96,
         "decode_forwards": [10] * 96, "n_demo_positions": [14] * 96},
        "eager", scope="decode_only")
    assert s["frac_rows_scope_live"] is None, "an unrecorded verdict must not read as 0.0 or 1.0"
    with pytest.raises(SystemExit, match="no per-mode verdict"):
        sb.assert_knockout_live(s)


def test_a_pre_scope_legacy_summary_still_passes_unchanged():
    """Committed artifacts and every caller that predates the flag keep working."""
    import score_behavior as sb
    s = sb.knockout_liveness_summary(
        {"n_rows": 96, "n_rows_decode_live": 96, "decode_edits": [42] * 96,
         "decode_forwards": [10] * 96, "n_demo_positions": [14] * 96}, "eager")
    assert s["knockout_scope"] == sb.DEFAULT_KNOCKOUT_SCOPE
    assert sb.assert_knockout_live(s) is True


def test_an_unknown_scope_cannot_reach_the_gate_silently():
    import score_behavior as sb
    with pytest.raises(SystemExit, match="unknown knockout scope"):
        sb.knockout_liveness_summary({"n_rows": 1}, "eager", scope="not_a_mode")
    with pytest.raises(SystemExit, match="unknown knockout scope"):
        sb.assert_knockout_live({"n_rows": 96, "knockout_scope": "not_a_mode"})


def test_zero_rows_is_still_a_failure_under_every_scope():
    import score_behavior as sb
    for scope in ("legacy_all_query",) + SCOPED:
        with pytest.raises(SystemExit, match="zero rows"):
            sb.assert_knockout_live(_summary(scope, _stats(500, 500), n_rows=0))


# --------------------------------------------------------------------------- #
# 6. pre-flight -- a scope that resolves to no rows must die before the run
# --------------------------------------------------------------------------- #
def test_a_scope_with_no_resolvable_rows_is_infeasible_not_a_null():
    """The hook refuses an empty required span, but it is built INSIDE the per-row try, so that
    refusal would arrive as silent ledger failures and a quietly shrunken population."""
    import score_behavior as sb
    assert sb.scoped_span_is_dead("query_prefill_only", set(), DEMO) is True
    assert sb.scoped_span_is_dead("demo_processing_only", PROT, []) is True


def test_a_scope_with_rows_to_edit_is_feasible():
    import score_behavior as sb
    assert sb.scoped_span_is_dead("query_prefill_only", PROT, DEMO) is False
    assert sb.scoped_span_is_dead("demo_processing_only", PROT, DEMO) is False
    # decode_only edits EVERY decode row and needs no span at all -- it must never be called dead
    assert sb.scoped_span_is_dead("decode_only", set(), []) is False
    assert sb.scoped_span_is_dead("legacy_all_query", set(), []) is False


def test_the_preflight_consults_the_hooks_own_row_resolver():
    """Restating the span algebra beside the hook is how it drifts; it must be derived from it."""
    src = _src()
    assert "resolve_scoped_query_rows" in src, \
        "the pre-flight no longer derives the row set from pair_common's resolver"
    assert "scoped_span_is_dead(_knock_scope" in src, "the pre-flight check is gone"
    assert "dead_scope_span" in src, "the pre-flight no longer counts or reports these rows"


# --------------------------------------------------------------------------- #
# 7. the derived counter -- a missing key must not read as a dead hook
# --------------------------------------------------------------------------- #
def test_prefill_edits_are_derived_for_the_legacy_hook_which_does_not_record_them():
    """AllQueryAttentionKnockout writes no n_prefill_edits, and `stats.get(key, 0)` cannot tell a
    key nobody wrote from a real zero. Left undermined, every legacy run would be reported DEAD at
    prefill -- a fabricated failure, the mirror image of the dead guard."""
    import score_behavior as sb
    ks = sb.knockout_row_stats({"n_forward": 41, "n_decode_forward": 40, "n_prefill_forward": 1,
                                "n_edits": 100, "n_decode_edits": 40})
    assert ks["n_prefill_edits"] == 60, "the n_edits == prefill + decode invariant is not applied"


def test_a_real_zero_is_never_overwritten_by_the_derivation():
    """The scoped hook records the counter itself; a genuine 0 must survive as 0, or the gate is
    blind to exactly the mode it is meant to police."""
    import score_behavior as sb
    ks = sb.knockout_row_stats(_stats(prefill_edits=0, decode_edits=500))
    assert ks["n_prefill_edits"] == 0
    live = sb.new_knockout_live()
    sb.record_knockout_row(live, "legacy_all_query", ks)
    assert live["n_rows_scope_live"] == 0, "a dead prefill half passed the legacy contract"
