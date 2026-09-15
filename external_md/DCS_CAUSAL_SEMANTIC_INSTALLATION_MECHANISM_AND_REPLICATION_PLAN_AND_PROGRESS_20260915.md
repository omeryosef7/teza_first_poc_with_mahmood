# DCS — Causal Semantic Installation: Mechanism and Replication
## Plan and Progress (append-only) — opened 2026-09-15

**Branch** `behavioral-causality-sprint` · **HEAD at open** `0a8c7e6d`
**Predecessor log (authoritative for everything before this file)**
`external_md/DCS_BOMBNESS_REPRESENTATION_TO_CAUSAL_ASR_CONTINUATION_20260910.md` (11891 lines)

> **This file is append-only.** Corrections are appended as new entries with an explicit
> `CORRECTION` / `WITHDRAWN` / `VOID` / `CANNOT ANSWER` marker. Nothing above an entry is ever
> silently rewritten. Where this file disagrees with a derived summary, this file and the
> on-disk artifacts win.

Entry IDs in this sprint are `S-###` (sprint entries) to avoid colliding with the predecessor
log's `C-CONT-###`.

---

# PART I — THE PLAN (frozen 2026-09-15, before any new result is read)

## 0. Operating mode

Autonomous extended research sprint. Ordinary research decisions are made and documented, not
escalated. Blocked branches are recorded and the sprint continues on every other runnable branch.
When several scientifically reasonable options exist, the more comprehensive / better-powered one
is chosen unless it compromises validity. Smoke tests may be small; scientific experiments may not.

Escalate to Omer **only** for externally impossible things (API credits, credentials, human
raters, unreconstructable weights/data, authorisation, a decision that changes the scientific
question). Even then: record the blocker here, mark the blocked dependency, and keep working.

## 1. Where the science actually stands (start-of-sprint position)

The old framing — *does the hidden state of an innocent codeword move toward the BOMB
representation?* — is no longer sufficient. The `button → bomb` direction **B1** produced a real
geometric signal but failed the standards for "a BOMB representation": not localised to the
codeword, strongly interaction/context dependent, not cleanly concept-specific, no causal-use
test passed, and other positions aligned as strongly or more strongly.

The better scientific object is **SEMANTIC INSTALLATION**: has the model adopted the in-context
mapping such that the innocent codeword is *internally interpreted* as the harmful concept?

* Primary instrument: the **concept-free one-word readout** `semantic_one_word` → `y_install`.
  It asks what the codeword refers to without naming the concept in the probe.
* The forced-choice probe is **not** an acceptable primary semantic instrument (the question
  contains the concept; it has leaked severely before).

Chain we are trying to establish:

```
demonstrations
  -> retrieval / semantic-remapping computation
  -> query-side installed-meaning representation
  -> semantic interpretation
  -> downstream refusal / behaviour
```

Established so far (predecessor log):

* The **A1 attention knockout** (`demo_all:attn_knockout:6-14:1.0`, scope
  `target_surface_row_only` — the query codeword row loses access to the demonstration block over
  layers 6–14) substantially reduces semantic installation on **both** button and basket.
* The knockout perturbs a **query-side** representation specifically along an
  installation-predictive axis (CONT-162→166; replicated; energy-reduction rival refuted;
  3–4× placebo margin; survives mean-state projection-out).
* On **button**, restoring the whole clean query span under the live knockout recovers ~42% of
  the knockout's de-refusal (`reports/DCS_CONT_PATCH_ENDPOINT_button.json`).

Not established: that the *installation-predictive representation itself* is the causal variable
(the current rescue restores an entire residual state, not a component), and that any of this
transfers behaviourally beyond button.

## 2. Central question for this sprint

> How do Doublespeak demonstrations cause a model to install a new semantic meaning for an
> innocent codeword in the query; what internal representation carries that installed meaning;
> which computation writes it; and is that representation causally used by downstream behaviour?

