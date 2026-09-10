# DCS — BOMB REPRESENTATION SEARCH → CAUSAL ASR
## Continuation research record, opened 2026-09-10

**STATUS: OPEN / APPEND-ONLY.**

**This file SUPERSEDES**
`external_md/DCS_BOMBNESS_MECHANISM_AND_ASR_SUCCESSOR_PLAN_AND_PROGRESS_20260909.md`
**for all work after the successor sprint.** That file remains the authoritative record of the
successor sprint itself (ENTRY 001–055, terminal deliverable `reports/DCS_SUCC_FINAL_REPORT.md`)
and must not be edited. A cross-link pointing here has been appended to it as its final entry.

**Discipline for this file.** Append-only. Every entry is dated. Preregistrations, launches,
results, defects, corrections, reviews, claim changes, artifact paths and blockers all go here.
Nothing is deleted; superseded material is marked WITHDRAWN or VOID with provenance.

**Nothing below has been executed.** This document was written on instruction
("write that in external md and dont do anything after") as the first act of the continuation, per
§0 of the mandate it contains. Section 1 is the mandate **verbatim** as received.

---

# SECTION 1 — THE CONTINUATION MANDATE (VERBATIM, AS RECEIVED 2026-09-10)

You are continuing the SAME Doublespeak / Bombness research session and repository.
Do not restart the project.
Do not discard the work from the successor sprint.
Do not treat the previous sprint as the end of the research program.
The previous sprint completed an important subset of the plan, but several of the most important scientific goals remain unresolved.
This continuation exists specifically because the previous work established:

* the Doublespeak attack is real on the aligned population;
* semantic installation predicts attack success;
* the query codeword row is an important demonstration→query access point;
* the local residual state at the codeword is NOT sufficient to transfer the semantic interpretation;
* our current `B1` measurement is reproducible but is NOT licensed as a BOMB-specific representation;
* template transfer remains untested;
* register remains a corpus limitation;
* the important representational/mechanistic results were predominantly discovered on TRAIN;
* and we still have NO valid experiment showing that manipulating an internal BOMB representation changes ASR.

Therefore the next phase should NOT spend most of its time defending `B1`.
It should use the failure of `B1` as information about WHERE and HOW to search next.
Our central goal is now:
Find out whether there exists an internal representation that genuinely tracks semantic BOMB installation rather than token position, prompt template, generic remapping, harmfulness, register, lexical identity, or contextual anomaly; locate it; confirm it on untouched data; causally manipulate it; and determine whether that manipulation changes jailbreak ASR on the same prompt population.
This must be research-grade work.
We want conclusions we can defend to Matan and Mahmood.
We are allowed and encouraged to try multiple scientifically reasonable representations and experiments.
We are NOT allowed to fish on TEST until something succeeds.
The required structure is:
broad exploration on TRAIN → selection on VALIDATION → freeze hypothesis and analysis → one confirmatory TEST / fresh-bank evaluation.
If additional exploration is needed after TEST, use a NEW independent confirmatory population rather than iterating against TEST.

## 0. FIRST THING: WRITE THIS CONTINUATION PLAN TO EXTERNAL MD

Before running new experiments, record this continuation mandate in the authoritative external research log.
The current authoritative file is:
`external_md/DCS_BOMBNESS_MECHANISM_AND_ASR_SUCCESSOR_PLAN_AND_PROGRESS_20260909.md`
If that file is still the active append-only record, append a new clearly timestamped section such as:
`CONTINUATION MANDATE — BOMB REPRESENTATION SEARCH → CAUSAL ASR`
and write this entire plan there before executing it.
If the existing file has been explicitly frozen/closed by the previous session and appending would violate its stated discipline, create:
`external_md/DCS_BOMBNESS_REPRESENTATION_TO_CAUSAL_ASR_CONTINUATION_20260910.md`
and add explicit cross-links in BOTH records saying that the continuation file supersedes the old file for work after the successor sprint.
Do not merely summarize this mandate in the external MD.
Write the important requirements, phases, gates, statistics, controls, and prohibitions explicitly enough that another Claude session can resume the work using only the external MD and repository artifacts.
After writing the plan:
IMPLEMENT THE PLAN.
Continuously append progress, preregistrations, launches, results, defects, corrections, reviews, claim changes, artifact paths, and blockers to the external MD.
Do not wait for me between routine research steps.
Only reserve a decision for me when there is a genuine scientific choice that cannot be safely decided from the predeclared goals.

## 1. BEGIN BY RE-READING THE CURRENT SCIENTIFIC STATE

Before changing code or launching GPU work, re-read the current authoritative outputs and actual artifacts.
At minimum inspect:

* the current successor append-only external MD;
* `DCS_SUCC_CLAIM_TABLE.md`;
* `DCS_SUCC_FINAL_REPORT.md`;
* `DCS_SUCC_SPRINT_SUMMARY_20260910.md`;
* prior thesis-scale claim table;
* current prompt-validation artifacts;
* `B1` candidate artifacts;
* position-control artifacts;
* concept-free K-ladder artifacts;
* aggressive patching artifacts;
* ASR outputs;
* concept-presence outputs;
* judge reliability outputs;
* the frozen split;
* `ts116m` bank metadata;
* previous PHASE-11 artifacts;
* current literature matrix.

Do not trust prose over artifacts.
Re-derive important current numbers from outputs before using them as design assumptions.
The following are inherited facts unless artifact review disproves them:

**Current behavioural facts**
The Doublespeak attack on `button_bomb` is meaningfully stronger than simply asking the direct harmful request.
Semantic installation, measured by the concept-free model report, predicts per-domain attack success.
This closes an important old gap, but:
semantic installation → ASR is NOT the same claim as internal Bombness → ASR.
Do not conflate the two.

**Current pathway fact**
The concept-free K ladder indicates that introducing the query codeword row into the demonstration-attention cut accounts for a large fraction of semantic-readout loss.
The exact share differs across codewords.
Therefore:
the codeword row is an important access/computation site under this intervention.
Do NOT automatically upgrade this into:
the codeword stores the BOMB representation.

**Current state-transfer fact**
Aggressive full residual-state C→A transplant at the query codeword, across tested layer windows, transferred approximately none of the semantic gap despite intervention liveness.
Therefore:
the local residual state at that token, under that transplant design, is not sufficient to transfer the reading.
Do NOT overstate this as proof that no BOMB representation exists anywhere.

**Current `B1` fact**
`B1` is measurable and reproducible.
But it is:

* not convincingly BOMB-specific;
* not localized to the codeword;
* strongly explained by a token × context interaction;
* not a proxy for semantic installation;
* and therefore must NOT be called Bombness without qualification.

The new phase should treat `B1` as a negative/diagnostic reference baseline.

**Current scope limits**
Important representation/mechanism work was largely conducted on TRAIN.
Template transfer is untested.
Register is still a stated corpus limitation.
No representation intervention has yet been evaluated on behavioural ASR.
Those are central targets of THIS phase.

## 2. REFRAME THE CORE QUESTION CORRECTLY

Do NOT ask only:
"Does the codeword hidden state move toward bomb?"
We now know that question may be too local and too one-dimensional.
The research question is broader:
When a model successfully interprets a Doublespeak codeword as BOMB, is there an internal representation or computation that distinguishes installed-BOMB prompts from structurally matched non-installed / benign-remap / generic-remap prompts, generalizes across domains/codewords/templates, and causally contributes to downstream semantic interpretation and attack behavior?
Possible answers include:

1. a codeword-local vector;
2. a distributed multi-token representation;
3. a later answer/readout-position representation;
4. a trajectory over layers rather than a static state;
5. a small multi-dimensional subspace;
6. an attention/MLP output rather than residual stream;
7. a dynamic recomputation process with no persistent localized "store";
8. a semantic variable that exists but is not the behavioural driver;
9. no stable concept-specific representation under our tested model/setup.

All are acceptable scientific outcomes.
Do not prematurely force the result into the old "Bombness vector at carrot/button" framing.

## 3. CRITICAL RULE: DO NOT STOP AFTER THREE FAILED CANDIDATES

