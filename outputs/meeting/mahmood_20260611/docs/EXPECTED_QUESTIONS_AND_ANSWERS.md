# Expected Questions and Answers — Mahmood Meeting, 2026-06-11

---

## Q1: Why not claim the refusal direction is causal?

**A:** Stage 4A2 tested this directly: we applied 160 causal interventions (steering vectors on Layer-22 activations) and 0/160 survived. The model either collapsed its output or ignored the intervention. A direction that cannot be steered to produce the expected causal effect is not a validated causal mechanism — it's correlational. The correlation is real (projection diverges early in successful attacks), but correlation ≠ causation here.

---

## Q2: What exactly did Stage 4A2 show?

**A:** Stage 4A2 selected 160 intervention candidates (parameter combinations: intervention strength, layer, timing) and applied each to a held-out set of attack prompts. The criterion was: does steering the direction change compliance in the predicted direction (reduce it for high-projection, increase it for low-projection)? Zero out of 160 candidates met the criterion. The status was recorded as `intervention_selection_failed_no_survivors`. This is a strong negative result — the space of interventions explored was large enough to rule out simple scalar steering.

---

## Q3: If A succeeds more, why is Layer 22 projection lower for A?

**A:** The most parsimonious explanation: the Layer-22 direction doesn't track compliance — it tracks thinking depth (or a related reasoning-style feature). When the puzzle format induces deep extended thinking (condition A: mean 11,458 tokens), the model's representations "move away" from the direction — which is consistent with the direction capturing a shorter, more defensive (less reasoning-saturated) response style. When thinking is shallow (condition D: 2,924 tokens; F: 824 tokens), projection is higher. The Spearman ρ between projection and log(thinking tokens) is −0.678 (condition A, p=0.015), confirming this.

---

## Q4: Does this disprove refusal dilution?

**A:** It weakens the specific version we tested. The scalar Layer-22 direction we extracted does not dilute in proportion to compliance — it dilutes in proportion to thinking depth. A richer hypothesis (e.g., a multi-dimensional subspace that separately tracks thinking depth and compliance tendency) could still be consistent with a refusal-dilution mechanism. We haven't tested that. What we've ruled out is the simplest version: "compliance correlates with reduced projection onto this one direction."

---

## Q5: Does the puzzle matter, or only length?

**A:** Both length and puzzle structure matter — but they're not the same thing. Condition F (length-matched benign wrapper) controls for length and still performs much worse than A (3/11 vs 10/12). So length alone is insufficient. However, we haven't isolated what specific property of the puzzle structure matters — whether it's the semantic content (instructions, constraints), the reasoning structure it induces (multi-step problem solving), or the task coherence (clear goal with embedded target). The benign wrapper rules out length; it doesn't tell us which of these is the active ingredient.

---

## Q6: Does thinking matter?

**A:** Yes. Condition E (full puzzle, thinking=off) succeeds at 4/9 (44%), vs A (full puzzle, thinking=on) at 10/12 (83%). Sign test A−E: p=0.031. So turning off thinking substantially reduces success even with the full puzzle. The thinking phase is a necessary contributor, not just a side effect.

---

## Q7: Why is StrongREJECT enough or not enough?

**A:** StrongREJECT is a validated automated evaluator for attack success on harmful requests. It's consistent and fast. Its main limitation is that it may not match human judgment in edge cases, and we skipped the Gemini judge alternative (spending cap). For the purposes of this experiment — comparing conditions on the same model and prompt set — StrongREJECT is sufficient to detect relative differences. It is not a claim about absolute harm or about how a human would evaluate the outputs.

---

## Q8: Why not continue LLM onset annotation?

**A:** The LLM-onset annotation pipeline (using Gemini to label where "thinking" switches from reasoning to compliance in the CoT) is currently blocked by a spending cap on the Gemini API. The data exists but the annotation run hasn't been approved. This limits our ability to analyze the within-thinking-phase dynamics at the token level. It's documented as blocked, not abandoned.

---

## Q9: Why not do RL now?

**A:** RL (reinforcement learning to optimize the attack prompt using behavioral signal) requires either (a) a validated mechanistic direction to use as the reward signal, or (b) a behavioral reward signal. Option (a) failed: the scalar direction doesn't track compliance. Option (b) — using StrongREJECT — is Option C in our next-sprint discussion, which is a reasonable path if the thesis goal is attack optimization. But doing RL before validating the behavioral signal at scale (more goals, more prompts) risks optimizing for a brittle proxy.

---

## Q10: Why did behavior-conditioned direction extraction fail?

**A:** "Behavior-conditioned direction extraction" requires matched-outcome cells — cells where the same prompt × condition produces both successes and failures across different seeds. This gives us contrastive pairs that differ only in the model's stochastic behavior, not in the prompt or condition. Stage 4.8 found only 3 such cells (threshold was 4). With 3 cells, the extracted direction would be unreliable. The reason there are so few matched cells: Goal 1 fails deterministically (0/15) and Goal 3 succeeds deterministically (15/15), leaving only Goals 0 and 2 with variation. We need more goals with intermediate susceptibility.

---

## Q11: What should we do next?

**A:** Three options with clear trade-offs:

1. **Option A (more data):** Run Stage 4.9 with more goals/phrasings to increase statistical power and get more matched cells. Best if we want stronger empirical evidence before the mechanistic step.

2. **Option B (mechanistic probe):** Fit a low-dimensional subspace/probe on existing Stage 4.7/4.8 representations, test on held-out goals. Best if the thesis needs a mechanistic contribution.

3. **Option C (AutoInject behavioral adaptation):** Use StrongREJECT as the behavioral objective for prompt optimization, bypassing the failed scalar direction. Best if the thesis goal is attack-improvement.

Primary recommendation: **Option B** if Mahmood wants a mechanistic thesis; **Option C** if he wants attack-improvement. These require different amounts of new GPU compute (B needs small targeted Stage 4.9 first; C needs access to the AutoInject pipeline).

---

## Q12: What would count as a publishable result?

**A:** Several possible publication frames:

- **Behavioral frame:** "Structured puzzle format in CoT attacks: length is not sufficient, thinking is necessary, and the effect generalizes across goals." This is already supported by Stages 4.7 and 4.8. Needs more goals to be convincing at the workshop level.

- **Mechanistic null frame:** "Simple scalar refusal-direction theory fails in controlled settings — the direction tracks thinking depth, not compliance." This is a strong negative result, publishable as a findings note or workshop paper.

- **Mechanistic contribution frame (if Option B succeeds):** "A low-dimensional reasoning subspace predicts compliance in controlled attacks better than the scalar refusal direction." This would be the strongest contribution, likely workshop or main conference.

- **Attack frame (if Option C succeeds):** "Behavioral reward signal (StrongREJECT) is sufficient to adapt AutoInject to reasoning models; optimized prompts resemble puzzle structure." Publishable as an attack paper if the effect is strong.
