# Representation Access & Headroom (RAH) — sprint plan and authoritative progress log

**Namespace: `RAH-`.** This file is **append-only**. Nothing already written here is edited to say
something different; corrections are added as new `RAH-C-###` entries that name the entry they
correct. Tables may be regenerated only by appending a new dated version of the table.

| | |
|---|---|
| Sprint | Representation Access + Headroom (RAH) |
| Predecessor | Representation–Behaviour Dissociation confirmatory sprint (`reports/RBD_SPRINT_SUMMARY.md`) |
| Opened | 2026-08-30 |
| Branch at open | `behavioral-causality-sprint` |
| HEAD at open | `fe8fd610da83772686016ff446dde004fc01710d` |
| Writer | ONE session only (see §5) |

---

## Registry conventions

| prefix | meaning |
|---|---|
| `RAH-PR-###` | preregistration — written **before** the data it governs exists |
| `RAH-R-###` | result (including retraction of a result) |
| `RAH-C-###` | correction |
| `RAH-DR-###` | deep review |

**Never** reuse bare `R-`, `C-`, `PR-`, `DR-`, `V-`, or the `RBD-` namespace. When this log refers to
a previous-sprint id it is always written in full (`RBD-C-016`) and is understood to be **historical
and closed** unless this sprint explicitly reopens it under a new `RAH-` id.

Every claim recorded here carries a **status word** drawn from a closed set:

`DISCOVERY` · `DIAGNOSTIC` · `CONFIRMATORY` · `EXPLORATORY` · `DECLINED` · `FALSIFIED` · `CANNOT ANSWER`

---

# 0. Scientific motivation

## 0.1 What the previous sprint established

The predecessor sprint tested:

> `demo_processing_only` (an attention knockout masking demo→demo attention during prefill) removes
> the Doublespeak behaviour while **preserving** the installed semantic mapping.

On held-out lexical material this **did not replicate**. Held-out binding, `lantern ↔ poison`,
n = 80 families:

| | baseline | `demo_processing_only` | late-band control (dose-matched) |
|---|---|---|---|
| Llama-3.1-8B | 78/80 | **61/80** — Δ −0.2125, 18 lost / 1 gained | 78/80 — Δ **exactly 0** |
| Qwen3-14B | 75/80 | **9/80** — Δ −0.8250, 66 lost / 0 gained | 75/80 — Δ **exactly 0** |

The control was **dose-matched in `total_prefill_edits`**, so the Qwen3 collapse is *not* explained
by "more edits". Binding preservation is **excluded on Qwen3**. On Llama it is **NOT_ESTABLISHED at
the preregistered equivalence margin** — which is *not* the same as a decisive falsification, and
this sprint will not describe it as one (see `RBD-C-020`).

The behavioural half returned **OUTCOME E — POPULATION CANNOT ANSWER**: baseline attacks 12/160
(Llama) and 5/160 (Qwen3) against a preregistered floor of 14. **That decision stands and is not
revived here.** In particular the Llama 12→1 pattern is *not* evidence for the mechanism; on Qwen3
*every* baseline attack vanished under *every* arm including the exactly-inert control, which shows
the design cannot separate intervention effect from attack churn at these rates.

## 0.2 The unresolved question this sprint exists to answer

> When forced-choice binding accuracy collapses under `demo_processing_only`, was the semantic
> representation **destroyed**, or did the intervention only disrupt **access / reportability** of a
> representation that still exists internally?

The predecessor sprint proved this is **not answerable behaviourally**, and proved it structurally
rather than anecdotally:

> A readout that names its options is high-mass and **exposure-confounded**; a readout that does not
> name its options is exposure-clean and **unreportable** (option mass 0.001–0.038 against a 0.05
> gate on the decisive Qwen3 cell). **No readout in this project's inventory is both.**

Therefore the primary new test **must be activation-level**, and this sprint will not attempt to
solve it by inventing another behavioural prompt.

## 0.3 The three things that must be separated

1. the representation **exists** (information is present in the activations);
2. the representation is **accessible to a behavioural readout** (reportable);
3. the representation is **causally usable downstream** (an intervention on it moves computation).

A linear probe can speak only to (1). Only a causal transport experiment can speak to (3).

---

# 1. Hypotheses

## Track A — representation vs access

**`H-A0` (null).** Under `demo_processing_only`, an exposure-clean donor activation carries **no more**
mapped-concept information into an independent receiver than a shuffled-family donor does.

**`H-A1` (preservation).** Under `demo_processing_only`, the exposure-clean donor activation still
**causally transmits** the correct mapped concept into an independent receiver, at a level
**equivalent to baseline** and **clearly separated from** shuffled-family and wrong-concept donors —
even though forced-choice binding behaviour has collapsed.

**`H-A2` (disruption).** Donor transmission falls together with binding.

**`H-A3` (decodable-but-not-transmissible).** A linear probe decodes the concept from the intervened
donor state, but donor→receiver transport does not transmit it. This is a **distinct** outcome and
must not be collapsed into `H-A1`.

