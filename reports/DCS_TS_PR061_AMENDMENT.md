# `DCS-PR-061` — PHASE 11's launcher, and the decision on `PR059-D1`

**Date** 2026-09-08 · **CPU only. No GPU. No SLURM job submitted or cancelled. No network. No
commit.** `configs/dcs_ts_pr059_phase11.json` is **FROZEN and was not edited**; the amendment is a
**new file**, `configs/dcs_ts_pr061_phase11_amendment.json`.

Read before writing a line: `configs/dcs_ts_pr059_phase11.json`,
`reports/DCS_TS_PR059_ANALYZER.md` (body + appendix A), `reports/DCS_TS_PR058_PR059_DESIGN.md` §2,
`scripts/dcs_ts_pr059_localisation.py`, `scripts/dcs_ts_pr059_verifier.py`,
`scripts/dcs_ts_prereg.py`, `external_md/DCS_THESIS_SCALE_MANDATE_20260906.md` §14, and — as the
model to imitate — `src/boombness/pr057_run_causal.py` + `reports/DCS_TS_PR057_RUNNER.md`.

---

## 1. What was written

| file | what it is |
|---|---|
| `src/boombness/pr059_run_localisation.py` | **NEW.** The launcher (`PR059-D2`). Loads the model **once**, loops the analyzer's **own** arm manifest, drives `score_behavior.py` in-process. |
| `configs/dcs_ts_pr061_phase11_amendment.json` | **NEW.** The amendment. Decides `PR059-D1`, re-derives the checklist as `V1…V15`, records four new defects. |
| `reports/DCS_TS_PR061_AMENDMENT.md` | **NEW.** This file. |

Nothing else was written **by this session**: `score_behavior.py`, `pair_common.py`, the PR-059
analyzer, the PR-059 verifier and every `*pr057*` / `*pr058*` file were never opened for writing
here. That is a statement about **this session**, not about the working tree — a concurrent writer
was editing `scripts/dcs_ts_pr057_causal.py` concurrently and committed it mid-session, and §7
says so with its numbers.

---

## 2. Observed numbers

| entry point | observed |
|---|---|
| `pr059_run_localisation.py --self-test` | **51 checks, 0 failed** |
| `pr059_run_localisation.py --mutate` | **43/43 RED** |
| `pr059_run_localisation.py --plan` | **78 arms**, 76 constructible, 2 unbuildable; `stage_partition` `{kill: 6, family: 72, smoke: 6}` |
| `pr059_run_localisation.py --stage smoke --split train --dry-run` | **rc = 0**, 6 arms constructed and validated, model NOT loaded, **nothing written** (`outputs/boombness/pr059_runner` does not exist afterwards) |
| `dcs_ts_pr059_localisation.py --self-test` | **92 checks, 0 failed** — unchanged |
| `dcs_ts_pr059_localisation.py --mutate` | **80/80 RED** — unchanged |
| `dcs_ts_pr059_verifier.py --self-test` | **22 checks, 0 FAILED** — unchanged |
| `dcs_ts_pr059_verifier.py --mutate` | **22/22 RED** — unchanged |
| `dcs_ts_prereg.py --check` (parent) | clean: FROZEN, 17 hashes pinned and verified, 12/12 mandate-21 fields |
| `dcs_ts_prereg.py --check --for-extraction` (parent) | **4 refusals** (U2, U3, U8, `analyzer_exists`) — unchanged |
| `dcs_ts_prereg.py --check` (**amendment**) | **clean**: FROZEN, **18 hashes** pinned and verified, 12/12 mandate-21 fields |
| `dcs_ts_prereg.py --check --for-extraction` (**amendment**) | **7 refusals** — V3, V8, V10, V11, V12, V13 and `artifacts.analyzer_exists` |
| repo tests: the **26** files importing `score_behavior` / `pair_common` / `dcs_ts_prereg` / the PR-059 analyzer | **676 passed, 1 warning, 605.02 s** — RAN TO COMPLETION |

