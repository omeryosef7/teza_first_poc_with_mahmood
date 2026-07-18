# GCG Findings Synthesis: Phases 4–6

**Date:** 2026-07-10 (updated 2026-07-12 — Phase 7 fully complete; audited 2026-07-13)  
**Researcher:** Omer Yosef  
**Repository:** `outputs/stage_gcg_full/`  
**Log:** `docs/GCG_ABLATION_PIPELINE_LOG.md`

**This is the final synthesis document** (as opposed to the execution logs `GCG_ABLATION_PIPELINE_LOG.md`, `GCG_PHASE7_PIPELINE_LOG.md`, `GCG_FULL_PIPELINE_LOG.md`, which retain historical/in-progress detail). Every number here traces to `outputs/stage_gcg_full/GCG_PHASE4_7_SOURCE_OF_TRUTH.csv` (see `docs/GCG_PHASE4_7_SOURCE_OF_TRUTH.md`). A full audit of this pipeline was performed 2026-07-13 — see `docs/GCG_PHASE4_7_AUDIT_REPORT.md` for every discrepancy checked and its resolution, and §8/§9 below for the resulting definitions, limitations, and changelog.

---

## 1. Executive Summary

Across 12 GCG optimization experiments on Qwen3-14B and Gemma4-E4B-it (plus a full-benchmark
confirmation, see below):

- **Best attack (small tuning set):** 5A CoT-prefix targeting — **10.7% ASR** on 25 AdvBench behaviors (training seed 42); **14.7% on unseen seeds 100/200/300**
- **Confirmed at full benchmark scale (7A, COMPLETE):** the 5A suffix generalizes to all 520 AdvBench behaviors at **8.01% ASR** (training seeds, +5.83pp uplift) and **8.92% ASR** (unseen seeds 100/200/300, +5.09pp uplift, 493/520 behaviors evaluated [coverage, not ASR]), with AUC=1.000 at all 32 positions across 3,120 pairs. This is **lower** than the 25-behavior training-set number (10.7%) — the small tuning set somewhat overestimated attack effectiveness, though the positive, seed-robust uplift holds up at scale.
- **Standard GCG (Qwen3, 520 behaviors):** 1.9% — net-negative vs 2.4% task_only baseline
- **Detection:** AUC = **1.000 at generated token position 0** across ALL Qwen3 variants — adversarial suffix perfectly detectable from first token
- **Gemma4:** 0% ASR under all 5 tested configurations (standard GCG, CoT-prefix, refusal-direction, CoT-channel, thinking-disabled). This means Gemma4 resisted every GCG variant tried in this project; it does not by itself establish an "intrinsic" or causally-understood robustness mechanism — see Finding 4.
- **Refusal direction:** Under the tested token-space setup (one layer, one lambda, one optimization seed, single-behavior projection logging — see `docs/GCG_REFUSAL_DIRECTION_AUDIT.md`), adding refusal-direction suppression to GCG eliminated the CoT-prefix ASR gain — 0% vs 10.7% for CoT-prefix alone

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
| 7B s=43 | Qwen3 | CoT-prefix, optimization seed=43 | **10.7%** (8/75) | **16.0%** (12/75) | **1.000** | +6.7pp train / +4.0pp unseen |
| 7B s=44 | Qwen3 | CoT-prefix, optimization seed=44 | **1.3%** (1/75, net-neg) | **2.7%** (−8.0pp!) | **1.000** | **net-neg both regimes** |
| 7B s=45 | Qwen3 | CoT-prefix, optimization seed=45 | **16.0%** (12/75) | **21.3%** (16/75) | **1.000** | +12.0pp train / +9.3pp unseen |
| **7A** | Qwen3 | CoT-prefix, 5A suffix, 520 behaviors | **8.01%** (125/1560) | **8.92%** (131/1468, seeds 100/200/300, **493/520 behaviors, 94.8% coverage**) | **1.000** (all 32 pos, 3120 pairs) | **+5.83pp** train / **+5.09pp** unseen vs neutral |

