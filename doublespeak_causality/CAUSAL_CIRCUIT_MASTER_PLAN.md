# Doublespeak Causal Circuit — Master Plan

**Project:** Mechanistic interpretability of Doublespeak / in-context representation hijacking
**Primary paper:** https://arxiv.org/pdf/2512.03771
**Primary model:** Llama-3.1-8B-Instruct (32 layers, 32 heads/layer), bf16 for all causal claims
**Status:** Planning document (written, not yet executed)

---

## Central research goal

Identify the complete causal circuit by which the model:

1. Reads codeword-to-concept bindings from the demonstrations.
2. Retrieves the relevant binding when it encounters the query codeword.
3. Writes the retrieved harmful concept into the residual stream.
4. Makes that concept available to downstream generation.
5. Avoids or bypasses the normal refusal mechanism.
6. Produces harmful behavior.

**Main hypothesis:** one or more attention heads retrieve the temporary binding from
the demonstrations, and one or more later MLPs write the retrieved concept into the
residual stream. This is a hypothesis to be tested exhaustively, not a result to
confirm by selecting a convenient layer/head.

---

## Absolute experimental coverage requirements (non-negotiable)

### 1. Every layer must be tested
- Test every transformer layer individually: `L0, L1, …, L31`.
- No early/middle/late-only windows for raw tables. Windows are secondary summaries only.
- Attention experiments: every head in every layer.
- MLP experiments: MLP in every layer.
- Path patching: every downstream MLP layer for every gated head/head-set.
- Other models: detect layer count dynamically, test every layer.

### 2. ≥ 20 unique examples per experimental cell
A **cell** = one specific combination of: dataset split · prompt condition · layer ·
head (when relevant) · patched activation type · patched token-position set ·
intervention direction · control/experimental condition · intervention strength (when relevant).

- Every cell ≥ 20 **unique** examples.
- Repeated seeds / generations / continuations / judge calls for one prompt do **not** count.
- Paired examples may be reused across matched cells, but each cell still needs ≥ 20 unique IDs.

### 3. Complete train/test separation
- Permanent split created **before** selecting layers/heads/paths/directions/thresholds/weights.
- ≥ 20 unique train/dev examples, ≥ 20 locked test examples → ≥ 40 unique overall.
- Split by underlying harmful intent / semantic cluster. Paraphrases, near-duplicates,
  demonstration variants, and same-base-request examples stay in the same split.
- Test split must **not** be used for: head/layer/path/MLP/strength selection,
  objective-weight tuning, threshold selection, #-demonstrations selection, early
  stopping, or deciding what is "interesting".
- After train freezes the hypothesis + config, repeat the **complete relevant layer
  sweep** on the locked test split. Never evaluate only the selected best layer on test —
  preserve the full all-layer test curve so layer-selection bias is visible.

### 4. No layer cherry-picking
Always save/report: all layers · all tested heads · all directions · all controls ·
all examples · failed and null results. Main table must not contain only the best layer.
When reporting a best layer/head, also report: its rank among all components · the full
distribution · neighboring layers · corrected significance · whether it replicates on test.

### 5. Primary causal conclusions require bf16
Quantization allowed only for exploratory scans/debug/runtime estimation. Any **causal**
result must be repeated on the primary unquantized/bf16 model with the exact successful
chat template and generation setup.

---

## Known findings that guide the new work

Existing experiments indicate:

1. Patching only the final query-codeword hidden state did **not** transfer the harmful
   interpretation into a neutral context.
2. Replacing that state with a neutral state did **not** remove the harmful interpretation
   from the full Doublespeak context.
3. → the final local codeword representation alone was neither necessary nor sufficient.
4. An explicit harmful-concept direction **could** causally alter interpretation.
5. Early concept installation + refusal ablation substantially increased harmful behavior.
6. The naturally observed Doublespeak−neutral direction had almost no causal effect.
7. A separate CoT-Hijacking success direction was predictive but neither necessary nor sufficient.
8. Optimizing a predictive internal projection did not reliably improve behavioral ASR.

**Therefore:**
- Patch **all** relevant codeword occurrences, not only the final one.
- Separate the **concept direction** from the **refusal direction**.
- Do not optimize a representation until causal interventions validate it.
- Focus primarily on attention-edge knockout, head activation patching, MLP patching, path patching.

---

## Phase 0 — Repository and result audit

Before any new experiment:

