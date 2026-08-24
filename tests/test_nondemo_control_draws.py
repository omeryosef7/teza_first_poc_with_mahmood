"""The Phase-1 SAME-BAND, NON-DEMO-KEY control draws (plan section 4).

WHAT IS UNDER TEST. `score_behavior.nondemo_control_draw` and the `nondemo_matched_d*` /
`nondemo_capped_d*` arms it backs. A Phase-1 arm masks attention to the DEMO block across a layer
band; the matched control must mask approximately the SAME NUMBER of key positions in the SAME band
but OUTSIDE the demo block, so the contrast isolates "these tokens" from "this many tokens at these
layers". The band is the spec's `layers` field and is shared by construction, so everything here is
about WHICH KEYS and HOW MANY.

TWO PUBLISHED FAILURES THIS FILE IS THE RECEIPT FOR:

  * prev-REVIEW-1 M1 -- the pool. The non-demo pool is a near-CONSTANT ~53 tokens (chat template +
    the ~90-char request + the generation header) while the demo block grows 12 -> 25.5 -> 53.5 ->
    106 tokens across n_examples 1/2/4/8. An unprotected count-matched draw therefore deleted the
    question the model is asked to answer, with a dose that scaled with the arm's own dose.
    `test_the_query_span_is_never_drawn` and `test_MUTANT_*` below are the red/green pair for the
    protection: the second removes it from the REAL SOURCE and shows the first goes red.
  * prev-R-G / prev-R-D -- the lottery. One random draw at a large magnitude is not a control (four
    same-dose draws spanned 0.325 ASR against a 0.036 arm effect), so the control is a BAND of
    >= 3 separately-seeded draws. `test_three_draws_are_three_different_draws` pins that they are
    genuinely different, and `test_same_seed_same_positions` that each one is reproducible.

THE POPULATION IS NOT INVENTED. `_bank_population` rebuilds per-row demo/query/sequence lengths from
SCALAR fields of the real committed bank (character counts only -- no prompt text is read into a
test assertion, printed, or compared other than by length), and
`test_population_reconstructs_the_published_token_counts` checks the reconstruction against the
token counts the M1 review measured with the real Llama tokenizer before any feasibility claim is
made from it.

Run:  python -m pytest tests/test_nondemo_control_draws.py -q
"""
import importlib.util
import json
import os
import statistics
import sys
import types

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRCB = os.path.join(REPO, "src", "boombness")
sys.path.insert(0, SRCB)

import score_behavior as sb            # noqa: E402  -- the REAL implementation, never a copy
from common import FailureLedger       # noqa: E402


# --------------------------------------------------------------------------- #
# a row shaped like the real ones: [BOS | chat template | DEMO | request+header]
# --------------------------------------------------------------------------- #
def _row(n_template, n_demo, n_query):
    """(demo_keys, protected, seq_len) for one synthetic row with that layout."""
    demo = list(range(n_template, n_template + n_demo))
    seq_len = n_template + n_demo + n_query
    protected = set(range(n_template + n_demo, seq_len))
    return demo, protected, seq_len


# The M1 arithmetic in miniature: a 32-token template, a 12-token demo block, a 20-token request.
DEMO, PROT, SEQ = _row(32, 12, 20)


# --------------------------------------------------------------------------- #
# 1. determinism -- the same seed must give the same positions on the same row
# --------------------------------------------------------------------------- #
def test_same_seed_same_positions():
    a, _ = sb.nondemo_control_draw(DEMO, SEQ, PROT, seed=4242)
    b, _ = sb.nondemo_control_draw(DEMO, SEQ, PROT, seed=4242)
    assert a == b and a == sorted(a)


def test_different_seeds_give_different_positions():
    draws = {tuple(sb.nondemo_control_draw(DEMO, SEQ, PROT, seed=s)[0])
             for s in (1, 2, 3, 4, 5)}
    assert len(draws) == 5, f"five seeds produced {len(draws)} distinct draws"


