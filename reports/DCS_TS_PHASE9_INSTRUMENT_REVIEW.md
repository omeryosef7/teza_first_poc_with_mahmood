# DCS-PR-057 PHASE 9 INSTRUMENT — ADVERSARIAL CODE REVIEW

**Date:** 2026-09-07 · **Mode:** READ + RUN + REPORT. No file edited, no commit, no stash, no GPU,
no SLURM, no network. One temporary detached worktree was created under the session scratchpad and
removed again (`git worktree remove --force` + `prune`); the shared tree and index were not touched.

**Target:** `git diff 30c3128b e9dae21c` over `src/boombness/score_behavior.py`,
`scripts/dcs_ts_pr048_analysis.py`, `scripts/dcs_ts_pr057_causal.py`.
**Author's account under test:** `reports/DCS_TS_PHASE9_BLOCKERS_CLEARED.md`.

Python: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`.

---

## 0. Reproduction of the author's reported numbers

| author reported | I observed | verdict |
|---|---|---|
| `--self-test` 73 checks / 0 failed | **73 checks, 0 FAILED** | REPRODUCED (working tree only — see F1) |
| `--mutate` 38/38 RED | **38/38 mutations produced a refusal**, 0 GREEN/survivors | REPRODUCED (working tree only) |
| `dcs_ts_pr048_analysis.py --selftest` 16/16 | **16/16 guards reachable** | REPRODUCED |
| pytest "1693 passed / 4 pre-existing failures" | **NOT REPRODUCIBLE** — see F10 | NOT REPRODUCED |

Commands run, verbatim:

```
python scripts/dcs_ts_pr057_causal.py --self-test
python scripts/dcs_ts_pr057_causal.py --mutate
python scripts/dcs_ts_pr048_analysis.py --selftest
python -m pytest -q -p no:randomly
python -m pytest -q -p no:randomly --ignore=AutoInject --ignore=TROPT --ignore=Chain_of_Thought_Hijacking
```

The three self-test/mutation figures are exact. **They were measured against a tree containing
uncommitted changes** — that is F1, and it is the first finding because it conditions the other
three rows of this table.

---

## FINDINGS

### F1 — BLOCKING. Commit `e9dae21c` does not run. The Q12 half of the instrument was never committed.

**Where:** `doublespeak_causality/pair_common.py` (absent from the commit);
`src/boombness/score_behavior.py:1430-1471` (the callers).

The author's report names `pair_common.py` as one of four edited files and attributes Q12's
liveness instrumentation, `DisabledHookBridge`, the single-site wiring and the view-aliasing fix to
it. **`pair_common.py` is not in commit `e9dae21c`:**

```
$ git diff --stat 30c3128b e9dae21c -- doublespeak_causality/pair_common.py
(empty)
$ git diff --stat HEAD -- doublespeak_causality/pair_common.py
 doublespeak_causality/pair_common.py | 370 +++++++++++++++++++++++++++++++++--
 1 file changed, 354 insertions(+), 16 deletions(-)
```

`hook_stats_dict`, `project_out_liveness_violations` and `DisabledHookBridge` exist at neither
`30c3128b` nor `e9dae21c` — only in the uncommitted working tree. The committed
`AllPositionProjectOut.__init__` signature at `e9dae21c` is
`(self, model, layer_idx, direction, alpha=1.0)` — **no `stats` keyword** — while committed
`score_behavior.py:1433` calls `pc.AllPositionProjectOut(..., stats=st)` and `:1440` calls
`pc.SinglePositionProjectOut(..., stats=st, rel_end=q)`.

Run at a clean detached worktree checked out at `e9dae21c`:

```
$ python scripts/dcs_ts_pr057_causal.py --self-test
AttributeError: module 'pair_common' has no attribute 'hook_stats_dict'
```

Consequences:

1. The committed instrument is not self-consistent. The 73/38 figures certify the working tree, not
   `e9dae21c`.
2. This is a **regression for every pre-existing `project_out` caller**, not only PR-057 arms. The
   `stats=` keyword is passed unconditionally (`stats=st` where `st` may be `None`), so at the
   committed tree *any* `--intervene ...:project_out:...` run raises `TypeError`. The "additive and
   default-off, an existing caller gets byte-identical behaviour" claim is true of the working tree
   and false of the commit.
3. The author's headline evidence — "84/84 make_intervention hook constructions and 300/300
   pair_common hook applications bit-identical to HEAD" — was measured against a HEAD whose
   `pair_common.py` is the uncommitted one. I could not re-run that comparison against the
   committed baseline because the committed baseline does not import.

**Would it change a PHASE 9 conclusion?** It prevents PHASE 9 from being *run* from the commit, and
it means the frozen provenance of the instrument is a working-tree state that no commit records. In
a tree with a documented third concurrent writer this is not a formality.

---

### F2 — BLOCKING. The liveness producer and the liveness consumer disagree on the record schema. Every healthy arm is gated VOID.

**Where:**
producer `doublespeak_causality/pair_common.py:1116-1140` (`hook_stats_dict`) and
`src/boombness/score_behavior.py:2851-2862` (the `PR057_LIVENESS.jsonl` writer);
consumer `scripts/dcs_ts_pr057_causal.py:781-845` (`liveness_gate`) and `:848-869`
(`orthogonal_residual_gate`).

The two are explicitly wired: `score_behavior.py` writes `run.p("PR057_LIVENESS.jsonl")` and
`dcs_ts_pr057_causal.py:220` sets `CONTRACT_LIVENESS = "PR057_LIVENESS.jsonl"`, which
`load_arm_run` (`:1449`) reads into `out["liveness"]`. `liveness_gate` is named in
`O2_10_2_REQUIRED_COMPANION_GATES` as mandatory for the **C-112 primary**.

`hook_stats_dict` never creates `n_cells_edited_expected` or `orthogonal_residual_delta_l2`
(confirmed: `grep -c` returns 0 in both `pair_common.py` and `score_behavior.py`). Both consumers
read them with a defaulting `.get`.

I produced three records with the **real** hook on a 5120-dim toy model, verified the producer calls
them clean, and fed those exact records to the two consumer gates (`liveness_gate` and
`orthogonal_residual_gate` extracted by `ast` and executed standalone):

```
producer verdict (pair_common.project_out_liveness_violations): CLEAN on all 3 rows
cos_pre_post sample: 0.9998400211334229
'n_cells_edited_expected' present in producer record: False
'orthogonal_residual_delta_l2' present: False

CONSUMER liveness_gate -> live = False   n_cells_expected = 0
   REASON: n_cells_edited_expected is 0 everywhere: the arm declared no destinations, so
           'realised == expected' is vacuously true and proves nothing
           (a check that binds zero is not a check)

CONSUMER orthogonal_residual_gate -> ok = False  n_violations = 3 / 3  max_abs = nan
   detail: the orthogonal component was NOT preserved; H2b is VOID (I-N7 is blocking)
```

`liveness_gate` returns `live = (not reasons)` (`:842`), so **every real arm this instrument
produces is `live=False`**, and the 10.2 primary is unreportable by its own required companion gate.

`orthogonal_residual_gate` is worse than a false negative. The field is absent, so
`float(r.get(..., float("nan")))` yields NaN, `abs(nan) <= tol` is False, every row counts as a
violation, `max_abs` is `nan`, and the artifact asserts *"the orthogonal component was NOT
preserved; H2b is VOID"* — a positive claim of a physical violation when the truth is "the quantity
was never recorded". This is the mirror image of the repo's own recorded bug class (a check reading
the producer's own null field): here the check reads a field the producer never wrote and reports a
substantive failure rather than a missing measurement.

Note the frozen config `configs/dcs_ts_pr057_phase9.json` → `persist_per_row_and_per_arm.fields`
requires `n_cells_edited_expected`, `orthogonal_residual_delta_l2 (H2b: must be 0 to tolerance)`,
`frac_cellmean_spread_removed`, `cosine(edit, v_used)`, `direction_file_sha256` and
`control_draw_seed`, and its `void_if` includes *"realised != expected cell count"*. None of these
reach the liveness record the instrument actually writes. `dcs_ts_pr057_causal.py` has a **second,
parallel** `LivenessStats` dataclass (`:325-345`) that does carry them — so there are two liveness
schemas in the instrument and the one that is written is not the one that is read.

**Would it change a PHASE 9 conclusion?** Yes, directly: the primary's mandatory liveness gate fails
open-loop on correct data. Either PHASE 9 halts on a spurious VOID, or the gate gets waived — and a
waived liveness gate is exactly the C-13 hole this work exists to close.

---

### F3 — SERIOUS. Q12(d): `rel_end` is recorded as the absolute index. The frozen config's mandated end-relative persistence never happens.

**Where:** `src/boombness/score_behavior.py:2540` resolves the CLI offset to an absolute index
(`_pr057_pos.append(len(ids_r) + _r)`); `:1438` and `:1440-1441` then pass that **already-absolute**
value as *both* `pos=q` **and** `rel_end=q`.

`pair_common.py:1540` stores `stats["rel_end"] = int(rel_end)`, and the single-position hook computes
`_abs = pos if pos >= 0 else int(h.shape[1]) + int(pos)` — with `pos` already non-negative, `_abs ==
pos == rel_end`. The requested end-relative offset never reaches any artifact.

Demonstrated by replaying `:2540` + `:1438-1441` exactly, for `--pr057-edit-positions=-3`:

```
seq_len=10 CLI rel_end requested=-3 | RECORDED rel_end=7  resolved_abs=[7]  seq_len_last=10
           | documented invariant abs == seq_len + rel_end HOLDS? False
           | liveness violations: []
