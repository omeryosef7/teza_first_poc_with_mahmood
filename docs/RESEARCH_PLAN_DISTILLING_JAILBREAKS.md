# Research Plan: Distilling Reasoning-Model Jailbreaks into Optimizable Objectives

## 1. Research Goal
The project should now move beyond the narrow question:
Can standard GCG be adapted to jailbreak reasoning models?
The stronger research question is:
Can we take a real jailbreak attack that succeeds against a reasoning model, identify the earliest internal signal that predicts its success, validate that signal causally, and convert it into an optimization objective for generating short adversarial triggers?
The core hypothesis is:
Existing reasoning-model attacks such as Chain-of-Thought Hijacking work because they induce a specific internal state or computation pattern. If that pattern can be identified and expressed as a differentiable objective, it may be possible to reproduce the same vulnerability using a short optimized suffix rather than a long manually designed attack prompt.
The intended final contribution is therefore not simply a stronger GCG implementation. It is a pipeline:

1. Start with a real successful attack.
2. Identify its internal mechanism.
3. Validate the mechanism causally.
4. Convert it into an optimization objective.
5. Optimize short discrete triggers with TROPT and MAC.
6. Test whether the resulting attack transfers to unseen instructions, categories, and models.

## 2. Main Research Questions
The project should answer five primary research questions.
RQ1 — Baseline vulnerability
How successful are existing reasoning-specific jailbreak attacks on the exact models and instructions used in our experiments?
This establishes the attack strength that the distilled objective should aim to reproduce.
RQ2 — Predictive internal signal
What is the earliest internal signal that distinguishes successful attacks from failed attacks?
The signal may involve:

* Residual-stream representations.
* Refusal-direction projection.
* Attention allocation.
* Logit changes.
* Early reasoning-token behavior.
* Internal representations of the harmful instruction.
* Changes in how strongly the model represents safety-relevant concepts.

RQ3 — Causal mechanism
Does manipulating the discovered signal change the probability of attack success?
Correlation alone is insufficient. The signal must survive direct intervention tests.
RQ4 — Objective distillation
Can the causal signal be converted into a differentiable objective that can guide prompt optimization?
The objective should outperform or complement standard target-prefix cross-entropy.
RQ5 — Generalization
Does the objective produce triggers that generalize across:

* Unseen instructions.
* Unseen categories.
* Different optimization seeds.
* Different decoding seeds.
* Different reasoning models.
* Single-instruction and multi-instruction settings.

## 3. Overall Project Structure
The work should be divided into three connected workstreams.
Workstream A — Core mechanistic attack research
This is the primary research contribution.
Goal:
Distill Chain-of-Thought Hijacking or another real reasoning-model jailbreak into a causal, optimizable internal objective.
Workstream B — Optimization infrastructure and evaluation
Goal:
Rebuild the attack pipeline using TROPT and MAC, establish reliable baselines, and ensure that improvements are not caused by implementation details, data leakage, decoding randomness, or evaluation mistakes.
Workstream C — Category, universality, and transfer analysis
Goal:
Use the large suffix dataset and our own experiments to understand when attacks specialize, transfer, overfit, or become universal.
Workstream C should support the core mechanistic story. It should not become a disconnected data-analysis project unless the results are independently strong.

## 4. Phase 0 — Freeze the Current State
Before beginning new experiments, create a clean snapshot of the existing work.
### 4.1 Preserve the current results
Archive:

* The current presentation.
* All v1 and v2 experiment outputs.
* The placement-bug audit.
* All optimized suffixes.
* All generation outputs.
* StrongREJECT evaluations.
* Refusal-direction artifacts.
* Hidden-state detector results.
* Per-behavior optimization results.
* Current SLURM scripts.
* Current code commit.

### 4.2 Create a frozen research snapshot
Create a directory such as:

```text
research_snapshots/
└── 2026-07-post-mahmood-meeting/
    ├── README.md
    ├── code_commit.txt
    ├── presentation/
    ├── configs/
    ├── optimized_suffixes/
    ├── generation_results/
    ├── judge_results/
    ├── analysis_results/
    └── known_issues.md

```

### 4.3 Document the current conclusions
The snapshot README should state clearly:

* The original assistant-turn placement bug.
* Which experiments are unaffected by the bug.
* Which v1 numbers are invalid or provisional.
* Which v2 runs are complete.
* Which v2 runs are partial.
* Which results appear robust.
* Which results are still hypotheses.

### 4.4 Separate facts from hypotheses
Create a table with three labels:
Established
Examples:

* Standard target-prefix GCG is weak on the tested reasoning setup.
* Optimization loss does not reliably rank suffixes by behavioral ASR.
* Some intermediate checkpoints outperform final best-loss checkpoints.
* Attack performance is highly seed-dependent.
* Gemma remains resistant in the current setup.

Suggestive
Examples:

* Weak refusal-direction suppression may improve search.
* Per-behavior optimization may recover attack strength.
* Certain categories may be more vulnerable.

Unproven
Examples:

* The refusal direction is causally responsible for success.
* The current detector represents attack success rather than attack presence.
* CoT Hijacking succeeds through a specific representation-level mechanism.
* The mechanism transfers across models.

Deliverable

```text
CURRENT_STATE_AUDIT.md

```

Phase-0 completion criterion
No new large experiment should begin until every reported number can be traced to:

* A configuration.
* A suffix.
* A generation file.
* A judge result.
* A code version.

## 5. Phase 1 — Redesign the Dataset Split
The current 25-example development panel was selected from the full 520-example set. Therefore, evaluating on all 520 after optimizing on the 25 introduces overlap.
This must be corrected.
### 5.1 Construct three disjoint sets
Development set
25 instructions used for rapid iteration.
Suggested internal split:

* 20 optimization instructions.
* 5 validation instructions.

These 25 instructions must never be included in the held-out benchmark.
Held-out AdvBench set
The remaining 495 instructions.
These should be used only after an objective and configuration have passed all development gates.
External transfer set
Use a second benchmark not involved in target construction, direction construction, hyperparameter selection, or checkpoint selection.
The external dataset should be selected based on:

* Clear licensing.
* Clear harmful-behavior definitions.
* Compatibility with StrongREJECT or another robust judge.
* Minimal semantic duplication with the development set.

### 5.2 Stratify the 25-example development set
The development set should include multiple categories rather than evenly spaced rows alone.
Suggested structure:

* Cyber or hacking.
* Fraud and financial abuse.
* Misinformation.
* Weapons.
* Physical harm or violence.
* Privacy or identity theft.
* Malicious code.
* Other difficult categories.

The exact taxonomy should be stored in a versioned file.
### 5.3 Prevent hidden overlap
Check overlap at three levels:
Exact-text overlap
Exact instruction matches.
Near-duplicate overlap
High semantic similarity or minor paraphrases.
Target overlap
Different instructions that use nearly identical target completions.
Use embedding similarity plus manual review for high-similarity pairs.
### 5.4 Store a split manifest
Each row should contain:

```text
task_id
source_dataset
split
category
instruction
target_prefix
target_style
duplicate_group
notes

```

Deliverables

```text
data/manifests/dev_25.csv
data/manifests/dev_train_20.csv
data/manifests/dev_val_5.csv
data/manifests/heldout_495.csv
data/manifests/external_transfer.csv
data/manifests/split_audit.md

```

Phase-1 completion criterion
No instruction or near-duplicate instruction may appear in both development and held-out sets.

