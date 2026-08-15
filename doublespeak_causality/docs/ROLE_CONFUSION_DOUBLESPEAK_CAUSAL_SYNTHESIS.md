# Role Confusion × Doublespeak — Causal Synthesis

Capstone deliverable (plan §20, §22). Llama-3.1-8B-Instruct. All numbers trace to the
claim audit (`reports/ROLE_PROBE_CLAIM_AUDIT_TABLE.md`) and the run artifacts.

---

## 1. One-paragraph takeaway

Doublespeak makes the model internally re-map a benign codeword to a harmful concept:
the codeword becomes near-perfectly decodable as "BOMB-like" before generation (Gate 1,
held-out AUC 0.997), and this semantic-identity signal is geometrically **orthogonal to
the refusal axis** at the codeword (cos 0.09). Yet this vivid, decodable, causally
manipulable confusion is **behaviorally epiphenomenal**: it does not predict which
Doublespeak prompts jailbreak (AUC 0.59 vs refusal 0.98), and directly ablating it — an
intervention that provably collapses the concept readout by ~1.3–1.6 — does not change
harmful ASR (ΔASR −0.05 [−0.14, +0.05]), in either refusal state (2×2 interaction +0.00
[−0.14, +0.14]). The one lever that moves behavior is refusal suppression (ablation
ΔASR +0.24/+0.36, refusal rate 0.64→0.05). **Being placed in the adversarial latent
identity is not the security failure; a separable refusal-suppressed control state is.**

## 2. What was already known before this sprint

- A real, distributed concept-remapping circuit (demo K/V retrieval L8–10 → L8–11 write
  → L14–21 carry → L30–31 readout); the concept representation is real and causal for
  the model's internal readout of the codeword (§1.1).
- Concept representation ≠ jailbreak behavior: removing the concept circuit changes the
  readout but has little specific behavioral effect (§1.2).
- Refusal suppression is the behavioral lever; the refusal direction is ~orthogonal to
  the concept direction and strongly causal (§1.3).
- An attack-optimization asymmetry: the refusal axis is reachable in continuous input
  space but the discrete-token objective is non-specific and seed-unstable (§1.4).

## 3. What the role-probe paper motivated

*Prompt Injection as Role Confusion* trains controlled linear probes for a model's
perceived latent role and shows stylistic spoofing moves text into another role's latent
representation, with probe-measured confusion tracking attack success pre-generation. We
imported the method — a controlled linear probe for latent identity, confound-minimized —
and asked the sharper question their design leaves open (it has **no causal
intervention**, verified by grep, Appendix A9.9): does the latent confusion **cause** the
jailbreak, or merely accompany it?

## 4. Exact probe construction

Analogue of "same text, different role" → **same surface codeword, different contextual
binding.** From the v3 corpus (leakage-0; train 162 / dev 82 / test 80; codeword- and
concept-disjoint): positive = the Doublespeak prompt (demos bind codeword X → harmful
target), negative = the Benign prompt (same X → benign concept). Probe reads `resid_post`
(= `hidden_states[L+1]`, D1) at the query codeword (`codeword_last`) and the decision
token (`final_prompt`), fit on train, C/layer selected on dev, evaluated once on the
frozen test holdout. Estimator: L2 logistic (+ diff-of-means for directions). Extraction
reuses `pair_common.capture_components`; chat-templated prompts (the corpus spans and the
attack are both templated).

## 5. Probe validity controls (Gate 1)

Holdout AUC **0.997** [0.990, 1.000] @L11. All trivial controls near chance: length 0.587,
position 0.578, **token-identity 0.500** (exact — matched pairs share the codeword),
label-shuffle 0.465, random 0.529. The holdout is codeword-disjoint (22 unseen codewords),
so it *is* a cross-codeword generalization test → the probe reads the binding relation,
not memorized codeword→topic associations. Geometry: cos(Bombness, refusal_L18) = **+0.09**
at the codeword (orthogonal), +0.47 at the decision token. Two mechanical confounds were
also ruled out offline before extraction (length/position AUC 0.55 over n=340).

## 6. Prediction results (Phase 3)

Which pre-generation state predicts *which* Doublespeak prompts jailbreak (outcome joined
by example_id; stable across 3 behavioral runs, 94–96% agreement)? Nested logistic models
on the frozen holdout (n=42):

| model | holdout AUC |
| --- | --- |
| Bombness only | 0.592 [0.506, 0.855] |
| **Refusalness only** | **0.976** [0.921, 1.000] |
| both | 0.959 (Δ over refusal −0.016) |

