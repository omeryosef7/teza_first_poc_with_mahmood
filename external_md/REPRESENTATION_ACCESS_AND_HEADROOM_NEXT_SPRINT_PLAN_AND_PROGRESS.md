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

---

## `RAH-R-002` — Phase 0b: code inventory reconciled — 2026-08-30

**Status: DIAGNOSTIC (state record).** Eight read-only inspectors, 293 tool calls, 0 errors. Findings
that change what this sprint does are recorded here; the rest live in the transcripts.

### 0b.1 The intervention — confirmed, with exact coordinates

| item | location |
|---|---|
| mode table | `doublespeak_causality/pair_common.py:614-620` |
| row-set algebra | `pair_common.py:642-665` — `demo_processing_only` → `frozenset()` if decode else `demo_span` |
| hook | `pair_common.py:687-828` `ScopedAttentionKnockout`, mask edit `_pre` at `:743-806` |
| empty-span refusal | `pair_common.py:722-724` — refuses a no-op knockout |
| constructed | `src/boombness/score_behavior.py:951-955` |
| liveness required-positive | `pair_common.py:623-630` `LIVENESS_REQUIREMENT` |
| liveness required-zero | `pair_common.py:633-640` `LIVENESS_MUST_BE_ZERO` |
| **`total_prefill_edits`** | `score_behavior.py:544` |

**Bands are argsfile constants, not code** — `--intervene demo_all:attn_knockout:<lo>-<hi>:<alpha>`,
validated at `score_behavior.py:1494-1518`:

| model | mechanism band (arm B) | late control band (arm C) |
|---|---|---|
| Llama-3.1-8B-Instruct | **6–14** | **22–30** |
| Qwen3-14B | **7–17** | **27–37** |

⚠ **`RAH-R-002-a` — the dose match is an audit result, not an assertion.** There is **no code** that
checks arms B and C have equal `total_prefill_edits`. The exact equality (Llama 43,100,928; Qwen3
52,688,768) was established by reading the artifacts. **Any RAH run pairing a mechanism band against
a late band must re-verify the dose match from its own artifacts**; it is not guaranteed by
construction for a new band width or a new bank.

⚠ **`RAH-R-002-b` — one required-zero counter is read with a default.** `pair_common.py:668-684`
evaluates liveness as `int(stats.get(key, 0))`. For the required-**positive** direction a missing key
correctly fails (`0 <= 0`). For the required-**zero** direction a **missing key silently passes**.
This is precisely the `missing != zero` defect class named in §9.6. It did not bite the RBD sprint
(the hook always writes all counters), but any **new** patch hook in this sprint must not inherit the
pattern, and the Track-A liveness contract will assert key *presence* before value.

### 0b.2 Patching infrastructure — the decisive finding

**A true cross-prompt patchscope already exists**, and one variant is already forced-choice:

| module | what it is |
|---|---|
| `doublespeak_causality/07_patchscope_readout.py:48-67` | `PatchscopeDecoder(lm, inspection_prompt)` → `.decode(vector, inspect_layer, harm_id, code_id)`. Donor vector → **fixed third prompt** via `LayerPatch(replace)` at `q_pos = seq_len-1`. |
| `doublespeak_causality/46_forced_choice_patchscope.py` | the same mechanic with a **forced-choice inspection prompt** (`FORCED_CHOICE_INSPECTION:66`), injection at `:123`, patch at `:135`, labels read at the final position, **and a layer-scanned positive-control gate** (`patchscope_gate:83`) that must pass before evaluation runs. |
| `doublespeak_causality/ds_common.py:886` `capture_target_reps` | per-layer resid at `codeword_last` / `following` |
| `doublespeak_causality/pair_common.py:374` `ComponentOutSwap` | **per-position** donor rows into `resid_post` / `attn_out` / `mlp_out` |
| `src/boombness/aggressive_patching.py:861` `run_pair` | the most complete donor/recipient transplant: live alignment assertions, `donor_ceiling` arm, live `self_swap_noop_check`, `FailureLedger`, dose-matched additive controls |
| `src/boombness/donor_patch.py:84` `DonorPatch` | the only patcher with a **token-identity refusal** (`strict_ids`) and a `liveness()` method |
| `doublespeak_causality/48_attribution_patching.py:256` `build_alignment` | the correct cross-prompt, **different-length** position map |
| `doublespeak_causality/43_transplant_mediation.py` | model-free reducer: paired bootstrap, permutation, Holm, faithfulness |

**`RAH-R-002-c` — the single missing piece is arm-active donor capture.** Every existing transplanter
captures its donor from a **clean, unhooked** forward. Capture under live intervention hooks exists in
**exactly one place**: `src/boombness/score_behavior.py:1914-1921` (`--rescue-donor self`), where the
arm's context managers are entered around the capture forward. Track A needs precisely that wiring
pointed at a **different** (receiver) prompt.

