# PART 2 — what we did between 2026-09-05 20:00 and 2026-09-06 19:18

**This file is a continuation. It is self-contained and does not edit Part 1.**

| | |
|---|---|
| **Part 1** | `reports/SPRINT_SUMMARY_2026-09-02_TO_09-05.md` — covers 2026-09-02 00:25 → 2026-09-05 19:47, ending at commit `8fb3c7e3` (`DCS-C-046`). |
| **Part 2 (this file)** | covers **`8fb3c7e3` → `b80db84d`**, 2026-09-05 19:47 → 2026-09-06 19:18. **105 commits.** |

**The boundary is exact.** Part 1 ends with `C-046` and the continuation plan it produced. This file
begins with what that plan's item #1 became (`PR-030`), and then follows a **new phase log** opened
2026-09-05 20:54:

> `external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`
> — **5,281 lines, §0–§75.** The `DCS-` id namespace continues from the older log, which stays
> authoritative for everything up to `R-077` / `C-047`.

**New ids in this window:** results `R-077`…`R-097`, preregistrations `PR-030`…`PR-045`, corrections
`C-047`…`C-071`, audits `A-019`…`A-033`, blockers `B-017`…`B-021`, questions `Q-001`…`Q-005`,
process entries `DCS-040`…`DCS-044`.

**Same rules as Part 1.** Every headline below was re-checked against the producing JSON artifact
and/or the producing script by independent agents; §19 reports what matched, what could not be
checked, and every defect found. Caveats travel in the same block as the number they bound.

**Reading rule inherited from the phase's own deliverable:** in three cases (`R-086`, `R-092`,
`R-093`) the caveat changes what the number is allowed to mean.

---

## Contents

