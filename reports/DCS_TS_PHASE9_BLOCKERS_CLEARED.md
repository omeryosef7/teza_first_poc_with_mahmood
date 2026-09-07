# DCS-PR-057 — PHASE 9 BLOCKERS Q9–Q13: what was cleared, and how it was checked

**Date:** 2026-09-07 · **Author:** this work session · **Nothing was run on a GPU. No SLURM job was
submitted. No commit was made.**

Governing documents, read in full before any edit:

- `reports/DCS_TS_PR057_DESIGN.md` — the design report that raised Q9–Q13 (§7, §9)
- `configs/dcs_ts_pr057_phase9.json` — **FROZEN**, governs
- `external_md/DCS_THESIS_SCALE_MANDATE_20260906.md` §10 (lines 789–927)
- log entry **C-112**, which changed the primary arm after that report was written

Files edited (all four are SHARED with other phases):

| file | blocker(s) |
|---|---|
| `doublespeak_causality/pair_common.py` | Q12 (liveness instrumentation, single-site scoping, the disabled-hook bridge) |
| `src/boombness/score_behavior.py` | Q13, Q12, Q9 |
| `scripts/dcs_ts_pr048_analysis.py` | Q10 |
| `scripts/dcs_ts_pr057_causal.py` | Q9 (the C-112 primary), Q10/Q11 (frozen probe + in-run O1 capture), plus 27 new self-test checks and 17 new mutations |

> **One correction to the task as written.** `make_intervention` does **not** live in
> `pair_common.py`; it lives in `src/boombness/score_behavior.py:938`. `pair_common.py` holds the
> hook *classes* it constructs (`AllPositionProjectOut`, `SinglePositionProjectOut`,
> `make_project_out_hook`). Q13 and the scoping half of Q12 are therefore fixed in
> `score_behavior.py`, and the hook-level instrumentation and the bridge in `pair_common.py`. Both
> files are on the permitted list, so nothing was written outside it.

---

## 0. The C-112 design change, honoured

R-115 measured installation per concept on four banks: bomb 70/113 domains, knife 3/113, gun 1/113.
**R-116 (2026-09-07) redid it on all six banks and supersedes those figures — knife is ZERO:**

| concept | median `concept_binary_prob` | median `semantic_logodds` | domains installing (113) | on the 23 TEST domains |
|---|---|---|---|---|
| bomb | 0.7284 | +0.99 | **0.619** | **0.522** |
| knife | 0.0011 | −6.83 | **0.000** | **0.000** |
| gun | 0.0006 | −7.38 | 0.009 | **0.000** |

Mandate 10.1's upper-bound patch takes a **donor** `C_knife` prompt and writes it into a `C_bomb`
target. Under R-115 that donor was uninstalled for ~97 % of domains. Under R-116 it is uninstalled
for **all** of them: "the reading did not shift to knife" is a statement about the donor, not about
the target's concept axis, in **every** domain.

That arm is therefore **demoted to exploratory** and its null is **CANNOT ANSWER by construction**.
R-116 strengthens the demotion rather than softening it: the arm is not under-powered, its
population is **empty**, so on this bank it is **unconstructible** and must not be submitted at all.
(This landed after the work below was done; the stale R-115 figures were carried in
`C112_PRIMARY_IS_10_2` and in this report and have been corrected to R-116 in both.)
Mandate **10.2** — project `v_bomb_specific` out of a BOMB prompt where the concept demonstrably
*does* install — is the **primary** causal test. It is recorded in code, not only here, as
`C112_PRIMARY_IS_10_2` in `scripts/dcs_ts_pr057_causal.py`, and the primary outcome has its own
function (`o2_projection_out_from_rows`) separate from the exploratory cross-concept one
(`o2_from_rows`). The work below prioritises 10.2 accordingly: **Q13 → Q12 → Q10 → Q9 → Q11**.

---

## 1. Q13 — the norm-matched control's base direction (**CLEARED**)

### The defect

`make_intervention`'s `random` / `orthogonal` / `in_subspace` / `in_subspace_orth` controls read

```python
base = payload["d_surface"]                      # HARD-CODED
...
gaps = (payload.get("gap") or {}).get("d_surface", {})
```

On the PR-053 payload the live direction is `v_bomb_specific`, not `d_surface`. Every consequence
of the mismatch is invisible:

- **C1** would be norm-matched to an axis no PHASE 9 arm touches;
- **C4** would be orthogonal **to the wrong thing** — and "orthogonal to the concept subspace" is
  the entire content of that control;
