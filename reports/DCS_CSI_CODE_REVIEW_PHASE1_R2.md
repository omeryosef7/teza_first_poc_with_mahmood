# DCS-CSI Phase-1 adversarial code review — ROUND 2

Scope: only the code written *after* `reports/DCS_CSI_CODE_REVIEW_PHASE1.md`.
`score_behavior.py` (`_rescue_row_fields` + its four call sites, `_rpos_row`,
`make_rescue_basis_loader`, the post-`parse_args` guards), `donor_patch.py`
(`refuse_degenerate`, the modified prefill/decode guard), `scripts/dcs_csi_subspace_analyze.py`
(whole file), `scripts/dcs_csi_rederive_patch.py` (`row_file`, `slurm_node_for_job`,
`--tag-prefix`), `scripts/dcs_cont_layerpos_map.py` (`allow_query_kinds`),
`scripts/dcs_csi_axis.py` (M1/M4 additions).

**Bottom line.** The round-1 MAJORs that were actioned are genuinely fixed and I verified the
fixes numerically (M2/M3 now `raise`, m2's decode guard now fires, `refuse_degenerate` refuses
before any write, the M1/M4 provenance checks bind on the real corpus). The two stale-cell
suspicions in the brief are **refuted** — `_rescue_ctx` and `_rpos_row` are both reset
unconditionally at the top of every row iteration. `holm()` is **correct**. The `--tag-prefix`
`.replace` is **safe**.

What is wrong is not in the intervention primitive. It is in the *analyser's* enforcement ring:
**the `dcs_csi_subspace_analyze.py` VOID block does not verify arm identity at all.** I built
synthetic arm sets in which (a) the identity control never fired, and (b) the candidate and its
comparator were the same intervention — and in both cases the analyser emitted `VOID: []`, all
three gates `true`, and a final VERDICT line. Plus one arithmetic defect that produces a wrong
number the first time the new `--option-mass-floor` sensitivity arm is run.

Scratch scripts: `…/scratchpad/r2a.py` (donor_patch behavioural tests), `r2b.py` / `r2c.py`
(synthetic-arm analyser harnesses), plus the inline snippets quoted below.

---

## BLOCKER

### B1. `--option-mass-floor` drops rows **per arm independently**, so the paired domain contrast compares different populations
`scripts/dcs_csi_subspace_analyze.py:43-79` (`installation_with_option_mass`) and `:91-105`
(`arm_domain_means`).

Each arm's `y_install` map is built by dropping every row whose `option_mass < floor`, arm by arm.
`arm_domain_means` then averages whatever survives *in that arm* into a per-domain mean, and
`main()` intersects only the **domains** (`:229`), never the **slots**. But `option_mass` is an
outcome of the intervention — the knockout raises it sharply — so the floor deletes a large,
arm-dependent, outcome-correlated slice of the population, and the two domain means being
subtracted are then means over *different sets of slots*.

Measured on the real Phase-1 train arms (`csi1_button_train_{BASE,KO,KO_FULL}`, 670 rows each):

```
floor 0.00   rows kept  BASE 670  KO 670  KO_FULL 670
floor 0.05   rows kept  BASE 586  KO 658  KO_FULL 649
floor 0.20   rows kept  BASE 435  KO 582  KO_FULL 549
```

BASE loses 235 rows at floor 0.2 while KO loses 88. The resulting contrasts, as implemented vs.
with the surviving-key set held identical across arms (the only honest comparison):

```
floor   KO-BASE as implemented   KO-BASE key-intersected   FULL-KO impl.   FULL-KO intersected
0.00          -0.2070                  -0.2070               +0.0706            +0.0706
0.05          -0.2448                  -0.2114               +0.0747            +0.0738
0.20          -0.3297                  -0.2215               +0.0816*          +0.0816
```
(`*` as-implemented FULL-KO at 0.20 is +0.0873; intersected +0.0816.)

At floor 0.2 the manipulation effect is inflated by **49%** (−0.330 vs −0.221) purely by
differential row deletion. The recovery fraction — numerator `CAND−KO`, denominator `FULL−KO`,
both divided through by a `KO−BASE` that moved 49% — is wrong by a correspondingly arbitrary
amount. Nothing in the VOID list detects it: row counts are checked against `--expect-n` on the
*raw* `results.jsonl`, not on the post-floor population, and
`rows_dropped_by_option_mass_floor` is recorded but never compared across arms or gated.