seq_len=17 CLI rel_end requested=-3 | RECORDED rel_end=14 resolved_abs=[14] seq_len_last=17
           | documented invariant abs == seq_len + rel_end HOLDS? False
           | liveness violations: []
```

The **edit itself is correct** — position 7 for a 10-token row, 14 for a 17-token row, resolved per
row as required. This is a record/audit defect, not a wrong intervention. But:

* `pair_common.py:1524-1531`'s own comment states the auditable invariant
  `resolved_absolute_index == seq_len + rel_end`. It is false on every row, and the liveness checker
  reports **clean**.
* The frozen config mandates `"token position edited (as rel_end AND as the resolved absolute
  index)"` and adds `"_absolute_index_is_persisted_only_as_a_witness"`. The artifact persists the
  witness twice under two names and the mandated quantity zero times, so the S1 arm's 10.3 artifact
  is non-conformant with the frozen preregistration.
* The reader-side check the config describes is defeated. A reader inspecting `rel_end` across rows
  sees it **varying** (7, 14, …) where a correct artifact would show it constant at −10. That reads
  as evidence of the very bug class the field exists to detect.

`make_intervention`'s own docstring (`:1067-1076`) does not state whether `edit_positions` is
absolute or end-relative; the report's §2(a) table conflates the two ("`edit_positions=[7]`
(rel_end −3)"). That ambiguity at the boundary is where the value was mislabelled.

**Would it change a PHASE 9 conclusion?** Not the S1 point estimate. It makes the S1 liveness
artifact fail its own frozen spec and removes the audit that distinguishes a correctly resolved
site from the repo's twice-recorded absolute-index bug.

---

### F4 — MINOR/SERIOUS. Q10's probe pin is opt-in and nothing requires it.

**Where:** `scripts/dcs_ts_pr057_causal.py:651` `load_frozen_probe(path, expect_sha=None)`; `:676`
`if expect_sha and fp.sha256 != expect_sha`.

`pr048_analysis.py:566-570` computes a content hash and comments *"PHASE 9 pins this, so a probe
that has been re-fitted, re-selected or re-scaled between the two phases cannot be loaded silently
under the name of the one that produced R-113."* The pin fires only when a caller supplies
`expect_sha`. The only two callers at this commit are in the self-test (`:2056`, `:2068`) and
**neither passes it**, and `configs/dcs_ts_pr057_phase9.json` carries no probe sha key. The stated
guarantee is therefore currently unenforced — the repo's own "threshold published but never
enforced" pattern.

Mitigating: the production caller is `src/boombness/pr057_run_causal.py`, which is being written by
another agent and does not exist at this commit, so this may be closed there. Flagged so it is not
assumed closed.

---

### F5 — MINOR. Q10's export guards can void an already-completed inference.

**Where:** `scripts/dcs_ts_pr048_analysis.py:576-633`, all before `json.dump(res, f)` at `:640`.

Five `PreregError` raises and one self-verification raise sit between the completed permutation test
and the write. If any fires, the run produces **no output at all** — the observed accuracy, the sign
test and the (expensive, ~7.8 h) permutation null are discarded. The author documents this for
`n_samples_seen_` but not as a general property. The block is additive to the *numbers* but not to
the *failure modes*, and the guards are near-untrippable on valid data, so: MINOR.

---

### F6 — MINOR. The liveness magnitude gate reads only the LAST forward.

**Where:** `pair_common.py:1157-1160` (`_record_edit` **assigns** `activation_norm_pre/post`,
`projection_removed_l2`, `cos_pre_post` each call; only `sum_projection_removed_l2` accumulates);
gated at `:1194-1206`.

`AllPositionProjectOut` fires on prefill *and* every KV-cached decode step, and each call overwrites
the gated scalars. The gate therefore certifies the **last decode step**, not the run. A hook dead
on prefill but live on the final decode step passes; a hook live on prefill whose final decode step
had a near-zero projection fails. `sum_projection_removed_l2` is recorded and never gated, so the
information to close this is present and unused. The author explicitly handled the analogous
*partially-dead-band* case with per-layer records but not the partially-dead-across-forwards case.

Attack line 5's narrow question — *can the liveness counter be satisfied by a hook that fired but
wrote nothing?* — is **NO**: `hook_fired_count` is incremented inside `_record_edit`, i.e. only
after a write, and `n_cells_edited_realised`, `projection_removed_l2` and `max_abs_delta` must all
be `> 0`, plus a scale-free float32-epsilon bar. The residual weakness is partial liveness across
forwards, not zero liveness.

---

### F7 — MINOR. `PR057_ARM.json` reports one arbitrary row's absolute edit positions as the arm's.

**Where:** `score_behavior.py:2534` rebinds `_pr057_echo = {}` **per row**; `:1465-1471` appends
`"edit_positions": _pos` (absolute, per-row); `:2898-2906` writes the last surviving row's echo.

For an S1 arm the manifest reads e.g. `"edit_positions": [412]` when the arm edited a *different*
absolute position on every row. Combined with F3, `PR057_ARM.json` contains no representation of the
requested site. `"edit_positions_flag"` does carry the raw CLI string, which partially mitigates.

---

### F8 — MINOR. `_resolve_hook_target` still has a whole-model fallback behind a broad `except`.

**Where:** `scripts/dcs_ts_pr057_causal.py:493-513`.

The ordering fix the author claims is **real and correct**: `ds_common._get_layers` is tried FIRST,
and only an object it cannot resolve falls through to `hasattr(model, "register_forward_hook")`.
`layers[layer_idx]` is outside the `try`, so an out-of-range index raises rather than falling back.
Residual: `except Exception` around `_get_layers` means an architecture that makes `_get_layers`
raise silently hooks the whole model while every log says "layer 9" — the exact defect, one
condition removed. Not reachable for the Qwen/Llama models in play.

---

### F9 — MINOR. The two components encode contradictory cosine policies.

`pair_common.py:1209-1213` deliberately does **not** gate `cos_pre_post == 1.0`, with a stated
reason: at float32 a genuine small edit rounds the cosine to 1.0 and gating would refuse live hooks.
`dcs_ts_pr057_causal.py:800-801, 822-824` **does** gate it: `abs(c - 1.0) <= tol`, `tol=1e-6`. At
5120 dims with `alpha=1` I measured `cos_pre_post = 0.99984`, i.e. `|c-1| ≈ 1.6e-4`, ~160× the
tolerance, so it passes today. At a reduced dose or a narrower band it would not, and the author's
own argument indicts the consumer.

---

### F10 — MINOR (reporting). The pytest figure is not reproducible and the invocation is not recorded.

Author: "1693 passed / 4 pre-existing failures". Observed:

| invocation | tree | result |
|---|---|---|
| `pytest -q -p no:randomly` (repo root) | working tree | **0 tests ran** — `Interrupted: 8 errors during collection` |
| same | clean `e9dae21c` | **0 tests ran** — 7 collection errors |
| `pytest -q --ignore=AutoInject --ignore=TROPT --ignore=Chain_of_Thought_Hijacking` | working tree | **35 failed, 2320 passed, 56 skipped** |
| same | clean `e9dae21c` | **53 failed, 2274 passed, 84 skipped** |

The report records no pytest command, so "1693 / 4" cannot be checked. A count with no invocation is
not a measurement.

**On attack line 7 — are the failures pre-existing and unrelated? YES.** All 35 working-tree
failures are in `poc_stage4_5`, `poc_stage4_6`, `poc_stage4_7`, `poc_stage_gcg_early` and
`tests/test_prompt_families_strict.py`; none touches `score_behavior.py`, `pair_common.py`,
`dcs_ts_pr048_analysis.py` or `dcs_ts_pr057_causal.py`. Every one of those families also fails at
clean `e9dae21c`. The 53−35 = 18 extra failures at the clean worktree
(`test_cited_artifact_check`, `test_my_cited_artifacts`, `test_run_completeness_check`,
`test_run_index`) are tests that read untracked corpus and run artifacts, which a detached worktree
does not receive — a worktree artifact, not a regression.