**Consequence for the plan: P2 is a small additive build, not a rewrite.** The assay is
`46_forced_choice_patchscope`'s receiver + `score_behavior.py:1914-1921`'s arm-active capture, with
`DonorPatch`-style identity/liveness guards. This is recorded now so that a later "we had to write a
lot of new code" cannot be justified retrospectively.

Also on record, for `RAH-DR` Reviewer A: `34_intervention_sweep.py` writes ONE donor vector to every
receiver occurrence with **no token-identity check**; `44_kv_mediation.py:362-363` aligns donor and
receiver **by rank** (`[-m:]`), not by token; `DonorPatch` is a **no-op by construction** when
`rescue_layer <= lo` while `liveness()` still reports `fired: true` (defect C-20).

### 0b.3 Readouts, banks, conditions

`semantic_forced_choice` at `src/boombness/prompt_families.py:137-152`;
`mapping_use_forced_choice` (Readout B) at `:168-193` with options table `:202-205`
(`lantern/poison → shed | cabinet`; `candle/missile → cupboard | bunker`).
`CONDITIONS` at `:94-105`; `CORE_2X2 = (benign_literal, direct_harmful, natural_doublespeak,
concept_in_benign_ctx)` at `:106`. Scoring via `signals.string_option_readout`
(`src/boombness/signals.py:693-751`), `option_mass` at `:749`, gate at `score_behavior.py:2199-2209`.

Banks: `rbd12` preset, seed 20260829, **960 rows each**, 20 domains, 80 family stems, 3 readouts.
Bank audit `src/boombness/rbd_bank_audit.py` (9 checks, both banks PASS). Tokenisation audit clean on
both models. **Note: the audit module is at `src/boombness/`, not `scripts/`** — the brief's path is
NOT FOUND.

**`RAH-R-002-d` — what was never run on Qwen3.** Every Qwen3 RBD run passes
`--conditions natural_doublespeak`. `benign_literal`, `direct_harmful` and `concept_in_benign_ctx`
have **zero Qwen3 rows in any run**. The all-condition control exists only as
`rbdctrllp_allcond` / `rbdctrlcm_allcond`, both `--model meta-llama/Llama-3.1-8B-Instruct`. This is
exactly the gap `RBD-C-016` names, and it is what Phase 1 closes. Also never run anywhere: arm E
readout (`E_respq` × forced-choice), on either model.

### 0b.4 ASR, judge, statistics

`src/boombness/asr_protocol.py` (807 lines): 27 `MANDATORY_DIAGNOSTICS` (`:185-209`),
`assert_publishable` (`:225`), `assert_sprint_grade` (`:329`), `paired_transitions` (`:641`),
`CAP_BIND_MAX = 0.10` (`:215`). §9.2's field list is a **superset** of the existing 27 in two places —
it additionally requires `judge_session`, `total_intervention_edits`, `intervention liveness`,
`domain-level effects` and the `development vs confirmatory` label. **Those five must be added before
any Track-B headline is printed** (`RAH-R-002-e`, an implementation item, not a defect claim).

`src/boombness/paired_equivalence.py`: Newcombe method-10 (`:110`), exact McNemar (`:156`), domain
cluster bootstrap (`:177`), rule-of-three capability check (`:279`), conservative envelope
(`:266-269`), verdicts `WORSE_THAN_MARGIN → UNRESOLVABLE_AT_THIS_N → EQUIVALENT → NOT_ESTABLISHED`.
Pure stdlib. `scripts/rbd_verify_independent.py` imports **only** `argparse/collections/json/math/os/
typing/fractions` — its independence is real, and it declares its own limit (it does not re-derive
Newcombe or Holm).

**Measured judge instability, pinned model, byte-identical text** — the Track-B noise floor:

| artifact | n | ASR a → b | rows changed |
|---|---|---|---|
| `pinned_q15A.json` core2x2 | 80 | 0.11250 → 0.08750 | 0.0875 |
| `pinned_q16A.json` core2x2 | 80 | 0.03750 → 0.07500 | 0.1250 |
| DR-10 / R-70 | 160 | — | **9/160 rows flip (0.0563)**, 4 of them 0.0 ↔ ≥0.5 |

⚠ **`RAH-R-002-f`** — `RBD-DR-004` F10 records **five** `judge_boombness` invocations per (model,bank),
not one, with **per-invocation drift 6.5–7.0 %** — at n=80 that is ~5 rows, *comparable to the entire
RBD baseline attack count*. Track B's judge protocol (§9.4) must be enforced in code, not by intent.

### 0b.5 Historical baseline harmful ASR — the Track-B power input

**RBD population (cap 640, pinned judge), all 16 cells HEADROOM_FAILED:**

