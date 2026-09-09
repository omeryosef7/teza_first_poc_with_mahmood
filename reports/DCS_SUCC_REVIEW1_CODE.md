# DCS-SUCC-REVIEW-1 — ADVERSARIAL CODE REVIEW of the 2026-09-09 successor session

Reviewer: independent read-only agent. Scope: everything written or modified in the session that
produced commits `9b74e475 .. 130d3684`. Nothing was fixed, nothing was modified, no GPU or SLURM
job was submitted. `VERIFIED` = I ran the check or read the producing artifact. `INFERRED` = I
reasoned it from source without executing the failing path.

Files under review:

| file | status |
|---|---|
| `src/boombness/aggressive_patching.py` | MODIFIED (PR-068) |
| `src/boombness/kladder_run.py` | new |
| `scripts/dcs_succ_bombness_candidates.py` | new |
| `scripts/dcs_succ_pr068_preflight.py` | new |
| `scripts/dcs_ts_make_exclusions.py` | new |
| `scripts/dcs_succ_pr066_behaviour.py` | new (agent-written) |
| `scripts/dcs_succ_kladder_analysis.py` | new (agent-written) |
| `configs/dcs_ts_pr066_behaviour.json` | new FROZEN preregistration |

---

## RANKED FINDINGS

### F1 — CRITICAL. `PR-068` KILLED THE TRANSPLANT ARM OF BOTH HISTORICAL PAIRS. The log's claim that they are "byte-for-byte unchanged" is FALSE.

`src/boombness/aggressive_patching.py:1026-1047`, `donor_positions()`. The token-identity assertion
is **not** guarded by `align_mode`:

```python
if align_mode == "absolute":
    dp = list(rpos)
else:
    dp = [len(d_ids) + (p - len(r_ids)) for p in rpos]
for rp, dpi in zip(rpos, dp):
    if not (0 <= dpi < len(d_ids)):            # line 1039
        ...
    if d_ids[dpi] != r_ids[rp]:                # line 1042  <-- UNCONDITIONAL
        ledger.fail(f"patch_token_identity_differs:...")
        return None
```

The two historical pairs are, by construction, pairs whose donor and recipient carry **different
tokens** at the patched position:

* `harm_ctx = (direct_harmful, natural_doublespeak)` — donor `target_surface = "bomb"`,
  recipient `target_surface = "button"` (VERIFIED over the whole bank:
  `('direct_harmful','bomb')` / `('natural_doublespeak','button')`, all 22272 rows).
* `benign_ctx = (concept_in_benign_ctx, benign_literal)` — donor `"bomb"`, recipient `"button"`.
* On the module's own `DEFAULT_BANK` (`boombness_prompt_bank.jsonl`) it is `bomb` vs `carrot`
  (VERIFIED).
* Those are distinct single tokens: job 872577 printed
  `readout ids (whole_answer): concept=[13054] codeword=[3215]` (VERIFIED).

So under `absolute`, `d_ids[dpi] != r_ids[rp]` is **true for every scope of every family**,
`donor_positions()` returns `None`, and `run_pair` line 1091 does `continue`. **The entire
`transplant` family emits zero rows** for `harm_ctx` and `benign_ctx`. (INFERRED — no GPU run of
the old pairs exists in this session to observe it — but the inference is arithmetic, not
probabilistic.)

Worse, **the run still exits 0**: `baseline` (`intervention="none"`), `donor_ceiling` and
`self_swap_noop_check` are emitted *before* `donor_positions()` is ever called
(`aggressive_patching.py:1049-1082`), and `GATED_INTERVENTIONS = ("none", "donor_ceiling")`
(line 598) — so `option_mass_gate` sees both of its gating buckets, reports `PASS`, and
`run.finish` writes `n_rows > 0`. The loss is visible only as a ledger reason count. This is
exactly the "a gate that passes on an empty selection" shape the module's own docstring at line 158
says it fixed.

Entry 013 of the authoritative log states: *"Under `absolute` it is the identity map, so nothing
changes for the old pairs."* The **index map** is the identity; the **assertion** is new and
unconditional. The commit message repeats the same claim.

