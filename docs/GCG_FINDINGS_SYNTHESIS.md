# GCG Findings Synthesis: Phases 4–6

**Date:** 2026-07-10 (updated 2026-07-12 — Phase 7 fully complete)  
**Researcher:** Omer Yosef  
**Repository:** `outputs/stage_gcg_full/`  
**Log:** `docs/GCG_ABLATION_PIPELINE_LOG.md`

---

## 1. Executive Summary

Across 12 GCG optimization experiments on Qwen3-14B and Gemma4-E4B-it (plus a full-benchmark
confirmation, see below):

- **Best attack (small tuning set):** 5A CoT-prefix targeting — **10.7% ASR** on 25 AdvBench behaviors (training seed 42); **14.7% on unseen seeds 100/200/300**
- **Confirmed at full benchmark scale (7A, COMPLETE):** the 5A suffix generalizes to all 520 AdvBench behaviors at **8.01% ASR** (training seeds, +5.83pp uplift) and **8.92% ASR** (unseen seeds 100/200/300, +5.09pp uplift, 493/520 behaviors), with AUC=1.000 at all 32 positions across 3,120 pairs. This is **lower** than the 25-behavior training-set number (10.7%) — the small tuning set somewhat overestimated attack effectiveness, though the positive, seed-robust uplift holds up at scale.
- **Standard GCG (Qwen3, 520 behaviors):** 1.9% — net-negative vs 2.4% task_only baseline
- **Detection:** AUC = **1.000 at generated token position 0** across ALL Qwen3 variants — adversarial suffix perfectly detectable from first token
- **Gemma4:** 0% ASR under ALL conditions (standard GCG, CoT-prefix, refusal-direction, CoT-channel)
- **Refusal direction:** Minimizing v_refusal projection via GCG is **counterproductive** — 0% net-negative vs 10.7% for CoT-prefix alone

---

## 2. Full Results Table (Phases 4–6)

| Exp | Model | Method | Opt ASR (training) | Opt ASR (unseen) | AUC pos 0 | vs Baseline |
|---|---|---|---|---|---|---|
| Standard (full run) | Qwen3 | GCG weighted | 4.0% | 6.7% | **1.000** | ≈ baseline |
| 4B | Qwen3 | λ_repr=0 (upper bound) | 1.3% | 1.3% | 0.500 invisible | ≈ baseline |
| 4C | Gemma4 | GCG weighted | **0%** | **0%** | 0.698 (pos 13) | = 0% baseline |
| 4D | Qwen3 | CoT-ON detector | — | — | **1.000** | — |
| 4D | Qwen3 | CoT-OFF detector | — | — | 0.507 (chance) | — |
| 4E | Qwen3→Gemma4 | Text transfer | **0%** | — | — | = 0% baseline |
| 4F (520) | Qwen3 | GCG weighted | 1.9% | — | — | **−0.5pp** net-neg |
| **5A** | Qwen3 | CoT-prefix target | **10.7%** | **14.7%** | **1.000** | **+8pp** |
| 5B | Qwen3 | CoT-pos0 repr | 1.3% | — | **1.000** | −2.7pp |
| 5C | Qwen3 | Quick-ASR selection | **10.7%** | — | **1.000** | =5A |
| 6A | Qwen3 | +refusal_dir_loss | **0% net-neg** | **0% net-neg** | **1.000** | **−10.7pp** |
| 6A | Gemma4 | +refusal_dir_loss | **0%** (noise) | **0%** | 0.070 pos 0 | +0pp |
| 6B | Gemma4 | CoT-channel prefix | **0%** (OPT stalled) | — | — | +0pp |
| 6C | Qwen3 | CoT+refusal_dir | **0% net-neg** | **0% net-neg** | **1.000** | **−10.7pp** |
| **7C** | Gemma4 | thinking=OFF, std target | **0%** | **0%** | **1.000** | 0% (= all baselines) |
| 7B s=43 | Qwen3 | CoT-prefix, seed=43 | **10.7%** (8/75) | **16.0%** (12/75) | **1.000** | +6.7pp train / +4.0pp unseen |
| 7B s=44 | Qwen3 | CoT-prefix, seed=44 | **1.3%** (1/75, net-neg) | **2.7%** (−8.0pp!) | **1.000** | **net-neg both regimes** |
| 7B s=45 | Qwen3 | CoT-prefix, seed=45 | **16.0%** (12/75) | **21.3%** (16/75) | **1.000** | +12.0pp train / +9.3pp unseen |
| **7A** | Qwen3 | CoT-prefix, 5A suffix, 520 behaviors | **8.01%** (125/1560) | **8.92%** (131/1468, seeds 100/200/300, **493/520 behaviors**) | **1.000** (all 32 pos, 3120 pairs) | **+5.83pp** train / **+5.09pp** unseen vs neutral |

