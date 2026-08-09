# Next Sprint Plan — Doublespeak / In-Context Representation Hijacking (2026-08-09)

We are continuing the Doublespeak / In-Context Representation Hijacking causal-mechanism project.

DO NOT start this as a fresh project and DO NOT blindly rerun experiments that are already completed.

First read the existing repository, especially the current sprint summary / master log / experiment registry / causal reports, and reconstruct exactly what has already been run, what is VERIFIED, what is NULL/NEGATIVE, what is UNDERPOWERED, and what was designed but never executed.

The point of this next sprint is to CONTINUE the work we just reported to Mahmood and Matan and close the highest-value remaining questions.

============================================================
0. CURRENT SCIENTIFIC STATE — TREAT THIS AS THE STARTING POINT
============================================================

The current result on Llama-3.1-8B-Instruct is:

1. Doublespeak computes a real concept-remap circuit:
   - demo-codeword retrieval around L8–L10
   - strongest MLP write around L9
   - distributed carry through roughly L14–L21
   - late concept readout
   - patching all codeword occurrences strengthened the representational effect versus demo-only patching.

2. But this concept circuit is NOT the behavioral cause of the jailbreak:
   - powered whole-circuit concept ablation: ΔASR ≈ +0.046, ns
   - matched random ablation: ≈ +0.161
   - therefore the concept circuit is epiphenomenal BY SPECIFICITY, not simply “nonexistent” or “equivalent to zero”.

3. Refusal suppression is a separate, near-orthogonal computation and is the behavioral lever:
   - concept/refusal cosine is near zero across layers
   - refusal ablation strongly increases harmful behavior
   - refusal restoration suppresses Doublespeak
   - decision-token refusal-state restoration cuts ASR on train/dev
   - train/dev mediation is ≈ full
   - refusal projection predicts jailbreak outcome
   - prospective predictor: train AUC ≈ 0.80; frozen test AUC ≈ 0.97, but test has only 7 positives / 42 examples
   - Jacobian readout also predicts behavior; concept Jacobian is much weaker/inert.

4. Attention/path results already obtained:
   - query→demo-codeword attention-edge KO is a clean negative
   - demo K/V content is necessary but no single edge is
   - candidate-head activation patching indicates a distributed mechanism
   - no single head bottleneck
   - head→MLP path patching failed to expose a clean sparse route
   - therefore do NOT rerun the same broad experiments unless required by a specific new hypothesis/control.

5. Attack-objective result so far:
   - first-cut refusal-derived GCG objective improves ASR
   - BUT a norm-matched random direction performs essentially identically:
       refusal ≈ 0.465
       random ≈ 0.464
   - only 2 seeds / short run / incomplete arm matrix
   - conclusion currently = NEGATIVE / NON-SPECIFIC / FIRST-CUT, not a formal final null.

6. Defense:
   - refusal restoration genuinely reduces ASR on train (~−0.22 at best layer)
   - but causes substantial over-refusal on attack-structured benign prompts
   - unrelated-normal prompts show zero over-refusal.
   This is interesting, but the attack-objective question is higher priority this sprint.

7. Cross-model:
   - Qwen3-14B thinking-off reproduces the concept-vs-refusal dissociation.
   - refusal ablation raises ASR ≈ +0.17–0.19
   - concept ablation is approximately null.
   - We now want a THIRD MODEL FAMILY, preferably a THINKING / reasoning model.

8. Quantization:
   - refusal-ablation robustness has already been tested under bf16 / 8-bit / 4-bit.
   - Do NOT waste compute simply rerunning that exact result.
   - Quantization work in this sprint should extend the pieces that have NOT yet been checked under quantization.

The paper-level hypothesis we are now testing is:

    A model can causally compute the harmful semantic remapping without that
    representation being the cause of harmful behavior. Instead, a separate
    refusal-control variable determines behavior.

And the second question is:

    Even if a representation is genuinely causal for behavior and highly
    predictive of jailbreak success, does that imply that it is a useful
    token-space optimization objective?

The first-cut GCG result currently says “probably not”.
This sprint must turn that into a properly controlled conclusion.

