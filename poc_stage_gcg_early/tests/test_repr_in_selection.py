"""
P9.0 regression tests: the representation objective must enter CANDIDATE SELECTION.

THE BUG (plan §5 P9.0 item 1): _evaluate_candidates called composite_loss without
candidate_hs/reference_hs, so objectives.composite_loss took the
`lambda_repr > 0 and candidate_hs is not None` branch never, returned
r_loss = tensor(0.0) for every candidate, and selection ran on task_loss alone. Every
"the mechanism-derived objective does not help" conclusion was therefore about an
objective that only ever shaped the gradient, never the choice of candidate.

THE PROVENANCE BUG (item 2): ObjectiveWeights.repr_layers was never populated and the
reference cache directory was not a config field, so CONFIG.json showed
"repr_layers": [] and config_hash() ignored both — two arms differing only in objective
wiring shared a hash and could silently cross-resume each other's checkpoint.pt.

All tests are CPU-only and use the toy tokenizer/model from conftest.py.
Run: python -m pytest poc_stage_gcg_early/tests/test_repr_in_selection.py -v
"""
from __future__ import annotations

import gc
import sys
import warnings
from pathlib import Path
from typing import Dict, List

import pytest
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early import build_reference_cache, run_optimization as run_opt_cli
from poc_stage_gcg_early.config import (
    GCGHyperparams,
    ObjectiveWeights,
    RunConfig,
    reference_cache_content_id,
)
from poc_stage_gcg_early.gcg_optimizer import _evaluate_candidates
from poc_stage_gcg_early.model_adapter import _EMBED_PATHS_BY_FAMILY, get_embedding_matrix
from poc_stage_gcg_early.objectives import composite_loss
from poc_stage_gcg_early.suffix_token_manager import build_suffix_spans, replace_suffix

INSTRUCTION = "List three fruits"
TARGET = "Apple Banana Cherry"
SUFFIX_LEN = 4
REPR_LAYERS = [1, 2]
CANDIDATES: List[List[int]] = [
    [5, 6, 7, 3],
    [8, 9, 17, 11],
    [12, 13, 14, 10],
    [21, 5, 9, 20],
    [3, 3, 3, 3],
    [17, 17, 6, 6],
    [11, 10, 21, 8],
    [7, 20, 13, 5],
]
NEUTRAL_SUFFIX_IDS = [4] * SUFFIX_LEN  # the ' ' token, as the real reference cache uses


# ---------------------------------------------------------------------------
# The PRE-P9.0 implementation, copied verbatim from gcg_optimizer.py
# (git bb48167, lines 258-311). Used to prove byte-identical behaviour when the
# representation objective is off.
# ---------------------------------------------------------------------------

def _evaluate_candidates_pre_p90(
    model, model_family, base_spans, candidate_suffix_lists, eval_batch_size, config,
    reference_hs_per_task=None, reference_logits_per_task=None,
) -> List[Dict]:
    device = next(model.parameters()).device
    results = []

    for i in range(0, len(candidate_suffix_lists), eval_batch_size):
        batch_cands = candidate_suffix_lists[i: i + eval_batch_size]
        batch_ids = []
        for cand_ids in batch_cands:
            new_spans = replace_suffix(base_spans, torch.tensor(cand_ids))
            batch_ids.append(new_spans.input_ids)

        batch_tensor = torch.stack(batch_ids).to(device)
        attn_mask = torch.ones_like(batch_tensor)

        with torch.no_grad():
            logits = model(
                input_ids=batch_tensor,
                attention_mask=attn_mask,
            ).logits

        for j, cand_ids in enumerate(batch_cands):
            losses = composite_loss(
                logits=logits[j],
                ids=batch_tensor[j],
                loss_slice=base_spans.loss_slice,
                target_slice=base_spans.target_slice,
                lambda_repr=config.objective.lambda_repr,
                lambda_kl=config.objective.lambda_kl,
                suffix_ids=torch.tensor(cand_ids),
            )
            results.append({k: v.item() for k, v in losses.items()})

        del batch_tensor, logits
        gc.collect()

    return results


# ---------------------------------------------------------------------------
# Fixtures
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
        run_id="p90_unit",
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
    """(spans of the current suffix, repr positions, reference_hs) for the toy pair."""
    torch.manual_seed(0)
    base = _spans(toy_tokenizer, NEUTRAL_SUFFIX_IDS)
    # Same convention as run_optimization(): last N tokens of the suffix.
    repr_positions = [base.suffix_slice.stop - 2, base.suffix_slice.stop - 1]
    with torch.no_grad():
        out = tiny_model(input_ids=base.input_ids.unsqueeze(0), output_hidden_states=True)
    # fp16 CPU tensors, exactly like build_reference_cache stores them
    reference_hs = {
        layer: {p: out.hidden_states[layer][0, p, :].detach().cpu().to(torch.float16)
                for p in repr_positions}
        for layer in REPR_LAYERS
    }
    return base, repr_positions, reference_hs


