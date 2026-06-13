"""
REINFORCE policy for structural wrapper selection.

Policy: softmax over {A, D, F, E} per goal_index.
Parameters: theta[n_goals, n_actions]  (log-preference; initialized to 0 = uniform)
Update:    REINFORCE gradient with exponential moving average baseline per goal.

This is genuine policy gradient RL. The update rule is:
    advantage = reward - baseline[goal]
    baseline[goal] = 0.9 * baseline[goal] + 0.1 * reward
    grad_log_pi[action] = 1 - pi[action]   (for chosen action)
    grad_log_pi[other]  = -pi[other]        (for unchosen actions)
    theta[goal] += lr * advantage * grad_log_pi

The log-softmax parameterisation ensures the policy is always a valid distribution.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

from poc_rl_loop.rl_environment import ACTIONS

N_ACTIONS = len(ACTIONS)
ACTION_TO_IDX = {a: i for i, a in enumerate(ACTIONS)}
IDX_TO_ACTION = {i: a for i, a in enumerate(ACTIONS)}


def _softmax(logits: list[float]) -> list[float]:
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    s = sum(exps)
    return [e / s for e in exps]


@dataclass
class PolicyStep:
    goal_idx: int
    action_idx: int
    condition: str
    probs: list[float]          # P(A), P(D), P(F), P(E)
    log_prob: float


class REINFORCEPolicy:
    """
    Per-goal softmax policy trained with REINFORCE.

    n_goals: number of distinct goal_index values in the data (typically 4).
    lr:      learning rate for parameter updates.
    ema:     exponential moving average coefficient for baseline (0.9 = slow baseline update).
    """

    def __init__(self, n_goals: int = 4, lr: float = 0.05, ema: float = 0.9, rng_seed: int = 0):
        self.n_goals = n_goals
        self.lr = lr
        self.ema = ema
        self._rng = random.Random(rng_seed)

        self.theta: list[list[float]] = [[0.0] * N_ACTIONS for _ in range(n_goals)]
        self.baseline: list[float] = [0.0] * n_goals
        self.n_updates: list[int] = [0] * n_goals

    def sample(self, goal_idx: int) -> PolicyStep:
        """Sample an action for this goal from the current policy."""
        logits = self.theta[goal_idx]
        probs = _softmax(logits)
        # Weighted random sample
        r = self._rng.random()
        cumulative = 0.0
        action_idx = N_ACTIONS - 1
        for i, p in enumerate(probs):
            cumulative += p
            if r < cumulative:
                action_idx = i
                break
        condition = IDX_TO_ACTION[action_idx]
        log_prob = math.log(max(probs[action_idx], 1e-12))
        return PolicyStep(
            goal_idx=goal_idx,
            action_idx=action_idx,
            condition=condition,
            probs=probs,
            log_prob=log_prob,
        )

    def update(self, goal_idx: int, action_idx: int, reward: float) -> dict:
        """REINFORCE gradient update. Returns diagnostic info."""
        probs = _softmax(self.theta[goal_idx])

        advantage = reward - self.baseline[goal_idx]
        self.baseline[goal_idx] = self.ema * self.baseline[goal_idx] + (1 - self.ema) * reward

        # Score function gradient: d/dtheta log pi(a|s) = e_a - probs
        for i in range(N_ACTIONS):
            indicator = 1.0 if i == action_idx else 0.0
            grad = indicator - probs[i]
            self.theta[goal_idx][i] += self.lr * advantage * grad

        self.n_updates[goal_idx] += 1
        return {
            "advantage": round(advantage, 4),
            "baseline": round(self.baseline[goal_idx], 4),
            "delta_theta_norm": round(
                math.sqrt(sum((self.lr * advantage * (int(i == action_idx) - p)) ** 2
                              for i, p in enumerate(probs))), 6
            ),
        }

    def get_probs(self, goal_idx: int) -> dict[str, float]:
        """Current action probabilities for a goal."""
        probs = _softmax(self.theta[goal_idx])
        return {IDX_TO_ACTION[i]: round(p, 4) for i, p in enumerate(probs)}

    def get_probs_table(self) -> list[dict]:
        rows = []
        for g in range(self.n_goals):
            probs = _softmax(self.theta[g])
            row = {"goal_idx": g, "n_updates": self.n_updates[g], "baseline": round(self.baseline[g], 4)}
            for i, a in enumerate(ACTIONS):
                row[f"prob_{a}"] = round(probs[i], 4)
            rows.append(row)
        return rows

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({
            "n_goals": self.n_goals,
            "lr": self.lr,
            "ema": self.ema,
            "theta": self.theta,
            "baseline": self.baseline,
            "n_updates": self.n_updates,
        }, indent=2))

    @classmethod
    def load(cls, path: Path) -> "REINFORCEPolicy":
        d = json.loads(path.read_text())
        p = cls(n_goals=d["n_goals"], lr=d["lr"], ema=d["ema"])
        p.theta = d["theta"]
        p.baseline = d["baseline"]
        p.n_updates = d["n_updates"]
        return p
