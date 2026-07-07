# GCG Ablation Pipeline Log

**Started:** 2026-07-07  
**Researcher:** Omer Yosef

---

## Overview

This pipeline executes 6 ablation experiments following Stage GCG-Full completion.
All ablations build on existing GCG-Full results in `outputs/stage_gcg_full/`.

| Exp | Description | Status | Jobs |
|---|---|---|---|
| 4A | CoT ablation: free-gen with enable_thinking=False | 🔄 RUNNING (642268) | 642268 |
| 4B | lambda_repr=0.0 optimization (upper-bound ASR) | 🔄 RUNNING (642269) | 642269 |
| 4C | Gemma4-only GCG-Full (cross-model CoT comparison) | 🔄 REF CACHE RUNNING (642270) | 642270 |
| 4D | Real-time adversarial detector (position-0 classifier) | 🔄 RUNNING (642271) | 642271 |
| 4E | Qwen3→Gemma4 text transfer eval | 🔄 RUNNING (642273) | 642273 |
| 4F | Full 520-behavior AdvBench eval (statistical robustness) | 🔄 RUNNING (642274) | 642272+642274 |

---

## Research Questions

1. **4A:** Does CoT reasoning cause GCG to fail? If `enable_thinking=False` raises ASR significantly, CoT is the primary defense.
2. **4B:** Is low ASR due to `repr_loss` conflict or CoT? With `lambda_repr=0.0`, does ASR change?
3. **4C:** Does Gemma4 (no extended CoT) show higher ASR than Qwen3 under identical GCG?
4. **4D:** Can a position-0 hidden-state classifier serve as a production-ready detector?
5. **4E:** Does the Qwen3-optimized suffix transfer to Gemma4 (text transfer)?
6. **4F:** What is the ASR across all 520 behaviors, not just the 25 we sampled?

---

## Phase 1: Batch 1 Submission (2026-07-07)

### Job Submissions

| Job ID | Script | Description |
|---|---|---|
| 642268 | run_gcg_cot_ablation.slurm | 4A: CoT disabled free-gen + unseen-seed | RUNNING |
| 642269 | run_gcg_full_lambda0.slurm | 4B: lambda_repr=0.0 optimization | RUNNING |
| 642270 | build_gcg_reference_cache_gemma4_full.slurm | 4C prep: Gemma4 reference cache | RUNNING |
| 642271 | run_gcg_train_detector.slurm | 4D: position-0 detector training | RUNNING |
| 642273 | run_gcg_cross_model_transfer.slurm | 4E: Qwen3→Gemma4 text transfer | RUNNING |
| 642272 | build_gcg_full520_manifest.slurm | 4F prep: build 520-behavior manifest | ✅ DONE (520 rows) |
| 642274 | run_gcg_full520_eval.slurm | 4F: full 520-behavior eval | RUNNING |

---

## Phase 2: Batch 2 (pending Phase 1 results)

- **4A post-processing:** replay + analysis (after 4A free-gen completes)
- **4B post-processing:** free-gen + unseen-seed + replay + analysis (after 4B opt completes)
- **4C optimization:** run_gcg_full_gemma4.slurm (after 4C ref cache completes)
- **4F evaluation:** run_gcg_full520_eval.slurm (after 4F manifest build completes)

---

## Phase 3: Batch 3 (pending Phase 2 results)

- **4B analysis:** detection delay after post-processing
- **4C post-processing:** free-gen + unseen-seed + replay + analysis (after 4C opt completes)

---

## Results (filled as jobs complete)

### 4A: CoT Ablation Results

**Run dir:** `outputs/stage_gcg_full/gcg_full_qwen3_cot_disabled/`

| Seed set | GCG optimized (CoT ON) | GCG optimized (CoT OFF) | Delta |
|---|---|---|---|
| Training (42,43,44) | 0.040 | TBD | TBD |
| Unseen (100,200,300) | 0.067 | TBD | TBD |

### 4B: lambda_repr=0.0 Results

**Run dir:** `outputs/stage_gcg_full/gcg_full_qwen3_lambda0/`

| Metric | lambda_repr=1.0 (original) | lambda_repr=0.0 |
|---|---|---|
| Best task_loss | 7.9746 (step 330) | TBD |
| Loss reduction | 74% | TBD |
| Training seed ASR | 0.040 | TBD |
| Unseen seed ASR | 0.067 | TBD |
| AUC at pos 0 | 1.000 | TBD |

### 4C: Gemma4-only Results

**Run dir:** `outputs/stage_gcg_full/gcg_full_gemma4_weighted/`

| Metric | Qwen3 (CoT, lambda=1.0) | Gemma4 (no extended CoT) |
|---|---|---|
| Best task_loss | 7.9746 | TBD |
| Training seed ASR | 0.040 | TBD |
| Unseen seed ASR | 0.067 | TBD |
| AUC at pos 0 | 1.000 | TBD |

### 4D: Real-Time Detector Results

**Report:** `outputs/stage_gcg_ablation/detector/DETECTOR_REPORT.md`

| Metric | Value |
|---|---|
| Training AUC (5-fold CV) | TBD |
| Precision (threshold=0.5) | TBD |
| Recall (threshold=0.5) | TBD |
| Feature: position-0 hidden state | layer-averaged, all 8 layers |
| Latency overhead | TBD ms |

### 4E: Transfer Eval Results

**Run dir:** `outputs/stage_gcg_full/gcg_full_qwen3_to_gemma4_transfer/`

| Condition | Qwen3→Gemma4 ASR | Gemma4 baseline (task_only) |
|---|---|---|
| optimized_weighted (Qwen3 suffix) | TBD | TBD |
| neutral_control | TBD | TBD |

### 4F: Full 520-Behavior Results

**Run dir:** `outputs/stage_gcg_full/gcg_full_qwen3_full520_eval/`

| Condition | Hits/Total | ASR | vs Training-set ASR |
|---|---|---|---|
| optimized_weighted | TBD | TBD | TBD |
| task_only | TBD | TBD | TBD |
| neutral_control | TBD | TBD | TBD |

---

## Bugs Fixed

(filled as found)

---

## Key Findings

(filled as experiments complete)
