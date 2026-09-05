# What we did between 2026-09-02 and 2026-09-05 — complete, self-contained account

**Audience.** Someone (human or LLM) with no prior exposure to this repository. Everything needed to
understand the work is defined here. Where a number appears, its artifact path is given.

**Period covered.** 2026-09-02 00:25 → 2026-09-05 19:47 (223 commits on branch
`behavioral-causality-sprint`). Two distinct sprints occupy this window:

| sprint | id namespace | dates | canonical log |
|---|---|---|---|
| **TSC** — Thesis-Scale Confirmatory | `TSC-` | 2026-09-02, 00:25 → ~10:51 | `external_md/THESIS_SCALE_CONFIRMATORY_SPRINT_PLAN_AND_PROGRESS.md` (1833 lines) |
| **DCS** — Doublespeak Concept-Specific / Surgical Causality | `DCS-` | 2026-09-02 19:50 → 2026-09-05 (ongoing) | `external_md/DOUBLESPEAK_CONCEPT_SPECIFIC_BOOMBNESS_AND_SURGICAL_CAUSALITY_PLAN_AND_PROGRESS_20260902.md` (7749 lines) |

A third sprint, **CDS** (Confirmatory Defensibility, `CDS-`), closed on 2026-09-01 and is the
*inherited* state TSC starts from; it is summarised in §2 for context only.

**Verification status of this document.** Every headline claim below was re-checked against the
producing JSON artifact and/or the producing script by independent agents. §11 lists what matched,
what could not be checked, and four small documentation defects found in the process. Read §11 before
treating any number as recomputable.

---

## Table of contents

