# Doublespeak Causal Circuit — Implementation Progress Log

Tracking execution of `CAUSAL_CIRCUIT_MASTER_PLAN.md`.
Model: Llama-3.1-8B-Instruct (bf16 for causal claims). Branch: `behavioral-causality-sprint`.

**Legend:** ☐ not started · ◐ in progress · ☑ done · ⚠ blocked/needs-decision · ✗ null/negative result

---

## Live status (most recent first)

- **2026-08-03 (iter 22, loop tick)** — **corrected-control result FINAL (window).** Necessity SIG in
  the **mid band on BOTH cohorts** (curated mid +0.177 [.087,.278] & early +0.258 [.146,.372]; clearharm
  mid +0.081 [.012,.151]); late ns; sufficiency robust NULL (S3≈0). → demo-codeword K/V **necessary but
  not sufficient** = distributed/context-bound binding (direct multi-concept confirmation of IE_state≈0/
  DE_context≈99%). Self-swap dev 0. Updated `reports/PHASE4_DEMO_RETRIEVAL.md` with corrected CIs +
  asymmetry. Launched corrected per-layer localization **703248/703249** (peak expected L9-11). Next
  tick: finalize localization, then the surgical per-head query→demo edge knockout (Phase 4.2 induction).


- **2026-08-03 (iter 21, loop tick)** — full nec+suf runs 703213/703214 done, but **caught a control
  bug** by cross-checking vs my earlier ad-hoc CI (clearharm ns then, "SIG" in unified harness). The
  unified harness's necessity `random_control` sourced from DS-OWN random activations (a near-no-op)
  instead of the BENIGN donor that C3 uses → inflated the specific effect. **Fixed** random_control to
  use benign donor (matched to C3). Re-ran full window **703237/703238**. Sufficiency result unaffected
  (S3≈0 both cohorts, robust null). Next tick: corrected necessity CIs (expect curated SIG, clearharm
  conservative) → finalize PHASE4_DEMO_RETRIEVAL asymmetry. Rigor note: self-caught control error.


- **2026-08-03 (iter 20, loop tick)** — sufficiency smoke 703199 clean → **necessity/sufficiency
  ASYMMETRY.** Necessity holds (curated early 0.154 [.038,.290], mid 0.220 [.099,.346] SIG). But
  **sufficiency FAILS**: installing DS demo-codeword K/V into a benign receiver gives S3 p_concept=0.0
  at ALL windows (incl. late) → does NOT create the reading. So demo-codeword K/V is **necessary but
  not sufficient** — the binding needs the codeword K/V *within* its harmful demo context, not the
  local activations (consistent with IE_state≈0 / DE_context≈99% distributed mechanism). Launched full
  nec+suf window runs **703213/703214** to confirm on full data. Next tick: aggregate → write the
  asymmetry into PHASE4_DEMO_RETRIEVAL.


- **2026-08-03 (iter 19, loop tick)** — Extended demoKO harness with the **sufficiency leg**: install
  DS demo-codeword K/V into the BENIGN receiver (mirror of necessity), + built-in paired bootstrap CIs
  (necessity specific = random−C3; sufficiency specific = S3_install−S_random) + self-swap faithfulness
  both directions. Syntax ok; smoke **703199** (curated n=8). Next tick: does installing DS demo K/V
  into benign CREATE the reading (S3>S_random)? Then full runs both cohorts × window/layer → the
  necessity+sufficiency pair for demo-KV retrieval, completing the Phase 4.2 demo-position core.


