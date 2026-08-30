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

---

## `RAH-DR-001` — adversarial review of the Track-A design, BEFORE implementation — 2026-08-30

**Status: DEEP REVIEW.** Five independent read-only lenses (capture site · receiver · controls &
confounds · statistics & anti-fishing · prior-art archaeology) plus a synthesis pass, over a written
design spec and the source it proposed to build on. **6 agents, 172 tool calls, 0 errors.** The spec
reviewed is `scratchpad/TRACK_A_ASSAY_SPEC_v1.md`; no assay code existed.

It returned **10 FATAL and 21 SERIOUS defects**. Running the review before writing the code, rather
than after, is the single highest-value decision of the sprint so far. Full findings are in the
workflow transcript; the ones that change the plan are recorded below.

### The four that would have produced a WRONG ANSWER rather than a broken run

**`RAH-DR-001-F1` — the instrument's positive control has already failed, by ~712×.** See
`RAH-C-002` below. This is the finding that reorders the sprint.

**`RAH-DR-001-F2` — a whole family of donor layers makes `D-base` and `D-dpo` bit-identical, and
every gate still passes.** Under `demo_processing_only` the mask edits **demo** query-rows only, so a
**query** position's residual first differs at block `lo+1`. For any donor block `L ≤ lo` (6 Llama /
7 Qwen3) at `p-codeword` or `p-final`, `v_base == v_dpo` **byte for byte**. Every validity gate
(positive control, `D-self`, `D-wrong`, option mass) is computed *without* `D-dpo`, so all of them
pass at such a layer. The confirmatory stage would then report *"receiver identical under base and
dpo ⇒ representation preserved"* **when the two input tensors were the same bytes** — a false
positive for the sprint's preferred hypothesis, manufactured by the anti-fishing protocol itself.
*Required:* constrain `L > lo` (`L ≥ lo` at `p-demo-end`); add a **mandatory vacuity gate** logging
`‖v_dpo − v_base‖` and `cos` per row, with `median(delta) == 0` written `VACUOUS`, never a null; keep
one below-band cell as a deliberate negative control that must show Δ = 0 exactly.
*Consequence:* **`D-late` is deleted.** A late band (22-30 / 27-37) with a fixed mid-depth capture
site is `D-base` relabelled — it cannot differ. It is replaced by the repo's existing same-band,
count-matched key control `nondemo_matched_d1..3` (`score_behavior.NONDEMO_DRAW_ARMS`), which fixes
band, depth, dose and key count and varies only key *identity*. **This changes `CA4` as registered in
`RAH-PR-001` §6.1** and is recorded as a deviation here rather than silently applied.

**`RAH-DR-001-F3` — the donor capture path double-counts BOS on Llama, shifting every position +1.**
`ds_common.forward_hidden_states:876` calls the tokenizer **without** `add_special_tokens=False` on an
**already chat-templated** string, while every position-resolution helper in the repo
(`query_span_positions`, `demo_key_positions`, `46:115`) uses `add_special_tokens=False`. Executed on
both tokenizers: Llama templated prompt → **38 vs 37 ids**, leading `[128000, 128000, …]`; **Qwen3
unaffected**. Track A would have read every Llama donor one token off, silently, with a plausible
number out the other end — and a Qwen3-only pilot would not have caught it.

**`RAH-DR-001-F4` — two live layer-index conventions, and the top row is a different coordinate.**
`capture_target_reps` returns `[n_layers+1, H]` where row `l` = `hidden_states[l]` = resid *after
block l−1*; `LayerPatch(layer_idx=L)` writes `hidden_states[L+1]`. Additionally transformers ties
`hidden_states[-1]` to the **post-final-norm** state, so the top row is not a block output at all.
The archived failing run's "best" layer was **32 of 32** — i.e. that anomalous row.

### Serious defects adopted into the design (abridged)

`S-1` both harmful labels rise together with harm salience → primary estimand becomes the
**harm-matched** `logp(poison) − logp(missile)`. `S-2` donor/receiver residual **norm differs 5–6×**
(measured from a committed artifact: ‖h‖ 5.68 @L6 → 38.25 @L28) and `mode="replace"` therefore
*deletes* far more than it *writes* → rescale to the receiver's native norm, report un-rescaled as
secondary; **and nothing in this repo has ever measured residual norm under a knockout** — one paired
measurement is now required before freeze. `S-3` a Gaussian `D-rand` is off-manifold and cannot be
the floor → add `D-mean` and `D-perm`. `S-4` `D-shuf` shares the same mapping, so it is
**repeatability, not specificity** → renamed `D-exch`; specificity moves to *same-codeword,
different-concept* (`basket_bomb` → `basket_knife`) and *same-concept, different-codeword*.
`S-6` the donor is lexically clean (**verified: 0/80 rows contain "poison"**) but the demos carry
*vial / hazardous materials / antidote / spills* while the distractors come from a different semantic
field → **domain-matched distractors** and a new mandatory `D-nomap` arm from `benign_remap`.
`S-8` Qwen3's receiver would read `<think>`, not the answer, unless `enable_thinking=False` is passed
**explicitly**. `S-9` the search space is ~1330 cells, not 54, because the gate itself argmaxes over
all donor layers. `S-11` the missing `Answer:` prefix. `S-12` `eager` must be forced on **every** arm
or `D-base` loads SDPA and `D-dpo` loads eager. `S-18` `D-self` as specified is a bitwise tautology.
`S-19` add a **patch-free linear/logit-lens channel** on the same vectors — *"linearly present but
not transportable"* is the most informative outcome available and no single channel can produce it.

### What the review confirmed as CORRECT — recorded so it is not re-litigated

The core construction (options in a different prompt from the measured state); the residual
coordinate claim; capturing at a query position under `demo_processing_only` **does** measure the
intended thing subject to `L > lo`; `ScopedAttentionKnockout`'s key/row algebra has **no off-by-one**;
a single prefill-only donor forward reproduces the behavioural intervention exactly, so there is **no
KV hazard**; the receiver must never be hooked (and in fact *cannot* be — `demo_processing_only`
raises on an empty demo span); `RAH-R-002-b` confirmed at `pair_common.py:678-684`; the three-level
population design with a pre-data freeze; reporting the full 4-cell distribution.

---

## `RAH-C-002` — correcting `RAH-R-002`: I cited a gate as an asset without checking that it had ever passed — 2026-08-30

**Status: CORRECTION of a claim made in this sprint's own inventory.**

`RAH-R-002` §0b.2 wrote, of `doublespeak_causality/46_forced_choice_patchscope.py`:

> *"the same mechanic with a **forced-choice inspection prompt** … **and a layer-scanned positive-control
> gate** (`patchscope_gate:83`) that must pass before evaluation runs."*

and concluded:

> *"**P2 is a small additive build, not a rewrite.**"*

**That is an overstatement, and the omission is material.** I recorded that the module *has* a
positive-control gate. I did not check whether the gate had ever *passed*. It has not.

**Re-derived by me from the raw artifact**, `doublespeak_causality/outputs/next3_fc_patchscope_bomb.json`
(the **only** `46` artifact in the repository; Llama-3.1-8B, carrot↔bomb, `n_layers` 32, R = 28,
injection position 35 of 75):

```
positive_control.pos_ctrl_max   = 1.404e-04      gate: > 0.1      -> failed by ~712x
positive_control.best_ps_layer  = 32             (= n_layers: the POST-NORM row, RAH-DR-001-F4)
per_layer_p_concept             = 3.2e-05 .. 1.4e-04, FLAT across all 33 rows
evaluated                       = false
surface_baseline.p_codeword     = 0.9529   <-- option mass is NOT the problem
```

`surface_baseline.p_codeword = 0.9529` is the important half: the receiver answers confidently when
unpatched. **The patch simply does not move it.** So the failure is transport, not readout mass.

**Corroborated on two further model families** by the review, from committed artifacts:
`pair_kv_mediation_Llama-3.1-8B-Instruct_…` 2.53e-04; `…Qwen3-14B…` 3.59e-06;
`multiconcept_necsuff_llama8b_fixed/stage2b_results.json` `positive_control_ok: false` on **36/36**
items. And the repository had already drawn the conclusion — `HANDOFF.md:21`: *"Patchscope readout is
unusable as configured (late-layer read, no positive control) — dropped."*

**What is corrected.** `RAH-R-002`'s *factual* statements about `46` stand — the module exists, it is
cross-prompt, it is forced-choice, it has a gate. The **inference** does not: *"P2 is a small additive
build"* assumed a working instrument. **The correct statement is:**

> Track A rests on an instrument that has **one recorded run and a failed positive control**, whose
> failure was **flat in the donor layer** — the very axis the design proposed to search. Whether the
> instrument can be made to work is now an **open empirical question that must be settled first**.

**Why this matters beyond bookkeeping.** Had the review not run, Stage-A calibration would have swept
donor layers on discovery data, found nothing above the gate anywhere, and burned the sprint into
outcome **A-IV (assay invalid)** — while `RAH-R-002` sat in the log calling the instrument an asset.

**Correction discipline (§9.5):** the corrected figure was re-derived by me from the raw JSON before
this entry was written, not accepted from the reviewing agent. The old wording is quoted verbatim
above rather than edited away. Scope of the error: an *inference*, not a number.

---

## `RAH-PR-004` — GO/NO-GO transport pre-flight, with a stop rule — 2026-08-30

**Status: PREREGISTERED (prospective). Written and committed before the runs are submitted.**

### The one question

> Is there **any** (receiver form, receiver layer `R`) at which a clean, concept-bearing donor
> activation forces a receiver to name that concept?

This is a question about the **instrument**, not about the intervention. No arm, no knockout, no
`demo_processing_only` appears anywhere in it.

### The lead being tested — receiver GEOMETRY, not donor layer

The only patchscope configuration in this repository that has ever passed a positive control
(`07_patchscope_readout.py`, `P(virus) = 0.722`) patches the **final** prompt token and reads the
logits **at that same position** — *zero attention hops*, raw string, no chat template. The failing
`46` patches ~40 tokens upstream of its read position with 4 blocks remaining. Since the archived
failure was **flat in donor layer**, donor layer is not the axis that explains it. **Geometry is.**

Four receiver forms, ordered by hops, are swept against `R ∈ {n/8, n/4, n/2, 3n/4, n−4}` and all
donor blocks `L ∈ [0, n_layers−2]`:

| form | template | patch at | read at | hops |
|---|---|---|---|---|
| `id07_raw` | none (raw string) | last token | **same position** | **0** |
| `id07_tmpl` | chat template | last token | **same position** | **0** |
| `fc_probe_last` | chat template | probe (near end) | final, after `Answer:` | few |
| `fc46` | chat template | probe (first mention) | final | ~40 |

`fc46` is retained deliberately: this run must **reproduce the archived failure**, not assume it.

### Donor

`direct_harmful` × `behavioral` rows from the RBD banks — the condition whose *surface is the concept
itself*, so the captured state is the "clean concept rep" the positive control requires. Captured at
the **last occurrence of the concept surface**, resolved by character offset in that prompt's own
tokenisation. `n_donors = 4`, reported as a mean over donors so a single row cannot carry the verdict.

### Defects fixed by construction, so a failure cannot be a bug

`RAH-DR-001-F3` own tokenisation with `add_special_tokens=False` (`capture_target_reps` and
`forward_hidden_states` are **not used**) · `F4` one layer convention, `L` ↔ `hidden_states[L+1]`,
capped at `n_layers−2` to exclude the post-norm row · `S-8` `enable_thinking=False` explicit, with the
rendered receiver asserted to contain a **closed** `<think></think>` · `S-11` `Answer:` prefix ·
`S-12` `attn_implementation="eager"` on every forward · `S-10` probe resolved by character offset into
the quoted slot and then asserted to be a subtoken of the probe · `RAH-DR-001-F7` labels scored by
`signals.readout_ids(...)["primary_id"]`, one id each, pairwise disjointness asserted.