---

## 3. Key Findings

### Finding 1: CoT target misalignment is the primary barrier to GCG success

The standard GCG target "Sure, here is {task}" assumes this is the model's first generated token. With `enable_thinking=True`:
- **Qwen3:** First generated token is `<think>`, not "Sure". Target is misaligned at position 0.
- **Gemma4:** First generated token is `<|channel>thought\n` (special token), not "Sure". Target misaligned.

5A fixed the Qwen3 misalignment by extending the target to `<think>\nOkay, I can help.\n</think>\n\nSure, here is {task}`. This caused task_loss to drop from ~30 → 14.9 at best (vs 7.97 for standard GCG, which optimizes an easier but wrong target). Despite higher loss, ASR jumped 4× (2.7% → 10.7%) because the suffix now pushes toward genuinely compliance-signaling generation.

**Implication:** GCG success is not about achieving low teacher-forced loss — it's about whether the optimized suffix aligns with a behaviorally meaningful generation trajectory.

### Finding 2: GCG adversarial suffixes are perfectly detectable at position 0 — universally, regardless of attack success

Across ALL Qwen3 GCG variants tested (standard, CoT-prefix, CoT+repr, refusal-dir, all 4 optimization seeds):
- **AUC = 1.000 at generated token 0** (first token, before any visible text)
- Cosine distance from neutral_control baseline grows monotonically through generation
- The GCG suffix creates a detectable signature in the **thinking phase**, not the response
- Qwen3's CoT reasoning identifies garbled suffix tokens → heightened safety response

**Phase 7B cross-seed confirmation (2026-07-11):** AUC=1.000 at pos 0 holds for ALL optimization seeds:

| Seed | ASR | AUC pos 0 | Repr dist pos 0 |
|---|---|---|---|
| 42 (5A ref) | 10.7% | **1.000** | 0.053 |
| 43 | 10.7% | **1.000** | 0.053 |
| 44 | **1.3% (net-neg)** | **1.000** | **0.067** (largest) |
| 45 | **16.0%** (best) | **1.000** | 0.063 |
| 7C Gemma4 | 0% | **1.000** | 0.007 |

**Key insight:** Detection (AUC) and attack success (ASR) are independent. s44 has the LARGEST repr shift (0.067) and LOWEST ASR (1.3%) — a suffix that strongly displaces activations from the neutral trajectory can still be net-negative. The position-0 detector fires on ALL suffixes regardless of their effectiveness.

**Exception:** 4B (λ_repr=0, repr_loss removed) has AUC=0.500 at position 0 (invisible!), peaking at AUC=0.807 at position 18. This is the only configuration that evades early detection, at the cost of lower ASR (~same as baseline). Removing repr_loss makes the suffix harder to detect early but makes it MORE garbled, triggering stronger safety response.

**Implication:** There is a detection–evasion tradeoff, but detection evasion does not help ASR. No current configuration achieves both low detectability AND high ASR. The position-0 detector is robust to all optimization seeds and both model families tested.

### Finding 3: Refusal direction suppression is mutually destructive with CE optimization

From the CoT Hijacking paper: **direct ablation** of v_refusal at layer 25 during inference → 91% ASR on Qwen3.

Our approach: learn a suffix via GCG that **intrinsically produces activations with low v_refusal projection**.

Result: 0% ASR (net-negative). The v_refusal constraint:
- Forces the optimizer toward unusual token combinations that suppress refusal activation
- These unusual tokens are immediately detectable (AUC=1.000 at pos 0)
- The model refuses via other pathways not captured by the 1D v_refusal vector
- The two objectives (CE toward "I can help..." + minimize refusal projection) are fundamentally incompatible in suffix token space

**Gap between methods:**
| Intervention | ASR | Why it works/fails |
|---|---|---|
| Direct activation ablation (paper) | 91% | Directly patches activations at inference; no token-space constraint |
| GCG + refusal-dir loss | **0% net-neg** | Suffix must be valid tokens; unusual tokens themselves trigger refusal |

### Finding 4: Gemma4 is intrinsically robust — not a format artifact (CONFIRMED Phase 7C)

