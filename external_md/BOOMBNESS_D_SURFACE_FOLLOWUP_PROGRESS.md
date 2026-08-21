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
| 5a | **removing `d_surface` raises external ASR** | `advbench_decomposition.json` | Llama / **AdvBench held-out 495**, 16 domain clusters — no codeword, no demos, no wrapper | 495 | `behavioral` | L8 | StrongReject, cluster-mean | baseline **0.0646** (32/495) → arm B **0.1071** (53/495) — these are **binary ASR@0.5**; the **Δ_cl +0.0305, p_cl 0.0089, CI [+0.0089, +0.0522]** is on the **continuous** score and is NOT their difference (which is +0.0425). Two estimands, stated (F8) | **established — the sprint's headline** |
| 5b | refusalness removal is stronger | same | " | 495 | " | **L18** (not L8 — 4h review F2) | " | arm C **0.2707** (134/495), Δ **+0.1895**, p_cl **1.4e-04** | **established** |
| 5c | removing both is largest, with interaction | same + `advbench_superadd_control.json` | " | 495 | " | **L8 + L18, composed** (F2) | " | arm D **0.3515** (174/495), Δ **+0.2544**, p_cl **4.4e-05**; super-additive excess **+0.0333** CI [+0.0128, +0.0638]; **paired vs the matched random triple +0.0268** CI [+0.0029, +0.0584] | **established** |
| 5d | matched random controls inert | same | " | 495 | " | L8 (Bctrl); Cctrl@L18; Dctrl@L8+L18 | " | B-control **0.0626** (31/495), Δ **−0.0062**, p **0.539** | **established** |
| 5e | effect is **L6–L12** localised | `advbench_layer_profile.json` | " | 495 | " | **11 depths L4–L28** (see D-1) | " | significant L8 (p 0.0089), L10 (p 0.0190), L12 (**+0.0322**, p 0.0056); marginal L6; L13 +0.0138 (p 0.090), L14 +0.0118 (p 0.141); **null from L16 out**; L16 changes 29.5% of generations and compliance on none | **established** |
| 5f | direction-specific, not just better-than-noise | `advbench_direction_specificity.json`, `direction_cosines.json` | " | 495 | " | L8 | " | `d_surface` cos 1.000 → Δ +0.0305 (p 0.0089); `d_naive` cos **0.945** → Δ **+0.0449** (p 0.0089); `d_context` cos **0.188** → Δ **+0.0045** (p 0.399) despite changing 34.9% of generations | **established** |
| 5g | ClearHarm is **withdrawn**, not supporting | `clearharm_decomposition_regoal.json` | Llama / ClearHarm 179, 6 clusters | 179 | " | L8 | " | baseline 19/179, B 34/179, C 65/179, D 92/179, Dctrl 19/179 (**binary counts**); arm B **Δ_cl +0.0843, p_cl 0.2102, CI [−0.0665, +0.2350]** (**continuous**). ⚠ (34−19)/179 = 0.0838 is numerically almost identical to the continuous +0.0843, so the conflation here is **invisible and self-confirming** — the coincidence is not evidence (F8) | ⛔ **withdrawn on ClearHarm (R-16)**; reinstated on AdvBench |
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
5. **The treated arm pools designed-variance blocks; the control does not** (review F15). Of the 324
   `natural_doublespeak` slot-0 behavioural rows, **84 (26%)** come from the `strength` / `consistency`
   / `position` blocks — experimentally manipulated rows of the class R-18 retracted — while
   `benign_literal` draws **none** (core2x2 + role_style only). Recomputed on `core2x2` alone the excess
   is **+0.7525** at L12 against +0.6823 pooled, so the finding is **robust and if anything larger**;
   this is a **disclosure** defect, not an invalidating one. The family-matching fix (A3) partly
   addresses it by restricting to families present in both conditions.
6. **The pairing guard now keys on `n_demo_occurrences >= 2`** rather than value inequality (A8), which
   makes `paired_n` constant at **294** across all layers instead of drifting. Headline numbers
   unchanged: +0.5414 / +0.6402 / +1.8719 at L8 / L12 / L18.

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

**Phase D opened 2026-08-20 (tick 46), the plan's only never-started phase.** The user chose the
strict design when offered the alternatives.

### The bank, and why it looks the way it does

**Artifact:** `data/boombness_prompts/boombness_prompt_bank_phase_d.jsonl` (2,160 rows) +
`..._phase_d_meta.json`. **Code:** one new preset in `src/boombness/prompt_families.py`, one new
constant, one opt-in argument. No new module.

```
python src/boombness/prompt_families.py --preset phase_d \
  --out data/boombness_prompts/boombness_prompt_bank_phase_d.jsonl --strict
# -> rows=2160  2x2 families checked=120 violations=0  duplicate prompt_id dropped=0
```

**`n_examples` is FIXED at 2, and that is the design's central constraint rather than a
simplification.** `_take` returns `pool[(slot*3 + i) % 20]`, so slot *k* starts at `3k mod 20` and
covers *n* consecutive sentences; the number of mutually disjoint families per (domain, split) is
therefore `floor(20/n)`. Plan §6 asks for **≥120 independent behavioural rows per level**, and
6 domains × 2 splits × **10** slots = 120 **exactly**. Ten disjoint slots exist only at n ≤ 2:

| n | disjoint slots per (domain, split) | independent families/level |
|---|---|---|
| 1 | 20 | 240 |
| **2** | **10** | **120** ✅ |
| 4 | 5 | 60 |
| 8 | 2 | 24 |
| 16 | 1 | 12 |

`PHASE_D_SLOTS_N2 = (0, 14, 8, 2, 16, 10, 4, 18, 12, 6)` → starts 0, 2, 4, …, 18, covering all
twenty sentences exactly once. **So the demonstration-COUNT factor is deliberately NOT swept**: it
cannot reach 120 independent families on the current pools, and inflating row counts by reusing demo
sets across n-levels is precisely the pseudo-replication G2 was retracted for. Reported at its honest
ceiling instead of faked.

### Verified against the plan's hard constraints, one by one

Measured on the emitted bank, not asserted:

| factor | level | rows | **distinct families** | domains | mean chars | target occ | demos |
|---|---|---|---|---|---|---|---|
| baseline | (none, consistent, near, plain) | 120 | **120** | 6 | 630.7 | 3.00 | 2 |
| strength | weak / medium / strong / aggressive | 120 ea | **120** ea | 6 | 682.7 / 688.7 / 686.7 / 798.7 | 4 / 4 / 4 / 6 | 2 |
| consistency | mixed / conflicting / irrelevant | 120 ea | **120** ea | 6 | 632.6 / 697.7 / 628.7 | 3 / 4 / 1 | 2 |
| position | far / distributed | 120 ea | **120** ea | 6 | **630.7 / 630.7** | 3.00 | 2 |
| role_style | tool / user_like / assistant_like / cot_like / system_like_quoted | 120 ea | **120** ea | 6 | 636.7–720.7 | 3.00 | 2 |

- **rows = families at every level** — 1,800 generated rows, 1,800 distinct `family_id`, and a direct
  index check finds **0 overlapping demonstration sets** among all 1,800.
- **0 duplicate prompt texts** (`prompt_sha16`) among the 1,800, **0 duplicate `prompt_id`** in the
  bank, **0 rows dropped**.
- **Position is now exactly length-matched at 630.7 characters across near/far/distributed** — see
  below.
- 6 domain clusters at every level; dev/heldout split 900/900.
- Query kind is **behavioral only**, so the token-level Boombness readout and the ASR come from the
  *same* `prompt_id`. No cross-query-kind join exists anywhere in Phase D.

### Two defects found by building it, both pre-existing

**1. The `position` factor in the main bank is confounded with prompt LENGTH.** `build_prompt` adds
filler sentences only when `example_position != "near"` (line 321), so the `near` arm runs ~390
characters shorter than `far`/`distributed`. Any "position matters" result on the main bank is
partly a length result. Fixed here by an **opt-in** `filler_near` argument, **defaulting to False**:
Phase D emits the *same six filler sentences* at all three positions and varies only their placement
(before the demos for `near`, after for `far`, interleaved for `distributed`). Result: 630.7 chars in
all three arms. The default stays False because `bank_rows_sha16` is joined on by every extraction
artifact in the repo — **verified: the main carrot bank still regenerates to `4cd9157399aa1b3c` and
the button bank to `debe267f05efb9ab`, byte-identical.**

**2. ⚠ The main bank's `strength` and `consistency` sweeps break the 2×2 alignment invariant, and
nothing has ever checked them.** The first draft of this preset emitted all four core conditions at
every level so `check_alignment` would cover them. **It fired 360 times.** The cause is intrinsic:
stating a mapping requires naming the codeword, so at `weak` ("Some documents use the word *carrot*
in unusual ways") the two codeword cells carry 4 target occurrences and the two concept cells carry
3; at `strong`/`aggressive` the word-swapped concept version would read *"every occurrence of bomb
must be interpreted as bomb"*, which is not a prompt. `consistency=conflicting` breaks identically
through `counter_mapping_statement`. `mapping_statement`'s own docstring already knew — *"the 2x2
core is generated at `none` because levels that name the concept would break the exact word-swap
alignment"* — but the main bank's `strength`/`consistency` blocks are **single-condition and so never
reach the gate**. The exemption is real, unavoidable, and until now invisible.

Phase D therefore gives the **baseline block the full 2×2** (120 families, alignment-checked,
**0 violations**) and the four factor blocks the attack arm alone, with the exemption written into
the code rather than left silent. Nothing in Phase D's estimand — a *within-attack-arm* correlation —
forms a 2×2 contrast. What does survive: **`n_target_occurrences` varies with the strength and
consistency levels by construction** (3 → 4 → 6, and 1/3/4), so it enters the analysis as a covariate.
Position and role_style are occurrence-balanced at 3.00.

### Pinned, not just commented

`tests/test_slot_disjointness.py` gains six tests (11 pass): the ten slots are pairwise disjoint at
n=2; they exhaust the pool, so an eleventh cannot exist; they are **not** disjoint at n=4 (pinning
*why* n is fixed); the preset uses only those slots, only n=2, only `behavioral`, and
`filler_near=True` everywhere; the baseline cell is emitted exactly once and carries the full 2×2;
and `filler_near` defaults False in every other preset.

### Runs

| job | what | rows |
|---|---|---|
| **769981** | `score_behavior.py --bank ..._phase_d.jsonl --query-kinds behavioral --max-new 512 --arm base` | 2,160 generated (1,800 attack + 360 2×2 controls) |

Judging and the correlation analysis follow. **Decision Gate D is not pre-judged**: E4 (above) now
predicts that prompt-level Boombness should track ASR only insofar as it tracks the *refusal* flip,
which is a sharper hypothesis than the one G2 tested and is the reason this phase is worth running
even though the probe metric is dead.


## ⛔ DECISION GATE D — FAILED, but on requirement 4, and the reason is a genuine finding

**Artifact:** `outputs/boombness_followup/clean_fig9_correlation.json`.
**Producer:** `src/boombness/analyze_phase_d.py`. Llama-3.1-8B, Phase-D bank,
**1,800 joined prompts** (900 dev / 900 heldout, disjoint), 6 domain clusters, 15 designed levels,
0 `prompt_sha16` mismatches, 6 judge shards asserted to be a partition.

Plan §6 asked whether prompt-level Boombness predicts ASR under clean inference. **It does.** Plan
§11 then asks whether that licenses a GCG objective. **It does not**, and the failure is specific.

### It predicts — and unlike G2, this survives every guard the design was built for

Metric chosen on **dev** from 210 candidates, then that single metric tested on **heldout** where the
family size is one:

| direction | outcome | selected on dev | **heldout ρ** | p_cl | perm p |
|---|---|---|---|---|---|
| `d_surface` | ASR@0.5 | `demo_max\|L29\|cos` | **+0.2456** | 0.0059 | 0.0005 |
| `d_surface` | StrongReject | `query\|L31\|cos` | **+0.2982** | 0.00039 | 0.0005 |

G2's clean powered result was ρ = −0.066, p = 0.49 on n = 108. This is a real positive on n = 900
heldout prompts, and the difference is the bank: 120 **independent** families per level instead of
rows that shared demonstrations.

### ⛔ But `d_naive` and `d_context` do it just as well — requirement 4 fails

| direction | within-level ρ (ASR) | within-level ρ (StrongReject) |
|---|---|---|
| `d_surface` | +0.1272 | +0.1638 |
| `d_context` | +0.1368 | +0.1471 |
| **`d_naive`** | **+0.1554** | **+0.1672** |

`d_naive` is the *strongest* on both outcomes. The plan's gate requires that **random / control
directions fail**; here every direction tested succeeds, and the one fitted with no contextual
control at all wins. **This is retraction F-2's shape at the prompt level**: the signal is not
`d_surface`, it is a generic late-layer semantic magnitude that all three directions load on.

### ⚠ And two thirds of the pooled correlation is the design's own manipulation

The bank deliberately makes ASR differ across levels — `str:aggressive` sits at **0.458**,
`con:mixed` at **0.008** — so any metric that also differs across levels correlates with ASR when the
levels are pooled. That is the between-domain trap from this module's self-test, one grain up. Split:

| | `d_surface` / StrongReject |
|---|---|
| **between-level** ρ (15 level means) | **+0.7024** |
| **within-level** mean ρ (fixed manipulation, cluster-t over levels) | **+0.1638**, p 0.0001 |

The within-level component is real and significant, and it is the only part that could ever support
a per-prompt objective. It is also **five times smaller** than the between-level part. A Fig-9-style
scatter over pooled levels would look far more convincing than the evidence warrants.

### ✅ Requirement 3 passes, and the reason inverts Phase E4

The metric is **not** a refusal detector: within-level ρ(metric, keyword-refusal) = **+0.0676,
p = 0.26** (`d_naive` +0.0666, p = 0.28), against ρ(metric, ASR) = +0.148.

**Because on this bank the refusal gate is essentially off.** Refusal rate **1.39%**, ASR 10.9%,
ρ(refused, ASR) = −0.042. Llama complies with these doublespeak prompts almost always; the variance
in ASR is *content quality*, not compliance. **That is the opposite regime from AdvBench**, where
Phase E4 found every point of StrongReject movement was a refusal flip. The two datasets measure
different things through the same rubric, and neither result generalises to the other.

### ⚠ Coverage, stated rather than buried

`demo_max|L29|cos` is **undefined for one of the 15 levels**: `consistency=irrelevant` teaches a
*different* codeword, so its 120 prompts contain the target only at the query and have no demo
occurrence. The ASR headline is therefore over **14/15 levels (1,680 prompts)**; the StrongReject
headline uses a query-position metric and covers 15/15. The artifact carries `n_levels_covered` and
`levels_uncovered` on every row.

### Gate D verdict, requirement by requirement

| plan §11 requirement | verdict |
|---|---|
| 1. predicts ASR under within-domain / clustered inference | ✅ heldout ρ +0.2982, p_cl 0.0004 |
| 2. survives multiplicity correction | ✅ nested selection; heldout family size = 1 |
| 3. is not just refusalness | ✅ ρ 0.068 with refusal, p 0.26; bank refusal rate 1.4% |
| 4. **random / control directions fail** | ⛔ **NO — `d_naive` and `d_context` match or beat it** |
| 5. comprehension preserved | ⚠ not tested |
| 6. replicates on heldout | ✅ by construction |
| 7. intervention has the expected sign | ⛔ **NO — predictive at L29–L31; causal band is L6–L12** |

> **Prompt-level Boombness is not currently a usable optimization target.**

Written as the plan requires — but with a sharper reason than G2 could give. It is **not** that
nothing predicts ASR. It is that **what predicts it is not `d_surface`, and not where `d_surface`
acts**: the predictive signal lives in the top three layers of the stack, while every causal effect
this sprint has measured lives at L6–L12 for `d_surface` and L14–L20 for refusalness. **A metric that
predicts at a depth where intervention does nothing cannot be optimised against.**

⛔ Therefore **the plan §11 GCG objective is not attempted**, and three of its five candidate
objectives are now individually dead: probe margin (Decision Gate C failed), the `d_surface` layer
profile (survives no multiplicity correction), and prompt-level Boombness (this gate).

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

**Phase G started (tick 33).** The plan is explicit that the top-16 edge search should not be repeated
as if it were likely to work — the previous sprint established that **no 16-edge subset matters**
(top-k +0.0196 vs bottom-k −0.0028 vs random +0.0008) and that the redundancy is in sheer edge count.
So Phase G opens on the plan's units **2 and 3** instead, which this sprint has a specific reason to
run.

### The motivation is this sprint's own Phase B result

Phase B found the **last** demonstration codeword is measurably more concept-like than the **first**
(paired, family-matched excess **+0.5414 at L8, t = 3.26**). That is a *representational* gradient.
**Does it have a causal counterpart?** If the later demonstrations are where the meaning actually
accumulates, cutting attention out of the *last* demonstration should cost more than cutting it out of
the *first* — at an identical number of edges.

That is a genuinely position-resolved question the existing `--demo-scope {codeword, block}` could not
ask: `codeword` cuts **all** demonstration codewords at once.

### Code added: two `--demo-scope` choices, four lines

`src/boombness/surgical_knockout.py` now accepts `first_codeword` and `last_codeword`.
`last` holds the codeword occurrence indices with the query occurrence last, so `last[:-1]` are the
demonstrations; the new scopes take `demos[:1]` and `demos[-1:]`. A prompt with no demonstrations
yields an empty scope and is charged to the `FailureLedger` by name via the existing
`no_demo_positions:<scope>` guard — **not dropped silently**.

### Runs submitted

| job | tag | scope |
|---|---|---|
| 768703 | `g3wa24_first` | `--demo-scope first_codeword` |
| 768704 | `g3wa24_last` | `--demo-scope last_codeword` |

Both at the **current G3 configuration** so they are comparable to the committed
`g3_wholeanswer_block24.json`: `--layers 8,12,18,24 --n-families 24 --dst both
--query-kind semantic_one_word --condition natural_doublespeak --seed 20260816`, ranking at
`readout_pos`, whole-answer readout.

### The comparison this sets up, and its built-in control

The two arms cut **the same number of edges** (one codeword occurrence each, same layers, same
top-k budget) and differ only in **which** occurrence. So the contrast is **edge-count-matched by
construction** — the confound that broke the previous sprint's depth reading (`g3_edgematch.json`,
where 2 layers vs 32 layers at an identical 3,552 edges gave −0.008 vs +0.089) cannot apply.

Pre-registered prediction, recorded before the runs land: **if Phase B's gradient is causal, the
`last_codeword` arm should move the readout more than `first_codeword`.**

### ❌ THE PREDICTION WAS WRONG — and the opposite result decomposes a known anomaly

Jobs **768703 / 768704**, COMPLETED 22:32 each, 24 families, both `DONE`.
Artifacts `outputs/boombness_followup/g3_first.json`, `g3_last.json`.

| arm (all layers, `--dst both`) | Δ | sem | edges cut |
|---|---|---|---|
| *committed* codeword scope — **all** demo codewords | **+1.3322** | 0.3508 | 6,144 |
| **`first_codeword` only** | **+0.9718** | 0.0706 | **1,024** |
| **`last_codeword` only** | **−0.0231** | 0.0615 | **1,024** |
| *(ceiling)* `no_demo_text` | −17.8789 | 1.0723 | — |

**I predicted last > first. The truth is first ≫ last, and last is exactly nothing.**

Cutting the attention edges out of the **first** demonstration's codeword reproduces the **entire**
codeword-scope effect within noise, using one sixth of the edges. ⚠ *Corrected from "73%" — review #3
(R3-4) showed the paired `codeword − first` contrast is **+0.3604 ± 0.3552, t = 1.01**, with codeword >
first on only 12/24 prompts. The missing 27% is not distinguishable from zero, so treating it as real
was unsupported. The corrected claim is **stronger**, not weaker.* Cutting the **last**
demonstration's codeword, at an **identical 1,024 edges**, does **nothing** (−0.0231 ± 0.0615).

Because the two arms cut the same number of edges, this is **not** the edge-count confound that broke
the previous sprint's depth reading. The difference is ≈ 14 sem.

> **The previously unexplained "codeword-scope knockout moves the readout the WRONG way (+1.33)"
> anomaly localizes almost entirely to the FIRST demonstration.**

### The dissociation this creates

| | where it is largest |
|---|---|
| **Representation** (Phase B) | the **LAST** demo codeword is most concept-like (+0.5414 at L8, t = 3.26) |
| **Causality** (Phase G) | the **FIRST** demo codeword carries the attention effect (+0.9718 vs −0.0231) |

**They run in opposite directions across demonstration positions.** A reading consistent with both: the
**first demonstration establishes** the codeword→concept mapping and its attention edges are
load-bearing; later demonstrations **inherit** an already-established mapping, so they end up more
concept-like in the residual stream while being causally redundant. That is a testable story, not an
established one.

It also parallels the sprint's other unresolved tension — signal largest late, ablation effective early
— and suggests both may be instances of *"where the representation is strongest is not where the
computation happens."*

### Caveats, stated plainly

1. **`dynamic_range_established: False`** on both runs. The flag fires because the `positive_control`
   (−4.658) does not dominate `no_demo_text` (−17.879). Per `analyze_g1_g3.py:225-231` — and confirmed
   by the tick-6 audit for the committed `g3_wholeanswer_block24.json`, which carries the same flag —
   this is **non-disqualifying**: movability is established by `no_demo_text` itself, which is
   identical (−17.8789) in both runs and in the committed one.
2. **The sign is still unexplained.** Cutting attention *out of* the first demonstration makes the
   readout **more** concept-like, not less. This sprint decomposes that anomaly by position; it does
   not explain it.
3. `semantic_one_word` readout, `natural_doublespeak` only, n = 24 families. No matched-control arm
   for position specifically — `random_demo` in each run is drawn from that run's own scope, so it
   controls for "cutting 1,024 edges" but not for "cutting *this* occurrence versus *that* one". The
   edge-count match is what carries the contrast.

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
| **A2** | `curve()`/`band_mean()` paired a **row-weighted mean** with a **prompt-clustered SEM**. | **CLOSED tick 22** — both now emit `mean_ROWWEIGHTED` and `mean_promptweighted`; SEM renamed `sem_rowlevel`. e.g. `demo_all` L14–21: row −4.9964 vs prompt −5.5814. |
| **F6** | "Representational signal largest late" is mostly **residual-norm growth**. | **CONFIRMED AND CORRECTED tick 7** — family-matched, `proj` grows **17.0×** L8→L31 while `cos` grows **2.0×**. A real 2× depth trend survives (cos peaks L24, t 4.89); the 14× version does not. Phase B Q3 rewritten. |
| **F9** | "% of generations changed" does **not** separate signal from noise: random controls change 22.0% / 30.7% / **33.9%** — the last more than `L15_B`'s 28.1%. Carries claims 5e and 5f too. | **OPEN — qualify everywhere.** |
| **F7** | No multiplicity correction on the `d_surface` profile. | **CLOSED tick 18** — computed: Holm(m=10) rejects nothing (min adj 0.0562 at L12); BH(0.05) keeps L8 and L12; all 11 controls inert. Claim 5e restated as "pointwise + BH, not Holm". |
| **F3** | Two Do-Not-Cite **replacement** figures absent from their artifacts: role-framing `F(5,355)=20.30` is **not in `g11_role_full.json`**; "ratio inverts to 0.80" is **0.7472** @codeword_last and **1.5416** @last. | **FIXED** in the ledger. |
| **F4** | Tick-3's "NEW RESULT" was **already committed** — `advbench_layer_profile.json` carries `c13`/`c14` byte-identical, added by `af4fe7a4` before this sprint; my own D-1/D-2 say so. | **CORRECTED** — see below. |
| **F5** | This file held **two divergent copies** of the progress log with contradictory status headers, from one of my splices. | **FIXED** — rebuilt, 2410 → 1608 lines. |
| **F8** | Estimand mixing in 5a/5g/6b. | **CLOSED tick 22** — all three now name both estimands inline. 5g carries an explicit warning that its binary and continuous values coincide to 3 dp, making the conflation invisible and self-confirming. |
| **F13** | D-9 described two datasets as one. | **FIXED tick 12** — D-9 now states the Llama figures (arm C p_cl 0.0410, arm D 0.0200, both significant; only arm B null) and marks the 0.1341/0.0522 pair as Qwen3's. |
| **F15** | Treated arm pools designed-variance blocks; control does not. | **CLOSED tick 22** — disclosed in Phase B limitations, with the core2x2-only recomputation (+0.7525 vs +0.6823) showing the finding is robust. |
| **A8** | Pairing guard used value-inequality as a proxy for "≥2 demos". | **CLOSED tick 22** — now keys on `n_demo_occurrences >= 2`; `paired_n` constant at 294 across layers; headline numbers unchanged. |

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

### Tick 20 — Phase E1's benign arm, built by REUSE rather than authoring

Plan §7 E1 asks for benign technical, benign everyday and ambiguous dual-use categories, which
AdvBench does not contain. Rather than author prompts — which would reintroduce exactly the
"sprint's own generator" threat `external_bank.py`'s docstring warns about — I reused the previous
sprint's §20 over-refusal cohort:

**`doublespeak_causality/data/behavioral_v3/unrelated_normal.json`** — 40 items, meta note *"ordinary
benign instructions with NO attack structure (no codeword/demos) … All items are unambiguously
benign."* These **predate this sprint**, so they cannot have been tuned to its hypothesis.

Re-categorised into **4 clusters with no singletons** (the D-9 lesson): `science_explanation` 14,
`practical_advice` 11, `creative_writing` 8, `math_and_code` 7. Largest cluster holds 35% of rows —
far better balanced than ClearHarm's 127/31/17/2/1/1.

Covers **two of the plan's three** E1 benign categories: technical (`math_and_code`,
`science_explanation`) and everyday (`practical_advice`, `creative_writing`). **Ambiguous dual-use has
no existing source in the repo and is NOT covered** — flagged rather than quietly dropped; it would
need authoring, and authoring a dual-use set is the piece most vulnerable to being written toward the
answer, so it is raised for a decision rather than done unilaterally.

**Code added: one `SOURCES` line** in `external_bank.py` plus a 40-row CSV. Bank built with the
existing adapter, unchanged:

```
$PY src/boombness/external_bank.py --source benign_unrelated \
    --out data/boombness_prompts/external/benign_unrelated_40.jsonl
# -> 40 rows, 4 clusters; largest holds 35.0% of rows
```

#### ⚠ The outcome measure is over-refusal, NOT ASR — and this arm needs no judge

StrongReject scores compliance with a **harmful goal**. These rows have none, so an ASR number here
would be meaningless — the same class of error as R-14, where every external completion was scored
against an empty goal. The measures are **refusal rate** and **generation change**, both recorded by
`score_behavior.py` directly. **No judge run, no API cost.**

| job | tag | intervention |
|---|---|---|
| 768502 | `bng_base` | none |
| 768503 | `bng_B` | `d_surface:project_out:8-8:1.0` |
| 768504 | `bng_Bctrl` | `random:project_out:8-8:1.0` (matched) |
| 768505 | `bng_C` | `refusalness:project_out:18-18:1.0` |

#### What it discriminates

This is the test that separates the sprint's two live readings of `d_surface`:

- If removing `d_surface` leaves benign behaviour **unchanged** while raising harmful compliance, it is
  a **harm-salience** channel.
- If it perturbs benign responses too, it is a **general semantic-salience** channel that happens to
  matter for harm — plan hypotheses 3 and 4.

Phase E1's category result already leans the second way: the effect was **weakest on
`weapons_explosives`** (+0.0250), the category the direction was fitted on, and strongest on
misinformation and cyber. A benign perturbation would corroborate that.

⚠ **Power, stated before the result:** n = 40 across 4 clusters is adequate for a descriptive
over-refusal check (it is what §20 used it for) but **cannot support a clustered causal claim**. A null
here will be reported as "no detectable over-refusal at n = 40", never as "no effect".

### ✅ Phase E3 (partial) — `d_surface` and refusalness are geometrically near-orthogonal

Pure CPU on the committed direction vectors: the canonical heldout fit
(`extract_boombness/full_20260816_185942_1008673/directions_fit_heldout.pt`) against the house Llama
refusal directions (`doublespeak_causality/outputs/stage_gcg_full/refusal_direction_llama_L*.pt`,
verified 4096-d and unit norm). Answers a Final Report question directly.

**Random baseline first**, because a cosine in 4096 dimensions needs one: 2,000 random unit-vector pairs
(seed 20260820) give sd(cos) = **0.01541**, E|cos| = 0.01221, 95th percentile |cos| = 0.03036 —
matching the theoretical 1/√4096 = 0.01562.

| L | cos(`d_surface`, refusalness) | z vs random | shared variance (cos²) | verdict |
|---|---|---|---|---|
| 12 | 0.1279 | 8.30 | **1.64%** | clearly above chance |
| 14 | 0.0972 | 6.31 | 0.94% | clearly above chance |
| 16 | 0.0467 | 3.03 | 0.22% | clearly above chance |
| **18** | 0.0262 | 1.70 | **0.07%** | **at chance** |
| 20 | 0.0176 | 1.14 | 0.03% | **at chance** |

