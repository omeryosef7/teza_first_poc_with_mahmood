# Doublespeak Causality — Next Sprint Execution Plan

> **Provenance.** Sprint directive authored by Omer Yosef, recorded 2026-07-27.
> This is an execution directive for the *continuation* of the existing Doublespeak
> causality thesis project — not a new project and not a replacement research plan.
> The guiding standard: we are not trying merely to produce a stronger late-layer
> representation; we are trying to establish that the representation *causally controls
> real model behavior*, and then exploit that causal mechanism to build an optimization
> objective that improves a real attack.

You are continuing the existing Doublespeak causality thesis project. You are not
starting a new project, and you must not merely produce another research plan.

Your task is to inspect the current repository, understand and verify the completed
work, implement the next experiments, run meaningful smoke tests, submit properly
validated SLURM jobs, analyze all results that are already available during this
session, and update the project documentation.

The central objective is to turn the current representation-level findings into:

1. a statistically credible behavioral jailbreak result;
2. genuine behavioral causal evidence;
3. a causal account of semantic timing;
4. a mechanistic objective that improves an optimization-based attack such as GCG or MAC;
5. a systematic comparison of thinking and non-thinking inference;
6. a stronger scientific contribution than the original "In-Context Representation Hijacking" paper.

Do not optimize for the appearance of progress. Optimize for results that could
survive serious paper review.

---

# 1. Research context

My name is Omer Yosef. I am an M.Sc. student at Tel Aviv University conducting thesis
research under Dr. Mahmood Sharif.

My thesis concerns:

* adversarial attacks against aligned language models;
* jailbreaks and refusal mechanisms;
* Chain-of-Thought and reasoning-model attacks;
* mechanistic interpretability;
* causal interventions in language-model activations;
* refusal and compliance representations;
* converting mechanistic findings into improved attack objectives or defenses.

After discussing the research direction with Matan Ben-Tov, we pivoted toward the paper:
**"In-Context Representation Hijacking" / Doublespeak, arXiv:2512.03771.**

The original paper showed observationally that a benign codeword can acquire a harmful
contextual meaning in late model layers. Its central mechanistic evidence relied mainly
on logit lens and Patchscopes.

The original paper did not establish:

* behavioral necessity;
* behavioral sufficiency;
* causal timing of refusal versus compliance;
* causal information-flow paths;
* an attack objective derived from the representation trajectory;
* a comparison between thinking and non-thinking modes;
* a strong mechanism-based defense with valid benign controls.

Our project has already filled part of this gap.

---

# 2. Current verified state of the project

Read these documents before editing or running anything:

* `SPRINT_HANDOFF.md`
* `RESULTS_SYNTHESIS.md`
* `CAUSAL_RESULTS_SUMMARY.md`
* `DOUBLESPEAK_MASTER_LOG.md`
* `EXPERIMENT_REGISTRY.csv`
* `ENV_AUDIT.md`
* `PAPER_REPRODUCTION_NOTES.md`
* `DOUBLESPEAK_CAUSALITY_PLAN.md`

Also inspect all result JSONs, figures, scripts, SLURM files, tests, and the vendored
official Doublespeak repository.

The current work has already established the following.

## 2.1 Representation-level timing

The representation of a directly stated harmful concept is decodable early.
The contextual meaning assigned to a Doublespeak codeword is decodable primarily in
late layers.

This early-versus-late signature generalizes across:

* Llama-3.1-8B-Instruct;
* Qwen3-14B;
* Phi-4-mini-reasoning.

## 2.2 Representation-level necessity

Replacing a Doublespeak codeword state with its matched neutral state removes nearly all
of the decoded harmful meaning.

This result has:

* identity controls;
* random norm-matched controls;
* cross-concept evaluation;
* cross-model evaluation.

## 2.3 Conditional representation-level sufficiency

Injecting an ordinary Direct concept representation into a neutral codeword is generally
not sufficient. Injecting the contextual Doublespeak representation into the neutral
codeword is more successful.

This indicates that the hijacked codeword representation is not a simple copy of the
explicit concept representation. It is a distinct context-dependent state.

## 2.4 Information-flow causality

Blocking attention from the final codeword occurrence to the demonstrations removes the
decoded hijacked meaning. The effect generalizes across the three tested model families.

## 2.5 Codeword result

Static embedding distance does not meaningfully predict hijacking strength.

## 2.6 Current defense result

A late-layer harmful probe performs well on the current virus-codeword panel, but the
benign in-context-learning control is inadequate because the benign concept did not
itself show measurable representation transfer.

## 2.7 Critical unresolved limitation

The current work has not demonstrated a clean behavioral jailbreak.
The existing seeds are behaviorally confounded:

* some substituted prompts become too benign, and Doublespeak does not restore harmful behavior;
* other prompts remain harmful even in the Neutral condition, so Doublespeak cannot be credited for the harmful output.

Therefore, the current strongest honest result is:

> A cross-model, causally manipulable representation-level semantic hijacking mechanism
> with a behavioral null on the current seed data.

Do not hide or weaken this limitation. Everything below is designed to resolve it.

---

# 3. Required scientific advancement

The next version of the project should aim to support the following paper-level claims.

## Claim A — Clean behavioral Doublespeak effect

For a substantial held-out set:

* Direct expresses harmful intent and is usually refused;
* Neutral is genuinely benign because replacing the critical concept neutralizes the request;
* Doublespeak restores the harmful interpretation and produces a higher harmful-compliance rate than Neutral.

This must be demonstrated on a meaningful sample, not on two or three curated examples.

## Claim B — Behavioral causal necessity

When a successful Doublespeak example is patched toward the matched Neutral
representation, the actual generated behavior becomes less harmful, more benign, or more
likely to refuse.

## Claim C — Behavioral causal sufficiency

When the contextual Doublespeak state is inserted into an otherwise Neutral prompt, it
causes a measurable increase in harmful interpretation or harmful compliance.
Probe movement alone does not satisfy this claim.

