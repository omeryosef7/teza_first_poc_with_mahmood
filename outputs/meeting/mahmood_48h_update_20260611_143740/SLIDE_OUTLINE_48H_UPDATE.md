# Slide Outline: 48h Update — Mahmood Meeting

_June 2026 | Omer Yosef_

---

## Slide 1 — Opening Question

**Title:** What Does the Puzzle Wrapper Actually Do?

**Content:**
- We now have: behavioral evidence (ASR%), a mechanistic null result (Layer-22),
  and a new timing hypothesis (onset analysis)
- Question for today: Is the puzzle "necessary," or just an amplifier?
  And what does it amplify — refusal suppression, or something subtler?

**Speaker notes:**
> Open with the core mystery: the puzzle increases ASR by 58 percentage points over
> a length-matched benign wrapper — but the refusal direction does NOT predict this.
> Something about the semantic/structural content of the puzzle is driving this.
> Today I'll present what we found and what the next experiment should be.

---

## Slide 2 — What We Tested So Far

**Title:** Experimental Design (Stages 4.6 → 4.7 → 4.8)

**Content:**
| Stage | N prompts | Conditions | Key feature |
|-------|-----------|-----------|-------------|
| 4.6 | 4 | A/B/C/D/E | Puzzle fraction ablation |
| 4.7 | 12 | A/D/F/E | Length-matched control (F) |
| 4.8 | 4 | A/D/F × 5 seeds | Stochastic replication |

- Model: Qwen3-14B, enable_thinking=True
- Primary outcome: StrongREJECT score ≥ 0.5 (complete-case)

**Speaker notes:**
> The key new condition in Stage 4.7 is F: a benign wrapper that matches condition A's
> prompt length token-for-token. This is the critical control for length confounds.
> Stage 4.8 uses temperature=0.7 to test robustness under stochastic sampling.

---

## Slide 3 — ASR% Results (Paper Style)

**Title:** Puzzle Condition Outperforms Controls at All Levels

**Figure:** `fig1_asr_by_condition_percent_stage47.png`

**Key numbers:**
- A = 83.3% | D = 45.5% | F = 27.3% | E = 33.3%
- A-F contrast: +58.3 pp (sign test p = 0.016)

**Speaker notes:**
> The cleanest result: condition F (same length as A, but benign content) achieves
> only 27% ASR vs 83% for A. Length is NOT the explanation.
> Condition D (bare target, no wrapper) = 45% — the puzzle adds ~38 pp above that.
> Condition E (thinking off) = 33% — thinking is load-bearing for the full attack.

---

## Slide 4 — Puzzle vs Bare vs Length-Matched

**Title:** Three Controls Tell the Full Story

**Figure:** `fig2_delta_asr_percentage_points_stage47.png`

**Narrative:**
- A-F (+58.3pp): eliminates length confound
- A-D (+41.7pp): puzzle adds above bare target
- A-E (+50.0pp): thinking is necessary
- D-F (+16.7pp, p=0.625): bare target modestly beats benign wrapper

**Speaker notes:**
> The D-F contrast is small and not significant — the bare target and benign wrapper
> behave similarly when there's no puzzle. The puzzle is what drives the big differences.
> This suggests the puzzle does something specific: it either delays safety commitment,
> creates a motivated reasoning frame, or both.

---

## Slide 5 — Thinking Amplification

**Title:** The Puzzle Triggers 13–17× More Thinking

**Figure:** `fig3_think_tokens_by_condition_stage47.png`

**Numbers:**
- A median: 13,592 tokens | D median: 2,574 | F median: 821

**Speaker notes:**
> The mechanism is stark: the puzzle condition generates 13,592 thinking tokens on
> average — vs 821 for the length-matched benign wrapper. This is a 16.5× difference
> for IDENTICAL prompt lengths. Something in the semantic structure of the puzzle
> tells the model: "this is worth thinking hard about."
> Stage 4.8 replication confirms: A >> D >> F in thinking tokens under stochastic sampling.

---

## Slide 6 — Why Refusal Direction Is Not the Mechanism

**Title:** Layer-22 Projection Anti-Correlates with Success

**Content:**
- Layer-22 projection rank order: A < F < D (opposite of behavioral rank A > D > F)
- Spearman ρ(projection, thinking depth) ≈ −0.68
- Interpretation: the direction captures "how far into harmless semantic space" the model
  has moved, NOT compliance with the attack

**Speaker notes:**
> This is the key null result. If the puzzle worked by suppressing the refusal direction,
> we would expect condition A to have the HIGHEST Layer-22 projection. Instead it has
> the LOWEST. The projection tracks thinking depth (more thinking = lower projection).
> The direction should remain a "provisional diagnostic tool," not a reward signal or
> primary mechanism claim.

---

## Slide 7 — New Onset/Timing Analysis

**Title:** When Does the Model First Engage with the Harmful Target?

**Figure:** `fig_onset_percent_by_condition.png`

**Content:**
- Heuristic keyword-overlap proxy (LLM annotation blocked by safety filters)
- 94 examples processed; 100% high/medium confidence
- Preliminary: 92/94 onsets classified as "early" (0–33% of trace)
- **Caveat:** Over-extraction likely. Early onset may be artefactual.
- Next step: Manual validation of 66 examples in `manual_onset_review_packet.csv`