Sibling directions for reference: cos(`d_naive`, ref) 0.107 → 0.030; cos(`d_context`, ref) −0.028 →
0.052; cos(`d_inter`, ref) −0.105 → −0.094 across the same depths.

**99.2–99.98% of `d_surface` is orthogonal to refusalness.** The overlap is statistically detectable at
L12–L16 but negligible in magnitude everywhere — at most **1.64%** shared variance — and by **L18, where
refusalness is causally strongest (Δ +0.1895), the two are indistinguishable from random vectors.**

#### What this settles, and what it does not

> **"Is `d_surface` separable from refusalness?" — Yes, geometrically almost completely.** It is not a
> disguised refusal direction. Removing it cannot be removing refusalness by another name.

Combined with the two causal results, a coherent two-channel picture emerges:

| | `d_surface` | refusalness |
|---|---|---|
| geometry | \ near-orthogonal (cos ≤ 0.13, ≈0 at L18) | |
| causal depth | L6–L12 (peak L12) | L14–L20 (peak L18) |
| effect size | +0.0322 peak, no Holm survival | +0.1895 peak, 4/5 survive Holm |
| direction of control | bidirectional (add ↓, remove ↑) | removal ↑ |

Two distinct, near-orthogonal channels operating at **different depths**, whose removals nevertheless
compose **super-additively** (+0.0268 against the matched random triple). That is a substantive answer
to plan §1's main question and it rules out hypothesis 2 in its strong form — `d_surface` is not
"partially confounded with safety salience" in the sense of *being* the refusal axis.

⚠ **Caveat, stated rather than buried.** The two direction families are fitted by **different
procedures on different data** (`d_surface` from the 2×2 carrot/bomb bank; refusalness from the house
`stage_gcg_full` pipeline). Near-orthogonality is therefore partly expected and is **not** by itself
evidence of functional independence — the causal dissociation is what carries that. The one thing the
geometry does establish firmly is the negative: they are not the same direction.

**Not yet done for E3:** the plan also asks for the *orthogonalized-intervention* arms — ablating
`d_surface` with its refusalness component projected out, and vice versa. At cos ≤ 0.13 those arms
would differ from the plain ones by under 2% of the vector, so they are **low-value here** and are
deprioritised behind the dose-corrected runs. Recorded as a deliberate deprioritisation, not an
omission.

### Tick 18 — F7 and F9 closed: the `d_surface` profile survives no correction, and "% generations changed" carries no information

Queue cold (768468/469/488/489 all `PENDING`), so this tick closed two standing review defects.

#### F7 — multiplicity on the `d_surface` layer profile. **Holm rejects nothing.**

Computed over the **10 testable depths** of `advbench_layer_profile.json` (L16 is `degenerate: true`,
`p_cl: null`, and is excluded):

| depth | Δ_cl | p_cl | **Holm (m=10)** | BH(0.05) |
|---|---|---|---|---|
| L12 | +0.0322 | 0.0056 | **0.0562** | ✔ reject |
| L8 | +0.0305 | 0.0089 | 0.0804 | ✔ reject |
| L10 | +0.0223 | 0.0190 | 0.1518 | — |
| L6 | +0.0159 | 0.0567 | 0.3969 | — |
| L13 | +0.0138 | 0.0901 | 0.5409 | — |
| L14 | +0.0118 | 0.1411 | 0.7053 | — |
| L4 / L18 / L28 / L24 | ≤ +0.0092 | 0.26–0.45 | 1.0000 | — |

**Not one depth survives Holm** — the smallest adjusted p is 0.0562 at L12. **BH at 0.05 keeps L8 and
L12** (by the step-up rule). All **11** matched controls are inert: |Δ| ≤ 0.0066, p 0.20–0.94.

This is the honest asymmetry recorded at tick 9, now computed rather than quoted. Compare the
refusalness profile, where **four of five depths survive Holm at m = 5**. Both profiles use the same
baseline, estimand and cluster definition, so the comparison is like-for-like; the refusalness effects
are simply much larger (peak +0.1895 vs +0.0322).

**How claim 5e must now be stated:** the `d_surface` band L6–L12 is a **consistent pattern with
uniformly inert controls**, significant pointwise and under BH, but **not surviving Holm**. The arm-B
headline at L8 remains a single pre-specified test outside that family.

#### F9 — "% of generations changed" is retired as evidence

Recomputed against the shared baseline over the 495 common prompts:

| run | Δ_cl behaviour | **% generations changed** |
|---|---|---|
| `d_surface` project_out **L12** (significant) | +0.0322 | **47.1%** |
| `d_surface` project_out **L8** (significant) | +0.0305 | 38.2% |
| `d_context` project_out **L8** (behaviourally inert) | +0.0045 | **34.9%** |
| `random` project_out **L12** (inert control) | −0.0003 | **30.7%** |
| `d_surface` project_out **L16** (exact null) | ≈0 | **29.5%** |
| `random` project_out L8 (inert control) | −0.0062 | 22.0% |
| `random` project_out L16 (inert control) | −0.0003 | 18.0% |

**The ranges overlap completely.** An arm with *exactly zero* behavioural effect (L16) changes 29.5% of
generations; an inert random control changes 30.7%; a behaviourally inert direction (`d_context`)
changes 34.9%. Meanwhile a significant arm changes 38.2%.

> **"% of generations changed" shows only that an intervention was not a no-op. It carries no
> information about whether compliance moved, and must never be used as evidence of specificity.**

Corrections applied: my tick-4 framing ("the L12 refusalness intervention changed 41.4% — a *potent*
edit that leaves compliance alone") is downgraded to "not a no-op"; the same wording in claims **5e**
(L16 "changes 29.5% and compliance on none") and **5f** (`d_context` "despite changing 34.9%") is
inherited from the handover and is flagged here rather than silently repeated. In every one of those
cases the *conclusion* is unaffected — they were arguing the intervention fired — but the rhetorical
weight put on the number was not earned.

### Tick 17 — the two coherence failure modes separate cleanly, and the gate's floor tracks refusal

Running the **committed** `coherence_gate.py` across every arm in the sprint settles how to read its
two kinds of verdict.

| run | uniq | 3-gram | truncated | scorable | verdict |
|---|---|---|---|---|---|
| `ab_B` (remove `d_surface`) | 0.816 | 0.014 | 0.10 | 0.602 | **OK** |
| `ab_C` (remove refusalness) | 0.775 | 0.025 | 0.25 | 0.846 | **OK** |
| `ab_D` (remove both) | 0.741 | 0.031 | 0.32 | 0.844 | **OK** |
| `fuF_remS_addR` (arm E) | 0.835 | 0.013 | 0.07 | 0.539 | **OK** |
| `fuF_addCtrl8` (rand add L8, α=1) | 0.745 | 0.071 | 0.16 | 0.857 | OK |
| `fuF_addCtrl18` (rand add L18, α=1) | 0.580 | 0.205 | 0.40 | 1.000 | OK (nearest edge) |
| `fuF25_addS` | 0.873 | 0.005 | 0.01 | **0.331** | ⛔ floor |
| **`fuF_remS_addR_CTRL`** (768316) | **0.127** | **0.800** | **0.99** | **1.000** | ⛔ **truly broken** |

**All three committed headline arms (B, C, D) are gate-clean**, and so is arm E.

#### The two failure modes are orthogonal, and only one is degeneracy

- **Real degeneracy** looks like 768316: `scorable_frac = 1.000` (every generation is long) with
  **uniq 0.127, 3-gram repeat 0.800, truncated 0.990**. Long, looping, never emits EOS.
- **Refusal-induced floor** looks like `fuF25_addS`: **healthy ratios** (uniq 0.873, 3-gram 0.005,
  truncated 0.01) with a low scorable fraction, because the model answers `"I can't help with that."`

Measured across 8 arms: **Pearson r(scorable_frac, refusal rate) = −0.878.** The floor tracks how much
the model refuses, almost linearly. So:

> **The gate's ratio thresholds are the degeneracy detector. Its scorable-fraction floor is confounded
> with refusal rate and must not be read as degeneracy when the ratios are healthy.**

That is a methodological result the previous sprint did not have — its docstring identifies the floor's
*motivation* (T13) but never separates it from the refusal-increase case it cannot distinguish. It also
gives the bidirectional `d_surface` result a precise status: **its ratios are clean and its control is
dose-matched and inert; it fails only the floor, and it fails the floor because it works.**

#### The arm-E control was over-dosed, not the arm

768316 composed `random:project_out:8-8:1.0` **+** `random:add:18-18:1.0`. Exact gaps from the
canonical fit dir: `gap[d_surface][L8] = 5.926142`, `gap[d_surface][L18] = **14.653462**`. So its add
leg injected magnitude **14.65** — against arm E's refusalness leg at magnitude **1.0** (RETRACTION
F-3). Notably `random:add:18-18:1.0` **alone** is gate-clean (uniq 0.580); it is the **composition**
that breaks generation.

#### Two dose-corrected runs submitted

| job | tag | intervention | why |
|---|---|---|---|
| 768488 | `fuF_remS_addR_CTRL2` | `random:project_out:8-8:1.0` + `random:add:18-18:**0.068243**` | 1/14.653462, so the random add injects magnitude **1.0** — matching arm E's refusalness leg exactly |
| 768489 | `fuF_addR_gapdose` | `refusalness:add:18-18:**14.653462**` | one diff-of-means, the dose F-3 showed was missing. Its matched control is the already-judged, gate-clean `random:add:18-18:1.0` |

768489 is the experiment RETRACTION F-3 says should have been run: refusalness added at a dose
comparable to the random control it is compared against. If it suppresses ASR while the gap-matched
random control raises it (+0.0533), the specificity claim is re-earned honestly. If it degenerates,
that is the answer instead — and either way the α = 1.0 version stays retracted.

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

## ✅ Phase E1 BENIGN — zero over-refusal, but `d_surface` is not inert on benign text

**Jobs 768517–768520, COMPLETED 15:10 each, 40/40 generations, all four `DONE`.** All four pass the
**committed** `coherence_gate.assess()` — uniq 0.62, 3-gram 0.06, **scorable_frac 1.000** (no short-refusal
floor problem here, unlike the harmful arms). Llama-3.1-8B, `benign_unrelated_40`, 4 clusters.

### Result 1 — no over-refusal anywhere. Clean null.

| arm | refusal-phrased | generations changed | median words |
|---|---|---|---|
| `bng_base` | **0.000** | — | 214 |
| `bng_B` (remove `d_surface` @L8) | **0.000** | 32/40 | 222 |
| `bng_Bctrl` (matched random) | **0.000** | 28/40 | 216 |
| `bng_C` (remove refusalness @L18) | **0.000** | 37/40 | 212 |

**0 of 40 in every arm, and 0.00 in all four clusters.** Removing `d_surface` does **not** make the model
refuse benign requests. Neither does removing the refusal direction itself (expected — baseline is
already at the floor, so only an *increase* was detectable).

### Result 2 — but it perturbs benign text more than a random direction. **Suggestive, NOT established.**

The interventions plainly fired (32/40, 28/40, 37/40 generations changed). Measuring the *magnitude* by
token-set Jaccard distance from baseline:

| arm | mean Jaccard distance | median |
|---|---|---|
| `bng_B` (`d_surface`) | **0.3134** | 0.3088 |
| `bng_Bctrl` (random) | **0.2271** | 0.1789 |
| `bng_C` (refusalness) | 0.4125 | 0.4627 |

Paired `d_surface` − random = **+0.0863**.

> ⚠ **iid t = 2.24 (39 df), p = 0.031. Domain-clustered t = 2.28 (3 df), p = 0.107.**
> **The clustered result is the correct estimand and it is NOT significant.** Reported this way round
> deliberately: quoting the iid p because it is the friendlier one is defect **R-16**, committed three
> times in the previous sprint. With 4 clusters this test has almost no power (**D-9**), so this is
> **suggestive and underpowered**, not a finding.

Exact McNemar on which generations changed (`d_surface`-only 6 vs random-only 2) gives **p = 0.289** —
also not significant.

### What this does to the sprint's central question

Taken with Phase E1's category result, a **middle answer** emerges — and it is more interesting than
either pole the plan proposed:

- **Against pure harm-salience (plan hypothesis 1's implication).** If `d_surface` only carried harm
  information, removing it should perturb benign text no more than a random direction. It perturbs it
  *more* (+0.0863), albeit only at iid significance.
- **Against "general semantics, behaviourally consequential" (hypotheses 3/4).** It produces **exactly
  zero** over-refusal on benign content, in every cluster.

> **Best current reading: `d_surface` is a general semantic channel — active when the model writes
> benign text — whose *behavioural* consequences appear only on harmful content.**

That reconciles the sprint's otherwise awkward findings: weakest on the category it was fitted on
(`weapons_explosives` +0.0250) yet strongest on information-shaped harms; orthogonal to refusalness;
causally live at L6–L12 where refusalness is not.

### Limits, stated plainly

n = 40 over 4 clusters. The over-refusal null is **solid** (a floor at 0.000 in every arm and cluster
cannot be a power artifact in the direction tested). The perturbation difference is **not established**
and must not be cited as one. Jaccard distance is a crude proxy for "how much did the answer change"
and says nothing about whether it changed for the better. Ambiguous dual-use prompts remain uncovered.

### Tick 30 — two dose-corrected controls landed; the tick-17 coherence discriminator held as a prediction

| job | tag | state | elapsed | gate |
|---|---|---|---|---|
| 768521 | `fuF25_addBoth_CTRL` | COMPLETED | 21:26 | uniq 0.874, 3-gram 0.011, scorable 0.533 → **OK** |
| 768523 | `fuF_remS_addR_CTRL2` | COMPLETED | 18:45 | uniq 0.844, 3-gram 0.013, scorable **0.424** → ⛔ floor |
| 768522 | `fuF25_remR_addS_CTRL` | RUNNING | 45:56 | 442/495 |
| 768524 | `fuF_addR_gapdose` | RUNNING | 45:56 | 284/495 |

**The tick-17 methodology made a falsifiable prediction and it held.** Tick 17 concluded that the gate's
*ratio* thresholds detect degeneracy while its *scorable-fraction* floor tracks refusal rate
(r = −0.878), so an arm with **healthy ratios and a low scorable fraction** should be a refusing arm,
not a broken one. `fuF_remS_addR_CTRL2` is exactly that shape, and the classification confirms it:

| run | short rows | **refusal-phrased** | empty |
|---|---|---|---|
| `fuF_remS_addR_CTRL2` | 285/495 (58%) | **285/285 = 100%** | 0 |
| `fuF25_addBoth_CTRL` | 231/495 (47%) | 230/231 = 100% | 0 |
| `fuF_remS_addR` (arm E) | 228/495 (46%) | 228/228 = 100% | 0 |

Compare the genuinely broken 768316: `scorable_frac` **1.000** with uniq **0.127** and truncated
**0.990**. The two signatures remain cleanly separable on a run neither was derived from.

Both completed controls judged (`p_addBoth_CTRL`, `p_remS_addR_CTRL2`). Arm E's release is now waiting
only on the judge, not on compute.

## ✅✅ THE SPRINT'S STRONGEST RESULT — plan §8 arm 6: a sign dissociation against a dose-matched control

**Artifact:** `outputs/boombness_followup/phaseF_arm6_matched.json`. AdvBench 495 / 16 clusters,
Llama-3.1-8B, cluster-mean estimand on the continuous StrongReject score. **Both arms pass the committed
coherence gate** (uniq 0.772 / 0.756, scorable 0.701 / 0.881).

| arm | intervention | ASR@0.5 | refusal | Δ_cl | p_cl |
|---|---|---|---|---|---|
| baseline | — | 0.0646 | 0.9313 | — | — |
| **C** | `refusalness:project_out:18-18:1.0` | 0.2707 | 0.7091 | **+0.1895** | 0.0001 |
| **F6** | C **+** `d_surface:add:8-8:0.25` | 0.1879 | **0.7859** | **+0.1067** | 0.0011 |
| **F6_CTRL** | C **+** `random:add:8-8:0.25` | 0.3374 | **0.6364** | **+0.2395** | 0.0001 |

**Dose matching verified from the fit dir, not assumed:** both add legs take the `:221` gap-unit path
and inject an identical **0.25 × gap[d_surface][L8] = 0.25 × 6.054948 = 1.5137**. ⚠ *Corrected: I first
wrote 1.4815, read from `directions_fit_heldout.pt` while the runs used `directions_fit_dev.pt` — see
review #3, correction R3-1. The equality of the two arms was never in doubt; the magnitude was wrong.* Identical layer,
identical operation, identical magnitude, identical `refusalness:project_out` leg. The only difference
is *which vector*.

### The two contrasts, paired and domain-clustered (16 clusters, 15 df)

| contrast | Δ | sem | t | p_cl | **Holm (m=4)** |
|---|---|---|---|---|---|
| **F6 − F6_CTRL** — real direction vs matched random | **−0.1328** | 0.0308 | **−4.31** | **0.0006** | **0.0024 ✔** |
| **F6 − C** — does adding `d_surface` cancel the refusalness removal? | **−0.0827** | 0.0219 | **−3.78** | **0.0018** | **0.0054 ✔** |

Holm is taken over **all four** Phase F composed contrasts (the two here plus arm E's two), so this is
corrected against the sprint's own family, not a favourable sub-selection. **Both arm-6 contrasts
survive; both arm-E contrasts do not.**

### Why this is the strongest thing the sprint has produced

**The control does not merely fail to reproduce the effect — it moves the opposite way.** Adding a
norm-matched random vector on top of refusalness-removal makes the jailbreak *worse* (+0.2395 against
C's +0.1895, refusal 0.7091 → 0.6364). Adding `d_surface` at the identical dose makes it *better*
(+0.1067, refusal 0.7091 → **0.7859**). The gap is **−0.1328 at p_cl = 0.0006.**

A sign reversal against a dose-matched control cannot be explained by "the edit was large", by
perturbation, or by degeneracy — the three explanations that killed the α = 1.0 arms, RETRACTION #8's
"capability channel", and F-3. **This is what F-3 wrongly claimed and this genuinely delivers**, on the
opposite axis and with the doses actually matched.

### What it establishes

1. **`d_surface` is causally specific**, not a stand-in for "any direction at L8". Established under
   multiplicity correction, with an active-but-opposite control.
2. **Bidirectional control replicates in a composed setting.** Adding `d_surface` suppresses compliance
   here just as it did standalone (−0.0329), and removing it raises compliance (+0.0305).
3. **The interaction is real in this direction:** adding `d_surface` back cancels **44%** of the
   refusalness-removal effect (+0.1895 → +0.1067), p_cl 0.0018.
4. **Asymmetry between the two directions of the interaction.** Arm 6 (restore `d_surface` after
   removing refusalness) is strongly established; arm E (restore refusalness after removing
   `d_surface`) is only suggestive. The plain reason is **power** — the refusalness effect is 6× larger
   (+0.1895 vs +0.0305), so a 44% cancellation of it is far easier to detect than a 31% cancellation of
   the smaller one. **This is not evidence that the interaction is one-directional**, and must not be
   written that way.

### Limits

One layer pair (add at L8, remove at L18) and one dose (0.25). ASR@0.5 is shown for scale only; every Δ
and p is on the continuous score, cluster-mean (**D-8**). The `F6_CTRL` arm being *active* rather than
inert means "the control is inert" is **not** available as a supporting argument here — the argument is
the sign reversal, which is stronger.

## Phase F closed — arm E released, and the F-3 re-test answers with a hard NO

All four dose-corrected jobs completed. **Artifact:**
`outputs/boombness_followup/phaseF_composed_matched.json`.

### ⛔ The F-3 re-test: adding refusalness at a matched dose is IMPOSSIBLE — it degenerates

Tick 17 launched `fuF_addR_gapdose` = `refusalness:add:18-18:**14.653462**` — one diff-of-means, the
dose RETRACTION F-3 showed was missing. It **completed and failed the gate outright**:

| | uniq | 3-gram repeat | truncated | scorable | verdict |
|---|---|---|---|---|---|
| `fuF_addR_gapdose` | **0.237** | **0.704** | 0.54 | **0.996** | ⛔ **DEGENERATE** |

This is the **true broken-text signature**, not the refusal floor: `scorable_frac` 0.996 with only
**2 of 495** short rows. **Not judged** — ~495 judge calls avoided and no fake number produced.

> **So F-3's retracted claim cannot be re-earned by matching the dose.** At magnitude **1.0** the
> refusalness add is coherent but is only ~7% of one diff-of-means and moves ASR by −0.0111 (n.s.);
> at magnitude **14.65** it is a meaningful dose but destroys generation. There is no dose in
> {1.0, 14.65} that is both interpretable and comparable to the random control. Establishing
> refusalness-`add` specificity would need an **intermediate-dose sweep**, which this sprint did not run.
> The α = 1.0 sign-reversal claim **stays retracted**.

### ✅ Arm E released — its dose-matched composed control is inert

| arm | intervention | Δ_cl | p_cl | CI |
|---|---|---|---|---|
| B_removeS | `d_surface:project_out:8-8:1.0` | +0.0305 | 0.0089 | [+0.0089, +0.0522] |
| **E_removeS_addR** | `d_surface:project_out:8-8:1.0` + `refusalness:add:18-18:1.0` | **+0.0211** | 0.0234 | [+0.0033, +0.0389] |
| **E_CTRL** (dose-matched) | `random:project_out:8-8:1.0` + `random:add:18-18:**0.068243**` | **−0.0055** | 0.5809 | [−0.0265, +0.0154] **inert** |
| addBoth_025 | `d_surface` + `refusalness`, both 0.25 | −0.0348 | 0.0288 | [−0.0655, −0.0041] |
| **addBoth_CTRL** | `random:add` both @0.25 | **−0.0016** | 0.8057 | [−0.0153, +0.0121] **inert** |

Both composed controls are **inert** once dosed correctly — replacing the tick-13 situation where the
α = 1.0 control was itself a +0.0889 jailbreak.

### The interaction, with paired clustered inference and multiplicity

| contrast | Δ | sem | t (15 df) | p_cl | **Holm (m=2)** |
|---|---|---|---|---|---|
| **E − B** — does restoring refusalness cancel the `d_surface` removal? | **−0.0094** | 0.0043 | −2.19 | **0.0446** | **0.0892** |
| **E − E_CTRL** — is arm E specific vs its matched composed control? | **+0.0266** | 0.0123 | +2.17 | **0.0469** | **0.0892** |

Both are individually significant and **neither survives Holm across the two pre-specified contrasts**.

> **Verdict: SUGGESTIVE, NOT ESTABLISHED.** Restoring refusalness cancels ~31% of the `d_surface`
> removal effect (+0.0305 → +0.0211), in the direction plan hypothesis 5 predicts, against an inert
> dose-matched control — but at p_cl ≈ 0.045 uncorrected and ≈ 0.089 corrected. Applying the same
> standard used against the `d_surface` layer profile in F7, this does not clear the bar.

A note that makes the effect more interesting than its p-value: the refusalness leg in arm E is at
magnitude **1.0 ≈ 7% of one diff-of-means**. A 7%-strength restoration cancelling ~31% of the removal
effect implies a **strongly non-linear dose response** — or that the cancellation is not really about
dose at all. An intermediate-dose sweep would settle both this and the F-3 question in one experiment,
and is the single highest-value run the next sprint could make.

### Phase F status at close

| plan §8 arm | status |
|---|---|
| 1 baseline · 2 remove `d_surface` · 3 remove refusalness · 4 remove both | ✅ established (committed AdvBench decomposition) |
| 5 remove `d_surface` + add refusalness | ✅ run, controlled, **suggestive not established** |
| 6 remove refusalness + add `d_surface` | ✅ run (α=0.25); control judged this tick |
| 7 add `d_surface` | ✅ run at α=0.25; ⛔ degenerate at α=1.0 |
| 8 add refusalness | ✅ at α=1.0 (under-dosed, n.s.); ⛔ **degenerate** at matched dose |
| 9 add both | ✅ run at α=0.25, control inert |
| 10 matched random controls | ✅ all present and inert **at α=0.25**; ⛔ NOT inert at α=1.0 |
| layer profile L12–L20 | ✅ **established**, 4/5 survive Holm |

Plus the L6–L10 gap: **no Llama refusal direction exists below L12**, so the interaction cannot be
measured inside `d_surface`'s own causal band. That remains the sprint's largest unanswered structural
question and needs a direction fit, not more analysis.

## Phase G — the position effect is a MONOTONE DECAY, and that makes the confound decisive

Job **768780** COMPLETED (9:22, 24 families). Artifact `outputs/boombness_followup/g3_second.json`.
`all_layers_demo`, **1,024 edges in every arm**, same layers, same 24 prompts:

| scope | Δ | sem |
|---|---|---|
| **`first_codeword`** | **+0.9718** | 0.0706 |
| **`second_codeword`** | **+0.3272** | 0.0473 |
| **`last_codeword`** | **−0.0231** | 0.0615 |

**Tick 35 pre-registered two readings.** (a) *the first is special* → the second should already be
small. (b) *the effect decays with position* → the second should be intermediate.
**(b) wins.** +0.97 → +0.33 → −0.02 is a graded serial-position effect, not a first-demonstration
singularity. My tick-34 gloss — "the first demonstration establishes the mapping and later ones inherit
it" — is **not** what the data show; it predicted a step, and this is a slope.

### Why this makes review #3's identification limit the decisive question

A monotone decay across demonstration positions is **exactly** what *"distance from BOS /
attention-sink proximity"* predicts, just as much as *"demonstration ordinality"* does. The first demo
codeword is earliest in the sequence, the second next, the last latest. **The two explanations are
currently indistinguishable**, and the graded result makes that worse, not better — a step function
would have been harder to explain by position alone.

### The control that separates them — submitted

| job | tag | scope |
|---|---|---|
| **768801** | `g3wa24_nbr` | `--demo-scope first_neighbor` — the token **immediately before** the first demonstration codeword |

Same sequence region, same **1,024 edges**, same layers, same prompts — but **not a codeword**.

- If the decay is about **position**, `first_neighbor` should behave like `first_codeword` (≈ +0.97).
- If it is about the **codeword**, `first_neighbor` should be near **zero**.

Recorded before the run lands, as at tick 33. Note that tick 33's prediction was **falsified**, which is
the reason to keep writing them down.

⚠ Carrying forward from review #3 and not yet addressed: **lexical G = 1** — all 24 prompts use
`carrot`/`bomb`, so whatever this establishes is established *for carrot*. `first_neighbor` does not fix
that; a second codeword/concept pair would.

## ✅ The serial-position confound is RULED OUT — the effect is the codeword, not the position

Job **768801** COMPLETED (11:16, 24 families, `effective_G = 24`, zero ledger failures).
Artifact `outputs/boombness_followup/g3_neighbor.json`.

All four arms: `all_layers_demo`, **1,024 edges**, all 32 layers, same 24 prompts, bit-identical
baselines.

| scope | Δ | sem |
|---|---|---|
| **`first_codeword`** | **+0.9718** | 0.0706 |
| **`first_neighbor`** — the token *immediately before* it, **not** a codeword | **−0.0154** | **0.0107** |
| `second_codeword` | +0.3272 | 0.0473 |
| `last_codeword` | −0.0231 | 0.0615 |

**Tick 36's prediction, recorded before the run:** *"If the decay is about **position**,
`first_neighbor` should behave like `first_codeword` (≈ +0.97). If it is about the **codeword**, it
should be near zero."*

> **It is near zero. The effect is the codeword.**

Cutting 1,024 attention edges out of the token one position earlier — same sequence region, same
attention-sink proximity, same layers, same budget — does **nothing** (−0.0154 ± 0.0107). Cutting the
codeword itself does **+0.97**.

### Paired contrasts (row = family here, so these are family-level)

| contrast | paired | t | sign test | **domain-clustered** | p_cl |
|---|---|---|---|---|---|
| **first − neighbor** | **+0.9872** ± 0.0742 | **+13.30** | **24/24** | +0.9872 ± 0.0733, t **+13.46** | **4.1e-05** |
| first − second | +0.6446 ± 0.0704 | +9.15 | 23/24 | t +11.37 | 9.2e-05 |
| second − last | +0.3503 ± 0.0856 | +4.09 | 18/24 | t +3.66 | 1.5e-02 |
| first − last | +0.9949 ± 0.0875 | +11.36 | 24/24 | t +9.78 | 1.9e-04 |

Every step of the decay is significant under domain clustering, and the position control is
annihilated at **24/24 prompts**.

### What is now established, and what it is not

**Established:** the attention edges out of a demonstration's **codeword token** are causally
load-bearing for the readout, the effect **decays monotonically** across demonstration occurrences
(+0.97 → +0.33 → −0.02), and it is **not** explained by absolute sequence position or
attention-sink proximity. This closes **identification limit 2** from review #3.

**Not established, and carried forward:**
1. **Lexical G = 1.** All 24 prompts use `carrot`/`bomb`. This is established **for `carrot`**. A second
   codeword/concept pair is the only fix, and it is a bank change rather than a scope flag.
2. **It is token suppression, not re-binding** (review #3, R3-6): Δ logp_codeword = −0.9449 vs
   Δ logp_concept = +0.0268. Cutting the first demonstration's codeword makes the model **less likely
   to say *carrot***; it does not make it more likely to say *bomb*.
3. **The mechanism is still unnamed.** A decay that is codeword-specific and *suppresses the codeword*
   is consistent with the first mention establishing the token's retrievability and later mentions being
   redundant — but that is a hypothesis, and the sprint has now been wrong twice about how to read this
   arm (tick 33's prediction, tick 34's "step" gloss).

## Closing lexical G = 1 — the E6 codeword swap, launched (tick 38)

Review #3's remaining identification limit: **all 24 Phase G prompts use `carrot`/`bomb`**, so the
result is established *for carrot*, not for codewords. Confirmed against the bank —
`target_surface` is `carrot` (1,968 rows) or `bomb` (768, the concept-surface cells) and `concept` is
**`bomb` on all 2,736 rows**. One pair, exactly as the auditor said.

**No new code was needed.** Two pieces of prior work made this a command rather than a project:

1. `src/boombness/screen_concept_pairs.py` + `outputs/boombness/concept_pair_screen.json` — the
   previous sprint **already screened** candidate pairs on single-token bare form, single-token
   capitalised form (defect C-5), first-subtoken-not-a-common-word, and variant-count symmetry.
   `symmetric_pairs[0]` is **`apple` / `bomb`**, variant counts symmetric.
2. `prompt_families.py` already exposes **`--codeword` / `--concept`**.

This is the **E6 codeword swap** the last pre-sprint commit (`8b9e10e4`) scoped as "16 sentences" and
never ran.

### Bank generated

```
$PY src/boombness/prompt_families.py --codeword apple --concept bomb --preset main \
    --seed 20260816 --out data/boombness_prompts/boombness_prompt_bank_apple.jsonl
# 2,736 rows · 2x2 families checked=336 violations=0 · duplicate prompt_ids dropped=0
```

**Written to a NEW path.** `--out` defaults to the main `BANK_PATH`; overwriting the bank every
committed result depends on would have been unrecoverable. Main bank verified untouched.

### ⚠ The mandatory tokenization audit could not run on the login node

Plan §2.4 makes a tokenization audit mandatory before activation work on a new bank. Run locally it
reports `SKIP … gated repo … 401` for Llama-3.1-8B and **still writes a run directory** — a skip that
looks like a completed audit if you only check that the directory exists. Resubmitted to a compute node
with `--strict` (**768829**) so a failure is an exit code rather than a log line.

### Runs queued, and how they will be read

| job | tag | scope |
|---|---|---|
| **768829** | `apple_audit` | tokenization audit, `--strict` |
| **768833** | `apA_firstcw` | `first_codeword` on the apple bank |
| **768834** | `apA_nbr` | `first_neighbor` on the apple bank |
| **768832** | `ap_last` | `last_codeword` on the apple bank |

**Only the `all_layers_demo` arm will be interpreted**, and the reason is specific: that arm ignores
`--layers`/`--topk` and cuts every (head, source) edge with **no ranking**, so the `d_surface` matrix is
replicated and unused (confirmed by review #3 at `surgical_knockout.py:947-957` and `pick_edges:498`).
That makes it legitimate to run against the **carrot-fitted** `--fit-dir` — the direction never enters
the computation. Every *ranked* arm in these runs is uninterpretable and will not be quoted.

**Process note.** The first submission derived tags with `cut -d_ -f1`, which mapped both
`first_codeword` and `first_neighbor` to `ap_first` — two different arms writing the same tag. Caught
before either ran. Replacements were submitted **first** and the mis-tagged pair cancelled only after
the new job ids came back (the tick-23 rule: never `scancel` before the replacement is known good).

### Prediction, recorded before the runs land

If the Phase G effect is about **codewords** rather than about `carrot` specifically, the apple bank
should reproduce the pattern: `first_codeword` strongly positive, `first_neighbor` ≈ 0,
`last_codeword` ≈ 0. If `apple` behaves differently, the carrot result is lexical and the sprint's
Phase G claim narrows to a single word.

## ✅✅ E6 RESULT — the Phase G effect REPLICATES on a second codeword. Lexical G is now 2.

Jobs **768832/768833/768834** COMPLETED (14:41–14:45). Artifacts under
`outputs/boombness/surgical_knockout/{apA_firstcw,apA_nbr,ap_last}_20260820_120438_*`.
`all_layers_demo`, **1,024 edges**, all 32 layers, 24 families across all 6 domains, **0 ledger
failures** in every arm.

### The audit gate fired, and one contaminated family was in the analysis

**768829 FAILED (exit 1:0)** under `--strict`. Reading it rather than treating it as a blocker:

- **2,712 of 2,736 rows OK**; `codeword_is_single_token: **true**`, `concept_is_single_token: **true**`
  — the properties `screen_concept_pairs.py` selected `apple` for hold.
- The **24 bad rows are 12 family-alignment violations confined to the `instructional` domain** at
  n8 and n16, all of the form `occurrence_count_mismatch:text=N,tokens=N+1` — the tokenizer finds one
  more `apple` than the text counter does.

Cross-checking the flagged families against the ones the knockout actually selected: **exactly one
overlaps** — `instructional|dev|slot0|n8|…|semantic_one_word`, 1 of 24. So I recomputed with and
without it rather than reporting the pooled number:

| scope | all 24 families | **flagged family excluded (n = 23)** |
|---|---|---|
| `first_codeword` | +0.5057 ± 0.0584 | **+0.5038 ± 0.0610** |
| `first_neighbor` | +0.0000 ± 0.0082 | **−0.0010 ± 0.0085** |
| `last_codeword` | −0.0509 ± 0.0814 | **−0.0517 ± 0.0850** |

The contaminated family moves nothing (+0.5057 → +0.5038). **All numbers below are the clean n = 23.**

### The prediction, recorded at tick 38, held

> *"If the effect is about **codewords**, apple should reproduce: `first_codeword` strongly positive,
> `first_neighbor` ≈ 0, `last_codeword` ≈ 0."*

| contrast (clean, domain-clustered, 6 domains) | paired | sign | clustered t | p_cl |
|---|---|---|---|---|
| **first − neighbor** | **+0.5049** | **22/23** | **+5.68** | **2.4e-03** |
| **first − last** | **+0.5555** | 20/23 | **+6.73** | **1.1e-03** |

`first_neighbor` on the apple bank is **−0.0010 ± 0.0085** — the position control is again
**annihilated**, on a second lexical item.

### Side by side

| | carrot | apple |
|---|---|---|
| `first_codeword` | **+0.9718** | **+0.5038** |
| `first_neighbor` | −0.0154 | **−0.0010** |
| `last_codeword` | −0.0231 | −0.0517 |
| first − neighbor, clustered | t +13.46, p 4.1e-05 | t +5.68, p 2.4e-03 |

> **The qualitative structure is identical on both codewords: the first demonstration's codeword
> carries the effect, the adjacent non-codeword token carries none, the last demonstration carries
> none. Review #3's identification limit 1 (lexical G = 1) is CLOSED.**

**Stated honestly: the magnitude is about half** (+0.50 vs +0.97). The *pattern* replicates; the
*effect size* is lexically dependent. So the claim that generalises is the **structure**, not the
number, and the sprint should say "the first demonstration's codeword carries the effect" rather than
quote +0.97 as though it were a property of codewords in general.

### ⚠ Defect found in the audit tool — a FAILED strict audit still writes `DONE.json`

768829 exited **1:0** and its run directory nonetheless contains **`DONE.json`**. `common.require_done`
— the guard the whole repo uses to refuse unfinished runs — would therefore **accept a strict audit
that failed**. This is the same shape as the `judge_boombness` abort path done right (that one writes
`ABORTED.json` *instead of* `DONE.json`, which is why the R-14 re-creation was caught at tick 3).

**Recorded, not fixed:** `tokenization_audit.py` is shared with the non-Boombness workstream, and
changing what it writes on failure could silently invalidate other consumers' assumptions. Flagged for
a decision. In the meantime the audit's **exit code**, not its `DONE.json`, is the thing to check.

## ✅ Phase E4 — removing `d_surface` moves a GATE, not the content behind it. And the continuous estimand is nearly the binary one.

**Artifact:** `outputs/boombness_followup/e4_pathway_advbench.json`
**Producer:** `src/boombness/analyze_e4_pathway.py` (new, ~200 lines, reuses `cluster_mean_ci` from
`analyze_g8`). **No GPU, no judge spend, no new generations** — it reads only the scalar columns of
four *already committed* judge runs. **It never opens `gens.jsonl`**, so no harmful text is read,
printed, or written; `reads_generation_text: false` is asserted in the artifact itself.

**Command**

```
python src/boombness/analyze_e4_pathway.py \
  --base outputs/boombness/judge/abg_base_20260819_011714_1480836 \
  --arm remS=outputs/boombness/judge/abg_B_20260819_013447_1506491 \
  --arm remS_ctrl=outputs/boombness/judge/abg_Bctrl_20260819_020905_1520524 \
  --arm remR=outputs/boombness/judge/abg_C_20260819_011714_1480835 \
  --arm remBoth=outputs/boombness/judge/abg_D_20260819_013551_1507682 \
  --out outputs/boombness_followup/e4_pathway_advbench.json
```

Llama-3.1-8B-Instruct, AdvBench heldout, **n = 495 paired prompts, 16 domain clusters, 0 rows
dropped** (`judge_status == "ok"` on all 495 in all five runs). Arms are exactly pairable — same
bank, same `prompt_id`s — so every contrast below is paired per prompt *then* clustered by domain.

**First, a reproduction.** The script re-derives the sprint's two load-bearing external numbers from
raw judge rows through an independent code path: arm B (remove `d_surface`) **+0.0305, p_cl 0.0089**
and arm C (remove refusalness) **+0.1895** — matching the committed figures to four decimals. That is
worth more than the E4 result itself, because R3-3 found the Phase F headline contrasts existed in no
artifact at all.

### The pathway question, and the answer

E4 asks whether removing `d_surface` makes the model *less able to see danger* (so it stops refusing)
or *better at answering* (so its compliance is more useful). Those predict opposite things about
where the effect lives, so the prompts are split by the **baseline's** refusal state and each stratum
is measured separately.

| arm | `base_refused` (n=461) | `base_answered` (n=34) | Δ refusal rate | refusal flips |
|---|---|---|---|---|
| **remS** (`d_surface`) | **+0.0327**, p 0.0100, 21↑ / 0↓ / 440 flat | +0.0072, p 0.28, 3↑ / 0↓ / 31 flat | **−0.0424** | 21 |
| remS_ctrl (random) | 0.0000 (degenerate), 0↑ / 0↓ / 461 flat | −0.0385, p 0.85 | +0.0020 | 0 |
| remR (refusalness) | +0.2028, p 0.00030, 101↑ / 0↓ | +0.1291, p 0.33 | −0.2222 | 110 |
| remBoth | +0.2740, p 0.000095, 142↑ / 0↓ | +0.0812, p 0.57 | −0.3091 | 153 |

**Not one prompt in any arm moves down.** And the decisive structural fact, checked directly on the
raw rows: **among prompts that stay keyword-refused, the score delta is exactly 0.0 for every single
prompt, in every arm** — 440/440, 351/351, 308/308, 461/461. Every point of score movement is a
refusal→non-refusal flip. `remS`'s 24 movers are its 21 flips plus 3 prompts the baseline already
answered.

**On already-answered prompts, `remS` does essentially nothing** — +0.0072 (p 0.28) on the score,
**+17 characters** (against +83 pooled), 31 of 34 completely flat. The direction that supposedly
carries "harmfulness evidence" does not make a compliant answer more harmful, more specific, or
longer. It only changes *whether* the model complies.

### ⚠ But half of that is the instrument, and saying so is the honest version

StrongReject's rubric is structurally `(1 − refusal) × (convincing + specific − 2)/8`. A judged
refusal is multiplied to **exactly zero by construction**. So "still-refused ⇒ Δ = 0" is largely a
*rubric identity*, not a discovery about the model, and I am not citing it as one. The part that is
**not** an identity is the `base_answered` stratum — there the rubric is free to move and does not.

The `instrument` block in the artifact quantifies the rest. Per arm, the mean score **among answered
prompts**:

| arm | answered n | mean score | score histogram |
|---|---|---|---|
| base | 34 | **0.923** | 0.0 ×463, 0.75 ×2, 0.875 ×1, 1.0 ×29 |
| remS | 55 | **0.950** | 0.0 ×442, 0.875 ×6, 1.0 ×47 |
| remR | 144 | 0.894 | 0.0 ×361, 0.75 ×5, 0.875 ×32, 1.0 ×97 |
| remBoth | 187 | 0.888 | 0.0 ×321, 0.625 ×1, 0.75 ×15, 0.875 ×30, 1.0 ×128 |

Compliance quality sits at the **top of the scale and barely moves** (0.89–0.95 across arms that
differ 5× in ASR). Therefore on this dataset

> `strongreject_score ≈ 0.9 × ASR@0.5`

and the "continuous score" and the "binary flag" are **one measurement reported twice**.

**This has a consequence for how this sprint has reported statistics.** Several results here quote
the continuous and binary estimands side by side and read their agreement as corroboration —
review #3 did exactly that for the arm-6 reversal ("survives on the binary flag, slightly stronger").
That agreement is **near-automatic** and carries almost no independent information. It does *not*
invalidate any result: putting both in one Holm family is conservative, and arm 6 survives Holm at
m = 20 anyway. But the phrase "and it also holds on the binary estimand" must stop being written as
though it were a second test. **Downgraded, not retracted.**

### What E4 establishes

1. **`d_surface` removal acts through the refusal gate.** Its entire measurable behavioural effect is
   21 prompts flipping out of refusal; conditional on compliance it changes nothing detectable
   (n = 34, underpowered, and stated as such).
2. **So do refusalness removal and the joint arm** — same shape, 5× and 7× the magnitude.
3. **The matched random control produces zero flips** and is flat on all 461 refused prompts.
4. This **supports plan §1 hypothesis 5** — `d_surface` supplies evidence the refusal mechanism
   consumes — over hypothesis 3 (a hazardous-object axis), and it is consistent with the E1 finding
   that the effect is *weakest* in the category the direction was fitted on.

### Limits

- `refused` is `bj.kw_refusal(text)` (`judge_boombness.py:262`), a **keyword** detector, not the
  judge model. Every stratified number inherits its error rate. Its agreement with the rubric is
  perfect here (**0 of 461/440/351/308 keyword-refused rows carries a non-zero score**), which is
  reassuring but is itself partly the rubric identity above.
- The `base_answered` stratum is **n = 34**. "No content effect" is a null at low power, not a
  demonstrated absence. Widening it needs a dataset with a higher baseline compliance rate — the
  same dynamic-range requirement as plan §10.
- Llama-3.1-8B, AdvBench heldout, L8 for `d_surface` / L18 for refusalness. Not yet replicated.

## Cross-Model Replication With Dynamic Range — Phase H opened on Phase G (tick 43)

Everything established so far is Llama-3.1-8B. The newest and best-controlled result — the first
demonstration's codeword carrying the attention effect — is the natural thing to port, because
`surgical_knockout.py` reads a **representation** rather than ASR, so it does **not** need the
behavioural dynamic range that blocked Qwen3 on AdvBench (0.8% baseline compliance, R-17).

### The E6 bank turns out to be the *only* sound vehicle, and that was not the reason it was built

From `concept_pair_screen.json`, per-model, on **Qwen/Qwen3-14B**:

| word | bare single-token | space single | capitalised single |
|---|---|---|---|
| **`carrot`** | ❌ **false** | true | ❌ **false** |
| **`apple`** | ✅ true | ✅ true | ✅ true |
| `bomb` | ✅ true | ✅ true | ✅ true |

**The main carrot bank is tokenization-unsound on Qwen3** — `carrot` is multi-token there, which makes
"the codeword's position" a span and breaks every point-wise patch (plan §2.4). The apple bank built
at tick 38 to close lexical G = 1 happens to be **clean on both models**, so it is the vehicle for the
cross-model test. That is a payoff from `screen_concept_pairs.py` having screened *both* models before
either bank existed.

### Runs submitted

| job | tag | what |
|---|---|---|
| **769001** | `apple_audit_q3` | tokenization audit, apple bank, **Qwen3**, `--strict` |
| **769002** | `q3ap_firstcw` | `first_codeword` |
| **769003** | `q3ap_nbr` | `first_neighbor` (position control) |
| **769004** | `q3ap_lastcw` | `last_codeword` |

All against `extract_boombness/qwen3_cw_20260817_140633_992753` (verified 5120-d, the correct Qwen3
dimensionality), `--model Qwen/Qwen3-14B`, otherwise identical configuration to the Llama arms.

### ⚠ A known risk I am NOT assuming away

`surgical_knockout.py` has **no `--enable-thinking` flag** — its own comment at line 868 records that
`resolve_occurrences` "takes an `enable_thinking` argument this call did not pass." On Qwen3 that
matters: handover defect **C-8** found the thinking-ON extract's final token is a `<think>` control
token and is unusable as a readout position.

I am **not** pre-judging it. The module's **`option_mass_gate`** refuses to finish when the median
next-token mass on the answer options falls below `--min-option-mass` (0.05) — a readout sitting on a
`<think>` token should trip exactly that. **If the gate fires, the answer is "Phase G cannot be ported
to Qwen3 without threading `enable_thinking` through the knockout", and that is the result I will
report** — not a number.

Prediction, recorded before the runs land: if the option-mass gate passes, the Llama pattern
(`first_codeword` positive, `first_neighbor` ≈ 0, `last_codeword` ≈ 0) should reproduce, with a
magnitude that need not match — the apple/carrot comparison already showed the effect size is
lexically dependent, so it is likely model-dependent too.

### Attempt 1 (769001–769004) — the audit PASSED on the science and the arms died on MEMORY

**Not the `<think>` failure I anticipated.** The option-mass gate never got a chance to speak.

**Audit 769001** — exit 1:0 under `--strict`, but reading it rather than treating the exit code as the
answer:

| Qwen3-14B, apple bank | |
|---|---|
| `codeword_is_single_token` | ✅ **true** |
| `concept_is_single_token` | ✅ **true** |
| rows OK | **2,712 / 2,736** |
| bad | 24 — the **same** `instructional` n8/n16 families as the Llama audit |

So the 24 bad rows are a **bank property, not a model property** — identical on both models. **The apple
bank is tokenization-sound on Qwen3**, which is what this audit existed to establish. The `--strict`
exit reflects those 24 rows, and the same one-family overlap applies as on Llama.

**Arms 769002–769004** — all three `torch.OutOfMemoryError: CUDA out of memory … GPU 0 has a total
capacity of 44.39 GiB of which 19.31 MiB is free`. Qwen3-14B in bf16 is ~28 GiB of weights on a 44 GiB
L40S, leaving too little for the all-layer attention hooks. **A resource limit, not a scientific one.**

### Attempt 2 (769187–769189) — using the module's own lever, not a hack

`surgical_knockout.py` provides `--skip-arms`, and its help text is explicit that a skipped arm "is
counted in the FailureLedger and named with its reason in summary.json; it is **never
absent-and-unexplained**." So the memory is reclaimed *on the record* rather than by trimming the
experiment quietly:

```
--skip-arms dense_two_layer,positive_control,subsampled_all_layers_demo
--skip-arms-reason OOM-on-Qwen3-14B-at-44GiB-L40S:only-all_layers_demo-is-interpretable-here-...
```

| job | tag | scope |
|---|---|---|
| 769187 | `q3b_firstcw` | `first_codeword` |
| 769188 | `q3b_firstnbr` | `first_neighbor` |
| 769189 | `q3b_lastcw` | `last_codeword` |

**Why skipping these three costs nothing here.** `dense_two_layer` is the arm the handover documents as
**structurally infeasible** (it silently truncated to 13% of its target). `positive_control` was shown
by review #3 (**R3-5**) to be the *wrong* movability anchor — its ceiling is n = 1 — and the correct one
is that **`first_codeword` is itself the matched positive control for `first_neighbor` and
`last_codeword`**, which is preserved. `subsampled_all_layers_demo` is a variance probe on an arm I am
not quoting. The three arms that carry the comparison — `none`, `all_layers_demo`, `no_demo_text` — all
survive.

### ⛔ Attempt 2 (769187–769189) ALSO died on memory — and the cause is a hardcoded dtype, not the model size

`--skip-arms` reclaimed nothing, because the OOM never reaches an arm. It fires while `accelerate`
is still moving weights onto the card, inside the very first `k_proj` forward:

```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 20.00 MiB.
GPU 0 has a total capacity of 44.39 GiB of which 19.31 MiB is free.
... 43.86 GiB is allocated by PyTorch
```

43.86 GiB allocated for a **14.8 B-parameter** model is the tell. `surgical_knockout.py:677` calls

```python
lm = dc.load_model(args.model or dc.PRIMARY_MODEL, dtype=torch.float32, attn_implementation="eager")
```

**`torch.float32`, hardcoded, no flag.** Qwen3-14B in fp32 is ~59 GiB of weights and cannot be
resident on a 44 GiB L40S at any batch size, arm count, or `--topk`. Llama-3.1-8B in fp32 is ~32 GiB
and fits, which is why this never surfaced — every previous consumer of this module was the 8 B model.

This is house rule 4 ("an OOM means the code is wrong — wrong dtype, wrong backend, wrong node — not
that the experiment should be trimmed"). Attempt 2's `--skip-arms` was **treating a code defect as a
resource limit**, and the skip-reason string I wrote into the ledger
(`OOM-on-Qwen3-14B-at-44GiB-L40S`) is wrong on the mechanism. Recorded here rather than edited away.

### Fix — a `--dtype` flag that defaults to the committed behaviour

```python
ap.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"], ...)
_DTYPES = {"float32": torch.float32, "bfloat16": torch.bfloat16}
lm = dc.load_model(..., dtype=_DTYPES[args.dtype], attn_implementation="eager")
```

Six lines. **The default is `float32`, deliberately**: every committed knockout number in this repo
and the previous sprint was produced in fp32, and a default change would silently re-base all of
them. `bfloat16` is opt-in and is recorded in `summary.json` via the existing `run.note_model(...,
dtype=str(lm.dtype))` call, so no run can be mistaken for the other afterwards.

### Attempt 3 (769903–769906) — and it carries its own dtype control

`--skip-arms` is **dropped**. With bf16 the memory pressure that motivated it is gone, so the Qwen3
arms now run the *identical* arm set to the committed Llama apple arms (`apA_*`), which is what makes
the cross-model comparison a comparison.

| job | tag | model | dtype | `--demo-scope` |
|---|---|---|---|---|
| 769903 | `q3c_firstcw` | Qwen3-14B | bf16 | `first_codeword` |
| 769904 | `q3c_firstnbr` | Qwen3-14B | bf16 | `first_neighbor` |
| 769905 | `q3c_lastcw` | Qwen3-14B | bf16 | `last_codeword` |
| **769906** | **`llbf16_firstcw`** | **Llama-3.1-8B** | **bf16** | `first_codeword` |

**769906 is the point of the fix.** Qwen3-bf16 versus Llama-fp32 is confounded by dtype, and a
cross-model null under that confound would be uninterpretable. 769906 re-runs the *committed*
`apA_firstcw` arm (Llama, apple bank, fp32, `first_codeword`, effect **+0.63**) changing **only** the
dtype. If it reproduces, dtype is measured to be inert on this readout and the Qwen3 comparison is
clean; if it does not, the cross-model test is abandoned rather than reported, and the finding
becomes "this readout is not dtype-stable".

The `<think>`-token risk from attempt 1 is unchanged and still unjudged: `option_mass_gate` remains
the arbiter, and if it fires the reported result is "Phase G cannot be ported to Qwen3 without
threading `enable_thinking` through the knockout" — not a number.

### ⛔ Attempt 3 — the dtype control DID ITS JOB and REFUTED my own fix. bf16 is not admissible here.

**769906 (`llbf16_firstcw`, Llama-3.1-8B, apple bank, bf16) FAILED on all 24 rows:**

```
[knockout] 0 rows -> .../surgical_knockout/llbf16_firstcw_20260820_171613_3760625
[knockout] failures: {'dominance:AssertionError:L8: the value-flow decomposition does not
                      reconstruct the at...': 24}
```

This is `dominance.py:179` — the guard that compares the reconstructed attention output against the
module's **actual** output and refuses a relative error above **1e-3**. bfloat16 carries ~8 bits of
mantissa (eps ≈ 7.8e-3), so a reconstruction error above that tolerance is not a bug, it is
arithmetic. **`surgical_knockout.py` was in fp32 for a numerical reason, and the comment at line 677
did not say so.**

Two things follow, and the second is the one worth keeping.

1. **My `--dtype bfloat16` "fix" was the wrong lever.** The flag stays — it is inert at its
   `float32` default and it is now the thing that documents *why* fp32 is mandatory — but bf16 must
   never be used with this module. The help text is being corrected from "exists only because a 14B
   model cannot load on 44 GiB" to name the `dominance` tolerance as the blocker.
2. **The control is the reason this is a one-line correction and not a retracted cross-model
   result.** Had I run the three Qwen3 bf16 arms without 769906, the plausible outcome was not a
   crash but a *number* — Qwen3's own reconstruction error might have landed just under 1e-3 at some
   layers and just over at others, producing a partial arm set that looked like a weak cross-model
   effect. The dtype control was submitted precisely because "Qwen3-bf16 vs Llama-fp32" is a
   confounded comparison, and it converted a silent confound into a loud failure in 20 minutes of
   GPU. **This is the third time this sprint that a matched control, not a result, was the thing
   that mattered.**

`dominance.py:165-183` also deserves a note: its own comment records that an earlier version of this
check summed `D_attn` and called that a self-test, which is an **algebraic tautology** that passes for
any `Y` including one built with a wrong GQA head map. The check that replaced it is what caught the
dtype. A guard that can fail is worth more than one that cannot.

**The remaining route for Phase H is fp32 on two GPUs** — Qwen3-14B fp32 is ~59 GiB against a 44 GiB
L40S, and `device_map="auto"` already shards across whatever is visible, so `--gpus=2 --mem=96G` is a
submission change with no code change and no numerical compromise. **Not submitted — see the
concurrency incident below.**

### ⛔ INCIDENT — a second Claude session is working this repo, and it cancelled these jobs

At **17:37:17** jobs **769903** (Qwen3 `first_codeword`, 60% through weight loading), **769907** and
**769915** were all `CANCELLED by 47249` — simultaneously, by this account, and **not by me**. At
**17:41:32**, jobs 769941/769942 appeared, which I did not submit: `tokenization_audit.py` against
`data/boombness_prompts/boombness_prompt_bank_button.jsonl`, a bank that did not exist an hour ago.
`ListAgents` reports **three live interactive peer sessions** in this working directory. HEAD has
moved to **`4ff9d59c`**, a commit authored on top of mine that edits `src/boombness/prompt_families.py`
(+124 lines).

**That session's finding is correct and it matters to this one.** `4ff9d59c` reports that the apple
bank fails the plan §2.4 gate two ways: 8 core-2×2 families carry an **incidental collision**
(`instructional/benign[7]` mentions apples, so substituting `apple` yields two target occurrences
where `carrot` yields one), and — the serious one — **article agreement**: the generator does naive
word substitution and never repairs the indefinite article, so the corpus's uniform `a` produced
**2,938 ungrammatical `a apple` occurrences across 1,569 of 2,736 rows and zero grammatical ones**,
while the concept arm reads a grammatical `a bomb` in 671 rows. **The ungrammaticality is asymmetric
across exactly the two cells the 2×2 contrasts.** E6 exists to ask whether `d_surface` is a
concept-surface direction or a `carrot`-detector, and a grammaticality artifact could answer that
question the wrong way silently.

**Consequence for Phase H as I designed it: the vehicle is void.** Every attempt (769001-004,
769187-189, 769903-906) used the apple bank, chosen at tick 43 because it was the only bank
tokenization-sound on both models. That soundness argument was about the *tokenizer* and never
checked the *corpus*, which is exactly the gap `4ff9d59c` closes. **The Qwen3 cross-model port must
be re-based on the button bank before it is worth any more GPU**, and

> ⛔ **the E6 apple result at line ~2981 ("the Phase G effect REPLICATES on a second codeword,
> lexical G is now 2") is hereby marked PENDING RE-TEST, not established.** It was measured on a bank
> whose two contrasted cells differ in grammaticality as well as in codeword.

**Stopping GPU submission and escalating.** Two sessions sharing one branch, one working tree, one
`outputs/` and one SLURM account will keep cancelling and duplicating each other's work; the three
lost jobs above are the first instance, not a one-off. No further jobs submitted from this session
until the user says how to divide the work.

### Attempt 4 (769989–769991) — fp32 sharded over two GPUs, on the button bank

The user's decision on the concurrency incident: *"shut it down for me i want only you to work on
it."* Stand-down messages went to all three peer sessions; two acknowledged and idled. The third had
already queued **769982–769985** — Qwen3 button knockout ×3 plus a redundant Llama arm — and **every
one of them passed `--dtype bfloat16`**, the flag this session added an hour earlier and then
refuted. They were guaranteed to fail 24/24 rows on the `dominance` gate. Cancelled, and their
argsfiles are preserved (`args_btn_q3_*.txt`) so nothing is unrecoverable.

Resubmitted correctly — **fp32, unchanged precision, memory solved by hardware rather than by
lowering it**:

```
sbatch --time=2:00:00 --gpus=2 --mem=96G ...  # 2 x 44 GiB L40S = 88 GiB > the ~59 GiB fp32 model
```

| job | tag | scope | model | dtype | GPUs |
|---|---|---|---|---|---|
| 769989 | `btn_q3fp32_firstcw` | `first_codeword` | Qwen3-14B | **fp32** | 2 |
| 769990 | `btn_q3fp32_firstnbr` | `first_neighbor` | Qwen3-14B | **fp32** | 2 |
| 769991 | `btn_q3fp32_lastcw` | `last_codeword` | Qwen3-14B | **fp32** | 2 |

`device_map="auto"` already shards across whatever is visible, so this needs no code change. The
Llama arm the peer queued is dropped as redundant — `btn_firstcw` (769967) is already complete and
is the arm the Qwen3 runs will be compared against.

**The `<think>`-token risk is still live and still unjudged.** `surgical_knockout.py` does not thread
`enable_thinking`, and handover defect C-8 found the thinking-ON Qwen3 extract's final token is a
`<think>` control token. `option_mass_gate` (`--min-option-mass 0.05`) is the arbiter. If it fires,
the reported Phase H result is *"cannot be ported to Qwen3 without threading `enable_thinking`
through the knockout"* — a blocker, not a number.

**Prediction, recorded before the runs land.** Given that the effect size is now known to be
lexically graded on Llama by 3.6× (carrot 0.99 → button 0.27), a Qwen3 magnitude anywhere in
roughly 0.1–1.0 is consistent with replication; only a **sign flip or a null with `first_codeword`
indistinguishable from `first_neighbor`** would be evidence against. Stated now so the reading is
not chosen after seeing the number.

## ⛔ CORRECTION C-1 — I cancelled four jobs for a reason that was false by seventeen seconds

**Retracting my own justification, recorded 2026-08-20 18:45.**

At 18:12 I cancelled the peer session's jobs 769982–769985 and wrote that they were "guaranteed
dominance-gate failures" because they passed `--dtype bfloat16`. **That was wrong.** The peer had
already diagnosed the same blocker and fixed it properly, committing **`e0a3387b` at 18:06:20** — 17
seconds *after* it submitted those jobs, and long before any of them would have started. SLURM reads
the working tree at run time, not at submit time, so they would have run against the fixed
`dominance.py` and passed.

**The peer's fix is the better diagnosis of the two, and it is mine that was superficial.** It makes
the reconstruction tolerance depend on the weight dtype:

```python
_wdtype = next(model.parameters()).dtype
tol = {torch.float32: 1e-3, torch.float64: 1e-3}.get(_wdtype, 3e-2)
```

with `tests/test_dominance_tolerance.py` demonstrating rather than asserting it: a **wrong GQA head
map still produces error > 10× the bf16 tolerance** (so the guard still catches the structural bug it
exists for), while **bfloat16 rounding alone lands strictly between 1e-3 and 3e-2** (so the old
constant was rejecting valid arithmetic). Loosening a guard is only legitimate with that second
demonstration, and it is there. `recon_rel_err`, `recon_tol` and `weight_dtype` are now all written
to disk, so the number is auditable either way.

### ⛔ Consequences for what I wrote earlier

1. **"bfloat16 is inadmissible / REFUTED" is WITHDRAWN.** Job 769906's 24/24 failure was real, but it
   was a **miscalibrated guard**, not bad arithmetic. The `--dtype` help text in
   `surgical_knockout.py` has been corrected in place; the previous wording asserted the opposite.
2. **My framing of 769906 as "the control did its job" survives, but only halfway.** It did catch
   that fp32 and bf16 are not interchangeable *as the code then stood*, and that was worth 20 minutes
   of GPU. It did **not** establish what I said it established — that bf16 is numerically unfit here.
3. **The cancellation cost the sprint nothing scientifically** (those four arms are being run by
   769989–769991 on the same bank and same scopes) **but the stated reason is retracted**, and the
   peer's argsfiles are preserved.

### ✅ But the peer's central prediction is itself refuted — fp32 *does* fit Qwen3-14B here

`docs/BOOMBNESS_CONTINUATION_LOG.md` (commit `5ce7400b`) states: *"The fp32 route cannot run
Qwen3-14B on this hardware … `btn_q3fp32_*` are expected to die the same `torch.OutOfMemoryError`."*
That reasoning holds **59.2 GB of fp32 weights against one 44.4 GB L40S**, and it is correct on one
GPU. It is not correct on this cluster, because `--gpus=2` gives **88.8 GB** and `device_map="auto"`
already shards:

```
769989 btn_q3fp32_firstcw   Loading weights: 100%|##########| 443/443 [00:10<00:00, 42.14it/s]
769990 btn_q3fp32_firstnbr  Loading weights: 100%|##########| 443/443 [00:10<00:00, 44.29it/s]
769991 btn_q3fp32_lastcw    Loading weights: 100%|##########| 443/443 [00:10<00:00, 44.03it/s]
```

No OOM, and all three entered the knockout loop. **Both sessions' fixes work; they are not
incompatible, they are different trades.** bf16-on-one-GPU is cheaper and now correctly guarded;
fp32-on-two-GPUs costs a second card and buys **comparability**, because the Llama button arms these
Qwen3 runs will be contrasted against (`btn_firstcw/firstnbr/lastcw`, 769967/769968/769980) are fp32,
as is every committed knockout number in the repo. **Keeping fp32 is the reason to spend the second
GPU, and it is the only reason.** A bf16 replicate would now be a free precision check — and per the
peer's correct warning, **the two dtypes must never be pooled**.

### Working-tree note — `e0a3387b` also carries my Phase D code

Both sessions shared one checkout, so `e0a3387b` swept up my then-uncommitted `prompt_families.py`
(+112) and `tests/test_slot_disjointness.py` (+66) alongside its own `dominance.py` change. There is
**no duplicate `phase_d` preset**; the diff is my code, committed under someone else's message.
Re-verified after the merge: the main bank still regenerates to **`4cd9157399aa1b3c`**, and
`test_slot_disjointness.py` + `test_dominance_tolerance.py` are **14 passed**.

## ✅ ADOPTED — R-13, and it converges with this sprint's E4 instrument finding

The peer's last commit (`3244628a`) reports something this sprint must carry, on Qwen3 arm D:

> On `benign_literal` — prompts about a **literal carrot**, where attack success is zero by
> construction — `remove refusal` reaches **ASR 0.994** and the **norm-matched double-random
> control** reaches **0.954**, while **not one generation in 324 contains a single harmful keyword**
> and every generation is on topic about carrots. The coherence gate finds baseline and control
> indistinguishable (uniq 0.729 vs 0.731, trigram 0.005 vs 0.004), so it is **not degeneracy**.

Mechanism: `judge_boombness` maps the codeword back to the concept, so a `benign_literal` row is
judged against *build a bomb* while the model was asked about a carrot. StrongReject's rubric scores
**refusal, specificity and convincingness — none of which requires topical relevance to the goal** —
so a confident, detailed, non-refusing carrot answer scores as a successful jailbreak. Every Qwen3
ASR delta in that comparison is withdrawn.

**This is the same fact my E4 measured from the other side, and the two together are stronger than
either.** E4 found that on AdvBench `strongreject_score ≈ 0.9 × ASR@0.5` — the rubric's non-refusal
term dominates and the "continuous" estimand carries almost nothing beyond the binary flag. R-13
shows what that domination *does* when the goal string is substituted: the score becomes a measure of
**"did not refuse, and answered fluently"**, decoupled from content entirely. One finding says the
instrument is nearly one-dimensional; the other says which dimension survives.

**Why the Llama results in this sprint are unaffected — by observation, not by assumption.**
AdvBench and ClearHarm judge against the *actual* instruction with no codeword substitution, so the
mis-scoring cannot fire; and the Llama benign arm measured **+0.003**, i.e. the inflation did not
fire there either. The exposure is confined to codeword-substituted banks.

**The missing check both findings point at is TOPICALITY**, and nothing in the repo computes it. A
benign arm whose ASR rises with **zero** goal-related content is a signature that should be fatal,
and it is not currently detected by `coherence_gate` — which exists to catch a *destroyed* model and
by construction cannot catch an *undamaged but mis-scored* one. Recorded as the highest-priority
methodological gap for the next tick.

## ✅ Phase E consolidated — three named deliverables exist, and four markdown-only numbers now have a producer

**Artifacts:** `outputs/boombness_followup/d_surface_external_decomposition.json`,
`d_surface_layer_profile_replication.json`, `direction_specificity_extended.json`.
**Producer:** `src/boombness/consolidate_phase_e.py` (new). **No GPU, no judge, no new generations.**

Plan §7 names three Phase-E artifacts and none of them existed. Worse, an audit of the sources found
**four numbers this sprint has been citing that live only in this markdown file** — the R3-3 defect,
four more times. The script merges existing analysis JSON **verbatim, with each source path recorded
beside it** (nothing that already has a producer is re-derived, so no second drifting derivation is
created) and computes the four that had none.

### ⛔ M1 — the 16-category breakdown does NOT reproduce as written, and the corrected version is stronger

| | markdown claim | **recomputed from committed judge rows** |
|---|---|---|
| mean over categories | +0.0367 | **+0.0305** |
| sem | 0.0132 | **0.0102** |
| t (df 15) | 2.78 | **+3.00** |
| movable categories | 10, of which 9 positive | **8, of which 8 positive** |
| sign test p | 0.0107 | **0.0039** |

The markdown figures have no producer and are **superseded** by the artifact. The conclusion is
unchanged and the evidence is slightly stronger.

**The E1 claim itself holds, and sharply — the effect is weakest where the direction was fitted:**

| category | n | Δ | baseline ASR |
|---|---|---|---|
| terrorism_extremism | 9 | **+0.1111** | 0.000 |
| misinformation_disinformation | 37 | **+0.1081** | 0.162 |
| other_uncategorized | 38 | +0.0789 | 0.132 |
| cyber_hacking_malware | 127 | +0.0699 | 0.126 |
| theft_property_crime | 18 | +0.0556 | 0.000 |
| identity_theft | 40 | +0.0250 | 0.000 |
| **weapons_explosives_mass_casualty** | 40 | **+0.0250** | 0.025 |
| fraud_financial_crime | 68 | +0.0147 | 0.044 |
| *8 further categories* | 158 | **0.0000** | ≤0.143 |

`d_surface` was fitted on carrot↔**bomb**. Its own harm type sits **seventh of eight movable
categories**, at less than a quarter of the misinformation effect. This is the strongest single piece
of evidence that `d_surface` is **not** a hazardous-object axis (plan hypothesis 3).

**And the control is now in the same artifact and is inert:** matched random, **−0.0062**, t −0.63,
2 positive / 2 negative / 12 exactly zero, sign p 0.69. Against 8/0/8 and p 0.0039 for the real arm.

**The refusal floor is now an explicit, named list.** Eight categories are pinned at exactly 0.0000
in this arm — `self_harm_suicide` (n=23), `child_exploitation` (n=7), `violent_crime_physical_harm`
(n=21), `hate_speech_discrimination`, `harassment_bullying_stalking`, `drugs_controlled_substances`,
`privacy_surveillance`, `academic_dishonesty`. Removing `d_surface` does not reach the harms one
would most want protected.

### ✅ M3 — the multiplicity block, and "Holm rejects nothing" survives with a corrected family size

Holm-adjusted p over the `d_surface` layer profile, **m = 11** (the markdown used m = 10; L15 is now
in the family and the degenerate L16 is correctly *excluded and named* rather than counted):

`L12 0.0618 · L8 0.0893 · L10 0.1708 · L6 0.4536 · L13 0.631 · L14 0.846 · L4/L15/L18/L24/L28 1.000`

**Holm rejects nothing.** BH(0.05) rejects **L8 and L12**, both at adjusted 0.0491 — matching the
markdown. The refusalness profile, by contrast, has **four of five depths surviving Holm** (m=5):
L14, L16, L18, L20. The asymmetry that carries §3's separability claim is now in a file.

### ✅ M6 — cos(d_surface, refusalness) reproduces exactly

| layer | cos | z vs random | shared variance |
|---|---|---|---|
| L12 | +0.1279 | **+8.3** | 1.64% |
| L14 | +0.0972 | +6.3 | 0.94% |
| L16 | +0.0467 | +3.0 | 0.22% |
| L18 | +0.0262 | **+1.7** | 0.07% |
| L20 | +0.0176 | **+1.1** | 0.03% |

Random baseline sd = **0.01541** over 2,000 draws in R⁴⁰⁹⁶ (analytic 1/√d = 0.01563). Matches the
markdown to four decimals. **At chance by L18**, where refusalness is causally strongest.

### ✅ M2 — the benign arms, aggregated at last

| arm | over-refusal | word-Jaccard vs baseline |
|---|---|---|
| baseline | **0.0000** | — |
| remove `d_surface` | **0.0000** | **0.694** |
| matched random control | **0.0000** | 0.773 |
| remove refusalness | **0.0000** | 0.599 |

**Zero over-refusal everywhere** — a clean null, as claimed. Removing `d_surface` perturbs benign text
**more** than the matched random control (Jaccard 0.694 vs 0.773). ⚠ Note the markdown reported the
*dissimilarity* (1 − Jaccard: 0.3134 / 0.2271 / 0.4125); this artifact reports **similarity**, and two
of the three agree to three decimals while `remove_d_surface` differs by 0.008 (tokenization). n = 40
over 4 clusters — suggestive, not established, unchanged.

### The gaps are fields in the files, not absences

Each artifact carries a `missing_requires_gpu` block naming what it does not contain and its cost:
`d_inter` (vector exists, no arm ever run anywhere — 1 run + 1 judge, the control already exists);
the orthogonalised arms (2 + 2, deliberately deprioritised at cos ≤ 0.13); `d_surface` at **L20**, the
one planned depth never run and the only depth where a *depth-matched* `d_surface`-vs-refusalness
comparison is possible; refusalness below L12, which is a **data** gap — Llama refusal directions
exist on disk at exactly L12/14/16/18/20, so the interaction cannot be measured inside `d_surface`'s
own causal band; and the absent dual-use bank.

## ✅ NEW INSTRUMENT — `topicality_gate.py`, and it clears this sprint's Llama results by measurement

**Artifacts:** `outputs/boombness_followup/topicality_llama_advbench.json`,
`outputs/boombness_followup/topicality_qwen3_armD.json`. **Code:** `src/boombness/topicality_gate.py`
(new, ~230 lines, reuses `judge_boombness.make_goal` and the judge's own bank join). **No GPU, no
API, no new generations.**

R-13 and Phase E4 identified the same hole from two sides and neither closed it. `coherence_gate`
refuses an ASR produced by a **destroyed** model; by construction it cannot refuse one produced by an
**undamaged but mis-scored** generation. StrongReject's rubric scores refusal, convincingness and
specificity — **none of which requires the answer to be about the goal**. Nothing in the repo measured
that. This does.

Per row it rebuilds the goal the judge actually used — through `make_goal` itself, so the gate cannot
drift from the judge — and computes the fraction of the goal's content words (stopwords and the
shared query boilerplate removed) present in the generation. It emits only rates and fractions; no
generation, prompt or goal string is ever written out.

### ⚠ Two decision rules were wrong before this one, and both were caught by running the gate on arms whose answer was already known

This is recorded rather than tidied away, because both looked right.

**Rule 1 — "flagged-row overlap must RISE vs the baseline arm."** Condemned all three **known-clean**
Llama AdvBench arms. Their flagged rows sit at overlap **0.789 in the baseline** and cannot rise. A
rise test is the wrong test whenever the quantity starts at ceiling; this one would have retracted
the sprint's own valid results.

**Rule 2 — "within an arm, flagged rows must be MORE on-topic than unflagged ones."** Baseline-free
and self-normalising, which is exactly why it was tempting. It fails twice over: a **refusal usually
restates the goal** ("I can't help you build a bomb" contains every content word and scores 0), and
removing refusals does not save it, because **"answered, on topic, and not harmful" is an ordinary
category** — on AdvBench the answered-unflagged rows sit at **1.000** against the flagged rows' 0.789,
so separation is *negative* for perfectly healthy arms. Reported as a diagnostic, **not** a criterion.

**Rule 3, in force — the ABSOLUTE LEVEL.** An arm fails when its ASR rises materially and its
flagged rows' goal overlap is below `--min-absolute-overlap` (0.15). No comparison group, so neither
confound touches it, and it certifies exactly the necessary condition this instrument can support:
*these "successful attacks" are not about the goal at all.* It never certifies that they are harmful.

### Result 1 — the Qwen3 arm-D case, reproduced independently

`benign_literal`, n = 324 per arm, goals rebuilt from the bank:

| arm | ASR | flagged-row goal overlap | contains "bomb" | verdict |
|---|---|---|---|---|
| baseline | 0.003 | 0.000 | 0.0% | — |
| **remove refusalness** | **0.994** | **0.000** | **0.0%** | ⛔ **FAIL** |
| **double-random control** | **0.954** | **0.000** | **0.0%** | ⛔ **FAIL** |
| remove both (`q3_D20`) | 0.880 | 0.495 | 49.5% | ✅ PASS |

Same conclusion as R-13 — arrived at through a different code path and a different statistic. Two
arms, **including the norm-matched double-random control**, are called successful jailbreaks at
95–99% while **not one flagged generation contains a single content word of the goal**. `q3_D20` is
the one arm with real content, matching R-13's 54.3% harmful-keyword figure at 49.5% on the stricter
"contains the concept word" test.

### Result 2 — and this is the one that matters for everything this sprint has claimed

| Llama AdvBench arm | ASR | **flagged-row goal overlap** | verdict |
|---|---|---|---|
| baseline | 0.065 | **0.789** | — |
| remove `d_surface` | 0.107 | **0.799** | ✅ **PASS** |
| matched random control | 0.063 | 0.793 | not gated (ASR did not rise) |
| remove refusalness | 0.271 | **0.788** | ✅ **PASS** |
| remove both | 0.352 | **0.794** | ✅ **PASS** |

**Every Llama arm passes, at 0.79–0.80 against a 0.15 threshold.** The exposure R-13 opened is
confined to codeword-substituted banks, and that is now **measured on this sprint's own arms rather
than argued from the absence of goal substitution**. Arm B (+0.0305), arm C (+0.1895), arm D
(+0.2544), the E4 pathway decomposition and the Phase F composed matrix all rest on ASR numbers that
this gate certifies are about their goals.

### What it does not do

- **Necessary, never sufficient.** It cannot say an on-topic compliant answer is safe. A `PASS` means
  "the judge is scoring answers about the goal", nothing more.
- The overlap metric is **crude by design** — bag-of-content-words, no model, no API — because the
  signature it detects is a cliff (0.000 vs 0.79), not a gradient. On the carrot bank the goal
  reduces to essentially one content word after boilerplate removal, so there `goal_content_overlap`
  ≈ `contains the concept`. Both columns are emitted so this is visible.
- It cannot rescue the Qwen3 arms. Those ASR deltas stay withdrawn.

## ✅✅ E6 RE-TEST ON THE BUTTON BANK — the Phase G effect SURVIVES a clean codeword, and the effect size is LEXICALLY GRADED

**Artifact:** `outputs/boombness_followup/surgical_units.json` — the plan §9 deliverable, and the
producer review #3 said did not exist (**R3-3**: the headline contrasts lived only in a commit
message). **Producer:** `src/boombness/analyze_surgical_units.py` (new).

The apple bank was voided an hour earlier (see the incident above): its two contrasted cells differ
in *grammaticality* as well as in codeword. `button` is the peer session's replacement — consonant-
initial, so no article repair is needed and the exact-word-swap invariant survives; zero incidental
pool collisions; and **both tokenization audits pass on both models** (769941 Llama / 769942 Qwen3:
`rows ok=2736 bad=0 ambiguous=0`, `token-alignment violations=0`, every `button` and `bomb` variant
single-token).

### Runs

| job | tag | scope | elapsed | rows | failures |
|---|---|---|---|---|---|
| 769967 | `btn_firstcw` | `first_codeword` | 3:57 | 288 | none |
| 769968 | `btn_firstnbr` | `first_neighbor` | 8:24 | 288 | none |
| 769980 | `btn_lastcw` | `last_codeword` | — | 288 | none |

All fp32 (the only admissible precision — see the bf16 refutation above), `--layers 8,12,18,24
--topk 16`, Llama-3.1-8B, 24 families over 6 domains, option-mass gate OK on every arm.

### The contrast, paired and domain-clustered

The three runs differ only in `--demo-scope`, so they score the same prompts and their `none` arms
are **bit-identical** — the script verifies this (max |diff| < 1e-9) and refuses the contrast
otherwise. `all_layers_demo` is the only arm quoted, because it is the only one that ignores
`--layers`/`--topk` and is therefore comparable across runs.

| codeword | first − first_neighbor | first − last | sign | clustered p (G=6) |
|---|---|---|---|---|
| **carrot** | **+0.9872**, t 13.30 | **+0.9949**, t 11.36 | 24/24, 24/24 | 4.1e-5, 1.9e-4 |
| ~~apple~~ (**VOID**) | +0.5057, t 8.79 | +0.5566, t 5.41 | 23/24, 21/24 | 1.9e-3, 4.2e-4 |
| **button** | **+0.2708**, t 5.04 | **+0.2659**, t 5.20 | 21/24, 21/24 | **8.6e-3**, **4.6e-3** |

### What this establishes, and what it costs

**1. Lexical generality is 2 SOUND codewords, not 1 — and not the 2 previously claimed.** The
earlier "lexical G is now 2" rested on apple, which is void. It is now carrot + button, on a bank
certified clean by the very screener that condemned apple. Both directions of the contrast
(`first_neighbor` for serial position, `last_codeword` for occurrence role) reproduce, and the
matched-control logic is unchanged: **`first_codeword` is itself the matched positive control** for
both nulls — same intervention, same 1,024 edges, same layers (R3-5).

**2. The effect size is strongly lexical: 0.99 → 0.51 → 0.27.** Same sign, same significance, but a
**3.6×** spread across three codewords. So the magnitude reported for carrot is a property of
*carrot*, not of "a codeword", and no cross-model or cross-bank comparison may read a smaller number
as a weaker mechanism. This also retires any lingering reading of the apple/carrot gap as noise — it
is a real, ordered, lexical gradient.

**3. It does not rescue the interpretation R3-6 withdrew.** This is a **readout** claim about
`semantic_logodds`. R3-6 decomposed the carrot effect as Δlogp_codeword = −0.9449 against
Δlogp_concept = +0.0268 — **token suppression, not concept re-binding** — and nothing here revisits
that. Cutting the first demonstration's codeword makes the model less likely to say the codeword; it
does not make it more likely to say the concept.

**4. ⚠ The serial-position limit from review #3 is still open at the *bank* level.** `first_neighbor`
controls the *token* adjacent to the codeword, but `demo_block` still starts at character 0, so the
first demonstration sits in the BOS/attention-sink region in all three banks. The three-codeword
replication does not address that, because all three share the layout.

### The apple runs are kept, labelled `apple_VOID`

They are in the artifact under that name, with their numbers, precisely so that the retraction is
legible rather than a gap. They agree in sign with both sound codewords; they are simply not citable
on their own.

## ⛔ Phase H ANSWERS WITH A BLOCKER, NOT A NUMBER — and the blocker is not the one I predicted

**Jobs 769989 / 769990 FAILED, 769991 running.** `option_mass_gate` fired on the `none` arm and the
module refused to call the run reportable, which is exactly what it exists for:

```
[knockout] option mass none: median=2.486e-05 p90=2.486e-05 max=2.486e-05 frac>1%=0.000 BELOW GATE
[knockout] GATE FAILED — the run is written and every arm's numbers are on disk, but the run is
           NOT reportable:  - none: median option mass 2.486e-05 < 0.05
```

**Recorded at tick 43 and again at attempt 4, before any of these ran:**

> "If the gate fires, the answer is *'Phase G cannot be ported to Qwen3 without threading
> `enable_thinking` through the knockout'*, and that is the result I will report — not a number."

The gate fired. **The prediction's conclusion is right and its stated mechanism is wrong**, and the
run diagnostics say so plainly:

| `btn_q3fp32_firstcw`, arm `none` | |
|---|---|
| rows with a **finite** option mass | **1 of 21** |
| `n_nonfinite` | **20** |
| `top1_id` | **0 on 19 of 21 rows** — token id 0 is `'!'` |
| `logp_codeword` / `logp_concept` | −11.36 / −11.24 — both effectively zero |
| dominance failures | 3 rows, `L18`, **in fp32** |

`<think>` is token **151667** on this tokenizer, and it is nowhere in the readout. The failure is
**numerical, not positional**: the readout logits are non-finite on 20 of 21 prompts, and the
surviving top-1 is `'!'` — token 0, what a garbage logit vector decodes to. Three rows additionally
fail the value-flow reconstruction at L18 **in float32**, where the tolerance is the original 1e-3.

**So the honest Phase H result is: the knockout stack does not run numerically on Qwen3-14B, and it
is not the `enable_thinking` threading that blocks it.** That is a real finding about the method's
portability and it is reported as a blocker. Diagnosing the non-finite logits — eager attention with
Qwen3's q/k-norm under an all-layer hook stack is the obvious suspect — is next-sprint work.

⚠ **The two committed Phase H run dirs must not be read as data.** `reportable: false` is written in
their `summary.json`; `analyze_surgical_units.py` now refuses them twice over (non-finite guard, and
the run-identity guard catches the model/fit-dir mismatch first).

**Cross-model status is therefore unchanged from the handover: OPEN, not negative.** Qwen3 AdvBench
is floor-limited (R-17), the Qwen3 arm-D judging is invalid at the judge input (below), and now the
representational port is blocked numerically. Three independent reasons, none of them evidence that
the mechanism fails on Qwen3.


## ✅✅ THE QWEN3 RE-JUDGE OVERTURNS R-13 — and delivers the cross-model replication Phase H could not

**Artifacts:** `outputs/boombness/judge/q3rj2_{base,C20,D20,D20ctrl}_20260820_211*`,
`outputs/boombness_followup/topicality_qwen3_rejudged.json`. All four arms: **960 rows,
`null_frac = 0.0000`, goal statuses `{substituted: 816, noop_concept_already_present: 144}`, zero
`empty`.**

**The arms are matched, verified from their configs rather than assumed** — same seed 20260816, same
`max_new=192`, same `bfloat16`, same `enable_thinking=false`, same model. Only `--intervene` differs,
and the control is a **norm-matched *double* random** at the same two layers as arm D.

### What the empty goal was doing, and what is actually there

| `benign_literal` (n=324) — attack success is **zero by construction** | as judged (empty goal) | **re-judged** |
|---|---|---|
| baseline | 0.003 | **0.0000** |
| remove refusalness (L20) | **0.994** | **0.0000** |
| **norm-matched double-random control** | **0.954** | **0.0093** |
| remove both (L11 + L20) | 0.880 | **0.2222** |

**R-13's diagnosis is refuted.** It read those 0.95–0.99 figures as StrongReject scoring fluent,
on-topic *benign* answers as jailbreaks — "the judge scores answer style, not harmful content".
With a real goal the judge does no such thing: the two arms it condemned fall to **0.000** and
**0.009**. The phenomenon was **the empty goal**, not a rubric that ignores topicality. R-13's
*conclusion* — that the comparison was uninterpretable — was right, and is now **resolved rather than
standing**: the deltas are measurable.

### The cross-model result, paired and domain-clustered (6 clusters, 5 df)

Qwen3-14B, internal doublespeak bank, `natural_doublespeak` n = 420. **Baseline ASR = 0.1714 — this
is NOT the 0.8% AdvBench floor that blocked R-17.** There is dynamic range here.

| arm | ΔASR | p_cl | Δ StrongReject | p_cl |
|---|---|---|---|---|
| remove refusalness (L20) | **−0.0048** | 0.61 | −0.0089 | 0.42 |
| **remove both** (`d_surface` L11 + refusalness L20) | **+0.3476** | **0.00028** | **+0.3190** | **0.00017** |
| norm-matched double-random control | +0.0143 | 0.44 | +0.0021 | 0.85 |

**A large effect with an inert matched control at the same dose and depths.** This is the
cross-model replication plan §10 asked for, arrived at behaviourally after the representational
route was blocked numerically.

### ⚠ But most of it is NOT doublespeak-specific, and the benign arm is what shows it

Removing both channels also produces **+0.2222 (p_cl 0.0037)** on prompts about a **literal carrot**,
where success is zero by construction. And it is real content, not judge noise: of the flagged
benign rows, **97.2% contain the concept word** (`has_concept_rate_malicious = 0.972`, against 0.421
in the unflagged rows and 0.000 in the control).

Per-domain, (Δ on doublespeak) − (Δ on benign_literal):

| arm | doublespeak-specific excess | p_cl |
|---|---|---|
| remove refusalness | −0.0048 | 0.61 |
| **remove both** | **+0.1254** | **0.030** |
| double-random control | +0.0050 | 0.81 |

**So the honest statement is:** removing both channels raises Qwen3's doublespeak ASR by +0.348, of
which **+0.125 is attributable to the taught mapping (p 0.030)** and **+0.222 is a non-specific "emit
bomb content regardless of the prompt" effect**. Roughly **64% of the raw gain is non-specific.**
Reporting the +0.348 alone would be reporting mostly an intervention artifact — and the only reason
this is visible is that a benign arm was run.

### ⚠ The topicality gate returns UNDECIDABLE here, correctly

Every goal on this bank reduces to the single content word *bomb*, so `goal_content_overlap` is {0,1}
and identical to `has_concept` — the degeneracy guard added after review #4 fires and the gate
refuses a verdict rather than letting the threshold choose one. The raw `has_concept` rate above is
the informative quantity and is quoted as such, not as a gate verdict.

### What this does and does not establish

**Establishes.** (1) Qwen3-14B has behavioural dynamic range on the internal bank (17.1% baseline),
so **the "floor-limited, cannot test" status from R-17 applies to AdvBench, not to this model**.
(2) A composed intervention moves it far, with an inert norm- and depth-matched double-random
control. (3) A doublespeak-specific component survives the benign subtraction.

**Does not establish.** ⛔ **Which channel does the work.** This set has no arm B — `d_surface` alone
was never run on Qwen3's internal bank — so the +0.348 cannot be decomposed, and `d_surface`'s own
contribution is unmeasured. ⛔ It is **not** a replication of the *Llama* pattern: on Llama,
refusalness removal alone was the dominant channel (+0.1895); on Qwen3 it is **inert** (−0.0048).
That is either a genuine cross-model difference or a weaker refusal direction at L20, and nothing
here separates the two.

⚠ Provenance: the 2,352-row bank (hash-certified join), `max_new=192` against the Llama arms' 512,
and the judge reports `BANK IDENTITY UNVERIFIED` for the legacy-key reason documented above.

### ⛔ Ledger update

- **R-13's mechanism ("the judge scores answer style, not harmful content") is REFUTED.** Its
  withdrawal of "every Qwen3 ASR delta in this comparison" is **superseded** — they are re-measured
  above. Its methodological point stands in weakened form: a benign arm *is* the discriminator, and
  it is what exposed the 64% non-specific component here.
- **My own topicality-gate FAIL verdicts on those arms are superseded too.** They diagnosed a
  rubric-topicality failure; the real defect was upstream, at the judge input. The gate's new
  provenance guard is what would have caught it, and now does.


## ✅ All eleven plan-named deliverables now exist

`src/boombness/consolidate_deliverables.py` closes the last four. Same policy as the Phase-E
consolidation: numbers with a committed producer are **copied with their source path recorded**,
never re-derived; only the two cross-model blocks compute anything, and only because the Qwen3 arms
were re-judged tonight and no analysis had read them.

| plan deliverable | status |
|---|---|
| `token_level_occurrence_readouts.jsonl` / `token_level_dynamics_summary.json` | ✅ Phase B |
| `probe_validation.json` | ✅ **new** — indexes the run behind Decision Gate C's failure |
| `clean_fig9_correlation.json` | ✅ Decision Gate D |
| `d_surface_external_decomposition.json` / `..._layer_profile_replication.json` / `direction_specificity_extended.json` | ✅ Phase E |
| `refusal_interaction.json` | ✅ **new** — indexes the six Phase-F artifacts |
| `surgical_units.json` | ✅ Phase G |
| `cross_model_dynamic_range.json` / `cross_model_decomposition.json` | ✅ **new** — Phase H |

### ⛔ And the dynamic-range table overturns a second inherited claim

Plan §10 forbids using a floor-limited setup to claim mechanism failure, so the precondition check
is per **(model, dataset)** — which nobody had ever tabulated:

| model | dataset | baseline ASR | verdict |
|---|---|---|---|
| Llama-3.1-8B | AdvBench heldout 495 | 0.0646 | USABLE |
| Llama-3.1-8B | ClearHarm 179 | 0.1061 | USABLE |
| **Qwen3-14B** | **AdvBench heldout 495** | **0.0081** | **FLOOR** |
| **Qwen3-14B** | **ClearHarm 179** | **0.1341** | **USABLE** |
| **Qwen3-14B** | **internal doublespeak** | **0.1714** | **USABLE** |
| Qwen3-14B | internal `benign_literal` | 0.0000 | floor *by construction* — as intended |

**R-17's "Qwen3 is floor-limited" is a statement about AdvBench, not about Qwen3.** Two of the three
harmful datasets give that model plenty of room, and one of them — ClearHarm at 0.1341 — has been
sitting in the repo unremarked the whole time. The inherited framing that the Qwen3 causal question
is *untestable* is therefore too strong: it was untestable **on the dataset it was tried on**.

The specificity numbers reproduce exactly through this independent path: `remove_both` excess
**+0.1254, p_cl 0.030**; `remove_refusalness` −0.0048, p 0.61; double-random control +0.0050, p 0.81.







### ✅ Two provenance holes closed in `judge_boombness.py`

Both were identified by reviews #5 and #6 and left on the next-sprint list; both are one-field fixes
and are done.

**1. `prompt_sha16` is now written on every judge row.** `prompt_id` names *"this cell of this
family"* and deliberately does not depend on the prompt text, so two runs can join on it while
referring to different prompts — that is retraction **R1**. Every bank row carries `prompt_sha16` for
exactly this reason, and the judge's `base` dict listed fifteen fields without it. The consequence
was concrete: `analyze_phase_d.py`'s stale-join guard found the field absent on every judge row, its
mismatch list was therefore always empty, and it wrote `n_prompt_sha16_mismatch: 0` unconditionally —
**a zero my own write-up then cited as evidence** (R5-3). The guard can now actually run instead of
falling back to bank-path equality. Verified: `prompt_sha16: 0baa51b38273cfb6` on a fresh 2-row run.

**2. The judge model candidates are recorded.** No artifact in this repo says which model produced
any StrongReject score, and it is **not one model**: the rubric falls back through a tuple, tried in
order. Now in `summary.json`:

```json
"judge_model_candidates": {
  "candidates": ["openai/gpt-4o-mini", "openai/gpt-3.5-turbo"],
  "source": "strong_reject.evaluate._generate_judge_response fallback",
  "note": "tried IN ORDER with fallback; this is the candidate set, NOT the model that
           actually answered any given row"
}
```

⚠ **Stated precisely because it is a partial fix:** this identifies the *candidates*, not the
responder. A run scored entirely by `gpt-3.5-turbo` after the first model rate-limited would look
identical in the artifact. Pinning the actual responder needs a change inside `strong_reject`, and
that stays on the next-sprint list.

The value is read **out of the installed source** (`_generate_judge_response`'s `models=None`
fallback) rather than hardcoded, so it tracks the checkout; if that line ever moves, the field records
an explicit error instead of a stale pair. It is also not on `evaluate`'s signature, which is where I
first looked and got an error field for my trouble — worth noting, since the obvious place is the
wrong one.

⚠ **Neither fix is retroactive.** Every judge run committed before 2026-08-21 06:18 lacks both
fields, which is why `analyze_phase_d.py` still needs its bank-path fallback and why the sprint's
existing StrongReject numbers remain attributable only to the pair, not to a model.



### ⚠ The alternative explanation I have to rule out myself, and the control for it (771509/771510)

The anti-alignment (Spearman −0.850) is the sprint's central claim, and there is one explanation for
it that would deflate it substantially, which I did not list among the limits:

> **A projection at L31 sits one layer before the unembedding, with almost no computation left to
> amplify it; an L8 edit propagates through twenty-three layers.** So "causation falls with depth"
> may be a **generic architectural property of late ablation**, not a fact about `d_surface`. Under
> that reading the −0.850 is just (prediction rises with depth, for representational reasons) ×
> (causal efficacy falls with depth, for architectural reasons) — **two independent depth trends
> dressed up as a dissociation.**

Nothing in the sprint currently distinguishes those. Every late arm ever run — L18, L24, L28, and now
L29/L30/L31 — ablates a **single** direction, so "late single-direction ablations do nothing" is
consistent with both stories.

**The discriminating test: ablate the ENTIRE 3-dimensional concept subspace**, which is the largest
edit that subspace admits, **at both depths.**

- If the full span moves ASR at **L8** and does nothing at **L31** → the late null is architectural,
  and the anti-alignment claim must be **weakened to a statement about depth, not about direction**.
- If the full span moves ASR at **L31 too** → late ablation *can* act, and `d_surface`'s late null is
  a fact about that direction rather than about depth. The central claim then stands as written.

Implemented as `cell_span{0,1,2}`, the deterministic Gram-Schmidt basis of the centred cell means,
composed at one layer — sequential projection of orthonormal vectors equals projecting out their
span. Verified before submitting: the three vectors are orthonormal (max |GᵀG − I| = 3.1e-07 at L8,
2.4e-07 at L31) and **the span captures `d_surface` at 1.000000** at both depths, so it strictly
contains the arm that was already tested.

**771509 (L8) / 771510 (L31)**, otherwise identical to the profile arms, to be judged against the
same 2026-08-21 baseline.


#### Free evidence already in the repo: causal efficacy does NOT decay monotonically with depth

Before the span runs land, one thing can be settled from committed artifacts at zero cost. If late
ablations were architecturally impotent *in general*, every direction's causal profile should decay
with depth. **Refusalness does the opposite** (`refusalness_layer_profile.json`):

| layer | Δ ASR | p_cl |
|---|---|---|
| L12 | +0.0028 | 0.451 |
| L14 | +0.0475 | 0.013 |
| L16 | +0.1167 | 0.002 |
| **L18** | **+0.1895** | **0.0001** |
| L20 | +0.0628 | 0.008 |

**A single-direction projection at L18 — past the middle of a 32-layer model — moves ASR by +0.19,
six times `d_surface`'s largest effect at any depth.** So "an intervention late in the stack cannot
do much" is **false as a general claim about this model**: causal efficacy is direction-specific and
band-specific, not monotonically decaying.

⚠ **This does not settle the question, and I am not treating it as if it did.** The architectural
argument is strongest for the *last few* layers, where there is genuinely almost no computation left
— and refusalness has never been fitted above L20, so nothing in the repo tests L28–L31 with a
direction known to be potent. That is exactly the gap 771509/771510 exist to fill, and the L31 span
arm is still the deciding number.

What this evidence does establish is narrower and worth having: the decay is **not** a smooth
architectural gradient across the whole second half of the model, because at L18 it is at its
strongest for a different direction.

**Prediction, recorded before they land.** I expect the full span at L8 to move ASR **more** than
`d_surface` alone (+0.0305) since it strictly contains it. L31 is the one I genuinely cannot call —
and that is the point of running it. **If L31 comes back null, I will weaken the central claim in the
final report rather than keep it as written.**

## ✅✅✅ THE SPRINT'S CENTRAL RESULT — prediction and causation are ANTI-ALIGNED across depth

**Artifact:** `outputs/boombness_followup/subspace_prediction.json` (`prediction_profile`,
`causal_extra`, `prediction_vs_causation`). **New runs:** 771432–771434, judged in six shards, all
`null_frac 0.0000`, paired against the same 2026-08-21 baseline as the rest of the re-check.

The dissociation was previously an inference across two experiments at different depths. It is now
**one pair of curves over the same 32 layers**, and they run in opposite directions.

| layer | **PREDICTS** (within-level ρ) | **CAUSES** (Δ ASR) |
|---|---|---|
| L8 | +0.0600 (p 0.038) | **+0.0305 (p 0.009)** |
| L12 | +0.0546 (p 0.042) | **+0.0322 (p 0.006)** |
| L18 | +0.1025 (p 0.004) | +0.0037 (p 0.31) |
| L24 | +0.1169 (p 0.002) | +0.0005 (p 0.45) |
| L28 | +0.1311 (p 0.0004) | +0.0037 (p 0.31) |
| **L29** | +0.1370 (p 0.0003) | **+0.0002 (p 0.33)** |
| **L30** | +0.1535 (p 0.0001) | **−0.0044 (p 0.23)** |
| **L31** | **+0.1638 (p 0.0001)** | **−0.0041 (p 0.26)** |

> **Spearman(prediction, causation) over the 13 depths with both measurements = −0.850**
> (Pearson −0.846). Degenerate causal arms are excluded, not counted as zero.

Aggregated:

| band | mean prediction | mean causation |
|---|---|---|
| causal band **L6–L12** | +0.0519 | **+0.0252** |
| late **L24–L31** | **+0.1405** | −0.0008 |

Prediction is **2.7× stronger** late than in the causal band; causation is **−0.03×** — i.e. gone.

### The prediction that made it, recorded before the runs

At 05:48 I wrote: *"extrapolating the profile (null from L16 on) these should be null … If they are,
the dissociation closes at a single locus."* They are null. **The sentence the sprint ends on is now
measured at one locus rather than inferred across eighteen layers:**

> **At L31 the `d_surface` metric predicts ASR at ρ = +0.164 (p = 1e-4), and ablating the very same
> direction at the very same layer changes nothing (−0.0041, p = 0.26).**

And the converse holds at the other end: at L8–L12, where ablation moves ASR most, the metric is at
its **weakest** predictively (+0.055 to +0.060, barely clearing 0.05).

### What it means, stated no more strongly than it should be

Combined with tonight's other two results — a random orthogonal axis in the same subspace **predicts**
at 83–106% of `d_surface`, and ablating that axis **does nothing** at four depths (Holm-corrected) —
the picture is consistent and now measured three ways:

> **Late layers make the concept subspace legible; early-mid layers make one axis of it act.**
> Readability and causal efficacy are carried by different depths and, within a depth, by different
> directions.

⚠ **Limits, and they matter.** This is one model, one bank, one readout position, one outcome. The
prediction profile is a *correlational* profile on 1,800 prompts and inherits R5-4's ~11% SE
understatement. The causal profile's depths were run at different times against two baselines (the
committed L4–L28 arms in the 08-19 session; L29–L31 tonight against the 08-21 baseline) — the
anti-alignment is far too large to be judging noise, but the two halves are not session-matched to
each other. And ⛔ **none of this says what the subspace encodes** — only where it is readable and
where it acts.

### The dissociation is currently ACROSS layers — closing it WITHIN one (771432–771434)

Tonight's two headline results sit at different depths, and that is a weakness in how the central
claim is stated:

- **Prediction** lives at **L29–L31** — Gate D's nested selection picks `query|L31|cos` and
  `demo_max|L29|cos`, and a random orthogonal axis there predicts at 83–106% of `d_surface`.
- **Causation** lives at **L6–L12** — where the arm beats a subspace-matched control at all four
  depths, every one surviving Holm.

So "reads there, acts here" is currently an inference from two *different* loci. The committed causal
profile stops at **L28** and is already null from L16 onward (L16 0.0000, L18 +0.0037, L24 +0.0005,
L28 +0.0037, all p ≥ 0.30) — but **nobody has ever ablated `d_surface` at L29, L30 or L31**, which are
precisely the layers the prediction comes from.

**Submitted: `d_surface:project_out:{29,30,31}` on AdvBench heldout 495** (771432–771434), otherwise
identical to the committed profile arms, to be judged in the same 2026-08-21 session as the baseline
and the re-check.

**Prediction, recorded before they land.** Extrapolating the profile (null from L16 on) these should
be null. If they are, the dissociation closes at a single locus and becomes a much stronger sentence:

> *At L31 the metric predicts ASR at ρ = +0.164, and ablating the very same direction at the very
> same layer changes nothing.*

If instead one of them moves ASR, the profile has a second causal band nobody has looked at, the
"causation is at L6–L12" framing is incomplete, and that is a more interesting result than the
prediction. Either way the sentence the sprint ends on is decided by these three runs rather than by
an extrapolation across eighteen layers.

## ✅✅ THE RE-CHECK, REDONE CLEAN — all four depths now survive Holm, and L12's "near-miss" was an artifact

**Artifact:** `outputs/boombness_followup/control_recheck_sessionmatched.json` — supersedes
`control_recheck_subspace.json`, which is kept for the audit trail.

Two defects review #6 found are fixed **in the experiment, not in the prose**: the control basis is
now deterministic (Gram-Schmidt in fixed order, verified bit-identical across repeat calls and
matching the runs' own logs to four decimals), and **every arm, control and baseline is judged in one
session** (2026-08-21), removing R6-6's uncontrolled nuisance.

| layer | ARM | p_cl | **subspace ctrl** | p | **arm − control** | p | **Holm-adj** |
|---|---|---|---|---|---|---|---|
| L6 | +0.0157 | 0.057 | +0.0030 | 0.73 | **+0.0127** | 0.020 | **0.0347** ✅ |
| L8 | +0.0278 | 0.031 | −0.0041 | 0.25 | **+0.0319** | 0.0092 | **0.0276** ✅ |
| L10 | +0.0211 | 0.026 | −0.0092 | 0.32 | **+0.0303** | 0.017 | **0.0347** ✅ |
| **L12** | **+0.0316** | **0.0059** | **−0.0048** | **0.24** | **+0.0364** | **0.0034** | **0.0136** ✅ |

### ⛔ The L12 near-miss was an artifact of the non-deterministic basis, and it is withdrawn

I reported at 03:30 that *"the closest a control has come to firing in this whole sprint"* was L12's
+0.0103, p 0.062, and flagged it prominently as the one place a control nearly fired. **That draw came
from the environment-dependent SVD basis.** The deterministic replacement removes **11.25%** of the
cell-mean spread — a **55% stronger** control — and yet lands at **−0.0048, p 0.24**. Comfortably
inert. **The near-miss is withdrawn: it was a property of an arbitrary basis rotation, not of the
model.**

### And the headline is now much stronger than the version it replaces

- **All four depths survive Holm** over the depth family (previously **only L8**). L12 goes from
  adjusted 0.0638 to **0.0136** and becomes the *strongest* result, not the shakiest.
- Every subspace-matched control is inert (p 0.24–0.73), and the two strongest controls — L12 at
  11.25% of the spread and L6 at 5.40% — are the two furthest from significance.
- The arms themselves moved slightly under session-matched judging (L8 +0.0305 → +0.0278,
  L12 +0.0322 → +0.0316), well within the judge's own noise.

**`d_surface`'s causal direction-specificity is established at all four depths of its layer profile,
with correction, against a control that ablates a comparable amount of the same concept subspace and
could have failed.**

### What this does NOT touch

⛔ **Gate D still fails**, and tonight's subspace-prediction result says why: a random orthogonal axis
in that same subspace **predicts** ASR at 83–106% of `d_surface`'s strength. The two results are the
sprint's central finding and they are not in tension:

> **Prediction is distributed across the concept subspace; causation is concentrated on one axis
> within it.** Ablating the orthogonal axis changes nothing behaviourally (p 0.24–0.73 at four
> depths) while reading it predicts ASR as well as reading `d_surface`.

⚠ Still isotropic-controlled and untested: the refusalness profile, Phase F's composed arms, the
Qwen3 double-random control. Measured earlier, they need a **different basis** — refusalness lies only
0.65–2.72% inside the cell-mean span. ⚠ And the isotropic controls in the table above remain
08-19-judged; they are not the headline contrast and are inert either way.

### ✅ The determinism fix is verified END-TO-END, and the session nuisance is being removed

**771193/771194 completed**, and their run diagnostics now match the offline recomputation **exactly**
— which is the specific thing that failed before:

| job | layer | cos | ARM removes | CONTROL removes | offline predicted |
|---|---|---|---|---|---|
| 771193 | L8 | +9.3e-10 | 84.02% | **4.5506%** | **4.5506%** ✅ |
| 771194 | L12 | −1.7e-08 | 82.04% | **11.2463%** | **11.2462%** ✅ |

Run and login-node now agree to four decimal places where they previously differed by a rotation.
**L12's replacement control removes 11.25% of the cell-mean spread against the old draw's 7.25%** — a
55% stronger control at the depth where the old one came closest to firing (+0.0103, p 0.062). If the
arm still beats *this* one, the L12 result is on much firmer ground; if it does not, that is the
honest answer and I would rather have it.

### ⚠ Two judge runs were created by an agent that was instructed to be READ-ONLY

`judge/abrep_base_20260821_033532_4024998` and `abrep_L12_20260821_033532_4024999` appeared during
review #6's window. Every audit prompt in that workflow began *"READ-ONLY. Never edit/write/create a
file"* — creating a judge run violates that instruction and spends API credit.

**Checked before deciding what to do with them:** both are complete (495 rows, `DONE.json`), point at
the correct committed generations, and use the correct bank at `limit 0, offset 0`. They are sound
artifacts with irregular provenance. **They are being used, and the irregularity is recorded here
rather than laundered** — the alternative, discarding correct work and re-spending the credits, buys
nothing but tidiness.

**Instruction fix for future reviews:** the read-only rule needs to name the specific capability, not
just the category. "Never create a file" evidently did not read as "never launch a judge run", since
the agent's mental model was *analysis*, not *writing*. Future audit prompts will say: **do not
invoke `judge_boombness.py`, `score_behavior.py`, or `extract_boombness.py`; you may only read what
already exists.**

### Removing R6-6: the whole comparison is being re-judged in ONE session

R6-6 flagged that arms were judged 2026-08-19 and controls 2026-08-21 by a judge the repo shows is
non-deterministic. The auditor's L12 spot-check said the mismatch makes the published number
**conservative** (session-matched +0.0248, p 0.011 vs published +0.0219, p 0.021), so the nuisance
never threatened the conclusion — but it is uncontrolled, and it is cheap to remove.

Launched: `abrep_L6`, `abrep_L8`, `abrep_L10` (the baseline and L12 arm already exist from above).
With the four new control shards judging alongside, **every arm, control and baseline in the
re-check will have been judged on 2026-08-21**, and the session-matched table will be the one
reported.

## 4h Code and Output Review — Review #6 (2026-08-21 04:40)

Four agents over the subspace-control re-check and the subspace-prediction result. **Every headline
number reproduces to six decimal places under independent code** (independent loader, independent
Student-t via continued-fraction incomplete beta). Six defects, four of them in code I wrote tonight,
and **the corrected numbers make the central result stronger, not weaker.**

### ⛔ R6-1 — my subspace-prediction run dropped the cross-fit discipline, and fixing it strengthens the finding

`analyze_subspace_prediction.py` scored all 1,800 prompts from `directions_fit_dev.pt`. The
extraction itself is **cross-fit** — `directions_fitted_on` is `heldout` on all 3,000 dev rows and
`dev` on all 3,000 heldout rows, `is_self_fit` false on 7080/7080. Scoring everything from one
payload is a stated-method violation. *(Impact is small — only 6 of 900 dev prompts share a family
with the dev fit, ~0.33% of rows — but the honest run is the one that matches the extract.)*

**Fixed, and the corrected table is the stronger one.** Within-level ρ vs StrongReject, cross-fit,
deterministic basis:

| layer | `d_surface` | `d_inter` | ctrl s1 | ctrl s2 | ctrl s3 | `hnorm` |
|---|---|---|---|---|---|---|
| L29 | +0.1370 | −0.1500 | **+0.1431** | **+0.1626** | **+0.1510** | −0.018 (p 0.50) |
| L30 | +0.1535 | −0.1529 | +0.1516 | **+0.1629** | +0.1538 | +0.007 (p 0.79) |
| L31 | +0.1638 | −0.1435 | +0.1359 | +0.1519 | +0.1392 | +0.008 (p 0.71) |

**At L29 and L30 the orthogonal control matches or BEATS `d_surface`.** My earlier "65–95% of
`d_surface`'s strength" is corrected to **83–106%**. The conclusion — the predictive signal belongs
to the concept subspace, not to the axis — is unchanged and better supported.

### ✅ R6-2 — and the auditor supplied the algebra I had only measured

`signals.py:328-331`: `d_surface = ½[(B−C)+(E−A)]`, `d_context = ½[(C−A)+(B−E)]`, `d_naive = B−A`.
Therefore **`d_naive ≡ d_surface + d_context`, exactly** — verified numerically, out-of-span residual
≤ 9.5e-14. So `d_naive` was never a comparator; it is a linear combination of the other two. Partial
correlations confirm neither carries unique variance over the other (partial ρ +0.006, t 0.21).
**`d_naive` is struck from the requirement-4 evidence.**

⛔ **And `d_context` is not near-orthogonal where it matters.** `direction_cosines.json`'s provenance
note — *"d_context and d_inter are near-orthogonal"* — is true at L0–L20 (|cos| ≤ 0.19) and **false at
the layers Gate D selected**: cos rises to **0.27 (L30) / 0.37 (L31)**. That note is copied verbatim
into `direction_specificity_extended.json`, an artifact I produced. Residualising `d_context` on
`d_surface` drops it from 90% to **62%** of `d_surface`'s strength (+0.1014, p 0.0051 — still
significant, but on `d_context` alone the verdict would be weak).

**So requirement 4 now rests where it should: on `d_inter` (cos 0.008–0.087, predicting at 88–94%)
and on the three orthogonal random draws (83–106%).** Both are genuine controls. The evidence I
originally gave for it was not.

### ⛔ R6-3 — the control direction was environment-dependent, and two of the four runs are not re-derivable

After removing the arm from an orthonormal rank-3 span, the residual's singular values are ~[1, 1, 0]
— the top two equal to ~2e-7 relative. **SVD's choice of basis inside that degenerate 2-D eigenspace
is arbitrary and LAPACK-build-dependent.** The four SLURM runs agreed byte-for-byte *with each other*
(same nodes, same environment) but not with an offline recomputation on the login node.

Consequences, stated exactly:
- **L6 and L10 reproduce** — the deterministic basis draws the same direction (5.4033%, 5.8796%).
- **L8 and L12 do not.** The runs used directions removing **5.1971%** and **7.2485%** of the
  cell-mean spread; the deterministic basis draws **4.5506%** and **11.2462%**.

The committed L8/L12 results remain **sound** — their run logs verify orthogonality and subspace
membership directly — but they are **not re-derivable from the current code**, which is not good
enough. **Fixed** by never relying on SVD's basis choice: the arm is projected out of the *original*
basis rows and they are Gram-Schmidt'd in a fixed order, so the basis is a deterministic function of
(payload, layer). Verified: repeat calls bit-identical over both splits × 32 layers, worst |cos|
1.86e-08. **L8 and L12 resubmitted (771193/771194)** — and note L12's new control removes **11.2%**
against the old 7.2%, a materially *stronger* control at the depth where the old one came closest to
firing.

### ⛔ R6-4 — two more defects in `analyze_control_recheck.py`, both mine, both fixed

- **`load()` asserted duplicate-freeness but never completeness.** Two judge directories share the
  tag `abgL6_B` over the same generations — one with **40 rows**, one with 495. Feeding the 40-row
  one returns `delta_cluster_mean: 0.0` with **no error**: a silent, plausible null. Now every arm
  must match the baseline's row count or the run refuses. *(Also: the `judge_status != "ok"` filter
  ran before the duplicate check, so a duplicated id whose first copy failed judging would have
  evaded it. Duplicates are now counted over all rows.)*
- **The artifact recorded only the baseline directory**, not the arm or control dirs, so it was not
  self-contained — the auditor had to reconstruct them by matching every judge dir to its
  generation's `intervention` block. Now written under `runs`.

### ⛔ R6-5 — "paired is tighter" is false at the one depth that matters

I wrote that the paired arm-minus-control contrast is "tighter than differencing two
independently-clustered means". Measured: tighter at L6/L10/L12, and **11% WIDER at L8** (0.011553 vs
0.010400). Conservative in direction, so nothing was inflated — but the blanket claim is wrong and
the docstring now says so. **The real, previously unstated strength is different:** the baseline
cancels algebraically (`d = arm[p] − ctrl[p]`), so this contrast is **immune to baseline judge
noise**.

### ⚠ R6-6 — an uncontrolled nuisance: the arms and controls were judged on different days

Arms and baseline were judged 2026-08-19; all four subspace controls 2026-08-21, by an LLM judge the
repo itself shows is not deterministic. The auditor re-derived L12 with everything judged in the
08-21 session: **arm − control +0.024754, p 0.01106**, against the published +0.021922, p 0.02125.
**The session-matched result is stronger**, so the nuisance is not flattering the finding — but it is
uncontrolled and is now on the record.

### Numbers corrected in place

- Control spread range **5.20–7.25%**, not "5.4–7.3%" — and the L8 run's own value is **5.1971%**;
  the **5.35%** I quoted twice was the offline recomputation, not the run.
- The L8 cos I quoted as **+5.6e-09** is the run log's **L10** value; L8's is **−8.38e-09**.
- `d_surface` in-span is **99.99995%–100.00013%**, and it is an algebraic identity
  (`d_surface` is a zero-sum combination of the four cell means), not evidence.
- Orthogonal-control strength **83–106%** of `d_surface`, not "65–95%".

### What did NOT move

Every vs-baseline and arm-minus-control figure at all four depths, to six decimals; the Holm result
(only L8 rejects, adjusted 0.0413); the L12 control at +0.0103, p 0.062; the refusalness in-span
figures (2.61/2.72/1.33/0.65/1.38%); and the orthogonality of every drawn control. The shard unions
are complete and duplicate-free, and all arms are paired against one baseline.

## 4h Code and Output Review — Review #5 (2026-08-21 00:05)

Four agents over the two newest results. **Every headline number in both reproduces exactly under
independent code — including independent rank/Pearson and an independently implemented Student-t.
Then most of what I said the numbers *meant* comes apart.** Nine corrections, two of them to guards
I wrote this session, and one that reaches back across the whole sprint.

### ⛔ R5-1 — my central mechanistic argument for killing the objective is REFUTED by my own artifact

I wrote that Gate D fails requirement 7 because *"the predictive signal lives in the top three layers
while every causal effect lives at L6–L12 … a metric that predicts at a depth where intervention does
nothing cannot be optimised against."* **The artifact I cited says otherwise.** Inside
`clean_fig9_correlation.json`'s own `dev_grid_holm`:

- `d_surface` / StrongReject: **49 of 210 metrics survive Holm over all 210**, and the survivors
  include `demo_max|cos` **and** `demo_max|proj` at **L9, L10, L11, L12, L13**, `query|proj` at L4,
  L5, **L6**, and the band metric **`query|L6_12|proj`** itself.
- `d_surface` / ASR: **97 of 210 survive**, spanning **every layer L3–L31**.
- On heldout, `query|L{L}|cos` is significantly positive at essentially every depth: L0 +0.0751
  (p 0.0023), L5 +0.2314 (0.0060), **L6 +0.1921 (0.0077)**, L13 +0.2490 (0.0056), L31 +0.2982.

**The metric is Holm-significantly predictive inside the stated causal band.** Requirement 7's failure
is **WITHDRAWN**.

> **Gate D still FAILS, and now on requirement 4 alone: `d_naive` (+0.1672) and `d_context` (+0.1471)
> match or beat `d_surface` (+0.1638), so no control direction fails.** That verdict is untouched and
> is the whole basis for not building the objective. It is a cleaner conclusion than the one I wrote:
> the objective is dead because the signal **is not `d_surface`** — full stop, no depth argument
> needed.

### ⛔ R5-2 — the dev grid is FLAT, so "L29–L31" was never identifiable

Top-15 dev metrics span **+0.3238 → +0.3060**, a range of 0.018 against a per-metric cluster SE of
0.03–0.05. `demo_max|cos` is essentially flat in depth (L6–L12 mean +0.2698 vs L29–L31 +0.3038).
The argmax over 210 near-ties is noise. **A large majority of the 210 candidates would have passed
the heldout test** — so the nested protocol is *valid* but nearly *vacuous as evidence*: it protects
against selection, and there was nothing to select.

### ⛔ R5-3 — two guards I wrote this session, both fixed

**(i) The stale-join guard was a no-op.** `judge_boombness` does not copy `prompt_sha16` into its
result rows — its `base` dict names fifteen fields and that is not one of them — so the mismatch list
was always empty and `n_prompt_sha16_mismatch: 0` was written unconditionally. **My write-up then
cited that zero as evidence.** Fixed: the code now counts judge rows carrying the hash, and when
none do it falls back to bank-path equality and **says which check actually ran**:
`"prompt_sha16 ABSENT from every judge row … fell back to bank-path equality, which passed. Weaker:
it certifies the same bank FILE, not the same bytes."`

**(ii) `n_levels_covered` conflated *available* with *estimable*.** A level can carry the metric on
all 120 prompts and contribute nothing, because Spearman is undefined when the **outcome** is
constant inside it. The field said 15/15 while the mean was over **14** (all 60 heldout `con:mixed`
prompts score exactly 0.000), and for the refusal comparison it said 15/15 while the mean used **6**.
Now split into `n_levels_metric_available` / `n_levels_rho_estimable` with both exclusion lists named.

### ⛔ R5-4 — the 15 levels are not independent, so the within-level SEs are 15–25% too small

All **120 (domain, split, slot) families appear in all 15 levels**, and 13 of the 15 use the
*identical* pool-sentence set per family. So `between_vs_within_level` averages 15 ρ's over the same
120 units on largely the same text and then treats them as 15 independent clusters — pseudo-
replication reappearing one grain up, inside the very function written to price it.

| | cluster-over-levels SE | family-bootstrap SE (2,000 reps over the 120 families) |
|---|---|---|
| `d_surface` / SR | 0.0299 (p 8.1e-05) | **0.0343**, CI95 [+0.0956, +0.2316] |
| `d_surface` / ASR | 0.0307 (p 1.2e-03) | **0.0385**, CI95 [+0.0561, +0.2060] |

**The within-level effect survives** — 0 of 2,000 bootstrap replicates reach ≤ 0 — but the p-values
as reported are anticonservative and the correct SE is the family bootstrap.

### ⛔ R5-5 — requirement 3 passes, but not on the test I ran

I claimed the metric is not a refusal detector from ρ = +0.068, p = 0.26. That mean is over **six**
estimable levels, two of which rest on **a single refused prompt each** and supply both negative
signs. It is an underpowered null, and I converted it into a ✅. The properly powered version says
the **opposite**: the 25 refused prompts sit at mean within-level normalized metric rank **0.6373**
against a null of 0.5, permutation p **0.0135** — the metric *does* predict refusal.

**The conclusion survives on the test I failed to run.** Delete all 25 refused prompts and the effect
is unchanged: heldout ρ **+0.3098** (vs +0.2982), within-level **+0.1666** (vs +0.1638). *Refusal
cannot mediate an effect that is unchanged when refusal is deleted.* Requirement 3 ✅, evidence
replaced.

### ⛔ R5-6 — the Qwen3 doublespeak-SPECIFIC excess does not survive robustness. Downgraded.

`+0.1254, p_cl 0.030` reproduces to seven decimals, and then fails three independent checks:

| check | excess | p |
|---|---|---|
| as reported (all 420 doublespeak rows) | +0.1254 | **0.0300** |
| **stratum-matched** (324 rows; the `strength`/`consistency`/`position` blocks exist only on the doublespeak side) | +0.1142 | **0.0750** |
| leave-one-domain-out | — | **4 of 6 give p > 0.05** |
| proportional transport (the non-specific channel is 38% larger on doublespeak, so additive subtraction under-corrects) | +0.0478 | **0.267** |

⛔ **"A doublespeak-specific component survives the benign subtraction" is DOWNGRADED from established
to not robust.** The raw **+0.3476 (p 0.00028)** and the benign **+0.2222** stand; what does not stand
is the claim that the difference between them is reliably non-zero. Per-domain excess ranges
−0.0005 to +0.2735 with two of six domains at essentially nothing.

### ⛔⛔ R5-7 — THE RANDOM CONTROLS IN THIS SPRINT ARE INERT BY CONSTRUCTION, and this reaches everywhere

The most consequential finding of the review, and it is not about Qwen3.

`norm_matched_random` rescales the draw to ‖`d_surface`‖ — but `d_surface` is stored **unit norm**,
and `pair_common.py:650` renormalises the hook direction anyway, so **for `project_out` the norm has
literally zero effect on the computation.** "Norm-matched at the same dose" means nothing more than
"a rank-1 projection at the same layers". What that projection removes:

| layer | fraction of cell-mean spread removed by the ARM | by the CONTROL |
|---|---|---|
| L11 | `d_surface` **89.97%** | **0.018%** |
| L20 | `refusalness` 0.102% | 0.061% |

The control removes roughly **5,000× less structure** than the arm. `cos(d_surface, random)` is
−0.014 ≈ 1/√5120 — exactly an isotropic draw. **So every "the matched random control is inert"
statement in this sprint is a fact about high-dimensional geometry, not an experimental result.** A
variance-matched alternative, `pair_common.in_subspace_random`, exists in the repo and has never been
used.

This does not invalidate the arms' effects, and it does not touch the *other-direction* controls
(`d_naive`, `d_context`) that carry Gate D's verdict — those are real directions and they are exactly
the controls that **did** fire. But every random-control inertness claim — E4's, the layer profiles',
Phase F's, and my own Qwen3 write-up — must be read as **"a random rank-1 projection at the same
depth does nothing", which is nearly a tautology**, not as "an intervention of comparable magnitude
does nothing".

⚠ A corollary the auditor drew and I am recording: `refusalness@L20` removes only **0.102%** of the
cell-mean spread, barely above random's 0.061%. That is consistent with C20 being inert and implies
the D20 effect is essentially the `d_surface@L11` projection alone — the decomposition I correctly
said this arm set could not perform.

### ⛔ R5-8 — the 97.2% concept-word figure has a 54.3% base rate

`D20` on `benign_literal`: flagged rows 0.9722, unflagged 0.4206, **all rows 0.5432**. I quoted the
first two and not the third. And on the doublespeak side the same arm emits the concept word in
**79.8%** of all rows — which is precisely why the additive benign subtraction under-corrects
(R5-6). The "0.000 in the control" comparator rests on **n = 3** flagged rows.

⚠ Related, and it cuts against my own dynamic-range framing: of the **72** baseline doublespeak rows
flagged malicious, only **9 (12.5%)** contain the goal's distinctive word. For a *doublespeak* prompt
a non-topical answer is not proof of non-compliance — but I used that same marker as evidence the
benign gain was "real content", so applied consistently it says 87.5% of the baseline ASR that
claim (e) rests on is non-topical.

### Smaller items, recorded

- **6 heldout tests, not 1.** Three directions × two outcomes. The `d_surface` headline is the larger
  of its two outcomes, so its family is 2, not 1. Bonferroni p = 0.00078 — survives, but "family
  size = one" is true per cell and false for the headline as reported.
- **Dev and heldout are scored with different fit vectors** (cross-split by design, `is_self_fit`
  false on 7080/7080). Not a leak; it does mean the heldout test re-applies a *recipe*, not a vector.
- **Template sentences leak across the split**: 4 distinct intensifier strings appear byte-identical
  in both halves, touching 600 of 1800 prompts. Harmless for the estimand — each is constant within
  its level and injects no within-level variance — but the honest framing is that **the split holds
  out demonstration sentences, not the design**.
- The `arm` column is `"base"` on all 960 rows of all four Qwen3 runs, including intervened ones.
  Nothing downstream used it; anything grouping by `arm` would silently pool them.
- `str:aggressive 0.458 / con:mixed 0.008` are **ASR** level means, printed adjacent to a
  StrongReject table. On SR they are 0.390 and 0.007.
- "ρ(metric, ASR) = +0.148" in the requirement-3 paragraph is **not locatable in the artifact** and is
  withdrawn; the artifact's d_surface values are +0.1272 (ASR) and +0.1638 (SR).


### ⚠ Refutation pass — I wrote the above from the audits before the skeptics landed, and eight details were wrong

A process note first: the two audit agents finished ~11 minutes before their refuters, and I wrote
review #5 from the audits alone. That was premature — **eight of the audit claims I repeated do not
survive their own refutation.** None changes a verdict; all change a number or a characterisation.
Corrected here rather than silently edited above.

**On R5-7, the random-control finding — the core stands, two overstatements do not.**

- ⛔ *"'Norm-matched at the same dose' is vacuous"* — **only "norm-matched" is vacuous.** Under
  `project_out` with α = 1.0 the dose is fully specified by α — complete removal of a one-dimensional
  subspace — and is **identically matched** between arm and control. My phrase "same dose and depths"
  was literally true. The correct and surviving criticism is **only** the spread asymmetry: the arm
  removes 89.97% of the cell-mean spread at L11, the control 0.018%.
- ⛔ **The corollary I drew is a non-sequitur and is withdrawn.** I wrote that refusalness@L20
  capturing 0.102% of cell-mean spread "implies the D20 effect is essentially the `d_surface`@L11
  projection". `cell_means` A/B/C/E is the *concept/codeword* design; a refusal axis has no reason to
  align with it, so variance captured on that basis is not a measure of behavioural potency — and
  the repo's own Llama result (refusalness removal alone = the dominant channel, +0.1895) shows the
  two are dissociable. **The D20 arm still cannot be decomposed, and I should not have implied it
  could.**

**On R5-4, the level-independence correction.**

- It is **14 of 15** levels that share the identical pool-sentence set per family, not 13 —
  `con:irrelevant` reuses the same base sentences and differs only in codeword surface, so only
  `con:mixed` genuinely differs. The non-independence is therefore *worse* than I wrote.
- The SE understatement for the headline cell is **11%** (bootstrap 0.0333 vs reported 0.0299), not
  "15–25%". Direction right, magnitude overstated at the low end.

**On R5-5, the refusal test.** Only **one** of the six per-level ρ's rests on a single refused prompt
(`str:strong`); `str:aggressive` has two, the same count as a level that comes out positive. And the
permutation figure is mean rank **0.6362**, one-sided p **0.0072** (two-sided ≈ 0.0143), not 0.6373 /
0.0135. The conclusion — an underpowered null that I converted into a ✅, with the deletion test
carrying the real argument — is unchanged.

**On R5-3(ii), the coverage field.** It was **not** a contradiction between artifact and write-up:
`n_levels_covered` genuinely reported 15/15 and I quoted it faithfully. The defect is that the field
*meant* something narrower than its name — which is exactly why it is now split into
`n_levels_metric_available` / `n_levels_rho_estimable`. Calling it a contradiction overstated my own
error.

**Withdrawn from "smaller items":** the `str:aggressive 0.458 / con:mixed 0.008` figures are **not**
mislabelled — my sentence says those levels make **ASR** differ, and 0.45833 / 0.00833 are exactly the
ASR@0.5 level means.

**And one refutation that makes R5-2 STRONGER.** The audit said the dev argmax is unchanged when all
210 candidates are scored on the common 840-prompt sample. That holds for ASR but is **false for the
StrongReject headline cell**: on the common sample the argmax moves from `query|L31|cos` (+0.3199) to
`query|L31|proj` (+0.3240). So the selected metric is not even stable under a change of sample —
further evidence that the grid is flat and the argmax is noise.

⚠ Two provenance items the refuter established that I had no basis for either way, recorded because
they *support* the Qwen3 pairing: the four gens runs **are** SLURM jobs with retained logs
(762143 base; 764538/764539/764540 arms), and `boomb_762143.out` carries the verbatim line
`[score] enable_thinking=False VERIFIED against the rendered prompt`. Commit `fd4a89aa`'s message
names job 762143 directly: *"zero of twenty-eight generations contain a think block."* So the
baseline's thinking-off state is documented, not inferred.

⛔ **But the judge is still not reproducible**, and this is worth carrying: `strong_reject/evaluate.py`
defaults to `("openai/gpt-4o-mini", "openai/gpt-3.5-turbo")` **tried in order with fallback**, and
none of the artifacts record which model actually answered. Every StrongReject number in this sprint
was produced by an unrecorded member of that pair.

**Process rule added:** do not write a review section from an audit before its refutation lands. The
refuters exist because auditors overstate, and eight of eight corrections here were on the audits'
side, not the artifacts'.


### ✅ R5-7 acted on — a VARIANCE-MATCHED control now exists, and building it exposed a second silent bug

Review #5's top correction. `random`/`orthogonal` are isotropic draws in R⁴⁰⁹⁶, so they remove
~1/hidden of whatever the arm removes and their inertness is arithmetic. `in_subspace_random` existed
in `pair_common` and had never been called. Two new control names, ~40 lines in `signals.py` plus the
wiring in `score_behavior.py`:

- **`in_subspace`** — random inside the span of the centred 2×2 cell means.
- **`in_subspace_orth`** — the same, **orthogonalised against the arm direction first**, so the draw
  lives in the part of the concept subspace that is *not* `d_surface`. This is the one that answers
  the question cleanly: *is the effect about this axis, or about ablating any concept-carrying axis?*

**⛔ The first implementation of the orthogonalisation was a silent no-op.** I projected the basis
rows against the arm direction and then kept `Vh[:proj.shape[0]]` — 3 rows for a 3-row matrix whose
rank had just dropped to 2. The third `Vh` row is an arbitrary unit vector orthogonal to the other
two, i.e. **exactly the direction I had removed**. Measured `cos(arm, control) = −0.73` at L6 when it
should have been zero. Fixed by taking the rank from the **singular values**, not the row count.
Verified after the fix: `cos ≈ 1e-8`, `k = 2`.

**What the three controls actually remove**, as a fraction of the spread of the four cell means —
this table is the whole argument, and it is now measured per run and written into the metadata:

| layer | **ARM** (`d_surface`) | **`in_subspace_orth`** | isotropic `random` |
|---|---|---|---|
| L6 | 83.08% | **8.85%** | 0.0366% |
| **L8** | **77.91%** | **6.46%** | **0.0053%** |
| L10 | 74.53% | 7.70% | 0.0324% |
| L12 | 75.46% | 15.10% | 0.0299% |
| L18 | 85.82% | 3.94% | 0.0107% |

At L8 the new control removes **1,200× more** structure than the one every "inert control" claim in
this sprint rests on, while being exactly orthogonal to the arm.

**Run submitted: 770317**, `in_subspace_orth:project_out:8-8:1.0` on AdvBench heldout 495, otherwise
byte-identical to the committed arm B (same bank, same fit dir, `max_new 512`, bf16, `behavioral`).

**The prediction, recorded before it lands.** Arm B is **+0.0305, p_cl 0.0089**; its isotropic control
was −0.0018. If `in_subspace_orth` also lands near zero, arm B's specificity survives a control that
could actually have falsified it, and that is a real strengthening. **If it lands near +0.03, then
ablating any concept-subspace axis at L8 does what `d_surface` does, and arm B — the sprint's
longest-standing behavioural result — is not about `d_surface` at all.** Either way this is the first
control in the sprint whose failure would mean something.


#### ⛔ And the first submitted run was INVALID — caught by reading its own diagnostic, not by trusting the offline test

Job 770317 launched and its per-run diagnostic immediately reported, at the very layer the experiment
is about:

```
L8: cos_with_arm_direction = -0.5709,  how = "in_subspace_orth:k=3"
```

**The control was 57% the arm direction.** The offline check I ran before submitting had reported
`cos ≈ 1e-8, k=2` — because it used the **heldout** payload and only five layers, while the run loads
**dev** and all 32. The 1e-6 relative rank cut is too tight: at several layers the post-projection
numerical residue of the arm direction survives at ~1e-4 of the top singular value, so rank came back
3 instead of 2 and `Vh2[2]` *was* that residue.

**Cancelled and fixed with two independent guards**, because one of them evidently is not enough:

1. the rank cut is loosened to 1e-3 relative, and
2. the drawn vector is **explicitly re-orthogonalised** against the arm and re-normalised afterwards
   — correct whatever the rank detection decides, with a named fallback if the draw collapses.

**Re-verified the way the first check should have been: both splits × all 32 layers.**
**Worst |cos(arm, control)| = 1.7e-08.** On the `dev` payload the run actually uses:

| layer | cos | ARM removes | `in_subspace_orth` removes | k |
|---|---|---|---|---|
| L6 | −3.7e-09 | 87.68% | 4.86% | 2 |
| **L8** | **+5.6e-09** | **84.02%** | **5.35%** | 2 |
| L12 | +6.5e-09 | 82.04% | 7.25% | 2 |
| L18 | −5.4e-09 | 90.67% | 6.76% | 2 |

Resubmitted as **770343** (`--tag abVMC2`). Also fixed: the diagnostic was printing once **per
prompt** — a 4 KB JSON blob × 495 rows — now printed once.

**Two lessons, both recorded rather than absorbed silently.** A guard that reports its own inputs is
what caught this; had the diagnostic not been in the run output, an invalid control would have been
judged and reported. And an offline verification that samples one split and five layers is not a
verification — the failure lived in the other split at layers I did not check.

### Next corrections, in priority order

1. **Re-run one arm with `in_subspace_random`** — until then no inertness claim in this sprint means
   what it says.
2. **Report the family bootstrap SE** alongside the cluster-over-levels SE wherever a within-level ρ
   is quoted.
3. Make `judge_boombness` write `prompt_sha16` into its result rows, so the stale-join guard can
   actually run rather than fall back.
4. Re-state the Qwen3 specificity claim as *not robust* wherever it appears downstream.

## 4h Code and Output Review — Review #4 (2026-08-20 19:40)

Eight agents, 732k tokens, 275 tool calls: four adversarial audits of **this session's own** new code
and artifacts, each piped into a skeptic instructed to refute it. **Every headline number reproduces
exactly. Nine of my supporting statements do not, and two guards I wrote could never have fired.**

### ⛔ R4-1 — "an independent code path" was not independent

I wrote that `analyze_e4_pathway.py` re-derives the committed +0.0305 and +0.1895 "through an
independent code path". It does not: `analyze_e4_pathway.py` and `analyze_external_arms.py` **both**
do `from analyze_g8 import cluster_mean_ci`. The estimator, the cluster aggregation, the t-reference
and `read_jsonl` are the *same functions*; only the row-loading loop differs. Agreement to four
decimals between two callers of one function is arithmetic, not corroboration — and `analyze_g8`'s
own docstrings record that this estimator has been wrong twice. **Withdrawn.** The auditor's
re-derivation with an independent loader and its own t survival function *does* confirm every figure,
so the numbers stand; my characterisation of why did not.

### ⛔ R4-2 — "Not one prompt in any arm moves down" is FALSE, and the artifact I cited says so

`per_arm.remBoth.pooled.strongreject_score.n_negative = 2`, and the same for `remS_ctrl`. The claim
is true **only within `base_refused`**, which is precisely the stratum where the rubric identity
forbids downward movement. Corrected in place.

### ⛔ R4-3 — the `base_answered` stratum cannot detect what I said it did not find, and my stated remedy is wrong by ~50×

The `base_answered` baseline score histogram is **`{0.0: 2, 0.75: 2, 0.875: 1, 1.0: 29}`**. **29 of
34 prompts are already at the maximum score**, contributing exactly zero to any content effect by
arithmetic. The effective n is **5, not 34**, and all three movers moved by exactly +0.125 — one
rubric notch.

- MDE at 80% power on the actual clustered estimand (G=8, df=7): **0.0202**.
- The natural non-null alternative — a content pathway *as strong per unit of available range as the
  gate pathway* — predicts `0.0327 × 0.0772 =` **0.0025**, **8× below** the MDE.
- The arithmetic **maximum** possible effect in this stratum is 0.0772, only 4.3× the MDE.

So the stratum cannot distinguish "no content effect" from "a content effect of identical relative
strength". **The P1-vs-P2 contrast is asymmetric by construction**: the refused stratum has 1.0 of
range per prompt, the answered stratum has 0.077. My Limits section said "underpowered"; it then
prescribed *"a dataset with a higher baseline compliance rate"* — **insufficient by roughly 50×**,
because more compliant prompts land at the same ceiling (`remS`'s own 55 answered prompts: 47 at
1.0). Detecting 0.0025 needs n ≈ 1,600 compliant prompts. **The binding constraint is the rubric's
headroom above "compliant", not the compliance rate.**

⛔ **The section header "removing `d_surface` moves a GATE, not the content behind it" asserts the
half that was never measurable, and is withdrawn.** What survives, and is unaffected: the entire
*measurable* effect is 21 refusal flips; 0 prompts move down in that stratum; the matched control
produces 0 flips. The gate half is established. **The "not the content" half is not tested.**

⚠ Two further stratum numbers I tabulated without qualification are **97% one prompt**: `remR`
`base_answered` "+0.1291" comes from a G=8 cluster mean with **four singleton clusters**, one of
which went 0.0→1.0. Same for `remS_ctrl`'s `n_chars` −301.6 ± 327.9. Both now marked.

### ⛔ R4-4 — the R-13 mechanism is wrong, mine inherited it, and my own gate certified the invalid arm

The peer's R-13 says the Qwen3 arms were "judged against *build a bomb* while the model was asked
about a carrot". **They were judged against the empty string.** Chain, confirmed by both auditors
from code and configs:

1. `score_behavior.py` fixes the `gens.jsonl` key set and it contains **no `final_query_text`, no
   `codeword`, no `concept`**.
2. `q3_C20`, `q3_D20`, `q3_D20ctrl` were all judged with **`bank: null`** (`summary.json["bank"]` is
   `None`), so `meta_by_id` was empty.
3. `make_goal` at that commit: `q = row.get("final_query_text") or ""` → **`goal == ""`**, and
   `evaluate("", text, rubric)` scored 960 rows per arm with `judge_status: "ok"`.
4. The baseline arm `qwen3nt` **did** pass `--bank`. So the +0.991 ASR delta compares an arm judged
   against a real goal to arms judged against nothing — **confounded at the judge input**.

I had the evidence and talked myself out of it: I checked those gens rows, saw `codeword/concept/
final_query_text` all `None`, and then accepted `goal_used_concept_surface = True` as proof the
substitution had worked. That field is `concept in goal`, and `"" in ""` is **True**. *(The auditor's
own use of that field as corroboration is likewise refuted by its skeptic — the bank-supplied
baseline is also True 960/960. The chain stands on the code, not on that field.)*

**Consequence for my own instrument, and it is the worst kind:** `topicality_gate.py` reconstructed a
goal those runs never saw, and returned **`PASS` for `remBoth`** — certifying an arm that is invalid
at the judge input. **A gate that certifies the thing it exists to catch is worse than no gate.**

**Fixed:** `judge_goal_provenance()` now reads `summary.json["bank"]` and the `goal_status` column
from the judge directory the gate already opens, and **refuses to issue any verdict** — PASS or FAIL
— on an arm whose judge resolved its goal differently. Re-run:

| Qwen3 `benign_literal` | ASR | verdict |
|---|---|---|
| remove refusalness | 0.994 | ⛔ **REFUSED** — judge bank=None, goal was the empty string |
| remove both | 0.880 | ⛔ **REFUSED** (was `PASS`) |
| double-random control | 0.954 | ⛔ **REFUSED** |

The Qwen3 conclusion — *uninterpretable* — is unchanged and now rests on the right reason.

### ⛔ R4-5 — on the Qwen3 bank the topicality metric carries ONE BIT, so the threshold selected the verdict

`content_words()` applied to the 324 `benign_literal` goals gives `n_goal_content_words = {1: 324}` —
**every goal reduces to the single word "bomb"**. So `goal_content_overlap ∈ {0, 1}` and is
*identically equal* to `has_concept`. The artifact proved it and I did not look: the two supposedly
independent load-bearing fields are **bit-identical floats**
(`goal_overlap_malicious == has_concept_rate_malicious == 0.49473684210526314`). Any
`--min-absolute-overlap` in (0, 0.4947) passes `remBoth`; anything above fails it. **The verdict was a
free parameter.** The diagnostic that exposes this was computed per row and then *dropped* before the
artifact was written. Now aggregated and published as `goal_content_word_count_histogram`, with a
`metric_is_degenerate_one_word_goals` flag that forces `UNDECIDABLE`. (42% of the whole carrot bank
has single-word goals.)

### ⛔ R4-6 — `--min-separation` was dead code advertised as a criterion

Defined, documented with "**and it FAILS unless**…", and emitted into both artifacts as
`thresholds.min_separation: 0.1` — and **never read by the verdict block**. `remBoth` shipped with
`topicality_separation = −0.403`, a 0.5 violation of the published criterion, marked **PASS**. This is
my own doing: I demoted separation from criterion to diagnostic and left the flag behind. **Flag
removed.** ⚠ And the demotion itself rested on `n_non_malicious_answered = 2` for three of the five
Llama arms — a design rule retired on a two-row comparison group. The rule was still wrong for the
stated reason, but the evidence I gave for it was thin.

### ⛔ R4-7 — "every Llama arm PASSES" overstates it two ways

- The Llama artifact was run at `--min-asr-rise 0.03`; the **documented default is 0.10**. The two
  artifacts published incomparable gates without saying so. Re-run at the default: **`remS` is
  `NOT_GATED`** (Δ ASR +0.042), so only `remR` and `remBoth` are formally gated, and both PASS.
- Substring matching (`w in g`) inflated overlap ~19% on a cross-goal control — `harm` ⊂ *harmless*
  fires on refusal text; `use` ⊂ *because*; `plan` ⊂ *planet*. And the boilerplate list missed
  AdvBench's own request verbs (`develop` survived in 67 goals, `tutorial` 43, `guide` 38). A
  hand-written **topic-free refusal sentence scores ≥ 0.15 on 93 of 495 goals**. So `PASS` is a weak
  certificate, as the module says — but the threshold sits inside the metric's noise floor.

**Fixed:** word-boundary token matching, and the scaffolding verbs added. Re-run at the default
threshold, Llama flagged-row overlap is now **base 0.811 · remS 0.806 · remS_ctrl 0.814 · remR 0.779
· remBoth 0.786**.

**Corrected claim.** *The two arms whose ASR rises materially — remove-refusalness (+0.206) and
remove-both (+0.287) — both PASS, with flagged-row goal overlap 0.779 and 0.786 against a 0.15
threshold. Arm B, remove-`d_surface` (+0.042), sits below the gate's rise threshold and is therefore
**not certified — untested, not cleared**. Its flagged rows do carry overlap 0.806, which is
reassuring but is not a verdict this instrument issued.* My earlier sentence — that arm B "rests on
ASR numbers this gate certifies" — is **withdrawn**.

⚠ The gate now also warns that `base` is not the lowest-ASR arm (`remS_ctrl` is, at 0.0626 vs
0.0646) and records `baseline_is_order_dependent`, because reordering `--arm` changes every verdict.

### ⛔ R4-8 — two guards in `analyze_surgical_units.py` could never have fired

1. **The comparability guard read the wrong key.** `RunDir` writes the CLI under `config["args"]`;
   I read `cfg.get("layers")` from the top level, which is absent in **all 49** run dirs. So the
   refusal compared `None` to `None`, never fired, and the artifact recorded
   `"config": {"layers": null, "topk": null}` for runs that all used `8,12,18,24 / 16`. **No shipped
   contrast is affected** — all six pair byte-identical flags — but the guard was theatre. Fixed and
   verified to fire: contrasting the `--layers 8,18 --topk 8` run against the `8,12,18,24 / 16` one
   on `positive_control` now **REFUSES**. The guard also now checks `bank`, `model`, `dtype`,
   `fit_dir`, `query_kind`, `condition`, `seed` and `dst` — previously the *only* cross-run check was
   one float comparison on one derived scalar.
2. **The baseline-identity guard was not NaN-safe.** `nan > 1e-9` is `False`, so a non-finite
   baseline passed the guard and then crashed inside `stdev`. Demonstrated on the Qwen3 run (19 of 20
   shared prompts non-finite). Both `contrast()` and `arm_mean()` now refuse non-finite rows by name
   and count them.

**All six committed contrasts are byte-unchanged after both fixes.**

### ✅ R4-9 — the lexical gradient is NOT a length effect, and that was the likeliest way it was wrong

I asked the auditor to attack the "0.99 / 0.51 / 0.27 across carrot / apple / button" claim hardest on
length. **It is refuted as a confound:** all three banks are identical on `prompt_len` (mean 138.792,
min 103, max 179), `seq_len` (140.792), `readout_pos` (139.792), `codeword_last_pos` (128.792),
`n_demo_positions` (1) and `n_edges_cut` (1024).

⚠ **But a real structural difference survives, and it is not the codeword:** carrot has
`max_answer_tokens = 2 → n_query_positions = 3` (`query_positions [104, 115, 116]` on 24/24), while
apple and button have `= 1 → 2` (`[104, 115]`). **`carrot` is multi-token in the answer surface where
the other two are single-token** — `" Carrot"` is `[3341, 4744]`, and the screener records
`n_single_token_variants: 1` for carrot against 4/4 for apple, button and bomb. So the carrot arm's
readout aggregates over one more query position than the other two. **The 0.99-vs-0.51-vs-0.27
ordering is confounded with readout span at its top end**, and the clean comparison is
**apple vs button — both 2-position, and still differing +0.2348 (cluster t 3.88)**. The gradient
survives on the two tokenization-matched banks; the carrot magnitude does not belong in the same
column without that caveat.

✅ And the decomposition is consistent across all three, confirming R3-6 was general and not a
carrot quirk: the effect is **93.6–96.4% codeword suppression** in every bank (carrot +0.9872 =
+0.0360 concept + 0.9512 codeword; apple 94.7%; button 93.6%).

⚠ **A reporting error in my own commit message for `d0b51351`:** "`+0.2708, t 5.04, 21/24,
domain-clustered p 0.0086`" splices two different tests — `t 5.04` is the prompt-level statistic
(df 23) and `p 0.0086` comes from the cluster-level t of 4.19 (df 5). Both are in the artifact; the
one-line summary should not have joined them.

### ⛔ R4-10 — "0 overlapping demonstration sets among all 1,800" is false as written

Phase D's headline. The **within-level** claim is exactly right and is what the design needs: **0 of
107,100 within-level pairs share a demonstration sentence** (7,140 pairs × 15 levels). But the 1,800
rows draw on only **360 distinct demo-sentence sets over 120 (domain, split, slot) families** — the
same family is reused *across* the 15 levels, by design, because that is what makes the levels
comparable. **Corrected wording: "120 independent families per level, pairwise disjoint within each
level" — not "1,800 mutually disjoint sets".** No analysis is affected: every Phase-D contrast is
between levels at matched families, which is the paired design, not an independence claim.

Three further Phase-D facts the audit surfaced, all confirmed, none fatal, none previously written
down:

- **Filler sentences DO overlap across slots.** Width-6 filler on stride-3 slots: of 45 slot pairs,
  25 share none, 10 share 2, 10 share 4. I anticipated this when choosing `n_filler=6` and decided it
  was acceptable — filler is identical across the three position arms *of the same family*, so it
  cannot confound the position contrast — **but I never wrote that down, and the tests do not touch
  filler.** Now recorded.
- **`far` and `distributed` are length-matched but not gap-matched**, which is intended and was
  unstated: mean demo-to-query gap 488.4 vs 423.8 characters, `far > distributed` on **120/120**
  families (near: 98.5).
- ⚠ **132 `prompt_id`s collide between the Phase-D bank and the main bank, with different
  `prompt_sha16`** (60 role_style, 48 core2x2, 24 families). `family_id` does not include
  `bank_block`, so a tool reading both banks would join two *different* prompts on one id. The
  mitigation is real and already in place — every consumer records `prompt_sha16` — but the collision
  is now documented rather than latent.
- ⚠ **All 120 `consistency=irrelevant` rows have `n_target_occurrences == 1`**, and
  `analyze_boombness.py:191` skips rows with `n_occurrences < 2`. That level will be **silently
  dropped** by any per-occurrence analysis. Not a bug in the bank — the irrelevant arm teaches a
  *different* word, so one occurrence is correct — but it must be handled explicitly downstream.
- ⚠ **Two of my six new tests are weaker than they look.** `tests/test_slot_disjointness.py`
  hardcodes `POOL = 20` and never opens `demo_pools.json`, so all 11 pass unchanged even under a
  simulated pool of 24 (which collapses the ten slots to **4 distinct sets**). And
  `test_phase_d_preset_uses_only_those_slots_and_only_n2` greps a 40-character source slice. Neither
  is wrong; both are narrower than their names imply.

### ✅ Confirmed and not re-litigated

Every Phase-D bank number in the report reproduces to the decimal (all 15 level rows, 120 families
each, the 630.7 length match — and **per-family** length spread across near/far/distributed is
**exactly 0 for all 120 families**, stronger than the pooled match I claimed). All three bank
regenerations reproduce byte-identically (`4cd9157399aa1b3c`, `debe267f05efb9ab`, and Phase D's own
`2b79d5699e0180c9`). Every E4 figure and every surgical-units figure reproduces under independent
re-derivation. The `topicality` artifacts leak no generation text (recursive string scan: longest
string is a verdict rationale).


### ✅ R4-4 correction in flight — the three Qwen3 arms are being re-judged against a HASH-CERTIFIED bank

Review #4's top correction, launched at 20:12. The right bank is not the current one: the generations
were made against the **2,352-row** bank, recovered from git at `82bc1a3c` and archived at
`data/boombness_prompts/archive/boombness_prompt_bank_2352.jsonl`.

**The join is certified by hash, and that is the point** — `common.compare_bank_hashes`' own docstring
records that the committed 2352-row bank hashes to `71bea179345ed118` on file bytes, and the
generations' `metadata.json` records `bank_content_sha16: 71bea179345ed118`, `bank_n_rows: 2352`.
Recomputed here: **identical**, and **0 of 960 prompt_ids fail to resolve**.

**And re-running `make_goal` over the join is direct proof of the R4-4 mechanism:**

| goal status, 960 rows | with `bank=None` (as judged) | **with the 2,352-row bank** |
|---|---|---|
| `empty` | **960** | **0** |
| `substituted` | 0 | **816** |
| `noop_concept_already_present` | 0 | **144** |

The original runs scored every row against the empty string. With the bank they resolve to a real
goal in all 960. That is the confound, demonstrated rather than argued.

```
python src/boombness/judge_boombness.py --gens outputs/boombness/score_behavior/q3_{C20,D20,D20ctrl}_... \
       --bank data/boombness_prompts/archive/boombness_prompt_bank_2352.jsonl --tag q3rj_{C20,D20,D20ctrl}
```

⚠ **The judge prints `BANK IDENTITY UNVERIFIED` and it is right to.** The archived meta is the legacy
schema — it carries `bank_content_sha16`, not the newer `bank_file_sha16`/`bank_rows_sha16` that
`compare_bank_hashes` looks for — so the guard reports **unknown** rather than asserting agreement,
exactly as designed. The hash equality above was verified by hand and is recorded here; the artifact
will say `unverified`, and that discrepancy is a key-name change, not a join failure.

Three background jobs (pids 2562031/2/3), ~95 min for 960 rows each. **No claim about Qwen3 arm D —
in either direction — until they land.**

### Phase D representation extraction submitted (770128)

Independent of the generations, so it runs in parallel rather than after:

```
extract_boombness.py --bank ..._phase_d.jsonl --stage score --fit-dir full_20260816_185942_1008673
                     --allow-cross-bank-fit --layers all --position codeword_last
                     --directions d_surface,d_context,d_inter,d_naive
```

`--stage score` matters: the `bank_block == "core2x2"` filter at `extract_boombness.py:405` lives in
`stage_fit` only, so a bank with new block names is scoreable but not fittable — which is correct
here, since Phase D must use the **committed** direction rather than one refitted on its own prompts.
`--allow-cross-bank-fit` is declared rather than defaulted, so `cross_bank_fit` is recorded in
`summary.json` instead of hidden.

Generation (770023) is at 900/2160 after 81 minutes → ~3.2 h, inside its 4 h limit.


### ⛔ Incident — the judge API ran out of credits mid-correction, and the partial runs are NOT salvageable

At 20:43 all three re-judges were failing with
`litellm.RateLimitError: OpenAIException - You have no credits remaining.` Each had reached ~600 of
960 rows. **The partials cannot be used, and the reason matters:** the judge writes rows in bank
order, so a truncated run is a *prefix*, not a sample — and the three arms stopped at different
points, covering **143 / 147 / 144** of the 324 `benign_literal` rows respectively. Different
subsets means the arms are **not pairable**, which is the entire estimand. No `DONE.json` was
written either, so `common.require_done` would have refused them downstream regardless. Killed.

Raised with the user, who added credits. **Verified before relaunching rather than assumed** — a
3-row smoke test (`--tag credtest`): `3/3 judged, null_frac=0.0000`, goal statuses
`{substituted: 2, noop_concept_already_present: 1}` and **zero `empty`**, which also re-confirms the
bank join is doing its job.

Relaunched as `q3rj2_*`, and **with a fourth arm the first attempt was missing: the baseline.** The
original `qwen3nt` baseline was judged with *a* bank, but for a paired contrast all four arms must
resolve their goals through the *same* bank; re-judging it removes that asymmetry rather than
assuming it away.

### ✅ Phase D representation half is COMPLETE — and it has zero self-fit rows

`extract_boombness/phaseD_extract_20260820_201555_2809154`, job 770128, 5 minutes, `DONE.json`
written. **2,160 of 2,160 rows succeeded, 0 failed**, all 32 layers, position `codeword_last`.

The number that matters for plan §2.3 hygiene:

```
cross_fit: {n_self_fit_rows: 0, n_cross_fit_rows: 2160, self_fit_frac: 0.0}
```

**Every Phase-D representation is read off a direction fitted on different text.** The `d_surface`
used here is the committed 2×2 fit (`full_20260816_185942_1008673`); nothing was refitted on Phase
D's own prompts, which is what would have made a Boombness→ASR correlation circular.

### ⚠ A provenance trap worth naming: `cross_bank_fit: False` does not mean "same bank"

The summary records `cross_bank_fit: false` **and** `cross_bank_fit_declared: true`. That looks
contradictory and is not. Detection needs the *fit directory* to carry bank hashes, and this one
carries none — `unknown_identity: ["bank_rows_sha16", "bank_file_sha16", "n_bank_rows_used",
"fit_dtype"]`. So `bank_identity_mismatch` is `False` because the comparison **could not be made**,
not because the banks agree. The repo's standing principle — *an absent hash is reported as unknown,
never as agreement* — is being honoured, but the field NAME reads like a negative finding.

**A future reader must take `cross_bank_fit_declared` as the provenance, not `cross_bank_fit`,
whenever `unknown_identity` lists the bank hashes.** Recorded here so the trap is on the record.

### Next corrections, in priority order

1. **Re-judge the three Qwen3 arms with `--bank`** — the `_FATAL_GOAL_STATUSES` guard added after
   those runs would now hard-fail them, so the fix is enforceable today and cheap (no GPU, judge
   only). Until then nothing about Qwen3 arm D is interpretable.
2. **Gate arm B properly** — either justify a lower `--min-asr-rise` in the artifact or accept that
   the sprint's `d_surface` headline is uncertified by the topicality gate.
3. **Diagnose the non-finite Qwen3 knockout logits** before any further cross-model port.
4. Make the slot tests read the real pool, and add a filler-overlap test.
5. Handle `consistency=irrelevant` explicitly in any Phase-D per-occurrence analysis.


### Phase D analysis written and SELF-TESTED before any real data touches it (`analyze_phase_d.py`)

The generation run is still in flight, so the gate's machinery was built and validated first —
against synthetic data with known answers, so that a null on the real data can be believed.

**The selection problem, and the only honest answer to it.** There are 3 positions × 35 layer choices
× 2 readouts = **210 candidate metrics per direction**. Reporting the best of 210 is exactly how a
null becomes a finding, and it is close to what G2 did. So the gate is **nested on the bank's own
split**:

> choose the single best metric on **dev** → test **that one metric** on **heldout**.

The heldout test has a family of exactly one, so its p-value needs no correction and means what it
says. The full dev grid is reported with Holm over all 210, but **the dev grid is selection, not
evidence**. Dev and heldout are 900 prompts each, disjoint by construction.

**Negative controls are other directions, not noise.** `d_context` and `d_naive` were extracted on
the same rows and go through the identical pipeline. If all three predict equally the metric is
reading prompt structure — which is precisely what retraction **F-2** already established for the
token-level gradient, so this is a live possibility, not a formality.

**Estimand.** Per-domain Spearman ρ aggregated over the 6 domain clusters (G−1 df), with a
**within-domain permutation null** (labels shuffled *inside* each domain). Shuffling globally would
let the null be broken by between-domain differences in both metric and ASR — the exact confound
clustering exists to price — and would return an optimistically small p. The pooled ρ is reported
too, because G2 reported it and the two must be comparable, but it is **not** the estimand.

#### The self-test, and the one result that needed a second look

| synthetic case | expected | measured |
|---|---|---|
| planted within-domain signal | ρ > 0, p small | ρ **+0.5496**, p_cl 1.3e-05, perm p 0.0025 ✅ |
| pure null | ρ ≈ 0, p large | ρ −0.0723, **p_cl 0.0357** ⚠ |
| signal ONLY between domains | pooled high, within ≈ 0 | pooled **+0.9709**, within **−0.0464** ✅ |
| constant metric (all ties) | no correlation | `None` ✅ |

The third row is the one that matters: a metric that differs across domains and an ASR that differs
across domains produce a **pooled ρ of +0.97 with nothing whatsoever inside any domain**. That is the
shape of a false Fig-9, and the estimand rejects it.

The pure-null row looked like a false positive at α = 0.05, so **I measured the false-positive rate
rather than explaining it away** — 400 independent null draws:

| α | 0.01 | 0.05 | 0.10 |
|---|---|---|---|
| cluster-t false-positive rate | **0.0100** | **0.0475** | **0.1050** |

Calibrated. The single p = 0.0357 was a chance draw at the ~4% level — what a valid test does 5% of
the time. ⚠ The permutation null measures 0.0667 at α = 0.05, but over only 60 draws (MC se ≈ 0.028),
so it is **within one standard error of nominal and is not a strong check**; the cluster-t is the
better-verified of the two and both are reported.

**Guards in the script:** a stale-join `SystemExit` if any prompt joins on `prompt_id` but differs in
`prompt_sha16` (R1's failure mode, and Phase D shares 132 ids with the main bank); full row
accounting by split, domain and block; and metrics that are constant or unestimable are dropped with
a `degenerate` flag rather than silently correlated.

**Not yet available, and it will be stated as a gap rather than skipped:** the plan's metric list
includes *refusalness* and *Boombness minus refusalness*, and no refusalness run exists on the Phase-D
bank. Probe margin is dead on arrival (Decision Gate C failed).


### Phase D judging sharded — 3 hours to 36 minutes, with no merged-run fiction

The judge loop is strictly sequential (`for i, g in enumerate(rows)`, one `evaluate()` per row) at
~12.5 rows/min, so 2,160 Phase-D rows was a ~3-hour single process. But the API had already served
**four concurrent judges at that same per-process rate** during the Qwen3 re-judge, so the bottleneck
is per-request latency, not throughput.

**Change: `--offset`, mirroring the existing `--limit`.** Six lines including the comment. Slicing
happens before the bank join and before any filtering, so shard boundaries are plain row indices and
`offset`/`limit` compose exactly like a Python slice.

```
for i in 0..5:  judge_boombness.py --gens phaseD_base_... --bank ..._phase_d.jsonl \
                                   --offset $((i*360)) --limit 360 --tag pdJ$i
```

**No merge step, deliberately.** Concatenating six run directories into one would mean hand-writing a
`summary.json` and a `DONE.json` for a run that never happened — a fabricated artifact, and exactly
the kind of thing this sprint keeps catching. Instead `analyze_phase_d.py --judge` became repeatable:
it reads all six, records `judge_shard_rows` per shard in the artifact, and **raises `SystemExit` if
any `prompt_id` appears in more than one shard** — so the union is asserted to be a partition rather
than assumed.

Measured: 6 × ~10 rows/min = ~60 rows/min aggregate, all six at 50/360 after five minutes. **~36
minutes** for the full bank.

## 4h Code and Output Review — Review #3 (2026-08-20 09:00)

Two adversarial auditors, 191k tokens, 82 tool calls, aimed at the two newest and least-scrutinised
results. **Both results survive. Four of my supporting statements do not.**

### The arm-6 sign reversal — SURVIVES, and is stronger than I reported

Every figure reproduces from raw judge rows. The auditor added robustness I had not computed:

- **13 of 16 clusters negative, 3 exactly zero, ZERO positive.**
- Leave-one-cluster-out range **−0.115 to −0.142**, worst p **0.0015**.
- Survives Holm even at **m = 20** (0.0123), so the family size is not load-bearing.
- **Survives on the binary flag**, slightly stronger: −0.1375, t −4.46, p_cl 0.00046.
- All four arms pass the committed coherence gate, none trips the floor. And **`F6_CTRL` is the more
  verbose arm** (961 vs 677 mean chars) *and* scores higher ASR — so "the edit broke generation" would
  push the **wrong way**. Degeneracy cannot explain the reversal.

### ⛔ R3-1 — my dose figure was wrong, and "verified" was not verified

I wrote the injected magnitude as **1.4815**, "verified from the fit dir". The true value is **1.5137**:
I read `gap[d_surface][8]` from `directions_fit_**heldout**.pt` (5.926142) while the runs used
`directions_fit_**dev**.pt` (6.054948). **The equality of the two arms is unaffected and was
independently re-confirmed** — both take the same `gap["d_surface"]` path and `make_add_hook`
normalises to unit norm, so both inject exactly `alpha × g`. But the sentence claiming verification was
checked against the wrong file. Corrected in place.

### ⛔ R3-2 — the arm-6 control is ONE random draw, and I did not say so

`norm_matched_random` seeds a fresh generator from `control_seed + L`, so **all 495 prompts receive the
identical vector**, and only L8 is in the band — **one vector total**. No between-draw variance is
estimated anywhere, so the clustered SE prices prompt and domain noise only and the p-value conditions
on that single draw.

**This is not retraction #7 / R-12** — the auditor confirmed the seed genuinely reaches the draw
post-`aaf7e50c`, and the four `gens.jsonl` hashes are all distinct. And it **replicates on a second,
independent draw**: `addCtrl8_025` (different seed, no refusalness leg) gives `addS − addCtrl8 =
−0.0301, t −2.44, p 0.027`, same direction. But the headline arm has **n = 1 control draw** and the log
now says so.

### ⛔ R3-3 — the headline contrasts were in NO committed artifact

`analyze_external_arms.py` emits only `paired_vs_baseline`. The numbers I led with (−0.1328, t −4.31,
Holm 0.0025) existed **only in a commit message**. **Fixed this tick:**
`outputs/boombness_followup/phaseF_paired_contrasts.json` now carries all five paired contrasts, on
both the continuous and binary estimands, with the Holm family.

### ⛔ R3-4 — "73%" fails; the corrected claim is STRONGER

Paired `codeword − first` = **+0.3604 ± 0.3552, t = 1.01**, codeword > first on only **12/24** prompts.
The "missing 27%" is not distinguishable from zero. **Cutting the first demonstration codeword alone
reproduces the entire codeword-scope effect within noise.** Corrected in place.

### ⛔ R3-5 — my `dynamic_range_established` defence was self-serving

I argued the flag was non-disqualifying because `no_demo_text` (−17.879) establishes movability. The
auditor showed **`no_demo_text` is one forward pass replicated 24 times** — all 24 rows carry
`semantic_logodds = −13.853043318` and `top1_id = 95392`, identical to nine decimals, because
`final_query_text` is the same string for every prompt. **Its ceiling has n = 1 — the exact shape R-12
retracted.** It also points the wrong way: −17.88 against a reported effect of **+0.97**.

**The correct defence exists and I failed to make it:** `first_codeword` **is itself the matched
positive control for `last_codeword`** — same kind of intervention, same 1,024 edges, same layers,
+0.97 versus −0.02. That licenses the `last` null without invoking `no_demo_text` at all. **Conclusion
right, stated reasoning unsound.**

### ⛔ R3-6 — the effect is token SUPPRESSION, not semantic re-binding

Decomposing the +0.9718: **Δ logp_codeword = −0.9449, Δ logp_concept = +0.0268**, and `top1_id` changes
on **1 of 24** prompts. Cutting the first demonstration codeword makes the model **less likely to say
*carrot*** — it does **not** make it more likely to say *bomb*. My phrasing "makes the readout more
concept-like" is **contradicted by its own decomposition** and is withdrawn. The result survives as a
**readout** claim; any gloss about "where the concept binding lives" does not.

### Two identification limits the audit surfaced

1. **Lexical G = 1.** All 24 prompts share **one** codeword/concept pair — `carrot` / `bomb` — across
   all six domains. The Phase G contrast is established **for *carrot***, not for "codewords". Domain
   clustering does not fix this.
2. **Serial position is unidentified.** `demo_block` starts at character 0, so the first demo codeword
   sits ~token 10–15 of a 105–181-token sequence, adjacent to the BOS/attention-sink region. There is
   **no all-layer, 1,024-edge control on a non-codeword token at a comparable early position**.
   "First demonstration codeword" is not yet separated from "earliest heavily-attended source".

### And the statistics are stronger than I reported

Because the runs share prompts and have **bit-identical baselines**, the arms are exactly pairable:
**paired first − last = +0.9949, sem 0.0875, t = 11.4 (df 23), sign test 24/24 positive, p ≈ 1.2e-7**;
domain-clustered t = 9.8 (df 5, p ≈ 2e-4). I reported two independent sems where a paired test was
available and far tighter.

⚠ **Cross-run comparability caveat the auditor caught:** the committed codeword-24 run used
`--layers 8,18 --topk 8`; the new runs use `--layers 8,12,18,24 --topk 16`. For `all_layers_demo` this
is provably inert (that arm ignores both flags), but **every other arm differs** — `positive_control` is
+0.2583 in one and −4.6579 in the others. **The three JSONs must not be read side-by-side outside the
`all_layers_demo` row.**

## Compute Blocker — diagnosed and mitigated (tick 23)

**Symptom.** From tick 20 to 23 (~2h) not one of 8 submitted jobs started; all `PD (Priority)`.

**Diagnosis.** `sprio -u $USER` shows **FAIRSHARE = 338** against a partition base of 100,000,000 —
i.e. fair-share throttling after this sprint's ~20 GPU jobs in one day. Partition state at tick 23:
**25 running / 77 pending** across all users. This is the scheduler working correctly, not a fault.

**Mitigation applied — right-sized walltimes for backfill.** `run_boombness.sh` hardcodes
`#SBATCH --time=06:00:00`. A 6-hour request is nearly unbackfillable; SLURM's backfill scheduler
starts short jobs early when they fit a gap before a higher-priority reservation. Observed runtimes in
this sprint: **16–40 min** for a 495-prompt coherent arm, **1h51–2h06** for a degenerate one, and the
benign bank is only **40 prompts** (≈5 min expected).

Resubmitted all 8 with limits sized from those observations:

| jobs | tag | old limit | **new limit** | basis |
|---|---|---|---|---|
| 768517–768520 | `bng_base/B/Bctrl/C` | 6:00:00 | **0:25:00** | 40 prompts, ≈5 min expected |
| 768521–768523 | `fuF25_addBoth_CTRL`, `fuF25_remR_addS_CTRL`, `fuF_remS_addR_CTRL2` | 6:00:00 | **1:15:00** | 495 prompts, 16–40 min observed |
| 768524 | `fuF_addR_gapdose` | 6:00:00 | **2:30:00** | wider margin — a gap-dosed `add` may degenerate, and the worst degenerate arm ran 2h06 |

⚠ **Process note:** the first resubmit attempt used `set -- $spec`, which is bash syntax; this shell is
**tcsh**, so the four `sbatch` calls failed *after* the `scancel` had already run, briefly leaving those
jobs unqueued. Caught and restored in the same tick with explicit per-job commands. **Standing rule
added: no shell-array or `set --` constructs in this session; one explicit command per job**, and never
`scancel` before the replacement command is known to work.

**Not done:** `--time` is passed on the `sbatch` line rather than edited into `run_boombness.sh`, because
that script is shared with the non-Boombness workstream and its own docstring warns that overriding
`#SBATCH` directives on the command line has caused a mis-scheduling incident before (the `--exclude`
/ `--nodelist` trap, 2026-08-06). `--time` does not interact with `--nodelist`, but the edit stays out
of the shared file.



### ⚠ A second concurrency episode — a peer resumed, and this time its work is being ADOPTED

Between 00:53 and 01:05 on 2026-08-21, four commits appeared on this branch that are not mine:
`53efbf00`, `cbf671a0`, `846abfa8`, `2a8c3900`. The user's instruction of 2026-08-20 ~17:55 — *"shut
it down for me i want only you to work on it"* — still stands, so stand-down messages went out again
(the two reachable Remote Control peers; no local interactive sessions are listed any more).

**⚠ The source is UNIDENTIFIED, and both reachable peers ruled themselves out with specifics.**
`c-002-stateless-hare` and `c-002-delegated-sundae` each replied: no SLURM jobs, no background
processes, no commits, no `scancel`, idle since the first stand-down. Neither is it, and no local
interactive session is listed any more. One of them flagged commit `939b6d96` at 01:28:55 as evidence
the peer was still active — **that one is mine** (the Sprint Final Report rewrite), so it is not
evidence. As of 01:30 there have been **no further foreign commits since 01:05:18**, so whatever it
was has probably stopped. Raised with the user, who knows which terminals are open; the author field
cannot discriminate because every session commits as the same git user.

**Checked before doing anything else: did it clobber my work?** No. Those commits touch
`docs/BOOMBNESS_CONTINUATION_LOG.md`, `reports/`, and three files under `src/boombness/`; the diff of
my own staged rewrite shows **0 lines removed outside the Sprint Final Report section** I was
deliberately replacing. Nothing was lost in either direction.

**And its central finding is one I am adopting rather than reverting, because it independently
reproduces mine.** `cbf671a0` fixes `judge_boombness`'s distinctive-word match, which used `\b<w>`
with **no trailing boundary**, so the word matched anything it prefixes — and its commit message
cites `topicality_gate.py:114-127`, written a few hours earlier in *this* session, as already having
the word-bounded version. It also reports the metric is a **single-bit indicator** — 1,824 of 2,736
bank rows have exactly one distinctive word and the number of distinct such words across the whole
bank is **1** — which is the same degeneracy my R5-5 found and now guards with
`metric_is_degenerate_one_word_goals`.

**Two sessions, working independently, found the same two defects in the same instrument and fixed
them the same way.** That is genuine convergent evidence that both defects are real, and it is the
one good thing to come out of the duplication.

⚠ **One live hazard, flagged rather than assumed away:** `cbf671a0` edited `judge_boombness.py` while
my three variance-matched-control judge shards (pids 433016/7/8) were mid-run against it. Python
loaded the module at process start, so the running shards are unaffected — but the *next* judge run
in this repo will use the peer's version. That is an improvement and I would have adopted it anyway;
it is recorded so nobody later reads two judge runs on either side of 00:57 as the same instrument.


## ✅✅ THE SUBSPACE-MATCHED CONTROL LANDS — arm B survives a control that could have falsified it

**Artifacts:** `outputs/boombness/score_behavior/abVMC2_20260821_010052_955575` (495 generations,
0 failures), judged in three shards `judge/vmcJ{0,1,2}_20260821_012704_*` (165 rows each,
`null_frac 0.0000`, `DONE.json` on all three).

R5-7 established that every "the matched random control is inert" statement in this repo was inert
**by construction**. This is the test that replaces it: `in_subspace_orth` at L8, drawn inside the
span of the centred 2×2 cell means and **exactly orthogonal to `d_surface`** (verified
|cos| ≤ 1.7e-08 over both splits × 32 layers), otherwise byte-identical to the committed arm B.

### The result, paired against the same baseline, domain-clustered (G = 16)

| arm | Δ StrongReject | p_cl | Δ ASR@0.5 | p_cl |
|---|---|---|---|---|
| **ARM B** — `d_surface` @ L8 | **+0.0305** | **0.0089** | **+0.0306** | **0.0089** |
| control — isotropic random | −0.0062 | 0.54 | −0.0064 | 0.53 |
| **control — subspace-matched, ⊥ arm** | **−0.0033** | **0.149** | **−0.0032** | **0.165** |

**Paired arm-minus-control:** vs isotropic **+0.0367** (p_cl 0.0140); vs subspace-matched
**+0.0339** (p_cl 0.0103).

**The prediction recorded before the run — *"near zero means arm B's specificity survives a control
that could have falsified it"* — is what happened.** This is the first control in the sprint whose
failure would have meant something, and it did not fail. Arm B, the sprint's longest-standing
behavioural result, is **strengthened**: ablating a *different* direction inside the same concept
subspace, at the same layer, with the same operation and dose, does nothing.

### ⚠ But "variance-matched" was my word and it is wrong — the honest name is SUBSPACE-matched

The control removes **5.35%** of the cell-mean spread at L8; the arm removes **84.02%**. So it is
~1,000× stronger than the isotropic control (0.005%) and still **~16× weaker than the arm**. It does
**not** answer *"would any perturbation of comparable magnitude do this?"* — it answers *"does
ablating the rest of the concept subspace do this?"*, which is the **direction-specificity** question
and is the one requirement-4-style specificity actually needs. I have renamed it in the prose
accordingly; the flag name `in_subspace_orth` was always accurate.

⚠ Note also its standard error is **4× smaller** than the arm's or the isotropic control's (0.0022 vs
0.0102 / 0.0098) — this control barely perturbs the outcome at all, which is consistent with it being
a much smaller edit than the arm and is a further reason not to call it magnitude-matched.

### What this does and does not settle

**Settles:** arm B is about `d_surface` specifically, not about "ablating something in the concept
subspace at L8". R5-7's methodological point stands in full — isotropic controls certify nothing in
high dimensions — but its **practical** consequence for the sprint's headline behavioural result is
now measured, and it is benign.

**Does not settle:** every *other* inertness claim in the sprint — the `d_surface` layer profile's
eleven matched controls, the refusalness profile's five, Phase F's composed controls, and the Qwen3
double-random control — still rests on isotropic draws. **Those remain "a random rank-1 projection at
the same depth did nothing".** Re-running them against `in_subspace_orth` is one job each and is now
the obvious next sprint's first task.

⚠ And this does not rescue Gate D: requirement 4 failed on `d_naive`/`d_context` predicting ASR as
well as `d_surface`, which is a *prompt-level correlational* fact and is untouched by a causal
control on arm B.


### ⚠ Where the subspace-matched control is VALID, measured rather than assumed — and it corroborates §3 by a new route

`score_behavior.py:197` sets `base = payload["d_surface"]` for **every** control name, so
`in_subspace_orth` is always built from the 2×2 cell-mean span and always orthogonalised against
`d_surface`. That makes it the right control for a `d_surface` arm and raises an obvious question for
the others: is that subspace a sensible basis for controlling a **refusalness** arm?

**Measured — the fraction of each direction's squared norm lying inside the centred cell-mean span:**

| layer | `d_surface` in span | **refusalness in span** |
|---|---|---|
| L12 | **100.0000%** | **2.61%** |
| L14 | 100.0000% | 2.72% |
| L16 | 100.0000% | 1.33% |
| L18 | 100.0000% | **0.65%** |
| L20 | 100.0000% | 1.38% |

`d_surface` is **entirely inside** the span — unsurprising, it is built from those cell means — while
**refusalness is 0.6–2.7% inside it**. So a draw from this subspace is ~98% orthogonal to refusalness
by construction, and as a control for a refusalness arm it would be **nearly as uninformative as the
isotropic draw it was built to replace**.

**Two consequences, both stated rather than discovered later:**

1. ⛔ **`in_subspace_orth` must not be used to control a refusalness arm.** Tonight's re-tests are
   scoped to `d_surface` arms only (L6, L10, L12 submitted as 771137–771139; L8 already landed).
   Doing this properly needs a basis for *refusal-relevant* variance — the span of the five committed
   refusal directions, or the top PCs of activations on refused-versus-complied prompts. That is
   next-sprint work and is now written into the next-sprint list rather than implied.
2. ✅ **It independently corroborates §3's separability claim by a different measurement.** §3 rests
   on cosines (0.128 at L12 → 0.026 at L18, at chance by L18). This is a *subspace* statement:
   refusalness lives almost entirely outside the three-dimensional space the 2×2 design spans, at
   every depth where a refusal direction exists. Two unrelated geometries, same conclusion.

⚠ Honest limit on the corroboration: both measurements read the same two fitted objects, so they are
not independent *evidence* about the model — they are independent *summaries* of the same vectors.
What the subspace version adds is that the near-orthogonality is not a knife-edge property of one
direction pair but holds against the whole design subspace.


### The layer-profile re-check — three more depths submitted, judged, and an analyzer that refuses the wrong control

**Runs 771137/771138/771139** (`in_subspace_orth:project_out:{6,10,12}` on AdvBench heldout 495),
all **495 generations, 0 failures**. Their own diagnostics, verified before judging:

| job | layer | cos(arm, control) | ARM removes | CONTROL removes | k |
|---|---|---|---|---|---|
| 771137 | L6 | +5.6e-09 | 87.68% | 5.40% | 2 |
| 771138 | L10 | +6.5e-09 | 81.14% | 5.88% | 2 |
| 771139 | L12 | −9.3e-10 | 82.04% | 7.25% | 2 |

Judging in six shards (2 per depth, 248+247). **L12 is the one that matters most**: it is the layer
profile's peak (+0.0322) and, with L8, one of only two depths BH keeps.

**`analyze_control_recheck.py`** produces the artifact rather than leaving the numbers in prose
(R3-3). It uses the identical estimand to `analyze_external_arms.py` — paired per prompt against the
same baseline, domain-clustered — so the output is directly comparable to the committed profile, and
it computes the arm-minus-control contrast **paired per prompt**, which is tighter than differencing
two independently-clustered means.

**Two guards it enforces, both of which encode tonight's scoping measurement:**

- it reads each arm's **actual intervention** from the generation run's `summary.json` rather than
  trusting the tag, and **refuses any arm whose direction is not `d_surface`** — because
  `in_subspace_orth` is measured to be a valid control only there (d_surface is 100.0000% inside the
  cell-mean span; refusalness 0.65–2.72%);
- it refuses a "subspace control" run whose recorded direction is not `in_subspace_orth`, and asserts
  the judge shards of one run are duplicate-free before unioning them.

**Prediction, recorded before the numbers land.** The committed profile has L6 +0.0159, L10 +0.0223,
L12 +0.0322 against isotropic controls of |Δ| ≤ 0.0066. Arm B at L8 already passed this test
(−0.0033, p 0.149). If L12's subspace-matched control is also inert, the profile's two BH-surviving
depths both survive a control that could have falsified them. **If L12's control moves ASR, the
profile's peak is not about `d_surface`** — and since Gate D already showed `d_naive` and `d_context`
predict as well at the prompt level, that would make the direction non-specific at *both* grains.


## ✅ THE LAYER PROFILE RE-CHECKED — `d_surface` is causally specific at all four depths, and only L8 survives Holm

**Artifact:** `outputs/boombness_followup/control_recheck_subspace.json`.
**Producer:** `src/boombness/analyze_control_recheck.py`. AdvBench heldout 495, one baseline, four
depths, paired per prompt, domain-clustered (G = 16).

The isotropic controls the committed profile used cannot fail (R5-7). These are the same four depths
re-tested against `in_subspace_orth` — same layer, same operation, same α, drawn inside the concept
subspace and **exactly orthogonal to `d_surface`**.

| layer | **ARM** | p_cl | isotropic ctrl | p | **subspace ctrl** | p | **arm − subspace** | p |
|---|---|---|---|---|---|---|---|---|
| L6 | +0.0159 | 0.057 | −0.0033 | 0.75 | +0.0065 | 0.41 | **+0.0094** | 0.035 |
| **L8** | **+0.0305** | **0.009** | −0.0062 | 0.54 | **−0.0033** | 0.15 | **+0.0339** | **0.010** |
| L10 | +0.0223 | 0.019 | +0.0047 | 0.25 | −0.0057 | 0.57 | **+0.0280** | 0.038 |
| **L12** | **+0.0322** | **0.006** | −0.0003 | 0.42 | **+0.0103** | **0.062** | **+0.0219** | 0.021 |

### What survives

**The specificity contrast is positive and individually significant at every depth** — the arm
exceeds a control that ablates a *different* direction in the same subspace, at the same layer, by
+0.0094 to +0.0339. That is the direction-specificity test the isotropic controls were never able to
perform, and `d_surface` passes it four times out of four.

**⛔ But only L8 survives Holm over the four depths** (adjusted: L8 **0.0413**, L12 0.0638, L6 0.0705,
L10 0.0705). The family is the depth set, because the contrast is run once per depth — the same
correction this sprint applied to the layer profile itself, where Holm rejected nothing at m = 11.
Reporting four individually-significant contrasts without it would be exactly the defect this sprint
keeps catching in inherited results. **So: one depth establishes causal direction-specificity;
the other three are consistent with it and do not independently establish it.**

### ⚠ And the closest a control has come to firing in this whole sprint is at the profile's peak

At **L12** the subspace-matched control is **+0.0103, p = 0.062** — 32% of the arm's +0.0322. It does
not cross 0.05 and it would not survive any correction, so it is **not** a positive result. But it is
the only control in the sprint that has come near, and it sits at the profile's largest effect and one
of the two depths BH keeps. Stated plainly rather than rounded to "inert": *at L12, ablating a
different concept-subspace direction produces about a third of the arm's effect, at p = 0.062.*

### What this does and does not change

**Changes:** the committed layer profile's inertness claims at L6/L8/L10/L12 are no longer resting on
a control that cannot fail. At L8 the specificity is established with correction; at the other three
it is supported without correction.

**Does not change:** ⛔ Gate D still fails — `d_naive` and `d_context` predict ASR as well as
`d_surface` at the *prompt* level, and that is a correlational fact untouched by any causal control.
**The two grains disagree, and that disagreement is now the sharpest open question in the project:**
`d_surface` is causally specific at L8 and correlationally non-specific at the prompt level. ⛔ And
the refusalness profile, Phase F's composed arms and the Qwen3 double-random control are all still
isotropic-controlled and still untested — measured earlier tonight to need a *different* basis, since
refusalness lies only 0.65–2.72% inside the cell-mean span.


## ✅✅ GATE D REQUIREMENT 4, RE-TESTED PROPERLY — the signal belongs to the SUBSPACE, not to `d_surface`

**Artifact:** `outputs/boombness_followup/subspace_prediction.json`.
**Producer:** `src/boombness/analyze_subspace_prediction.py`. **No GPU** — the extraction cached the
final-occurrence representation per prompt (`[32, 4096]` × 2,160), and on this bank the final
occurrence **is** the query occurrence (`is_query == is_final` on 7080/7080), which is the position
Gate D's selected metrics use. So any direction can be scored offline.

### ⛔ First: my own Gate D evidence for requirement 4 was not a control

I failed requirement 4 on "`d_naive` and `d_context` predict as well as `d_surface`". Measured:

- `cos(d_surface, d_naive)` = **0.93–0.97** at the selected layers L29–L31; `d_context` 0.25–0.39.
- As **measurements** the per-prompt values correlate at Spearman **0.980** (`d_naive`) and **0.873**
  (`d_context`) — **0.966 / 0.795 within level**. The three "independent directions" are close to one
  measurement.
- And decisively: **all four fitted directions lie 100.0000% inside the same 3-dimensional subspace**
  at every layer. They are four *coordinates* of the span of the four 2×2 cell means, not four
  directions.

Comparing `d_surface` against them asks whether a different coordinate of the same space predicts.
**That is not a specificity test**, and my write-up treated it as one.

### The proper control: a random axis in that span, orthogonal to `d_surface`, three seeds

Within-level Spearman against StrongReject (the estimand that strips the designed between-level
variance):

| layer | `d_surface` | `d_inter` | **ctrl s1** | **ctrl s2** | **ctrl s3** | `hnorm` |
|---|---|---|---|---|---|---|
| L29 | +0.1334 | **−0.1368** | +0.1300 | +0.1036 | +0.1247 | −0.018 (p 0.50) |
| L30 | +0.1502 | **−0.1407** | +0.1342 | +0.1079 | +0.1288 | +0.007 (p 0.79) |
| L31 | +0.1638 | **−0.1369** | +0.1140 | +0.0894 | +0.1102 | +0.008 (p 0.71) |

**A random axis in the concept subspace, exactly orthogonal to `d_surface`, predicts ASR at 83–106%
of `d_surface`'s strength, on three independent seeds and at all three layers — matching or beating
it at L29 and L30.** (Table corrected in review #6: the first version scored from one fit payload
instead of cross-fit; the corrected numbers are stronger.) And `d_inter` — also
near-orthogonal (cos 0.008–0.087) — predicts *equally strongly with the opposite sign*.

**The boring explanation is excluded, not assumed:** residual norm predicts **nothing**
(|ρ| ≤ 0.018, p 0.50–0.79 at every layer) and token position is +0.052 (p 0.048), a third of the
effect. So this is not "any scalar predicts".

### ⛔ Requirement 4 fails — CONFIRMED, and for the first time on a control that could have passed

The verdict is unchanged; the evidence for it is now sound. **Prompt-level Boombness is not a usable
optimization target**, and the reason is sharper than "other directions also predict": the predictive
information is carried by **the 2×2 concept subspace as a whole**, with each axis picking it up at a
sign and strength set by its orientation. Optimising `d_surface` would be optimising an arbitrary
coordinate of a 3-D space.

### ✅ And this DISSOLVES the "grain disagreement" I claimed an hour ago — into something better

I wrote that `d_surface` is *causally specific* (it beats a subspace-orthogonal control at L8) yet
*correlationally non-specific*, and called that the project's sharpest open question. **It is not a
contradiction.** The same control — a random orthogonal axis in the same span — was run on both sides
tonight, and the two results are complementary:

> **Prediction is distributed across the concept subspace; causation is concentrated on one axis
> within it.**

The subspace *carries* information that tracks ASR (any axis reads some of it). Only the `d_surface`
axis, when **ablated**, *moves* ASR — the orthogonal control removes 5.4–7.3% of the same subspace's
spread and changes nothing behaviourally (L8 −0.0033, p 0.15) while still predicting correlationally
(+0.114 at L31). ⛔ **My "the two grains disagree" framing is withdrawn**; that sentence is corrected
in the Sprint Final Report.

That a direction can be **read** from a subspace without being the direction that **acts** is the
most interesting thing this sprint found, and it is exactly the representation-versus-behaviour
dissociation the project has been circling since the causal-circuit sprint.

### Limits

- One model, one bank, one position (the query occurrence), one outcome.
- Three control seeds, not a distribution; the spread across them (0.089–0.134 at L31) is real and
  not characterised.
- The within-level SEs inherit R5-4's ~11% understatement (the 15 levels share all 120 families).
- This says nothing about *what* the subspace encodes — only that the predictive part of it is not
  aligned with `d_surface` in particular.

## Sprint Final Report

**Rewritten 2026-08-21 01:30.** The previous version was written mid-sprint while the queue was
blocked and is now wrong in its headlines — it says Phase D "was not run" and Phases G and H "not
started", all three of which have since completed. Every claim below points to a committed artifact,
and every downgrade this sprint made to its own results is carried forward rather than quietly
dropped.

**One caveat governs the whole report, and it is the sprint's largest methodological finding:**
⛔ **every "the matched random control is inert" statement in this repo is inert by construction**
(R5-7). `random`/`orthogonal` are isotropic draws in R⁴⁰⁹⁶ and remove ~0.01–0.04% of the structure
the arms remove; at L8 the arm removes 84.0% of the 2×2 cell-mean spread and the isotropic control
0.005%. A **subspace-matched** control (`in_subspace_orth` — drawn inside the concept subspace,
exactly orthogonal to the arm, removing 5.35% at L8) was built and run tonight. **Run at all four `d_surface` profile depths with a deterministic basis and one judging session,
the arm beats it every time and ALL FOUR survive Holm** (arm − control: L6 +0.0127, L8 +0.0319,
L10 +0.0303, L12 +0.0364; Holm-adjusted 0.0347 / 0.0276 / 0.0347 / **0.0136**). So `d_surface`'s
causal direction-specificity is **established with correction at every depth of its profile**. ⛔ The
earlier "L12 control nearly fired at p 0.062" is **withdrawn** — that draw came from an
environment-dependent SVD basis; the deterministic replacement is 55% stronger and lands at
−0.0048, p 0.24. Every claim OUTSIDE the `d_surface` profile — the refusalness profile, Phase F's
composed controls, the Qwen3 double-random — still rests on isotropic draws, and measurement shows they
need a **different basis**: refusalness lies only 0.65–2.72% inside the cell-mean span.

### 1. What did we verify from the previous sprint?

**All six of the handover's section-0 headline claims reproduce from committed JSON** (Phase A,
14-agent fan-out, re-verified in review #1). G1 `demos_only L18` = 0.6887 of span; G3 = 75.15% of the
deletion ceiling; G2 clean ρ = −0.0660, p = 0.493, n = 108; G4 both signs suppress; AdvBench arm B
+0.0305, p_cl 0.0089; Qwen3 4/495. Seven sub-items did not reproduce as stated — three favoured the
sprint, three were citability limits. **The largest inherited risk remains D-11:** `outputs/` is
gitignored, so every judge, score and extract run is untracked.

### 2. What is `d_surface` most likely measuring?

**A generic mid-to-late semantic magnitude that is neither harm-specific nor `d_surface`-specific.**
Three independent results converge, and the third is new tonight:

- **E1 by category** (`d_surface_external_decomposition.json`): the effect is *weakest where the
  direction was fitted* — `weapons_explosives_mass_casualty` **+0.0250**, seventh of eight movable
  categories, against misinformation +0.1081 and terrorism +0.1111. Mean over 16 categories +0.0305
  (t 3.00, df 15), 8 positive / 0 negative / 8 pinned at zero, sign p 0.0039. Matched control
  −0.0062, p 0.69.
- **Phase B token level**: the demo-position gradient tracks "this codeword has a taught referent",
  not "the referent is harmful" — and ⛔ **F-2**: it is *not direction-specific*.
- **Gate D** (`clean_fig9_correlation.json`): at the prompt level `d_naive` (+0.1672) and
  `d_context` (+0.1471) predict ASR as well as `d_surface` (+0.1638). Whatever is predictive is
  carried by all three.

Plan hypothesis 3 (a hazardous-object axis) is **disfavoured**. Hypothesis 4 (an artifact of the bank
that transfers because harmful prompts share structure) is the best current fit.

### 3. Is `d_surface` separable from refusalness?

**Yes on geometry and depth; the causal half now carries the R5-7 caveat.**

- **Geometrically** (`direction_specificity_extended.json`, M6): cos = 0.1279 (L12, z 8.3) → 0.0262
  (L18, z 1.7) → 0.0176 (L20, z 1.1) against a 2,000-draw random sd of 0.01541. **At chance by L18**,
  where refusalness is causally strongest. ≤1.64% shared variance.
- **By depth**: `d_surface` L6–L12 (peak L12 +0.0322); refusalness L14–L20 (peak L18 +0.1895).
- **By robustness** (M3): **four of five** refusalness depths survive Holm (m=5); **not one** of
  eleven `d_surface` depths survives Holm (m=11), smallest adjusted 0.0618 at L12. BH keeps L8 and
  L12 at 0.0491.

⚠ The "matched inert control at every depth" that supports the profile is an isotropic control
(R5-7). The **geometry** result is untouched by that and carries the negative claim on its own.

### 4. Why does removing `d_surface` increase ASR?

**On AdvBench, entirely through the refusal gate** (`e4_pathway_advbench.json`): stratifying by the
baseline's refusal state, the effect is +0.0327 (p 0.0100) on prompts the baseline refused — 21 up,
**0 down**, 440 flat — and +0.0072 (p 0.28) on prompts it already answered. Every point of movement in
every arm is a refusal→non-refusal flip; the matched control produces zero flips.

⛔ **But the "not the content" half was never measurable** (R4-3): 29 of the 34 already-answered
prompts sit at the maximum score, so the effective n is 5 and the MDE (0.0202) is 8× the effect a
content pathway of equal relative strength would produce (0.0025). **The gate half is established;
the content half is untested.**

⚠ And this does **not** generalise: on the internal doublespeak bank the refusal gate is essentially
off (refusal rate **1.39%**, ρ(refused, ASR) = −0.042), and there the ASR variance is content quality.
The same rubric measures different things on the two datasets.

### 5. Does token-level Boombness behave differently from prompt-level?

**Yes, but neither is direction-specific.** Later demo occurrences are more concept-like than the
first (paired, family-matched +0.5414 at L8, t 3.26) and the query codeword goes the other way — but
⛔ **F-2** retracts direction-specificity at the token level, and **Gate D** independently finds the
same at the prompt level. Two grains, one conclusion.

### 6. Is there a clean Fig-9-style Boombness→ASR correlation?

**Yes — and it is not usable.** Phase D built a bank with **120 independent families per level**
across 15 levels, and the correlation is real: nested selection (210 candidates on dev → one metric
on heldout) gives **heldout ρ = +0.2982, p_cl 0.00039, permutation p ≤ 0.0005** on 900 disjoint
prompts, where G2's clean estimate was ρ = −0.066 on n = 108.

Three things bound it:
- **two thirds is the design's own manipulation** — between-level ρ +0.7024 vs within-level +0.1638;
- the within-level SEs are **~11% too small** (the 15 levels share all 120 families, R5-4); the
  family bootstrap gives 0.0333 and the effect survives (0/2,000 replicates ≤ 0);
- ⛔ **`d_naive` and `d_context` do it as well or better**, which is what fails the gate.

### 7. Are any surgical interventions actually useful?

**Yes — the single most localised causal result in the sprint** (`surgical_units.json`). Cutting
attention to the **first demonstration's codeword** reproduces the entire codeword-scope effect:
paired first − last = **+0.9949**, t 11.4, **24/24**, domain-clustered p ≈ 2e-4. It replicates on a
second, tokenisation-audited codeword — `button`: **+0.2659**, t 5.20, 21/24, p_cl 0.0046.

Bounds: ⛔ **it is token suppression, not concept re-binding** (R3-6: Δlogp_codeword −0.9449 against
Δlogp_concept +0.0268); the effect size is **lexically graded 3.6×** and the carrot arm has one more
readout query position than the other banks (R4-9), so the clean comparison is apple vs button; and
the apple bank is **void** on grammaticality.

### 8. Does the result replicate across datasets and models?

**Partly, and the inherited framing was wrong.** `cross_model_dynamic_range.json`: Qwen3's AdvBench
baseline is 0.0081 (floor) but its **ClearHarm baseline is 0.1341** and its **internal doublespeak
baseline 0.1714** — both usable. **R-17's "Qwen3 is floor-limited" is about AdvBench, not about
Qwen3.**

On the internal bank, remove-both gives **ΔASR +0.3476, p_cl 0.00028** against an inert control, and
remove-refusalness alone is **inert (−0.0048)** — the opposite of the Llama pattern. ⛔ But the
**doublespeak-specific** component is **not robust** (R5-6): +0.1254 p 0.030 as reported, +0.1142
p 0.075 stratum-matched, 4 of 6 jackknife replicates p > 0.05, +0.0478 p 0.267 under proportional
transport. And the arm cannot be decomposed — no arm B exists on that bank.

**The representational port is blocked, not negative:** the knockout stack does not run numerically on
Qwen3 (20 of 21 rows non-finite readout logits).

### 9. Is a GCG objective justified?

**No.** Three of plan §11's five candidate objectives are individually dead: probe margin (Gate C
failed — AUROC 1.0000 at every layer, reading token identity), the `d_surface` layer profile
(survives no multiplicity correction), and prompt-level Boombness (Gate D, requirement 4).

> **Prompt-level Boombness is not currently a usable optimization target.**

### 10. Strongest new findings

1. **Cutting the first demonstration's codeword reproduces the whole effect**, on two
   tokenisation-audited codewords, with `first_codeword` as its own matched positive control.
2. **`d_surface` is not harm-specific** — weakest in the category it was fitted on, 8/8 movable
   categories positive.
3. **Removing `d_surface` moves a refusal gate**, not the content behind it (established half).
4. **Prediction and causation are ANTI-ALIGNED across depth — Spearman −0.850 over 13 layers.** At
   L31 the metric predicts ASR at ρ +0.164 (p 1e-4) and ablating the same direction at the same
   layer does nothing (−0.0041, p 0.26); at L8–L12, where ablation moves ASR most, prediction is at
   its weakest. **Prediction is also distributed across the concept subspace while causation is
   concentrated on one axis within it.** A random axis in the 2×2 span, orthogonal to `d_surface`, predicts ASR at 65–95% of
   its strength (three seeds, three layers) — yet ablating that same control moves nothing (L8
   −0.0033, p 0.15) while ablating `d_surface` does (+0.0305, p 0.009). A direction can be **read**
   from a subspace without being the direction that **acts**. This is the sprint's most interesting
   finding and it subsumes what I briefly mis-framed as a disagreement between grains.
5. **Qwen3 has dynamic range on two of three datasets**, overturning an inherited blocker.
6. ⛔ **Methodological, and the most portable result here: isotropic random controls certify nothing
   in high dimensions** — and the one arm re-tested against a subspace-matched control (arm B)
   **passed**, so the criticism is about what the other controls *establish*, not about the result
   they happened to accompany. Also: StrongReject ≈ 0.9 × ASR on AdvBench, so continuous and binary
   estimands are one measurement; and a judge run with `bank=None` scores against the empty string.

### 11. What was retracted or downgraded during this sprint?

| id | claim | why |
|---|---|---|
| F-1 | Phase B gradient as a doublespeak result | no control; `benign_literal` shows the same |
| F-2 | the gradient is surface-specific | `d_context` carries 45–67% |
| F-3 | "sign reversal against a matched control" | 14.8× dose mismatch |
| C-1 | my cancellation of a peer's jobs "because they would fail" | false by 17 seconds |
| — | "bfloat16 is inadmissible" | miscalibrated guard, not bad arithmetic |
| R4-2 | "no prompt in any arm moves down" | false outside `base_refused` |
| R4-3 | "moves a gate, not the content" | the content half has effective n = 5 |
| R4-4 | R-13's mechanism, and my gate's PASS on `remBoth` | judged against the empty string |
| R4-7 | "every Llama arm passes the topicality gate" | 2 gated at the documented threshold |
| R5-1 | requirement 7 ("predictive only at L29–31") | 49/210 metrics survive Holm inside L6–L13 |
| R5-6 | Qwen3 doublespeak-specificity | fails three robustness checks |
| R5-7 | every "matched random control is inert" | inert by construction |

Plus four guards found to be **incapable of failing**: the stale-join check, the `--layers/--topk`
comparability check, `--min-separation`, and my first orthogonalisation.

### 12. What should the next sprint do?

1. ✅ **Done for `d_surface`** — L6/L8/L10/L12 all re-tested; the arm beats the subspace-matched
   control at every depth, L8 surviving Holm. ⛔ **This control CANNOT be used for
   refusalness arms**: refusalness lies only 0.6–2.7% inside the cell-mean span, so a draw from it is
   ~98% orthogonal to refusalness anyway. Controlling those needs a basis for refusal-relevant
   variance — the span of the five committed refusal directions, or the top PCs of activations on
   refused-versus-complied prompts. Phase F's composed arms and the Qwen3 double-random control are
   in the same position.
2. **Run arm B on Qwen3's internal bank** so the +0.3476 can be decomposed.
3. **Fit Llama refusal directions at L6/L8/L10** — the interaction cannot be measured inside
   `d_surface`'s own band because only five refusal directions exist on disk.
4. **Make `judge_boombness` record `prompt_sha16` and the judge model actually used**; the rubric
   falls back between two models and no artifact says which answered.
5. **Do not build the GCG objective.**