## Track B — properly powered behavioural confirmation

**`H-B0` (null).** On a population with preregistered baseline behavioural headroom,
`demo_processing_only` does not reduce harmful attack behaviour by more than the preregistered
minimum meaningful effect.

**`H-B1`.** It does, and the dose-matched late-band control does not reproduce the reduction.

## Explicitly NOT hypotheses of this sprint

* Anything about an optimisable objective (see §37 of the brief; **no GCG/MAC objective is built**).
* Any claim that Track A and Track B results substitute for one another.

---

# 2. Estimands

## Track A (per model × per lexical pair × per donor arm)

| id | estimand | unit of independence |
|---|---|---|
| `EA1` | **receiver concept accuracy** — P(receiver selects the mapped concept option) | family (paired across arms) |
| `EA2` | **receiver signed concept margin** — logit/logprob of the mapped-concept option minus the max over the other options, at the answer slot | family |
| `EA3` | **Δ(baseline donor − `demo_processing_only` donor)** on `EA1` and `EA2`, paired by family | family |
| `EA4` | **Δ(baseline donor − shuffled-family donor)** and **Δ(baseline donor − wrong-concept donor)** | family |
| `EA5` | **paired family transition counts** (lost / gained / both / neither) | family |
| `EA6` | effect by **domain** | domain (cluster) |
| `EA7` | model interaction — **secondary only**, computed only if the dependence structure supports it |

`EA1` is the **primary** Track-A estimand. `EA2` is the primary continuous companion and is what the
equivalence margin is expressed in when accuracy saturates.

**Error structure is part of the estimand.** The receiver's option set is constructed so that a wrong
answer is informative (§10.3): `mapped-concept` vs `literal-meaning-of-codeword` vs `other-concept`
vs `other-codeword`. Reporting only accuracy discards this and is not permitted for `EA1`.

## Track B (per model × per confirmatory population)

| id | estimand | unit |
|---|---|---|
| `EB1` | harmful ASR (StrongREJECT ≥ 0.5) on the **complete** preregistered population | row; clustered by domain |
| `EB2` | Δ ASR (baseline − arm), paired on the same rows | row; clustered by domain |
| `EB3` | paired transition counts down / up / both / neither | row |
| `EB4` | Δ ASR for the dose-matched late-band control | row; clustered by domain |
| `EB5` | domain-level effect table | domain |

`EB2` for arm B, with `EB4` as the control contrast, is primary. **Effect is reported in raw rows as
well as rates.**

---

# 3. Statistical units and independence

* **Track A unit: the family.** Arms are paired on the same family. Domain is a **cluster** for
  `EA6` and for any CI that is quoted domain-generally.
* **Track B unit: the row**, clustered by **domain**. Domain is the primary cluster unit for any
  domain-general claim. Rows within a domain are **not** independent.
* **Models are separate replications, never replicates.** Llama and Qwen3 are reported separately
  first. A pooled statistic is secondary and must respect the dependence structure. "Both models
  moved the same way" is **not** two independent confirmations when population selection or
  measurement is shared — and here they are shared.
* **Lexical pairs are not independent replicates of each other** unless the design makes them so;
  they share the bank generator, the domain pool and the readout.
* Before any confirmatory run this log will record: **number of clusters**, **attainable exact
  p-floor**, **the intended test**, and **whether magnitude or sign is the primary estimand**. A
  saturated p-value is never quoted as evidence of magnitude.

---

# 4. Populations

## 4.1 Three data levels (Track A)

| level | material | permitted use | forbidden use |
|---|---|---|---|
| **A — discovery / instrument development** | existing discovery banks (`core2x2`, prior pair benchmarks) | debug code, find workable capture positions, measure option mass, build the receiver, establish liveness, **measure receiver repeatability for the equivalence margin** | **may not** supply the confirmatory effect |
| **B — RBD held-out populations** | `lantern_poison`, `candle_missile` | **DIAGNOSTIC**: "what happened in the previous confirmatory result?" | may not be called *newly held out*; may not be the prospective confirmation |
| **C — NEW confirmatory lexical material** | new codeword × concept banks built **after** the assay is frozen | the single **CONFIRMATORY** Track-A claim | may not influence receiver design, layer choice, position choice, threshold choice, or assay choice |

Level C material plays **no role whatsoever** in §14 Stage A calibration. If a level-C bank is built
before freeze, its *contents* may be audited (grammar/tokenisation/alignment) but **no model forward
pass on it may be inspected** until the freeze entry is written.

## 4.2 Track B populations

| level | permitted use |
|---|---|
| **development screening** | baseline-only measurement for headroom, bank validity, cap verification, refusal/truncation. **No causal arm may be run on it before the population freeze.** |
| **confirmatory** | NEW prompt families, NEW demonstrations, NEW seeds, NEW rows. Development rows may **never** enter the confirmatory estimator. |