# ---------------------------------------------------------------------------
# (a) repr_loss is now NON-ZERO and DIFFERENT across candidates in selection
# ---------------------------------------------------------------------------

def test_a1_pre_p90_repr_loss_is_identically_zero(toy_setup, tiny_model):
    """Documents the bug: with the old wiring every candidate scores repr_loss == 0.0."""
    base, _, _ = toy_setup
    config = _make_config(lambda_repr=1.0)
    old = _evaluate_candidates_pre_p90(
        tiny_model, "qwen3", base, CANDIDATES, len(CANDIDATES), config,
    )
    assert [r["repr_loss"] for r in old] == [0.0] * len(CANDIDATES)
    assert all(r["total_loss"] == r["task_loss"] for r in old)


def test_a2_repr_loss_nonzero_and_varies_across_candidates(toy_setup, tiny_model):
    """The fix: repr_loss enters selection, is non-zero, and discriminates candidates."""
    base, repr_positions, reference_hs = toy_setup
    config = _make_config(lambda_repr=1.0)
    new = _evaluate_candidates(
        tiny_model, "qwen3", base, CANDIDATES, len(CANDIDATES), config,
        repr_in_selection=True,
        reference_hs=reference_hs,
        repr_layers=REPR_LAYERS,
        repr_positions=repr_positions,
    )
    repr_vals = [r["repr_loss"] for r in new]
    assert len(repr_vals) == len(CANDIDATES)
    assert all(v > 0.0 for v in repr_vals), repr_vals
    assert len(set(repr_vals)) == len(CANDIDATES), repr_vals  # all distinct
    # total_loss actually carries the term
    for r in new:
        assert r["total_loss"] == pytest.approx(r["task_loss"] + 1.0 * r["repr_loss"], rel=1e-6)
    # and it changes the selected candidate's ranking vs task_loss alone
    by_task = sorted(range(len(new)), key=lambda i: new[i]["task_loss"])
    by_total = sorted(range(len(new)), key=lambda i: new[i]["total_loss"])
    assert by_task != by_total


def test_a3_sub_batching_does_not_change_any_candidate_loss(toy_setup, tiny_model):
    """Memory guard: sub-batching the hidden-state pass must be numerically inert."""
    base, repr_positions, reference_hs = toy_setup
    config = _make_config(lambda_repr=1.0)
    kwargs = dict(
        repr_in_selection=True, reference_hs=reference_hs,
        repr_layers=REPR_LAYERS, repr_positions=repr_positions,
    )
    full = _evaluate_candidates(tiny_model, "qwen3", base, CANDIDATES,
                               len(CANDIDATES), config, hs_sub_batch_size=64, **kwargs)
    split = _evaluate_candidates(tiny_model, "qwen3", base, CANDIDATES,
                                 len(CANDIDATES), config, hs_sub_batch_size=3, **kwargs)
    assert full == split


def test_a4_refusal_direction_enters_selection(toy_setup, tiny_model):
    """Gate-7 objective: the refusal-direction projection must also drive selection."""
    base, repr_positions, _ = toy_setup
    torch.manual_seed(7)
    direction = torch.randn(tiny_model.d_model)
    direction = direction / direction.norm()
    config = _make_config(lambda_refusal_dir=5.0)
    res = _evaluate_candidates(
        tiny_model, "qwen3", base, CANDIDATES, len(CANDIDATES), config,
        repr_in_selection=True,
        refusal_direction=direction,
        refusal_dir_layer=2,
        refusal_dir_positions=[base.suffix_slice.stop - 1],
        lambda_refusal_dir=5.0,
    )
    rd_vals = [r["refusal_dir_loss"] for r in res]
    assert all(v != 0.0 for v in rd_vals)
    # TinyModel's layers are position-wise linear (no attention), so the hidden state at
    # the single measured position depends only on the token AT that position: the number
    # of distinct projections is exactly the number of distinct final suffix tokens.
    assert len(set(rd_vals)) == len({c[-1] for c in CANDIDATES})
    for r in res:
        assert r["total_loss"] == pytest.approx(
            r["task_loss"] + 5.0 * r["refusal_dir_loss"], rel=1e-6
        )
    by_task = sorted(range(len(res)), key=lambda i: res[i]["task_loss"])
    by_total = sorted(range(len(res)), key=lambda i: res[i]["total_loss"])
    assert by_task != by_total


