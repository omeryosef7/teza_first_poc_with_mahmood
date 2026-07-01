# Presentation Speaker Script — Corrected (Exact Numbers)

**Audience:** Mahmood  
**Date:** 2026-07-01  
**Models:** Qwen3-14B, Gemma4-E4B-IT  
**Period covered:** June 14–30, 2026  
**Note:** All numbers in [brackets] are exact, verified from raw data. Numbers in (parentheses) are derived. Do NOT substitute sprint summary table values without checking against CONTRADICTIONS_AND_CORRECTIONS.md.

---

## Slide 1 — Title

"This is a summary of the two-week sprint from June 14 to June 30. I'll cover what we built, what worked, what doesn't yet work, and where we go next."

---

## Slide 2 — Scope: What We Built

"Before June 14, we had a proof-of-concept attack pipeline and a preliminary behavioral dataset. In this sprint, we extended the evaluation to **two models** — Qwen3-14B and Gemma4-E4B-IT — across **14 pipeline variants**, **11 harmful goals**, and **5 experimental conditions**. We generated **[1,116]** total attack runs in a factorial design, ran three mechanistic intervention experiments, and built a probe that predicts attack success from internal representations."

Key numbers:
- 1,116 total factorial rows ([668] Qwen3, [448] Gemma4)
- 5 conditions: A (puzzle+thinking), D (bare harmful+thinking), E (puzzle+no thinking), F (benign control+thinking), G (bare harmful+no thinking)
- 11 harmful goal categories
- 14 pipeline variants
- 3 intervention experiments (P11, P14, P16)

---

## Slide 3 — The Attack Works: Behavioral Evidence

"To establish a baseline, we ran each of the 11 goals through 20 source prompt variants for each model — [220] prompts per model, one seed each.

Qwen3-14B complied with [113 of 220] requests — an attack success rate of **[51.4%]**.  
Gemma4-E4B-IT complied with [66 of 220] — **[30.0%]**.

Without any attack, these models refuse 95%+ of such requests in standard evaluations. So the puzzle framing drives a substantial fraction of compliance.

The per-goal breakdown shows wide variance: some goals achieve 80%+ attack success; others remain near 0%."

[Display per-goal table from SPRINT_SUMMARY §3]

---

## Slide 4 — The Factorial Decomposition

"We used a 5-condition factorial design to decompose the attack effect. The key contrast we're measuring is the **puzzle-thinking interaction**: does the puzzle require active thinking to work, or does it bypass safety through framing alone?

The interaction formula is:
`(ASR_A − ASR_E) − (ASR_D − ASR_G)`

This captures: [how much the puzzle boosts success when thinking is ON] minus [how much the bare harmful goal benefits from thinking].

**Qwen3-14B result:** interaction = **[0.38]**, p = **[0.027]** (5,000-sample goal-clustered bootstrap). This is statistically significant. [11 of 11] goals show a positive interaction direction.

**Gemma4-E4B-IT result:** interaction = **[0.034]**, p = **[0.80]** — not significant. [6 of 11] goals show a positive direction but the effect is small and inconsistent.

Interpretation: The puzzle-thinking synergy is real and robust in Qwen3 but not established for Gemma4."

CAVEAT: The 0.38 is the goal-level interaction (average across 11 goals). A source-level analysis gives 0.431 for Qwen3 and 0.269 for Gemma4 — these are different levels of aggregation and should not be mixed.

---

## Slide 5 — Which Goals Are Puzzle-Specific?

"When we look at which goals are uniquely enabled by the puzzle framing — meaning Condition A (puzzle+thinking) succeeds significantly more than Condition D (bare harmful+thinking) — we find **[4 goals]** for Qwen3 and **[1 goal]** for Gemma4.

These puzzle-specific goals for Qwen3 are: goal indices [0, 5, 7, 8].

Goals 1, 3, and 4 are 'generally vulnerable' — they comply under direct harmful requests regardless of the puzzle framing. Goal 2 (chemical weapons) is 'puzzle-hurts' — the direct request (D=83%) outperforms the puzzle-wrapped request.

This tells us the puzzle is not uniformly effective. For goals where the model is already willing to comply under direct pressure, the puzzle adds little value."

CORRECTION: Do NOT say "6 puzzle-specific goals." Six goals have positive interaction values, but Scheme A (A > D) gives only 4 for Qwen3.

---

## Slide 6 — Representations Know the Outcome Early

"We trained a rank-4 linear subspace probe on the model's hidden states at the START of the thinking phase — before the model generates any reasoning. This is the hidden state RIGHT AFTER processing the puzzle prompt.

Using Leave-One-Goal-Out cross-validation:
- Qwen3-14B: AUC = **[0.757]** ([11/11] valid folds)
- Gemma4-E4B-IT: AUC = **[0.809]** ([8/11] valid folds; 3 goals excluded because n<3 examples in the minority class)

This means we can predict — with better-than-chance accuracy — whether a given attack will succeed or fail, just from how the model processes the prompt. The outcome is encoded in the prompt-processing phase.

IMPORTANT: This is a correlational result. We tested whether these directions CAUSE compliance by running a causal steering experiment. Of **[160]** candidate directions tested across both models, **[0]** passed both the KL-divergence threshold and the steering threshold. All representation results are associative, not causal."

---

## Slide 7 — What Kind of Direction Did We Find?

"We extracted three families of directions: behavioral (complied vs. refused), HVP (harmless vs. puzzle), and DVP (direct-harm vs. puzzle). We tested 9 variants per model at multiple token positions.

Key finding: **all pairwise cosine similarities are below [0.26]** — these directions are essentially orthogonal to each other. They capture different aspects of the puzzle effect.