## 6. Phase 2 — Freeze the Evaluation Protocol
The evaluation protocol must be finalized before objective development. Otherwise, every objective change risks being evaluated differently.
### 6.1 Primary metric
The primary metric should be behavioral Attack Success Rate measured on free generation.
Use:
[
ASR=\frac{\text{number of successful harmful responses}}
{\text{number of evaluated generations}}
]
The primary judge should evaluate actual harmful assistance, not merely whether the model avoided refusal language.
### 6.2 Primary decoding mode
Use greedy decoding as the primary evaluation setting.
Reasons:

* Deterministic.
* Easier to reproduce.
* Less sensitive to generation seeds.
* Common for comparing optimization methods.
* Separates attack quality from sampling luck.

Suggested configuration:

```text
do_sample = false
temperature = 0
top_p = 1

```

### 6.3 Secondary decoding mode
Use sampled generation as a robustness analysis.
For example:

```text
temperature = 0.7
top_p = 0.95
generation_seeds = [100, 200, 300, 400, 500]

```

This should not replace greedy evaluation.
### 6.4 Required conditions
Every optimized trigger must be compared against:

1. No suffix.
2. Random suffix with matched token length.
3. Initialization suffix.
4. Standard GCG or MAC with target-prefix CE only.
5. The complete original attack being distilled.
6. Any relevant ablation of the new objective.

### 6.5 Required metrics
Each result row should contain several levels of success.
Optimization metric
The exact scalar objective used during optimization.
Prefix probability
Teacher-forced probability of the target prefix.
Exact prefix match
Whether the free generation begins with the exact target prefix.
Semantic prefix match
Whether the response begins with semantically compliant framing even if the exact string differs.
Refusal rate
Whether the model clearly refuses.
Harmful-compliance rate
Whether the model provides actionable harmful assistance.
StrongREJECT score
Store the raw score, thresholded label, judge version, and judge prompt version.
Generation length
Store total generated tokens and reasoning/output lengths separately where possible.
Reasoning-state features
Store the relevant internal metrics discovered later.
### 6.6 Judge validation
Before trusting the judge:

* Manually annotate a stratified sample.
* Include successes, refusals, ambiguous answers, partial compliance, and safe redirections.
* Compare human annotations to the automated judge.
* Record false positives and false negatives.
* Freeze the judge version after validation.

### 6.7 Statistical reporting
For each comparison, report:

* Raw numerator and denominator.
* ASR.
* Absolute uplift.
* Relative uplift.
* Bootstrap confidence interval.
* Paired significance test where conditions share instructions.
* Per-category results.
* Per-instruction results.
* Seed variance.

Do not report only percentages.
Deliverables

```text
EVALUATION_PROTOCOL.md
JUDGE_VALIDATION.md
configs/evaluation/greedy.yaml
configs/evaluation/sampled.yaml
schemas/evaluation_result.schema.json

```

Phase-2 completion criterion
Running the same suffix twice with the same greedy configuration must produce identical output and identical evaluation.

## 7. Phase 3 — Reproduce Baselines in TROPT
Before introducing a new objective, reproduce the current pipeline using TROPT.
The purpose is to separate:

* Improvements from the optimizer.
* Improvements from the objective.
* Improvements from implementation changes.
* Improvements from target construction.

### 7.1 Integrate the target models
Implement or validate TROPT adapters for:

* Qwen3-14B as the main model.
* Gemma reasoning model as the secondary model.
* A third model only if its clean refusal baseline leaves sufficient attack headroom.

For each adapter verify:

* Chat template.
* User and assistant turn boundaries.
* Thinking-token handling.
* EOS handling.
* Target placement.
* Suffix placement.
* Tokenization stability.
* Prefix-cache correctness.
* Hidden-state extraction.
* Gradient access.
* Generation parity with the existing pipeline.

### 7.2 Reproduce standard GCG
Run the standard target-prefix objective using:

* Existing GCG implementation.
* TROPT GCG implementation.

Use identical:

* Model.
* Instructions.
* Targets.
* Initial suffix.
* Suffix length.
* Optimization steps.
* Candidate budget.
* Decoding.
* Judge.

The result should answer:
Does TROPT reproduce our current GCG baseline within expected seed variance?
### 7.3 Reproduce MAC
Use the MAC optimizer with its recommended momentum configuration.
Initial development configuration:

```text
optimizer = MAC
suffix_length = 20
momentum = 0.6
top_k = 256
candidate_batch = 256, or largest feasible batch
num_steps = 20 for paper-faithful baseline
num_steps = extended value for compute-matched comparison

```

Run two comparisons:
Paper-faithful comparison
Use the reference MAC configuration.
Compute-matched comparison
Give GCG and MAC the same approximate number of:

* Gradient evaluations.
* Candidate evaluations.
* Forward passes.
* GPU-hours.

### 7.4 Test retokenization handling
Because retokenization behavior was previously a major implementation issue, explicitly compare:

* Retokenization filtering enabled.
* Retokenization filtering disabled.
* Constrained token set.
* Printable token set.
* ASCII-only token set.
* Full vocabulary.

Measure:

* Candidate rejection rate.
* Optimization progress.
* Final suffix token stability.
* ASR.
* Whether the decoded suffix re-encodes identically.

### 7.5 Baseline experiment matrix
Run on the 20 development-train instructions:
IDOptimizerObjectiveSettingB1Existing GCGPrefix CEPer instructionB2TROPT GCGPrefix CEPer instructionB3TROPT MACPrefix CEPer instructionB4TROPT GCGPrefix CEMulti-instructionB5TROPT MACPrefix CEMulti-instructionB6TROPT MACPrefix CEGenerated target responseB7TROPT MACCoT-prefix CEPer instructionB8TROPT MACCoT-prefix CEMulti-instruction
### 7.6 Required output
For each run store:

```text
run_id
optimizer
optimizer_seed
instruction_ids
target_style
objective_name
objective_parameters
initial_suffix
final_suffix
best_loss_suffix
checkpoint_suffixes
loss_trajectory
gradient_norms
candidate_statistics
runtime
GPU model
software commit

```

Deliverable

```text
TROPT_BASELINE_REPORT.md

```

Phase-3 decision gate
Proceed only if:

* TROPT reproduces the expected baseline behavior.
* Prompt construction is byte-verified.
* Candidate filtering is understood.
* MAC runs reliably.
* Checkpoint extraction works.
* Evaluation is identical across pipelines.

## 8. Phase 4 — Establish the Real Attack Baseline
Before distilling an attack, measure the attack itself.
The primary source attack should be Chain-of-Thought Hijacking or another reasoning-specific jailbreak with reproducible prompts.
### 8.1 Implement the original attack faithfully
Do not immediately simplify or rewrite it.
Record:

* Full attack prompt.
* Prompt structure.
* Placement of the harmful instruction.
* Reasoning scaffold.
* Any puzzle or distraction component.
* Output cue.
* Required decoding parameters.
* Whether the attack is single-turn or multi-turn.

### 8.2 Verify against the original source
Check that the implementation matches:

* The paper.
* Released code.
* Released examples.
* Author clarification, if necessary.

### 8.3 Ask authors for missing artifacts
Contact the relevant authors if the following are unavailable:

* Attack model.
* Prompt-generation model.
* Exact attack prompts.
* Evaluation scripts.
* Model checkpoints.
* Attack trajectories.
* Failure examples.

The message should clearly state that the purpose is faithful academic reproduction.
### 8.4 Run the baseline on the 25-example development set
Conditions:

1. No attack.
2. Original attack.
3. Length-matched harmless scaffold.
4. Structure-matched scaffold with the harmful instruction removed.
5. Randomized reasoning scaffold.
6. Harmful instruction alone.
7. Original attack with the puzzle or distraction removed.
8. Original attack with the target span moved.