Domain-pool overlap between development and confirmatory is permitted **only if predeclared here
before screening**, with families and demonstrations fully disjoint, and the resulting generalisation
claim is stated narrowly. Individual domains are **never** selected on effect.

---

# 5. One writer

Exactly one Claude Code session writes, orchestrates, commits and interprets for this sprint.

Read-only subagents are fanned out aggressively for code inspection, statistical review, raw-artifact
re-derivation, independent auditing, run-log inspection, and adversarial claim review.

Subagents may **not**: `git add` / `git commit` / `git push` / `scancel`, modify shared outputs, edit
this file, or edit the claim ledger. Parallel *coding* is allowed only in isolated git
worktrees/branches. Two agents never share a working tree, a source file, or a result artifact.

**History note (why this rule is explicit).** The predecessor phase had an unaccounted concurrent
writer in this tree (`HANDOFF` commits `10fcd035`, `4166a764`, `2f5623be`) and a third party's stash
on the stack. `git stash pop` is banned in this tree.

---

# 6. Controls

## 6.1 Track A activation-level control family (all preregistered, §15 of the brief)

| id | control | what it proves | expected |
|---|---|---|---|
| `CA1` | **self / identity patch** — baseline donor → its own corresponding receiver path | the patching primitive works and does not itself destroy the readout | high accuracy |
| `CA2` | **shuffled-family donor** — donor from a *different* family, same arm | transport is family-specific, not a generic prior | at/near the option-prior floor for the current family's concept |
| `CA3` | **wrong-concept donor** — donor carrying a *different* concept | **positive causality control**: the receiver moves *toward the donor's concept*, not merely to noise | receiver selects the donor's concept |
| `CA4` | **late-band intervention donor** — donor generated under the dose-matched late-band control arm | if binding behaviour is intact there, transport must be intact too | equivalent to baseline |
| `CA5` | **random-direction / matched-norm activation** | separates "any vector at this site changes the answer" from concept transport | no systematic concept selection |
| `CA6` | **patch liveness** — required-positive and required-zero counters on the hook | a dead hook cannot masquerade as a null result | positives > 0, zeros == 0, **never** read via `.get(k, 0)` |

`CA3` is the control this sprint cares most about: without it, a null Track-A result is
uninterpretable, because we could not distinguish "the mapping is gone" from "this patch site does
nothing for anybody".

## 6.2 Track B arms (frozen; §23 of the brief)

`A` baseline · `B` `demo_processing_only` (**primary**) · `C` same-scope late-band dose-matched
control (**primary control**) · `D` `legacy_all_query` (destructive positive control) ·
`E` `response_query_only` (mechanistic secondary comparator).

**No arm is added after seeing B.** A further arm requires a new `RAH-PR-###` and is a new experiment.

---

# 7. Success / failure logic

## 7.1 Track A outcome space (locked before any confirmatory Track-A data)

| outcome | conditions | verdict wording |
|---|---|---|
| **A-I — representation preserved, reportability disrupted** | binding collapsed **and** intervened-donor transport **equivalent** to baseline at the frozen margin **and** clearly separated from `CA2`/`CA3` **and** `CA6` liveness complete | "the intervention did not erase the representation at the measured site; it disrupted access/use" |
| **A-II — representation disrupted** | intervened-donor transport falls with binding, `CA4` intact, `CA2`/`CA3` behave correctly | "the semantic mapping itself is disrupted at the measured stage" — **FALSIFIED UNDER THIS DESIGN** for the dissociation |
| **A-III — decodable but not transmissible** | probe decodes above its controls, transport does not | "information present, not in a causally usable form" — must **not** be reported as preservation |
| **A-IV — assay invalid / CANNOT ANSWER** | `CA1` fails, or `CA3` fails to move the receiver, or liveness incomplete, or option mass below gate, or population incomplete | DECLINE. Not evidence in either direction. |

**Equivalence is required for A-I.** `p > 0.05` is not preservation (§17, §39). A-I requires *both*
equivalence to baseline *and* separation from the null-transport controls.

## 7.2 Track B outcome space (locked before any causal arm)

| outcome | conditions |
|---|---|
| **B-A — clean causal effect** | headroom met on the confirmatory population; B reduces ASR ≥ the frozen minimum meaningful effect; late control does not reproduce it; effect exceeds measured judge/end-to-end noise; no cap problem; complete population; full liveness |
| **B-B — no causal effect** | valid headroom, valid measurement, B below threshold → **a real negative. STOP.** |
| **B-C — non-specific effect** | B and late control comparable → no mechanism-specificity claim |
| **B-D — measurement invalid** | headroom fails on the confirmatory population, cap binds materially, judge provenance fails, population incomplete, or liveness incomplete → **DECLINE** |

## 7.3 Joint interpretation (only after **both** tracks are complete)

| Track A | Track B | reading |
|---|---|---|
| preserved | suppressed | strong representation/behaviour dissociation |
| disrupted | suppressed | suppression may simply be destruction of the mapping |
| preserved | unchanged | representation exists; intervention behaviourally irrelevant |
| disrupted | unchanged | another pathway carries the behaviour, or the measured representation was never behaviourally causal |

