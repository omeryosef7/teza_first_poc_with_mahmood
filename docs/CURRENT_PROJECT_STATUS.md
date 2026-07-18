# Current Project Status

**As of:** 2026-07-12

---

## Overall Status: ALL GPU WORK COMPLETE

All GCG pipeline phases (Early, Full, Ablation 4–6, Phase 7) are done.  
Headline result: **5A CoT-prefix suffix achieves 8.92% unseeded ASR on all 520 AdvBench behaviors (+5.09pp vs neutral baseline, AUC=1.000).**

---

## Stage Completion Summary

| Stage | Status | Key outputs |
|-------|--------|-------------|
| Stage 2B | ✅ Complete | 42 attack examples, Qwen3-14B generations |
| Stage 3 | ✅ Complete | StrongREJECT scores for all 42 examples |
| Stage 4 (token dynamics) | ✅ Complete, frozen | Layer-0–39 projection; L22 direction (diagnostic) |
| Stage 4A2 (causal validation) | ✅ Complete | 0/160 survivors — direction diagnostic, not causal |
| Stage 4.5–4.8 | ✅ Complete | Attention, factorial, replication, stochastic gens |
| Mechanistic validation (P11/P14/P16) | ✅ Complete (SR-validated Jun 29) | L3–L22 causal; zero_attn_L26=0% ASR (−62pp) |
| Stage AE (early-token expansion) | ✅ Complete (Jul 1) | Paired A/D/E/G hidden-state replay; StrongREJECT scored |
| Stage GCG-Early | ✅ Complete (Jul 6) | 8 findings confirmed; unseen-seed generalization on both models |
| Stage GCG-Full | ✅ Complete (Jul 7) | AUC=1.000; GCG net-negative vs task_only on training seeds |
| GCG Ablation Phases 4–6 | ✅ Complete (Jul 10) | Best=5A CoT-prefix 10.7% on 25 behaviors; refusal-dir net-negative |
| GCG Phase 7A (scale to 520) | ✅ Complete (Jul 12) | 8.92% unseeded ASR, 493/520 behaviors, AUC=1.000 |
| GCG Phase 7B (seed variance) | ✅ Complete (Jul 12) | ASR range 1.3–16% across seeds; loss ≠ ASR predictor |
| GCG Phase 7C (Gemma4 intrinsic) | ✅ Complete (Jul 12) | 0% ASR even with thinking=OFF; Gemma4 intrinsically robust |

---

## GCG Phase 7 — COMPLETE (Jul 12)

### 7A — Scale 5A to all 520 behaviors
- **Training-seed ASR (seed 42):** 8.01% (125/1560, +5.83pp over neutral 2.18%)
- **Unseeded ASR (seeds 100/200/300):** **8.92%** (131/1468, 493/520 behaviors evaluated, +5.09pp over neutral 3.83%)
- **AUC:** 1.000 at ALL 32 generated-token positions (3,120 pairs, 520 behaviors × 3 seeds)
- **Seed-transfer gap:** −0.7pp (training seed 8.46% vs others 7.79%) — negligible
- **Key finding:** Full-scale ASR (8.92%) is lower than 25-behavior training-set ASR (10.7%) — small tuning set slightly overestimates, but positive uplift is robust and seed-independent.

### 7B — Seed variance across seeds 43/44/45
- Seed 45 achieves 16.0% (best); seed 44 achieves 1.3% (net-negative); seed 43 intermediate
- Loss at convergence does NOT predict ASR — loss is a poor ASR proxy
- AUC=1.000 universally for all seeds

### 7C — Gemma4 intrinsic robustness
- Optimization with thinking=OFF: best task_loss=12.47 (step 202), per-task avg 0.62 — better convergence than 5A Qwen3 (1.03)
- ASR = 0% across all 25 behaviors, all conditions (task_only baseline also 0%)
- Conclusion: **Gemma4 is intrinsically robust** — format-mismatch hypothesis ruled out; safety is deeper than 1D refusal direction or CoT alignment issue

