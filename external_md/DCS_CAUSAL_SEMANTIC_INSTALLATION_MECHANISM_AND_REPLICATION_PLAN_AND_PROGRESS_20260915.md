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

---

## S-002 — P0.5 DONE. Independent re-derivation of the button patch headline: the RUN is clean, the STATISTIC is not. **CORRECTION + WITHDRAWAL.**

New tool: `scripts/dcs_csi_rederive_patch.py`. It does **not** import or call
`dcs_cont_patch_endpoint.py`. It re-discovers the run directories under a stricter rule,
re-reads `gens.jsonl` *and* `results.jsonl` from scratch, re-derives population/arm identity/split
membership from raw rows plus the external split manifest, implements its own domain-clustered
bootstrap and its own **exact sign-flip randomisation test**, recovers each arm's node/GPU from
SLURM accounting, and runs a **second, independently written refusal detector** alongside the
phase's frozen native one. Generation text is read but never printed or written.

Artifacts: `reports/DCS_CSI_REDERIVE_PATCH_button.json`, `reports/DCS_CSI_REDERIVE_PATCH_basket.json`.

### Part 1 — the mechanical audit PASSES on both codewords

| check | button | basket |
|---|---|---|
| run dirs: `DONE.json status=ok`, `rows_written == --expect-n == 180`, gens lines == 180 | 4/4 arms | 3/3 arms |
| identical `prompt_id` set across arms | 180/180 | 180/180 |
| identical `prompt_sha16` per `prompt_id` across arms (arms saw the *same prompts*) | 0 mismatches | 0 mismatches |
| shared config surface (bank, model, conditions, n_examples, bank_blocks, exclusions, max_new, dtype, attn_impl, seed) | identical | identical |
| population | 180 rows / 90 domains | 180 rows / 90 domains |
| split membership vs external manifest | 67 train + 23 validation, **0 TEST**, 0 excluded | same |
| model revision | `…/snapshots/0e9e39f249a16976918f6564b8830bc894c89659` | same |
| dtype / attention | bfloat16 / **eager** on every arm | same |
| knockout liveness (intervened arms) | prefill edits min 405, median 513, **decode edits 0**, `hook_n_query_rows_edited = 9` on every row (= the 9 layers 6–14), 0 liveness violations | same |
| rescue liveness | fired on 180/180; layer set `{20}`; 24 positions/row (full span), 12/row (size-match), constant | fired 180/180; layer `{18}` |
| knockout target token identity | `" button"` × 180 on every intervened arm; CTRL records none (correct — no knockout) | `" basket"` |
| hardware | ctrl t-806, ko t-806, rescue n-801, sizematch n-803 — **all `l40s`: SAME ARCHITECTURE** | ctrl n-803, ko n-803, rescue t-806 — all `l40s` |
| detector agreement (native vs independent refusal regex) | **100.00 %** of 720 labels | 100.00 % of 540 labels |

So: the population is right, the arms are right, the intervention was live, the rescue fired, the
split is clean, no TEST leak, no empty generations, and the refusal endpoint is not an artifact of
one regex. **`VERDICT: PASS` on both.** Two flags raised in the first pass were verifier bugs, not
run bugs, and are fixed in the committed version (argparse's inert `--rescue-donor` default on
non-rescue arms; comparing CTRL's necessarily-empty knockout-target histogram against the
intervened arms).

### Part 2 — the statistic: **how few events actually carry the headline**

Refusal events, `button`, over the 180-row / 90-domain population:

| arm | refusal rows (of 180) | domains with any refusal (of 90) | domain-mean rate |
|---|---|---|---|
| CTRL | 20 | 18 | 0.1111 |
| KO | 8 | 6 | 0.0444 |
| RESCUE_CLEAN | 13 | 11 | 0.0722 |
| SIZEMATCH12 | 11 | 9 | 0.0611 |

Only domains whose **paired** difference is nonzero carry information. With *k* such domains an
exact two-sided sign-flip test over domains cannot return a p below **2/2^k**. That budget:

| contrast | Δ (domain-mean) | bootstrap CI95 | informative domains *k* | exact p | **attainable p-floor** |
|---|---|---|---|---|---|
| KO de-refusal (CTRL−KO) | **+0.0667** | [+0.0333, +0.1000] | **12** (12 pos, 0 neg) | 0.000488 | 0.000488 |
| recovery (RESCUE−KO) | **+0.0278** | [+0.0056, +0.0556] | **5** (5 pos, 0 neg) | **0.0625** | **0.0625** |
| size-match recovery (SIZEMATCH−KO) | +0.0167 | [0.0000, +0.0389] | **3** | 0.25 | 0.25 |
| **full − size-match** | +0.0111 | [0.0000, +0.0278] | **2** | **0.50** | **0.50** |
| residual (CTRL−RESCUE) | +0.0389 | [+0.0167, +0.0667] | 7 | — | — |
| recovery fraction | **0.417** | [0.133, 0.714] | denominator from 12 domains | — | — |

Read that column. **The rescue contrast has 5 informative domains; an exact domain-level test on
5 domains cannot reach p < 0.0625 no matter how large the effect.** The KO contrast's p is *also*
exactly at its own floor — it exhausted the test's resolution, which is not the same as being
overwhelmingly strong.

**Why the bootstrap CI looked reassuring and should not have.** With 5 positive and 85 tied
domains, a domain-resampled bootstrap draw contains zero positive domains with probability
(85/90)^90 = **0.0058**. So the 2.5th percentile is above zero *by construction* whenever five
same-signed domains exist. "CI excludes 0" here carries almost no information beyond "five domains
moved and none moved against"; it is not independent evidence.

### Consequences — status changes

* **CORRECTION to `c029b4fb` ("button patch test PRIMARY result — clean query-rescue recovers
  ~42% of the KO de-refusal (CI excludes 0)").** The point estimate, the population, the liveness
  and the mechanics all reproduce exactly. But the significance framing does not survive an exact
  domain-level test. The defensible statement is now:
  > Under the live A1 knockout, restoring the clean query span moved refusal from 0.044 back to
  > 0.072 against a CTRL of 0.111 — a point recovery of 42% of the knockout's de-refusal. The
  > effect rests on **5 of 90 domains**, all moving in the predicted direction and none against;
  > an exact domain-level sign-flip test is at its attainable floor of p = 0.0625 and therefore
  > **cannot certify the effect at α = 0.05**. Status: **EXPLORATORY / DIRECTIONALLY CONSISTENT,
  > UNDERPOWERED** — not a confirmed causal-mediation result.
* **WITHDRAWN: `0a8c7e6d` "button size-match PASSES (dose-dependent recovery)".** The
  full-vs-size-match difference rests on **2 domains** and its exact test cannot go below p = 0.50.
  The point estimates do order as predicted (full 0.0722 > size-match 0.0611 > KO 0.0444), and the
  size-match arm is mechanically perfect (12 positions written on every row, constant). But
  ordering of point estimates is not a PASS, and this is exactly the failure the sprint plan §5.2
  pre-committed against. **Correct status: CANNOT ANSWER — the position-identity-vs-count control
  is not resolvable at this event count.**
* **CONFIRMED CANNOT ANSWER (P0.1): basket.** CTRL 0.00556 / KO 0.000 / RESCUE 0.00556 — that is
  **one** movable refusal event in the whole 180-row population, *k* = 1 informative domain,
  attainable p-floor = 1.0, and the recovery-fraction estimator returns `CANNOT ANSWER` from its
  degeneracy guard. Not a failed replication: **the basket behavioural endpoint could not test the
  hypothesis.** The forbidden sentence "basket failed to replicate" stands forbidden.

### What this does to the sprint plan

It *strengthens* the plan's two central design choices rather than changing them:

1. **Phase 1 is right to use semantic installation, not refusal, as the primary endpoint.** Button
   refusal yields 5–12 informative domains at 90 domains; that is not enough resolution to
   adjudicate a subspace-vs-full-state comparison, which needs to separate several arms that are
   *closer together* than full-rescue-vs-KO.
2. **Phase 2's ~260–300-domain bank is not a luxury.** At the observed event rate (20 CTRL refusal
   rows per 180, and 12 informative domains per 90 for the largest contrast), the arms Phase 5
   wants to separate are simply not separable at n=90 domains. A domain-unit power calculation is
   now a hard gate (task **POWER**), not a formality.

Checklist: **P0.1 ✔ · P0.4 ✔** (the strict-run-dir rule is implemented and exercised here) **· P0.5 ✔**.
P0.2 is superseded in substance — the size-match arm is now analysed, with the honest answer being
CANNOT ANSWER rather than PASS.

---

## S-003 — Phase 1 premise verified, and the endpoint choice is vindicated by the record

Before building the subspace rescue I checked its load-bearing premise — *does the A1 knockout
actually move semantic installation?* — against the primary log rather than the plan's summary of
it. `CONT-ENTRY 054` (predecessor log line 5776 ff.):

| | button (`DR-071`) | basket (`cinstbk_*`) |
|---|---|---|
| installation `base` (no knockout) | 0.6785 | 0.4768 |
| installation `ko` (A1, band 6–14) | 0.4703 | 0.2405 |
| installation `ctrl` (dose-matched placebo band 20–28) | 0.6854 | 0.4840 |
| **`ko − ctrl`** | **−0.2150** [−0.234, −0.196] | **−0.2435** [−0.273, −0.213] |
| **domains moving negative** | **67/67** | **67/67** |

Protocol recovered from the run metadata: scope `target_surface_row_only`, ko band 6–14, placebo
band 20–28, `--query-kinds semantic_one_word`, `--conditions natural_doublespeak`, `--n-examples 4`,
`--readout-ids whole_answer`, **`--readout-max-batch 1`**, `--min-option-mass 0.05`, seed 20260913,
eager/bf16, 670 rows over 67 TRAIN domains, 1735 s per arm (no generation — this is a next-token
readout, which is why it is ~3× cheaper than the behavioural arms).

Note the arm vocabulary: `ctrl` here is a **dose-matched placebo knockout at a late band**, not a
no-knockout arm; the no-knockout arm is `base`. Phase 1 keeps all three.

**Why this settles the endpoint question.** Compare the informative-domain budget of the two
endpoints on the same intervention:

| endpoint | informative domains | attainable exact p-floor |
|---|---|---|
| refusal (behavioural), CTRL−KO, 90 domains | **12** | 4.9e−4 |
| refusal, RESCUE−KO, 90 domains | **5** | **0.0625** |
| **semantic installation, KO−CTRL, 67 TRAIN domains** | **67** | **1.4e−20** |

The semantic endpoint has **an order of magnitude more resolution** on the same causal pathway.
Plan §6.1's choice of `y_install` as the Phase-1 primary is therefore not a convenience — it is the
only endpoint on which the several *closely-spaced* arms a subspace experiment needs (candidate vs
orthogonal vs shuffled vs random vs full) can possibly be separated.

## S-004 — POWER task DONE: what the behavioural endpoint can and cannot support

`scripts/dcs_csi_power.py` → `reports/DCS_CSI_POWER.json`, `reports/DCS_CSI_POWER.md`. Monte-Carlo
over the *measured* per-domain refusal profiles, domain unit, exact sign-flip test, α = 0.05.

| contrast | observed effect | power at today's **D = 90** | **D for 80 % power** |
|---|---|---|---|
| KO de-refusal (CTRL−KO) | 0.0667 | **0.98** | ≈ 59–63 |
| **recovery (RESCUE−KO)** | 0.0278 | **0.39** | **≈ 143–147** |
| size-match (SIZEMATCH−KO) | 0.0167 | 0.08 | ≈ 237 |
| planned to the CI *lower bound* instead of the point | — | — | KO ≈ 121, recovery ≈ **710** |

MDE at 80 % power (base rate 0.111): **D = 90 → 0.0455** (41 % of base), D = 180 → 0.0221,
**D = 300 → 0.0134** (12 % of base). MDE scales ≈ 1/D rather than 1/√D because the binding
constraint is the *count of informative domains*, not row noise.

Two findings beyond the brief, both important:

1. **At D = 90 a recovery-style experiment has a 61 % prior probability of being structurally
   incapable of significance** — the p-floor 2/2^k exceeds 0.05 before a single token is generated
   (92 % for the size-match contrast). The observed p = 0.0625 and p = 0.25 in S-002 **are** their
   floors. This is not hindsight: it is the design's expected behaviour.
2. **Basket is a headroom problem, not a sample-size problem.** k = 1, p-floor 1.0; ~540 domains
   would only make significance *attainable*, not likely. No amount of basket data fixes basket.

**Headroom vs domains.** For the limiting recovery contrast, 2× baseline refusal cuts required D by
46 % (149 → 80) and 3× by 61 % (149 → 58). So a 2×-headroom codeword would make the *existing* 90
domains adequately powered (0.90) for recovery with **zero new data collection**. Headroom is the
cheaper lever and converts tied domains into informative ones — but it is a 2–3× lever, not
orders of magnitude, and the estimate is an upper bound (it assumes arm separation survives on the
latent scale).

Reconciliation with the prior `DCS_CONT_LINKING_POWER.json` ≈ 252: the two do **not** agree and
should not — different endpoint (a continuous linking quantity), different estimator (Fisher-z on
Pearson r, where all N contribute) and different effective N (67 vs 90; here 78 of 90 domains are
tied and contribute nothing). Both land at 10² domains. **D ≈ 300 satisfies every currently-known
target simultaneously; D ≈ 150 is the minimum that unblocks recovery alone.**

⇒ This is now the quantitative backing for plan §7.4's "~260–300+ independent domains", and it
promotes **codeword headroom screening** (§7.2 criterion 3) from a nicety to the single
highest-leverage design decision in Phase 2.

## S-005 — Phase 1 primitive implemented and unit-tested: `SubspaceDonorPatch`

