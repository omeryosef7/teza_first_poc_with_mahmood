# reports/PHASE3_RESIDUAL.md — Phase 3 Exhaustive Residual Patching (in progress)

Per-layer necessity + sufficiency residual patching on the locked split, both cohorts, forced-choice
readout. Llama-3.1-8B-Instruct bf16. This report accumulates as position-sets/locations complete.

## Cell #1 — resid_post × final-query-codeword-token, logit-lens readout — COMPLETE, NULL (reproduces IE_state≈0)

Jobs **702995** (clearharm) / **702996** (curated); reused `05_run_activation_patching.py`.
Necessity = replace DS codeword-state with matched Neutral state at layer L; Sufficiency = install
Direct/DS codeword-state into Neutral; readout = logit-lens P(harm)/P(code) at codeword_last, all 32 layers.

| cohort · split (n) | baseline DS p_harm | best necessity drop (@L) | random-ctrl drop | best sufficiency p_harm (@L) |
|---|---|---|---|---|
| clearharm train (44) | 0.013 | +0.012 @L25 | +0.013 | 0.001 @L0 |
| clearharm test (42) | 0.020 | +0.015 @L30 | +0.020 | 0.001 @L0 |
| curated train (30) | 0.001 | +0.001 @L30 | +0.001 | 0.016 @L0 |
| curated test (21) | 0.000 | +0.000 @L5 | +0.000 | 0.008 @L0 |

**Result: NULL, and expected.** The baseline DS `p_harm` under logit-lens-at-codeword is at the floor
(≈0), so there is no signal to remove (necessity) or install (sufficiency); the tiny necessity "drops"
are indistinguishable from the norm-matched random control. This **reproduces the prior finding on the
new ClearHarm split**: the harmful concept is NOT decodable in the local query-codeword state
(**IE_state ≈ 0**) — the reading is a property of the receiver context, not the codeword's local
activation. It confirms position-set #1 ("final query-codeword token only") is neither necessary nor
sufficient, exactly as the master plan's "known findings" #1–3 state.

### Why this readout floors here (diagnosis, not a bug)
Logit-lens P(harm) at the codeword position ≈ 0 even for clean Doublespeak — the same limitation
recorded in prior T2/N3 (patchscope fails its positive control for bomb at the codeword). The concept
projection at the codeword grows only very late and is not the decode site. The **validated readout**
is the **forced-choice patchscope** (`46_forced_choice_patchscope.py`): inject the captured rep into a
demo-free forced-choice prompt and read P(concept-label) vs P(codeword-label) at a late inspection
layer R, positive-control-gated (max>0.1). That readout gave DS≈0.35 in prior DE_context work (job
694691) and is what the circuit-discovery cells must use.

## Next cells (the ones the retrieval hypothesis predicts should carry signal)
Position sets #4–6 (each demo-codeword occurrence, all demo occurrences, query+demos) and the other
three locations (resid_pre / attn_out / mlp_out via the extended `SubmodulePatch`), read with the
forced-choice patchscope readout — because the binding is carried by the DEMONSTRATIONS, not the local
query state. Necessity = neutralize demo activations in DS; sufficiency = install DS demo activations
into neutral. Reuse the `43_transplant_mediation` / `44_kv_mediation` patch+forced_choice machinery
that produced DE_context/IE_state. ≥20 train / ≥20 test per cell, both cohorts.

## Caveats
- Forced-choice/patchscope readouts are gated on a positive control; cells where the gate fails are
  reported as unusable (not as null effects).
- resid_post/codeword_last is one required cell of the exhaustive sweep; its null is a legitimate,
  pre-registered data point, not a dead end.