- an additive control would be dosed in `gap["d_surface"]` units, i.e. dose-mismatched as well as
  axis-mismatched (the F-3 retraction's arithmetic, one level down);
- the arm label, the seed, the draw log and the printed dose would all read correctly.

This is the **eighth** instance in this project of a checker disagreeing with the thing it checks,
and it is the variety that looks correct in every log.

### The fix — make the mismatch impossible, not unlikely

Four changes, all in `score_behavior.py`:

1. **The base is named in the spec.** `split_control_base()` parses `random@v_bomb_specific`, or a
   `control_base=` / `--pr057-control-base` argument. It travels with the arm through the composed
   recursion instead of being assumed. **No `@` and no flag ⇒ `d_surface`, exactly as before.**
2. **The control is derived from the live direction object**, layer by layer, from
   `payload[<named base>]`. A base that is not in the payload is a refusal that names what the
   payload *does* carry — never a fall-through to another axis.
3. **The norms are asserted at hook-install time**, before a single forward runs, by
   `assert_control_norm_matched()`. It refuses a relative norm difference above `1e-4` (`1e-2` for
   half precision, announced), a zero-norm base, and a check that binds **zero layers**.
4. **The resolved base and the per-layer norms are echoed** into `arm_echo` → `PR057_ARM.json`, so
   a reader can see which axis was controlled for without re-deriving it.

Two answers to "which axis is this a control for" (an `@base` *and* `--pr057-control-base`) is a
refusal, at argument-parse time and again inside `split_control_base`.

### Evidence it is real, and tight

Measured on the actual house control makers (`ab.py`, §5): every one of them renormalises exactly
to `‖base‖`, so the realised relative difference is float32 round-off — `0.0` for `random` and
`in_subspace`, `8.4e-08` for `orthogonal` at one layer. The `1e-4` bar is ~1000× that, and the
mutation `M28` (control matched to the wrong base) is RED.

---

## 2. Q12 — single-site scoping and a real disabled-hook bridge (**CLEARED**)

### (a) Scope, mandate 10.4

`make_intervention` only ever constructed `AllPositionProjectOut`. An S1 (single-site) arm launched
through it today would have been an **all-position, all-timestep edit reported under the
single-site arm's name** — a larger intervention wearing a smaller label, which is exactly the
shape of the `knock_scope` defect already recorded on the line above it.

`SinglePositionProjectOut` existed in `pair_common.py` and was never wired. It is now:
`make_intervention(..., edit_positions=[...])` builds one `SinglePositionProjectOut` per position
per layer; `edit_positions=None` (the default) keeps `AllPositionProjectOut` unchanged. The CLI
entry is `--pr057-edit-positions`, which takes **end-relative** (negative) offsets and resolves
them **per row** against that row's realised length — never a length captured from an earlier row.
A non-negative offset is refused by name as this repository's twice-recorded bug class.

Refusals: an **empty** position list (a single-site edit with no site is a no-op, and a no-op
scores as a healthy null), duplicate positions (a double dose under a single-dose label), and
`edit_positions` with `mode != project_out` (refusing beats silently widening the scope back).

Measured on a 12-layer toy model, band `[7, 8]`, a 10-token prompt (`wire.py`, §5):

| arm | class built | positions moved |
|---|---|---|
| S2, `edit_positions=None` | `AllPositionProjectOut` ×2 | **10 of 10** |
| S1, `edit_positions=[7]` (rel_end −3) | `SinglePositionProjectOut` ×2 | **1 of 10**, `resolved_absolute_index = [7] = 10 + (−3)` |

### (b) The C5 bridge, as a code path

`pair_common.DisabledHookBridge` registers on the **same layer objects**, **runs the real hook in
full**, measures what its edit would have been, and returns the **unmodified** output.

"Just omit `--intervene`" is not this control: it never runs the direction load, the resolution,
the dtype/device cast or the projection, so it cannot show that the machinery *around* the edit is
inert. And it records `would_have_changed_max_abs`, so a bridge whose inner hook was itself dead is
**refused** rather than passing as a perfect identity.

Measured: output **bit-identical** to the untouched forward
(`torch.equal(y, baseline) == True`), `would_have_changed_max_abs = 0.063 / 0.123` at the two
layers, `n_cells_edited_realised = 0`, liveness clean **as a bridge**. The **same record presented
as a live arm** returns `['hook_fired_count==0', 'zero_cells_edited', 'zero_projection_removed',
…]` — i.e. **a deliberately disabled hook is DETECTED, not tolerated.**

### (c) Hook liveness — the C-13 hole, closed at the hook

`make_project_out_hook`, `AllPositionProjectOut`, `make_single_position_project_out_hook` and
`SinglePositionProjectOut` wrote **no statistics of any kind**. They now accept `stats=` (default
`None` ⇒ no record and an unchanged hook body) and fill a `hook_stats_dict()` with every quantity
mandate 10.3 lists:

```
mode enabled layer alpha direction_norm
n_forward_calls n_prefill_forward n_decode_forward
hook_fired_count n_destination_rows n_cells_edited_realised
activation_norm_pre activation_norm_post norm_ratio
projection_removed_l2 sum_projection_removed_l2 cos_pre_post max_abs_delta
positions rel_end occurrence_index resolved_absolute_index seq_len_last
would_have_changed_max_abs would_have_changed_l2 bridged_and_discarded
```

`AllPositionProjectOutMultiLayer` takes `stats_by_layer`: **one independent record per layer**,
because a single shared counter lets a hook that fired at one layer mask a hook that never fired at
another — a *partially* dead band.

`project_out_liveness_violations()` refuses: a record missing any key; `n_forward_calls == 0`; a
zero-norm direction; and, on a **live** arm, `hook_fired_count == 0`, zero cells edited, zero
projection removed, `max_abs_delta == 0`, an edit below float32 resolution relative to the state,
or an unrecorded cosine. On a **bridge** it refuses any edited cell and a bridge whose inner hook
would not have changed anything.

> **A bug the instrument found in itself, on its first run.** The first version of the
> single-position recorder read `hp` *after* `h[:, pos, :] = h_new`. `hp` is a **view** into the
> cloned tensor, so it compared the post-edit state with itself and reported
> `projection_removed_l2 = 0.0`, `cos_pre_post = 1.0` — the exact dead-hook signature — for a hook
> that had fired correctly. The instrument would have manufactured the failure it exists to
> detect. Fixed by copying the pre-edit slice before the write; the comment in the file says so.

> **A tolerance decision, stated rather than hidden.** `cos_pre_post` is **recorded** (mandate 10.3
> requires it) but is **not gated on `== 1.0`**: at float32 a genuine small edit rounds the cosine
> to `1.0000001`, so gating on it would refuse **live** hooks. "Did the state change" is answered
> by `max_abs_delta` and by a scale-free `projection_removed_l2 / activation_norm_pre` bar at the
> float32 epsilon, which catches an under-dosed edit that `max_abs_delta > 0` alone would not.

### (c-bis) A second latent wrong-scope defect, found and fixed on the way

`InstrumentedHook` (already in `scripts/dcs_ts_pr057_causal.py`) resolved its target as

```python
if hasattr(model, "register_forward_hook"):   # a real HF model HAS this
    self.layer = model
else:
    self.layer = dc._get_layers(model)[layer_idx]
```

An HF model **is** an `nn.Module`, so the first branch always wins on the GPU path: the hook would
have been registered on the **whole model**, editing (or, for the probe capture, reading) the
**final** hidden state while every log said `layer 9`. The test path — where the object passed *is*
a bare layer — would have looked perfect. That is the Q12 wrong-scope shape one level down, and the
first draft of `ProbeReadCapture` inherited it by copying.

Both now go through a resolver that tries `ds_common._get_layers` **first** and only treats an
object it cannot resolve as being itself the layer (`_resolve_hook_target` in the analyzer,
`_resolve_layer` in `pair_common`). The order is load-bearing and the docstring says why.

### (d) Per-row liveness artifact

`--pr057-liveness-out auto` writes `PR057_LIVENESS.jsonl` into the run directory — where the
analyzer's `load_arm_run` already looks — one record per row per hook, carrying the row's
`prompt_id / domain / split / cell / concept / codeword`, `seq_len`, and the violations list.

Three refusals, all `SystemExit` **on purpose**: `SystemExit` is a `BaseException`, so the per-row
`except Exception` does **not** catch it and a dead hook **aborts the run** instead of being charged
to the failure ledger and producing 229 more rows under a label claiming an intervention happened.

- zero instrumented hooks on a row → refuse (a zero-hook bind is not a null result);
- any liveness violation on any row → write the record, flush, abort;
- zero liveness records after the whole loop → refuse (an empty liveness file reads to a consumer
  as "no violations").

`--pr057-liveness-out` given with no `--intervene` is refused up front, as are
`--pr057-disable-hooks`, `--pr057-edit-positions` and `--pr057-control-base`. And
`--pr057-disable-hooks` **without** `--pr057-liveness-out` is refused: the bridge is a
control whose entire content is a liveness claim, and without the record it is
indistinguishable from a run with no hooks at all — the one thing it exists to rule out.

---

## 3. Q10 — the frozen PR-048 probe, exported (**CLEARED**)

`scripts/dcs_ts_pr048_analysis.py` persisted `SELECTION_TRACE`, the selected `(layer, C)` and the
per-domain accuracies but **not the estimator**. With no frozen probe, the only way to compute O1
under intervention would have been to **refit** — which lets the probe chase the edit and makes O1
unfalsifiable by construction.

`fit_score()` gained `return_estimator=False` (**default-off**). The observed pass now hands back
**the objects it already fitted** — not a re-fit, because a second fit, however identical it looks,
is a different object and Q10 asks for *the* probe behind R-113. A new `res["FROZEN_PROBE"]` block
carries:

- `estimator.coef` / `estimator.intercept` / `n_iter_`, `selected_C`, `max_iter`
- `scaler.mean` / `scale` / `var` / `n_samples_seen`, `with_mean`, `with_std`
- `selected_layer`, `read_site.position`, `feature_dim`, `classes`, `sklearn_classes_`
- `fit_on`: split, row count, domain count, **the train domain list**
- `scoring_rule` in words, `sklearn_version`, `prereg`, `_do_not_refit: true`
- `sha256` — a **content** hash over the numbers (layer, C, classes, feature_dim, estimator,
  scaler), so PHASE 9 pins the estimator, not a file path

**Zero-bind refusals:** no coefficients, a scaler width ≠ `feature_dim`, a coefficient row width ≠
`feature_dim`, zero train rows or zero train domains.

**Self-verification, and why it matters.** The block re-scores the test rows **from the exported
numbers alone** — not from the sklearn objects — and refuses to write if the predictions disagree
with the estimator on a single row. A `scoring_rule` written in prose that nobody executes is the
same failure shape as a threshold published and never enforced; this one is executed. Verified
independently against sklearn for **both** parameterisations:

```
ncls=3  coef_rows=3  disagreements=0  max|FrozenProbe − sklearn predict_proba| = 0.000e+00
ncls=2  coef_rows=1  disagreements=0  max|FrozenProbe − sklearn predict_proba| = 0.000e+00
```

(The 2-class case matters: sklearn's binary parameterisation stores **one** coefficient row and a
sigmoid, not two rows and a softmax. Reading it as multiclass would silently invert a class.)

**No number the analyzer reports changed.** The block adds a key to `res`; it fits nothing, draws
no randomness, and reads nothing it did not already have.

---

## 4. Q9 — the outcome (**CLEARED**, in two parts)

### (a) `semantic_logodds` IS sufficient for the 10.2 primary — with the field names

Mandate 10.2 projects `v_bomb_specific` out of a **BOMB** prompt. The intervention and the prompt
carry the **same** concept, so the outcome needs no source-concept log-odds and no second installed
concept. The question is whether the model's semantic reading of the codeword moves **away** from
that concept, and that contrast exists on every PHASE 7 row today:

| field | meaning on a bomb bank |
|---|---|
| `logp_concept` | log P(`bomb`) — whole-answer, variant-summed |
| `logp_codeword` | log P(`button`) — same rule |
| **`semantic_logodds`** = `logp_concept − logp_codeword` | **the outcome** |
| `option_mass_core_pair` (= `option_mass` when the Q9 flag is off) | the engagement gate |
| `top1_id`, `gens.jsonl` | O3, corroborant only |

The statistic is the **domain-mean change in `semantic_logodds`** between the intervened arm and
the untouched PHASE 7 baseline over the 23 TEST domains — exactly `primary.statistic`'s form.
Implemented as `o2_projection_out_from_rows()` in `scripts/dcs_ts_pr057_causal.py`, which refuses a
zero bind and refuses a missing field rather than substituting one.

**Why it is sufficient here and was not sufficient for 10.1.** The recorded objection to
`semantic_logodds` is that a fall cannot be told from a destroyed readout — for a claim that *the
answer moved toward knife*, which needs `logP(knife)`. The 10.2 primary makes no such claim. Its
claim is one-sided and directional: removing the bomb component reduces the bomb reading.
"Destroyed" is not an alternative *interpretation* of that claim, it is a **rival cause** for the
same observation, and rival causes are what the preregistered controls are for. So the function
returns `reportable_alone: False` and ships the rival-cause list **as data**, not as a sentence in
a report nobody re-reads:

```
option_mass_gate        the channel must still be ENGAGED after the edit
C1  norm-matched random control, 5 distinct draws
C4  same-norm edit orthogonal to the concept subspace, dosed in gap units
C5  disabled-hook bridge reproduces the untouched baseline byte-for-byte
liveness_gate           a fall measured through an unverified hook is VOID
```

It also records `_what_it_cannot_say`: it cannot say the answer moved **toward** another concept.

### (b) An optional explicit answer set, for the exploratory 10.1 arm

`--semantic-extra-words knife,gun` (default `""` = **off**) appends extra candidate words to the
semantic answer set under the **existing** `logp_{group}` rule, so a bomb bank emits `logp_knife`
and `logp_gun`, and word-named **aliases** of the bank's own pair (`logp_bomb`, `logp_button`) so a
cross-concept contrast is expressible.

**What R-116 changes about why this is worth having.** The original justification — "it makes the
exploratory 10.1 arm measurable on the ~3 installing knife domains" — is **dead**, because R-116
puts that count at **zero**. There are no installing knife domains to measure on. What the flag is
still for is the weaker and more honest thing: it makes `logP(knife)` **expressible**, so a claim
that the reading did *not* move toward knife can be **shown** rather than assumed from the absence
of a field. A quantity that cannot be computed cannot be reported as null; this makes the null
sayable. It does **not** resurrect the 10.1 arm, whose population is empty.

**The one-pair-per-bank assertion is NOT relaxed.** Q9's original prescription was to relax it; that
turned out to be unnecessary and worse. The assertion guards against a bank carrying *two
concept/codeword pairs* being scored entirely against `rows[0]`'s pair. Adding extra **candidates**
does not admit a second **pair**, so the guard stays exactly where it is and keeps doing its job.

Refusals when the flag is used: duplicates; a word colliding with a reserved group name; a word that
**is** the bank's own concept or codeword (it is already scored — re-adding it would double-count it
in `option_mass`, and its alias is emitted anyway); and a word containing whitespace (it becomes a
`results.jsonl` field name, and a field name with a space binds zero rows silently).

