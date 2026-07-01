# SLIDE 9 — Exact Audit: CoT Role (Amplifier, Not Gate)

**Audit date:** 2026-07-01  
**Source:** `outputs/stage4/intervention_judge_validation/cot_causal_role_sr_scored.jsonl`  
**Run:** `outputs/stage4/cot_causal_role/run_20260628_211949/results.jsonl` (32 rows)  
**Type:** Exploratory pilot (N=8 per condition)

---

## Dataset

- 32 rows total (8 per condition)
- 4 conditions: `baseline`, `forced_own_thinking`, `forced_cross_thinking`, `empty_thinking`
- All 32 rows have SR API scores (no NaN, no missing)
- Model: Qwen3-14B only
- Specific goals and source prompts: NOT extractable from available metadata (goal_index=None in the scored file)

---

## Results (authoritative: `sr_api_binary`)

**WARNING:** The field `sr_success` in this file is UNRELIABLE. All 32 rows have `sr_success=True` because `sr_score=0.5` (a placeholder) ≥ 0.5 threshold. The correct field is `sr_api_binary`.

| condition | N | sr_api_binary=True | ASR | adjudicated_label distribution |
|-----------|---|-------------------|-----|-------------------------------|
| baseline | 8 | **5** | **62.5%** | (counted via sr_api_binary) |
| forced_own_thinking | 8 | **5** | **62.5%** | |
| forced_cross_thinking | 8 | **4** | **50.0%** | |
| empty_thinking | 8 | **3** | **37.5%** | |
| **TOTAL** | **32** | **17** | **53.1%** | compliant=17, refusal=13, truncated=2 |

**Exact condition names in data:**
- `forced_own_thinking` (NOT "forced_own_cot" as documentation sometimes says)
- `forced_cross_thinking` (NOT "forced_cross_cot")
- `empty_thinking` ✓
- `baseline` ✓

---

## What Each Condition Does

**baseline:** Standard Condition A run. Model receives puzzle-wrapped prompt with thinking enabled. Generates its own reasoning and answers normally. ASR = 5/8 = 62.5%.

**forced_own_thinking:** The model's OWN CoT from a PREVIOUS run is pre-filled (inserted as assistant text). The model then generates the final answer starting from its own previously-generated reasoning. Tests whether the final answer is determined by the content of the thinking.

**forced_cross_thinking:** A DIFFERENT example's successful CoT is inserted (from a DIFFERENT source prompt/seed, also a successful A-condition run). Tests whether ANY successful CoT transferred from elsewhere can induce compliance on a new prompt.

**empty_thinking:** Thinking block is left empty (no reasoning inserted). Model generates final answer directly with no intermediate reasoning. Tests whether the puzzle alone (without CoT) can cause compliance.

---

## Interpretations

| Condition | Comparison | Interpretation |
|-----------|-----------|----------------|
| forced_own_thinking (62.5%) ≈ baseline (62.5%) | +0pp | CoT content: present and from correct source. Same ASR as no intervention → CoT IS sufficient (consistent with) |
| forced_cross_thinking (50%) < baseline (62.5%) | -12.5pp | Cross-source CoT reduces but doesn't eliminate success → CoT content partially source-specific |
| empty_thinking (37.5%) < baseline (62.5%) | -25pp | No CoT suppresses attack but 37.5% still succeed → CoT NOT necessary for all attacks |

---

## Scientific Assessment of Claims

| Claim | Status | Justification |
|-------|--------|---------------|
| "CoT is sufficient" | CONSISTENT WITH — not proven | forced_own_thinking = same ASR as baseline. But n=5/8 — very small. Could be sampling noise. |
| "CoT is not necessary" | CONSISTENT WITH | empty_thinking = 3/8 = 37.5%. The puzzle alone causes 37.5% of attacks to succeed without any CoT. So CoT is not required for compliance. |
| "CoT provides +25pp" | IMPRECISE | empty_thinking=37.5% vs baseline=62.5% → difference is 25pp. But this compares to a 8-example baseline. No paired test performed. |
| "CoT is an amplifier" | PLAUSIBLE but not proven | The 62.5% vs 37.5% difference suggests CoT amplifies puzzle effectiveness, but n=8 is far too small for confidence. |
| "Puzzle framing alone causes 37.5% ASR" | SUPPORTED from data | empty_thinking = 3/8 = 37.5%. Exact value. BUT: this uses a small N and is limited to specific goals and source prompts used in this pilot. |

**Statistically safe wording for N=8 per condition:**
"In this 8-example pilot, empty-thinking (no CoT) achieved 3/8=37.5% attack success, versus 5/8=62.5% for baseline — consistent with CoT amplifying but not being necessary for the attack. These cell sizes are too small for formal inference; the finding warrants replication."

---

## 13.97× Token Ratio

This number is from **Stage 4.7** (multi-prompt behavioral replication), NOT from the CoT causal role experiment.

**Source:** SPRINT_SUMMARY_JUN14_30.md §4 (Stage 4.7 results)

"Condition A averages 11,458 tokens vs F's 824 tokens → 13.97× ratio despite identical total prompt lengths."

This ratio quantifies how much MORE thinking the puzzle induces compared to a length-matched benign wrapper. It comes from 12 source prompts (3 per goal, 4 goals) run under greedy decoding.

**DO NOT present this number as coming from the CoT causal-role experiment.** These are separate experiments.

---

## Pending: What This Experiment Cannot Answer

1. Whether the CoT forcing method correctly captures natural CoT dynamics (model may "ignore" pre-filled thinking)
2. Whether results generalize beyond the specific goals tested (goal_index not recorded in scored file)
3. Whether the Gemma4 model shows the same pattern (experiment only run for Qwen3)
4. Whether 37.5% empty_thinking success is due to the puzzle structure, the specific harmful goal, or the generation temperature