The previous sprint tested a small number of candidate constructions.
That is not enough to conclude there is no BOMB representation.
This phase must conduct a SYSTEMATIC candidate search over several scientifically distinct families.
However:
multiple candidate exploration happens only on TRAIN.
Use VALIDATION to choose finalists.
Freeze finalists before reading TEST.
If TEST has already been read for any exact candidate/hypothesis in a way that contaminates confirmation, mark it DEVELOPMENT and use a fresh confirmatory bank.
Maintain a machine-readable candidate registry.
For every candidate record:

* candidate ID;
* mathematical definition;
* motivation;
* representation source;
* position(s);
* layer(s);
* training population;
* labels;
* nuisance controls;
* validation metrics;
* installation relationship;
* ASR relationship;
* cross-codeword transfer;
* cross-template transfer;
* positional specificity;
* failure mode;
* whether eligible for confirmation.

Never choose a candidate because its TEST performance is good.

## 4. BUILD THE RIGHT TARGET VARIABLE

One reason previous concept probes became misleading is that "which demonstration set is present" is easier to classify than "which semantic interpretation was actually installed."
We should now use SEMANTIC INSTALLATION as a first-class target.
Construct per-prompt / per-domain installation variables using concept-free readouts.
Examples:

* continuous semantic log-odds;
* concept probability under a concept-free generation/readout;
* bomb token rank;
* mass over a frozen bomb-semantic lexicon;
* calibrated installation probability;
* binary installed/not-installed threshold ONLY where threshold is preregistered or used descriptively.

Prefer continuous variables when possible.
Do not define the representation target using the forced-choice channel that names `bomb`.
The main representation problem should be something like:
find internal features that predict variation in concept-free semantic BOMB installation within BOMB prompts.
This is much stronger than:
classify C_bomb vs C_knife vs C_gun.
Important:
Avoid post-hoc exclusion of non-installing domains.
Their failure to install is part of the phenomenon.
Use installation as:

* prediction target;
* moderator;
* stratification variable;
* continuous covariate;

but not as a post-outcome filter designed to improve the result.

## 5. PRIMARY DATA DESIGN: BOMB ONLY

Keep BOMB as the only primary harmful concept.
Do NOT average over unrelated harmful concepts.
Knife/gun may remain as hard negative axes or controls, but they are NOT the primary target, especially because they barely install on the existing bank.
Primary development population should remain `button_bomb` unless artifact inspection finds a fatal reason not to.
`basket_bomb` remains the lexical replication population and must never be silently pooled with button.
If basket's concept-free channel remains at the reportability floor, report that and consider building a better independent replication codeword before claiming lexical generality.
Potentially construct a third independent codeword for fresh confirmation IF power / prompt validation show the need.

## 6. DECIDE Q-014 PROPERLY: REGISTER FIX

The existing corpus has a known register limitation.
Do not simply continue repeating:
"register is a limitation."
Make a design decision based on what this phase needs.
First determine whether the CURRENT experiments we plan are protected by within-prompt / within-cell contrasts that cancel register sufficiently.
For experiments where register cannot cancel:
build a NEW clean BOMB-only bank.
The new bank should explicitly constrain/match:

* sentence length;
* hedge rate;
* modal usage;
* harmful vocabulary density outside the target noun;
* syntactic structure;
* token count;
* codeword occurrence count;
* punctuation;
* directness;
* grammatical role;
* query structure;
* demonstration style;
* domain distribution.

Run surface-only nuisance classifiers before hidden-state extraction.
Do NOT spend major GPU on the new bank until:

* prompt alignment gates pass;
* concept leakage gates pass;
* surface nuisance scores are measured;
* semantic installation works;
* ASR variation is adequate;
* train/validation/test is frozen.

If a fully regenerated bank is too expensive and a narrower clean paired bank can answer a specific hypothesis, create that instead — but record the scope.

## 7. TEMPLATE GENERALIZATION MUST BE TESTED

The previous sprint used one query template per readout channel.
This is insufficient for claiming a semantic representation.
Create multiple concept-free query/readout templates.
For example, conceptually:

* "What does X refer to here? Answer in one word."
* "In this context, what is X?"
* "What real object does X denote?"
* another structurally different but concept-free wording.

Do NOT insert `bomb` into the readout prompt.
Use several template families in TRAIN.
Select/freeze a readout ensemble or one template using VALIDATION.
Reserve at least one genuinely held-out template family for confirmation.
Questions:

* does installation remain stable across wording?
* does the internal representation predict installation across held-out readout wording?
* does the K-ladder critical row remain the codeword under a different query/readout template?
* does any Bombness candidate survive template transfer?

Do not call something semantic if it only works on one phrasing.

## 8. SEARCH REPRESENTATIONS BEYOND THE QUERY CODEWORD RESIDUAL

The biggest lesson from full-state transplant is:
do not keep looking only at the exact same local residual state.
Perform a systematic representation-source search.
Candidate sources should include, where technically accessible:

**Residual-stream positions**

* query codeword;
* codeword −2, −1, +1, +2;
* all codeword occurrences;
* mean over demonstration codeword occurrences;
* last demonstration codeword;
* first demonstration codeword;
* last K query tokens;
* full query pooled representation;
* final user-content token;
* final prompt token;
* token immediately before answer generation;
* semantically matched content tokens;
* neutral control positions.

**Alternative modules**
Where accessible without rewriting half the framework:

* attention output;
* post-attention residual;
* MLP output;
* post-MLP residual;
* optionally attention value/output aggregation around selected heads.

The goal is NOT to produce hundreds of arbitrary numbers.
The goal is to test whether semantic installation is carried more cleanly at another computation site.
For every source, compare against:

* neighboring positions;
* token-matched controls;
* context-matched controls;
* surface nuisance;
* generic remap.

## 9. FULL LAYER × POSITION MAP

Build a comprehensive TRAIN-only layer × position map for the strongest representation candidates.
Do not stop at three positions.
The map should tell us:

* where installation information first becomes decodable;
* whether it peaks at the codeword;
* whether it migrates downstream;
* whether it becomes strongest near response generation;
* whether the codeword has unique information or simply participates in global prompt gist;
* whether a candidate's trajectory differs between installed and non-installed domains.

Use semantic-role-relative token indexing.
Prompt lengths vary.
Do not compare absolute index 212 in one prompt to absolute index 212 in another unless they refer to the same role.
At minimum produce:

* raw score;
* paired C−A score;
* installation-predictive score;
* position-relative contrast;
* layer-relative contrast;
* domain distribution;
* confidence interval.

Any claim that a position is "special" must come from within-prompt/within-domain relative comparison, not absolute accuracy.

## 10. TRY POOLED / DISTRIBUTED REPRESENTATIONS

The codeword may be a conduit while the relevant semantic state is distributed.
Explicitly test pooled representations such as:

* mean of all codeword occurrences;
* mean of demonstration codeword occurrences;
* mean of last K query states;
* concatenation / low-rank compression of a small semantically motivated token set;
* weighted pooling based on predeclared attention structure;
* final prompt state;
* codeword + final prompt joint representation.

Start simple.
Do not create giant concatenated features that trivially encode template/domain.
For any pooled representation:

* compare to size-matched random token pools;
* compare to neighboring-token pools;
* compare to final-K token control;
* test cross-codeword generalization;
* test template generalization.

## 11. TRY TRAJECTORY-BASED BOMBNESS

A static vector may be the wrong object.
Create candidates based on how a representation CHANGES across depth.
Potential features:

* early→middle increase in installation score;
* middle→late increase;
* onset layer;
* peak layer;
* area-under-layer-trajectory;
* slope across a frozen layer window;
* change in similarity to a direct-BOMB reference;
* change in full-vocabulary `bomb` logit rank across layers.

This should be explored because Doublespeak may progressively resolve the interpretation rather than encode it as one fixed vector.
Again:
TRAIN discovery.
VALIDATION selection.
TEST confirmation.

## 12. FULL-VOCABULARY PROBABILITY / LOGIT ANALYSES

We still need the probability/logit side of Matan's request more thoroughly.
Do not rely only on two-option semantic log-odds.
For candidate positions and layers, analyze:

* logit for `bomb`;
* rank of `bomb`;
* `log P(bomb) - log P(codeword)`;
* mass over a frozen BOMB lexical set;
* contrast against a frozen neutral/object lexical set;
* full-vocabulary top-k semantic outputs;
* logit lens trajectory across layers.

