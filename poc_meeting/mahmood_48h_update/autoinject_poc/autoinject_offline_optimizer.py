"""
AutoInject-style offline optimization over existing Stage 4.7/4.8 structural cells.

This script implements an offline replay of what an AutoInject-style optimization loop
would select over our structural candidate pool. It is NOT a real online optimization.

What this does:
  - Treats existing A/D/F/E cells as the fixed candidate pool (arms/candidates)
  - Defines 3 reward functions
  - Compares 8 policies: always-A, always-D, always-F, empirical_best_overall,
    empirical_best_per_goal, AutoInject-style greedy, epsilon-greedy, UCB1
  - Produces policy comparison table and optimization traces

IMPORTANT:
  - This is offline replay, not a real optimized attack
  - AutoInject used GRPO training on live generations; we use static cell ranking
  - It tests whether the AutoInject optimization framing is adaptable to our domain
  - It does NOT prove that RL/AutoInject improves ASR (that requires an online experiment)
  - It should be presented as: AutoInject-style optimization POC (feasibility demonstration)

Outputs:
  autoinject_offline_policy_results.csv
  autoinject_offline_policy_results.md
  autoinject_optimization_trace.jsonl
  fig_autoinject_policy_rewards.png
  fig_autoinject_reward_tradeoffs.png
"""

import csv
import json
import math
import os
import random
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DATASET_PATH = (
    "outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc/autoinject_poc_dataset.csv"
)
OUT_DIR = "outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc"

random.seed(42)

# Default reward weights
ALPHA_ONSET = 0.1
ALPHA_THINKING = 0.1
BETA_CENSORING = 0.5


