# DCS-PR-058 — the PHASE 10 analyzer

**File:** `scripts/dcs_ts_pr058_symmetry.py` (2,100 lines, CPU-only, no network, no GPU).
**Governs:** `configs/dcs_ts_pr058_phase10.json`, status FROZEN, loaded **only** through
`scripts/dcs_ts_prereg.py`. The config was not edited; three conflicts found against it are
recorded in §4 rather than fixed.
**Written:** 2026-09-07. No cell-B or cell-E row has been scored by any run, so this analyzer has
never seen an outcome — which is the state `_freeze_rule` asks for.

---

## 1. What it does

Five entry points, one module, so the liveness contract and the statistics that consume it cannot
drift apart into two files that disagree.

| entry point | what it does |
|---|---|
| `--plan` | the arm manifest — 38 arms (7 controls × 3 cells × 2 confirmatory banks, K5 cell-B-only, K4 at dose 0, K7 at dose 8) with each arm's exact launch command. Reads no outcome. |
| `--self-test` | 55 CPU unit checks on synthetic data |
| `--mutate` | 52 corruptions, each of which must produce a refusal |
| `--power-t3` | checklist T3 as a **code path**: measures the between-domain SD on VALIDATION domains only and returns `CANNOT ANSWER WITHOUT READING TEST` below the power bar |
| default | the analysis: identity gate → gate-literal audit → population bind → liveness → verdict. **Refuses when no arm has run.** |

### The non-negotiables, as code paths

* **No numeric gate literal.** `alpha`, `n_perm`, the attainable p-floor, the `option_mass` gate,
  the power bar, the installation cut, the declared MDE, the seeds, the read layer, the band, the
  family membership and the negative's wording all come from `Prereg.require()` or are *parsed* out
  of the frozen file's own prose (`option_mass_gate_value`, `power_bar`, `ceiling_quantile`,
  `intervention_band`). `source_gate_literal_audit()` re-reads **this analyzer's own source** and
  fails if any declared gate value appears as a numeric literal. It fired for real during
  development — three synthetic test values happened to equal `0.5` — and the file was changed, not
  the audit. Scope limit, stated: float gates and integer gates of ≥3 digits; short integer gates
  (read layer, draw count) are covered by accessor unit tests instead.
* **`p_floor()` re-derives** `1/(n_perm+1)` and refuses if the config's `attainable_p_floor`
  disagrees with it. Every p is formatted through PR-048's `fmt_p`, i.e. always beside its floor,
  and a p at the floor is printed as `p < 9.999e-05 (FLOOR; 0 exceedances — the design cannot
  resolve below this)`.
* **Domain-level permutation only.** There is no row-level code path to disable. The only
  permutation implemented flips the whole domain's paired sign together, and
  `forbid_non_domain_unit()` refuses any unit other than `primary.independence_unit`.
* **Binding is on `cell`.** `bind_rows(..., selector_field=)` refuses anything but `cell` *before*
  the bind (A-039), and raises `ZeroBinding` if the bind returns no rows or no domains. It also
  cross-checks `condition` against the preregistered value per cell and refuses on disagreement —
  `condition` is verified, never used to select.
* **Exclusions from the boolean.** `whole_population_exclusions()` reads
  `preregistered_exclusions[].whole_population`; an exclusion that omits the boolean, or carries a
  non-boolean, is a refusal. Prose is never matched.
* **Installation stratifies, never excludes.** `stratify_by_installation()` reports pooled + both
  strata and **refuses** if any analysed domain lacks an installation statistic — because the
  alternative, dropping it, is the mandate-15 post-hoc exclusion arriving by accident.
  `refuse_installation_as_exclusion()` exists as a separate explicit guard.
* **No verdict on unclean liveness.** `liveness_gate()` runs before any outcome is computed and
  refuses on `hook_fired_count == 0`, a non-eager `attn_implementation` read back from the loaded
  config, `n_prefill_edits == 0`, `n_decode_edits != 0`, realised ≠ expected cells, and a zero
  realised dose. `verdict()` raises before it can reach any of its four branches.
