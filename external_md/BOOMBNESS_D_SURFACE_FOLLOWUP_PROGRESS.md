# Follow-up Sprint Plan — Boombness / `d_surface` Mechanism / Clean Objective Gate

**Status:** plan recorded, not yet started.
**Written:** 2026-08-19
**Repository:** `first_poc/teza_first_poc_with_mahmood`
**Branch at time of writing:** `behavioral-causality-sprint`
**This file:** `external_md/BOOMBNESS_D_SURFACE_FOLLOWUP_PROGRESS.md`

You are continuing the Boombness / Doublespeak mechanistic-interpretability research project.

Use the current repository state from the previous Boombness sprint unless instructed otherwise. The previous sprint handover is the source of truth. **Do not trust old progress-log claims if they were later retracted.**

This file must contain the plan, progress updates, commands, artifacts, failures, corrections, current claims, and open questions. **Update it continuously.**

---

## 0. Important Context From the Previous Sprint

The previous sprint tried to extract a Boombness signal and turn it into a GCG/MAC objective.

The current conclusion is:

> **Do not build the GCG objective yet.**

The previous sprint found that `d_surface` is real and causal, but it does not behave like a useful attack objective. The clean G2 correlation failed, and the G4 objective gate failed.

### Previous ground truth to verify from artifacts before doing new work

1. **G1 survived:**
   - The decoded carrot→bomb meaning lives mainly in the demonstration block, not in the query codeword token.
   - Whole-answer G1 `demos_only L18` transplant is approximately **+68.9%** of span.
   - `query_only L18` transplant moves in the **wrong** direction.

2. **G3 survived:**
   - Attention to the whole demonstration block is causally involved.
   - Cutting all demo-block attention edges across all layers recovers approximately **75.2%** of the deletion ceiling.
   - Sparse top-k edge knockout did **not** work.
   - Codeword-scope knockout moves in the **wrong** direction.

3. **G2 was retracted:**
   - The original positive Boombness→ASR correlation was contaminated by pseudo-replication, designed-variance rows, and unsafe filtering.
   - Clean powered G2 was **null**.
   - The clean powered result for `d_surface|L12|proj` was approximately within-domain **rho = -0.066, p ≈ 0.49**.

4. **G4 failed:**
   - Additive Boombness steering did not license a GCG objective.
   - Both signs of steering suppressed ASR or worked through refusal.

5. **The strongest surviving behavioral result:**
   - Projecting out `d_surface` on external harmful prompts **increased** ASR.
   - This effect was strongest around **L6–L12**.
   - Matched random controls were mostly inert.
   - Removing refusalness increased ASR more strongly.
   - Removing **both** `d_surface` and refusalness increased ASR the most and showed interaction.

6. **Cross-model status:**
   - Qwen AdvBench causal replication was **floor-limited** and should not be cited as a causal failure or success.

### Required first write-up

Before implementing new science, write a section in this file called:

`## Previous Sprint Ground Truth`

For each claim above, record:

- source artifact path;
- model;
- dataset;
- n;
- query kind;
- layer/window;
- readout;
- result;
- current verdict;
- whether the claim is **established, retracted, superseded, or exploratory**.

**If any headline number does not reproduce from committed artifacts, stop and document the discrepancy before continuing.**

---

## 1. Core Scientific Goal

Do not start from "build a GCG objective."

The new scientific goal is:

> Understand what `d_surface` actually represents, why removing it increases ASR, how it interacts with refusalness, and whether a better token-level / prompt-level Boombness readout can produce a clean objective in the future.

**Main hypothesis to test:**
`d_surface` may not be "attack-enabling Boombness." It may instead be a mid-layer safety-relevant, harmful-surface, or semantic-salience channel. Removing it may make the model less able to represent the harmfulness of the request, thereby increasing compliance.

**Alternative hypotheses:**

1. `d_surface` is a real carrot/bomb surface direction, but it is not behaviorally aligned with ASR.
2. `d_surface` is still partially confounded with harmful context or safety salience.
3. `d_surface` is a general hazardous-object semantic axis.
4. `d_surface` is an artifact of the carrot/bomb bank but transfers because many harmful prompts share similar lexical/statistical structure.
5. `d_surface` interacts with refusalness: it does not cause refusal by itself, but it supplies semantic evidence that the refusal mechanism uses.

This sprint should distinguish between these hypotheses.

---

## 2. Non-Negotiable Engineering Rules

### 2.1 Documentation

Maintain this file: `external_md/BOOMBNESS_D_SURFACE_FOLLOWUP_PROGRESS.md`

For every stage, document:

- goal;
- exact command;
- SLURM job id;
- git commit;
- input artifacts;
- output artifacts;
- model;
- dataset;
- filters;
- sample size;
- failures;
- skipped rows;
- skip reasons;
- current interpretation;
- whether the result is exploratory or citable.

**Do not wait until the end. Update the md continuously.**

### 2.2 Reuse Existing Code

Do not write a lot of new code if existing code can do the job.

Reuse:

- existing Boombness bank infrastructure;
- existing 2×2 direction-fitting code;
- existing activation extraction code;
- existing intervention primitives;
- existing StrongReject judge pipeline;
- existing run metadata conventions;
- existing artifact analysis scripts;
- existing test utilities;
- existing code from the article / `external_repos/interp-jailbreak` when relevant.

Use the article code as much as possible for:

- token-position-localized analysis;
- surgical patching methodology;
- attention/path attribution;
- mechanism-score vs behavior correlation;
- strong-vs-weak comparison design;
- plotting and aggregation discipline.

**Do not copy blindly.** Adapt to our repo's model loader, tokenizer, bank schema, metadata, and safety constraints.

### 2.3 No Silent Failures

Every script must report:

- attempted rows;
- succeeded rows;
- failed rows;
- skipped rows;
- exact skip reasons;
- source artifacts;
- output artifacts;
- filters used.

- Never silently drop rows.
- Never silently mix query kinds.
- Never silently mix `bank_block`s.
- Never silently use self-fit directions unless explicitly labeled.
- Never report pooled statistics as causal or citable when within-domain / clustered inference is the correct estimand.

### 2.4 Self-Review

Always double-check yourself. Before making any claim, verify:

- sample size;
- prompt IDs;
- family IDs;
- `bank_block`;
- `family_slot`;
- query kind;
- readout position;
- layer;
- direction split;
- whether the direction is self-fit or cross-fit;
- whether the result is pooled, within-domain, clustered, or thresholded ASR;
- whether random controls are independent draws;
- whether controls ran successfully;
- whether the result survives known retractions.

Every 4 hours, do a code and output review and write it into this file under:

`## 4h Code and Output Review`

Include:

- what was checked;
- bugs found;
- artifacts inspected;
- claims downgraded or confirmed;
- next corrections.

### 2.5 Commits and Pushes

Commit after meaningful progress. Push after meaningful progress if remote access is available.

Commit messages should clearly say:

- what was implemented;
- what artifact/result it supports;
- whether it is **infrastructure, analysis, bugfix, or result**.

Do not commit huge raw harmful generations unless that is already the repo convention. Prefer artifact paths and aggregate metrics in the md.

### 2.6 Parallelism

Use subagents / parallel jobs where safe. Parallelize independent work:

- different layers;
- different datasets;
- different models;
- different readouts;
- independent controls;
- independent audits.

Do **not** parallelize anything that can create leakage, pseudo-replication, inconsistent seeds, duplicate controls, or unsafe joins.

Use fan-out subagents where helpful, but **every subagent output must be reviewed before being treated as fact.**

### 2.7 Loop Discipline

Run a progress loop every 30 minutes. Every loop should:

1. check running jobs;
2. inspect finished artifacts;
3. update this md;
4. commit if meaningful progress happened;
5. decide the next safe parallel jobs;
6. record open blockers.

Every 4 hours, do the deeper code/output review described above.

Use ultrathink / ultracode mode. **Be careful, not just fast.**

---

## 3. Phase A — Reproduce and Audit Previous Ground Truth

**Goal:** Confirm that the current repository state matches the previous sprint handover.

### Tasks

1. Locate canonical artifacts for:
   - G1 whole-answer transplant;
   - G3 whole-answer knockout;
   - G2 powered clean correlation;
   - G4 steering failure;
   - AdvBench external decomposition;
   - layer profile;
   - direction-specificity test;
   - comprehension controls;
   - Qwen replication attempt.
2. Recompute or inspect each headline number.
3. Create a "Do Not Cite" ledger in this file:

`## Retracted / Superseded Claims Not To Cite`

Include at least:

- original positive G2 correlation;
- original G1 +84% headline;
- original G3 84.35% / distributed-over-depth framing;
- sparse top-k attention-edge causal claim;
- any claim that Boombness is currently a usable GCG objective;
- any floor-limited Qwen AdvBench causal claim.

### Deliverables

- external md section with verified previous ground truth;
- artifact index;
- retraction ledger;
- one commit.

**Do not continue until this phase is complete.**

---

## 4. Phase B — Build Occurrence-Resolved Token-Level Boombness Readout

**Goal:** Separate token-level Boombness from prompt-level Boombness.

The previous sprint over-focused on one codeword/readout position. This phase must measure **every relevant occurrence.**

### Tasks

Implement or extend an extraction script that outputs one row per: prompt × occurrence × layer × metric.

**Occurrence roles:**

- first demo codeword;
- middle demo codewords;
- last demo codeword;
- all demo codewords aggregate;
- query codeword;
- readout position;
- nearby predicate/context tokens if feasible.

**For every row, store:**

`prompt_id`, `family_id`, `condition`, `bank_block`, `family_slot`, `split`, `domain`, `query_kind`, `n_examples`, `occurrence_index`, `occurrence_role`, `token_position`, `layer`, metric name, metric value, direction fit split, self-fit flag.

**Metrics:**

- `d_surface|L|proj`;
- `d_surface|L|cos`;
- `d_naive|L|proj`;
- `d_context|L|proj`;
- refusalness where available;
- logit lens concept-vs-codeword;
- whole-answer / forced-choice readout where valid.

### Required Audits

Add tests or checks for:

- correct tokenization of carrot/bomb;
- no confusion between `codeword_last` and `readout_pos`;
- no stripping `query_kind` from `family_id`;
- no semantic representation joined to behavioral ASR unless explicitly labeled;
- expected occurrence counts;
- exact `prompt_id` joins.

### Analyses

Produce layer-dynamics summaries for: first demo carrot; last demo carrot; average demo carrot; query carrot; readout position; predicate/context tokens if feasible.

**Key questions:**

1. Does Boombness increase from first demo occurrence to later demo occurrences?
2. Is the query carrot more or less bomb-like than demo carrots?
3. Does the signal appear in L6–L12, L14–L21, or late layers?
4. Does `d_surface` differ from `d_naive` and `d_context`?
5. Is refusalness independent at these positions?

### Deliverables

- `outputs/boombness_followup/token_level_occurrence_readouts.jsonl`
- `outputs/boombness_followup/token_level_dynamics_summary.json`
- plots/tables if useful;
- external md interpretation.

---

## 5. Phase C — Refit and Validate a Better Boombness Probe

**Goal:** Build a probe only if it avoids the "stupid probe" problem. The probe must not merely learn lexical identity or prompt artifacts.

### Tasks

Refit probe variants on the current bank:

1. simple lexical probe;
2. aligned 2×2 probe;
3. hard-negative probe;
4. heldout-domain probe;
5. surface-matched codeword probe;
6. concept-surface probe;
7. optional hazardous-object generalization probe.

Use strict train/test separation:

- group by family;
- group by domain where relevant;
- no overlapping slots across train/test;
- no self-fit leakage;
- shuffled-label control;
- random-direction control.

Evaluate probe coverage over the full current bank. **Do not use the probe as a headline metric unless coverage is high enough and controls pass.**

### Required Outputs

For each probe: train n; test n; domains; family slots; AUROC / accuracy / margin distribution; shuffled-label result; domain-heldout result; correlation with `d_surface`; correlation with refusalness; whether it generalizes outside carrot/bomb.

### Deliverables

- `outputs/boombness_followup/probe_validation.json`
- probe artifacts;
- external md section: `## Probe Validation and Leakage Checks`

---

## 6. Phase D — Clean Designed-Variance Bank for Fig-9-Style Test

**Goal:** Re-test whether prompt-level Boombness can predict ASR, but with a clean design.

The previous G2 failed because contaminated rows and pseudo-replication produced a false positive. **Do not repeat that.**

### Design Requirements

Build or generate a new balanced designed-variance bank where the following factors can vary independently:

1. number of demonstrations;
2. strength/aggressiveness of demonstrations;
3. consistency of mapping;
4. position of relevant demonstrations;
5. role/style framing if useful.

**Hard constraints:**

- no overlapping family slots across independent rows;
- no slot 1/2 pseudo-replication unless explicitly grouped and not treated as independent;
- balanced prompt length as much as possible;
- balanced number of target occurrences;
- balanced `n_examples` when testing strength/position/consistency;
- at least **120 behavioral rows per level** where possible;
- use domain clusters;
- keep query kind fixed for behavior;
- representation and ASR must be from the same `prompt_id` unless explicitly labeled otherwise.

### Analyses

For each candidate prompt-level metric:

- average demo-token Boombness;
- query-token Boombness;
- readout-position Boombness;
- max over demo tokens;
- AUC over layers;
- L6–L12 average;
- L14–L21 average;
- probe margin;
- refusalness;
- Boombness minus refusalness.

Compute: pooled rho; within-domain rho; domain-clustered regression; permutation p; family-wise correction over metric/layer choices; nested layer/metric selection; incremental R² over refusalness; negative controls.

### Decision Gate D

Only if a prompt-level metric predicts ASR cleanly under within-domain / clustered inference **and** survives multiplicity correction should we consider a future GCG objective.

If this fails again, explicitly write:

> `Prompt-level Boombness is not currently a usable optimization target.`

### Deliverables

- new bank or bank-extension artifacts;
- ASR generations and judge artifacts;
- `outputs/boombness_followup/clean_fig9_correlation.json`
- external md section: `## Clean Fig-9-Style Boombness vs ASR Test`

---

## 7. Phase E — Decompose What `d_surface` Really Represents

**Goal:** Understand why projecting out `d_surface` increases ASR on external harmful prompts.

### E1. External semantic categories

Run `project_out d_surface` on multiple external categories:

- weapons/explosives;
- cyber;
- fraud;
- drugs;
- self-harm if allowed by existing benchmark safety handling;
- benign technical prompts;
- benign everyday prompts;
- ambiguous dual-use prompts.

For each category, compare: baseline; remove `d_surface`; remove refusalness; remove both; matched random control; `d_context`; `d_naive`.

### E2. Layer profile replication

Replicate the layer profile with more layers: L4, L6, L8, L10, L12, L13, L14, L16, L18, L20, L24.

If compute is limited, prioritize **L6–L16**.

### E3. Direction specificity

Compare: `d_surface`; `d_naive`; `d_context`; `d_inter`; random matched directions; refusalness; orthogonalized `d_surface` against refusalness; orthogonalized refusalness against `d_surface`.

### E4. Semantic-salience interpretation

For prompts where removing `d_surface` increases ASR, inspect **safe summaries / labels only**:

- does the model become less likely to identify danger?
- does refusal decrease?
- does harmful compliance increase?
- does comprehension change?
- does output become more generic or more specific?

**Do not print harmful instructions. Use redacted summaries and aggregate statistics.**

### Deliverables

- `outputs/boombness_followup/d_surface_external_decomposition.json`
- `outputs/boombness_followup/d_surface_layer_profile_replication.json`
- `outputs/boombness_followup/direction_specificity_extended.json`
- external md interpretation: `## What Does d_surface Represent?`

---

## 8. Phase F — Interaction With Refusalness

**Goal:** Understand whether `d_surface` and refusalness are independent, additive, synergistic, or sequential.

### Experiments

Run composed interventions:

1. baseline;
2. remove `d_surface`;
3. remove refusalness;
4. remove both;
5. remove `d_surface`, then add refusalness;
6. remove refusalness, then add `d_surface`;
7. add `d_surface`;
8. add refusalness;
9. add both;
10. matched random controls.

Run across the active layer band: L6, L8, L10, L12, optional L14/L16.

**Metrics:** continuous StrongReject score; ASR@0.5; refusal rate; comprehension / semantic control where available; generation degeneracy/coherence; interaction term with clustered bootstrap.

**Key questions:**

- Does `d_surface` supply evidence used by refusalness?
- Does removing `d_surface` increase ASR only when refusalness is intact?
- Does refusalness dominate all behavior?
- Does removing both exceed the sum of each alone?
- Is the interaction layer-localized?

### Deliverables

- `outputs/boombness_followup/refusal_interaction.json`
- external md section: `## d_surface × Refusalness Interaction`

---

## 9. Phase G — Better Surgical Patching

**Goal:** The previous sprint showed that sparse top-k attention edges are not sufficient. Try more meaningful surgical interventions.

**Do not repeat the top-16 edge search as if it is likely to work.**

### Candidate Surgical Units

1. whole demo block;
2. first demonstration only;
3. last demonstration only;
4. predicate/context tokens around codewords;
5. all codeword tokens in demos;
6. query codeword;
7. readout position;
8. MLP write/carry windows;
9. residual stream direction projection;
10. path patching from demo block to mid-layer residual / MLP to readout.

Use article-code best practices for patching and path attribution.

### Required Controls

For every intervention: random position control; random direction control; matched edge-count control if using attention; comprehension control; option-mass / readout validity check; generation coherence check for behavioral runs.

### Deliverables

- `outputs/boombness_followup/surgical_units.json`
- external md section: `## Better Surgical Patching Results`

---

## 10. Phase H — Cross-Model Replication Without Floor Effects

