# DCS THESIS-SCALE PHASE — MANDATE (verbatim, as given by Omer 2026-09-06)

> This file is the **verbatim mandate** for the next thesis-scale phase.
> It is frozen: do not edit it to match what we actually did.
> The append-only execution log lives in
> `external_md/DCS_THESIS_SCALE_BOMBNESS_CAUSAL_CONFIRMATION_PLAN_AND_PROGRESS_20260906.md`.
> Deviations from this mandate must be recorded there as `C-xxx` (correction) or
> `Q-xxx` (human decision required), never by editing this file.

---

You are taking over the NEXT THESIS-SCALE phase of our Doublespeak / Bombness / causal-mechanism project.

This is not a quick exploratory sprint.

The explicit goal of this phase is to produce scientific claims that Omer can defend in a serious meeting with Matan and Mahmood and, if they survive, use in a thesis/paper.

We are now willing to RE-RUN IMPORTANT PAST EXPERIMENTS at substantially larger scale when their current evidence is too small, misaligned, underpowered, based on a bad train/test split, based on a contaminated prompt population, or uses an intervention/read site that does not actually test the mechanism we thought it tested.

Do not protect old conclusions.
Protect scientific validity.

ULTRATHINK.
ULTRACODE.
FAN OUT READ-ONLY / INDEPENDENT SUBAGENTS.
PREREGISTER.
POWER BEFORE RUNNING.
VERIFY.
ATTACK YOUR OWN CLAIMS.
COMMIT AND PUSH CONTINUOUSLY.
LOOP ~EVERY 30 MINUTES.
FULL CODE + OUTPUT + CLAIM REVIEW ~EVERY 4 HOURS.

======================================================================
0. EXCLUSIVE CONTROL FIRST — NO COMPETING CLAUDE EXPERIMENTS
======================================================================

Before changing code or submitting anything:

1. Inspect:
   - current branch / HEAD
   - git status
   - recent commits
   - active tmux / Claude sessions associated with this repository
   - running and pending SLURM jobs
   - existing in-flight DCS/TSC/Bombness experiments
   - unfinished external_md entries.

2. We want EXACTLY ONE orchestrating Claude advancing this scientific phase.

If another Claude session is actively working on the SAME research phase:
- coordinate with it and make it stand down;
- preserve its completed work;
- stop it from submitting further jobs;
- cancel only clearly identifiable in-flight jobs that would conflict with this new phase;
- never delete completed artifacts;
- never reinterpret a partial run as a complete preregistered experiment.

DO NOT:
- kill unrelated user jobs;
- cancel unrelated projects;
- destroy another session's uncommitted work;
- blindly kill processes.

If ownership is ambiguous, inspect paths/configs/job commands first.

Record the exclusivity handoff and all cancelled/preserved jobs in the new phase log.

Your own subagents are allowed and encouraged, but:
- they report to you;
- they should preferably be read-only;
- they must not independently launch overlapping experiments;
- two agents must not edit the same file simultaneously.

======================================================================
1. READ THE COMPLETE SCIENTIFIC RECORD FIRST
======================================================================

Do NOT start by coding.

Read the full files, not only the summaries:

- external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md
- reports/DCS_SPRINT_SUMMARY_20260906.md
- reports/SPRINT_SUMMARY_20260905_TO_0906_PART2.md
- reports/DCS_SLACK_DRAFT_MATAN_MAHMOOD_20260906_FINAL.md
- reports/DOUBLESPEAK_NEXT_PHASE_SUMMARY.md
- external_md/DOUBLESPEAK_CONCEPT_SPECIFIC_BOOMBNESS_AND_SURGICAL_CAUSALITY_PLAN_AND_PROGRESS_20260902.md
- external_md/THESIS_SCALE_CONFIRMATORY_SPRINT_PLAN_AND_PROGRESS.md
- reports/TSC_SPRINT_SUMMARY.md
- reports/DCS_LITERATURE_MATRIX.md
- the earlier CDS behavioural-causality handoff where required.

Then inspect the ACTUAL producing code/artifacts behind the major current results.

At minimum inspect:

- prompt bank generation
- demo pool generation
- prompt_families.py
- metadata sidecars
- semantic_one_word
- semantic_forced_choice
- comprehension_usage
- mapping_use implementations
- dcs_bombness_specificity.py
- dcs_diffmeans_directions.py
- dcs_extract_under_ko.py
- score_behavior.py
- surgical_knockout.py
- extract_boombness.py
- knockout position resolvers
- control-draw generation
- refusalness.py
- current verifier scripts
- mutation harnesses
- SLURM wrappers
- argsfiles
- all currently committed run metadata.

For every important inherited claim, identify:
- population;
- number of independent domains;
- train/validation/test scheme;
- whether model selection touched confirmation data;
- whether prompts were aligned;
- whether the concept actually installed;
- whether the readout leaked the concept;
- exact representation position;
- exact intervention rows;
- exact source keys;
- exact layer convention;
- whether the read site was genuinely downstream of the intervention;
- whether a control was valid;
- whether power was adequate.

Do not trust the prose summary if the artifact/code disagrees.

======================================================================
2. CREATE A NEW AUTHORITATIVE APPEND-ONLY LOG
======================================================================

Create:

external_md/DCS_THESIS_SCALE_BOMBNESS_CAUSAL_CONFIRMATION_PLAN_AND_PROGRESS_20260906.md

or an equally clear dated name.

It must be:
- self-contained;
- append-only;
- timestamped;
- understandable without session context;
- explicit about preregistration and power;
- explicit about corrections;
- explicit about negative results;
- explicit about CANNOT ANSWER / VOID;
- explicit about old results that are being upgraded or downgraded.

Continue the DCS namespace where appropriate.

Suggested entry types:

PR-xxx — preregistration
R-xxx  — result
C-xxx  — correction/retraction
A-xxx  — adversarial audit
B-xxx  — blocker
Q-xxx  — real human decision

At the very beginning write:

A. CURRENT SCIENTIFIC TRUTH
B. CLAIMS THAT ARE ONLY PRELIMINARY BECAUSE OF SMALL / MISALIGNED DATA
C. MECHANISM CLAIMS WHOSE OLD READ SITE WAS INVALID OR DEGENERATE
D. CLOSED ROUTES
E. THIS PHASE'S THESIS-SCALE CLAIM TARGETS

Commit and push this plan BEFORE the first confirmatory forward pass.