* **CANNOT ANSWER and the kill conditions are branches.** `kill_condition_channel` (disengaged
  primary channel — and falling back on the display channel is forbidden), `kill_condition_whole_query`
  (K6; reports UNEVALUATED rather than passed when K6 has not run), `kill_condition_ceiling`, and
  the `t3_power` underpowered return.
* **Refusal on no data.** With no complete arm directory the analyzer raises and names the
  outstanding blocking checklist items; it never prints an empty result.
* **Banks are a transfer pair, not a pool.** `refuse_pooling_across_banks()` refuses an estimate
  over more than one codeword bank; `refuse_descriptive_as_confirmatory()` refuses quoting a
  knife/gun arm as a mechanism result.

### The ceiling risk, handled structurally

`primary._largest_risk` — the cell-B/E query names the concept, so `logp_concept` sits at a ceiling
cell C does not have. All three declared mitigations are enforced, not described:

1. `PairedDelta` takes a `BaselineDistribution` as a **required** constructor argument and refuses
   with `baseline=None`; `render_delta()` refuses until `baseline.render()` has run. A delta
   cannot reach a reader ahead of its own baseline distribution (full quantiles, min/max, scored
   range, option_mass median).
2. `ceiling_gate()` returns CANNOT ANSWER when the cell-E baseline's p90 sits at the top of the
   scored range; cell B carries the identical query text so H1−H3 differences the ceiling out.
3. `copy_vs_mechanism()` evaluates the two accounts' **opposite sign** predictions for H1 relative
   to H2 and labels the result MECHANISM-CONSISTENT / COPY-CONSISTENT / NEITHER / UNDETERMINED.

---

## 2. Observed results

All run with `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`, CPU only.

| run | observed |
|---|---|
| `--self-test` | **55 checks, 0 failed** |
| `--mutate` | **52/52 mutations produced a refusal** |
| default, no arm data | **REFUSES** (`rc=1`): "NO DCS-PR-058 arm has produced a COMPLETE run … 38 arm tags searched, 38 absent … Blocking checklist items outstanding: T1, T2, T3, T4, T6, T7, T8, T9, T10" |
| default, planted dead-hook arm | binds the real banks (1130 rows / 113 domains per bank per cell, split 67/23/23), then **REFUSES the verdict** on `hook_fired_count == 0` |
| `dcs_ts_prereg.py --check` | clean: FROZEN, 17 hashes pinned and verified, 12/12 mandate-21 fields |
| `dcs_ts_prereg.py --check --for-extraction` | **10 refusals** — unchanged (see §3) |

The six mutations the task named explicitly are each RED: dead hook (M1), zero-row bind (M25),
row-level permutation attempt (M23), threshold read from a literal (M28, plus M50 which plants a
gate literal in a synthetic analyzer source), delta printed without its baseline (M30), verdict on
unclean liveness (M33). Also RED: SDPA arm (M2), zero realised dose (M3), decode-edit leak (M4),
identical control-band hashes (M8), absolute edit index reused (M13), unequal per-arm populations
(M14), outcome computed at the concept-token read site (M35), installation used as an exclusion
(M37), three-of-four conjunctive conditions (M15), pooling the two banks (M51).

**Independent confirmation of the config's row arithmetic.** Binding `cell` ∈ {E, B, C} on
`semantic_one_word` at dose 4 against `button_bomb` and `basket_bomb`, after the three
whole-population exclusions, returns **1130 rows over 113 domains, split 67 train / 23 validation /
23 test** in every one of the six (bank, cell) combinations — exactly
`population.n_rows_per_bank_per_cell` and `split.n_domains_analysed`.

---

## 3. Blocking checklist: what is closable, what is not

**Closable by this work (subject to the §4 conflict):**

