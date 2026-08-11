# FINAL SYNTHESIS — NEXT_SPRINT_2026_08_09 (Doublespeak causal-mechanism sprint)

**One-line result:** the refusal direction is a **causal, specific, quantization-robust** lever on
harmful behavior **when ablated in activation space**, but it does **not** convert into a **token-space**
GCG objective that beats a norm-matched random direction; the concept circuit is behaviorally
epiphenomenal. A clean **representation ≠ behavior** dissociation that holds across **three model
families** (Llama-3.1-8B, Qwen3-14B, Phi-4-mini-reasoning).

Scope: v3 leakage-0 ClearHarm split (train pool 40, held-out test 42/37), StrongREJECT-judged,
off-by-one fix applied, compute-matched GCG (batch32×200), norm-matched random controls, paired stats
(McNemar + bootstrap CI). Companion docs: PAPER_CLAIM_TABLE.md, PAPER_OUTLINE_V1.md,
THIRD_FAMILY_REPLICATION.md, QUANTIZATION_EXTENSION.md, ATTACK_OBJECTIVE_FULL_MATRIX.md.

## The 7 questions, answered

**Q1 / Q3 — Does the validated refusal-suppression objective beat a norm-matched random direction as a
GCG attack? NO — non-specific, seed-dependent.** refusal@L18 vs refusal_rand@L18 on held-out test:
ΔASR = −0.027 / +0.162 / −0.081 across seeds 42/43/44; **sign flips, no seed significant** (McNemar
p = 1.00 / 0.11 / 0.51, every bootstrap CI includes 0), 3-seed mean ΔASR **+0.018** with a between-seed
swing (~0.24) an order of magnitude larger. The corrected leakage-0 split at 4× the first-cut budget with
paired stats confirms the first-cut "refusal ≈ random" result. **GATE D = NON-SPECIFIC NEGATIVE.**

**Q2 — Is the Jacobian sensitivity-peak layer (L12) a better attack target than the readout layer? NO.**
refusal@L12 GCG ASR 0.216 < vanilla 0.243 and < refusal@L18; it edges its own random (+0.108) but ns
(p=0.125) and both sit below vanilla. The first-order refusal-projection at the ‖J‖ peak is not a useful
token-space lever.

**Q4 — Does the concept term help? NO — the concept objective is inert / epiphenomenal.** concept@L9 GCG
ASR = 0.243 / 0.270 / 0.243 across seeds — **≤ vanilla every seed** (identical to vanilla at s42), and vs
its random +0.054 / −0.027 / −0.027 (all ns). Combined (concept+refusal) is worse than refusal alone.
Consistent with the concept circuit being behaviorally epiphenomenal despite being decodable.

**Q5 — Mechanistic validity: does the refusal-optimized suffix move its own internal target more than a
random suffix, on held-out prompts? NO.** At the fitted rows, the refusal suffix lowers the L18 refusal
projection **LESS** than a norm-matched random suffix (Δ −1.66 vs −2.04 @hs19; −2.81 vs −3.53 @hs23).
Adversarial suffixes suppress the refusal signal **generically**; the validated-direction objective adds
no specificity **even at the mechanism level**. This resolves the ASR seed-variance: the failure is
non-specific at the mechanism level, not merely ASR-underpowered.

**Q6 — Does representation ≠ behavior replicate on a third family (Phi-4-mini-reasoning)? YES.**
- X2: refusal direction **strongly separable at all layers** (0.34–0.58) but behaviorally **valid at only
  1/6** (L14, ablate+induce +0.20) → representation ≫ behavioral potency.
- X3: refusal **ablation is causal, dose-dependent, SPECIFIC** — direct ASR 0.714→0.952 (α=1) while
  random ablation is flat (0.714→0.714), refusal_rate 0.095→0.0; ΔASR **+0.238, McNemar p=0.006**;
  refusal-suppression ≈ Doublespeak (ds vs refabl p=2e-5).
- X5: concept ⟂ refusal (cos ≈ 0 at every layer, |cos| ≤ 0.056); **neither** the concept nor the refusal
  linear readout predicts jailbreak (AUC ≈ 0.5, all CIs span 0.5) — the strongest form of the
  dissociation: causal-under-intervention yet non-predictive-as-readout; concept not privileged.

**Q7 — Is the causal refusal-ablation effect quantization-robust? YES, at every precision.** Llama
refusal-direction ablation raises ASR dose-dependently and significantly, specific vs random, at bf16 /
8-bit / 4-bit: α=1 ΔASR **+0.286 (p=5e-4) / +0.262 (p=7e-3) / +0.571 (p<1e-4)**; random ablation stays
flat and refusal_rate collapses (0.76→0.07–0.24) at all precisions. The effect is if anything **strongest
at 4-bit**. The central causal claim does not depend on full precision.

## The unifying picture
Two facts sit side by side and define the contribution:
1. **Intervene** on the refusal direction (activation-space ablation) → large, specific, dose-dependent,
   quantization-robust, cross-family behavioral change (Q6-X3, Q7). The direction is **causal**.
2. **Optimize toward** the same direction in token space (GCG) → indistinguishable from a random
   direction, seed-dependent, and it doesn't even move its own internal target more than random (Q1–Q5).
   The direction is **not a reachable optimization objective**.

Representation-level causal handles are **not** free token-space attack objectives. This is a concrete
caution for mechanistic-interpretability-guided red-teaming and for refusal-direction-based defenses, and
it is robust across three model families and three weight precisions.

## Limitations
Held-out n = 37–42 (GCG matrix / behavioral); single concept pair per family; GCG at 200 steps / suffix-16;
Phi is highly compliant on direct harmful (small refusal headroom → X5 AUC underpowered); StrongREJECT
judge noise. All negatives are reported across all seeds without cherry-picking.
