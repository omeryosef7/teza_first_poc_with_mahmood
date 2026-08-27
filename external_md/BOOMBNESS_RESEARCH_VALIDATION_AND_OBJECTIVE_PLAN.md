# Boombness — RESEARCH VALIDATION AND OBJECTIVE SPRINT

**File:** `external_md/BOOMBNESS_RESEARCH_VALIDATION_AND_OBJECTIVE_PLAN.md`
**Opened:** 2026-08-27
**Repo:** `first_poc/teza_first_poc_with_mahmood`, branch `behavioral-causality-sprint`
**HEAD at open:** `2576ea5b`
**Owner:** this Claude session. SLURM submissions for this sprint are owned here and logged in §L.

> **This file is the authoritative live research log for this sprint.** It is append-oriented:
> a superseded conclusion is marked `⛔ RETRACTED — reason` beside its correction, never
> silently overwritten. Every result names artifact, run dir, command, model, bank,
> population, n, judge, seed, layer/window and commit.

---

## 0. FRAMING — what this sprint is and is not

The goal is **not** to defend the previous sprint's conclusions. It is to (a) repair
measurement defects, (b) determine whether a real boombness signal exists that can become a
GCG/MAC objective, and (c) leave a publishable answer either way. **A clean negative is a
result and will be reported as one.**

Standing constraints for this sprint (from the sprint brief, binding):

* Length-filtered ASR and post-treatment-thresholded ASR are **diagnostics, never the main
  estimator**.
* `d_surface` is **not** called causal unless the dose-matched *and* aligned-bank tests support it.
* Token-level and prompt-level boombness are **separate objects**, measured separately.
* **No GCG/MAC objective is built unless the Phase 7 gate passes.**
* No post-hoc favourable filtering. No `newest()` artifact selection. No broad `git add -A`.
* Row counts always reported beside percentages; rates always recomputed from rows.
* Judge model pinned and recorded per row; completion hash-joined generation→judgement.
* A guard that fails stops the work or the result is explicitly declared void.
* Never trust a green test that has not been mutation-tested.

### 0.0 Inherited state — read before citing any old number

The previous sprints already retracted the original chain
`Boombness → predicts ASR → causally increases jailbreak → GCG objective`.
Condensed from `external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md` and
`reports/SPRINT_SUMMARY_2026-08-16_TO_08-26.md`:

* **G2 RETRACTED (R-18).** `d_surface` does not predict attack success on clean rows.
* **G4 directional null.** Both signs of `d_surface` steering suppress ASR.
* **Removing `d_surface` RAISES ASR** on AdvBench-495 held out (L8 +0.0424, 21 net flips).
* **Refusal is the far larger Llama channel** (arm D +0.2869).
* **Dose confound (R-25):** `d_surface` ≈ PC1 of the cell-mean span; every in-subspace control
  removes ≤0.13 of the spread the arm removes 0.81–0.88 of.
* **No concept transfer (R-23/R-24).** The object is `d_surface_carrot_bomb`, **not** "boombness".
* **Retrieval knockout suppresses the attack** (96 down / 18 up over 8 populations) but **no
  calibrated cluster test of magnitude excludes zero** (C-18).

This sprint therefore starts from a **provisional-everything** posture, exactly as the brief asks.

### 0.1 Existing infrastructure this sprint REUSES (no rewrites)

`src/boombness/` is ~37 kLOC of mature, guard-covered code. The sprint reuses it rather than
rebuilding. Mapping of brief-phase → existing module:

| brief phase | already exists | what is genuinely new |
|---|---|---|
| 1 aligned banks | `prompt_families.py` (the **core 2×2** A/C/E/B, axes `n_examples, strength, consistency, example_position, role_style, domain, query_kind, split`), `tokenization_audit.py` | new cells, larger n, demo-count/aggressiveness sweeps |
| 2 token/prompt boombness | `extract_boombness.py` (per-occurrence × layer, cross-fitted), `signals.py`, `probes.py`, `followup_token_level.py` | the **separation** of the two objects + heldout prediction |
| 3 aggressive patching | `aggressive_patching.py`, `donor_patch.py` | dose-matched controls under the fixed ASR protocol |
| 4 surgical/knockout | `surgical_knockout.py`, `09_attention_knockout.py`, `50_path_patching.py` | re-measurement under fixed ASR |
| 5 comprehension | `score_behavior.py` `semantic_one_word` / `comprehension_usage`, `semantic_binding_probe.py`, `completion_phenotype.py` | pairing them to every new arm |
| 0.2 ASR protocol | per-row `stop_reason`/`n_new_tokens`/`gen_truncated`/`n_chars` **already recorded** | the **aggregator + publication guard**, and the cap raise |