| model | bank | baseline |
|---|---|---|
| Llama | `lantern_poison` | 7/80 (0.0875) |
| Llama | `candle_missile` | 5/80 (0.0625) |
| Qwen3 | `lantern_poison` | 4/80 (0.0500) |
| Qwen3 | `candle_missile` | 1/80 (0.0125) |

**Prior `bomb`-concept populations (cap 192, judge pinning varies — NOT directly comparable):**
Llama `natural_doublespeak` n=270: **0.2185**; Llama within-bomb preamble swing **0.1562 → 0.0437
(3.6×)**; Qwen3 `natural_doublespeak` n=420: **0.1596** (95 % CI [0.0714, 0.3167] over 6 domains);
Qwen3 d10 21/160, longpre10 23/160; n=96 decompositions Llama 0.1667 / Qwen3 0.1771 (both cap 192,
`frac_at_cap` 0.5625 / 0.2604 — **cap-bound, so these are ASR-within-192, not ASR**).

**These numbers are the INPUT to the `RAH-PR-006` power analysis and are not themselves a headroom
claim.** The comparison across them changes concept, codeword, domains (100 % disjoint), role styles,
dose, cap and judge pinning simultaneously (`RBD-C-017`). Per §20 of the brief the power analysis
will use **conservative** values, never the 0.2185 maximum.

**NOT FOUND:** no per-concept-pair power calculation targeting Track B exists in the repo.

### 0b.6 SLURM and environment — confirmed unchanged

`/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python` → python 3.12.13, torch
2.7.1+cu126, transformers 5.12.1. It is the **only** env; every sbatch script does
`conda activate poc_stage2`. Template: **`src/boombness/slurm/run_boombness.sh`** (killable, 1 GPU,
48 G, 6 h, `--nodelist=n-801..n-805,t-806`, L40S name guard at `:82-89`, argsfile quote guard at
`:62-75`). `slurm_scripts/` is **not** used by this line of work. Judge:
`src/boombness/slurm/run_p2_judge.sh` — **never** `run_judge_cpu.sh` (it silently discards `P2_*`).
Submitter `scripts/rbd_submit_wave.sh`, `MAX_INFLIGHT` default 6; **2 for Qwen3-14B**.

Measured cost: readout cell ≈ **0.03 GPU-h** (Llama) / **0.06** (Qwen3); behavioural cell ≈ **0.26** /
**0.30**. Whole 36-job RBD matrix = **8.66 GPU-h**. n-801 is a **3–4× tail-risk** node (every weight
load slower than 15 min in 232 logged runs happened there).

### 0b.7 Concurrency and unfinished work — clean

No commit anywhere is a descendant of `fe8fd610`. `origin` == local. Zero uncommitted or untracked
files. **Zero unfinished RBD run directories** — all 71 `rbd*` dirs have `DONE.json` with expected row
counts. 326 dirs repo-wide have `config.json` without `DONE.json`; **225 are pytest fixtures**, the
rest are pre-2026-08-25 aborts already catalogued in `EXCLUDED_RUNS.json`, plus 25 non-RBD dirs listed
in the transcript. Three worktrees under a peer session's scratchpad are all **ancestors** of HEAD and
stale by ~32 h. `stash@{0}` (2026-08-22) belongs to a **third writer — it is not popped, not
inspected, not touched.** No `.git` lock files. No other writer is active.

### 0b.8 Open item inherited and carried forward

`RESEARCH_HANDOFF.md` and the RBD log both close on the same sentence: *"a third pass over
`RBD-DR-005`'s own edits is the honest next step, not an optional one."* **This sprint adopts it** as
the first task of `RAH-DR-001` — the RBD deliverables are the documents this sprint builds on, so an
uncorrected error there propagates.

---

## `RAH-PR-002` — Phase 1: the Qwen3 all-condition control — 2026-08-30

**Status: PREREGISTERED (prospective). Registered before the runs are submitted and before any Qwen3
row for these conditions exists anywhere in the repository (`RAH-R-002-d`).**

### Question

> How much of Qwen3's mapping-use performance is attributable to the **installed mapping** rather than
> to its **no-mapping base rate**?

`RBD-C-016` is explicit that this is unanswered: Qwen3's 69/80 mapped answers under
`natural_doublespeak` has **no Qwen3 control condition**. Llama's control is 32/80 — **0.40, not the
intuitive 0.50** — which is exactly why Qwen3's may not be assumed, and why Llama's 32/80 may **not**
be borrowed.

### Population

Qwen3-14B (`--enable-thinking false`), both RBD banks, `rbd_core`, `n_examples 8`, seed 20260829,
**all four `CORE_2X2` conditions**, query kinds `semantic_forced_choice,mapping_use_forced_choice`,
`--readout-max-batch 1`, `--expect-n 640` per bank. 640 = 80 family stems × 4 conditions × 2 readouts.