One collection error deserves a note because it looks alarming and is not:
`doublespeak_causality/tests/test_hook_firing_synthetic.py` ERRORs during whole-root collection at
**both** commits, but run alone it is `4 passed in 108.98s`. It is a duplicate-`tests`-package
import collision, not a hook failure.

---

## ATTACK LINES WITH NO FINDING

These are real results. I looked and found nothing.

**1 — Q10, the frozen probe. NO FINDING.** `return_estimator` (`pr048_analysis.py:393-411`) changes
only what the tuple contains; `sc` and `clf` are fitted unconditionally on the lines above and are
handed back, not re-fitted. The observed pass is a **single** call at `:463-464`, exactly as before.
Nothing in the export block consumes randomness. Ordering verified: the export (`:537-633`) runs
strictly **after** the permutation block (`:487-503`), so `rng = np.random.default_rng(seed)` and
`seeds = rng.integers(...)` are untouched. I specifically checked the trap you would expect — that
the permutation loop rebinds `pred` or `_obs_clf` before the self-verification reads them: it does
not; `_one_draw` (`:494-501`) uses only local names and its own `np.random.default_rng(seed_i)`.
The permutation's `_sc` is a separate scaler fit on the same `tr` rows, so exporting `_obs_scaler`
is correct. The self-verification (`:617-632`) re-scores from the exported numbers alone and refuses
on any disagreement, and the consumer `load_frozen_probe` (`:667-675`) refuses a probe whose
producer did not self-verify. **The export is additive; no reported number, RNG draw or permutation
stream shifts.**

**2 — Q9, the multi-concept answer set. NO FINDING.** The one-pair-per-bank assertion is intact and
untouched by the diff, at `score_behavior.py:2287-2291`
(`_pairs_in_bank = sorted({(r["codeword"], r["concept"]) for r in rows})`, refuse if `!= 1`). The
relaxation is scoped to the answer set only: `--semantic-extra-words` defaults to `""`, so
`extra_words == []`, `sem_variants` is the historical two-group dict, and `_semantic` sees an
identical input. In `signals.string_option_readout:693` each `logp_{group}` is a teacher-forced
absolute score independent of the other groups, and `top1_id` is read from `lp[0, ...]` — the first
variant of the first group — which extra words, appended after the two historical groups, cannot
displace. `option_mass` does widen; that is handled by feeding the gate `option_mass_core_pair`
(`:2846`). **A PHASE 7 bank re-run through this code path yields identical `logp_*`; R-116 stands.**
Two additive schema changes for the record: `option_mass_core_pair` is emitted unconditionally
(`:2612-2614`) and three keys are added to `run.note` — new fields, no changed values. One edge case
too small to be a finding: extra words are de-duplicated case-sensitively, so `knife` and `Knife`
would both be admitted and double-count in `option_mass` (though not in the gated
`option_mass_core_pair`).

**3 — Q13, the control base direction. NO FINDING.** The alias reaches **both** control families:
`base = payload[_ctl_base_name]` at `:1325` feeds the `in_subspace`/`in_subspace_orth` branch via
`for L, v in base.items()` (`:1336`) *and* the `random`/`orthogonal` branch via
`{L: maker(v, ...) for L, v in base.items()}` (`:1372`). The dose alias is applied too:
`gaps = (payload.get("gap") or {}).get(_ctl_base_name, {})` at `:1376`. A missing base **refuses**
by name and lists what the payload does carry (`:1318-1324`) — no fall-through. Two answers refuse
twice: at argument-parse time (`:2003-2007`) and inside `split_control_base` (`:1004-1009`).
`assert_control_norm_matched` (`:997-1043`) refuses at hook-install time on a zero-norm base, a
relative norm difference above tolerance, and a **zero-layer bind**. On the echo: `arm_echo` records
the *resolved name*, but `assert_control_norm_matched` computes `base_norm`, `control_norm`,
`rel_norm_diff` and `cos_with_base` from the **actual tensor objects** used, and those per-layer
numbers go into the same echo — so the manifest is bound to the realised direction, not merely to
the requested label. One honest caveat, not a defect: in the happy path the check compares the
control against the same object the maker derived it from, so it is close to tautological and
functions as a maker-regression tripwire; the substantive Q13 protection is the removal of the
hard-coded `payload["d_surface"]`, which is real. Mutation `M28` and `M32` are RED.

**4 — Q12(d), single-position scoping. NO FINDING on scope.** `edit_positions=None` keeps
`AllPositionProjectOut`; a list routes to one `SinglePositionProjectOut` per position per layer
(`:1430-1444`). An S1 arm cannot degrade to an all-position edit — the two classes are selected by
an `if _pos is None` on which nothing else depends. Degradation paths refuse rather than widen:
empty list (`:1408-1412`), duplicates (`:1414-1416`), and `mode != "project_out"`
(`:1417-1421`, *"Refusing rather than silently widening the scope back"*). The CLI refuses a
non-negative offset by name (`:2530-2536`) and refuses an offset outside the row
(`:2537-2539`). Self-test `q12_single_vs_all_position_scope` measures `all=9 one=1`. The
**bookkeeping** of that scope is F3.

**5 — hook liveness. The two named fixes are REAL.** The view-aliasing fix is in the file:
`pair_common.py:1516-1522` copies the pre-edit slice (`hp_pre = hp.clone()`) **before**
`h[:, pos, :] = h_new`, with the comment saying why. The whole-model-hook fix is in the file:
`dcs_ts_pr057_causal.py:493-513` tries `ds_common._get_layers` first and documents that a `hasattr`
check first would have hooked the whole model while logging "layer 9". The dead-hook signature
cannot be mistaken for a clean null: `project_out_liveness_violations` refuses `n_forward_calls==0`,
`hook_fired_count==0`, zero cells, zero projection, `max_abs_delta==0`, an edit below float32
resolution relative to the state, and an unrecorded cosine; the bridge branch refuses any edited
cell and a bridge over a hook that would not have changed anything. Self-tests
`q12_bridge_presented_as_live_is_DETECTED`, `q12_bridge_over_a_dead_hook_refused` and
`q12_hook_that_never_ran_refused` all pass. Residual weaknesses are F6 (last-forward scalars) and
F8 (fallback), and the whole subsystem is subject to F1 and F2.

**6 — layer convention. NO FINDING.** Read and write agree, in the new code, on
`block L == hidden_states[L+1]`. Write side: `AllPositionProjectOut`/`SinglePositionProjectOut`
resolve through `_resolve_layer(model, L)` and use `register_forward_hook`, i.e. block L's output;
`make_project_out_hook`'s docstring states the convention explicitly. Read side: `ProbeReadCapture`
(`dcs_ts_pr057_causal.py:709`) uses `_resolve_hook_target(model, layer_idx)` and
`register_forward_hook` — the same tensor. Probe-fit side: `pr048_analysis.py:344` indexes
`t[run_layers.index(L)]` into the extraction cache, and `src/boombness/extract_boombness.py:21`
declares `block L == hidden_states[L+1]`. The frozen config states the same convention and records
`"layer_convention_verified_by": "planted-hook GPU test, job 860184, 2026-09-07 -- CONFIRMED"`.
The post-final-norm trap is avoided: `read_layer_grid` is `[7..14]`, nowhere near `hidden_states[n_layers]`.
`ProbeReadCapture` also refuses a non-negative `rel_end` (`:704-707`) and resolves per forward as
`seq_len + rel_end` (`:722`) — correctly end-relative, unlike F3. One interpretive caveat, not a
code defect: for propagation reads at blocks 10–14 the L9-fitted frozen probe is applied
off its fit layer, and nothing in `o1_from_probe_rows` flags that; a fall in the probe score there
confounds "the concept moved" with "the probe is off-manifold at that layer". `probe_fit_layer` is
recorded alongside `read_layer`, so the confound is at least visible in the artifact.

---

## What I would fix before PHASE 9 runs

1. **F1** — commit `pair_common.py`, then re-run `--self-test`, `--mutate` and the bit-identity
   comparison against a baseline that actually imports.
2. **F2** — make one liveness schema. Have `hook_stats_dict` carry `n_cells_edited_expected`
   (computable: `n_layers × n_positions × batch × seq` for all-position, `× 1` for single-site) and
   `orthogonal_residual_delta_l2`; or have `liveness_gate`/`orthogonal_residual_gate` **refuse a
   record that lacks the key** instead of defaulting it to `0` / `NaN` and reporting a substantive
   failure. The second is the smaller change and is the correct behaviour regardless.
