# HERETIC × CSI — ORIGINAL USER SPRINT MANDATE (VERBATIM)

**Recorded:** 2026-10-13, at the user's request. **Author of the mandate:** Omer Yosef.
**Status:** reference copy of the user's instructions, written down as given. The numbering
irregularities (e.g. the second "24." under §23 and the restart at "8." under §28) are in the
original and were left as is.

**Relationship to other files:** this sprint's plan and append-only progress log, which interprets
and implements this mandate, is
`external_md/HERETIC_CAUSAL_SEMANTIC_INSTALLATION_PLAN_AND_PROGRESS_20261001.md`. That log restates
the mandate in its own words; this file keeps the original text. If the two conflict, this file
records what was asked.

---

We are starting a new research sprint that integrates Heretic into our existing Doublespeak / causal-semantic-installation project.

Heretic:
https://github.com/p-e-w/heretic
https://heretic-project.org/

The goal is NOT merely to run Heretic's default "decensoring" pipeline.

The goal is to exploit Heretic's infrastructure — especially Arbitrary-Rank Ablation (ARA), its module-I/O optimization, LoRA-based weight interventions, external Modifier/Scorer plugin API, and Optuna multi-objective search — to answer the next mechanistic question in our existing research:

Can the causal semantic-installation mechanism we have found be distilled into a compact weight-level operator/subspace intervention, and does the required dimensionality / location explain the basket-vs-button dissociation?

This is a research sprint. Treat Heretic as a mechanistic-intervention framework.

Do not wait for me after writing the plan. Implement the plan and run the experiments.

## 0. FIRST: READ BEFORE TOUCHING ANYTHING

Before coding or launching jobs, deeply inspect the existing repository and understand the current scientific state.

Read, at minimum:

* `SUMMARY_2026-09-02_TO_09-26.md`
* `reports/DCS_CSI_CLAIM_TABLE.md`
* `reports/DCS_CSI_RESULTS_DRAFT.md`
* the authoritative CSI `external_md/...20260915...md` progress log
* existing `dcs_csi_*` analysis/intervention scripts
* frozen preregistrations and runargs
* the current domain/codeword split definitions
* the latest git history and working tree
* any untracked OPTIONMASS / sensitivity files mentioned in the summary

Then independently inspect Heretic itself.

Clone or otherwise obtain:
`https://github.com/p-e-w/heretic`

Pin the exact commit SHA used in every experiment.

Read at least:

* `README.md`
* `config.default.toml`
* `src/heretic/main.py`
* `src/heretic/model.py`
* `src/heretic/plugin.py`
* `src/heretic/modifier.py`
* `src/heretic/scorer.py`
* `src/heretic/evaluator.py`
* `src/heretic/modifiers/abliteration.py`
* `src/heretic/modifiers/ara.py`
* `src/heretic/scorers/*`

Do NOT treat Heretic as a black box.

Write down exactly:

1. what ARA optimizes;
2. which modules it currently modifies;
3. which token position its module-I/O hooks capture;
4. which parameters Optuna searches;
5. how reset/reproduction works;
6. how external Modifier and Scorer plugins work;
7. what can be reused without modifying upstream Heretic.

Important discovery you should independently verify from source:

Current ARA captures module input/output at the LAST PREFILL POSITION (`[:, -1, :]`).

That is not sufficient for our primary experiment because our strongest causal site is associated with particular prompt positions / codeword rows.

Do not silently use last-token ARA as if it were testing our mechanism.

## 1. DOCUMENTATION FIRST

Create an authoritative append-only research log, e.g.
`external_md/HERETIC_CAUSAL_SEMANTIC_INSTALLATION_PLAN_AND_PROGRESS_20261001.md`

The top of that file must contain:

* exact scientific motivation;
* exact inherited results;
* hypotheses;
* experiment gates;
* frozen data populations;
* train/selection/confirmation policy;
* metrics;
* control families;
* stopping rules;
* VOID conditions;
* artifact paths;
* Heretic commit SHA;
* our repository commit SHA;
* model revision/tokenizer revision;
* environment;
* SLURM information.

Append progress to this file continuously.

Never rewrite history to make a result look cleaner.

Negative results, nulls, bugs, corrections, abandoned hypotheses, and contradictions are first-class results.

