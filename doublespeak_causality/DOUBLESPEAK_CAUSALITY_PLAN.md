# Doublespeak Causality — Research Plan

> Pivot toward the paper **“In-Context Representation Hijacking”** — arXiv:2512.03771
> Paper: https://arxiv.org/pdf/2512.03771
> Official code: https://github.com/1tux/doublespeak
>
> **Directive:** Read the paper, appendices, official codebase, and all relevant existing files in the research repository before making substantial changes. Do not merely write a plan — audit the existing environment, implement the research infrastructure, run small validation experiments, and prepare the larger SLURM experiments where appropriate.

---

## 1. Research context

My name is Omer Yosef. I am an M.Sc. student at Tel Aviv University conducting thesis research under Dr. Mahmood Sharif.

My broader thesis concerns:

* adversarial attacks against aligned language models;
* jailbreaks and refusal mechanisms;
* mechanistic interpretability of attack success and failure;
* causal interventions in model activations;
* converting mechanistic findings into attack objectives or defenses.

Until now, much of the project focused on Chain-of-Thought hijacking, GCG-style attacks, refusal directions, early-thinking representations, and attempts to optimize attacks using mechanistic signals.

After discussing the project with Matan Ben-Tov, we decided to pivot toward the Doublespeak / in-context representation hijacking paper.

The central reason for this pivot is that the paper contains a promising mechanistic observation but leaves substantial low-hanging fruit around causality.

The paper shows that a benign codeword such as `carrot` or `potato`, when repeatedly used in contexts associated with a harmful concept such as `bomb`, develops a representation that becomes increasingly similar to the harmful concept across model layers.

However, the paper mainly provides observational evidence using tools such as:

* logit lens;
* Patchscopes;
* layer-wise representation analysis.

It does not establish strong causal evidence through interventions such as:

* activation patching;
* directional activation addition or removal;
* attention knockout;
* path patching;
* controlled manipulation of when the harmful representation emerges.

Our goal is to move from:
“The representation changes when Doublespeak succeeds”
to:
“We can causally control whether, where, and when the representation changes, and this causally controls whether the model misunderstands, refuses, or complies.”

The intended high-level research story is:
**From observing in-context representation hijacking to causally controlling it.**

## 2. Main research questions

The project should answer the following questions.

### RQ1 — Necessity
Is the harmful semantic representation of the benign codeword necessary for Doublespeak to work?

Operationally:

* Start with a successful Doublespeak prompt.
* Replace or remove the harmful component of the codeword activation.
* Determine whether the model stops interpreting the codeword as the harmful concept.

A successful necessity result would show that removing the representation changes behavior from:

* Malicious → Benign;
* Malicious → Rejected;
* or substantially decreases harmful semantic decoding and attack score.

### RQ2 — Sufficiency
Is inserting the harmful semantic representation into a benign codeword sufficient to make the model interpret it as the harmful concept?

Operationally:

* Start with a neutral prompt containing `carrot`, with no Doublespeak demonstrations.
* Patch or inject the representation associated with `bomb`.
* Determine whether the internal interpretation and output behavior change.

We should distinguish multiple levels of sufficiency:

1. The internal probe or Patchscope decodes the representation as `bomb`.
2. The model semantically interprets `carrot` as the harmful concept.
3. The output behavior changes accordingly.
4. The intervention bypasses refusal in a full attack setting.

Do not collapse these levels into one result.

### RQ3 — Timing
Does the layer at which the harmful meaning appears determine whether the model refuses or complies?

The paper hypothesizes a time-of-check versus time-of-use mechanism:

* refusal-relevant processing may happen relatively early;
* the harmful semantic overwrite may emerge later;
* the model therefore uses the harmful meaning after the relevant safety check has already occurred.

We must directly test this.

Compare the effects of injecting the same harmful semantic direction:

* in early layers;
* in middle layers;
* in late layers.

The key possible result is:

* early injection causes more explicit refusal;
* late injection causes more malicious compliance;
* very late injection may affect decoding but not behavior;
* removing late harmful semantics reduces attack success.

This early-versus-late intervention is one of the highest-priority experiments.

### RQ4 — Information flow
Where does the new meaning of the codeword come from?

Determine whether information is transferred from:

* earlier appearances of the codeword;
* context words surrounding those appearances;
* the full in-context demonstration sentences;
* particular attention heads;
* particular MLP blocks;
* particular paths through the residual stream.

Use attention knockout and, if appropriate, path patching to identify the causal route.

### RQ5 — Attack objective
Can the representation dynamics be converted into a mechanistic optimization objective?

Instead of directly optimizing only for a compliant output, optimize for a temporal representation pattern:

* benign semantics in early layers;
* harmful semantics in late layers.

This may be a more targeted objective for Doublespeak than ordinary output-based GCG.

### RQ6 — Codeword selection
Does choosing a codeword far from the harmful word in the embedding space improve the attack?

Do not assume that maximum static embedding distance is best.

Test whether attack success is better predicted by:

* initial embedding distance;
* token frequency;
* tokenization length;
* lexical category;
* polysemy;
* contextual learnability;
* early-layer benign retention;
* late-layer harmful alignment;
* semantic onset layer.

The best codeword may not be the farthest word. It may be the word that stays benign early while acquiring the harmful meaning strongly enough in later layers.

## 3. Models

Use the open-weight models evaluated in the paper.

### Primary mechanistic model
Begin with the exact Llama 8B instruction-tuned checkpoint used by the paper, expected to be:

* Llama-3.1-8B-Instruct

Verify the exact Hugging Face model ID, revision, tokenizer, and chat template against the official paper repository. Do not guess silently.

This should be the primary model because:

* it is computationally manageable;
* the paper performs its main Patchscopes analysis on the 8B instruction model;
* it supports full white-box activation interventions;
* it allows complete layer and head sweeps.

### Secondary models
After the complete causal pipeline works on 8B, validate selected high-value findings on:

* Llama-3.3-70B-Instruct;
* Gemma-3-270M-IT;
* Gemma-3-1B-IT;
* Gemma-3-4B-IT;
* Gemma-3-27B-IT.

Resolve exact model IDs from the official model cards and the paper repository.

Do not immediately launch full intervention sweeps on 70B or Gemma-3-27B. First establish a reliable effect on the 8B model.

Use the smaller Gemma models initially for scaling and implementation validation. Use the larger models only for selected confirmatory experiments.

### Additional evaluation targets
The paper also evaluates:

* GPT-4o;
* o1 or the exact o1 variant used in the paper;
* Claude-3.5-Sonnet;
* LlamaGuard-3-8B.

These are secondary behavioral or transfer targets.

Do not block the core work on closed-model API access. Use them only if credentials and prior infrastructure already exist.

Closed models cannot be used for white-box activation interventions.

LlamaGuard may later be used to evaluate whether representation hijacking bypasses a dedicated external guardrail.

## 4. Existing environment and repository rules

The current research repository is expected to be under:
`/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood`

The existing Python environment has previously been:
`poc_stage2`

The cluster has previously used SLURM with resources such as:

* account: `gpu-research`;
* partitions including `gpu-sharifm`, `killable`, and `cpu-killable`.

Do not assume these details are still correct. Inspect the existing scripts, environment, available modules, and current SLURM configuration first.

Reuse established working conventions from previous project scripts where sensible.

Before creating new infrastructure:

1. Inspect the repository tree.
2. Read existing README files, experiment logs, research summaries, and SLURM scripts.
3. Identify reusable utilities for:
   * model loading;
   * activation hooks;
   * generation;
   * StrongReject evaluation;
   * dataset handling;
   * SLURM submission;
   * reproducibility and logging.
4. Document which components are reused and which are new.

Create the Doublespeak work in a separate, clearly named module or directory. Do not mix its results with the previous CoT/GCG experiments.

A reasonable namespace would be:
`doublespeak_causality/`

Adapt this to the existing repository structure rather than forcing an incompatible layout.

## 5. General working rules

These rules are mandatory throughout the project.

### 5.1 Inspect before changing
Do not blindly rewrite existing code.
Read relevant files and understand the existing pipeline before editing them.
Prefer extending known-good utilities over reimplementing them.

### 5.2 Preserve previous work
Do not overwrite or delete previous experimental outputs.
Do not silently modify old result files.
New runs must use unique run directories containing:

* timestamp or run ID;
* model identifier;
* git commit hash;
* configuration;
* random seed;
* command;
* environment metadata.

### 5.3 Never fabricate results
Never write placeholder values as if they were experimental results.
Clearly label states as:

* `NOT_RUN`;
* `RUNNING`;
* `FAILED`;
* `PARTIAL`;
* `COMPLETE`.

If a job fails, preserve the failure logs and explain the reason.

### 5.4 Reproducibility
For every run, record:

* exact model ID;
* model revision or commit;
* tokenizer revision;
* chat template;
* dtype;
* device configuration;
* generation configuration;
* random seeds;
* library versions;
* source code commit;
* dataset version;
* intervention parameters;
* prompt IDs;
* token positions;
* evaluation configuration.

Use deterministic inference where possible.
Where sampling is necessary, store the seed and report variance over multiple seeds.