These ablations should determine whether success comes from:

* Length.
* Structure.
* Distraction.
* Position.
* Reasoning format.
* Explicit response cue.
* Interaction between these components.

### 8.5 Measure attack headroom
For each model calculate:

```text
clean refusal rate
clean ASR
attack ASR
absolute attack uplift
number of crackable behaviors
category distribution of successes

```

A model should only remain a main target if the attack has meaningful headroom.
For example, a model with 50% clean harmful compliance is a poor primary target because attack improvements become difficult to interpret.
### 8.6 Success criterion
The original attack should show:

* Clear uplift over the clean baseline.
* More than a few isolated successes.
* Reproducibility under greedy decoding or a stable sampled protocol.
* Enough successful and failed examples for mechanistic comparison.

Deliverable

```text
REAL_ATTACK_BASELINE_REPORT.md

```

Phase-4 decision gate
Do not begin mechanistic distillation until one attack-model pair provides a sufficiently large set of both:

* Successful attacked examples.
* Failed attacked examples.

## 9. Phase 5 — Build a Mechanistic Analysis Dataset
The mechanistic dataset must distinguish attack success from attack presence.
The earlier optimized-versus-clean detector is insufficient because it may identify unusual suffix text rather than the mechanism of jailbreak success.
### 9.1 Required example groups
Collect at least the following groups:
Group A — Clean refusals
No attack, harmful instruction, model refuses.
Group B — Clean accidental compliance
No attack, model complies.
Group C — Attack failures
Attack present, model still refuses.
Group D — Attack successes
Attack present, model provides harmful assistance.
Group E — Control scaffold
Length- and structure-matched prompt without the active attack component.
Group F — Optimized suffix failures
GCG or MAC suffix present, attack fails.
Group G — Optimized suffix successes
GCG or MAC suffix present, attack succeeds.
These groups let us separate:

* Harmful content representation.
* Attack-format detection.
* Refusal.
* Compliance.
* Actual jailbreak success.

### 9.2 Pair examples whenever possible
Construct matched pairs with the same:

* Harmful instruction.
* Prompt structure.
* Attack family.
* Model.
* Decoding configuration.

Pairs should differ only in:

* Attack success.
* Optimization seed.
* Generation seed.
* Small attack variation.

Matched analysis reduces confounding by instruction category and prompt length.
### 9.3 Save internal model data
For every example collect:

* Residual stream by layer.
* Attention outputs by layer.
* MLP outputs by layer.
* Final-token and early-token hidden states.
* Logits at critical positions.
* Refusal-token probabilities.
* Target-prefix probabilities.
* Attention maps to instruction, suffix, reasoning scaffold, and system prompt.
* Thinking-token sequence where available.
* Layer-normalized activations where needed.

### 9.4 Critical positions
At minimum analyze:

1. Last input token.
2. First generated token.
3. First token inside the thinking block.
4. First five thinking tokens.
5. First ten thinking tokens.
6. Transition from thinking to final answer.
7. First final-answer token.
8. Token where refusal language begins.
9. Token where harmful content begins.

### 9.5 Metadata
Each internal-state file must include:

```text
example_id
task_id
category
condition
attack_family
attack_variant
success_label
judge_score
model
model_revision
prompt_tokens
generation_tokens
critical_positions
decoding_config
seed

```

Deliverables

```text
mechanistic_dataset/
MECHANISTIC_DATASET_CARD.md

```

Phase-5 completion criterion
The dataset must contain enough matched successes and failures to train and test predictors without reusing the same behaviors across train and test folds.

## 10. Phase 6 — Search for Predictive Internal Signals
The goal is to identify the shallowest signal that reliably predicts attack success.
“Shallowest” means:

* Earliest layer.
* Earliest token position.
* Simplest representation.
* Lowest-dimensional signal.

“Predictive” means:

* Predicts success versus failure.
* Generalizes across held-out behaviors.
* Is not merely detecting attack formatting.

### 10.1 Candidate signal families
A. Refusal-direction projection
Measure projection onto refusal-related directions.
Candidate directions:

* Harmful versus harmless difference-of-means.
* Refusal versus compliance difference-of-means.
* Attack-success versus attack-failure direction.
* Linear probe coefficient.
* Direction from an external refusal-direction method.

B. Success direction
Train a linear classifier specifically on:
[
\text{successful attacked examples}
\quad\text{vs.}\quad
\text{failed attacked examples}
]
This is more relevant than optimized-versus-clean classification.
C. Harmful-intent representation
Measure whether the model still strongly represents the harmful instruction during early reasoning.
Possible hypothesis:
Successful hijacking weakens or displaces the representation of harmful intent before the model reaches its safety decision.
D. Attention hijacking
Measure attention from early generated tokens to:

* Harmful instruction span.
* Puzzle span.
* Suffix span.
* System prompt.
* Output cue.

Possible metrics:

* Fraction of attention allocated to each span.
* Attention entropy.
* Maximum attention concentration.
* Ratio of suffix attention to harmful-span attention.
* Layer-wise movement of attention mass.

E. Compliance logits
Measure early probability assigned to:

* Refusal tokens.
* Compliance tokens.
* Thinking continuation.
* Target prefix.
* Safe-redirection phrases.

F. Reasoning-state categories
Classify early reasoning into categories such as:

* Recognizes harmful intent.
* Plans a refusal.
* Restates the task.
* Treats the task as benign.
* Follows the attacker’s reasoning scaffold.
* Begins producing an answer before safety assessment.

Use these only as behavioral descriptors unless they are tied to internal representations.
### 10.2 Layer-position sweep
For each candidate signal evaluate all combinations of:

* Layer.
* Token position.
* Signal family.
* Normalization method.

Output:

```text
AUC
accuracy
precision
recall
calibration
cross-behavior performance
cross-category performance
cross-seed performance

```

### 10.3 Strict validation splits
Do not randomly split individual generations.
Use grouped validation:

* Leave-one-behavior-out.
* Held-out behavior groups.
* Held-out categories.
* Held-out attack variants.
* Held-out optimization seeds.
* Held-out generation seeds.

### 10.4 Confound controls
For each strong signal test whether performance remains after controlling for:

* Prompt length.
* Suffix length.
* Token frequency.
* Non-ASCII token count.
* Attack family.
* Target category.
* Generation length.
* Position of the harmful instruction.

### 10.5 Signal selection rule
Choose candidate signals using a Pareto criterion:

* Earlier is better.
* Simpler is better.
* Higher cross-behavior AUC is better.
* Lower dependence on prompt formatting is better.
* Better calibration is better.

Do not automatically select the maximum-AUC signal if it occurs after the model has already generated harmful content.
Deliverable

```text
PREDICTIVE_SIGNAL_REPORT.md

```

Phase-6 decision gate
A signal should advance to causal testing only if it:

* Predicts attack success rather than attack presence.
* Generalizes to held-out behaviors.
* Appears before the final answer.
* Remains predictive after basic confound controls.

## 11. Phase 7 — Causal Validation
Predictive signals must be tested with direct interventions.
### 11.1 Activation addition and subtraction
For a direction (d), intervene at layer (l):
[
h_l' = h_l + \alpha d
]
and:
[
h_l' = h_l - \alpha d
]
Sweep:

```text
alpha ∈ {-3, -2, -1, -0.5, 0.5, 1, 2, 3}

```

The scale should be normalized relative to the natural projection distribution.
### 11.2 Intervention timing
Apply interventions at:

* Last input token.
* First generated token.
* First few thinking tokens.
* All thinking tokens.
* Final-answer transition.

The objective is to find the smallest temporal intervention that changes behavior.
### 11.3 Layer sweep
Test:

* Early layers.
* Middle layers.
* Late layers.
* Previously identified refusal-direction layers.
* Layers with maximal predictive performance.

### 11.4 Required conditions
For each intervention compare:

1. Clean harmful prompt.
2. Successful original attack.
3. Failed original attack.
4. Successful optimized suffix.
5. Failed optimized suffix.
6. Harmless prompts.

### 11.5 Causal predictions
A valid success-related direction should produce consistent effects.
For a compliance direction:

* Adding it should increase attack success or reduce refusal.
* Subtracting it should reduce attack success or increase refusal.

For a refusal direction:

* Adding it should reduce attack success.
* Subtracting it should increase attack success.

### 11.6 Specificity tests
Interventions must not simply break the model.
Measure:

* Perplexity.
* Output coherence.
* Harmless task accuracy.
* Repetition.
* Empty output rate.
* Generation length.
* General compliance on benign prompts.

A direction that causes random incoherence is not a useful causal mechanism.
### 11.7 Mediation test
Test whether the original attack changes the signal and whether manipulating the signal reduces the attack effect.
Conceptually:

1. Attack changes signal.
2. Signal predicts success.
3. Intervention on signal changes success.
4. Blocking the signal weakens the attack.

This provides a stronger mechanistic argument.
### 11.8 Attention interventions
If the candidate mechanism is attention-based, test:

* Attention masking.
* Attention rescaling.
* Blocking attention to the suffix or puzzle.
* Restoring attention to the harmful instruction.
* Equalizing attention distributions.

Deliverable

```text
CAUSAL_VALIDATION_REPORT.md

```

Phase-7 decision gate
A signal becomes an optimization-objective candidate only if intervention changes attack success without broadly destroying model quality.

## 12. Phase 8 — Construct Candidate Objectives
After identifying causal signals, convert them into losses.
### 12.1 Standard behavioral objective
Baseline:
[
L_{\text{prefix}}
-\log P(y_{\text{target}}\mid x+s)
]
where:

* (x) is the instruction.
* (s) is the suffix.
* (y_{\text{target}}) is the target prefix.

### 12.2 Refusal-direction objective
For hidden state (h_{l,p}) and refusal direction (d_r):
[
L_{\text{refusal}}
\langle h_{l,p},d_r\rangle
]
If positive projection corresponds to refusal, minimizing this term should suppress refusal.
The sign must be empirically verified.
### 12.3 Success-direction objective
For success direction (d_s):
[
L_{\text{success}}
-\langle h_{l,p},d_s\rangle
]
Minimizing this objective encourages movement toward the successful-attack state.
### 12.4 Attention-hijacking objective
Possible forms include:
Reduce attention to harmful span
[
L_{\text{harm-attn}}
\sum_{t\in T}
\sum_{j\in H}
A_{t,j}
]
where (H) is the harmful-instruction span.
Increase attention to attack scaffold
[
L_{\text{scaffold-attn}}
* 
\sum_{t\in T}
\sum_{j\in S}
A_{t,j}
]
where (S) is the suffix or reasoning scaffold.
Match attack attention pattern
[
L_{\text{attn-match}}
D\left(A(x+s), A_{\text{successful attack}}\right)
]
where (D) may be MSE, KL divergence, or cosine distance.
### 12.5 Representation-matching objective
Match the internal state induced by a successful original attack:
[
L_{\text{repr}}
\left|
h_{l,p}(x+s)
h_{l,p}(x_{\text{original attack}})
\right|_2^2
]
A normalized cosine version may be more stable:
[
L_{\text{repr-cos}}
1-\cos\left(
h_{l,p}(x+s),
h_{l,p}(x_{\text{original attack}})
\right)
]
### 12.6 Distributional semantic objective
Inspired by reinforcement-style adversarial optimization:
[
L_{\text{semantic}}
* 
\mathbb{E}_{y\sim P(\cdot\mid x+s)}
\left[
R(y,x)
\right]
]
The reward should score whether the generated response:

* Follows the malicious instruction.
* Provides substantive assistance.
* Remains relevant.
* Avoids mere affirmative language without content.

### 12.7 Composite objectives
Use explicit convex weighting:
[
L_{\text{total}}
\lambda L_A
+
(1-\lambda)L_B
]
Examples:
[
L_{\text{total}}
\lambda L_{\text{semantic}}
+
(1-\lambda)L_{\text{success}}
]
[
L_{\text{total}}
\lambda L_{\text{prefix}}
+
(1-\lambda)L_{\text{refusal}}
]
[
L_{\text{total}}
\lambda L_{\text{semantic}}
+
(1-\lambda)L_{\text{attn-match}}
]
### 12.8 Normalize objective components
Before combining losses, normalize them.
Possible methods:
Initial-value normalization
[
\tilde{L}_i = \frac{L_i}{|L_i^{(0)}|+\epsilon}
]
Z-score normalization
Use the distribution over random suffixes.
Gradient-norm balancing
Scale components so their gradient norms are initially comparable.
Running normalization
Maintain a running mean and variance during optimization.
The selected normalization must be logged.
### 12.9 Lambda sweep
Use:

```text
lambda ∈ {0, 0.1, 0.25, 0.5, 0.75, 0.9, 1}

```

Start with the smaller set:

```text
lambda ∈ {0, 0.25, 0.5, 0.75, 1}

```

Only refine around promising regions.
Deliverable

```text
OBJECTIVE_SPECIFICATION.md

```

## 13. Phase 9 — Soft Optimization as an Upper-Bound Test
Before spending significant compute on discrete tokens, test each objective with a continuous soft prompt.
### 13.1 Purpose
The soft prompt answers:
Is the objective controllable at all through the input?
If a continuous prompt with unconstrained embeddings cannot meaningfully change the objective or behavior, a short discrete suffix is unlikely to succeed.
### 13.2 Soft-prompt setup
Optimize a sequence of continuous embeddings of lengths:

```text
5
10
20
40

```

Keep the base model frozen.
### 13.3 Run per instruction first
For each candidate objective:

* Optimize separately on 5 representative instructions.
* Use multiple initialization seeds.
* Save the entire optimization trajectory.

### 13.4 Evaluate four levels
For each optimized soft prompt measure:

1. Objective improvement.
2. Internal-signal movement.
3. Prefix-match change.
4. Behavioral ASR change.

### 13.5 Interpretation matrix
Case A
Objective improves, signal moves, ASR improves.
This is the ideal objective. Proceed to discrete optimization.
Case B
Objective improves, signal moves, ASR does not improve.
The signal may not be causally sufficient, or the objective targets the wrong position.
Case C
Objective does not improve.
The objective may be poorly conditioned or uncontrollable from the input.
Case D
ASR improves without the intended signal moving.
The mechanism hypothesis may be wrong, or another optimization path is being used.
### 13.6 Compare against soft prefix CE
Every new soft objective must be compared to:

* Soft prefix CE.
* Random soft prompt.
* Soft refusal-direction objective.
* Combined objective.

Deliverable

```text
SOFT_OPT_UPPER_BOUND_REPORT.md

```

Phase-9 decision gate
Only objectives that show a meaningful behavioral or causal effect under soft optimization should proceed to large discrete MAC experiments.

## 14. Phase 10 — Discrete Optimization with TROPT and MAC
This phase tests whether the mechanistic objective can produce actual token suffixes.
### 14.1 Initial experiment scope
Use only the 20 development-train instructions.
Do not evaluate the 495 held-out instructions yet.
### 14.2 Optimizers
Compare:

* TROPT GCG.
* TROPT MAC.
* Random coordinate search if useful.
* Soft-to-discrete initialization if supported.
* Current custom GCG only as a legacy baseline.

### 14.3 Objective matrix
IDObjectiveO1Prefix CEO2CoT-prefix CEO3Refusal directionO4Success directionO5Attention objectiveO6Representation matchingO7Semantic reward proxyO8Prefix CE + refusal directionO9Semantic objective + success directionO10Semantic objective + attention objective
### 14.4 Optimize per behavior first
Start with one suffix per instruction.
Reasons:

* Easier optimization.
* Higher attack ceiling.
* Better for testing objective validity.
* Avoids conflating objective quality with universality constraints.

### 14.5 Checkpoint policy
Save suffixes at:

```text
step 0
step 10
step 20
step 50
step 100
step 200
step 300
step 400
final
best objective

```

For short MAC runs, save every step.
### 14.6 Selection policies
Compare four suffix-selection policies.
Final-step selection
Use the final suffix.
Best-objective selection
Use the suffix with lowest optimization objective.
Validation-prefix selection
Use the suffix with best prefix behavior on validation generations.
Validation-ASR selection
Use the suffix with best free-generation ASR on a small validation seed set.
This directly tests the previous observation that the best checkpoint may occur before the final optimization step.
### 14.7 Avoid selection leakage
Use separate generation seeds for:

* Checkpoint selection.
* Final reporting.

For example:

```text
selection seeds = [10, 20, 30]
reporting seeds = [100, 200, 300, 400, 500]

```

Greedy evaluation remains separate and primary.
### 14.8 Candidate evaluation policy
The earlier refusal-direction term only influenced candidate proposals while acceptance was based on task CE.
This must be tested explicitly.
Compare:
Proposal-only objective
New term affects gradients but not candidate ranking.
Evaluation-only objective
Candidates are proposed using CE but ranked with the new objective.
Full objective
New term affects both gradient proposals and candidate ranking.
Two-stage ranking
First shortlist by differentiable proxy; then rank by a more expensive semantic or free-generation score.
### 14.9 Compute-matched comparison
All optimizer comparisons should match either:

* Number of candidate evaluations.
* Number of backward passes.
* GPU-hours.

Report which budget is matched.
Deliverable

```text
DISCRETE_OBJECTIVE_COMPARISON.md

```

Phase-10 decision gate
An objective should advance only if it improves behavioral ASR over prefix CE on:

* Multiple behaviors.
* Multiple optimization seeds.
* At least one validation behavior not used for optimization.

## 15. Phase 11 — Distributional and Reinforcement-Style Optimization
This phase operationalizes the insight that fixed target-prefix likelihood is not equivalent to behavioral attack success.
### 15.1 Motivation
A suffix can make “Sure” likely without causing harmful compliance.
A behavioral objective should reward complete generated responses rather than a fixed opening string.
### 15.2 Reward design
Construct a reward with components such as:
[
R =
w_1R_{\text{instruction-following}}
+
w_2R_{\text{harmful-detail}}
+
w_3R_{\text{relevance}}
w_4R_{\text{refusal}}
w_5R_{\text{nonsense}}
]
The reward must not over-reward:

* Repetition.
* Empty compliance.
* Restating the request.
* Vague agreement.
* Non-actionable content.

### 15.3 Reward-model validation
Manually inspect high-reward and low-reward outputs.
Test for reward hacking:

* Repeating harmful keywords.
* Producing target prefix only.
* Long irrelevant answers.
* Judge manipulation.
* Empty reasoning followed by refusal.
* Safe fictional framing without actionable help.

### 15.4 Efficient proxy strategy
Because free-generation rewards are expensive and often non-differentiable:

1. Use a differentiable proxy objective to generate candidates.
2. Free-generate from the top candidate subset.
3. Score those generations with the semantic reward.
4. Use reward to select candidates or checkpoints.

### 15.5 Compare optimization approaches
Offline ASR selection
Optimize normally, then select checkpoints using generation reward.
Online periodic ASR selection
Every (K) steps, generate and score the current suffix.
Candidate reranking
At selected steps, free-generate from multiple candidates and rerank them.
Learned differentiable reward proxy
Train a lightweight model to predict semantic reward from internal states or logits.
Policy-gradient-style update
Use sampled outputs and reward estimates where computationally feasible.
### 15.6 Key comparison
The most important comparison is:
MethodCandidate proposalCandidate selectionStandard GCGPrefix CEPrefix CECurrent RD methodCE + RD gradientPrefix CEASR-selected GCGPrefix CEGeneration rewardMechanistic MACMechanistic objectiveMechanistic objectiveHybrid methodDifferentiable proxyGeneration reward
Deliverable

```text
DISTRIBUTIONAL_OBJECTIVE_REPORT.md

```

## 16. Phase 12 — Multi-Instruction and Universal Optimization
Only begin this phase after per-instruction optimization demonstrates that the objective works.
### 16.1 Distinguish settings clearly
Single-instruction attack
One suffix optimized for one harmful instruction.
Category-specific attack
One suffix optimized over several instructions from one category.
Multi-category attack
One suffix optimized over instructions from several categories.
Universal attack
One suffix optimized to transfer broadly to unseen instructions.
These settings must never be merged into one aggregate result.
### 16.2 Training-set sizes
Test:

```text
1 instruction
3 instructions
5 instructions
10 instructions
20 instructions

```

### 16.3 Category conditions
For each category with enough examples:

* Train within category, test within category.
* Train within category, test outside category.
* Train across categories, test within known categories.
* Train across categories, test on unseen categories.

### 16.4 Universality versus specialization
Measure:

* Mean ASR.
* Median ASR.
* Number of behaviors cracked.
* Category coverage.
* Worst-category ASR.
* Transfer to unseen instructions.
* Transfer to unseen categories.
* Trigger diversity.
* Sensitivity to optimization seed.

### 16.5 Gradient aggregation strategies
Compare:

* Mean gradient across instructions.
* Sum of normalized gradients.
* Worst-case instruction objective.
* Random instruction minibatches.
* Category-balanced minibatches.
* Curriculum from easy to hard.
* Momentum across batches.

### 16.6 Objective aggregation strategies
Compare:
[
L_{\text{mean}}=\frac{1}{N}\sum_i L_i
]
[
L_{\text{max}}=\max_i L_i
]
[
L_{\text{weighted}}=\sum_i w_iL_i
]
[
L_{\text{CVaR}}=\text{mean of worst-performing fraction}
]
Worst-case or CVaR objectives may reduce domination by easy behaviors.
Deliverable

```text
SINGLE_VS_MULTI_INSTRUCTION_REPORT.md

```

## 17. Phase 13 — Analyze the Large GCG Suffix Dataset
This should run in parallel with the mechanistic work.
### 17.1 Ingest and validate the dataset
Inspect:

* Available columns.
* Missing values.
* Duplicated instructions.
* Duplicated suffixes.
* Model identities.
* Optimization method.
* Objective type.
* Training membership.
* Universality labels.
* Evaluation score.
* Generation outputs.

### 17.2 Create a reliable category taxonomy
Because AdvBench does not provide an official category taxonomy, the category labels must be treated as an analysis tool rather than ground truth.
Use a two-stage process:

1. Automated initial labeling.
2. Manual validation and correction.

Store:

* Primary category.
* Secondary category.
* Confidence.
* Labeling rationale.