## 2. SCIENTIFIC CONTEXT THAT MUST BE PRESERVED

Do not accidentally rediscover or overstate claims we already resolved.

The relevant inherited picture is approximately:

* Llama-3.1-8B-Instruct shows a real Doublespeak effect.
* The effect did not replicate on Qwen3-14B in the prior capable replication.
* Semantic installation is highly decodable, but simple decodability is not sufficient evidence of causality.
* The inherited scalar "Bombness"/`d_surface` story failed as a general causal representation.
* Installation→attack-success correlation was TRAIN-only and did not cleanly replicate on held-out splits.
* Attention knockout can strongly reduce semantic installation/refusal-related effects without materially changing content-true attack success.
* raw LLM-judge ASR badly overestimated content-true success, so DO NOT optimize against a naive LLM-judge ASR metric.
* whole-state rescue establishes that the relevant site can carry causal information.
* the rank-1 semantic axis gives a strong codeword dissociation:
   * basket: controlled rank-1 rescue works;
   * button: matched-power rank-1 rescue fails.
* this is not adequately explained by layer choice alone.
* the codeword position is unusually important.
* an approximately 8-head circuit carries much of the basket knockout effect.
* the strongest basket head does not simply transfer in amplitude to button.
* cell-depth structure transfers better than raw effect amplitude.
* all claims must remain scoped to the exact rung / endpoint they actually establish.

Most importantly:

Rank-1 failure does NOT imply that the semantic mechanism is non-causal, because whole-state rescue works.

Therefore the natural next question is dimensionality / distributed transformation.

This is where Heretic ARA becomes interesting.

## 3. CENTRAL HYPOTHESIS

Heretic's ARA removes the single-direction assumption.

Instead of saying:
`semantic mechanism ≈ one direction v`

we will test whether the causal transformation is better approximated by a low-rank operator:
`ΔW = B A`
with effective rank greater than 1.

The primary hypothesis is:

The basket-vs-button dissociation partly reflects a difference in the dimensionality and/or operator structure required to install or restore the concept, rather than merely the existence or absence of a rank-1 semantic direction.

A second hypothesis is:

ARA can discover a compact operator-level intervention whose learned singular subspace overlaps the causal head/layer structure we independently identified.

A third hypothesis is:

Heretic's learned operator can be distilled back into a mechanistically interpretable low-dimensional subspace, giving us a better candidate causal variable than the old `d_surface` / Bombness scalar.

These hypotheses MUST be tested, not assumed.

## 4. DO NOT START BY MODIFYING HERETIC

Keep upstream Heretic isolated and pinned.

Prefer using its external plugin API.

Create research-specific code under our repository, for example:
`research/heretic_csi/`

with something like:

* `position_aware_ara.py`
* `semantic_installation_scorer.py`
* `state_geometry_scorer.py`
* `preservation_scorer.py`
* `head_restricted_ara.py`
* `extract_learned_subspace.py`
* `configs/`
* tests

Heretic supports external plugins of the form:
`path/to/plugin.py:ClassName`

Use that mechanism if practical.

Only patch/fork Heretic itself when the plugin API genuinely cannot support the experiment.

If an upstream modification is necessary, keep the patch minimal and explicitly document it.

Heretic is AGPL-licensed. Preserve its license and attribution; do not copy large chunks into our project without tracking provenance/license.

## 5. PHASE A — REPRODUCE AND AUDIT HERETIC

Before doing science, make sure we understand the machinery.

Run a tiny smoke test.

Do not spend a huge GPU allocation here.

Validate:

* model loads;
* LoRA reset works;
* ARA optimization runs;
* Optuna study resumes;
* scorers work;
* artifacts are deterministic enough;
* modifier parameters restore correctly;
* model outputs before and after identity reset match.

Produce a tiny artifact comparing:
`base -> modify -> reset -> base`
and verify reset error.

Also inspect ARA's actual learned `ΔW` and numerical rank.

Do not accept "the command completed" as validation.

## 6. PHASE B — NATIVE HERETIC AS A CONTROL

Run vanilla Heretic ARA using OUR matched populations, not blindly using `mlabonne/harmful_behaviors`.