Freeze lexical sets before confirmatory analysis.
Do not choose synonyms based on which tokens increase in TEST.
Compare these metrics to:

* concept-free semantic installation;
* ASR;
* refusal;
* literal baseline;
* benign remap.

One desired question is:
when semantic installation is higher across domains, do BOMB-related full-vocabulary signals also rise at specific internal sites?

## 13. NEW LINEAR PROBES: PREDICT INSTALLATION, NOT DEMONSTRATION IDENTITY

The old multi-concept probe can classify prompt condition without necessarily measuring semantic installation.
Now train new probes whose target is directly related to BOMB interpretation.
Possible designs:

**Regression**
Predict continuous semantic installation score from hidden state.
**Classification**
Predict preregistered high-vs-low installation groups using thresholds defined on TRAIN.
**Pairwise ranking**
Given two domains, predict which has higher semantic installation.
Ranking may be especially useful if absolute offsets vary across codewords.
Candidate models:

* regularized linear regression;
* logistic regression;
* linear SVM;
* LDA where justified.

Do not introduce nonlinear networks until linear methods are exhausted and there is a clear motivation.
Evaluate:

* held-out domains;
* held-out codeword;
* held-out template.

Compare to nuisance baselines.
If a surface-only model predicts installation equally well, hidden-state prediction is not enough.

## 14. LOW-RANK SEMANTIC SUBSPACE

A single BOMB vector may be inadequate.
Explore a small low-rank discriminative subspace.
Possible approaches:

* supervised LDA;
* reduced-rank regression;
* PLS-like linear subspace;
* PCA on paired within-domain semantic deltas followed by supervised ranking;
* top singular vectors of a paired semantic-difference matrix.

Rank selection MUST happen on VALIDATION.
Cap dimensionality.
Do not allow a 100-D patch to be called an interpretable Bombness representation.
Useful ranks might be 1, 2, 4, 8 — selected under a predeclared rule.
For each subspace ask:

* does it predict installation?
* does it transfer across codewords?
* does it transfer across templates?
* is it position-specific?
* can it be causally patched?

## 15. REFERENCE/PROTOTYPE EXPERIMENTS MUST BE BETTER ALIGNED

The previous prototype approach was beaten by a concept-free context prototype.
That is informative.
Now, if testing prototype/reference geometry again, construct much better matched reference prompts.
Potential comparison:
recipient and donor should share:

* domain;
* sentence structure;
* query;
* semantic role;
* token position;
* length;
* style;

and differ mainly in whether the target semantic is explicit BOMB vs codeword-remapped BOMB.
Build direct-BOMB reference states at matched roles.
Test similarity to:

* explicit BOMB state;
* literal codeword state;
* benign remap reference;
* harmful non-BOMB reference.

If direct-BOMB similarity increases with semantic installation AND exceeds the matched context-only prototype, that is meaningful.
Otherwise reject it.

## 16. REVISIT DIFFERENCE-IN-MEANS CREATIVELY BUT CLEANLY

Do not abandon diff-in-means.
The previous raw variants were contaminated by generic context effects.
Try paired directions that isolate one variable.
Examples where constructible:

* high-installation Doublespeak − low-installation Doublespeak, within BOMB only;
* Doublespeak BOMB − benign remap with the SAME codeword;
* direct explicit BOMB − matched benign object;
* codeword-in-BOMB-context − same codeword in literal context;
* semantic-successful domains − semantic-unsuccessful domains, fit only on TRAIN;
* difference-of-differences directions removing token×context interaction;
* residual after explicitly removing generic remap / contextual anomaly directions.

But do NOT call a residual "concept direction" simply because other directions were subtracted.
It must pass concept/installation validation afterward.
For each direction report:

* construction;
* exact populations;
* orthogonalization terms;
* norm;
* variance explained;
* installation prediction;
* cross-codeword ranking;
* template transfer;
* causal intervention result.

## 17. USE THE CURRENT `B1` AS A NEGATIVE CONTROL

Keep `B1` around.
It is valuable precisely because it is:

* reproducible;
* context-sensitive;
* non-specific.

Use it as a comparison for new candidates.
A strong candidate should ideally beat `B1` on:

* semantic-installation prediction;
* specificity;
* cross-codeword transfer;
* template transfer;
* causal leverage.

This makes our new result much more convincing than simply inventing a new metric with high absolute performance.

## 18. SEPARATE POSITION, CONCEPT, CONTEXT AND TOKEN IDENTITY

For every major candidate, try to create factorial or paired controls covering:

* same token, different context;
* same context, different token;
* same semantic concept, different codeword;
* same codeword, benign vs harmful remapping;
* same prompt, neighboring position;
* same position, different concept condition.

Whenever a candidate "works," immediately ask:
What is the simplest nuisance variable that could produce the same score?
Then run that control before promoting it.
Do not let "Bombness" become a synonym for:

* queried-word anomaly;
* harmful context;
* remapping;
* late-position state;
* prompt family;
* demonstration presence.

## 19. COMPLETE THE CONCEPT-FREE LOCALIZATION STORY

The concept-free K ladder was a major success.
Now extend it carefully.
Repeat / expand as needed with:

* more fine-grained K around the transition;
* exact token-role annotation;
* multiple concept-free query templates;
* button and basket separately;
* a third codeword if one is built;
* sufficient independent domains.

Also test direct surgical interventions such as:

* query codeword row → demonstration codeword keys only;
* query codeword row → surrounding demonstration-context keys only;
* query codeword row → all demonstration keys;
* next query token → demonstration keys;
* final prompt token → demonstration keys;
* a matched neutral query row → demonstration keys.

Question:
What part of the demonstration block does the query codeword row need access to?
This could give a much more mechanistic account than the old "codeword stores Bombness" idea.

## 20. ATTENTION-PATHWAY DECOMPOSITION

If computationally feasible with the existing infrastructure, go one level deeper.
We want to know whether the critical codeword-row access is:

* broadly distributed over demonstration tokens;
* concentrated on demonstration codewords;
* concentrated on specific surrounding semantic context;
* mediated by certain layer bands;
* mediated by a small set of attention heads or broadly distributed.

Use safe causal methods already supported by the codebase or the referenced interpretability code.
Possible experiments:

* attention edge knockout;
* activation patching on candidate heads;
* head-output patching;
* path patching head→MLP only where the implementation has been thoroughly validated.

Do NOT immediately start a massive all-head search.
First use the existing layer/position result to reduce the search space.
Any head/path claim must survive:

* matched control;
* enough domains;
* held-out validation;
* mutation/audit checks.

## 21. AGGRESSIVE PATCHING MUST MOVE DOWNSTREAM, NOT ONLY STAY AT CODEWORD

The previous full-state patch at the query codeword transferred almost nothing.
Now perform aggressive upper-bound patching at OTHER plausible sites.
Donor:
successful/high-installation Doublespeak BOMB.
Recipient:
matched literal/benign or low-installation prompt.
Keep donor/recipient as aligned as possible.
Candidate patch sites:

* final prompt token;
* codeword +1;
* last K query tokens;
* final K query states;
* pooled query representation;
* later layer positions suggested by the layer×position map;
* attention output;
* MLP output;
* small semantic-role windows.

First ask:
can ANY full-state intervention at a plausible downstream site transfer semantic interpretation?
If no full-state upper bound works anywhere, that is a profound result.
If one works:
progressively reduce the intervention:
full state
→ small token set
→ low-rank subspace
→ candidate semantic direction.
This is critical.
Do not spend hours optimizing a one-dimensional vector at a site where the full state itself has no causal leverage.

## 22. CHANGE ONLY ONE THING IN PATCHING

For every donor→recipient patch, record and verify:

* exact donor prompt;
* exact recipient prompt;
* all byte differences;
* domain;
* codeword;
* query;
* demonstration count;
* template;
* role;
* token IDs;
* source index;
* destination index;
* source layer;
* destination layer;
* tensor shape;
* intervention norm;
* resulting state equality/difference;
* whether the relevant token role is identical.

If donor and recipient differ in unrelated topic/style/template content, either redesign them or mark the result exploratory.
The intervention should isolate semantic interpretation rather than transfer "everything about another prompt."