============================================================
1. NON-NEGOTIABLE WORKING RULES
============================================================

Carry forward ALL of the working rules from the previous plans.

COMPUTE / SLURM
---------------
- Maximum 6 concurrent SLURM GPU jobs. NEVER exceed 6.
- Real runs: L40S only.
- Use:
    --partition=killable
    --account=gpu-research
    --gpus=1
    --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
- Do NOT use gpu-sharifm.
- No SLURM dependencies.
- If a job is PENDING for >30 minutes, cancel and resubmit appropriately.
- Smoke-test every new runner/config before scaling.
- bf16 is the canonical precision for primary causal claims.
- Login-node GPU can only be used for tiny float16 code-validation smoke tests, not scientific runs.
- Never launch a giant sweep before validating one tiny end-to-end run.

MODEL/CACHE RULES
-----------------
- No new model-weight downloads without explicit human approval.
- Use cached weights only and force offline mode:
    HF_HOME=$PROJECT_DIR/.cache/huggingface
    HF_HUB_CACHE=$HF_HOME/hub
    HF_HUB_OFFLINE=1
    TRANSFORMERS_OFFLINE=1
- Cached models include at least:
    meta-llama/Llama-3.1-8B-Instruct
    Qwen/Qwen3-14B
    microsoft/Phi-4-mini-reasoning
    DeepSeek-R1-Distill-Llama-8B
- For the third-family experiment, PRIORITIZE Phi-4-mini-reasoning because it gives us a genuinely different architecture/family and is a reasoning model.
- DeepSeek-R1-Distill-Llama-8B can be a secondary reasoning replication if useful, but it does not replace a third architectural family.

DATA / STATISTICS
-----------------
- ClearHarm is the PRIMARY dataset.
- Reuse the existing LOCKED ClearHarm split. DO NOT silently create a new split.
- Split/cluster assignment must happen BEFORE any layer/head/objective/hyperparameter selection.
- Train data can be used for:
    objective construction
    direction fitting
    λ selection
    layer selection
    hyperparameter selection
    early stopping choices
- Locked test can ONLY be used after those decisions are frozen.
- Never optimize or select an arm based on test performance.
- Minimum 20 UNIQUE examples per experimental cell.
- Repeated generations / seeds DO NOT count toward the n>=20 requirement.
- Prefer the full existing ClearHarm train/test cells whenever computationally feasible.
- Preserve intent-cluster separation and all existing leakage checks.
- Never pool train/test.
- Never pool non-exchangeable cohorts just to obtain significance.
- Report n and denominator with every percentage.
- Keep all nulls and negative results.
- Use paired tests wherever possible:
    paired bootstrap CIs
    exact McNemar for paired binary behavior
    permutation tests
    Wilcoxon where appropriate
    Holm-Bonferroni for families of tests
- Report effect size + CI, not only p-values.
- The existing practical between-run ASR variation is ~6pp; very small between-run effects should not be overinterpreted.
- Prefer within-run paired arm comparisons.

EVALUATION
----------
IMPORTANT: use the CURRENT Doublespeak evaluation protocol from this sprint.
Do NOT accidentally resurrect an older CoT-Hijacking evaluation threshold/config.

- StrongREJECT continuous score + current 3-way behavioral label.
- MALICIOUS threshold = the currently validated sprint threshold (0.25).
- Preserve all outputs, including empty/degenerate generations, in denominators.
- Track:
    StrongREJECT score
    MALICIOUS / REJECTED / BENIGN label
    refusal rate
    empty rate
    stop reason
    generation length
- The earlier max_new_tokens=200 setting caused substantial truncation, especially in one cohort.
  For new confirmatory generation runs, first smoke-test a larger generation budget and freeze a value that makes truncation negligible before running the matrix.
- Do not change generation length separately by arm.

SCIENTIFIC INTEGRITY
--------------------
- A predictive signal is NOT automatically a mechanism.
- A causal activation intervention is NOT automatically a token-space optimization objective.
- A concept representation that is causally necessary for semantic readout is NOT automatically causally necessary for behavior.
- Do not call a result “specific” unless it beats appropriate matched random controls.
- Do not claim “inert” when the supported statement is “epiphenomenal by specificity”.
- Do not claim Qwen reproduces every fine-grained Llama circuit result; it currently reproduces the high-level concept-vs-refusal dissociation.
- Keep exploratory / confirmatory / underpowered labels explicit.
- Negative results are first-class results.
- Never hide an arm because it makes the story weaker.