Refusalness − Bombness gap +0.384 [0.114, 0.482] (excludes 0). Refusalness quantiles →
success are strongly monotone; Bombness quantiles are flat. Bombness adds nothing to
discrimination after conditioning on refusal.

## 7. Causal intervention results (Phase 4, Gate 4)

Manipulation check: ablating v_bomb at the codeword over L8–18 collapses the downstream
Bombness readout by −1.3 to −1.6 at L20/24/28/31; norm-matched random ablation ≈ 0
(specific). Behavioral (n=42, two independent runs):

| arm | ASR | refusal rate |
| --- | --- | --- |
| baseline | 0.21–0.24 | 0.64 |
| **Bombness ablated** | 0.19–0.21 | **0.64** |
| random ablated | 0.19–0.24 | 0.66 |
| **refusal ablated** | 0.48–0.57 | **0.05** |

- **Bombness necessity:** ΔASR **−0.05** [−0.14, +0.05], p=0.63; refusal rate unchanged.
- **Refusal (positive control):** ΔASR **+0.24** [+0.07, +0.41], p=0.02; refusal rate
  collapses. The design detects effects of that size; the Bombness null CI **excludes** it.
- **2×2 factorial (§8.6):** main-effect Bombness **+0.00** [−0.07, +0.07]; main-effect
  refusal **+0.36** [+0.20, +0.50]; **interaction +0.00** [−0.14, +0.14]. Bombness is
  inert whether refusal is intact *or* suppressed — **Story B (gated causality) refuted.**
- **Sufficiency (§8.5):** injecting Bombness into neutral prompts to the natural
  doublespeak level (manipulation check verified on-manifold, readout +5 to +8) does not
  induce harm — neu_bomb_add ΔASR **+0.05** [p=0.50], refusal rate identical; the
  refusal-from-neutral control moves ASR **+0.33** [p=0.001]. **Bombness is not sufficient.**

**Bombness is neither necessary, nor sufficient, nor gated** — fully epiphenomenal for
behavior, established from both intervention directions (remove and add) plus the 2×2.

## 8. Concept-vs-refusal dissociation

Three independent lines, one conclusion:

| | Bombness (semantic identity) | Refusal (control state) |
| --- | --- | --- |
| decodable | 0.997 | — |
| geometry at codeword | ⊥ refusal (0.09) | — |
| predicts jailbreak | 0.59 (chance) | 0.98 |
| causally necessary | −0.05 [−0.14,+0.05] | +0.24 [+0.07,+0.41] |
| 2×2 main effect | +0.00 [−0.07,+0.07] | +0.36 [+0.20,+0.50] |

The concept representation is real, decodable, orthogonal to refusal, and causally
manipulable — and behaviorally inert. Refusal predicts and causally controls behavior.

## 9. Cross-cohort and cross-model status

**Cross-cohort (generated cohort, gpt-4o-mini one-line requests; run 757957):**
- **Gate 1 replicates strongly** — Bombness holdout AUC **0.997** [0.990, 1.000], controls
  near chance. The decodability result generalizes to a distributionally-different cohort.
- **Bombness is non-predictive there too** (AUC 0.49) — the epiphenomenal half of Story A
  holds cross-cohort.
- **The refusal-predicts-jailbreak result is weaker on generated** and does not cleanly
  replicate: frozen clearharm refusal direction AUC 0.525 (gap vs Bombness CI includes 0);
  a native decision-token probe reaches only 0.60–0.63 vs clearharm's 0.98. So the
  *strength* of the refusal-prediction result is clearharm-specific — attributable to
  cross-distribution transfer of the refusal direction (B17) and to generated jailbreaks
  being inherently less predictable. The directional dissociation survives; the effect
  size does not. The clearharm **causal** result (Gate 4/2×2) is unaffected; a
  generated-cohort Phase-4 run would test causal replication (deferred).

**Cross-model — Gate 1 replicates on THREE model families** (runs 758022 Phi, 758030 Qwen):

| model | hidden | Gate 1 holdout AUC | max control | cos(Bombness, refusal) |
| --- | --- | --- | --- | --- |
| Llama-3.1-8B-Instruct | 4096 | 0.997 [0.990,1.000] | 0.587 | 0.06–0.15 |
| Phi-4-mini-reasoning | 3072 | 0.985 [0.967,0.998] | 0.562 | 0.01–0.04 |
| Qwen3-14B (8-bit) | 5120 | 0.999 [0.995,1.000] | 0.591 | 0.03–0.12 |