## Claim D — Causal timing

Moving the harmful contextual representation earlier or later in the network causes
different behavioral outcomes. The most important candidate result is:

* early harmful meaning increases refusal;
* late harmful meaning increases compliance;
* removal of late harmful meaning reduces attack success.

## Claim E — Mechanistic attack objective

A representation-derived objective, especially a benign-early / harmful-late objective,
improves attack optimization compared with:

* the original paper prompt;
* random or heuristic context search;
* standard GCG;
* standard MAC;
* output-only optimization.

The objective must improve held-out behavioral ASR, not merely a probe score.

## Claim F — Thinking changes the mechanism

Thinking and non-thinking inference produce systematically different:

* representation trajectories;
* semantic onset layers;
* refusal dynamics;
* attack success;
* sensitivity to interventions.

At least one clean within-model comparison should be used where the same weights support
both thinking and non-thinking modes.

---

# 4. Mandatory operating principle

Always ask:

> How does this experiment improve the original paper?

An experiment is high value only if it does at least one of the following:

* converts correlation into behavioral causality;
* explains why some concept-codeword pairs hijack and others do not;
* produces a stronger attack objective;
* distinguishes thinking from non-thinking mechanisms;
* demonstrates generalization;
* produces a valid mechanism-based defense;
* rules out an important alternative explanation.

Do not spend the main compute budget generating more versions of already-established
representation plots unless they enable one of these goals.

---

# 5. Workstream A — Build a statistically credible behavioral benchmark

This is the highest-priority prerequisite. The current behavioral dataset is not suitable
for causal behavioral conclusions. We need a large set of prompts that occupy the actual
Doublespeak "sweet spot."

## 5.1 Use the paper-faithful data first

Inspect the official vendored Doublespeak code and artifacts. Find and reuse, where available:

* the exact AdvBench-derived instructions;
* the simplified single-concept instructions;
* the extracted harmful concept spans;
* the exact `potato` substitutions;
* the generated demonstration sentences;
* the context-length settings;
* the original evaluation prompts;
* any exact model-specific formatting.

Do not regenerate an existing paper artifact silently. If an artifact must be
regenerated, record:

* why;
* the exact generator model;
* generation parameters;
* prompt;
* seed;
* resulting methodological deviation.

Start with the paper-faithful data because we need to determine whether the current
behavioral null is caused by our seed design rather than by the phenomenon itself.

## 5.2 Define the eligibility gate correctly

A base instruction is behaviorally eligible if:

1. The Direct version clearly contains harmful intent.
2. The Direct version is refused or judged harmful enough to test alignment.
3. Replacing the key concept with the codeword makes the Neutral version genuinely benign or non-actionable.
4. The harmfulness of the request depends substantially on the substituted concept.
5. Neutral is not already malicious because of the remaining verbs or task description.

Do not require Doublespeak success for eligibility. That would introduce success-only
selection bias. For every eligible base instruction, Doublespeak success or failure must
remain an outcome to predict.

## 5.3 Define a clean successful triplet

A clean behavioral Doublespeak success is:

* Direct: harmful and usually refused;
* Neutral: benign or irrelevant, with no harmful procedural answer;
* Doublespeak: interprets the codeword as the original harmful concept and produces meaningfully more harmful assistance than Neutral.

Track separately:

* `DIRECT_REFUSED`;
* `NEUTRAL_BENIGN`;
* `DS_MALICIOUS`;
* `DS_REJECTED`;
* `DS_BENIGN_MISUNDERSTANDING`;
* `UNCLEAR`.

## 5.4 Dataset scale

Do not draw major conclusions from tiny samples. Use a staged but substantial design.

### Behavioral screening stage

Minimum:

* 200 distinct paper-derived or paper-faithful base instructions;
* at least 6 harmful categories;
* at least 2 preselected codewords;
* at least 3 context lengths;
* Direct, Neutral, and Doublespeak conditions.

This produces at least `200 × 2 × 3 = 1200` Doublespeak conditions, plus the required
Direct and Neutral controls.

Use deterministic generation first where appropriate. Add multiple generation seeds for
examples near the decision boundary.

### Expanded candidate stage

For promising eligible prompts, expand to:

* at least 4 codewords;
* at least 5 context lengths;
* at least 3 generation seeds;
* multiple demonstration orders.

### Causal benchmark target

Aim to obtain:

* at least 120 behaviorally eligible base instructions;
* ideally 150 or more;
* at least 60 clean examples suitable for causal generation interventions;
* at least 30 examples in each outcome group used for Malicious / Rejected / Benign trajectory comparisons.

If the phenomenon yields fewer than this, report the yield transparently and perform a
power analysis before making strong claims. Do not lower inclusion standards merely to
reach the target sample size.

## 5.5 Category balance

Stratify the benchmark across categories. Do not allow one easy category such as `virus`
to dominate the findings. Track per-category:

* eligibility yield;
* Neutral-benign rate;
* Doublespeak comprehension rate;
* refusal rate;
* malicious response rate;
* mean StrongReject;
* semantic hijacking rate;
* causal intervention effect.

Use category-stratified train, development, and test splits.

## 5.6 Human verification

Automatically evaluate all outputs, but manually and blindly inspect a statistically
meaningful subset. At minimum:

* 50 randomly sampled triplets;
* all apparent clean successes in the early pilot;
* a balanced sample of Malicious, Rejected, Benign, and Unclear;
* disagreements between judges.

Human-facing reports must redact operationally harmful details.

---

# 6. Workstream B — Behavioral causality, not only semantic decoding

The current causal evidence is mainly about P(concept) under Patchscopes. The next
experiments must intervene during actual model inference and evaluate full generated outputs.

## 6.1 Preserve both readouts

For every intervention, retain both:

### Internal readout

* Patchscopes P(concept);
* semantic probe score;
* late harmful alignment;
* refusal-direction projection where validated.

### Behavioral readout