1. Locate exact scripts/configs/data/checkpoints/outputs that produced:
   - State × context transplant experiment.
   - Concept × refusal factorial experiment.
   - Explicit-concept vs Doublespeak-signature comparison.
   - Refusal-direction construction.
   - Forced-choice concept evaluation.
   - StrongREJECT behavioral evaluation.
   - Existing GCG and MAC/TROPT experiments.
   - Existing train/dev/heldout splits.
   - Existing TransformerLens or custom-hook code.
2. Reproduce all important presentation values from raw output files.
3. Create `reports/CAUSAL_PATCHING_AUDIT.md` including: repository map · exact model &
   tokenizer revisions · chat template · attention implementation · precision ·
   activation-hook definitions · current dataset structure · existing split structure ·
   run IDs · SLURM jobs · result provenance · known bugs/inconsistencies · presentation
   values that can and cannot be reproduced.
4. Create automated validation checks for: train/test overlap · duplicate intent clusters ·
   duplicate prompts · tokenization changes · missing codeword occurrences · multi-token
   codewords · failed generations · missing judge results · duplicate output rows ·
   incorrect layer/head indices · mismatched model/config hashes.

**Gate:** do not begin large experiments until existing positive controls reproduce.

---

## Phase 1 — ClearHarm dataset and locked split

Switch the primary harmful-query source to the exact ClearHarm version + prompt format
used by Matan's pipeline. Search repo for: ClearHarm ingestion · Matan's dataset files ·
TROPT/MAC configs · existing filters · dataset revision · evaluation conventions.

Create `data/splits/clearharm_doublespeak_v1.json`. Each example must include:
stable project example ID · original ClearHarm ID · harm category · semantic-intent
cluster · original request · target concept · codeword · tokenized target forms ·
tokenized codeword forms · Doublespeak prompt · neutral prompt · direct harmful prompt ·
benign prompt · shuffled-binding prompt · demonstration IDs · demonstration token
positions · query-codeword token positions · every codeword occurrence after chat
templating · split assignment · dataset revision · prompt-generation provenance.

- Primary minimum: 20 train, 20 locked test.
- carrot↔bomb: ≥ 20 train and ≥ 20 test if reported independently.
- Additional concept pairs: same requirement whenever a pair gets a separate statistical claim.
- Use single-token codewords/targets for primary analysis when possible; explicitly
  exclude or separately analyze multi-token cases.

---

## Phase 2 — Exact baseline reproduction and positive controls

### 2.1 Behavioral baselines (≥ 20 train, ≥ 20 test per condition)
1. Neutral prompt.
2. Benign codeword prompt.
3. Direct harmful prompt.
4. Doublespeak prompt.
5. Shuffled-binding prompt.
6. Unrelated-binding prompt.
7. Direct harmful + refusal ablation.
8. Doublespeak + refusal ablation.
9. Benign codeword + explicit-concept intervention.
10. Benign codeword + concept intervention + refusal ablation.

Measure: forced-choice harmful-concept probability · harmful−benign logit difference ·
full generation · StrongREJECT score · behavioral ASR · refusal rate · invalid/incoherent
generation rate.

> Direct harmful + refusal ablation must **not** receive a concept-direction intervention.
> It is the behavioral upper bound for refusal removal when the harmful concept is explicitly present.

### 2.2 Separate concept and refusal directions
Maintain separate objects: `concept_direction[L]`, `refusal_direction[L]`.
- `concept_direction[L] = mean(DIRECT) − mean(NEUTRAL)`
- `refusal_direction[L]` = constructed independently from harmful/refused vs harmless/compliant.
- Do **not** call `mean(DOUBLESPEAK) − mean(NEUTRAL)` a concept direction. Label it `doublespeak_signature[L]`.

For every layer report: norm · cosine similarity · covariance-adjusted similarity ·
projection distributions · intervention effects · cross-layer transfer effects.

---

## Phase 3 — Exhaustive all-occurrence residual-stream patching

Replace the earlier last-state-only experiment with complete layer×position analysis.

For every layer L0–L31, patch each activation location:
1. resid_pre · 2. attention output · 3. MLP output · 4. resid_post.

For every location, compare token-position sets:
1. Final query-codeword token only.
2. All subtokens of the query codeword.
3. Every query occurrence.
4. Each demonstration-codeword occurrence individually.
5. All demonstration-codeword occurrences together.
6. Query + all demonstration occurrences.
7. Every occurrence of the target concept in direct prompts.
8. Position-matched random tokens.
9. Same number of unrelated noun tokens.
10. Same number of punctuation tokens.

**Directions:**
- **Necessity:** patch neutral/shuffled activations into Doublespeak. *Does removing the
  attack-specific activation reduce harmful interpretation / behavioral ASR?*