1. [Orientation — the new question and its vocabulary](#1-orientation)
2. [Closing the old phase: PR-029, PR-030/R-077, C-047](#2-closing)
3. [The new phase: what it was for, and its stage plan](#3-phase)
4. [The preregistration, and its two void-and-respecify cycles](#4-preg)
5. [The headline — R-086 / R-089: a concept-specific state, POSITIVE](#5-headline)
6. [R-091 — the remapping axis and the concept axis are different directions](#6-axes)
7. [The K ladder — R-079/R-080/R-081/R-082 and PR-037/R-083](#7-kladder)
8. [Gate R3 — R-092 FAILS, and C-066 says why](#8-r3)
9. [Gate R5 — R-093, the readout/representation dissociation](#9-r5)
10. [Gates R6, §13 and R8 — three CANNOT ANSWERs, each for a different reason](#10-gates)
11. [PHASE 4 — R-088: the intuitive readout is blind](#11-phase4)
12. [R-085 — the control masks are not row-independent](#12-r085)
13. [Literature — the novelty claim narrows twice](#13-lit)
14. [The scoreboard: gate ledger, established, retracted, must-not-say](#14-scoreboard)
15. [Corrections and bug catalogue — the methodological record](#15-corrections)
16. [Code and artifacts produced](#16-code)
17. [Blockers and the five open questions for Omer](#17-blockers)
18. [Live state at 2026-09-06 19:18](#18-live)
19. [Independent verification of this document's numbers](#19-verification)

---

<a name="1-orientation"></a>
## 1. Orientation — the new question and its vocabulary

### 1.1 The question this phase exists to answer

Prior work (Part 1) established that the demonstration→query attention path is causally **necessary**
for the codeword→concept remapping. Matan's question, stated falsifiably:

> Is there an internal quantity that specifically means **"the codeword is being represented as
> BOMB"**, as opposed to *generic harmfulness*, *generic remapping*, *contextual shift*, *template
> identity*, or *demonstration presence*?

I.e. is the state the knockout destroys a **concept-specific** state, or merely a *"this word has
been remapped to something"* state? The inherited answer was a weak negative under one instrument
(`R-002`), which the phase notes was *"a replication across concepts, NOT a specificity control"*,
had pre-aggregated cell means so **no test statistic**, and put each concept in a separate bank with
its own anchor.

### 1.2 New vocabulary (beyond Part 1 §1)

- **Cells.** Part 1 used `A` (`benign_literal`), `B` (`direct_harmful`), `C` (`natural_doublespeak`,
  the attack cell), `E` (`concept_in_benign_ctx`). This phase adds **`F` = `benign_remap`** — the
  codeword remapped to a *benign* source word (`REMAP_SOURCE_WORD = "bicycle"`). Cell `F` is the only
  comparator that separates *bomb* from **generic remapping** rather than from another weapon.
- **The concept banks.** Eight banks, `{button, basket} × {bomb, knife, gun, club}`, preset `main`,
  **6 domains**, 288 rows each. `A-019` verified the four concepts' demonstration pools are
  **independently authored** (harm sentences differ in substance, not by word substitution), so the
  concept is genuinely carried by the demonstrations. ⚠ These are **6-domain `main` banks** — a
  different population and preset from the 38/116-domain `main_longpre_cds` banks where Part 1's
  causal results live.
- **Probes `P1` and `P2`.**

  | id | train | test | a PASS means | what surface-token identity can do |
  |---|---|---|---|---|
  | **P1** | cell `B` (+ cell `A` as `literal`) | cell `C` | the codeword's state is concept-specific **in the same code** the model uses for the explicit concept word | solves training for free; cannot solve the test |
  | **P2** | cell `C` of the 5 train domains | cell `C` of the held-out domain | the codeword's state carries **which** concept was installed | **nothing** — the surface token is `button`/`basket` in every row of every class |

  After `A-020`, **`P2` is the sole primary and `P1` a reported secondary.**
- **Gates `R1`–`R8`** are the brief's own gate family (`R3` lexical transfer, `R5` does the knockout
  destroy the concept signal, `R6` the same under `KO-1`, `R8` does destruction predict behaviour,
  plus §13 — read the concept signal at the explicit concept word). The ledger is in §14.1.
- **The independence unit is the DOMAIN, n = 6.** A two-sided sign test at n = 6 has an **attainable
  floor of 2/2⁶ = 0.03125**, so *any Holm family with m ≥ 2 is UNINFORMATIVE BY CONSTRUCTION*. This
  single arithmetic fact shapes nearly every design in this phase: **exactly one significance test**
  per preregistration, everything else descriptive with no p-value.

### 1.3 Three design facts established before any data, that shaped everything

1. ⛔ **`semantic_forced_choice` LEAKS THE CONCEPT and cannot carry the probe** (`A-019` §2.3).
   Its question names both options (*"…does `button` refer to a button or to a **bomb**?"*), where the
   final word varies by bank, so a classifier on late-position hidden states could separate concepts
   by reading the **question**. Verified by `A-021`: the concept appears in **72/72** cell-`C` question
   texts for every one of bomb/knife/gun/club, and **0/288** for `comprehension_usage` and
   `semantic_one_word`. Called *"the single most consequential design fact found in this audit."*
   ⇒ It remains the **installation/prompt-validation endpoint**; it is never a probe channel.
   *Leakage disqualifies a channel for a **probe**, not for an **endpoint**.*
2. ⛔ **`prompt_id` IS NOT A KEY.** It is identical across all eight banks — **2736/2736 shared**
   between any two. Joining on it alone silently merges eight populations. Every join in this phase
   uses the compound key **`(bank_file_sha16, prompt_id)`**.
3. ⛔ **`club` is contaminated** (`A-020` §8.3). Its pools use the social-club / room sense, not the
   weapon sense, in three domains. **Excluded from the primary composite on mechanistic, pre-outcome
   grounds** — the exclusion reads demonstration text alone and would be identical whatever the
   result. It is still run and reported in full, and it becomes the **control** class.

---

<a name="2-closing"></a>
## 2. Closing the old phase: `PR-029`, `PR-030`/`R-077`, `C-047`

Part 1 ended with `PR-029` (extend the control population to K = 32, 24 draws, ~55 GPU-h) live in the
queue. Three things then happened.

### 2.1 `PR-030` / `R-077` — the gate that ran *while the spend was in flight*

Continuation-plan item #1, written and committed **before it was run**, on data already on disk, at
**0 GPU-h**. Its point: `PR-029` is buying 24 draws to divide `R-075`'s between-control sd of
**0.0783** by √K, *and that arithmetic is only valid if the 0.0783 is a real per-draw offset.* The
phase had quoted the series **0.0295 → 0.0586 → 0.0783** as pure draw heterogeneity and **never
subtracted the row and judge floors**.

Branches were declared before looking, including one that would **cancel a spend mid-flight**.
Result (`scripts/dcs_draw_offset_reliability.py`, K = 8 arms × 116 domains):

- **Split-half reliability**, Spearman-Brown corrected, unit = arm, **400 splits**:
  **median ρ = +0.988**, 95% band [+0.923, +1.000]; permuted-arm null median +0.047.
  ⇒ *An arm's ASR on half the domains predicts its ASR on the other half almost perfectly.*
- **Variance decomposition** of the observed between-arm variance **0.006126**:

  | component | variance | share |
  |---|---|---|
  | within-arm sampling (ICC 0.097, m = 10 ⇒ design effect 1.87) | 0.000322 | **5.3 %** |
  | judge instability (empirical, from `R-074`'s byte-identical re-judge) | 0.000076 | **1.2 %** |
  | **DRAW OFFSET** | **0.005728** | **93.5 %** |

**VERDICT: `REAL DRAW OFFSET`.** The K ladder is well specified; the √K arithmetic divides a quantity
that is really there. ⚠ *"This is the first time the phase has decomposed that number instead of
quoting it"* — which happens to vindicate the earlier usage, but was not established before and could
as easily have gone the other way.

⇒ **This upgrades `R-075` from a nuisance into a target.** The 25-fold spread in induced refusal at
identical dose is **not noise to be averaged away** — it is a **reproducible function of which
positions the mask hits** (ρ = 0.988). ⛔ `R-076` already excluded the seven positional-geometry
features as that function, so the search must move to what the masked keys were **carrying**, not
where they sat.

### 2.2 `C-047` — `PR-029`'s six arms ran the wrong script and produced nothing

All six jobs (**853040–853045**) exited **`COMPLETED`, exit `0:0`**, in 11–27 min against an expected
~2.3 h, and **no `dcsp29_*` directory exists**.

**Cause:** the submission passed `--export=ALL,ARGSFILE=…` — *a variable the runner never reads*.
`src/boombness/slurm/run_boombness.sh` reads `BOOMB_SCRIPT` and `BOOMB_ARGSFILE`, and the silencing
detail is that **`BOOMB_SCRIPT` defaults to `extract_boombness.py` (line 56)**. Every job fell through
to the default and ran the extraction pipeline on its own default config. The correct form is
documented in that script's own header at lines 34–41.

**Why nothing caught it:** `sacct` says `COMPLETED 0:0` — *the jobs did succeed, at the wrong task.*
⇒ **Every guard this phase owns checks artifacts** (`DONE.json`, row counts, contracts, prompt
hashes); **none checks that the artifact expected was even attempted.** A missing arm looks identical
to an arm not yet started.

Cost ~1.7 GPU-h; no scientific result affected. The six stray runs were quarantined to
`VOID_wrongscript_*` (third time in the phase that wreckage under a live prefix had to be
quarantined). **Standing rule adopted:** read the `boombness:` line and the `args:` line of every new
job's log before trusting any artifact from it — it costs nothing and would have caught this in
minutes.

### 2.3 `PR-029`'s final status

**Preregistered, frozen, submitted, void by execution error, resumable, currently halted, zero
results.** The 24 argsfiles at `runargs/dcs/dcsp29_*.txt` are committed and valid, with the correct
submission form recorded verbatim. `R-077` explicitly cleared it to proceed. It was **not** resumed —
Omer stopped the work — and its own sizing gives power **0.34** against the observed −0.0222.

### 2.4 `DCS-040` — an operational rule that mis-predicts

The standing "cap 2 model-loading jobs per node" rule failed. Three jobs on n-805 loaded weights in
seconds; the single job on n-802 sat at 25% after 9:28 (~1000× slower). Cause, checked not assumed:
n-805's other occupants were 7–13 hours old, long past their I/O phase; n-802 carried another user's
job started 12 minutes earlier — loading **concurrently**. ⇒ Weight-load time is set by how many jobs
are loading on that node *at that moment*, regardless of owner. Not actionable as a placement
constraint (other users' start times aren't visible before submitting). What **is** actionable: never
infer a stall from elapsed time — read the progress bar.

---

<a name="3-phase"></a>
## 3. The new phase: what it was for, and its stage plan

Opened 2026-09-05 20:54 at commit `32634ceb`, SLURM empty.

**§0.1 — exclusive control, obtained by negotiation.** Five Claude sessions had the repo as cwd. No
process was killed: a `kill -TERM` was attempted and **refused by the harness permission classifier**,
and coordination was achieved by messaging, which preserved a peer's in-progress `C-047` write-up.
All peers confirmed in writing they would not submit jobs, write to `external_md/` or `reports/`, or
commit. ⚠ The lock is **advisory** — tree and git index are shared, so only `git commit -- <paths>`
is safe. This happened **twice more** (`DCS-042` was the second takeover; the log records this as the
third exclusivity assertion on the branch).

**§5 — the stage plan.**

| stage | content | cost | gate |
|---|---|---|---|
| **S1** | `PR-031` — concept specificity on the leakage-safe readout, 8 banks, readout-only | ~1–2 GPU-h | decides whether "Bombness" is sayable at all |
| **S2** | direct semantic agreement: `comprehension_usage` vs the forced-choice family | 0 GPU-h | rides S1 |
| **S3** | causal validation of whatever S1 promotes | ~2 GPU-h | only if S1 promotes a score |
| **S4** | the surgical row ladder K = 3…7, readout-only, no judge | ~3 GPU-h | independent; runs regardless |
| **S5** | domain-level representation ↔ behaviour, existing artifacts only | 0 GPU-h | variance gate first |

⚠ **S3 was blocked** by `A-020` §8.4 until an aligned `cds`-format comparator bank exists, and stays
blocked (`Q-001`). S4 ran independently and became `R-079`…`R-083`.

**`B-017` (new blocker, still open).** Two 38-domain banks (`…_38dom_ticket_knife`,
`…_38dom_tk_fcslots`) **declare `concept: knife` but were generated from bomb pools**; at a matched
`prompt_id` they are byte-identical apart from the codeword, so the demonstrations install **bomb**
semantics. ⇒ Any bomb-vs-knife contrast on those banks is a *codeword* contrast, not a concept one.
**Concept-backed hard negatives exist only at 6 domains.** This is why the whole phase runs on a
6-domain population.

---

<a name="4-preg"></a>
## 4. The preregistration, and its two void-and-respecify cycles

This is the most instructive part of the phase for an outside reader: the primary was specified,
amended four times before data, **voided by its own null control**, respecified, and then found not to
implement its own respecification.

### 4.1 `PR-031` and its three pre-data amendments

- **`PR-031`** (frozen before any forward pass): multinomial logistic probe on the codeword's L6–14
  hidden state, 5 classes, train on cell `B`, test on cell `C`, leave-one-domain-out over 6 domains,
  layer and regularisation selected on **cell `B` only**. Capability gate: held-out cell-`B` 4-way
  accuracy ≥ 0.60 — fail ⇒ `VOID — instrument incapable`, **never** evidence against specificity.
  Four outcomes declared (POSITIVE / NEGATIVE / CANNOT ANSWER / VOID).
- **`PR-031a`** — a defect found before data: training on cell `B`, where the surface token *is* the
  concept word, means the probe can succeed at training by learning **token identity**. A cell-`C`
  failure would then be ambiguous. ⇒ **`P2` added as co-primary**, where the surface token is the
  codeword in every row of every class so token identity carries **zero** information.
- **`PR-031c`** — the primary readout channel switched on **power** grounds: `comprehension_usage`
  gives **4 rows per domain per concept** (60 training rows in 4096 dimensions — "a design that
  cannot return an interpretable negative"), while `semantic_one_word` gives **40**. The phase notes
  it *"has already been bitten three times by reading an underpowered negative as a null."*
- **`PR-031d`** — ⛔ **the theoretical chance level is the WRONG null, and the analyzer's own self-test
  found it.** Run on **pure Gaussian noise with no class structure**, the preregistered primary
  statistic returned `6/6 negative, p = 0.0312 — SIGNIFICANT`. Not a coding bug: finite-sample
  held-out accuracy under a pipeline containing a selection step does not centre on 1/k. Measured
  false-positive rates over 12 synthetic nulls: sign-test-vs-1/3 **1/12 = 0.083**; group-permutation
  null **0/12 = 0.000**. ⇒ The primary inference becomes a **group-permutation null** (whole
  concept groups relabelled within domain, never individual rows), `n_perm = 200`, floor **1/201 =
  0.00498**. The miscalibrated statistic is **still computed and still reported**, labelled as such.

### 4.2 `A-020` — an independent audit that contradicted the preregistration, and was adjudicated

A 6-agent read-only audit returned *"a valid concept-specificity test CANNOT be built from the
existing banks."* The session **did not average this against its own view**; it re-measured all four
blockers from source. **Three confirmed, one confirmed-but-not-binding, one disputed and the
disagreement recorded rather than deferred:**

- **Blocker 1 CONFIRMED** — cell `A` is a different corpus per concept bank (`generate_pools` re-draws
  every `(domain, valence)`, so even *benign* demonstrations differ). ⇒ `P2` becomes sole primary;
  `P1`'s failure may not be read as a concept negative. *(Later narrowed by `C-060`: it holds
  **modally**, 250/348 ids, not universally.)*
- **Blocker 2 CONFIRMED as a gap, REFUTED as a shortcut** — prompt lengths differ (bomb 616, gun 613,
  knife 654, club 682 chars) but within-class sd is ≈160, so a **length-only classifier scores
  0.240 against chance 0.250**. Retained as a mandatory pre-registered control.
- **Blocker 3 CONFIRMED and worse** — `club`'s polysemy. ⇒ excluded from the primary composite;
  comparator becomes `mean(knife, gun)`.
- **Blocker 4 CONFIRMED and it bounds the claim** — the concept banks are preset `main`, 6 domains,
  no preamble; the headline causal population is `main_longpre_cds`, 38 domains, with a preamble.
  ⇒ **Binding scope statement: nothing from this stage transfers automatically to Part 1's causal
  results.** S3 blocked.
- **The audit's fifth claim — "all comparators are themselves harmful, so this cannot separate BOMB
  from generic harmfulness" — ⛔ DISAGREED.** Rebuttal: *a feature encoding generic harmfulness would
  be identical for bomb and knife*, so a classifier that separates them cannot be running on it;
  harmful hard negatives are exactly the right control for "is it just harm?". ⚠ What harmful
  comparators genuinely cannot do is separate BOMB from **generic remapping** — and there the audit is
  right, so **cell `F` was added as a fifth class**, upgrading the design rather than blocking it.

### 4.3 `C-048` — the first gate was VACUOUS, not failed

`PR-033` preregistered an installation gate at logit-lens **L16**. Run on all four `button` banks it
returned 3/6, 3/6, 1/6, 3/6 domains positive — read naively, *"bomb does not install"*, which would
VOID the whole phase. Applying the phase's standing rule (`option_mass` travels beside every
log-odds) to the logit lens:

| layer | option mass (C) | Δ boombness | domains + |
|---|---|---|---|
| **16 ← the gate** | **1.18e-05** | −0.277 | 3/6 |
| 31 | 3.69e-04 | **+3.441** | **6/6** |

At L16 the model holds ~1e-5 total probability across both options; `boombness` there is **a ratio of
two numbers the model does not hold**. ⇒ **VACUOUS, not failed.** The threshold now lives in code
(emit `VACUOUS` below option mass 1e-4).

⛔ **The gate was NOT moved to L31** even though L31 gives a clean 6/6 pass and is the canonical
logit-lens endpoint — because the verdict is **rule-dependent** ("shallowest layer with mass > 1e-4"
gives L20 → FAIL), both numbers have now been seen, and L31 is *both* the canonical choice **and** the
maximum-Δ layer, "exactly the coincidence that should provoke suspicion." The logit lens is demoted to
a diagnostic and the gate re-specified on the phase's own validated instrument (`PR-034`).

### 4.4 `R-078` — the installation gate: **PARTIAL**

Forced-choice `semantic_logodds`, 48 rows/bank, 6 domains, zero failures:

| bank | cell `A` | cell `C` | **Δ_inst** | domains + | option_mass A→C | gate |
|---|---|---|---|---|---|---|
| `button_bomb` | −7.272 | **+5.812** | **+13.084** | **6/6** | 0.146 → 0.836 | **PASS** |
| `button_club` | −1.941 | +4.494 | **+6.435** | 6/6 | 0.125 → 0.388 | **PASS** |
| `button_knife` | −2.022 | +2.068 | **+4.089** | 6/6 | 0.296 → 0.752 | **PASS** |
| `button_gun` | −3.692 | +0.406 | **+4.098** | **4/6** | 0.136 → 0.451 | **FAIL** |

**VERDICT PARTIAL** — `gun` **NOT INSTALLED**. Per the pre-declared consequence table, the primary is
reported **both with and without gun**, neither promoted. ⛔ State as *"gun's mapping installs
inconsistently across domains"*, never *"gun does not remap"* — its Δ (+4.098) is essentially
identical to knife's (+4.089), which passes 6/6; it fails on **consistency, not magnitude**.

**And this created a new confound, declared BEFORE the primary ran:** bomb installs roughly three
times harder than any hard negative. ⇒ A 3-way classifier could separate bomb by **how strongly the
codeword was remapped** rather than by **which concept**. Controls fixed in advance:
**(1) MANDATORY — knife-vs-club, 2-way, bomb excluded entirely.** Their strengths are close to each
other and bomb is not in the problem at all, so a bomb-anchored strength direction cannot drive it.
**If this control is at chance while the bomb-containing contrast succeeds, the positive is attributed
to remapping strength and may not be called Bombness.**

*(⚠ `C-070` later corrects the phrasing: bomb is **2.03×** club, not "~3× any hard negative".
Club is the nearest hard negative on strength, which is precisely why it is the control.)*

### 4.5 `C-049` — ⛔ THE NULL CONTROL FIRED. `PR-031` AS SPECIFIED IS **VOID**

`PR-031a` §7.2 justified `P2` on the claim: *"the surface token is `button` in every row of every
class, so token identity carries zero information."* **False.** The `strength` template block emits an
**explicit mapping statement** naming the concept word.

| population | rows | rows naming the concept |
|---|---|---|
| cell `C`, `n_examples ∈ {4,8}` (the **primary**) | 240 | **12 (5.0 %)** |
| cell `C`, `n_examples = 0` (the **null control**) | 36 | **12 (33.3 %)** |

Measured on real caches: the `n_examples = 0` control returns **0.5556 vs chance 0.3333, above chance
in 6/6 domains**, split as **clean rows 0.3333 (n=72) / leaking rows 1.0000 (n=36)**.
`PR-031a` §7.5 is unambiguous: *"a `P2` accuracy above chance at `n_examples = 0` **voids the entire
run, no exceptions**."*

⇒ **THE RUN IS VOID.** Recorded as VOID, **not repaired in place**.
⚠ **A number exists and is deliberately not treated as a result:** the review reported `P2` primary
≈ **0.72**. *That number is from a VOID run and may not be quoted*, recorded only so its later
reappearance cannot be mistaken for independent confirmation.

**Why the permutation null did not protect against this:** under group permutation the lexical cue is
remapped to a different label in each training domain, so the **null stays at chance while the
observed statistic is lifted** — the signature of a false positive, not something a null absorbs.
⇒ *A valid permutation null does not protect against a feature genuinely present and genuinely
predictive.* Only the preregistered `n_examples = 0` control caught it.

**Two guards that should have caught it and did not:** the bank's own `occurrence_analysis_safe` is
`True` on all 240 rows (it inspects the *question*, not the body); and the verifier's leakage check
reads **`final_query_text` only, never `full_prompt`** — so `A-021`'s "0/288" figures describe the
question text alone, and its leakage PASS was **scoped too narrowly**.

**Three further critical defects, all confirmed:** `VOIDS_RUN` was a **dead flag** — computed, written
to JSON, and never read, with an **undeclared +0.15 slack** appearing nowhere in the preregistration;
the mutation harness printed `MUTATION HARNESS OK` on a corruption it **never applied**; and a missing
bank silently becomes a smaller problem scored against the larger chance level.

### 4.6 `PR-035` — the respecification

Replaces `PR-031`/`031a`/`031c`/`031d`. The repair is a **new preregistration**, not a quiet re-run.

- **§23.1 exclusion, defined from prompt text alone:** exclude every row whose `full_prompt` contains
  its bank's concept word, word-boundary, case-insensitive. **Mechanical and pre-outcome** — reads the
  prompt, never a hidden state, never an accuracy. Realised: **12 of 240** primary rows and **12 of 36**
  null rows per bank, **all** in `bank_block = strength`, **identical counts in all three primary
  banks** ⇒ balanced across classes, cannot induce a class asymmetry.
- **§23.2 the null control is now BLOCKING, in code:** if its permutation p ≤ 0.05 the analyzer
  **exits non-zero and prints no primary**. A dead JSON flag is what let a fired null coexist with a
  headline; the fix is a hard exit. The undeclared slack is removed.
- **§23.5 verdict rule, five clauses**, all required for POSITIVE: null passes · class set complete ·
  3-way permutation p ≤ 0.05 above chance · **the knife-vs-club control also clears** · length-only
  control does not match.
- **§23.7 standing on the record:** *"This is the second void-and-respecify in this phase. If
  `PR-035`'s null control fires again, the honest conclusion is that this population cannot support
  the test and the answer is `CANNOT ANSWER` — not a third respecification."*

### 4.7 `C-050` and `C-053` — the analyzer did not implement its own preregistration

`C-050`, found **by reading source before running it**: the §23.1 exclusion — *the entire repair
`C-049` demanded* — **was not implemented at all** (`excluded` was returned but never assigned;
`grep` confirms no match anywhere in the file). It would have died with `NameError` on first call.
⚠ **The one thing that went right:** *crash, not silent skip.* Had `excluded` been initialised to
`{}`, the analyzer would have completed and produced a headline on the exact population `C-049`
voided. Three more defects: `P1` trained on cell `C`, not `B` (so it was `P2` wearing a fourth class
label no row carried, scored against the wrong chance level — `C-049`'s own defect reappearing inside
the analyzer written to fix it); the cell-`F` contrast had **no inference attached**; and §23.5's
clause 5 was computed and never read.

Then **`C-053` / `A-024` — a 33-agent adversarial audit** *"found more wrong with the `C-050` repair
than `C-050` found wrong with `PR-035`."* Seven further defects, of which three matter most:

- ⛔ **The blocking null was not computing the declared statistic** — its `(layer, C)` picks were
  grid-searched on **the null rows' own true labels**. *The single number that decides whether the run
  is VOID was not the preregistered statistic.*
- ⛔ **CRITICAL — hidden states joined on `prompt_id`, which collides 8-way.** The code built a
  compound key, its own docstring said *"prompt_id ALONE IS NOT A KEY"*, and then joined with
  `reps[pid]`; the compound key was **never read anywhere in the file**. A mis-pointed run directory
  would have joined another bank's hidden states, reported **zero missing rows**, raised **no VOID**,
  and produced a plausible headline. Fixed by requiring each run's `metadata.json` to match the bank
  joined.
- ⛔ **The cell-`F` comparator as built would have manufactured a positive** — 228 bomb rows against
  24, so a constant "bomb" predictor scores **0.906** against a printed chance of 0.5, and the
  group-permutation null does not absorb it. Fixed with balanced accuracy. **Unfixable structural
  confound declared:** cells `C` and `F` sit in **disjoint template blocks**; interpretation fixed
  asymmetrically before the numbers — a NEGATIVE is informative, a **POSITIVE is not attributable to
  concept**.
- **§28.0, a process failure recorded first:** the analyzer was **edited while being audited**; the
  audit observed the file change five times in ~5 minutes and caught it in two non-executable states.
  ⇒ **Rule adopted: the analyzer is committed and its sha recorded *before* the audit that signs it
  off and before it runs on real caches.**

---

<a name="5-headline"></a>
## 5. The headline — `R-086` / `R-089`: a concept-specific state, **POSITIVE**

### 5.1 The claim, stated exactly

> On **held-out domains**, a linear probe on the codeword's **L6–14** hidden state identifies **which
> of bomb / knife / gun** the demonstrations installed — **0.7485** against a **0.3333** chance,
> **6/6** leave-one-domain-out folds, permutation **p = 0.004975** from a test measured to reject
> noise at **0.030**.

| element | value |
|---|---|
| primary accuracy | **0.7485380116959064** |
| per-domain | city_bridge .77193 · farm_storage .842105 · game_manual .54386 · instructional .929825 · lab_safety .77193 · news_report .631579 |
| bomb-absent control (knife vs club) | **0.8596**, p = 0.0498, test FPR 0.020, power 0.760 |
| gun-excluded 2-way {bomb, knife} | **0.9079**, 6/6, p = 0.0498 |
| length-only control | 0.336 vs null q95 0.488 (does not match) |
| blocking null (`n_examples = 0`) | 0.3333 at chance, 0/6 domains, p = 1.0 (`R-084`) |

⚠ **`p = 0.004975` IS the attainable floor** at `n_perm = 200` (= 1/201) — the smallest value this
test can emit, not a measured tail.

**Why the bomb-absent control matters:** a 3-way probe could in principle separate on *installation
strength* rather than *identity*. Knife-vs-club have similar strengths (**+4.089**, **+6.435**) and
the contrast **contains no bomb term at all**, so a bomb-anchored strength axis cannot drive it — and
it separates. **That is what licenses "identity, not strength alone."**

### 5.2 `R-084` — the blocking null passes, and demonstrably so

The first line of output, before any primary: `[null n_examples=0] mean_acc=0.3333 chance=0.3333
above=0/6 perm_p=1.0`. `C-049` measured the same control on the *unrepaired* population at **0.5556,
6/6 domains**. Today's retained population reproduces `C-049`'s **clean-row split to the digit** (72
rows, 0.3333, with 12 excluded per bank) ⇒ **the exclusion removed exactly the leaking rows and
nothing else.** The repair is targeted.

### 5.3 The verdict was overturned on a sign error and restored — the phase's most serious mistake

This arc is worth reading in full because the log itself names it *"the most serious error of this
phase."*

1. **The analyzer printed `POSITIVE`.** The author **overrode** it (`C-058`): three different 2-class
   contrasts returned **p = 0.04975124378109453, identical to 16 digits**, explained by a **symmetry**
   — if the same label permutation is drawn in every domain, the classifier learns the relabelled
   mapping and scores exactly the observed accuracy. At 2 classes that has probability 2/64 ⇒ **6.25
   expected of 200 draws**. `C-058` concluded the p-values were *"fully explained by the symmetry"* and
   therefore invalid, so §23.5's clause 4 was not satisfied by a valid test.
2. ⛔ **`C-061` — the direction of the bias was backwards.** `p = (1 + #{null ≥ obs}) / (1 + n_perm)`,
   and a global relabel gives `null = obs`, so it **counts in the numerator** ⇒ the symmetry makes
   **p LARGER, not smaller**. It is **conservative**. Removing those draws removes *high* null values,
   so the observed looks more extreme and p falls. Found because the author **calibrated their own
   fix** and it failed on pure noise. The downgrade was **SUSPENDED, not reinstated and not
   confirmed** — *"having now been wrong once in each direction."*
3. ✅ **`C-062` / `R-089` / `R-090` — the head-to-head measurement.** Job 854780, four procedures ×
   2 class-counts × {pure noise, planted signal}, same data, same seeds, 100 reps:

   | | | **FPR** (noise, must be ≤ .05) | **power** (planted) |
   |---|---|---|---|
   | **3-class** | **cell `B` + ORIGINAL** ⇐ *the primary, as run* | ✅ **0.030** | 1.000 |
   | | cell `B` + EXCLUDING | 0.030 | 1.000 |
   | | test set + ORIGINAL | ⛔ 0.100 | 1.000 |
   | | test set + EXCLUDING | ⛔ 0.100 | 1.000 |
   | **2-class** | **cell `B` + ORIGINAL** ⇐ *clause 4, as run* | ✅ **0.020** | 0.760 |
   | | cell `B` + EXCLUDING | 0.050 | 0.940 |
   | | test set + ORIGINAL | ⛔ 0.090 | 0.840 |
   | | test set + EXCLUDING | ⛔ 0.140 | 0.930 |

   ⇒ Both tests **as run** are validly calibrated and **conservative**. `C-058` is **RETRACTED**;
   §23.5 clause 4 **is** satisfied and understated. **`POSITIVE — concept-specific` STANDS.**

4. **`R-090`'s design lesson, for the paper's methods section:**
   > *In a leave-one-group-out design with a group-permutation null, **where the hyper-parameters are
   > selected matters far more than which permutations the null contains.** Selecting on the test
   > population and then freezing those picks across the null inflates the false-positive rate 3–5×.
   > Selecting on an independent population makes the same test conservative.*

   It generalises beyond this repo: **any probing paper that grid-searches a layer on its evaluation
   set and then permutation-tests it has this defect, and the inflation is large.** At 3 classes the
   two nulls are indistinguishable on all four measurements (the symmetry fires at 1/7776) ⇒ *`C-058`
   argued about an effect that does not exist at the primary's class count.* The symmetry costs
   **power, not validity** (0.760 vs 0.940).

⚠ **How close this came to being lost:** a correct, independently verified headline was overturned by
the log's own author on a sign error, **committed and reported**, and recovered only because a
*measured* false-positive rate is mandatory before a null is trusted — and **the first measurement was
itself wrong** (it tested test-set selection, which would have "confirmed" the erroneous override at
0.090). **Two successive measurements were needed to undo one piece of bad reasoning.**

### 5.4 Five independent reproductions of the primary

The producer run is the source, not one of them.

1. **Job 854618** — independent recomputation from banks and caches, **all 16 digits**.
2. **`A-029`** — full verification pass once `V2` was made a real check (`A-028` retracted an earlier
   vacuous `V2 PASS`). Its `V4` re-ran the permutation on a **different seed (90613)** and matched
   inside a stated Monte-Carlo band (0.0050 vs 0.004975) — ⛔ *not* to 16 digits, a different event.
3. **`A-031` §57.1** — thread-invariance at both `OMP=4` and `OMP=1`, identical to 16 digits.
   *(⛔ **DECISION 1:** any re-run intended to reproduce a published number uses `OMP_NUM_THREADS=4`.
   The analyzer is **not** bit-reproducible across thread counts on one instrument — the cell-`F`
   contrast moves 0.8882 → 0.8904.)*
4. **`R-094`** (the `PR-043` re-run at HEAD with `PR-039`'s five repairs live) — a **fifth** exact hit.
5. **`A-032`/`A-033`** — re-derived by agents' own code importing nothing from `scripts/`.

### 5.5 Every caveat that travels with `R-086`

- ⛔ **Decodability, not causality.** `A-025` `F-3` (arXiv 2605.04061) reports **0 % task transfer
  across all 28 layers of Llama-3.2-3B *despite 100 % probing accuracy***. The causal gate is `R5`
  (§9), and the signal **survives** the knockout.
- ⛔ **Not "bomb vs generic remapping"** — the cell-`F` comparator has an invalid p **and** is
  block-confounded; `A-031` DECISION 3 makes it **permanently descriptive on this bank** (cell `F` is
  the only benign-remap cell that exists: 24 rows, one block, so no disjoint selection population can
  ever exist for it). **No p-value, ever, from these banks.**
- ⛔ **`P1` is UNINFORMATIVE**, not a concept negative — it scored **0.0000** (not chance,
  *systematically* wrong) from class imbalance, 504 `literal` rows vs 144. And once re-run with a
  balanced fit it would publish a **floor** p regardless of signal ⇒ **`P1` must be reported with no
  p-value at all.**
- ⛔ **Lexical transfer is bounded by `R-092`/`C-066`** (§8).
- ⚠ The 2-class control is **underpowered by construction** (power 0.760 where a symmetry-free null
  reaches 0.940) — clearing 0.0498 was *harder* than the number looks. ⚠ And it clears at **exactly
  10/201**, one null replicate from 11/201 = 0.0547 and a `NOT ATTRIBUTABLE` verdict. **The entire
  "concept-specific, not remapping strength" clause rests on that one-replicate margin.**
- ⛔ **The `(layer, C)` "selection on cell `B`" SELECTS NOTHING** (`C-070`, §15.4). Cell-`B`
  leave-one-domain-out accuracy is **1.000000 at all 36 grid points**, so `select()`'s strict-`>` test
  returns the **first** grid element and the pick `(6, 0.01)` is a **tie-break artifact of grid
  order**. ⚠ **What this does NOT do:** it changes no reported number, and a *constant* pick is if
  anything a **stronger** guarantee of test-set independence than a fitted one. ⚠ **What it does do:**
  the sentence *"selects the layer that maximises cell-`B` accuracy"* is **false as written**.
  ✅ **And the substantive claim survives the whole grid:** recomputed at every one of the 36 points,
  the primary ranges **0.6594–0.7690** and is **6/6 above chance at 36/36**. *The 16-digit headline
  rests on a `>` vs `>=` comparison; the finding does not.* ⛔ This 36-point sweep is **post-hoc**,
  run in response to a defect — descriptive reassurance, not a preregistered robustness check.
- ⛔ **The capability gate is VACUOUS** — `train-fold accuracy = 1.0` everywhere; at 4096 dimensions
  the probe separates its own training fold perfectly, so `PR-031` §6.6's gate is trivially passed and
  carries no information.
- ⛔ **Two pre-declared instruments are ABSENT and are reported as absent, not quietly dropped:**
  §9.3's 4-way-with-`club` secondary (deleted by the `C-050` edit) and §21.2(2)'s
  **installation-strength covariate** — which was control (2) of three fixed in advance against the
  very strength confound the club control is relied on to answer.
- ⚠ **One model, one codeword, 6 domains, one layer band.**

---

<a name="6-axes"></a>
## 6. `R-091` — the remapping axis and the concept axis are **different directions**

`scripts/dcs_diffmeans_directions.py`, **44 s CPU, zero GPU**. A *different instrument* from the
classifier: directions estimated on train domains only, leave-one-domain-out over n = 6, paired on
`family_id`, statistic = the **mean over the inherited L6–14 band** ⇒ **no layer selection and no
hyper-parameter anywhere**, so no selection defect is possible. Four numbers independently re-derived
to 10 significant figures by a verifier with its own loader.

| direction | *is it remapped?* (`C_bomb` vs `A_bomb`) | *which concept?* (`C_bomb` vs pooled `C_{knife,gun,club}`) |
|---|---|---|
| **`v_bomb`** (raw diff-in-means) | **AUROC 0.9987**, d 5.755, 6/6 | **0.5743** — vs `gun` **0.4978**, i.e. chance |
| **`v_bomb_specific`** (= `v_bomb` − mean of the three) | 0.6070, 3/6 | **AUROC 0.8964**, d 1.786, **6/6** |

⇒ **The two axes are nearly complementary.** The raw difference-in-means is a **remapping** axis and
is almost blind to *which* concept; the residualized direction is a **concept-identity** axis and
barely registers remapping. Primary: **6/6, p = 0.03125 = the attainable floor**; per-layer profile
**flat** (0.880–0.912) ⇒ not a single-layer artifact.

**Controls:** the bomb-absent `v_knife − v_club` on held-out `C_knife` vs `C_club` gives **AUROC
0.9815**, d 4.796, 6/6 (basket 0.9657) — *the strongest single row in the result, and immune to a
bomb-anchored strength axis*. The blocking null passes exactly (‖`v_bomb`‖ = 0.000, AUROC 0.5000,
0/6; `A` vs `C` byte-identical 12/12). Synthetic calibration over 50 replicates carrying a shared
remap but **no concept component** ⇒ FPR **0.040**.

### 6.1 `C-065` — this reconciles the inherited `R-002` negative

`R-002` (Part 1) found the `toward_B_frac` geometry proxy **not bomb-specific**, with knife/gun/club
matching or exceeding bomb, and the project carried it as *"a negative under one instrument."*
`R-091` says **why**: that proxy measured movement along the **remapping** axis, and `v_bomb` versus
the hard negatives is **0.5743, with `gun` at exactly chance**.

⇒ ⛔ **`R-002` was not a failure to find concept specificity; it was a correct measurement of an axis
that does not carry it.** ⛔ `R-002` is **not retracted** — its measurement stands. What changes is its
**interpretation**.

**Caveats:** ⛔ the **strength confound is not fully closed by the primary** — `v_bomb_specific`
subtracts a mean over three concepts of very unequal installation strength, and a strength component
is **present inside the primary**; only the bomb-absent control is immune, and that control is
descriptive. ⚠ Cell-`A` overlap on the exact families used is 6–18/168, so on ~90 % a benign-corpus
difference survives as a nuisance term. ⛔ **n = 6** — only 6/6 or 0/6 can clear α. ⛔ Still a
**decodability** result.

---

<a name="7-kladder"></a>
## 7. The K ladder — `R-079`/`R-080`/`R-081`/`R-082`, and `PR-037`/`R-083`

Part 1's `R-021`/`R-022` bracketed the transition between K = 2 (null) and K = 8 (large); rungs 3–7
were never run. `PR-032` ran them, with every setting inherited byte-comparably and each rung against
its own dose-matched control.

### 7.1 `R-079` — what `K` actually cuts, recovered before any rung was read

⚠ **This reframes the whole ladder, and the prediction was committed to git before the analyzer
ran.** `query_span_positions` anchors on `final_query_text` and runs to the true end of the
**whole chat-templated prompt, generation header included**. Over **all 380 prompts, 380/380 with
zero variation**, the token newly entering the cut at each rung is:

| K | token newly cut | what it is |
|---|---|---|
| 1 | `'\n\n'` | chat scaffold |
| 2 | `<\|end_header_id\|>` | chat scaffold |
| 3 | `assistant` | scaffold (generation header) |
| 4 | `<\|start_header_id\|>` | chat scaffold |
| 5 | `<\|eot_id\|>` | scaffold (end of user turn) |
| **6** | **`?`** | **first USER-TEXT token** |
| **7** | **`' bomb'`** | **first CONTENT word** |
| 8 | `' a'` | question text |

⇒ **Rungs 1–5 cut only chat-template scaffold.** `R-021`/`R-022`'s "K=1 and K=2 have no effect" was
read as *"one or two query rows do not need demonstration access"*; the licensed statement is only
*the last one or two tokens of the chat template's generation header do not need demonstration
attention*.

`PR-036` then fixed three predictions in a commit **before any K = 4…7 row was read**, with a declared
falsifier. **All three confirmed.**

### 7.2 `R-080`/`R-081` — the ladder resolves: `K* = 7`, `shape = STEP`

| K | token newly cut | Δ (demo − control) | % of Δ₈ | domains − | p | Holm | option_mass |
|---|---|---|---|---|---|---|---|
| 1 | `'\n\n'` | −0.0132 | 0.2 % | 23/38 | 2.56e-01 | — | 0.879 |
| 2 | `<\|end_header_id\|>` | −0.0115 | 0.2 % | 23/38 | 2.56e-01 | — | 0.878 |
| 3 | `assistant` | −0.0697 | 1.1 % | **35/38** | 6.68e-08 | ~0 | 0.879 |
| 4 | `<\|start_header_id\|>` | −0.0194 | 0.3 % | 21/38 | 6.27e-01 | 1.000 | 0.880 |
| 5 | `<\|eot_id\|>` | **+0.0225** | 0.3 % | 18/38 | 8.71e-01 | 1.000 | 0.878 |
| **6** | **`?`** | **−0.5015** | **7.6 %** | 34/38 | 6.04e-07 | ~0 | 0.853 |
| **7** | **`' bomb'`** | **−5.9849** | **90.5 %** | **38/38** | 7.28e-12 | ~0 | **0.409** |
| 8 | `' a'` | −6.6161 | 100 % | 38/38 | 7.28e-12 | — | 0.368 |
| 16 | — | −7.8884 | 119.2 % | 37/38 | 2.84e-10 | — | 0.372 |

**`K* = 7`** (smallest K with Holm p ≤ 0.05 **and** |Δ| ≥ 0.5·|Δ₈| = 3.308). **`shape = STEP`**, fired
by the declared criterion at K=6 → K=7 (0.076 → 0.905). Largest single-rung rise **+82.9 percentage
points**.

✅ **The §11.7 kill criterion passes exactly:** the K=8 re-run three days later reproduces
**−6.616111537245543** to the digit (absolute difference **0.000000**).

> **Claimable, with its bound attached:** demonstration→query attention is **not required by the chat
> template's own scaffold tokens at all**; the requirement appears exactly where the cut reaches the
> question's content, and it is a **step, not a ramp** — 90 % of the full effect arrives with a single
> additional token.

**Caveats:**
- ⛔ **The decisive rung is structurally confounded, and this was declared before the numbers.** The
  token entering at K=7 is `' bomb'` **only because** the `semantic_forced_choice` question names both
  options. So this may **not** be written as *"blocking the codeword's query row breaks the mapping"*.
  An equally consistent reading is *"the question's concept-option token is where demonstration
  information is integrated for this readout"* — a fact about the **instrument** as much as the
  mechanism.
- ⛔ **Not "the mechanism is one token"** — K=7 cuts K=1…6's tokens too, and row count and cut-cell
  count still rise together by construction.
- ⛔ `R-021`/`R-022`'s bracketing is **superseded**, and any sentence of the form *"one or two query
  rows do not need demonstration access"* must not be written.
- ⚠ **The profile is not monotone** — K=5 is +0.0225, the wrong sign, 18/38 domains.
- ⚠ **K=3 is significant at a 1.1 % magnitude** (35/38 domains, p = 6.7e-08) while K=4 and K=5 sit at
  chance. Significance at n = 38 does **not** imply mechanistic meaning; this is the phase's cleanest
  demonstration of that, and it has **no explanation**.
- ⚠ **`option_mass` collapses across the transition** (0.878 → 0.853 → **0.409** → 0.368), so the
  effect-carrying rungs are measured where the forced-choice options hold under half the probability
  mass — and the collapse **tracks Δ**, so it is not an independent check.

### 7.3 `R-082` — the effect is complete before the codeword's own row is cut

Not a new experiment; a structural reading of the committed token table against the committed profile.
Over the same 380 prompts, **380/380 with zero variation, neither occurrence of the codeword
` button` enters the cut until `K = 11`**, while the effect has reached 100 % of Δ₈ by K = 8.
⇒ An independent confirmation of `KO-1`'s null by a different route.

### 7.4 `PR-037` / `R-083` — **CANNOT ANSWER, by 1.9 percentage points**

The follow-up designed to separate the two readings, on `semantic_one_word` (whose question **never
names the concept**): there the codeword enters at **K = 10** and **no concept word ever enters**, so
K=9 is a matched control and the K=9→K=10 increment is the single primary.

⚠ **`B-018` — the dose-matched control is INFEASIBLE on this bank**, discovered when all six `ctrl`
arms refused pre-generation: *"164 of 168 rows cannot carry this knockout… do NOT rescope to the
feasible rows, because demo length IS the dose variable."* Amended pre-data: an unintervened
**baseline** replaces the control, which cancels exactly in the between-rung increment (verified:
`keys_masked` is **identical at 2754 in all six arms**; K=9 and K=10 differ by exactly 36 edited rows
and nothing else). ⛔ **What is lost:** this cannot ask whether the effect is specific to demonstration
keys on this population — that is answered for the 38-domain ladder (`R-080`) and inherited here.

| arm | rows cut | `semantic_logodds` | Δ vs baseline | % of Δ_ref | option_mass |
|---|---|---|---|---|---|
| baseline | 0 | **+3.3696** | — | — | 0.294 |
| K=5 (all scaffold) | 180 | +2.5960 | −0.774 | **12.1 %** | 0.280 |
| K=6 (`?`) | 216 | +2.5997 | −0.770 | 12.1 % | 0.282 |
| `ko1` (codeword row ALONE) | 36 | +1.2841 | −2.086 | **32.7 %** | 0.478 |
| K=9 (`' actually'`) | 324 | +0.3845 | −2.985 | 46.8 % | **0.105** |
| **K=10 (`' button'`)** | 360 | **−2.6859** | −6.056 | **94.8 %** | 0.243 |
| `ref` (whole query span) | 1008 | −3.0151 | −6.385 | 100 % | 0.227 |

**Primary:** `inc = Δ_K10 − Δ_K9` = **−3.0704**, **6/6 domains negative**, sign test
**p = 0.03125 = exactly the attainable floor**. Magnitude gain **48.089 %** of |Δ_ref| against the
preregistered **50 %** `CODEWORD-ROW` bar.

⇒ ⛔ **`CANNOT ANSWER`, missed by 1.9 percentage points. The bar was not moved.** *"48.1 % is
essentially 50 %"* is the forbidden goalpost move. Honest statement: **the data point strongly toward
the codeword row and do not clear the bar set to conclude it.**

**`C-054` — and it went against the session's own prediction.** `R-082` had read `H-codeword` as
disfavoured; on **this** template it is the best-supported reading — the `ko1` arm (codeword row
alone, 36 rows) moves the readout **32.7 %** of the way to the full effect, **which is not a null**,
while Part 1's `R-005`/`R-006` found `KO-1` a null (+0.278, p = 0.073). ⇒ **`R-082`'s claim and
`KO-1`'s null are BOUNDED TO THEIR TEMPLATE.** Correct statement: *on `semantic_forced_choice` the
effect saturates before the codeword row is cut, so the codeword row adds nothing there; on
`semantic_one_word` the codeword row alone carries a third of the effect.* These are **not
contradictory measurements** — same ladder logic on templates whose content words sit in different
places — but *"the codeword row is not necessary"* is false as a general claim.

⚠ **Three limitations bound everything above:** no dose-matched control on this population; **the
floor is not zero** — K=5, masking the same 2754 keys from all-scaffold rows, already moves the
readout **12.1 %**, and rescaling against that floor **would lift the primary above 50 %**, which is
*"not preregistered, not applied, and does not change the verdict"* — recorded only so a future reader
cannot present it as a discovery; and `option_mass` at K=9 is **0.105**, the standing measurement-regime
limit at its worst in this phase, cutting **against** over-reading the increment.

⚠ **A post-hoc account, labelled and NOT adopted:** both templates saturate exactly when the cut
reaches the question's semantically loaded content word. Tidy, but post-hoc pattern-matching across
two experiments; would need its own design and **must not be written as a finding**.

---

<a name="8-r3"></a>
## 8. Gate `R3` — `R-092` **FAILS**, and `C-066` says why

⛔ **These two must never be reported one without the other.** Reporting `R-092` alone publishes a
false sentence; reporting `C-066` alone rescues a gate that failed.

**Why a new preregistration was needed:** `C-064` found the frozen analyzer's
`P2_basket_lexical_transfer` **trains and tests on basket** — only the layer *selection* comes from
button. ⇒ **There is no transfer in it**; `R3` is recorded as **NOT IMPLEMENTED** in the frozen file,
and the published **0.6974** may never be cited as transfer. Editing a frozen published analyzer is a
preregistration question, not an edit, so `R3` was implemented in a separate script (`PR-041`).

**`R-092`** — train on **button** cell `C`, test on **basket** cell `C`, selection on **button** cell
`B`, leave-one-domain-out across codewords. Populations verified 228/class both sides.

| domain | held-out basket accuracy |
|---|---|
| city_bridge | 0.6754 |
| instructional | 0.3509 |
| news_report | 0.3509 |
| farm_storage | **0.3333** ⇐ exactly chance |
| game_manual | **0.3333** ⇐ exactly chance |
| lab_safety | **0.3333** ⇐ exactly chance |
| **mean** | **0.3962** (chance 0.3333; `R3-FAIL` bar 0.4164) |

⇒ **`R3-FAIL`**, on the **magnitude** criterion declared in advance.
⚠ **The significance half is uninformative by construction:** three domains sit at *exactly* chance,
their signed deviations are zero, the sign test drops them, n falls 6 → 3, and the attainable floor
rises **0.03125 → 0.25**. *"The sign test fails" here is arithmetic, not evidence.*

**`C-066`** — scoring the **same** button-trained classifier by macro one-vs-rest **AUROC**, which is
pure ranking and invariant to any per-class offset:

| domain | argmax acc | macro OvR AUROC |
|---|---|---|
| city_bridge | 0.6754 | 0.8691 |
| **farm_storage** | **0.3333** | **0.9317** |
| game_manual | 0.3333 | 0.5185 |
| instructional | 0.3509 | 0.8668 |
| **lab_safety** | **0.3333** | **0.8386** |
| news_report | 0.3509 | 0.7462 |
| **mean** | **0.3962** | **0.7951** (chance 0.500) |

⛔ **`R-092`'s sentence — *"the concept signal is codeword-specific, encoded in different directions"*
— is WRONG and RETRACTED.** The directions are **shared**. What fails to transfer is the **decision
offset**: the button-fitted boundary sits in the wrong place for basket states, so `argmax` collapses
even though the ordering is preserved. ✅ This **reconciles `R-091` and `R-092` completely** — one
measured a ranking (0.9204), the other an argmax with an absolute boundary (0.3962); there was never a
contradiction.

> **The corrected scientific statement:** *the concept direction is shared across codewords and
> transfers by ranking (AUROC 0.795 macro OvR; 0.9204 by the independent diff-in-means instrument);
> the absolute decision boundary is codeword-specific and does not transfer.*

✅⛔ **Gate `R3` still FAILS as preregistered.** §60.3 declared held-out **accuracy**. ⛔ **We are not
switching to AUROC to rescue the gate** — that is metric-shopping, *and it is the second time in one
day a better-behaved metric became available after a failure*. ⚠ `C-066` is a **descriptive
diagnostic with no p-value** and changes no verdict.

⚠ **Method note worth keeping:** a leave-one-group-out classifier's **accuracy conflates** whether the
representation carries the label with whether the boundary is portable. Any transfer claim should
report **both** an offset-free ranking statistic **and** the accuracy, and say which one the gate is
defined on.

⚠ **The reverse direction (basket→button) was never run.** Do not report a second direction.

---

<a name="9-r5"></a>
## 9. Gate `R5` — `R-093`, the readout/representation dissociation

### 9.1 Getting there: `B-021` and the bridge

Gate `R5` was **blocked on a missing capability**: `extract_boombness.py` persists multi-layer hidden
states but has **no `--intervene`**; `score_behavior.py` applies the knockout but persists only
`hnorm|L*` **norms** — *and a norm cannot train a probe*. ⇒ **No existing path writes a knocked-out
rep cache.** The pattern exists exactly once in the repo (an arm-active donor capture). `Q-005` was
put to Omer and answered: **build it**. `scripts/dcs_extract_under_ko.py` (1238 lines) reimplements
nothing — capture site from `extract_boombness`, blocked keys from `score_behavior`, the hook from
`pair_common` — and writes the same cache format the **frozen** `PR-035` analyzer consumes unchanged.

**`PR-040a` — the bridge passed its kill criterion, and the author nearly voided it with an invalid
metric.** The first check used element-wise relative error and got q95 = 0.215, which by the letter of
the kill criterion voids the bridge. **The metric was invalid** — on dense 4096-dim vectors,
element-wise relative error is dominated by components near zero. Under proper metrics:

| bridge arm | min cosine vs baseline | mean rel-L2 |
|---|---|---|
| knockout **DISABLED**, eager | **0.999849** | 0.0140 |
| knockout **ENABLED** | **0.7639** | **0.3764** |

⇒ disabled reproduces baseline to cosine 0.9999; the knockout demonstrably fires — a **27×**
separation. Switching metrics after a failure is **flagged, not buried**; defensible because the
replacement was not chosen for its answer and an independent layer-offset sweep confirmed the
convention. ⛔ **And the residual 1.4 % is a confound**, so the design was amended pre-data: the
primary compares `ko_on` against `ko_off` **bridge-to-bridge**, which cancels the code-path offset
exactly.

### 9.2 `R-093` — **`R5-FAIL`**

Six arms, zero aborts, 228/class both sides, bank binding verified per class, every fold picking
`(L=6, C=0.01)`.

**Bridge validation:** `ko_off` **0.7529** vs `R-086`'s published **0.7485**, difference **0.0044**
against a VOID bar of **0.10** ✅.

| domain | `ko_off` | `ko_on` | drop |
|---|---|---|---|
| city_bridge | 0.7807 | 0.7632 | +0.018 |
| farm_storage | 0.8421 | 0.8596 | **−0.018** |
| game_manual | 0.5526 | 0.5263 | +0.026 |
| instructional | 0.9298 | 0.8509 | +0.079 |
| lab_safety | 0.7719 | 0.7018 | +0.070 |
| news_report | 0.6404 | 0.5263 | +0.114 |
| **mean** | **0.7529** | **0.7047** | **+0.0482** |

Sign test **5/6, p = 0.21875**, floor **0.03125**. The drop is **11.5 %** of the 0.4196 available,
below the preregistered 20 % bar. ⇒ ⛔ **`R5-FAIL`: the concept signal SURVIVES.**

⚠ **This is an *informative* negative, not an uninformative one:** the floor was 0.03125 and the
design **could** have cleared α — unlike `R-092`, where ties raised the floor to 0.25. The test had
the power to detect a drop and found 11.5 %.

**Secondary (no p):** train-on-KO / test-on-KO = **0.7120**. That branch existed to separate *gone*
from *re-based* **given a drop**; with no real drop it is confirmatory — 0.7120 ≈ 0.7047 ≈ 0.7529 ⇒
the representation is **intact and in the same basis**. ⛔ The script's printed label *"PRESENT BUT
RE-BASED"* **overstates**; the correct reading is **PRESENT AND UNMOVED**.

### 9.3 The dissociation

| measurement | baseline | whole-query knockout | |
|---|---|---|---|
| **readout** — `semantic_logodds` (`R-083`'s `ref` arm) | **+3.3696** | **−3.0151** | ⛔ **sign flip**, Δ −6.38 |
| **representation** — concept probe | **0.7529** | **0.7047** | ✅ **94 % retained** |

⇒ The same intervention, on the same bank, in the same layer band, **destroys the model's ability to
report the mapping while leaving which concept was installed decodable from the codeword's hidden
state.**

**The phase's one-line statement:**
> Doublespeak installs a concept-specific state at the codeword that a linear probe can read on
> held-out domains; the demonstration→query attention path is **necessary for the model to report**
> that mapping, and **not necessary for the state to remain decodable**.

**Caveats — all of them travel:**
- ⛔ **Not "the knockout does nothing."** It abolishes the forced-choice preference; Part 1's
  `R-010`/`R-011` stand entirely.
- ⛔ **Not a claim about behaviour.** `R-075` remains an underpowered negative; gate `R8` is
  **CANNOT ANSWER** (§10.3) — *not unrun, and not a null.*
- ⛔ **No dose-matched control is feasible on this bank** (`B-018`) ⇒ a localisation **conditional on
  `R-080`**, not independent evidence about demonstration keys.
- ⚠ The two rows are **different instruments at different sites** — a generated forced-choice answer at
  the answer position vs a probe on `codeword_last` hidden states. The dissociation is between **what
  the model can report** and **what is linearly decodable**, ⛔ not two measurements of one quantity.
  **No population matching closes that gap**; only a readout taken at the same site could, and none
  exists.
- ⚠ It arrives one level earlier than the brief expected: it was posed as *representation vs
  behaviour*; this is *representation vs **readout***.
- ⚠ `game_manual` is weak throughout (0.5526 baseline); `farm_storage` moves the **wrong way**. n = 6.

### 9.4 `R-093a` — it survives a matched-population check

Restricting the probe to `PR-037`'s exact three blocks (168 rows/class): `ko_off` **0.7361** →
`ko_on` **0.6865**, drop **+0.0496** = **12.3 %** of available. ⚠ Only **4/6** domains, with
`city_bridge` moving −0.119 the wrong way; on those rows the probe retains **~88 %**, not the 94 %
the headline leads with. ⇒ The two arms are the same intervention on the same rows; the dissociation
is not a population artefact. *(The two masks were also verified to be the same kind of intervention:
both prefill-only demonstration-block knockouts over the same band, zero decode edits on both sides.)*

### 9.5 ⛔ `C-068` — `R-093`'s **description** must be corrected, though its verdict stands

Gate `R6` re-ran the same probe against a knockout scoped to **only the codeword's own query row**
(1.7 % of the whole-query dose). It reproduced `R-093` **to sixteen digits** — every per-domain value.
The cause is **arithmetic, not empirical**:

- all six folds pick **`L = 6`**, the **first layer of the `6–14` knockout band**;
- at the band's first layer no lower layer is perturbed, so the read row's state is a function of
  unperturbed inputs masked by **its own query row** — and both scopes block the same keys there;
- measured: `ko_on` vs `ko1` at `L6`, **max abs elementwise difference 0.000e+00** over all 2520
  shared rows, rising to 0.36 at L7 and 1.42 at L14. An adversarial review pointed specifically at
  this could not break it: **0 differing fp16 bit patterns, 0/2520 rows, in all three banks.**

⇒ At `L = 6`, the only layer any `R-093` fold reads, its "whole-query" manipulation is
**arithmetically identical to blocking the single codeword row**. **The verdict (`R5-FAIL`, the
dissociation) is unchanged; ⛔ the sentence *"destroying the whole demonstration→query pathway"*
overstates what was in force at the site read.** The correct statement is *"blocking the codeword
row's own view of the demonstrations leaves the representation at that row 94 % decodable."*

⚠ **General trap, for the methods section:** *any band-limited intervention read at the band's **first**
layer measures only the read row's own mask* — a trap applying to **every knockout result in this
project that selects `L = 6`**.

### 9.6 `R-096` — above the degenerate layer, the scopes DO separate

`PR-045` re-read `R6` and §13 on layers **7–14**, a **structural** exclusion derivable from the band
definition, applied uniformly to both arms and to selection, **declared before the numbers**.

| | baseline | knockout | drop | domains | of available |
|---|---|---|---|---|---|
| `KO-1`, codeword row only | 0.6784 | 0.6594 | **+0.0190** | 4/6 | 5.5 % |
| `KO-legacy`, whole query | 0.6784 | 0.6418 | **+0.0365** | 5/6 | 10.6 % |

⚠ Dropping `L6` costs the baseline **0.0745** (below the declared 0.10 VOID bar, **narrowly**), so
these are weaker measurements on a weaker probe. ⛔ **No p-values.** The ratio **0.520** is descriptive
with no bar.
✅ **What it buys:** the two scopes **separate exactly where `C-068` predicts they would**, and
`R-093`'s dissociation **survives on a grid `L6` cannot influence** — even the whole-query knockout
removes only **10.6 %** of available accuracy.
⛔ **May NOT be said:** *"the codeword's own row accounts for half the causal effect"* — the 0.520
ratio is two drops of 0.019 and 0.037 on a weakened probe, with no p-value and no bar.

---

<a name="10-gates"></a>
## 10. Gates `R6`, §13 and `R8` — three CANNOT ANSWERs, each for a different reason

### 10.1 `R6` — uninformative by construction

`PR-044` produced numbers identical to `R-093`'s to sixteen digits, for the arithmetic reason in §9.5.
`PR-045`'s layers-7–14 re-read is **descriptive by declaration**. ⇒ ⛔ **`R6` has no verdict.**
It is **not a null and not a confirmation.**

✅ What the arms *did* establish, methodologically: the scoped knockout **works** (1.7 % of the dose,
exact closed-form liveness on **7560 rows** across three banks, zero decode leakage, zero scope
violations) and is validated for future use; and `ko_off` vs `ko1` **do** differ at L6
(rel 0.158, cos 0.988), so the scoped knockout is **not a no-op** — it is simply not distinguishable
from the whole-query one *at that layer*.

### 10.2 §13 — the instrument is at ceiling by construction

Reading the concept signal at the **explicit concept word** gives baseline **1.0000 in 6/6 domains**
on both grids, so the available range is **zero**. Cause is structural and foreseeable: the capture
site for cell `B` **is the token ` bomb` itself**, so the probe reads **lexical identity**. No choice
of layer repairs it (picks scattered across L7–L14 on the restricted grid). ⇒ ⛔ **CANNOT ANSWER; a
design error, not a property of the model.** §13 has **no valid instrument** this sprint.

*(⚠ `C-070` concedes the *argument* was wrong even though the verdict is right: §69.3's "a readout
pinned at ceiling cannot fall" is a **logic error** — a ceiling means it cannot **rise**; it could have
fallen by 0.6667, and the analyzer computes exactly that denominator.)*

### 10.3 `R-097` / gate `R8` — CANNOT ANSWER, and the bound was computed before any ρ

`scripts/dcs_pr042_mediation.py`, CPU only, 11.5 s. **Structured backwards from a normal analyzer:**
it spends its effort on the **predictor variance and the design**, and computes the correlation last
under an explicit "NOT INTERPRETABLE" banner. It **manufactures no null** — there is no null model in
the file.

**The exact n = 6 inference bound, enumerated over all 720 rank assignments before any observed ρ:**
p-floor **2/720 = 0.002778**; of 18 attainable |ρ| levels **exactly three** reach α (1.0000, 0.9429,
0.8857); the next rung (0.8286) is p = 0.0583 and fails. ⇒ the bound is **Σd² ≤ 4**.

| | |
|---|---|
| predictor `x` (per-domain probe drop) reliability | **0.5758** vs 0.50 bar — ✅ **PASS** |
| range / rms(se) | **4.2120** vs 4.0 bar — ✅ PASS |
| outcome A (`mapping_use`) | ⛔ UNUSABLE — blind at baseline (`R-088`, GAP −0.0396 vs bar 1.0) |
| outcome B (semantic probe) | ⚠ available, but it is the model's **report**, not behaviour |
| outcome C (attack rate) | ⛔ NOT FEASIBLE — lives on `cds116`, whose shared-**name** domains share **0/672** byte-identical prompts and **3/960** demonstration sentences with this bank, at 10 judged rows/domain (binomial SE 0.158) |
| `y` reliability (candidate B) | 0.6334 |
| attenuation ceiling √(rel_x·rel_y) | **0.6039** < 0.8857, the smallest reachable |ρ| |
| power under a **perfectly monotone** truth (20,000 draws) | ⛔ **0.2501** vs 0.50 bar |
| … even with `x` measured without error | 0.4818 — still below the bar |

⇒ ⛔ **`R8` is CANNOT ANSWER for two independent reasons**, the first design-level: **no behavioural
outcome exists on the bank `x` was measured on**; and even the readout substitute is uninformative by
construction — *a perfect relationship would fail this test three times out of four*.
⛔ **ρ = +0.60 (p = 0.242) was computed and is NOT CITABLE IN EITHER DIRECTION.** It is not a null; no
null model was fitted.

⚠ **`R-097` carries a recorded process deviation:** no `PR-xxx` preregistration was committed before
that analyzer first ran — it was written, run, then committed. **Recorded, not excused**; `R8` may not
be promoted on this run. Damage limited because the decisive failure (power 0.2501 vs 0.50) is not
marginal, and the *other* gate that passes works **against** CANNOT ANSWER, so choosing it after
seeing the number would have been self-harming.

**What `R8` would need, quantified:** (a) a behavioural outcome measured on *this* bank, with enough
judged rows/domain that its SE is small relative to the between-domain spread; (b) more than 6
independence units. **Neither is purchasable by re-analysis.**

---

<a name="11-phase4"></a>
## 11. PHASE 4 — `R-088`: the intuitive readout is blind

`PR-038` asked Matan's PHASE 4 question — *does destroying the pathway also destroy the model's
**explicit** reading of the codeword?* — using an existing `mapping_use` probe already in the repo
(`comprehension_usage`: *"is the word `button` used **literally**, or as a **code** for something
else?"*), judge-free and deterministic. **No new prompt, no new code.**

A normaliser was fixed **before the data**: `GAP = mean(base, C) − mean(base, A)`, with `GAP < 1.0`
⇒ `CANNOT ANSWER`.

| baseline, `comprehension_usage` | value |
|---|---|
| cell `C` (`natural_doublespeak`) | −3.0581 |
| cell `A` (`benign_literal`) | −3.0185 |
| **`GAP`** | **−0.0396** (3/6 domains with C > A) |

⇒ ⛔ **The gate fired; the primary was not computed, exactly as preregistered.** *Without that gate we
would have differenced two arms on a readout that measures nothing, and could have reported a
manufactured null.*

**And the reason is the result** — the same `core2x2` block, same bank, same conditions, through two
questions:

| question put to the model | cell `A` | cell `C` | swing |
|---|---|---|---|
| `semantic_forced_choice` — *"…does `button` refer to a button or to a bomb?"* | −7.272 | **+5.812** | **+13.08** |
| `comprehension_usage` — *"…is `button` used literally, or as a code for something else?"* | −3.019 | −3.058 | **−0.04** |

**0/24** benign and **1/24** doublespeak rows answer `coded`; per-domain means negative in 6/6 domains
in **both** cells. ⇒ *Asked what the codeword refers to, the model says `bomb`. Asked whether the
codeword is being used as a code, the same model on the same prompt says `literally`.*

**A direct answer to the brief's §11:** an *intuitive* readout was requested on the theory it would be
cleaner than ASR — **on this instrument it is not cleaner, it is blind.**

**Caveats:** ⛔ Not *"the model is unaware of the remapping"* — the forced-choice readout on the same
prompt shows it is not; this is a fact about the **metalinguistic question**, not the model's state.
⛔ Not *"`comprehension_usage` is broken"* — its `option_mass` is 0.22–0.41, far above the 0.05 bar,
so the model engages the options and answers `literal`. ⚠ One asymmetry not over-read: mass is 0.224
in `A` vs 0.414 in `C` ⇒ the doublespeak condition moves the model toward *considering* the
literal/coded distinction without moving *which* answer it gives.

⛔ **PHASE 4 is CLOSED at `CANNOT ANSWER` and is not re-run with a lower bar.** The live successor is a
**3-way object-level** probe ("Bomb / Button / Neither"), a new experiment needing its own
preregistration, not a rescue of this one.

---

<a name="12-r085"></a>
## 12. `R-085` — the control masks are not row-independent

The brief's §16C, the one piece of the control-variance analysis never run. **Zero GPU, 56–83 s**,
reusing the persisted `control_draw` positions and **importing** `nondemo_control_draw` rather than
reimplementing it. Provenance hard-checked and **passed on all 9,280 rows**.

**Primary:** absolute-position Jaccard over all C(1160,2) = **672,220** row pairs per arm, against a
row-independent sampling null (mean 0.2459 ± 0.0003) ⇒ observed **0.4772–0.5095, ≈ 2.0× the null,
z = +715…+815, 8/8 arms**, sign test over arms **p = 0.0078 = the attainable floor** (floors declared
before any p; the script returns `CANNOT ANSWER` when the arm count puts the floor above 0.05,
verified live with an n = 2 run).

**Mechanism, verified in source:** `nondemo_draw_seed(control_seed, draw_index)` depends only on the
run seed and the draw index — **not on the row** — and `knockout_key_set` calls the sampler once per
row with that same seed. Measured: `distinct_draw_seeds = 1` in all 8 arms, and on the 701 row pairs
per arm with identical `(n_pool, k)` the pool-**rank** sets are **byte-identical in 1.0000 of pairs
versus 0.0000 under the null**.

**What it explains:** `R-077`'s split-half ρ = +0.988 and 93.5 % draw-offset variance — a measurement
that had no mechanism; and `R-076`'s null, because the offset is **not a row-level property at all**.

**Caveats:** ⛔ It does **not** invalidate `R-075`, `R-076` or `R-077` — each measured what it
measured. What changes is the **interpretation of the between-control spread**: not sampling noise
over row-independent draws, but variation among **8 distinct systematic maskings**. ⚠ This is a
property of the **control construction**, not a finding about doublespeak — it belongs in a methods
section. ⛔ It does not say the control is *wrong* (a fixed mask per arm is a defensible design), only
that the eight arms are **not eight independent samples**, so the spread **cannot be read as an error
bar**. ⇒ It opens **`Q-004`**.

⚠ **One layer of this was itself a false positive** (`A-027` §45.3): the script's own population
verdict *"TRUE AND VARYING — a live candidate for the offset spread"* **may not be quoted** — its rule
is not discriminating, and 30 pseudo-arms generated *by construction* from the same single-seed
mechanism also exceed its threshold. `R-085`'s measurements survived an independent re-implementation;
only that verdict layer did not.

---

<a name="13-lit"></a>
## 13. Literature — the novelty claim narrows twice

### 13.1 `A-022` (2026-09-05) — the sentence that must never be written

> ⛔ *"Nobody has causally intervened on the demonstration→query pathway in in-context learning."*

**FALSE, and has been since 2023–24.** Both directions are published: **Hendel, Geva & Globerson
(arXiv 2310.15916)** patch a compressed task vector into a zero-shot pass at the query (*sufficiency*);
**Todd et al. (arXiv 2310.15213)** ablate function-vector heads found by causal mediation
(*necessity*). ⇒ This phase's method is a **redirection** of an existing intervention.

Also found and previously **missing from the matrix**: **Wang et al., *Label Words are Anchors*
(2305.14160)** — the closest method precedent inside ICL; and **Cheng & Zhang (2605.04061)** — *"single-
position intervention 0 % success, multi-position up to 96 %"*, with an independently-found
**"universal intervention window at ~30 % depth" that coincides with our L6–14** — the most direct
threat to `R-022`'s step in K.

⚠ **A wording rule adopted phase-wide:** our headline is a **readout** endpoint and the behavioural
link is not established, and two 2026 papers exist precisely to caution against inferring behaviour
from such an endpoint. ⇒ Write **"abolishes the forced-choice preference"**, never **"destroys the
remapping"**.

### 13.2 `A-025` (2026-09-06) — a closer precedent, and the framing published four days ago

- ⛔ **`F-1`** — **Bakalova, Veitsman, Huang & Hahn, arXiv 2504.00132.** The matrix cited this paper's
  **follow-up** and **missed the parent that contains the ablation**. Verified verbatim from the HTML:
  it ablates **demonstration-output → final-prediction-position** edges by replacing K/V with
  counterfactual activations, at every layer and head simultaneously, scoring accuracy drop.
  ⇒ *"We are the first to causally intervene on demonstration→query attention in ICL" is FALSE.*
  **What survives, narrowly:** they patch counterfactual K/V, we **zero** attention; they run all
  layers and heads, we run a **layer band**; they score task accuracy, we score a semantic readout;
  they intervene at a single query position so there is **no analogue of our K ladder**; and they have
  no attack, no semantic remapping, and no `intervention × condition` interaction.
- ⛔ **`F-2`** — **Sudheendra & Srivastava, arXiv 2609.02438, submitted 2026-09-02 — four days before
  the phase read it.** It publishes the representation-vs-behaviour dissociation framing in almost
  exactly this design shape: near-chance behavioural performance while the property is almost perfectly
  decodable and remains so under **held-out templates, domains and inference families**, with
  probe-direction interventions having only weak nonspecific effects vs random controls.
  **It does not scoop us** (logical validity, not concept remapping; no attack; no attention
  intervention) — **but if we lead with dissociation it is a citation, not a contribution.**
- ⛔ **`F-3`** — Cheng & Zhang's 0 %-transfer-despite-100 %-probing result bears **directly on
  `PR-035`** as the strongest published warning that a probe result predicts nothing about causal use.

⇒ **`Q-002` for Omer and Matan** (§17). The defensible novelty is now a **three-way intersection**,
not a single axis: *zeroing demonstration→query attention **within a layer band**, on a **semantic-
remapping** condition, with an **intervention × condition** interaction and a **query-row-count
threshold**.*

⚠ **Standing rule, applied twice:** the query-row-threshold axis returned nothing on target across
four search phrasings and an arXiv API query — recorded as a **null search, not evidence of novelty**.
⚠ **The largest uncovered risk remains open:** no OpenReview or proceedings search was performed, so a
competing mechanistic Doublespeak paper under review now would be invisible.

---

<a name="14-scoreboard"></a>
## 14. The scoreboard

### 14.1 Gate ledger (the phase's own, §71.5, as decided by `R-097`)

| gate | status |
|---|---|
| `R1` | ✅ **PASS** |
| `R2` | ✅ **PASS** |
| `R3` — lexical transfer | ⛔ **FAIL on accuracy** (`R-092`); direction transfers at **AUROC 0.795** (`C-066`) — never quote one without the other. Previously recorded **NOT IMPLEMENTED** in the frozen analyzer (`C-064`). |
| `R5` — does the knockout destroy the concept signal? | ⛔ **FAIL** — the signal survives (`R-093`); an **informative** negative. Survives `R-093a` (matched population) and `R-096` (layers 7–14). |
| `R6` — the same under `KO-1` | ⛔ **CANNOT ANSWER** — `PR-044` degenerate by construction (`C-068`); `PR-045` descriptive by declaration. **No verdict.** |
| `R7` | ✅ **PASS** |
| `R8` — does destruction predict behaviour? | ⛔ **CANNOT ANSWER** — no behavioural outcome on this bank; power **0.2501** vs a 0.50 bar (`R-097`). |
| §13 — read at the explicit concept word | ⛔ **CANNOT ANSWER** — instrument at ceiling by construction. |
| template-family claim | ⛔ **NO VALID INSTRUMENT** (`C-067`). |
| installation gate (`R-078`) | **PARTIAL** — bomb/knife/club PASS 6/6; **gun installs inconsistently (4/6)**. |
| PHASE 4 (`PR-038`) | **CANNOT ANSWER**, closed (`R-088`). |

*(No `R4` row appears in the ledger.)* The log's own gloss: **"Four CANNOT ANSWERs and one FAIL are
not four nulls and a null."**

### 14.2 What this phase established

| # | claim | scope / caveat |
|---|---|---|
| `R-086`/`R-089` | **A linear probe on the codeword's L6–14 state identifies WHICH concept the demonstrations installed** — 0.7485 vs 0.333, 6/6 held-out domains, p = 0.005 from a test calibrated at FPR 0.030 | ⛔ **decodability, not causality**; 6 domains, 1 model, 1 band; the bomb-absent control clears at one replicate's margin |
| `R-091` | **The remapping axis and the concept axis are different directions** — `v_bomb` AUROC 0.9987 for *remapped?* but **0.5743** for *which?*; the residualized axis is 0.6070 / **0.8964** | ✅ reconciles Part 1's `R-002` negative; ⛔ strength confound not fully closed by the primary |
| `R-093` | **The knockout destroys the READOUT (+3.37 → −3.02, sign flip) and leaves the REPRESENTATION intact (94 % retained)** | ⛔ description narrowed by `C-068`: at L6 the whole-query knockout is arithmetically identical to blocking the codeword row |
| `R-079`/`R-080`/`R-081` | **The K ladder: rungs 1–5 cut only chat scaffold; `K* = 7`, `shape = STEP`, 90 % of the effect arrives with one token** | ⛔ the decisive rung's token is `' bomb'` only because the question names it — a fact about the instrument as much as the mechanism |
| `R-088` | **The intuitive metalinguistic readout is blind** — same prompt, +13.08 swing on "what does it refer to?" and **−0.04** on "is it used as a code?" | a readout-dependence result; ⛔ not "the model is unaware" |
| `R-085` | **Control masks are not row-independent** — one seed per arm; Jaccard ≈2× the null on 8/8 arms | explains `R-077` and `R-076`; a **methods-section** result, not a doublespeak finding |
| `R-077` | **The between-control spread is a real draw offset** — split-half ρ = +0.988, **93.5 %** draw offset | upgrades Part 1's `R-075` from nuisance to target |
| `R-078` | **The 6-domain banks install their mappings** — bomb +13.08 (6/6), knife +4.09 (6/6), club +6.44 (6/6), gun +4.10 (**4/6**) | ⛔ `C-060`: a paired improvement is not an installed mapping — **6 cells PASS while cell `C`'s own mean log-odds is still negative** |

### 14.3 Retracted or withdrawn in this window

| # | retracted | why |
|---|---|---|
| `PR-031` run, and its ≈**0.72** primary | `C-049` | the `n_examples = 0` null control **fired** (0.5556, 6/6); the run is VOID and the number may not be quoted |
| `C-058`'s downgrade of `PR-035` | `C-061` → `C-062` | the symmetry makes p **larger**, not smaller — it is **conservative**. The `POSITIVE` verdict is restored (`R-089`) |
| `R-092` §61.2 *"encoded in different directions"* | `C-066` | the directions are **shared**; only the decision **offset** fails to transfer |
| `R-082`'s *"the codeword's query rows are not necessary"* | `C-054` | template-bounded — on `semantic_one_word` the codeword row alone carries **32.7 %** |
| `R-093`'s *"destroying the whole demonstration→query pathway"* | `C-068` | at L6 it is arithmetically identical to blocking the codeword row. **Verdict unchanged, description overstated** |
| `A-020` §8.1's *"cell `A` is a different corpus in each concept bank"* | `C-060` | holds **modally** (250/348 ids), not universally — bomb and club share a byte-identical whole prompt on 82 design cells |
| `A-026`'s promotion of `R-080`/`R-081` | `C-055` | promoted on a verifier that **seven corruptions walk through**; re-established on a second, row-level verifier |
| job 854618's `V2 PASS` | `A-028` | printed from inside `V3`'s success branch; **carried no information** |
| `R-085`'s script verdict *"TRUE AND VARYING"* | `A-027` §45.3 | a false positive; its rule is not discriminating |
| the `option_mass < 0.30` "degraded regime" framing | `C-059` | unpreregistered — the plan fixes the bar at **0.05**, twice |
| `A-027` §45.4's downgrade of `C-057` | `C-062` §51.3 | test-set selection inflates FPR **0.020 → 0.090**; `C-057` was serious and correctly raised |
| §72.3's variance decomposition | `C-070` | the **stale pre-`C-069`** upper-bound pair, printed beside the post-fix reliability |
| *"the selection maximises cell-`B` accuracy"* | `C-070` | the surface is **flat at 1.000000 on all 36 grid points**; the pick is a tie-break artifact of grid order |
| *"bomb installs ~3× harder than any hard negative"* | `C-070` | it is **2.03×** against club — and club is the control |

### 14.4 Sentences that must not be written (this phase's additions)

- ⛔ *"We are the first to causally intervene on demonstration→query attention in ICL"* — **false**
  (arXiv 2504.00132).
- ⛔ *"The model represents the codeword as BOMB"* — over-general. Licensed form: *"the state of **this**
  codeword, in **this** lexical setting, carries which concept was installed."*
- ⛔ *"The concept signal does not transfer across codewords"* — `C-066` refutes it.
- ⛔ **Any causal reading of `R-086`.** It is a decodability result, and `R-093` shows the signal
  **survives** the knockout that destroys the readout.
- ⛔ *"The codeword's query row is not necessary"* — template-bounded (`C-054`).
- ⛔ *"K=1 and K=2 show one or two query rows don't matter"* — those rungs are chat-template scaffold.
- ⛔ *"48.1 % is essentially 50 %, so it's the codeword row"* — the goalpost move `R-083` refused.
- ⛔ *"The knockout does nothing"* — it flips the semantic readout from +3.3696 to −3.0151.
- ⛔ *"Gun does not remap"* — it installs **inconsistently across domains** (4/6).
- ⛔ *"The representation is present but re-based"* (the script's printed label) — it is **present and
  unmoved**.
- ⛔ Any citation of **0.6974** as lexical transfer — it is basket-trained and basket-tested.
- ⛔ Any **p-value** for the cell-`F` contrast or for `P1`, **ever**, from these banks.
- ⛔ *"Gate `R6` passes"* or *"gate `R6` is null"* — `R6` has **no verdict**.
- ⛔ *"The codeword's own row accounts for half the causal effect"* — the 0.520 ratio has no bar.
- ⛔ *"The concept survives even when its own word is blocked"* — that readout is at **ceiling**.
- ⛔ *"The result is robust to hyper-parameters"* as a **preregistered** check — the 36-point sweep is
  **post-hoc**.
- ⛔ Any novelty claim resting on a search that returned nothing — recorded as a **null search**.
- ⛔ Treating **any** of the four `CANNOT ANSWER`s as a null — *"in either direction"*, since the
  collaborator drafts were also caught calling `R8` **"unrun"** while reporting it CANNOT ANSWER.

---

<a name="15-corrections"></a>
## 15. Corrections and bug catalogue — the methodological record

This phase produced **25 corrections (`C-047`…`C-071`) in ~23 hours.** The patterns are more valuable
than any individual fix.

### 15.1 Bugs caught before they produced a number

- **`C-050`** — the analyzer did not implement its own preregistration; caught by **reading source
  before running it**, and it would have **crashed rather than silently skipped**.
- **`C-053`/`A-024`** — the 33-agent audit, seven further defects including the 8-way `prompt_id` join
  that would have produced *a plausible headline with zero missing rows and no VOID raised*.
- **`C-057`** — two secondaries carried the selection defect; **declared INVALID before their numbers
  existed**, while the job was still running.
- **`C-070`** — the cell-`B` selection **selects nothing**; found by measuring the selection surface,
  which no artifact had ever recorded because **every call site discarded `best_acc`**.

### 15.2 The dominant failure mode: a check that cannot fail

Five distinct instances in one phase, each one layer up from the last:

| # | the check | what it actually asserted |
|---|---|---|
| `C-049` | `VOIDS_RUN` | computed, written to JSON, **never read** — plus an undeclared +0.15 slack |
| `C-049` | the mutation harness | printed `OK` on a corruption it **never applied**, because it only checked that *some* check failed |
| `C-055` | `dcs_verify_kladder.py` | **seven corruptions walk through** — it reasoned about arm *directories* and the *producer's own key set*, never inside a scored row nor joined to the bank. ⇒ *"a verifier that iterates the producer's own key set can be made VACUOUS BY THE PRODUCER"* |
| `C-056` | `dcs_verify_pr035.py` | its `C6` recomputes the blocking null **and nothing else**, so the primary is read from the producer as ground truth. **A fabricated headline passes all fourteen checks** — demonstrated by rewriting the primary to a self-consistent POSITIVE on a fixture of pure noise |
| `A-028` | `V2` | printed `PASS` from **inside `V3`'s success branch**, never reading the producer's picks, and could never enter `fails` |
| `C-071` (`H-1`…`H-4`) | four verifier harnesses | one printed *"VERIFIER BREACHED"* over **zero attacks**; one credited a **zero-byte** corruption as a confirmed blind spot; two **passed over the empty set** |

⚠ **This matters for how much weight the verification chain carries:** the earlier verification passes
ran with those harnesses in place.

### 15.3 Fixes that were themselves wrong, in the same direction

Twice in one day, and the log names the pattern:

- **`C-069` fix #2** replaced an unconditional `CANNOT ANSWER` with `setdefault(..., False)` — **the
  same defect with an extra keystroke**; nothing ever set it `True`, so the `ANSWERABLE` branch stayed
  unreachable.
- **`C-071`'s `H-2` fix** refused a `SURVIVES` credit whenever the producer verdict contained `VOID`
  **or** `NOT ATTRIBUTABLE` **or** `CANNOT` — which flipped a **real** blind spot to "not as declared".
  The distinction it missed: **`VOID` means the artifacts confess**; `NOT ATTRIBUTABLE` and
  `CANNOT ANSWER` are **legitimate scientific verdicts a perfectly clean run can reach**.

> ⇒ **A fix is not verified by having been written.** Both were caught only by *running the thing
> afterwards and reading what it printed* — the rule this phase applies to results, applied to repairs.

### 15.4 Selection, permutation and the independence unit

- **The §28.2 defect** — grid-searching `(layer, C)` on the test population's own labels and then
  freezing those picks across the permutation null — is **the dominant error, not the symmetry**:
  measured at **3.3× the FPR at 3 classes and 4.5× at 2 classes** (`R-090`).
- **`C-067`** — the leave-one-block-out instrument is **UNINTERPRETABLE**: its null sits at **0.8494**,
  not chance, because LOBO folds on `bank_block` while `group_permute` relabels per **domain**, so the
  relabelling hits train and test identically and the classifier simply learns it. **Two independent
  defects in one instrument, the second only visible once the first was repaired.** ⛔ Its null was
  **not** fixed after the fact — changing a published instrument's null after seeing it misbehave is
  exactly what the standing rules forbid.

### 15.5 Preregistration prose drifting from the code that implements it

**Three internal contradictions**, all resolved before any outcome was read: §23.1's cell-`B` clause
(`C-050`), gate `R3`'s train/test description (`C-064`), and `PR-040`'s "train on cell `B`" prose
(`PR-040b`). ⚠ *"In each case the code was right and the prose was wrong — which is lucky, and is not
a method."*

Related: **`PR-037` §30.6's declared outcome set did not partition the space** — it defines
`CANNOT ANSWER` as *"the sign test fails* but the magnitude sits in [0.2, 0.5]", and the actual result
had the sign test **pass** at the floor with only the magnitude failing. The conservative verdict is
right; the declared branches were not exhaustive.

### 15.6 Operational

- **`DCS-041`** — a background job monitor reported **all six jobs COMPLETE while five were PENDING**,
  because *zsh does not word-split unquoted variables*, so `$JOBS` expanded as a single token and the
  loop ran once. ✅ **What saved it:** the monitor also printed `caches present: 2`, contradicting its
  own headline. ⇒ **Every monitor now prints a corroborating artifact count beside its verdict**, and
  analyzers no longer trust job state at all (`load_results` requires `DONE.json`).
- **`DCS-044`** — the `PR-035` job ran **7 h 55 m, produced one line of output, and was cancelled with
  nothing written.** Measured cause: **BLAS thread oversubscription** — three real fits take **2.88 s
  at `OMP_NUM_THREADS=1`, 1.99 s at 4, and 34.06 s at 16**, and the job requested 16 CPUs. Fit budget
  ≈ **22,572 fits**; at the oversubscribed rate it needed ~40 more hours against 2 h remaining.
  ⚠ *A correctness fix (`C-053` §28.2) had made the analysis ~30× more expensive*, and the author's
  "3–5 hours" estimate was unmeasured and **wrong by ~10×**. ⇒ **Rule: never submit a long analysis
  job without (a) a measured per-unit cost, (b) `OMP_NUM_THREADS` set explicitly, (c) progress
  output.** The progress ticks added were **proven print-only**, line by line.
- **`DCS-043`** — the primary was started on the **login node** and ran 41 minutes at 1133 % CPU with
  no output before being killed. Nothing lost; resubmitted to `cpu-killable`.
- **`B-019`** — ⛔ **the Llama weights were purged from scratch mid-session.** All three `PR-038` arms
  failed in 4–47 s with `mkdir: cannot create directory '.../.cache/huggingface': File exists` — a
  **misleading message**, because the path is a **symlink** and `mkdir -p` reports "File exists" on a
  **dangling** one, and the wrapper runs under `set -euo pipefail`. `/vol/scratch` itself was healthy
  with other users' directories present ⇒ **this user's scratch directory was purged, not the volume**.
  ⚠ **No result was invalidated and nothing that already ran needed re-running** — completed arms,
  caches and the `PR-035` primary all live under `outputs/`. Repaired by re-downloading (16 G, 10:24–
  10:28). ⇒ **`Q-003`**: scratch is a purged-by-policy volume and the project symlink points into it.

---

<a name="16-code"></a>
## 16. Code and artifacts produced

**25 new scripts, 18,613 lines across all `dcs_*.py`.** ⚠ **`src/boombness/` has NO changes in this
range** (`git log 8fb3c7e3..HEAD -- src/` is empty) and **no tests were added or modified** — every
new capability was built in `scripts/` on top of existing `src/boombness/` modules, and the
bug-pinning function was carried by the verifier/red-team layer instead.

**Common architecture across every analyzer:** a docstring stating *"FROZEN BEFORE ITS DATA"* pinned to
a numbered section of the phase log; preregistered constants as module globals; a `DONE.json`
completeness check before reading any run dir (the `C-047` rule); and an explicit **attainable p-floor**
statement — hence *"exactly one significance test"* in most files.

### 16.1 Producers and analyzers

| script | lines | what it computes |
|---|---|---|
| `dcs_bombness_specificity.py` | 798 | the `PR-035` primary — the concept probe, its blocking null, both 2-class contrasts, the cell-`F` and LOBO secondaries, the length-only control. **Frozen producer**; modified 5× and never edited after publication |
| `dcs_extract_under_ko.py` | 1238 | ⭐ **the gate-`R5` capture bridge** — the single biggest new piece of infrastructure. Writes the exact cache format the frozen analyzer consumes, captured **while an attention knockout is live**. Reimplements nothing; a scope that cannot fire is **refused at argument time**, never discovered as a null |
| `dcs_pr042_mediation.py` | 1066 | gate `R8` — structured backwards: spends its effort on **predictor variance and design**, computes the correlation last under a "NOT INTERPRETABLE" banner, **manufactures no null** |
| `dcs_diffmeans_directions.py` | 998 | `R-091` — diff-in-means directions; **no layer selection, no hyper-parameter**, so no selection defect is possible |
| `dcs_metadata_sidecar.py` | 1467 | the §19 prompt-validation table + declared-vs-observed metadata; compound-key collision tests that **must fail** on a `prompt_id`-only join |
| `dcs_readout_family.py` | 581 | a **reporting instrument, not a test** — decomposes `semantic_logodds` into its family; names D `concept_binary_prob`, **never `P(bomb)`**; **refuses to emit a cross-arm difference** |
| `dcs_mask_overlap.py` | 540 | `R-085`; the normalisation is a **matched null**, not a rescaling |
| `dcs_kladder_analysis.py` | 264 | `R-080`/`R-081`; `find_arm()` makes DONE-completeness part of arm *selection* |
| `dcs_pr037/038/040/041/044/045_analysis.py` | 173–314 each | one gate apiece, each with exactly one significance test |
| `dcs_draw_offset_reliability.py` | 166 | `PR-030` — the gate that could have cancelled a spend in flight |
| `dcs_null_calibration{,2}.py` | 51 / 114 | the head-to-head that produced `R-090` |
| `dcs_bombness_installation.py`, `dcs_installation_gate_fc.py` | 182 / 122 | the two installation gates (`PR-033` VACUOUS, `PR-034` PARTIAL) |

### 16.2 Verifiers and red-team harnesses

| script | lines | what it pins |
|---|---|---|
| `dcs_verify_pr035.py` | 1787 | 14 checks; each of eleven injected defects must be caught by its **own designated check** — *"some check failed" is not acceptance* |
| `dcs_verify_pr035_primary.py` | 450 | closes the named root hole: **recomputes the primary from the preregistration text**, with its **own permutation seed (90613)**. Also the shared probe library imported by `pr040/041/044/045` |
| `dcs_verify_kladder.py` | 1514 | arm identity byte-for-byte against the committed argsfile, dose per family, pairing, the K=8 anchor, Holm membership |
| `dcs_verify_kladder_rowlevel.py` | 326 | the seven corruptions the first verifier passes; declares its expected key set **from the preregistration**, not from the producer |
| `dcs_redteam_pr035_verifier.py` | 783 | attacks the verifier. Confirms its eleven detections are real, then **finds seven it does not catch** |
| `dcs_redteam_kladder_verifier.py` | 635 | the same treatment for the kladder verifier |
| `dcs_verify_bombness_specificity.py` | 292 | `A-021`; **later found defective** (`C-049` §22.5) — its harness printed OK on a corruption it never detected |

⚠ The two red-team files and `dcs_verify_pr035.py` were **untracked until commit `7c49c78d`**.

### 16.3 Argsfiles and artifacts

**40 new `runargs/dcs/` argsfiles** (K-ladder rungs 1,3–7 + the K=8 re-run anchor; the `semantic_one_word`
ladder; PHASE 4 comprehension; the 9 capture-bridge arms) plus **17 new `runargs/bombspec/`** (8
extraction, 8 installation, 1 smoke). All GPU arms: Llama-3.1-8B-Instruct, bfloat16, `--attn-impl
eager`.

**13 new JSONs in `outputs/boombness/dcs_analysis/`** — `dcs_bombness_specificity{,_rerun}.json`,
`dcs_bombness_installation.json`, `dcs_installation_gate_fc.json`, `dcs_kladder.json`,
`dcs_pr037/038/040/041/042/044/045.json`, `dcs_draw_offset_reliability.json`. **Each carries its own
verdict string**, and every `CANNOT ANSWER` is explicitly marked *"NOT a null"* **in the artifact
itself**, not only in prose.

⚠ **Only 2 of the 13 are tracked in git** — see §19.4.

---

<a name="17-blockers"></a>
## 17. Blockers and the five open questions for Omer

### 17.1 Blockers

| id | status | content |
|---|---|---|
| `B-017` | **OPEN — permanent scope limit** | Two 38-domain banks declare `concept: knife` but were generated from **bomb** pools; the demonstrations install bomb semantics. ⇒ concept-backed hard negatives exist **only at 6 domains**, which is why this whole phase runs there |
| `B-018` | **OPEN — declared INFEASIBLE, conditions every downstream causal claim** | The dose-matched control cannot be built on the `main` `button_bomb` bank: **164 of 168 rows** cannot carry it (`match_ratio` 0.048 at n=4, **0.000** at n=8). Written on mechanical infeasibility with no outcome read. Binds `R-083`, `R-088`, `R-093` |
| `B-019` | **REPAIRED in practice, never marked closed** | Llama weights purged from scratch; re-downloaded (16 G verified on disk). ⚠ But `~/.cache/huggingface` is **no longer a symlink** — the home cache still holds the 8.9 MB stub, so the restored copy lives **only** on the purged-by-policy volume |
| `B-020` | **DOES NOT EXIST** | the id was skipped |
| `B-021` | **CLOSED** | gate `R5` blocked on a missing bridge; the bridge was built (`Q-005` answered) |

### 17.2 The five open questions

- **`Q-001`** — *does the aligned comparator rebuild get funded, and on what result?* Concept-backed
  hard negatives exist only at 6 domains on a different preset, so `PR-031`'s answer **does not
  transfer** to the population where the causal results were measured, and stage S3 stays blocked.
  The rebuild (`S1b`) keeps `|benign`/`|filler`/`|remap` byte-identical and regenerates only the 38
  `|harm` pools, so cells `A`/`E`/`F` become identical by construction — but needs a `valence` subset
  flag, a **polysemy screen no existing guard performs** (nothing caught `club`), and API spend.
  ⚠ Bounded by `C-060`: cell `A` differs across concept banks **modally, not universally**.
- **`Q-002`** — ⛔ **paper positioning against arXiv 2609.02438** (submitted 2026-09-02), which
  publishes the representation-vs-behaviour dissociation framing in almost exactly our design shape.
  It does not scoop us, **but if we lead with dissociation it is a citation, not a contribution** —
  which may change which half of the paper is the headline. Plus the second novelty narrowing against
  arXiv 2504.00132.
- **`Q-003`** — the scratch purge will **recur by policy**. Move the cache somewhere durable, or add a
  "is the cache symlink live?" pre-flight to the wrapper? ⚠ Shared infrastructure was **not repointed
  unilaterally**.
- **`Q-004`** — should control draws be **re-seeded per row** (`seed + hash(prompt_id)`), making arms
  genuinely exchangeable, or **kept fixed per arm** with the between-arm spread reported as systematic
  rather than stochastic? It changes what a "control draw" means across the whole behavioural half.
- **`Q-005`** — *(the original, answered: the bridge was built.)* A **new, forward-looking `Q-005`** is
  open: should a future preregistration **shrink the selection grid**, or add a `selection_acc < 1.0`
  guard that VOIDs a selection which selected nothing?

### 17.3 Recorded but not closed

`H-6` (published `se_mcnemar` values are BLAS-thread dependent; at `OMP=1` one boundary row flips and
the analyzer returns VOID — `OMP=4` is now **binding on `PR-042` too**), `H-8` (`mask_head_mult`
inferred from row 0 and never bounded, so a whole-query knockout could complete under the scoped name;
the three shipped arms are unaffected), `H-10` (a verifier gap, not an undisclosed claim), and
`A-032` `B1`'s **stale code-review coverage gap** — the "no CRITICAL found" verdict covers
`40bcc969..524ee475`, and **4,260 lines landed after its endpoint**. *(That gap was then partly closed
by `A-033`, which reviewed exactly those 4,260 lines and found four CRITICALs.)*

⚠ **Also recorded as a gap, not closed:** the permutation p **0.004975124378109453** is
**not independently reproduced**. It is 1/201, the arithmetic floor at `n_perm = 200`, so checkable
only as *"no permutation reached the observed mean."*

---

<a name="18-live"></a>
## 18. Live state at 2026-09-06 19:18

- **SLURM: completely empty.** `squeue -u omeryosef` returns the header row only — **nothing running,
  nothing pending.** All GPU work in this sprint is finished. The last GPU output landed **18:03**
  (jobs 857564/857565, the `ko1` capture arms); the last analysis JSON at **19:08**.
- **Git: working tree clean** at `b80db84d`, branch `behavioral-causality-sprint`.
- ⚠ Two run directories `bombspecko_20260906_1838xx/1839xx` contain **only `config.json` +
  `RUNMETA.json`** — no `DONE.json`, no `results.jsonl`. Runs launched that produced no output.
  *(Harmless: every consumer filters on `DONE.json` — the rule adopted after `C-047`.)*
- **PHASE 7 closed `R8` at CANNOT ANSWER**; `PR-029` remains halted with zero results; nothing is
  preregistered and waiting to run.

---

<a name="19-verification"></a>
## 19. Independent verification of this document's numbers

Four agents re-checked every headline against the producing JSON and script, ran the verifier and
red-team harnesses, and inspected the live cluster state.

### 19.1 Clean matches (verified end-to-end)

| claim | artifact | verdict |
|---|---|---|
| `R-086` primary (0.7485380116959064, chance, 6/6, p = 1/201, all six per-domain values), the blocking null, the length-only control, all three 2-class contrasts, `P1` = 0.0000, LOBO, the class counts | `dcs_bombness_specificity{,_rerun}.json` | **MATCH** |
| `R-090`'s **entire eight-row calibration table**, including median-p and min columns, and the 3 h 14 m runtime | `outputs/boombness/logs/analysis_854780.out` | **MATCH exactly** |
| `R-078`'s installation strengths (bomb 13.0843, club 6.4350, knife 4.0892, gun 4.0980 with `n_domains_positive = 4`, `passed = false`) | `dcs_installation_gate_fc.json` | **MATCH** |
| **Every K-ladder rung** — Δ, % of Δ₈, negative-domain counts, p, Holm p, `option_mass`, `K* = 7`, `shape = STEP`, the +82.9 pp rise | `dcs_kladder.json` | **MATCH**, and independently re-derived |
| The K=8 anchor: **−6.61611153724554324 vs −6.61611153724554324**, absolute difference **0.0** | both run dirs | **CONFIRMED** by independent re-derivation from the four `results.jsonl` |
| `R-083`'s "CANNOT ANSWER by 1.9 points" — 48.089 % vs the 50 % bar, all six per-domain increments, p = 0.03125 = floor | `dcs_pr037.json` | **MATCH** ("1.9 points" confirmed) |
| `R-093` (ko_off/ko_on/drop/5-6/p/floor/11.5 %/bridge 0.0044/secondary 0.7120/verdict string) | `dcs_pr040.json` | **MATCH**; sign-test arithmetic re-derived |
| `R-092` (all six per-domain accuracies, mean 0.3962, both bars re-derived, verdict string) | `dcs_pr041.json` | **MATCH** |
| `C-068`'s "identical to sixteen digits" | `dcs_pr044.json` vs `dcs_pr040.json` | **CONFIRMED by direct float comparison — True on every field** |
| `R-096`'s ratio **0.5199999999999996** and the 0.0745 baseline cost | `dcs_pr045.json` | **MATCH**, recomputed exactly |
| `R-097`'s entire table — 720 permutations, p-floor, the three attainable levels, Σd² ≤ 4, reliabilities, ceiling, power 0.25015, ρ = 0.6 / p = 0.24167, all six sub-reasons for candidate C | `dcs_pr042.json` | **MATCH** |
| `R-088` (both cell means, GAP, 3/6, option_mass 0.371, primary **not computed**, verdict) | `dcs_pr038.json` | **MATCH** |
| `R-077` (K=8, sd 0.0783, split-half ρ 0.988, 93.5 % draw offset) | `dcs_draw_offset_reliability.json` | **MATCH** |

**Verifier stdout, run live:**
- `dcs_verify_pr035.py` — **all 14 checks PASS, `---> VERIFIED`**, including `C5b` (the null's picks
  reproduce from cell-`B` selection on 6/6 folds, all L6/C0.01) and `C8` (verdict re-derived).
- `dcs_redteam_pr035_verifier.py --self-test` — **`SELF-TEST OK`**, 8/8 rig checks, X1–X7 all
  `[SURVIVES]` as documented, positive controls `[CAUGHT]`.
- `dcs_verify_kladder.py` — **`VERIFIED`**, C1–C7 all PASS including token identity 380/380 at every
  rung; `--mutate` **7/7 caught by designated check**.
- `dcs_verify_kladder_rowlevel.py` — **`ROW-LEVEL VERIFIED`**, R1–R5 PASS, `MUTATION HARNESS OK`.
- ⚠ `dcs_verify_pr035_primary.py` — **did not finish**: 2 h 10 m wall, ~21 h CPU, zero bytes of stdout
  (it buffers and prints at the end). **No stdout verdict to report.** Its `V3`/`V4`/`V5` claims
  therefore remain confirmed by the log's record of job 854618 and `A-029`'s job 854790, not re-run
  here. The cheapest re-run is as a batch job at `OMP_NUM_THREADS=4`, not on the login node.

### 19.2 Claims with no artifact or code path behind them

1. ⛔ **`C-066`'s entire AUROC table** (the 0.7951 macro mean and all six per-domain values) — **no
   artifact, no code, log prose only.** `scripts/dcs_pr041_lexical_transfer.py` contains **no AUROC
   code**, and a repo-wide grep for 0.7951 / 0.9317 / 0.8691 returns nothing. It is internally
   consistent (the six values mean to 0.79515) — **and it is the correction that keeps `R-092`'s
   retracted sentence from being re-quoted.**
2. **`R-093a`'s matched-population figures** (0.7361 / 0.6865 / +0.0496 / 12.3 %) — **no committed
   artifact and no `*093a*` script.** An independent agent reproduced them to 16 digits, but there is
   nothing on disk to check.
3. **§69's dose triples and liveness counts** — run logs only. ⚠ And `C-070` concedes the per-arm
   pairing printed in the log is **wrong** (correct: bomb 495/28449, gun 495/28980, knife 522/30996 —
   the multiset is right, the assignment is not).
4. **§48.3's per-cell `option_mass`** (0.224 / 0.414) — only the pooled median 0.371 is stored.
5. **§74.2's 36-point grid sweep** — no grid artifact is stored.

### 19.3 Defects found by this verification pass

- ⛔ **§47's calibration table is unsourced and contradicts the only surviving artifact.** §47 reports
  the `PR-039` null at **2-class FPR 0.083 / 3-class 0.133**. The v1 artifact
  (`analysis_854724.out`) reports **0.140** and **0.100**. Neither 0.083 nor 0.133 appears anywhere in
  the repo. ⚠ The *direction* argument survives on 0.140/0.100, so `C-061`'s conclusion is unaffected —
  but **the two numbers printed in §47 are not reproducible.**
- ⛔ **§57.4 mis-attributes `R-090`'s commit.** It states job 854780 ran at `cd6dc033`;
  `analysis_854780.out` records `git_commit = d44f441b`. ⚠ The safety argument still holds (both
  precede the gate at `21036812`), but the cited hash is a **different job's**.
- ⛔ **§47.2's "the head-to-head is running (job 854722)" is stale and was never corrected.**
  `analysis_854722.err` shows that job **died in seconds**: `can't open file '…/scratchpad/nullcmp.py'`
  — the node-local-scratchpad failure mode. The real head-to-head is **854780**.
- ⛔ **§72.3's variance decomposition is the upper-bound variant** printed beside the point-estimate
  reliability, and divides to 0.5596 rather than the 0.5758 next to it. *(Already conceded by
  `C-070` §74.4 #2, which is the correct handling.)*
- ⚠ **"a different node" is wrong for the K=8 demo arm.** The log and both deliverables say the re-run
  ran on a different node. RUNMETA: `dcsk8_C_demo` **n-802** vs `dcsk8r_C_demo` **n-802** — same node.
  Only the *control* arm moved (n-802 → n-805). **The claim is half true and overstated.**
- ⚠ **The K=8 anchor's agreement is stronger — and therefore weaker — than stated.** A field-by-field
  row diff shows the 380 rows differ in **exactly one field, `arm`**; zero numeric differences
  anywhere. So this is **bit-level determinism of the whole pipeline**, which the log's own caveat
  concedes, and it carries **no independent information** about the K=8 estimate. Also: *"reproduces
  the inherited `R-022` value exactly"* fuses two things — the 15-digit comparator is a
  **re-analysis** of the 2026-09-03 arm; agreement with `R-022` **as published** is to 3 dp.
- ⚠ **`dcs_pr038.json` carries `ok_n: false` on both arms** while `n_rows` is 48 and `void` is empty.
  Cause: it imports `contract()` from `dcs_pr037_analysis.py`, whose module-level `EXPECT_N = 168`;
  PR-038's own gate uses its own `EXPECT_N = 48` and passed. **Substantively correct, but a reader
  auditing the JSON alone sees two flags that look like contract failures.** The same `contract()`
  reuse pattern appears in two other analyzers.
- ⚠ **Schema drift between the two specificity artifacts**: `verdict_inputs.null_control_passed`
  (bool) vs `verdict_inputs.null_control_p` (float). A consumer keyed on the older name reads `None`.
- ⚠ **§26.1's token table rows for K=8 and K=9 are not covered by any verifier** — the check stops at
  K=7.
- ⚠ **§30.6's declared outcome set does not cover the cell `R-083` actually landed in** (sign test
  passes, magnitude fails). The verdict comes from the analyzer's catch-all `else` branch, whose
  emitted string reads as if the sign test had failed. **The conservative outcome is right; the
  declared branches were not exhaustive.**

### 19.4 Provenance warnings

- ⛔ **11 of the 13 result JSONs are UNTRACKED** — `.gitignore:11` contains `outputs/`, so they are
  *ignored*, not merely unstaged, which is why `git status` reads clean. **Only `dcs_pr037.json` and
  `dcs_kladder.json` were force-added.** Every artifact behind the gate ledger — `dcs_pr040`,
  `pr041`, `pr042`, `pr044`, `pr045`, both specificity files, the two installation gates, the mask
  overlap and the draw-offset reliability — **has no committed copy.**
- ⛔ **The restored 16 G Llama checkpoint sits solely on `/vol/scratch`**, the volume `Q-003`
  documents as purged by policy and which **already purged once during this session**. And
  `~/.cache/huggingface` is **no longer a symlink into it** — the home cache and the scratch cache are
  now two independent trees, with the home one still holding the 8.9 MB stub.
- ⚠ **The reverse-direction lexical transfer (basket→button) was never run.** Only button→basket
  exists. Do not report a second direction.
- ⚠ **Do not quote §64.3's dissociation table without §69.2.** The two rows come from two different
  artifacts measuring two different instruments at two different sites, and at `L = 6` the
  "whole-query knockout" is arithmetically identical to blocking the codeword's own row. The log
  states both bounds; the risk is downstream quotation, not the log.

---

## Appendix — index of every preregistration in this window and its outcome

| PR | question | outcome |
|---|---|---|
| `PR-029` | extend the control population to K = 32 | ⛔ **never ran** — six arms executed the wrong script (`C-047`); zero results; halted, resumable |
| `PR-030` | is the between-control spread a real draw offset? | ✅ `R-077` **REAL DRAW OFFSET** — split-half ρ 0.988, 93.5 % |
| `PR-031`/`a`/`c`/`d` | is there a BOMB-specific readout of the codeword? | ⛔ **VOID** (`C-049`) — the `n_examples = 0` null control fired |
| `PR-032`/`PR-036` | the surgical row ladder K = 3…7 | ✅ `R-080`/`R-081` — `K* = 7`, `shape = STEP`; all three `PR-036` predictions confirmed |
| `PR-033` | installation gate at logit-lens L16 | ⛔ **VACUOUS** (`C-048`) — option mass ~1e-5 |
| `PR-034` | the gate re-specified on the forced-choice instrument | ⚠ `R-078` **PARTIAL** — gun not installed (4/6) |
| `PR-035` | the specificity primary, respecified | ✅ `R-086`/`R-089` **POSITIVE — concept-specific** (after an override and its retraction) |
| `PR-037`/`a` | is `K*` the codeword's row or the template's option word? | ⛔ `R-083` **CANNOT ANSWER**, by 1.9 points |
| `PR-038` | does the pathway carry the model's EXPLICIT reading? | ⛔ `R-088` **CANNOT ANSWER at its gate** — and the reason is the result |
| `PR-039` | the "corrected" permutation null | ⛔ **UNADOPTED** (`C-062`) — it changes a preregistered statistic, was proposed after seeing outcomes, and is irrelevant at 3 classes |
| `PR-040`/`a`/`b` | gate `R5` — does the knockout destroy the concept signal? | ⛔ `R-093` **`R5-FAIL`** — the signal survives; the dissociation |
| `PR-041` | gate `R3` as actually specified | ⛔ `R-092` **`R3-FAIL`** on accuracy; `C-066` corrects the interpretation |
| `PR-042` | gate `R8` — does destruction predict behaviour? | ⛔ `R-097` **CANNOT ANSWER** for two independent reasons |
| `PR-043` | the `PR-039` re-run, with what may be read fixed in advance | ✅ `R-094` — a **fifth** exact reproduction; ⛔ `C-067` — LOBO still uninterpretable |
| `PR-044` | gate `R6` and §13 on one arm set | ⛔ `R-095`/`C-068` — **uninformative by construction**; §13 at ceiling |
| `PR-045` | re-read `R6` and §13 above the degenerate layer | `R-096` — the scopes **do** separate (ratio 0.520); descriptive, no p-values |