* **T7** — "write the analyzer; every threshold through `Prereg.require()`, no numeric gate literal
  anywhere in the file, the underpowered return as a CODE PATH, the conjunctive four-condition
  success rule evaluated explicitly, and a refusal to emit any verdict when hook liveness is
  unclean." All five properties are implemented and each is exercised by a named self-test check.
* **T8** — "mutation-test that analyzer: a dead hook, an SDPA arm, a zero realised dose, an
  identical-hash control band, a row-level p-value, an absolute edit index, unequal per-arm
  populations, and a delta computed from the concept-token read site must EACH produce a refusal."
  All eight are RED (M1, M2, M3, M8, M23, M13, M14, M35), inside a 52-mutation harness.
* `artifacts.analyzer_exists` — an analyzer now exists on disk. **The flag is still `false` and this
  session may not edit the frozen config**, so the loader still refuses on it.

**Not closable on CPU / not closed here:**

* **T1** (cells-B/E token-role map, and the ` bomb` subtoken count) — needs the tokenizer and a
  re-derivation; H4's read site stays UNVERIFIED and H4 can therefore return CANNOT ANSWER.
* **T2** (score cells B/E, `option_mass`, cell-E ceiling) — GPU.
* **T3** (validation-only SD, MDE, power) — the code path exists and was exercised on synthetic
  input; the *measurement* needs T2's rows.
* **T4** (`target_surface_positions` on cells B/E, empty-needle guard) — GPU/tokenizer.
* **T6** (nondemo draw protects the query span; 3 distinct hashes) — the analyzer-side gate exists
  (`control_band_gate`), but "verify at THIS call site" is a GPU run.
* **T9** (independent verifier, R1–R5) — deliberately **not** written here: a verifier that shares
  this session's assumptions is not independent, and the task scoped writes to two files.
* **T10** (smoke run) — GPU.
* T5, T11 — non-blocking.

**So the loader's refusal count stays at 10.** Nine blocking items are still `done: false` in the
frozen file and `analyzer_exists` is still `false`. T7 and T8 are *substantively* satisfied but
their booleans are the config owner's edit, not the analyzer's — flipping them here would be the
analyzer marking its own homework, which is the failure mode `_freeze_rule` and C-086 both name.

---

## 4. Conflicts and defects found against the FROZEN config

**PR058-D1 — `artifacts.analyzer` names a different file (BLOCKING for the freeze).**
The frozen config and `reports/DCS_TS_PR058_PR059_DESIGN.md` §3 both name
`scripts/dcs_ts_pr058_symmetry.py`; checklist T7 says "write `scripts/dcs_ts_pr058_symmetry.py`".
This analyzer was commissioned as `scripts/dcs_ts_pr058_symmetry.py`. The config is FROZEN and was
**not** edited. `analyzer_identity_gate()` refuses to run the analysis unless
`--ack-analyzer-path-conflict` is passed, and records the acknowledgement in the output. Resolution
is the config owner's: either rename this file to the declared path, or amend `artifacts.analyzer`
(which, being an amendment to a FROZEN preregistration, is itself a decision that must be logged).
Until then `artifacts.analyzer` points at a path that does not exist on disk, which
`analyzer_exists_flag()` reports explicitly.

**PR058-D2 — the ceiling rule has no numeric criterion.**
`primary._largest_risk` and `kill_condition` say the arm is CANNOT ANSWER "if its p90 is at the top
of the scored range", but `semantic_logodds` has no scored range pinned anywhere in the config, and
a log-odds contrast is not bounded a priori. So the rule as written cannot be evaluated by any
program. `ceiling_gate()` therefore **refuses** unless the producing arm persists a
`scored_range` — it does not invent a cut. This is the "published threshold never enforced" shape
caught before it ships: the mitigation the design calls its primary defence against the largest
interpretability risk in the phase is currently unevaluable.