- **Sufficiency:** patch Doublespeak activations into neutral/shuffled. *Does installing
  the attack activation create harmful interpretation / increase behavioral ASR?*

**Controls:** self patch · identity patch · no-op hook · shuffled donor · unrelated donor ·
random matched donor · norm-matched random vector · position-matched control · incorrect-layer
donor · adjacent-layer donor (where dims compatible).

Every layer × activation type × position set × direction × control cell: ≥ 20 train, ≥ 20 test
(after freezing config). Do not collapse layers into windows before saving full data.

**Outputs:** full 32-layer curves · per-example heatmaps · necessity & sufficiency curves ·
train-vs-test overlays · position-set comparisons · raw & normalized causal effects ·
behavioral & forced-choice results.

---

## Phase 4 — Exhaustive attention analysis

### 4.1 All-head attention scan (descriptive only)
For every layer & head, compute attention from destination = every query-codeword subtoken
to source = every demonstration-codeword occurrence. Also: query→surrounding demo tokens ·
query→target-concept tokens · query→random matched · query→punctuation · query→previous-token ·
query→same-token occurrences in neutral · query→shuffled bindings.

Run for: Doublespeak · Neutral · Direct · Shuffled · Unrelated · Benign.
≥ 20 train and ≥ 20 test per reported layer/head condition. Magnitude is descriptive, not causal.

### 4.2 Exact query→demonstration edge knockout
For every layer & head, knock out specifically the query-codeword destination →
demonstration-codeword source edges. Implementation must: modify attention scores/probs
before value aggregation · remove only selected edges · renormalize the remaining row
correctly · leave unrelated edges unchanged · support multiple query subtokens · support
every demonstration occurrence · support removing one occurrence at a time · support
removing all relevant occurrences together.

For every layer & head, test:
1. Knock out all query→demo-codeword edges.
2. Knock out each demonstration occurrence separately.
3. Knock out first demonstration occurrence.
4. Knock out final demonstration occurrence.
5. Knock out same number of random source edges.
6. Knock out surrounding-token edges.
7. Knock out punctuation edges.
8. Knock out query→codeword edges in neutral prompts.
9. Knock out reverse demonstration→query edges.
10. Knock out all outgoing query edges (broad degradation control).
11. Zero the complete head output.
12. No-op hook.

Each cell: ≥ 20 train, ≥ 20 locked test, every layer, every head.

Measure: forced-choice harmful-vs-benign probability · harmful−benign logit difference ·
Jacobian projection · Patchscopes score (if retained) · behavioral ASR · refusal rate ·
generation coherence · perplexity / next-token degradation · attention row normalization ·
magnitude of unrelated activation changes.

**A query→demo edge is causally relevant only when:** its removal reduces harmful
interpretation · random-edge removal does not reproduce the effect · complete-head
destruction is not the only effective intervention · effect not explained by global
degradation · predicted sign on train · replicates on locked test · CI excludes negligible effect.

### 4.3 Attention-edge sufficiency
For every layer & head, where feasible, test whether adding/transplanting the relevant
attention behavior is sufficient:
1. Patch Doublespeak attention patterns into neutral.
2. Patch Doublespeak Q into neutral.
3. Patch Doublespeak K into neutral.
4. Patch Doublespeak V into neutral.
5. Patch Doublespeak z/head output into neutral.
6. Patch query-position attention only.
7. Patch all codeword-position attention.
8. Patch complete pattern (positive control).
9. Patch shuffled/unrelated patterns (controls).

Every layer/head/activation-type cell: ≥ 20 examples per split.

---

## Phase 5 — Exhaustive activation patching of all attention heads

For every layer & head, patch: 1. attention pattern · 2. Q · 3. K · 4. V · 5. z ·
6. head result (resid coords) · 7. complete attention output for the layer.

Token positions: 1. query codeword only · 2. all query subtokens · 3. each demo codeword
separately · 4. all demo codewords · 5. all codeword occurrences · 6. all positions (broad
positive control) · 7. position-matched random.

Directions: necessity (neutral/shuffled/unrelated → Doublespeak), sufficiency (Doublespeak
→ neutral/shuffled).

Controls: self · identity · no-op · random head same layer · random head different layer ·
norm-matched random activation · shuffled donor · unrelated donor · neighboring token
positions · complete-head zero ablation.

Coverage: every layer, every head, every activation type, ≥ 20 train and ≥ 20 test per
frozen confirmatory cell. Full test sweep: at minimum repeat the complete z/head-result and
edge-knockout scans on all heads/layers. For Q/K/V/pattern, repeat the full all-layer test
sweep unless a documented compute failure makes it impossible (report the limitation, do not
silently reduce coverage).

