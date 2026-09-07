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