**The single largest genuinely-new engineering item is Phase 0.2**, and it is small precisely
because the per-row diagnostic fields already exist — what is missing is an estimator that
refuses to publish without them.

---

## A. THE PLAN (as briefed, with this repo's bindings)

### PHASE 0 — stabilise measurement before any new science
* **0.1** Claim ledger: every prior claim → KEEP / KEEP-NARROWED / NEEDS-RERUN / RETRACT / OPEN,
  re-derived from artifacts, not prose.
* **0.2** Fixed ASR protocol: cap ≥512 (768/1024 if the cap still binds >10–20 %), same cap for
  every arm, no length conditioning, no post-treatment row drops. Report ASR, continuous judge
  score, refusal-keyword rate, median chars, median tokens, fraction at cap, fraction <40/<80/<120
  chars, fraction EOS-ended, scorable fraction. **A guard refuses an ASR table lacking these.**
* **0.3** Re-run the key old comparisons under the fixed protocol → table
  "old conclusion vs fixed-ASR conclusion". **No objective work starts before that table exists.**

### PHASE 1 — aligned banks (topic leakage is the enemy)
Matched families; cells A natural_doublespeak / B benign_literal / C direct_harmful /
D concept_in_benign_context plus E–J controls; `n_examples ∈ {0,1,2,4,8,12}`; aggressiveness
sweep (weak/medium/strong/inconsistent/position/repeat); family-disjoint train/dev/test;
strict tokenization + grammar gates (incl. the vowel-article bug that killed `arrow`);
byte-identical regeneration test; bank report with rows/families/domains/hashes/sha16.

### PHASE 2 — token-level ≠ prompt-level
2.1 per-occurrence readouts across layers (logit lens, direction projection, 2×2 `d_surface`,
trained probe, embedding baseline, controls). 2.2 prompt-level candidates, **pre-registered on
dev**. 2.3 probes 0–3 (naive lexical baseline → matched → 2×2 residualised → heldout pair
transfer). 2.4 Fig-8-style token dynamics. 2.5 Fig-9-style prompt→ASR with cluster bootstrap by
domain and partial correlation controlling `n_examples`, length, strength, refusalness, domain, pair.

### PHASE 3 — aggressive intervention first
Can we force carrot→bomb at all (positive patch) and remove it (negative patch), with
norm-matched / random / concept / refusal controls, dose measured **in the hook's own space**
(the R-25/C-6 trap), bidirectional and monotone-by-dose. **If no aggressive patch moves behaviour
without degeneracy, stop and record the negative.**

### PHASE 4 — surgical patching / knockout, publishable standard
Attention knockout with exact query/key positions, fired counters, liveness assertions,
key-matched + late-layer + count-matched controls; activation patching; path patching only after
readouts nominate components. Surgicality criteria: fires where intended, matched control,
fluency preserved, comprehension preserved, not length collapse, not refusal alone, survives one
heldout population, not single-domain.

### PHASE 5 — comprehension and binding controls
Forced-choice binding, free-generation binding, benign mapped task, literal comprehension, direct
comprehension, refusal detector. **Success = ASR falls while binding stays high.**

### PHASE 6 — the demonstration-count experiment, done cleanly
`n_examples ∈ {0,1,2,4,8,12}` × {token boombness per occurrence, prompt boombness, fixed-protocol
ASR, binding, refusal, length/truncation, retrieval mass, probe}. **If boombness is just
`n_examples` wearing a different name, it is not an objective.**

### PHASE 7 — objective gate (hard gate)
Candidates scored on dev, ≤2 pre-registered, evaluated on heldout against baselines (refusalness,
`n_examples`, length, random dir, context dir, naive concept dir). Proceed only if a candidate
predicts heldout ASR beyond those controls, has a plausible causal result, is not a lexical/topic
classifier, is measurable from internals during optimisation, and has variance across
prompts/suffixes. **Otherwise write "No objective should be built" and stop.**

