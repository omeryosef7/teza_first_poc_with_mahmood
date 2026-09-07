# DCS-PR-057 — PHASE 9 DESIGN: the causal concept-axis intervention (CLAIM C)

**Status:** analyzer built and unit-tested on CPU. **Nothing has been run.** No GPU job has been
submitted and none may be until the blocking checklist at the end of this document closes.

- Governing preregistration: `configs/dcs_ts_pr057_phase9.json` (status `FROZEN`, frozen 2026-09-07)
- Governing mandate: `external_md/DCS_THESIS_SCALE_MANDATE_20260906.md`, section 10 (lines 789–927)
- Analyzer: `scripts/dcs_ts_pr057_causal.py`
- Report the analyzer will write: `reports/DCS_TS_PR057_CAUSAL.md` (mandate section 34, output #7)

---

## 0. Config vs mandate: they agree

Both were read in full, side by side, before a line of code was written.

| mandate 10.x | config | agree? |
|---|---|---|
| 10.1 upper-bound patch, matched (domain, family, codeword, n_examples), `C_knife → C_bomb`, "also run bomb ← gun", reverse pairs if preregistered, no post-hoc picking | `hypotheses[H1]`: same four match keys, same source/target, `also_run` bomb←gun, `reverse_directions` knife←bomb and gun←bomb declared now, `_no_post_hoc_picking` | yes |
| 10.2 projection-out and counterfactual component replacement preserving the orthogonal residual; TRAIN-estimated directions only; never fit on test | `hypotheses[H2a]`, `hypotheses[H2b]` (+ numeric verification of the residual), `directions.estimated_on = "TRAIN domains ONLY"`, `directions.void_if` | yes |
| 10.3 seven controls; verify intervention magnitude; persist pre/post norm, projection removed, cosine, layer, token, occurrence, actual hook fired count | `controls.arms` C1–C7 (+ the honest note that the "orthogonal harmful direction" is NOT AVAILABLE on this bank rather than substituted), `persist_per_row_and_per_arm` | yes |
| 10.4 both scope levels preregistered as distinct hypotheses, multiplicity corrected, "do not rescue a failed single-layer test by inventing a multi-layer one later" | `scope_levels.S1/S2`, `declared_as_distinct_hypotheses: true`, family `PHASE9_CAUSAL` with all six members | yes |
| 10.5 four success conditions; "if probe score changes but model interpretation does not: decodable but not causally used. That is a valuable result." | `primary.success.conditions` (conjunctive), `primary.negative.MANDATORY_WORDING` | yes |

**No disagreement was found**, so nothing in the analyzer is a choice between the two. Where the
config is *more* specific than the mandate (the four directed pairs as fixed strata; O3 demoted to
"reported, not required"; the p-floor rule) the analyzer follows the config, which is the frozen
document.

The one genuine conflict found is **not** config-vs-mandate: it is **config-vs-code**, and it is
`BLOCKER Q9` in section 7 below.

## 1. Where the schema came from

**A COMPLETED PHASE 7 run was inspected**, not derived from the writer.
`outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103` has
`DONE.json {status: ok, rows_written: 5568, wall_seconds: 2296.557}`. Three of the six banks were
complete at the time of writing (`button_bomb`, `button_knife`, `button_gun`); `basket_bomb` was
mid-flight and had no `DONE.json`, which is precisely why `_find_run` filters on `DONE.json` rather
than on recency (C-051/C-012).

Fields taken verbatim from `results.jsonl` (30 keys, row 0 read directly):

```
prompt_id prompt_sha16 family_id condition cell domain split bank_block query_kind n_examples
strength consistency example_position role_style target_surface n_target_occurrences arm model
knockout_scope readout logp_concept p_concept n_variants_concept logp_codeword p_codeword
n_variants_codeword option_mass top1_id semantic_logodds semantic_margin_p_diff
```

and from `summary.json`: `option_mass["semantic/semantic_one_word"]` with `median_true`,
`frac_above_1pct`, `reportable`, plus `option_mass_gate`. On the inspected bank
`semantic_one_word` has `median_true = 0.0825`, `reportable = true`, `option_mass_gate = "PASS"`
— i.e. the primary mechanistic channel is engaged on that bank. That is a *bank-level*
observation, not the phase-level Q0 sign-off, which needs all six.

`semantic_logodds = logp_concept - logp_codeword` (`score_behavior.py:2193`). No field name in the
analyzer was invented; the two artifacts the analyzer *defines* (§4) are new files, not new fields
of an existing one.

## 2. The population, unchanged

Bank family `ts116m`, six banks `{button,basket} × {bomb,knife,gun}`, each pinned by
`bank_file_sha16` + `bank_rows_sha16` and verified against disk at load. Cell **`C`** — selected on
the field `cell`, never on `condition` (A-039: the wrong field binds zero rows). Query kind
`semantic_one_word`, dose `n_examples = 4`. Three whole-population exclusions
(`restaurant_kitchen`, `subway_station`, `school_campus`, all in TRAIN) leave 113 analysed domains
split 67/23/23 by `data/boombness_prompts/dcs_ts116_domain_split.json` field `dsplit`.
Rows per domain per concept = 10, so **230 rows per arm on TEST**.

Independence unit is the **domain**. Permutation is arm-label flip *within domain* over whole
domains; row-level permutation has a measured FPR of 0.2000 on this design and is not available in
the code path at all.

## 3. What the analyzer implements, in mandate section 10 order

### 3.1 — H1, the upper-bound activation patch (`10.1`)

Source `C_knife` → target `C_bomb`, matched exactly on **domain, family (codeword bank), codeword,
n_examples**. An unmatched pair is refused, never substituted.

Reuse is `src/boombness/donor_patch.py` `ActivationCapture` / `DonorBlock` /
`DonorPatch(strict_ids=True)` — the class that *refuses rather than misaligning*. Two things about
it had to be got right and both are unit-tested:

1. **`strict_ids` compares `recipient_ids[p]` against `donor.input_ids[p]` at the same absolute
   index.** Across concepts the prompts have different lengths — the frozen file records the
   absolute codeword index as identical in **0/2300** triples, mean cross-concept spread
   9.36 ± 5.90 tokens — so a single shared absolute position list is wrong before any relaxation is
   even considered. `donor_span_contract()` therefore resolves the span **end-relative in each
   prompt separately** (`len(input_ids) + rel_end`) and pairs by offset. `build_cross_prompt_donor`
   then addresses the `DonorBlock` in **recipient** indices carrying the **donor's** tokens, so
   `DonorPatch`'s check re-verifies, for every strictly checked position, that the token whose
   activation is being written matches the token being written over. The guard is not weakened; it
   is correctly addressed.
2. **The concept-word span.** Over a wide span the concept word itself (`bomb` vs `knife`)
   necessarily differs and `DonorPatch` will reject there even on the aligned bank. The contract
   exempts **exactly** that span and asserts identity everywhere else, and it refuses three ways:
   a differing token that was *not* declared exempt; an exempt offset whose tokens are identical
   anyway (an over-broad relaxation that bought nothing and hid something); and an exemption
   covering the whole span (which is `strict_ids` turned off with extra steps). Positions written
   without an identity check are counted into the artifact as
   `n_written_without_identity_check` rather than disappearing inside a relaxed predicate.

For the sites this phase actually edits (`codeword_last`, rel_end −10, one subtoken, byte-identical
across concepts) the exempt set is **empty** and identity is asserted at every patched position.
The exemption machinery exists, is tested, and is not used by the declared arms — which is the
right way round.

H1 is an **upper bound on purpose**: it replaces the whole state, so it cannot separate the concept
direction from everything else at that site. If H1 does not move O2, H2a/H2b at the same site are
reported as **uninformative**, not as negatives (`primary.cannot_answer`, and the second kill
condition: they are not submitted).

### 3.2 — H2a / H2b, the surgical subspace intervention (`10.2`)

- **H2a**, projection-out: `h' = h − proj_{v_bomb_specific}(h)`. Scale-free; the realised dose is
  reported as `frac_cellmean_spread_removed`, never as alpha.
- **H2b**, counterfactual component replacement:
  `h' = h − proj_{v_bomb_specific}(h) + c_knife · v_knife_specific`, with the orthogonal residual
  preserved **exactly** and **verified numerically on every edited cell**
  (`orthogonal_residual_delta_l2`, null `I-N7`, blocking, arm VOID if non-zero).

The arithmetic mirrors `pair_common.make_project_out_hook` / `AllPositionProjectOut` /
`SinglePositionProjectOut` and the `score_behavior --intervene <dir>:project_out:<lo>-<hi>:<alpha>
--fit-dir` path; none of that is reimplemented as science. What *is* added is instrumentation (§4).

**Directions come from PR-053, TRAIN ONLY, and are reused, never refitted.** `v_bomb_specific`,
`v_knife_specific`, `v_remap`. `direction_provenance_gate()` reads the fit manifest, refuses if it
does not name its fit domains at all, and VOIDs the arm if any fit domain is validation or test.
The direction file could not be pinned in the frozen config because it does not exist yet, so its
**sha256 is recomputed at load and written into every run artifact** (checklist Q2's requirement).

### 3.3 — The controls (`10.3`), all of them

| id | arm | how the analyzer treats it |
|---|---|---|
| C1 | norm-matched random direction, 5 seeded draws (seed 20260907) | **decisive**: success requires it does NOT move O2, reported with an **equivalence interval**, never a bare `p > 0.05`. `control_band_gate` requires **5 distinct output hashes**; identical hashes VOID the band (this project has published a secretly-n=1 "control band" twice, with a fake between-draw sd of 0.0048) |
| C2 | shuffled-label concept direction | same estimator, same code path, same norm |
| C3 | `v_remap` | labelled **"the raw axis"**, never "the remapping-only axis" — R-111's question D failed and no arm in this design isolates remapping |
| C4 | same-norm activation edit, orthogonal to the concept subspace | separates "this direction matters" from "this much perturbation matters"; dosed in **gap units** (§3.5) |
| C5 | disabled-hook bridge | **blocking**: must reproduce the untouched baseline byte-for-byte *and* the hidden states at `max\|diff\| == 0.000e+00`. `liveness_gate(..., expect_enabled=False)` additionally refuses a bridge that made **zero forward calls** — a bridge that never ran the code path bridges nothing |
| C6 | untouched baseline | the PHASE 7 readout itself; no new job |
| C7 | self-patch identity (H1) | **blocking**: patch the target with its own activations; the output must be EXACTLY reproduced or no patch number means anything |

The mandate also lists "orthogonal harmful direction if available". It is **not available** on this
bank and is recorded as such rather than substituted with the house refusal directions, which were
fitted on a different population and would make the comparison a reparameterisation of the concept
axis.

### 3.4 — Both scope levels, corrected together (`10.4`)

- **S1**: `codeword_last` (rel_end −10), **block 9 only** — inherited from PR-048's
  validation-only selection, not selected here.
- **S2**: `codeword_last`, **blocks 7–14** — the band the probe reads.

Both are declared now, both are run, both are Holm-corrected inside `PHASE9_CAUSAL` across the six
members `{H1,H2a,H2b} × {S1,S2}`. Running S2 only after S1 fails would be exactly the rescue 10.4
forbids; running both and reporting the better one is the same thing wearing a different hat. A
declared member that is not run enters Holm at **p = 1.0**, never dropped. `family_members()`
refuses if the config's family is not `PHASE9_CAUSAL` or does not have exactly six members (C-106).

**The read site must be able to see the intervention.** `propagation_read_layers()` returns layers
strictly above the edited band — 10–14 for an S1 edit at block 9, 15 for the S2 band — and
`assert_read_sees_edit(..., "propagation")` refuses a propagation claim read at or below the edit.
This is C-068 applied to a write instead of a mask: at the band floor the arms are bit-identical
and the null is a statement about the read site. Reading O1 at block 9 for an S1 edit at block 9 is
still done and is legitimate *for O1* (it is the same tensor, deliberately) but is labelled
non-evidence of propagation. O2 is downstream of everything by construction, since it is scored
from generated tokens.

### 3.5 — Gap-unit dosing (`Q6`)

`gap_unit_alpha(alpha, gap)` refuses a bare alpha with no `gap` and multiplies otherwise
(alpha = 1 is one difference-of-means). At L18 the gap is 14.65, so a bare alpha = 1 is ~7% of one
diff-of-means. The bug was fixed in `aggressive_patching` and **missed at the second call site
once already**; this is the third call site and it is unit-tested
(`gap_units`, `bare_alpha_refused`).

## 4. Hook liveness — the largest single piece of this design

`C-13`: `make_project_out_hook`, `AllPositionProjectOut` and `SinglePositionProjectOut` write **no
statistics of any kind**. A hook on the wrong layer object, a hook with a zero direction, a hook
whose handle was removed before the forward, and a hook that only ever sees decode steps all
produce **exactly** the artifact that a real intervention with no effect produces.

**A dead hook scores as a clean null.** That is the single most dangerous failure mode in this
phase and it is the recorded state of the hooks this work was told to reuse.

The analyzer therefore ships instrumented wrappers — `make_instrumented_project_out_hook`,
`make_instrumented_component_replace_hook`, `InstrumentedHook`, and the donor contract — which
record per row and per edited (layer, position):

```
hook_fired_count  n_forward_calls  n_destination_rows
n_cells_edited_realised  n_cells_edited_expected
activation_norm_pre  activation_norm_post  norm_ratio
projection_removed_l2  frac_cellmean_spread_removed
cos_pre_post  cos_edit_vs_direction  orthogonal_residual_delta_l2
layer  rel_end  seq_len  resolved_absolute_index  occurrence_index  n_subtokens
direction_file_sha256  control_draw_seed  enabled
```

Three new artifacts carry them, defined here because the runner must write something the analyzer
can refuse on:

| file | contents |
|---|---|
| `PR057_ARM.json` | the arm manifest echo — what the run believed it was doing |
| `PR057_LIVENESS.jsonl` | one record per row per edited (layer, position) — the C-13 fix |
| `PR057_PROBE.jsonl` | one record per row per read layer — O1 from the frozen PR-048 probe |

`liveness_gate()` refuses an arm whose hooks did not **demonstrably fire** *and* **demonstrably
change the state**: `hook_fired_count == 0`, a partially dead hook, `realised != expected` cells, a
zero `n_cells_edited_expected` (a check that binds zero is not a check),
`projection_removed_l2 ≈ 0`, `cos(h_pre,h_post) == 1`, or a bridge record leaking into a live arm.
`verdict()` puts the VOID branch **first**: unclean liveness returns
`VOID — HOOK LIVENESS UNCLEAN`, and the mandated negative wording is simply not reachable from
that state. A null with an unverified hook is VOID, not a negative.

`audit_end_relative()` enforces `resolved_absolute_index == seq_len + rel_end` on every record and
reports how many *distinct* absolute indices appeared — a single value across concepts is the
signature of an absolute index reused across examples, this repository's twice-recorded bug class.

**Unit-tested, on CPU, against the real hook functions** (not a re-implementation): a live hook
fires and changes the state; a **deliberately disabled hook reproduces its input exactly, passes as
a bridge, and is REFUSED when presented as a live arm**; a hook that never ran is refused; a
zero-norm direction is refused before it can score a null.

## 5. The four success conditions (`10.5`), as four separate checks

`evaluate_success()` returns a per-condition record and a conjunction:

1. **O1** — the frozen PR-048 probe's posterior margin (source minus target) moves in the intended
   direction, significantly, at the domain level.
2. **O2** — the semantic readout, the **model-interpretation** variable, moves in the intended
   direction, significantly, at the domain level.
3. **C1** — the norm-matched random control does **not** move O2, with its equivalence interval and
   with its five draws proved distinct.
4. **Across domains** — a domain-level sign test with a majority of test domains moving the
   intended way. Not a pooled-row result.

All four together, or it is not a causal result. Each alone has a cheap way to be satisfied — (1)
by construction, (2) by a large enough perturbation of anything, (3) by an under-dosed control, (4)
by a lucky pooling — and the self-test asserts that **each of the four dropped alone yields
`success = False` at 3/4**.

O1 is co-required but never sufficient: an edit along a direction moving a linear readout of that
same direction is nearly guaranteed by construction, which is why O2 and not O1 is the primary.

**The negative.** If O1 moves and O2 does not, `verdict()` emits the literal string

> `DECODABLE BUT NOT CAUSALLY USED UNDER THIS INTERVENTION`

which lives in the code as `MANDATORY_NEGATIVE_WORDING`, is cross-checked against
`primary.negative.MANDATORY_WORDING` at every load (a divergence is a refusal), and is the only
path to a negative. `assert_sayable()` scans every emitted string against
`things_that_must_not_be_said` merged with a local list and **raises** on the forbidden sentence, so
it cannot reach a report, a log or a Slack draft. "The representation is meaningless" is not
sayable by this program. If **neither** O1 nor O2 moves, the verdict is
`VOID PENDING DIAGNOSIS`, not a negative: check hook liveness, dose and the bridge first.

## 6. Statistics and the underpowered branch

- Domain-level group permutation, arm-label flip within domain, `n_perm = 10000`, seed 20260907.
  Every p is printed beside its attainable floor via the imported `fmt_p`; on zero exceedances it
  prints `p < 1/(B+1)` and says the design cannot resolve below it.
- Two-sided sign test over domains with **exact ties counted**.
- Holm across the six `PHASE9_CAUSAL` members on the O2 p-values; controls are **gates, not
  members**, and are not corrected.
- `q1_power()` measures the between-domain SD of O2 on **VALIDATION DOMAINS ONLY**, recomputes MDE
  and power for the declared 0.5-nat effect at n = 23, and returns
  `CANNOT ANSWER WITHOUT READING TEST` when power is below the bar. The bar itself is **parsed out
  of the frozen file** (checklist Q1 / `primary.cannot_answer`) rather than typed as `0.80` in the
  analyzer — a threshold re-typed in code is B-020 with a different fingerprint. It refuses if
  `power.o2_semantic_readout.between_domain_sd` has stopped being `null`, and refuses a measured SD
  of exactly zero (that is the byte-identical-arms signature, not a measurement). Both branches are
  unit-tested.

Numerical tolerances (`1e-6` for "the state changed", `1e-4` for the orthogonal residual) are the
only bare numbers in the file. They are tolerances, not scientific gates, and they are named as
arguments so a caller can tighten them.

## 7. What the analyzer found that is NOT yet buildable — new blockers

These were discovered while writing the analyzer and are **not** in the frozen checklist. They are
blocking. The config is frozen, so they are recorded here and must be added to
`pre_extraction_checklist` (as booleans, per C-086) before `--for-extraction` can pass.

**Q9 — the preregistered O2 is not computable with the instrument as it stands. (BLOCKING)**
`score_behavior` asserts **one codeword/concept pair per bank** (`score_behavior.py:1960`) and
builds the answer set once from `rows[0]`, so a bomb bank scores `{bomb, button}` and nothing else.
There is **no `logP(knife)` on a bomb bank**. The frozen config's O2 is
`semantic_logodds(source vs target concept)` over `{bomb, knife, gun, codeword, neither}`. That
contrast cannot be formed. The fix is to extend `_semantic` to a multi-concept answer set — the
existing `logp_{group}` rule (`next_token_readout:119`) then emits `logp_bomb / logp_knife /
logp_gun / logp_codeword` with no new naming convention — and to relax the one-pair assertion for
that answer set only. `o2_from_rows()` requires those fields, and when they are absent it returns
`computable = False` and reports the companion `delta semantic_logodds(target concept vs literal
codeword)` **explicitly labelled as unable to satisfy success condition 2**, because it cannot
distinguish "the answer moved toward knife" from "the readout was destroyed". The analyzer does not
substitute it and does not emit a verdict from it.

**Q10 — there is no frozen probe artifact for O1. (BLOCKING)** `scripts/dcs_ts_pr048_analysis.py`
persists `SELECTION_TRACE`, the selected layer/C and the per-domain accuracies, but **not the
fitted coefficients**. O1 needs the PR-048 estimator itself, frozen, at layer 9 / C = 0.01, fitted
on TRAIN domains, with a sha. It must be exported and **must not be refit under intervention** —
refitting would let the probe chase the edit.

**Q11 — there is no intervened extraction path for O1. (BLOCKING)** `extract_boombness.py` has no
`--intervene`. O1 must therefore be captured **inside** the intervention run: a read hook at the
primary read layer *and* at `propagation_read_layers()`, applying the frozen probe on the fly and
writing `PR057_PROBE.jsonl`. Capturing it in a separate un-intervened job would measure nothing.

**Q12 — four things `score_behavior` cannot do yet.** (a) a **cross-prompt donor** — `--rescue-donor`
offers only `clean` and `self`, both on the *same* prompt (this is the config's own `Q3`);
(b) a **`component_replace` mode** for H2b; (c) a **disable-hooks flag** for the C5 bridge that runs
the whole code path and edits nothing; (d) **single-position scoping** for S1 — `make_intervention`
only ever constructs `AllPositionProjectOut`, so an S1 arm launched through it today would silently
be an all-position edit. All four must route through the instrumented wrappers in
`dcs_ts_pr057_causal.py`, or the C-13 hole reopens.

**Q13 — the norm-matched control's base direction.** `make_intervention`'s `random` / `orthogonal`
controls are derived from `payload["d_surface"]` specifically. If the PR-053 fit payload does not
alias `d_surface` to `v_bomb_specific`, C1 and C4 will be norm-matched to **the wrong base
direction** while looking correct in every log. The arm manifest echo must record the control's
base direction and the analyzer must refuse a mismatch. C4 additionally needs a `gap` entry for its
direction or `make_intervention` refuses the additive dose — which is the correct behaviour and
must not be worked around.

## 8. Launch

**Order is fixed and is not negotiable:** Q0 → Q1 (validation only) → smoke (Q7) → H1 → H2.
H1 is the upper bound; if it does not move O2 at a site, H2a/H2b are **not submitted** at that site
(the config's second kill condition), and the H2 arms are reported as uninformative rather than as
negatives.

Arms in the manifest (`--plan`): **54 runs** — 24 live (16 H1 across 4 directed pairs × 2 scopes ×
2 codewords, 4 H2a, 4 H2b) and 30 control (20 C1 draws, 2 each of C2/C3/C4/C5/C7). C6 is the
PHASE 7 baseline and needs no job.

### 8.1 The exact sbatch command

The runner `src/boombness/pr057_run_causal.py` **does not exist yet** (blocking item Q4b below); it
must load the model **once** and loop the manifest, because 54 separate `score_behavior`
invocations would spend more wall time loading weights than computing. It imports its hooks,
its donor contract and its arm manifest from `scripts/dcs_ts_pr057_causal.py` so that the runner
and the analyzer cannot drift into two files that disagree about what an arm is.

```bash
# 1. the argsfile MUST live on the shared filesystem -- /tmp is node-local and the job dies in 3s
cat > outputs/boombness/pr057_args.txt <<'EOF'
--prereg configs/dcs_ts_pr057_phase9.json --stage h1 --split test --fit-dir outputs/dcs_ts_pr053_diffmeans/<run> --emit-liveness --emit-probe
EOF
# no quote characters and no spaces inside a value: BOOMB_ARGS is word-split (job 766661)

# 2. submit
sbatch --export=ALL,BOOMB_SCRIPT=pr057_run_causal.py,BOOMB_EXPECT=pr057_run_causal.py,BOOMB_REQUIRE_ARGS=1,BOOMB_ARGSFILE=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/boombness/pr057_args.txt \
       --time=06:00:00 \
       src/boombness/slurm/run_boombness.sh
```

`BOOMB_EXPECT` and `BOOMB_REQUIRE_ARGS=1` are both set: without them a mistyped variable name falls
through to the runner's default script and exits `COMPLETED 0:0` in 11–27 minutes having run the
wrong thing (jobs 853040–853045, ~1.7 GPU-hours, and nothing caught it). `run_boombness.sh` already
pins the six L40S nodes `n-801..n-805,t-806`; do **not** add `--exclude` on the sbatch line, which
nullifies the `#SBATCH --nodelist`.

The **Q1 validation power run** is the same command with `--stage q1 --split validation`, and it
must complete and print `PROCEED` before any `--split test` job is submitted.

### 8.2 Expected cost

Measured on the PHASE 7 baseline: 5568 rows in 2296.557 s wall on one L40S, `eager` attention,
`whole_answer` readout, `max_new 8` — **2.42 rows/s including model load**, so the figures below
are conservative.

| stage | arms | rows | estimate |
|---|---|---|---|
| Q7 smoke: H1 × S1, a handful of TRAIN domains, self-patch + liveness | 2 | ~60 | ~10 min incl. load |
| Q1 power: H1 × S1 and H2a × S1 on VALIDATION | 2 | 460 | ~10 min incl. load |
| H1 confirmatory (16 arms + 2 C7), TEST | 18 | 4 140 | ~29 min (+~6% for the donor forward per row) |
| H2a/H2b confirmatory, TEST | 8 | 1 840 | ~13 min |
| controls C1–C5, TEST | 28 | 6 440 | ~44 min |
| **total, one allocation, model loaded once** | **54** | **12 420** | **~1.5–2 GPU-hours** |

Request `--time=06:00:00` (the house default in `run_boombness.sh`), one GPU, `--mem=48G`,
`--cpus-per-task=4`. Do not raise the memory: 48G leaves all 8 GPU-shares per node feasible and is
the fast-allocating default. Budget **≤ 2 concurrent model-loading jobs per node** — three on one
node produced a 16× weight-load slowdown.

If the H1 kill condition fires, the H2 and most of the control rows are never spent and the true
cost is roughly half the table.

## 9. Blocking checklist — what must close before anything is submitted

From the frozen `pre_extraction_checklist` (`--for-extraction` refuses on every one of these
today, which is the design working):

| id | item | state |
|---|---|---|
| **Q0** | the PHASE 7 readout (job 865335) has LANDED on **all six banks**, `option_mass` shows `semantic_one_word` engaged, and the installation stratification exists | **NOT DONE** — 3 of 6 banks complete at the time of writing; without it O2 does not exist and the phase repeats R-097 exactly |
| **Q1** | between-domain SD of O2 measured on **VALIDATION ONLY**; MDE and power recomputed; return CANNOT ANSWER if under the bar | **NOT DONE** — code path exists (`q1_power`, both branches tested); needs the validation run |
| **Q2** | PR-053 TRAIN-ONLY direction file produced; fit manifest names TRAIN domains only; sha256 recomputed and recorded | **NOT DONE** — `dcs_ts_pr053_diffmeans.py` writes a JSON report and **no `directions.pt`**; `direction_provenance_gate` is written and tested and refuses without it |
| **Q3** | cross-prompt donor for H1: identity re-verification **scoped** to the patched span and still refusing a mismatch; self-patch reproduces exactly | **DESIGNED AND UNIT-TESTED HERE** (`donor_span_contract`, `build_cross_prompt_donor`, `self_patch_gate`); **the GPU wiring is not built** |
| **Q4** | write `scripts/dcs_ts_pr057_causal.py` — every threshold via `Prereg.require()`, no numeric gate literal, underpowered branch as a code path, conjunctive success rule explicit, refusal to emit a verdict on unclean liveness | **DONE** — 46 self-test checks, 0 failures |
| **Q4b** | *(new)* write `src/boombness/pr057_run_causal.py`, the GPU runner, importing hooks/manifest from the analyzer | **NOT DONE** |
| **Q5** | mutation-test the analyzer: dead hook, zero-magnitude edit, identical-hash control band, broken orthogonal residual, self-patch that changes the output, direction fitted on test, absolute edit index each produce a refusal | **DONE** — `--mutate`, **21/21 RED**, including all seven named |
| **Q6** | gap-unit dosing verified at this call site | **DONE** — `gap_unit_alpha`, tested both ways |
| **Q7** | smoke run: H1 × S1 on a handful of TRAIN domains, confirming liveness, the self-patch control and a non-zero edit magnitude, before the full submission | **NOT DONE** — needs Q4b |
| Q8 | confirm PR-056 (PHASE 8) completed or explicitly deferred so the two GPU phases do not compete for fair-share | not done (non-blocking) |
| **Q9** | *(new)* multi-concept answer set so O2 exists at all | **NOT DONE — the phase cannot produce its primary outcome without it** |
| **Q10** | *(new)* export the frozen PR-048 probe (coefficients + scaler + sha) for O1 | **NOT DONE** |
| **Q11** | *(new)* intervened probe capture inside the intervention run (`extract_boombness` has no `--intervene`) | **NOT DONE** |
| **Q12** | *(new)* `score_behavior`: cross-prompt donor path, `component_replace` mode, disable-hooks bridge flag, single-position scoping for S1 | **NOT DONE** |
| **Q13** | *(new)* control base-direction alias (`payload["d_surface"]`) recorded and checked, and a `gap` entry for C4 | **NOT DONE** |

## 10. What this phase still cannot say, whatever it returns

- **REGISTER remains CANNOT ANSWER** as an absolute confound on this corpus. It cancels inside
  *this* design's paired within-prompt contrasts — a real strength, stated here so it is not
  over-claimed elsewhere — and nowhere else.
- **CLAIM B remains UNSUPPORTED.** R-111's question D failed: the residual axis carries remapping
  *and* identity together (0.9764 vs the hard negatives, but 0.8309 separating knife/gun from the A
  baseline). A causal result here does not repair it, and C3 is labelled "the raw axis" for exactly
  that reason.
- **CLAIM A is narrowed by R-112 to the PROMPT, not the codeword** — a control nine tokens
  downstream decodes identity at 0.9261 against the codeword's 0.9446, which does not survive
  preregistered Holm.
- Behaviour, ASR and representation–behaviour mediation are **not** run in this phase.
- **Llama-3.1-8B-Instruct only**, by decision (Qwen3-14B is absent from both caches under
  `HF_HUB_OFFLINE=1`). A scope limit, never a model-specificity claim.
- And the sentence this design exists to make sayable if the data say so:
  **DECODABLE BUT NOT CAUSALLY USED UNDER THIS INTERVENTION** — scoped to this intervention, these
  sites, this dose and this population. "Under this intervention" is part of the claim, not a hedge
  that can be trimmed.

---

### Reproducing the checks in this document

```bash
python3 scripts/dcs_ts_pr057_causal.py --self-test   # 46 checks, 0 failures
python3 scripts/dcs_ts_pr057_causal.py --mutate      # 21/21 mutations RED
python3 scripts/dcs_ts_pr057_causal.py --plan        # the 54-arm manifest with launch commands
python3 scripts/dcs_ts_pr057_causal.py               # REFUSES: no arm has run yet
python3 scripts/dcs_ts_pr057_causal.py --for-extraction   # REFUSES: 8 blocking items outstanding
```