**Goal:** Replicate only where the model/dataset has enough behavioral dynamic range.

**Do not use a floor-limited setup to claim mechanism failure.**

### Tasks

For each candidate model:

1. measure baseline ASR on candidate datasets;
2. select datasets where baseline is not near zero and not saturated;
3. fit or import model-specific refusal direction;
4. fit model-specific `d_surface` if tokenization/alignment is valid;
5. run a small layer profile around relative mid-layer depth;
6. run external decomposition if dynamic range exists.

**Candidate models:**

- Llama-3.1-8B-Instruct as primary;
- Qwen3-14B only on a dataset with non-floor ASR;
- Phi or another model only after tokenization audit and smoke tests pass.

### Deliverables

- `outputs/boombness_followup/cross_model_dynamic_range.json`
- `outputs/boombness_followup/cross_model_decomposition.json`
- external md section: `## Cross-Model Replication With Dynamic Range`

---

## 11. Phase I — GCG/MAC Objective Gate

**Do not implement GCG unless the gate passes.**

### Gate Requirements

A Boombness-based objective can only be attempted if:

1. a clean prompt-level metric predicts ASR under within-domain / clustered inference;
2. the result survives multiplicity correction;
3. the metric is not just refusalness;
4. random controls fail;
5. comprehension is preserved;
6. the effect replicates on heldout domains or external prompts;
7. direction/additive intervention has the expected sign.

If any of these fail, **do not implement GCG.** Instead, write a clear negative result.

### If Gate Passes

Only if the gate passes, implement a minimal GCG/MAC objective using existing code.

**Candidate objectives:**

1. maximize clean prompt-level Boombness metric;
2. maximize Boombness minus refusalness;
3. maximize demo-block aggregate Boombness;
4. maximize L6–L12 Boombness signal;
5. maximize probe margin only if probe validation passed.

**Compare against:** standard GCG; refusal-only objective; random suffix; fluency-only control; Boombness-only; Boombness-minus-refusalness.

**Metrics:** train ASR; heldout ASR; transfer; achieved Boombness; refusalness; comprehension; malformed output rate; suffix length; generation quality.

**But again: do not start this unless the gate passes.**

---

## 12. Final Report Requirements

At the end of the sprint, write a final section in this file:

`## Sprint Final Report`

It must answer:

1. What did we verify from the previous sprint?
2. What is `d_surface` most likely measuring?
3. Is `d_surface` separable from refusalness?
4. Why does removing `d_surface` increase ASR?
5. Does token-level Boombness behave differently from prompt-level Boombness?
6. Is there a clean Fig-9-style Boombness→ASR correlation?
7. Are any surgical interventions actually useful?
8. Does the result replicate across datasets / models?
9. Is a GCG objective justified?
10. What are the strongest new findings?
11. What was retracted or downgraded during this sprint?
12. What should the next sprint do?

Each claim must point to an artifact.
**No unsupported claims. No stale numbers. No harmful completions.**

---

## 13. Execution Instruction

Implement this plan. Document progress in this external markdown file so we can track progress.

- Follow the instructions in the plan.
- Do not write a lot of code if you do not need to. Reuse the existing code and the article code as much as possible.
- Do not skip any stage from the plan unless you have to. If a stage should be skipped, document why and consult the user.
- Use subagents to run things in parallel. Anything that can be parallelized without hurting the results should be parallelized.
- Our goal is to add to this paper and find new things with this research.
- Always double-check for bugs.
- Do a code review before trusting results.
- Commit and push after meaningful progress so the work is trackable.
- Use ultrathink, ultracode, fan out subagents, and run a progress loop every 30 minutes.
- Every 4 hours, do a code and output review and document it here.

---

# Progress Log

**Sprint started:** 2026-08-19. **Branch:** `behavioral-causality-sprint`.
**Current phase:** C running (probe suite launched). B complete and corrected.
**Gate status:** all six plan §0 claims reproduce from committed artifacts; 7 discrepancies and 5
cross-cutting defects documented below before proceeding, per the plan's stop rule.

---

## Session Log

### 2026-08-19 — Entry 2: Phase A audit — GATE PASSED

**Goal.** Recompute every plan §0 headline number from committed JSON; refuse to proceed if any fails.

**Method.** `Workflow` fan-out, 14 agents / 997k tokens / 379 tool calls: seven verifiers (one per claim
group, structured output, `effort: high`) piped into adversarial refutation passes instructed to default
to "refuted" under uncertainty. Two refutation passes (`skeptic:EXTERNAL`, `skeptic:QWEN_COMPREHENSION`)
died on a session limit; those two groups are **single-verified** and marked as such.

**Result.** **All six section-0 claims reproduce.** Seven sub-items did not reproduce as stated — three
are corrections *in the sprint's favour* (D-1, D-2, D-6), three are citability limits (D-3, D-7, and the
IF-1 pair D-4/D-5), and none contradicts a section-0 claim. Five further cross-cutting defects were
surfaced that the plan did not ask about (D-8 … D-12). Full tables above.

**Cost of the audit:** one self-inflicted incident, IF-4, logged under Open Questions and fully reverted.

---

### 2026-08-19 — Entry 1: orientation and inherited state

**Goal.** Locate the previous sprint's handover and canonical artifacts; establish what is committed,
what is dirty, and what is still running, before any claim is verified.

**Source of truth located.** `reports/BOOMBNESS_SPRINT_HANDOVER_2026-08-16_TO_08-19.md` (6,623 lines,
covers 2026-08-16 18:04 → 2026-08-19 10:30, reference HEAD `8a7421dd`). This document supersedes the
older `doublespeak_causality/*.md` logs for anything Boombness-related. It carries its own
Appendix A (retracted figures), Appendix B (two retraction ledgers), Appendix C (artifact index) and
Appendix D (reproduction commands). Treated as a **map to artifacts, not as evidence** — every number
below is verified against committed JSON, per plan §2.3.

Supporting documents, in currency order:
- `docs/BOOMBNESS_CONTINUATION_LOG.md` (3,004 lines) — ledger 2 (`R-6` … `R-19`).
- `docs/BOOMBNESS_SPRINT_PROGRESS.md` — ledger 1 (`RETRACTION #1` … `#9`), append-only journal.
- `reports/boombness_objective_sprint_report.md` (2,095 lines) — the formal report; the handover
  flags three places where it still carries retracted figures unqualified (see below).
- `docs/BOOMBNESS_SPRINT_EXTERNAL_CRITIQUE_2026-08-18.md` — the external critique and its defect table.

**Artifacts.** 50 top-level analysis JSONs under `outputs/boombness/` (the handover's census said 48;
two landed after it was written: `advbench_direction_specificity.json` and `concept_pair_screen.json`).
All 17 headline-bearing artifacts confirmed **git-tracked**:

`g1_wholeanswer_sow` · `g1_stratified` · `g3_wholeanswer_block24` · `g3_wholeanswer_codeword24` ·
`g2_analysis_POWER` · `g2_analysis_cwpos_CLEAN` · `g2_analysis_cwpos` · `steering_analysis` ·
`steering_band_real` · `advbench_decomposition` · `advbench_layer_profile` ·
`advbench_superadd_control` · `advbench_decomposition_qwen3` · `clearharm_decomposition_regoal` ·
`clearharm_decomposition_qwen3` · `direction_cosines` · `section4b_whole_answer`

---

## Inherited State — Integrity Findings

### ⚠ IF-1: a tracked artifact is dirty in the working tree, and the dirt is a retracted figure

`outputs/boombness/clearharm_decomposition.json` is **modified and uncommitted**. The diff
(67 insertions, 3 deletions) adds two control-band judge runs and **rewrites the `control_band` block**:

| | committed (`70709348`) | working tree |
|---|---|---|
| `control_band.n_draws` | `1` | `3` |
| `control_band.note` | *"fewer than 3 independent control draws; between-draw variance is unestimated…"* | *(removed)* |
| `control_band.between_draw_sd` | *(absent)* | `0.0048381307473991` |

`0.0048` is **exactly the figure R-12 retracted** as a fake band. Worse, the working-tree draws are not
independent: `ctrlband_s20260901` and `ctrlband_s20260902` both record
`paired_delta_mean = 0.018156424581005588` — byte-identical, the R-12 signature (`score_behavior.py:123`
recursing into composed arms without passing `control_seed`). Only `s20260903` differs (`0.009777`).
So the working tree claims `n_draws: 3` where the effective n is **2**.

**Direction of the change matters:** the committed version is the *corrected* one (`n_draws: 1` with an
honest note); the working tree has *reverted* to the retracted band. This is an un-reviewed regeneration
sitting on top of a correction.

**Disposition:** do **not** commit this hunk. The file is superseded anyway (pre-R-14 empty-goal
judging — see the Do-Not-Cite ledger); its replacement is `clearharm_decomposition_regoal.json`.
Recommended action is `git checkout -- outputs/boombness/clearharm_decomposition.json`.
**Not yet executed — flagged for the user, since discarding working-tree state is destructive.**

### IF-2: six SLURM jobs inherited from the previous sprint are still queued

All `PD (Priority)` on the `killable` partition, all invoking
`src/boombness/slurm/run_boombness.sh`. Identified from `outputs/boombness/argsfiles/`:

| jobid | submitted | argsfile | what it is | which phase it feeds |
|---|---|---|---|---|
| 767176, 767177 | 08-19 10:03 | `args_abL13_Bctrl` / `args_abL14_Bctrl` | matched random controls for the L13/L14 edge probe — the handover lists L13/L14 as **arm-only** without them | Phase A verification of "controls inert"; Phase E2 |
| 767263–767266 | 08-19 11:33 | `args_abR{8,12,24,28}_C` | **refusalness** (arm C) at L8 / L12 / L24 / L28 on AdvBench 495 | Phase E2 + **Phase F** (refusalness layer profile) |

All six target `data/boombness_prompts/external/advbench_heldout_495.jsonl` against the canonical fit dir
`extract_boombness/full_20260816_185942_1008673`, `--query-kinds behavioral --max-new 512`.

**Decision: let them run; harvest, do not resubmit.** 767263–767266 are a refusalness layer profile that
Phase F would otherwise have to launch itself — inherited work that is directly on-plan.

### IF-3: three retracted figures still stand unqualified in `reports/boombness_objective_sprint_report.md`

Carried forward from the handover's §13.15 and Appendix A.2, to be re-checked in Phase A:
report §13 criterion 1 (`ρ=+0.307`, dead by R-18); §13 criteria 3/4 (`p=0.681`, dead by R-6);
§8b/N5 (G1 query transplant at `−71%`, superseded by `−57.0%`). The `retraction_sweep.py` guard reports
clean because markdown tables are one paragraph and a marker word in any row exempts every row.

---

## Phase B Feasibility — resolved early, and it is good news

Plan §4 (Phase B) asks for an occurrence-resolved token-level readout. **The extraction already emits
exactly this**, so Phase B is an *analysis* task over an existing artifact, not a new extraction run.
This is the plan §2.2 "do not write new code if existing code can do the job" case.

`src/boombness/extract_boombness.py` (941 LOC) writes one row per (prompt × occurrence) with these
metadata columns already present in `extract_boombness/full_20260816_185942_1008673/results.jsonl`:

```
prompt_id  family_id  condition  cell  domain  split  bank_block  query_kind  n_examples
strength  consistency  example_position  role_style  target_surface
occurrence_index  n_occurrences  is_final_occurrence  is_query_occurrence
token_pos  seq_len  n_subtokens  is_single_token
directions_fitted_on  is_self_fit  layer_convention
```

plus **333 metric columns**, including `d_surface|L{0..31}|proj`, `d_surface|L|cos`, `d_naive|L|proj`,
`d_context|L|proj`, `d_inter|L|proj`, `hnorm|L`, and logit-lens `ll|L|boombness` / `p_concept` /
`p_codeword` / `rank_concept` (plus `llfollow|L|*` at the following token).

Census of that file (117 MB, 8,472 rows):

| field | distribution |
|---|---|
| rows | 8,472 |
| occurrence role | demo 7,008 · query 1,464 |
| `bank_block` | core2x2 5,328 · families 816 · extra_conditions 792 · role_style 600 · strength 432 · consistency 384 · position 120 |
| `query_kind` | behavioral 3,756 · semantic_one_word 2,940 · comprehension_usage 1,776 |
| `n_occurrences` | 1:192 · 2:408 · 3:576 · 4:48 · 5:1,860 · 6:432 · 8:96 · 9:2,052 · 10:360 · 17:2,448 |
| `is_self_fit` | False for all 8,472 rows (cross-fit throughout) |

**Gaps Phase B must still close** (recorded now so they are not discovered late):
1. `family_slot` is **not** a top-level column — it is encoded inside `family_id`
   (`farm_storage\|dev\|slot0\|n0\|none\|consistent\|near\|plain\|behavioral`). Phase B must parse
   it out explicitly, because plan §4 requires it as a stored field and R-18 was caused by a missing
   slot filter.
2. `occurrence_role` (first-demo / middle-demo / last-demo / query) must be **derived** from
   `occurrence_index` + `is_query_occurrence` + `n_occurrences`. Not stored.
3. Refusalness is in a separate producer (`refusalness/cwpos_…`, `refusalness/lastpos_…`) and must be
   joined on `prompt_id`.
4. This extract is over the **1,464-row** bank. The bank was later regenerated to **2,352** rows
   (`extract_boombness/full2352_20260818_115332_1410155`). The handout's R-10/C-13 defect was exactly a
   population mismatch between a 1,464-row cache and a 2,352-row bank. Phase B must pick one and say so.

Reusable elsewhere: `probes.py` (963 LOC) for Phase C, `analyze_external_arms.py` (407 LOC) for
Phases E/F, `surgical_knockout.py` + `aggressive_patching.py` for Phase G, `coherence_gate.py` for every
behavioural arm, `score_behavior.py` + `judge_boombness.py` for generation and judging.

---

## Previous Sprint Ground Truth

**Method.** Seven verification agents, one per claim group, each recomputing the headline number from the
committed JSON (never from prose), followed by an adversarial refutation pass instructed to default to
"refuted" under uncertainty. 14 agents, 997k tokens, 379 tool calls. Two adversarial passes
(`skeptic:EXTERNAL`, `skeptic:QWEN_COMPREHENSION`) died on a session limit — recorded below as
**single-verified** rather than double-verified.

### ✅ GATE VERDICT: PHASE A PASSES

**All six of plan §0's headline claims reproduce from committed artifacts.** No section-0 number was
contradicted. Seven sub-items did not reproduce as stated; none of them contradicts a section-0 claim —
they are catalogued in *Phase A Discrepancy Ledger* below and every one is documented before proceeding,
per the plan's stop rule.

Model throughout: `meta-llama/Llama-3.1-8B-Instruct` (rev `0e9e39f2`, bfloat16, sdpa, 32 layers) unless
stated. Judge: StrongReject. Δ and p are on the **continuous** StrongReject score, cluster-mean estimand;
ASR@0.5 is the thresholded rate — see discrepancy **D-8**.

