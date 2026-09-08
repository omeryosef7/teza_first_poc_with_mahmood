# `DCS-PR-059` PHASE 11 — the localisation analyzer, and what U1–U6 actually close

**Written** 2026-09-07. **CPU only**, no GPU, no SLURM, no network.
**Governing file** `configs/dcs_ts_pr059_phase11.json`, status `FROZEN`, **not edited**.
**Analyzer** `scripts/dcs_ts_pr059_localisation.py` — written at **exactly** the path
`artifacts.analyzer` declares, so `PR058-D1` (analyzer written under another name, mismatch became
a blocking defect, resolved only by renaming afterwards) is designed out rather than repeated.
`analyzer_identity_gate()` is kept anyway and mutation **M40** injects the mismatch on a *copy* of
the preregistration, so the refusal stays reachable even though the conflict does not exist.

---

## 1. Observed numbers

| entry point | observed |
|---|---|
| `--self-test` | **92 checks, 0 failed** |
| `--mutate` (U6) | **80/80 RED**, every refusal reachable, each firing for its own reason |
| `--verify-token-map` (U4) | `ok=true`, **6900/6900 prompts**, `problems=[]` |
| default (no arm data) | **REFUSED**, rc=1 — "78 arm tags searched, 78 absent" |
| `--u3-inventory` | rc=2, **NOT CLOSABLE**, 0 runs on the preregistered banks |
| `--control-draws` (U2) | rc=1 — 2 of 6 scopes have **no constructible** dose-matched control |
| `--plan` | 78 arms over 2 confirmatory banks, baseline and `S_G` ordered first |
| `dcs_ts_prereg.py --check` | clean: FROZEN, 17 hashes pinned and verified, 12/12 mandate-21 fields |
| `dcs_ts_prereg.py --check --for-extraction` | **9 refusals** — U1…U8 blocking-and-not-done, plus `artifacts.analyzer_exists == false`. **Unchanged**: the config is frozen and this session does not flip either flag. |

The source-literal audit checks **12 declared gates** against this analyzer's own source text and
finds **0** numeric-literal violations. Every threshold — alpha, `n_perm`, the p-floor, the
`option_mass` gate, the power bar, the resolver tolerance, the half-of-`S_G` rule, the installation
cut, the declared MDE and all three seeds — is fetched through `Prereg.require()` or **parsed out of
the frozen file's own prose**. Mutation **M38** proves the audit fires by handing it a source that
does carry one.

---

## 2. U4 — CONFIRM or REFUTE, with counts

Re-derived from `outputs/dcs_ts/token_roles_ts116m.json.gz` per prompt, from the raw `query_roles`
arrays — **nothing imported from the design's own summary**.