**The gate's meaning does not drift.** Extra options can only *raise* `option_mass`, which would
make `--min-option-mass` more permissive. So `option_mass_core_pair` is emitted on **every**
semantic row and is what the gate is fed whenever the flag is on — the gate keeps measuring exactly
what it measured before.

---

## 5. Q11 — O1 captured inside the intervention run (**CLEARED — wired, not merely documented**)

`extract_boombness.py` has no `--intervene`, and adding one would not fix this: an un-intervened
extraction measures the **baseline**, which is O1's reference and not its outcome. The fix is not a
new extractor. It is to read the state **where it already exists**, during the intervened forward.

`ProbeReadCapture` (in `scripts/dcs_ts_pr057_causal.py`) is a **read-only** forward hook that:

- registers at the primary read layer and at each `propagation_read_layers()` layer;
- resolves the site **end-relative** per forward (`seq_len + rel_end`); a non-negative index is
  refused by name;
- applies the frozen probe on the fly and appends a `PR057_PROBE.jsonl` record carrying the
  posterior, the O1 margin, `probe_sha256`, `resolved_absolute_index`, `seq_len`, `hidden_norm` and
  `n_forward_calls`;
- **returns `output` unchanged.** That is load-bearing and it is unit-tested
  (`max|y − x| == 0.000e+00`): a read hook that accidentally edited would contaminate the very arm
  it measures, invisibly, because that arm is *supposed* to be edited.

