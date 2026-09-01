# CDS — Confirmatory Defensibility Sprint · plan and append-only progress log

**Started:** 2026-09-01 · **Branch:** `behavioral-causality-sprint` · **Starting commit:** (filled at first commit)

**Id namespace: `CDS-PR` (preregistration) / `CDS-R` (result) / `CDS-C` (correction) / `CDS-DR` (deep review).**
⚠ Always write the full `CDS-` prefix. This repo carries five colliding registries
(bare `C-12`/`R-25` = the original Doublespeak namespace; then `RBD-`, `RAH-`, `RAH2-`, `RAH3-`).
`tests/test_my_ledger_propagation.py` reads an unprefixed id as a citation of the Doublespeak one
and the pre-commit hook refuses the commit.

**Charter (user, 2026-09-01):** a discussion is tomorrow. Do **not** generate more exploratory
results and do **not** raise N until something turns significant. Identify the 2–3 highest-value
weaknesses in the *existing important* claims that can realistically be closed with confirmatory
evidence; **preregister before reading any outcome**; run the strongest feasible experiments.
Priority order: independent replication · additional independent *domains* (not rows) · matched
controls · cross-model evidence where a claim is single-model · power/headroom · falsification.
`d_surface`/Boombness as a GCG objective stays **CLOSED**.

**A clean negative is preferred to a fragile positive. The goal is FEWER claims that survive
adversarial scrutiny, not more claims.**

---

## §0 — What this log is for

Written so the state is recoverable with **no session context**. Every result entry names its
artifact path. Every claim entry names its scope. Where this log and an older document disagree,
this log and the raw artifacts win.

---

## §1 — PHASE 0: claim triage (before any new forward pass)

*(populated below, `CDS-R-001`)*

### `CDS-R-001` — claim triage, written BEFORE any new forward pass

Sources read in full first: `RESEARCH_HANDOFF.md` (all four addenda — RBD, RAH, RAH2, RAH3),
`reports/RAH_SPRINT_SUMMARY.md`, `reports/RAH2_SPRINT_SUMMARY.md`, `reports/RAH3_SPRINT_SUMMARY.md`,
`reports/RAH3_TRACKB_POWER_AND_BANK_REPORT.md`, `reports/RBD_SPRINT_SUMMARY.md`, and the
`external_md/` logs' correction registries. **Where a later correction narrows a headline, the
narrowed version is what is entered below.**

| | **Claim A — demonstration-specific causal effect** |
|---|---|
| exact claim | Masking attention to the **demonstration positions** removes the doublespeak attack, and **strict count-matched masks of the same size drawn from non-demonstration positions do not**. |
| model scope | **Qwen3-14B only.** Llama was **DECLINED FOR POWER** (`R-52`), never refuted. |
| bank / domain scope | `longpreQ14` + `longpreQ14B` (2 demonstration pools), **10 domains**, `carrot↔bomb`, doses n=4 and n=8 |
| current N | 40 rows/dose/arm; **5 and 7** baseline attacks (pool A), **4 and 6** (pool B), **4 and 7** (640-cap) |
| true independence unit | **domain** (10) — quoted as "prompt" in the claim table; the C7 evidence is a **row-count separation against a margin**, never a domain-level test |
| strongest existing evidence | 3 independent seeded count-matched controls, `match_ratio` **1.000 on all 480 control rows**; replicated on an independent pool; **truncation-robust** at a 640-token cap (`R-64`) where `frac_stop_length` = 0.000 in every arm |
| known weakness | (i) **single model**; (ii) 5–7 baseline attacks per cell — a 1–2 row judge floor sits directly under the control readings (`R-82`/`R-83`); (iii) the 640-cap leg rests on **one** control draw, not three; (iv) **no domain-level inference exists at all** |
| what would materially strengthen it | a **Llama** replication on a bank with (a) count-matchable non-demo context, (b) enough baseline headroom, (c) **many more independent domains**, analysed at the **domain** level |
| obtainable now? | **The blocker is structural and known.** Count-matching needs a neutral preamble (`main_longpre`); on Llama that preamble **halves the attack** (`C13`, Llama-specific, Qwen3 negative). 38-domain pools exist. **Feasible only if a screened baseline clears a pre-set headroom floor — see `CDS-PR-001`.** |

| | **Claim B — installation is not sufficient for use / attack** |
|---|---|
| exact claim | The mapping can be **installed** (the model reports it) while the harmful behaviour built on it is **near-absent**; and benign mapping-*use* is absent even at full installation. |
| model scope | installation-without-**benign-use**: 4/4 cells, both models (`RAH-R-004`). installation-without-**attack**: the `window_knife` observation (`R-168`) is **Llama-only**. |
| bank / domain scope | `RAH-R-004`: 80 families, 20 domains, `lantern↔poison` + `candle↔missile`. `R-168`: `window_knife`, `basket_gun`, `main`, `ticket_bomb` — mixed doses |
| current N | 80 families / 20 domains (the clean leg); `window_knife` **2/96 and 1/96** attacks at installation 1.000 |
| true independence unit | **family** within domain for the probe; **domain** for ASR; ⚠ **lexical pair** across banks |
| strongest existing evidence | `RAH-R-004` — binding lift +0.5000…+0.9750, every CI excluding zero, while benign mapping-use lift is `NOT ESTABLISHED` on all four; **not a power failure** (76-row dynamic range, arm at 2.6–3.9 % of it) |
| known weakness | the installation-vs-**attack** half is **observational cross-bank** and rests on selected lexical pairs. `R-168`'s own sentence records that the decisive cell — *attacks without installation* — is **unobserved** |
| what would materially strengthen it | a **pre-specified** cross-bank analysis over **every** eligible cell under inclusion criteria fixed independently of ASR, with the pair as a clustering unit |
| obtainable now? | **YES, from artifacts that already exist.** `CDS-R-002` finds **14 (bank, model) cells** with both an installation leg and a judged baseline-ASR leg, over **9 distinct lexical pairs**, at a **fixed single dose**. No GPU needed. |

