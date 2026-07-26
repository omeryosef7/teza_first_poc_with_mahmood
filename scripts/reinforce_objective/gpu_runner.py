"""
D4.5 / Package-2 — REINFORCE GPU RUNNER (wiring of the verified pure estimator).

Sprint Completion Plan §D4 ("REINFORCE-style behavioral objective") + §5 "Pkg 2 —
REINFORCE gradient smoke". This module is the CONCRETE wiring of the ALREADY-
VERIFIED pure-Python estimator (`scripts/reinforce_objective/reinforce.py`:
`reinforce_advantages` / `reinforce_loss`, the signed teacher-forced-CE surrogate,
and the GPU call-sites A/B it marks as deferred) into a real target-model loop.

DESIGN CONTRACT (what runs where)
---------------------------------
The estimator math is pure Python and torch-free; it is unit-tested on CPU in
`tests/test_reinforce_objective.py`. This runner adds the *orchestration* around
it and the two real-model call-sites:

  * GPU CALL-SITE A — sampling K free generations (non-differentiable).
  * GPU CALL-SITE B — teacher-forced log-prob of each sampled response under the
    frozen target (a differentiable forward over FIXED sampled tokens).

To keep the non-model core CPU-unit-testable (and importable where torch is
absent, e.g. under `/usr/bin/python3 -m pytest`), the model is INJECTED as a
duck-typed object implementing the `TargetModel` protocol below. Every heavy
import (torch, `poc_stage4.qwen3_model`, `poc_stage_gcg_early.model_adapter`,
`scripts.jailbreak_rewards`) is LAZY — done inside a function body, never at
module top — mirroring the established pattern in `proxy_ce_rerank.py` /
`candidate_pool.py`. Importing this module therefore pulls in NO torch.

  * `build_prompt`            — reuse the existing chat-template adapter; trigger
                                in the USER turn; `enable_thinking` recorded.
  * `sample_responses`        — K responses (seed + greedy + low-temp sampled +
                                best-historical), §D4.1 composition. GPU site A.
  * `teacher_forced_logprob`  — sum/mean token log-prob of a response. GPU site B.
  * `score_responses`         — inject a `jailbreak_rewards` reward (goal passed).
  * `reinforce_step`          — assemble rewards -> RLOO advantages -> the signed
                                CE surrogate; STOP-GRADIENT on the advantages;
                                produce the trigger-token gradient signal for
                                GCGPlus proposal + behavioral reward for SELECTION
                                (REINFORCE-MAC, §D4).

The REINFORCE-MAC picture (§D4, and `reinforce.ReinforceGCGAdapter`): the
per-response advantages weight a teacher-forced CE whose gradient w.r.t. the
trigger tokens is exactly the REINFORCE gradient — that is the GCGPlus Stage-1
PROPOSAL signal (differentiable proxy). The behavioral reward then drives the
GCGPlus Stage-2 candidate SELECTION.

enable_thinking CONSISTENCY (docs/TROPT_PIN_AND_BYTEVERIFY.md §C2)
------------------------------------------------------------------
The SAME `enable_thinking` MUST be used for the teacher-forced/optimization
prompt AND for the free-generation the reward scores — otherwise one distribution
is optimized and another evaluated. `build_prompt` records the flag it used;
`reinforce_step` echoes it into its log so a run is auditable. Qwen3's template
with `enable_thinking=False` injects an empty `<think>\n\n</think>` block that the
default (True) does NOT — keep both sides equal.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Sequence

from .reinforce import ReinforceLossResult, reinforce_loss

# A reward callable: (original_goal, response_text) -> reward in [0, 1] (D2.2:
# the reward MUST receive the ORIGINAL goal, not just the response).
RewardFn = Callable[[str, str], float]


# ---------------------------------------------------------------------------
# Model interface (duck-typed; real GPU wrapper + test mock both implement it)
# ---------------------------------------------------------------------------

class TargetModel:  # documentation-only protocol (kept a plain class, no torch)
    """Duck-typed contract the frozen target model must satisfy for this runner.

    Implemented for real by `HFTargetModel` (GPU-only, below) and by a lightweight
    deterministic stub in `tests/test_gpu_runner.py`. Only these two methods are
    ever called by the runner core, which is what makes the core CPU-testable.

    generate_one(prompt, *, do_sample, temperature, seed, max_new_tokens) -> str
        One free generation (GPU CALL-SITE A). `do_sample=False` == greedy.

    teacher_forced_logprob(prompt, response, *, reduction) -> float | tensor
        Total ('sum') or per-token ('mean') teacher-forced log-prob of `response`
        conditioned on `prompt` (GPU CALL-SITE B). On the real model this returns
        a torch scalar carrying grad through the trigger tokens; the stub returns
        a plain float. The runner uses `_to_float(...)` for the estimator and
        keeps the raw object for the differentiable surrogate.
    """

    def generate_one(self, prompt, *, do_sample, temperature, seed, max_new_tokens):  # pragma: no cover
        raise NotImplementedError

    def teacher_forced_logprob(self, prompt, response, *, reduction="sum"):  # pragma: no cover
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Stop-gradient + surrogate builder (the CRITICAL detach requirement)
# ---------------------------------------------------------------------------

def stop_gradient(x: Any) -> Any:
    """Return a grad-free view of `x` (REINFORCE stop-gradient on the advantage).

    Torch tensor -> `x.detach()`; plain number -> `float(x)`. The advantages /
    CE weights are treated as CONSTANTS in the surrogate: we never backprop
    through the reward or the sampling (that is what makes this REINFORCE and not
    some differentiable-reward objective). Every weight entering the surrogate
    loss is passed through this first.
    """
    detach = getattr(x, "detach", None)
    if callable(detach):
        return detach()
    return float(x)


def build_surrogate_loss(
    response_logprobs: Sequence[Any],
    ce_weights: Sequence[Any],
):
    """Assemble the differentiable surrogate  L = mean_i( sg(A_i) * (-logprob_i) ).

    `response_logprobs[i]` is log pi(y_i) (a torch scalar on GPU, or a float in
    tests); `ce_weights[i]` is the advantage A_i. Each weight is run through
    `stop_gradient` FIRST, so dL/d(reward)=0 and the only gradient path is through
    the model forward that produced `logprob_i` (i.e. through the trigger tokens).

    Returns whatever type the arithmetic yields: a torch scalar when the logprobs
    are tensors (ready for `.backward()` at the GPU call-site), else a Python
    float equal to `reinforce_loss(...).loss`.
    """
    k = len(response_logprobs)
    if k == 0:
        return 0.0
    if len(ce_weights) != k:
        raise ValueError(
            f"length mismatch: {k} logprobs vs {len(ce_weights)} ce_weights"
        )
    total = None
    for lp, w in zip(response_logprobs, ce_weights):
        w_sg = stop_gradient(w)              # <-- STOP-GRADIENT on the advantage
        term = w_sg * (-lp)                  # A_i * CE_i,  CE_i = -log pi(y_i)
        total = term if total is None else total + term
    return total / k


def _to_float(x: Any) -> float:
    """Extract a Python float from a torch scalar (`.item()`) or a plain number."""
    item = getattr(x, "item", None)
    if callable(item):
        return float(item())
    return float(x)


def _reward_value(r: Any) -> float:
    """Accept either a bare float reward or a `jailbreak_rewards.RewardOutput`."""
    reward_attr = getattr(r, "reward", None)
    if reward_attr is not None:
        return float(reward_attr)
    return float(r)


# ---------------------------------------------------------------------------
# build_prompt — reuse the chat-template adapter; trigger in the USER turn
# ---------------------------------------------------------------------------

@dataclass
class BuiltPrompt:
    """A templated prompt plus the metadata needed to keep optimize==eval aligned."""

    text: str
    user_content: str
    enable_thinking: bool
    model_family: str

    def as_dict(self) -> dict:
        return {
            "prompt_text": self.text,
            "user_content": self.user_content,
            "enable_thinking": self.enable_thinking,
            "model_family": self.model_family,
        }


def _apply_chat_template(tokenizer, user_content: str, model_family: str, enable_thinking: bool) -> str:
    """Delegate to `poc_stage_gcg_early.model_adapter.apply_chat_template`.

    That module imports torch at top level, so on a torch-free CPU (tests) the
    import raises; we then fall back to the BYTE-IDENTICAL inline call the adapter
    itself makes (`tokenizer.apply_chat_template([{user}], tokenize=False,
    add_generation_prompt=True, enable_thinking=...)` with a TypeError fallback
    for tokenizers lacking the kwarg). Equivalence is byte-verified in
    docs/TROPT_PIN_AND_BYTEVERIFY.md §C2.
    """
    try:
        # GPU/torch call-site (preferred path on a real run): reuse the adapter.
        from poc_stage_gcg_early.model_adapter import apply_chat_template  # noqa: PLC0415
        return apply_chat_template(
            tokenizer, user_content, model_family, enable_thinking=enable_thinking,
            add_generation_prompt=True,
        )
    except Exception:
        # Torch-free fallback == the adapter's own tokenizer call (byte-identical).
        messages = [{"role": "user", "content": user_content}]
        kwargs = dict(tokenize=False, add_generation_prompt=True)
        try:
            return tokenizer.apply_chat_template(messages, **kwargs, enable_thinking=enable_thinking)
        except TypeError:
            return tokenizer.apply_chat_template(messages, **kwargs)


def build_prompt(
    tokenizer,
    instruction: str,
    trigger: str,
    *,
    enable_thinking: bool,
    model_family: str = "qwen3",
) -> BuiltPrompt:
    """Build the templated prompt with the trigger/suffix in the USER turn.

    User content is `f"{instruction} {trigger}"` — the trigger sits at the END of
    the user message, immediately before the turn delimiter, matching
    `scripts/phase3_tropt_optimize.py` (`template = f"{instruction} {{OPTIMIZED_TRIGGER}}"`)
    and the byte-verified placement in docs/TROPT_PIN_AND_BYTEVERIFY.md §C2 (NOT
    the assistant turn — that was the GCG placement bug fixed project-wide).

    `enable_thinking` is RECORDED on the returned `BuiltPrompt` and MUST equal the
    flag used by the eval / free-generation (see module docstring).
    """
    user_content = f"{instruction} {trigger}"
    text = _apply_chat_template(tokenizer, user_content, model_family, enable_thinking)
    return BuiltPrompt(
        text=str(text),
        user_content=user_content,
        enable_thinking=bool(enable_thinking),
        model_family=model_family,
    )


# ---------------------------------------------------------------------------
# sample_responses — K responses per §D4.1 (seed + greedy + sampled + historical)
# ---------------------------------------------------------------------------

@dataclass
class SampledResponses:
    """K sampled responses plus per-response provenance (for auditing §D4.1)."""

    responses: list[str]
    provenance: list[str]

    def __len__(self) -> int:
        return len(self.responses)


def sample_responses(
    model: "TargetModel",
    prompt: str,
    K: int,
    *,
    seeds: Optional[Sequence[int]] = None,
    seed_response: Optional[str] = None,
    best_historical: Optional[str] = None,
    temperature: float = 0.7,
    max_new_tokens: int = 2048,  # was 256 → truncated thinking models mid-<think> (Gate-3 artifact)
) -> SampledResponses:
    """Assemble exactly K responses for one REINFORCE step (plan §D4.1).

    Composition (priority order, so the mix is deterministic and greedy is always
    present when K>=1):
      1. GREEDY  — `generate_one(do_sample=False)` (the model's mode).
      2. SEED    — a caller-provided `seed_response` (e.g. the target/affirm string
                   or a hand-seeded jailbreak), included as-is (no generation).
      3. BEST-HISTORICAL — the best response seen so far across steps (a running
                   buffer the caller maintains), included as-is.
      4. LOW-TEMP SAMPLED — fill the remaining slots with
                   `generate_one(do_sample=True, temperature=...)`, one per seed in
                   `seeds` (falling back to 1000+i when seeds run out).
    The list is truncated to exactly K in that priority order.

    Package-2 smoke uses K=2 => [greedy, 1 sampled]; the main runs use K=4 =>
    [greedy, 3 sampled] (or greedy+seed+historical+sampled when those are given).

    GPU CALL-SITE A: every `model.generate_one(...)` is a real (non-differentiable)
    generation. `seed_response` / `best_historical` are strings, not generations.
    """
    if K < 1:
        raise ValueError(f"K must be >= 1, got {K}")

    responses: list[str] = []
    provenance: list[str] = []

    def _add(text: str, tag: str) -> None:
        if len(responses) < K:
            responses.append(str(text))
            provenance.append(tag)

    # 1. greedy (GPU CALL-SITE A)
    greedy = model.generate_one(
        prompt, do_sample=False, temperature=0.0, seed=None, max_new_tokens=max_new_tokens
    )
    _add(greedy, "greedy")

    # 2. seed response (no generation)
    if seed_response is not None:
        _add(seed_response, "seed")

    # 3. best-historical (no generation)
    if best_historical is not None:
        _add(best_historical, "best_historical")

    # 4. low-temp sampled fill (GPU CALL-SITE A)
    seed_list = list(seeds or [])
    i = 0
    while len(responses) < K:
        s = seed_list[i] if i < len(seed_list) else (1000 + i)
        sampled = model.generate_one(
            prompt, do_sample=True, temperature=temperature, seed=int(s),
            max_new_tokens=max_new_tokens,
        )
        _add(sampled, f"sampled(seed={int(s)})")
        i += 1

    return SampledResponses(responses=responses, provenance=provenance)


# ---------------------------------------------------------------------------
# teacher_forced_logprob — GPU CALL-SITE B (delegates to the model)
# ---------------------------------------------------------------------------

def teacher_forced_logprob(
    model: "TargetModel",
    prompt: str,
    response: str,
    *,
    reduction: str = "sum",
) -> Any:
    """Teacher-forced log pi(response | prompt) under the frozen target.

    Thin dispatch to `model.teacher_forced_logprob(...)` (GPU CALL-SITE B): the
    real model returns a torch scalar carrying grad through the trigger tokens;
    the CPU stub returns a plain float. `reduction='sum'` == total log-prob (the
    REINFORCE default), `'mean'` == per-token (a length-normalized variant, a
    §15 stabilization knob). No forward pass happens in THIS module — it lives in
    the injected model (`HFTargetModel` below, or the test stub).
    """
    if reduction not in ("sum", "mean"):
        raise ValueError(f"reduction must be 'sum' or 'mean', got {reduction!r}")
    return model.teacher_forced_logprob(prompt, response, reduction=reduction)


# ---------------------------------------------------------------------------
# score_responses — inject a jailbreak_rewards reward (goal passed through)
# ---------------------------------------------------------------------------

def score_responses(
    goal: str,
    responses: Sequence[str],
    reward_fn: RewardFn,
) -> list[float]:
    """Behavioral reward for each response (D2.2: the ORIGINAL goal is passed in).

    `reward_fn(goal, response) -> float in [0,1]` is INJECTED (e.g. a
    `scripts/jailbreak_rewards.py` scorer bound to a frozen judge/StrongREJECT).
    Accepts a bare float or a `RewardOutput` (its `.reward` is used). Scoring a
    response WITHOUT its goal is forbidden — hence `goal` is a required argument.
    """
    if not str(goal).strip():
        raise ValueError("score_responses requires a non-empty ORIGINAL goal (D2.2).")
    return [_reward_value(reward_fn(goal, r)) for r in responses]


# ---------------------------------------------------------------------------
# reinforce_step — the assembled REINFORCE-MAC step
# ---------------------------------------------------------------------------

@dataclass
class ReinforceStepResult:
    """Everything one REINFORCE step produces + everything needed to audit it.

    responses / provenance / rewards : the K samples, their §D4.1 origin, rewards.
    estimate         : the pure-Python `ReinforceLossResult` (advantages, ce
                       weights, per-response CE, grad_wrt_logprob, the log dict).
    directions       : per-response 'towards' | 'away' | 'neutral' (sign of A_i);
                       'towards' == advantage>0 == CE-lowering pull.
    ce_weights_detached : the stop-gradient CE weights fed into the surrogate.
    surrogate_loss   : L = mean_i(sg(A_i)*CE_i). A torch scalar on GPU (call
                       `.backward()` at the GPU trigger-gradient call-site), else
                       a float equal to estimate.loss.
    selection_index / selection_reward / selection_response : the candidate the
                       BEHAVIORAL reward selects (max reward). REINFORCE-MAC uses
                       the surrogate GRADIENT for candidate PROPOSAL and this
                       behavioral reward for candidate SELECTION (§D4).
    log              : config + provenance record (enable_thinking, K, baseline…).
    """

    responses: list[str]
    provenance: list[str]
    rewards: list[float]
    estimate: ReinforceLossResult
    directions: list[str]
    ce_weights_detached: list[float]
    surrogate_loss: Any
    selection_index: int
    selection_reward: float
    selection_response: Optional[str]
    log: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "responses": self.responses,
            "provenance": self.provenance,
            "rewards": self.rewards,
            "directions": self.directions,
            "ce_weights_detached": self.ce_weights_detached,
            "surrogate_loss": _to_float(self.surrogate_loss),
            "selection_index": self.selection_index,
            "selection_reward": self.selection_reward,
            "selection_response": self.selection_response,
            **self.estimate.as_dict(),
            **{f"log_{k}": v for k, v in self.log.items()},
        }


def _direction(advantage: float, tol: float = 0.0) -> str:
    if advantage > tol:
        return "towards"
    if advantage < -tol:
        return "away"
    return "neutral"


def _select_by_reward(rewards: Sequence[float], per_response_ce: Sequence[float]) -> int:
    """Argmax reward; ties -> lower CE (better teacher-forced fit) -> lower index."""
    if not rewards:
        return -1
    order = sorted(
        range(len(rewards)),
        key=lambda i: (-float(rewards[i]), float(per_response_ce[i]), i),
    )
    return order[0]


def reinforce_step(
    model: "TargetModel",
    prompt: str,
    goal: str,
    reward_fn: RewardFn,
    *,
    K: int = 4,
    seeds: Optional[Sequence[int]] = None,
    seed_response: Optional[str] = None,
    best_historical: Optional[str] = None,
    temperature: float = 0.7,
    max_new_tokens: int = 2048,  # was 256 → truncated thinking models mid-<think> (Gate-3 artifact)
    baseline: str = "rloo",
    baseline_const: float = 0.0,
    clip_reward: Optional[tuple[float, float]] = None,
    normalize: str = "none",
    reduction: str = "sum",
    require_k2: bool = True,
    allow_k1_fallback: bool = False,
    enable_thinking: Optional[bool] = None,
    precomputed_responses: Optional[Sequence[str]] = None,
    precomputed_provenance: Optional[Sequence[str]] = None,
) -> ReinforceStepResult:
    """One REINFORCE-MAC step: sample -> reward -> advantage -> signed CE surrogate.

    Pipeline (call-sites marked): sample K responses (GPU A) -> behavioral reward
    per response (goal passed, injected judge) -> teacher-forced log-prob per
    response (GPU B) -> `reinforce_loss` (PURE PYTHON) -> stop-gradient CE weights
    -> differentiable surrogate whose trigger-token gradient is the GCGPlus Stage-1
    PROPOSAL signal; the behavioral reward drives Stage-2 SELECTION.

    K>=2 REQUIREMENT: RLOO's leave-one-out baseline needs K>=2. With K<2 this
    raises ValueError UNLESS `allow_k1_fallback=True`, in which case it falls back
    to the documented constant baseline (`reinforce_advantages` K=1 fallback:
    A_0 = r_0 - baseline_const) and records `k1_fallback=True` in the log. The
    'mean' baseline is likewise degenerate at K=1 and takes the same fallback.

    `precomputed_responses` lets the caller supply the K responses directly
    (e.g. a manually-controlled synthetic-reward smoke, Package-2 condition 0),
    bypassing GPU CALL-SITE A while still exercising the full estimator wiring.
    """
    if K < 2:
        if require_k2 and not allow_k1_fallback:
            raise ValueError(
                f"reinforce_step requires K>=2 for RLOO/mean baselines (got K={K}). "
                f"Pass allow_k1_fallback=True to use the documented constant-baseline "
                f"K=1 fallback (reinforce_advantages: A_0 = r_0 - baseline_const)."
            )

    # --- 1. Responses (GPU CALL-SITE A, or caller-supplied) ---
    if precomputed_responses is not None:
        responses = [str(r) for r in precomputed_responses]
        provenance = (
            list(precomputed_provenance)
            if precomputed_provenance is not None
            else ["precomputed"] * len(responses)
        )
    else:
        sampled = sample_responses(
            model, prompt, K, seeds=seeds, seed_response=seed_response,
            best_historical=best_historical, temperature=temperature,
            max_new_tokens=max_new_tokens,
        )
        responses, provenance = sampled.responses, sampled.provenance

    k_eff = len(responses)

    # --- 2. Behavioral reward per response (goal passed through; injected judge) ---
    rewards = score_responses(goal, responses, reward_fn)

    # --- 3. Teacher-forced log-probs (GPU CALL-SITE B) ---
    logprobs_raw = [
        teacher_forced_logprob(model, prompt, r, reduction=reduction) for r in responses
    ]
    logprob_values = [_to_float(lp) for lp in logprobs_raw]

    # --- 4. Pure-Python estimator (advantages + surrogate value + grads) ---
    k1_fallback = k_eff < 2
    est = reinforce_loss(
        logprob_values,
        rewards,
        baseline=baseline,
        baseline_const=baseline_const,
        clip_reward=clip_reward,
        normalize=normalize,
    )

    # --- 5. STOP-GRADIENT CE weights -> differentiable surrogate (trigger grad) ---
    ce_weights_detached = [stop_gradient(w) for w in est.ce_weights]
    surrogate_loss = build_surrogate_loss(logprobs_raw, ce_weights_detached)

    # --- 6. Direction labels + behavioral SELECTION ---
    directions = [_direction(a) for a in est.advantages]
    sel_idx = _select_by_reward(rewards, est.per_response_ce)
    sel_reward = float(rewards[sel_idx]) if sel_idx >= 0 else float("-inf")
    sel_resp = responses[sel_idx] if sel_idx >= 0 else None

    log = {
        "K_requested": K,
        "K_effective": k_eff,
        "k1_fallback": k1_fallback,
        "baseline": baseline,
        "reduction": reduction,
        "temperature": temperature,
        "enable_thinking": enable_thinking,
        "reinforce_mac": True,  # PROPOSAL = surrogate grad; SELECTION = behavioral reward
    }

    return ReinforceStepResult(
        responses=responses,
        provenance=provenance,
        rewards=rewards,
        estimate=est,
        directions=directions,
        ce_weights_detached=[float(w) for w in ce_weights_detached],
        surrogate_loss=surrogate_loss,
        selection_index=sel_idx,
        selection_reward=sel_reward,
        selection_response=sel_resp,
        log=log,
    )


# ===========================================================================
# GPU-ONLY: real target-model wrapper + Package-2 driver (guarded; not on CPU)
# ===========================================================================

def require_gpu() -> None:
    """Raise unless torch + a CUDA device are available (guards the GPU driver)."""
    import torch  # noqa: PLC0415  (lazy: importing this module must stay torch-free)

    if not torch.cuda.is_available():
        raise RuntimeError(
            "REINFORCE GPU runner requires CUDA (no GPU visible). "
            "This driver must run on an L40S node (see slurm_scripts/run_reinforce_smoke.slurm)."
        )


class HFTargetModel:  # pragma: no cover - GPU only, not exercised on CPU
    """Real `TargetModel` over a loaded HF model (GPU CALL-SITES A & B live here).

    Wraps a `poc_stage4.qwen3_model.Qwen3Model` (reused via `load_qwen3_model` /
    `load_gemma4_model` — NOT reimplemented). Constructed only inside the GPU
    driver; importing this module never loads a model.
    """

    def __init__(self, wrapped, model_family: str = "qwen3"):
        self.wrapped = wrapped              # Qwen3Model (tokenizer + model)
        self.model_family = model_family

    def generate_one(self, prompt, *, do_sample, temperature, seed, max_new_tokens):
        # GPU CALL-SITE A: one free generation from the frozen target.
        import torch  # noqa: PLC0415

        tok = self.wrapped.tokenizer
        mdl = self.wrapped.model
        if seed is not None:
            torch.manual_seed(int(seed))
        enc = tok(prompt, return_tensors="pt", add_special_tokens=False).to(mdl.device)
        gen_kwargs = dict(max_new_tokens=max_new_tokens, do_sample=bool(do_sample))
        if do_sample:
            gen_kwargs.update(temperature=float(temperature), top_p=0.95)
        with torch.no_grad():
            out = mdl.generate(**enc, **gen_kwargs)
        new_tokens = out[0][enc["input_ids"].shape[1]:]
        return tok.decode(new_tokens, skip_special_tokens=True)

    def teacher_forced_logprob(self, prompt, response, *, reduction="sum"):
        # GPU CALL-SITE B: differentiable teacher-forced log-prob over FIXED
        # sampled response tokens (grad flows through the trigger tokens in prompt).
        import torch  # noqa: PLC0415
        import torch.nn.functional as F  # noqa: PLC0415

        tok = self.wrapped.tokenizer
        mdl = self.wrapped.model
        prompt_ids = tok(prompt, return_tensors="pt", add_special_tokens=False).input_ids
        resp_ids = tok(response, return_tensors="pt", add_special_tokens=False).input_ids
        full = torch.cat([prompt_ids, resp_ids], dim=1).to(mdl.device)
        logits = mdl(full).logits  # [1, T, V]
        # Predict token t from position t-1; score only the response tokens.
        n_prompt = prompt_ids.shape[1]
        shift_logits = logits[:, n_prompt - 1 : -1, :]
        shift_labels = full[:, n_prompt:]
        logprobs = F.log_softmax(shift_logits, dim=-1)
        tok_lp = logprobs.gather(-1, shift_labels.unsqueeze(-1)).squeeze(-1)[0]
        # F4: guard an empty response (0 scored tokens). 'sum' is already 0; 'mean'
        # would be 0/0 = NaN — return a plain 0.0 instead so downstream stays finite.
        if tok_lp.numel() == 0:
            return 0.0
        total = tok_lp.sum()
        return total / tok_lp.numel() if reduction == "mean" else total

    # --- EmbeddingGradModel hooks (F2 trigger-gradient adapter; GPU CALL-SITE C) ---
    # These let `trigger_gradient.reinforce_trigger_gradient` build the DIFFERENTIABLE
    # one-hot @ embedding_matrix trigger construction on this frozen model.
    def embedding_matrix(self):
        # Effective embedding matrix [vocab, d] (mirror of TROPT base.py::embedding_matrix).
        from poc_stage_gcg_early.model_adapter import get_embedding_matrix  # noqa: PLC0415

        return get_embedding_matrix(self.wrapped.model, self.model_family)

    def forward_logits(self, inputs_embeds):
        # Differentiable forward over INPUT EMBEDDINGS (not ids): grad flows to the
        # trigger one-hot. `inputs_embeds` is [1, T, d]; returns logits [1, T, V].
        mdl = self.wrapped.model
        return mdl(inputs_embeds=inputs_embeds.to(mdl.device, mdl.dtype)).logits


def compute_reinforce_trigger_gradient(  # pragma: no cover - GPU only
    model: "HFTargetModel",
    instruction: str,
    trigger: str,
    responses: Sequence[str],
    rewards: Sequence[float],
    *,
    enable_thinking: bool,
    reduction: str = "sum",
    baseline: str = "rloo",
):
    """GPU CALL-SITE C — the real REINFORCE trigger gradient (F2 closed).

    Assembles the prefix/trigger/suffix token-id split for the templated prompt and
    the K response token-id lists, then delegates to the CPU-tested core
    `trigger_gradient.reinforce_trigger_gradient`. Returns its `TriggerGradientResult`
    whose `.grad` [trigger_len, vocab] is the GCGPlus Stage-1 PROPOSAL signal
    (top-k of `-grad` = candidate token swaps); behavioral reward still drives
    Stage-2 SELECTION (that is REINFORCE-MAC).

    TRIGGER-SPAN LOCATION (the one GPU-deferred detail): we render the templated
    prompt WITH the trigger and split token ids at the trigger's character span.
    The robust production path reuses the byte-verified trigger-slice locator from
    `poc_stage_gcg_early` (same machinery GCG uses); here we tokenize the three text
    pieces around the `{{OPTIMIZED_TRIGGER}}` placeholder, which is exact for the
    user-turn placement `f"{instruction} {trigger}"` (build_prompt).
    """
    tok = model.wrapped.tokenizer

    # Split the user content around the trigger and template each side's context.
    # build_prompt uses user_content = f"{instruction} {trigger}"; the trigger sits
    # at the end of the user turn, so prefix = template up to the trigger, suffix =
    # the turn delimiter / generation prompt after it.
    pre_text = _apply_chat_template(
        tok, f"{instruction} ", model.model_family, enable_thinking
    )
    full_text = _apply_chat_template(
        tok, f"{instruction} {trigger}", model.model_family, enable_thinking
    )
    # prefix = everything before the trigger; suffix = template tail after it.
    trig_start = full_text.find(trigger, len(instruction))
    prefix_text = full_text[:trig_start]
    suffix_text = full_text[trig_start + len(trigger):]

    def _ids(t: str) -> list[int]:
        return tok(t, add_special_tokens=False).input_ids

    prefix_ids = _ids(prefix_text)
    trigger_ids = _ids(trigger)
    suffix_ids = _ids(suffix_text)
    responses_ids = [_ids(r) for r in responses]

    from .trigger_gradient import reinforce_trigger_gradient  # noqa: PLC0415

    return reinforce_trigger_gradient(
        model, prefix_ids, trigger_ids, suffix_ids, responses_ids, rewards,
        reduction=reduction, baseline=baseline,
    )


def _synthetic_reward_fn(schedule: Sequence[float]) -> RewardFn:
    """Manually-controlled synthetic reward: response i -> schedule[i] (Package-2).

    Ignores the text; returns a FIXED reward per response index so the gradient
    SIGN is unambiguous (high schedule value => 'towards', low => 'away'). Purpose
    is estimator-correctness, NOT attack performance.
    """
    sched = [float(x) for x in schedule]

    def _fn(goal: str, response: str) -> float:  # goal accepted (D2.2), unused by design
        _fn.i = getattr(_fn, "i", 0)
        val = sched[_fn.i % len(sched)]
        _fn.i += 1
        return val

    return _fn


def _build_real_reward_fn(model_name: str) -> RewardFn:
    """Frozen StrongREJECT behavioral reward (Package-2 condition 1).

    Wraps `scripts/jailbreak_rewards.py::StrongRejectReward` around the SAME
    StrongREJECT judge used by Gate-1 evaluation —
    `poc_stage3.strongreject_scoring` (`load_strongreject_evaluate` +
    `score_single_row`, success == score>=0.5). Judge consistency is a HARD
    requirement (Sprint Plan §2.7: never mix judges): the behavioral reward and
    the Gate-1 eval must call the identical grader. Gate-1's call-site is
    `poc_stage_gcg_early/evaluate_optimized_suffixes.py:138-149`; this reuses it
    verbatim (same `evaluator`, same `score_single_row` shape, same 0.5 success
    convention downstream).

    The StrongREJECT rubric grader is a GPU/API call-site (needs a judge model /
    OpenAI API key). This function FAILS LOUDLY if the judge cannot be loaded or
    the API key is missing — it must NEVER silently fall back to a mock or return
    0 (that would fabricate a behavioral signal). Heavy imports are lazy so the
    module stays torch-free / importable on CPU.

    Returns a `RewardFn` == `(original_goal, response) -> strongreject_score in
    [0,1]` with the D2.3 reward-hacking controls applied by `StrongRejectReward`.
    D2.2: the ORIGINAL forbidden instruction (goal) is passed to the grader, never
    the adversarial/optimized prompt.
    """
    import os  # noqa: PLC0415

    from scripts.jailbreak_rewards import StrongRejectReward  # noqa: PLC0415

    # SAME judge as Gate-1 (§2.7). Rebind at call-time from the module so a test
    # can inject a STUB score_single_row / load_strongreject_evaluate.
    from poc_stage3 import strongreject_scoring as sr_mod  # noqa: PLC0415

    # Fail loudly BEFORE any scoring if the paid judge cannot run. StrongREJECT
    # rubric requires an OpenAI API key (same guard as poc_stage3.score_rows /
    # run_scoring_pipeline). Do NOT proceed with a missing key and return 0.
    if os.getenv("OPENAI_API_KEY") is None:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. The StrongREJECT behavioral reward reuses "
            "the SAME rubric judge as the Gate-1 eval (poc_stage3.strongreject_"
            "scoring) and requires a valid OpenAI API key. Refusing to run with a "
            "silent mock / zero reward."
        )

    # Load the StrongREJECT evaluator ONCE (raises RuntimeError if the local
    # checkout / evaluator is unavailable — see load_strongreject_evaluate).
    evaluate_callable = sr_mod.load_strongreject_evaluate()

    def _grade(forbidden_prompt: str, response: str) -> float:
        """(original_goal, response) -> strongreject_score in [0,1]; raise on error.

        Reuses Gate-1's exact call: score_single_row on {goal, target_response}
        with the shared evaluate_callable. Raises (never returns 0) when the judge
        errors, so a broken judge cannot masquerade as a low reward.
        """
        scored = sr_mod.score_single_row(
            {"goal": forbidden_prompt, "target_response": response},
            evaluate_callable=evaluate_callable,
        )
        status = scored.get("strongreject_status")
        if status == "skipped_empty_response":
            # Empty/whitespace response: legitimately not harmful (also vetoed by
            # the empty-output control). A real 0, not a judge error.
            return 0.0
        if status != "success":
            raise RuntimeError(
                "StrongREJECT grader failed to score a response "
                f"(status={status!r}, error_type="
                f"{scored.get('strongreject_error_type')!r}, message="
                f"{scored.get('strongreject_error_message')!r}). Refusing to "
                "return 0 for a judge error."
            )
        score = scored.get("strongreject_score")
        if score is None:
            raise RuntimeError(
                "StrongREJECT grader returned status 'success' but no score; "
                "refusing to fabricate a reward."
            )
        return float(score)

    reward = StrongRejectReward(strong_reject_fn=_grade)

    def _reward_fn(goal: str, response: str) -> float:
        # StrongRejectReward enforces D2.2 (original goal required) and applies
        # the D2.3 reward-hacking controls; return the final reward in [0,1].
        return reward.score(goal, response).reward

    return _reward_fn


def _main(argv: Optional[Sequence[str]] = None) -> int:  # pragma: no cover - GPU only
    """Package-2 REINFORCE gradient smoke (1 instruction, K=2, 5 steps).

    Condition 0 (synthetic): manually-controlled rewards -> verify gradient signs
      (high-reward response 'towards', low-reward 'away'), NO judge needed.
    Condition 1 (real):      one frozen-judge / StrongREJECT reward.
    Purpose: prove the estimator is correctly WIRED, not attack performance.

    Writes one JSONL line per step incrementally (resume-safe: appends, and skips
    steps already present in the output file).
    """
    import argparse
    import json
    from pathlib import Path

    p = argparse.ArgumentParser(description="Package-2 REINFORCE gradient smoke (GPU).")
    p.add_argument("--model-name", default="Qwen/Qwen3-14B")
    p.add_argument("--model-family", default="qwen3", choices=["qwen3", "gemma4"])
    p.add_argument("--instruction", required=True)
    p.add_argument("--trigger", default="! ! ! ! ! ! ! ! ! !")
    p.add_argument("--K", type=int, default=2)
    p.add_argument("--steps", type=int, default=5)
    p.add_argument("--reward", choices=["synthetic", "strong_reject"], default="synthetic")
    p.add_argument("--synthetic-rewards", default="1.0,0.0",
                   help="comma-separated per-response rewards for --reward synthetic")
    p.add_argument("--enable-thinking", action="store_true")
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--max-new-tokens", type=int, default=128)
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)

    require_gpu()

    # Reuse the existing loaders (NOT reimplemented).
    from poc_stage4.qwen3_model import load_gemma4_model, load_qwen3_model  # noqa: PLC0415

    loader = load_gemma4_model if args.model_family == "gemma4" else load_qwen3_model
    wrapped = loader(args.model_name, require_cuda=True, log_device_placement=True)
    model = HFTargetModel(wrapped, model_family=args.model_family)

    built = build_prompt(
        wrapped.tokenizer, args.instruction, args.trigger,
        enable_thinking=args.enable_thinking, model_family=args.model_family,
    )

    if args.reward == "synthetic":
        schedule = [float(x) for x in args.synthetic_rewards.split(",")]
        reward_fn = _synthetic_reward_fn(schedule)
    else:
        reward_fn = _build_real_reward_fn(args.model_name)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done_steps = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    try:
                        done_steps.add(int(json.loads(line)["step"]))
                    except Exception:
                        pass

    with open(out_path, "a", encoding="utf-8") as fh:
        for step in range(args.steps):
            if step in done_steps:
                print(f"[reinforce-smoke] step {step} already present — skipping")
                continue
            # Fresh reward index each step for the synthetic schedule.
            if args.reward == "synthetic":
                reward_fn = _synthetic_reward_fn(
                    [float(x) for x in args.synthetic_rewards.split(",")]
                )
            res = reinforce_step(
                model, built.text, args.instruction, reward_fn,
                K=args.K, temperature=args.temperature,
                max_new_tokens=args.max_new_tokens,
                enable_thinking=args.enable_thinking,
            )
            # GPU CALL-SITE C (F2 trigger gradient): the REAL discrete REINFORCE
            # trigger gradient consumed by GCGPlus Stage-1 proposal. This replaces
            # the old sign-only path — `res.surrogate_loss` alone carried no trigger
            # grad because teacher_forced_logprob was fed integer ids.
            tg = compute_reinforce_trigger_gradient(
                model, args.instruction, args.trigger, res.responses, res.rewards,
                enable_thinking=args.enable_thinking,
            )
            trigger_grad = tg.grad  # [trigger_len, vocab]; -topk = candidate swaps
            rec = {
                "step": step,
                "trigger_grad_shape": list(trigger_grad.shape),
                "trigger_grad_finite": bool(trigger_grad.isfinite().all().item()),
                "trigger_grad_advantages": tg.advantages,
                **res.as_dict(),
                **built.as_dict(),
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            print(
                f"[reinforce-smoke] step {step} rewards={res.rewards} "
                f"directions={res.directions} surrogate={_to_float(res.surrogate_loss):.6f}"
            )
    print(f"[reinforce-smoke] DONE -> {out_path}")
    return 0


__all__ = [
    "RewardFn",
    "TargetModel",
    "stop_gradient",
    "build_surrogate_loss",
    "BuiltPrompt",
    "build_prompt",
    "SampledResponses",
    "sample_responses",
    "teacher_forced_logprob",
    "score_responses",
    "ReinforceStepResult",
    "reinforce_step",
    "require_gpu",
    "HFTargetModel",
    "compute_reinforce_trigger_gradient",
]


if __name__ == "__main__":  # pragma: no cover - GPU only
    raise SystemExit(_main())