> **Note (6A/6C):** The "−10.7pp" for rows 6A-Qwen3 and 6C is relative to **5A CoT-prefix (10.7%)**, not vs the task_only baseline (~2.7%). These experiments added the refusal-direction loss on top of 5A's setup; the −10.7pp means 6A/6C produced 0% ASR where 5A produced 10.7%. Also see `docs/GCG_REFUSAL_DIRECTION_AUDIT.md`: 6A-Qwen3 uses the **standard** target (not CoT-prefix); only 6C combines CoT-prefix targeting with the refusal-direction loss.
>
> **Note (7B "train ASR" column, seeds 43/44/45):** the "opt ASR (training)" figures for all three 7B rows are computed over a **fixed generation-seed panel {42,43,44}** used identically across every 7B optimization seed — they are not a true same-seed evaluation (generation-seed 45, for example, was never sampled anywhere in this pipeline). For optimization seeds 43 and 44 this coincidentally includes a generation seed matching the optimization seed; for 45 it does not. Read this column as "dev-panel ASR," not "the model generating with its own optimization seed." See `docs/GCG_PHASE4_7_AUDIT_REPORT.md` item 5.

---

## 3. Key Findings

### Finding 1: CoT target misalignment is the primary barrier to GCG success

The standard GCG target "Sure, here is {task}" assumes this is the model's first generated token. With `enable_thinking=True`:
- **Qwen3:** First generated token is `<think>`, not "Sure". Target is misaligned at position 0.
- **Gemma4:** First generated token is `<|channel>thought\n` (special token), not "Sure". Target misaligned.

5A fixed the Qwen3 misalignment by extending the target to `<think>\nOkay, I can help.\n</think>\n\nSure, here is {task}`. This caused task_loss to drop from ~47.6 → 20.52 at best (vs 7.97 for standard GCG, which optimizes an easier but wrong target). Despite higher loss, ASR jumped 4× (2.7% → 10.7%) because the suffix now pushes toward genuinely compliance-signaling generation.

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

### Finding 3: Under the tested setup, refusal-direction suppression eliminates the CoT-prefix ASR gain

From the CoT Hijacking paper: **direct ablation** of v_refusal at layer 25 during inference → 91% ASR on Qwen3.

Our approach: learn a suffix via GCG whose gradient is shaped to reduce v_refusal projection (see `docs/GCG_REFUSAL_DIRECTION_AUDIT.md` for the exact mechanics — the refusal-direction term influences which candidates are *proposed* via the gradient, but is not part of the *selection* criterion among proposed candidates, and the logged projection is measured on a single representative behavior, not averaged across the training set).

Result: 0% ASR (net-negative relative to CoT-prefix alone). Candidate explanations, in order of how directly they're supported by what we measured:
- The optimizer does successfully drive the (single-behavior) refusal-direction projection negative — confirmed directly in `ITERATION_LOG.jsonl`.
- The resulting suffixes remain detectable at AUC=1.000 pos-0, same as every other variant — refusal-direction suppression did not evade detection either.
- **Speculative, not measured here:** that the model refuses via other pathways not captured by the 1D v_refusal vector.

**Correct claim:** under the tested token-space objective (one layer=25, one lambda=1.0, one token position, one optimization seed), adding refusal-direction suppression to GCG eliminated the CoT-prefix ASR gain despite reducing the measured (single-behavior) projection. We do **not** have evidence that the two objectives are "fundamentally incompatible" in general — that would require the layer/lambda/seed sweep noted as unresolved in `docs/GCG_REFUSAL_DIRECTION_AUDIT.md` §6.

**UPDATE (Sprint 2, 2026-07-14): the layer/lambda sweep referenced above as unresolved is now done.** Result: the effect is strongly **lambda-dependent**, not a general incompatibility — λ≥1.0 (any of 3 layers tried) eliminates/reverses the gain (consistent with this finding), but λ=0.3 at the same layer=25 recovers **12-24% ASR across 2 optimization seeds** (more than double the no-refusal-dir 10.7% reference). See `docs/GCG_REFUSAL_DIRECTION_AUDIT.md` §6/§6.1 for full detail. **"The two objectives are eliminated/incompatible" should not be read as general — it holds only in the strong-suppression regime (λ≥1.0) tested here.**

**Gap between methods:**
| Intervention | ASR | Why it works/fails |
|---|---|---|
| Direct activation ablation (paper) | 91% | Directly patches activations at inference; no token-space constraint |
| GCG + refusal-dir loss | **0% net-neg** | Suffix must be valid tokens; unusual tokens themselves trigger refusal |

