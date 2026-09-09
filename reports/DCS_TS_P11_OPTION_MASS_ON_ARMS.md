# PHASE 11 — where the `option_mass` gate applies, and what a below-gate arm takes down with it

**DCS-R-146 / DCS-PR-065.** CPU only. No SLURM job submitted or cancelled. No GPU.
Parents FROZEN and unedited.

---

## 0. The one-paragraph answer

**The design already settled it, and it settled it against the convenient reading.** The FROZEN
`DCS-PR-059` scopes the `option_mass` gate to **every arm**, says so in three fields, and states the
**baseline** case *separately, in different words, with a different consequence* in a fourth. So
reading **(b)** is not adopted here — it was adopted on 2026-09-07, before any of these numbers
existed. Nothing in the gate moves.

What the parent never says is what happens to the **eleven other arms** of the stage. That is the
only thing `DCS-PR-065` decides, and it decides it by **arm role**, never by margin.

---

## 1. The measurement

Job **870536**, node **n-804**, stage `kill`, split `validation`, 12 arms planned, 1 completed.
Bank `ts116m_basket_bomb`, channel `semantic_one_word`, cell C, dose 4, **n = 230** rows over the
23 validation domains.

| arm | `median_true` | `median` (upper-middle) | p10 | p90 | frac > 1% | `reportable` | exit |
|---|---|---|---|---|---|---|---|
| `basket_bomb_S_0_baseline` | **0.08080** | 0.08100 | 0.006151 | 0.3286 | 0.8696 | `true` | 0 |
| `basket_bomb_S_G_scope` | **0.04517** | 0.04831 | **0.0001146** | 0.4493 | **0.6478** | `false` | **4** |

Two things are true at once and both matter.

* **The intervention worked.** The knockout roughly **halves** the median option mass —
  0.08080 → 0.04517, a ratio of **0.5590**. Read on its own, the gate is refusing the arm *because
  the manipulation succeeded*.
* **The knockout arm's readout really did move into the tail.** p10 falls by a factor of **54**
  (0.006151 → 0.0001146) and the fraction of rows carrying ≥ 1% of the next-token mass falls from
  **0.8696 to 0.6478**. On 35.2% of rows the two scored options now hold under a hundredth of the
  next-token mass. This is not a median that drifted a little; it is a distribution with a new
  lower tail.

The U8 smoke (job 870382) ran the same arm at **n = 40** and measured `median_true` **0.2611**,
comfortably clear. The smoke was not wrong — it was 40 rows.

---

## 2. What the design says — quoted

All four are in `configs/dcs_ts_pr059_phase11.json`, **FROZEN 2026-09-07**.

> **`outcome_variables.O1_semantic_readout.cannot_answer_if`**
> "median option_mass in **a scope's arm** falls below the 0.05 gate — CANNOT ANSWER, never a
> fallback to the display channel"

> **`primary.cannot_answer`, clause (a)**
> "ANY of: (a) median option_mass **in an arm** falls below the 0.05 gate; …"

> **`primary._largest_risk`, mitigation (3)**
> "if median option_mass **in an arm** drops below the gate the arm is CANNOT ANSWER"

> **`kill_condition`, SECOND kill — the BASELINE case, worded separately**
> "SECOND kill condition: if median option_mass in **the S_0 baseline** falls below the 0.05 gate on
> this population, **no knockout job is submitted at all**."

**The fourth quotation is the decisive one.** If "an arm" in the first three had meant "the
baseline", the parent would be saying the same thing twice in one file with **two different
consequences** — CANNOT ANSWER in one place, nothing-is-submitted in the other. It is not. Three
clauses say *an arm* and attach an **analysis** consequence; one names *S_0* and attaches a
**submission** consequence. Two rules, two scopes, two consequences, written together.

Corroborating, and independent of the above:

* **Both prior amendments re-froze the arm-scoped wording byte for byte** —
  `dcs_ts_pr061_phase11_amendment.json:331,333` and `dcs_ts_pr064_phase11_amendment2.json:346,348`.
  It survived two design reviews; it is not a slip of the pen.
* `reports/DCS_TS_PR058_PR059_DESIGN.md:374` and `:492` say it again in prose.
* **The travels-with rule is also already declared** — `primary._largest_risk` mitigation (1): "the
  argmax decoded answer and the full option_mass distribution are reported for **every arm beside
  every delta, never after it**."