* query span = `rel_end −28…−1`, **28 tokens in 6900/6900 prompts**; `n_prompts_whose_span_differs = 0`.
* role census **constant in 6900/6900** and **agrees with the config's declared census**;
  `layout_mismatches = {}` (the config's own `rel_end_layout` matches the artifact at every offset).

| scope | rows | realised roles per prompt | decoded | verdict |
|---|---|---|---|---|
| `S_A` | 5 | `chat_scaffold` 1 + `response_header` 4 | — | **CONFIRMED** |
| `S_B` | 0 | — | — | **CONFIRMED UNCONSTRUCTIBLE** |
| `S_C` | 1 | `codeword` 1 | `' button'` 3450 / `' basket'` 3450 | CONFIRMED |
| `S_D` | 22 | `answer_format_instruction` 8 + `punctuation` 3 + `user_instruction_scaffold` 11 | — | CONFIRMED |
| `S_E` | 23 | as `S_D` + `codeword` 1 | — | CONFIRMED |
| `S_F` | 1 | `user_instruction_scaffold` 1 | `' actually'` 6900 | CONFIRMED |
| `S_F2` | 1 | `response_header` 1 | `'\n\n'` 6900 | CONFIRMED (scaffold, not a substitute for `S_F`) |
| `S_G` | 28 | 8 + 3 + 11 + 1 + 1 + 4 | — | CONFIRMED |

**The two claims I was asked to confirm or refute, both CONFIRMED:**

1. **Scope A is exactly `query_last_k_rows` K=5.** `sorted(query_span)[-5:]` equals `S_A`'s declared
   `rel_end` set in **6900/6900 prompts**, and those five rows are `<|eot_id|>`,
   `<|start_header_id|>`, `assistant`, `<|end_header_id|>`, `'\n\n'` — **zero query content**.
2. **Scope B is UNCONSTRUCTIBLE.** `neutral_content` = **0 tokens across all 6900 prompts**
   (`n_neutral_content_tokens_total = 0`); `concept_word` is likewise 0. `S_B` enters
   `PHASE11_LOCALISATION` at **p = 1.0 as an absent member** (`holm_with_absent`,
   `unconstructible_members = ['S_B']`), never dropped — dropping it would shrink the family and
   make every surviving member easier to declare significant. **M43** refuses the shrunken family.

---

## 3. What each U-item now is

| item | state | detail |
|---|---|---|
| **U1** | **analyzer half CLOSED; producer half OPEN** | `surface_span_from_rel_end()` is the single definition (`selector_sites_agree()` makes "both call sites agree" structural), plus `assert_realised_equals_declared()` (L-N4, positions **and** decoded tokens) and `resolver_failure_gate()`. **The producer-side patch into `src/boombness/score_behavior.py` (two call sites) and `scripts/dcs_extract_under_ko.py` is NOT done: those files are owned by a concurrent writer in this shared tree and this session was instructed to write neither.** U1 stays BLOCKING until that patch lands. |
| **U2** | **analyzer half CLOSED; producer half OPEN** | `random_row_control_draw()` / `random_row_control_band()` — m rows from the query span excluding the scope's own rows, seeded from `seeds.random_row_draws` via `hashlib` (never salted `hash()`), reproducible across processes, **with the draw recorded** (seed, derived seed, pool, excluded rows, chosen rows). Wiring it into the runner is producer-side. |
| **U3** | **NOT CLOSABLE — and here is exactly what is missing** | see §4 |
| **U4** | **CLOSED** (subject to the config owner flipping `done`) | §2 |
| **U5** | **CLOSED** | the analyzer exists at the declared path, 92/92 self-test |
| **U6** | **CLOSED** | 80/80 mutations RED, including all eight the config names by hand |

The eight corruptions `U6` names explicitly, and where each fires:
dead hook **M1**; SDPA arm **M2**; realised row set ≠ declared `rel_end` set **M8** (and **M9** for
the decoded token); identical-hash control band **M11**; row-level p-value **M32**; scope reported
without its dose-matched control **M41/M42**; a dropped family member **M43**; a display-channel
number used as a mechanism result **M46** (and **M47** for the fallback).

---

## 4. U3 — the SD is not measurable from existing rows, and this is what is missing

`--u3-inventory` walks every completed run and binds against the preregistered banks:

* **0** knockout runs on the concept-free channel exist on **any** of the 6 preregistered `ts116m`
  banks. **29** exist off-population.
* The nearest usable rows are the `dcssow_*` family (`boombness_prompt_bank_button_bomb.jsonl`,
  `semantic_one_word`, cell C, dose 4, `demo_all:attn_knockout:6-14:1.0`, with a matched untouched
  baseline `dcssow_base_demo_*`). They are on the **concept-free** channel, so they are *not* the
  forbidden display-channel borrowing — **but they are 6 domains on a different bank**, and of those
  six only **one** (`game_manual`) is a `ts116` **validation** domain. An SD over n=1 does not exist.

Descriptive only, from those 6 domains, paired within `prompt_id` (**not** a U3 measurement, **not**
this population, **must not be entered into the frozen file**):

| arm | n domains | mean Δ `semantic_logodds` | between-domain SD | median `option_mass` |
|---|---|---|---|---|
| baseline `S_0` | 6 | — | — | 0.2129 |
| `query_prefill_only` (`S_G`-shaped) | 6 | −5.9700 | **1.2790** | 0.2283 |
| `target_surface_row_only` (`S_C`-shaped) | 6 | −2.3801 | 0.8440 | 0.3520 |
| `query_last_k_rows` K=5 (`S_A`-shaped) | 6 | −0.8655 | 0.9008 | 0.2166 |

At SD = 1.279 the declared 0.5-nat effect would have power 0.9846 at n=113, 0.8836 at n=67 and
**0.4338 at n=23** (MDE 0.7818 nats on test alone). **Two warnings that follow from these rows and
should be carried into U8:** (a) the `S_A`-shaped arm on that bank **moves** (−0.87), and a moving
scaffold-only arm is the frozen file's third kill condition — it must be checked on *this* template
before the family is trusted; (b) that bank is not this template, so the K=5 rows there are not
necessarily the scaffold rows the token map confirms here.

**What U3 needs, minimally:** the untouched baseline `S_0` and the reference scope `S_G`, both on a
preregistered `ts116m` bank, cell C, `semantic_one_word`, `n_examples=4`, over the **23 validation
domains**, paired within `prompt_id`. That is GPU work. `power.mde.in_semantic_logodds_nats` stays
`null` and **U3 stays BLOCKING**. `u3_power()` is the code path that consumes the measurement when
it exists, and returns **CANNOT ANSWER WITHOUT READING TEST** below the bar (**M26**).

---

## 5. Conflicts with the frozen config — recorded, never edited

**PR059-D1 — the per-scope random-row control is not constructible for `S_D` and `S_E`.**
`dose_matching.per_scope_random_row_control` requires, *"for every scope of size m, a SEEDED RANDOM
m-row draw from the query span that excludes the scope's own rows"*. The query span is **28 rows**
(confirmed in 6900/6900 prompts, §2). `S_D` cuts 22 and leaves a pool of **6**; `S_E` cuts 23 and
leaves a pool of **5** — in both cases *fewer rows than the dose to be matched*. The control the
design requires for every scope **cannot exist** for the two largest scopes, one of which (`S_D` vs
`S_E`) is the phase's **declared primary contrast**. `random_row_control_constructible()` reports
this before extraction; `random_row_control_draw()` **refuses** rather than silently drawing fewer
rows (**M58**); and the arm manifest omits the control arms for those scopes instead of shipping a
smaller draw labelled as dose-matched. `assert_scope_has_its_control()` then refuses to render a
delta for a scope with no control — so as the design stands, **`S_D` and `S_E` cannot be rendered at
all** and the primary contrast needs an amendment (a new preregistration, not an edit). Resolving
this is a config-owner decision; the analyzer states it rather than choosing.

**Not a defect, worth recording:** `S_C`'s random-row draw 0 lands on `rel_end −9`, which is `S_F`'s
row and the `following` read site. That is a legal draw from the declared pool, but a reader
comparing `S_C` against its own control is then comparing it against `S_F`'s row.

**Loader state, unchanged and correct:** `--for-extraction` still emits **9 refusals**
(U1…U8 blocking-and-not-done, plus `artifacts.analyzer_exists == false`). Flipping `done` on U4/U5/U6
and flipping `analyzer_exists` are the config owner's edits; this session did not touch the frozen
file.

---

## 6. Reproduce

```
python3 scripts/dcs_ts_pr059_localisation.py --self-test        # 92 checks, 0 failed
python3 scripts/dcs_ts_pr059_localisation.py --mutate           # 80/80 RED
python3 scripts/dcs_ts_pr059_localisation.py --verify-token-map # U4, 6900/6900
python3 scripts/dcs_ts_pr059_localisation.py --selector-demo    # U1
python3 scripts/dcs_ts_pr059_localisation.py --control-draws    # U2 (+ PR059-D1)
python3 scripts/dcs_ts_pr059_localisation.py --u3-inventory     # U3, rc=2
python3 scripts/dcs_ts_pr059_localisation.py --plan
python3 scripts/dcs_ts_pr059_localisation.py                    # REFUSES: no arm has run
python3 scripts/dcs_ts_prereg.py --check --for-extraction configs/dcs_ts_pr059_phase11.json
```

---

# Appendix A — 2026-09-08: the producer halves of U1/U2, and the independent verifier (U7)

**CPU only**, no GPU, no SLURM, no network. Governing file `configs/dcs_ts_pr059_phase11.json`,
still `FROZEN`; only its `pre_extraction_checklist` **booleans** were touched, each with a
`closed_evidence` / `why_open` string, which is the house convention (`configs/dcs_ts_pr048.json`
is FROZEN with all items `done: true`; `configs/dcs_ts_pr060_phase9_amendment.json` carries
per-item evidence blocks). The design sections were not edited.

## A.1 Observed numbers

| entry point | observed |
|---|---|
| `dcs_ts_pr059_localisation.py --self-test` | **92 checks, 0 failed** |
| `dcs_ts_pr059_localisation.py --mutate` | **80/80 RED** |
| `dcs_ts_pr059_localisation.py --verify-token-map` | `ok=true`, **6900/6900**, `layout_mismatches={}` |
| `dcs_ts_pr059_localisation.py --control-draws` | rc=1 (2 of 6 scopes have no constructible control) |
| **`dcs_ts_pr059_verifier.py --self-test`** (NEW) | **22 checks, 0 FAILED** |
| **`dcs_ts_pr059_verifier.py --mutate`** (NEW) | **22/22 RED** |
| **`dcs_ts_pr059_verifier.py`** (default) | **rc=2** — "82 declared arm(s) searched, 0 present on disk" |
| `dcs_extract_under_ko.py --self-test` | **35/35** |
| repo tests importing either changed script (26 files) | **676 passed**, 1 warning, 326 s |
| `dcs_ts_prereg.py --check` | clean: FROZEN, 17 hashes pinned and verified, 12/12 mandate-21 fields |
| `dcs_ts_prereg.py --check --for-extraction` | **9 refusals → 4** (U2, U3, U8, `analyzer_exists`) |

**PHASE 9 (PR-057) is UNMOVED**, measured before and after the edits, identical both times:
`dcs_ts_pr057_causal.py --self-test` **111 checks, 0 FAILED**; `--mutate` **90/90 RED**;
`pr057_run_causal.py --self-test` **70 checks, 0 FAILED**; `--mutate` **41/41 RED**.

## A.2 U1 — the producer half, CLOSED

`score_behavior.surface_span_from_rel_end()` is **one definition called at three sites**: the
pre-flight feasibility pass, the per-row resolution, and — by import, not by restatement —
`scripts/dcs_extract_under_ko.py`. "The two call sites agree" is therefore structural rather than
remembered. The legacy `sorted(query_span)[-K:]` branch is left intact and is still the branch
taken when the new flag is absent, so every pre-existing invocation is byte-for-byte the run it was.

* **END-RELATIVE IN EVERY PROMPT SEPARATELY** — offsets resolve against *this* row's
  `len(input_ids)` and are constrained to *this* row's query span.
* **AN ABSOLUTE INDEX REFUSES**, at argument time and again at resolution time. Observed:
  `--knockout-rel-end-rows=9` → `ABSOLUTE INDEX REFUSED -- offsets [9] are not negative`.
* **Persisted on every row**: `surface_span_positions`, `surface_span_rel_end`,
  `surface_span_decoded`, `surface_span_tokens`, `seq_len`, `knockout_scope_id`,
  `knockout_selector`; `summary.json` gains `declared_offset_scope` **only** on this path.
* **Agreement with the analyzer, re-derived**: the producer's selector and the analyzer's return
  identical positions for all five constructible scopes at `seq_len ∈ {60, 137, 400, 1024}` —
  **0 mismatches**. `S_D` → 22 offsets, `S_E` → 23, `S_F` → `[-9]`.

**A usability caveat, recorded because it will bite whoever writes the argsfiles.** `argparse`
rejects a bare `-28..-6` as an option (it is not a valid negative number) and dies with
`expected one argument`. The value must be passed as `--knockout-rel-end-rows=-28..-6`. This is
documented in `--help` on both scripts. The alias `--declared-rel-end` was added because that is
the spelling `--plan` prints, so the planned command and the flag that exists are one string.

## A.3 U2 — PARTIALLY closed, and it cannot close as written

Implemented and reproducible: `random_row_control_rel_end()` draws *m* rows from the declared
query span **excluding the scope's own rows**, seeded from `--knockout-random-row-seed` (never
inherited from `--seed`) through `sha256(seed|scope_id|draw_index)` rather than the salted builtin
`hash()`, and the **whole draw is recorded** — seed, derived seed, pool, excluded rows, chosen
rows — per row and in `summary.json`. Observed: `S_A` draw 0 → `[-28, -25, -21, -16, -8]`, m=5,
pool=23, **byte-equal to the draw `--plan` prints and to the draw the new verifier re-derives from
the frozen seeds with no shared code**. All three draws agree with the analyzer on `S_A`, `S_C`,
`S_F` and `S_F2` (rows, pool, derived seed).