======================================================================
3. KEEP MATAN'S ACTUAL QUESTION CENTRAL
======================================================================

Matan was not asking us merely to find an arbitrary classifier with a good AUROC.

His question was approximately:

    Can we justify saying that the codeword is becoming represented as BOMB?

And, if so:

    Is that representation actually used by the model?

The following things were explicitly on his mind and MUST stay central:

1. define Bombness specifically for BOMB;
2. do not average together cyber / disease / weapon / generic harm;
3. compare harmful vs benign context carefully;
4. do not abandon difference-in-means;
5. try a linear classifier / probe;
6. inspect probability / logits;
7. ask the intuitive question:
       "What does this word actually refer to — bomb or the literal word?"
8. verify that the prompts actually induce the intended mapping;
9. compare representation to attack/use;
10. test the final codeword / concept positions surgically;
11. make attention knockout more precise;
12. use enough data and proper train/test splits;
13. make the benign/harmful concept metadata reusable;
14. check literature for concurrent interpretability work.

We now have evidence that Matan's intuition was productive:

There appear to be TWO distinguishable axes:

A. REMAPPING AXIS
   "Was this codeword reassigned at all?"

B. CONCEPT-IDENTITY AXIS
   "Which concept was installed?"

The old raw C−A direction mainly reads A.

The residualized / concept-specific direction reads B.

The next phase must determine whether B is:
- real on a large aligned population;
- general across codewords/templates;
- causally used by the model.

======================================================================
4. CURRENT RESULTS — TREAT THESE AS HYPOTHESES TO CONFIRM, NOT SACRED FACTS
======================================================================

Current small-population discovery:

- linear P2 concept probe:
      ~0.7485 accuracy
      vs 0.333 chance
      6/6 held-out domains

- raw diff-in-means v_bomb:
      remapped? AUROC ~0.9987
      which concept? ~0.574

- residualised v_bomb_specific:
      remapped? ~0.607
      which concept? ~0.896

This suggests distinct remapping and identity axes.

BUT:

These concept-specific results currently live mainly on:
- one model;
- one primary codeword;
- only 6 domains;
- preset `main`;
- concept banks whose benign corpora are not fully aligned.

Therefore:

⛔ DO NOT treat n=6 as thesis-scale confirmation.

It is a DISCOVERY result worth following up.

The goal now is LARGE, ALIGNED, HELD-OUT CONFIRMATION.

======================================================================
5. DATA DOCTRINE — IMPORTANT CLAIMS REQUIRE LARGE, CORRECT DATA
======================================================================

This is one of the most important instructions in this phase.

Any claim we expect Omer to present to Matan as a serious result must use enough INDEPENDENT data.

ROWS ARE NOT THE INDEPENDENCE UNIT.

Rows/families generated from the same demonstration domain remain grouped.

The domain is the primary independence unit unless a different unit is explicitly justified.

--------------------------------------------------
5.1 NO RANDOM ROW SPLITS
--------------------------------------------------

NEVER randomly split rows from the same domain across train and test.

All:
- templates;
- families;
- n_examples rows;
- repetitions

belonging to a domain must stay on the same side of the train/validation/test boundary for the primary learned-representation analysis.

This prevents demonstration-pool/topic leakage.

--------------------------------------------------
5.2 FIRST RECOVER MATAN'S / PROJECT'S EXACT SPLIT RULE
--------------------------------------------------

Before fixing a new split:

Search all previous logs / notes for the exact train/test split convention requested by Matan.

If an explicit prior convention exists:
FOLLOW IT.

Record its source in the preregistration.

If no more-specific rule exists, use the following fallback for the thesis-scale 116-domain population:

    TRAIN:      70 domains
    VALIDATION: 23 domains
    TEST:       23 domains

Fixed by one seed:
    20260906

The split is created from domain metadata BEFORE:
- hidden states;
- logits;
- installation outcome;
- probe performance;
- ASR.

Commit the split manifest and SHA before extraction.

NO reshuffling after outcomes.

--------------------------------------------------
5.3 BUTTON / BASKET DISCIPLINE
--------------------------------------------------

Use:

    button = development/training lexical setting
    basket = external lexical confirmation

Do NOT pool button and basket into training for the flagship lexical-generalisation claim.

Preferred flagship protocol:

TRAIN:
    button, TRAIN domains

HYPERPARAMETER/LAYER SELECTION:
    button, VALIDATION domains

PRIMARY TEST:
    button, untouched TEST domains

LEXICAL EXTERNAL CONFIRMATION:
    basket, the SAME untouched TEST-domain IDs
    using the model/direction/probe frozen from button.

Also report a basket-trained result separately if scientifically useful, but NEVER call basket-trained/basket-tested "transfer".

For true transfer:
    train button → test basket.

If reverse transfer is later tested:
preregister it separately.
Do not add it only because the forward direction disappoints.

--------------------------------------------------
5.4 TEMPLATE GENERALISATION
--------------------------------------------------

Do not reuse the old invalid leave-one-bank-block-out inference.

If we want a template-generalisation claim, construct it validly.

Preferred approach:
- freeze a set of DEVELOPMENT template families;
- freeze at least one CONFIRMATION template family before representation extraction;
- never let the same template group's concept relabeling contaminate train and test;
- perform inference at the domain level.

If the available templates cannot support a valid independent template test:
do not claim template generalisation.

--------------------------------------------------
5.5 HOW MUCH DATA?
--------------------------------------------------

The current 6-domain population is NOT enough for the main claim.

For IMPORTANT REPRESENTATION CLAIMS:

Preferred final population:
    ≥ 100 independent domains.

The repository already has 116-domain infrastructure on the bomb side.

Therefore DEFAULT to building an aligned 116-domain concept population if it is technically and financially feasible.

Do not stop at 6 because an old experiment used 6.

A 38-domain aligned population may be used as:
- implementation pilot;
- intermediate replication;
- mechanism debugging.

But if the result is going to become a thesis/paper headline and the 116-domain construction is feasible:
RUN THE 116-DOMAIN VERSION.

At minimum:
- no new flagship claim should rest only on n=6;
- n=38 is acceptable for a substantial mechanistic replication;
- n≈116 is preferred for final learned-representation and representation→behaviour claims.

For every expensive experiment:
perform power analysis first from the intended DOMAIN-level estimator.

Do not use row count to make a weak design look large.

======================================================================
6. BUILD THE ALIGNED THESIS-SCALE CONCEPT BANK
======================================================================