| # | claim (plan §0) | artifact | model / dataset | n | query kind | layer | readout | stored result | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1a | G1 `demos_only L18` ≈ **+68.9%** of span | `g1_wholeanswer_sow.json` → `G1.pairs.harm_ctx.arms["transplant\|demos_only\|L18"].frac_of_span` | Llama-3.1-8B / boombness bank (2352 rows, sha16 `71bea179`) | 24 families, 6 domains | `semantic_one_word` | L18 single-layer | `semantic_logodds`, whole-answer, `answer_prefix='Answer:'` | **0.6887** = +68.87%; CI (paired domain bootstrap) **[+51.3%, +97.4%]** | **established** |
| 1b | `query_only L18` moves the **wrong way** | same artifact, arm `transplant\|query_only\|L18` | " | 24 | `semantic_one_word` | L18 | " | **−0.5700** = −57.0%, CI [−102.8%, −40.1%] | **established** |
| 1c | whole-prompt transplant is null *(handover, not §0)* | same, arm `transplant\|all\|L18` | " | 24 | " | L18 | " | **+0.1329**, CI [−16.7%, +33.9%] — straddles 0 | **established** |
| 1d | self-swap no-op check near zero | same, `self_swap_max_abs_delta` / `span` | " | 24 | " | n/a | " | **0.0649 / 8.2171 = 0.79% of span** | **established** |
| 2a | G3: all demo-block edges, all layers ≈ **75.2%** of deletion ceiling | `g3_wholeanswer_block24.json` → `arms.all_layers_demo.delta_mean ÷ arms.no_demo_text.delta_mean` | Llama / boombness bank | 24 families | behavioural readout at `readout_pos` | all layers, `--dst both`, `--demo-scope block` | whole-answer | **−13.436759 / −17.878933 = 0.75154 → 75.2%**; mean edges cut **81,706.67** | **established** |
| 2b | sparse top-k knockout **did not work** | same artifact | " | 24 | " | layers [8,18], topk=8 → **16 edges** | " | top-k **+0.01961** (sem 0.01652) · bottom-k **−0.00283** · random **+0.00082** — all within noise | **established** |
| 2c | codeword-scope knockout moves the **wrong way** | `g3_wholeanswer_codeword24.json` | " | 24 | " | all layers, `--demo-scope codeword` | " | **+1.33** (wrong sign vs the −13.44 block arm) | **established** |
| 3a | G2 clean powered `d_surface\|L12\|proj`: ρ_within **−0.066**, p **0.493**, n **108** | `g2_analysis_POWER.json` → `clustered_inference.{rho_within_domain, p_perm_within_domain_rho, n}` | Llama / purpose-built power block (`core2x2` 60 + `core2x2_slot3` 48; demos disjoint from every existing family) | **108** independent prompts | `behavioral` | L12 | `d_surface\|L12\|proj` @ `codeword_last` | **ρ = −0.06601851932290928, p_perm = 0.49325337331334335, n = 108** | **established (as a null)** |
| 3b | clean slot-0 replication | `g2_analysis_cwpos_CLEAN.json` (`--slot0-only --require-bank-block`) | " | **90** | `behavioral` | L12 | " | ρ_pooled **+0.0860**, ρ_within **−0.0518**, p_perm **0.658** | **established (as a null)** |
| 3c | the **retracted** published value | `g2_analysis_cwpos.json` | " | **234** (contaminated) | `behavioral` | L12 | " | ρ_pooled **+0.3067**, ρ_within **+0.2618**, p_perm **5.00e-04**; `row_composition` confirms core2x2 60 + families 72 + role_style 30 + strength 24 + consistency 36 + position 12, by slot **162/36/36** | ⛔ **retracted (R-18)** |
| 4a | G4: steering does not license a GCG objective | `steering_analysis.json`, `steering_band_real.json` | Llama / 270 doublespeak rows | 270 | `behavioral` | L8 | StrongReject | both signs suppress; no objective built | **established (as a negative)** |
| 4b | genuine 4-draw control band | `steering_band_real.json` | " | 4 draws | " | L8 | " | draws **+0.0120 / −0.0551 / −0.0097 / +0.0046**, mean **−0.0120**, between-draw sd **0.03009**; +0.25 arm clearance falls to **p = 0.043** | **established** |
| 4c | the **fake** 4-draw band | `steering_analysis.json` → `control_band` | " | nominally 4, actually **1** | " | L8 | " | −0.0343 / −0.0338 / −0.0440 / −0.0343, mean −0.0366, sd **0.00494**; four byte-identical completions (sha256 `e4a15fcb` ×4) | ⛔ **retracted (#7)** |
| 5a | **removing `d_surface` raises external ASR** | `advbench_decomposition.json` | Llama / **AdvBench held-out 495**, 16 domain clusters — no codeword, no demos, no wrapper | 495 | `behavioral` | L8 | StrongReject, cluster-mean | baseline **0.0646** (32/495) → arm B **0.1071** (53/495); **Δ_cl +0.0305, p_cl 0.0089, CI [+0.0089, +0.0522]** | **established — the sprint's headline** |
| 5b | refusalness removal is stronger | same | " | 495 | " | **L18** (not L8 — 4h review F2) | " | arm C **0.2707** (134/495), Δ **+0.1895**, p_cl **1.4e-04** | **established** |
| 5c | removing both is largest, with interaction | same + `advbench_superadd_control.json` | " | 495 | " | **L8 + L18, composed** (F2) | " | arm D **0.3515** (174/495), Δ **+0.2544**, p_cl **4.4e-05**; super-additive excess **+0.0333** CI [+0.0128, +0.0638]; **paired vs the matched random triple +0.0268** CI [+0.0029, +0.0584] | **established** |
| 5d | matched random controls inert | same | " | 495 | " | L8 (Bctrl); Cctrl@L18; Dctrl@L8+L18 | " | B-control **0.0626** (31/495), Δ **−0.0062**, p **0.539** | **established** |
| 5e | effect is **L6–L12** localised | `advbench_layer_profile.json` | " | 495 | " | **11 depths L4–L28** (see D-1) | " | significant L8 (p 0.0089), L10 (p 0.0190), L12 (**+0.0322**, p 0.0056); marginal L6; L13 +0.0138 (p 0.090), L14 +0.0118 (p 0.141); **null from L16 out**; L16 changes 29.5% of generations and compliance on none | **established** |
| 5f | direction-specific, not just better-than-noise | `advbench_direction_specificity.json`, `direction_cosines.json` | " | 495 | " | L8 | " | `d_surface` cos 1.000 → Δ +0.0305 (p 0.0089); `d_naive` cos **0.945** → Δ **+0.0449** (p 0.0089); `d_context` cos **0.188** → Δ **+0.0045** (p 0.399) despite changing 34.9% of generations | **established** |
| 5g | ClearHarm is **withdrawn**, not supporting | `clearharm_decomposition_regoal.json` | Llama / ClearHarm 179, 6 clusters | 179 | " | L8 | " | baseline 19/179, B 34/179, C 65/179, D 92/179, Dctrl 19/179; arm B **Δ_cl +0.0843, p_cl 0.2102, CI [−0.0665, +0.2350]** | ⛔ **withdrawn on ClearHarm (R-16)**; reinstated on AdvBench |
| 6a | Qwen3 AdvBench is **floor-limited** | `advbench_decomposition_qwen3.json` | **Qwen3-14B** / AdvBench 495 | 495 | `behavioral` | L8-equiv | " | baseline **0.0081** (4/495), arm B **0.0141** (7/495), Δ **+0.0024**, p_cl **0.657** | **established as a floor, NOT as a causal failure** |
| 6b | Qwen3 ClearHarm shows reversed channels | `clearharm_decomposition_qwen3.json` | Qwen3-14B / ClearHarm 179 | 179 | " | " | " | baseline **0.1341** (24/179), B **0.2793** (50/179), D **0.2793** (50/179) — ⚠ **"B = D to 4 dp" holds only at the 0.5 threshold** (review F8). The **continuous** cluster-mean deltas differ by a third: B **+0.0416** vs D **+0.0557**. A threshold coincidence was being read as a mechanism. p_cl **0.181** | **exploratory** — the "reversed channels" reading is **downgraded**; it rests on a binary tie that the continuous estimand does not reproduce |
| 6c | Qwen3 G2 carries the R-18 filter defect | `qwen3_g2_analysis.json` | Qwen3-14B | 384 | `behavioral` | L12 | " | argv passes **neither** `--slot0-only` nor `--require-bank-block`; no `row_composition`; 72 sibling-slot rows; ρ_pooled 0.3638 / ρ_within 0.1438; p_cr1_pooled 0.206 vs p_perm_within 0.005 | ⛔ **retracted (R-18 class)** |
| C1 | comprehension: `project_out` **improves** it | `section4b_whole_answer.json` | Llama / bank | 288 comprehension, 1104 semantic | `comprehension_usage` + semantic | L8 (arm), L8+L18 (control) | whole-answer forced choice | comprehension **+0.2795 [+0.1752, +0.3838], p 0.00099**; semantic **+2.4073**; double-random control comprehension **−0.0041 (p 0.630)** | **established** — but see D-6, D-7, D-10 |

### Phase A Discrepancy Ledger

Seven items did not reproduce **as stated**. None contradicts a section-0 claim. Three are corrections in
the sprint's favour; three are citability limits; one is the working-tree regression already logged as IF-1.

| id | item | what the audit found | consequence |
|---|---|---|---|
| **D-1** | "nine-point layer profile" | The committed artifact carries **eleven** depths, not nine. Commit `8b5654a9` had nine; `e9000c5c` added the L13/L14 arms plus the c6/c10/c16/c28 controls; `af4fe7a4` added c13/c14. | **Superseded upward.** Claim 5e is stronger than stated. Use "eleven-point profile". |
| **D-2** | handover ch. 10.4: the four edge-depth controls "are not yet in any committed artifact" | **Stale, and stale in the sprint's favour.** All four (L6, L10, L16, L28) **are** in the committed JSON, verified against the git blob `af4fe7a4`, not the working tree. | The plan §0 phrase "controls were *mostly* inert" can be strengthened: every control at every controlled depth is committed and inert. |
| **D-3** | ClearHarm arm-B matched random control (21/179, Δ_cl +0.0039, p_cl 0.208) — cited in handover §13.14 as closing an open item | The number is correct **but exists only in an uncommitted working-tree rewrite** of `clearharm_decomposition_regoal.json` (mtime 08-19 05:35). At HEAD the `Bctrl` key **does not exist**. | ⚠ **Not citable.** ClearHarm arm B has **no committed matched control**. Re-run through a committed module before any use. |
| **D-4** | `clearharm_decomposition.json` control band | Confirms **IF-1** and sharpens it: the file has exactly **one** commit (`70709348`), and at that commit `control_band = {n_draws: 1, note: "...variance is unestimated"}`. The working-tree 3-draw band is **not a revert to any prior committed state** — it is a fresh uncommitted regression re-inflating the retracted figure on top of a HEAD that had already guarded it. | Do not commit. See Open Questions. |
| **D-5** | same file, sd 0.0048 | The retracted `between_draw_sd = 0.0048381307473991` exists **only** in the working tree; HEAD never carried it. Two of three draws share `paired_delta_mean = 0.018156424581005588` — effective n = 2. | As above. |
| **D-6** | "median option mass 0.297" (R-6 resolution) | **Mismatch.** `section4b_whole_answer.json` carries no option-mass field at all. The three arms actually used read **0.3064 / 0.3084 / 0.3155**. The only stored 0.297 (0.29686) comes from a **24-row smoke run** that is not one of the three arms. | Substance of R-6 survives intact — the readout is a healthy ~0.31, not a 1e-5 tail. **Quote 0.31, not 0.297.** |
| **D-7** | the *retracted* R-6 descriptors (p = 0.681; median option mass 4.4e-05; 0 of 288 rows above 1%) | **No artifact anywhere in the repo carries them.** They exist only in prose. `section4b_whole_answer.json` carries a `supersedes` key naming what it replaces, which is the artifact's own acknowledgement — but the retracted quantities themselves are unevidenced. | The retraction stands on its replacement, not on a recorded baseline. Note when citing R-6. |

### Cross-cutting findings the audit surfaced (not in the plan's claim list)

