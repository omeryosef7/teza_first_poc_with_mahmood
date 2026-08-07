# P6 — Jacobian / projection-matrix readout (concept vs refusal)

**Status: ✅ COMPLETE, both cohorts + decisive behavioral-prediction arm** — clearharm (job `732004`,
n = 44/42) and curated (job `732011`, n = 30/21), both targets, all three conditions, `final_prompt` +
`probe_last` positions; plus the per-item Jacobian→ASR dissociation (§2.5). This is the phase the master plan
(§5 P6, granularity B7) had prepped but never executed until 2026-08-07.

**Bottom line:** the refusal Jacobian sensitivity predicts which items jailbreak (AUC 0.807, 0.815 locked
test) while the concept Jacobian is behaviorally inert (AUC 0.58, CI includes chance; difference +0.225,
CI [0.055, 0.361]) — the sprint's headline dissociation restated with a gradient measure.

**Cross-cohort replication is exact on the localization and stronger on the suppression.** Curated
reproduces the concept ‖J‖ peak at **L16** (5 of 6 cells) and the refusal ‖J‖ peak at **L12** (all 6 cells,
identical to clearharm), Taylor ratio 0.957. The refusal-scalar drop under Doublespeak is even larger on
curated — **direct 66–70 → DS 9–11** (near-total suppression) vs clearharm's 65 → 28 — consistent with the
established cohort difference (curated suppresses refusal *uniformly/totally* → concept-dilution, `ds_refused
_rate = 0.000`; clearharm suppresses *unevenly* → the under-suppressed items still refuse).

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
| concept Jacobian behaviorally inert; refusal Jacobian predicts held-out ASR | **✅ MET** — see §2.5: refusal ‖J‖@L12 predicts jailbreak at AUC 0.807 (0.815 on locked test); concept ‖J‖@L16 is inert (AUC 0.583, CI includes 0.5); difference significant |

---

## 2.5 The decisive arm — the refusal Jacobian predicts jailbreak, the concept Jacobian does not

Per-item join of the Doublespeak `final_prompt` Jacobian with the `behav_refusal` `ds_base` StrongREJECT
label (`item_key == id`, exact, 86/86), `scripts/analyze_jacobian_predicts_behavior.py` →
`outputs/p6_predicts_behavior_clearharm.json`. AUC oriented ≥0.5, seeded 5 000-resample percentile bootstrap.

| per-item feature | AUC pooled | 95% CI | train | test (locked) | reads |
|---|---|---|---|---|---|
| **refusal ‖J‖ @ L12** (Jacobian sensitivity) | **0.807** | **[0.696, 0.901]** | 0.800 | **0.815** | lower refusal-sensitivity → jailbreak |
| refusal scalar (L31 projection) | 0.845 | [0.758, 0.916] | 0.845 | 0.847 | lower refusal → jailbreak |
| refusal projection @ decision L21 | 0.867 | — | 0.863 | 0.891 | reproduces `REP_PREDICTS_BEHAVIOR` (0.874) |
| **concept ‖J‖ @ L16** | **0.583** | **[0.454, 0.709]** | 0.575 | 0.593 | **inert — CI includes 0.5** |
| concept scalar (logit-diff) | 0.508 | [0.373, 0.636] | 0.597 | 0.422 | **inert — chance** |
| concept jac_proj @ L16 | 0.501 | — | 0.481 | 0.528 | **inert — chance** |

**Paired difference: refusal ‖J‖ − concept ‖J‖ AUC = +0.225, 95% CI [0.055, 0.361] — excludes 0.**

⇒ **The pre-registered dissociation holds on an entirely new axis.** Not only is the refusal *projection*
predictive of which items jailbreak (already known), but the refusal *causal sensitivity* — how much the
refusal scalar would move if you perturbed the mid-band residual — is itself predictive at **AUC 0.81, and
0.815 on the locked test**, with the CI clear of chance. Meanwhile **nothing about the concept target
predicts behavior**: neither its value (AUC 0.51) nor its Jacobian sensitivity (0.58, CI includes 0.5) nor
its projected Jacobian (0.50). This is the Jacobian-based restatement of the sprint's headline — the concept
circuit is a behaviorally epiphenomenal bystander, the refusal channel is the causal lever — now shown for a
gradient/sensitivity measure, not only for the static readout.

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
- **Both cohorts done; single model** (Llama-3.1-8B-Instruct). No cross-architecture check.
- The behavioral-prediction arm (§2.5) is done on **clearharm** only; a curated join is expected to be
  weaker-by-construction (curated suppresses refusal *uniformly*, so its refusal projection was already
  non-predictive at AUC 0.42 in `REP_PREDICTS_BEHAVIOR` — concept-dilution, not under-suppression).

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