### PHASE 8 — only if 7 passes: small GCG/MAC pilot
Reuse `TROPT` / existing GCG code. Arms: baseline, refusal-only, boombness-only, boombness+refusal,
random-internal control. Small and controlled; not overbuilt.

### PHASE 9/10 — deliverables and minimum success criteria
The seven questions in the brief get a clean YES/NO each, including "should a GCG/MAC objective be
built" — and a NO is a valid, reportable answer.

---

## L. LIVE PROGRESS LOG

*(newest entries appended at the bottom of each section; retractions marked inline)*

### L.0 — 2026-08-27, sprint opened
* Branch `behavioral-causality-sprint`, HEAD `2576ea5b`.
* `python src/boombness/check_all.py` → **6/6 deliverable guards pass** at open.
* SLURM queue **empty** for the account; all six L40S nodes (`n-801..n-805, t-806`) present in
  `killable`.
* Working tree carried 4 modified files from the prior phase (progress doc + two sprint summaries
  + a bank meta); none are results-changing for this sprint and they are left untouched.
* Infrastructure survey done (§0.1). Decision recorded: **reuse `src/boombness/` throughout; the
  only new modules this sprint should need are an ASR estimator/guard and thin analysis scripts.**

---

## §0.2 — ASR MEASUREMENT PROTOCOL *(deliverable 3; implemented 2026-08-27)*

### 0.2.1 The defect, measured rather than assumed

Every prior ASR number in this project was computed ad hoc by whichever analysis script needed
it, and the diagnostics that decide whether it *means* anything lived in a different file
(`score_behavior/*/results.jsonl`) from the ASR itself (`judge/*/summary.json`). Nothing forced
them to be reported together. So the first thing this sprint did was measure the damage.

**Generation-side scan — all 463 behavioural run dirs in `outputs/boombness/score_behavior/`:**

| cap | run dirs | rows | weighted truncation | median run truncation |
|---|---|---|---|---|
| 128 | 1 | 8 | 0.2500 | 0.2500 |
| **192** | **193** | **45 935** | **0.4617** | **0.5000** |
| 512 | 264 | 127 345 | 0.0915 | 0.0586 |
| 640 | 5 | 432 | 0.0000 | 0.0000 |

**At `max_new=192`, roughly half of every population never finished its answer.**

**Judge-side scan — all 614 judge run dirs re-scored under the new estimator**
(`outputs/boombness/asr_protocol/corpus_sweep_20260827.json`, 596 scored, 18 unscorable):

| cap | judge dirs | rows | dirs where the cap BINDS (>10 % at cap) | median frac at cap |
|---|---|---|---|---|
| **192** | **242** | **69 904** | **221 (91.3 %)** | **0.4729** |
| 512 | 349 | 146 798 | 51 (14.6 %) | 0.0586 |
| 640 | 5 | 432 | 0 (0.0 %) | 0.0000 |

**Verdict, stated plainly:**

* **324 judge dirs / 135 867 rows are quotable as plain ASR.**
* **271 judge dirs / 81 088 rows are quotable ONLY as "ASR within first N generated tokens".**
* 1 dir is refused outright (`ctrlbandfix_s20260903`, missing diagnostics).
* **0 join failures and 0 duplicate `prompt_id`s corpus-wide** — the generation↔judgement join is
  sound; the defect is truncation, not population drift. That is a genuinely good piece of news
  and it is recorded here so the sprint does not go looking for a bug that is not there.
* 18 judge dirs point at a `gens` directory that **no longer exists** (`fu_abL15_*`, `p1j_late9`,
  `q3dec_B11`, …). They cannot be re-derived and are marked unscorable, not "fine".

### 0.2.2 A second, separate defect the scan exposed

**51 run dirs still bind at `cap=512`, and raising the cap will not fix them.** Their length
distribution is *bimodal*: `median_new_tokens = 20–30` with 25–40 % of rows at the cap. Examples
(all `n` and row counts, never rates alone):

