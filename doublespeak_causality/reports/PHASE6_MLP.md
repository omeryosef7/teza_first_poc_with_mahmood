# reports/PHASE6_MLP.md — MLP Write-Location (in progress)

Does an MLP write the retrieved harmful concept into the residual stream, and where?

## Representational projection (COMPLETE) — late-dominated = readout-proximity artifact, NOT causal

`scripts/phase6_mlp_projection.py` on the extracted reps (means.npz mlp_out) + directions.npz. Per layer,
MLP write update = mean(DS mlp_out) − mean(NEUTRAL mlp_out) at codeword_last, projected onto the concept
direction (d_Direct in mlp_out space). Split=dev.

Top concept-write layers (proj_concept, cos):
- clearharm: **L31 11.5 (cos 0.69)**, L30 3.97, L29 3.59, L27 1.06 … band: early 1.7 / mid 4.4 / **late 25.3**
- curated: **L31 6.2 (cos 0.45)**, L30 1.64, L29 1.18, L28 0.51, L11 0.47, L13 0.42 … band: early 1.4 / mid 2.3 / **late 11.1**

**This is the readout-proximity confound, NOT the causal write.** The projection peaks at the last layers
(L29–31) on both cohorts. But a large projection late is exactly what the master plan warns about ("a write
layer must satisfy MORE than a large projection") and what prior N7-C established: late MLP output aligns
with the concept direction because the residual is accumulating toward the unembedding, while the validated
attribution-patching (AtP, pearson 0.93–0.95 vs true SubmodulePatch(mlp)) put the *causal* MLP write in the
**mid-band L9–14** (late MLP AtP ≈ 0 despite large mechanical patch effects). curated shows a faint mid-band
bump (L11, L13) consistent with the true mid-band write, swamped in raw projection by the late proximity term.

**Conclusion:** the projection metric reproduces the known late-proximity artifact on the new split and must
NOT be read as the write location. The causal write requires exact MLP intervention (next).

## Causal MLP write (PENDING)
Patch the DS mlp_out ← benign at codeword positions, per layer (necessity), with the FC readout, and/or
recompute AtP for MLP layers on the split. Expect the causal write in the mid-band (L9–14), matching the
demo-KV retrieval band (L8–11) + a +1/+2 layer attention→MLP cascade (prior N7-E). This is the write half
that pairs with the demo-KV retrieval necessity (PHASE4_DEMO_RETRIEVAL).