**PR058-D3 — `read_site.position_NOT_USED` is named after the wrong cell's surface.**
The refused site is recorded as `"codeword_last"`. In cells B and E the target surface is the
*concept* (` bomb`), not the codeword, and the config's own prose says so ("Reading at rel_end −10
in cell B/E is reading AT the ` bomb` token"). A producer that captured the cell-E concept-token
read under any other position label — `target_surface_last`, `concept_last` — would slip past a
refusal keyed on the name alone. `read_site_gate()` closes this by refusing the named position
*and* every position that is not the single preregistered downstream site, but the config's naming
is a matcher/scope hazard of the recorded class.

**Observation (not a defect).** `power.mde_formula` is the z-based
`2.80158/sqrt(n)`. The exact one-sample-t MDE this analyzer computes is ~1% larger at n = 113
(0.2658 SD units against the config's 0.26355). Both are reported; the difference is the t/z
correction, not a disagreement about the design.

---

## 5. Reproduce

```
P=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
$P scripts/dcs_ts_pr058_symmetry.py --self-test          # 55 checks, 0 failed
$P scripts/dcs_ts_pr058_symmetry.py --mutate             # 52/52 RED
$P scripts/dcs_ts_pr058_symmetry.py --plan               # 38 arms
$P scripts/dcs_ts_pr058_symmetry.py                      # REFUSES: no arm has run
$P scripts/dcs_ts_prereg.py --check --for-extraction configs/dcs_ts_pr058_phase10.json   # 10 refusals
```

---

## 6. CPU checklist closure, 2026-09-08 — T1, T4, T6, T7, T8, T9

Everything in this section was run on the login node with
`/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`. **No GPU, no SLURM
submission, no network.** GPU job 869869 (cells B and E, `semantic_one_word`, doses 0 and 4, no
intervention) is item **T2** and is *not* touched here; T2, T3 and T10 remain open.

### 6.1 T1 — the cells-B/E token-role map

`scripts/dcs_ts116m_token_roles.py` grew a `--cell {C,B,E}` argument. The **default path is
unchanged**: cell C still binds `configs/dcs_ts_pr048.json`, still excludes `restaurant_kitchen`
only, still writes `outputs/dcs_ts/token_roles_ts116m.json.gz`, and a 4-domain regression run
reproduced the committed artifact on **240/240 records byte-identically** apart from four newly
added record fields (`cell`, `condition`, `target_surface`, `target_surface_is_concept`). Cells B
and E bind `configs/dcs_ts_pr058_phase10.json`, its **three** whole-population exclusions and its
113 domains, and write their own artifacts and reports.

| | cell B | cell E |
|---|---|---|
| records | **6,780** (113 × 2 × 3 × 10) | **6,780** |
| artifact | `outputs/dcs_ts/token_roles_ts116m_cellB.json.gz` `ceb5d1be171cd23e` | `..._cellE.json.gz` `3310cf9171de9bf2` |
| | *(gzip embeds a build timestamp: a re-run changes the file hash, not the records)* | |
| report | `reports/DCS_TS116M_TOKEN_ROLE_MAP_CELLB.md` | `..._CELLE.md` |
| distinct query-side role censuses | **1** in 6,780/6,780 | **1** in 6,780/6,780 |
| query-side tokens per prompt | **28** (23 content + 5 scaffold) | **28** |
| `concept_word` | **1** | **1** |
| `codeword` | **0** | **0** |
| `neutral_content` | **0** | **0** |

**The census, both cells:** `answer_format_instruction` 8, `user_instruction_scaffold` 11,
`punctuation` 3, **`concept_word` 1**, `chat_scaffold` 1, `response_header` 4.

**`concept_word` IS NON-EMPTY on cells B and E — the cell-C figure was a property of the cell, not
of the bank.** Cell C reports `concept_word` = 0 tokens in 6,900/6,900 prompts; cells B and E
report **1 token in 6,780/6,780**, and the mirror is exact — `codeword` is **0** here where
`concept_word` was 0 there. The role precedence had to be made cell-aware to see it: `target_surface`
holds the concept in B/E, so under the original codeword-first precedence every one of those tokens
would have been labelled `codeword` and the map would have reported `concept_word: 0` on the very
cells whose query names the concept. The flip is conditioned on `target_surface == concept`, which
is why cell C is bit-identical.

**Dose parity holds, so the fallback comparison is not triggered.** The final `target_surface`
occurrence inside the query is **one subtoken at `rel_end −10` in 6,780/6,780 prompts on both
cells** — ` bomb` = 13054, ` knife` = 22145, ` gun` = 6166, each a single Llama-3.1 token, exactly
as ` button` = 3215 is. Cell E is therefore a **1-row cut compared against cell C's 1-row cut**, and
`intervention.dose._dose_must_be_equal_across_the_three_cells_or_the_symmetry_is_not_a_symmetry`
does not fire.

**The `following` read site survives into cells B and E.** `rel_end −9`, `' actually'`, id **3604**,
all four downstream-neutral criteria in **6,780/6,780** (strictly after every target occurrence
6,780/6,780; token-identical across the three concepts at matched `prompt_id` **2,260/2,260**; no
`bomb`/`knife`/`gun` substring; present in every prompt), ranked **1 of 9** qualifying offsets. So
`read_site._following_in_cells_B_and_E_IS_NOT_YET_VERIFIED` is now **verified**, and **H4 is not
CANNOT ANSWER on read-site grounds**.

**Two cell-C premises are violated by construction on B/E, and are reported rather than
suppressed.** Named in source (`CELL_BE_EXPECTED_VIOLATIONS`) *before* the run, still executed,
still counted, excluded from the exit status only:
`C_query_tail_token_ids_identical_across_concepts` **4,520/4,520** and
`D_no_bomb_knife_gun_token_anywhere_inflection_aware` **6,780/6,780**. The query names the concept
here; that is `leakage.cell_BE_caveat`, not a defect.

**PR058-D4 (new, cell B only) — six multi-subtoken concept occurrences, all upstream of the query.**
`H_codeword_is_one_subtoken` fails on **6 of 33,900** target-surface occurrences in cell B: four
`BOMB` (uppercase, `theatre_backstage`) and two `-knife` (hyphenated, `radiology_suite`). **All six
sit inside the demonstration block; none is in the query span**, so the destination-row dose is
untouched. Cell E is **0/33,900**. This is the same shape as the cell-C map's item 4 (`BASKET` is
three subtokens where ` basket` is one) and it is recorded, not repaired.