3. **F3** — pass the requested end-relative offset, not the resolved absolute index, as `rel_end`;
   assert `resolved_absolute_index == seq_len_last + rel_end` in
   `project_out_liveness_violations` so the invariant the comment claims is actually enforced.

---

## VERDICT

**NO — not as committed.** `e9dae21c` does not import (F1), and even with the uncommitted
`pair_common.py` the primary outcome's mandatory liveness gate returns VOID on correct data (F2)
and the S1 arm's position artifact does not conform to the frozen preregistration (F3). Q10, Q9,
Q13, the Q12 scope split and the layer convention all survived attack; the instrument is close, but
F1–F3 must be closed first.

---

# APPENDIX A — FIXES APPLIED, 2026-09-07 (second session)

**Mode:** EDIT + RUN + REPORT. CPU only. No SLURM job submitted, no GPU, no network, no commit,
no stash, no `git add`. `configs/dcs_ts_pr057_phase9.json` was **not** edited; the one place this
work interprets a frozen field is recorded in A.3.

Python: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`.

**Files modified (unscoped `git status --porcelain`, ` M` entries only):**

```
 M doublespeak_causality/pair_common.py
 M scripts/dcs_ts_pr057_causal.py
 M src/boombness/pr057_run_causal.py
 M src/boombness/score_behavior.py
```

Nothing else in the tree was written. `scripts/dcs_ts_pr059_localisation.py`, the `ts116*` banks
and the `ts_cand/ts_repair/ts_smoke` directories are untracked files belonging to other work and
were not touched. F1 was already closed by commit `021b20e8` and was not redone.

---

## A.1 — C-117 / F2: the two liveness schemas, reconciled

The core bug named in the task is the one that was fixed: **a defaulting `.get` that turns a
MISSING field into a FAILING verdict.** It was fixed on both sides at once, and NOT by making the
gate lenient.

**Ownership, decided deliberately and written into the code as a comment block at
`pair_common.py:HOOK_STATS_KEYS`:**

| field | owner | why |
|---|---|---|
| `n_cells_edited_expected` | **PRODUCER** | only the hook sees the tensor it was HANDED. It is counted at the top of each forward from the input shape and the declared scope, **before** the write; `n_cells_edited_realised` is counted from the slice actually written. `realised == expected` is then a real bind instead of `0 == 0`. |
| `orthogonal_residual_delta_l2` | **PRODUCER** | only the hook holds `h_pre`, `h_post` and `d`. A `project_out` edit is `alpha*(h.d)d`, so its component orthogonal to `d` must be 0 to float error; measuring it costs one projection and turns I-N7 from an assertion into a number. Measured for `project_out` in `pair_common` **and** in the analyzer's own instrumented hook, and against `span{v_out,v_in}` in the component-replace hook. |
| `n_forward_with_destinations`, `min_projection_removed_l2` | **PRODUCER** | new, for F6 (below). |
| `seq_len_at_resolution` | **PRODUCER**, supplied by the caller | for F3 (A.2). |
| the missing-vs-zero distinction | **CONSUMER** | `liveness_gate` and `orthogonal_residual_gate` now raise `NotMeasured` (a new `Refusal` subclass) when a field is **absent**, and still return a failing verdict when it is a **measured zero**. |
| the record SHAPE (`resolved_absolute_index` as a list, `seq_len` vs `seq_len_at_resolution`, an all-position record with no `rel_end`) | **CONSUMER** | `audit_end_relative` was made schema-aware instead of the runner rewriting the artifact. A list of one is unpacked; an all-position record is reported as *not applicable* and counted, never given an invented `rel_end`. |

`hook_stats_dict` initialises the two measured floats to **`None`, not `0.0`** — a default of `0.0`
for `orthogonal_residual_delta_l2` is a *measured perfect preservation*, i.e. the I-N7 verdict,
handed out to a hook that never computed it. The analyzer's `LivenessStats` had exactly that
default and it was changed too.

`src/boombness/pr057_run_causal.py` no longer invents `n_cells_edited_expected := n_destination_rows`
in `annotate_liveness`; it **requires** the producer's own count (`n_destination_rows` is only
incremented *after* a successful write, so annotating from it would make `realised == expected`
true by construction again — the vacuity one level down). `orthogonal_residual_delta_l2` moved in
`PERSIST_LOCATION` from `("arm", "H2b only")` — a waiver — to `("row", ...)`, a number, and a LIVE
arm that lacks it is a refusal.

**Observed, the reviewer's exact reproduction (REAL `pair_common` records, 5120-dim toy model,
3 rows of length 10/17/23, fed to the two consumer gates):**

```
PRODUCER verdict (pair_common.project_out_liveness_violations): ['CLEAN', 'CLEAN', 'CLEAN']
cos_pre_post sample: 0.999975860118866
'n_cells_edited_expected' present in producer record: True -> 1
'orthogonal_residual_delta_l2' present: True -> 1.801280177460285e-06

CONSUMER liveness_gate -> live = True   n_cells_expected = 3  n_cells_realised = 3  n_fired = 3
   reasons: []
CONSUMER orthogonal_residual_gate -> ok = True  n_violations = 0 / 3  max_abs = 1.820e-06  tol = 1e-04
CONSUMER audit_end_relative -> ok = True  n = 3  violations = 0  distinct_abs = 3

MISSING expected      -> NotMeasured: "arm repro: liveness record 1/1 does not carry
                         ['n_cells_edited_expected']. This gate will not turn an UNRECORDED
                         quantity into a scientific verdict about the arm..."
MEASURED ZERO expected -> live = False | "n_cells_edited_expected is 0 everywhere: the arm
                         declared no destinations, so 'realised == expected' is vacuously true..."