### 5.5 Start small
Do not begin with the full AdvBench dataset or a 70B model.
Use the following progression:

1. one manually inspected safe diagnostic example;
2. three to five prompts;
3. a small mechanistic subset;
4. matched Malicious, Rejected, and Benign examples;
5. a larger evaluation subset;
6. only then full-scale evaluation and larger models.

Every stage must pass smoke tests before expensive SLURM jobs are submitted.

### 5.6 Do not infer causality from correlation
A layer-wise representation curve is not causal evidence.
Use the term “causal” only when the conclusion is supported by an explicit intervention and appropriate controls.
Keep observational, predictive, and causal results separate in all reports.

### 5.7 Avoid success-only selection bias
The original paper’s central representation analysis uses successful attack examples.
Our analysis must include:

* Malicious;
* Rejected;
* Benign.

Do not select only successful prompts and then claim that their representation trajectory explains success.
Compare outcomes under matched conditions.

### 5.8 Separate evaluation metrics
Do not use “ASR” ambiguously.
Report separately:

* binary malicious-response rate;
* binary refusal rate;
* binary benign-misunderstanding rate;
* mean StrongReject score;
* median StrongReject score;
* semantic probe score;
* intervention effect size.

The paper reports the average continuous StrongReject score as ASR in some experiments. Preserve this metric for reproduction, but do not confuse it with a binary success percentage.

### 5.9 Preserve native model generation behavior
Use each model’s official chat template and native generation configuration.
Do not overwrite a model’s native end-of-sequence configuration with an incorrect scalar value.
In particular:

* preserve all native EOS and end-of-turn token IDs;
* inspect `model.generation_config.eos_token_id`;
* support list-valued EOS configurations;
* log actual stopping tokens;
* verify that outputs stop correctly.

We previously encountered severe generation errors when a model’s native multi-token stopping configuration was overwritten. Do not repeat this mistake.

### 5.10 Handle tokenization explicitly
Never assume `carrot`, `potato`, or `bomb` is represented by exactly one token.
For every model:

* record tokenization;
* record all target token indices;
* distinguish first, last, and pooled word representations;
* test at least the final subtoken and a pooled representation if the word is split;
* never hardcode token offsets that depend on prompt length;
* validate positions after applying the chat template.

If exact single-token pairs are required for a controlled experiment, search for and document them.

### 5.11 Use paired examples
Direct, Neutral, and Doublespeak prompts must be matched as closely as possible.
Control for:

* wording;
* target position;
* sentence structure;
* length;
* chat formatting;
* tokenization;
* generation settings.

Do not compare unrelated prompts and call the difference a semantic direction.

### 5.12 Responsible handling of harmful outputs
This is authorized academic safety research, but the pipeline must minimize unnecessary exposure to harmful content.

* Do not print detailed harmful generations to the terminal.
* Redact dangerous procedural content in human-facing summaries.
* Use prompt IDs and category labels in plots.
* Store raw generations only where required for evaluation and under the repository’s established access controls.
* Never include operational harmful instructions in README files, presentations, or reports.
* Use automated judges and abstract labels where possible.
* Preserve enough data for research reproducibility without unnecessarily reproducing harmful content.

### 5.13 Statistical rigor
Use paired statistical tests where appropriate.
Report:

* sample sizes;
* confidence intervals;
* bootstrap intervals;
* paired effect sizes;
* seed variability;
* multiple-comparison correction for large layer/head sweeps.

Do not report only the best layer or best alpha selected after looking at the test set.
Use development and held-out evaluation splits for intervention selection.

### 5.14 No silent deviations
When implementation differs from the paper, record:

* what changed;
* why it changed;
* expected impact;
* whether the change affects comparability.

### 5.15 Autonomous but careful execution
Do not stop at every small ambiguity.
Inspect the repository and make the most grounded decision available.
Log important assumptions.
Do not launch expensive jobs before validating that the implementation is correct.

## 6. Initial reproduction targets

Reproduce the paper’s Doublespeak setup before introducing our interventions.
Use the official repository where possible rather than recreating the attack from memory.

The paper uses:

* AdvBench as the harmful-prompt source;
* prompt simplification to isolate one harmful concept;
* a benign substitute such as `potato`;
* generated context sentences;
* a final query where the harmful concept is replaced by the substitute;
* StrongReject-based evaluation;
* manual categories of Malicious, Benign, and Rejected.

Verify exact implementation details from the official code.
If the processed prompts or generated context sentences are already available in the repository, use those for exact reproduction.
Do not silently regenerate them with a different model.

If reproduction requires GPT-4o-mini or GPT-4o and no configured credentials are available:

* use provided processed artifacts;
* or clearly document that exact regeneration is unavailable;
* do not replace them with a different model without marking the run as a methodological variant.

## 7. Controlled prompt conditions

For each selected harmful concept, construct at least the following matched conditions.

### A. Direct concept
The final request contains the original harmful concept directly.
Example notation: `DIRECT_BOMB`
This condition provides a source representation for the explicit harmful concept.

### B. Neutral codeword
The request contains `carrot`, but there are no demonstrations teaching it a new meaning.
Example notation: `NEUTRAL_CARROT`
The model should interpret the word literally.

### C. Doublespeak codeword
The request contains `carrot`, preceded by demonstrations that establish `carrot` as the substitute for the harmful concept.
Example notation: `DOUBLESPEAK_CARROT`

### D. Context-only controls
Create controls such as:

* equivalent-length benign context;
* shuffled demonstrations;
* demonstrations containing `carrot` without harmful semantics;
* harmful contexts without consistent codeword substitution;
* unrelated concept substitutions.

### E. Repetition diagnostic
Create a minimal controlled diagnostic prompt containing repeated target tokens, for example:
`carrot carrot carrot`
or a grammatical benign sentence containing several matched occurrences.
This is not automatically a jailbreak experiment.
Use it as a controlled sufficiency test:

* inject or patch the representation of the harmful concept into one or more `carrot` positions;
* determine whether probes and Patchscopes decode the target harmful concept;
* determine whether downstream behavior changes under a separately defined neutral task.

Keep semantic decoding and full behavioral jailbreak claims separate.

## 8. Stage 1 — Representation mapping

### 8.1 Activation collection
For Direct, Neutral, and Doublespeak conditions, collect the target-token representations at every layer.
At minimum, collect:

* residual stream before the block;
* residual stream after attention;
* residual stream after MLP;
* final residual stream.

If storage permits, retain attention-head outputs for the small diagnostic subset.
Do not initially save full-sequence, full-layer activations for the full dataset.
Save only required positions and components, in a chunked format with explicit metadata.

**Do not inspect only the codeword token itself.** The decoded harmful concept may be transferred downstream rather than remaining localized at the codeword position. In addition to the codeword token, also collect and compare the representations of:

* the immediately following token(s) after the codeword;
* the first generated answer tokens.

Track at every layer where and when the harmful concept appears across these positions — whether it stays localized at the codeword, moves to the following token, or only surfaces in the generated answer tokens. Store these position-resolved trajectories separately so downstream transfer is measurable rather than assumed.

Add **nearest-neighbor decoding** (embedding-space nearest tokens to the representation) as an auxiliary diagnostic alongside logit lens and Patchscopes. Do not treat nearest-neighbor decoding as standalone evidence of semantic meaning or causality — it is a corroborating signal only, to be triangulated with probes and interventions.

### 8.2 Harmful semantic direction
For each layer, construct a matched mean-difference direction:

d_harm^(ℓ) = μ_direct^(ℓ) − μ_neutral^(ℓ)

Use training examples only.
Do not construct and evaluate the direction on the same examples without cross-validation.
Also train a simple linear probe distinguishing Direct from Neutral representations.
Compare:

* mean-difference direction;
* logistic-regression probe;
* whitened mean difference if statistically justified;
* cosine-based centroids.

### 8.3 Doublespeak trajectory
For each layer, measure how far the Doublespeak codeword has moved from Neutral toward Direct.
At minimum compute:

* projection onto d_harm^(ℓ);
* cosine similarity to Direct centroid;
* cosine similarity to Neutral centroid;
* normalized Direct-versus-Neutral score;
* linear-probe probability;
* Patchscopes decoding score;
* logit-lens score where meaningful.

Define and store:

* semantic onset layer;
* maximum harmful alignment;
* early-layer harmful alignment;
* late-layer harmful alignment;
* area under the harmful-alignment curve;
* early-to-late change.

Do not infer meaning from raw cosine similarity alone.

### 8.4 Outcome comparison
Compare trajectories across:

* Malicious;
* Rejected;
* Benign.

A major hypothesis is:

* Benign: no strong harmful semantic transition.
* Rejected: harmful meaning emerges sufficiently early or strongly to trigger refusal.
* Malicious: harmful meaning emerges later, after the most refusal-sensitive region.

Treat this as a hypothesis, not a conclusion.

## 9. Stage 2 — Activation patching

Activation patching is the first major causal experiment.

### 9.1 Necessity patch
Run a successful Doublespeak prompt.
At a chosen layer and target position, replace the Doublespeak activation with the matched Neutral activation:

h_DS^(ℓ) ← h_Neutral^(ℓ)

