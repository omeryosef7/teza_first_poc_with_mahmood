#!/usr/bin/env python3
"""
Online REINFORCE RL experiment for CoT hijacking structural wrapper selection.

Runs 3 reward variants (cost_asr, cost_mechanistic, cost_l22_deflect) with a
REINFORCE policy gradient algorithm. Policy learns to select from conditions
{A, D, F, E} based on StrongReject success + research-motivated secondary signals.

Usage (simulation mode — uses existing Stage 4.7/4.8 data):
    python3 run_rl_experiment.py \\
        --out-dir outputs/rl_experiment/run_$(date +%Y%m%d_%H%M%S) \\
        --n-episodes 200 \\
        --lr 0.05 \\
        --seed 42

Usage (live mode — actually calls Qwen3-14B via SLURM):
    python3 run_rl_experiment.py \\
        --out-dir outputs/rl_experiment/run_$(date +%Y%m%d_%H%M%S) \\
        --n-episodes 48 \\
        --live-eval \\
        --seed 42
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)


def run_sim_mode(args: argparse.Namespace) -> None:
    """Run simulation mode: REINFORCE over stochastic empirical simulator."""
    from poc_rl_loop.rl_environment import StochasticEnvironment
    from poc_rl_loop.rl_reward_function import ResearchRewardFunction, RewardVariant
    from poc_rl_loop.rl_training_loop import run_rl_experiment
    from poc_rl_loop.rl_l22_diagnostic import analyze_l22_by_outcome, analyze_l22_by_condition
    from poc_rl_loop.generate_rl_figures import (
        generate_reward_curve, generate_policy_convergence, generate_l22_diagnostic_bar
    )
    from poc_rl_loop.generate_rl_report import generate_report

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log.info("Output directory: %s", out_dir)

    log.info("Loading environment from Stage 4.7 + 4.8 data...")
    env = StochasticEnvironment(rng_seed=args.seed)
    env_summary = env.summary()
    log.info("Environment loaded. %d cells, goals=%s, conditions=%s",
             len(env_summary), env.available_goals, env.available_conditions)

    reward_fn = ResearchRewardFunction(env)
    log.info("L22 population stats: %s", reward_fn.population_l22_stats())

    variants = [RewardVariant.cost_asr, RewardVariant.cost_mechanistic, RewardVariant.cost_l22_deflect]
    all_traces: dict[str, list[dict]] = {}
    all_summaries: dict[str, dict] = {}
    all_diagnostics = {}

    for i, variant in enumerate(variants):
        log.info("=== Running variant %d/3: %s ===", i + 1, variant.value)
        var_dir = out_dir / variant.value
        trace = run_rl_experiment(
            variant=variant,
            n_episodes=args.n_episodes,
            lr=args.lr,
            ema=args.ema,
            rng_seed=args.seed + i * 1000,
            out_dir=var_dir,
            env=env,
            reward_fn=reward_fn,
            verbose=True,
        )
        all_traces[variant.value] = trace
        all_summaries[variant.value] = json.loads((var_dir / "run_summary.json").read_text())
        all_diagnostics[variant.value] = analyze_l22_by_outcome(trace)
        l22_by_cond = analyze_l22_by_condition(trace)
        (var_dir / "l22_by_condition.json").write_text(json.dumps(l22_by_cond, indent=2))

    log.info("Generating figures...")
    generate_reward_curve(all_traces, out_dir / "fig_rl_reward_curve.png")
    for variant_name, trace in all_traces.items():
        generate_policy_convergence(trace, variant_name,
                                    out_dir / f"fig_rl_policy_convergence_{variant_name}.png")
    generate_l22_diagnostic_bar(all_diagnostics, out_dir / "fig_rl_l22_diagnostic.png")

    log.info("Generating report...")
    report_path = generate_report(
        out_dir=out_dir,
        summaries=all_summaries,
        diagnostics=all_diagnostics,
        n_episodes=args.n_episodes,
        lr=args.lr,
        ema=args.ema,
        env_summary=env_summary,
    )
    log.info("Report written: %s", report_path)

    # Write combined metadata
    meta = {
        "mode": "simulation",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "n_episodes": args.n_episodes,
        "lr": args.lr,
        "ema": args.ema,
        "seed": args.seed,
        "variants": list(all_summaries.keys()),
        "dominant_actions": {v: s.get("dominant_action") for v, s in all_summaries.items()},
        "asr_last50": {v: s.get("asr_last50") for v, s in all_summaries.items()},
        "env_n_cells": len(env_summary),
        "env_goals": env.available_goals,
        "env_conditions": env.available_conditions,
    }
    (out_dir / "experiment_meta.json").write_text(json.dumps(meta, indent=2))
    log.info("Experiment complete. Meta: %s", json.dumps(meta))
    print(f"\nRL experiment complete. Results in: {out_dir}")
    print(f"Report: {report_path}")


def run_live_mode(args: argparse.Namespace) -> None:
    """Run live mode: REINFORCE with actual Qwen3-14B calls per episode."""
    import csv
    import math
    from poc_rl_loop.rl_policy import REINFORCEPolicy, ACTION_TO_IDX, IDX_TO_ACTION, ACTIONS
    from poc_rl_loop.rl_reward_function import RewardVariant
    from poc_rl_loop.rl_environment import EpisodeObs, StochasticEnvironment
    from poc_rl_loop.rl_reward_function import ResearchRewardFunction
    from poc_rl_loop.live_rl_runner import load_model, _load_prompt_pool, run_live_episode

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log.info("LIVE MODE — Output: %s", out_dir)

    variant = RewardVariant[args.live_variant]
    log.info("Reward variant: %s", variant.value)

    # Load goal texts for StrongReject scoring
    _baseline = Path(__file__).resolve().parent / "outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl"
    goal_text_map: dict[int, str] = {}
    if _baseline.exists():
        import json as _json
        for line in _baseline.read_text().splitlines():
            line = line.strip()
            if line:
                r = _json.loads(line)
                gi = int(r.get("goal_index", -1))
                if gi >= 0 and gi not in goal_text_map:
                    goal_text_map[gi] = r.get("goal", "")
        log.info("Loaded goal texts for %d goal indices", len(goal_text_map))
    else:
        log.warning("Baseline JSONL not found; StrongReject scoring will be skipped")

    env = StochasticEnvironment(rng_seed=args.seed)
    reward_fn = ResearchRewardFunction(env)
    goals = env.available_goals
    n_goals = max(goals) + 1 if goals else 4

    policy = REINFORCEPolicy(n_goals=n_goals, lr=args.lr, ema=args.ema, rng_seed=args.seed)
    goal_rng = random.Random(args.seed + 777)
    seed_rng = random.Random(args.seed + 888)

    log.info("Loading Qwen3-14B...")
    tokenizer, model = load_model()
    prompt_pool = _load_prompt_pool()
    log.info("Prompt pool loaded: %d cells", len(prompt_pool))

    var_dir = out_dir / variant.value
    var_dir.mkdir(parents=True, exist_ok=True)

    trace: list[dict] = []
    cumulative_reward = 0.0

    trace_path = var_dir / "rl_policy_trace.jsonl"
    sel_path = var_dir / "rl_condition_selection_history.csv"

    with trace_path.open("w") as trace_f, sel_path.open("w", newline="") as sel_f:
        writer = csv.DictWriter(sel_f, fieldnames=[
            "step", "goal_idx", "condition", "sr_success", "reward_total",
            "prob_A", "prob_D", "prob_F", "prob_E", "elapsed_seconds"
        ])
        writer.writeheader()

        for step in range(1, args.n_episodes + 1):
            goal_idx = goal_rng.choice(goals)
            policy_step = policy.sample(goal_idx)
            condition = policy_step.condition
            seed = seed_rng.randint(200, 9999)

            log.info("[step %d/%d] goal=%d condition=%s", step, args.n_episodes, goal_idx, condition)

            live_result = run_live_episode(
                goal_idx=goal_idx,
                condition=condition,
                prompt_pool=prompt_pool,
                model=model,
                tokenizer=tokenizer,
                seed=seed,
                goal_map={(gi, c): goal_text_map.get(gi, "") for gi in goal_text_map for c in ["A","D","F","E"]},
            )

            if live_result is None:
                log.warning("Skipping step %d (no prompt or inference failed)", step)
                continue

            obs = EpisodeObs(
                goal_idx=goal_idx,
                condition=condition,
                sr_success=live_result.sr_success,
                sr_score=live_result.sr_score,
                think_token_count=live_result.think_token_count,
                is_censored=live_result.is_censored,
                onset_percent=live_result.onset_percent,
                l22_think_phase=math.nan,
                data_source="live",
            )
            reward_comps = reward_fn.compute(obs, variant)
            update_info = policy.update(goal_idx, policy_step.action_idx, reward_comps.total)
            cumulative_reward += reward_comps.total
            probs = policy.get_probs(goal_idx)

            record = {
                "step": step,
                "goal_idx": goal_idx,
                "condition": condition,
                "variant": variant.value,
                "sr_success": live_result.sr_success,
                "sr_score": live_result.sr_score,
                "think_token_count": live_result.think_token_count,
                "is_censored": live_result.is_censored,
                "onset_percent": None if math.isnan(live_result.onset_percent) else live_result.onset_percent,
                "elapsed_seconds": round(live_result.elapsed_seconds, 2),
                "reward_total": reward_comps.total,
                "advantage": update_info["advantage"],
                "baseline": update_info["baseline"],
                "prob_A": probs["A"],
                "prob_D": probs["D"],
                "prob_F": probs["F"],
                "prob_E": probs["E"],
                "cumulative_reward": cumulative_reward,
                "mean_reward_so_far": cumulative_reward / step,
            }
            trace.append(record)
            trace_f.write(json.dumps(record) + "\n")
            trace_f.flush()
            writer.writerow({
                "step": step,
                "goal_idx": goal_idx,
                "condition": condition,
                "sr_success": live_result.sr_success,
                "reward_total": round(reward_comps.total, 4),
                "prob_A": probs["A"],
                "prob_D": probs["D"],
                "prob_F": probs["F"],
                "prob_E": probs["E"],
                "elapsed_seconds": round(live_result.elapsed_seconds, 2),
            })

            if step % 10 == 0:
                policy.save(var_dir / f"policy_checkpoint_step{step}.json")
                log.info("[step %d] cumr=%.3f P(A)=%.3f P(D)=%.3f P(F)=%.3f P(E)=%.3f",
                         step, cumulative_reward / step,
                         probs["A"], probs["D"], probs["F"], probs["E"])

    policy.save(var_dir / "policy_final.json")
    log.info("Live RL experiment complete. %d episodes. Output: %s", len(trace), var_dir)
    print(f"\nLive RL done. {len(trace)} episodes. Output: {var_dir}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=str,
                        default=f"outputs/rl_experiment/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        help="Output directory")
    parser.add_argument("--n-episodes", type=int, default=200,
                        help="Number of RL episodes per variant (sim) or total (live)")
    parser.add_argument("--lr", type=float, default=0.05, help="REINFORCE learning rate")
    parser.add_argument("--ema", type=float, default=0.9, help="Baseline EMA coefficient")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--live-eval", action="store_true",
                        help="Live mode: actually call Qwen3-14B per episode (requires GPU)")
    parser.add_argument("--live-variant", type=str, default="cost_mechanistic",
                        choices=["cost_asr", "cost_mechanistic", "cost_l22_deflect"],
                        help="Reward variant for live mode (single variant only)")
    args = parser.parse_args(argv)

    if args.live_eval:
        run_live_mode(args)
    else:
        run_sim_mode(args)


if __name__ == "__main__":
    main()