CODE QUALITY
------------
- Reuse existing code. Do NOT reinvent loaders, model wrappers, StrongREJECT, token localization, hooks, GCG/MAC infrastructure, etc.
- TROPT-FIRST:
  before implementing a new optimizer, determine whether the desired objective can be expressed through existing TROPT loss/recipe/GCGPlus/CombinedLoss infrastructure.
- Do not edit upstream TROPT unless absolutely unavoidable; prefer project-local wrappers.
- Every new module or meaningful code change:
    1. unit/smoke test
    2. independent adversarial code-review pass
- Review specifically:
    chat-template boundaries
    suffix placement
    target placement
    tokenizer round-trip
    all codeword occurrence detection
    cached generation hooks
    native EOS
    thinking tokens
    truncation
    gradient sign
    random-vector normalization
    direction sign
    test leakage
    duplicate rows
    resume behavior
    stale caches
    judge denominators

IMPORTANT cluster safeguard:
- Subagents must NOT inspect harmful generation text.
- Harmful prompt/generation handling remains in the main agent or SLURM pipeline.
- Subagents may inspect benign code, scalar outputs, schemas, statistics, plots, and aggregation logic.

RESULT MANAGEMENT
-----------------
- Results must be written incrementally.
- Every run must be resumable.
- Resume ONLY missing indices.
- NEVER overwrite completed result files.
- Give every run:
    config hash
    git commit
    model
    dtype/quantization
    seed
    split
    objective arm
    optimizer
    steps
    suffix length
    timestamp
- Add every scientific run to the experiment registry.
- Maintain an append-only execution log.
- After every meaningful phase, document:
    hypothesis
    implementation
    commands/jobs
    exact paths
    sample sizes
    result
    statistics
    interpretation
    limitations
    next gate
- Git commit is allowed.
- Do NOT git push.

DO NOT MODIFY THE OLD MASTER RESEARCH PLAN.
Create a new continuation plan/log for this sprint.

============================================================
2. PHASE 0 — AUDIT FIRST; DO NOT REPEAT FINISHED WORK
============================================================

Before writing new experimental code:

A. Read all current Doublespeak causal reports and raw result paths.

At minimum locate and reconcile:
- current sprint summary
- DOUBLESPEAK_MASTER_LOG.md
- RESULTS_SYNTHESIS.md
- CAUSAL_RESULTS_SUMMARY.md
- EXPERIMENT_REGISTRY.csv
- GATE7_EXECUTION_PLAN / GCG objective reports
- Jacobian readout report + implementation
- Qwen cross-model report
- quantization report
- powered concept-ablation report
- Gate-B / mediation reports
- head-edge / head-MLP path reports

B. Build:

docs/NEXT_SPRINT_PLAN_2026_08_09.md
docs/NEXT_SPRINT_EXECUTION_LOG.md
docs/NEXT_SPRINT_GAP_MATRIX.md

The gap matrix must classify every requested item as:

DONE — no rerun needed
DONE BUT NEEDS CONFIRMATION
PARTIAL
UNDERPOWERED
NOT RUN
NEW

Specifically audit these old requests:

1. query-codeword → demo-codeword attention-edge KO
2. candidate induction-head activation patching
3. head→MLP path patching
4. all-codeword-occurrence patching
5. Jacobian / projection-based readout
6. clean separation of concept/refusal directions
7. corrected Doublespeak baseline
8. GCG under corrected setup
9. ClearHarm migration
10. quantization

Do NOT rerun something merely because it appears in this prompt.
Only rerun it if:
- the old run is invalid,
- a bug is discovered,
- the new objective matrix needs an exactly compute-matched instance,
- the third-model replication requires it,
- or we need a confirmatory replication with a corrected protocol.

============================================================
3. PHASE 1 — FREEZE THE CORRECTED BASELINE
============================================================