```

Compare the review's §F2 block: `live = False`, `n_cells_expected = 0`, `ok = False`,
`n_violations = 3/3`, `max_abs = nan`. Both consumers now return the correct verdict on the same
class of record, and **missing and zero are two different outcomes**, which is the whole of C-117.

---

## A.2 — F3: `rel_end` is now the offset, and the invariant is asserted per row

`score_behavior.py` resolved the CLI offset to an absolute index and passed it as **both** `pos=`
and `rel_end=`. It now carries two lists: `_pr057_pos` (what the hook EDITS, resolved against this
row) and `_pr057_rel` (what the artifact RECORDS), plus `edit_positions_seq_len = len(ids_r)` (the
length the site was resolved against). `make_intervention` gained
`edit_positions_rel_end=` / `edit_positions_seq_len=` and refuses a length mismatch, a non-negative
offset, and any pair failing `seq_len + rel_end == pos`.

**The absolute index remains the hook's input, deliberately, and this is the one design point
worth stating:** the site is defined relative to the *prompt*, and the single-position hook also
fires on the readout's variant forwards, whose realised lengths differ. Re-resolving `-10` inside
the hook against each of those would MOVE the edit. So the invariant is not
`resolved_absolute_index == seq_len_last + rel_end` (the last forward's length — that identity is
false on correct rows) but `resolved_absolute_index == seq_len_at_resolution + rel_end`, where
`seq_len_at_resolution` is `len(input_ids)` of the row. That is the same number
`score_behavior`'s liveness-row wrapper already writes as `seq_len`, so the consumer's audit needed
no new field.

The check is made at **three** points: `SinglePositionProjectOut.__init__` (construction time, per
row, the earliest possible), `make_intervention` (before any hook is built), and
`project_out_liveness_violations` over the persisted record (which aborts the run at the row).

**Observed, the review's §F3 table re-run through the real `make_intervention` path:**

```
seq=10  rel_end=-3  seq_len_at_resolution=10  resolved_abs=[7]   violations=CLEAN
seq=17  rel_end=-3  seq_len_at_resolution=17  resolved_abs=[14]  violations=CLEAN
```

`rel_end` is now **constant at -3** across rows (it was 7 and 14) and the absolute index **varies**
(7, 14, 20 over the three repro rows, `n_distinct_absolute_indices = 3`) — which is the direction
the witness is supposed to point. `PR057_ARM.json` also now carries `edit_positions_rel_end` and
`edit_positions_seq_len` alongside the per-row absolute list (a partial mitigation of F7; see A.5).

---

## A.3 — C-119: the C5 bridge, and the interpretation adopted

**An interpretation of a frozen field is recorded here rather than being made silently.**

`configs/dcs_ts_pr057_phase9.json` → `controls.arms[C5]` carries **only** `id`, `name`, `rule`,
`blocking`. It states **no alpha for C5 and no dose for it anywhere** — I grepped the whole file.
The `alpha = 0.0` and the gloss *"none -- the hook is registered and edits nothing"* were **literals
typed into `scripts/dcs_ts_pr057_causal.py`'s `build_arm_manifest`**, which is not frozen. So this
is not a case of overriding a preregistered quantity; it is a case of the code having chosen one
reading of the frozen rule and that reading being unevaluable. (The task brief states "alpha=0 is
what it says"; the frozen file does not say it, and that difference is why this could be fixed at
all rather than only recorded.)

**The reading adopted, from the rule's own words** — *"the full intervention code path with the
hook DISABLED"*: "the full intervention code path" is the LIVE arm's path at the LIVE arm's dose,
and "the hook DISABLED" is `DisabledHookBridge` — registered on the same layer objects, run in
full, write discarded. **The bridge's dose to the model is zero because nothing is WRITTEN, not
because alpha is.** C5 now carries `alpha = 1.0`, matched to the H2a arm it shadows.

**Why it must be the live alpha.** At `alpha = 0` the inner projection is `h - 0*(h.d)d`, an
identity: the bridge would reproduce the baseline byte-for-byte *even with a garbage direction on
the wrong layer, hooked onto the whole model*. It would pass for reasons that have nothing to do
with what C5 certifies. At the live alpha the inner hook computes the real edit,
`would_have_changed_max_abs > 0` proves the machinery around the write actually ran, and the
byte-identical output then means what the frozen rule says it means.

The alpha=0 refusal is **kept as a tripwire** (`DEFECT_C119_BRIDGE_ALPHA` still fires on a
`mode="disabled"` arm with `alpha == 0`, mutation M26). `build_argv`'s `arm.alpha or 1.0` was also
removed: that fallback would have launched an alpha-0.0 manifest arm at 1.0, so the arm submitted
would not have been the arm declared.

**Observed:** `--plan --split test` now reports **28 of 54 arms constructible** (was 26); the two
newly constructible arms are `c5_disabled_bridge_s1` and `c5_disabled_bridge_s2`. The smoke stage's
constructible set is now `['h2a_s1_projout_button', 'c5_disabled_bridge_s1']` — 2 of 2, where the
previous report recorded 1 of 2 with "the C5 half is blocked by C-119".

---

## A.4 — F6 and F9, fixed (both were cheap and neither required a threshold)

**F6 — the magnitude gate read only the LAST forward.** Two additive producer fields close it
without inventing a numeric bar:

* `min_projection_removed_l2` — the **minimum over forwards**, refused at exact zero. This is the
  substantive half of the F6 fix: the magnitude a forward removed is now bounded below across the
  whole run rather than sampled at the last one. Mutation **M44** is RED. The scale-free `rel_tol`
  bar is deliberately left on the last-forward value, so no threshold was tightened and no
  additional false-refusal risk was introduced on GPU.
* `n_forward_with_destinations` — incremented at the top of every forward that HAD cells to edit;
  `project_out_liveness_violations` refuses `hook_fired_count != n_forward_with_destinations`.
  **Stated honestly: in the two hooks as they stand today this identity holds by construction**
  (both counters are incremented in the same branch), so its value is as a *regression tripwire* on
  any future hook that can skip a write, not as a fix to a live defect. Mutation **M43** (fired 1
  of 4) shows the refusal is reachable.

**F9 — the two components encoded contradictory cosine policies.** `pair_common`'s argument was the
correct one and the consumer was changed to match it, not the other way round: `liveness_gate` no
longer refuses on `abs(cos_pre_post - 1.0) <= 1e-6` (which at a reduced dose or a narrower band
would have voided healthy arms — the review measured `|c-1| ≈ 1.6e-4`, only ~160× that tolerance).
The "did the state change" question is answered by the **same scale-free relative-magnitude rule
the producer applies** (`||removed|| / ||h_pre|| < 1.19e-07`), and the cosine is required to be
RECORDED (mandate 10.3 persists it) rather than gated on a value. This is a *stricter*, not a
laxer, test: it is dose-independent.

---

## A.5 — F4, F5, F7, F8: reported, not fixed

* **F4** (the probe pin is opt-in) — unchanged, and it is **not** closed by the runner: `--emit-probe`
  is refused outright on C-118, so `load_frozen_probe` is never reached with an `expect_sha` in
  production. It remains a published-but-unenforced guarantee and should be closed when Q10's
  artifact is regenerated.
* **F5** (Q10 export guards can void a completed 7.8 h inference) — unchanged. It lives in
  `scripts/dcs_ts_pr048_analysis.py`, which this task did not authorise editing.
* **F7** (`PR057_ARM.json` reports one arbitrary row's absolute positions as the arm's) —
  **partially** mitigated, not fixed: the echo now also carries `edit_positions_rel_end` and
  `edit_positions_seq_len`, so the REQUESTED site (constant across rows) sits next to the last
  row's resolved indices. The per-row rebinding of `_pr057_echo` at `score_behavior.py:2534` is
  untouched.
* **F8** (`_resolve_hook_target`'s whole-model fallback behind a broad `except`) — unchanged. Not
  reachable for the Qwen/Llama models in play.

---

## A.6 — Verification, with the numbers observed

| command | before | **observed now** |
|---|---|---|
| `scripts/dcs_ts_pr057_causal.py --self-test` | 73 checks, 0 FAILED | **77 checks, 0 FAILED** |
| `scripts/dcs_ts_pr057_causal.py --mutate` | 38/38 RED | **52/52 mutations produced a refusal** |
| `src/boombness/pr057_run_causal.py --self-test` | 49 checks, 0 FAILED | **50 checks, 0 FAILED** |
| `src/boombness/pr057_run_causal.py --mutate` | 26/26 RED | **28/28 RED** |
| `src/boombness/pr057_run_causal.py --plan --split test` | 54 arms, 26 constructible | **54 arms, 28 constructible, 26 unbuildable** |

**The new mutations the task asked for, each observed RED:**

```
M39 liveness record MISSING n_cells_edited_expected  -> NotMeasured (the arm is UNJUDGED)
M40 expected cell count MEASURED and genuinely 0     -> live = False (judged, and it FAILED)
M41 realised != expected cell count                  -> live = False
M42 pair_common: absolute index recorded as rel_end  -> absolute_index_is_not_end_relative
M43 pair_common: partially dead hook (1 of 4 fwds)   -> partially_dead_hook        (F6)
M44 pair_common: some forward removed exactly zero   -> min_projection_removed_l2  (F6)
M45 pair_common: orthogonal residual never measured  -> ..._NOT_MEASURED
M46 orthogonal residual MISSING (not zero)           -> NotMeasured
M47 orthogonal residual recorded as NaN              -> NotMeasured
M48 end-relative audit on a record with no seq_len   -> NotMeasured
M49 single-site hook whose rel_end names another tok -> refused at CONSTRUCTION
M50 single-site hook given a NON-NEGATIVE rel_end    -> refused at CONSTRUCTION
M51 score_behavior: edit index that is not seq+rel   -> [score] REFUSING
M52 score_behavior: absolute index passed as rel_end -> [score] REFUSING
runner M26 alpha=0 disabled bridge                   -> RunnerRefusal (C-119 tripwire)
runner M27 record missing the producer's expected    -> RunnerRefusal (not repaired by annotation)
```

M39 vs M40 is the pair that matters: **a missing field raises and a measured zero fails.** If
either collapsed into the other the fix would be undone — defaulting missing→0 is the C-117 bug,
and excusing a measured 0 is the leniency that would let a dead hook pass as a clean null.

---

## A.7 — Repo tests: what was actually observed

The node is contended (72–73 users, load ~10, several other sessions' `pytest` runs and a
multi-hour job). A targeted subset was run rather than the whole root, and **only runs that went
to completion in this session are reported.** Both were run against the final state of all four
files.

| invocation | **observed** |
|---|---|
| `pytest -q -p no:randomly` over the 5 `doublespeak_causality/tests/` files that drive the changed hooks — `test_projectout_hook_synthetic`, `test_singleposition_projectout_synthetic`, `test_hook_firing_synthetic`, `test_resolve_positions_synthetic`, `test_alladd_hook_synthetic` | **43 passed, 0 failed, in 87.74 s** |
| `pytest -q -p no:randomly` over the 11 `tests/` files that drive `make_intervention` and the readout — `test_donor_patch`, `test_option_mass_gate`, `test_prompt_id_exclusions`, `test_readout_liveness`, `test_cell_residual_dose`, `test_knockout_liveness_gate`, `test_band_range_and_abort`, `test_silent_failures`, `test_composed_knockout`, `test_scoped_knockout_wiring`, `test_nondemo_control_draws` | **237 passed, 0 failed, in 410.48 s** |

Those 16 files are the complete set that imports `pair_common`, `score_behavior.make_intervention`,
or the project-out hooks (established by grep over `tests/` and
`doublespeak_causality/tests/`); **no test in the repo references `hook_stats_dict`,
`project_out_liveness_violations` or `SinglePositionProjectOut` directly**, so the changed liveness
API has no other test surface. `test_hook_firing_synthetic.py` is the file the first review noted
ERRORs under whole-root collection for a duplicate-`tests`-package reason; run in this subset it
passes.

**The whole-root suite was NOT re-run and nothing is claimed for it.** The first review already
established that `pytest` at this repo root does not collect (8 collection errors, 0 tests), and
its `--ignore`-ed variant takes far longer than this contended node allows. A cancelled run is not
a pass, so no green suite is reported.

**Backward compatibility, checked by inspection rather than assumed:** the two new
`make_intervention` keywords default to `None`, and the two other production callers
(`scripts/dcs_extract_under_ko.py:522`, `src/boombness/rah_transport_assay.py:300`) pass no
`edit_positions` at all. `doublespeak_causality/scripts/validate_refusal_directions.py:232` calls
`SinglePositionProjectOut(lm.model, L, vec, alpha, pos=-1)` positionally; the new
`seq_len_at_resolution` parameter was appended last, so no positional argument shifted. With
`stats=None` — every pre-PR-057 caller — no liveness branch is entered at all and the hook body is
unchanged.

---

## A.8 — What remains blocking before the Q1 validation job can be submitted

Nothing in this appendix's three defects. What is left is unchanged from the runner report:

1. **The Q1 stage itself is now constructible** — 2 arms (`h2a_s1_projout_*`), 230 rows each — and
   both blockers this task named (C-117, C-119) and F3 are closed. `--dry-run` should be re-run on
   the shared filesystem immediately before submission.
2. **C-113 stands** (recorded, not fixed): the frozen `directions.artifact.path` can never load;
   the runner uses the directory `outputs/dcs_ts/directions_pr053` and lets the loader join.
3. **C-118 stands**: `--emit-probe` is refused (no per-row attribution for `ProbeReadCapture`, and
   `outputs/dcs_ts/pr048_result.json` still carries no `FROZEN_PROBE` block). O1 is not obtainable
   from this run; Q1 does not need it.
4. **26 of 54 arms remain unbuildable** and each is refused by name: 16 H1 + 2 C7 (`patch` has no
   code path, and under C-112/R-116 the H1 population is empty), 4 H2b (`component_replace` has no
   code path), 2 C2 (no shuffled-label direction in the PR-053 payload), 2 C4 (`add` is still
   **not instrumented** — `pc.AllPositionAdd` is constructed with no `stats=`, so a C4 arm produces
   zero liveness records; this is the one remaining place in the intervention stack where a dead
   hook could score as a clean null, and it blocks C4, not Q1).
5. **F4 is still an unenforced pin** and **F5** still discards a completed inference on a guard
   failure. Neither blocks Q1.
6. The instrument as a whole is again **uncommitted working-tree state** (four modified files).
   Given F1, that provenance should be committed before the GPU time is spent — by the session
   that owns the tree, under the house's path-limited commit rule.

---

# APPENDIX B — THE LAST TWO CODE BLOCKERS, 2026-09-08 (third session)

**Mode:** EDIT + RUN + REPORT. CPU only. **No SLURM job submitted, no GPU, no network, no commit,
no `git add`, no `git stash`.** `configs/dcs_ts_pr057_phase9.json` and `configs/dcs_ts_pr048.json`
are FROZEN and were **not** edited; the one place this work reads a frozen field rather than a
literal is recorded in B.2.

Python: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`.

