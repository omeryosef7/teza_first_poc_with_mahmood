# DCS-PR-057 — checklist item Q4b: the GPU runner `src/boombness/pr057_run_causal.py`

**Date:** 2026-09-07 · **Nothing was run on a GPU. No SLURM job was submitted. No commit was made.
Nothing outside `src/boombness/pr057_run_causal.py` and this report was written.**
`configs/dcs_ts_pr057_phase9.json` is FROZEN and was **not** edited; the conflicts found in it are
recorded below.

Read before writing a line: `reports/DCS_TS_PR057_DESIGN.md` (§7, §8),
`reports/DCS_TS_PHASE9_BLOCKERS_CLEARED.md`, `scripts/dcs_ts_pr057_causal.py`,
`src/boombness/score_behavior.py`, `src/boombness/slurm/run_boombness.sh`,
`scripts/dcs_ts_readout_multi.py`, `scripts/dcs_ts_extract_multi.py`, the frozen config.

---

## 1. What was built

One file, `src/boombness/pr057_run_causal.py`. It **loads the model once and loops the arm
manifest** — the reason Q4b exists at all — and it **imports** the manifest, the hooks, the donor
contract, the liveness gates and the end-relative audit from `scripts/dcs_ts_pr057_causal.py`. It
re-derives none of them.

| requirement | how it is met |
|---|---|
| load once, loop the arms | `ModelCache` memoises `ds_common.load_model`; `score_behavior.main()` is invoked in-process per arm with `sys.argv` set, so the readout, the flags and their meanings are the house code, not a copy. `DONE.json.model_loads` is the number that proves it (1 for a stage). |
| `--prereg --stage {q1,smoke,h1,h2} --split {validation,test} --fit-dir --emit-liveness --emit-probe` | all present; `--dry-run` and `--plan` construct and validate **every** arm with no GPU, no model load, and **no writes at all** (the exclusion files are computed and hashed, not written). |
| `--fit-dir` is a DIRECTORY | `direction_gate()` resolves `directions_fit_dev.pt` (then `_heldout`) the way the loader does, recomputes the payload `sha256`, and runs the analyzer's `direction_provenance_gate` (TRAIN-only). The frozen config's unloadable `directions.artifact.path` is recorded as **C-113** and not "fixed". |
| fail-closed on every arm | non-zero exit, `SystemExit` from any house guard, missing `DONE.json`, zero rows, row count ≠ the bound population, a dead hook, a zero-magnitude edit, a bridge record in a live arm, an index that is not `len(input_ids)+rel_end`, a missing `PR057_ARM.json` — each STOPS the run and writes `ABORTED.json`. |
| the frozen persist contract, field by field | `persist_contract_report()` walks `persist_per_row_and_per_arm.fields` **out of the frozen file** and looks each field up where it is supposed to live (row record, or the runner's per-arm gate). A field the runner has no location for is a refusal; a field that is *present but NULL* on a live arm is a refusal (`hook_stats_dict` pre-populates every key with `None`, so presence alone would be a check that reads the producer's own null field). The two fields the producer does not emit are supplied by the runner and labelled: the **per-draw output sha256** (over the outcome fields of `results.jsonl`, since `--no-generate` leaves no `gens.jsonl`) and the recomputed **`direction_file_sha256`**; `cos(edit, v_used)` is recorded as ±1 **by construction** for `project_out`. |
| control C1's band | at the end of a stage the runner feeds the five draws' output hashes to the analyzer's `control_band_gate`; identical hashes **VOID the band** and stop the stage, before anyone computes an equivalence interval from a band that is secretly n=1. |
| per-row / per-arm persistence, incl. the ACTUAL hook-fired count | every arm is launched with `--pr057-liveness-out auto`; `--emit-liveness` is **required** for any hooked arm. Each finished arm is gated **twice** — the producer's `pair_common.project_out_liveness_violations` and the analyzer's `liveness_gate` — and both verdicts, the total `hook_fired_count`, the realised cell count and the end-relative audit are written to `PR057_ARM_GATE.json` in the arm's run directory. |
| launch order + second kill condition as CODE | `assert_stage_order()` reads the earlier stages' own `DONE.json`; `q0_gate()` checks all six PHASE 7 banks; `h1_kill_state()` / `apply_kill_condition()` / `assert_kill_condition_honoured()` implement "if H1 does not move O2 at a site, the H2 arms at that site are NOT submitted and are **uninformative, not negative**". |
| resumable manifest, no partial mistaken for complete | `PR057_RUN_MANIFEST.json` per `<stage>_<split>`, re-verified against the artifact on every load (an arm recorded `done` whose directory has no `DONE.json` is reset to pending). Terminal file is `DONE.json` **or** `ABORTED.json`, never both. |

