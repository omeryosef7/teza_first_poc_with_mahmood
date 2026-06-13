# AutoInject Code Audit

**Audit date:** 2026-06-11  
**Auditor:** Omer Yosef (TAU MSc thesis, CoT hijacking project)  
**Purpose:** Understand AutoInject's optimization framing to assess how it can be safely adapted
for reasoning-model hijacking research.  
**AutoInject repo location:** `AutoInject/AutoInject/`

---

## 1. What AutoInject Optimizes

AutoInject learns to inject adversarial instructions into LLM agent pipelines. It optimizes
**text suffixes** appended to environmental context (e.g., tool outputs, system memory) that
redirect an AI agent to execute an injected malicious task *in addition to* the legitimate user
task.

**Domain:** Prompt injection attacks against LLM agent benchmarks (AgentDojo suite — banking,
Slack, travel, workspace task types).

**This is NOT the same as our CoT hijacking project.** Key differences:

| Dimension | AutoInject | Our CoT Hijacking |
|-----------|-----------|-------------------|
| Target | LLM agent pipelines | Reasoning model (Qwen3-14B) |
| Attack vector | Text suffix injected into tool outputs | Structural puzzle wrapper around harmful goal |
| Action space | Continuous text tokens in suffix | Discrete structural wrappers (A/D/F/E) |
| Reward | Binary task success in agent benchmark | StrongReject score (sr_success/sr_score) |
| Optimization | GRPO policy gradient (online) | Offline cell ranking (this POC) |

---

## 2. Optimization Method: GRPO-Based Reinforcement Learning

AutoInject uses **GRPO (Group Relative Policy Optimization)**, a policy gradient variant
implemented in the TRL (Transformer Reinforcement Learning) library by Hugging Face.

**GRPO is genuine RL** — it trains a language model policy using gradient descent on rollout
rewards. It is NOT:
- Black-box search / evolutionary optimization
- Random mutation / beam search
- Bayesian optimization or bandit algorithms

**GRPO details:**
- The policy model generates candidate suffixes (rollouts)
- Each candidate is evaluated in the AgentDojo benchmark environment
- Rewards are computed and rank-normalized within a group of candidates
- Policy gradient updates adjust the suffix-generating model toward high-reward suffixes
- KL penalty (beta=10.0) prevents policy collapse

**Key training parameters found in `learner.py`:**
```python
grpo_num_generations: int = 8          # rollouts per training step
grpo_learning_rate: float = 1e-7       # very conservative LR
grpo_per_device_train_batch_size: int = 2
grpo_max_grad_norm: float = 0.1        # gradient clipping for stability
grpo_beta: float = 10.0                # KL penalty weight
```

---

## 3. Key Components and File Inventory

### 3.1 Main Optimization Loop
**File:** `src/rlpi/agentdojo/adaptive_agentdojo.py`  
**Function:** `run_adaptive_attack(cfg, suite, pipeline, attacker, learner, ...)`  
**Role:** Orchestrates the full iterative attack loop. Manages query budgets, checkpointing,
iteration control, and calls the learner's `learn()` method each iteration.  
**Reusability:** The loop structure (candidate → evaluate → update → checkpoint) is directly
analogous to what our offline optimizer does over structural cells.

### 3.2 GRPO Learner
**File:** `src/rlpi/attack/learners/trl_suffix/learner.py`  
**Class:** `TRLSuffixLearner`  
**Role:** Implements the GRPO training loop using TRL's `GRPOTrainer`. Takes a candidate suffix
pool, evaluates them in AgentDojo, computes rewards, updates the policy model.  
**Direct reuse:** NOT possible without AgentDojo + live LLM API + GPU.

### 3.3 Reward Utilities
**File:** `src/rlpi/attack/learners/trl_suffix/reward_utils.py`  
**Functions:**
- `rank_normalize_rewards(rewards)` — converts raw rewards to [-1, 1] normalized ranks
- `extract_injection_goal_from_prompt(prompt)` — parses goal from adversarial prompt
- `create_experience_based_reward_function(...)` — wraps evaluator into a TRL reward callable  
**Reusability:** `rank_normalize_rewards` is directly portable to our offline optimizer. The
rank normalization logic is useful for comparing policies across different reward scales.

### 3.4 Adaptive Reward / GPT Feedback
**File:** `src/rlpi/attack/learners/common/feedback_utils.py`  
**Function:** `compute_adaptive_reward(...)`, `compare_suffix_with_previous(...)`  
**Role:** Uses GPT-4 to compare suffix quality against a baseline and compute a comparative
reward signal. Requires OpenAI API.  
**Reusability:** NOT safe to use directly. Conceptually, this corresponds to our L22 projection
diagnostic — both are secondary signals that add nuance beyond binary success.

### 3.5 Random Baseline
**File:** `src/rlpi/attack/learners/adaptive_random_suffix/learner.py`  
**Role:** Random suffix mutation baseline for comparison against GRPO.  
**Reusability:** Conceptually maps to our `always_A` / `always_D` / `always_F` fixed baselines.

### 3.6 AgentDojo Benchmark
**Directory:** `agentdojo/src/agentdojo/`  
**Role:** Defines task suites (banking, Slack, travel, workspace) with injection and user tasks.
Also provides the evaluation harness that scores whether the agent executed the injected goal.  
**Reusability:** NOT applicable to our domain.