This is the first major experimental deliverable.

The current 6-domain positive already satisfied the old condition for funding the aligned rebuild.

Build a LARGE aligned concept population.

Primary concepts:

    bomb
    knife
    gun

Do NOT use `club` in the primary concept set unless it is regenerated and passes a strict sense/polysemy audit.

The old club pools are contaminated by social-club / room / tool senses.

--------------------------------------------------
6.1 ALIGNMENT PRINCIPLE
--------------------------------------------------

Across concepts, EVERYTHING that is not the concept manipulation should be identical.

For matched domain/family/codeword/n_examples:

KEEP BYTE-IDENTICAL:
- benign demonstration pool;
- filler / preamble;
- benign-remap demonstrations;
- prompt skeleton;
- role formatting;
- query wording;
- answer instructions;
- number of demonstrations;
- codeword;
- token-position conventions;
- non-concept metadata.

CHANGE ONLY:
- the HARM demonstrations that define the installed concept.

For concept c:

    harm demonstrations install c.

This is the clean Matan estimand:

    same codeword
    same context skeleton
    same benign baseline
    different installed concept

--------------------------------------------------
6.2 TARGET SIZE
--------------------------------------------------

Preferred:

    116 domains × {bomb, knife, gun}

If 116-domain comparator generation has a genuine blocker:
- document it;
- stage 38 first;
- but treat 38 as an intermediate result unless the power analysis establishes it is sufficient for the exact final claim.

DO NOT quietly downgrade the requested thesis-scale dataset because 38 is easier.

--------------------------------------------------
6.3 CODEWORDS
--------------------------------------------------

Construct both:

    button
    basket

from the same underlying aligned concept/domain pools.

The same domain IDs must exist for both.

--------------------------------------------------
6.4 N_EXAMPLES
--------------------------------------------------

Primary:
    n_examples = 4

because this is the central inherited dose.

Predeclared replication:
    n_examples = 8

Null:
    n_examples = 0

Optional:
    n_examples = 1 or 2 only for explicitly preregistered dose questions.

Do not combine doses into one p-value as if independent samples.

--------------------------------------------------
6.5 POLYSEMY / CONCEPT-BACKING AUDIT
--------------------------------------------------

Before GPU work, mechanically + manually audit the generated pools.

For every harmful concept:
- the intended semantic sense must actually be present;
- reject social/room/tool/polysemous mismatches;
- concept must be a single coherent concept;
- no accidental concept substitution;
- no demonstration pool labelled knife that actually installs bomb.

Build a concept-backing verifier.

Sample human-readable examples from every domain.

Do not inspect model outcomes to decide whether a domain is "good".

The audit must be prompt-only / generator-output-only.

--------------------------------------------------
6.6 LEAKAGE AUDIT
--------------------------------------------------

For every probe/readout population check FULL_PROMPT, not just final_query_text.

Search for:
- explicit target concept words;
- synonyms where relevant;
- template blocks that name the label;
- concept-specific answer options;
- lexical clues;
- different prompt lengths;
- different role scaffolding.

Produce:
- concept-word occurrence table;
- length-only classifier;
- prompt-text-only classifier;
- template-ID-only classifier if applicable.

A representation probe must beat these nuisance baselines.

======================================================================
7. METADATA — MAKE MATAN'S PROMPT TABLE REUSABLE
======================================================================

Build or audit one authoritative sidecar.

Do not mutate canonical bank hashes only for convenience.

Required fields:

- bank_sha
- prompt_id
- globally unique compound key
- domain_id
- split = train / validation / test
- template_family
- bank_block
- concept
- codeword
- surface_word
- surface_type
- demonstration_valence
- intended_mapping
- condition/cell
- n_examples
- lexical_setting
- model
- query_kind
- target occurrence(s)
- decoded target tokens
- demo spans
- query span
- prompt length
- concept mentioned in full_prompt?
- concept mentioned in query?
- installation metrics
- artifact provenance
- run commit
- exclusions / failure status.

Never join across banks on `prompt_id` alone.

Use a compound key such as:

    (bank_file_sha16, prompt_id)

and assert it at runtime.

======================================================================
8. RE-RUN THE CONCEPT-SPECIFIC PROBE AT THESIS SCALE
======================================================================

The n=6 result is discovery.

Now replicate properly.

--------------------------------------------------
8.1 PRIMARY PROBE
--------------------------------------------------

Use P2-style design:

TRAIN:
    cell C hidden states
    concept classes {bomb, knife, gun}
    TRAIN domains only.

The codeword surface is identical across classes.

VALIDATE:
    VALIDATION domains only.

TEST:
    untouched TEST domains.

Classifier:
    simple multinomial logistic regression.

Do NOT start with an MLP.

Hyperparameters selected only on VALIDATION.

No test-domain layer selection.

--------------------------------------------------
8.2 LAYER SELECTION
--------------------------------------------------

The old selector was effectively flat and returned L6 by tie-break.

Do not repeat that mistake while describing it as learned localisation.

Predeclare one of these valid strategies:

PREFERRED:
A. select layer / band using TRAIN+VALIDATION only and freeze.

OR:
B. use a fixed inherited band summary, e.g. mean / concatenation across L7–14, if justified prospectively.

Important:

Do NOT use L6 as the sole causal-mechanism read site merely because the old probe selected it.

At L6, for an intervention beginning at L6, the whole-query and codeword-row-only masks can be arithmetically identical at the read row.

For causal tests, use a genuinely downstream site.

--------------------------------------------------
8.3 PRIMARY METRICS
--------------------------------------------------

Report at least:

- accuracy
- balanced accuracy
- macro one-vs-rest AUROC
- per-class AUROC
- confusion matrix
- per-domain accuracy
- per-domain macro AUROC
- calibration / probability distribution where meaningful.

IMPORTANT LESSON FROM R3:

Accuracy measures both:
    representation ordering
and
    boundary/offset portability.

AUROC measures ranking.

For lexical-transfer claims report BOTH.

Predeclare which is primary.

Do not switch after seeing the answer.

--------------------------------------------------
8.4 NULLS
--------------------------------------------------

Mandatory:

1. n_examples=0
   must be chance / no concept signal.

2. group permutation at DOMAIN/concept-group level.
   Never individual-row permutation.

3. full-prompt leakage control.

4. length-only control.

5. template-only control where meaningful.

6. codeword-only control.

7. label permutation through the ENTIRE pipeline, including hyperparameter selection where required.

