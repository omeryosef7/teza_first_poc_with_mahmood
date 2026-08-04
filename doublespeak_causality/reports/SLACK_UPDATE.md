# Doublespeak causal-circuit sprint — status (2026-08-04)

**TL;DR (headline, updated Aug 4):** We mapped the full concept circuit **and** then tested whether it
actually drives the jailbreak — it does **not**. **The Doublespeak jailbreak is, mechanistically, an
imperfect in-context *refusal-suppression* technique; the elaborate token→concept remap is behaviorally
epiphenomenal.** Two independent behavioral experiments (both cohorts, locked splits, StrongREJECT-judged,
paired McNemar, count-matched controls):
- **Concept circuit → behaviorally NULL.** Ablating the components that are necessary+sufficient for the
  concept *readout* (L8–11 demo write; L14–21 carry heads) throughout harmful generation leaves ASR
  statistically unchanged.
- **Refusal axis → behaviorally NECESSARY + SUFFICIENT.** Ablating one (orthogonal, cos≈0.03) refusal
  direction turns a refusing model into a complying one (ASR +0.43–0.48, every split p≤0.004) and is a
  *stronger* attack than Doublespeak itself; and re-injecting it *into* Doublespeak drives ASR→**0.000**
  (dose-dependent, axis-specific, generations verified as coherent refusals).
- **Defense implication (sharp):** monitor/scrub the **refusal** axis, not the concept subspace — the
  latter is causally disconnected from compliance.

Detail: `reports/PHASE_BEHAV_REFUSAL.md` (+ `_CARRY`/`_WRITE`), folded into `FINAL_CAUSAL_CIRCUIT_REPORT.md`.

---

**Earlier status (Aug 3 — representational circuit):** New locked ClearHarm split + curated replication
cohort built; the Doublespeak attack and its representational structure reproduce; and the retrieval
mechanism is now pinned on the new data with matched controls: **the demonstration-codeword content is
causally necessary in the L8–11 mid-band (significant on both cohorts) but NOT sufficient, and NOT carried
by a surgical query→demo attention edge — it's a distributed, context-bound binding.** All on Llama-3.1-8B
bf16, forced-choice readout, paired bootstrap CIs, both cohorts.

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
- The representational claims are forced-choice (DE_context) readout. **Behavioral-generation confirmation
  is now DONE** (BEHAV-* above) — and it revealed the concept cells are behaviorally inert while refusal is
  the causal locus. That is the sprint's main scientific result.

## Next
Behavioral causal frontier is complete (concept null ×2, refusal necessary+sufficient, coherence-audited).
Remaining is consolidation/write-up: unify the representational circuit (retrieval→write→carry→readout) with
the behavioral dissociation into the paper narrative. Optional deeper probes: refusal-axis onset layer for
the injection, and whether Doublespeak's *partial* refusal suppression is what makes it weaker than direct
ablation.

Full detail: `reports/PHASE2_*`, `PHASE3_RESIDUAL`, `PHASE4_DEMO_RETRIEVAL`, `PHASE6_MLP`,
`FINAL_CAUSAL_CIRCUIT_REPORT`. Tracking: `IMPLEMENTATION_PROGRESS.md`.