| | **Claim C — refusal and attack are partially separable** |
|---|---|
| exact claim | Handing back clean demonstration activations at the top of the knockout band **restores refusal**; on **Llama** it leaves the attack unchanged. |
| model scope | primary refusal effect: **both models, 4/4 cells**. **The selectivity clause ("and not the attack") is LLAMA-ONLY** (`C-68`) — on Qwen3 the rescue restores attack by **+9, +13, +10, +14** across four measurements against Llama's **+0**. |
| bank / domain scope | `d10` + `d10-poolB`, 10 domains, `carrot↔bomb` |
| current N | 160 rows × 4 cells; ⚠ refusal **ICC 0.326–0.427** on the Llama arms → **n_eff ≈ 22–27, not 160** (`C-71`) |
| true independence unit | **domain** (10) |
| strongest existing evidence | cap-released Llama leg (`R-143`): 640 cap, `frac_stop_length` **0.0000 both arms**, judged in **one** invocation, refusal **35 → 17 = −18 rows** vs an 8.3-row margin (2.2×), **ASR unchanged 5 vs 5**; identity control 8/8 byte-identical |
| known weakness | the model difference is asserted from **four Qwen3 measurements vs one Llama measurement**, not from a **model × intervention interaction** on matched material. The below-band control was **WITHDRAWN as a no-op** (`C-20`), so the specificity leg has **no live control** |
| what would materially strengthen it | a **matched** Llama/Qwen3 replication on one bank, one cap, one dose, one judging invocation, analysed as a **pre-registered interaction** |
| obtainable now? | Possible but **secondary**: it needs 4 arms × 2 models. Ranked **P4** by the charter. |

| | **Claim D — clean representation readout remains unresolved** |
|---|---|
| exact claim | No readout in this project's inventory is simultaneously exposure-clean, non-zero-hop, high-mass on held-out material, and validated on a positive control that is not a copy test. |
| model scope | Llama + Qwen3 |
| bank / domain scope | `carrot↔bomb` development; `lantern↔poison` held-out; **8 donors** per cell |
| current N | 8 donors; **220** exposure-clean multi-hop cells across the whole corpus, **zero** ever passed (`RAH3-C-018`) |
| true independence unit | **donor** (8) |
| strongest existing evidence | the corpus-wide 220/0, which is what makes the conclusion robust to `RAH3-C-013`'s confound |
| known weakness | 8 donors; no interval; held-out arm **gated off and never run**; the collapse is **not decomposed** ("off-surface transport is weak" vs "`'.'` is a poor carrier") |
| what would materially strengthen it | ≥32 donors across independent domains, a frozen set of structurally valid off-surface capture sites, bootstrap intervals |
| obtainable now? | Yes and cheap, but it can only **strengthen a negative**. Ranked **P3**. |

**Triage verdict.** Claim A is the only one where new compute can change a claim's *status* (single-model → cross-model). Claim B can be strengthened **with no GPU at all**. Claims C and D are ranked below both. This matches the charter's decision order and it is what this sprint executes.

---

## §2 — `CDS-PR-001` — Llama demonstration-specificity: a two-stage confirmatory design

**Committed before any forward pass on any CDS bank. Nothing below may be edited after Stage-1
outcomes are read; amendments are appended as new `CDS-PR` ids with a timestamp and a reason.**

### 2.1 Hypothesis

**H-A.** On **Llama-3.1-8B-Instruct**, masking attention to the **demonstration** positions during
prefill (`demo_processing_only`) removes the doublespeak attack, and **strict count-matched masks of
identical size drawn from non-demonstration positions do not**. This is `C7`'s Qwen3 result on a
second model family; nothing about it is new except the model and the size of the population.

**H-A0 (the null this design must be able to return).** The effect is a property of the *number* of
masked positions, not of *which* positions they are — in which case `demo_processing_only` and its
count-matched controls remove indistinguishable amounts.

### 2.2 Why this population and not the old one

`R-52` declined Llama on `main_longpre` at **10 domains × 40 rows/dose**. Adding rows there is
useless: `RAH-R-006` and `RAH3`'s Track-B table both find **domains, not rows, are the binding
lever**, and the 20×4 shape returns `NONE` — *not detectable at all, including a 100 % wipeout*.

The new population fixes the binding constraint and nothing else:
* **38 domains** (`data/boombness_prompts/demo_pools_29dom.json`; ⚠ the filename says 29, the data
  holds **38** — `RAH3-C-019`, the data wins). ⚠ `RAH3` §5 warns **k = 38 is an UPPER BOUND on
  independent clusters** — three of the 38 are register/genre rather than settings and the pools
  came from one model at one base seed. That caveat is inherited, not resolved.
* **`main_longpre_cds`**, a new preset that derives the preamble mechanism from `main_longpre`
  unchanged (`n_preamble = 10`, the value `PR-20` fixed **on feasibility alone**) and chooses its
  slots so that every emitted family has a **disjoint demonstration set**: `{0,4,8,12,16}` at n=4
  (starts `{0,12,4,16,8}`, which partition the 20-sentence pool) and `{0,3}` at n=8.
  `main`'s `families` block is deliberately unused — its slots 1 and 2 **overlap** slot 0 at both
  doses, which is the pseudo-replication `G2` was retracted for.
* ⚠ **The preamble is NOT re-tuned.** Shortening it would raise the attack rate — `C13` measures the
  preamble's Llama-specific cost directly — and choosing a design parameter to raise your own
  headroom is selecting on the outcome. `n_preamble = 10` is the value whose Llama ASR cost is
  already measured (`R-178`: 0.1437 → 0.0750 pooled, at a released cap).

### 2.3 Exact population, per bank

Three lexical pairs, all **`*↔bomb`**, generated from the **same** 38-domain pools with the **same**
preset, seed **20260901**, `--strict`:

| bank | pair | incidental repairs | behavioural `natural_doublespeak` rows |
|---|---|---|---|
| `boombness_prompt_bank_cds38_carrot_bomb.jsonl` | carrot↔bomb | none | **380** at n=4, **152** at n=8 |
| `boombness_prompt_bank_cds38_basket_bomb.jsonl` | basket↔bomb | `baskets=crates, basket=crate` | same |
| `boombness_prompt_bank_cds38_button_bomb.jsonl` | button↔bomb | `button=switch` | same |