* **PHASE 9 fixed this in code before PHASE 11 existed.** `scripts/dcs_ts_pr057_causal.py:1929-1930`
  applies the gate to the **intervened** arm's own rows and states the rationale in one line:
  > "the semantic_one_word channel must still be **ENGAGED after the edit**. A destroyed readout
  > collapses option_mass; **a moved readout does not**."

  That sentence *is* reading (b), and it distinguishes the two cases exactly as reading (a) fears
  it cannot. Measured across PHASE 9's **35** intervened arm directories: `option_mass_gate` =
  `PASS` on 35/35, `reportable` = `true` on 35/35, lowest `median_true` **0.05210**. **PHASE 9
  therefore fixes where the gate sits and supplies no precedent for what to do when it fires,
  because it never fired.**

### 2.1 The margin did not decide anything

Every quotation above predates job 870536. The rule reads identically had arm 2 measured **0.01** or
**0.20**. The 10% margin appears in this report and in `decision_PR059_D9.the_measurement` as an
*observation* and nowhere as an *argument*. The stop-scope adopted below is a **total function of
the arm's role** — it reads no measured quantity at all beyond the boolean `median_true < gate`.

---

## 3. What was genuinely open, and the decision

The parent says a below-gate arm is **CANNOT ANSWER** — a verdict, published beside the arm's own
option-mass distribution. It never says whether the **remaining arms of the stage** are still
submitted. The runner had a *de facto* answer nobody preregistered: any non-zero return code is a
stage failure. So one below-gate arm in bank 1 took down **ten unrun arms, six of them the whole of
bank 2**, a bank `primary.statistic` declares is **"reported per codeword bank and never pooled
across banks"**.

`score_behavior.py`'s own message says return code 4 is not a crash:

> "TAIL GATE FAILED — the run is written and its healthy readouts are usable, but these are **NOT
> reportable**"

**The rule adopted — `configs/dcs_ts_pr065_phase11_amendment3.json` `option_mass_gate_policy`:**

| arm role | disposition | authority |
|---|---|---|
| `baseline` (S_0) | **KILL_BANK** — no knockout job for that bank | the parent's SECOND kill condition, **unchanged** |
| reference scope (S_G) | **CANNOT_ANSWER_BANK** — no further arm of *that bank*; that bank's verdict is CANNOT ANSWER | `primary.success` conditions 1 and 2: every narrower number in a bank is a **fraction of S_G**, so an unreadable denominator makes all of them undefined |
| any narrower scope, any control, the bridge | **CANNOT_ANSWER_ARM** — that arm alone; **the stage continues** | the parent's own consequence for a below-gate arm, applied and nothing more |
| **every case** | **other banks are unaffected** | `primary.statistic`: "reported per codeword bank and never pooled across banks" |

A **NaN** readout is explicitly *not* covered: a NaN option mass is an **absent** measurement, not a
low one, and remains a hard stage failure. Return code 4 from an arm that is not actually below its
gate is likewise not laundered through this path.

**Nothing about the gate moves.** Same scope, same value, same statistic, same channel; the baseline
gate is not relaxed under any reading. What changes is only *how many other arms one below-gate arm
is allowed to take down*.

---

## 4. What is lost by choosing this

| | cost |
|---|---|
| **L1** | **A successful manipulation is unreportable.** basket_bomb's S_G knockout demonstrably worked and PHASE 11 may not report its `semantic_logodds` delta. All that can be said is the channel movement itself (0.08080 → 0.04517, p10 0.006151 → 0.0001146), reported as a **channel-engagement observation** — `option_mass` is declared in `outcome_variables.O3` as "REPORTED ALWAYS; descriptive, no multiplicity membership" — and **never as an outcome**. |
| **L2** | **PHASE 11 may lose its transfer pair.** If button_bomb's S_G also reads below the gate, PHASE 11 is CANNOT ANSWER outright. If it reads above, PHASE 11 has **one** bank, not the declared "transfer pair, never pooled": any positive rests on a single codeword and the transfer claim is unavailable. That must be in the result, not the appendix. |
| **L3** | **The basket_bomb localisation question is closed unanswered.** S_D vs S_E — the codeword-row contrast — is never measured on that bank. It is **not a null** and is not evidence that the codeword row does not matter. |
| **L4** | 249s of a 3238s stage bought no outcome number. |
| **L5** | **What the *other* reading would have cost.** Under (a), PHASE 11 would publish a paired delta whose knockout limb has p10 = 1.146e-04 and where 35.2% of rows carry under 1% of the next-token mass — an ordering inside a residual that is itself largely inside the tail the gate exists to refuse. That is precisely the failure named in `score_behavior.py`'s own gate comment: "a forced choice decided inside a 1e-5 tail is not a forced choice … the sprint published §2.6 verdicts from exactly that for two months without noticing." **Both readings cost something. This is not a free win.** |

