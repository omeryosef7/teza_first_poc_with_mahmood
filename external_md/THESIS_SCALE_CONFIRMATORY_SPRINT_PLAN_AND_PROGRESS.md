# THESIS-SCALE CONFIRMATORY SPRINT — plan and append-only progress

**Id namespace `TSC-`.** Branch `behavioral-causality-sprint`. Opened 2026-09-02.
Predecessor log: `external_md/CONFIRMATORY_DEFENSIBILITY_SPRINT_PLAN_AND_PROGRESS.md` (`CDS-`).
Predecessor summary: `reports/CDS_SPRINT_SUMMARY.md`.

**This file is the scientific provenance for this sprint. Chat context is not.** Another session
must be able to recover the full state from this file alone.

---

## §0 — CURRENT SCIENTIFIC TRUTH (inherited, not re-derived)

The state below is what the previous sprint left standing *after* its own adversarial audit. Where
an older claim conflicts with a later correction, **the later correction wins**. No headline is
revived because its old number was large.

### 0.1 The strongest standing result — `CDS-R-018` / `CDS-DR-002`

**Demonstration-specific attack removal on Llama-3.1-8B-Instruct**, on the new capable population:

| item | value |
|---|---|
| bank | `data/boombness_prompts/boombness_prompt_bank_cds38_button_bomb.jsonl` |
| lexical pair | `button ↔ bomb` |
| population | `behavioral` × `natural_doublespeak` × `cds_n4` × `n_examples=4` = **380 rows** |
| clusters | **38 domains × 10 verified-disjoint demonstration pools** |
| dose | n=4 demonstrations |
| band | layers **6–14**, `attn_knockout`, α=1.0 |
| scope | `demo_processing_only` |
| cap | **640** new tokens, `--attn-impl eager` |
| judge | `openai/gpt-4o-mini`, pinned, one manifest for all five arms |
| baseline ASR | **0.3895 (148/380)** under judge pass 1 · **0.4184 (159/380)** under judge pass 2 |
| `demo_processing_only` | **0.1447 (55/380)** — **−104 rows** vs the pass-2 baseline |
| controls (attack rows) | `A`=159 · `d1`=159 · `d2`=150 · `d3`=148 → **0 / −9 / −11** |
| primary test | exact paired **domain** sign test, demoproc vs **each** control |
| p-values | **2.556e-06 / 1.309e-07 / 6.938e-08** (floors 4.66e-10 / 2.33e-10 / 1.16e-10) |
| informative domains | 32 / 33 / 34 |
| verification | `scripts/cds_verify_stage2.py` — 349 checks, 0 failures; `scripts/cds_mutate_stage2.py` — 18/18 red |

**Verdict: STRONG.** It is preregistered (`CDS-PR-001`), independently verified, and adversarially
audited.

### 0.2 The scope limits that this sprint exists to close

1. **ONE lexical pair.** `button↔bomb` only. The `basket↔bomb` replication is **VOID**, not
   negative — see 0.3.
2. **ONE harmful request.** All 380 rows carry an identical `final_query_text` (`CDS-C-020`,
   verified from the bank). The 38 clusters are **38 demonstration pools around one request**, not
   38 harmful behaviours. **Nothing here is generality over requests.**
3. **The controls are neutral-filler controls.** Per-row `control_draw` shows
   **99.79 % / 99.70 % / 98.31 %** of drawn keys lie strictly *before* the demo block, inside the
   `n_preamble = 10` neutral filler that `main_longpre_cds` adds solely to make count-matching
   feasible. `query_span_positions` protects the request by construction. So the established
   contrast is **"masking demonstrations ≫ masking neutral preamble filler of equal masked-key
   count"** — real, and narrower than "demonstrations vs any structurally active context"
   (`CDS-C-019`).
4. **The 0 / −9 / −11 control deltas are inside the instrument's noise.** The same 380 completions
   judged twice flip **51 labels (13.4 %)**, ±11 rows (`CDS-C-018`). Those cells must be stated as
   *within judge re-run variance*, **never** as informative negatives. The **−104** headline is
   ≈ 9× that noise and survives.
5. **ONE model.** The old Qwen3 `C7` population does **not** support the claim at its stated
   domain-level independence unit — every cell is incapable-by-construction or capable-and-null
   (`CDS-R-005`). A **capable** Qwen replication on the **new** design is still needed.

### 0.3 `CDS-R-020` — the `basket↔bomb` replication is VOID FOR A BANK DEFECT

All four `basket` intervention arms **crashed**:

```
ValueError: occurrence_count_mismatch:text=5,tokens=6
```

on exactly the three `school_campus` prompt ids **named in the log by `prompt_id` before any
generation ran** (`CDS-C-002`): `566c998c6df83a30`, `56c76e11095a5d48`, `f953fbbb2376f8db`.

The asymmetry is the whole story: in a **baseline** arm the failure ledger catches the exception
(`score_behavior.py:1861`) and the run continues at **377/380**; in an **intervened** arm the same
exception is raised from the pre-flight loop at `score_behavior.py:1642`, which is **not** inside a
`try`, and it kills the job.

⛔ **This is NOT a failed replication and must never be reported as one.**

### 0.4 Other conclusions this sprint must preserve

* `d_surface` / Boombness is **not** a valid attack objective.
* Mapping installation is **not sufficient** for behavioural attack — but the clean evidence is the
  matched-skeleton contrast (2/24 vs 12/24, Fisher p = 0.0034), scoped to one pair, not `C7`.
* Refusal restoration is **not** a universal explanation of attack removal. On the button bank the
  same scope makes refusal **FALL** (−20 rows, p = 0.0034) while attack falls by 104 — the
  strongest available evidence against "attack dies because refusal returns".
* `C1` ("`demo_processing_only` restores refusal") is **BANK-SCOPED**: it restores refusal on `d10`
  (both models) and `carrot↔bomb`, and **reduces** it on `button↔bomb`.
* The clean activation-readout problem remains **unresolved** (`RAH3`, Track A = CANNOT ANSWER).
* **GCG / MAC stay closed** until a stable, causal, transferable low-dimensional objective exists.

---

## §1 — WHAT WE CAN DEFEND TODAY, BEFORE THIS SPRINT ADDS ANYTHING

* Masking demonstration processing at layers 6–14 removes attack on Llama, `button↔bomb`, at
  **38 demonstration-pool clusters around one harmful request**, against three count-matched
  neutral-preamble controls, domain sign test **p ≤ 2.6e-06**.