**`--plan` reproduces the analyzer's arm count exactly: 78.** The runner does not build a manifest;
it calls `dcs_ts_pr059_localisation.build_arm_manifest`, and `--self-test` asserts
`build_arm_manifest.__module__ == "dcs_ts_pr059_localisation"` so the import cannot quietly become
a copy.

**The argv was validated end to end on CPU, against the real `score_behavior`**, with a
deliberately wrong `--expect-n`:

```
[score] DCS-PR-059 U1 declared-offset scope S_C: 1 row(s) [-10]
[score] population filter {'query_kinds': ['semantic_one_word'],
        'conditions': ['natural_doublespeak'], 'n_examples': [4]} -> {'n': 1160, ...}
SystemExit: REFUSING: population is 1160 rows, --expect-n says 999999.
```

Every flag parsed, the declared-offset selector was accepted, the population bound — **before the
model was loaded.**

---

## 3. `PR059-D1` — the decision, and what it costs

### 3.1 The arithmetic

`dose_matching.per_scope_random_row_control` requires, *for every scope of size m*, a seeded random
**m**-row draw from the query span **excluding the scope's own rows**. The query span is **28 rows**
(re-derived in 6,900/6,900 prompts). The pool is therefore `28 − m`, and the control exists **only
where `28 − m ≥ m`, i.e. `m ≤ 14`.**

| scope | m | pool | control |
|---|---|---|---|
| `S_A` | 5 | 23 | ✅ |
| `S_C` | 1 | 27 | ✅ |
| `S_F` | 1 | 27 | ✅ |
| `S_F2` | 1 | 27 | ✅ |
| **`S_D`** | **22** | **6** | ❌ |
| **`S_E`** | **23** | **5** | ❌ |
| **`S_G`** (reference) | **28** | **0** | ❌ |

Three independent derivations agree: the analyzer's `random_row_control_constructible()`,
`score_behavior.random_row_control_rel_end()` (which refuses by name), and the verifier's `T10`.
No GPU time changes it.

### 3.2 The decision: **option 3**, and the honest headline

> **PHASE 11's declared primary contrast — `S_D` vs `S_E` — CANNOT BE RUN AS DESIGNED.**
> The control the design requires for it does not exist and cannot be built on this template.
> This is recorded as a **CANNOT ANSWER with a stated reason**, not rescued.