Before the new optimization study, make sure all arms share the same current protocol.

On Llama-3.1-8B bf16 / ClearHarm:

Confirm in one compute-matched pipeline:
- DIRECT
- NEUTRAL
- DOUBLESPEAK
- no-suffix harmful baseline
- vanilla GCG baseline
- MAC/TROPT baseline where applicable
- random/length-matched suffix control

Use >=20 unique train and >=20 unique locked-test items.
Prefer the complete existing ClearHarm split.

The purpose is NOT to rediscover Doublespeak.
The purpose is to guarantee that the new GCG objective arms are compared under exactly the same:
- prompt construction
- chat template
- generation budget
- judge
- denominator
- suffix length
- optimizer budget
- seed handling

Audit stop_reason and eliminate the previous 200-token truncation problem.

Gate 1:
If baselines do not reproduce within a reasonable run-to-run envelope, STOP scaling and diagnose first.

============================================================
4. PHASE 2 — MECHANISTIC CLOSURE / ATTENTION
============================================================

Most of the old attention questions are already answered.

Do NOT launch another indiscriminate all-head/all-edge sweep.

Instead:

A. Reconfirm the NEGATIVE at high specificity only if needed:
   query codeword → demonstration codeword attention edge.

B. Targeted induction-head path test:
   Take only the strongest already-discovered candidate heads / layers.
   Perform a targeted sender→receiver intervention that tests whether the retrieved binding travels through a specific induction-style route.

Controls:
- matched random heads
- matched random source positions
- self donor
- shuffled donor
- same number of ablated edges
- general-attention knockout positive control

Primary readout:
- existing safe concept readout
- Jacobian/projection readout where useful

Behavioral readout:
- only for the strongest targeted intervention, because we already know the concept circuit is behaviorally weak.

The purpose is NOT to force a sparse circuit to exist.
A clean “still distributed / no specific path” is a valid final result.

C. ALL CODEWORD OCCURRENCES:
This has already produced a stronger representational effect.
Verify the old result from raw artifacts.
Use all occurrences by default in any NEW concept-side intervention unless the hypothesis explicitly concerns query-only or demo-only positions.
Always use count-matched position controls.

============================================================
5. PHASE 3 — JACOBIAN / PROJECTION-MATRIX READOUT
============================================================

We already have an existing Jacobian result:
- refusal Jacobian predicts outcome
- concept Jacobian is much weaker
- mid-layer Jacobian sensitivity is distinct from late readout.

DO NOT throw this implementation away.

Read the exact existing P6 Jacobian code/report and reconstruct the mathematics.

I previously referred to this as the “Jacobian / projection-matrix approach from Anthropic”.
Do NOT use that label in the paper/code unless the implementation actually matches a specific cited method.
Document exactly what WE compute.

Required outputs per layer:
- scalar projection
- Jacobian / sensitivity magnitude
- train/test AUC
- bootstrap CI
- concept vs refusal paired comparison
- location of sensitivity peak vs ordinary readout peak

Most importantly, turn the Jacobian quantity into a differentiable candidate optimization loss for the next phase.

Before using it in GCG:
run a gradient/sign sanity test:
- one tiny continuous perturbation in the predicted improving direction
- verify the target metric moves in the predicted direction
- verify a matched random direction does not systematically do so.

============================================================
6. PHASE 4 — THE MAIN EXPERIMENT: FULL ATTACK-OBJECTIVE MATRIX
============================================================

THIS IS THE HIGHEST PRIORITY OF THE SPRINT.

The current 0.465 refusal vs 0.464 random result is only a first-cut negative.
We need to determine whether that negative survives a properly powered, compute-matched matrix.

FIRST:
Find the already-designed but never fully executed 13-arm matrix in the repository
(GCG_MAC_EVALUATION / GATE7 plan or equivalent).

Do not silently replace it.

Reconcile that matrix with the latest requested objectives below.
If an old arm is now scientifically redundant, document why before removing it.

At minimum, the final matrix must contain these families:

A. BASELINES
1. no attack / no suffix
2. vanilla GCG objective
3. vanilla MAC/TROPT objective where comparable

