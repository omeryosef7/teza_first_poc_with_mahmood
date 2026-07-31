# NEXT6 — Findings ("all new directions")

Plan: `NEXT6_PLAN.md`. Env: Llama-3.1-8B / Qwen3-14B / Phi-4 / DeepSeek, L40S, poc_stage2,
forced_choice. Honest — negatives included. Scalars only; no harmful text in any artifact. Single
Holm family across all new NEXT6 inferential claims (assembled at the end).

---

## D6 — Unified depth timeline: superposition + circuit + TOCTOU as one story. **[WIN, synthesis]**

Reusing three committed artifacts (W3-b per-layer projections, W4-B z-AtP by layer, T3 refusal
depth) — no GPU — the Doublespeak mechanism resolves into a single depth timeline on bomb/Llama
(`next6_d6_depth_story.py`, `outputs/next6_depth_story.json`):

- **Codeword-first, concept-lagging superposition.** The codeword component leads (present from
  L2: codeword@L2–6 = +0.28 vs concept@L2–6 = +0.15) and both grow together thereafter — the rep
  carries the codeword identity from the start and the harmful concept accretes on top, exactly the
  superposition picture (W3-b), now resolved across depth.
- **TOCTOU as a monotonic concept-emergence gradient [the key quantitative result].** The concept
  component at the EARLY refusal-check depth (bomb's check is early, T3) is **+0.183** (L0–9 mean);
  at the LATE use depth it is **+4.124** (L20–end mean) — a **22.5×** gradient. So the refusal check
  reads a residual in which the harmful concept is ~22× weaker than where it is finally used: the
  codeword still "looks benign" when checked, and the concept only fully materializes downstream.
  This quantifies the paper's §3.4 TOCTOU bypass as a clean, monotonic depth gradient (not just an
  early/late binary), and mechanistically explains why the early-gated refusal is bypassed.
- **Attention writes the context-link mid-band (L7–14, peak L9 = 61.7% of Σ|AtP|)** — where heads
  causally move the demonstration context into the query's readout path (W4-B).
- **Honest nuance — write-band and concept-growth are DECOUPLED.** The attention WRITE band (mid)
  does NOT coincide with where the concept PROJECTION grows fastest: corr(z-AtP write[L], concept
  emergence[L→L+1]) = **−0.30** (excl. the mechanical readout jump). The concept projection rises
  fastest LATE (near the unembedding), after the attention writes have tapered. Interpretation: the
  mid-band attention establishes the demo→query context LINKAGE (consistent with S2 "context
  supplies the reading"), but the concept REPRESENTATION keeps accumulating downstream through the
  residual/MLP stream — the causal write and the readable projection live at different depths. We
  report this rather than force a "they align" story.
- **Synthesis:** one timeline unifies all four results — S2 (context supplies the reading
  progressively, not stored locally early), superposition (codeword+concept coexist, codeword-first),
  the mid-band distributed circuit (where attention links context), and TOCTOU (early check sees
  concept ≈0.18, late use sees ≈4.1 → 22.5× bypass gradient).
- Artifact: `outputs/next6_depth_story.json`. Code: `next6_d6_depth_story.py`.

---

## D2 — Superposition generalization: bomb-specific but CROSS-ARCHITECTURE. **[nuanced / honest]**

Ran `next5_w3b_superposition.py` on grenade/chlorine/pistol (Llama, fixed band L12–24) and bomb on
Qwen3-14B (band L15–30, proportional). DS-specific = DS concept component above the benign-remap
control (the load-bearing superposition claim).

| pair / model | DS loads both? | DS−BENIGN concept [CI] | DS-specific? |
|---|---|---|---|
| **bomb / Llama** | yes | **+0.555 [+0.26,+0.87]** | **YES** |
| **bomb / Qwen3-14B** | yes | **+8.96 [+6.39,+11.63]** | **YES (cross-arch)** |
| grenade / Llama | yes | +0.078 [−0.23,+0.38] | no |
| chlorine / Llama | yes | −0.118 [−0.48,+0.26] | no |
| pistol / Llama | yes | −0.176 [−0.51,+0.16] | no |

- **Co-loading is universal:** every pair's DS rep loads BOTH the codeword and concept axes (both
  CIs exclude 0) — the basic superposition geometry is general.
- **DS-specific concept elevation is a BOMB property that CROSSES ARCHITECTURES.** Only bomb shows
  the concept component elevated above the benign-remap control — and it does so on **both** Llama
  (+0.55) and Qwen3-14B (**+8.96**, even stronger). For grenade/chlorine/pistol the DS concept-axis
  loading is statistically indistinguishable from a benign remap (all NS vs BENIGN) — i.e. the
  concept axis `d_Direct` for those pairs captures generic "codeword-is-remapped" structure that any
  remap shares, not a DS-specific harmful-concept component.
- **Honest reading:** this mirrors the recurring pattern (S4/T3) that bomb is the strongest, cleanest
  hijack — the DS-specific superposition is a bomb property, but a robust one (replicates on a second
  architecture). The non-generalization to other Llama pairs is reported honestly; a pair-specific
  band (analogous to T3's pair-dependent depths) is untested future work (avoided here to prevent
  post-hoc band-tuning / double-dipping).
- Artifacts: `w3b_superposition.json` in each pair's reps dir (`..._694882/883/884`, Qwen3 `..._695832`).
