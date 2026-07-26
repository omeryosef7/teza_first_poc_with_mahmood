"""Behavioral candidate RERANK runner (Package-1 Condition 3).

Consumes a candidate pool captured by `candidate_pool.py` and selects the best
trigger by a BEHAVIORAL reward computed over FREE GENERATIONS — the §15.4/§15.6
"free-generate from the top candidate subset, then select by reward" step. This
is the piece that unblocks Condition 3: the driver now yields a candidate POOL
(via the capturing optimizer), and this runner reranks it.

WHAT IS CPU-TESTABLE vs GPU-DEFERRED
------------------------------------
CPU-testable core (no torch, no model, unit-tested):
  * `parse_pool`            — JSONL pool -> unique candidates (min proxy_loss kept)
  * `select_by_precomputed_rewards` — pick the max-reward candidate, deterministic

GPU-deferred (call-sites MARKED, NOT run here):
  * `rerank_pool`           — free-generates from each top-N candidate and scores
    it with an injected `jailbreak_rewards` reward. Generation needs a loaded
    model; the StrongREJECT/judge reward needs a judge model + API key. Those are
    the GPU package's job; this module only wires them and does the (CPU)
    selection once rewards exist.

The reward is injected as `reward_fn(goal, response) -> float in [0,1]` (e.g.
`scripts/jailbreak_rewards.py::StrongRejectReward.score(...).reward` bound to a
frozen judge, per D2.2 which REQUIRES the original goal). Generation is injected
as `generate_fn(trigger_str) -> response_str`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

from .candidate_pool import (
    F_PROXY_LOSS,
    F_STEP,
    F_TRIGGER_STR,
    read_pool,
)

# A "big" loss sentinel for candidates that lack a recorded proxy_loss.
_INF = float("inf")


@dataclass
class RerankCandidate:
    """A unique candidate to rerank, aggregated across the captured pool."""

    trigger_str: str
    proxy_loss: float = _INF          # best (lowest) proxy_loss seen for this string
    first_step: int = -1              # earliest step it appeared at
    count: int = 0                    # how many pool rows referenced it


def parse_pool(
    path: Union[str, Path],
    max_candidates: Optional[int] = None,
) -> list[RerankCandidate]:
    """Parse a captured-pool JSONL into UNIQUE candidates, best proxy_loss kept.

    Dedupes by ``trigger_str`` (a candidate re-selected across steps counts once),
    keeping the lowest ``proxy_loss`` and earliest step. Returns candidates sorted
    ascending by ``proxy_loss`` (best proposals first); ``max_candidates`` caps the
    list AFTER sorting — the top-N subset the runner will free-generate from.
    """
    records = read_pool(path)
    return dedupe_records(records, max_candidates)


def dedupe_records(
    records: Sequence[dict],
    max_candidates: Optional[int] = None,
) -> list[RerankCandidate]:
    """Pure-Python dedupe of pool records -> sorted unique candidates."""
    by_str: dict[str, RerankCandidate] = {}
    for rec in records:
        s = str(rec[F_TRIGGER_STR])
        loss = float(rec.get(F_PROXY_LOSS, _INF))
        step = int(rec.get(F_STEP, -1))
        cur = by_str.get(s)
        if cur is None:
            by_str[s] = RerankCandidate(
                trigger_str=s, proxy_loss=loss, first_step=step, count=1
            )
        else:
            cur.count += 1
            if loss < cur.proxy_loss:
                cur.proxy_loss = loss
            if step >= 0 and (cur.first_step < 0 or step < cur.first_step):
                cur.first_step = step

    ordered = sorted(
        by_str.values(),
        key=lambda c: (c.proxy_loss, c.trigger_str),  # deterministic
    )
    if max_candidates is not None:
        ordered = ordered[: max(0, int(max_candidates))]
    return ordered


@dataclass
class RerankResult:
    """Outcome of a behavioral rerank."""

    best_trigger_str: Optional[str]
    best_reward: float
    best_proxy_loss: float
    n_candidates_scored: int
    ranking: list[dict] = field(default_factory=list)  # per-candidate, best-first


def select_by_precomputed_rewards(
    candidates: Sequence[RerankCandidate],
    rewards: Sequence[float],
) -> RerankResult:
    """Select the max-BEHAVIORAL-REWARD candidate (CPU-testable core).

    ``rewards[i]`` is the behavioral reward for ``candidates[i]``. Ties (equal
    reward) are broken deterministically by LOWER ``proxy_loss``, then by
    ``trigger_str`` — so the outcome never depends on dict/iteration order.
    Empty input -> a null result (no crash).
    """
    if len(candidates) != len(rewards):
        raise ValueError(
            f"candidates ({len(candidates)}) and rewards ({len(rewards)}) "
            f"must be the same length"
        )
    if not candidates:
        return RerankResult(
            best_trigger_str=None,
            best_reward=float("-inf"),
            best_proxy_loss=_INF,
            n_candidates_scored=0,
            ranking=[],
        )

    scored = [
        {
            "trigger_str": c.trigger_str,
            "reward": float(r),
            "proxy_loss": c.proxy_loss,
            "first_step": c.first_step,
        }
        for c, r in zip(candidates, rewards)
    ]
    # Best-first: max reward, then min proxy_loss, then lexicographic trigger_str.
    scored.sort(key=lambda d: (-d["reward"], d["proxy_loss"], d["trigger_str"]))
    best = scored[0]
    return RerankResult(
        best_trigger_str=best["trigger_str"],
        best_reward=best["reward"],
        best_proxy_loss=best["proxy_loss"],
        n_candidates_scored=len(scored),
        ranking=scored,
    )


def rerank_pool(
    pool_path: Union[str, Path],
    goal: str,
    reward_fn: Callable[[str, str], float],
    generate_fn: Callable[[str], str],
    max_candidates: int = 16,
) -> RerankResult:
    """Full rerank: parse pool -> free-generate top-N -> reward -> select best.

    ``goal`` is the ORIGINAL forbidden instruction (D2.2: the reward MUST see it).
    ``reward_fn(goal, response) -> float`` and ``generate_fn(trigger_str) ->
    response`` are INJECTED.

    GPU/model CALL-SITE (deferred, NOT run here): ``generate_fn`` loads/runs the
    target model and ``reward_fn`` runs a judge (+ possibly an API). Only call
    this from the GPU package with real callables. The parse + select steps are
    the CPU-testable core (see `select_by_precomputed_rewards`).
    """
    candidates = parse_pool(pool_path, max_candidates=max_candidates)
    rewards: list[float] = []
    for c in candidates:
        # GPU/model CALL-SITE (deferred): free generation from the candidate trigger.
        response = generate_fn(c.trigger_str)
        # JUDGE CALL-SITE (deferred): behavioral reward over the real generation.
        rewards.append(float(reward_fn(goal, response)))
    return select_by_precomputed_rewards(candidates, rewards)


__all__ = [
    "RerankCandidate",
    "RerankResult",
    "parse_pool",
    "dedupe_records",
    "select_by_precomputed_rewards",
    "rerank_pool",
]