Additive to `src/boombness/donor_patch.py` (the existing rescue primitive's module), plus
`tests/test_subspace_donor_patch.py`. **No new stack** — it reuses `DonorBlock`,
`ActivationCapture` and the existing donor-capture flow in `score_behavior.py` unchanged.

```
h' = h + P_W (h_donor - h),     P_W = W^T W,   W orthonormal [r, hidden]
```

Design notes that matter scientifically:

* **One primitive covers both causal directions.** The formula is symmetric in which forward is
  the donor: live = KO with a clean donor **adds** the installed component (sufficiency); live =
  CLEAN with a KO donor **removes** it (necessity, plan §6.4). Phase 2 therefore needs no new code,
  and the two directions cannot drift apart in implementation.
* **`orthonormalise()` is applied inside the class, not trusted from the caller.** A ridge weight
  vector is not a unit vector and low-rank components are not orthogonal; projecting with a
  non-orthonormal basis silently computes something that is not a projection. Linearly dependent
  rows are refused.
* **float64 arithmetic, cast once on write.** A bf16 projection of a small delta loses a visible
  fraction of it.
* **The token-identity guard was factored out**, not copied: `assert_token_identity()` is now
  shared by `DonorPatch` and `SubspaceDonorPatch`. Two hand-copied safety checks is how one of
  them quietly loses it. `DonorPatch`'s behaviour is unchanged and is covered by a test.
* **Dose is recorded, never inferred**: per-row mean ‖delta‖, ‖P_W(delta)‖, written norm,
  norm-match target, captured energy fraction, rank, position count, and a degeneracy counter.

### A real bug the tests caught, and what it would have done to the science

The first implementation norm-matched a control by **rescaling its projection** of the delta:
`proj * (target / max(‖proj‖, 1e-12))`. When the control subspace carries essentially none of the
difference, `‖proj‖ ≈ 2.6e−17`, so this multiplies floating-point noise by ~1e11 and writes a
direction that is pure rounding error — the test measured it writing **4e−6 where it should have
written 0.143**. A norm-matched control that silently writes ~nothing is a control that *cannot
fail*, and it would have manufactured apparent specificity for the candidate.

Fixed: when a control subspace's projection is degenerate (‖P_W(delta)‖ < 1e−6·‖delta‖) the class
injects along a **deterministic unit vector of the subspace** at the candidate's norm, and
**records `n_positions_norm_match_degenerate`** so a degenerate control cannot pass unnoticed.

Two further test "failures" turned out to be the code being right and the test wrong, and both are
now documented in the test file rather than silently edited away:
* the token-identity guard is **position-scoped** — a token differing *outside* the patched span
  cannot misplace anything and must not refuse;
* a control orthogonal to a candidate that *is* one row of the delta is exactly orthogonal to that
  row and is **correctly** flagged degenerate. A learned installation axis is never one row's delta,
  so the test now uses a generic candidate.

`tests/test_subspace_donor_patch.py`: **24/24 PASS**, including the two that carry the most weight —
a full-rank subspace reproduces `DonorPatch` **exactly** (max|diff| = 0.00e+00, so the subspace arm
and its own positive control are on the same scale), and add-then-remove returns the unpatched
forward exactly (so the Phase-2 necessity arm is the same operation run backwards).

## S-006 — two infrastructure failures, recorded

* **The S-002 commit silently did nothing.** `git commit -- <paths>` only accepts *tracked* paths;
  for new files it errors per-path — and the shell pipeline still exited 0. Lesson for this sprint:
  **new files must be `git add`-ed first, and every commit must be verified against `git log`, not
  against an exit code.** (This is the path-limited-commit discipline the shared tree requires,
  with the new-file case spelled out.)
* **Job 896365 (basket `semantic_one_word` extraction) FAILED in 71 s.** `--model` was omitted, so
  it resolved to the HF id `meta-llama/Llama-3.1-8B-Instruct`, which has no weights in the cache on
  n-306. The button corpus's own metadata records `--model null`, which is how the omission looked
  reasonable. Fixed by pinning the snapshot path explicitly; resubmitted as **896369**.

### Jobs in flight

| job | what | node | status |
|---|---|---|---|
| 896356 | all 4 button patch arms in ONE allocation (P0.6) | n-303, **RTX 3090** | RUNNING |
| 896363 | same 4 arms pinned to **l40s** (P0.6b, architecture-matched replicate) | — | PENDING |
| 896369 | basket `semantic_one_word` corpus (Phase 1 cross-codeword prerequisite) | — | PENDING |
| 896358 | QPROBE basket VALIDATION audit (P0.3) | n-303 | RUNNING |

896356 landing on a 3090 rather than an L40S is **not** a problem for its own internal comparison —
all four arms share one node and one GPU by construction, which is the whole point. It additionally
yields a *cross-architecture* churn bound. 896363 supplies the architecture-matched replicate that
is directly comparable to the published L40S numbers.

---

## S-007 — Phase 1 is built: candidate export, intervention wiring, preregistration, analyser

Four pieces, all additive, no parallel stack.

**1. `scripts/dcs_csi_axis.py` — the TRAIN-only candidate export.** Produces one `.pt` holding every
named basis the experiment needs, built from the *same rows, split, centring and fit*:

| basis | what |
|---|---|
| `cand_rank1` | the rank-1 ridge installation axis |
| `cand_pls1..5` | rank-r PLS1 subspaces with **explicit deflation** |
| `ctrl_orth` | a direction orthogonal to `cand_rank1` |
| `ctrl_random0..7` | i.i.d. Gaussian directions (the control *distribution*) |
| `ctrl_shuffled0..4` | the identical ridge fit on **domain-preserving** shuffled labels |

Discipline baked in: the fit refuses if any validation/test domain reaches it or if the corpus
contains test rows; the **site is FROZEN to the prior winner `rel-6` and is not re-searched**, so
this adds no new site-selection multiplicity; only *layer* and *rank* are selected, nested inside
TRAIN by leave-one-**domain**-out; PLS deflation is explicit and commented against the phase's
earlier wrong "one-dimensional" claim; and `ctrl_orth` is verified orthogonal or the script
refuses. Controls are built in the same file as the candidate on purpose — a control assembled
later by different code differs from the candidate in more ways than the one under test.

**Two candidate families are exported and both are frozen before VALIDATION** (plan §4.2):
`--fit-prompt semantic` fits on the *same forward the intervention acts on* — the right
representation for a causal claim, but it shares a forward with the readout and so is **not**
offered as a clean observational claim; `--fit-prompt behavioral` fits on the non-circular lineage
the existing Q1 probe used and asks whether that axis **transfers**. VALIDATION adjudicates; TEST is
not involved. Jobs 896371 / 896372.

**2. `score_behavior.py` wiring — three flags, one branch.** `--rescue-basis`,
`--rescue-basis-key`, `--rescue-norm-match-key`. The subspace patch reuses the *existing* donor
capture, positions, layer and token-identity guard; the **only** difference from the whole-state
rescue is the projection — which is what makes the full-state arm an exact upper bound rather than
a differently-constructed comparison. Guards added: `--rescue-basis` without `--rescue-layer`
refuses (it would be silently inert); an unknown basis key refuses rather than defaulting (two arms
differing only by a typo must not produce the same numbers under different labels); the basis
key, norm-match key, file name and realised dose are **recorded on every row**, so the artifact can
prove which subspace an arm wrote instead of trusting the arm label.

**3. `configs/dcs_csi_pr001_subspace_rescue.json` — PR-CSI-001, frozen before any arm exists.**
15 arms; primary endpoint `y_install`; **primary contrast `KO_AXIS − KO_ORTH`** (both norm-matched,
same layer, same positions, same donor) rather than a rank test against the control set — because
the paired domain contrast has 67 domains of resolution (p-floor 1.4e−20) whereas ranking the
candidate among ~11 control arms has a floor of 1/12. The control family is still run, and is
analysed as 11 pairwise domain-level contrasts under **Holm**, plus the control recovery
*distribution* with its rank and that rank's honest floor.

Three gates run **before** any contrast is reported: manipulation check (`KO − BASE` negative, the
established ≈ −0.2), identity check (`KO_SELF` inert), and **instrument capability**
(`KO_FULL − KO > 0`). If the whole-state rescue itself does not recover installation, the subspace
question is **CANNOT ANSWER for want of a capable instrument — explicitly not a negative.** The
prereg also carries its `must_not_be_said_if_positive` list, including the standing prohibition on
"first to causally intervene on demo→query attention in ICL", which the literature review confirms
is false (Wang et al., *Label Words are Anchors*, EMNLP 2023).

**4. `scripts/dcs_csi_subspace_analyze.py` — the analyser, with VOID applied first.** Reuses
`load_installation` (same concept-free channel filter, same duplicate-key refusal) and imports
`strict_run_dir`, the domain bootstrap and the exact sign-flip test from the S-002 verifier so that
"complete run" and "p-floor" mean exactly one thing across the sprint. It refuses to print any
contrast from a run set that trips a VOID condition, and — the check that matters most for a
controls experiment — it **verifies norm matching from the rows**: if a norm-matched control's
written delta norm differs from the candidate's by more than 1e−5, or any position was flagged
norm-match-degenerate, the run is VOID rather than quietly showing false specificity.

### Phase 2 necessity arm: a wiring gap, recorded

The primitive already supports necessity (live = CLEAN, donor = KO), but `score_behavior.py` gates
the whole rescue block on the arm having a knockout, so the *clean-live / ko-donor* combination
cannot be expressed by existing flags. Deferred, not forgotten: Phase 1 first, then a small
additive `--rescue-donor ko` that builds the knockout hooks for the donor capture only. Noted here
so it is not mistaken for "necessity was tested".

---

## S-008 — data-quality findings that change Phase 1's design (plan §13/§15 gate)

Three things surfaced while preparing the Phase-1 population. Two are latent footguns worth
recording permanently; one forces a real design decision.

### (a) `prompt_id` is **100 % shared across codeword banks**; `prompt_sha16` is not

Measured on 4002 sampled rows of `ts116m_button_bomb` vs `ts116m_basket_bomb`:

| key | overlap across the two banks |
|---|---|
| `prompt_id` | **4002 / 4002 = 100 %** |
| `prompt_sha16` (the text hash) | 1001 / 4002 = **25 %** |

`prompt_id` is derived from the row's **axes**, not its text. Consequences:

* An `--exclude-prompt-ids` file built from the wrong codeword's bank applies **silently** — it
  cannot trip `score_behavior`'s "every exclusion id must be present in the population" check,
  because every id *is* present. (Both `*_sow_validation.txt` files came out with the same
  `exclusion_sha16 64f6bb1310332073`, which is how this was noticed.)
* Any join on `prompt_id` across codewords pools them without a trace. This is why the existing
  analyses carry a `bank_sha` guard, and it is why **the Phase-1 analyser now asserts bank
  identity from each run's own `config.json`** and VOIDs on a mismatch or on a bank path that does
  not name the declared codeword.
* The 25 % `prompt_sha16` overlap is exactly the **codeword-degenerate cells**: where the concept
  token replaces the codeword, button and basket rows are byte-identical. Independent confirmation
  of the standing "verify populations differ before spending GPU" lesson.

The S-002 verifier's cross-arm check was already the right one (`prompt_sha16`, i.e. text), so no
existing result is affected.

### (b) Phase-1 populations are now physically separate per split

`dcs_ts_make_exclusions.py` **refuses** a multi-split selection ("split 'train,validation' is not a
value of the frozen manifest") — a good guard, and it pushes toward the better design. Built:

| file | remaining rows | domains |
|---|---|---|
| `exclude_{button,basket}_bomb_sow_train.txt` | 670 | 67 |
| `exclude_{button,basket}_bomb_sow_validation.txt` (new) | 230 | 23 |

TRAIN and VALIDATION are therefore **separate runs**, which makes accidental pooling impossible
rather than merely forbidden. Sequencing: TRAIN is the gate, VALIDATION is the claim — and note
explicitly that **the TRAIN evaluation is in-sample for the candidate** (the exported basis is fit
on all TRAIN domains), so the honest held-out number is VALIDATION.

### (c) The `semantic` candidate family is BLOCKED, for two independent reasons — and the plan is better without it

Job **896371 FAILED**: `no multiposition_reps.pt under cont1_semantic_one_word_button_bomb_…`. The
semantic corpus holds only `final_occurrence_reps.pt` (580 MB); its behavioural sibling holds both
(12 GB). The two extractions were issued with **byte-identical flags except `--only-query-kind`**,
both report `n_rows_captured 3720` and `skip_reasons {}`, and both wrote a clean `DONE.json` — so
the missing multiposition cache is invisible from the run's own summary. Another instance of the
phase's recurring shape: *a run that completes cleanly without producing what you need.*

Independently, `lpm.load_corpus` **deliberately refuses** a semantic corpus as a predictor
population:

> "the predictor corpus must be the BEHAVIOURAL population; … The semantic prompt's next token IS
> the target, so a representation read there predicts it circularly." (REVIEW-1/T0-4, CONT-ENTRY 002)

**Decision, and the reasoning, stated openly.** I am *not* overriding that frozen guard silently.
It is about **observational** circularity, and my use would be **interventional** — "does restoring
this component restore the readout" is a causal question for which same-forward provenance is
arguably the *correct* choice, not a defect. But that is an argument to be made explicitly and
reviewed, not smuggled in behind a flag while a job runs.

So: **the behavioural-fit axis becomes the Phase-1 primary candidate** (job 896372). This is
strictly better on the merits:

* it is non-circular *by the project's own frozen standard*;
* it is the lineage of the TEST-confirmed Q1 probe;
* injecting an axis learned on a **different prompt type** and having it causally control
  installation is **stronger** evidence than a same-forward direction would be.

**The cost, stated before the result is read:** this builds in a *transfer* assumption. If the
primary comes out null, "the axis does not transfer across prompt type" is confounded with "the
axis is not causal", and that null must be reported as **ambiguous between those two**, not as a
clean negative. The mitigation — a semantic multiposition re-extraction (~15 GPU-min) plus an
explicit, documented override argument — is queued behind the question of whether job 896369
(basket semantic extraction) produces a multiposition cache at all, which will say whether the
button-semantic absence was transient or structural.

PR-CSI-001 is amended accordingly: the `semantic` family is **deferred, not withdrawn**, and the
ambiguity clause above is added to its `must_not_be_said_if_null` list.

### Operational note

`python` stdout is block-buffered under SLURM, so these jobs show nothing but the shell's own
`echo` until they exit. Progress must be read from **artifacts**, not logs. `PYTHONUNBUFFERED=1` is
set in the new Phase-1 smoke script and should be set in every future runner.

---

## S-009 — P0.3 RESOLVED: the basket QPROBE validation number is a **coincidence, not a bug**, and is citable

`reports/DCS_CSI_QPROBE_VALIDATION_AUDIT.md`, `scripts/dcs_csi_qprobe_valaudit.py`, job 896358.

The suspicion (plan §5.3) was that basket's `validation_best.rho = 0.6525` being byte-identical to
its TRAIN grid value at rel-6/L18 was the signature of a validation path silently re-reading the
training population. Settled by full-precision re-derivation:

| codeword | cell | TRAIN `rho_loo` | VALIDATION transfer `rho` | abs diff |
|---|---|---|---|---|
| button | rel-6, L20 | 0.5934700332983854 | 0.6450094807413964 | 5.15e−02 |
| basket | rel-6, L18 | **0.6524545477487157** | **0.6525210881770593** | **6.65e−05** |

They are **different floats** that happen to agree to 4 dp. Three independent lines confirm it:

1. **The populations are provably disjoint.** |TRAIN| = 67, |VALIDATION| = 23, |TEST| = 23, with
   TR∩VA = TR∩TE = VA∩TE = ∅. The basket corpus (3714 rows / 93 domains) splits into 2680 rows over
   67 TRAIN domains and 920 rows over 23 VALIDATION domains, with **0 TEST rows**. The built fit
   populations are 670 slots / 67 domains vs 230 slots / 23 domains, sharing **0 (domain, slot)
   keys and 0 prompt_ids**, with different y-vector hashes. So the reported `slots=230 domains=23`
   is what the code actually computed — explanation (c) is dead.
2. **The validation rho moves with the fit.** Refitting on 33 of the 67 TRAIN domains shifts it to
   0.6468854 (basket) and 0.6226473 (button). A leaked number would not move.
3. **The same code path produces a large gap elsewhere** — 0.0515 on button, and 0.0471 for the F5
   incumbent on basket. A systematic aliasing bug would not be selective.

The collision is unsurprising once looked at: basket's rel-6 TRAIN row is a **flat plateau**
(0.6417 / 0.6525 / 0.6512 / 0.6386 across L16–L22) and the held-out transfer lands in the same band.

**Status: the basket validation figure MAY be cited as independent validation** — quoted as
**0.65252 validation vs 0.65245 train** so the near-equality is not mistaken for identity, and
carrying its existing caveats (rel-6 is a plateau, not a resolved peak; `train_best_perm_p` is a
single-cell bound, not family-wise).

**Hardening applied** to `scripts/dcs_cont_qprobe.py` (additive, in the file's existing
`REFUSING:` + return-2 style, all raising, none warning or defaulting):

* a **split-level** guard before any load — refuses on empty TRAIN, empty VALIDATION, TR∩VA,
  TR∩TEST, VA∩TEST;
* a **population-level** guard before any fitting — `_built_keys()` enumerates exactly what
  `build()` would return (same filter, same `(domain, family_slot) × cell` key, same 4-cell
  completeness rule) **without reading any `[site, layer]` slice**, so it costs no tensor I/O, and
  refuses on an empty TRAIN population, an empty VALIDATION population, shared keys, or shared
  prompt_ids.

All six guards pass on current data, so **no frozen result changes**. This closes P0.3 and, with
S-002, completes **Phase 0**.

### Phase 0 closing status

| item | status |
|---|---|
| P0.1 basket endpoint = CANNOT ANSWER, artifact committed | ✔ |
| P0.2 size-match arm analysed | ✔ (answer: **CANNOT ANSWER**, claim **WITHDRAWN**) |
| P0.3 QPROBE basket validation | ✔ (coincidence; citable; guards added) |
| P0.4 `latest_dir` hardening | ✔ (`strict_run_dir`, shared by both analysers) |
| P0.5 independent re-derivation of the button headline | ✔ (run clean; statistic **CORRECTED**) |
| P0.6 same-node / same-architecture replicate | ⏳ jobs 896356 (3090, running), 896363 (l40s, pending) |

---

## S-010 — adversarial code review of the Phase-1 code: **no BLOCKERs, six MAJORs, all fixed**

`reports/DCS_CSI_CODE_REVIEW_PHASE1.md`. An independent reviewer read `SubspaceDonorPatch`,
`orthonormalise`, the factored-out `assert_token_identity`, the `score_behavior` wiring,
`dcs_csi_axis.py` and the test file, with instructions to find bugs that produce a **wrong but
plausible scientific number**, and to verify numerically rather than speculate.

### Verified correct (the two load-bearing claims are EXACT, not approximate)

* **A full-rank `SubspaceDonorPatch` equals `DonorPatch` bit-identically** in fp32 *and* bf16
  (max|diff| = 0.0). This is what makes the whole-state arm a valid upper bound for the subspace
  arm — the recovery-fraction denominator is sound.
* Per-position **norm matching exact to 1e−9**; ridge dual == primal to **8.3e−17**;
  **PLS1 deflation is genuine** (W rows mutually orthonormal, Gram off-diagonal 5.6e−17, rank 4 of
  4) — *the historical "rank-1 in a hat" defect is absent*; `shuffled_y` preserves within-domain
  multisets with 0/200 identity draws; the PLS fit is strictly inside the LOO fold; the TRAIN-only
  fit population is confirmed.

### The six MAJORs, and what each would have done

| # | finding | what it would have produced | fix |
|---|---|---|---|
| **M6** | **the add-then-remove test was VACUOUS** — the two patches ran in *separate* forwards, so the "remove" patch's donor equalled the live state and delta was identically zero. **Proven**: the assertion still passed with the write path disabled (`scale=0.0`). | Phase 2's necessity arm had **no test coverage at all** while appearing to have it | rewritten to compose **both hooks in ONE forward** (which is what the intervention actually is); holds at any rank by idempotence of P; plus an explicit **anti-vacuity** check that the forward patch alone *does* change the output (it does, by 9.45e−02) |
| **M2** | a basis fit at layer L18 could be written at any `--rescue-layer` behind a `print` **WARNING** | a different experiment wearing the same arm label | now `SystemExit` — this is the repo's own *"threshold published but never enforced"* class, and `assert_control_norm_matched` SystemExits on the analogous condition |
| **M3** | nothing cross-checked the axis's declared codeword/bank against the population being scored | a **button-fit axis silently scored on a basket run** — and per S-008 `prompt_id` is 100 % shared across banks, so *nothing downstream would catch it* | refuses when the basis's codeword is not named by `--bank` |
| **M1** | `--fit-prompt` was a free-text **label** never checked against the corpus | an artifact that **misdescribes its own fit population** | derived from the rows' `query_kind` and refused on mismatch; `--codeword` checked against `target_surface` too |
| **M4** | a TRAIN-fit axis scored on TRAIN rows was undetectable from the artifact; the fit-domain list went to **stdout only** | in-sample results indistinguishable from held-out ones | the axis now carries a `fit_population.domains_sha16`; `rescue_basis_meta` travels **on every row**; the analyser reports `evaluation_is_in_sample` per arm by intersecting scored domains with the axis artifact's fit-domain list |
| **M5** | the degenerate norm-match branch was **counted but never enforced**; its fallback direction `W.sum(0)` is an arbitrary QR-gauge artifact, not reproducible across LAPACK versions for r > 1 | a control arm that is norm-matched but **scientifically meaningless**, completing with `fired=True` | now **raises** by default (`refuse_degenerate=True`); tests opt in to exercise the branch |

Plus **m2** (a real minor): the prefill/decode guard `hidden.shape[1] <= max(positions)` is wrong
when the only patched position is 0 — a length-1 decode step satisfies `1 <= 0 == False` and the
hook would write during decoding. Fixed in **both** patchers and covered by a new test.

`tests/test_subspace_donor_patch.py` now **31/31 PASS**.

**Process note.** Three of these six (M1, M2, M3) are the same defect in three places: *a
provenance field that describes the experiment but is never checked against it.* That is worth
naming, because the sprint will keep adding such fields. The rule going forward: **every field
written into an artifact's provenance must have a code path that can refuse on it**, or it is
decoration.

---

## S-011 — BLOCKER: `git push` is credential-blocked. Work continues locally.

```
remote: Invalid username or token. Password authentication is not supported for Git operations.
fatal: Authentication failed for 'https://github.com/omeryosef7/teza_first_poc_with_mahmood.git/'
```

This matches the predecessor log's standing "`git push` token-blocked" item, so it is not new and
not something I can resolve — it needs a valid PAT from Omer. **Per the operating mode: recorded,
the dependency is marked, and the sprint continues.** All work is committed locally on
`behavioral-causality-sprint` and will push in one go once a token exists. I will not retry the
same impossible push on every loop tick.

**→ ACTION FOR OMER (non-blocking):** refresh the GitHub PAT (or switch the remote to SSH) when
convenient. Nothing in the sprint waits on it.

## S-012 — loop armed; jobs in flight at the end of the first working block

A 30-minute operational loop is scheduled (`*/30 * * * *`). Each tick: poll SLURM, collect finished
artifacts, launch the next valid work, append to this log, commit. A deeper adversarial code+output
review every ~4 h (the first one is S-010).

| job | what | node | status |
|---|---|---|---|
| 896356 | 4 button patch arms, ONE allocation (P0.6) | n-303 **RTX 3090** | RUNNING (~33 min, arm 1/4) |
| 896363 | same 4 arms pinned **l40s** (P0.6b) | — | PENDING (Resources) |
| 896369 | basket `semantic_one_word` corpus | n-306 | RUNNING (~23 min) |
| 896372 | **behavioural axis fit, button** (Phase-1 primary candidate) | n-306 | RUNNING (~18 min) |
| 896371 | semantic axis fit | — | **FAILED** — no multiposition cache (S-008c) |
| 896365 | basket semantic extraction, first attempt | n-306 | **FAILED** — `--model` unpinned (S-006) |

Ready and waiting on the axis artifact: `slurm_scripts/dcs_csi_p1_smoke.slurm` (6-arm liveness
smoke) then `slurm_scripts/dcs_csi_p1_arms.slurm` (group A = gates + primary contrast, group B =
control distribution with a `KO_AXIS_ANCHOR` re-run so cross-allocation drift is **measured, not
assumed**).

Housekeeping: `reports/DCS_CSI_REDERIVE_PATCH_button.json` was briefly overwritten with a
2000-draw bootstrap while smoke-testing the `strict_run_dir` refactor; regenerated at the
preregistered 20000 draws. Numbers unchanged (recovery +0.02778, CI [0.00556, 0.05556], 5 of 90
domains).

Two run directories need quarantining once their live siblings finish (a failed attempt left a
sibling dir that would make `strict_run_dir` correctly refuse as ambiguous):
`cont1_semantic_one_word_basket_bomb_20260915_170803_2607554` (from failed job 896365).

---

## S-013 — the Phase-1 candidate axis is BUILT (button, behavioural fit), and it independently reproduces Q1

Job 896372 COMPLETED. `configs/dcs_csi_axis_button_behavioral.{pt,json}`, 20 named bases.

### Independent reproduction of the published query-probe number

| | published `DCS_CONT_QPROBE.json` | `dcs_csi_axis.py` (this sprint) |
|---|---|---|
| site | rel-6 | rel-6 (frozen, not searched) |
| layer | 20 | **20** (selected on TRAIN) |
| TRAIN LOO rho | 0.5935 | **0.5935** |
| slots / domains | 670 / 67 | 670 / 67 |

Two independently written scripts, the same corpus and readout, the same number. That is a real
cross-check of the whole feature-assembly path (within-domain centring, the ABCE completeness rule,
the `(domain, family_slot)` join, leave-one-**domain**-out), not a re-print.

### What the fit actually says

**The layer is on a plateau, and the selection is not a resolved peak:**

| L16 | L18 | **L20** | L22 | L24 | L26 | L28 | L30 | L31 |
|---|---|---|---|---|---|---|---|---|
| 0.5781 | 0.5931 | **0.5935** | 0.5894 | 0.5853 | 0.5803 | 0.5798 | 0.5596 | 0.5407 |

L18 and L20 differ by **0.0004**. So "layer 20" is a consistent *choice* within L18–L22, not an
identified maximum — the same plateau caveat the query-probe result already carried. This matters
now that review M2 makes a layer mismatch a hard refusal: the refusal enforces *consistency between
the fit and the write*, which is what it is for; it does not certify that L20 is special.

**The low-rank PLS family does NOT beat the rank-1 ridge on TRAIN:**

| PLS r=1 | r=2 | r=3 | r=4 | r=5 | ridge (rank-1 direction) |
|---|---|---|---|---|---|
| 0.5021 | 0.5350 | 0.5482 | 0.5717 | 0.5767 | **0.5935** |

Two honest readings, both recorded before any intervention runs:
* every PLS rank scores **below** the plain ridge, so **`cand_rank1` is the natural primary
  candidate** and the prereg's ordering stands;
* `selected_rank = 5` sits **at the edge of the search grid** and is still rising, so it is **not a
  well-identified rank**. `KO_PLS` is therefore **exploratory**, not a second headline, and no
  claim of the form "the representation is r-dimensional" may be made from it. (The plan's §6.2
  question "does increasing rank give genuine VALIDATION improvement" remains open and is
  answerable only on VALIDATION.)

Note also that PLS component 1 has **|cos| = 0.566** with the ridge direction — the two candidates
are genuinely different directions, not reparametrisations of one.

**The shuffled-label controls behave**: TRAIN LOO rho = 0.0547, 0.0484, −0.0085, 0.0182, 0.0022 —
i.e. near zero, as a domain-preserving label shuffle should be. `ctrl_orth` has **|cos| = 0.0
exactly** with the candidate.

### Provenance re-run

896372 used the **pre-review** script, so its artifact lacks the `fit_population.domains_sha16`
fingerprint that review M4's row-level in-sample detection reads, and it never exercised M1's
corpus-vs-`--fit-prompt` check. Re-submitted as **896396** with the fixed script; the numbers must
come out identical, which doubles as a reproducibility check. Phase-1 scoring waits on that
artifact so that every scored row carries a complete, checkable provenance record.

---

## S-014 — the axis artifact is deterministic ON A NODE, and the sha mismatch was cross-node float noise

The post-review re-run (896398, n-303) reproduced 896372 (n-306) exactly on **every scalar** —
selected layer 20, TRAIN LOO rho 0.5935, selected rank 5, 670 rows / 67 domains, identical layer
grid, identical rank grid, identical `bank_sha16` — but the **basis sha16 values differed**. That
needed explaining rather than waving through, because a candidate direction that changes between
builds is a candidate whose identity is not well-defined.

**Which bases differed is itself the diagnosis:**

| | bases |
|---|---|
| **identical** (8) | `ctrl_random0..7` — pure seeded `torch.randn`, no data involved |
| **differed** (12) | `cand_rank1`, `cand_pls1..5`, `ctrl_orth` (derived from `cand_rank1`), `ctrl_shuffled0..4` — every **data-derived** basis |

That is the signature of last-bit BLAS/LAPACK differences in the 670×670 dual solve, not a logic
bug. Confirmed by measurement rather than left as an inference:

**Three builds on the SAME node (n-303) are BIT-IDENTICAL** — `|cos| = 1.00000000000000` and
`max|elementwise diff| = 0.000e+00` for `cand_rank1`, `cand_pls5`, `ctrl_orth`, `ctrl_shuffled0`
and `ctrl_random0`, across all three pairwise comparisons. So the script is deterministic given a
fixed node; the only varying factor was n-306 vs n-303. A direct cross-node comparison
(job 896409, pinned `--nodelist=n-306`) is running to put a number on the residual.

**Practical risk to the experiment: none.** The basis is built **once** into a `.pt` file and every
arm reads that same file, so no arm-to-arm comparison can be affected by it. The finding matters
for *reproducibility by a third party*, and the honest statement is: the axis is reproducible to
float precision, bit-reproducible only on matched hardware — which is the same caveat this project
already carries for generation.

## S-015 — operational: I caused an NFS contention slowdown, and the diagnostic worked

Job 896369 (basket `semantic_one_word` extraction) sat at **35 minutes with zero rows written**.
It is **not hung**: the `.err` weight-loading bar reads `64% | 185/291 [33:31<21:13]` — i.e. it is
loading Llama weights at ~10 s/shard instead of seconds. The button sibling did the whole job in
873 s.

Cause: I had stacked three of my own jobs on **n-306** — this GPU model-load plus CPU axis jobs
that each mmap a 12 GB corpus over the same NFS mount. That is precisely the documented
"3 model-loading jobs on one node → large weight-load slowdown; cap ~2 per node and spread"
failure, and I walked into it by submitting CPU analysis wherever the scheduler put it.

Projected: ~52 min load + ~15 min extraction ≈ 67 min against a `--time=01:30:00` wall — it should
finish with ~23 min of margin, so no action beyond not adding further load to n-306.

**Standing rule adopted for the rest of this sprint:** before submitting, check which node my
existing jobs hold, and spread — especially never co-schedule a GPU model-load with a large-mmap
CPU job. The weight-loading bar in `.err`, not `squeue`, is the liveness test.

---

## S-016 — MEASURED: cross-architecture generation churn is **77 %**, but the refusal endpoint flips on **0.6 %** of rows

The first arm of the P0.6 replicate finished, giving a clean paired measurement that this project
has previously only had a rough figure for. The **CTRL arm** was run twice with *identical* bank,
prompts, exclusions, seed (20260816), `--max-new`, dtype (bf16), attention implementation (eager)
and model revision — differing **only in GPU architecture**:

| | L40S (t-806) | RTX 3090 (n-303) |
|---|---|---|
| common `prompt_id`s | 180 | 180 |
| **byte-identical completions** | \multicolumn{2}{c}{**42 / 180 = 23.3 %**} | |
| refusal rows | 20 | 21 |
| **refusal LABEL flips** | \multicolumn{2}{c}{**1 / 180 = 0.6 %**} | |

**Read both numbers together — they say opposite-sounding things and both matter.**

* **Greedy decoding is not reproducible across GPU architectures**: 77 % of completions changed.
  This independently confirms the standing prohibition on ever writing "greedy decoding reproduces
  byte-identically", and it is now a *paired, same-prompt* number rather than an aggregate.
* **The refusal endpoint is nevertheless very stable**: a single label flipped out of 180. The
  keyword refusal detector is reading something robust to the token-level churn.

**Why this is not merely reassuring — it sizes the risk on the S-002 headline.** The button recovery
effect is a domain-mean of **+0.0278 carried by 5 refusal events**. Cross-architecture churn
contributes ~1 flipped label per 180 rows *per arm*, so differencing two arms could inject on the
order of 1–2 rows of noise against a 5-row signal — roughly a **3:1 signal-to-churn ratio**. Not
fatal, but not comfortable, and it is exactly why the P0.6 design puts all four arms in **one
allocation on one node**, where this term should be **zero** rather than small. The two replicates
now running (896356 all-3090, 896363 all-L40S) will show whether the effect survives with that term
removed, and whether it reproduces on two different architectures independently.

This also retroactively supports the S-002 verdict that the published arms (ctrl/ko on t-806,
rescue on n-801, size-match on n-803 — **all L40S**) were not *invalidated* by running on three
nodes: same architecture is the condition that matters, and the churn measured here is *across*
architectures. Within-architecture, cross-node churn is measured by the pair
(896363 on n-801 vs the published t-806 run) once 896363's CTRL arm lands.

---

## S-017 — Phase 4 §9.1 (template generalisation) is **BLOCKED on a new extraction**, and here is the cheap test that is available instead

Matan's concern — *is the representation just detecting prompt/template structure?* — is plan §9.1,
and I checked whether it can be answered from the caches already on disk. It cannot.

Parsing `family_id` (`domain|split|slot|n_ex|strength|consistency|example_position|role_style|query_kind`)
across all 3720 rows of the behavioural corpus:

| axis | distinct values in the corpus |
|---|---|
| domain | 93 |
| slot | 5 (`slot0/4/8/12/16`) |
| bank-internal split | 2 (`dev`, `heldout`) |
| n_examples | **1** (`n4`) |
| strength | **1** (`none`) |
| consistency | **1** (`consistent`) |
| **example_position** | **1** (`near`) |
| **role_style** | **1** (`plain`) |

**The corpus contains exactly one template family.** `example_position` and `role_style` are the
two template axes the generator supports, and both are constant here. So a train-on-template-A /
test-on-template-B experiment is **not analysable from existing activations** — it needs a new GPU
extraction over template-varied rows (which *do* exist in the bank; they were simply not captured).

Recorded as a real cost, not waved away: §9.1 requires **one new extraction**, and it is queued
behind Phase 1 rather than dropped. It should not be attempted with a substitute axis and called
template generalisation.

**What IS available now, and is worth doing:** the bank-internal `dev` / `heldout` split is a
**prompt-level** holdout orthogonal to the ts116m domain split — different demonstration sentences,
same template, same domains. Fitting the axis on `dev` rows and scoring it on `heldout` rows within
the same TRAIN domains tests whether the axis depends on the *particular demonstration sentences*
rather than on installed meaning. That is a weaker claim than template transfer and **must not be
reported as template transfer**, but it is a genuine generalisation check, it is pure CPU, and it
reuses `dcs_csi_axis.build()` unchanged. Added to the checklist as **P4-a**.

Also noted: this corpus carries **93 domains**, i.e. it includes the three globally-excluded ones;
the exclusion is applied at fit time (`EXCLUDED_DOMAINS`), which is why the fit population is 67.

---

## S-018 — P4-a RESULT: the installation axis is **not sentence-specific**. It transfers across demonstration sentences at full strength.

`scripts/dcs_csi_prompt_transfer.py` → `reports/DCS_CSI_PROMPT_TRANSFER_button.json`, job 896413.
Button, site rel-6, layer L20, TRAIN domains only, the same `build`/ridge/leave-one-domain-out
imported from `dcs_csi_axis` so only the row filter differs.

| fit on | scored on | fit rows → score rows | within-fit LOO rho | **cross-prompt transfer rho** |
|---|---|---|---|---|
| `dev` | `heldout` | 335 → 335 | 0.5057 | **+0.6326** |
| `heldout` | `dev` | 335 → 335 | 0.5865 | **+0.5634** |
| | | | mean **0.546** | mean **+0.598** |

The axis learned from one set of demonstration sentences predicts installation on a **different set
of demonstration sentences** at ρ ≈ 0.60 — essentially the same as the full-TRAIN in-sample LOO
(0.5935 on 670 rows). **Retention 1.095.**

**How to read the retention > 1, honestly.** It does *not* mean transfer beats in-sample. The
within-fit LOO is computed on a **halved** fit set (335 rows), so it is the noisier, weaker number;
the transfer fits on 335 and scores on a *different* 335. The correct statement is: **halving the
data costs the axis nothing on held-out sentences** — there is no sentence-level overfitting to
recover from.

**What this rules out.** One live alternative explanation for the query-probe signal was that the
axis memorises the particular demonstration sentences used to install the mapping. It does not.

**What this does NOT show, and must not be reported as:**

* **Not template generalisation.** Every row in this corpus is `example_position=near`,
  `role_style=plain` — one template family (S-017). §9.1 still needs a new extraction.
* **Not domain generalisation.** The `dev`/`heldout` split is *within* the same TRAIN domains, so
  domain topic is shared between fit and score. Within-domain centring is what guards against
  topic here, not the design. Domain-level generalisation is the separate TRAIN→VALIDATION
  transfer, already reported as +0.645.
* **Not a causal claim.** This is the observational axis. Whether it *mediates* anything is
  Phase 1, which is what the GPU arms are for.

So the axis now has three independent generalisation results — across **domains** (TRAIN→VAL
+0.645), across **codewords** (button +0.645 / basket +0.653), and now across **demonstration
sentences** (+0.598, retention 1.095) — and one known untested axis, **templates**.

---

## S-019 — **CORRECTION to S-014**: the sha mismatch was *not* cross-node float noise. Cross-node builds are bit-identical.

S-014 concluded, from the pattern of which bases differed, that the axis sha16 mismatch between
jobs 896372 (n-306) and 896398 (n-303) was "the signature of last-bit BLAS/LAPACK differences" and
flagged a direct cross-node measurement as pending. **That measurement has now run (job 896409,
pinned `--nodelist=n-306`) and it refutes the inference.**

n-303 build vs n-306 build, same script revision:

| basis | 1 − \|cos\| | max\|elementwise diff\| |
|---|---|---|
| `cand_rank1` | −1.11e−15 | **0.000e+00** |
| `cand_pls1` | −8.88e−16 | **0.000e+00** |
| `cand_pls5` | −8.88e−16 | **0.000e+00** |
| `ctrl_orth` | −1.33e−15 | **0.000e+00** |
| `ctrl_shuffled0` | −2.00e−15 | **0.000e+00** |
| `ctrl_random0` | −4.44e−16 | **0.000e+00** |

(The tiny negative values are float rounding on a cosine of exactly 1.) **Every basis is
bit-identical across nodes.** Together with the three bit-identical same-node builds from S-014,
that is four builds on two different nodes agreeing exactly.

**So what differed about 896372?** It ran a **different revision of the script** — the pre-review
version, before the M1/M4 patch. Its `.pt` was overwritten by the re-run, so its tensors no longer
exist and the difference **cannot now be attributed definitively**. What is bounded: every scalar
summary matched to 4 dp (selected layer, TRAIN LOO rho, selected rank, the full layer grid, the
full rank grid), and the seeded-random bases were identical, so whatever moved was small and
data-path-local.

**The honest statement, replacing S-014's:** the axis build is **bit-reproducible across every node
and run that can still be compared**. One earlier build under a different script revision produced
different basis hashes with identical scalar summaries; its tensors are gone, so the cause is
**unexplained**, not "cross-node noise". Practical risk to the experiment remains **zero** — the
basis is built once into a `.pt` that every arm reads.

**Process lesson, and it is the reason this correction exists:** S-014 offered a *mechanism* ("BLAS
noise") on the strength of a *pattern* (which bases differed), and the pattern was equally
consistent with "a code change touched the data path". I labelled the measurement "pending" and
then wrote the conclusion anyway. Rule reaffirmed: **a diagnosis stated before its confirming
measurement is a hypothesis, and must be written as one.** Also: do not overwrite an artifact you
are still using as a comparison baseline — copying only the JSON cost the ability to answer this.

---

## S-020 — loop tick 18:02. Claim table opened; basket-side CPU work launched.

**Deliverable added: `reports/DCS_CSI_CLAIM_TABLE.md`** (plan §21/§27), maintained live and
organised as the plan requires — **what we can defend / exploratory / CANNOT ANSWER / must not
say**. It does not overwrite `reports/DCS_CONT_CLAIM_TABLE.md`, which stays the predecessor phase's
frozen record. Every row cites its statistic, population, caveats and sprint entry. Section D now
carries **14** standing prohibitions, four of them new this sprint (the withdrawn size-match pass,
the downgraded 42 % recovery, the sentence-vs-template distinction, and the refuted
node-sensitivity claim).

**Launched, cross-codeword replication of the two CPU results (both off n-306, per S-015):**

| job | what |
|---|---|
| 896422 | basket behavioural axis fit (the Phase-1 basket candidate) |
| 896423 | basket prompt-level transfer — does S-018's "not sentence-specific" replicate on a second codeword? |

**Still in flight:** 896356 (3090 patch replicate, arm 2/4), 896363 (L40S replicate, arm 1/4),
896369 (basket semantic corpus, 91 % through its weight load), 896421 (Phase-1 smoke, PENDING).

**Scheduler note:** everything new is PENDING on `(Priority)` — fair-share is depleted by this
sprint's own submissions. Not a fault, and not something to fix by resubmitting; the 30-minute rule
applies from `SUBMIT_TIME` and nothing has crossed it yet.

---

## S-021 — BASKET: the axis reproduces the published number too, and the "not sentence-specific" result REPLICATES cross-codeword

Jobs 896422 (axis) and 896423 (prompt transfer), both COMPLETED.

### Second independent reproduction of the published query-probe number

| | published `DCS_CONT_QPROBE_basket.json` | `dcs_csi_axis.py` |
|---|---|---|
| site / layer | rel-6 / L18 | rel-6 / **L18** (selected on TRAIN) |
| TRAIN LOO rho | 0.6525 | **0.6525** |
| slots / domains | 670 / 67 | 670 / 67 |

So the axis pipeline now reproduces the prior result on **both** codewords, at each one's own
selected layer. `bank_sha16 = 79511d9e254571e6` confirms the basket bank (distinct from button's
`dcd92d723f3e6d00`), so the never-pool guard held.

### An asymmetry in the rank curve that corrects a button-specific statement

| PLS rank | r1 | r2 | r3 | r4 | r5 | rank-1 ridge |
|---|---|---|---|---|---|---|
| **button** | 0.5021 | 0.5350 | 0.5482 | 0.5717 | **0.5767** ← boundary | 0.5935 |
| **basket** | 0.5629 | 0.6354 | **0.6407** ← interior peak | 0.6206 | 0.6123 | 0.6525 |

S-013 said "the selected rank sits at the grid boundary and is therefore not well identified."
**That is true of button and NOT of basket** — basket's curve has a clean interior maximum at
**r = 3**, rises to it and falls away. The corrected statement:

* on **both** codewords every PLS rank scores **below** the rank-1 ridge, so `cand_rank1` remains
  the primary candidate on both;
* the *rank* is **unidentified on button** (boundary) and **identified at r = 3 on basket**
  (interior peak). `KO_PLS` therefore stays exploratory on button but is a meaningful second arm on
  basket.

`ctrl_orth` has |cos| = 0.0 exactly on both. The basket shuffled-label controls all sit slightly
**negative** (−0.040, −0.049, −0.084, −0.047, −0.042), i.e. near zero as required.

### The prompt-level transfer result replicates

| codeword | fit→score | within-fit LOO | cross-prompt transfer | retention |
|---|---|---|---|---|
| button | dev→heldout | 0.5057 | +0.6326 | 1.095 |
| button | heldout→dev | 0.5865 | +0.5634 | 0.960 |
| **button mean** | | 0.546 | **+0.598** | **1.095** |
| basket | dev→heldout | 0.5923 | +0.6705 | 1.132 |
| basket | heldout→dev | 0.6750 | +0.5820 | 0.862 |
| **basket mean** | | 0.634 | **+0.626** | **0.988** |

Basket's two directions **bracket 1.0** (1.132 and 0.862) and average to 0.988 — which is the
cleaner picture and confirms the S-018 reading that retention is ≈ 1 with direction-to-direction
noise, rather than transfer genuinely exceeding in-sample. **The axis is not sentence-specific on
either codeword.**

Claim table row **D4** is updated to cross-codeword, and its caveats stand unchanged: this is
sentence-level, not template-level (C3), not domain-level, and not causal.

## S-022 — pre-flight of the Phase-1 launcher population (plan §13 gate)

Before spending a 7-arm allocation, checked the exact population each arm will select — a wrong
`--expect-n` aborts the whole job, and a split impurity would invalidate it silently:

| codeword | split | `expect_n` | domains | wrong-split domains | excluded domains present | cells selected |
|---|---|---|---|---|---|---|
| button | train | 670 | 67 | **0** | **0** | `['C']` |
| button | validation | 230 | 23 | **0** | **0** | `['C']` |
| basket | train | 670 | 67 | **0** | **0** | `['C']` |
| basket | validation | 230 | 23 | **0** | **0** | `['C']` |

All four match the expected counts exactly, contain no domain from another split and none of the
three globally-excluded domains. The selection resolves to **cell C only**, which is correct —
`condition=natural_doublespeak` *is* cell C, and installation is defined on cell C — and it
confirms the launcher's inline `NKEEP` computation agrees with an independent recount.

## S-023 — tick close 18:10

| job | what | state |
|---|---|---|
| 896421 | **Phase-1 smoke** (6 arms, 24 rows), L20 / rank 5 | RUNNING on n-302, loading weights |
| 896369 | basket `semantic_one_word` corpus | RUNNING — past the weight load, **919 / 3720 rows** written |
| 896356 | 3090 patch replicate | RUNNING, arm 2/4 |
| 896363 | L40S patch replicate | RUNNING, arm 1/4 |

Completed this tick: 896422 (basket axis), 896423 (basket prompt transfer), plus the claim table
and this pre-flight. Nothing is blocked except `git push` (S-011). Eleven commits on the branch.

---

## S-024 — the Phase-1 smoke STALLED on weight loading; diagnosed, cancelled, resubmitted

Job 896421 (Phase-1 smoke) on **n-302** sat at `Loading weights: 1/291 [03:24<16:28:37, 204.54s/it]`
and **the bar did not advance for ~6 minutes**. Against a 2 h walltime and a projection of 16.5 h,
that job would have died having produced nothing while holding a GPU.

This is the documented diagnostic working as intended: **`squeue` said RUNNING; the weight-loading
bar in `.err` said stalled.** `squeue` is liveness for the *allocation*, not for the *work*.
Distinguishing "stuck at shard 1" from "slow but advancing" required two readings a few minutes
apart — one reading would have been an outlier (the first shard is legitimately the slowest), and
S-015's basket job *was* genuinely slow-but-advancing and correctly left alone. One data point
cannot tell those apart; two can.

Cancelled and resubmitted as **896495** with `--exclude=n-302,n-306`; it picked up **n-350** and is
loading normally.

**A refinement to S-015's rule.** S-015 framed the contention as per-node ("cap ~2 model loads per
node and spread"). That is incomplete. All of these jobs read the **same Llama snapshot from the
same NFS export** (`matanbentov/hub/...`), so the binding constraint is the number of **concurrent
reads of that shared export**, not how the jobs are distributed across nodes — spreading across
nodes does not help if four jobs are all pulling 16 GB from one mount. The corrected rule:

> **Cap concurrent model loads globally, not per node.** Before submitting a job that loads the
> model, check how many of my running jobs are still in their weight-loading phase — not how many
> nodes they occupy. Once a job is past its load, it no longer contends.

By the time 896495 launched, the other three jobs were all past their loads, which is why it is
loading normally on a node chosen by the scheduler.

Basket `semantic_one_word` corpus (896369): past the load, **2965 / 3720 rows** written.

---

## S-025 — the `semantic` candidate family is UNBLOCKED, and the anti-circularity guard is opted into explicitly rather than weakened

S-008(c) deferred the semantic-fit candidate family for two reasons. **The first has now
dissolved:** the basket `semantic_one_word` extraction (896369) produced **both**
`final_occurrence_reps.pt` *and* `multiposition_reps.pt` (13 GB). So a semantic corpus *can* carry
the multiposition cache — the button-semantic corpus's missing one was a **transient failure**
(consistent with the recorded disk-space event of CONT-161), not a structural property of semantic
prompts. S-008's diagnosis of *that* run stands; its implied generalisation does not.

**The second reason — the frozen anti-circularity guard — is a scientific question, and here is the
argument, made explicitly so it can be reviewed rather than smuggled in.**

`lpm.load_corpus` refuses a semantic corpus because *"the semantic prompt's next token IS the
target, so a representation read there predicts it circularly"* (REVIEW-1/T0-4, CONT-ENTRY 002).
**That is correct, and it is correct about a PREDICTIVE claim** — which is exactly what the
query-probe and F5 results are. It is not correct about an **interventional** one:

* In Phase 1 the fitted direction only decides **which component of the state an intervention
  restores**. The causal inference comes from the intervention and its controls, not from the fit.
* The **controls are fit the same way** — `ctrl_orth` is derived from the candidate,
  `ctrl_shuffled*` use the identical ridge on shuffled labels — so whatever circularity the
  candidate enjoys, the controls enjoy too. The primary contrast `KO_AXIS − KO_ORTH` differences it
  out.
* A circularly-fit direction is a legitimate thing to **intervene along**; it is not a legitimate
  thing to **report a predictive rho for**.

**Implementation, deliberately conservative.** `lpm.load_corpus` gains
`allow_query_kinds=("behavioral",)` — the **default is unchanged and every existing caller keeps
the original refusal**. `dcs_csi_axis.py` opts in *only* when `--fit-prompt semantic` was declared,
and `--fit-prompt` is itself checked against the corpus rows (review M1), so the opt-in cannot be
used to slip a semantic corpus in under a behavioural label. The justification above is written
into both call sites, and a standing prohibition is added to the claim table:

> **Must not say:** any predictive rho obtained from a `--fit-prompt semantic` fit. That fit's only
> legitimate output is a direction to intervene along.

**Still required before the semantic family can run:** a button `semantic_one_word` re-extraction
with the multiposition cache (~13 GB, one GPU job). It is **not** submitted yet — per S-024's
corrected rule, the smoke (896495) is mid-weight-load and adding a concurrent load of the same NFS
snapshot is what caused the stall. It goes in once the smoke is past its load.

Disk check before committing to another 13 GB cache: the filesystem is at **94 % with 1.3 T free**,
so one more corpus is affordable; the two 12–13 GB behavioural caches plus this one are the
dominant consumers and are reconstructable if space becomes tight.

---

## S-026 — P0.6 FIRST REPLICATE: in a single allocation the recovery effect is **larger and now clears α = 0.05**

Job 896356: CTRL, KO and RESCUE_CLEAN run back-to-back in **one allocation on one node**
(n-303, `geforce_rtx_3090`), so the hardware term that S-016 measured is **zero by construction**
rather than small. `reports/DCS_CSI_REDERIVE_PATCH_button_p0cmp.json`; VERDICT **PASS**.

| | published arms (3 nodes, all l40s) | **single-allocation replicate (1 node, 3090)** |
|---|---|---|
| CTRL | 0.1111 | 0.1167 |
| KO | 0.0444 | 0.0500 |
| RESCUE_CLEAN | 0.0722 | **0.0889** |
| KO de-refusal (CTRL−KO) | +0.0667, k=12, p = 4.88e−4 | **+0.0667, k=12, p = 4.88e−4** |
| **recovery (RESCUE−KO)** | +0.0278, **k=5**, p = **0.0625** *(= its floor)* | **+0.0389**, **k=7**, p = **0.0156** *(= its floor)* |
| recovery fraction | 0.417 [0.133, 0.714] | **0.583 [0.286, 0.875]** |
| residual (CTRL−RESCUE) | +0.0389 | +0.0278 |

**The KO de-refusal reproduces to four decimal places** — same point estimate, same 12 informative
domains, same p. That is a strong sign the endpoint and population are stable.

**The recovery is larger and now significant by the exact test.** It rests on **7** informative
domains instead of 5, all same-signed, and the exact two-sided sign-flip p is **0.0156 < 0.05**.
Note it is *again exactly at its attainable floor* (2/2⁷ = 0.015625) — the test has once more
exhausted its resolution — but this time **the floor itself is below 0.05**, which the published
run's 0.0625 floor could never be.

**How much weight this carries, stated carefully.** This is a **second experiment**, not a
re-analysis: same prompts and seed, different hardware, so the two estimates (+0.0278 on 5 domains,
+0.0389 on 7 domains) are two draws whose difference is within the churn S-016 measured. Two
independent runs both showing a positive recovery with **every** informative domain moving in the
predicted direction and **none against** (5/5 and 7/7) is meaningfully better than one. It does not
yet make E1 a confirmatory result — the endpoint is still resolution-limited, the power analysis
still says D ≈ 145 for 80 % power, and TEST is still unspent. The honest upgrade is:

> **E1 (revised): directionally consistent across two independent runs, and significant by an exact
> domain-level test in the hardware-controlled replicate (p = 0.0156, at its floor). Still
> underpowered and still exploratory; not a confirmatory claim.**

The L40S replicate (896363, arms 3/4 done) will say whether this holds on a *second architecture*.
If it does, the recovery has reproduced on two architectures and in two hardware-controlled
allocations, which is about as much as this 90-domain endpoint can be asked to give.

**Verifier fix that this exposed.** `slurm_node_for_tag` greps the logs for `--tag <tag>`, which
works when each arm is its own sbatch but **not** when arms run inside a wrapper `.slurm` — the tag
never reaches the job's stdout. The verifier therefore reported "hardware unknown" and **VOIDed the
most hardware-controlled run in the sprint**. Added `--slurm-job` to declare the allocation
explicitly, which is precisely the fact the wrapper design guarantees. A verifier that fails closed
on missing provenance is right to; the fix is to give it the provenance, not to relax the check.

---

## S-027 — the semantic-fit axis empirically VINDICATES the anti-circularity guard, and that changes how Phase 1 may use it

Job 896543 built the basket **semantic**-fit axis (the first use of the S-025 opt-in). The result
is the clearest possible demonstration of why the guard exists.

**Layer grid, basket, `--fit-prompt semantic` (state and target read on the SAME forward):**

| L16 | L18 | L20 | L22 | L24 | L26 | L28 | **L30** | L31 |
|---|---|---|---|---|---|---|---|---|
| 0.6105 | 0.6194 | 0.6316 | 0.6972 | 0.7055 | 0.7282 | 0.7560 | **0.7630** | 0.7611 |

Compare the **behavioural**-fit axis on the same codeword: peak **L18**, rho **0.6525**, with the
grid *falling* toward late layers (L30 = 0.6002).

**The semantic fit rises monotonically into the output layers and peaks at L30.** That is not
"installed meaning becoming clearer"; it is **output adjacency** — by L30 the residual state
increasingly *is* the next-token prediction, and the target *is* that next token. The guard's
stated reason ("the semantic prompt's next token IS the target, so a representation read there
predicts it circularly") is now an observed property of the data, not just an argument.

### The trap this would have set for Phase 1, and how the design avoids it

Had the semantic-fit axis been used **at its own TRAIN-selected layer (L30)**, the Phase-1 rescue
would have restored an output-adjacent direction — which under a knockout would partially restore
the readout *almost by construction*. That is a **false positive generator**: it would have looked
like "restoring the installed-meaning component restores installation" while actually meaning
"restoring the model's own next-token prediction restores the next-token prediction."

So the rule for this sprint, decided now and before any semantic-fit arm is run:

1. **Phase 1's primary candidate stays the BEHAVIOURAL-fit axis**, at its own selected layer
   (button **L20**, basket **L18**) — the band where the knockout acts and where the fit is not
   circular.
2. **A semantic-fit arm, if run at all, must be written at the behavioural band**, never at its own
   argmax. Review M2's hard layer-mismatch refusal now has to be given an explicit, documented
   override for exactly this arm — which is the right shape: the refusal makes the exception
   visible instead of letting it happen quietly.
3. The semantic fit's rho is **never** reported (claim-table prohibition #15, already standing).

**This also re-ranks the two families' value.** S-008 framed the behavioural axis as a
*compromise* forced by a missing cache, carrying a transfer confound. That framing was too
pessimistic: the behavioural axis is the **scientifically preferable** candidate, and the semantic
axis's apparent superiority (0.763 vs 0.6525) is largely the circularity the guard names. The
transfer caveat in PR-CSI-001 stands — a null is still ambiguous between "does not transfer" and
"not causal" — but the semantic family is no longer the obviously-better comparison it looked like.

Controls behave: shuffled-label rho 0.0087 / 0.0426 / −0.0029 / 0.0034 / 0.0037, `ctrl_orth`
|cos| = 0.0 exactly, `bank_sha16 79511d9e254571e6` (basket).

---

## S-028 — the Phase-1 SMOKE DID ITS JOB: the rescue instrumentation was blind on the readout path

Job 896495 ran all six smoke arms to completion, `rc=0`, `DONE.json` on every arm — and the checker
returned **SMOKE FAIL (13)**. This is the smoke working exactly as designed.

### What the checker found

| check | result |
|---|---|
| knockout live on semantic prompts, 0 decode edits, BASE unhooked | **PASS** on all arms |
| `KO_SELF` reproduces `KO` on `y_install` | **PASS**, max\|diff\| = **0.000e+00** over 24 keys |
| `KO` reduced installation vs `BASE` | **PASS** (0.804 → 0.588) |
| **rescue fired on every row** | **FAIL — 0/24 on every rescue arm** |
| **`n_rescue_positions` recorded** | **FAIL — None** |
| **`rescue_basis_key` recorded** | **FAIL — None** |
| **written norm recorded / norm-matched** | **FAIL — nothing recorded** |

### The contradiction that identified the bug

The arms' `y_install` on 24 rows (a sanity read, **not a result**):

```
BASE 0.804 | KO 0.588 | KO_SELF 0.588 | KO_FULL 0.682 | KO_AXIS 0.590 | KO_ORTH 0.593
```

`KO_FULL` moved the endpoint from 0.588 to 0.682 — so **the rescue was plainly firing** — while the
artifact reported `fired: 0/24`. The rescue was not broken; **the instrumentation was blind.**

**Root cause.** The rescue's row fields were written only on the **generation** path. The readout
path has a *separate* field builder, `_readout_knock_fields`, which carried none of them. So a
`--query-kinds semantic_one_word` rescue run — i.e. **every arm Phase 1 will ever run** — produced
rows with `rescue_liveness: null`, `n_rescue_positions: null`, `rescue_basis_key: null`.

This is the same bug class as correction **C-6**, which hit the *knockout's* own fields on this
exact path and was fixed by routing both paths through one `record_knockout_row`. Two hand-copied
field builders; the second one falls out of date. **Same remedy applied:** a single
`_rescue_row_fields(rescue_ctx, rpos)` now serves the generation path and all three readout call
sites, and it emits the full key set (as `None`) even on non-rescue arms so every row in a run set
shares one schema.

### Why this mattered more than an instrumentation nit

Look again at the numbers: `KO_AXIS` 0.590 and `KO_ORTH` 0.593 both sit essentially **at KO**
(0.588), while `KO_FULL` recovers ~44 % of the KO-induced installation loss. Taken at face value
that is *"the rank-1 axis rescue does nothing while the whole-state rescue works"* — a substantive
Phase-1 negative.

**But it could not be believed, and that is the point.** With no `written_norm` and no `fired` flag,
"the axis rescue fired and did nothing" and "the axis rescue never fired" are the *same artifact*.
Drawing the negative from this run would have been exactly the error the liveness record exists to
prevent: *a null that looks like evidence the information was not there.*

**No Phase-1 conclusion is drawn from 896495.** Its numbers are recorded here as a 24-row
diagnostic only. Smoke relaunched as **896623** against the fixed instrumentation; the same six
arms must come back with `fired = 24/24`, a non-zero `written_norm` on `KO_AXIS`, and `KO_ORTH`
norm-matched to it per row before any Phase-1 arm is launched at scale.

**Open question flagged, not yet answered:** the minimum prefill-edit count differs between arms —
1980 on `KO`/`KO_SELF` versus 1584 on the clean-donor arms (`KO_FULL`/`KO_AXIS`/`KO_ORTH`). Both
are live and both have zero decode edits, so neither is broken, but a 25 % difference in the
knockout's own edit count across arms that are supposed to differ only in the rescue needs an
explanation before the arms are compared. Added to the checklist.

---

## S-029 — the 1980-vs-1584 prefill-edit anomaly: RESOLVED, benign, and the identity control is what licenses saying so

S-028 flagged a 25 % difference in the knockout's own edit count between `KO`/`KO_SELF` and the
clean-donor arms. Measured rather than theorised, on the **same `prompt_id`, same `seq_len` 208,
same 28 query-span positions, same 48 blocked keys**:

| arm | hooked forwards | prefill edits | edits per hooked forward |
|---|---|---|---|
| `KO` | **45** | 2160 | 48 |
| `KO_SELF` | **45** | 2160 | 48 |
| `KO_FULL` / `KO_AXIS` / `KO_ORTH` | **36** | 1728 | 48 |

**The rate is identical (48 per hooked forward).** The arms differ only in how many forwards the
hook observed, and 45 − 36 = 9 = the band width (layers 6–14), i.e. **exactly one model forward**.

**Mechanism.** The rescue block runs a donor-capture forward before the readout. Under
`--rescue-donor self` that forward runs *inside* `ctxs`, so it is hooked and contributes its 9
layer-visits; under `--rescue-donor clean` it runs *outside*, unhooked, contributing none. The
totals line up exactly: `KO` = 5 readout forwards × 9; `KO_SELF` = 1 capture × 9 + 4 × 9 = 45;
`KO_FULL` = 0 + 4 × 9 = 36.

**Does it contaminate the comparison? No — and the reason is the identity control, not an argument.**

* The **scored option set is identical across arms**: `option_mass == option_mass_core_pair` on
  every arm, so `y_install = softmax(logp_concept, logp_codeword)` is a two-way comparison over the
  same core pair everywhere. No denominator differs.
* **`KO_SELF` reproduces `KO` bit-exactly** on the endpoint — `max|diff| = 0.000e+00` over all 24
  keys, and the underlying log-probs match to the last digit (`logp_codeword −1.0291664600372314`,
  `logp_concept −1.0331529378890991` on both). `KO_SELF` *has* the donor capture and *has* an
  active patch that writes back identical values. So the capture forward and the patch mechanics
  demonstrably **do not perturb the readout**.

That is exactly what the identity control is for, and it is why it earns its GPU time: it converts
"the bookkeeping differs, is the comparison safe?" from an argument into a measurement. Any
difference between `KO_FULL`/`KO_AXIS` and `KO` is therefore attributable to **the donated
content**, not to the machinery that donates it.

**Status: closed, no action.** The checklist item from S-028 is discharged. Worth keeping in the
record because the honest first reaction to "one arm shows 25 % fewer intervention edits than
another" is alarm, and the resolution depended on a control that was already in the design rather
than on a post-hoc rationalisation.

---

## S-030 — P0.6 complete on the 3090: all four arms, one allocation. Size-match is stronger but **still CANNOT ANSWER**.

Job 896356 COMPLETED (1:42:33), all four arms back-to-back on **n-303 / `geforce_rtx_3090`**.
VERDICT **PASS**. `reports/DCS_CSI_REDERIVE_PATCH_button_p0cmp.json`.

| contrast | published (3 nodes, l40s) | **replicate (1 node, 3090)** |
|---|---|---|
| CTRL / KO / RESCUE / SIZEMATCH | 0.1111 / 0.0444 / 0.0722 / 0.0611 | 0.1167 / 0.0500 / 0.0889 / **0.0611** |
| KO de-refusal | +0.0667, k=12, p=4.88e−4 | +0.0667, k=12, p=4.88e−4 |
| recovery (RESCUE−KO) | +0.0278, k=5, p=0.0625 *(floor)* | **+0.0389, k=7, p=0.0156** *(floor)* |
| size-match recovery (SM−KO) | +0.0167, k=3, p=0.25 | +0.0111, k=2, p=0.50 |
| **full − size-match** | +0.0111, **k=2**, p=**0.50** *(floor)* | **+0.0278**, **k=5**, p=**0.0625** *(floor)* |
| recovery fraction, full | 0.417 [0.133, 0.714] | **0.583 [0.286, 0.875]** |
| recovery fraction, size-match | 0.250 [0.0, 0.50] | **0.167 [0.0, 0.417]** |

### Position identity vs position count: the ordering is now clean, the test still cannot certify it

In the replicate the dose-ordering is exactly what the hypothesis predicts and much more separated
than before: the **full** 24-position rescue recovers **58 %** of the knockout's de-refusal, the
**12-position** size-matched rescue recovers **17 %**, and the gap between them is +0.0278 on **5**
informative domains, **all same-signed, none against**.

**And it still does not pass.** The exact domain-level sign-flip test on 5 informative domains is
pinned at its attainable floor of **0.0625**, which is above 0.05. So:

> **C2 stands: the position-identity-vs-count control is CANNOT ANSWER.** The `0a8c7e6d`
> "size-match PASSES" withdrawal is **not** reversed. What has changed is that the contrast is now
> **2.5× larger and rests on 5 domains instead of 2**, and is directionally consistent across two
> independent runs (+0.0111 and +0.0278, 2/2 and 5/5 same-signed, 0 against).

This is the sprint's recurring shape and worth stating plainly: **the effects keep pointing the
predicted way, and the endpoint keeps running out of resolution before it can certify them.** Three
separate contrasts (recovery, size-match recovery, full−size-match) have now returned a p that is
*exactly* their attainable floor. That is not a statement about the effects; it is a statement about
a 90-domain, ~20-event endpoint — precisely what S-004's power analysis predicted and why Phase 1's
primary endpoint is semantic installation (67/67 informative domains) rather than refusal.

The L40S replicate (896363) is on arm 3/4 and will say whether this holds on a second architecture.

---

## S-031 — **SMOKE PASS.** Phase-1 group A is LAUNCHED. And the 24-row diagnostic now means something.

Job 896666, all six arms, `reports/DCS_CSI_P1_SMOKE_button.json` → **SMOKE PASS** (was FAIL (13)
before the S-028 instrumentation fix).

| check | result |
|---|---|
| knockout live on every arm, **0** decode edits, BASE unhooked | PASS |
| rescue **fired 24/24** on every rescue arm, **28 positions** each | PASS |
| `KO_SELF` reproduces `KO` on `y_install` | PASS, **max\|diff\| = 0.000e+00** |
| `KO_AXIS` wrote a **non-zero** delta | PASS, min 0.0321 / mean **0.0682** |
| **`KO_ORTH` norm-matched to `KO_AXIS` per row** | PASS, **max\|diff\| = 1.39e−17** |
| zero norm-match-degenerate positions | PASS |
| basis keys recorded on rows (`cand_rank1`, `ctrl_orth`) | PASS |

The norm match is exact to machine precision *per row*, and the identity control is bit-exact.
Every failure mode the smoke was written against is now excluded.

### The 24-row read, now that it is interpretable — and how much it is allowed to mean

```
BASE 0.804 | KO 0.588 | KO_SELF 0.588 | KO_FULL 0.682 | KO_AXIS 0.590 | KO_ORTH 0.593
```

Unchanged from the broken run — which is itself reassuring, since the fix was to the *recording*,
not the computation. But now the liveness is verified, so the reading is no longer ambiguous
between "did nothing" and "never ran":

* the **whole-state** rescue recovers ≈ **44 %** of the knockout's installation loss;
* the **rank-1 axis** rescue lands at **0.590** against KO's 0.588 — essentially **nothing**;
* the **norm-matched orthogonal control** lands at **0.593**, *marginally above the candidate*.

**This is a credible preliminary indication that the rank-1 installation axis is NOT the causal
variable**, while the site plainly is. It is stated here as a **prior expectation recorded before
the powered run reads out**, not as a result: 24 rows, one codeword, no domain-level statistics, no
controls beyond one orthogonal draw. PR-CSI-001's primary contrast is 670 rows / 67 TRAIN domains
with the full control family, and it will decide.

Recording it now matters for a specific reason: if the powered run comes back null, this entry is
the evidence that the null was **anticipated from the instrument, not constructed after the fact** —
and if it comes back positive, this entry is the evidence that I did not quietly discard a
contrary signal.

Note the prereg's failure clause already covers this shape: *"`KO_AXIS − KO_ORTH` not
distinguishable from 0 while `KO_FULL − KO` is clearly positive and `KO_SELF` is inert — that is an
informative negative: the site carries the effect but the installation-predictive component is not
the causal variable."*

### Launched

**Job 896679 — PR-CSI-001 group A, button, TRAIN**: `BASE, KO, KO_SELF, KO_FULL, KO_AXIS, KO_PLS,
KO_ORTH`, 670 rows / 67 domains each, all seven in **one allocation on one node**, layer L20 and
rank 5 read from the axis artifact. Group B (4 shuffled + 6 random + a `KO_AXIS_ANCHOR`) follows.

Two operational notes: the `l40s` pin was dropped from the arms launcher — readout endpoints are
hardware-stable (S-016) and every arm shares one allocation regardless, so pinning only bought queue
time. And the smoke stalled **twice more** (n-302, n-503, ~9 min at 0/291 shards each) on nodes
where I had *no* other jobs, so the NFS export contention is not self-inflicted; it succeeded
immediately on **n-303**, where the page cache was still warm from the replicate that had just
finished there. **Landing on a node that recently ran the same model is worth more than any node
preference.**

---

## S-032 — P0.6b: the L40S replicate reproduces the published numbers EXACTLY. Significance is **hardware-contingent**, which is a verdict on the endpoint.

Job 896363, arms 1–3 of 4 complete, all on **n-801 / `l40s`** in one allocation. VERDICT PASS.

| | published (3 l40s nodes) | **l40s, ONE allocation** | 3090, ONE allocation |
|---|---|---|---|
| CTRL | 0.11111 | **0.11111** | 0.11667 |
| KO | 0.04444 | **0.04444** | 0.05000 |
| RESCUE_CLEAN | 0.07222 | **0.07222** | 0.08889 |
| KO de-refusal | +0.06667, k=12, p=4.88e−4 | **+0.06667, k=12, p=4.88e−4** | +0.06667, k=12, p=4.88e−4 |
| **recovery** | +0.02778, **k=5**, p=**0.0625** | **+0.02778, k=5, p=0.0625** | **+0.03889, k=7, p=0.0156** |
| recovery fraction | 0.4167 [0.133, 0.714] | **0.4167 [0.133, 0.714]** | 0.5833 [0.286, 0.875] |

Two things fall out, and the second is the important one.

### 1. Within one architecture the endpoint is *exactly* reproducible — even across nodes

The published arms ran on **t-806 and n-801**; this replicate ran entirely on **n-801**. Every
number matches to five decimal places. So **same-architecture cross-node churn on the refusal
endpoint is zero here**, which retroactively confirms S-002's judgement that the published run's
three-node spread did not invalidate it, and sharpens S-016: the 23 % byte-identity figure is a
*cross-architecture* number, and within an architecture the endpoint is stable to the last digit.

### 2. Whether the recovery "passes" depends on which GPU you ran it on — **REFINEMENT of S-026**

S-026 reported the 3090 replicate as *"larger and now clears α = 0.05"*. With the L40S arm in hand
that framing needs qualifying, and I am qualifying it rather than leaving it to be read the
favourable way:

* on **l40s**: recovery **+0.0278**, k = 5, exact p = **0.0625** — at its floor, **does not clear 0.05**;
* on **3090**: recovery **+0.0389**, k = 7, exact p = **0.0156** — at its floor, **clears 0.05**.

The *point estimate is positive on both*, and on both **every informative domain moves in the
predicted direction and none against** (5/5 and 7/7). What flips is **k** — the number of domains
with any movement — from 5 to 7, and with it the attainable floor from 0.0625 to 0.0156.

> **So the correct statement is not "the recovery is significant." It is: the recovery is
> positive and same-signed on two architectures, and whether an exact domain-level test can
> certify it at α = 0.05 is decided by a two-domain difference that hardware alone produces.**

That is a damning verdict on the *endpoint*, not on the effect. A result whose significance is
contingent on GPU architecture is a result whose instrument has run out of resolution — exactly
what S-004 predicted (power 0.39 at D = 90) and what three floor-pinned p-values have been saying
all afternoon.

**Claim table E1 revised again** — and this supersedes the S-026 wording:

> **E1 (final for this endpoint): the clean query-span rescue recovers part of the knockout's
> de-refusal. Point estimate +0.0278 (l40s, twice, identically) to +0.0389 (3090), recovery
> fraction 0.42–0.58, every informative domain same-signed on every run, none against. NOT
> confirmatory: the exact domain-level test sits at its attainable floor in all three runs, and
> clears 0.05 on one architecture only. Underpowered by design at D = 90; D ≈ 145 needed.**

This is the last thing the refusal endpoint can usefully be asked. Further behavioural work waits
for the Phase-2 bank (D ≈ 300), and the sprint's weight is now correctly on Phase 1's semantic
endpoint, where the same intervention moves 67/67 domains.

**Traceability note:** two background commits raced and the S-032 content landed inside commit
`ab72df04`, whose message describes only S-031. No content was lost (verified: S-032, the
`p0cmpL` artifact and the revised E1 are all in `HEAD`), but a reader scanning `git log` will not
find "S-032" as a commit subject — it is in `ab72df04`. This log, not the commit subjects, is the
authoritative index. Cause: launching a second background commit while the first was still inside
the pre-commit guard. The standing rule (never two commits in flight) exists for exactly this and
I broke it; re-adopted.

---

## S-033 — Phase-1 group A is running, and its BASE arm reproduces the predecessor's installation baseline exactly

Job 896679 on n-303, `EXPECT_N=670 LAYER=20 RANK=5`, ~8.75 min per arm → ~1 h for all seven.
First arm complete and audited **while the run is still going**, so a defect would cost minutes
rather than the whole allocation.

**`csi1_button_train_BASE`, 670 rows:**

| check | value |
|---|---|
| rows / domains | **670 / 67** — matches `--expect-n` exactly |
| split census | **{train: 67}** — no validation, no test |
| globally-excluded domains present | **none** |
| cells | **C only** |
| readout / query kind | `semantic` / `semantic_one_word` only |
| rescue fields | all present, all `None` (the S-028 schema stabilisation working on a non-rescue arm) |
| **`y_install` mean** | **0.6784** |

That last row is the cross-check worth having: the predecessor's `DR-071` button **`base`**
installation is **0.6785** (S-003). My Phase-1 BASE arm, built through an independently written
population selector, a different exclusion file and the rewritten rescue-field plumbing, reproduces
it to **four decimal places**. Together with the axis reproducing the query-probe rho on both
codewords (S-013, S-021), the Phase-1 pipeline now agrees with the established record at three
independent points.

### A limitation of the endpoint, recorded before it can be discovered inconveniently

`option_mass` over the 670 rows: **mean 0.3669, min 0.0001**, against a `--min-option-mass 0.05`
gate. The gate's scope is **pooled** (the phase's frozen setting, inherited from DR-071), so it
tests the pooled mean and passes comfortably — but individual rows exist where the
(concept, codeword) pair carries **almost no probability mass at all**, i.e. the model's actual
prediction is some third word.

`y_install` is a two-way softmax over `logp_concept` and `logp_codeword`. On a row with option mass
1e−4 it is a ratio of two quantities the model barely entertains — arithmetically well-defined,
epistemically thin. This is the known "tail readout" problem the code carries a flag for
(`--allow-tail-readout`), and I am **not** changing the protocol: DR-071, A1 and every installation
number in the predecessor phase were measured this way, and switching now would make my numbers
incomparable with the record I have just reproduced.

What I will do instead, at analysis time: report the primary contrast **and** a sensitivity
re-computation restricted to rows above a per-row option-mass floor. If the Phase-1 conclusion
flips between the two, that is itself the finding and it goes in the log; if it does not, the
result is robust to the thinnest rows. Added to the checklist as **P1-f**.

---

## S-034 — P1-f implemented: the option-mass sensitivity arm, and what the floor actually removes

`scripts/dcs_csi_subspace_analyze.py --option-mass-floor F`. The selection logic
(`semantic_one_word`, cell C, the `(domain, family_slot)` key, the duplicate-key refusal, the
missing-field refusal) is kept identical to `lpm.load_installation`, and a guard
`_assert_matches_loader` **refuses to run unless the local re-implementation reproduces the frozen
loader key-for-key at floor 0** — otherwise the sensitivity arm would be measuring a different
thing from the primary and any disagreement between them would be uninterpretable. Verified:
**PASS**.

**What the floor removes, measured on the BASE arm (670 rows):**

| option-mass floor | rows kept | dropped | mean `y_install` |
|---|---|---|---|
| 0.00 (frozen protocol) | 670 | 0 | **0.6784** |
| 0.01 | 654 | 16 | 0.6914 |
| 0.05 | 586 | 84 | 0.7420 |
| 0.10 | 522 | 148 | 0.7943 |

**The floor is not neutral, and that has to be said before the sensitivity result is read.**
`y_install` rises monotonically as thin rows are dropped — from 0.678 to 0.794. This is not an
artifact; it is the sensible reading: a row where the model entertains *neither* the concept nor
the codeword is typically a row where **the mapping did not install at all** (the model is
predicting some third word), and those rows carry low `y_install`. So raising the floor
preferentially deletes low-installation rows and inflates the level.

**Consequence for how P1-f may be used.** The sensitivity arm is *not* a check on whether the
installation **level** is robust — it demonstrably is not, and it should not be. It is a check on
whether the **contrast between arms** is robust, which is the only quantity PR-CSI-001 claims. At
analysis time the primary contrast is reported at floor 0 (the frozen protocol, comparable with
DR-071/A1) and re-computed at a floor; **if the sign or the conclusion of the contrast flips, that
is the finding and it goes in the log.** A level shift between the two is expected and means
nothing.

---

## S-035 — I verified the two load-bearing literature claims MYSELF. Both hold, and the novelty boundary is now precise.

The subagent's literature review (S-001 workstream) made two claims that govern everything we may
write. Both are too consequential to take second-hand, so I fetched the paper directly.

### Claim 1 — our attack is already published. **CONFIRMED.**

**Yona, Sarid, Karasik, Gandelsman, "In-Context Representation Hijacking", arXiv:2512.03771.**
Verified from the paper itself: it introduces **"Doublespeak"** — harmful keywords replaced with
benign tokens across in-context examples — with the benign token's representation *"converging
toward that of the harmful one, effectively embedding the harmful semantics under a euphemism"*,
and reports **74 % ASR on Llama-3.3-70B-Instruct**. Their worked example is `carrot → bomb`, giving
prompts like *"How to build a carrot?"*

⇒ **We cannot claim the phenomenon, the name, the `codeword → concept` construction, or the
layer-by-layer representational convergence.** Claim-table prohibition #10 stands and is now
verified rather than inherited.

### Claim 2 — their evidence is read-only. **CONFIRMED, with a precision the summary lacked.**

From the full text: they apply the **logit lens** (*"a fast, lightweight way to peek into the
model's computation"*) and **Patchscopes** (*"patching h^{i,l} into a different sequence S′"*).
There is **no attention knockout, no ablation, and no steering.**

The precision that matters: **Patchscopes *is* a forward-pass edit**, so "they performed no
intervention" would be wrong. The correct distinction is that Patchscopes patches a state into a
*different* sequence **in order to read out what that state encodes** — it is interpretation
machinery, not an ablation that removes a computation and measures what breaks. I will state it
that way and not the sloppier way.

And the finding that most directly motivates this sprint:

> *"While it successfully detected and explained our attack on Llama-70B-instruct, it **failed to
> do so on the smaller Llama-3.1-8B-instruct model**."* (they fall back to Patchscopes there;
> Appendix H, Table 4)

**Their primary interpretability tool fails on our exact model.** Our causal battery — the A1
demo→query attention knockout, the whole-state rescue, and the subspace rescue with norm-matched
controls — is being run precisely where their read-only approach did not work.

### The novelty boundary, stated conservatively

**NOT ours, and must never be claimed:**
* the Doublespeak attack, its name, and the representation-convergence observation (2512.03771);
* attention knockout as a technique (Geva et al. 2023);
* **layer-banded demonstration→query attention blocking in ICL** (Wang et al., *Label Words are
  Anchors*, EMNLP 2023) — this is why prohibition #9, *"first to causally intervene on demo→query
  attention in ICL"*, is FALSE and stays forbidden;
* corrupt-then-restore / activation patching (Meng et al., ROME);
* the ablate-and-add template for low-dimensional refusal mediation (Arditi et al. 2024);
* low-rank causal subspace intervention (DAS / Boundless DAS).

**Plausibly ours, and still to be earned by results rather than asserted:**
* a **causal** account of *this* attack's mechanism, on a model where the published read-only
  account failed;
* the concept-free installation readout used as an **intervention-scorable dependent variable**
  rather than a descriptive probe;
* the demo→query edge established as causal **for semantic installation specifically**, separated
  from generic ICL retrieval;
* the attempt to link that representation to **behaviour** on a powered endpoint.

Every one of these is contingent on Phase 1 and Phase 5 producing results. **No novelty sentence
is to be written before those read out**, and the literature report is to be re-checked against
anything published since — arXiv:2605.00123 and arXiv:2605.18830 were flagged by the review as
potentially narrowing items 2 and 3 and have **not** been read yet. Recorded as an open dependency.

---

## S-036 — the two flagged papers are REAL and both NARROW our novelty. The honest position is now much more modest.

S-035 recorded arXiv:2605.00123 and arXiv:2605.18830 as flagged-but-unread, with the warning that
either could narrow items 2 and 3 of the novelty list. I read them. **Both exist, and both do.**

### arXiv:2605.18830 — *In-Context Learning Operates as Concept Subspace Learning*
Tang, Jiang, Karray & Hu (May 2026).

> *"mechanistic analyses often identify compact activation directions that steer prompted behavior"*
> … **"patching the complementary subspace restores 0 %"** … *"Concept swaps redirect predictions
> toward injected relations."*

This is **causal subspace patching of in-context concept representations** — structurally the same
method as PR-CSI-001. They identify low-dimensional task-aligned subspaces that **mediate** ICL
behaviour and validate them by patching, including the complementary-subspace control. No
jailbreaks; the domain is structured task families.

⇒ **Our Phase-1 *method* is not novel.** "Restore only the concept subspace and the behaviour comes
back / patch its complement and nothing comes back" is published for ICL.

An interesting substantive contrast worth keeping in view rather than burying: their finding is
that the task subspace **is** causal (complement restores 0 %). Our own 24-row smoke (S-031)
pointed the other way — rank-1 axis ≈ KO, whole-state rescue recovers ~44 %. If the powered run
confirms that, we are reporting a **dissociation from** a published positive, which is a
substantive result in its own right and a reason to be *more* careful, not less, about controls.

### arXiv:2605.00123 — *Minimal, Local, Causal Explanations for Jailbreak Success in LLMs*
Kumar & Ahuja, **COLM 2026**.

> LOCA identifies *"a minimal set of interpretable, intermediate representation changes that
> causally induce model refusal on an otherwise successful jailbreak request."*

This is **causal representation→refusal analysis for jailbreaks** — structurally the same question
as our Phase 5.

⇒ **Our representation→behaviour framing is not novel either.**

### Revised novelty position — narrow, and contingent

Everything in S-035's "plausibly ours" list except one item is now either published or heavily
anticipated. What survives, stated at the size it actually is:

* the **demonstration→query attention edge** established as the causal locus **for semantic
  installation specifically** in a Doublespeak attack — the edge (Wang et al.) and the attack
  (Yona et al.) are each published, but their **causal junction** is not something I have found;
* the **concept-free installation readout** used as an intervention-scorable DV;
* whatever Phase 1 actually finds about a low-rank installation axis — **including, and perhaps
  especially, a negative that dissociates from 2605.18830's positive**;
* the empirical fact that this is done on **Llama-3.1-8B-Instruct, where the published descriptive
  account's primary tool failed** (S-035).

**What this changes operationally.** Nothing about the experiments — they were worth running before
and are worth running now. What changes is the framing: this sprint is no longer plausibly
"a new method"; it is **a causal account of a specific published attack, on a specific model, with
a specific readout**, whose main value may turn out to be a *dissociation* rather than a
confirmation. Claim-table prohibition #10c is amended: the two papers are now **read**, and the
novelty list is replaced by the four narrow items above.

**Process note.** This is the second time today that checking a subagent's flagged-but-unverified
item changed a conclusion (the first was S-019). The review flagged these two correctly and I
recorded them as an open dependency rather than proceeding — that is the only reason the
overclaim did not reach a draft. **Flagged-and-unread is a blocker, not a footnote.**

---

## S-037 — group B landed on V100 twice: caught a hardware confound **and** an impossible walltime before either cost anything

PR-CSI-001 group B (the control distribution: `KO_AXIS_ANCHOR` + 4 shuffled + 6 random) was
submitted unpinned after its `--nodelist=n-303` pin left it PENDING 25 min on `(Resources)`. It
then landed on **`rack-bgw-dgx1`**, and after a cancel-and-resubmit on **`rack-gww-dgx1`** — both
**`gpu:v100:8`**. Cancelled both. Two independent reasons, and the first is the one that matters:

1. **V100 has no native bfloat16.** `--dtype bfloat16` is emulated there. Group A's arms —
   including the **candidate** `KO_AXIS` — are running on **n-303 / `geforce_rtx_3090`**. The Holm
   specificity analysis compares the candidate against **each** group-B control, so this would have
   put candidate and controls on different numerical paths in the sprint's *primary specificity
   test*. That is a hardware confound sitting directly under the result PR-CSI-001 exists to
   produce.
2. **It could not have finished.** Throughput was ~13 rows/min against n-303's 50–90, projecting
   **~9.4 h for 11 arms** versus an **8 h** walltime. The job would have died incomplete — and,
   per the standing lesson, `sacct` would have shown a clean cancellation rather than "your
   control distribution is missing four arms".

Both aborted anchor-arm directories are **quarantined, not deleted** (`outputs/boombness/quarantine/`),
each with a `QUARANTINE.json` naming the reason — an invalid run is evidence, and leaving two
sibling directories under one tag would correctly make `strict_run_dir` refuse as ambiguous.

**Fix, and the general lesson.** Chasing bad nodes one at a time with `--exclude` is the wrong
instrument — the cluster has `l40s`, `geforce_rtx_3090`, `v100` and `titan`, and an exclude list
grows forever while the scheduler keeps finding new ways to be unhelpful. The right instrument is
to **pin the GPU model positively**: group B is resubmitted as `--gpus=geforce_rtx_3090:1`, the
**same architecture group A is running on**. The `KO_AXIS_ANCHOR` arm then measures
*allocation-to-allocation* drift with architecture held fixed, which is what it was designed to
isolate.

> **Rule adopted:** when two run groups will be compared statistically, pin the **GPU model**
> positively on both. Do not rely on exclusions, and do not rely on the scheduler happening to
> choose alike.

This also retroactively explains why the S-016 cross-architecture churn measurement was worth the
GPU time: without a measured sense of how much hardware moves these endpoints, "it landed on a
V100" would have read as a scheduling detail rather than as a threat to the primary analysis.

---

## S-038 — PR-CSI-001's two VOID gates both PASS at full TRAIN scale, and the manipulation check reproduces DR-071

Group A's first three arms are complete (670 rows / 67 domains each). The preregistration's gates
are checked **before** any contrast is computed, exactly as written, and both pass.

```
domain-mean y_install:   BASE 0.67843   KO 0.47064   KO_SELF 0.47064
```

### Gate 1 — manipulation check: **PASS**

| | this sprint (Phase-1 group A) | predecessor `DR-071` |
|---|---|---|
| `base` installation | **0.67843** | 0.6785 |
| `ko` installation | **0.47064** | 0.4703 |
| **drop** | **−0.20779** | −0.2082 |
| **domains moving negative** | **67 / 67** | 67 / 67 |

The knockout removes **31 %** of installation, on **every single domain**, and the whole thing
lands within 0.0005 of a number measured by different code on a different day. The A1 effect is
reproduced, not assumed.

### Gate 2 — identity control: **PASS, bit-exactly**

`KO_SELF − KO`: **max |diff| = 0.000e+00 across all 670 keys.** **Zero** keys differ, at all. The
domain-mean difference is exactly `+0.000e+00`.

This is the gate that licenses every later comparison. Writing a run's own activations back into it
reproduces it *to the last bit* on 670 rows — so the donor capture, the `ExitStack` ordering, the
token-identity guard and the patch write-back are all provably inert when they should be. Any
difference `KO_FULL`, `KO_AXIS` or `KO_ORTH` shows against `KO` is therefore attributable to **the
donated content**, and to nothing about the machinery that donates it. (S-029 argued this from the
24-row smoke; it is now established at full scale.)

### What remains

`KO_FULL` is running, then `KO_AXIS`, `KO_PLS`, `KO_ORTH`. Gate 3 — **instrument capability**
(`KO_FULL − KO > 0` with a CI excluding zero) — is the last one before the primary contrast may be
read. If it fails, PR-CSI-001 returns **CANNOT ANSWER for want of a capable instrument**, which is
explicitly *not* a negative.

The smoke's 24-row read (S-031) put `KO_FULL` at 0.682 against `KO` 0.588 — a ~44 % recovery — so
gate 3 is expected to pass, but it is not assumed and the prereg's wording stands either way.

**Group B** (control distribution) is now on **n-307 / `geforce_rtx_3090`** — the architecture pin
from S-037 working, and matching group A's n-303. Two further aborted anchor directories were
quarantined along the way (n-302 stalled at 0/291 shards for a third time; both V100 attempts).

---

## S-039 — the weight-load stall is a NODE property, not contention. Four stalls, and the rule that actually works.

Group B took **five** submissions to start. The full record, because the pattern only became legible
once it had happened enough times:

| job | node | GPU | outcome |
|---|---|---|---|
| 896693 | (pinned n-303) | 3090 | PENDING 25 min on `(Resources)` — n-303 is 8/8 allocated |
| 896728 | rack-bgw-dgx1 | **v100** | cancelled — no native bf16, and ~9.4 h projected vs 8 h wall |
| 896738 | rack-gww-dgx1 | **v100** | cancelled — same |
| 896743 | **n-302** | 3090 | **stalled 0/291 shards, ~6 min** |
| 896764 | **n-307** | 3090 | **stalled 0/291 shards, ~8.5 min** |
| **896771** | **n-350** | 3090 | **loading normally**, 17/291 at 4.06 s/it |

**The stall is not contention, and my earlier diagnosis in S-015/S-024 was incomplete.** S-015
blamed per-node job stacking; S-024 corrected that to "concurrent reads of the shared NFS export".
Both are now insufficient: **896764 stalled on n-307 while nothing else of mine was loading**, and
896771 loads fine on n-350 *at the same moment* group A is running on n-303. Sorted by observed
behaviour:

* **n-303** — instant (page cache warm from a job that just finished there);
* **n-350** — cold but **advancing**, ~4–5 s/shard, ~20 min total;
* **n-302, n-307, n-503** — **0/291, indefinitely**.

That is three distinct regimes, and the third looks like a genuinely bad or saturated mount on
those specific nodes rather than anything about my job mix.

> **Operational rule, replacing S-015 and S-024's versions:** the weight-loading bar in `.err`
> after **two readings a few minutes apart** is the only reliable liveness test, and a node that
> shows **0/291 twice is bad** — cancel immediately rather than waiting out the walltime. Keep a
> known-good list (**n-303 warm, n-350 cold-but-working**) and pin to it. Exclusion lists chase the
> problem; a positive pin ends it.

Cost of learning this: ~35 minutes of wall-clock and four aborted allocations, all quarantined with
reasons rather than deleted. Cost of *not* learning it would have been a group-B job dying at the
8-hour walltime with four control arms missing — and `sacct` reporting a clean `CANCELLED`.

**Note on the architecture pin.** S-037's rule (pin the GPU model positively when two groups will
be compared) survives intact: n-350 is `geforce_rtx_3090`, matching group A's n-303. So candidate
and controls remain architecture-matched, and the `KO_AXIS_ANCHOR` arm still measures only
allocation-to-allocation drift.

---

## S-040 — **GATE 3 PASSES.** The instrument is capable, and the semantic endpoint delivers the resolution the refusal endpoint never had.

`KO_FULL` complete. All three PR-CSI-001 gates, at full TRAIN scale (670 rows / **67 domains**),
domain-clustered bootstrap (20 000 draws) and sign-flip randomisation:

| gate | contrast | estimate | CI95 | pos / neg / tied | k | p |
|---|---|---|---|---|---|---|
| 1 manipulation | `KO − BASE` | **−0.20779** | [−0.22704, −0.18941] | **0 / 67 / 0** | 67 | < 1e−5 |
| 2 identity | `KO_SELF − KO` | **+0.00000** | [0, 0] | 0 / 0 / **67** | 0 | — |
| **3 capability** | **`KO_FULL − KO`** | **+0.07135** | **[+0.06127, +0.08204]** | **66 / 1 / 0** | **67** | **< 1e−5** |
| — residual | `BASE − KO_FULL` | +0.13644 | [+0.12325, +0.14984] | 67 / 0 / 0 | 67 | < 1e−5 |

**Recovery fraction of the knockout's installation loss: 0.3434, CI95 [0.3088, 0.3775].**

### Gate 3 passes decisively — the subspace question is answerable, not CANNOT ANSWER

Restoring the clean query-span state under the live knockout recovers **34 %** of the installation
the knockout removed, on **66 of 67 domains**, with a CI nowhere near zero. So there *is* a capable
instrument at this site and layer, and PR-CSI-001's CANNOT-ANSWER branch is closed. Whatever the
subspace arms show, they will be interpretable.

### The endpoint change was the single best decision in this sprint

Compare the same causal question on the two endpoints:

| | refusal (behavioural) | **semantic installation** |
|---|---|---|
| informative domains for the recovery contrast | **5–7** | **67** |
| recovery fraction CI | [0.13, 0.71] *(l40s)* / [0.29, 0.88] *(3090)* | **[0.309, 0.378]** |
| exact test | **pinned at its attainable floor in all three runs** | **not floor-limited** — p is limited by my Monte-Carlo sample (1/200001), while the exact floor is 1.36e−20 |
| significance stable across hardware? | **no** — flips with GPU architecture (S-032) | not yet tested, but the margin is ~10× the hardware churn |

The recovery-fraction CI is **an order of magnitude tighter** (width 0.07 vs 0.58), and for the
first time in this sprint a p-value is **not** sitting on its own floor. Every floor-pinned result
recorded today (S-002, S-026, S-030, S-032) was a symptom of a ~20-event endpoint; this is what the
same intervention looks like measured on an instrument with headroom.

Note the one dissenting domain in Gate 3 (66 positive, **1 negative**) — recorded rather than
rounded away. With 67 domains and a CI of [+0.061, +0.082] it does not threaten the conclusion, but
it is the honest count.

### What is now unblocked

`KO_AXIS` is running with the correct basis (`cand_rank1`, sha16 `d543d8f0a76e78cc`, fit on 67 TRAIN
domains at rel-6/L20 — printed by the run and recorded on every row). Then `KO_PLS` and `KO_ORTH`.
The preregistered primary contrast `KO_AXIS − KO_ORTH` becomes readable once group A finishes, and
group B's control distribution follows from n-350.

**Standing expectation, from S-031 and unchanged:** the 24-row smoke put `KO_AXIS` at KO's level
while `KO_FULL` recovered. If that holds at 67 domains, PR-CSI-001's *failure* clause applies — the
site carries the effect, the installation-predictive rank-1 component does not — and given S-036,
that would be a **dissociation from a published positive** (arXiv:2605.18830 found the ICL concept
subspace *is* causal, with its complement restoring 0 %). That would make the controls matter more,
not less.

---

## S-041 — **The rank-1 axis spans only 3.6 % of the perturbation.** Recorded BEFORE the primary reads out, because it decides how a null may be interpreted.

The dose fields the S-028 fix put on every row are not bookkeeping — they carry the quantity that
governs the whole interpretation. Measured on the smoke arms (24 rows, both arms identical prompts):

| quantity | `KO_AXIS` (`cand_rank1`) | `KO_ORTH` (norm-matched control) |
|---|---|---|
| ‖delta‖ = ‖h_clean − h_ko‖ per position | **1.4808** | 1.4808 (same rows) |
| ‖written‖ | 0.0682 | 0.0682 *(matched by construction)* |
| **captured energy fraction** | **0.0364** | 0.0135 |

**The rank-1 installation axis spans 3.64 % of the norm of the state change the knockout causes.**

### What that number means, against the right baseline

A *random* rank-r subspace of a 4096-dim space captures √(r/d) of an arbitrary vector's norm:

| r | 1 | 3 | 5 | 10 | 50 |
|---|---|---|---|---|---|
| √(r/4096) | **1.56 %** | 2.71 % | 3.49 % | 4.94 % | 11.05 % |

So the axis at 3.64 % is **2.3× the geometric baseline** for a random direction, and **2.7×** the
measured orthogonal control (1.35 %, itself close to the 1.56 % prediction). **The axis is
genuinely aligned with the knockout's perturbation far more than chance** — which is a real,
independent corroboration of the observational result, obtained from the intervention's own dose
record rather than from a probe.

### Why this had to be written down now

If `KO_AXIS` comes back at KO's level, the tempting sentence is *"the installation-predictive
component is not the causal variable."* **That sentence would not be safe**, because restoring
**3.6 % of a perturbation's norm** and observing no recovery is close to arithmetically
unsurprising. That is exactly the trap plan §15 names — *"never conclude 'this state carries
nothing' from a transplant that has never demonstrated transfer capability"* — in its subtlest
form: here the transplant *is* capable (Gate 3, +0.071 at 100 % of the delta), but the **candidate
arm is administering a ~27× smaller dose than the positive control**.

**So the arms are not interchangeable, and the comparisons must be read at matched dose:**

* `KO_FULL` restores **100 %** of the delta → +0.0714 recovery. Comparing `KO_AXIS` to *that* is
  1 dimension against 4096 and is **not** an apples-to-apples test of the axis.
* **The preregistered primary is `KO_AXIS − KO_ORTH`** — rank-matched *and* norm-matched to 1.4e−17
  per row (S-031). That isolates exactly one thing: **at this dose, does the installation direction
  do more than an arbitrary direction?** The prereg got this right, and it is the contrast that
  will be reported as primary.
* `KO_PLS` (rank 5) supplies a **dose rung**: more dimensions, more captured energy (~3.5 % random
  baseline, so an informative subspace should exceed it).

**Licensed readings, fixed in advance:**

* `KO_AXIS > KO_ORTH` ⇒ the installation direction carries causal weight **at a dose of 3.6 %**,
  and the effect size should be reported per unit dose, not compared naively to `KO_FULL`.
* `KO_AXIS ≈ KO_ORTH` ⇒ **at this dose, direction identity does not matter.** That is *not* the
  same as "the axis is not causal", and it **must not** be written that way. It licenses one
  further question — whether a larger-rank or amplified intervention along the same direction does
  anything — and nothing stronger.
* Either way, the honest headline quantity is **recovery per unit of restored norm**, not raw
  recovery.

**Checklist addition P1-g:** report captured-energy fraction alongside every subspace arm, and
express recoveries per unit dose. Already recorded on every row by the S-028 builder, so this costs
nothing but the reporting discipline.

---

## S-042 — **CORRECTION.** A prefix-collision in my own run-directory matching made the identity gate VACUOUS. Gates re-derived; conclusions survive, one claim withdrawn.

### The bug

Run directories are named `<tag>_<YYYYmmdd>_<HHMMSS>_<pid>`. My matching globbed `<tag>_*` — which
also matches **every sibling arm whose tag extends this one**:

```
glob("csi1_button_train_KO_*")  ->  KO, KO_AXIS, KO_AXIS_ANCHOR, KO_FULL, KO_PLS, KO_SELF
```

Ad-hoc checks that took `sorted(...)[-1]` therefore resolved arm **`KO`** to the **`KO_SELF`**
directory. Consequences:

* **The identity gate compared `KO_SELF` against `KO_SELF`** — a comparison that *cannot fail*. The
  "max |diff| = 0.000e+00 across all 670 keys" in S-038/S-040 was that vacuity, not a measurement.
* The same mis-resolution affected **S-029**'s hooked-forward analysis (its "KO" was `KO_SELF`) and
  **S-031**'s smoke check (`newest()` used the same unanchored glob).

`strict_run_dir` — the *real* analyser's resolver — was never fooled: it demands **exactly one**
complete directory and would have **refused**. The defect lived only in the quick checks I wrote
alongside it. That is a small mercy and not an excuse: the quick checks are what I reported from.

**Fixed** in both `dcs_csi_rederive_patch.strict_run_dir` and
`dcs_csi_p1_smoke_check.newest`: the tag must now be followed by exactly
`_\d{8}_\d{6}_\d+` and nothing else. Verified: `csi1_button_train_KO` now resolves to the KO
directory.

### Gates re-derived with anchored resolution (670 rows / 67 domains)

| gate | contrast | **corrected** | as reported in S-038/S-040 | pos/neg/tied | p |
|---|---|---|---|---|---|
| 1 manipulation | `KO − BASE` | **−0.20704** [−0.2264, −0.1886] | −0.20779 | **0/67/0** | < 1e−5 |
| **2 identity** | `KO_SELF − KO` | **−0.00076** [−0.00165, **+0.00013**] | ~~0.00000 exactly~~ | 28/39/0 | **0.107** |
| 3 capability | `KO_FULL − KO` | **+0.07060** [+0.0606, +0.0812] | +0.07135 | **66/1/0** | < 1e−5 |
| — | recovery fraction, FULL | **0.3410** [0.3064, 0.3752] | 0.3434 | — | — |

**WITHDRAWN:** *"`KO_SELF − KO` = 0.000e+00 on all 670 keys; zero keys differ at all"* (S-038,
repeated in S-040). It was an artifact of comparing an arm with itself.

**Gate 2 still PASSES, on the correct comparison.** The true identity difference is **−0.00076**,
its CI **includes zero**, p = 0.107, and |diff| is **6.6× below** the preregistered tolerance
(`self_inert_tol = 0.005`). But the honest description changes from *"bit-exact"* to
**"inert within measurement error"**: 28 domains move up, 39 move down, no systematic direction.
The residue is consistent with floating-point nondeterminism introduced by the extra donor-capture
forward pass, and it is ~1 % of the `KO_FULL` effect it must not contaminate.

**Gates 1 and 3 are unaffected in substance** — the point estimates move in the fourth decimal and
every domain count is identical. So S-040's conclusion stands: the instrument is capable, the
CANNOT-ANSWER branch is closed, and the semantic endpoint has the resolution the refusal endpoint
lacked.

### The secondary contrast, now correctly resolved

| contrast | estimate | CI95 | pos/neg/tied | p | recovery fraction |
|---|---|---|---|---|---|
| `KO_FULL − KO` | **+0.07060** | [+0.0606, +0.0812] | 66/1/0 | < 1e−5 | **0.341** |
| **`KO_AXIS − KO`** | **+0.00040** | **[−0.00025, +0.00106]** | 40/27/0 | **0.249** | **0.0019** |

The rank-1 installation axis recovers **0.2 %** of the knockout's installation loss where the
whole-state rescue recovers **34 %** — and its CI comfortably includes zero. This is the picture the
24-row smoke indicated (S-031), now at full scale with the correct arms.

**It is still not the primary contrast.** `KO_ORTH` is the preregistered comparator and is running.
And S-041's constraint governs the reading: the axis administers **3.6 %** of the perturbation's
norm, so `KO_AXIS ≈ KO` on its own is *not* licence to write "the installation component is not
causal". The question the design can answer is `KO_AXIS` vs `KO_ORTH` **at matched dose**.

### How this was caught, and what it says

Not by a test — by reading a diagnostic table and noticing that the `KO` row and the `KO_SELF` row
named **the same directory**. The lesson is the sprint's own recurring one, now self-inflicted:
**a control that cannot fail is worse than no control**, and the way it presents is a number that
looks *too good* — "0.000e+00 on all 670 keys" should have prompted suspicion at the time rather
than satisfaction. Exact zeros from a floating-point pipeline are a red flag, not a triumph.

---

## S-043 — two further corrections cascading from S-042, and a threshold moved onto the preregistered quantity

### (a) S-029's forward-count explanation was **inverted**. Corrected.

With anchored resolution, the smoke arms' hooked prefill-forward counts are:

| arm | prefill forwards | edits per forward |
|---|---|---|
| `KO` | **36** | 55.0 |
| **`KO_SELF`** | **45** | 55.0 |
| `KO_FULL` / `KO_AXIS` / `KO_ORTH` | **36** | 55.0 |

S-029 reported `KO = 45, KO_SELF = 45, clean-donor arms = 36` and built an elaborate
page-cache/readout-caching story to explain why the *clean* arms were the odd ones out. **That was
the mis-resolved `KO` again**, and the truth is far simpler:

> `KO_SELF` is the **only** arm at 45. The `--rescue-donor self` capture runs **inside** `ctxs`, so
> it is hooked and contributes exactly **+9** layer-visits (one forward × the 9-layer band 6–14).
> Clean-donor captures run **outside** `ctxs` and contribute nothing. `KO` has no capture at all.
> 36 + 9 = 45. Everything else is 36.

**WITHDRAWN:** S-029's cache-warming mechanism. **Retained and now better supported:** its
conclusion — the knockout applies **identically** across arms at **55.0 edits per hooked forward on
every single arm**, so the intervention dose is not confounded with the rescue.

### (b) The smoke's identity check was too strict *because* it was built on the artifact

With correct arms, `KO_SELF` vs `KO` on 24 smoke rows gives **per-key max |diff| = 2.635e−02**, and
the smoke's threshold of `max|diff| < 1e-6` **failed**.

That threshold was **my invention, not the preregistration's**, and it "passed" before only because
the vacuous self-comparison returned exact zeros. PR-CSI-001 specifies
`self_inert_tol = 0.005` on the **mean** difference — which is the quantity that enters every
contrast. Per-key scatter from float nondeterminism in the extra donor-capture forward does not.

So the gate is **moved onto the preregistered quantity**, and the per-key max is retained as a
**diagnostic**:

```
PASS  KO_SELF reproduces KO in the MEAN (prereg self_inert_tol=0.005)
      mean diff = -4.141e-03   (per-key max = 2.635e-02 over 24 keys, diagnostic only)
```

**I want to be explicit that this is not threshold-shopping.** Loosening a gate because it failed
would be exactly the wrong move. What happened is: an unpreregistered, artifact-derived criterion
was replaced by the criterion the preregistration actually names, which is *stricter in the sense
that matters* — it binds the quantity the science depends on. And at full TRAIN scale that quantity
is **−0.00076** (S-042), i.e. **6.6× inside** the tolerance, on 670 rows rather than 24.

### Running tally of what S-042's single glob defect touched

| entry | claim | status |
|---|---|---|
| S-029 | "KO and KO_SELF both make 45 hooked forwards; clean arms 36" | **WITHDRAWN**, replaced above |
| S-029 | "the knockout applies identically per forward across arms" | **stands**, now 55.0/forward on all five arms |
| S-031 | "SMOKE PASS" incl. bit-exact identity | **re-run**: still **SMOKE PASS**, on the corrected criterion |
| S-038 | "`KO_SELF − KO` = 0.000e+00 on all 670 keys" | **WITHDRAWN** (S-042) |
| S-038/S-040 | Gates 1 and 3, capability, recovery fraction | **stand**, point estimates move in the 4th decimal |
| S-041 | the 3.6 % captured-energy dose constraint | **stands** — computed from `KO_AXIS`/`KO_ORTH`, neither of which the glob could mis-resolve |

**One defect, six entries touched, two claims withdrawn, and the scientific conclusions intact.**
That is the append-only log doing its job: every number above was recoverable because the raw arms
were still on disk and each entry named the artifact it came from.

---

## S-044 — adversarial review round 2: **1 BLOCKER, 4 MAJOR — all real, all demonstrated, all fixed before the primary was read**

`reports/DCS_CSI_CODE_REVIEW_PHASE1_R2.md`. Every finding was verified end-to-end by the reviewer
rather than argued, and every one is a defect I would have shipped.

### BLOCKER R2-B1 — the P1-f option-mass floor was **post-treatment selection**

`option_mass` is an **outcome of the intervention**. Filtering each arm independently on it deletes
an arm-dependent, outcome-correlated slice — a **collider** — and because the analyser then
intersected only *domains* and never *slots*, the paired domain means were averages over
**different slot sets**.

Reproduced on the real arms (BASE vs KO, 67 TRAIN domains):

| floor | OLD: rows kept BASE / KO | OLD `KO − BASE` | **FIXED** keys | **FIXED `KO − BASE`** |
|---|---|---|---|---|
| 0.00 | 670 / 670 | −0.2070 | 670 | **−0.2070** |
| 0.05 | 586 / **658** | −0.2448 | 586 | **−0.2144** |
| 0.20 | 435 / **582** | **−0.3297** | 435 | **−0.2299** |

At floor 0.20 the buggy filter inflates the manipulation effect by **59 %** (−0.207 → −0.330),
purely by keeping 147 more rows in KO than in BASE. **S-034's P1-f design was wrong**, and had I
run the sensitivity as written it would have produced a spurious "the effect is even stronger on
clean rows" result.

**Fixed:** the retained key set is chosen **once**, from a single reference arm (default `BASE`, the
un-intervened condition), and applied **identically to every arm**. The corrected sensitivity says
the manipulation is **robust** to dropping thin rows (−0.207 → −0.214 → −0.230), which is a modest,
believable dependence rather than a manufactured one. Stated openly: conditioning on BASE's option
mass is still conditioning on a *measured* quantity and is not strictly pre-treatment — but it
cannot differ between arms, which was the defect that mattered.

### MAJOR R2-M1 — the identity arm was exempt from its own liveness VOID

`KO_SELF` was the one rescued arm skipped by the `rescue_fired != expect_n` check — and it is
precisely the arm whose null **is** the identity gate. A self-patch that never fires is
byte-identical to KO, so the gate reads exactly 0.0 and passes for the worst possible reason. The
reviewer demonstrated it: `rescue_fired: 0 of 100`, `VOID: []`, all gates true, `PRIMARY PASSES`.
**This is the same shape as S-042's vacuous control, reached by a different route.** Fixed: no arm
declaring a rescue is exempt.

### MAJOR R2-M2 — the analyser never verified **arm identity**

It trusted the arm *label*. The reviewer built a run set where candidate and comparator both
carried `cand_rank1` and no basis at all, and it emitted a full contrast table with `VOID: []` — a
publishable negative from **an arm contrasted with itself**. Fixed: the analyser now VOIDs unless
candidate and comparator declare *different* basis keys, both declare one, the comparator is
norm-matched, and the arms agree on knockout scope.

### MAJOR R2-M3 — `--rescue-basis-key` without `--rescue-basis` ran the whole-state patch

An unset shell variable in an sbatch line (a documented failure mode here) would run the
**positive control** while labelling its rows with the subspace key — reporting `KO_FULL`'s 34 %
recovery as the candidate's. The ORTH arm was caught by the existing norm-match guard; **the AXIS
arm was not**. Fixed: refused outright.

### MAJOR R2-M4 — my `--slurm-job` made the hardware VOID **tautological**

I added `--slurm-job` in S-026 to fix a false VOID. It passes one job id for every arm, so `gpus`
is constant *by construction* and "SAME ARCHITECTURE" could never fail — and nothing tied the
declared job to the run directories. **Fixed with a real check rather than a softer verdict:** each
arm's `DONE.json` end timestamp must fall inside the declared job's `sacct` [start, end] window; an
arm outside it is a PROBLEM. Re-verified on the p0cmp replicate: still PASS, now non-vacuously.

### Refuted by test (recorded, because negative review findings are findings)

The reviewer's own tests **cleared**: both stale-cell suspicions (`_rescue_ctx` / `_rpos_row` are
reset every row), `holm()` (2000 randomised cases against a reference implementation, **0
mismatches**), the `.replace("patch_", …, 1)` anchoring, `allow_query_kinds` default equivalence
across 22 call sites, and readout-forward token alignment (0/120 tokenizer prefix breaks).

### The pattern worth naming

**Three separate defects this sprint produced a control that could not fail** — S-042's glob
collision, R2-M1's exemption, R2-M2's missing identity check. Each arrived by a different route and
each would have presented as a *clean pass*. The generalisation for the rest of this sprint:

> **Every control must be tested against a deliberately broken input**, not merely observed to
> pass. A control that has only ever been seen to succeed has not been shown to be a control.

---

## S-045 — the `KO_AXIS_ANCHOR` reads **zero** allocation drift, and this time the zero is verified not to be an artifact

The anchor arm exists to answer one question before group A's candidate is compared against group
B's controls: **does running in a different allocation move the endpoint?**

| | run | node | mean `y_install` |
|---|---|---|---|
| group A `KO_AXIS` | job 896679 | n-303, `geforce_rtx_3090` | **0.471794** |
| group B `KO_AXIS_ANCHOR` | job 896771 | n-350, `geforce_rtx_3090` | **0.471794** |

`ANCHOR − AXIS` = **+0.000000**, CI [0, 0], **0 / 0 / 67** pos/neg/tied.
Per key: **670 / 670 identical**, max |diff| = **0.000e+00**.

Against the effect it must not contaminate — `KO_FULL − KO` = +0.07060 — the drift is **0.00 %**.

### The zero is checked, because S-042 taught me not to trust one

An exact zero is exactly what a vacuous self-comparison produces, so before recording this I
verified the two arms are genuinely distinct runs:

```
KO_AXIS        -> csi1_button_train_KO_AXIS_20260915_195425_1707119   end 20:08:35
KO_AXIS_ANCHOR -> csi1_button_train_KO_AXIS_ANCHOR_20260915_194600_3238175  end 20:18:13
SAME DIRECTORY? False
```

Different run ids, different arm labels, different end timestamps, different jobs, different nodes
— and the *same* `basis_key = cand_rank1` and `layer = 20`, which is what makes them a valid
anchor pair. The anchored resolver from S-042 is what keeps `KO_AXIS` from swallowing
`KO_AXIS_ANCHOR`, and it demonstrably did.

### What this licenses, and what it says about the endpoint

* **The cross-allocation comparison is safe.** Group B's shuffled and random controls may be
  contrasted against group A's candidate with no hardware-drift term at all. The Holm specificity
  analysis is unconfounded.
* **A readout on fixed architecture is bit-reproducible.** This is the same fact S-032 found from
  the other direction (the L40S replicate reproducing published refusal numbers to five decimals),
  now at the strongest possible resolution: 670 keys, zero differences. It also sharpens S-016 —
  the 23 % byte-identity figure is **entirely** a cross-*architecture* phenomenon.
* **The S-037 architecture pin was the right call, and is now shown to be sufficient.** Holding GPU
  model fixed reduces the drift term to exactly zero; nothing further (same node, same allocation)
  buys anything for this endpoint.

One practical consequence worth carrying into Phase 2: for **readout** endpoints, arms do *not*
need to share an allocation — only an architecture. That materially loosens the scheduling
constraint for the larger banks, where forcing 17 arms into one allocation is what created the
8-hour walltime problem in the first place.

---

# S-046 — **PR-CSI-001 PRIMARY RESULT, button, TRAIN.** The rank-1 installation axis does NOT mediate. Dimensionality does.

Group A complete (job 896679, all seven arms, one allocation, n-303 / `geforce_rtx_3090`).
`reports/DCS_CSI_SUBSPACE_button_train.json`. **`VOID: []`** — no void condition triggered.

## Gates (all three PASS)

| gate | contrast | estimate | CI95 | pos/neg/tied | p |
|---|---|---|---|---|---|
| manipulation | `KO − BASE` | **−0.20704** | [−0.2264, −0.1886] | 0 / **67** / 0 | < 1e−5 |
| identity | `KO_SELF − KO` | −0.00076 | [−0.00165, +0.00013] | 28 / 39 / 0 | 0.107 |
| capability | `KO_FULL − KO` | **+0.07060** | [+0.0606, +0.0812] | **66** / 1 / 0 | < 1e−5 |

## THE PREREGISTERED PRIMARY

> **`KO_AXIS − KO_ORTH` = +0.00041, CI95 [−0.00034, +0.00116], 39/28 pos/neg, p = 0.290.**
>
> **VERDICT: THE PRIMARY DOES NOT PASS.**

At matched rank (1) and matched norm (to 1.4e−17 per row), **the installation-predictive direction
does no more than an arbitrary orthogonal direction.**

**This is a well-powered null, not an uninformative one.** With 67 informative domains the exact
test has resolution to p = 1.4e−20 — it is nowhere near its floor. The CI width is **0.0015**,
i.e. we exclude any effect larger than **1.6 % of the positive control's**. And per S-041's dose
argument the linear-in-dose prediction for a 3.5 %-energy intervention is **+0.00246** — which the
CI **also excludes**. The axis does *less* than a naive dose extrapolation, not merely "not more
than a control".

## The dose ladder — and the finding the primary alone would have hidden

| arm | rank | captured energy | recovery vs KO | CI95 | p | recovery / dose | linear prediction |
|---|---|---|---|---|---|---|---|
| `KO_ORTH` | 1 | 1.28 % | −0.00001 | [−0.0008, +0.0008] | 0.971 | −0.001 | +0.00090 |
| `KO_AXIS` | 1 | 3.48 % | +0.00040 | [−0.0003, +0.0011] | 0.249 | 0.012 | +0.00246 |
| **`KO_PLS`** | **5** | **10.04 %** | **+0.00302** | **[+0.0013, +0.0047]** | **0.00102** | **0.030** | +0.00709 |
| `KO_FULL` | 4096 | 100 % | **+0.07060** | [+0.061, +0.081] | < 1e−5 | 0.071 | — |

Three things fall out:

1. **The rank-5 PLS subspace DOES beat KO** (+0.00302, 50/17 domains, **p = 0.001**) where the
   rank-1 axis does not. Restoring five dimensions recovers **7.5×** what one dimension recovers
   while carrying only **2.9×** the energy.
2. **Recovery per unit dose rises monotonically with rank**: −0.001 → 0.012 → 0.030 → 0.071. The
   effect is **superlinear in dimensionality**, not in norm.
3. **Every subspace arm recovers *less* than linear-in-norm** (0.00040 vs 0.00246; 0.00302 vs
   0.00709). Restoring a given amount of norm along few directions is worth far less than the same
   norm spread across the state.

Read together: the knockout's effect on installation is **not carried by one direction**, and it is
not simply a matter of how much norm you put back — it needs *many* dimensions. That is a
**distributed** representation result, and it is exactly the shape plan §19 Gate A anticipated for
a NO: *"investigate whether the information is distributed/nonlinear."*

## The limitation that blocks the strongest version of this claim

**`KO_PLS` has no rank-matched control.** Every control in the frozen candidate set —
`ctrl_orth`, `ctrl_random0..7`, `ctrl_shuffled0..4` — is **rank 1**. So `KO_PLS`'s significance is
measured against `KO`, and its advantage over `KO_AXIS` is **confounded with dose** (10.0 % vs
3.5 % captured energy). I cannot yet say whether rank-5 wins because of *which* five directions or
merely because it is *five* directions.

**This is the immediately indicated next experiment**, and it is being built now: rank-5 random and
rank-5 shuffled-label subspaces, norm-matched to `cand_pls5`. Until it runs, the licensed statement
about `KO_PLS` is *"a rank-5 subspace recovers significantly more than the knockout alone"* and
**not** *"the installation subspace is causal"*.

## What may and may not be said

**MAY:** the preregistered rank-1 primary is a **well-powered null** at matched dose; the whole-state
rescue at the same site recovers **34 %** of the installation loss (so the site is causal); recovery
is superlinear in rank; a rank-5 subspace recovers significantly more than KO.

**MAY NOT** (and PR-CSI-001's `must_not_be_said_if_null` list governs):
* *"The query-side representation carries no installation information."* — refuted by `KO_FULL`.
* *"Semantic installation is not causally mediated."* — one subspace, one layer, one site.
* *"The installation subspace is causal."* — `KO_PLS` lacks its rank-matched control.
* *"The representation is one-dimensional."* — the opposite of what this shows.

## Relation to the literature (S-036)

arXiv:2605.18830 reports that an ICL **concept subspace is causal** and that *"patching the
complementary subspace restores 0 %"*. Our rank-1 result points the other way on this attack and
this model. That is a **dissociation from a published positive**, which S-036 flagged as the likely
shape of our contribution — and it is a reason to hold the controls to a higher standard, not a
lower one. It is also consistent with their result if the causal object is a *multi-dimensional*
subspace rather than a direction, which is precisely what the rank ladder suggests and what the
rank-matched control will test.

---

## S-047 — the repo's own completeness guard blocked my commit, and it was right: one row missing per shuffled control, from **my own degeneracy guard firing in production**

`check_all.py` refused the S-046 commit: `run_completeness_check` FAILED with

```
SHORT csi1_button_train_KO_SHUF0: persisted 669 rows against --expect-n 670
SHORT csi1_button_train_KO_SHUF1: persisted 669 rows against --expect-n 670
```

**Cause, traced to the row:** the `SubspaceDonorPatch` degeneracy refusal added in review **R2-M5**
— the one that raises rather than injecting an arbitrary QR-gauge direction when a control subspace
carries < 1e−6 of the delta. On one row of each shuffled arm (`b1471eb1c15d84b3`,
`efccdac0f106d4bd`) the shuffled-label basis was near-orthogonal to the KO→clean delta at **1 of 28
positions**, and the guard refused the row.

**The guard is working exactly as designed** — it declined to fabricate a control rather than
silently writing a meaningless one. That is the behaviour I wanted. But it creates a second-order
problem the guard cannot see.

### The second-order problem, and why it is R2-B1 again

A missing row makes that arm's population differ from the others'. My analyser intersected
**domains**, not **(domain, slot) keys** — so the affected domain's mean for that arm would have
been an average over **fewer slots** than the arms it is paired against. **That is exactly review
R2-B1's defect arriving by a completely different route**: paired means over non-identical key sets.

**Fixed:** the analyser now intersects `(domain, slot)` keys across **all** arms before averaging,
reports `keys_dropped_by_intersection` per arm, and prints the intersection when it bites.
Re-verified on group A (all seven arms at 670 keys, so a no-op there): the primary is **unchanged**
at +0.00041, CI [−0.00034, +0.00116], p = 0.290.

### Why the loss is acceptable, argued rather than asserted

The two dropped rows are **outcome-independent**: degeneracy is a property of the angle between a
*fixed* basis and a *fixed* delta, both determined before any readout — and the delta is
**identical across arms**, since it is the same KO→clean difference. It is not domain-clustered
(one row, one arm, each). And after the key intersection every arm is compared on exactly the same
key set regardless. Both runs are now documented in the guard's `KNOWN_SHORT` with that reasoning
spelled out; the guard passes.

### The meta-point

This is the third time today a guard I did not write caught something I would have shipped — after
`strict_run_dir` refusing ambiguous tags and the pre-commit test suite. And the chain here is worth
noticing: **a fix from review round 2 (R2-M5) caused a row loss, which the repo's completeness
guard caught, which exposed a gap that was review round 2's other finding (R2-B1) in disguise.**
Defensive machinery compounds — each layer catches what the previous one's fix disturbed. The cost
was one blocked commit; the alternative was a control arm quietly averaged over a different
population than the candidate it is meant to bound.

---

## S-048 — building the control S-046 showed was missing: a **rank-5 matched** comparator for `KO_PLS`

S-046's finding — rank-5 recovers significantly (+0.00302, p = 0.001) where rank-1 does not — is
**not yet attributable to direction**, because every control in the frozen set is **rank 1**. A
rank-r subspace captures ≈ √(r/d) of any vector *before any information enters it*, so `KO_PLS`'s
advantage over `KO_AXIS` is confounded with dose (10.0 % vs 3.5 % captured energy). Group C supplies
the missing comparator.

**New bases** (`--rank-controls 5`, job 896950): six **random rank-5** subspaces
(`ctrl_random_r5_0..5`, pure geometry) and four **rank-5 PLS fits on domain-preserving shuffled
labels** (`ctrl_shuffled_pls5_0..3`, same fitting procedure, same dimensionality, no real
label–feature association). Every group-C arm is **norm-matched to `cand_pls5`**, so the only thing
varying across the arm set is **which five directions**.

### A provenance hazard, caught and handled

Regenerating the axis on a different node reproduced every **scalar** exactly but changed the
**data-derived tensors** in their last bits — the same cross-node effect as S-014/S-019. Confirmed
by which keys matched: the **8 seeded-random bases were identical**; all 12 data-derived ones
differed. Using the regenerated `cand_pls5` as group C's norm-match reference would have meant the
candidate arm (group A) and its controls (group C) were matched to **different tensors**.

So rather than adopting the new file, I **merged only the genuinely new keys into the original
artifact** and verified the originals survived untouched — against the **git-committed** copy, not
against the JSON's own hashes (those are computed pre-float32-cast, which made my first check
compare apples to oranges and report a spurious 20/20 "changed"):

```
original keys: 20   changed by the merge: NONE (max|diff| = 0.0 on every one)
new keys added: 10  (ctrl_random_r5_0..5, ctrl_shuffled_pls5_0..3)
```

`cand_rank1`, `cand_pls5` and `ctrl_orth` are therefore **byte-identical** to what groups A and B
ran against. The artifact records the merge and its provenance in `meta.rank_matched_controls_added`.

**Job 896961** launched on n-350 (`geforce_rtx_3090`, matching groups A and B per S-037), 11 arms:
`KO_PLS_ANCHOR` + 6 random-rank-5 + 4 shuffled-rank-5.

### What group C can and cannot settle

* If `KO_PLS` beats its rank-5 matched controls → **the specific five directions matter**, and the
  installation subspace has causal content that rank-1 could not express.
* If `KO_PLS` ≈ its rank-5 controls → its advantage over rank-1 was **dose, not direction**, and the
  honest conclusion becomes that recovery scales with how much of the perturbation you restore
  *however you restore it* — i.e. the knockout's effect on installation is **genuinely distributed**
  and not carried by any identifiable low-dimensional subspace at this site and layer.

Either way it is the contrast that decides, and it is now preregistered by this entry before the
arms have produced a single row.

---

## S-049 — the shuffled-label controls **calibrate** the null: the candidate sits *inside* the control distribution, and one shuffled control beats it

Group B's four rank-1 shuffled-label controls are complete. Re-analysed with all 11 available arms
on the **668 keys common to every arm** (the cross-arm intersection from S-047 doing its job — two
arms are short by one row each, so every arm is compared on the same 668).

`VOID: []`. All gates pass. Primary essentially unchanged: **`KO_AXIS − KO_ORTH` = +0.00040,
CI [−0.00036, +0.00114], p = 0.308.**

### Recoveries against KO (67 domains)

| arm | recovery | CI95 | pos/neg | p |
|---|---|---|---|---|
| `KO_FULL` | **+0.06968** | [+0.0596, +0.0803] | 66/1 | < 1e−5 |
| `KO_PLS` (rank 5) | **+0.00295** | [+0.0012, +0.0046] | 49/18 | **0.0013** |
| `KO_SHUF2` | **+0.00098** | [+0.0004, +0.0016] | 46/21 | **0.0020** |
| **`KO_AXIS`** (candidate) | **+0.00037** | [−0.0003, +0.0010] | 40/27 | 0.292 |
| `KO_ORTH` | −0.00003 | [−0.0008, +0.0007] | 34/33 | 0.936 |
| `KO_SHUF1` | −0.00000 | [−0.0007, +0.0006] | 38/29 | 0.992 |
| `KO_SHUF0` | −0.00073 | [−0.0016, +0.0001] | 27/40 | 0.100 |
| `KO_SHUF3` | **−0.00144** | [−0.0021, −0.0008] | 24/43 | **0.00015** |

### The finding: **shuffled-label controls are not null, and the candidate is not the best of them**

Two of four shuffled controls are individually significant at p < 0.05 — **in opposite directions**
(`KO_SHUF2` **+0.00098**, `KO_SHUF3` **−0.00144**). The shuffled spread runs from −0.0014 to
+0.0010, i.e. **±0.001**, which is **larger than the candidate's entire effect** (+0.00037).

> **The candidate ranks 2nd of 5 in the control distribution — `KO_SHUF2`, a direction fitted to
> randomised labels, recovers 2.6× more than the real installation axis.**

That is the calibration the primary null needed. It is no longer only "the axis does no better than
an orthogonal direction"; it is **"the axis does no better than a direction fitted to shuffled
labels, and worse than one of them."** Any rank-1 perturbation of this norm nudges the readout by
~±0.001 in an arbitrary direction, and the installation axis is indistinguishable from that noise.

### A methodological correction to my own specificity test

Holm over the four candidate-vs-control contrasts rejects **only `KO_SHUF3`** (p_holm = 0.00034).
**That rejection does not support specificity** — it fires because `KO_SHUF3` is unusually
*negative*, so `candidate − SHUF3` is positive. My specificity test is **two-sided**, which
conflates *"the candidate beats this control"* with *"the candidate differs from this control"*.

Recorded rather than silently reinterpreted: for a specificity claim the test must be **one-sided**
(candidate > control). Under a one-sided reading the honest summary is the rank statistic the
analyser already reports: **candidate rank 2 of 5, attainable rank-p floor 0.2** — no specificity,
and not enough controls to have shown any even if it existed. **Checklist P1-h:** make the
specificity test one-sided and report direction per control.

### What this does and does not change

* **Strengthens** the S-046 primary null substantially — it is now bracketed by a measured control
  distribution rather than a single orthogonal draw.
* **Raises the bar for `KO_PLS`.** At +0.00295 it is 3× the largest shuffled rank-1 control, which
  is suggestive — but those controls are **rank 1** and `KO_PLS` is **rank 5**, so the comparison is
  still dose-confounded. **Group C is now the load-bearing experiment of this phase**, not a
  nicety: without rank-5 matched controls, "+0.00295 beats the rank-1 shuffled spread" is a
  statement about dimensionality, not direction.
* Six rank-1 random controls (`KO_RAND0..5`) are still running and will widen the calibration.

**Addendum to S-049 — the short-run documentation is now automated, but only for the cause it can verify.**
`KO_RAND0` came back 669/670 from the same degeneracy refusal (row `dd0c77189b0e8fcb`), and with
~20 control arms still to run this will recur. Rather than hand-write each `KNOWN_SHORT` entry —
which invites a copy-paste that says something slightly untrue about a run nobody re-checked —
`scripts/dcs_csi_known_short.py` generates them, and **refuses any run it cannot verify**: the
shortfall must be ledgered *entirely* to the degeneracy refusal, and the ledger's counts must agree
with the rows on disk. Anything else it prints as `LEFT FOR A HUMAN`. That keeps the guard's
purpose — forcing per-run justification — while removing the transcription risk it would otherwise
create.

---

# S-050 — **The rank-5 result was DOSE, not direction.** A random rank-5 subspace beats the installation subspace. And a "PRIMARY PASSES" verdict that must NOT be believed.

Group C's first three rank-5 matched controls are in, and they settle S-048's question.

## Rank-5 arms, recovery vs KO (67 domains, common-key intersection)

| arm | recovery | CI95 | pos/neg | p |
|---|---|---|---|---|
| `KO_FULL` (rank 4096) | **+0.07060** | [+0.061, +0.081] | 66/1 | < 1e−5 |
| **`KO_R5RAND2`** (random) | **+0.00428** | [+0.0032, +0.0054] | 56/11 | < 1e−5 |
| **`KO_PLS`** (the candidate) | **+0.00302** | [+0.0013, +0.0047] | 50/17 | 0.001 |
| `KO_PLS_ANCHOR` | +0.00302 | — | 50/17 | 0.001 | 
| `KO_R5RAND1` (random) | **−0.00285** | [−0.0038, −0.0019] | 17/50 | < 1e−5 |
| `KO_R5RAND0` (random) | **−0.00532** | [−0.0064, −0.0043] | 7/60 | < 1e−5 |

**A norm-matched RANDOM rank-5 subspace spans −0.0053 to +0.0043 — and one of the three
(`KO_R5RAND2`, +0.00428) recovers MORE than the installation subspace (+0.00302).** The candidate
ranks **2nd of 4**.

> **S-046's rank-5 significance was dimensionality, not direction.** Restoring *any* five
> norm-matched directions moves the readout by several times what one direction does; which five
> they are does not appear to matter. The apparent "rank-5 works where rank-1 does not" is a dose
> effect, exactly the confound S-048 was built to test for — and the test says the confound was the
> whole story.

Note also how much *larger* the rank-5 arbitrary effects are than the rank-1 ones (±0.005 vs
±0.0016). That is the superlinear-in-rank pattern of S-046 reappearing **in the controls**, which
is the cleanest possible demonstration that the pattern is about how much of the state you disturb,
not about what you restore.

## ⚠ The analyser printed **"PRIMARY PASSES"** and it must not be believed

Running the rank-5 configuration with `--comparator-arm KO_R5RAND0` produced:

```
VERDICT: PRIMARY PASSES on split=train -- candidate beats its norm-matched comparator
```

**That verdict is an artifact of which control I happened to name as the comparator.**
`KO_R5RAND0` is the *most negative* control in the distribution (−0.00532), so the candidate beats
it overwhelmingly (one-sided p = 5e−6, Holm-corrected 1.5e−5). Name `KO_R5RAND2` instead and the
same data yields a clear FAIL (p = 0.869).

This is the **same failure mode as S-049's two-sided Holm**, at the level of the verdict rather
than the test: with a control distribution spanning ±0.005, **any single control is an arbitrary
comparator**, and a verdict built on one is a coin-flip dressed as an inference.

**The honest statistic is the one the analyser already emits alongside it** — the candidate's
**rank within the control distribution**: 2 of 4 here (attainable rank-p floor 0.25), 3 of 8 for
the rank-1 family. Both say the same thing: **the candidate is inside its control distribution.**

**Fix required (P1-i):** when a control family is present, the verdict must be computed from the
candidate's position in the control *distribution*, never from a single named comparator; and a
single-comparator verdict must be suppressed rather than printed. PR-CSI-001 named
`KO_AXIS − KO_ORTH` as the primary, which was defensible when `ctrl_orth` was the *only* control —
but `ctrl_orth` is now one draw among many and must be treated as such. **This is an amendment to
the preregistration, recorded before the remaining controls land**, and it *weakens* the reported
result rather than strengthening it: the rank-1 primary's p = 0.29 stands, and the rank-5 "pass"
is withdrawn before it was ever claimed.

## Where Phase 1 now stands

| candidate | its control distribution | candidate's rank | verdict |
|---|---|---|---|
| rank-1 installation axis | 7 controls, −0.0014 … +0.0016 | **3 of 8** | inside the distribution |
| rank-5 installation subspace | 3 controls (of 10), −0.0053 … +0.0043 | **2 of 4** | inside the distribution |
| whole state (4096) | — | — | **+0.0706, 66/67 domains, far outside anything** |

**The knockout's effect on semantic installation is not carried by any low-dimensional subspace we
can identify at this site and layer — informative or random. What predicts recovery is how much of
the state is restored, not which directions.** The site is unambiguously causal (`KO_FULL` recovers
34 % of the installation loss); the *representation* at that site is distributed.

Seven rank-5 controls remain (3 random + 4 shuffled) and will finish the distribution; the reading
above is stated on 3 of 10 and will be re-run when all land.

**P1-i implemented.** The analyser's verdict is now computed from the candidate's **rank within the
control distribution** whenever a control family of ≥ 2 is present; the single-comparator verdict is
**suppressed** and recorded only as a note saying what it *would* have said and that it is not
reported. Re-running the exact rank-5 configuration that printed `PRIMARY PASSES` in S-050 now gives:

```
VERDICT: PRIMARY DOES NOT PASS on split=train -- the candidate ranks 2 of 4 in its own
control distribution (rank p=0.5, attainable floor 0.25). It is INSIDE the controls,
not above them.
```

The verdict no longer depends on which control the caller names. Note the honest weakness the new
wording exposes and the old one hid: with 3 controls the attainable rank-p floor is **0.25**, so
even a candidate that beat every control could not reach α = 0.05 — **the rank-5 family needs its
full 10 controls before any pass is attainable at all.** That is now visible in the verdict string
instead of buried.

---

## S-051 — rank-5 distribution at 5 of 10 controls; and the POSITION ladder, which is the experiment the result now demands

**Rank-5 control distribution so far** (candidate `KO_PLS` = **+0.00302**):

| control | recovery |
|---|---|
| `KO_R5RAND2` | **+0.00428** |
| `KO_R5RAND1` | −0.00285 |
| `KO_R5RAND3` | −0.00468 |
| `KO_R5RAND0` | −0.00532 |
| `KO_R5RAND4` | −0.00565 |

**Candidate ranks 2 of 6** (rank p = 0.333, attainable floor 0.167). Verdict: does not pass.

**A nuance worth stating, and explicitly labelled EXPLORATORY.** Four of the five random rank-5
controls are **negative** — a random norm-matched subspace injection typically makes installation
*worse* than the knockout alone, which makes sense: injecting an arbitrary 5-dim component at 10 %
of the delta's norm is a perturbation, and perturbations mostly hurt. The candidate is the only
*positive* arm apart from one random outlier. Against the control **mean** (−0.0028) the candidate
sits ≈ 1.4 sd high.

**I am not switching to that test.** The rank statistic is what P1-i fixed and what the analyser
reports, and moving to a parametric comparison *after seeing* that it looks more favourable is
precisely the move this sprint has spent the day guarding against. The rank verdict stands; the
distributional observation is recorded as exploratory, to be revisited when all 10 controls land
(4 shuffled-label rank-5 are still to run, and they are the *harder* control — same fitting
procedure, same rank, no real labels).

## The next experiment: a POSITION ladder (group D)

Phase 1's finding is that recovery tracks **how much of the state is restored**, not which
directions. The dimension ladder established that for directions. **Positions are the other axis of
"how much", and it is untested.**

Group D restores the **full clean state** at a seeded-random subset of **k of the ~28 query-span
positions**, for k ∈ {1, 2, 4, 8, 14, 20, 28}. Only the number of restored positions varies.

* If recovery scales **smoothly with k**, the effect is distributed across the span as well as
  across dimensions, and "how much of the state" is the whole story.
* If **a few positions carry most of it**, that is **localisation** — a genuine positive finding
  about *where* the installed meaning lives, reachable even though the *directional* question came
  back null.

This reuses `--rescue-n-positions`, the existing size-match mechanism (seeded per `prompt_id`,
refuses any row that cannot supply k), so **no new intervention code is involved** — the same
primitive that produced the behavioural size-match arm, applied to the endpoint that actually has
resolution.

It is also the natural successor to the **withdrawn** behavioural size-match claim (C2 / S-002):
that contrast could not be resolved at 2–5 informative domains on refusal, and here it has 67.

**VALIDATION group A launched** (job 897057, n-303, `geforce_rtx_3090`): the seven-arm set on the
held-out 230 rows / 23 domains, to convert the TRAIN discovery into a held-out claim.

---

# S-052 — **DEFINITIVE rank-1 result: the installation axis ranks 4th of 11 in its own control distribution.**

Group B complete (job 896771). The full rank-1 control family — **6 random + 4 shuffled-label**
directions, every one norm-matched to the candidate per row — analysed on the **666 keys common to
all 16 arms**.

| | recovery vs KO |
|---|---|
| `KO_RAND2` | **+0.00159** |
| `KO_SHUF2` | **+0.00104** |
| `KO_RAND3` | **+0.00049** |
| **`KO_AXIS`  ← the candidate** | **+0.00040** |
| `KO_SHUF1` | +0.00011 |
| `KO_RAND5` | +0.00008 |
| `KO_RAND1` | +0.00005 |
| `KO_RAND4` | −0.00038 |
| `KO_SHUF0` | −0.00068 |
| `KO_RAND0` | −0.00098 |
| `KO_SHUF3` | −0.00138 |

> **The installation axis ranks 4 of 11.** Three controls — two random directions and one fitted to
> shuffled labels — recover *more* than it. Rank p = 0.364.

The control distribution is centred near zero (median ≈ +0.00007) with a spread of ±0.0015, and the
candidate sits unremarkably inside it. **This is not a power failure**: with 10 controls the rank
test would have reached p = 0.0909 had the candidate been strictly largest, and it is not close to
largest. (Worth stating plainly, though: 1/11 = **0.0909 is above 0.05**, so a rank test with 10
controls cannot reach α = 0.05 even in the best case — ≥ 19 controls would be needed. That limits
what a *positive* could have claimed; it does not soften this negative, which fails on rank, not on
resolution.)

## Phase 1's answer, stated at full strength

**PR-CSI-001 asked:** under the live A1 knockout, does restoring only the installation-predictive
component of the query representation restore semantic installation?

**Answer: NO — and the null is comprehensively controlled.**

| | result |
|---|---|
| the **site** is causal | `KO_FULL` recovers **+0.0706**, 66/67 domains, 34 % of the knockout's installation loss |
| the **rank-1 axis** | ranks **4 / 11** in its control distribution; CI [−0.0003, +0.0010] excludes even the linear-in-dose prediction |
| the **rank-5 subspace** | ranks **2 / 6** so far in its *rank-matched* controls; its apparent significance was **dose** |
| the **controls** | random and shuffled directions produce effects up to ±0.0016 (rank 1) and ±0.0057 (rank 5) |

**The knockout's effect on semantic installation is distributed.** No low-dimensional subspace we
can identify at rel-6 / L20 — informative, random, or shuffled — carries it. What predicts recovery
is **how much of the state you restore**, not which directions.

This is **plan §19 Gate A = NO**, with the plan's own instruction followed: *"Do not force the
causal-representation story. Investigate whether the information is distributed/nonlinear."* The
position ladder (group D) is that investigation on the remaining axis.

## Claim-table consequences

**MAY now be said** (TRAIN, button, pending VALIDATION):
* the demonstration→query attention edge is causally necessary for semantic installation
  (−0.207, 67/67 domains, reproducing DR-071);
* the **query-span state at rel-6/L20 causally carries a third of that effect** (whole-state rescue,
  +0.0706, 66/67);
* **no rank-1 or rank-5 subspace at that site reproduces it** beyond its matched controls.

**MAY NOT be said:**
* *"the installation representation is causal"* — refuted here at rank 1 and unsupported at rank 5;
* *"there is no installation representation"* — `KO_FULL` refutes that; the information is there,
  it is simply not low-dimensional **at this site and layer**;
* *"installation is not mediated by the query state"* — the opposite of the `KO_FULL` result;
* anything about **other layers or sites** — one site, one layer, one codeword, TRAIN only.

---

# S-053 — **VALIDATION replicates.** The recovery fraction is held-out to within 0.013.

Job 897057, the held-out split: **230 rows / 23 domains**, arms `BASE, KO, KO_SELF, KO_FULL,
KO_AXIS` complete (`KO_PLS`, `KO_ORTH` still running). The axis is **out of sample** here — fit on
TRAIN, applied to domains it has never seen — which is the honest test.

| | **TRAIN** (670 / 67) | **VALIDATION** (230 / 23) |
|---|---|---|
| `BASE` | 0.67843 | 0.67145 |
| `KO` | 0.47140 | 0.38154 |
| **gate 1 manipulation** `KO − BASE` | −0.20704, **0/67** | **−0.28991**, [−0.343, −0.246], **0/23** |
| **gate 2 identity** `KO_SELF − KO` | −0.00076, p = 0.107 | **+0.00075**, [−0.0008, +0.0023], p = 0.361 |
| **gate 3 capability** `KO_FULL − KO` | +0.07060, **66/1** | **+0.09502**, [+0.0767, +0.1145], **23/0** |
| **recovery fraction** | **0.3410** [0.3064, 0.3752] | **0.3278** [0.2896, 0.3631] |
| `KO_AXIS − KO` | +0.00040, p = 0.249 | +0.00134, [0.00000, +0.00275], p = 0.073 |

**All three gates pass held-out**, and gate 3 does so on **23 of 23 domains** with no dissenter
(TRAIN had 66/67).

## The finding that replicates is the scale-invariant one

The absolute quantities are *larger* on VALIDATION — the knockout removes more installation
(−0.290 vs −0.207) and the whole-state rescue restores more (+0.095 vs +0.071). The validation
domains are simply more susceptible. But the **recovery fraction — the quantity the claim is about
— replicates to within 0.013**: 0.3410 vs 0.3278, with CIs overlapping across most of their range.

> **Held-out claim, now defensible: under the A1 knockout, restoring the clean query-span state at
> rel-6/L20 recovers about one third of the semantic installation the knockout removes.**
> TRAIN 34.1 % [30.6, 37.5], VALIDATION 32.8 % [29.0, 36.3].

That is the sprint's central *positive* result, and it is the one that survives on held-out data.

## `KO_AXIS` on VALIDATION — and why it must not be reported as a trend

`KO_AXIS − KO` comes out **+0.00134, p = 0.073**, larger than TRAIN's +0.00040 and closer to
significance. **It would be wrong to call that a trend**, for a reason this sprint has already
measured rather than assumed:

> On TRAIN, **random rank-1 directions reached +0.00159** and a shuffled-label direction reached
> +0.00104 (S-052). **+0.00134 sits inside that range.**

A bare `candidate − KO` number is uninterpretable without its control distribution — that is the
whole lesson of S-050 and S-052. `KO_ORTH` is still running and the validation control family does
not exist at all yet. Until it does, the honest statement is: **the validation axis effect is
within the range arbitrary directions produced on TRAIN**, and nothing more. Recorded now, before
the comparator lands, so the reading is fixed in advance.

## Claim-table status

**MAY be said (TRAIN + VALIDATION, button):**
* the demo→query attention edge is causally necessary for semantic installation — 67/67 and 23/23 domains;
* the query-span state at rel-6/L20 causally carries **≈ 1/3** of that effect, **replicated held-out**;
* the whole-state rescue is the only intervention that has ever cleared its controls.

**MAY NOT be said:** anything positive about the rank-1 axis on VALIDATION until its control family
exists; anything about other layers, sites, codewords, or TEST.