`S_D`, `S_E` and `S_G` are **demoted**: they still run, still report their full per-domain
distributions, still enter `PHASE11_LOCALISATION` at their own Holm-corrected p-values (dropping
them would shrink the family — the analyzer's `M43` refuses that), and still carry their
**nondemo-key** control, whose draw pool is non-demonstration *keys* and is therefore untouched by
the 28-row span. What they do **not** get is the third of the four conjunctive success conditions.

### 3.3 Why each of the four logged options was accepted or refused

**1 — draw the control rows from the DEMO block. REFUSED.** It changes the experiment, not just the
control. `intervention.source_keys` is explicit: the demonstration keys are *"IDENTICAL in every
scope: only the DESTINATION rows vary. That is what makes the family a localisation experiment
rather than a dose sweep."* A control whose destinations are demonstration rows blocks demo→demo
attention — a different causal graph, upstream of the query entirely. It would answer *"does cutting
m rows anywhere matter?"* when the question is *"does cutting **these** m **query** rows matter?"*.
It is also not constructible through the instrument: `surface_span_from_rel_end` constrains every
offset to the row's own query span, precisely so a selector cannot cut a demonstration row and
report it as a query-position result.

**2 — allow overlap. REFUSED.** Then it is not a control. Any 23-row draw from a 28-row span shares
at least 18 rows with `S_E`; at m = 22 and m = 23 the "control" *is* the scope. Its expected effect
is the scope's effect, so it cannot fail — and a control that cannot fail is a check that binds
nothing. This repo has its own name for that shape: *a check that reads the same broken source*.

**3 — accept, demote, rely on the other declared controls. ADOPTED.** It is the only option that
changes nothing about what the arms are and states the loss plainly.

**4 — redefine the primary contrast onto a smaller scope pair (`S_C` vs `S_F`). REFUSED.** It would
make the headline a comparison the design *itself* predicts is uninformative, and it says so before
any data exist: `primary.negative._this_is_a_real_result` — *"A single-row null (`S_C`, `S_F`) is
the EXPECTED shape and on its own is close to uninformative"*, citing arXiv:2605.04061's 0%
single-position task transfer across all 28 layers despite 100% probing accuracy. Promoting it
would be **choosing the contrast that survives rather than the contrast the question asks** —
subset shopping with the selection moved one level up. `S_C` vs `S_F` remains an exactly
dose-matched, fully controlled **reported** comparison; it is simply not promoted.

### 3.4 A fifth option, identified here — named, and deliberately NOT adopted

The primary contrast is a **difference of two scopes**, and what needs controlling is the **one row
by which they differ**. The dose-matched control for that row is not an m-row draw at all — it is

> **`S_D` ∪ {one random non-codeword row}** — m = 1 drawn from the span excluding `S_D`'s 22 rows
> *and* excluding the codeword row −10. Pool = **5** (`{−5, −4, −3, −2, −1}`), 5 distinct 1-row
> draws available for the 3 the design requires.

That arm is 23 rows, **exactly** matched to `S_E`, and differs from it only in *whether the added
row is the codeword*. It is arithmetically constructible. **It is not adopted here**, because it is
a **new arm**, and the arm manifest is built by the analyzer that was committed before the outcome
exists — `artifacts._freeze_rule`: *"The analyzer is committed BEFORE the outcome exists. It is not
edited to rescue an outcome. A new design is a new preregistration."* It is recorded as the
constructive path a **successor preregistration** should take, and it is not smuggled into this one.
One caveat travels with it: the 5 available substitutes are exactly `S_A`'s scaffold rows, so the
arm is only interpretable if `L-N5` holds.

### 3.5 What is LOST

1. **PHASE 11 cannot answer its own declared primary question.** *"Does removing the codeword row
   from an otherwise identical 23-row cut change the effect?"* is mandate §14.1's D-vs-E pair and
   the comparison this design was built around. It will be reported and will carry **no confirmatory
   weight**.
2. **The rows-versus-cells confound is not separated for `S_D`, `S_E` or `S_G`.** `PR-032` declared
   it could not separate rows from cells; the per-scope random-row control was this phase's answer,
   and for the three largest scopes the answer is withdrawn. Within `S_A`, `S_C`, `S_F`, `S_F2` it
   still holds.
3. **`S_D` vs `S_E` cannot separate "the codeword row specifically" from "one more row of any
   kind".** The two arms differ by one row of *dose* as well as by that row's *identity*, and those
   are exactly what a 23rd-random-row control (§3.4) would have separated. **Any `S_D`/`S_E`
   difference is an upper bound on the codeword row's contribution, never an estimate of it.**
4. **Success condition 3 is unevaluable for the three largest scopes**, and success is conjunctive
   (*"Any three of four is not a localisation result"*), so if the only scope reaching half of `S_G`
   is `S_D` or `S_E` the phase's verdict is **CANNOT ANSWER — not a positive**.
5. **`S_G`, the denominator of every fraction this phase reports, has no control either.** Nothing
   in the manifest ever asked for one, so no Holm-corrected claim rests on it — but the parent's
   *"for every scope"* clause is contradicted, and the contradiction is recorded rather than read
   past.

### 3.6 What is NOT lost

`S_A` (the scaffold null `L-N5`), `S_C` (the codeword row), `S_F` (the readout row) and `S_F2` keep
a fully constructible 3-draw dose-matched random-row control. **`S_C` vs `S_F` — exactly matched at
1 row each, both controlled — is intact**, and is what the phase can still answer cleanly. The
nondemo-key control exists for every scope.

**One caveat carried forward, not introduced here.** `reports/DCS_TS_PR059_ANALYZER.md` §5 already
records it: `S_C`'s random-row draw 0 lands on `rel_end −9`, which **is** `S_F`'s row and the
`following` read site. It is a legal draw from the declared pool, but a reader comparing `S_C`
against its own control is then comparing it against `S_F`. So "fully controlled" means the control
exists and is seeded and distinct — not that draw 0 is uninformative-by-construction. That is a
reporting caveat for whoever writes the `S_C` vs `S_F` comparison up, and it is not fixed here. Every scope's fraction of `S_G`, the 0.5 rule, the Holm
family, `S_B` at p = 1.0 and both installation strata are unchanged.

### 3.7 Against mandate §14

Mandate §14.1 says exactly two things about dose: *"define a SMALL family such as A…F"* and
*"Match dose wherever the scientific comparison requires it."* It does **not** require a random-row
control for every scope — that is the parent's own (good) tightening. Where the scientific
comparison requires matched dose, this decision leaves it matched: `S_C` vs `S_F` is 1 against 1,
and `S_D` vs `S_E` is 22 against 23 by construction. What is withdrawn is the parent's *extra*
requirement in the three places it is arithmetically unbuildable. §14.1 also says *"If a further
hypothesis is suggested by these results: new preregistration. No subset shopping."* — which is why
option 5 is named and not adopted, and why option 4 is refused.

**Declared before any outcome exists.** No PHASE 11 arm has been scored on any bank on any channel:
the analyzer refuses with *"78 arm tags searched, 78 absent"* and the verifier with *"82 declared
arm(s) searched, 0 present on disk"*. This decision cannot have been made to fit a number.

---

## 4. `PR059-D2` — the launcher

`scripts/dcs_ts_readout_multi.py` forwards **no** `--only-cell`, **no** `--knockout-scope` and **no**
row-set flag, so every line `--plan` prints is a design statement. `src/boombness/pr059_run_
localisation.py` is the launcher, built on PHASE 9's `Q4b` pattern:

| requirement | how it is met |
|---|---|
| load once, loop the manifest | `ModelCache` memoises `ds_common.load_model`; `score_behavior.main()` runs in-process per arm with `sys.argv` set. `DONE.json.model_loads` is the number that proves it. |
| **import** the manifest, scopes and gates | `build_arm_manifest`, `ArmSpec`, `declared_scopes`, `query_span_rel_end`, `random_row_control_draw` / `_constructible`, `liveness_gate`, `audit_end_relative`, `assert_realised_equals_declared`, `resolver_failure_gate`, `bind_rows`, `control_band_gate`, `assert_scope_has_its_control` all come **from the analyzer**. Nothing is restated. |
| cross-check every argv against the analyzer | `assert_argv_agrees_with_analyzer()` parses the analyzer's own `launch_command()` and compares bank, cell, channel, dose, attention implementation, intervention arm/mode/band/alpha, knockout scope and the declared `rel_end` row set. Any disagreement is a refusal (mutations `M07`–`M11`). |
| `--stage` / `--split` binding the frozen split | an **outcome-independent** `--exclude-prompt-ids` list built from `dcs_ts116_domain_split.json` (its sha is written into the file's own header comment) plus `--expect-n`. TRAIN binds **67 analysed domains × 10 = 670 rows**; TEST binds **23 × 10 = 230**. Both the *analysed* count and the manifest's *assigned* count are checked, against different sources. |
| `--expect-n` **equals** `--limit` (`C-123`) | clamped **once**, above the ctx, and refused in **both** directions before submission — not by `score_behavior`'s row-count guard after a queue wait and a model load. Mutations `M01`–`M03`. |
| refuse a stage with a prior verdict (`C-124`) | `assert_stage_has_no_prior_verdict()` runs **before any arm**, and the remedy is deliberately manual (archive with provenance, never overwrite). Mutations `M04`–`M06`. |
| SLURM provenance in every terminal record (`A15`) | `slurm_provenance()` — job id, array task id, nodelist, hostname, pid — read from the environment, `null` off a batch node, never invented. |
| fail-closed per arm; resumable manifest; `DONE`/`ABORTED` never both | a non-zero exit, a missing `DONE.json`, zero rows, a row count ≠ the bound population, SDPA on the loaded config, a dead hook, a decode leak, a zero realised dose, a realised row set ≠ the declared one, a pinned absolute index — each **stops** the stage and writes `ABORTED.json`. A manifest arm claiming `done` whose directory has no `DONE.json` is reset to pending. |
| CPU-testable `--plan` / `--dry-run` | both construct and validate every arm, load no model and **write nothing** (the exclusion files are computed and hashed, not written). |

**The second half of `PR059-D2`, recorded and not closed.** `launch_command` also prints
`--nondemo-matched-draws N --nondemo-draw-seed S`, and **neither flag exists on `score_behavior`
either**. The nondemo control is selected by the *intervention arm name* (`nondemo_matched_d1..3`)
and seeded from `--seed`. The runner carries that as its **only other** sanctioned translation, with
the analyzer's 0-based draw index / producer's 1-based arm suffix written down once and asserted.

**The stage-aware checklist gate runs for every stage, including the smoke.** A gate skipped for
the one stage anybody actually runs is the *threshold published but never enforced* failure. An item
is scoped out only if the scope is declared **and** the runner carries a predicate that re-derives
its relevance from the arm manifest and the run's own binding **and** that predicate says it is
irrelevant. `artifacts.analyzer_exists` is applied on the same re-derivation and no other;
`scripts/dcs_ts_prereg.py --for-extraction` is **unchanged** and still refuses on it
unconditionally.

---

## 5. Four NEW defects, found while building the launcher

**`PR059-D4` — the liveness producer and consumer do not share a schema. BLOCKING (item `V10`).**
The analyzer's `liveness_gate()` reads `hook_fired_count`, `n_cells_edited_expected`,
`n_cells_edited_realised`, `n_forward`, `n_prefill_edits`, `n_decode_edits` — the **PR-057
project-out** schema (`pair_common.hook_stats_dict`). The **attention-knockout** producer writes
`hook_n_forward`, `hook_n_edits`, `hook_n_prefill_edits`, `hook_n_decode_edits`,
`hook_n_query_rows_edited`, `hook_n_keys_masked` — and **no `hook_fired_count` and no expected cell
count anywhere**. Three of the six fields have **no producer source at all**, so *"realised ==
expected cells"* cannot be evaluated for a knockout arm and `liveness_gate` would VOID every healthy
arm for a schema reason rather than a scientific one. This is the `C-117` class recurring. The
runner **refuses to invent** the missing counts — PR-057's runner records exactly this lesson
(*"no longer invents `expected := n_destination_rows`"*) — gates each arm on the producer's own
fields plus the realised-vs-declared audit, and writes **both** verdicts into `PR059_ARM_GATE.json`.
A field with no mapping is left **absent**, never defaulted to 0. Fixing it needs
`score_behavior.py` or `pair_common.py`, both held by other work: **reported, not fixed.**

**`PR059-D5` — the analyzer's manifest and the independent verifier's expected arm set disagree,
78 against 82. BLOCKING (item `V11`).** The difference is exactly (a) the verifier expects 3
nondemo-key draws for the reference scope `S_G` and the analyzer's `build_arm_manifest` gives the
reference **no** controls (`"the denominator gets no dose-matched control"`), **+6**; and (b) the
analyzer adds one disabled-hook **bridge** arm per bank that the verifier does not know about,
**−2**. Under the verifier's `R5` a complete 78-arm run would fail **both ways at once** — six arms
*"complete on disk and absent from the output"* and two *"arms nobody preregistered"*. One of the
two derivations is wrong and the disagreement is the finding. Neither file is edited here.
Observed: `only_in_analyzer_manifest = ['pr059_basket_bomb_s_g_bridge_n4',
'pr059_button_bomb_s_g_bridge_n4']`.

**`PR059-D6` — null `L-N1`, the disabled-hook bridge, is NOT CONSTRUCTIBLE for an attention
knockout. BLOCKING (item `V12`).** `pair_common.DisabledHookBridge` bridges an inner context that
exposes `(_hook, layer)` or `(_hooks, layers)`. `ScopedAttentionKnockout` — the class **every
intervened** arm of this phase installs (the untouched baseline `S_0` installs no hook at all) —
exposes `layers` and `_handles` and **no hook attribute**, so the bridge
raises:

```
TypeError: DisabledHookBridge cannot bridge Stub: it exposes neither (_hook, layer)
           nor (_hooks, layers). Refusing rather than registering nothing ...
```

Measured on CPU against the real class, not inferred from the source. `L-N1` is **BLOCKING** in the
frozen file and the manifest builds one bridge arm per bank, so the `kill` stage cannot complete as
designed. The launcher refuses the bridge arm **by name** rather than launching it to die at the
node after a queue wait and a model load. Fixing it needs `pair_common.py`, held by other work.

**`PR059-D7` — the analyzer has no verdict path. BLOCKING (item `V13`).**
`dcs_ts_pr059_localisation.analyse()` ends at the liveness / realised-row gates and returns 0 after
printing *"(baseline readout, then the kill conditions, … then the verdict — in that order)"*.
`evaluate_success()`, `holm_with_absent()`, `render_delta()` and `verdict()` are exercised only
under `--self-test` and `--mutate`. This is the same shape `PR-060` recorded for PHASE 9.
**`artifacts.analyzer_exists` therefore stays `false`** in the amendment, which keeps
`--for-extraction` fail-closed — the correct state today.

---

## 6. The amendment's checklist

`V1`–`V15`. Every parent item `U1`–`U10` is superseded **by name**; five items are new. Booleans
only (`C-086`).

| item | supersedes | blocking | done | in one line |
|---|---|---|---|---|
| `V1` | `U1` | ✅ | ✅ | the declared-offset selector; producer and analyzer agree at 4 sequence lengths, 0 mismatches |
| `V2` | `U2` + `PR059-D1` | ✅ | ✅ | the control where constructible; refused by name where not; **consequence decided** (§3) |
| `V3` | `U3` | ✅ | ❌ | the validation power run — GPU, never run |
| `V4` | `U4` | ✅ | ✅ | token map, 6900/6900 |
| `V5` | `U5` | ✅ | ✅ | the analyzer, 92/0 |
| `V6` | `U6` | ✅ | ✅ | its mutations, 80/80 |
| `V7` | `U7` | ✅ | ✅ | the independent verifier, 22/22 + 22/22 — **but see `V11`** |
| `V8` | `U8` | ✅ | ❌ | the smoke — GPU, now **launchable** |
| `V9` | `U8` (launcher half) + `PR059-D2` | ✅ | ✅ | **the launcher** |
| `V10` | (new) `PR059-D4` | ✅ | ❌ | the liveness schema mismatch |
| `V11` | (new) `PR059-D5` | ✅ | ❌ | 78 vs 82 arms |
| `V12` | (new) `PR059-D6` | ✅ | ❌ | the bridge is unbuildable |
| `V13` | (new) `PR059-D7` | ✅ | ❌ | the analyzer has no verdict path |
| `V14` | `U9` | ⬜ | ❌ | fair share; the staged order is now a code path |
| `V15` | `U10` | ⬜ | ❌ | re-hash the token-role map |

`go_no_go.verdict` = **NO-GO for the confirmatory stages; CONDITIONAL-GO for the `U8` smoke alone.**

---

## 7. Nothing else moved — and the UNSCOPED `git status --porcelain`

At the end of this session, the only entries attributable to it are:

```
?? configs/dcs_ts_pr061_phase11_amendment.json
?? reports/DCS_TS_PR061_AMENDMENT.md
?? src/boombness/pr059_run_localisation.py
```

Everything else `git status --porcelain` lists is pre-existing untracked data
(`data/boombness_prompts/boombness_prompt_bank_ts116*.jsonl`, `demo_pools_116dom_ts_*.json`,
`ts_cand/`, `ts_repair/`, `ts_smoke/`) that this session neither created nor touched.
**No `git add`, no `git commit`, no `git stash`, and nothing under `outputs/`.**


| entry point | recorded in `DCS_TS_PR059_ANALYZER.md` appendix A | observed here |
|---|---|---|
| `dcs_ts_pr059_localisation.py --self-test` / `--mutate` | 92/0 · 80/80 RED | **92/0 · 80/80 RED** — unchanged |
| `dcs_ts_pr059_verifier.py --self-test` / `--mutate` | 22/0 · 22/22 RED | **22/0 · 22/22 RED** — unchanged |
| `dcs_ts_prereg.py --check --for-extraction` (parent) | 4 refusals | **4 refusals** — unchanged |
| PHASE 9 `dcs_ts_pr057_causal.py --self-test` / `--mutate` | 111/0 · 90/90 | **117/0 · 102/102** |
| PHASE 9 `pr057_run_causal.py --self-test` / `--mutate` | 70/0 · 41/41 | **70/0 · 41/41** — unchanged |

**The PHASE 9 analyzer's numbers moved, and not because of this session.** Mid-session
`git status --porcelain` showed `M scripts/dcs_ts_pr057_causal.py`, `M reports/DCS_TS_CLAIM_TABLE.md`
and `?? reports/DCS_TS_PHASE9_VERDICT_REVIEW.md` — a **concurrent writer's** work in this shared
tree, which they committed before this session ended (those entries are gone from the final
`git status`). This session did not open that file for writing, and it is not in the three-file diff of §1.
Both PHASE 9 harnesses pass at their current numbers. **Measured once, after the work** — there is
no "before" measurement from this session to compare against, and claiming one would be inventing
it.

**Repo tests ran to completion.** The 26 test files that import `score_behavior`, `pair_common`,
`dcs_ts_prereg` or the PR-059 analyzer: **676 passed, 1 warning, in 605.02 s** (`pytest -q`, the
`poc_stage2` interpreter). Nothing in the tree imports the new launcher, so it cannot have added a
failure — but that is an argument and the 676 is a measurement.

---

## 8. Reproduce

```
python3 src/boombness/pr059_run_localisation.py --self-test
python3 src/boombness/pr059_run_localisation.py --mutate
python3 src/boombness/pr059_run_localisation.py --plan
python3 src/boombness/pr059_run_localisation.py --stage smoke --split train --dry-run
python3 scripts/dcs_ts_prereg.py --check                  configs/dcs_ts_pr061_phase11_amendment.json
python3 scripts/dcs_ts_prereg.py --check --for-extraction configs/dcs_ts_pr061_phase11_amendment.json
python3 scripts/dcs_ts_pr059_localisation.py --self-test   # 92/0, unchanged
python3 scripts/dcs_ts_pr059_localisation.py --mutate      # 80/80, unchanged
python3 scripts/dcs_ts_pr059_verifier.py --self-test       # 22/0, unchanged
python3 scripts/dcs_ts_pr059_verifier.py --mutate          # 22/22, unchanged
```

---

## 9. The exact `sbatch` line for the `U8` smoke — **NOT SUBMITTED**

```bash
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood

# 1. the argsfile MUST live on the SHARED filesystem -- /tmp is node-local and the job dies in 3s.
#    NO quote characters and NO spaces inside a value: BOOMB_ARGS is word-split (job 766661).
#    `--knockout-rel-end-rows` is passed by the RUNNER, not here, and always with '='.
cat > outputs/boombness/pr059_smoke_args.txt <<'EOF'
--prereg configs/dcs_ts_pr059_phase11.json --amendment configs/dcs_ts_pr061_phase11_amendment.json --stage smoke --split train --smoke-limit 40
EOF

# 2. submit. BOOMB_EXPECT and BOOMB_REQUIRE_ARGS=1 are BOTH set: without them a mistyped variable
#    name falls through to the runner's default script and exits COMPLETED 0:0 having run the
#    wrong thing (jobs 853040-853045, ~1.7 GPU-hours, and nothing caught it).
sbatch --export=ALL,BOOMB_SCRIPT=pr059_run_localisation.py,BOOMB_EXPECT=pr059_run_localisation.py,BOOMB_REQUIRE_ARGS=1,BOOMB_ARGSFILE=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/boombness/pr059_smoke_args.txt \
       --time=02:00:00 \
       src/boombness/slurm/run_boombness.sh
```

It runs **6 arms**: the untouched baseline `S_0`, the reference scope `S_G` and the codeword scope
`S_C`, on both confirmatory banks, 40 TRAIN rows each, **one model load**. Notes that are part of
the command:

* `run_boombness.sh` already pins the six L40S nodes via `#SBATCH --nodelist`. **Do not add
  `--exclude`** — it nullifies that directive.
* `--mem=48G`, `--cpus-per-task=4` are the script's defaults; do not raise them.
* Budget ≤ 2 concurrent model-loading jobs per node. This is **one** job for the whole stage.
* **`--dry-run` first, always.** It exits 0 today and writes nothing.
* A smoke is **not a result**: it reads TRAIN, it is truncated to 40 rows, and no number it produces
  may enter any estimate. Its whole content is that the instrument does what the design says.

---

## 10. What still blocks PHASE 11 from a GPU submission

**The smoke is unblocked.** Everything else is not.

1. **`V3` / `U3` — power has never been measured on the concept-free channel.** `--u3-inventory`
   returns rc = 2: **0** knockout runs on that channel exist on **any** of the 6 preregistered
   `ts116m` banks. `power.mde.in_semantic_logodds_nats` stays `null`. This is a **validation** run,
   and the launcher can now do it — but it is a separate submission and it must print PROCEED before
   any confirmatory stage exists.
2. **`V12` / `PR059-D6` — the `kill` stage cannot complete as designed.** `L-N1` is a BLOCKING null
   and its bridge arm cannot be constructed for an attention knockout. Needs `pair_common.py`.
3. **`V10` / `PR059-D4` — the analyzer's liveness verdict is not evaluable for a knockout arm.**
   Needs `score_behavior.py` or `pair_common.py`.
4. **`V11` / `PR059-D5` — 78 arms against 82.** Until one derivation is corrected, a complete run
   fails the independent verifier's `R5` in both directions at once.
5. **`V13` / `PR059-D7` — the analyzer emits no verdict.** `analyse()` ends at the liveness gates,
   so even a perfect run would produce no localisation result, and `artifacts.analyzer_exists`
   correctly stays `false`.
6. **`PR059-D1` itself is not "unblocked" — it is DECIDED.** The phase's declared primary contrast
   cannot be run as designed and will report **CANNOT ANSWER for a stated reason**. That is the
   outcome, not an obstacle to be removed.

Items 2, 3 and 4 all need files this session was instructed not to write. Each is **reported, not
worked around**, and each is a named refusal reachable from `--plan` on CPU before a queue slot is
spent.
