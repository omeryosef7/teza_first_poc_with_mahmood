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
| 1 | `PR-017` | preregistered: the gradient on **both headline populations** with the real dose-matched control | ✅ |
| 1 | `R-041` | ✅ **`PR-017` SUPPORTED on the blind primary** — Llama contrast **−0.907**, perm **p = 2.0e-04**. The effect is **graded by installation** | ✅ |
| 1 | `A-006` | self code review of the new statistic: ρ vs scipy 2.2e-16 on tied data, null calibration 0.035/0.0275, mutation harness **3/3 caught** | ✅ |
| 1 | `PR-018` | preregistered + submitted: **manipulate** installation via the never-run `cds_n8` block (849686–849688) | ✅ |
| 1 | `R-042` | ⛔ **the manipulation did not manipulate** — 0.908→0.928, 25/38 domains at ceiling ⇒ predictions 2–3 **VOID** by the prereg's own rule | ✅ |
| 1 | `C-028` | my pre-flight never asked whether the predictor had **room to move** | ✅ |
| 1 | `PR-018a`/`R-043` | the strict control refused; `capped` is legitimate here (ratio 0.9967, not `R-033`'s 0.0). Contrast **−0.404, p = 0.0482**; control ρ **−0.040** | ✅ |
| 1 | `C-029`/`B-013` | my severity estimate for the 11 under-matched rows was wrong; and the per-row ratio is **not persisted** despite the artifact saying it is | ✅ |
| 1 | — | **deliverables re-synced**: summary, `LIVE STATUS`, and `DCS_FIGURES.png` gains **panels F and G**; the PNG was **read back** and three layout defects were fixed (`C-026`) | ✅ |
| 2 | `DCS-033` | `PR-014`'s bounding analyzer committed **while the judge was on arm 5 of 8**; closes the row-assignment freedom the prereg left open | ✅ |
| 2 | `C-030` | ⛔ **`PR-014`'s bound points the wrong way** — the refusal-adjusted end is the **favourable** one, not the hostile one. Caught and corrected **before** the analysis ran | ✅ |
| 2 | `A-007` | self code review of that analyzer: 5/5 pass, incl. `C-030` turned into an **executable invariant** (300/300) and a 3-mutant harness (3/3) | ✅ |
| 2 | `R-044` | exploratory screen: installation is ⛔ **not** a prompt-length or dose artifact (ρ = −0.000, p = 0.9996); 2 of 7 candidates struck as **tautological** | ✅ |
| 2 | `PR-019` → `R-045` | plausibility instrument: reliability gate **FIRED** (5 of 38 over a gate of 4) ⇒ ⛔ `CANNOT ANSWER`; threshold **not** moved | ✅ |
| 2 | `R-046` | ⛔ **`temperature 0` is NOT deterministic** — an identical re-run flipped 1 of 38 rating vectors and moved the gate count 5 → 6 | ✅ |
| 2 | `C-031` | `RUBRIC_B` invents its own settings when given one item; the **strict parser refused**, and the lenient fallback would have mislabelled every domain | ✅ |
| 2 | `R-047` | ⛔ **`PR-019a` STOPS** — `CANNOT ANSWER` on this instrument family, as declared. The available repair is recorded and **not taken** | ✅ |
| 2 | `DCS-034` | `R-046`'s consequence for `PR-014` declared **before** its result exists; new blocker `B-014` | ✅ |
| 3 | `PR-020` | preregistered **while `PR-014` had no result**: measure `B-014`, the judge noise floor on the **attack** rubric | ✅ |
| 3 | `C-032` | ⚠ I repeated `C-018` — two backgrounded commits collided on the index lock; the symptom reads as a bad pathspec, and deleting the lock would have been destructive | ✅ |
| 3 | `R-048` | ⚠ **`PR-014` ANSWERED: `CONFOUND-LIMITED`.** All 6 brackets **straddle zero**; 0 of 6 directional claims survive. Judge-free: `KO-3` removes **150** refusals, buys **+21** attacks (**86 %** do not convert) | ✅ |
| 3 | `C-033` | ⚠ `C-030` named the conservative end **unconditionally**; which end it is depends on the **sign**. Analyzer now reports the **bracket** | ✅ |
| 3 | — | `R-048` propagated to the summary, `LIVE STATUS` and the **figure scope card** (read back and verified) | ✅ |
| 3 | `R-049` | `PR-020` answered: noise floor **18/380** (net +6) — **too small to explain `R-048`**; ✅ `refused` **0/380**, so `C-023` holds and the bound's input is verified deterministic | ✅ |
| 3 | `A-008` | coverage audit: **10 of 10** preregistrations closed, read from the corpus not a regex; both verifier suites re-run **PASS** | ✅ |
| 3 | — | `R-049` propagated to summary + `LIVE STATUS`; `B-014` closed | ✅ |
| 4 | `PR-021` | preregistered + ran the **never-run `benign_literal`** cell (849861) — the codeword present with **no** remapping | ✅ |
| 4 | `R-050` | primary ⛔ **`CANNOT ANSWER`** (1 of 38 domains, gate needed 4). ✅ But: full installation swing **+10.68**; `option_mass` **0.877→0.264** without a mapping; benign demos install a **benign** remapping (` Mushroom` 22/380) | ✅ |
| 4 | `DCS-035` | my watch treated *left `squeue`* as terminal and raced the writer; the **analyzer's** `DONE.json` guard is what covered it | ✅ |
| 4 | — | `R-050` propagated to summary `SCOPE` + `ESTABLISHED` and to `LIVE STATUS` | ✅ |
| 5 | `A-009` | **adversarial audit of `R-041`**, five attacks declared in the committed script first. A/B/E ✅ survive; ⛔ **C lands** (13 varying domains: −0.503, **p = 0.343**); ⛔ **D**: the control's gradient is real | ✅ |
| 5 | `R-051` | `B-015`: ⛔ my preamble mechanism **refuted** (4 populations, all with preamble, ρ = +0.31/−0.04/−0.02/−0.33); `A-009` D narrowed to **population-specific**; ⛔ **the −0.907 headline is inflated** ⇒ quote **ρ<sub>KO</sub> −0.44…−0.73** | ✅ |
| 5 | — | narrowing propagated to summary (new **NARROWED** section), `LIVE STATUS`, and the figure (**panels F and G + card**), PNG read back | ✅ |

## Live

| what | id | state |
|---|---|---|
| *(nothing in flight)* | — | `squeue` **empty**, GPU and CPU. All 10 preregistrations closed |

## Standing rules being followed this session

* Preregistration and analyzer are committed **before** the numbers they judge.
* `git commit -- <paths>` only — never `git add -A` (`feedback_git_add_all_shared_tree`); the tree is shared.
* A retraction is a **new dated entry**; §1 is frozen; old paragraphs are never edited.
* Plots are a separate surface from prose and need their own retraction sweep (`C-026`).
