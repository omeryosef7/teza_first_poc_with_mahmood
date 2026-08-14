# DOUBLESPEAK CAUSALITY — NEXT RESEARCH SPRINT

## Role

You are continuing the existing Doublespeak causal-mechanism research program in:

```
/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/
```

Primary working directory:

```
$ROOT/doublespeak_causality
```

Branch:

```
behavioral-causality-sprint
```

This is not a fresh project. Do not redo experiments that have already been closed unless a specific control, replication, correction, or missing causal test below requires it.

The goal of this sprint is to take the strongest results we already have, incorporate the methodology from *Prompt Injection as Role Confusion*, and answer a sharper mechanistic question:

> **What latent state actually causes Doublespeak to jailbreak?**
>
> Is the model's internal CARROT → BOMB identity confusion itself behaviorally causal, or is it merely a real but epiphenomenal representation while a separate refusal/compliance state determines behavior?

The desired output is a publishable causal story, not another large collection of correlations.

---

## 0. FIRST: READ THE CURRENT STATE AND DO NOT LOSE IT

Before writing code or launching compute, read in full:

1. `RESEARCH_LOG_SPRINT_2026-08-02_TO_08-14.md`
2. `RESEARCH_LOG_AUDIT_2026-08-14.md`
3. the latest `RESEARCH_HANDOFF.md`
4. `docs/ASYMMETRY_FINAL_SYNTHESIS.md`
5. `docs/SECTION20_RESULTS.md`
6. `docs/OWED_SUBMISSIONS.md`
7. `BUG_AND_DEVIATION_LOG.md`
8. `EXPERIMENT_REGISTRY.csv`
9. the relevant current manifests and raw artifacts.

When documents disagree:

> raw per-example artifact > recomputation > audit correction > current synthesis > older report > old prose summary.

Never silently choose the prettier number.

Create:

```
docs/ROLE_PROBE_NEXT_SPRINT_EXECUTION_LOG.md
```

and record every decision, job, failure, deviation, correction, and result there as the sprint proceeds.

---

## 1. THE SCIENTIFIC STARTING POINT — TREAT THESE AS ESTABLISHED

Do not spend compute trying to rediscover these.

### 1.1 The concept-remapping circuit is real

On Llama-3.1-8B-Instruct we have mapped:

```
demo-codeword K/V retrieval around L8–L10
→ distributed L8–L11 / L9 MLP write
→ L14–L21 carry heads
→ L30–31 readout.
```

The circuit is distributed.

There is no single edge, head, or layer that is the bottleneck.

The carry representation is partially sufficient for the concept readout.

The concept representation is therefore real and causal for what the model internally reads the codeword as.

### 1.2 But concept representation ≠ jailbreak behavior

This is our central established dissociation.

Removing the concept circuit substantially changes the concept readout while producing little or no specific behavioral effect.

The large powered experiment found approximately:

- concept write+carry ablation: small / non-significant behavioral shift;
- count-matched random intervention: substantially larger behavioral movement;
- clearharm concept ablation: essentially zero specific behavioral effect.

The correct claim is **epiphenomenal by specificity**, not "mathematically zero."

### 1.3 Refusal suppression is the behavioral lever

The validated refusal direction is approximately orthogonal to the concept direction.

It has strong behavioral causality:

- refusal ablation substantially increases harmful behavior;
- refusal induction/restoration substantially decreases harmful behavior;
- decision-state patching moves behavior toward Direct;
- the decision state mediates nearly the full Doublespeak behavioral effect;
- pre-generation refusal state predicts which prompts jailbreak.

The current best causal picture is:

```
Doublespeak demos → broad refusal suppression → mid/late refusal decision → behavior
```

while simultaneously:

```
Doublespeak demos → concept remapping circuit → BOMB-like representation
```

with the second branch largely decoupled from behavior.

### 1.4 We also know an important attack-optimization asymmetry

The refusal axis is:

- causally potent in activation space;
- highly reachable from continuous input space;
- exploitable by a continuous soft-prompt optimizer;

but the corresponding discrete GCG objective is non-specific and seed-unstable.

Continuous input optimization produced a large behavioral effect.

Discrete token optimization toward the same coordinate did not reliably outperform a matched random direction.

Do not restart basic "refusal direction GCG" experiments.

### 1.5 The current strongest conceptual thesis

We currently have two distinct dissociations:

**Representation → behavior**

A representation can be real and causally manipulable as a readout while not causing the jailbreak.

**Objective → behavior**

An optimizer can strongly manipulate an internal coordinate without producing a correspondingly stable behavioral effect.

This sprint should determine whether the new role-probe methodology lets us explain *why*.

---

## 2. WHAT THE NEW ROLE-CONFUSION PAPER ADDS

The methodological idea we want to import is not merely "train another probe."

The useful idea is:

> Build a controlled linear probe for the model's perceived latent identity/state, deliberately minimizing semantic and positional confounds, and then ask whether the attack moves adversarial text into that latent state **before generation**.

The role-confusion paper trains role classifiers under tightly controlled conditions and shows that stylistic spoofing can move text into the latent representation of another role, with the resulting probe-measured confusion strongly associated with attack success before generation. (arXiv)

Our analogue is:

- CoTness → Bombness
- Userness / CoTness competition → Carrotness / Bombness
- role-confusion state → semantic-identity confusion
- jailbreak-driving latent state → compare against Refusalness / Complianceness

The important scientific question is therefore:

> Does high Bombness **cause** jailbreak success, or does Doublespeak merely produce Bombness while a separate low-Refusalness state causes the behavior?

If the second answer survives proper causal intervention, that is stronger than either paper alone.

---

## 2A. USE THE AUTHORS' OFFICIAL IMPLEMENTATION AS THE REFERENCE

Before implementing any Bombness / contextual-identity probe work below, the
authors' released implementation is the **primary reference implementation**.

Official repository:

```
https://github.com/role-confusion/prompt-injection-as-role-confusion
```

### 2A.1 Import it as a plain source folder — NOT as Git

Immutable snapshot location:

```
$ROOT/doublespeak_causality/third_party/prompt_injection_role_confusion/
```

Do **NOT**:

- `git clone`;
- add a git submodule;
- add a git subtree;
- initialize another git repository;
- preserve a nested `.git/` directory.

Download the GitHub master-branch archive as ZIP/tarball via curl/wget, extract,
remove the temporary archive:

```bash
mkdir -p "$ROOT/doublespeak_causality/third_party/prompt_injection_role_confusion"
tmpdir=$(mktemp -d)
curl -L \
  "https://github.com/role-confusion/prompt-injection-as-role-confusion/archive/refs/heads/master.zip" \
  -o "$tmpdir/role_confusion.zip"
unzip -q "$tmpdir/role_confusion.zip" -d "$tmpdir/unpacked"
rsync -a \
  "$tmpdir/unpacked/prompt-injection-as-role-confusion-master/" \
  "$ROOT/doublespeak_causality/third_party/prompt_injection_role_confusion/"
rm -rf "$tmpdir"
```

Verify explicitly that this returns nothing:

```bash
find "$ROOT/doublespeak_causality/third_party/prompt_injection_role_confusion" -name .git
```

Do not modify the downloaded upstream source in place. Treat it as a frozen
reference snapshot.

Create `third_party/prompt_injection_role_confusion/SOURCE_INFO_LOCAL.md`
containing: upstream repository URL; upstream branch; retrieval date; exact
upstream commit SHA if retrievable through the GitHub HTTP API; a statement that
this is a plain downloaded snapshot and not a Git repository; and which files
from the upstream implementation we actually reused/adapted.

Keep the upstream `LICENSE.md`. If substantial source code is copied or adapted
into our codebase, preserve appropriate MIT attribution.

> **STATUS 2026-08-14: DONE.** Snapshot imported at commit
> `ec333c40fd43fe991e1ebf66765051b6d7e35784` (`master`, 2026-05-31), MIT, 110
> files, 7.3 MB. `find … -name .git` returns nothing; git tracks it as ordinary
> files with no gitlink. `LICENSE.md` retained unmodified. Provenance recorded in
> `SOURCE_INFO_LOCAL.md`.

### 2A.2 Read their implementation before writing ours

Do not independently reinvent the probe pipeline first. Read the relevant
upstream code end-to-end.

Start with:

```
demo/role-probe-demo.ipynb
demo/simple_test_helpers.py
```

Then the full implementation under `experiments/role-analysis/`, especially the
notebook responsible for training/evaluating role probes. Also inspect the
role-confusion projection code under `experiments/cot-forgery-role-confusion/`,
because it shows how trained probe directions are subsequently applied to attack
activations.

Understand exactly how the authors implement:

1. activation extraction;
2. token selection;
3. role labels;
4. layer selection;
5. linear-probe training;
6. preprocessing / normalization;
7. train/test handling;
8. probe logits/probabilities;
9. projection of unseen examples;
10. aggregation across tokens/examples;
11. plotting and evaluation.

Before implementing anything, write the code review covering: relevant upstream
files; what each does; exact probe estimator; activation tensor convention;
which residual-stream location is used; preprocessing; label construction; token
aggregation; metrics; assumptions specific to their models; components we can
reuse directly; components we need to adapt for Llama-3.1-8B and Doublespeak;
and any discrepancy between the paper description and the released code.

Do not proceed based only on the paper prose if the released implementation
answers the question.

> **STATUS 2026-08-14: DONE.** Full review is **Appendix A** of this document.

### 2A.3 Base our probe implementation on their code

For the Bombness work in this plan, the default is to **adapt the authors'
released role-probe implementation rather than building an unrelated probe
framework from scratch**. We are changing the scientific labels and dataset
construction, not unnecessarily changing the probe machinery.

Their conceptual task:

```
same text + different role → learn latent role identity
```

Our main task:

```
same surface codeword + different contextual binding → learn latent semantic identity
```

Preserve their methodology wherever scientifically appropriate. In particular
reuse/adapt their implementation for:

- extracting residual activations;
- constructing probe matrices;
- fitting the linear classifier;
- obtaining continuous probe scores;
- projecting unseen attack examples;
- computing per-layer probe performance;
- applying probes to arbitrary token positions.

Do not blindly copy model-specific assumptions. Audit all: layer indexing;
tokenizer behavior; chat template; hidden-state convention; special tokens;
residual-stream hook location; dtype/device behavior.

Our known Llama implementation and existing causal infrastructure remain
authoritative for model mechanics.

### 2A.4 Keep the upstream snapshot and our adaptation separate

The upstream folder is a reference implementation. New research code lives in our
normal project source tree:

```
doublespeak_causality/
    third_party/
        prompt_injection_role_confusion/   # untouched upstream snapshot
    src/
        probes/
            contextual_identity_probe.py
            probe_dataset.py
            probe_projection.py
```

Reuse functions directly only when doing so is clean and stable. Otherwise port
the minimal required logic into our project with clear comments:

```python
# Adapted from:
# role-confusion/prompt-injection-as-role-confusion
# commit ec333c40fd43fe991e1ebf66765051b6d7e35784
# MIT License — see third_party/prompt_injection_role_confusion/LICENSE.md
```

Do not make our experiment depend on executing their notebooks interactively.
Convert the relevant logic into reproducible Python modules / SLURM entrypoints.

### 2A.5 First reproduce a small upstream probe sanity check

Before trusting our adaptation, reproduce a small version of their role-probe
behavior using their own code or minimally adapted code.

This is not a full paper reproduction. It is an implementation validation test.
Use a small enough dataset/model setting to establish that we understand their
pipeline.

Record: train probe performance; held-out probe performance; role-projection
behavior; expected directionality.

Do not spend H200-scale compute reproducing the entire paper. The upstream README
explicitly distinguishes the lightweight role-probe demo from the much more
expensive full reproduction pipeline.

Once this sanity test passes, freeze the relevant implementation choices.

### 2A.6 Then implement our contextual Bombness analogue

The headline probe still follows §5.2 below. Do **not** merely classify literal
BOMB vs literal CARROT tokens. Construct controlled pairs where the probed
surface codeword is identical, its position is controlled, the carrier structure
is controlled, and only the contextual binding changes its semantic identity.

They hold semantic content fixed while changing role; we hold lexical identity
fixed while changing contextual semantic binding.

### 2A.7 Using upstream code does not override any existing rule

Every requirement in §3 remains mandatory: SLURM for meaningful GPU/model work;
no unmanaged background compute; inspect resources before submission; max 6
concurrent jobs; ≥20 independent matched examples per condition/layer/window;
larger n / prospective power for behavioral claims; train/dev/frozen-holdout
discipline; no test-set tuning; seeds 42/43/44; immutable raw artifacts;
manifests; exact configs; model/tokenizer revisions; SLURM job IDs; registry
updates; bug/deviation log; no overwriting prior runs; identity/no-op/random
intervention controls; explicit layer-index audits; tokenizer/chat-template
audits; StrongREJECT ≥0.5 for new binary headline results with continuous score
saved; paired statistics; failed manipulation check ≠ causal null.

### 2A.8 Do not let their code dictate our scientific conclusion

Their role probe is a **measurement tool**. Our existing causal results already
warn us that a representation can be extremely real and decodable while not being
the thing that causes jailbreak behavior.

After establishing Bombness, continue with the causal program:

1. compare Bombness against the validated refusal direction;
2. test which predicts DS success;
3. orthogonalize Bombness and refusal;
4. causally increase/decrease Bombness;
5. verify the manipulation actually changes Bombness / `p_concept`;
6. measure whether behavior changes;
7. run the Bombness × refusal 2×2 factorial.

The upstream code should help us **measure** that question cleanly. It must not
cause us to replace our causal framework with a correlation-only probe analysis.

### 2A.9 Report exactly what was reused

Maintain the **Upstream → Our Implementation Mapping** table (Appendix A §11).
For every important piece record: our component; upstream reference; reused /
adapted / rewritten; reason.

This must make it possible for us — and eventually a reviewer — to distinguish
what comes directly from the Role Confusion methodology, what is our adaptation,
and what is novel in the Doublespeak causal analysis.

---

## 3. NON-NEGOTIABLE EXECUTION RULES

These apply to the entire sprint.

### 3.1 SLURM ONLY

All meaningful compute must run through SLURM.

This includes:

- model inference;
- hidden-state extraction at scale;
- probe-dataset extraction involving model forward passes;
- activation patching;
- generation;
- GCG;
- soft-prompt optimization;
- cross-model experiments;
- StrongREJECT evaluation at scale.

Do not run GPU/model compute directly on the login node.

Do not use:

- `nohup`;
- unmanaged `&`;
- hidden background Python processes;
- persistent bash loops performing compute;
- ad-hoc tmux jobs instead of SLURM.

Lightweight repository inspection, grep, JSON inspection, documentation, small offline statistics, and unit tests are fine on the login node when they do not load models or consume significant resources.

### 3.2 Inspect resources before submission

Before every new job family:

1. inspect partitions;
2. inspect current GPU availability;
3. inspect current queue and our existing jobs;
4. inspect expected VRAM;
5. inspect walltime from comparable historical runs;
6. choose the smallest safe resource request.

Preferred GPU remains L40S when practical.

Validated 3090/A5000 fallback is acceptable where memory permits.

Do not blindly submit to hardware known to fail the current VRAM/runtime guard.

Do not duplicate already-running jobs.

Maximum 6 concurrent SLURM jobs unless an existing documented project rule explicitly changes this.

Do not use SLURM dependencies.

If a job is stuck because of a bad resource choice, cancel and resubmit intentionally rather than layering duplicate jobs.

### 3.3 Minimum sample-size rule

At least 20 independent matched examples per relevant layer / window / condition.

This is a hard floor, not evidence that n=20 is statistically adequate.

For behavioral headline claims, perform a prospective paired power calculation.

The existing n≈37 behavioral corpus is known to produce bounds around ±0.2 ASR and cannot support fine behavioral null claims.

Therefore:

Never call a behavioral effect "absent" merely because n≥20.

Use equivalence bounds / CIs and state what magnitude the experiment can exclude.

### 3.4 Seeds

For stochastic optimization:

minimum seeds = 42, 43, 44.

No single-seed optimization result can become a verdict.

If seeds disagree in sign, report the disagreement.

Do not hide it by averaging.

For deterministic greedy model generation, still preserve all reproducibility metadata.

### 3.5 Frozen split discipline

No tuning on confirmatory test.

The old v3 test has now been inspected repeatedly and is not a pristine future confirmatory set for new hypotheses.

For each new probe/objective:

- fit on train;
- select hyperparameters/layers/doses on dev only;
- freeze;
- evaluate once on a genuinely unexposed holdout.

If such a holdout does not exist, construct one before making a confirmatory claim.

All splitting must be cluster-disjoint at the semantic/task level.

Explicitly test:

- instruction overlap;
- concept overlap where required;
- codeword overlap;
- prompt-template overlap where relevant.

### 3.6 StrongREJECT contract

Resolve the current threshold inconsistency before new headline experiments.

For all new work, freeze:

```
binary malicious = StrongREJECT score ≥ 0.5
```

and always save the continuous StrongREJECT score as well.

If raw scores permit it, build a sensitivity table for the major historical behavioral claims at:

- threshold 0.25;
- threshold 0.5;
- continuous score.

Never mix thresholds in the same table without explicit labels.

Never silently quote old 0.25 binary results as if they used 0.5.

Do not quote ASR to three decimals when judge/sampling precision does not support it.

### 3.7 Every run must be immutable and reconstructable

Every run directory must contain or point to:

- raw per-example outputs;
- full config;
- dataset manifest;
- dataset hash/revision;
- model revision;
- tokenizer revision;
- git commit;
- exact command;
- seed;
- SLURM job ID;
- host/GPU;
- dtype;
- attention implementation;
- package/environment versions;
- timestamps;
- code version;
- summary;
- validation result;
- DONE marker only after successful validation.

Never overwrite completed raw outputs.

If rerunning a corrected experiment, create a new run directory and mark the old run SUPERSEDED in documentation.

### 3.8 Registry and deviation log are mandatory

The audit found that these stopped being maintained during the prior sprint.

Repair that first.

Every new experiment must have a row in:

```
EXPERIMENT_REGISTRY.csv
```

and every bug, post-registration change, unexpected implementation issue, killed/rescoped experiment, judge change, data change, or parameter deviation must enter:

```
BUG_AND_DEVIATION_LOG.md
```

the same day it occurs.

### 3.9 Independent bug review

After every meaningful new implementation, perform an independent review before scale.

Explicitly inspect:

- chat-template boundaries;
- BOS/EOS handling;
- token positions;
- hidden-state indexing;
- `hidden_states[L]` vs `hidden_states[L+1]`;
- query vs demo token indexing;
- suffix placement;
- truncation;
- tokenizer round trip;
- GQA head mapping;
- hook actually firing;
- eager vs SDPA;
- candidate-selection objective;
- gradient sign;
- objective sign;
- resume logic;
- duplicate rows;
- stale cache;
- judge denominator;
- split leakage.

We have already been burned by:

- suffix placement;
- hidden-state off-by-one;
- candidate-selection objective not being used;
- fused attention hooks;
- absolute-position assumptions.

Treat all four as first-class regression tests.

### 3.10 Hook tripwires

Every activation/attention intervention must include:

- identity patch;
- self-swap;
- α=0;
- no-op hook;
- positive control;
- random control.

Identity/no-op effects should be numerically zero up to expected floating-point noise.

If a hook that should change a known positive control does nothing, stop.

For attention-pattern intervention, force eager attention where required.

Never trust an SDPA hook without explicit verification.

### 3.11 Keep negatives

Do not optimize the story.

A powered negative is valuable.

An underpowered negative is a bound.

A failed manipulation check is not a behavioral negative.

A probe is not a mechanism.

A correlation is not causality.

A direction that changes its projection is not automatically controlling the behavior associated with that projection.

---

## 4. PHASE 0 — GOVERNANCE AND REPOSITORY REPAIR

Priority: mandatory before new GPU science.

### 4.1 Reconcile current live work

Inspect SLURM and the repo.

Determine the final state of the previously running:

- §20.7 600-step seed 43 jobs;
- §20.7 seed 44 shards;
- any other outstanding jobs.

Do not trust the August 14 prose status blindly.

Update:

- `docs/OWED_SUBMISSIONS.md`
- execution log
- Section 20 report
- registry

with the actual current state.

Do not launch duplicates.

### 4.2 Repair governance history

Backfill the missing Asymmetry / Section 20 experiment entries into `EXPERIMENT_REGISTRY.csv` from immutable artifacts.

Backfill known bugs/deviations into `BUG_AND_DEVIATION_LOG.md`.

At minimum capture:

- GCG candidate-selection bug;
- v1 leakage;
- refusal-layer indexing bug;
- test-selected continuous dose;
- missing/pruned GCG raw directories;
- threshold conflict;
- known Section 20 deviations;
- any stale/superseded claims identified by the August 14 audit.

Produce:

```
reports/GOVERNANCE_REPAIR_2026_08_14.md
```

with:

- number of output dirs;
- number registered;
- missing raw artifacts;
- missing manifests;
- dead paths;
- which claims are raw-reproducible;
- which are summary-only;
- which are report-only.

### 4.3 Freeze the new sprint

Before GPU scale create:

```
configs/manifests/role_probe_sprint_v1.json
```

containing the planned experiments, datasets, models, seeds, primary endpoints and statistical tests.

Commit it.

After this commit, changing a confirmatory endpoint or primary dose/layer requires a logged deviation.