**PR058-D5 (new) — checks `A` and `A2` were reading the wrong bank field on B/E, and were repaired
rather than excused.** Both compared the re-derived `target_surface` occurrence count against
`n_codeword_occurrences`. On a cell-B row that compares a count of ` bomb` (5) against a count of
` button` (0) — a **180/180, then 6,780/6,780 "failure" that is a wrong key, not a defect**: the
recorded matcher/scope bug class. They now select `n_concept_occurrences` when `target_surface` *is*
the concept, and pass **6,780/6,780** on both cells; the mutation that proves `A` can fail was
retargeted to the field the check selects, or it would have come back GREEN. **26/26 mutations RED**
on cell B.

**PR058-D6 (new, cell C, not repaired here) — the committed cell-C map and PR-048 disagree about the
exclusion set.** The map hardcodes `{restaurant_kitchen}` and 115 domains; `configs/dcs_ts_pr048.json`
now names **three** whole-population exclusions (`subway_station` C-087 and `school_campus`
C-075/R-108 were added after the map was built), which implies 113. The new `--cell` path reads the
exclusion set back from the bound preregistration: excluding a domain the preregistration does *not*
name is **fatal**; the reverse is a printed `[WARN]` and a recorded `exclusion_readback` block,
because repairing it would rewrite a committed artifact whose sha16 PR-058 pins as a witness. Cells
B and E agree with PR-058 exactly.

### 6.2 T4 — `target_surface_positions` on cells B and E