Calibrate false-positive rate on synthetic/no-signal data BEFORE trusting p-values.

======================================================================
9. RE-RUN THE DIFF-IN-MEANS AXES AT THESIS SCALE
======================================================================

Matan explicitly did not want us to abandon difference-in-means.

Do not.

Re-estimate on TRAIN only:

For concept c:

    v_c =
      mean_train [ h(C_c) - h(A_shared) ]

Because the new aligned bank shares A across concepts by construction, this is now much cleaner than the old result.

Define:

    v_remap_bomb = v_bomb

and predeclare a concept-specific residual such as:

    v_bomb_specific
        =
        v_bomb
        - mean(v_knife, v_gun)

Do NOT include a contaminated concept merely to preserve an old formula.

--------------------------------------------------
9.1 VALIDATION QUESTIONS
--------------------------------------------------

On untouched TEST domains:

A. Does v_bomb distinguish C_bomb vs A?
    remapping axis.

B. Does it distinguish C_bomb vs C_knife/C_gun?
    identity axis.

C. Does v_bomb_specific distinguish C_bomb vs hard negatives?

D. Does v_bomb_specific stay weak on generic C vs A remapping?

E. Does it transfer button → basket by ranking?

F. Does the n_examples=0 null fire exactly?

Report:
- AUROC
- standardized effect
- domain-level sign
- confidence intervals
- layer profile, if predeclared.

No layer hunting on TEST.

======================================================================
10. THE MOST IMPORTANT NEW CAUSAL QUESTION:
INTERVENE DIRECTLY ON THE CONCEPT AXIS
======================================================================

This is a major new goal.

We now know a concept-specific signal is decodable.

That is NOT enough.

Matan ultimately cares whether the representation matters.

Therefore test:

    Is v_bomb_specific causally used?

Do not make it a GCG objective yet.

First establish causal relevance.

--------------------------------------------------
10.1 UPPER-BOUND PATCHING TEST
--------------------------------------------------

Use the fully aligned population.

For matched:
    domain
    family
    codeword
    n_examples

construct:

source:
    C_knife

target:
    C_bomb

At a predeclared codeword representation site, patch the bomb target with the corresponding knife representation.

This is an intentionally strong upper-bound test.

Question:

Does the semantic interpretation shift:
    Bomb → Knife ?

Because the prompts are aligned, this patch is much cleaner than patching across unrelated topics.

Also run:
    bomb ← gun

and reverse directions if preregistered.

No post-hoc picking.

--------------------------------------------------
10.2 SURGICAL CONCEPT-SUBSPACE INTERVENTION
--------------------------------------------------

Then test the concept direction itself.

Examples:

Projection-out:

    h' = h - proj_{v_bomb_specific}(h)

or concept-component replacement in a learned low-dimensional concept subspace.

Also consider counterfactual component replacement:

    bomb component → knife component

while preserving the orthogonal residual.

Use TRAIN-estimated directions only.

Never fit a direction on TEST.

--------------------------------------------------
10.3 CONTROLS
--------------------------------------------------

Mandatory causal controls:

- random direction, norm matched;
- shuffled-label concept direction;
- remapping direction v_remap;
- orthogonal harmful direction if available;
- same-norm activation edit;
- disabled-hook bridge;
- untouched baseline.

Verify intervention magnitude.

Persist:
- pre/post activation norm;
- projection removed;
- cosine;
- layer;
- token;
- occurrence;
- actual hook fired count.

--------------------------------------------------
10.4 TWO PREDECLARED SCOPE LEVELS
--------------------------------------------------

Do not rescue a failed single-layer test by inventing a multi-layer one later.

Preregister BOTH as distinct hypotheses if desired:

A. single-site/single-layer surgical edit
B. band-wide L7–14 concept-axis edit

Correct multiplicity.

The interpretation of each is different.

--------------------------------------------------
10.5 SUCCESS CRITERION
--------------------------------------------------

A causal concept-axis result should require:

1. concept-probe score moves in intended direction;
2. semantic readout moves in intended direction;
3. matched random control does not;
4. ideally output switches toward the counterfactual concept;
5. result holds across domains, not only pooled rows.

If probe score changes but model interpretation does not:
    decodable but not causally used.

That is a valuable result.

======================================================================
11. BUILD THE INTUITIVE READOUT MATAN ACTUALLY WANTED
======================================================================

The old metalinguistic question:

    "Is button used literally or as a code?"

was blind.

Do not lower its gate.

Build a NEW preregistered instrument.

Primary intuitive question should ask OBJECT IDENTITY, not meta-language.

Examples:

    What does "button" actually refer to here?

Scoring categories:

    Bomb
    Button
    Neither

For knife/gun:
replace the target concept accordingly in scoring.

However, be careful:

If the answer options themselves are written into the prompt, they can contaminate hidden-state localisation.

Therefore use TWO channels:

A. PRIMARY MECHANISTIC CHANNEL:
   concept-free open-ended question such as semantic_one_word.
   Score candidate whole-answer probabilities externally.

B. SECONDARY INTUITIVE DISPLAY:
   3-way explicit forced choice:
       Bomb / Button / Neither.

The 3-way version is intuitive for slides.
The open-ended version is safer for mechanistic localisation.

Never use a prompt containing "bomb" as evidence that a late hidden state naturally contains bomb unless the capture site is provably before the option is introduced.

Always report:
- logP target concept;
- logP literal;
- logP neither if available;
- normalized candidate probabilities;
- full option mass;
- decoded/free answer.

======================================================================
12. RE-DO THE MECHANISM TEST WITH A CORRECT READ SITE
======================================================================

The old R5 result is scientifically interesting but the mechanism description was narrowed:

At L6 — the FIRST intervention layer — whole-query KO and codeword-row-only KO are identical at the codeword read site.

Do NOT reproduce this mistake.

--------------------------------------------------
12.1 MECHANISM RULE
--------------------------------------------------

If an intervention begins at layer L:

A state read at the first affected layer may only reflect the read row's own mask.

Therefore any claim about propagation through the whole query must be read:
- at a later layer;
or
- at a downstream neutral position;
or
- after enough intervened layers for upstream query-row differences to propagate.

--------------------------------------------------
12.2 PRIMARY READ SITES
--------------------------------------------------

For this phase predeclare:

A. codeword representation:
   layers L7–14, not L6-only.