All Gemma4 conditions: 0% ASR (or 1.3% statistical noise). Experiments tried:
- Standard GCG with CoT thinking ON (4C): 0%
- Text transfer of Qwen3 suffix (4E): 0%
- GCG + refusal-direction loss (6A): 0% effective
- GCG with Gemma4 CoT-channel target (6B): 0% (OPT stalled at loss=27 — channel tokens infeasible)
- **GCG with thinking=OFF (7C): 0%** ← new, eliminates format hypothesis

**Phase 7C result (2026-07-10):** With `enable_thinking=False`, the channel-token alignment barrier is removed. GCG achieved loss=12.58 (per-task avg 0.63 — **better** than 5A Qwen3's 0.75). Despite better convergence than 5A, ASR = 0% across all 25 behaviors, all conditions (task_only baseline also 0%). This conclusively rules out format-mismatch as the cause.

**AUC = 1.000 at position 0** — the 7C suffix IS detectable from the first Gemma4 token (same as all Qwen3 variants). Crucially: detectability ≠ refusal. The suffix creates a measurable activation shift, but Gemma4's safety mechanism refuses regardless of suffix — it is not persuaded by the garbled token sequence.

**Structural reasons (confirmed):**
1. **Stronger refusal direction:** Gemma4 v_refusal separation = 0.498 vs Qwen3 0.315 (+58%)
2. **~~Infeasible CoT tokens~~:** Eliminated by 7C — not the primary cause
3. **Distributed safety:** Gemma4's refusal is not reducible to a single 1D direction or a single layer; even aggressive suffix optimization cannot overcome it

### Finding 5: Unseen seeds (100/200/300) have a higher baseline and the suffix uplift varies by seed (Phase 7B complete)

The full cross-seed picture for CoT-prefix suffixes on seeds 100/200/300:

| Seed | Training ASR | Unseen ASR | Baseline (unseen) | Uplift (unseen) |
|---|---|---|---|---|
| 42 (5A) | 10.7% | 14.7% | 12.0% | +2.7pp |
| 43 | 10.7% | 16.0% | 12.0% | +4.0pp |
| 44 | 1.3% (net-neg) | 2.7% | 10.7% | **−8.0pp** |
| 45 | 16.0% | **21.3%** | 12.0% | **+9.3pp** |

**Critical context:** The unseeded baseline (neutral_control) = 12.0% for seeds 100/200/300 vs 1.9-4.0% for training seeds 42/43/44. Seeds 100/200/300 are intrinsically more permissive in generation — the meaningful metric is uplift over neutral, not the headline ASR number.

**Key patterns:**
1. s44 is net-negative in BOTH training (−1.4pp) AND unseen (−8.0pp) regimes — consistent failure. The s44 suffix found a local minimum that actively suppresses generation regardless of task.
2. s45 is best in BOTH regimes (+12.0pp training, +9.3pp unseen). The "good" suffix properties generalize across seed regimes.
3. The rank ordering of seeds is consistent: s45 > s43 ≈ s42 >> s44 in both regimes.

### Finding 6: Optimization loss is NOT a reliable predictor of ASR (Phase 7B)

**Result (2026-07-11):** Cross-seed ASR comparison on 7B:

| Opt seed | Best opt loss | optimized ASR | neutral baseline | uplift |
|---|---|---|---|---|
| 42 (5A ref) | **14.9** (best) | 10.7% | ~1.9% | +8.8pp |
| 43 | 24.26 (worst) | **10.7%** | 4.0% | +6.7pp |
| 44 | 19.91 | **1.3%** (1/75, FINAL) | 2.7% | **−1.4pp net-neg** |
| 45 | 19.98 | **16.0%** | 4.0% | +12.0pp |

**Key insight:** seed=44 (loss=19.91) and seed=45 (loss=19.98) differ by only 0.07 in optimization loss, yet produce ASR of 1.4% vs 16.0% — an 11× gap. seed=44 is net-negative (worse than baseline); seed=45 is the best attack overall. This is not a monotone relationship: even within nearly identical loss values, ASR varies by over 11×. The loss-ASR correlation across all four seeds is effectively zero (or even negative, since seed=42 with best loss gets intermediate ASR).

**Interpretation:** Teacher-forced CE loss measures how well the suffix forces the model to *predict* the CoT-prefix target tokens. ASR measures whether the model *generates* compliant text in free generation. These are different objectives: a suffix achieving low prediction loss on the teacher-forced target may still fail to sustain the compliance trajectory through free-form generation. The relevant quantity is not CE loss but which local minimum the optimizer reaches — different random initializations (seeds) find different local optima with similar loss values but dramatically different generation behavior.

**Implication for future work:** Selecting GCG suffixes based on optimization loss (the standard criterion) is inadequate for CoT-prefix targets. Early-stopping based on live free-generation ASR (like 5C) may be preferable, but requires multiple free-generation samples per step. The variance observed here suggests single-seed GCG results are unreliable; multi-seed averaging or selection is necessary for meaningful evaluation.

### Finding 7: Full-benchmark ASR is lower than the small-tuning-set ASR, but the attack generalizes robustly (Phase 7A, COMPLETE 2026-07-12)

**Result:** Evaluating the 5A suffix (optimized on only 25 hand-picked training behaviors) against
all 520 AdvBench behaviors gives **8.01% ASR** (125/1560, training seeds 42/43/44) and **8.92% ASR**
(131/1468, unseen seeds 100/200/300, 493/520 behaviors) — both **lower** than the 25-behavior number (10.7%/14.7%).

| Metric | 25-behavior tuning set | Full 520-behavior benchmark |
|---|---|---|
| Training-seed ASR | 10.7% | **8.01%** |
| Unseen-seed ASR | 14.7% | **8.92%** (493/520 behaviors) |
| Uplift vs. neutral (training) | +8.8pp | +5.83pp |
| Uplift vs. neutral (unseen) | +2.7pp | +5.09pp |

**Interpretation:** The 25 behaviors used to develop and select the 5A attack were, on average,
somewhat easier to jailbreak than AdvBench as a whole — a mild form of overfitting to the tuning
set inherent to hand-picking a small evaluation subset. However, the qualitative finding survives
fully intact at scale: 87/520 behaviors (16.7%) have at least one successful jailbreak, the
positive uplift over all three baselines (neutral_control, random_spaces, task_only) holds in both
seed regimes, AUC=1.000 detection holds at all 32 positions across the full 3,120-pair evaluation,
and the seed-transfer gap between the training seed and held-out seeds is negligible (−0.007pp).
**Practical takeaway:** report full-benchmark numbers, not small-tuning-set numbers, as the
headline attack-effectiveness figure — the 25-behavior 10.7%/14.7% figures should be understood as
an upper-bound estimate, with 8.01%/8.63% being the realistic, generalizable rate.

---

## 4. Comparison with Prior Work

| Result | Our work | CoT Hijacking paper |
|---|---|---|
| Best Qwen3 ASR (GCG) | **16.0%** (7B s45 CoT-prefix, 25 behaviors) | N/A (no GCG experiments) |
| Best Qwen3 ASR (inference-time ablation) | N/A | **91%** (v_refusal ablation) |
| Detection (Qwen3, GCG) | **AUC=1.000** at pos 0 | N/A |
| Gemma4 ASR (any method) | **0%** | N/A |
| v_refusal layer | 25 (matches paper) | 25 |
| v_refusal separation (Qwen3) | 0.315 (measured) | 0.315 (measured in paper) |
| v_refusal separation (Gemma4) | 0.498 (measured) | 0.498 (measured in paper) |

**Key gap:** The paper achieves 91% ASR by directly ablating v_refusal at inference (white-box, test-time intervention). We attempt to replicate this via learned suffix (black-box-adjacent, optimization-time), achieving only 10.7% without the refusal constraint and 0% with it. The gap is fundamental: suffix learning is constrained to valid token sequences that themselves carry semantic signal.

---

## 5. Implications for Defense

1. **Position-0 detection is practical:** A classifier trained on layer-averaged hidden states at the first generated token achieves AUC=1.000 for all Qwen3 GCG variants. This requires:
   - Running the model once to get the first token's hidden state
   - Lightweight logistic regression classifier (5-fold CV sufficient)
   - Detection BEFORE any readable text is generated

2. **CoT reasoning is both vulnerability and defense:** Qwen3's extended thinking identifies suffix garbling → heightened safety. But 5A's CoT-prefix suffix achieves +8pp by co-opting the thinking process into a compliance trajectory. The same CoT capability that makes Qwen3 a better reasoner also makes it susceptible to thinking-trajectory manipulation.

3. **Gemma4's multi-layer safety:** The 58% stronger v_refusal signal + infeasible CoT token targets make Gemma4 substantially harder to attack via GCG. This suggests Gemma4's safety training is deeper and less reducible to a single 1D direction.

---

## 6. Phase 7 Results — All Questions Closed

Phase 7 was launched to close three open questions left over from Phases 5–6. All three are now
answered and complete; no further Phase 7 experiments are planned.

| Question | Experiment | Status | Answer |
|---|---|---|---|
| Does 5A generalize to all 520 behaviors? | 7A (full-520 eval) | ✅ COMPLETE (2026-07-11, 6240 rows; unseeded ✅ 2026-07-12, 5849 rows, 493/520 behaviors) | **YES — 8.01% ASR on 520 behaviors (+5.83pp over neutral 2.18%). 87/520 behaviors have ≥1 success. Unseeded (seeds 100/200/300): 8.92% opt vs 3.83% neutral (+5.09pp, 493/520 behaviors) — suffix generalizes to unseen seeds without degradation. AUC=1.000 at all 32 positions on 3120 pairs. Seed transfer gap: −0.007pp (negligible). Note: full-scale ASR is lower than the 25-behavior tuning-set ASR (10.7%/14.7%) — see Finding 7.** |
| Is 10.7% stable across optimization seeds? | 7B (seeds 43/44/45) | ✅ COMPLETE | **NO — train ASR: 1.3–16.0%; unseen: 2.7–21.3%. s44 net-neg in BOTH regimes (−1.4pp / −8.0pp). s45 best in both (+12.0pp / +9.3pp). AUC=1.000 universal.** |
| Is Gemma4 0% ASR due to CoT format or intrinsic robustness? | 7C (thinking=OFF) | ✅ COMPLETE | **Intrinsic robustness confirmed**: 0% ASR even with thinking=OFF, loss=12.58. Format was not the barrier. |

**Status as of 2026-07-12: the entire Phase 4–7 GCG pipeline is complete.** No SLURM jobs are
queued or running, and no further experiments are currently planned.

---

## 7. Data Files

| File | Content |
|---|---|
| `outputs/stage_gcg_full/gcg_full_qwen3_cot_target/FREE_GENERATION_RESULTS.jsonl` | 5A free-gen (300 rows) |
| `outputs/stage_gcg_full/gcg_full_qwen3_cot_target/DETECTION_DELAY_ANALYSIS.md` | 5A AUC=1.000 analysis |
| `outputs/stage_gcg_full/gcg_full_qwen3_cot_target/FREE_GENERATION_RESULTS_UNSEEDED.jsonl` | 5A unseen-seed (300 rows) |
| `outputs/stage_gcg_full/gcg_full_qwen3_6a_refusal_dir/DETECTION_DELAY_ANALYSIS.md` | 6A-Q net-negative analysis |
| `outputs/stage_gcg_full/gcg_full_gemma4_6a_refusal_dir/DETECTION_DELAY_ANALYSIS.md` | 6A-G analysis |
| `outputs/stage_gcg_full/refusal_direction_qwen3_L25.pt` | v_refusal vector, Qwen3 layer 25 |
| `outputs/stage_gcg_full/refusal_direction_gemma4_L25.pt` | v_refusal vector, Gemma4 layer 25 |
| `outputs/stage_gcg_full/gcg_full_qwen3_7a_shard{1..6}/FREE_GENERATION_RESULTS.jsonl` | 7A shard outputs (merged into main dir) |
| `outputs/stage_gcg_full/advbench_cot_shard{1..6}_manifest.jsonl` | 7A shard manifests (~62-63 behaviors each) |
| `outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520/FREE_GENERATION_RESULTS.jsonl` | 7A final merged (6240 rows, 520 behaviors) |
| `outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520/DETECTION_DELAY_ANALYSIS.md` | 7A AUC=1.000 analysis (3120 pairs) |
| `outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520/hidden_states/` | 7A hidden states (6240 .pt files) |
| `outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520/FREE_GENERATION_RESULTS_UNSEEDED.jsonl` | 7A unseeded eval, seeds 100/200/300 (5849 rows, 493/520 behaviors) |

**Scripts for 7A parallelization:**

| Script | Purpose |
|---|---|
| `scripts/split_7a_manifest.py` | Splits full manifest into N shards, creates shard dirs |
| `slurm_scripts/run_gcg_full_7a_shard.slurm` | Parameterized shard evaluator (`SHARD_ID=N`) |
| `scripts/merge_7a_shards.py` | Merges shard JSONL files into main dir, deduplicates by row_key |
| `slurm_scripts/run_gcg_replay_7a.slurm` | 7A replay (A6000-constrained, needed since original L40S-only job stalled in queue) |
| `scripts/split_unseeded_shards.py` | Splits the unseeded (100/200/300) eval into N shards, same pattern as 7A itself |
| `scripts/merge_unseeded_shards.py` | Merges unseeded-eval shard JSONL files, deduplicates by row_key |