### 17.3 Core analyses
A. Within-category performance
Does a suffix perform best on the category it was optimized on?
B. Cross-category transfer
Which category pairs transfer well?
Create a transfer matrix:
[
M_{i,j}
ASR(\text{suffix trained on category }i,\text{tested on }j)
]
C. Single versus multi-instruction suffixes
Compare:

* Average ASR.
* Category coverage.
* Unseen-instruction performance.
* Seed robustness.
* Suffix length.
* Token composition.

D. Train versus unseen instructions
Measure genuine transfer separately from performance on optimization instructions.
E. Universality rank
Examine whether more universal suffixes share:

* Attention patterns.
* Token patterns.
* Internal-state effects.
* Prefix behavior.
* Refusal-direction effects.

F. Lexical and token-level commonalities
Analyze:

* Non-ASCII frequency.
* Language mixture.
* Punctuation.
* Imperative words.
* Response-prefill phrases.
* Roleplay markers.
* Formatting tokens.
* Repeated token patterns.

Do not assume lexical commonality implies a causal mechanism.
G. Objective-dependent behavior
Compare suffixes trained with:

* Prefix CE.
* Refusal suppression.
* Other objectives.
* Different optimizers.

### 17.4 Mechanistic subset
Select representative suffixes:

* Highly universal.
* Category-specific.
* High training ASR but low transfer.
* Low training ASR but high transfer.
* High refusal-direction shift.
* Low refusal-direction shift.

Run internal-state analysis on this subset.
Deliverables

```text
DATASET_ANALYSIS_REPORT.md
CATEGORY_TRANSFER_MATRIX.csv
SUFFIX_TAXONOMY.csv

```

## 18. Phase 14 — Held-Out Evaluation
Only run this phase after selecting the objective and optimizer using the development set.
### 18.1 Freeze the final configuration
Before opening the held-out 495 instructions, freeze:

* Objective.
* Objective normalization.
* Lambda.
* Optimizer.
* Optimization budget.
* Suffix length.
* Target style.
* Candidate-selection method.
* Checkpoint-selection policy.
* Decoding.
* Judge.

No further tuning on held-out results.
### 18.2 Evaluate multiple attack settings
Per-instruction setting
Optimize separately for a stratified held-out subset if compute allows.
Category-specific setting
Apply category-specific suffixes to unseen instructions in the same category.
Universal setting
Apply universal suffixes to all 495 held-out instructions.
### 18.3 Compare against baselines
Required baselines:

* No attack.
* Random suffix.
* Standard GCG.
* MAC with prefix CE.
* Original CoT Hijacking.
* Best existing objective.
* New mechanistic objective.
* Distributional reward objective.
* Hybrid objective.

### 18.4 Report complete denominator coverage
Do not mix partial evaluations with complete evaluations.
For each result report:

```text
completed examples
planned examples
missing examples
failed jobs
judge failures
generation failures

```

### 18.5 Statistical analysis
Use:

* Paired bootstrap confidence intervals.
* McNemar test for paired binary outcomes.
* Category-level bootstrap.
* Seed-level variance.
* Behavior-level union metrics only as secondary analyses.

Clearly separate:

* Per-generation ASR.
* Per-behavior any-seed success.
* Per-suffix success.
* Ensemble success.

Deliverable

```text
HELDOUT_495_FINAL_REPORT.md

```

## 19. Phase 15 — External Dataset Transfer
After completing held-out AdvBench evaluation, test external transfer.
### 19.1 No new tuning
The final configuration must be applied without adjusting:

* Lambda.
* Target.
* Optimizer.
* Selection policy.
* Suffix.
* Judge threshold.

### 19.2 Measure two forms of transfer
Dataset transfer
Does the same suffix or objective work on a different harmful-instruction benchmark?
Prompt-style transfer
Does it work when instructions are phrased differently from AdvBench?
### 19.3 Duplicate control
Remove examples semantically overlapping with:

* Development instructions.
* Held-out AdvBench instructions.
* Target-response templates.

Deliverable

```text
EXTERNAL_TRANSFER_REPORT.md

```

## 20. Phase 16 — Cross-Model Generalization
Only perform cross-model experiments after the main result is established on Qwen3.
### 20.1 Models
Use models with:

* A meaningful clean refusal rate.
* A visible reasoning process or reasoning mode.
* Accessible gradients for white-box optimization.
* Stable generation code.

### 20.2 Cross-model questions
Objective transfer
Does the same kind of mechanistic signal exist across models?
Layer transfer
Does the signal appear at analogous relative depths?
Trigger transfer
Does a suffix optimized on one model work on another?
Direction transfer
Does a refusal or success direction trained on one model transfer after alignment or projection?
Optimizer transfer
Does MAC outperform standard GCG consistently across architectures?
### 20.3 Avoid poor-headroom models
If a model already complies with a large fraction of harmful requests without attack, report that as a baseline failure and do not use it as the main generalization result.
Deliverable

```text
CROSS_MODEL_GENERALIZATION_REPORT.md

```

## 21. Phase 17 — Defensive Interpretation
The current Qwen3 detector result can become a defensive contribution, but only after stronger validation.
### 21.1 Change the prediction target
The current detector distinguishes attacked prompts from clean prompts.
The next detector should distinguish:
[
\text{successful attack}
\quad\text{vs.}\quad
\text{failed attack}
]
### 21.2 Test adaptive attacks
An adaptive attacker may optimize against the detector.
Test:
[
L_{\text{attack+evasion}}
L_{\text{attack}}
+
\beta L_{\text{detector}}
]
This asks whether attack success and detectability can be traded off.
### 21.3 Compare detector types

* Logistic regression.
* Linear probe.
* Small MLP.
* Refusal-direction threshold.
* Success-direction threshold.
* Attention-based detector.
* Logit-based detector.

### 21.4 Detection timing
Measure detection at:

* Last input token.
* First generated token.
* First five thinking tokens.
* Before final-answer generation.

The most valuable detector is one that can intervene before harmful content appears.
### 21.5 Defense intervention
Possible defense:

1. Detect suspicious internal state.
2. Increase refusal-direction activation.
3. Re-run or redirect generation.
4. Compare with simply refusing the request.

Deliverable

```text
ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md

```

## 22. Experiment Tracking and Reproducibility
Every run must be represented by one immutable configuration.
### 22.1 Run identifier
Suggested format:

```text
MODEL__SPLIT__OPTIMIZER__OBJECTIVE__LAMBDA__SEED__DATE

```

Example:

```text
qwen3-14b__dev20__mac__successdir-prefixce__l050__s42__20260722

```

### 22.2 Required configuration fields

```yaml
run_id:
model:
model_revision:
chat_template:
dataset_manifest:
instruction_ids:
optimizer:
optimizer_seed:
generation_config:
suffix_length:
initial_suffix:
num_steps:
candidate_batch:
top_k:
momentum:
objective:
objective_components:
objective_normalization:
lambda:
target_style:
checkpoint_policy:
selection_policy:
judge:
judge_version:
code_commit:
slurm_job_id:

```

### 22.3 Required artifact hierarchy

```text
runs/<run_id>/
├── config.yaml
├── environment.txt
├── stdout.log
├── stderr.log
├── checkpoints/
├── suffixes.jsonl
├── optimization_trace.jsonl
├── free_generations.jsonl
├── judge_results.jsonl
├── metrics.json
└── summary.md

```

### 22.4 Result validation script
Create one script that verifies:

* Expected row count.
* No duplicate evaluation rows.
* All suffixes are present.
* All conditions are present.
* All judge scores are present.
* No train-test overlap.
* No missing generations.
* No inconsistent denominators.
* Configuration hash matches the run directory.