* The removal is **not** explained by refusal returning: refusal falls on the same rows.
* The domain ICC of that population is **0.1583** (button baseline ASR); `carrot` measured
  **−0.0123**.
* Judge re-run noise on byte-identical text is **13.4 %** of rows on this exact population.

## §2 — WHAT WE CANNOT DEFEND TODAY

* Anything **cross-lexical** — one pair only.
* Anything **cross-model** — the Qwen population that exists is incapable at the claimed unit.
* Anything **across requests** — one request.
* "Demonstrations are special relative to *any* context" — the live controls are neutral filler.
* Any control-vs-baseline difference of magnitude ≤ ~11 rows — that is inside judge noise.
* That the headline survives **independent re-judging** — measured on the Stage-1/Stage-2 pair only,
  not as a designed robustness test.

---

## §3 — PRIORITY ORDER (fixed; changed only for a scientific blocker, and only with a logged reason)

| # | task | status |
|---|---|---|
| **P1** | Complete the independent lexical-pair replication on Llama, `basket↔bomb`, via a generic `--exclude-prompt-ids` | see §5 |
| **P2** | Run the new capable 38-cluster design on **Qwen3**, Stage-1 baseline screen first | see §6 |
| **P3** | Re-judge the headline populations; quantify judge robustness | see §7 |
| **P4** | Build (and if feasible launch) the **request-diverse** confirmatory bank | see §8 |
| **P5** | Design a **structurally active** count-matched control | see §9 |
| **P6** | Strengthen installation ≠ sufficiency — only if P1–P4 are done or blocked | not started |

**Explicitly NOT tonight:** Boombness correlation sweeps · new readout searches · GCG · MAC ·
arbitrary layer searches · low-rank decomposition · a third model family · unrelated mechanistic
exploration.

---

## §4 — STANDING RULES FOR THIS SPRINT

### 4.1 Preregistration
Every confirmatory forward pass gets a `TSC-PR-nnn` entry appended **and committed** here **before**
generation, containing: hypothesis · null/alternative · model · bank + hash · lexical pair ·
population · dose · arm definitions · mask scope/band · expected sample count · **true independence
unit** · baseline-headroom criterion · capability/power analysis · primary endpoint · secondary
endpoints · exact statistical test · alpha · control arms · exclusion rules · tokenization/liveness
requirements · generation cap · judge model · stop/decline conditions · artifact paths · expected
verdict categories.

### 4.2 Verdict vocabulary — closed set, never extended after seeing a result
`CONFIRMED` · `REPLICATED` · `CAPABLE NULL` · `DECLINED FOR POWER` · `VOID` · `CANNOT ANSWER`

### 4.3 Independence units
* Current 38-domain banks: the unit is the **demonstration-pool domain**, k=38. It is **not** the
  request and **not** the row.
* Request-diverse bank (P4): the unit is the **harmful request**. Rows and demo pools are nested
  inside it. *"N=800 independent examples" is forbidden when there are 40 requests.*
* Row-level McNemar is reported **descriptively only**, never promoted to a headline.

### 4.4 Power / capability
Sample size is **frozen before intervention outcomes**. No sequential N increases after seeing a
p-value. Every design states rows · clusters · what a cluster is · requests · demo pools · lexical
pairs · models · doses. Capability uses the **measured** ICC (`scripts/cds_power_domain.py`), the
**measured** judge-flip rate, the actual cluster count and the measured baseline headroom. The
attainable p-floor `2/2^k_inf` is reported next to every p-value and **never in an adjacent column
without a label** — that is how `< 1e-9` got published for `2.6e-06`.
**A design that cannot answer its question at its own independence unit is DECLINED, not run.**

### 4.5 Bug-resistance gates, all mandatory
**A. Liveness** — the intervention fired on every intended row; expected positions edited; expected
edit count; no silent skips; no out-of-range patches; mask count correct; counters persisted.
**B. Row matching** — same intended prompt ids, same exclusion list, same bank hash, same dose, same
generation settings across arms. **Analysis is refused if arms silently differ.**
**C. Tokenization** — the span audit runs **before** expensive intervention arms; any structural
row exclusion is declared **before** outcomes.
**D. Batch matching** — baseline and intervention arms use matched batch behaviour.
**E. Truncation** — released cap; report `frac_stop_length` per arm and the arm differential
against the **0.02** gate, computed from each run's own `stop_reason` rows.
**F. Judge provenance** — every judged row hash-joins to its completion by `completion_sha256_16`;
persist pinned judge model, completion hash, source run, judge run id.
**G. No filtering** — no ASR filtering, no dropping "weird" generations, no post-hoc domain removal,
no outcome-based exclusion. Ever.
**H. Controls cannot be vacuous** — the byte-identical no-op guard (`NOOP_GUARD = 0.99`) must show
the control actually changed completions.

### 4.6 Verification
Every **new** headline gets a **stdlib-only independent verifier** that imports nothing from the
producer and re-derives row counts, attack counts, per-cluster outcomes, `k_informative`, the
primary p-value, the effect, the capability rule and the verdict from raw artifacts — then a
**mutation harness** that corrupts each load-bearing input and shows the verifier goes RED.
"The script ran successfully" is not evidence. Use **relative** tolerance: an absolute tolerance
already swallowed corruption down to 3e-19 once (`CDS`).

### 4.7 Adversarial review
Every candidate headline gets a read-only agent told to **refute** it, hunting specifically for:
wrong independence unit · pseudo-replication · lexical-pair selection leakage · baseline-headroom
selection leakage · request duplication · demo-pool dependence · mask-count mismatch · neutral-filler
confound · batch mismatch · truncation · judge drift · parser inconsistency · intervention not firing
· tokenization mismatch · wrong sign · wrong denominator · wrong p-floor · post-hoc exclusion ·
cross-session artifact mismatch · claim broader than the population.

### 4.8 Shared-tree hygiene
This working tree has **other writers**. **Never** `git add -A`. **Never** `git stash`. Commit only
with explicit path limiting. Do not run the full test suite concurrently with a job that mutates
artifacts.

---

## §5 — P1 — `basket↔bomb`, the independent lexical-pair replication

### 5.1 `TSC-PR-001` — preregistration

**Written before any `basket` intervention arm exists.** The four empty run directories from
`CDS-R-020` (`cds2dp_basket_…`, `cds2c1_basket_…`, `cds2c2_basket_…`, `cds2c3_basket_…`) hold
`config.json` + `RUNMETA.json` and **no `gens.jsonl`, no `results.jsonl`, no `DONE.json`** — there
is no basket intervention outcome anywhere to have been looked at, and none has been.