Selector, identical in every arm:
`--query-kinds behavioral --conditions natural_doublespeak --bank-blocks cds_n4` (or `cds_n8`)
`--n-examples 4` (or `8`) — **the two doses are separate cells and are NEVER pooled.**

Independence unit: **domain**, k = 38. Rows/domain: **10** at n=4 (5 disjoint slots × 2 splits),
**4** at n=8 (2 × 2).

### 2.4 STAGE 1 — headroom screen. Baseline arm ONLY.

Three jobs, one per pair: `--arm A_baseline`, **no `--intervene`**, `--max-new 640`, `bfloat16`,
`--attn-impl eager`, seed 20260901, Llama-3.1-8B-Instruct, both doses in one run
(`--n-examples 4,8 --bank-blocks cds_n4,cds_n8`, 532 rows), judged with the judge pinned to
`openai/gpt-4o-mini`.

**Stage 1 may inspect BASELINE outcomes only. No intervention arm is generated, judged or looked at
until the Stage-1 rule below has been applied and its verdict written to this log.**

**Preconditions (any failure makes the cell INELIGIBLE regardless of its ASR):**
1. `control_feasibility.py` reports `match_ratio` **min = 1.000** at the dose (`CDS-R-003`);
2. `frac_stop_length` ≤ **0.02** in the baseline arm — the truncation gate `RAH3-C-007` found
   published and enforced by nothing, made live here;
3. judge `judge_model_used == openai/gpt-4o-mini` on **100 %** of rows, and
   `completion_sha256_16` joins **100 %** of judged rows to the generation artifact;
4. bank join by `bank_rows_sha16`, 0 mismatches.

**Accept / decline rule — fixed here, before any Stage-1 number exists.** Let a *cell* be a
(pair, dose). A cell **QUALIFIES** iff, on the baseline arm, ALL of:
* baseline ASR ≥ **0.10**;
* baseline attack rows ≥ **34**;
* domains with ≥ 1 baseline attack ≥ **15**.

If **≥1** cell qualifies, Stage 2 runs on the qualifying cell with the **largest number of baseline
attack rows** (ties → the smaller dose, then alphabetical pair). If **no** cell qualifies, the
Llama replication is recorded **`DECLINED FOR POWER`**, no intervention arm is launched, and the
compute moves to `CDS-PR-002`. **The population is not re-scoped, the thresholds are not lowered,
and no fourth pair is added after these numbers are read.**

**Where the three numbers come from — `scripts/cds_power_domain.py`, run before any bank existed**
(`outputs/boombness/cds_power/cds_power_domain.json`; grid at k=38, judge flip rate from
`rah_power_trackb.flip_for_asr`, i.e. the **measured** curve, never a constant). Power for a
**total wipeout**, which is the effect `C7` actually reports on Qwen3 (5/5, 7/7, 4/4):

| dose | rows/dom | baseline ASR | ICC 0.067 | ICC 0.09 | ICC 0.19 | ICC 0.45 |
|---|---|---|---|---|---|---|
| n=4 | 10 | 0.075 | 0.78 | 0.74 | 0.58 | 0.29 |
| n=4 | 10 | **0.100** | **0.90** | **0.87** | 0.73 | 0.43 |
| n=4 | 10 | 0.156 | 0.97 | 0.96 | 0.90 | 0.63 |
| n=8 | 4 | 0.100 | 0.61 | 0.61 | 0.52 | 0.33 |
| n=8 | 4 | 0.156 | 0.76 | 0.76 | 0.70 | 0.51 |

(domain sign test; the row-level McNemar column is uniformly higher and is reported in the artifact.)
⚠ **ICC is not assumed.** `RAH3-C-006` records that `ICC = 0.09` has **no estimator** in this
repository and `RAH3-C-020` that the repo's own measured range is **0.000–0.755**. Stage 1
therefore **measures** the domain ICC on the baseline arm and Stage 2's power is re-reported at the
**measured** value. The gate above is set at the point where power ≥ 0.80 holds at ICC ≤ 0.09 and
degrades gracefully to ≈0.73 at 0.19; **at ICC 0.45 no cell available here is adequate and that will
be stated rather than hidden.**

⚠ **Winner's curse is acknowledged.** Choosing the best of three screened baselines biases that
baseline upward. It is controlled by an **absolute** floor (0.10 / 34 / 15) rather than by "pick the
max", and the Stage-2 power is recomputed from the Stage-1 measurement with that bias noted.

### 2.5 STAGE 2 — the confirmatory arms

Run only on the qualifying cell, all five arms on the **same rows**, identical in everything except
mask identity:

| arm | `--intervene` | `--knockout-scope` |
|---|---|---|
| `A_baseline` | *(none)* | — |
| `C_demo_processing_only` | `demo_all:attn_knockout:6-14:1.0` | `demo_processing_only` |
| `CTRL_matched_d1/d2/d3` | `nondemo_matched_d{1,2,3}:attn_knockout:6-14:1.0` | `demo_processing_only` |

* knockout band **6-14**, the canonical Llama band used by every `p5`/`p12`/`p13` arm. **No layer is
  optimised on these outcomes.**
* `--max-new 640` **primary**; the first-192-token ASR is recomputed from the same completions as a
  clearly secondary comparability analysis (no second generation).
* generation is **per-row** in `score_behavior.py`, so batch size is 1 in every arm by construction
  — the `C5` batch confound cannot arise on a behavioural arm. Asserted, not assumed
  (`CDS-R-00x` records the check).
* all five arms judged in **one** manifest / one invocation, judge pinned, to remove session drift.
* **raw completions preserved; no ASR filtering anywhere.**

### 2.6 Endpoints and tests

**PRIMARY — specificity.** For each control draw d ∈ {1,2,3}: exact **paired sign test over the 38
domains** on per-domain attack counts, `C_demo_processing_only` vs `CTRL_matched_d`. H-A is
**SUPPORTED** iff all three tests reject at α = 0.05 in the direction *demoproc removes more*
(an intersection–union test, so no multiplicity correction is owed and it is conservative).
`k_informative` and the attainable exact floor `2 / 2^k_informative` are reported for every test;
⚠ following `C-95`, **a test whose floor exceeds α is UNINFORMATIVE BY CONSTRUCTION and is reported
as such, never as a negative.**