# ---------------------------------------------------------------------------
# (b) with lambda=0 the selected candidate is identical to before the change
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("eval_batch_size", [len(CANDIDATES), 3, 1])
def test_b1_task_only_arm_is_byte_identical_to_pre_p90(toy_setup, tiny_model, eval_batch_size):
    """lambda_repr = 0: every loss component and the argmin must be unchanged."""
    base, _, _ = toy_setup
    config = _make_config(lambda_repr=0.0)
    old = _evaluate_candidates_pre_p90(
        tiny_model, "qwen3", base, CANDIDATES, eval_batch_size, config,
    )
    new = _evaluate_candidates(
        tiny_model, "qwen3", base, CANDIDATES, eval_batch_size, config,
    )
    assert new == old  # exact float equality, all components
    for key in ("task_loss", "total_loss"):
        assert (min(range(len(new)), key=lambda i: new[i][key])
                == min(range(len(old)), key=lambda i: old[i][key]))


def test_b2_repr_in_selection_false_forces_the_old_path(toy_setup, tiny_model):
    """Explicit opt-out reproduces the old numbers even with a cache and lambda_repr > 0."""
    base, repr_positions, reference_hs = toy_setup
    config = _make_config(lambda_repr=1.0)
    old = _evaluate_candidates_pre_p90(
        tiny_model, "qwen3", base, CANDIDATES, len(CANDIDATES), config,
    )
    off = _evaluate_candidates(
        tiny_model, "qwen3", base, CANDIDATES, len(CANDIDATES), config,
        repr_in_selection=False,
        reference_hs=reference_hs,
        repr_layers=REPR_LAYERS,
        repr_positions=repr_positions,
    )
    assert off == old


# ---------------------------------------------------------------------------
# (c) config_hash() provenance
# ---------------------------------------------------------------------------

def test_c1_new_fields_at_default_do_not_change_the_hash():
    """Backward compatibility: pre-P9.0 configs keep their stored hash."""
    base = _make_config()
    explicit_defaults = _make_config(
        repr_in_selection=None, repr_selection_sub_batch=8,
        reference_cache_id=None, objective_name=None,
    )
    assert base.config_hash() == explicit_defaults.config_hash()


@pytest.mark.parametrize("dir_name,expected", [
    ("outputs/stage_gcg_full_v2_userfix/gcg_full_qwen3_7b_seed44", "667c66fed0bea00e"),
    ("outputs/stage_gcg_full_v2_userfix/gcg_full_qwen3_8_rd_lambda03", "0f780c49b883b917"),
])
def test_c2_real_run_hashes_still_reproduce(dir_name, expected):
    """Regression against two real runs: hash == the value stored in their checkpoint.pt."""
    run_dir = _REPO_ROOT / dir_name
    if not (run_dir / "CONFIG.json").exists():
        pytest.skip(f"run directory not available: {run_dir}")
    cfg = RunConfig.from_json((run_dir / "CONFIG.json").read_text(encoding="utf-8"))
    assert cfg.config_hash() == expected


def test_c3_repr_layers_changes_the_hash():
    a = _make_config(lambda_repr=1.0, repr_layers=[0, 5, 10])
    b = _make_config(lambda_repr=1.0, repr_layers=[0, 5, 20])
    empty = _make_config(lambda_repr=1.0, repr_layers=[])
    assert a.config_hash() != b.config_hash()
    assert a.config_hash() != empty.config_hash()


def test_c4_reference_cache_id_and_objective_name_change_the_hash():
    base = _make_config(lambda_repr=1.0, repr_layers=[0, 5])
    cache_a = _make_config(lambda_repr=1.0, repr_layers=[0, 5], reference_cache_id="aaaa1111")
    cache_b = _make_config(lambda_repr=1.0, repr_layers=[0, 5], reference_cache_id="bbbb2222")
    named = _make_config(lambda_repr=1.0, repr_layers=[0, 5], objective_name="refusal_dir_L22")
    in_sel = _make_config(lambda_repr=1.0, repr_layers=[0, 5], repr_in_selection=False)
    hashes = {base.config_hash(), cache_a.config_hash(), cache_b.config_hash(),
              named.config_hash(), in_sel.config_hash()}
    assert len(hashes) == 5