It stays **BLOCKING and `done: false`** for two independent reasons:

1. **`PR059-D1` is arithmetic, and it now also names `S_G`.** The query span is 28 rows. `S_D`
   (22) leaves a pool of **6**, `S_E` (23) leaves **5**, and the reference scope `S_G` (28) leaves
   **0**. The producer **refuses by name** rather than drawing fewer rows — observed:
   `REFUSING: PR059-D1: scope S_E asks for 23 control row(s) but the query span (28 rows) has only
   5 row(s) outside the scope`. `dose_matching.per_scope_random_row_control` requires one for
   *every* scope, so the item cannot be satisfied as written.
2. The item's second clause — *"verify the 3 draws produce 3 DISTINCT output hashes"* — is a
   statement about **arm outputs, which do not exist**; that is GPU work behind `U8`. The CPU
   precondition is met (three distinct **row sets** for every constructible scope) and the
   output-hash gate itself is implemented as the new verifier's `R3`, where mutation **M06**
   ("control band is secretly n=1") is RED.

## A.4 U7 — the independent verifier

`scripts/dcs_ts_pr059_verifier.py`. **Independence is enforced, not claimed**: `T00a` scans the
verifier's own source for any import of the analyzer and `T00b` asserts the analyzer is absent from
`sys.modules` after the verifier is fully imported, which also catches an indirect import through a
third module. Every quantity is re-derived — its own offset parser (all three shapes the frozen
file uses, including `[-28..-6] minus [-10]`), the scope table from `scopes.family`, the span from
`token_map.rel_end_layout`'s keys, the draws from `seeds.*`, the arm tags from a rule stated in the
verifier, the outcomes from each arm directory's `results.jsonl`. The only shared objects are the
frozen config (a data file) and the arm directories.