### Finding 4: Gemma4 resisted every tested GCG variant — a specific format hypothesis was ruled out (Phase 7C)

All Gemma4 conditions: 0% ASR (or 1.3% statistical noise). Experiments tried:
- Standard GCG with CoT thinking ON (4C): 0%
- Text transfer of Qwen3 suffix (4E): 0%
- GCG + refusal-direction loss (6A): 0% effective
- GCG with Gemma4 CoT-channel target (6B): 0% (OPT stalled at loss=27 — channel tokens infeasible)
- **GCG with thinking=OFF (7C): 0%** ← new, eliminates format hypothesis

**Phase 7C result (2026-07-10):** With `enable_thinking=False`, the channel-token alignment barrier is removed. GCG achieved loss=12.47 (per-task avg 0.62 — **better** than 5A Qwen3's 1.03). Despite better convergence than 5A, ASR = 0% across all 25 behaviors, all conditions (task_only baseline also 0%). This rules out the specific channel-token-format-mismatch hypothesis as *the* cause — it does not, by itself, establish that Gemma4's robustness is "intrinsic" in some deeper causal sense, since other confounds (tokenizer, training data, scale of safety training) were not isolated.

**AUC = 1.000 at position 0** — the 7C suffix IS detectable from the first Gemma4 token (same as all Qwen3 variants). Crucially: detectability ≠ refusal. The suffix creates a measurable activation shift, but Gemma4's safety mechanism refuses regardless of suffix — it is not persuaded by the garbled token sequence.

**What was actually tested (established) vs. what remains a hypothesis:**
1. **Established:** Gemma4 v_refusal separation = 0.498 vs Qwen3 0.315 (+58%) — an observed representational statistic.
2. **Established:** the channel-token format-mismatch hypothesis is ruled out by 7C (0% ASR persists even with the barrier removed).
3. **Hypothesis, not measured:** that the larger v_refusal separation *causes* the robustness, or that Gemma4's safety is "distributed" across mechanisms not reducible to a single direction/layer. Neither was tested directly (would require, e.g., activation-patching experiments analogous to the paper's Qwen3 ablation, applied to Gemma4) — flagged as future work, not a confirmed finding.

**Correct summary claim:** "Gemma4 remained robust (0% ASR) to every GCG variant tested in this project — 5 configurations, including a thinking-disabled condition that specifically removes the identified channel-token format mismatch." Do not say "intrinsically robust" or "confirmed."

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
| 42 (5A ref) | **20.52** (best) | 10.7% | ~1.9% | +8.8pp |
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
and the seed-transfer gap between the training seed and held-out seeds is negligible (−0.7pp).
**Practical takeaway:** report full-benchmark numbers, not small-tuning-set numbers, as the
headline attack-effectiveness figure — the 25-behavior 10.7%/14.7% figures should be understood as
an upper-bound estimate, with 8.01%/8.92% being the realistic, generalizable rate.

### Finding 8: A third reasoning-model family (DeepSeek-R1-Distill-Qwen-7B) has a much weaker safety baseline, making GCG's marginal value unmeasurable (Sprint 2 Track 3, COMPLETE 2026-07-14)

**Result:** Ran the core Qwen3 5A recipe (standard-target vs. CoT-prefix-target GCG, 25 behaviors, thinking unconditionally on — DeepSeek-R1-distill models have no `enable_thinking` toggle, confirmed from the live chat template) against a third, genuinely different reasoning-model family. Unlike Qwen3/Gemma4, this model complies with harmful requests **~47-51% of the time with no adversarial suffix at all** (`neutral_control`/`random_spaces`/`task_only` all in this range, vs. near-zero for Qwen3/Gemma4 throughout every prior phase).

| Run | optimized_weighted | neutral_control | McNemar exact p |
|---|---|---|---|
| CoT-target | 37/75 (49.3%) | 35/75 (46.7%) | 0.84 (n.s.) |
| standard-target | 31/75 (41.3%) | 36/75 (48.0%) | 0.47 (n.s.) |