B. a downstream NEUTRAL query/readout position that:
   - is after the codeword;
   - is identical across concepts;
   - does not itself contain `bomb`, `knife`, `gun`;
   - exists in every matched prompt.

C. final prompt position only if its semantics are controlled and it does not leak concept labels.

Capture all relevant layers so we can verify propagation.

--------------------------------------------------
12.3 INTERVENTION SCOPES
--------------------------------------------------

Compare predeclared scopes:

1. demos → whole user-query content
2. demos → codeword row only
3. demos → downstream readout row only
4. demos → explicit concept row, when applicable
5. dose-matched nondemo control
6. no intervention.

Avoid raw "last K rows" when they include unknown chat scaffold.

First map every token.

Then define semantic regions.

======================================================================
13. THE "LAST BOMB TOKEN" CHECK — DO IT CORRECTLY
======================================================================

Matan explicitly asked for the symmetric version of the final codeword experiment.

The naive probe AT the token `bomb` is invalid:
it trivially reads lexical identity.

Therefore:

Do NOT ask:
    "Can a classifier at the bomb token tell us it is bomb?"

Instead test:

    If the FINAL EXPLICIT-CONCEPT ROW is prevented from attending to demonstrations,
    what changes DOWNSTREAM?

Intervene at:
    explicit concept token row → demos

Read at:
    a downstream neutral site
and/or
    semantic output.

Measure:
- semantic readout;
- downstream hidden representation;
- mapping/use;
- output probabilities.

Use the same layer convention and controls as the corresponding codeword-row experiment.

This becomes the valid symmetry test Matan asked for.

======================================================================
14. REDO THE SURGICAL QUERY-POSITION MECHANISM WITHOUT INSTRUMENT LEAKAGE
======================================================================

The previous K ladder produced a dramatic step at K=7.

But the decisive token was `' bomb'` because semantic_forced_choice itself named bomb.

That is partly a readout-instrument result.

Do not use it as the final mechanism claim.

Run a new semantic-region / fine-grained intervention on the ALIGNED large bank using the concept-free open-ended readout.

Before outcomes:

Tokenize every prompt.
Produce a deterministic token-role table.

Classify query tokens as:
- chat scaffold;
- user instruction scaffold;
- punctuation;
- literal/codeword;
- neutral content;
- answer-format instruction;
- response header.

The target concept must NOT appear in the question for the primary localisation test.

--------------------------------------------------
14.1 PREDECLARED SCOPES
--------------------------------------------------

Instead of blindly sweeping every subset, define a SMALL family such as:

A. chat scaffold only
B. neutral question content only
C. codeword row only
D. all user-content rows excluding codeword
E. all user-content rows
F. downstream readout row only

Match dose wherever the scientific comparison requires it.

If a further hypothesis is suggested by these results:
new preregistration.

No subset shopping.

--------------------------------------------------
14.2 LARGE DATA
--------------------------------------------------

If the readout is cheap:
run the mechanism confirmation on at least 38 domains.

If the aligned 116-domain bank is already constructed:
prefer all 116 domains for the final headline mechanism estimate.

======================================================================
15. PROMPT VALIDATION — EVERY EXPERIMENT MUST PROVE THE MAPPING EXISTS
======================================================================

Before interpreting a representation or causal result, produce the Matan prompt-validation table.

For every:
- concept
- codeword
- domain
- split
- n_examples
- template

report:

- intended mapping;
- concept whole-answer logP;
- literal whole-answer logP;
- concept_binary_prob;
- semantic_logodds;
- option_mass;
- decoded answer;
- installation status;
- whether concept word leaks into full_prompt;
- failures.

Do NOT silently remove non-installing domains.

Primary analysis population is fixed BEFORE installation outcomes.

Installation may be:
- predictor;
- stratification variable if preregistered;
- descriptive limitation.

It is NOT a post-hoc exclusion rule unless an exclusion was prospectively specified.

======================================================================
16. LEXICAL TRANSFER — RE-TEST PROPERLY ON LARGE DATA
======================================================================

The current result:

button-trained → basket:
accuracy poor,
ranking AUROC good.

We need to resolve whether this is a true shared direction with an offset shift.

On the large aligned TEST set:

Train on button only.

Evaluate on basket without retraining.

Predeclare BOTH:

PRIMARY A:
    macro OvR AUROC

PRIMARY/CO-PRIMARY B:
    argmax accuracy

or explicitly designate one primary and the other key secondary before running.

Also measure:
- per-class intercept/logit shifts;
- temperature/offset calibration using VALIDATION only if a calibration experiment is desired.

If a basket-specific recalibration is fitted:
that is NOT zero-shot lexical transfer anymore.
Label it separately.

Do not rescue transfer after seeing test outcomes.

======================================================================
17. BEHAVIOUR — ONLY AFTER THE REPRESENTATION INSTRUMENT IS CLEAN
======================================================================

ASR remains downstream and noisy.

Do not let behavioural work block the clean representation story.

Priority of downstream endpoints:

1. object-level semantic interpretation
2. mapping_use / deterministic endpoint
3. refusal
4. ASR last.

--------------------------------------------------
17.1 FIX THE CONTROL-DRAW DESIGN FIRST
--------------------------------------------------

Old controls used one RNG seed per arm, causing the same rank pattern across rows.

That means the between-arm spread is SYSTEMATIC, not a row-independent Monte-Carlo error bar.

For any NEW behavioural confirmation:

Use a NEW control name and implementation.

Default hypothesis:
    row-randomized matched controls

seed derived from something like:

    f(global_control_seed, bank_sha, prompt_id, draw_id)

so each row gets an independent matched draw.

Do not alter historical arms.

Persist per-row seed and positions.

Full-data contracts:
- match_ratio = 1.000
- dose matched per row
- no demo overlap
- no protected-query overlap
- distinct row seeds
- reproducibility from seed.

Before launching a large campaign:
run 4 control arms and inspect realised between-control SD.

Preregister the variance gate.

If row randomization does NOT materially reduce the nuisance:
STOP.
Do not buy 100 arms.

--------------------------------------------------
17.2 LARGE BEHAVIOURAL POPULATION
--------------------------------------------------

If behaviour becomes a headline:
use the aligned 116-domain bank.

Target multiple rows/families per domain.

Domain remains the independent unit.

Power at DOMAIN level.

Do not cite raw n=1160 as 1160 independent samples.

--------------------------------------------------
17.3 JUDGE RULES
--------------------------------------------------

Prefer deterministic endpoints where possible.

