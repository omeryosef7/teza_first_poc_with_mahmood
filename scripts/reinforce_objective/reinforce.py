"""
D4 — REINFORCE-style behavioral objective estimator (PURE PYTHON, model-agnostic).

Sprint Completion Plan §D4 / original plan §15 ("Distributional and
Reinforcement-Style Optimization", §15.5 "Policy-gradient-style update").

WHAT THIS IS
------------
The estimator math for a policy-gradient (REINFORCE) update over *sampled free
generations*, expressed entirely in pure Python (lists + `math`) so it runs
under `/usr/bin/python3 -m pytest` where torch/numpy are NOT installed. Every
operation here is elementwise and equally valid on torch tensors / numpy arrays
(pass `.tolist()`); the module deliberately takes no tensor dependency so the
core policy-gradient math is unit-testable on toy numbers.

WHAT THIS IS *NOT*
------------------
This module does NOT sample, does NOT run a model, and does NOT backprop through
sampling. It converts *already-obtained* per-response rewards and per-response
teacher-forced log-probs into (a) advantages, (b) per-response CE weights, and
(c) a scalar surrogate loss whose gradient w.r.t. the response log-probs equals
the REINFORCE gradient. The forward/backward that produces `response_logprobs`
needs a real model and is a GPU-package concern — see `ReinforceGCGAdapter`.

THE MATH (why the signs are what they are)
------------------------------------------
REINFORCE maximizes E_{y~pi}[R(y)].  Its gradient estimate from K sampled
responses y_1..y_K with rewards r_1..r_K and a baseline b is:

    grad(J) ~= (1/K) * sum_i  A_i * grad(log pi(y_i)),   A_i = r_i - b_i

TROPT *minimizes* a loss.  A teacher-forced cross-entropy of response y_i is
    CE_i = -log pi(y_i)                       (per-response, teacher forced)
so  log pi(y_i) = -CE_i.  Define the surrogate loss (to MINIMIZE):

    L = (1/K) * sum_i  A_i * CE_i             ( = -(1/K) sum_i A_i log pi(y_i) )

Minimizing L moves each CE_i in the direction  -sign(A_i):
  * A_i > 0  (reward ABOVE baseline)  -> weight > 0 -> minimizing L LOWERS CE_i
    -> pushes the model TOWARDS y_i  ("towards" / CE-lowering).
  * A_i < 0  (reward BELOW baseline)  -> weight < 0 -> minimizing L RAISES CE_i
    -> pushes the model AWAY from y_i ("away").
Hence the per-response CE weight is exactly the advantage A_i
(`signed_teacher_forced_ce_grad_weight`), and dL/d(CE_i) = A_i / K,
dL/d(log pi(y_i)) = -A_i / K.  We do NOT differentiate A_i (stop-gradient on the
reward/baseline), matching REINFORCE (no backprop through sampling).

STABILIZATION KNOBS (all configurable + logged, §15.2/§15.3 variance control)
-----------------------------------------------------------------------------
  * reward clipping        -> `clip_reward=(lo, hi)`
  * reward normalization   -> `normalize='none'|'center'|'zscore'`
  * RLOO vs mean baseline  -> `baseline='rloo'|'mean'`
  * small constant baseline-> `baseline_const` (used for K=1 fallback and added)
Every applied transform is recorded in the returned log dict so a run is fully
reproducible/auditable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence


# ---------------------------------------------------------------------------
# Baselines & advantages (D4: RLOO leave-one-out)
# ---------------------------------------------------------------------------

def reinforce_advantages(
    rewards: Sequence[float],
    baseline: str = "rloo",
    baseline_const: float = 0.0,
) -> list[float]:
    """Per-response advantages A_i = r_i - b_i (§15.5).

    baseline:
      * 'rloo' — RLOO leave-one-out (Ahmadian et al. 2024): for K>1,
            b_i = mean_{j != i} r_j = (S - r_i) / (K - 1),  A_i = r_i - b_i.
        This is the recommended low-variance, UNBIASED baseline and makes the
        advantages sum to ~0 exactly (see `assert_zero_sum`).
      * 'mean' — shared baseline b = mean(r); A_i = r_i - mean(r). Also sums ~0.

    K == 1 FALLBACK: RLOO/mean are undefined (no "other" samples / zero variance).
    We fall back to a constant baseline:  A_0 = r_0 - baseline_const. The
    zero-sum property does NOT hold for K == 1 and must not be asserted there.

    `baseline_const` is additionally subtracted from every advantage (a small
    constant baseline is variance-reducing and bias-free because it is constant
    across i).
    """
    r = [float(x) for x in rewards]
    k = len(r)
    if k == 0:
        return []
    if k == 1:
        # Documented K=1 fallback: no leave-one-out possible.
        return [r[0] - baseline_const]

    if baseline == "rloo":
        s = sum(r)
        adv = [(ri - (s - ri) / (k - 1)) for ri in r]
    elif baseline == "mean":
        mean = sum(r) / k
        adv = [ri - mean for ri in r]
    else:
        raise ValueError(f"unknown baseline {baseline!r}; use 'rloo' or 'mean'")

    if baseline_const != 0.0:
        adv = [a - baseline_const for a in adv]
    return adv


def assert_zero_sum(advantages: Sequence[float], tol: float = 1e-9) -> None:
    """Assert sum(advantages) ~= 0 (holds for RLOO/mean with K>1, baseline_const=0)."""
    total = math.fsum(advantages)
    assert abs(total) <= tol, f"advantages not zero-sum: sum={total} (tol={tol})"


# ---------------------------------------------------------------------------
# Signed teacher-forced CE weight (D4: towards / away)
# ---------------------------------------------------------------------------

def signed_teacher_forced_ce_grad_weight(advantage: float) -> float:
    """Weight applied to a response's teacher-forced CE in the surrogate loss.

    Returns the advantage itself. In the loss  L = mean_i(weight_i * CE_i):
      * advantage > 0  -> weight > 0 -> minimizing L LOWERS that CE  ("towards"),
      * advantage < 0  -> weight < 0 -> minimizing L RAISES that CE  ("away"),
      * advantage == 0 -> no contribution.
    Monotonically increasing in the advantage (higher reward-vs-baseline =>
    stronger "towards" pull). The advantage is a STOP-GRADIENT scalar: we never
    backprop through it (no backprop through sampling / the reward).
    """
    return float(advantage)


# ---------------------------------------------------------------------------
# Reward stabilization transforms (§15 variance control; all logged)
# ---------------------------------------------------------------------------

def _transform_rewards(
    rewards: Sequence[float],
    clip_reward: Optional[tuple[float, float]],
    normalize: str,
) -> tuple[list[float], dict]:
    r = [float(x) for x in rewards]
    log: dict = {"n": len(r), "raw_mean": (sum(r) / len(r)) if r else 0.0}

    if clip_reward is not None:
        lo, hi = clip_reward
        if lo > hi:
            raise ValueError(f"clip_reward lo>hi: {clip_reward}")
        r = [min(max(x, lo), hi) for x in r]
        log["clip_reward"] = (lo, hi)

    if normalize == "none":
        pass
    elif normalize == "center":
        m = (sum(r) / len(r)) if r else 0.0
        r = [x - m for x in r]
        log["normalize"] = "center"
        log["center_mean"] = m
    elif normalize == "zscore":
        n = len(r)
        m = (sum(r) / n) if n else 0.0
        var = (sum((x - m) ** 2 for x in r) / n) if n else 0.0
        std = math.sqrt(var)
        # Guard zero variance (e.g. all-equal rewards) to avoid div-by-zero.
        denom = std if std > 1e-8 else 1.0
        r = [(x - m) / denom for x in r]
        log["normalize"] = "zscore"
        log["zscore_mean"] = m
        log["zscore_std"] = std
        log["zscore_std_guarded"] = std <= 1e-8
    else:
        raise ValueError(f"unknown normalize {normalize!r}")

    return r, log


# ---------------------------------------------------------------------------
# REINFORCE surrogate loss (D4)
# ---------------------------------------------------------------------------

@dataclass
class ReinforceLossResult:
    """Result of `reinforce_loss` — the scalar surrogate plus everything needed
    to audit it and to wire a real backward pass.

    loss: scalar surrogate  L = mean_i(A_i * CE_i)  (to MINIMIZE).
    advantages: A_i (stop-gradient).
    ce_weights: per-response CE weights (== advantages; from
        `signed_teacher_forced_ce_grad_weight`).
    per_response_ce: CE_i = -logprob_i used.
    grad_wrt_logprob: dL/d(log pi(y_i)) = -A_i / K  (the REINFORCE gradient the
        real backward pass must reproduce; finite whenever advantages are).
    grad_wrt_ce: dL/d(CE_i) = A_i / K.
    log: applied-transform + config record (reproducibility).
    """

    loss: float
    advantages: list[float]
    ce_weights: list[float]
    per_response_ce: list[float]
    grad_wrt_logprob: list[float]
    grad_wrt_ce: list[float]
    log: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "loss": self.loss,
            "advantages": self.advantages,
            "ce_weights": self.ce_weights,
            "per_response_ce": self.per_response_ce,
            "grad_wrt_logprob": self.grad_wrt_logprob,
            "grad_wrt_ce": self.grad_wrt_ce,
            **{f"log_{k}": v for k, v in self.log.items()},
        }


def reinforce_loss(
    response_logprobs: Sequence[float],
    rewards: Sequence[float],
    baseline: str = "rloo",
    baseline_const: float = 0.0,
    clip_reward: Optional[tuple[float, float]] = None,
    normalize: str = "none",
) -> ReinforceLossResult:
    """Signed, advantage-weighted combination of per-response teacher-forced CEs.

    Args:
      response_logprobs: per-response teacher-forced TOTAL (or mean) log pi(y_i).
        CE_i is defined as -logprob_i. These come from a real model forward pass
        (GPU-deferred); here they are plain floats.
      rewards: per-response behavioral reward r_i (e.g. from
        `scripts/jailbreak_rewards.py`), one per sampled response.
      baseline / baseline_const: see `reinforce_advantages`.
      clip_reward / normalize: stabilization knobs (logged).

    Returns a `ReinforceLossResult`.  L = mean_i(A_i * CE_i) with A_i a
    stop-gradient advantage; minimizing L pulls TOWARDS above-baseline responses
    and AWAY from below-baseline ones.
    """
    if len(response_logprobs) != len(rewards):
        raise ValueError(
            f"length mismatch: {len(response_logprobs)} logprobs vs {len(rewards)} rewards"
        )
    k = len(rewards)
    if k == 0:
        return ReinforceLossResult(0.0, [], [], [], [], [], {"n": 0})

    proc_rewards, log = _transform_rewards(rewards, clip_reward, normalize)
    log.update({"baseline": baseline, "baseline_const": baseline_const, "K": k})

    advantages = reinforce_advantages(
        proc_rewards, baseline=baseline, baseline_const=baseline_const
    )
    ce_weights = [signed_teacher_forced_ce_grad_weight(a) for a in advantages]
    per_response_ce = [-float(lp) for lp in response_logprobs]

    loss = math.fsum(w * ce for w, ce in zip(ce_weights, per_response_ce)) / k
    grad_wrt_ce = [w / k for w in ce_weights]           # dL/dCE_i  = A_i / K
    grad_wrt_logprob = [-w / k for w in ce_weights]     # dL/dlogp_i = -A_i / K

    return ReinforceLossResult(
        loss=loss,
        advantages=advantages,
        ce_weights=ce_weights,
        per_response_ce=per_response_ce,
        grad_wrt_logprob=grad_wrt_logprob,
        grad_wrt_ce=grad_wrt_ce,
        log=log,
    )


# ---------------------------------------------------------------------------
# D4 adapter — how this plugs into TROPT GCGPlus (interface + docstring only)
# ---------------------------------------------------------------------------

@dataclass
class ReinforceGCGAdapter:
    """Interface describing how the D4 estimator drives TROPT `GCGPlusOptimizer`.

    THIS CLASS RUNS NO MODEL. It documents the two GCGPlus call-sites a GPU
    package must fill (both marked below), and exposes the pure-Python estimator
    (`reinforce_loss`) that turns their outputs into a loss + gradient weights.

    GCGPlus two-stage design (see TROPT/tropt/optimizer/gcgplus_optimizer.py):
      Stage 1 (proposal, on proxy): gradient-ranked candidate token flips from a
        DIFFERENTIABLE `proxy_loss`.  For REINFORCE the differentiable proxy is
        the advantage-weighted teacher-forced CE: the per-response CE weights are
        the advantages (`ce_weights`), so the proxy gradient of
        sum_i A_i * CE_i(trigger) w.r.t. the trigger embeddings is exactly the
        REINFORCE gradient — computed with the SAME machinery GCGPlus already
        uses for PrefillCELoss, only with per-response weights A_i applied.
      Stage 2 (selection, on target): each surviving candidate is scored by the
        NEGATIVE expected behavioral reward over its own free generations
        (lower loss = higher reward), i.e. the black-box behavioral scorer.

    Per-step protocol (K samples per candidate):
      1.  # GPU CALL-SITE A (sampling): responses = model.generate(prompt+trigger,
          num_return_sequences=K, do_sample=True, temperature=...).  Sampling is
          NON-differentiable and we never backprop through it.
      2.  rewards = [reward_fn(goal, resp) for resp in responses]   # jailbreak_rewards
      3.  # GPU CALL-SITE B (teacher-forced pass): logprobs =
          model.teacher_forced_logprob(prompt+trigger, resp) for each resp
          (a differentiable forward pass over FIXED sampled tokens).
      4.  res = reinforce_loss(logprobs, rewards, **stab_knobs)   # PURE PYTHON (here)
      5.  proxy gradient = backward of sum_i res.ce_weights[i] * CE_i  (uses
          res.grad_wrt_logprob at call-site B's graph).  # GPU (autograd)

    Realizing this inside TROPT WITHOUT editing upstream (per hard rules) means a
    project-local `BaseLoss` subclass whose value is the advantage-weighted CE
    and whose `require_generation=True`; it would be passed as GCGPlus
    `proxy_loss` (differentiable) with a behavioral selection `loss`. Building
    that loss requires the model wrappers and is GPU-deferred; this adapter fixes
    the interface so the GPU package is a fill-in-the-blanks job.
    """

    K: int = 4
    temperature: float = 1.0
    baseline: str = "rloo"
    baseline_const: float = 0.0
    clip_reward: Optional[tuple[float, float]] = None
    normalize: str = "none"

    def estimate(
        self,
        response_logprobs: Sequence[float],
        rewards: Sequence[float],
    ) -> ReinforceLossResult:
        """Pure-Python estimator step (call-sites A & B must already have run)."""
        return reinforce_loss(
            response_logprobs,
            rewards,
            baseline=self.baseline,
            baseline_const=self.baseline_const,
            clip_reward=self.clip_reward,
            normalize=self.normalize,
        )

    def sample_responses(self, *args, **kwargs):  # pragma: no cover - GPU only
        raise NotImplementedError(
            "GPU CALL-SITE A: model.generate(..., num_return_sequences=K). "
            "Requires a real model; not runnable in the CPU/toy package."
        )

    def teacher_forced_logprobs(self, *args, **kwargs):  # pragma: no cover - GPU only
        raise NotImplementedError(
            "GPU CALL-SITE B: teacher-forced forward pass over sampled tokens. "
            "Requires a real model; not runnable in the CPU/toy package."
        )


__all__ = [
    "reinforce_advantages",
    "assert_zero_sum",
    "signed_teacher_forced_ce_grad_weight",
    "reinforce_loss",
    "ReinforceLossResult",
    "ReinforceGCGAdapter",
]
