# reports/PHASE8_READOUT.md — Concept-readout emergence across layers (descriptive)

**Question (plan Phase 8):** where does the harmful concept become LINEARLY readable in the residual
stream, and does that emergence coincide with the causal circuit (L9 write, L14–21 carry)?

## Method
`scripts/phase8_readout.py` (CPU; reuses the extracted Llama reps + the unified per-layer concept
direction). Per layer L, at the answer/readout position (final prompt token), the linear concept readout
is `emergence[L] = (mean(DOUBLESPEAK resid_post)[L] − mean(NEUTRAL resid_post)[L]) · unit(concept_dir[L])`.
dev/heldout separate; both cohorts. This is a linear "lens" — a READOUT, not a cause.

## Result — linear readability emerges LATE (peak L31), dissociated from the causal loci

| cohort/split | onset (50% of max) | peak | proj@L9 (frac of max) | @L14 | @L21 |
|--------------|--------------------|------|------------------------|------|------|
| curated dev      | L31 | L31 | −0.07 (−0.09×) | 0.08 (0.10×) | 0.15 |
| curated heldout  | L31 | L31 | −0.07 (−0.16×) | 0.07 (0.16×) | 0.10 |
| clearharm dev    | L31 | L31 | 0.01 (0.01×)   | −0.08 | 0.12 |
| clearharm heldout| L31 | L31 | −0.01 (−0.01×) | −0.08 | 0.20 |

- **The linear concept projection grows monotonically and peaks at the LAST layer (L31)** on all cells;
  at the causal write layer L9 it is ≈0, and only ~10–16% of its maximum by L14.
- So **where the concept is linearly READABLE (late, L31) ≠ where it is causally WRITTEN/CARRIED (L9 / L14–21).**

## Interpretation
- The late-peaking linear readout is the residual **accumulating** the concept toward the unembedding — the
  classic readout-proximity pattern (same as the Phase-6 MLP *projection* artifact). It is mechanistically
  CONSISTENT with the causal circuit: written at L9 (demo) → carried by L14–21 answer-position heads →
  accumulated into the final residual, becoming linearly readable only by ~L31.
- **This confirms the plan's central methodological point:** a naive logit-lens / linear-projection readout
  is DESCRIPTIVE and misleads about mechanism — its emergence layer (L31) reflects proximity to the
  unembedding, not the causal write. This is precisely why the causal interventions (edge-KO, MLP patching,
  head z-patching, path patching), not the readout, were used to localize the circuit. "Jacobian readout is
  descriptive until intervention in the corresponding coordinate changes output" — here it does not.

## Caveats / next
- A per-layer TUNED linear lens (Jacobian of the concept-vs-codeword logit w.r.t. each layer's residual)
  would sharpen the readout but cannot change the descriptive→causal gap; the causal localization stands
  on the interventions. Available as a refinement if needed.
- Emergence measured at the final-prompt position (the readout site); the demo-codeword-position emergence
  is the write site (Phase 6) and is small/mid-band, consistent with the above.

Reproduce: `python scripts/phase8_readout.py --reps-dir <llama pair_reps> --cohort <curated|clearharm>`.