**Files modified (unscoped `git status --porcelain`, ` M` entries only):**

```
 M doublespeak_causality/pair_common.py
 M reports/DCS_TS_PHASE9_INSTRUMENT_REVIEW.md
 M scripts/dcs_ts_pr048_analysis.py
 M scripts/dcs_ts_pr057_causal.py
 M src/boombness/pr057_run_causal.py
 M src/boombness/score_behavior.py
```

Plus **one artifact**, which does not appear in `git status` because `.gitignore:11` ignores
`outputs/`: `outputs/dcs_ts/pr048_result.json` — two keys ADDED, none changed, none removed (B.2).
It is named here rather than left to the ` M` list, because a file the status output cannot show is
exactly the kind that gets omitted from a handover.

Nothing else in the tree was written. `scripts/dcs_ts_pr058_*`, `scripts/dcs_ts_pr059_*`, the
`ts116*` banks and the `ts_cand/ts_repair/ts_smoke` directories belong to other work and were not
touched.

---

## B.1 — C-122: control C4's `add` mode was UNINSTRUMENTED. Closed.

**Why this one was the highest priority.** `pc.AllPositionAdd` received no `stats=`, so unlike
`project_out` it produced **no liveness record at all**. C4 is the equal-magnitude orthogonal
control — the arm that separates *"this DIRECTION matters"* from *"this much PERTURBATION at this
site matters"*. A dead C4 hook — a stale layer object, a zero direction, a handle removed before the
forward — produces exactly the *"the control did not move the readout"* artifact that a **positive**
H2a wants to see. It was the last place in the intervention stack where a dead hook could score as a
clean null, and it sat in the one arm whose whole job is to be sceptical.

**Instrumented to the same standard `project_out` now meets, on Appendix A's ownership split.**

| what | where | how |
|---|---|---|
| `n_cells_edited_expected` | PRODUCER, **before** the write | `make_add_hook` counts `batch x seq` at the top of every forward from the tensor it was HANDED; `make_single_position_add_hook` counts `batch`. `n_cells_edited_realised` is counted from the slice actually written, so `realised == expected` is a real bind and not `0 == 0`. |
| `orthogonal_residual_delta_l2` | PRODUCER | `_record_edit(direction=d)` — an additive edit is `alpha*d`, so its component orthogonal to `d` must be 0 to float error. Measured, not asserted. |
| MISSING vs MEASURED ZERO | CONSUMER | unchanged and inherited: a missing field raises `NotMeasured`, a measured zero fails. `hook_stats_dict` initialises the measured floats to **`None`, not `0.0`**; the four new dose fields are initialised to `None` for the same reason (an undeclared dose and a declared dose of zero are opposite verdicts, and `realised_dose_l2_per_cell == 0.0` IS the dead-additive-hook signature). |
| `n_forward_with_destinations`, `min_projection_removed_l2` | PRODUCER | the F6 fix applies to the additive hook too, for free. |

**The dose is in GAP UNITS at this call site, and that is now DECLARED and CHECKED — both ways.**

`score_behavior.py`'s second `AllPositionAdd` call site passes `alpha * g`, where
`g = gaps[L]` is the difference-of-means gap for the arm's own base direction (Q13's `gaps` alias,
not `d_surface`). `make_add_hook` normalises its direction, so the alpha it receives is an
**absolute** residual magnitude and `alpha * g` is what makes `alpha=1` mean *one difference of
means*. **Verified, on the real `make_intervention` path with a toy layer:**

```
[score] ADD DOSE v_bomb_specific L9: alpha=1 x unit=2.500000 -> EFFECTIVE MAGNITUDE 2.500000
scope S2 | mode add_all    | viol [] | alpha 2.5 gapunits 1.0 gap 2.5 | realised/cell 2.5000
scope S1 | mode add_single | viol [] | alpha 2.5 gapunits 1.0 gap 2.5 | realised/cell 2.5000
                                     | abs [7] rel_end -3
```

and the other way, which is the direction that matters — a **bare** `alpha` at this call site
injects an absolute magnitude under a gap-unit label. At L18 that is a 14.65x overdose from an
identical-looking flag (RETRACTION F-3), and this repository has written it at this exact second
call site before. It is now refused **at construction**:

```
AllPositionAdd: the hook was handed alpha=1 but the caller declares 1 GAP UNITS x gap_norm 2.5
= 2.5. A bare alpha at this call site injects an ABSOLUTE magnitude under a gap-unit label --
the RETRACTION F-3 arithmetic. Refusing to build the hook.
```

Two independent binds, neither a threshold on a scientific quantity: (1) the caller declares
`alpha_gap_units` and `gap_norm` and the absolute `alpha` must be their product — this catches the
flag arithmetic; (2) `realised_dose_l2_per_cell`, the L2 of the change actually **written** to a
cell, is MEASURED in the hook and must equal `alpha` — this catches a hook body that disagrees with
its own manifest, which (1) alone cannot see. The second bar is 5% relative and is **numerical, not
scientific**: the add is computed in the model's dtype (bf16 on the L40S nodes), while the error it
exists to catch is a gap FACTOR of 1.6x–2.6x at these layers.