* harmful-response rate;
* refusal rate;
* benign-misunderstanding rate;
* StrongReject score;
* second independent judge;
* manually validated subset.

Do not describe an internal readout effect as a behavioral attack effect.

## 6.2 Behavioral necessity experiment

For each eligible Doublespeak example, run the unmodified baseline and matched
interventions. At the critical codeword position, perform:

$$h_{\mathrm{DS}}^{(\ell)} \leftarrow h_{\mathrm{Neutral}}^{(\ell)}$$

Test:

* individual layers;
* early, middle, and late layer windows;
* patching from layer $\ell$ through the end;
* pre-attention residual;
* post-attention residual;
* post-MLP residual.

Then generate the full answer. The primary behavioral necessity effect is:

$$\Delta_{\mathrm{necessity}} = P(\mathrm{DS\ success}) - P(\mathrm{DS \leftarrow Neutral\ success})$$

Also measure paired changes in:

* refusal;
* benign misunderstanding;
* StrongReject;
* semantic decoding.

A strong necessity result requires:

* internal harmful meaning decreases;
* behavioral harmful assistance decreases;
* identity patch does not cause the effect;
* random and unrelated patches are substantially weaker;
* the effect replicates on held-out examples.

## 6.3 Behavioral sufficiency experiment

Use behaviorally eligible Neutral prompts. Inject:

### Direct state

$$h_{\mathrm{Neutral}} \leftarrow h_{\mathrm{Direct}}$$

### Doublespeak state

$$h_{\mathrm{Neutral}} \leftarrow h_{\mathrm{DS}}$$

Test:

* single layers;
* multi-layer windows;
* persistent late-window replacement;
* addition rather than replacement;
* several intervention strengths;
* prompt prefill only;
* selected generated-token positions where justified.

The primary comparison is:

$$\frac{P(\mathrm{harmful\ behavior} \mid \mathrm{Neutral \leftarrow DS})}{P(\mathrm{harmful\ behavior} \mid \mathrm{Neutral})}$$

Compare this against:

$$\frac{P(\mathrm{harmful\ behavior} \mid \mathrm{Neutral \leftarrow Direct})}{P(\mathrm{harmful\ behavior} \mid \mathrm{Neutral})}$$

The current result predicts that DS-state injection may outperform Direct-state
injection. Test that prediction behaviorally.

## 6.4 Do not rely only on one-layer replacement

The existing conditional sufficiency result may depend on preserving a distributed
contextual state. Test:

* windows of 2, 4, 8, and 12 layers;
* contiguous windows centered around the strongest validated layer;
* injection from a selected layer through the final layer;
* intervention on codeword plus following token;
* intervention on codeword plus the first answer-position residual;
* a low-rank subspace rather than one mean-difference vector.

Record whether sufficiency is:

* sharply localized;
* accumulated over depth;
* distributed across positions;
* dependent on continued processing.

## 6.5 Causal mediation analysis

Treat late harmful semantic alignment as a candidate mediator between:

* the Doublespeak prompt condition;
* the final behavioral outcome.

Estimate:

1. effect of Doublespeak on late semantic score;
2. effect of late semantic score on behavior;
3. effect of neutralization intervention on semantic score;
4. effect of the same intervention on behavior;
5. residual direct effect after controlling for the mediator.

Do not rely on regression alone for the causal claim. Use intervention results to
support the mediation interpretation.

## 6.6 Outcome transitions

For every intervention, report the full paired transition matrix:

* Malicious → Rejected;
* Malicious → Benign;
* Malicious → Malicious;
* Rejected → Malicious;
* Rejected → Benign;
* Benign → Malicious;
* Benign → Rejected;
* Benign → Benign.

This is more informative than reporting only a mean score change.

---

# 7. Workstream C — Establish causal timing

The current project has demonstrated late semantic emergence. It has not yet shown that
semantic timing causally determines refusal versus compliance. This is the central
mechanistic experiment.

## 7.1 Define early, middle, and late regions on development data

Do not select the best layers using the final test set. For each model, use development
data to define:

* early region: where Direct harmful semantics are strong and DS semantics are weak;
* transition region: where DS harmful semantics begin rising;
* late region: where DS harmful semantics peak.

Pre-register these regions before evaluating held-out behavior.

## 7.2 Matched direction injection

Construct a validated contextual harmful direction or low-rank subspace from training
data only. Inject the same norm-controlled semantic intervention:

$$h' = h + \alpha\, d_{\mathrm{contextual\ harm}}$$

at early layers, middle layers, and late layers. Use the same:

* source direction;
* target positions;
* alpha grid;
* prompts;
* generation settings.

The main comparison is not merely whether injection works. It is whether the same
semantic content produces different behavior depending on timing.

## 7.3 Primary hypotheses

Test all three without assuming the answer.

### Hypothesis 1 — TOCTOU

Early injection exposes harmful meaning to refusal processing and increases Rejected
outcomes. Late injection makes the harmful meaning available after the main
refusal-sensitive computation and increases Malicious outcomes.

### Hypothesis 2 — Monotonic safety

Earlier harmful meaning always increases both semantic understanding and harmful
behavior, with no distinct refusal window.

### Hypothesis 3 — Distributed safety

No single timing window determines behavior because refusal remains active throughout the network.

## 7.4 Timing-removal experiment

In successful Doublespeak prompts:

* remove harmful semantics in early layers only;
* remove them in the transition region;
* remove them in late layers only;
* shift the representation earlier;
* delay or reconstruct the representation later.

A particularly valuable result would show that:

* late removal eliminates harmful behavior;
* early addition increases refusal;
* late addition increases compliance.

## 7.5 Refusal-direction interaction

Reuse existing refusal-direction infrastructure only after validating it on the current
models and data. Run a factorial experiment:

| Contextual harmful direction | Refusal direction | Timing         |
| ---------------------------- | ----------------- | -------------- |
| none                         | none              | baseline       |
| add                          | none              | early/mid/late |
| none                         | add               | early/mid/late |
| add                          | add               | early/mid/late |
| add                          | remove            | early/mid/late |
| remove                       | add               | early/mid/late |