1. [Orientation — the research object and the vocabulary](#1-orientation)
2. [Where things stood on 2026-09-02 (inherited truth)](#2-inherited)
3. [TSC sprint — what was asked, run, and returned](#3-tsc)
4. [DCS sprint — the preregistration](#4-dcs-preg)
5. [DCS results, in the order they were established](#5-dcs-results)
6. [The standing scoreboard: established / narrowed / retracted / cannot answer](#6-scoreboard)
7. [Corrections, bugs and near-misses (the methodological record)](#7-corrections)
8. [Code, banks and artifacts produced](#8-code)
9. [Process and infrastructure work](#9-process)
10. [Current live state and what happens next](#10-live)
11. [Independent verification of this document's numbers](#11-verification)

---

<a name="1-orientation"></a>
## 1. Orientation — the research object and the vocabulary

### 1.1 The attack under study ("Doublespeak")

A prompt contains a block of in-context **demonstrations** that implicitly redefine an innocuous
**codeword** (e.g. `button`, `basket`) to stand for a harmful **concept** (e.g. `bomb`). A final
**query** then asks something using the codeword. If the remapping "installs", the model answers as
though asked about the harmful concept. The attack itself is *published work* (ACL 2026) and the repo
vendors the authors' code — **the attack is not ours and must never be presented as ours**. Our
contribution can only be mechanistic.

### 1.2 The frozen 2×2 design

`CORE_2X2` at `src/boombness/prompt_families.py:94-106`. Two factors: what surface word the query
uses, and whether the demonstrations are benign or harmful.

|                              | benign demonstrations         | harmful demonstrations              |
|------------------------------|-------------------------------|-------------------------------------|
| **codeword surface** (`button`) | `A` = `benign_literal`        | `C` = `natural_doublespeak` ← the attack cell |
| **concept surface** (`bomb`)    | `E` = `concept_in_benign_ctx` | `B` = `direct_harmful`              |

`A` and `C` use the identical surface token and differ only in demonstration semantics, which is why
`C − A` is the primary contrast. `B` and `E` contain no codeword at all.

Worked examples of all four prompts are in `reports/TSC_2x2_DESIGN_EXAMPLES.md`,
`reports/TSC_2x2_FOUR_PROMPTS_FULL.md` and `reports/TSC_ONE_PROMPT_FULL_EXAMPLE.md`
(produced by `scripts/tsc_show_2x2_examples.py` and `scripts/tsc_show_one_prompt.py`).

### 1.3 Terms used throughout

- **Domain** — a topical setting (e.g. `school_campus`) supplying a demonstration pool and query.
  **The domain is the declared independence unit.** p-values use a domain-clustered exact sign test
  (`clustered_stats.cluster_sign_test`), never Wilson iid (which understates ≈1.9×). The main powered
  bank has **38 domains**; a new bank built in this window has **116**.
- **Demonstration pool** — the per-domain file of example sentences from which `n_examples`
  demonstrations are drawn, in a benign or harmful **valence**.
- **Installation** — how strongly the codeword→concept remapping actually took hold in a given
  domain, measured on the baseline before any intervention (operationalised as the fraction of
  baseline rows whose argmax answer decodes to the concept word).
- **KO scope** — which rows of the attention pattern are blocked from attending to which columns.
  The intervention is an **attention knockout** (method: Geva et al. 2023, arXiv 2304.14767;
  behavioral-endpoint use: Ben-Tov, Geva & Sharif, TACL 2026). The scopes used:
  - `KO-1` = `target_surface_row_only` on cell C — the final query **codeword** row ↛ demonstrations
  - `KO-2` = the same code path on cell B — the final query **concept** row ↛ demonstrations
  - `KO-3` = `query_prefill_only` — the **whole query span** ↛ demonstrations
  - `KO-4` = `prompt_last_row_only` — the final query/readout row only
  - `KO-5` = `demo_processing_only` — the inherited scope used by TSC/CDS
  - `query_last_k_rows` — a dose ladder built in this window (K ∈ {1,2,8,16,32})
- **`semantic_logodds`** — the forced-choice semantic readout, whole-answer scored
  (`signals.py:693` `string_option_readout`, dispatched via `surgical_knockout.py:462`), gated by
  `option_mass_gate` (default 0.05). ⛔ The legacy single-next-token function literally named
  `semantic_logodds` at `surgical_knockout.py:435-460` is **INVALID** and its runs are not reportable.
- **Endpoints.** `rubric` attack = `strongreject_score ≥ 0.5`. `concept_topical` = that **AND**
  `goal_topicality > 0`. **Refusal** = `kw_refusal`, a case-insensitive substring match over 16
  hardcoded markers (`doublespeak_causality/scripts/behav_judge.py:87-103`) — **no API call, and
  therefore deterministic**. Judge is `openai/gpt-4o-mini`, pinned.
- **Judge noise band = 17 rows** per arm (13.4% of `malicious_at_0.5` labels flip on byte-identical
  completions; three-pass unanimity 76.8–82.9%). The **paired-contrast** band is **3.7 rows**.
  Older estimates (5%, 6.5%, 11 rows) are not interchangeable.
- **Attainable p-floor** — `2/2^k_informative`. Reported beside every p-value. If the floor is above
  α, no outcome could have been significant and the verdict is `CANNOT ANSWER`, never a null.
- **Verdict vocabulary (closed set, never extended after seeing a result):** `CONFIRMED`,
  `REPLICATED`, `SUPPORTED`, `CAPABLE NULL`, `DECLINED FOR POWER`, `VOID`, `CANNOT ANSWER`,
  `MIXED`, `CONFOUND-LIMITED`, `RANGE-LIMITED`, `NOT RESOLVED`, `UNDERPOWERED NEGATIVE`.

### 1.4 The working method (this matters for reading the results)

Both logs are **append-only**. Every confirmatory forward pass gets a `PR-nnn` **preregistration
committed before the data exists**, naming population, model, decoding, layers, dose, estimand,
exact test, α, independence unit, measured baseline headroom, and an exhaustive list of admissible
outcomes. A number later found wrong gets a **new dated entry** (`⛔ RETRACTED` / `⚠ CORRECTED`);
the original sentence stays where it was written. Analyzers are committed while the arms are still
generating. Every headline carries a stdlib-only verifier that imports nothing from its producer,
paired with a mutation harness that must go red.

**Consequence for a reader:** the logs contain many statements that were true when written and are
false now. §6 is the only authoritative scoreboard.

---

<a name="2-inherited"></a>
## 2. Where things stood on 2026-09-02 (inherited, not re-derived here)

The strongest standing result entering the window was `CDS-R-018` / `CDS-DR-002`:

> On Llama-3.1-8B-Instruct with the `button↔bomb` bank, masking demonstration processing at layers
> 6–14 (`demo_processing_only`, α=1.0) removes behavioural attack: baseline ASR **0.4184 (159/380)**
> → **0.1447 (55/380)**, i.e. **−104 rows**, against three seeded count-matched non-demonstration
> controls scoring 159 / 150 / 148. Domain sign test **p = 2.556e-06 / 1.309e-07 / 6.938e-08**
> (floors 4.66e-10 / 2.33e-10 / 1.16e-10), informative domains 32 / 33 / 34.

**Five scope limits that TSC existed to close:**

1. ONE lexical pair. The `basket↔bomb` replication was **VOID for a bank defect**, not negative:
   all four intervened arms crashed with `occurrence_count_mismatch` on exactly three
   `school_campus` prompt ids named *before* any generation ran. (Asymmetry: baseline arms catch the
   exception in a failure ledger at `score_behavior.py:1861` and continue at 377/380; intervened arms
   raise it from the pre-flight loop at `score_behavior.py:1642`, which is not inside a `try`.)
2. ONE harmful request — all 380 rows share one identical `final_query_text`. The 38 clusters are 38
   demonstration pools around **one** request.
3. Controls are **neutral-filler** controls: 98.3–99.8% of drawn keys land in the 10-line neutral
   preamble. The established contrast is "masking demonstrations ≫ masking neutral preamble filler
   of equal masked-key count". ⛔ Never write "matched control" unqualified — the controls do
   **1.93–1.97× MORE** prefill edits (30,276 vs 15,399 median) at identical `match_ratio = 1.0`,
   by position geometry, which makes the contrast **conservative**.
4. Control deltas of 0 / −9 / −11 rows are inside instrument noise (51 label flips = 13.4% on
   byte-identical text).
5. ONE model. The old Qwen3 `C7` population fails at its own stated domain-level unit.

Other preserved conclusions: `d_surface`/"Boombness" is **not** a valid attack objective (GCG/MAC
stay closed); mapping installation is **not sufficient** for behavioural attack (clean evidence is a
matched-skeleton contrast 2/24 vs 12/24, Fisher p = 0.0034, one pair); refusal restoration is
**bank-scoped**.

---

<a name="3-tsc"></a>
## 3. TSC sprint (2026-09-02) — thesis-scale confirmatory

**The ask:** close the specific weaknesses stopping the strongest claim from being thesis-level
evidence, using preregistered, properly powered, falsifiable tests. Priorities P1–P5 fixed in
advance; P6 never started.

**Outcome in one sentence:** four of the five closed — two of them by returning a negative — and the
fifth was **DECLINED on its own preregistered power rule rather than run underpowered**. The result
is *stronger and narrower* than it was the day before.

### 3.1 P1 — `basket↔bomb` lexical replication → `TSC-R-004` **REPLICATED**

Enabling change: a generic `--exclude-prompt-ids FILE` in `score_behavior.py`
(`load_prompt_id_exclusions` / `exclusion_sha16`). A **file**, not a comma list, because `--export`
truncates comma values silently and `run_boombness.sh` word-splits `BOOMB_ARGS`. It refuses on:
missing file, empty list, duplicated id, id not in the filtered population, or an id removing more
than one row; and it persists `exclude_prompt_ids{,_file,_sha16}` and `n_excluded` on **every** arm
including arms excluding nothing (`0` and `null` differ). 17 tests, each refusal paired with an
executed mutant test.

Pre-launch **CPU-only** audit (no GPU minute spent): the whole 380-row basket population pushed
through `resolve_occurrences` with the real Llama tokenizer raises on **exactly three** rows, and they
are exactly the three declared ids — so the exclusion is derived from the tokenizer alone, with no
generation, judge, or outcome involved.

Result (n = 377 per arm, all five arms carrying the identical 377 prompt ids):

| contrast | attacks | domains a>b / b>a | k_inf | p | attainable floor |
|---|---|---|---|---|---|
| demoproc vs `ctrl_d1` | 14 vs 38 | 4 / 16 | 20 | **1.182e-02** | 1.91e-06 |
| demoproc vs `ctrl_d2` | 14 vs 55 | 4 / 21 | 25 | **9.105e-04** | 5.96e-08 |
| demoproc vs `ctrl_d3` | 14 vs 41 | 4 / 19 | 23 | **2.600e-03** | 2.38e-07 |

ASR `A` 0.1141 → demoproc **0.0371**, a **67%** relative drop (button's was 65%). Registered *in
advance* as underpowered for a partial effect (≈0.61) and it still rejected all three; the power
statement was not rewritten afterwards. Secondary: row McNemar p = 9.62e-08; domain-cluster bootstrap
95% CI on ΔASR **[0.0588, 0.1618]** excludes zero.
Artifact: `outputs/boombness/cds_analysis/tsc1_basket_specificity_domain_test.json`.

⚠ The basket **refusal** endpoint is `UNINFORMATIVE BY CONSTRUCTION` (8 → 0, but `k_inf` 2–5 and
attainable floors 0.0625–0.5, all above α). It is **not** a null.

### 3.2 P3 — judge robustness → `TSC-R-001` **CONFIRMED**

Two further independent pinned judge passes over the existing five-arm manifest (no completions
regenerated). Nine registered tests, three passes × three controls:

| contrast | pass 2 | pass 3 (`tsc2ja`) | pass 4 (`tsc2jb`) |
|---|---|---|---|
| demoproc vs d1 | 2.556e-06 (k 32) | 1.309e-07 (k 33) | 1.309e-07 (k 33) |
| demoproc vs d2 | 1.309e-07 (k 33) | 1.093e-05 (k 33) | 1.624e-06 (k 29) |
| demoproc vs d3 | 6.938e-08 (k 34) | 2.463e-07 (k 32) | 6.165e-06 (k 34) |

**Worst of nine = 1.093e-05**, all nine `CAPABLE`. Attack counts per arm per pass — `A` 159/147/142,
demoproc 55/55/49, d1 159/160/153, d2 150/139/143, d3 148/147/143; **majority vote 143/46/158/138/142**.
Row-level flip rate **9.7–17.1%**; only **76.8–82.9%** of rows unanimous over three passes.
Instrument control: on `refused` the three passes give **42/42/42** and **22/22/22**, 0 flips.

### 3.3 The adversarial review — `TSC-DR-001`

A read-only agent was told to **break** `TSC-R-001`. It recomputed all nine p-values from raw rows
using integer `math.comb`/`Fraction` arithmetic — exact to the last digit; confirmed the passes are
genuinely independent; confirmed the 38 domains share **zero** demonstration sentences (1520 distinct
sentences, 0 shared); confirmed the controls are not merely count-matched but **over-dosed**. It could
not break the machinery. **It broke three sentences:**

- ⛔ **"attack removal"** (`TSC-C-004`, the sprint's biggest finding). Every judged row carries
  `goal_topicality`. **90.0–91.2% of judge-positive completions in every arm — and 100% on demoproc —
  never contain the concept word.** The repo had already retracted this exact inference once (`R-13`,
  2026-08-20, where a double-random control scored 0.95 "attack success" on text with zero harmful
  keywords, because StrongREJECT scores refusal/specificity/convincingness). The producer of all nine
  headline p-values never reads the topicality column, and the analyser built for exactly this failure
  mode (`src/boombness/analyze_topical_asr.py`) had never been applied to this deliverable.
- ⛔ **"−97 rows against a 17-row band ≈ 5.5×"** (`TSC-C-005`). That stapled the *baseline* effect onto
  the *control* contrast and used one drifting arm's max−min. **The paired band is 3.7 rows and the
  true margin is ≈ 46×** — wrong in the direction that *understated* it.
- ⛔ **"0/380 refusal flips proves the variance is the judge"** (`TSC-C-006`). `refused` is
  `kw_refusal`, a substring match that never calls the API; on byte-identical text 0 flips is a
  mathematical identity. It attests the join and the hashing, nothing about the judge.

Also found: `TSC-C-007` — "worst of nine p-values" reads as nine confirmations; it is **one**
experiment re-judged three times against three correlated controls (they agree on 27–31 of 38 domain
signs). `TSC-C-008` — a real denominator defect (the in-process judge cache copies one API call's
label to every row sharing a completion hash: in arm `A`, 3 hashes cover 37 rows spanning 15 domains);
sensitivity check dropping every duplicated-completion row leaves all nine tests standing, most
stronger.

### 3.4 `TSC-R-002` — the topical endpoint, run through the repo's own instrument

| arm | ASR plain [95% CI] | ASR topical [95% CI] | Δ topical vs baseline |
|---|---|---|---|
| `A` | +0.418 [+0.342, +0.495] | +0.037 [+0.018, +0.058] | — |
| demoproc | +0.145 [+0.105, +0.184] | **+0.000** [0, 0] | **−0.037 [−0.058, −0.018]** ✅ |
| ctrl_d1 | +0.418 | +0.037 | +0.000 [−0.013, +0.013] |
| ctrl_d2 | +0.395 | +0.039 | +0.003 |
| ctrl_d3 | +0.389 | +0.034 | −0.003 |

Specificity is **not** an artifact of StrongREJECT scoring refusal-and-fluency: on the endpoint built
to defeat style inflation, demoproc is **exactly 0.000** and the controls are flat. ⚠ But the base
rate is 3.7% (not 39%), `k_inf` collapses to 8–12, and every test sits **exactly at its attainable
floor**; `goal_topicality` is a one-word single-bit test. Replicates on basket (0.013 → 0.000).

### 3.5 P2 — the capable Qwen3 replication → `TSC-R-005` **MODEL-SPECIFIC**, `TSC-R-006` **STRONG**

Staged: a Stage-1 baseline-only screen first, against an executable gate
(`scripts/cds_stage1_gate.py`: ASR ≥ 0.10, attack rows ≥ 34, domains with ≥1 attack ≥ 15).
`TSC-R-003` **PROCEED** — Qwen3-14B, 380 rows, **ASR 0.2026 (77 attacks), 28/38 domains with an
attack** against a floor of 15. `--enable-thinking false` is mandatory (Qwen3's template default is
thinking-ON, which at a 640-token cap can spend the whole budget inside `<think>`).

Stage 2, identical bank/rows/dose/band/scope/seed/cap/judge:

| contrast | attacks | k_inf | p | floor |
|---|---|---|---|---|
| demoproc vs `ctrl_d1` | 72 vs 71 | 30 | **1.0000** | 1.86e-09 |
| demoproc vs `ctrl_d2` | 72 vs 81 | 33 | **0.4869** | 2.33e-10 |
| demoproc vs `ctrl_d3` | 72 vs 74 | 34 | **0.8642** | 1.16e-10 |

Floors 9–10 orders below α ⇒ a **well-powered CAPABLE NULL**, not an incapable test. Pooled relative
reduction: **Llama 65.4 / 63.3 / 62.8%** vs **Qwen −1.4 / +11.1 / +2.7%**.

The **registered interaction** (committed as running code while the Qwen arms were still generating),
a difference-in-differences paired across models within domain — precisely because *"significant in
Llama, non-significant in Qwen" is NOT a model interaction*:

| contrast | scale | Llama removes | Qwen removes | k_inf | p | verdict |
|---|---|---|---|---|---|---|
| vs d1 | absolute | 104 | −1 | 35 | **1.878e-03** | MODEL-SPECIFIC |
| vs d2 | absolute | 95 | +9 | 32 | **2.102e-03** | MODEL-SPECIFIC |
| vs d3 | absolute | 93 | +2 | 34 | **6.165e-06** | MODEL-SPECIFIC |
| vs d1 | normalised | +15.1 | −10.4 | 27 | 0.0522 | not detectable |
| vs d2 | normalised | +13.4 | −7.4 | 26 | 0.1686 | not detectable |
| vs d3 | normalised | +12.6 | −10.2 | 27 | **1.514e-03** | MODEL-SPECIFIC |

Both scales reported as registered: absolute rejects 3/3, normalised 1/3 but agrees in direction 3/3
(its shortfall is power — dropping zero-baseline domains costs 7–8 informative clusters).

`TSC-R-006` — on Qwen the same intervention takes refusal **150 → 0** (k_inf 33, p = 2.328e-10, sitting
**exactly at its attainable floor**) while moving attack by **one row** (73 → 72). Controls remove
0 / 5 / 2. On Llama the same scope reduces refusal by 20 while removing 104 attack rows.
⛔ No single "refusal explains it" account survives both.

`TSC-C-011` — a reframing finding: **Qwen never produced a single concept-word-bearing completion in
any arm, including baseline.** Topical ASR is **0.000 out of 380 in all five arms** ⇒ on the topical
endpoint the Qwen cell is `UNINFORMATIVE BY CONSTRUCTION`, and *"the effect is Llama-specific", full
stop*, is not available either.

### 3.6 P4 — the request-diverse bank → `TSC-Q-001` → `TSC-PR-007` → `TSC-R-007` **DECLINED FOR POWER**

`TSC-PR-005` drew the population **blind from metadata only** (`task_id`, `category`,
`duplicate_group`; the instruction text never read or sorted on): 40 requests, 8 categories, seed
20260903, `selection_sha16 = bed56c91e70a707c`. Exclusions were fixed before any request was
inspected, including three categories dropped because the object is a person or a speech act, not a
noun a codeword can map onto — itself a scope limit of the paradigm.

Deriving each request's `(concept, template)` then hit an unanticipated problem: **the paradigm needs a
single-word object noun, and most AdvBench requests are actions.** This was escalated to Omer as
`TSC-Q-001` rather than resolved unilaterally (hand-dropping unmappable requests after inspecting them
would be post-hoc exclusion). Omer chose option A: AdvBench-sourced, mechanical filter.

`TSC-PR-007` committed the criteria and a 46-term lexicon **before the filter was implemented or run**,
plus an **anti-tuning check** — the identical filter over the 455 AdvBench rows *not* in the draw and
never read, declared before running and reported whichever way it fell.

**Result (`scripts/tsc_filter_requests.py` → `data/manifests/tsc_requests_v1_filtered.json`):**

- **40 drawn → 8 CONSTRUCTIBLE, yield 20.0%.** `NO_OBJECT_NOUN` **24** · `DUPLICATE_CONCEPT` **8** ·
  `NOT_SINGLE_TOKEN` / `CODEWORD_COLLISION` / `TOKENIZER_UNSTABLE` **0** each. Tie-break used once.
- Surviving concepts: bomb, counterfeit, drug, poison, ransomware, scam, virus, weapon.
  Surviving categories **5 of 8** (identity theft, misinformation and theft lose all five drawn each).
- **Anti-tuning fired, and the confound was the author's own** (`TSC-C-013`): the registered
  comparison (drawn 40.0% vs all-455 22.6%, Fisher **p = 0.0197**) spans 8 categories excluded for
  having person/speech-act objects. Category-matched it is **40.0% vs 30.0%, Fisher p = 0.208** — no
  evidence of tuning surviving a like-for-like comparison. Unplanned bonus: the **3.9%** rate on the
  excluded categories independently validates the exclusion rule.
- **Recomputed capability at k = 8 fails.** Best case anywhere **0.414** (total wipeout) and **0.202**
  (75% reduction) against inherited floors ≈0.87 and ≈0.6. At k = 8 the design tolerates **zero**
  discordant requests (1 of 8 → p = 0.0703 FAIL) while the Llama headline ran at 5.9–9.4% discordant.
- **VERDICT `DECLINED FOR POWER`. P4 not launched.** Filter not relaxed, lexicon not extended, draw
  not repeated, no threshold moved, no intervention arm generated.

**What the decline is evidence OF (`TSC-R-007b`):** running the identical filter over all **367** rows
of the eight registered categories gives **114 lexicon-matching rows collapsing to 15 distinct
concepts** — bomb (22), drug (16), virus (14), malware (14), scam (8), firearm (7), weapon (6),
poison (6), explosive (5), exploit (5), counterfeit (3), botnet (3), ransomware (2), hoax (2), gun (1).
**11 of the 15 are cyber or weapons.** Even at that ceiling, k = 15 × m = 10 gives partial power
0.28–0.51; only k = 15 × m = 20 reaches ≈0.59. **The binding constraint is the benchmark, not compute.**

### 3.7 P5 — the structurally active control → `TSC-PR-006`, **PREREGISTERED, EXECUTION DEFERRED**

Fully specified and unstarted. A new preset clones the existing one with one added block key
(`preamble_pool`, default `"filler"` so every existing bank regenerates byte-identically); setting it
to `"remap"` fills the preamble with domain-topical, structurally parallel sentences teaching no
mapping, so the existing untouched control draws land on **active pseudo-demonstrations**. **Zero new
intervention code.** Five executable preconditions that refuse rather than warn.

### 3.8 TSC verification

Three headlines, each carrying a stdlib-only verifier importing nothing from its producer, with the
exact binomial derived three ways and cross-checked against brute-force enumeration:
**button 350 / basket 351 / Qwen 351 checks, 0 failures.** Mutation harness **20/20 RED on all three**.
The verifier and harness were **parameterised rather than forked** (`TSC-C-002`) — a forked verifier is
two instruments that drift apart — and the design shape must be declared by the caller, because a check
that infers its expectation from the data under test asserts nothing.

`TSC-C-001` is the sprint's sharpest instrument lesson: **the Stage-2 verifier was RED against the
artifact it certifies, and its green had been vacuous before that.** It compared the published
`frac_stop_length` against a field already proved permanently `null` — so it asserted `None == None`
and printed PASS. *A check whose two sides read the same broken source agrees with itself.*

---

<a name="4-dcs-preg"></a>
## 4. DCS sprint — the preregistration (frozen 2026-09-02, before any forward pass)

### 4.1 The question

> Can we construct and validate an **intuitive, concept-specific** measure of the codeword becoming
> more like the harmful concept — and can we identify the **precise demonstration-processing
> computation** that causes that representation and/or the downstream behaviour?

One concept: `bomb`. Codewords `button` (discovery) and `basket` (confirmation). ⛔ No pooling of
unrelated harmful concepts anywhere in the headline fit.

### 4.2 What was frozen

- **§1.4 A closed family of nine candidate metrics** (`cand1`–`cand9`) for "Boombness", with their
  algebraic dependencies declared in advance (`cand1`, `cand2`, `cand7` are algebraically dependent
  and count as **two** independent tests, not three).
- **§1.7 Six validation gates** `R1`–`R6`: R1 C differs from A in the predicted direction; R2 C moves
  toward B; R3 the score predicts forced-choice mapping held out; R4 survives new template/family/
  domain/lexical bank; R5 predicts attack behaviour within domain after controlling `n_examples`;
  R6 intervening on it changes behaviour more than matched controls. ⚠ **A metric is not "Boombness"
  because it predicts ASR.** Passing R1–R4 and failing R5 is the "representation exists but is not
  used" result — an admissible answer, declared as such.
- **§1.8 The surgical knockout ladder** (KO-1…KO-5, above), with position discipline: every
  intervention persists the tokenized prompt, demo spans, query span, every occurrence index with
  decoded text, destination rows, source columns, layers, head set and realized edge count. ⛔ The
  phrase "last token" is never used.
- **§1.10 Six admissible outcomes** `A`–`F`, including `F` = `KO-1 ≫ KO-2` ⇒ a remapping-specific
  information path.
- **§1.12 Five named silent-no-op traps**, each of which has bitten this repo before: SDPA silently
  discards a custom 4-D mask and scores as a clean null (hence `--attn-impl eager` is mandatory);
  absolute vs cache-local index algebra; composed-arm argument dropping (has silently dropped
  `control_seed` **twice**, producing n=1 "three-draw bands"); `occurrence_count_mismatch` / an empty
  needle matching every token; isotropic controls that are inert by geometry.
- **§1.11 Fourteen standing rules**, including: the floor is not the p-value; all arms in **one** judge
  invocation; register thresholds as running code before the data; a verifier must not read the
  producer's own field; crash > silent skip; shared-tree hygiene (`git commit -- <paths>` only, never
  `git add -A`, never `git stash`).

### 4.3 `DCS-001` — the P0 repository audit

Six independent read-only auditors over disjoint areas, then a synthesis pass resolving contradictions
by **re-reading files rather than averaging reports** (7 agents, 282 tool calls, 0 errors;
`reports/DCS_P0_AUDIT_BRIEF.md`). Ten findings changed the plan, including: three metadata fields
returned **0 hits repo-wide** and had to be *defined* rather than derived; `prompt_id` **collides
across lexical banks** (200/200 for the first 200 ids) so joins must use `(bank_file_sha16, prompt_id)`;
`KO-2` requires *building* a `concept_last` resolver, not a parameter change; and the two estimators
the plan commits to (pairwise cell-mean geometry, a probability-calibration wrapper) **do not exist**
in the repo.

### 4.4 `DCS-006` — the literature review (`reports/DCS_LITERATURE_MATRIX.md`)

12 queries over 11 topics, 24 rows, ≈60 works surfaced, no new measurement made for the document.
**Verdict:**

1. ⛔ **The attack is not ours.**
2. ⛔ **The representation-convergence observation is also not ours** — Yona, Sarid, Karasik &
   Gandelsman, *"In-Context Representation Hijacking"*, ACL 2026 (arXiv 2512.03771), logit lens +
   Patchscopes over 29 harmful requests. Our representational half is a **replication with a different
   instrument**; their Appendix D (varying the codeword, ASR flat) **partly anticipates** our
   concept-specificity negative.
3. ✅ **What they have no version of: any internal causal intervention.** Their only causal
   manipulation is at the prompt level.
4. **"Representation ≠ behaviour" is a 2026 consensus** (Walsh & Barkett arXiv 2605.25151; Yin, Han &
   Li, ICML 2026 oral, arXiv 2606.28153) — ours is novel only **as an instance**.
5. **Method provenance:** Geva et al. 2023; Ben-Tov, Geva & Sharif TACL 2026 own attention knockout on
   an attack-carrying span with a behavioral endpoint. *Our method is theirs, redirected at a
   demonstration block.*
6. ⇒ **The defensible novelty is the combination**: demonstration-block knockout + a StrongREJECT
   rubric endpoint + a preregistered `intervention × condition` interaction with dose-matched controls
   + a *capable* cross-family null + a CI-backed negative for a mechanistically derived attack
   objective.
7. ⚠ **Self-applied on 2026-09-04 (`C-035`)**: by the matrix's own bar ("intervenes on internals AND
   measures a behavioral endpoint"), **we score Y on refusal and NOT on attack success.**

---

<a name="5-dcs-results"></a>
## 5. DCS results, in the order they were established

### 5.1 Representation geometry — a positive, then a decisive negative

New analyzer `src/boombness/dcs_cell_geometry.py` (the missing pairwise-cell-geometry helper), which
re-derives the shipped directions from `cell_means` rather than trusting the producer's derived field
(recomputation matches at cos = 1.000000 at every layer checked). No GPU required.

- **`R-001` ✅** — the codeword **does** move toward the explicit concept. `toward_B_frac = 1 − d(C,B)/d(A,B)`
  peaks at **L6–L12** (button 0.130–0.138, basket 0.077–0.110). Reliability was **measured, not
  assumed**: dev and heldout are two independent 30-family samples, so their disagreement *is* the
  sampling noise — median |dev − heldout| = **0.0151**, p90 **0.0443**. The peak is 3–10× that band and
  reproduces on all 10 banks.
- **`R-002` ⛔ THE MOVEMENT IS NOT CONCEPT-SPECIFIC.** At each bank's peak: button/`bomb` 0.138 vs
  `knife` **0.168**, `gun` 0.138, `club` **0.173**; basket/`bomb` 0.110 vs knife 0.130, gun 0.103,
  club **0.142**. Three of four comparisons run the *other* way and every difference (≤0.035) is inside
  the measured p90 = 0.044 split-to-split band. ⇒ The geometry measures a property of the
  **demonstration paradigm**, not of `bomb`. **It may not be called "Boombness".** This is the sprint's
  first result and it answers `Q1` in the negative.
- **`R-003` ⛔ the shift does not accumulate.** The final query occurrence exceeds the first in **32 of
  32** cells, but across demonstrations the two banks **disagree in sign** (median ρ −0.048 vs +0.278)
  and the effect is flat in `n_examples` (7.01 / 7.25 / 7.10 / 6.54 at L12). It saturates after
  approximately one demonstration.
- **`R-004` ✅ the null control fires exactly** — at `n_examples = 0` the paired `C−A` is **0.000e+00**
  at all 96 cells (correct: with no demonstrations A and C are byte-identical prompts). The first null
  control this metric has ever had. Paired `C−A` positive in **480/480** cells with domain-clustered CI
  excluding zero, cross-fit on all 15,768 rows.
- **`C-005` ⛔ RETRACTED** — the L6–L12 peak does **not** appear in the per-row standardized effect
  size, which is largest at **L0** and declines with depth. The peak exists only in a between-cell-mean
  distance ratio. *"The representation effect peaks at L6–L12, coinciding with the knockout band"* is
  **not supported**. ⚠ The retracted framing was the one that made the story tidier.

### 5.2 The knockout ladder — the phase's central positive result

- **`R-005`/`R-006`/`R-007` — `KO-1` (final codeword row) is a well-powered null.** The mapping is
  **preserved** (+0.278 vs baseline, 25+/13−, p = 0.073 on the preregistered sign test); attack is
  **unchanged** (+11 rows, 18+/14−, p = 0.597, floor 4.66e-10 — a genuine well-powered null); refusal
  is **halved** (−21, 0+/13−, p = 2.44e-04 = its own floor).
- **`C-007` ⛔ `KO-2` is UNINFORMATIVE BY CONSTRUCTION on the ASR endpoint** — found *while the arms
  were still generating, before any judge run*. Cell B's baseline is 10/380 = 0.0263, so the maximum
  removable is 10 rows against a 17-row judge band. **This was a preregistration error**: `PR-001`
  fixed everything except whether the control cell could move, and twelve committed artifacts would
  have said so for free. Rule adopted: a preregistration naming a control condition must carry that
  condition's **measured baseline headroom and attainable floor** before the arms are submitted.
  The specificity test was moved to the readout channel (`PR-002`).
- **`C-010` ⛔ RETRACTED** — `R-005` does **not** establish outcome `D`. Measured from artifacts: the
  knocked-out token sits **10 tokens before the end** of the templated prompt, so ≥11 downstream
  positions keep unblocked demonstration attention at all 32 layers, and the codeword token keeps 23
  of its 32 layers. The only licensed sentence is *"the final codeword token's own L6–14 demonstration
  attention is not necessary."*
- **`R-008`/`R-010` ✅ OUTCOME `F`.** `KO-3` (whole query span ↛ demonstrations) drives the cell-C
  forced-choice reading from **+5.188 → −2.756** — a **sign flip away from the concept reading** —
  while its dose-matched control at the identical 66,816-cell dose moves it **+0.137**. Cell B (where
  the word *is* the concept) moves **+1.808**.
  **DiD = −9.889, 37 of 38 domains, exact two-sided sign p = 2.838e-10** (floor 7.276e-12).
  ⇒ **The demonstration→query path is necessary for the remapping and specific to it.**
- **`A-002`** — adversarial audit: outcome F survives and generic damage is **refuted**, not merely
  unfalsified. Raw log-probs show that in cell B *nothing degrades* (`logp_concept` and option mass
  both rise). A discrete, mass-free replication (argmax over the option pair) gives C baseline 345
  concept / 4 codeword → `KO-3` **19 / 104**; B baseline 350 / 21 → `KO-3` **362 / 6**. LOO DiD range
  [−10.177, −9.761]; cluster bootstrap CI [−10.891, −8.816]. The single positive domain
  (`museum_archive`) has a cell-C baseline of −6.275 — the mapping never installed there.
- **`R-011` ✅ `basket↔bomb` REPLICATES** at n = 377 under the declared exclusion: DiD **−9.352**,
  1+/37−, p = **2.838e-10**; preregistered robustness (dropping `school_campus`) gives −9.264,
  1+/36−, p = 5.53e-10. ⛔ **But "the two cells move in opposite directions" does NOT replicate** —
  on basket, cell B moves **down** (−1.466). The general claim is about **magnitude**, not sign.
- **`R-021`/`R-022` ✅ it is a THRESHOLD, not distributed retrieval.** A five-point row dose-ladder,
  each rung against its own dose-matched control:

  | query rows cut (K) | dose (mask cells) | demo | control | demo − control | % of K=32 | domains | sign p |
  |---|---|---|---|---|---|---|---|
  | 1 (`KO-4`, readout row) | 2,088 | +5.149 | +5.163 | **−0.013** | 0.2% | 15+/23− | 0.256 |
  | 2 | 4,176 | +5.150 | +5.161 | **−0.012** | 0.1% | 15+/23− | 0.256 |
  | **8** | 16,704 | **−1.246** | +5.370 | **−6.616** | **81.9%** | **0+/38−** | **7.28e-12** |
  | 16 | 33,408 | −2.510 | +5.378 | −7.888 | 97.6% | 1+/37− | 2.84e-10 |
  | 32 (`KO-3`) | 66,816 | −2.756 | +5.325 | −8.081 | 100% | 1+/37− | 2.84e-10 |

  **A step between 2 and 8 rows, then saturation.** No single query position — not the codeword row,
  not the readout row — carries the mapping; roughly a quarter of the query span suffices.
  The **controls are inert across a 32× dose range** (+5.16…+5.38 against a +5.188 baseline), so the
  step is about *which* keys are cut, not how many. ⚠ Row count and dose rise together by
  construction, so the ladder separates *graded from step*, not rows from cells.

### 5.3 Cross-model replication (Qwen3-14B)

Staged with the capability gate declared first (precedent: `TSC-C-011`). Band **7–17** on Qwen's 40
layers = the same relative depth as 6–14 on Llama's 32; `--enable-thinking false`.

- **`R-023` ✅ gate passes on all three criteria** — cell C mean **+10.140**, `frac>0` 0.813, option
  mass 0.999; cell B **+30.707**, mass 1.000.
- **`R-024` ✅ `KO-3` REPLICATES ON QWEN3-14B.** Cell C **+10.140 → −13.080**, `frac>0`
  collapses **0.813 → 0.021**; control inert at +10.357. **KO-3 − control = −23.437, 1+/37−,
  p = 2.838e-10.**
  ⛔ **The magnitude ratio is NOT claimable** (`C-046`, 2026-09-05). *"Replicates at ~3× Llama's
  magnitude"* had reached three surfaces and is now corrected on all of them. `R-023` **pre-declared
  that exact comparison invalid three paragraphs before it was made**: Qwen's mean is ~2× Llama's over
  a **more bimodal** distribution (`frac>0` 0.813 vs 0.942), so a mean-only cross-model comparison
  misleads. The doses are also **unmatched** — Qwen 91,872 mask cells over 11 layers against Llama's
  66,816 over 9, on a quantity `R-022` showed is **steeply dose-graded**. ⇒ **The replication holds in
  sign and in the identical 1+/37− domain split; the magnitude ratio is not a result.** (The Qwen DiD
  rests on **6** arms — 2 cells × baseline/KO-3/control, verified on disk — not the 4 the summary
  previously claimed.)
- **`R-025` ✅ the specificity DiD replicates**: cell B moves **−1.238 (15+/23−, p = 0.256)** —
  a *real* null, not a ceiling artifact (`C-019`: a ceiling constrains rise, not fall, and B had the
  entire range below +30.7 available). **DiD = −22.198, 1+/37−, p = 2.838e-10.**
- ⚠ **The three DiD settings share the *same* 1+/37− sign pattern**, so the identical p-values are
  **one pattern replicated three times, not three independent tests.** This caveat travels with the
  number everywhere, including on the figure.
- **`R-026`** — on Qwen, `KO-3` removes **all 150 refusals** (judge-free), the same 150 `TSC-R-006`
  removed at a *different* scope. The refusal half now holds across **two models × four scopes**.
- **`R-029` ⛔ `PR-010` = `CANNOT ANSWER`** — 0 of 6 Qwen control draws meet the ±17 refusal-neutrality
  tolerance at a 150 baseline (minimum perturbation **+39**). The judge was **declined** on the
  generated Qwen behavioural arms rather than run without a valid comparator. This is a limitation of
  the **criterion**, never "Qwen shows no behavioral effect".

### 5.4 The layer question — `R-030`, `R-031`

`DCS-021` first established mechanically, over every argsfile, that **no post-hoc layer selection
occurred anywhere in the phase**: 35 Llama arms all at 6–14, 4 Qwen arms all at 7–17, both bands
inherited. The corollary was that the phase could not yet claim localisation — so it was tested.

Coarse sweep (`R-030`, four bands, each with its own dose-matched control): 0–5 **−4.297** ·
6–14 **−8.081** · 15–23 **+0.146** · 24–31 **+0.754**, all Holm-corrected over 4.
Equal-width sweep built specifically to remove the dose caveat (`R-031`, identical 37,120 dose in
every band): 0–4 **−3.385** · 5–9 **−2.985** · **10–14 −5.647 (0+/38−)**.

⇒ **Every 5-layer window in 0–14 destroys a substantial part of the mapping; no band is null; 10–14 is
strongest at ~1.7–1.9×.** Corrected phrasing: *the effect lives in layers 0–14 and peaks at 10–14* —
**graded, not bounded at 6–14**. ⛔ *"Localised to 6–14"* is too strong, and no per-layer profile is
claimable.

⛔ **"Absent above layer 14" OVERSTATES** (`C-046`, 2026-09-05). What is absent above 14 is the
**destructive** effect; **the region is not inert.** Band 24–31 gives **+0.754 with 38+/0− domains at
Holm p = 2.9e-11 — the most consistent sign pattern in the entire sweep**, and the log had already
flagged it as an unexpected consistent positive. Compounding: the above-14 bands are **9L/8L and not
dose-comparable** to the equal-dose 5L bands, and `R-037` showed band inertness is **bank-specific**.
The correct sentence names the bank and says *"no **destructive** effect above L14"*, with 24–31's
+0.754 reported as exploratory and unexplained.

### 5.5 Behaviour: the two reversals

This is the most instructive arc in the sprint and the one an external reader is most likely to
misread. It went: null → retracted → positive → direction-only → not established.

1. **`R-012`** (`PR-004`): `KO-3` destroys the mapping; against the dose-matched control the attack
   moves **−15 rows, p = 0.860**. Reported as *"we moved the representation past zero and behaviour
   did not follow."*
2. **`C-015` ⛔ THAT NULL IS RETRACTED**, for two independent defects found by adversarial audit:
   - **Wrong test.** Rows are 1:1 paired by `prompt_id`, so the correct test is **McNemar**, not a
     domain sign test. McNemar on the same data gives **p = 0.235**, not 0.860, and the sign test's
     MDE is a **43% reduction** — a 30% reduction had power 0.10.
   - **The comparator is not exchangeable (fatal).** Dose matching was flawless, but the control
     suppresses attack **by inducing refusal** (19 direct `ATTACK→REFUSE`, refusal +33, p = 9.5e-07) —
     a channel `KO-3` annihilates to **zero**. Refusal-discounted: **−34 rows, McNemar p = 0.0051**.
   - Also: *"below the 17-row judge band"* is a category error — noise on a **difference of two
     independently judged arms** is ≈√2 × 17 ≈ 24 rows.
   - Also: only **14 of 162** baseline "attacks" have `goal_topicality ≥ 0.5` — **91% off-goal**.
3. **`B-008`** was opened with settlement conditions preregistered: a control **verified
   refusal-neutral** *before* any attack number exists (`refused` is judge-free, so the ordering is
   enforced by construction). At n = 380, **exactly one of four draws qualified**.
4. **`R-016` ✅ REVERSES `R-012`** — against the qualifying control, `KO-3` removes attacks
   (**−36, McNemar p = 3.39e-03**); the rejected controls sit at 117–135 attacks precisely because they
   suppress attack by inducing refusal. *The `R-012` null **was** the rejected control's refusal
   suppression.*
5. **`A-004`/`C-016` ⛔ two published sentences were FALSE** and the magnitude was halved:
   - *"All six arms judged in one invocation"* — **false**: six processes, two batches, two commits.
     `d1` (batch A) scored **117** and `capped_d1` (batch B) **135** on **byte-identical text** — an
     **+18 cross-batch drift** in the direction that inflates the contrast.
   - *"Four controls" / "a family of six draws"* — **false**: `capped_dK ≡ matched_dK` by construction
     on this bank (verified 380/380 byte-identical). **Three** distinct draws existed; the promised
     six-point correlation would have been a fabrication.
   - The selection critique was confirmed and larger than estimated: **r(refusal Δ, attack) = −0.97**.
   - ✅ It survives anyway: `KO-3` sits at `refused = 0`, the most attack-favourable point, and the
     composition-free endpoint (attack rate among non-refused rows) puts `KO-3` at **0.313** below
     every control (0.384–0.473) and below baseline (0.453).
6. **`R-017`/`R-019`** — three genuinely new control draws at a second seed (verified different: 0/210,
   0/205, 0/192 identical draw positions). All three qualifying contrasts negative
   (**−41, −21, −28; mean −30 of 153**) across **3 controls × 2 seeds × 4 judgings**. ✅ The prospective
   prediction held: the *rejected* draw shows no contrast. ⛔ **But at the declared independence unit
   none reaches α** (0.061 / 0.150 / 0.136; pooled p = 0.405). Only a magnitude-aware clustered
   permutation reaches p = 0.032.
7. **`C-017` ⛔** — *"the effect lives in the held-out half"* is **withdrawn**; that was the
   difference-in-significance error. Tested directly by permutation: p = 0.14 / 0.23.
8. **`R-048`** (Qwen, all 8 arms judged in one invocation): **`CONFOUND-LIMITED`.** Face value says
   `KO-3` has *more* attacks than every control (+23…+45, significant on all six); the refusal
   adjustment says *fewer* (−11…−32). **All six brackets straddle zero; 0 of 6 directional claims
   survive.** Forbidden in **both** directions. ✅ One judge-free fact survives intact: **`KO-3` removes
   all 150 refusals and buys only +21 attacks (74 → 95) — 86% of removed refusals do not become
   attacks.** This requires no between-arm judge comparison, which is exactly why it survives the
   confound that kills the contrast.
9. **`R-049`** measured the judge noise floor on the attack rubric directly: re-judging one arm at
   byte-identical settings in a fresh invocation flips **18 of 380** labels (net **+6**), while
   `refused` flips **0 of 380**. Against observed deltas of +23…+45 that is a 3–6× margin ⇒ **both ends
   of `R-048` are real signals that disagree; the limitation is the confound, not judge noise.**

### 5.6 Generality to other harmful concepts — `PR-013` → `R-035` **MIXED**

Two concepts already in-repo, same pipeline, band deliberately kept at 6–14 (switching to `R-031`'s
peak would have been the post-hoc move), 20 domains each:

| concept | cell C Δ | domains | p | verdict |
|---|---|---|---|---|
| `lantern`→`poison` | **−7.760** | **0+/20−** | **1.907e-06** (at floor) | ✅ PASSES |
| `candle`→`missile` | −2.333 | 6+/14− | **0.115** | ⛔ FAILS |

⛔ **The dose-matched control is structurally impossible in these banks** (`R-033`/`R-033a`): they have
no preamble field, so the prompt is ~85% demonstration and the non-demonstration key pool is **63
tokens** against a required 117.5 — max attainable `match_ratio` **0.54**, versus **3.03×** headroom in
the headline bank. The refusal was correct and byte-identical on both concepts. So generic attention
damage is **excluded on `bomb` and inherited, not re-verified, here**.

`PR-015` supplied two substitutes:
- **Part A, a layer placebo** (identical keys at 15–23) — ⚠ `R-037` **INTERMEDIATE**: the placebo is
  **not inert**, it is **13.6% / 17.2%** of the 6–14 magnitude and **opposite in sign**. Partial
  exclusion, quantified as a ratio and not rounded up. It also **falsified its own premise**: band
  inertness measured on one bank **does not transfer** to another. ⛔ *"Layers 15–23 are inert"* now
  requires naming the bank.
- **Part B, a dose test of the offered excuse** — ⛔ `R-038`: *"candle failed because its mapping is
  weak"* is **NOT supported**. Doubling demonstrations raised installation 0.400 → 0.525 and grew the
  effect 47%, while the sign split stayed **bit-identical** (6+/14−, p = 0.115). A power problem
  improves consistency; this did not.

### 5.7 The installation gradient — from a clean positive to a settled categorical claim

This is the arc where the headline moved **twice downward**, each time by the project's own audit.

- **`R-039` ⚠ exploratory** — candle's wrong-sign domains are not resampling noise: across an
  independent dose doubling the per-domain sign is concordant **18/20**, and 5 of 6 positive domains
  are identical. ⇒ Installation is a property of the domain, not noise.
- **`R-040` ⚠ `RANGE-LIMITED`** (`PR-016`, out of sample) — direction right on 4 of 4 populations,
  primary does not reach α (ρ_KO −0.281, p = 0.228; contrast −0.627, p = 0.0749). Crucially it
  established that **regression to the mean (RTM) is real, large, and sign-unstable**: the *placebo
  alone* gives ρ = −0.460 (p = 0.042) on one bank and **+0.345** on another, so the mechanical
  component cannot be subtracted analytically and must be measured per population.
- **`R-041` ✅ `PR-017` SUPPORTED on the blind primary.** Substituting the real dose-matched control
  for the layer placebo (justified before the result, with "no going back" stated in advance):

  | population | blinding | ρ_KO | p | ρ_control | contrast | contrast p |
  |---|---|---|---|---|---|---|
  | button→bomb **Llama**, 38 dom | fully blind | **−0.594** | 1.5e-04 | **+0.312** (p=0.058) | **−0.907** | **2.0e-04** |
  | button→bomb **Qwen**, 38 dom | ρ pre-seen | −0.734 | <1e-4 | −0.326 (p=0.045) | −0.407 | 0.0594 |

- **`R-042` ⛔ the manipulation did not manipulate.** Running the never-before-executed `cds_n8` block
  raised installation only **0.908 → 0.928** with **25 of 38 domains already at ceiling** ⇒ predictions
  2–3 are **VOID by `PR-018`'s own declared rule**, not falsified. The effect *did* grow strongly
  (−7.944 → −9.025, 34/38, p = 6.04e-07) but that is a **dose** effect of the kind the row ladder
  already established. ⇒ **`R-041` remains CORRELATIONAL.**
  `C-028`: the pre-flight measured row counts, control share and novelty but **never asked whether the
  predictor had room to move**. *Before manipulating a bounded quantity, read its distance from the
  bound, not just its variance.*
- **`R-043` ✅** the gradient replicates at a second dose against a real (capped) control: ρ_KO −0.444
  (p = 0.0049), ρ_control −0.040 (p = 0.817), contrast **−0.404, p = 0.0482** — written as marginal
  wherever it appears. Not an independent population (same bank, same 38 domains, a second *dose*).
- **`A-009` — adversarial audit of `R-041`, five attacks committed before any ran.** A (leave-one-out),
  B (three operationalisations) and E (arm-exchangeable null) ✅ survive. ⛔ **C lands**: on the 13
  domains that actually vary, the contrast is **−0.503, p = 0.343**. ⛔ **D**: the control's +0.312
  gradient is real and stable.
- **`R-051`/`B-015` ⛔ the −0.907 headline is INFLATED.** Every population with a control also has a
  preamble, so the offered mechanism was testable: the control gradient is **+0.31 / −0.04 / −0.02 /
  −0.33** across dose, codeword and model on the same bank family. **Preamble mechanism refuted; the
  +0.312 is population-specific.** ⇒ The reproducible quantity is **ρ_KO ≈ −0.44 … −0.73**, and the
  contrast may only be quoted with its population named.
- **`R-052`** — the ceiling is **structural**, producing a catch-22: every population with a working
  control has exactly **1** low-installation domain; the only population with real spread (`candle`) is
  the exploratory *source* of the hypothesis **and** has no possible control. One opening: Qwen has
  **30 of 38** domains below ceiling on a population that does have a control.
- **`R-053` ⛔ attack C REPLICATES on Qwen at n = 30** — the contrast there is **−0.173, p = 0.504**,
  i.e. *smaller*, not merely noisier. **n = 30 kills the power defence.** Mechanism now visible: within
  the varying subrange ρ_KO = −0.601 but ρ_control = **−0.428** — exactly what RTM predicts.
  Qwen additionally fails LOO (worst p = 0.127) and the arm-exchangeable null (p = 0.165).
- **`PR-023`/`R-054`/`R-055` — a bank built specifically to make the test pass, and it still failed.**
  A new derived preset `main_longpre_cds_lowdose` added `cds_n1` and `cds_n2` blocks (same 38 domains,
  same slots, same preamble; **dose is the only thing that varies**). Both staged gates passed:
  control feasibility **9.20×** at n=1, and installation is **monotone in dose — 0.708 → 0.847 → 0.908**
  — with **20** domains ≤0.75 against a required >13. Stage 3 returned the **NULL** branch:

  | population | varying subrange | contrast | p |
  |---|---|---|---|
  | Llama n=4 | 13 domains | −0.503 | 0.343 |
  | Qwen n=4 | 30 domains | −0.173 | 0.504 |
  | **Llama n=1 (built for this)** | **33 domains** | **−0.284** | **0.210** |

  And the mechanism was demonstrated **within a single arm**: on `cds_n1` the *control's* ρ moves
  **−0.086 → −0.338** purely by conditioning on the varying subrange, **with no knockout applied**.
  That is textbook regression to the mean, shown rather than inferred.

**⇒ SETTLED POSITION.** The knockout's effect is **larger in fully-installed domains than in
partially-installed ones** — a **categorical** contrast, robust to leave-one-out and to three
operationalisations across **three populations, two models, three doses** (ρ_KO −0.693 / −0.594 /
−0.444 / −0.734). ⛔ **There is NO continuous dose-response within the partially-installed range** on
any population, including one built to provide it; the apparent within-range gradient is **accounted
for by RTM**.

### 5.8 `R-050` — the missing reference cell (the only measurement of *installation*)

`PR-021` ran `cds38`'s never-touched fourth condition, `benign_literal` — the codeword present with
**no** remapping installed — justified regardless of its hypothesis because the phase had never
measured a natural no-mapping reference.

- Primary ⛔ `CANNOT ANSWER` by its own declared gate (1 of 38 domains qualifies against a required 4).
- ✅ **The full installation swing:** `benign_literal` sits at **−5.495** against cell C baseline's
  **+5.188** ⇒ the doublespeak demonstrations move the reading **+10.68 log-odds**. Every other number
  in the phase measures *removal*; this is the only measurement of *installation*.
- ⚠ **A phase-wide readout limit:** `option_mass` collapses **0.877 → 0.264** without the remapping ⇒
  the forced-choice options only capture the model's answer *when a remapping is installed*. On any
  weakly-mapped population `semantic_logodds` contrasts two options the model largely rejects.
  **Report `option_mass` beside it.**
- ✅ **The benign demonstrations install their own benign remapping** — surface answers include
  ` Mushroom` **22**/380 (the food sense of *button mushroom*), ` Vegetable` 2, ` Salad` 1, and ` Bomb`
  in only **3**/380. ⇒ **The paradigm installs whatever the demonstrations say. Nothing about it is
  specific to harm** — `R-002`'s negative shown positively.

### 5.9 `R-032` — what the model actually *says* (the surface readout)

New analyzer `scripts/dcs_surface_readout.py` decodes `top1_id` beside `option_mass`.

| Llama cell C | ` Bomb` | ` Neither` | ` Button` | option_mass |
|---|---|---|---|---|
| baseline | **345** (90.8%) | 26 | 3 | 0.877 |
| `KO-3` | **19** (5.0%) | **255 (67.1%)** | **102 (26.8%)** | **0.353** |

| Qwen cell C | ` bomb` | ` button` | option_mass |
|---|---|---|---|
| baseline | **306** (80.5%) | 71 | 0.999 |
| `KO-3` | 8 (2.1%) | **372 (97.9%)** | **1.000** |

⇒ The concept answer is destroyed on both models, but **the replacement is model-dependent**: Qwen
cleanly restores the literal codeword; Llama mostly answers ` Neither`. ⛔ *"Flips back to the literal
meaning"* is a **Qwen** statement, not a Llama one. Specificity holds at the surface on both models.

### 5.10 Scaling up: `B-009`, the 116-domain bank, and its result

**`R-056`** sized the fix from **measured** parameters (`C-028`'s lesson), reusing
`scripts/cds_power_domain.py` unchanged at this phase's own numbers (p0 = 0.403, effect 0.196,
m = 10, ICC = 0.158, judge flip 0.0658):

| domains k | power (domain sign test) |
|---|---|
| **38 (what existed)** | **0.311** |
| 76 | 0.632 |
| **114** | ✅ **0.814** |

This **quantitatively explains `R-019`**: at 38 domains the design had 31% power, so p = 0.061/0.150/
0.136 was the expected outcome of an underpowered test, not evidence about the effect. It also
**corrected prior advice to Omer**: splitting 114 domains across two concepts gives ~57 each at power
≈0.5 — worse than useless. **All domains go on one concept**; generality is a separate question with
its own bank.

Omer authorised it. **78 new demonstration domains were authored** (`demo_pools.py`, +877 lines),
merged and audited (`R-057`: 116 domains, 464 pools, 0 short, homogeneous on generator/seed/concept/
codeword/`n_per_pool`/`per_split`; homogeneity **verified, not assumed** — the generator's CLI default
seed is 20260816 while the canonical pools used 20260828, so parameters had to be taken from the
existing pools' own meta). The bank `cds116_button_bomb` has **12,992 rows, 116 domains × 112 rows,
0 alignment violations, 0 duplicate prompt_ids**; the behavioural cell C at `cds_n4` is **1,160 rows**.
`PR-024a` closed the comparator freedom **before the pools existed**: five arms, primary = a
**conjunction** requiring significance against **all three** dose-matched controls, all three reported,
no selection. ~13.5 GPU-hours.

**`R-061` ⛔ `B-009` NOT RESOLVED — 1 of 3.**

| arm | ASR | attacks | refused | induced |
|---|---|---|---|---|
| baseline | 0.3422 | 397 | 144 | — |
| **KO-3** | **0.2741** | **318** | **0** | — |
| d1 | 0.3172 | 368 | 277 | **+133** |
| d2 | 0.3405 | 395 | 179 | **+35** |
| d3 | 0.2819 | 327 | 344 | **+200** |

Primary domain sign test over 116 domains: **p = 0.175 / 0.0096 / 0.466**. ⛔ **The d2 value may not be
quoted alone** — that is exactly the error corrected earlier in the sprint.

**Why it failed is the useful part.** Realised **ICC came in better** than assumed (0.089–0.112 vs
0.158) but the realised **base rate came in 20% lower** (0.32 vs 0.403) ⇒ recomputed power
**0.65 / 0.35 / 0.05** — precisely the observed pattern. ⇒ **Domain count was never the binding
constraint.** The binding constraint is that the controls induce refusal loads of **+35 / +133 / +200**
and the **between-control spread (0.0586) exceeds the effect (0.0391)**: choosing a control returns
anything from p = 0.0096 to p = 0.47 **on identical data**.

**`R-062`** (`PR-025`) then quantified the confound: induced refusal predicts lost attacks
(pooled ρ **−0.378**, p = 5.0e-05; within each control −0.35 to −0.41) — but the **magnitude is not
regular**: conversion is **0.218 / 0.057 / 0.350**, a 6× range. Since `PR-014`'s bracket assumed
conversion **1.000**, its adjusted end **over-credits the control by 3–17×**.

**`R-063`** (`PR-026`) applied the measured conversion **symmetrically to both arms** (the face end
never debited `KO-3` for clearing all 144 baseline refusals, which by the same mechanism gifted it
attacks):

| control | face (c=0) | `PR-014` adjusted (c=1) | **calibrated interval** |
|---|---|---|---|
| d1 | −50 | −183 | **[−146.9, −65.8]** |
| d2 | −77 | −112 | **[−139.6, −87.2]** |
| d3 | **−9** | −209 | **[−129.4, −28.6]** |

Entirely negative for all three and **half the width**. On d3 the face value (−9) lies **outside** the
calibrated interval, so *"nearer the face value"* would have been wrong too. `C-038` records the
pattern honestly: three statements about the same bracket in three hours, over-corrected then
over-corrected back; the pattern matters more than either fix.

**`R-064` ⛔ `PR-027` STOPS at Stage 1** — the installation ceiling is a property of the **paradigm**,
not of these domains. The 78 independently-authored new domains reproduce the original 38's
installation distribution almost exactly (mean **0.900 vs 0.908**, sd **0.192 vs 0.197**); the
low-installation yield is **3.45%** either way, so a usable low tail needs **~580 domains**. The gate
failed on ≤0.25 count (4, needed >5) and Stage 2 did not run.

### 5.11 The final move: treat the control draw as a random effect (`PR-028`)

The diagnosis of `R-061` was that *choosing* a comparator is the problem. Rather than choose better,
`PR-028` **removed the choice**: the three controls are seeded draws from one population at identical
dose, so the draw is a **random effect** — test `KO-3` against the control **distribution**, with the
between-control sd as the error term. Sized from the K=3 spread (sd 0.0295) and observed effect
(−0.0391), **K = 8** was chosen (3 existing + 5 new, ~10.1 GPU-h).

Before the data, three things were frozen:
- `PR-028a` — the analyzer, committed while arms were at 113–351 of 1160 rows; its dry run at K=3
  reproduced the sizing inputs exactly (δ −0.0391, t(2) = −2.293, p = 0.1488), and **found a defect in
  itself**: the verdict read "WELL-POWERED NEGATIVE at K=3", which is false since the design predicts
  p = 0.149 at K=3 *even if the effect is real*. Also declared, before the data: **the calibration can
  manufacture its own significance** — at `c_hi` it removes 74% of the between-control spread, so
  calibrated-only significance is explicitly not sufficient.
- `PR-028b` — **judge all ten arms in one invocation**, re-judging the five that already had labels,
  to remove a `(5/8)·offset` session-bias term from the primary.
- `PR-028c` — the drift analyzer, frozen before a single re-judged label existed.

Supporting results:
- **`R-065`/`R-066`** — blocker `B-007` (control-draw positions not persisted) is **CLOSED and its
  premise was false**: the positions *are* written per row in
  `control_draw["<arm>@seed<seed>"]["positions"]` on **46/46 behavioural arms** (and absent on 20/20
  *readout* arms — the blocker had been raised on a readout arm and over-generalised). Identity-verified:
  regeneration from the spans + seed reproduces the persisted set on **200/200** rows, and the `seed+1`
  mutant on **0/200**. Same for `B-013`.
- **`R-070`** — the eight draws are **almost** independent (mean pairwise overlap 25.54 vs a simulated
  null of 25.06; ratio 1.0193, 5.0 SE). Declared *before* the result: positive dependence makes the
  primary **mildly anti-conservative**, which cannot manufacture a null.
- **`R-074`** (`PR-028c` final, 5 arms × 1160 = **5800 byte-identical rows**, 0 sha exclusions):
  **728 flips (12.6%) but net −54.** The preregistered row-level binomial gives p = 0.0494 — **at the
  wrong unit**: 5800 rows are not 5800 replicates of a *session* offset; there are five arms.
  Arm-level: mean −0.00931, **t(4) = −1.69, p = 0.1655, 95% CI [−0.0246, +0.0060]**.
  ⇒ **`NO ESTABLISHED OFFSET`**, and `R-068`'s earlier "19–25% bias" figure is **withdrawn**. The CI
  contains both prior estimates (0.0020 and 0.0158), so the data cannot distinguish them.
  ✅ **`C-023` is now very strongly supported: 0 refusal-label flips in 5800 rows** (plus `R-049`'s 380).
  `C-043` records that the analyzer had been run at 1, 2 and 3 arms and that a nominal p = 0.0489 at the
  third look carries ≈13% family-wise error — **the drift verdict was taken once, at 5 arms.**

**`R-075` — `PR-028` PRIMARY at K = 8: `UNDERPOWERED NEGATIVE`.**
All ten arms judged in one session (job 852324), 1160 rows each, `judge_status` ok on all 11,600.

| control | ASR | refusals | induced |
|---|---|---|---|
| d1 | 0.2991 | 277 | +133 |
| d2 | 0.3448 | 179 | +35 |
| d3 | 0.2672 | 344 | +200 |
| s0905_d1 | 0.3190 | 166 | +22 |
| s0905_d2 | 0.3741 | 137 | **−7** |
| s0905_d3 | 0.2328 | 354 | +210 |
| s0906_d1 | **0.1259** | **706** | **+562** |
| s0906_d2 | 0.2353 | 281 | +137 |

**KO-3 ASR 0.2526 vs control mean 0.2748; δ = −0.0222; t(7) = −0.80; p = 0.449.**

⛔ **Not a well-powered negative** — the design's own declared branch fired instead. The realised
between-control sd is **0.0783**, **2.65×** the 0.0295 the K=8 sizing rested on, so the minimum
detectable effect (**0.0654**) is **larger than the −0.0391 the design set out to detect**; realised
power against that effect is **0.232**. ⇒ **The behavioural half is NOT ESTABLISHED on Llama, and this
null is NOT evidence of absence.**

**The cause is the substantive finding: dose-matched controls are NOT an exchangeable population.**
At *identical* dose (`keys_masked` median **522.0**, `match_ratio` **1.000**, verified on all eight),
induced refusal spans **−7 to +562** — a **25-fold** range — and ASR spans **0.126–0.374**. The extreme
arm was checked and has no defect. ⇒ **Which positions are masked dominates behaviour at constant
dose.** The "dose-matched control" is not one intervention with noise; it is a **family of very
different interventions.**

Calibration does not rescue it: `c = 0.057` → p = 0.176, and the `c = 0.350` p is **not quotable**
because the correction removes 59% of the between-control spread — declared in `PR-028a` before the data.

**`R-076`** re-ran the mask-geometry screen at k = 8 (where the sign-test floor is 0.0078 and the test
*could* have concluded): **0 of 4 non-degenerate features sign-consistent** within arms, and
**nothing** between arms (best |ρ| = 0.238, p = 0.589, n = 8). `R-067`'s specific prediction was borne
out — the one "consistent" feature at k=3 is not consistent at k=8, exactly what noise produces there.
⚠ Scope stated severely: at n = 8 only |ρ| ≳ 0.71 could have been detected, so this closes *this
feature set*, not the idea. **Consequence:** the repair `R-061` proposed — a control matched on
*predicted* refusal — is **closed**. Matching on *observed* refusal is post-hoc (`C-023`); matching on
predicted refusal needs a predictor, and there is none.

**`C-045`** then corrected `R-075`'s own power arithmetic: the "K ≈ 24 for 80% power" figure came from a
crude normal approximation. Recomputed with the non-central t at df = K−1:

| K | SE | MDE | power(−0.0391) | power(−0.0222) |
|---|---|---|---|---|
| 8 (done) | 0.0277 | 0.0655 | **0.23** | 0.11 |
| 24 | 0.0160 | 0.0331 | 0.65 | 0.27 |
| **32** | 0.0138 | **0.0282** | **0.78** | 0.34 |
| 52 | 0.0109 | 0.0218 | 0.94 | 0.52 |
| 105 | 0.0076 | 0.0152 | 1.00 | 0.82 |

---

<a name="6-scoreboard"></a>
## 6. The standing scoreboard

### 6.1 What we can defend

| # | claim | scope / caveat |
|---|---|---|
| `R-008`/`R-010`/`R-011`/`R-025` | **The demonstration→query path is necessary for the remapping and specific to it.** DiD −9.89 (Llama·button), −9.35 (Llama·basket), −22.20 (Qwen·button) | ⚠ all three share the same **1+/37−** sign pattern — one pattern replicated 3×, **not** 3 independent p-values |
| `R-021`/`R-022` | **No single query position carries it; ~¼ of the span does.** K=1 −0.01, K=2 −0.01, **K=8 −6.62**, K=16 −7.89, K=32 −8.08 — a step, then saturation | ⚠ row count and dose rise together |
| `R-022` controls | **Controls inert across a 32× dose range** (+5.16…+5.38 vs +5.19 baseline) | the step is about *which* keys are cut |
| `R-024` | **The mechanism is cross-model.** Qwen3-14B replicates `KO-3` **in sign and in the identical 1+/37− domain split**; `frac>0` 0.813 → 0.021 | capability gate passed first (`R-023`); ⛔ **no magnitude ratio** — doses unmatched and distributions differently shaped (`C-046`) |
| `R-030`/`R-031` | **Lives in layers 0–14, peaks at 10–14; no *destructive* effect above 14.** Equal-dose bands −3.39 / −2.99 / **−5.65**; 15–23 +0.15, 24–31 +0.75 | ⛔ *"localised to 6–14"* is too strong; ⛔ *"absent above 14"* overstates — 24–31 is +0.754 at **38+/0−** and **not inert** (`C-046`); no per-layer profile claimable |
| `R-041`/`R-043`, settled by `R-055` | **Fully-installed domains lose MORE — CATEGORICALLY.** ρ_KO −0.693 / −0.594 / −0.444 / −0.734 over 3 populations, 2 models, 3 doses | ⛔ **no** continuous dose-response; the within-range gradient is **RTM** |
| `R-006`/`R-014` | `KO-1` leaves mapping **and** attack unchanged, on a verified refusal-neutral control | a valid, well-powered null |
| `R-012b`/`R-026`/`R-048`/`R-061` | **Refusal moves under every scope tested** — Llama 42→0, 144→0; **Qwen 150→0** — and on Qwen the 150 removed refusals buy only **+21** attacks, so **86% do not become attacks** | 2 models × 4 scopes; the 86% is judge-free within one invocation |
| `R-050` | **The paradigm installs whatever the demonstrations say** — benign demonstrations install a benign remapping (` Mushroom` 22/380, ` Bomb` 3/380). Full installation swing **+10.68 log-odds** | mechanism, not harm-specific |
| `R-002`/`R-003`/`R-004` | ⛔ not concept-specific · ⛔ does not accumulate · ✅ null control exact (0.000e+00 at 96 cells) | evaluated negatives + a positive control |
| `R-075` (as a finding) | **Dose-matched controls are not an exchangeable population**: at identical dose, induced refusal spans −7…+562 (25×) and ASR 0.126–0.374 | the most interesting negative in the sprint |
| `TSC-R-004` | `basket↔bomb` **REPLICATES** the behavioural removal on Llama, p = 1.18e-02 / 9.11e-04 / 2.60e-03 | `demo_processing_only` scope |
| `TSC-R-001` | The `button` headline survives **three independent judge passes**; worst of nine p = 1.093e-05 | |
| `TSC-R-005` | The behavioural effect is **MODEL-SPECIFIC**, measured not inferred (registered interaction, absolute 3/3) | Qwen is a **capable null**, k_inf 30–34 |
| `TSC-R-007` | **The paradigm is constructible for only ~20% of a category-balanced AdvBench draw**; the whole 495-row benchmark affords **15** distinct mappable object-concepts, 11 of them cyber or weapons | a scope statement about the method |

### 6.2 Claims we must not say (verbatim from the logs)

- ⛔ *"Installation was manipulated"* / *"the gradient is causal"* — `R-042`: the knob did not turn.
- ⛔ *"The effect is GRADED by installation"* as a **continuous** claim — `R-053`/`R-055`. Say
  **categorical**.
- ⛔ *"The gradient's effect size is −0.907"* — `R-051`: inflated by a control gradient that does not
  reproduce. Quote **ρ_KO**, and the contrast only with its population named.
- ⛔ *"Attack C only failed for lack of power"* — tested at 13, 30 and **33** domains; the contrast is
  *smaller*, not noisier. **Dead.**
- ⛔ *"116 domains was not enough"* — `R-061`: ICC came in better, base rate 20% lower, and
  control-to-control variance exceeds the effect.
- ⛔ *"`KO-3` reduces attack at the domain unit"* — `R-061`: 1 of 3. And never `p = 0.0096` alone.
- ⛔ *"`KO-3` increases attack on Qwen"* (the face value, exactly what the confound predicts) **and**
  ⛔ *"`KO-3` reduces attack on Qwen"* (the adjusted end, significant on 2 of 6) **and** ⛔ *"Qwen shows
  no behavioural effect"* (a straddling bracket is **undetermined**, not null).
- ⛔ The K=8 null as *"the attack doesn't work"* — it is an **underpowered** negative; the correct
  sentence is *"the behavioural effect is not established, and is bounded below ~0.066."*
- ⛔ *"Layers 15–23 are inert"* without naming the bank (`R-037`), and ⛔ *"the effect is absent above
  layer 14"* at all (`C-046`) — say *"no **destructive** effect above L14"*, and report 24–31's
  +0.754 (38+/0−) as exploratory and unexplained.
- ⛔ Any **cross-model magnitude ratio** (`C-046`) — the replication is in **sign and domain split**.
- ⛔ `R-002` and `R-050` quoted under **one** scope line (`C-046`) — different banks, different
  independence units.
- ⛔ *"Retrieval is distributed across the query span"* — `R-022` shows a **threshold**.
- ⛔ *"Demonstration-specific ATTACK removal"* without the topicality sentence beside it
  (`TSC-C-004`: 90–100% of judge-positive completions never contain the concept word).
- ⛔ Three p-values of 2.8e-10 as independent evidence — **one sign pattern, three times**.
- ⛔ *"p < 1e-9"* anywhere — that was the attainable **floor** printed as the p-value.
- ⛔ *"matched control"* unqualified — the control does ≈1.95× more edits by position geometry.
- ⛔ *"38 domains means 38 independent harmful behaviours"* — it is 38 *contexts for a single mapping*.
- ⛔ `d_surface` as validated, or as a GCG/MAC objective. GCG/MAC stay closed.

### 6.3 Retracted — never revive

| # | retracted claim | why |
|---|---|---|
| `C-010` | "The mapping is constructed during demonstration processing, not retrieved at the final codeword token" | the knocked-out token sits 10 tokens before the end; ≥11 downstream positions keep unblocked demo attention at all 32 layers |
| `C-005` | `R-001`'s L6–L12 peak | absent from the per-row standardized effect size, which is largest at L0 |
| `C-008` | `R-005`'s option-mass caveat | algebraically impossible; log-odds is mass-invariant to 1.8e-15. The caveat *understated* the result |
| `C-009`/`C-011` | "The controls are inert" | negligible in magnitude (\|Δ\| < 0.31) but **not sign-null** (31+/7− and 6+/32−) |
| `C-015` | `R-012`'s null — "the mapping can be destroyed without the attack changing" | wrong test (sign test on row-paired data) **and** a non-exchangeable control that suppresses attack by inducing refusal |
| `C-016a` | "All six `B-008` arms were judged in one invocation" | **false** — two batches; +18-attack drift on byte-identical text |
| `C-016b` | "Four controls" / "a family of six draws" | **false** — `capped_dK ≡ matched_dK`; **three** distinct draws existed |
| `C-016c` | `R-016`'s "−36 attacks, p = 0.0034" as a magnitude | direction survives; magnitude does not |
| `C-017` | "The effect lives in the held-out half" | difference-in-significance error; tested directly, p = 0.14 / 0.23 |
| `C-002` | "The basket replication is partly an illusion" | measured: cells A and C are **0.000** byte-identical across lexical banks |
| `R-068`'s "19–25% judge-drift bias" | withdrawn by `R-074` | drift is **not established**; point estimate ≈15% with an interval spanning −39% to +10% |
| `R-075`'s "K ≈ 24 for 80% power" | withdrawn by `C-045` | crude normal approximation; the correct answer is **K = 32** |
| "Qwen replicates at **~3×** the Llama magnitude" | withdrawn by `C-046` | `R-023` pre-declared the comparison invalid; distributions differently shaped and doses unmatched (91,872/11L vs 66,816/9L) on a steeply dose-graded quantity |
| "The effect is **absent** above layer 14" | withdrawn by `C-046` | 24–31 is **+0.754 at 38+/0−, Holm p = 2.9e-11** — the most consistent sign pattern in the sweep. Only the **destructive** effect is absent |
| *inherited* | `d_surface` as validated or as a GCG/MAC objective | still **BLOCKED** |

### 6.4 Cannot answer / underpowered

- **`KO-2` on the ASR endpoint** — `UNINFORMATIVE BY CONSTRUCTION`, `k_informative = 1`.
- **`PR-010`** (Qwen behavioural interaction) — `CANNOT ANSWER`: 0 of 6 draws qualify. A limitation of
  the **criterion**, superseded by `R-048`'s bounding.
- **`PR-014`** — `CONFOUND-LIMITED`: all six brackets straddle zero.
- **`PR-019`/`PR-019a`** (does prior plausibility predict installation?) — `CANNOT ANSWER` on this
  instrument family. The reliability gate fired by exactly one domain, and the threshold was **not
  moved**.
- **`PR-021`** primary — `CANNOT ANSWER` by its own gate (1 of 38 domains vs a required 4).
- **`PR-024`/`B-009`** — **NOT RESOLVED**: 1 of 3 on the declared conjunction.
- **`PR-028`** at K=8 — **UNDERPOWERED NEGATIVE**.
- **`TSC-R-007`/P4** — `DECLINED FOR POWER`, never launched. ⛔ A decline is **not** a null.
- **The topical endpoint on these banks** — degenerate (one distinctive word, values ∈ {0,1}).

---

<a name="7-corrections"></a>
## 7. Corrections, bugs and near-misses — the methodological record

These are worth reading on their own: several are reusable bug classes, and three were caught **before**
they produced a result.

### 7.1 Bugs caught before they produced a number

- **`C-001`** — the position resolver returned an **empty span on 1032/1032 real rows**. Cause: Llama's
  BPE emits `" button"` as one token whose offset span starts at the *leading space*, so a containment
  predicate (`a >= lo and b <= hi`) rejected it for being one character too wide. Fixed by testing
  **overlap** and taking membership on the last subtoken. ⚠ **All 63 synthetic tests passed against the
  broken resolver** because the toy harness hands the scope its span directly and never exercises the
  tokenizer. ⛔ A no-op knockout scores as a clean null.
- **`C-006`** — the pre-flight declared a healthy scope **universally dead** because
  `scoped_span_is_dead` was not forwarded the `surface_span` argument. *The per-row site was wired and
  the pre-flight site was not* — the same one-of-two-paths shape that has silently dropped
  `control_seed` twice. ✅ It **REFUSED rather than running a no-op and reporting a clean null.**
- **`C-014`** — `CDS-R-020` reproduced **exactly**, one day after reading about it, and was caught by
  two guards: the intervened arms crashed rather than silently returning a different row set, and the
  pre-commit `run_completeness_check` flagged the short baseline. `--no-verify` was not used.
- **`C-030`** — `PR-014`'s bound pointed **the wrong way**, corrected *before* the analysis ran.
  Then **`C-033`**: which end is conservative depends on the observed **sign**, so it cannot be fixed
  in a preregistration at all — the correct pre-declaration is *"report the bracket"*.
- **`C-037` / `C-037b` / `C-037c`** — a real bug in shared code. The incidental-collision **detector**
  matched `\b{word}s?\b` (singular *and* plural) while the **repair** matched singular only, so a
  plural collision was detected and could **never** be repaired. The first fix reached
  `pool["sentences"]` but not `pool["dev"]`/`pool["heldout"]` — **the fields `build_prompt` actually
  reads** — so the detector saw a repaired pool and the builder used an unrepaired one; the defect
  reached a 12,992-row bank. `C-037c` is the near-miss: the bank was **rebuilt under a running job**,
  and because `prompt_id`s are identical across builds, an analyzer asserting `prompt_id` set equality
  would have paired a baseline from bank A against knockouts from bank B. Cost: 8 GPU-minutes.
  ⇒ **Rule: never rewrite an input artifact while a job reading it is in flight.**
- **`A-011`** — the regression test for the above, and the lesson that *"the test I would have trusted
  misses the second bug"*: a test expressed in terms of the **detector** inherits the detector's blind
  spots; state the invariant over the fields the **consumer** reads.

### 7.2 Instrument failures — checks that agreed with themselves

- **`TSC-C-001`** — a verifier comparing a published field against `summary.json`'s copy of the same
  permanently-`null` field asserted `None == None` and printed PASS. Now re-derives from raw rows.
  **Fifth instance in three sprints.**
- **`C-034`** — verifier acceptance bands were **hardcoded** for a Monte-Carlo rejection rate, valid at
  exactly one N. Cost one false alarm (a null calibration flagged anti-conservative at 0.0767 when a
  3000-draw re-run put it at 0.0490) and one **withdrawn claim** (`A-006`'s "conservative" label). Fixed
  at the root: the band is now derived from N as `α ± 3·sqrt(α(1−α)/n)`.
- **`A-014`** — and then **`C-034` repeated inside the very instrument built to catch it**: the audit's
  own first run failed on a hardcoded `ok = n_cons <= 6`.
- **`A-005`** — a coverage audit whose regex flagged three preregistrations as unresolved; **all three
  were false positives**, resolved in later entries under different ids. Redone by *reading the
  resolving entry*. `A-013` repeated the lesson: a regex over `PR-` mentions is useless because they
  appear everywhere.
- **`C-036`** — the pool audit **rejected the canonical pools** (27 of 94 flagged collisions were in the
  38-domain pools behind every committed bank in the phase). The matcher was wrong, not the data.

### 7.3 The independence-unit error, three times

`C-016`/`R-016` first, then `R-067` (a pooled within-prompt test that said "signal" because it was
confounded with arm identity — **k = 3 draws is the real sample size, not 3480 residuals**), then
`R-074` (a preregistered row-level binomial over 5800 rows that is not 5800 replicates of a *session*
offset — there are five arms). In `R-074` the correction moved the result **away** from significance
(0.049 → 0.166), inside the author's own preregistered analyzer.

### 7.4 Instrument nondeterminism

- **`R-046` ⛔ `temperature = 0` is NOT deterministic** on the OpenAI endpoint — an identical re-run
  flipped 1 of 38 rating vectors and moved a gate count 5 → 6. Found because a refactor made a
  published result be re-run. ⇒ `R-045`'s *verdict* is robust; `R-045`'s *count* is not.
- **`C-031`** — a rubric paraphrase invented its own item list when handed a single item; **the strict
  parser refused**, and the contemplated lenient fallback would have silently recorded the wrong
  domain's rating for every domain.
- **`B-016` ⚠ open** — artifacts record the judge **alias** (`openai/gpt-4o-mini`), never the served
  **snapshot** (`gpt-4o-mini-2024-07-18`), so drift and a silent model rotation are not separable in
  general. Mitigated by probing the snapshot before and after each judging run; for the `PR-028` run it
  was **identical before and after**.

### 7.5 Process failures

- **`C-018`, repeated exactly as `C-032` one day later** — two `git commit`s in flight collided on
  `.git/index.lock` (the pre-commit hook runs 9 deliverable guards + 341 tests, ~165 s on a quiet
  filesystem). The symptom reads as a bad pathspec, not a lock collision, and **deleting the lock would
  have been destructive**. ⇒ Rule: never background a commit here; never have two in flight.
- **`C-021`** — a commit whose message named 26 untracked argsfiles contained **none of them**:
  `git commit -- <paths>` operates on **tracked** files only and exits 0 with no warning. Caught only by
  a post-commit re-count. ⇒ A commit introducing **new** files must be followed by a re-count of the
  untracked set, not by reading its exit status.
- **`C-041`** — the judge was started **on the login node** and wrote a partial arm under the live tag
  prefix before a 2-minute timeout killed it. Quarantined, not deleted; 0 live directories verified
  before submitting the real job.
- **`DCS-035`** — a liveness watch treated "job left `squeue`" as terminal and raced the writer. What
  protected the analysis: the analyzers **refuse without `DONE.json`** and on wrong row counts.
- **`DCS-023`** — under NFS degradation (2.6 s per small-file read) a commit sat in the pre-commit hook
  for 90 minutes. `--no-verify` was **declined**, because the two guards that could not complete were
  exactly the number-checking ones on a commit adding ten new headline numbers. It was used **once,
  deliberately, later**, with 8 of 9 guards verified green out-of-band and the 9th's property checked
  by hand.

### 7.6 `C-046` — the closing adversarial re-audit, and the phase's dominant failure mode

Committed **2026-09-05 19:47** (`8fb3c7e3`), after the body of this summary was drafted. A 14-agent
synthesis re-read the whole log end-to-end and put six load-bearing claims to **refutation** agents
instructed to *default to refuted* if a number could not be verified, and to read the **last** mention
of every id (this log corrects itself later). Each correction was verified **by hand against the log**
before being acted on — agent output is not authority.

**2 of 6 survived unchanged; 4 were corrected:**

1. ⛔ *"Qwen replicates at ~3× the Llama magnitude"* — **not claimable** (see §5.3).
2. ⛔ *"The effect is absent above layer 14"* — **overstates** (see §5.4).
3. ⚠ `R-037`'s core finding stands, but the claim as surveyed **misstated its population**.
4. ⚠ `R-002` + `R-050` carry no retraction, but the two legs run on **different banks with different
   independence units** (`R-002` on the x2fit banks over 30 families; only `R-050` is cds38 / 38
   domains) and were being quoted under **one** scope line.

⇒ **The pattern is uniform and worth naming: not one of the four was a wrong number.** Every figure
checked out. All four were **scope, unit or comparability** errors — claims true of one population,
dose or bank, stated as if general. That is this phase's dominant failure mode (`C-027`, `R-066`,
`R-067`, `R-074` are the same class), **and it survived four prior audits** (`A-005`, `A-009`, `A-013`,
`A-014`) because those checked *whether the numbers were right*, not *what population they described*.

### 7.7 Preregistrations whose declared branches did not partition the space

Three times (`R-035`, `R-038`, `R-049`) the observed outcome fell between the declared branches. The
recorded design lesson: **branches defined on a conjunction leave the "one conjunct satisfied" region
unlabelled.** Each was reported as intermediate rather than rounded to the nearer branch.

---

<a name="8-code"></a>
## 8. Code, banks and artifacts produced

### 8.1 New analysis scripts (`scripts/`)

Convention: analyzers are committed **before** the data they read exists, are stdlib-only (plus a
tokenizer where needed), read only scalar columns of `results.jsonl`, and never open `gens.jsonl`.

| Script | Computes |
|---|---|
| `dcs_cell_interaction.py` | `PR-001` cell×intervention DiD; distinguishes outcome E from F; pairs by domain only across cells; reports absolute **and** headroom-normalised forms |
| `dcs_generality.py` | `PR-013` second/third-concept replication; per-domain paired Δ log-odds, sign test over 20 domains |
| `dcs_installation_gradient.py` | `PR-016`/`PR-017`; Spearman ρ(install, Δ) with a seeded permutation test; **the reported quantity is the ρ contrast, never ρ_KO alone** |
| `dcs_surface_readout.py` | decodes `top1_id` at the readout position → the surface answer distribution beside `option_mass`; `--did-both` for the decision-level DiD |
| `dcs_pr014_bound.py` | `PR-014` bounding (not comparator selection); row-paired exact McNemar + a maximally-hostile refusal-credit assignment |
| `dcs_judge_repeat_delta.py` | `PR-020`/`B-014`; same arm judged twice at byte-identical settings |
| `dcs_plausibility_rating.py` | `PR-019`/`PR-019a` external plausibility instrument with its reliability gate |
| `dcs_merge_audit_pools.py` | `PR-024` pool merge + acceptance audit; prints **ids and counts only**, never sentence text |
| `dcs_audit_r041.py` | the five adversarial attacks on `R-041`, all named before any ran; **imports** the gradient script rather than re-implementing it |
| `dcs_draw_geometry_predicts_refusal.py` | `R-067`/`R-076`; within-prompt estimand, arm as unit; pooled test explicitly labelled CONFOUNDED; degenerate features flagged, not scored 0 |
| `dcs_pr028_primary.py` | the `PR-028` primary; KO-3 vs the control **distribution**; raw **and** calibrated; guards judge-session mixing on `slurm_job_id` |
| `dcs_judge_drift_p24j_vs_p28j.py` | `PR-028c`; byte-identity gated on `completion_sha256_16`; tests the **net**, at the arm unit |
| `dcs_figures.py` | the phase figure set; **recomputes every plotted number from committed `results.jsonl`**; four of eight planned panels deliberately not drawn |
| `dcs_check_tracker.py` | structural check for the session tracker (written after an inline version false-positived on an escaped pipe) |
| `tsc_select_requests.py` | the blind, metadata-only request draw |
| `tsc_judge_robustness.py` | `TSC-PR-002`; flip rate over both raw-row and **distinct-completion** denominators |
| `tsc_model_interaction.py` | `TSC-PR-004`; refuses to let "significant in one, not the other" stand as an interaction |
| `tsc_filter_requests.py` | `TSC-PR-007` mechanical constructibility filter + `--anti-tuning`; never prints request text |

**Verifier / mutation-harness pairs** (all new): `dcs_verify_installation_gradient.py`,
`dcs_verify_pr014_bound.py`, `dcs_verify_audit_r041.py`, `dcs_verify_merge_audit.py`,
`dcs_verify_domain_test.py`, `dcs_verify_draw_regenerable.py`, `dcs_audit_r067.py`.
Notable: `dcs_verify_pr014_bound.py` **check 4 turns the `C-030` prose correction into an assertion**
(`bounded_delta ≤ face_delta`, 300/300); `dcs_audit_r067.py` mutates the **data**, never the analyzer.

**Shell runners:** `judge_dcsqw_behavioral.sh` (8 Qwen arms, one invocation), `judge_pr020_repeat.sh`,
`judge_pr024_behavioral.sh` (5 arms × 1160), `judge_pr028_all10.sh` (**all ten** arms in one
invocation), `run_plausibility.sh`, `run_pool_generation.sh`.

### 8.2 New modules in `src/boombness/`

- **`dcs_cell_geometry.py`** — the 2×2 representation geometry the repo previously could not report;
  re-derives every direction from `cell_means` and checks the recomputation against the shipped unit
  vectors rather than trusting the producer's derived field.
- **`dcs_metadata.py`** — the concept-metadata backfill as a **sidecar table**, joined on
  `(bank_file_sha16, prompt_id)`, deliberately *not* new bank fields (that would change
  `bank_rows_sha16`, which every result-to-bank join keys on).
- **`dcs_rowwise.py`** — per-row candidate projections and occurrence trajectories, computed from an
  algebraic identity re-asserted at runtime, so **no GPU, no model, no re-extraction**.

### 8.3 Modified

- **`score_behavior.py`** — three commits: the `target_surface_row_only` scope + resolver (one code
  path serving both KO-1 and KO-2, so treatment and specificity control cannot differ in dose); the
  pre-flight fix; the `query_last_k_rows` scope + `--knockout-last-k`, which **refuses in both
  directions** (the flag with any other scope; K < 1, which would be "a no-op knockout that scores as a
  null").
- **`prompt_families.py`** — the `C-037`/`C-037b` plural-repair fix, and the **derived** preset
  `main_longpre_cds_lowdose` (derived rather than edited so every existing preset stays byte-stable).
- **`demo_pools.py`** (+877) — authors the 78 new demonstration domains.
- **`run_completeness_check.py`** — documented `KNOWN_SHORT` entries for the basket arms, each naming
  the exclusion file, its sha, the non-uniform loss, and the preregistered robustness recomputation.
- **`retraction_sweep.py`** — wires this phase's two deliverables into the sweep; until then the whole
  phase was invisible to it.
- **`slurm/run_boombness.sh`** — a **10 MB** write-and-read-back guard before model load, because the
  quota failure is **size-dependent** (a 5-byte write succeeded in the same second a 100-byte write
  returned `EDQUOT`), so a token `touch` reports healthy.
- **`doublespeak_causality/pair_common.py`** — the `prompt_last_row_only` and `query_last_k_rows`
  scopes, both **derived from arguments the consumer already resolves** so the two cannot drift.

### 8.4 Tests

| Path | Pins |
|---|---|
| `tests/test_incidental_repair_plural.py` (NEW, 4 tests) | `C-037` **and** `C-037b`; asserts repair on **every field the builder reads**, and that the two matchers agree |
| `tests/test_scoped_knockout_wiring.py` | the `C-006` pre-flight regression, in **both** directions, plus a source-grep so the pre-flight cannot silently check a different population |
| `tests/test_readout_liveness.py` | liveness for the three new scopes |
| `doublespeak_causality/tests/test_scoped_attnknockout.py` | `test_the_three_rungs_are_separable` (each narrow rung a strict subset, the two narrow rungs disjoint); dose monotone in K; K = \|Q\| reproduces `query_prefill_only` exactly |
| `tests/test_prompt_id_exclusions.py` (17 tests) | every `--exclude-prompt-ids` refusal, each paired with an executed mutant |
| `tests/test_tsc_request_filter.py` (15 tests) | including that the artifact leaks **no** source instruction or 40-char fragment |

### 8.5 Data banks built

| Bank | Rows | Domains | Notes |
|---|---|---|---|
| `boombness_prompt_bank_cds116_button_bomb.jsonl` | **12,992** | **116** | 38 canonical + 78 new, disjoint, union exactly 116; 112 rows/domain uniform; 16 cells all populated; `bank_rows_sha16 = d46a48ccc3df66d2`; built twice (rebuilt after `C-037b`) |
| `boombness_prompt_bank_cdslow38_button_bomb.jsonl` | **10,336** | 38 | `PR-023` low-dose blocks `cds_n1` / `cds_n2`; byte-identical regeneration test passes; the shared `cds_n4` block has an identical sha in both banks |
| `demo_pools_78new.json` | 312 pools | 78 | gpt-4o-mini, seed **20260828** (not the CLI default 20260816) |
| `demo_pools_116dom.json` | 464 pools | 116 | `content_sha16 = 976aa2b0b617118d`, matching the bank meta's `pools_sha16` |
| `exclusions/cds38_basket_bomb_occurrence_mismatch_forcedchoice.txt` | 3 ids | — | different ids from the behavioural exclusion; named from the **baseline** arm's failure ledger before any intervened outcome existed |

### 8.6 Argsfiles and outputs

`runargs/dcs/` holds **125 tracked files** (122 argsfiles), one line of `score_behavior.py` CLI
arguments each, basename always equal to the `--tag`. Prefixes encode the experiment
(`dcsro_` readout, `dcsbeh_` behavioural, `dcsbk_` basket, `dcsg_` generality, `dcsqw_`/`dcsqwb_` Qwen,
`dcsLb*`/`dcsFf*` layer sweeps, `dcsk2/8/16_` the row ladder, `dcsp15…dcsp29_` the numbered
preregistrations). `dcsp29_` holds the **24** live K=32 draws.

`outputs/boombness/dcs_analysis/` holds **50 JSON artifacts** across seven schemas
(`DCS_INSTALLATION_GRADIENT/1`, `DCS_AUDIT_R041/1`, `DCS_GENERALITY/1`, `DCS_SURFACE_READOUT/1`,
`DCS_SURFACE_DID/1`, `DCS_CELL_INTERACTION/1`, `DCS_PR014_BOUND/1`, plus the drift, geometry,
plausibility and pool-merge artifacts).

---

<a name="9-process"></a>
## 9. Process and infrastructure work

- **`DCS-002`** — a **disk quota** blocker: `quota` reported the user at exactly 200 GiB against a
  *displayed* limit of 16384 G, while `df` showed 5.4 T free. The failure is **size-dependent** and hits
  compute nodes too. Resolved by moving the 65 G HuggingFace cache to `/vol/scratch` behind a symlink
  (deleting nothing), verified 242 files both sides, 0 broken symlinks. ⚠ A `pkill -f` against a broad
  pattern nearly matched **another user's process** on the shared login node — not a safe verb there.
- **`DCS-030`/`C-021`/`DCS-031` — the provenance layer.** For most of the phase **none** of its outputs
  were in version control: `.gitignore` carries a bare `outputs/`, so `git status` cannot list them and
  their absence was invisible. **0 of 674** artifact files were tracked, against **1166** from earlier
  sprints. Force-added the provenance-and-summary layer (`config.json`, `RUNMETA.json`,
  `metadata.json`, `summary.json`, `DONE.json` across all runs, plus the cited analysis JSONs) —
  **503 files, 5.0 M**, verified to contain 0 row-level files. ⛔ Deliberately **not** tracked:
  `results.jsonl` (49 M), `gens.jsonl` (24 M), `dcs_rowwise_*.json` (136 M).
  ⇒ **Phase headlines are reproducible by rerunning the committed configs on GPU. They are NOT
  recomputable from the repository alone** — `results.jsonl` is what the DiD scripts read, and it is
  not there. Whether to track it is a shared-tree footprint decision, still pending, and explicitly
  **not** a scientific judgement to be made unilaterally.
- **`C-022`/`C-024` — the cost question, answered twice.** `C-022` costed the *marginal* judging spend
  (~$0.08/arm, ~$21 for a 150-domain design) and concluded API budget is not a blocker. `C-024` then
  found the OpenAI account had **no credits** — `C-022` had answered the wrong question. The guard
  worked: the judge pre-flight refused before writing anything, creating 0 directories. The real
  expense throughout is **GPU queue time**, not API spend.
- **`DCS-036`** — the collaborator draft was found **19 result-entries stale**, with two statements
  outright wrong. It is now guarded by a stale-claim sweep that must return zero hits.
- **`C-035`** — the **novelty claim overstated us**, judged by the literature matrix's own bar. A class
  of staleness no number-sweep catches: qualitative prose whose supporting evidence changed underneath
  it.
- **`A-014`/`A-018`** — 4-hourly self reviews; six then seven verifiers re-run green each time, plus a
  5/5 data-mutation audit of the `R-067` analyzer. The pre-commit gate is **9 deliverable guards +
  341 tests** at every commit.
- **`DCS-039`/`C-041`** — wreckage quarantine (never deletion) for partial runs left under a live tag
  prefix, after verifying every consumer filters on `DONE.json`.

**Figures.** `reports/DCS_FIGURES.png` (from `scripts/dcs_figures.py`) has seven panels plus a
**scope card** naming the population (*"38 contexts for a single mapping, not 38 mappings"*), the
figures deliberately **not** drawn and why, and the behavioural status. Four times in the phase,
rendering the PNG and **reading it back as an image** caught something a code diff could not — most
recently `C-044`, where the scope card overflowed into a panel title and *"the per-column width guard
I thought existed"* turned out to be a one-off measurement never committed. The script now parses its
own scope-card columns and **refuses to render** above 48 lines or 50 chars per column ("trim the
text — do NOT just shrink the font"); it was confirmed to fire at 51 lines before passing at 46/45.

---

<a name="10-live"></a>
## 10. Current live state (as of 2026-09-05 19:30) and what happens next

### 10.1 Running now

**6 SLURM jobs, all PENDING (Reason=Priority), partition `killable`: 853040–853045.** Submitted
2026-09-05T19:23:29, `TimeLimit=06:00:00`, 1 GPU each, nodelist `n-[801-805],t-806`. No GPU work has
started; no output directories exist yet. These are the first 6 of **`PR-029`'s 24 new control draws**
(6 at a time, per the standing parallelism rule).

`git log` ends at **8fb3c7e3** (`DCS-C-046`, 19:47), which landed **while this summary was being
written** — this is a **shared tree with concurrent writers**, and the log can move under a reader.
Working tree otherwise clean.

### 10.2 `PR-029` — extend the control population to K = 32

Frozen before the first arm returns; seeds verified distinct from the existing 8 and from each other
(24/24 argsfiles read back).

- **PRIMARY, unchanged from `PR-028`:** `KO-3` against the control distribution, between-control sd as
  the error term, reported raw **and** `R-063`-calibrated, carrying forward `PR-028a`'s shrinkage
  caveat and `R-070`'s anti-conservatism caveat.
- ⛔ **Declared honestly, before the data:** K = 32 is powered for the effect the phase
  **hypothesised**, not the one it **observed** — **0.78** against −0.0391 but only **0.34** against
  −0.0222. ⇒ *A null is the more likely outcome even if a −0.022 effect is real*, and it will be
  reported as **bounding** the effect (MDE 0.0282), never as absence. Detecting −0.0222 would need
  **K ≈ 105 ≈ 240 GPU-h**, which is **not** proposed.
- **Cost:** 24 arms × ~2.3 GPU-h ≈ **55 GPU-h**; then **34 arms** re-judged in **one** session ≈ $8.3,
  ~16 h. ⚠ **Known pending action:** the judge wrapper's `--time=08:00:00` is too short for 34 arms and
  must be raised before submitting — recorded now so it is not discovered at hour eight.
- ✅ **The secondary is arguably worth more than the primary and is guaranteed to deliver**, independent
  of whether the primary clears α: at K = 32 the *distribution* of induced refusal (−7…+562 at
  identical dose on 8 draws) becomes describable — is the +562 arm a tail or a second mode? Is induced
  refusal continuous or bimodal? Does ASR fall off monotonically with it?
- **Declared outcomes:** significant raw **and** across the calibrated `c` range ⇒ the effect is
  established against the comparator population (still does **not** resolve `B-009`'s conjunction);
  significant raw only ⇒ `CONFOUND-LIMITED`; **null ⇒ "effect bounded below 0.028, not absent", and the
  K ladder STOPS here** — the phase moves to the variance problem instead; realised sd materially above
  0.0783 ⇒ even K = 32 is under-sized, stop adding draws, **the comparator itself is the problem**.

### 10.3 Open blockers

| id | status |
|---|---|
| `B-009` | ⛔ **NOT RESOLVED** (`R-061`, 1 of 3). Explicitly not resolved by `R-075` either. |
| `0b-old` | Is the gradient causal? Answered in the categorical form; the continuous version is dead (`R-055`). |
| `B-006` | After `KO-3` the two cells are in different measurement regimes (Llama only, `R-032`); the defense exists and **must be argued in text**. |
| `B-011` | `enable_thinking` not persisted in artifact metadata; recoverable from argv only. |
| `B-012` | Three pre-commit guards scale with **run count** (755 dirs), not the diff ⇒ 30–90 min commits under NFS load. Needs an incremental mode. |
| `B-016` | ⚠ Judge **alias** recorded, never the served **snapshot**. Upstream of this repo; mitigated by before/after probing. |
| `B-002`, `B-003`, `B-004` | No closure marker. `B-003` (the L18 transplant result) is **neither retracted nor re-affirmed and may not be cited**. `B-004`: the topical endpoint is degenerate on these banks. |
| `B-007`, `B-013` | ✅ **CLOSED for behavioural arms** (`R-065`, `R-066`); correctly scoped as still open for **readout** arms. The header table in the log is stale on these two. |
| `B-005`, `B-008`, `B-010`, `B-014`, `B-015`, `B-001` | closed. |

### 10.4 The collaborator draft (`reports/DCS_SLACK_DRAFT_MATAN_MAHMOOD.md`)

⛔ **DRAFT ONLY. NOT SENT.** No Slack integration is configured and none was used; it is to be sent only
on explicit instruction from Omer. Rewritten on 2026-09-05 evening because **the previous draft's
central ask has since been answered in the negative** and must not be sent.

Its current ask, in three parts:
1. *"Last time I said the question was 'can we build controls matched on induced refusal?' We tried,
   and that route is now closed — so the ask has changed."*
2. **The real question: do we keep buying draws, or change the estimand?** Three options tabled —
   (a) the behavioural claim rests on a test we can afford to run; (b) attack the **variance** rather
   than the sample size; (c) **reframe the paper around the representation/behaviour dissociation**,
   which is what the data actually supports.
3. **Positioning:** the representational half replicates Yona et al. (ACL 2026); what is new is the
   causal half. *Frame as a causal follow-up, or hold?*

### 10.5 The continuation plan (`external_md/DCS_CONTINUATION_PLAN_20260905.md`)

Written with `C-046`: **nine ranked experiments**, each with a cost, an independence unit and a kill
criterion. Ranked by information gained per (GPU-h + $); the **top five total ~16 GPU-h and $0**.
⛔ **None is preregistered yet.**

**The central unresolved tension it names:** the representation-level result is large, replicated and
causally clean against its own dose-matched control — *yet the comparator that makes it clean is
behaviourally worthless.* At identical dose the control family's induced refusal spans 25-fold and its
ASR spans 0.126–0.374, so the between-control sd is **three times the effect being sought**, and the
geometry features that would let us match or predict that offset do not exist. The consequence is not
"the attack does not run on the mechanism" — it is that **the only instrument we have for asking has an
error term dominated by an unmodelled property of *which* positions a mask happens to hit.**

| # | experiment | cost | why |
|---|---|---|---|
| **1** | **Split-half reliability + variance decomposition of the draw offset** | **0 GPU-h**, ~1–2 CPU-h | **Gating.** Is the 0.0783 a stable, prompt-independent property of the mask at all? Decomposes it into constant arm offset / arm×domain / Bernoulli residual, with **the judge term measured empirically** from `R-074`'s byte-identical re-judge rather than from a formula. **Kill:** split-half < 0.5 with a CI containing zero ⇒ no stable draw-level quantity ⇒ #7 cannot average it out, #8 cannot predict it, and **stop buying draws entirely.** |
| **2** | **The dissociation as a POSITIVE result**: ρ(per-domain Δ`semantic_logodds`, per-domain Δattack) | **0 GPU-h**, rides `PR-029`'s committed spend | If the attack runs on the remapping, the domains where `KO-3` destroys it most must lose the most attack. Immune to `C-015` because the control enters only as a per-domain **average over 32 draws** — nothing is chosen, so the between-control variance is a term to be **divided by √32**, not tested against. Outcomes frozen in advance, including a **power simulation of the full-mediation ρ as the first deliverable**. |
| 3 | **M1: the dose is attention *mass*, not key count** | ~1 GPU-h | `R-075`'s "identical dose" is `keys_masked` = 522, a **count**; attention is heavy-tailed, so two uniform 522-key draws can remove mass differing by an order of magnitude. `R-076`'s seven features are pure functions of the sorted position list — **the model is never run.** This is the first candidate that asks what the masked positions were *carrying*. |
| 4 | G1: a refusal-free behavioural endpoint (`mapping_use`), eight draws replayed | — | removes the channel that generates the nuisance |
| 5 | G3: constructible-control concept rebuild + a third model family (readout only) | — | widens the half that works |
| 6–9 | judge-free assay of the control spread; row-randomised controls; off-sample draw covariate; exhaustive L6–14 sub-band partition | gated | ⛔ #7–#9 risk real GPU and sit behind gates that read realised sd, cross-fitted R², and a two-cap pilot **before** the primary |

**§5 of the plan — what to do if everything returns null.** *"The paper does not depend on the
behavioural link, and it should stop being written as if it does."* The claim to defend becomes:

> In-context doublespeak installs a codeword→concept remapping whose construction is causally
> localised to demonstration→query attention in a low-layer band — necessary, remapping-specific,
> threshold-shaped, replicating across two model families and two codewords — **and the harmful
> behaviour the paradigm is credited with does not measurably depend on that construction.**

The second clause is worth more than the failed positive **provided it is stated as a measured bound
with a positive test behind it**, not as a failure to reject. Seven things must then be in the paper:
the **bound, not the p-value**; `R-075` as a finding in its own right (a methodological result about
attention-knockout controls that generalises beyond this paradigm); `R-076` as its companion; #2's
positive dissociation if it lands; the variance decomposition (which *"retires the 'just run more
rows' objection in one table"*); **every scope correction in the text, not the appendix**; and a
limitations section naming the paradigm ceiling.

### 10.6 What would change the picture (from the draft's own "what would change your mind")

- ⛔ **Not** new demonstration pools — 116 domains were run and `k` was never the constraint.
- ⛔ **No longer** controls matched on induced refusal — there is no predictor to match on.
- ✅ **A second harmful concept at adequate power** (generality is MIXED, 1 of 2).
- ✅ **An estimator that differences out the refusal nuisance** rather than averaging over it.
- The low-dose question is **closed**: the bank was built, both gates passed, and the continuous
  gradient still failed.

---

<a name="11-verification"></a>
## 11. Independent verification of this document's numbers

Four agents re-checked the headline claims against the producing JSON artifacts and scripts, ran the
tests, re-derived unpersisted quantities, and inspected the live cluster state. Results:

### 11.1 Clean matches (verified end-to-end)

| claim | artifact | verdict |
|---|---|---|
| `R-075` K=8 primary (K, n, ASR, sd, SE, δ, t, p, calibration, shrinkage, all 8 per-control rows, single judge session) | `dcs_pr028_primary.json` + `scripts/dcs_pr028_primary.py` | **MATCH**, including the script's own computed verdict string |
| `R-006` attack DiD (per-cell counts, p = 0.1849, `k_informative = 1`, `UNINFORMATIVE BY CONSTRUCTION`) | `dcs_ko1_ko2_did.json` | **MATCH** |
| `R-041` (ρ_KO, ρ_control, contrast and its permutation p, both models, `binary_split = CANNOT_ANSWER` with `n_low = 1`) | `dcsp17_headline_button_bomb_{llama,qwen}.json` | **MATCH** |
| `R-043` primary (ρ_KO −0.444/0.0049, ρ_ctrl −0.040/0.817, contrast −0.404/**0.0482**) | `dcsp18a_n8_controlled.json` | **MATCH** |
| `R-048` (all 6 controls: induced, face δ/p, bounded δ/p; 6 brackets straddling; secondary rates) | `dcs_pr014_bound.json` | **MATCH**, exactly |
| `R-074` (per-arm flips/net, pooled 5800/728/−54, arm-level t(4)/p/CI, 0 refusal flips) | `dcs_judge_drift_p24j_p28j.json` | **MATCH** |
| `R-076` part 1 (k=8 floor 0.0078, 0 of 4 consistent, 3 degenerate features, Bonferroni α) | `dcs_draw_geometry_refusal_k8.json` | **MATCH** |
| All five TSC headline claim-sets (`R-001` nine p-values + per-pass counts + bands; `R-002` all five arms; `R-004` three contrasts + secondaries; `R-005`/`R-006` + the interaction on both scales; `R-007` attrition) | `outputs/boombness/cds_analysis/tsc*.json`, `data/manifests/tsc_requests_v1_filtered.json`, `outputs/boombness/cds_power/tsc_power_k{8,15}.json` | **MATCH** |
| The 116-domain bank (12,992 rows, 116 domains, 112 rows each, 16 cells, both halves present and disjoint, `pools_sha16` chain intact, **0** plural-`buttons` occurrences, **0** occurrence mismatches across all 12,992 rows) | bank + meta, measured directly from the JSONL | **PASS** |
| `C-037`/`C-037b` fix present at both substitution sites; detector reports 16 collisions pre-repair and **[]** after, residual occurrences **0** across all three fields | `src/boombness/prompt_families.py` | **PASS** |
| `python -m pytest tests/test_incidental_repair_plural.py -q` | — | **4 passed** |
| `scripts/dcs_check_tracker.py` | — | **PASS** |
| The 15-concept AdvBench ceiling and the category-matched anti-tuning statistics (neither persisted in any artifact) | recomputed by re-running the committed filter functions | **reproduce exactly**, including every per-concept count |

### 11.2 Claims with no artifact backing them (not wrong — unverifiable from the repo)

1. **`R-005` and `R-009`'s numbers are not in the artifact the `R-006` entry cites.**
   `dcs_ko1_ko2_did.json` contains **only** the attack-endpoint DiD; it has no representation-channel
   field at all. `R-005`'s `semantic_logodds` figures (+0.278 / −0.085 / **+0.363**, 26+/12−,
   p = 3.36e-02) and `R-009`'s forced-choice DiD (**+0.503**, 25+/13−, p = 7.30e-02) live in the
   `dcsro_C_*` run artifacts, not in any file under `dcs_analysis/`. A grep for `0.503` across that
   directory hits only unrelated files. ⇒ Recomputable from `results.jsonl` by rerunning, not
   locatable as a published analysis JSON.
2. **`R-076` part 2 (the arm-level geometry↔refusal correlation) has no artifact and no code path.**
   `dcs_draw_geometry_refusal_k8.json` has no between-arm block, and
   `scripts/dcs_draw_geometry_predicts_refusal.py` computes only within-prompt Spearman +
   permutation — it never correlates arm-mean geometry against induced refusal. The reported
   ρ = +0.238 (p = 0.589) appears nowhere in the JSON. ⚠ The *inputs* do cross-check: the eight induced
   refusals and the eight `refused` counts in that file match `dcs_pr028_primary.json` exactly.
3. **`R-075`'s power figures are prose-only.** Neither "realised power 0.232" nor the K-ladder is
   computed in `dcs_pr028_primary.py` or stored in its JSON; the script computes only
   `mde = 2.365 × SE`. (The K ≈ 24 figure was itself retracted by `C-045`.)

### 11.3 Documentation defects found (none changes a verdict)

- The DCS log prints `R-041`'s Llama ρ_KO p as **1.0e-04**; the artifact says **1.4999e-04**. The two
  other citations of the same run (which quote the *contrast* p) match.
- The log prints `R-075`'s MDE as **0.0655**; the artifact string says **0.0654** (true value 0.06544).
- `R-076` illustrates `spread_norm`'s inconsistency as "+0.047 … −0.255"; the actual range is
  **+0.2857 … −0.2551** — the sign-inconsistency claim holds, the quoted range understates the positive
  end.
- `dcs_pr028_primary.py`'s frozen docstring still carries the superseded "not significant at K=8 → a
  WELL-POWERED NEGATIVE" branch, which the code no longer implements. The log records this exact defect
  and its fix under `R-075`.
- TSC names the pass-2 analysis file as `cds2j_button_*_domain_test.json`; the file on disk is
  `cds2_button_*_domain_test.json` (its internal provenance points at the right judge dirs).

### 11.4 Freshness and provenance warnings

- ⚠ **The DCS log's own §0 `LIVE STATUS` block is stale** — it is dated **2026-09-04**, before
  `R-062`…`R-076`, `PR-029` and the K=8 result. `reports/DOUBLESPEAK_NEXT_PHASE_SUMMARY.md` **is**
  current through `R-075`/`R-076`, though its header line still says *"Dates 2026-09-02 → 2026-09-03"*.
- ⚠ **The session tracker's "Live" table says "nothing in flight"** while 853040–853045 are queued
  (its row 47 does record the `PR-029` submission as ⏳).
- ⚠ **This document was itself overtaken once during writing.** `C-046` (commit `8fb3c7e3`, 19:47)
  landed after the body was drafted and corrected two claims it contained; §5.3, §5.4, §6.1, §6.2,
  §6.3, §7.6, §10.5 and the appendix were updated. On a shared tree with concurrent writers, **re-read
  the tail of the log before quoting anything from here.**
- ⚠ **The two newest headline artifacts are untracked in git** — `dcs_pr028_primary.json` and
  `dcs_draw_geometry_refusal_k8.json` are not under version control in this tree, so their content is
  not pinned to the commits that describe them (a consequence of the bare `outputs/` gitignore
  documented in `DCS-031`).

---

## Appendix — one-line index of every DCS preregistration and its outcome

| PR | question | outcome |
|---|---|---|
| `PR-001`/`001a` | the `KO-1`/`KO-2` arms and the cell×intervention DiD | `R-006` null on `KO-1`; `KO-2` uninformative (`C-007`) |
| `PR-002` | specificity moved to the readout channel | `R-009` **capable null** at the KO-1 scope |
| `PR-003` | the basket bank's 3-row defect, declared before the outcome | handled; `R-011` replicates |
| `PR-004` | does destroying the mapping move the attack? | `R-012` → **RETRACTED** (`C-015`) → `R-016` positive → direction-only (`R-019`) |
| `PR-005` | replicate judging to settle the magnitude | `R-017`: claim stands at ≈ −30, noise floor ±7 |
| `PR-006` | three new control draws at a second seed | `R-018`/`R-019`: 3 of 6 qualify; direction survives, significance at the domain unit does not |
| `PR-007` | `KO-4` — which query position retrieves? | `R-021`: **no single row carries it** |
| `PR-008` | the row dose-ladder | `R-022`: a **THRESHOLD**, not distributed retrieval |
| `PR-009` | Qwen3-14B replication, staged | `R-023` gate passes; `R-024`/`R-025` replicate **in sign and domain split** (⛔ no magnitude ratio, `C-046`) |
| `PR-010` | the formal model × endpoint interaction | `R-029` **CANNOT ANSWER** (0 of 6 draws qualify) |
| `PR-011` | coarse layer sweep | `R-030`: localised; inherited band best of four |
| `PR-012` | equal-width layer sweep | `R-031`: **distributed across 0–14**, peak 10–14 |
| `PR-013` | generality to a 2nd and 3rd concept | `R-035` **MIXED**, 1 of 2 |
| `PR-014` | the Qwen behavioural contrast, by bounding | `R-048` **CONFOUND-LIMITED** |
| `PR-015` | layer placebo + dose test | `R-037` **INTERMEDIATE**; `R-038` excuse **not supported** |
| `PR-016` | is the effect graded by installation, out of sample? | `R-040` **RANGE-LIMITED** |
| `PR-017` | the gradient on the headline populations with the real control | `R-041` ✅ **SUPPORTED** on the blind primary |
| `PR-018`/`018a` | **manipulate** installation | `R-042` predictions **VOID**; `R-043` replicates at a 2nd dose |
| `PR-019`/`019a` | is installation predicted by prior plausibility? | `R-045`/`R-047` **CANNOT ANSWER** on this instrument family |
| `PR-020` | the judge noise floor on the attack rubric | `R-049`: 18/380 (net +6); `refused` 0/380 |
| `PR-021` | the never-run `benign_literal` cell | `R-050` primary **CANNOT ANSWER**; the arm is valuable anyway |
| `PR-022` | attack `C` on Qwen at n = 30 | `R-053` **NULL branch** — the power defence dies |
| `PR-023` | the purpose-built low-dose block | `R-054` both gates pass; `R-055` **NULL branch** — attack `C` fails a third time |
| `PR-024`/`024a` | `B-009` at 116 domains | `R-061` **NOT RESOLVED**, 1 of 3 |
| `PR-025` | is the refusal confound quantifiable? | `R-062`: regular in direction, **not** in magnitude (conversion 0.057–0.350) |
| `PR-026` | a conversion-calibrated bracket, applied symmetrically | `R-063`: entirely negative for all three, **half the width** |
| `PR-027` | attack `C` at 116 domains, staged on a gate | `R-064` **STOPS at Stage 1** — the ceiling is a **paradigm** property |
| `PR-028`/`028a/b/c` | treat the control draw as a random effect (K = 8) | `R-075` **UNDERPOWERED NEGATIVE**; `R-074` drift **NOT ESTABLISHED** |
| `PR-029` | extend the control population to K = 32 | ⏳ **live** — 24 draws submitted (853040–…) |

| TSC PR | question | outcome |
|---|---|---|
| `TSC-PR-001` | `basket↔bomb` lexical replication | `R-004` **REPLICATED** |
| `TSC-PR-002` | judge robustness | `R-001` **CONFIRMED** |
| `TSC-PR-003` | Qwen3 Stage-1 baseline screen | `R-003` **PROCEED** |
| `TSC-PR-004` | Qwen Stage-2 + the model × intervention interaction | `R-005` **CAPABLE NULL** / **MODEL-SPECIFIC** |
| `TSC-PR-005` | the request-diverse bank, drawn blind | population drawn; blocked at `TSC-Q-001` |
| `TSC-PR-006` | the structurally active matched control | **PREREGISTERED, EXECUTION DEFERRED** |
| `TSC-PR-007` | the mechanical constructibility filter | `R-007` **DECLINED FOR POWER** (8 of 40) |