Use **actual** activation patching for final claims. Attribution patching only as
ranking/diagnostic — it cannot replace exact activation patching.

---

## Phase 6 — Exhaustive MLP write-location analysis

For every layer L0–L31, inspect/intervene on: 1. MLP input · 2. normalized MLP input ·
3. MLP pre-activation · 4. activated neuron values · 5. MLP output · 6. residual before MLP ·
7. residual after MLP.

For every location, patch positions: 1. query codeword only · 2. all query subtokens ·
3. demo codewords individually · 4. all demo codewords · 5. every codeword occurrence ·
6. all positions (broad control) · 7. position-matched unrelated tokens.

Run necessity (neutral/shuffled → Doublespeak) and sufficiency (Doublespeak → neutral/shuffled).
Every layer × activation type × position set × direction: ≥ 20 train, ≥ 20 locked test.

For every layer, project the MLP residual update onto: explicit concept direction ·
Doublespeak signature · refusal direction · Jacobian harmful-vs-benign direction.

A write layer must satisfy more than a large projection — exact MLP intervention must change
a downstream concept or behavioral metric.

---

## Phase 7 — Head-to-MLP path patching

Proceed after the all-head scan identifies heads/head-sets with reproducible causal effects.
Do not select the final path from test results.

For each validated sender head at layer S, test every downstream receiver MLP at
`S, S+1, …, final`. Do not test only one middle-layer MLP.

For each sender-head → receiver-MLP pair, test:
1. Sender head result → MLP input.
2. Sender head result → MLP pre-activation.
3. Sender head result → MLP output.
4. Query-position path only.
5. All codeword-position path.
6. Direct residual path.
7. MLP-mediated path.
8. Sender head with receiver MLP patched.
9. Sender head patched while alternative attention paths held fixed.
10. Receiver MLP patched while sender head remains clean.

Controls: validated head → random MLP · random head → candidate MLP · random head → random
MLP · same-layer noncandidate head · norm-matched random path · shuffled donor · unrelated
donor · no-op path patch · self path patch.

Every sender-head × receiver-layer × path-definition × control cell: ≥ 20 train, ≥ 20 test
(after freezing candidate heads).

Outcomes: change in receiver MLP activation · concept projection · downstream residual
representation · forced-choice interpretation · behavioral ASR · mediation fraction · raw &
normalized path effect · coherence controls.

If no single head→MLP path explains the effect: test validated head sets · multiple-head →
every downstream MLP · multiple-head → multiple-MLP circuits · estimate cumulative mediation ·
report the mechanism as distributed. **Do not force a single-head explanation.**

---

## Phase 8 — Jacobian/projection readout across all layers

Implement the Jacobian/projection-matrix approach as replacement/complement to naïve logit
lens. For every layer, compute a layer-specific projection for `harmful-concept logit −
benign-codeword logit`. Use a calibration corpus that does not overlap train/test attack examples.

Compare at every layer: naïve logit lens · existing Patchscopes result · token-specific
Jacobian projection · tuned linear lens (if implemented) · actual forced-choice output ·
behavioral generation.

Analyze: layer-wise concept emergence · train/test stability · prompt-length confounding ·
token-position sensitivity · codeword-occurrence differences · correlation with exact
patching effects · correlation with edge-knockout effects · correlation with behavioral ASR.

Jacobian readout is descriptive until intervention in the corresponding coordinate changes output.

---

## Phase 9 — Intervention-strength sweeps

For every main causal intervention, dose-response sweep: concept-direction add · concept
removal · refusal removal · head-output patch interpolation · MLP-output patch interpolation ·
path-contribution scaling · attention-edge attenuation.

Strengths: `0.00, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00, 3.00`. Include negative strengths for
removal/signed directions where meaningful. Each layer × strength × condition: ≥ 20 examples.
A valid handle shows an ordered dose response, not one isolated successful coefficient.

---

## Phase 10 — Distill a causal optimization objective

Do not optimize a feature merely because it predicts success. An internal metric is eligible
only if: 1. changes under validated circuit intervention · 2. manipulating it changes harmful
interpretation · 3. necessity demonstrated · 4. sufficiency demonstrated (where feasible) ·
5. dose response exists · 6. replicates on ≥ 20 locked test examples · 7. random/unrelated
controls fail · 8. not general degradation · 9. distinct from global refusal removal ·
10. transfers across > 1 prompt/concept condition.

