# Paper Claim Table — defensible claims + the evidence behind each (NEXT sprint, 2026-08-09→11)

Each row is a claim we can defend, the exact evidence, and the scope/caveat. Models: Llama-3.1-8B-Instruct
(primary), Qwen3-14B (prior X-series), Phi-4-mini-reasoning (this sprint). Split: v3 leakage-0 ClearHarm.

| # | Claim | Evidence | Scope / caveat |
|---|---|---|---|
| C1 | The refusal direction is **causal** for harmful compliance: ablating it raises ASR dose-dependently. | Llama activation-ablation: ASR 0.19→0.48 (bf16), refusal_rate 0.76→0.24; α=1 ΔASR +0.286, McNemar p=5e-4. | Activation-space intervention; test n=42. |
| C2 | The causal effect is **specific** to the refusal direction. | Norm-matched **random**-direction ablation is flat/negative at every α and every precision (bf16/8/4-bit). | Random control matched on norm. |
| C3 | The causal effect is **quantization-robust**. | bf16 ΔASR +0.286 (p=5e-4), 8-bit +0.262 (p=7e-3), 4-bit +0.571 (p<1e-4); random flat throughout. | Llama; bnb 8-bit & NF4 4-bit. |
| C4 | Mechanism-derived **GCG suffixes do NOT beat random**: the refusal axis does not convert to a token-space lever. | 3-seed v3 test: refusal@L18 ASR 0.324/0.405/0.162 vs its random 0.351/0.243/<s44>; sign flips across seeds, mean small, swing ~0.19 ≫ mean. | GCG token-space; underpowered/seed-dependent (report all seeds). |
| C5 | The failure is **non-specific at the mechanism level**, not merely ASR-underpowered. | Q5 held-out mech-validity: the refusal-optimized suffix lowers the L18 refusal projection LESS than a random suffix (−1.66 vs −2.04 @hs19). | Held-out v3 test; forward-pass. |
| C6 | The **concept** axis is behaviorally **inert / epiphenomenal**. | concept@L9 GCG ASR = vanilla (0.243/0.270/0.243 ≈ vanilla, ≤ vanilla all seeds); on Phi concept⟂refusal (cos≈0) and concept readout AUC≈0.5. | Concept circuit is real in representation, not in behavior. |
| C7 | The Jacobian **sensitivity-peak layer (L12)** is not a better attack target than the readout layer. | refusal@L12 GCG ASR 0.216 < vanilla 0.243 and < refusal@L18; edges its random but ns (p=0.125). | Operationalized first-order Jacobian objective. |
| C8 | **representation ≠ behavior replicates on a third family** (Phi-4-mini-reasoning). | X2 refusal separable at all layers (0.34–0.58) but behaviorally valid at 1/6 (L14); X3 ablation causal+specific (ΔASR +0.238, p=6e-3, refusal_rate→0); X5 concept⟂refusal (cos≈0), neither readout predicts jailbreak (AUC≈0.5, CIs span 0.5). | Phi highly compliant (small headroom); AUC underpowered n=42. |
| C9 | The refusal-suppression mechanism **reproduces the Doublespeak effect**. | ds_base vs direct+refusal-ablation ΔASR≈0 at matched α across precisions and families (Llama p≈1 at α=0; Phi α=1 p=2e-5 for the gap closing). | "refusal-suppression ≈ Doublespeak". |

## One-sentence thesis
The refusal direction is a **causal, specific, quantization-robust** lever on behavior **when intervened on
in activation space** (C1–C3, C8), but it does **not** convert into a token-space optimization signal that
beats a random direction (C4–C5), and the concept circuit is behaviorally epiphenomenal (C6) — a clean
**representation ≠ behavior** dissociation that holds across three model families.
