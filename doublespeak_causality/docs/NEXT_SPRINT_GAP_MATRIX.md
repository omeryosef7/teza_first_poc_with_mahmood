# Next Sprint — Gap Matrix (2026-08-09)

Classification of every requested item. Statuses: **DONE** (no rerun) · **DONE-CONFIRM**
(done but needs confirmatory replication) · **PARTIAL** · **UNDERPOWERED** · **NOT RUN** · **NEW**.

Sources: SPRINT_SUMMARY_2026-08-02_TO_08-09.md, configs/manifests/phase9_gcg_mac_matrix.json,
reports/*. This drives what we spend GPU on. **Do not rerun DONE items.**

## A. Old mechanistic/attention requests (Plan §2 list 1–10)

| # | Item | Status | Evidence / why | Action this sprint |
|---|---|---|---|---|
| 1 | query→demo-codeword attention-edge KO | **DONE (NEGATIVE)** | §7.5 clearharm spec-vs-rand +.0020 ns; curated −.0026 ns; all-query-edges 13–49× larger → distributed | none (reconfirm only if a new hypothesis needs it) |
| 2 | candidate induction-head activation patching | **DONE** | §7.8 all-head z-patch (58/0/31/31 Holm); §7.9 joint-KO superadditive; no single head | none |
| 3 | head→MLP path patching | **DONE (NULL/NO-PATH)** | §8 (P8_HEAD_MLP_PATH) candidate 1.44× < 2× needed; 17/25 no-path | none |
| 4 | all-codeword-occurrence patching | **DONE** | §7.3 residual NULL; P2 all-occ L9 write 1.38–2.27× demo-only (stronger repr effect); use all-occ by default in any new concept intervention | reuse (all-occ default) |
| 5 | Jacobian / projection-based readout | **DONE** | P6: refusal ‖J‖ AUC 0.807 vs concept 0.583, paired +0.225 CI[.055,.361] | reuse → turn into GCG loss (Phase 3) |
| 6 | clean separation of concept/refusal directions | **DONE** | §7.2 cos≈0.01–0.06, |cos|≤0.153; P7 refusal validated L13-20 | reuse frozen directions |
| 7 | corrected Doublespeak baseline | **DONE-CONFIRM** | §7.1 baselines exist; but Gate-7 arms must share ONE compute-matched pipeline w/ larger gen budget (truncation fix) | Phase 1 freeze |
| 8 | GCG under corrected setup | **PARTIAL / first-cut** | §14-18 multi-seed NEGATIVE (2 seeds, 50 steps, 20-item train); 16-arm matrix NOT RUN | **Phase 4 (highest priority)** |
| 9 | ClearHarm migration | **DONE** | locked v1 split (44/42) + v3 confirmatory (N=324, leakage 0); manifests built, JOIN 86/86 | reuse |
| 10 | quantization | **PARTIAL** | §29 refusal-ablation bf16/8/4-bit DONE; concept geometry/predictor/attack under quant NOT run | Phase 6 (exploratory) |

## B. This sprint's core questions (Plan §10 Q1–Q7)

| Q | Question | Status | Action |
|---|---|---|---|
| Q1 | Does the GCG negative survive a full fair matrix (more seeds/steps)? | **NOT RUN** (first-cut only) | Phase 4: run screen (16 arms×seed42, 200 steps, 44-item train) → 3–5 seeds on finalists |
| Q2 | Jacobian refusal objective > simple refusal-projection objective? | **NOT RUN** | Phase 3+4: arms 07 (proj) vs 10 (jacobian refusal) |
| Q3 | ANY refusal-derived objective beat norm-matched random? | **PARTIAL** (dead heat 2 seeds) | Phase 4: powered, compute+norm-matched random control |
| Q4 | Does concept term help/hurt/nothing? | **NOT RUN** | Phase 4: arms 06 (concept) / 08 (combined) vs controls |
| Q5 | Does the intended internal mechanism change actually occur? | **NOT RUN** | Phase 4 mechanistic-validity check: measure refusal-proj / concept-proj before→after per suffix |
| Q6 | Dissociation reproduces in 3rd family (Phi-4-mini-reasoning)? | **NOT RUN** (only Qwen3 done) | Phase 5 X0→X5 |
| Q7 | Dissociation/objective survives quant beyond refusal-ablation? | **PARTIAL** | Phase 6 |

## C. 16-arm matrix — per-arm readiness (configs/manifests/phase9_gcg_mac_matrix.json)

| Arm | Objective | Stack | Status (spec) | Blocker → resolution |
|---|---|---|---|---|
| 01 nosuffix direct | none | none | ready | — |
| 02 nosuffix doublespeak | none | none | ready | — |
| 03 vanilla GCG direct | task_loss | gcg | ready | — |
| 04 vanilla GCG doublespeak | task_loss | gcg | ready | main comparator |
| 05 harmful-target-logits | harmful_target_logits | gcg | **blocked** | bit-identical to arm4 (one target). Resolve: drop OR source longer harmful continuation. **Likely DROP as redundant** (document) |
| 06 concept-up | concept_up | gcg | needs_input | build reference cache (direct) + frozen concept readout position |
| 07 refusal-down L22 | refusal_projection_down | gcg | **ready, first-to-run** | lambda from P8.1; **this is the extended first-cut** |
| 08 concept+refusal | combined | gcg | needs_input | arm6 cache + degeneration penalty |
| 09 jacobian concept | jacobian_concept | gcg | gated | P6 → differentiable loss (Phase 3) |
| 10 jacobian refusal | jacobian_refusal | gcg | gated | P6 → differentiable loss (Phase 3) |
| 11 MAC concept | concept_up | tropt_mac | needs_impl | TROPT Loss subclass + venv |
| 12 MAC refusal | refusal_projection_down | tropt_mac | needs_impl | TROPT Loss subclass |
| 13 MAC combined | combined | tropt_mac | needs_impl | TROPT Loss subclass |
| 14 attention/carry | attention_carry | gcg (eager) | gated | only if carry path causally validated — **it is NOT** (§8/§10 null) → **DROP or negative-control only** |
| 15 random-suffix control | random_suffix | none | ready | length-matched null |
| 16 transfer train→test | transfer | none | ready | replay winning suffix string |
| (17) signature negative control | doublespeak_signature | gcg | optional | best-supported causal null (≤3e-5) — add as neg control if run |

**Random-DIRECTION control** (criterion 6) = re-run arm07 with a norm-matched random direction
(distinct from arm15 random-suffix). Must exist for every mechanism arm at matched norm/layer/seeds.

## D. Sprint execution priority (gated)

1. **Phase 1 (Gate A)** — freeze corrected baseline: one compute-matched pipeline, larger gen
   budget (kill 200-tok truncation), arms 01/02/03/04/15 + no-suffix harmful. Verify baselines
   reproduce within ~6pp envelope.
2. **Phase 3 (Gate B)** — implement refusal-projection loss (exists) + Jacobian-refusal loss (NEW);
   gradient/sign sanity test: tiny perturbation moves target metric, random doesn't.
3. **Phase 4 (Gate C→D)** — MAIN: screen arms (seed 42, 200 steps) → pilot specificity vs random →
   3–5 seeds on finalists (refusal-proj, jacobian-refusal, concept, combined, +matched randoms).
   Mechanistic-validity check on every optimized suffix.
4. **Phase 5 (Gate E)** — Phi-4-mini-reasoning X0→X5 (native reasoning). Parallelizable with Phase 4.
5. **Phase 6 (Gate F)** — quantization extension (concept geometry/predictor + final 2 attack arms).

Phases 5 (Phi smoke + behavioral repro) can run in PARALLEL with Phase 4 GCG on separate GPUs
(≤6 total). Phase 6 is last / exploratory.

## E. Items explicitly NOT to rerun (already convincingly DONE)
- Attention-edge KO, head z-patch, head→MLP path, residual all-occ patch, concept/refusal geometry,
  refusal per-layer validation, refusal ablation/re-injection behavioral, decision-token localization,
  Gate B forward, full mediation, 2×2, orthogonalization, rep-predicts-behavior AUC, Jacobian readout,
  Qwen3 cross-model dissociation, refusal-ablation quantization, defense/utility (Gate F FAIL).