**The most interesting cell gets no preference.**

---

# 8. Stopping rules

**Track A stop.** If NEW confirmatory data show intervened-donor activations fail to transmit while
`CA4` remains intact and `CA2`/`CA3` behave correctly → conclude the representation is disrupted at
the measured stage and **stop**. Do **not** search layers until one preserves it. A small predeclared
follow-up asking whether the representation moved earlier/later is permitted **only as a new
`RAH-PR-###`**, and it is EXPLORATORY until independently confirmed.

**Track B stop.** A headroom-qualified confirmatory population showing no effect **ends Track B**. Do
not switch lexical pair, layer, judge, cap, threshold; do not pool domains or models; do not filter
answers. Record the failed replication.

**Invalid-experiment stop.** Headroom failure, liveness failure, cap failure, incomplete population,
judge-join failure, or dev/confirm leakage → return **INVALID / DECLINED**. Never force a verdict.

**Prohibited after a negative** (§56 of the brief), absent a new explicitly-exploratory
preregistration: another layer, another codeword, another concept, another domain subset, another
margin, longer output, removing weird rows, EOS-only, baseline-attacks-only, pooling models, pooling
banks.

---

# 9. Audit rules

1. **Evidence priority.** raw generations → raw judge rows → raw activation artifacts → run
   configs/argv → independent re-derivation → claim ledger → progress log → report prose. **Never
   verify one summary against another summary.**
2. **Every headline number is independently re-derived** from raw artifacts. The most important
   result gets **two** independent re-derivations. Two scripts importing the same helper are **not**
   independent.
3. **Independent verifier** in the spirit of `scripts/rbd_verify_independent.py`: does not import the
   producing analysis module; reads raw artifacts; recomputes the estimand; checks population ids,
   denominator, pairing, domain counts, expected n. Minimal dependencies.
4. **Quantifier / scope audit.** Every deep review greps the sprint's documents for
   `all|every|both|exactly|inert|preserved|replicated|generalizes|model-independent|domain-independent|matched|identical`
   and asks of each occurrence only: **does this name its population?** A true number under a false
   quantifier is a false claim.
5. **Correction discipline — a correction is a NEW CLAIM.** For every `RAH-C-###`:
   (a) independently recompute the corrected value; (b) grep every document for the old wording;
   (c) fix tables **and** the prose people quote; (d) re-read the new sentence for scope/quantifier
   errors; (e) have a separate read-only auditor inspect the correction itself.
   *The predecessor sprint's correction pass was its single largest source of new error.*
6. **Liveness contracts.** Every intervention/patch declares required-positive counters,
   required-zero counters, expected row count, model-specific layer range, and prefill/decode
   semantics. A **missing counter fails**. `stats.get(key, 0)` is banned for a required-zero
   scientific field: **missing ≠ zero**.
7. **Every new guard must prove it can fail**: a passing test, an *executed* mutation that makes it
   RED, a minimum-count assertion, a production-wiring test, a missing-key test, and where possible
   the intended bad historical case. A guard matching zero rows and passing is a **defect**. A guard
   never called is a **defect**. A guard that fires on valid in-flight runs is also a defect.
8. **Smoke tests are not pilot science.** Smokes validate shapes, hooks, masks, liveness, row counts,
   artifact metadata, GPU compatibility. The scientific plan is fixed **before** the smoke. An 8-row
   effect direction never alters the plan.
9. **Full test suite runs serially and exclusively** — never concurrently with another suite, agents
   editing tracked files, tests mutating committed artifacts, or report generation. `git status`
   before and after; verify no tracked artifact changed. Order-dependent behaviour is investigated,
   not re-rolled. Stale test counts are never quoted.
10. **~30-minute loop**: SLURM → logs → run completeness → liveness → expected n → repo status →
    concurrent-edit check → update this file → check next action against preregistration → do not
    branch into new hypotheses on partial data.
11. **~4-hour deep review** (`RAH-DR-###`), read-only subagents in parallel: **A** intervention/code
    (mask coordinates, capture site, patch site, prefill/decode, KV-cache, batching, token indices,
    layer bounds, stale state, hook firing, receiver construction) · **B** measurement (binding,
    transport, benign mapping use, ASR, option mass, truncation, judge provenance, completion joins)
    · **C** population/statistics (independence units, headroom, selection rule, dev/confirm leakage,
    domain independence, equivalence, multiplicity, p-floor, denominators) · **D** claim auditor
    (destroy every headline from raw data; hunt false quantifiers) · **E** correction auditor
    (corrections since the last tick — corrections do not audit themselves).

## 9.1 The ASR filtering rule — ABSOLUTE

The primary ASR estimator uses the **COMPLETE** preregistered population. Primary ASR is **never**
computed after dropping truncated rows, non-EOS rows, short answers, "unscorable" answers, refusals,
incoherent rows, low-option-mass rows; never after conditioning on both arms finishing; never after
selecting domains with baseline attacks or dropping domains with an unexpected sign; never after
dropping prompt families post-generation.