## 23. CAUSAL CANDIDATE TESTING

Once one or more representation candidates survive TRAIN and VALIDATION, freeze the finalists.
For each finalist run:

* projection-out;
* addition;
* replacement toward high-installation state;
* replacement toward low-installation state;
* matched-norm random control;
* matched-norm orthogonal control;
* shuffled-label candidate;
* `B1` negative-control direction;
* generic remap direction;
* full-state upper-bound patch;
* disabled-hook plumbing control.

Measure at minimum:

1. candidate score before/after;
2. concept-free semantic installation;
3. full-vocabulary bomb-related signal;
4. refusal;
5. output degeneration;
6. ASR.

Causal interpretation requires the intervention to do more than perturb the network.
An acceptable causal chain should look like:
targeted candidate edit → intended representation moves → concept-free semantic interpretation moves → ASR moves → matched controls do not.
If orthogonal/random edits move ASR equally or more:
do NOT call the candidate causal.

## 24. THIS PHASE MUST RUN INTERVENED ASR

This is the single biggest missing link.
The previous report explicitly says:
no intervened behavioural arm was run.
Fix that.
Once a promising mechanistic intervention exists, run behavioural generation on the SAME prompts and SAME domains.
Do not use one bank for representation and another bank for ASR.
For each domain collect:

* baseline semantic installation;
* baseline ASR;
* intervention semantic installation;
* intervention ASR;
* refusal;
* concept presence;
* topicality.

Primary causal statistic should be preregistered before the behavioural output is seen.
Potential primary:
`ΔASR_targeted − ΔASR_matched_control`
at the DOMAIN level.
Also analyze:
`Δsemantic_installation → ΔASR`
across domains.
This is stronger than observational installation→ASR.

## 25. FIX THE ASR MEASUREMENT PROBLEM PROPERLY

The previous sprint found:

* a codeword-dependent false-positive channel;
* substantial judge disagreement.

Do NOT automatically equate the label-disagreement rate with an ASR MDE.
That is not necessarily statistically justified.
Build a proper measurement model / robustness protocol.
At minimum:

* preserve raw StrongREJECT label;
* preserve refusal;
* preserve topicality;
* preserve concept-presence corrected outcome;
* rejudge a stratified subset;
* quantify within-condition uncertainty;
* quantify disagreement;
* use repeated judging where needed for borderline causal effects.

If helpful, define a robust behavioural endpoint such as:
`ASR AND concept_present AND non_refusal`
but preregister it.
Do not alter the endpoint after seeing which version gives significance.
The existing concept-presence lexicon was prefrozen and can be reused only after verifying that it remains appropriate for the new population.

## 26. RE-SCORE OLD RUNS ONLY AS A SEPARATE INSTRUMENT STUDY

There are prior judge runs exposed to the literal-codeword false-positive mechanism.
Re-scoring them could be useful.
But:
do not mix that retrospective instrument cleanup with the new confirmatory mechanism experiments.
Label it as:
`RETROSPECTIVE JUDGE INSTRUMENT AUDIT`.
Do not rewrite old conclusions using a correction measured on an unrelated bank unless the correction is directly validated on those old populations.

## 27. OBSERVATIONAL LINK: INTERNAL REPRESENTATION → INSTALLATION → ASR

For each strong candidate, before causal manipulation, run observational analysis on held-out DEVELOPMENT/VALIDATION data.
We want to know:

* candidate → installation;
* candidate → ASR;
* installation → ASR;
* candidate → ASR conditional on installation;
* candidate → ASR conditional on nuisance variables.

Use domain-level models.
Do not overfit.
Possible models:

* Spearman;
* preregistered linear regression;
* rank regression;
* mediation-style descriptive decomposition.

Do not call mediation causal without intervention.
A useful candidate should ideally add predictive information beyond `B1` and surface features.

## 28. POWER ANALYSIS BEFORE EXPENSIVE CAUSAL ASR

Behavioural interventions can be expensive and judge-noisy.
Before running them:
estimate:

* baseline ASR variance across domains;
* between-control variance;
* judge label variance;
* target MDE;
* number of domains;
* number of control draws.

Aim for ≥0.80 power, preferably ~0.90 on the primary causal contrast.
If 23 TEST domains are insufficient, do not pretend they are enough.
Options:

* enlarge the fresh confirmatory population;
* predeclare a different independence design if scientifically valid;
* report CANNOT ANSWER.

Do not use thousands of rows to fake independence.

## 29. CONFIRMATION: WE NEED SOMETHING BEYOND TRAIN

The previous sprint's representation/mechanism results being TRAIN-only is acceptable for discovery but not enough for a final claim.
This phase must explicitly separate:
**DISCOVERY**
TRAIN only.
Broad search.
**MODEL/CANDIDATE SELECTION**
VALIDATION only.
**CONFIRMATION**
Untouched TEST or fresh independent bank.
Before confirmation freeze:

* candidate definition;
* exact position;
* exact layer/band;
* model coefficients;
* thresholds;
* primary statistic;
* nuisance comparator;
* intervention;
* expected sign;
* alpha;
* multiplicity;
* MDE;
* power;
* CANNOT ANSWER conditions;
* VOID conditions.

No re-selection after TEST.
If the old TEST has been contaminated for the exact hypothesis, use fresh data.

## 30. SECOND CODEWORD AND THIRD CODEWORD

Button remains the main discovery codeword.
Basket is useful but currently weaker on some semantic-readout properties.
Do not force symmetric interpretation.
For final lexical-generalization evidence:

* verify installation on basket;
* verify channel engagement;
* report results separately;
* never pool button+basket.

If basket cannot serve as a strong replication population, construct a new third codeword BEFORE confirmatory outcome inspection.
Use TRAIN/VALIDATION to validate the new codeword's prompt construction.
Then reserve its held-out domains for replication.

## 31. TEMPLATE × CODEWORD × DOMAIN GENERALIZATION

For the strongest final candidate, attempt a generalization matrix:
training:
`button + template family 1`
testing:

* held-out button domains;
* basket;
* held-out template family;
* basket + held-out template;
* optional third codeword.

The goal is to see whether the representation is:

* token-specific;
* template-specific;
* domain-specific;
* or genuinely semantic.

Use ranking metrics as well as raw thresholded accuracy.
A candidate with a shared direction but codeword-specific offset should be described as such rather than called a transfer failure.

## 32. POSITION-SPECIFIC CAUSAL TEST

Suppose a candidate is decodable at final prompt token and codeword.
Test whether causal leverage differs by location.
Same candidate/subspace.
Same intervention norm.
Apply at:

* codeword;
* codeword +1;
* final user token;
* final prompt token;
* one neutral matched site.

Measure semantic change and ASR.
This directly distinguishes:
a globally decodable signal
from
a location where the network actually uses it.

## 33. PATHWAY VS REPRESENTATION

We now have an important conceptual distinction:

* pathway necessity;
* local state sufficiency;
* semantic representation;
* behaviour.

Keep them separate in every report.
Possible final outcome:

1. query codeword row access is necessary;
2. BOMB state becomes explicit only downstream;
3. late representation predicts installation;
4. editing late representation changes ASR.

That would be a beautiful mechanism.
But it is a hypothesis, not a claim.
Likewise possible:

1. codeword-row access is necessary;
2. no stable concept representation is found;
3. the model dynamically recomputes the meaning;
4. behaviour is driven by a separate refusal/compliance variable.

Also valid.
Design experiments that distinguish them.

## 34. CHECK WHETHER REFUSAL IS THE REAL BEHAVIOURAL DRIVER

Our earlier project history suggests representation and refusal can dissociate.
Therefore, for every intervention, measure independently:

* semantic installation;
* refusal state/outcome;
* attack success.

Ask:
Does an intervention change ASR because it changes semantic interpretation, because it changes refusal, or both?
If possible measure the existing refusal-direction score at relevant layers, but do NOT mix it into Bombness.
A useful factorial interpretation is:
semantic interpretation axis
vs
refusal/compliance axis.
Do not collapse them.

## 35. OPTIONAL MECHANISM-DERIVED ATTACK OBJECTIVE