Candidate objectives: causally validated attention-head contribution · validated
query→demonstration retrieval contribution · validated MLP concept-write contribution ·
validated head→MLP path contribution · late harmful-concept Jacobian projection · a two-term
objective separating late concept writing from early refusal evidence.

Keep separately logged: `concept_objective`, `refusal_objective`, `retrieval_objective`,
`mlp_write_objective`, `path_objective`, `language_model_objective`. Do not merge concept and
refusal directions into one vector.

---

## Phase 11 — GCG and MAC/TROPT evaluation

Only after an objective passes the causal gate, integrate into GCG and MAC/TROPT. Compare:
1. No attack · 2. Standard Doublespeak · 3. Naïve GCG · 4. Existing MAC/TROPT ·
5. Refusal-suppression objective · 6. Doublespeak-signature objective (noncausal negative
control) · 7. Mechanistic objective only · 8. Standard + mechanistic · 9. Mechanistic +
refusal term · 10. Random-direction objective · 11. Wrong-layer objective · 12. Wrong-head
objective · 13. Wrong-path objective.

Hold constant: train/test examples · optimization steps · restarts · suffix length ·
candidate batch size · token budget · generation settings · judge · model · compute accounting.

**Primary success criterion:** the causally derived objective must improve held-out behavioral
ASR over a compute-matched naïve GCG or MAC/TROPT baseline. An increase in projection without
increased held-out behavioral ASR is a **null result**.

---

## Statistical requirements

Paired analysis across matched examples. For every all-layer experiment report: n per cell ·
#unique intents · mean · median · SD · bootstrap 95% CI · paired permutation test (where
appropriate) · binary ASR CI · multiple-comparison correction across layers/heads · effect
size · per-example results · train/test comparison · full layer curve.

Use **Holm** correction for predefined families: 32 layer comparisons · all heads within one
experiment · sender-head × receiver-MLP path families · multiple token-position variants.

Normalized causal effect: `normalized_effect = (intervention − corrupted) / (clean − corrupted)`.
Also report the raw effect. Handle near-zero denominators explicitly.

---

## Engineering requirements

Add tests confirming: no-op hooks reproduce baseline logits · self-patching reproduces source
output · alpha zero is exact no-op · all 32 layers included · all heads included · no layer
indices skipped · attention knockout modifies only requested edges · attention rows remain
normalized · every codeword occurrence detected · multi-token codewords handled or excluded
explicitly · token positions computed after chat templating · train/test IDs do not overlap ·
discovery scripts cannot read test split without an explicit final-evaluation flag · cached
activations match model/config hash · resume does not duplicate rows · every cell reaches
n ≥ 20 · missing cells fail aggregation loudly · judge failures recorded & retried · output
rows contain layer, head, example ID, split, condition, intervention metadata.

**Coverage validator** produces a table:
`experiment · split · layer · head · activation_type · position_set · direction · control ·
n_unique_examples · complete`. Run marked incomplete if any required cell has < 20 unique examples.

---

## SLURM execution strategy

Job arrays organized by: experiment · split · layer · head · activation type · position
condition · intervention direction · control condition.

Smoke tests first: 2 examples · 2 layers · 2 heads · no expensive judge unless required.
Then launch complete arrays. Before submission estimate: #cells · forward passes · backward
passes · GPU hours · storage · judge calls.

Do not reduce the 20-example requirement to save compute. Instead: cache clean activations ·
cache corrupted activations · reuse tokenization · batch compatible interventions · reuse
baseline generations · use forced-choice readouts during exhaustive scans · run full
behavioral generation for all decisive causal conditions · quantization only for exploratory ·
resume failed array jobs without rerunning completed cells.

**Project SLURM rules (from memory):** no SLURM dependencies · max 6 parallel jobs · no
trimming · L40S only · bf16 + default SDPA (do not disable flash) · GCG always `--no-filter-cand`.

---

## Required experiment matrices

Machine-readable manifests before launching jobs, in `configs/manifests/`:
`all_occurrence_patching.json` · `all_head_edge_knockout.json` ·
`all_head_activation_patching.json` · `all_layer_mlp_patching.json` ·
`head_to_all_mlp_path_patching.json` · `jacobian_all_layers.json` ·
`intervention_strength_sweeps.json`. Each enumerates every expected cell.

`scripts/validate_experiment_coverage.py` compares expected vs completed rows and fails if:
a layer is missing · a required head is missing · a control arm is missing · a split is
missing · a cell has < 20 unique examples · results contain duplicate example IDs within a cell.