**`--split` is load-bearing, not decorative.** `score_behavior` has no split flag and the bank's own
`split` field is `dev/heldout`, which is *not* the preregistered domain split. The runner binds the
split as a declared, outcome-independent `--exclude-prompt-ids` list built from the frozen manifest
(plus the three whole-population exclusions) and asserts the size with `--expect-n`. A validation
stage therefore never computes a TEST row. It also verifies **A-039** per bank: selecting on
`condition` must bind exactly the rows selecting on `cell` would have (it does, on `button_bomb`
and `basket_bomb`; the check refuses on a bank where it would not).

---

## 2. Verification — the numbers observed

```
python3 src/boombness/pr057_run_causal.py --self-test      ->  49 checks, 0 FAILED
python3 src/boombness/pr057_run_causal.py --mutate         ->  26/26 RED
python3 src/boombness/pr057_run_causal.py --plan --split test
                                                           ->  54 arms, 24 live / 30 control,
                                                               26 constructible today
```

**The 54-arm manifest reproduces exactly.** 24 live (16 H1 × 4 directed pairs × 2 scopes × 2
codewords, 4 H2a, 4 H2b) and 30 control (20 C1 draws, 2 each of C2/C3/C4/C5/C7); C6 is the PHASE 7
baseline and needs no job. **My count does not differ from the design's.** The stages `h1` (18 =
16 H1 + 2 C7) and `h2` (36) **partition** the manifest, and that partition is asserted in the
self-test rather than assumed.

**26 of the 54 are constructible today; 28 are not, each with a named reason** (§3).

The five mutations the task names, each RED, plus twenty-one more:

| # | mutation | refusal |
|---|---|---|
| M1 | dead hook (`hook_fired_count == 0`) | `liveness_gate`: THE HOOK NEVER FIRED |
| M2 | zero-magnitude edit | `projection_removed_l2 <= 1e-06: a ZERO-MAGNITUDE EDIT scores as a clean null` |
| M3 | direction file sha ≠ the pin | `direction_gate`: the axis is not the axis the pin names |
| M4a | ABSOLUTE (not end-relative) edit index | `audit_end_relative`: 1 violation |
| M4b | a non-negative `rel_end` parsed out of the config | `read_site_rel_end` refuses by name |
| M5 | submitting an H2 arm at a killed site | `assert_kill_condition_honoured` |
| M6 | disabled bridge presented as a live arm | refused |
| M7 | liveness record missing a producer key | refused |
| M8 | an arm launched with no liveness instrumentation | refused (C-13) |
| M9 | an UNMAPPED manifest direction label | refused, never resolved by resemblance |
| M10 | an arm whose mode has no code path launched anyway | refused |
| M11 | runner argv naming a different bank from the analyzer's | anti-drift refusal |
| M12 | an argv value containing a space | refused (`BOOMB_ARGS` is word-split) |
| M13 | a run directory with no `DONE.json` read as complete | refused |
| M14 | a split that binds zero rows | `ZeroBinding` |
| M15 | a domain absent from the frozen split manifest | refused |
| M16 | a run whose row count ≠ the bound population | refused (end-to-end through `verify_arm_artifacts`) |
| M17 | a COMPLETE-looking run whose hooks never fired | refused end-to-end |
| M18 | an EMPTY liveness file read as "no violations" | refused |
| M19 | a run with no `PR057_ARM.json` | refused |
| M20 | an arm with no `realized_dose` (so no `frac_cellmean_spread_removed`) | refused |
| M21 | a confirmatory stage with no completed Q1 | order refusal |
| M22 | an arm-vs-baseline delta that pairs nothing | refused |
| M23 | a required persisted quantity present but **NULL** | refused |
| M24 | a 5-draw control band whose outputs are identical (secretly n=1) | `control_band_gate` VOIDs the band |
| M25 | `--emit-probe` with no attributable probe | refused |

