# Literature Bridge: Delayed Safety Commitment / Reasoning-Path Hijacking

_Prepared for Mahmood meeting, June 2026_

---

## Unified Hypothesis

> **Delayed Safety Commitment / Reasoning-Path Hijacking:**
> These attacks succeed when the model is pulled into a long reasoning trajectory before
> the unsafe objective is treated as a direct safety decision. The unsafe target may appear
> as a puzzle constraint, semantic alias, educational frame, or internal reasoning target.
> The important variables are not just refusal strength, but **timing**, **representation**,
> and **commitment to a reasoning path**.

The key insight: once a model has invested significant reasoning tokens in a trajectory
that implicitly accepts the harmful goal as a "task to complete," it becomes progressively
harder for safety mechanisms to reverse course. The puzzle wrapper *manufactures* this
reasoning investment before the model encounters the explicit harmful target.

---

## Paper 1 — Chain-of-Thought Hijacking (our research anchor)

**Finding:** Long harmless-looking reasoning preambles can dilute or delay safety
responses. Wrapping a harmful target in a puzzle structure dramatically increases both
thinking token count and attack success rate.

**Measurable predictions:**
- ASR(A: full puzzle + thinking) > ASR(D: bare target + thinking) > ASR(F: benign wrapper + thinking)
- Thinking token count: A >> D >> F (for the same harmful target)
- Thinking off (condition E) dramatically reduces ASR

**Our data:**
- Stage 4.7 confirms: A = 83.3%, D = 45.5%, F = 27.3% ASR (complete-case, n=12)
- Thinking tokens: A median ~13,600, D median ~2,574, F median ~821
- Condition E: ~0% ASR (thinking off = no hijacking)
- Stage 4.8 independently replicates: A = 60%, D = 50%, F = 40% (n=20, stochastic)

**Limitation:** We have behavioral evidence but not yet mechanistic evidence of the
timing mechanism. The Layer-22 projection direction does not confirm causal refusal
suppression (it anti-correlates with thinking depth, not behavior).

---

## Paper 2 — In-Context Representation Hijacking / Doublespeak

**Reference:** "Doublespeak" / In-Context Representation Hijacking  
_(Conceptual class: papers showing benign surface tokens acquiring harmful internal semantics)_

**Core claim:** Under certain contextual conditions, semantically harmless surface tokens
can acquire harmful internal representations across context and model layers. The model
can process harmful objectives through tokens that appear benign on the surface.

**Measurable predictions:**
- Representations of neutral tokens in the puzzle wrapper shift toward harmful semantic
  space as context accumulates
- A single direction in layer activations captures this "semantic drift"
- The drift should be detectable in intermediate layers (e.g., Layer 22) before the
  model outputs anything harmful

**Connection to our data:**
- The Layer-22 projection direction was extracted as a harmful-vs-harmless contrast direction
- However, it anti-correlates with behavioral success: higher projection → fewer successes
- This refutes simple single-direction hijacking: the direction may capture "how far into
  harmless semantic space the model is pushing" rather than "compliance with the attack"
- Alternative interpretation: benign puzzle tokens pull model INTO harmless semantic space,
  which actually *reduces* the harmful-direction signal while simultaneously enabling attack

**Our refinement:** Representation hijacking may be happening in a more complex, non-linear
way. The puzzle may work by diluting refusal-relevant features rather than by directly
activating harmful features. This is why a simple linear direction fails to predict behavior.

---

## Paper 3 — Towards Safer Large Reasoning Models: Safety Before CoT

**Reference:** Towards Safer Large Reasoning Models by Promoting Safety Decision-Making
before Chain-of-Thought Generation  
_(2025; focuses on the ordering of safety vs reasoning in thinking models)_

**Core claim:** Safety decisions should be made BEFORE extended reasoning begins, not
after. If a model enters a long reasoning trajectory without first committing to a
refusal, it may reason itself into compliance with harmful requests.

**Measurable predictions:**
- Models that check safety BEFORE thinking (before <think> tags) should show lower ASR
  than models that check safety only at output time
- The timing of the first safety-relevant reasoning step matters more than the total
  reasoning length