| id | finding | why it matters |
|---|---|---|
| **D-8** | **Estimand mixing in prose.** In `analyze_external_arms.py`, `asr_at_0.5` comes from the binary `malicious_at_0.5` flag (line 124) while `delta_pooled` / `delta_cluster_mean` / `ci95_domain_clustered` / `p_cl` all come from the continuous `strongreject_score` (line 143). Verified: AdvBench arm B `delta_pooled` 0.006818… = mean_score(B) 0.013889 − mean_score(base) 0.007071 **exactly**. So on Qwen3 the invited subtraction 0.0141 − 0.0081 = 0.0060 is the **binary** gap (3/495), while the reported Δ +0.0024 is the domain-equal-weighted **continuous** mean. | The artifacts are honest — every `paired_vs_baseline` block carries an `estimand_note`. **The prose is what drops the distinction.** This sprint must always state which estimand a Δ is on. |
| **D-9** | **ClearHarm's clustering has almost no power.** Its 6 "domains" are sized **127 / 31 / 17 / 2 / 1 / 1** — two clusters are single prompts. | A **null** under clustering on ClearHarm is weak evidence of absence. ⚠ **Corrected 2026-08-19 (review F13):** my original wording said "no arm reaches significance under clustering on ClearHarm". That is true of **Qwen3** but **false of Llama** — `clearharm_decomposition_regoal.json` gives arm C **Δ_cl +0.3941, p_cl 0.0410** and arm D **Δ_cl +0.4603, p_cl 0.0200**, both significant; only arm B is null (+0.0843, p_cl 0.2102). I had described two datasets as one. The 0.1341 / `asr_cluster_mean` 0.0522 gap quoted here is **Qwen3's**, and matters before leaning on the 13.4%-vs-0.8% floor contrast in claim 6a. |
| **D-10** | **The "inert" double-random control is inert only on comprehension.** In the same artifact, its **semantic** block reads Δ **+0.0666, CI [0.0462, 0.0869], p = 3.93e-04** — significantly non-zero. It is also the composed random-L8 + random-L18 control for arm D, **not** a matched single-layer control for the `project_out`-at-L8 arm it is being used to license. | Do not describe it as inert without qualification, especially since the semantic readout is where the `project_out` effect is claimed largest (+2.4073). Phase E3 should fit a properly matched single-layer control. |
| **D-11** | **Nothing upstream is committed.** `.gitignore` line 11 ignores `outputs/` wholesale; the analysis JSONs are tracked only because they were force-added. `git ls-files outputs/boombness/score_behavior` and `.../judge` both return **zero** files. Every judge run, score run and extract fit that every artifact points at is untracked and gitignored. | Combined with `argv: ["-"]` on `section4b_whole_answer.json`, the R-6 resolution rests on data existing in exactly one place on one filesystem with no committed code path to it. **This is the single largest reproducibility risk inherited by this sprint.** |
| **D-12** | **`provenance.git_dirty` is `true` on all three G2 artifacts** (and on 16 of the handover's 19 provenance-carrying files). | The recorded `git_commit` identifies the commit a run was launched *near*, not the code that ran. Treat provenance as advisory. |

---

## Retracted / Superseded Claims Not To Cite

Assembled from the handover's Appendix A and both retraction ledgers (23 labelled entries, 22 distinct
events — progress-log #9 ≡ ledger-2 R-10), restricted to entries whose evidencing artifact this audit
confirmed. **Nothing below may appear in a slide, abstract, or paper without the word "retracted".**

⚠ **Two colliding id schemes.** Ledger 1 (`RETRACTION #1…#9`, `docs/BOOMBNESS_SPRINT_PROGRESS.md`) and
ledger 2 (`R-6…R-19`, `docs/BOOMBNESS_CONTINUATION_LOG.md`). `#7` ≠ `R-7`.

### The plan's mandated minimum, each confirmed against an artifact

| ⛔ dead figure | where it lived | why dead | replacement (verified) |
|---|---|---|---|
| **G2 ρ = +0.3067 pooled / +0.2618 within-domain, p 5e-4, n 234**, "Boombness predicts attack success" | report §0 gate table, §3, §9; short update; six-criteria table; N2/N15 | ⛔ **R-18.** `analyze_g2.py:484` filtered on `condition` only — no `bank_block`, no `family_slot`. 31% sibling families (pseudo-replication) + 31% experimentally-manipulated rows | **Not established.** −0.0518 (n=90), −0.0832 (n=60), **−0.0660, p 0.493 (n=108)**. `g2_analysis_cwpos_CLEAN.json`, `g2_analysis_POWER.json` |
| **G1 "+84% of span, CI [+57%, +105%], n = 8 families, 2 domains"** | report §2, §8b, limitations | ⛔ **R-8, superseded.** n=8/2 domains pilot; `semantic_logodds` structurally biased at the single-token readout | **+68.87%**, CI [+51.3%, +97.4%], **24 families / 6 domains**. `g1_wholeanswer_sow.json` |
| **G3 ceiling recovery 84.35%** (`−9.707864 / −11.508745`), edge counts **56,832 / 3,552** | report §2/§10; `g3_dstfix.json`, `g3_edgematch.json` | ⛔ **R-7.** Edge *ranking* still computed at the final codeword occurrence while the readout sits ≈9 tokens later; the 6-family run also failed its own option-mass check (`all_layers_demo` mass 0.0165, `reportable = False`) | **75.15%** (`−13.436759 / −17.878933`), **81,707 / 5,107** edges, 24 families, ranking at `readout_pos`. `g3_wholeanswer_block24.json` |
| **The "distributed over depth" framing** and **"~93% of demo influence does not flow through attention"** (6.8% of ceiling) | progress log 08-17; report §10 as first written | ⛔ **RETRACTION #3.** Knockout blocked edges into the final codeword occurrence (tok ≈104) while the readout was the last token (≈113) — a 9-token gap on every prompt; the positive control additionally blocked the destination's own self-edge, driving the softmax row uniform | Whole §10 withdrawn and re-run with `--dst both`. `g3_dynrange.json` is the dead artifact. Current claim: **6.25% of demo edges does nothing however distributed** — discharged 2026-08-19, live |
| **Any sparse top-k attention-edge causal claim** | report §10 lineage | ⛔ Confirmed dead by this audit: at 16 edges, top-k **+0.0196** (sem 0.0165), bottom-k **−0.0028**, random **+0.0008** | The redundancy is in **edge count**, not in any identifiable subset. `g3_wholeanswer_block24.json` |
| **Any claim that Boombness is a usable GCG objective** | the sprint's original goal | ⛔ **G4 failed.** Both signs of steering suppress ASR; the one arm clearing a random band does so **through refusal**; α = 1's "3.47× ASR" was degenerate (uniq ratio 0.302, trigram repeat 0.551, truncated 1.000) | **No objective was built and none is licensed.** `steering_analysis.json`, `steering_band_real.json`, `coherence_steering.json` |
| **Any floor-limited Qwen3 AdvBench causal claim** — incl. "removing `d_surface` raises external ASR in BOTH models", Llama +0.083 / Qwen3 +0.131 pooled | continuation log; report §7c/§7f | ⛔ **R-17.** Written on **pooled** estimates; neither Qwen3 number survives clustering (ClearHarm p_cl 0.181, AdvBench p_cl 0.657). Cause is a **floor**: Qwen3 complies with 0.8% of AdvBench | Withdrawn. **"Is `d_surface` causal on Qwen3?" is OPEN, not negative.** `advbench_decomposition_qwen3.json` |

### Further dead figures confirmed by this audit

| ⛔ figure | why dead | replacement |
|---|---|---|
| **The 4-draw steering band** (mean −0.0366, sd 0.00494) and everything derived — "clears the band, t = −3.23, p = 0.0014" | ⛔ **RETRACTION #7.** Four byte-identical completions (sha256 `e4a15fcb` ×4); `make_intervention` seeded the control from the literal `20260816 + L`, so `--seed` never reached it. **n = 1 wearing an n = 4 label** | Genuine band mean **−0.0120**, sd **0.03009** (6.1× larger); clearance falls to **p = 0.043**. `steering_band_real.json` |
| **The ClearHarm 3-draw band, sd 0.0048** | ⛔ **R-12.** `score_behavior.py:123` recursed into composed arms without passing `control_seed` | Real band: 3 distinct sha256s, mean 0.1024, sd **0.0129**. `clearharm_decomposition_regoal.json`. ⚠ **The retracted sd 0.0048 is currently sitting in the working tree** — see IF-1 / D-4 / D-5 |
| **Every pre-R-14 ClearHarm ASR** (baseline 0.1006, B 0.2067, C 0.3408, D 0.5419) and "arm D takes ASR 0.101 → 0.542" | ⛔ **R-14.** `external_bank.py:62` never emitted `final_query_text`, so **StrongReject scored every external completion against an empty goal**, recorded as `judge_status: "ok"` | Re-judged: 19/179, 34/179, 65/179, 92/179. Every arm moved ≤0.03 and the ordering held — the cost was **measurement validity, not the conclusion**. `clearharm_decomposition_regoal.json` |
| **ClearHarm arm B "+0.1047 ± 0.0238", "the bank-artifact explanation is excluded"** | ⛔ **R-16.** Empty-goal judging **and** an **iid** SEM treating 179 prompts as independent when 127 share a domain | Withdrawn on ClearHarm (Δ_cl +0.0843, p_cl 0.2102). **Reinstated on AdvBench** (+0.0305, p_cl 0.0089) |
| **"Boombness beats refusalness 3.7×"** (and its predecessor "40×") | ⛔ **RETRACTION #5.** The two probes were read at **different tokens** | At matched position the ratio is **0.7472** @`codeword_last` — but **1.5416** @`last`, where Boombness exceeds refusalness, so "inverts" is one-directional (4h review F3b). `position_2x2.json`, computed on the **234-row R-18 population** |
| **The incremental-R² pair "refusalness +0.144 vs Boombness +0.028"** | ⛔ **R-13.** Both increments against the same model, giving refusalness **5 df against Boombness's 1**. The pair exists in **no committed artifact in any commit** | At matched df on clean rows the ordering **reverses**: Boombness +0.0441, refusalness +0.0378. `g9_three_predictor_cwpos_CLEAN.json` |
| **"`project_out` is the only arm that leaves comprehension unchanged, p = 0.681"** | ⛔ **R-6.** Forced choice scored leading-space tokens at a position emitting the no-leading-space form | **Resolved in the sprint's favour**: comprehension **improves** +0.2795, p 0.00099. ⚠ See **D-6** (quote median mass ~0.31, not 0.297) and **D-7** (the retracted descriptors have no artifact) |
| **Role framing "does not move Boombness", F(5,810)=0.175, p=0.972** | ⛔ **RETRACTION #6.** Wrong error term; `plain` and role styles sit in **disjoint `bank_block`s** with zero family-id overlap | ⚠ **the replacement figure F(5,355)=20.30, p=8.1e-18 is NOT in `g11_role_full.json`** (4h review F3a) — that artifact holds a within-stem permutation omnibus **p = 4.9975e-04** at the 2000-perm floor over 36 crossed stems. The F figure exists only in prose. Role framing does move Boombness, but cite the permutation p — though absolutely small. `g11_role_full.json` |
| **"the §10.4 effect is harmful-yes / benign-no"** | ⛔ **R-15.** One significant cell of six under domain clustering; the split tracks **sample size**, not harm | Not established. The deltas themselves reproduce and are **not** retracted — only the reading. `condition_profile_llama_projout.json` |
| **The LOCALIZATION claim "both probes are 2–4× more predictive at the codeword token"** | ⛔ **R-19, half wrong.** Same `condition`-only filter | On the clean 90, `d_surface`'s position effect **disappears** (1.18×). Defensible statement is qualitative only |
| **"§18 = B — mechanistic but not causal"** | ⛔ **R-9.** B requires interventions that do not affect ASR **or** destroy comprehension — **both clauses fail** | **"C, amended"** |
| **"the designed-variance rows have never contaminated a published number"** (N12) | ⛔ **Falsified by R-18** — they were 31% of G2's n | Corrected in place |

### ⚠ Retracted figures still standing unqualified at HEAD (inherited, not yet fixed)

`retraction_sweep.py` reports clean because it exempts at **blank-line paragraph scope**, and a markdown
table is one paragraph — a single marker word in any row exempts every row.

| site | text still present | dead by |
|---|---|---|
| `reports/boombness_objective_sprint_report.md` §13, criterion 1 | "YES IN LLAMA ONLY — ρ=+0.307, p<5e-4 clustered, 6/6 domains positive" | R-18 |
| same, criteria 3 and 4 | "comprehension unchanged (p=0.681)" / "project_out: preserved (p=0.681)" | R-6 |
| same, §8b negative results N2 / N5 / N8 | "ρ≈+0.307 at L12"; G1 query transplant at "−71%"; ClearHarm super-additivity "+0.0922" | R-18; superseded readout (now −57.0%); R-14 |
| `reports/boombness_objective_sprint_short_update.md` (rev 9) header | "§18 settles at B" | R-9 |

**This sprint will not repair these unilaterally** — they are the previous sprint's deliverables. Logged
so nothing here inherits them. A row-scoped or claim-scoped sweep is the durable fix.

## Phase B — Occurrence-Resolved Token-Level Boombness

**Status:** runs complete, self-review in flight. Numbers below are **provisional until the independent
replication returns** (a second agent re-deriving them without touching my code).

### What was built, and how little of it is new

`analyze_boombness.py` already implemented the plan's §7.1 token-level analysis — but it splits
occurrences only into `{final, earlier}`. The follow-up needs **first-demo / middle-demo / last-demo /
query**, because G1 (meaning lives in the demo block, not the query token) predicts those four behave
differently and a two-way split cannot see it. So: **one new file, 330 lines**,
`src/boombness/followup_token_level.py`, which imports `mean`, `sem`, `cohens_d`, `col`,
`discover_columns`, `direction_sanity` and the cell constants from `analyze_boombness` rather than
reimplementing them. No new extraction, no GPU.

**Phase B needed zero GPU time** — the occurrence rows already existed.

### Inputs, and why this extract

| | choice | why |
|---|---|---|
| extract | `extract_boombness/full2352_20260818_115332_1410155` (14,016 rows / 2,352 prompts) | It contains **all 960** refusalness prompts. The 1,464-row canonical fit dir contains only **660** of them. The plan (§4 gap 4) required choosing explicitly; this is the choice and the reason. |
| refusalness | `refusalness/cwpos_20260817_050713_304734` | `codeword_last`, 960 prompts, layers {12,14,16,18,20} |
| directions | cross-fit throughout — `is_self_fit` is `False` on **all 14,016** rows | plan §2.3 |

### Commands

```
PY=.../envs/poc_stage2/bin/python
EX=outputs/boombness/extract_boombness/full2352_20260818_115332_1410155
RF=outputs/boombness/refusalness/cwpos_20260817_050713_304734

# per query kind, slot-0 clean (R-18 hygiene)
$PY src/boombness/followup_token_level.py --run $EX --refusalness $RF \
    --out-dir outputs/boombness_followup/phaseB_<QK>_slot0 \
    --query-kind <QK> --slot 0 --no-jsonl --strict
# QK in {behavioral, semantic_one_word, comprehension_usage, semantic_forced_choice}

# behavioral, all slots — the slot1/2 pseudo-replication comparison
$PY ... --out-dir outputs/boombness_followup/phaseB_behavioral_allslots --query-kind behavioral --no-jsonl --strict

# the full row-level deliverable
$PY ... --out-dir outputs/boombness_followup --strict
```

SLURM: **none** — pure CPU. Git commit: see below.

### Outputs

| artifact | size | committed? |
|---|---|---|
| `outputs/boombness_followup/token_level_occurrence_readouts.jsonl.gz` | 16.2 MB, **448,512 rows** | no — `outputs/` is gitignored (D-11); path recorded here per plan §2.5 |
| `outputs/boombness_followup/token_level_dynamics_summary.json` | 190 KB | **yes**, force-added |
| `phaseB_{behavioral,semantic_one_word,comprehension_usage,semantic_forced_choice}_slot0/` + `phaseB_behavioral_allslots/` | summaries | **yes** |

**Deliberate deviation from the plan, recorded so nobody thinks a metric was dropped.** The plan asks for
one row per (prompt, occurrence, layer, **metric**). The artifact emits one row per (prompt, occurrence,
layer) with the metrics as a dict on the row — identical information, ~6× fewer bytes. 448,512 rows
rather than ~2.7 M.

### Row accounting (plan §2.3 — no silent failures)

Full dump: **attempted 14,016 → kept 14,016 → 0 skips.** Every filtered run reconciles exactly:

| run | attempted | kept | skips |
|---|---|---|---|
| behavioral slot0 | 14,016 | 4,680 | `filtered_query_kind` 8,520 + `filtered_family_slot` 816 |
| semantic_one_word slot0 | 14,016 | 4,680 | `filtered_query_kind` 9,336 |
| comprehension_usage slot0 | 14,016 | 1,776 | `filtered_query_kind` 12,240 |
| semantic_forced_choice slot0 | 14,016 | 2,064 | `filtered_query_kind` 11,952 |

### Audits required by plan §4, and their results

| audit | result |
|---|---|
| **query vs demo occurrence not confused** | **Enforced, not assumed.** `assign_roles` aborts unless every prompt has exactly one `is_query_occurrence` at the highest `occurrence_index`. Verified across both extracts: `query-not-last: 0`, `multi-query: 0`, `no-query: 0`, on 1,464 and 2,352 prompts. |
| **`codeword_last` vs `readout_pos` not confused** | Refusalness is joined **prompt-level** and carries an explicit `refusalness_readout_position` field; the summary states it is *not* occurrence-resolved. This is the ~9-token gap that caused three retractions last sprint. |
| **`query_kind` not stripped from `family_id`** | Checked per row: `family_id` field 9 must equal the `query_kind` column, else the row is skipped with a named reason. **0 rows failed.** |
| **`family_slot` recovered** | Parsed from `family_id` field 3; a row whose slot is unparseable is skipped by name. **0 failures** across 14,016 rows. |
| **expected occurrence counts** | `len(rows_for_prompt) == n_occurrences` asserted per prompt. **0 failures.** |
| **exact `prompt_id` joins** | refusalness matched **816/816** behavioral slot-0 prompts, 0 unmatched. |
| **no semantic representation joined to behavioural ASR** | **No ASR is joined in Phase B at all.** Representation only. |
| **direction sanity gate** | `d_surface|cos` separates concept-surface cells {B,E} from codeword-surface {A,C} at **32 of 32 layers**, all runs, `--strict`. |

**Discovered, not assumed:** only `behavioral` prompts have `slot1`/`slot2` (408 rows each). Every other
query kind is slot-0 only. So R-18's sibling-family pseudo-replication was **structurally confined to the
behavioural rows** — which is exactly where ASR lives.

Also discovered: there is a **fifth** query kind, `semantic_forced_choice` (2,064 rows), which the plan's
list did not mention. It was run rather than dropped.

### ⛔ RETRACTION F-1 — my own Phase B headline, retracted the same day I published it

Commit `ff6c21f1` claimed *"later demo occurrences are MORE concept-like than the first"* as a
doublespeak finding, and read the query-token deficit as corroborating G1. **A self-review caught that
this had no matched control.** Both claims are now corrected below. The arithmetic reproduces exactly —
an independent agent re-derived all 15 numbers without touching my code — but **the reading was wrong**.

| ⛔ as published in `ff6c21f1` | why dead | what replaces it |
|---|---|---|
| "later demo occurrences are more concept-like than the first" as a **doublespeak** result: +1.0971 (d 2.66) @L8, +1.4342 (d 2.64) @L12 | No control condition. `benign_literal` — where **no mapping is taught and there is nothing to become** — shows the same positive gradient (+0.49 @L8, +0.76 @L12). The gradient is condition-general. | The doublespeak-specific quantity is the **excess over control**: +0.612 @L8, +0.682 @L12. Roughly **half** the raw gradient was the control effect. |
| "the query codeword never becomes bomb-like in behavioural prompts — this corroborates G1 on the rows that matter" | Also uncontrolled. Against `benign_literal` the query deficit in the causal band is **≈0** (−0.032 @L8, −0.056 @L12). | Not supported in L6–L12. The deficit is condition-general there and only becomes doublespeak-specific at L18+ (−1.13). |
| the contrast n's (324 vs 294) | Unpaired: a prompt with exactly one demo contributes a `demo_first` and no `demo_last`, and that lone demo is the one nearest the query — the position driving the effect. | **Paired within prompt**, n = 294 matched pairs. Effect barely moves (+1.4451 vs +1.4342 @L12) but the composition confound is gone. |
| `query_minus_demo_all` = −1.0431 @L12 | Row-weighted `demo_all` (1–17 rows/prompt) subtracted from a prompt-weighted `query` (1 row/prompt) — two different units. | **Prompt-weighted**: −0.7973 @L12. The published figure was **31% too large**. |

Six further defects were fixed in the same pass: per-metric layer lists (logit-lens covers 9 of 32
depths, so a band averaging 8 layers of `d_surface` was averaging 2 of `ll|boombness` and printing them
side by side); domain- and prompt-clustered SEMs alongside the row-level one (row-level understates
~2.3×); NaN-safe `n`; a **false provenance string** — the full-dump summary asserted query kinds were
"never pooled" while pooling all four kinds *and* slots 0/1/2, the exact R-18 defect class.

### Findings (corrected, control-matched)

Behavioural, slot-0, `d_surface|proj`, **paired within prompt**. Higher = more concept-like (sign fixed
by the sanity gate passing 32/32 layers).

#### The control test, which is the whole story

`demo_last − demo_first`, paired, by condition:

| condition | cell / what it is | L8 | L12 | L18 | n pairs | sem (domain) @L12 |
|---|---|---|---|---|---|---|
| `benign_literal` | A — codeword surface, **no mapping taught** | +0.491 | +0.763 | +1.312 | 228 | 0.129 |
| `natural_doublespeak` | C — codeword surface, **harmful mapping taught** | **+1.103** | **+1.445** | **+3.058** | 294 | 0.105 |
| `direct_codeword` | D — codeword surface, mapping **stated** | +0.944 | +1.298 | +3.008 | 24 | 0.151 |
| `benign_remap` | F — codeword surface, **benign mapping taught** | +1.361 | +1.792 | +3.986 | 24 | 0.162 |
| `direct_harmful` | B — **concept** surface | −0.745 | −0.794 | −1.238 | 48 | 0.064 |
| `concept_in_benign_ctx` | E — **concept** surface, benign context | −0.705 | −0.891 | −3.460 | 48 | 0.156 |

**Every codeword-surface cell (A, C, D, F) is positive. Both concept-surface cells (B, E) are negative.**
The underlying regularity is that a token's projection on the surface axis *regresses toward zero* with
repetition, and is re-asserted at the query. That is a property of repeated tokens, not of doublespeak.

#### What survives, and what does not — **corrected 2026-08-19 19:15** (family-matched, domain-paired)

The tick-6 review found the excess was neither family-matched nor correctly errored (A3 + A4). Both are
now fixed in `followup_token_level.py`: the excess restricts to the **228 families present in BOTH
conditions** (66 doublespeak families, 22%, have no `benign_literal` twin and are dropped), and the SEM
is over **per-domain excesses** rather than quadrature over two conditions' SEMs. Numbers below
supersede the ones in commit `fef79630`.

| contrast, `d_surface\|proj` | L8 | L12 | L18 |
|---|---|---|---|
| excess **as first published** (unmatched families, quadrature SEM) | +0.612 | +0.682 | +1.745 |
| **excess, family-matched** | **+0.5414** | **+0.6402** | **+1.8719** |
| domain-paired SEM | 0.1660 | 0.2147 | 0.4564 |
| **t** (5 df) | **3.26** | **2.98** | **4.10** |

So the doublespeak-specific gradient **survives** family matching — but at t ≈ 3 on 5 df (p ≈ 0.02–0.03),
not the "about 4 sigma" I claimed. **That claim is corrected.**

And the direction comparison, which is what RETRACTION F-2 was about, is unchanged by the fix — if
anything sharper:

| direction | L8 excess (t) | L12 excess (t) |
|---|---|---|
| `d_surface` | +0.5414 (**3.26**) | +0.6402 (**2.98**) |
| `d_naive` | +0.6200 (4.24) | +0.7153 (3.32) |
| `d_context` | +0.4430 (**4.10**) | +0.3764 (2.17) |

At L8 `d_context`'s t (4.10) **exceeds** `d_surface`'s (3.26). There is no sense in which the token-level
gradient is specific to the surface axis.

#### Q2 — the query token, corrected

`query − demo_all`, **prompt-weighted**:

| | L8 | L12 | L18 |
|---|---|---|---|
| doublespeak, raw | −0.495 | −0.797 | −1.980 |
| excess over `benign_literal` | **−0.032** | **−0.056** | −1.132 |
| excess over `benign_remap` | +0.238 | +0.280 | +0.006 |

In **L6–L12 — the band where ablating `d_surface` actually changes behaviour** — the query-token deficit
is condition-general: essentially zero excess over control. It becomes doublespeak-specific only at
L18+, outside the causal band. **My earlier reading of this as representational corroboration of G1 is
withdrawn.**

#### Q3 — layer band — **corrected: most of the depth trend was residual norm**

The 4h review (F6) flagged that the "largest late" reading used unnormalised projections. On the
**scale-free** `cos` readout, family-matched:

| L | 4 | 6 | **8** | 10 | **12** | 16 | 18 | 24 | 31 |
|---|---|---|---|---|---|---|---|---|---|
| `proj` excess | 0.139 | 0.399 | 0.541 | 0.492 | 0.640 | 1.540 | 1.872 | 4.270 | **9.202** |
| `cos` excess | 0.024 | 0.054 | 0.074 | 0.062 | 0.068 | 0.125 | 0.121 | **0.146** | 0.152 |
| `cos` t | 2.01 | 2.91 | 3.87 | 3.11 | 2.99 | 4.23 | 4.13 | **4.89** | 3.62 |

**`proj` grows 17.0× from L8 to L31; `cos` grows 2.0×.** The dramatic late rise was overwhelmingly
**residual-norm growth**, not signal.

A real but much weaker depth trend does survive on the scale-free metric: `cos` excess roughly doubles
from the L6–L12 band (0.054–0.074) to a peak at L24 (0.146, t = 4.89). So the tension with the causal
band still exists — the representational peak is at L24 while ablation only changes behaviour at
L6–L12 — but it is a **2× discrepancy, not a 14× one**. The sprint's "sharpest open question" framing
was inflated by the readout and is hereby scaled down.

#### Q4 — direction specificity — ⛔ **RETRACTED (F-2), see the 4h review**

I reported that `d_context` "shows nothing" at the token level (d = −0.03 at L12) while `d_surface`
shows +1.4342, and called this the strongest Phase B result. **That comparison was uncontrolled in
exactly the way F-1 was.** Each direction has its own control baseline; once subtracted, `d_context`
carries **45–67%** of `d_surface`'s gradient rather than none. **The token-level gradient is not
direction-specific.** Corrected table in the 4h review.

#### Q5 — refusalness (unchanged)

`refusalness|cos` at `codeword_last`, prompt-level, 816 prompts. At L12 doublespeak (−0.0746) sits
between `benign_literal` (−0.1031) and `direct_harmful` (−0.0097), but the most refusal-positive
condition is `concept_in_benign_ctx` (+0.0251), which is **not** the most concept-like on `d_surface`.
The two orderings come apart — consistent with hypothesis 5.

⚠ Refusalness exists **only for `behavioral` prompts** (960 of 2,352); the `semantic_one_word` join
matches 0. Any combined Boombness/refusalness metric is restricted to behavioural rows.

### Known limitations of Phase B, stated before anyone cites it

1. **Descriptive, not inferential.** No domain clustering, no permutation test, no multiplicity
   correction. Cohen's d and means only. These are **exploratory** numbers; Phase D supplies the
   inference. Given the sprint's history of iid-where-positive / clustered-where-negative (R-16), that
   distinction is stated up front rather than in a footnote.
2. **Logit lens is not available at every layer.** `ll|boombness` returns nan at L18 because the extract
   computed logit-lens columns only at selected layers. Reported, not silently meaned over.
3. **`demo_middle` pools heterogeneous positions** — a prompt with 17 occurrences contributes 15 middles.
   Position-within-block is not yet a covariate.
4. **The 2,352-row bank is not the 1,464-row probe cache.** Phase C must not join across them (this is
   the R-10/C-13 defect class).

## Probe Validation and Leakage Checks

**Status:** Phase C launched, running. First results due at the next loop tick.

### Reuse assessment — `probes.py` already covers most of plan §5

963 LOC, and it already implements six train/test regimes with the controls the plan demands:

| plan §5 variant | `probes.py` regime | pool |
|---|---|---|
| simple lexical probe | `d1_simple` | whole bank |
| aligned 2×2 probe | `d2_aligned` | `core2x2` |
| hard-negative probe | `d3_hard_negative` | train on A vs B (the confounded diagonal), **test on the off-diagonal E and C** |
| heldout-domain probe | `d4_heldout_ds` | train without cell C, evaluate on all |
| surface-matched codeword probe | `d5_surface_matched_codeword` | A vs C, both surface "carrot" |
| concept-surface probe | `d6_surface_matched_concept` | B vs E |
| hazardous-object generalization | — | **not implemented**; plan marks it optional |

Already built in: group-k-fold over **domains**, shuffled-label controls, `--null-draws` random-direction
nulls, an explicit `check_leakage` gate (`--leak-tol` 0.05 AUROC, `--leak-z` 2.0), nested inner folds,
and PCA-64 before the logistic fit — the last because an unregularised fit on ~576 examples in 4096
dims returned **AUROC = 1.0000 at every layer including layer 0**, i.e. a saturated probe carrying no
graded information. That trap is already guarded; it is the plan's "stupid probe" problem.

**So Phase C needs no new probe code.** What it needs is the right *population* and an honest coverage
statement.

### The population decision, and the defect it avoids

Run on the **2,352-row** extract cache (`full2352_20260818_115332_1410155/cache`, 592 MB), not the
1,464-row one. Handover defect **R-10 / C-13** was exactly a probe cache built over 1,464 rows while
the bank had grown to 2,352, so whole `bank_block`s had no cached representation and the artifact's
own n's contradicted the prose.

**Coverage limit found by reading the source, not the docs:** regimes `d2`–`d6` are hardcoded to
`bank_block == "core2x2"` (`probes.py:275, 288, 293, 297, 300`). The handover's C-13 records this for
`d5` only; it is in fact **five of the six regimes**. Only `d1_simple` sees the whole bank. That is a
defensible design choice — the 2×2 identification design lives in `core2x2` — but it means probe AUROC
is **not** a whole-bank quantity, and the plan's "evaluate probe coverage over the full current bank"
must be answered as such. Recorded before results arrive so it cannot be quietly dropped afterwards.

### Command (completed)

```
$PY src/boombness/probes.py \
  --run outputs/boombness/extract_boombness/full2352_20260818_115332_1410155 \
  --regimes d1_simple,d2_aligned,d3_hard_negative,d4_heldout_ds,\
            d5_surface_matched_codeword,d6_surface_matched_concept \
  --folds 3 --null-draws 20 --emit-scores --tag fu2352
```

Run dir `outputs/boombness/probes/fu2352_20260819_161048_1978941` (`DONE`). Model Llama-3.1-8B-Instruct.
17 layers evaluated (every 2nd). 3-fold **grouped by domain**. 20 shuffled-label null draws per layer.

*(A tick-4 note that the run was "5 rows in 100 minutes and possibly pathological" was wrong: the
artifact emits **one row per regime**, so 6 rows is the complete output. Retracted here.)*

### ⛔ DECISION GATE C — FAILED. No probe in the suite is usable as a Boombness metric.

Plan §5: *"Build a probe only if it avoids the 'stupid probe' problem. The probe must not merely learn
lexical identity or prompt artifacts."* It does not avoid it.

| regime | pool (train/eval) | nested AUROC | layers picked in inner folds | stable? | shuffled-label |
|---|---|---|---|---|---|
| `d1_simple` | 2208 / 2208 | **1.0000** | [0, 0, 0] | yes | 0.493 |
| `d2_aligned` | 1152 / 1152 | **1.0000** | [0, 0, 0] | yes | 0.495 |
| `d3_hard_negative` | 576 / 576 | **1.0000** | [0, 0, 0] | yes | 0.498 |
| `d4_heldout_ds` | 864 / 1152 | **1.0000** | [0, 0, 0] | yes | 0.501 |
| `d5_surface_matched_codeword` | 576 / 576 | 0.9855 | [2, 6, 2] | **no** | 0.498 |
| `d6_surface_matched_concept` | 576 / 576 | 0.9806 | [2, 4, 8] | **no** | 0.496 |

**The machinery is sound** — every shuffled-label control sits at 0.49–0.50, and `check_leakage` flags
**zero** layers in all six regimes (`leak: false`, 17 layers checked, no undecidable layers). The probes
genuinely separate their classes. They separate them on the wrong thing.

#### Per-layer AUROC — the profiles are flat, and already at ceiling by the first block

| layer | d1 | d2 | d3 | d4 | **d5** | **d6** |
|---|---|---|---|---|---|---|
| 0 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9587 | 0.9711 |
| 8 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9849 | 0.9837 |
| 16 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9772 | 0.9849 |
| 24 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9813 | 0.9815 |
| 31 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9831 | 0.9798 |

*(full 17-layer table in the artifact; the profile never leaves the 0.975–0.986 band for d5/d6, and is
exactly 1.0 at all 17 layers for d1–d4.)*

**d1–d4 read token identity.** Their label is concept-surface {B,E} vs codeword-surface {A,C} — literally
*different words* ("bomb" vs "carrot"). AUROC is 1.0000 at every layer including the first, and nested
selection picks layer 0 in all three folds of all four regimes. This is precisely the failure the module
docstring records at `probes.py:245-248` and tried to fix with per-regime labels; the fix does not reach
d1–d4. **These four regimes carry no information about Boombness whatsoever.**

**d5 and d6 are surface-matched and still not usable.** They compare A vs C (both surface "carrot") and
B vs E (both "bomb"), so token identity cannot solve them — and they still reach ~0.96–0.97 at the
lowest layer measured and stay flat to L31.

I tested the obvious artifact and it is **not** the explanation: prompt length and readout position
separate the d5/d6 labels at **AUROC 0.527 / 0.528** — chance. *(A hypothesis I had written down and
then checked; recorded because the check is the point.)*

The actual explanation is the layer convention. The extract records
`layer_convention = "block_L == hidden_states[L+1]; hidden_states[0] == embeddings"`, so probe **"layer
0" is the output of transformer block 0, not the embedding**. One attention layer over the whole prompt
is already enough to make "was this token surrounded by harmful text" linearly decodable. What d5/d6
measure is **context detection, available immediately and constant thereafter** — not a concept
representation that builds across depth.

A flat 0.98 profile cannot distinguish "Boombness develops with depth" from "the context was decodable
from the first block". As a graded metric it is uninformative in exactly the way the plan anticipated.

#### Coverage

`d2`–`d6` are hardcoded to `bank_block == "core2x2"` (`probes.py:275, 288, 293, 297, 300`) — **five of
six regimes**, not just `d5` as handover C-13 records. Eval pools are 576–1152 rows of the 2,352-row
bank (25–49%); only `d1_simple` reaches 2,208. **Probe AUROC is not a whole-bank quantity**, and per
plan §5 coverage is not high enough to promote it regardless.

#### Verdict

> **The probe is not usable as a headline Boombness metric, and Phase I's candidate objective
> "maximize probe margin" is dead on arrival.** Four regimes measure lexical identity; two measure
> context that is fully present after one block. No regime shows the mid-stack structure a Boombness
> metric would need.

This is a **negative result, and a clean one** — the controls all pass, so the failure is diagnostic
rather than a broken pipeline. It also *narrows* the sprint: `d_surface` projection, not a learned
probe, remains the only instrument with a mid-stack causal band.

Artifact: `outputs/boombness/probes/fu2352_20260819_161048_1978941/{results.jsonl,summary.json}`.
**Citable as a negative.**

## Clean Fig-9-Style Boombness vs ASR Test

_Not started. Phase D deliverable._

## What Does d_surface Represent?

**Phase E1 — external semantic categories. Done with zero new compute:** AdvBench's 16 domain clusters
*are* the plan's semantic categories, and every arm needed was already judged. Model
Llama-3.1-8B-Instruct, AdvBench held-out 495, continuous StrongReject means per category.

### The matched contrast, per category

`B − Bctrl` — both arms remove *a* direction at L8, so this is the specificity contrast, not
arm-vs-baseline:

| category | n | baseline | **B − Bctrl** |
|---|---|---|---|
| misinformation_disinformation | 37 | 0.162 | **+0.1081** |
| other_uncategorized | 38 | 0.118 | **+0.0757** |
| cyber_hacking_malware | **127** | 0.125 | **+0.0699** |
| theft_property_crime | 18 | 0.000 | +0.0556 |
| fraud_financial_crime | 68 | 0.044 | +0.0294 |
| weapons_explosives_mass_casualty | 40 | 0.025 | **+0.0250** |
| identity_theft_personal_data_theft | 40 | 0.000 | +0.0250 |
| privacy_surveillance | 7 | 0.143 | +0.1429 |
| terrorism_extremism | 9 | 0.000 | +0.1111 |
| harassment_bullying_stalking | 18 | 0.000 | **−0.0556** |
| violent_crime · hate_speech · drugs · academic · **self_harm_suicide** · **child_exploitation** | 23/18/16/8/23/7 | 0.000 | 0.0000 |

**Mean over the 16 categories = +0.0367, sem 0.0132, t = 2.78 on 15 df (p ≈ 0.014).**
**Sign test: 9 of the 10 non-zero categories are positive, p = 0.0107.**

*(This +0.0367 independently reproduces the value the 4h auditor obtained by domain-clustered bootstrap
for F11 — +0.0367, CI [+0.0118, +0.0625] — by a different route.)*

### Three things this says about what `d_surface` is

**1. The effect is broad, not harm-type-specific.** 9 of 10 movable categories go the same way. This is
the opposite of retracted **R-15** ("harmful-yes / benign-no"), which failed because it was one
significant cell of six tracking sample size. Here the *sign* is consistent across categories that
differ enormously in content, and the contrast is against a matched random direction.

**2. It is weakest where the bank was fitted.** `d_surface` was fitted **entirely** on carrot→**bomb**
prompts, yet `weapons_explosives_mass_casualty` (n = 40) shows **+0.0250** — below the mean and far
below `misinformation` (+0.1081) or `cyber` (+0.0699). The largest effects are in **information-shaped**
harms: misinformation, cyber, uncategorized, theft. **This argues against plan hypothesis 3** (a general
hazardous-object semantic axis) and against a narrow bomb-concept reading: whatever `d_surface` carries,
it is not "explosives-ness", and it transfers *better* to categories unlike its training bank than to
the category that generated it.

**3. Two categories are immovable by either channel — a refusal floor neither direction touches.**
`self_harm_suicide` (n = 23) and `child_exploitation` (n = 7) sit at **exactly 0.000 in every arm**:
baseline, remove `d_surface`, remove refusalness, **and remove both**. Removing the refusal direction
raises compliance by +0.19 on average and by +0.41 on misinformation — and does **nothing** here.

That is a genuine safety observation and it is new in this sprint: **the refusal direction is not the
only thing preventing compliance.** Something categorical, not carried by either `d_surface` or the
refusalness direction at these depths, holds those two categories at the floor. It also bounds the
sprint's own attack story — the channel we can manipulate does not reach the harms one would most want
protected.

### Status and limits

**Exploratory, not citable as established.** Per-category means at n = 7–127 with no per-category
inference; the *aggregate* (t = 2.78 over categories, sign test p = 0.011) is the defensible statistic
and it is a **category-level** estimand, not the prompt-level cluster-mean used elsewhere. Six
categories are exactly zero, so the sign test uses 10. The two floor categories are the smallest movable
claim here and rest on n = 23 and n = 7 respectively — the n = 7 one should not be quoted alone.

**Still to do in Phase E1:** benign technical, benign everyday and ambiguous dual-use prompt sets, which
AdvBench does not contain. Those need a new external bank and are not yet built.

## d_surface × Refusalness Interaction

**Status:** blocked on data, and the blocker is now precisely characterised.

### ⛔ BLOCKER F-B1 — the refusalness layer profile is capped at L20, and it is a data gap, not a bug

Three of the four inherited `arm C` jobs (L8, L24, L28) died with
`no refusal directions matched .../refusal_direction_llama_L*.pt`. Diagnosed at tick 2:

**Llama-3.1-8B refusal directions exist at exactly five layers — L12, L14, L16, L18, L20** — all in
`doublespeak_causality/outputs/stage_gcg_full/`, all 4096-d, all verified by loading them.

So a refusalness layer profile cannot presently go below L12 or above L20. **This matters for Phase F**:
the causal `d_surface` band is L6–L12, and the *lower* half of that band has no refusal direction at all,
so the interaction cannot yet be measured where the `d_surface` effect is strongest.

### ⚠ LANDMINE F-B2 — five mislabeled direction files that would cross-contaminate models

`doublespeak_causality/outputs/refusal_qwen3/` contains five files named
`refusal_direction_llama_L{16,20,24,28,32}.pt`. **Every one of them is 5120-dimensional — they are
Qwen3-14B directions wearing Llama filenames.** (Llama-3.1-8B is 4096-d; Qwen3-14B is 5120-d.)
Confirmed by loading all fifteen direction files in the repo and printing their dimensions:

| directory | files | true model |
|---|---|---|
| `doublespeak_causality/outputs/stage_gcg_full/` | `llama_L{12,14,16,18,20}` | **Llama, 4096-d — correct** |
| `outputs/stage_gcg_full/` | `qwen3_L{20,25,28}` (5120-d), `gemma4_L{25,31}` (2560-d) | correct |
| `doublespeak_causality/outputs/refusal_qwen3/` | `llama_L{16,20,24,28,32}` | ⛔ **Qwen3, 5120-d — MISLABELED** |

Note L16 and L20 appear in **both** the first and third directory with *different dimensions*. Any
resolution order that reached `refusal_qwen3/` first would load a Qwen3 vector for a layer that has a
perfectly good Llama one. The `expect_dim` guard (added 2026-08-18) is the only thing preventing that;
it fired correctly during this diagnosis. **Recommend renaming those five files** to
`refusal_direction_qwen3_L*.pt`. Not done unilaterally — renaming files other runs may reference is the
user's call.

### Bugfix — `refusal_glob_for` never fell through, and a profile could silently short itself

`src/boombness/refusalness.py`: `refusal_glob_for` returned the glob for the **first root holding any
file for the model family** and never looked further, so a request for a layer that root lacks died even
when the file existed elsewhere. Two changes:

1. `load_refusal_dirs` now searches **all** roots and unions **per layer**, first root winning for a
   layer it actually has. Root order is preserved, so every previously-resolvable layer resolves to the
   same file and **no existing number changes** — verified: request `[12,14,16,18,20]` still returns all
   five at 4096-d.
2. A requested layer that cannot be found is now a **hard failure naming the missing layers**, rather
   than a profile quietly running on a subset. Verified: request `[24,28]` is refused, request `[8]` is
   refused.

Ironically the fix does **not** unblock L24/L28 — it makes the files reachable, and the dimension guard
then correctly refuses them because they are Qwen3. The honest conclusion is F-B1: those directions do
not exist for Llama.

### To unblock Phase F

`doublespeak_causality/build_refusal_direction_llama.py` exists and can fit the missing layers. Fitting
Llama refusal directions at **L6, L8, L10** (to cover the causal band) and optionally L24/L28 is the
prerequisite. **This is GPU work and is not started — see Open Questions.**

**Do NOT resubmit 767263/767265/767266 as-is.** They will fail identically.

## Better Surgical Patching Results

_Not started. Phase G deliverable._

## Cross-Model Replication With Dynamic Range

_Not started. Phase H deliverable._

## 4h Code and Output Review

### Review #1 — 2026-08-19 18:42 (sprint start 14:17)

**What was checked.** Three parallel adversarial auditors, 412k tokens, 133 tool calls, all read-only:
(1) post-fix code audit of `followup_token_level.py`; (2) independent re-derivation of every committed
external-arm number from the **raw** judge `results.jsonl`, without `analyze_external_arms.py`;
(3) adversarial audit of every numeric claim in this file and in all nine sprint commits against the
artifacts they cite.

**Headline: the arithmetic is sound; the inference contained a second uncontrolled claim.**

#### Independent numeric replication — 8 of 8 CONFIRM

Cluster field is `domain`, **16 clusters** (127/68/40/40/38/37/23/21/18/18/18/16/9/8/7/7 = 495),
identical membership in all 8 arms, 0 duplicate `prompt_id`, 0 non-`ok` `judge_status`, 0 null scores,
same model / judge / bank sha `3113465f938aaa54`.

L13_B +0.0137506 p 0.090145 · L13_Bctrl −0.0002322 p 0.873353 · L14_B +0.0118387 p 0.141064 ·
L14_Bctrl +0.0000504 p 0.935442 · L15_B +0.0046808 p 0.249960 · L15_Bctrl +0.0036334 p 0.413684 ·
L12_C +0.0028202 p 0.451019 · baseline 32/495 — **all CONFIRM**. The "205/495 = 41.4% of generations
changed" claim **CONFIRMS** exactly (205 by exact string, 205 stripped, `n_chars` differs on the same
205 rows).