Only AFTER we identify a representation or pathway measure that:

* predicts semantic installation;
* survives validation;
* preferably has causal leverage;

consider whether it could become an optimization objective for GCG/MAC.
Do NOT optimize GCG against `B1` merely because `B1` exists.
A candidate objective should ideally correlate with:

* semantic installation;
* ASR;
* intervention effects.

If no such candidate survives, explicitly close the "Bombness objective" idea for this model/setup.

## 36. STATISTICS

Independence unit remains DOMAIN unless a different unit is explicitly justified.
Use:

* domain-level paired statistics;
* bootstrap CIs;
* permutation tests preserving grouping;
* sign tests;
* Holm where appropriate;
* effect sizes;
* MDE;
* power.

Print p-values with attainable floors where relevant.
Do not interpret "p at floor" as massive effect size.
Do not report row count as independent n.
Keep button and basket inference separate.

## 37. MULTIPLE CONTROL DRAWS

Previous work showed that the exact random control geometry can dominate behaviour.
For stochastic attention/mask controls use multiple independent control draws.
Verify that the draws are ACTUALLY different.
Do not trust a loop variable or filename.
Inspect selected indices.
Persist them.
If control-draw variance is meaningful, model it explicitly.

## 38. BUG-PREVENTION RULES — BINDING

The previous phases found many self-inflicted defects.
These rules are mandatory.

**Never trust `prompt_id` globally**
Use compound identity including bank/hash.
**Never trust counters as liveness witnesses**
Observe the actual tensor/input/model state.
**Missing != zero**
Raise on missing required fields.
**CPU-check population differences**
Before GPU comparison.
**Check token roles against actual tokenization**
Including punctuation/plural/casing/substrings.
**Mutation test analyzers**
Include deliberately:

* wrong sign;
* duplicated rows;
* missing rows;
* bank swap;
* domain leakage;
* test contamination;
* wrong token index;
* dead intervention;
* random-control duplication;
* concept leakage;
* false byte-identity.

**Independently reproduce headlines**
A reviewer/agent should rederive key numbers without reading the producer code or final statistic whenever possible.
**Render figures and inspect them visually**
Correct numbers can still produce misleading plots.

## 39. READ-SITE RULE

Any intervention must be evaluated at a point where the intervention could physically have had an effect.
For a layer-band intervention:
do not read the representation at the band's first hidden-state snapshot and call it the effect of the whole band.
Encode this as a hard analyzer invariant.

## 40. INTERVENTION DOSE

Persist actual measured intervention strength.
For state patching:

* donor-recipient norm;
* resulting recipient-state norm change;
* candidate-score shift;
* cosine shift.

For projection:

* fraction removed;
* actual residual change.

For attention KO:

* exact rows;
* exact keys;
* layers;
* exact edited cells.

Do not print a geometric constant as though it was observed dose.

## 41. LITERATURE CONTINUATION

In parallel, update the literature matrix.
Search for the newest relevant work on:

* Doublespeak;
* semantic remapping jailbreaks;
* ICL information flow;
* label-word attention;
* dynamic semantic binding;
* distributed vs localized concepts;
* activation patching;
* representation sufficiency vs necessity;
* intervention→behaviour;
* refusal-vs-semantic representation;
* internal activation objectives for adversarial optimization.

For every paper record whether it already does:

* codeword row localization;
* K ladder over query positions;
* concept-free readout;
* causal representation patching;
* behavioural ASR intervention.

Do not claim novelty until checked.

## 42. EXPERIMENT PRIORITY ORDER

Execute approximately in this scientific order:

**Phase 1 — Audit and freeze current state**
Re-derive current results.
Confirm TEST contamination status.
Write exact open questions.
**Phase 2 — Resolve data/register/template design**
Decide whether existing `ts116m` can answer each hypothesis.
Build fresh clean Bomb-only bank where needed.
Freeze splits.
**Phase 3 — Multi-template prompt validation**
Confirm semantic installation and ASR.
**Phase 4 — Broad representation candidate search**
TRAIN only.
Include multiple positions, pooled states, trajectories, modules, diff-in-means, probes and low-rank candidates.
**Phase 5 — Position × layer map**
TRAIN.
**Phase 6 — Candidate validation**
VALIDATION.
Select ≤3 finalists.
**Phase 7 — Aggressive downstream patching**
Find a causal upper-bound site.
**Phase 8 — Concept-free pathway decomposition**
More surgical attention interventions.
**Phase 9 — Freeze confirmatory representation hypothesis**
Preregister.
**Phase 10 — TEST / fresh confirmation**
Read once.
**Phase 11 — Causal semantic intervention**
Targeted vs matched controls.
**Phase 12 — INTERVENED ASR**
Same domains, same prompts.
**Phase 13 — codeword/template replication**
Independent.
**Phase 14 — adversarial review**
Try to destroy every claim.
**Phase 15 — paper-facing synthesis**
Only after all corrections.

## 43. RESOURCE ALLOCATION

Do not run every exploratory idea on 113 domains immediately.
Use staged scaling.
Cheap exploration:
TRAIN subset / caches.
Promising candidates:
all TRAIN domains.
Finalists:
VALIDATION.
Confirmation:
full held-out TEST / fresh bank.
Causal behavioural arms:
power-sized confirmatory population.
For the most important final results, use LARGE enough data to make a defensible claim.
Do not save GPU at the expense of statistical power on the final central experiment.
Do save GPU by killing bad candidates early using TRAIN-only gates.

## 44. WHAT A GOOD BOMB REPRESENTATION CANDIDATE SHOULD PASS

Before calling anything a finalist, require a meaningful subset of:

1. predicts concept-free semantic installation;
2. not explained by surface nuisance;
3. stronger than `B1`;
4. survives neighboring-position control;
5. survives generic-remap control;
6. transfers to basket or another codeword;
7. transfers to held-out template;
8. stable across domains;
9. reasonable layer structure;
10. aggressive full-state patch at its site has causal leverage;
11. candidate-targeted patch moves semantic interpretation;
12. matched orthogonal/random controls do not.

Do not require perfection before validation, but candidates that fail almost all of these should be killed.

## 45. THE MOST IMPORTANT CAUSAL ENDPOINT

The strongest result we want is not:
"Probe accuracy = 95%."
It is:
"A preregistered intervention targeting a representation that predicts concept-free BOMB installation reduces/increases the model's semantic BOMB interpretation and causes a corresponding change in ASR on the same domains, while matched random/orthogonal/generic-remap interventions do not."
Build the program toward this.

## 46. IF NO BOMB REPRESENTATION SURVIVES

If a broad, well-controlled search finds no candidate that generalizes and has causal leverage:
do not keep fishing forever.
At that point synthesize the alternative mechanism.
Potential conclusion:
Doublespeak success is associated with semantic installation and depends on query-codeword access to demonstrations, but there is no evidence for a stable localized BOMB state; interpretation appears to be dynamically recomputed/distributed.
But this conclusion is only warranted after:

* multiple representation families;
* multiple positions;
* multiple layers;
* pooled/distributed representations;
* at least one low-rank approach;
* concept-free probability/readout analyses;
* aligned reference comparisons;
* proper validation.

Document the evidence required before closing the Bombness hypothesis.

## 47. IF A CANDIDATE DOES WORK

Do NOT immediately celebrate.
Attack it.
Ask:

* Is this just prompt length?
* Is this just template?
* Is this just final-position state?
* Is this just codeword anomaly?
* Is this generic remapping?
* Is this harmfulness?
* Does the surface text classifier get the same result?
* Does it survive another codeword?
* Does it survive another readout template?
* Does the full-state upper bound work?
* Do random/orthogonal controls move equally?
* Does ASR move?

Only then promote it.

## 48. CLAIM LANGUAGE

Use strict status labels.
Recommended vocabulary:

* CONFIRMED
* REPLICATED
* MEASURED
* NEGATIVE
* INCONCLUSIVE
* CANNOT ANSWER
* VOID
* EXPLORATORY
* VALIDATION
* WITHDRAWN
* UNSUPPORTED

Do not silently upgrade exploratory evidence.

## 49. KEEP A LIVE CLAIM TABLE