---

## 5. A below-gate arm never travels alone

`primary._largest_risk` mitigation (1) already requires it, and PHASE 9 made the analogous
requirement structural for its nulls' realised dose (`dcs_ts_pr057_causal.py:1776`, `verdict()/_null`
refuses to emit a null-shaped verdict without `format_realised_dose`). Mirrored here:

* **`below_gate_record()`** (runner) attaches `median_option_mass`, the gate, `p10`,
  `frac_above_1pct`, `n`, `cannot_answer: true`, the full `option_mass` block, and the sentence
  *"This arm is CANNOT ANSWER. It is NOT a null."* It **refuses** if any field named in
  `required_travelling_fields` is absent.
* The record is written to the manifest **and** to `PR059_ARM_GATE.json` in the arm's own run dir.
* `DONE.json` now always carries `cannot_answer_arms`, `n_cannot_answer` and `closed_banks` —
  written even when empty, so their absence is detectable.
* Arms not submitted because their bank closed are recorded per arm as `status: not_submitted` with
  `_not_a_null: "this arm was NEVER RUN"`. An unsubmitted arm can never be read as a measured null.
* A stage in which **no** arm produced a reportable readout does **not** get a `DONE.json`.

---

## 6. Verification — observed numbers

| harness | before | after |
|---|---|---|
| `dcs_ts_pr059_localisation.py --self-test` | 114 / 0 | **122 / 0** |
| `dcs_ts_pr059_localisation.py --mutate` | 94 / 94 RED | **104 / 104 RED** |
| `pr059_run_localisation.py --self-test` | 58 / 0 | **69 / 0** |
| `pr059_run_localisation.py --mutate` | 49 / 49 RED | **56 / 56 RED** |
| `dcs_ts_pr059_verifier.py --self-test` | 25 / 0 | **27 / 0** |
| `dcs_ts_pr059_verifier.py --mutate` | 22 / 22 RED | **25 / 25 RED** |
| `dcs_ts_pr057_causal.py` (PHASE 9) | 117 / 0, 102 / 102 | **117 / 0, 102 / 102 — UNMOVED** |
| `dcs_ts_pr058_symmetry.py` (PHASE 10) | 57 / 0, 56 / 56 | **57 / 0, 56 / 56 — UNMOVED** |
| `dcs_ts_pr058_verifier.py` (PHASE 10) | PASS, 18 / 18 | **PASS, 18 / 18 — UNMOVED** |
| `dcs_extract_under_ko.py --self-test` | 35 / 35 | **35 / 35 — UNMOVED** |

`scripts/dcs_ts_prereg.py --check configs/dcs_ts_pr065_phase11_amendment3.json` →
*clean: status FROZEN, 21 hashes pinned and verified, all 12 mandate-21 fields present.*
`--for-extraction` → **3 refusals: V3, V16, V17.** The amendment still refuses on what is genuinely
open.

**Repo tests, to completion:** `pytest tests/ -q` → **1693 passed, 4 failed, 7 skipped**
(19m 27s). All four failures are in `tests/test_prompt_families_strict.py` and are
**pre-existing and unrelated** — the prompt-family generator refuses because 142 pool sentences
incidentally contain `carrot`/`was`, breaking the exact-word-swap invariant. That is another
writer's in-flight prompt-bank work (the untracked `data/boombness_prompts/ts_cand/`,
`ts_repair/`, `ts_smoke/` and `demo_pools_116dom_*` files that were present before this session
began). It touches no file changed here and no `pr059` code path.

**Runner dry-run**, `--stage kill --split validation --dry-run`: **12 arms constructed and
validated, 0 blocking gates, model NOT loaded, nothing written** — confirming V17 does not block
the stage that answers it.

**Unscoped `git status --porcelain`** shows exactly four entries beyond the pre-existing untracked
prompt-bank data: `M scripts/dcs_ts_pr059_localisation.py`, `M scripts/dcs_ts_pr059_verifier.py`,
`M src/boombness/pr059_run_localisation.py`, `?? configs/dcs_ts_pr065_phase11_amendment3.json`,
plus this report. No `configs/*.json` was edited; nothing was staged, committed or stashed.