The docstring's own defence ("the primary contrast is computed on ALL rows and RE-computed above a
floor, and both are reported") is exactly the claim that fails: the two are not the same estimand.

*Wrong number:* "the P1-f sensitivity confirms the primary" (or contradicts it) when the only
thing the floor changed was which slots each arm was allowed to contribute.

*How verified:* `scratchpad` inline script over the three real run dirs; numbers above.

*Fix:* compute the surviving key set for **every** arm first, intersect it, and build all domain
means from that single common key set. Record `n_keys_common` and refuse if the intersection is
below a stated fraction of the floor-0 population. Add a VOID on
`max(rows_dropped) - min(rows_dropped) > 0` unless the intersection is used.

---

## MAJOR

### M1. The identity control `KO_SELF` is **exempted** from the rescue-liveness VOID, so the gate it anchors cannot fail
`scripts/dcs_csi_subspace_analyze.py:262-264`:
```python
if arm.startswith("KO_") and arm != a.self_arm:
    if m["rescue_fired"] != a.expect_n:
        void.append(...)
```
`KO_SELF` is the one arm the check is skipped for. `KO_SELF` is also the arm whose *null* is the
`identity_check` gate — "the patch is writing what it read, so a rescue number is interpretable"
(`--self-inert-tol` help text). A self-patch that never fires is byte-identical to `KO`, produces
`|KO_SELF − KO| = 0.0`, and passes the gate perfectly. This is the repo's own "a control that
cannot fail" pattern, in the exact place `assert_control_norm_matched` exists to prevent.

*Verified* (`scratchpad/r2c.py`, synthetic 6-arm set, `KO_SELF` rows carrying
`rescue_liveness.fired = False` and `y` copied from `KO`):
```
VOID: []
gates: {'manipulation_check': True, 'identity_check': True, 'instrument_capable': True}
KO_SELF rescue_fired: 0 of 100
identity contrast point: 0.0
VERDICT: PRIMARY PASSES on split=train -- candidate beats its norm-matched comparator
```
A dead identity control certified the instrument and the run published a PASS.

*Fix:* drop the `and arm != a.self_arm` exemption — `KO_SELF` fires a `DonorPatch` like every other
rescued arm and must be held to the same liveness bar. If the exemption exists because `KO_SELF`
rows legitimately record a different liveness shape, check `rescue_liveness.fired` explicitly for
it instead of skipping it.

### M2. The analyser has **no arm-identity table**: candidate and comparator may be the same intervention, or carry no basis at all
`scripts/dcs_csi_subspace_analyze.py:233-289`. The VOID block checks bank, exclusion file,
`attn_impl`, `dtype`, row count, hook liveness, model revision, prefill/decode edits, rescue-fired
count, rescue layer, position count and test leakage. It never checks:

* that `meta[candidate_arm]["basis_keys"] != meta[comparator_arm]["basis_keys"]`;
* that the candidate arm used a basis **at all** (`rescue_basis` may be `None`);
* `intervene` (so one KO arm could carry a different knockout band than another);
* `rescue_donor`, `rescue_positions`, `rescue_n_positions` (the rows carry `rescue_positions` but
  `row_meta` never reads it — `demo` vs `query` spans of the same size would pass the position-count
  VOID silently).

Compare `dcs_csi_rederive_patch.ARM_SPEC` (`:320-337`), which does exactly this job for its four
arms and refuses on any mismatch. The subspace analyser — the one whose PRIMARY *is* "arms differ
only in the intervention" — has no equivalent.

*Verified* (`scratchpad/r2b.py`): a synthetic set in which `KO_AXIS` and `KO_ORTH` both carry
`rescue_basis_key = "cand_rank1"` and `rescue_basis = None`:
```
VOID: []
gates: {'manipulation_check': True, 'identity_check': True, 'instrument_capable': True}
arm_meta KO_AXIS  basis_keys ['cand_rank1']  rescue_basis None
arm_meta KO_ORTH  basis_keys ['cand_rank1']  rescue_basis None   norm_match ['cand_rank1']
in_sample: {}                     # both arms silently absent
VERDICT: PRIMARY DOES NOT PASS on split=train
```
A "negative result" from a contrast between an arm and itself.

