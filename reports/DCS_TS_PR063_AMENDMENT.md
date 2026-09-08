# DCS-PR-063 — PHASE 10's readout, repaired without regenerating the bank

**Amendment config:** `configs/dcs_ts_pr063_phase10_amendment.json` (FROZEN 2026-09-08)
**Parent:** `configs/dcs_ts_pr058_phase10.json`, sha16 `574e94b4bf4807cf` — NOT edited, no design field changed.
**Diagnostic this rests on:** `reports/DCS_TS_P10_CELLBE_OPTION_MASS.md`, sha16 `5c7ad43b7e451601`.
CPU only. No job was submitted or cancelled. No GPU. No network. Nothing was committed.

---

## The headline

**The correct option set IS recoverable from artifacts already on disk. Nothing is regenerated and
no pin moves.**

The word cells B/E need as their second option is the word their demonstrations remap the concept
*toward*, and it is carried by the demonstration-pool file the parent preregistration **already
pins by content hash**:

> `data/boombness_prompts/demo_pools_116dom.json` → `pools["<demo_pool_domain>|benign"]["natural_word"]`
> — `_meta.content_sha16` `976aa2b0b617118d`, which is `population.pools.shared_pools_sha16` in
> `dcs_ts_pr058_phase10.json`, unchanged.

Cell E's demonstrations are the **benign pool with `carrot` substituted by the concept**:

| bank text (cell E, hospital_supply) | benign pool sentence |
|---|---|
| "a large crate of **bomb** puree" | "a large crate of **carrot** puree" |
| "a fresh supply of organic **bomb** juice" | "a fresh supply of organic **carrot** juice" |

**Per-row coverage: 66 816 / 66 816** cell-B and cell-E rows across all six `ts116m` banks resolve
to a non-empty, non-degenerate contrast word. 0 unresolved, 0 equal to the concept. `natural_word`
is `carrot` in 116/116 benign pools (a global property of the pool file, not per-domain), and
`demo_pool_domain == domain` on 133 632 / 133 632 rows.

*Corroboration (not the proof, which is the field itself):* inverting the substitution on cell-E
demo blocks — replacing the concept with `carrot` — reproduces a **verbatim** benign-pool sentence
on **149 922 / 150 336 = 99.72 %** of demo lines over the six banks. The 414 residuals are
capitalised-inside-quotes forms and length-truncated lines, not a different pool.

**What was genuinely absent, and is still reported absent:** `mapping_use_options` is `None` on all
22 272 rows of every `ts116m` bank, exactly as the diagnostic §2 and the parent's `O3_mapping_use`
say. The diagnostic's recommendation to regenerate was reached by looking at *that* field only; it
did not look at the demonstration pools. `O3` stays **UNCONSTRUCTIBLE ON THIS BANK** and the repair
does not use it.

### Alternatives, costed and declined

| option | what it costs | what it invalidates |
|---|---|---|
| **Per-cell option set from the pinned pool** ✅ chosen | one flag on `score_behavior.py`; zero regeneration | nothing |
| A new bank **family** | full generation pass + a new token-role map + a new installation table (R-116 is measured on `ts116m`) | nothing pinned — but PHASE 10 would then sit on a *different population* from PHASE 9, so the within-phase symmetry PR-058 exists to obtain becomes a cross-family comparison |
| **Regenerate `ts116m`** ❌ | generation + re-pin of 5 configs + re-verification of every downstream artifact | `bank_file_sha16`/`bank_rows_sha16` in `dcs_ts_pr048`, `pr057_phase9`, `pr060_phase9_amendment`, `pr058_phase10`, `pr059_phase11` — i.e. the provenance of a COMPLETED confirmatory result (PHASE 9, 30 arms, 6900 rows) |

---

## The rule, and why it is keyed on `query_surface`

```
query_surface == "codeword"  (cells A/C)  ->  {concept, codeword}                    [UNCHANGED]
query_surface == "concept"   (cells B/E)  ->  {concept, benign pool natural_word}    [REPAIRED]
```