---

## Go/no-go gates

- **Gate 1 — Reproduction:** do not interpret new mechanisms until existing presentation results reproduce.
- **Gate 2 — Exhaustive layer coverage:** do not report a patching/knockout experiment until all layers complete with n ≥ 20 per required cell.
- **Gate 3 — Attention causality:** do not begin objective design until an edge/head/head-set passes exact necessity tests vs matched controls.
- **Gate 4 — Write location:** do not claim an MLP writes the binding unless exact MLP patching changes downstream interpretation/behavior.
- **Gate 5 — Path mediation:** do not claim a head→MLP circuit from correlation alone; require path-patching across every possible downstream receiver layer.
- **Gate 6 — Objective:** do not optimize an internal signal until it has causal evidence, dose response, controls, locked-test replication.
- **Gate 7 — Behavioral improvement:** do not claim optimization success from an internal metric; require improved held-out StrongREJECT ASR vs compute-matched baseline.

---

## Required reports

```
reports/CAUSAL_PATCHING_AUDIT.md
reports/DATASET_AND_SPLIT_CONTRACT.md
reports/ALL_OCCURRENCE_PATCHING.md
reports/ATTENTION_EDGE_KNOCKOUT.md
reports/ALL_HEAD_ACTIVATION_PATCHING.md
reports/ALL_LAYER_MLP_PATCHING.md
reports/HEAD_TO_MLP_PATH_PATCHING.md
reports/JACOBIAN_READOUT.md
reports/CAUSAL_OBJECTIVE.md
reports/GCG_MAC_EVALUATION.md
reports/FINAL_CAUSAL_CIRCUIT_REPORT.md
reports/SLACK_UPDATE.md
```

Every report states: exact sample count · exact train/test split · model & revision · every
tested layer · every tested head (where relevant) · missing/failed cells · controls ·
statistical corrections · positive results · null results · remaining uncertainty.

---

## Final scientific deliverable — must answer

1. Which demonstration tokens provide the binding?
2. Which query→demonstration attention edges retrieve it?
3. Which heads are necessary?
4. Which heads/head-sets are sufficient?
5. At which layers is the binding first causally available?
6. Which MLP/MLP-set writes it?
7. Which head→MLP paths mediate the effect?
8. Is the mechanism localized or distributed?
9. How is the concept mechanism separated from refusal?
10. Does the causal mechanism generalize to locked test examples?
11. Can it be converted into a differentiable objective?
12. Does that objective improve held-out GCG/MAC behavioral ASR?

---

## Startup sequence

1. Repository audit.
2. Reproduction of existing positive controls.
3. Permanent ClearHarm train/test manifest.
4. Complete experiment-cell manifests.
5. Coverage-validation script.
6. Two-example smoke test of all-occurrence patching.
7. Two-example smoke test of exact attention-edge knockout.
8. Two-example smoke test of head activation patching.
9. Complete SLURM plan for all 32 layers and all heads.
10. Launch complete jobs only after smoke tests and coverage checks pass.

Continue autonomously through phases. Do not ask for confirmation between normal steps. Do
not stop after finding one promising layer/head — complete the full layer-wise analysis and
all required controls.

---

# Mandatory intervention granularities

Every principal patching, knockout, ablation, direction-intervention, and path-patching
experiment must run at **three distinct granularities**:

1. Every layer individually.
2. Every required multi-layer window.
3. All layers simultaneously.

A result at one granularity does not replace the others. Every cell at every granularity
uses ≥ 20 unique train and ≥ 20 locked test examples, paired across matched conditions when
possible. Repeated generations/seeds do not increase the unique-example count.

### Granularity A — Every layer individually
For N layers, test `L0 … L(N-1)` (Llama: L0–L31). Intervention applied only at the specified
layer; all others untouched. Required for: resid_pre · attention-output · individual-head
activation · attention-edge knockout · Q/K/V/pattern/z/head-result · MLP-input · MLP-output ·
resid_post · concept-direction add/remove · Doublespeak-signature add/remove · refusal
projection/ablation · Jacobian-coordinate · head-to-MLP path · strength sweeps.
Output: one result per layer · full curves · no omitted layers · ≥ 20 unique examples per
layer-specific cell per split.

### Granularity B — Canonical non-overlapping windows
For 32 layers: `early L0–L9`, `middle L10–L19`, `late L20–L31`. Also `early+middle L0–L19`,
`middle+late L10–L31`. Intervention applied simultaneously to all relevant components in all
layers of the window (e.g., concept-direction window adds layer-specific concept direction at
each layer; refusal window removes layer-specific refusal component at each layer; edge
window knocks out designated edge in each layer/head; MLP window replaces MLP output at every
layer; residual window replaces selected residual at every layer). Do not replace
layer-specific vectors with one copied vector unless separately labeled. ≥ 20 train, ≥ 20 test.

