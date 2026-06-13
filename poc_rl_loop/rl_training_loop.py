"""
Online REINFORCE training loop for structural wrapper selection.

Each episode:
  1. Sample a goal_index uniformly from available goals.
  2. Policy samples a condition action.
  3. Environment draws one observation from the empirical cell.
  4. Reward function computes reward from the observation.
  5. Policy updates via REINFORCE gradient.
  6. Log everything to trace.

This is online RL: policy updates happen after *every* episode,
not in batches. The policy starts at uniform and converges over N_EPISODES.
"""

from __future__ import annotations

import csv
import json
import math
import random
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from poc_rl_loop.rl_environment import ACTIONS, StochasticEnvironment
from poc_rl_loop.rl_policy import REINFORCEPolicy
from poc_rl_loop.rl_reward_function import ResearchRewardFunction, RewardVariant

CHECKPOINT_EVERY = 50


def run_rl_experiment(
    variant: RewardVariant,
    n_episodes: int,
    lr: float,
    ema: float,
    rng_seed: int,
    out_dir: Path,
    env: StochasticEnvironment,
    reward_fn: ResearchRewardFunction,
    verbose: bool = True,
) -> list[dict]:
    """
    Run a single REINFORCE experiment for one reward variant.

    Returns list of episode records (also written to out_dir/rl_policy_trace.jsonl).
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    goals = env.available_goals
    n_goals = max(goals) + 1 if goals else 4
    policy = REINFORCEPolicy(n_goals=n_goals, lr=lr, ema=ema, rng_seed=rng_seed)
    goal_rng = random.Random(rng_seed + 100)

    trace: list[dict] = []
    cumulative_reward = 0.0
    t0 = time.time()

    trace_path = out_dir / "rl_policy_trace.jsonl"
    selection_path = out_dir / "rl_condition_selection_history.csv"

    with trace_path.open("w") as trace_f, selection_path.open("w", newline="") as sel_f:
        sel_writer = csv.DictWriter(
            sel_f,
            fieldnames=["step", "goal_idx", "condition", "sr_success", "reward_total",
                        "prob_A", "prob_D", "prob_F", "prob_E",
                        "advantage", "baseline", "l22_think_phase",
                        "data_source", "variant"],
        )
        sel_writer.writeheader()

        for step in range(1, n_episodes + 1):
            goal_idx = goal_rng.choice(goals)

            policy_step = policy.sample(goal_idx)
            condition = policy_step.condition

            obs = env.step(goal_idx, condition)
            if obs is None:
                if verbose:
                    print(f"  [step {step}] No data for goal={goal_idx} cond={condition}, skipping")
                continue

            reward_components = reward_fn.compute(obs, variant)
            update_info = policy.update(goal_idx, policy_step.action_idx, reward_components.total)

            cumulative_reward += reward_components.total
            probs = policy.get_probs(goal_idx)

            record = {
                "step": step,
                "goal_idx": goal_idx,
                "action_idx": policy_step.action_idx,
                "condition": condition,
                "variant": variant.value,
                "sr_success": obs.sr_success,
                "sr_score": obs.sr_score,
                "think_token_count": obs.think_token_count,
                "is_censored": obs.is_censored,
                "onset_percent": None if math.isnan(obs.onset_percent) else obs.onset_percent,
                "l22_think_phase": None if math.isnan(obs.l22_think_phase) else obs.l22_think_phase,
                "data_source": obs.data_source,
                "prob_A": probs["A"],
                "prob_D": probs["D"],
                "prob_F": probs["F"],
                "prob_E": probs["E"],
                "reward_primary": reward_components.primary,
                "reward_onset_bonus": reward_components.onset_bonus,
                "reward_censoring_penalty": reward_components.censoring_penalty,
                "reward_l22_secondary": reward_components.l22_secondary,
                "reward_total": reward_components.total,
                "advantage": update_info["advantage"],
                "baseline": update_info["baseline"],
                "cumulative_reward": cumulative_reward,
                "mean_reward_so_far": cumulative_reward / step,
            }
            trace.append(record)
            trace_f.write(json.dumps(record) + "\n")

            sel_writer.writerow({
                "step": step,
                "goal_idx": goal_idx,
                "condition": condition,
                "sr_success": obs.sr_success,
                "reward_total": round(reward_components.total, 4),
                "prob_A": probs["A"],
                "prob_D": probs["D"],
                "prob_F": probs["F"],
                "prob_E": probs["E"],
                "advantage": update_info["advantage"],
                "baseline": update_info["baseline"],
                "l22_think_phase": None if math.isnan(obs.l22_think_phase) else round(obs.l22_think_phase, 3),
                "data_source": obs.data_source,
                "variant": variant.value,
            })

            if step % CHECKPOINT_EVERY == 0:
                policy.save(out_dir / f"policy_checkpoint_step{step}.json")
                if verbose:
                    mean_r = cumulative_reward / step
                    probs_all = policy.get_probs(goals[0])
                    print(f"  [step {step:4d}/{n_episodes}] mean_reward={mean_r:.3f}  "
                          f"P(A)={probs_all['A']:.3f} P(D)={probs_all['D']:.3f} "
                          f"P(F)={probs_all['F']:.3f} P(E)={probs_all['E']:.3f}")

    policy.save(out_dir / "policy_final.json")

    # Final policy probs table
    probs_table_path = out_dir / "policy_final_probs.csv"
    with probs_table_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["goal_idx", "n_updates", "baseline",
                                               "prob_A", "prob_D", "prob_F", "prob_E"])
        writer.writeheader()
        writer.writerows(policy.get_probs_table())

    elapsed = time.time() - t0
    summary = _compute_run_summary(trace, variant.value, n_episodes, lr, elapsed, reward_fn)
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2))

    if verbose:
        print(f"  Done. {n_episodes} episodes in {elapsed:.1f}s. "
              f"Final mean reward: {summary['mean_reward_all']:.3f}  "
              f"ASR (last 50): {summary['asr_last50']:.1%}")

    return trace


def _compute_run_summary(
    trace: list[dict],
    variant: str,
    n_episodes: int,
    lr: float,
    elapsed: float,
    reward_fn: ResearchRewardFunction,
) -> dict:
    if not trace:
        return {"error": "no episodes"}

    asr_all = [r["sr_success"] for r in trace]
    rewards_all = [r["reward_total"] for r in trace]
    last50 = trace[-50:]

    cond_counts: dict[str, int] = {}
    cond_asr: dict[str, list] = {}
    for r in trace:
        c = r["condition"]
        cond_counts[c] = cond_counts.get(c, 0) + 1
        cond_asr.setdefault(c, []).append(r["sr_success"])

    # Final policy probs per goal (average over goals)
    final_probs: dict[str, list] = {a: [] for a in ACTIONS}
    for r in trace[-20:]:
        for a in ACTIONS:
            final_probs[a].append(r[f"prob_{a}"])
    avg_final = {a: sum(v) / len(v) if v else 0 for a, v in final_probs.items()}
    dominant = max(avg_final, key=avg_final.get)

    l22_vals = [r["l22_think_phase"] for r in trace if r.get("l22_think_phase") is not None]

    return {
        "variant": variant,
        "n_episodes": len(trace),
        "lr": lr,
        "elapsed_seconds": round(elapsed, 2),
        "mean_reward_all": round(sum(rewards_all) / len(rewards_all), 4),
        "asr_all": round(sum(asr_all) / len(asr_all), 4),
        "asr_last50": round(sum(r["sr_success"] for r in last50) / len(last50), 4),
        "condition_selection_counts": cond_counts,
        "condition_asr": {c: round(sum(v) / len(v), 3) for c, v in cond_asr.items()},
        "final_policy_avg_probs": avg_final,
        "dominant_action": dominant,
        "l22_episodes_with_data": len(l22_vals),
        "l22_mean_all_episodes": round(sum(l22_vals) / len(l22_vals), 4) if l22_vals else None,
        "l22_direction_label": "provisional harmful-vs-harmless contrast direction (Layer 22)",
        "reward_fn_params": reward_fn.population_l22_stats(),
    }