Any analysis conditioning on a post-treatment variable is labelled, in the artifact and in the prose:

```
POST-TREATMENT DIAGNOSTIC — NOT AN ESTIMATOR
```

and may never replace or reword the headline.

## 9.2 Self-auditing ASR table — structural requirement

The code must be **structurally unable** to emit a headline ASR without: expected n · generated n ·
judged n · joined n · missing ids · duplicated ids · baseline attacks num/den · arm attacks num/den ·
paired down/up/both/neither · domain-level effects · fraction at cap · EOS fraction · median
generated tokens · token-length quantiles · refusal-marker rate · degeneracy/coherence diagnostic ·
intervention liveness · total intervention edits · judge model · judge session · completion-hash join
· development-vs-confirmatory label.

## 9.3 Cap rule

Cap is verified on **development** data and then frozen (the predecessor's cap = 640 gave 5 cap-bound
rows in 1600 — that standard is kept). If a primary confirmatory arm materially hits the cap, declare
`CAP-INVALID FOR PRIMARY INTERPRETATION`; then either stop, or raise the cap and **regenerate
baseline and every primary comparator at the new cap and judge them together**, replacing the old
comparison. **Never** compare baseline at cap X against an arm at cap Y.

## 9.4 Judge protocol

One pinned judge model; `judge_model_used` recorded per row; 100 % completion-hash joins; **all arms
of a primary comparison judged in the same invocation/session**; headline values never joined across
judge sessions; raw judge outputs preserved; re-judge instability measured on byte-identical text;
effect reported in raw rows as well as rates. If the causal effect is comparable to judge churn, say
so. Never tell a prompt-level story from individual flip identities when the judge flips those
identities at a similar rate.

## 9.5 Bank validity — before any generation

Strict grammar · tokenisation on **both** models · exact codeword occurrence · exact concept
occurrence · article a/an correctness · lexical collision · family alignment · condition structural
equality · demonstration integrity · duplicate detection · domain counts · role-style balance ·
`n_examples` balance · prompt-length distribution · token-position distribution · codeword/concept
token-count diagnostics. **A failing bank is fixed, never statistically adjusted around.**

---

# 10. Implementation plan

## 10.0 Phase map and gates

| phase | content | gate to the next phase |
|---|---|---|
| **P0** | repository & claim freeze (§11) | snapshot recorded here |
| **P1** | Qwen3 all-condition mapping-use control (cheap open item) | result recorded; **must not** expand into a new mechanism branch |
| **P1B** | execute `RBD-PR-005` **exactly as registered** | its verbatim text transcribed here **first**; then run; then close |
| **P2** | Track-A assay build: donor capture + receiver + patch, on **level-A discovery data only** | `CA1` passes, `CA3` moves the receiver, option mass ≥ gate, liveness complete, mutation tests RED |
| **P3** | Track-A Stage-A calibration on **level-A only** (§14) | smallest justified layer × position set chosen |
| **P4** | **Track-A FREEZE** (`RAH-PR-005`) — layers, positions, patch type, donor/receiver construction, primary readout, control family, statistical test, equivalence margin | freeze entry written and committed **before** any level-C forward pass |
| **P5** | Track-A diagnostic run on **level-B** (`lantern_poison`, `candle_missile`) — answers "what happened last sprint?" | DIAGNOSTIC only |
| **P6** | Track-A **confirmatory** run on **level-C** new material | primary Track-A claim |
| **P7** | Track-B power/sensitivity analysis + headroom threshold freeze (§20) | if the attainable sample cannot separate B-A from B-B, **redesign; do not run the matrix** |
| **P8** | Track-B screening-algorithm freeze, then **baseline-only** development screening | full candidate table (§22); population frozen |
| **P9** | Track-B confirmatory matrix (arms A–E) on the frozen population | outcome B-A/B-B/B-C/B-D |
| **P10** | join the tracks (§7.3), final claim matrix, reproduction manifest **executed**, handoff, sprint summary | sprint close |

**No expensive confirmatory GPU run starts before** instrument validation, power calculation,
population audit, preregistration freeze, code review, and a liveness smoke.

## 10.1 Track-A assay — architecture

The principle: **separate the activation that may contain the mapped concept from the downstream
prompt that turns it into a readable answer.** The donor state is captured **before any answer option
is ever shown**, so options in the receiver cannot have created the donor representation.

```
DONOR PROMPT                                RECEIVER PROMPT
(demonstrations installing codeword→concept) (standardised, safe, option-bearing)
(query context using the codeword)           ┌──────────────────────────┐
NO answer options anywhere                   │ ... <PLACEHOLDER> ...     │
        │                                    │ (A) …  (B) …  (C) …  (D) …│
        │ capture h at (layer L, position p) │ Answer: (                 │
        └───────────────► PATCH ────────────►└──────────────────────────┘
                                                        │
                                              read option logprobs at the answer slot
```