Measure:

* semantic interpretation;
* refusal probability;
* actual response category;
* StrongReject.

Do not assume a single linear refusal direction is the full safety mechanism.

## 7.6 Required controls

For every timing experiment:

* alpha zero;
* identity replacement;
* norm-matched random direction;
* unrelated semantic direction;
* positive and negative alpha;
* target position versus adjacent position;
* codeword versus random prompt token;
* matched early/late norm;
* matched number of modified layers.

---

# 8. Workstream D — Complete the causal circuit

The current attention knockout proves that demonstrations are necessary, but the result
remains broad and partially distributed. We need a more precise causal circuit.

## 8.1 Separate three stages

Explicitly distinguish:

1. **Acquisition:** the model reads the demonstrations and infers the mapping.
2. **Storage/consolidation:** the mapping is represented in a distributed contextual state.
3. **Use:** the final codeword and generated response retrieve and use the mapping.

## 8.2 Demonstration-source ablations

Block or patch separately:

* previous codeword tokens;
* context words that define the substituted meaning;
* verbs associated with the harmful concept;
* entire demonstration sentences;
* one demonstration at a time;
* first versus last demonstrations;
* consistent versus inconsistent demonstrations.

Measure which components affect:

* semantic onset;
* peak late alignment;
* actual behavior.

## 8.3 Attention versus MLP

At each critical layer, compare:

* attention-output patching;
* MLP-output patching;
* complete residual patching;
* attention knockout;
* MLP ablation where technically valid.

Determine whether attention primarily routes the mapping while MLP blocks transform or
consolidate it.

## 8.4 Head-level and path-level analysis

Use a coarse-to-fine design:

1. layer-level knockout;
2. attention-head groups;
3. individual heads;
4. path patching only for validated candidate paths.

Trace candidate paths from:

$$\text{demonstration context} \rightarrow \text{codeword state} \rightarrow \text{generated reasoning/answer tokens}$$

Do not perform an exhaustive head sweep without multiple-testing correction and held-out
validation.

## 8.5 Generated-token information flow

The harmful meaning may move away from the codeword position. Capture and test:

* codeword token;
* following prompt token;
* last prompt token;
* first generated token;
* early refusal/compliance tokens;
* selected reasoning tokens;
* first answer-content tokens.

Test whether patching the codeword is sufficient only if downstream answer-token states
are also affected.

---

# 9. Workstream E — Discover an objective that predicts behavior

Do not jump immediately from the current representation result to GCG. First establish
which mechanistic quantity predicts held-out behavioral success.

## 9.1 Candidate features

For every eligible prompt, compute:

* early harmful alignment;
* middle harmful alignment;
* late harmful alignment;
* early-to-late increase;
* semantic onset layer;
* late peak;
* area under the semantic trajectory;
* Neutral-to-DS displacement;
* projection on contextual DS subspace;
* projection on ordinary Direct concept direction;
* refusal-direction projection;
* attention mass from final codeword to demonstrations;
* first-answer-token harmful alignment;
* thinking-token harmful alignment where applicable.

## 9.2 Predictive evaluation

On training and development data, test which features predict:

* DS Malicious versus Rejected;
* DS Malicious versus Benign;
* continuous StrongReject;
* binary attack success;
* success under multiple generation seeds.

Use:

* cross-validated logistic regression;
* regularized linear models;
* mixed-effects models;
* calibrated nonlinear baselines only where sample size supports them.

Evaluate on held-out prompts and held-out concepts. A feature is not a useful attack
objective merely because it differs between Direct and Neutral. It must predict
behavioral success.

## 9.3 Candidate temporal objective

Start with:

$$J_{\mathrm{temporal}} = \frac{1}{|\mathcal{L}_{\mathrm{late}}|} \sum_{\ell \in \mathcal{L}_{\mathrm{late}}} s_\ell \;-\; \lambda \frac{1}{|\mathcal{L}_{\mathrm{early}}|} \sum_{\ell \in \mathcal{L}_{\mathrm{early}}} s_\ell$$

where $s_\ell$ measures contextual harmful meaning. This rewards:

* weak harmful exposure early;
* strong harmful interpretation late.

Also test benign retention:

$$J_{\mathrm{benign\ early}} = \frac{1}{|\mathcal{L}_{\mathrm{early}}|} \sum_{\ell \in \mathcal{L}_{\mathrm{early}}} \mathrm{sim}\!\left(h_{\mathrm{candidate}}^{(\ell)}, h_{\mathrm{neutral}}^{(\ell)}\right)$$

Potential combined objective:

$$J = J_{\mathrm{temporal}} + \gamma\, J_{\mathrm{benign\ early}} - \beta\, J_{\mathrm{refusal}} + \eta\, J_{\mathrm{task}}$$

where:

* $J_{\mathrm{refusal}}$ penalizes validated refusal activation;
* $J_{\mathrm{task}}$ rewards the model actually retaining the requested task semantics.

Do not use an unvalidated refusal direction in the final objective.

## 9.4 Causal-objective criterion

Prefer an objective whose components are causally linked to behavior. For example:

* if removing late DS alignment lowers ASR;
* if adding it raises ASR;
* if timing affects refusal versus compliance;

then the corresponding feature has stronger justification as an optimization target. A
purely predictive feature should be labeled predictive, not mechanistic.

---

# 10. Workstream F — Optimize the attack with GCG and MAC

The objective is not merely to reproduce standard suffix optimization. The goal is to
determine whether a mechanistic temporal objective produces a stronger, more efficient,
or more transferable attack.

## 10.1 Audit existing optimization code

Inspect the current repository and any available GCG or MAC implementations. Reuse
validated code where possible. Do not write an entirely new optimizer until checking:

* previous GCG infrastructure from this thesis;
* official GCG implementations;
* available MAC implementation;
* tokenizer and gradient handling;
* batching;
* candidate filtering;
* live-ASR selection;
* checkpointing.