Answering the review's sub-questions on (d) directly:

* Is `donor_positions()` the identity under `absolute`? **The mapping is; the function is not.**
  It has a side effect (a new refusal) that the old code did not have.
* Does anything else index `donor_hs` by recipient positions? **No** — `donor_hs` appears at
  exactly two lines, 970 (creation) and 1096 (the patched read), and 1096 now uses `dpos`
  (VERIFIED by grep). The read/write split is correct.
* Is every new refusal reachable? **Three of the six are dead:**
  - `unknown_align_mode` (line 917) — `align_mode` comes only from `PAIR_ALIGNMENT`, whose only
    values are the two accepted literals; `run_pair`'s default is `"absolute"`. Unreachable.
  - `donor_position_out_of_range` (line 1040) — under `end_relative`, the preceding checks force
    `-S <= r_rel = d_rel <= -1` and `len(d_ids) >= S`, so `dpi ∈ [0, len(d_ids)-1]` always; under
    `absolute` the length equality is already asserted. Unreachable in both modes.
  - `scope_not_constructible_under_end_relative` (line 952) — `main()` raises `SystemExit` on the
    same condition (line 1407) before `run_pair` is called, reading the same `args.scopes`. Only
    reachable through a whitespace mismatch (`main()` strips each scope, `run_pair` receives
    `args.scopes.split(",")` **unstripped**, line 1480), which is itself a latent inconsistency.

**Consequence:** the next run of `--pairs harm_ctx,benign_ctx` — the default — silently produces a
transplant-free artifact that looks healthy.

---

### F2 — CRITICAL. `PR-068` CANNOT RUN ON `ts116m` AT ALL, AND IT ALREADY FAILED. The preflight validated a population `aggressive_patching` cannot select.

`src/boombness/aggressive_patching.py:1277-1279`:

```python
rows = [r for r in rows if r["query_kind"] == args.query_kind and r["n_examples"] in want_n
        and r["bank_block"] == "core2x2"]
```

`bank_block == "core2x2"` is a hard-coded literal that PR-068 did not touch. The `ts116m` bank
carries **no** `core2x2` block — VERIFIED, its blocks are
`{cds_n4: 9280, cds_n4_sow: 4640, cds_n8: 3712, cds_n0: 2784, cds_n8_sow: 1856}`. Only the legacy
`boombness_prompt_bank.jsonl` has `core2x2`.

VERIFIED in the artifact and the job log:

* `outputs/boombness/aggressive_patching/pr068smoke_20260909_220845_3917795/` contains **only**
  `config.json`, `RUNMETA.json` and an empty `plots/` — no `rows.jsonl`, no `summary.json`, no
  `DONE.json`.
* `outputs/boombness/logs/boomb_872575.err` (the re-run of the smoke after 872548 was cancelled)
  ends with:
  `the selected bank slice carries 0 distinct (concept, codeword) pairs, ...`
  i.e. `assert_single_concept_codeword_pair([])` at line 1362.

So `PR-068` loaded 8 B of weights, selected zero rows and died. **This is not recorded anywhere in
`external_md/...20260909.md`** — entry 013 still reads "built and proved constructible", and the
run's failure is a negative that has not been appended (§41).

The deeper defect is in the preflight: `scripts/dcs_succ_pr068_preflight.py` re-implements
`run_pair`'s **per-row** preconditions (P1–P8) faithfully — I checked its P6 against
`donor_positions()`'s mapped index and they are equivalent given P4 — but it never touches
`main()`'s **population selector**. It filters on `query_kind`, `n_examples`, `domain` and `cell`
(lines 79-81) and never on `bank_block`. A preflight that reproduces the checks but not the
selection cannot answer "will this arm bind any families", which is the one question it exists to
answer. `n_families_constructible: 670` in `outputs/dcs_succ/pr068_preflight.json` is a true
statement about a set of rows that the runner discards before it looks at any of them.

Two more mismatches between the preflight and the runner, both currently latent:

* the preflight keys `by_family[family_id][cell]` (line 82) with **no duplicate guard** — the
  `D-001` shape. Currently safe (VERIFIED: 2320 (family_id, cell) pairs, 2320 distinct, max dup 1),
  but unguarded.