def test_three_draws_are_three_different_draws():
    """The control is a BAND, not one ticket (prev-R-G / prev-R-D)."""
    assert sb.NONDEMO_CONTROL_N_DRAWS >= 3
    got = {}
    for k in range(1, sb.NONDEMO_CONTROL_N_DRAWS + 1):
        arm = f"{sb.NONDEMO_DRAW_PREFIX['strict']}{k}"
        got[arm] = tuple(sb.knockout_key_set(arm, DEMO, SEQ, 20260823, protected=PROT))
    assert len(set(got.values())) == sb.NONDEMO_CONTROL_N_DRAWS, got.keys()


def test_the_draw_seed_is_an_explicit_reproducible_function_of_the_run_seed():
    seeds = {sb.nondemo_draw_seed(20260823, k)
             for k in range(1, sb.NONDEMO_CONTROL_N_DRAWS + 1)}
    assert len(seeds) == sb.NONDEMO_CONTROL_N_DRAWS
    assert sb.nondemo_draw_seed(20260823, 2) == sb.nondemo_draw_seed(20260823, 2)
    # a different run seed is a different draw, or --seed would be decorative
    assert sb.nondemo_draw_seed(20260824, 2) != sb.nondemo_draw_seed(20260823, 2)
    # and it must not collide with the composed-leg offset: that collision is retraction #7's shape
    assert sb.NONDEMO_DRAW_SEED_STRIDE != sb.COMPOSED_SEED_STRIDE


def test_the_seed_actually_used_is_recorded_with_the_positions():
    log = {}
    arm = f"{sb.NONDEMO_DRAW_PREFIX['strict']}2"
    pos = sb.knockout_key_set(arm, DEMO, SEQ, 20260823, protected=PROT, draw_log=log)
    (rec,) = list(log.values())
    assert rec["draw_seed"] == sb.nondemo_draw_seed(20260823, 2)
    assert rec["control_seed"] == 20260823 and rec["draw_index"] == 2 and rec["arm"] == arm
    assert rec["positions"] == pos, "the recorded positions are not the ones the arm used"
    # and the record alone is enough to regenerate them
    again, _ = sb.nondemo_control_draw(DEMO, SEQ, PROT, seed=rec["draw_seed"],
                                       policy=rec["policy"])
    assert again == pos


# --------------------------------------------------------------------------- #
# 2. the protected query span is NEVER touched (M1)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("policy", ("strict", "capped"))
@pytest.mark.parametrize("seed", (1, 7, 20260823, 987654321))
def test_the_query_span_is_never_drawn(policy, seed):
    pos, rec = sb.nondemo_control_draw(DEMO, SEQ, PROT, seed=seed, policy=policy)
    assert set(pos).isdisjoint(PROT), "the control blocked part of the request"
    assert set(pos).isdisjoint(set(DEMO)), "the control drew inside the demo block"
    assert 0 not in pos, "BOS must be spared"
    assert max(pos) < SEQ - 1, "the control must not cut the final prompt token"
    assert rec["n_pool"] == SEQ - 2 - len(DEMO) - len(PROT) + 1  # [1, SEQ-2] minus demo minus prot


def test_removing_the_protection_provably_eats_the_request():
    """RED/GREEN through the real code path: with `protected` empty the draw MUST hit the request.

    Pigeonhole, so it is not a coin flip: the unprotected pool is 30 candidates of which 20 are
    request positions, and a count-matched draw takes 12 -- at least 2 of them are the request.
    """
    demo, prot, seq = _row(12, 12, 20)          # pool without protection = 30, with it = 10
    pos, _ = sb.nondemo_control_draw(demo, seq, set(), seed=20260823, policy="capped")
    assert len(set(pos) & prot) >= 2, "the pigeonhole says the unprotected draw eats the request"


