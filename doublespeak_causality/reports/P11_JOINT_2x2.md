# §11 — Joint 2×2 Factorial (concept-circuit {intact/ablated} × refusal {restored/not})

**Status:** ✅ DONE. Clean predicted pattern: **refusal restoration collapses ASR regardless of concept state;
concept ablation barely moves ASR; no interaction (additive).** Confirms concept-vs-refusal dissociation via
the mechanism×mechanism factorial (Claim C/D). Not floor-bound (near_floor_flag=False).

**Run:** `phase11_joint_2x2_W8_9_10_11_R18_...736657` (v3 pooled n=324). Concept ablation = write(L8-11)+carry
(reused from §10); refusal restoration = calibrated AllPositionAdd @ L18 (reused from calinj/§19-21). McNemar +
within-item DiD interaction (bootstrap CI + perm-p).

## Result — POOLED (n=324, not floor-bound: I_max=0.79)
| cell (concept, refusal) | ASR |
|---|---|
| (0,0) ds_base | 0.321 |
| (1,0) concept-ablated | 0.315  (Δ_concept = −0.006, ns) |
| (0,1) refusal-restored | 0.219  (Δ_refusal = **−0.102, p=9e-6**) |
| (1,1) both | 0.191  (Δ_both = −0.130) |

**Interaction Ihat = −0.022, 95% CI [−0.083, +0.040], perm-p=0.56 → NO significant interaction (additive).**
clearharm cohort: same pattern (refusal −0.112 p=5e-4; concept +0.065 ns; Ihat −0.047 ns).

## Interpretation
- **Refusal restoration is the behavioral lever** (−0.10 ASR, p<1e-5) — and it works whether or not the concept
  circuit is ablated (no interaction).
- **Concept ablation is behaviorally inert** in BOTH refusal states (Δ≈0; slightly +0.06 on clearharm =
  non-specific degradation, per §10).
- The two mechanisms are **causally independent and only refusal matters** → the cleanest mechanism×mechanism
  statement of the concept-vs-refusal dissociation (Claim C: separable; Claim D: refusal is the decision lever).