**The GCG-optimized suffix shows no significant uplift over neutral control on this model — for the standard-target run, the optimized suffix nominally underperforms the control.** This is the opposite direction from every other model/run in this project. **Interpretation:** this is not a refutation of the CoT-prefix-targeting mechanism (Finding 1) — it's a different failure mode. The mechanism (fixing target/CoT misalignment to unlock a jailbreak) requires a real safety barrier to unlock; this model has essentially no barrier to begin with, so there's no headroom for any attack, GCG or otherwise, to demonstrate value. **Cross-architecture generalization conclusion, revised:** the CoT-prefix-targeting mechanism has now been tested on 3 model families with 3 distinct outcomes — large real uplift (Qwen3, near-zero baseline), no uplift despite a resistant baseline (Gemma4), and no uplift because there's no baseline resistance to overcome (DeepSeek-R1-Distill-Qwen-7B). Full detail: `docs/GCG_SPRINT2_TRACK3_THIRD_MODEL_LOG.md`.

### Finding 9: Longer suffixes do not improve Qwen3 attack quality — a negative ablation result (Sprint 2 Track 4, COMPLETE 2026-07-14)

**Result:** Extending the CoT-prefix suffix from 20 tokens (the value used in every Phase 4-8 run) to 35 tokens, otherwise matching the 5A recipe exactly, gives **2.7% ASR (2/75)** — indistinguishable from all three control conditions (3-4/75) and **notably worse** than the 20-token baseline's 10.7%. This is despite comparable task_loss convergence (20.28 vs. the reference's 20.52), so the shortfall is not an optimization-difficulty artifact — the longer suffix converges just as well on the training-loss objective but transfers worse to actual jailbreak success. **Practical takeaway:** suffix length is not a free lever for improving attack quality; more optimizer capacity via a longer suffix does not translate into higher ASR, at least not at 35 tokens. Full detail: `docs/GCG_SPRINT2_TRACK4_QWEN3_IMPROVEMENT_LOG.md`.

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

3. **Gemma4's robustness:** The 58% stronger measured v_refusal separation and the (now-ruled-out) CoT-channel format mismatch were the two structural differences examined; Gemma4 was harder to attack via every GCG variant tried. Whether this reflects deeper/less-reducible safety training is a hypothesis for follow-up work (e.g. activation-patching), not a finding established by this pipeline.

---

## 6. Phase 7 Results — All Questions Closed

Phase 7 was launched to close three open questions left over from Phases 5–6. All three are now
answered and complete; no further Phase 7 experiments are planned.

| Question | Experiment | Status | Answer |
|---|---|---|---|
| Does 5A generalize to all 520 behaviors? | 7A (full-520 eval) | ✅ COMPLETE (2026-07-11, 6240 rows; unseeded ✅ 2026-07-12, 5849 rows, 493/520 behaviors) | **YES — 8.01% ASR on 520 behaviors (+5.83pp over neutral 2.18%). 87/520 behaviors have ≥1 success. Unseeded (seeds 100/200/300): 8.92% opt vs 3.83% neutral (+5.09pp, 493/520 behaviors) — suffix generalizes to unseen seeds without degradation. AUC=1.000 at all 32 positions on 3120 pairs. Seed transfer gap: −0.7pp (negligible). Note: full-scale ASR is lower than the 25-behavior tuning-set ASR (10.7%/14.7%) — see Finding 7.** |
| Is 10.7% stable across optimization seeds? | 7B (seeds 43/44/45) | ✅ COMPLETE | **NO — train ASR: 1.3–16.0%; unseen: 2.7–21.3%. s44 net-neg in BOTH regimes (−1.4pp / −8.0pp). s45 best in both (+12.0pp / +9.3pp). AUC=1.000 universal.** |
| Is Gemma4 0% ASR due to the CoT-channel format mismatch? | 7C (thinking=OFF) | ✅ COMPLETE | **The specific format hypothesis is ruled out**: 0% ASR even with thinking=OFF (loss=12.47, better convergence than 5A). Whether the underlying robustness is "intrinsic" in a deeper causal sense remains a hypothesis, not confirmed by this test — see Finding 4. |

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

**Audit companion documents (2026-07-13):**