`liveness_violations()` reports `probe_read_hook_never_ran` / `probe_read_captured_zero_rows`, so a
capture that never ran is a measured zero rather than an absent file. `o1_from_probe_rows()` refuses
a zero bind and refuses records produced by **two different probes** — O1 is defined against one
frozen estimator.

`load_frozen_probe(path, expect_sha=…)` refuses a missing file, a missing `FROZEN_PROBE` block
(naming Q10's fix), an export that was never self-verified, a self-verification with any
disagreement, and a sha that does not match the pin.

**What the runner must do** (`src/boombness/pr057_run_causal.py`, still Q4b and still not written):

```python
probe = load_frozen_probe(PR048_RESULT_JSON, expect_sha=PINNED_SHA)      # never refit
recs  = []
with contextlib.ExitStack() as st:
    for c in make_intervention(..., edit_positions=..., hook_stats=stats):
        st.enter_context(c)                                              # the EDIT hooks
    for L in [primary_read_layer] + propagation_read_layers(edit_layers, grid, n_layers):
        st.enter_context(ProbeReadCapture(model, L, probe, rel_end=-10,
                                          source="knife", target="bomb",
                                          records=recs, row_meta=row_meta))
    rec = score_the_semantic_readout(...)      # O2, under the same hooks
```

**O1 under the C-112 primary.** `FrozenProbe.margin(x, source, target)` is the cross-concept form
mandate 10.5 / `O1_probe` defines, and it is what the exploratory 10.1 arm uses. For the **10.2**
primary the matching one-sided quantity is the probe's posterior mass on the **target concept
itself** — `posterior(x)["bomb"]`, which must **fall** when `v_bomb_specific` is projected out —
and that is why `posterior()` is exposed as a first-class method rather than only as the internal of
`margin()`. Both are computed from the same frozen coefficients; the record written to
`PR057_PROBE.jsonl` carries the **full posterior**, so either reading is derivable after the fact
without a second forward. A concept the probe was never fitted on is a refusal, not a zero.

Both hook sets live in **one** `ExitStack`, so O1 and O2 are measured on the **same** intervened
forward. `assert_read_sees_edit(...)` still refuses a *propagation* claim read at or below the edit;
reading O1 at the edited layer remains legitimate for O1 and is labelled non-evidence of
propagation.

---

## 6. Evidence

| check | result |
|---|---|
| `python3 scripts/dcs_ts_pr057_causal.py --self-test` | **73 checks, 0 FAILED** (was 46/0; **+27**, all Q9–Q13) |
| `python3 scripts/dcs_ts_pr057_causal.py --mutate` | **38/38 RED** (was 21/21; **+17**, all Q9–Q13) |
| `python3 scripts/dcs_ts_pr048_analysis.py --selftest` | **16/16 guards reachable** (unchanged) |
| A/B `make_intervention` vs HEAD, defaults | **84/84 hook constructions bit-identical** |
| A/B `pair_common` hooks vs HEAD | **300/300 hook applications bit-identical**, both `stats=None` **and** `stats` on |
| Frozen-probe arithmetic vs sklearn | `max|Δ| = 0.000e+00`, 3-class and 2-class |
| `pytest tests/` (102 files, 1704 tests) | see §7 |

The new mutations, each shown RED:

```
M22 pair_common: hook that never ran            M30 zero-norm base direction
M23 hook ran and edited nothing                 M31 two answers for the control base
M24 disabled bridge presented as a live arm     M32 '@base' on a non-control direction
M25 bridge over a hook that would not have      M33 10.2 primary over ZERO rows
    edited                                      M34 10.2 primary with no semantic_logodds
M26 edit below float32 resolution               M35 frozen probe with all-zero coefficients
M27 liveness record missing keys                M36 probe read at an ABSOLUTE index
M28 control matched to the WRONG base           M37 O1 over zero probe records
M29 control norm check binding zero layers      M38 probe records from two DIFFERENT probes
```

`mutate()`'s except-clauses were widened to include `SystemExit`, because `score_behavior`'s house
refusal idiom is `SystemExit` rather than an exception class of ours — without that, guards living
in that shared file could not be shown RED at all.

---

## 7. Test suite: pass / fail

`python -m pytest tests/ -q` — **1693 passed, 4 failed, 7 skipped** (726.74 s), on a run started
AFTER the last edit. An earlier full run, before the final three argparse guards, returned the
identical `4 failed, 1693 passed, 7 skipped` on the identical four test ids.

The four failures are **pre-existing and unrelated**, and that was verified rather than assumed:

- all four are in `tests/test_prompt_families_strict.py`, which drives
  `src/boombness/prompt_families.py` **as a subprocess**;
- `prompt_families.py`'s import graph is `common` + `demo_pools` — **none of the four files edited
  here is in it**;
- the failure is a refusal about **working-tree data**: 142 demo-pool sentences containing
  `carrot` / `was` incidentally, which breaks the exact-word-swap invariant. Those pool files are
  untracked in this shared tree and were not written by this work;
- **decisive check:** the same four tests were run in a **detached git worktree at clean HEAD
  (`df30feb1`)**, with none of these edits present, and produced the identical
  `4 failed, 1 passed` on the identical four ids:

```
FAILED tests/test_prompt_families_strict.py::test_violating_input_really_violates
FAILED tests/test_prompt_families_strict.py::test_strict_violation_writes_nothing
FAILED tests/test_prompt_families_strict.py::test_strict_violation_does_not_clobber_an_existing_bank
FAILED tests/test_prompt_families_strict.py::test_non_strict_violation_still_writes_both_files
```

Nothing was broken; nothing was fixed there either, because it is another writer's data state.

---

## 8. What existing behaviour was verified unchanged, and how

Every change is additive and default-off. The verification is measurement, not inspection.

1. **`make_intervention` builds the same hooks from the same directions.**
   `git show HEAD:src/boombness/score_behavior.py` was loaded side by side with the edited module
   and both were driven over **6 direction names × 2 modes × 2 seeds, plus a composed arm** with a
   stub `pc` that records every `(mode, layer, direction, alpha)`.
   → **84/84 constructions bit-identical** (`torch.equal`), and the new code passes **no unexpected
   kwargs** on the default path. `d_surface`, `d_naive`, `random`, `orthogonal`, `in_subspace`,
   `in_subspace_orth` all covered, `project_out` and `add`, single and composed.
   The baseline used was verified byte-identical to current `HEAD`.

2. **The `pair_common` hooks compute the same tensors.** HEAD's module and the edited module were
   driven over 20 random directions × 3 sequence lengths (1, 5, 17 — i.e. decode **and** prefill) ×
   3 positions × both hook factories.
   → **300/300 applications bit-identical**, and identical **again with `stats` switched on**: the
   instrumentation is numerically inert, not merely optional.

3. **The default control base has not moved.** `split_control_base("random") == ("random",
   "d_surface")` and `split_control_base("d_surface") == ("d_surface", "d_surface")`, asserted in
   the self-test. An existing caller passing `random:project_out:8-21:1.0` gets the direction it
   always got — confirmed numerically by (1).

4. **The new norm assertion cannot fire on existing behaviour.** All four house control makers
   (`random_control_direction`, `orthogonal_control_direction`, `in_subspace_control_direction`
   and its two fallbacks) renormalise **exactly** to `‖base‖`. Measured realised relative
   differences on a live payload: `0.0`, `0.0`, `0.0` (`random`), `8.4e-08` at one layer
   (`orthogonal`), `0.0` (`in_subspace`, `in_subspace_orth`) — against a `1e-4` bar.

5. **The semantic answer set is untouched with the Q9 flag off.** `extra_words == []` leaves
   `sem_variants` exactly `{"concept", "codeword"}`, so `string_option_readout`'s flattened variant
   list, its batching, its padding width, its `top1_id` row and every emitted number are
   unchanged. `option_mass` is still fed `rec["option_mass"]`; the core-pair mass is substituted
   **only** when the flag is on. New fields (`option_mass_core_pair`, and the aliases) are additive
   to `results.jsonl`; `RunDir.note()` is free-form `**kw`, and no consumer in the tree asserts an
   exact key set.

6. **`dcs_ts_pr048_analysis.py` reports the same numbers.** `return_estimator` defaults to `False`
   and is passed `True` at exactly **one** call site — the observed pass — where it returns the
   objects already fitted. No extra fit, no RNG consumption, no change to `pred/truth/doms`. The
   `FROZEN_PROBE` block only **adds** a key to `res`. `--selftest` still reports **16/16**.

7. **The analyzer's pre-existing guarantees hold.** All 46 original self-test checks and all 21
   original mutations still pass/RED, alongside the 27 and 17 new ones.

8. **`AllPositionProjectOutMultiLayer`, `AllPositionAdd`, `AttentionKnockout`,
   `ScopedAttentionKnockout`, `DonorPatch` and the whole knockout path are untouched** on their
   default paths; the multi-layer class gained an optional `stats_by_layer=None` and nothing else.
   Covered by the 1693 passing tests, which include `test_composed_knockout`,
   `test_scoped_knockout_wiring`, `test_composed_seed`, `test_knockout_heads`, `test_donor_patch`
   and `test_intervention_liveness`.

---

## 9. What remains open (NOT Q9–Q13)

These were already outstanding and are not touched by this work:

| id | state |
|---|---|
| **Q0** | PHASE 7 readout landed on all six banks — **still required before O2 exists at all** |
| **Q1** | validation-only power run — code path exists and is tested; needs the run |
| **Q2** | PR-053 TRAIN-ONLY `directions.pt` — **does not exist yet**; without it there is no `v_bomb_specific` to project out |
| **Q3 / Q12(a,b)** | cross-prompt donor (10.1) and `component_replace` (H2b). Designed and unit-tested; GPU wiring not built. **Not needed for the 10.2 primary (H2a)** — and under R-116 the 10.1 donor arm is **unconstructible on this bank** (knife installs in 0/113 domains), so Q3 should be closed as NOT APPLICABLE here rather than left as work to do. |
| **Q4b** | `src/boombness/pr057_run_causal.py`, the multi-arm runner — not written (outside the permitted file list). §5 gives the exact shape it must take. |
| **Q7** | smoke run — needs Q2 |
| Q8 | PR-056 fair-share coordination (non-blocking) |

**The frozen checklist was NOT amended, deliberately.** `configs/dcs_ts_pr057_phase9.json` is
`status: FROZEN` and is outside the file list this work was authorised to write. The design report
(§7) says Q9–Q13 "must be added to `pre_extraction_checklist` (as booleans, per C-086) before
`--for-extraction` can pass". They are **not** added here — editing a frozen preregistration to
record that its own blockers are cleared is exactly the move a frozen file exists to prevent, and it
needs an explicit, separate authorisation. Verified after all edits:
`scripts/dcs_ts_pr057_causal.py` still **refuses** by default ("Blocking checklist items
outstanding: Q0, Q1, Q2, Q3, Q4, Q5, Q6, Q7") and `--for-extraction` still **refuses** on Q5/Q6/Q7
and on `artifacts.analyzer_exists = false`. The design working is that these refusals persist until
someone updates the frozen file on purpose.

One observation outside the five, recorded rather than acted on: `score_behavior` has **no `--cells`
flag**, so cell C is selected via `--conditions natural_doublespeak`. On
`ts116m_button_bomb` that mapping is exactly 1:1 (`A/benign_literal`, `B/direct_harmful`,
`C/natural_doublespeak`, `E/concept_in_benign_ctx`, 5568 rows each), so the command in §10 binds the
intended population — but the design report's rule is "select on `cell`, never on `condition`"
(A-039), and the launcher does the latter. It is correct **on this bank** and should not be assumed
correct on another.

---

## 10. The exact sbatch command for the 10.2 primary arm

**Do not submit it yet.** Q0, Q1 and Q2 are still open; in particular `--fit-dir` below has no
directory to point at until PR-053 writes `directions.pt` (Q2). The command is exact in form; the
`<run>` placeholder is the one thing that must be filled in.

The 10.2 primary is **H2a**: projection-out of `v_bomb_specific` on the **bomb** banks. Both scope
levels are preregistered as distinct hypotheses and **both are launched together** — running S2
only after S1 fails is the rescue mandate 10.4 forbids.

```bash
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood

# 1. the argsfile MUST live on the shared filesystem -- /tmp is node-local and the job dies in 3s.
#    NO quote characters and NO spaces inside a value: BOOMB_ARGS is word-split (job 766661).
#    Note --pr057-edit-positions=-10 uses '=' : argparse accepts a bare -10 after a space but
#    rejects a comma list of negatives as an unknown option.
cat > outputs/boombness/pr057_h2a_s2_args.txt <<'EOF'
--bank data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl --query-kinds semantic_one_word --conditions natural_doublespeak --n-examples 4 --readout-ids whole_answer --attn-impl eager --max-new 8 --no-generate --fit-dir outputs/dcs_ts_pr053_diffmeans/<run> --intervene v_bomb_specific:project_out:7-14:1.0 --seed 20260907 --arm H2a_S2_bomb_projectout --tag pr057_h2a_s2_button_bomb --pr057-liveness-out auto --expect-n 1160
EOF

# 2. submit. BOOMB_EXPECT and BOOMB_REQUIRE_ARGS=1 are BOTH set: without them a mistyped variable
#    falls through to the runner's default script and exits COMPLETED 0:0 having run the wrong
#    thing (jobs 853040-853045, ~1.7 GPU-hours, and nothing caught it).
sbatch --export=ALL,BOOMB_SCRIPT=score_behavior.py,BOOMB_EXPECT=score_behavior.py,BOOMB_REQUIRE_ARGS=1,BOOMB_ARGSFILE=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/boombness/pr057_h2a_s2_args.txt \
       --time=06:00:00 \
       src/boombness/slurm/run_boombness.sh
```

**The S1 companion** — same file, two differences (block 9 only, and the single site at
`codeword_last`, rel_end −10):

```
... --intervene v_bomb_specific:project_out:9-9:1.0 --pr057-edit-positions=-10 --arm H2a_S1_bomb_projectout --tag pr057_h2a_s1_button_bomb ...
```

Notes that are part of the command, not commentary:

- `run_boombness.sh` already pins the six L40S nodes `n-801..n-805,t-806` via `#SBATCH --nodelist`.
  **Do not add `--exclude` on the sbatch line** — it nullifies that directive.
- Budget **≤ 2 concurrent model-loading jobs per node**; three on one node produced a 16× weight-load
  slowdown. So submit S1 and S2 together, then the controls, rather than all arms at once.
- `--mem=48G`, `--cpus-per-task=4` are the script's defaults and leave all 8 GPU-shares per node
  feasible. Do not raise them.
- Population bound by this command: **1160 rows over 116 domains**; 1130 after the three
  preregistered whole-population exclusions; the analyzer subsets to the **23 TEST domains = 230
  rows per arm**. `--expect-n 1160` makes a silently shrunken population fail loudly.
- `--no-generate` is set because O2 is the forward readout; drop it if O3 (the free one-word answer)
  is wanted, at the cost of generation time.
- The **controls** reuse the same file with `--intervene random@v_bomb_specific:project_out:7-14:1.0`
  (C1, five runs at five `--seed` values — the band is five draws, never one ticket),
  `orthogonal@v_bomb_specific:...` (C4), `v_remap:...` (C3), and
  `v_bomb_specific:project_out:7-14:1.0 --pr057-disable-hooks --pr057-liveness-out auto` (C5, the
  bridge, which must reproduce
  the untouched baseline byte-for-byte). C6 is the PHASE 7 baseline and needs no job.
- The **exploratory 10.1** arm is **not launchable on this bank and should not be submitted at
  all.** R-116 puts knife installation at **0/113 domains (0/23 TEST)**, so the donor population is
  empty; its null would be **CANNOT ANSWER by construction** (C-112). If it is ever run on a bank
  where the source concept does install, it additionally needs `--semantic-extra-words knife,gun`.

---

## 11. Answers to the four closing questions

**CLEARED: Q9, Q10, Q11, Q12, Q13** — all five.

- **Q9** — `semantic_logodds` (= `logp_concept − logp_codeword`, with `option_mass_core_pair` as the
  engagement gate) is confirmed sufficient for the 10.2 primary and is implemented as
  `o2_projection_out_from_rows()`, which ships its rival-cause gates as data and refuses to be
  reported alone. The optional `--semantic-extra-words` flag adds explicit candidate words
  (default-off) so `logP(knife)` is **expressible** — which under R-116 is what lets a cross-concept
  null be *shown* rather than assumed, since knife installs in 0/113 domains and the 10.1 arm has no
  population to be "measurable" on; the one-pair-per-bank assertion is kept, not relaxed.
- **Q10** — the fitted coefficients, scaler statistics, selected `(layer, C)`, train domains and a
  content `sha256` are persisted as `res["FROZEN_PROBE"]`, self-verified against the estimator on
  every test row, and loadable by `load_frozen_probe(path, expect_sha=…)`. No reported number
  changed.
- **Q11** — wired, not merely documented: `ProbeReadCapture` captures O1 read-only inside the
  intervened forward, in the same `ExitStack` as the edit hooks, writing `PR057_PROBE.jsonl`.
- **Q12** — single-position scoping wired (`edit_positions` / `--pr057-edit-positions`), the
  disabled-hook bridge is a real code path (`pair_common.DisabledHookBridge` /
  `--pr057-disable-hooks`), and every hook now records the full liveness set with a gate that
  **detects** a deliberately disabled hook instead of tolerating it.
- **Q13** — the control's base direction travels with the arm, is derived from the live direction
  object, is norm-asserted at hook-install time, and is echoed into `PR057_ARM.json`. Default
  behaviour is unchanged and that was proved by an 84-case bit-identical A/B against HEAD.

**REMAIN (none of them Q9–Q13):** Q0, Q1, Q2, Q4b, Q7 — and Q3 / Q12(a,b), the 10.1-donor and H2b
paths, neither required for the 10.2 primary; under R-116 the 10.1 arm is unconstructible on this
bank and Q3 is better closed as NOT APPLICABLE than carried as outstanding work. **Q2 is the immediate
blocker**: there is no `v_bomb_specific` on disk to project out.

**The launch command** is §10. **What was verified unchanged, and how**, is §8.

---

## 12. Q2 — `v_bomb_specific` on disk (**CLEARED**) — appended 2026-09-07

> The closing summary above names Q2 as *"the immediate blocker: there is no `v_bomb_specific` on
> disk to project out."* It now exists. **Nothing was run on a GPU. No SLURM job was submitted. No
> commit was made.** Files written by this section: `scripts/dcs_ts_export_directions.py` and
> `outputs/dcs_ts/directions_pr053/` — nothing else was touched.

### 12.1 The artifact

| | |
|---|---|
| `--fit-dir` argument | **`outputs/dcs_ts/directions_pr053`** |
| payload | `directions_fit_dev.pt` (1 657 661 B) — the name `score_behavior.py:2082` tries **first** |
| payload `sha256` | `0d59b25561d220a58bac9ebe08b39690c5bdb9f8b613001dd3edba3a0dac5df7` |
| content `sha256` of the arrays | `8df3fdec93c4c7b73cf38178612cc365608ab9a9f04351b1dadf0fadbe56a435` |
| provenance / verification records | `MANIFEST.json`, `VERIFY.json`, `MUTATIONS.json` in the same directory |
| produced by | `scripts/dcs_ts_export_directions.py --export [--verify] [--mutate]` |

The format was **derived from the consumer, not guessed**. `score_behavior.py:2081-2085` joins
`--fit-dir` with `directions_fit_dev.pt` (falling back to `directions_fit_heldout.pt`) and
`torch.load`s it; `make_intervention` then indexes `payload[<name>][<int layer>] -> Tensor[H]`,
`payload["gap"][<name>][<layer>]` for `mode=add`, `payload["cell_means"][<cell>][<layer>]` for the
realised-dose records, and — since **Q13**, §1 above — `payload[<control base>]` for a norm-matched
control's base axis. The payload carries exactly those keys.

> ⚠ **One naming discrepancy, recorded rather than silently resolved.**
> `configs/dcs_ts_pr057_phase9.json` `directions.artifact.path` says
> `outputs/dcs_ts_pr053_diffmeans/<run>/directions.pt`. That path can never be loaded: the
> **loader**, not the preregistration, decides the filename, and it only ever looks for
> `directions_fit_dev.pt` / `directions_fit_heldout.pt` inside `--fit-dir`. The file is therefore
> named for the loader. The prereg's `pin_rule` is honoured instead in the way it asks for — the
> `sha256` is computed at write time and is recoverable from the artifact — and the config is
> FROZEN, so it was not edited.

Directions exported (per layer, **L6–14**, `hidden = 4096`, stored **unit**, raw diff-of-means norm
kept in `gap` because `make_intervention` doses `add` in gap units):

| key | definition | ‖raw‖ L6 → L14 |
|---|---|---|
| `v_bomb_specific` | `v_bomb − mean(v_knife, v_gun)` — **the PHASE 9 arm** | 0.955 1.077 1.443 1.605 1.843 1.906 1.855 2.162 2.338 |
| `v_remap` | `v_bomb`, the raw axis — **control C3** | 1.013 1.137 1.522 1.653 1.874 2.094 2.097 2.490 2.618 |
| `v_bomb` `v_knife` `v_gun` | `mean_TRAIN[ h(C_c) − h(A_shared) ]`, paired on `family_id` | knife 1.380 … 2.931; gun 1.116 … 2.519 |
| `v_knife_specific` | `v_knife − mean(v_bomb, v_gun)` — named by `phase9.json` for the H3 replacement arm | 0.803 0.912 1.241 1.391 1.569 1.603 1.545 1.784 1.937 |

Also recorded in `meta`: the 67 fit domains **by name**, the validation and test domain lists, the
three exclusions, the layer list, the split-manifest `sha16`, the six `bank_rows_sha16` from
`configs/dcs_ts_pr048.json`, the three extraction run directories, the read site, the model id and
revision, the per-layer norms, the `sha256` of `configs/dcs_ts_pr053.json`, and the content `sha256`
of the arrays. **PHASE 9 can prove which axis it projected out**: the content sha is recomputable
from the payload alone and is re-derived by every `--verify`.

`cell_means` (cells `A` and `C`, 670 TRAIN rows each, development codeword's **bomb** bank) is a
**diagnostic** block only — `score_behavior` reads it for `cellmean_dose` /
`cell_residual_frac_removed`, never for the axis. Note that with two cells the centred spread is
**rank 1**, so `cellmean_dose` returns 1.0000 for `v_remap` *by construction* and 0.14–0.17 for
`v_bomb_specific`; the informative realised-dose number for this phase is
`cell_residual_frac_removed` (at α=1: cell C 0.094 at L9, 0.206 at L12).

### 12.2 TRAIN ONLY — the property the artifact exists to guarantee

The estimator is **imported** from `scripts/dcs_ts_pr053_diffmeans.py` (`build_arm`, `verify_run`,
`excluded_domains`, `load_split`, `_nonempty`) and `scripts/dcs_diffmeans_directions.py` (`auroc`,
`unit`, `project`, `band`, `std_diff`). Nothing is reimplemented; `fit_directions()` is the same
`mean over TRAIN domains` that `evaluate()` computes as `U[:,0].mean(axis=0)` / `W[:,0].mean(axis=0)`.

The fit set is asserted **equal to** the frozen manifest's train split — not merely disjoint from
test — so a population that silently grew *or shrank* is a refusal:

```
[GREEN] fit domain set is NON-EMPTY
[GREEN] fit domain set == the frozen manifest's TRAIN split, exactly   n_fit=67 n_train=67 extra=[] missing=[]
[GREEN] fit domain set is DISJOINT from validation / from test
[GREEN] the three whole-population exclusions are absent from the fit set
        (restaurant_kitchen, school_campus, subway_station)
```

Rows for the validation and test domains **are** loaded — the reproduction below needs them — but
they enter no direction, and the domain-set checks above are what proves it rather than the
loading pattern.

### 12.3 It reproduces `R-111` — exactly

`--verify` reloads the written `.pt` from disk and re-scores the **23 untouched TEST domains**:
per-domain, per-layer AUROC of `proj(h, v_bomb_specific)` separating `C_bomb` from
{`C_knife`, `C_gun`}, `button`, `semantic_one_word`, `n_examples = 4`.

| quantity | published (`R-111`, `reports/DCS_TS_PR053_DIFFMEANS.md` §4/§4.1) | recomputed from the artifact |
|---|---|---|
| band-mean AUROC, L6–14 | **0.9764** | **0.976401** ✅ |
| 95 % CI over domains | [0.9622, 0.9906] | [0.962219, 0.990583] ✅ |
| between-domain SD | 0.0347 | 0.034703 ✅ |
| domains above chance | 23 / 23 | 23 / 23 ✅ |
| per-layer L6…L14 | 0.9639 0.9687 0.9735 0.9746 0.9793 0.9809 0.9824 0.9830 0.9813 | identical to 4 dp ✅ |
| Cohen's *d*, band | 2.81 → 3.15 | 2.806 → 3.148 ✅ |

All **25 checks GREEN** (`VERIFY.json`, verdict `GREEN`). The export path refuses to write at all if
any check is RED — a direction that does not reproduce the result it is named after is worse than no
direction.

### 12.4 The mutation harness — **20 mutations, 20 turned a check RED**

`--mutate` round-trips each mutated payload through `torch.save`/`torch.load` first, so every case
is judged on the object PHASE 9 would actually see (`MUTATIONS.json`):

| # | mutation | red |
|---|---|---|
| 1–3 | fit on TRAIN+TEST (leakage) / on VALIDATION / on TRAIN−1 domain | 3 / 3 / 2 |
| 4 | `meta.fit_domains` rewritten to the TEST domains | 3 |
| 5–6 | `v_bomb_specific` := raw `v_bomb` (no residualisation) / coefficient 1.0 instead of 0.5 | 2 / 2 |
| 7 | `v_remap` (control **C3**) pointed at `v_bomb_specific` | 2 |
| 8–10 | one layer perturbed by 1e-4 / stored at 2× unit norm / **zeroed** (`project_out` a no-op) | 2 / 3 / 4 |
| 11 | `v_bomb_specific` missing layer 14 | 3 |
| 12–14 | `content_sha256` / `bank_rows_sha16` / `split_manifest_sha16` disagree with their source | 1 / 1 / 1 |
| 15 | payload layer list truncated to L6–12 | 5 |
| 16–18 | scored with the sign-flipped axis / with `v_bomb` (contrast B) / with `v_knife_specific` | 5 / 6 / 6 |
| 19 | reproduction scored on VALIDATION rows instead of TEST | 5 |
| 20 | layers rotated by one (an off-by-one layer convention) | 7 |

**20/20 caught.** `--selftest` (no data) is 16/16 and covers the algebra, the zero-bind refusals,
and that a merely-close AUROC of 0.9700 does **not** pass as 0.9764.

Every bind fails loudly on an empty set: a zero-domain fit, a duplicated fit domain, a zero-row
domain, a zero-domain reproduction, a zero-norm direction and a zero-row `cell_means` each raise
`PreregError` rather than returning a number (the C-074 / A-039 shape).

### 12.5 What the direction means under `R-116` — flagged, not changed

`v_bomb_specific` is exported **exactly as `PR-053` froze it and exactly as `R-111` measured it**:
`v_bomb − mean(v_knife, v_gun)`. The definition was not touched. But `R-116` measured that only
**bomb** installs — bomb 0.619 of 113 domains, **knife 0.000, gun 0.009** — which is why `C-112`
demoted the knife→bomb patch arm and made projection-out on BOMB prompts the primary causal test.
The consequence for *this* axis, stated plainly:

- The two **subtracted** terms, `v_knife` and `v_gun`, are differences `h(C_c) − h(A_shared)` over
  demonstration sets that **install nothing**. They are not "the knife concept" and "the gun
  concept"; they are whatever a non-installing harm demonstration does to the codeword's
  representation — register, lexical content, demonstration length, harm-topic salience.
- So `v_bomb_specific` is best read as **the bomb remapping direction with the non-installing
  common-mode of two other harm-demonstration sets removed**. That subtraction is doing real work:
  `cos(v_bomb_specific, v_remap)` is only **0.22 → 0.44** across L6–14, so it is not a rescaled
  `v_bomb`. And it evidently isolates something that discriminates bomb from the negatives at
  AUROC 0.976.
- What it does **not** license: reading a projection-out null (or effect) as being about *concept
  identity* alone. `R-111`'s own question **D failed** — the residual axis still carries generic
  remapping at 0.8236 on `C_bomb` vs `A` — and `R-116` adds that the residualisation was performed
  against two contrasts with no installed concept in them. A movement under projection-out is
  evidence that *this axis* is causally used; attributing it specifically to "the bomb concept
  rather than remapping" is **not** supported by this artifact, and the same caveat is written into
  the payload as `meta.interpretation_warning` so it travels with the file.
- Control **C3** (`v_remap`) is likewise **not** an orthogonal control: `cos ≈ 0.22–0.44` with the
  arm. `phase9.json` already says so in `controls.arms[2]._honest_label`; the exported norms make
  the overlap checkable rather than assumed.

### 12.6 Consumer smoke test (CPU, no model)

Run against the written payload with the real house code, not a re-typed copy:
`split_control_base("random@v_bomb_specific")` → `('random', 'v_bomb_specific')`;
`signals.random_control_direction` / `orthogonal_control_direction` derived per layer from
`payload["v_bomb_specific"]` and passed to `assert_control_norm_matched` → **8/8 layers**, max
relative norm difference `1.2e-07`, orthogonal control `|cos| ≤ 9.2e-09`;
`signals.in_subspace_control_direction` builds from `cell_means`; `insubspace_null_test.cellmean_dose`
and `score_behavior.cell_residual_frac_removed` both return numbers. The hook itself needs a GPU and
was **not** run here.

### 12.7 The command PHASE 9 should use

```
--fit-dir outputs/dcs_ts/directions_pr053
```

i.e. §10's primary-arm launch line with
`--intervene 'v_bomb_specific:project_out:7-14:1.0' --fit-dir outputs/dcs_ts/directions_pr053`,
and its C3 / C1 / C4 controls as `v_remap:project_out:…`, `random@v_bomb_specific:project_out:…`
and `orthogonal@v_bomb_specific:project_out:…` — the `@base` form being what §1 (Q13) added so a
control is norm-matched to the axis the arm actually edits.

**Q2 is CLEARED.** Remaining, unchanged: Q0, Q1, Q4b, Q7 (and Q3 / Q12(a,b), NOT APPLICABLE on this
bank under R-116).