M16–M20 build a real `score_behavior`-shaped run directory and go through `verify_arm_artifacts`,
so they are not assertions about re-typed arithmetic.

**Repo tests — what completed, and what did not.** A 7-file subset covering exactly the machinery
this runner drives — `tests/test_donor_patch.py`, `test_option_mass_gate.py`,
`test_prompt_id_exclusions.py`, `test_readout_liveness.py`, `test_cell_residual_dose.py`,
`test_intervention_liveness.py`, `test_knockout_liveness_gate.py` — ran to completion:
**113 passed, 0 failed, in 222.99 s.** That covers the donor patch, the `--exclude-prompt-ids`
population mechanism the runner uses for `--split`, the readout/intervention liveness contracts and
the realised-dose arithmetic.

The wider run — 26 test files touching everything this runner imports, plus
`tests/test_prompt_families_strict.py` — got through **115 tests with 0 failures** and was then
running at ~1.5 % CPU behind two *other* sessions' `pytest` suites and a 5.5-hour joblib job on the
same node. It was cancelled rather than left competing for the node. **It was NOT run to
completion, and the four known `test_prompt_families_strict.py` failures were therefore not
re-observed in this session.**

What can be said without the suite: **no existing file was modified.** The only new file is
`src/boombness/pr057_run_causal.py`, nothing in the tree imports it, and the four known
`tests/test_prompt_families_strict.py` failures are a working-tree demo-pool data state the
previous session reproduced at clean HEAD. There is therefore no path by which this work could add
a failure, but that is an argument, not a measurement, and the suite should be re-run on a quiet
node before the first submission.

**The argv was validated end to end on CPU, against the real `score_behavior`.** The primary arm's
argv was handed to `score_behavior.main()` with a deliberately wrong `--expect-n`: it parsed every
flag, applied the runner's exclusion file (`EXCLUDED 930 declared prompt_ids ... 1160 -> 230 rows`,
`by_domain` = exactly the 23 TEST domains at 10 rows each, `by_condition` = `natural_doublespeak`
only) and then refused with `population is 230 rows, --expect-n says 999999` — i.e. the whole flag
set is valid and the population binds to the preregistered 230 **before** the model is loaded.

**Dry runs observed** (CPU, nothing written, model never loaded):

- `--stage q1 --split validation --dry-run` → 2 arms constructed and validated, 230 rows each.
- `--stage h2 --split test --dry-run` → 36 selected, 26 constructible, 10 unbuildable, exit 3 with
  `BLOCKING pre-extraction checklist` — the frozen preregistration still refuses `--for-extraction`,
  which is the design working.
- `--stage h2` with no completed Q1 → refuses on the launch order.
- `--stage smoke` without `--emit-liveness` → refuses on C-13.

**Q0 is now satisfied**, which the design report could not yet say: all six PHASE 7 banks have a
COMPLETE run and `option_mass` shows `semantic_one_word` engaged on every one (`q0_gate` in
`--plan`: `ok True`, no missing tags, none disengaged).

---

## 3. What is still blocking — and what is new

