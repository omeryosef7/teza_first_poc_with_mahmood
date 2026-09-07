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