**The expected arm set is declared HERE** — `expected_arms()` builds **82** arms over the two
confirmatory banks — and `R5` fails both when the producer reports *less* (an arm complete on disk
and absent from its output) and when it reports *more* (an arm nobody preregistered).

| class | what it closes | mutations RED |
|---|---|---|
| `V0` | the verifier is still bound to the design it was written against | (T20) |
| `R1` | silent denominator; non-uniform domains | M01, M02 |
| `R2` | row-level identity: swapped arms, a baseline claiming a scope, an argsfile that disagrees | M03, M04, M05 |
| `R3` | a control band that is secretly n=1; an arm that is a byte-copy; a short band | M06, M07, M08 |
| `R4` | population swap and population drift | M09, M10 |
| `R5` | vacuous by omission; and an invented arm | M12, M13, M14 |
| `P1` | **realised ≠ declared** — a pinned absolute index, an off-by-one, missing decoded tokens | M15, M16, M17 |
| `P2` | SDPA, a dead hook, a scope that leaked into decode | M18, M19, M20 |
| `P3` | the display channel used as a mechanism result | M11 |
| `P4` | `PR059-D1` — an impossible control shipped, or claimed by the producer | M21, M22 |

The fixture is built from the **design**, not from the checks: it writes what a correct producer
would write, with a **per-row-varying `seq_len`**, precisely so an absolute-index producer cannot
pass `P1` by accident.