*Fix:* add an ARM_SPEC-style table: candidate/comparator must name **different** `rescue_basis_key`
values; every rescued arm must carry a non-null `rescue_basis` and one identical `rescue_basis`
basename; `intervene`, `rescue_donor`, `rescue_positions`, `rescue_n_positions` must be read from
`config.json` and must agree across every arm that is not the one deliberately varied.

### M3. `--rescue-basis-key` without `--rescue-basis` is not refused — the arm silently runs the **whole-state** rescue under the subspace label
`src/boombness/score_behavior.py:2415-2420` (guards) and `:3686-3692` (branch).

```python
if args.rescue_basis and args.rescue_layer is None:      raise SystemExit(...)
if args.rescue_norm_match_key and not args.rescue_basis: raise SystemExit(...)
```
There is no guard for `--rescue-basis-key` set while `--rescue-basis` is empty. In that case
`if args.rescue_basis:` (`:3686`) is False and the row gets a full `DonorPatch` — the positive
control — while `_rescue_row_fields` (`:3108-3109`) writes
`"rescue_basis": None, "rescue_basis_key": "cand_rank1"` onto every row. The `--rescue-basis-key`
help text's own promise ("an unknown key silently falling back to any default would make two arms
that differ only by a typo produce the same numbers under different labels") is defeated one level
up: no key is looked up at all.

This is not hypothetical in this repo: `feedback_sbatch_export_comma` records `--export` values
silently arriving empty. An unset shell variable in the `KO_AXIS` sbatch line yields exactly this
state, and per M2 the analyser then reports the *whole-state* recovery as the subspace candidate's.
Note the asymmetry that makes it plausible: the `KO_ORTH` arm passes `--rescue-norm-match-key` and
*would* be caught by the `:2419` guard; the `KO_AXIS` arm does not and would not.

*Fix:* `if args.rescue_basis_key and not args.rescue_basis: raise SystemExit(...)`, next to the two
existing guards.

### M4. `slurm_node_for_job` makes the GPU-architecture VOID tautological
`scripts/dcs_csi_rederive_patch.py:257-281`, used at `:370`, checked at `:606-611`.

```python
hw[arm] = (slurm_node_for_job(a.slurm_job) if a.slurm_job else slurm_node_for_tag(_tag))
...
hw_verdict = ("SAME ARCHITECTURE" if len({g for g in gpus.values() if g}) == 1
              and all(gpus.values()) else "MIXED OR UNKNOWN -- NOT COMPARABLE")
```
With `--slurm-job`, the *same* `job` string is passed for every arm, so `gpus` is a constant
dict by construction and `hw_verdict` is `SAME ARCHITECTURE` whenever `sacct`+`scontrol` succeed —
independently of where the arms actually ran. Nothing cross-checks that the declared job produced
those run dirs (no job id is recorded in `config.json` or `DONE.json`; I checked both). The check
whose docstring says "compared generation arms that ran on different GPU ARCHITECTURES are not
comparable" is now satisfied by operator assertion, and the replacement was introduced precisely to
stop a run being VOIDed — i.e. to make a failing check pass.

*Wrong number:* a greedy-decoding generation contrast pooled across an a5000 arm and an l40s arm,
certified `SAME ARCHITECTURE`.

*Fix:* persist `SLURM_JOB_ID` into each run's `config.json` at score time, and have
`slurm_node_for_job` refuse unless every arm's recorded job id equals the declared one. Until then,
at minimum record `"source": "declared --slurm-job"` into `hw_verdict` itself
(`"SAME ARCHITECTURE (DECLARED, NOT MEASURED)"`) so no reader quotes it as evidence.

---

## MINOR

### m1. The duplicate-key refusal stops firing once a row is dropped by the floor
`dcs_csi_subspace_analyze.py:71-76`. The `if k in out: raise` happens **before** the
`if om < floor: continue`, so a dropped row leaves no trace and a second row bearing the same key
is silently accepted.