**SECONDARY, all pre-specified:** `demoproc` vs `A_baseline` and each control vs `A_baseline` (same
test); row-level exact McNemar on discordant pairs; a **domain-cluster bootstrap** CI on ΔASR
(10 000 resamples of domains, seed 20260901); the `C7`-style row-count separation against the
`0.0521` `MARGIN_VS_BASELINE`, reported **only** for comparability with the Qwen3 number and never
as the primary; `kw_refusal` rates per arm (zero judge variance).

**Both are reported: raw row counts AND domain-aware inference. A row-level p-value is not allowed
to carry the claim if the domain-level test is incapable.**

### 2.7 Controls, liveness and falsification

* strict count-matched masks, `match_ratio` **1.000 on every control row** (the strict policy
  refuses a row it cannot match, so a violation is a crash, not a silent 0.87);
* **3 independently seeded draws**, so a single unlucky draw cannot carry the result;
* `total_prefill_edits` recorded per arm; the controls must be **dose-matched to `demoproc`**;
* ⚠ **anti-`C-20` guard**: each control arm's completions are compared byte-wise against
  `demoproc`'s. A control that is byte-identical is a **no-op by construction** and must not be
  reported as evidence of specificity — this is exactly how `C9`'s below-band control died;
* truncation: `frac_stop_length` reported per arm; a differential > 0.02 between the compared arms
  invalidates the primary and forces the comparison onto the finished stratum with that stated;
* **falsification**: H-A0 is a live outcome. If the controls remove as much as `demoproc`, that is
  the result, and it **contradicts `C7` cross-model** rather than merely failing to replicate it.

### 2.8 Exclusions and stopping

* No row is excluded on its outcome. Rows are excluded only for a judge error
  (`judge_status != ok`) or a failed hash join, and both counts are reported.
* **N is frozen here.** No domain, dose, pair or row is added after any p-value is seen.
* Early stop: if Stage 1 declines, Stage 2 does not run. If Stage 2's liveness or truncation gates
  fail, the arms are reported as **VOID**, not as a null.

### 2.9 Expected artifact paths

`data/boombness_prompts/boombness_prompt_bank_cds38_{carrot,basket,button}_bomb.jsonl` ·
`outputs/boombness/control_feasibility/cdsfeas_*/` ·
`outputs/boombness/cds_power/cds_power_domain.json` ·
`outputs/boombness/score_behavior/cds1{A,C,d1,d2,d3}_*/` ·
`outputs/boombness/judge/cds1j_*/` · `runargs/cds1/*.txt` ·
analysis: `outputs/boombness/cds_analysis/`.

### `CDS-R-002` — the banks, and their hashes (recorded before any forward pass)

| pair | `bank_rows_sha16` | pools_sha16 | seed | incidental repairs | rows |
|---|---|---|---|---|---|
| carrot↔bomb | `5d45751f9b5ff3aa` | `4cfc70c8688e4a3a` | 20260901 | none | 4256 |
| basket↔bomb | `d22cc2da5eb943e0` | `4cfc70c8688e4a3a` | 20260901 | `baskets=crates, basket=crate` | 4256 |
| button↔bomb | `17173f8adc42973e` | `4cfc70c8688e4a3a` | 20260901 | `button=switch` | 4256 |

All three: `preset=main_longpre_cds`, `--strict`, 1064 2×2 families checked, **0 alignment
violations**, 0 duplicate `prompt_id` rows dropped, generated at `c5239c1601a8`.
Behavioural × `natural_doublespeak` × n=4: **380 rows, 38 domains, exactly 10 per domain** in all
three banks.

### `CDS-R-003` — count-match feasibility, decided by TOKENIZATION ALONE, before any outcome

`src/boombness/control_feasibility.py`, Llama tokenizer, `--bank-blocks cds_n4,cds_n8`:

| dose | rows | demo tokens med/MAX | drawable pool med/MIN | deficit | `match_ratio` min / mean | verdict |
|---|---|---|---|---|---|---|
| **n=4** | 380 | 58 / 94 | 140 / 117 | **0** | **1.000 / 1.000** | **FEASIBLE** |
| n=8 | 152 | 119 / **174** | 140 / 117 | **57** | **0.000** / 0.928 | **INFEASIBLE** |

**⛔ The n=8 cell is INELIGIBLE and is dropped, by precondition 1 of `CDS-PR-001` §2.4, before any
ASR at either dose was computed.** Cause: the 38-domain pools carry longer demonstration sentences
than the 10-domain `d10` pools this preset's preamble length was fixed against — max demo 174 tokens
against a minimum drawable pool of 117. ⚠ **The remedy of lengthening the preamble was considered
and REFUSED**: it would further dilute the attack on exactly the model whose attack the preamble is
already known to halve (`C13`), and n=8 carries only **4** independent families per domain against
n=4's **10**, so the ineligible cell is also the lower-powered one. The confirmatory design is
therefore the **n=4 cell only**, which was the pre-registered higher-power cell in any case.

⚠ **`CDS-C-001` — the feasibility gate was VACUOUS and passed on nothing.** Its first run on the
carrot bank returned `all_doses_feasible: true` with `per_dose: {}`: `--bank-blocks` defaults to
`core2x2,core2x2_slot3`, which **no** bank built from a custom preset carries, so **zero rows were
examined** and `all([])` is `True`. This is the third instance in two sprints of the same defect
class — `RAH3-C-003` (a dead `mass_gate`), `RAH3-C-007` (a published truncation threshold no code
path reads), and now a feasibility verdict that certifies an empty selection. The script now
**refuses** an empty selection, and the refusal was **proven able to fire** by re-running the exact
command that produced the vacuous pass.