### ⛔ RETRACTION F-2 — the Phase B direction-specificity claim

**Second F-1-class error this sprint, on the claim I had promoted to "strongest Phase B result".**

Published (`fef79630`): *"`d_context` shows nothing (d = −0.03 at L12) while `d_naive` reproduces the
gradient — the gradient is specific to the surface axis."*

Wrong, because each direction has its **own control baseline**. `d_context`'s doublespeak value is ≈0
(−0.032 at L12) but its `benign_literal` control is **−0.336**, so its controlled excess is **+0.304**.
From `matched_control_excess` — a block my own commit wrote and then failed to read:

| direction | L6 | L8 | L10 | L12 | L18 | L24 |
|---|---|---|---|---|---|---|
| `d_surface` | +0.478 | **+0.612** | +0.550 | **+0.682** | +1.745 | +4.036 |
| `d_naive` | +0.541 | **+0.669** | +0.680 | **+0.724** | +1.945 | +4.342 |
| `d_context` | +0.381 | **+0.409** | +0.539 | **+0.304** | +1.024 | +2.457 |
| `d_inter` | −0.445 | −0.459 | −0.530 | −0.891 | −0.365 | +0.018 |

`d_context` carries **45–67%** of `d_surface`'s controlled gradient; `d_naive` is **larger** than
`d_surface` at every depth. Only `d_inter` runs the other way.