Parent hashes unchanged and re-verified: `dcs_ts_pr059_phase11.json` `55c722ac1f5e9603`,
`dcs_ts_pr061_phase11_amendment.json` `1da927fb07200b20`,
`dcs_ts_pr064_phase11_amendment2.json` `9fb381425e2e6752`.

### 6.1 Two stale things this work exposed, fixed rather than left

* **The runner's `AMENDMENT_DEFAULT` still pointed at `DCS-PR-061`,** two amendments behind. Moving
  it to `DCS-PR-065` immediately failed two self-test assertions that had **hardcoded DCS-PR-061's
  open-blocker set** — they had been passing only because the default was stale. Both now
  **re-derive** the open set from the loaded amendment (and refuse to pass vacuously on an empty
  set) instead of pinning a literal list.
* **`summary.json` labels a below-gate arm `option_mass_gate: "OVERRIDDEN — NOT REPORTABLE: …"`
  even when `--allow-tail-readout` was never passed** — the argv for arm 2 contains no such flag and
  the process exited 4. Nothing was overridden. This is a **mislabel in a shared producer field**,
  recorded here and **not fixed in this pass**: `score_behavior.py` is written by three phases at
  once and changing a published string's meaning while PHASE 11 is in flight is not a repair a side
  task gets to make. `reportable: false` and the exit code are unambiguous and are what every code
  path reads.

### 6.2 New refusals, each reachable

Analyzer M91–M100 and runner M47–M53 make every way of softening the policy RED: no amendment
loaded; no `option_mass_gate_policy`; the policy restating the gate at a different value; the policy
re-scoping the gate to the baseline; a stop-scope that reads the margin; a relaxed baseline gate; an
unmapped arm role; a below-gate arm closing another bank; a below-gate arm reported without its
option mass; a different gate statistic.

The **independent verifier** gains check class **P5** (`scripts/dcs_ts_pr059_verifier.py`), which
re-derives each arm's median from that arm's **own** `summary.json` using this file's own gate
parse — importing nothing from the analyzer — and fires in three directions: a below-gate arm that
**vanishes** instead of being declared (M23); an **above**-gate arm relabelled CANNOT ANSWER (M24);
an arm reported as **both** a result and CANNOT ANSWER (M25). T21 additionally checks that the gate
is stated identically at all three prose sites (0.05, 0.05, 0.05) and T22 that this file holds no
constant copy of it.

---

## 7. Can the kill/validation stage be resumed?

**Not yet, and not by this work.**

`outputs/boombness/pr059_runner/kill_validation/ABORTED.json` exists, carrying provenance **job
870536, node n-804, written 2026-09-09 02:37:28**. Per **C-124** the runner refuses to resume a
stage while a terminal file sits in its directory, and **that refusal is correct** — it is the
record of why arm 2 of 12 stopped a run under the old stop-scope.

**It has not been deleted and has not been archived here.** What must happen, by the stage owner:

1. **Archive** `ABORTED.json` **with its provenance** (job 870536, node n-804) to a path that is not
   read as a terminal file. **Do not delete it**: a stage that loses the record of why it stopped is
   a stage that can be re-reported as though it never did.
2. Resume `--stage kill --split validation --amendment configs/dcs_ts_pr065_phase11_amendment3.json`.

On resume, under the new policy:

* `basket_bomb_S_0_baseline` — `status: done`, `output_sha256`
  `6a9c531cb01956bcb6ddedcfe9d600af90ad3304c7c397819495969351fe922d` — **skipped**.
* `basket_bomb_S_G_scope` — re-classified **CANNOT ANSWER**; its bank becomes
  **CANNOT_ANSWER_BANK**; its four remaining arms are **NOT submitted**.
* **The six `button_bomb` arms are submitted.** They never were.

**PHASE 11 cannot proceed to the `family` stage on either bank.** basket_bomb is
CANNOT_ANSWER_BANK; button_bomb is unmeasured. New blocking checklist item **V17** enforces this and
is scoped by **re-derivation, not by stage name**
(`pr059_run_localisation.py::_scores_a_narrower_scope`): it blocks any stage that scores a scope
whose only declared use is a fraction of S_G, and it does **not** block the `kill` stage, which is
the run that answers it — the same circularity `decision_PR059_D8` resolved for V3, resolved the
same way.

**Declared here, before the arm runs:** if `button_bomb`'s S_G also falls below the gate, PHASE 11 is
**CANNOT ANSWER** on the localisation question, reported with both banks' measured option-mass
distributions and explicitly **not** as a mechanism null.