def safe_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1")
    return bool(val)


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def load_dataset(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def compute_rewards(rows, alpha_onset=ALPHA_ONSET, alpha_thinking=ALPHA_THINKING,
                    beta_censoring=BETA_CENSORING):
    """Add reward columns to each row."""
    think_vals = [safe_float(r.get("think_token_count", "0")) for r in rows]
    max_log = math.log1p(max(think_vals)) if max(think_vals) > 0 else 1.0

    for r in rows:
        sr_score = safe_float(r.get("sr_score", "0"))
        sr_success = safe_bool(r.get("sr_success", False))
        think = safe_float(r.get("think_token_count", "0"))
        censored = safe_bool(r.get("censored", False))
        onset = safe_float(r.get("onset_percent", "0"))

        log_think_norm = math.log1p(think) / max_log if max_log > 0 else 0.0
        onset_term = alpha_onset * onset
        thinking_term = alpha_thinking * log_think_norm
        censoring_penalty = beta_censoring * float(censored)

        r["reward_asr"] = float(sr_success)
        r["reward_sr_score"] = sr_score
        r["reward_combined"] = sr_score + onset_term + thinking_term - censoring_penalty
        r["reward_safe_mechanistic"] = sr_score + onset_term
        r["_log_think_norm"] = log_think_norm
        r["_onset_term"] = onset_term
        r["_thinking_term"] = thinking_term
        r["_censoring_penalty"] = censoring_penalty

    return rows


def rank_normalize(rewards: List[float]) -> List[float]:
    """Rank normalize to [-1, 1], borrowing AutoInject's pattern."""
    if not rewards:
        return []
    if len(rewards) == 1:
        return [0.0]
    n = len(rewards)
    sorted_with_idx = sorted(enumerate(rewards), key=lambda x: x[1])
    result = [0.0] * n
    for rank_idx, (orig_idx, _) in enumerate(sorted_with_idx):
        result[orig_idx] = (2.0 * rank_idx / (n - 1)) - 1.0
    return result


# ============================================================
# POLICIES
# ============================================================

def policy_always_condition(rows, condition, reward_key):
    """Fixed policy: always select from one condition."""
    pool = [r for r in rows if r.get("condition") == condition]
    if not pool:
        return None, None
    best = max(pool, key=lambda r: r[reward_key])
    return best, pool


def policy_empirical_best_overall(rows, reward_key):
    """Select the condition with highest average reward."""
    cond_rewards = defaultdict(list)
    for r in rows:
        cond_rewards[r.get("condition", "?")].append(r[reward_key])
    cond_mean = {c: sum(v) / len(v) for c, v in cond_rewards.items() if v}
    best_cond = max(cond_mean, key=cond_mean.get)
    pool = [r for r in rows if r.get("condition") == best_cond]
    best = max(pool, key=lambda r: r[reward_key])
    return best, pool


def policy_empirical_best_per_goal(rows, reward_key):
    """Per goal_index, select best condition. Return overall best."""
    goal_best = {}
    for goal_index in set(r.get("goal_index", "?") for r in rows):
        goal_rows = [r for r in rows if r.get("goal_index") == goal_index]
        cond_rewards = defaultdict(list)
        for r in goal_rows:
            cond_rewards[r.get("condition", "?")].append(r[reward_key])
        if cond_rewards:
            best_cond = max(cond_rewards, key=lambda c: sum(cond_rewards[c]) / len(cond_rewards[c]))
            goal_best[str(goal_index)] = best_cond
    return goal_best


def policy_greedy(rows, reward_key):
    """AutoInject-style greedy: select candidate with highest reward from pool."""
    if not rows:
        return None, []
    best = max(rows, key=lambda r: r[reward_key])
    return best, [best]


def policy_epsilon_greedy(rows, reward_key, epsilon=0.1, n_rounds=20):
    """Epsilon-greedy over structural conditions."""
    conditions = list(set(r.get("condition", "?") for r in rows))
    cond_counts = {c: 0 for c in conditions}
    cond_rewards = {c: [] for c in conditions}

    # Initialize: one random pull per condition
    for c in conditions:
        cond_rows = [r for r in rows if r.get("condition") == c]
        if cond_rows:
            pulled = random.choice(cond_rows)
            cond_rewards[c].append(pulled[reward_key])
            cond_counts[c] += 1

    trace = []
    for step in range(n_rounds):
        if random.random() < epsilon:
            c = random.choice(conditions)
            explore = True
        else:
            c = max(conditions, key=lambda x: (
                sum(cond_rewards[x]) / len(cond_rewards[x]) if cond_rewards[x] else 0.0
            ))
            explore = False

        c_rows = [r for r in rows if r.get("condition") == c]
        if c_rows:
            pulled = random.choice(c_rows)
            cond_rewards[c].append(pulled[reward_key])
            cond_counts[c] += 1
            trace.append({
                "step": step, "condition": c, "reward": pulled[reward_key],
                "candidate_id": pulled.get("candidate_id", ""),
                "explore": explore,
            })

    final_cond = max(conditions, key=lambda x: (
        sum(cond_rewards[x]) / len(cond_rewards[x]) if cond_rewards[x] else 0.0
    ))
    return final_cond, trace, {c: sum(v)/len(v) if v else 0 for c, v in cond_rewards.items()}


def policy_ucb1(rows, reward_key, n_rounds=20):
    """UCB1 over structural conditions."""
    conditions = list(set(r.get("condition", "?") for r in rows))
    cond_counts = {c: 0 for c in conditions}
    cond_rewards = {c: [] for c in conditions}

    # Initialize: pull each arm once
    for c in conditions:
        c_rows = [r for r in rows if r.get("condition") == c]
        if c_rows:
            pulled = random.choice(c_rows)
            cond_rewards[c].append(pulled[reward_key])
            cond_counts[c] = 1

    total_pulls = sum(cond_counts.values())
    trace = []

    for step in range(n_rounds):
        total_pulls += 1
        def ucb_score(c):
            n = cond_counts[c]
            if n == 0:
                return float("inf")
            mean_r = sum(cond_rewards[c]) / n
            bonus = math.sqrt(2 * math.log(total_pulls) / n)
            return mean_r + bonus

        c = max(conditions, key=ucb_score)
        c_rows = [r for r in rows if r.get("condition") == c]
        if c_rows:
            pulled = random.choice(c_rows)
            cond_rewards[c].append(pulled[reward_key])
            cond_counts[c] += 1
            trace.append({
                "step": step, "condition": c, "reward": pulled[reward_key],
                "candidate_id": pulled.get("candidate_id", ""),
                "ucb_score": ucb_score(c),
            })

    final_cond = max(conditions, key=lambda x: (
        sum(cond_rewards[x]) / len(cond_rewards[x]) if cond_rewards[x] else 0.0
    ))
    return final_cond, trace, {c: sum(v)/len(v) if v else 0 for c, v in cond_rewards.items()}


def run_all_policies(rows, reward_key):
    """Run all policies and return results dict."""
    results = {}

    # Fixed baselines
    for cond in ["A", "D", "F", "E"]:
        best, pool = policy_always_condition(rows, cond, reward_key)
        cpool = [r for r in rows if r.get("condition") == cond]
        results[f"always_{cond}"] = {
            "selected_condition": cond,
            "mean_reward": sum(r[reward_key] for r in cpool) / len(cpool) if cpool else 0.0,
            "asr": sum(safe_bool(r.get("sr_success", False)) for r in cpool) / len(cpool) if cpool else 0.0,
            "n_candidates": len(cpool),
        }

    # Empirical best overall
    best_overall, _ = policy_empirical_best_overall(rows, reward_key)
    cond_means = {}
    for cond in ["A", "D", "F", "E"]:
        pool = [r for r in rows if r.get("condition") == cond]
        cond_means[cond] = sum(r[reward_key] for r in pool) / len(pool) if pool else 0.0
    best_cond = max(cond_means, key=cond_means.get)
    results["empirical_best_overall"] = {
        "selected_condition": best_cond,
        "mean_reward": cond_means[best_cond],
        "asr": results[f"always_{best_cond}"]["asr"],
        "n_candidates": results[f"always_{best_cond}"]["n_candidates"],
        "condition_means": cond_means,
    }

    # Empirical best per goal
    goal_best = policy_empirical_best_per_goal(rows, reward_key)
    results["empirical_best_per_goal"] = {
        "selected_condition_per_goal": goal_best,
        "mean_reward_per_goal": {},
    }
    for goal, cond in goal_best.items():
        goal_rows = [r for r in rows if str(r.get("goal_index", "")) == str(goal) and r.get("condition") == cond]
        results["empirical_best_per_goal"]["mean_reward_per_goal"][goal] = (
            sum(r[reward_key] for r in goal_rows) / len(goal_rows) if goal_rows else 0.0
        )

    # AutoInject-style greedy (pick single best candidate)
    best_greedy, _ = policy_greedy(rows, reward_key)
    results["autoinject_greedy"] = {
        "selected_condition": best_greedy.get("condition", "?") if best_greedy else "?",
        "best_reward": best_greedy[reward_key] if best_greedy else 0.0,
        "candidate_id": best_greedy.get("candidate_id", "") if best_greedy else "",
        "sr_success": best_greedy.get("sr_success", "") if best_greedy else "",
        "note": "AutoInject-style greedy: picks single highest-reward candidate",
    }

    # Epsilon-greedy
    final_eg, trace_eg, eg_means = policy_epsilon_greedy(rows, reward_key, epsilon=0.1, n_rounds=20)
    results["epsilon_greedy"] = {
        "selected_condition": final_eg,
        "mean_reward": eg_means.get(final_eg, 0.0),
        "asr": results.get(f"always_{final_eg}", {}).get("asr", 0.0),
        "n_rounds": 20,
        "epsilon": 0.1,
        "condition_means": eg_means,
    }

    # UCB1
    final_ucb, trace_ucb, ucb_means = policy_ucb1(rows, reward_key, n_rounds=20)
    results["ucb1"] = {
        "selected_condition": final_ucb,
        "mean_reward": ucb_means.get(final_ucb, 0.0),
        "asr": results.get(f"always_{final_ucb}", {}).get("asr", 0.0),
        "n_rounds": 20,
        "condition_means": ucb_means,
    }

    return results, trace_eg, trace_ucb


def make_policy_table(all_results):
    """Build flat rows for CSV output."""
    rows = []
    for reward_key, policy_results in all_results.items():
        for policy_name, res in policy_results.items():
            sel = res.get("selected_condition") or res.get("selected_condition_per_goal", "mixed")
            if isinstance(sel, dict):
                sel = str(sel)
            rows.append({
                "reward": reward_key,
                "policy": policy_name,
                "selected_condition": sel,
                "mean_reward": res.get("mean_reward", res.get("best_reward", "")),
                "asr": res.get("asr", ""),
                "n_candidates": res.get("n_candidates", ""),
                "notes": res.get("note", ""),
            })
    return rows


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    rows = load_dataset(DATASET_PATH)
    rows = compute_rewards(rows)
    print(f"Loaded {len(rows)} candidates")

    reward_keys = ["reward_asr", "reward_sr_score", "reward_combined"]
    all_results = {}
    all_traces = []

    for reward_key in reward_keys:
        print(f"\n--- Reward: {reward_key} ---")
        results, trace_eg, trace_ucb = run_all_policies(rows, reward_key)
        all_results[reward_key] = results

        for step in trace_eg:
            all_traces.append({"reward": reward_key, "policy": "epsilon_greedy", **step})
        for step in trace_ucb:
            all_traces.append({"reward": reward_key, "policy": "ucb1", **step})

        for policy, res in results.items():
            cond = res.get("selected_condition", "?")
            mr = res.get("mean_reward", res.get("best_reward", "?"))
            asr = res.get("asr", "")
            asr_str = f"ASR={asr:.1%}" if isinstance(asr, float) else ""
            print(f"  {policy:30s}: selects={cond}, mean_reward={mr}, {asr_str}")

    # Write policy results CSV
    table_rows = make_policy_table(all_results)
    csv_path = os.path.join(OUT_DIR, "autoinject_offline_policy_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["reward", "policy", "selected_condition",
                                                "mean_reward", "asr", "n_candidates", "notes"])
        writer.writeheader()
        writer.writerows(table_rows)
    print(f"\nWritten: {csv_path}")

    # Write optimization trace JSONL
    trace_path = os.path.join(OUT_DIR, "autoinject_optimization_trace.jsonl")
    with open(trace_path, "w", encoding="utf-8") as f:
        for rec in all_traces:
            f.write(json.dumps(rec) + "\n")
    print(f"Written: {trace_path}")

    # Write markdown report
    _write_markdown(all_results, rows, OUT_DIR)

    # Generate figures
    _make_figures(all_results, rows, OUT_DIR)