---

## GCG Ablation Phases 4–6 — COMPLETE (Jul 10)

| Phase | Experiment | ASR (train) | ASR (unseen) | Key finding |
|-------|-----------|-------------|--------------|-------------|
| 4A | CoT OFF | 0% | 0% | CoT is required for any ASR |
| 4B | λ=0 (no repr loss) | 1.3% (1/75) | 2.7% | repr_loss actively suppresses ASR |
| 4C | Gemma4 optimization | 0% | 0% | Gemma4 resists optimization even with repr_loss |
| 4F | Full-520 (standard) | 1.9% | — | Net-negative at full scale |
| **5A** | **CoT-prefix** | **10.7% (8/75)** | **8.92% (7A result)** | **Best attack; +8pp over task_only** |
| 5B | CoT repr loss | 2.7% | — | Adds repr but no gain over task_only |
| 5C | Quick ASR | 10.7% | — | Confirms 5A result |
| 6A | Qwen3 + refusal dir | 0% | 0% | Refusal dir net-negative (−2.7pp vs task_only) |
| 6B | Gemma4 CoT target | 0% | 0% | Gemma4 resists |
| 6C | Qwen3 CoT + refusal | 0% | 0% | −10.7pp vs 5A (additive negative) |

---

## GCG-Full Pipeline — COMPLETE (Jul 7)

- **Qwen3 optimization:** 500 steps; best task_loss=20.52 (step 497); ASR on training seeds ~0.04 (near baseline)
- **Multimodel (Qwen3+Gemma4):** timed out at step 414, resumed; AUC=1.000 at all positions
- **Key finding:** GCG net-negative vs task_only on training seeds; CoT suppresses attack at position 0; AUC=1.000 means GCG suffix shifts generation reliably but compliance still blocked

---

## Mechanistic Validation (Sprint 2) — COMPLETE (SR-validated Jun 29)

- **P11 (full-range patching):** L3–L22 CAUSAL (0–10% ASR vs 50% baseline, 108/110 SR-valid)
- **P14 (gen-phase patching):** gen_thinking_L26=0%; all answer-phase=0% (attack committed late in thinking)
- **P16 (block ablation):** zero_attn_L26=0% ASR (−62pp most critical); ALL SUPPRESSIVE (109/117 SR-valid)
- **P4/P4b/P7:** Behavioral direction NON-CAUSAL (robust, n=11/11/4)

---

## No Running GPU Jobs

All jobs complete as of 2026-07-12. Documentation and analysis phase.

---

## Active Documents

| Document | Status |
|----------|--------|
| `docs/GCG_FINDINGS_SYNTHESIS.md` | ✅ Current (7 findings, 8.92% unseeded ASR) |
| `docs/GCG_PHASE7_PIPELINE_LOG.md` | ✅ Current (7A/7B/7C complete) |
| `docs/GCG_ABLATION_PIPELINE_LOG.md` | ✅ Current (Phases 4–6 complete) |
| `docs/GCG_FULL_PIPELINE_LOG.md` | ✅ Current (all phases complete) |
| `docs/RESEARCH_MASTER.md` | ✅ Updated (P11/P14/P16 SR-validated, P16 NON-CAUSAL overturned) |
| `docs/GCG_Phases4-7_Summary_2026-07-11.pptx` | ✅ Updated (all numbers corrected) |

---

## Important Constraints

- All GPU jobs: L40S nodes `n-801,n-802,n-803,n-804,n-805` (single GPU per job); no multi-GPU splitting except in documented multimodel runs
- GCG optimization: always pass `--no-filter-cand` (BPE tokenizers fail silently without it)
- Models: `Qwen/Qwen3-14B` and `google/gemma-4-E4B-it`
- Max 6 SLURM jobs in parallel; no job dependencies
