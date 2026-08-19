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
| 5b | refusalness removal is stronger | same | " | 495 | " | L8 | " | arm C **0.2707** (134/495), Δ **+0.1895**, p_cl **1.4e-04** | **established** |
| 5c | removing both is largest, with interaction | same + `advbench_superadd_control.json` | " | 495 | " | L8 | " | arm D **0.3515** (174/495), Δ **+0.2544**, p_cl **4.4e-05**; super-additive excess **+0.0333** CI [+0.0128, +0.0638]; **paired vs the matched random triple +0.0268** CI [+0.0029, +0.0584] | **established** |
| 5d | matched random controls inert | same | " | 495 | " | L8 | " | B-control **0.0626** (31/495), Δ **−0.0062**, p **0.539** | **established** |
| 5e | effect is **L6–L12** localised | `advbench_layer_profile.json` | " | 495 | " | **11 depths L4–L28** (see D-1) | " | significant L8 (p 0.0089), L10 (p 0.0190), L12 (**+0.0322**, p 0.0056); marginal L6; L13 +0.0138 (p 0.090), L14 +0.0118 (p 0.141); **null from L16 out**; L16 changes 29.5% of generations and compliance on none | **established** |
| 5f | direction-specific, not just better-than-noise | `advbench_direction_specificity.json`, `direction_cosines.json` | " | 495 | " | L8 | " | `d_surface` cos 1.000 → Δ +0.0305 (p 0.0089); `d_naive` cos **0.945** → Δ **+0.0449** (p 0.0089); `d_context` cos **0.188** → Δ **+0.0045** (p 0.399) despite changing 34.9% of generations | **established** |
| 5g | ClearHarm is **withdrawn**, not supporting | `clearharm_decomposition_regoal.json` | Llama / ClearHarm 179, 6 clusters | 179 | " | L8 | " | baseline 19/179, B 34/179, C 65/179, D 92/179, Dctrl 19/179; arm B **Δ_cl +0.0843, p_cl 0.2102, CI [−0.0665, +0.2350]** | ⛔ **withdrawn on ClearHarm (R-16)**; reinstated on AdvBench |
| 6a | Qwen3 AdvBench is **floor-limited** | `advbench_decomposition_qwen3.json` | **Qwen3-14B** / AdvBench 495 | 495 | `behavioral` | L8-equiv | " | baseline **0.0081** (4/495), arm B **0.0141** (7/495), Δ **+0.0024**, p_cl **0.657** | **established as a floor, NOT as a causal failure** |
| 6b | Qwen3 ClearHarm shows reversed channels | `clearharm_decomposition_qwen3.json` | Qwen3-14B / ClearHarm 179 | 179 | " | " | " | baseline **0.1341** (24/179), B **0.2793** (50/179), D **0.2793** (50/179) — B = D to 4 dp; p_cl **0.181** | **exploratory** (underpowered; see D-9) |
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
| **D-9** | **ClearHarm's clustering has almost no power.** Its 6 "domains" are sized **127 / 31 / 17 / 2 / 1 / 1** — two clusters are single prompts. | "No arm reaches significance under clustering on ClearHarm" is near-uninformative as evidence of absence. It also drives the gap between the pooled ClearHarm baseline (0.1341) and `asr_cluster_mean` (0.0522) — worth knowing before leaning on the 13.4%-vs-0.8% floor contrast in claim 6a. |
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
| **"Boombness beats refusalness 3.7×"** (and its predecessor "40×") | ⛔ **RETRACTION #5.** The two probes were read at **different tokens** | At matched position the ratio **inverts to 0.80**. `position_2x2.json` |
| **The incremental-R² pair "refusalness +0.144 vs Boombness +0.028"** | ⛔ **R-13.** Both increments against the same model, giving refusalness **5 df against Boombness's 1**. The pair exists in **no committed artifact in any commit** | At matched df on clean rows the ordering **reverses**: Boombness +0.0441, refusalness +0.0378. `g9_three_predictor_cwpos_CLEAN.json` |
| **"`project_out` is the only arm that leaves comprehension unchanged, p = 0.681"** | ⛔ **R-6.** Forced choice scored leading-space tokens at a position emitting the no-leading-space form | **Resolved in the sprint's favour**: comprehension **improves** +0.2795, p 0.00099. ⚠ See **D-6** (quote median mass ~0.31, not 0.297) and **D-7** (the retracted descriptors have no artifact) |
| **Role framing "does not move Boombness", F(5,810)=0.175, p=0.972** | ⛔ **RETRACTION #6.** Wrong error term; `plain` and role styles sit in **disjoint `bank_block`s** with zero family-id overlap | Role framing **does** move Boombness: within-stem **F(5,355)=20.30, p=8.1e-18** — though absolutely small. `g11_role_full.json` |
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