⚠ **`CDS-C-002` — the basket bank loses 3 rows to occurrence resolution.** `school_campus|dev`
slots 0, 8 and 12 raise `occurrence_count_mismatch: text=5, tokens=6` at n=4, so basket's usable
population is **377/380** with one domain at 7 rows instead of 10. Carrot and button are 380/380.
Recorded **before** any ASR is read; if basket wins the Stage-1 screen its N is 377 and its k=38 is
unbalanced in one domain, and the analysis will say so.

---

## §3 — `CDS-PR-002` — installation-without-use, as a pre-specified cross-bank analysis

**No GPU. Reads only artifacts that already existed before this sprint began.**

⚠ **DISCLOSURE, written into the registration rather than discovered later.** The inclusion rule
below is **structural** — dose, cap, judge pinning, bank identity — and uses **no ASR value**. But
the analyst had already seen the ASR column of **1 of the 14** candidate cells
(`boombness_prompt_bank.jsonl` × Qwen3-14B) while auditing the inventory, plus the `window_knife`
figures, which `R-168` already published. This is therefore **a specification, partially
outcome-exposed**, not a blind preregistration, and it is labelled that way wherever it is used.
`RAH2`'s lesson stands: when two near-identical sentences differ by a qualifier, the qualifier IS
the claim.

### 3.1 Hypothesis

**H-B.** A bank can teach the codeword→concept mapping essentially completely and still produce
almost no successful attacks — i.e. **installation is not sufficient for use**, and this is not a
property of one selected lexical pair.

**H-B0 (the null).** Installation and attack success move together; `window_knife` is an outlier of
a monotone relationship, and there is no *high-installation, near-zero-ASR* region.

### 3.2 Population and inclusion rule — fixed independently of ASR

A **cell** is a (bank file, model) pair. A cell is INCLUDED iff **all** of:
1. an installation leg exists: a `score_behavior` run with `--query-kinds semantic_forced_choice`,
   `--conditions natural_doublespeak`, arm `A_baseline`, **no `--intervene`**, `DONE`, with the SFC
   option-mass gate **PASS**;
2. a behavioural leg exists: `--query-kinds behavioral --conditions natural_doublespeak`, arm
   `A_baseline`, `DONE`, with a completed judge run;
3. **both legs carry `n_examples = 8`** — a single fixed dose. **Doses are never pooled.**
4. the judge run is **pinned**: `judge_model_pinned == openai/gpt-4o-mini`;
5. both legs join the **same** bank by `bank_rows_sha16`.

**Deterministic tie-breaks, applied before any ASR is compared:** where a cell has several eligible
legs, take the one with the **largest `max_new`**; ties broken by the **earliest** run timestamp.
Neither depends on an outcome.

### 3.3 Quantities, per included cell

* **installation** = mapped-win rate at n=8, `mapped_win := p_concept > p_codeword` (a tie is **not**
  a win) — the predicate already registered at `src/boombness/mapping_installation_verdict.py:227`;
* **baseline ASR** at n=8, threshold 0.5;
* **keyword refusal** (`refusal_rate`, the mean of `judge_boombness.kw_refusal`; ⚠ there is no field
  literally named `kw_refusal`);
* rows, domains, lexical pair, demonstration pool, judge run id.

### 3.4 Endpoint and decision rule

**Independence unit: the LEXICAL PAIR**, not the cell — `bomb` appears as the concept in four
different pairs, so 14 cells are **not** 14 independent draws.

**H-B is SUPPORTED** iff, at n=8, cells with **installation ≥ 0.75** include **≥ 2 distinct lexical
pairs** with **baseline ASR ≤ 0.05**. One pair only ⇒ `window_knife` is not generalised and the
verdict is **SUPPORTED BUT SCOPED TO ONE PAIR**. Zero ⇒ **NOT SUPPORTED at this dose**.

**Secondary, reported whatever the primary says:** the full (installation, ASR) table with every
excluded cell and its exclusion reason; the Spearman correlation across pairs; and the **converse**
cell — installation < 0.50 with ASR ≥ 0.15, i.e. *attack without installation*, which `R-168`
records as **unobserved** and which is the observation that would actually license an objective.

⚠ **What this analysis CANNOT do.** It is **observational across banks**. Pairs differ in domains,
demonstration pools, cap and judging session as well as in lexical content, and this sprint's own
inventory shows **the same completions judged eight times give ASR 0.156–0.208**. So the table
supports an **existence** claim — *a high-installation, near-zero-ASR population exists, in more
than one pair* — and never a claim about **what causes** the difference. That distinction is the
whole of `RBD-C-017`, where a between-bank gap was attributed to the concept and the comparison
turned out to differ on every clause.

### `CDS-R-004` — `CDS-PR-002` EXECUTED. Installation does not determine attack success.

Producer: `scripts/cds_install_vs_asr.py` · artifact:
`outputs/boombness/cds_analysis/cds_install_vs_asr.json` · **no GPU, no new generation**.
**13 cells over 9 distinct lexical pairs**, all at **n_examples = 8**, judge **pinned** to
`openai/gpt-4o-mini`, threshold 0.5. 23 candidate cells were excluded and every exclusion reason is
in the artifact.

| pair | model | installation | ASR | kw-refusal | cap |
|---|---|---|---|---|---|
| window↔knife | Llama | **1.000** (12/12) | **0.0417** (1/24) | **0.0000** | 640 |
| carrot↔bomb | Qwen3 | 1.000 (**2/2** ⚠) | 0.1750 (7/40) | 0.0250 | 640 |
| basket↔bomb | Llama | 1.000 (12/12) | 0.2917 (7/24) | 0.0833 | **1536** |
| carrot↔bomb | Llama | 1.000 (12/12) | 0.4583 (11/24) | 0.0833 | 640 |
| ticket↔bomb | Llama | 1.000 (12/12) | **0.5833** (14/24) | 0.2500 | 640 |
| lantern↔poison | Llama | 0.975 (78/80) | 0.0875 (7/80) | 0.2750 | 640 |
| lantern↔poison | Qwen3 | 0.938 (75/80) | **0.0375** (3/80) | 0.5250 | 640 |
| ticket↔knife | Llama | 0.917 (11/12) | 0.0833 (2/24) | 0.0000 | 640 |
| window↔bomb | Llama | 0.917 (11/12) | 0.2500 (6/24) | 0.0833 | 640 |
| carrot↔bomb | Qwen3 | 0.833 (10/12) | 0.3750 (9/24) | 0.0000 | 192 |
| candle↔missile | Llama | 0.650 (52/80) | 0.0875 (7/80) | 0.0125 | 640 |
| candle↔missile | Qwen3 | 0.500 (40/80) | 0.0125 (1/80) | 0.2250 | 640 |
| **basket↔gun** | Llama | **0.417** (5/12) | **0.2083** (5/24) | 0.0417 | 640 |