- Interventions that force safety commitment early in the reasoning trace should reduce ASR

**Connection to our data:**
- This paper's hypothesis is the theoretic foundation for our "delayed safety commitment"
  framing
- Our onset analysis (Task 2) directly operationalizes "when does the model first engage
  with the harmful target" as a proxy for this timing question
- Stage 4.7 condition F shows that same-length benign wrappers fail to trigger long
  thinking → suggesting the puzzle's semantic structure, not just length, is what delays
  safety commitment
- Stage 4.7 condition E (thinking off) = 0% ASR → confirms thinking is load-bearing for
  the attack, consistent with safety-before-CoT hypothesis

**Tension with our data:**
- If safety-before-CoT fully explains the attack, we would expect onset to be consistently
  late for successes and early for failures
- Our onset proxy is not yet validated; this test is pending

---

## Paper 4 — AutoRAN / H-CoT / Safety-Reasoning Hijacking (Monitoring Note)

**Status:** Several papers in this space appeared in 2025–2026 that may be relevant.
Specific papers to verify: AutoRAN (automated reasoning attack generation), H-CoT
(hierarchical CoT attacks), direct safety-reasoning hijacking variants.

**Connection:** These papers may provide additional attack surface definitions, alternative
puzzle structures, and countermeasures that our RL readiness plan should account for.

**Action needed:** Set search alerts (see `LITERATURE_WATCH_ALERTS.md`) and review
any new papers in this space before the next meeting.

---

## Unified Theory: How the Papers Connect

```
                    ATTACK SURFACE
                         |
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
    Behavioral      Representational   Timing
    evidence        evidence           evidence
    (CoT Hijacking) (Doublespeak)      (Safety-before-CoT)
          |              |              |
          └──────────────┼──────────────┘
                         ↓
         Delayed Safety Commitment Hypothesis:
         Attack succeeds when model commits to
         reasoning path before safety triggers
                         |
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
    Our Stage 4.7   Layer-22 probe   Onset analysis
    A>D>F (behavior) (mechanism?)     (timing proxy)
    CONFIRMED       REFUTED as       PENDING validation
                    primary signal
```

**What our data adds:**
1. First systematic behavioral comparison with length-matched control (condition F)
2. First quantitative evidence that Layer-22 direction is NOT the behavioral mechanism
3. First attempt to measure onset/timing proxy in thinking traces

**What we need:**
1. Validated onset measurements (manual annotation)
2. Per-token safety-commitment detection (is there a moment when the model "decides"?)
3. Controlled difficulty variation experiments (harder puzzle → later safety commitment?)

---

## Measurable Predictions Per Hypothesis

| Hypothesis | Prediction | Our Evidence | Status |
|-----------|-----------|-------------|--------|
| CoT Hijacking: long harmless preamble delays refusal | ASR(A) > ASR(D) | A=83% vs D=45% (n=12) | ✅ Confirmed |
| CoT Hijacking: thinking is load-bearing | ASR with thinking off ≈ 0% | E=0% | ✅ Confirmed |
| Doublespeak: harmful semantics in benign tokens | Layer-22 projection predicts ASR | ρ(proj, ASR) < 0 | ❌ Refuted (anti-correlation) |
| Safety-before-CoT: timing matters | Early onset → lower ASR | Pending | ⏳ Pending |
| Length confound | ASR(A) ≈ ASR(F) for same-length prompts | A=83% vs F=27% | ✅ Refuted length confound |
| Delayed safety commitment | Success correlates with late onset | Pending | ⏳ Pending |

---

## What This Framing Offers to the Paper

1. **Novelty:** We provide both behavioral confirmation AND mechanistic null result —
   the attack is real but the mechanism is more complex than a single direction.
2. **Theory:** "Delayed safety commitment" unifies the behavioral and timing observations
   under a single hypothesis grounded in 3 prior papers.
3. **Future work:** The RL next step is natural: learn to manufacture delayed safety
   commitment via structural prompt features, guided by onset timing as a reward.
4. **Defensibility:** By NOT overclaiming the Layer-22 direction, we avoid the common
   weakness in interpretability papers of oversimplifying mechanism.
