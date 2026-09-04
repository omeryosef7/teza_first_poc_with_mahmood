# DCS session tracker — 2026-09-04 (continuation)

**Purpose.** A one-screen dashboard for the Doublespeak concept-specific / surgical-causality phase.
The canonical, append-only record is
[`DOUBLESPEAK_CONCEPT_SPECIFIC_BOOMBNESS_AND_SURGICAL_CAUSALITY_PLAN_AND_PROGRESS_20260902.md`](DOUBLESPEAK_CONCEPT_SPECIFIC_BOOMBNESS_AND_SURGICAL_CAUSALITY_PLAN_AND_PROGRESS_20260902.md).
⛔ This file is a **pointer**, not a second source of truth — if the two disagree, the log wins.
Rewritten each tick.

## Where the session picked up

Inherited state at `06157b87`: `PR-015` in flight (849114–849119), `PR-014` `BLOCKED-ON-CREDITS`
(`C-024`), queue otherwise empty, 14 of 15 preregistrations closed (`A-005`).

## What this session has done

| tick | id | what | status |
|---|---|---|---|
| 1 | — | `PR-015` jobs verified `COMPLETED`, 6 dirs, declared row counts | ✅ |
| 1 | `R-037` | `PR-015` **Part A** layer placebo → **INTERMEDIATE** (13.6 % / 17.2 %, opposite sign); ⛔ falsifies "15–23 is inert" off the `cds38` bank | ✅ |
| 1 | `R-038` | `PR-015` **Part B** n=16 dose test → my *weak-mapping* excuse **NOT supported**; 6+/14− at both doses | ✅ |
| 1 | `R-039` | ⚠ EXPLORATORY: the effect is **graded by installation**; 18/20 sign concordance across an independent dose doubling | ✅ |
| 1 | — | OpenAI credits re-probed live (HTTP 200) ⇒ `C-024` lifted; `PR-014` judging submitted (**849653**) | ⏳ running |
| 1 | `PR-016` | preregistered **with its analyzer**, three limits declared first | ✅ |
| 1 | `R-040` | `PR-016` → **RANGE-LIMITED**; contrast given a direct permutation p (0.0749) rather than the `C-017` error | ✅ |
| 1 | `C-027` | ⚠ `PR-016`'s limit #2 was **FALSE** — probed the behavioral arm instead of the readout arm | ✅ |
| 1 | `PR-017` | preregistered: the gradient on **both headline populations** with the real dose-matched control | ⏳ |

## Live

| what | id | state |
|---|---|---|
| `PR-014` Qwen behavioural judging, 8 arms, one invocation | 849653 | ⏳ `cpu-killable`, running |
| `PR-017` headline installation gradient | — | ⏳ analysis-only, runs once its prereg commit lands |

## Standing rules being followed this session

* Preregistration and analyzer are committed **before** the numbers they judge.
* `git commit -- <paths>` only — never `git add -A` (`feedback_git_add_all_shared_tree`); the tree is shared.
* A retraction is a **new dated entry**; §1 is frozen; old paragraphs are never edited.
* Plots are a separate surface from prose and need their own retraction sweep (`C-026`).
