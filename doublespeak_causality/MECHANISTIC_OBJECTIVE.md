# Mechanistic Objective — does the temporal signature predict jailbreak success?

**Deliverable (plan §23, Workstream E / Phase 5).** Tests whether the "benign-early / harmful-late"
mechanistic signature *predicts* which Doublespeak prompts behaviorally jailbreak (DS_MALICIOUS) —
the prerequisite for a mechanism-derived attack objective (Phase 6). Benign scalar analysis.
Model: Llama-3.1-8B; curated benchmark; 240 conditions, 46 DS_MALICIOUS. Scripts: `21` (features),
`22` (predictors). Raw: `outputs/features_llama8b/`.

---

## 1. Candidate features (plan §9.1)
Per DS prompt, from the codeword-rep trajectory: alignment[l] = cos(DS_rep[l] − Neutral_rep[l], d[l]),
where d[l] = train-split mean(Direct_rep − Neutral_rep) per layer (a validated contextual-harm axis).
Features: `early_align`, `mid_align`, `late_align` (mean over layer thirds), `early_to_late` (late−early),
`onset_layer`, `peak_align`, `argmax_layer`, `auc_align`.

## 2. Predictive evaluation (plan §9.2) — DOES it predict?

| predictor | AUC (predicting DS_MALICIOUS) |
|---|---|
| early_align | 0.651 |
| mid_align | 0.657 |
| **early_to_late** (late−early) | 0.654 |
| **temporal objective** (late − λ·early) | 0.654 |
| onset_layer | 0.606 |
| auc_align | 0.609 |
| late_align (alone) | **0.502** (no signal) |
| peak_align (alone) | 0.517 (no signal) |
| **multivariate 5-fold CV** | **0.732 ± 0.060** |
| **HELD-OUT-CONCEPT (generalization)** | **0.668 ± 0.089** |

**Verdict — Level 4 achieved (moderately).** The mechanistic temporal signature predicts held-out
behavioral jailbreak success (held-out-concept AUC **0.668**, above chance; multivariate CV 0.73).

**The predictive component is EARLY, not late.** `late_align` alone carries no signal (0.502); the
predictive features are the **early alignment** and the **early→late change**. Prompts whose codeword is
*less* aligned with the harmful direction *early* are more likely to jailbreak. This is exactly what the
TOCTOU timing law (Claim D) predicts: **low early harmful alignment = evades the early refusal check =
jailbreaks.** So the mechanistic predictor and the causal timing law tell the same story from two
directions (correlational + causal).

## 3. Causal support (plan §9.4)
The predictive feature (early alignment) is *causally* linked to behavior via the timing experiment:
injecting harmful meaning early → refusal (0.86); late → compliance. So "keep early alignment low" is not
merely predictive — the causal timing law explains *why* it should work as an attack objective.

## 4. Candidate objective for Phase 6 (GCG/MAC)
J = late_harmful_align − λ·early_harmful_align  (benign-early / harmful-late), realized as a layer-weighted
`repr_loss` in `poc_stage_gcg_early/objectives.py` (already exists — see Phase 6 pre-audit). Given §2, the
**early-suppression term (−λ·early_align) is the load-bearing part**; the late term alone is inert.

## 5. Honest limitations
- Predictive power is **moderate** (held-out AUC 0.67, not 0.9) — the signature predicts but does not
  determine success; other factors (concept, codeword, generation stochasticity) matter.
- Single model (Llama-8B), single direction construction (Direct−Neutral mean). A low-rank subspace and a
  second model are pending.
- The objective's *utility* is only established when Temporal-GCG/MAC **improves held-out behavioral ASR**
  vs standard GCG/MAC (Phase 6) — predictive ≠ optimizable-with-gain. Not yet claimed.