This is deliberately a baseline/control because native ARA uses the last prefill position.

Construct frozen local dataset files from the existing TRAIN population.

Do not invent what cells A/B/C/E mean.

Recover their exact definitions from existing code/artifacts first and document the mapping.

For semantic experiments, rename ARA's conceptual groups in our notes from:
`good / bad`
to:
`target / source`
so we do not confuse Heretic's safety terminology with our semantic experimental design.

Use domain-matched examples.

Do NOT allow nearest-neighbor matching to pair unrelated semantic domains without testing that explicitly.

Run the native last-position ARA baseline and record whether it changes:

* semantic installation;
* semantic logodds / option mass;
* frozen probe readout;
* refusal;
* benign control behavior;
* KL;
* content-true behavior.

Do not expect this experiment to work.

Its purpose is to establish whether generic end-of-prompt operator editing is sufficient.

## 7. PHASE C — BUILD POSITION-AWARE ARA

This is the most important engineering step.

Create an external Modifier inspired by Heretic ARA but capable of capturing module I/O at specific prefill positions per example, not simply `[:, -1, :]`.

Call it something like:
`PositionAwareARA`
or another clear name.

It must support position selectors such as:

* exact codeword token;
* exact query codeword;
* `rel-10`;
* `rel-6`;
* existing readout position;
* matched neutral/control positions;
* optionally multiple positions.

Do NOT assume a fixed absolute token index across prompts.

Find the correct token using the existing prompt metadata/token-span infrastructure.

For every example, save:

* raw text;
* tokenized text;
* absolute target position;
* relative position;
* token ID;
* decoded token;
* codeword span;
* whether codeword is one token or multiple tokens.

Fail loudly if token selection is ambiguous.

Padding must be handled correctly.

Write unit tests with different prompt lengths.

The I/O hook must capture the intended token, not a padding token or generated token.

## 8. DEFINE A CSI-SPECIFIC ARA OBJECTIVE

Vanilla ARA uses a generic geometric objective.

For our paired domain design, implement a stronger matched objective.

For each matched source/target pair, optimize a weight edit so that at the intervention site:

1. target/control representations change as little as possible;
2. source representations move toward their matched target representations;
3. optionally, source representations move away from their original source state;
4. unrelated/domain-control examples remain stable.

Start from a mathematically explicit loss such as:
`L = λ_preserve L_preserve + λ_target L_source_to_target + λ_away L_away`

but compare multiple valid formulations on TRAIN rather than declaring one correct.

At minimum compare:

* paired MSE;
* cosine / angular objective;
* whitened representation distance;
* Heretic's original kNN formulation.

Any choice used for confirmation must be frozen based on TRAIN only.

Do not tune an objective on the final behavioral endpoint.

## 9. THE CORE EXPERIMENT — RANK SWEEP

This is probably the highest-value experiment.

Run the same matched intervention with LoRA/operator rank:
`1, 2, 4, 8, 16, 32, 50`
and possibly one full-rank diagnostic if technically feasible.

Do it independently for:

* basket;
* button.

Primary endpoint:
semantic installation / semantic rescue, not raw jailbreak ASR.

The core plot should be something like:
`semantic rescue vs intervention rank`
for basket and button.

Also report:

* parameter count;
* intervention norm;
* KL/preservation loss;
* refusal;
* random-rank-matched control distribution.

The question is:

Does basket saturate at rank 1 while button requires rank > 1?

That would directly connect Heretic/ARA to the dissociation we already found.

But DO NOT overclaim if button simply never responds.

Possible outcomes must be preregistered:

A. basket low-rank, button higher-rank;
B. both low-rank;
C. both require multi-rank;
D. button remains resistant even at high rank;
E. the effect disappears under proper controls.

All five are scientifically meaningful.

## 10. CONTROLS FOR EVERY RANK

A rank-k intervention cannot be compared with a rank-1 null.

Use rank-matched controls.

At minimum include:

* random orthogonal rank-k subspaces;
* shuffled source↔target domain pairing;
* norm-matched random LoRA updates;
* neutral-position optimization;
* no-op identity adapter;
* source→source fitting;
* target→target fitting.

Match:

* rank;
* approximate update norm;
* targeted layers;
* targeted components;
* number of optimized parameters;
* training examples.