* the preflight restricts to TRAIN domains; `aggressive_patching.main()` has **no split filter at
  all** (VERIFIED by grep: no `--split`, no `dsplit`, no exclusion handling), so its round-robin
  family selection at line 1425-1435 will happily draw recipients from validation and test domains.
  For the historical pairs on the legacy bank there is no frozen split, so this is new exposure
  introduced by pointing the module at `ts116m`.

---

### F3 — HIGH. `kladder_run.py`'s `--split` flag does not select the population, and its `test` refusal is cosmetic.

`src/boombness/kladder_run.py:154` declares `--split` with `choices=["train","validation"]`, and the
module docstring (line 46) says *"This file refuses `test` outright."* What actually selects the
population is `--exclude-prompt-ids` (line 151), a free-form path. `argv_for()` (lines 125-136)
**never passes `--split` to `score_behavior`** (VERIFIED — `score_behavior` has no `--split`
argument). `a.split` is used only to name the manifest file (line 176) and to be echoed into
`man["args"]`.

Therefore:

* `--split validation` runs the **train** exclusion file and writes a manifest that says
  `"split": "validation"`. Nothing refuses.
* a `test` exclusion file passed as `--exclude-prompt-ids` runs test rows under a manifest that
  says `train`. The `choices=` refusal never sees it.

The sibling analyzer knows this — `scripts/dcs_succ_kladder_analysis.py:697-702` refuses when
`split == "train"` and `"train" not in os.path.basename(exclude_prompt_ids)`, with a comment
naming the disconnect explicitly. That is a substring test on a filename, and it is only applied
when `split == "train"`; it is a plaster on a hole in the runner, not a fix. The runner should
derive the exclusion path from the split, or refuse when they disagree.

---

### F4 — HIGH. `kladder_run.py`'s "an arm must not take down the ladder" guarantee is broken by a string-coded `SystemExit`.

`src/boombness/kladder_run.py:191-199`:

```python
try:
    rc = SB.main()
except SystemExit as e:            # score_behavior refuses with SystemExit
    rc = int(e.code or 0)
except Exception as e:             # noqa: BLE001 -- an arm must not take down the ladder
    rc = 99
```

`score_behavior` raises `SystemExit` with **message strings**, not integers — e.g.
`score_behavior.py:2337`, `:2355`, `:2360`, `:2415`, all `raise SystemExit("[score] REFUSING: ...")`.
`int("[score] REFUSING: ...")` raises `ValueError` **inside the `except SystemExit` handler**, which
Python does not route to the sibling `except Exception` clause (VERIFIED by direct experiment). The
exception escapes the `for` loop: the arm's record is never appended to `man["arms"]`, `finished`,
`model_loads` and `model_cache_hits` are never written, and every remaining rung is lost.

That is precisely the `PR-065` stop-scope failure the entry-009 log text claims this runner fixed
"by construction rather than inherited". The only refusals it survives are the integer-coded ones
(the `rc=4` option-mass gate).

---

### F5 — HIGH. `dcs_succ_pr066_behaviour.py`'s `--installation-run` override defeats the only thing that makes `Q2`'s join compound.

The preregistration and the code both declare the `Q2` join key as
`(bank_file_sha16, domain)` — `configs/dcs_ts_pr066_behaviour.json:primary._the_join_is_domain_level...`,
and `scripts/dcs_succ_pr066_behaviour.py:1176` (`"_join_key": "(bank_file_sha16, domain) -- COMPOUND"`)
and `:1080` (`"_join": "(bank_file_sha16, domain)"`).

The code never builds that key. `analyse()` (lines 1481-1487) joins `inst["x"]` and `y`, both
plain `{domain: value}` dicts, on `set(x) & set(y)`. The digest is carried as a **label only**;
`inst["bank_file_sha16"]` is never compared to `arm.bank_sha`.