B. REFUSAL-PROJECTION OBJECTIVES
4. validated refusal projection objective
5. norm-matched random-direction objective

C. JACOBIAN OBJECTIVES
6. refusal-Jacobian / sensitivity objective
7. matched random Jacobian/control objective

D. CONCEPT OBJECTIVES
8. concept-direction objective
9. concept-Jacobian objective or the closest mathematically valid concept analogue

These are IMPORTANT NEGATIVE CONTROLS because the concept circuit is representationally causal but behaviorally epiphenomenal.

E. COMBINED OBJECTIVES
10. standard attack loss + refusal projection
11. standard attack loss + refusal Jacobian
12. concept + refusal objective
13. best causally justified combined mechanism objective from the existing Gate-7 design

If the old 13-arm plan contains better-defined versions, preserve those definitions.

Random-control discipline:
Every mechanism objective MUST have a compute-matched and norm-matched random control.
If there are multiple vector magnitudes / layers, random controls must match those too.

CRITICAL:
Do NOT select the best layer using test ASR.

Layer / parameter choices:
- choose based on existing causal validation or train only
- freeze before test.

For refusal, prioritize already validated layers (e.g. L16/L18 area) rather than searching test.
For Jacobian, use the already identified train-side peak unless the existing implementation dictates otherwise.
For concept, use the already validated causal concept-write/readout location appropriate for that objective.

--------------------------------
OPTIMIZATION BUDGET
--------------------------------

The old result used only 2 seeds and short optimization.

New confirmatory target:
- minimum 3 seeds
- TARGET 5 seeds if compute permits
- seeds must be identical across arms
- same initialization distribution
- same suffix length
- same candidate budget
- same number of optimizer steps
- same evaluation cadence.

Do not call a multi-seed result “confirmed” from 2 seeds.

Steps:
- smoke: ~5–10 steps on 1–3 items
- pilot: ~50–100 steps
- confirmatory: at least ~200 steps
- for finalists / ambiguous refusal-vs-random comparisons, extend to ~500 steps if runtime permits.

Do NOT compare a 500-step mechanism arm against a 50-step random arm.

Use early stopping only if the stopping rule is fixed identically across arms.

--------------------------------
TRAIN / TEST
--------------------------------

Use >=20 unique training examples.
Use >=20 unique locked-test examples.
Prefer all available ClearHarm samples.

All of:
- objective weights
- λ
- layer
- suffix length
- optimizer hyperparameters
- arm selection
must be frozen from train.

Then evaluate ONCE on locked test.

If the optimization unit is per-behavior rather than a shared universal suffix, preserve the existing attack setup, but the same principle applies:
all global method/hyperparameter selection is train-only.

--------------------------------
MECHANISTIC VALIDITY CHECK
--------------------------------

This is essential.

For every optimized suffix, do not report only ASR.

Measure whether the optimizer actually changed the intended internal mechanism:

- refusal projection before → after
- refusal Jacobian metric before → after
- concept projection before → after
- concept readout where relevant
- refusal rate
- ASR
- StrongREJECT score

Then ask:

1. Did the mechanism-derived objective move its intended internal target more than random?
2. Did moving that target improve behavior more than random?
3. Across examples/seeds, does objective change mediate or predict ASR improvement?
4. Did random succeed by simply being another useful optimization signal?

This distinction is central to the paper.

Possible final outcomes:

A. refusal objective > random:
   mechanism is causal, predictive, AND gives a specific token-space optimization lever.

B. refusal objective ≈ random:
   causal/predictive activation-space mechanism does NOT directly translate to a specific token-space attack objective.

C. random > refusal:
   even stronger negative; investigate optimization geometry without hiding it.

Any of these is publishable if cleanly controlled.

--------------------------------
GCG + MAC
--------------------------------

Do not test only one optimizer if the objective can be expressed in both.

TROPT-FIRST:
- attempt the mechanism objective in the existing GCG/TROPT/MAC infrastructure.
- Keep optimization budgets compute-matched.
- Distinguish:
    optimizer effect
    objective effect

