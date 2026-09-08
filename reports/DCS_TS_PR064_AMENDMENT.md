# DCS-PR-064 — PHASE 11 AMENDMENT 2: five items close on measured evidence, and PHASE 11 is allowed to measure its own power

**Date** 2026-09-09 · **Commit at writing** `1d33f1cc` · **CPU only. No GPU. No SLURM job submitted
or cancelled. No network. No `git add` / `git commit` / `git stash`.**

Every `configs/*.json` file is FROZEN and none was edited. `configs/dcs_ts_pr059_phase11.json`
(sha16 `55c722ac1f5e9603`) and `configs/dcs_ts_pr061_phase11_amendment.json` (sha16
`1da927fb07200b20`) were opened **read-only**. An amendment is a **new file**.

**Files written by this work:**

* `configs/dcs_ts_pr064_phase11_amendment2.json` — new
* `src/boombness/pr059_run_localisation.py` — **two re-derivation predicates added, nothing else**
* `reports/DCS_TS_PR064_AMENDMENT.md` — this file

Nothing else was touched. Nothing named `*pr057*`, `*pr058*`, `*pr063*`, `score_behavior.py` or
`pair_common.py` was opened for writing.

---

## 1. The headline

`--stage kill --split validation --dry-run` refused on **six** items. **Five of them are now
closed on measured evidence.** The sixth, **V3 (power)**, is *what the blocked run measures* —
so it was **scoped**, not closed.

| item | DCS-PR-061 | DCS-PR-064 | on what |
|---|---|---|---|
| `V8` smoke | BLOCKING, not done | **done** | slurm job **870382**, 6 arms, 240 rows, 972.23 s |
| `V10` liveness schema (D-4) | BLOCKING, not done | **done** | producer-side counts, `expected=12 realised=12 hook_fired_count=2` |
| `V11` arm-set disagreement (D-5) | BLOCKING, not done | **done** | **84 vs 84, tag for tag**, `only_in_* = []` |
| `V12` disabled-hook bridge (D-6) | BLOCKING, not done | **done** | `cells_would=12 realised=0`, byte-identical; C-130 fixed |
| `V13` analyzer verdict path (D-7) | BLOCKING, not done | **done** | `observe()`/`decide()`, six verdict classes on CPU |
| `artifacts.analyzer_exists` | `false` | **`true`** | the analyzer emits a verdict |
| **`V3` power** | BLOCKING, not done, stages `["kill","family"]` | **BLOCKING, not done**, stages **`["family"]`** | *re-scoped, not closed* |
| **`V16`** *(new)* | — | BLOCKING, not done, stages `["family"]` | the one V8 clause the smoke did **not** execute |

`--for-extraction` went from **7 refusals to 2** — V3 and V16 — and that refusal is still the
correct state.

---

## 2. `V3` — the circular precondition (`PR059-D8`), and the PHASE 9 precedent

V3's own wording:

> *measure the between-domain SD of the paired knockout delta in `semantic_logodds` **on the
> concept-free channel**, on **VALIDATION DOMAINS ONLY**, and recompute MDE and power …; **if power
> < 0.8, return CANNOT ANSWER WITHOUT READING TEST.***

It gates **reading TEST**. The only run in this design that *produces* that SD is the `kill` stage
on the **VALIDATION** split — it is the only stage that puts a knockout arm and its baseline on the
concept-free channel over validation domains. DCS-PR-061 gave V3 `applies_to_stages ["kill",
"family"]`, so the item **blocked the run that would answer it**. The item could then never close,
and neither preregistered branch — PROCEED, or CANNOT ANSWER WITHOUT READING TEST — was ever
reachable.

**PHASE 9 met this exactly and resolved it the same way.** DCS-PR-057's `Q1` was the same power
item; DCS-PR-060 records it as `A1`; and the validation run that measured it — stage `q1`, split
`validation`, **slurm job 867233**, 23 validation domains, between-domain SD
`0.04200821142171075`, power `1.0`, decision **PROCEED** — *executed while the checklist was still
open*, because the power item gates READING TEST, not running VALIDATION.

