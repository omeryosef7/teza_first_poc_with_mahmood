# P6 — Jacobian / projection-matrix readout (concept vs refusal)

**Status: ✅ COMPLETE for clearharm** (job `732004`, n = 44 train / 42 test, both targets, all three
conditions, `final_prompt` + `probe_last` positions). Curated cohort (`732011`) running for cross-cohort
replication. This is the phase the master plan (§5 P6, granularity B7) had prepped but never executed until
2026-08-07.

**What it measures.** For each layer L, the local linear map (Jacobian) from a residual-stream perturbation
at L to a target scalar, computed by autograd rooted at `inputs_embeds` (no `[n_params]` grad buffer). Two
targets, never merged:
- **concept** = `mean logit(concept surface forms) − mean logit(codeword forms)` at the final prompt token
  (the same logit-diff metric as `48_attribution_patching`).
- **refusal** = `⟨hidden_states[32][−1], unit(refusal_direction_L31)⟩` (the `phase_refusal_projection.py`
  readout).

Reported next to the **plain** per-layer projection of the same targets, so the *causal* lens (Jacobian
norm ‖J‖ = how much the scalar moves if you perturb layer L) and the *readout* lens (projection = how
linearly readable the scalar is at L) share one table.

**Harness self-checks (both passed):** `hs_index_check_maxabs = 0.0` (acts[L] aligns with
hidden_states[L+1] exactly); **Taylor gate median ratio = 0.941** (the layer-L Jacobian predicts the true
finite-difference response to within ~6% — the local linear approximation is sound). `fits_nothing = True`
(a gradient needs no training, so train and test are one pass).

---

## 1. Headline — the causal lens peaks MID-BAND, the readout lens peaks LATE (both targets)

Doublespeak condition, `final_prompt` position:

| target | peak ‖J‖ (causal sensitivity) | peak \|projection\| (readout) |
|---|---|---|
| **concept** | **L16** (train) / **L12** (test); top layers L12–L17 | **L30** (both splits) |
| **refusal** | **L12** (both splits); top layers L10–L14 | **L30** (both splits) |

- **Concept:** causal sensitivity is concentrated in the **L12–L17 write/early-carry band** (train top-5
  L16/L15/L17/L0/L14; test top-5 L12/L13/L15/L14/L16), while linear *readability* peaks at **L30**. This is
  the **same "readout ≠ mechanism" dissociation Phase 8 found by projection, now reproduced by an
  independent gradient method** — the layer where the concept scalar is most *manipulable* is not the layer
  where it is most *readable*.
- **Refusal:** causal sensitivity peaks at **L12** (top layers L10–L14 — the L8–11 concept-write band where
  Doublespeak suppresses refusal), while refusal readability peaks at **L30**.

**Independent corroboration that Doublespeak suppresses refusal.** The refusal *scalar itself* (S =
projection at hs32) drops sharply under Doublespeak vs the matched direct-harmful prompt, in both splits:

| condition | refusal S (train) | refusal S (test) |
|---|---|---|
| direct | 65.3 | 65.5 |
| **doublespeak** | **29.1** | **27.5** |
| neutral | 42.6 | 41.9 |

DS sits far below direct and below neutral — the same ordering the projection harness (§8.5 of the sprint
summary) reported, now recovered from a completely separate code path.

---

## 2. Relation to the pre-registered predictions

| prediction (plan §5 P6 / `run_jacobian.sh` header) | outcome |
|---|---|
| concept Jacobian peaks at the causal band (L9 / L14–21) | **MET (approx):** ‖J‖ peaks L12–L17, straddling the write and early-carry bands |
| refusal Jacobian peaks L16–22 | **PARTIAL:** the projected Jacobian `jac_proj` peaks **L22–L26** (as predicted), but the raw ‖J‖ peaks earlier at **L12** — see the caveat below |
| concept Jacobian behaviorally inert; refusal Jacobian predicts held-out ASR | **NOT YET TESTED** — this is a join of the per-item Jacobian with the ASR outcomes (analogous to the item-level `REP_PREDICTS_BEHAVIOR` analysis) and is the P6 follow-on |

---

## 3. Honest caveats

- **‖J‖ is a partly-generic sensitivity profile.** The raw Jacobian norm peaks at **similar mid layers
  (~L12) for BOTH the concept and the refusal target**, and the cosine of the Jacobian with the semantic
  directions is small (`cos_jac_concept` peaks at only ~0.030, `cos_jac_refusal` ~0.015). So a large part of
  the mid-band ‖J‖ peak reflects a generic "mid-layer gradients are larger" profile rather than a clean
  per-target localization. The **target-specific** signal lives in `jac_proj` (the Jacobian projected onto
  the target direction) and in the projection curves, which is why the concept-vs-refusal *readout*
  dissociation (mid-band causal vs L30 readout) is the load-bearing result, not the bare ‖J‖ peak.
- **No inferential test on the peak layer yet.** The peaks are argmax of point estimates over 32 layers;
  the per-layer `grad_norm` carries a bootstrap `[lo,hi]` but a formal "peak is in the mid-band" test
  (e.g. bootstrap the argmax, or a mid-vs-late contrast) is not yet run.
- **clearharm only so far;** curated replication (`732011`) pending. Single model (Llama-3.1-8B-Instruct).
- The behavioral-prediction arm (does the refusal Jacobian predict which items jailbreak while the concept
  Jacobian does not?) is the decisive dissociation test and has **not** been run — it needs a join with the
  `behav_refusal` ASR outcomes.

---

## 4. Reproduce

```
sbatch --export=ALL,DSN=0 --nodelist=n-501,n-502,n-503,n-802,n-803,n-804,n-805,t-806 \
  doublespeak_causality/slurm/run_jacobian.sh                 # clearharm
sbatch --export=ALL,DSN=0,DSCOHORT=curated,DSBENCH=doublespeak_causality/data/behavioral/beh_curated.json \
  --nodelist=... doublespeak_causality/slurm/run_jacobian.sh  # curated
```
Output: `outputs/jacobian_clearharm_20260807_132150_732004/` (summary.json + raw.jsonl + RUNMETA + DONE).
Per-layer curves are in `summary.json → by_split_condition[<split>|<cond>].by_position.<pos>.<target>.per_layer`
(`grad_norm` = ‖J‖, `jac_proj` = Jacobian·direction, `proj_concept/refusal/signature` = plain readouts).