On the default path this is inert: `check_generation_provenance` pins every arm to
`bank_pin(pr, ...)["bank_file_sha16"]` (line 693) and `bind_installation_run` selects the readout
run by the same digest (lines 1112-1124), so both sides are independently pinned. **The
`--installation-run DIR` override (lines 1107-1111) returns the directory without checking its
digest at all.** A `basket_bomb` (or `button_knife`) readout run passed there would join cleanly:
`A-101.1` records that the neighbouring banks share **116/116 domain names** and 0/1160
prompt_sha16 — the domain names are exactly the part that is *not* discriminating. The result is a
silently wrong `rho` with a full provenance block that records the wrong bank's digest beside it
and refuses nothing.

Two lines would fix it (compare `inst["bank_file_sha16"]` to `arms[("C", top)].bank_sha` and
refuse), and the file's own `--mutate` already proves it knows how to catch this class
(`RED join on prompt_id alone (no bank digest)` — VERIFIED, 5/5 sabotages caught).

---

### F6 — MEDIUM-HIGH. `dcs_ts_make_exclusions.py` prints a domain count that is not the domain count — the exact `D-002` defect, in a script written the same session `D-002` was fixed.

`scripts/dcs_ts_make_exclusions.py:103-104`:

```python
print("wrote %s: selected=%d excluded=%d remain=%d domains_remain=%d exclusion_sha16=%s"
      % (a.out, sel, len(exc), sel - len(exc), len(doms - set(EXCLUDED_DOMAINS)), sha))
```

`domains_remain` ignores `keep_domains`, i.e. it ignores the `--split` filter that produced the
exclusions. VERIFIED by re-running the exact command that produced the committed train file
(output written to scratch; the committed file is byte-identical):

```
wrote ...: selected=1160 excluded=490 remain=670 domains_remain=113 exclusion_sha16=b3ba3d5ea6c91d34
```

670 rows over 113 domains is arithmetically impossible (the bank has 10 rows per domain per block).
The **file header** written by the same function (lines 90-96) is correct — it says
`670 rows remain over 67 domains`. So the operator's console says 113 and the artifact says 67.
That is the same "published a count that is not the count analysed" shape as `D-002`, which the
session had already found and fixed in `dcs_succ_bombness_candidates.load_bank` hours earlier.

Related, smaller, in the same file: the `if not exc:` refusal (line 68) fires only when the
exclusion list is **completely** empty. If one or two of the three preregistered whole-population
domains are absent from a selection, the list is non-empty and the missing exclusions are silent.
A gate on "all three of `EXCLUDED_DOMAINS` were present and removed" is the gate that was intended.

---

### F7 — MEDIUM. `dcs_succ_bombness_candidates.py` assumes, and never checks, that the six extraction caches agree on layers, position and layer convention — and it hard-codes `position` into the artifact.

* `scripts/dcs_succ_bombness_candidates.py:278` — `layers = banks["bomb"]["layers"]`, and every
  subsequent `[L_i]` index is applied to all three concept banks' tensors. There is **no** check
  that `banks["knife"]["layers"] == banks["bomb"]["layers"]`. A mismatch would silently compare
  layer 6 of one bank with layer 11 of another and produce a plausible number.
* `blob["position"]` and `blob["layer_convention"]` are read into `meta` (lines 151-153) and never
  compared — neither across banks nor against what the artifact claims.
* `main()` writes `"position": "codeword_last"` into the result JSON as a **literal string**
  (line ~723), independent of what the caches actually contain.
* `meta["token_text_by_cell"]` is collected (line 148) and never asserted. The whole `B1`
  construction rests on the token being ` button` in cells A and C and ` bomb` in B and E; the data
  to prove it is gathered and then only printed.

Currently all six caches agree (VERIFIED with torch: `layers [6..14]`, `position codeword_last`,
same `layer_convention`, and the committed artifact's `token_text_by_cell` is correct in all 24
cells). So this is an unguarded assumption, not a live wrong number — but it is unguarded on
exactly the axis (`layers`, `position`) where a re-extraction would break it silently.

Two smaller items in the same file:

* `line 147` — `if len(rows) != n_selected: raise Refusal(...)` is **dead**. The duplicate-key
  refusal at line 138 already guarantees `len(rows) == n_selected`; the count guard the `D-001`
  entry credits with turning the mistake into a refusal can no longer fire.