### Options considered, and why the others were rejected

1. **Mark V3 done because the launcher exists.** Rejected — it is a *measurement* and nothing has
   measured it. That is "published threshold never enforced" with the sign flipped.
2. **Demote V3 to `blocking:false`.** Rejected — it would stop blocking the TEST read, the one
   thing it must never stop doing.
3. **Assume the SD from the nearest rows** (`dcssow_*`, 6 domains, a different bank). Rejected —
   `--u3-inventory` already returns rc=2 NOT CLOSABLE for exactly that reason, and one estimate is
   not a stability property.
4. **Scope V3 to the TEST-reading stage, re-derived at launch.** **Adopted.**
5. **Read TEST now and measure the SD there.** Rejected outright — that is the read V3 exists to
   prevent.

### The scope is RE-DERIVED, not read off the prose

This is the A14 pattern DCS-PR-060 established and `pr059_run_localisation.py` already implements:
an item is scoped out of a stage **only if** (1) it declares `applies_to_stages` and the stage is
not in it, **and** (2) the runner carries a predicate that re-derives its relevance, **and** (3)
that predicate, run against the stage's own arms and binding, says it is irrelevant. *A prose scope
with no code path is not a scope.*

V3's existing entry pointed at `_feeds_a_confirmatory_estimate`, which returns **True** for a
validation run — so a name-only re-scope would have been refused as a contradicted scope. **V3
needed a new predicate and got one:**

```python
CHECKLIST_STAGE_RELEVANCE["V3"] = (
    "the population this stage will actually score contains a domain the frozen split "
    "manifest assigns to TEST", _reads_the_test_split)
```

`_reads_the_test_split` loads the frozen split manifest, builds the **exact `keep_ids` exclusion
list the run will hand `score_behavior`** for each confirmatory bank *from the bank on disk*, and
asks whether **any kept prompt's domain is assigned to TEST**. It never reads the stage's name or
the flag's spelling, and it **fails closed** — any exception returns `True` and the item blocks.

### Proven in both directions

| command | result |
|---|---|
| `--stage kill --split validation --dry-run` | **rc = 0** — `V3: SCOPED OUT of stage 'kill' … RE-DERIVED at launch: NOT (the population this stage will actually score contains a domain the frozen split manifest assigns to TEST)`; 12 arms constructed, model NOT loaded, nothing written |
| `--stage family --split test --dry-run` | **rc = 3** — `CHECKLIST BLOCKS family: V3 … is BLOCKING, not done, and applies to stage 'family'` (and V16) |
| `--stage kill --split test --dry-run` | **rc = 3** — and this is the strong one: `V3 … declares applies_to_stages=['family'], but stage 'kill''s OWN arms and binding contradict that … The declared scope is wrong and the item blocks.` **A stage-name-only scope would have let this through.** |
| `scripts/dcs_ts_prereg.py --check --for-extraction` | **2 refusals**, V3 among them — the published gate ignores `applies_to_stages` entirely and is unchanged |

**V3 is not closed.** It is `blocking: true, done: false`. If the measurement returns power < 0.8,
the preregistered answer is **CANNOT ANSWER WITHOUT READING TEST**, and nothing here makes that
branch harder to reach.

---

## 3. What closed, and the numbers each closure rests on

Every number below was **re-observed on 2026-09-09 before the flag was flipped**, from
`outputs/boombness/pr059_runner/smoke_train/` and from the per-arm `PR059_ARM_GATE.json` /
`summary.json`, not from a report.

### `V8` — the smoke. Job **870382**, node `n-802`, COMPLETED 0:0

`DONE.json`: `status ok`, 6 arms selected / 6 done / **0 unbuildable**, **240 rows**,
`wall_seconds 972.230` (**16.2 min**), `model_loads 1`, `model_cache_hits 4`.