*Verified* (two rows, same `(domain, family_slot)`, `option_mass` 0.001 and 0.9):
```
floor 0.00 -> REFUSED: installation key ('dA', 'dev|slot0|...') binds two rows
floor 0.01 -> ({('dA','dev|slot0|...'): 0.00739}, 1)      # silently accepted
```
The docstring claims the refusal is "kept identical to `lpm.load_installation`"; it is not, for any
floor > 0 — and `_assert_matches_loader` (which would catch it) is only called when floor == 0
(`:96-98`), so the sensitivity path has no backstop at all. Currently latent: I measured 0
duplicate keys across all 670 cell-C rows of every `csi1_button_train_*` arm.
*Fix:* record every seen key in a separate set before the floor test and refuse on that set.

### m2. `_assert_matches_loader` is skipped on the sensitivity path
`:91-99`. Confirmed: the equality-with-the-frozen-loader assertion runs only in the `else` branch.
Beyond m1 this also means `n_rows` changes meaning between the two branches — `len(inst)` (deduped
keys) at floor > 0 vs `lpm.load_installation`'s `n_seen` (rows) at floor 0 — and both are written
to the artifact as `installation_rows_all_splits`.
*Fix:* call `_assert_matches_loader` unconditionally; it is cheap and it is the only thing binding
the two arms to one definition.

### m3. The in-sample detector degrades to `None` in silence, and the fingerprint it records is never compared
`:295-311`. Three separate soft failures, none of which appends to `void` or even prints:
* an arm with no `rescue_basis_meta` is simply **absent** from `in_sample` (demonstrated in M2's
  output: `in_sample: {}`);
* the fit-domain list is read from `REPO/configs/<basename>.json` — if the axis `.pt` lived
  anywhere but `configs/`, or the sidecar is a different vintage than the `.pt` the run loaded,
  `fit_doms` is `None`, `n_overlap` is `None` and `evaluation_is_in_sample` is `None`;
* `bmeta["fit_domains_sha16"]` — the row-portable fingerprint that `dcs_csi_axis.py:284-287` was
  added to provide for exactly this — is copied into the output and **never compared** to
  `sha256("|".join(sorted(fit_doms)))[:16]` from the sidecar. This is the repo's
  "threshold published but never enforced" shape, one line away from being closed.

Also: `evaluation_is_in_sample` never enters the VERDICT string. The default `--split train`
(`:191`) is 100% in-sample for the shipped button axis — `fit_population.n_domains = 67` and the
train split has 67 domains — yet the VERDICT reads "PRIMARY PASSES on split=train" with no
qualifier. That is the line that gets quoted.

### m4. `specificity_all_controls_rejected` is computed and never gated
`:372-373`. The Holm-corrected specificity result is written to the JSON but plays no part in
`out["VERDICT"]`, which depends only on `PRIMARY_candidate_minus_comparator`. A run can report
`PRIMARY PASSES` beside `specificity_all_controls_rejected: false`.

### m5. `ActivationCapture` did not get the guard both patchers got
`donor_patch.py:68` is still `if hidden.shape[1] <= max(self.positions, default=-1)`, while both
patchers now also short-circuit on `hidden.shape[1] == 1` (`:126`, `:230`). With
`positions == [0]`, a length-1 forward under the capture hook would be **captured** and overwrite
`self.acts` with a decode-step activation. Latent — the capture runs under exactly one explicit
forward — but the whole point of factoring `assert_token_identity` was that three copies of a guard
is how one of them loses it, and this is the third copy.

### m6. The decode guard is a silent no-op, not a refusal
`donor_patch.py:126`, `:230`. Verified on the fake-model harness (`scratchpad/r2a.py`):
```
DonorPatch n_applied on a genuine 1-token PREFILL: 0
SubspaceDonorPatch n_applied on a length-1 forward, positions=[0]: 0
```
So m2 from round 1 is fixed. The residual: a legitimate 1-token prefill is now *skipped* rather
than refused. It cannot occur here — every prompt goes through the chat template and ends
`…<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n` (verified on 40 real bank rows) —
and `liveness().fired == False` would surface it downstream. Prefer the guard the round-1 report
suggested: record `seq_len_at_capture` on the `DonorBlock` and refuse a mismatch, rather than
inferring "decode" from a length.