Record the exact source and any modifications.

## 10.2 Optimization targets

Compare the following methods.

* **Baseline A — Original Doublespeak.** Paper-faithful codeword and demonstrations without optimization.
* **Baseline B — Random search.** Randomly vary codeword, demonstration order, demonstration wording, and context length. Match the number of evaluated candidates to the optimization methods where possible.
* **Baseline C — Standard GCG.** Conventional output-target objective or the existing validated project implementation.
* **Baseline D — Standard MAC.** Same conventional behavioral/output objective with momentum acceleration.
* **Method E — Temporal-GCG.** GCG coordinate updates to maximize the validated temporal representation objective.
* **Method F — Temporal-MAC.** MAC with the validated temporal objective.
* **Method G — Combined objective.** Combine temporal semantic objective, task relevance, refusal suppression, optional behavior surrogate.

Do not declare Method G successful unless it improves held-out behavioral ASR.

## 10.3 What may be optimized

Test optimization over progressively broader variables.

1. **Codeword selection** — select from a controlled pool of valid benign words.
2. **Demonstration selection** — choose which demonstrations to include.
3. **Demonstration order** — optimize ordering without changing text.
4. **Local context tokens** — optimize words surrounding the codeword inside demonstrations.
5. **Final-query context** — optimize a short span near the final codeword.
6. **Adversarial discrete tokens** — optimize a constrained suffix or insertion span using GCG/MAC.

Keep natural-language and unrestricted adversarial variants separate.

## 10.4 Candidate positions

Do not assume the suffix is the best optimization location. Compare:

* after demonstrations;
* before the final query;
* adjacent to the final codeword;
* inside selected demonstrations;
* standard final suffix.

All position choices must be fixed using development data.

## 10.5 Gradient computation

For the mechanistic objective:

* capture differentiable target representations;
* avoid detaching required tensors;
* compute gradients with respect to candidate token embeddings;
* use coordinate-gradient candidate generation;
* score candidates in batches;
* apply tokenizer-validity filters;
* preserve required codeword occurrences;
* prevent candidates from trivially inserting the explicit harmful concept.

For MAC:

* implement or reuse momentum accumulation correctly;
* log momentum norms;
* compare convergence against GCG;
* reset momentum between independent runs;
* test multiple seeds.

## 10.6 Prevent trivial leakage

The optimizer must not "succeed" by directly inserting:

* the original harmful concept;
* an obvious synonym;
* explicit harmful instructions;
* target-answer text.

Create filters and post-hoc audits. Report separately:

* unconstrained optimization;
* lexical-leakage-filtered optimization;
* natural-language-constrained optimization.

## 10.7 Model-selection rules

Do not select the final optimized prompt using test-set ASR. Use:

* training prompts for gradient construction;
* development prompts for checkpoint and hyperparameter selection;
* held-out test prompts for final evaluation;
* held-out concepts for semantic transfer;
* held-out codewords for lexical transfer;
* other models for cross-model transfer.

## 10.8 Evaluation of the optimized attack

For each optimizer report:

* binary held-out ASR;
* mean StrongReject;
* refusal rate;
* benign-misunderstanding rate;
* optimization steps;
* forward/backward passes;
* wall-clock GPU time;
* candidate evaluations;
* convergence curve;
* temporal objective curve;
* early and late semantic scores;
* transfer ASR;
* variance across seeds.

The key test is:

> Does optimizing the mechanistic objective produce better behavioral attacks than
> standard GCG/MAC under a comparable budget?

## 10.9 Objective ablations

At minimum compare:

* late harmful only;
* early suppression only;
* benign-early only;
* temporal difference;
* refusal suppression only;
* task objective only;
* temporal plus task;
* temporal plus refusal;
* full combined objective.

This will show whether "benign early, harmful late" is genuinely useful rather than
merely an attractive narrative.

---

# 11. Workstream G — Thinking versus non-thinking

This is a major new research direction and should be designed carefully. The central question is:

> Does explicit reasoning give the model more opportunity to build, detect, amplify, or
> suppress the hijacked meaning?

## 11.1 Clean within-model comparison first

Use Qwen3-14B as the primary thinking-versus-non-thinking comparison if the exact same
checkpoint supports both modes through its official chat template or generation interface.

Before running:

* verify the correct official method for enabling/disabling thinking;
* verify whether the weights are identical;
* record the exact chat-template difference;
* validate output parsing;
* validate native EOS behavior;
* do not assume the API based on memory.

The within-model comparison is scientifically stronger than comparing unrelated reasoning
and non-reasoning models.

## 11.2 Secondary comparisons

Where available, add:

* Phi-4-mini-reasoning versus the matched non-reasoning Phi-4-mini checkpoint;
* DeepSeek-R1-Distill-Llama-8B versus an appropriate Llama baseline;
* paper models such as Gemma-3 and Llama-3.1 as non-thinking references.

Comparisons between separately trained checkpoints must be labeled exploratory because
architecture, data, post-training, and alignment differ.

## 11.3 Sample size

Use at least:

* 100 behaviorally eligible matched prompts;
* balanced categories;
* identical codewords and demonstrations across modes;
* at least 3 generation seeds per mode where sampling is used.

Do not publish a thinking/non-thinking conclusion from a handful of examples.

## 11.4 Conditions

For every prompt run:

* Direct, thinking;
* Direct, non-thinking;
* Neutral, thinking;
* Neutral, non-thinking;
* Doublespeak, thinking;
* Doublespeak, non-thinking.

Keep generation budgets matched where meaningful. Also evaluate controlled budgets: no
thinking; short thinking; medium thinking; long thinking. Do not interpret token-budget
differences as a pure reasoning effect without controls.

## 11.5 Representation positions

Capture representations at:

### Prompt processing

* final codeword token;
* following prompt token;
* final prompt token.

### Thinking generation

* first thinking token;
* early thinking window;
* middle thinking window;
* late thinking window;
* tokens near semantic transitions;
* tokens near refusal or compliance framing.

