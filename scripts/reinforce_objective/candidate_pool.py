"""Candidate-pool CAPTURE for behavioral reranking (Package-1 Condition 3).

WHY THIS EXISTS
---------------
`scripts/phase3_tropt_optimize.py` records only `result.best_trigger_str` /
`result.best_loss`. TROPT's `GCGPlusOptimizer` evaluates a *pool* of candidate
triggers every step (Stage-2 evaluation, see
`TROPT/tropt/optimizer/gcgplus_optimizer.py:_evaluate_candidates`) but only the
single best survives into the `OptimizerResult`. With no candidate POOL there is
nothing to rerank behaviorally — that is the Condition-3 blocker
(docs/PACKAGE1_CLEARHARM_SMOKE_PLAN.md §"Condition 3 blocker").

NO CLEAN TROPT HOOK EXPOSES THE POOL
------------------------------------
Verified against `TROPT/tropt/optimizer/base.py` and `tropt/tracker/base.py`:
the optimizer calls `self.log(loss, trigger_str=...)` once per step, so a
`BaseTracker` only ever sees the per-step BEST — never `candidate_trigger_ids`
or the per-candidate `losses`. A tracker/callback therefore CANNOT capture the
pool without editing `TROPT/tropt/*` (forbidden by the hard rules).

The clean, zero-TROPT-edit path is a project-local THIN SUBCLASS of
`GCGPlusOptimizer` (`build_capturing_optimizer` below) that:
  * overrides `_evaluate_candidates` to stash the most-recently evaluated
    (candidate_ids, decoded strings, losses) batch, and
  * overrides `log` to flush that stash to JSONL after `super().log(...)`.
Because `log` is called at the END of each step (after the Stage-2 evaluation
and the best-update), the stash at flush time is exactly that step's Stage-2
candidate pool. No driver change to TROPT is needed; the only driver change is
to build the capturing optimizer instead of a bare `GCGPlusOptimizer` (a
one-line swap in the project-local D3 assembly — see `proxy_ce_rerank.py`).

JSONL SCHEMA (one JSON object per line)
---------------------------------------
    {
      "step":        int,    # optimization step; -1 = pre-loop initial-trigger log
      "rank":        int,    # 0 = lowest proxy_loss within this step's captured top-K
      "trigger_str": str,    # decoded candidate trigger string
      "proxy_loss":  float,  # the optimizer's per-candidate evaluation loss at capture
                             #   (the cheap Stage-2 loss used to RANK candidates; the
                             #    expensive behavioral rerank happens later in the runner)
      "trigger_ids": [int]|null,  # candidate token ids (null if not recorded)
      "n_pool":      int     # total candidates evaluated this step (before top-K truncation)
    }

The pure-Python pieces (`select_top_k`, `capture_pool_records`,
`CandidatePoolWriter`, `read_pool`, `group_by_step`) import and unit-test under
`/usr/bin/python3` with NO torch. The `build_capturing_optimizer` factory imports
TROPT/torch lazily and is a GPU-package concern (never run on CPU).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence, Union

PoolRecord = dict

# JSONL field names (single source of truth for the schema).
F_STEP = "step"
F_RANK = "rank"
F_TRIGGER_STR = "trigger_str"
F_PROXY_LOSS = "proxy_loss"
F_TRIGGER_IDS = "trigger_ids"
F_N_POOL = "n_pool"


# ---------------------------------------------------------------------------
# Pure-Python selection + serialization (no torch; unit-testable)
# ---------------------------------------------------------------------------

def select_top_k(
    candidate_strs: Sequence[str],
    proxy_losses: Sequence[float],
    top_k: Optional[int] = None,
    candidate_ids: Optional[Sequence[Sequence[int]]] = None,
) -> list[tuple[int, str, float, Optional[list[int]]]]:
    """Return the ``top_k`` lowest-loss candidates as ``(orig_idx, str, loss, ids)``.

    Sorted ascending by ``proxy_loss``; ties broken deterministically by the
    candidate's ORIGINAL index (stable), so equal-loss pools always serialize in
    the same order. ``top_k=None`` keeps the whole pool.
    """
    if len(candidate_strs) != len(proxy_losses):
        raise ValueError(
            f"candidate_strs ({len(candidate_strs)}) and proxy_losses "
            f"({len(proxy_losses)}) must be the same length"
        )
    if candidate_ids is not None and len(candidate_ids) != len(candidate_strs):
        raise ValueError("candidate_ids must align with candidate_strs")

    order = sorted(
        range(len(candidate_strs)),
        key=lambda i: (float(proxy_losses[i]), i),  # deterministic tie-break
    )
    if top_k is not None:
        order = order[: max(0, int(top_k))]

    out: list[tuple[int, str, float, Optional[list[int]]]] = []
    for idx in order:
        ids = list(candidate_ids[idx]) if candidate_ids is not None else None
        out.append((idx, str(candidate_strs[idx]), float(proxy_losses[idx]), ids))
    return out


def capture_pool_records(
    step: int,
    candidate_strs: Sequence[str],
    proxy_losses: Sequence[float],
    top_k: Optional[int] = None,
    candidate_ids: Optional[Sequence[Sequence[int]]] = None,
) -> list[PoolRecord]:
    """Build the JSONL records for one step's captured pool (schema in module doc)."""
    n_pool = len(candidate_strs)
    selected = select_top_k(candidate_strs, proxy_losses, top_k, candidate_ids)
    records: list[PoolRecord] = []
    for rank, (_orig_idx, s, loss, ids) in enumerate(selected):
        records.append(
            {
                F_STEP: int(step),
                F_RANK: rank,
                F_TRIGGER_STR: s,
                F_PROXY_LOSS: loss,
                F_TRIGGER_IDS: ids,
                F_N_POOL: n_pool,
            }
        )
    return records