Every arrow in the chain needs its own evidence. Observational prediction and causal mediation
are never collapsed into one sentence.

## 3. Non-negotiable scientific rules

**3.1 Independence unit = DOMAIN.** Bootstrap domains, permute within/at domain level, compute
domain-level effects before population tests. Rows are for within-domain estimation only and
never inflate n.

**3.2 The `ts116m` split is frozen** (~67 TRAIN / 23 VALIDATION / 23 TEST after exclusions).
TRAIN = exploration, layer/position/hyperparameter selection, candidate construction, codeword
screening, head ranking. VALIDATION = choosing between frozen candidate families, replication,
promotion decisions. TEST = read **once**, only under a preregistration that freezes candidate,
layer, position, population, endpoint, direction, controls, test, success rule, CANNOT-ANSWER
and VOID conditions.

**3.3 Codewords are transfer tests, not pooled samples.** button and basket are never pooled to
improve a p-value. A floor-limited endpoint on one codeword is **CANNOT ANSWER**, not a negative
replication.

**3.4 Concept specificity.** Mechanistic work is BOMB-specific. BOMB/knife/gun/etc. are not
pooled into "harmful concept": they install at dramatically different rates, so a null on a
barely-installable concept is uninformative. Without a second comparably-installable concept the
honest word is **concept-dependent**, not **BOMB-specific**.

**3.5 Preregister anything that could become a headline.** Machine-readable JSON under
`configs/`, frozen and committed *before* the result is read, containing: question, hypothesis,
population, domain scope, codeword, concept, split, intervention, layer/position, primary and
secondary endpoints, statistical unit, estimator, bootstrap/permutation procedure, expected sign,
MDE/power, success criterion, failure criterion, CANNOT-ANSWER criteria, VOID conditions,
required controls, and explicit "must not be said if positive" / "must not be said if null" lists.

## 4. Claims that must NOT be revived

`A16` · `A17` · `K1` · "B1 is the BOMB representation" · "F5 is the causal mediator" · "basket
replicated the button patch result" · "raw StrongREJECT ASR is a clean estimate of attack
success" · anything marked WITHDRAWN / VOID / unsupported / CANNOT ANSWER.

Forbidden sentences, standing:

* "We found the BOMB representation." (not supported)
* "F5 is the mechanism." (its demo-side site is upstream of the A1 edit and bit-identical across
  ko/ctrl — it *cannot* mediate A1)
* "Basket failed to replicate." (the endpoint is at floor → **could not test**)
* "Installation does not affect ASR." (underpowered in content-true attack units)
* "The knockout does nothing to behaviour." (it visibly rewrites completions and changes refusal)

## 5. PHASE 0 — repair the current frontier before building on it

| # | Item | Action |
|---|---|---|
| 0.1 | basket patch endpoint | Record as **CANNOT ANSWER** (≈1 movable refusal event in 180 rows; recovery-fraction estimator degenerate). Commit the untracked artifact. |
| 0.2 | button size-match | Extend `dcs_cont_patch_endpoint.py` to read the SIZEMATCH arm; recompute KO / full rescue / size-matched rescue / recovery / recovery fraction / full-minus-sizematch, all domain-clustered. If the size-match CI includes zero, **say so** — ordering of point estimates is not a PASS. |
| 0.3 | QPROBE basket VALIDATION | The basket `validation_best.rho` is byte-identical to its TRAIN grid value (0.6525). Re-derive; add an assertion that TRAIN and VALIDATION populations are disjoint and non-empty, verified by an independent membership check. |
| 0.4 | `latest_dir` | Must require `DONE.json`, assert `rows_written == --expect-n`, and raise on incomplete/ambiguous runs. Never silently pick a newest partial directory. |
| 0.5 | button patch headline | Independently re-derive from raw `gens.jsonl` with an implementation that does not call the producer's summariser. Confirm population, arm identities, domain/row counts, refusal rates, KO effect, rescue effect, recovery fraction, CI, intervention liveness, hardware identity, model revision. |