**Verified on CPU before submission**, both tokenizers: `poison/lantern/missile/candle` →
Llama `21109/74265/26290/38899`, Qwen3 `20476/73165/25224/37799`, **4 distinct on both**; probe
`widget` is a single token (`9264` / `9086`) and collides with no label.

### The gate and the STOP RULE — fixed now

* **PASS** — at least one configuration reaches `pos_ctrl_max > 0.1` (the threshold `46` itself
  applies, restated rather than imported so this verdict does not depend on the failing module).
  Track A proceeds; the passing geometry is carried into the Stage-A design.
* **FAIL** — **no** configuration reaches the threshold on either model. Then:

> **Track A STOPS.** The sprint reports: *the activation-transport instrument this design requires
> does not exist in this repository, on either model, across four receiver geometries, five receiver
> layers and every donor layer — now the fifth recorded positive-control failure.* That is a
> **sourced, reusable negative**, not a null result, and it is reported as such.

**We do not lower the threshold, and we do not proceed on a failed control.** A null from a readout
that fails its own positive control is uninterpretable, and this repository has already retracted a
result on exactly that ground.

### Scope

This is instrument validation only (§9.8: *smoke tests are not pilot science*). It measures no arm,
supports no claim about representation or behaviour, and its outcome selects only whether Track A
continues — a decision the brief's §34 gate requires be made before any large causal search.

---

## `RAH-C-003` — `RAH-PR-003`'s judge clause is NOT implementable; the deviation, declared before running — 2026-08-30

**Status: CORRECTION / DEVIATION, declared prospectively.** No judge output exists yet.

`RAH-PR-003` registered:

> **the n = 8 rows are re-judged in the SAME invocation as the n = 16 rows**, one session per
> (model × bank), 120 rows each (80 at n = 8 + 40 at n = 16), pinned `openai/gpt-4o-mini`

**That cannot be done, and the reason is a guard doing its job.** The two doses live in **different
banks** — `boombness_prompt_bank_rbd_*` (preset `rbd12`, 960 rows) and
`boombness_prompt_bank_rbdn16_*` (preset `rbd12_n16`, 480 rows). `judge_boombness.py:487` calls
`common.compare_bank_hashes(gens_meta, bank_meta, strict=True)`, which **raises** when a run's
recorded bank does not match the bank passed to the judge. `scripts/judge_p2.sh` takes exactly one
`P2_BANK` per invocation. A single invocation spanning both doses would be refused — correctly.

Merging the two banks into one file to satisfy the join would produce a third hash matching
**neither** run, so it fails the same guard. There is no implementable version of the clause.

### What is done instead

**Eight separate `judge_p2.sh` invocations** — 2 models × 2 lexical pairs × 2 doses — each with one
tag, its own correct `P2_BANK`, its own `P2_EXPECT_ROWS` (80 at n = 8, 40 at n = 16), the **same**
pinned judge model, the same commit, launched in the same window. **No code change**: `P2_BANK`,
`P2_MANIFEST`, `P2_EXPECTED`, `P2_PREFIX`, `P2_EXPECT_ROWS` and `P2_PIN_JUDGE_MODEL` are already
parameters of the existing driver.

### Why this is not a weakening relative to the predecessor sprint

`RBD-DR-004` finding **F10** already established that *"one invocation per bank" is literally FALSE*
for the RBD sprint: it ran **five `judge_boombness` invocations per (model, bank)**, one per arm, and
the measured drift is **per invocation**. So the RBD sprint's own arm-to-arm comparisons were already
cross-invocation. This design has the same structure — the difference is that it is **stated here in
advance** rather than discovered by an auditor afterwards.

### What is gained, and how the noise is handled

Re-judging the n = 8 rows produces a **direct measurement of cross-invocation drift on the exact rows
being compared**, at the same commit and pinned model. The `RBD-PR-005` verdict is therefore reported
as:

> the n = 16 − n = 8 difference, **against the measured re-judge drift on the n = 8 rows themselves**

and a difference not exceeding that drift is reported as **not resolvable**, never as a null. This
also supplies `RAH-PR-006` with a freshly measured judge-noise input on this exact population, which
§20 requires to be *measured* rather than assumed.

### Scope

The **RBD sprint's published n = 8 ASR figures are not overwritten and not restated.** They remain the
product of their own sessions. This diagnostic quotes only its own joint-window values, and labels
them as such.

---

## `RAH-R-005` — `RBD-PR-005`, Llama half. PARTIAL — Qwen3 pending — 2026-08-30

**Status: EXPLORATORY (inherited from `RBD-PR-005`). PARTIAL RESULT — the Qwen3 half is still
generating; no verdict is issued until all four cells exist.**

Independently re-derived by `scripts/rah_verify_dose.py` (stdlib only; its own domain cluster
bootstrap; imports nothing from the producer) → **PASS** on every count, rate, ratio, interval and
cache figure. Producer: `scripts/rah_analyze_dose.py` → `outputs/boombness/rah_phase1b/rah_dose.json`.

### Baseline harmful ASR by dose — same window, same pinned judge, same commit

| Llama-3.1-8B | n = 8 | n = 16 | ratio |
|---|---|---|---|
| × `candle_missile` | 7/80 = 0.0875, domain-cluster [0.0250, 0.1500] | **8/40 = 0.2000**, [0.0750, 0.3500] | **2.29×** |
| × `lantern_poison` | 7/80 = 0.0875, [0.0375, 0.1375] | 3/40 = 0.0750, [0.0000, 0.2000] | 0.86× |
| **pooled** | 14/160 = 0.0875 | 11/80 = 0.1375 | **1.57×** |

All 240 rows: 20 domains per cell, judge `openai/gpt-4o-mini` pinned on 100 %, `judge_status: ok` on
100 %, arm `A_baseline` on 100 %, zero duplicate ids, **no filtering of any kind**.

### The two banks disagree, and the pooled effect is below the preregistered resolution

`RAH-PR-003` recorded, **before these runs**, that the design's MDE at 80 % power is **2.68×** on
Llama. The **pooled** observed ratio is **1.57×** — *below* it. One bank moved (2.29×) and the other
did not (0.86×), on **two lexical pairs that are not independent replicates** (shared generator,
shared 20-domain pool, shared readout). The domain-cluster intervals for the moving cell,
[0.0250, 0.1500] against [0.0750, 0.3500], **overlap**.

> **On the Llama half, `RBD-PR-005` does not resolve dose vs concept.** The pooled effect is smaller
> than the design can detect, the two banks point in opposite directions, and no numeric threshold
> was ever registered to adjudicate. This is the outcome `RAH-PR-003`'s power table anticipated.

### A newly measured number this sprint owns: re-judge drift on byte-identical text

`RAH-C-003` predicted this measurement would be the compensation for the unavoidable
cross-invocation comparison. It exists:

| cell | fresh flips / fresh rows | rate | up / down | cached (cannot flip) |
|---|---|---|---|---|
| × `candle_missile` | **2 / 80** | 0.0250 | 2 / 0 | 0 |
| × `lantern_poison` | **4 / 59** | 0.0678 | 2 / 2 | **21** |

⚠ **`judge_cache_hit` rows cannot flip** — a cached verdict is replayed, not recomputed — so the
honest denominator is the freshly judged subset, and both are recorded. The `lantern_poison` cell had
**21 of 80 rows served from cache**; quoting 4/80 there would understate the rate by 26 %. This is a
measurement hazard not previously documented in the repository.

Pooled fresh: **6 flips / 139 rows = 0.0432**, 4 up / 2 down — consistent with the repository's
pinned-judge floor and **symmetric**, which is the benign direction (`paired_test_noise_sensitivity`
shows type-I inflation needs an *asymmetric* up-bias).

### ⚠ A join hazard found while writing the verifier

`prompt_id = sha256(family_id | condition)[:16]`, and **`family_id` does not carry the codeword**.
The same `prompt_id` (`6977d4d985a09834`) therefore exists in **both** the `lantern_poison` and
`candle_missile` n = 16 banks, on unrelated rows. **Any cross-bank join on `prompt_id` silently pairs
unrelated prompts.** No current analysis does this; `scripts/rah_verify_dose.py` joins strictly
within a bank and says so in its docstring. Recorded so a future analysis does not learn it the hard
way.

### ⚠ Ordering disclosure — a DEVELOPMENT observation now in hand, before `RAH-PR-007` exists

The `candle_missile` n = 16 cell reads **8/40 = 0.2000**. Scaled to a 160-row arm that is ≈ 32
attacks, against the predecessor sprint's headroom floor of **14** — the gate every one of its 16
cells failed.

**This observation is recorded, and nothing is done with it yet.** It was made while executing an
inherited exploratory diagnostic, **before** the Track-B screening rule (`RAH-PR-007`) is written, so
the ordering is disclosed here in full:

* it **cannot** promote any declined estimand — `RBD-PR-005` is bound by its own registration and by
  `RAH-PR-003`'s scope clause, and the behavioural estimand stays **DECLINED**;
* it is **development-level** material, which is exactly what §18 says a headroom screen may inspect;
* `RAH-PR-007` will be written **without tuning its rule to this cell**, and any confirmatory Track-B
  population must use **new families, new demonstrations and new seeds** per §21;
* the fact that this number was seen *before* the screening rule was written is itself a deviation
  from the clean ordering §19 prescribes, and is declared here rather than discovered later.

### Still open

Qwen3-14B × both banks — generation running (jobs 817148 / 817157, both alive, weight-loading under
the documented two-14B-per-node contention). `RBD-PR-005` is **not closed** until those land.

---

## `RAH-C-005` — the pre-flight crashed on my own span resolver; fixed, tested, resubmitted — 2026-08-30