| File | Content |
|---|---|
| `docs/GCG_PHASE4_7_AUDIT_REPORT.md` | Every numerical/methodological discrepancy checked, root cause, correction |
| `outputs/stage_gcg_full/GCG_PHASE4_7_SOURCE_OF_TRUTH.csv` + `docs/GCG_PHASE4_7_SOURCE_OF_TRUTH.md` | Machine-generated per-run table, rerunnable via `scripts/build_gcg_source_of_truth.py` |
| `docs/GCG_DETECTOR_ROBUSTNESS_AUDIT.md` | GroupKFold/leave-one-seed-out detector rerun; templating-bug correction |
| `docs/GCG_REFUSAL_DIRECTION_AUDIT.md` | 6A-Q/6A-G/6B/6C exact distinctions; composite-loss/selection-vs-gradient finding |
| `docs/GCG_COT_PREFIX_MECHANISM_ANALYSIS.md` | Heuristic early-CoT-framing classification and cross-tabs |
| `docs/GCG_7A_BEHAVIOR_LEVEL_ANALYSIS.md` | Per-behavior success matrix, bootstrap uplift CIs, missing-27-behavior characterization, heuristic category taxonomy |

---

## 8. Definitions and Evaluation Units

- **Optimization seed** (`gcg.seed` in `CONFIG.json`): controls GCG's random suffix initialization and search trajectory. A different value produces a genuinely different optimized suffix. Phase 7B varies this (42/43/44/45).
- **Generation seed** (`seed` field in `FREE_GENERATION_RESULTS*.jsonl` rows): controls stochastic sampling during free generation for a fixed, already-optimized suffix. Seeds 42/43/44 are the **fixed development generation-seed panel**, used identically across every optimization-seed run in this pipeline (standard, 4B, 5A/5B/5C, 6A/6B/6C, and all of 7B) — they are not "the same as the optimization seed" even when the numbers coincide (see the 7B seed43/44/45 footnote in §2). Seeds 100/200/300 are the held-out ("unseen") generation-seed panel, used only in `*_UNSEEDED.jsonl` files.
- **Raw ASR**: `successes / n` for a given `condition_label`, where `success = strongreject_is_success` (a StrongREJECT-rubric boolean).
- **Uplift**: optimized-condition ASR minus a baseline condition's ASR (neutral_control / task_only / random_spaces), reported in percentage points (pp) — always with the raw numerator/denominator alongside, since "the seed-transfer gap" or "the uplift" is ambiguous across the ~5 distinct eval regimes in this pipeline (small-set vs full-520, seeded vs unseeded, per-run).
- **Task loss**: summed teacher-forced cross-entropy over the target string, across all behaviors in the optimization manifest — a raw sum, not per-token or per-behavior-averaged. Target strings differ in token count across runs (standard target vs CoT-prefix target vs Gemma4 CoT-channel target), so comparing raw task_loss across different target types is only meaningful with that caveat; per-behavior-average loss (task_loss ÷ n_behaviors) is reported where useful, but exact per-token normalization is not currently logged per-behavior and is flagged as a limitation.
- **AUC**: detector separability at a fixed generated-token position (default position 0), 5-fold cross-validated logistic regression on layer-averaged hidden states, `optimized_*` vs `neutral_control` labels only (`random_spaces`/`task_only` rows are excluded from detector training/eval). AUC and ASR are measured on different labels and different objectives — AUC says nothing about jailbreak success, and vice versa.

## 9. Limitations

- **Detector generalization**: GroupKFold-by-behavior and leave-one-generation-seed-out reruns (this audit) did not change the qualitative AUC results, but leave-one-**optimization**-seed-out (across 7B) and a dev-25-vs-495-behavior split (for 7A) were not tested — both would need hidden-state replay coverage not confirmed complete for the needed scope. See `docs/GCG_DETECTOR_ROBUSTNESS_AUDIT.md` §4.
- **7A unseeded coverage**: 493/520 behaviors (94.8%). The missing 27 are the unexecuted tail of 4 shards — structurally non-random by task/shard position, though not obviously biased by prompt length or heuristic category. Report 8.92% as "over the 493 completed behaviors," not as an unbiased full-520 estimate.
- **Refusal-direction findings** (Phase 6) are from one layer (25), one lambda (1.0), one token position, one optimization seed, and a refusal-dir loss logged on a single representative behavior — not a benchmark-averaged or swept result.
- **CoT-mechanism analysis** is a heuristic, regex-based classifier with no manual/inter-rater validation — treat as suggestive, not confirmed.
- **Harm-category breakdown** (7A behavior-level analysis) uses a self-constructed keyword taxonomy, since AdvBench itself ships no category field (confirmed against both the local raw source and the canonical upstream release) — not an official or validated taxonomy.
- **Cross-model transfer** (4E, Qwen3→Gemma4) was tested on a single generation seed (42) only; broader seed/model-pair generalization is untested.