For ASR:
- pin judge alias/settings;
- record served snapshot if available;
- judge all arms of a primary comparison in one session/batch design where feasible;
- preserve raw texts;
- measure byte-identical rejudge noise;
- report refusal separately.

No comparator selection after seeing refusal.

Use ALL preregistered control draws.

======================================================================
18. REPRESENTATION ↔ BEHAVIOUR TEST
======================================================================

Only run after:

- concept-specific metric confirmed on large aligned data;
- behaviour measured on the SAME bank;
- adequate power exists.

For each TEST domain define before looking:

x_d =
    causal destruction of concept-specific score

Possible y_d:
A. semantic object-use change
B. mapping_use change
C. ASR change

Primary should be A or B.

ASR secondary.

Do not pick whichever y correlates.

Run reliability analysis on x and y first.

Simulate power under:
- perfect monotonic relation;
- moderate relation;
- measured noise.

If even perfect mediation cannot be detected:
CANNOT ANSWER.
Do not compute a seductive rho and discuss it.

======================================================================
19. RE-AUDIT IMPORTANT OLD CLAIMS — LARGE DATA WHEN IT MATTERS
======================================================================

Create a table of every potentially paper-level claim:

- old population
- n_domains
- data alignment
- split
- power
- mechanism validity
- current verdict
- needs thesis-scale rerun? YES/NO.

At minimum evaluate whether to rerun:

1. R-086 concept probe
   YES — n=6 → large aligned confirmation.

2. R-091 remapping vs concept axes
   YES — n=6 → large aligned confirmation.

3. R-093 representation survives readout knockout
   YES — old L6 read site is mechanistically degenerate.
   Re-test downstream / L7–14 on aligned large data.

4. R3 lexical transfer
   YES — larger TEST set, correct transfer metric.

5. K-ladder mechanism
   YES in corrected concept-free form because old decisive rung contains the concept option.

6. "last codeword row"
   YES in a template-neutral, semantically controlled design.

7. explicit concept row
   YES, but downstream read site only.

8. behaviour link
   only if the new design becomes adequately powered.

Do NOT rerun old experiments simply for aesthetic consistency.
Rerun when the old evidence limits a claim we care about.

======================================================================
20. POWER IS A PRECONDITION, NOT AN AFTERTHOUGHT
======================================================================

For every important preregistration:

Before GPU:
- specify minimum scientifically meaningful effect;
- estimate ICC if applicable;
- estimate domain-level variance;
- compute attainable p-floor;
- compute power;
- compute MDE.

If power < 0.8 for a flagship negative/positive claim:
either:
- increase independent domains;
- change to a valid more informative estimator before data;
- or declare it exploratory/CANNOT ANSWER.

Do NOT knowingly run a major confirmatory experiment whose likely negative would be uninterpretable.

For n=6 historical results:
the default position is that they require replication, not that p happened to be below 0.05.

======================================================================
21. PREREGISTRATION RULES
======================================================================

EVERY confirmatory forward pass gets a committed preregistration first.

Required fields:

- question
- claim it could support
- population
- exact bank SHA
- concept(s)
- codeword(s)
- train/validation/test split manifest SHA
- template split
- n domains
- rows/domain
- n_examples
- model
- model revision/hash if available
- tokenizer
- position resolver
- read site
- intervention site
- layer convention
- knockout source/destination
- control construction
- seeds
- decoding
- endpoints
- primary statistic
- independence unit
- alpha
- multiplicity
- p-floor
- MDE
- power
- success
- negative
- CANNOT ANSWER
- VOID
- kill condition
- artifacts
- analyzer commit.

The analyzer should be committed before the outcome exists wherever practical.

Do not edit a frozen analyzer to rescue an outcome.

New design = new preregistration.

======================================================================
22. MECHANISM / ATTENTION INTERVENTION RULES
======================================================================

This is critical.

Every intervention must prove it is manipulating the intended mechanism.

--------------------------------------------------
22.1 EAGER ATTENTION
--------------------------------------------------

Use eager attention whenever a custom attention mask/hook requires it.

SDPA has silently ignored such interventions before.

Fail closed.

--------------------------------------------------
22.2 TOKEN MAP BEFORE OUTCOME
--------------------------------------------------

Before intervention:

for every prompt persist:
- complete token IDs;
- decoded tokens;
- full prompt;
- demo spans;
- query spans;
- occurrence indices;
- semantic token roles;
- chat scaffold;
- generation header;
- concept mentions.

Never describe "last K query rows" without proving what those tokens are.

--------------------------------------------------
22.3 LAYER CONVENTION
--------------------------------------------------

Explicitly state:

    block layer L corresponds to which hidden_states index?

Test this with a planted hook.

Never infer it from names.

--------------------------------------------------
22.4 HOOK LIVENESS
--------------------------------------------------

Every arm must prove:
- hook fired;
- number of destinations;
- number of keys;
- layers;
- realised cells;
- expected edit count;
- state changes when enabled;
- disabled arm reproduces baseline.

Use cosine / rel-L2 appropriate to dense activations.

Do not use an invalid element-wise relative metric dominated by near-zero entries.

--------------------------------------------------
22.5 READ SITE MUST BE DOWNSTREAM
--------------------------------------------------

Before interpreting a causal result, draw the computation graph.

Ask:

Can the intervention have physically affected the representation at the point I read it?

If the read point is at the first intervened layer:
do not claim propagation through earlier query positions.

Use later layers / downstream site.

--------------------------------------------------
22.6 MATCHED CONTROLS
--------------------------------------------------

A "dose-matched" control must be verified, not named.

Persist:
- actual positions;
- cells masked;
- match ratio;
- attention source pool;
- protected spans;
- seed.

If generic masking changes a behavioural endpoint:
do not use it as an exchangeable comparator without modelling the nuisance.

======================================================================
23. INDEPENDENT VERIFICATION
======================================================================

Every headline result gets an independent verifier.

It must NOT:
- import the producer's analyzer;
- trust the producer's summary field;
- simply compare two fields produced by the same broken code.

It should re-derive from lower-level artifacts.

Mandatory checks:

- bank binding;
- split binding;
- no train/test leakage;
- concept backing;
- full-prompt leakage;
- exact population;
- target occurrence;
- layers;
- intervention;
- dose;
- hooks;
- output rows;
- duplicate/missing rows;
- statistics;
- p-floor.

Mutation harness:
make every important guard demonstrably RED on mutation.