def test_MUTANT_source_without_the_protection_fails_the_query_span_test(tmp_path):
    """The same red/green, but by MUTATING THE REAL SOURCE rather than an argument.

    `_stripped` re-executes score_behavior.py with the `i not in prot` clause deleted from the pool
    construction -- literally the pre-fix behaviour -- and the assertion of
    `test_the_query_span_is_never_drawn` is re-run against it. It must fail there.
    """
    src = open(os.path.join(SRCB, "score_behavior.py")).read()
    old = "pool = [i for i in range(1, max(0, n - 1)) if i not in dks and i not in prot]"
    assert src.count(old) == 1, "the protected-complement pool moved; re-anchor this mutation"
    dst = tmp_path / "score_behavior_mutant.py"
    dst.write_text(src.replace(old, "pool = [i for i in range(1, max(0, n - 1)) if i not in dks]", 1))
    spec = importlib.util.spec_from_file_location("score_behavior_nondemo_mutant", str(dst))
    mut = importlib.util.module_from_spec(spec)
    sys.modules["score_behavior_nondemo_mutant"] = mut
    spec.loader.exec_module(mut)
    demo, prot, seq = _row(12, 12, 20)
    hits = 0
    for seed in (1, 7, 20260823, 987654321):
        pos, _ = mut.nondemo_control_draw(demo, seq, prot, seed=seed, policy="capped")
        hits += len(set(pos) & prot)
    assert hits > 0, "the mutant did NOT eat the request -- this test no longer proves anything"


# --------------------------------------------------------------------------- #
# 3. count-matching, and what happens when it is impossible
# --------------------------------------------------------------------------- #
def test_strict_is_exactly_count_matched_when_it_is_feasible():
    pos, rec = sb.nondemo_control_draw(DEMO, SEQ, PROT, seed=11, policy="strict")
    assert len(pos) == len(DEMO) == rec["n_drawn"]
    assert rec["match_ratio"] == 1.0


def test_strict_REFUSES_rather_than_silently_under_matching():
    """Under-matching is the dose confound in a new costume, so the row is refused instead."""
    demo, prot, seq = _row(32, 60, 20)          # 60 demo keys, pool = 31
    with pytest.raises(sb.InfeasibleControl) as ei:
        sb.nondemo_control_draw(demo, seq, prot, seed=1, policy="strict")
    assert issubclass(sb.InfeasibleControl, Exception)
    assert not issubclass(sb.InfeasibleControl, SystemExit)
    assert ei.value.record["n_pool"] < ei.value.record["n_demo_keys"]


def test_the_refused_row_is_charged_to_the_failure_ledger():
    """The per-row guard in main() is `except Exception -> ledger.fail`; this is that shape run
    against the REAL FailureLedger, so an InfeasibleControl can never become a silent skip."""
    demo, prot, seq = _row(32, 60, 20)
    ledger = FailureLedger()
    try:
        sb.knockout_key_set(f"{sb.NONDEMO_DRAW_PREFIX['strict']}1", demo, seq, 20260823,
                            protected=prot)
        ledger.ok()
    except Exception as e:                       # exactly the guard main() uses
        ledger.fail(f"knockout:{type(e).__name__}", "pid-0")
    d = ledger.as_dict()
    assert d["n_failed"] == 1 and d["n_succeeded"] == 0
    assert "knockout:InfeasibleControl" in d["failure_reasons"]


def test_an_infeasible_row_still_records_WHY_in_the_draw_log():
    """Auditability does not stop at the feasible rows: the pool arithmetic is recorded too."""
    demo, prot, seq = _row(32, 60, 20)
    log = {}
    with pytest.raises(sb.InfeasibleControl):
        sb.knockout_key_set(f"{sb.NONDEMO_DRAW_PREFIX['strict']}1", demo, seq, 20260823,
                            protected=prot, draw_log=log)
    (rec,) = list(log.values())
    assert rec["n_drawn"] == 0 and rec["positions"] == [] and rec["match_ratio"] == 0.0
    assert rec["n_pool"] == 31 and rec["n_demo_keys"] == 60