**C4 also gained a real single-site form.** `edit_positions` was `project_out`-only, so
`c4_samenorm_orth_s1` would have been an **all-position** edit under a single-site label — the
silent-larger-intervention shape this phase refuses everywhere else. `pc.SinglePositionAdd` is the
additive mirror of `SinglePositionProjectOut`, with the same three-argument site contract
(`pos` / `rel_end` / `seq_len_at_resolution`, identity asserted at construction) and the same
copy-before-write detail. Measured: the all-position hook moves 9 of 9 positions, the single-site
hook moves 1.

**One deliberate, recorded behaviour change.** `AllPositionAdd` now resolves its layer through
`pair_common._resolve_layer` instead of indexing `dc._get_layers(model)` directly — the same helper
`AllPositionProjectOut` uses. For every real model the two are identical; the difference is that
`_resolve_layer` falls back to a hookable object, which is what lets the additive hook be
unit-tested on CPU **against the real hook function** rather than a re-implementation of it (C-13
lived in exactly that gap). It inherits review **F8**'s residual: an architecture that makes
`_get_layers` raise would be hooked whole-model. Not reachable for the Qwen/Llama models in play,
and it is now the same residual the project-out hook already had rather than a new one.

**Not touched, and why:** the *first* `AllPositionAdd` call site (`refusalness`, dosed in units of
the direction's own norm) passes no `stats`, so it is default-off and byte-identical;
`AllPositionAddMultiLayer` has no PR-057 caller and was left alone.

### Constructibility

**26 → 28 (after Appendix A's C5 fix) → 30.** Both C4 arms are now constructible:

```
--plan --split test:  54 arms, 30 constructible today, 24 unbuildable
newly constructible:  c4_samenorm_orth_s1, c4_samenorm_orth_s2
```

The runner's `build_argv` also stopped hard-coding `"project_out"` as the launched mode. That was
correct only while `add` was unbuildable; with C4 constructible it would have launched the
equal-magnitude **orthogonal** control as a **projection** — a different intervention under the
control's name, and one that would have passed the direction check. C5 remains the single arm whose
launched mode (`project_out` + `--pr057-disable-hooks`) differs from its manifest mode, which is
what the analyzer's own `launch_command` writes and what `assert_argv_agrees_with_analyzer`
compares.

The remaining 24: 16 H1 + 2 C7 (`patch` has no code path, and under C-112/R-116 the H1 population is
empty), 4 H2b (`component_replace` has no code path), 2 C2 (no shuffled-label direction in the
PR-053 payload). Each is refused by name.

---

## B.2 — C-118(b): the FROZEN_PROBE artifact, exported without re-running the inference

`outputs/dcs_ts/pr048_result.json` was produced **before** the Q10 export block existed, so it
carried no `FROZEN_PROBE` and O1 had no estimator to score against. Re-running the analyzer costs
~7.8 h of CPU in the permutation alone and re-reads the TEST split for a number already published.

`--export-frozen-probe-only` was added instead. It:

* **reads the frozen selection rather than recomputing it** — layer 9, C=0.01, taken out of the
  existing result file. Re-selecting would be a second look at validation and could move the layer.
  It is read at the TOP of `run_probe`, before a single representation is loaded, so a missing or
  malformed result refuses before the expensive part — and so the representation load can be
  narrowed to **the selected layer only** (the 9-layer grid otherwise accumulates
  6780 x 9 x 5120 float32 twice over; on this shared node that was an OOM kill, observed);
* re-fits the OBSERVED pass at that selection and **verifies the re-fit reproduces the published
  number BIT-FOR-BIT** before anything is written;
* **does not re-run the permutation.** The published null is carried through untouched;
* exports the estimator through the **same** `_finish_probe_export` the full run now uses — one
  probe builder, two callers, so the two cannot drift into exporting different estimators under one
  name;
* writes **non-destructively**: every guard raises before the write (review F5), and the write goes
  to a temp file in the same directory and is `os.replace`d in, so a crash mid-write cannot truncate
  the published result either.

**Observed:**

```
--export-frozen-probe-only: SELECTION IS NOT RECOMPUTED. Taking layer=9 C=0.01 from
outputs/dcs_ts/pr048_result.json; re-selecting would be a second look at validation.
Loading layer 9 ONLY.
RE-FIT at the frozen selection: observed domain-mean accuracy = 0.939855072463768
PUBLISHED in outputs/dcs_ts/pr048_result.json:                 0.939855072463768
bit-for-bit identical: True   per-domain disagreements: 0
permutation: NOT RE-RUN. The published null is carried through from the existing file unchanged.
```

Diff of the artifact before/after, by key: **added `FROZEN_PROBE`, `_frozen_probe_export`;
removed nothing; changed nothing.** The probe: layer 9, C=0.01, feature_dim 4096, classes
`['bomb','knife','gun']`, fit on 4020 TRAIN rows over 67 TRAIN domains, sha256
`c54bd39765aaa40140480717b5a3f170e948d301b94c46c674addc9710eb8e4e`, self-verification
**0 disagreements over 1380 test rows** (predictions recomputed from the exported
`coef`/`intercept`/`scaler` alone, not from the sklearn objects).

The reproduction gate is a module-level function (`assert_refit_reproduces_published`) so the
self-test can prove it fires, and it is **bit-for-bit, not a tolerance**: a probe that reproduces
the headline "to six decimal places" is a different probe. Four new self-test cases cover it,
including a re-fit that differs in the 15th decimal and one whose headline matches while a single
per-domain accuracy does not.

**Review F4 is now closed too, as a side effect.** `load_frozen_probe(expect_sha=...)` has always
been able to refuse a re-fitted probe and **no caller ever passed a sha** — the repo's own
"threshold published but never enforced" shape. The runner reads the sha off the artifact it just
gated and puts `--pr057-probe-sha` in every arm's argv, so an artifact swapped between the gate and
the node is refused **at the node**.

---

## B.3 — C-118(a): O1's attribution. The blocker's stated reason was half wrong, and it is closed.

The recorded reason was: *"ProbeReadCapture is a read hook on a layer and `score_behavior` exposes
NO per-row callback; one row produces many forwards (variant batches), so order-based attribution
would be the exact silent misalignment this phase refuses."*

**The first half is wrong.** `score_behavior` builds its interventions **inside the row loop** — it
must, because the edit site is end-relative and is resolved against the row's own length — and its
`PR057_LIVENESS.jsonl` writer already stamps `prompt_id` and `domain` from exactly that scope. The
read hook is now built there too and handed the row's metadata, so **attribution is by construction
and never by the order records arrive in**. A record that cannot name its domain cannot form a
domain-level O1; these can.

**The second half is real, and it is closed by pinning rather than by ordering.** One row makes many
forwards of DIFFERENT lengths, so a hook resolving `seq_len + rel_end` internally reads a DIFFERENT
TOKEN on each of them and O1 would be a mean over several tokens. Two changes:

* `ProbeReadCapture(abs_index=, seq_len_at_resolution=)` **pins** the site to the index resolved
  against the ROW's prompt — the same number, computed by the same arithmetic, that the edit hook
  is given, so read and edit are at the same token by construction. The end-relative contract is the
  same three-argument one `SinglePositionProjectOut` carries: the offset is the record, the absolute
  index is the input, and `seq_len_at_resolution + rel_end == abs_index` is asserted at
  construction. A pin without the length it was resolved against is refused — an unaudited absolute
  index is the bug class the pin exists to avoid.
* **ONE record per row per layer**, and the invariant that makes that sound is CHECKED rather than
  assumed. The model is causal and `signals.string_option_readout` **right**-pads over a shared
  context prefix (`# LEFT padding would shift the context; pad on the RIGHT`), so a prompt position
  cannot see the variant appended after it and every forward of a row must read the same state.
  Every capture is hashed; a row whose forwards disagree at the pinned index is **REFUSED**, not
  averaged. If that assumption ever breaks — a left-padding change, a template that inserts rather
  than appends — the run stops instead of reporting a mean over several different tokens.

**Verified on CPU against the real `ProbeReadCapture`:** two forwards of lengths 11 and 15 produce
`n_forward_calls=2, n_captures=2, records=1`, at pinned index 8, carrying `domain='warehouse'`.
Unpinned that hook would have read index 8 on one forward and index 12 on the other.

**`--emit-probe` is therefore no longer refused.** `probe_gate` now returns `ok=True` when the
artifact loads, and the Q1 dry run emits the full argv:

```
--pr057-probe-out auto --pr057-probe-json outputs/dcs_ts/pr048_result.json
--pr057-probe-sha c54bd39765aaa40140480717b5a3f170e948d301b94c46c674addc9710eb8e4e
--pr057-probe-read-layers 7,8,9,10,11,12,13,14 --pr057-probe-rel-end=-10
--pr057-probe-source knife --pr057-probe-target bomb
```

The read layers come from the frozen `read_site.read_layer_grid` and the offset from
`read_site_rel_end(pr)`; the source/target come off the ArmSpec's own
`source_concept`/`target_concept`. No literal here.

### The honest limit on B.3, stated before it is used

**The `score_behavior` half of the O1 capture has never run against a model.** What has been
verified on CPU is: the flags parse (14 `--pr057-probe*` entries in `--help`); the frozen probe
loads and the **sha pin refuses a wrong sha**; the hook itself behaves as described, against the
real `ProbeReadCapture` (four self-test checks, three mutations); and the runner's `--dry-run`
constructs and validates the whole argv. What has **not** been exercised is the in-loop wiring
itself — the per-row construction and the record writer — because that needs a loaded model.

There is also one assumption it shares with the **edit** path and does not remove: the readout
scores `templated + answer_prefix`, so a token-boundary merge at that join would move both the read
and the edit together. That is pre-existing, it is not made worse here, and both now write the
resolved index down so it is visible in the artifact.

**Consequence:** O1 is **capturable** — it is no longer CANNOT ANSWER by construction — but the
capture must be proved by the **smoke stage (Q7)** before any O1 number is reported. O2, the
primary, is unaffected either way, and **Q1 does not need O1.**

---

## B.4 — Verification, with the numbers observed

| command | before (Appendix A) | **observed now** |
|---|---|---|
| `scripts/dcs_ts_pr057_causal.py --self-test` | 77 checks, 0 FAILED | **86 checks, 0 FAILED** |
| `scripts/dcs_ts_pr057_causal.py --mutate` | 52/52 RED | **64/64 RED** |
| `src/boombness/pr057_run_causal.py --self-test` | 50 checks, 0 FAILED | **53 checks, 0 FAILED** |
| `src/boombness/pr057_run_causal.py --mutate` | 28/28 RED | **28/28 RED** |
| `src/boombness/pr057_run_causal.py --plan --split test` | 54 arms, 28 constructible | **54 arms, 30 constructible, 24 unbuildable** |
| `scripts/dcs_ts_pr048_analysis.py --selftest` | 16/16 | **20/20 guards reachable** |

The baselines in the "before" column were re-measured at the session's start commit `97fdf678`
(77/0, 52/52, 50/0, 28/28, 28 constructible, 16/16) rather than quoted from Appendix A.

**The new mutations the task asked for, each observed RED:**

```
M53 C4: an add hook that never fired (dead C4)            -> hook_never_ran:n_forward_calls==0
M54 C4: add dosed in ABSOLUTE not gap units               -> add_dosed_in_ABSOLUTE_units
M55 C4: add whose dose units were never declared          -> add_dose_units_NOT_DECLARED
M56 C4: realised per-cell magnitude != declared alpha     -> add_realised_dose_!=_declared
M57 C4: realised per-cell magnitude NEVER MEASURED        -> ..._NOT_MEASURED
M58 C4: AllPositionAdd handed a BARE (absolute) alpha     -> refused at CONSTRUCTION
M59 C4: SinglePositionAdd whose rel_end names another tok -> refused at CONSTRUCTION
M60 C4: SinglePositionAdd given a NON-NEGATIVE rel_end    -> refused at CONSTRUCTION
M61 C4: half a dose declaration (gap_norm, no gap units)  -> refused at CONSTRUCTION
M62 O1 read pinned with no seq_len_at_resolution          -> Refusal (the pin is unauditable)
M63 O1 read pin that is not seq_len + rel_end             -> Refusal
M64 O1 read site MOVED between a row's forwards           -> Refusal (never averaged)
```

`M25_probe_without_artifact` was **re-pointed, not deleted**: it used to aim at the real result
file, where it was reachable only because that file had no `FROZEN_PROBE`. Now that the block
exists, leaving it there would have made it GREEN — an unreachable refusal dressed as a passing
test. It aims at an absent artifact, which is the condition the guard is actually for. Likewise the
self-test's `unbuildable_add` check was **inverted, not deleted**: C4 must now be constructible at
BOTH scopes, because a C4 buildable only all-position would be an all-position edit under an S1
label.

**Repo tests — what completed, honestly.** The node was heavily contended throughout (load average
~130, 112 users, ~2 GB RAM free; one background run was OOM-killed and is reported as killed, not as
a pass). Only runs that went to completion are reported, all against the final state of all five
code files.

| invocation | **observed** |
|---|---|
| `pytest -q -p no:randomly` over the 5 `doublespeak_causality/tests/` files that drive the changed hooks (`test_projectout_hook_synthetic`, `test_singleposition_projectout_synthetic`, `test_hook_firing_synthetic`, `test_resolve_positions_synthetic`, `test_alladd_hook_synthetic`) | **43 passed, 0 failed, 26.77 s** |
| `pytest -q -p no:randomly` over the 12 `tests/` files that drive `make_intervention` and the readout — `test_donor_patch`, `test_option_mass_gate`, `test_prompt_id_exclusions`, `test_readout_liveness`, `test_cell_residual_dose`, `test_knockout_liveness_gate`, `test_band_range_and_abort`, `test_silent_failures`, `test_composed_knockout`, `test_scoped_knockout_wiring`, `test_nondemo_control_draws`, `test_intervention_liveness` | **248 passed, 0 failed, 221.44 s** |

**The whole-root suite was NOT re-run and nothing is claimed for it.** An earlier session
established that `pytest` at this repo root does not collect (8 collection errors, 0 tests), and its
`--ignore`-ed variant takes far longer than this node allows. A cancelled run is not a pass.

---
## B.5 — `git status --porcelain`, UNSCOPED, at the end of this session

Reproduced verbatim, because omitting one modified file left HEAD unable to import earlier in this
sprint. The untracked `data/boombness_prompts/**` entries are another writer's and were **not**
touched by this work; they are shown because the listing is unscoped, which is the point of it.

```
 M doublespeak_causality/pair_common.py
 M reports/DCS_TS_PHASE9_INSTRUMENT_REVIEW.md
 M scripts/dcs_ts_pr048_analysis.py
 M scripts/dcs_ts_pr057_causal.py
 M src/boombness/pr057_run_causal.py
 M src/boombness/score_behavior.py
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_knife.jsonl
?? data/boombness_prompts/demo_pools_116dom_ts_bomb.json
?? data/boombness_prompts/demo_pools_116dom_ts_gun.json
?? data/boombness_prompts/demo_pools_116dom_ts_knife.json
?? data/boombness_prompts/ts_cand/
?? data/boombness_prompts/ts_repair/
?? data/boombness_prompts/ts_smoke/
```

**Not shown by that command, and therefore stated here:** `outputs/dcs_ts/pr048_result.json` was
modified (two keys added, nothing changed or removed). `outputs/` is gitignored
(`.gitignore:11`), so `git status` cannot surface it and a reader of the ` M` list alone would
miss the one artifact this session wrote.

---

## B.6 — What still blocks the Q1 validation submission

1. **Nothing in this appendix.** Both blockers the task named are closed: C-122 (C4's `add` mode
   uninstrumented) and C-118 (both halves — the attribution point and the missing `FROZEN_PROBE`).
   The Q1 stage is 2 arms (`h2a_s1_projout_*`), 230 rows each, and `--dry-run` constructs and
   validates both with `--emit-liveness --emit-probe`.
2. **`--dry-run` must be re-run on the shared filesystem immediately before submission**, as
   before.
3. **The instrument is again uncommitted working-tree state** (six modified files plus one ignored
   artifact). Given F1 — a commit that did not import — that provenance should be committed before
   GPU time is spent, by the session that owns the tree, under the house's path-limited
   `git commit -- <paths>` rule.
4. **O1's `score_behavior` wiring has not run against a model** (B.3). It does not block Q1 — Q1's
   outcome is O2 — but the **smoke stage (Q7)** must exercise `--emit-probe` before any O1 number is
   reported.
5. **Carried over, unchanged:** C-113 (the frozen `directions.artifact.path` can never load; the
   runner uses the directory and lets the loader join) and **24 of 54 arms unbuildable**, each
   refused by name (16 H1 + 2 C7, 4 H2b, 2 C2).
6. **F5 is now closed for the export path** (guards raise before an atomic replace) and **F4 is
   closed** (`--pr057-probe-sha` is supplied by the runner). **F7** and **F8** remain as recorded in
   A.5.