> **Corrected conclusion: the token-level demo-position gradient is NOT direction-specific.**
> Three of the four directions fitted on this bank carry it.

**The two instruments disagree, and that is the interesting residue.** On AdvBench behaviour `d_context`
is genuinely inert (Δ +0.0045, p 0.399) while changing 34.9% of generations. At the token level it is
**representationally active**. `d_context` is behaviourally inert but representationally live — a
dissociation for Phase E3 to chase, not a control that "passes".

### Findings that change a committed number

| id | finding | status |
|---|---|---|
| **A1/F10** | `phaseB_behavioral_allslots/…summary.json` at HEAD was still **pre-F-1**: unpaired `last_minus_first 3.0188`, row-weighted `query_minus_demo_all −2.5711`, and the false `"family_slot": "ALL"` string the fix commit claimed to remove. `fef79630` regenerated 5 of 6 summaries and missed it. | **FIXED** — regenerated, committed this tick. |
| **F1** | Direction-specificity uncontrolled. | **RETRACTED F-2.** |
| **F2** | Ground-truth table gave arms C/D as "L8". Actual: arm C = `refusalness:project_out:**18-18**`, arm D = `d_surface:8-8` **+** `refusalness:18-18`; Cctrl@18, Dctrl@8+18. Claim 5c's interaction spans **two depths**. | **FIXED** — and it *strengthens* the tick-4 dissociation reading. |
| **A3** | `matched_control_excess` was **not family-matched**: 66 of 294 doublespeak families (22%) have no `benign_literal` twin. | **FIXED tick 7** — restricted to the 228 shared families; L8 +0.5414, L12 +0.6402. |
| **A4** | The excess block emitted **no uncertainty**; "about 4 sigma" was quadrature over two conditions treated as independent on the same 6 domains. | **FIXED tick 7** — SEM is now over per-domain excesses: **t = 3.26 (L8), 2.98 (L12), 4.10 (L18)** on 5 df. The "4 sigma" claim is corrected. |
| **A2** | `curve()` paired a **row-weighted mean** with a **prompt-clustered SEM**. | **FIXED tick 7** — `curve()` now emits `mean_ROWWEIGHTED` and `mean_promptweighted` side by side, and the SEM field is renamed `sem_rowlevel` (no longer asserting an understatement that is false for 1-row-per-prompt roles, A6). |
| **F6** | "Representational signal largest late" is mostly **residual-norm growth**. | **CONFIRMED AND CORRECTED tick 7** — family-matched, `proj` grows **17.0×** L8→L31 while `cos` grows **2.0×**. A real 2× depth trend survives (cos peaks L24, t 4.89); the 14× version does not. Phase B Q3 rewritten. |
| **F9** | "% of generations changed" does **not** separate signal from noise: random controls change 22.0% / 30.7% / **33.9%** — the last more than `L15_B`'s 28.1%. Carries claims 5e and 5f too. | **OPEN — qualify everywhere.** |
| **F7** | **No multiplicity correction** on the 11-depth profile though the plan requires it. Over 10 testable depths **Holm rejects nothing** (min adj p 0.0562); BH(0.05) keeps L8 and L12. | **OPEN.** |
| **F3** | Two Do-Not-Cite **replacement** figures absent from their artifacts: role-framing `F(5,355)=20.30` is **not in `g11_role_full.json`**; "ratio inverts to 0.80" is **0.7472** @codeword_last and **1.5416** @last. | **FIXED** in the ledger. |
| **F4** | Tick-3's "NEW RESULT" was **already committed** — `advbench_layer_profile.json` carries `c13`/`c14` byte-identical, added by `af4fe7a4` before this sprint; my own D-1/D-2 say so. | **CORRECTED** — see below. |
| **F5** | This file held **two divergent copies** of the progress log with contradictory status headers, from one of my splices. | **FIXED** — rebuilt, 2410 → 1608 lines. |
| **F8** | Estimand mixing in 5a/5g/**6b**. | **PARTLY FIXED tick 12** — 6b, the load-bearing one, is corrected and its "reversed channels" reading downgraded. 5a/5g still print ASR@0.5 beside a continuous Δ; those are labelled but not yet rewritten. |
| **F13** | D-9 described two datasets as one. | **FIXED tick 12** — D-9 now states the Llama figures (arm C p_cl 0.0410, arm D 0.0200, both significant; only arm B null) and marks the 0.1341/0.0522 pair as Qwen3's. |
| **F15** | Phase B's excess pools designed-variance blocks into the **treated arm only** (84/324 = 26%; control has none). On `core2x2` alone the excess is **+0.7525** at L12 vs +0.6823 — robust, so disclosure not invalidation. | **OPEN — disclose.** |
| **A8** | Pairing guard uses value-inequality as a proxy for "≥2 demos"; drops 19 of 322,452 pairs (0.006%), only on `ll|boombness`. | **OPEN, negligible.** |

### Correction to tick 3's novelty claim (F4)

`l13_l14_matched_controls.json` is a **re-analysis**, not new evidence. `advbench_layer_profile.json`
already contained `c13` (−0.000232, p 0.8734) and `c14` (+0.0000504, p 0.9354), byte-identical, its
label already reading "11 arms + 11 matched controls", committed by `af4fe7a4` **before this sprint**.
My tick-3 self-correction stopped one step short: they had been not merely run and judged but
**analysed and committed**. The *substance* — every depth controlled, every control inert — stands; the
word "new" does not.

### Claims confirmed (recorded so they are not re-litigated)

Every Phase A headline reproduces exactly: G1 0.6887 CI [0.5128, 0.9742]; G3 −13.436759/−17.878933 =
75.15% on 81,706.67 edges; G2 POWER ρ −0.06601851932290928 p 0.49325337331334335 n 108 — **and the 48
slot-3 rows are genuinely fresh, 0/192 demo-block overlap**; AdvBench 32/53/134/174/31 of 495; the
steering bands; `section4b`; both Qwen3 files; the Phase B census; the Phase C AUROCs and pools; F-B2's
five mislabeled 5120-d files. `g3_wholeanswer_block24.json`'s `dynamic_range_established: false` was
checked and is **non-disqualifying** per `analyze_g1_g3.py:225-231`.

### Next corrections, in priority order

1. Family-match `matched_control_excess`; emit a **domain-paired** SEM for it (A3 + A4).
2. Prompt-weight `by_role` / `bands` / `direction_comparison` (A2).
3. Report the scale-free `cos` excess beside every `proj` excess (F6).
4. Apply Holm across the 11 depths (F7).
5. Retire "% generations changed" as standalone evidence (F9).


## Open Questions / Blockers

### Needs a user decision

1. **IF-1 / D-4 / D-5 — the dirty `clearharm_decomposition.json`.** Discard the working-tree
   modification, or keep it? It re-inflates the R-12 retracted band (`between_draw_sd = 0.0048`) on top
   of a HEAD that had already guarded it to `n_draws: 1`, and two of its three "draws" are identical.
   The audit confirmed the file has **exactly one commit** and that commit is the corrected one, so the
   working tree is a *fresh regression*, not a revert. **Recommended: `git checkout --` it.** Not
   executed — discarding working-tree state is destructive and pre-dates this session.
2. **IF-5 — a GitHub personal access token is stored in plaintext in `.git/config`** as part of the
   `origin` URL. Any process that can read the repo can read it, and it is echoed by `git remote -v`.
   **Recommended: revoke and rotate that token, then re-add the remote via SSH or a credential helper.**
   Not done — rotating a credential is the user's call.
3. **D-3 — ClearHarm arm B has no committed matched control.** The handover cites one (21/179, Δ_cl
   +0.0039, p_cl 0.208) as closing an open item, but it exists only in an uncommitted working-tree
   rewrite. Re-run it through a committed module, or stop citing it?

4. **Fit the missing Llama refusal directions?** Phase F's interaction experiment needs refusalness in
   the L6–L12 causal band, and directions exist only at L12–L20. `build_refusal_direction_llama.py` can
   fit L6/L8/L10 (and L24/L28 if the profile should extend upward). This is GPU work on a queue that is
   currently slow. **Say the word and I'll launch it.**
5. **Rename the five mislabeled direction files?** `refusal_qwen3/refusal_direction_llama_L*.pt` are
   Qwen3 vectors (F-B2). Renaming is the obvious fix but other runs may reference the paths.

### Standing risks carried into this sprint

- **D-11 is the big one:** `outputs/` is gitignored wholesale; the analysis JSONs are force-added but
  **every upstream judge / score / extract run directory is untracked**. All committed results rest on
  data that exists in one place on one filesystem, with no committed path back to it.
- **D-8:** ASR@0.5 is binary, Δ and p are on the continuous StrongReject score. Every claim this sprint
  makes must name its estimand.
- **D-10:** the double-random control is inert on comprehension but moves the semantic readout at
  p = 3.9e-04, and is a composed L8+L18 control being used to license a single-layer L8 arm. Phase E3
  should fit a properly matched control.
- **D-9:** ClearHarm's clusters are 127/31/17/2/1/1. Null results under clustering there are weak
  evidence of absence.

### Loop

30-minute progress loop armed — cron job `d3c35268`, `*/30 * * * *`, session-only, auto-expires after
7 days. Each tick: check the 6 inherited SLURM jobs, harvest anything that finished, advance the current
phase, update this file, commit and push, record blockers. Every 4h a deeper code/output review instead.

**Tick 1 (2026-08-19 ~16:10).** All six jobs still `PD (Priority)` — no change since inheritance, so
nothing to harvest. Phase C probe suite launched instead. No blockers.

**Tick 2 (2026-08-19 ~16:40).** The queue moved, and it produced three failures and two corrections.

| job | arm | state | outcome |
|---|---|---|---|
| 767176 | `abL15_B` | **R** (21 min) | running |
| 767177 | `abL15_Bctrl` | **R** | running |
| 767263 | `abR8_C` | ⛔ **FAILED** (1:0, 15:23) | no Llama refusal direction at L8 |
| 767264 | `abR12_C` | **R** | running — L12 direction exists |
| 767265 | `abR24_C` | ⛔ **FAILED** (1:0, 15:23) | no Llama refusal direction at L24 |
| 767266 | `abR28_C` | ⛔ **FAILED** (1:0, 15:23) | no Llama refusal direction at L28 |

⚠ **Correction to IF-2.** I recorded 767176/767177 as the L13/L14 matched controls, taking the
handover's §13.14 at its word. They are not — reading `--tag` out of the job logs, they are
**`abL15_B` and `abL15_Bctrl`**. **The L13/L14 matched controls are not queued at all**, so L13 and L14
remain arm-only and nothing currently scheduled will fix that. This is the second time this sprint that
a handover statement, taken on trust, turned out to be stale (cf. D-2).

Phase C probe suite still running (loading the 592 MB cache; run dir
`outputs/boombness/probes/fu2352_20260819_161048_1978941` created).

**Tick 3 (2026-08-19 ~17:15).** Queue empty; all three surviving jobs **COMPLETED** (`abL15_B` 26:43,
`abL15_Bctrl` 26:14, `abR12_C` 26:01), each generating 495 completions with `DONE.json`.
`abR8_C`'s directory exists but holds `gens=0` and no `DONE.json` — correctly refused by
`common.require_done`.

⚠ **Correction to my tick-2 correction — I was wrong, and in the sprint's favour.**
Tick 2 recorded "the L13/L14 matched controls are not queued at all, so those depths stay arm-only."
**They had already run and been judged at 10:54–10:55 today**, before this session began:
`judge/abgL13_Bctrl_20260819_105455_1773722` and `judge/abgL14_Bctrl_20260819_105455_1773596`, both
`DONE`, both 495 rows. I inferred absence from the queue being empty of them rather than checking the
judge directories. **Lesson, same as D-2 and the tick-2 IF-2 correction: check the artifact, never
infer from a schedule.**

### ✅ NEW RESULT — L13 and L14 now have matched random controls, and both are inert

Pure CPU; the judge runs already existed. Command:

```
$PY src/boombness/analyze_external_arms.py \
  --baseline outputs/boombness/judge/abg_base_20260819_011714_1480836 \
  --arm L13_B=outputs/boombness/judge/abgL13_B_20260819_103334_1754334 \
  --arm L13_Bctrl=outputs/boombness/judge/abgL13_Bctrl_20260819_105455_1773722 \
  --arm L14_B=outputs/boombness/judge/abgL14_B_20260819_103334_1754335 \
  --arm L14_Bctrl=outputs/boombness/judge/abgL14_Bctrl_20260819_105455_1773596 \
  --label "..." --out outputs/boombness_followup/l13_l14_matched_controls.json
