# Sprint Completion Plan — Fully Executing the Matan / Mahmood Research Agenda

**Status:** planning document (this file only; execution artifacts are produced during the sprint).
**Created:** 2026-07-25.
**Author:** Omer Yosef (with Claude Code).
**Immutable upstream plan:** `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` — **do not edit.** This file *extends* it.
**Companion execution artifacts (created during the sprint, not now):**
`docs/SPRINT_COMPLETION_EXECUTION_LOG.md`, `docs/SPRINT_COMPLETION_GAP_MATRIX.md`,
`docs/THINKING_ATTACK_LITERATURE_MATRIX.md`, and the per-phase reports listed in §11.

---

## 0. Context — why this sprint exists and how it connects to the original plan

The original research plan (`RESEARCH_PLAN_DISTILLING_JAILBREAKS.md`) pursues **one mechanistic
spine** (its §30 "Final Strategic Principle"):

> Real Attack → Predictive Signal → Causal Validation → Soft Objective → MAC Trigger → Held-Out Transfer

That spine was executed end-to-end (see `docs/PLAN_EXECUTION_SUMMARY.md`). It produced a strong,
honest, **but negative** central result:

- The success-vs-failure residual signal is **predictive** (grouped-LOGO AUC ≈ 0.90, pre-generation)
  across **4 architectures / 2 backbone families**, …
- … **but not causal.** Every causal test is NULL — activation-addition steering (sufficiency +
  necessity, layer + timing sweeps), attention-temperature intervention, and the optimization-side
  soft-prompt test. And the predictive signal is **prompt-length-confounded** on Qwen3
  (gain-beyond-length CI includes 0 at n=44).

In the plan's own decision tree (§25), this is **Gate 3 = No** and **Gate 4 = No**. Those two gates
**correctly routed the pipeline *past* Phases 10–12** (Discrete MAC / Distributional-RL / Universal):
they were **never entered**, because the plan only advances a *mechanistic* objective into discrete
optimization if it first survives the causal gates.

**What Matan & Mahmood raised** organizes into three workstreams, which map onto the original plan's
own Workstreams A/B/C but push each further than the executed work reached:

| Matan/Mahmood workstream | Original-plan home | State after the mechanistic sprint |
|---|---|---|
| **1. Attack by category** (suffix dataset, specialization, transfer, single-vs-multi, universality) | Workstream C → Phases 12, 13, 15, 16 | Phase 13 *descriptive* analysis done (336 suffixes); Phase 12 *controlled* category/multi-instruction attacks **never run** (gated off) |
| **2. Attack reasoning / thinking** (reproduce mechanisms, literature gaps, multi-turn, defenses) | Workstream A/B → Phases 4, 4X, 5–9, 17 | CoT-Hijacking baseline + cross-model + mechanistic + detector done; **exact head/span mechanism, context-hijacking, SEMA multi-turn, cross-family defense = open** |
| **3. Interpretability → optimization objective** (mechanistic *and* behavioral/REINFORCE) | Workstream A → Phases 8–11 | Mechanistic objective **closed as negative** (Gates 3/4 = No); **behavioral REINFORCE objective never built** |

### 0.1 The single most important connection to state precisely

The original plan's **Phase 11 (§15) — "Distributional and Reinforcement-Style Optimization"**
*already specifies* the behavioral objective this sprint centers on: §15.1 says "a suffix can make
'Sure' likely without causing harmful compliance … a behavioral objective should reward complete
generated responses"; §15.2 specifies the multi-component reward; §15.4 specifies the
differentiable-proxy → free-generate → reward-select bridge; §15.5–15.6 specify the exact comparison
table (Prefix-CE vs generation-reward selection vs policy-gradient).

**Phase 11 was never executed** — not because it was tested and failed, but because the pipeline was
routed past it by the *mechanistic* Gate-3/Gate-4 nulls. The behavioral objective was never itself
gated. **This sprint re-activates Phase 11 as a first-class track**, faithfully implements the
REINFORCE-style estimator (per arXiv 2502.17254), and re-opens Phases 10 and 12 *through the
behavioral objective* rather than the (closed) mechanistic one.

