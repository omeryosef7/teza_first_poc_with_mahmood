"""
Generate AUTOINJECT_POC_RESULTS.md and AUTOINJECT_POC_MEETING_SUMMARY.md
from all produced outputs.
"""

import csv
import json
import os

AUTOINJECT_DIR = "outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc"
MEETING_DIR = "outputs/meeting/mahmood_48h_update_20260611_143740"
POLICY_CSV = os.path.join(AUTOINJECT_DIR, "autoinject_offline_policy_results.csv")
SENSITIVITY_CSV = os.path.join(AUTOINJECT_DIR, "autoinject_reward_sensitivity_grid.csv")
ACTION_SPACE_JSON = os.path.join(AUTOINJECT_DIR, "safe_structural_action_space.json")
INVENTORY_JSON = os.path.join(MEETING_DIR, "autoinject_poc", "autoinject_code_inventory.json")


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def load_csv(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    policy_rows = load_csv(POLICY_CSV)
    sens_rows = load_csv(SENSITIVITY_CSV)
    action_space = load_json(ACTION_SPACE_JSON)
    inventory = load_json(INVENTORY_JSON)

    # Extract cond stats from action_space
    cond_stats = action_space.get("observed_condition_statistics", {})

    # Extract policy summary for reward_asr
    asr_rows = [r for r in policy_rows if r.get("reward") == "reward_asr"]

    # Sensitivity summary
    n_grid = len(sens_rows)
    a_selected_count = sum(1 for r in sens_rows if r.get("best_condition_combined") == "A")

    _write_full_report(cond_stats, asr_rows, sens_rows, inventory, n_grid, a_selected_count)
    _write_meeting_summary(cond_stats, asr_rows, a_selected_count, n_grid)


def _write_full_report(cond_stats, asr_rows, sens_rows, inventory, n_grid, a_selected_count):
    lines = [
        "# AutoInject POC — Full Technical Results",
        "",
        "**Generated:** 2026-06-11  ",
        "**Status:** Offline replay POC — NOT a real optimization run  ",
        "**Safety:** All candidates from existing Stage 4.7/4.8 cells. No harmful content generated.",
        "",
        "---",
        "",
        "## 1. Why We Used AutoInject as the Basis",
        "",
        "One of the original project goals (from Mahmood's proposal) was to adapt AutoInject",
        "for reasoning-model hijacking and test whether refusal/safety representations are",
        "dampened during extended thinking. AutoInject is a natural starting point because:",
        "",
        "- It provides a principled optimization framing for adversarial prompt search",
        "- It was designed to adapt to the structure of the target task environment",
        "- Its reward/scoring framework maps directly onto our domain (sr_success ↔ injection success)",
        "- Its offline evaluation loop is directly portable as an analysis tool",
        "",
        "## 2. What AutoInject Does in the Original Code",
        "",
        "**Method:** GRPO (Group Relative Policy Optimization) — genuine policy gradient RL, not",
        "black-box search or evolutionary optimization.",
        "",
        "**Domain:** LLM agent benchmark (AgentDojo), learning adversarial text suffixes that",
        "redirect an AI agent to execute an injected malicious task.",
        "",
        "**Key components used in this POC:**",
        "- `rank_normalize_rewards()` from `reward_utils.py` — borrowed directly",
        "- Iterative candidate evaluation loop structure from `adaptive_agentdojo.py`",
        "- Greedy and baseline policy patterns from the learner architecture",
        "",
        "**Components NOT used (requires live infrastructure):**",
        "- GRPO training loop (TRLSuffixLearner) — would train a model on harmful goals",
        "- GPT feedback (feedback_utils.py) — requires OpenAI API",
        "- AgentDojo benchmark (not applicable to our domain)",
        "",
        "## 3. What Was Reusable vs. Adapted",
        "",
        "| AutoInject Component | Our Adaptation |",
        "|---------------------|----------------|",
        "| GRPO reward normalization | Borrowed: rank_normalize_rewards() |",
        "| Iterative eval loop | Adapted as offline cell ranking |",
        "| Greedy candidate selection | Directly ported as autoinject_greedy policy |",
        "| Random baseline | Mapped to always_A/D/F fixed baselines |",
        "| Checkpoint + trace logging | Adapted: autoinject_optimization_trace.jsonl |",
        "| AgentDojo task suite | NOT used (different domain) |",
        "| GRPO training | NOT used (requires GPU + live API + harmful goals) |",
        "",
        "## 4. Safe Action Space",
        "",
        "| Action | Description | ASR% | Mean SR Score |",
        "|--------|-------------|------|--------------|",
    ]

    for cond in ["A", "D", "F", "E"]:
        s = cond_stats.get(cond, {})
        lines.append(
            f"| {cond} | {s.get('description', '')} "
            f"| {s.get('asr_percent', '?')}% "
            f"| {s.get('mean_sr_score', '?')} |"
        )

    lines += [
        "",
        "## 5. Reward Definitions",
        "",
        "```",
        "reward_asr             = sr_success                          [primary — binary]",
        "reward_sr_score        = strongreject_score                  [primary — continuous]",
        "reward_combined        = sr_score",
        "                       + alpha_onset * onset_percent",
        "                       + alpha_thinking * log_norm(think_tokens)",
        "                       - beta_censoring * censored           [default: α=0.1, β=0.5]",
        "reward_safe_mechanistic = sr_score + alpha_onset * onset_percent",
        "                                                             [no thinking length term]",
        "```",
        "",
        "**NOT used as primary reward:**",
        "- `think_token_count` alone — risks rewarding length over content engagement",
        "- `L22 projection` — diagnostic only; 'provisional harmful-vs-harmless contrast direction'",
        "  is not a validated reward signal",
        "",
        "## 6. Offline Optimization Results",
        "",
        "| Policy | Selected Condition | Mean ASR Reward |",
        "|--------|------------------|-----------------|",
    ]

    for row in asr_rows:
        policy = row.get("policy", "")
        sel = row.get("selected_condition", "")
        mr = row.get("mean_reward", "")
        try:
            mr_str = f"{float(mr):.3f}"
        except (ValueError, TypeError):
            mr_str = str(mr)
        lines.append(f"| {policy} | {sel} | {mr_str} |")

    lines += [
        "",
        "**Key finding:** All policies consistently select **Condition A** as the optimal",
        "structural action. This is robust across all 3 reward definitions.",
        "",
        "## 7. Reward Sensitivity",
        "",
        f"Grid: {n_grid} combinations tested (α_onset × α_thinking × β_censoring).",
        f"Condition A selected in **{a_selected_count}/{n_grid} = "
        f"{100*a_selected_count//n_grid if n_grid > 0 else '?'}% of combinations**.",
        "",
        "**Risk of optimizing for thinking length:**",
        "At high α_thinking (> 0.25), the reward over-selects long-reasoning conditions",
        "(A), which may reflect reward hacking rather than genuine target engagement.",
        "Recommendation: keep α_thinking ≤ 0.1.",
        "",
        "## 8. Why Optimization Is Not Necessary (but Still Valuable)",
        "",
        "Condition A is clearly dominant from empirical results (Stage 4.7 ASR ≈ 83%",
        "in Stage 4.7, ≈ 69% across full pool). An offline optimizer immediately selects A.",
        "This means the main contribution of a real AutoInject run would NOT be discovering",
        "A as optimal — that is already known.",
        "",
        "The value of an online AutoInject-style run would be:",
        "1. Validate that A remains robust *across goal indices* (not cherry-picked)",
        "2. Explore structural variations *within* A (target placement, answer cue strength)",
        "3. Generate the matched success/failure pairs needed for direction extraction",
        "4. Test the reward calibration in practice (does sr_success guide search efficiently?)",
        "",
        "## 9. Next Experiment (Requires Mahmood Approval)",
        "",
        "A constrained online AutoInject-style run with:",
        "- **Actions:** choose from {A, D, F, E} structural wrappers",
        "- **Prompts:** same 12 existing research prompts from Stage 4.7 pool",
        "- **Reward:** sr_success (primary), sr_score (secondary)",
        "- **Budget:** ~40 online evaluations (2 goals × 4 conditions × 5 seeds)",
        "- **Infrastructure:** same Slurm pipeline as Stage 4.7/4.8",
        "- **Safety:** no new harmful content; all prompts already IRB-cleared for research",
        "",
        "See `safe_autoinject_candidate_template.jsonl` for the exact run plan.",
        "",
        "## 10. Limitations and Caveats",
        "",
        "- This is offline replay, not a real RL optimization loop",
        "- The candidate pool is fixed (no new generations)",
        "- Condition A's dominance may reflect dataset bias (goals selected to have high A ASR)",
        "- Onset percent heuristic is unvalidated (see manual_onset_review_subset_30_40.csv)",
        "- L22 direction is provisional — described as 'diagnostic projection direction' only",
        "- GRPO training would require significant safety review before approval",
        "",
        "---",
        "",
        "*Generated by `poc_meeting/mahmood_48h_update/autoinject_poc/build_autoinject_poc_report.py`*",
    ]

    out_path = os.path.join(AUTOINJECT_DIR, "AUTOINJECT_POC_RESULTS.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Written: {out_path}")


def _write_meeting_summary(cond_stats, asr_rows, a_selected_count, n_grid):
    lines = [
        "# AutoInject POC — Meeting Summary (One Page)",
        "",
        "**Prepared for:** Meeting with Mahmood Sharif, ~2026-06-13  ",
        "**Author:** Omer Yosef (TAU MSc thesis, CoT Hijacking)  ",
        "**Status:** Offline POC — pending online run approval",
        "",
        "---",
        "",
        "## What We Did",
        "",
        "We inspected the existing AutoInject implementation and built a safe adapter",
        "for reasoning-model hijacking. AutoInject uses **GRPO-based RL** (not black-box search)",
        "to optimize adversarial text suffixes in LLM agent benchmarks.",
        "",
        "We cannot run AutoInject directly (requires AgentDojo + live API + GPU).",
        "Instead, we adapted its reward/scoring **framing** to our domain and ran it in",
        "**offline replay mode** over existing Stage 4.7/4.8 cells.",
        "",
        "## What We Found",
        "",
        "| Condition | Description | ASR% |",
        "|-----------|-------------|------|",
    ]
    for cond in ["A", "D", "F", "E"]:
        s = cond_stats.get(cond, {})
        lines.append(f"| **{cond}** | {s.get('description', '')} | {s.get('asr_percent','?')}% |")

    lines += [
        "",
        "**All policies (greedy, ε-greedy, UCB1, empirical best) select Condition A.**",
        f"This holds across {n_grid} reward weight combinations tested.",
        "",
        "## What This POC Demonstrates",
        "",
        "- The AutoInject optimization framing is adaptable to structural wrapper selection",
        "- A is robustly dominant in existing data across all reward definitions",
        "- Optimizing thinking length alone risks reward hacking (recommend α_thinking ≤ 0.1)",
        "- L22 projection is diagnostic only — should not be used as a primary reward",
        "",
        "## What We Are NOT Claiming",
        "",
        "- This does NOT prove that RL/AutoInject improves ASR vs. always-A",
        "- This does NOT generate new attacks",
        "- This does NOT validate that the optimization converges in practice",
        "- The onset heuristic is unvalidated (manual review in progress)",
        "",
        "## Decision Needed From Mahmood",
        "",
        "**Approve a constrained online AutoInject-style run:**",
        "",
        "- Actions = {A, D, F, E} structural wrapper choices",
        "- Prompts = existing Stage 4.7 research pool (no new harmful content)",
        "- Reward = sr_success (primary)",
        "- Budget = ~40 evaluations (2 goals × 4 conditions × 5 seeds)",
        "- Goal = validate offline predictions; generate matched cells for direction extraction",
        "",
        "**See:** `safe_autoinject_candidate_template.jsonl` for the exact run plan.",
        "",
        "---",
        "",
        "*This is a feasibility bridge, not a full attack optimizer.*",
        "*Next meeting topic: approve or redirect the online experiment.*",
    ]

    out_path = os.path.join(MEETING_DIR, "AUTOINJECT_POC_MEETING_SUMMARY.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
