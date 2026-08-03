# Doublespeak causal-circuit sprint — status (2026-08-03)

**TL;DR:** New locked ClearHarm split + curated replication cohort built; the Doublespeak attack and its
representational structure reproduce; and the retrieval mechanism is now pinned on the new data with
matched controls: **the demonstration-codeword content is causally necessary in the L8–11 mid-band
(significant on both cohorts) but NOT sufficient, and NOT carried by a surgical query→demo attention
edge — it's a distributed, context-bound binding.** All on Llama-3.1-8B bf16, forced-choice readout,
paired bootstrap CIs, both cohorts.

## What's done
- **Data (Phase 1):** `data/splits/clearharm_doublespeak_v1.json` — 137 examples, 2 cohorts, both ≥20/≥20
  (ClearHarm-native primary 86; curated harm-in-one-noun replication 51). Validator: 0 FATAL (no
  id/cluster/prompt leakage, all single-token). Reproducible (cached gpt-4o-mini gen).
- **Behavioral (Phase 2.1):** Doublespeak reproduces. ClearHarm doublespeak malicious 0.35 vs direct
  0.12 (refusal bypass); curated isolates it cleanly (neutral floor 0.04 → DS 0.33 on train, +0.30).
  Curated *test* weak (n=21) — flagged.
- **Directions (Phase 2.2):** concept ⊥ refusal at every layer (mean cos 0.01/0.06) — separate levers.
  concept ≠ doublespeak-signature (dissociation replicates).
- **Local state (Phase 3):** patching the query-codeword resid_post is neither necessary nor sufficient
  (IE_state ≈ 0) — reproduced on the new split.
- **Retrieval (Phase 4.2):** demo-codeword K/V neutralization reduces the reading, **significant in the
  mid band both cohorts** (curated early +0.26 [.15,.37], mid +0.18 [.09,.28]; clearharm mid +0.08
  [.01,.15]), **per-layer significant L8–L11**, peak L9–10. **Not sufficient** (installing into benign
  ⇒ p_concept ≈ 0). **Query→demo attention edges NOT necessary** (band knockout ns both cohorts) →
  distributed, not a surgical induction edge. Resolves the old N7-M ambiguity (clean negative w/ controls).
- **MLP (Phase 6, representational):** concept-projection is late-dominated (L29–31) = readout-proximity
  artifact, NOT the causal write (per plan warning + prior AtP mid-band). Causal MLP patching next.

## Headline science
The Doublespeak binding is **distributed and context-bound**: the demonstration content is causally
necessary in the L8–11 mid-band, but no single head, no local codeword state, and no specific query→demo
edge is the bottleneck. This generalizes the prior carrot↔bomb mid-band retrieval to a multi-concept
ClearHarm dataset with matched-control necessity + sufficiency tests — and adds a clean negative
(the 3.5× query→demo attention *pattern* is not causally load-bearing).

## Honest caveats
- ClearHarm-native concepts are noisier (harm not always in one swapped noun) → its effects are weaker /
  sometimes ns; the clean **curated** cohort carries the significant claims, ClearHarm corroborates direction.
- Curated test split is small (n=21).
- Results are forced-choice (DE_context) readout; behavioral-generation confirmation of the decisive
  causal cells is a remaining step.

## Next
Causal MLP write (mid-band, intervention) → head→MLP path → concept-direction dose-response →
(only if a signal passes the causal gate) GCG/MAC objective. Prior priors (temporal objective backfires,
d_DS inert) mean the objective/GCG phases are at genuine risk of null — will be reported as such.

Full detail: `reports/PHASE2_*`, `PHASE3_RESIDUAL`, `PHASE4_DEMO_RETRIEVAL`, `PHASE6_MLP`,
`FINAL_CAUSAL_CIRCUIT_REPORT`. Tracking: `IMPLEMENTATION_PROGRESS.md`.
