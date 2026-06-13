"""
Stochastic RL environment for CoT hijacking structural wrapper selection.

Backed by real Qwen3-14B experimental data from Stage 4.7 and Stage 4.8.
Each step() randomly draws one observation from the empirical distribution
of the (goal_index, condition) cell, simulating a new seed run.

Cell pools:
  Stage 4.7: goals {0,1,2,3} x conditions {A,D,F,E}  → 3 obs per cell
  Stage 4.8: goals {0,2}     x conditions {A,D,F}    → 5 obs per cell (seeds 101-105)

L22 projections (layer 22 of Qwen3-14B, "provisional harmful-vs-harmless contrast direction")
are attached from Stage 4.7 projection_summary.jsonl. Stage 4.8 rows have l22=NaN (no
direction extraction run yet).
"""

from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent

_CANON_CSV = _REPO_ROOT / "outputs/stage4_7/runs/run_array_20260610_1442/analysis/canonical_per_run_results.csv"
_PROJ_JSONL = _REPO_ROOT / "outputs/stage4_7/runs/run_array_20260610_1442/projection_analysis/projection_summary.jsonl"
_STAGE48_JSONL = _REPO_ROOT / "outputs/stage4_8/runs/run_array_20260611_0109/run_summary.jsonl"
_ONSET_CSV = _REPO_ROOT / "outputs/meeting/mahmood_48h_update_20260611_143740/onset_proxy_dataset.csv"

ACTIONS = ["A", "D", "F", "E"]


@dataclass
class EpisodeObs:
    goal_idx: int
    condition: str
    sr_success: bool
    sr_score: float
    think_token_count: int
    is_censored: bool
    onset_percent: float        # fraction of think tokens before first target engagement; NaN if unknown
    l22_think_phase: float      # Layer-22 mean projection during think phase; NaN if unknown
    data_source: str            # 'stage4_7' or 'stage4_8'
    source_example_id: str = ""


def _safe_float(v, default=math.nan) -> float:
    try:
        f = float(v)
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


def _safe_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes")


def _load_stage47(
    canon_path: Path,
    proj_path: Path,
    onset_path: Path,
) -> list[EpisodeObs]:
    """Load Stage 4.7 data: canonical results + L22 projections + onset."""
    # Load projections keyed by run_id
    proj_by_run: dict[str, dict] = {}
    if proj_path.exists():
        for line in proj_path.read_text().splitlines():
            line = line.strip()
            if line:
                r = json.loads(line)
                proj_by_run[r["run_id"]] = r

    # Load onset keyed by (source_example_id, condition)
    onset_by_key: dict[tuple[str, str], float] = {}
    if onset_path.exists():
        reader = csv.DictReader(onset_path.open(encoding="utf-8"))
        for row in reader:
            if row.get("stage", "") in ("4.7", "stage4.7", ""):
                key = (row.get("source_example_id", ""), row.get("condition", ""))
                op = _safe_float(row.get("onset_percent", ""), math.nan)
                if not math.isnan(op):
                    onset_by_key[key] = op

    obs_list: list[EpisodeObs] = []
    if not canon_path.exists():
        return obs_list

    reader = csv.DictReader(canon_path.open(encoding="utf-8"))
    for row in reader:
        run_id = row.get("run_id", "")
        condition = row.get("condition", "")
        goal_idx = int(row.get("goal_index", 0))
        source_example_id = row.get("source_example_id", "")

        pr = proj_by_run.get(run_id, {})
        l22 = _safe_float(pr.get("layer22_think_phase_mean_projection", ""), math.nan)

        onset_key = (source_example_id, condition)
        onset_pct = onset_by_key.get(onset_key, math.nan)

        obs_list.append(EpisodeObs(
            goal_idx=goal_idx,
            condition=condition,
            sr_success=_safe_bool(row.get("sr_success", "False")),
            sr_score=_safe_float(row.get("strongreject_score", "0"), 0.0),
            think_token_count=int(_safe_float(row.get("think_token_count", "0"), 0)),
            is_censored=_safe_bool(row.get("is_censored", "False")),
            onset_percent=onset_pct,
            l22_think_phase=l22,
            data_source="stage4_7",
            source_example_id=source_example_id,
        ))
    return obs_list