### 22.5 Central results table
Maintain one append-only table:

```text
results/EXPERIMENT_REGISTRY.csv

```

Columns should include:

```text
run_id
status
model
split
optimizer
objective
lambda
opt_seed
selection_policy
greedy_asr
sampled_asr
neutral_asr
random_asr
uplift
n_success
n_total
runtime_hours
notes

```

## 23. Compute Strategy
### 23.1 Do not start with full-scale evaluation
The correct order is:

1. One instruction.
2. Five representative instructions.
3. Twenty development-train instructions.
4. Five validation instructions.
5. Held-out subset.
6. Full held-out evaluation.
7. External transfer.

### 23.2 Cheap-to-expensive ordering
For each new objective:

1. Check scalar and gradients.
2. Test on stored activations if possible.
3. Run causal intervention.
4. Run soft optimization.
5. Run short discrete optimization.
6. Run full discrete optimization.
7. Run free-generation selection.
8. Run held-out scale evaluation.

### 23.3 SLURM job classes
Create separate launchers for:

* Activation extraction.
* Causal interventions.
* Soft optimization.
* Per-instruction discrete optimization.
* Multi-instruction optimization.
* Generation evaluation.
* Judge evaluation.
* Analysis.

### 23.4 Resume safety
Every large job must:

* Write outputs incrementally.
* Skip completed examples.
* Verify existing rows before resuming.
* Avoid overwriting finished runs.
* Record failed task IDs.
* Support array resubmission only for missing tasks.

### 23.5 Early stopping
Stop an optimization run when:

* Objective has not improved for a defined number of steps.
* Suffix repeats or cycles.
* Free-generation validation has not improved across several checkpoints.
* The objective becomes numerically unstable.
* The trigger becomes invalid under tokenization.

## 24. Statistical and Scientific Standards
### 24.1 Avoid development-set overclaiming
Results on 25 examples are for:

* Debugging.
* Objective comparison.
* Hypothesis generation.

They are not final benchmark claims.
### 24.2 Report uncertainty
For small evaluations such as 10 generation seeds per behavior, report wide confidence intervals.
Do not describe 30% versus 10% as stable without uncertainty.
### 24.3 Control multiple comparisons
Large sweeps over:

* Layers.
* Positions.
* Lambdas.
* Seeds.
* Objective variants.

can produce false discoveries.
Use:

* Held-out validation.
* Multiple-comparison correction where appropriate.
* Predefined selection rules.
* Final frozen held-out evaluation.

### 24.4 Distinguish exploratory and confirmatory experiments
Every report should label experiments as:

* Exploratory.
* Validation.
* Confirmatory.

The final held-out experiment must be confirmatory.
### 24.5 Keep negative results
Record:

* Objectives that improved loss but not ASR.
* Signals that predicted but were not causal.
* Models without attack headroom.
* Categories where attacks failed.
* Seeds that collapsed.
* Soft objectives without discrete realizability.

These negative results are scientifically valuable and prevent repetition.

## 25. Decision Tree
Gate 1 — Does the original attack work?
No

* Verify implementation.
* Try the second most credible reasoning-specific attack.
* Select a model with clearer vulnerability and stronger refusal baseline.
* Do not proceed to mechanistic distillation without enough successful examples.

Yes
Proceed to predictive-signal analysis.
Gate 2 — Is there a success-predictive internal signal?
No

* Expand signal families.
* Use matched success/failure pairs.
* Analyze later positions.
* Test nonlinear probes.
* Examine attention and logits.
* Reconsider whether the attack uses multiple heterogeneous mechanisms.

Yes
Proceed to intervention.
Gate 3 — Is the signal causal?
No

* Treat it as a detector only.
* Do not use it as the main mechanistic objective.
* Test alternative signals.
* Consider multivariate mechanisms.

Yes
Proceed to objective construction.
Gate 4 — Does soft optimization manipulate the signal and behavior?
No

* The signal may not be controllable from the input.
* Change the layer, position, or objective formulation.
* Test a composite objective.
* Do not spend large discrete compute yet.

Yes
Proceed to discrete MAC optimization.
Gate 5 — Does the discrete objective beat prefix CE?
No

* Test normalization.
* Test proposal-only versus full-objective integration.
* Test more suitable candidate selection.
* Test soft-to-discrete initialization.
* Test distributional checkpoint selection.

Yes
Proceed to validation and universality.
Gate 6 — Does it generalize to the five validation instructions?
No

* The objective may overfit.
* Add multi-instruction training.
* Add category balancing.
* Reduce objective complexity.
* Avoid held-out scaling.

Yes
Freeze the configuration and evaluate on the 495 held-out instructions.

## 26. Immediate Priority Order
The next work should occur in the following order.
Priority 1 — Evaluation cleanup

1. Create the disjoint 25/495 split.
2. Freeze greedy decoding.
3. Add explicit target-prefix match metrics.
4. Validate the judge.
5. Build the experiment registry.
6. Finish or clearly mark all partial v2 evaluations.

Priority 2 — TROPT reproduction

1. Install and validate TROPT.
2. Reproduce prefix-CE GCG.
3. Reproduce MAC.
4. Verify suffix placement and target placement.
5. Compare existing code against TROPT on identical prompts.
6. Confirm checkpoint extraction.

Priority 3 — Real attack baseline

1. Implement CoT Hijacking faithfully.
2. Run it on the 25-example development set.
3. Run the length- and structure-matched controls.
4. Quantify clean versus attacked ASR.
5. Identify crackable and non-crackable behaviors.

Priority 4 — Mechanistic dataset

1. Collect successful and failed attack generations.
2. Extract activations, attention, and logits.
3. Create matched success/failure pairs.
4. Train success-versus-failure probes.
5. Search for the earliest generalizing signal.

Priority 5 — Causal validation

1. Test refusal-direction addition and subtraction.
2. Test success-direction addition and subtraction.
3. Test layer and token-position sweeps.
4. Measure attack success and benign-task degradation.
5. Select only causally supported signals.

Priority 6 — Objective experiments

1. Implement the causal objective.
2. Implement soft optimization.
3. Compare against prefix CE.
4. Normalize objective components.
5. Sweep lambda.
6. Move successful objectives to TROPT MAC.

Priority 7 — Distributional optimization

1. Reproduce checkpoint ASR selection systematically.
2. Separate selection seeds from reporting seeds.
3. Add generation-based candidate reranking.
4. Compare with semantic reward optimization.
5. Test hybrid mechanistic and behavioral objectives.

Priority 8 — Category and universality analysis

1. Download and validate the suffix dataset.
2. Build the category taxonomy.
3. Analyze train versus unseen performance.
4. Compare single- and multi-instruction suffixes.
5. Build the cross-category transfer matrix.
6. Select suffixes for mechanistic comparison.

Priority 9 — Scale

1. Freeze the best configuration.
2. Evaluate on the five development-validation examples.
3. Open the 495 held-out set.
4. Evaluate external dataset transfer.
5. Test cross-model transfer.

## 27. Concrete First Experiment Package
The first complete experimental package should contain the following.
Package A — Baselines
Run on the 20 development-train examples:

1. No suffix.
2. Random 20-token suffix.
3. Existing GCG with prefix CE.
4. TROPT GCG with prefix CE.
5. TROPT MAC with prefix CE.
6. Original CoT Hijacking.
7. Length-matched control prompt.
8. Structure-matched control prompt.

Primary evaluation:

* Greedy ASR.
* Prefix match.
* Refusal rate.
* StrongREJECT.
* Runtime.
* Per-category results.