@dataclass
class CandidatePoolWriter:
    """Append-only JSONL writer for captured candidate pools.

    ``top_k`` bounds how many candidates are kept per step (None = all).
    Opened lazily on first write so constructing it is side-effect free (handy
    in tests). Call :meth:`close` (or use as a context manager) when done.
    """

    path: Union[str, Path]
    top_k: Optional[int] = None

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self._fh = None

    def _ensure_open(self):
        if self._fh is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(self.path, "a", encoding="utf-8")
        return self._fh

    def write_step(
        self,
        step: int,
        candidate_strs: Sequence[str],
        proxy_losses: Sequence[float],
        candidate_ids: Optional[Sequence[Sequence[int]]] = None,
    ) -> int:
        """Serialize one step's top-K pool; returns the number of rows written."""
        records = capture_pool_records(
            step, candidate_strs, proxy_losses, self.top_k, candidate_ids
        )
        fh = self._ensure_open()
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        return len(records)

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def __enter__(self) -> "CandidatePoolWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def read_pool(path: Union[str, Path]) -> list[PoolRecord]:
    """Read a captured-pool JSONL into a list of records (skips blank lines)."""
    out: list[PoolRecord] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def group_by_step(records: Iterable[PoolRecord]) -> dict[int, list[PoolRecord]]:
    """Group pool records by their ``step``, each group sorted by ``rank``."""
    groups: dict[int, list[PoolRecord]] = {}
    for rec in records:
        groups.setdefault(int(rec[F_STEP]), []).append(rec)
    for step in groups:
        groups[step].sort(key=lambda r: r[F_RANK])
    return groups


# ---------------------------------------------------------------------------
# GPU-deferred: thin capturing subclass of GCGPlusOptimizer (lazy TROPT import)
# ---------------------------------------------------------------------------

def build_capturing_optimizer(
    writer: CandidatePoolWriter,
    **gcgplus_kwargs,
):
    """Construct a `GCGPlusOptimizer` that also captures its per-step pool to ``writer``.

    Thin PROJECT-LOCAL subclass — does NOT edit `TROPT/tropt/*`. All keyword
    args are forwarded verbatim to `GCGPlusOptimizer.__init__`.

    GPU/torch CALL-SITE: importing TROPT pulls in torch and constructing the
    optimizer needs a loaded `model`. Running `optimize_trigger` is GPU-only and
    is NOT invoked here.
    """
    # GPU/torch CALL-SITE (deferred): tropt import requires torch.
    from tropt.optimizer.gcgplus_optimizer import GCGPlusOptimizer  # noqa: PLC0415

    class _CandidatePoolCapturingOptimizer(GCGPlusOptimizer):
        """GCGPlus + per-step candidate-pool capture (Package-1 Condition 3)."""

        def __init__(self, *args, _pool_writer: CandidatePoolWriter, **kwargs):
            super().__init__(*args, **kwargs)
            self._pool_writer = _pool_writer
            self._pool_step = -1                # incremented per log() flush
            self._last_candidate_strs: list[str] = []
            self._last_losses: list[float] = []
            self._last_candidate_ids: Optional[list[list[int]]] = None

        def _evaluate_candidates(self, candidate_trigger_ids):  # type: ignore[override]
            losses = super()._evaluate_candidates(candidate_trigger_ids)
            # Stash the MOST-RECENT evaluated batch; log() (end of step) flushes it,
            # so at flush time this holds the Stage-2 candidate pool.
            try:
                self._last_candidate_strs = list(
                    self.proxy_model.tokenizer.decode_triggers(candidate_trigger_ids)
                )
                self._last_candidate_ids = [
                    [int(t) for t in row] for row in candidate_trigger_ids.tolist()
                ]
                self._last_losses = [float(x) for x in losses.tolist()]
            except Exception:  # pragma: no cover - never break optimization for capture
                self._last_candidate_strs, self._last_losses = [], []
                self._last_candidate_ids = None
            return losses

        def log(self, loss, trigger_str=None, **extra):  # type: ignore[override]
            super().log(loss, trigger_str=trigger_str, **extra)
            if self._last_candidate_strs:
                self._pool_writer.write_step(
                    step=self._pool_step,
                    candidate_strs=self._last_candidate_strs,
                    proxy_losses=self._last_losses,
                    candidate_ids=self._last_candidate_ids,
                )
            self._pool_step += 1

    return _CandidatePoolCapturingOptimizer(_pool_writer=writer, **gcgplus_kwargs)


__all__ = [
    "PoolRecord",
    "F_STEP",
    "F_RANK",
    "F_TRIGGER_STR",
    "F_PROXY_LOSS",
    "F_TRIGGER_IDS",
    "F_N_POOL",
    "select_top_k",
    "capture_pool_records",
    "CandidatePoolWriter",
    "read_pool",
    "group_by_step",
    "build_capturing_optimizer",
]