> **Honesty flag (verified against the source docs):** the existing reports do **not** contain any
> statement that "a REINFORCE / behavioral objective remains open." That framing is *introduced by
> this sprint*. It is justified — the causal null gates off the *mechanistic-success-direction*
> objective (§12.3 O4), not the behavioral reward objective (§15) — but it is a **re-scoping**, and
> is labelled as such wherever it appears. We do **not** claim the original docs left it open.

### 0.2 What is genuinely NET-NEW vs the original plan

The original plan does **not** cover these; the sprint adds them:

1. **ClearHarm as the primary suffix benchmark.** Original plan uses AdvBench dev-25 / held-out-495
   only. ClearHarm is **not vendored** anywhere in the repo (verified). → new Phase B.
2. **Context-hijacking / Doublespeak** as a distinct attack family. **No code exists** (verified).
   → new Phase F2. (Original plan's only "hijacking" is TROPT attention-hijacking + CoT-Hijacking.)
3. **SEMA / multi-turn attacker-policy learning.** **No code, no simulator exists** (verified).
   → new Phase G. (This is a *different problem class* from the original plan's single-turn spine.)
4. **Cross-family + adaptive defense.** Original plan's Phase 17 built an in-distribution detector
   and *scoped* (did not run) adaptive/§21.2 and defense-intervention/§21.5. → new Phase H.
5. **Controlled category-specific & multi-instruction attack generation** (Phase 12 was never run).

---

## 1. Crosswalk — sprint phase ↔ original plan ↔ current state

This is the core "how the two plans connect" table. `DONE` = verified artifact exists;
`PARTIAL` = descriptive/scoped only; `NEW` = not in executed work; `RE-OPEN` = specified in the
original plan but gated off, re-activated here.

| Sprint phase | Original-plan section(s) | State | Reuse / entry point |
|---|---|---|---|
| **A** Gap audit + reconciliation | §4 (Ph0), §22 registry, §25 gates | NEW (audit) | `results/EXPERIMENT_REGISTRY.csv`, `scripts/validate_eval_results.py` |
| **A2** Literature matrix | §2 RQs, §31 amendment | NEW | `Chain_of_Thought_Hijacking/…/paper`, TROPT `GCGHij` (bentov2025 = arXiv 2506.12880) |
| **B** ClearHarm primary benchmark + unified schema | §5 (Ph1), §6 (Ph2) | NEW dataset; schema EXTENDS | `data/manifests/*`, `schemas/evaluation_result.schema.json`, `configs/evaluation/*.yaml` |
| **C** TROPT baseline completion (GCG/MAC on ClearHarm) | §7 (Ph3), §14 (Ph10 rows B4–B8) | RE-OPEN / extend | `scripts/phase3_tropt_optimize.py`, `scripts/phase3_eval_triggers.py`, TROPT `mac__wang2024`/`gcg__zou2023` |
| **D** REINFORCE-style behavioral objective | **§15 (Ph11)** — the central re-activation | **RE-OPEN (never executed)** | TROPT `GCGPlusOptimizer`, `PrefillCELoss`, `ResponseHarmfulnessLoss`, `CombinedLoss`; reward struct from `poc_rl_loop/rl_reward_function.py` |
| **E** Category workstream completion | §16 (Ph12) controlled + §17 (Ph13) descriptive | Ph13 PARTIAL / Ph12 RE-OPEN | `scripts/gcg_advbench_llm_taxonomy.py`, `results/SUFFIX_TAXONOMY.csv`, `results/CATEGORY_TRANSFER_MATRIX.csv`, TROPT `GCGMult__zou2023` |
| **F1** CoT-Hijacking exact head/span mechanism | §11.8 (Ph7 attention), §C1 | PARTIAL (uniform-temp null only) | `poc_stage4/model_family_utils.py`, `poc_stage_ae/*`, `scripts/phase7_*`, `Chain_of_Thought_Hijacking/Hijacking/config/system_prompts.py` |
| **F2** Context-hijacking / Doublespeak | — | **NEW** | none — resolve reference first (§F2.0) |
| **G** SEMA / multi-turn | — | **NEW** | reuse model+judge wrappers only; simulator is new |
| **H** Cross-family + adaptive defense | §21 (Ph17) §21.2/§21.5 | Detector DONE / adaptive+intervention SCOPED | `scripts/phase17_detector.py`, `scripts/phase17_confound.py`, `scripts/detector_groupkfold_audit.py` |
| **I** Unified final evaluation | §18 (Ph14), §19 (Ph15), §20 (Ph16) | Original held-out DONE; ClearHarm final NEW | `data/manifests/heldout_495.csv`, external sets in §2 |

**Gate correspondence** — the sprint's Gates 1–7 (its §13) map onto the original plan's §25 tree:
sprint-Gate-1 (ClearHarm reproduces Prefix-CE mismatch) ⇄ new; sprint-Gate-3/4 (soft-opt then
REINFORCE-MAC beat Prefix-CE) ⇄ original **Gate-4/Gate-5** re-instantiated for the *behavioral*
objective; sprint-Gate-5 (CoT/context internal signal is causal) ⇄ original **Gate-3** re-run for
head/position-specific mechanisms (which the original's *uniform* attention null explicitly did
**not** rule out); sprint-Gate-6 (detector survives OOD) ⇄ original §21.2.

---

## 2. Verified current state — DO NOT REPEAT (with artifact paths)

Confirmed against the reports and registry. Denominators are shown because several runs have <25 due
to attacker/API row-gaps (not placement bugs).

**CoT-Hijacking attack baselines (greedy/behavioral StrongREJECT, dev-25, `data/manifests/dev_25.csv`):**
- gpt-o4-mini **0.917 (22/24)** — `outputs/phase4_cot_baseline/…_strongreject.jsonl`
- Qwen3-14B white-box **0.818 (18/22)** — `outputs/phase5_qwen3_cot/…_strongreject.jsonl`
- DeepSeek-R1-Distill-Llama-8B **0.957 (22/23)**, uplift +0.597 — `outputs/phase4_hf_local/…`
- Phi-4-mini-reasoning **0.773 (17/22)**, +0.373 — `outputs/phase4_hf_local/…`
- gemma-3-4b-it **1.000 (25/25)**, clean 0.000 — `outputs/phase4_hf_local/…`
- external MaliciousInstruct transfer **0.848 SR (84/99)** / 0.737 Gemini — `outputs/phase_external/mech/`

**TROPT suffix baselines (Qwen3-14B, dev-train-20, per-behavior on own behavior, greedy):**
- GCG+PrefixCE **0.450 (9/20)**; MAC+PrefixCE **0.150 (3/20)**; no-attack/random **0.100 (2/20)**;
  min prefix-CE **0.0002** co-occurs with 45% success. — `outputs/phase3_tropt/eval_greedy/FREE_GENERATION_RESULTS.jsonl`
- **Do not rerun** unless: a bug is found, the ClearHarm protocol needs the parallel baseline, or a
  compute-matched GCG-vs-MAC comparison is missing (it is — see Phase C).

**Mechanistic (predictive-but-not-causal) — retain as detector-only, do NOT re-sweep:**
- Success-dir grouped-LOGO AUC ≈ 0.90 pre-generation (`prefill_last` L16 = 0.904; `think_content_1`
  L20 = 0.906) — `outputs/phase5_mechanistic/phase6_CvsD_auc.csv`
- Length confound: length-alone AUC 0.827; gain-beyond-length CI includes 0 (n=44) —
  `phase6_CvsD_confound_bootstrap.csv`
- Causal NULL everywhere: `outputs/phase7_causal/steer_*`, attention-temp `outputs/phase8_attn_causal/`,
  soft-opt `outputs/phase9_softopt/`. **Gate-3 = No, Gate-4 = No.**
- Detector (positive use): MLP AUC 0.925 / logistic 0.917 pre-generation — `outputs/phase17_detect/`.
  **Dataset-specific:** external transfer AUC 0.461 (chance).

**Category dataset (Phase 13) — descriptive DONE, controlled attacks NOT:**
- 336 suffixes analysed (`results/SUFFIX_TAXONOMY.csv`), transfer matrix
  (`results/CATEGORY_TRANSFER_MATRIX.csv`, off-diagonal per-behavior transfer NOT on disk — diagonal
  only), single-vs-multi gap **not like-for-like** (single = best-candidate upper bound n=12; multi =
  genuine 520-avg; model-family confounded). `docs/DATASET_ANALYSIS_REPORT.md`.

---

## 3. Non-negotiable working rules (inherited + sprint-specific)

Inherited from the original plan's Working Rules and the user's standing rules:
- **Do not edit** `RESEARCH_PLAN_DISTILLING_JAILBREAKS.md`.
- **Max 6 SLURM jobs concurrent**; L40S; no SLURM dependencies; cancel+resubmit if pending >30 min;
  smoke-test before scale; write results incrementally; resume only missing indices; never overwrite
  completed results.
- **No new model-weight downloads** without explicit approval; read cached weights offline
  (`HF_HUB_OFFLINE=1`). Open-weight, locally-controlled targets only for new attacks.
- **TROPT-first** (§3.3 of the sprint): prove TROPT cannot express the need (recipe / custom loss /
  `CombinedLoss` / `GCGPlusOptimizer` / proxy+text loss / minimal recipe wrapper) *before* writing
  new optimization infrastructure. TROPT runs under `TROPT/.venv/bin/python`.
- **Minimal code**: reuse the loaders/judge/eval harness in §1 (right column). Every new module gets
  a smoke or unit test.
- **Independent bug review** after every meaningful change (separate subagent), checking prompt
  construction, chat-template boundaries, suffix/target placement, thinking-token & EOS handling,
  truncation, tokenizer round-trip, train/test leakage, judge denominators, gradient/rank signs,
  resume, duplicate rows, stale cache.
- **Scientific integrity**: never report affirmative-prefix as success; never call a detector a
  mechanism (no causal evidence) or a defense (no adaptive/OOD test); keep negatives; label scaled
  reimplementations as *not* paper-faithful; never mix AdvBench/ClearHarm denominators or
  StrongREJECT/Gemini ASRs; keep empty/degenerate generations in the denominator; keep single- vs
  multi-instruction results separate everywhere.
- **Judge is not yet frozen** (`docs/JUDGE_VALIDATION.md`: human annotation pending, sample is
  bimodal). Freeze it (Phase B4) **before** any confirmatory objective claim.

---

## 4. Execution order (respecting compute limits and the gates)

Sequential, stopping at gates. Priorities 1–2 are CPU/small-GPU and run first.

### Priority 1 — CPU + documentation (no gate blocks these; do all)
1. **Phase A** — gap matrix (`docs/SPRINT_COMPLETION_GAP_MATRIX.md`), literature matrix
   (`docs/THINKING_ATTACK_LITERATURE_MATRIX.md`, resolving the CoT-Hijacking / H-CoT /
   context-hijacking / Doublespeak ambiguity), registry integrity audit
   (`docs/SPRINT_COMPLETION_AUDIT.md`, updating `results/EXPERIMENT_REGISTRY.csv`).
   - Registry integrity checks: every row → existing artifact; every ASR = n_success/n_total;
     dev/held-out disjoint; confirm `phase3_tropt_*` used `suffix_placement=user` (fix is in
     `poc_stage_gcg_early/config.py`, dated 2026-07-19); judge versions consistent; record
     branch/commit (`main` @ current HEAD; Phase-0 froze `36b7960`).
2. **Phase B (CPU parts)** — build ClearHarm manifests
   (`clearharm_opt15 / val15 / universal100 / reserve`, disjoint, category-documented, versioned
   targets, stable task_ids), extend the unified result schema (add mechanistic/steering/denominator
   fields flagged in the schema audit), and one validation script.
3. **Phase E1–E3 (CPU)** — full HF-dataset audit + strengthened taxonomy + the remaining descriptive
   analyses (goal-level & suffix-level bootstrap; do **not** treat rows sharing a suffix/instruction
   as independent). Reconcile the "336" selection vs the full response-level table.
4. **Phase G1 + G2 (CPU)** — prepare the SEMA academic code-access request (document date/status);
   build the reusable multi-turn simulator skeleton (reusing model+judge wrappers).
5. **Phase F1.1 / F2.0 (CPU)** — span annotations for existing CoT-Hijacking outputs; resolve the
   Doublespeak/context-hijacking reference (prepare a one-line clarification for Matan/Mahmood — see
   §6). No new generation yet.

### Priority 2 — small TROPT validation (Package 1)
Pin TROPT (commit, env, revisions → `docs/TROPT_CLEARHARM_BASELINE_REPORT.md` header); byte-verify
prompts against `poc_stage_gcg_early/model_adapter.py`; run **3-instruction** ClearHarm smoke: GCG
Prefix-CE, MAC Prefix-CE, and MAC(Prefix-CE proposals → behavioral candidate reranking). Verify
denominator handling. **Gate 1:** does ClearHarm reproduce the Prefix-CE↔behavior mismatch? If no →
audit targets/prompts/judge before proceeding.

### Priority 3 — behavioral objective (Phases D + Packages 2–3), gated
D2 rewards + `tests/test_jailbreak_rewards.py` + `docs/REWARD_VALIDATION.md` → D3 proxy-CE
behavioral reranking (label clearly: **NOT REINFORCE**) → D4 true REINFORCE estimator with RLOO
(`tests/` for signs, finite grads, zero-sum advantages) → Package 2 gradient-sign smoke → D5
soft-prompt upper bound (**Gate 3**) → D6 objective matrix D0–D8 (≥3 seeds) → **Gate 4**
(REINFORCE-MAC vs Prefix-CE-MAC). A negative here is a valid, reportable result.

### Priority 4 — category completion (Phase E4–E6)
Only after the behavioral objective is stable: controlled category-specific & category-balanced
multi-instruction MAC (TROPT `GCGMult`), within/cross-category held-out eval, universality-mechanism
bridge (does high-universality ⇒ stronger chat-template attention dominance via TROPT `GCGHij`?).

### Priority 5 — exact thinking mechanisms (Phase F), gated
F1.2 prompt ablations, F1.3 per-layer/head attention measurement, F1.4 candidate-head discovery
(discovery split only), F1.5 targeted causal interventions (head ablation/scaling/patching — the
mechanisms the *uniform*-temperature null did **not** rule out). **Gate 5:** only if a targeted
mechanism is causal, distil into a TROPT loss (F1.6) and compare to REINFORCE. In parallel, F2
context-hijacking behavioral reproduction + representation-convergence + causal tests.

### Priority 6 — SEMA (Phase G3–G8)
Scaled reimplementation (1.5–3B attacker / 3–8B victim, PEFT, T∈{1,3,5}) labelled **not
paper-faithful**; paper-faithful track only if official code + compute arrive. **Gate 7** documents
the compute/access gap honestly.

### Priority 7 — defense + final eval (Phases H + I)
Only after all attack families produce stable artifacts. **Gate 6** (detector survives held-out
families/datasets) before any general-defense claim; then adaptive attacks (§H3). Phase I opens
held-out sets **only after** method selection on dev/val.

---

## 5. First concrete run package (deliberately small; ≤6 jobs total)

- **Pkg 1 — TROPT ClearHarm smoke** (3 instr, 1 seed, short steps): GCG-PrefixCE / MAC-PrefixCE /
  MAC-PrefixCE-proposals+behavioral-selection. Validates prompts, reward, runtime; manual output
  inspection. → Gate 1.
- **Pkg 2 — REINFORCE gradient smoke** (1 instr, K=2, synthetic then one real judge reward, 5 steps):
  proves estimator correctness (signs, finiteness), **not** attack performance.
- **Pkg 3 — Soft behavioral upper bound** (5 instr, lengths 5 & 20, Prefix-CE vs REINFORCE reward, 1
  seed then 3). → Gate 3.
- **Pkg 4 — CPU dataset analysis** (Phase E1–E3): no GPU.
- **Pkg 5 — CoT exact-mechanism prep** (Phase F1.1 span annotation + head-attention extraction from
  *existing* successful/failed outputs; candidate-head discovery on discovery split): no new attack
  generation initially.

---

## 6. Open decisions requiring Matan / Mahmood input (do not block CPU work)

1. **"Context hijacking" reference.** No repo record fixes which paper Matan meant. Leading candidate
   = **In-Context Representation Hijacking / Doublespeak**; the TROPT `GCGHij` (bentov2025 =
   *Universal Jailbreak Suffixes Are Strong Attention Hijackers*, arXiv 2506.12880) is a *different*
   attention-hijack. Proceed on the Doublespeak assumption, document the ambiguity in the literature
   matrix, and confirm with Matan.
2. **ClearHarm acquisition.** Not vendored. Dataset (not weights) download — confirm licensing/source
   before fetching; document exact split sizes if the available dataset forces a change from
   15/15/100.
3. **5th model / non-CoT attack** — carried over open items from the mechanistic sprint
   (`RESEARCH_PLAN_PROGRESS_LOG.md` iter 143/144); relevant to Phase I model set.

---

## 7. Reuse map (build-new only where forced)

**Reuse (do not reimplement):**
- **Optimization** → TROPT `recipe_hub` under `TROPT/.venv`: `gcg__zou2023`, `mac__wang2024`
  (`GCGPlusOptimizer`, momentum, `jailbroken_model_name` distillation), `gcg_hij__bentov2025` /
  `attn_gcg__wang2024` (attention hijacking = `CombinedLoss([PrefillCELoss, AttentionEnhLoss])`),
  `gcg_mult__zou2023` (universal), `soft_prompt__schwinn2024`. Losses: `PrefillCELoss`,
  `ResponseHarmfulnessLoss` (black-box judge loss — validate/replace its judge), `SteeringActivationLoss`,
  `CombinedLoss`. Refusal dir: `TROPT/tropt/utils/refusal_dir.py`.
- **Model + chat-template + suffix-placement + free-gen + StrongREJECT** →
  `poc_stage4/qwen3_model.py` (`load_qwen3_model`, `load_gemma4_model`),
  `poc_stage_gcg_early/model_adapter.py` (+ `config.py` `suffix_placement="user"`),
  `poc_stage_gcg_early/evaluate_optimized_suffixes.py`, vendored `strong_reject/`,
  already bridged by `scripts/phase3_tropt_optimize.py` + `scripts/phase3_eval_triggers.py`.
- **Reward structure** → `poc_rl_loop/rl_reward_function.py` (`ResearchRewardFunction`,
  `RewardComponents`) — reuse the component design; note its existing `REINFORCEPolicy` is a
  bandit over discrete CoT-conditions, **not** token/soft-prompt RL.
- **Detectors / category** → `scripts/phase17_detector.py`, `scripts/phase17_confound.py`,
  `scripts/detector_groupkfold_audit.py`, `scripts/gcg_advbench_llm_taxonomy.py`.
- **Attack code** → `Chain_of_Thought_Hijacking/Hijacking/` (released prompts in
  `config/system_prompts.py`) + `refusal_direction/` (Arditi pipeline + processed HarmBench /
  MaliciousInstruct / StrongREJECT datasets).

**Build-new (no existing implementation — verified):** ClearHarm manifests; **RLOO** baseline;
the **token/soft-prompt REINFORCE estimator** as a TROPT loss/recipe (`reinforce_gcg` / `reinforce_mac`
via project-local extension modules, not upstream edits); a real **multi-turn simulator** and any
**SEMA** / **Doublespeak** method.

---

## 8. Decision gates (stop here; do not skip)

| Gate | Question | If NO | If YES |
|---|---|---|---|
| 1 | ClearHarm reproduces the Prefix-CE↔behavior mismatch? | audit targets/prompts/judge/model | → behavioral optimization |
| 2 | behavior-aware reranking beats Prefix-CE? | still go to true REINFORCE (not equivalent) | continue |
| 3 | REINFORCE soft upper bound improves behavioral ASR? | audit reward + gradient; test reward variants; **do not** launch discrete sweep | → REINFORCE-MAC |
| 4 | REINFORCE-MAC beats Prefix-CE-MAC? | report valid negative; diagnose variance/candidate/realizability | → category + held-out scaling |
| 5 | CoT/context internal signal is **causal** (head/position-specific)? | retain as detector only; **do not** distil | soft-opt → TROPT-MAC → compare to REINFORCE |
| 6 | detector survives held-out families + datasets? | not a general defense; do OOD/mechanism-specific | test adaptive attackers |
| 7 | SEMA reproducible at available compute? | complete scaled reimpl; document gap; **not** paper reproduction | run paper-faithful track |

---

## 9. Definition of completion

**WS1 Category:** dataset fully audited; validated taxonomy; complete transfer matrix; single-vs-multi
separated; controlled category-specific MAC done; within/cross-category held-out done.
**WS2 Thinking:** CoT-Hijacking exact head/span mechanism tested causally; context-hijacking reference
resolved + reproduced; SEMA access documented + ≥ scaled multi-turn evaluated; literature gaps
documented; defense tested against >1 attack family.
**WS3 Objective:** residual objective retained as negative; behavioral REINFORCE implemented +
evaluated; TROPT-MAC integration done; soft upper bound done; any new mechanistic objective passes a
causal gate before discrete opt; behavioral vs mechanistic directly compared.
**Best practice:** TROPT used wherever appropriate; MAC primary + fair vs GCG; ClearHarm primary for
new claims; greedy primary eval; single/multi separated; registry + artifacts complete; every
headline number independently verified.

---

## 10. Verification (how each phase is checked end-to-end)

- **Reproducibility:** same suffix + greedy config → identical output & score (Phase-2 rule; still
  needs GPU generate-twice verification — do it in Pkg 1). `scripts/validate_eval_results.py` asserts
  fields, dup rows, split leakage, score range, denominator consistency, single code_commit.
- **Every code change:** run its unit/smoke test, run a minimal smoke experiment, then an independent
  adversarial subagent review (§3 checklist); fix substantive findings; log in
  `docs/SPRINT_COMPLETION_EXECUTION_LOG.md`.
- **Numbers:** always report numerator/denominator + ASR + uplift + bootstrap CI; never percentages
  alone; keep empty/degenerate in the denominator; per-category + per-instruction + seed variance.
- **Registry:** append-only; one row per run with the §22 run_id schema; artifacts under a fixed
  hierarchy.

---

## 11. Deliverables (produced during execution)

`docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md` (this file) · `…_EXECUTION_LOG.md` · `…_GAP_MATRIX.md` ·
`…_AUDIT.md` · `THINKING_ATTACK_LITERATURE_MATRIX.md` · `TROPT_CLEARHARM_BASELINE_REPORT.md` ·
`REWARD_VALIDATION.md` · `REINFORCE_TROPT_IMPLEMENTATION.md` · `REINFORCE_OBJECTIVE_REPORT.md` ·
`CATEGORY_ATTACK_COMPLETION_REPORT.md` · `COT_HIJACKING_EXACT_MECHANISM_REPORT.md` ·
`CONTEXT_HIJACKING_REPRODUCTION_REPORT.md` · `SEMA_REPRODUCTION_STATUS.md` ·
`SEMA_SCALED_REIMPLEMENTATION_REPORT.md` · `CROSS_FAMILY_ADAPTIVE_DEFENSE_REPORT.md` ·
`SPRINT_FINAL_SYNTHESIS.md` (with the request → completed/partial/blocked/negative table).
Results CSVs: `TROPT_CLEARHARM_BASELINES`, `REINFORCE_OBJECTIVE_COMPARISON`,
`CATEGORY_TRANSFER_MATRIX_V2`, `CATEGORY_CONTROLLED_OPTIMIZATION`, `SUFFIX_TAXONOMY_V2`,
`SEMA_MULTITURN_RESULTS`, `DEFENSE_OOD_RESULTS`, `ADAPTIVE_ATTACK_RESULTS`.