#### What survives, and what does not

| contrast | L8 | L12 | L18 | verdict |
|---|---|---|---|---|
| doublespeak − `benign_literal` (no mapping) | **+0.612** | **+0.682** | +1.745 | **survives.** ≈4σ against the combined domain-clustered sem. Teaching a codeword a referent steepens the gradient. |
| doublespeak − `direct_codeword` (mapping stated) | +0.159 | +0.147 | +0.049 | ≈0 |
| doublespeak − `benign_remap` (**benign** mapping taught) | **−0.258** | **−0.347** | −0.928 | **goes the wrong way** — but n = 24 pairs / 6 domains, sem 0.162. **Underpowered; not established either way.** |

**The finding is that the demo-position gradient tracks *"this codeword has a taught referent"*, not
*"the referent is harmful."*** Against the structure-matched benign control the doublespeak gradient is
if anything *smaller*. I will not call that a null — at n = 24 pairs it cannot exclude a modest
difference, and calling an underpowered null a finding of absence is defect **D-9** from Phase A.
Powering the F cell is now a Phase C/D item.

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

#### Q3 — layer band (unchanged, and still the interesting tension)

The excess over control grows monotonically with depth: +0.478 (L6), +0.612 (L8), +0.550 (L10),
+0.682 (L12), +1.745 (L18), +4.036 (L24), +6.492 (L30). The representational signal is **largest late**,
while the causal `project_out` effect is confined to **L6–L12** and null from L16 out. The layers where
the signal is biggest are not the layers where removing it changes behaviour. **This is now the sharpest
open question in the sprint and it is Phase E's job.**

#### Q4 — direction specificity (survives, and is the strongest Phase B result)

`demo_last − demo_first`, doublespeak:

| direction | cos with `d_surface` | L8 | L12 |
|---|---|---|---|
| `d_surface` | 1.000 | **+1.0971** (d +2.66) | **+1.4342** (d +2.64) |
| `d_naive` | 0.945 | +1.0048 (d +2.67) | +1.3110 (d +2.78) |
| `d_context` | 0.188 | **+0.0957** (d +0.35) | **−0.0123** (d −0.03) |
| `d_inter` | ≤0.24 | −1.0758 (d −2.90) | −1.3048 (d −2.22) |

The near-collinear sibling reproduces it; the near-orthogonal `d_context` shows **nothing** (d = −0.03 at
L12). So the gradient is specific to the surface axis rather than a generic drift. **This is the
token-level analogue of the AdvBench direction-specificity test**, where `d_context` was also inert
(Δ +0.0045, p 0.399) despite changing 34.9% of generations — two independent instruments, same sibling,
same verdict. *(These numbers are the uncontrolled within-doublespeak contrast; the point is the
comparison across directions, which shares the control.)*

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

### Command (running)

```
$PY src/boombness/probes.py \
  --run outputs/boombness/extract_boombness/full2352_20260818_115332_1410155 \
  --regimes d1_simple,d2_aligned,d3_hard_negative,d4_heldout_ds,\
            d5_surface_matched_codeword,d6_surface_matched_concept \
  --folds 3 --null-draws 20 --emit-scores --tag fu2352
```

Writes a new run dir under `outputs/boombness/probes/fu2352_*` — it does **not** overwrite any
committed artifact. Log: scratchpad `phaseC_probes.log`.



## Clean Fig-9-Style Boombness vs ASR Test

_Not started. Phase D deliverable._

## What Does d_surface Represent?

_Not started. Phase E deliverable._

## d_surface × Refusalness Interaction

_Not started. Phase F deliverable. Note: inherited jobs 767263–767266 (arm C at L8/12/24/28) supply the
refusalness layer profile this phase needs._

## Better Surgical Patching Results

_Not started. Phase G deliverable._

## Cross-Model Replication With Dynamic Range

_Not started. Phase H deliverable._

## 4h Code and Output Review

_No reviews yet. First review due 4h after sprint start._

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

## Sprint Final Report

_Not started._