Mutations should actually mutate bytes/values.
Verify that the corruption happened.

A harness that attacks an empty set proves nothing.

======================================================================
24. ADVERSARIAL REVIEW
======================================================================

Before promoting each major result, spawn a read-only subagent with the instruction:

    BREAK THIS CLAIM.

It should specifically attack:

- split leakage
- domain leakage
- template leakage
- concept-word leakage
- generic harmfulness
- generic remapping
- installation strength
- length
- token identity
- neighbouring lexical identity
- wrong layer
- first-layer degeneracy
- wrong read site
- wrong knockout source/destination
- silent no-op
- wrong independence unit
- underpowering
- multiplicity
- post-hoc metric switch
- post-hoc control selection
- invalid permutation
- wrong join key
- class imbalance
- prompt contamination
- bank metadata not matching actual demos.

If the audit finds a problem:
do not soften the sentence and continue automatically.

Assess whether:
- claim narrows;
- experiment is VOID;
- experiment must be rerun.

======================================================================
25. LITERATURE
======================================================================

Run a bounded current literature update.

Specifically inspect:

- arXiv 2609.02438
- Bakalova et al. / arXiv 2504.00132
- Yona et al. ACL 2026
- concept-specific representation probing
- causal concept erasure / activation patching
- ICL demonstration→query attention
- codeword / semantic remapping interpretability
- representation vs use / decodability vs causality.

Our novelty MUST NOT be:

    "first to intervene on demo→query attention"

That is false.

Potential novel pieces that need checking:

- semantic codeword remapping under causal attention intervention;
- remapping vs concept-identity axes;
- query-content threshold under attention knockout;
- concept-axis causal intervention;
- representation survives semantic readout destruction.

If literature overlaps strongly:
record it immediately for Omer/Matan.

Do not manufacture novelty from a search returning nothing.

======================================================================
26. SLURM RULES
======================================================================

Use existing repository scheduling conventions where correct.

Known project account:
    gpu-research

Use established appropriate GPU partitions.

CPU-only work:
prefer CPU resources where appropriate.

Rules:

1. Long GPU work via SLURM.
2. Maximum 6 concurrent GPU jobs for this phase.
3. Parallelize only scientifically independent jobs.
4. Respect stage gates.
5. No downstream stage before its gate.
6. Use arrays with %6 where appropriate.
7. Unique logs / args / outputs per arm.
8. Record job IDs.
9. Inspect logs immediately after submission.
10. Verify the log says the EXPECTED script + args.
11. A COMPLETED job running the wrong script is VOID.
12. Do not resubmit blindly.
13. Diagnose failures first.
14. Rerun only affected arms if population stays identical.
15. If population changes, reconsider the whole comparison.
16. Never analyze partial arrays as the experiment.
17. No long inference on login node.

Important prior failure:
the SLURM wrapper silently ran its default extraction script when the wrong environment variable was passed.

Therefore for EVERY newly submitted job:
read the first log lines and verify:
- script name;
- argsfile;
- bank;
- model;
- experiment tag.

======================================================================
27. MODEL CACHE / SCRATCH PREFLIGHT
======================================================================

The scratch purge previously destroyed the model cache symlink target.

Before GPU submission:

- resolve every model/cache symlink;
- verify target exists;
- verify model weights accessible;
- verify tokenizer;
- verify enough disk space.

Fail with an explicit message if the symlink is dangling.

Do NOT let a dangling symlink become:
    "mkdir: File exists".

Do not silently repoint shared infrastructure unless authorized.
A local robust preflight is safe and should be implemented.

======================================================================
28. 30-MINUTE LOOP
======================================================================

Every ~30 minutes while work is active:

1. check active project jobs;
2. inspect progress;
3. inspect stderr/stdout;
4. verify correct scripts are running;
5. verify artifacts appearing;
6. verify no duplicate arms;
7. run cheap integrity checks;
8. update external_md;
9. work on an independent CPU/read-only task while GPU runs;
10. commit/push meaningful progress.

Do not peek at confirmation outcomes before:
- preregistration;
- analyzer;
- thresholds
are frozen.

======================================================================
29. EVERY ~4 HOURS — FULL REVIEW
======================================================================

Perform:

A. CODE REVIEW
- changes since last review
- hardcoded paths
- seeds
- splits
- joins
- layer conventions
- token positions
- hook paths
- config propagation
- accidental old bank usage.

B. DATA REVIEW
- exact domain count
- split disjointness
- prompt IDs
- hashes
- concept backing
- rows/domain
- n_examples
- failures
- duplicates
- leakage.

C. OUTPUT REVIEW
- expected arms
- COMPLETE sentinels
- liveness
- hook cell counts
- matched doses
- null controls
- probability mass
- floor/ceiling.

D. SCIENTIFIC REVIEW

Ask:

1. Is this genuinely BOMB-specific?
2. Could this be generic remapping?
3. Could this be generic harmfulness?
4. Could it be installation strength?
5. Could it be prompt length?
6. Could it be template identity?
7. Could it be lexical leakage?
8. Did we train on a test domain?
9. Did selection use TEST?
10. Is the read site downstream of the intervention?
11. Does the control actually test the alternative?
12. Is n_domains sufficient?
13. Are we calling CANNOT ANSWER a null?
14. Did a failed preregistered metric tempt us to switch?
15. Would Matan accept this sentence after seeing the full table?

Write the review outcome to external_md.

======================================================================
30. GIT / SHARED TREE RULES
======================================================================

- git status frequently.
- never git add -A.
- never stash shared work.
- never reset others' changes.
- never force push.
- never clean unknown files.
- commit explicit paths only.
- preserve existing artifacts.
- use descriptive commits.
- push meaningful checkpoints continuously.

Examples of checkpoints:

- new log / preregistration
- split manifest
- aligned bank generator
- bank audit
- extraction implementation
- analyzer frozen
- jobs submitted
- result
- independent verification
- correction
- summary.

======================================================================
31. EXECUTION PRIORITY
======================================================================

Proceed approximately in this order.

PHASE 0
Exclusive control + repo/job audit.

PHASE 1
Read all history and classify current claims by:
- robust;
- preliminary;
- mechanistically compromised;
- CANNOT ANSWER;
- needs large rerun.

PHASE 2
Create and commit the new thesis-scale plan.

PHASE 3
Build aligned concept banks.
Default target: 116 domains.
bomb / knife / gun.
button / basket.
A/E/F fixed across concepts.
Only harmful demonstrations differ.