It is **not** keyed on the cell name and **not** on the demonstration valence. Cell B's
demonstrations are the *harm* pool, whose own `natural_word` **is** the concept — degenerate. It is
also the wrong question to ask of a matched specificity control: the parent's
`primary._largest_risk` mitigation (2) requires cell B to carry "the identical query text and the
identical ceiling" so that H1−H3 differences the ceiling out, and two cells scored on two different
axes cannot difference anything. So B and E share one axis, and on cell B the contrast option is the
counterfactual that was never installed — which is what a specificity control is for.

The readout **group names stay `concept` and `codeword`**, so `semantic_logodds =
logp_concept − logp_codeword` keeps its field names *and* the parent's declared H1 sign. The two
words actually scored are written to metadata and to **every row**
(`semantic_concept_word`, `semantic_contrast_word`, `semantic_options_source`), so no reader has to
infer them from a cell name.

---

## The A/C byte-identity proof

**Ground truth "before" is not re-derived from the code under test.** It is the answer set the two
runs on disk actually shipped, read from their `metadata.json`:
`{"concept": [" bomb", " Bomb"], "codeword": [" button", " Button"]}`, sha256[:16] **`bbb81e6ccf7c34b3`**
— identical in `ts116m_readout_button_bomb_20260907_133811_3183103` and
`ts116m_p10be_button_bomb_20260908_190838_351592`.

`src/boombness/signals.py` is **unmodified** (empty `git diff`), and the `sem_variants = {...}`
construction line is unchanged from git HEAD.

| bank | cells A / C — sha16 | == pre-amendment | cells B / E — sha16 |
|---|---|---|---|
| button_bomb | `{" bomb"," Bomb"}/{" button"," Button"}` `bbb81e6ccf7c34b3` | **True** | `{" bomb"," Bomb"}/{" carrot"," Carrot"}` `95e6fc5f20682015` |
| basket_bomb | `…/{" basket"," Basket"}` `a624225d36810b5a` | **True** | `95e6fc5f20682015` |
| button_knife | `…/{" button"," Button"}` `6d4afb4482097de3` | **True** | `9e5e0c4d8ad19ed7` |
| basket_knife | `…/{" basket"," Basket"}` `fcc2fbe1c4133504` | **True** | `9e5e0c4d8ad19ed7` |
| button_gun | `…/{" button"," Button"}` `2b29e43308a7c29c` | **True** | `c43a74593fd5dba5` |
| basket_gun | `…/{" basket"," Basket"}` `3bdf384ac86aca18` | **True** | `c43a74593fd5dba5` |

**6/6 banks, cells A and C byte-identical.** Computed over all 22 272 rows of each bank (133 632
rows).

**Enforced in code, not only here.** `score_behavior.main()` REFUSES to start if a cell resolved to
the bank pair does not reproduce the run-wide set exactly, and if one cell resolves to two option
sets. A published identity claim with no code path is B-020.

**The launcher too.** `scripts/dcs_ts_readout_multi.py` appends the four new flags only when they
differ from `score_behavior`'s defaults; `--print-cmd-only` (CPU, launches nothing) reproduces job
869869's command line byte for byte against that run's own `config.json`.

---

## The option-mass gate, PER CELL AND PER DOSE

Recomputed CPU-only from the written `results.jsonl` of the two runs on disk, with the same function
the amended gate uses (`score_behavior.option_mass_block`). Gate 0.05 on `median_true`.
**These rows carry the PRE-amendment option set** — the table measures the defect, not the repair.

### job 869869 — cells B/E, `semantic_one_word`

| bucket | n | median_true | p10 | p90 | gated | verdict |
|---|---|---|---|---|---|---|
| **POOLED** | 2784 | 0.010148 | 0.000295 | 0.054883 | — | BELOW GATE |
| B / n0 | 232 | 0.000330 | 0.000051 | 0.001864 | no | not gated |
| B / n4 | 1160 | 0.012608 | 0.002509 | 0.036601 | **yes** | **BELOW GATE** |
| E / n0 | 232 | 0.000330 | 0.000051 | 0.001864 | no | not gated |
| E / n4 | 1160 | 0.015763 | 0.001245 | 0.092356 | **yes** | **BELOW GATE** |

