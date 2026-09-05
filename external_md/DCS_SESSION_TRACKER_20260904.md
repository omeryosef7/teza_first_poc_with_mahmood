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
| 6 | `R-052` | the installation **ceiling is structural**: every population with a control has **1** low-installation domain; the only ones with spread (`candle`) are the **source** and have **no control** ⇒ a low-dose block is the only route | ✅ |
| 6 | `PR-022`/`R-053` | ⛔ **NULL branch: attack `C` REPLICATES on Qwen at n=30** (−0.173, p=0.504) — power is **not** the explanation. Qwen also fails `A` and `E`. Within the subrange ρ<sub>ctrl</sub> −0.428 ≈ ρ<sub>KO</sub> −0.601 ⇒ **RTM** | ✅ |
| 6 | — | claim narrowed to **CATEGORICAL** and propagated to summary, `LIVE STATUS` and the figure; card **compressed** and a **per-column width guard** added after text overran the page edge | ✅ |
| 7 | `PR-023` | built the **low-dose block** `R-052` said was the only route — a **derived** preset (`main_ne12`'s convention); byte-identical regeneration test **passes**, shared `cds_n4` sha identical | ✅ |
| 7 | `R-054` | Stages 1–2 **both gates pass**: control **9.20×** headroom, installation **0.708** vs 0.908, **20** domains ≤0.75 (gate 13). Installation is **monotone in dose** | ✅ |
| 7 | `R-055` | ⛔ **NULL branch: attack `C` fails a THIRD time** at **33** domains on purpose-built data (p=0.210) ⇒ power is dead. ✅ The within-range gradient **IS RTM** — control ρ **−0.086 → −0.338** by conditioning alone | ✅ |
| 7 | — | settled claim propagated to summary, `LIVE STATUS`, figure (panel F + card); blocker `0b` **closed** | ✅ |
| 8 | `A-010` | **self code review of the auditor** — `dcs_audit_r041.py` carried three populations' conclusions with **no** verifier. Now 6 checks incl. attack `E`'s **power** (59/60) and a mutant that makes `E` unable to reject | ✅ |
| 8 | `C-034` | ⚠ my verifier bands were **hardcoded** ⇒ one false ANTI-CONSERVATIVE alarm on `E` (0.0767 at n=300; **0.0490** at n=3000) and one **withdrawn** claim from `A-006`. Band now **derived from N** | ✅ |
| 9 | `DCS-036` | the **collaborator draft** was **19 entries stale** and said two answered questions were still open. Rewritten; the **−0.907** is now an explicit do-not-send | ✅ |
| 9 | `C-035` | ⚠ our **novelty claim** overstated us by the literature matrix's **own** bar: we clear it on **refusal**, ⛔ not on **ASR**. No number moved — prose true when written became false | ✅ |
| 10 | `R-056` | **`B-009` sized from MEASURED parameters**: power **0.311** at k=38 (which explains `R-019`), **0.814** at k=114. ⛔ Also **corrected my own advice** — splitting across two concepts halves power | ✅ |
| 10 | `PR-024` | preregistered; **78 domains authored** (k=38→116), text audit passes, `test_bank_regenerates_byte_identically` still green (the `C-10` fix) | ✅ |
| 11 | — | pool generation submitted (**850676**), parameters copied from the existing pools' `_meta` — the CLI default seed is **20260816**, the real one **20260828** | ⏳ |
| 11 | `DCS-037` | pool audit **mutation-tested before it judges anything**: 7/7, every refusal fires; the cross-domain-duplicate non-refusal is pinned as a **recorded judgement call** | ✅ |
| 12 | `PR-024a` | ⛔ closed the **comparator freedom** `PR-024` left open — primary is now a **conjunction over all three** controls, no selection; refusal-neutrality selection is discredited (`C-023`) | ✅ |
| 13 | `C-036`/`R-057` | my pool audit **rejected the canonical pools** (27 of them) ⇒ matcher rescoped; **116-domain pool set** built, 464 pools, 0 short, homogeneous | ✅ |
| 13 | `C-037`/`R-058` | ⛔ **real shared-code bug**: collision detector matches `word s?`, repair matched singular only ⇒ plural collisions detectable but **unrepairable**. Fixed; 116-domain bank built, 12 992 rows, 0 violations | ✅ |
| 14 | `C-037b` | ⚠ my own fix was **incomplete** — it reached `sentences` but not `dev`/`heldout`, **the field `build_prompt` actually reads**. Third scope mismatch: guard and builder read different fields | ✅ |
| 14 | `C-037c` | ⚠ **near-miss**: I rebuilt the bank 10 min into a running arm. `prompt_id`s are identical across builds, so pairing would have been **silently wrong**. Cancelled + resubmitted all five | ✅ |
| 14 | `PR-024a` | five arms resubmitted (850792–850796); knockout pre-flight **1160 rows, 0 infeasible_control** | ⏳ |
| 15 | `A-011` | regression test for `C-037`/`C-037b` — and ⚠ **the detector-based invariant MISSES `C-037b`**; only the every-field test catches it. A guard-shaped invariant inherits the guard's blind spots | ✅ |
| 15 | `DCS-038` | the 30-min stall rule says resubmit `850796`; ⛔ **not doing it** — nodelist is already all six nodes and it is queued behind **my own** arms. Reason recorded | ✅ |
| 16 | `R-059` | the two bank halves are **structurally homogeneous** — demo tokens identical to the digit (59.0), so the halves get the same intervention **dose**. Run at 400/1160, before any outcome | ✅ |
| 16 | `DCS-039` | `C-037c`'s wreckage was still on disk under the **live tag prefix**, incl. **53 rows from the pre-fix bank**. Every selector verified to filter on `DONE.json`; dirs **quarantined**, not deleted | ✅ |
| 17 | `DCS-038`→held | `850796` started **on its own** at 23:39, as predicted when I declined the 30-min stall rule. Queued behind my own work, not fair-share | ✅ |
| 17 | `R-060` | **dose matched to the digit** — `keys_masked` 522/378/846 identical for `KO-3`, `d1`, `d2`. Recorded with **nothing judged** | ✅ |
| 18 | `A-012` | self review of `cds_domain_test.py` **before** it computed the primary: 5/5. ⚠ Check 4 failed on **my own simulator** — third audit this phase to fail on its instrument | ✅ |
| 18 | `R-061` | ⛔ **`B-009` NOT RESOLVED** — 1 of 3 on the declared conjunction (p = 0.175 / **0.0096** / 0.466). ⚠ Realised power 0.35/0.65/0.05 explains the pattern; **control spread 0.0586 > effect 0.0391** | ✅ |
| 19 | — | `R-061` propagated: summary `B-009` entry, `LIVE STATUS` blockers + two new must-not-say entries, and the **collaborator ask rewritten** — the question is no longer *more domains or a second concept* | ✅ |
| 20 | `PR-025`/`R-062` | the refusal confound is **regular in direction** (pooled ρ **−0.378**, consistent in all 3 controls, survives the RTM restriction) but ⛔ **not in magnitude** — conversion **0.057–0.350** vs the bracket's assumed **1.000** | ✅ |
| 20 | — | ⚠ `R-062` **corrects `R-061`'s own emphasis**; the overstated *"bracket is unanimous"* framing was propagated out of the log into **both** deliverables, incl. the collaborator draft, and is now fixed there too | ✅ |
| 21 | `PR-026`/`R-063` | calibrated bracket applied **symmetrically**: **[−147,−66] / [−140,−87] / [−129,−29]**, entirely negative for all three and **half the width**. ⛔ `PR-014`'s bracket is wrong at **both** ends. Verdict unchanged: `B-009` **NOT RESOLVED** | ✅ |
| 21 | `C-038` | ⚠ **over-corrected, then over-corrected back** — `R-061` trusted the adjusted end, `R-062` trusted the face end, and on `d3` the face value lies **outside** `R-063`'s interval. Checking a two-ended bracket **one end at a time** makes the other look right by contrast | ✅ |
| 22 | — | `B-009` reaches the **figure**, the last surface: behavioural status rewritten from *direction only* to `NOT RESOLVED` + the control-spread constraint. Width guard caught **9** over-wide lines; card font 7.0→6.2 after read-back showed overflow | ✅ |
| 23 | `A-013` | closing audit: **15/15** preregistrations resolved (by resolving-entry heading, not a regex window — `A-005`'s failure recurred on the first try); **all 5 verifiers + 7 pytest** re-run and green | ✅ |
| 24 | `PR-027`/`R-064` | ⛔ gate **FAILS** (46>40 ✅ but only **4** domains ≤0.25, need >5) ⇒ **stops at Stage 1**. ✅ The 78 NEW domains reproduce the old 38's installation distribution almost exactly (0.900/0.192 vs 0.908/0.197) ⇒ **the ceiling is a PARADIGM property**; low-installation yield **3.45 %**, so ~580 domains would be needed | ✅ |
| 24 | — | `R-064` propagated. ⛔ The figure asserted *"a low-dose block is the only route"* — falsified **twice** since (`R-054` built it and it yielded 1 domain; `R-064` shows ~580 domains is the route). Corrected in figure + summary | ✅ |
| 25 | `C-039` | ⚠ `PR-028` asserted *"the new arms persist the per-row draw positions"* — `score_behavior.py` was **never touched**; the sentence was written from intent, not read off the file. Design unaffected; sentence withdrawn | ✅ |
| 25 | `R-065` | ✅ **`B-007` CLOSED** and its premise was **false**: positions are exactly regenerable from `demo_span_bounds`+`query_span_bounds`+`seq_len`+the recorded seed. **200/200** rows, `match_ratio` median **1.000**. No code change, no schema change, ~600 k ints/arm not written | ✅ |
| 25 | `C-040` | ⚠ `R-065` was right by the wrong route: the positions are **written verbatim** in `control_draw[...]["positions"]`. My probe tested for **key names I guessed** and read absence. ✅ The persisted list supplies the identity check `R-065` lacked — **200/200** exact, `seed+1` mutant **0/200** | ✅ |
| 25 | `R-066` | ✅ **`B-007` and `B-013` are READOUT-ONLY.** Behavioural **46/46** carry the draw, readout **0/20**, **zero counterexamples**; grounded in code (`_readout_knock_fields` never gets `knock_draw`). ⇒ both **CLOSED for the arms that matter**, incl. all 8 `PR-024`/`PR-028` controls; a predicted-refusal control is fittable with **no re-run**. ⛔ `C-027`'s bug class, mirrored | ✅ |
| 26 | `R-067` | ⚠ EXPLORATORY, CPU-only: can refusal be predicted from **mask geometry**? ⛔ **No** on this feature set. The pooled test hits the floor on **7/7** features and is an **arm-level artifact** (k=3 draws, not 3480 rows — `C-016`'s error from a new direction). Within arm: **1/6** sign-consistent, `d3` flips sign on four. ⚠ `min_dist_to_query` is **DEGENERATE** in `d3` (1 distinct value), not null. ✅ Analyzer fixed **before** commit — it first printed `SIGNAL` off the confounded test. Re-run at **k=8** once `PR-028` is judged (floor 0.25 → 0.0078) | ✅ |
| 27 | `A-014` | 4-hourly review (`A-013`+4h34m): **6/6 verifiers**, 9 guards, 341 tests green. ✅ Adversarial audit of the `R-067` analyzer — **5/5** mutations; M1/M2 prove it **detects a planted signal**, so `R-067`'s null is **measured, not vacuous**. ⚠ The audit's own M4 first FAILED on a **hardcoded** threshold — **`C-034` repeated inside the instrument built to catch it**; band now derived from k. ✅ M4 also *measures* the k=3 floor: **7/20 noise features look consistent** | ✅ |
| 27 | — | ⚠ The standing loop prompt is **stale in all four facts** (76 domains/k=114/power 0.814/`B-009` as current work). Actual: **78** domains, **k=116**, realised power **0.65/0.35/0.05**, `B-009` **NOT RESOLVED** (`R-061`). Recorded so no tick rebuilds pools on it | ✅ |
| 28 | `PR-028a` | Analyzer frozen **while the arms generate** (113-351/1160 rows). ✅ Contracts hold on all 5 (`decode_edits` 0, `match_ratio` 1.0, seeds as declared, `keys_masked` ~522). ✅ Calibration rederived from `R-063`'s table to **0.1 rows**; `load_arm` reused; t-tail matches scipy to **1e-11**. ✅ K=3 dry run reproduces `PR-028`'s sizing **exactly** (sd 0.0295, δ −0.0391, p 0.1488 vs 0.149) | ✅ |
| 28 | `PR-028a` | ⛔ Dry run caught the verdict reading **"WELL-POWERED NEGATIVE" at K=3**, where `PR-028` predicts p=0.149 *even if the effect is real* — now gated on K≥8. ⚠ NEW pre-data caveat: the calibration **removes 74% of the between-control spread** (sd 0.0295→0.0076, p 0.149→0.0013), so a calibrated-only p is a property of the **correction**. Quote the c-range + shrinkage, never `c_hi` alone | ✅ |
| 29 | `PR-028b` | Judge **all 10** arms in ONE invocation, **re-judging** the 5 that already have labels: a session offset would hit 5/8 controls but **not `KO-3`**, biasing the primary by (5/8)·offset. The two drift estimates disagree **8×** (0.0020 vs 0.0158 = **3%–25%** of the effect) and `R-049`'s net is only **1.41 sd** from zero ⇒ remove the term, don't assume it. ✅ Re-judge also *settles* that disagreement on 5×1160 byte-identical rows | ✅ |
| 29 | — | ✅ Guard is in the **analyzer**: judge invocation derived from **tag prefix** (exact, not a timestamp heuristic); refuses on mixed sessions, tested both ways. ⛔ Found **two** silent-failure bugs in my own pre-flight — under `set -e -o pipefail` both `ls -d` *and* the `while` loop return non-zero exactly when an arm is unready, killing the script **before** the `REFUSING` line ⇒ exit 1 with **no reason**. Fixed and verified | ✅ |
| 30 | `PR-028c` | Drift analyzer frozen **before any `p28j_` label existed** (arms at 399-682/1160). ⛔ Byte-identity **checked** per row (`completion_sha256_16`), mismatches excluded+counted — the mistake `judge_session_drift.json` records against itself. ✅ Exact binomial on the **net**, matches scipy to **2.8e-16**, and replays `R-049` to **p=0.2379** ⇒ that net was never an established offset | ✅ |
| 30 | — | ✅ Foot-gun closed: `dcs_pr028_primary.py` defaults pointed at **`p24j_`**, so a default run after the re-judge would have **silently mixed sessions** — the very bias `PR-028b` removes, reintroduced by a default. Now `p28j_`; refuses cleanly until it exists; K=3 dry run still reproducible explicitly (δ −0.0391, p 0.1488) | ✅ |

## Live

| what | id | state |
|---|---|---|
| `852000`-`852004` (PR-028, 5 control draws) | `PR-028` | 2 RUNNING (n-802/n-803), 3 PENDING; ~2.7 h each |

## Standing rules being followed this session

* Preregistration and analyzer are committed **before** the numbers they judge.
* `git commit -- <paths>` only — never `git add -A` (`feedback_git_add_all_shared_tree`); the tree is shared.
* A retraction is a **new dated entry**; §1 is frozen; old paragraphs are never edited.
* Plots are a separate surface from prose and need their own retraction sweep (`C-026`).
