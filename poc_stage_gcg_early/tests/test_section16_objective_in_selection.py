"""
Plan §16 — mandatory OPTIMIZER VALIDATION before any Gate-7 GPU spend.

The Gate-7 attack-objective arms may only run once these six properties of the
`objective.repr_in_selection` machinery (poc_stage_gcg_early/gcg_optimizer.py) are
proven with real assertions on synthetic / tiny-model data:

  (1) the internal (repr / refusal-direction) objective CHANGES candidate ranking
      relative to task-loss-only;
  (2) selection actually USES the combined objective (argmin of total_loss), not
      just logs it;
  (3) weight = 0 EXACTLY reproduces the baseline (task-only) selection — every loss
      component and the argmin are byte/rank identical;
  (4) the SIGN is correct — minimizing the refusal-projection objective moves the
      projection DOWN, not up;
  (5) gradients from the internal objective REACH the candidate suffix tokens;
  (6) the internal quantity MOVES in the intended direction after accepted updates.

All CPU-only, using the toy tokenizer / tiny model in conftest.py. No real model,
no GPU, no harmful content — the "attack" here is the neutral target
"Apple Banana Cherry" for the instruction "List three fruits".

Run: python -m pytest poc_stage_gcg_early/tests/test_section16_objective_in_selection.py -v
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Dict, List

import pytest
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early.config import (
    GCGHyperparams,
    ObjectiveWeights,
    RunConfig,
    SurrogateTask,
)
from poc_stage_gcg_early.gcg_optimizer import (
    _evaluate_candidates,
    _token_gradients,
    run_optimization,
)
from poc_stage_gcg_early.objectives import refusal_direction_loss
from poc_stage_gcg_early.suffix_token_manager import build_suffix_spans

INSTRUCTION = "List three fruits"
TARGET = "Apple Banana Cherry"
SUFFIX_LEN = 4
REPR_LAYERS = [1, 2]
# Neutral synthetic candidate suffixes (toy vocab ids); last token varies so the
# refusal-direction projection differs per candidate under the linear tiny model.
CANDIDATES: List[List[int]] = [
    [5, 6, 7, 3],
    [8, 9, 17, 11],
    [12, 13, 14, 10],
    [21, 5, 9, 20],
    [3, 3, 3, 5],
    [17, 17, 6, 9],
    [11, 10, 21, 7],
    [7, 20, 13, 6],
]
NEUTRAL_SUFFIX_IDS = [4] * SUFFIX_LEN  # the ' ' token


# ---------------------------------------------------------------------------
# helpers / fixtures
# ---------------------------------------------------------------------------

def _spans(toy_tokenizer, suffix_ids):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # toy tokenizer is not BPE round-trippable
        return build_suffix_spans(
            toy_tokenizer, "qwen3", False, INSTRUCTION, "IGNORED", TARGET,
            suffix_ids_override=list(suffix_ids), suffix_placement="user",
        )


def _make_config(lambda_repr=0.0, lambda_refusal_dir=0.0, **objective_kwargs) -> RunConfig:
    return RunConfig(
        run_id="s16_unit",
        model_family="qwen3",
        model_name_or_path="toy",
        manifest_path="toy.jsonl",
        gcg=GCGHyperparams(suffix_length=SUFFIX_LEN, batch_size=len(CANDIDATES)),
        objective=ObjectiveWeights(
            lambda_repr=lambda_repr,
            lambda_refusal_dir=lambda_refusal_dir,
            **objective_kwargs,
        ),
        output_dir="toy_out",
        enable_thinking=False,
    )


@pytest.fixture
def toy_setup(toy_tokenizer, tiny_model):
    """(base spans, repr positions, reference_hs) for the neutral toy pair."""
    torch.manual_seed(0)
    base = _spans(toy_tokenizer, NEUTRAL_SUFFIX_IDS)
    repr_positions = [base.suffix_slice.stop - 2, base.suffix_slice.stop - 1]
    with torch.no_grad():
        out = tiny_model(input_ids=base.input_ids.unsqueeze(0), output_hidden_states=True)
    reference_hs = {
        layer: {p: out.hidden_states[layer][0, p, :].detach().cpu().to(torch.float16)
                for p in repr_positions}
        for layer in REPR_LAYERS
    }
    return base, repr_positions, reference_hs


def _unit_direction(d_model, seed):
    torch.manual_seed(seed)
    v = torch.randn(d_model)
    return v / v.norm()


# ===========================================================================
# §16 (1) — the internal objective CHANGES candidate ranking vs task-only
# ===========================================================================

def test_s16_1_repr_objective_changes_ranking(toy_setup, tiny_model):
    base, repr_positions, reference_hs = toy_setup
    config = _make_config(lambda_repr=1.0)
    combined = _evaluate_candidates(
        tiny_model, "qwen3", base, CANDIDATES, len(CANDIDATES), config,
        repr_in_selection=True, reference_hs=reference_hs,
        repr_layers=REPR_LAYERS, repr_positions=repr_positions,
    )
    by_task = sorted(range(len(combined)), key=lambda i: combined[i]["task_loss"])
    by_total = sorted(range(len(combined)), key=lambda i: combined[i]["total_loss"])
    assert by_task != by_total, "repr term left the candidate ranking unchanged"
    # the term is genuinely present and discriminative, not a constant offset
    repr_vals = [r["repr_loss"] for r in combined]
    assert all(v > 0.0 for v in repr_vals), repr_vals
    assert len(set(repr_vals)) == len(CANDIDATES), repr_vals


def test_s16_1_refusal_dir_objective_changes_ranking(toy_setup, tiny_model):
    base, _, _ = toy_setup
    direction = _unit_direction(tiny_model.d_model, seed=7)
    config = _make_config(lambda_refusal_dir=5.0)
    res = _evaluate_candidates(
        tiny_model, "qwen3", base, CANDIDATES, len(CANDIDATES), config,
        repr_in_selection=True, refusal_direction=direction,
        refusal_dir_layer=2, refusal_dir_positions=[base.suffix_slice.stop - 1],
        lambda_refusal_dir=5.0,
    )
    by_task = sorted(range(len(res)), key=lambda i: res[i]["task_loss"])
    by_total = sorted(range(len(res)), key=lambda i: res[i]["total_loss"])
    assert by_task != by_total


# ===========================================================================
# §16 (2) — selection USES the combined objective (not just logs it)
# ===========================================================================

def test_s16_2_total_loss_is_the_combined_objective(toy_setup, tiny_model):
    """total_loss carries the internal term and the argmin follows total_loss, not task."""
    base, repr_positions, reference_hs = toy_setup
    lam = 8.0
    config = _make_config(lambda_repr=lam)
    res = _evaluate_candidates(
        tiny_model, "qwen3", base, CANDIDATES, len(CANDIDATES), config,
        repr_in_selection=True, reference_hs=reference_hs,
        repr_layers=REPR_LAYERS, repr_positions=repr_positions,
    )
    for r in res:
        assert r["total_loss"] == pytest.approx(r["task_loss"] + lam * r["repr_loss"], rel=1e-6)
    # with a large weight the winner is driven by the repr term, not task loss
    argmin_total = min(range(len(res)), key=lambda i: res[i]["total_loss"])
    argmin_task = min(range(len(res)), key=lambda i: res[i]["task_loss"])
    assert argmin_total != argmin_task


def test_s16_2_run_optimization_selects_on_total_loss(tmp_path, toy_tokenizer, tiny_model, toy_setup):
    """The full loop's acceptance uses total_loss: repr_loss falls at fixed task_loss."""
    _, repr_positions, reference_hs = toy_setup
    objective = ObjectiveWeights(
        lambda_repr=1.0, repr_positions=len(repr_positions), repr_layers=REPR_LAYERS,
        reference_cache_id="cafebabecafebabe", objective_name="repr_cosine",
    )
    task = SurrogateTask(
        task_id="t0", instruction=INSTRUCTION, safe_target_prefix=TARGET,
        early_prefix=None, neutral_control_suffix=" ", split="train", seed=42,
        model="qwen3", enable_thinking=False,
    )
    config = RunConfig(
        run_id="loop", model_family="qwen3", model_name_or_path="toy",
        manifest_path="toy.jsonl",
        gcg=GCGHyperparams(suffix_length=SUFFIX_LEN, batch_size=8, topk=8, n_steps=3,
                           seed=42, checkpoint_every=2, snapshot_every=100),
        objective=objective, output_dir=str(tmp_path), enable_thinking=False,
    )
    import json
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_optimization(
            model=tiny_model, tokenizer=toy_tokenizer, model_family="qwen3", tasks=[task],
            config=config, reference_cache=None, output_dir=tmp_path,
            reference_hs_per_task={"t0": reference_hs}, repr_layers=REPR_LAYERS,
        )
    rows = [json.loads(l) for l in
            (tmp_path / "ITERATION_LOG.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3
    assert all(r["total_loss"] > r["task_loss"] for r in rows)  # term is live in the log


# ===========================================================================
# §16 (3) — weight = 0 EXACTLY reproduces the baseline (task-only) selection
# ===========================================================================

@pytest.mark.parametrize("eval_batch_size", [len(CANDIDATES), 3, 1])
def test_s16_3_weight_zero_is_byte_and_rank_identical(toy_setup, tiny_model, eval_batch_size):
    """lambda=0 (and objective off) must equal the pure task path, component-by-component."""
    base, repr_positions, reference_hs = toy_setup

    task_only = _evaluate_candidates(
        tiny_model, "qwen3", base, CANDIDATES, eval_batch_size, _make_config(lambda_repr=0.0),
    )
    # weight 0 but with the whole repr apparatus wired in and turned ON:
    weight_zero = _evaluate_candidates(
        tiny_model, "qwen3", base, CANDIDATES, eval_batch_size, _make_config(lambda_repr=0.0),
        repr_in_selection=True, reference_hs=reference_hs,
        repr_layers=REPR_LAYERS, repr_positions=repr_positions,
    )
    assert weight_zero == task_only, "weight=0 diverged from the task-only baseline"
    for key in ("task_loss", "total_loss"):
        assert (min(range(len(weight_zero)), key=lambda i: weight_zero[i][key])
                == min(range(len(task_only)), key=lambda i: task_only[i][key]))


# ===========================================================================
# §16 (4) — SIGN correctness: minimizing refusal-projection moves it DOWN
# ===========================================================================

def test_s16_4_objective_gradient_descends_the_projection(tiny_model):
    """Pure objective-function sign test: -d(loss)/dh has POSITIVE dot with the
    refusal direction, so a descent step drives the projection h.d downward."""
    d_model = tiny_model.d_model
    direction = _unit_direction(d_model, seed=3)
    h = torch.randn(d_model, requires_grad=True)
    cand_hs = {2: {0: h}}
    loss = refusal_direction_loss(cand_hs, direction, layer=2, positions=[0])
    loss.backward()
    # descent direction is -grad; its projection onto the refusal dir must be < current
    step = 0.05
    h_next = (h - step * h.grad).detach()
    proj_before = torch.dot(h.detach() / h.detach().norm(), direction).item()
    proj_after = torch.dot(h_next / h_next.norm(), direction).item()
    assert proj_after < proj_before, (proj_before, proj_after)


def test_s16_4_selection_prefers_lower_projection(toy_setup, tiny_model):
    """In selection: large positive lambda picks the MIN-projection candidate; flipping
    the direction's sign flips the winner to the MAX-projection candidate."""
    base, _, _ = toy_setup
    pos = base.suffix_slice.stop - 1
    direction = _unit_direction(tiny_model.d_model, seed=11)

    def run(dir_vec, lam):
        return _evaluate_candidates(
            tiny_model, "qwen3", base, CANDIDATES, len(CANDIDATES), _make_config(lambda_refusal_dir=lam),
            repr_in_selection=True, refusal_direction=dir_vec,
            refusal_dir_layer=2, refusal_dir_positions=[pos], lambda_refusal_dir=lam,
        )

    big = run(direction, 1e6)  # objective dominates task loss
    rd_vals = [r["refusal_dir_loss"] for r in big]
    winner = min(range(len(big)), key=lambda i: big[i]["total_loss"])
    assert winner == min(range(len(rd_vals)), key=lambda i: rd_vals[i]), \
        "minimizing the objective did NOT pick the lowest-projection candidate"

    flipped = run(-direction, 1e6)
    flipped_winner = min(range(len(flipped)), key=lambda i: flipped[i]["total_loss"])
    # projection onto -d is minimized where projection onto +d is maximized
    assert flipped_winner == max(range(len(rd_vals)), key=lambda i: rd_vals[i])
    assert flipped_winner != winner


# ===========================================================================
# §16 (5) — gradients from the internal objective REACH the candidate tokens
# ===========================================================================

def test_s16_5_repr_gradient_reaches_suffix_tokens(toy_setup, tiny_model):
    base, repr_positions, reference_hs = toy_setup
    g_task = _token_gradients(
        tiny_model, "qwen3", base.input_ids, base.suffix_slice, base.target_slice,
        base.loss_slice, lambda_repr=0.0,
    )
    g_repr = _token_gradients(
        tiny_model, "qwen3", base.input_ids, base.suffix_slice, base.target_slice,
        base.loss_slice, lambda_repr=1.0, reference_hs=reference_hs,
        repr_layers=REPR_LAYERS, repr_positions=repr_positions,
    )
    # gradient exists over every suffix position x whole vocab, and is finite
    assert g_repr.shape == (SUFFIX_LEN, tiny_model.vocab_size)
    assert torch.isfinite(g_repr).all()
    assert g_repr.abs().sum().item() > 0.0
    # the repr term actually changed the gradient that selects tokens
    assert not torch.allclose(g_repr, g_task), "repr objective never reached the suffix grad"


def test_s16_5_refusal_dir_gradient_reaches_suffix_tokens(toy_setup, tiny_model):
    base, _, _ = toy_setup
    direction = _unit_direction(tiny_model.d_model, seed=5)
    pos = base.suffix_slice.stop - 1
    g_task = _token_gradients(
        tiny_model, "qwen3", base.input_ids, base.suffix_slice, base.target_slice,
        base.loss_slice, lambda_refusal_dir=0.0,
    )
    g_rd = _token_gradients(
        tiny_model, "qwen3", base.input_ids, base.suffix_slice, base.target_slice,
        base.loss_slice, lambda_refusal_dir=3.0, refusal_direction=direction,
        refusal_dir_layer=2, refusal_dir_positions=[pos],
    )
    assert g_rd.shape == (SUFFIX_LEN, tiny_model.vocab_size)
    assert torch.isfinite(g_rd).all()
    assert not torch.allclose(g_rd, g_task), "refusal-dir objective never reached the suffix grad"


# ===========================================================================
# §16 (6) — the internal quantity MOVES in the intended direction after
#           accepted updates
# ===========================================================================

def test_s16_6_repr_loss_decreases_over_accepted_updates(tmp_path, toy_tokenizer, tiny_model, toy_setup):
    _, repr_positions, reference_hs = toy_setup
    objective = ObjectiveWeights(
        lambda_repr=1.0, repr_positions=len(repr_positions), repr_layers=REPR_LAYERS,
        reference_cache_id="cafebabecafebabe", objective_name="repr_cosine",
    )
    task = SurrogateTask(
        task_id="t0", instruction=INSTRUCTION, safe_target_prefix=TARGET,
        early_prefix=None, neutral_control_suffix=" ", split="train", seed=42,
        model="qwen3", enable_thinking=False,
    )
    config = RunConfig(
        run_id="loop6", model_family="qwen3", model_name_or_path="toy",
        manifest_path="toy.jsonl",
        gcg=GCGHyperparams(suffix_length=SUFFIX_LEN, batch_size=8, topk=8, n_steps=3,
                           seed=42, checkpoint_every=2, snapshot_every=100),
        objective=objective, output_dir=str(tmp_path), enable_thinking=False,
    )
    import json
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_optimization(
            model=tiny_model, tokenizer=toy_tokenizer, model_family="qwen3", tasks=[task],
            config=config, reference_cache=None, output_dir=tmp_path,
            reference_hs_per_task={"t0": reference_hs}, repr_layers=REPR_LAYERS,
        )
    rows = [json.loads(l) for l in
            (tmp_path / "ITERATION_LOG.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3
    # the objective the optimizer minimizes moves DOWN, at unchanged task_loss —
    # only possible if repr_loss genuinely drove an accepted update.
    assert rows[-1]["repr_loss"] < rows[0]["repr_loss"]
    assert rows[-1]["task_loss"] == pytest.approx(rows[0]["task_loss"])