---

## 4. Candidate Generation / Mutation Logic

In AutoInject, candidate generation works as follows:
1. The policy model (LLM) generates `grpo_num_generations=8` suffix candidates per training step
2. Each candidate is a token sequence of up to `max_suffix_length=20` tokens
3. Candidates are inserted into the AgentDojo injection point
4. The agent pipeline runs; the evaluator scores whether the injected goal was executed

There is no explicit evolutionary mutation — GRPO learns to propose better suffixes via
gradient updates, not by manually mutating past suffixes.

**Our analogy:** In our offline POC, "candidate generation" means selecting from the existing
pool of Stage 4.7/4.8 runs. The structural wrapper choices (A/D/F/E) replace the continuous
suffix token space.

---

## 5. Reward / Scoring Signal

**AutoInject reward:** Binary 0/1 from AgentDojo evaluator — did the agent execute the injected
task? GPT feedback optionally adds a soft comparative signal.

**Rank normalization:** Raw binary rewards are rank-normalized to [-1, 1] within a group of
candidates (GRPO requirement).

**Our analogy:** We use `sr_success` (binary) and `strongreject_score` (continuous [0,1]).
These are direct analogues of AutoInject's binary success signal. We implement our own
`rank_normalize_rewards` (borrowed from `reward_utils.py`) and add onset timing, thinking
length, and censoring penalty as secondary components.

---

## 6. What Parts Are Reusable for CoT Hijacking

| Component | Reusable? | How |
|-----------|-----------|-----|
| `rank_normalize_rewards()` | YES | Directly borrowed in offline optimizer |
| Iterative candidate scoring loop | YES (structure only) | Implemented in `autoinject_offline_optimizer.py` |
| Greedy candidate selection | YES | Adapted as AutoInject-style greedy policy |
| Checkpoint + trace logging | YES (pattern) | `autoinject_optimization_trace.jsonl` |
| GRPO training | NO | Requires AgentDojo + live API + GPU; not safe to run |
| GPT comparative feedback | NO | Requires OpenAI API; not appropriate at this stage |
| AgentDojo task suite | NO | Different domain entirely |

---

## 7. What Parts Are Unsafe or Inappropriate to Run Directly

1. **Full GRPO training on harmful goals** — would directly train a model to generate harmful
   content more effectively. Not appropriate.
2. **GPT feedback on suffix quality** — requires OpenAI API and would expose harmful content
   to an external service.
3. **Running AgentDojo with injection tasks** — not relevant to reasoning-model hijacking.
4. **Any online generation of new hijacking prompts** — must be offline-only until Mahmood
   explicitly approves an online optimization run with a safe action/reward definition.

---

## 8. Minimal Safe Integration Path

The safe adaptation of AutoInject for our project follows this path:

**Step 1 (this POC — offline):** Treat existing Stage 4.7/4.8 structural condition cells
(A/D/F/E) as a fixed candidate pool. Apply AutoInject-style reward scoring and greedy selection.
Borrow `rank_normalize_rewards` logic. Produce an optimization trace showing which structural
conditions would be selected.

**Step 2 (requires Mahmood approval — constrained online):** Run a small online experiment
where the "action" is choosing a structural wrapper (A/D/F/E) and the "generation" is running
Qwen3-14B on that wrapper. Use sr_success as the primary reward. No new harmful content is
generated — the prompts are the same existing research prompts already used in Stage 4.7.

**Step 3 (requires additional safety review):** Extend the action space to include minor
structural variations within a condition (e.g., target placement, answer cue phrasing). Only
if Step 2 is validated.

---

## 9. Is AutoInject RL, Black-Box Search, or Something Else?

**Conclusion: AutoInject is genuine RL (GRPO-based policy gradient).**

Evidence:
- Uses `GRPOTrainer` from TRL — a real RL training loop with gradient updates
- Policy model weights are updated each iteration
- KL divergence penalty against reference policy (standard RL constraint)
- Rank normalization of rewards (GRPO-specific technique)
- Very conservative learning rate (1e-7) typical of fine-tuning with RL

It is NOT:
- Random search (there is a learning signal updating model weights)
- Evolutionary algorithms (no population, selection, mutation operators)
- Bayesian optimization (no surrogate model, no acquisition function)
- Prompt mutation / GCG-style gradient attacks (no gradient through the victim model)

**For our meeting:** We should describe AutoInject as "GRPO-based RL training of adversarial
suffix policy" and clearly explain that our POC uses the reward/scoring *framing* from
AutoInject but runs in offline replay mode over existing structural candidates.

---

## 10. Summary

- AutoInject is a GRPO RL system for prompt injection in LLM agent benchmarks
- Its core contribution is showing that RL can learn to craft more effective prompt injections
  than random search
- For our CoT hijacking project, the directly relevant idea is: **use reward-shaped optimization
  over structural wrapper choices** rather than training a new model
- This POC validates that the AutoInject optimization framing can be adapted to our domain,
  using existing Stage 4.7/4.8 data as the offline candidate pool
- The next step — a constrained online AutoInject-style run — would require Mahmood's approval
  and a careful safety review of the action/reward definition