At minimum answer:
“Does the mechanism-derived objective beat its random counterpart under GCG?”
and, if expressible:
“Does the conclusion survive MAC/TROPT?”

Do not build a new optimizer just to obtain a positive result.

============================================================
7. PHASE 5 — THIRD MODEL FAMILY: THINKING MODEL
============================================================

Priority model:
    microsoft/Phi-4-mini-reasoning

Reason:
- cached
- white-box
- reasoning model
- different architectural family from Llama and Qwen.

Do this in stages.

STAGE X0 — compatibility smoke
- load offline
- native chat template
- native EOS
- verify reasoning tokens / answer parsing
- verify codeword localization AFTER templating
- verify generation works
- no scientific claim from the smoke.

STAGE X1 — behavioral reproduction
On locked ClearHarm with >=20 examples/cell:
- Direct
- Neutral
- Doublespeak
- structurally matched controls

Report:
- ASR
- refusal
- generation length
- stop reason
- native reasoning behavior

Do NOT disable reasoning merely to copy Qwen.
Use the model’s native reasoning mode as the primary third-family condition.
If a clean official thinking-off mode exists and is trivial to run, it may be a secondary comparison.

STAGE X2 — separate directions
Fit on train only:
- concept direction
- refusal direction

Measure:
- layer-wise geometry
- cos(concept, refusal)
- concept readout
- refusal projection
- train vs locked test.

STAGE X3 — causal dissociation
Run only the minimum experiments needed to answer the cross-family hypothesis:

CONCEPT:
- strongest validated concept-side ablation
- all codeword occurrences
- count-matched random control

REFUSAL:
- validate refusal direction causally first
- refusal ablation
- random ablation control

Question:
Does refusal intervention change behavior substantially more than concept intervention?

STAGE X4 — prediction
If sufficient positive/negative behavioral outcomes exist:
- refusal projection AUC
- concept projection AUC
- Jacobian versions if computationally practical.

STAGE X5 — optional objective transfer
ONLY after X1–X4:
take the best/final Llama mechanism objective and its random control
and run a small frozen cross-model GCG test.

Do NOT retune it on Phi test.

If Phi has no meaningful attack headroom or no Doublespeak effect:
that is a result.
Do not force the model into giving us the desired story.

If useful after Phi, a SECONDARY reasoning-style replication may use cached DeepSeek-R1-Distill-Llama-8B, but Phi has priority because we specifically want a third architecture family.

============================================================
8. PHASE 6 — QUANTIZATION EXTENSION
============================================================

This is exploratory and comes AFTER the bf16 confirmatory work.

Existing result:
refusal-ablation causality already survives bf16 / 8-bit / 4-bit.

Therefore do NOT simply rerun that.

Instead fill the missing quantization gaps on Llama:

At minimum compare bf16 vs 8-bit vs 4-bit for:
1. concept-vs-refusal geometry
2. concept behavioral ablation vs matched random
3. refusal predictor / projection
4. if feasible, the FINAL two attack-objective arms:
      best mechanism objective
      matched random objective

Use >=20 unique examples/cell.

Important:
Primary paper claims remain bf16.
Quantization is a robustness/exploration section.

Two useful analyses:
A. REFIT:
   fit directions separately in each precision.

B. TRANSPORT:
   fit in bf16 and apply to 8/4-bit.

This tells us whether the mechanism itself persists or only a precision-specific fitted direction does.

Do this only if it can be implemented cleanly without blowing the compute budget.

============================================================
9. DECISION GATES
============================================================

Use explicit gates. Do not keep spending GPU just because a phase exists.

GATE A — corrected setup
Baselines and evaluator are stable.
If not: fix before optimization.

GATE B — objective implementation
The candidate loss actually moves its intended internal scalar in a gradient/sign sanity test.
If not: do not launch 5-seed GCG.

GATE C — pilot specificity
After pilot:
mechanism objective is compared with matched random.
If mechanism is clearly worse AND the intended internal scalar is not moving:
debug.
If mechanism scalar moves correctly but ASR does not beat random:
that is scientifically meaningful; proceed to confirmatory seeds to establish the negative.