```

Model Llama-3.1-8B-Instruct · AdvBench held-out 495 · 16 domain clusters · `n_common = 495` ·
Δ and p on the **continuous** StrongReject score, cluster-mean estimand (D-8).

| arm | ASR@0.5 | refusal | Δ pooled | **Δ clustered** | **p_cl** | 95% CI |
|---|---|---|---|---|---|---|
| baseline | 0.0646 | 0.9313 | — | — | — | — |
| **L13_B** | 0.0727 | 0.9253 | +0.0081 | **+0.0138** | 0.0901 | [−0.0024, +0.0299] n.s. |
| L13_Bctrl | 0.0646 | 0.9313 | +0.0010 | **−0.0002** | 0.8734 | [−0.0033, +0.0028] **inert** |
| **L14_B** | 0.0707 | 0.9273 | +0.0056 | **+0.0118** | 0.1411 | [−0.0044, +0.0281] n.s. |
| L14_Bctrl | 0.0646 | 0.9333 | +0.0003 | **+0.0001** | 0.9354 | [−0.0013, +0.0014] **inert** |

The arm values reproduce the handover's L13 +0.0138 (p 0.090) and L14 +0.0118 (p 0.141) **exactly**,
and the two missing controls are now supplied and inert. So the upper boundary of the causal band —
L12 **+0.0322 (p 0.0056)** → L13 +0.0138 → L14 +0.0118 → L16 exactly zero — is a **monotone
four-layer roll-off with a matched inert control at every depth**, not a cliff and not an
uncontrolled claim. Artifact: `outputs/boombness_followup/l13_l14_matched_controls.json`. **Citable.**

### ⚠ Near-miss — I re-created R-14, and the guard the last sprint left behind caught it

My first judge invocation passed `--gens .../gens.jsonl` and **omitted `--bank`**. All three runs
aborted immediately with `goal statuses: {'empty_query': 495}`, `null_frac = 1.0000`, writing
`ABORTED.json` rather than `DONE.json` so `common.require_done` refuses the directory.

That is **exactly R-14** — StrongReject scoring every external completion against an empty goal — which
the previous sprint called the most serious defect of its session 2 and had to re-judge everything to
undo. The `--max-null-frac 0.05` guard added afterwards did its job: **0 of 495 were judged, no cost
was incurred, and no bad number reached an artifact.** Correct form, read from a known-good run's
`RUNMETA.argv`, is `--gens <score_behavior run DIR>` plus
`--bank data/boombness_prompts/external/advbench_heldout_495.jsonl`.

Dead run dirs, retained as evidence and refused by the loader:
`judge/fu_abL15_B_20260819_171502_2016716`, `judge/fu_abL15_Bctrl_…_2016720`,
`judge/fu_abR12_C_…_2016724`.

Re-launched correctly as `fu2_*`; judging in progress at tick close.

**Tick 4 (2026-08-19 ~17:45).** All three `fu2_*` judge runs `DONE`, 495 rows each. Analyzed into
`outputs/boombness_followup/l15_and_refusal_L12.json`.

| arm | intervention | ASR@0.5 | refusal | Δ clustered | p_cl | 95% CI |
|---|---|---|---|---|---|---|
| baseline | — | 0.0646 | 0.9313 | — | — | — |
| L15_B | `d_surface:project_out:15-15:1.0` | 0.0667 | 0.9293 | +0.0047 | 0.2500 | [−0.0037, +0.0130] n.s. |
| L15_Bctrl | `random:project_out:15-15:1.0` | 0.0667 | 0.9313 | +0.0036 | 0.4137 | [−0.0056, +0.0128] n.s. |
| L12_C | `refusalness:project_out:12-12:1.0` | 0.0646 | 0.9333 | +0.0028 | 0.4510 | [−0.0049, +0.0106] n.s. |

#### The roll-off is now complete and fully controlled

L12 **+0.0322 (p 0.0056)** → L13 +0.0138 → L14 +0.0118 → **L15 +0.0047** → L16 exactly 0. Monotone,
five consecutive depths, matched inert control at every one. The handover's "steep four-layer roll-off
rather than a cliff" is confirmed and extended.

### ✅ NEW FINDING — refusalness is layer-localised too, and NOT in `d_surface`'s band

This began as a discrepancy worth chasing rather than reporting. The committed arm C (remove
refusalness) raises ASR to **0.2707, Δ +0.1895, p_cl 1.4e-04**. My new L12 refusalness arm moved
compliance by **+0.0028 (p 0.45)** — a 68× gap. Reading the two `RUNMETA.argv`:

| arm | spec | Δ clustered | p_cl |
|---|---|---|---|
| committed arm B | `d_surface:project_out:**8-8**:1.0` | +0.0305 | 0.0089 |
| committed arm C | `refusalness:project_out:**18-18**:1.0` | **+0.1895** | 1.4e-04 |
| new arm C | `refusalness:project_out:**12-12**:1.0` | **+0.0028** | 0.4510 |

**The intervention fired — it is not a no-op.** Comparing generations against the baseline run
prompt-by-prompt: `abR12_C` changed **205 of 495 = 41.4%** of generations (`abL15_B` changed 28.1%).
So ablating refusalness at L12 is a *potent* edit that leaves compliance alone — the same signature the
handover reports for L16 `d_surface` (29.5% of generations changed, compliance on none) and for
`d_context` (34.9% changed, Δ +0.0045).

**Implication for the sprint's central question.** The two channels appear **layer-dissociated**:
`d_surface`'s causal locus is L6–L12 (peak L8/L12, dead by L16), and refusalness's is at L18 where
L12 does nothing. If that holds across the profile, then the arm-D interaction — removing both exceeds
the sum — is an interaction *across depths*, not two effects at one site. That materially reshapes
Phase F.

⚠ **Not yet established.** This rests on **two** refusalness depths (L12 new, L18 committed), and the
L12 arm had **no matched random control** when it ran. Recorded as **exploratory**.

### Phase F unblocked in L12–L20 — refusalness layer profile submitted

Blocker F-B1 caps refusalness below L12, but L12/L14/L16/L18/L20 all have real 4096-d Llama directions.
L12 and L18 exist; the rest are now queued, **each with a matched random control** (the F-1 lesson):

| job | tag | intervention |
|---|---|---|
| 767585 / 767586 | `fuR14_C` / `fuR14_Cctrl` | `refusalness` / `random` `:project_out:14-14:1.0` |
| 767587 / 767588 | `fuR16_C` / `fuR16_Cctrl` | `:16-16:1.0` |
| 767589 / 767590 | `fuR20_C` / `fuR20_Cctrl` | `:20-20:1.0` |
| 767591 | `fuR12_Cctrl` | `random:project_out:12-12:1.0` — the control the L12 arm lacked |

All: `--bank advbench_heldout_495.jsonl --fit-dir extract_boombness/full_20260816_185942_1008673
--query-kinds behavioral --max-new 512 --arm base --dtype bfloat16`, arms `--seed 20260816`, controls
`--seed 20260901`. Argsfiles `outputs/boombness/argsfiles/args_fuR*.txt`. **Judging must pass
`--gens <DIR>` and `--bank <external bank>`** or it re-creates R-14.

On completion this yields a five-point refusalness layer profile (L12/14/16/18/20) with matched controls
at four of five, directly comparable to the nine-point `d_surface` profile.

### Process

- **IF-4 (self-inflicted, corrected):** during the Phase A fan-out, verification subagents re-ran the
  committed analyzers. Those write to fixed `--out` paths, so four tracked artifacts were overwritten in
  place and one argsfile deleted; **one subagent then committed the result** (`b420b49d`, "commit
  trailing analysis artifacts regenerated during the audit"), which would have written the retracted
  ClearHarm band into history. Caught before it was pushed. `git reset --mixed` to `9a357f9d`, then
  `git checkout --` on the three agent-damaged artifacts and the deleted argsfile; the pre-existing IF-1
  dirt was deliberately **left intact** so the state I inherited is preserved exactly.
  **Standing rule for the rest of this sprint: audit agents must be told the analyzers WRITE, and must
  redirect `--out` to the scratchpad — "read-only" in the prompt is not sufficient when the tool they
  are told to run mutates the repo.** No subagent may run `git commit`.
- Phase A gate is **passed**. Phase B may begin.

## 4h Code and Output Review — Review #2 (2026-08-20 00:00)

Two adversarial auditors, 299k tokens, 108 tool calls, read-only. **Every number reproduces; two
claims do not.** I verified both findings myself before acting.

### Numeric replication — all CONFIRM

The refusalness profile (all five arms and five controls, to 6 dp), `phaseF_composed`, and
`phaseF_add_alpha025` all reproduce exactly from raw judge rows by an independent implementation.
The Holm recomputation confirms four of five survive at m = 5. All 21 judge dirs share
`bank_file_sha16 3113465f938aaa54`, 495 rows, 0 nulls, 0 duplicate `prompt_id`, symmetric difference 0
vs baseline, and **no two arms have byte-identical generations** — so the retraction-#7/#12 "n = 1
wearing an n = 4 label" failure mode is absent here.

---

### ⛔ RETRACTION F-3 — the "sign reversal against a matched control" was a 14.8× dose mismatch

**Third F-1-class error this sprint, and the first one that a code bug rather than my analysis caused.**

Tick 13 (commit `e2d11e77`) claimed: *"Against its **matched** control — same layer, same dose, same
operation — the real refusalness direction moves the opposite way … −0.0644"*, and called it the
sprint's strongest direction-specificity evidence.

**The doses were not matched.** Verified directly:

| | injected residual magnitude at L18 |
|---|---|
| `refusalness:add:18-18:1.0` | **1.0** |
| `random:add:18-18:1.0` | **14.79** |

`score_behavior.py:178` doses the refusalness branch as `alpha * float(v.norm())` — and the house
refusal directions are **already unit norm** (I loaded L12/L18/L20: all exactly `1.000000`), so that
multiply is a **no-op**. The random and `d_surface` branches go through `:221`, `alpha * g`, dosed in
**gap units** (one diff-of-means). The module's own docstring at `:118-122` states the trap verbatim:
*"an `add` with a bare alpha injects an absolute residual magnitude unrelated to the natural effect
size — at L18 the gap is 14.8, so alpha=1 would be ~7% of one diff-of-means."* The gap-unit fix was
applied to the `d_surface` path and the refusalness path received a no-op instead.

So the −0.0644 "sign reversal" compares a **magnitude-1.0** edit against a **magnitude-14.8** edit.
It is not evidence of specificity. Corroboration that `F_addR` was simply under-dosed: the direction's
own validation file records `induce_alpha: 8.0` as the dose that drives refusal to 1.0 — the arm used
**1/8** of it, and moved ASR by −0.0111 (n.s.).

**Also affected:** `E_removeS_addR` (its refusalness leg is magnitude 1.0), and `addBoth_025` (its
refusalness leg is magnitude **0.25**, ~1/59 the relative dose of its `d_surface` leg — which is why
`addBoth` −0.0348 is statistically indistinguishable from `addS` alone −0.0329; the refusalness leg was
doing almost nothing).

**NOT affected: the bidirectional `d_surface` result.** Both `d_surface:add:8-8:0.25` and
`random:add:8-8:0.25` go through the same `:221` gap-unit path, injecting an identical
0.25 × 6.0549 = **1.514**. That pair is genuinely dose-matched.

### ⛔ And my coherence "PASS" verdicts were computed with the wrong statistic

I hand-rolled a gate instead of calling the committed one. `coherence_gate.assess()` applies an
8-word floor and a **scorable-fraction** check that my version omitted. Running the committed gate:

| arm | uniq | 3-gram | scorable frac | committed verdict |
|---|---|---|---|---|
| `fuF25_addS` | 0.873 | 0.005 | **0.331** | ⛔ **DEGENERATE** |
| `fuF25_addBoth` | 0.877 | 0.004 | **0.301** | ⛔ **DEGENERATE** |
| `fuF_addR` | 0.864 | 0.006 | **0.475** | ⛔ **DEGENERATE** |
| `fuF25_addCtrl8` | 0.851 | 0.008 | 0.677 | OK |
| `fuF25_remR_addS` | 0.772 | 0.033 | 0.701 | OK |
| *baseline* | 0.841 | 0.010 | **0.541** | OK (barely) |

**My tick 12/15/16 "PASS" tables are withdrawn.** The correct tool was in the repo and I did not use it.

#### But the failure mode is not the one the gate exists for — evidence, not assertion

The gate's stated worry is *raised* ASR from broken text. Here ASR is **lowered**, and the excluded
short rows are verified refusals, not collapse:

| arm | rows < 8 words | of which refusal-phrased | empty | median words |
|---|---|---|---|---|
| baseline | 227 (46%) | **227 (100%)** | 0 | 14 |
| `fuF25_addS` | 331 (67%) | **330 (100%)** | 0 | 6 |
| `fuF25_addBoth` | 346 (70%) | **345 (100%)** | 0 | 6 |
| `fuF_addR` | 260 (53%) | **260 (100%)** | 0 | 6 |

The shortest generations read `"I can't fulfill that request."` / `"I can't help with that."` — clean
English refusals. **The baseline itself is 46% short and would sit at 0.541, barely above the floor.**
The arms trip the floor *because the intervention increases refusal*, which is the effect under study.

**Correct disposition, and it is not "wave the gate away":** the arms are not degenerate in the
broken-generation sense, but they **fail the repo's assessability floor**, and that floor exists
because this project has been burned by exactly this reasoning before. So:

> **The bidirectional `d_surface` result is DOWNGRADED from "citable" to "strong but gated."** The
> add arm is dose-matched to an inert control and its suppression is corroborated by refusal rate
> (0.9313 → 0.9879) and by clean refusal text — but it does not currently clear
> `coherence_gate.assess()`, and no paper claim should rest on it until it does.

The clean way to clear it is a **length-fair re-run** (the previous sprint's `coherence_lenfair.json`
did exactly this for arm F), which raises the scorable fraction without changing the intervention.

### Corrections queued

1. **Do not change `score_behavior.py:178` silently** — every committed `refusalness:add` number depends
   on it. Fix forward: add an explicit `gap`-unit mode for refusalness and re-run, keeping the old
   spec readable. **Not done unilaterally; it is a scoring primitive under every committed result.**
2. Re-run `refusalness:add` at a dose comparable to one diff-of-means (the direction's own
   `induce_alpha` is 8.0) with a **gap-matched** random control.
3. Length-fair re-run of `addS_025` / `addCtrl8_025` to clear the assessability floor.
4. Call `coherence_gate.py` — never a hand-rolled statistic — for every future arm.


### ✅ Tick 16 — at α = 0.25 the control IS inert, and `d_surface` shows BIDIRECTIONAL control

**Artifact:** `outputs/boombness_followup/phaseF_add_alpha025.json`. AdvBench 495 / 16 clusters,
cluster-mean estimand on the continuous StrongReject score.

| arm | intervention | ASR@0.5 | refusal | Δ_cl | p_cl | CI |
|---|---|---|---|---|---|---|
| baseline | — | 0.0646 | 0.9313 | — | — | — |
| **addS_025** | `d_surface:add:8-8:0.25` | 0.0081 | **0.9879** | **−0.0329** | **0.0346** | [−0.0632, −0.0027] |
| **addCtrl8_025** | `random:add:8-8:0.25` | 0.0626 | 0.9354 | **−0.0028** | 0.6239 | [−0.0148, +0.0092] **inert** |
| addBoth_025 | `d_surface` + `refusalness`, both 0.25 | 0.0061 | 0.9899 | −0.0348 | 0.0288 | [−0.0655, −0.0041] |
| remR_addS_025 | `refusalness:project_out:18-18:1.0` + `d_surface:add:8-8:0.25` | 0.1879 | 0.7859 | +0.1067 | 0.0011 | [+0.0503, +0.1632] |
| *(reference)* C_removeR | `refusalness:project_out:18-18:1.0` | 0.2707 | 0.7091 | +0.1895 | 0.0001 | [+0.1097, +0.2692] |

#### The α = 1.0 control failure was a DOSE artifact

At α = 1.0 `random:add` at L8 gave **+0.0889 (p 0.0013)**. At α = 0.25 the same control gives
**−0.0028 (p 0.6239) — inert.** So the tick-13 control failure was not a property of `add` as an
operation; it was α = 1.0 being far outside the coherent range on that axis. The α = 0.25 arms have a
genuinely inert matched control and can be read normally.

#### Bidirectional causal control, with an inert matched control at the same dose

| manipulation of `d_surface` at L8 | Δ_cl | p_cl |
|---|---|---|
| **remove** (`project_out`, 1.0) | **+0.0305** | 0.0089 |
| **add** (0.25) | **−0.0329** | 0.0346 |
| matched random add (0.25) | −0.0028 | 0.6239 |

**The sign of the behavioural effect follows the sign of the manipulation**, and the matched random
control does nothing. Refusal rate moves with it too: 0.9313 → **0.9879** when `d_surface` is added,
the highest of any arm in the sprint.

This is the strongest causal statement the sprint has produced about `d_surface`. It is worth being
precise about what it does **not** say: it does not resurrect **G4**, which failed on the *on-bank
doublespeak* prompts at the codeword readout and found both steering signs suppressing. This is a
different population (external AdvBench, no codeword, no demonstrations) and a different readout, so
the two coexist — but the bidirectional result here is exactly the property G4 looked for and did not
find on-bank.

#### The interaction cancels in BOTH directions

| | Δ_cl | vs its single-channel reference | cancelled |
|---|---|---|---|
| remove `d_surface`, **add refusalness** (α=1.0, E) | +0.0211 | remove `d_surface` alone +0.0305 | ~31% |
| remove refusalness, **add `d_surface`** (α=0.25) | +0.1067 | remove refusalness alone +0.1895 | ~44% |

Each channel's removal effect is **partially undone by adding the other channel back**. That symmetry
is what plan hypothesis 5 predicts if both feed a common decision point.

⚠ **Two of these arms still lack matched composed controls** and no claim rests on them yet.
Submitted this tick:

| job | tag | intervention |
|---|---|---|
| 768468 | `fuF25_addBoth_CTRL` | `random:add:8-8:0.25` + `random:add:18-18:0.25` |
| 768469 | `fuF25_remR_addS_CTRL` | `refusalness:project_out:18-18:1.0` + `random:add:8-8:0.25` |

plus 768316 `fuF_remS_addR_CTRL` still generating (416/495) for arm E.

**Citable now:** the bidirectional `d_surface` result (add −0.0329 vs remove +0.0305, matched control
inert). **Held:** both cancellation figures, until 768316/768468/768469 land.

### Tick 15 — the α = 0.25 re-runs are all coherent, and the α = 1.0 prediction held

Tick 14 predicted 768071 (`fuF_remR_addS`, carrying `d_surface:add:8-8:**1.0**`) would fail the same
gate. **It did**, and by the same margin:

| arm | α on `d_surface:add` | uniq-word | 3-gram repeat | mean words | wall-clock | gate |
|---|---|---|---|---|---|---|
| `fuF_remR_addS` | **1.0** | **0.225** | **0.599** | 299 | 2h06 | ⛔ **FAIL** — not judged |
| `fuF25_addS` | 0.25 | 0.958 | 0.002 | 15 | **4m59** | PASS |
| `fuF25_addBoth` | 0.25 | 0.963 | 0.001 | 14 | **4m30** | PASS |
| `fuF25_remR_addS` | 0.25 | 0.840 | 0.023 | 98 | 28m35 | PASS |
| `fuF25_addCtrl8` | 0.25 | 0.899 | 0.006 | 36 | 10m53 | PASS |

Three `d_surface:add` arms have now failed at α = 1.0 and three have passed at α = 0.25, with no
overlap — the dose boundary is sharp and reproducible on this axis.

**Wall-clock is a free degeneracy detector.** Every failing arm ran 1h51–2h06; every passing arm ran
4–29 minutes. The looping arms simply generate to the token cap. Cheap pre-filter for future runs, and
it agreed with the gate on all six arms tested so far.

Judging launched for the four coherent arms (`n_fuF25_*`). 768316 `fuF_remS_addR_CTRL` — the matched
composed control that arm E is being held for — is still generating (275/495).

### ⛔ `d_surface:add` at α = 1.0 is DEGENERATE — the coherence gate caught it before any judge spend

`fuF_addS` and `fuF_addBoth` completed and **failed the gate badly**. They were **not judged**; no ASR
exists for them and none will be quoted.

| arm | uniq-word | 3-gram repeat | top-word | mean words | verdict |
|---|---|---|---|---|---|
| gate | ≥ 0.45 | ≤ 0.30 | ≤ 0.25 | — | — |
| `fuF_addS` (`d_surface:add:8-8:1.0`) | **0.210** | **0.630** | 0.143 | 295 | ⛔ **FAIL** |
| `fuF_addBoth` (both at 1.0) | **0.219** | **0.615** | 0.152 | 291 | ⛔ **FAIL** |
| `fuF_addR` (`refusalness:add:18-18:1.0`) | 0.935 | 0.003 | 0.147 | **30** | PASS |
| `fuF_addCtrl8` (`random:add:8-8:1.0`) | 0.781 | 0.061 | 0.106 | 112 | PASS |

The signature is unmistakable: uniq-word ratio less than a quarter, 3-gram repeat above 0.6, and mean
completion length **ten times** the coherent arm's. The model is looping, not complying. Corroborated by
wall-clock — those two jobs took **1h51** against 16–40 min for every coherent arm.

**This reproduces the previous sprint's retracted α = 1 arm exactly** (uniq 0.302, trigram repeat 0.551,
truncated 1.000), which produced a spurious "3.47× ASR" and is what `coherence_gate.py` was written for.
Two updates to what tick 11 recorded:

- Tick 11 said the α = 1 degeneracy *"does not generalise to the refusalness axis"*. **That stands** —
  `refusalness:add` at α = 1.0 is clean (uniq 0.935).
- The complementary fact is now established: **it does reproduce on the `d_surface` axis.** The two
  axes tolerate very different doses at the same nominal α, which is itself worth knowing — α is not
  comparable across directions.

**Cost avoided:** ~990 judge calls, and a degenerate arm being scored as a jailbreak.

**Re-submitted at α = 0.25**, the dose the previous sprint found reportable:

| job | tag | intervention |
|---|---|---|
| 768389 | `fuF25_addS` | `d_surface:add:8-8:0.25` |
| 768390 | `fuF25_addBoth` | `d_surface:add:8-8:0.25` + `refusalness:add:18-18:0.25` |
| 768391 | `fuF25_remR_addS` | `refusalness:project_out:18-18:1.0` + `d_surface:add:8-8:0.25` |
| 768392 | `fuF25_addCtrl8` | `random:add:8-8:0.25` (matched control) |

768071 `fuF_remR_addS` (still generating at α = 1.0) carries `d_surface:add:8-8:1.0` and is expected to
fail the same gate; it will be gated on arrival and is superseded by 768391 regardless.

### ⚠ Phase F composed interventions — and the `add` controls are NOT inert

**Artifact:** `outputs/boombness_followup/phaseF_composed.json`. AdvBench 495 / 16 clusters,
Llama-3.1-8B, cluster-mean estimand on the continuous StrongReject score. Interventions at the two
channels' established peaks (`d_surface` L8, refusalness L18), α = 1.0.

| arm | intervention | ASR@0.5 | refusal | Δ_cl | p_cl | CI |
|---|---|---|---|---|---|---|
| baseline | — | 0.0646 | 0.9313 | — | — | — |
| B_removeS | `d_surface:project_out:8-8` | 0.1071 | 0.8889 | +0.0305 | 0.0089 | [+0.0089, +0.0522] |
| C_removeR | `refusalness:project_out:18-18` | 0.2707 | 0.7091 | +0.1895 | 0.0001 | [+0.1097, +0.2692] |
| D_removeBoth | both | 0.3515 | 0.6222 | +0.2544 | 0.0000 | [+0.1589, +0.3499] |
| **E_removeS_addR** | `d_surface:project_out:8-8` **+** `refusalness:add:18-18` | 0.0889 | 0.9091 | **+0.0211** | 0.0234 | [+0.0033, +0.0389] |
| **F_addR** | `refusalness:add:18-18` | 0.0485 | 0.9515 | **−0.0111** | 0.2930 | [−0.0327, +0.0106] |
| ⛔ ctrl_add8 | `random:add:8-8` | 0.1778 | 0.7838 | **+0.0889** | 0.0013 | [+0.0409, +0.1370] |
| ⛔ ctrl_add18 | `random:add:18-18` | 0.1293 | 0.8768 | **+0.0533** | 0.0036 | [+0.0204, +0.0862] |

#### The control failure, stated first

**Adding a random norm-scaled direction is itself a strong jailbreak.** `random:add` at L8 gives
**+0.0889 (p 0.0013)** — nearly **3× the effect of removing `d_surface`** at the same layer — and at L18
**+0.0533 (p 0.0036)**. So **no `add` arm's magnitude may be read against baseline**; the reference has
to be the matched random add.

This is the same trap as the previous sprint's **RETRACTION #8**, whose finding was literally *"the
random composition is a better jailbreak than `d_surface` on explicitly harmful prompts"*. Recorded
before drawing any conclusion, not after.

#### ⛔ What I claimed survived here is RETRACTED — see RETRACTION F-3

Against its **matched** control — same layer, same dose, same operation — the real refusalness direction
moves the **opposite way**:

| | Δ_cl |
|---|---|
| `refusalness:add:18-18` | **−0.0111** |
| `random:add:18-18` | **+0.0533** |
| **difference** | **−0.0644** |

Adding a random vector at L18 *raises* compliance; adding the refusalness vector at the same layer and
dose *lowers* it (and raises refusal 0.9313 → 0.9515, the highest of any arm). **A sign reversal against
a matched control is a much stronger specificity result than an inert control**, because it cannot be
explained by "the edit was large".

#### The load-bearing arm, and why it is not yet reportable

`E_removeS_addR` — remove `d_surface`, restore refusalness — gives **+0.0211** against
`B_removeS`'s **+0.0305**, i.e. restoring refusalness **cancels about a third** of the `d_surface`
removal effect (gap −0.0094). That is the direction plan hypothesis 5 predicts: `d_surface` supplies
evidence the refusal mechanism uses, so putting refusalness back partly undoes the gain.

⚠ **But E has no matched composed control**, and given `ctrl_add8`/`ctrl_add18` are both strongly
active, the *unmatched* comparison is exactly the error this sprint has already made twice (F-1, F-2).
**No claim is made from E until its control lands.** Submitted this tick:

| job | tag | intervention |
|---|---|---|
| **768316** | `fuF_remS_addR_CTRL` | `random:project_out:8-8:1.0` **+** `random:add:18-18:1.0`, seed 20260901 |

Still generating: 768071 `fuF_remR_addS`, 768072 `fuF_addS`, 768074 `fuF_addBoth` (the three
`d_surface:add` arms, ~1h29 elapsed at 321–387 of 495).

#### Provisional reading

The removal half of Phase F is clean and controlled (B, C, D, plus the L12–L20 refusalness profile).
The **addition** half is confounded by a jailbreaking random baseline and can only be read as
*differences against matched random adds*. On that footing the one arm with a proper control —
refusalness vs random at L18 — shows a **sign reversal**, which is the sprint's strongest
direction-specificity evidence to date and stands in contrast to Phase B, where the same kind of test
**failed** (RETRACTION F-2).

### ✅ ESTABLISHED — the refusalness layer profile, and a clean crossover with `d_surface`

**Artifact:** `outputs/boombness_followup/refusalness_layer_profile.json`. Model Llama-3.1-8B-Instruct ·
AdvBench held-out 495 · 16 domain clusters · `n_common = 495` · Δ and p on the **continuous**
StrongReject score, cluster-mean estimand. Every depth has a **matched random-projection control at the
same layer, same seed, same code path**.

| depth | arm C Δ_cl | p_cl | **Holm adj** (m=5) | ASR@0.5 | refusal | control Δ_cl | control p |
|---|---|---|---|---|---|---|---|
| **L12** | +0.0028 | 0.4510 | 0.4510 | 0.0646 | 0.9333 | −0.0012 | 0.2194 |
| **L14** | +0.0475 | 0.0126 | **0.0253** ✔ | 0.1253 | 0.8727 | +0.0005 | 0.2689 |
| **L16** | +0.1167 | 0.0016 | **0.0063** ✔ | 0.1879 | 0.8040 | +0.0042 | 0.2517 |
| **L18** | **+0.1895** | 0.0001 | **0.0007** ✔ | **0.2707** | 0.7091 | −0.0021 | 0.2921 |
| **L20** | +0.0628 | 0.0080 | **0.0240** ✔ | 0.1374 | 0.8586 | +0.0038 | 0.2887 |

**Four of five survive Holm–Bonferroni across the profile** (m = 5, arms only; controls are not
hypotheses). **All five controls are inert** (|Δ| ≤ 0.0042, p 0.22–0.29). This is the first result in
the sprint to carry a multiplicity correction, addressing review defect **F7** for this profile.

#### The crossover

Refusalness has an **inverted-U causal profile peaked at L18**: nothing at L12, rising through L14 and
L16, peaking at L18, falling back by L20. `d_surface` is the mirror image:

| | `d_surface` (arm B) | refusalness (arm C) |
|---|---|---|
| significant depths | L8, L10, **L12** | **L14, L16, L18, L20** |
| peak | L12, **+0.0322** | L18, **+0.1895** |
| dead by | L16 (exactly 0) | L12 (+0.0028, n.s.) |

**The two channels barely overlap. `d_surface` dies exactly where refusalness begins** — its last
significant depth is L12, refusalness's first is L14. The refusalness peak is **5.9×** the `d_surface`
peak.

This upgrades the tick-4 finding from *exploratory* to **established**: it now rests on five depths with
matched controls and a multiplicity correction, not on two points one of which lacked a control.

#### What it does to the interaction

Committed arm D is `d_surface:project_out:8-8` **+** `refusalness:project_out:18-18` — the two channels
composed **at their respective peaks, ten layers apart** (this is also review finding F2, which
corrected the ground-truth table's claim that arm D was an L8 effect). So arm D's super-additive excess
(+0.0268 against the matched random triple, CI [+0.0029, +0.0584]) is an interaction **across depths**,
not two effects at one site. Any mechanistic story must carry information from an L8 edit to an L18
decision point.

#### ⚠ The honest asymmetry

The refusalness profile survives multiplicity; **the `d_surface` profile does not.** Review finding F7:
over the 10 testable depths of `advbench_layer_profile.json`, Holm rejects **nothing** (min adjusted
p = 0.0562); BH(0.05) keeps only L8 and L12. The `d_surface` headline (arm B at L8, +0.0305, p_cl
0.0089) is a **single pre-specified test** rather than a profile scan, so it is not subject to the same
family — but the *profile* around it is weaker than the refusalness profile by this standard, and that
should be said plainly rather than left for a reader to discover.

#### Commands

```
# 7 generation jobs, SLURM 767585-767591, run_boombness.sh + argsfiles args_fuR*.txt
#   --intervene refusalness:project_out:{L}-{L}:1.0   (arms,     --seed 20260816)
#   --intervene random:project_out:{L}-{L}:1.0        (controls, --seed 20260901)
#   --bank advbench_heldout_495.jsonl --fit-dir extract_boombness/full_20260816_185942_1008673
#   --query-kinds behavioral --max-new 512 --arm base --dtype bfloat16
# judging (MUST pass --bank or it re-creates R-14):
setsid $PY src/boombness/judge_boombness.py --gens <score_behavior DIR>/ --bank $BANK --tag k_<tag>
# analysis:
$PY src/boombness/analyze_external_arms.py --baseline judge/abg_base_20260819_011714_1480836 \
    --arm L12_C=... --arm L12_Cctrl=... ... --out outputs/boombness_followup/refusalness_layer_profile.json