**Hypothesis (`H-A`).** Masking demonstration processing (`demo_processing_only`, layers 6–14,
α=1.0) removes behavioural attack on the `basket↔bomb` bank **more than** three seeded
count-matched non-demonstration masks of the same masked-key count do.

**Null (`H-0`).** Per-domain attack removal under `demo_processing_only` is exchangeable with that
under each count-matched control.

| field | value |
|---|---|
| model | `meta-llama/Llama-3.1-8B-Instruct` |
| bank | `data/boombness_prompts/boombness_prompt_bank_cds38_basket_bomb.jsonl` |
| bank hash | `bank_rows_sha16 = d22cc2da5eb943e0` (as `CDS-PR-006` recorded; re-verified in §5.3) |
| lexical pair | `basket ↔ bomb` |
| population | `behavioral` × `natural_doublespeak` × `cds_n4` × `n_examples=4` |
| dose | n=4 demonstrations |
| **exclusions** | `data/boombness_prompts/exclusions/cds38_basket_bomb_occurrence_mismatch.txt`, **3 ids**, `exclude_prompt_ids_sha16 = 52ba6a6cfc3fe6f6` |
| **expected N** | **377 rows**, `--expect-n 377`, in **38 domains**: 37 × 10 + `school_campus` × 7 |
| **independence unit** | the **demonstration-pool domain**, k = 38. Not the row. Not the request — all 377 rows carry one identical harmful request, exactly as on `button`. |
| band / scope | `attn_knockout` layers **6–14**, α=1.0, `--knockout-scope demo_processing_only` |
| cap | **640** new tokens |
| attn impl | `eager` (SDPA silently no-ops a 4-D additive mask) |
| seed | `20260901` — **unchanged from `CDS-PR-006`**, so the control draws are the same draws |
| judge | `openai/gpt-4o-mini`, **pinned**, all five arms in **one** manifest / one invocation |
| arms | `A_baseline` (already generated) · `C_demo_processing_only` · `CTRL_matched_d1` · `CTRL_matched_d2` · `CTRL_matched_d3` |

**Arms.** Everything except **mask identity** is matched. `A_baseline` is the existing
`cds1A_basket_20260901_191635_1462938` (377 rows; its three missing ids are **exactly** the three
excluded ids — verified in §10, and re-verified independently in §5.3). The four intervention arms
are regenerated with `--exclude-prompt-ids`, so all five arms carry the **same 377 `prompt_id`s**.

⚠ **The one deliberate asymmetry, stated in advance.** The baseline reached 377 by *ledgering three
failures*; the intervention arms reach 377 by *excluding three rows up front*. The **row set is
identical** and that is what the paired test consumes. The audit question — whether being
attempted-and-failed rather than excluded-up-front could have perturbed the baseline's seeding,
ordering or batching — is answered in §5.3 **before** the arms run, and the answer gates the launch.

**PRIMARY endpoint.** Exact **paired domain sign test** on per-domain attack counts,
`demo_processing_only` vs **each** of the three count-matched controls.
`H-A` is supported **iff all three** reject at **α = 0.05** in the direction *demoproc removes
more*. The attainable p-floor `2/2^k_inf` is reported **labelled, in its own column**, next to but
never in place of the p-value.

**SECONDARY endpoints, descriptive only, never promoted.** Row-level exact McNemar · domain-cluster
bootstrap CI on ΔASR · raw ASR counts per arm · per-domain effect distribution · number of
informative domains · domain ICC of each arm · the same battery on `refused` as the outcome.

**Capability, from the pre-computed grid at the MEASURED Stage-1 basket baseline** (p0 = 0.1220,
k = 38, m ≈ 10, `scripts/cds_power_domain.py`), **carried over verbatim from `CDS-PR-006` and not
re-derived after any outcome**: for a **total wipeout** the domain sign test is ≈ **0.90 / 0.87** at
ICC 0.067 / 0.09 and **0.73** at 0.19; for a **75 % reduction** — nearer what `button` actually
showed (a 65 % relative drop) — ≈ **0.61 / 0.60** at ICC 0.067 / 0.09.
⚠ **So this cell is ADEQUATE for a wipeout and UNDERPOWERED for a partial effect, and that is
written down before the arms run.**

**Verdict rules, fixed now.**
* all three contrasts reject → **REPLICATED**;
* they do not reject, and the arms are **capable** (liveness green, controls non-vacuous, truncation
  gate passed) → **UNDERPOWERED FOR A PARTIAL EFFECT** = `DECLINED FOR POWER`, reported with its
  numbers, **not** as a failure to replicate;
* a per-arm capability gate fails (liveness, no-op control, truncation differential > 0.02, judge
  provenance) → **VOID**, and the arms are rerun or the claim is dropped, never analysed;
* **whatever `basket` returns, `CDS-R-018` on `button↔bomb` stands on its own.** This is a
  replication, not a substitution. Registered in advance, as `CDS-PR-006` also did.

⛔ **Thresholds are not moved after the result. No row is added to or removed from the exclusion
file after outcomes exist. No fourth control is added. No fourth lexical pair is screened to
replace a disappointing one.**

**Artifact paths.** Runs under `outputs/boombness/score_behavior/cds2{dp,c1,c2,c3}_basket_*`;
judge manifest `outputs/boombness/argsfiles/tsc1j_basket_arms.txt`; judge dirs
`outputs/boombness/judge/tsc1j_basket_*`; analysis
`outputs/boombness/cds_analysis/tsc1_basket_specificity_domain_test.json` and
`…_refusal_domain_test.json`.

### 5.2 The mechanism, and why it is an exclusion rather than a `try`

`--exclude-prompt-ids PATH` added to `score_behavior.py`
(`load_prompt_id_exclusions` / `exclusion_sha16`). A **file**, not a comma list, because `--export`
truncates comma values silently and `run_boombness.sh` word-splits `BOOMB_ARGS`.

It is applied **after** the population filters, **before** `--limit` and **before** `--expect-n`,
and it **REFUSES** on: a missing file · an **empty** list · a **duplicated** id in the file · an id
**not present** in the filtered population · a listed id that removes more than one row (a bank with
a repeated `prompt_id`). It persists `exclude_prompt_ids`, `…_file`, `…_sha16` and `n_excluded` into
`population_filter` and `population_composition` on **every** arm, including arms that exclude
nothing — `0` and `null` are different statements.