GATE D — full objective conclusion
After >=3 seeds, preferably 5:
classify:
SPECIFIC POSITIVE
NON-SPECIFIC NEGATIVE
UNDERPOWERED
IMPLEMENTATION FAILURE

Do not merge the last two.

GATE E — third model
Only claim cross-family dissociation after both:
- concept intervention
- refusal intervention
have appropriate random controls.

GATE F — quantization
Exploratory only; cannot overturn bf16 primary conclusion.

============================================================
10. WHAT I WANT AT THE END OF THIS SPRINT
============================================================

I do NOT want a giant pile of scripts.

I want clear answers to these questions:

Q1.
Does the GCG negative survive a full, fair arm matrix with more seeds and more optimization steps?

Q2.
Does a Jacobian-based refusal objective outperform the simple refusal-projection objective?

Q3.
Does ANY refusal-derived objective beat a norm-matched random objective?

Q4.
Does adding the concept term help, hurt, or do nothing?

Q5.
Does the mechanism change that the optimizer is supposed to induce actually occur internally?

Q6.
Does the representation≠behavior dissociation reproduce in a third architecture family, ideally Phi-4-mini-reasoning?

Q7.
Does the dissociation/objective conclusion survive quantization beyond the refusal-ablation result we already have?

============================================================
11. REQUIRED FINAL DELIVERABLES
============================================================

Maintain throughout:
- docs/NEXT_SPRINT_EXECUTION_LOG.md
- results/EXPERIMENT_REGISTRY.csv

At the end produce:

1. docs/NEXT_SPRINT_FINAL_SYNTHESIS.md
   Very detailed.
   Separate:
   OBSERVATIONAL
   PREDICTIVE
   CAUSAL-REPRESENTATIONAL
   CAUSAL-BEHAVIORAL
   OPTIMIZATION
   NEGATIVE
   CROSS-MODEL
   ROBUSTNESS

2. docs/ATTACK_OBJECTIVE_FULL_MATRIX.md
   Include every arm, seed, optimizer, steps, n, train/test, ASR, CI, internal-target movement, random-control comparison.

3. docs/THIRD_FAMILY_REPLICATION.md

4. docs/QUANTIZATION_EXTENSION.md

5. docs/PAPER_CLAIM_TABLE.md
   One row per potential paper claim:
   claim
   supporting experiments
   exact n
   train/test
   effect
   CI/p
   model
   status:
       VERIFIED
       NEGATIVE
       UNDERPOWERED
       WITHDRAWN
       EXPLORATORY
   limitations

6. docs/PAPER_OUTLINE_V1.md

The paper outline should be structured around this story:

I. Doublespeak causes a real semantic remapping.
II. We causally map the concept circuit.
III. Surprisingly, destroying that circuit does not destroy the jailbreak.
IV. A separate, nearly orthogonal refusal state causally determines behavior.
V. That refusal state predicts jailbreak outcome.
VI. Representation therefore dissociates from behavior.
VII. A further dissociation may exist:
    causal/predictive activation-space control ≠ useful token-space optimization objective.
VIII. Cross-model + robustness.

7. Produce a SHORT Slack-ready summary for Mahmood and Matan:
   max ~10 bullets
   only the highest-value results
   every number verified against raw artifacts.

============================================================
12. AUTONOMOUS EXECUTION
============================================================

Do not stop after writing the plan.

Execute it.

Start with:
1. repository/result audit
2. write the gap matrix
3. identify the exact existing 13-arm Gate-7 design
4. implement/smoke the missing objective arms
5. launch the first <=6-job package

Keep no more than 6 GPU jobs alive at once.

When jobs finish:
- analyze them
- update the log
- run bug review
- make the next decision based on the gate
- submit the next batch.

If something is scientifically negative, DO NOT “fix” it until it becomes positive.
Verify it, control it, and report it.

If you discover that something I asked for has ALREADY been convincingly completed, mark it DONE and move on rather than burning compute.

The goal of this sprint is not the maximum number of experiments.

The goal is to convert the current result into the strongest defensible paper story, with special emphasis on CAUSAL evidence, specificity controls, train/test discipline, and results that remain interesting even when they are negative.