**Status: CORRECTION (defect in this sprint's own code, caught by its first GPU run).**

Job `817294` (Llama × `lantern_poison`) resolved its label ids correctly —
`poison 21109 · lantern 74265 · missile 26290 · candle 38899`, matching the CPU pre-check exactly —
and then **died in donor capture**:

```
ValueError: no token covers char span [870,876)
  rah_preflight_transport.py:190 -> token_index_covering
```

**Cause.** `token_index_covering` required a token *contained* in the word's character span
(`a >= lo and b <= hi`). A BPE tokenizer emits the **leading space as part of the word token**:

```
target_surface 'poison' at chars [870, 876)
tokens overlapping:  idx=149  span=[869, 876)  piece=' poison'
                     containment test (a >= 870) -> FALSE, so NOTHING matched
```

**Containment is the wrong rule; overlap is the right one.** The fix takes the LAST token whose span
*overlaps* the word, and the caller now additionally asserts the resolved token **decodes to a piece
of the target word** (`assert_token_is_part_of`), so a mis-resolution fails loudly instead of
producing a plausible wrong capture site.

⚠ **The failure mode was lucky, and that is the point.** This crashed rather than silently resolving
to a neighbouring token — but only because *no* token satisfied the containment test on this
segmentation. On a tokenizer that split the word without a leading-space merge, the same bug would
have returned a **valid-looking but wrong index** and the whole assay would have measured the wrong
position. This is the `feedback_absolute_position_index_bug` class that has hit this repository twice
before, arriving a third way.

**Tests added** — `tests/test_rah_preflight_spans.py`, **7 passing**, including:

| test | what it pins |
|---|---|
| `test_leading_space_token_is_resolved` | the real failing case, [869,876) for a word at [870,876) |
| `test_MUTANT_containment_semantics_would_have_failed` | **executed proof** the old rule found nothing on the same input |
| `test_multi_subtoken_word_returns_the_LAST_piece` | multi-piece words resolve to the last subtoken |
| `test_no_overlap_still_raises` | the guard can still fail |
| `test_zero_width_tokens_are_ignored` | degenerate spans do not win |
| `test_MUTANT_assert_token_is_part_of_REJECTS_a_wrong_token` | the new identity assertion can fail |

**Re-validated on CPU before resubmitting**, both models × both banks × 4 donors each: every donor
position resolves to a token decoding exactly to the concept (`poison` / `missile`), and
`target_surface` is confirmed to be the **concept** on `direct_harmful` rows. The receiver hop ladder
is as designed:

| receiver form | Llama seq / q_pos / read / **hops** | Qwen3 seq / q_pos / read / **hops** |
|---|---|---|
| `id07_raw` | 10 / 9 / 9 / **0** | 10 / 9 / 9 / **0** |
| `id07_tmpl` | 45 / 44 / 44 / **0** | 22 / 21 / 21 / **0** |
| `fc_probe_last` | 75 / 66 / 74 / **8** | 52 / 39 / 51 / **12** |
| `fc46` | 81 / 34 / 80 / **46** | 58 / 7 / 57 / **50** |

`fc46`'s 46–50 hops is the archived failing geometry, retained deliberately so the run reproduces the
known failure rather than assuming it.

**No scientific claim was affected** — the job produced no result artifact. `RAH-PR-004`'s gate and
stop rule are unchanged.

---

## `RAH-R-006` — the Track-B power analysis, and what it says about the whole behavioural design class — 2026-08-30

**Status: DIAGNOSTIC. This is the INPUT to `RAH-PR-006`; the thresholds are NOT frozen in this entry.**
The freeze waits on the self-review currently auditing whether the clustering correction is applied
correctly for a paired McNemar test (§38 requires the power analysis itself be right before it can
gate an expensive matrix).

Producer `scripts/rah_power_trackb.py`, reusing `paired_test_noise_sensitivity.simulate()` — the
repository's existing paired-McNemar-with-judge-noise simulator, already covered by 14 tests
including a positive control asserting that asymmetric noise *does* inflate type-I. This file adds
only a bisection over the true effect and a clustering correction.

### Inputs, all measured, all conservative (§20)

| input | value | provenance |
|---|---|---|
| judge flip rate | **not a constant** — 0.0213 at ASR 0.0125 rising to 0.0851 at ASR 0.2708 | `effective_flip_rate` over each population's own score distribution (`RAH-C-004`) |
| flip symmetry | symmetric | pinned re-tests 8 up / 8 down, exact p = 1.0; this sprint's own 4 up / 2 down |
| domain ICC | **0.09** | the TOP of the range estimable on balanced populations (ab_base 0.030, 38dom 0.067, d10-Llama 0.090). The RBD baselines cannot estimate ICC at 4 rows/domain — every point estimate ≤ 0 — so their apparent zero is **not** used |
| α, power | 0.05 two-sided, 0.80 | |

### The result

MDE at 80 % power, ICC 0.09, measured flip rate. `n/a` = **even reducing ASR to zero does not reach
80 % power**.

| k domains | rows/domain | n | baseline ASR | expected attacks | MDE (absolute) | MDE (relative) |
|---|---|---|---|---|---|---|
| 20 | 4 | **80** | 0.05 → 0.20 | 4 → 16 | **n/a at every baseline** | — |
| 20 | 8 | 160 | 0.0875 | 14 | **n/a** | — |
| 20 | 8 | 160 | 0.1500 | 24 | **n/a** | — |
| 20 | 8 | 160 | 0.2000 | 32 | 0.1896 | 0.95 |
| 20 | 16 | 320 | 0.1375 | 44 | 0.1294 | 0.94 |
| 30 | 8 | 240 | 0.1375 | 33 | 0.1258 | 0.91 |
| 38 | 16 | **608** | 0.0875 | 53 | 0.0795 | 0.91 |
| 38 | 16 | **608** | 0.1375 | 84 | 0.0964 | **0.70** |
| 38 | 16 | **608** | 0.2000 | 122 | 0.1211 | **0.61** |

### What this says, and it is larger than Track B

> **The 80-rows-per-arm design used throughout this project cannot detect a behavioural effect of any
> size, at any baseline ASR up to 0.20, once judge noise and domain clustering are both accounted
> for.** Not "is underpowered for small effects" — *cannot detect a total wipeout*.

This is a **retrospective explanation** of why the behavioural half kept failing, and it is
independent of the headroom gate that formally declined it. The predecessor sprint declined its
behavioural estimand because baseline attacks (12/160, 5/160) fell below a floor of 14. This analysis
says that **even had the floor been met, the design could not have resolved the effect**: at n = 160
and baseline 0.15 the MDE is still `n/a`.

⚠ It also **removes a tempting reading of `RAH-R-005`**. The `candle_missile` n = 16 cell rose to
0.2000, which looks like the headroom the sprint wanted. At k = 20 × m = 2 (the n = 16 population is
40 rows) the design is *further* below the n/a threshold, not above it. **Headroom alone was never
the binding constraint.**

### Two consequences that are not obvious

1. **A higher-headroom population does not buy proportional power.** Judge churn concentrates near
   the 0.5 boundary, so the effective flip rate *rises* with baseline ASR (0.021 → 0.085 measured).
   Choosing a bomb-class concept buys signal **and** noise. This is why the n = 160 / baseline-0.20
   cell needs a 95 % relative reduction.
2. **Domains, not rows, are the binding lever** — as the predecessor phase's own R-BE finding said.
   Going 20 → 38 domains at fixed rows/domain is what moves MDE from `n/a` to 0.61–0.70 relative.

### The feasibility question this poses for `RAH-PR-006`

A design at **k = 38 domains × 16 rows = 608 rows** on a baseline of **≥ 0.15** reaches a relative MDE
of **0.61–0.70**. The discovery-bank observation that motivated this whole line was a **73 % relative
reduction** (30/96 → 8/96); the RBD Llama arm-B pattern was 92 % (12 → 1). So an effect of the size
previously observed **is** detectable — but only at ~600 rows over ~38 domains on a high-headroom
population, and **not** at any design this project has run.

Such a bank already exists: `boombness_prompt_bank_38dom_gatesub.jsonl` — **38 domains, 608 rows,
Llama baseline ASR 0.1562** (`d38gj_20260829_043706_310488`). Whether it is usable is a question for
`RAH-PR-007`, which is **not yet written**, and nothing here selects it.

**Nothing is frozen by this entry.** `RAH-PR-006` will state the minimum headroom, the minimum
meaningful effect, the required rows and the required domains — after the method is audited.

---

## `RAH-DR-002` / `RAH-C-006` — the self-review of my own code found FIVE fatal defects — 2026-08-30

**Status: DEEP REVIEW + CORRECTION.** Three read-only lenses (numerics · guards-and-vacuity ·
semantics) plus a synthesis pass, over the five scripts this sprint has written. **4 agents, 130 tool
calls.** Every finding below was **re-verified by me from source before being accepted** — the brief's
rule that a correction is itself a claim.

The single most important thing this review establishes: **a running GPU job was executing code that
could have returned a false GO on the sprint's most important gate.** Job `817661` was cancelled
mid-flight rather than allowed to write a misleading artifact.

### FATAL — would have changed a number or inverted a verdict

**`F2` — the pre-flight gate could pass with ZERO transport.** `positive_control_ok` tested an
**absolute** probability, `p_concept > 0.1`. But two of the four receiver forms **print all four
labels in the prompt**, so the *unpatched* prior on the concept is of order 1/4 — already far above
the threshold. `base_dist` was computed, stored, and **never used in the verdict**. A receiver that
ignored the patch entirely would have reported **GO**, on the gate whose entire purpose is to detect
exactly that. *Fixed:* three required conjuncts — level > t **and** uplift over the unpatched prior
> t **and** `p_concept > p_codeword`. `p_concept_unpatched` and `uplift_over_unpatched` are now
persisted per row, and the rule itself is written into the artifact.

**`F3` — the answer prefix was on the wrong side of the chat template, so every `read_at=final`
probability was measured at the wrong token.** I put `Answer:` inside the **user** message.
Templating then appends the assistant header, and `read_pos = len-1` lands on the trailing newline.
Verified by me:

```
fc_probe_last  last 3 tokens = ['\n\n', 'Answer', ':']   <- AFTER fix
               (before: ['<|start_header_id|>','assistant','<|end_header_id|>','\n\n'])
```

`score_behavior.next_token_readout:85` implements the validated form as
`tokenizer(templated + answer_prefix, add_special_tokens=False)` and its own comment records why
(`as_is 1.4e-2 → forced 0.979`). *Fixed:* receivers are now built as
`apply_template(body) + "Answer:"`.

**`F1` — `id07_raw` was not "07 exactly".** I applied `add_special_tokens=False` unconditionally,
including to the one **untemplated** form. `07_patchscope_readout.py:56` tokenizes that same raw
prompt with the default `add_special_tokens=True`. Verified: 07 gives `ids[0]=128000
'<|begin_of_text|>'`, len 11; mine gave `ids[0]=15339 'hello'`, len 10. **The one configuration in
this repository that has ever passed a patchscope positive control was not actually being
reproduced.** *Fixed:* `add_special_tokens = not form["templated"]`; verified BOS restored, len 11.

**`F4` — the power artifact claimed 20 000 replicates; every simulation ran at 4 000.** `mde()`
passed `reps // 5` internally while the artifact recorded `REPS`. A reader would attribute √5 more
Monte-Carlo precision than exists (per-evaluation SE at power 0.80 is 0.0063). *Fixed:* `SIM_REPS` is
a named constant, it is what the artifact records, and the artifact now carries an explicit note that
the MDE is printed to 4 dp for reproducibility, **not** because it is resolved to 4 dp.

**`F5` — `clustered_proportion_ci` silently substitutes an iid Wilson interval** on a degenerate
bootstrap (e.g. a 0/40 cell), announcing it only on stdout. Publishing that under a *clustered* name
is what its own comment warns against — and it would have made the independent verifier **FAIL a
correct cell**. This was prospective-live: both Qwen3 cells were still pending with baselines of
0.0125 and 0.05, so a 0/40 `n16` cell was entirely plausible. *Fixed:* the producer captures
`return_diag=True` and persists `ci_interval_source`; the verifier refuses a `MISSING` source and
skips-with-a-flag when the source is the Wilson fallback.

### SERIOUS — guards that could not fail

**`S1`** — the `enable_thinking` guard tested for an open `<think>` with no close. But
`ds_common.apply_template` **swallows** `TypeError/ValueError` and falls back to a plain call, so the
"thinking silently left ON" state contains **no `<think>` at all** and the guard was silent in
exactly the case it names. *Fixed:* the guard now tests the **effect** — render with
`enable_thinking=False` and with `None`, and refuse unless they differ **and** the closed tag is
present. Verified firing correctly on both models.

**`S2`** — an **absolute** 5e-4 tolerance on the exact McNemar p made that check vacuous for all four
headline cells (they sit at 5e-23 … 4e-16); any producer value below 5e-4 would have passed,
including one computed from the wrong cells. *Fixed:* relative comparison at 1e-12. **Re-ran the
Phase-1 verifier under the tightened rule: still PASS**, so `RAH-R-004`'s numbers are unaffected.

**`S3`** — the dose verifier *printed* the producer's own drift figures and checked only `n_cached`,
while its PASS text claimed the drift was reproduced. It was an echo, not a verification — and
`flip_rate_fresh` is quoted downstream in the power analysis. *Fixed:* the producer persists
`orig_judge_dir`; the verifier loads it and recomputes every drift figure independently.

**`S4`** — a pending cell was skipped with a `print`, so the producer exited 0 with `problems: []`
over **2 of 4** registered cells and the verifier PASSed over whatever survived. *Fixed:* a pending
cell is now a recorded problem, the artifact carries `complete`, and the verifier **refuses to
certify an incomplete population**.

### What this costs, and what it buys

Job `817661` is cancelled and the pre-flight rerun; the Qwen3 judge wave is launched so the dose
population can complete. **No published number moves** — `RAH-R-004` re-verifies clean under the
tightened check, and `RAH-R-005`'s counts are unaffected (F5 changes interval *provenance*, not the
Llama intervals, whose bootstraps were non-degenerate).