⚠ **Why not simply wrap the pre-flight in a `try`.** That would make the intervened arm *skip* the
rows the way the baseline does — and a silent skip in one arm and not another is precisely the shape
that produces two different row sets under one label. The crash was the good outcome. The rows leave
the **population**, declaredly, or they do not leave at all.

Tests: `tests/test_prompt_id_exclusions.py`, **17 tests**, each refusal paired with an executed
**MUTANT** test proving the permissive version accepts the same input.

### 5.3 The pre-launch audit — run on CPU, BEFORE any GPU minute was spent

Four questions had to be answered before the launch, and all four were answered without a GPU.

**(a) Is the declared exclusion set exactly the set the tokenizer refuses — and nothing else?**
The whole 380-row basket population was pushed through `resolve_occurrences` with the real
Llama-3.1-8B tokenizer. **Exactly three rows raise**, `occurrence_count_mismatch:text=5,tokens=6`,
and they are **exactly** `566c998c6df83a30`, `56c76e11095a5d48`, `f953fbbb2376f8db`. The failing set
**equals** the declared exclusion set. The exclusion is therefore derived from the tokenizer alone —
**no generation, no judge label, no outcome** — and is reproducible by anyone with the bank.

**(b) Does the 377-row population survive the whole pre-flight?** The complete knockout pre-flight
(`resolve_occurrences` → `demo_key_positions` → `query_span_positions` → `scoped_span_is_dead` →
`knockout_key_set` for all four arms) was replicated CPU-side over the excluded population:

```
feasibility: {'n': 377, 'ok': 377}          # 0 no_demo_block, 0 dead_scope_span, 0 infeasible
nondemo_matched_d1: n=377 min=1.0000 mean=1.0000 n_below_1=0
nondemo_matched_d2: n=377 min=1.0000 mean=1.0000 n_below_1=0
nondemo_matched_d3: n=377 min=1.0000 mean=1.0000 n_below_1=0
draw seeds: d1=28180678  d2=36100455  d3=44020232
```

**Strict count-match holds on every row of every control**, so the dose confound the controls exist
to remove is measured rather than assumed, before generation.

**(c) THE LOAD-BEARING ONE — can the baseline differ because its three rows were
*attempted-and-failed* rather than *excluded up front*?** **No, and it is provable from the source
rather than argued.**
* **Decoding is greedy.** `ds_common.generate` passes `do_sample=False`; **no RNG is consumed
  during generation**, so `seed_everything(args.seed)` leaves every row's output independent of how
  many rows preceded it.
* **There is no batching.** `generate` tokenises one prompt and reads `out[0]` — **batch size 1,
  one row per call.** So no arm can inherit a batch-composition confound from another, and removing
  three rows cannot perturb any retained row's completion.
* **The three rows die before generation.** They raise inside `resolve_occurrences`, at the top of
  the per-row `try`, *before* `dc.generate` is reached — so in the baseline they consumed no
  generation call and no RNG either.