* **Backend.** `attn_implementation: "eager"` **from the LOADED config** in all four intervened
  arms and in `button_bomb_S_0_baseline`. **One correction to the brief:** the sixth arm,
  `basket_bomb_S_0_baseline`, is a **cache hit from the earlier job 870303 on `n-801`** and records
  **no backend field at all** (`attn_implementation` is `''` in its arm gate). That is correct and
  gated — the arm gate requires the backend only of a **non-baseline** arm. So *five of six* arms
  carry `'eager'`, not six.
* **Liveness.** `frac_rows_scope_live 1.0`, `frac_rows_decode_live 0.0`, `scope_violations {}`,
  producer `n_decode_edits 0`, `n_zero_dose_rows 0`, in **all four** intervened arms. Analyzer
  liveness `live=true`, `evaluable=true`, `reasons=[]`, `n_cells_realised == n_cells_expected`.
* **Realised == declared.** `realised_equals_declared ok=true` over 40 records per arm,
  `n_row_mismatches 0`, `n_token_mismatches 0`, against `[-10]` for S_C and the full 28-row span
  `-28..-1` for S_G. `end_relative_audit n_violations 0`, with **26 distinct first positions over
  26 distinct sequence lengths** — a single first position across differing lengths is the
  absolute-index signature and would have failed.
* **Internal consistency worth citing.** S_G (28 declared rows) shows **57,456 prefill edits per
  row** (2,298,240 over 40 rows); S_C (1 declared row) shows **2,052 per row** (82,080 over 40).
  `2,298,240 / 82,080 = 28.000` — the declared scope sizes, exactly. *(The brief quoted the
  per-row figures; the artifacts carry the 40-row totals. Both are recorded in the amendment.)*
* `resolver_failure_gate`: `n_failed 0 / n_total 40`, `cannot_answer false`, every arm.

**What this closure does NOT cover — and why `V16` exists.** V8 inherited U2's clause *"verify the
3 draws produce 3 DISTINCT output hashes"*. The smoke built the baseline, S_G and S_C only —
**zero control arms** — and `DONE.json` records `control_bands {}`. Closing that inside V8 would
have marked *measured* a thing nothing measured. It is **carved out into V16**, on the DCS-PR-060
precedent that split `Q7` into `A7a` / `A7b`.

### `V10` — the liveness schema (`PR059-D4`)

Closed **producer-side**, exactly as C-117 was fixed; the gate was **not** made lenient.
`ScopedAttentionKnockout._pre` counts on **opposite sides of the write** —
`n_cells_edited_expected` from the rows the forward *resolved*, before the mask is written;
`n_cells_edited_realised` **read back out of the mask that was actually written**, at the
coordinates the write targeted — so `realised == expected` is not a tautology and `realised <=
expected` always holds. Measured on CPU against the real class: **`n_edits=12 expected=12
realised=12 hook_fired_count=2 n_forward_with_destinations=2`**. `liveness_gate()` now **RAISES by
name** on a missing field; a field **present and zero** stays **DEAD HOOK → VOID**. Confirmed on
real GPU rows by job 870382: `analyzer_liveness_contract ok=true, n_fields 11, unmapped [], defect
''`, with `n_cells_realised == n_cells_expected` (2,298,240 for S_G; 82,080 for S_C, per bank) and
`n_fired 1440` over 40 rows.

### `V11` — the arm-set disagreement (`PR059-D5`). Closed although the brief did not list it