def test_capped_records_the_ACHIEVED_match_ratio_instead_of_pretending():
    demo, prot, seq = _row(32, 60, 20)
    pos, rec = sb.nondemo_control_draw(demo, seq, prot, seed=1, policy="capped")
    assert len(pos) == rec["n_pool"] == 31 < len(demo)
    assert rec["n_drawn"] == 31 and rec["match_ratio"] == pytest.approx(31 / 60)
    assert set(pos).isdisjoint(prot) and set(pos).isdisjoint(set(demo))


def test_the_policy_is_visible_in_the_arm_name():
    """A count-matched control and a pool-capped one are different experiments; an artifact must
    not need a footnote to tell them apart."""
    assert sb.parse_nondemo_draw_arm("nondemo_matched_d2") == ("strict", 2)
    assert sb.parse_nondemo_draw_arm("nondemo_capped_d3") == ("capped", 3)
    assert sb.parse_nondemo_draw_arm("nondemo_random") is None
    assert sb.parse_nondemo_draw_arm("demo_all") is None
    over = sb.NONDEMO_CONTROL_N_DRAWS + 1
    assert sb.parse_nondemo_draw_arm(f"nondemo_matched_d{over}") is None


def test_an_empty_demo_block_is_refused_not_scored_as_a_null():
    with pytest.raises(sb.InfeasibleControl):
        sb.nondemo_control_draw([], SEQ, PROT, seed=1)


def test_an_empty_pool_is_refused_even_under_the_capped_policy():
    demo, prot, seq = _row(1, 12, 20)            # BOS only, so the pool is empty
    with pytest.raises(sb.InfeasibleControl):
        sb.nondemo_control_draw(demo, seq, prot, seed=1, policy="capped")


def test_an_unknown_policy_raises():
    with pytest.raises(SystemExit):
        sb.nondemo_control_draw(DEMO, SEQ, PROT, seed=1, policy="whatever")


# --------------------------------------------------------------------------- #
# 4. feasibility on the REAL bank population, per n_examples
# --------------------------------------------------------------------------- #
# Rebuilt from SCALAR fields only (character counts). CHARS_PER_TOKEN is calibrated against the
# token counts the M1 review measured with the real Llama tokenizer on this bank
# (12 / 25.5 / 53.5 / 106 demo tokens at n_examples 1 / 2 / 4 / 8), and
# test_population_reconstructs_the_published_token_counts checks it before anything else uses it.
CHARS_PER_TOKEN = 5.75
GEN_HEADER_TOKENS = 5
NONDEMO_POOL_TOKENS = 53          # the measured near-constant: template + request + header
PUBLISHED_DEMO_TOKENS = {1: 12.0, 2: 25.5, 4: 53.5, 8: 106.0}
BANK = os.path.join(REPO, "data", "boombness_prompts", "boombness_prompt_bank.jsonl")

#: MEASURED on that reconstruction (behavioral rows of the committed main bank): the fraction of
#: rows at each dose level on which a STRICT count-matched, query-protected control exists at all.
#: This is the number the whole policy question turns on, so it is pinned rather than described:
#:   n_examples 1 -> 1.000 (96 rows)      2 -> 0.898 (264 rows)
#:              4 -> 0.000 (342 rows)     8 -> 0.000 (306 rows)
#: i.e. the matched control is IMPOSSIBLE at the two high-dose levels, and rescoping the arm to the
#: feasible rows is not a way out -- demo length IS the dose variable.
STRICT_FEASIBLE_FRAC = {1: (1.0, 1.0), 2: (0.85, 0.95), 4: (0.0, 0.0), 8: (0.0, 0.0)}
#: and the achieved ratio a CAPPED run reports there (median over rows), same reconstruction
CAPPED_MEDIAN_RATIO = {1: (1.0, 1.0), 2: (0.95, 1.0), 4: (0.55, 0.65), 8: (0.27, 0.35)}


