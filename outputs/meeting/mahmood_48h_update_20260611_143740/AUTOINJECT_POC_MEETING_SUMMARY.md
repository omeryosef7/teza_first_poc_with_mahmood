# AutoInject POC — Meeting Summary (One Page)

**Prepared for:** Meeting with Mahmood Sharif, ~2026-06-13  
**Author:** Omer Yosef (TAU MSc thesis, CoT Hijacking)  
**Status:** Offline POC — pending online run approval

---

## What We Did

We inspected the existing AutoInject implementation and built a safe adapter
for reasoning-model hijacking. AutoInject uses **GRPO-based RL** (not black-box search)
to optimize adversarial text suffixes in LLM agent benchmarks.

We cannot run AutoInject directly (requires AgentDojo + live API + GPU).
Instead, we adapted its reward/scoring **framing** to our domain and ran it in
**offline replay mode** over existing Stage 4.7/4.8 cells.

## What We Found

| Condition | Description | ASR% |
|-----------|-------------|------|
| **A** | Full puzzle wrapper + thinking enabled | 68.8% |
| **D** | Bare target only + thinking enabled | 46.9% |
| **F** | Full puzzle + thinking disabled (length-matched benign) | 34.4% |
| **E** | Bare target + thinking disabled | 33.3% |

**All policies (greedy, ε-greedy, UCB1, empirical best) select Condition A.**
This holds across 64 reward weight combinations tested.

## What This POC Demonstrates

- The AutoInject optimization framing is adaptable to structural wrapper selection
- A is robustly dominant in existing data across all reward definitions
- Optimizing thinking length alone risks reward hacking (recommend α_thinking ≤ 0.1)
- L22 projection is diagnostic only — should not be used as a primary reward

## What We Are NOT Claiming

- This does NOT prove that RL/AutoInject improves ASR vs. always-A
- This does NOT generate new attacks
- This does NOT validate that the optimization converges in practice
- The onset heuristic is unvalidated (manual review in progress)

## Decision Needed From Mahmood

**Approve a constrained online AutoInject-style run:**

- Actions = {A, D, F, E} structural wrapper choices
- Prompts = existing Stage 4.7 research pool (no new harmful content)
- Reward = sr_success (primary)
- Budget = ~40 evaluations (2 goals × 4 conditions × 5 seeds)
- Goal = validate offline predictions; generate matched cells for direction extraction

**See:** `safe_autoinject_candidate_template.jsonl` for the exact run plan.

---

*This is a feasibility bridge, not a full attack optimizer.*
*Next meeting topic: approve or redirect the online experiment.*
