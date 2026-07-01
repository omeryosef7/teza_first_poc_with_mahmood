# Missing Data for Presentation

**Audit date:** 2026-07-01  
**Note:** Items listed here cannot be filled in without new experiments, new API calls, or re-running code. They are NOT errors in the current data — they are gaps in the experimental record.

---

## M1 — Full Text for Condition A Failures

**What's missing:** The thinking trace and final output for most Condition A failures.

**Scale:**
- Qwen3: 104/114 Condition A failures have no text (91%)
- Gemma4: 159/160 Condition A failures have no text (99%)

**Why it's missing:** The original runs did not store text for non-success cases in Condition A (disk space optimization).

**Impact on presentation:**
- Cannot describe WHY the puzzle attack fails for most Qwen3 Condition A cases
- Cannot describe Gemma4 A-condition failure mechanisms at all
- Any qualitative characterization of "why the puzzle fails" is based on at most 10/114 (Qwen3) or 1/160 (Gemma4) inspectable failures

**What's needed:** Re-run with `store_text=True` for failed rows only.

---

## M2 — Stage 4A2 Per-Model Causal Candidate Breakdown

**What's missing:** Which of the 160 candidates are Qwen3 vs Gemma4; whether Gemma4 was included in the 0/160 count.

**Why it's missing:** The `intervention_candidate_scores.checkpoint.jsonl` files were not read in this audit, and the sprint summary does not break down 160 = X (Qwen3) + Y (Gemma4).

**Impact on presentation:**
- Cannot confidently say "0/80 for each model" vs "0/160 Qwen3 only"
- Gemma4 causal status is ambiguous

**What's needed:** Read `outputs/stage4/qwen3-14b/intervention_candidate_scores.checkpoint.jsonl` and `outputs/stage4/gemma4-e4b-it/intervention_candidate_scores.checkpoint.jsonl` to count per-model.

---

## M3 — CoT Causal Role: Goal Identities

**What's missing:** Which specific goals were used in the 32-row CoT causal role experiment.

**Why it's missing:** `cot_causal_role_sr_scored.jsonl` has `goal_index=None` for all rows. The original `results.jsonl` also lacks goal metadata.

**Impact on presentation:**
- Cannot state which goals were tested
- Cannot assess whether the goals are representative
- Cannot compare ASR to the per-goal baseline from the factorial dataset

**What's needed:** Trace back the source prompts in the CoT causal role run to identify which goals they represent.

---

## M4 — Canonical Refusal Direction for Qwen3-14B and Gemma4

**What's missing:** The direction vector extracted using the standard harmful-vs-harmless protocol (Zou/Arditi/similar).

**Why it's missing:** This experiment was never run. The current repo contains only our HVP/DVP/Behavioral directions.

**Impact on presentation:**
- Cannot say whether our behavioral direction is the same as the canonical refusal direction
- Cannot say whether the puzzle attack moves the representation toward or away from the canonical refusal direction
- Cannot make any comparative claim about "refusal direction" without this extraction

**What's needed:** Run `extract_refusal_direction.py` with a standard harmful/harmless dataset (e.g., HarmBench), compute cosine similarity to behavioral direction.

---

## M5 — CoT Causal Role Results at Scale

**What's missing:** Replication of the 4-condition CoT experiment with N ≥ 50 per condition across all 11 goals.

**Why it's missing:** Only a pilot was run (N=8 per condition, 4 goals, Qwen3 only).

**Impact on presentation:**
- All CoT causal role claims (62.5%, 50%, 37.5%) rest on N=8 — too small for inference
- Gemma4 CoT causal role is completely untested
- Cannot distinguish "CoT is sometimes sufficient" from "CoT is usually sufficient"

**What's needed:** Scale-up run with N≥50, all 11 goals, both models.

---

## M6 — P11/P14/P16 for Gemma4

**What's missing:** Causal intervention results (prefill patching, generation patching, block ablation) for Gemma4-E4B-IT.

**Why it's missing:** All three experiments were run only for Qwen3-14B.

**Impact on presentation:**
- All intervention claims are Qwen3-only
- Cannot determine whether L26 is specific to Qwen3 or general
- Gemma4's "best layer" (L17) may have different causal properties

**What's needed:** Replicate P11/P14/P16 for Gemma4 at L17 (behavioral best layer) and L24 (DVP best layer).

---

## M7 — P14 Mechanism of Suppression

**What's missing:** Whether P14 suppression (0% ASR in gen_answer and gen_full conditions) is due to genuine refusal or truncation.

**Why it's missing:** The adjudicated_label shows 56/70 rows as "truncated" — but "truncated" means the output was cut off, not that the model refused. The SR API scores these as non-compliant (ASR=0%), but this may reflect a truncated output scoring low, not a genuine safety-behavior change.

**Impact on presentation:**
- Cannot claim "generation-phase patching induces refusal" — it may just break the output
- The mechanism is "truncation" not "refusal redirection"

**What's needed:** Read the actual truncated outputs to determine if they contain partial harmful content (mid-generation truncation) or clean refusal text.

---

## M8 — Selectivity Experiment Interpretation

**What's missing:** A null-disruption control that definitively separates "patching causes refusal" from "any context disruption causes output degradation."

**Why it's missing:** The selectivity pilot was run, but sham=66.7% and identity=55.6% suggests generic disruption is nearly as effective as targeted patching. We don't have a "clean null" experiment where context disruption is controlled at the same patch magnitude.

**Impact on presentation:**
- Cannot claim P11 "specifically inserts refusal signal"
- Cannot rule out that the entire P11 effect is disruption-not-refusal

**What's needed:** A disruption-matched control (e.g., random Gaussian noise with same magnitude as D-context activations).

---

## M9 — Gemma4 EOS Bug Full Impact

**What's missing:** Exact count of how many Gemma4 rows were affected by the two-terminal-token bug (finish_reason=max_tokens vs eos_token).

**Why it's missing:** The sprint mentions "~30% of Gemma4 outputs hit max_new_tokens" but the exact count by condition and whether the bug was fixed for all runs is not clear from currently-read files.

**Impact on presentation:**
- Some Gemma4 outputs may have been artificially truncated (causing incorrect sr_success=False)
- This could inflate Gemma4 refusal counts in early runs

**What's needed:** Check `finish_reason` field distribution in Gemma4 rows and compare pre-fix vs post-fix runs.

---

## M10 — Stage 4.7 Source Prompts and Goals

**What's missing:** Exact goal identities and source prompts used in the 13.97× token ratio calculation (Stage 4.7, 12 sources, 3 per goal, 4 goals).

**Why it's missing:** The sprint mentions "4 goals" but does not list which 4 of the 11 were used.

**Impact on presentation:**
- Cannot assess whether the 13.97× ratio generalizes to all 11 goals
- 4 goals may have been selected non-randomly

**What's needed:** Read the Stage 4.7 run manifest or output files to identify the 4 goals used.