### run 20260907_133811 — cells A/C, `semantic_one_word`

| bucket | n | median_true | p10 | p90 | gated | verdict |
|---|---|---|---|---|---|---|
| **POOLED** | 2784 | 0.082485 | 0.011940 | 0.566811 | — | PASS |
| A / n0 | 232 | 0.041589 | 0.017590 | 0.064549 | no | not gated *(would have been BELOW)* |
| A / n4 | 1160 | 0.059274 | 0.005875 | 0.216002 | **yes** | PASS |
| C / n0 | 232 | 0.041589 | 0.017590 | 0.064549 | no | not gated *(would have been BELOW)* |
| C / n4 | 1160 | 0.313414 | 0.039177 | 0.732514 | **yes** | PASS |

### run 20260907_133811 — cells A/C, `semantic_forced_choice` (SECONDARY DISPLAY ONLY)

| bucket | n | median_true | gated | verdict |
|---|---|---|---|---|
| **POOLED** | 2784 | 0.358080 | — | PASS |
| A / n0 | 232 | 0.000421 | no | not gated |
| A / n4 | 1160 | 0.266485 | yes | PASS |
| C / n0 | 232 | 0.000421 | no | not gated |
| C / n4 | 1160 | 0.876273 | yes | PASS |

Quoted as a gate table only. Its question names both options and answers itself (R-116), and the
parent forbids falling back on it.

**The pooled pass on A/C was carried entirely by C/n4.** Three of its four sub-buckets sit at or
below 0.05. With dose 0 excluded on the evidence below, both *gated* A/C buckets pass on their own.

### Dose 0: EXCLUDED from the gate, and still reported

Decision: **excluded**, via `--option-mass-gate-min-dose 1`, recorded with `gated: false` and a
reason string.

*Why.* At dose 0 the passage carries no demonstrations, the queried word occurs only inside the
question, and the correct one-word answer is "None" — the decoded argmax is `" None"` on **232/232
rows in every cell of both runs on disk**. Neither scored option is that answer, in any cell, so the
instrument is **inapplicable** there rather than the model disengaged, and feeding the gate a
population where it cannot apply measures the question rather than the model.

*Why excluded rather than "scored as None".* A `None` median propagates as a **NaN refusal** through
the tail gate, which would condemn a bucket that is behaving exactly as it should. It is excluded
from the *verdict*, never from the *record*.

A gate whose only buckets are ungated **refuses** rather than passing vacuously
(`kill_condition_channel_by_cell_dose`, mutation M56 RED).

---

## What this does NOT settle

`p(carrot)` has never been scored by any run on this bank and **cannot** be computed from the
written rows — `results.jsonl` carries `logp_concept`, `logp_codeword`, `option_mass` and `top1_id`
only. `" Carrot"` is the argmax on **0 of 1160** cell-E dose-4 rows, which bounds nothing about its
mass. The repair makes the gate *mean* something on cells B/E; it does **not** promise the mass will
clear 0.05. That measurement is amendment item **A2**, and it is still the phase's kill condition.

---

## Defence in depth: a wrong option set is now VOID, not CANNOT ANSWER

Job 869869 had 2784 rows, zero failures and a clean `DONE.json`. Every liveness, population and
provenance check in the analyzer *and* the verifier would have passed it. The tail gate caught it and
then **mis-named** it — reporting a disengaged model when the model's argmax was
` Threat` / ` Explos` / ` Device` on 69 % of cell-B dose-4 rows. A mass gate cannot tell a
disengaged model from a dead second option.

* **Analyzer** `scripts/dcs_ts_pr058_symmetry.py` — new `instrument_gate()` **raises** on a
  concept-query row scored against the bank codeword, on a row that does not record its contrast
  word, and on a zero-row check. New `kill_condition_channel_by_cell_dose()` refuses a pooled key and
  refuses a gate that binds only ungated doses.
* **Verifier** `scripts/dcs_ts_pr058_verifier.py` — new check class **R9**, which re-derives the
  expected contrast word **per row** from the pinned bank's `query_surface` and the pinned pool's
  `natural_word`, imports nothing from the producer, and re-hashes the pool against the amendment's
  pin. R9 reports **EMPTY, never PASS**, when the amendment is absent from disk.