Exercised at the real call site (`demo_key_positions` → `query_span_positions` →
`target_surface_positions`, on the same templated string `ds_common.apply_template` produces) over
the **full primary population: 6,780 cell-B + 6,780 cell-E = 13,560 rows**, six banks,
`semantic_one_word`, `n_examples` 4, after the three exclusions.

| quantity | cell B | cell E |
|---|---|---|
| agreement with an **independent** re-derivation of "final concept occurrence inside the query span" | **6,780 / 6,780** | **6,780 / 6,780** |
| realised dose | 1 token, 6,780/6,780 | 1 token, 6,780/6,780 |
| end-relative index | **−10**, 6,780/6,780 | **−10**, 6,780/6,780 |
| decoded | ` bomb` 2260, ` knife` 2260, ` gun` 2260 | same |
| the `following` token | `−9 ' actually'`, 6,780/6,780 | 6,780/6,780 |
| resolved outside the query span / fell back to a demo occurrence / refusal reasons | 0 / 0 / 0 | 0 / 0 / 0 |

The comparison rule was **written for this check, not imported from the resolver** — a verifier that
re-runs the producer's own code and compares it with itself asserts `None == None`.

**Empty-needle guard:** on a *planted* empty `target_surface` (never present on these rows on disk)
the resolver returned `([], "empty_target_surface")` in **100/100** trials, 50 per cell — before any
search, so it never matches at every token.

### 6.3 T6 — the dose-matched nondemo draw, at this call site

Read-only, over the same 13,560 rows, calling
`knockout_key_set("nondemo_matched_d{1,2,3}", demo_keys, seq_len, control_seed=20260908,
protected=query_span_positions(...))` exactly as the production call sites do. The protection is
plumbed at **four** call sites — `src/boombness/score_behavior.py:2636`/`:2718` (main loop),
`:2283` (pre-flight) and `scripts/dcs_extract_under_ko.py:368`/`:499` — and `knockout_key_set`
forwards `protected` into `nondemo_control_draw`, whose pool is `range(1, seq_len-1)` minus the demo
keys **minus the protected set**.

| observed | value |
|---|---|
| rows where **no** drawn key intersects `query_span_positions` | **13,560 / 13,560** |
| rows where the three draws are **distinct key sets** | **13,560 / 13,560** (0 collisions) |
| draws with `match_ratio` < 1.000 | **0** |
| `InfeasibleControl` refusals | **0** |
| smallest protected pool seen | **117** keys |

**Residual, stated rather than glossed.** The frozen item also asks for **3 distinct *output*
hashes**. That requires generation and therefore GPU time; it is not CPU-observable and is **not**
claimed. Distinct key sets are the necessary precondition — identical draws would guarantee
identical outputs — and the sufficient check stays a run-time VOID gate, enforced by
`dcs_ts_pr058_symmetry.control_band_gate` and independently by the new verifier's **R3**, whose
mutation `X3` is RED.

### 6.4 T7 / T8 — the analyzer, re-run rather than inherited

`--self-test` **55 checks, 0 failed**; `--mutate` **52/52 mutations produced a refusal**, including
each of the eight T8 names it in terms (dead hook, SDPA arm, zero realised dose, identical-hash
control band, row-level p-value, absolute edit index, unequal per-arm populations, a delta from the
concept-token read site). `source_gate_literal_audit` reads the analyzer's own source and confirms
no declared gate value appears as a numeric literal, so the no-literal property is **checked**.
`analyzer_identity_gate` now reports `match=True`: **PR058-D1 is resolved by the rename**.

### 6.5 T9 — `scripts/dcs_ts_pr058_verifier.py`, the independent verifier

Imports **nothing** from the analyzer — not the run-finder, the split loader, the bank loader, the
`Prereg` loader or the arm-tag rule — and re-derives all of them from the frozen file read as plain
JSON plus the arm directories on disk. `assert_independent_of_analyzer()` enforces that against the
file's own source text and is the **first** line of `--self-test`, so the independence is checked,
not claimed.