The lesson is the one the predecessor sprint paid for and this sprint has now paid for twice: **the
defects were all in guards and provenance, not in arithmetic.** Every number my code computed was
right. What was wrong was what the code *claimed to have checked*.

---

## `RAH-C-007` — my F5 correction created a vacuous guard, caught one tick later — 2026-08-30

**Status: CORRECTION OF A CORRECTION.** This is the failure mode `RBD-C-018` documented and the
sprint brief §9.5 exists for: *a correction is a new claim and needs the same audit as the claim it
replaces.*

`RAH-C-006`'s F5 fix taught the dose verifier to skip the clustered-interval comparison when the
producer had fallen back to an iid Wilson interval. I wrote the test as
`elif src != "cluster_bootstrap"`. **The healthy value `common.py` actually emits is
`cluster_percentile_bootstrap`** (`common.py:1479`). So the branch matched **every** cell, skipped
**every** interval comparison — and the run still printed:

> `INDEPENDENT VERIFY (dose): PASS -- counts, rates, ratios, cluster intervals ... all reproduced`

**8 of 8 interval comparisons were silently skipped under a PASS that claimed them.** A guard that
matches zero rows and passes is a defect (§9.7); I created one while removing one.

**Fix.** The test is now on the **degenerate** prefixes — `wilson_iid_fallback…` and `undefined…` —
which are the enumerable set (`common.py:1440, 1450, 1462`), so an **unrecognised** source now fails
loudly instead of being waved through. The PASS line reports `cluster intervals compared: N of M` and
names any skipped cell. Re-run: **8 of 8 compared, all match.**

**Why it was caught:** the fix printed a per-cell line saying "SKIPPED", and eight of them appeared
under a PASS. Making a guard *say what it did not check* is what made a vacuous guard visible.

---

## `RAH-R-007` — `RBD-PR-005` CLOSED: the dose diagnostic does not resolve dose vs concept — 2026-08-30

**Status: EXPLORATORY (inherited). COMPLETE — all four cells. `RBD-PR-005` is CLOSED.**

Producer `scripts/rah_analyze_dose.py` → `outputs/boombness/rah_phase1b/rah_dose.json`
(`complete: true`, 4/4 cells, `problems: []`). Independently re-derived by
`scripts/rah_verify_dose.py` — stdlib only, its own cluster bootstrap, refuses an incomplete
population — **PASS, 8 of 8 cluster intervals compared, every count / rate / ratio / drift figure
recomputed from raw judge rows.**

### The complete result

| model × bank | n = 8 | n = 16 | ratio | n=16 observed vs flat expectation |
|---|---|---|---|---|
| Llama × `candle_missile` | 7/80 = 0.0875 [0.0250, 0.1500] | 8/40 = 0.2000 [0.0750, 0.3500] | **2.29×** | 8 vs 3.5 → **+4.5 rows** |
| Llama × `lantern_poison` | 7/80 = 0.0875 [0.0375, 0.1375] | 3/40 = 0.0750 [0.0000, 0.2000] | 0.86× | 3 vs 3.5 → −0.5 |
| Qwen3 × `candle_missile` | 1/80 = 0.0125 [0.0000, 0.0375] | 1/40 = 0.0250 [0.0000, 0.0750] | 2.00× | 1 vs 0.5 → +0.5 |
| Qwen3 × `lantern_poison` | 3/80 = 0.0375 [0.0000, 0.0750] | 1/40 = 0.0250 [0.0000, 0.0750] | 0.67× | 1 vs 1.5 → −0.5 |
| **pooled Llama** | 14/160 = 0.0875 | 11/80 = 0.1375 | **1.57×** | |
| **pooled Qwen3** | 4/160 = 0.0250 | 2/80 = 0.0250 | **1.00×** | |

Intervals are domain-cluster percentile bootstraps, k = 20, `interval_source =
cluster_percentile_bootstrap` on all eight. Judge pinned `openai/gpt-4o-mini` on 100 % of rows,
`judge_status: ok` on 100 %, arm `A_baseline` on 100 %, **no filtering of any kind**.

### The verdict, in the registration's own vocabulary

`RAH-PR-003` fixed the interpretation rules before the runs and recorded the attainable resolution:
**MDE at 80 % power = 2.68× (Llama), 4.10× (Qwen3).** Observed pooled: **1.57×** and **1.00×** —
both **below** their own thresholds.

> **`RBD-PR-005` DOES NOT MOVE AT A RESOLVABLE SIZE.** Per its registration this licenses
> *"no LARGE dose effect"* and **never** *"no dose effect"*. It does not resolve whether the low
> baseline ASR is dose-driven or concept-driven.

**Three of four cells sit within ±0.5 rows of the flat expectation.** Only Llama × `candle_missile`
deviates (+4.5 rows) — a single cell, against a measured re-judge drift of ~2 rows at n = 80, with
overlapping domain-cluster intervals ([0.0250, 0.1500] vs [0.0750, 0.3500]), and no preregistered
threshold to adjudicate it. **It is one cell of four and is not promoted.**

### Bound scope, honoured

`RBD-PR-005` was registered EXPLORATORY and **cannot promote any declined estimand**. The behavioural
estimand remains **DECLINED** on both models. Nothing here is evidence about attack suppression.
`RBD-PR-005` is now **CLOSED** and will not be re-run, re-cut, or pooled differently.

⚠ **An observation recorded and deliberately NOT pursued.** The *direction* is bank-consistent across
models — `candle_missile` up on both (2.29×, 2.00×), `lantern_poison` down on both (0.86×, 0.67×).
Three of those four movements are ±0.5 rows, i.e. indistinguishable from nothing. Reading a
bank × dose interaction out of this would be **branching into a new hypothesis on partial data**,
which §51 of the brief forbids. It is written down here so it is not rediscovered later as if new,
and it is **not** acted on.

### The reusable number this produced

**Pooled re-judge drift on byte-identical text, freshly measured on the very rows compared:
11 flips / 299 freshly-judged rows = 0.0368**, direction 4 up / 7 down.

| cell | fresh flips / fresh rows | rate | cached (cannot flip) |
|---|---|---|---|
| Llama × `candle_missile` | 2 / 80 | 0.0250 | 0 |
| Llama × `lantern_poison` | 4 / 59 | 0.0678 | **21** |
| Qwen3 × `candle_missile` | 0 / 80 | 0.0000 | 0 |
| Qwen3 × `lantern_poison` | 5 / 80 | 0.0625 | 0 |

This is a **directly measured, pinned-judge, same-commit** noise floor on this exact population, and
it is what `RAH-PR-006` uses rather than the repository's unsourced 6.5–7.0 % per-invocation figure
(which `RAH-R-002-f` cited and which has **no committed artifact** behind it — it exists only as a
hand-assembled table in a prior plan document, from unpinned-era runs).

### Checklist

`[x] P1B  RBD-PR-005 executed as written, then closed  → RAH-R-007`

---

## `RAH-R-008` — the transport gate PASSES, and the five prior failures were the RECEIVER LAYER — 2026-08-30

**Status: DIAGNOSTIC / INSTRUMENT VALIDATION. `RAH-PR-004`'s gate: GO.**
Artifact `outputs/boombness/rah_preflight/rahpf_plp_20260830_195527.json`, job `817882`,
Llama-3.1-8B-Instruct, `lantern↔poison`, 4 `direct_harmful` donors, 20 configurations
(4 receiver forms × 5 receiver layers) × 31 donor layers.

### The gate

**`any_config_passes = true`, 5 of 20 configurations pass**, under the corrected three-conjunct rule
(`RAH-C-006` F2: level > 0.1 **and** uplift over the unpatched prior > 0.1 **and** concept beats
codeword).

| best configuration | value |
|---|---|
| form | `fc_probe_last` (4-way forced choice, probe last, assistant-side `Answer:`) |
| receiver layer R | **4** of 32 |
| donor layer L | 3 (best); **the profile is broad — see below**) |
| P(concept) | **0.8421** |
| P(concept) unpatched | 0.00209 |
| **uplift** | **+0.8400** |
| P(codeword) | 0.00210 → **concept/codeword = 402×** |

### The finding: it is the RECEIVER INJECTION LAYER, and nothing else

P(concept), best over donor layers, by receiver layer:

| form | R=4 | R=8 | R=16 | R=24 | R=28 |
|---|---|---|---|---|---|
| `id07_raw` | 0.5043 | **0.6019** | 0.0029 | 0.0005 | 0.0519 |
| `id07_tmpl` | 0.0033 | 0.0413 | 0.0007 | 0.0002 | 0.0572 |
| **`fc_probe_last`** | **0.8421** | 0.6999 | 0.0168 | 0.0201 | 0.0065 |
| `fc46` | 0.2771 | 0.0877 | 0.0133 | 0.0117 | 0.0088 |

**Every form works at R = 4–8 and dies at R ≥ 16.** For `fc_probe_last` that is a **130× collapse**
from R=4 to R=28.

**`fc46` at R = 28 is exactly `46_forced_choice_patchscope.py`'s default** (`R = n_layers − 4`,
`46:164`). It returns **0.0088** here — reproducing the archived `pos_ctrl_max = 1.404e-04`
(`next3_fc_patchscope_bomb.json`) to within the difference expected from a different bank and
concept, and **both are far below the 0.1 gate**.

> **The instrument was never broken. It was injected 4 layers from the output, leaving the receiver
> no depth in which to use the transplanted state.** Moving the injection from R = 28 to R = 4 takes
> the same donor, the same model and the same readout from **0.0088 to 0.8421 — a ~96× improvement.**

This explains **all five** recorded positive-control failures in this repository
(`next3_fc_patchscope_bomb` 1.4e-04; `pair_kv_mediation` Llama 2.53e-04 and Qwen3 3.59e-06;
`multiconcept_necsuff` 36/36 items), every one of which used a late-layer injection inherited from
`07_patchscope_readout.py`'s `n_layers − 4` **readout** default being reused as an **injection**
layer. `RESEARCH_HANDOFF.md:21`'s conclusion — *"Patchscope readout is unusable as configured
(late-layer read, no positive control) — dropped"* — named the right cause and dropped the method
anyway.

### Why the winning configuration is also the RIGHT one for Track A

`RAH-DR-001` F2 established that Track A is vacuous at any donor layer `L ≤ lo` (Llama `lo = 6`),
because `demo_processing_only` masks demo rows only, so a query-position residual is **bit-identical**
between arms below the band. An assay that only worked at L ≤ 6 would be unusable.

`fc_probe_last @ R = 4` has a **broad, flat donor-layer profile**:

```
L :   0     1     2     3     4     5     6     7     8     9    10    11    12    13    14    15    16
pC: 0.740 0.774 0.835 0.842 0.827 0.789 0.772 0.694 0.733 0.677 0.678 0.651 0.747 0.747 0.775 0.676 0.636
```

At **L = 14 — the top of the Llama intervention band 6–14 — P(concept) = 0.7745** against
P(codeword) = 0.0094, an **82× ratio.** The assay therefore has strong signal *exactly where the
intervention acts*, and the `L > lo` constraint costs almost nothing. The two `R = 8` variants are
sharply peaked at L ≈ 5 and decay fast, which is why `R = 4` is preferred on more than its maximum.

### ⚠ Population discipline — a deviation, declared

This pre-flight ran on **`lantern_poison`, a LEVEL-B (diagnostic) population**, not level-A discovery
material. `RAH-PR-004` scoped it as *"instrument validation only … its outcome selects only whether
Track A continues"*, and it used `direct_harmful` donors — an instrument-validity condition, never
the attack condition — with **no intervention anywhere**. So it measures no arm and supports no
claim about representation or behaviour.

**But the receiver layer R was chosen while looking at level-B material, and that cannot be
unseen.** Therefore, binding on the rest of the sprint:

* the **Stage-A calibration (P3) that freezes the configuration must be re-run on LEVEL-A discovery
  banks** (`boombness_prompt_bank`, `basket_bomb`, `button_bomb`, …), and must confirm the R = 4–8
  band independently. If level-A disagrees, that is informative and the disagreement is reported;
* `RAH-PR-005`'s freeze records **R chosen on level-A**, with this pre-flight cited only as the
  GO/NO-GO that licensed continuing;
* the level-C confirmatory claim remains untouched by both.

### Checklist

```
[x] P2   GO/NO-GO transport pre-flight, Llama            RAH-PR-004 / RAH-R-008  -> GO
[~] P2   same pre-flight, Qwen3-14B (submitted)
[ ] P3   Stage-A calibration on LEVEL-A data, R re-derived independently
```

Qwen3 is the decisive model — its binding collapsed 75/80 → 9/80 — so the assay must be shown to work
there before any Track-A claim. That run is submitted.

---

## `RAH-PR-009` — Stage-A calibration on LEVEL-A discovery data — 2026-08-30

**Status: PREREGISTERED (prospective). Written and committed before the level-A runs are submitted.**

`RAH-R-008` bound this sprint to re-derive the receiver configuration on **level-A discovery
material**, because the GO/NO-GO pre-flight chose `R` while looking at a level-B population.

> **Registry note.** The §10.0 phase map originally pointed P3 at `RAH-PR-004`. `RAH-PR-004` was
> spent on the GO/NO-GO pre-flight, so the Stage-A procedure takes the next free id, **`RAH-PR-009`**.
> `RAH-PR-005` stays reserved for the **freeze**. Recorded rather than silently renumbered.

### What is calibrated, and on what

| | |
|---|---|
| banks (level A, **discovery**) | `boombness_prompt_bank` (carrot↔bomb), `_basket_bomb` (basket↔bomb), `_ticket_knife` (ticket↔knife) — 6 domains each, 2736 rows, all conditions |
| donors | `direct_harmful` × `behavioral`, **`n_examples = 8`** (matching the RBD dose), 4 per bank, sorted by `prompt_id` — a deterministic, outcome-blind selection |
| distractor labels | **domain-matched** (`RAH-DR-001` F6): on a bomb bank the other concept is `knife` and the other codeword is `ticket`; on the knife bank, `bomb` / `carrot`. All four labels verified **single-token and pairwise distinct on both models** — Llama `13054/75294/22145/11989`, Qwen3 `12764/74194/21430/11727` |
| models | Llama-3.1-8B-Instruct and Qwen3-14B (`--enable-thinking false`) |
| grid | 4 receiver forms × 5 receiver layers `R` × all donor layers `L ∈ [0, n_layers−2]` |

### The selection rule, fixed now

Choose the `(form, R)` that **maximises the MINIMUM uplift across all level-A banks and both models**,
subject to the three-conjunct gate passing on every one of them.

Maximising the *minimum* rather than the maximum is deliberate: it selects for **robustness across
lexical pairs and models**, not for a peak on one lucky cell — the failure mode `RAH-DR-001` F9/F10
warned about when a gate argmaxes over ~1300 cells.

Deterministic tie-break, in order: **lower `R`** → **broader donor-layer support above the
intervention band** (count of `L > lo` with uplift > threshold) → **form order as listed**.

### Why this selection CANNOT be contaminated by the effect it will later estimate

`RAH-DR-001` F10 required *"absence of the cell, not a promise"*. It is satisfied structurally:

```
$ grep -cE "intervene|ScopedAttentionKnockout|AttentionKnockout|knockout|demo_processing_only" \
        src/boombness/rah_preflight_transport.py
0
```

**The Stage-A runner contains no intervention code path at all.** It cannot compute a
`demo_processing_only` arm even if instructed to. The `base − dpo` contrast that Track A will
estimate is not merely unexamined here — it is **uncomputable** by this program.

Additionally, every donor is `direct_harmful` (the concept is literally present) — an
instrument-validity condition, never the `natural_doublespeak` attack condition — so no attack row is
touched.

### What the result licenses

Stage A selects `(form, R)` **and nothing else**. It does **not** license any claim about
representation, behaviour, the intervention, or any lexical pair. Its output is an input to the
`RAH-PR-005` freeze, which will additionally fix the donor position, the donor layer set
(constrained to `L > lo` per `RAH-DR-001` F2), the control family, the statistical test and the
equivalence margin.

**If level-A disagrees with the pre-flight's R = 4–8 band, that disagreement is reported as a
finding, and the level-A answer wins** — the pre-flight is a GO/NO-GO, not a calibration.

---

## `RAH-R-009` — Qwen3 gate PASSES; level-A Llama calibration; two structural findings — 2026-08-30

**Status: DIAGNOSTIC / INSTRUMENT VALIDATION. Selection NOT yet made — Qwen3 level-A is still
running, and `RAH-PR-009`'s rule requires both models.**

### The Qwen3 gate — the decisive model — PASSES

`rahpf_qlp_20260830_201039.json`, job `818419`, Qwen3-14B, `lantern↔poison`, `n_layers = 40`.
**10 of 20 configurations pass**, best `1.0000`.

P(concept), best over donor layers, by receiver layer:

| form | R=5 | R=10 | R=20 | R=30 | R=36 |
|---|---|---|---|---|---|
| `id07_raw` | 0.6925 | 0.2200 | 0.0486 | 1.26e-04 | 0.0071 |
| `id07_tmpl` | 2.89e-05 | 5.66e-04 | 0.2276 | 2.22e-06 | 0.0097 |
| **`fc_probe_last`** | **1.0000** | **1.0000** | **1.0000** | 0.8930 | 0.9394 |
| `fc46` | 0.1310 | 0.3004 | 1.55e-05 | 1.54e-06 | 1.92e-06 |

`fc_probe_last @ R = 5`: P(concept) **0.99999991** against an unpatched prior of **0.0223**, with
P(codeword) **3.4e-12**. The donor-layer profile is **flat at 1.000 from L = 0 to L = 31**, still
0.910 at L = 36, and **31 of 31 donor layers above the Qwen3 band (`lo = 7`) clear the gate**.

**The depth fraction, not the absolute layer, is what transfers across models.** Llama passes at
R = 4 and 8 of 32 (0.125 and 0.25 of depth); Qwen3 passes at R = 5 and 10 of 40 — *the same two
fractions*. `fc46` again fails hardest at the late layers that were its default.

### ⚠ Caveat that must travel with this number

A positive control this saturated shows the **channel works** — it does **not** show the channel
carries a *mapped* concept. The donor here is a `direct_harmful` prompt in which the concept word is
**literally present**, so its residual at that token largely *is* that token's identity. Transporting
it and reading it back is close to a copy test.

> **What Track A must still establish is the non-trivial claim: that a donor captured at the
> CODEWORD position of a `natural_doublespeak` prompt transports the CONCEPT.** `RAH-R-008` and
> `RAH-R-009` license only *"the instrument can transport something"*. They are not evidence about
> the doublespeak mapping.

A second consequence: on Qwen3 the positive control **saturates at 1.000 across 31 donor layers**, so
it carries **no information for choosing a donor layer** on that model. The donor layer must be fixed
on mechanism (`L > lo`, inside/above the intervention band), never on this curve — which is what
`RAH-PR-009` already requires.

### Level-A Llama calibration — all three banks pass

| bank | labels | passing | best (`fc_probe_last` R=4) | R=8 |
|---|---|---|---|---|
| `carrot↔bomb` | bomb / carrot / knife / ticket | 8/20 | **0.9078** | 0.8606 |
| `basket↔bomb` | bomb / basket / knife / ticket | 9/20 | **0.9134** | 0.8813 |
| `ticket↔knife` | knife / ticket / bomb / carrot | 9/20 | **0.8550** | 0.8347 |

`fc_probe_last` at R = 4 is the best form on **every** level-A bank, and the R = 4–8 band reproduces
the pre-flight's independently. **No disagreement to report** — the level-A answer and the level-B
GO/NO-GO agree, which is the outcome `RAH-R-008` pre-committed to check.

### ⚠ Structural finding: two of my three level-A banks share their donors byte-for-byte

`direct_harmful` carries the **concept** surface and never the codeword, so two banks with the same
concept have **identical** `direct_harmful` rows. Verified:

```
carrot_bomb vs basket_bomb  : 4/4 donor prompts BYTE-IDENTICAL   (concepts bomb vs bomb)
carrot_bomb vs ticket_knife : 0/4                                (concepts bomb vs knife)
```

This is visible in the results as identical `id07_raw` / `id07_tmpl` values for the two bomb banks
(0.7652 / 0.8459 / 0.4323 / 0.5643) — the `id07` receiver contains no codeword, so with an identical
donor those cells *must* agree, and they do to the last digit.

**Consequence, recorded before the selection is made:** level-A supplies **two distinct donor sets
(bomb, knife), not three.** `RAH-PR-009`'s "minimum across banks" must be read that way, and the
`carrot_bomb` vs `basket_bomb` pair is **not** independent replication.

**It is still useful, as an unplanned control**: the *same* donor into two receivers differing only in
one label gives 0.9078 vs 0.9134 — so the readout is **insensitive to distractor identity** at the
0.006 level. That is a free specificity check the design did not ask for.

### Next

Qwen3 level-A (`818651/2/3`) is running. The `RAH-PR-009` selection — maximise the **minimum** uplift
across level-A banks and **both** models — is applied only when those land, and is then frozen as
part of `RAH-PR-005`.

---

## `RAH-R-010` — Stage-A COMPLETE: the configuration selected by the registered rule — 2026-08-30

**Status: DIAGNOSTIC (instrument selection). P3 complete. This is the INPUT to the `RAH-PR-005`
freeze, not the freeze itself.**

Six level-A runs (3 banks × 2 models), 20 configurations each, selected by
`scripts/rah_select_config.py` — a pure deterministic function, 8 unit tests, run over the committed
grid so a reviewer can re-run it and assert equality.

### Eligible cells, ranked by the rule registered in `RAH-PR-009`

| form | depth | R (Llama/Qwen3) | **min uplift over runs** | min over concepts | min support above band |
|---|---|---|---|---|---|
| **`fc_probe_last`** | **0.125** | **4 / 5** | **0.8516** | 0.8516 | **23** |
| `fc_probe_last` | 0.250 | 8 / 10 | 0.8313 | 0.8313 | 8 |
| `id07_raw` | 0.125 | 4 / 5 | 0.7376 | 0.7376 | 10 |
| `fc46` | 0.125 | 4 / 5 | 0.4687 | 0.4687 | 4 |
| `id07_raw` | 0.250 | 8 / 10 | 0.4492 | 0.4492 | 6 |