Nothing in Phase 1+ is allowed to build on the patch frontier until 0.5 passes.

## 6. PHASE 1 (PRIORITY 1) — causal **subspace** rescue of semantic installation

The single most important experiment of this sprint.

**Question.** Under the live A1 knockout, if we restore **only the component of the query
representation that predicts semantic installation**, does semantic installation recover?

**Primary endpoint:** concept-free semantic installation `y_install` (not refusal, not
StrongREJECT). Rationale: it measures the construct the representation is claimed to encode; it
has headroom (unlike basket refusal); A1 already has a large semantic effect there; and it does
not immediately confound the representation question with a low-base-rate behaviour.

**Candidate construction — TRAIN only.** Start from the existing query-side installation probe
(`Q1_query_side_probe_rel6`). Re-validate the exact best (site, layer) on TRAIN. Current working
sites: button ≈ rel-6 / L20, basket ≈ rel-6 / L18 — the basket number is **not trusted** until
0.3 is fixed. Compare at least (a) **rank-1**: the installation-predictive ridge direction, and
(b) a **small low-rank subspace** learned strictly on TRAIN. Do not assume one dimension; test
whether higher rank gives genuine VALIDATION improvement, with nested TRAIN selection.
Dimensionality is never selected on TEST.

**Arms (per codeword, never pooled).**

1. `CTRL` — no knockout.
2. `KO` — A1 knockout.
3. `KO+SELF` — write back the knocked-out forward's own state (intervention-mechanics identity
   control; must be inert).
4. `KO+FULL` — existing full clean-state rescue (positive control / upper bound).
5. `KO+AXIS` — restore only the clean state's component along the TRAIN-learned direction:
   `h' = h_ko + P_w(h_clean − h_ko)`. (Formula verified against the actual hook/layer conventions
   before use, not applied blindly.)
6. `KO+SUBSPACE` — same with the TRAIN-selected multi-dimensional subspace, if it survives VAL.
7. `KO+ORTH` — same intervention norm, direction orthogonal to the candidate.
8. `KO+SHUFFLED` — identical probe architecture trained on domain-preserving shuffled
   installation labels, injected at matched norm; **several** independent shuffles, not one.
9. `KO+RANDOM` — enough random directions to estimate the control *distribution*, not one draw.

**Bidirectional (Priority 2).** Also test necessity where valid: from a clean high-install state,
`h' = h_clean − P_w(h_clean − h_ko)` (remove the installed component) and ask whether installation
*drops*, with same-norm orthogonal subtraction controls. Add-under-KO **and** remove-under-CLEAN
together are far stronger than either alone.

**Success shape.**

```
CTRL            high
KO              substantially lower
KO+SELF         ~ KO
KO+RANDOM       ~ KO
KO+SHUFFLED     ~ KO
KO+ORTH         ~ KO
KO+AXIS         materially toward CTRL
KO+FULL         sensible upper bound
```

with recovery consistent across domains, stable TRAIN→VALIDATION, outside the control
distribution, not explained by intervention norm or state magnitude, and not driven by a few
domains. Report **absolute recovery and recovery fraction**; the fraction estimator must raise
or return CANNOT ANSWER when the denominator is degenerate (the basket lesson).

## 7. PHASE 2 (PRIORITY 3) — replication bank with codewords that have headroom

Basket refusal is at floor; rerunning it cannot fix that. Instead: **hold the concept fixed at
BOMB and vary the innocent codeword**, which tests lexical generalisation without reintroducing
the concept-installability confound of knife/gun.

**Screening (TRAIN only, predeclared criteria).** Generate a larger candidate codeword pool
(button/basket/carrot may enter but are not privileged) and screen on: (1) sufficient installation
under natural Doublespeak; (2) meaningful KO-induced semantic change; (3) behavioural/refusal
headroom if it will carry a behavioural endpoint; (4) low literal/judge confounding; (5) a valid
concept-free readout; (6) adequate cross-domain variance. TEST is never inspected. Selected
transfer codewords are frozen before VALIDATION.