**Unbuildable today: 28 of 54 arms.** Not substituted, not silently dropped; each is refused by
name and reported by `--plan` / `--dry-run`.

| arms | why |
|---|---|
| 16 H1 + 2 C7 | mode `patch` has no code path (Q3 / Q12(a)); and under **C-112/R-116** the donor concept installs in 0/113 domains, so the H1 population is EMPTY and the arm must not be submitted at all |
| 4 H2b | mode `component_replace` has no code path (Q12(b)) |
| 2 C2 | the shuffled-label direction does not exist in the PR-053 payload (which carries `v_bomb`, `v_bomb_specific`, `v_gun`, `v_knife`, `v_knife_specific`, `v_remap`) |
| 2 C4 | **new:** mode `add` is *not instrumented* — `pc.AllPositionAdd` is constructed with no `stats=`, so a C4 arm with `--pr057-liveness-out` produces zero liveness records and is refused, and without it a dead additive hook scores as a clean null. C4 also has no single-site form (`edit_positions` is `project_out`-only), so C4 × S1 would be an all-position edit under a single-site label |
| 2 C5 | **C-119 (new)**, below |

### New defects found while building this (all recorded, none worked around)

- **C-113 (recorded, not fixed).** The frozen config's `directions.artifact.path`
  (`outputs/dcs_ts_pr053_diffmeans/<run>/directions.pt`) can never load: the *loader* decides the
  filename. The runner uses the directory `outputs/dcs_ts/directions_pr053`. The config is FROZEN
  and was not edited.
- **C-117 — the liveness producer and consumer do not share a schema. BLOCKING FOR ANALYSIS.**
  `pair_common.hook_stats_dict()` writes `n_destination_rows` / `n_cells_edited_realised` and **no
  `n_cells_edited_expected`**; the analyzer's `liveness_gate()` reads a missing/zero expected count
  as "the arm declared no destinations" and **VOIDs the arm** — so *every* arm `score_behavior`
  produces would be VOID at analysis time. The producer also writes `resolved_absolute_index` as a
  **list** and leaves `rel_end` **None** for an all-position (S2) edit, while `audit_end_relative()`
  does `int(...)` on both and would raise. The runner does **not** rewrite
  `PR057_LIVENESS.jsonl`: it gates with the producer's own function, feeds the consumer an
  **annotated copy** (`expected := n_destination_rows`, single-site index unpacked, all-position
  records marked *not applicable* rather than given an invented `rel_end`), and writes both
  verdicts and this note into `PR057_ARM_GATE.json`. **Someone must reconcile the two schemas
  before the analyzer is run**; until then the analyzer's own verdict on a real arm is VOID for a
  schema reason rather than a scientific one.
- **C-118 — O1 cannot be attributed to a row, so `--emit-probe` is REFUSED.** `ProbeReadCapture`
  is a read hook on a layer and `score_behavior` exposes **no per-row callback**; one row produces
  many forwards (the variant batches), so order-based attribution would be exactly the silent
  misalignment this phase refuses. O1 is a domain-level statistic and records that cannot name
  their domain cannot form it. Second, independent blocker: the frozen probe (Q10) is a code path
  in `scripts/dcs_ts_pr048_analysis.py` but the artifact on disk,
  `outputs/dcs_ts/pr048_result.json`, carries **no `FROZEN_PROBE` block** — the analysis has not
  been re-run since the export was added. `--emit-probe` names both and refuses.
- **C-119 — control C5's preregistered dose makes it unrunnable.** The manifest gives the
  disabled-hook bridge `alpha = 0.0` ("none — the hook is registered and edits nothing"). But the
  bridge is the *live arm's* hook run in full with its write discarded, and
  `project_out_liveness_violations` **refuses a bridge whose inner hook would not have edited
  anything** (`would_have_changed_max_abs == 0`). An α=0 bridge is refused at the node — and if it
  were not, it would certify nothing. The runner refuses the arm and records this rather than
  silently substituting α=1: the dose of a control is a preregistered quantity.