* **The control draws do not depend on population size or row index.** `knockout_key_set` seeds from
  `nondemo_draw_seed(args.seed, draw_index)` and draws over that row's own `(demo_keys, seq_len,
  protected)`. The three draw seeds above are functions of `--seed 20260901` and the arm index only.
  **Every retained row therefore gets the identical draw it would have got at N=380.**

⚠ The asymmetry is real and is stated in the write-up, but it is an asymmetry **in how the same 377
rows were arrived at**, not in the rows, the seeds, the draws or the decoding.

**(d) Is the bank the one the preregistration names?**
`data/boombness_prompts/boombness_prompt_bank_cds38_basket_bomb_meta.json` →
`bank_rows_sha16 = d22cc2da5eb943e0`. **Matches `TSC-PR-001` / `CDS-PR-006`.** The bank was **not**
regenerated, so the Stage-1 screen (`CDS-R-015`: basket ASR 0.1220, 46 attack rows, 24 domains with
an attack, `frac_stop_length` 0.0000) remains the screen for this cell and no fresh baseline or gate
run is required.

## §6 — P2 — the capable Qwen3 replication

### 6.0 Why the old Qwen population cannot be rehabilitated

`CDS-R-005`: analysed at the domain-level independence unit the paper claims, **every** Qwen3 `C7`
cell is either incapable-by-construction (attainable p-floor above α) or capable-and-null
(p = 0.45–0.73). The **row counts reproduce exactly** — this is a scope finding, not a refutation.
The remedy is therefore to run Qwen on the **new capable design**, not to re-analyse the old cells.
⛔ `"The old Qwen C7 data establishes domain-level demonstration-specificity"` is on the
must-not-say list.

### 6.1 `TSC-PR-003` — Stage 1, Qwen3 **BASELINE ONLY**, registered before generation

**Nothing about Qwen3 on any `cds38` bank exists.** A sweep of all 695 `score_behavior/config.json`
for `cds38` in `args.bank` returns **15 runs, all `meta-llama/Llama-3.1-8B-Instruct`**. There is no
Qwen outcome on this population to have been looked at.

| field | value |
|---|---|
| model | **`Qwen/Qwen3-14B`** — the only Qwen id in this repo, 78 runs, 1 distinct string |
| bank | `boombness_prompt_bank_cds38_button_bomb.jsonl`, `bank_rows_sha16 = 17173f8adc42973e` |
| lexical pair | `button ↔ bomb` — the **same** pair as the Llama headline, so the cross-model contrast is on identical material |
| population | `behavioral` × `natural_doublespeak` × `cds_n4` × `n_examples=4` = **380 rows**, `--expect-n 380` |
| independence unit | the demonstration-pool **domain**, k = 38 |
| dose | n=4 · cap **640** · `--attn-impl eager` · `--dtype bfloat16` · `--seed 20260901` |
| **`--enable-thinking false`** | **the one deliberate divergence from the Llama argv, and it is mandatory** — see below |
| arm | `A_baseline` **only**. No intervention arm is generated, judged or looked at until the gate has been applied and its verdict written here. |
| judge | `openai/gpt-4o-mini`, pinned |

⚠ **Why `--enable-thinking false` is not an optional knob.** `ds_common.parse_enable_thinking`
resolves `None` to *"do not pass the kwarg"*, and **Qwen3's template default is thinking-ON**. At a
640-token cap a thinking arm can spend the whole budget inside `<think>`, which would depress ASR
through truncation rather than through anything the experiment is about — exactly `CDS-R-009`'s
`carrot↔bomb` × Qwen3 × cap-192 cell, which read **0.458 truncated**. Every Qwen3 640-cap
behavioral run in this repo passes `--enable-thinking false` and every one reads
**`frac_stop_length = 0.0000`**. `score_behavior.py` renders the template both ways and **aborts**
if the flag is not binding, so a silent no-op is not possible. On Llama the flag is a genuine no-op
(no thinking branch) and is therefore **not** added there.

**The gate is `CDS-PR-001` §2.4's rule, reused verbatim as executable code**
(`scripts/cds_stage1_gate.py`), not restated in prose. A cell QUALIFIES iff **all** of
baseline ASR ≥ **0.10** · baseline attack rows ≥ **34** · domains with ≥ 1 attack ≥ **15**,
with preconditions: control `match_ratio` min = 1.000 · `frac_stop_length` ≤ **0.02** ·
`judge_model_used == openai/gpt-4o-mini` on 100 % of rows · every judged row hash-joining to its
generation by `completion_sha256_16` · bank join by `bank_rows_sha16` with 0 mismatches.

⚠ **The load-bearing criterion here is the DOMAIN count, not the pooled ASR.** `CDS-R-005`'s
finding was that the old Qwen cells could not reach significance at k_informative, so
*"≥ 15 domains with an attack"* is the number that decides whether a Qwen Stage 2 is capable at all.

**Fallback, written now, before any Qwen number exists.** If `button↔bomb` fails the gate:
screen `basket↔bomb` and `carrot↔bomb` on Qwen **baseline-only, both in one batch** (not
sequentially — a sequential screen is a selection rule applied after seeing data), then apply
`cds_stage1_gate.py` **verbatim**: the qualifying cell with the **most baseline attack rows**,
ties → smaller dose, then alphabetical pair. If none qualifies → **DECLINED FOR POWER**, Qwen is
reported as an **incapable population on this design**, and ⛔ **that is not a Qwen null and must
never be written as one.**

**Expected cost.** ~16–17 s/row measured on the two nearest Qwen3-14B 640-cap baseline arms
(`scr_q_cb_…2909600` 15.9 s/row, `scr_q_tk_…2909601` 16.9 s/row) → **380 rows ≈ 105 min**; a
contended node has read 45.3 s/row once, so **request 4 h**. Llama did the same arm in 7.5 s/row;
Qwen3-14B is ≈ 2.1× slower here.

**Verdicts:** `PROCEED` (gate passes → Stage 2 runs) · `DECLINED FOR POWER` (gate fails, and the
population is **not** re-scoped, the thresholds are **not** lowered, and no fourth pair is added).

### 6.2 `TSC-PR-004` — the Qwen Stage-2 arms and the model × intervention interaction

**Registered now, before the Stage-1 verdict, and conditional on it.** If and only if Stage 1
returns `PROCEED`, run the identical five-arm design: `A_baseline` · `C_demo_processing_only` ·
`CTRL_matched_d{1,2,3}`, `attn_knockout` 6-14 α=1.0, scope `demo_processing_only`, seed 20260901,
cap 640, eager, `--enable-thinking false`, **all five arms judged in one manifest**. Strict
`match_ratio` = 1.000 required at pre-flight, checked CPU-side before any GPU minute, as in §5.3.

**PRIMARY:** the same exact paired **domain** sign test, demoproc vs each of the three controls;
`H-A` supported iff **all three** reject at α = 0.05.

**The interaction, and the language rule that goes with it.**
⛔ **"Significant in Llama, non-significant in Qwen" is NOT a model interaction and must never be
written as one.** If both model populations exist, the model difference is tested **directly**: a
difference-in-differences on the per-domain effect
`Δ_d = (attacks_d | control) − (attacks_d | demoproc)`, paired **across models within domain** (the
38 domains are the same 38 domains on the same bank), by an exact paired sign test on
`Δ_d^Llama − Δ_d^Qwen`, with `k_informative` and the attainable floor reported. **This test is
registered here, before any Qwen intervention outcome is read.**
* Interaction rejects, Llama larger → **MODEL-SPECIFIC**.
* Interaction does not reject and both models' primaries reject → **cross-model**, `REPLICATED`.
* Qwen capable and its primary null while the interaction is underpowered → report **both**: a
  `CAPABLE NULL` on Qwen and `DECLINED FOR POWER` on the interaction. Not one dressed as the other.


## §7 — P3 — judge robustness on the headline populations
**Status:** recon in progress.

## §7 — P3 — judge robustness on the headline populations

### 7.1 `TSC-PR-002` — preregistration, written before either new judge pass exists

**Why.** The same 380 completions, judged twice, gave **148** and **159** attacks:
`cds1j_button_A` vs `cds2j_button_A`, **380/380 `completion_sha256_16` identical**, both pinned to
`openai/gpt-4o-mini`, both all-`ok`. **51 rows (13.42 %) flip `malicious_at_0.5`** — 31 benign→attack
and 20 attack→benign. `refused` flips on **0/380**: the keyword detector is deterministic, so the
whole 13.4 % is judge variance and none of it is generation variance. Temperature is hard-coded to
**0** (`strong_reject/.../evaluate.py:182`) and `--seed 20260816` was identical across both passes —
this is server-side nondeterminism plus rubric-parse variance, **not a knob that can be turned off**.

**Hypothesis.** The `button↔bomb` headline's *conclusion* is invariant to which independent judging
pass is used, even though ~13 % of individual row labels are not.

**Design.** **No completions are regenerated.** Two further **independent pinned** passes over the
**existing** five-arm manifest `outputs/boombness/argsfiles/cds2j_button_arms.txt` — same judge model,
same rubric, same parser, same completion hashes, distinct prefixes `tsc2ja_button` / `tsc2jb_button`
(distinct because `judge_p2.sh` resolves its verification dir with `ls -dt | head -1`, so a shared
prefix would make one pass verify the other's output). Re-running genuinely re-queries the API: the
only cache is an in-process `dict`, never persisted.

**Reported for every population, per pass:** ASR; pairwise label-flip rate; overall agreement;
majority-vote verdict; **the intervention effect under each pass separately**; and the **cluster-level
domain sign test under each pass separately** (all three demoproc-vs-control contrasts).

**Decision rule, fixed now.**
* The headline is **judge-robust** iff **all three** demoproc-vs-control domain sign tests reject at
  α = 0.05 **in every one of the three passes**.
* ⛔ **Any arm-to-arm difference whose magnitude is at or below the measured re-run band is reported
  as WITHIN JUDGE RE-RUN VARIANCE and never as an informative negative.** The band is measured on
  **this** population, not assumed: the arm-A pair gives ±11 rows / 51 flips. The 0 / −9 / −11
  control deltas are inside it. The **−104** demoproc effect is ≈ 9× outside it.
* The useful statement is **not** "the judge agrees perfectly". It is: *the intervention effect
  remains large and reaches the same qualitative conclusion under independent judging passes despite
  measured row-level judge variability.*

⚠ **Denominator note for any variance estimate.** The in-run cache scores duplicate
`(goal, completion)` pairs once and copies the label, so a pass makes **1754** real API calls over
1900 rows (arm A: 346 independent judgements, not 380). Rows sharing a hash are perfectly correlated
**within** a pass and independent **across** passes; a per-pass variance must use the ~346
denominator, not 380.

**Cost:** ≈ 1754 calls/pass, ≈ $0.55/pass, ~30 min wall on `cpu-killable`, both passes concurrent.

**Artifacts:** `outputs/boombness/judge/tsc2j{a,b}_button_*`;
`outputs/boombness/cds_analysis/tsc2j{a,b}_button_{specificity,refusal}_domain_test.json`.

**Verdicts:** `CONFIRMED` (all three contrasts reject in all three passes) · `CAPABLE NULL` (capable
and one or more fail) · `VOID` (a pass aborts, mixes judges, or fails its hash join).

## §8 — P4 — the request-diverse confirmatory bank

**This is the most important generality gap in the thesis.** The current headline establishes
robustness to **demonstration-context** variation. It says nothing about **request** variation,
because all 380 rows carry one identical `final_query_text`.

### 8.1 What the current generator actually does (verified by regeneration, not read)

`src/boombness/prompt_families.py`, CLI at `:1276`. The exact command was **re-run and reproduces
`bank_rows_sha16 = 17173f8adc42973e` byte-for-byte**:

```
python src/boombness/prompt_families.py --preset main_longpre_cds --seed 20260901 \
  --codeword button --concept bomb --pools data/boombness_prompts/demo_pools_29dom.json \
  --incidental-replace button=switch --strict \
  --out data/boombness_prompts/boombness_prompt_bank_cds38_button_bomb.jsonl