> **GATE 0**
>
> Proceed only if:
>
> - current jobs are reconciled;
> - threshold contract is frozen;
> - train/dev/holdout policy is explicit;
> - registry/deviation logs are current enough to support the new sprint;
> - new manifest is committed.

---

## 5. PHASE 1 — BUILD A REAL "BOMBNESS" PROBE

This is the main new experiment inspired by the role-confusion paper.

Do not simply train a classifier on the hidden state of the literal tokens `"bomb"` vs `"carrot"` and call that Bombness.

That classifier may merely learn token identity.

We need two probes.

### 5.1 Probe A — lexical concept probe

Purpose:

A simple positive control / upper bound.

Construct matched carrier prompts where the only concept-level difference is:

- BOMB
- CARROT

Keep constant:

- template;
- token position;
- prompt length as closely as tokenizer permits;
- role;
- answer anchor.

Do not train directly on the embedding layer alone.

Measure hidden state at pre-registered anchors such as:

1. concept token;
2. next semantic anchor;
3. final prompt / decision token.

Train a separate linear probe at each layer.

Primary model:

```
meta-llama/Llama-3.1-8B-Instruct
```

Primary probe:

L2-regularized logistic regression.

Secondary robustness estimator:

difference-of-means direction.

Hyperparameters tuned on dev only.

Report:

- ROC-AUC;
- balanced accuracy;
- probe logit separation;
- 95% bootstrap CI;
- per-layer curves.

This probe is mainly a sanity check.

### 5.2 Probe B — contextual-binding Bombness probe — HEADLINE PROBE

This is the important analogue of the role-probe methodology.

Construct matched examples where the surface query codeword is held constant, while the context determines whether that codeword represents:

- BOMB-like meaning;
- CARROT/benign meaning.

The goal is to force the probe to decode **contextually assigned identity**, not merely lexical identity.

Use multiple codewords and multiple carrier templates in training.

Critically:

**CARROT itself should be held out from probe fitting whenever possible and used as a zero-shot test codeword.**

Likewise hold out some templates.

Example conceptual structure:

```
Condition BOMB-binding:
<context binds X → bomb> ... query using X

Condition benign-binding:
<matched context binds X → benign concept> ... same query using X
```

The token being probed should be surface-identical across the pair.

Do not allow label to be trivially reconstructed from:

- sequence length;
- number of demonstrations;
- codeword identity;
- position;
- template;
- special-token differences.

Use paired data.

Create separate splits by:

- codeword;
- carrier/template;
- underlying harmful instruction.

At least 20 independent pairs per layer/condition, preferably substantially more.

Primary probe positions:

1. query codeword;
2. last prompt / decision token.

Secondary descriptive analysis:

token-by-token Bombness map across the full prompt.

### 5.3 Compare Bombness against existing readouts

For every layer compute relationships between:

- Bombness probe logit;
- forced-choice `p_concept`;
- existing concept direction;
- `d_Direct`;
- `d_DS`;
- refusal direction.

Compute per-layer cosine geometry between probe normal and:

- concept direction;
- refusal direction;
- `d_DS`.

Expected useful result:

Bombness should align with concept identity but remain largely orthogonal to refusal.

If it instead primarily aligns with refusal, stop and understand the confound before behavioral claims.

### 5.4 Probe controls

Required:

**Label-shuffle control** — AUC ≈ chance.

**Random-direction control** — same dimensionality/norm.

**Position-only baseline** — Can position predict the label?

**Length-only baseline** — Can sequence length predict the label?

**Token-identity baseline** — Can the surface codeword alone predict the label?

**Template-only baseline** — Can prompt template predict the label?

**Cross-codeword transfer** — Train without CARROT, test CARROT.

**Cross-template transfer** — Train on templates A/B, test C.

**Neutral/no-binding condition** — Bombness should not spontaneously rise just because the word is unusual.

> **GATE 1 — Probe validity**
>
> The contextual Bombness probe passes only if:
>
> 1. held-out discrimination is clearly above chance;
> 2. the effect transfers to held-out codewords/templates;
> 3. trivial position/length/token controls cannot explain it;
> 4. result reproduces on both dev and frozen holdout;
> 5. its geometry is interpretable relative to the known concept/refusal directions.
>
> If this gate fails, do not use Bombness as a mechanistic variable.

---

## 6. PHASE 2 — BUILD AN INDEPENDENT REFUSAL / COMPLIANCE READOUT

We already possess a causally validated refusal direction.

Do not replace it.

Instead use two parallel quantities:

### 6.1 Causal refusal axis

Freeze the existing validated refusal direction.

For Llama, use the correctly indexed validated direction/layer from the authoritative artifact.

Do not silently refit it on new evaluation data.

This remains the primary causal coordinate.

### 6.2 Outcome-state probe

Train an independent pre-generation linear classifier on train-only examples to predict downstream behavioral class from the decision-token hidden state.

Prefer a 3-class formulation:

- REFUSAL
- MALICIOUS / HARMFUL COMPLIANCE
- OTHER / BENIGN MISUNDERSTANDING

Do not throw "other" examples away merely to make the classifier cleaner.

A binary refusal-vs-malicious analysis may be reported secondarily.

Cross-validate on train/dev.

Freeze before holdout.

Call the relevant derived scores:

- Refusalness
- Complianceness

Compare them to the existing refusal-axis projection.

The purpose is:

- independent measurement;
- paper-style probability-like readout;
- **not** a replacement causal claim.

> **GATE 2**
>
> Proceed if:
>
> - outcome probe predicts held-out behavior above trivial baselines;
> - existing refusal direction remains the better-supported causal quantity;
> - probe and causal direction have sensible but non-identical geometry.

---

## 7. PHASE 3 — ROLE-PAPER-STYLE LATENT-STATE EXPERIMENTS

Now apply Bombness and Refusalness to actual Doublespeak.

The key experiment should be **pre-generation**.

For every matched prompt and every layer, conditions:

1. Direct harmful;
2. Neutral codeword;
3. Doublespeak;
4. Benign-remap;
5. shuffled control where available;
6. unrelated control where available.

Do not claim behavioral results for shuffled/unrelated merely because these conditions existed in old datasets. Actually run them if they are used in the new behavioral analysis.

### 7.1 Layer trajectories

Measure:

- Bombness;
- Carrotness;
- refusal-axis projection;
- Refusalness;
- Complianceness;
- forced-choice `p_concept`.

Plot from embedding → final layer.

Main questions:

- **Q1** When does Doublespeak become BOMB-like?
- **Q2** When does refusal suppression begin?
- **Q3** Which happens first?
- **Q4** Are they coupled item-by-item?
- **Q5** Do successful and failed jailbreaks differ more strongly in Bombness or Refusalness?

Do not interpret the layer at which a probe is maximally readable as the causal write layer.

We already know readout ≠ mechanism.

### 7.2 Paper-style confusion quantiles

On held-out attacks:

rank prompts by pre-generation Bombness. Compute attack success by quantile.

Separately rank by refusal suppression / Complianceness. Compute attack success by quantile.

Use bootstrap CIs.

But this is descriptive. The important test is the joint model.

### 7.3 Joint predictive model

Fit on train/dev only:

```
success ~ Bombness + Refusalness + Bombness×Refusalness + baseline difficulty
```

Use frozen pre-registered layers/positions.

Potential baseline difficulty terms may include:

- Direct baseline outcome;
- baseline refusal projection;
- instruction category.

Do not add features opportunistically after reading holdout.

Compare nested models:

- A. Bombness only
- B. Refusalness only
- C. Bombness + Refusalness
- D. Bombness + Refusalness + interaction

Report:

- cross-validated AUC;
- held-out AUC;
- log-loss;
- coefficient CIs;
- incremental predictive value.

The scientifically interesting result would be:

> Bombness rises strongly under Doublespeak but contributes little additional behavioral prediction after conditioning on refusal state.

That would provide a clean latent-state version of our current causal dissociation.

But do not assume it.

### 7.4 Mediation-style observational decomposition

Test the candidate DAG:

```
Doublespeak → Bombness → refusal suppression → behavior
```

versus:

```
Doublespeak → Bombness
```

and independently:

```
Doublespeak → refusal suppression → behavior
```

Our existing causal work predicts the parallel-path model.

Use observational mediation only as descriptive support.

The causal answer comes from Phase 4.

> **GATE 3**
>
> Write a frozen intermediate report:
>
> ```
> reports/LATENT_STATE_PREDICTION_REPORT.md
> ```
>
> before starting probe-direction behavioral intervention.

---

## 8. PHASE 4 — CAUSAL INTERVENTIONS ON BOMBNESS

This is the most important phase of the sprint.

The new paper shows that a latent confusion measure tracks attack success.

Our contribution should ask:

> Can directly manipulating that latent identity state change behavior?

Probe accuracy alone is not enough.

### 8.1 Define the intervention directions

At each candidate layer derive:

- `v_bomb`
- existing `v_refusal`

Construct:

- `v_bomb_perp_refusal`
- `v_refusal_perp_bomb`

using explicit orthogonalization.

Also construct:

- norm-matched random direction;
- covariance-matched random direction where practical.

Always report the cosine before and after orthogonalization.

### 8.2 Natural-range calibration

Do not repeat the old mistake of relying on huge arbitrary α where random directions also cause large effects.

Define primary dose in natural state units.

For example calibrate against the observed train distribution:

- fraction of Direct↔Neutral concept-state gap;
- or empirical standard deviation of projection.

Pre-register a modest grid such as:

```
0, 0.25, 0.5, 1.0 × natural gap
```

A larger off-manifold stress dose may be run separately but cannot establish specificity.

Primary claims must come from doses where:

- completions remain coherent;
- random control is not behaviorally disruptive;
- projection remains near the natural activation range when possible.

### 8.3 Manipulation-check experiment

Before generation, intervene on Bombness.

Candidate sites:

**A. Query codeword** — primary concept-specific location.

**B. Decision token** — tests whether a downstream Bombness state can matter even after the concept circuit has completed.

**C. All codeword occurrences** — only after A/B and only if necessary.

For each dose measure:

- Bombness;
- forced-choice `p_concept`;
- refusal projection;
- Refusalness.

The manipulation check passes only if the Bombness intervention actually shifts:

- Bombness;
- preferably `p_concept`;

while the matched random direction does not.

If Bombness does not move, do not run an expensive behavioral generation and conclude "no causal effect."

### 8.4 Behavioral Bombness necessity

In Doublespeak prompts:

subtract / neutralize Bombness while preserving refusal as much as possible.

Measure:

- binary StrongREJECT ≥0.5;
- continuous StrongREJECT;
- refusal rate;
- empty/degenerate rate;
- concept readout.

Primary comparison:

> Bombness ablation vs matched random

Secondary:

> Bombness⊥refusal ablation vs matched random.

If concept readout collapses but ASR stays unchanged: that is a powerful replication of the epiphenomenal-concept conclusion using an entirely different intervention family.