### Carried over, unchanged

**Q1** (the validation power run) has never been run — it is the next thing this runner is for.
**Q4b** is closed by this file. **Q7** (smoke) selects 2 arms, of which 1 is constructible today
(the C5 half is blocked by C-119, and the design's self-patch half by Q3). The frozen
`pre_extraction_checklist` still refuses `--for-extraction` on Q1–Q7 and on
`artifacts.analyzer_exists = false`; the runner's confirmatory stages refuse with it, which is why
the `h2` dry run exits 3.

---

## 4. The exact sbatch command — NOT SUBMITTED

The first job this runner should ever run is the **Q1 power stage on VALIDATION**, and it must
print `PROCEED` before any `--split test` job exists. The runner refuses `--split test` for `q1` and
refuses `h1`/`h2` until Q1 and the smoke have their own `DONE.json`.

```bash
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood

# 1. the argsfile MUST live on the SHARED filesystem -- /tmp is node-local and the job dies in 3s.
#    NO quote characters and NO spaces inside a value: BOOMB_ARGS is word-split (job 766661).
cat > outputs/boombness/pr057_q1_args.txt <<'EOF'
--prereg configs/dcs_ts_pr057_phase9.json --stage q1 --split validation --fit-dir outputs/dcs_ts/directions_pr053 --emit-liveness
EOF

# 2. submit. BOOMB_EXPECT and BOOMB_REQUIRE_ARGS=1 are BOTH set: without them a mistyped variable
#    name falls through to the runner's default script and exits COMPLETED 0:0 having run the
#    wrong thing (jobs 853040-853045, ~1.7 GPU-hours, and nothing caught it).
sbatch --export=ALL,BOOMB_SCRIPT=pr057_run_causal.py,BOOMB_EXPECT=pr057_run_causal.py,BOOMB_REQUIRE_ARGS=1,BOOMB_ARGSFILE=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/boombness/pr057_q1_args.txt \
       --time=06:00:00 \
       src/boombness/slurm/run_boombness.sh
```

The confirmatory stage is the same line with an argsfile reading
`--prereg configs/dcs_ts_pr057_phase9.json --stage h2 --split test --fit-dir outputs/dcs_ts/directions_pr053 --emit-liveness`
(and `--stage smoke --split train` for Q7). Notes that are part of the command, not commentary:

- `run_boombness.sh` already pins the six L40S nodes `n-801..n-805,t-806` via `#SBATCH --nodelist`.
  **Do not add `--exclude`** — it nullifies that directive.
- `--mem=48G`, `--cpus-per-task=4` are the script's defaults; do not raise them.
- Budget ≤ 2 concurrent model-loading jobs per node. This runner is *one* job for the whole stage,
  which is the point.
- `--dry-run` first, always: it constructs and validates every arm on CPU, writes nothing, and
  exits non-zero listing every blocking gate rather than the first one.

---

## Defect-ID renumbering (bookkeeping, 2026-09-07)

This report originally labelled its three new defects `C-114`, `C-115` and `C-116`. Those IDs were **already taken** in the progress log by unrelated defects recorded the same day (`C-114` the stale four-bank prompt-validation table; `C-115` a background waiter that committed 7 files under a 3-file message; `C-116` a transposed sweep triple in the claim table). They have been renumbered here to **C-117**, **C-118** and **C-119** respectively.

`C-113` is unchanged and is genuinely this phase's — the frozen config's unloadable `directions.artifact.path`.

`src/boombness/pr057_run_causal.py` carried the old numbers in its docstring, its `DEFECT_*`
constants and two check labels; it has been updated to `C-117` / `C-118` / `C-119` so the code and
this report cannot cite different IDs for the same defect. `--self-test` was re-run after the
rename.

Recorded rather than silently corrected because a defect ID is a citation target: anything written against the old numbers between this report's creation and this note is ambiguous, and the ambiguity is worth naming.