No "rank-5 is significant compared with rank-1 controls" mistakes.

We already learned that lesson.

## 11. LAYER AND COMPONENT SEARCH

Heretic's Optuna machinery is useful here.

But keep discovery and confirmation separate.

On TRAIN, allow Optuna to search:

* start layer;
* end layer;
* attention vs MLP;
* rank;
* preserve weight;
* steering weight;
* overcorrection weight;
* possibly optimizer hyperparameters.

Bias the initial search toward layers implicated by existing evidence, but include enough surrounding layers to falsify that belief.

Our existing work makes layers around:
L6, L8, L10, L11, L14, L18
especially interesting.

Do not hard-code those as the only possibilities without a control/search region.

After TRAIN search, freeze a small set of candidates.

Do not keep searching validation until something passes.

## 12. HEAD-RESTRICTED ARA

This can make the project substantially more interesting.

We already have evidence implicating a concentrated head circuit.

Investigate whether ARA's transformation can be restricted to the attention contribution of specific heads.

For Llama attention, do NOT assume the head→`o_proj` mapping.

Inspect the exact implementation and confirm how head outputs are concatenated and mapped into `o_proj`.

If valid, implement a modifier that restricts `ΔW` to the relevant input-column block corresponding to a chosen attention head.

Start with:

* the existing 8-head set;
* heads 2, 19, 17, 23;
* especially the existing L10/head-2 result;
* matched random heads.

Compare:

* full `o_proj` edit;
* target-head-only edit;
* matched random-head edit;
* MLP-only edit;
* attention+MLP edit.

Question:

Can a learned low-rank operator concentrated in the independently discovered causal heads reproduce the semantic rescue?

If yes, this links two previously separate pieces of evidence:

activation-level causal localization
→
weight-level operator intervention.

Do not call a cell a "writer" without appropriate arbitrary-cell controls.

## 13. EXTRACT THE SUBSPACE HERETIC LEARNS

Do not stop once an intervention works.

The learned edit itself is data.

For every successful ARA intervention, save the effective:
`ΔW = W_modified - W_original`
for every modified module.

Run SVD:
`ΔW = U S V^T`

Analyze:

* singular-value spectrum;
* effective rank;
* cumulative explained Frobenius norm;
* cumulative semantic-rescue contribution;
* left singular vectors;
* right singular vectors.

Then test whether the leading learned vectors align with:

* basket rank-1 installation axis;
* button rank-1 axis;
* old `d_surface`;
* direct-concept direction;
* refusal direction;
* existing probe weights;
* head/cell candidate directions.

Use cosine similarity only as descriptive geometry unless a causal test accompanies it.

Then perform SVD truncation interventions:

top-1,
top-2,
top-4,
top-8,
...

of the learned `ΔW`.

This gives us a much cleaner measure than arbitrary LoRA rank:

What is the minimum learned subspace actually necessary to retain the causal semantic rescue?

Also test removal:

full successful ARA
minus singular component i

to measure necessity of discovered components.

This is potentially one of the key new scientific results.

## 14. USE HERETIC TO TEST THE C1 EXPLANATION

The remaining codeword dissociation currently has a surviving explanation roughly equivalent to:

"basket simply has a better probe."

Quantify this instead of narrating it.

For each codeword, compute independently on held-out data:

* rank-1 probe quality;
* existing semantic-axis quality;
* minimum ARA rank required for semantic rescue;
* maximum attainable controlled rescue;
* singular-spectrum concentration;
* effective learned rank;
* required intervention norm.

Then ask whether probe quality predicts:

* minimal sufficient rank;
* optimization difficulty;
* controlled semantic rescue.

Do this first on discovery data.

Do not use button/basket alone to claim a population relationship.

## 15. SCALE BEYOND TWO CODEWORDS

The project already contains a larger codeword screen.

Recover exactly which codewords are usable and which have already been used for selection.

Do not silently reuse a contaminated set as confirmation.

Use a staged design.

First perform development on a modest set of codewords that spans:

* high frequency;
* medium frequency;
* low frequency;
* strong installer;
* weak installer.

Then freeze the method.

Use untouched codewords / fresh confirmation data for the real population claim.

One central question should be:

Does lexical/codeword frequency predict the dimensionality or strength of the learned semantic-installation operator?

This could explain part of the button/basket asymmetry.

Predeclare the statistic.

Do not post-hoc select only codewords where ARA succeeds.

## 16. HERETIC SCORERS

Implement external Scorer plugins rather than parsing console output.

Potential scorers:

**SemanticInstallationScore**
Primary semantic endpoint using the existing validated semantic metric.

**OptionMassScore**
Existing option-mass/readout endpoint, after fixing the known readout-validity issue.

**RepresentationScore**
Projection/probe metric using frozen analysis objects.

**PreservationScore**
Measure unrelated representation/output preservation.

**KLDivergence**
Reuse Heretic's implementation when appropriate.

**RefusalScore**
Secondary endpoint only.

**ContentTrueBehaviorScore**
Use the project's content-gated endpoint rather than naive raw LLM-judge ASR.

Every scorer must clearly specify:

* direction (`minimize`/`maximize`/none);
* population;
* aggregation unit;
* baseline;
* denominator.

Do not allow a score to change meaning between experiments.

## 17. MULTI-OBJECTIVE OPTIMIZATION

Use Heretic's Optuna infrastructure for actual Pareto optimization.

A scientifically meaningful Pareto problem is:

maximize semantic installation/rescue

while

minimizing unrelated-model change.

For example:

`maximize SemanticInstallation`
`minimize PreservationDamage`
`minimize KL`

Do NOT optimize directly for raw LLM-judge jailbreak success.

That metric is known to be badly confounded in this project.

Behavioral attack endpoints can be measured after the mechanistic intervention is frozen.

Save the entire Pareto front.

Do not report only the nicest point.

## 18. BEHAVIORAL LINKING TEST COMES LAST

Only after a semantic/operator intervention is:

1. reproducible;
2. controlled;
3. held-out;
4. mechanistically interpretable enough;
5. better than rank-matched random controls;

should we test downstream behavior.

Use the same-population chain:

`operator intervention`
→
`semantic installation changes`
→
`downstream behavior/refusal`

Measure both semantics and behavior on the same examples.

Do not infer mediation merely because both change.

And preserve the existing result that semantic/refusal changes have previously failed to move content-true attack success.

A new null here is completely acceptable.

Never optimize around judge false positives.

## 19. DATA AND SPLIT RULES

These are mandatory.

No leakage.

TRAIN is for:

* feature discovery;
* hyperparameter search;
* Optuna;
* choosing ranks/layers/objectives.

A held-out selection split may be used only according to its predeclared role.

The old TEST data must NOT be casually described as "untouched": existing project records indicate it has already been read/used.

For any new confirmatory claim, identify a genuinely fresh confirmation population where possible.

Before running expensive experiments, produce a split/provenance table showing:

* domains;
* codewords;
* prompt families;
* requests;
* sample counts;
* whether each item has previously influenced selection.

At least 20 independent examples per meaningful cell; use substantially larger populations for thesis-level claims whenever available.

The unit of independence is generally domain/request/codeword as appropriate — NOT individual prompt rows when rows share a domain.

No ASR-based exclusion.

No post-hoc filtering.

Attrition must be mechanical and declared in advance.

All denominators must be reported.

## 20. POWER BEFORE GPU

Before a confirmatory run:

compute whether the planned control family and sample size can actually resolve the preregistered criterion.

If the minimum attainable permutation/rank p-value is above the threshold, do not run an expensive "confirmatory" experiment and later call it a null.

Label it:

`CANNOT ANSWER / UNDERPOWERED`

and redesign it before GPU use.

We have already lost time to floor-limited tests.

Do not repeat that.

## 21. INDEPENDENT VERIFICATION

For every important positive OR negative result:

have a second analyser independently recompute the primary statistic without sharing the primary implementation.

At minimum verify:

* row counts;
* domain counts;
* hashes;
* pairing;
* positions;
* intervention masks;
* rank;
* norms;
* seed;
* baseline;
* effect;
* CI;
* p-value;
* control family.

Run mutation tests.

Examples:

* shuffle labels → signal should disappear;
* swap source/target → expected direction should change;
* neutral position → primary effect should weaken;
* random rank-k subspace → should follow null family;
* identity adapter → zero effect;
* replay saved parameters → identical or tolerance-matched result.