def test_c5_new_fields_land_in_config_json():
    cfg = _make_config(lambda_repr=1.0, repr_layers=[0, 5],
                       reference_cache_id="deadbeefdeadbeef",
                       objective_name="repr_cosine")
    written = cfg.to_json()
    assert '"repr_layers": [' in written
    assert '"reference_cache_id": "deadbeefdeadbeef"' in written
    assert '"objective_name": "repr_cosine"' in written
    # and survives the round-trip used on resume
    assert RunConfig.from_json(written).config_hash() == cfg.config_hash()


def test_c6_reference_cache_content_id_tracks_manifest_content(tmp_path):
    d1, d2, d3 = tmp_path / "c1", tmp_path / "c2", tmp_path / "c3"
    for d, body in ((d1, '{"task_id": "t1", "cache_key": "k1"}\n'),
                    (d2, '{"task_id": "t1", "cache_key": "k1"}\n'),
                    (d3, '{"task_id": "t1", "cache_key": "k2"}\n')):
        d.mkdir()
        (d / "REFERENCE_CACHE_MANIFEST.json").write_text(body, encoding="utf-8")
    assert reference_cache_content_id(d1) == reference_cache_content_id(d2)
    assert reference_cache_content_id(d1) != reference_cache_content_id(d3)
    with pytest.raises(FileNotFoundError):
        reference_cache_content_id(tmp_path / "missing")


# ---------------------------------------------------------------------------
# (d) llama model family
# ---------------------------------------------------------------------------

def test_d1_llama_embedding_path_resolves(tiny_model):
    assert _EMBED_PATHS_BY_FAMILY["llama"] == ["model.embed_tokens"]
    w = get_embedding_matrix(tiny_model, "llama")
    assert w.shape == (tiny_model.vocab_size, tiny_model.d_model)


@pytest.mark.parametrize("module,argv", [
    (run_opt_cli, ["--model-family", "llama"]),
    (build_reference_cache, ["--model-family", "llama"]),
])
def test_d2_llama_is_an_accepted_cli_choice(module, argv, capsys):
    """argparse rejects an unknown --model-family before the required-args check."""
    with pytest.raises(SystemExit):
        module.main(argv)
    err = capsys.readouterr().err
    assert "invalid choice" not in err, err
    assert "required" in err, err


# ---------------------------------------------------------------------------
# (e) end-to-end: the whole optimization loop, not just _evaluate_candidates
# ---------------------------------------------------------------------------

def _run_loop(tmp_path, toy_tokenizer, tiny_model, objective, reference_hs, repr_layers):
    from poc_stage_gcg_early.config import SurrogateTask
    from poc_stage_gcg_early.gcg_optimizer import run_optimization

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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_optimization(
            model=tiny_model, tokenizer=toy_tokenizer, model_family="qwen3", tasks=[task],
            config=config, reference_cache=None, output_dir=tmp_path,
            reference_hs_per_task=reference_hs, repr_layers=repr_layers,
        )
    import json
    return [json.loads(l) for l in
            (tmp_path / "ITERATION_LOG.jsonl").read_text(encoding="utf-8").splitlines()]


def test_e1_full_loop_task_only_logs_zero_repr(tmp_path, toy_tokenizer, tiny_model):
    rows = _run_loop(tmp_path, toy_tokenizer, tiny_model, ObjectiveWeights(), None, None)
    assert len(rows) == 3
    assert all(r["repr_loss"] == 0.0 for r in rows)
    assert all(r["total_loss"] == r["task_loss"] for r in rows)


def test_e2_full_loop_repr_arm_selects_on_repr(tmp_path, toy_setup, toy_tokenizer, tiny_model):
    """The candidate that wins must be one repr_loss helped choose."""
    _, repr_positions, reference_hs = toy_setup
    objective = ObjectiveWeights(lambda_repr=1.0, repr_positions=len(repr_positions),
                                 repr_layers=REPR_LAYERS,
                                 reference_cache_id="cafebabecafebabe",
                                 objective_name="repr_cosine")
    rows = _run_loop(tmp_path, toy_tokenizer, tiny_model, objective,
                     {"t0": reference_hs}, REPR_LAYERS)
    assert len(rows) == 3
    assert all(r["repr_loss"] > 0.0 for r in rows)
    assert all(r["total_loss"] > r["task_loss"] for r in rows)
    # A suffix is accepted purely because it lowers repr_loss at equal task_loss —
    # impossible before P9.0, where total_loss == task_loss for every candidate.
    assert rows[-1]["repr_loss"] < rows[0]["repr_loss"]
    assert rows[-1]["task_loss"] == pytest.approx(rows[0]["task_loss"])
