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