11 of 16 cells were **rejected for failing the gate on at least one run** — the rule's whole purpose.

### SELECTED

```
form            fc_probe_last     (4-way forced choice, probe last, assistant-side "Answer:")
depth fraction  0.125             -> R = 4 of 32 (Llama), R = 5 of 40 (Qwen3)
min uplift      0.8516            across ALL SIX level-A runs
support         23                donor layers ABOVE the intervention band clear the gate,
                                  on the WORST of the six runs
```

The winner is not marginal (0.8516 vs 0.8313 for the runner-up) and it is the **same configuration**
the level-B GO/NO-GO pre-flight found. `RAH-R-008` pre-committed to reporting a disagreement and
letting level-A win; **there is no disagreement to report.**

`min_uplift_over_runs` equals `min_uplift_over_concepts`, so the `RAH-R-009` donor-set collapse
(`carrot_bomb` and `basket_bomb` sharing byte-identical donors) **does not change the winner**.

### Anti-fishing, made auditable rather than promised

| requirement (`RAH-DR-001` F10) | how it is met |
|---|---|
| the runner cannot compute the `dpo` arm | `grep -cE "intervene\|knockout\|demo_processing_only"` on the Stage-A runner returns **0** — no intervention code path exists |
| selection is a pure deterministic function with a written tie-break | `scripts/rah_select_config.py::select`, 8 unit tests including one proving **max-min beats max-max**, one proving a cell failing on **one** run is ineligible, and one proving support counts **only** layers above the band |
| the full grid is committed | `outputs/boombness/rah_stagea/rah_stagea_selection.json` carries `full_table`, all 16 cells, eligible and rejected |
| level-B cannot leak in | the loader **refuses** any artifact whose bank name contains `rbd` |

### One forced clarification, recorded not applied silently

`RAH-PR-009` wrote the rule over "(form, R)". **R is not commensurable across models** — 32 blocks vs
40 — and the grid was built as `int(n_layers × f)`. The shared axis is the **depth fraction**, and the
rule is applied on it. This is an interpretation, not a change: the design already parameterised R by
fraction. It is written down because an unrecorded interpretation of a registered rule is how a
preregistration quietly stops binding.

### What is still NOT frozen

`RAH-PR-005` must additionally fix, before any level-C forward pass: the **donor position**; the
**donor layer set** (constrained `L > lo`); the **control family** as revised by `RAH-DR-001`
(`D-late` deleted, `D-nomap` / `D-cw` / `D-exch` / `D-mean` / `D-perm` added); the **primary
estimand** (harm-matched margin per S-1, not bare accuracy); the **statistical test**; and the
**equivalence margin** — which per F5 must come from a *nuisance ensemble*, since the receiver is a
single deterministic forward and "repeatability" is float jitter.

### Checklist

```
[x] P2   GO/NO-GO transport pre-flight, both models       RAH-R-008 / RAH-R-009  -> GO
[x] P3   Stage-A calibration on LEVEL-A data              RAH-PR-009 / RAH-R-010
[ ] P4   TRACK-A FREEZE                                   RAH-PR-005
```

---

## `RAH-R-011` — the assay's first smoke: the count-matched key control is INFEASIBLE on this population — 2026-08-30

**Status: DIAGNOSTIC (instrument constraint, found by a liveness smoke).** Per §9.8 this smoke was
read for shapes, hooks, liveness and row counts only — **never** for effect direction.

Job `818854` (Llama × `lantern_poison`, 4 rows, donor L = 14, R = 4) resolved its labels correctly
and then stopped on a **guard in the existing code, firing correctly**:

```
score_behavior.InfeasibleControl: nondemo control draw (strict, seed 28180607):
  query-protected pool 30 < demo count 125. Count-matching is impossible on this row;
  use a capped arm and read control_draw_match_ratio, or shorten the demos.
```

### What this means

The same-band key control asks: *is the effect specific to masking DEMONSTRATION keys, or would
masking an equal number of keys anywhere in the same band do it?* Answering it requires drawing
**as many** non-demo keys as there are demo keys, from the complement that also excludes the request
span (`query_span_positions` — excluding it is review finding M1 and is not optional).

On this population that complement is **30 positions against a 125-key demo block**. The control
**cannot be count-matched**, on this row, at any seed.

> **The RBD population at `n_examples = 8` cannot support a dose-matched non-demo key control.**
> The demonstration block is roughly **4× larger** than the entire protected complement.

This is a property of the stimulus geometry, not of the intervention, and it is worth stating plainly
because the predecessor sprint's *exact* dose match (arms B and C identical in `total_prefill_edits`)
was one of its genuine strengths — and that match was available there only because the control was a
**different band**, not a different key set. `RAH-DR-001` F2 then established that a different band is
**vacuous** at a fixed mid-depth capture site. **Both dose-matched controls are therefore unavailable
to Track A on this population, for two independent reasons.**

### What was done, and what was deliberately not done

The infeasible control is now **recorded, never skipped silently and never substituted**:

* the default key arm becomes the **capped** policy (`nondemo_capped_d1`), which draws what the pool
  allows and writes `control_draw_match_ratio` on every row;
* `InfeasibleControl` is caught **per row**, the reason is stored, and the row count for which the
  arm was unavailable is written into `meta.json`;
* every row additionally carries a **measured** `strict_match_feasible` flag, obtained by actually
  attempting the strict draw — so the infeasibility is a measurement in the artifact, not a claim in
  a comment;
* `base` and `dpo` remain **required**; a row missing either is dropped with a recorded problem. A
  missing *key control* degrades the row rather than killing it, and the degradation is counted.

**What was NOT done:** the capped control is **not** presented as dose-matched. A null on an
under-dosed control is uninterpretable, and `control_draw_match_ratio` is precisely what tells a
reader how far under-dosed it is. Track A's specificity therefore rests primarily on the **donor-side**
controls — `exch` (seeded derangement), `mean`, `perm`, `rand`, and the wrong-concept donor — which
are unaffected by this geometry, with the capped key control reported as a **secondary, explicitly
under-dosed** check.

### Why the smoke was worth running before any science

It cost one 4-row job and it changed the control family. It also confirmed the parts that matter:
labels resolved to the frozen ids (`21109/74265/26290/38899`), `R = 4` at depth 0.125 as frozen by
`RAH-R-010`, band `6-14`, donor layer 14 accepted against `lo = 6`. **No effect direction was read.**

---

## `RAH-R-012` — assay liveness smoke PASSES; the vacuity gate passes empirically — 2026-08-30

**Status: DIAGNOSTIC (liveness only).** Job `819180`, 4 families, Llama × `lantern_poison`,
donor L = 14, R = 4. **Read for shapes, hooks, masks, liveness, dose and row counts only.**
Per §9.8 no effect direction was read and no plan was altered on it.

### Structural criteria — all pass

| check | result |
|---|---|
| rows written | **56** = 4 families × 7 arms × 2 rotations, exactly as expected |
| arms present | `base, dpo, exch, keys, mean, perm, rand` |
| `complete` / `problems` | **true** / **`[]`** |
| option mass | min **0.5715**, median **0.8565** — against a 0.05 gate |
| `attn_implementation` | `{eager}` on every row (S-12) |
| frozen config honoured | `receiver_R = 4` (depth 0.125), `donor_layer = 14`, band `6-14`, `band_lo = 6` |
| receiver geometry | `(q_pos, read_pos) = (66, 74)` — constant across rows, 8 hops, as designed |

### The vacuity gate — the biggest open risk — passes on real data

`RAH-DR-001` F2's hazard was that the `base` and `dpo` donors could be **bit-identical**, letting the
assay report "preserved" on two copies of the same tensor. Measured at donor layer 14:

```
rows with delta EXACTLY zero : 0 of 4
median ||v_dpo - v_base|| / ||v_base|| : 0.6127
median cos(v_base, v_dpo)              : 0.8321
```

**The intervention genuinely moves the captured state at L = 14** — a 61 % relative change. The
constraint `L > lo` is doing its job, and the gate is now an empirical measurement in every artifact
rather than an argument.

### The `RAH-R-011` under-dosing, now quantified

| arm | `n_keys_masked` | `n_prefill_edits` | `n_decode_edits` |
|---|---|---|---|
| `dpo` | 1062 – 1188 | 63 189 – 79 002 | **0** |
| `keys` (capped) | **261** | 30 798 – 34 452 | **0** |

The key control masks **261/1125 = 23.2 %** of the demonstration dose. `strict_match_feasible_rows =
0 of 4` — the strict draw was *attempted on every row and failed on every row*, so `RAH-R-011`'s
claim is a measurement, not an inference. `n_decode_edits = 0` on every intervened row confirms the
prefill-only scope.

### ⚠ One VALIDITY question the smoke raises and CANNOT answer

The smoke shows the instrument produces scorable output with ample option mass. It does **not** show
that a **baseline** donor transports the *mapped concept* — that is an effect-direction question, it
has n = 4, and §9.8 forbids reading it.

But it makes explicit a precondition that must be **preregistered rather than discovered**, and it is
review finding S-6:

> **BASELINE-TRANSPORT PRECONDITION.** If `base` donors do not transport the mapped concept
> detectably above the donor-side controls (`exch`, `mean`, `perm`, `rand`), then there is **nothing
> for the intervention to remove**, and a `base ≈ dpo` result means the instrument measured nothing —
> **not** that the representation was preserved. That outcome is **A-IV (assay invalid /
> CANNOT ANSWER)**, never preservation.

This must be evaluated on the **development** population and written into `RAH-PR-005` as a
precondition on the verdict, computed on the *same rows* the claim is made from. It is recorded here,
before that data exists, so it cannot later be mistaken for a post-hoc escape hatch.

### Checklist

```
[x] P2   donor->receiver assay implemented                 RAH-R-011 / RAH-R-012
[x] P2   liveness smoke: shapes, hooks, dose, row counts   RAH-R-012  -> PASS
[ ] P4   TRACK-A FREEZE                                    RAH-PR-005
```

---

## `RAH-C-009` — the nuisance run crashed on my own code path; a smoke-discipline lesson — 2026-08-30