| arm | n | frac at cap | median tokens | ASR@0.5 | refusal-kw rate |
|---|---|---|---|---|---|
| `ch_D` / `chg_D` | 179 | 0.397 | 431 | 97/179, 92/179 | 0.447 |
| `abg_D` | 495 | 0.317 | 24 | 174/495 | 0.622 |
| `ab_C` | 482 | 0.243 | 20 | 133/482 | 0.716 |
| `p1a_rnd75` / `unlk_rnd75` | 495 | 0.378 | 30 | 135/495, 128/495 | 0.774 |
| `m_fuF_addCtrl18` | 495 | 0.404 | 97 | 64/495 | 0.877 |

A median of 20 tokens with a third of the mass at 512 is **two populations, not one**: short
refusals plus runaway generations. **This bears directly on the largest surviving old claim —
"refusal is the far larger Llama channel" (arm C +0.2061, arm D +0.2869)** — because those are
exactly the C and D arms. That claim is therefore marked **NEEDS RERUN / KEEP-NARROWED** pending
§0.3, not retracted: the cap binding does not by itself say which way the estimate moves.

### 0.2.3 The estimator and its guard

`src/boombness/asr_protocol.py` (new). Design commitments:

* **It has no filtering parameter. At all.** Not min-length, not both-EOS, not drop-truncated.
  Length-conditioned and post-treatment-thresholded ASR were the two headline measurement
  defects, and *a knob that cannot be passed cannot be passed by accident*. The absence is
  asserted by a test over `inspect.signature`, not merely documented.
* **`MANDATORY_DIAGNOSTICS`** — 21 fields that must travel with any quotable ASR: `n_rows`,
  `n_judged`, `n_scorable`, `scorable_frac`, `asr_at_0.5` **with** `asr_rows_at_0.5`,
  `asr_at_0.25` with its rows, `score_mean`/`score_median`, `refusal_keyword_rate` with rows,
  `median_chars`, `median_new_tokens`, `max_new`, `frac_at_cap` with `rows_at_cap`,
  `frac_lt_40/80/120_chars`, `frac_eos`, `n_join_missing`.
* **Rates are recomputed from rows**, and the row count travels beside every rate.
* **`assert_publishable` refuses** on: any missing diagnostic; any judged row with no matching
  generation; a bound cap (>0.10) still labelled "ASR" rather than "ASR within first N generated
  tokens". **`assert_table_publishable` additionally refuses a table that mixes caps** — the same
  cap for baseline and every arm, or the treatment is confounded with the text budget.
* **The join is hashed.** Every generation is `sha256`-hashed at load, so a re-judge can prove it
  scored the same text rather than a regenerated one.
* Text is read only to hash and length it; nothing reaches stdout or the artifact.

**Guard mode:** `python src/boombness/asr_protocol.py --check <asr_table.json>` exits non-zero on
an unpublishable table, so it can be wired into `check_all.py`.

### 0.2.4 The tests can fail — proved, not asserted

`tests/test_asr_protocol.py`, **34 tests, all passing**, built on synthetic run-dir fixtures (no
model, no API, no real generations). Per the sprint rule *"never rely on a green test unless you
have mutation-tested that the test can fail"*, six mutations were applied to the estimator and
the suite re-run each time:

| # | mutation | result |
|---|---|---|
| 1 | cap-binding check disabled | ✅ RED (1 failed) |
| 2 | join-failure check disabled | ✅ RED (1 failed) |
| 3 | missing-diagnostic check disabled | ✅ RED (22 failed) |
| 4 | mixed-cap check disabled | ✅ RED (1 failed) |
| 5 | `>=` → `>` at the ASR threshold | ⛔ **SURVIVED** |
| 6 | truncation read from the wrong field | ✅ RED (2 failed) |

**Mutation 5 survived, and that is the most useful thing in this table.** The fixtures scored
0.9/0.3/0.0 and never exactly 0.5, so an off-by-one at the decision boundary was invisible. A
boundary test (`test_thresholds_are_inclusive_at_the_boundary`, scores 0.5/0.4999/0.25/0.2499)
was added; mutation 5 was re-applied and now goes **RED**. All six mutations are caught; 34/34
green at HEAD.

**Status of §0.2: COMPLETE.** Deliverable 3 exists, is guarded, and is mutation-tested.