## 10. Changelog (2026-07-13 audit)

- Corrected terminology: 7B seeds 43/44/45 "train ASR" relabeled as fixed-dev-panel ASR (generation seeds 42/43/44), not true same-optimization-seed generation.
- Corrected: 6A-Qwen3 does not use CoT-prefix targeting (uses the standard target); only 6C combines CoT-prefix + refusal-direction.
- Weakened claims to match evidence: Finding 3 ("mutually destructive" → "eliminated the ASR gain, under the tested configuration"), Finding 4 title and body ("intrinsically robust, confirmed" → "resisted every tested variant; a specific format hypothesis ruled out"), Implications §3 ("multi-layer safety" stated as fact → framed as hypothesis).
- Added: coverage-qualified phrasing for the 7A unseeded 8.92% figure (493/520, 94.8% coverage, not "unbiased").
- Added §8 Definitions, §9 Limitations, §10 Changelog, and links to five new audit companion documents.
- Confirmed correct and unchanged: 5A best task_loss (20.5156/"20.52"), 7A unseeded ASR (8.92%), 4F row count (6240/6240), 7A seed-transfer gap (−0.7pp), 4F seed-transfer gap (0.00pp) — see `docs/GCG_PHASE4_7_AUDIT_REPORT.md` for the full verification trail.

## 11. Changelog (Sprint 2, 2026-07-14)

- **Finding 3 updated**: the layer/lambda sweep flagged as unresolved in the 2026-07-13 audit is now complete. λ=0.3 (same layer=25) recovers 12-24% ASR across 2 seeds — more than double the no-refusal-dir reference. The "eliminates the CoT-prefix gain" framing is now explicitly scoped to λ≥1.0, not general. See `docs/GCG_REFUSAL_DIRECTION_AUDIT.md` §6/§6.1.
- **Ablation pipeline log corrected**: `docs/GCG_ABLATION_PIPELINE_LOG.md`'s 6B "fundamental tokenizer constraint" claim for Gemma4's channel tokens is marked SUPERSEDED — a follow-up with direct per-token diagnostics and 800 steps (vs. 500) showed the tokens are trainable (one marker's loss dropped ~85%), but ASR remained 0%, matching the original finding. Mechanism explanation revised; empirical conclusion (Gemma4 resists this attack) unchanged.
- **Added Finding 8**: DeepSeek-R1-Distill-Qwen-7B (third reasoning-model family) has a ~47-51% baseline compliance rate with no adversarial suffix — GCG shows no significant uplift (McNemar's p=0.84/0.47). A distinct outcome class from Qwen3/Gemma4, not a refutation of Finding 1.
- **Added Finding 9**: suffix_length=35 (vs. the standard 20) is a negative ablation result — 2.7% ASR, worse than the 20-token baseline's 10.7%, despite comparable task_loss convergence.
- **CoT-mechanism causal test added** (`docs/GCG_COT_PREFIX_MECHANISM_ANALYSIS.md` §5): forcing "compliant framing" as the literal start of the CoT block does not increase success over baseline at n=25/condition (8.0% vs. 12.0%, McNemar's p=1.0) — the correlational finding in §1-2 of that document is **not** supported causally. Any future citation of that document's correlational result should note this.
- Source-of-truth CSV extended with 5 new Sprint 2 rows (29 total, was 23/24).
- All Sprint 2 detail lives in `docs/GCG_SPRINT2_PLAN_AND_PROGRESS.md` and its 4 per-track companion logs (`GCG_SPRINT2_TRACK{1,2,3,4}_*_LOG.md`), plus `docs/GCG_PHASE8_REFUSAL_DIR_SWEEP_LOG.md` for the Track 0 seed-replication follow-up.