* `line 507` — `frac_kept = frac_kept_by_concept["bomb"]` is assigned and never used (the dict is
  what goes into `axis_geometry`). Dead.
* the gap normaliser is **not** leave-one-out. `gap[c]` (line 287) and `gap_harm` (line 367) are
  full-sample means including the domain being scored, while the file's headline discipline is
  "EVERY REFERENCE DIRECTION IS LEAVE-ONE-DOMAIN-OUT". The numerator is LOO, the denominator is
  not. The leakage is small (`D-003` measured LOO leakage at ~1 %) but the claim is stated without
  qualification.
* the log's entry 008 says *"The module **refuses** `--split test` outright."* It does not:
  `--split` accepts `test` (line 686) and is gated by `--i-am-the-frozen-analyzer`. An escape hatch
  is defensible; describing it as an outright refusal is not.

---

### F8 — MEDIUM. `kladder_run.py`: `--allow-tail-readout` is dead, and `--control-ks` silently drops rungs.

* `src/boombness/kladder_run.py:161` declares `--allow-tail-readout`; `argv_for()` never emits it
  (VERIFIED — the flag appears nowhere else in the file). An operator who passes it expecting the
  option-mass gate to be overridden gets no change and no warning.
* `build_arms` line 116: `if k in ctrl_ks` — a K named in `--control-ks` but absent from `--k-list`
  produces no control arm and no message. The downstream analyzer builds its expected arm list from
  `control_ks × draws` (`dcs_succ_kladder_analysis.py:717`) and would then refuse with
  `MISSING ARM(S)` rather than with the real cause.

---

### F9 — MEDIUM. The rung→token map is asserted, not re-derived, and the artifacts the runner chose cannot check it.

Answering sub-question (e) precisely. I did **not** trust the map; I checked
`score_behavior`'s own selector and then the realised artifacts.

* the selector for `--knockout-scope query_last_k_rows` is `sorted(prot)[-K:]` where `prot =
  query_span_positions(...)` — `score_behavior.py:3385-3387` (per-row) and `:2866-2868`
  (pre-flight), one definition each side.
* `query_span_positions` (`:1041-1067`) returns every token whose char-end lies at or after the
  start of `final_query_text`, i.e. a contiguous suffix of the sequence.
* **VERIFIED on the real run dirs** (`ts116m_sowk_K01/K02/K03/K06/K07_demo`, 670/670, 670/670,
  670/670, 670/670, 397/397 rows): `n_query_span_positions == 28` on every row,
  `query_span_bounds[1] == seq_len - 1` on every row, and the realised
  `surface_span_positions` are exactly `rel_end -K .. -1` on every row. So `QUERY_SPAN_ROWS = 28`
  and "rung K reaches `rel_end = -K`" are **correct**, and the runner's `K <= 14` control-pool
  constraint is correct.
* the **token identity** at `rel_end -10` is *not* checkable from these artifacts:
  `surface_span_decoded` / `surface_span_rel_end` are written only on the declared-`rel_end` path
  (`score_behavior.py:3374-3379`), and the ladder uses the legacy last-K path. INFERRED-only:
  `final_query_text` ends `"...what does the word button actually refer to?"` and the chat template
  appends `<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n`, which reproduces the map
  `-1 '\n\n' … -6 '?' -7 ' to' -8 ' refer' -9 ' actually' -10 ' button'` exactly.