### m7. `refuse_degenerate` surfaces as geometry-correlated silent row loss
`donor_patch.py:255-267` raises `ValueError` inside the hook; `score_behavior.py:4011-4013` is a
blanket `except Exception: ledger.fail(...); continue` around the whole row body. So a partially
degenerate control arm does not abort — it silently deletes exactly the rows whose delta lies
outside the control subspace, i.e. a non-random, geometry-correlated subset. Verified that the
raise happens before any write (`n_applied = 0`, `_dose = None`, `fired = False`), so there is no
partial-write hazard, and `strict_run_dir` + the analyser's `n_rows != expect_n` VOID both catch the
shortfall. Worth an explicit, named abort so the operator sees *why* rather than a ledger histogram.

### m8. The axis's codeword check silently passes on a corpus with no `target_surface`
`dcs_csi_axis.py:248-252`: `if cws_C and cws_C != {a.codeword}`. If no cell-C row carries
`target_surface`, `cws_C` is empty and the check binds nothing. Presently sound — I confirmed the
real behavioural corpus carries `('C','button') × 930` with zero missing keys — but the empty case
should refuse ("cannot verify") rather than pass.

### m9. `bank_sha16` travels all the way to the row and is never used
`score_behavior.py:2063` puts `bank_sha16` into `rescue_basis_meta`; the M3 refusal at `:2053-2058`
instead tests `codeword in args.bank`, a substring test on a **path**. The rows already carry
`bank_file_sha16`; comparing the two shas is strictly stronger and is already plumbed.

### m10. The realised rescue positions are not persisted
`score_behavior.py:3669` computes `_rpos` (and, under `--rescue-n-positions`, a prompt_id-seeded
random draw of it) and publishes it into `_rpos_row` **only to take its length** —
`"n_rescue_positions": len(rpos)`. The row field named `rescue_positions` holds the *mode string*
(`"query"`), not the indices. Ten lines further down, `control_draw` is persisted with the comment
"THE DRAW IS PERSISTED, not only seeded … auditable after the fact rather than only reproducible in
principle". Given this repo's twice-recorded absolute-position-index bug class, the rescue's own
draw deserves the same treatment. (Measured: `n_rescue_positions == 28` on 670/670 rows, so the
count-based VOID has essentially no discriminating power.)

### m11. Generation path emits the rescue keys only under `if _wants_knockout`
`score_behavior.py:3859` gates the `_rescue_row_fields` call at `:3888`, whereas the three readout
call sites (`:3738`, `:3763`, `:3775`) are unconditional. `_rescue_row_fields`'s own docstring says
the keys are emitted "even on non-rescue arms (as None) so every row in a run set shares one
schema"; on `gens.jsonl` that holds only for knockout arms. Inert for Phase 1 (readout-only runs)
but it is the same one-of-two-paths shape the function was written to close.

### m12. `domains_sha16` fingerprints the *intended* fit population, not the realised one
`dcs_csi_axis.py:281-287` hashes `fit_doms` (`corpus_doms & TR`), while `n_fit_domains`
(`:308`) is `len(doms)` from `build()` — the domains that actually contributed rows after the two
uncounted joins flagged as round-1 m3. The two can differ and the fingerprint claims to be "the
exact fit population".

### m13. Two different GPU regexes for the same field
`dcs_csi_rederive_patch.py:277` uses `Gres=gpu:([a-z0-9_]+):`, `:312` uses `([a-z0-9]+)`. The same
node can yield two different `gpu` strings depending on which code path read it, and those strings
are compared for equality at `:608`.

---

## NIT

* `installation_with_option_mass` raises on a missing `option_mass` even at `floor == 0.0`, where
  the field is unused — so `_assert_matches_loader`, and therefore the whole *primary* path,
  refuses any run predating the field.
* `dcs_csi_subspace_analyze.py:265-266`: `if …: pass  # reported below once` — a computed condition
  with an empty body. It *is* correctly reported at `:268-269`, but an empty `if` inside a VOID
  loop is one edit away from being the real thing.