---

## Verification — every number observed today

| check | result |
|---|---|
| `dcs_ts_pr058_symmetry.py --self-test` | **57 checks, 0 failed** (was 55/0; `+instrument_gate` n=4, `+kill_channel_by_cell_dose` n=4) |
| `dcs_ts_pr058_symmetry.py --mutate` | **56/56 refusals** (was 52/52; M53–M56 new) |
| `dcs_ts_pr058_verifier.py --self-test` | **PASS**, 9 assertions (clean synthetic tree passes; empty root still FAILS R5; zero-bound check still EMPTY) |
| `dcs_ts_pr058_verifier.py --mutate` | **18/18 caught by the named check** (was 16/16); **X17** "cells B/E scored against the BANK CODEWORD (job 869869's defect)" → RED on R9; **X18** "the rows do not record which two words the forced choice was between" → RED on R9 |
| `dcs_ts_pr058_verifier.py` on the real run root | **R9 instrument pins PASS** (mode=per_cell_remap, valence=benign, pool sha16 `976aa2b0b617118d`, gate=per_cell_dose/min_dose=1); **R5 FAIL** — no PR-058 arm has ever produced a complete run. Correct. 3/4. |
| `dcs_ts_prereg.py --check` on the amendment | **clean**: status FROZEN, **16 hashes pinned and verified**, all 12 mandate-21 fields present |
| `dcs_ts_prereg.py --check --for-extraction` | **4 refusals** — A2, A3, A4, A5 BLOCKING and not done |
| `dcs_ts_prereg.py --mutate` on the amendment | **6/6** mutations produced a refusal |
| `dcs_ts_prereg.py --check` on the **parent** | still **clean**, 17 hashes verified — no pin moved |
| `pytest tests` | run to COMPLETION twice. First run (before the fix below): **1692 passed, 5 failed, 7 skipped** in 22:09. Final run: **1693 passed, 4 failed, 7 skipped** in 21:10. The 4 remaining failures are all `tests/test_prompt_families_strict.py`, which shells out to `src/boombness/prompt_families.py` — a file this task did not touch, which is not in `git diff --name-only`, and whose generator now refuses earlier (exit 2, the incidental-word guard) than the test expects (exit 1, the strict alignment check). PRE-EXISTING, not mine. |
| refusal branches of `resolve_semantic_options_for_row` | absent pool / empty `natural_word` / contrast == concept / unknown `query_surface` / no domain → each a `ValueError` |
| pooled-block agreement | `option_mass_block()` == the inline pooled block on **3000/3000** random inputs incl. NaN and None; and asserted at runtime inside `score_behavior` |

### A defect found on the way, recorded and NOT fixed here (item A9)

The pooled tail gate's *failure* test reads `med` (the upper-middle element) while its own
`reportable` field, its own comment, and `tests/test_option_mass_gate.py` all read `median_true`.
`med >= median_true` by construction, so the pooled *failure* path is biased toward passing.

Swept over the corpus: **244** runs on disk carry an `option_mass` block, **241** buckets have both
fields, **230** differ, and the 0.05 verdict differs on **0 of 241** — no published verdict is at
stake today. It is left exactly as it was, because changing a published gate's definition on a shared
file while PHASE 9 and PHASE 11 are in flight is not a repair an instrument amendment gets to make.
The new per-cell gate reads `median_true`, the stricter of the two, so it does not inherit the bias.

### A second source-text pin, and the design it forced (my one test failure, fixed)

`tests/test_readout_liveness.py::test_the_readouts_run_INSIDE_the_intervention_contexts` walks the
AST of `main()` and asserts the literal string `_semantic(templated)` appears inside the
`contextlib.ExitStack` block — "if it did not, every forward-only intervention ever produced was a
baseline". Passing the per-row answer set as a second positional argument changed that call site and
broke the pin.

The pin was **not** weakened. The row's answer set now travels through a one-slot cell
(`_active_sem_variants`), set immediately before the call, and the call site reads
`_semantic(templated)` exactly as it always did. `score_behavior.py` sha16 is therefore
`2aa691c10b412ecf`, not the `f2a8ee74c2eb549c` of the first draft, and the amendment records both
the hash and the reason.