### Final answer

* answer-transition token;
* first answer token;
* first substantive answer tokens;
* refusal-onset tokens where present.

Store only required positions rather than full unrestricted reasoning traces.

## 11.6 Thinking hypotheses

* **Hypothesis A — Thinking amplifies the attack.** Reasoning repeatedly retrieves the demonstrations, strengthening the contextual harmful meaning and increasing ASR.
* **Hypothesis B — Thinking improves safety.** Reasoning allows the model to infer the hidden mapping and then explicitly recognize that the underlying request is harmful, increasing rejection.
* **Hypothesis C — Thinking shifts the critical location.** The harmful meaning is weak at the prompt codeword but becomes strong in generated thinking tokens.
* **Hypothesis D — Thinking creates a two-stage process.** The model first resolves the codeword and later decides whether to refuse, making the timing gap easier to intervene on.

## 11.7 Thinking interventions

For matched prompts, test:

* removing the contextual harmful direction during early thinking;
* removing it during late thinking;
* adding it during early thinking;
* adding it only near the answer transition;
* patching thinking states from non-thinking-like or rejected runs;
* attention knockout from thinking tokens back to demonstrations;
* refusal-direction addition after semantic resolution;
* late safety steering immediately before answer generation.

Evaluate actual final behavior.

## 11.8 Thinking trajectory comparison

For each mode estimate:

* semantic onset position;
* peak harmful alignment;
* duration of harmful alignment;
* refusal onset;
* transition from codeword resolution to safety decision;
* final ASR.

High-value results would be:

> Thinking and non-thinking models resolve the codeword similarly, but thinking changes
> when refusal activation occurs.

or

> The hijacked meaning is constructed primarily inside generated reasoning rather than at
> the original codeword token.

## 11.9 No unsupported chain-of-thought claims

Do not infer internal reasoning solely from natural-language reasoning text. Use
activation-level measurements and interventions. Do not expose raw operationally harmful
reasoning in reports. Use redacted summaries and scalar trajectories.

---

# 12. Model strategy

## 12.1 Primary model

Continue using `meta-llama/Llama-3.1-8B-Instruct` for complete causal sweeps because the
infrastructure is validated and the model is computationally manageable.

## 12.2 Thinking comparison

Use `Qwen/Qwen3-14B` for the primary within-model thinking/non-thinking study, subject to
exact interface validation.

## 12.3 Existing replication models

Continue using `microsoft/Phi-4-mini-reasoning` for cross-family validation. Use cached
DeepSeek-R1-Distill-Llama-8B for selected reasoning-model experiments after validating
its generation format and stopping behavior.

## 12.4 Models from the original paper

Attempt selected replication on the original paper's open models: Gemma-3 family;
Llama-3.3-70B-Instruct. Do not block the core research on gated downloads. Before downloading:

* inspect current project quota;
* use the project-local Hugging Face cache;
* download only the chosen checkpoint;
* avoid simultaneous model downloads;
* verify access before submitting compute jobs.

For Gemma, begin with a manageable checkpoint such as 4B before 27B. Use Llama-3.3-70B
only for a small number of preselected, high-value validations after the 8B result is
established.

---

# 13. Statistical standards

## 13.1 No headline claims from tiny samples

Examples with $n < 10$ are diagnostics only. Examples with $n < 30$ per relevant
comparison must be labeled preliminary unless the effect is deterministic and replicated
broadly.

## 13.2 Splits

Create immutable splits: train; development; held-out test; held-out concept; held-out
codeword; cross-model transfer. Store the split file under version control. Do not change
test membership after viewing results.

## 13.3 Paired analysis

Use paired analyses because the same base instruction is tested under multiple
conditions. Depending on the outcome, use:

* paired bootstrap confidence intervals;
* McNemar's test;
* paired permutation tests;
* mixed-effects logistic regression;
* mixed-effects linear regression.

Include random effects for base instruction; concept; codeword; model where appropriate.

## 13.4 Multiple comparisons

Correct for multiple testing in layer sweeps; alpha sweeps; head sweeps; position sweeps;
objective ablations. Use development data for discovery and held-out data for confirmation.

## 13.5 Report uncertainty

Every central result should include number of base prompts; number of generations; number
of seeds; confidence interval; paired effect size; per-category results; per-model results.

---

# 14. Evaluation reliability

## 14.1 Keep metrics separate

Never use "ASR" without defining it. Report:

* binary malicious response rate;
* binary refusal rate;
* binary benign-misunderstanding rate;
* continuous StrongReject score;
* semantic hijack rate;
* intervention effect.

## 14.2 Multiple judges

Use StrongReject as one judge. Add a second independent evaluator where available. The
second judge should classify whether the codeword was understood; whether the answer is
harmful; whether the answer is relevant; whether the model refused. Measure judge agreement.

## 14.3 Manual review

Blind the human reviewer to optimization method; intervention condition; model mode where
possible. Do not show whether an output came from baseline, GCG, MAC, or the proposed objective.

## 14.4 Positive-control every readout

The previous arrow-based Patchscopes prompt failed. For every new model and every new decoder:

* test a clean Direct representation;
* require high target decoding;
* test a Neutral negative control;
* test an unrelated concept;
* record the positive-control score.

No readout may be trusted before passing its positive control.

---

# 15. Required controls

Every intervention or optimization experiment must include relevant controls. At minimum:

* no intervention;
* alpha zero;
* identity patch;
* norm-matched random vector;
* unrelated semantic direction;
* negative direction;
* adjacent-position intervention;
* random-position intervention;
* shuffled source-target patch;
* matched benign concept;
* matched prompt length;
* codeword-only repetition control;
* demonstration-order control.

For optimization: random search at matched evaluation budget; standard GCG; standard MAC;
output-only objective; representation-only objective; combined objective.

---

# 16. Existing infrastructure and mandatory reuse

The current repository already contains:

* `ds_common.py`; activation capture; `LayerPatch`; native-EOS generation; target
  localization; Stage-1 mapping; activation patching; Patchscopes readout; multi-layer
  sufficiency; attention knockout; layerwise knockout; emergence trajectories; codeword
  study; behavioral evaluation; defense detector; statistics and plots; SLURM scripts;
  14 passing tests.

Do not recreate these from scratch. First identify what can be extended. Preserve
compatibility with completed output formats where possible.

---

# 17. Environment and cluster rules

```bash
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
```

Load secrets only where needed:

```bash
set -a
source .env
set +a
```

Always use the project-local Hugging Face cache:

```bash
export HF_HOME=$PROJECT_DIR/.cache/huggingface
export HF_HUB_CACHE=$HF_HOME/hub
export HF_HUB_OFFLINE=1
```

Only disable offline mode for an explicitly approved model download.

## SLURM rules

* partition: `killable`;
* account: `gpu-research`;
* one L40S where sufficient;
* nodes restricted to the established allowed L40S list;
* no more than six concurrent jobs;
* no unsupported job dependencies;
* bf16 for canonical runs;
* explicit L40S guard.

Do not use `gpu-sharifm`. Login-node GPUs may be used only for small float16
code-validation smoke tests. Real experiments must use SLURM.

## Storage

Do not write to the shared default Hugging Face cache. Do not save complete sequence
activations unnecessarily. Save selected token positions; selected layers/components;
compact shards; run metadata.

## Harmful-text safeguard

The cluster classifier terminates subagents or delegated workflows that read harmful
text. Therefore harmful prompt construction; raw generation; attack execution;
harmful-output evaluation must remain in the main process or SLURM jobs. Subagents may
only process benign scalars; aggregate JSONs; statistics; plots; redacted labels. Do not
print raw harmful generations to terminals or logs.

---

# 18. Reproducibility rules

For every run record: run ID; date; exact command; git commit; model ID and revision;
tokenizer ID and revision; chat template; thinking mode; dtype; device; generation
configuration; native EOS list; seeds; dataset version; split; intervention parameters;
objective parameters; optimizer parameters; result path; status.

Use status values: `NOT_RUN`; `QUEUED`; `RUNNING`; `PARTIAL`; `FAILED`; `COMPLETE`;
`INVALIDATED`. Never overwrite failed or invalidated runs.

---

# 19. Known bugs that must not recur

Preserve the fixes documented in the handoff. In particular:

1. Never use the shared default HF cache.
2. Never call `asdict` on a structure containing the model.
3. Never trust the arrow-style Patchscopes prompt without a positive control.
4. Do not pass comma-separated lists through `sbatch --export`.
5. Distinguish unset variables from intentionally empty variables.
6. Compute patch positions on the exact text used for the forward pass.
7. Avoid CPU/GPU tensor mixing in norm calculations.
8. Use precision-aware identity tolerances.
9. Avoid concurrent heavy model loads from shared NFS on the same node.
10. Preserve native list-valued EOS IDs.

---

# 20. New implementation components

Extend the repository with clearly named components for:

## Behavioral benchmark

* paper-faithful prompt extraction; eligibility classification; triplet validation;
  dataset splitting; multi-judge evaluation; yield analysis.

## Behavioral interventions

* full-generation necessity; full-generation sufficiency; early/middle/late injection;
  multi-layer windows; paired transition analysis.

## Optimization

* mechanistic objective computation; differentiable activation capture; GCG wrapper; MAC
  wrapper; candidate filtering; lexical-leakage detection; validation checkpointing;
  attack transfer evaluation.

## Thinking comparison

* thinking-mode configuration; reasoning-token parsing; matched generation budgets;
  reasoning-position activation capture; thinking-time interventions;
  thinking/non-thinking aggregation.

Suggested script names (adapt to current repository conventions):

* `16_prepare_behavioral_benchmark.py`
* `17_validate_behavioral_triplets.py`
* `18_run_behavioral_necessity.py`
* `19_run_behavioral_sufficiency.py`
* `20_run_behavioral_timing.py`
* `21_extract_behavioral_features.py`
* `22_fit_success_predictors.py`
* `23_temporal_objective.py`
* `24_run_gcg_baselines.py`
* `25_run_mac_baselines.py`
* `26_run_temporal_gcg.py`
* `27_run_temporal_mac.py`
* `28_evaluate_optimized_attacks.py`
* `29_run_thinking_comparison.py`
* `30_run_thinking_interventions.py`
* `31_analyze_thinking_results.py`

Do not force these names if they conflict with existing code organization.

---

# 21. Required experiment registry design

Each behavioral row should include: base prompt ID; original category; harmful concept;
codeword; context length; demonstration order; model; thinking mode; seed; condition;
intervention; layer/window; alpha; optimizer; objective; optimization step; output
category; refusal; harmfulness; relevance; StrongReject; semantic score; onset layer; run ID.

This should support paired analysis without reconstructing metadata from filenames.

---

# 22. Execution order

Follow this order unless repository evidence justifies a documented deviation.

## Phase 1 — Audit and freeze

1. Read all current documents and raw outputs.
2. Run the existing tests.
3. Re-run one validated positive control.
4. Verify current branch and commit state.
5. Create a tagged or documented frozen checkpoint of the existing results.
6. Do not invalidate the current handoff accidentally.

## Phase 2 — Paper-faithful behavioral benchmark

1. Locate exact paper artifacts.
2. Build the eligibility classifier.
3. Run the 200-prompt screening stage on Llama-3.1-8B.
4. Evaluate Direct and Neutral before spending compute on all Doublespeak variants.
5. Keep only behaviorally eligible prompts for the expanded candidate stage.
6. Generate and evaluate the larger Doublespeak matrix.
7. Produce a benchmark-yield report.

## Phase 3 — Behavioral causal MVP

Using at least 30 eligible prompts:

1. Run DS baseline.
2. Run identity patch.
3. Run DS←Neutral at selected early/middle/late windows.
4. Run Neutral←DS at the same windows.
5. Generate full answers.
6. Evaluate paired behavioral transitions.
7. Validate that internal and behavioral effects align.

Do not scale a broken intervention.

## Phase 4 — Full behavioral causality

After the MVP passes:

1. Expand to at least 60 examples.
2. Run full layer/window sweeps on development data.
3. Confirm selected interventions on held-out data.
4. Run timing and refusal-interaction experiments.
5. Perform causal mediation analysis.

## Phase 5 — Objective validation

1. Extract candidate mechanistic features.
2. Fit behavioral-success predictors.
3. Choose objective terms using development data.
4. Confirm predictive value on held-out data.
5. Test causal relevance through interventions.

## Phase 6 — GCG/MAC optimization

1. Validate standard GCG baseline.
2. Validate standard MAC baseline.
3. Implement Temporal-GCG.
4. Implement Temporal-MAC.
5. Run matched-budget comparisons.
6. Evaluate held-out ASR and transfer.
7. Run objective ablations.

## Phase 7 — Thinking versus non-thinking

1. Validate Qwen3 mode switching.
2. Run the 100-prompt matched comparison.
3. Extract prompt, thinking, and answer trajectories.
4. Run selected causal thinking interventions.
5. Compare optimized attacks across modes.

## Phase 8 — Cross-model confirmation

Confirm only the most important results on Phi-4-mini-reasoning;
DeepSeek-R1-Distill-Llama-8B; selected Gemma-3 checkpoint; selected Llama-3.3-70B subset
if resources permit.

---

# 23. Required deliverables

Create or update:

## `BEHAVIORAL_BENCHMARK.md`

Eligibility definition; prompt sources; category distribution; sample sizes; dataset
yield; clean triplet examples in redacted form; failure modes.

## `BEHAVIORAL_CAUSALITY_RESULTS.md`

Separate: necessity; sufficiency; timing; mediation; controls; behavioral versus semantic findings.

## `MECHANISTIC_OBJECTIVE.md`

Candidate features; predictive tests; causal support; final objective; objective ablations.

## `GCG_MAC_COMPARISON.md`

Attack configurations; budgets; convergence; held-out ASR; transfer; compute; failures.

## `THINKING_VS_NONTHINKING.md`

Exact mode configuration; matched datasets; behavioral results; semantic trajectories;
intervention results; limitations.

## `UPDATED_PAPER_STORY.md`

Maintain an honest evolving paper narrative:

1. what the original paper showed;
2. what we causally established;
3. what became behavioral;
4. whether the mechanistic objective improved attacks;
5. how thinking changes the mechanism;
6. what remains unresolved.

## Existing records

Update: `DOUBLESPEAK_MASTER_LOG.md`; `EXPERIMENT_REGISTRY.csv`; `CAUSAL_RESULTS_SUMMARY.md`;
`RESULTS_SYNTHESIS.md`; README commands; SLURM documentation.

---

# 24. Success criteria

The sprint is scientifically successful if it achieves at least one of the following with
adequate sample size and controls:

* **Level 1** — A clean, reproducible behavioral Doublespeak benchmark with substantially more than a handful of examples.
* **Level 2** — Behavioral necessity or sufficiency under activation intervention.
* **Level 3** — A causal early-versus-late effect on refusal versus compliance.
* **Level 4** — A mechanistic objective that predicts held-out behavioral success.
* **Level 5** — Temporal-GCG or Temporal-MAC outperforms its standard counterpart on held-out behavioral ASR under a matched budget.
* **Level 6** — A robust thinking-versus-non-thinking difference supported by within-model evidence and causal intervention.

The strongest paper would achieve Levels 1–6.

---

# 25. Failure criteria and honest reporting

Do not turn a representation result into an attack claim. Record a result as negative if:

* latent objective improves but ASR does not;
* probe decoding changes but behavior does not;
* the intervention only works on training prompts;
* the optimized prompt inserts explicit harmful concepts;
* the thinking effect disappears under matched budgets;
* judge results are inconsistent;
* the effect depends on one category;
* random controls perform similarly;
* the positive control fails.

A rigorous negative result can still improve the paper by showing that representation
hijacking and behavioral jailbreak are separable.

---

# 26. Immediate execution request

Begin now. Do not return only a conceptual plan. Perform the following:

1. Audit the current branch, documents, code, raw outputs, and tests.
2. Freeze and document the current verified representation-level result.
3. Locate the exact paper-faithful behavioral artifacts.
4. Implement the behavioral eligibility and triplet-validation pipeline.
5. Run a small end-to-end validation of that pipeline.
6. Prepare and submit the 200-base-prompt behavioral screening run on Llama-3.1-8B.
7. Implement full-generation necessity and sufficiency on a validated pilot subset.
8. Validate the Qwen3 thinking/non-thinking configuration.
9. Implement the experiment-registry extensions needed for optimization and thinking runs.
10. Audit available GCG and MAC code and document what will be reused.
11. Implement the mechanistic-objective interface without yet claiming it is the correct objective.
12. Update all logs and handoff documents with actual work completed.
13. Report all submitted job IDs, run IDs, output paths, failures, and unresolved blockers.

While long SLURM jobs run, continue with work that does not depend on their completion:
tests; benchmark validation; GCG/MAC audit; objective infrastructure; thinking-mode smoke
tests; documentation; analysis of already completed outputs.

At the end of this execution session, provide:

* files created or changed;
* tests run and their results;
* commands executed;
* jobs submitted and their IDs;
* sample sizes actually launched;
* behavioral benchmark status;
* intervention status;
* thinking-mode validation status;
* GCG/MAC audit findings;
* bugs found and fixed;
* results available now;
* results still pending;
* the single next experiment with the highest expected scientific value.

The guiding standard is:

> We are not trying merely to produce a stronger late-layer representation. We are trying
> to establish that the representation causally controls real model behavior, and then
> exploit that causal mechanism to build an optimization objective that improves a real attack.