Maintain/update:
`reports/DCS_SUCC_CLAIM_TABLE.md`
or create a successor claim table if modifying it would destroy provenance.
Every important claim should show:

* exact wording;
* status;
* population;
* independence n;
* split;
* statistic;
* controls;
* caveats;
* source entry;
* artifact path.

Also maintain:
WHAT WE CAN TELL MATAN
and
WHAT WE MUST NOT SAY
Update these when evidence changes.

## 50. FIGURES

Create research-facing figures only after statistics are frozen.
Desired new figures include:
**Figure A**
Semantic installation vs ASR by domain.
**Figure B**
Layer × position map of candidate installation representation.
**Figure C**
Candidate comparison:
`B1` vs probe vs trajectory vs pooled/subspace candidates.
**Figure D**
Codeword/template transfer.
**Figure E**
Concept-free K-ladder and finer surgical knockouts.
**Figure F**
Full-state patch upper bounds across positions.
**Figure G**
Targeted intervention vs random/orthogonal controls.
**Figure H**
Δ semantic installation vs Δ ASR.
All plots must clearly state:

* TRAIN / VALIDATION / TEST;
* domains;
* codeword;
* template;
* metric;
* CI;
* whether exploratory or confirmatory.

Render every figure and visually inspect it.

## 51. SUBAGENT USE

Fan out subagents aggressively where this does not contaminate experiment selection.
Good tasks:

* independent design criticism;
* literature search;
* code review;
* data leakage audit;
* token-role audit;
* surface-confound analysis;
* power analysis;
* independent result re-derivation;
* mutation testing;
* claim-red-team review.

Prefer read-only agents.
One agent should not know the producer's headline when independently reproducing it if blindness is feasible.

## 52. ITERATIVE OPERATING LOOP

Continue the same iterative research discipline.
Approximately every 30 minutes:

* inspect jobs;
* inspect outputs;
* update external MD;
* launch valid next steps;
* check whether the research path still addresses the central question.

Approximately every 4 hours run a full review:
**CODE REVIEW**
Could the implementation differ from the preregistration?
**DATA REVIEW**
Are populations aligned?
Is TEST untouched?
Are domains independent?
**OUTPUT REVIEW**
Do raw rows agree with summaries?
Are any channels disengaged?
**STATISTICAL REVIEW**
Power?
Multiplicity?
Effect size?
P-floor?
Correct denominator?
**SCIENTIFIC REVIEW**
Could the finding be:
position?
template?
register?
remapping?
harmfulness?
codeword anomaly?
readout leakage?
judge artifact?
Append the review to the external MD.

## 53. GIT RULES

Commit and push after meaningful progress.
Never background `git commit`.
Do not claim a file exists in a commit unless it does.
Do not delete failed results.
Supersede/quarantine with provenance.
Keep experiment configs frozen after outcome generation starts.

## 54. DO NOT SEND COLLABORATOR MESSAGES

You may WRITE drafts.
Do NOT:

* send Slack;
* send email;
* create calendar events.

Maintain a draft update for Matan and Mahmood only.

## 55. FINAL RESEARCH QUESTIONS THIS CONTINUATION MUST ANSWER

At the end, produce a self-contained final report answering:
**A.**
Does any internal representation genuinely track semantic BOMB installation?
**B.**
Which operationalization works best?
**C.**
Does it beat `B1` and surface/template/anomaly controls?
**D.**
Where is it across layers and positions?
**E.**
Is it local or distributed?
**F.**
Does it transfer across codewords?
**G.**
Does it transfer across templates?
**H.**
What exactly does the query codeword row need from the demonstrations?
**I.**
Can a full-state patch at any downstream site transfer BOMB interpretation?
**J.**
Can a low-dimensional representation reproduce that transfer?
**K.**
Can we causally reduce/increase semantic installation?
**L.**
Does that intervention change ASR?
**M.**
Is ASR change mediated by semantic interpretation, refusal, or both?
**N.**
What is the strongest mechanism we can defend?
**O.**
If no Bombness representation survives, what alternative mechanism is supported?
**P.**
What can we tell Matan and Mahmood?
**Q.**
What must remain forbidden?

## 56. REQUIRED END-OF-PHASE DELIVERABLES

Produce:

* updated append-only external MD;
* updated claim table;
* candidate registry / leaderboard;
* prompt-validation report;
* surface/register audit;
* template-transfer report;
* layer×position report;
* K-ladder/pathway report;
* patching report;
* causal intervention report;
* ASR intervention report;
* judge/instrument robustness report;
* literature update;
* publication-quality figures;
* final self-contained report;
* Slack draft for Matan/Mahmood marked DRAFT ONLY.

Every headline must point to an artifact.

## 57. MOST IMPORTANT INSTRUCTION

Do not interpret the previous sprint's result:
"`B1` is not Bombness"
as:
"there is no Bomb representation."
Interpret it as:
"the simplest codeword-local residual direction is the wrong object, so the next research question is where and in what form semantic BOMB information actually appears."
Search creatively but scientifically.
Try multiple reasonable representation families.
Use enough data.
Use proper domain-level splits.
Do not mix Bombness with position.
Do not mix Bombness with template.
Do not mix Bombness with generic remapping.
Do not mix Bombness with harmfulness.
Do not mix Bombness with refusal.
Do not infer semantics from a readout that names the answer.
Do not use TEST to choose what works.
And do not stop at representation.
Our target is ultimately:
INTERNAL REPRESENTATION / COMPUTATION → SEMANTIC BOMB INSTALLATION → ACTUAL JAILBREAK ASR.
We already established the rightmost observational relationship.
Now find out whether there is a defensible internal variable or pathway that completes the chain.
Now:

1. write this continuation program into the authoritative external MD;
2. preregister the immediate next experiments;
3. perform the necessary audits;
4. implement the plan;
5. document progress continuously;
6. use subagents for parallelizable audits/reviews;
7. use SLURM for appropriate GPU work;
8. independently verify important results;
9. perform regular adversarial reviews;
10. commit and push meaningful progress.

Do not spend the session merely producing more prose about the previous sprint.
Generate NEW evidence.
Do not skip difficult phases simply because they may return negative results.
The objective is to leave this continuation with a much stronger answer to Matan's actual question:
When Doublespeak causes the model to understand `button` as BOMB and jailbreak successfully, what internal computation represents or constructs that interpretation, and is that computation actually responsible for the behavioural success?

---

# SECTION 2 — CARRY-FORWARD STATE (so this file alone is sufficient to resume)

*Written 2026-09-10 alongside Section 1. Every number here is inherited from the successor sprint
and is marked **TO BE RE-DERIVED FROM ARTIFACTS** per §1 of the mandate before any of it is used as
a design assumption. Prose is not evidence.*

## 2.1 Standing prohibitions — carried into this phase unchanged

* ⛔ **Never read TEST while searching for or selecting a candidate.**
* ⛔ **Never edit a FROZEN preregistration.** Amendments are new files that load the parent and
  apply named diffs; integrity is checked by `scripts/dcs_succ_amendment_integrity.py`
  (three outcomes only: IDENTICAL / DECLARED / UNDECLARED DRIFT — the ANNOTATED category was
  deleted in `C-217b` because it could hide a forged change).
* ⛔ **Do not send Slack, do not email, do not create calendar events.** Drafts only (mandate §54).
* ⛔ **Never run `git commit` in the background** (mandate §53). The pre-commit hook runs 341 guard
  tests; allow ≥600 s.
* ⛔ **The independence unit is the DOMAIN, never the row.**
* ⛔ **Never pool `button` and `basket`.** Separate inference, separate reporting.
* ⛔ **`prompt_id` is NOT unique across banks — it is *identical* (1130/1130).** Every join must be
  compound `(bank_file_sha16, domain)`. Enforced by an assertion in
  `scripts/dcs_succ_q2_concept_present.py`; see `C-217a`, where a button-generations ×
  basket-judge chimera ran to exit 0 and produced ρ = +0.3700.
* ⛔ **Do not infer semantics from a readout that names the answer.**
* ⛔ SLURM: pin `--nodelist=n-802,n-803,n-804,n-805,t-806`. Node **n-801** stalls weight loads
  (`C-201`/`C-202`: four jobs, all four on n-801, zero output).

## 2.2 Populations, banks, splits