### 8.5 Behavioral Bombness sufficiency

Start from a non-jailbreaking state such as Neutral or Direct/refusing, depending on the exact causal question.

Increase Bombness.

Ask:

> Does making CARROT internally more BOMB-like cause harmful compliance?

Required comparison:

- Bombness steering;
- random steering;
- refusal suppression positive control.

Expected possible outcomes:

**Outcome A** — Bombness rises, `p_concept` rises, ASR unchanged. → strong representation≠behavior result.

**Outcome B** — Bombness raises ASR only when refusal is simultaneously suppressed. → concept representation is conditionally causal, not globally epiphenomenal.

**Outcome C** — Bombness alone changes ASR specifically. → our current model is incomplete; follow the causal pathway.

### 8.6 2×2 causal factorial — highest-value experiment

Run:

|                | Refusal intact | Refusal suppressed |
| -------------- | -------------- | ------------------ |
| Bombness low   | cell 1         | cell 2             |
| Bombness high  | cell 3         | cell 4             |

Use orthogonalized interventions so that the concept and refusal manipulations are as independent as possible.

Primary endpoints:

- ASR;
- refusal rate;
- Bombness;
- refusal projection.

Estimate:

- main effect of Bombness;
- main effect of refusal;
- interaction.

This is the causal analogue of the paper's "latent confusion predicts success" result.

It is probably the single most paper-valuable experiment in this plan.

> **GATE 4 — Causal latent-state result**
>
> A Bombness behavioral claim is allowed only if:
>
> 1. manipulation check succeeds;
> 2. random controls pass;
> 3. coherence remains acceptable;
> 4. effect is reproduced on held-out data;
> 5. paired statistics support the stated effect or bound.

---

## 9. PHASE 5 — COMPONENT-RESTRICTED / PROBE-MEDIATED PATCHING

Use the learned directions to revisit our existing path-patching results more cleanly.

Do not remap the entire old circuit again.

Instead decompose the donor activation difference into:

- Bombness component;
- refusal component;
- orthogonal remainder.

For matched DS↔Direct or DS↔Neutral pairs:

```
Δh = Δh_bomb + Δh_refusal + Δh_other
```

Patch the components separately.

At candidate bands:

- concept write region L8–L11;
- refusal onset around L13–L18;
- decision region L18–L22.

Questions:

- **Q1** Which component mediates `p_concept`?
- **Q2** Which component mediates refusal projection?
- **Q3** Which component mediates behavior?
- **Q4** Does the orthogonal remainder contain additional behavioral signal?

This creates a much sharper causal decomposition than another generic residual patch.

Use:

- component patch;
- complement patch;
- self patch;
- random component;
- full donor patch.

At least 20 matched examples per tested layer/window.

Do not sweep 32×32 components blindly.

Use existing causal bands to keep this hypothesis-driven.

---

## 10. PHASE 6 — CLOSE THE MOST IMPORTANT EXISTING MISSING CONTROL: D3

The prior sprint's strongest hierarchy is currently:

```
activation intervention > continuous input steering > discrete tokens
```

but the activation intervention has a much broader scope than the 16-token soft prompt.

This is a confound.

Run the missing scope-matched activation control D3.

### 10.1 Scope-match activation to the soft prompt

Match as closely as possible:

- same 16 input positions;
- same target layer / coordinate;
- comparable norm/budget;
- same evaluation prompts;
- same objective direction.

Compare:

1. activation intervention;
2. continuous soft prompt;
3. discrete GCG;
4. matched random control.

This is a reviewer-critical control.

Primary question:

> Does activation-space control remain substantially stronger when it receives the same positional budget as the input attack?

### 10.2 Confirm the continuous dose properly

The previous successful continuous dose `budget_rel=0.10` was selected after inspecting test.

Therefore it is exploratory.

Freeze exactly that dose.

Do not retune it.

Run it on the untouched confirmatory split selected for this sprint.

Minimum 3 seeds.

Report:

- ASR;
- refusal rate;
- projection;
- coherence;
- random control.

If it replicates, the continuous-control headline becomes confirmatory.

### 10.3 Actually generate from the rounded continuous solution

Previous work showed only ~5.7% projection retention after rounding a simplex solution to discrete tokens.

But behavior after rounding was never generated.

Run the missing experiment.

For each continuous optimized prompt:

1. evaluate continuous state;
2. round/project to nearest valid discrete tokens using the pre-registered rule;
3. generate;
4. score behavior;
5. compare internal projection and ASR.

This directly tests whether the continuous→discrete gap appears at:

- representation;
- behavior;
- or both.

---

## 11. PHASE 7 — COMPLETE THE PHI CROSS-FAMILY CLAIM

Do not currently say that the full concept-vs-refusal dissociation has replicated on Phi.

The refusal half has. The concept half has not.

Run the missing Phi concept intervention.

Required:

- Phi-4-mini-reasoning;
- concept ablation;
- count-matched / norm-matched random control;
- concept manipulation check;
- behavior;
- refusal projection.

Use at least 20 valid examples; use more if power analysis requires it.

If the concept manipulation specifically changes `p_concept` while failing to specifically alter behavior, then the full concept-vs-refusal dissociation is supported on a third family.

If floor/ceiling prevents an informative concept test, report it as underpowered rather than "replicated."

---

## 12. PHASE 8 — CROSS-MODEL ROLE-PROBE REPLICATION

Only after the Llama probe method passes.

Replicate the probe framework on:

1. Qwen3-14B;
2. Phi-4-mini-reasoning.

Do not immediately perform a 32-layer exhaustive causal sweep on every model.

First ask:

- can contextual Bombness be decoded?
- does Doublespeak raise it?
- is it orthogonal/separable from refusal?
- which one predicts behavior?

Use model-specific validated refusal layers.

Compare normalized depth, not raw layer number alone.

Interesting possible result:

> Semantic identity confusion is a cross-family property, while the behaviorally relevant safety-control state differs by model.

That would be stronger than merely reproducing Llama layer numbers.

---

## 13. PHASE 9 — ONLY THEN TEST A NEW MECHANISM-DERIVED ATTACK OBJECTIVE

Do not immediately turn Bombness into GCG.

We already learned that:

> decodable + causal activation direction ≠ useful discrete objective.

Therefore a new objective gets promoted to GCG only if it passes all of:

1. reliable held-out probe;
2. behavioral causal intervention;
3. continuous-input controllability;
4. specificity vs random;
5. position/index audit.

If Bombness is behaviorally epiphenomenal, do not optimize Bombness for attack ASR.

That negative is the result.

### 13.1 If a new causal state emerges: exact-state objective

If the dual-probe analysis identifies a new causal state beyond the old scalar refusal direction, test a more faithful objective.

Prefer a state-matching objective over a single scalar.

Candidate:

match the successful pre-generation trajectory across the causal band, e.g.:

```
L13–L22 decision-token latent state
```

rather than merely maximizing one L18 projection.

Potential objectives:

- **O1 — refusal scalar** — existing baseline.
- **O2 — Bombness scalar** — only if Phase 4 says behaviorally causal.
- **O3 — joint latent state** — high Bombness + low Refusalness.
- **O4 — multi-layer successful-state matching** — distance to a successful continuous/causal donor trajectory.
- **O5 — state difference with generic-suffix component removed** — attempt to separate targeted state movement from the generic suppression profile already observed for random suffixes.

All objectives require a norm/covariance-matched random objective.

### 13.2 Candidate selection must use the objective

Add a regression test that verifies the mechanism objective influences both:

1. gradient proposal;
2. candidate selection.

This specifically prevents recurrence of P9.0.

### 13.3 GCG settings

For any confirmatory GCG comparison:

- suffix length 16 unless pre-registered otherwise;
- `suffix_placement=user`;
- `--no-filter-cand`;
- corrected hidden-state indexing;
- weighted candidate selection;
- minimum 3 seeds: 42/43/44;
- compute-matched candidate-forward budget;
- matched random direction/objective;
- best-so-far optimization statistics;
- never compare endpoint ratios.

Report per seed.

Do not summarize sign-inconsistent seeds with a misleading mean.

### 13.4 Exact hidden-state candidate scoring

Where computationally feasible, test whether candidate selection using the actual hidden-state objective improves over the first-order surrogate.

This specifically addresses the known fact that the linear surrogate collapses near real one-token step size.

Use the gradient only to generate candidates, then score shortlisted candidates by an exact forward pass on the actual state objective.

Compare against:

- normal first-order GCG;
- random objective;
- vanilla GCG.

This is more scientifically informative than simply increasing λ again.

### 13.5 MAC / TROPT

MAC/TROPT remains a genuine open item.

Do not write a new optimizer first.

Inspect whether the existing TROPT abstraction can express the new objective.

Reuse infrastructure where possible.

Run MAC/TROPT only after the causal-state gate passes.

If the state is not behaviorally causal, do not spend compute trying to make it an attack objective.

---

## 14. PHASE 10 — FIX THE BEHAVIORAL POWER PROBLEM

The n≈37 behavioral endpoint is too weak for many of our nulls.

We need a second harmful-instruction corpus if we want publication-grade claims about ~0.1 ASR effects.

### 14.1 Build a second corpus

Choose a second dataset with:

- enough harmful instructions;
- deduplicatable concepts;
- cluster-level splitting;
- usable targets;
- no overlap with current optimization pools.

Before model inference:

- normalize;
- deduplicate;
- cluster;
- construct train/dev/frozen holdout;
- verify no straddling;
- record source revision/hash.

Do not pool it with ClearHarm initially.

Treat it as an independent replication.

### 14.2 Prospective behavioral power

Use the actual discordant-pair rates from prior experiments to estimate n required for:

- ΔASR ≈ 0.10;
- ΔASR ≈ 0.15;
- the effect size relevant to the new experiment.

Target ≥80% power where practical.

If the available corpus cannot support that, state the maximum detectable/bounded effect before running.

Do not substitute a graded endpoint and claim it magically solves the sample-size problem unless prospective analysis shows it does.

### 14.3 Replicate only headline causal experiments

On the second corpus prioritize:

1. refusal causal intervention;
2. Bombness manipulation check;
3. Bombness behavioral intervention;
4. 2×2 Bombness×refusal factorial;
5. dual-probe prediction.

Do not rerun every circuit-anatomy experiment.

The purpose is external validity and power.

---

## 15. PHASE 11 — PAPER-HYGIENE TASKS FROM SECTION 20

These are secondary to the new causal probe experiment but should not disappear.

### 15.1 Complete currently running 600-step results

Finish/reconcile seeds 43 and 44 if they are still incomplete.

Use full-n only.

Do not interpret biased partial shards.

### 15.2 μ sweep for §20.1

The "78% cost" claim currently corresponds to a near-total pin.

Run the planned:

```
μ ∈ {0.1, 0.3, 1, 3, 10}
```