**Bank design.** Preserve the aligned factorial structure: benign literal / direct harmful
concept / natural Doublespeak / concept-in-benign-context, plus cells only where a preregistered
contrast demands them. Every row explicitly stores `benign_concept`, `harmful_concept`,
`surface_codeword`, `template_family`, `domain`, `family_slot`, `dose`, the semantic mapping, and
the condition/cell — so later analyses `groupby` fields rather than re-parsing strings. Audit
tokenised inputs across concepts/codewords **before** GPU to prevent byte-identical cells
recurring (the B/E codeword-degeneracy lesson).

**Scale.** Semantic replication: at least the existing ~90 TRAIN+VAL independent-domain scale.
Behavioural: power from the *measured* effect. The existing linking analysis implies ≈252
independent domains for an effect of the observed magnitude — so a serious representation→behaviour
test is designed at **~260–300+ independent domains**, not a knowingly underpowered 90. Power
calculation happens before GPU spend.

## 8. PHASE 3 (PRIORITY 4) — the demonstration → query circuit

Only after Phase 1 has a credible positive result.

* **8.1 Layers.** Systematic decomposition inside the A1 band on TRAIN, scored on *semantic
  installation* (not hidden-state distance). Is the effect concentrated or distributed, early or
  late? Validate the chosen structure on VALIDATION and a second codeword.
* **8.2 Heads.** Cheap attribution → top candidate set → genuine causal head knockout/patch →
  held-out validation → cross-codeword transfer. **Attribution proposes; intervention decides.**
  A high attribution score is not a mechanism.
* **8.3 Demo-key specificity.** Compare masking access to demonstration *codeword* occurrences vs
  concept-relevant positions vs surrounding context vs matched random demo positions vs matched
  non-demo positions. Control and **persist the realised intervention dose** (count actual edited
  attention cells; never a count the instrumentation cannot observe).
* **8.4 Query-row specificity.** Dose-matched position controls at neighbouring rows (codeword
  row, previous neutral, following neutral, final prompt row) so the claim is about the query
  semantic computation, not generic query-span disruption.
* **8.5 "Only the final button sees no demonstrations"** — Matan's narrowest intervention,
  constructed explicitly. **Every captured/patched/masked site records absolute position,
  relative position, token id, and decoded token text.** (A prior one-token error silently turned
  a codeword experiment into a punctuation experiment.)
* **8.6 The "last BOMB token" question, redesigned.** The earlier attempt was CANNOT ANSWER
  because the instrument was at ceiling / arithmetically degenerate — that is **not** a negative
  result. Redesign for headroom: graded concept-free log-odds instead of a ceilinged binary;
  hidden-state intervention/recovery instead of an impossible classification; non-degenerate
  donor/recipient readouts; avoid B/E where the codeword/concept structure makes the readout
  meaningless. Prove the endpoint *can move* before spending GPU. Secondary to the main codeword
  mechanism.
* **8.7 Head → MLP / path patching** once candidate heads exist, reusing the repo's causal
  tooling. TRAIN discovery, VALIDATION adjudication, never a path search on TEST.

## 9. PHASE 4 (PRIORITY 5) — construct validation of "Bombness"

Not "which metric correlates best" but **which measurements track installed semantics rather than
template, topic, harmfulness, surface token, or generic context**. One benchmark, same populations
and splits, comparing at minimum: B1; benign→harmful diff-in-means; Doublespeak−benign
diff-in-means; context-interaction contrasts; raw residual state; the query-side installation
probe; the F5 demo-side probe; logit-lens quantities; low-rank candidates where justified;
concept-free installation; and well-defined output probability/log-odds measures. A new candidate
family requires a hypothesis, not merely that the previous one lost.

### 9.1 Template generalisation (explicit Matan concern)

Train the representation on **one template family only**, evaluate on a held-out family, then
reverse. No held-out-family examples may enter representation construction. A candidate that works
only within one template family is capturing structure, not installed semantics.