The analyzer states this limitation honestly and prominently
(`dcs_succ_kladder_analysis.py:44-52`, and again in the result's `limitation` field) and
`_rung_geometry` (`:451-479`) proves the part that *is* provable, row by row. **That is the right
behaviour and I record it as such.** The criticism is of the runner: `kladder_run.py:76-78` claims
`REL_END_ROLE` is *"Re-derived from the frozen token-role map, NOT retyped from prose: the runner
prints it and refuses if `--k-max` would run past the query span."* There is **no `--k-max`
argument** and no refusal that compares the map to anything; the dict is retyped prose, and
switching the ladder to `--knockout-rel-end-rows` would have made it checkable at zero cost.

---

### F10 — LOW-MEDIUM. Reporting and small hygiene items.

* `aggressive_patching.py:1509` — `run.finish(summary={... "pairs": list(PAIRS) ...})` still
  publishes **all three** pairs regardless of `--pairs`. `pairs_requested` was added beside it, so
  a reader sees two contradictory fields.
* `aggressive_patching.py:1480` vs `:1407` — `main()` strips scope names before the end-relative
  check, `run_pair` receives them unstripped. `--scopes " query_only"` passes the `main()` gate and
  then dies per row (end-relative) or raises an uncaught `ValueError` from
  `select_positions` (absolute).
* `dcs_succ_pr066_behaviour.py:1203-1205` — `goal_topicality` is gathered with `r.get(...)` and
  `None`s are filtered out, so a partially-missing field yields a mean over an unnamed subset. The
  count is reported (`goal_topicality_n`) and the field is explicitly labelled a diagnostic, so
  this is the mildest instance of the (b) pattern in the session — but every other field in that
  function goes through `require_field`.
* `dcs_ts_make_exclusions.py` binds nothing to the bank identity: the emitted file is a bare list
  of `prompt_id`s, and `prompt_id` is not unique across banks. The bank is recorded in a `#`
  comment only. `score_behavior` refuses ids absent from the selected population, which catches the
  common cases, but the artifact itself is not self-identifying.

---

## (f) DEAD CODE / UNREACHABLE REFUSALS / SELF-CHECKING CHECKS — consolidated

| location | what |
|---|---|
| `aggressive_patching.py:917` | `unknown_align_mode` — unreachable |
| `aggressive_patching.py:1040` | `donor_position_out_of_range` — unreachable in both modes |
| `aggressive_patching.py:952` | end-relative scope refusal — shadowed by the `SystemExit` in `main()` reading the same source |
| `kladder_run.py:161` | `--allow-tail-readout` — never forwarded |
| `kladder_run.py:154` | `--split` — never forwarded; refuses `test` only as a string, not as a population |
| `dcs_succ_bombness_candidates.py:147` | count guard made unreachable by the duplicate guard above it |
| `dcs_succ_bombness_candidates.py:507` | `frac_kept` assigned, unused |
| `dcs_succ_pr068_preflight.py` | checks `run_pair`'s per-row assertions but not `main()`'s selector — the check does not cover the thing that actually failed (F2) |

---

## (g) WOULD THE TWO AGENT-WRITTEN ANALYZERS SURVIVE THE REAL ARTIFACTS?

Both were exercised against the artifacts on disk, not only against their fixtures.

**`dcs_succ_pr066_behaviour.py` — yes, so far.**
`--selftest` PASS, `--mutate` 5/5 RED, `--plan` runs and correctly reports 5 complete arms, 3
incomplete, and binds `Q2`'s predictor to
`outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103` (all VERIFIED
by execution). The full path cannot be exercised until all eight arms land, and it refuses to
half-analyse, which is correct. The one real defect is F5.

**`dcs_succ_kladder_analysis.py` — yes.** VERIFIED against the live run dirs:

* every field in `REQUIRED_ROW_FIELDS` and `REQUIRED_KO_FIELDS` is present in the real
  `results.jsonl` (checked against `ts116m_sowk_K03_demo_*`; `knockout_scope`, `knockout_last_k`,
  `seq_len`, `query_span_bounds`, `n_query_span_positions`, `hook_*` all present);
* `mass_key = "semantic/semantic_one_word"` is exactly the bucket key in the real `summary.json`,
  and `median_true` is the field name the producer writes;
* `config_vs_argv(cfg["args"], manifest_argv)` returns `[]` on the real pair — the flag→key
  normalisation works on every flag the runner emits;
* `control_draw_seeds` **is** written by `score_behavior.py:2906` for `nondemo_matched_d*` arms
  (VERIFIED on `pr059_button_bomb_s_g_nondemo_control1_*`: `{"nondemo_matched_d2": 36100463}`), so
  the control-band provenance refusal will not misfire;
* `_rung_geometry`'s assertions hold on 670/670 rows at every rung run so far;
* run against the live mid-flight manifest, the analyzer refuses cleanly:
  *"the manifest carries no `finished` timestamp: the ladder is MID-FLIGHT."*

One design note rather than a defect: `classify_shape`'s RAMP monotonicity test iterates
list-adjacent entries (`for i in range(len(f)-1)`) rather than K-adjacent ones, which contradicts
its own declared defect-2 rule. It is unreachable today because a missing rung sets
`shape = INCOMPLETE` and returns before the monotone test runs.

---

## REUSE OF EXISTING CODE (mandate §28)

**Genuinely reused (verified by import):**

| new file | reused |
|---|---|
| `kladder_run.py` | `score_behavior.main()` driven in-process (the house readout, not a second copy); `ModelCache` from `pr059_run_localisation` |
| `dcs_succ_pr068_preflight.py` | `aggressive_patching.resolve_occurrences` / `END_RELATIVE_SHARED_SUFFIX` / `END_RELATIVE_SCOPES`; `ds_common` |
| `dcs_succ_kladder_analysis.py` | `clustered_stats.cluster_bootstrap_ci`, `clustered_stats.cluster_sign_test` |
| `dcs_succ_pr066_behaviour.py` | `asr_protocol.build_entry` / `assert_publishable` (the sole gens↔judge join), `dcs_readout_family.concept_binary_prob`, `dcs_ts_prereg.Prereg` |
| `aggressive_patching.py` (PR-068) | extended in place rather than forked — the right call |

**Written new that duplicates something already in the repo:**

* **`holm`** — `dcs_succ_kladder_analysis.py:171` and `dcs_succ_pr066_behaviour.py:888` are the
  **13th and 14th** copies of Holm–Bonferroni in this repository (VERIFIED: `def holm` also in
  `dcs_kladder_analysis`, `dcs_verify_kladder`, `dcs_ts_pr059_localisation`, `dcs_ts_pr053_diffmeans`,
  `dcs_ts_pr051_positional`, `dcs_ts_pr057_causal`, `dcs_ts_pr058_symmetry`, `analyze_g2`,
  `reanalyze_corrected`, `consolidate_phase_e`, `analyze_phase_d`, `rbd_analysis`). The kladder copy
  states a real reason (no numpy on the login node) and pins itself to the original in its selftest;
  the `pr066` copy states none.
* **the sign test and the clustered bootstrap** — `dcs_succ_pr066_behaviour.py` reimplements
  `two_sided_sign_p`, `sign_p_floor` and `cluster_bootstrap_ci`, all of which exist in
  `src/boombness/clustered_stats.py` (`cluster_sign_test`, `cluster_bootstrap_ci`) and which the
  **sibling analyzer written in the same session imports**. Two files written hours apart made
  opposite reuse decisions on the same helper, and only one of them wrote down why.
* **`dcs_succ_bombness_candidates.py`** imports nothing from the repo at all: `sign_test_two_sided`,
  `boot_ci`, `mean`, `sd`, `cohen_d_paired` are all local reimplementations of `clustered_stats`
  functionality. Its `--mutate` harness covers only four reducers (`sign_test_two_sided`,
  `loo_direction`, `_unit`, `mean`) — none of the mutations mandated by §24.8 that matter most here
  (swap bank identity, corrupt split, join wrong prompts, leak concept tokens) is present, and the
  selftest never touches `load_bank`, `domain_cell_means`, the residualisation or the prototype
  arithmetic. "4/4 RED" is a true statement about a thin family.
* **`dcs_ts_make_exclusions.py`** — no prior equivalent found; genuinely new and the right shape
  (derive, don't hand-maintain), modulo F6.

---

## WHAT I COULD NOT CHECK

* No GPU run of `harm_ctx` / `benign_ctx` exists after the PR-068 edit, so F1 is arithmetic
  inference from source, not an observed zero-row artifact.
* `PR-066`'s full analysis path (Q1 contrasts, Q2, N1–N7) cannot execute until all eight arms land;
  only `--selftest`, `--mutate` and `--plan` were exercised.
* The identity of the token at `rel_end = -10` (F9) rests on the frozen token-role map and on my
  own reading of the templated query, not on any field in the ladder's run dirs.
