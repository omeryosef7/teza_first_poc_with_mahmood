# Demonstration Retrieval → Behavioral Causality — plan, decision gates, and live progress log

**File:** `external_md/DEMONSTRATION_RETRIEVAL_BEHAVIORAL_CAUSALITY_NEXT_PHASE_PLAN_AND_PROGRESS.md`
**Opened:** 2026-08-25 00:30 IDT
**Repo:** `first_poc/teza_first_poc_with_mahmood`, branch `behavioral-causality-sprint`
**HEAD at open:** `059e819f` ("C-18 code closure: four defects fixed and verified; the tool now warns
about its own statistic", 2026-08-24 23:53:54 +0300)
**Owner of this phase:** this Claude session. SLURM submissions for this phase are owned here and
logged in §B4.

> **This file is the authoritative live research log for this phase.** Part A (the plan) is **stable**
> and is not rewritten as results arrive. Part B is **append-oriented**: superseded conclusions are
> marked `⛔ RETRACTED — reason` with the corrected statement beside them, never silently overwritten.

> **Concurrency.** A peer Claude session (`BOOMBNESS_D_SURFACE_FOLLOWUP implementation`) owns the
> previous phase's log (`external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md`) and
> `src/boombness/crossbank_knockout_test.py`, and had jobs **779083–779086** (Phase 10b, `button_gun`)
> in flight when this file was opened. **This session does not touch those files or those jobs and does
> not run `scancel`.** Staging is by explicit path; `git add -A` is forbidden here.

---

## ⚠️ READ THIS FIRST — LIVE CLAIMS LEDGER *(initialised 2026-08-25 00:30)*

**Nothing in this phase has produced a result yet.** The rows below are the **inherited** state this
phase starts from, carried in so that no figure is quoted from the previous phase without its current
status attached. Every row names the correction that last touched it.

### ✅ LIVE — what currently stands (inherited)

| claim | evidence | where |
|---|---|---|
| **The demonstration-attention knockout suppresses the doublespeak attack — DIRECTION, on the bomb corpus** | ⚠ **AMENDED by R-2.** The pooled 113 / 30 (p = 1.577e-12) is **one demonstration corpus**: bomb **81/11 p = 2.50e-14**, knife **15/7 p = 0.134**, gun **17/12 p = 0.458**; **drop bomb → 32/19, p = 0.092**. The 143 comparisons come from **67 distinct prompt_ids**. Replicates on the high-headroom bank of **both** models (**−0.1771** Llama, **−0.2083** Qwen3); every arm verified live; **no fitted direction, so no dose confound is possible** | R-R, R-T, R-AB, R-AY; **amended R-2** |
| ⚠ **…and the binding constraint is the number of DOMAINS, not banks/pools/models** | domain marginal k=6: `game_manual` −0.2562, `news_report` −0.0938, `city_bridge` −0.0875, `instructional` −0.0750, `farm_storage` −0.0063, `lab_safety` +0.0000; mean −0.0865, sd 0.0927, d = 0.933, **CI upper +0.0108 → includes zero**. Projection at fixed mean/sd: **8 domains → −0.0090 (excludes zero)**, 10 → −0.0202, 12 → −0.0276 | **prev-R-BE** (`7838dcd2`), inherited; see **D-4** |
| **The both-EOS control is not a 10-population control** | reproduces at 30/1 (p = 2.98e-08) but **5 of 10 populations contribute zero both-EOS discordant rows** | **R-2** |
| ⚠ **…but NO calibrated cluster test of MAGNITUDE excludes zero** | `pool × domain` k=18 was a **crossed 3×6 table on one shared 96-prompt set**; both marginals include zero (**k=3 pools [−0.3043, +0.1516]**, **k=6 domains [−0.1649, +0.0121]**); crossed random-effects CI **[−0.2796, +0.1268]** at df 2.53 | **C-18 / REVIEW-8** — *R-BD RETRACTED* |
| Retrieval and refusal are **independent channels** on Llama | knockout Δ = −0.1771 with refusal intact **and** with refusal removed; refusal removal alone includes zero | R-T ⚠ aggregate-level only (see DEAD row on "the same 17 prompts") |
| **The mechanism is layer-redundant** | all 40 heads of Qwen3 L8 = **+0.0104**; ≥8 contiguous layers needed for a large effect | R-AM, R-AQ (D-12) |
| **A concept axis `N` is invariant across 4 codewords at the split-half ceiling** | cos **0.984–0.989** vs an isotropic null with \|max\| **0.0569** | R-AE P4, survives C-7 |
| **Concept identity is a dominant plane with real third-direction structure** | PC3 **0.164–0.249** vs a pre-registered isotropic null of **[0.3170, 0.3297]**; replicated on two codewords | R-AX, R-BC |
| **Codeword identity is a (K−1)-dim subspace, not an axis** | four distinct reproducible `u_c`, split-half 0.985–0.997 | R-AE Test 2, C-4 |
| **`d_surface` fails specificity at matched dose** | at a real dose *below* the inert concept arm the codeword arm does nothing (+0.0104, p = 1.0000) | R-AH |
| **The retrieval scalar fails prediction and transfer** | vanishes within `n_examples` strata (3 of 4 exactly 0.0000); band-mean **anti-predicts** on Qwen3 | R-AJ, R-AK |
| **Attackability is a (bank × model) property** | two models on the identical bank share **1 of 9** attackable prompts | R-AU |

### ⛔ DEAD — do not quote these

| retracted claim | why | superseded by |
|---|---|---|
| **R-BD** "the calibrated CI excludes zero at k=18" (Δ −0.0764, [−0.1459, −0.0069]) | crossed 3×6 table on one shared prompt set; **62.1 %** of the spread is two main effects counted 3× and 6× over | **C-18** |
| **R-BA** (p = 0.0156 "weights by evidence", "robust to any drop") | p is sign-only; LOO provably cannot fail; fails leave-one-**model**-out (0.109) | C-16, C-17 |
| **R-AR** `p = 2.44e-04` and its bank×domain clustering | banks share only 2 demo pools → bootstrap miscalibration → model non-independence | C-11 → C-13 → C-14 → C-17 |
| **R-AV / R-AW** ("CI excludes zero at EVERY unit"; "every arm excludes zero, every control includes it") | percentile bootstrap ~30 % too narrow at small k; tail counts are the arithmetic floor `(n_zero/k)^k` | C-14 |
| **R-AG** "at matched dose, identity decides behaviour" | dose measured in a space the hook does not act in (6.60× real gap) | C-6 |
| **R-AN / R-AO / R-AP** layer laws | fitted to 1–3 prompt differences smaller than the measurement's own reproducibility | C-10 |
| R-AK "attention mass irrelevant at **any** granularity" | at head granularity the causal band wins on Qwen3 | C-8 |
| "the codeword axis `W`" / "the concept axis `N`" **as axes** | both are chords of subspaces | C-4, R-AX |
| Qwen3 "**hard** `in_subspace_orth` control" | 24.79× weaker; a dose-matched orthogonal control at L11 cannot exist | C-3 |
| **`C_all` (all-layers knockout) as "100 % suppression"** | degenerate — 24 (Llama) / 10 (Qwen3) distinct completions of 96 | R-AB, S8 |
| **The old `--demo-deleted` arm as a population ceiling** | the 96-row arm is **one prompt**, 1 distinct generation | REVIEW-2 M1 |
| **`goal_topicality` as evidence the model lost the mapping** | reads 0.0000 on the baseline too, by construction on a doublespeak bank | R-R |
| **"the knockout removes the same ~17 prompts regardless of refusal state"** | nets are −17/96 in both, but **23 vs 19** prompts cross the threshold and the down-sets overlap in only **7** | Part-II audit §11.1 defect 3 |
| **`uniq_frac` as "distinct completions"** | it is distinct completion **lengths**; by text Llama A and C_band are **96/96** unique | Part-II audit §11.1 defect 4 |

### 🔬 IN FLIGHT

*(none from this phase yet — see §B3 for the Phase-0 board)*

---

# PART A — THE PLAN *(stable; do not rewrite as results arrive)*

## 0. CURRENT STATE — TREAT THIS AS THE STARTING TRUTH

We continue from branch `behavioral-causality-sprint`. The plan as handed over named `8c83c8f3` as the
last audited state; **HEAD had already moved three commits past it when this file was opened**, and the
third of those commits **retracts the headline that `8c83c8f3` published**. Do not hard-reset. The
starting truth below is stated against `059e819f`.

**Reading order:** (1) `reports/SPRINT_SUMMARY_2026-08-23_TO_08-24_PART_II.md`;
(2) `external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md`, especially its LIVE CLAIMS
LEDGER; (3) `reports/SPRINT_SUMMARY_2026-08-16_TO_08-23.md`;
(4) `reports/boombness_objective_sprint_report.md`; (5) the existing causal-intervention code
(`doublespeak_causality/pair_common.py`, `src/boombness/score_behavior.py`,
`src/boombness/surgical_knockout.py`); (6) `external_repos/interp-jailbreak` (Matan/Mor), reusing its
surgical patching / knockout methodology rather than reinventing infrastructure.

### What is closed

**`d_surface` is not our attack objective.** It is a real and highly reproducible representational
object, but there is **no demonstrated direction-specific causal role in jailbreak behaviour**. Its
apparent behavioural effects were repeatedly explained by **dose** or **output collapse**. The
crossed-bank repair gave the first genuinely dose-matched test and it was **negative**.
→ *Do not spend this sprint trying to rescue `d_surface`.*

**The attention-mass / retrieval-strength scalar is closed as an objective.** It is measurable, but
much of its apparent predictive power was `n_examples`; it does not track causal importance
consistently across models; on Qwen3 the relation **reverses**; and the strongest-attending single head
is causally **dispensable**. → *Do not build GCG/MAC around attention mass.*

**Fine-grained layer localisation is closed for now.** Differences between short sub-bands are smaller
than the experiment's own session-to-session reproducibility. → *No new large head sweep and no new
"layer law" unless a new experiment first provides a reason to reopen the question.*

### What survived

The strongest surviving result is the **demonstration-attention intervention**. Masking attention to
the demonstration block across a mid-stack band substantially suppresses the Doublespeak attack on both
models: **Llama-3.1-8B-Instruct ≈ −0.1771**, **Qwen3-14B ≈ −0.1667** (−0.2083 on the shared
high-headroom bank). The effect replicates across two model families; is much larger in the causal
mid-stack band than in the matched late-layer control; scales with demonstration count; is not explained
by the refusal channel on Llama; is distributed/redundant rather than carried by one head; and **fits no
direction, so the old direction-dose confound does not apply**.

**⚠ Correction to the plan's own statement of the magnitude claim.** The plan as handed over cites the
Phase-10 analysis — 3 pools, 5 banks, 2 models, 10 populations, `pool × domain` k=18, mean Δ ≈ −0.0764,
CI95 ≈ [−0.1459, −0.0069]. **That result (R-BD) was retracted by C-18 at 23:52 on 2026-08-24**, before
this phase opened. All ten populations use the **identical 96 `prompt_id`s**, so the 18 "clusters" are a
fully crossed 3 × 6 table in which **62.1 % of the variance is two main effects counted 3× and 6× over**;
both marginals include zero (k=3 pools [−0.3043, +0.1516]; k=6 domains [−0.1649, +0.0121]) and only
their product excludes it. **The correct position is C-17's:** *the direction is well supported;
no calibrated cluster test of magnitude excludes zero.* The result is also still materially stronger on
Qwen3 than on Llama — **Llama alone remains ≈ p = 0.131**, and under C-18's leave-one-out sweep **every
single drop kills the exclusion**.

**This does not weaken the case for the plan; it strengthens it.** The plan's own priority — isolate
*what computation the knockout destroys* — does not depend on the magnitude claim, and Phase 4 below is
now a genuinely open confirmatory question rather than a formality.

### The key unresolved issue

The current knockout has **not established exactly what computation is being destroyed**. The present
attention knockout can affect more than generated response tokens: depending on the query row during
prefill, it can also interfere with the **demonstrations' own processing**
(`lo = max(0, kp − past)` blocks each demonstration token from attending to itself and to earlier
demonstration tokens — recorded as caveat **S8** in the previous phase). So the wording *"generated
answer tokens need to retrieve information from the demonstrations"* is **stronger than what has been
isolated**.

> **The highest-priority experiment of this sprint is to separate response-query retrieval from
> demonstration encoding / prefill corruption.** This is more important than another layer/head sweep.

### The larger scientific goal

The project currently has: *representation is real*; *behaviour is causally attackable*; **but
representation and behaviour still do not meet.** This sprint tests a stronger causal chain:

```text
demonstration block
    ↓
response-time retrieval
    ↓
semantic codeword binding / remapping
    ↓
distributed internal state
    ↓
behavioral compliance
```

The goal is **not** to force this chain to be true. It is to test it hard enough that, whether it
survives or fails, we learn what the mechanism actually is.

---

## 1. NON-NEGOTIABLE WORKING RULES

### 1.1 Scientific rules

**Never interpret an intervention before proving it fired.** Every new intervention must carry explicit
liveness instrumentation recording at minimum: number/fraction of rows where the intervention was live;
prefill forwards; decode forwards; prefill edits; decode edits; number of keys actually masked; query
positions affected; layers affected; heads affected; intended versus resolved spans. **Any full
experiment with liveness below the pre-registered threshold is VOID** — do not "interpret with a caveat".

**Pre-register before the expensive result exists.** For each major experiment, write down first:
(1) primary estimand, (2) primary comparison, (3) unit of independence, (4) expected outcomes,
(5) what each outcome would mean, (6) falsifier, (7) stopping rule, (8) which secondary analyses are
allowed. Do not add the interpretation after seeing the number, and **if an interim result looks
favourable, do not compute an unregistered favourable subset.**

**Null-model-first geometry.** For every geometric claim: define the null, simulate or derive it, save
the null artifact, and only then inspect the observed geometry. Do not call a structure interesting
because it visually looks regular.

**Measurement reproducibility before structure fitting.** If an effect differs by only a few prompts,
first repeat the exact same arm in a second judging session. Do not fit laws to differences smaller
than the measurement's own reproducibility.

**Distinguish effect size from p-value floors.** With small cluster counts a sign-flip p may be pinned
at its arithmetic minimum. Always report effect magnitude, number of informative clusters, attainable
p-floor, and a calibrated interval where appropriate. Run the "destroy magnitudes, preserve signs"
diagnostic on any permutation statistic claiming to use magnitude; **if the p does not move, call it a
sign test.**

**Never treat bank, model and prompt count as independent when they are not.** The demonstration pool is
the meaningful independence axis; banks sharing a pool are not independent clusters; Llama and Qwen3 on
the same material are not automatically independent replicates. **And per C-18: a crossed table over two
shared design factors is not k = product-of-levels.** Preserve the `pool × domain` logic only as a
*marginal* analysis unless a new design creates a genuinely different unit.

**No per-prompt causal stories from unstable judge labels.** Identical completions can cross the 0.5
StrongReject threshold on re-judging (measured: same generations, two sessions, same binary label on
only **78/96** rows). Aggregate rates and paired aggregate differences are usable; per-prompt
"this exact prompt was rescued" stories require much stronger evidence. **Do not say two interventions
affect "the same prompts" merely because their net deltas match.**

### 1.2 Coding rules

Reuse existing code; prefer a small additive modification to the boombness / causality framework over
new machinery, and reuse `external_repos/interp-jailbreak` where it provides better patching practice.
**Do not rewrite old intervention classes whose semantics are needed to reproduce committed artifacts —
add new classes/modes instead.** Every important bug fix ships with a regression test that demonstrably
fails under the pre-fix behaviour; mutation-test critical guards where practical. **Do not duplicate
formulas inside tests** — import and test the real implementation.

### 1.3 Testing rules

Environment: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`. Login-shell
`python` has no torch; its failures are not repo failures. At the start run `check_all.py` and the full
`pytest tests/`. The inherited state — `check_all` green, **721 passed / 18 failed / 7 skipped** — is
**not** an acceptable "all green": fix or explicitly classify the 18 before building a large new stack,
and **take the 12 artifact-regeneration failures seriously** rather than dismissing them as environment
noise. For commits: always `check_all.py`, always the science-critical fast subset, the full relevant
suite before every milestone and during the 4-hour reviews. **Do not use `--no-verify`.**

### 1.4 Git rules

This branch has had an unexplained concurrent writer. Before every commit run `git status`,
`git log -n 5 --oneline`, `git diff`. **Stage explicit paths; never `git add -A`.** Do not overwrite
another session's work; if HEAD moves unexpectedly, inspect and reconcile before continuing. Commit and
push after meaningful progress — logical milestones, not one giant commit at the end.

### 1.5 Artifact rules

**No important number may exist only in markdown.** For every result save: producing script, compact
JSON artifact, exact input/run paths, model, bank, pool, intervention spec, judge config, estimator,
cluster definition, seed, git SHA, timestamp, DONE marker. `outputs/` is gitignored, so **also create a
tracked compact result manifest for every paper-level result** — small JSON summaries, hashes, producing
paths and commands, never huge tensors. This explicitly fixes the situation where **R-W and R-AC can
only be reconstructed by reverse-engineering prose.**

### 1.6 SLURM rules

GPU-heavy work runs through SLURM, never the login node. Use the known-working account/partition; do not
repeatedly probe inaccessible partitions. Keep **≈ 6 or fewer independent GPU runs in flight**. Use CPU
nodes for statistical analysis, artifact audits, prompt generation, API judging, null simulations and
report generation. Parallelise genuinely independent work; do not parallelise where a later arm depends
on an earlier gate. **Record every job id and final status; FAILED/CANCELLED jobs stay visible in this
log.**

### 1.7 Dataset / split rules

Maintain family-disjoint dev/heldout splits; never reintroduce the sibling-family leakage that
invalidated G2. Do not optimise on heldout prompts. For every new bank audit explicitly: rows, family
ids, split overlap, demonstration-pool hash, prompt ids, template identities, token alignment, codeword
occurrence alignment, demo-span alignment, grammar, tokenizer behaviour on **both** models. Use at least
the existing scale; do not interpret tiny samples as final results.

---

## 2. PHASE 0 — REPAIR THE EVIDENCE PIPELINE BEFORE NEW SCIENCE

### 2.1 Reproduce the current headline

Recompute the current cross-bank result from its **raw** artifacts via an **independent** analysis path
— not by calling the existing summary writer. Confirm population membership, pool hashes, the cluster
counts, the aggregation, model-specific values, calibrated intervals, the sign-flip statistic, the
count-permutation statistic and the both-EOS control. **Given C-18, the object to reproduce is the
C-17/C-18 position** (direction supported; marginals include zero), not R-BD. Save the re-derivation as
a tracked compact artifact.

### 2.2 Fix known live artifact defects

*(Several of these were fixed by the peer session's C-18 code closure at 00:12 — verify each before
re-fixing, and do not duplicate.)*

* **Crossbank summary overwrite** — `summary.json` keys omitted the model, so Llama silently overwrote
  Qwen3. Schema must carry an explicit model dimension. Regression test with two models and
  deliberately different values.
* **`n_independent_pools`** — must count distinct demonstration-pool identities/hashes, not bank names.
  Test with several banks sharing one pool.
* **Strict bank generation** — validation must happen **before** the bank is available as an output.
  `--strict` must not leave a violating bank consumable merely because the file exists: write to a
  temporary path and rename only after validation. Regression test reproducing the `arrow` failure.
* **Misleading metric names** — no more `uniq_frac` for distinct completion *lengths*, `delta_pooled`
  for a mean-*score* delta, bare `dose` without naming the norm/variance/residual quantity, or
  `spearman` for Pearson-on-log2. Keep backward compatibility for old artifacts; **new artifacts must be
  unambiguous.**
* **Judge provenance** — build a mode where the judge model is selected and pre-flighted **before** the
  session, frozen for it, and persisted along with the raw judge response, prompt/completion hashes;
  where the same completion is not needlessly re-judged; and where a partial backend failure cannot
  silently turn one session into a mixed-model judge. **Do not rewrite historical artifacts.**
* **Incomplete run directories** — identify the three `crossbank_knockout_test` dirs without
  `DONE.json`; either complete them or mark them excluded in a **machine-readable** manifest so no
  glob-based analysis ingests them.

### 2.3 Fix the real failing tests

Run the full suite in the correct environment and separate genuine repo failures from
environment-dependent ones. **If a committed recipe no longer reproduces its committed artifact, fix the
recipe or explicitly version the artifact. Do not weaken tests to obtain green.**

### 🚦 PHASE-0 EXIT GATE

No large GPU matrix until: `check_all.py` passes; science-critical tests pass; genuine full-suite
failures are repaired or classified; crossbank summary overwrite fixed; pool counting fixed; strict
generation safe; judge backend provenance fixed for new runs; and the current headline independently
reproduces. **Commit and push this state.**

---

## 3. PHASE 1 — ISOLATE WHAT THE DEMONSTRATION KNOCKOUT IS ACTUALLY DOING

**Core question.** Does the causal effect come from (1) generated response tokens retrieving from the
demonstrations, (2) the final query representation retrieving during prefill, (3) corruption of the
demonstrations' own representations, or (4) some combination?

### 3.1 Scoped attention-knockout semantics

Add an **additive** implementation that independently controls:

| mode | prefill behaviour | decode behaviour |
|---|---|---|
| **`query_prefill_only`** | only the final user/query span is blocked from attending to demo keys; demo tokens process normally | unmodified |
| **`decode_only`** | unmodified | generated-token query rows blocked from demo keys |
| **`response_query_only`** | final query span blocked | all generated query rows blocked — demo-token processing untouched. **The cleanest test of "the response computation needs access to the demonstrations."** |
| **`demo_processing_only`** | query rows *inside* the demonstration block blocked from demo keys; final-query/decode access left intact where possible | unmodified |
| **`legacy_all_query`** | the existing `AllQueryAttentionKnockout` semantics, unchanged | unchanged — the bridge to the previous result |

**Document explicitly:** `decode_only` **cannot** affect the logits used to sample the first generated
token if those logits come from the final prefill query state.

### 3.2 Required synthetic tests

Small deterministic synthetic-attention tests proving, per mode: exactly which query rows are edited;
exactly which key positions; prefill behaviour; cached-decode behaviour; first-token behaviour;
multi-token behaviour; different prompt and demo lengths; **no `kp`/`past` coordinate confusion**; no
modification outside selected layers; none outside selected heads. **Mutation-test the span resolver and
the decode liveness condition — the old failure mode must turn the regression test red.**

### 3.3 First smoke

≈ 8 rows per model. Do not judge scientific effect. Check: 100 % of intended rows hit the hook; expected
prefill/decode counters; generations actually change; no crashes; no pathological collapse; **no
all-layer experiment.** If the hook does not fire exactly as designed, fix it before continuing.

---

## 4. PHASE 1 FULL EXPERIMENT — SAME-SESSION DECOMPOSITION

Canonical **96-row** behavioural population, both models, the already-supported causal bands
(**Llama L6–14**, **Qwen3 depth-matched L7–17**). **Do not retune these based on new outcomes.**

**Arms (minimum):** `A_baseline` · `C_legacy_full_scope` · `C_response_query_only` ·
`C_query_prefill_only` · `C_decode_only` · `C_demo_processing_only` · `D_response_query_late_control`.

Plus **same-band non-demo-key controls**: mask approximately the same number of key positions outside
the demo block, using **≥ 3 seeded deterministic draws** rather than one random lottery; protect
special/query-critical regions from accidental masking; **persist the exact positions used per row.**

**4.1 Judge all directly comparable arms in ONE session** with one fixed, pre-flighted backend. Do not
compare a new arm against an arm judged in an old session. Report **mean StrongReject score** and
**binary ASR@0.5**; pre-register 0.25 / 0.50 / 0.75 sensitivity as secondary.

**4.2 Generation-health metrics per arm:** median/mean characters; truncation rate; EOS termination
rate; refusal rate; **number of unique completion texts**; **number of distinct completion lengths as a
separately named metric**; empty/near-empty fraction; generation-change rate vs baseline. **A reduction
in judged ASR is not behavioural suppression if it is another output-length collapse.**

**4.3 Pre-register interpretation categories** with an equivalence margin fixed *before* judging, using
the known within-session reproducibility (≈ 2–3 prompts of 96) as the reference:

* **Outcome A** — `response_query_only` ≈ legacy while `demo_processing_only` is weak → strong evidence
  the causal path is **response/query access to demonstration information**.
* **Outcome B** — `demo_processing_only` carries most of it → **retract/reframe** the "generated answer
  retrieval" wording; the result becomes *disrupting the demonstrations' internal representation
  suppresses the attack*. Still scientifically interesting.
* **Outcome C** — `query_prefill_only` dominates, `decode_only` small → the retrieval event occurs
  largely while constructing the final query state before generation.
* **Outcome D** — `decode_only` remains large → genuinely ongoing retrieval during autoregressive
  generation.
* **Outcome E** — legacy strong but **every** cleanly scoped arm weak → the legacy effect depends on
  interacting disruptions across prompt and response computation. **State that directly; do not average
  the scoped arms into a preferred story.**

---

## 5. PHASE 2 — BRIDGE THE BEHAVIOURAL RESULT TO SEMANTIC BINDING

The causal result shows behaviour changes when demo attention is blocked. It does **not** show what
semantic information was lost. `goal_topicality` is invalid here (successful Doublespeak outputs keep
speaking in the codeword and never use the target word) — **do not reuse it as the primary instrument.**

**5.1 Matched semantic binding probe.** For every behavioural family, a probe using the **same
demonstration block and same mapping**, e.g. *"In the code used above, what does `<codeword>` mean?
Answer with one word."* Measure recovery of the intended mapped concept with deterministic/model-native
measurements: exact one-word accuracy; probability/logit margin of the intended concept against
appropriate alternatives; forced-choice accuracy. **Do not fit a new arbitrary hidden-state direction
for this primary probe** — use the observable mapping output first.

**5.2 Run the causal intervention on the probe:** baseline · validated `response_query_only` ·
late-layer matched control · same-band non-demo controls, on the same families.
*Does the intervention that suppresses behavioural attack success also destroy recovery of the
codeword→concept mapping?* **This is the first direct bridge we need.**

**5.3 Cross-condition specificity** across the 2×2 conditions (A natural doublespeak · B benign literal ·
C direct harmful · E concept in benign context): is semantic mapping selectively affected where
demonstrations matter? does general benign instruction-following collapse? does direct-harmful
refusal/compliance change? is the intervention simply damaging generation? **Essential, because the
late-layer control alone does not rule out "masking a large prompt region mid-model generically hurts
in-context computation."**

---

## 6. PHASE 2B — CHARACTERISE WHAT THE SUPPRESSED COMPLETIONS BECOME

Build a **completion phenotype instrument**; do not use it as the primary causal estimator until its
reliability is measured. Mutually exclusive categories: (1) mapped/codeword compliance; (2) literal
codeword interpretation; (3) explicit refusal/safety response; (4) garbled/incomplete/truncated
non-answer; (5) other coherent response.

**Blind the evaluator to the arm.** Persist evaluator backend, prompt/version, raw output, parsed
category, completion hash. Use ≥ 2 independent views where practical (structured semantic classifier;
deterministic lexical/termination/refusal metrics) and **measure agreement — do not hide disagreement.**

> **When the attack disappears, did the model lose the mapping, refuse, become literal, or simply
> destabilise?** This is currently unknown and should become known.

---

## 7. PHASE 2C — REBUILD THE TEXT-DELETION CONTROL CORRECTLY

The old ceiling was invalid: the supposedly 96-row arm collapsed to essentially one prompt. Build a
**row-specific** demo-deletion transformation that preserves each row's query and row identity, removes
only the intended demonstrations, preserves the rest of the prompt structure, **verifies diversity by
text hash rather than length**, requires many distinct transformed prompts, saves transformed prompt
hashes, and **fails if accidental duplication exceeds a pre-registered threshold.**

Only after the transformation is proven correct, compare: demonstration text deletion · response-query
attention knockout · late control · same-band non-demo mask. **Do not call deletion a "ceiling" until it
is genuinely row-wise.**

---

## 8. PHASE 3 — CAUSAL RESCUE: CONNECT INTERNAL STATE TO BEHAVIOUR

Do not start by inventing another scalar. Ask the stronger question: **if the retrieval knockout
destroys a necessary internal state, can we restore that state and rescue the semantic mapping or
behaviour?** Use surgical activation-patching practice from the existing project and the local
`interp-jailbreak` code.

**8.1 Clean vs corrupted paired runs** on the exact same row (CLEAN = baseline, CORRUPTED = validated
retrieval knockout). Cache activations at: the final query token/span during prefill; band exit;
immediately after the causal band; attention output; residual stream. **Do not begin with hundreds of
heads — the previous data say the mechanism is distributed.**

**8.2 Full-state rescue first.** At a pre-registered boundary such as band exit, patch the CLEAN
residual state at the final query position into the CORRUPTED run. Primary target: **semantic binding
probe**. Secondary: behavioural generation. Controls: mismatched-family clean activation; clean
activation from a late/inert layer where dimensions allow; random-row activation; norm/energy-matched
perturbation. **A huge full-residual transplant is not direction specificity** — its only purpose is to
prove the lost causal information is recoverable at this state.

**8.3 Retrieval-effect subspace — only after full-state rescue succeeds.** Build the paired
intervention-effect matrix on **dev** only: `Δh = h_clean − h_knockout` at the pre-registered
state/layer. **Do not fit to StrongReject labels** — the basis comes from the causal perturbation, not
from attack outcomes. PCA/SVD or equivalent. Before looking at heldout behaviour, record the singular
spectrum, split-half stability, an isotropic/random-subspace null, and a **predeclared train-only
rank-selection rule** (not many ranks tried on heldout ASR).

**8.4 Low-rank add-back test** on heldout families: start from the knockout run, add back only the
clean-minus-knockout component **inside the learned subspace**, measure semantic recovery, then
behavioural rescue. Use **equal-rank random subspaces** and match the actual intervention energy.
Report semantic recovery, behavioural recovery, and **fraction of full-state rescue recovered**.

* **Low-rank rescue succeeds** → a major result: a compact state that is demonstration-induced, causally
  necessary and behaviourally relevant. *Only then* does it become a candidate optimization handle.
* **Full-state succeeds, low-rank fails** → also strong: the behaviourally necessary retrieval state is
  high-dimensional/distributed, consistent with the observed layer/head redundancy.
* **Even full-state fails** → the relevant information lives elsewhere, or generated-token dynamics
  dominate, or the intervention changes a distributed trajectory that cannot be repaired at one
  boundary. **Do not force a direction.**

---

## 9. PHASE 4 — ADD THE FOURTH INDEPENDENT DEMONSTRATION POOL

The magnitude claim is thin on Llama and — after C-18 — has **no surviving calibrated cluster test at
all**. The `club` corpus already exists and is audited. This is the obvious confirmatory increment, run
as a **frozen confirmatory analysis, not another adaptive statistics search**.

**9.1 Freeze the analysis before running club**, using only existing data: primary estimand; the
aggregation unit **(and, per C-18, whether it is a marginal or a crossed table)**; model handling; CI
procedure; count-permutation statistic; threshold; both-EOS control; leave-one-pool-out;
leave-one-model-out; model-specific analyses. **Persist this configuration before any club outcome is
inspected, and do not compute a favourable subset when the first arm arrives.**

**9.2 Run both existing club banks** rather than making new lexical material, using the validated scoped
intervention from Phase 1; optionally the legacy arm as a bridge, but it must not replace the cleaner
intervention. Both models if compute permits. **Two banks sharing the club pool do not create two
independent pools — the count becomes 4 pools, not 4 + banks.**

**9.3 Primary questions.** Does the pool-level interval remain below zero with a fourth pool? Does it
survive leave-one-pool-out? What happens to Llama alone? Does Qwen3 continue carrying it? Do
positive-delta churn cells continue to align with truncation/non-termination? Does the scoped
intervention produce a more stable result than the legacy one? **Accept the result even if Llama remains
null; do not keep adding pools until p crosses a preferred threshold.**

---

## 10. PHASE 5 — BUILD THE JOINT CROSSED BANK

The current crossed geometry pools **independently generated and fitted** banks, leaving a bank/pair
nuisance term. Build **one jointly generated crossed bank.**

**Factors.** Codewords: four existing audited consonant-initial codewords that avoid article-grammar
problems, tokenize cleanly and align on both tokenizers — **do not introduce a new codeword for
novelty.** Concepts: the established four — `bomb`, `knife`, `gun`, `club`. **Do not use `arrow`;
do not repeat the `a arrow` / `a apple` failure.**

**Joint design requirement.** All codeword × concept combinations generated from a **common
template/family universe**, with the base family identifiable independently of the lexical assignment,
and each pair's 2×2 cells preserved (natural doublespeak · benign literal · direct harmful · concept in
benign context). The purpose is to make codeword/concept variation the **controlled factor** rather than
*"which separately generated bank did this come from?"*

**Strict acceptance criteria before any geometry is fitted:** zero prompt-family violations; zero grammar
violations; zero ambiguous target occurrences; zero demo-span ambiguity; clean tokenizer audit;
base-family alignment across all pair combinations; family-disjoint train/dev/heldout; sufficient rows
per cell; model-specific tokenization report for **both** models. **The generator must abort before a
violating bank becomes available.**

---

## 11. PHASE 5B — REPLICATE THE GEOMETRY ON LLAMA *AND* QWEN3

The current decomposition is Llama-only. **11.1** Pre-register normalised-depth analysis layers — do not
select Qwen3 layers after seeing which look most similar; fit all layers if cheap but distinguish
pre-registered primary depths from exploratory plots. **11.2** Compute split-half ceilings first for
every factor/subspace (dev fit, heldout fit, similarity, null) — no cross-factor statement is meaningful
without the measurement ceiling. **11.3** Use a proper factor decomposition with **orthonormal bases**;
do not repeat tables that mix projection fractions, raw norms and nested terms and *look* like a variance
partition without being one; state whether terms are orthogonal, nested or overlapping, and **do not make
them sum to 1 unless they mathematically partition.**

**11.4 Main questions.** Is the concept representation codeword-invariant on the joint bank? Does the
four-concept representation remain plane-dominated with non-zero third-direction structure? Does Qwen3
show the same structure? Is the codeword side genuinely a (K−1)-dimensional factor subspace? Does the
interaction remain small under a joint design? At what depths does factor separation emerge? Isotropic
nulls fixed before observed structure is interpreted. **This can be a valuable representational result
even if it stays behaviourally non-causal — do not quietly reconnect it to ASR without a causal bridge.**

---

## 12. PHASE 6 — QWEN3 REPLICATION OF RETRIEVAL × REFUSAL

The Llama 2×2 suggested retrieval and refusal are separate channels; that has not been cleanly
replicated on Qwen3. **Do not reuse a Llama refusal direction in Qwen3.**

**12.1** Build/validate a Qwen3-specific refusal intervention with the existing refusal-direction
machinery. Choose the primary candidate layer(s) **before** evaluating the doublespeak interaction; a
depth-matched layer should be considered. The existing Qwen3 refusal directions at L20/L25/L28 are
secondary references — do not force them into an interaction merely because they exist. Validate on
heldout harmful/benign data: does projection actually change refusal behaviour? does it avoid
pathological benign degradation? does the intervention fire? is the effect measurable?

**12.2 Identifiability gate.** If refusal removal has essentially no measurable effect on the chosen
Qwen3 population, a retrieval × refusal interaction **is not identifiable there**. **Do not claim
"independence" from two inert cells** — record *refusal interaction unidentifiable on this population.*
If there is headroom, run one same-session 2×2 (baseline · retrieval knockout · refusal · both) using
the **validated scoped** retrieval intervention, comparing aggregate effects only.

---

## 13. PHASE 7 — OBJECTIVE REOPEN GATE

**There is currently no justified GCG/MAC objective. That is a scientific result, not an unfinished
task.** The track reopens only if a new candidate — most plausibly the Phase-3 retrieval-effect subspace
— passes all six gates:

* **O1 Measurement** — reproducible across split halves; not dominated by measurement noise; **not simply
  `n_examples`, completion length, or refusal score.**
* **O2 Prediction** — on heldout data predicts semantic mapping, behavioural vulnerability, or causal
  knockout sensitivity, **after conditioning on demonstration count, bank, domain and pool.**
* **O3 Causality** — a direct intervention on the candidate changes the relevant quantity, with
  energy/dose-matched controls; **random directions/subspaces must be allowed to fail.**
* **O4 Specificity** — beats matched random/equal-rank controls, **not merely by removing more residual
  energy.**
* **O5 Transfer** — the sign/role must be coherent on both models. The vector need not transfer across
  hidden dimensions, but the mechanism cannot mean *"ascend on Llama and descend on Qwen3."*
* **O6 Optimization direction** — a clear scalar loss whose causal meaning is supported, which does not
  reproduce length collapse, the refusal lottery, the attention-mass reversal, or dose-only behaviour.

---

## 14. ONLY IF ALL OBJECTIVE GATES PASS — GCG/MAC

If any gate fails, **Phase 7 remains BLOCKED and GCG/MAC is not implemented.** If all pass: reuse the
existing GCG/MAC implementation from the article/local repos; minimise new code; optimise only on
dev/train families; **freeze the suffix before heldout evaluation**; compare against the standard
GCG/MAC objective, a random equal-rank subspace, `d_surface`, attention mass and a refusal objective;
evaluate transfer across heldout families, codewords, concepts, pools and models where dimensionally
possible; record ASR, semantic mapping, refusal, generation length, truncation and objective value; and
**explicitly test whether optimization merely collapses generation.**

> The goal is to **discover** a mechanism-derived optimization target, not to manufacture one.
> *"The causal mechanism is distributed and does not admit a useful low-dimensional optimization
> handle"* is a valid and potentially stronger paper result.

---

## 15. LATER GENERALIZATION — ONLY AFTER THE MECHANISM IS CLEAN

**Third model family** — only if the repo already supports one with reasonable attack headroom; use a
headroom gate before interpreting a null; **do not tune the causal band by looking at ASR** — use
depth-normalised pre-registration. **Quantized variant** — if already supported, test whether the causal
retrieval effect survives quantization. Both are **secondary** generalization results.

---

## 16. THINGS NOT TO DO IN THIS SPRINT

Do not: rescue `d_surface` · call it "bombness" · build GCG from `d_surface` · build GCG from raw
attention mass · run another huge single-head sweep · infer a layer law from 1–3 prompt differences ·
treat all-layer knockout as clean evidence · use `C_all` as "100 % suppression" · use the old
text-deletion arm as a population ceiling · use `goal_topicality` as evidence the mapping was lost ·
use `arrow` · add new lexical concepts before exhausting the audited set · use a single random control
at large magnitude · call model/bank replicates independent when they share pools or prompts · report
uncalibrated small-k percentile bootstrap intervals as definitive · round a CI across zero · say "all
tests pass" when only `check_all.py` passes · persist a statistical function that is never called ·
leave a headline number only in markdown · interpret an intervention without liveness proof · hide
failed or cancelled jobs.

---

## 17. REVIEW PROTOCOL

Use subagents aggressively for independent tracks: intervention semantics + synthetic tests · statistics
audit · judge/provenance repair · prompt-bank validation · artifact/reproducibility audit · independent
adversarial reviewer. **Do not use multiple agents to change the same files without coordination.**

For each major result, run an adversarial reviewer instructed approximately:

> *Try to prove this claim wrong. Recompute it from the raw artifact. Check population identity,
> intervention liveness, model/pool independence, estimator definition, judge provenance, truncation,
> alternative controls, and whether the statistic is saturated or misnamed. Default to refuting the
> proposed interpretation.*

Do this **before** promoting a result to the LIVE CLAIMS LEDGER. If the reviewer overturns it: append a
correction, do not rewrite history, mark the previous claim superseded/retracted, update the ledger.

---

## 18. 30-MINUTE / 4-HOUR WORK LOOP

**Every ≈ 30 minutes:** inspect running jobs; inspect failed jobs; check whether a gate has resolved;
update this file; commit/push meaningful completed progress; queue only experiments still justified by
current evidence.

**Every ≈ 4 hours, a deeper code + output review:** inspect git diff/history · run `check_all.py` · run
the relevant/full test suite · inspect recent raw outputs manually · independently recompute current
headline numbers · check liveness fields · check pool/model/bank provenance · check for silent
overwrites · check judge-session consistency · check whether any claimed p is actually sign-only · check
truncation/EOS · check whether structure is being fitted below the reproducibility floor · update the
LIVE CLAIMS LEDGER · document corrections immediately. **Continue after the review; do not stop because
one experiment completed.**

---

## 19. REQUIRED FINAL DELIVERABLES

**A. Live research log** — this file, with the full chronological record.
**B. A clean sprint summary** — a new report covering only this phase, understandable with no session
context, structured like the Part-II summary: starting state · plan · exact experiments · where we won ·
where we failed · corrections · final claims · limitations · canonical artifacts · reproduction.
**C. Research handoff** — create/update `RESEARCH_HANDOFF.md`: exact current scientific truth ·
strongest result · retracted claims that must not be revived · open items · next decisive experiment ·
artifact paths · current HEAD.
**D. Paper-level claim table** — per surviving claim: claim text · model(s) · population · n ·
independence unit · effect size · interval/test · intervention · control · artifact · code · status
(exploratory / replicated / confirmatory / retracted / unresolved).
**E. Reproduction manifest** — every paper-level result has **one command/script path** that regenerates
its compact analysis artifact from raw data. **No important result should require reconstructing a
method from prose.**

---

## 20. WHAT SUCCESS LOOKS LIKE

Success is **not** "GCG works". This sprint succeeds if these are answered cleanly:

1. Is the demonstration-knockout effect genuinely caused by **response-query retrieval**, or partly by
   corrupting the demonstrations during prefill?
2. When the knockout suppresses the attack, **what changes** — codeword mapping, literal interpretation,
   refusal, generation quality, or something else?
3. Can the lost information be **causally rescued** by activation patching?
4. If full-state rescue works, is the behaviourally relevant information **low-rank or irreducibly
   distributed**?
5. Does the mechanism survive a **fourth independent demonstration pool**, especially on Llama?
6. Does the codeword/concept factorization replicate on **Qwen3** in a properly joint crossed design?
7. Does the Llama retrieval/refusal independence result replicate on Qwen3, or is it model-specific?
8. Only if the causal retrieval state becomes a stable, specific, transferable low-dimensional handle:
   can it become a legitimate GCG/MAC objective?

The ideal contribution is no longer *"we found a bombness direction"* — that hypothesis is closed. The
more interesting possible contribution is:

> **Doublespeak constructs a robust semantic remapping representation, but that representation alone is
> not behaviourally causal. The attack instead depends on a distributed, mid-stack demonstration-retrieval
> process. Removing response access to the demonstrations suppresses behaviour across model families; the
> next mechanistic question is whether the lost distributed state can be causally restored and compressed
> into a behaviourally meaningful representation.**

**Test that claim aggressively. Do not protect it.** If the response-only knockout fails, say so. If the
semantic binding survives while behaviour disappears, that is extremely important. If full-state patching
restores mapping but not behaviour, that is extremely important. If low-rank rescue fails, that is
extremely important. **The goal is to add a real causal result to the paper, not to preserve the story we
started with.**

---
---

# PART B — LIVE PROGRESS LOG *(append-oriented, newest first within each section)*

## B1. PRE-REGISTRATIONS

*(Each entry is fixed before the corresponding result exists and is never edited afterwards; a
superseded pre-registration gets a new entry that says so.)*

### 🔒 PR-2 (02:45) — **PHASE 2: which probe rows carry the headline.** Fixed before the probe is run against any model, and before Phase 1 has resolved.

**The instrument is SELECTION, not synthesis** — and that is a finding about the bank, not a
convenience. `src/boombness/semantic_binding_probe.py` constructs no prompt text at all. The bank
already carries the plan-§5.1 probe:

| query_kind | rows |
|---|---|
| `behavioral` | 1152 |
| `semantic_one_word` | 1008 |
| `semantic_forced_choice` | 288 |
| `comprehension_usage` | 288 |

**Verified independently by me** (after first getting it wrong — see the note below): joining on
`(family_id minus its trailing query_kind field, condition)`, all **1584** probe rows pair **1:1** with
a behavioural row — **0 orphans, 0 duplicate behavioural keys, and the `demo_block` is BYTE-IDENTICAL
across the pair in 1584 / 1584 cases.** So the probe asks about *the same demonstrations the
behavioural row uses*, which is the whole point: the same mask can be applied to both and compared.
Synthesising prompts would have broken the bank's `prompt_sha16` / `bank_rows_sha16` provenance chain,
required its own tokenization audit, and produced a demo block that is **not** the behavioural row's.

#### 📌 PRE-REGISTERED, before any probe run

1. **The headline group is `probe_tests_binding = True` on `natural_doublespeak`.**
   **240 of the 1008** `semantic_one_word` rows (cells B and E, `query_surface == "concept"`) ask about
   the **concept word itself**, so `target_surface == target_semantic` and **no codeword→concept
   binding is tested at all**. They are not a weaker version of the measure — they are a different
   measure.
2. **The `probe_tests_binding = False` rows are the CONTROL**, and their role is fixed now: they answer
   *"did the intervention simply break generic in-context readout?"* — plan §5.3's specificity question.
   An intervention that destroys binding **and** destroys the concept-itself readout has not
   demonstrated anything about binding.
3. **The 156 probe rows with an empty `demo_block`** (`n_examples = 0`) are **excluded**, consistent
   with the behavioural population, which excludes `n_examples = 0` as structurally ineligible (R-B).
   A probe with no demonstrations cannot test retrieval from demonstrations.
4. **These three groups are never averaged together.** `summarize()` refuses to, and the artifact flags
   each row.

⚠ **Recorded against myself:** my first independent check of the 1:1 join reported **168/1584** matched
demo blocks and 6 duplicate keys, and I nearly filed it as a correction against the agent. **My check
was the broken one** — `family_id` is **pipe**-delimited (`farm_storage|dev|slot0|…|behavioral`) and I
split on `_`, so my stem function returned `None` for all 2736 rows and collapsed every key. The agent
used `rpartition("|")` and was right. **The lesson is the one this project keeps relearning: a
disagreement between two computations locates a bug, but says nothing about which side holds it.**

---

### 🔒 PR-1 (00:58) — **PHASE 1: the same-session scoped decomposition.** Written before any scoped arm exists, before any code for it is merged, and before any judging.

**Primary estimand.** Paired ASR@0.5 delta against the *same-session* baseline `A`, on the canonical
96-row behavioural population, per model. **Paired**, because the inherited judge-reliability finding
(same generations re-judged: identical binary label on only **78/96** rows) means only paired
aggregates are stable.

**Primary comparison.** `C_response_query_only` versus `C_legacy_full_scope`. Everything else in the
arm list exists to interpret that one contrast.

**Unit of independence.** The **domain** (k = 6). Not the prompt (the 96 slots are one shared design —
R-1), not the bank, not the model. The attainable two-sided sign-flip floor at 6 informative domains is
`2/2⁶ = 0.03125`, and **any p at or near that floor is reported as a sign test, with the floor quoted
beside it**. The magnitude and its calibrated interval are the quotable quantities.

**THE EQUIVALENCE MARGIN, fixed now.** Two arms are called **equivalent** when
`|Δ_arm1 − Δ_arm2| ≤ 0.03125`, i.e. **3 prompts of 96**. Justification, in advance: the previous
phase's own within-session re-measurement spread on identical arms was **2–3 prompts of 96**
(prev-C-10's table: `L7–9` −0.0208 → −0.0625; `L10–12` −0.0312 → −0.0625), and prev-R-BE's cross-session
judge drift is ~1 row. **A difference smaller than 3 prompts is below this instrument's demonstrated
reproducibility and will not be interpreted, in either direction.** An arm is called **weak** when
`|Δ| ≤ 0.03125` and **large** when it reaches ≥ 50 % of the legacy arm's Δ in the same session.

**Expected outcomes and what each would mean** — the plan's Outcomes A–E, with the margin applied:

| outcome | pattern | reading |
|---|---|---|
| **A** | `response_query_only` ≈ legacy (within margin) **and** `demo_processing_only` weak | the causal path is **response/query access to the demonstrations**. The strongest available result, and the one that would license the wording the project has been using loosely |
| **B** | `demo_processing_only` large, `response_query_only` weak | ⛔ **retract the "generated answer retrieval" wording.** The result becomes *disrupting the demonstrations' own encoding suppresses the attack* — still publishable, differently worded |
| **C** | `query_prefill_only` large, `decode_only` weak | the retrieval event is concentrated in constructing the final query state **before** generation |
| **D** | `decode_only` large | genuinely ongoing retrieval **during** autoregressive generation |
| **E** | legacy large, **every** scoped arm weak | the legacy effect needs interacting disruption across prompt **and** response computation. **State it directly; do not average the scoped arms into a preferred story** |

**Falsifier for the phase's headline hypothesis.** The chain
*demonstrations → response-time retrieval → behaviour* is **falsified** if `response_query_only` is
weak (|Δ| ≤ 0.03125) while the legacy arm is large **on both models**. That is Outcome B or E and it
will be reported as a falsification, not as a scoping caveat.

**Stopping rule.** One 7-arm session per model. **No arm is added after seeing a number.** If a mode's
liveness gate fails, that arm is **VOID** and is re-run after the hook is fixed — it is never reported
with a caveat.

**Secondary analyses allowed** (declared now, so nothing is added later): thresholds 0.25 / 0.75;
per-domain deltas; refusal rate; the generation-health block in §4.2 of the plan; and the
`n_examples` monotonicity check that prev-R-AI ran. **Not allowed:** per-prompt "the same prompts
flipped" claims, any leave-one-out that was not declared here, and any re-clustering after seeing the
result.

#### ⚠ Two design blockers established BEFORE implementation, both from the adversarial review

**(1) The liveness gate will refuse two of the five modes by construction.**
`assert_knockout_live` requires `frac_rows_decode_live ≥ 0.99` (`KNOCKOUT_MIN_LIVE_FRAC`). But
`query_prefill_only` and `demo_processing_only` **make no decode edits at all** — that is their
definition. Left as-is the gate would either abort them or, worse, they would be reported as clean
nulls from a hook that never fired at decode because it was never supposed to. **Resolution, fixed
now:** liveness becomes **mode-aware** — each mode declares which counter is its proof
(`prefill_edits > 0` for the prefill-scoped modes, `decode_edits > 0` for the decode-scoped ones, both
for `response_query_only` and `legacy_all_query`) and the gate asserts *that* counter. **A mode whose
declared counter is zero is VOID.** The gate must not be loosened to "either counter", which would let
a genuinely dead decode hook pass on its prefill edits.

**(2) `decode_only` cannot affect the first generated token.** Verified, not assumed: the prefill mask
is unmodified and decoding is greedy (`do_sample=False`), so token 1 comes from the final prefill query
state and is **bit-identical to baseline** by construction. **Consequence for interpretation:** a small
`decode_only` effect is *not* evidence that decode-time retrieval is unimportant if the behavioural
fork is decided at token 1. ⚠ The review also measured that the fork is **not** normally at token 1 on
this population (median `n_new_tokens` = 117.5, min 29, **fraction with ≤ 3 new tokens = 0.000**), so
the confound is real but is not the typical case. **Both facts go in the write-up; neither is used to
explain away a null.**

**Pre-registered instrument check, before any scientific arm.** The 8-row smoke must show, per mode:
the intended query rows edited and no others; the intended key positions and no others; the declared
liveness counter non-zero on **100 %** of rows; generations changed versus baseline; and
`legacy_all_query` **byte-identical** to today's behaviour. **If any of these fails the arm does not
run.**

## B2. DECISIONS

**D-1 (00:30) — the starting truth is `059e819f`, not `8c83c8f3`, and the plan's §0 magnitude paragraph
is amended on arrival.** The plan was written against the audited state `8c83c8f3` and quotes R-BD's
k=18 CI as the current magnitude claim. HEAD had already moved three commits, the last of which
(**C-18 / REVIEW-8**, 23:52) **retracts R-BD**: all ten populations share the identical 96 `prompt_id`s,
so `pool × domain` k=18 is a crossed 3×6 table in which 62.1 % of the spread is two main effects counted
3× and 6× over; both marginals include zero. Amending the plan's own starting state is *within* the
plan's instruction to "inspect the current HEAD first in case more work has landed", and the amendment
**does not change a single phase** — it strengthens Phase 4, which is now confirmatory on an open
question rather than on a settled one. Recorded here rather than silently editing Part A §0.

**D-2 (00:30) — file and code ownership is split with the peer session, in writing.** ⛔ **CORRECTED at
00:41 — the split I proposed was addressed to the wrong owner.** I messaged the peer session
(`BOOMBNESS_D_SURFACE_FOLLOWUP implementation`) proposing that it keep
`external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md`,
`src/boombness/crossbank_knockout_test.py` and jobs 779083–779086. **It replied that it owns none of
them**: its log is `external_md/BOOMBNESS_D_SURFACE_FOLLOWUP_PROGRESS.md` (a *different* file —
`D_SURFACE_FOLLOWUP`, not `DSURFACE_NEXT_PHASE`), its only job was **776368** on `cpu-killable`, and it
has stopped entirely and released everything. **See P-1.** Corrected split: **this session owns
everything in the boombness line**, and no path is frozen on the peer's behalf. **No `scancel` by this
session under any circumstance** — that part stands regardless of ownership.

**D-3 (00:42) — the 18 test failures are triaged before any GPU work, and the 12 provenance failures are
treated as real.** Baseline reproduced at `059e819f` with the project env:
**721 passed, 18 failed, 7 skipped in 154.26 s.** The split is exactly as the Part-II audit predicted:
**6** are `test_module_imports_without_torch` / `test_import_is_torch_free` assertions
(`test_candidate_pool`, `test_gpu_runner`, `test_phase_f_attention_probe`, `test_phase_f_probe_driver`,
`test_reinforce_mac`, `test_soft_prompt_reinforce`) and **12** are artifact-regeneration / provenance
assertions (`test_estimand` ×5, `test_g2_selection` ×6, `test_analyze_steering::test_T2_...` ×1).
Per §1.3 the second group is **not** environment noise and is not dismissed.

**D-4 (00:35) — ⚠ PHASE 4's AXIS IS WRONG, AND I AM FLAGGING IT TO THE USER RATHER THAN SILENTLY SWAPPING IT.**
Plan §9 says the next confirmatory increment is **a fourth demonstration pool** (`club`). Two findings
that landed *after* the plan was written say that cannot work:

* **prev-R-BE** (`7838dcd2`, inherited): all four axes the previous phase added — banks, pools, models,
  concepts — **reuse the same six domains**, and the sign-flip test clusters on domains, so its p-floor
  is `2/2⁶` *regardless of how many prompts, banks or pools each domain holds*. Phase 8 stated this in
  its own words before Phases 8/9/10/10b spent four banks, a third pool, a second model and a fourth
  concept on the wrong axis.
* **R-2** (this phase): pool is **perfectly confounded with concept** here, and the pooled direction is
  carried by a single corpus. A fourth pool adds a fourth concept, not a fourth independent replicate
  of the domain structure.

**The untried route is domains.** `src/boombness/demo_pools.py` holds its domain list in a module-level
`DOMAINS` dict (~line 60) and records it in `_meta.domains`, so regenerating pools at 8–10 domains and
rebuilding one bank per pool is an ordinary bank-generation job — no new machinery.
⚠ **Carry prev-R-BE's own caveat:** the projection holds mean and sd fixed while the effect is
concentrated (`game_manual` −0.2562 against a −0.0865 mean, `lab_safety` exactly 0.0000). **New domains
could be `lab_safety`-like, raising sd as they lower the mean. "8 domains" is optimistic, not
guaranteed.**

**Decision:** Phase 4 is **not started** and **not silently redefined**. It is downstream of Phases 1–3
anyway, so nothing is blocked by deferring it. The question for the user is whether Phase 4 becomes
*"add a fourth demonstration pool"* as written, *"regenerate pools at 8–10 domains"* per R-BE, or both.
**Phases 1, 2 and 3 are unaffected and proceed.**

**D-5 (00:52) — USER RULING ON D-4: do BOTH. Phase 4 keeps the fourth demonstration pool *and* gains a
domain-expansion arm.** Asked directly (D-4 laid out fourth-pool / more-domains / both); the answer was
**both**. So Phase 4 splits into two independently-reportable sub-phases, and the ordering matters
because they answer different questions:

* **4A — fourth pool (`club`), as plan §9 wrote it.** Confirmatory, frozen analysis, the `club` corpus
  already exists and is audited. It tests *"does the effect hold on a corpus it was not discovered
  on?"* — and after **R-2** that question is sharper than when the plan was written, because the
  pooled direction is currently carried by the bomb corpus alone (81/11) while knife (15/7, p = 0.134)
  and gun (17/12, p = 0.458) are null. **`club` is therefore a genuine test, not a formality: if it
  behaves like knife and gun, the honest claim becomes "the effect is a property of the bomb corpus".**
  ⚠ It adds **no** domain clusters, so it cannot move the k=6 marginal — that is not its job.
* **4B — regenerate pools at 8–10 domains, one bank per pool.** This is the axis prev-R-BE identifies
  as the binding one, and it is the only untried route to a domain marginal that could exclude zero.
  `src/boombness/demo_pools.py` holds `DOMAINS` at module level (~line 60) and records it in
  `_meta.domains`, so this is an ordinary bank-generation job with no new machinery.
  ⚠ Carry prev-R-BE's caveat verbatim: the 8-domain projection holds mean and sd fixed while the effect
  is **concentrated** (`game_manual` −0.2562 against a −0.0865 mean; `lab_safety` exactly 0.0000). New
  domains may be `lab_safety`-like and raise sd as they lower the mean. **Pre-register that the new
  domains are accepted or rejected on their audit, never on their effect size**, or 4B becomes a search
  for domains that help.

**Both remain downstream of Phases 1–3** and neither is started. The scoped-knockout decomposition
(Phase 1) is still the sprint's highest-priority experiment, because 4A and 4B both measure *an
intervention whose scope is not yet isolated* — running either before Phase 1 would spend a corpus and
a bank-generation cycle on the legacy arm.

## B3. EXPERIMENT STATUS BOARD

Legend: ⬜ not started · 🔬 running · ✅ complete · ⛔ failed/retracted · ⏸ blocked

| id | phase | experiment | status | gate |
|---|---|---|---|---|
| P0.1 | 0 | independent re-derivation of the cross-bank result from raw artifacts | ✅ **R-1** — reproduces prev-C-18 to the digit; **R-2** is new and amends the headline | — |
| P0.2a | 0 | prev-C-18 fixes pinned by regression tests + `require_done` on inputs + k=1 guard | ✅ done | — |
| P0.2b | 0 | atomic `--strict` bank write | ✅ done — validation now precedes the rename | — |
| P0.2c | 0 | judge backend pinning + per-row provenance | ✅ opt-in mode, default byte-identical | — |
| P0.2d | 0 | `EXCLUDED_RUNS.json` | ✅ **R-4** — 62 dirs across 6 experiments | — |
| P0.2e | 0 | metric renames | ✅ done — `uniq_frac` had **no producer at all**; one added | — |
| P0.3 | 0 | full test suite triage — 18 failures classified and repaired | ✅ **760 passed, 0 failed, 7 skipped** (was 721/18/7) | **Phase-0 exit** |
| P1.1 | 1 | scoped attention-knockout semantics (5 modes) + synthetic tests | ✅ **R-3** — +225/−0, 52 tests, 194 passed | — |
| P1.2 | 1 | 8-row liveness smoke, Llama first | 🔬 **779477–779482 queued** | must fire exactly as designed |
| P1.3 | 1 | same-session 7-arm decomposition, both models | ⬜ | Outcomes A–E |
| P2 | 2 | semantic binding probe + causal intervention on it | 🔬 instrument BUILT (not run); **PR-2** fixes the headline group | — |
| P2B | 2B | completion phenotype instrument | ✅ built (blinded, two views, agreement + confusion matrix persisted); **not a causal estimator until its reliability is measured** | — |
| P2C | 2C | row-wise demo-deletion control | ⛔ **DESCOPED on this bank (R-7)** — the deleted population is 1 prompt by construction | — |
| P3 | 3 | full-state rescue, then retrieval-effect subspace | ⬜ | full-state first |
| P4A | 4 | fourth demonstration pool (`club`), frozen confirmatory | ⬜ | analysis frozen first |
| P4B | 4 | regenerate pools at 8–10 **domains**, one bank per pool | ⬜ | domains accepted on audit, never on effect size |
| P5 | 5 | joint crossed bank | ⬜ | strict acceptance |
| P5B | 5B | geometry on both models | ⬜ | — |
| P6 | 6 | Qwen3 retrieval × refusal | ⬜ | identifiability gate |
| P7 | 7 | objective reopen gate | ⏸ | O1–O6 |

## B4. SLURM JOB LEDGER

*(every job submitted by this phase, with the commit its tree will execute; FAILED and CANCELLED rows
stay visible)*

| job id | owner | what | submitted | tree commit | output | status |
|---|---|---|---|---|---|---|
| **779083 / 779084** | ⚠ **UNATTRIBUTED — now identified** | `boomb`, submitted **2026-08-24 23:20:23**, `killable`, `n-801`, `WorkDir` = this repo. Read from the previous log as Phase 10b Qwen3 `button_gun`. **Nobody in contact claims them.** | 23:20 | presumed `3e3000a0` | `.../score_behavior/` | ✅ **COMPLETED 01:29:56**, both, exit 0:0. **Left alone throughout; never cancelled.** Owner identified at 00:47 as `bridge:session_014rrdKYhbejM6zf4W2mjomM`, which has since stopped and explicitly disowned them. **Not consumed by this phase** — and their scientific value is moot regardless, because prev-C-18 invalidated the *unit*, not the number, so equalising the gun pool's depth cannot rescue prev-R-BD |
| 779085 / 779086 | ⚠ unattributed | Llama half of the same pair; reported COMPLETED in the previous log | 23:20 | presumed `3e3000a0` | `.../score_behavior/` | COMPLETED (per prev-log) |
| **779477** | this | **P1.2 smoke** `A_baseline`, Llama, `--limit 8` | 01:32 | `802d73ef` | `s1A_20260825_015705_731547` | ✅ COMPLETED 6:19, 0:0 |
| **779478** | this | smoke `legacy_all_query` — the bridge arm | 01:32 | `802d73ef` | `s1_legacy_all_query_20260825_020636_732499` | ✅ COMPLETED 1:12, 0:0 — **R-5 partial** |
| **779479** | this | smoke `query_prefill_only` — **must show 0 decode edits** | 01:32 | `802d73ef` | `.../score_behavior/s1_query_prefill_only_*` | PENDING (Priority) |
| **779480** | this | smoke `decode_only` — **must show 0 prefill edits** | 01:32 | `802d73ef` | `.../score_behavior/s1_decode_only_*` | PENDING (Priority) |
| **779481** | this | smoke `response_query_only` — **the primary arm of the phase** | 01:32 | `802d73ef` | `.../score_behavior/s1_response_query_only_*` | PENDING (Priority) |
| **779482** | this | smoke `demo_processing_only` | 01:32 | `802d73ef` | `.../score_behavior/s1_demo_processing_only_*` | PENDING (Priority) |
| 776368 | peer (`…FOLLOWUP implementation`) | `run_band2_judge.sh`, `cpu-killable` | 2026-08-23 17:16 | `91e30a62` | `.../judge/bnd2_*` | peer has stopped and is not analysing it |

## B5. RESULTS

*(`R-` ids, newest first)*

### ⛔⛔ R-7 (03:05) — **THE DEMONSTRATION-DELETION CEILING IS NOT RECONSTRUCTIBLE ON THIS BANK, BY ANY DELETION RULE. Phase 2C cannot run here, and that is a property of the bank rather than of the old code.**

**Producing module:** `src/boombness/demo_deletion_control.py` (new). **Verified independently by me**
with a hash-only census — no prompt text read out.

Canonical Phase-1 population (`behavioral` ∧ `natural_doublespeak` ∧ `bank_block ∈
{core2x2, core2x2_slot3}` ∧ `n_examples ∈ {1,2,4,8}`), **n = 96**:

| quantity | distinct values |
|---|---|
| `full_prompt` | **96** |
| `demo_block` | **96** |
| prefix (text before the demo span) | **1** |
| suffix (text after the demo span) | **1** |
| **deleted prompt (prefix + suffix)** | **1** ← the ceiling population |
| rows where the demo block is not uniquely locatable | 0 |

**The 96 rows differ ONLY inside their demonstration blocks**, which are **68.0 %** of the prompt by
characters; everything outside is byte-identical across all 96. Widening to the whole behavioral bank
(1152 rows), the demo-free residue takes **9** distinct values.

> **Deleting the demonstrations is precisely the operation that deletes all between-row variation.**
> The ceiling is one Bernoulli draw *regardless of implementation quality*.

**This reframes prev-REVIEW-2's M1.** That finding — `final_query_text` takes only 2 distinct values
bank-wide, so the 96-row `--demo-deleted` arm was one prompt — was read as a defect in the arm.
**Fixing the arm does not recover a population.** A row-specific, structure-preserving deletion built
correctly still yields **one** prompt, because the rows never differed outside their demo blocks in the
first place. **A deletion ceiling requires a bank whose rows vary OUTSIDE the demo block** — varied
queries, wrappers or surfaces per cell.

**D-6 — Phase 2C is descoped on this bank, not deleted from the plan.** The module is kept and is
written to work unchanged on a bank that does vary outside the demo block; its guard passes once ≥ 90 %
of transformed prompts are distinct. ⚠ **That 0.90 floor was chosen by the implementer, not by the
plan** — it is stated and defended in the module docstring and asserted at the 18/20-vs-17/20 boundary
in tests, and the plan should ratify or change it before 2C is ever scheduled.
📌 **Opportunity, recorded for later:** **Phase 4B** (regenerate pools at 8–10 domains) and **Phase 5**
(the joint crossed bank) are both bank-generation jobs. **If either varies the query surface outside the
demo block, the deletion ceiling becomes reconstructible for free.** That is a design requirement worth
carrying into those phases rather than discovering afterwards.

---

### ⚠⚠ R-6 (03:00) — **A COUNT-MATCHED, QUERY-PROTECTED SAME-BAND NON-DEMO CONTROL DOES NOT EXIST AT HIGH DOSE. The plan's §4 control is only runnable at low `n_examples`.**

**Code:** `src/boombness/score_behavior.py` (+215/−10, additive), arms
`nondemo_matched_d1..d3` (strict) and `nondemo_capped_d1..d3` (capped), seeded from the run's own
`--seed` by a stride distinct from the composed-leg stride so a draw index can never collide with a
composed offset — prev-retraction-#7's shape.

**The geometry is the whole finding.** The demonstration block **grows** with `n_examples` while the
non-demo pool is a near-constant ~53 tokens, of which the request and generation header are
**protected** (`query_span_positions`, the existing prev-REVIEW-1 M1 fix, reused rather than
re-derived). Measured per row on the real bank:

| `n_examples` | rows | fraction where a **strict** count-matched control EXISTS | median achieved ratio when capped |
|---|---|---|---|
| 1 | 96 | **1.000** | 1.00 |
| 2 | 264 | **0.898** | 1.00 |
| **4** | 342 | **0.000** | **0.60** |
| **8** | 306 | **0.000** | **0.30** |

⚠ **My own coarse cross-check disagrees at `n_examples = 2` and I am recording the disagreement rather
than picking a side.** Using prev-M1's *published* token constants (|demo_keys| 12 / 25.5 / 53.5 / 106
against a ~15-token protected pool) I get n=2 **infeasible** with a max ratio of 0.59, and capped ratios
of 0.28 / 0.14 at n=4 / n=8 — roughly half the measured ones. The per-row measurement is the better
instrument (my check substitutes one published constant for a per-row quantity), **and the two agree
completely on the load-bearing conclusion: strict count-matching is impossible at `n_examples` 4 and 8.**

**Consequence for inference, stated now:** at `n_examples` 4 and 8 the available control is
**under-dosed**, so it can support *"control ≥ arm, therefore not demo-specific"* but **never the
reverse**. The arm name carries the policy (`matched` vs `capped`) so a capped run cannot be filed as a
matched one, and every row records `control_draw_match_ratio` plus the exact integer positions drawn.

**D-7 — the primary matched control remains the LAYER SWAP, exactly as prev-D-10 already decided.**
This result independently re-derives and quantifies the reasoning behind that decision: the same demo
key set applied at control layers is exactly count-matched by construction, always feasible at every
`n_examples`, and isolates *"these tokens at these layers"* from *"these tokens anywhere"*. The
same-band non-demo draws are a **secondary** control, reported where strict matching exists and clearly
labelled capped where it does not. **The plan's §4 asks for them; the bank can only partly supply them,
and the honest answer is to say so rather than to run a capped arm under a matched name.**

---

### 📌 COMPUTE (02:40) — **fair-share, not capacity, and I am not resubmitting.** Measured before acting.

Smoke jobs 779479–779482 have been `PENDING (Priority)` for **65 minutes**. Diagnosed rather than
assumed:

| evidence | value |
|---|---|
| L40S nodes | `n-801`…`n-805` **mixed** (partially allocated), `t-806` **allocated** |
| pending jobs in `killable` | **56** |
| top pending priority | **100002365** (another user), then 100001218 ×2 |
| **our priority** | **100000441** — last |
| our `gpu-research` FairShare | **0.050676 / 0.370270** |

**We are behind 56 jobs on priority, and the nodes are `mixed` rather than full, so this is the
fair-share ordering the previous phase already diagnosed as the sole constraint** — where widening the
`--nodelist` was *tested with one submission before acting* and changed nothing.

**Actions deliberately NOT taken:**
* **No `scancel`.** Standing rule of this phase, and a blanket cancel on this account destroyed three
  jobs once already.
* **No resubmission.** Re-queueing loses position and, with 56 jobs ahead, makes it strictly worse.
* **No switch to `gpu-students`** despite its FairShare of **0.987162** — `studentkillable` carries no
  L40S, and `run_boombness.sh` hard-fails unless the GPU reports `*L40S*`. Already established; not
  re-derived.

**The queue simply has to drain.** All CPU-side work continues at full speed, which is what the tick
below spends its time on.

---

### 🔬 R-5 PARTIAL (02:10) — **the bridge arm fires correctly on a real model, and the derived prefill counter is confirmed off the toy harness.** 2 of 6 smoke arms landed; the four decisive ones are still throttled.

**Artifacts:** `outputs/boombness/score_behavior/s1A_20260825_015705_731547` (baseline, job 779477,
COMPLETED 6:19) and `s1_legacy_all_query_20260825_020636_732499` (job 779478, COMPLETED 1:12). Both
carry `DONE.json`.

**`legacy_all_query` liveness block, verbatim from `summary.json`:**

| field | value |
|---|---|
| `n_rows` | 8 |
| `frac_rows_decode_live` | **1.0** |
| **`frac_rows_scope_live`** | **1.0** ← the new per-mode gate |
| `liveness_required` | `["n_prefill_edits", "n_decode_edits"]` |
| `liveness_must_be_zero` | `[]` |
| **`scope_violations`** | **`{}`** |
| `median_prefill_edits` | 19 354.5 |
| `median_decode_edits` | 64 948.5 |
| `min_prefill_forwards` | 9 *(= the 9 band layers, one prefill forward each)* |
| `min_decode_forwards` | 1 368 |
| `total_prefill_edits` / `total_decode_edits` | 250 065 / 698 733 |
| `attn_implementation` | `eager` |

**The derived-counter path is confirmed on a real model, not just the toy.** R-3 verified
`n_edits == n_prefill_edits + n_decode_edits` on three toy geometries; the legacy arm routes to
`AllQueryAttentionKnockout`, which never writes `n_prefill_edits`, so this run exercises the derivation
against Llama-3.1-8B. Per row, from `gens.jsonl` (scalar fields only):

| row | `hook_n_edits` | `hook_n_decode_edits` | derived prefill | recorded prefill |
|---|---|---|---|---|
| 0 | 21 087 | 18 018 | **3 069** | **3 069** ✅ |
| 1 | 55 890 | 46 413 | **9 477** | **9 477** ✅ |
| 2 | 120 780 | 94 545 | **26 235** | **26 235** ✅ |

**Rows violating the invariant: 0 of 8.** So the legacy liveness verdict is a measurement on the real
model, not an artifact of the derivation.

**Auditability holds:** `intervention.knockout_scope = "legacy_all_query"` is in `summary.json`, and
every `gens.jsonl` row carries `knockout_scope`, `hook_n_prefill_edits`, `hook_n_query_rows_edited` and
`hook_liveness_violations`. A scope is not distinguishable only by a flag that appears nowhere.

⚠ **This is NOT the smoke passing.** The two arms that carry the whole design — `query_prefill_only`
(must show **zero** decode edits) and `decode_only` (must show **zero** prefill edits) — are jobs
779479 and 779480, still `PENDING (Priority)`, along with `response_query_only` (779481) and
`demo_processing_only` (779482). **A mode that silently collapsed into another would look perfectly
healthy in the block above.** The smoke is read as a whole or not at all, and no scientific arm runs
until it is.

---

### ★★★★ R-3 (01:20) — **PHASE 1 INSTRUMENT BUILT: five scoped modes, purely additive, and the legacy path still constructs the ORIGINAL class.** No scientific arm has run.

**Code:** `doublespeak_causality/pair_common.py` **+225 / −0** — `git diff --numstat` confirms **zero
deleted lines**, so `AttentionKnockout` and `AllQueryAttentionKnockout` are byte-for-byte untouched and
every committed G1/G3/Phase-2-4 artifact keeps its producing semantics.

**The five modes** (`pc.SCOPED_KNOCKOUT_MODES`), all differing only in *which query rows* are filtered
on top of the existing `lo = max(0, kp − past)` algebra:

| mode | prefill | decode |
|---|---|---|
| `legacy_all_query` | every row | every row |
| `query_prefill_only` | final-query span only | — |
| `decode_only` | *(untouched)* | every generated row |
| `response_query_only` | final-query span | every generated row |
| `demo_processing_only` | rows **inside** the demo block | — |

**The design decision that matters most:** `--knockout-scope` defaults to `legacy_all_query`, and that
default **routes to `pc.AllQueryAttentionKnockout`, not to the new class**
(`score_behavior.py:583`). So existing recipes are unchanged *by construction* rather than by test —
the strongest available guarantee, and it means no argsfile in the repo changes behaviour.

**Mode-aware liveness, and the trap PR-1 predicted.** Two modes make **zero decode edits by
definition**, so the inherited `frac_rows_decode_live ≥ 0.99` gate would have aborted them or, worse,
reported them as clean nulls. The contract now lives in one place — `LIVENESS_REQUIREMENT` (counters
that must be > 0) and `LIVENESS_MUST_BE_ZERO` (counters that must be exactly 0) — and
`scoped_liveness_violations(mode, stats)` asserts **both directions**. I verified by reading it that it
is **not** the forbidden "either counter is non-zero" form: a decode-scoped mode with zero decode edits
still fails.

#### ⚠ The subtle bug this could have had, found and handled

`AllQueryAttentionKnockout` **does not write `n_prefill_edits`**, but
`LIVENESS_REQUIREMENT["legacy_all_query"]` requires it > 0, and `scoped_liveness_violations` reads
`stats.get(key, 0)` — so **a key the legacy hook never wrote is indistinguishable from a real zero, and
every legacy arm would have been reported as dead at prefill.** A *fabricated liveness failure* is as
useless as a fabricated pass, and both are silent. It is derived instead, in one place, from the
invariant both classes share: `n_edits == n_prefill_edits + n_decode_edits`.

**I did not take that invariant on trust.** Driven independently through the repo's own toy harness on
three geometries (1 prefill + n decode steps):

| layers / seq / decode steps | legacy `n_edits` | legacy `n_decode_edits` | derived `n_prefill_edits` | scoped `n_prefill_edits` |
|---|---|---|---|---|
| 2 / 8 / 3 | 34 | 12 | **22** | **22** ✅ |
| 3 / 12 / 5 | 123 | 45 | **78** | **78** ✅ |
| 1 / 6 / 1 | 5 | 1 | **4** | **4** ✅ |

`n_edits` and `n_decode_edits` are identical between the two classes on all three, the gate **passes**
the derived legacy stats, and — the check that matters — it still **catches** a hand-injected dead
decode hook (`n_decode_edits = 0` → violation). **The legacy liveness verdict is sound and is not
fabricated in either direction.**

**Tests:** 52 new synthetic tests reusing the existing `ToyModel` harness rather than re-implementing
it, including legacy **byte-identity** at prefill and every decode step, zero-decode-edits for both
prefill-only modes, `decode_only` leaving the prefill mask `torch.equal` to baseline, and the
**disjointness** test that makes the decomposition a decomposition:
`query_prefill_only` and `demo_processing_only` edit **disjoint** query-row sets whose union is a subset
of legacy's. Both absolute-vs-cache-local coordinate-confusion directions are tested.
**Verified by me, serially: 194 passed** across the 10 new and affected files.

⚠ **What this is NOT.** No arm has run, no GPU has been used, and nothing here says anything about
behaviour. The next step is PR-1's 8-row liveness smoke, and **no scientific arm runs until every mode
fires exactly as designed.**

---

### ★★★ R-4 (01:16) — **THE INCOMPLETE-RUN PROBLEM IS 12× BIGGER THAN THE AUDIT FOUND: 62 directories, not 5 — and one of them is my own.**

**Artifact:** `outputs/boombness/EXCLUDED_RUNS.json` (schema `EXCLUDED_RUNS/1`, tracked).
**Producing script:** `src/boombness/excluded_runs.py`.

The Part-II audit found **5 of 12** incomplete dirs under `crossbank_knockout_test/`. Scanning **every**
experiment directory instead:

| experiment | dirs lacking `DONE.json` |
|---|---|
| `judge` | **31** |
| `score_behavior` | **21** |
| `crossbank_knockout_test` | 5 |
| `extract_boombness` | 3 |
| `retrieval_strength` | 1 |
| `rederive_crossbank` | **1 — mine** |
| **total** | **62** |

By reason: **28** `no_done_json`, **27** `empty_skeleton`, **7** `aborted`. **33 carry partial results**
— the dangerous shape, because a partial dir flows through a `newest()`-style lookup and produces a
plausible number. **Nothing is marked `safe_to_delete`; nothing was deleted.** The skeletons are
evidence of a debugging sequence.

**The scanner immediately earned its keep by catching my own debris:**
`rederive_crossbank/rederive10_20260825_002905_2199605` — the run that died on the repo's
`FailureLedger` guard while I was building R-1 — is classified `no_done_json`, `has_partial_results:
true`, `superseded_by: rederive10_20260825_002934_2201570`. **A glob over that experiment directory
would have had two candidates and no way to tell them apart.**

---

### ⛔⛔ R-2 / C-1 (00:29) — **THE HEADLINE DIRECTION IS ONE DEMONSTRATION CORPUS. Drop the bomb pool and the prompt-level effect is p = 0.092.** First correction of this phase, and it is to the claim the whole phase inherits.

**Artifact:** `outputs/boombness/rederive_crossbank/rederive10_20260825_002934_2201570/rederive_crossbank.json`
**Producing script:** `src/boombness/rederive_crossbank.py` (new, this phase)
**Command:** see §B9. Threshold 0.50, 10 populations, 143 discordant comparisons.

The surviving inherited claim is *"the direction is well supported — 113 down against 30 up,
p = 1.577e-12."* **Decomposed by demonstration pool, that p is one corpus:**

| demonstration pool | concept | down / up | **exact two-sided binomial p** |
|---|---|---|---|
| **`b5e399712b996b7d`** | **bomb** | **81 / 11** | **2.50151e-14** |
| `5d3080f60af987c6` | knife | 15 / 7 | **0.133801** |
| `79e93dbb2b65c820` | gun | 17 / 12 | **0.458258** |

| leave-one-pool-out | down / up | p |
|---|---|---|
| drop knife | 98 / 23 | 3.23986e-12 |
| drop gun | 96 / 18 | 4.72143e-14 |
| **drop bomb** | **32 / 19** | **0.0919145** |

> **The effect is significant on one of three demonstration corpora and null on the other two.**
> That is a materially different claim from *"113 down against 30 up over 10 populations"*, and it is
> the claim the artifact supports.

⚠ **And `pool` is perfectly confounded with target CONCEPT here** — b5e3 = bomb, 5d30 = knife,
79e9 = gun. So "three independent demonstration pools" and "three target concepts" are **the same
factor**. The pool main effect in the ANOVA below is also a concept main effect and cannot be
separated at k=3. Nothing in the previous phase says this.

**Two further composition defects in the same statistic, both confirmed:**

* **The n is inflated by design-slot reuse.** The 143 discordant comparisons come from only
  **67 distinct `prompt_id`s** of 96 — the ten populations are the same 96 design slots with different
  lexical fill, so one slot can contribute up to 10 comparisons. The binomial assumes prompt
  independence, which this violates by construction.
* **The both-arms-EOS control is not a 10-population control.** It reproduces numerically
  (**30 down / 1 up, p = 2.9802322387695312e-08**) but **5 of the 10 populations contribute zero
  both-EOS discordant rows**: `Q|window_knife`, `L|ticket_bomb`, `L|button_knife`, `L|window_knife`,
  `L|basket_gun`. Truncation is heavily asymmetric on Llama, so the control is carried by the same
  populations as the effect.

**Status:** the LIVE ledger's direction row is amended, not deleted. Direction still holds *as a
direction*; what is withdrawn is the implication that 10 populations, 5 banks and 3 pools are
independent support for it.

---

### ★★★★ R-1 (00:29) — **PHASE-0 §2.1 SATISFIED: an independent re-derivation reproduces prev-C-18 to the digit, including the number C-18 could not have taken from the repo's own table.**

**Artifact:** as R-2 above. **The path is genuinely independent** — `rederive_crossbank.py` imports
`common` only (for `RunDir` / `FailureLedger`) and does its own arithmetic; it never imports
`crossbank_knockout_test`. Agreement is therefore evidence, not tautology.

| quantity | prev-C-18 | **this re-derivation** |
|---|---|---|
| all 10 populations are the same 96 `prompt_id`s | asserted | **CONFIRMED** — all 45 pairwise intersections = 96, union = 96 |
| distinct demonstration pools | 3 | **3** (proved from bank `_meta.pools_sha16`, not bank names) |
| pool main effect | SS 0.10102, df 2, 30.2 % | **0.10101996528, df 2, 30.207657 %** |
| domain main effect | SS 0.10655, df 5, 31.9 % | **0.10655381944, df 5, 31.862427 %** |
| interaction | SS 0.12684, 37.9 % | **0.12684461806, df 10, 37.929916 %** |
| **share that is double-counted main effects** | 62.1 % | **62.0701 %** |
| k=18 crossed cells *(the retracted unit)* | [−0.1461, −0.0066] | **[−0.1461364242, −0.0066413536]**, excludes 0 |
| k=3 pool marginal | [−0.3043, +0.1516] | **[−0.3043121512, +0.1515343734]**, includes 0 |
| k=6 domain marginal | [−0.1649, +0.0121] | **[−0.1648382480, +0.0120604702]**, includes 0 |
| crossed random-effects interval | [−0.2796, +0.1268] at df 2.53 | **[−0.2795835881, +0.1268058104] at df 2.5294593771** |

**One thing this pins that was previously unverifiable.** The crossed random-effects interval
reproduces *only* with a real t distribution (`scipy.stats.t.ppf`); the repo's own shipped `_T`
interpolation gives t = 3.7095 at df 2.53 and hence [−0.28901, +0.13623]. **So prev-C-18's published
number did not come from the tool's table**, and if that interval is ever moved into an artifact the
two paths would disagree by 0.0095 on the lower limit. Recorded so the discrepancy is a known
convention rather than a future correction.

⚠ **An ambiguity in "the domain marginal" that someone must resolve.** There are two of them, and the
previous phase quotes both. **Pool-balanced** (mean the 3 pool cells per domain, then the 6 domains):
mean **−0.0763888889**, CI **[−0.1648382480, +0.0120604702]** — what this artifact reports.
**Population-weighted** (mean the 10 population cells per domain): mean **−0.0865**, CI upper
**+0.0108** — what prev-R-BE reports. **Both include zero, so the conclusion is identical**, but the
numbers differ and adjacent tables in the previous log quote the k=6 CI from one and the k=6 p from the
other. **This phase uses the pool-balanced version and says so**, because pool is the independence
axis C-11 established.

**Judge hygiene, checked rather than assumed:** `judge_status == "ok"` on all 96 rows of all 20 judge
dirs; zero null `strongreject_score`; the `FailureLedger` records 0 unpaired prompt_ids, 0 null scores,
0 missing `stop_reason` across all 10 populations (960 paired rows).

## B6. CORRECTIONS / RETRACTIONS

*(`C-` ids, newest first. This phase's numbering starts at C-1 and is namespaced to this file; the
previous phase's C-1…C-18 are referenced by name, e.g. "prev-C-18".)*

### ⛔⛔ C-2 (00:42) — **TWO CONCURRENT PYTEST RUNS CORRUPTED A COMMITTED SCIENTIFIC ARTIFACT, and the corruption survived both runs' restore logic. Caused by my own parallelisation.**

**What happened.** `tests/test_verify_report_numbers.py` contains two guard tests that **mutate real,
committed files in place** and restore them in a `finally`:

* `test_FAILS_when_an_artifact_value_is_tampered_with` writes `0.9999` into
  `outputs/boombness/advbench_decomposition.json` → `paired_vs_baseline.B.delta_cluster_mean`;
* `test_FAILS_when_the_number_is_removed_from_the_report` rewrites `+0.0333` → `+0.0999` in
  `reports/boombness_objective_sprint_report.md`.

Both are correctly written for **serial** execution: `shutil.copy2` to a `.testbak`, mutate, assert the
guard catches it, `finally: shutil.move(backup, original)`, then a final
`assert _run().returncode == 0, "restore failed; the tree is left dirty"`.

**They are not safe under concurrency, and I ran them concurrently.** Four repair agents were editing
disjoint file sets, and at least two of them ran `pytest tests/` at the same time as I did. The race is
the obvious one: run A copies a clean backup and mutates the file; run B then copies **the already
mutated file** as *its* backup; A restores its clean copy; B restores its dirty one. **The last writer
wins and the tamper value is left on disk.**

**Detected, not stumbled into.** The next serial run failed `test_passes_on_the_real_tree` with
`14-B arm B clustered delta … expected 0.0305, actual 0.9999 VALUE MISMATCH` — the tamper constant
itself, sitting in a committed artifact. `check_all.py` then reported
`1 of 6 guards FAILED: verify_report_numbers`.

**Blast radius, measured rather than assumed.** Both files are **tracked**, so `git status` showed them
modified and `git checkout --` restored them exactly:
`delta_cluster_mean` is back to **0.030519369707034255**, which is bit-identical to the value Part I
§6.1 publishes, and the report again contains **4** occurrences of `+0.0333`. `check_all.py` is green.
No `.testbak` files remain anywhere in the tree. **No result of this phase read either file while it
was corrupt** — R-1/R-2 use `rederive_crossbank.json`, which touches neither.

⚠ **A stale `.git/index.lock` (0 bytes, 00:38:54) blocked the first restore attempt** — a git process
from a killed agent. Verified no `git` binary was running before removing it, per git's own message.

#### Standing rules adopted, and they bind the rest of this phase

1. **Never run `pytest tests/` concurrently with anything else in this repo** — not another agent, not
   a second shell. The suite mutates tracked files by design. Full-suite runs are **serial and
   exclusive**, and the §18 4-hour review must schedule them that way.
2. **Parallel agents may not run the full suite.** They run only the subset covering their own files.
   *(This is a correction to my own workflow instructions, which told four agents to "run the full
   suite" — three of them did, simultaneously.)*
3. **After any full-suite run, check `git status outputs/ reports/`.** A clean run leaves nothing dirty;
   anything dirty is a corrupted artifact, not a stale file.
4. **Proposed hardening, not yet implemented** (recorded so it is not lost): these two tests should
   operate on a **copy in `tmp_path`** with the verifier pointed at it, rather than mutating the real
   tree — or take an exclusive lock. Filed as an open item rather than fixed now, because changing a
   guard's mechanism during a repair pass is how the previous phase produced its dead guards.

**This is the third time in two phases that a defect has been caught only by cross-checking two
computations of the same thing** (prev-R-BD's silent overwrite, prev-C-18's crossed table, now this).
The pattern is worth naming: **the corruption was invisible inside either run and obvious the moment a
third, independent run read the same file.**

---

### ⚠ C-1 — see **R-2** in §B5

The amendment to the inherited headline direction (the effect is carried by one demonstration corpus)
is recorded as R-2 rather than duplicated here, because it is a *result* of this phase's own
re-derivation rather than a correction to something this phase published.

## B7. FAILED / VOID RUNS

*(kept visible on purpose)*

*(none yet from this phase)*

## B7b. PROCESS NOTES

### ⚠⚠ P-1 (00:41) — **THE THIRD WRITER IS CONFIRMED BY A SECOND, INDEPENDENT ROUTE. I attributed a job pair, a log file and a tool to a session that has never touched any of them.**

At 00:28 I messaged the peer session proposing an ownership split (D-2). Its reply, verbatim in
substance:

* **779083 / 779084 are not its jobs.** Its only job was **776368** (`cpu-killable`,
  `run_band2_judge.sh`). It has no Phase 10b, no Qwen3 `button_gun`, no crossbank work. *"Do NOT wait on
  me to finish 10b — nobody in this session is going to. If you plan around my finishing it, you will
  wait forever."*
* **`external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md` and
  `src/boombness/crossbank_knockout_test.py` are not its files.** Its log is
  `external_md/BOOMBNESS_D_SURFACE_FOLLOWUP_PROGRESS.md` — a different file whose name differs by two
  characters. **Treating those two as "the peer's" would have frozen paths that have no owner in
  contact.**
* It has **stopped entirely** and released every boombness file, the crossbank tool and job 776368.

**Why this is a finding and not just a mix-up.** The previous phase already recorded one unattributed
commit (`91e30a62`, 17:09 on 08-23) that neither session in contact wrote. **This is the second
independent sign of the same thing**, and it is stronger: an entire live phase — its log, its tool, its
running jobs — has been read by two different sessions as belonging to each other. `sacct` confirms
779083/779084 were submitted **2026-08-24 23:20:23** with `WorkDir` inside this repo, under this
account, and they are still RUNNING. Git cannot help: **all commits on this branch carry one identical
author *and* committer identity with zero date skew**, so a third writer is invisible in the metadata.

**Standing consequences for this phase, adopted now:**

1. **`git log` immediately before every commit**, and `git diff HEAD` on the files just written
   afterwards to confirm the committed bytes are the intended bytes. HEAD moved three commits between
   the plan being written and this file being opened.
2. **Never `scancel`.** 779083/779084 are left to run to completion. A blanket cancel on this account
   destroyed three jobs once already (2026-08-20 17:37).
3. **Do not consume 779083–779086's outputs in this phase** without independently re-verifying their
   provenance (tree commit, argsfile, population, liveness) — their producing session is unreachable, so
   their configuration cannot be confirmed by asking.
4. **Attribute by artifact, never by inference from the queue.** The error I made was reading
   "a job is running under my account" as "the session I am talking to launched it".

### ✅ Two inherited findings the peer independently corroborated (00:41)

* **Judge instability, from the other side.** The peer saw identical generations move a baseline ASR
  **0.1714 → 0.1595** across sessions while a **paired** delta reproduced to four decimals — the same
  phenomenon as the 78/96 binary-label agreement in §B8. **Its mitigation is the one this phase adopts:
  paired estimators, never per-prompt identity claims.**
* **Length-proxy gates.** The coherence gate's `scorable_frac` is a **length** proxy that flags
  *refusal* rather than incoherence: six runs excluded as degenerate were lexically **healthier** than
  the untreated baseline. `uniq` **by text** and `trigram_repeat` behaved correctly; `scorable_frac` and
  length-based uniqueness did not. **Adopted as a rule for Phase 1 §4.2:** any arm exclusion must be
  justified on a by-text metric, never on a length proxy.

### ⛔ P-2 (00:41) — an inherited claim that must not be reintroduced

**"Established at L10/L12" is WITHDRAWN.** Under the repo's own depth-family policy
(`analyze_control_recheck.py`, *"the family is the depth set"*) Holm gives **0.0732 at m=4** and
**0.2014 / 0.2440 at m=11**. **Nothing rejects.** Flagged by the peer as easy to reintroduce by accident
from older notes; recorded here so this phase cannot do so.

## B8. REVIEWER FINDINGS

*(adversarial reviews, with what was accepted, what was refuted, and by what recomputation)*

**Inherited — the Part-II audit (2026-08-24/25, 361 checks against committed artifacts).** 338 MATCH /
14 MISMATCH / 9 UNVERIFIABLE; of the mismatches, 5 refuted, 1 superseded, **8 upheld**. The eight, all
of which this phase must avoid inheriting: R-AE's codeword-subspace upper endpoint is **0.5714** not
0.5722; REVIEW-2 M3's "byte-identical cell E" is false for `basket_bomb` (maxabsdiff 7.81e-04) though
its counts are right; R-T's "same ~17 prompts" is net-only (**23 vs 19** crossings, 7 overlapping);
`uniq_frac` is distinct completion **lengths**; R-U's demo-token median is **38.5** not 44; R-AI's
"Spearman ρ" is Pearson r on log₂(n_examples) (**both Qwen3 p's become 0.3333** under real Spearman);
Phase-6d's codeword PC2 dose is **0.0020** not 0.0027; and `cell_residual_frac_removed` is carried by
**2 of 9** R-AH runs. Full detail: `reports/SPRINT_SUMMARY_2026-08-23_TO_08-24_PART_II.md` §11.

**Inherited — judge re-scoring instability (the single most consequential finding for this phase).**
Sessions 776893 and 777030 judged the **same generation files**; on byte-identical text `p2A` returned
an identical `strongreject_score` on **70/96** rows and the same binary label on **78/96** — **18 of 96
prompts crossed the 0.5 threshold on re-judging.** Aggregate ASR is identical (the flips cancel).
**Consequence for this phase:** every per-prompt claim needs an explicit reliability budget, and Phase
1's equivalence margin must be set above this floor. This is why §1.1's per-prompt rule exists.

## B9. REPRODUCTION COMMANDS

*(one command per result; filled in as results land)*

```bash
# environment (login-shell python has no torch; its failures are not repo failures)
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python

# the six deliverable guards — must exit 0 before any commit
$PY src/boombness/check_all.py

# full suite baseline
$PY -m pytest tests/ -q

# the knockout instrument (CPU-only, ~26 s)
$PY -m pytest -q doublespeak_causality/tests/test_allquery_attnknockout.py \
                 doublespeak_causality/tests/test_attnknockout_synthetic.py

# R-1 / R-2 -- the independent re-derivation of the cross-bank result (CPU, ~30 s, no GPU, no API).
# Does NOT import crossbank_knockout_test; all arithmetic is local, so agreement is evidence.
$PY src/boombness/rederive_crossbank.py \
    --manifest outputs/boombness/argsfiles/xb_manifest10.txt \
    --thresholds 0.25,0.5,0.75 --tag rederive10
# -> outputs/boombness/rederive_crossbank/rederive10_<stamp>/rederive_crossbank.json
```


### P1.2 smoke — the exact command lines *(argsfiles live under `outputs/`, which is gitignored, so the literals are embedded here; this is the reproducibility gap the previous phase had to close retroactively)*

Common prefix, identical in all six arms:

```
--bank /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/data/boombness_prompts/boombness_prompt_bank.jsonl --query-kinds behavioral --conditions natural_doublespeak --bank-blocks core2x2,core2x2_slot3 --n-examples 1,2,4,8 --max-new 192 --dtype bfloat16 --seed 20260825 --model meta-llama/Llama-3.1-8B-Instruct --attn-impl eager --limit 8
```

Per-arm suffix:

| arm | suffix |
|---|---|
| `s1_A` | `--arm A_baseline --tag s1A` |
| `s1_<MODE>` | `--intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope <MODE> --arm C_<MODE> --tag s1_<MODE>` |

with `<MODE>` ranging over the five values of `pc.SCOPED_KNOCKOUT_MODES`. Submitted as:

```bash
sbatch --export=ALL,BOOMB_SCRIPT=score_behavior.py,\
BOOMB_ARGSFILE=$REPO/outputs/boombness/argsfiles/s1_<NAME>.txt \
       src/boombness/slurm/run_boombness.sh
```

⚠ `--limit 8` is applied **after** `--expect-n` is checked and after `run.note` records the population,
so each smoke artifact will report `n: 96` in its composition block while holding 8 rows. That is
prev-REVIEW-2's finding S3, not a new defect — **the smoke's row count must be read from the liveness
block, never from `population_composition`.**

## B10. CANONICAL ARTIFACTS OF THIS PHASE

| artifact | produced by | holds |
|---|---|---|
| `outputs/boombness/rederive_crossbank/rederive10_20260825_002934_2201570/rederive_crossbank.json` | `src/boombness/rederive_crossbank.py` | **R-1 / R-2** — population identity, pool proof, per-population ASR, crossed ANOVA + both marginals + crossed random-effects interval, prompt-level binomial **decomposed by demonstration pool**, both-EOS composition |

---

*Opened 2026-08-25 00:30 at HEAD `059e819f`. Part A is stable. Everything below it is append-only.*