with matched seeds/budget.

Measure:

- degree of refusal pinning;
- task-objective progress;
- behavior where justified.

Goal: produce a dose curve of coordinate constraint vs optimization cost.

Do not call 78% "the cost of the coordinate" before this sweep.

### 15.3 2000-step point

Do not launch an expensive 2000-step extension merely because an old plan listed it.

First finish and analyze all 600-step seeds.

If 600 remains clearly saturated/null and the 2000-step experiment adds little scientific value, leave 2000 explicitly deferred.

If the final 3-seed 600 result leaves a meaningful unresolved compute-scaling hypothesis, pre-register the 2000-step extension and run it.

### 15.4 §20.5 / §20.6 / §20.9

Open the original Section 20 plan and recover their exact definitions.

Do not invent replacements based on the section numbers.

If §20.6 remains corpus-blocked, leave it blocked until Phase 10 supplies a second sufficiently large corpus.

Record the decision.

---

## 16. STATISTICAL CONTRACT

Use paired designs wherever prompts are matched.

### 16.1 Behavioral

Primary:

- exact McNemar;
- paired bootstrap 95% CI, preferably 10,000 resamples for final claims.

Also report:

- b/c discordant counts;
- n;
- baseline ASR;
- intervention ASR;
- ΔASR;
- refusal rate;
- empty rate.

For continuous StrongREJECT: paired bootstrap / appropriate paired nonparametric test.

### 16.2 Layer sweeps / probes

Use:

- ROC-AUC;
- bootstrap CI;
- balanced accuracy;
- cross-validated estimates;
- Wilcoxon where paired scalar layer effects are tested;
- Holm correction across layer/head families.

Never report p=0. Use the actual numerical resolution floor.

### 16.3 Probe comparisons

When comparing Bombness vs Refusalness, report:

- held-out AUC;
- ΔAUC;
- log-loss;
- coefficient CI;
- nested-model improvement;
- quantile plot.

Do not claim one representation "causes more" from AUC.

### 16.4 Equivalence/nulls

A non-significant p-value is not equivalence.

Use pre-specified equivalence bounds and report what the experiment can exclude.

At small n, say:

> "No effect larger than approximately X is supported/excluded under this design"

rather than:

> "No effect."

### 16.5 Multiple seeds

Present every seed.

No "mean positive" if signs disagree.

The recurring historical failure mode was: single-seed quantity promoted to a verdict.

Do not repeat it.

---

## 17. HIGH-VALUE FIGURES TO PRODUCE

Do not make dozens of plots. Aim for figures that directly support the causal story.

### Figure 1 — Dual latent-state trajectory

Layer on x-axis.

Curves:

- Bombness;
- refusal projection / Refusalness.

Conditions:

- Direct;
- Neutral;
- Doublespeak.

Show successful vs failed DS if readable.

Main visual question: Doublespeak becomes BOMB-like while simultaneously moving into a low-refusal state.

### Figure 2 — Which latent state predicts behavior?

Two panels:

- A. Bombness quantile → ASR
- B. Refusalness quantile → ASR

Plus nested-model summary.

### Figure 3 — Causal 2×2

Bombness low/high × refusal intact/suppressed.

Show ASR and manipulation-check projections.

This is likely the strongest figure.

### Figure 4 — Representation vs behavior

For Bombness intervention dose:

- x-axis: induced Bombness / concept-readout change
- y-axis: ASR

Overlay refusal intervention.

Potential key message: large semantic-state movement with little behavior vs modest refusal-state movement with large behavior.

### Figure 5 — Activation vs continuous vs discrete, budget matched

Only after D3. Same scope. Same target. Same approximate budget.

Compare:

- activation;
- soft prompt;
- rounded soft prompt;
- discrete GCG;
- random.

---

## 18. DECISION TREE / STOPPING RULES

Do not blindly execute every later attack experiment.

**Gate A — controlled Bombness probe**

- FAIL: Stop probe-derived attack work. Diagnose confound.
- PASS: Continue.

**Gate B — Doublespeak causes latent Bombness**

- FAIL: The role-confusion analogy is weak. Report it.
- PASS: Continue to prediction and causal manipulation.

**Gate C — Bombness manipulation works internally**

- FAIL: Cannot make a behavioral causal statement from this direction.
- PASS: Run behavioral intervention.

**Gate D — Bombness behaviorally causal**

- If NO but manipulation check is strong: this is a major positive scientific result — semantic identity confusion is real but behaviorally epiphenomenal. Do not waste compute optimizing Bombness.
- If YES: map interaction with refusal and consider attack objective.

**Gate E — new state continuously controllable**

Required before discrete optimization.

**Gate F — discrete objective beats matched random across ≥3 seeds**

Only then call it a mechanism-derived attack objective. Otherwise report an optimization negative.

---

## 19. PRIORITY ORDER

If compute/time becomes constrained, execute in this order.

**PRIORITY 0 — mandatory hygiene**

- reconcile live jobs;
- repair registry/deviation log;
- freeze threshold;
- pre-register new sprint.

**PRIORITY 1 — highest scientific value**

Controlled Bombness probe + Refusalness comparison. This directly imports the new paper's idea.

**PRIORITY 2 — highest causal value**

Bombness causal steering + 2×2 Bombness×refusal factorial. This is the core experiment.

**PRIORITY 3 — reviewer-critical existing gap**

D3 scope-matched activation control + confirm continuous dose.

**PRIORITY 4 — cross-family completeness**

Phi concept intervention + probe replication.

**PRIORITY 5 — power**

Second corpus + headline causal replication.

**PRIORITY 6 — attack objective**

Only if a new behaviorally causal state passes the gates.

**PRIORITY 7 — remaining Section 20 compute**

μ sweep is useful. 2000-step GCG is low priority unless the 600-step final state motivates it.

---

## 20. REQUIRED DELIVERABLES

At sprint completion create/update:

**Planning / provenance**

- `configs/manifests/role_probe_sprint_v1.json`
- `docs/ROLE_PROBE_NEXT_SPRINT_EXECUTION_LOG.md`
- `EXPERIMENT_REGISTRY.csv`
- `BUG_AND_DEVIATION_LOG.md`

**Main science**

- `reports/BOMBNES_PROBE_VALIDATION.md`
- `reports/DUAL_STATE_PREDICTION.md`
- `reports/BOMBNESS_CAUSAL_INTERVENTION.md`
- `reports/BOMBNESS_REFUSAL_FACTORIAL.md`
- `reports/PROBE_COMPONENT_PATCHING.md`
- `reports/D3_SCOPE_MATCHED_CONTROL.md`
- `reports/PHI_CONCEPT_COMPLETION.md`

Use a consistent spelling such as BOMBNESS in filenames if needed; do not maintain two aliases.

**Final synthesis**

Create:

```
docs/ROLE_CONFUSION_DOUBLESPEAK_CAUSAL_SYNTHESIS.md
```

It must have:

1. one-paragraph takeaway;
2. what was already known before this sprint;
3. what the role-probe paper motivated;
4. exact probe construction;
5. probe validity controls;
6. prediction results;
7. causal intervention results;
8. concept-vs-refusal dissociation;
9. cross-model status;
10. attack-objective implication;
11. limitations/power;
12. what is still not established;
13. ranked next steps.

**Claim audit**

Create:

```
reports/ROLE_PROBE_CLAIM_AUDIT_TABLE.md
```

For every headline claim include:

- claim;
- source artifact;
- script;
- n;
- split;
- seeds;
- effect;
- CI/p;
- control;
- status: VERIFIED / REPORT-ONLY / UNDERPOWERED / SUPERSEDED / WITHDRAWN / BLOCKED.

---

## 21. FINAL INDEPENDENT AUDIT

Before declaring the sprint complete, run an independent adversarial audit.

The auditor should not trust summaries. It must reopen raw artifacts and recompute the load-bearing numbers.

Specifically audit:

1. Bombness probe has no trivial token/position leakage.
2. CARROT was genuinely held out where claimed.
3. no test tuning.
4. all layer indexing.
5. orthogonalization math.
6. α/dose sign.
7. random controls.
8. StrongREJECT threshold.
9. paired denominators.
10. 2×2 factorial estimands.
11. GCG candidate selection if any attack objective is run.
12. all seed coverage.
13. all new output dirs registered.
14. all deviations logged.
15. no run directories were overwritten.

If a report disagrees with raw data: fix the report, not the raw data.

---

## 22. THE PAPER-LEVEL QUESTION THIS SPRINT SHOULD ANSWER

Do not let the sprint become a generic probe benchmark.

The endpoint should be one of these two clear stories.

### Story A — likely given our current evidence

Doublespeak creates genuine semantic identity confusion: CARROT becomes internally BOMB-like before generation. But this semantic confusion is not the behavioral security failure. The model simultaneously enters a distinct refusal-suppressed state, and that state — not Bombness — predicts and causally controls jailbreak behavior. Thus latent-state poisoning contains separable representational and control components.

This would extend the role-confusion idea by showing that: being placed in an adversarial latent identity is not automatically the causal behavioral mechanism.

### Story B — if the new experiment surprises us

Bombness becomes behaviorally causal only under a low-refusal state, revealing a gated interaction between semantic interpretation and safety control.

That would mean the old "epiphenomenal concept circuit" conclusion was incomplete rather than wrong.

Either result is valuable.

What is **not** valuable is another correlation-only statement that "Bombness goes up during Doublespeak."

We already know the model computes the remapping.

The next sprint must determine what that computation actually does to behavior, and why.

---
---

# APPENDIX A — ROLE-CONFUSION CODE REVIEW

Review of the official implementation of *Prompt Injection as Role Confusion*
(Ye, Cui, Hadfield-Menell, ICML 2026) as the reference implementation for our
contextual-identity ("Bombness") probe work. Deliverable of §2A.2.

| | |
| --- | --- |
| Snapshot | `third_party/prompt_injection_role_confusion/` |
| Upstream commit | `ec333c40fd43fe991e1ebf66765051b6d7e35784` (`master`, 2026-05-31) |
| Provenance | `third_party/prompt_injection_role_confusion/SOURCE_INFO_LOCAL.md` |
| Reviewed | 2026-08-14 |
| Reviewer | main-loop read of the full source tree (110 files); all load-bearing code read end-to-end, not skimmed |
| Status | Code review complete. **No adaptation code written yet.** |

Everything below is sourced from the released code, not the paper prose. Where
the code and the paper's description of the method could plausibly diverge, the
code is treated as authoritative and the divergence is flagged in §A9.

## A1. Relevant upstream files and what each does

### A1.1 Core (load-bearing for us)