**Status: CORRECTION (defect in this sprint's own code). No artifact was produced; no claim affected.**

Job `819307` (Llama, nuisance ensemble) captured **40/40 donors**, built its **8 receiver variants**,
and then died:

```
File "src/boombness/rah_transport_assay.py", line 417, in main
    arms = {"base": vb, "dpo": r["vectors"]["dpo"], ...
KeyError: 'dpo'
```

**Cause.** `--nuisance-ensemble` restricts the live arms to `("base",)` — deliberately, so the run
that produces the equivalence margin cannot see the effect. But the decode loop still referenced the
`dpo` vector unconditionally. The donor-side controls (`exch`, `mean`, `perm`, `rand`) are derived
from `base` and were fine; only the **live** arms are conditional.

**Fixed:** the arms dict is built from `base` plus the derived controls, and the live arms are added
**only if they were constructed**. `819308` (the Qwen3 twin) was cancelled before it reached the same
line rather than left to burn a GPU allocation on a known crash.

### The lesson, which is the actual finding

> **I smoke-tested the SCRIPT and not the new MODE.** `RAH-R-012`'s smoke exercised the default path
> (`base, dpo, keys`) and passed cleanly. `--nuisance-ensemble` is a *different code path through the
> same script*, and it had never been executed before a 40-row, two-model job was submitted on it.

§9.8 says a smoke validates shapes, hooks, liveness and row counts — it does not say *"of the script"*.
It should be read as **of every path a run can take**. The cost here was one wasted 16-minute weight
load; the same omission on a path that *silently* produced wrong numbers instead of crashing would
have been far more expensive. The crash was the good outcome, and only because the missing arm was
referenced by key rather than defaulted — a `.get("dpo")` there would have produced `None` and, one
line later, a plausible wrong number. That is the `stats.get(k, 0)` defect class (`RAH-R-002-b`)
arriving in my own new code.

**Standing rule added for this sprint:** a new *mode*, flag or branch is smoked at minimum size
before it is run at scale, exactly as a new script is.

---

## `RAH-R-013` — the equivalence margin, and the BASELINE-TRANSPORT PRECONDITION FAILS at the frozen configuration — 2026-08-30

**Status: DIAGNOSTIC, on DEVELOPMENT (level-A) data. This is the precondition registered in
`RAH-R-012` before this data existed, firing exactly as written.**

Runs `nuis_p_cb_20260830_215702` (Llama) and `nuis_q_cb_20260830_220236` (Qwen3): 40/40 families,
**1600 rows each**, `problems: 0`, `live_arms = ['base']`, **no intervened arm constructed**.

### The equivalence margin — derived and ATTAINABLE

| | |
|---|---|
| nuisance ensemble | 4 option orders × 2 receiver wordings = 8 variants, base donors only |
| `s_accuracy` (p95 of pairwise \|Δaccuracy\|, worst model) | **0.0750** |
| floor (repo T3/T5 precedent) | 0.10 |
| **MARGIN** | **0.10** |
| rule-of-three at n = 40 | 0.0750 → **equivalence is ATTAINABLE** |

The check `RAH-DR-002` F5 warned about is now satisfied *and shown to be satisfied*: a
repeatability-derived margin (~1e-6) would have made `EQUIVALENT` unreachable for every dataset.
The nuisance-derived margin does not.

### The precondition fails, and the reason is specific

At the frozen configuration — `fc_probe_last`, R at depth 0.125, donor layer 14 (Llama) / 17 (Qwen3),
captured at the **codeword position of a `natural_doublespeak` prompt** — the base donor transports
**the codeword, not the mapped concept**:

| model | argmax over 40 families | mean P(codeword) | mean P(concept) | mean option mass |
|---|---|---|---|---|
| Llama × `carrot↔bomb` | **`carrot` 40/40** | **0.6987** | **1.6e-05** | 0.699 |
| Qwen3 × `carrot↔bomb` | **`carrot` 40/40** | **1.0000** | **0.0** | 1.000 |

Donor-side controls behave sensibly and rule out the trivial explanations:

* `exch` (a seeded derangement — another family's base donor) also decodes to `carrot`, but is
  **not** identical to `base` per family (**0/40 identical**) and the donor norms vary across
  families (sd 0.129 / 3.703). So the donors *are* family-specific; they simply all encode the same
  surface word.
* `perm` and `rand` (norm-matched, direction-destroyed) decode to `ticket` — a *different* label —
  so the receiver is not stuck on one answer regardless of input.
* the unpatched receiver prior on the concept is 0.0053 (Llama) / 0.0001 (Qwen3), so 40/40 `carrot`
  is a patch effect, not a prior.

> **The instrument transports the SURFACE TOKEN, and at this layer and position there is no mapped
> concept in it to transport.** The positive control (`RAH-R-008`/`RAH-R-009`) reached
> P(concept) 0.84–1.00 — but it captured at the **concept** token of a `direct_harmful` prompt,
> where the concept is literally present. That was always closer to a copy test, as `RAH-R-009`
> recorded at the time.

### What this licenses, and what it does not

**It does NOT license "the representation does not exist."** The predecessor sprint measured the
model answering the binding question correctly **78/80** on Llama — the mapping is behaviourally
available. What is established is narrower and it is about the *instrument*:

> At donor layer 14/17 and the query-codeword position, the mapped concept is **not present in a
> form this channel transports**. Baseline transport is therefore ~0, and **there is nothing for
> `demo_processing_only` to remove**. A `base ≈ dpo` result here would mean the instrument measured
> nothing — **outcome A-IV (assay invalid), never preservation.**

This is exactly why the precondition was registered in advance. **No Track-A confirmatory claim may
be made at this configuration.**

### `RAH-PR-010` — the one small follow-up the stopping rule permits

§8 permits *"a small predeclared follow-up testing whether the representation moved earlier or later,
as a NEW preregistration"*, and forbids searching layers until one works. Registered now:

| | |
|---|---|
| question | **is there ANY donor layer at which the codeword position transports the mapped concept?** |
| data | **level-A discovery only** (`carrot↔bomb`), both models |
| donor | `natural_doublespeak` × `behavioral`, `n_examples = 8`, captured at the last codeword occurrence — 8 donors |
| sweep | **every** donor layer `L ∈ [0, n_layers−2]` × the 5 receiver layers, via the EXISTING pre-flight sweep (`--donor-condition natural_doublespeak`) — no new sweep code |
| effect-blindness | the pre-flight has **no intervention code path** (`grep` returns 0), so this cannot see `dpo` |
| outcome if some layer transports | that layer is a candidate; it must then be **re-derived on held-out material** before any freeze, and `L > lo` still binds |
| **outcome if NO layer transports** | **Track A returns A-IV on this construction**: the codeword position carries no transportable mapped concept at any depth, and the donor→receiver design cannot answer the sprint's question. That is a **sourced negative**, reported as such. |

**We do not lower the gate, and we do not switch to a different donor position to find a signal.**
A position change would be a new construction, not a follow-up, and would need its own registration.

### Checklist

```
[x] margin derived and ATTAINABLE (0.10, rule-of-three 0.075 at n=40)   RAH-R-013
[!] P4  TRACK-A FREEZE BLOCKED -- baseline transport fails the precondition
[~] RAH-PR-010  donor-layer sweep at the codeword position (level-A, base only)
```

---

## `RAH-DR-003` / `RAH-C-010` — six of my own published claims were wrong; one correction makes the main result STRONGER — 2026-08-30

**Status: DEEP REVIEW + CORRECTION PASS.** Four read-only lenses (claims · code · quantifiers ·
corrections) plus an adjudicator, 5 agents, 246 tool calls, over every entry from `RAH-R-008` onward.
**Every finding below was re-verified by me from raw artifacts before being accepted**, and two of the
lenses' proposed fixes were themselves wrong and are not applied (see A2).

**No conclusion of the sprint reverses. Six statements were overstated, one control is vacuous, and
one alternative explanation I said was still open is now CLOSED — against my own null.**

### `A4` — the correction that matters most, and it strengthens `RAH-R-013`

`RAH-R-013` defended a **level-A** null by citing binding **78/80**, which is a **level-B**
(`lantern_poison`) number. That is exactly the cross-population substitution `RBD-C-017` was raised
for. The dose-matched **level-A** number exists, and I recomputed it from raw rows
(`semantic_forced_choice`, `natural_doublespeak`, `A_baseline`, predicate `p_concept > p_codeword`):

| `carrot↔bomb`, level A | n_ex=1 | 2 | 4 | **8 (the assay dose)** |
|---|---|---|---|---|
| Llama (`p5A_main_20260828_014436`) | 8/12 | 11/12 | 11/12 | **12/12 = 1.000** |
| Qwen3 (`q2A_20260825_101300`) | 6/12 | 7/12 | 9/12 | **10/12 = 0.833** |

> **This CLOSES the one alternative explanation I said the layer sweep could not answer.** The
> mapping **is** installed, at the assay's own dose, on the **same bank** where transport sits at the
> floor — 12/12 on Llama. So the null is **not** an artifact of a bank that failed to install the
> mapping. `RAH-R-013` is *stronger* than when it was written, and the `lantern_poison` control I
> prepared for this purpose is **no longer needed for it**.

### `A1` — "a patch effect, not a prior" is FALSE on Qwen3 as written

I cited the prior on the **concept** to license a claim about the **codeword** argmax. Recomputed
per rotation, frozen form:

| | Llama unpatched argmax | Qwen3 unpatched argmax | Qwen3 prior P(carrot) |
|---|---|---|---|
| rot0 | ticket | **carrot** | **0.0705** |
| rot1 | ticket | ticket | 0.0275 |
| rot2 | ticket | ticket | 0.0515 |
| rot3 | ticket | **carrot** | **0.3123** |

**Corrected:** on **Llama** the unpatched argmax is `ticket` on **160/160** rows, so 40/40 `carrot`
*is* a patch effect. On **Qwen3** the unpatched receiver already argmaxes `carrot` in **2 of 4
rotations**, so the argmax alone is not evidence there — the Qwen3 patch effect is the **probability**
move 0.115 → 0.99999, not the identity of the argmax. **No lens caught this; the adjudicator did.**

### `A2` — the headline table was `rot0` only, labelled as "the frozen configuration"

The frozen configuration is the frozen *form* over **all four rotations** (n = 160), not one rotation
(n = 40). Recomputed:

| | published (rot0, n=40) | **corrected (frozen form, 4 rotations, n=160)** |
|---|---|---|
| Llama argmax | carrot 40/40 | **carrot 160/160** |
| Llama mean P(codeword) | 0.6987 | **0.6938** |
| Llama mean P(concept) | 1.6e-05 | **4.373e-06** |
| Qwen3 mean P(codeword) | 1.0000 | **1.0000** |
| Qwen3 mean P(concept) | 0.0 | **3.166e-12** |

**The qualitative claim survives unchanged.** ⚠ Two lenses proposed publishing the **8-variant** pool
instead; that is **wrong** — it includes `fc_probe_last_v2`, which is *not* the frozen configuration
the sentence is about. Adjudicated from source; the middle column is what is published.

### `A3` — the "~96×" crosses two receiver forms and two donor layers

0.0088 is `fc46 @ R=28, L=19`; 0.8421 is `fc_probe_last @ R=4, L=3`. **Corrected:** like-for-like,
moving injection R=28 → R=4 takes `fc46` from **0.0088 → 0.2771 (31×)** and `fc_probe_last` from
**0.0065 → 0.8421 (130×)** — the 130× figure the same entry already states correctly six lines
earlier. **The 96× must not be quoted.**

### `A5` — "all five recorded positive-control failures" is wrong in count and in mechanism

The corpus holds **seven** artifacts, and `readout_layer` is **`n_layers − 2`** (30) in the two
`multiconcept_necsuff_llama8b` runs, not `n_layers − 4`. **Corrected:** *"the seven recorded
positive-control failures, all of which injected within the last 2–4 blocks. **Only the `46`
configuration was re-run here; the other six are consistent with, not demonstrated by, this
result.**"*

### `A6` — "Every form works at R = 4–8" is falsified by my own table

`id07_tmpl` has `positive_control_ok = False` at **all five** R (its maximum, 0.0572, is at
**R = 28**), and `fc46` fails at R = 8. **Corrected:** *"Three of four forms pass at R = 4 and two at
R = 8; every **passing** form dies at R ≥ 16. An early injection layer is **necessary but not
sufficient** — `id07_tmpl` fails at every R, so the receiver form matters too."* The heading
*"it is the RECEIVER INJECTION LAYER, and nothing else"* is withdrawn.

### `B1` — my registered precondition is VACUOUS against two of the controls it names

`rah_transport_assay.py` deranges over the **full** donor list and the receiver prompt is
family-independent, so `{v_exch}` is a **permutation** of `{v_base}`. Verified directly:

```
sorted(base p(concept)) == sorted(exch p(concept))  ->  True   (n=160, BOTH models)
```

**`exch` therefore cannot differ from `base` on ANY aggregate statistic, by construction.** The
baseline-transport precondition (`RAH-R-012`) names `exch` and `mean` among the controls base must
clear — **that part of it was unfalsifiable.**

**It does not change the verdict**, because the informative controls are `perm` and `rand`, and base
sits **below** them (base 4.4e-06 against perm 0.011 and rand 0.030 on Llama). **Corrected:** `exch`
is a **paired per-family** control only and is removed from the aggregate precondition; the
precondition now reads *"base must exceed the OFF-MANIFOLD controls (`perm`, `rand`)"*.

### `B2` — the margin is the imported floor; the ensemble contributed almost nothing

`accuracy_by_variant` is **0.0 in 15 of 16** model×variant cells. The single nonzero is Llama
`fc_probe_last_v2|rot1` = 0.075 = **3 families of 40**. **Corrected:** *"MARGIN = 0.10 is the
repository's T3/T5 floor. The nuisance ensemble measured s = 0.075 from **one** variant on **one**
model (3 of 40 families) and did **not** bind. Without the floor, `rule_of_three = 0.075 < 0.075` is
False and equivalence would be **UNREACHABLE** — the attainability in `RAH-R-013` is supplied by the
floor, not earned by the ensemble."* Presenting 0.075 and 3/40 as two independent quantities was
misleading; they are the same three families.

### What this pass says about the sprint

Six overstatements, one vacuous control, **zero arithmetic errors** — the same signature as
`RAH-DR-002` and as the predecessor sprint's two audits. **The numbers keep being right and the
sentences around them keep being wrong.** The recurring shape is a claim whose *scope* is wider than
the population it was computed on (A1, A2, A4, A5, A6) — which is precisely §9.4's quantifier rule,
and I have now violated it five times in one day despite auditing for it.

**The `lantern_poison` base-transport control is no longer required for `RAH-R-013`** (A4 closed that
question). It is **not** run.

---

## `RAH-R-014` / `RAH-C-011` — the mapped concept IS transportable from the codeword position; the FROZEN configuration is the wrong instrument for the question — 2026-08-30

**Status: DIAGNOSTIC on level-A development data. `RAH-PR-010` answered. It CORRECTS `RAH-R-013`.**

Runs `basesweep_p_cb_20260830_221814` / `basesweep_q_cb_20260830_222108`: donor =
`natural_doublespeak` × `behavioral`, `n_examples = 8`, captured at the **codeword** (`' carrot'` on
every donor), 8 donors, every donor layer × 5 receiver layers × 4 forms. **No intervention exists in
this program**, so the sweep is effect-blind.

### The answer to `RAH-PR-010`: YES, at some configurations

P(concept = `bomb`), best over donor layers; `*` = passes the three-conjunct gate:

| form | Llama R=4 | R=8 | R=16 | R=24 | R=28 |
|---|---|---|---|---|---|
| `id07_raw` | 0.0163 | 0.0282 | 0.0350 | 0.0161 | 0.0236 |
| `id07_tmpl` | 0.0223 | 0.0304 | 0.0408 | 0.0113 | 0.0174 |
| **`fc_probe_last`** (FROZEN) | 0.0223 | 0.0086 | 0.0131 | 0.0085 | 0.0071 |
| `fc46` | 0.1602 | **0.2337\*** | 0.1255 | 0.1022 | 0.0935 |

| form | Qwen3 R=5 | R=10 | R=20 | R=30 | R=36 |
|---|---|---|---|---|---|
| `id07_raw` | **0.3127\*** | **0.3214\*** | **0.3361\*** | **0.3886\*** | **0.1875\*** |
| `id07_tmpl` | **0.4163\*** | **0.4039\*** | **0.4070\*** | **0.4344\*** | **0.2078\*** |
| **`fc_probe_last`** (FROZEN) | 0.0682 | 0.0933 | 0.0003 | 0.0029 | 0.0022 |
| `fc46` | 0.0001 | 3.2e-05 | 5.1e-05 | 4.4e-05 | 1.4e-05 |

### `RAH-C-011` — correcting `RAH-R-013`

`RAH-R-013` said:

> *"at this layer and position there is no mapped concept in it to transport"*

**That is too strong and is withdrawn.** The corrected statement:

> **At the FROZEN configuration (`fc_probe_last`, depth 0.125) the codeword-position donor does not
> transport the mapped concept — on Llama P(concept) 0.022 against P(codeword) 0.037, on Qwen3 0.093
> against 0.484. But OTHER configurations of the same channel DO transport it: `fc46 @ R=8` reaches
> 0.2337 on Llama, and `id07_tmpl` reaches 0.4344 on Qwen3, both beating the codeword.**

Everything `RAH-R-013` measured remains correct — including that base sits below the off-manifold
controls **at the frozen configuration**. What was wrong was the **scope**: a property of one
configuration was written as a property of the position. That is the fifth instance today of the
`RAH-DR-003` signature, and it was caught within one tick by the follow-up the stopping rule required.

### The methodological finding, which is larger than this sprint

> **The receiver configuration selected on the POSITIVE CONTROL is the WORST of the four for the
> actual question.** `fc_probe_last` won Stage A (min uplift 0.8516 across six runs) because it best
> transports a donor captured at the **concept** token, where the concept is literally present. On a
> donor captured at the **codeword** token it is last on Qwen3 and third on Llama. The forms that
> detect the mapped concept — `id07_raw` / `id07_tmpl`, the repetition-style patchscope with **no
> labels in the prompt** — *lost* Stage A.

A plausible mechanism, **stated as a hypothesis and not tested here**: the 4-way forced-choice
receiver prints the codeword as one of its options, so a donor carrying that surface token can win by
lexical match; the repetition receiver names nothing and cannot be won that way. **Not investigated —
that would be branching on partial data.**

**The consequence is procedural and it binds the rest of the sprint:** validating an instrument on a
positive control does **not** establish that it is the right instrument for the phenomenon, and
`RAH-PR-009`'s selection rule — however carefully de-fished — optimised the wrong objective.

### ⚠ What may NOT be done with this

Switching to `id07_tmpl` because it gives a better answer is exactly the form-fishing §14/§35 forbid.
Worse, `RAH-DR-001` **F10** applies directly: Δ = base − dpo, and selecting a configuration that
maximises **base** inflates Δ by selection even though `dpo` was never computed.

Also recorded before it can be quoted: **Llama's only passing cell peaks at donor L = 4, BELOW the
band (`lo = 6`), where base and dpo are bit-identical** — so it is **vacuous for Track A** at its own
optimum. Above the band only **4 of 24** Llama donor layers clear 0.1 (L = 7, 11, 12, 13). Qwen3's
passing layers (L = 30–37) are above its band and are **not** vacuous.

### `RAH-PR-011` — registered now, before any intervened arm is run

| | |
|---|---|
| question | on a configuration where **baseline transport is established**, does `demo_processing_only` reduce it? |
| configuration | selected from the **committed** level-A base-only grid by a deterministic rule, **not by eye**; `L > lo` enforced; Llama's below-band optimum is **ineligible** |
| population | **held-out** — the level-B diagnostic banks, never level A, since level A selected the configuration |
| mandatory reporting (`RAH-DR-001` F10) | Δ at the selected configuration **and** Δ across **every** gate-passing configuration; if the selected cell is an outlier, say so |
| selection bias | acknowledged in advance: selecting on **base** inflates Δ. The all-configurations table is the mitigation, and the claim is scoped as *"on configurations where baseline transport is established"*, never as *"the effect"* |
| Llama status | **may be DECLINED**: 4 of 24 above-band layers clearing 0.1, with the optimum vacuous, may not support a claim. That is decided by the registered rule, not after seeing Δ |

**The `RAH-PR-005` freeze remains BLOCKED** and `fc_probe_last` is **not** frozen for this question.

### Checklist

```
[x] RAH-PR-010  donor-layer sweep at the codeword position   -> RAH-R-014: transport EXISTS
[x] RAH-C-011   RAH-R-013 narrowed from "the position" to "the frozen configuration"
[ ] RAH-PR-011  intervened arm on a transport-established configuration, held-out
[!] P4  TRACK-A FREEZE still blocked
```

---

## `RAH-C-012` / `RAH-R-015` — the selection rule gated at the wrong layer; corrected, Llama is DECLINED — 2026-08-30

**Status: CORRECTION of a rule + SELECTION RESULT. The rule was committed (`5eff51fb`) before being
applied, and its flaw was found by testing its own output.**

### The flaw

`RAH-PR-011`'s first implementation read `positive_control_ok` for eligibility. That flag is computed
by the producing sweep at the **GLOBAL best donor layer** — which may sit **below the band**, where
the base and dpo arms are bit-identical. **A cell could therefore qualify on the strength of a layer
the intervened comparison can never use.** That is `RAH-DR-001` F2 re-entering through the selection
rule rather than through the assay.

Caught by re-testing the three conjuncts at the layer the rule had actually selected:

| model | selected cell | level | uplift | dominance | gate at THAT layer |
|---|---|---|---|---|---|
| Llama | `fc46` R=8, L=11 (global best was **L=4, below band**) | 0.1072 ✓ | **0.1072 − 0.0838 = 0.0234 ✗** | ✓ | **FAIL** |
| Qwen3 | `id07_tmpl` R=30, L=34 | 0.4344 ✓ | **0.4344 − 0.0000 = 0.4344 ✓** | ✓ | **PASS** |

**Llama's apparent transport is largely its receiver's PRIOR.** The `fc46` receiver already places
**0.0838** on `bomb` with no patch at all, so an above-band level of 0.1072 is an uplift of 0.0234.
This is `RAH-DR-003` A1 recurring — a level cited where an uplift was required — and it is exactly
why the uplift conjunct exists.

**Fixed:** the gate is recomputed at the best **above-band** layer, and the per-cell table now prints
`uplift` and `prior` beside the level so a prior-driven cell is visible on sight.

### The selection, under the corrected rule

```
Llama-3.1-8B   DECLINED BY THE RULE
               no cell passes the three conjuncts at its best ABOVE-BAND layer
               with >= 3 such layers clearing the threshold

Qwen3-14B      SELECTED  id07_tmpl, R = 30, donor layer L = 34
               p(concept) 0.4344   uplift 0.4344   p(codeword) 0.0000
               breadth: 8 above-band donor layers clearing the threshold (L = 30..37)
```

**Llama is declined by the rule, not by the result** — no intervened arm has been run on either
model. Qwen3 is also the scientifically decisive model: its binding is what collapsed 75/80 → 9/80.

### What `RAH-PR-011` now runs

| | |
|---|---|
| model | **Qwen3-14B only** |
| configuration | `id07_tmpl`, R = 30, donor L = 34 — selected on **level-A** `carrot↔bomb` |
| population | **HELD-OUT: level-B `lantern_poison`**, 80 families. The configuration was selected on level A and has never seen this bank |
| arms | `base`, `dpo`, capped key control, plus the donor-side controls |
| built-in precondition | the run measures baseline transport **on the held-out bank**. If `base` does not transport there, the configuration did not generalise — reported as such, and no Δ is interpreted |

The assay is now parameterised on `--receiver-form` / `--receiver-R`, with the `RAH-R-010` values as
**defaults**, so every previously committed run still reproduces byte-identically.

⚠ **The declared selection bias stands** (`RAH-DR-001` F10): the configuration was chosen to maximise
**base** transport, so Δ = base − dpo is inflated by selection even though `dpo` was never computed
by the selecting program. The mandatory mitigation — Δ at the selected cell **and** across every
gate-passing cell — is unchanged and will be reported with the result.