Package B — Refusal-direction verification
For each example:

1. Measure natural refusal-direction projection.
2. Compare clean refusal, attack failure, and attack success.
3. Add and subtract the direction during inference.
4. Sweep layer, position, and intervention strength.
5. Measure ASR and benign degradation.

Package C — Success-direction discovery

1. Train a success-versus-failure linear probe.
2. Use grouped cross-validation by behavior.
3. Identify the earliest strong layer-position pair.
4. Convert the probe vector into an intervention direction.
5. Test addition and subtraction.

Package D — Soft-objective upper bound
Compare:

1. Prefix CE.
2. Refusal direction.
3. Success direction.
4. Prefix CE plus success direction.
5. Semantic reward proxy.

Run on five representative instructions.
Package E — Initial MAC objective test
For objectives that pass Package D:

1. Run per-instruction MAC.
2. Use three optimization seeds.
3. Save all checkpoints.
4. Compare final, best-loss, and best-validation-ASR selection.
5. Report greedy results on the five validation instructions.

## 28. Expected Final Paper Story
A strong final project could tell the following story:

1. Standard target-prefix adversarial-suffix optimization is poorly aligned with actual jailbreak success on reasoning models.
2. Existing reasoning-specific jailbreaks succeed through an identifiable early internal mechanism.
3. The discovered signal predicts attack success across held-out instructions and is not merely a detector of attack formatting.
4. Direct intervention on the signal changes jailbreak probability, demonstrating causal relevance.
5. Converting the signal into an optimization objective improves short-trigger attacks over standard prefix CE.
6. A hybrid mechanistic and semantic objective provides the strongest or most stable performance.
7. The resulting triggers show measurable transfer across instructions and categories.
8. Universal transfer remains harder than per-instruction optimization, revealing a tradeoff between attack specialization and universality.
9. The same internal signal may support early attack detection or defensive intervention.

## 29. Minimum Publishable Outcome
The project does not need to solve every phase to be valuable.
A minimum publishable result would be:

1. A rigorous reproduction showing that canonical GCG underperforms on reasoning models.
2. A clean demonstration that target-prefix loss is poorly correlated with harmful behavioral success.
3. A real reasoning-model attack with sufficient success.
4. A success-predictive internal signal that generalizes across behaviors.
5. A causal intervention showing that the signal affects attack success.
6. Initial evidence that optimizing the signal improves attack search or checkpoint selection.

A stronger result would additionally include:

* A new discrete trigger objective.
* TROPT/MAC implementation.
* Held-out transfer.
* Category generalization.
* Cross-model validation.
* Adaptive detection or defense.

## 30. Final Strategic Principle
The project should not continue as a sequence of loosely connected suffix sweeps.
Every new experiment should answer one of four questions:

1. Does a real attack work?
2. What internal mechanism predicts its success?
3. Is the mechanism causal?
4. Can the mechanism be optimized into a shorter or more transferable attack?

The central workflow is:
[
\text{Real Attack}
\rightarrow
\text{Predictive Signal}
\rightarrow
\text{Causal Validation}
\rightarrow
\text{Soft Objective}
\rightarrow
\text{MAC Trigger}
\rightarrow
\text{Held-Out Transfer}
]
This should be the organizing structure for the codebase, experiments, future presentations, and eventual paper.

---

## 31. Phase 4X — Cross-Model CoT-Hijacking Benchmark (AMENDMENT — added on user request 2026-07-21)

**Logical position:** executes **after Phase 4** (§8, the gpt-o4-mini dev-25 CoT-Hijacking baseline)
and before Phase 5 (§9). Added by the plan owner; the rest of the plan (§1–30) is unchanged.

### 31.1 Goal
Measure how **general** the reasoning-model vulnerability is: run the *same* CoT-Hijacking attack
on the *same* 25 development goals against **≥3 additional thinking models** beyond gpt-o4-mini.
This gives RQ1 breadth and identifies which model(s) have enough attack headroom to serve as a
white-box mechanistic target later (Phases 5–7).

### 31.2 Model set — OPEN-SOURCE thinking models ONLY (≥3 NEW; user hard constraint 2026-07-21)
**Do NOT attack proprietary / public-API models** (no gpt-*, gemini-*, grok, claude as *targets*).
The attack TARGET must be an **open-source, locally-run HF thinking model**. "New" = beyond Qwen3
(the GCG work). Candidates (all open-weight reasoning models):
  - `gemma` — the group's "gemma4" (prior `gemma4-e4b-it` / `google/gemma-3-*`) — **user-requested**
  - `deepseek-ai/DeepSeek-R1-Distill-Llama-8B` — reasoning, Llama-based (non-Qwen), MIT
  - `microsoft/Phi-4-reasoning` (or `Phi-4-mini-reasoning`) — native reasoning, open (MIT)
  - (optional 4th) another open reasoning model, e.g. `nvidia/*-reasoning` or a QwQ variant if a
    non-Qwen set isn't reachable.
**Note:** the attacker LM and judge remain Gemini API (that's the harness, not a *target under
attack*); only the **target** must be open-source. If the user wants attacker/judge open-source
too, swap them to a local model as a follow-up.

### 31.3 Constraint — DO NOT cache local model weights (user)
Local HF model weights must **not** be persisted to the project HF cache (`.cache/huggingface`).
Download to **node-local ephemeral storage** (`$SLURM_TMPDIR` or `/tmp/$SLURM_JOB_ID`) via
`HF_HOME`/`HF_HUB_CACHE`, wiped when the job ends. API targets have no weights (n/a).

### 31.4 Method (reuse, no new attack logic; open-source target only)
- Same dev-25 goals (`data/manifests/dev_25.csv`), same StrongREJECT scoring
  (`slurm_scripts/run_strongreject_cpu.slurm`, frozen protocol §6). Reuse
  `poc_stage2/run_phase4_cot_baseline.py`.
- The CoT-Hijacking core currently targets models via LiteLLM (API only). Add a **local open-source
  HF target path** so the **target** is a local thinking model run on GPU (l40s). Options to
  evaluate (minimal, reuse-first): (a) serve the local model behind a local OpenAI-compatible
  endpoint (vLLM) that LiteLLM calls at `api_base=localhost`; or (b) a minimal HF-`generate()`
  target backend implementing the core's target interface. Weights → node-local ephemeral storage
  (31.3), NOT the project cache.
- ~~API-target track~~ REMOVED per user (2026-07-21): do not attack proprietary API models.

### 31.5 Deliverables
Per model: behavior-level **StrongREJECT ASR** (any-stream ≥0.5) + gemini-judge ASR, per-category
breakdown, clean-vs-attacked headroom, and a `results/EXPERIMENT_REGISTRY.csv` row.
Cross-model synthesis: `docs/CROSS_MODEL_COT_BENCHMARK_REPORT.md` — which reasoning models are
most/least vulnerable and how that tracks model family / thinking style.

### 31.6 Decision gate
A model with meaningful attack headroom **and** white-box access becomes a candidate mechanistic
target feeding Phase 5+. API-only models give breadth but cannot be dissected mechanistically.

---

## Working Rules (operational constraints for whoever executes this plan)

* Don't run more than 6 SLURM runs at once. Use the configs that you know are working. If you have anything in pending for more than 30m, cancel and resubmit.
* Don't write a lot of unnecessary code — just things that actually matter.
* After every change you made, run another subagent that checks that you have no bug.
* Always document your progress with path references in another md file (after every time you do something, make sure it's documented).
* Don't change this md! This is the plan.