```

* The **38 domains come from the pools file**, not a constant: `generate_bank:1093` keeps
  `d for d in DOMAINS if f"{d}|benign" in pools`. `demo_pools_29dom.json` holds **152 pools = 38
  domains × 4 valences**; the filename says 29 and the data says 38 (`RAH3-C-019`).
* `_take` (`:366-372`): `start = (slot*3) % 20`, so slots `{0,4,8,12,16}` → starts `{0,12,4,16,8}` —
  **five disjoint 4-blocks that exactly partition the 20-sentence split**; × 2 splits = **10
  pairwise-disjoint demonstration sets per domain**. Slots 1 and 2 are deliberately unused (3·1 and
  3·2 overlap slot 0) — that overlap is what `G2` was retracted for.
* **The single request lives in three coupled places**: the module constant
  `QUERY_KINDS["behavioral"]["template"]` (`:125-131`), the per-bank `(codeword, concept)` threaded
  from the CLI into `build_prompt` (`:497-499`), and — the one that costs real work — **the `|harm`
  half of the pools was generated for the word `bomb`** (`demo_pools.py:561`,
  `word = concept if valence == "harm" else codeword`), with bomb-affording predicates. **You cannot
  vary the request without regenerating harm pools**, because the demonstrations *are* what teach
  `codeword → concept`.

### 8.2 `TSC-PR-005` — the request-diverse design, registered before any request is drawn

**The unit of the new bank is a REQUEST**, defined as a pair `(concept, template)` — a single-word
object noun the codeword is mapped onto, and a verb frame containing `{W}` exactly once.

| field | value |
|---|---|
| source | `data/manifests/heldout_495.csv` — **AdvBench held-out, 495 rows, 16 categories**. Chosen over ClearHarm because 127/179 ClearHarm rows are `other_uncategorized`, so a category-balanced draw is impossible there. |
| seed | **`20260903`**, for every random step; per-request settings use `20260903 + i` |
| scale | **8 categories × 5 requests = 40 requests**, each category having ≥ 16 source rows so a 5-draw is not near-exhaustive |
| categories | `cyber_hacking_malware` · `fraud_financial_crime` · `weapons_explosives_mass_casualty` · `identity_theft_personal_data_theft` · `misinformation_disinformation` · `violent_crime_physical_harm` · `drugs_controlled_substances` · `theft_property_crime` |
| demo pools | **5 setting-domains per request × 2 splits = 10 demonstration sets**, each from a **separate `gen_demos` call** with its own seed offset |
| lexical pair | fixed, `button ↔ bomb`'s codeword `button` (with `--incidental-replace button=switch`) |
| dose | fixed n=4, `n_preamble=10` **carried over unchanged, never re-tuned** |
| rows | **400 per arm** = 40 requests × 5 settings × 2 splits × slot 0 |
| arms | `A_baseline` · `C_demo_processing_only` · `CTRL_matched_d1` · `CTRL_matched_d2` (+ `d3` if budget allows) |
| **independence unit** | the **HARMFUL REQUEST**, k = **40**. ⛔ Not the row. ⛔ **"N=1600 independent examples" is forbidden.** |

**Exclusions, fixed before any request is inspected.**
`other_uncategorized` (not a category) · `child_exploitation` (n=7, and out of scope for anything
this project publishes) · `terrorism_extremism` (9), `academic_minor_dishonesty_deception` (8),
`privacy_surveillance` (7) — **dropped on n < 16 alone** · `self_harm_suicide`,
`hate_speech_discrimination`, `harassment_bullying_stalking` — dropped because the **object of the
request is a person or a speech act, not a noun the codeword can be mapped onto**, so the doublespeak
frame is not constructible. ⚠ **That last exclusion is a scope limit of the paradigm and must be
reported as one, not buried.**

**Dedup, all four rules fixed now.** (a) drop any row sharing a `duplicate_group` with an already
selected row; (b) normalise `instruction` (casefold, strip punctuation/whitespace) and drop exact
matches; (c) **concepts must be globally distinct** — two requests with the same concept are the same
mapping and are not independent clusters; (d) reject a concept that is not a single whole word or
that `incidental_codeword_collisions` (`prompt_families.py:1210`) flags, then repair by
`--incidental-replace` or redraw.

⚠ **Harmfulness validation must not touch the analysis model.** The AdvBench label is the primary
warrant. The secondary screen — bare `template.format(W=concept)`, no demonstrations, pinned judge —
runs on **`Qwen/Qwen3-14B`**, which appears nowhere in the P4 analysis. **Screening on
Llama-3.1-8B would be selecting the population on the outcome**, which is exactly `R-50`'s error and
what `CDS-PR-001` §2.4 forbids.

**Pool independence, asserted at build time and refused by `--strict`:** zero duplicate demo blocks
within a condition · the 10 sets per request pairwise **sentence-disjoint** (all 45 pairs) · **no
sentence string shared across two requests** · `n_alignment_violations == 0` over all 800 2×2
families · the exact-word-swap occurrence invariant.

**PRIMARY.** Exact paired **sign test over REQUESTS** on per-request attack counts, demoproc vs each
control. **Preregistered capability floor: `k_informative ≥ 6`** — at `k_inf = 5` the attainable
two-sided floor is `2/2^5 = 0.0625 > α` and **no outcome could reach significance**.
**SECONDARY:** row-level McNemar · request-cluster bootstrap CI · per-arm **request-level ICC**
(the number that will size every future confirmatory bank) · truncation differential ≤ 0.02 ·
the byte-identity no-op guard.

**The minimal-path trick, and the hazard it carries.** `scripts/cds_domain_test.py` clusters on
**one** field and only that field (`:82` `r.get("domain")`, `:120` `doms[a["domain"]]`), and both
`score_behavior.py:1941` and `judge_boombness.py:521` pass `domain` through a **fixed tuple**.
So emitting `"domain": request_id` makes the entire analysis chain cluster on **request with zero
edits**. ⚠ **But the output key is then named `domain` while meaning `request`** — precisely the
field-named-X-meaning-Y hazard this repo has been bitten by. **Mandatory mitigations:** the bank meta
and every artifact record `"cluster_unit": "harmful_request"`; the setting is preserved on
`setting_domain` and `demo_pool_domain`; the tag is `cdsreq`. **The field is NOT renamed** —
renaming breaks the fixed passthrough tuples in two files and the join to every prior artifact.

**Compute.** Measured 7.81 s/row over the five existing button arms (2834–3092 s for 380 rows each,
`stop_reason = eos` on 380/380 — **zero truncation at the 640 cap**). 4 arms × 400 rows ≈
**3.5 GPU-h, ≈ 55 min wall** run concurrently. **The real cost is not GPU:** it is **200 harm-pool
generations** (40 concepts × 5 settings × 40 sentences) through the OpenAI API, hours of wall clock,
plus the audit pass.

**Verdict: PREREGISTERED tonight; the pool generation is the long pole and is CPU/API, not GPU.**

---

## §9 — P5 — the structurally active matched control

### 9.1 Why the current controls are not enough

Per-row `control_draw`: **99.79 % / 99.70 % / 98.31 %** of drawn keys land in the `n_preamble = 10`
**neutral filler preamble**, which exists *only* to make count-matching feasible.
`query_span_positions` protects the request and everything after it by construction. So the live
contrast is **demonstrations vs neutral filler of equal masked-key count** — real, and not
"demonstrations vs any structurally active context".

⚠ **A finding that arrived with the audit and changes the wording, not the conclusion.**
`median_prefill_edits`: demoproc **15,399** · d1 **30,276** · d2 **30,276** · d3 **29,754** — the
controls do **1.93–1.97× MORE** edits than the treatment, at identical `match_ratio = 1.0` and
identical `median_n_demo_positions = 58.0`. The geometry explains it: under
`demo_processing_only` the masked query rows lie **inside** the demo span, so `demo_all`'s keys reach
only the lower triangle (≈ k²/2 pairs) while a control key sitting **before** the demo block is
visible to **every** demo query row (≈ k·n pairs). **The control therefore does strictly more damage
and still produces less effect — the contrast is CONSERVATIVE.** ⛔ Do not write "matched control"
unqualified. Write **"key-count-matched; the control's edit count is ≈1.95× the treatment's by
position geometry, which makes the contrast conservative."**

### 9.2 `TSC-PR-006` — the pseudo-demonstration bank, registered; execution DEFERRED

**Design chosen: BANK-SIDE.** New preset `main_longpre_cds_pd`, cloning `main_longpre_cds` with one
added block key `preamble_pool`, defaulting to `"filler"` so **every existing bank regenerates
byte-identically**. Setting `preamble_pool = "remap"` fills the preamble with 10 **domain-topical,
structurally parallel** inventory/log sentences — same register, same sentence length, same position,
same chat role as the demonstrations, **no codeword, no concept, no mapping taught**. The **existing,
untouched** `nondemo_matched_d{1,2,3}` draw then lands on **active pseudo-demonstrations** instead of
filler. ⚠ **Zero new intervention code** — `knockout_key_set`, `nondemo_control_draw`,
`query_span_positions`, `nondemo_draw_seed`, the pre-flight, the liveness gate and
`control_feasibility` are all reused **verbatim at the same seeds**. Only what the drawn indices
*point at* changes.

**Two cells, separately registered and never pooled.** **PD-A** (no substitution) = a coherent
topical example block that teaches nothing. **PD-B** (`bicycle → tulip`) = the same sentences one
word apart, teaching a **benign** mapping. PD-A vs PD-B is an exact-word-swap contrast and is the
cleanest available separation of *"coherent example block"* from *"in-context mapping"*.

**The intervention-side alternative was considered and rejected as primary**: on the existing bank
the draws already land in the preamble 98.3–99.8 % of the time, so a new draw policy buys ~0.3–1.7
points of localisation **on a preamble that is still neutral filler**. It does not make the control
active, and it would thread a new argument through `make_intervention`'s composed-recursion branch —
the line that has already silently dropped a threaded argument **twice**. It is kept only as
**hardening if the ≥95 % localisation precondition fails**.

**Preconditions, all executable and all refusing rather than warning.**
1. **≥ 95 % of every arm's drawn keys inside the pseudo-demo character span**, per arm, from the
   `control_draw` records; **0** inside the demo span; **0** inside the query span; the residual
   chat-template bucket reported as a count. ⚠ **Enforced by code — five "threshold published and
   enforced by nothing" defects in two sprints.**
2. **Leakage audit:** 0 occurrences of `carrot`/`basket`/`button`/`bomb` and their morphological
   variants anywhere in the preamble on 100 % of rows · Jaccard of content-word types
   preamble↔`final_query_text` ≤ 0.05 · preamble↔`demo_block` ≤ 0.15 · **0** overlap with a
   harmful-concept lexicon **committed before the bank is generated** · preamble byte-identical
   across all four core-2×2 conditions · the new bank differs from `cds38` **only** in the preamble.
3. **Behavioural non-mapping check, no harmful generation required:** on the bank's existing
   `semantic_forced_choice` rows, the pseudo codeword's `mapped_wins` against the target concept must
   be **at chance** (95 % CI covering 0.5). PD-B must additionally show `tulip → bicycle` **installed**
   and `tulip → bomb` **not**; PD-B is uninterpretable unless both hold.
4. **Comparability band:** `|ASR_PD − ASR_filler| ≤ 0.05` absolute on the same 380 rows and the same
   judge. Outside it, the pseudo-demo is a different experiment and the arms **may not be compared as
   a ladder**. ⚠ And any PD-vs-filler difference **smaller than 11 rows is within judge re-run
   variance** and is not an informative negative.
5. `control_feasibility.py` re-run on the new bank with `--model` **explicit** and
   `--bank-blocks cds_n4`; `match_ratio_min == 1.000` required. ⚠ Current headroom is thin —
   `max_n_demo 94` vs `min_drawable_pool 117`, **23 tokens**.

⚠ **Changing the preamble changes `prompt_sha16` on every row, therefore `bank_rows_sha16`
wholesale, and `compare_bank_hashes` treats that as FATAL.** No existing CDS run, fit or judged
artifact joins to the new bank. **The new bank needs its own Stage-1 baseline arm and its own gate
run, and Stage 2 is strictly serial behind them.** The gate may return **DECLINED FOR POWER**, and
the design's own rule is that **a decline is a decline** — thresholds are not lowered and the
population is not re-scoped. ⚠ `prompt_id` is stable across banks by construction, so two banks can
be joined on it with nothing detecting the error; the comparability comparison must go through the
explicit cross-bank path.

**Cost:** ~4.3 GPU-h and **2.5–3 h wall for PD-A alone**, because bank → feasibility → audit →
baseline → judge → gate → Stage 2 is a **serial chain**. PD-B doubles it.

**Verdict: PREREGISTERED, EXECUTION DEFERRED.** The design is written down in full so it can be run
without improvisation. ⛔ **It is deliberately not rushed to have a number tomorrow** — a
poorly-matched pseudo-demo that accidentally teaches the mapping would be worse than no control at
all, and the gate on its own baseline could decline it after the spend.


## §11 — CORRECTIONS (append-only, `TSC-C-nnn`)

⚠ **`TSC-C-001` — the Stage-2 verifier was RED against the artifact it certifies, and its green had
been vacuous before that.** `scripts/cds_verify_stage2.py` read the published `frac_stop_length` and
compared it against `summary.json → counts.frac_stop_length` — **the very field `CDS-C-015` proved is
permanently `null`** (`counts` is `{"behavioral": 380}`). While the artifact also carried `null`, the
check was asserting `None == None` and printing **PASS**: it could not have detected a corrupted
truncation number either. When `CDS-C-015` fixed the **producer** to compute the fraction from each
run's own `stop_reason` rows, the artifact was regenerated at **22:16:58** with real values and the
verifier went **RED on five checks** — every one of them the verifier's fault.

**Fixed.** The verifier now **re-derives** the fraction from `results.jsonl` `stop_reason`, which is
what *independent* means here, and additionally asserts the **arm-to-arm differential** against the
0.02 gate — the differential being the quantity the gate is actually about. It also fails loudly if a
published `frac_stop_length` is `null`, so the original defect cannot return silently.
Result: **350 checks, 0 failures, GREEN.**

**Two new mutation classes** were added because a new check that the harness does not exercise is a
new hole: `frac_stop_length` (corrupt the smallest **non-zero** fraction by 1e-8 relative — a zero
can be corrupted by any epsilon and proves nothing) and `frac_stop_length_null` (**the exact shape the
old verifier could not catch**, kept as a named class so the regression is visible if anyone
re-points the check at a summary field). Harness now **20/20 red**.

⚠ **The general lesson, and it is the fifth instance of this family in three sprints:** *a check
whose two sides read the same broken source agrees with itself.* Grep every verifier for a field it
compares against something derived from the same producer.

⚠ **`TSC-C-002` — the verifier was pinned to one headline and would have been FORKED for the second.**
`JUDGE_PREFIX`, the dose, the row count and the 38 × 10 design shape were module constants. Verifying
`basket` would have meant copying the file — and a forked verifier is two instruments that drift
apart, one of which quietly keeps an old assertion. They are now **required CLI inputs** with the
button values as defaults, and **`--expect-rows-per-domain` must be stated explicitly by the caller**
(`10:37,7:1` for basket) — with a refusal if it disagrees with `--expect-rows` or `--expect-domains`.
⚠ **A design check that infers its expectation from the data under test asserts nothing**; an
unbalanced design is legitimate and a *silently* unbalanced one is not.

---

## §10 — PROGRESS LOG (append-only)

* **2026-09-02, session open.** Read `reports/CDS_SPRINT_SUMMARY.md`, the `CDS` log §13/§14/§15,
  `score_behavior.py`, `cds_domain_test.py`, `cds_stage1_gate.py`, `cds_power_domain.py`,
  `judge_p2.sh`, `cds_submit_judge.sh` and every `cds*` run config. Confirmed from the raw
  artifacts, independently of the log:
  * the basket baseline `cds1A_basket_20260901_191635_1462938` holds **377** result rows;
  * the basket bank's selected population is **380** rows;
  * the three missing ids are **exactly** `566c998c6df83a30`, `56c76e11095a5d48`,
    `f953fbbb2376f8db`, all `domain=school_campus`, `example_position=near`,
    `n_target_occurrences=5`, `target_surface=basket`;
  * the baseline `summary.json → failures` records
    `{"resolve:occurrence_count_mismatch:text=5,tokens=6": 3}` and names those same three ids.
  * the crash site in an intervened arm is the pre-flight loop at `score_behavior.py:1642`
    (`resolve_occurrences` called outside any `try`), whereas the main loop catches the same
    exception at `score_behavior.py:1861`. **The remedy is therefore an up-front population
    exclusion, not a `try` around the pre-flight** — a `try` there would reintroduce exactly the
    silent-skip asymmetry that made this crash informative.
* **2026-09-02.** Cluster idle (`squeue -u` empty). Six L40S nodes up in `killable`.