`--stage kill --split validation` scopes V11 out (`family`-only), which is why it was not among the
six refusals. But it is **measurably closed**, and leaving a resolved blocker reading `done:false`
is the stale-claim failure this project has recorded before. **Neither of the two numbers was
right:** the verifier was right about the `+6` (S_G's nondemo-**key** controls are buildable at any
`m` — their pool *excludes* `query_span_positions` — and skipping them left the **denominator of
every fraction this phase reports** with no control of any kind); the analyzer was right about the
`-2` (L-N1's bridge is a declared BLOCKING null and must be run to be reported). **Observed:
analyzer 84, verifier 84, `only_in_analyzer []`, `only_in_verifier []`, tag for tag**, recorded on
a real run in the smoke's `DONE.json` `arm_set_disagreement: agree=true, n_runner=84,
n_verifier=84, defect=''`. Consequence: the arm count is **84** — `kill` is **12** arms, `family`
is **72**, the smoke is still 6.

### `V12` — the disabled-hook bridge (`PR059-D6` + C-130)

`DisabledHookBridge` grew an `attn_pre_kwargs` family reached only by objects the two existing
branches already refused; it runs `_pre` **in full** and hands back the **original** `(args,
kwargs)`. Measured on CPU: `kind='attn_pre_kwargs' n_forward_calls=2 prefill=2 **cells_would=12
realised=0**`, `liveness_violations []`, `max|bridged − baseline| = 0`, **BYTE-IDENTICAL True —
L-N1 HOLDS**. A bridge over a dead inner hook is still refused; an unbridgeable object still raises.
**And the worse half, C-130:** `make_intervention` returned the knockout hooks from an early
`return` *above* its own bridge block, so `--pr057-disable-hooks` was **silently ignored** and the
arm installed a **fully live knockout recorded as the C5 bridge** — a live arm wearing the null's
name. Both returns now route through `_bridge_if_disabled()`, the identity when `disable_hooks` is
False. The guard survives (runner mutation `M46` RED). Re-observed: `--stage kill --split
validation --dry-run` **constructs** both bridge arms with `--pr057-disable-hooks
--pr057-liveness-out auto`.

### `V13` + `artifacts.analyzer_exists` — the verdict path (`PR059-D7`)

`analyse()` splits into `observe()` (all I/O; pairs within `prompt_id`, refuses unequal per-arm
populations by name — L-N11) and **`decide()`, which is pure** and therefore driven end to end by
`--self-test` on CPU. It reaches, in order: **POSITIVE, NEGATIVE, CANNOT_ANSWER, VOID (unclean
liveness), VOID (a triggered void clause), NO_VERDICT** — and, for a reference that moved the wrong
way, the kill condition before any narrower scope is read. The four conjuncts are scored against
**their own** expected signs (O1's parsed from two prose statements that must agree; sign = −1 from
2 statements). `void_walk()` / `cannot_answer_walk()` give all **10** and **4** frozen clauses a
status; a clause with no evidence key is a refusal. The NEGATIVE branch returns the pinned
`MANDATORY_WORDING` literal. Holm keeps `m` **pinned at 6**. Every p prints its attainable floor
`[9.9990e-05]`. `analyzer_exists` is flipped to `true` because the flag's whole content is *"can
this file emit a verdict"* — and `--for-extraction` still refuses, on V3 and V16.

---

## 4. `V16` — the carve-out, and a gap it exposes (`PR059-D9`, **reported, not fixed**)

`V16` = *"verify that the per-scope RANDOM-ROW control band's three seeded draws produce THREE
DISTINCT OUTPUT HASHES, on the arms' own outputs."* — BLOCKING, not done, `applies_to_stages
["family"]`, predicate `_runs_a_random_row_control_band`.

It does not block `kill` for a re-derived reason, not a naming one: the `kill` stage builds **2
baseline + 2 S_G scope + 6 S_G nondemo-key controls + 2 bridges** and **zero arms of kind
`random_row_control`** — the reference scope's random-row control has pool `28 − 28 = 0`, which
`decision_PR059_D1` already decided. A stage that builds none of those arms can make the clause
neither true nor false. `family` builds all **24** and blocks.

**`PR059-D9`, found while carving this out.** The runner's end-of-stage band check
(`pr059_run_localisation.py`, *"L-N7: the random-row control bands, THREE DISTINCT OUTPUT HASHES"*)
selects with `if arm.kind != "random_row_control": continue`. The **six nondemo-key control draws
the `kill` stage actually runs** are kind `nondemo_control`, so they pass through untouched and the
kill stage's `band_report` is `{}`. The frozen `dose_matching` text asks for three distinct draws of
the nondemo-key control too, **and nothing checks that they differ.** This project has **twice**
published a control band that was secretly `n=1` because the seed never reached the draw — which is
why the check exists. It is **recorded in the amendment and not fixed here**: fixing it changes what
the runner *does* on the kill stage, and this file's mandate is the checklist and the V3 scoping.
**No nondemo-key band may be reported as a band until it lands.**

---

## 5. The launcher edit — two predicates, nothing else

`src/boombness/pr059_run_localisation.py` gained exactly two functions and two
`CHECKLIST_STAGE_RELEVANCE` entries:

* `_reads_the_test_split` → `V3`
* `_runs_a_random_row_control_band` → `V16`

**No gate was loosened and no refusal removed.** `AMENDMENT_DEFAULT` still points at DCS-PR-061 —
deliberately, because an un-flagged run then gates on the *stricter* older checklist (fail-closed),
and because the self-test's assertions about the default amendment stay meaningful. **The `sbatch`
line must therefore pass `--amendment` explicitly.**

Verified unchanged after the edit: `--self-test` **58 checks, 0 failed**; `--mutate` **49/49 RED**.

---

## 6. Observed numbers — everything I ran

### PHASE 11 harnesses (expected → observed, before **and** after the edit)

| harness | expected | observed |
|---|---|---|
| `scripts/dcs_ts_pr059_localisation.py --self-test` | 114/0 | **114 checks, 0 failed** |
| `scripts/dcs_ts_pr059_localisation.py --mutate` | 94/94 RED | **94/94** |
| `src/boombness/pr059_run_localisation.py --self-test` | 58/0 | **58 checks, 0 failed** (before and after) |
| `src/boombness/pr059_run_localisation.py --mutate` | 49/49 RED | **49/49** (before and after) |
| `scripts/dcs_ts_pr059_verifier.py --self-test` | 25/0 | **25 checks, 0 FAILED** |
| `scripts/dcs_ts_pr059_verifier.py --mutate` | 22/22 RED | **22/22 RED** |

Every expected number reproduced. No item was flipped on a number that did not.

### PHASE 9 / PHASE 10 — provably unchanged

| harness | expected | observed |
|---|---|---|
| `scripts/dcs_ts_pr057_causal.py --self-test` | 117/0 | **117 checks, 0 FAILED** |
| `scripts/dcs_ts_pr057_causal.py --mutate` | 102/102 RED | **102/102** |
| `src/boombness/pr057_run_causal.py --self-test` | 70/0 | **70 check(s), 0 FAILED** |
| `src/boombness/pr057_run_causal.py --mutate` | 41/41 RED | **41/41 RED** |
| `scripts/dcs_ts_pr058_symmetry.py --self-test` | 57/0 | **57 checks, 0 failed** |
| `scripts/dcs_ts_pr058_symmetry.py --mutate` | 56/56 RED | **56/56** |

### The new amendment under the published loader

```
$ python scripts/dcs_ts_prereg.py --check configs/dcs_ts_pr064_phase11_amendment2.json
[prereg] clean: status FROZEN, 21 hashes pinned and verified, all 12 mandate-21 fields present   rc=0

$ python scripts/dcs_ts_prereg.py --check --for-extraction configs/dcs_ts_pr064_phase11_amendment2.json
  REFUSE pre-extraction checklist V3  is BLOCKING and not done: ...
  REFUSE pre-extraction checklist V16 is BLOCKING and not done: ...
[prereg] 2 refusal(s)                                                                            rc=1
```

**21 hashes** pinned and verified (DCS-PR-061 had 18; the extra three are the re-pinned
`pair_common_sha16_at_freeze` plus the analyzer/verifier/launcher/score_behavior/smoke witnesses).
**2 refusals**, down from 7.

### Both dry-runs from the scoping task

```
--stage kill   --split validation --dry-run   ->  rc = 0   (V3 and V16 SCOPED OUT, re-derived; 12 arms)
--stage family --split test       --dry-run   ->  rc = 3   (BLOCKS on V3 and V16)
--stage kill   --split test       --dry-run   ->  rc = 3   (BLOCKS on V3, via the PREDICATE)
--stage smoke  --split train      --dry-run   ->  rc = 0   (6 arms, unchanged)
```

### Artifact hashes pinned in the amendment

| file | sha16 |
|---|---|
| `configs/dcs_ts_pr059_phase11.json` (parent prereg) | `55c722ac1f5e9603` |
| `configs/dcs_ts_pr061_phase11_amendment.json` (parent amendment) | `1da927fb07200b20` |
| `scripts/dcs_ts_pr059_localisation.py` | `ba86aecc714e5e8f` |
| `scripts/dcs_ts_pr059_verifier.py` | `b1f98ccba896a229` |
| `src/boombness/pr059_run_localisation.py` (after the two-predicate edit) | `5a521e94a8d20236` |
| `src/boombness/score_behavior.py` | `d5317fd490986293` |
| `doublespeak_causality/pair_common.py` (**re-pinned**, was `33da1f4a5a4bdae5`) | `b89f9226b522f1c8` |
| `outputs/.../smoke_train/DONE.json` | pinned in `artifacts.smoke_done_json_sha16` |

### Repo tests — RAN TO COMPLETION

```
python -m pytest <26 test files importing score_behavior / pair_common / dcs_ts_prereg /
                  the PR-059 analyzer / the PR-059 verifier / the PR-059 launcher> -q

676 passed, 1 warning in 338.12s (0:05:38)      rc = 0
```

Same 676 the DCS-PR-061 ADDENDUM recorded. The single warning is a pre-existing
`scipy.stats.spearmanr` warning, unrelated to this work.

### UNSCOPED `git status --porcelain`

```
 M src/boombness/pr059_run_localisation.py
?? configs/dcs_ts_pr064_phase11_amendment2.json
?? reports/DCS_TS_PR064_AMENDMENT.md
?? data/boombness_prompts/boombness_prompt_bank_ts116{,m,n}_{basket,button}_{bomb,gun,knife}.jsonl   (18 files)
?? data/boombness_prompts/demo_pools_116dom_ts_{bomb,gun,knife}.json                                 (3 files)
?? data/boombness_prompts/ts_cand/  ts_repair/  ts_smoke/
```

The **three** entries attributable to this work are the first three. Everything under
`data/boombness_prompts/` is pre-existing untracked data this session neither created nor touched.
`reports/SPRINT_SUMMARY_2026-09-05_TO_09-06_PART2.md` was `??` at session start and a peer has
since committed it. During the pytest run `?? src/boombness/_prefix_analyze_g2_under_test.py`
appeared and then vanished — it is a transient fixture that `tests/test_g2_selection.py:574`
creates and removes.

**No `git add`, no `git commit`, no `git stash`.** Nothing was written under `outputs/`.

---

## 7. The exact `sbatch` line for `--stage kill --split validation` — **NOT SUBMITTED**

```bash
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood

# 0. ALWAYS dry-run first. It exits 0 today, loads no model and writes nothing.
python3 src/boombness/pr059_run_localisation.py \
        --amendment configs/dcs_ts_pr064_phase11_amendment2.json \
        --stage kill --split validation --dry-run

# 1. The argsfile MUST live on the SHARED filesystem -- /tmp is node-local and the job dies in 3 s.
#    NO quote characters and NO spaces inside a value: BOOMB_ARGS is word-split (job 766661).
#    --amendment IS LOAD-BEARING: AMENDMENT_DEFAULT still points at DCS-PR-061, whose V3 blocks
#    this stage. Omitting the flag gates on the stricter older checklist and the job refuses.
cat > outputs/boombness/pr059_kill_validation_args.txt <<'EOF'
--prereg configs/dcs_ts_pr059_phase11.json --amendment configs/dcs_ts_pr064_phase11_amendment2.json --stage kill --split validation
EOF

# 2. Submit. BOOMB_EXPECT and BOOMB_REQUIRE_ARGS=1 are BOTH set: without them a mistyped variable
#    name falls through to the runner's default script and exits COMPLETED 0:0 having run the
#    wrong thing (jobs 853040-853045, ~1.7 GPU-hours, and nothing caught it).
sbatch --export=ALL,BOOMB_SCRIPT=pr059_run_localisation.py,BOOMB_EXPECT=pr059_run_localisation.py,BOOMB_REQUIRE_ARGS=1,BOOMB_ARGSFILE=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/boombness/pr059_kill_validation_args.txt \
       --time=08:00:00 \
       src/boombness/slurm/run_boombness.sh
```

**No `--limit` and no `--smoke-limit`**: this is the measurement run, not a smoke, and a truncated
population would make `_feeds_a_confirmatory_estimate` false and the estimate meaningless.

It runs **12 arms** — 2 baselines, 2 `S_G` scopes, 6 `S_G` nondemo-key controls, 2 disabled-hook
bridges — over the **23 analysed validation domains**, `--expect-n 230` per arm, **one model load**.
Time budget: the smoke's 240 rows took 972 s with one arm hitting 779 s under node contention;
2,760 rows is ~11.5× that, so 8 h is a deliberately generous ceiling, not an estimate.

* `run_boombness.sh` already pins the six L40S nodes via `#SBATCH --nodelist`. **Do not add
  `--exclude`** — it nullifies that directive.
* `--mem=48G`, `--cpus-per-task=4` are the script's defaults; do not raise them.
* Budget ≤ 2 model-loading jobs per node. This is **one** job for the whole stage.
* `assert_stage_has_no_prior_verdict` refuses a stage that already carries `DONE.json` or
  `ABORTED.json` **before any arm runs** (C-124), and `assert_stage_order` reads the smoke's own
  `DONE.json` rather than a comment.

**This run may not be reported as a confirmatory result.** Its purpose is V3: the between-domain SD
of the paired knockout delta in `semantic_logodds` on the concept-free channel, on validation
domains only; the recomputed MDE at the 0.80 power bar; the power at the declared 0.50-nat effect;
and a **PROCEED / CANNOT-ANSWER** decision. A further amendment records that number, in the shape
DCS-PR-060 item `A1` uses.

---

## 8. What still blocks the TEST-reading stage

1. **`V3`** — power has never been measured on the concept-free channel. `--u3-inventory` still
   returns rc=2 NOT CLOSABLE; **0** knockout runs on that channel exist on any of the 6
   preregistered `ts116m` banks. `power.mde.in_semantic_logodds_nats` stays **`null`** — this file
   does not fill it in, guess it, or bound it. Until the validation run above prints its SD, its
   MDE and a PROCEED, **no TEST read is authorised**; and if it prints power < 0.8 the
   preregistered answer is **CANNOT ANSWER WITHOUT READING TEST**.
2. **`V16`** — the three seeded draws of the per-scope random-row control have never produced three
   output hashes, distinct or otherwise. All 24 of those arms are family-stage arms.
3. **`decision_PR059_D1`, unchanged** — `S_D` vs `S_E`, PHASE 11's **declared primary contrast**,
   still cannot be run as designed, and the codeword-row question still returns **CANNOT ANSWER for
   a stated reason** unless a controlled narrower scope reaches half of `S_G`. That is the outcome,
   not an obstacle to be removed.
4. **`PR059-D9`** (§4) — no nondemo-key control band may be reported as a band until the runner's
   distinctness check covers `nondemo_control` arms.

Non-blocking and still open, carried across unchanged: `V14` (fair-share / submission-time
operational check) and `V15` (re-run `dcs_ts116m_token_roles.py` and confirm its report sha16).

**The phrase "the representation is meaningless", and any paraphrase, remains forbidden**
(DCS-PR-059 `primary.negative`).