**Donor arms** (each produces a donor bank of activations, one per family):

| donor id | arm |
|---|---|
| `D-base` | baseline (no intervention) |
| `D-dpo` | `demo_processing_only` |
| `D-late` | late-band dose-matched control (`CA4`) |
| `D-shuf` | baseline activation from a **different family** (`CA2`) |
| `D-wrong` | baseline activation from a family carrying a **different concept** (`CA3`) |
| `D-rand` | matched-norm random direction (`CA5`) |
| `D-self` | identity/no-op patch path (`CA1`) |

Interventions are active **during donor prefill**, i.e. the donor is the intervened model's own
internal state. The receiver forward pass is **always unintervened** — the receiver is a fixed
measuring instrument, identical across all arms. This is what makes the arms comparable.

## 10.2 Donor capture — candidate sites (final set frozen at P4)

Layers (coarse, mechanistically justified, per model — exact indices filled from the P0 inventory):

* **`L-below`** — below the intervention band (control: information not yet written)
* **`L-band`** — top of the intervention/mechanism band (where the knockout acts)
* **`L-late`** — late control band

Positions (small, preregistered, only where implementation semantics make sense):

* **`p-demo-end`** — last token of the demonstration block
* **`p-codeword`** — last token of the codeword occurrence **in the query**
* **`p-final`** — final pre-response position

`p-codeword` is the mechanistically central site: it is where a codeword must retrieve its mapped
concept. **Position indices are computed per example from that example's own tokenisation.** The
absolute-position-index bug class — a position computed from `example[0]` reused as an absolute index
across examples — has hit this repository twice and is an explicit review item for `RAH-DR` Reviewer A.

## 10.3 Receiver — construction and error structure

The receiver is a fixed, safe, benign decoding prompt containing a placeholder token whose residual
is overwritten by the donor vector, followed by an explicit option list (so option mass is high and
the readout is statistically valid).

The option set is **4-way and diagnostic**:

| option role | example on `lantern↔poison` | what selecting it means |
|---|---|---|
| **mapped concept** | `poison` | the mapping transmitted |
| **literal meaning of the codeword** | `lantern` | the surface token transmitted, not the mapping |
| **other concept** | `missile` | wrong-concept confusion (and the target for `CA3`) |
| **other codeword** | `candle` | wrong-surface confusion |

Reporting **only** accuracy discards the mapped-vs-literal contrast, which is the sharpest available
evidence about *what* survives. `EA1` is therefore always reported as the full 4-cell distribution.

Option order is counterbalanced across families and the counterbalancing is part of the frozen assay.
Option **mass** (summed probability of the four option tokens at the answer slot) is gated exactly as
in the predecessor sprint; a receiver failing the mass gate is invalid, and a *cell* failing it is
`CANNOT ANSWER` for that cell.

## 10.4 Probe — SECONDARY only

A linear probe may be fit as a secondary diagnostic answering "is concept information linearly
decodable?" It cannot answer "is that information causally available", so it is **never** the primary
Track-A evidence. If used: family-disjoint train/test; lexical-pair-disjoint where possible; balanced
classes; no same-family leakage; shuffled-label control; isotropic/random-direction control;
calibration reported; never fit and evaluated on the same lexical material; high accuracy alone is
never mechanism evidence. A probe/transport disagreement is outcome **A-III**, not preservation.

## 10.5 Track-B implementation

Reuse the existing matrix machinery (bank generator → arm runner → `asr_protocol` → pinned judge →
`paired_equivalence` where relevant). New code is limited to:

* the **screening stage** (baseline-only, development, with the candidate table of §22), and
* whatever `asr_protocol` fields are missing from §9.2.

## 10.6 Reuse policy

Prefer small additive changes over new abstractions. Reuse: `demo_processing_only`, the late-band
scoped control, the patching/rescue infrastructure, `paired_equivalence.py`,
`mapping_use_forced_choice`, `scripts/rbd_bank_audit.py`, `scripts/rbd_verify_independent.py`,
`asr_protocol`, the completion-hash join, the pinned judge pipeline, the existing bank generator, the
strict tokenizer/alignment audits, and `external_repos/interp-jailbreak` surgical patching where
appropriate. **Do not break historical reproduction paths.**

---

# 11. SLURM and environment rules