### 9.2 Harmful vs benign context

Separate **surface identity**, **context harmfulness**, and **installed concept** using the
A/B/C/E matrix. The thing we call "installed meaning" must explain installation *beyond* codeword
identity, generic harmfulness, template family, domain topic, response register and prompt length
— via nuisance controls, not assertion.

### 9.3 Direct semantic readouts to retain

Concept-free one-word query (primary); logit lens (a *measurement*, topic-controlled, not
automatically a mechanism); probability/log-odds of a BOMB-like interpretation **only** where
tokenisation makes it meaningful (audit exact tokens; never silently conflate `bomb`, ` Bomb`,
subword pieces, and category words like `Explos…`); attack success only via clean endpoints.

## 10. PHASE 5 (PRIORITY 6) — representation → behaviour, properly powered

Goal: *change representation → change behaviour*, not *representation predicts behaviour*.

Intervention: the Phase-1 candidate/subspace. `KO` vs `KO + installed-meaning rescue` for
sufficiency; `CLEAN` vs `CLEAN − installed-meaning` for necessity. Endpoints must have headroom —
button refusal does, basket refusal does not; **one event in 180 cannot support a behavioural
causal replication**. A frozen TRAIN-only feasibility calculation runs first; if the endpoint
cannot discriminate the hypotheses, declare **CANNOT ANSWER BEFORE RUNNING** rather than buying a
fake null with GPU hours. Raw StrongREJECT is never a bare claim (substantial literal-codeword
false positives); maintain the content-true analysis, and treat CR-002 as an upper-bound-style
instrument. Human blind labels where scientifically required; if blocked, record and continue.
Power in DOMAIN units before every low-base-rate behavioural run.

## 11. PHASE 6 (PRIORITY 7) — mechanistic optimisation objective

Only after the causal gates pass. Gate: the candidate (1) predicts installation held-out,
(2) survives template transfer, (3) survives codeword transfer, (4) moves under the knockout,
(5) candidate-specific rescue changes installation, (6) same-norm/random/shuffled controls do
not, (7) preferably has downstream behavioural leverage. Then, and only then: can a causal
semantic-installation objective predict or manipulate jailbreak behaviour better than purely
output-based objectives? Reuse the existing GCG/optimisation stack. Objective-TRAIN data stays
separate from final evaluation; evaluate on held-out domains, templates, codewords, and
eventually another model. Never optimise on TEST; never call an optimisation result a general
jailbreak without adaptive/OOD evaluation.

## 12. Literature workstream (parallel, subagent)

`reports/DCS_CAUSAL_SEMANTIC_INSTALLATION_LITERATURE.md`. Topics: Doublespeak / semantic-remapping
jailbreaks; in-context concept remapping; activation patching of semantic representations; causal
mediation in transformers; refusal circuits; semantic interpretation vs refusal; demonstration
retrieval circuits; induction/retrieval heads; representation hijacking; activation-based jailbreak
mechanisms; causal subspace interventions. Per work: citation, date, model, phenomenon,
intervention, causal vs correlational, similarity to us, what remains novel. **No novelty claim
before this review lands.**

## 13. Data-quality gate before any major GPU run

No duplicate domains across splits; no prompt leakage; no unintended byte-identical prompts across
concepts; correct template / codeword / harmful concept / benign concept / family slot / dose /
cell; tokenizer round-trip; target token positions; decoded token text; truncation; prompt lengths;
expected row and domain counts; cross-split verbatim sharing; stale caches; stale run directories;
resume behaviour; duplicate prompt IDs; compound-key uniqueness. Audit passes → spend the GPU
freely.

## 14. Code rules