### Granularity C — Sliding contiguous windows
Widths `2, 4, 8`. For N layers and width W, evaluate every valid window `L0–L(W-1) …
L(N-W)–L(N-1)`. Apply intervention simultaneously at all layers inside the window. ≥ 20 train,
≥ 20 test per cell. Save every window, including nulls. Do not report only the best window.

### Granularity D — Cumulative prefix windows
`L0 · L0–L1 · L0–L2 · … · L0–L31`. For endpoint k, intervene jointly across L0–Lk. Reveals
whether an effect appears only after enough early computation is modified. ≥ 20 per split.

### Granularity E — Cumulative suffix windows
`L31 · L30–L31 · … · L0–L31`. For start k, intervene jointly across Lk–L31. Distinguishes
early retrieval · middle-layer writing · late representation carrying · late behavioral use.
≥ 20 per split.

### Granularity F — Mechanism-derived windows
After train-only individual-layer scans, define windows around contiguous regions with related
effects (retrieval window around attention-edge effects · write window around MLP-output
effects · late-use window around downstream behavioral effects). Rules: selected using
train/dev only · boundaries frozen before test · do not replace canonical/sliding windows ·
clearly labeled data-derived · evaluated on ≥ 20 locked test examples.

### Granularity G — All layers simultaneously
Run the same intervention jointly across L0–L31 (distinct required condition). E.g., patch
relevant activation at all layers · knock out relevant edge at all layers · patch every
corresponding MLP output · apply layer-specific concept direction at every layer · remove
refusal at every layer · patch all validated retrieval heads across all layers · intervene on
all codeword positions at all layers. Do not reuse one layer's vector across the model — at
each layer L use the activation/direction/projection/component defined for L. ≥ 20 train, ≥ 20 test.

### Required granularity comparison table
For every major intervention, one table containing: best individual layer · all individual
layers · canonical windows · sliding windows · cumulative prefixes · cumulative suffixes ·
mechanism-derived windows · all layers simultaneously. Report raw & normalized effects. Table
must answer: 1. Is one layer sufficient? · 2. Are multiple adjacent layers required? ·
3. Does effect grow monotonically with wider window? · 4. Does all-layer improve the effect? ·
5. Does all-layer damage coherence? · 6. Is an early/middle/late region necessary? · 7. Can a
narrow window reproduce the all-layer effect? · 8. Does the effect replicate on test?

### Granularity requirements by experiment

**Residual-stream patching** — for each of resid_pre / attention output / MLP output /
resid_post, run: every layer separately · canonical windows · sliding widths 2/4/8 ·
cumulative prefixes · cumulative suffixes · all layers. For positions: query codeword only ·
all query subtokens · each demo occurrence · all demo occurrences · query+demos · all codeword
occurrences · matched controls. Both necessity and sufficiency.

**Attention-edge knockout** — first every layer & head separately. Then window-level using
causally plausible head sets. For attention windows, do not assume head index h at different
layers is one shared head. Distinguish: (1) same-index exploratory window (apply head index h
at every layer in the window; label explicitly) · (2) candidate-head-set window (knockout to
all train-selected candidate heads inside the window) · (3) all-head window (remove only
target query→demo edges in every head in every layer of the window). Run each applicable form
for canonical / sliding / cumulative prefix / cumulative suffix / all layers. ≥ 20 per cell.

**Individual-head activation patching** — every head in every layer separately. Then candidate
head sets within each canonical window · within every applicable sliding window · in
cumulative prefixes · in cumulative suffixes · all validated heads across all layers. Also
matched random-head sets with the same #heads/layer and approx matched activation norms.

**MLP patching** — for every MLP layer individually: input · pre-activation · activated-neuron ·
output. Then apply the same MLP intervention jointly across canonical / sliding / cumulative
prefix / cumulative suffix / mechanism-derived write windows / all layers.

**Concept-direction intervention** — for every layer L use `concept_direction[L]`. Run each
layer alone · canonical · sliding · cumulative prefixes · cumulative suffixes · all layers.
On a window, apply the corresponding layer-specific direction at each layer. Compare positions:
query codeword only · all query occurrences · demo occurrences · every codeword occurrence ·
every token position (broad positive control).