*Note on the refactor that was reverted:* folding the pooled loop into `option_mass_block()` broke
three source-text tests in `tests/test_option_mass_gate.py`, which pin the exact code of those six
lines. The pooled loop is therefore left byte-for-byte as it was and the two are held together by a
**runtime equality assertion** instead of by shared code — a second copy of a gate is a second gate
unless something compares them.

---

## Can PHASE 10 be re-run on GPU?

**The T2 / A2 pre-run: yes, and it is the next thing to run.** It is a readout-only, no-intervention
job over the same 2784 rows job 869869 already scored, with a correctly specified answer set.

**The knockout arms: no, not yet.** A2 (the repaired-instrument option-mass measurement), A3 (the
cell-E ceiling), A4 (parent T3, SD and power) and A5 (parent T10, the smoke run) are BLOCKING and
open; `--for-extraction` refuses on all four, which is the design working. And the parent's own
kill condition stands: if a *gated* (cell, dose) bucket is below 0.05 with the repaired option set,
no knockout job is submitted and the readout outcome is CANNOT ANSWER.

`--allow-tail-readout` is still **not** to be passed. The correct repair was a correct option set.

---

## The exact sbatch line — NOT SUBMITTED

This runs **A2 only**: the readout-only, no-intervention re-score of cells B and E with the
repaired answer set, over the two confirmatory bomb banks. It is one job, one allocation, one model
load, ~2 × 2784 rows. No knockout arm is submitted by it, and none may be until A2, A3, A4 and A5
close.

```bash
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood

# 1. the argsfile MUST live on the SHARED filesystem -- /tmp is node-local and the job dies in 3s.
#    NO quote characters and no spaces inside a value: BOOMB_ARGS is word-split.
cat > outputs/boombness/pr063_a2_args.txt <<'ARGS'
--banks button_bomb,basket_bomb --family ts116m --tag-prefix ts116m_p10be_pr063 --query-kinds semantic_one_word --conditions direct_harmful,concept_in_benign_ctx --n-examples 0,4 --attn-impl eager --arm base --semantic-options per_cell_remap --semantic-remap-pool data/boombness_prompts/demo_pools_116dom.json --option-mass-gate-scope per_cell_dose --option-mass-gate-min-dose 1
ARGS

# 2. submit. BOOMB_SCRIPT is a BARE FILENAME under src/boombness/, so a scripts/ target needs the
#    relative escape the runner documents. BOOMB_EXPECT and BOOMB_REQUIRE_ARGS=1 are BOTH set:
#    without them a mistyped variable falls through to the default script and exits COMPLETED 0:0
#    having run the wrong thing (jobs 853040-853045).
sbatch --export=ALL,BOOMB_SCRIPT=../../scripts/dcs_ts_readout_multi.py,BOOMB_EXPECT=../../scripts/dcs_ts_readout_multi.py,BOOMB_REQUIRE_ARGS=1,BOOMB_ARGSFILE=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/boombness/pr063_a2_args.txt \
       --time=04:00:00 \
       src/boombness/slurm/run_boombness.sh
```

Notes that are part of the command, not commentary:

- `run_boombness.sh` already pins the six L40S nodes via `#SBATCH --nodelist`. **Do not add
  `--exclude`** — it nullifies that directive.
- `--mem=48G`, `--cpus-per-task=4` are the script's defaults; do not raise them.
- At most 6 parallel jobs and at most 2 model-loading jobs per node. This is *one* job for the whole
  stage. PHASE 9 (PR-057) and PHASE 11 (PR-059) share the fair-share allocation — amendment item
  A10.
- Expect a **non-zero exit** if a gated `(cell, dose)` bucket is below 0.05. That is the gate
  working: the run is written, `option_mass_by_cell` records every bucket, and the readout is
  labelled not-reportable. **Do not pass `--allow-tail-readout`.**
- Dry-run the command line first with
  `python3 scripts/dcs_ts_readout_multi.py … --print-cmd-only` (CPU, launches nothing).
