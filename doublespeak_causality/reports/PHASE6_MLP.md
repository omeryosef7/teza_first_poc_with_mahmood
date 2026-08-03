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

## Causal MLP write — DEMO codeword L9 (mid-band L9–L12) necessary [Holm]; QUERY codeword inert

**Method.** `scripts/phase6_mlp_causal.py` (exact intervention, not projection): patch DS `mlp_out` ←
matched BENIGN `mlp_out` at codeword positions, per layer, FC DE_context readout, paired sign-flip
permutation p-values **Holm-corrected across all 32 layers**, dev(train)/heldout(test) reported SEPARATELY,
self-swap = exact no-op (dev 0.0), random-non-codeword-position control. `--positions {demo,query}`
distinguishes the demonstration codewords (n=12/prompt) from the query codewords in the FC question
(n=2/prompt) — after fixing a token-index-vs-char-offset classification bug that had merged them.
Clean per-layer jobs 703531/703532 (demo) + 703533/703534 (query), both cohorts. Primitive
`pc.ComponentOutSwap` (per-position mlp/attn-output swap; 4/4 synthetic tests; code-reviewed clean).

**DEMO codeword — necessity, Wilcoxon signed-rank, Holm-corrected across 32 layers (specific =
random_control − C3).** *(Statistics corrected 2026-08-03 audit: switched from a sign-flip permutation —
RNG-order-dependent + resolution-limited — to Wilcoxon, which is robust to the strong right-skew of the
necessity diffs. The paired t-test is over-conservative here because a few strong-concept examples dominate
the mean; Wilcoxon and the properly-resolved permutation agree. L9 survives on all four cells under both.)*
- curated dev: **L9 +0.049 [.021,.082]** (also L5, L12, L20) — survive Holm.
- curated heldout (locked test): **L9 +0.097 [.040,.166]** — survives Holm (the only layer).
- clearharm dev: **L9 +0.063 [.023,.115]** (also L11 +.017, L12 +.018) — survive Holm.
- clearharm heldout (locked test): **L9 +0.015, L10 +0.009, L11 +0.013, L12 +0.006** (also L5, L13) — the
  **L9–L12 band survives Holm** on this cell.
- → **L9 is the one layer significant on ALL FOUR cells** (both cohorts × train+test). The broader L9–L12
  band survives on clearharm heldout; L10 is split-dependent (clearharm heldout yes, clearharm dev no). Same
  band as the demo-KV retrieval necessity (PHASE4, L8–11 peak L9–10): the MLP write and the K/V retrieval
  **co-localize at L9 on the demonstration codeword**.

**Sufficiency ≈ 0 at every layer** (installing DS `mlp_out` into benign does NOT create the reading) →
necessary but **not sufficient**, mirroring demo-KV. Effect sizes are **small** (~0.02–0.10): L9 is one
contributor in a distributed set, not a dominant sufficient write.

**QUERY codeword — NOT robustly necessary.** After Holm: curated heldout = **nothing survives**; clearharm
dev/heldout = **nothing survives** (only curated dev shows tiny L11/L20). → the MLP output at the QUERY
codeword is essentially inert, consistent with the query-codeword *local state* being inert (Phase 3 /
iter-13, IE_state≈0). **The concept-binding MLP write is at the DEMONSTRATION codeword (where the binding is
defined), not at the query codeword (where it is used).**

**Confound resolved.** The broad canonical `early` WINDOW (L0–9 jointly) gave a large necessity (+0.42) with
NEGATIVE sufficiency (−0.18) = broad-intervention degradation. The per-layer Holm analysis isolates the
real, small, replicating driver at L9; the window number is degradation, not the effect size.

**Gate 4:** an MLP at L9 (mid-band L9–L12) contributes causally at the demonstration codeword (necessity,
both cohorts, locked-test replication, 32-layer Holm, matched controls, self-swap 0) — a small,
necessity-only, non-sufficient, distributed contribution; the query-codeword MLP is inert. Answers plan
Q5 (binding first causally available ≈ L9) and Q6 (which MLP writes ≈ L9 demo-position, distributed L9–L12).

Reproduce: `python scripts/phase6_analyze.py <output_dir>` (per-split + Holm).