- **2026-08-03 (iter 18, loop tick)** — **Phase 4.2 demo-KV necessity result COMPLETE (full runs
  703151-703154).** Neutralizing demonstration-codeword K/V reduces the hijacked reading, above random
  controls, **significantly on curated** (early specific +0.180 [.026,.328], mid +0.133 [.053,.217],
  both CI>0, mid survives Holm/3; late ns) and **same direction (ns) on clearharm** (concept noise).
  **Per-layer peak L9-L11 on BOTH cohorts** — replicates the prior mid-band retrieval/write on the
  multi-concept split. Readout validated (DS C1 p_concept .76/.88 vs benign 0.0; self-swap dev 0).
  Wrote `reports/PHASE4_DEMO_RETRIEVAL.md` (paired bootstrap CIs, per-layer localization, honest
  cohort split). **Gate 3 (attention causality) partially met on curated.** Next: sufficiency leg
  (install DS demo K/V into benign) + other locations + the exact per-head edge knockout (Phase 4.2 full).


- **2026-08-03 (iter 17, loop tick)** — **demoKO harness WORKS + first real circuit signal.** FC-readout
  smoke 703123: DS C1 p_concept high (bomb .99, mean .74) vs **benign 0.0 for every example** (clean
  discrimination), self-swap dev=0 (faithfulness). **Core result (n=16 smoke): neutralizing demo-codeword
  K/V reduces the reading SPECIFICALLY at EARLY layers** — ReRead(C1−C3) early **0.154 vs random 0.048**;
  mid 0.220≈random 0.222 (non-specific); late 0.013<random 0.103. = early induction-style retrieval binding.
  **Launched FULL runs 703151-703154** (clearharm/curated × window/layer, all examples) to confirm with
  proper n + per-layer curve. Next tick: aggregate → the demo-KV necessity result + per-layer localization,
  then random/self-swap controls, both cohorts. This is the Phase 4.2 retrieval-necessity core.