* `:238` `a.codeword not in (list(banks)[0] or "")` is a substring test on a path; see m9.
* `holm()` uses `adj < 0.05` rather than `<=`. Conservative, so not a defect.
* `contrast()` reuses one bootstrap seed (`20260915`) for every contrast, which correlates the
  resampling across contrasts. Harmless for the marginal CIs reported; would matter if anyone ever
  differenced two of them.
* `make_rescue_basis_loader` still validates lazily (round-1 m6, not actioned): the now-fatal M2/M3
  refusals fire on the first row, after weight loading.

---

## CHECKED AND FOUND CORRECT

Everything below was checked, and where a numeric claim is made it was verified by running code.

**The two stale-cell suspicions — both REFUTED.**

1. `_rescue_ctx` and `_rpos_row` are reset on **every** row, unconditionally.
   `score_behavior.py:3646-3647` sit at indent 12, inside the `try:` at `:3553` (indent 8), which is
   the immediate body of the row loop `for i, row in enumerate(rows):` at `:3457` (indent 4). I
   enumerated every `for`/`while` at a shallower indent between `:3457` and `:3646` — there is none,
   so there is no inner loop that could execute the readout twice off one assignment. Both
   assignments precede every `continue` inside the rescue block, and every `continue` skips the row
   entirely (no row is logged), so no later row can read a previous row's value. The four
   `_rescue_row_fields` call sites (`:3738`, `:3763`, `:3775`, `:3888`) are all downstream of
   `:3647`. `_rpos_row` is a fresh `[None]` list object per row, not a module- or closure-level cell,
   so even aliasing cannot carry a value forward.
2. Relatedly: the round-1 finding-16 ordering property still holds — the donor capture is inside the
   row body after `ctxs` exists, so `--rescue-donor self` cannot read a previous row's hooks.

**`holm()` is correct** (`dcs_csi_subspace_analyze.py:165-174`). 2000 randomised cases (m = 1…6,
with deliberate ties at 0.01/0.02/0.05/0.2) against an independent reference implementation of the
step-down: **0 mismatches**. The `(m - i)` multiplier is right for 0-based `i`, the running max
enforces monotonicity (which makes rejection-by-adjusted-p equivalent to the step-down's
stop-at-first-failure rule), ties are handled correctly by the running max regardless of sort
order, and the `min(1.0, …)` cap is applied after the max so it cannot un-cap a later value.
Rejection uses the unrounded `adj`, not the rounded `p_holm`.

**`--tag-prefix`'s `.replace("patch_", prefix + "_", 1)` is effectively anchored**
(`dcs_csi_rederive_patch.py:365`). Every `ARM_SPEC` tag template literally begins with `"patch_"`,
so the first occurrence is always at index 0 and `count=1` replaces exactly the prefix. Traced the
adversarial case: `--codeword patch_x` gives `"patch_ctrl_patch_x"` → `"p0cmp_ctrl_patch_x"`, still
correct. `--tag-prefix patch` (the default) is a no-op.

**`load_corpus(allow_query_kinds=...)` default behaviour is byte-identical**
(`dcs_cont_layerpos_map.py:149`, `:187`). Old: `if qks != {"behavioral"}`. New:
`if qks != set(allow_query_kinds)` with `allow_query_kinds=("behavioral",)`, and
`set(("behavioral",)) == {"behavioral"}`. The default is an immutable tuple, so no shared-default
mutation hazard. I enumerated all 22 call sites of `lpm.load_corpus` across the repo: only
`dcs_csi_axis.py:229` passes the new parameter. Every other caller is unchanged. (Naming note: the
test is set *equality*, not subset, so the parameter is stricter than "allow" implies — which is
the conservative direction.)

**The round-1 fixes actually fire.**
* M2 (layer mismatch) and M3 (codeword/bank) are now `raise SystemExit`, not prints
  (`score_behavior.py:2044-2058`).
* m2 (decode guard) verified on the fake-model harness: `DonorPatch` and `SubspaceDonorPatch` both
  write **0** positions on a length-1 forward with `positions=[0]`, where before both wrote 1.
* `refuse_degenerate=True` raises *before* any mutation: after the raise, `n_applied == 0`,
  `_dose is None`, `liveness()["fired"] is False`. The `norm_match_basis`-only scope is right —
  a candidate arm (no `norm_match_basis`) never enters the branch.
