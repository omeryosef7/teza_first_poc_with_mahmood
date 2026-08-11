# Paper Outline V1 — "Representation ≠ Behavior: the refusal direction is causal but not a token-space lever"

Working title. Builds the current Gate-7 first-cut into a full story via the sprint's 9 defensible claims
(see PAPER_CLAIM_TABLE.md). Three families: Llama-3.1-8B, Qwen3-14B, Phi-4-mini-reasoning.

## Abstract
In-context representation hijacking ("Doublespeak") and refusal-direction analyses suggest a single
linear "refusal" axis governs harmful compliance. We show a sharp dissociation: ablating the refusal
direction in *activation space* is a causal, specific, and quantization-robust lever on behavior, yet the
same direction does **not** yield a *token-space* adversarial-suffix objective that beats a norm-matched
random direction. A "concept" circuit that is decodable in representation is behaviorally epiphenomenal.
The pattern replicates across three model families. Representation-level causality does not imply a
token-space optimization handle — a caution for mechanistic-interpretability-guided attacks and defenses.

## 1. Introduction
- Doublespeak / refusal-direction background; the intuitive "one axis" hypothesis.
- Our question: does a causal, decodable direction give an *attacker* a usable token-space objective?
- Contributions: C1–C9 (claim table). Headline = representation≠behavior, three families.

## 2. Setup
- Models, ClearHarm v3 leakage-0 split (train pool 40, held-out test 42), StrongREJECT judging.
- Refusal direction (diff-of-means, validated by ablate+induce); concept direction (concept vs codeword).
- GCG (`poc_stage_gcg_early`), refusal-projection loss, off-by-one fix, compute-matched batch32×200.
- Norm-matched random-direction controls; paired stats (McNemar, bootstrap CI).

## 3. The refusal direction is causal in activation space (C1–C3)
- Ablation dose-response, specific vs random, quantization sweep (Fig: bf16/8/4-bit dose curves).
- → refusal-suppression reproduces Doublespeak (C9).

## 4. …but not a token-space lever (C4–C5, C7)
- Full attack-objective matrix: refusal@L18 / Jacobian@L12 / concept@L9 / combined vs random, 3 seeds.
- The seed-dependent near-tie; Gate-D NON-SPECIFIC NEGATIVE.
- Mechanistic-validity (Q5): suffixes suppress the projection *generically*, random ≥ mechanism.

## 5. The concept circuit is epiphenomenal (C6)
- concept@L9 GCG inert; concept⟂refusal geometry; concept readout AUC≈0.5.

## 6. Cross-family replication (C8)
- Phi-4-mini-reasoning X2/X3/X5; representation≠behavior holds; caveats (compliance headroom, n).

## 7. Discussion
- Why activation-space causality ≠ token-space optimizability (leverage vs reachability).
- Implications for interp-guided red-teaming and for refusal-direction defenses.
- Limitations: held-out n=42, GCG budget, single concept pair per family, judge noise.

## 8. Conclusion
Representation-level causal handles are not free attack objectives; report negative/again-random results.

## Figures/Tables
- T1 claim table; F1 quant dose curves; T2 3-seed attack matrix; T3 Q5 mech-validity; F2 Phi X2/X3/X5; F3 concept⟂refusal geometry.