| File | Role |
| --- | --- |
| `demo/simple_test_helpers.py` | Self-contained version of the whole pipeline's plumbing: `ReconstructableTextDataset`, `stack_collate`, `convert_outputs_to_df_fast`, `run_and_export_states`, `label_gptoss_content_roles`. **This is the cleanest and most portable code in the repo.** |
| `demo/role-probe-demo.ipynb` | End-to-end minimal pipeline: load model → build role-rendered corpus → hook-based activation export → label tokens → fit per-layer probes → apply to a CoT-forgery example → plot token-wise CoTness. Contains the only architecture-agnostic extractor (`run_gptoss_custom`, hook-based). |
| `utils/probes.py` | Production versions of `run_and_export_states` (identical logic to the demo) and `run_projections` (probe → per-token role probabilities in long format). |
| `utils/dataset.py` | Production `ReconstructableTextDataset` (same as demo copy). |
| `utils/loader.py` | Model registry (HF id, architecture, attn impl, n_layers), tokenizer/model loading, and `load_custom_forward_pass` which **verifies the hand-written forward pass reproduces HF logits exactly** (`torch.equal`). |
| `utils/pretrained_models/*.py` | Per-architecture re-implementations of the decoder loop that expose per-layer `all_pre_mlp_hidden_states` and `all_hidden_states`. 11 architectures. **No Llama.** |
| `experiments/role-analysis/02-train-role-probes.ipynb` | The real probe-training experiment: corpus construction, hyperparameters, per-layer/per-role-space probe fitting, validation on real conversations, tagged/untagged/mistagged conditions. |
| `experiments/role-analysis/config/probe.yaml` | Per-model probe hyperparameters (`C`, `add_scaling`), sequence length, sample size, test prefix, role separators. |
| `experiments/cot-forgery-role-confusion/03-project-role-probes.ipynb` | Applies frozen probes to attack activations; labels which tokens are the injected span; emits token×role_space×layer projection table. |
| `experiments/cot-forgery-role-confusion/04-analyze-injection-probe-results.ipynb` | (R) The headline "role confusion predicts attack success" analysis: per-prompt CoTness → quantile → ASR with bootstrap CIs. |

### A1.2 Supporting

| File | Role |
| --- | --- |
| `utils/role_templates.py` | `render_single_message`, `render_mixed_cot`, `fold_cot_into_final`, `load_chat_template` — manual per-model role rendering. |
| `utils/role_assignments.py` | 89 KB of per-architecture token→role labelling from raw token streams. |
| `utils/substring_assignments.py` | `flag_message_types` — maps known message strings back onto token spans. |
| `utils/store_outputs.py`, `store_topk.py`, `memory.py`, `misc.py` | Dataframe conversion, MoE top-k capture, CUDA memory hygiene. |
| `utils/chat_templates/*.j2` | Corrected Jinja chat templates (8 models). |

## A2. Exact probe estimator

**Primary and only estimator: multinomial L2-regularized logistic regression, GPU (cuML).**

```python
# demo/role-probe-demo.ipynb, cell 15; experiments/role-analysis/02-train-role-probes.ipynb, cell 18
steps = []
if add_scaling:
    steps.append(('scaler', cuml.preprocessing.StandardScaler()))
steps.append(('clf', cuml.linear_model.LogisticRegression(
    penalty='l2', max_iter=5_000, linesearch_max_iter=100, fit_intercept=True, C=C)))
lr_model = sklearn.pipeline.Pipeline(steps)
```

Facts that matter:

- **Multiclass, not binary.** The probe is fit over a *role space* (an ordered
  tuple such as `('system','user','cot','assistant')`). The reported "CoTness"
  is the **softmax probability of the `cot` class**, so it is defined *relative
  to the chosen role space*. Changing the role space changes the number. There
  is no single "CoT direction" vector used anywhere.
- **`fit_intercept=True`**, so the probe is an affine classifier, not a pure
  direction.
- **Standardization is optional and model-specific** (`add_scaling`: true only
  for `gptoss-120b`, `glm-4.7-flash`). No other preprocessing — no centering, no
  norm-stripping, no whitening beyond that optional scaler.
- `C` is tuned per model over `[1e-4 … 1e2]` and stored in `probe.yaml`; the
  grid-search cell is **commented out** in the released notebook, so the shipped
  values are the record of the search, not a reproducible search.
- Only `predict_proba` is ever consumed downstream. `coef_` is **never** read
  anywhere in the repo (verified by grep).
- **Secondary estimator: none.** There is no difference-of-means variant, no
  linear-regression variant, no non-linear probe.

### Metrics

- Probe fitting reports **plain accuracy** (`lr_model.score`) and **log-loss**
  (`cuml.metrics.log_loss`), plus `acc_by_role` (confusion counts) and
  `acc_by_pos` (accuracy by token-position-within-segment).
- Downstream validation reports two things per (conv_type, role_space, layer, role):
  mean probability assigned to the true class, and hard argmax accuracy.
- **No ROC-AUC anywhere. No bootstrap CI on probe metrics. No calibration check.**
- The only bootstrap in the repo is in the R analysis notebook, on the
  CoTness→ASR curve (1000 resamples, 5th/95th percentile band).

## A3. Activation tensor convention — THE critical difference

**Upstream probes are fit on `all_pre_mlp_hidden_states[L]`, defined as:**

```python
# utils/pretrained_models/qwen3.py:87-93  (identical shape in all 11 arch files)
hidden_states = residual + attn_out            # resid_mid  (post-attention residual)
residual = hidden_states
pre_mlp = layer.post_attention_layernorm(hidden_states)   # <-- NORMALIZED
if return_hidden_states:
    all_pre_mlp_hidden_states.append(pre_mlp.reshape(-1, D).detach().cpu())
```

So `all_pre_mlp_hidden_states[L]` = **`post_attention_layernorm(resid_mid_L)`** —
the *RMSNorm-normalized, mid-block* residual stream: the literal input tensor to
layer L's MLP. Verified identical in `qwen3.py`, `qwen3moe.py`, `gptoss.py`,
`glm46v.py`, `glm4moelite.py`, `apriel.py`, `jamba.py` (`pre_ff_layernorm`),
`nemotron3.py` (`block.norm`), `olmo3.py`. The demo's hook
(`layer.post_attention_layernorm.register_forward_hook`, capturing `output`)
captures exactly the same tensor.

The repo *also* captures `all_hidden_states[L]` = post-block-L residual (raw),
but **it is never used for probing** — it exists only for the forward-pass
equality check.

### A3.1 Mapping to our convention

| | Upstream | Ours |
| --- | --- | --- |
| Probed tensor | `post_attention_layernorm(resid_mid_L)` | `hidden_states[L+1]` = post-block-L residual |
| Normalized? | **Yes** (RMSNorm + learned gain) | **No** (raw residual) |
| Position in block | mid-block (after attn, before MLP) | end-of-block |
| Norm information | destroyed by RMSNorm | preserved |
| Index alignment | upstream `all_hidden_states[L]` ≡ HF `hidden_states[L+1]` ≡ our layer L | — |

**Consequences we must handle (this is a first-class regression-test item):**

1. A direction fit in upstream's space is **not** in the same space as our
   validated refusal direction (`hidden_states[19]`, i.e. post-block-18 raw
   residual — `build_refusal_direction_llama.py:20`, `47_repr_toctou.py:12`).
   Cosines between a probe normal from upstream's space and our refusal
   direction are **meaningless without an explicit change of basis.**
2. RMSNorm is not a linear map (it divides by the per-token RMS). A hyperplane
   in normalized space pulls back to a *cone-like* region in raw residual space,
   not a hyperplane. Steering along a normalized-space normal is therefore not a
   well-defined residual-stream intervention.
3. Because RMSNorm removes norm, upstream's probe is **scale-invariant by
   construction**. Ours would not be. That is a genuine methodological
   difference, not a bug — and it is arguably a *feature* for probe validity
   (kills a "the adversarial span just has bigger activations" confound).

**Decision for our adaptation (pre-registered here, subject to Gate 1):** fit
the probe in **our** raw post-block residual space (`hidden_states[L+1]`), the
space our causal machinery already operates in, and additionally fit a
normalized-space variant as a robustness arm. Rationale: Phase 4 requires
*causally steering* the probe direction, and a direction is only steerable in the
space where our hooks write. Adopting upstream's space for the headline probe
would make the headline probe uninterventionable. The normalized variant is
retained because it is the faithful reproduction of their method and guards the
scale confound. This is a deliberate, logged deviation from upstream methodology
— see §A8 and the mapping table in §A11.

## A4. Which residual-stream location / layer selection

- Layers probed: `range(0, n_layers, 4)` when `n_layers >= 30`, else
  `range(0, n_layers, 2)`. A coarse sweep, not every layer.
- The headline analysis layer is **hardcoded**: `TEST_LAYER_IX = 12` in the demo
  and `test_layer_ix = 12` in the R analysis — the midpoint of gpt-oss-20b's 24
  layers. There is no principled selection procedure, and **no dev/holdout split
  behind that choice** (see §A9.3).
- `layer_ix = 0` is the pre-MLP state of the *first* block, i.e. one attention
  sublayer after the embedding — not the embedding itself. There is no
  embedding-layer probe. (The R analysis filters `layer_ix > 0` in one place,
  suggesting layer 0 was regarded as degenerate.)

## A5. Label construction and the controlled design

This is the methodological core worth importing.

### A5.1 Training corpus — "same text, different role"

```
raw text x  (C4 25% / Dolma3 75%, streamed, shuffled, truncated to seq_len)
   ↓
render x into EACH role slot:
   <system>x</system>, <user>x</user>, <tool>x</tool>, <cot>x</cot>, <assistant>x</assistant>
   ↓
each rendering is one sequence; every content token inherits the label of its slot
```

The confound control is exactly this: **the content is byte-identical across
classes; only the role wrapper differs.** The probe therefore cannot win by
learning topic, register, or vocabulary — the same C4 paragraph appears under
every label. It must learn the model's *contextually assigned* role state.

This is the property we want to replicate. Our analogue inverts which factor is
held fixed:

| | Upstream | Ours |
| --- | --- | --- |
| Held identical | the content text | the probed surface codeword |
| Varied | the role wrapper | the contextual binding of that codeword |
| Probe must decode | assigned role identity | assigned semantic identity |

### A5.2 Sample granularity

**One training sample = one token.** Not one sequence. Every content token of
every rendered sequence is a labelled row. `n_sample_size: 250` base texts × 5
roles × up to 1024 tokens ⇒ order 10⁶ token-samples.

Implications for us:

- Their effective n is huge at the *token* level but only 250 at the
  *independent-text* level. Their train/test split is by `prompt_ix`, which
  correctly prevents the same rendered sequence straddling — **but the same base
  text appears in 5 different `prompt_ix` values (once per role), and the split
  is over `prompt_ix`, not `question_ix`.** So the same C4 paragraph can be in
  train under `<user>` and in test under `<cot>`. Given the design that is
  arguably intended (it is the same content by construction), but it means the
  reported test accuracy is *not* a clean held-out-content estimate. Flagged in
  §A9.1.