Sweep across:

* every layer;
* pre-attention residual;
* post-attention residual;
* post-MLP residual;
* single layer;
* short windows of consecutive layers;
* from layer ℓ through the end.

Measure whether this intervention changes:

* semantic decoding;
* target-concept probe score;
* refusal;
* benign misunderstanding;
* malicious behavior;
* StrongReject score.

A necessity claim requires that neutralizing the relevant representation reliably reduces the target semantic interpretation and downstream attack behavior.

### 9.2 Sufficiency patch
Start with a Neutral `carrot` prompt.
Patch in either:

h_Neutral^(ℓ) ← h_Doublespeak^(ℓ)

or:

h_Neutral^(ℓ) ← h_Direct^(ℓ)

Sweep layers and components.
Determine whether this intervention is sufficient for:

1. semantic probe movement;
2. Patchscopes decoding;
3. downstream interpretation;
4. output behavior.

Do not describe a probe-only change as full behavioral sufficiency.

### 9.3 Reverse and unrelated patches
Include:

* Doublespeak → Neutral;
* Neutral → Doublespeak;
* Neutral → Direct;
* Doublespeak → unrelated concept;
* Neutral → unrelated concept;
* random-vector patch controls.

## 10. Stage 3 — Directional interventions

### 10.1 Harmful-direction addition
Inject the layer-specific harmful direction:

h' = h + α · d_harm^(ℓ)

Sweep:

* layer;
* alpha;
* target position;
* single-layer versus multi-layer injection;
* pre-attention, post-attention, and post-MLP locations.

Use both positive and negative alpha values.

### 10.2 Harmful-direction removal
For Doublespeak examples, remove the harmful component:

h' = h − α · (⟨h, d⟩ / ‖d‖²) · d

Test both:

* complete projection removal;
* partial removal.

### 10.3 Timing experiment
This is a top-priority experiment.
Use the same direction and norm-matched intervention at:

* early layers;
* middle layers;
* late layers.

The central test is whether early and late injection produce different outcomes:

* early harmful meaning may increase Rejected outcomes;
* late harmful meaning may increase Malicious outcomes;
* very late intervention may affect decoding without changing the final behavior.

Use held-out prompts and fixed alpha values chosen on development data.

### 10.4 Refusal-direction interaction
If the existing project already contains reliable refusal-direction code, measure and intervene on both:

* harmful semantic direction;
* refusal direction.

Test a small factorial design:

* no intervention;
* harmful direction only;
* refusal direction only;
* both directions.

Apply these at early and late layers.
This can test whether harmful semantic timing and refusal activation interact.
Do not assume the refusal direction is the complete safety mechanism.

## 11. Stage 4 — Attention knockout and causal tracing

### 11.1 Block information from demonstrations
For the target `carrot` token in the final request, selectively block attention to:

* previous `carrot` occurrences;
* words that reveal the harmful context;
* individual demonstration sentences;
* all demonstrations;
* matched benign context positions.

Use proper attention-mask or hook-based intervention without corrupting unrelated causal attention structure.

### 11.2 Layer and head sweep
Identify layers and heads where knockout produces the largest reduction in:

* harmful semantic alignment;
* semantic probe score;
* malicious behavior.

Use a coarse-to-fine procedure:

1. layer-level attention knockout;
2. head groups;
3. individual heads;
4. selected path-patching experiments.

Correct for multiple comparisons.

### 11.3 Path patching
Where feasible, trace paths from:

demonstration tokens → attention heads → target codeword representation → answer tokens

Only attempt detailed path patching after a robust layer/head signal exists.

### 11.4 MLP contribution
If attention knockout does not fully explain the transition, test whether MLP blocks create or transform the harmful semantic representation.
Compare:

* attention output patching;
* MLP output patching;
* full residual patching.

## 12. Stage 5 — Mechanistic attack objective

Do not begin prompt optimization until at least one causal intervention produces a reliable held-out effect.

### 12.1 Temporal objective
Define a representation-level objective that rewards:

* benign similarity in early layers;
* harmful similarity in late layers.

For example:

J_temporal = (1/|L_late|) Σ_{ℓ∈L_late} s_ℓ − λ · (1/|L_early|) Σ_{ℓ∈L_early} s_ℓ

Optionally add early benign-retention:

J = J_temporal + γ · (1/|L_early|) Σ_{ℓ∈L_early} sim(h_candidate^(ℓ), h_neutral^(ℓ))

The objective should not merely maximize harmful similarity at every layer.
That could make the harmful meaning visible too early and increase refusal.

### 12.2 Optimization variables
Evaluate optimization over:

* codeword choice;
* number of demonstrations;
* demonstration order;
* demonstration wording;
* context words around the codeword;
* final-query wording;
* short natural-language suffix;
* adversarial discrete tokens only at a later stage.

Start with interpretable search over codewords and demonstration wording.
Only then consider GCG-style discrete optimization.

### 12.3 Optimization baselines
Compare:

1. original paper prompt;
2. random codeword and random context selection;
3. late harmful similarity only;
4. early-benign plus late-harmful temporal objective;
5. output-compliance objective;
6. combined representation and behavior objective.

Evaluate all methods on held-out prompts.

### 12.4 Avoid objective leakage
Do not optimize and report on the same requests.
Separate:

* objective construction set;
* development set;
* held-out test set;
* cross-concept transfer set;
* cross-codeword transfer set;
* cross-model transfer set.

## 13. Stage 6 — Codeword study

Construct a controlled pool of benign substitute words.
Include variation in:

* static embedding distance from the harmful concept;
* lexical category;
* frequency;
* token count;
* concreteness;
* polysemy;
* semantic neighborhood density.

Include at least:

* the paper’s main substitute, `potato`;
* the illustrative substitute, `carrot`;
* several additional one-token benign nouns;
* matched words from other lexical categories where appropriate.

For each codeword, measure:

* tokenizer behavior;
* static embedding distance;
* baseline harmful association;
* early benign alignment;
* late harmful alignment;
* semantic onset layer;
* Malicious rate;
* Rejected rate;
* Benign rate;
* StrongReject score.

Test whether static embedding distance predicts attack success after controlling for:

* token frequency;
* token length;
* contextual learnability;
* model;
* number of demonstrations.

Do not select the best codeword using the final test set.

## 14. Stage 7 — Scaling and generalization

Only after the 8B causal result is reliable, expand along the following axes.

**Models**

* Llama-3.1-8B-Instruct;
* selected experiments on Llama-3.3-70B-Instruct;
* Gemma-3-270M-IT;
* Gemma-3-1B-IT;
* Gemma-3-4B-IT;
* selected experiments on Gemma-3-27B-IT.

**Concepts**
Use multiple harmful categories from the processed AdvBench data without exposing detailed content in summaries.

**Codewords**
Use several matched codewords.

**Context lengths**
Reproduce or approximate the paper’s context-length sweep.

**Multiple concepts**
Only after the single-concept analysis is complete, test multi-token hijacking.

**Transfer**
Evaluate whether:

* a direction learned from one concept transfers to related concepts;
* a temporal objective learned on one codeword transfers to another;
* a codeword/context optimized on one model transfers to another.

## 15. Stage 8 — Defense experiments

After establishing the mechanism, implement a small number of mechanism-based defenses.

Candidate defenses include:

**Late-layer safety probe**
Run a harmful-semantic probe at later layers, after contextual meaning has emerged.

**Early–late discrepancy detector**
Measure:

D = s_late − s_early

Flag prompts where a benign-looking token undergoes a large harmful semantic transition.

**Harmful-direction removal**
Remove the harmful semantic direction in the identified critical late-layer window.

**Information-flow blocking**
Block the attention path that transfers the codeword mapping from demonstrations.

Evaluate:

* attack reduction;
* benign utility;
* false-positive rate;
* effects on legitimate in-context learning;
* computational overhead.

A defense is not useful if it destroys ordinary contextual word learning.

## 16. Evaluation framework

For each generated response, store:

* prompt ID;
* condition;
* model;
* seed;
* generation settings;
* raw output in protected result storage;
* redacted output for human-facing reports;
* binary refusal;
* binary benign misunderstanding;
* binary malicious response;
* StrongReject score;
* judge explanation where permitted;
* manual-review status.

Use the three-way labels:

* `MALICIOUS`;
* `REJECTED`;
* `BENIGN`.

Where ambiguous, use:

* `UNCLEAR`;
* require manual review;
* do not force an uncertain label.

For intervention experiments, also store:

* source condition;
* target condition;
* layer;
* component;
* position;
* alpha;
* direction source;
* direction norm;
* pre-intervention semantic score;
* post-intervention semantic score;
* output change;
* paired effect.

## 17. Statistical analysis

Use paired comparisons because the same base prompt appears under multiple conditions.
Depending on the metric, use:

* paired bootstrap confidence intervals;
* permutation tests;
* McNemar’s test for paired binary outcomes;
* mixed-effects logistic regression for multi-model or multi-prompt analysis;
* multiple-testing correction for layer/head sweeps.

Report both:

* statistical significance;
* practical effect size.

