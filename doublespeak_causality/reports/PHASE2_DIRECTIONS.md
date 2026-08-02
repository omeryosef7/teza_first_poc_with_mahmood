# reports/PHASE2_DIRECTIONS.md — Phase 2.2 Separate Concept / Refusal / Signature Directions

Three **separate** per-layer direction families (never merged), on the locked split
(`data/splits/clearharm_doublespeak_v1.json`), Llama-3.1-8B-Instruct bf16.

- **concept_direction[L]** = mean(DIRECT_CONCEPT) − mean(NEUTRAL_CODEWORD)  (`d_Direct`)
- **doublespeak_signature[L]** = mean(DOUBLESPEAK) − mean(NEUTRAL_CODEWORD)  (`d_DS`, NOT a concept direction)
- **refusal_direction[L]** = independent harmful/refused vs harmless/compliant (last-token, all 32 layers)

Position `resid_post/codeword_last`, cross-fit `dev` (train-derived). Artifacts:
`outputs/unified_directions/{clearharm,curated}.{npz,json}`; concept/signature from
`33_build_directions` (reps jobs 702731/702692), refusal from job 702750 (`build_refusal_direction_llama`,
bench pair_carrot_bomb 60 harmful / 20 harmless).

## Headline — concept and refusal are ORTHOGONAL at every layer (both cohorts)

| metric | clearharm (PRIMARY) | curated (REPLICATION) |
|---|---|---|
| mean cos(concept, refusal) | **0.012** | **0.061** |
| max\|cos(concept, refusal)\| over L0–31 | 0.078 | 0.153 |
| mean cos(signature, refusal) | 0.127 | 0.151 |
| mean cos(concept, signature) | 0.245 | 0.138 |
| refusal-separation peak layer | L23 | L23 |

**Interpretation.** The harmful-**concept** axis is ~orthogonal to the **refusal** axis across
all 32 layers on both cohorts (|cos| ≤ 0.15 everywhere) → they are **independent levers**. This
justifies the plan's core rule to keep concept and refusal as distinct objects and never merge
them, and separates "installing the harmful concept" (Doublespeak's job) from "bypassing refusal."
The **doublespeak_signature** is a bit closer to refusal than the concept is (cos ~0.13–0.15) and
only partially aligned with the concept (cos 0.14–0.25) — consistent with the concept↔signature
**dissociation** (`d_DS` is not the concept direction).

## Refusal is concentrated mid-late, not uniform
Per-layer refusal separation (harmful vs harmless projection) rises 0.33 (L0) → ~1.03 (L20–23)
→ 0.94 (L31); |cos(concept,refusal)| stays ≈0 throughout. So refusal information concentrates in
L16–27 while the concept axis remains a separate direction at every depth. (Whether refusal is
*causally* concentrated vs distributed is a separate intervention experiment — Phase 2.2 refusal-
granularity sweep — not settled by this representational separation alone.)

## Status / caveats
- Representational only. Causal effects (adding/removing each direction per layer, dose-response)
  are Phase 3/9 — a large projection or orthogonality is descriptive until intervention validates it.
- Refusal bench = pair_carrot_bomb (proven, sep 0.92 at L16); a ClearHarm-native refusal bench is a
  possible v2 but the refusal axis is model-general, not concept-specific.
- Covariance-adjusted (whitened) similarity is a listed plan output not yet computed here (raw cosine
  + norms only) — queued.
- `heldout` split directions also built (for frozen confirmatory use); numbers above are `dev`.