def _bank_population():
    if not os.path.exists(BANK):
        pytest.skip("bank not present")
    rows = []
    with open(BANK) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("query_kind") != "behavioral":
                continue
            ne = r.get("n_examples")
            if ne not in PUBLISHED_DEMO_TOKENS:
                continue
            n_demo = int(round(len(r.get("demo_block") or "") / CHARS_PER_TOKEN))
            n_query = int(round(len(r.get("final_query_text") or "") / CHARS_PER_TOKEN)) \
                + GEN_HEADER_TOKENS
            n_template = NONDEMO_POOL_TOKENS - n_query
            demo, prot, seq = _row(n_template, n_demo, n_query)
            rows.append({"n_examples": ne, "demo": demo, "prot": prot, "seq": seq})
    assert rows, "no behavioral rows at the four dose levels"
    return rows


def test_population_reconstructs_the_published_token_counts():
    """Faithfulness gate: if this drifts, every feasibility claim below is about a fiction."""
    pop = _bank_population()
    for ne, want in PUBLISHED_DEMO_TOKENS.items():
        got = statistics.median([len(r["demo"]) for r in pop if r["n_examples"] == ne])
        assert abs(got - want) <= 2.0, f"n_examples={ne}: rebuilt {got}, M1 measured {want}"
    for r in pop:                       # the near-constant non-demo pool, per M1
        assert r["seq"] - len(r["demo"]) == NONDEMO_POOL_TOKENS


@pytest.mark.parametrize("n_examples", sorted(PUBLISHED_DEMO_TOKENS))
def test_strict_feasibility_is_measured_at_every_dose_level(n_examples):
    """The count-matched control is FEASIBLE at small n_examples and IMPOSSIBLE at large ones.

    This is not a defect of the implementation, it is the M1 pool arithmetic, and it is the whole
    reason `strict` refuses and `capped` records a ratio. Asserted per level so a change in either
    direction is caught: silently under-matching at n_examples=8 would turn the last case green in
    the worst possible way.
    """
    pop = [r for r in _bank_population() if r["n_examples"] == n_examples]
    ok = 0
    for r in pop:
        try:
            pos, rec = sb.nondemo_control_draw(r["demo"], r["seq"], r["prot"],
                                               seed=sb.nondemo_draw_seed(20260823, 1))
            assert len(pos) == len(r["demo"]) and rec["match_ratio"] == 1.0
            assert set(pos).isdisjoint(r["prot"])
            ok += 1
        except sb.InfeasibleControl:
            pass
    frac = ok / len(pop)
    lo, hi = STRICT_FEASIBLE_FRAC[n_examples]
    assert lo <= frac <= hi, (
        f"n_examples={n_examples}: {frac:.3f} of rows carry a count-matched control, expected "
        f"[{lo}, {hi}] from a pool of ~{NONDEMO_POOL_TOKENS} non-demo tokens. Above the range "
        f"means the draw is no longer protecting the request or no longer count-matching; below "
        f"means the pool shrank.")


@pytest.mark.parametrize("n_examples", sorted(PUBLISHED_DEMO_TOKENS))
def test_capped_covers_every_dose_level_and_never_hides_the_shortfall(n_examples):
    pop = [r for r in _bank_population() if r["n_examples"] == n_examples]
    ratios = []
    for r in pop:
        pos, rec = sb.nondemo_control_draw(r["demo"], r["seq"], r["prot"], seed=99,
                                           policy="capped")
        assert set(pos).isdisjoint(r["prot"]) and set(pos).isdisjoint(set(r["demo"]))
        assert len(pos) == rec["n_drawn"] == min(len(r["demo"]), rec["n_pool"])
        assert rec["match_ratio"] == pytest.approx(rec["n_drawn"] / len(r["demo"]))
        ratios.append(rec["match_ratio"])
    assert len(ratios) == len(pop), "capped must produce a control on every row"
    lo, hi = CAPPED_MEDIAN_RATIO[n_examples]
    med = statistics.median(ratios)
    assert lo <= med <= hi, f"n_examples={n_examples}: median achieved match ratio {med:.3f}"
    if n_examples >= 4:
        assert max(ratios) < 1.0, "a capped run at this dose must report an honest shortfall"