* M1/M4 in `dcs_csi_axis.py` bind on real data: `--fit-prompt` is now derived from the rows
  (`:236-244`), the cell-C `target_surface` check binds (930 rows, all `button`), and
  `fit_population.domains_sha16` is produced (`4614853e5636eb5f`) and does reach the scoring rows —
  I read it back off a real `csi1_button_train_KO_AXIS` row's `rescue_basis_meta`. (What is missing
  is the *comparison*; see m3.)

**`hidden[0]` is not a batch bug.** `SubspaceDonorPatch._hook` and `DonorPatch._hook` both patch
only batch row 0. Under `_wants_knockout`, `string_option_readout` is pinned to `max_batch=1`
(`score_behavior.py:3337-3339`), and the rescue block refuses any row without a knockout
(`:3649-3651`), so batch > 1 is unreachable on the rescue path. Confirmed against the real runs:
`readout_max_batch: 1` in every `csi1*` config.

**The donor positions stay valid in the readout forwards.** The donor is captured on
`ids_r = tok(templated)` but the readouts run on `templated + answer_prefix + variant`. I tested
prefix stability with the real Llama-3.1-8B-Instruct tokenizer on 40 cell-C bank rows × 3 suffixes
(`"Answer:"`, `"Answer: bomb"`, `"Answer: button"`): **0/120 prefix breaks**, because `templated`
ends on special tokens (`<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n`). So the
absolute indices in `_rpos` address the same tokens in the readout forward as at capture time. Also
confirmed `templated` (used for the readouts) and `templated_r` (used to resolve `dk`/`prot`/the
donor positions) are produced by the same `dc.apply_template(tok, row["full_prompt"],
enable_thinking=…)` call with the same arguments — `extract_boombness.resolve_occurrences:291-292`.

**`_dose` being overwritten per forward is benign here.** Each row makes 4 patched forwards
(measured: `n_forward_calls == 4` on 670/670 rows, `n_positions_written == 112 == 28 × 4`), one per
answer variant. Because attention is causal and only the appended variant differs, the residual at
the patched query positions is identical across the four, so the last-forward dose the row records
equals every forward's dose. Confirmed on real rows: `delta_norm_mean` is bit-identical across the
`KO_AXIS`, `KO_AXIS_ANCHOR` and `KO_ORTH` runs for the same `prompt_id`
(`1.5539617661040213`), which is the expected signature of a deterministic, arm-independent donor.

**Norm matching is live and correct in the real artifacts.** `KO_ORTH` row 1:
`proj_norm_mean = 0.02840`, `written_norm_mean = 0.07220` — exactly `KO_AXIS`'s
`proj_norm_mean = 0.07220`. `n_positions_norm_match_degenerate` is 0 summed over all 670 rows, so
the `refuse_degenerate` path never fired on the shipped data.

**`strict_run_dir(row_file=...)` is sound** (`dcs_csi_rederive_patch.py:53-86`). The new parameter
only changes which file is line-counted; `DONE.json.status == "ok"` and
`rows_written == expect_n` are still both required, and the "exactly one candidate" rule is
unchanged. The default stays `gens.jsonl`, so `dcs_csi_rederive_patch`'s own call at `:366` is
unchanged. `dcs_csi_subspace_analyze` passes `results.jsonl`, which is correct for its
`--no-generate` readout runs (where `rows_written` counts result rows).

**The analyser's remaining VOID conditions are all appended *and* checked.** I traced each computed
condition to an `append` and confirmed `if void: … return 2` at `:323-329` precedes every
`contrast()` call at `:341`. The three exceptions are called out above: `in_sample` (m3),
`specificity_all_controls_rejected` (m4) and `rows_dropped_by_option_mass_floor` (B1) are computed
and recorded but never gated. `row_meta`'s `basis_meta` uniqueness refusal (`:152-157`) does fire.
The `prefill_edits_min` check correctly treats both `None` (field absent on every row) and `0` as
VOID. `doms` is the intersection across arms and every contrast and the `installation_by_arm`
summary are computed on that same `doms`, so no contrast is formed over a domain one arm lacks.