* Interpreter: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`, unless the
  P0 inventory shows the documented project environment has legitimately changed (recorded here if so).
* Reuse existing submission infrastructure (`scripts/rbd_submit_wave.sh`, `slurm_scripts/`). No
  unnecessary wrappers.
* Parallelise only **scientifically independent** jobs; up to ~6 concurrent where safe.
* **At most TWO concurrent 14B weight loads** across the project unless current documented evidence
  supports otherwise (3 model loads on one node produced a 16× weight-load slowdown).
* No SLURM dependencies. L40S preferred; `a5000`/`3090` in killable when L40S is saturated.
* Do **not** `scancel` healthy queued jobs for being slow; do not resubmit duplicates; preserve
  fair-share position. Never cancel another user's job.
* A job PENDING > 30 min may be cancelled and resubmitted with a *different* config (e.g. widened
  nodelist); measure by `SUBMIT_TIME`, not `%M`.
* Liveness is `squeue`/`scontrol`. `sacct` is history and can report RUNNING on dead jobs.
* Argsfiles must live on the **shared** filesystem — the scratchpad `/tmp` path is node-local and
  jobs fail in ~3 s with "argsfile not found".
* `--export` comma-list values silently truncate; verify row counts after "COMPLETED".
* Inspect logs before diagnosing failure; "no output yet" ≠ stuck (use the weight-loading bar in
  `.err`). Check for existing DONE artifacts before launching compute.
* Shell hazards in this environment: backticks in `git commit -m` silently delete the word; unquoted
  `$VAR` does not word-split; `$var:x` is a zsh modifier. Build arg files with `printf` and grep them
  back.

---

# 12. Deliverables

1. **This file** — authoritative append-only sprint log.
2. **`RAH-*` claim ledger** — every claim with: status word · model · lexical pair · domains · n ·
   unit of independence · intervention · control · raw counts · effect · CI · p · corrected p ·
   p-floor · equivalence margin · headroom status · cap status · liveness status · judge provenance ·
   artifact paths.
3. **Development headroom-screen table** — **all** candidates, including failures.
4. **Activation-level assay report** — donor, receiver, capture position, patch position, controls,
   option mass, liveness, causal transport results.
5. **Paper-grade summary table** — counts + denominators + uncertainty. **No standalone headline
   percentages.**
6. **Reproduction manifest** — for every paper-level number: raw artifact, producing command,
   independent verifier, commit. **Executed** before sprint close.
7. **Updated `RESEARCH_HANDOFF.md`** — what survived, what failed, what is unresolved, what is
   diagnostic only, what must never be quoted, the exact next step.
8. **New standalone sprint summary** readable with no conversation context.

## 12.1 Final claim matrix (skeleton — populated at P10, one per model × confirmatory population)

| quantity | baseline | `demo_processing_only` | late control | interpretation |
|---|---|---|---|---|
| behavioural forced-choice binding | | | | |
| activation-level donor→receiver concept accuracy | | | | |
| activation-level concept margin | | | | |
| benign mapping use | | | | |
| refusal markers | | | | |
| harmful ASR | | | | |
| cap fraction | | | | |
| liveness | | | | |

Then exactly one of: **A** representation preserved / behaviour suppressed · **B** destroyed /
suppressed · **C** preserved / unchanged · **D** destroyed / unchanged · **E** measurement invalid.
**No prose may contradict this table.**

---

# 13. The scientific standard for this sprint

A clean negative beats a fragile positive. The goal is not a positive result and not the continuation
of a story; it is to learn which story is true. Failure modes this project has already paid for and
will not repeat: ASR filtering · post-treatment conditioning · low baseline headroom · fake power
from repeated domains · population contamination · lexical-pair selection by intervention outcome ·
dose mismatch · option-mass-invalid readouts · truncation · judge-session mixing · prompt-level
stories below judge noise · dead hooks · missing liveness counters read as zero · correction-pass
overstatements · false universal quantifiers · concurrent writers · layer fishing · objective-building
from a merely decodable quantity.

If an experiment cannot answer the question: **CANNOT ANSWER**. If a result fails to confirm:
**FAILED TO CONFIRM**. If a hypothesis is falsified: **FALSIFIED UNDER THIS DESIGN**. No prose rescue.

---

# 14. Progress checklist

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked · `[-]` declined/dropped

```
[~] P0   repository & claim freeze                          RAH-R-001
[ ] P0b  code inventory reconciled into this file           RAH-R-002
[ ] P1   Qwen3 all-condition mapping-use control            RAH-PR-002 / RAH-R-###
[ ] P1B  RBD-PR-005 transcribed verbatim                    RAH-PR-003
[ ] P1B  RBD-PR-005 executed as written, then closed        RAH-R-###
[ ] P2   donor→receiver assay implemented                   RAH-R-###
[ ] P2   assay validation: CA1, CA3, option mass, liveness  RAH-R-###
[ ] P2   mutation tests proven RED for every new guard      RAH-R-###
[ ] P3   Stage-A calibration on level-A data only           RAH-PR-004 / RAH-R-###
[ ] P4   TRACK-A FREEZE                                     RAH-PR-005
[ ] P5   Track-A diagnostic on level-B populations          RAH-R-###
[ ] P6   Track-A CONFIRMATORY on level-C new material       RAH-R-###
[ ] P7   Track-B power/sensitivity; headroom threshold      RAH-PR-006
[ ] P8   screening algorithm frozen                         RAH-PR-007
[ ] P8   baseline-only development screening + full table   RAH-R-###
[ ] P8   confirmatory population LOCKED                     RAH-R-###
[ ] P9   Track-B confirmatory matrix (arms A–E)             RAH-PR-008 / RAH-R-###
[ ] P10  joint 2x2 interpretation + final claim matrix      RAH-R-###
[ ] P10  reproduction manifest EXECUTED                     RAH-R-###
[ ] P10  RESEARCH_HANDOFF.md updated                        RAH-R-###
[ ] P10  standalone sprint summary                          RAH-R-###
[ ] DR   deep review ~every 4h                              RAH-DR-###
```

---
---

# LOG

Entries are appended below in chronological order. Nothing above this line is rewritten to say
something different; it is amended only by appended `RAH-C-###` entries.