# --------------------------------------------------------------------------- #
# 5. reachable as an arm, exactly like every other knockout arm
# --------------------------------------------------------------------------- #
class _FakeKnockout:
    def __init__(self, model, layer_idxs, blocked_keys=None, heads=None, stats=None):
        self.layers = list(layer_idxs)
        self.blocked_keys = list(blocked_keys or [])


class _PC:
    def __init__(self):
        self.made = []

    def AllQueryAttentionKnockout(self, model, layers, blocked_keys=None, heads=None, stats=None):
        k = _FakeKnockout(model, layers, blocked_keys, heads, stats)
        self.made.append(k)
        return k


class _LM:
    model = types.SimpleNamespace(config=types.SimpleNamespace(hidden_size=16))


def test_every_draw_arm_is_registered_as_a_knockout_arm():
    assert set(sb.NONDEMO_DRAW_ARMS) <= set(sb.KNOCKOUT_ARMS)
    assert len(sb.NONDEMO_DRAW_ARMS) == 2 * sb.NONDEMO_CONTROL_N_DRAWS
    # the historical arms are untouched -- nothing was removed or repurposed
    for legacy in ("demo_all", "nondemo_random", "allpast"):
        assert legacy in sb.KNOCKOUT_ARMS


def test_a_draw_arm_runs_through_make_intervention_like_any_other_arm():
    pc, log = _PC(), {}
    spec = {"direction": "nondemo_matched_d3", "mode": "attn_knockout",
            "layers": [8, 9], "alpha": 1.0}
    sb.make_intervention(None, pc, _LM(), spec, None, control_seed=20260823,
                         demo_keys=DEMO, seq_len=SEQ, protected=PROT, draw_log=log)
    (hook,) = pc.made
    (rec,) = list(log.values())
    assert hook.blocked_keys == rec["positions"], "the hook and the artifact disagree"
    assert hook.layers == [8, 9], "the control must run in the SAME band as the arm"
    assert set(hook.blocked_keys).isdisjoint(PROT)


def test_a_composed_spec_forwards_the_draw_log_to_every_leg_without_collision():
    """Dropping a threaded argument on that recursion line is this file's house failure; and two
    legs keyed by arm name alone would store one draw under the name of two."""
    pc, log = _PC(), {}
    leg = {"direction": "nondemo_matched_d1", "mode": "attn_knockout",
           "layers": [4], "alpha": 1.0}
    sb.make_intervention(None, pc, _LM(), {"composed": [leg, dict(leg)]}, None,
                         control_seed=20260823, demo_keys=DEMO, seq_len=SEQ, protected=PROT,
                         draw_log=log)
    assert len(pc.made) == 2
    assert len(log) == 2, f"two legs recorded {len(log)} draws: {sorted(log)}"
    seeds = {v["draw_seed"] for v in log.values()}
    assert len(seeds) == 2, "both legs drew under the same seed -- retraction #7's shape"
    assert {tuple(k.blocked_keys) for k in pc.made} == {tuple(v["positions"])
                                                        for v in log.values()}


def test_the_row_record_persists_the_positions_and_the_match_ratio():
    """main() cannot be called without a model, so the persistence is pinned at the source.

    Positions are integers, so they can be written on the row; a control whose exact key set is
    only reproducible in principle is not auditable after the fact.
    """
    src = open(os.path.join(SRCB, "score_behavior.py")).read()
    i = src.index('"control_draw": (_cd or None),')
    assert '"control_draw_match_ratio": _cd_ratio,' in src[i:i + 400]
    assert '"n_control_draw_positions"' in src[i:i + 600]
    assert "draw_log=knock_draw" in src, "the row loop no longer collects the draw"
    assert "control_draw_match_ratio" in src[src.index("_feas["):], \
        "the pre-flight no longer reports the achieved match ratio"