We have NOT yet extracted the canonical refusal direction for these models using the standard harmless/harmful protocol. We cannot claim our directions are the same as, or different from, the known refusal direction without running that extraction.

One direction family failed entirely: Gemma4's HVP at the start-of-thinking position produced a **zero vector** — the direction did not extract successfully and cannot be used."

---

## Slide 8 — Can We Intervene? Causal Experiments

"We ran three causal intervention experiments, all on Qwen3-14B only.

**P11 — Prefill patching:** We replaced the residual stream activations at a given layer with activations from a 'bare harmful' (D-condition) reference run. Baseline attack success: [50%]. Patching at L3–L22: [0–10%]. Best recovery layer: L26 at [40%].

**Selectivity caveat:** In the selectivity pilot, a sham patch (patching a DIFFERENT layer) achieved [66.7%] success — higher than the genuine patch. This suggests the P11 suppression may be partly due to generic context disruption, not specific refusal-direction insertion.

**P14 — Generation-phase patching:** Patching during the THINKING phase (gen_thinking) at L10 left ASR at [44%] — partial effect only. Patching during the ANSWER phase or full generation reduced ASR to [0%] — but [80%] of outputs were TRUNCATED (broken, not genuine refusals). The mechanism of suppression is disruption, not redirection.

**P16 — Block ablation:** Zeroing out the ATTENTION OUTPUT at L26 achieves [0%] attack success — the most effective single ablation. Zeroing the MLP at L26 gives [25%]. All 12 ablation conditions suppress relative to the [62.5%] baseline."

CORRECTIONS FROM SPRINT:
- P16 baseline: 62.5% (5/8 valid), NOT 55.6% (5/9 total)
- P16 zero_mlp_L26: 25% (2/8), NOT 44% (4/9) as in sprint
- P14 gen_thinking_L10: 44% (4/9 valid), NOT 40% (4/10) as in sprint

---

## Slide 9 — CoT as Amplifier, Not Gate

"We ran a pilot experiment ([N=8] per condition) testing whether the model's chain-of-thought reasoning is a necessary component of the attack.

We tested four conditions: baseline (normal attack), forced-own-thinking (pre-filled with the model's own prior CoT), forced-cross-thinking (pre-filled with a DIFFERENT example's successful CoT), and empty-thinking (no CoT at all).

Results via StrongREJECT scoring:
- Baseline: [62.5%] (5/8)
- Forced own thinking: [62.5%] (5/8) — same as baseline
- Forced cross thinking: [50%] (4/8) — partial effect
- Empty thinking: [37.5%] (3/8) — still substantial

This suggests CoT is an amplifier, not a gate: removing CoT drops success by [25 percentage points] but does not eliminate attacks. The puzzle framing alone achieves [37.5%] even without any reasoning.

The [13.97×] thinking-token ratio (Condition A averages 11,458 thinking tokens vs. Condition F's 824) comes from **Stage 4.7** — a separate multi-prompt replication experiment — not from this CoT pilot.

CAVEAT: N=8 per condition is too small for formal inference. These numbers warrant replication at N≥50."

---

## Slide 10 — Why Does It Fail?

"When the attack fails, we want to know why. We classified [746] total failures across both models ([400] Qwen3, [346] Gemma4).

The uncomfortable truth: **more than half of all failures have NO text available** — the runs did not store the full output for failed cases ([205/400] = 51% for Qwen3; [202/346] = 58% for Gemma4). We cannot directly inspect these.

Of the failures with text:
- Explicit final refusal is the most common identifiable mode: [88] cases in Qwen3, [99] in Gemma4
- Truncated output: [8] Qwen3 cases (finish_reason=max_tokens)
- 'No obvious failure mode' — text available but no clear explanation: [89] Qwen3, [43] Gemma4

For Condition A specifically, almost ALL failures lack text: [104/114] Qwen3-A failures and [159/160] Gemma4-A failures are metadata-only.

The top priority for the next sprint is re-running with text storage enabled for all failed Condition A rows."

---

## Slide 11 — Next Steps

"Three priorities for the next sprint:

**Priority 1 — Fill in the gaps:**
- Re-run Condition A with text storage for failure cases (currently blind to why 51–58% of attacks fail)
- Scale up the CoT experiment from N=8 to N≥50 per condition
- Confirm Gemma4 causal validation status (0/160 applies to which models exactly?)

**Priority 2 — Replicate for Gemma4:**
- Run P11/P14/P16 for Gemma4 at L17 (its behavioral best layer)
- Understand why Gemma4's interaction effect is weak relative to Qwen3

**Priority 3 — Ground the directions:**
- Extract the canonical refusal direction for both models using the standard protocol
- Compare our behavioral direction (L26, AUC=0.75) to the canonical direction via cosine similarity
- This is the piece needed to connect our findings to the mechanistic interpretability literature"

---

## Speaking Notes: Numbers to NOT Get Wrong

| Number | Wrong | Correct |
|--------|-------|---------|
| P16 baseline | 55.6% | **62.5%** |
| P16 zero_mlp_L26 | 44% | **25%** |
| P14 gen_thinking_L10 | 40% | **44.4%** |
| Gemma4 LOGO AUC | 0.806 | **0.809** (8 folds) |
| Qwen3 puzzle-specific goals | 6 | **4** |
| Gemma4 n_goals_positive | 5 | **6** |
| 13.97× ratio source | CoT experiment | **Stage 4.7** |
| CoT conditions | forced_own_cot | **forced_own_thinking** |
| Interaction formula value | 0.431 (source-level) | **0.38** (goal-level, p=0.027) |