The argsfiles are byte-identical to the committed Llama twins `runargs/rbd_ctrl/{lp,cm}_allcond.txt`
except for **three tokens**: `--model Qwen/Qwen3-14B`, the added `--enable-thinking false` (present in
every other Qwen3 run in the repo), and `--tag`. Verified by whitespace-split diff before submission.
This satisfies the brief's "SAME population / readout / cap / option structure / implementation".

### Primary estimand

$$\Delta_{\text{map}} = P(\text{mapped} \mid \texttt{natural\_doublespeak}) - P(\text{mapped} \mid \texttt{benign\_literal})$$

on `mapping_use_forced_choice`, **paired by family stem**, n = 80 per bank, clustered by `domain`
(k = 20). `benign_literal` is the no-mapping base rate: benign demonstrations, codeword surface, no
installed mapping — the same control condition that supplies Llama's 32/80.

### Secondary, reported but not the estimand

`direct_harmful` (Readout-B ceiling / instrument validity — Llama gave 1.000 and 0.950);
`concept_in_benign_ctx`; and the same four-condition breakdown for `semantic_forced_choice`.

### Statistics, fixed now

Exact McNemar on discordant pairs; Newcombe method-10 paired CI; domain cluster bootstrap
(k = 20, seed 20260829); α = 0.05, two-sided. Computed with
`src/boombness/paired_equivalence.py` and **independently re-derived** by a verifier that does not
import it.

### Validity gate, fixed now