- **2026-08-03 (iter 16, loop tick)** — smoke 703115 confirmed the BENIGN-source fix (C3 fires, 48
  rows/cell, self-swap=0) but exposed the readout was still wrong: **ps_concept_gated≈0 even for clean
  bomb** — I was reading the patchscope of the query-codeword rep (IE_state≈0, floors), not the
  DE_context reading. **Rewrote to the forced-choice-question readout** (30's forced_choice template):
  append 'does the word "cw" refer to "concept" or to "cw"?' to the demo block, read
  P(concept-label)/(P(concept)+P(codeword)) at the answer position (this is the DS≈0.35 DE_context
  measurement). Demo positions via char-offset filter (before the question); validity = DS C1
  p_concept > BENIGN (built-in discrimination, no patchscope gate). Syntax ok, smoke **703123** submitted.
  Next tick: does DS C1 discriminate from benign? self-swap≈0? ReRead sign → then full runs.


- **2026-08-03 (iter 15, loop tick)** — demoKO smoke 703105 ran clean (24 rows, no crash) but exposed
  a real bug: **C3_demoKV never fired** because I sourced neutralization from NEUTRAL (which is
  demo-free → no demo-codeword K/V). **Fixed:** source from BENIGN_REMAP (same codeword in benign demo
  sentences = correct non-harmful-binding source). Also the smoke drew LSD/MDMA (weak-decoding
  concepts → positive control failed); resubmitted larger smoke **703115** (curated n=8) to confirm C3
  fires + positive control passes for strong concepts + ReRead sign. Next tick validates, then full runs.


- **2026-08-03 (iter 14, loop tick)** — Built the **pivotal multi-concept patching harness**. Found the
  prior pair scripts (44_kv_mediation) hardwire a single global concept/codeword for the readout →
  can't run on the multi-concept split. Wrote `scripts/phase3_demo_neutralize.py` reusing 44's exact
  primitives (DemoStateSwap at demo-codeword resid_pre, PatchscopeDecoder gated readout,
  resolve_positions, ComponentCapture) but **per-row concept/codeword + per-example positive control**.
  Cells C1 / C3_demoKV (neutralize demo K/V = necessity) / C1_selfswap (faithfulness) / random_control;
  per window AND per layer; ReRead_test=mean(C1−C3). Syntax ok, bench pairing verified (0 missing).
  **SMOKE submitted 703105** (curated, n=2, window). Next tick: validate smoke (positive-control passes?
  self-swap≈0? ReRead sign?), then full runs both cohorts × {window, layer} granularity → the core
  retrieval-necessity result on ClearHarm.


- **2026-08-03 (iter 13, loop tick)** — **Phase 3 cell #1 (resid_post × query-codeword, logit-lens)
  COMPLETE → NULL, as expected.** Jobs 702995/702996 done. Baseline DS p_harm ≈0 (logit-lens floors at
  codeword) → necessity ≈ random control, sufficiency ≈0, ALL layers, both cohorts/splits.
  **Reproduces IE_state≈0** (harmful concept NOT in local query-codeword state) on the new ClearHarm
  split — plan's known-findings #1-3 confirmed. Diagnosed: logit-lens-at-codeword fails its positive
  control (prior T2/N3); the **validated readout is the forced-choice patchscope** (`46`, DS≈0.35 in
  DE_context job 694691). Wrote `reports/PHASE3_RESIDUAL.md`. **Next: circuit-discovery cells** =
  DEMO/all-occurrence positions (binding is in the demos, not query state) × 4 locations, forced-choice
  readout, reusing 43/44/46 patch+forced_choice machinery. That's where signal is predicted.


- **2026-08-02 (iter 12, loop tick)** — **Phase 3 (resid_post core) STARTED.** Found `05_run_activation_
  patching.py` consumes items in my `beh_<cohort>.json` format → per-example necessity(neutral→DS) +
  sufficiency(Direct/DS→neutral) + identity + norm-matched-random controls across ALL 32 layers,
  forced-choice logit-lens P(harm)/P(code) at resid_post/codeword_last+following. Fixed
  `ds_common.target_positions` with a BOS-aligned offset-finder fallback (all 137 items resolve;
  localization+resid_pre tests 20/20). Submitted **702995 (clearharm) + 702996 (curated)** via new
  `slurm/run_stage2_patch_split.sh`. Next tick: per-layer necessity/sufficiency curves (does patching
  the final codeword state at any layer remove/install the harmful reading? — prior work said
  final-state-only was insufficient; now tested exhaustively per-layer on the split, both cohorts).
  Then extend to 4 locations (resid_pre/attn_out/mlp_out via SubmodulePatch) + all-occurrence positions.


- **2026-08-02 (iter 11, loop tick)** — **curated behavioral 702862 COMPLETE → Phase 2.1 core DONE,
  Gate 1 (reproduction) SATISFIED.** Curated neutral = clean **0.039** floor (harm-in-one-noun), DS
  train **0.333 vs neutral 0.033 = +0.30 (10×)** — clean Doublespeak effect. ClearHarm DS>>direct
  (0.349 vs 0.116, refusal bypass) stable train/test. **Honest weak result:** curated TEST DS=0.095
  (n=21, 2 malicious) — big train→test drop, small-n/concept-composition (baseline, not overfitting;
  flagged, needs more test ex). Wrote `reports/PHASE2_BEHAVIORAL.md` (per-split table + caveats).
  Gate 1 met (attack reproduces behaviorally + representationally). **Next: Phase 3** exhaustive
  all-occurrence residual patching (causal core, forced-choice readout) — or Phase 2.1 extended
  conditions first.


- **2026-08-02 (iter 10, loop tick)** — **ClearHarm behavioral baseline 702861 COMPLETE** (n=86,
  StrongReject): malicious rate **direct 0.116 / neutral 0.256 / doublespeak 0.349**; mean_SR 0.108 /
  0.218 / 0.294. **Core Doublespeak result holds: doublespeak >> direct (+0.23)** — codeword rephrase
  bypasses the refusal that blocks the direct request. **Neutral elevated (0.256)** = ClearHarm concept
  noisiness (harm not always in the single swapped noun; e.g. "boosted-fission weapon"→"…potato" keeps
  harmful context) — predicted in split-contract Limitation 2; motivates curated cohort. Curated
  702862 RUNNING → next tick reads it (expect neutral≈0, cleaner direct/DS gap), then write
  `reports/PHASE2_BEHAVIORAL.md`.


- **2026-08-02 (iter 9, loop tick)** — **Phase 2.1 behavioral baseline SUBMITTED.** Confirmed
  StrongReject available (OPENAI_API_KEY + `strongreject_scoring`). Wrote `scripts/split_to_behavioral.py`
  (split → `14_behavioral_eval` data; demos extracted from DS prompt — verified byte-identical rebuild
  of direct/neutral/doublespeak) + `slurm/run_behavioral_split.sh`. Submitted jobs **702861 (clearharm,
  86 items) + 702862 (curated, 51)** → direct/neutral/doublespeak generation + StrongReject, per cohort.
  Next tick: read per-condition StrongReject/ASR/refusal (does Doublespeak jailbreak vs direct/neutral
  on the locked split). Extended conditions (benign/shuffled/unrelated + interventions) = follow-up.


- **2026-08-02 (iter 8, loop tick)** — refusal 32-layer build **702750 COMPLETE** (L0–31.pt; sep
  0.33→peak ~1.03 @ L20-23→0.94, concentrated mid-late). Wrote `scripts/build_unified_directions.py`
  → `outputs/unified_directions/{clearharm,curated}.{npz,json}`. **HEADLINE RESULT: concept_direction
  ⊥ refusal_direction at every layer, both cohorts** — mean cos(concept,refusal) **0.012** (clearharm)
  / **0.061** (curated), max|·|≤0.15. Concept axis is independent of refusal → separate levers (plan §2
  validated). cos(signature,refusal) ~0.13-0.15; cos(concept,signature) 0.14-0.25 (dissociation).
  Wrote `reports/PHASE2_DIRECTIONS.md`. **Phase 2.2 (direction separation) essentially DONE**
  (representational). Remaining Phase 2: 2.1 behavioral baselines (SLURM); covariance-adjusted sim (queued).


- **2026-08-02 (iter 7, loop tick)** — reps job **702731 clearharm COMPLETE** (516 rows, 0 missing).
  Ran **`33_build_directions` on clearharm** → `outputs/pair_directions_20260802_201124_1612201`
  (192 direction keys; `d_Direct|…`, `d_DS|…` each [32,4096]). cos(d_Direct,d_DS) resid_post/
  codeword_last dev mean **0.245** (curated 0.14) — dissociation holds on BOTH cohorts.
  **Both cohorts now have concept + signature + control directions.** Existing refusal artifact only
  covered L12-20 → submitted **all-32-layer refusal build (job 702750)** via new
  `slurm/run_refusal_alllayers.sh` (bench pair_carrot_bomb, layers hardcoded via seq to dodge
  --export comma bug). **Next tick:** when 702750 done, write `scripts/build_unified_directions.py`
  co-locating concept/refusal/signature per-layer + cos(concept,refusal), cos(signature,refusal),
  norms; then Phase 2.1 behavioral baselines.


- **2026-08-02 (iter 6, loop tick — user nudged "be on loop")** — reps job 702692 **curated COMPLETE**
  (306 rows, 0 missing); 702691 clearharm **FAILED** (`resolve_positions` strict finder missed codeword
  'pumpkin' in a ClearHarm context). **Fixed** `pair_common.resolve_positions` with an offset-finder
  fallback (only fires where strict raised → no regression); verified all 822 bench rows resolve, tests
  10/10. Resubmitted clearharm reps → **702731 PENDING**. Ran **`33_build_directions` on curated** →
  `outputs/pair_directions_20260802_200945_1610756` (128 directions + 64 subspaces). **Result:**
  cos(d_Direct, d_DS) resid_post/codeword_last dev mean **0.14** (max .39) — the concept↔signature
  **dissociation replicates** on the ClearHarm-style curated cohort (keep concept & signature separate).
  Next: 33 on clearharm reps when 702731 done; refusal direction (reuse `outputs/stage_gcg_full/*.pt`
  if valid); unify per-layer concept/refusal/signature.


- **2026-08-02 (iter 5, loop tick)** — reps jobs 702652/702653 **FAILED** at the summary-write
  (`KeyError: 'pair'` — `32_extract_pair_reps` records `bench["pair"]`; adapter omitted it). Reps
  arrays (means/per_prompt/subsample) were saved fine; only `reps_summary.json` crashed. **Fixed**
  adapter to emit a `pair` key (multi-concept descriptor), regenerated bench, **resubmitted:
  702691 (clearharm) + 702692 (curated)**, PENDING. Next tick: verify COMPLETE → `33_build_directions`.
- **2026-08-02 (iter 4, loop tick)** — **Phase 2 reps extraction SUBMITTED** on L40S:
  job **702652** (clearharm bench) + **702653** (curated bench), `32_extract_pair_reps --readout fixed`,
  killable partition. Outputs → `doublespeak_causality/outputs/pair_reps_*`. **Next tick:**
  when both COMPLETE, run `33_build_directions --reps-dir <each>` (concept d_Direct + signature d_DS +
  controls + per-layer cosines), check for a reusable existing `refusal_direction` in
  `outputs/stage_gcg_full/*.pt` (else rebuild via `build_refusal_direction_llama --validate`), then
  unify into separate per-layer concept/refusal/signature objects + cross-direction cosines.


- **2026-08-02 (iter 3, loop)** — **Phase 1 COMPLETE.** Locked split `data/splits/clearharm_doublespeak_v1.json`
  finalized: **137 records, both cohorts ≥20/≥20** (clearharm PRIMARY 44/42, curated REPLICATION 30/21).
  Validator **12 ok / 0 warn / 0 FATAL** (no id/cluster/prompt leakage, all single-token). Caught+fixed a
  cross-split leakage bug (duplicate neutral prompts from shared codeword+template → now unique codeword
  per concept). Reproducible via committed `_concept_cache.json`+`_demo_cache.json`. Wrote
  `reports/DATASET_AND_SPLIT_CONTRACT.md` (schema, 6 matched conditions, methodology, 4 honest limitations
  incl. ClearHarm concept noisiness + near-dup clustering not yet applied). **Gate for Phase 2/3 open.**


- **2026-08-02 (iter 2, autonomous loop)** — Cron loop set (`*/30 * * * *`, job a5747db4). **Phase 1
  nearly done.** Built `data/splits/clearharm_doublespeak_v1.json` (both cohorts). Found + fixed two
  builder bugs: (a) curated template top-up, (b) **codeword-skip bug** — main loop dropped any item
  whose cycled codeword was multi-token, silently shrinking cells (curated 19→51 after fix). Added
  **concept-extraction caching** (locked split reproducibility) + **per-cohort ≥20/≥20** validator
  check. ClearHarm primary cohort already ≥20/≥20; curated now yields 51 (17 concepts×3) → ≥20/≥20.
  Also advanced Phase-3 infra: **added `resid_pre` to `SubmodulePatch`** (unified 4-location patch:
  resid_pre/attn_out/mlp_out/resid_post) + 4 GPU-free tests (10/10 pass). Final cached canonical
  build running; then validate + write `reports/DATASET_AND_SPLIT_CONTRACT.md`. All committed+pushed.


- **2026-08-02 (iter 1)** — **Phase 0 audit COMPLETE.** 7-lane parallel audit finished (0 errors,
  367k tok). Wrote `reports/CAUSAL_PATCHING_AUDIT.md` (full repo map, reusable primitives,
  provenance, reproducible-vs-not values, gap list, 10 footguns). Wrote
  `scripts/validate_data_integrity.py` (train/test overlap, intent-cluster leakage, dup prompts,
  codeword-occurrence & multi-token checks, output-row dup/metadata checks) — syntax-ok, dry-run
  graceful (no split yet). **Key priors captured:** d_DS causally inert (d_Direct is the lever);
  temporal/repr GCG objective backfires (ASR 0.0, refusal 0.615) — attack is demonstration-bound;
  N7-M all-layer edge knockout degenerate → **surgical per-head edge knockout (Phase 4.2) is the
  flagged next step**; mechanism distributed (no single-head/layer bottleneck). Novel EV =
  ClearHarm generalization + locked-split/Holm rigor + full 4-loc/all-layer/all-head coverage +
  surgical knockout. **Consulting Omer on ClearHarm→Doublespeak mapping (§7 of audit).**
- **2026-08-02** — Session start. Wrote master plan. Oriented repo: found mature existing
  infra (`ds_common.py`, `pair_common.py`) already implementing LayerPatch, AttentionKnockout,
  ZHeadPatch/Capture, DemoStateSwap, SubmodulePatch, project-out/add hooks (single+multilayer),
  norm-matched/orthogonal/in-subspace random controls, all-occurrence `find_word_occurrences`,
  templating, `EXPERIMENT_REGISTRY.csv` (45 runs), `tests/` (17 tests). Created `reports/`,
  `configs/manifests/`, `scripts/`. Launched **Phase 0 audit workflow** (7 parallel code auditors).

---

## Phase checklist

| Phase | Description | Status | Notes |
|------|-------------|--------|-------|
| 0 | Repo & result audit → `reports/CAUSAL_PATCHING_AUDIT.md` + validation checks | ☑ | audit report + data-integrity validator done; Gate 1 satisfiable from artifacts |
| 1 | ClearHarm locked split → `data/splits/clearharm_doublespeak_v1.json` (≥20 train/≥20 test) | ☑ | 137 recs, both cohorts ≥20/≥20, validator 0 FATAL, contract written |
| 2 | Baseline reproduction + concept/refusal directions | ◐ | 2.2 directions DONE; 2.1 core behavioral DONE (Gate 1 met); extended conditions + interventions pending |
| 3 | Exhaustive all-occurrence residual patching (L0–31 × 4 loc × 10 pos × 2 dir) | ◐ | resid_post/codeword core RUNNING (702995/702996 via reused 05); 4-loc + all-pos pending |
| 4 | Exhaustive attention: all-head scan + edge knockout + edge sufficiency | ☐ | reuse AttentionKnockout, ZHeadPatch |
| 5 | Exhaustive all-head activation patching (Q/K/V/z/pattern/result) | ☐ | reuse ZHeadCapture/Patch |
| 6 | Exhaustive MLP write-location analysis | ☐ | reuse 51_mlp_attribution, SubmodulePatch |
| 7 | Head→MLP path patching (every downstream receiver) | ☐ | reuse 50_path_patching |
| 8 | Jacobian/projection readout all layers | ☐ | reuse 07_patchscope, 46_forced_choice |
| 9 | Intervention-strength dose-response sweeps | ☐ | reuse 34_intervention_sweep |
| 10 | Distill causal optimization objective | ☐ | gated on 3-7; reuse MECHANISTIC_OBJECTIVE |
| 11 | GCG / MAC / TROPT evaluation | ☐ | gated on 10; reuse 25_eval_gcg_asr, TROPT skill |

## Granularity coverage (per major intervention)
A single-layer · B canonical windows · C sliding (w2/4/8) · D cumulative prefix · E cumulative suffix · F mechanism-derived · G all-layers. Tracked per experiment once Phase 3 begins.

## Gates
- G1 Reproduction ☐ · G2 Layer coverage ☐ · G3 Attention causality ☐ · G4 Write location ☐ · G5 Path mediation ☐ · G6 Objective ☐ · G7 Behavioral improvement ☐

## Deliverable reports (status)
`CAUSAL_PATCHING_AUDIT` ◐ · `DATASET_AND_SPLIT_CONTRACT` ☐ · `ALL_OCCURRENCE_PATCHING` ☐ ·
`ATTENTION_EDGE_KNOCKOUT` ☐ · `ALL_HEAD_ACTIVATION_PATCHING` ☐ · `ALL_LAYER_MLP_PATCHING` ☐ ·
`HEAD_TO_MLP_PATH_PATCHING` ☐ · `JACOBIAN_READOUT` ☐ · `CAUSAL_OBJECTIVE` ☐ ·
`GCG_MAC_EVALUATION` ☐ · `FINAL_CAUSAL_CIRCUIT_REPORT` ☐ · `SLACK_UPDATE` ☐

## Phase 2 — concrete next actions (queued for next loop iteration; GPU/L40S/SLURM)
Phase 2 is GPU-bound (model forward passes) and must run on **L40S** via SLURM (login node is
TITAN Xp 12GB, too small for 8B bf16). Plan, reusing `32_extract_pair_reps` + `33_build_directions`
+ `build_refusal_direction_llama`:
1. ☑ **Split→bench adapter** DONE (`scripts/split_to_bench.py`, CPU). Output
   `data/bench/bench_{clearharm,curated}.json` — every condition×split cell ≥20 (clearharm 44/42,
   curated 30/21; 516 + 306 rows). probe_word = concept for DIRECT_CONCEPT else codeword; train→dev,
   test→heldout. **Next loop: submit SLURM.**
2. **Reps extraction** (SLURM, L40S): run `32_extract_pair_reps.py --bench <adapter out>` for each
   cohort → per-(condition,split,component,position,layer) reps. bf16.
3. **Directions** (CPU): `33_build_directions.py --reps-dir <...>` → `d_Direct` (concept), `d_DS`
   (doublespeak_signature), `d_benign`/`d_unrelated` controls, PCA subspaces, cross-fit dev/heldout,
   per-layer cosines. Then `build_refusal_direction_llama.py --validate` → `refusal_direction[L]`.
4. **Unify** (`scripts/build_unified_directions.py`): co-locate concept/refusal/doublespeak_signature
   as separate per-layer objects + per-layer cos(concept,refusal), cos(signature,refusal),
   covariance-adjusted sim, norms → `reports/`-ready. Keep them SEPARATE (never merge concept+refusal).
5. **2.1 behavioral baselines** (SLURM, L40S, larger): 10 conditions × ≥20/≥20, forced-choice prob +
   logit-diff + StrongREJECT + ASR + refusal-rate. Reuse `14/18/19` + StrongREJECT harness.
Guardrail: bf16 for causal claims; discovery on `train` only; `test` only for frozen replication.

## Decisions / open questions for Omer
- **2026-08-02 — ClearHarm construction (RESOLVED):** (1) **Blend** — ClearHarm-native single-token
  subset = PRIMARY cohort; curated 40-pair set = parallel REPLICATION cohort; results reported
  separately, claim only what replicates (~2x compute on L×head scans accepted). (2) **Reuse
  gpt-4o-mini pipeline** (seed_concepts_gpt4omini convention: harmful_word/codeword/12 demos,
  fixed openai_seed, content-hash provenance) + single-token filter.
- Constraint reminder: all concept-extraction + demo-generation runs in the MAIN LOOP (cyber-safeguard
  kills subagents on harmful codeword-binding text); subagents only for scalar/structural work.

## Known constraints (from project memory)
- SLURM: no deps, max 6 parallel, L40S only, no trimming. bf16 + default SDPA (don't disable flash). GCG always `--no-filter-cand`.
- Cyber-safeguard kills subagents that read ClearHarm/jailbreak **text**; keep harmful-text handling in main loop, delegate code/scalar work only.
