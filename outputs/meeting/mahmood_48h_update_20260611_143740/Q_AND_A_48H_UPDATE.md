# Q&A Preparation — 48h Mahmood Update

_June 2026 | Omer Yosef_

---

## Q1: "Do we still believe in refusal direction?"

**Short answer:** As a diagnostic probe, yes. As a causal mechanism, no.

**Full answer:**
The Layer-22 direction has strong linear separability (separation score 14.17) between harmful
and harmless prompts. It is a valid feature of the model's representation space. However:

- In Stage 4.7, the projection anti-correlates with behavioral success
  (conditions with lower projection = more successful attacks)
- It correlates with thinking depth, not compliance
- Stage 4A2 showed 0/160 successful causal interventions via dampening

The direction tells us something real about the model's representation of harmful content,
but it is not the mechanism of the attack. Label it "provisional harmful-vs-harmless contrast
direction" — useful for analysis, not the main story.

---

## Q2: "Is the puzzle necessary?"

**Short answer:** Not strictly necessary, but reliably amplifying.

**Full answer:**
- Condition D (bare target, no puzzle) achieves 45.5% ASR in Stage 4.7
  and 50% in Stage 4.8 — not zero
- Goals 1 and 3 succeed or fail across all conditions regardless of puzzle
- Some source prompts succeed in D but not F and vice versa

The puzzle is a **reliable amplifier** (+41.7 pp over D, +58.3 pp over F in Stage 4.7),
but the attack is possible without it at ~45-50% baseline. This is actually an important
nuance: we're studying amplification dynamics, not an on/off switch.

---

## Q3: "Is this just prompt length?"

**Short answer:** No. Condition F controls for this.

**Full answer:**
Condition F is a benign wrapper constructed to match condition A's token count within ±5%.
It achieves only 27.3% ASR vs 83.3% for A. Same length, drastically different outcomes.

Condition F also generates only 821 median thinking tokens vs 13,592 for A — despite
identical prompt lengths. This rules out the hypothesis that more prompt tokens → more
thinking → more attack success. The semantic/structural content of the puzzle drives
both the thinking amplification and the behavioral effect.

---

## Q4: "Why not start RL now?"

**Short answer:** We don't yet have a validated reward function for the interesting component.

**Full answer:**
We could start RL with just StrongREJECT score as reward — that would work. But it would
be optimizing blindly without understanding *what structural features matter*. Specifically:

1. The onset timing reward (delayed safety commitment) is unvalidated — the heuristic
   may be classifying 92% of traces as "early" due to over-extraction
2. We have only 3 matched-outcome cells (need 4) for the behavior-conditioned direction
3. We don't know if RL will discover the same "puzzle amplification" mechanism or a
   completely different structural feature

RL after onset validation = principled. RL now = optimizing a black box.

---

## Q5: "What did the new papers change?"

**Short answer:** They give us theory (Safety-before-CoT) and a name (Delayed Safety Commitment).

**Full answer:**
- **CoT Hijacking:** Our behavioral evidence confirms and extends the original paper
  with the length-matched control (condition F) that prior work lacked
- **Doublespeak / Representation Hijacking:** Our Layer-22 null result refutes the
  simple linear direction claim as a mechanism, while being consistent with more
  complex representation effects
- **Safety-before-CoT:** This paper provides the theoretical framework for why onset
  timing matters — and gives our new analysis a literature anchor

Together, they shift the framing from "we found an attack" to "we understand why it works
and what to measure next." That's a stronger paper.

---

## Q6: "What is the next publishable contribution?"

**Short answer:** First paper combining behavioral ASR, mechanistic null, onset timing, and RL readiness.

**Full answer:**
The key elements for a publishable contribution:

1. **Behavioral contribution** (already solid): A > D > F with length-matched control,
   confirmed under greedy and stochastic decoding, at n=12 diverse prompts
2. **Mechanistic contribution** (null but important): Layer-22 refusal direction does
   NOT predict behavioral success — first clear demonstration of this limitation
3. **Timing contribution** (pending): Onset proxy analysis + manual validation showing
   when safety commitment occurs relative to attack success
4. **Theory contribution** (ready): "Delayed Safety Commitment" hypothesis unifying 3 papers

The paper is about characterizing the attack mechanism rather than just reporting ASR numbers.
That's the positioning relative to prior work.

---

## Q7: "What would convince us the unified theory is wrong?"

**Short answer:** If onset timing does NOT correlate with success, the timing hypothesis fails.

**Full answer:**

| Falsification test | Result if theory is wrong |
|-------------------|--------------------------|
| Onset timing does not predict success | Timing mechanism not load-bearing |
| Condition F generates same thinking as A on some goals | Semantic content not causal |
| RL finds a non-timing-related structural feature that beats A | A different mechanism explains the effect |
| Layer-22 intervention DOES reduce ASR (re-run of Stage 4A2 with different approach) | Direction IS mechanistically relevant |
| Bare target (D) outperforms puzzle (A) on more goals as n increases | Puzzle is not a reliable amplifier |

The theory is falsifiable. We should be actively trying to falsify it with the next
experiments, not just confirming it. If manual onset annotation shows no difference
between success and failure onset positions, that's an important null result.

---

## Q&A — AutoInject POC [NEW]

**Q: What is AutoInject and why are we using it?**

AutoInject is a GRPO-based RL system for learning adversarial prompt suffixes in LLM agent
benchmarks. We use it because one of the original project goals was to adapt it for
reasoning-model hijacking. The offline POC validates that its optimization framing is
directly applicable to our structural wrapper selection problem.

**Q: Is this safe to run?**

The offline POC is completely safe — it uses existing Stage 4.7/4.8 cells and generates no
new content. An online run would also be safe if constrained to structural wrapper choices
over existing research prompts. No new harmful content would be generated.

**Q: Does this prove that RL improves ASR?**

No. The offline POC shows that all optimization policies would select Condition A,
which we already know is the best condition. The value of a real online run is to
(a) validate robustness and (b) generate matched cells for mechanistic analysis.

**Q: What is GRPO and why is it different from random search?**

GRPO (Group Relative Policy Optimization) is a policy gradient RL algorithm that
trains a model's weights using reward signals from rollouts. Unlike random search,
it updates the policy model to generate better candidates over time. In our POC,
we borrow the reward framing but run offline (no model training).

**Q: Why is L22 projection not used as a reward?**

The Layer-22 direction is described as a "provisional harmful-vs-harmless contrast
direction" or "diagnostic projection direction." It is not a proven refusal mechanism.
Using it as a reward would risk optimizing a proxy that may not generalize. Primary
reward must be sr_success/sr_score.

**Q: What is the difference between the offline POC and what we want to run next?**

Offline POC: Fixed pool of existing cells → rank/select → no new generations.
Online experiment (pending approval): Same research prompts → run Qwen3-14B → collect
sr_success → apply AutoInject-style policy update → repeat for ~40 evaluations.
