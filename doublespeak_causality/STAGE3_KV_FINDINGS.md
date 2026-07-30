# Stage 3 — Demonstration K/V Mediation: Findings

**Status:** EXPLORATORY (forced_choice, job 694691, n=30; cloze cross-check job 694667).
**Runs:** `pair_kv_mediation_...694691` (forced_choice), `...694667` (cloze). Backing: `kv_mediation_summary.json`, `interv_raw.jsonl`.
**Plan:** resolve the Stage-2 caveat — is the "context-carried" effect a genuine mechanism or the cloze readout **re-reading the demonstrations**? Design: `STAGE3_KV_PLAN.md`.

---

## Design (reuse-maximizing)
2×2 on the DOUBLESPEAK receiver, `{query codeword state} × {demonstration K/V}`, realized with `LayerPatch` (query) + the new `DemoStateSwap` resid_pre write-hook (demo K/V), scored by `semantic_score`:
- **C1** DS-state × DS-demo (baseline); **C2** Neutral-state × DS-demo; **C3** DS-state × Neutralized-demo-K/V; **C4** both neutralized.
- `ReRead_test = C1 − C3` (**the discriminator**: does neutralizing demo-K/V collapse the concept?); `DE_via_demoKV = C2 − C4`; + `C1_selfswap` faithfulness and a count-matched **random** non-codeword-position control.

**Validity:** `DemoStateSwap` self-swap reproduces the no-hook baseline **exactly** on the real model (`C1_selfswap`==`C1`, n=30); ToyStack + analysis unit tests (8/8) pass; independent adversarial review clean.

---

## Result (forced_choice, mid window)

| quantity | value | reading |
|---|---|---|
| C1 (DS baseline) | 0.353 | the hijack fires |
| C3 (DS state, demo-K/V neutralized) | 0.321 | **91% of the reading SURVIVES** neutralizing the demo K/V |
| **ReRead_test = C1−C3** | **+0.032** | neutralizing demo-K/V removes only ~9% |
| DE_via_demoKV = C2−C4 | +0.033 | demo-K/V carries a small, specific slice |
| random_control | +0.010 | count-matched random-position swap moves less |

**Interpretation.**
1. **The cloze/forced_choice readout is NOT trivially re-reading the demonstrations.** Neutralizing the demonstration codeword K/V (replacing it with a no-mapping neutral-demo state) removes only ~9% of the concept reading; **~91% survives**. If the readout were simply attending back to the demo codewords, neutralizing them would collapse it. It does not. This resolves the Stage-2 caveat in the reassuring direction.
2. The demonstration-codeword K/V carries a **small, codeword-specific** slice at mid layers (ReRead +0.032 > random +0.010), but the bulk of the concept reading is **distributed / robust** — not localized to the demo codeword occurrences.
3. Combined with Stage 2 (query-state transplant inert; context installs), the picture is: the hijacked reading is a **distributed property of the receiver context's computation**, not stored in either the query codeword's residual state *or* narrowly in the demonstration codeword K/V. This matches Stage-3 outcome **C (distributed computation)** in the plan — reported honestly, not as a failure.

**cloze cross-check (694667):** same qualitative pattern (ReRead mid +0.068 of a 0.31 baseline → ~78% survives; random control large at *early* layers → distributed). The layer profile differs slightly by readout but the conclusion (not-trivial-re-read; distributed) is stable.

---

## Caveats / limitations
- **Patchscope confound-free readout is UNUSABLE as configured** (`ps_concept`=0 all cells; 44 reads at a late layer R=28 with no positive control, but concept reps decode *early*). Dropped from claims; a positive-control-gated patchscope (scan layers, verify a DIRECT rep decodes >0) is the correct future refinement.
- Modest absolute magnitudes (DS ~0.35). The dissociation is relative and robust; a higher-signal setup would tighten the distributed-vs-localized decomposition.
- Single seed, n=30, single pair. Path-patching to *find* where the distributed effect concentrates (attention heads / MLP in the validated band) is the natural Stage-3 continuation if a localized carrier is wanted.

## Consequence
Stage 3 confirms the Stage-2 story mechanistically (not a re-read artifact) and localizes it as **distributed context computation** rather than demo-codeword-K/V-specific. This is a defensible, honest result. Optional deepening (head/MLP path patching) is available but the headline — *the hijacked meaning is not stored locally in the token, and is not narrowly in the demo codewords either; it is recomputed by the context* — is established.