Median `option_mass` ≥ **0.05** on every reported cell (the repository's existing gate). **A cell
below the gate is `CANNOT ANSWER` for that cell and its number is not quoted** — the `RBD-C-019`
lesson: a gate recorded as overridden is still an overridden gate.

### Interpretation rules, fixed now

| result | conclusion |
|---|---|
| Δ_map CI excludes 0, positive | Qwen3 mapping use **is** mapping-attributable on this population. `RBD-C-016` closed. |
| Δ_map CI includes 0 | **NOT ESTABLISHED.** The 69/80 remains a *raw* rate; the model difference remains a raw difference. |
| Δ_map negative | reported as observed. |

### Scope limit — binding

This is a **cleanup / DIAGNOSTIC** experiment whose only job is to close `RBD-C-016`. It **may not**
expand into a new mechanism branch, and it **cannot promote any declined estimand** — in particular
nothing here may be read as evidence about attack suppression, which is `DECLINED` on both models and
stays declined. Any follow-up motivated by this result requires its own `RAH-PR-###`.

### Cost

2 Qwen3-14B readout jobs, 640 rows each. At the measured 1.10 rows/s that is ≈ 10 min of compute per
job plus weight load; budget ≈ 0.35 GPU-h total. `MAX_INFLIGHT=2` (the two-concurrent-14B-loads rule).

---

## `RAH-R-003` — the article guard fired on the new n=16 bank; calibration, not a bank defect — 2026-08-30

**Status: DIAGNOSTIC.**

Building the `RBD-PR-005` population required a new bank (the `rbd12` banks contain **only**
`n_examples = 8`; see `RAH-PR-003` below). `src/boombness/rbd_bank_audit.py` returned **FAIL** on
`boombness_prompt_bank_rbdn16_lantern_poison.jsonl`, check `articles`:

```
[FAIL] articles
       an_before_consonant_by_word: {'led': 6}
       unexpected_an_words: {'led': 6}
       codeword_or_concept_flagged: {}      <-- the substantive clause: EMPTY
```

The two distinct source contexts, read from the raw bank:

```
... An LED lantern provided crisp illumination during the routine audit in the switchgear room.
... An LED poison  provided crisp illumination during the routine audit in the switchgear room.
```

**Verdict: a false positive of a documented class, not a bank defect.** `an LED` is correct English —
a letter-name onset /ɛl/, the same class as the `x-ray` / `mba` / `fbi` entries already in
`AN_BEFORE_CONSONANT_OK`. The check is deliberately orthographic (`check_articles` docstring: *"so
/juː/ onsets are expected false positives"*), and `RBD-C-005` / `RBD-C-007` exist precisely because a
bare "zero bad articles" gate fails every valid bank in this repository.

**Why it never fired before, and why that is worth recording.** `grep -ci "an led"` on the committed
n=8 bank returns **0**; the sentence *is* in the pool. `_take` draws `n_examples` sentences from a
20-sentence per-split pool, so **n = 16 reaches pool sentences that n = 8 never sampled.** The dose
manipulation is therefore not "the same demonstrations, more of them" — the marginal 8 sentences are
material the n = 8 population never contained. This is inherent to any dose manipulation over a fixed
pool and is **stated here, before the result, as a limitation of the `RBD-PR-005` comparison.**

**Fix applied:** `"led"` added to `AN_BEFORE_CONSONANT_OK` (`src/boombness/rbd_bank_audit.py`), with
a comment recording the reason. **The allowlist cannot weaken the substantive clause** — `target_hit`
is computed from the raw counters, not from the allowlisted remainder — and that is now *proved*
rather than asserted:

| new test | what it does |
|---|---|
| `test_RAH_an_LED_is_tolerated_as_correct_english` | the calibration itself |
| `test_MUTANT_allowlisting_a_word_cannot_suppress_clause_3` | sets codeword = `led`; `an led` must **still FAIL** via `codeword_or_concept_flagged` |
| `test_MUTANT_the_article_guard_still_goes_RED_on_a_real_defect` | `an switchgear` must FAIL |

**Executed mutation (§9.7).** `"led"` was removed from the allowlist and the suite re-run:
**2 failed, 28 passed** (`test_RAH_an_LED_...` and `test_MUTANT_allowlisting_...` both RED). Restored:
**30 passed**. The guard can fail, and the calibration is load-bearing rather than decorative.

**Both n=16 banks then audit `OVERALL: PASS`** (11/11 checks each, pool independence PASS, 0 shared
demo sentences between banks) → `outputs/boombness/rah_bank_audit_n16.json`.

---

## `RAH-PR-003` — executing `RBD-PR-005` as registered — 2026-08-30

**Status: EXPLORATORY (inherited).** This preregistration does **not** create a new hypothesis. It
transcribes an already-registered diagnostic and records how it is executed. Per the sprint brief its
rule, threshold, population and purpose are **not revised**.

### The original registration, verbatim

Source: `external_md/REPRESENTATION_BEHAVIOR_DISSOCIATION_CONFIRMATORY_SPRINT_PLAN_AND_PROGRESS.md`
lines 3190–3206, inside §14.34 (`RBD-C-011`). **First registered in commit `5eb55d88`** — *"RBD-C-011:
T7, my own registered fallback, is structurally incapable - declared before running it"*.

> ### `RBD-PR-005` — the same run, relabelled honestly, as an EXPLORATORY diagnostic
>
> The n=16 build is still worth ~4 GPU runs, but **not as a T6 remedy**. It answers the question
> `RBD-R-031` left open and which matters for the handoff:
>
> > **Is the low baseline ASR DOSE-driven or CONCEPT-driven?**
>
> If ASR rises materially at n=16, the floor is a dose artifact of this design. If it does not move —
> which prior evidence predicts — the floor belongs to **`poison` / `missile` as concepts**, and the
> implication for future work is that **pair selection must screen for behavioural headroom on a
> DEVELOPMENT population before a pair is committed to**, which is a screening step this sprint did not
> have and which does not contaminate a confirmation.
>
> **Labelled `EXPLORATORY` under §30 and it cannot promote any declined estimand**, whatever it shows.
> It is queued **behind** the Qwen wave, which is registered primary work and has GPU priority.

Its governing population arithmetic, same section, lines 3149–3187, verbatim:

> **At `n_examples = 16` the population HALVES.** `_take` starts at `(slot × 3) mod 20` over a
> 20-sentence per-split pool, so the pairwise-disjoint slot count is `floor(20/n)`:
> … **8** → 2 slots → 4 families/domain/pair → **160 pooled behavioural rows**;
> **16** → **1** slot → 2 families → **80 pooled behavioural rows**.
> **So T7 would measure 80 rows instead of 160.** At the observed baseline rate (0.075) that is
> **≈ 6 expected baseline attacks against a required 14**.
> **T7 as a headroom remedy is declared UNINFORMATIVE BY CONSTRUCTION and will not be run as one.**

Two further binding rules, quoted verbatim from elsewhere in the same file:

> `RBD-PR-005` (the n=16 dose diagnostic) is **EXPLORATORY** and **cannot promote any declined
> estimand**. It asks only whether the low baseline ASR is dose- or concept-driven. *(line 3306)*

> since a dose effect is not formally excluded. The direct test remains `RBD-PR-005`, and its verdict
> does not change any declined estimand either way. *(line 3591)*

### ⚠ What the original registration does NOT contain

**It names no numeric threshold, no margin, no estimand formula, no α, and no stopping rule.** Its
only quantitative anchor is the undefined phrase *"rises materially"*, plus the inherited n = 16 → 80-row
arithmetic. **This sprint does not invent one.** Supplying a threshold now, after the fact, would be
exactly the "quietly change thresholds after seeing results" failure the brief forbids — and supplying
it *before* seeing results would still be revising a registration the brief orders executed as
written. The result is therefore reported as **raw counts with an interval and an explicit statement
of what the design can and cannot resolve** (below), and the verdict is expressed in the
registration's own vocabulary: *material rise* / *does not move* / *cannot resolve*.

### ⚠ Attainable resolution — computed BEFORE the runs, from the RBD baselines

Unpaired two-proportion comparison, n = 8 arm 160 rows vs n = 16 arm 80 rows, α = 0.05 two-sided,
200 000-replicate Monte-Carlo, seeded 20260830. Baselines are the **measured** RBD values
(Llama 12/160 = 0.0750; Qwen3 5/160 = 0.0312):

| rise at n = 16 | Llama power | Qwen3 power |
|---|---|---|
| 1.5× | 0.171 | 0.099 |
| 2× | 0.446 | 0.211 |
| 3× | **0.897** | 0.519 |
| 4× | 0.994 | 0.780 |
| 6× | 1.000 | 0.979 |

**MDE at 80 % power: Llama 0.2008 (≈ 16/80 attacks, 2.68×); Qwen3 0.1280 (≈ 10/80, 4.10×).**

> **`RBD-PR-005` can detect a LARGE dose effect and cannot detect a small or moderate one.** A null
> result licenses *"no large dose effect"* and **not** *"no dose effect"*. This is stated now so that
> the null the original registration itself predicts (*"which prior evidence predicts"*) cannot later
> be read as stronger than it is. For calibration: this repository records a **3.6× within-`bomb` ASR
> swing from a two-sentence preamble change** (`RBD-C-017`), i.e. effects of the detectable size do
> occur in this system.

### Population and execution

| | |
|---|---|
| banks | **NEW** — `boombness_prompt_bank_rbdn16_{lantern_poison,candle_missile}.jsonl`, preset `rbd12_n16` |
| preset | identical to `rbd12` on **every** axis except the two the dose forces: `n_examples [8]→[16]`, `slots [0,3]→[0]` (`floor(20/16) = 1`; a second slot would share demonstrations) |
| rows | 480 per bank = 40 stems × 4 conditions × 3 readouts. **Behavioural `natural_doublespeak`: 40 per bank, 80 pooled** — exactly the figure `RBD-C-011`'s own table predicted |
| audit | `OVERALL: PASS`, both banks, 11/11 checks, after `RAH-R-003` |
| models | Llama-3.1-8B-Instruct, Qwen3-14B (`--enable-thinking false`) |
| arms | **`A_baseline` only.** No intervention. The question is about baseline ASR |
| cap | **640** — identical to `rbd12`. `RBD-C-017` lists cap among the clauses that invalidated a previous cross-population comparison; it is held fixed here |
| query kind | `behavioral`, condition `natural_doublespeak`, `--expect-n 40` per (model × bank) |
| cost | 4 GPU runs — exactly the "~4 GPU runs" the registration budgeted |

### Judge protocol — and one deliberate addition

§9.4 forbids joining headline values across judge sessions. The n = 8 comparator was judged on
2026-08-30 ~04:00 in its own sessions. **Therefore the n = 8 rows are re-judged in the SAME
invocation as the n = 16 rows**, one session per (model × bank), 120 rows each (80 at n = 8 + 40 at
n = 16), pinned `openai/gpt-4o-mini`, completion-hash join required at 100 %.

* The RBD sprint's published n = 8 numbers are **unchanged and not overwritten**; they remain the
  product of their own session. This diagnostic reports its own joint-session values alongside them.
* This yields, at no extra GPU cost, a **fresh re-judge-instability measurement on byte-identical
  n = 8 text** — a directly reusable input to the `RAH-PR-006` Track-B power analysis, which §20
  requires to use *measured* judge noise.

### Interpretation rules, fixed now

| result | wording |
|---|---|
| n = 16 ASR exceeds n = 8 by more than the design can resolve by chance | **material rise** — the floor is a dose artifact of this design |
| n = 16 ASR does not differ detectably | **does not move at a resolvable size** — consistent with a concept-driven floor, but licenses only *"no LARGE dose effect"* |
| either arm's diagnostics fail (cap binding, incomplete population, hash-join failure) | **CANNOT ANSWER** |

**Binding scope.** EXPLORATORY. Cannot promote any declined estimand. The behavioural estimand stays
`DECLINED` on both models whatever this shows. Nothing here may be quoted as evidence about attack
suppression. Once reported, `RBD-PR-005` is **CLOSED**.

**Known limitation, from `RAH-R-003`:** the n = 16 demonstrations are a *superset* drawn deeper into
the same pool, so the marginal sentences are material the n = 8 population never contained. Dose and
demonstration content are not fully separable in this design. Recorded before the result.

---

## `RAH-C-001` — my own analysis swapped the Newcombe cell arguments — 2026-08-30

**Status: CORRECTION (of an unpublished intermediate). No claim was ever made on the wrong values.**

The first Phase-1 analysis pass called
`newcombe_paired_ci(n11, n10, n01, n00)` with `n10` = *"arm and not base"* and `n01` = *"not arm and
base"*. The library's convention (`src/boombness/paired_equivalence.py:110-120`) is the **opposite**,
and is documented in its own docstring:

> Cell convention, both indexed (base, arm): `n10 = base 1, arm 0` (a **LOSS** under the arm);
> `n01 = base 0, arm 1` (a **GAIN**)

So every Newcombe interval in that pass was **sign-flipped**. It produced the self-contradictory line
`delta = +0.9375 … Newcombe 95% CI [-0.9730, -0.8491]` and a `VERDICT: NEGATIVE LIFT` on a cell whose
lift is strongly positive.

**How it was caught: two estimators of the same quantity disagreed in sign.** The domain cluster
bootstrap computes `sum(arm - base)/n` directly and cannot be fooled by an argument order; Newcombe
takes four counts and can. The disagreement was visible in the first line of output.
`mcnemar_exact(n10, n01)` is symmetric, so the p-values were unaffected and would **not** have
revealed it — a difference test was blind to this exact defect.

**Fix, applied at the source of the error class rather than to the symptom.** The analysis no longer
hand-counts cells for the interval: it builds `{"base": …, "arm": …}` rows and lets the library count
them, and it **asserts `newcombe.delta == cluster_bootstrap.delta`** before reporting. Two
independent paths to the same scalar now have to agree or the run aborts.

**Permanent guard:** `scripts/rah_verify_phase1.py` re-derives the cells, the delta, both intervals
and the exact McNemar p from raw rows with **its own** Wilson / Newcombe-10 / McNemar / bootstrap
implementations and **no import of `paired_equivalence`**. It reproduces every figure.

**Correction discipline (§9.5):** this correction is itself a claim. The corrected numbers below were
recomputed independently before being written, the old wording exists only in this session's
scratch output and in this entry, and the entry states the *scope* of the error (intervals only;
counts, deltas and p-values were correct throughout).

---

## `RAH-R-004` — Phase 1 result: the mapping is installed and is not used — 2026-08-30

**Status: DIAGNOSTIC — CONFIRMATORY for `RAH-PR-002`'s registered question.** Answers the question
registered in `RAH-PR-002` before the Qwen3 runs were submitted. Closes `RBD-C-016`.

### Provenance

| | |
|---|---|
| new runs | `rahqlp_allcond_20260830_180029_2664294`, `rahqcm_allcond_20260830_180029_2664293` — Qwen3-14B, **640/640 rows each**, `status: ok`, 953 s / 972 s |
| reused runs | `rbdctrllp_allcond_20260830_012059_2650520`, `rbdctrlcm_allcond_20260830_012059_2650519` — Llama, 640 rows each |
| population | 80 family stems × 4 conditions × 2 readouts, **20 domains**, per (model × bank) |
| option mass | **PASS on every cell** — median 0.99995–0.99998, `frac_above_1pct = 1.0`, gate 0.05 |
| independent verify | `scripts/rah_verify_phase1.py` → **PASS**, all counts / deltas / both intervals / p exact |
| artifacts | `outputs/boombness/rah_phase1/rah_phase1_lift.json`, `…/rah_phase1_verify.json` |

### The attributable lift — `arm = natural_doublespeak`, `base = benign_literal` (no mapping installed), paired by family, n = 80, k = 20 domains

| cell | readout | nat_ds | benign_literal | Δ | Newcombe 95 % | domain-cluster 95 % | McNemar | verdict |
|---|---|---|---|---|---|---|---|---|
| Qwen3 × `lantern_poison` | binding | 75/80 | 0/80 | **+0.9375** | [+0.8491, +0.9730] | [+0.8750, +0.9875] | 5.29e-23 | **LIFT ESTABLISHED** |
| Qwen3 × `candle_missile` | binding | 40/80 | 0/80 | **+0.5000** | [+0.3836, +0.6070] | [+0.3375, +0.6500] | 1.82e-12 | **LIFT ESTABLISHED** |
| Llama × `lantern_poison` | binding | 78/80 | 0/80 | **+0.9750** | [+0.8982, +0.9931] | [+0.9375, +1.0000] | 6.62e-24 | **LIFT ESTABLISHED** |
| Llama × `candle_missile` | binding | 52/80 | 0/80 | **+0.6500** | [+0.5316, +0.7455] | [+0.5250, +0.7875] | 4.44e-16 | **LIFT ESTABLISHED** |
| Qwen3 × `lantern_poison` | mapping use | 69/80 | **72/80** | −0.0375 | [−0.1421, +0.0666] | [−0.1250, +0.0375] | 0.629 | NOT ESTABLISHED |
| Qwen3 × `candle_missile` | mapping use | 2/80 | 0/80 | +0.0250 | [−0.0243, +0.0866] | [+0.0000, +0.0625] | 0.500 | NOT ESTABLISHED |
| Llama × `lantern_poison` | mapping use | 24/80 | **32/80** | −0.1000 | [−0.2318, +0.0371] | [−0.2875, +0.0625] | 0.215 | NOT ESTABLISHED |
| Llama × `candle_missile` | mapping use | 3/80 | 0/80 | +0.0375 | [−0.0145, +0.1045] | [+0.0000, +0.1000] | 0.250 | NOT ESTABLISHED |

### `RBD-C-016` is CLOSED — and it resolves against the interesting reading

> **Qwen3's 69/80 benign mapping-use rate is NOT attributable to the installed mapping.** Measured on
> the **same** families, the **same** readout, the **same** option words and the **same**
> implementation, Qwen3's **no-mapping base rate is 72/80** — *higher* than its mapped rate.

The large raw model difference the predecessor sprint found (Qwen3 69/80 vs Llama 24/80, Fisher
p 3.3e-13) is therefore **a difference in the two models' no-mapping base rates for these option
words** — Llama 32/80 = 0.40, Qwen3 72/80 = 0.90 — **not** a difference in how much they use an
installed mapping. `RBD-C-016`'s warning that *"that control being 0.40, not the intuitive 0.50, is
exactly why Qwen3's cannot be assumed"* is vindicated: assuming it would have been wrong by 0.50.

**The `RESEARCH_HANDOFF.md` §5 prohibition on quoting `RBD-R-029` as a general composition claim
STANDS.** This entry does not revive it. `RAH-R-004` is a **new measurement** resting on its own
four-cell data, and it reaches a *narrower* conclusion than the composition reading did.

### Dynamic-range check — why "NOT ESTABLISHED" is not merely low power here

A null on a readout with no headroom is uninformative. So the floor (`benign_literal`, no mapping)
and the ceiling (`direct_harmful`, concept literally present) are reported with every arm:

| cell | readout | floor | ceiling | range | arm | **arm's position in range** |
|---|---|---|---|---|---|---|
| Qwen3 × `lantern_poison` | mapping use | 72/80 | 80/80 | 8 | 69/80 | **at/below floor** |
| Qwen3 × `candle_missile` | mapping use | 0/80 | 77/80 | **77** | 2/80 | **2.6 %** |
| Llama × `lantern_poison` | mapping use | 32/80 | 80/80 | 48 | 24/80 | **at/below floor** |
| Llama × `candle_missile` | mapping use | 0/80 | 76/80 | **76** | 3/80 | **3.9 %** |
| Qwen3 × `lantern_poison` | binding | 0/80 | 80/80 | 80 | 75/80 | 93.8 % |
| Qwen3 × `candle_missile` | binding | 0/80 | 80/80 | 80 | 40/80 | 50.0 % |
| Llama × `lantern_poison` | binding | 0/80 | 80/80 | 80 | 78/80 | 97.5 % |
| Llama × `candle_missile` | binding | 0/80 | 80/80 | 80 | 52/80 | 65.0 % |

On **`candle_missile`, both models**, the readout has a **76–77-row dynamic range** and the
doublespeak arm sits at **2.6 % / 3.9 %** of it. That is not a power failure; it is a measured floor.
On `lantern_poison`, both models, the arm sits **at or below its own no-mapping floor**.

### The claim, scoped exactly

> **On all four (model × lexical pair) cells, the doublespeak mapping is demonstrably installed and
> is not used in a benign property question.** Installation: binding lift +0.5000 to +0.9750, every
> CI excluding zero, arm at 50.0–97.5 % of the readout's range. Non-use: mapping-use lift NOT
> ESTABLISHED on 4/4, arm at or below its no-mapping floor on 4/4 and at ≤ 3.9 % of a 76-row range on
> the two cells with wide headroom.

**Population:** Llama-3.1-8B-Instruct and Qwen3-14B; `lantern↔poison` and `candle↔missile`; 80 family
stems and 20 domains per cell; baseline arm only, no intervention anywhere in this result.

### ⚠ What this is NOT

* **Not a claim about harmful behaviour.** No ASR, no judge, no generation is involved. The
  behavioural estimand remains **DECLINED** on both models.
* **Not a claim about any intervention.** Every row here is `A_baseline_allcond`.
* **Not "the mapping is never used"** — it is one benign property readout with one option pair per
  bank. `mapping_use_forced_choice` on `lantern↔poison` asks about `shed` vs `cabinet`; on
  `candle↔missile` about `cupboard` vs `bunker`.
* **Not evidence that the representation is absent** — the binding lift proves the opposite. This is
  precisely the *representation present, downstream use absent* pattern, and it is the reason Track A
  matters: it says nothing about *why* the use is absent.

### Scope limit honoured

`RAH-PR-002` bound this to a cleanup experiment that may not expand into a new mechanism branch. It
has not. Phase 1 is **CLOSED**. Any follow-up requires a new `RAH-PR-###`.