A pipeline that cannot fail its own positive control is not evidence.

## 22. SLURM / GPU RULES

Use SLURM for model-loading experiments.

Current project conventions should be recovered from the repository and existing scripts rather than guessed.

Expected infrastructure includes:

* account `gpu-research`;
* existing GPU partitions such as `killable` / `gpu-sharifm`;
* `cpu-killable` for heavy CPU analysis.

Use the established shared model/HF cache.

Use the already cached pinned model whenever possible.

Primary model remains the exact existing:
`Llama-3.1-8B-Instruct`
revision/config used by the CSI work.

Keep bf16 / attention implementation / tokenizer consistent with the existing experiments unless an experiment explicitly varies them.

Do not download another large model without a genuine need. If a new model download requires my approval or credentials, document it and continue everything else.

Maximum roughly 6 concurrent independent experimental GPU jobs unless cluster conditions or existing project rules are stricter.

Use arrays with a concurrency cap when appropriate.

However, do NOT create unnecessary simultaneous cold NFS model loads. Cold model loading has been a major runtime bottleneck.

When possible, batch/sequentially execute several compatible experiment arms inside one allocation after loading the model once.

Do not infer "job stalled" purely from elapsed time during model loading. Inspect the actual progress/log.

For expensive non-model analysis use CPU SLURM.

A SLURM job is NOT considered successful because `sacct` says COMPLETED.

Validate:

* log trailer;
* expected artifacts;
* row count;
* checksum/hash where relevant;
* explicit `DONE` marker.

## 23. ENGINEERING RULES

Reuse existing project code.

Reuse Heretic code/interfaces.

Do not write thousands of lines merely because it is possible.

Prefer one clean generic experiment engine over one script per condition.

But do not "generalize" working research code in a way that silently changes frozen behavior.

Every meaningful behavior change gets tests.

Before launching a large run:

24. unit test;
25. tiny synthetic test;
26. small real-data smoke test;
27. inspect outputs manually;
28. only then launch scale run.

Check GPU memory explicitly.

Offload frozen activations / analysis tensors to CPU where appropriate.

Do not retain unnecessary computation graphs.

## 24. AUTONOMOUS EXECUTION

Do NOT stop after writing the plan.

Implement it.

Do NOT ask me questions merely because there are multiple reasonable scientific choices.

Use the more comprehensive scientifically conservative choice, document it, and continue.

Only stop and ask me if progress is genuinely impossible without my intervention, e.g.:

* credentials unavailable;
* required data absent everywhere;
* paid API exhausted;
* genuinely new model download requiring approval;
* two mutually exclusive choices would irreversibly invalidate existing frozen work.

Even then:

document the blocker and continue every independent branch of work that is still possible.

Do not leave the whole sprint idle because one experiment is blocked.

## 25. PARALLELISM

Use subagents aggressively where their work is genuinely independent.

Good parallel branches include:

* Heretic source audit;
* current CSI artifact audit;
* position-aware hook implementation;
* scorer implementation;
* statistical/power design;
* SVD/subspace analysis;
* SLURM runner preparation;
* independent verification.

Do NOT allow two agents to modify the same files simultaneously.

Do NOT run competing duplicate GPU experiments.

Before launching new jobs, inspect active jobs and existing same-project Claude sessions.

## 26. REVIEW CADENCE

Use the existing project loop discipline.

Approximately every 30 minutes:

* inspect SLURM;
* inspect logs;
* inspect artifacts;
* identify failed/duplicate/stale jobs;
* update the append-only progress log;
* continue useful work.

Approximately every 4 hours of substantial progress:

perform a deeper adversarial review.

Ask:

* Are token positions actually correct?
* Is source/target pairing correct?
* Did we leak validation?
* Is the statistic using the right independence unit?
* Are ranks and control ranks matched?
* Are effects driven by update norm?
* Did we select after seeing the endpoint?
* Does a positive survive independent recomputation?
* Are we confusing representation with behavior again?
* Are we confusing sufficiency with necessity?
* Are we claiming "mechanism" when we only have a scorer?

Actively try to kill our own headline.

## 27. GIT