---

## `RAH-PR-001` — sprint frame preregistered — 2026-08-30

**Status: CONFIRMATORY-FRAME (prospective).**

Everything in §0–§14 above is registered **before** any RAH-sprint model forward pass exists. In
particular the following are fixed now and may not be quietly changed after seeing results:
populations (§4), controls (§6), estimands (§2), statistical units (§3), success/failure logic (§7),
stopping rules (§8), the ASR no-filtering rule (§9.1), the cap rule (§9.3), the judge protocol (§9.4)
and the phase gates (§10.0).

Deliberately **left open** here, because they must be derived from data that is legitimately
development-only, each requiring its own freeze entry before the corresponding confirmatory run:

* the Track-A **layer × position** set → `RAH-PR-005` at P4, derived from level-A calibration only;
* the Track-A **equivalence margin** → `RAH-PR-005` at P4, derived from level-A receiver repeatability;
* the Track-B **minimum headroom / minimum meaningful effect / required rows and domains** →
  `RAH-PR-006` at P7, derived from a power analysis using conservative historical values;
* the Track-B **candidate pool and deterministic selection rule** → `RAH-PR-007` at P8, written
  before any baseline ASR for a candidate pair is inspected.

---

## `RAH-R-001` — Phase 0 repository freeze — 2026-08-30

**Status: DIAGNOSTIC (state record).**

```
branch          behavioral-causality-sprint
HEAD            fe8fd610da83772686016ff446dde004fc01710d
                "RBD: standalone sprint summary, built from twice-verified artifacts"
git status      CLEAN — 0 porcelain lines (no staged, no modified, no untracked)
SLURM           squeue -u $USER : EMPTY (no running, no pending jobs)
```

Latest 40 commits — `fe8fd610 … e783b6dd` — span the whole RBD confirmatory sprint
(`3c85dc36 RBD-PR-001/002: preregistration LOCKED` through
`fe8fd610 RBD: standalone sprint summary`), preceded by four `HANDOFF` commits
(`e783b6dd`, `10fcd035`, `4166a764`, `2f5623be`) recording the unaccounted-writer episode.

Authoritative documents located:

| document | path | mtime |
|---|---|---|
| RBD sprint summary | `reports/RBD_SPRINT_SUMMARY.md` | 2026-08-30 |
| RBD live progress log | `external_md/REPRESENTATION_BEHAVIOR_DISSOCIATION_CONFIRMATORY_SPRINT_PLAN_AND_PROGRESS.md` (252 KB) | Aug 30 16:59 |
| research handoff | `RESEARCH_HANDOFF.md` (48 KB) | Aug 30 16:58 |
| previous phase log | `external_md/DEMONSTRATION_RETRIEVAL_BEHAVIORAL_CAUSALITY_NEXT_PHASE_PLAN_AND_PROGRESS.md` (1.18 MB) | Aug 29 15:15 |
| session handoff | `HANDOFF_SESSION_2026-08-29_acbaec5b.md` | Aug 29 15:27 |

Artifact roots: `outputs/boombness/` (newest: `score_behavior`, `judge`, `logs`, `argsfiles` — all
Aug 30 ~04:30; `rbd_bank_audit.json` Aug 29 23:53; `rbd_readout_b_option_screen.json` Aug 29 16:33).

Code roots: `doublespeak_causality/` (numbered stage scripts incl. `05_run_activation_patching.py`,
`07_patchscope_readout.py`, `43_transplant_mediation.py`, `44_kv_mediation.py`,
`46_forced_choice_patchscope.py`, `50_path_patching.py`), `src/boombness/`, `scripts/` (`rbd_*`),
`tests/`, `slurm_scripts/`, `external_repos/interp-jailbreak`.

A read-only inventory fan-out (8 parallel inspectors: intervention implementation, patching
infrastructure, readouts & banks, ASR/judge/statistics, `RBD-PR-005` verbatim text, SLURM &
environment, tests & guards, handoff & open items) was launched at freeze time. **Its findings are
appended as `RAH-R-002` and no code is written before then.**

**Deviations from the brief's Phase-0 list, stated explicitly:** the brief asks for "staged files,
uncommitted files, unfinished run directories, newest claim ledger, newest correction/retraction
registry". Staged/uncommitted are empty (tree clean). Unfinished run directories, other-branch work,
and the ledger/registry locations are part of the pending inventory and are reported in `RAH-R-002`
rather than being guessed here.
