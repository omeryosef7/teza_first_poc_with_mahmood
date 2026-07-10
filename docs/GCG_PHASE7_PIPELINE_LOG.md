# GCG Phase 7 Pipeline Log

**Started:** 2026-07-10  
**Researcher:** Omer Yosef

---

## Overview

Phase 7 extends the GCG ablation pipeline based on findings from Phases 4–6:

| Exp | Description | Status |
|---|---|---|
| 7A | 5A suffix evaluated on all 520 AdvBench behaviors (scale) | 🔄 RUNNING |
| 7B-s43 | 5A optimization re-run with seed=43 (variance) | 🔄 RUNNING |
| 7B-s44 | 5A optimization re-run with seed=44 (variance) | 🔄 RUNNING |
| 7B-s45 | 5A optimization re-run with seed=45 (variance) | 🔄 RUNNING |
| 7C | Gemma4 GCG with enable_thinking=False (CoT-format robustness probe) | 🔄 RUNNING |
| 7D | GCG findings synthesis document (no GPU) | 🔄 IN PROGRESS |

---

## Research Questions

1. **7A:** Does the 5A CoT-prefix suffix generalize to all 520 AdvBench behaviors, or is the 10.7% ASR specific to the 25 training behaviors?
2. **7B:** What is the variance of the 5A attack across optimization seeds? Is 10.7% stable or seed-sensitive?
3. **7C:** Is Gemma4's 0% ASR due to the channel-token format issue, or intrinsic robustness? Testing with thinking=OFF removes the tokenization barrier.
4. **7D:** Written synthesis of Phases 4–6 GCG findings for paper/meeting use.

---

## Motivation from Phase 4–6 Findings

| Run | Optimized ASR | vs Baseline | Key Finding |
|---|---|---|---|
| Standard GCG (4F, 520 behaviors) | 1.9% | −0.5pp | Net-negative at full scale |
| 5A CoT-prefix (25 behaviors) | **10.7%** | +8pp | **Best attack; CoT misalignment was key** |
| 5A unseen seeds | **14.7%** | +2.7pp over training seeds | Generalizes, likely floor-suppressed |
| 5B CoT-pos0 repr | 1.3% | −1.4pp | repr_loss at CoT pos never converged |
| 5C quick-ASR | 10.7% | =5A | Selection cadence doesn't matter |
| 6A Qwen3 refusal-dir | 0% net-neg | −2.7pp | Refusal-dir constraint destroys suffix |
| 6A Gemma4 refusal-dir | 0% (noise) | +0pp | Gemma4 robust regardless |
| 6B Gemma4 CoT-channel | 0% (OPT stalled) | +0pp | Channel tokens infeasible for GCG |
| 6C Combined CoT+rd | 0% net-neg | −10.7pp | Objectives mutually destructive |

**Central Gap:** 5A achieves 10.7% but only tested on 25/520 behaviors with seed=42 only. Phase 7 closes this gap.

---

## Experiment 7A: 5A Suffix on Full 520 Behaviors

**Run dir:** `outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520/`  
**Manifest:** `outputs/stage_gcg_full/advbench_cot_full520_manifest.jsonl` (520 behaviors with CoT target)  
**Suffix source:** `gcg_full_qwen3_cot_target/FINAL_CANDIDATES.jsonl` (5A best suffix, seed=42)  
**Seeds evaluated:** 42, 43, 44 (training) + 100, 200, 300 (unseen)  
**Config:** Same as 5A free-gen; no optimization  
**Expected rows:** 520 × 4 conditions × 3 seeds = 6240  
**Wall time:** ~26h total → 4 passes of 8h each  

**Slurm:** `slurm_scripts/run_gcg_full_7a_5a_full520.slurm`

### Job Log

| Job | Pass | Rows | Status |
|---|---|---|---|
| **652222** | 1 | 0→? | 🔄 RUNNING |

### Results (TBD)

---

## Experiment 7B: Multi-seed 5A Optimization

**Run dirs:** `gcg_full_qwen3_7b_seed{43,44,45}/`  
**Manifest:** `advbench_cot_target_manifest.jsonl` (same 25-behavior CoT manifest as 5A)  
**Config:** Identical to 5A (500 steps, suffix_length=20, batch=64, topk=256, lambda_repr=0.0)  
**Only difference:** SEED = 43, 44, 45  
**Slurm:** `slurm_scripts/run_gcg_full_7b.slurm` (SEED env var)  
**Expected runtime:** ~4h each (same as 5A)

### Job Log

| Job | Seed | Status | task_loss best | ASR |
|---|---|---|---|---|
| **652223** | 43 | 🔄 RUNNING | — | TBD |
| **652224** | 44 | 🔄 RUNNING | — | TBD |
| **652225** | 45 | 🔄 RUNNING | — | TBD |

### Results (TBD)

**Hypothesis:** If 5A ASR is stable across seeds, the 10.7% is a robust estimate. If seed-dependent, it suggests the suffix depends on specific gradient paths.

---

## Experiment 7C: Gemma4 GCG with Thinking=OFF

**Run dir:** `outputs/stage_gcg_full/gcg_full_gemma4_7c_nothink/`  
**Model:** Gemma4-E4B-it  
**enable_thinking:** False (no `<|channel>thought\n` token in generation)  
**Target:** "Sure, here is {task}" (standard suffix, no CoT prefix)  
**Config:** 500 steps, batch=64, suffix_length=20, topk=256, lambda_repr=0.0  
**Slurm:** `slurm_scripts/run_gcg_full_7c_gemma4_nothink.slurm`

**Hypothesis:** 4C used Gemma4 with thinking=ON and target="Sure, here is..." → 0% ASR.  
This fails because the model always generates `<|channel>thought\n` first, so the target is misaligned.  
With thinking=OFF, "Sure, here is..." IS the correct first token — removing the alignment gap.  
If ASR is still 0%, Gemma4 is intrinsically robust (not just format-mismatched).

### Job Log

| Phase | Job | Status |
|---|---|---|
| OPT | **652226** | 🔄 RUNNING |
| Free-gen | TBD | awaiting OPT |
| Replay | TBD | awaiting free-gen |
| Analysis | TBD | awaiting replay |

### Results (TBD)

---

## Experiment 7D: GCG Findings Synthesis

**Output:** `docs/GCG_FINDINGS_SYNTHESIS.md`  
**Status:** 🔄 IN PROGRESS  
**No GPU required**

---

## Submission Log

| Job | Script | Experiment | Status |
|---|---|---|---|
| **652222** | run_gcg_full_7a_5a_full520.slurm | 7A full-520 eval pass 1 | 🔄 PENDING |
| **652223** | run_gcg_full_7b.slurm SEED=43 | 7B seed=43 opt | 🔄 PENDING |
| **652224** | run_gcg_full_7b.slurm SEED=44 | 7B seed=44 opt | 🔄 PENDING |
| **652225** | run_gcg_full_7b.slurm SEED=45 | 7B seed=45 opt | 🔄 PENDING |
| **652226** | run_gcg_full_7c_gemma4_nothink.slurm | 7C Gemma4 no-think opt | 🔄 PENDING |