Reuse aggressively; prefer small additive changes over parallel implementations. Every non-trivial
module gets a smoke or unit test. After each meaningful change, independently review token
indexing, layer convention, hook location, donor/recipient identity, intervention liveness, mask
scope, edited-cell count, split selection, denominators, cache provenance, resume logic, hardware
metadata. **Missing load-bearing fields must raise** — no `row.get("generation", row.get(...))`,
no missing-data-to-plausible-zero. Verifiers must be independent: reconstruct expected rows from
raw source, compare IDs against an external manifest, recompute headline statistics. For headline
results, a subagent re-derives without reading the original analyser.

## 15. Positive controls are mandatory

A null is uninterpretable unless the instrument has been shown capable of moving something. Every
intervention family ships a positive control using the same mechanism (full clean rescue for a
subspace rescue; a known-live knockout; a self-patch identity test; a known semantic contrast for
a decoder). Never conclude "this state carries nothing" from a transplant never shown to transfer.

## 16. SLURM / GPU operating rules

* Shared HF cache: `/home/sharifm/students/matanbentov/hub/...` snapshot
  `0e9e39f249a16976918f6564b8830bc894c89659` (Llama-3.1-8B-Instruct). Verify it exists before
  launching; never re-download on compute nodes.
* Knockout runs: pinned revision, **bf16**, **eager** attention (the knockout needs a real 4-D
  additive mask and must refuse under SDPA/Flash). Persist the actually-loaded config.
* **Compared generation arms must share GPU architecture** — greedy decoding is not
  byte-reproducible across architectures. Persist hostname, GPU model, CUDA, revision, dtype,
  attention implementation. Cross-GPU differences are not experimental effects.
* `--nodelist` must not be a multi-node expression (SLURM then waits for *all* of them). Exclude
  bad nodes only after checking current cluster state.
* **Never** pass comma-containing commands through `sbatch --export=ALL,CMD="..."` — it truncates
  at the first comma. Put such commands inline in the `.slurm` file.
* `sacct COMPLETED 0:0` is **not** success. Success = expected artifacts + completion marker +
  expected rows + expected domains + intervention liveness + run trailer + no empty outputs + no
  quota error. Analysers refuse incomplete runs.
* Disk: effective ~200 GB cap despite misleading `quota`. Clean only reconstructable caches;
  quarantine invalid runs with a reason rather than deleting evidence.
* Heavy CPU analysis goes to `slurm_scripts/dcs_cont_cpu.slurm`, never the login node.
* Amortise model loading (the NFS load dominates); sequence compatible experiments in one
  allocation; avoid two big loads on one node.
* `do_sample=False` reruns are **not** new independent samples. Increase domains, not repeats.

## 17. Statistics to report for every major result

independent domains · raw rows (separately) · effect estimate · domain-clustered CI · exact or
permutation p where appropriate · the **attainable p-floor** · MDE/power · positive/negative/tied
domain counts · split · codeword · concept · template · layer · position · intervention dose.
Never a p-value alone. A p at the attainable floor means the test exhausted its resolution.
Family-wise correction (Holm or another preregistered procedure) where candidates/layers are
genuinely selected simultaneously.

## 18. Judge / ASR rules

Raw LLM-judge ASR is not ground truth here (established literal-codeword false positives;
non-deterministic labels — the judge flips ~13% on byte-identical text). Prefer semantic
installation for semantic claims, native refusal for refusal claims, concept/content presence,
CR-002/content-true analysis, and human blind labels where semantic adjudication is required. An
affirmative or fluent literal answer is not an attack success. Freeze the judge before
confirmatory use.

## 19. Decision gates

* **Gate A — is there a causal semantic representation?** KO reduces installation AND
  candidate-specific rescue restores it AND random/shuffled/orthogonal do not AND it survives
  held-out validation. If NO: do not force the story — ask whether the information is
  distributed/nonlinear, or whether full-state rescue works through another feature.
* **Gate B — does it transfer?** Another codeword/template with adequate headroom. If NO: call it
  surface/template-specific.
* **Gate C — can we identify the writer circuit?** Causal head/path intervention, not attribution.
  If NO: keep the representation result; do not invent a circuit.