## A.5 New, recorded, not fixed here

**`PR059-D2` — `--plan`'s commands are not runnable, so `U8` has no launcher.** Every arm line
`dcs_ts_pr059_localisation.py --plan` prints is addressed to `scripts/dcs_ts_readout_multi.py`,
which accepts only `--banks --family --tag-prefix --query-kinds --conditions --n-examples
--max-new --attn-impl --arm --intervene --fit-dir`. It forwards **no** `--only-cell`,
**no** `--knockout-scope`, **no** `--knockout-rel-end-rows`. The printed line is therefore a design
statement, not a command. `U8` (smoke `S_G` and `S_C`) cannot be launched through it as written;
either the wrapper grows the pass-through or the arms go through `score_behavior.py` directly.
That file is outside this session's write scope, so this is recorded rather than fixed.

**`PR059-D1` now also names `S_G`.** The earlier record named `S_D` and `S_E`. Re-derived
independently by the new verifier (`T10`): the scopes whose dose-matched control is arithmetically
impossible are **`S_D`, `S_E` and `S_G`** — pools 6, 5 and 0 against doses 22, 23 and 28. `S_G` is
the *denominator*, not a family member, so no Holm-corrected claim rests on its control; but
`dose_matching` says *every* scope, and it does not have one.

**Does `PR059-D1` still block the primary contrast? YES.** `S_D` vs `S_E` is
`scopes.family[S_D].interpretation`'s "THE DECISIVE CONTRAST OF THIS PHASE", and
`assert_scope_has_its_control()` refuses to render a delta for a scope with no dose-matched
control. Nothing in this session changed that: the producer now refuses to *build* the impossible
control instead of silently drawing a smaller one, which makes the block explicit rather than
removing it. Resolving it is a config-owner decision and a new preregistration.

## A.6 Reproduce

```
python3 scripts/dcs_ts_pr059_verifier.py --self-test          # 22/22
python3 scripts/dcs_ts_pr059_verifier.py --mutate             # 22/22 RED
python3 scripts/dcs_ts_pr059_verifier.py                      # rc=2, 82 arms searched, 0 present
python3 scripts/dcs_ts_pr059_localisation.py --self-test      # 92/0
python3 scripts/dcs_ts_pr059_localisation.py --mutate         # 80/80 RED
python3 scripts/dcs_ts_pr059_localisation.py --verify-token-map
python3 scripts/dcs_ts_prereg.py --check --for-extraction configs/dcs_ts_pr059_phase11.json
python3 scripts/dcs_extract_under_ko.py --self-test           # 35/35
python3 scripts/dcs_ts_pr057_causal.py --self-test            # 111/0   (PHASE 9, unchanged)
python3 scripts/dcs_ts_pr057_causal.py --mutate               # 90/90   (PHASE 9, unchanged)
python3 src/boombness/pr057_run_causal.py --self-test         # 70/0    (PHASE 9, unchanged)
python3 src/boombness/pr057_run_causal.py --mutate            # 41/41   (PHASE 9, unchanged)
```