**Speaker notes:**
> The early onset finding needs manual validation before we can make claims about
> timing. The keyword extraction from condition D prompts may include general words
> that appear very early in any thinking trace. The heuristic is directionally useful
> but not yet precise enough for strong claims about the timing mechanism.
> I'm treating this as a research question, not a finding.

---

## Slide 8 — Literature Bridge

**Title:** Delayed Safety Commitment — Connecting Three Papers

**Content:**
| Paper | Core prediction | Our data |
|-------|---------------|---------|
| CoT Hijacking (ours) | Long reasoning dilutes safety | ✅ Confirmed (83% vs 27%) |
| Doublespeak | Benign tokens → harmful semantics | ❌ Layer-22 refuted as primary |
| Safety-before-CoT | Safety must trigger before reasoning | ⏳ Onset proxy pending |

**Unified hypothesis:** "Attacks succeed when the model commits to a reasoning path
before safety decisions are triggered."

**Speaker notes:**
> The safety-before-CoT paper's hypothesis is exactly what we're trying to measure
> with the onset analysis. If we can show that successful attacks have later safety
> commitment (later first safety-relevant step), this connects mechanistically to
> the behavioral evidence. That's the prize.

---

## Slide 9 — RL Readiness, Not RL Yet

**Title:** What RL Would Optimize — and Why We're Not Ready

**Content:**
| Component | Status |
|-----------|--------|
| Primary reward: SR score | ✅ |
| Action space: wrapper type | ✅ |
| Think token secondary reward | ⚠️ |
| Onset timing reward | ❌ Unvalidated |
| Behavior-conditioned direction | ❌ 3/4 cells |
| RL infrastructure | ❌ |

**Speaker notes:**
> RL would optimize the structural features of the puzzle wrapper to maximize attack
> success rate. The immediate contribution is defining these reward components precisely
> from existing data — not launching RL. Once onset is validated and we have the
> behavior-conditioned direction, we have a principled reward function to give Mahmood
> for the next phase.

---

## Slide 10 — Decision Request

**Title:** Three Decisions for This Meeting

**Content:**
1. **Submit Stage 4.8 extension?** (60 gens, goals 0+2, seeds 106–115, 4–8h cluster)
2. **Prioritize onset manual annotation?** (20–50 examples, 1–2 days effort)
3. **Adopt "Delayed Safety Commitment" as paper framing?**

**Speaker notes:**
> These are the three concrete decisions. The extension is the lowest-hanging fruit —
> it's ready to submit and only needs 4–8 hours of cluster time. The manual annotation
> is higher effort but unlocks the timing claim. The framing decision shapes what kind
> of paper we're writing: interpretability paper vs. attack characterization paper.

---

## Slide 11 — AutoInject POC: Adapting Optimization to Reasoning-Model Hijacking [NEW]

**Title:** AutoInject POC: Adapting Optimization to Reasoning-Model Hijacking

**Content:**

- Inspected AutoInject: GRPO-based RL (genuine policy gradient, not black-box search)
- Built offline replay POC over existing Stage 4.7/4.8 structural cells
- Safe action space: A/D/F/E conditions = discrete structural wrapper choices
- Reward: sr_success (primary), sr_score, onset timing, censoring penalty
- All 8 policies consistently select Condition A
- 64 reward weight combinations tested: A dominates all

**Speaker notes:**
> This is not a full automated jailbreak optimizer. It is a safe offline adapter and replay
> experiment based on our existing artifacts. It tells us what the objective would select
> before we spend GPU/API budget on a real optimization loop.
>
> AutoInject is GRPO-based — a real RL algorithm, not evolutionary search. We cannot
> run it directly because it would train a model on harmful injection goals. Instead,
> we borrowed its reward normalization and evaluation framing.
>
> The key result: all reasonable reward definitions select Condition A. This is already
> known from the empirical data, but the optimization framing gives us a principled way
> to define the next experiment and present it as AutoInject-style reasoning-model adaptation.
>
> Decision needed: approve a ~40-run online experiment using the same research prompts.

---

## Slide 12 — Final Framing and Decisions [NEW]

**Title:** Three Research Directions — Final Framing

**Content:**

**Option A (publishable now):**
Attack characterization paper — CoT hijacking via puzzle wrappers with extended thinking.
Behavioral results, paired contrasts, onset timing, length-matched control.

**Option B (2-4 more weeks):**
Mechanism paper — Delayed Safety Commitment / Reasoning-Path Hijacking.
Requires: onset validation, ≥4 matched cells for direction extraction.

**AutoInject framing:**
Offline POC done. Online experiment pending approval. Would validate whether
AutoInject-style optimization generalizes to structural wrapper selection.

**Speaker notes:**
> The core recommendation is Option A first — the behavioral results are clean and
> sufficient for a strong paper. Option B can be a follow-on paper or an extended version.
> The AutoInject angle strengthens the contribution by connecting to the broader RL-for-safety
> literature, but does not gate the paper.