Check `git status` before modifying anything.

Do not overwrite unrelated user work.

Commit meaningful progress frequently.

Never run `git commit` in the background.

Push when the repository's credentials/session allow it.

If push fails because of the known credential/session issue, do NOT stop research. Keep clean local commits and document the push blocker.

Commit messages should identify the experiment/workstream.

Never retroactively rewrite artifacts from a completed read merely to make them match a corrected interpretation.

Create corrected artifacts and document the supersession.

## 28. OUTPUTS I EXPECT

At the end of this sprint I want:

1. An authoritative append-only `external_md` log.
2. A concise final research report answering:
   * What parts of Heretic were useful?
   * Did native ARA work?
   * Did position-aware ARA work?
   * What rank was required?
   * Did basket and button differ?
   * Which layers/components mattered?
   * Did head restriction preserve the effect?
   * What did the learned SVD/subspace look like?
   * Did it align with our existing causal circuit?
   * Did it generalize across codewords?
   * Did semantics change without behavior?
   * Which hypotheses were killed?
3. A machine-readable experiment registry containing:
   * config;
   * git SHA;
   * Heretic SHA;
   * dataset hash;
   * split;
   * SLURM job;
   * seed;
   * parameters;
   * artifact paths;
   * status;
   * verdict.
4. Tables/plots for:
   * rescue vs rank;
   * preservation vs rank;
   * basket vs button;
   * singular spectra;
   * cumulative SVD rescue;
   * layer/component search;
   * head-restricted vs full-module edits;
   * codeword frequency/probe quality vs required rank.
5. Independent verification reports for every headline.
6. A section titled:

   `WHAT WE CAN DEFEND`

   and another:

   `WHAT WE MUST NOT SAY`

7. A short update suitable for a meeting with Matan/Mahmood explaining only the scientifically defensible results.

8. PRIORITY ORDER

Do not fan out into dozens of weak experiments.

The priority is:

* P0 — verify Heretic implementation and reproduce it.
* P1 — implement correct arbitrary-position ARA.
* P2 — basket vs button rank sweep with strong rank-matched controls.
* P3 — inspect/SVD the learned operator and distill a minimal causal subspace.
* P4 — compare learned operator with existing layer/head/cell circuit.
* P5 — quantify the "better probe vs different state" explanation across additional codewords.
* P6 — scale to fresh codewords / confirmation data.
* P7 — only after all of the above, perform downstream behavioral linking.

If P2 produces a strong, replicated dimensionality result, spend the compute necessary to make that claim thesis/paper quality before exploring flashy side directions.

9. THE RESULT WE ARE ACTUALLY LOOKING FOR

Do not optimize for "Heretic made the model more compliant."

That is not the scientific contribution.

The interesting result would look more like:

> A rank-1 intervention is sufficient for one Doublespeak codeword but not another. Direct operator optimization reveals that the second codeword requires a higher-dimensional transformation concentrated in the same depth/head circuit identified independently by causal attention interventions. Truncating the learned operator identifies the minimal sufficient semantic-installation subspace.

OR:

> Despite arbitrary-rank optimization, button remains resistant, falsifying the hypothesis that the codeword dissociation is merely dimensionality.

OR:

> ARA finds a low-dimensional operator for both codewords, showing that our previous button rank-1 null reflected the particular axis construction rather than high-dimensional mediation.

All of those are interesting.

Let the experiment decide.

---

Implement this plan now.

Write the plan and progress continuously to the new `external_md` file.

Do not wait for responses from me unless you are genuinely blocked.

Use GPU compute when the experiment deserves it.

Use enough data for claims we can defend.

Reuse existing code and Heretic rather than rebuilding infrastructure unnecessarily.

Use subagents for independent work.

Continuously audit yourself for bugs, leakage, wrong token positions, wrong populations, mismatched controls, and overclaiming.

Commit meaningful progress frequently and push when possible.

Run operational reviews approximately every 30 minutes and deep adversarial code/output reviews approximately every 4 hours.

Our goal is not to obtain a positive result.

Our goal is to determine whether Heretic's arbitrary-rank operator optimization exposes the missing causal representation/computation behind the Doublespeak semantic-installation mechanism, with enough rigor that we can defend the result later.