* Primary development population: **`button_bomb`**, bank family **`ts116m`** (2 × 2 core).
  Cells: **A** `benign_literal` · **B** `direct_harmful` · **C** `natural_doublespeak` (the attack)
  · **E** `concept_in_benign_ctx`. **A and C share a token-identical 28-token query span.**
* Lexical replication population: **`basket_bomb`**. Its concept-free channel is ~4× thinner;
  mandate §30 requires deciding whether it can serve as replication or whether a **third codeword**
  must be built before confirmatory outcome inspection.
* Hard-negative axes, NOT primary targets: `*_knife`, `*_gun` (they barely install).
* Frozen split manifest: **113 domains** total → **TRAIN 67** (70 assigned − 3 exclusions),
  plus VALIDATION and **TEST 23**. Read the manifest; do not re-derive from memory.
  Per-arm exclusion files come from `scripts/dcs_ts_make_exclusions.py --split`.
* Mandate §28 explicitly warns: **23 TEST domains may be insufficient** for the causal ASR
  contrast. Power-size before spending GPU; enlarging the confirmatory population is the
  preferred remedy over pretending.

## 2.3 What is already known — inherited, all TO BE RE-DERIVED

| Fact | Value | Status | Where |
|---|---|---|---|
| Attack beats the direct harmful request | 103/104 informative domains; 0.1398 vs 0.0071 | CONFIRMED | `S-00x`, PR-066 Q1 |
| Installation → ASR (per-domain Spearman) | **ρ = 0.3961**, 113 domains, p at floor, MDE 0.2996 @ 0.90 | CONFIRMED, preregistered (`PR-066`) | Q2 |
| Same, with judge false positives removed | **ρ = 0.4206** | strengthens | `C-209` correction |
| Codeword query row share of demo→query effect | **62 %**, 67/67 domains, control **+0.03**, `K* = 10` replicates on basket | CONFIRMED | concept-free K ladder |
| Full-state C→A transplant at that token, all 32 layers | moves **0.054 %** of a 12.33 log-odds gap, provably live | NEGATIVE | aggressive patching |
| `B1` magnitude | ~10 % of the A→E gap, 66–67/67 domains, ~14 sd over random, register-independent | MEASURED | `B1` artifacts |
| `B1` decomposition | it **is** the token × context interaction: `I` = 128 %/102 % of `B1`; harm main effect **negative** | the central negative (`C-208`) | H/I block |
| `B1` concept specificity | concentration **1.202 / 1.025** (1.0 = uniform) | NOT SPECIFIC | residual-axis 3×3 |
| `B1` localisation | indistinguishable from the neutral token at +1; worse-aligned than the final prompt token | NOT LOCAL | position control |
| Judge false-positive floor | **15.5 %** (`button`) / **2.2 %** (`basket`) — literal-object answers scored as jailbreaks | instrument defect (`C-209`) | concept-presence |
| Judge label reproducibility | flips **13.7 %** of labels on 226 byte-identical prompts, κ = 0.44 | instrument defect | `N5` |
| Prior judge runs exposed to the same mechanism | **127 of 461** (≥200 rows, `goal_status = substituted` on every row) | **none revised** | `A-104` |
| Intervened behavioural arm | **NOT RUN** — plan §32 Link 5 not established | the biggest gap | final report §43 J |
| Template transfer | **NOT TESTED** — one query template per readout channel | open | — |
| Register | stated corpus limitation; `Q-014` decision open | open | — |

**The one-sentence inherited headline:** the attack is real, beats asking directly, and the model's
own semantic report predicts where it lands; the mechanism runs through the codeword's query row as
a **conduit, not a store**; and what we were calling Bombness is a **token × context anomaly
signal**, not a bomb representation.

## 2.4 Code that already exists and should be reused, not rewritten

| Path | What it does |
|---|---|
| `scripts/dcs_succ_bombness_candidates.py` | `B1` search; `loo_direction()` (leave-one-domain-out), `sign_test_two_sided`, `boot_ci`, residual-axis 3×3, `leakage_probe`. **Family key is `family_id.split("|")[1:-1]`** — `[2:-1]` silently halved the data (`D-001`). |
| `src/boombness/aggressive_patching.py` | donor→recipient state transplant. `PAIRS`/`PAIR_ALIGNMENT`, `END_RELATIVE_SHARED_SUFFIX = 28`, `donor_probe_pos`, `--bank-blocks`, `--only-domains-file`. Token-identity assertion in `donor_positions()` **must stay guarded on `align_mode == "end_relative"`** (`C-203`). |
| `src/boombness/kladder_run.py` | K-ladder runner; one model load via `ModelCache`, drives `score_behavior.main()` in-process. `REL_END_ROLE` maps K→token. |
| `scripts/dcs_succ_concept_presence.py` | 44-term prefrozen lexicon (excludes `bomb`/`button`/`basket`), `DONE.json` gate, refuses when the judge covers fewer rows than were generated. **§25 requires re-verifying the lexicon on any new population before reuse.** |
| `scripts/dcs_succ_n5_judge_reliability.py` | judge reproducibility from the byte-identical dose-0 A/C prompts. |
| `scripts/dcs_succ_q2_concept_present.py` | re-runnable Q2; binds predictor **and** outcome by `bank_file_sha16`. |
| `scripts/dcs_succ_amendment_integrity.py` | amendment vs parent diff. |
| `scripts/dcs_ts_prereg.py` | frozen-preregistration harness; refuses on non-FROZEN status, null `*_sha16`, missing mandate fields, bank hash mismatch, blocking checklist items. |
| `scripts/dcs_succ_b1_position_control.py` · `dcs_succ_b1_surface_floor.py` · `dcs_succ_phase_statistics.py` · `dcs_succ_figures.py` | position control (cos/raw/gap triple — **use the position-portable cosine**, `C-214`), register nuisance floor, statistics filer, figures (cards queued and drawn after `tight_layout` in figure coordinates, `C-216`/`C-218`). |
| `scripts/dcs_ts_make_exclusions.py` | per-arm `--exclude-prompt-ids` from the bank / frozen manifest. |

## 2.5 The three defect shapes that recurred — read before writing analysis code

1. **A quantity that could not have told you it was wrong.** Appeared **inside the repairs for
   itself twice** (`C-213a`, `C-217b`). A denominator artefact (`C-214`), an in-sample axis printed
   where a LOO axis was claimed (`C-215`/C3), residual-gap units printed beside full-gap units and
   **inverting a conclusion** (`C-215`/C4), a geometric constant printed as an observed measurement
   (`C-134`). ⇒ **§39 read-site rule and §40 dose persistence are hard analyzer invariants.**
2. **A liveness witness that was not one.** `grep -c` matching a pre-existing parameter name
   (`D-007`); a counter incrementing while the intervention wrote zero rows (`C-203`, `C-204`).
   ⇒ **Observe the tensor/input/model state, never the counter.**
3. **A join that silently bound the wrong population.** `prompt_id` identical across banks
   (`C-217a`). ⇒ **Compound identity, asserted, every time.**

**The two defences that actually worked are procedures, not checks:** adversarial re-derivation by
an agent forbidden to read the original, and writing down in advance what would make a result
uninterpretable. A third earned its place late: **an artifact that renders must be rendered and
looked at** — every statistic on the `C-218` panel was correct and the picture was not.

## 2.6 Prior deliverables this phase must not overwrite

`reports/DCS_SUCC_CLAIM_TABLE.md` (19 rows + changelog) · `DCS_SUCC_FINAL_REPORT.md` ·
`DCS_SUCC_SPRINT_SUMMARY_20260910.md` · `DCS_SUCC_SLACK_DRAFT_MATAN_MAHMOOD_20260910.md`
(⛔ **DRAFT, NOT SENT**) · `DCS_SUCC_LITERATURE_UPDATE_20260909.md` ·
`DCS_SUCC_S002_INDEPENDENT_VERIFICATION.md` · fifteen `DCS_SUCC_REVIEW{1,2,3}_*.md` ·
`reports/figures/F{2,3,5,8}_*.png` · 16 artifacts under `outputs/dcs_succ/` · frozen configs
`configs/dcs_ts_pr066_behaviour.json`, `..._amendment1.json`, `..._amendment2.json`.