On all three (token-identity control exactly 0.500 in each, by matched-pair design),
contextual Bombness is **decodable and orthogonal to refusal**. The decodable,
refusal-orthogonal semantic-remapping representation is a **cross-family property** —
robust across three distinct architectures and three hidden sizes, not a Llama quirk.

**Behavioral Phase 4 across three families** (Llama 757931/757943/757992, Phi 758057,
Qwen 758075; manipulation check passed on all):

| model | base refusal | base ASR | Bombness necessity (ΔASR) | refusal ablation (ΔASR) |
| --- | --- | --- | --- | --- |
| Llama-3.1-8B | 0.64 | 0.24 | −0.05 (null, =random) | **+0.24, p=0.02** |
| Phi-4-mini | 0.048 | 0.26 | −0.07 (null, =random) | +0.10, p=0.39 (ns, floor) |
| Qwen3-14B | 0.119 | 0.071 | +0.05 (null, =random) | **+0.17, p=0.04** |

Two cross-family conclusions:
1. **Bombness is behaviorally epiphenomenal on all three families** — necessity null (=
   random) everywhere, manipulation check passed everywhere. The representation≠behavior
   dissociation is cross-family.
2. **Refusal is the causal lever on Llama and Qwen** (both significant) — the two families
   that retain refusal headroom against doublespeak. Phi's ns result is a **floor artifact**
   (base refusal 0.048; doublespeak already collapsed it), not a mechanism difference. So the
   refusal-lever story is general: refusal is causal *wherever there is refusal to ablate*.

**Interpretation.** Behavioral *susceptibility* to doublespeak is a spectrum (Phi most
susceptible, Qwen least, Llama middle), but the *mechanism* is invariant across families:
Bombness never matters; refusal always does when present. The semantic-remapping
representation and its behavioral epiphenomenality are both cross-family; the only
model-dependence is how much of the model's refusal doublespeak has already defeated.
(Phase 3 prediction: Llama refusal AUC 0.98; Phi/Qwen underpowered — Phi refusal
pre-collapsed, Qwen only 3 jailbreaks — so prediction is a Llama result.)

## 10. Attack-objective implication

Bombness is behaviorally epiphenomenal, so it must **not** be promoted to a discrete
attack objective (plan §13, Gate D→"do not optimize"). The only causally potent axis is
refusal, whose discrete-optimization asymmetry is already an established negative (§1.4).
No new attack objective is warranted by these results.

## 11. Limitations / power

- n=42 holdout for behavioral claims (base ASR ~0.22); nulls stated as CI bounds, not
  "zero." The bounds exclude the refusal-magnitude effect, so the nulls are informative,
  not merely underpowered.
- Single cohort (clearharm), single dose (α=1 full ablation), single band (L8–18), single
  seed for Phase 4; run-to-run ASR drift ~0.02–0.03 (B15) — the qualitative result is
  identical across the two full runs and the 2×2.
- Refusal direction fit cross-distribution (carrot_bomb, B17); it nonetheless predicts and
  causally controls clearharm behavior, which validates it.
- Necessity + interaction established; **sufficiency (§8.5) not run.**

## 12. What is still not established

- **Cross-family** Bombness (Phi/Qwen, Phase 8) and the **Phi concept** completion (B16).
- **Cross-cohort** (generated) and **second-corpus** (Phase 10) replication.
- The **normalized-space** (upstream mid-block) probe robustness arm.
- Component-restricted probe-mediated patching (Phase 5); D3 scope-matched control
  (Phase 6) — inherited open items.

## 13. Ranked next steps

1. **Phi concept completion (B16)** + **cross-family probe (Phase 8)** — is Story A a
   cross-family property? (GPU)
2. **A re-conditioned generated-cohort Phase-4** (narrower band / lower dose) to get a clean
   manipulation check there (E22); the clearharm causal result is complete.
3. **Second corpus + prospective power (Phase 10)** — publication-grade behavioral n.
4. Normalized-space robustness arm; component-restricted patching (Phase 5).
5. Independent adversarial audit (§21) against raw artifacts before write-up.

_Done since first draft: sufficiency (§8.5, run 757992) and generated-cohort Gate 1 +
prediction (§9)._

---

**Bottom line.** We reproduced the role-confusion methodology, confirmed that Doublespeak
induces a genuine latent identity confusion, and then showed — by prediction *and* by
causal intervention including a 2×2 factorial — that this confusion is not the behavioral
mechanism. The security failure lives in a separable, refusal-suppressed control state.
This extends the role-confusion result: being moved into an adversarial latent identity is
not automatically the cause of the attack's success.