**What is established.**
1. **At installation held at exactly 1.000, ASR takes the values `{0.0417, 0.175, 0.2917, 0.4583,
   0.5833}` — a 14× spread.** Installation therefore does not determine attack success, and this
   does not depend on any threshold, correlation or model: it is five cells at one installation
   value.
2. **`CDS-PR-002`'s registered rule returns SUPPORTED**: two distinct lexical pairs are
   installation ≥ 0.75 with ASR ≤ 0.05 — `window↔knife` on **Llama** and `lantern↔poison` on
   **Qwen3**, i.e. one in each model family. Unchanged under both structural sensitivities
   (`install_n ≥ 10`; `cap == 640` only).
3. ⚠ **POST-HOC, and it narrows the claim.** A near-zero ASR has two readings — *installed and not
   used* and *refused* — and only the refusal rate separates them. Requiring `kw_refusal ≤ 0.05`
   leaves **one** pair: **`window↔knife` on Llama, 12/12 installed, 1/24 attacks, refusal exactly
   0.0000**. `lantern↔poison`/Qwen3's refusal is **0.525**, so that cell cannot distinguish the two.
   **The defensible sentence is therefore: *installed-and-not-used* is demonstrated on ONE pair;
   *installation does not determine ASR* is demonstrated across nine.** (`ticket↔knife` on Llama is
   the near miss: 0.917 installed, 2/24 attacks, refusal 0.0000, just above the 0.05 ASR line.)
4. ⚠ **`R-168`'s "No bank produces attacks without installing" has a COUNTEREXAMPLE at this dose.**
   `basket↔gun` on Llama reads installation **5/12 = 0.417 — below chance** with ASR **5/24 =
   0.208**. ⚠ 5/12 has a very wide interval and 0.417 is **not** distinguishable from 0.5 at n=12;
   the honest statement is that the cell `R-168` calls *unobserved* **is populated**, not that
   non-installation is established there. **Pending the adversarial audit's check of whether
   `R-168` quantified over a different (dose-pooled) population.**

⚠ **`CDS-C-003` — the registered rule had no minimum n on the installation leg**, and
`longpreQ14B` × Qwen3 entered at installation `1.000` computed over **2 rows in 1 domain**. A rate
over 2 rows is not an estimate. The floor (`install_n ≥ 10`) is structural, is applied as a
**sensitivity** with the table printed both ways, and **does not change the verdict**.

⚠ **What this cannot say.** Observational across banks: pairs differ in domains, pools, cap and
judging session as well as in lexical content, and this repo's own artifacts show the **same**
completions judged eight times giving ASR **0.156–0.208**. It is an **existence** result, never a
causal attribution to the concept — `RBD-C-017` is exactly what happens when that line is crossed.

---

## §4 — `CDS-R-005` — the instrument was validated on `C7` itself, and it scopes `C7`

`scripts/cds_domain_test.py` was written and committed as `CDS-PR-001` §2.6's analysis **before any
CDS arm existed**. Before using it on new data it was run on the **published Qwen3 `C7` cells**,
which is both a validation of the instrument and — unplanned — the most consequential finding of
this sprint so far.

**It reproduces the published row counts exactly.** On the 640-cap cell (`p26j_*`,
`longpreQ14B`, 80 rows, doses 4+8) it returns `A → demoproc = −10 rows` and `A → ctrl_d1 = +1 row`.
`R-64` reports **−3 at n=4 and −7 at n=8** (= −10) and the control at **+1 and +0** (= +1).
Independent path, same numbers.

**And then it asks the question `C7` was never asked.** `PR-1` names the **domain** as the
independence unit. `C7`'s evidence is a row-count separation against a margin; **no domain-level
inference has ever been computed for it.** Here it is, on all three cells, with the exact paired
domain sign test and a domain-cluster bootstrap:

| cell | rows | contrast | Δ rows | row McNemar p | domains ↓/↑ | k_inf | domain sign p | attainable floor | capable? | cluster-bootstrap 95 % CI on ΔASR |
|---|---|---|---|---|---|---|---|---|---|---|
| pool A, 192 | 160 | A vs demoproc | **−11** | **0.0266** | 5/3 | 8 | **0.727** | 0.0078 | **YES** | [−0.2000, **+0.0187**] |
| pool A, 192 | 160 | demoproc vs ctrl_d1 | +10 | **0.0414** | 2/4 | 6 | **0.688** | 0.0312 | **YES** | [−0.0125, +0.1875] |
| pool A, 192 | 160 | demoproc vs ctrl_d3 | +13 | **0.0072** | 2/4 | 6 | **0.688** | 0.0312 | **YES** | [−0.0063, +0.2125] |
| pool B, 192 | 160 | A vs demoproc | **−10** | **0.0213** | 5/2 | 7 | **0.453** | 0.0156 | **YES** | [−0.1625, **+0.0062**] |
| pool B, 192 | 160 | demoproc vs ctrl_d1 | +12 | 0.0075 | 1/4 | 5 | 0.375 | 0.0625 | **NO** | [0.0000, +0.2000] |
| 640 cap | 80 | A vs demoproc | −10 | 0.0064 | 4/1 | 5 | 0.375 | 0.0625 | **NO** | [−0.2875, 0.0000] |
| 640 cap | 80 | demoproc vs ctrl_d1 | +11 | 0.0034 | 1/3 | 4 | 0.625 | 0.1250 | **NO** | [−0.0125, +0.3500] |
| pool A, **n=4 only** | 40 | A vs demoproc | −5 | 0.0625 | 4/0 | 4 | 0.125 | 0.1250 | **NO** | [−0.2250, **−0.0250**] |
| pool A, **n=4 only** | 40 | demoproc vs ctrl_d1 | +4 | 0.1250 | 0/3 | 3 | 0.250 | 0.2500 | **NO** | [0.0000, +0.2000] |
| pool A, **n=8 only** | 40 | A vs demoproc | −5 | 0.1797 | 3/1 | 4 | 0.625 | 0.1250 | **NO** | [−0.3500, +0.0250] |