| class | what it closes |
|---|---|
| **R1** | silent denominator — usable readouts, never JSON lines, and uniform per domain |
| **R2** | row-level arm identity — cell, channel, dose and scope on **every row**, so an arm swap fails |
| **R3** | anchor-by-copy, and the control band that is secretly n = 1 |
| **R4** | population swap/drift — rows **joined** to the pinned bank by `prompt_id` *and* `prompt_sha16` and to the frozen split manifest, plus a re-hash of each pinned bank file |
| **R5** | vacuous-by-omission / producer-picks-arms — the expected arm set and summary keys are declared **in the verifier**, from the preregistration |
| **R6** | VOID before outcome — eager read back from the loaded config, `hook_fired_count`, `n_decode_edits == 0`, realised == expected, non-zero realised dose, `index == len(input_ids)+rel_end`, no absolute index reused across differing sequence lengths, no outcome at the refused `position_NOT_USED` site |
| **R7** | the domain independence unit (row-level FPR 0.2000) |
| **R8** | equal populations across the arms of one cell (P-N8) |

A check that binds **zero** rows returns `EMPTY`, never `PASS`.

Observed: `--self-test` **PASS** (9 assertions, including that a clean synthetic arm tree passes
every check, that an **empty run root FAILS R5** rather than passing vacuously, and that a
zero-bound check is `EMPTY`); `--mutate` **16/16 mutations caught by the named check**. Run against
the real run root today it correctly refuses on **R5** — no PR-058 arm has ever produced a complete
run.

**A recorded scope divergence, not reconciled away.** The verifier's independent arm-set derivation
reproduces the analyzer's **38** arms exactly under `--banks button_bomb,basket_bomb`. Its *default*
is **114**, because `installation.THE_ASYMMETRY…what_is_still_run` says the knife and gun arms **are
run and are reported** as registered descriptive arms, and an arm that is run is an arm a verifier
must be able to see. Two independent derivations disagreeing about scope is what two independent
derivations are for; it is recorded in `declared_arm_tags()`.

### 6.6 Checklist state after this session

`done: true` with `closed_evidence` and `closed_on`: **T1, T4, T6, T7, T8, T9**.
`artifacts.analyzer_exists` flipped to **true** (`analyzer_commit` `9ee2170c`, working tree clean,
self-test and mutate re-run before the flip; no cell-B or cell-E row has been scored by any run, so
`analyzer_committed_before_outcome` is true in the only sense available).

Still open, and each is GPU or downstream of GPU: **T2** (the readout on cells B/E — the phase's
kill condition, job 869869), **T3** (the between-domain SD on validation only), **T10** (the smoke
run under a live hook), plus the non-blocking **T5** (the PR-053 train-only direction file) and
**T11** (fair-share coordination).

### 6.7 Reproduce

```
P=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
$P scripts/dcs_ts116m_token_roles.py --cell B          # 19/22 PASS, 2 expected-on-B, 6780 records
$P scripts/dcs_ts116m_token_roles.py --cell E          # 20/22 PASS, 2 expected-on-E, 6780 records
$P scripts/dcs_ts116m_token_roles.py --cell B --mutate --limit-domains 3   # 26/26 RED
$P scripts/dcs_ts_pr058_verifier.py --self-test        # PASS
$P scripts/dcs_ts_pr058_verifier.py --mutate           # 16/16 caught
$P scripts/dcs_ts_pr058_verifier.py                    # REFUSES on R5: no arm has run
$P scripts/dcs_ts_pr058_symmetry.py --self-test        # 55 checks, 0 failed
$P scripts/dcs_ts_pr058_symmetry.py --mutate           # 52/52 refusals
$P scripts/dcs_ts_prereg.py --check configs/dcs_ts_pr058_phase10.json                  # clean
$P scripts/dcs_ts_prereg.py --check --for-extraction configs/dcs_ts_pr058_phase10.json # 3 refusals
```