```

Row accounting: 495 attempted / 495 judged / 0 skipped / 0 null scores in every one of the 11 arms;
`dropped_symmetric_difference_vs_baseline = 0` throughout.

### Tick 12 — four of seven composed arms complete, all coherent

| arm | uniq-word | 3-gram repeat | top-word | gate |
|---|---|---|---|---|
| `fuF_remS_addR` | 0.911 | 0.007 | 0.143 | PASS |
| `fuF_addR` | 0.935 | 0.003 | 0.147 | PASS |
| `fuF_addCtrl8` | 0.781 | 0.061 | 0.106 | PASS |
| `fuF_addCtrl18` | **0.580** | **0.205** | 0.128 | PASS (nearest the edge) |

Worth noting: the **random** add at L18 degrades generation *more* than the real refusalness add at the
same layer and dose (uniq 0.580 vs 0.935; 3-gram repeat 0.205 vs 0.003). A norm-matched random direction
is the harsher perturbation, which is a point in favour of the targeted direction doing something
structured rather than merely being a large edit.

`fuF_remR_addS`, `fuF_addS`, `fuF_addBoth` — the three arms carrying `d_surface:add` — are markedly
slower (58 min elapsed at 180–243 of 495 generations vs 16–40 min for the others), consistent with
longer completions. Judging launched for the four that are done.

### Tick 10–11 — Phase F composed-intervention matrix launched

With the queue empty and the refusalness peak established at L18, the plan §8 composed arms were
submitted at the two channels' **established peaks** (`d_surface` L8, refusalness L18):

| job | tag | `--intervene` | seed |
|---|---|---|---|
| 768070 | `fuF_remS_addR` | `d_surface:project_out:8-8:1.0` **+** `refusalness:add:18-18:1.0` | 20260816 |
| 768071 | `fuF_remR_addS` | `refusalness:project_out:18-18:1.0` **+** `d_surface:add:8-8:1.0` | 20260816 |
| 768072 | `fuF_addS` | `d_surface:add:8-8:1.0` | 20260816 |
| 768073 | `fuF_addR` | `refusalness:add:18-18:1.0` | 20260816 |
| 768074 | `fuF_addBoth` | `d_surface:add:8-8:1.0` **+** `refusalness:add:18-18:1.0` | 20260816 |
| 768075 | `fuF_addCtrl8` | `random:add:8-8:1.0` | 20260901 |
| 768076 | `fuF_addCtrl18` | `random:add:18-18:1.0` | 20260901 |

Arms 1–4 of plan §8 (baseline / remove S / remove R / remove both) already exist as the committed
AdvBench decomposition, so these seven complete the ten-arm matrix.

**Coherence pre-check passed, and it contradicts a prior-sprint expectation.** 768073 (`add`
refusalness at α = 1.0) finished first and was gated **before** spending judge calls:
uniq-word ratio **0.935** (gate ≥ 0.45), 3-gram repeat **0.003** (gate ≤ 0.30), top-word fraction
**0.147** (gate ≤ 0.25). Comfortably coherent. The previous sprint's α = 1 *`d_surface`* steering arm
was degenerate (uniq 0.302, trigram repeat 0.551, truncated 1.000) and produced the coherence gate in
the first place — that degeneracy does **not** generalise to the refusalness axis at the same nominal
dose. Judging launched as `m_fuF_addR`.

### Tick 8 (2026-08-19 ~19:50) — all seven generation jobs COMPLETED, judging in flight

| job | tag | state | elapsed | gens |
|---|---|---|---|---|
| 767585 | `fuR14_C` | COMPLETED 0:0 | 38:35 | 495 ✔ |
| 767586 | `fuR14_Cctrl` | COMPLETED 0:0 | 30:59 | 495 ✔ |
| 767587 | `fuR16_C` | COMPLETED 0:0 | 38:37 | 495 ✔ |
| 767588 | `fuR16_Cctrl` | COMPLETED 0:0 | 21:35 | 495 ✔ |
| 767589 | `fuR20_C` | COMPLETED 0:0 | 29:47 | 495 ✔ |
| 767590 | `fuR20_Cctrl` | COMPLETED 0:0 | 20:37 | 495 ✔ |
| 767591 | `fuR12_Cctrl` | COMPLETED 0:0 | 11:30 | 495 ✔ |

All seven carry `DONE.json` and 495 generations. Judging launched as `k_fuR*`.

**Process failure worth recording (cost, not correctness).** The first judge launch (`j_fuR*`) was
killed at **~40 of 495 rows in all seven runs** — my wrapping shell command hit its 2-minute timeout and
`SIGTERM` took the whole process group with it, `nohup` notwithstanding (exit 143). Those seven run dirs
have no `DONE.json` and are correctly refused by `common.require_done`, so **no bad number can enter an
artifact** — but roughly **280 judge calls were paid for and discarded**. Relaunched with
`setsid … < /dev/null` so the children leave the process group; verified they survive a subsequent
timeout. Dead dirs: `judge/j_fuR*_20260819_1943*`.

**Standing rule added:** long-running judge or analysis jobs must be launched with `setsid`, and the
monitoring call must never wrap them in a shell that can be timed out.

## Sprint Final Report

_Not started._