- Token-level rows are massively non-independent within a sequence. Reported
  accuracies have no clustering correction. **We must not copy this.** Our
  statistical contract requires pair-level/cluster-level resampling.

### A5.3 Position handling

- `SKIP_FIRST_N = 32 if NESTED_REASONING else 0` — for reasoning models the
  first 32 tokens of each segment are dropped from probe training. This is an
  implicit acknowledgement that early-in-segment tokens carry role information
  from proximity to the role tag rather than from style.
- `acc_by_pos` (accuracy by `token_in_seg_ix`) is computed as a diagnostic, so
  position-dependence is monitored — but it is never turned into a formal
  position-confound control.
- The demo notebook explicitly notes that other architectures' role nesting
  "requires more complex constructions to **remove position bias** + ensure
  probe validity."

### A5.4 Controls actually present upstream

| Control | Present? |
| --- | --- |
| Same-content-different-role (topic confound) | **Yes** — the central design |
| Position-within-segment diagnostic | Partial (`acc_by_pos`, `SKIP_FIRST_N`) |
| Cross-model-conversation transfer | Yes (`alt_tagged`: haiku-4.5 / minimax-m2.1 / kimi-k2 conversations) |
| Tagged / untagged / mistagged conditions | Yes — the exogenous-role-variation design |
| Label shuffle | **No** |
| Random direction | **No** |
| Length-only baseline | **No** |
| Token-identity baseline | **No** |
| Template-only baseline | **No** |
| Held-out probe-training content | **No** (see §A9.1) |
| Calibration | **No** |

So of our Gate-1 control list (§5.4), upstream supplies roughly two of nine.
**We must add the rest ourselves.** Their design earns validity from the
same-content construction; ours cannot lean on that alone because our
manipulation is contextual binding, which necessarily changes surrounding text.

## A6. Token aggregation and the confusion measure

Per-token probabilities are aggregated to a per-prompt scalar by a **plain mean
over the tokens of the attack span**, at one layer:

```r
# 04-analyze-injection-probe-results.ipynb
filter(role == 'user' & base_message_type == 'forged_cot') %>%   # the injected span only
filter(role_space %in% c('user','assistant-cot')) %>%
filter(layer_ix == test_layer_ix) %>%
group_by(redteam_prompt_ix) %>%
summarize(cotness = mean(`assistant-cot`), userness = mean(`user`))
```

Note the two-level labelling that makes this work:

- `role` = the **architectural** role the tags declare (from `label_content_roles`).
- `base_message_type` = the **stylistic/source** identity (`forged_cot` for the
  injected paragraph, otherwise `= role`), assigned by locating the injected
  text within the token stream.

"Role confusion" is then: tokens whose `role == 'user'` but whose CoTness is
high. That two-key structure (declared identity vs. decoded identity) maps
directly onto our design: declared codeword (`CARROT`) vs. decoded semantic
identity (BOMB-like).

Span identification uses **exact substring matching** of known message text back
onto tokens, via char offsets (`utils/substring_assignments.py`,
`03-project-role-probes.ipynb` cell 25); for the chat case the forged-CoT span
is found by a heuristic — "user content after the last double newline"
(`dbl_here` / `after_last_para`). The heuristic is brittle; we do not need it
because we construct our prompts and know the codeword position exactly.

### The ASR analysis

```
per-prompt cotness → ntile(25) → ASR per quantile
→ 1000 bootstrap resamples of prompts → mean, 5th/95th percentile band
```

Correct in the sense of resampling at the prompt level. Two limitations: the
bins are recomputed inside each bootstrap replicate (so the band mixes bin-edge
noise with ASR noise), and it is purely descriptive — **no regression, no
nested-model comparison, no conditioning on any competing variable.**

## A7. Assumptions specific to their models

Things that do **not** transfer to Llama-3.1-8B-Instruct:

1. **Reasoning models with an explicit CoT channel.** Every supported model has
   a distinct `cot` role (Harmony `<|channel|>analysis`, or `<think>` tags).
   Their `cot` class only exists because the architecture exposes it. Llama-3.1
   has no CoT channel. Their probe's most interesting class has no Llama analogue.