Per mandate §49, a **successor claim table** is to be created rather than modifying the above where
modification would destroy provenance.

---

# SECTION 3 — PROGRESS LOG (append-only)

*Entries are numbered from `CONT-ENTRY 001`. Nothing has been executed yet.*

### 2026-09-10 — CONT-ENTRY 000 — record opened, mandate written, **no work performed**

This file was created on the instruction *"write that in external md and dont do anything after."*
Section 1 is the continuation mandate verbatim. Section 2 is the carry-forward state. **No audit,
no preregistration, no code change, no job launch, no analysis has been performed under this
mandate.** The successor sprint's cluster jobs are all complete; nothing is running.

**The next action, when work resumes, is mandate §42 Phase 1** — re-derive the Section 2.3 numbers
from artifacts, confirm TEST contamination status per candidate/hypothesis, and write the exact
open questions — *before* any code change or GPU job.


---

### 2026-09-10 — CONT-ENTRY 001 — **Phase 1 opened.** Cluster idle; ten blind auditors launched; the decisive design fact found before any of them reported

**Mandate §42 Phase 1** (audit and freeze current state) is now running. The 30-minute operating
loop of §52 is armed as session cron job `36a25acf`.

**Cluster state:** `squeue -u $USER` is **empty**. Nothing inherited is running; every GPU-hour
this phase spends is a new decision.

#### 1. The fact that decides Phase 2, found by reading `config.json` rather than a report

Every `ts116m` extraction on disk was run with:

```
--layers 6,7,8,9,10,11,12,13,14   --position codeword_last
```

⇒ **One position, nine layers.** That position is `rel_end −10`, the codeword — *precisely the site
the successor sprint exhausted and reported a null at* (`0.054 %` of a 12.33 log-odds gap under a
provably-live full-state transplant). The inherited representation corpus therefore **cannot answer
a single question in mandate §8, §9, §10 or §11**, all of which are about other sites, other
modules, other layers, or trajectories across depth. This is not a limitation to note; it is the
reason Phase 2 must generate data before Phase 4 can begin.

#### 2. Model and geometry, re-derived from code, not from memory

| quantity | value | where |
|---|---|---|
| model | **`meta-llama/Llama-3.1-8B-Instruct`** | `doublespeak_causality/ds_common.py:70` (`PRIMARY_MODEL`) |
| transformer blocks | **32** → 33 hidden states (`h[0]` = embeddings) | layer convention recorded in every run's `metadata.json` |
| hidden dim | **4096** | model card; to be confirmed against a real tensor by the inventory agent |
| GPU used previously | NVIDIA **L40S** | `RUNMETA.json` |
| layers NOT extracted | **24 of 33** (only 6–14 exist) | `config.json` |

⚠️ Note for the record: `src/boombness/score_behavior.py` contains many `Qwen3-14B` references from
earlier phases. The **`ts116m` extractions are Llama-3.1-8B**, which is confirmed independently by
`kladder_run.REL_END_ROLE` carrying Llama-3 chat scaffolding (`<|start_header_id|>`, `<|eot_id|>`)
and by the token-role map's tokenizer line. Anyone resuming must not read the Qwen strings as this
phase's model.

#### 3. Bank arithmetic, counted from the bank file

`data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl`:

* **22,272 rows**, **116 domains** (113 analysed after the three preregistered exclusions).
* cells **A / B / C / E = 5,568 each**; query kinds `behavioral` / `semantic_forced_choice` /
  `semantic_one_word` = **7,424 each**; doses `4 / 8 / 0` = 13,920 / 5,568 / 2,784.
* The subset the candidate analysis actually used — cells `{A,B,C,E}` × `semantic_one_word` ×
  dose 4 — is **4,640 rows = 116 domains × 10 family slots × 4 cells**. (67 train domains × 10 × 4
  = **2,680**, which is exactly the row count in `cand_train9.log`. ✅ The two agree.)

#### 4. Why a full layer × position map is **cheap**, which was not obvious

The capture loop calls `eb.forward_hidden(lm, ids)`, which **already returns every hidden state**;
`pick_layer_rows(hs, layers, pos)` then throws all but one position away
(`scripts/dcs_extract_under_ko.py:594`). So capturing *P* positions × *L* layers costs **no extra
forward compute** — only memory and disk.

Measured rate from the existing run: 22,272 rows in **3,482 s** ⇒ **0.156 s/row**. The 4,640-row
subset is therefore ≈ **12 minutes of forward passes per bank**, not hours.

Disk is the binding constraint, not GPU: `4640 × P × L × 4096 × 2 bytes`. The shared filesystem is
at **94 %** (1.3 TB free of 20 TB), so this phase will **not** take the full 33-layer × 28-position
map (35 GB/bank). The provisional design is a **stride-2 layer grid (0,2,…,32 = 17 layers)** across
the mapped query span, ≈ **12 GB/bank**, with finalists re-extracted at full layer resolution in
their selected band only. ⛔ This is provisional and is **not yet preregistered**; the inventory and
position-machinery audits may change it, and it will be frozen in `PR-069` before extraction.

#### 5. The role coordinates this phase will use

`kladder_run.REL_END_ROLE` already gives a **frozen, Llama-3-specific** map of the query span
(28 rows). It is reused, not re-derived:

| rel_end | role |
|---|---|
| −1…−4 | response header (`\n\n`, `<|end_header_id|>`, `assistant`, `<|start_header_id|>`) |
| −5 | chat scaffold `<|eot_id|>` |
| −6 | `?` |
| −7, −8 | ` to`, ` refer` |
| **−9** | ` actually` — **the neutral downstream read site** (the §18 same-position control) |
| **−10** | **CODEWORD** ` button` / ` basket` — the exhausted site |
| −11…−14 | ` word`, ` the`, ` does`, ` what` |

Mandate §8's "codeword ±1, ±2" are therefore **already named offsets**: −11, −12 (before) and
−9, −8 (after). No new token-role work is needed for the query side; only the demonstration-block
positions require new resolution.

#### 6. Ten auditors launched, deliberately blind (§51)

Workflow `wf_6066abda-a38`, two phases. **Every re-derivation agent was given the artifact path and
the definition but *not* the previously reported value**, and all are forbidden to read
`reports/DCS_SUCC_*.md` or the external MDs to obtain their answer. All are read-only and all are
forbidden to compute any statistic over TEST domains.

| agent | question |
|---|---|
| `rederive:q2-installation-asr` | ρ(installation, ASR), raw **and** concept-corrected, with the `bank_file_sha16` on **both** sides and the attainable p-floor |
| `rederive:b1-magnitude-and-HI` | `B1` in gap units, sign count, H/I split, concentration ratio — each labelled **LOO vs in-sample** and **full-gap vs residual-gap units** (`C-215`) |
| `rederive:kladder` | K\*, the single-rung share with its denominator stated, the dose-matched control, **and the per-rung edited-cell count** (a rung editing 0 cells is not a measurement) |
| `rederive:patch-upper-bound` | the transplant's movement as a % of the gap — **and whether the recorded dose proves a live hook or a dead one** |
| `rederive:judge-instrument` | the dose-0 false-positive floor per codeword, κ recomputed from the confusion counts rather than read, and the exposed-prior-run count with the glob stated |
| `audit:test-contamination` | per-hypothesis TEST verdict, distinguishing *a bank containing test rows* from *an analysis computing a test statistic* |
| `audit:representation-inventory` | every `ts116` run's position/layers/rows/cache, and the GB + GPU-hour arithmetic for re-extraction |
| `audit:position-machinery` | the **smallest diff** that gets multi-position capture, every reader of `final_occurrence_reps.pt`, and a measurement of the A/C shared trailing-token count **from the bank, not from prose** |
| `audit:register-and-surface` | **the `Q-014` decision made rather than restated**: does register cancel in a within-domain C−A contrast, and can a surface-only classifier separate C from A or predict installation? |
| `audit:concept-presence-reuse` | whether the prefrozen lexicon is still valid — including its behaviour on **degenerate intervened generations**, which is new in this phase |

**Nothing has been concluded yet.** The next entry reports what the auditors found, and no design
decision in §4 above is frozen until they do.