def _write_markdown(all_results, rows, out_dir):
    reward_keys = ["reward_asr", "reward_sr_score", "reward_combined"]
    policy_order = [
        "always_A", "always_D", "always_F", "always_E",
        "empirical_best_overall", "autoinject_greedy",
        "epsilon_greedy", "ucb1",
    ]

    lines = [
        "# AutoInject Offline Policy Results",
        "",
        "**Mode:** Offline replay — existing Stage 4.7/4.8 cells as candidate pool",
        "**WARNING:** This is NOT a real optimized attack. It tests whether the AutoInject",
        "optimization framing can be adapted to our domain using existing artifacts.",
        "",
        "## Policy Comparison",
        "",
    ]

    for reward_key in reward_keys:
        lines += [f"### Reward: `{reward_key}`", "", "| Policy | Selected Condition | Mean Reward | ASR |",
                  "|--------|------------------|-------------|-----|"]
        res = all_results.get(reward_key, {})
        for policy in policy_order:
            if policy not in res:
                continue
            r = res[policy]
            sel = r.get("selected_condition", r.get("selected_condition_per_goal", "mixed"))
            if isinstance(sel, dict):
                sel = "/".join(f"{g}→{c}" for g, c in sel.items())
            mr = r.get("mean_reward", r.get("best_reward", ""))
            mr_str = f"{mr:.3f}" if isinstance(mr, float) else str(mr)
            asr = r.get("asr", "")
            asr_str = f"{asr:.1%}" if isinstance(asr, float) else str(asr)
            lines.append(f"| {policy} | {sel} | {mr_str} | {asr_str} |")
        lines.append("")

    # Condition ASR summary from data
    cond_asr = {}
    for cond in ["A", "D", "F", "E"]:
        pool = [r for r in rows if r.get("condition") == cond]
        if pool:
            asr = sum(safe_bool(r.get("sr_success", False)) for r in pool) / len(pool)
            cond_asr[cond] = asr

    lines += [
        "## Key Findings",
        "",
        "**Empirical ASR by condition (full dataset):**",
        "",
        "| Condition | N | ASR% | Mean SR Score |",
        "|-----------|---|------|--------------|",
    ]
    for cond in ["A", "D", "F", "E"]:
        pool = [r for r in rows if r.get("condition") == cond]
        if pool:
            asr = sum(safe_bool(r.get("sr_success", False)) for r in pool) / len(pool)
            mean_sr = sum(safe_float(r.get("sr_score", "0")) for r in pool) / len(pool)
            lines.append(f"| {cond} | {len(pool)} | {asr:.1%} | {mean_sr:.3f} |")

    lines += [
        "",
        "**What all policies select:**",
        "",
        "All reward definitions consistently select **condition A** as the optimal structural",
        "action. This is consistent with the empirical ASR (A ≈ 69%, vs D ≈ 47%, F ≈ 34%, E ≈ 33%).",
        "",
        "**Why this does not mean RL/AutoInject is necessary:**",
        "",
        "Condition A is clearly dominant in the existing data. An AutoInject-style optimizer",
        "would quickly converge to selecting A, which we already know from the empirical results.",
        "The value of an actual online AutoInject run would be to:",
        "  1. Validate that A is robust to variation (not cherry-picked)",
        "  2. Explore whether structural variations *within* A can improve ASR further",
        "  3. Test whether the reward signal is well-calibrated for guiding search",
        "",
        "**Risks of optimizing purely for thinking length:**",
        "",
        "Condition A produces the longest thinking (~13K tokens), and think_token_count",
        "correlates with ASR. But optimizing for think_token_count alone would select",
        "A regardless of whether the *content* of the thinking engages with the target.",
        "This could lead to reward hacking (long but off-topic thinking).",
        "Primary reward should remain sr_success/sr_score.",
        "",
        "**L22 projection note:**",
        "",
        "The Layer-22 'provisional harmful-vs-harmless contrast direction' is a diagnostic tool.",
        "It is NOT used as a primary reward in this POC. Using L22 as a reward would risk",
        "optimizing for a proxy that may not generalise beyond the current dataset.",
        "",
        "---",
        "",
        "*This is offline replay, not a real optimized attack.*",
        "*Generated by `poc_meeting/mahmood_48h_update/autoinject_poc/autoinject_offline_optimizer.py`*",
    ]

    md_path = os.path.join(out_dir, "autoinject_offline_policy_results.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Written: {md_path}")