2. **`tool` role** likewise depends on the template.
3. **No Llama loader.** `utils/loader.py` has 11 entries; none is Llama. We must
   write our own extractor (trivial with the demo's hook approach).
4. **MoE-specific machinery** (top-k experts, router logits, `set_experts_implementation('eager')`)
   is irrelevant to us — but the *reason* for the eager setting (non-deterministic
   GEMM kernels in transformers v5 MoE) is a good reminder to pin determinism.
5. **`attn_implementation='kernels-community/vllm-flash-attn3'`** for gpt-oss.
   Our project rule is bfloat16 + default SDPA on L40S. Their choice is not
   binding on us. Note their extraction is hook/loop-based and does **not**
   require eager attention (no attention-pattern intervention anywhere), so SDPA
   is safe for extraction. It would **not** be safe for the attention-level work
   in later sprint phases.
6. **`padding_side='left'` + `padding='max_length'`** — see §A9.2, this is a real
   hazard for us.
7. **Manual template rendering with `add_special_tokens=False`** and hand-written
   `test_prefix` strings per model, rather than trusting `apply_chat_template`.
   They also ship *corrected* chat templates (`utils/chat_templates/*.j2`)
   because the stock ones mishandle CoT round-tripping. Good practice; we should
   likewise verify Llama's template round-trips our rendered prompts.

## A8. Components we can reuse directly vs. must adapt

### Reuse essentially as-is (port, don't rewrite)

| Component | Source | Note |
| --- | --- | --- |
| `ReconstructableTextDataset` | `demo/simple_test_helpers.py:11` | Offset-mapping token reconstruction is genuinely useful for BPE and solves a real problem (mapping probe scores back to exact source substrings). Works with any fast tokenizer. |
| `stack_collate` | same, `:117` | Trivial, correct. |
| `convert_outputs_to_df_fast` | same, `:131` | Efficient logits→token-level df; the `logsumexp` trick for top-1 prob avoids materializing the softmax. |
| Hook-based extractor pattern | `demo/role-probe-demo.ipynb` cell 4 | `register_forward_hook` on a submodule + `finally: h.remove()`. Architecture-agnostic. We retarget the hook (see below). |
| `run_and_export_states` skeleton | `utils/probes.py:14` | The batch → token-df + stacked-hidden-states contract, with `attention_mask`-based pad filtering, and the batch-0 perplexity sanity print. |
| `run_projections` | `utils/probes.py:91` | Probe → long-format (sample_ix, target_role, prob). Clean. |
| Sequence-level (not token-level) train/test splitting | `get_probe_result` | The *idea* is right; our grouping key must be stricter (§A9.1). |
| Two-key labelling: declared role vs decoded identity | `03-project` cell 14 | The conceptual backbone we are importing. |
| Per-prompt mean-over-span aggregation → quantile → bootstrap ASR curve | `04-analyze` cell 19 | Reuse as our §7.2 descriptive figure. |

### Must adapt

| Component | Why |
| --- | --- |
| **Extraction target** | Retarget from `post_attention_layernorm` output to post-block residual (`hidden_states[L+1]`) to match our causal space. Keep the normalized variant as a robustness arm. §A3.1. |
| **Model loader** | No Llama entry. Use our existing `ds_common` / `pair_common` loading (bfloat16, SDPA, pinned revisions) rather than `utils/loader.py`. |
| **Padding** | Switch to right-padding or per-example forward passes; do not inherit left-pad + `max_length`. §A9.2. |
| **Role rendering** | Replace `render_single_message` / role space with our binding-context construction. Roles are irrelevant to us; the class label becomes contextual semantic identity. |
| **`label_content_roles` / `role_assignments.py`** | 89 KB of per-architecture tag parsing we do not need — we construct our prompts and know the codeword offsets. Replace with exact offset bookkeeping at build time. |
| **Sample granularity** | Token-level rows are fine for *fitting*, but every reported statistic must be resampled at the pair/cluster level, not the token level. §A5.2. |
| **Metrics** | Add ROC-AUC, balanced accuracy, bootstrap CIs, calibration; keep their accuracy/log-loss as secondary. |
| **Layer selection** | Replace the hardcoded midpoint with dev-set selection, frozen before holdout. |
| **Estimator** | cuML requires RAPIDS. Unless RAPIDS is already in our env, use `sklearn.linear_model.LogisticRegression` — same estimator, no GPU dependency, and our probe-fitting data volume does not need GPU. Keep `penalty='l2'`, `fit_intercept=True`, tune `C` on dev. Add difference-of-means as our pre-registered secondary estimator (§5.1) — upstream has no equivalent. |

### Do not reuse

`utils/openrouter.py` (API calls), the MoE/top-k capture path, the R plotting
stack, the CoT-forgery prompt generation, the agent ReAct loop, the
`forged_cot`-span heuristic, `utils/chat_templates/*.j2` (no Llama).

## A9. Discrepancies, hazards, and bugs found in the released code

Numbered for citation in `BUG_AND_DEVIATION_LOG.md`.

### A9.1 Train/test split does not hold out probe-training *content*

`get_probe_result` splits on `prompt_ix`, which is unique per (base text × role)
rendering. The same base C4/Dolma paragraph therefore appears in train (as
`<user>`) and in test (as `<cot>`). Reported test accuracy is held-out-*rendering*,
not held-out-*content*. For their claim (role is decodable) this is mostly
benign, since content is designed to be uninformative. It would be **fatal in our
setting**, where the binding context is the informative part.

**Action:** our split key must be the underlying item (codeword × template ×
harmful-instruction cluster), never the rendered prompt index. Cluster-disjoint,
as §3.5 already requires.

### A9.2 Absolute position ids ignore left padding

All custom forward passes do:

```python
cache_position = torch.arange(0, N)
position_ids   = cache_position.unsqueeze(0)
```

with `padding_side='left'` and `padding='max_length'`. RoPE positions are thus
assigned from the start of the *padded* buffer, so identical content sitting in
sequences of different unpadded length receives **different absolute positions**.
This matches stock HF behaviour when `position_ids` is not supplied (which is why
their `torch.equal` logits check passes) — it is an inherited HF quirk, not a
deviation they introduced. It is nonetheless a live hazard.

For upstream it adds noise. **For us it is a direct threat to Gate 1**: if the
BOMB-binding and benign-binding contexts differ in token length, the probed
codeword token sits at a different RoPE position in the two conditions, and the
probe can win on position alone. This is precisely the *absolute
position-index bug class* already logged twice in this project.

**Action (mandatory):** (a) length-match the paired contexts at the token level,
(b) pass explicit `position_ids` derived from the attention mask, or right-pad,
and (c) run the position-only and length-only baselines from §5.4 as blocking
Gate-1 controls, not optional extras.

### A9.3 The headline layer is chosen without a holdout

`test_layer_ix = 12` is hardcoded, and the CoTness→ASR curve is computed on the
same data throughout. There is no train/dev/test discipline behind the layer
choice, the role-space choice, or the aggregation choice. The result is
descriptive and should be read as such.

**Action:** we select layer/position/role-space on dev only and freeze before
holdout. Our claim strength here can exceed theirs at no extra compute cost.

### A9.4 Key-name drift between notebooks (would crash on a clean run)

- `02-train-role-probes.ipynb` saves probes with key **`role_space`**.
  `utils/probes.py::run_projections` reads **`probe['role_space']`**. Consistent.
- `03-project-role-probes.ipynb` reads **`probe['roles']`** (cells 6, 18, 29) —
  a key that is never written. `04-analyze` likewise references a `roles` column
  produced from it.
- Path drift too: `02` writes to `experiments/role-analysis/outputs/probes/{m}.pkl`;
  `03` reads `experiments/role-analysis/probes/{m}.pkl`.

These are release/refactor artifacts (`roles` → `role_space` rename applied
unevenly). Harmless to us since we are not executing their notebooks, but they
confirm the released notebooks were not run end-to-end from a clean tree after
the final cleanup — so **the notebooks are a methodological reference, not a
runnable ground truth.** Reproduce the *method*, not the file layout.

### A9.5 Hyperparameter search is not reproducible

The `test_c` grid-search cell in `02-train-role-probes.ipynb` is commented out.
Only the resulting `C` values in `probe.yaml` survive. Their `C` for gpt-oss-20b
(`5e-3`) is very strong regularization; the notebook comment says `C` mainly
"modulates the extremeness of output probabilities" — i.e. it is effectively a
calibration knob for a measure that is then used as a continuous score. Since no
calibration check is performed, the absolute CoTness values are not calibrated
probabilities, only monotone scores.

**Action:** treat our probe output as a score; if we quote probability-like
numbers (Refusalness/Complianceness), either calibrate on dev or state plainly
that they are uncalibrated scores. Do not compare raw probe probabilities across
different `C` or different class-space sizes.

### A9.6 Token-level metrics reported without clustering correction

Accuracy/log-loss are computed over ~10⁶ non-independent token rows. No cluster
robust SEs, no CIs at all. Effective sample size is nearer 250 texts.

**Action:** all our probe metrics get pair-level bootstrap CIs.

### A9.7 `predict_proba` is class-space-relative

CoTness from a `(user, cot, assistant)` probe and from a
`(system, user, cot, assistant, tool)` probe are not comparable quantities. The
R analysis pins one role space (`assistant-cot,assistant-final,system,user`),
which is correct, but the constraint is implicit.

**Action:** fix our class space in the frozen manifest and never mix.

### A9.8 fp16 downcast before probing

Activations are cast bf16→fp16 for cuML/cupy compatibility
(`all_hs.to(torch.float16)`). bf16→fp16 narrows exponent range; a commented-out
`compare_bf16_fp16_batched` call suggests they checked it and moved on. Minor,
but we should fit in fp32 since we are not GPU-bound at probe-fit time.

### A9.9 No causal intervention anywhere in the repo — **confirmed by grep**

Searched the entire snapshot for `coef_`, `steer`, `ablat`, `patch`,
`intervent`, `orthogonal`, `register_forward_hook` used for writing. The only
hooks are read-only extraction hooks in the demo. `coef_` is never accessed.

**This is the single most important finding for our positioning.** The
role-confusion contribution is *measurement plus correlation*: a validated probe,
plus the observation that probe-measured confusion tracks attack success
pre-generation. It contains **no test of whether moving the latent role state
changes behaviour.**

Our Phase 4 (Bombness necessity/sufficiency) and §8.6 (Bombness × refusal 2×2
factorial) are therefore genuinely novel relative to this work, and our existing
representation≠behavior dissociation is exactly the confound their design cannot
rule out: a latent state can track attack success without causing it. That
framing should be explicit in the synthesis document.

### A9.10 Paper-vs-code divergences

The released code answers the questions the prose leaves open; where prose was
consulted, no contradiction was found, but the following are *underdetermined by
the paper and settled only by the code*: the probed tensor being
post-attention-**layernormed** rather than raw residual; the probe being
multiclass-softmax rather than a direction; the per-token (not per-sequence)
sample granularity; and the aggregation being an unweighted mean over span
tokens at a single hardcoded layer. Anyone reading only the paper would likely
implement all four differently.

## A10. Implications for our Bombness design (carried into Phase 1)

1. **Keep the "hold one factor byte-identical" trick.** Their validity comes from
   it. Ours must hold the probed codeword token surface-identical across the
   pair, with the binding context as the only manipulated factor.
2. **Adopt the two-key labelling.** Declared identity (`CARROT`) vs decoded
   identity (BOMB-like) is the exact analogue of declared role vs decoded role,
   and it is what makes "confusion" measurable rather than tautological.
3. **Do not adopt their probe space.** Fit in our raw residual space so Phase 4
   steering is well-defined; carry the normalized variant as robustness. §A3.1.
4. **Do not adopt their split.** Cluster-disjoint on item, not on rendering. §A9.1.
5. **Length-match pairs and control position explicitly.** §A9.2.
6. **Add the seven missing controls.** §A5.4.
7. **Their result is our null hypothesis, not our conclusion.** "Bombness rises
   under Doublespeak and correlates with success" would reproduce their finding
   and tell us nothing new. The sprint's value is entirely in the causal arm.

## A11. Upstream → Our Implementation Mapping

Deliverable of §2A.9. Planned mapping, to be updated with concrete file/line
references as each component lands. Target layout
(`doublespeak_causality/src/probes/`) does not exist yet — nothing written.

| Our component | Upstream reference | Reused / adapted / rewritten | Reason |
| --- | --- | --- | --- |
| `probe_dataset.py` — paired binding-context construction | `02-train-role-probes.ipynb` cell 11 `build_sample_seqs`; `demo` cell 7 | **Adapted (structure only)** | Keep the "one base item → N label-variants, content held fixed" generator shape; replace role rendering with binding-context rendering. Add length-matching and codeword-offset bookkeeping upstream has no need for. |
| `probe_dataset.py` — tokenized dataset + token reconstruction | `demo/simple_test_helpers.py::ReconstructableTextDataset`, `stack_collate` | **Reused** (ported, MIT header) | Offset-mapping reconstruction is correct and non-trivial; solves BPE→substring mapping we need for token-wise Bombness maps. Change: right-padding / explicit `position_ids`. |
| `activation_extraction.py` — forward pass + hidden-state export | `demo/role-probe-demo.ipynb` cell 4 (hook pattern); `utils/probes.py::run_and_export_states` | **Adapted** | Keep hook pattern and the batch→(token_df, stacked_hs) contract incl. pad filtering and the batch-0 PPL sanity check. **Retarget hook to post-block residual** (§A3.1); add normalized-space arm; load model via our existing loader (bf16/SDPA/pinned revision), not `utils/loader.py` (no Llama). |
| `contextual_identity_probe.py` — probe fitting | `demo` cell 15 / `02-train` cell 18 `fit_lr`, `get_probe_result` | **Adapted** | Same estimator family (L2 logistic, `fit_intercept=True`, optional scaler) and same fit-per-layer loop. Swap cuML→sklearn (no RAPIDS dep, fp32); **replace split key** (§A9.1); add ROC-AUC / balanced acc / bootstrap CIs; add difference-of-means secondary estimator (no upstream equivalent). |
| `probe_projection.py` — applying probes to new activations | `utils/probes.py::run_projections`; `03-project` cell 18 | **Reused** (ported) | Clean and correct; long-format output is the right shape for our per-layer/per-condition analysis. |
| Token aggregation → per-prompt score | `04-analyze` cell 19 (`mean(prob)` over span) | **Reused (as descriptive arm)** | Direct analogue for our §7.2 quantile figure. Our primary endpoints use pre-registered single positions (query codeword, decision token) instead, since we know exact offsets. |
| Layer sweep | `02-train` cell 19 (`range(0, n_layers, 4)`) | **Adapted** | Keep the per-layer independent-probe structure; probe **every** layer (Llama-8B is 32 layers, cost is trivial) and select on dev rather than hardcoding the midpoint (§A9.3). |
| Confusion-vs-ASR quantile curve + bootstrap | `04-analyze` cell 19 (R) | **Rewritten in Python** | Same estimand; fix bin edges outside the bootstrap; add the nested-model regression upstream lacks (§7.3). |
| Declared-vs-decoded identity labelling | `03-project` cell 14 (`role` vs `base_message_type`) | **Adapted (concept reused, code rewritten)** | The conceptual backbone. Their substring/heuristic span-finding is unnecessary for us — we build the prompts and record offsets at construction time. |
| Role/tag token labelling | `utils/role_assignments.py`, `utils/substring_assignments.py` | **Not reused** | 89 KB of per-architecture tag parsing solving a problem we do not have. |
| Causal intervention on the probe direction | **none exists upstream** (§A9.9) | **Novel** | Phases 4–5 of this plan have no upstream counterpart. This is our contribution, not an adaptation. |

## A12. Verdict

The released implementation is **worth adopting as the methodological starting
point** for probe construction, extraction plumbing, and the declared-vs-decoded
labelling idea. Its central design trick — hold one factor byte-identical, vary
only the factor of interest — is the right template for our contextual-binding
probe, and its plumbing (`ReconstructableTextDataset`, `run_and_export_states`,
`run_projections`) is clean, portable, and worth porting rather than rewriting.

It is **not** adoptable wholesale. Three things must change before it touches our
science: the probed tensor must move into our raw-residual causal space (§A3.1),
the split must become cluster-disjoint on item (§A9.1), and the position/length
confounds their design tolerates must become blocking Gate-1 controls (§A9.2,
§A5.4). Their statistical reporting (no CIs, token-level n, no holdout behind the
headline layer) is below our contract throughout and is not a model to follow.

Most importantly: the repo contains **no causal intervention of any kind**. The
role-confusion result is a measurement-plus-correlation result. Our sprint's
causal arm therefore does not duplicate it — and our existing
representation≠behavior dissociation is precisely the alternative their design
cannot exclude.

## A13. Next steps

1. Phase 0 governance repair (§4) — reconcile live SLURM jobs, registry,
   deviation log, threshold contract, freeze
   `configs/manifests/role_probe_sprint_v1.json`. **Gate 0 blocks all GPU
   science, including the §2A.5 sanity check.**
2. Small upstream sanity reproduction (§2A.5): a minimal role-probe run to
   validate we understand the pipeline before trusting our adaptation. Scope it
   to the demo tier, not the H200 full-reproduction tier. Must run under SLURM.
3. Then Phase 1 (§5) — implement `src/probes/` per the mapping table above, with
   the independent bug review (§3.9) before scale.