For layer sweeps, do not choose the best layer on all data and then report its uncorrected p-value.
Use development examples to identify candidate layers and held-out examples to test them.

## 18. Required controls

Every causal experiment should include relevant controls.
At minimum:

* random direction with identical norm;
* unrelated semantic direction;
* target-position versus adjacent-position injection;
* target-token versus random-token injection;
* positive versus negative alpha;
* norm-only rescaling;
* shuffled source-target patch;
* matched benign concept;
* matched prompt-length control;
* no-intervention replay.

Where possible, use multiple random control directions.

## 19. Implementation structure

Adapt to the repository, but ensure the following logical components exist.

**Core modules**

* model loading;
* chat-template handling;
* target-token localization;
* activation capture;
* activation patching;
* directional intervention;
* attention knockout;
* probe training;
* Patchscopes or compatible decoding;
* generation;
* evaluation;
* statistics;
* plotting;
* run registry.

**Suggested scripts** (names may be adjusted to existing conventions)

* `00_audit_environment.py`
* `01_prepare_doublespeak_data.py`
* `02_run_behavioral_baselines.py`
* `03_extract_target_activations.py`
* `04_train_semantic_probes.py`
* `05_run_activation_patching.py`
* `06_run_direction_interventions.py`
* `07_run_attention_knockout.py`
* `08_optimize_doublespeak_context.py`
* `09_evaluate_generations.py`
* `10_analyze_causal_results.py`
* `11_generate_research_report.py`

**Configuration**
Use declarative YAML or JSON configurations for:

* models;
* datasets;
* prompt conditions;
* layers;
* intervention types;
* alpha sweeps;
* generation;
* evaluation;
* SLURM resources.

Do not bury experiment parameters in source code.

## 20. SLURM rules

Inspect previous successful SLURM scripts in the repository and follow their conventions.
For every job:

* activate the correct environment;
* print hostname and GPU information;
* print git commit;
* print Python path and package versions;
* use explicit output and error logs;
* create the output directory before execution;
* fail on errors;
* use checkpointing or resumable shards;
* avoid recomputing completed shards;
* write a completion marker only after validation.

Run a local or interactive smoke test before submitting an array.
Use arrays for prompt shards and layer sweeps where appropriate.
Do not request excessive GPUs for an 8B experiment.
Do not use quantization for mechanistic activation comparisons unless a separate experiment verifies that quantization preserves the relevant representations.
For 70B experiments, first determine whether the cluster supports the required multi-GPU setup. Do not submit a configuration that is likely to fail immediately.

## 21. Data and storage efficiency

Full activation tensors can become extremely large.
Initially store only:

* target-token positions;
* selected neighboring positions;
* required residual components;
* compact metadata.

Use chunked, appendable storage such as HDF5, Zarr, or carefully structured PyTorch shards.
Do not store full activations for all sequence positions, layers, models, and prompts unless explicitly justified.
Build integrity checks that verify:

* number of examples;
* expected layers;
* expected target positions;
* no duplicate prompt IDs;
* no missing shards;
* compatible model revisions.

## 22. Required documentation

Create or update the following documents.

**`DOUBLESPEAK_RESEARCH_PLAN.md`**
A concise description of: thesis context; paper gap; research questions; stages; success criteria.

**`PAPER_REPRODUCTION_NOTES.md`**
Document: exact paper behavior reproduced; exact model checkpoints; prompts and datasets; deviations; reproduction results; unresolved differences.

**`DOUBLESPEAK_MASTER_LOG.md`**
Append-only chronological log containing: date; command; run ID; code revision; configuration; status; key findings; failures; next action.

**`EXPERIMENT_REGISTRY.csv`**
One row per experiment or run with machine-readable metadata.

**`CAUSAL_RESULTS_SUMMARY.md`**
Separate: observational findings; predictive findings; causal findings; failed interventions; open questions.

**`README.md`**
Include exact commands for: environment setup; smoke test; baseline run; activation extraction; patching run; evaluation; report generation; SLURM submission.

## 23. Tests

Implement tests for:

* target-token position detection;
* multi-token words;
* chat-template formatting;
* EOS handling;
* activation replacement;
* intervention applied only at requested positions;
* alpha zero reproduces baseline;
* random direction has expected norm;
* output files contain all required metadata;
* resuming does not duplicate examples;
* completed shards are not overwritten;
* source and target prompt pairing.

For patching, include a synthetic test demonstrating that replacing an activation actually changes the downstream tensor at the intended layer and nowhere else.

## 24. Initial minimum viable experiment

Before broad reproduction, implement this small end-to-end experiment on Llama-3.1-8B-Instruct.
Use approximately three to five manually inspected prompts.
For each prompt, run:

1. Direct concept.
2. Neutral `carrot`.
3. Doublespeak `carrot`.

Collect target representations at every layer.
Then run:

**Experiment A — Necessity**
Patch Doublespeak with Neutral at each layer.

**Experiment B — Sufficiency**
Patch Neutral with Direct at each layer.

**Experiment C — Timing**
Inject the harmful direction at: representative early layers; representative middle layers; representative late layers.
Use several norm-controlled alpha values.

**Experiment D — Demonstration attention knockout**
Block the final `carrot` token from attending to earlier codeword occurrences.

For every experiment, measure both: semantic interpretation; behavioral outcome.

Generate a compact diagnostic report showing:

* layer-wise semantic trajectories;
* intervention heatmaps;
* output category changes;
* refusal changes;
* effect sizes;
* failed cases.

## 25. Criteria for advancing to expensive experiments

Do not immediately scale merely because the code runs.
Advance only if:

1. Baseline behavior is reproducible.
2. Target-token indices are validated.
3. Direct, Neutral, and Doublespeak trajectories differ meaningfully.
4. Alpha zero reproduces the unmodified baseline.
5. Random controls do not reproduce the semantic effect.
6. At least one intervention changes semantic interpretation on held-out examples.
7. Behavioral effects are evaluated separately from probe effects.
8. Results survive multiple prompts and seeds.

If these criteria fail, diagnose the mechanism rather than launching larger models.

## 26. Definition of a strong causal result

A strong result would contain several complementary findings:

1. Doublespeak moves the codeword representation toward the harmful concept.
2. Removing this component reduces semantic interpretation and attack behavior.
3. Adding this component to a neutral codeword induces semantic interpretation.
4. Early and late injection produce systematically different refusal/compliance outcomes.
5. The effect is localized to specific layers, components, or information paths.
6. Random and unrelated directions do not produce the same behavior.
7. The result replicates on held-out prompts.
8. At least one part generalizes to another paper model.

Do not claim complete sufficiency if the intervention changes only a probe but not model behavior.
Do not claim a time-of-check mechanism unless early-versus-late interventions causally separate refusal from compliance.

## 27. Priorities

Use the following strict priority order.

* **Priority 1** — Audit and reproduce the paper’s core setup on Llama-3.1-8B-Instruct.
* **Priority 2** — Construct Direct, Neutral, and Doublespeak matched conditions and map their representations.
* **Priority 3** — Run activation patching for necessity and sufficiency.
* **Priority 4** — Run early-versus-late harmful-direction injection.
* **Priority 5** — Compare Malicious, Rejected, and Benign trajectories.
* **Priority 6** — Run attention knockout and selected path patching.
* **Priority 7** — Build and validate the temporal representation objective.
* **Priority 8** — Study codeword properties and embedding distance.
* **Priority 9** — Generalize to Gemma-3 and Llama-3.3-70B-Instruct.
* **Priority 10** — Test mechanism-based defenses.

## 28. What not to do

Do not:

* start by optimizing arbitrary suffixes;
* begin with the 70B model;
* analyze only successful attacks;
* report cosine similarity as proof of meaning;
* describe a probe correlation as causality;
* silently regenerate the paper’s data with another model;
* overwrite previous thesis results;
* expose detailed harmful outputs in reports;
* report the best post-hoc layer without held-out validation;
* confuse StrongReject mean score with binary attack rate;
* ignore tokenization differences;
* assume the refusal direction represents the complete safety mechanism;
* submit expensive jobs before smoke testing;
* stop after producing plots without testing interventions.

## 29. Immediate execution request

Begin now by doing the following:

1. Audit the existing thesis repository and environment.
2. Read the Doublespeak paper and official implementation.
3. Identify the exact model checkpoints and dependencies.
4. Create a separate `doublespeak_causality` research module.
5. Write the research-plan and reproduction-notes documents.
6. Implement the matched Direct, Neutral, and Doublespeak prompt pipeline.
7. Add robust target-token localization.
8. Run a three-to-five-example behavioral and activation smoke test on Llama-3.1-8B-Instruct.
9. Implement the first activation-patching necessity and sufficiency experiments.
10. Produce an initial diagnostic summary with real results only.
11. Prepare resumable SLURM scripts for the larger 8B layer sweep.
12. Update the master log with everything completed, failed, or still not run.

Do not only tell me what could be implemented.
Implement and validate as much of this as the available environment permits.

At the end, provide:

* the files created or changed;
* commands executed;
* smoke-test results;
* bugs found;
* unresolved blockers;
* jobs submitted and their IDs, if any;
* the exact next experiment with the highest expected research value.