**Refusal-direction intervention** — run refusal removal at each layer separately · canonical ·
sliding · cumulative prefixes · cumulative suffixes · all layers (to determine whether refusal
is concentrated or distributed). Keep refusal interventions separate from concept
interventions. Then factorial `concept granularity × refusal granularity`, comparing at
minimum: single concept layer × single refusal layer · concept window × refusal window ·
concept window × refusal all-layers · concept all-layers × refusal window · concept all-layers
× refusal all-layers. ≥ 20 per cell per split.

**Head-to-MLP path patching** — for each validated sender head, test every downstream receiver
MLP individually. Then MLP receiver windows: canonical · sliding · cumulative-suffix ·
mechanism-derived write · all downstream MLPs simultaneously. Sender granularities: one sender
head · all validated heads in one layer · validated heads within one retrieval window · all
validated retrieval heads across the model. Creates `sender granularity × receiver
granularity`. ≥ 20 per cell per split.

### Window controls
Every window intervention includes controls distinguishing a genuine distributed effect from
intervention magnitude: 1. same-width random layer window · 2. same-width shifted window ·
3. same #layers sampled non-contiguously · 4. same #random heads · 5. norm-matched random
directions · 6. same intervention at unrelated token positions · 7. shuffled-donor activation ·
8. identity/no-op · 9. individual layers composing the window · 10. all-layer intervention.
For a positive-effect window, explicitly test whether its effect exceeds: the best individual
layer inside it · the sum/expected combination of individual-layer effects · a random window
of the same width · a non-contiguous layer set of the same size.

### Interaction and synergy analysis
For window W with layers L1…Lk, compare `observed_window_effect` against `max individual-layer
effect`, `mean individual-layer effect`, `sum of individual-layer effects`, and the
independently predicted combined effect. Report whether the window is redundant · additive ·
sub-additive · super-additive/synergistic. Do not infer a distributed mechanism merely because
a wide window has a larger raw effect — control for the number and norm of interventions.

### Mandatory output visualizations
For every major patching/knockout family: 1. individual-layer line plot · 2. layer×head
heatmap · 3. fixed-window comparison · 4. sliding-window start×width heatmap · 5. cumulative-
prefix curve · 6. cumulative-suffix curve · 7. all-layers reference line · 8. train-vs-test
overlay · 9. intervention-vs-control overlay · 10. per-example distribution · 11. coherence/
degradation plot · 12. effect-vs-#intervened-layers plot. All plots include: #unique examples ·
CIs · split · intervention definition · model · token-position set · forced-choice vs behavioral.

### Coverage manifests (granularity-aware)
Every manifest row includes: `experiment · split · granularity_type · layer_start · layer_end ·
layer_list · window_width · head_list · activation_type · token_position_set ·
intervention_direction · intervention_strength · control_type · expected_unique_examples`.
Allowed `granularity_type`: `single_layer · canonical_window · sliding_window ·
cumulative_prefix · cumulative_suffix · mechanism_window · all_layers`.

Coverage validator fails if: any individual layer missing · any required canonical window
missing · any valid sliding window missing · any cumulative prefix missing · any cumulative
suffix missing · the all-layer condition missing · a required cell has < 20 unique examples ·
a control arm absent · test results exist for a configuration not frozen from train.

### Required scientific interpretation
For each intervention, the final report distinguishes:
- **Local causality:** one individual layer has a sufficient effect.
- **Distributed contiguous causality:** a contiguous window has an effect not reproduced by one layer.
- **Progressive accumulation:** cumulative-prefix effects increase as layers are added.
- **Late dependence:** cumulative-suffix effects identify downstream layers necessary for use.
- **Global dependence:** only the all-layer intervention is effective.
- **Redundant distributed computation:** no individual layer is necessary, but several alternative windows have effects.
- **Destructive broad intervention:** windows or all-layer interventions alter behavior only by degrading the model.

Do not describe a large all-layer effect as mechanistic evidence unless narrow windows,
random-window controls, and coherence checks rule out nonspecific damage.

### Updated completion gate
A main patching / knockout / MLP / direction / path experiment is not complete until it has:
1. Every individual layer · 2. Canonical windows · 3. Sliding windows · 4. Cumulative
prefixes · 5. Cumulative suffixes · 6. An all-layer condition · 7. ≥ 20 unique examples in
every required cell · 8. A separate locked-test replication · 9. Matched random and position
controls · 10. Behavioral or downstream causal validation · 11. Full coverage validation with
no missing cells.

Do not stop after finding one successful layer, window, or all-layer intervention. Complete
all granularities and report the entire effect landscape.