* **Gate D — does manipulating it change behaviour?** Needs a powered endpoint. NO from
  floor/underpower = CANNOT ANSWER. NO despite adequate power and a live semantic intervention =
  a scientifically important dissociation.
* **Gate E — good enough to become an optimisation objective?** Only if A–D justify it.

## 20. Deliverables

This log · machine-readable preregistrations in `configs/` · data manifests (hashes, split
membership, audit results) · an updated candidate registry (definition, training population,
layer, position, dimensionality, validation status, controls, causal status) · result JSONs in
`reports/` with enough raw intermediate statistics for independent reproduction · an updated claim
table (claim, status, statistic, population, caveats) ·
`reports/DCS_CAUSAL_SEMANTIC_INSTALLATION_LITERATURE.md` · a final self-contained handoff
(original question, what was attempted, what failed, causal evidence, replication status,
mechanism evidence, what we can defend, what we cannot claim, highest-value next experiments).

## 21. What a great outcome looks like

Not "another Bombness metric with a higher correlation". Rather:

```
Doublespeak demonstrations install a new semantic interpretation of an innocent codeword.
Blocking a specific demonstration->query retrieval pathway reduces that installation.
The intervention selectively perturbs an installation-predictive query-side representation.
Restoring only that representation causally restores semantic installation.
Specific attention heads/pathways write the representation.
Manipulating it changes downstream refusal on an adequately powered endpoint.
```

If reality does not support this, do not manufacture it. A well-controlled negative showing
installation is distributed or behaviourally dissociated is also valuable. Keep negative results,
failed controls and corrections. When the design cannot answer, say **CANNOT ANSWER**; when a run
did not execute the frozen design, say **VOID**; when a claim is invalidated, **WITHDRAW** it.

## 22. Execution checklist (working order)

- [ ] **P0.1** basket endpoint → CANNOT ANSWER; commit artifact
- [ ] **P0.2** size-match arm in the analyzer; recompute with CIs
- [ ] **P0.3** QPROBE basket VALIDATION re-derivation + disjointness assertion
- [ ] **P0.4** `latest_dir` hardening (DONE.json + row-count assertion)
- [ ] **P0.5** independent re-derivation of the button patch headline
- [ ] **P1.a** subspace-rescue hook (`SubspaceDonorPatch`) + unit tests
- [ ] **P1.b** TRAIN-only candidate export (rank-1 + low-rank), with token/site identity recorded
- [ ] **P1.c** preregistration frozen in `configs/`
- [ ] **P1.d** identity/liveness smoke (KO+SELF inert; axis rescue fires; dose recorded)
- [ ] **P1.e** full arm set launched on the semantic endpoint, TRAIN then VALIDATION
- [ ] **P2** bidirectional (CLEAN − component) necessity arms
- [ ] **P3** codeword screening + replication bank (concept fixed = BOMB)
- [ ] **P4** demo→query circuit decomposition (layers → heads → source positions → paths)
- [ ] **P5** construct validation / template transfer benchmark
- [ ] **P6** powered representation→behaviour test
- [ ] **LIT** literature review (parallel)
- [ ] **POWER** domain-unit power analysis for every behavioural endpoint

---

# PART II — CHRONOLOGICAL PROGRESS

## S-001 — sprint opened; repository and frontier state (2026-09-15)

```
HEAD           : 0a8c7e6d63d41f9d2954c63598bfa236e60ef948
branch         : behavioral-causality-sprint
date           : 2026-09-15T16:51:32+03:00
host           : c-009
untracked      :
                 ?? SUMMARY_2026-09-02_TO_09-15.md
                 ?? external_md/DCS_CAUSAL_SEMANTIC_INSTALLATION_MECHANISM_AND_REPLICATION_PLAN_AND_PROGRESS_20260915.md
                 ?? reports/DCS_CONT_PATCH_ENDPOINT_basket.json
snapshot exists: YES  (/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659)
squeue         : 0 job(s) running/pending
```