def _load_stage48(jsonl_path: Path, onset_path: Path) -> list[EpisodeObs]:
    """Load Stage 4.8 data: run_summary (no L22 yet)."""
    onset_by_key: dict[tuple[str, str, str], float] = {}
    if onset_path.exists():
        reader = csv.DictReader(onset_path.open(encoding="utf-8"))
        for row in reader:
            if row.get("stage", "") in ("4.8", "stage4.8"):
                key = (
                    row.get("source_example_id", ""),
                    row.get("condition", ""),
                    str(row.get("seed", "")),
                )
                op = _safe_float(row.get("onset_percent", ""), math.nan)
                if not math.isnan(op):
                    onset_by_key[key] = op

    obs_list: list[EpisodeObs] = []
    if not jsonl_path.exists():
        return obs_list

    for line in jsonl_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        condition = r.get("condition", "")
        goal_idx = int(r.get("goal_index", 0))
        source_example_id = r.get("source_example_id", "")
        seed = str(r.get("seed", ""))

        onset_key = (source_example_id, condition, seed)
        onset_pct = onset_by_key.get(onset_key, math.nan)

        obs_list.append(EpisodeObs(
            goal_idx=goal_idx,
            condition=condition,
            sr_success=_safe_bool(r.get("sr_success", False)),
            sr_score=_safe_float(r.get("strongreject_score", 0), 0.0),
            think_token_count=int(_safe_float(r.get("think_token_count", 0), 0)),
            is_censored=_safe_bool(r.get("is_censored", False)),
            onset_percent=onset_pct,
            l22_think_phase=math.nan,
            data_source="stage4_8",
            source_example_id=source_example_id,
        ))
    return obs_list


class StochasticEnvironment:
    """
    Stochastic RL environment over experimental CoT hijacking data.

    The environment is a lookup table: for each (goal_idx, condition), we have a pool
    of real experimental observations. step() draws one uniformly at random, simulating
    a new seed run. This is stochastic because different seeds gave different sr_success
    values (e.g., a marginal cell might have 2 successes and 1 failure).

    This is offline RL with a stochastic empirical simulator — the rewards are real
    experimental results, not synthetic.
    """

    def __init__(
        self,
        canon_csv: Path = _CANON_CSV,
        proj_jsonl: Path = _PROJ_JSONL,
        stage48_jsonl: Path = _STAGE48_JSONL,
        onset_csv: Path = _ONSET_CSV,
        rng_seed: int = 0,
    ):
        self._rng = random.Random(rng_seed)
        self._cells: dict[tuple[int, str], list[EpisodeObs]] = {}

        all_obs = _load_stage47(canon_csv, proj_jsonl, onset_csv)
        all_obs += _load_stage48(stage48_jsonl, onset_csv)

        for obs in all_obs:
            key = (obs.goal_idx, obs.condition)
            self._cells.setdefault(key, []).append(obs)

    @property
    def available_goals(self) -> list[int]:
        return sorted({k[0] for k in self._cells})

    @property
    def available_conditions(self) -> list[str]:
        return sorted({k[1] for k in self._cells})

    def cell_size(self, goal_idx: int, condition: str) -> int:
        return len(self._cells.get((goal_idx, condition), []))

    def cell_asr(self, goal_idx: int, condition: str) -> float:
        pool = self._cells.get((goal_idx, condition), [])
        if not pool:
            return math.nan
        return sum(o.sr_success for o in pool) / len(pool)

    def step(self, goal_idx: int, condition: str) -> Optional[EpisodeObs]:
        """Draw one observation from the empirical distribution of this cell."""
        pool = self._cells.get((goal_idx, condition))
        if not pool:
            return None
        return self._rng.choice(pool)

    def summary(self) -> dict:
        out = {}
        for (g, c), pool in sorted(self._cells.items()):
            asr = sum(o.sr_success for o in pool) / len(pool)
            l22s = [o.l22_think_phase for o in pool if not math.isnan(o.l22_think_phase)]
            out[f"goal{g}_{c}"] = {
                "n": len(pool),
                "asr": round(asr, 3),
                "mean_l22": round(sum(l22s) / len(l22s), 3) if l22s else None,
            }
        return out