**The finding, stated exactly.**

1. **Every `C7` cell's domain-level test is either INCAPABLE BY CONSTRUCTION or CAPABLE-AND-NULL.**
   Where the attainable floor `2/2^k_informative` exceeds α = 0.05, no outcome could have reached
   significance (`C-95`'s defect, now found in the flagship claim). Where the test **was** capable —
   the three pool-A/pool-B contrasts above — it returned **p = 0.45 to 0.73**.
2. **The domain-cluster bootstrap agrees.** Two independent domain-aware methods, same conclusion.
3. ⚠ **This does NOT refute `C7`.** The row-level numbers reproduce exactly and the row-level
   McNemar is significant on five contrasts. What it establishes is the **scope**: `C7` is a
   **row-level** result on **10 domains**, and at its own stated independence unit it is **not
   established**. The mechanism is visible in the counts — pool A's −11 rows sit in **5 domains
   down against 3 up**, which is a concentration of attacks in a few domains rather than a
   consistent across-domain shift.
4. **One leg survives partially.** At **n=4, pool A**, the cluster bootstrap on
   `A vs demoproc` is **[−0.2250, −0.0250], excluding zero** — so *attack removal by `demoproc`*
   has some domain-level support at that dose. ⚠ **The SPECIFICITY contrast does not**:
   `demoproc vs ctrl_d1` is **[0.0000, +0.2000]**, touching zero, at every dose and cell.
5. ⚠ **Doses were NOT pooled to get this.** The 160-row rows span `n_examples {1,2,4,8}`; the pooled
   reading is the **most favourable** one and it still fails. Per-dose is strictly weaker because
   `k_informative` shrinks.
6. The `NOOP` guard shows the control arms changed **78–100 %** of completions, so none of them is
   the `C-20` failure — they are real controls that simply do not separate at the cluster level.

**Consequence for the sprint.** This is the strongest argument for `CDS-PR-001` as designed: **38
domains is the first population in this project on which a demonstration-specificity test is
CAPABLE at the independence unit at all** (k=38 gives a floor of `2/2^38`, and the Stage-1 gate is
set where the *power*, not merely the floor, reaches 0.80). It also means Claim A must be written
down tomorrow as **row-level only** until such a test is run — whatever Stage 1 decides.

### `CDS-R-006` — independent verification of `CDS-R-004`

`scripts/cds_verify_install_vs_asr.py` — **stdlib only, imports nothing from the producer**, and
deliberately re-derives ASR and refusal from the judge's **per-row** `results.jsonl`
(`malicious_at_0.5`, `refused`, `n_examples`) rather than from the `summary.json` block the producer
read, so the two do **not** share a field. `RAH2-C-022` is the reason: a verifier that re-reads the
producer's chosen field inherits the producer's choice of field.

**206 checks, 0 failures.** 13 cells × 15 per-cell checks + 3 header + 8 aggregate. Relative
tolerance 1e-9 with a 1e-12 absolute floor — and the floor is not decoration: it is what makes
`refusal_rate == 0.0000` checkable at all, where a relative tolerance is degenerate
(`RAH2`'s "absolute tolerances are vacuous against small values", inverted).

`scripts/cds_mutate_verifier.py` — **15 of 15 mutation classes go RED**, each targeting the value
with the **least** headroom rather than the most (`RAH2-C-023`'s defect, avoided by construction):
`install_rate` perturbed by 1 part in 1e6 on the smallest rate; `refusal_rate` 0.0 → 1e-9, caught
only by the absolute floor; `judge_pinned` mutated to a **real adjacent model id**, not garbage;
`install_ties` 0 → 1. 14 of the 15 produce exactly **one** failing check — surgical, not collateral.

⚠ **Three limits the verifier itself reports, and they are the honest ones:**
1. **It verifies the numbers GIVEN the producer's run selection.** It does not re-derive the
   inclusion rule — the largest-cap-then-earliest tie-break, the SFC option-mass gate, or which of
   several candidate runs became `install_run` / `beh_run` / `judge_run`. **A cell built on the
   wrong run would verify as internally correct.** That is the remaining soft spot in `CDS-R-004`.
2. **The tie clause never fires on this corpus.** `install_ties` is 0 in all 13 cells and the
   smallest `|p_concept − p_codeword|` anywhere is 7.7e-4, so *"a tie is not a win"* — the sentence
   the producer's docstring foregrounds — carries **no** published number here. Only the mutation
   test exercises it.
3. **One boundary sits exactly on the knife edge**: a cell reads `install_rate == 0.5000` exactly,
   and the converse rule is the strict `< 0.50`. Change that comparator to `<=` and the converse
   count changes. (The other two thresholds have margin: nearest installation to 0.75 is
   0.65/0.8333; nearest ASR to 0.05 is 0.0417/0.0875.)

---

## §5 — `CDS-PR-003` — the Llama × Qwen3 rescue INTERACTION, at the domain level

⚠ **This is a SPECIFIED RE-ANALYSIS, not a blind preregistration.** The one-sample numbers it
re-analyses (`C9`: Llama ΔASR **+0**, Qwen3 **+9 / +13 / +10 / +14**) are already published in
`RESEARCH_HANDOFF.md` and were read before this was written. What is new is the **estimator**, and
that is the point: the charter's instruction is *"pre-register a model × rescue interaction rather
than performing two separate significance tests and inferring that models differ because one is
significant and the other is not."* `R-104` already had to make exactly this fix for `C13`.

**No new GPU.** The matched arms exist: at a **640-token cap**, on the **same** `d10` bank, both
models, same dose set — `p7r640_L5 → p7r640_L14` (Llama) and `q7r640_L5 → q7r640_L17` (Qwen3), with
`q6r640` on `d10_poolB` as a second Qwen3 pool.

**Estimand.** Per domain, `d_m = (rescue count) − (comparator count)`; the interaction is
`d_Llama − d_Qwen3`, **paired by domain** because both models ran the same bank rows.
**Primary:** exact paired domain **sign test** with `k_informative` and its attainable floor.
**Also:** an **exact randomisation test** — under the null the model label is exchangeable within a
domain, so the reference distribution is the enumeration of all 2^k sign flips — and a
domain-cluster bootstrap CI. Outcomes: **ASR** (the contested clause) and **`kw_refusal`** (which
has zero judge variance).

⚠ **The comparator is the below-band L5 patch, which `C-20` showed is BYTE-IDENTICAL to
knockout-only.** That makes it a faithful stand-in for knockout-only and **not** an independent
control; the byte-identical fraction is printed with every cell so this is visible, not assumed.

### `CDS-R-007` — `CDS-PR-003` EXECUTED. The refusal effect is the SAME in both models; the ASR selectivity is NOT established as an interaction.

640-token cap, `frac_stop_length` released, judge pinned `openai/gpt-4o-mini` on **100 %** of rows in
all four arms, 160 rows each, 10 shared domains, paired by domain. Artifacts:
`outputs/boombness/cds_analysis/cds_inter_{asr,refusal}_d10_640.json`, `cds_inter_asr_poolB_640.json`.

**The one-sample numbers reproduce exactly**, by an independent path: Llama comparator→rescue
**5 → 5 = +0** on ASR and **35 → 17 = −18** on refusal (`R-143`); Qwen3 **4 → 18 = +14** on ASR
(`R-154`) and **23 → 6 = −17** on refusal.

| outcome | cell | Llama Δ | Qwen3 Δ | interaction | domain sign p (floor) | **exact randomisation p** | cluster bootstrap 95 % CI |
|---|---|---|---|---|---|---|---|
| **ASR** | `d10`, matched | **+0** | **+14** | **−14 rows** | 0.508 (3.9e-3, **capable**) | **0.102** | **[−2.70, −0.20]** |
| **ASR** | `d10_poolB` (Qwen3) | +0 | +10 | −10 rows | 0.453 (1.6e-2, capable) | **0.156** | [−2.20, **0.00**] |
| **refusal** | `d10`, matched | **−18** | **−17** | **−1 row** | 0.727 (7.8e-3, capable) | **1.000** | [−1.90, +1.40] |

**What this establishes.**

1. ✅ **The rescue's REFUSAL effect is cross-model, and now as an interaction rather than as two
   one-sample results.** Llama −18 and Qwen3 −17 differ by **one row** over 160; the exact
   randomisation test on the 10 domains gives **p = 1.000** and the bootstrap CI **[−1.9, +1.4]**
   straddles zero. This is the strongest form the claim has ever had: *the primary effect is
   indistinguishable between model families on matched material at a released cap.*
2. ⚠ **The SELECTIVITY clause — "and not the attack, on Llama only" — does NOT reach significance
   as an interaction.** The direction is unambiguous and the size is large in rows (−14 and −10 in
   two independent Qwen3 pools), and the cluster bootstrap on the primary cell excludes zero — but
   the **exact randomisation test**, which is the principled test for a paired design with an
   exchangeable label, gives **p = 0.102** and **0.156**, and the domain sign test gives 0.508 and
   0.453. **Three domain-aware methods do not agree, and the two more conservative ones say no.**
   With **k = 10 domains** this is the project's structural power problem again, not a surprise.
3. **The honest sentence for tomorrow:** *"On matched 640-cap material the rescue restores refusal
   equally in both models (interaction −1 row, p = 1.000). It restores attack on Qwen3 (+14, +10)
   and not on Llama (+0), consistently in two pools; as a formal model × rescue interaction at the
   domain level that difference is **directional and not established** (exact randomisation
   p = 0.102 / 0.156, k = 10 domains)."* **Do not say the models are shown to differ.**
4. ⚠ **Comparator caveat, printed not assumed:** the below-band L5 arm is byte-identical to the
   rescue arm on **5.0 %** (Llama) and **0.6 %** (Qwen3) of rows, so it is a faithful stand-in for
   knockout-only and **not** an independent control (`C-20`).
5. ⚠ Doses `{1,2,4,8}` are pooled here, matching how `C9` itself is reported. That is the **most
   powered** reading; per-dose is strictly weaker.

### `CDS-R-008` — configuration smokes, and a scope note on what "dose-matched" means

All three modes smoked at `--limit 8` on the carrot CDS bank before any full arm:
`A_baseline` (8/8, 0 failures), `C_demo_processing_only` (8/8, `frac_rows_scope_live` **1.000**),
`CTRL_matched_d1` (8/8, `frac_rows_scope_live` **1.000**). `median_n_demo_positions` = **46.5** keys
at n=4. Zero decode edits in both intervened arms, which is `demo_processing_only`'s **correct**
liveness contract (`RBD-C-010`: applying one scope's must-be-zero rule to another produced a false
alarm three times).

⚠ **The count-matched control matches the KEY COUNT, not the EDIT COUNT — and it is ~1.95× the
intervention on edits.** Smoke: `demo_all` **83 628** total prefill edits, `nondemo_matched_d1`
**162 936**. This is **not** something this sprint introduced: every published `C7` arm pair shows
the same ratio — `q15` 3 692 777 vs 7 221 775 (1.96×), `p13` 3 017 169 vs 5 907 960 (1.96×),
640-cap `dp640` 3 626 722 vs `c1_640` 7 108 321 (1.96×). The cause is structural: under
`demo_processing_only` the edited rows are the demonstration positions, so masking demo→demo is
causally triangular (≈ n²/2) while masking demo→non-demo is not (≈ n²).

**Direction of the bias: it makes `C7` CONSERVATIVE.** The control applies about **twice** as many
attention edits as the intervention and still removes less attack. But *"dose-matched"* in the
handoff means **matched masked-key count**, and that is the sentence that should be written down —
`match_ratio = 1.000` is a statement about keys.