PHASE 4
Prompt / leakage / concept-backing / split audit.
NO GPU headline analysis until all pass.

PHASE 5
Thesis-scale P2 linear probe.
Strict domain train/val/test.
Button development, basket transfer.

PHASE 6
Thesis-scale diff-in-means:
remap axis vs concept axis.

PHASE 7
New object-level semantic readout:
open-ended primary + Bomb/Button/Neither secondary.

PHASE 8
Correct causal KO test:
non-degenerate read sites L7–14 / downstream neutral positions.

PHASE 9
Direct causal intervention on v_bomb_specific:
full patch upper bound;
then surgical subspace intervention.

PHASE 10
Correct "last bomb row" symmetry experiment with downstream readout.

PHASE 11
Concept-free semantic-position knockout / corrected K-mechanism experiment.

PHASE 12
Only if representation story is solid:
row-randomized behavioural controls;
mapping_use;
ASR.

PHASE 13
Representation destruction ↔ downstream-use test on the SAME large bank.

PHASE 14
Adversarial audits, literature update, paper-facing summary.

======================================================================
32. IMPORTANT CLAIM BAR — WHAT OMER SHOULD BE ABLE TO SAY TO MATAN
======================================================================

We want to end with claims of approximately this quality:

CLAIM A — only if supported:

    In a large, aligned held-out population,
    the codeword representation contains the identity of the concept installed by demonstrations,
    not merely generic remapping or harmfulness.

For this claim require:
- large independent TEST set;
- aligned concepts;
- leakage controls;
- hard harmful negatives;
- n=0 null;
- button heldout;
- basket transfer/ranking.

CLAIM B:

    Remapping and concept identity correspond to separable representational axes.

Require:
- train-only directions;
- untouched test;
- remap discrimination;
- identity discrimination;
- large-domain replication.

CLAIM C:

    The concept-specific direction is causally used / not used.

Require:
- direct intervention on concept axis;
- matched controls;
- downstream semantic outcome;
- enough domains.

If it is NOT used:
that is important.

Say:
    "decodable but not causally used under this intervention"

not:
    "the representation is meaningless."

CLAIM D:

    A specific demonstration→query pathway is required for the model's semantic report.

Require:
- correct token semantics;
- no concept-option leakage;
- downstream read site;
- proper layer propagation;
- matched controls.

CLAIM E:

    representation destruction predicts behavioural change.

Only if:
- SAME bank;
- adequate power;
- valid controls;
- domain-level estimator.

Otherwise:
CANNOT ANSWER.

======================================================================
33. THINGS THAT MUST NOT BE SAID
======================================================================

Do not say:

- "The model represents button as BOMB" without scope/decodability qualification.
- "Probe accuracy proves causal use."
- "The whole-query pathway was removed" if the read site only sees the first-layer row-local mask.
- "R3 passed" — it did not under its preregistered accuracy gate.
- "The concept signal does not transfer" — ranking transfer exists.
- "KO-3 restores the literal meaning" on Llama.
- "The codeword row is unnecessary" generally.
- "K=1/2 are query rows" — they were scaffold.
- "K=7 proves bomb token is the mechanism" — old instrument named bomb.
- "Gun does not remap" — it is inconsistent across domains.
- "Club is a clean harmful hard negative" on the old pools.
- "n=6 proves thesis-scale generality."
- "The K=8 behavioural negative proves no behavioural effect."
- "The attack is ours."
- "Representation hijacking is ours."
- "We are first to intervene on demo→query attention."
- "ASR defines Bombness."
- "A significant row-level p-value establishes a domain-level claim."

======================================================================
34. OUTPUTS REQUIRED AT THE END
======================================================================

Produce:

1. updated append-only external_md log;
2. aligned bank manifests + audit;
3. split manifest + hashes;
4. prompt validation table;
5. concept probe report;
6. remapping/concept-axis report;
7. causal concept-direction intervention report;
8. corrected attention mechanism report;
9. behavioural report if gated;
10. independent verifier reports;
11. literature matrix update;
12. thesis/paper claim table:
       CLAIM
       EVIDENCE
       N_DOMAINS
       TEST POPULATION
       CAVEAT
       STATUS
13. "WHAT WE CAN SAY TO MATAN"
14. "WHAT WE MUST NOT SAY"
15. short Slack draft for Matan + Mahmood.

DO NOT SEND SLACK.
DO NOT EMAIL.
DO NOT CREATE A CALENDAR EVENT.

Draft only.

======================================================================
35. FINAL OPERATING PRINCIPLE
======================================================================

The goal is not to maximize the number of experiments.

The goal is to turn the current promising observations into a small number of claims that survive:

- enough data;
- correct split;
- correct population;
- correct concept;
- correct prompt alignment;
- correct read site;
- correct intervention;
- correct control;
- correct independence unit;
- correct power;
- adversarial review.

If an old important result does not meet this bar:
RE-RUN IT PROPERLY.

If a new result does not meet this bar:
DO NOT PROMOTE IT.

Omer specifically wants to be able to sit with Matan afterwards and state results he can stand behind.

Therefore favor:

    fewer,
    larger,
    cleaner,
    preregistered,
    mechanistically valid experiments

over many small exploratory ones.

The core scientific questions remain:

1. What exactly is represented in the codeword state?
2. Is there a BOMB-specific component beyond generic remapping?
3. Does that component generalize?
4. Does the model causally USE that component?
5. Which demonstration→query computation allows the model to express/use it?
6. Does destroying it alter downstream attack/use?

Answer those with thesis-scale evidence.

Proceed autonomously.

ULTRATHINK.
ULTRACODE.
PREREGISTER.
USE LARGE DATA FOR IMPORTANT CLAIMS.
DOMAIN-LEVEL SPLITS.
NO TEST LEAKAGE.
VERIFY THE PROMPTS.
VERIFY THE TOKEN POSITIONS.
VERIFY THE ACTUAL INTERVENTION.
VERIFY THAT THE READ SITE CAN PHYSICALLY SEE THE INTERVENTION.
POWER BEFORE GPU.
MAX 6 GPU JOBS IN PARALLEL.
LOOP ~EVERY 30 MINUTES.
FULL REVIEW ~EVERY 4 HOURS.
ADVERSARIAL REVIEW.
COMMIT.
PUSH.
KEEP THE EXTERNAL_MD LOG CURRENT.

Proceed.