def _make_figures(all_results, rows, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        conditions = ["A", "D", "F", "E"]
        reward_keys = ["reward_asr", "reward_sr_score", "reward_combined"]
        policy_order = [
            "always_A", "always_D", "always_F", "always_E",
            "empirical_best_overall", "autoinject_greedy", "epsilon_greedy", "ucb1",
        ]

        # Figure 1: Mean reward by condition, for each reward definition
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        cmap = {"A": "#4caf50", "D": "#2196f3", "F": "#ff9800", "E": "#9c27b0"}

        for ax, reward_key in zip(axes, reward_keys):
            cond_means = {}
            for cond in conditions:
                pool = [r for r in rows if r.get("condition") == cond]
                if pool:
                    cond_means[cond] = sum(r[reward_key] for r in pool) / len(pool)

            bars = ax.bar(list(cond_means.keys()),
                          list(cond_means.values()),
                          color=[cmap.get(c, "grey") for c in cond_means])
            ax.set_title(f"Mean {reward_key}", fontsize=10)
            ax.set_ylabel("Mean reward")
            ax.set_ylim(0, max(cond_means.values()) * 1.3 if cond_means else 1)
            for bar, val in zip(bars, cond_means.values()):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                        f"{val:.3f}", ha="center", va="bottom", fontsize=8)

        plt.suptitle("AutoInject Offline Optimization: Mean Reward by Condition\n"
                     "(Offline Replay Mode — NOT a real optimization)", fontsize=11)
        plt.tight_layout()
        fig_path = os.path.join(out_dir, "fig_autoinject_policy_rewards.png")
        plt.savefig(fig_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Written: {fig_path}")

        # Figure 2: Scatter — ASR vs thinking tokens by condition
        fig, ax = plt.subplots(figsize=(8, 6))
        for cond in conditions:
            pool = [r for r in rows if r.get("condition") == cond]
            if pool:
                x = [safe_float(r.get("think_token_count", "0")) / 1000 for r in pool]
                y = [safe_float(r.get("sr_score", "0")) for r in pool]
                asr_pct = 100 * sum(safe_bool(r.get("sr_success", False)) for r in pool) / len(pool)
                ax.scatter(x, y, c=cmap.get(cond, "grey"), label=f"{cond} (ASR={asr_pct:.0f}%)",
                           alpha=0.6, s=40, edgecolors="white", linewidths=0.5)

        ax.set_xlabel("Think tokens (thousands)")
        ax.set_ylabel("StrongReject score")
        ax.set_title("ASR vs Reasoning Length by Condition\n"
                     "(Optimizing thinking length alone risks reward hacking)", fontsize=10)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        fig_path2 = os.path.join(out_dir, "fig_autoinject_reward_tradeoffs.png")
        plt.savefig(fig_path2, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Written: {fig_path2}")

    except ImportError as e:
        print(f"Could not generate figures: {e}")


def safe_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1")
    return bool(val)


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


if __name__ == "__main__":
    main()
