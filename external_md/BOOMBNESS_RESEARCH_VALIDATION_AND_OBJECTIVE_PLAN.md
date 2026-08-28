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
---

## §0.3a — DID THE 192-TOKEN CAP ACTUALLY CHANGE ASR? *(a natural experiment already in the corpus)*

**Artifact:** `outputs/boombness/cap_natural_experiment/capNE2_20260827_210525_3544980/cap_natural_experiment.json`
**Script:** `src/boombness/cap_natural_experiment.py` · **Tests:** `tests/test_cap_natural_experiment.py` (10, 5 mutations caught)
**Commands:** `python src/boombness/cap_natural_experiment.py --pairs-file <pairs.json> --tag capNE2`

§0.2 settled that a number with half its rows at the cap **may not be called ASR**. It did not
settle the different and more important question: **did the cap move the estimate, and which way?**
Relabelling a number is not the same as knowing it was wrong. Before spending any GPU on §0.3, it
is worth noticing that the corpus already contains the experiment.

### The design

Four `(bank, model, arm)` groups were run at two caps. In one — `g2A` vs `g3A640`,
**Llama-3.1-8B-Instruct** on `boombness_prompt_bank_basket_bomb`, arm `A_baseline`, **n=96** — the
two generation configs differ in **exactly one field**: `max_new` 192 → 640 (plus the run tag).

Decoding is greedy, so the large-cap run should be *literally* the small-cap run continued. That is
verified, not assumed:

| continuation proof (Llama pair) | result |
|---|---|
| rows that ended in EOS at cap=192 | 6/96 — **6/6 byte-identical at cap=640** |
| rows truncated at cap=192 | 90/96 — **90/90 extended verbatim at cap=640** |

**This is a within-row natural experiment, and the continuation proof above is what makes it one.** ⚠ Stated precisely, because the artifact's own ledger is more careful than an earlier wording here: **3 of the 4 pairs are flagged `config_confounded_but_row_level_valid`** — the two runs in those pairs differ in configuration beyond the cap, and all 4 pairs nonetheless carry `row_level_valid: true`. So the confound is real at the CONFIG level and neutralised at the ROW level by the byte-identity and verbatim-extension evidence. The earlier phrasing, *"no confound at all"*, asserted something stronger than the artifact records and hid the fact that the continuation proof is load-bearing rather than decorative. The right test is McNemar on
the discordant pairs — exact, because at n=17 discordant the asymptotic form is not usable — not a
difference of two independent rates, which would discard the pairing.

### The result

| pair | n | ASR@0.5 rows, cap 192 → 640 | Δ | up | down | exact 2-sided p | MDE |
|---|---|---|---|---|---|---|---|
| **Llama `basket_bomb` `A_baseline`** (cap-only) | 96 | **25/96 → 32/96** | **+0.0729** | 12 | **5** | **0.1435** | 0.0938 |
| Qwen3 `longpreQ14B` `A_baseline` | 80 | 10/80 → 11/80 | +0.0125 | 4 | 3 | 1.0000 | 0.0875 |
| Qwen3 `longpreQ14B` `CTRL_matched_d1` | 80 | 11/80 → 12/80 | +0.0125 | 2 | 1 | 1.0000 | **none** |
| Qwen3 `longpreQ14B` `C_demo_processing_only` | 80 | 1/80 → 1/80 | +0.0000 | 1 | 1 | 1.0000 | **none** |

*(The three Qwen pairs are flagged `cap_only=false` because `n_examples` differs — the small-cap run
generated a superset. The continuation proof holds on all 80 common ids, which proves at the row
level that those are the same prompts, so `row_level_valid=true` for all four.)*

### What this means, stated carefully

1. **Truncation is NOT a one-way suppressor.** On the clean Llama pair, 12 rows flipped 0→1 when
   allowed to finish and **5 flipped 1→0**. A completion cut at 192 tokens sometimes scores
   *higher* than the finished one, because it was cut before the model hedged, refused or wandered
   off-topic. Any story of the form "the old ASR was depressed by truncation" is **wrong on its
   face** and this sprint will not tell it.
2. **The cap did not detectably move the point estimate on any arm tested.** The largest shift,
   +0.0729 on Llama, has exact p=0.1435 and does not exclude zero.
3. **But two of those four nulls are uninformative, and the artifact says so.** At 3 and 2
   discordant pairs, **no split reaches α=0.05 in either direction** — the design could not have
   produced a significant result whatever happened. `min_detectable_net_flips` reports
   `detectable: false` rather than letting a p of 1.0 be read as evidence of absence. Even the
   Llama pair could only have seen a shift of **≥0.0938** (13/17 one way).
4. **The reporting defect stands regardless.** 271 judge dirs / 81 088 rows may be quoted only as
   "ASR within first N generated tokens".
5. **The arms that most warrant suspicion have NO cap pair.** The `ch_D`/`abg_D`/`ab_C` refusal
   arms — the ones carrying the largest surviving old claim and the ones with the bimodal length
   distribution at cap=512 — were never run at a second cap. §0.3 must generate that pair on GPU;
   it cannot be recovered from the corpus.

**Ledger effect:** this evidence pushes the ASR-based claims toward **KEEP-NARROWED** ("the point
estimate is not measurably a truncation artifact, but the number must be labelled by its cap"),
**not** toward RETRACT — with the explicit exception of the C/D refusal arms, which remain
**NEEDS RERUN** because no evidence either way exists for them.
---

## §0.1 — THE CLAIM LEDGER *(deliverable 2)*

**Artifact:** `reports/boombness_claim_ledger_2026-08-27.json` (schema `BOOMBNESS_CLAIM_LEDGER/1`)

### Method — re-derived from artifacts, then adversarially attacked

Three read-only audit agents re-derived every prior claim **from committed artifacts, never from
prose**. Each resulting entry was then handed to an **independent adversarial verifier** told to
*refute* it and to default to `refuted=true` when uncertain, checking five things: do the cited
paths exist; do the cited numbers appear at the stated fields to the stated precision; is the
status too strong or too weak; is the claim contaminated by the `max_new=192` defect; is there an
ignored confound. **20 agents, 1.53 M tokens, 558 tool calls.**

The verification did real work: **it refuted the reasoning of 7 of 14 entries and changed 4
verdicts — every one of them in the STRICTER direction.**

### The ledger

| # | claim | audit | **after verification** | ASR cap dependency |
|---|---|---|---|---|
| 1 | `d_surface` exists, is reproducible, describes the codeword↔concept contrast | KEEP-NARROWED | **KEEP-NARROWED** | not ASR-based |
| 2 | concept axis `N` codeword-invariant; codeword identity is a (K−1)-dim subspace | KEEP-NARROWED | **KEEP-NARROWED** | not ASR-based |
| 3 | **R-25 dose confound** — `d_surface` ≈ PC1 of the cell-mean span | KEEP | **KEEP** | mixed; geometric half not ASR-based |
| 4 | `d_surface` is CAUSAL because steering changes attack behaviour (G4) | RETRACT | **NEEDS RERUN** ⬆ | **cap 192** |
| 5 | removing `d_surface` at L8 RAISES ASR by +0.0424 on AdvBench-495 | NEEDS RERUN | **NEEDS RERUN** | cap 512 |
| 6 | **demonstration-retrieval knockout suppresses the attack** (96 down / 18 up) | KEEP-NARROWED | **NEEDS RERUN** ⬆ | **cap 192 on ALL TWENTY runs** |
| 7 | **refusal projection is the larger Llama channel** (C +0.2061, D +0.2869) | KEEP-NARROWED | **NEEDS RERUN** ⬆ | cap 512, **and the cap binds** |
| 8 | "R-75/DR-11 discharged the truncation caveat" for these ASR claims | RETRACT | **RETRACT** (retraction upheld) | meta-claim |
| 9 | **G2 — prompt-level boombness predicts ASR** | RETRACT | **RETRACT** (retraction upheld) | cap 192 throughout |
| 10 | a clean pre-registered dev/heldout Fig-9 bank *does* show a prompt-level→ASR relation | KEEP-NARROWED | **KEEP-NARROWED** | cap 512, not the 192 defect |
| 11 | token-level boombness rises across layers and across occurrences | KEEP-NARROWED | **KEEP-NARROWED** | not ASR-based |
| 12 | C7 demonstration-specificity | OPEN | **OPEN** | cap 192 |
| 13 | binding/comprehension **survives** the intervention that kills the attack | KEEP-NARROWED | **NEEDS RERUN** ⬆ | partially, cap 192 |
| 14 | **a GCG/MAC objective was ever justified on this axis** | RETRACT | **RETRACT** | cap 192 for the steering half |

**Tally: 5 NEEDS-RERUN · 4 KEEP-NARROWED · 3 RETRACT · 1 KEEP · 1 OPEN.**

### What the ledger settles for this sprint

* **The Phase 7 gate has already failed once, on the old evidence** (entry 14, RETRACT, upheld
  under attack). Nothing in this sprint may build a GCG/MAC objective on the *old* `d_surface`
  axis. A new objective would need new evidence.
* **The two claims the previous sprint leaned on hardest both moved to NEEDS RERUN** — the
  retrieval knockout (entry 6) and the refusal channel (entry 7). Entry 6 is the more serious:
  **all twenty runs behind the 8- and 10-population tests are at `max_new=192`**, the exact
  stratum §0.2 showed binds on 91.3 % of dirs.
* **Entry 4 moved the other way — RETRACT → NEEDS RERUN.** The audit wanted to retract "steering
  is causal"; the verifier showed the retraction was *itself* over-claimed and the honest state is
  "unmeasured at a usable cap". The sprint does not get to bank that negative either.
* **The purely geometric claims (1, 2, 3) survive**, because no generation enters them. The dose
  confound (3) survived a five-axis refutation attempt with every number reproducing bit-for-bit.

### A verification field that could not be trusted — checked, not propagated

The verifiers returned **three artifact paths flagged as hallucinated**. Per the sprint rule that a
subagent's output is data rather than a finding, all three were re-checked on disk:

| flagged path | exists? |
|---|---|
| `outputs/boombness_followup/phaseB_semantic_forced_choice_slot0/token_level_dynamics_summary.json` | ✅ exists |
| `src/boombness/semantic_binding_probe.py` | ✅ exists |
| `.../binding_behaviour_bridge/REPRO_bridge_20260826_050914_1018899/binding_behaviour_bridge.json` | ✅ exists |

**All three exist.** One was a legitimate but mis-filed observation (the artifact's `RUNMETA.json`
names `binding_behaviour_bridge.py`, not `semantic_binding_probe.py`, as its producer — a
wrong-producer error, not a missing file). The other two are simply wrong. The field is recorded in
the artifact as `verifier_bad_path_claims_RECHECKED` and **is not propagated into any verdict**.
Had it been, this ledger would have asserted that three existing artifacts are missing.

### A schema flaw I introduced, and how it was resolved

Two entries are phrased "*X — retracted as R-18*". For those, a verifier verdict of `KEEP` is
ambiguous: keep *X*, or keep the *retraction*? Both came back `KEEP`. Resolved by reading each
verifier's full reasoning, which upholds every clean and powered null: **in both cases KEEP means
the retraction stands and the claim is dead.** Recorded in the artifact as
`ambiguity_resolution_note`. Future audit schemas in this sprint will state claims in the
affirmative only.
---

## §1 — PHASE 1 REASSESSED: the aligned banks the brief asks for MOSTLY ALREADY EXIST

**Source:** bank inventory over all 25 banks in `data/boombness_prompts/` (field values and
`*_meta.json` scalars only; no prompt text opened) plus `src/boombness/prompt_families.py`.

The brief's Phase 1 assumes prompts "were not always structurally aligned … farms vs cities" and
asks for new banks. **That is not the current state of this repo.** `prompt_families.py` builds the
2×2 as an *exact word swap* — A/C and E/B share the same demo sentences up to one word, and all
four share a byte-identical final query up to the same swap — with domain, template, sentence
count, occurrence count, chat template and target position matched by design.

| brief asks for | already exists | gap |
|---|---|---|
| core 2×2 A/B/C/D cells | `CONDITIONS` — 6 of them, incl. `benign_remap` and a no-demo control | none |
| `n_examples ∈ {0,1,2,4,8,12}` | **`N_EXAMPLES = (0,1,2,4,8,16)`** | **12 occurs in ZERO rows in ZERO banks. 16 exists instead — and is strictly better for the question.** |
| aggressiveness sweep weak/med/strong/inconsistent | `STRENGTHS = (none,weak,medium,strong,aggressive)` and `CONSISTENCIES = (consistent,mixed,conflicting,irrelevant)`; `phase_d` bank has **120 rows per level** | none |
| position variants | `POSITIONS = (near,far,distributed)` | none |
| heldout codeword/concept pairs | **14 pairs**: 5 codewords × 4 concepts (6 cells missing) | none |
| family-disjoint train/dev/test | `dev ∩ heldout = 0` families on **every** bank | test split absent; dev/heldout only |
| ≥10 domains for cluster inference | **7 banks span 10 domains**, 456 rows/domain, evenly | **k = 10 is the ceiling; no bank has k > 10** |
| tokenization + grammar audit, byte-identical regeneration | `tokenization_audit.py`, `tests/test_bank_regenerates_byte_identically.py`, `bank_rows_sha16` + `pools_sha16` per bank | none |

**Conclusion: Phase 1 is largely a NO-OP and the sprint should not spend GPU or wall-clock
rebuilding it.** The bottleneck this sprint faces is not bank construction — it is **measurement at
a usable generation cap**, which is precisely what §0.2/§0.3 address. Rebuilding banks would have
been the expensive way to avoid the actual problem.

### Three genuine gaps, and what they cost

1. **`n_examples = 12` does not exist; `16` does.** The brief's sweep is unavailable as written.
   Running `{0,1,2,4,8,16}` answers the same question over a *wider* range and needs **no new
   bank**. **Adopted, with the deviation recorded here.**
2. **No `test` split** — only `dev`/`heldout`. Phase 7's "pre-register on dev, evaluate on heldout"
   is therefore executable exactly as written; a third split is not.
3. **A design constraint that is a property of the phenomenon, not a bug.** Per
   `prompt_families.py`, `strength != none` and `consistency = conflicting` are **incompatible with
   the exact-word-swap 2×2 invariant**, because stating a mapping must name the codeword. Every
   aggressiveness sweep in every bank is therefore single-condition (`natural_doublespeak`) and
   exempt from `check_alignment`, and `n_target_occurrences` varies across strength levels **by
   construction**. **The Phase 2.5 aggressiveness→ASR analysis must condition on
   `n_target_occurrences`, or "aggressiveness" and "how many times the codeword appears" are the
   same variable.** This is recorded now so it cannot be discovered in a later audit.

---

## §R.1 — SELF-REVIEW (30-minute checkpoint, 2026-08-27 ~21:20)

**Changed:** `asr_protocol.py` + guard + 38 tests (9 mutations caught); `cap_natural_experiment.py`
+ 10 tests (5 mutations caught); the claim ledger (14 entries, adversarially verified);
`corpus_sweep_20260827.json`; four commits pushed (`4da920c1`, `03c06b75`, `48388931`, `140462f7`).

**Running:** SLURM 787101/787102/787103 — `base`/`C`/`D` on `advbench_heldout_495` at
**`max_new=1024`**, the rerun ledger entry 7 demands. SLURM 787104 — the `W_codeword_pc1`
`d_surface:project_out:14-14` arm at **640**, whose 640 baseline (`g3A640`) already exists with a
**pinned** judge. All four PENDING on `(Priority)` — fair-share, not capacity; a first submission
pinned to single nodes was cancelled and resubmitted across 3-node subsets.

**Failed / corrected:** (a) a test fixture that never scored exactly 0.5, so a `>=`→`>` mutation
survived — closed. (b) my own hand-computed McNemar threshold (14/17) was wrong; the code was right
(13/17) — the test now derives it instead of memorising it. (c) three verifier-flagged "hallucinated"
paths all exist — not propagated. (d) an ambiguous audit schema for claims phrased "X, retracted as
R-18" — resolved by reading the full reasoning.

**What is currently supported:** §0.2 (the cap is a reporting defect on 271 dirs / 81 088 rows),
§0.3a (that defect did not measurably move the point estimate where it can be checked, and is
bidirectional at the row level), §0.1 (the ledger), §1 (Phase 1 is largely a no-op).
**No new claim about boombness itself has been made yet, and none should be until §0.3 lands.**

**Peer session:** a concurrent session owns job 787099 (`dpools`, cpu-killable). Path and job
ownership exchanged; both findings above sent to it so its summary does not quote a 192-cap ASR.
---

## §1.1 — THE LEAKAGE PROBE *(user-directed: "reuse, plus one new leakage probe")*

**Artifact:** `outputs/boombness/bank_leakage_probe/leak2_20260827_212632_3593613/bank_leakage_probe.json` · **Script:** `src/boombness/bank_leakage_probe.py`
**Tests:** `tests/test_bank_leakage_probe.py` (12, 5 mutations caught)
**Command:** `python src/boombness/bank_leakage_probe.py --tag leak2` · 24 banks, no GPU

§1 argued Phase 1 is a no-op. The user's instruction was: reuse the banks, **but first try to break
them** — if a lexical baseline can separate the cells, the alignment is not what the code claims.

### The test is deterministic, not a classifier accuracy

`d_surface = ½[(B−C) + (E−A)]`, and **both** of those differences hold valence fixed and swap only
the target word. So if the design is what it claims, then after masking every occurrence of the
codeword and the concept, `masked(B)` must equal `masked(C)` **byte for byte**, and `masked(E)`
must equal `masked(A)`. A byte-equality test is far stronger than any classifier accuracy and
cannot be argued with: if it holds, there is *no lexical difference left* for `d_surface` to carry.

### Result — `d_surface` is lexically clean

**23 of 24 banks pass**, on 384–640 complete families each. The 24th, `phase_d`, has **0 core-2×2
rows by construction** (it is the single-condition aggressiveness bank), so it is not a failure.

| measurement | result | reading |
|---|---|---|
| **`d_surface` pairs byte-identical after masking** | **100 % on 23/24 banks** | the contrast carries no topic, domain or valence |
| **surface arm predicted from masked text** | **0.5000 on every bank, majority baseline 0.5000, lift 0.0000** | a lexical classifier cannot beat chance |
| surface arm predicted from **unmasked** text | **1.0000** | the instrument works — this is the sanity check |
| **valence** predicted from masked text | **0.9167–0.9375** vs majority 0.5000 (**lift ≈ +0.43**) | `d_context` IS heavily lexical, as the design openly admits |
| **domain** predicted from masked text | 0.8472–1.0000 | topic is highly readable — and orthogonal to `d_surface` |

**The asymmetry is the point, and it is now quantitative rather than asserted: lift 0.00 for the
`d_surface` factor against +0.43 for the `d_context` factor.** The brief's topic-leakage concern
is real for `d_context` and for `domain` — and does **not** reach `d_surface`.

### An internal consistency check that came out exactly right

The `d_context` pairs are identical after masking on **48/384 = 12.5 %** of families. That is not
noise, and predicting it in advance is how one knows the instrument works: broken down by
`n_examples`, it is **48/48 identical at `n_examples=0` and 0/336 at every `n_examples ≥ 1`.**
With zero demonstrations there is no demo block, so valence *cannot* differ and the cells collapse.

### The probe found a bug in itself first — recorded, because it nearly became a finding

The first run reported **11 of 24 banks leaking**, concentrated suspiciously in every `knife` bank.
Rather than write that up, the violations were opened: they were exactly `{Knife: 8, Basket: 8}`.
**The masking was case-sensitive**, so a sentence-initial target survived and the pair compared
unequal — while the swap itself had been performed correctly. **A probe that manufactures alignment
violations is worse than no probe at all.** The mask is now case-insensitive; the regression is
pinned by a test; and because case-folding *gives something up*, a separate `capitalisation_audit`
recovers it — a genuine case mismatch **between** arms (which changes tokenization) is still
reported. It finds **0–2 families per bank**, concentrated in the knife banks: small, real, and
worth knowing before anyone fits a direction on a knife bank.

**Grammar:** 15–82 article disagreements per bank (`a` before a vowel). The masked-identity test is
structurally **blind** to this class — masking makes both arms identical exactly where the article
disagreement lives — which is why it is audited separately. This is the class that killed `arrow`
as a concept (R-AZ, 528 rows).

### Verdict

**The banks are reused.** The leakage probe the user asked for was run, it tried hard to break the
alignment, and the alignment held on the one contrast the sprint's central quantity depends on.

---

## §0.4 — THE JUDGE NOISE FLOOR, and a correction to §0.2's framing

**Artifacts:** `outputs/boombness/judge_stability/{unpinned_base,pinned_q15A,pinned_q16A}.json`
**Script:** `src/boombness/judge_retest.py` — **existing repo code, reused unmodified.**
**Commands:** `python src/boombness/judge_retest.py --judge-a <A> --judge-b <B> --score-a <..> --score-b <..> --out <..>`

While repointing the C7 ledger entry (§0.5) I noticed that `q15A` and `q16A` had each been judged
**twice**, and the two runs disagreed: 16/160 vs 17/160, and 13/160 vs 12/160. Same generations,
same pinned model. That is the judge re-scoring stability check the brief demands before any
per-prompt flip identity may be quoted, and it was sitting in the corpus unread.

### The measurement

Every pair below has **byte-identical generations** (verified: 660/660, 160/160, 160/160), so every
difference is the judge and nothing else.

| pair | pinned? | subset | n | flips | **flip rate** | rows w/ score change | ASR swing |
|---|---|---|---|---|---|---|---|
| `base` Llama, carrot bank | **no** | all | 660 | 37 | **0.0561** | 0.1212 | 1.06 pp |
| " | no | `natural_doublespeak` | 270 | 27 | **0.1000** | 0.2259 | 1.85 pp |
| " | no | `core2x2_n≥1` | 240 | 11 | 0.0458 | 0.0958 | 2.08 pp |
| " | no | `core2x2_n≥1_doublespeak` | 60 | 6 | **0.1000** | 0.2500 | **6.67 pp** |
| `q15A` Qwen3, longpreQ14 | **yes** | all | 160 | 7 | **0.0437** | 0.0875 | 0.62 pp |
| " | yes | `core2x2_n≥1` | 80 | 4 | 0.0500 | 0.0875 | 2.50 pp |
| `q16A` Qwen3, longpreQ14B | **yes** | all | 160 | 9 | **0.0563** | 0.0938 | 0.62 pp |
| " | yes | `core2x2_n≥1` | 80 | 5 | 0.0625 | 0.1250 | 3.75 pp |

### ⛔ CORRECTION to the framing in V-2 / §0.2.3

**I expected pinning the judge model to reduce this, and it does not.** On the matched
`core2x2_n≥1` subset the flip rate is **0.0458 unpinned against 0.0500 and 0.0625 pinned** — if
anything slightly worse, and certainly not better. The comparison is not fully controlled (different
model, different bank), so the honest statement is: **there is no evidence that pinning reduces
binary-label instability, and it should not be claimed.**

What pinning *does* buy is what `judge_boombness.py` was actually built for and what V-2 should have
said on its own: it stops an ASR from **silently averaging over two different judge models**, via a
pre-flight canary and a `JudgeModelMismatch` abort. That is a real and different protection. The
`assert_sprint_grade` requirement stands — **for that reason, not for this one.**

### What the floor actually costs

`gpt-4o-mini` at temperature 0 is **not deterministic**: it flips roughly **5 % of binary labels on
byte-identical text**, and changes the continuous score on 9–25 % of rows. On n=80 that is ~4 rows;
on n=160, ~8 rows.

**This is the same order of magnitude as several claims in the ledger.** C7's headline cell-sets are
net differences of 3–5 rows out of 80. A 4-row judge noise floor on an 80-row arm is not a
footnote — it is the effect size.

**The mitigation is already known and is in `judge_retest.py`'s own docstring: a paired comparison
scored inside ONE judge run is far less exposed than a comparison across two.** Most of the
exposed claims (C7, the retrieval knockout) difference an arm against a baseline **judged in a
different session**. §0.5 and the entry-6 rerun must therefore judge arm and baseline **in the same
judge invocation**, or carry this floor explicitly.

**No new code was written for this section.** `judge_retest.py` and `judge_session_drift.py` already
existed and already said the right things; what was missing was running them on the pinned pairs and
reading the answer.

---

## §0.5 — C7 REPOINTED, and the sprint's FIRST SPRINT-GRADE RESULT

**Artifact:** `outputs/boombness/asr_protocol/c7_640_20260827_214634_3657971/asr_table.json`
**Command:** `python src/boombness/asr_protocol.py --sprint-grade --tag c7_640 --judge-dir .../p26j_A_* --judge-dir .../p26j_dp_* --judge-dir .../p26j_c1_*`

### The repoint

My §0.1 ledger cited three **Llama** runs for C7 (`p12A`, `p12_demoproc`, `p13A`). A peer session
asserted C7 is Qwen3-only; I refused the assertion and checked. **Both were true.** All three Llama
runs exist and are all `Llama-3.1-8B-Instruct` at cap 192 — but they belong to the branch that was
**declined for power** (the longer preamble needed for the count-matched control took Llama baseline
ASR from 0.1562 to 0.0437). The published C7 is the 13 **Qwen3-14B** runs; I verified all 13 exist
and are Qwen3. **My ledger entry cited the wrong runs and is repointed.**

Scored under the protocol, **10 of the 13 published C7 runs are at cap 192** and the cap binds hard
(0.394–0.700 at cap) — those may be quoted only as "ASR within first 192 generated tokens".
**But the 3-run 640-cap replication is clean**, and it clears `--sprint-grade`.

### The result — and it is the sprint's first genuinely clean one

Qwen3-14B, `boombness_prompt_bank_longpreQ14B`, `n_examples ∈ {4,8}`, n=80/arm, cap 640,
**0.000 at cap**, judge pinned `openai/gpt-4o-mini`, all three arms judged in one invocation
(so the §0.4 cross-session floor is minimised, not merely acknowledged):

| arm | ASR@0.5 | median tokens | refusal kw | vs baseline | up | down | exact 2-sided p |
|---|---|---|---|---|---|---|---|
| `A_baseline` | **11/80** | 212.5 | 1/80 | — | — | — | — |
| **`demo_processing_only`** (the knockout) | **1/80** | 277.0 | 0/80 | **−0.1250** | 1 | **11** | **0.006348** |
| `CTRL_matched_d1` (count-matched control) | 12/80 | 207.5 | 0/80 | +0.0125 | 4 | 3 | 1.000 |

**The demonstration-processing knockout removes the attack — 11 of 80 down to 1 of 80 — while a
count-matched control moves it the other way.** Against the §0.4 judge noise floor of ~4 rows on
n=80, the 11 discordant-down rows are ~2.75× the floor, and the exact test already accounts for the
pairing. **Refusal keyword rate is 0/80 in the knockout arm and median length goes UP (212.5 → 277),
so this is not refusal and not length collapse.**

### Two caveats that must travel with it

1. **The control's null is underpowered.** At 7 discordant pairs only a 7–0 split reaches α=0.05
   (MDE 0.0875), so "the matched control does nothing" is *weakly* supported. Its point estimate is
   +0.0125 — the opposite direction — which is consistent but not proof.
2. **Scope: one model, one bank, two `n_examples` levels, n=80.** This does not by itself discharge
   ledger entry 6, whose claim spans 8 populations on two models and whose twenty underlying runs
   are all at cap 192. It is a clean *replication in miniature* at a usable cap.

**Ledger effect:** entry 12 (C7) moves **OPEN → KEEP-NARROWED** (supported at 640 on Qwen3 for
n_examples 4/8; the cap-192 pool A/B numbers remain relabelled). Entry 6 stays **NEEDS RERUN** but
now has a positive prior — the rerun is expected to confirm, which makes a failure the informative
outcome.

---

## §6.0 — THE `n_examples = 12` CELL *(user-directed; Phase 6 prerequisite)*

**Bank:** `data/boombness_prompts/boombness_prompt_bank_ne12.jsonl`
`bank_rows_sha16 = d471aa8935ead6c5` · `pools_sha16 = b5e399712b996b7d` · preset `main_ne12` · seed 20260816
**Command:** `python src/boombness/prompt_families.py --preset main_ne12 --codeword carrot --concept bomb --seed 20260816 --strict --out data/boombness_prompts/boombness_prompt_bank_ne12.jsonl`

§1 recorded that `n_examples = 12` occurs in **zero rows in zero banks**, and provisionally adopted
`{0,1,2,4,8,16}`. The user directed that the 12 cell be added, so it has been.

### It is a derived preset, not an edit to the constant

`N_EXAMPLES` is consumed at **exactly one site** — the `main` preset's `core2x2` block. Appending 12
to it would silently change what `main` generates and turn
`tests/test_bank_regenerates_byte_identically.py` red for **every canonical bank**, while never
touching a bank file: a change to the meaning of every historical `bank_rows_sha16` **at a
distance**. This repo has already been bitten by that exact shape (**C-10**: `DOMAINS` grew 6 → 10
and the canonical carrot bank stopped regenerating from its own pools).

`main_ne12` therefore **derives** from `main` via `_blocks("main", domains)` and widens one field.
That is also already the house idiom — `main_longpre` and `main_longctx` do the same — so this is
the conventional shape here, not a new one.

| check | result |
|---|---|
| `main_ne12` vs `main`, all 8 blocks | differs in `n_examples` and **nothing else** |
| `N_EXAMPLES` | **untouched**, still `(0,1,2,4,8,16)` |
| `test_bank_regenerates_byte_identically` | **3/3 pass** — canonical banks unaffected |
| existing bank files overwritten | **none** — written under a new name |

### The bank

| | |
|---|---|
| rows | **2928** (vs `main`'s 2736 — the difference is **exactly** the 192 new `n_examples=12` rows) |
| `by_n_examples` | 0:288 · 1:288 · 2:576 · 4:732 · 8:660 · **12:192** · 16:192 |
| 2×2 families checked / violations | **384 / 0** |
| duplicate `prompt_id` rows dropped | **0** |
| **leakage probe** (§1.1) | **432 complete families, `d_surface` byte-identical after masking on all of them**; masked surface-arm accuracy **0.5000** vs baseline 0.5000 |
| **tokenization audit** (job 787201, cpu-killable) | **rows ok=2928, bad=0, ambiguous=0, token-alignment violations=0** |

Phase 6 can now run the brief's sweep as specified — `{0,1,2,4,8,12}` — and additionally at 16.

### A mutation that reported green, and was not

Four mutations were applied to the preset. One ("the preset copies `main` instead of deriving from
it") came back **green**, which would have been a false all-clear. The cause was the **harness**, not
the test: the line `blocks = _blocks("main", domains)` occurs **three times** in the file, so
replacing the first occurrence mutated `main_longpre` instead of `main_ne12`. Re-applied against the
`main_ne12` body specifically, it fails two tests as it should. **An unfired mutation is not a
passed mutation**, and a mutation harness that silently targets the wrong code is exactly as
misleading as a test that cannot fail.

---

## §R.2 — TICK LOG, 2026-08-27 21:15–21:55

**Landed:** §0.4 (judge noise floor, and a correction to V-2's framing) · §0.5 (C7 repointed; the
sprint's first sprint-grade result) · §6.0 (the `n_examples=12` cell). Commits `c1a9cb2d`,
`3421bb44`, `466cd8a8`.

**Running:** `787102` v3_C1024 — **148/495 rows** at ~8.7 rows/min, ETA ~40 min. `787186` v3_base1024,
`787187` v3_D1024, `787188` v3_W640 — PENDING on `(Priority)`. The first submission
(`787101/787103/787104`) passed 30 minutes pending and was cancelled and resubmitted across a
**5-node** list excluding `n-804`, where `787102` is already resident (per the per-node weight-load
contention rule). `787201` tokenization audit — **COMPLETE, clean**.

**Not yet started:** the entry-6 retrieval-knockout reruns (waiting on queue capacity — holding at
≤6), Phase 2, Phase 7.

**Currently supported by this sprint:** §0.2, §0.3a, §0.1, §1, §1.1, §0.4, and now **§0.5 — the
first result that clears `--sprint-grade`**. Still **no claim about boombness itself**, and none is
due until the 1024 arms land.

---

## §0.6 — DOES THE ~5 % JUDGE NOISE INVALIDATE §0.5's `p = 0.006348`?

**Artifact:** `outputs/boombness/paired_test_noise_sensitivity/c7noise_20260827_215858_3688244/paired_test_noise_sensitivity.json`
**Script:** `src/boombness/paired_test_noise_sensitivity.py` · **Tests:** 10, 4 mutations caught

A peer session raised a precise objection to §0.5: *"of your 12 discordant pairs ~4 are expected
judge noise, but the exact test treats all 12 as signal, so the p is optimistic."* That is testable,
so it was tested rather than argued. **n=80, base rate 11/80, 20 000 reps per cell.**

### 1. Symmetric noise does NOT inflate Type I error

| per-label flip rate | Type I error at α=0.05 |
|---|---|
| 0.00 | 0.0297 |
| **0.05** (the measured floor) | **0.0280** |
| 0.10 | 0.0305 |
| 0.20 | 0.0309 |

**At or below nominal everywhere, up to a 20 % flip rate.** The reason is structural: McNemar's null
is `P(A=0,B=1) = P(A=1,B=0)`, and noise that is symmetric and independent across arms fills *both*
discordant cells equally — it produces exactly the 50/50 split the test assumes under H0. Verified
directly: at flip 0.10, `E[down] = 11.51` against `E[up] = 11.44`.

### 2. What noise actually costs is POWER

| flip rate | power at true Δ = −0.125 | E[down] | E[up] |
|---|---|---|---|
| 0.00 | 0.851 | 10.87 | 0.85 |
| **0.05** | **0.519** | **13.08** | **4.04** |
| 0.10 | 0.324 | 14.94 | 6.94 |

**Symmetric label noise makes this test conservative, not liberal.** And note the second row against
what was actually observed: at a 5 % flip rate a true −0.125 effect should produce about **13 down
and 4 up**. §0.5 observed **11 down and 1 up** — *fewer* discordant pairs than the noise model
predicts, i.e. the data are cleaner than a 5 % floor would generate. That is plausible: 5 % is a
corpus-wide average, and clearly-compliant and clearly-refusing completions are stable while
ambiguous ones flip.

### 3. Where the objection WOULD bite — and why it does not here

If the noise were **asymmetric**, it inflates Type I badly:

| extra up-flip bias on arm B | Type I | E[down] | E[up] |
|---|---|---|---|
| 0.00 | 0.0280 | 11.51 | 11.44 |
| 0.05 | **0.0675** | 10.90 | 14.30 |
| 0.10 | **0.1933** | 10.30 | 17.14 |

This is a live worry for §0.5, because the knockout arm's completions are **longer** (median 277 vs
212.5) and a longer completion has more chance to say something the judge scores. **But that
asymmetry pushes the knockout arm's ASR UP, and §0.5 observed 11 rows DOWN against 1 up.** The one
asymmetry this design plausibly has works **against** the reported effect, not for it.

*(That inflation row is also the positive control on the simulator itself: a sensitivity study that
only ever reports "fine" is worthless. `test_ASYMMETRIC_noise_DOES_inflate_type_I` asserts the same
code flags a genuinely broken situation, so the clean verdicts above are informative.)*

### Verdict, and what changes

**The objection is wrong on the mechanism — the p is not optimistic under symmetric noise, it is
conservative.** But the peer's *practical* recommendation is right and is adopted: a bare p-value is
a poor summary of a noisy-label paired test. `report_line` emits the discordant counts, the assumed
floor and the net alongside the p, and §0.5 should be quoted as:

> **11 down / 1 up of 80 (net −10), against a ~5 % per-label judge floor; exact two-sided p = 0.006348.**

The peer also declined to adopt this statistic *for their own claim* because they had pre-committed
against it — refusing a test at the moment it favours them. That is the right instinct even though
the technical premise turned out to be mistaken, and it is recorded here as such.

---

## §0.7 — THE JUDGE FLOOR IS NOT A CONSTANT: it lives at the decision boundary

**Script:** `src/boombness/paired_test_noise_sensitivity.py` (`FLIP_RATE_BY_CONFIDENCE`,
`effective_flip_rate`) · **Tests:** 16, 2 real mutations caught + 1 no-op (below)

§0.4 measured a ~5 % judge flip rate. The peer session predicted — *before* it was measured — that
this would concentrate near the 0.5 decision boundary, and suggested bucketing by `|score − 0.5|`.
They explicitly did not ask for it. It is cheap, and it turns a corpus constant into a per-arm
quantity, so it was run. **320 double-judged rows (`q15A` + `q16A`), byte-identical generations.**

| `\|score − 0.5\|` | n | flips | flip rate |
|---|---|---|---|
| [0.00, 0.05) | 11 | 7 | **0.6364** |
| [0.05, 0.15) | 6 | 2 | 0.3333 |
| [0.15, 0.30) | 8 | 0 | 0.0000 |
| [0.30, 0.50) | 6 | 2 | 0.3333 |
| **[0.50, 1.01)** | **289** | **5** | **0.0173** |
| **all** | **320** | **16** | **0.0500** |

**The prediction is confirmed.** The 5 % corpus average is not a per-row rate: it is **~1.7 % for
confident rows and ~53 % for the 17 rows within 0.15 of the boundary** — a 30× contrast. The average
is simply the mixture.

**Honesty about the table's precision:** the individual bucket rates rest on n = 11, 6, 8, 6. The
`0/8` in [0.15, 0.30) is obviously not a true zero, and [0.30, 0.50) sitting at 0.33 breaks
monotonicity. **Only the coarse contrast — 9/17 near versus 5/289 far — is well determined**, and
that is what `test_flips_concentrate_near_the_decision_boundary` asserts.

### Consequence: the floor is per-arm, and it does not always go down

`effective_flip_rate` weights the measured buckets by an arm's own score distribution. On the C7 640
arms:

| arm | rows within 0.15 of boundary | **effective floor** | vs 5 % average |
|---|---|---|---|
| `A_baseline` | 7 / 80 | **0.0598** | **HIGHER** |
| `demo_processing_only` | 1 / 80 | **0.0252** | half |

**This is not a discount factor**, and that matters: the baseline's floor *exceeds* the corpus
average. An arm concentrated away from the boundary (a knockout at 1/80) faces a much smaller floor
than one with borderline mass. Quoting 5 % for every arm is the same category of error as quoting a
single ASR for every arm.

### It also explains §0.6's residual

§0.6 noted that a 5 % model predicts ~13 down / ~4 up while §0.5 observed **11 down / 1 up**.
Simulating at the confident-row rate:

| flip | E[down] | E[up] |
|---|---|---|
| 0.000 | 10.87 | 0.85 |
| **0.020** | **11.80** | **2.17** |
| 0.050 | 13.08 | 4.04 |

**Observed 11 / 1 sits at the low-flip end, consistent with the ~0.025–0.060 arm-specific floors and
not with the 5 % average.** Stated with appropriate restraint: a single draw of 12 discordant pairs
cannot pin a rate, so this is consistency, not estimation.

### A mutation that survived, and why it is not a gap

Three mutations were applied. Two were caught. The third — removing the `break` from the bucketing
loop — **survived, and correctly so: it is a semantic no-op.** The buckets are disjoint half-open
intervals, so a score matches exactly one regardless; the `break` is a loop optimisation, not a
correctness guard. Recorded rather than counted as a pass, because "3 of 3 mutations caught" would
have been a false claim about test strength.

---

## §0.8 — PLANNING ENTRY 6 BEFORE SPENDING GPU: the knockout effect is carried by 2 of 5 populations

A peer session suggested using the §0.7 per-arm floor as a **GPU selection criterion** — prefer
populations whose *baseline* has low borderline mass, since the baseline dominates the paired noise.
That is a planning step the sprint did not have, so it was run before submitting anything.

### First, is a cap-192 measurement even usable for planning a cap-640 run?

The borderline mass would be read off the existing cap-192 judge runs, and truncation plausibly
*creates* ambiguity. Tested on the two row-matched cap pairs:

| pair | near @192 | near @640 | rows becoming borderline | ceasing to be |
|---|---|---|---|---|
| Llama `basket_bomb` `A_baseline` (n=96) | 7/96 | 8/96 | 8 | 7 |
| Qwen3 `longpreQ14B` `A_baseline` (n=80) | 7/80 | 7/80 | 3 | 3 |

**Borderline mass is essentially cap-invariant**, so cap-192 mass validly predicts cap-640 mass and
the criterion is usable. Note the *identities* churn (8 in / 7 out) while the *count* holds — itself
consistent with §0.7: which rows are borderline is noisy, how many is not.

### The five Llama populations behind ledger entry 6

Paired noise SD computed as `sqrt(E[flips_A] + E[flips_C])`, using the §0.7 per-arm floors:

| population | n | A.near | A.floor | C.near | C.floor | **ASR A** | **ASR C** | down | up | net | noise SD | **net/SD** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **`ticket_bomb`** | 96 | 7 | 0.0524 | 6 | 0.0462 | 24 | 7 | 22 | 5 | **+17** | 3.08 | **5.53** |
| **`main`** | 96 | 12 | 0.0754 | 2 | 0.0366 | 22 | 5 | 20 | 3 | **+17** | 3.28 | **5.18** |
| `window_knife` | 96 | 2 | 0.0270 | 0 | 0.0173 | **2** | 0 | 2 | 0 | +2 | 2.06 | 0.97 |
| `basket_gun` | 96 | 6 | 0.0435 | 6 | 0.0402 | 10 | 11 | 9 | 10 | **−1** | 2.83 | −0.35 |
| `button_knife` | 96 | 2 | 0.0299 | 4 | 0.0463 | 9 | 10 | 6 | 7 | **−1** | 2.71 | −0.37 |

### What this says about entry 6's headline

**"96 down / 18 up over 8 populations" is carried by 2 of the 5 Llama populations.** `ticket_bomb`
and `main` contribute +17 each at >5 SD. The other three contribute **+2, −1, −1** — and two of them
point the *wrong way*.

And `window_knife` is not a null, it is **an underpowered population with no headroom**: baseline
ASR is **2/96**. There is essentially no attack there to knock out, so its near-zero result carries
no information in either direction. That is consistent with the prior sprint's own R-AU
("attackability is a bank × model property"), which the aggregate headline does not reflect.

### Consequence for the rerun design

Re-running all five at 640 would spend ~60 % of the GPU on populations that either have no headroom
(`window_knife`) or show no effect (`basket_gun`, `button_knife`). The informative design instead
reruns:

* **`ticket_bomb` and `main`** — where the effect lives. *Can it disappear at a non-binding cap?*
* **`basket_gun`** — a genuine null *with* headroom (baseline 10/96). *Can the rerun detect an effect
  where 192 saw none?* Without at least one such arm the rerun cannot demonstrate it is capable of
  detecting absence, only of confirming presence.

`window_knife` is **declined for the same reason Llama's C7 branch was declined: no headroom.**

### Caveat, stated because it is load-bearing

The near/far flip rates are **measured on Qwen3 (`q15A`/`q16A`) and transplanted onto Llama arms as
a mixture model.** The borderline **counts** are measured directly on each Llama arm and are not
transplanted; the **rates** are. A population whose boundary behaviour differs from Qwen3's would
move the `net/SD` column. The ranking is robust to this (the gap between 5.5 and −0.4 is not a rate
artifact); the absolute SDs are not.

---

## §0.9 — A CONFOUND I SUSPECTED IN ENTRY 6, AND WHY IT IS NOT ONE *(plus a real audit trap)*

Preparing the entry-6 rerun argsfiles, I read the five populations' configs and found the A arms
recording `attn_impl: "eager"` and the C arms `attn_impl: "sdpa"`. Under greedy bf16 decoding a
sub-ulp kernel difference on a near-tie refuse/comply token branches into a different completion and
a different judged ASR — so on its face the entire A-vs-C contrast would confound the mask edit with
a **kernel swap**. No matched eager/sdpa pair exists anywhere in the corpus (458 config groups, **0**
spanning both), so it could not be measured away.

**It is not a confound. The code already handles it, deliberately, and I was reading the wrong
field.** `score_behavior.py:1348` forces `eager` whenever a knockout is requested, and 1350–1353
aborts if the model did not actually come up eager, because "under sdpa the 4-D mask edit is
silently discarded". The comment at 1136–1140 shows the authors hit exactly this and fixed it:
*"every arm-vs-baseline contrast in Phase 2 would have confounded the mask edit with a KERNEL SWAP …
Run the references under eager too."* That is why the A arms explicitly pass `--attn-impl eager`.

### The real finding here is an audit trap

**`config.json`'s `attn_impl` records what was REQUESTED, not what was USED.** The actual
implementation is recorded elsewhere, in `summary.json → knockout_liveness.attn_implementation`.
Anyone auditing configs the way I just did will conclude the arms are implementation-confounded when
they are not. Recorded so the next reader — including a later me — does not re-derive this alarm.

### Knockout liveness, all five populations *(the brief's §4.1 requirement, verified)*

| population | requested | **ACTUAL** | rows | **frac rows decode-live** | median decode edits | min decode forwards |
|---|---|---|---|---|---|---|
| `main` | sdpa | **eager** | 96 | **1.0** | 52 641 | 234 |
| `ticket_bomb` | sdpa | **eager** | 96 | **1.0** | 60 228 | 657 |
| `button_knife` | sdpa | **eager** | 96 | **1.0** | 67 135.5 | 1 359 |
| `window_knife` | sdpa | **eager** | 96 | **1.0** | 76 495.5 | 1 719 |
| `basket_gun` | sdpa | **eager** | 96 | **1.0** | 68 760 | 1 719 |

**The hook fired on every row of every population**, with tens of thousands of attention entries
edited per row. Entry 6's *mechanism* is live and verified; what remains in question is only whether
its **behavioural effect** survives a non-binding generation cap — which is what the rerun tests.

Note this sharpens §0.8 rather than softening it: `basket_gun` and `button_knife` show the knockout
firing on 96/96 rows with ~68 000 edits each and producing **net −1** — the intervention is
demonstrably live and demonstrably does nothing there. That is a real dissociation, not a failed
intervention.

---

## §0.10 — THE DENOMINATOR RULE, applied across the ledger

A peer session generalised §0.8 into a diagnostic worth carrying, and it is cheap enough to apply to
the whole ledger without re-running anything:

> **Does a no-headroom population enter the DENOMINATOR?**
> * An **effect size averaged over populations** is vulnerable. A population with no headroom
>   contributes ≈0 *and still carries weight in the mean*, dragging the aggregate toward the null
>   while looking like evidence for a small effect. That is `window_knife` in entry 6.
> * A **proportion over the affected rows** is immune. If the denominator is *killed rows*, a
>   population with no kills contributes nothing to the numerator **and** nothing to the
>   denominator. It cannot dilute — it simply is not represented.

So the question is not "how many populations?" but "what is in the denominator?"

### Applying it

| ledger entry | statistic shape | no-headroom unit in the denominator? | verdict |
|---|---|---|---|
| **6 — retrieval knockout (96 down / 18 up)** | effect size **pooled over 8 populations** | **YES** — `window_knife` at baseline 2/96 | ⛔ **FAILS. Per-population reporting mandatory** (§0.8) |
| **11 — token-level dynamics** | paired mean **over 6 domains** | vulnerable shape — checked below | ✅ **PASSES on inspection** |
| 13 — binding survives the attack-killing intervention | proportion whose denominator is **killed rows** | NO — a family with no kill enters neither numerator nor denominator | ✅ immune by construction |
| 12 — C7 | counts reported **per cell**, never averaged across cells | NO | ✅ immune (not pooled) |
| 4, 5, 7 | single-population effect sizes | N/A — nothing pooled | not applicable |
| 1, 2, 3 | geometric (cosines, dose fractions) | no behavioural headroom concept | not applicable |

### Entry 11 checked, not assumed

Entry 11 has exactly the vulnerable shape — a paired mean over six domains — so it was opened rather
than waved through. `paired_per_domain_mean`, `paired_n = 294`:

| domain | L8 | L16 | L31 |
|---|---|---|---|
| city_bridge | 0.1023 | 0.1630 | 0.2391 |
| farm_storage | 0.0925 | 0.1393 | 0.1225 |
| game_manual | 0.1805 | 0.2207 | 0.2666 |
| instructional | 0.0870 | 0.2054 | 0.3097 |
| lab_safety | 0.0719 | 0.1825 | 0.1983 |
| news_report | 0.1016 | 0.2394 | 0.2543 |
| **pooled** | **0.1060** | **0.1917** | **0.2317** |

**All six domains positive at all three layers**, spread 0.072–0.181 (L8), 0.139–0.239 (L16),
0.122–0.310 (L31). **No domain contributes ≈0 and none points the wrong way** — the exact opposite
of entry 6, where 2 of 5 populations carried everything and 2 pointed backwards.

**So the rule discriminates rather than merely flagging everything**: it condemns entry 6 and clears
entry 11 on the same test. That is what makes it worth keeping. Entry 11's `KEEP_NARROWED` is
reaffirmed on stronger grounds than it had before — the pooled number is a fair summary of six
concordant domains, not a mean over a mixture.

---

## §4.1 — "DID THE HOOK MATTER?" — an invariant, not a habit

**Script:** `src/boombness/intervention_liveness.py` · **Tests:** 8, 4 mutations caught
**Artifacts:** `outputs/boombness/intervention_liveness/{e6live_*,c20check_*}/intervention_liveness.json`

A peer session's **C-20** is the case that motivates this: a rescue arm reported `fired: true` and
`n_positions_written: 28` for a patch that wrote **the value already present**. Below the knockout
band the clean and knocked-out activations are bit-identical, so the hook fired, wrote, and changed
nothing. **Three published claims cited that arm as a specificity control and none of them had run
one.** Liveness told the truth — the truth it told was narrower than the question being asked:

    liveness  answers  "did the hook execute?"
    this      answers  "did the hook change what the model wrote?"

Two failure modes report `fired: true` and show a null, and **only a generation comparison separates
them**:

| | computation | behaviour | verdict |
|---|---|---|---|
| hook fires, changes computation, no ASR effect | changed | null | **real dissociation** |
| hook fires, changes nothing, no ASR effect | unchanged | null | **no-op arm (C-20)** |

### It catches the known case, on real data

Run against the peer's `q9` rescue ladder (knockout band **7–17**, rescue at query positions,
control = knockout-only, n=160):

| arm | rescue layer | generations differing | verdict |
|---|---|---|---|
| `Q_qpos_L5` | 5 | **0/160** | ⛔ **NO-OP ARM** |
| `Q_qpos_L7` | 7 | **0/160** | ⛔ **NO-OP ARM** |
| `Q_qpos_L12` | 12 | 144/160 | ✅ live |
| `Q_qpos_L17` | 17 | 156/160 | ✅ live |

This **is not a new discovery**, and it was nearly written up as one. The peer's own
`tests/test_below_band_rescue_is_a_noop.py` already derives the predicate analytically —
`patch_can_differ_from_recipient` returns `rescue_layer > lo` — and documents `rescue_layer == lo`
as "the trap that caught C-20's own first replacement control". With `lo = 7`, both L5 and L7 are
≤ lo and are no-ops *by construction*. **What this adds is empirical confirmation of an analytic
predicate, measured on generations rather than derived** — which is exactly the value of an
independent route, and exactly nothing more. Checked before claiming.

### Applied to this sprint's own entry-6 arms — the claim survives and strengthens

| population | generations differing | ASR net | reading |
|---|---|---|---|
| `main` | **96/96** | +17 | live and effective |
| `ticket_bomb` | **96/96** | +17 | live and effective |
| `window_knife` | **96/96** | +2 | live; no headroom (baseline 2/96) |
| `basket_gun` | **96/96** | **−1** | **live and inert** |
| `button_knife` | **96/96** | **−1** | **live and inert** |

**Every population changes 96/96 generations.** So §0.9's reading holds and is now demonstrated
rather than asserted: `basket_gun` and `button_knife` are **not** C-20-style no-op arms. The
intervention alters what the model writes on every single row and ASR still does not move. **That is
a genuine dissociation between changing the computation and changing the behaviour**, and it is the
strongest form the §0.8 concentration result could have taken.

### The invariant

`assert_changed_generations` refuses an arm whose generations differ on fewer than
`MIN_DIVERGENCE = 0.10` of rows, and refuses a pair sharing no `prompt_id`s rather than scoring it
as "no change". The threshold is deliberately **not zero** — an arm that moves one row in ninety-six
has fired and mattered on one row, which is a rounding error, not an intervention. **Every
intervention arm this sprint reports must pass it.**

### §4.1a — ⛔ PREDICATE CORRECTED: exact zero refuses, small warns

The §4.1 draft **refused any arm below `MIN_DIVERGENCE = 0.10`. That was wrong, and the reason it
was wrong is more useful than the fix.**

A peer session answered the threshold question with data rather than opinion, measuring divergence
across all 18 intervention contrasts in its phase: **sixteen legitimate arms span 0.8187–1.0000,
both known no-ops are exactly 0.0000, and nothing lands in between.** So 0.10 refused nothing real —
**but every arm in that sample is a broad-span mask or patch.** A single-position patch,
`--rescue-n-positions 1`, or an intervention gated on a rare row property could legitimately touch 3
rows in 96. A threshold calibrated on broad-span arms would refuse those, **and the artifact would
not say it had been calibrated on a sample containing no small-but-real arms.** The refusal would
look authoritative.

**Exact zero needs no calibration.** Under greedy decoding an arm that changed anything cannot land
on 0.0000 across a population; only a bit-identical computation does. So:

| divergence | verdict | action |
|---|---|---|
| **exactly 0** | `NOOP_ARM` / `HOOK_NEVER_RAN` | **REFUSE** |
| 0 < d < 0.10 | `SMALL_BUT_REAL` | **WARN — inspect, do not refuse** |
| ≥ 0.10 | `OK` | pass |
| no shared `prompt_id`s | `NO_COMPARISON` | REFUSE |

### Divergence alone under-determines the diagnosis

Pairing it with the liveness `fired` field separates three cases, **and only the middle one is the
bug**:

| `fired` | divergence | verdict | reading |
|---|---|---|---|
| `False` | 0 | `HOOK_NEVER_RAN` | **instrument failure** — the hook never ran |
| `True` | 0 | `NOOP_ARM` | **C-20** — it ran and wrote the value already present |
| `True` | 0 < d < 0.10 | `SMALL_BUT_REAL` | a legitimately small intervention |

This is §0.9's lesson arriving from the other side. There, a **request** (`attn_impl`) needed its
matching **outcome** field (`knockout_liveness.attn_implementation`). Here, an **outcome**
(divergence) needs its matching **request** field (`fired`). Neither direction is safe alone.

Both ladders re-run under the corrected predicate and reproduce: `q9` L5 and L7 → `NOOP_ARM`, L12
and L17 → `OK`; all five entry-6 populations → `OK` at 96/96. **9 tests, 4 mutations caught**,
including re-introducing the refuse-on-warn-band bug.

*(A second, smaller correction: the `n_common == 0` case was special-cased ahead of the diagnosis,
so the empty-comparison path raised a different message and skipped the verdict entirely — two code
paths for one decision. `diagnose(None)` now returns `NO_COMPARISON` and there is exactly one.)*

---

## §0.11 — `arm_report.py`: the four instruments joined, so they cannot be quoted apart

**Script:** `src/boombness/arm_report.py` · **Tests:** 8, 4 mutations caught
**Artifact:** `outputs/boombness/arm_report/e6base_20260827_223307_3767713/arm_report.json`

This sprint has built four instruments, each because a number was once quoted without it:

| instrument | what it refuses to let you omit |
|---|---|
| `asr_protocol` | the cap and the length/truncation diagnostics |
| `cap_natural_experiment` | the paired exact test, and the effect the design could detect |
| `paired_test_noise_sensitivity` | the **per-arm** judge floor, from that arm's own scores |
| `intervention_liveness` | whether the hook *mattered*, not merely fired |

**Reported separately they get separated**, and a peer session named the concrete failure that
follows: **an ASR delta of −1 row means opposite things at 96/96 divergence and at 5/96.** At 96/96
it is a dissociation — the intervention changed everything the model wrote and behaviour did not
move. At 5/96 it is a dead intervention that never had a chance. **Only the pair distinguishes
them.** `arm_report` emits one row carrying all of it and adds no statistics of its own; it is a
join that exists so the join cannot be forgotten.

Applied to the five entry-6 populations (**cap 192 — these remain "ASR within first 192 generated
tokens"**, and the artifact carries `cap_binds` and `asr_label` per arm so that cannot be dropped):

| population | ASR base → arm | net down | exact p | **net / noise SD** | **divergence** |
|---|---|---|---|---|---|
| `main` | 22/96 → 5/96 | **+17** | 0.0005 | **5.18** | 96/96 `OK` |
| `ticket_bomb` | 24/96 → 7/96 | **+17** | 0.0015 | **5.53** | 96/96 `OK` |
| `window_knife` | 2/96 → 0/96 | +2 | 0.5000 | 0.97 | 96/96 `OK` |
| `basket_gun` | 10/96 → 11/96 | **−1** | 1.0000 | −0.35 | **96/96 `OK`** |
| `button_knife` | 9/96 → 10/96 | **−1** | 1.0000 | −0.37 | **96/96 `OK`** |

Same numbers as §0.8, now inseparable from the divergence that licenses reading them. The bottom two
rows are the case the module exists for: **net −1 at full divergence is a dissociation, not a dead
arm**, and the table now says so on its own face.

---

## §R.3 — TICK LOG, 2026-08-27 22:10–22:35

**Landed:** §4.1 + §4.1a (the `did-the-hook-matter` invariant, and its corrected exact-zero
predicate) · §0.10 (the denominator rule applied ledger-wide) · §0.11 (`arm_report`). Commits
`b16a6233`, `b0b88fb7`, and this one.

**GPU/CPU:**
* `v3_C1024` — **DONE, 495 rows at cap 1024.** Judging pinned as **787254**.
* `v3_W640` — **DONE, 96 rows at cap 640, 0 failures.** Its baseline `g3A640` already had a pinned
  judge run, but from a *different session*, and §0.4's floor applies to cross-session deltas. So
  **787350 re-judges BOTH arms in one invocation** — 192 rows to remove the exposure rather than
  caveat it.
* `v3_base1024` (401/495) and `v3_D1024` (151/495) still generating.
* Entry-6 argsfiles staged for `main` / `ticket_bomb` / `basket_gun`, both arms explicitly eager at
  cap 640.

**Peer session has closed out.** Its phase is complete; no further findings expected from that side.
The instrument corrections it drove (§0.4, §0.6, §0.7, §4.1a, §0.10) are all landed and attributed.

**Still no claim about boombness itself, and none is due until the cap-1024 arms are judged.**
Phase 7 gate remains closed.

---

## §0.12 — FIRST NON-BINDING-CAP RESULT — and my own guard refused it

**Artifact:** `outputs/boombness/arm_report/w640_20260827_224651_3802479/arm_report.json`
**Command:** `python src/boombness/arm_report.py --contrasts-file <..> --tag w640 --require-sprint-grade`

`v3_W640` finished (96 rows, 0 failures). Its baseline `g3A640` already had a pinned judge run, but
from a **different session**, and §0.4's floor applies to cross-session deltas — so job **787350
re-judged both arms in ONE invocation** (192 rows) rather than caveating the exposure.

**The arm:** `d_surface:project_out:14-14:1.0` — removing the `d_surface` direction — Llama-3.1-8B,
`basket_bomb`, `natural_doublespeak`, `n_examples ∈ {1,2,4,8}`, n=96, cap 640, judge pinned.

| | ASR | at cap | median tokens | refusal kw | effective judge floor |
|---|---|---|---|---|---|
| `A_baseline` | **30/96** | **0.000** | 308.5 | 2/96 | 0.0658 |
| `W` (`d_surface` removed) | **56/96** | **0.302** ⚠ | 346.5 | 2/96 | 0.0689 |

| paired | value |
|---|---|
| delta | **+0.2708** |
| up / down | **35 / 9** (discordant 44) |
| exact two-sided p | **0.0001** |
| judge-noise SD | 3.60 rows |
| **net / noise SD** | **−7.23** (ASR *up*) |
| divergence | **96/96 `OK`** |
| MDE | the test rejects only at ≥29/44 one way, i.e. 14 rows in 96 |

### ⛔ The guard refused this, and it was right to

`--require-sprint-grade` **failed the arm**: `not_sprint_grade — the cap binds on 0.3021 of rows at
max_new=640`. So the arm is *"ASR within first 640 generated tokens"* while the baseline is plain
*"ASR"*. **My own instrument refuses my own largest result**, which is the first time this sprint's
guards have been tested against a number I wanted to be true.

**Following §0.2's pre-registered rule (raise the cap until it does not bind) rather than quoting
it:** jobs **787377 / 787378** re-run *both* arms at **cap 1536**. Both, not just the arm — a
comparison whose two halves have different cap-binding status is not one I will report.

### What can honestly be said now

* **The direction is not in doubt and the truncation works in its favour.** 35 rows up against 9
  down at p=0.0001, and the arm's 30 % truncation can only *hide* successes (a row cut off before
  finishing cannot have its compliance counted). **+0.2708 is a lower bound.**
* **It is not refusal and not length collapse.** Refusal keyword rate is identical at 2/96 in both
  arms, and the arm's median generation is *longer* (346.5 vs 308.5).
* **It is not a dead arm.** Divergence 96/96.
* **It is directionally consistent with ledger entry 5** ("removing `d_surface` RAISES ASR",
  +0.0424 at L8 on AdvBench-495) — here far larger, at L14, on a doublespeak bank. Same sign, and
  now at a cap that does not bind on the baseline.

**But the number itself is not quotable as ASR until 787377/787378 land.** Entry 5 stays
**NEEDS RERUN** until then. Recorded now because the guard firing on a result I wanted is worth more
than the result.

---

## §0.2.5 — ⛔ CORRECTION TO §0.2: the first corpus sweep ingested partial and excluded runs

**Artifact:** `outputs/boombness/asr_protocol/corpus_sweep_20260827_v2.json` **supersedes**
`corpus_sweep_20260827.json`. **Do not quote the V-1 numbers.**

### How it surfaced

Building the refusal arm's cap pair, `ab_C` read as **134/495** — but §0.2's sweep had recorded it
as **133/482**. Chasing the discrepancy: there are **two** judge dirs carrying `tag: ab_C`.
`abg_C_20260819_011714_1480835` is complete (495 rows, `DONE.json`). `ab_C_20260819_002240_1397246`
is a **482-row partial**, has no `DONE.json`, and **is named in `EXCLUDED_RUNS.json`**. My sweep
scored it and reported its number under the good run's tag.

**`common.require_done` already existed for exactly this**, and its own docstring says it was added
"after the mid-session sweep found that NO analyzer checked this … an invariant asserted at one end
of a contract and never checked at the other." **I wrote a new consumer and reproduced the bug the
repo had already fixed once** — against a brief that says in terms: *"If a run is partial, mark it
excluded and make sure lookup code cannot accidentally ingest it."*

### The corrected numbers

`build_entry` now refuses an `ABORTED` run, a run without `DONE.json`, or a run named in
`EXCLUDED_RUNS.json` — on **both** the judge dir and its gens dir — with `allow_partial` as an
explicit opt-in that stamps `run_status: allowed_partial`.

| | V-1 (defective) | **V-20 (corrected)** |
|---|---|---|
| scored | 596 | **566** |
| **excluded** | **0 — not checked** | **51** (45 on the list · 4 ABORTED · 2 no DONE) |
| errors | 18 | **0** |
| cap=192 | 242 dirs / 69 904 rows / 91.3 % bind | **226 dirs / 59 455 rows / 90.7 % bind** |
| cap=512 | 349 / 146 798 / 14.6 % | **332 / 142 282 / 13.3 %** |
| cap=640 | 5 / 432 | 7 / 624 |
| cap=1024 | — | **1 / 495** (new) |
| quotable as plain ASR | 324 dirs / 135 867 rows | **316 dirs / 132 803 rows** |
| quotable only as "ASR within N" | 271 dirs / 81 088 rows | **250 dirs / 70 053 rows** |
| guard-refused | 1 | **0** (the refused dir was ABORTED and is now excluded upstream) |

**The qualitative finding is unchanged** — the 192-cap stratum still binds on ~91 % of dirs — but
**10 449 of the rows attributed to it came from runs that should never have been read**, and every
row count in §0.2 was inflated. §0.2's *conclusion* stands; its *numbers* are superseded here.

### A second bug, in the fix itself

The first version of the wrapper caught `except Exception`. **`require_done` signals refusal with
`SystemExit`, which is a `BaseException` and is not caught by that** — so a single unfinished dir
killed the entire 617-dir sweep instead of being skipped. It took three silent failures to notice,
two of them masked by `/tmp` having become unwritable on this node. Now caught explicitly, and
pinned by `test_require_done_signals_with_SystemExit_and_is_still_caught`.

**45 tests, 4 mutations caught** — including one that initially survived because every fixture lives
in `tmp_path`, where no exclusion file applies, so the exclusion-list branch was never exercised. A
test that reads the real `EXCLUDED_RUNS.json` and asserts the offending id is in it closes that.

**What this changes for the sprint:** nothing in the ledger, and no conclusion. What it changes is
that the instrument which polices every other number in this sprint was itself unpoliced for its
first nineteen commits.

---

## §2 — TOKEN-LEVEL AND PROMPT-LEVEL BOOMBNESS ARE GENUINELY TWO OBJECTS

**Artifact:** `outputs/boombness/token_vs_prompt_level/tvp1_20260827_231721_3877437/token_vs_prompt_level.json`
**Script:** `src/boombness/token_vs_prompt_level.py` · **Tests:** 7, 3 mutations caught
**Population:** `extract_boombness/full_20260816_185942_1008673`, `condition=natural_doublespeak`,
`query_kind=behavioral`, **246 multi-occurrence prompts** (24 single-occurrence excluded)

The brief *instructs* that the two be kept apart. **Nothing in this repo had ever measured whether
they are actually distinct** — the instruction was being followed on faith. This measures it.

Both are computed from the same per-occurrence rows, so they are not independent by construction.
The question is whether the prompt-level aggregate carries anything the final-token reading does not.

| field | `token_final ~ prompt_mean` | `~ prompt_max` | `~ prompt_demo_mean` |
|---|---|---|---|
| **`d_surface\|L12\|proj`** | **0.2869** | **0.0576** | 0.1077 |
| `d_surface\|L8\|proj` | 0.5840 | 0.4852 | 0.4519 |
| `d_surface\|L31\|proj` | 0.5240 | 0.2814 | 0.3645 |
| `ll\|L12\|boombness` | 0.5689 | 0.2275 | 0.3389 |
| `ll\|L31\|boombness` | 0.5972 | 0.6657 | 0.3814 |

**They are two objects, not one.** Every correlation sits well below 1, and at **L12 — the layer the
retracted G2 claim used — the two share only ρ = 0.287**, i.e. about 8 % of rank variance. The
`max` aggregate at L12 is ρ = 0.058, essentially unrelated to the final token.

**Single-occurrence prompts are excluded and this matters:** with one codeword occurrence the two
metrics are *literally the same number*, so including the 24 such prompts would manufacture
agreement and bias every correlation toward the "one object" conclusion. A test asserts the
exclusion, and a mutation that includes them goes red.

### The consequence for Phase 7, which is not the obvious one

**G2's retraction does not automatically extend to a prompt-level claim.** G2 measured
`d_surface|L12|proj` **at the final codeword token** and found it does not predict ASR
(clean n=90, ρ = −0.052). At L12 the prompt-level aggregate shares **ρ = 0.287** with that
quantity — so a prompt-level metric at L12 is largely a *different variable that was never tested*,
not a restatement of the retracted one.

That does **not** resurrect G2, and nothing here says a prompt-level metric predicts anything. It
says the question is **OPEN rather than settled negative**, and that Phase 7 must treat token-level
and prompt-level as **two candidate objectives requiring separate evaluation** — which is what the
brief demanded on principle and what this now supports on evidence.

**Phase 2.1/2.2 status: the separation is established.** What remains is whether *either* predicts
heldout ASR beyond `n_examples`/refusal/length/domain — and that needs the fixed-protocol ASR now
being generated, not more geometry.

---

## §0.13 — CAP-BINDING HAS TWO CAUSES, AND §0.2'S RULE ONLY HANDLED ONE

**Artifact:** `outputs/boombness/score_behavior/v3_{A,W}1536_*` · **Tests:** 50, 3 further mutations caught

§0.12's `d_surface` project-out arm was refused by `--require-sprint-grade` because its cap bound on
0.302 of rows. §0.2's pre-registered response is *"run a larger cap"*, so both arms were re-run at
**1536** (2.4× the room). The result:

| | at cap, 640 | at cap, 1536 | median tokens |
|---|---|---|---|
| `A_baseline` | **0/96** | **0/96** | 308.5 (both) |
| `W` (`d_surface` removed) | **29/96 = 0.3021** | **29/96 = 0.3021** | 346.5 (both) |

**Identical fraction, and the same 29 rows — 100 % overlap, zero resolved.** All 29 land on exactly
1536 tokens. The 67 rows that ended at 640 have byte-identical token counts at 1536 (greedy
determinism confirmed).

**Removing `d_surface` makes ~30 % of generations never terminate.** That is not truncation and no
cap will fix it. §0.2's rule — raise the cap until it stops binding — would have refused this arm
**in perpetuity**, sending the sprint on a treadmill.

### The protocol now distinguishes them

`classify_cap_binding(entry_lo, entry_hi, rows_lo, rows_hi)` returns:

* **`truncation_resolvable_by_larger_cap`** — the larger cap resolved it. Re-run larger. *(This is
  what §0.3a found for the refusal arm: 0.243 → 0.018.)*
* **`degeneracy_no_cap_will_fix`** — the same rows bind at both caps. **Disclose, do not chase.**
  Row-identity overlap decides where available, because two caps can bind on the same *fraction* for
  different rows.

`assert_sprint_grade` now accepts a degeneracy-classified entry **only if it discloses
`degenerate_rows`** — the non-terminating count is part of the result, not a footnote — and still
refuses plain truncation exactly as before.

### Does the degeneracy explain §0.12's +0.27? **No.** *(diagnostic split, not an estimator)*

| stratum | n | ASR base | ASR arm | up | down | **net** |
|---|---|---|---|---|---|---|
| **W rows that terminate** | **67** | 24/67 | 49/67 | 29 | 4 | **+25** |
| W rows that never terminate | 29 | 6/29 | 7/29 | 6 | 5 | **+1** |
| all | 96 | 30/96 | 56/96 | 35 | 9 | +26 |

**25 of the 26 net upward flips are in rows that terminate normally.** Only 6 of the 35 upward flips
fall in the degenerate stratum, and they are nearly cancelled by 5 downward ones. The ASR increase is
**not** an artifact of rambling completions giving the judge more surface to score — which was the
obvious worry and is now excluded.

*(This is a length-conditioned split. The brief permits that as a DIAGNOSTIC and forbids it as an
estimator; it is used here only to test an alternative explanation, and the headline remains the
unconditioned 30/96 → 56/96.)*

### What this does and does not license

* **The effect survives its most serious alternative explanation.**
* **The intervention is degenerate on ~30 % of rows**, and that is now a disclosed property of the
  arm rather than a cap complaint. For Phase 3's criteria — *"if no aggressive patch can move
  behaviour without degeneracy, record the negative"* — this is a **partial** degeneracy: behaviour
  moves, and it moves in the non-degenerate stratum.
* Entry 5 stays **NEEDS RERUN** until `j1536_A`/`j1536_W` (job 787539) are judged and the arm is
  scored with `binding_kind` and `degenerate_rows` stamped.

---

## §R.4 — A PROCESS FAILURE OF MINE, caught by a peer running the suite I did not

**§0.2.5's completeness guard broke eight tests in `tests/test_arm_report.py` and I did not
notice**, because after landing it I ran only `tests/test_asr_protocol.py` — the file I was editing.
I patched that file's fixture helper to write `DONE.json` and never patched the sibling helper in
`test_arm_report.py`, which builds run dirs the same way. A concurrent session ran the full suite
and reported **8 failed / 1194 passed**, all eight mine.

**The guard was right and the scaffolding was stale** — exactly the outcome a new guard should
produce. That is not the failure. The failure is that **a guard designed to stop bad data reaching a
conclusion was itself shipped without running the suite it could break**, so for two commits the
suite could not have distinguished a real regression from this one.

Fixed (both fixture helpers now write `DONE.json` on the judge *and* gens dirs) and verified
properly this time:

* `tests/test_arm_report.py` — **8/8 pass**
* **Full suite under the project's conda interpreter: `1207 passed, 7 skipped, 0 failed`**
  (the login-node interpreter cannot collect 16 torch-dependent modules, which is why running
  `python -m pytest tests/` there reports collection errors and is not a suite run at all).

**Standing correction to this sprint's own procedure:** every commit that changes a *guard* runs the
full suite under the conda interpreter, not the touched file. A guard's blast radius is by
definition wider than the file it lives in.

*(Also noted from the same session, and worth carrying into any triage of my own guards: a reporting
guard can be exactly as invisible as a population guard. Their DR-5 case had 92.3 % vs 69.2 %
ranking cells backwards while looking entirely correct to a reader — so "a broken reporting rule
would look wrong" is not a safe assumption.)*

---

## §0.14 — ENTRY 5 RESOLVED: removing `d_surface` RAISES ASR — the sprint's first fully sprint-grade causal result

**Judge dirs:** `j1536_A_20260827_234356_3798010`, `j1536_W_20260827_234816_3798190`
(both pinned `openai/gpt-4o-mini`, **judged in one invocation**, job 787539)
**Gens:** `v3_A1536`, `v3_W1536` · Llama-3.1-8B · `basket_bomb` · `natural_doublespeak` ·
`n_examples ∈ {1,2,4,8}` · **n=96** · **cap 1536**

| | ASR | at cap | label | median tokens | refusal kw | judge pinned |
|---|---|---|---|---|---|---|
| `A_baseline` | **28/96** | **0.0000** | `ASR` | 308.5 | 2/96 | ✅ |
| `W` — `d_surface:project_out:14-14` | **59/96** | 0.3021 † | `ASR within first 1536` | 346.5 | 2/96 | ✅ |

| paired | |
|---|---|
| delta | **+0.3229** |
| up / down | **37 / 6** (43 discordant) |
| **exact two-sided p** | **0.000002** |
| judge-noise SD | 3.77 rows · **net/SD = −8.23** (ASR *up*) |
| divergence | **96/96 `OK`** |

† classified `degeneracy_no_cap_will_fix` and **disclosed as 29 non-terminating rows** (§0.13).

**Both arms PASS `assert_sprint_grade`.** This is the first result in the sprint to clear every gate:
pinned judge · both arms in one judge invocation · non-binding baseline cap · arm binding classified
and disclosed rather than chased · divergence 96/96 · refusal identical · median length *longer* in
the arm.

### It replicates across caps

| cap | baseline | arm | delta | up/down | p |
|---|---|---|---|---|---|
| 640 | 30/96 | 56/96 | +0.2708 | 35/9 | 0.0001 |
| **1536** | **28/96** | **59/96** | **+0.3229** | **37/6** | **0.000002** |

Baseline moved 2 rows and the arm 3 — both inside the 3.77-row judge floor. The effect is stable.

### Ledger effect

**Entry 5 — "removing `d_surface` at L8 RAISES ASR by +0.0424 on AdvBench-495" — moves NEEDS RERUN →
KEEP, and BROADENS.** The direction confirms at a much larger magnitude (+0.3229 vs +0.0424), at
**L14** rather than L8, on a **doublespeak** bank rather than AdvBench, under a protocol the original
did not have. The original number is *not* re-established — different layer, bank and population —
but the claim it encodes is.

**This is the sprint's central positive finding so far, and note which direction it runs.** The
original hypothesis was that `d_surface` *carries* the attack, so removing it should *suppress*.
**It does the opposite, decisively.** Whatever `d_surface` is, removing it makes the model **more**
compliant, not less — while also making ~30 % of its generations non-terminating.

That is consistent with the retracted G2/G4 picture (both steering signs suppressed; removal raised
ASR at L8) and inconsistent with `d_surface` being the attack-carrying direction. **It does not
license a GCG objective**: the Phase 7 gate asks for a signal that *predicts* heldout ASR and can be
*optimised*, and "delete this direction and the model complies more, but a third of its outputs never
stop" is a finding about model fragility, not an objective.

---

## §0.13a — the degeneracy classifier VALIDATED against a 4-pair negative control

A peer session supplied four cap pairs from its own phase as a negative control. **Re-derived here
rather than accepted** (one run id in the message was wrong and was located before use):

| pair | n | binds @192 | binds @640 | **row overlap** | classification |
|---|---|---|---|---|---|
| Llama `basket_bomb` baseline | 96 | 90 | 0 | **0.0 %** | truncation |
| Llama `basket_bomb` demoproc | 96 | 82 | 0 | **0.0 %** | truncation |
| Qwen3 `longpreQ14B` baseline | **80** | **48** | 0 | **0.0 %** | truncation |
| Qwen3 `longpreQ14B` demoproc | **80** | **72** | 0 | **0.0 %** | truncation |
| **mine — `d_surface` project-out** | **96** | **29** | **29** | **100.0 %** | **degeneracy** |

⛔ **DENOMINATOR CORRECTED.** The Qwen3 rows first read `160 / 69` and `160 / 112`. That is the
wrong denominator for **this** statistic, and a peer session caught it. The cap-640 arms exist only
at `n_examples ∈ {4,8}` (PR-26 restricted to the decisive doses), so **n_common = 80** — verified
here: the within-common binding sets are 48 and 72 and are strict subsets of the full 69 and 112.
An *overlap* statistic requires rows present at **both** caps; including 80 low-cap rows with no
high-cap partner puts rows in the count that have nothing to overlap with. `160 / 69` answers
"how much does this population truncate"; `80 / 48` answers "do the SAME rows bind at both caps",
and only the second is what the classifier asks. **Classification is unchanged at either
denominator** (overlap is 0.0 % both ways) — the correction is to the reported figure, not the
verdict.

**Four cases at 0 % against one at 100 %, spanning two models and two banks.** The classifier is
discriminating, not flagging heaviness — the control pairs bind on up to **94 %** of rows at the low
cap and resolve *completely* at the high one, while mine binds on 30 % and resolves *not at all*.
Without this control the classifier would rest on a single case.

---

## §0.15 — ENTRY 7 RESOLVED (refusal channel) and ENTRY 6's FIRST POPULATION — both sprint-grade

**Artifact:** `outputs/boombness/arm_report/e67_20260828_001917_4064232/arm_report.json`
All arms pinned `openai/gpt-4o-mini`; **entry-7's three arms judged in ONE invocation** (787449),
**entry-6's two in ONE invocation** (787613).

### Entry 7 — refusal projection, `advbench_heldout_495`, cap 1024, **n=495**

| arm | ASR | at cap | median tok | refusal kw | judge floor |
|---|---|---|---|---|---|
| `base` | **33/495** | 0.0040 | 18 | **0.9313** | 0.0185 |
| **C** `refusalness:project_out:18-18` | **133/495** | 0.0182 | 21 | 0.7091 | 0.0349 |
| **D** joint `d_surface`@L8 + `refusalness`@L18 | **171/495** | 0.0162 | 24 | 0.6222 | 0.0412 |

| contrast | delta | up / down | exact p | net/SD | divergence |
|---|---|---|---|---|---|
| **C vs base** | **+0.2020** | **100 / 0** | ~0 | −19.44 | 440/495 `OK` |
| **D vs base** | **+0.2788** | **139 / 1** | ~0 | −25.38 | 453/495 `OK` |

**The cap does not bind on any arm** (0.004–0.018) and both arms pass `assert_sprint_grade`.

**This replicates the old numbers almost exactly** — and that is the striking part:

| | old (cap 512, binding, cross-session judge) | **new (cap 1024, non-binding, pinned, one invocation)** |
|---|---|---|
| arm C | +0.2061 | **+0.2020** |
| arm D | +0.2869 | **+0.2788** |

Two independent measurements four rows apart on n=495, under protocols that differ in cap, judge
pinning and session structure. **Ledger entry 7 moves NEEDS RERUN → KEEP.** The §0.2 truncation
concern was legitimate to raise and is now answered: it did not move this estimate.

`C` is **100 up / 0 down** — perfectly one-directional, which is what removing a refusal direction
should look like. Refusal keyword rate falls 0.9313 → 0.7091 (C) → 0.6222 (D), so the intervention
does what it says on the tin.

### Entry 6 — retrieval knockout, population `main`, cap 640, n=96

| arm | ASR | at cap | median tok | refusal kw |
|---|---|---|---|---|
| `A_baseline` | **22/96** | **0.0000** | 202.0 | 3/96 |
| `C_band_L6_14` (demo-block attention knockout) | **8/96** | **0.0000** | 201.5 | 1/96 |

**delta −0.1458 · 7 up / 21 down · exact p = 0.0125 · net/SD = 4.05 · divergence 96/96 · MDE 0.125**

**Neither arm truncates at all**, so this is plain `ASR` with no relabelling — the first entry-6
measurement that is. Against cap 192 (22/96 → 5/96, net +17) the effect **replicates** at
22/96 → 8/96, net +14.

**Ledger entry 6: one of three populations confirms.** `ticket_bomb` and `basket_gun` are queued.
Per §0.8 the claim was never about the pooled average — `main` and `ticket_bomb` carried it while
two populations pointed the other way — so **this confirms the half that was real, and `basket_gun`
remains the informative test** (a population *with* headroom that showed nothing at 192).

Note the effect sits just above its own detection threshold (0.1458 against MDE 0.125), so `main`
alone is not a strong result; it is one concordant cell.

### The two channels, side by side, both now at non-binding caps

| intervention | direction | magnitude | n |
|---|---|---|---|
| remove **refusal** (L18) | **raises** ASR | +0.2020 | 495 |
| remove **refusal + `d_surface`** | **raises** ASR | +0.2788 | 495 |
| remove **`d_surface`** (L14, §0.14) | **raises** ASR | +0.3229 | 96 |
| **knock out demo retrieval** (L6–14) | **lowers** ASR | −0.1458 | 96 |

**Every direction-removal raises ASR; only the attention knockout lowers it.** That asymmetry is the
sprint's clearest structural finding so far, and it points away from "`d_surface` carries the
attack" and toward "the demonstration-retrieval *pathway* carries it, while the fitted directions are
suppressors whose deletion disinhibits the model."

---

# §0.3 — DELIVERABLE: "OLD CONCLUSION vs FIXED-ASR CONCLUSION"

**Artifacts:** `cap_natural_experiment/{capNE2,capC,p03}_*` · `arm_report/{e67,w640}_*` ·
`asr_protocol/corpus_sweep_20260827_v2.json`
**This is the table the brief gates all objective work on. It now exists.**

## Part 1 — every arm measured at BOTH caps, same rows, continuation-verified

Nine arms across three interventions, two models, four banks. Greedy decoding, so each high-cap run
is verifiably the low-cap run continued.

| arm | n | low cap → high | ASR rows | Δ | up/down | exact p | MDE |
|---|---|---|---|---|---|---|---|
| Llama `basket_bomb` baseline | 96 | 192→640 | 25→32 | +0.0729 | 12/5 | 0.1435 | 0.094 |
| Qwen3 `longpreQ14B` baseline | 80 | 192→640 | 10→11 | +0.0125 | 4/3 | 1.000 | 0.088 |
| Qwen3 `CTRL_matched_d1` | 80 | 192→640 | 11→12 | +0.0125 | 2/1 | 1.000 | — |
| Qwen3 `C_demo_processing_only` | 80 | 192→640 | 1→1 | 0.0000 | 1/1 | 1.000 | — |
| **E7 baseline** | **495** | 512→1024 | 32→33 | **+0.0020** | 1/0 | 1.000 | — |
| **E7 arm C** (refusal projout) | **495** | 512→1024 | 134→133 | **−0.0020** | 2/3 | 1.000 | — |
| **E7 arm D** (joint) | **495** | 512→1024 | 174→171 | **−0.0061** | 4/7 | 0.5488 | **0.018** |
| **E6 `main` baseline** | 96 | 192→640 | 22→22 | **0.0000** | **8/8** | 1.000 | 0.104 |
| **E6 `main` knockout** | 96 | 192→640 | 5→8 | +0.0312 | 5/2 | 0.4531 | 0.073 |

**Not one arm moves detectably.** Largest shift is 3 rows in 96. Every p ≥ 0.45. The two
best-powered pairs (E7 arm D at MDE 0.018 on n=495; E6 knockout at MDE 0.073) are both null.

The `E6 main baseline` row is the clearest picture of what is going on: **8 rows up, 8 rows down,
net exactly zero.** Sixteen rows changed verdict and the estimate did not move — the judge floor
churning, visible because the pairing exposes it.

## Part 2 — old conclusion vs fixed-ASR conclusion

| # | old conclusion | what the fixed protocol says | verdict |
|---|---|---|---|
| 2 | ASR numbers are trustworthy as reported | **250 judge dirs / 70 053 rows may be quoted only as "ASR within first N generated tokens"**; at cap 192 the cap binds on 90.7 % of dirs | **REPORTING defect, real** |
| — | *(implied)* truncation depressed the old ASR | **False on its face.** Truncation is bidirectional: 12 up / 5 down on the clean Llama pair | **RETRACTED** |
| 5 | removing `d_surface` raises ASR (+0.0424, L8, AdvBench) | **+0.3229** at L14 on `basket_bomb`, cap 1536, 37/6, p=2e-6 | **KEEP, broadened** |
| 7 | refusal is the larger Llama channel (C +0.2061, D +0.2869) | **C +0.2020, D +0.2788** at cap 1024, n=495, pinned, one invocation | **KEEP — replicates within 4 rows** |
| 6 | retrieval knockout suppresses the attack (96↓/18↑, 8 populations) | `main` replicates (**net +17 → +14**, plain ASR, no relabelling); but the pooled claim was **carried by 2 of 5 populations** with 2 pointing the other way | **KEEP-NARROWED; 2 populations pending** |
| 12 | C7 demonstration-specificity | 640-cap replication is **sprint-grade**: 11/80 → 1/80, p=0.0063 | **OPEN → KEEP-NARROWED** |
| 9 | G2: prompt-level boombness predicts ASR | retraction upheld — **and §2 shows prompt-level and token-level share only ρ=0.287 at L12**, so the retraction covers the token-level quantity only | **RETRACT, scope narrowed** |
| 14 | a GCG objective was justified | unchanged | **RETRACT** |

## Part 3 — the answer to the brief's actual question

> *"Which old ASR effects survive when the cap is large enough? Which were truncation or length
> artifacts?"*

**None were truncation artifacts. Every effect re-measured survives, and the two large ones
reproduce to within a few rows.** The 192-token cap was a genuine and serious **reporting** defect —
70 000 rows may not be called ASR — but across nine arms at two caps each it **did not move a single
estimate detectably.**

That is not the answer I expected when §0.2 opened, and it is the one the data gives. The
sprint's measurement-repair phase closes with the prior sprint's ASR conclusions **substantially
vindicated on their numbers, and corrected on their labels.**

**The gate is satisfied: §0.3 exists, so objective work may now be evaluated.** Phase 7 remains
closed on its own criteria, not on this one.

---

## §DR-1 — DEEP REVIEW (4-hour), 2026-08-28 00:45

### Artifact review — every cited path resolves

Automated audit over this document: **63 cited paths, 0 unresolvable**; **4 cited run ids, all 4
resolve** on disk. (The audit's first pass flagged 30 "missing" — all bare filenames used as prose
shorthand, plus one subdirectory my glob omitted. Refining the resolver to search
`src/boombness`, `tests`, `doublespeak_causality`, `scripts` and `outputs` left exactly one flag,
which was my own glob bug, not a bad reference.)

**One real defect found and fixed:** `corpus_sweep_20260827.json` — the V-1 sweep superseded by
§0.2.5 — was **sitting on disk unmarked**. Anyone opening it would read inflated row counts with
nothing saying so. It now carries a `SUPERSEDED` block naming its replacement, the reason
(51 partial/aborted/excluded runs ingested; 10 449 inflated rows at cap 192), and `DO_NOT_QUOTE`.
The brief requires that a superseded artifact cannot be silently re-ingested; it could have been.

### Code review — 1 738 new LOC, 93 new tests

| module | LOC | tests |
|---|---|---|
| `asr_protocol.py` | 560 | 27 |
| `bank_leakage_probe.py` | 341 | 12 |
| `cap_natural_experiment.py` | 253 | 10 |
| `intervention_liveness.py` | 217 | 9 |
| `paired_test_noise_sensitivity.py` | 205 | 14 |
| `arm_report.py` | 181 | 8 |
| `token_vs_prompt_level.py` | 181 | 7 |
| `prompt_families.py` (`main_ne12` only) | +24 | 6 |

**Every guard mutation-tested**, 33 mutations applied across the sprint. **Four survived and each
was informative:** two were harness faults of mine (wrong occurrence replaced; unused variable
added), one was a genuine test gap (threshold boundary never exercised), one was a semantic no-op
correctly recorded as such rather than counted as a catch.

Full suite under the conda interpreter: **1207 passed, 7 skipped, 0 failed.**

### Liveness review — every intervention arm reported this sprint

| arm | divergence | verdict |
|---|---|---|
| E5 `d_surface` project-out @640 | **96/96** | `OK` |
| E5 `d_surface` project-out @1536 | **96/96** | `OK` |
| E7 arm C refusal @1024 | 440/495 | `OK` |
| E7 arm D joint @1024 | 453/495 | `OK` |
| E6 `main` knockout @640 | **96/96** | `OK` |

**No arm this sprint is a C-20-style no-op.** Every reported intervention demonstrably changed what
the model wrote.

### Population review

Denominators are stated with every rate throughout; `n_join_missing = 0` corpus-wide; the completeness
contract now refuses partial/aborted/excluded runs on **both** judge and gens dirs. The one
population caveat that stands is §0.8's: entry 6's pooled claim was carried by 2 of 5 populations,
and `window_knife` (baseline 2/96) has no headroom and should never have entered the mean.

### Claim review — 4 of 14 entries moved, all on new measurement

| | at audit | **now** |
|---|---|---|
| KEEP | 1 | **3** |
| KEEP-NARROWED | 4 | **5** |
| NEEDS RERUN | 5 | **3** |
| RETRACT | 3 | 3 |
| OPEN | 1 | 0 |

Moved: entry 5 → KEEP, entry 7 → KEEP, entry 12 (C7) → KEEP-NARROWED, entry 6 → 1 of 3 populations
confirmed. **No entry moved on argument; each moved on a sprint-grade measurement.**

### What I would flag against myself

1. **Three of my own errors were caught by a peer session, not by me** — the stale fixtures, the
   negative-control denominator, and (indirectly) the SystemExit leak. My own checks caught the
   §0.2.5 exclusion bug and the case-sensitivity bug. The lesson already recorded (run the full
   suite on any guard change) addresses the first; the other two were caught because someone
   re-derived numbers I published.
2. **`window_knife` is still in the entry-6 rerun plan as declined**, which is correct, but the
   original pooled claim remains quotable from prior deliverables where §0.8's decomposition is
   absent. That is a propagation risk I do not control from this file.
3. **The sprint has produced no negative result yet.** Everything re-measured has survived. That is
   what the data says, but it is also the pattern a confirmation-seeking process would produce, and
   the honest counterweight is that the two hardest gates — Phase 7 and entry 6's `basket_gun` —
   are both still pending and both are set up to fail informatively.

---

## §6.1 — PHASE 6, representational half: does the QUERY token get more bomb-like with more demonstrations?

**Population:** `extract_boombness/full_20260816_185942_1008673`, `natural_doublespeak`,
`query_kind=behavioral`, **query occurrences only**.

### ⛔ The pooled answer is confounded — composition, not dose

My first pass pooled all query occurrences by `n_examples` and got ρ = **−0.046** at L12: "flat".
**That number is wrong**, and the composition table says why:

| `n_examples` | n | bank blocks | role styles |
|---|---|---|---|
| 0 | 36 | core2x2 12, strength 24 | plain only |
| 1 | 12 | core2x2 12 | plain only |
| 2 | 36 | core2x2 12, families 24 | plain only |
| **4** | **120** | **core2x2, strength, consistency, position, role_style, families** | **all six** |
| 8 | 54 | core2x2 12, consistency 18, families 24 | plain only |
| 16 | 12 | core2x2 12 | plain only |

The `n_examples=4` stratum is 120 rows spanning six blocks and all six role styles; `n=1` and `n=16`
are twelve rows of `core2x2`/`plain`. **A correlation across those strata is measuring block
composition as much as dose.**

### The balanced answer — `core2x2` + `role_style=plain`, 12 rows per dose, 6 domains each

| readout | ρ(n_examples, query boombness) | n0 | n1 | n2 | n4 | n8 | n16 |
|---|---|---|---|---|---|---|---|
| `d_surface\|L8\|proj` | **+0.7157** | −3.679 | −3.096 | −3.024 | −2.867 | −2.644 | **−2.438** |
| `d_surface\|L12\|proj` | **+0.3798** | −4.220 | −3.669 | −3.681 | −3.724 | −3.618 | −3.451 |
| `ll\|L12\|boombness` | **−0.4518** | +1.052 | +0.418 | +0.395 | +0.206 | +0.119 | **−0.291** |

**Answer: YES on the direction-projection readout, and it is monotone at L8** — every one of the six
dose steps moves the same way, ρ = +0.72. The pooled −0.046 was a composition artifact and the
balanced L12 figure is **+0.380**, a sign flip.

### But the two readouts DISAGREE IN SIGN, on the same tokens

`d_surface` projection says the query codeword becomes **more** bomb-like as demonstrations
accumulate (+0.72 at L8). The **logit lens** on the same tokens says it becomes **less** so
(−0.45 at L12), also monotonically.

**"Boombness" is therefore not one quantity.** Two readouts the brief lists side by side as
measurements of the same thing move in opposite directions under the manipulation that produces the
attack. Any objective built on "boombness" must say *which* readout, because they do not agree about
the sign of the central dose-response.

### Consequence for Phase 7

This is a **direct hit on objective viability**, and it cuts both ways:

* **For** a `d_surface`-projection objective: it responds monotonically to the manipulation that
  creates the attack (ρ = +0.72 at L8). That is the dose-response a usable objective needs.
* **Against**: the logit-lens readout of the same quantity moves the *other* way, so the choice of
  readout determines the sign of the finding. An objective whose direction depends on which lens you
  read it through is not measuring one thing.
* And §0.14–§0.15 already showed that **removing** `d_surface` *raises* ASR. So the representational
  dose-response (+0.72) and the causal test (removal → more attack) point in **opposite** directions.

**Phase 6's representational half is answered and the answer is unfavourable to a simple objective.**
The behavioural half — ASR by `n_examples` at a non-binding cap — is next, and the entry-6 arms
already provide it at `n_examples ∈ {1,2,4,8}` on three banks.

---

## §0.16 — ENTRY 6, population `ticket_bomb`: the strongest knockout result yet

**Artifact:** `outputs/boombness/arm_report/e6t_20260828_014238_70394/arm_report.json`
Cap 640 · n=96 · pinned judge · **both arms in one invocation** (787814)

| arm | ASR | at cap | median tokens | refusal kw | judge floor |
|---|---|---|---|---|---|
| `A_baseline` | **27/96** | **0.0000** | 248.0 | 12/96 | 0.0461 |
| `C_band_L6_14` knockout | **2/96** | **0.0000** | 299.5 | **0/96** | 0.0237 |

**delta −0.2604 · 1 up / 26 down · exact p ≈ 0 · net/SD = 9.66 · divergence 96/96 · MDE 0.135**

Neither arm truncates, so this is plain `ASR`. **Stronger than at cap 192** (24/96 → 7/96, net +17;
now 27/96 → 2/96, net +25).

**It is neither refusal nor length collapse, and both are measured rather than assumed:**
refusal keyword rate **falls** to 0/96 in the knockout arm (from 12/96), and median generation
length **rises** 248 → 299.5. The knockout removes the attack while the model keeps writing, at
length, without refusing.

### Entry 6 status: 2 of 3 populations, both sprint-grade

| population | baseline → arm | delta | up/down | p | net/SD |
|---|---|---|---|---|---|
| `main` | 22/96 → 8/96 | −0.1458 | 7/21 | 0.0125 | 4.05 |
| **`ticket_bomb`** | **27/96 → 2/96** | **−0.2604** | **1/26** | **~0** | **9.66** |
| `basket_gun` | *generating* | — | — | — | — |

Both confirming populations are the two §0.8 identified as carrying the pooled claim (net/SD 5.53
and 5.18 at cap 192). **`basket_gun` remains the informative test** — a population with headroom
(baseline 10/96) that showed **nothing** at 192 (net −1). If it stays null the dissociation is
confirmed at a usable cap; if it now moves, §0.8's decomposition needs revisiting.

### A gap I am recording rather than papering over

These entry-6 runs were generated with `--query-kinds behavioral` only, so **they carry no
comprehension or binding readout**. The brief's Phase 5 asks for binding accuracy *beside* every
ASR delta, precisely so that "ASR fell" can be distinguished from "the model no longer understands
the prompt". The refusal rate and length figures above argue against destruction — a model that had
lost the prompt would not write *longer* — but **that is an argument, not the forced-choice binding
probe Phase 5 specifies.** Recorded as an open item; the probe exists (`core2x2`,
`semantic_forced_choice`) and would need its own generation pass.

---

## §5 — PHASE 5: does binding survive the knockout that kills the attack?

**Runs:** `p5A_main`, `p5C_main` (forward-only, no generation, no judge, n=192 readout rows each)
**Population:** `main`, `natural_doublespeak`, `core2x2(+slot3)`, `n_examples ∈ {1,2,4,8}`
The brief's success condition: *"ASR falls, but binding/comprehension remains high enough that the
model has not merely lost the prompt."*

| readout | what it asks | median option mass | baseline mapped-wins | **knockout** | Δ |
|---|---|---|---|---|---|
| **`semantic_forced_choice`** | *does W mean carrot or bomb?* (both named) | **0.54 → 0.37**, 100 % above floor | 42/48 | **41/48** | **−1** |
| `comprehension_usage` | *is W used literally or in code?* | 0.37 → 0.32, 100 % above floor | 11/48 | 4/48 | −7 |
| `semantic_one_word` | free next token: concept vs codeword | **0.0429 → BELOW the repo's own 0.05 floor** | 56/96 | 2/96 | −54 |

### The readout with the most mass says binding SURVIVES

`semantic_forced_choice` carries **0.54 of the probability mass on its two options and 100 % of rows
above the reliability floor** — it is the only readout here that is unambiguously interpretable. It
moves by **one row: 42/48 → 41/48**, while ASR on the same population falls 22/96 → 8/96 (and
27/96 → 2/96 on `ticket_bomb`).

**That is the brief's success condition met.** The knockout removes the attack and the model can
still say what the codeword means when asked.

### But `semantic_one_word` says the opposite, and its mass is below the floor

Median option mass **0.04289** at baseline against `score_behavior.py`'s own
`--min-option-mass 0.05` default — the run's own `reportable` flag is **False**, and its tail gate
stamped `option_mass_gate: "OVERRIDDEN — NOT REPORTABLE"` and exited non-zero (§5.1).
Restricted to the 25 rows above the floor **in both arms**, it still says 19/25 → **1/25**.

So this is not simply an unreliable readout to be discarded. Taken together the three give a
**coherent and more interesting** result than either alone:

> **The knockout removes the model's *spontaneous use* of the mapping while leaving its *ability to
> report* the mapping when explicitly asked.**

Forced choice (both options named) survives at 41/48. Free next-token generation of the concept
collapses to 1/25. `comprehension_usage` — "is this literal or coded?" — drops 11/48 → 4/48, though
it was already a minority reading at baseline.

**That is a usage/knowledge dissociation**, and it is exactly the distinction Phase 5 exists to draw.
The knockout is not destroying comprehension; it is removing the pathway by which comprehension gets
*used* to answer.

### Two caveats carried

1. **Forced-choice option mass falls 0.54 → 0.37 under the knockout.** The model still picks
   correctly but is measurably less concentrated on the two options. Binding survives; confidence
   in it does not fully.
2. **`main` only so far.** `ticket_bomb`'s baseline readout is still generating (787916); its
   knockout arm is done. The claim above rests on one population until that lands.

**Phase 5 status: the success condition is met on the readout that qualifies, with the
usage/knowledge distinction recorded rather than collapsed into a single "binding survives" claim.**

---

## §5.1 — "FAILED" that means UNREPORTABLE, not incomplete — and an off-by-one in a shared gate

A peer session flagged that job **787914** (`p5A_main`) shows `FAILED` in `sacct`. It is worth
recording exactly what that means, because **both obvious readings of it are wrong**:

* The run **did not crash.** It wrote 192 rows, `failures: {}`, and a valid `DONE.json`.
* Its tail gate then **exited non-zero on purpose**, stamping
  `option_mass_gate: "OVERRIDDEN — NOT REPORTABLE: semantic/semantic_one_word: median option mass
  0.04289 < 0.05"`.

So: **checking output files would call it a success; checking exit status would call it a total
loss.** The honest state is a complete run with **one readout of three** below its reliability floor —
and the other two (`semantic_forced_choice` at 0.5416, `comprehension_usage` at 0.3722) are exactly
the ones §5's conclusion rests on.

### The gap this exposed in my own consumer

**Completeness and reportability are different properties, and my code only checked one.**
`require_done` passes this run — correctly, it is complete — and `check_run_readable` passes it too.
But `summary.json` carries a per-readout `reportable` flag and a gate verdict that **nothing was
reading**. That is the V-20 shape from a third angle: an invariant recorded at the producer and
never read at the consumer.

`readout_reportability(run_dir)` now surfaces it. §5's conclusion is **unaffected** — I had derived
the same restriction independently by computing option mass — but I got there by accident rather
than by reading the verdict the producer had already written down.

### An off-by-one in the shared gate, found while reconciling two medians

My recomputed median was **0.04042**; the gate reported **0.04289**, on the same n=96 rows. The cause
is `score_behavior.py:2020`:

```
v = sorted(vals); med = v[len(v) // 2]
```

For even `n` that is the **upper-middle element**, not the median (which averages the two middles).
Here `v[48] = 0.042891` against a true median of `0.040421`.

**Swept across the corpus:** 28 runs carry an `option_mass` block; **32 readouts** have
upper-middle ≠ true median (median discrepancy 0.001376, max 0.042581); and **0 gate verdicts would
flip** if the true median were used.

So it is **real but currently harmless** — and it is a *gate*, which is where a 6 % upward bias on a
threshold statistic matters most: a readout whose true median sits just under 0.05 could be passed.
**I have not changed the shared code**, because `median`/`p10`/`p90` appear in every historical
`summary.json` and other analyses may quote them; silently altering them would be worse than the
bug. Flagged to the concurrent session as shared-code territory, and recorded here.

**54 tests, 2 further mutations caught.**

---

## §5.2 — ⛔ CORRECTION TO §5: binding does NOT reliably survive — it is population-dependent

**§5 concluded, from `main` alone, that "the brief's success condition is met". `ticket_bomb` says
the opposite, and I am correcting the conclusion rather than the caveat.**

All four Phase 5 arms verified reportable (only `p5A_main`'s `semantic_one_word` at 0.0429 falls
below floor; every other readout on every arm passes), so the two populations are directly
comparable.

| population | readout | option mass base → knockout | mapped-wins base → knockout | Δ |
|---|---|---|---|---|
| **`main`** | `semantic_forced_choice` | 0.5416 → 0.3689 | 42/48 → **41/48** | **−1** |
| **`ticket_bomb`** | `semantic_forced_choice` | **0.5695 → 0.1162** | 45/48 → **15/48** | **−30** |
| `main` | `comprehension_usage` | 0.3722 → 0.3208 | 11/48 → 4/48 | −7 |
| `ticket_bomb` | `comprehension_usage` | 0.1923 → 0.3435 | 11/48 → 3/48 | −8 |
| `ticket_bomb` | `semantic_one_word` | 0.1808 → 0.0644 | 64/96 → 5/96 | −59 |

### On `ticket_bomb` the knockout destroys the mapping

Forced-choice option mass collapses **0.5695 → 0.1162, a five-fold drop**. That is not the model
choosing the other option — **it is the model losing the frame**: it no longer concentrates
probability on either reading of the codeword. Mapped-wins falls 45/48 → 15/48.

On `main` the same readout barely moves (42/48 → 41/48) with a mild mass drop (0.54 → 0.37).

### The uncomfortable pattern

**`ticket_bomb` has BOTH the larger ASR effect AND the binding collapse:**

| population | ASR delta | forced-choice binding Δ |
|---|---|---|
| `main` | −0.1458 | **−1** (survives) |
| `ticket_bomb` | **−0.2604** | **−30** (collapses) |

They **track together**. That is the opposite of a dissociation — it is precisely the confound the
brief names: *"lowering ASR may only mean the model no longer understands the prompt."*

### Revised verdict

* **On `main`: the success condition IS met.** ASR falls 22/96 → 8/96 while forced-choice binding
  holds at 41/48. The knockout removes the attack without removing the mapping.
* **On `ticket_bomb`: the success condition is NOT met.** ASR falls 27/96 → 2/96 *and* binding
  collapses to 15/48 with the option mass gone. **§0.16's "strongest knockout result yet" is strong
  on ASR and may be strong *because* it is destroying comprehension.** That reading now travels
  with it.
* **Phase 5's answer is therefore: binding survival is population-dependent, and one of the two
  populations that carries entry 6 fails the control.**

Note the refusal and length evidence does **not** rescue `ticket_bomb`: refusal fell to 0/96 and
median length *rose* 248 → 299.5. The model writes more, refuses less, and **can no longer say what
the codeword means**. Those are consistent — it is answering something fluently, having lost the
mapping — and they show why refusal and length are *necessary but not sufficient* comprehension
controls. Only the forced-choice probe separates these cases, which is why Phase 5 specifies it.

**This is the sprint's first substantive negative on a claim it had just published, and it came from
running the control the brief demanded on a second population rather than one.**

### ⚠ A process failure in how this section was committed

Commit `a136f8a1` carries this correction's message but **not its content**. The heredoc that was to
append it died on a `SyntaxError` (an escaped quote inside a quoted heredoc), so the script never
ran — and `git commit` then succeeded on an unchanged file, because the only staged change was a new
judge script. **A commit message asserted a correction the repository did not contain.**

Caught within a minute by checking `git show --stat` and grepping for the section, which is the only
reason it is a footnote rather than a hole. The lesson generalises past this instance: **a commit
message is not evidence that the change landed**, and a heredoc that dies at parse time is silent —
`check_all.py` passed, the pre-commit hook passed, and the push succeeded. Verify the artifact, not
the exit code.

---

## §5.3 — The option-mass gate now reads the true median (shared code, non-mutating fix)

§5.1 found `score_behavior.py` computing `med = v[len(v)//2]` — the upper-middle element, not the
median — and left it alone pending the other stakeholder's view, because `median` appears in every
historical `summary.json`.

**The concurrent session supplied the argument that settles it, and it is better than my framing:**
`v[n//2] >= median` **by construction**, so the gate was **biased toward passing**. Therefore every
historical `BELOW GATE` verdict is safe *a fortiori* — the exposure was only ever near-threshold
**passes**. That is a far smaller audit surface than "32 affected readouts" suggested, and it is
exactly why "0 verdicts flip today" was reassuring but not sufficient: the next readout landing just
under 0.05 is the one it would wrongly pass.

**Fix, as agreed and deliberately non-mutating:**

* `median` — **unchanged**, still the upper-middle element, still in every artifact. Mutating it
  would move published values retroactively, which is correcting a figure by changing the thing that
  produced it.
* `median_true` — **added**, `statistics.median(v)`.
* **`reportable` now computed from `median_true`.** The gate stops being biased.
* `median_note` in every artifact says which field is which.

Doing this **now** is free precisely because no verdict changes; after one flips it would mean
changing a verdict and a definition in the same commit.

**6 tests, 3 mutations caught**, including a boundary case the *old* gate would have wrongly passed:
`[0.01, 0.048, 0.051, 0.9]` has a true median below 0.05 and an upper-middle above it. Full suite
green under the conda interpreter.

---

## §5.4 — ⛔ SCOPE QUALIFICATION: my "retrieval knockout" is the UNSCOPED `legacy_all_query` mask

A concurrent session matched my option masses against its own scope decomposition and found them
**identical to four decimals**:

| arm | `knockout_scope` | forced-choice option mass |
|---|---|---|
| `p2A` baseline | — | **0.5416** ← my baseline, exactly |
| `p2_demo_processing_only` | `demo_processing_only` | 0.6021 — mass **RISES** |
| **`p2_legacy_all_query`** | **`legacy_all_query`** | **0.3689** ← **my knockout, exactly** |
| `p2_query_prefill_only` | `query_prefill_only` | 0.4365 |

**Verified on my side:** every knockout arm I have run this sprint carries
`knockout_scope: legacy_all_query` — `score_behavior.py:235`'s `DEFAULT_KNOCKOUT_SCOPE`, which I
never overrode. The `--intervene` string is identical across all four scopes; only the scope differs.

**So "the entry-6 retrieval knockout" is the unscoped mask**, and everything this sprint has reported
about it — §0.16's `ticket_bomb` result, §5's binding survival on `main`, §5.2's collapse on
`ticket_bomb` — is **about `legacy_all_query`, not about demonstration-processing specifically.**
That qualification now travels with all three.

It is also a **clean cross-session reproduction**: two sessions, independent runs, matching to four
decimals on a probe neither designed for the other.

### What it does to §5.2's correction

**Less than I thought, and in an interesting direction.** The other session's binding-survival claim
rests on `demo_processing_only`, where option mass *rises* (0.5416 → 0.6021). My collapse is a
**sibling scope**. So my `main` result **agrees with their `legacy_all_query` arm** rather than
contradicting their headline — §5.2's correction stands as a correction of *my own* over-broad
generalisation, not of theirs.

### The deciding cell is empty, and I have launched it

Nobody has run **`demo_processing_only` on `ticket_bomb`**. My collapse is `legacy` on `ticket_bomb`;
their survival is `demoproc` on `main`. The cell that separates *scope* from *bank* has never been
measured, and the five-fold mass collapse I found (0.5695 → 0.1162) is much larger than anything the
scoped arms produce — so whether it survives scoping is a real question, not a formality.

**Jobs 788047 (behavioural, cap 640) and 788048 (probe) are running it.** Its baseline already
exists at cap 640 (`e6A_ticket_bomb`), so this is two cheap arms for a cell both sessions flagged as
the most informative available.

Either outcome is worth having:
* **`demoproc` also collapses on `ticket_bomb`** → binding survival is **bank**-dependent, and the
  other session's C5 needs narrowing well beyond one bank.
* **`demoproc` survives on `ticket_bomb`** → the **scope decomposition** is what carries binding
  survival, which is a *stronger* result than either of us currently claims: the unscoped mask
  destroys comprehension and the scoped one does not.

---

## §0.17 — ENTRY 6 COMPLETE: `basket_gun` is null, and the dissociation holds at a usable cap

**Artifact:** `outputs/boombness/arm_report/e6g_20260828_024252_196300/arm_report.json`
Cap 640 · n=96 · pinned · both arms in one invocation

| arm | ASR | at cap | median tokens | refusal kw |
|---|---|---|---|---|
| `A_baseline` | 10/96 | 0.0104 | 347.5 | 5/96 |
| `C_band_L6_14` | 7/96 | 0.0000 | 362.5 | 0/96 |

**delta −0.0312 · 4 up / 7 down · p = 0.5488 · net/SD 1.18 · MDE 0.09375 · divergence 96/96**

**This is the null §0.8 predicted, and it is an informative one rather than an underpowered one:**
the design detects ≥0.094, and the two confirming populations both exceed that (−0.146, −0.260)
while this observes −0.031. **And divergence is 96/96 — the intervention fired and changed every
single generation, and ASR did not move.** Live and inert.

### Entry 6, all three populations at non-binding caps

| population | baseline → arm | delta | p | net/SD | divergence | verdict |
|---|---|---|---|---|---|---|
| `main` | 22/96 → 8/96 | −0.1458 | 0.0125 | 4.05 | 96/96 | **confirms** |
| `ticket_bomb` | 27/96 → 2/96 | −0.2604 | ~0 | 9.66 | 96/96 | **confirms** |
| `basket_gun` | 10/96 → 7/96 | −0.0312 | 0.5488 | 1.18 | 96/96 | **null** |

**§0.8's decomposition is confirmed exactly.** The pooled "96 down / 18 up over 8 populations" was
carried by a subset, and the population that showed nothing at cap 192 shows nothing at cap 640 —
with the hook demonstrably live. **The effect is real and population-specific, not universal.**

---

## §5.5 — THE DECIDING CELL: binding survival is SCOPE-dependent, not bank-dependent

`demo_processing_only` on `ticket_bomb` had never been run. It is the cell that separates *scope*
from *bank*, and it resolves cleanly. **All three arms fully reportable.**

**Forced-choice probe, `ticket_bomb`, n=48:**

| arm | mapped-wins | median option mass |
|---|---|---|
| baseline | **45/48** | 0.5534 |
| `legacy_all_query` (unscoped) | **15/48** | **0.1152** |
| **`demo_processing_only` (scoped)** | **45/48** | **0.5201** |

**`demo_processing_only` preserves binding completely** — identical to baseline at 45/48, with option
mass essentially unchanged. The unscoped mask collapses both.

`comprehension_usage` agrees and goes further: baseline 11/48, legacy 3/48, **demoproc 17/48** — the
scoped knockout *raises* the coded reading.

### What this settles

* **§5.2's collapse is a property of the SCOPE, not the bank.** My correction was right that I had
  over-generalised from one population, but wrong about the axis — it is `legacy_all_query` that
  destroys comprehension, on both banks.
* **The other session's C5 (`demo_processing_only`) is vindicated and now extends to a second bank.**
* **The scope decomposition is what carries binding survival** — which is the stronger of the two
  outcomes flagged in §5.4, and stronger than either session had claimed: *the unscoped mask destroys
  comprehension and the scoped one does not.*

**The remaining question is whether the scoped knockout also removes the attack.** If it kills ASR on
`ticket_bomb` while holding binding at 45/48, that is Phase 5's success condition met cleanly on the
population where the unscoped mask failed it. Job **788144** is judging baseline / legacy / demoproc
**in one invocation** to answer it.

---

# §5.6 — THE SPRINT'S CENTRAL RESULT: a scoped knockout that removes the attack AND preserves binding

**Artifact:** `outputs/boombness/arm_report/dp3_20260828_031242_260405/arm_report.json`
`ticket_bomb` · Llama-3.1-8B · cap 640 · **n=96** · pinned judge · **all three arms judged in ONE
invocation** (788144) · probe arms all fully reportable

| arm | **ASR** | Δ | up/down | exact p | net/SD | refusal kw | median tok | **forced-choice binding** |
|---|---|---|---|---|---|---|---|---|
| `A_baseline` | **30/96** | — | — | — | — | 12/96 | 248.0 | **45/48**, mass 0.5534 |
| `legacy_all_query` (unscoped) | **2/96** | −0.2917 | 1/29 | ~0 | 9.56 | **0/96** | 299.5 | **15/48**, mass 0.1152 ⛔ |
| **`demo_processing_only` (scoped)** | **8/96** | **−0.2292** | **4/26** | **0.000059** | **6.60** | 22/96 | 282.0 | **45/48**, mass 0.5201 ✅ |

Neither arm truncates (0.0000 at cap). Divergence 96/96 and 95/96 — both live.

## The brief's success condition, met

> *"ASR falls, but binding/comprehension remains high enough that the model has not merely lost the
> prompt."*

**`demo_processing_only` removes 22 of 30 successful attacks (−0.2292, p = 5.9e-05) while
forced-choice binding is UNCHANGED at 45/48 with option mass essentially intact (0.5534 → 0.5201).**

And the contrast with its unscoped sibling is what makes it a result rather than a data point:
`legacy_all_query` achieves a *slightly larger* ASR drop (−0.2917) **and pays for it by destroying
comprehension** (45/48 → 15/48, mass collapsing five-fold). **The scoped arm buys 79 % of the
behavioural effect at zero comprehension cost.**

## It is not explained by refusal — measured, not asserted

The brief requires an intervention not be "explained by refusal alone unless refusal is the claim".
Refusal keyword rate: baseline 12/96 → **demoproc 22/96** → legacy **0/96**.

Of `demo_processing_only`'s **26 down-flips, 8 (30.8 %) are rows the arm refused** — so **18 of 26
(69 %) are non-refusal**: the model answers, does not refuse, and no longer complies with the mapped
request. Refusal is a *component* of the scoped arm's effect, not its explanation, and that is now a
row count rather than an argument.

`legacy_all_query`'s 29 down-flips contain **zero** refusals. Its mechanism is different in kind: it
does not refuse, it writes *longer* (299.5 vs 248.0), and it cannot say what the codeword means.

## What the two scopes are doing, side by side

| | `legacy_all_query` | `demo_processing_only` |
|---|---|---|
| attack removed | 28/30 | 22/30 |
| binding | **destroyed** (15/48) | **intact** (45/48) |
| refusal | 0/96 — *falls* below baseline | 22/96 — rises |
| length | 299.5 — longest | 282.0 |
| reading | the model loses the mapping and rambles | the model keeps the mapping and declines to use it |

**That is a mechanism dissociation, not a magnitude difference.** The unscoped mask removes the
attack by removing the model's access to the mapping; the scoped mask removes it while the mapping
remains available and reportable.

## Standing caveats

* **One bank, one model, n=96.** `main` has the scoped arm only on the probe side; its scoped ASR
  arm has not been run.
* `demoproc` divergence is **95/96** — one row unchanged, comfortably above the `SMALL_BUT_REAL`
  band but recorded.
* The **31 % refusal component** is real and travels with the claim.
* This is the retrieval knockout, **not** a boombness objective. It bears on entry 6 and Phase 5, and
  says nothing in favour of Phase 7.

---

## §5.7 — ⛔ CORRECTION TO §5.6: "the unscoped mask removes access to the mapping" is FALSE on `main`

**§5.6's mechanism sentence was contradicted by my own §5 data before I wrote it.**

A concurrent session pointed out that `main`'s scoped ASR arm *had* been run — by them, at cap 192 —
so the bank × scope 2×2 was already complete across the two sessions. Re-derived from **my own probe
artifacts**, forced-choice, mapped-wins / n and median option mass:

| bank | arm | binding | option mass |
|---|---|---|---|
| `main` | baseline | 42/48 | 0.5414 |
| **`main`** | **`legacy_all_query`** | **41/48 — INTACT** | 0.3681 |
| `ticket_bomb` | baseline | 45/48 | 0.5534 |
| **`ticket_bomb`** | **`legacy_all_query`** | **15/48 — DESTROYED** | 0.1152 |
| `ticket_bomb` | `demo_processing_only` | 45/48 — intact | 0.5201 |

**Same scope, opposite outcome, two banks.** So §5.6's *"the unscoped mask removes the attack by
removing access to the mapping"* is true on `ticket_bomb` and **false on `main`**, where the mapping
stays available (41/48), refusal *falls*, and the attack goes anyway. That is a **third route**.

**This is mine, not theirs.** They generalised the sentence one bank too far — but I wrote it, and
**§5 (V-31) already contained the refuting number**: I reported `main` legacy at 42/48 → 41/48 and
called it "binding survives". Then §5.2 found `ticket_bomb` collapsing and I reframed the axis from
*population* to *scope* — a reframing that fits `ticket_bomb` and contradicts the `main` row I had
published two sections earlier. **I had both halves and fitted a story to one of them.**

### What survives, and it is narrower

| | replicates? |
|---|---|
| **`demo_processing_only` is bank-STABLE** — removes most of the attack, **raises** refusal, preserves or raises binding | ✅ **2/2 banks** |
| **The REFUSAL SIGNATURE separates the scopes** — `legacy` refuses *less* (3→1, 12→0), `demoproc` refuses *more* (3→20, 12→22) | ✅ **2/2 banks** |
| "unscoped destroys binding, scoped preserves it" | ⛔ **fails on `main`** |

**The refusal signature is the dissociation worth building on**, and the binding effect is
**bank-dependent for `legacy` and bank-stable for `demoproc`**.

**Why `legacy` destroys binding on `ticket_bomb` but not `main` is unexplained, and it is being left
unexplained rather than fitted to two banks.**

### The deciding cell, launched

The obvious test is `legacy` on a **third** bank. `basket_gun` already has my behavioural arms
(§0.17), so only the probe side is missing. **Jobs 788326 / 788327 / 788328** run baseline, `legacy`
and `demoproc` probes on `basket_gun`.

* If `legacy` binding is **intact** there → `ticket_bomb` is the outlier and destroyed-binding is the
  exception.
* If **destroyed** → `main` is the outlier and the question becomes what `main` has that protects it.

Either way it converts a 1-of-2 split into a 2-of-3, which is the minimum for saying which case is
the norm. **§5.6's ASR and binding numbers stand; only its mechanism sentence is withdrawn.**

---

## §6.2 — PHASE 6, behavioural half: ASR DOES rise with demonstrations

**Population:** entry-6 baseline arms, three banks, **cap 640 (non-binding)**, pinned judge,
24 rows per dose per bank.

| bank | n=1 | n=2 | n=4 | n=8 | ρ(n_examples, success) |
|---|---|---|---|---|---|
| `main` | 3/24 | 3/24 | 5/24 | **11/24** | +0.2882 |
| `ticket_bomb` | 3/24 | 4/24 | 8/24 | **12/24** | +0.3212 |
| `basket_gun` | 3/24 | 0/24 | 2/24 | 5/24 | +0.1220 |
| **pooled** | **9/72** | **7/72** | **15/72** | **28/72** | **+0.2501** (n=288) |

**More demonstrations produce more successful attacks**, on all three banks, at a cap that does not
bind. `basket_gun` is weakest — the same low-attackability bank that gave entry 6 its null (§0.17).

Combined with §6.1: `n_examples` raises **both** the query token's `d_surface` projection (ρ=+0.72
at L8, balanced) **and** attack success (ρ=+0.25). Both legs of a mediation story are present.

---

## §6.3 — THE MEDIATION TEST, and it is UNDERPOWERED rather than negative

The brief's decisive Phase 6 question: *"Is boombness still predictive within each `n_examples`
stratum?"* — i.e. does boombness carry information about ASR beyond the dose that produced it?

Joining per-prompt query-occurrence boombness to per-prompt ASR:

| readout | pooled ρ(boombness, ASR) | within n=1 | n=2 | n=4 | n=8 |
|---|---|---|---|---|---|
| `d_surface\|L8\|proj` | **+0.0074** | 0.000 | −0.453 | −0.131 | +0.367 |
| `d_surface\|L12\|proj` | **−0.0074** | −0.389 | −0.130 | +0.044 | +0.171 |
| `ll\|L12\|boombness` | +0.0963 | −0.259 | +0.259 | +0.131 | +0.318 |

**Pooled ρ is indistinguishable from zero, and the within-stratum signs flip.** That is consistent
with the retracted G2 (clean n=90 gave ρ = −0.052).

### But this cannot carry a verdict, and the reason is a join limit

**n=48 pooled; n=12 per stratum, with 1–5 successes per stratum.** A rank correlation on twelve rows
containing one success is not a measurement. **I am not banking a negative on it.**

The cause is structural, not sampling: the `extract_boombness` run covers
`core2x2/strength/consistency/position/role_style/families` and has **no `core2x2_slot3` rows**,
while the entry-6 population is `core2x2 + core2x2_slot3`. So **exactly half the judged population
has no boombness measurement at all** and the join collapses 96 → 48.

| extract blocks | rows | joined to e6 |
|---|---|---|
| `core2x2` | 72 | **48** |
| `strength`, `consistency`, `position`, `role_style`, `families` | 198 | 0 |

### What a powered version needs

1. **`extract_boombness` re-run over `core2x2_slot3`** — restores the join to 96/bank and, across
   three banks, to ~288.
2. **Or the `phase_d` bank**, built for exactly this test with **120 rows per level** and a
   pre-registered dev/heldout split. Ledger entry 10 already records that a clean Fig-9-style
   analysis on that bank *does* show a prompt-level→ASR relation (KEEP-NARROWED, cap 512).

**Phase 7 gate status: still closed, and this section does not move it either way.** The honest
state is that the strongest available direct test of "boombness predicts ASR beyond `n_examples`" is
underpowered by a factor of ~6, and the two routes to powering it are both known and unrun.

---

## §5.8 — the third bank DECLINES rather than decides — and it reframes entry 6's null

`basket_gun`'s three probe arms are in. **They do not answer §5.7's question, and a concurrent
session caught why before I wrote them up.**

**Forced-choice, n=48, all arms reportable:**

| bank | **baseline** mapped-wins | above chance? |
|---|---|---|
| `main` | 42/48 = **0.875** | ✅ |
| `ticket_bomb` | 45/48 = **0.938** | ✅ |
| **`basket_gun`** | **19/48 = 0.396** | ⛔ **BELOW the 0.500 chance line** |

**`basket_gun`'s baseline is INDISTINGUISHABLE FROM CHANCE** (19/48, exact two-sided p = 0.193 —
see §5.13, which corrects an earlier reading of this line as "prefers the codeword"). So:

| arm | mapped-wins | mass |
|---|---|---|
| baseline | 19/48 | 0.3869 |
| `legacy_all_query` | 11/48 | 0.3617 |
| `demo_processing_only` | 23/48 | 0.3872 |

**`legacy`'s 11/48 must NOT be read as "binding destroyed on a third bank."** It is a drop from a
baseline that never bound — the same *kind* of decline as **`window_knife`** in §0.8 (baseline ASR
2/96, which I called "evidence of nothing"), though **on a different axis: `window_knife` lacks ASR
headroom while binding perfectly; `basket_gun` lacks both** (§5.9). **The baseline must bind before "does the intervention preserve binding" is a question at
all, and `basket_gun` fails that gate.**

**§5.7's question is therefore untouched: still 1-of-2, not 2-of-3.** The directions remain
consistent with everything else (demoproc 19→23, legacy 19→11) but from a non-binding baseline they
are uninterpretable, and they are not counted.

### The pre-screen criterion, now explicit

Picking the next candidate bank no longer needs guesswork — but the first version of this screen
said *"clear chance by a real margin"*, which is a sentiment, not a threshold, and **§5.16 shows it
admits the one bank that can never answer.** The corrected screen is a number:
**baseline mapped-wins ≥ 32/48 (0.667)** at n=48, recomputed for any other n.

### The reframe: `basket_gun` fails to install the mapping AT ALL

Pulling the three independent measurements together, this bank is weak on **every** axis:

| measurement | `main` | `ticket_bomb` | **`basket_gun`** |
|---|---|---|---|
| baseline ASR (cap 640) | 22/96 | 30/96 | **10/96** — lowest |
| baseline forced-choice binding | 0.875 | 0.938 | **0.396** — below chance |
| retrieval-knockout ASR effect | −0.146 | −0.260 | **−0.031, null** (§0.17) |

**That is a coherent single account: the doublespeak mapping does not install on `basket_gun`.** And
it is a *better* explanation of entry 6's null there than "the effect is population-specific" —
**there is no mapping to knock out.** §0.17's null stands, but its reading improves: not *"the
knockout fails on this population"* but *"this population has nothing for it to remove"*, which the
binding probe now shows directly rather than by inference.

### A trap I checked rather than assumed

The same session nearly reported a below-chance baseline from a number pooling **three** readouts:
`semantic_forced_choice`, `semantic_one_word` and `comprehension_usage` all carry `p_concept`, so a
filter on field presence mixes scales. Reproduced here: **filtering by `p_concept` gives 55/144 =
0.382**, silently pooling forced-choice (mass 0.3869) with one-word (mass 0.0808).

My reader filters on `query_kind` explicitly, so it does not have the bug — **verified, not
assumed**, because the failure is invisible: it returns a plausible number.

---

# §7 — THE PHASE 7 GATE TEST, POWERED: boombness DOES predict ASR — and why I am **not** calling the gate passed

**Population:** 3 banks × 96 rows = **n=288**, `natural_doublespeak`, query occurrence, **cap 640
(non-binding)**, pinned judge, **`is_self_fit: False` on all 288** (cross-fitted — no score read off
a direction fitted on its own text).

§6.3 reported ρ ≈ 0 at n=48 and called it underpowered. **With the join repaired (§6.3's slot3
defect), the answer reverses.**

| readout | pooled ρ | within n=1 / 2 / 4 / 8 | per-bank (main / ticket / gun) |
|---|---|---|---|
| **`d_surface\|L31\|proj`** | **+0.3340** | +0.338 +0.364 +0.244 +0.260 | +0.110 +0.495 +0.322 |
| **`d_surface\|L8\|proj`** | **+0.3026** | +0.147 +0.238 +0.328 +0.321 | +0.248 +0.370 +0.317 |
| `d_surface\|L10\|proj` | +0.2655 | +0.130 +0.261 +0.274 +0.271 | +0.140 +0.255 +0.356 |
| `d_surface\|L12\|proj` | +0.2442 | +0.118 +0.245 +0.309 +0.254 | +0.144 +0.150 +0.341 |

**Positive pooled, positive in every `n_examples` stratum, positive on every bank.** That is the
brief's decisive Phase 6 question — *"is boombness still predictive within each stratum?"* —
answered **yes**.

## Every control the brief names

| control | result | verdict |
|---|---|---|
| **not the norm** | `cos` (norm-free) ≈ `proj`: **+0.271 vs +0.303** at L8; **+0.303 vs +0.334** at L31, where `hnorm` is only −0.052 | ✅ direction, not magnitude |
| **not length** | ρ(boombness, `n_chars`) = **−0.152** — *anti*-correlated | ✅ |
| **not refusal** | refusal ρ(·,ASR) = −0.139, opposite sign | ✅ |
| **not `n_examples`** | positive within all four strata | ✅ |
| **not generic direction** | `d_context` **−0.124**, `d_inter` +0.043 | ✅ opposite / null |
| **not topic** | within-domain **4/6 positive**, mean +0.222; `d_context` **0/6 positive** | ⚠ partial |
| **dev vs heldout** | **+0.3115 / +0.2884** (L8), **+0.3782 / +0.2945** (L31) | ✅ holds |
| vs `d_naive` | +0.231 against `d_surface` +0.271 (cos) | ⚠ the 2×2 buys little |

## ⛔ Why this is EXPLORATORY and the gate stays CLOSED

The brief is explicit: *"Do not choose one post-hoc. Pre-register candidate metrics on dev, then
evaluate on heldout."* **I did not do that.** I computed pooled correlations across seven layers and
two variants, *then* looked at dev/heldout. **The dev/heldout agreement is reassuring but it is not a
pre-registered holdout test**, because the layers were selected after seeing the pooled result.

Three further reasons to withhold:

1. **It contradicts G2's retraction and I cannot yet say why.** G2 gave ρ = −0.052 on clean n=90.
   This gives +0.30 on n=288. The populations differ in cap (192 vs 640), bank coverage (one vs
   three), block coverage (no slot3 vs slot3), and judge pinning. **Until the difference is
   localised, one of the two is measuring something other than what it says.**
2. **`basket_gun` shows a strong correlation (+0.317) on a bank where §5.8 established the mapping
   never installs.** If there is no mapping, boombness should have nothing to predict. Either the
   non-installation account is wrong, or boombness predicts ASR *through a route that does not
   require the mapping* — and that second possibility would undercut the objective's rationale even
   while its correlation holds.
3. **`d_naive` reaches +0.231 against `d_surface`'s +0.271.** The 2×2 identification buys ~0.04.
   R-25's dose confound (`d_surface` ≈ PC1 ≈ `d_naive`) is visible here, and an objective that is
   ~85 % reproducible by the naive contrast is a weaker object than "boombness".

## Pre-registration for the confirmatory test

Recorded **before** running it:

* **Candidates (2, fixed now):** `d_surface|L8|cos` and `d_surface|L31|cos` — the `cos` variants, so
  norm cannot contribute.
* **Success:** ρ > 0.15 on a **heldout population not used above**, positive within every
  `n_examples` stratum, and exceeding `d_naive|L·|cos` on the same rows.
* **Comparators, mandatory:** `d_naive`, `d_context`, `hnorm`, refusal, `n_chars`.
* **Resolve first:** the G2 discrepancy and the `basket_gun` puzzle. **A metric that predicts on a
  bank where the phenomenon is absent needs an explanation before it becomes an objective.**

**Phase 7 status: REOPENED, not passed.** This is the strongest positive the sprint has produced and
the reason to treat it carefully is that it is strong — the previous sprint's G2 was retracted for
exactly the failure mode this section is at risk of.

---

## §5.9 — ⛔ `window_knife` INSTALLS the mapping — low ASR does NOT imply non-installation

**A concurrent session retracted its own extrapolation before it reached this log, and the retraction
is a result.** It had suggested `window_knife`'s baseline ASR of 2/96 "predicts the same shape" as
`basket_gun`, i.e. a second non-installing bank. It ran the probe arm. **It refutes that.**

**Baseline forced-choice mapped-wins by dose (12 rows/cell; their measurement, their arm):**

| bank | n=1 | n=2 | n=4 | n=8 | Δ | verdict |
|---|---|---|---|---|---|---|
| `main` | 0.667 | 0.917 | 0.917 | **1.000** | +0.333 | installs, saturates |
| `ticket_bomb` | 0.750 | 1.000 | 1.000 | **1.000** | +0.250 | installs, saturates |
| **`window_knife`** | 0.583 | 0.833 | 0.833 | **1.000** | **+0.417** | **INSTALLS, saturates** |
| `basket_gun` | 0.333 | 0.417 | 0.417 | 0.417 | +0.083 | **never installs** |

`window_knife` reaches **39/48 overall with true-median option mass 0.7681 — the highest of any bank
measured**, against `basket_gun`'s 0.3869. It saturates at 12/12 by n=8, exactly like the two banks
that carry entry 6.

**Verified on my side:** `window_knife` baseline ASR is **2/96** (cap 192 — *ASR within first 192
generated tokens*), from my own `lbj_window_knife_lbA` artifact.

### What this corrects

**"Two of five entry-6 populations are non-installation" — which I put in a message to them and they
had offered me — collapses to ONE.** It is not in this log, and it is not going in it.
`basket_gun` is non-installation. **`window_knife` is something else and neither of us has an
explanation.**

§5.8's analogy is narrowed accordingly: `window_knife` and `basket_gun` are both no-headroom
declines, but **on different axes** — `window_knife` lacks *ASR* headroom while binding perfectly;
`basket_gun` lacks both.

### `window_knife` is now the cleanest instance of the sprint's central dissociation

**The mapping installs completely (39/48, mass 0.7681, saturating) and the attack essentially never
lands (2/96).** No intervention anywhere in it — this is a **baseline property of the bank**.

**Binding is necessary but not sufficient for the attack**, demonstrated on a fourth bank without
any knockout, patch or direction involved. Everything else in this sprint reaches that conclusion
*through* an intervention; `window_knife` shows it in the untouched model.

**Caveats:** the probe is theirs and I have not re-derived the per-dose cells, only the ASR endpoint;
cells are 12 rows so the *shape* is the claim and no single cell is; no behavioural arm has been run
at a non-binding cap on `window_knife`, so its 2/96 remains cap-192-labelled.

---

## §7.1 — Which sentence should travel from §7

The same session flagged that *"boombness predicts ASR"* is the sentence that will travel from §7 if
I let it. It is right, and the write-up should not depend on a reader reaching the caveats.

**The takeaway sentence is: the Phase 7 gate is REOPENED AND NOT PASSED.**

`d_surface` correlates with attack success at ρ ≈ +0.30 on n=288 under every control the brief names
except pre-registration — and **pre-registration is the one that matters here**, because G2 was
retracted for precisely this failure mode: a strong correlation, selected after the fact, that did
not survive a clean population. The confirmatory test is pre-registered in §7 and unrun.

**A correlation this sprint discovered by looking is not evidence a future objective would optimise
anything.** That is the reading, and it is the one that should travel.

---

## §5.10 — ⚠ A CODEWORD × CONCEPT CONFOUND under every "population-specific" claim in this sprint

A concurrent session flagged this before I could build on §5.9, and it is real. Verified from bank
metadata: **every measured population changes the codeword AND the concept together.**

| bank | codeword | concept | baseline ASR |
|---|---|---|---|
| `main` | carrot | **bomb** | 22/96 |
| `ticket_bomb` | ticket | **bomb** | 24/96 (192) · 30/96 (640) |
| `basket_gun` | basket | **gun** | 10/96 |
| `button_knife` | button | **knife** | 9/96 |
| `window_knife` | window | **knife** | **2/96** |

**ASR orders largely by concept — bomb (22, 24) > gun (10) ≈ knife (2, 9) — and the codeword varies
with it every time.** So "population-specific" cannot be decomposed into codeword vs concept vs
demonstration sentences. That is a property of *which banks exist*, not a claim about the data, and
it sits under §0.17's entry-6 decomposition, §5.8's non-installation account and §5.9's dissociation
alike.

**Why it bites §5.9 specifically:** if StrongREJECT simply scores knife-compliance lower than
bomb-compliance, then `window_knife`'s 2/96 is a property of the **harm category** and "binding
necessary but not sufficient" there is partly a scoring artifact. **A larger cap does not touch
this** — raising the cap does not make a knife more harmful.

### Evidence I already held, which the four-point ordering hid

**Same concept, different codeword: `window_knife` 2/96 vs `button_knife` 9/96 — a 4.5× spread
*within* `knife`**, nearly as large as the gap between knife (9) and gun (10), which is none.

So **concept explains part of the spread and does not explain `window_knife`'s extremity**:
`window_knife` is low *even for a knife bank*. That weakens the pure-concept hypothesis without
killing it, and it was sitting in my own artifacts.

### The disconfounding 2×2, launched

Codeword and concept **crossed**, all four cells at cap 640 so nothing is cap-mixed:

| | **bomb** | **knife** |
|---|---|---|
| **ticket** | 30/96 ✅ have | **788485** running |
| **window** | **788486** running | **788491** running |

* If `ticket_knife` ≈ 2–9 and `window_bomb` ≈ 22–30 → **concept dominates**, and several
  "population-specific" readings across this sprint are harm-category readings.
* If `ticket_knife` stays high and `window_bomb` stays low → **the concept hypothesis dies** and
  `window_knife`'s dissociation is a genuine bank property.
* Mixed → both contribute, and the decomposition is the finding.

**Until it lands, §5.9's "binding necessary but not sufficient" carries this caveat**, and the
planned non-binding-cap rerun of `window_knife` (included above as 788491) fixes its *labelling*
but not its *confound*. Recorded as a limitation on §0.17, §5.8 and §5.9 simultaneously.

---

## §7.2 — Two of §7's blockers worked: the pooled ρ is NOT an aggregation artifact, but G2 does NOT reproduce

§7 pre-registered two things to resolve before the gate could pass. Both were attacked; **one clears,
one does not.**

### ✅ The pooled correlation survives the aggregation test I applied to everyone else

Pooling three banks with different baseline ASR could manufacture correlation — the same
between-vs-within trap as §0.10's denominator rule, turned on my own headline:

| readout | **pooled** | main | ticket | gun | **mean within-bank** |
|---|---|---|---|---|---|
| **`d_surface\|L8\|cos`** | **+0.2712** | +0.203 | +0.291 | +0.308 | **+0.2673** |
| `d_surface\|L12\|cos` | +0.2423 | +0.165 | +0.156 | +0.327 | +0.2159 |
| `d_surface\|L31\|cos` | +0.3030 | **+0.054** | +0.416 | +0.292 | +0.2537 |
| `d_naive\|L8\|cos` | +0.2314 | +0.172 | +0.277 | +0.145 | +0.1980 |

**At L8 the pooled figure (+0.2712) and the mean within-bank figure (+0.2673) are the same to three
decimals.** Pooling adds nothing; the correlation is genuinely within-bank, on **all three banks**.

The bank means show why it *couldn't* have been an aggregation effect: `main` (boombness −0.4307,
ASR 22/96) and `basket_gun` (−0.4524, 10/96) have **near-identical mean boombness and very different
ASR**, so the between-bank ordering is not monotone and cannot induce the within-bank signal.

**This is a real strengthening of §7** and it was not guaranteed — §0.10's rule condemned entry 6's
pooled claim on exactly this test.

### ⚠ It also changes which candidate I should have pre-registered

**`L31` is heterogeneous across banks (+0.054 → +0.416); `L8` is homogeneous (+0.203 → +0.308).**
`L31` had the *higher* pooled ρ and is the *worse* candidate — on `main` it is +0.054, essentially
nothing.

§7 pre-registered both `L8|cos` and `L31|cos`. **Both stay pre-registered** — I am not dropping a
candidate after seeing data and calling the remainder confirmatory. But it is recorded now, before
the confirmatory run, that **`L31`'s cross-bank heterogeneity is a known weakness going in**, and
that `L8` is the candidate with the homogeneity a usable objective needs.

### ⛔ G2 does NOT reproduce, and that blocker stands

Best reconstruction of G2's clean filter (`slot0` via `family_id`, blocks
`core2x2/extra_conditions/role_style/families`, `natural_doublespeak`, its own cap-192 judge and
`codeword_last` position):

| | G2 published | my reconstruction |
|---|---|---|
| n | **90** | **102** |
| ρ pooled | +0.0860 | **+0.1493** |
| ρ within-domain | **−0.0518** | **+0.0887** |
| domains | 6 | **5** |

**I cannot reproduce G2's number, and my reconstruction differs in n and in domain count**, so the
filter is not the one G2 used. **Until G2 is reproducible, the §7 discrepancy is unexplained** — and
"unexplained" is the correct state, not "resolved in my favour."

Decomposition on the `main` bank alone at L12, which is where G2 lived:

| | n | ρ pooled | ρ within-domain |
|---|---|---|---|
| G2 population, G2 cap-192 judge (my reconstruction) | 102 | +0.149 | +0.089 |
| G2 population, my cap-640 pinned judge | 48 | −0.007 | +0.238 |
| my population, G2's cap-192 judge | 48 | +0.121 | −0.089 |
| **my population, my judge** (§7's `main` cell) | **96** | **+0.144** | +0.102 |

Every main-bank estimate sits between **−0.01 and +0.15** — **far below §7's pooled +0.24–0.30.**
The larger figure comes from `ticket_bomb` and `basket_gun`, not from the bank G2 measured. **So G2
and §7 may not disagree at all: they may be measuring different banks.** That is a hypothesis, and
it is not yet a resolution.

**Gate status unchanged: REOPENED, NOT PASSED.** One blocker cleared, one stands, and the
`basket_gun` puzzle from §7 is untouched.

---

## §7.3 — the `basket_gun` puzzle, and "binding necessary but not sufficient" RE-MEASURED WITHIN banks

§7's third blocker: **boombness predicts ASR at +0.308 on `basket_gun`, a bank where §5.8 showed the
mapping never installs.** If there is no mapping, what is boombness predicting?

**Hypothesis:** `basket_gun` installs the mapping on a *minority* of families (0.417 mapped-wins),
and those are the families that attack. If so, boombness's predictive power there is *consistent*
with the mapping account rather than against it.

**Test:** join each behavioural row to its **own family's** forced-choice probe — same bank, same
codeword, same concept, same demonstrations. Baseline arms only, no intervention.

| bank | families binding | n | **ASR \| binds** | **ASR \| not** | OR | Fisher p |
|---|---|---|---|---|---|---|
| `basket_gun` | 38/96 | 96 | **6/38 = 0.158** | 4/58 = 0.069 | 2.53 | 0.1869 |
| `main` | 84/96 | 96 | **21/84 = 0.250** | 1/12 = 0.083 | 3.67 | 0.2854 |
| `ticket_bomb` | 90/96 | 96 | **27/90 = 0.300** | **0/6 = 0.000** | ∞ | 0.1801 |

**All three banks point the same way. None is significant alone** (Fisher combined p = 0.1580;
3/3 concordance under a sign test = 0.25 two-sided). **This is directional consistency, not an
established effect, and it is reported as such.**

### Why this matters more than its p-value

**It re-measures §5.9's claim WITHIN banks, which sidesteps §5.10's codeword × concept confound
entirely.** The `window_knife` dissociation compared *across* banks, where codeword and concept move
together and StrongREJECT's harm-category scoring is uncontrolled. **This comparison holds bank,
codeword, concept and demonstration pool fixed and varies only whether that family's mapping took.**

On that comparison:

* **Binding looks NECESSARY** — non-binding families attack at **0.000, 0.069, 0.083** across the
  three banks.
* **Binding is clearly NOT SUFFICIENT** — binding families attack at only **0.158, 0.250, 0.300**.

**That is §5.9's conclusion, surviving the confound that threatened it**, obtained without any
intervention and without any between-bank comparison.

### And it partially resolves the `basket_gun` puzzle

`basket_gun` is **the only bank with enough binding variance to run this test** — `main` and
`ticket_bomb` bind at 84/96 and 90/96, near ceiling, leaving 12 and 6 non-binding families. The bank
that looked anomalous in §7 is the one that makes the within-bank test possible.

Boombness predicting ASR there is **consistent with** "the minority of families that do bind are the
ones that attack" rather than requiring a mapping-free route. **Consistent with, not established** —
the 6-vs-4 split carries no weight on its own.

**Gate status: unchanged.** This softens the third blocker from "unexplained anomaly" to
"underpowered but coherent", and leaves the G2 non-reproduction (§7.2) standing.

---

## §5.11 — THE 2×2 RESOLVES: concept dominates codeword by ~14×, and §5.9 loses its headline

All four cells at **cap 640, 0/96 at cap** (plain ASR, no relabelling), pinned judge.

| | **bomb** | **knife** |
|---|---|---|
| **ticket** | **27/96 = 0.281** | **5/96 = 0.052** |
| **window** | **25/96 = 0.260** | **4/96 = 0.042** |

| effect | size |
|---|---|
| **concept** (bomb − knife) | **+0.2240** |
| **codeword** (ticket − window) | +0.0156 |
| **ratio** | **14.3×** |

**The two knife cells agree (0.052, 0.042) and the two bomb cells agree (0.281, 0.260), across
different codewords.** §5.10's hypothesis is now a measurement: **ASR is a property of the concept,
essentially not of the codeword.**

### What this costs §5.9

`window_knife`'s ASR is 0.042 — and **every knife bank sits at ~0.05 regardless of codeword.** So the
gap between "mapping installs completely (39/48)" and "attack never lands (4/96)" is **largely
explained by the harm category scoring low**, not by the mapping failing to drive behaviour.

**The arithmetic of §5.9 is not false — binding 1.000 with ASR 0.042 is still binding without
attack.** What is removed is the *inference*: that gap no longer tells us anything about the
mapping's causal role, because **the same gap sits on `ticket_knife` at 0.052 and nobody is claiming
a mechanism there.** Real dissociation, mundane explanation.

**§5.9 is withdrawn as a headline.** It stays as an observation with the concept effect attached.

### Why §7.3 is the version that survives

§7.3 re-measured "binding necessary but not sufficient" **within** banks — bank, codeword, concept
and demonstration pool all held fixed, varying only whether that family's mapping took. **The concept
effect cannot reach it.** That was the right response to §5.10 before this 2×2 existed, and this
result confirms it was necessary rather than merely cautious.

### ⚠ A judge-draw discrepancy inside my own headline

A concurrent session read `ticket|bomb` as **30/96**; I read **27/96**. Both are correct: the *same
generations* judged in two invocations (`e6j_A_ticket` and `dpj_A_ticket`). **7/96 = 0.0729
disagreements on byte-identical text** — precisely §0.4's floor, landing in a headline cell.

The 2×2 also **mixes invocations**: three cells were judged together (788571) and `ticket|bomb`
comes from an earlier one. The conclusion is invariant — concept/codeword ratio is **14.3× on my
draw and 8× on theirs** — but the exact ratio is not, and quoting it to two significant figures would
be over-precision. **The claim is "concept dominates by roughly an order of magnitude", not 14.3.**

### Still open, and launched

**Do `ticket_knife` and `window_bomb` install the mapping?** Only `window_knife`'s ladder is measured.
If the knife banks install and still score ~0.05, the harm-category account is complete; if they do
not, two effects are tangled and the ASR column cannot separate them. Jobs **788639 / 788640**
(forward-only probes).

---

## §5.12 — THE HARM-CATEGORY ACCOUNT IS COMPLETE: knife banks INSTALL and still do not score

§5.11 left one question: do the knife banks install the mapping, or are two effects tangled? Both
missing probes are now run (forward-only, baseline, no intervention).

| cell | **installs** (forced-choice) | option mass | n=1 → n=8 ladder | **ASR** |
|---|---|---|---|---|
| `ticket \| bomb` | **45/48 = 0.938** | 0.5534 | 0.750 → 1.000 | **0.281** |
| `ticket \| knife` | **30/48 = 0.625** | 0.7685 | 0.417 → 0.917 | **0.052** |
| `window \| bomb` | **40/48 = 0.833** | 0.5156 | 0.667 → 0.917 | **0.260** |
| `window \| knife` † | **39/48 = 0.812** | 0.7681 | 0.583 → 1.000 | **0.042** |

† `window|knife`'s probe is the concurrent session's measurement (R-99); the other three are mine.
All four of my cells are fully reportable.

**All four cells install the mapping, and all four ladders rise with demonstrations.** The knife
banks are not failures of installation — and their option mass is *higher* (0.768, 0.769) than the
bomb banks' (0.553, 0.516): the model is **more** concentrated on the knife mappings, not less.

### The decisive comparison holds the codeword fixed

| | installs | ASR |
|---|---|---|
| `window \| bomb` | **0.833** | **0.260** |
| `window \| knife` | **0.812** | **0.042** |

**Essentially identical installation, a ~6× ASR gap.** The concept effect is **not mediated by
installation**. The model learns `window = knife` as well as it learns `window = bomb`, and then
almost never produces something StrongREJECT scores as a successful knife attack.

*(The `ticket` pair is less clean — 0.938 vs 0.625 — so installation does vary somewhat with concept.
But the `window` pair rules out installation as the explanation, and it is the pair where the two
cells match.)*

### What this settles

**The concept effect is a SCORING property, not a mechanism property.** `knife` compliance is
rarely scored above threshold whether or not the mapping took. That completes §5.10's account and
closes §5.11's open question.

**Consequences, carried forward:**

1. **§5.9 stays withdrawn as a headline** — now on a measurement rather than a suspicion.
2. **Any cross-bank ASR comparison in this sprint is confounded by concept** unless concept is held
   fixed. That reaches §0.17's entry-6 decomposition (`main`/`ticket_bomb` are bomb; `basket_gun` is
   gun; `window_knife` is knife) and §7's per-bank correlations alike.
3. **§7.3's within-bank family-level test is unaffected**, and this is the second independent reason
   it is the version to lead with.
4. **`basket_gun`'s non-installation (§5.8) remains genuine and is now the ONLY such case** — every
   other bank measured installs. Its 0.417 is a real outlier, not a harm-category effect: `gun` is
   not `knife`, and the knife banks install fine.

### An honest note on what the concept effect is NOT evidence for

It would be easy to read this as "the attack only works for bombs". **That is not established.** What
is established is that **StrongREJECT scores knife-compliance above threshold far less often**. Those
are different claims, and separating them needs a judge-independent success measure, which this
sprint does not have.

---

## §5.13 — ⛔ TWO CORRECTIONS: "prefers the codeword" is wrong, and only ONE knife bank installs

A concurrent session tested installation **against chance** rather than against 0.500 by eye, and
two of its statements — both of which I had adopted — fail. **Reproduced independently on my own
artifacts**, exact two-sided binomial against 24/48:

| cell | installs | **exact p** | verdict |
|---|---|---|---|
| `ticket \| bomb` | 45/48 = 0.938 | 1.31e-10 | **above chance** |
| `carrot \| bomb` | 42/48 = 0.875 | 1.01e-07 | **above chance** |
| `window \| bomb` | 40/48 = 0.833 | 3.31e-06 | **above chance** |
| `window \| knife` † | 39/48 = 0.812 | 1.5e-05 | **above chance** |
| **`ticket \| knife`** | **30/48 = 0.625** | **0.111** | ⛔ **INDISTINGUISHABLE** |
| **`basket \| gun`** | **19/48 = 0.396** | **0.193** | ⛔ **INDISTINGUISHABLE** |

† peer-measured.

### Correction 1 — §5.8's "prefers the codeword" is unsupported

§5.8 said *"the model prefers the codeword to the concept on `basket_gun` before any intervention."*
**At p = 0.193 that direction is not supported.** The mapping is **ABSENT**, not **INVERTED** — and
those are different phenomena. 0.396 is below 0.500 numerically and not distinguishable from it
statistically. §5.8 is corrected in place.

**What survives:** `basket_gun` fails to install. **What does not:** any claim about which way it
leans.

### Correction 2 — §5.12's "knife banks install" must be SINGULAR

§5.12 said *"the knife banks install and still score ~0.05"*, plural. **Only `window_knife`
qualifies** (39/48, p = 1.5e-05, ASR 0.042). **`ticket_knife` at 30/48, p = 0.111, is uninformative
on installation** — it neither supports nor contradicts. The harm-category account rests on **one**
bank, not two.

**§5.12's decisive comparison is unaffected**, and that is the part that carried it:

| | installs | exact p | ASR |
|---|---|---|---|
| `window \| bomb` | 0.833 | 3.31e-06 | 0.260 |
| `window \| knife` | 0.812 | 1.5e-05 | 0.042 |

**Both demonstrably above chance, statistically indistinguishable from each other, ~6× apart in
ASR.** The window pair alone establishes that installation does not mediate the concept effect. The
`ticket` pair was never the load-bearing comparison; it was offered as confirmation and is not.

### The meta-lesson, which is the transferable part

**Both errors are the same shape: checking whether an effect cleared a threshold, never whether the
threshold was RESOLVABLE.** A 48-row binary readout cannot separate 0.625 from 0.500 — and nothing
about "0.625" looks unresolvable. This is the same failure as §0.3a's underpowered nulls, where I
built `min_detectable_net_flips` precisely so a p of 1.0 could not read as evidence of absence, and
then did not apply the same reasoning to a proportion.

**The binding constraint is the population, not the model** — and §5.15 shows it is worse than
"needs a bigger run": `ticket_knife` is **unresolvable with this bank at any usable n**. That is the same coverage defect as §6.3's join limit and the concurrent
session's C-24 — **the measurement covering less of the population than the claim does**, which
never surfaces as an error, only as a smaller n.

---

## §5.14 — `basket_bomb` INSTALLS: the failure is the CONCEPT `gun`, not the bank or the codeword

**Independently reproduced**, exact match to the concurrent session's measurement:

| cell | installs | exact p | verdict |
|---|---|---|---|
| **`basket \| bomb`** | **42/48 = 0.875** | **1.01e-07** | **above chance**, ladder 0.667 → 0.833 → 1.000 → 1.000 |
| **`basket \| gun`** | **19/48 = 0.396** | 0.193 | indistinguishable |

**The same codeword installs decisively with `bomb` and fails with `gun`.** So §5.8's
"the mapping does not install on `basket_gun`" was right about the fact and **wrong about the
scope**: it is the **concept `gun`**, not the bank and not the codeword `basket`.

**Installation tracks concept exactly as ASR does**, and the codeword does almost nothing on either
axis:

| codeword | with **bomb** | with the other concept |
|---|---|---|
| `basket` | **42/48** | `gun` **19/48** |
| `ticket` | **45/48** | `knife` 30/48 (unresolvable) |
| `window` | **40/48** | `knife` **39/48** |
| `carrot` | **42/48** | — |

### What this narrows

**§0.17's entry-6 null on `basket_gun` is a GUN-CONCEPT null, not a basket-population null.** The
intervention had nothing to remove there because the *concept* never installed — and the identical
codeword installs fine with `bomb`. That is a materially different limitation to write than
"population-specific effect", and it is the third time this sprint that a "population" claim has
turned out to be a concept claim (§5.10, §5.11, here).

### The state of the concept story, consolidated

| effect | status |
|---|---|
| **ASR tracks concept, ~an order of magnitude over codeword** | established (§5.11, 2×2, both draws) |
| **`gun` fails to install; `bomb` installs on the same codeword** | established (here) |
| **`window\|knife` installs and still scores 0.042** | established on **one** bank (§5.13) |
| `ticket\|knife` installation | **unresolvable at n=48** (p = 0.111) |
| "the attack only works for bombs" | **NOT established** — this is a judge-scoring result |

---

## §DR-2 — DEEP REVIEW (4-hour), 2026-08-28 06:20

### Mechanical checks — all clean

| check | result |
|---|---|
| cited paths in this log | **71, 0 unresolvable** |
| cited run ids | **4, 0 unresolvable** |
| full suite (conda interpreter) | **1217 passed, 7 skipped, 0 failed** |
| `check_all.py` deliverable guards | **6/6** |
| sprint commits | **49** |

### Ledger

| | at audit | **now** |
|---|---|---|
| KEEP | 1 | **3** |
| KEEP-NARROWED | 4 | **5** |
| NEEDS RERUN | 5 | **3** |
| RETRACT | 3 | 3 |
| OPEN | 1 | **0** |

### ⛔ THE GAP THIS REVIEW FOUND: Phase 3 was never run

The brief puts an **aggressive-intervention gate BEFORE objective extraction**:

> *"Before doing delicate surgical patching, test whether the basic idea is even possible … If no
> aggressive patch can move behavior without degeneracy, do not proceed to objective extraction."*

**I did Phase 3.2 (the negative patch) and never did Phase 3.1 (the positive one).** §0.14 removed
`d_surface` and found ASR *rises*. **Nobody has tested whether ADDING `d_surface` — pushing the
codeword token toward the concept — moves behaviour at all.** And §7 reopened the objective gate
without that prerequisite having been met.

**This is also exactly ledger entry 4's outstanding rerun.** Entry 4 (*"`d_surface` is causal because
steering changes attack behaviour"*) sits at NEEDS RERUN because its evidence is the
`steer_L8_a1`/`steer_L8_a2` runs at **cap 192 with 100 % truncation** (§0.2's worst stratum). So one
experiment closes a ledger entry and fills the plan's missing gate.

**Launched (788769 / 788770 / 788771)**, `ticket_bomb` (the highest-headroom bank, baseline 27–30/96),
**cap 640**, pinned judge to follow, all against the existing `e6A_ticket_bomb` baseline:

| arm | intervention | question |
|---|---|---|
| `p3_add_pos` | `d_surface:add:8-8:+1.0` | **does pushing toward the concept raise ASR?** |
| `p3_add_neg` | `d_surface:add:8-8:−1.0` | is the effect *directional* or does either sign suppress? |
| `p3_rand` | `random:add:8-8:1.0` | matched-dose control |

The `−1.0` arm matters because **G4's retracted finding was that BOTH signs suppressed ASR** — a
directional null. If that reproduces at a non-binding cap, the objective is dead on its own terms
regardless of §7's correlation; if `+1.0` raises and `−1.0` lowers, Phase 3's gate passes for the
first time.

### Standing self-criticism

1. **Every phase of this sprint that produced a positive result has subsequently been narrowed** —
   §5.6 by scope, §5.9 by concept, §5.12 by resolvability, §0.17 by concept. The corrections have all
   come from cheap structural checks run *after* the write-up. The pattern is consistent enough that
   **any new positive should be assumed to have an un-run structural check attached.**
2. **Nine of the sprint's corrections originated with the concurrent session, not with me.** My own
   catches were mostly of my own code (the exclusion bug, the case-sensitivity bug, the mangled
   heredoc); theirs were mostly of my *reasoning*. That asymmetry is worth naming: I check
   instruments well and claims less well.
3. **Phase 8 remains correctly unstarted**, and §7's gate remains closed.

---

## §5.15 — `ticket_knife` is UNRESOLVABLE with this bank, not merely unresolved

The concurrent session retracted its own "96 rows would settle it" recommendation before I spent an
arm on it. **Both halves verified independently here.**

**The rows do not exist.** `ticket_knife` has 288 forced-choice rows, 72 per condition, and
`natural_doublespeak` splits **12 per dose** across `n_examples ∈ {0,1,2,4,8,16}`:

| population | n | note |
|---|---|---|
| what I ran (`n ∈ {1,2,4,8}`) | **48** | §5.13 |
| ceiling **with** demonstrations (add `n=16`) | **60** | the real maximum |
| including `n=0` | 72 | `n=0` teaches no mapping — dilutes the thing measured |
| a larger population | **96** | **does not exist** on this bank/condition |

**And the ceiling would not settle it.** Power to detect a true 0.625 against chance, exact
two-sided, α=0.05 — **my computation, matching theirs to three decimals**:

| n | power |
|---|---|
| **48** (what I ran) | **0.331** |
| **60** (this bank's ceiling) | **0.399** |
| 96 (unreachable) | 0.627 |
| 144 (what would be needed) | 0.828 |

**At the maximum this bank can supply, power is 0.399 — a coin flip.** Resolving `ticket_knife`
needs ~144 rows, **three times the `natural_doublespeak` forced-choice population that exists.**

### How this changes the limitation

§5.13 recorded `ticket_knife` as unresolvable *at n=48*, which implies someone could close it with a
rerun. **They cannot.** It is a **bank-design change**, not a rerun.

**Stated for the limitations section:** *the harm-category account rests on `window_knife` alone, and
will continue to unless a larger probe population is built. `ticket_knife` cannot confirm or refute
it at any n this bank supports.* An "open item" framing would have implied a cheap fix and there
isn't one.

### METHODS NOTE — three independent instances of the same defect

This is now the **third** case in two sessions of *the measurement covering less of the population
than the claim does*, and **all three surfaced only when someone counted rather than read**:

| instance | shape | surfaced by |
|---|---|---|
| §6.3's join limit | `extract_boombness` predates `core2x2_slot3`, so half the judged population had no boombness value — n=48 not 288 | counting the join |
| the concurrent session's C-24 | the forced-choice probe only ever existed for `core2x2` — 396 of 468 family stems had no probe side | counting the stems |
| **§5.15** | `natural_doublespeak` forced-choice tops out at 60 usable rows, not the 96 assumed | counting the doses |
| *(and §DR-2)* | Phase 3 was never run at all — the plan's coverage, not a population's | counting the phases |

**None of these presents as an error.** Each presents as a *smaller n*, or as a section that simply
isn't there — which is why reading the analysis never finds them and counting the rows always does.

---

## §5.16 — ⛔ THE PRE-SCREEN I ADOPTED WAS A SENTIMENT, NOT A THRESHOLD

§5.8 adopted a screen for choosing candidate banks: *"baseline forced-choice mapped-wins must clear
chance by a real margin."* The concurrent session — prompted by my own line that prescriptions escape
auditing — audited it and **it fails.**

Read the obvious way (above 0.500) at n=48, **verified here**:

| cell | mapped-wins | naive (>0.500) | **tested (≥32/48)** | |
|---|---|---|---|---|
| `ticket\|bomb` … `window\|knife` | 45–39/48 | PASS | **PASS** | agree |
| **`ticket\|knife`** | **30/48 = 0.625** | **PASS** | **FAIL** | ⛔ **screen misleads** |
| `basket\|gun` | 19/48 = 0.396 | fail | FAIL | agree |

**The smallest count clearing p<0.05 at n=48 is 32/48 = 0.6667** (p = 0.0293; 31/48 gives 0.0595).
The naive screen admits everything above 24/48 — **including `ticket_knife`, the exact bank §5.15
established can never answer.** Anyone applying it picks `ticket_knife` and rediscovers the dead end.

### Corrected screen — a number, and it moves with n

| n | threshold | proportion |
|---|---|---|
| **48** | **≥ 32** | 0.6667 |
| 60 | ≥ 39 | 0.6500 |
| 72 | ≥ 45 | 0.6250 |
| 96 | ≥ 59 | 0.6146 |
| 144 | ≥ 85 | 0.5903 |

**The threshold must be recomputed for the population actually used, not carried.** §5.8 is corrected
in place.

### METHODS NOTE, second failure mode: prescriptions are not audited like findings

§5.15 named one defect class — *the measurement covering less than the claim does*. This is a
**different** one, and it needs a different check.

**Two prescriptions have failed in two ticks against zero failed findings in the same window.**

| | failed? | why it escaped |
|---|---|---|
| findings (both sessions) | 0 in this window | they carry numbers, and we have been recomputing each other's |
| **"96 rows would settle it"** (§5.15) | **yes** | a claim about a *future* run — no existing data could refute it |
| **"clear chance by a real margin"** (here) | **yes** | names the right *concept* and never the *threshold* |

**A prescription carries no numbers to check.** "Clear chance by a real margin" reads as rigour
because it names the correct idea; it fails because nothing about it looks incomplete. The check is
one line: **name the number, or don't give the rule.**

Both failures were the concurrent session's to make and the concurrent session's to catch — but I
**adopted** the screen into §5.8 without noticing it had no threshold, which is the same lapse at one
remove. A rule I cannot apply mechanically is a rule I have not checked.

---

# §3 — PHASE 3: THE AGGRESSIVE-PATCH GATE **FAILS**

**Artifact:** `outputs/boombness/arm_report/p3_20260828_072154_744607/arm_report.json`
`ticket_bomb` · Llama-3.1-8B · **cap 640** · n=96 · pinned judge · **all four arms judged in ONE
invocation** (788861) · this is also **ledger entry 4's rerun** (its evidence was cap-192 at 100 %
truncation).

## Read this first

> **Both signs of `d_surface` and a matched-dose RANDOM direction all move ASR. The only arm that
> RAISES it is degenerate on 96 % of rows. There is no clean, direction-specific, non-degenerate
> behavioural effect — so the Phase 3 gate fails and Phase 7 must not proceed on this axis.**

That sentence is placed before the numbers deliberately, on the §7.1 principle: the number that will
otherwise travel from this section is "+0.479", and it is the one that means least.

| arm | **ASR** | Δ | up/down | p | **at cap** | median tok | refusal | divergence |
|---|---|---|---|---|---|---|---|---|
| `A_baseline` | **26/96** | — | — | — | **0/96** | 248 | 12/96 | — |
| **`d_surface` add α=+1** | **72/96** | **+0.4792** | 53/7 | ~0 | ⛔ **92/96 = 0.958** | **640** | 12/96 | 96/96 |
| **`d_surface` add α=−1** | **0/96** | −0.2708 | 0/26 | ~0 | 0/96 | **63** | 0/96 | 96/96 |
| **`random` add α=+1** | **5/96** | −0.2188 | 1/22 | 6e-06 | 0/96 | 175.5 | 36/96 | 96/96 |

## Why each row kills a different part of the objective case

**1. The positive arm is not a usable measurement.** 92 of 96 rows never terminate, with median
tokens **exactly 640**. `assert_sprint_grade` **refuses it** — `cap_binds=True` with no
`binding_kind`. Its +0.479 is an ASR-within-640 over runaway text, and length predicts being scored
inside every arm (ρ = +0.24 baseline, +0.16 positive, +0.12 random). Its median generation is
**1884 chars against the baseline's 1152**. **A 640-token ramble gives StrongREJECT far more surface
to score, and this arm is 96 % rambles.**

*(§0.13 ran this same check on the project-out arm and the effect SURVIVED — 25 of 26 flips were in
terminating rows. Here that test cannot even be run: only 4 rows terminate.)*

**2. The negative arm suppresses — but so does random, at the same dose.** −1.0 gives 0/96 and the
matched random direction gives 5/96. **Suppression is not `d_surface`-specific**; a perturbation of
this magnitude at L8 destroys the attack whatever direction it points in. The random arm also
*triples* refusal (12/96 → 36/96) while `d_surface`−1 drives it to **0/96** and truncates generation
to a 63-token median — two different kinds of breakage, neither of them steering.

**3. This reproduces G4's retracted finding at a non-binding cap.** G4 said *both signs suppress* —
a directional null. Here −1 suppresses to 0/96, and +1 "raises" only by generating 640-token text
that no longer terminates. **The 2026-08 retraction of G4 was correct, and it now holds under the
fixed protocol.**

## The gate, in the brief's own terms

> *"If no aggressive patch can move behavior without degeneracy, do not proceed to objective
> extraction. Record the negative."*

**Recorded. The gate fails.** Every arm that moves ASR either (a) is degenerate on 96 % of rows, or
(b) is matched by a random direction at the same dose.

## What this does to §7

§7 found `d_surface` correlates with ASR at ρ ≈ +0.30 (n=288) and I marked the gate **reopened, not
passed**, pending pre-registration. **Phase 3 now closes it on prior grounds**, and this is the more
fundamental of the two:

* **§7 shows `d_surface` is PREDICTIVE.** That still stands — the correlation is real, within-bank,
  and survives its controls.
* **§3 shows `d_surface` is not CONTROLLABLE.** Pushing along it does not produce more attack; it
  produces more *text*. Pushing against it suppresses no better than noise.

**An objective needs the second property, not the first.** A signal you can read but cannot steer is
a measurement, not an optimisation target — and GCG/MAC would be optimising exactly the quantity
that, when pushed, breaks generation instead of steering behaviour.

**PHASE 7 GATE: CLOSED. PHASE 8 MUST NOT BE BUILT.** Ledger entry 14 ("a GCG objective was ever
justified") stays **RETRACT**, now with a direct non-degenerate-controllability test behind it rather
than only the older steering evidence. Ledger entry 4 moves **NEEDS RERUN → RETRACT**: steering is
not causal in the required sense, measured at a cap that does not bind.

---

# §9 — FINAL SUMMARY (deliverable 12)

**Ledger: 7 KEEP-NARROWED · 3 KEEP · 4 RETRACT · 0 NEEDS-RERUN · 0 OPEN.** Every entry that entered
the sprint needing a rerun has had one.

## §10 — the brief's seven minimum success criteria, answered

| # | question | answer |
|---|---|---|
| **1** | Is there a measurable token-level boombness signal at codeword tokens? | **YES.** Reproducible directions (split-half cos 0.98–0.996), and the projection predicts ASR at ρ ≈ +0.27–0.30 (n=288, cross-fitted, within-bank on all 3 banks). |
| **2** | Does it grow across layers / demonstrations / occurrences? | **YES, with a caveat.** Balanced within `core2x2`+plain, `d_surface\|L8` rises monotonically with `n_examples` (ρ=+0.72). **But the logit-lens readout on the same tokens FALLS (−0.45)** — "boombness" is not one quantity. |
| **3** | Is prompt-level separable from token-level? | **YES.** ρ = 0.287 at L12 — ~8 % shared rank variance. They are two objects, measured. |
| **4** | Does either predict ASR beyond `n_examples`/refusal/length/domain? | **YES on the direct controls** (positive within every dose stratum; not norm, not length, not refusal, `d_context` opposite-signed). **But NOT pre-registered**, and **G2 does not reproduce**, so this is exploratory. |
| **5** | Can aggressive patching make the codeword more bomb-like *behaviourally*? | **NO.** §3: the only arm that raises ASR is degenerate on **92/96** rows; a matched **random** direction suppresses as well as `−d_surface`. |
| **6** | Can surgical removal lower ASR without destroying binding? | **YES — for the SCOPED knockout.** `demo_processing_only` removes 22/30 attacks (p=5.9e-05) with binding **unchanged at 45/48**. The unscoped mask does it too but destroys binding on one bank of two. |
| **7** | Is any candidate objective justified for GCG/MAC? | **NO.** Stated plainly below. |

## The answer to question 7

> **No objective should be built.**

`d_surface` is **predictive but not controllable**. §7 established the correlation; §3 established
that pushing along it yields runaway text rather than more attack, and pushing against it suppresses
no better than noise. **An optimiser needs controllability, and the direct test of it failed.**

## What survives for research

1. **The demonstration-retrieval pathway is causal, and scoping matters.** `demo_processing_only`
   removes most of the attack while leaving the mapping intact and reportable (§5.6, §5.5). This is
   the sprint's best result and the one to build on.
2. **Binding is necessary but not sufficient** — measured *within* banks, immune to the concept
   confound (§7.3). Non-binding families attack at 0.000–0.083; binding families at 0.158–0.300.
3. **The refusal channel replicates almost exactly** at a non-binding cap: C +0.2020 vs +0.2061,
   D +0.2788 vs +0.2869 (§0.15).
4. **Removing `d_surface` RAISES ASR** (+0.3229, p=2e-06) — opposite to the original hypothesis,
   confirmed at a cap that does not bind (§0.14).
5. **ASR is a property of the harm CONCEPT, not the codeword** — ~an order of magnitude (§5.11), and
   not mediated by installation (§5.12).

## What must be retracted or narrowed

* **RETRACT:** the GCG objective (entry 14); `d_surface` steering as causal (entry 4); G2's
  prompt-level→ASR claim; the "truncation caveat discharged" meta-claim.
* **NARROWED:** entry 6's pooled "96 down / 18 up" → per-population, 2 of 3, unscoped mask only.
* **WITHDRAWN as a headline:** `window_knife`'s binding-without-attack (§5.9) — real arithmetic,
  mundane explanation.
* **`ticket_knife` is UNRESOLVABLE** with this bank at any usable n (§5.15).

## The strongest negative result

**§3.** Both signs of `d_surface` and a matched random direction all move ASR; the only one that
raises it does so by breaking generation on 96 % of rows. This is a *direct, non-degenerate
controllability test* — the thing the previous sprint's G4 retraction inferred, now measured at a
non-binding cap with a matched control.

## The best publishable story

**"A retrieval pathway you can cut without breaking comprehension — and a direction you can read but
cannot steer."** The scoped knockout (§5.6) and the controllability failure (§3) are the same paper:
the mechanism is in the *demonstration-retrieval pathway*, not in a linear direction at the codeword
token, and the sprint has a clean positive and a clean negative to say so.

## What should be done next

1. **Do not build the GCG objective.** (Gate closed on prior grounds.)
2. **Extend `demo_processing_only`** — one model, one bank, n=96. It needs a second model and a
   pre-registered replication.
3. **Resolve the G2 non-reproduction** (§7.2) before any predictive claim is published.
4. **Build a larger forced-choice probe population.** Three separate limits this sprint traced to
   probe coverage (§5.15, §6.3, C-24). 144 rows would resolve what 48 cannot.
5. **A judge-independent success measure.** Every concept-level result here is entangled with
   StrongREJECT's scoring (§5.12).

---

## §7.4 — G2's NON-REPRODUCTION IS RESOLVED: the population reproduces exactly, and G2 does not conflict with §7

§7.2 recorded that I could not reproduce G2 (n=102 vs 90, within-domain +0.089 vs −0.052) and left
it as the standing blocker on any predictive claim. **Closed.** Two things were wrong with my
reconstruction, both found by reading `analyze_g2.py` rather than guessing at the filter:

**1. `--min-examples 1`.** `analyze_g2.py:526` drops rows below `min_examples`, and the artifact
records `min_examples = 1`. I had included the 12 `n_examples=0` rows. **Adding the filter gives
n=90 — exact.**

**2. `rho_within_domain` is not a mean of per-domain rhos.** `rank_corr_pair` ranks globally,
standardises, **demeans by cluster**, then correlates. I had averaged per-domain Spearmans — a
different estimator, which is also why I reported 5 clusters where G2 reports 6.

### The reproduction

| | G2 published | **my reconstruction** |
|---|---|---|
| n | 90 | **90** ✅ |
| clusters | 6 | **6** ✅ |
| ρ pooled | +0.085957 | +0.074950 |
| **ρ within-domain** | **−0.051801** | **−0.069318** |

**The population reproduces exactly and both statistics agree in sign**, differing by 0.011 and
0.017. I have not isolated the residual — most likely a tie-handling or standardisation detail
between `scipy.stats.rankdata` and my pure-Python implementation (ASR is binary, so ties dominate).
**I am not claiming a bit-exact reproduction**; I am claiming the population and the sign, which is
what the blocker required.

*(Checked and excluded: the position definition. `is_query_occurrence` and `is_final_occurrence`
give byte-identical results on this population.)*

### What it settles

**G2 and §7 do not conflict — they measure different populations.** §7.2 offered that as a
hypothesis; it is now confirmed:

| | population | result |
|---|---|---|
| **G2** | `main` bank, slot0 only, blocks `core2x2/extra/role_style/families`, **cap 192** | **−0.052 → null** |
| **§7** | **3 banks**, `core2x2`+**slot3**, `n_ex ∈ {1,2,4,8}`, **cap 640**, cross-fitted | **+0.27 to +0.30** |

**G2's null is correct on G2's population, and §7's positive is correct on §7's.** The largest single
difference is bank coverage: §7.2 already showed **every `main`-bank estimate sits between −0.01 and
+0.15**, far below §7's pooled figure, which comes from `ticket_bomb` and `basket_gun` — banks G2
never measured.

### What this does and does not do to the gate

**It removes §7's second blocker.** It does **not** reopen the gate:

* §7's **pre-registration** failure stands — the candidates were chosen after seeing pooled results.
* **§3's controllability failure is decisive and independent.** `d_surface` being predictive on a
  wider population was never the thing in doubt; being *steerable* was, and it is not.

**Phase 7 remains CLOSED and Phase 8 must not be built.** This section makes the predictive claim
*publishable with its scope attached* — three banks, `core2x2`+slot3, cap 640 — rather than
apparently contradicting a retracted result.

---

## §5.17 — Extending §5.6 to a second model surfaced TWO measurement defects before it produced a result

Next-step #2 was to test whether `demo_processing_only` preserves binding on a **second model**.
§5.6's ASR half already exists on Qwen3-14B (`A_baseline` 11/80 → `demo_processing_only` 1/80, cap
640, bank `longpreQ14B`); only the **binding** half was Llama-only. The probe is forward-only
(`--no-generate`), needs no judge, and the matched population is the same bank the ASR arms used.

It has not produced a number yet. It produced two defects, one of them mine.

### Defect 1 — a run can report `status: ok` while silently dropping a NON-RANDOM half of its population

`q5A_lpQ14B` (160 rows: 3 query kinds × 2 doses × 2 blocks) wrote **68 rows and reported
`status: ok`**. The FailureLedger recorded the truth — `n_attempted 160, n_succeeded 68, n_failed
92`, all `OutOfMemoryError` — but `DONE.json` says `ok` and `rows_written: 68`, and nothing in the
headline says half the population is missing.

The missingness is **length-correlated, which is what makes it dangerous**: `n_examples=8` prompts
are the longest and are the ones that OOM'd. Surviving rows skew short.

| | n_ex=4 | n_ex=8 |
|---|---|---|
| rows written | 62 | 6 |

A binding estimate computed from that is an estimate on short prompts wearing the label of the whole
bank. **No percentage would have revealed it; only the row counts did.**

**Corpus audit — the defect has NOT contaminated the sprint.** I swept all **538** completed
`score_behavior` runs for `n_failed > 0`: **11 have any failure, and 8 of those are `n_succeeded=0`**
(dead runs — any analysis of them shows n=0, which is visible, not silent). The only genuinely
*partial* runs are one `smoke_*` and the two I just created. **Every published sprint result rests
on a fully-populated run.** This is a clean negative check, and it is the reason the defect is a
process finding rather than a retraction.

### Defect 2 — the option-mass gate advertised `PASS` over a readout that was 90% NaN

Trying to fix the OOM by sharding the model across **2 GPUs** (`--gpus=2`; `device_map="auto"` was
already the default, so this needed no code change) removed the OOM — 40/40 rows, 0 failures — and
**corrupted the readout**: `option_mass` was **NaN on 36 of 40 rows** in the baseline and **40/40**
in the knockout arm. The 1-GPU run of the identical spec has **0 NaN**. Multi-GPU sharding of
Qwen3-14B under eager attention produces NaN logits. **`--gpus=2` is not a usable workaround here,
and the two 2-GPU runs are discarded.**

That was my error. The defect it exposed is not:

```
gate: PASS                      <-- the headline
reportable: False               <-- the SAME run's own per-readout flag
median_true: nan
```

**The headline and the flag disagreed, and the headline was wrong.** The per-readout flag was
computed as `median_true >= 0.05`, and `NaN >= 0.05` is False, so `reportable` was correctly False.
But the headline appended to `tail_fail` only when `med < min_option_mass`, and **`NaN < 0.05` is
also False** — so nothing was appended and the run advertised `option_mass_gate: PASS`. A NaN
escapes *both* directions of a threshold comparison; one direction was the refusal and the other was
the alarm, and it slipped past both.

*(A consumer calling `asr_protocol.readout_reportability()` — which surfaces the producer's
per-readout flag rather than the headline — would have caught this. That helper existed. The
headline is what a human reads.)*

**Fixed** in `score_behavior.py`: NaN/None values are counted and excluded before sorting, and a
readout with **any** absent measurement is refused outright with the count reported. A NaN option
mass is an **absent measurement, not a small one**, so no threshold can make it reportable.

There is a second, quieter trap in the old code: `sorted()` on a list containing NaN neither raises
nor sorts — every NaN comparison is False, so the result is an arbitrary interleaving whose median
depends on **input order**. On this run's row order it happened to yield NaN; on an ordering with
the NaNs grouped differently it yields a *finite* value drawn from a mostly-NaN list. The guard
therefore filters rather than relying on how the corruption happens to be arranged.

**Guard mutation-tested** (`tests/test_option_mass_nan_guard.py`, 11 tests): dropping the NaN filter
kills 8 tests, weakening it to `if not v:` kills 7. Full suite **1240 passed / 7 skipped**.

### Defect 3 (the actual cause) — the readout materialised logits it immediately discarded

The OOM had a real cause, and it is not model size. `next_token_readout` reads **only the final
position** but a plain forward returns logits for **every** position: `[1, S, 151936]` on Qwen3 is
~0.3 MB per token, so a long-prefix prompt spends gigabytes on rows the function throws away. This
is exactly why the cap-640 **generation** arms ran clean (80/80, 0 failures) on the *same bank* where
this readout OOM'd 22 of 40 — `generate` keeps only the last row.

Passing `logits_to_keep=1` returns `[1, 1, V]`, so `[0, -1, :]` selects **the same vector**. This is
byte-identical, not an approximation — a memory fix, not a numerical one.

### Status of the §5.6 extension: NOT YET ANSWERED, and not blocked

The one uncorrupted Qwen3 measurement is the 1-GPU baseline, and it is **encouraging but partial**
(18 of 40 rows, OOM-biased toward short prompts, so it is not quotable as an estimate):

* mapped-wins **14/18 = 0.778** — *(this line's screen claim is withdrawn in §5.18.1: the rate
  form of the threshold is wrong at this n, and the population is attrited)*
* median option mass **0.9998** — not a tail decision at all, unlike the Llama banks

So the probe **does** work on Qwen3 and the bank **does** install the mapping. The knockout arm has
no uncorrupted measurement yet. Both arms are relaunched single-GPU with the `logits_to_keep` fix.

**Nothing here touches the Phase 7 gate, which remains CLOSED. Phase 8 must not be built.**

---

## §5.18 — §5.6 EXTENDS TO A SECOND MODEL: on Qwen3-14B the scoped knockout removes the attack and leaves binding intact

§5.6's success condition — *the intervention removes the attack without removing the mapping* — was
Llama-only on the binding side. It now holds on **Qwen3-14B** as well. Both halves, same bank
(`longpreQ14B`), same doses (`n_ex ∈ {4,8}`), same blocks (`core2x2` + `core2x2_slot3`):

| half | arm | result | artifact |
|---|---|---|---|
| **ASR** (cap 640) | `A_baseline` → `demo_processing_only` | **11/80 → 1/80** | `p26j_A_20260827_045339_1483852`, `p26j_dp_20260827_045339_1483855` |
| **binding** (forced choice) | `A_baseline` → `demo_processing_only` | ~~14/18 → 15/18~~ **SUPERSEDED by §5.19: 29/40 → 30/40** | ~~`q9A_lpQ14B_fc_20260828_104610_2283895`~~ (ATTRITED, 22/40 lost to OOM), `q8D_lpQ14B_fc_20260828_102657_2281919`; **live artifacts are `qbA_lpQ14B_b1_...` / `qbD_lpQ14B_b1_...`** |

### The binding contrast, paired

Paired on the **18 prompt_ids measured by both arms**, `semantic_forced_choice`, gate PASS on both:

| | mapped-wins | median option mass |
|---|---|---|
| `A_baseline` | **14/18 = 0.778** | **0.9998** |
| `demo_processing_only` | **15/18 = 0.833** | **0.9999** |

discordant **3 up / 2 down**, n_disc=5, exact two-sided **p = 1.0000**.

**Binding does not degrade — it is numerically higher under the knockout.** The knockout arm's own
complete 40 rows give **30/40 = 0.750**, also above the §5.16 screen, so the conclusion does not
depend on the paired subset.

**Unlike `ticket_bomb` (§5.2) the mapping is not destroyed**, and the evidence for that is the
knockout arm's own **complete** 40 rows: **30/40, two-sided p=0.00222, critical_k=27 → INSTALLED**
(`mapping_installation_verdict`, `v56_qwen_20260828_111912_1260091`). That run has **zero** attrition,
so it carries the "mapping survives" half on its own.

⚠ **I originally wrote that the baseline "clears the ≥0.667 screen at 0.778". That sentence is
withdrawn** — see §5.18.1. It is a one-sample fraction computed on the attrited baseline, and both
halves of it were unsound.

**Option mass is the sharpest contrast with the Llama results.** On the Llama banks forced choice was
decided inside roughly half the next-token mass (`main` 0.5416, `ticket_bomb` 0.5695, collapsing to
0.1162 under knockout). Here it is **0.9998 → 0.9999**: the two options are essentially all of what
the model was going to say, before *and* after. This is the least tail-bound forced-choice readout in
the sprint.

### The arm is LIVE, so "preserved" is not vacuous

A no-op hook preserves binding trivially (C-20). It is not one here:

* **18/18 rows changed** — zero bit-identical readouts between arms
* median |Δ logp_concept| **0.1111**, max **13.5200**
* the mask covered a median of **80.5 demo positions**, `attn_implementation: eager`,
  `knockout_scope: demo_processing_only`

*(`frac_rows_decode_live: 0.0` in the liveness block is expected and not a failure: this is a
`--no-generate` run, so there is no decode phase to edit. The prefill edit is the intervention, and
the 18/18 readout divergence is what evidences it.)*

### ⚠ What this result is NOT — the limits travel with it

1. **n=18 of a possible 40, and the missing rows are the LONG ones.** The baseline arm OOM'd 22 of
   40 rows. Prompts that succeeded are **200–255 tokens**; every prompt **262–325 tokens failed** —
   a razor-sharp cliff. The estimate is therefore on the **short half** of the bank.
2. **Underpowered.** MDE: **≥6** same-direction discordant pairs are needed for p<0.05 and only **5**
   pairs are discordant at all. A degradation affecting fewer than about a third of rows is
   undetectable here. **p=1.0000 is "no evidence of degradation", NOT "evidence of no degradation".**
3. **Dose 8 contributes 2 rows** (16 of the 18 are `n_ex=4`), so this is effectively a single-dose
   result.
4. It is **one bank on this model**, and it is not pre-registered.

### An unexplained asymmetry, recorded rather than explained away

The **baseline** arm OOM'd 22/40 **twice, reproducibly, on two different nodes** (n-802 and n-803),
while the **knockout** arm on the same node completed **40/40 with zero failures**. The intervened
arm does strictly more work, so this is backwards. Ruled out: node identity (reproduced on both),
GPU contention (`mem_get_info` reports **44.11 GiB free of 44.53** before load, i.e. the GPU is
exclusively ours), sequence length as such (the prompts are only **200–325 tokens**; eager attention
at S=325 is ~8 MB), fragmentation (an `empty_cache()` + one-retry path changed nothing), and the
discarded-logits hypothesis (`logits_to_keep=1` changed nothing). **I do not have an explanation**,
and a 12 MiB allocation failing on a 44 GiB card with a 30 GiB model remains unaccounted for. It is
recorded as open rather than papered over, because it is the reason limit (1) exists.

**This does not touch the Phase 7 gate, which remains CLOSED. Phase 8 must not be built.**

---

## §5.18.1 — ⛔ CORRECTION to §5.18: the installation screen was carried over as a RATE, and applied to a population that should have been refused

A peer session audited §5.18 against two corrections of its own. **Both land, and the finding
survives both.** Recording them here because one of them is the C-33 error recurring in a new
disguise.

### Error 1 — encoding a threshold as a rate IS the carry-over C-33 forbade

§5.16 fixed an earlier screen that had no threshold at all by setting **≥32/48 = 0.667**. I then
applied **0.667** at **n=18**. But C-33's correction was precisely that *the threshold moves with n
and must be recomputed, not carried over* — and **a rate is the carry-over form**. Storing 0.667
and multiplying by n is exactly the mistake, wearing a percentage.

Recomputed per n (exact two-sided binomial against chance, the convention that **reproduces §5.16's
own 32/48**, which is how I confirmed it is the right one — my first check used a one-sided test and
gave 31/48, disagreeing with the published screen):

| n | critical_k | implied rate |
|---|---|---|
| 18 | **14** | 0.778 |
| 40 | **27** | 0.675 |
| 48 | 32 | 0.667 |

**The rate screen is one row too permissive at n=18**: it admits **13/18** (two-sided p=0.0963,
NOT established) while the correct critical value is 14. My baseline was 14/18 (p=0.0309), so **the
sentence I wrote happened to be true** — but it was true by luck, and the same screen would have
passed 13/18 next time.

### Error 2 — the sentence was a one-sample fraction on a population my own §5.17 says is unusable

`q9A_lpQ14B_fc_...` has `option_mass_gate: PASS` and **18 of 40 rows, n_failed=22**. The peer's
`mapping_installation_verdict.py` **refuses it outright** — run against it, it prints
`REFUSING qwen3_baseline: 22 rows failed to generate.` — and that guard is right for the reason
**I documented in §5.17 myself**: gate PASS over a silently attrited population is the exact case,
and the 200–255 vs 262–325 token cliff is the length-correlation that makes the survivors
non-random. I flagged the attrition as a limit and then quoted a one-sample statistic off it anyway.

### What changes and what does not

| claim | status |
|---|---|
| **paired** binding contrast 14/18 → 15/18, 3 up / 2 down, p=1.0000 | **STANDS** |
| knockout installs on its **complete** 40 rows: 30/40, p=0.00222, crit=27 | **STANDS** — zero attrition |
| ASR half 11/80 → 1/80 | **STANDS** — untouched |
| "the baseline clears the ≥0.667 screen at 0.778" | **WITHDRAWN** |

**The pairing is not affected by the attrition.** Pairing on the 18 ids measured by *both* arms
controls for *which* rows survived — a biased subset is still a valid pairing, just a narrower
population, which limits (1)–(3) already state. What the attrition invalidates is a **one-sample
fraction**, and that is the one thing I quoted from it. The "mapping is not destroyed" half never
needed it: the knockout arm's complete 40 rows carry it alone.

**§5.18's conclusion is unchanged: on Qwen3-14B the scoped knockout removes the attack and leaves
binding intact.** One supporting sentence was withdrawn; no headline moved.

*(Method note, and the reason this correction is cheap: the peer's tool recomputes `critical_k` per
n and refuses attrited or non-finite populations. I am using it rather than re-deriving the screen —
which is what I should have done instead of applying a remembered rate. Their tool gained the
non-finite check from V-54's NaN finding, and V-54's finding is why it no longer trusts
`option_mass_gate`; this correction is the return leg of that exchange.)*

---

## §5.19 — The OOM is SOLVED, it was never about memory pressure, and §5.18 now stands on a complete n=40 matched-batch population

§5.18 rested on 18 of 40 rows because the baseline arm OOM'd, and §5.18 recorded that as unexplained.
It is now explained, fixed, and the result is re-measured on the full population. **The conclusion
does not change; the evidence for it does.**

### Ruling out the plausible causes, including my own two

A probe ran the exact 40 rows through a bare forward, **shortest-first and longest-first**, on the
same hardware. Both orders: **40/40, zero OOM, memory flat** — `alloc 27.52 GiB`, `free 16.42–16.46
GiB`, unchanged across every row.

* **Not a length cap.** The longest row (S=325) succeeded as **row 0** of the descending probe.
* **Not a leak.** The ascending probe reached S=325 last, after 39 prior forwards, allocation flat
  to 0.01 GiB.
* Also ruled out earlier: node identity (reproduced on n-802 *and* n-803), GPU contention
  (**44.11 GiB free of 44.53** before load), fragmentation (`empty_cache()` + retry changed nothing),
  and discarded logits (`logits_to_keep=1` changed nothing).

**Both of my published hypotheses were wrong**, and the "262-token cliff" of §5.17 was a correlation
inside a single failed run that I named as a mechanism. A peer session had propagated it into its own
ledger on my authority; it has since corrected that. *(Their banks confound dose with length at
**r=0.995**, so no bank of ours can separate the two — which is why the order-varying probe, not more
bank data, was the design that settled it.)*

### The actual cause is one line, and it is a batch size

```python
max_batch=(1 if _wants_knockout else 16)      # score_behavior.py
```

The knockout arm is pinned to **batch 1** by correction C-8 (knockout hooks are batch-1 only). The
baseline is **not**, so it runs `string_option_readout` at **batch 16**, which does:

```python
lp = torch.log_softmax(out.logits.float(), dim=-1)     # on the FULL [B, width, V]
```

At B=16 and V=151936 that is **~3.2 GB in fp32** for the cast and another for the softmax, **growing
linearly with context length**. That is simultaneously why the failure was arm-asymmetric (only the
baseline batches), why it reproduced across nodes, why it tracked length *without length being the
mechanism*, and why a batch-1 probe saw nothing.

**Confirmed, not inferred:** added `--readout-max-batch` and reran the baseline at batch 1 →
**40/40, zero failures, 0 NaN, gate PASS**. The 22 attrited rows come back.

### ⚠ A second finding, which is the more important one: BATCHING IS NOT NUMERICALLY INERT

I wrote in the new flag's help text that this "changes no number beyond float non-associativity."
**That was wrong**, and the same 18 rows measured at batch 16 and batch 1 — differing in nothing
else — show it:

| statistic | value |
|---|---|
| bit-identical rows | **0/18** |
| median \|Δ margin\| | **0.688** (max 1.250) — ⚠ **on the 18 rows the batch-16 arm survived, which are the SHORT rows: see §5.22. This is not a bank-level figure and the max is withdrawn as a window.** |
| verdict flips | **1** (margin +0.2503 → −0.7497) |

The forward runs in **bf16** and only the `log_softmax` is fp32, so batched and unbatched matmuls
take different reduction orders.

**And it is batching, not run-to-run noise.** The control — same arm, same config, **both batch 1**,
different runs — is **40/40 bit-identical, |Δ| exactly 0.000000, 30/40 reproducing exactly**. So
runs are perfectly reproducible at fixed batch size, and **cross-batch comparisons are biased rather
than merely noisy**, which is the worse of the two possibilities.

**Read it as an at-risk count, not a rate.** 1/18 is *not* a 5.6% per-row flip rate: median
\|margin\| is **10.000** against a ~0.7 perturbation, so **17 of 18 rows are untouchable** and
**exactly one row sat inside the perturbation — and it flipped**. The transferable quantity is *how
many rows crowd the boundary*, which scales with a bank's margin distribution, **not with n**.

*(A related trap, avoided: absolute \|Δ\| makes the codeword look **35×** more perturbed than the
concept. Normalised it reverses to **0.36×** — `logp_concept` sits at −0.006, i.e. p≈0.994, so its
absolute deltas are tiny by construction. Neither statistic is decision-relevant; the **margin** is.)*

### §5.18's contrast re-measured: both arms, batch 1, identical code path, complete populations

| | mapped-wins | median option mass | installation verdict (per-n `critical_k`) |
|---|---|---|---|
| `A_baseline` | **29/40** | 0.99985 | p=0.00643, crit=27 → **INSTALLED** |
| `demo_processing_only` | **30/40** | 0.99993 | p=0.00222, crit=27 → **INSTALLED** |

paired: discordant **6 up / 5 down**, exact two-sided **p = 1.0000**. Arm is **LIVE** — 0/40
bit-identical, median \|Δ margin\| between arms **6.44** (max 19.25), roughly **ten times** the
batching artifact.

**§5.18's conclusion is unchanged and now rests on a complete, matched-batch, n=40 population:
on Qwen3-14B the scoped knockout removes the attack (11/80 → 1/80) and leaves binding intact.**

§5.18.1's withdrawal is now **superseded in the correct direction**: the baseline installation claim
can be made again, because it is on a **complete** population and against a **recomputed per-n
`critical_k`=27** rather than a carried-over rate. Limits (1) and (3) of §5.18 — the attrited
short-half population and the effectively-single-dose composition — are **retired**: all 40 rows,
20 per dose. **Limit (2) stands**: MDE is still ≥6 same-direction discordant pairs against 11
discordant, so **p=1.0000 remains "no evidence of degradation", not "evidence of no degradation".**

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

---

## §5.20 — The batch confound audited across the whole corpus: §5 is settled by measurement, and I applied a Qwen3 window to Llama banks

§5.19 established that batching is not numerically inert and that cross-batch comparisons are
**biased, not noisy**. That is a corpus-wide concern, not a Qwen3 one, so this applies it to my own
ledger.

### Every baseline-vs-knockout forced-choice contrast in this sprint spans the batch split

Of **49** completed runs carrying `semantic_forced_choice` rows: **25 on the batch-16 path** (no
intervention) and **24 on batch-1** (knockout, pinned by C-8). Since the split is *exactly* the
baseline/knockout boundary, **every** forced-choice arm contrast is cross-batch by construction.

### The two Phase 5 claims, adversarially bounded

Both Phase 5 knockouts are `legacy_all_query` — **unscoped**. (§5.6's scoped `demo_processing_only`
result is a different contrast; conflating them is easy and I checked rather than assumed.)

Bound method (adopted from the peer's C-36): flip **every** at-risk row against the claim, counting
only those that can hurt — at-risk rows already sitting the wrong way can only help.

| claim | observed | at-risk base / knockout | adversarial |
|---|---|---|---|
| `ticket_bomb` **collapse** (§5.2) | 45/48 → 15/48 (**−30**, p=1.86e-09) | 1 / 10 | **−25** — survives |
| `main` **preserved** (§5) | 42/48 → 41/48 (**−1**, p=1.0000) | 2 / 10 | **−10** — fails |

`main`'s knockout arm sits at median \|margin\| **1.254**, the tightest in the Llama corpus, with
**24 of 48** rows inside even a generous window. And it is a **null** claim, so no bound can rescue
it: *"no degradation" is not established by surviving a worst case.* It had to be measured.

### Measured: the batch confound moves §5's `main` result by ZERO rows

Reran the `main` baseline at batch 1 so both arms share one code path (`p6A_main_b1`, 48/48, gate
PASS), pre-registering that the baseline would move by at most its at-risk count.

| | result |
|---|---|
| baseline batch16 → batch1 | **42/48 → 42/48**, **0 verdict flips** |
| \|Δ margin\| from batching | median **0.100**, max **0.462** |
| pre-registration (ii) (move ≤ 10) | **HELD** — observed 0 |
| matched-batch paired contrast | **42/48 vs 41/48**, up=5 down=6, **p=1.0000** |
| the cross-batch figure it replaces | 42/48 vs 41/48, **identical** |

**§5's result is unchanged to the row.** The adversarial bound failed and the measurement shows
nothing moved — which is exactly what "a failed bound is uninformative" means in practice.

**This removes a confound and creates no power.** MDE is still ≥6 same-direction discordant pairs
against 11 discordant, so p=1.0000 stays **"no evidence of degradation", not "evidence of no
degradation"**. A cleaner comparison must not be allowed to read as a stronger one.

### ⛔ CORRECTION: I applied a Qwen3-derived window to Llama banks

The at-risk counts above were first computed with **W=1.250** — the max \|Δ margin\| measured on
**Qwen3-14B / longpreQ14B**. The Llama perturbation, measured here on the same model and bank the
claims live on, is **max 0.462, median 0.100** — roughly **2.7× smaller**.

**A perturbation scale is a property of a model-and-bank, and I carried one across both.** That is
C-33's error a third time (§5.18.1 was the second): *a threshold that travels without its
population.* I flagged this exact shape to a peer one tick earlier — insisting the scale be
**named** — and then borrowed one myself.

It changes both verdicts, in **opposite directions**:

| claim | adversarial @ W=1.250 (borrowed) | adversarial @ W=0.462 (measured) |
|---|---|---|
| `main` preserved | −26 | **−10** |
| `ticket_bomb` collapse | −8 | **−25** |

So the borrowed window **overstated** exposure on `main` and **understated** the robustness of
`ticket_bomb`: §5.2's collapse survives at −25 against an observed −30, far more decisively than the
−8 I first reported. **Anyone applying my 1.250 to a Llama population is over-estimating their
exposure by roughly 2.7×** — flagged to the peer, who is using that window on Llama banks.

### The reporting form this argues for

Alongside any forced-choice count, report **two numbers**: median \|margin\|, and the count of rows
below **a named perturbation scale**. `14/18` and `15/48` are not comparable; *18 rows at median
margin 10.0* and *32 rows at median margin 1.075* are immediately so. The scale **must be named**,
because the batch artifact (0.462 on Llama, 1.250 on Qwen3) and the judge floor are different
numbers on different quantities.

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

---

## §5.20.1 — Addendum: which arm "main preserved" means, the window is per-BANK too, and why a borrowed window is invisible on the claims people trust most

Three refinements to §5.20, one of which is the most useful thing to come out of this exchange.

### 1. "`main` preserved" is ambiguous across two different contrasts — always name the arm

There are **two** `main` binding contrasts in this sprint and they give different answers:

| contrast | observed | adversarial @ measured W |
|---|---|---|
| baseline vs **`legacy_all_query`** (unscoped) — §5, §5.20 | 42/48 → 41/48 (−1) | **−10** |
| baseline vs **`demo_processing_only`** (scoped) — the peer's C5 main leg | 42/48 → **48/48** (+6, p=0.0265) | **+3** (protected) |

**Not a contradiction — different interventions.** But "main preserved" unqualified will collide in any
deliverable, so every quotation of it must name the arm. This is the §5.6-vs-§5 distinction again:
the **scoped** knockout is the one that preserves binding, and on this contrast mapped-wins actually
*rises*. *(The rise is not claimed: under adversarial batch bias +6 becomes +3, so the direction is
not robust, and the peer is not claiming it either.)*

### 2. The window is per-model **and per-bank** — I fixed the model half and left the bank half

§5.20 corrected a Qwen3 window applied to Llama banks. But I then used **one Llama window (0.462,
measured on `main`) for the `ticket_bomb` bank too** — the same carry-over, one level down. The peer
measured `ticket_bomb`'s directly: **max 0.3202, median 0.1151**.

| bank | measured max \|Δ margin\| |
|---|---|
| `main` (Llama) | 0.4616 |
| `ticket_bomb` (Llama) | 0.3202 |
| `longpreQ14B` (Qwen3-14B) | 1.2499 |

Recomputed with `ticket_bomb`'s own window: at-risk 1/**9** (was 1/10) and adversarial **−25** —
**identical to the published figure**. So §5.20's number survives, and it survives *by luck*: the
error was too small to bite on this bank. That is worth stating plainly, because "the conclusion
didn't change" is not evidence the method was sound.

### 3. ⚠ The asymmetry that makes this error dangerous: it is INVISIBLE on the claims people trust most

The peer's observation, and it generalises well past batching:

**An over-large window is CONSERVATIVE for a positive claim and ANTI-CONSERVATIVE for a null.**

* For an **INSTALLED / effect-present** verdict, inflating the at-risk set only makes the adversarial
  bound harder to pass. Surviving it with a borrowed window means you would also survive with the
  right one. Their published at-risk counts 10/5/12/6 become **4/1/2/0** at the measured scale and
  **every verdict holds either way**.
* For a **null / "no degradation"** claim, an inflated window manufactures exposure that is not there
  — which is exactly what produced §5.20's `−26`, the peer's withdrawn "C5 does not survive its own
  worst case", and my `main` `−10`.

So a borrowed window **cannot** damage the results that carry effects, and can **only** damage the
nulls. The claims most likely to be checked are the ones where the error is harmless, and the claims
where it does harm are the ones a reader is least likely to re-derive. **A robustness check that is
silently one-sided in favour of the headline is worse than none**, and this one was — in both our
ledgers, for two ticks, while both of us were auditing each other.

*(Both legs of the peer's C5 are now measured rather than bounded: `ticket_bomb` at batch 1 gives
45/48 → 45/48, **zero verdict flips**, matching my `main` result exactly — the batch path changes
every row's logits and moves no verdict on either bank. Their C-37 records the same borrowed-window
error against themselves. They also caught a direction bug in their own recomputation — the
collapse half pushed the favourable way — and flagged that the wrong-direction number "looks
impressive, which is exactly when it doesn't get checked.")*

### The rule, final form

Alongside any forced-choice count: **median \|margin\|**, plus the count below a **named, per-model-
and-bank, MEASURED** perturbation scale. The load-bearing word is **measured** — a quoted scale is
portable in exactly the way the discredited rate was.

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

---

## §5.21 — The two-number rule becomes an instrument that REFUSES a borrowed scale

Four corrections in this sprint share one shape — **a scale quoted away from the population it was
measured on**:

| | the carried scale |
|---|---|
| **C-33** | a threshold carried across n as a *rate* |
| **§5.18.1** | the ≥0.667 installation screen applied at n=18, where `critical_k` is 14 |
| **§5.20** | a Qwen3-measured perturbation window applied to Llama banks (**2.7×** too large) |
| **§5.20.1** | then *one* Llama window (`main`, 0.4616) applied to `ticket_bomb` (0.3202, **1.4×**) |

Documentation did not stop instances 3 and 4. **Instance 4 happened one tick after I wrote down
"the scale must be named", in the same analysis that corrected instance 3.** A convention that
fails while you are actively enforcing it on someone else is not a convention worth keeping — so
`src/boombness/margin_exposure.py` makes it a refusal.

### What it emits, and what it will not

Alongside any forced-choice count: **median \|margin\|** and the **count below a named, measured
scale**. It refuses to compute an at-risk count when the window's `(model, bank)` provenance does
not match the run's, refuses to *measure* a window across two populations, and requires a
`scale_name` — because "at-risk = 32" without saying at-risk-of-*what* invites the same carry-over.

Run on the `main` population, it reproduces §5.20's published numbers and then blocks the error:

```
MEASURED scale 'batch16-vs-batch1' on {bank: boombness_prompt_bank.jsonl}:
    max 0.4616  median 0.1000  (0/48 bit-identical, 0 verdict flips)
  p5A_main    42/48  median|margin| 3.423  at-risk  2 (0w/2l)
  p5C_main    41/48  median|margin| 1.254  at-risk 10 (7w/3l)
  REFUSED p5A_ticket_bomb: BORROWED SCALE — window measured on ...bank.jsonl,
          run is ...bank_ticket_bomb.jsonl
  BOUND[preserved] 42/48->41/48 (-1)  adversarial 44->34 (-10)
```

**That refusal is §5.20.1 caught automatically**, by the tool, instead of by a peer reading my
write-up.

The at-risk count is split into **wins and losses**, which a bare count hides: at-risk *losses* can
only move a count **up**, so they help a "preserved" claim and hurt a "collapse" one. The bound
therefore flips only rows that can *damage* the claim — flipping the rest would make it adversarial
against itself. *(A peer hit exactly that bug in their own recomputation, pushing a collapse the
favourable way; their note is worth keeping — the wrong-direction number "looks impressive, which
is exactly when it doesn't get checked.")*

**Guard mutation-tested, 5 mutants, all killed:** disabling the provenance check (2 tests),
comparing model but **ignoring bank** — precisely the §5.20.1 error — (1), dropping the
`scale_name` requirement (1), allowing a window to be measured across populations (1), and making
the bound flip rows that cannot hurt the claim (1). 10 tests.

### An honest blank beats an estimate

A peer applying the same rule now reports **5 of 10** forced-choice arms with the at-risk count as
**UNMEASURED** rather than estimated, having no measured window for those banks. That is the
correct output, and it is what this module produces by construction: it will not manufacture a
number by borrowing one. *Their note — "I'd have quietly filled those with 0.3202 a few ticks ago"
— is the whole argument for making it a refusal rather than a guideline.*

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

### ⛔ The guard's first version would have REFUSED the measurement that caught its own target bug

A peer pointed the module at the exact pair that produced the **0.3202** `ticket_bomb` window — the
measurement that reversed their R-111 and produced their C-37 — and was refused:

```
BorrowedScaleError: cannot MEASURE a window across different populations:
  {'model': 'DEFAULT', ...} vs {'model': 'meta-llama/Llama-3.1-8B-Instruct', ...}
```

**Both runs loaded the identical model.** `_provenance` read `config.args.model`, which is `None`
when `--model` is omitted, so one launch style read `DEFAULT` and the other read the model name.
**That is launch style, not science.**

The failure direction is what matters. **A guard built to prevent the borrowed-window error would
have blocked the measurement that DETECTED it.** An instrument that refuses the work catching its
own target bug is conservative in a direction that *suppresses corrections* — the same
one-sidedness this module warns about for windows, arriving one level up, in the module itself.

The basename half had the **opposite and quieter** failure, which I had not considered: two
**different** banks sharing a basename would have been silently **ACCEPTED**. A false refusal is
loud; a false accept is not.

**Fixed by reading the fields that actually carry identity**, all already recorded in
`metadata.json`: the **resolved** `model`, the resolved **weights commit**, and **`bank_rows_sha16`**
— a hash of the bank's rows, immune to path, basename and launch style alike. Verified against the
real pair: it now measures **max 0.3202, median 0.1151, 0 verdict flips** — reproducing the peer's
number exactly.

**Re-mutation-tested, 5 mutants, all killed:** disabling the provenance check (2 tests), allowing
cross-population measurement (3), ignoring the bank content hash (2), **reading the model from
config as the buggy version did (3)**, and ignoring the weights commit (2). 14 tests.

*(This is the third instance of one shape, which makes it the finding rather than an observation:
an instrument that can only move a result in one direction is safe on one class of claim and
silently unsafe on the other — the borrowed window, this guard, and `kw_refusal`, which anchors
refusal and can never confirm success and so must never be quoted as an ASR substitute.)*

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

---

## §5.22 — DEEP REVIEW: the new instrument had the attrition blind spot it was built next to, and the Qwen3 window I published is measured on a population the perturbation selected

The ~4h review, run against the newest code first, on the principle that new code is where a review
pays. It found one defect and one published number that needs its scope corrected.

### The defect: `margin_exposure` accepted an attrited population

One tick after writing it, `margin_exposure` computed `median |margin|` and an at-risk count over
an arm that had lost **22 of 40 rows** to OOM, reporting **n=18** as though 18 were the population.
Both of its two numbers describe survivors and neither said so.

This is **V-54's failure in a module written to prevent a neighbouring one**, and a peer's
`mapping_installation_verdict` already refuses exactly this. R-105 parity was simply missing.

**Fixed:** `assert_complete()` refuses any run with `n_failed > 0`, wired into *both* entry points.
**Mutation-tested, 4 mutants, all killed:** disabling the refusal (3 tests), tolerating <5 lost rows
(2), checking only the first run of a measured pair (1), and skipping the check in `exposure` (1).
18 tests.

### ⛔ The consequence: the Qwen3 window **1.2499** is measured on a subset the perturbation chose

That attrited pair is exactly where §5.20.1's `longpreQ14B` window came from. So **1.2499 was
measured on the 18 rows where the batch-16 arm survived** — and those are the **short** rows,
because *the perturbation being measured is what killed the long ones*.

**This is the sharpest form of the error this module exists to refuse: not a scale borrowed from
another population, but one borrowed from a biased sample of its own.** And the bias is not
incidental — it is induced by the very quantity under measurement.

Worse, it is **UNMEASURABLE, not merely unmeasured**: no complete batch-16 run on
Qwen3/longpreQ14B exists *or can exist*, because batch 16 is what OOMs. The honest entry is a
refusal, and the tool now produces one.

| bank | window | status |
|---|---|---|
| `main` (Llama) | 0.4616 | **measured**, complete 48/48 both arms |
| `ticket_bomb` (Llama) | 0.3202 | **measured**, complete 48/48 both arms |
| `longpreQ14B` (Qwen3) | ~~1.2499~~ | **WITHDRAWN — unmeasurable**; batch-16 cannot complete this bank |

### What this does and does not touch

**The batching finding itself STANDS, because it does not rest on the Qwen3 numbers.** "Batching is
not numerically inert" was independently established on Llama/`main` with **complete** populations
on both arms: 0/48 bit-identical, max \|Δ margin\| 0.4616. The determinism control (40/40
bit-identical at fixed batch, |Δ| exactly 0) also ran on complete populations.

What is scoped down is the **magnitude** I quoted from Qwen3 — median 0.688, max 1.250, 1 verdict
flip in 18 — which describes *the short half of `longpreQ14B`*, not the bank. It should never have
been tabulated as a bank-level window beside two that were properly measured.

**§5.20's audit is unaffected in its conclusions**, because the fix there was to *stop* using 1.250
on Llama banks; this correction removes the number entirely rather than relocating it. §5.19's and
§5.18's Qwen3 result are likewise untouched — both arms there are complete 40/40 at batch 1.

### The pattern, now at four instances

An instrument that can only fail in one direction is safe on one class of claim and silently unsafe
on the other: the borrowed window (safe on effects, unsafe on nulls), the provenance guard (safe
against false confidence, unsafe against corrections), `kw_refusal` (anchors refusal, never
success), and now **an attrition-blind exposure metric** — safe when a run is complete, silently
wrong when it is not, and *most* wrong precisely when the perturbation causes the attrition.

**A useful standing check for any new instrument: ask which direction it can fail in, and which
class of claim that direction protects.**

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

### §5.22.1 — "bit-identical" was the wrong name, and two correct counts disagreed because of it

A peer's determinism count and mine differed on the same pair — **0/48** against **1/48** — and both
were right. They counted rows identical on **both logps** ("did the computation change"); I counted
rows identical on the **margin** ("could the decision change"). The one discrepant row had
`logp_concept` and `logp_codeword` both shifted by exactly **−9.091e-02** — a **common-mode** shift
that cancels in the difference.

The margin definition is the correct one *for exposure*, since the margin is what the predicate
thresholds. But calling it `bit_identical` reads as *"the row did not change"*, and that row changed
measurably on both logits. **Two ledgers would have appeared to contradict each other over a naming
choice.** Both counts are now emitted under names that state the question:

```
0/48 identical MARGIN, 0 identical on both logps, 0 verdict flips
```

Covered by a test that constructs the common-mode case explicitly, so the distinction cannot
silently collapse back into one number.


---

## §10.1 — BANK DESIGN (§9 next step #2): rows are NOT the binding constraint — clusters are, and the agreed "144 rows" target does not deliver its power

§9's remaining next step is a larger forced-choice probe population. The working prescription — mine
and a peer's — was **"144+ forced-choice rows per condition, widened per-dose cells"**. The
arithmetic below says the row target is right and **the way we planned to reach it is not**.

### The power target reproduces independently

Exact two-sided binomial against chance, computed here rather than carried over:

| n | critical_k | power at a true rate of 0.625 |
|---|---|---|
| 48 | 32 | **0.331** |
| 60 | 39 | **0.399** |
| 144 | 85 | 0.828 |

Reproduces the peer's 0.331 and 0.399 exactly. Two refinements: the exact threshold for power ≥ 0.80
is **n=132**, and the requirement is **steep in effect size** — 90 rows at a true 0.65, but **204**
at 0.60. `ticket_knife`'s observed 0.625 sits in the worst part of that curve.

### Rows are cheaply available — far more than assumed

Forced-choice rows come from `core2x2` = domains × splits × slots, and the current bank uses
**one slot**, giving 12/dose. `core2x2_slot3` would add more but **omits
`semantic_forced_choice` from its query kinds**. The 20-sentence pool admits many more disjoint
slots than that (`_take` starts at `(slot*3) % 20`, verified empirically against `_take` itself,
including the wrapping slot 12):

| dose | pairwise-disjoint slots | fc rows/dose |
|---|---|---|
| 1 | 20 | 240 |
| 2 | 7 | 84 |
| 4 | 4 (0, 2, 4, 12) | 48 |
| 8 | 2 (0, 3) | 24 |
| 16 | 1 | 12 |

Doses {1,2,4,8} therefore supply **396** independent forced-choice rows against the 48 in use —
**no new bank template required**, just slots plus adding the query kind.

### ⛔ But adding slots buys almost nothing, because it adds ROWS and not CLUSTERS

Inference here is **domain-clustered**, and slots multiply rows *within* a domain. Measured ICC of
mapped-wins by domain on complete 48-row arms:

| arm | ICC | deff at m=8 | n_eff from n=48 |
|---|---|---|---|
| `main` baseline | **0.228** | 2.59 | **19** |
| `ticket_bomb` baseline | 0.064 | 1.45 | 33 |
| `main` unscoped knockout | 0.000 | 1.00 | 48 |

Since `n_eff = k·m / (1 + (m−1)·ICC)`, as rows-per-cluster grows this converges to **`k / ICC`** —
a ceiling set by the number of **domains**, not by rows:

| ICC | k=6 | k=10 | k=20 | k=30 |
|---|---|---|---|---|
| 0.05 | 120 | **200** | 400 | 600 |
| 0.10 | 60 | 100 | **200** | 300 |
| 0.228 | **26** | 44 | 88 | 132 |

**At ICC 0.228 and 6 domains the ceiling is ~26 effective rows — so all 396 rows would be worth
about as much as the 48 we already have.** Widening per-dose cells is close to free and close to
useless; the binding constraint is the cluster count.

`DOMAINS` already holds **10** (it grew from 6 on 2026-08-25 for Phase 4B), so 4 unused domains are
available immediately — `warehouse_logistics`, `harbour_dock`, `museum_archive`, `rail_depot` — with
no new prose to write.

### ⚠ The ICC itself is badly determined, and that is the finding

Three arms give **0.228, 0.064, 0.000** — from 6 clusters and 48 rows each. That is far too little
to size a design on, and the three values imply ceilings of 26, 94, and unbounded. **Committing to a
row count now would be sizing a bank against a number we cannot yet estimate**, which is the
carry-over error in a new costume: a quantity used away from the evidence that supports it.

So the recommendation is **staged**, and I am not generating a large bank on the current estimate:

1. **Pilot**: all **10** domains × the disjoint slots at doses {1,2,4,8}, forced-choice added to the
   slot blocks. Purpose is to **measure ICC on 10 clusters**, not to answer any claim.
2. **Size** the final design from that ICC via `k/ICC`, against the exact `critical_k` at the n
   actually used.
3. **Generate** only then — and ship each bank with **its own measured perturbation window**.

### The four design-time checks, with one added

The peer's three, plus the one this analysis forces:

1. **144+** forced-choice rows per condition — necessary, and now known to be **not sufficient**.
2. **Both arms completable** at the batch size intended. *(A bank whose window can only be measured
   on a subset its own perturbation selects has no usable window at all — §5.22.)*
3. **Window measured and shipped with the bank**, per model-and-bank.
4. **NEW: enough CLUSTERS that `k/ICC` clears the target `n_eff`.** A row target met by widening
   cells inside 6 domains satisfies check 1 and fails the power requirement it was written for.

All four are checkable **before a single generation**.

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

---

## §10.2 — §9 next step #2 is BLOCKED, quantified: the forced-choice population cannot reach the target power on the existing domain inventory

A peer answered both questions I raised in §10.1 with measurement (five complete Llama baseline arms
I do not have). **Their conclusion holds and my §10.1 pilot design was wrong.** Their magnitude was
over-severe, and the direction language was backwards — both established here rather than argued.

### Verified independently, against my own banks

* **Nesting confirmed.** For `core2x2` forced choice the 48 rows are 6 domains × 2 splits × 4 doses
  at **one slot**, and demo blocks are strictly **nested**: n=1 ⊂ n=2 ⊂ n=4 ⊂ n=8 (checked
  byte-wise on `city_bridge/dev`). The 8 rows in a domain are nested doses of **one** demonstration
  set.
* **Dose-centring raises ICC**, as they said — `main` 0.228 → **0.286**, `ticket_bomb` 0.064 →
  **0.114**. Raw ICC is an underestimate because the nested dose main effect inflates within-cluster
  variance.

### ⛔ My §10.1 pilot would have measured the wrong quantity — their point, and it is right

Every ICC either of us had was computed on rows **sharing one demonstration set**. That is a
same-demonstration correlation, not the domain correlation a **multi-slot** bank would exhibit. A
pilot varying only domains estimates a number that does not describe the bank being designed.

### But the direction was stated backwards, and the size of the error is measurable

`core2x2_slot3` supplies a second, **disjoint** slot on `semantic_one_word`, so the multi-slot
quantity can be measured **now**:

| ICC (domain), `semantic_one_word`, doses {1,2,4,8} | raw | dose-centred |
|---|---|---|
| slot0 only — **shared** demo set | 0.210 | 0.314 |
| slot3 only — **shared** demo set | 0.289 | 0.395 |
| **both slots — mixed demo sets** | **0.156** | **0.218** |

Cross-slot agreement on matched (domain, split, dose) is **32/48 = 0.667** against **0.514**
expected under independence — correlated, but well below same-slot.

**The one-slot estimate OVER-states the multi-slot ICC (0.31/0.40 → 0.22), so it is *pessimistic*
for the multi-slot design, not optimistic.** Sizing from it over-sizes, which is conservative rather
than dangerous. That matters for the magnitude: **29 domains needed, not the 42–53 the same-slot
figures imply.**

*(Caveat carried: this is measured on `semantic_one_word`, because `core2x2_slot3` carries no
forced-choice rows. It is a proxy for the forced-choice ICC, not the thing itself — which is
precisely why the slot-varying pilot is still required.)*

### The blocker, at the corrected ICC

At the **measured multi-slot dose-centred ICC of 0.218**, `n_eff` is capped at `k/ICC`:

| true rate | n_eff for 80% power | domains needed | feasible at k=10? |
|---|---|---|---|
| 0.625 (`ticket_knife`) | 132 | **29** | no |
| 0.650 | 90 | 20 | no |
| 0.700 | 54 | 12 | **no** (just misses) |
| 0.750 | 30 | 7 | **yes** |
| 0.800 | 24 | 6 | **yes** |

**10 domains give a ceiling of 46 effective rows.** So:

* **`ticket_knife`'s 0.625 is unreachable** — 29 domains against 10, and it stays unreachable no
  matter how many rows or slots are added, because the ceiling is `k/ICC`. This is now a **fourth**
  independent argument for the same verdict, alongside C-31 (not above chance), C-32 (unresolvable
  at any attainable n), and reproducibility.
* Even a true **0.70 just misses** at 12 domains needed.
* Effects at **0.75+ are answerable today** with 7 domains, no new prose.

**So §9 next step #2 is not "generate a bigger bank" — it is blocked on domain inventory, and the
block is quantified: ~19 more domains would have to be authored to resolve a `ticket_knife`-sized
effect.** The honest framing is that the probe can be strengthened for large effects now, and the
small-effect cells cannot be rescued by any amount of generation.

### What I am not doing

Not authoring 19 domains and not generating a bank. Both would commit real cost against an ICC whose
eight-estimate spread (0.000–0.327 raw across structurally identical banks) is **as large as the
quantity**, and — the peer's sharpest point — that spread is **across banks, not across clusters
within a bank**, so more clusters per bank tightens an estimate of a number that changes at the next
bank anyway. **A pilot cannot fix that by getting bigger.**

**One generation-time decision to record before any bank is built:** demo draws are currently
**nested** across doses, so dose rows are not independent even in principle. If dose is to be an
analysable factor rather than a nuisance, the new bank needs **disjoint draws per dose** — and that
is irreversible after generation.

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

---

## §10.3 — CORRECTION to §10.2: my "29 domains" is a ONE-BANK number, and the both-ends argument that replaced it does not hold either

Two corrections, one to me and one to the peer who caught mine.

### 1. My corrected ICC inherits exactly the instability I said killed the pilot

§10.2 replaced 42–53 domains with **29**, from a multi-slot ICC of 0.218. That figure is measured on
**one bank**. Run identically on `ticket_bomb` it is **zero**:

| bank (`semantic_one_word`, both slots, doses {1,2,4,8}) | ICC raw | dose-centred | domain win-rates | between-domain sd |
|---|---|---|---|---|
| `main` | 0.156 | **0.218** | 0.312 – 0.875 | **0.209** |
| `ticket_bomb` | **0.000** | **0.000** | 0.562 – 0.750 | **0.078** |

Same six domains, same prose, same model, **different codeword–concept pair** — a **2.7×**
difference in between-domain spread. Not saturation: `ticket_bomb` has 64/96 wins with slots at
27/48 and 37/48, so there is ample variance.

**Domain clustering is not a property of the bank template. It is a property of how a particular
concept interacts with those domains.** So §10.2's 29 is one draw from the same across-bank spread
that I had *just* accepted as fatal to the pilot — and I applied that argument to the peer's design
and not to my own measurement one section later. The honest form is a **range: from no clustering
penalty at all to ~53 domains.**

*(A mechanism the peer proposed and then refuted rather than shipped: `ticket_bomb`'s slots differ
by 0.208 in win rate, so a slot main effect might deflate its ICC as the dose effect did.
Slot-centring moves it 0.000 → 0.000. Plausible, tested, wrong.)*

### 2. But the both-ends argument that replaces it is wrong, because it uses the OLD row ceiling

The proposed rescue was that `ticket_knife` is unreachable under *both* regimes — cluster-limited at
high ICC, and row-limited at ICC 0 where C-32's 60-row ceiling binds against the 132 needed. **A
conclusion that survives at both ends of an unpinnable quantity would indeed be worth more than one
that needs it. This one does not survive, because 60 is the SINGLE-slot ceiling:**

| bank structure | doses {1,2,4,8,16} | doses {1,2,4,8} |
|---|---|---|
| single-slot (C-32's basis) | **60** | 48 |
| **multi-slot** (the design under discussion) | **408** | **396** |

At **ICC 0** there is no clustering penalty, so `n_eff = n`, and **396 rows clears 132 comfortably**.
The row ceiling only binds on the bank we already have — not on the one being designed, whose entire
point is the extra slots.

So the position is:

* **ICC high (`main`-like, 0.218):** ceiling `k/ICC` = 46 at 10 domains → **not reachable**, and no
  number of rows fixes it.
* **ICC ~0 (`ticket_bomb`-like):** `n_eff = n` → **reachable**, 396 rows against 132 needed.

**`ticket_knife`'s resolvability therefore depends on `ticket_knife`'s own ICC, which nobody has
measured.** It is not settled at both ends. The three existing arguments for its verdict — C-31
(not above chance), C-32 (unresolvable at attainable n *on the current bank*), and reproducibility —
stand on their own; what does **not** stand is the new fourth argument I recorded in §10.2, and it is
withdrawn.

### What actually follows

**The decisive measurement is cheap and specific: `ticket_knife`'s own multi-slot ICC.** It is one
number, it decides whether a multi-slot `ticket_knife` bank can answer at all, and it can be taken
from `semantic_one_word` on the existing two slots exactly as the two rows above were — no
generation required.

Also amended, per the peer and per the same rule as the window: **"7 domains suffices for 0.75
effects" is a `main`-bank statement.** ICC is bank-dependent, so the threshold must be re-measured
per bank rather than carried. That is §5.21's rule arriving in the design arithmetic, and it is the
fifth instance of one shape.

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

### §10.3.1 — Measured: `ticket_knife`'s OWN multi-slot ICC, which settles it on the right basis

§10.3 said the decisive measurement was `ticket_knife`'s own ICC, that it required no generation, and
that the fourth argument was withdrawn until someone took it. Taken — `p5_ticket_knife_...` carries
both slots on `semantic_one_word`:

| bank | multi-slot ICC (raw / dose-centred) | between-domain sd | domains for n_eff=132 |
|---|---|---|---|
| `main` | 0.156 / 0.218 | 0.209 | 29 |
| `ticket_bomb` | 0.000 / 0.000 | 0.078 | none — no penalty |
| **`ticket_knife`** | **0.162 / 0.190** | **0.189** | **26** |

**`ticket_knife` is `main`-like, not `ticket_bomb`-like.** At ICC 0.190 the ceiling with 10 domains
is **53 effective rows** against the **132** needed, so it is unreachable — and unreachable *however
many rows or slots are added*, because `k/ICC` does not depend on the row count.

**The fourth argument is restored, on a sound basis.** §10.2 asserted it from `main`'s ICC applied to
`ticket_knife` — a carried scale, the same error a fifth time. §10.3 withdrew it. It now rests on
`ticket_knife`'s **own** measurement, which is what it should have rested on from the start. The
difference matters precisely because `ticket_bomb` shows the number can be **zero** on the same
domains and prose: the conclusion could not have been assumed.

*(Two caveats travel with it: this is `semantic_one_word` as a proxy, since `core2x2_slot3` carries
no forced-choice rows; and `ticket_knife`'s one-word win rate is 25/96, so it is a low-scoring
population — which is consistent with C-31's "not above chance" and is the reason the cell is
contested in the first place.)*

**Net effect on the design: `main`-like and `ticket_knife`-like banks are cluster-limited and cannot
be rescued by generation; `ticket_bomb`-like banks have no clustering penalty and could reach 132
with the multi-slot rows that already exist. The ICC must be measured per bank before any bank is
sized — never carried, in either direction.**


---

## §10.4 — What domain clustering actually tracks: NOT the codeword, and a suggestive-but-unestablished link to how well the concept installs

§10.3.1 forced ICC to be measured per bank. That makes "what determines ICC" a real question rather
than a nuisance, and it is answerable from **existing artifacts** — six complete `A_baseline` runs
carry both slots on `semantic_one_word`, giving a codeword × concept design at no GPU cost.

| bank | codeword \| concept | wins/96 | ICC raw | ICC dose-centred | between-domain sd |
|---|---|---|---|---|---|
| `main` | carrot \| bomb | 56 | 0.156 | **0.218** | 0.209 |
| `ticket_bomb` | ticket \| bomb | 64 | 0.000 | **0.000** | 0.078 |
| `basket_gun` | basket \| gun | 36 | 0.371 | **0.381** | 0.293 |
| `basket_bomb` | basket \| bomb | 60 | 0.000 | **0.000** | 0.062 |
| `ticket_knife` | ticket \| knife | 25 | 0.162 | **0.190** | 0.189 |
| `window_bomb` | window \| bomb | 45 | 0.004 | **0.049** | 0.118 |

### It is definitively NOT a codeword property

The design contains two within-codeword contrasts, and both are large:

* **`basket`**: 0.381 with `gun`, **0.000** with `bomb`
* **`ticket`**: 0.190 with `knife`, **0.000** with `bomb`

Same codeword, same six domains, same prose, same model. **Whatever sets the clustering, it is not
the codeword.** By concept, `bomb` is near zero on three of four banks (0.000, 0.000, 0.049) with
`carrot|bomb` at 0.218 the exception, while `gun` (0.381) and `knife` (0.190) are high.

### The obvious hypothesis is suggestive and NOT established

The pattern invites a mechanism, and it connects to §5's finding that **the `gun` concept never
installs**: if a concept installs everywhere, domains have nothing to differentiate; if it installs
weakly, *whether* it installs becomes domain-dependent and clustering appears.

Tested directly:

* Spearman(win rate, ICC) = **−0.696**
* exact permutation two-sided **p = 0.1444** (104/720)

**Not significant at n=6 banks, so it is recorded as a hypothesis and not a finding.** The direction
is what the mechanism predicts and the magnitude is large, which is exactly the situation in which
this sprint has repeatedly been wrong — a plausible mechanism with a suggestive number is how the
"262-token cliff" got published (§5.19) and how a peer's slot-effect explanation for `ticket_bomb`
died (§10.3). It needs roughly **13 banks** to test at 80% power against ρ≈0.7; six exist.

### Why it would matter if it held

ICC currently has to be **measured** per bank before that bank can be sized — a real cost, and the
thing that blocks §9 next step #2. The win rate is far cheaper. **If the relationship held, a bank's
clustering penalty could be predicted from a quantity every run already reports**, turning a
blocking measurement into a free one. That is worth testing properly; it is not worth assuming, and
sizing a bank on ρ = −0.696 at p = 0.14 would be the same error this sprint has now made five times
in different costumes.

**Practical rule, unchanged: measure ICC on the bank you are about to size. It cannot yet be
predicted, and it is not inherited from the codeword.**

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

---

## §7.5 — A peer's audit found a gap class in MY ledger too: four corrections written up and never propagated

A peer found that two of their corrections existed in their plan file and never reached their
deliverable, both during fast exchanges, and both caught only by a **by-count audit**. Their point
is the important part: **the gap is invisible from inside the writing session, because the entry
demonstrably exists where you just wrote it.** They suggested running the same count here.

Ran it. **Four claim-bearing results were in the plan and absent from the claim ledger:**

| section | result that never propagated |
|---|---|
| §5.20 | the corpus batch-split audit, and that `main` moves by **zero rows** under it |
| §5.20.1 | the borrowed-window correction that **every adversarial bound depends on** |
| §10.3.1 | the per-bank ICC measurements |
| §10.4 | domain clustering is not a codeword property |

All four are now on the ledger — the first two on both entry 5 (retrieval knockout) and entry 12
(binding survival), which are the claims whose arms span the batch split; the ICC on entry 12; and
§10.4 as a **new entry 15**, since it is a finding about the phenomenon rather than a change to an
existing claim.

**The older corrections were clean.** Checking every earlier correction section — §0.2.3, §0.2.5,
§4.1, §5.2, §5.4, §5.7, §5.9, §5.13 — all eight had propagated. **The gap is confined to the recent
fast-exchange sections, exactly as the peer predicted.**

### Made repeatable, because a count nobody runs is not a control

`src/boombness/ledger_propagation_check.py`, wired into `check_all.py` as a **seventh** guard.

**It does not decide which corrections matter.** Several are method or instrument fixes with no
ledger consequence, and a guard demanding a trace for all of them would fail constantly and be
switched off. Instead a correction section must either leave a **trace** in the ledger or be named
in `METHOD_ONLY` **with a reason**. A new correction section fails until someone classifies it —
**silence is the only thing disallowed**, which is the actual failure mode.

Running it immediately found **six** further unclassified sections from earlier in the sprint; all
six turned out to have propagated correctly and are now registered with their trace tokens.

### ⚠ My first mutation test of this guard was worthless, and it is worth saying why

I mutated the guard against the repository's **passing** state — four mutants "survived", and I
briefly read that as the guard being broken. It was the *test* that was broken: with no violation
present there was nothing for a mutation to stop detecting, so every mutant trivially passes.

Redone against a **deliberately introduced** violation (an unclassified `§9.99` correction), the
guard fails correctly, and disabling any of its three detection paths — recording unclassified
sections, the `METHOD_ONLY` exemption, the heading-marker scan — makes that real violation
invisible. **A mutation test run against an all-green input measures nothing**, which is the
sharper form of the sprint's own "never rely on a green test unless mutation-tested that it can
fail". Eight pytest tests now pin the property, including one that constructs the violation.

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

---

## §7.6 — Three defects found by looking at the guard I had just shipped, one of them a duplicate-section-number collision it was silently mis-keyed on

### 1. THREE SECTION NUMBERS WERE DUPLICATED, and my own guard was keyed on the ambiguity

The bank-design sections appended as **§6.1, §6.2, §6.3** collided with the **existing Phase 6**
sections of the same numbers:

| id | existing | mine |
|---|---|---|
| §6.1 | PHASE 6, representational half | BANK DESIGN |
| §6.2 | PHASE 6, behavioural half | §9 next step #2 is BLOCKED |
| §6.3 | THE MEDIATION TEST | CORRECTION to §6.2 |

Not cosmetic: `ledger_propagation_check` keys `METHOD_ONLY` and `TRACE_TOKENS` **by section id**, so
three of its entries were ambiguous between a Phase 6 section and a bank-design one. Renumbered to
**§10.1–§10.4** with cross-references updated, and the `### §5.18 re-measured` sub-heading
disambiguated. *(§0.13/§0.13a and §4.1/§4.1a are suffixed variants, not collisions.)*

**The guard then failed on its own tables** — they still named §6.x — which is the guard doing
exactly its job on its author.

*(My first duplicate-detection command was also wrong: `grep -o` emits **every** `§` match on a
line, so a heading like "§5.18.1 — CORRECTION to §5.18" counted twice and produced six false
collisions. Extracting only the **leading** id gives the three real ones.)*

### 2. ⛔ The guard had a DEGENERATE PASS: an empty scan reported success

A peer guarded this on their version and I had not. If the marker convention changes, a path
breaks, or the regex stops matching, `secs` is empty, every loop is skipped, and **the guard reports
success having checked nothing**:

```
[ledger-prop] 0 correction sections; 5 classified method-only; -5 with a required ledger trace
[ledger-prop] every correction section is either traced to the ledger or classified   ← exit 0
```

**The tell was already printed**: `-5 with a required ledger trace`, a negative count nobody read.
Fixed with a `MIN_EXPECTED = 10` floor — a real drop means the *scanner* broke, not that the
corrections vanished — and the nonsensical arithmetic replaced with a direct count. Two tests pin
it, one asserting the empty scan is refused and one asserting the shipped floor is not zero.

**This is the green-on-green failure one level up from §7.5's mutation-test mistake.** There, a
mutation test against an all-green input measured nothing. Here, a guard against an all-empty input
measured nothing. Same shape, and I made it the same day I wrote up the lesson.

### 3. The peer's version of this guard found a class mine structurally cannot

Their strict variant failed on first run and surfaced **seven** corrections (C-2, C-3, C-4, C-7,
C-10, C-15, C-17) in **neither** deliverable — all outside the C-19…C-40 range their two by-hand
audits had assumed. Their conclusion is the strongest argument in this exchange for automating a
check you are already performing by hand: **the automation does not inherit your assumption about
where to look.** None was a live error, but C-15 is why checking beat assuming — it corrects an
overreach whose live descendant would otherwise have rested on a comparison one of their own
corrections had ruled out.

Also worth recording against my guard's green: **their `check_all` went 6/7 → 7/7 on my guard, and
that told them nothing about their ledger**, because it reads *my* two files. Taking that green as
coverage would have been the same error again.

**Both gap sets are confined entirely to fast-exchange sections, on two independent corpora — which
makes it a property of the working mode rather than of either session.**

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

---

## §10.5 — The seventh bank lands, and pooling it surfaced that THREE of the seven ICC estimates come from readouts their own gate marks NOT REPORTABLE

A peer generated the seventh bank (`window_knife`, 192/192, `n_failed=0`) to complete the third
within-codeword contrast, pre-registering that one extra point could not make the win-rate/ICC
relationship significant. **It could not, and it did not.** But pooling it required checking the
readout, and that check found something worse than the correlation result.

### ⛔ Three of seven `semantic_one_word` readouts are below the option-mass floor

| bank | median option mass | reportable | ICC (dose-centred) |
|---|---|---|---|
| `ticket_bomb` | 0.181 | **yes** | 0.000 |
| `basket_bomb` | 0.103 | **yes** | 0.000 |
| `basket_gun` | 0.081 | **yes** | 0.381 |
| `ticket_knife` | 0.077 | **yes** | 0.190 |
| `main` | **0.043** | **NO** | **0.218** |
| `window_bomb` | **0.040** | **NO** | 0.049 |
| `window_knife` | **0.019** | **NO** | 0.115 |

**`main` is one of them, and `main`'s 0.218 is the value §10.2's blocker table used as its
representative ICC.** A readout below the floor decides its forced choice inside a tail, so the
mapped-wins it produces — and therefore the ICC computed from them — may be ordering noise. This is
§0.16's tail-gate lesson arriving in an analysis I built two sections after quoting it.

**What survives:** `ticket_knife`'s **0.190 is on a REPORTABLE readout (0.077)**, so §10.3.1's
conclusion — `ticket_knife` is cluster-limited and unreachable at 10 domains — **stands on a sound
measurement**. That is the load-bearing claim of the whole design analysis, and it is the one that
happens not to depend on a tail-bound readout.

**What is scoped down:** §10.2's table quoted **ICC 0.218** as the working value. It should be read
as *`main`'s* number, from a readout that is not reportable. The reportable banks span **0.000 to
0.381**, so the honest working range is unchanged from §10.3's "no clustering penalty to ~53
domains" — the range was always the honest form, and this removes the temptation to collapse it to a
point.

### The seventh bank, against its pre-registration

`window|knife` = **0.115** against `window|bomb` = **0.049**. The peer pre-registered that a high
value would make it "three for three on concept-not-codeword" and a near-zero value would weaken the
concept story. It is **neither** — same direction as the other two contrasts (knife above bomb) but
a **2.3×** ratio where `basket` and `ticket` both showed bomb at exactly 0.000. Recorded as
**directionally consistent and materially weaker**, not as a third confirmation.

*(Concept-wise the ordering does hold on both codewords that carry two concepts: `ticket` 0.190
knife vs 0.000 bomb, `window` 0.115 knife vs 0.049 bomb. Two for two on `knife > bomb`. Both
`window` rows are non-reportable, so that contrast is the weakest evidence in the table.)*

### The correlation, and the pre-registration holding

| population | n | Spearman(win rate, ICC) | exact p |
|---|---|---|---|
| all banks | 7 | **−0.559** | 0.2056 |
| reportable readouts only | 4 | **−0.738** | 0.3333 |

Adding the seventh point moved ρ from −0.696 **away** from significance, exactly as pre-registered.
**Not established on any subset**, and the reportable-only subset is too small to test at all.
§10.4's verdict is unchanged: a hypothesis, needing ~13 banks, and not a finding.

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

---

## §10.6 — Rebuilt on REPORTABLE readouts: the codeword result strengthens, and the load-bearing row is now sound on BOTH readouts

§10.5 found three of seven `semantic_one_word` readouts below the option-mass floor. A peer rebuilt
the table on **`semantic_forced_choice`**, where all seven are comfortably reportable. **Every number
reproduces exactly on my copy**, including the correlation and its null simulation.

| bank | cw \| cc | wins | option mass | ICC (dose-centred) |
|---|---|---|---|---|
| `main` | carrot \| bomb | 42/48 | 0.5414 | 0.286 |
| `ticket_bomb` | ticket \| bomb | 45/48 | 0.5534 | 0.114 |
| `basket_gun` | basket \| gun | 19/48 | 0.3869 | **0.755** |
| `basket_bomb` | basket \| bomb | 42/48 | 0.6817 | 0.160 |
| `ticket_knife` | ticket \| knife | 30/48 | **0.7685** | 0.320 |
| `window_bomb` | window \| bomb | 40/48 | 0.5156 | 0.158 |
| `window_knife` | window \| knife | 39/48 | **0.7783** | 0.400 |

### §10.4's codeword result STRENGTHENS, and loses its degenerate figures

Three-for-three within-codeword, **with no zeros on either side**:

| codeword | bomb | other concept | ratio |
|---|---|---|---|
| `basket` | 0.160 | gun **0.755** | 4.7× |
| `ticket` | 0.114 | knife **0.320** | 2.8× |
| `window` | 0.158 | knife **0.400** | 2.5× |

On `one_word` three of those `bomb` values were exactly **0.000** — a degenerate figure — and two of
the three contrasts were non-reportable on both sides. **The finding is the same and the evidence is
now much better**, and §10.5's "materially weaker third contrast" is superseded: on reportable data
`window` (2.5×) sits alongside `ticket` (2.8×).

### ⚠ But the whole reportable table is SINGLE-slot, and that is a different estimand

`core2x2_slot3` carries **no forced-choice rows** — verified: forced choice is 48 rows from
`core2x2` alone, while `one_word` is 96 across both blocks. **So every figure above is a
same-demonstration correlation**, which §10.3 measured as *over-stating* the multi-slot quantity
(`main`: single-slot 0.314 → multi-slot 0.218, a 1.4× gap).

The design sizing needs the **multi-slot** ICC, because the bank under design has multiple slots.
So these numbers **over-size**, which is conservative rather than dangerous — but they are not the
quantity, and `one_word` remains the only readout that can measure it.

### The load-bearing row is now sound on BOTH readouts, which is better than either of us had

`ticket_knife` is the ideal case: **reportable on both**, and both say unreachable.

| readout | mass | reportable | ICC | domains for n_eff=132 |
|---|---|---|---|---|
| `one_word`, **multi-slot** (the design estimand) | 0.077 | yes | 0.190 | 26 |
| `forced_choice`, single-slot (conservative) | 0.7685 | yes | 0.320 | 43 |

**26 and 43, against 10 available.** Adopting the peer's recommendation with the estimand named:
the blocker row now cites the reportable forced-choice figure as the conservative bound and the
multi-slot figure as the design quantity, and **§10.3.1's verdict holds on both** — which removes
§10.5's "three of seven are non-reportable" caveat from the row that carries the conclusion.

### The correlation: much stronger, verified not to be an artifact, and still not claimed

ρ = **−0.847**, exact permutation **p = 0.0246** (n=7, all 5040 permutations) — against `one_word`'s
−0.559, p=0.206.

The peer tested whether it is mechanical before reporting it, which is the right order. ICC and win
rate come from the same binary outcomes and ICC attenuates near the ceiling, so a null simulation
with **zero** true clustering was run across the observed win rates. **Reproduced here:** mean null
ICC runs 0.0316 → 0.0224 from p=0.396 to p=0.938, a range of **0.0108** against an observed spread
of **0.641** — the real spread is **59×** the artifact. Real attenuation, far too small to explain
it.

**Neither session is claiming it, and I agree with that.** n=7, one test, and a **post-hoc** readout
choice — the motivation arrived before the result was read, so it is not selected for its answer,
but it is not what was pre-registered. My own standard is ~13 banks for 80% power at ρ≈0.7, and
**p=0.0246 on a secondary analysis is a reason to keep measuring, not to start sizing from win
rate**.

**The practical rule is unchanged: measure ICC on the bank you are about to size.**

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

### §10.6.1 — No correction factor bridges the two tables, and the bank makes that unfixable

§10.6 recorded that the reportable (forced-choice) table is single-slot and the multi-slot table
(`one_word`) is the one that keeps failing the mass floor. A peer verified that split **from the
bank source**, and it is structural, not a sampling accident:

* `semantic_forced_choice` exists in **`core2x2` only** — 72 rows
* `semantic_one_word` spans `core2x2` 72, `core2x2_slot3` 48, `role_style` 180, `strength` 48,
  `consistency` 36, `position` 12

**So the reportable readout is structurally incapable of measuring the multi-slot quantity, and the
readout that can measure it is the one that keeps failing the gate.** Neither session chose that; it
is how the bank was generated, and it is a generation-time property.

### The conservative-direction claim holds — on reportable rows only

Single-slot vs multi-slot ICC on every bank carrying both (dose-centred, `one_word`):

| bank | slot0 | multi | ratio | multi-slot mass | reportable |
|---|---|---|---|---|---|
| `ticket_bomb` | 0.248 | **0.000** | ∞ | 0.1801 | yes |
| `basket_gun` | 0.472 | 0.381 | 1.24 | 0.0808 | yes |
| `basket_bomb` | 0.000 | 0.000 | — | 0.1027 | yes |
| `ticket_knife` | 0.377 | 0.190 | 1.98 | 0.0774 | yes |
| `main` | 0.316 | 0.218 | 1.45 | 0.0404 | **no** |
| `window_knife` | 0.154 | 0.115 | 1.34 | 0.0193 | **no** |
| `window_bomb` | **0.000** | **0.049** | 0.00 | 0.0404 | **no** |

Single-slot ≥ multi-slot on **all four reportable rows**, so §10.6's conservatism argument stands —
and stands *specifically on reportable data*, not in general. There are two counterexamples where
single-slot **under**-states, `window_bomb` going 0.000 → 0.049 the wrong way, but both are below
the mass floor and so are not evidence against it. *(`basket_bomb` is 0.000 → 0.000, a degenerate
row that is neither support nor counterexample; it was absent from the peer's table and is included
here for completeness.)*

### ⛔ But the MAGNITUDE is not translatable, which is the stronger point

Among reportable rows the ratios are **1.24, 1.98, and infinity**. **No constant factor converts
one table into the other**, and my "1.4× from `main`" is a single draw from a spread that includes a
case collapsing to exactly zero.

So §10.6's "different estimands, neither substitutes for the other" needs its stronger form: **no
correction bridges them either.** That matters for anyone who later finds the reportable table and
tries to *adjust* it rather than re-measure — the adjustment does not exist.

**Consequence for the 13-bank pre-registration: it must fix the READOUT and the SLOT STRUCTURE up
front.** Both move the number, and this tick establishes that neither can be corrected for
afterwards.


---

## §10.7 — Enumerated the ICC population by code: my bank count is right, and the extra row it surfaces must be refused on ATTRITION, not on model

A peer found their six-bank table was hand-listed and missed rows, re-derived it by enumerating the
artifact tree, and got eight. **Their lesson applies to me identically — my table was hand-listed
too** — so I enumerated rather than assume mine was complete.

**Enumeration finds 8 runs and 7 distinct banks.** `ticket_bomb` appears twice: `p5A_ticket_bomb`
and the peer's batch-1 rerun `c5A_tb_b1` of the *same* bank. So no bank was missing from §10.4's
table, but I only know that because the enumeration was run.

### The eighth row is `longpreQ14B`, and it is the attrited run

Their eighth entry is `longpreQ14B` (0.107 → 0.042). It does not appear in my enumeration because I
filter attrited runs, and **the only `longpreQ14B` run carrying `one_word` is `q5A_lpQ14B`, which
lost 92 of 160 rows to OOM** — leaving 18 and 19 survivors from cells of 48.

**So the correct reason to exclude it is not that it is Qwen3.** It is the exact population §5.22
established must be refused: the survivors are the **short** rows *selected by the very perturbation
under study*. `margin_exposure.assert_complete()` refuses it on sight, which is what that guard was
added for:

```
REFUSED: q5A_lpQ14B — ATTRITED population, 92 rows failed
```

The peer's instinct to flag the silent exclusion was right, and their stated ground ("it's Qwen3, so
excluding it from a Llama table is defensible") is the weaker of the two available. **On attrition
grounds it is not a defensible exclusion, it is a required one** — and this is the one bank whose
perturbation window was already withdrawn for the same reason, so an unnoticed *inclusion* would
have been actively wrong.

### The generalisable rule, which is theirs

**When a table's rows are a POPULATION rather than a SELECTION, enumerate them by code.** A hand
list cannot be audited against what it should cover, because the omission is invisible from inside
the list — the same way a range assumption is invisible from inside the range. Their two failures
today (a ledger audit over a self-chosen `C-19…C-40` range that missed seven; a six-row hand list
that missed two) are instances of one sentence, and my §10.4 table was a third waiting to happen.

**Nothing concluded moves.** Direction still holds on every reportable row; magnitude is still
untranslatable at 1.24, 1.98 and ∞ among the non-degenerate reportable ones.


---

## §11 — §9 next step #3, a judge-independent success measure: the deterministic anchor is SOUND and structurally CANNOT cover the region the claims live in

Every concept-level result in this sprint is entangled with StrongREJECT's scoring, and §9 records
"find a judge-independent success measure" as an open next step. A peer proposed `kw_refusal` — the
deterministic keyword refusal test, measured at **0/160 flips on byte-identical text** against the
LLM judge's ~5% — with the caveat that it measures **refusal, not success**, and so anchors one side
only. This tests how far that gets.

*(Population enumerated by code rather than hand-listed, per §10.7.)*

### The anchor is sound: it essentially never contradicts the judge

Pooled over **598 judged arms, 217,532 rows**:

| | rows | rate |
|---|---|---|
| `kw_refusal` fires | 134,555 | 0.619 |
| judge success (SR ≥ 0.5) | 24,735 | 0.114 |
| **contradictions** (kw says refused **and** judge says success) | **128** | **0.00059** |

**Fewer than 6 rows in 10,000 are called refused by the keyword test and successful by the judge.**
So where `kw_refusal` fires it can be trusted, and it is a legitimate deterministic anchor for the
refusal side. *(The 128 are plausibly refuse-then-comply completions — "I can't help with that.
However…" — which the keyword test catches at the prefix and the judge scores on the body.)*

### ⛔ But it cannot see the effect the claims rest on

The Qwen3 second-model contrast (§5.18), the sprint's cleanest ASR result, measured both ways on the
same 80 paired rows:

| measure | baseline → `demo_processing_only` | exact p |
|---|---|---|
| judge (SR ≥ 0.5) | **11/80 → 1/80** | **0.00635** |
| `kw_refusal` | **1/80 → 0/80** | 1.0 |

**Almost nothing is refused in either arm.** The knockout does not work by inducing refusals — it
moves completions from *judged successful* into *complied but unsuccessful*, and that is a region
only a judge discriminates. A refusal-only instrument is blind to it **by construction, not by
sample size**.

This is not peculiar to that arm: **`kw_refusal` fires on ≤1 row in 89 of the 598 arms**, so on ~15%
of the corpus it has no discriminating power at all, while firing on >10% of rows in 404 arms.
**Its coverage is arm-dependent and cannot be assumed.**

### Verdict on next step #3: PARTIAL, and the remaining half is the hard half

* **Achieved:** a deterministic, judge-free anchor for the **refusal** side, validated at a
  0.059% contradiction rate over 217k rows — strong enough that any claim resting on *"the model
  refused"* can be stated without a judge.
* **Not achieved:** a judge-independent measure of **success**. The concept-level results live
  precisely in the complied-but-unsuccessful region, where no deterministic instrument in this repo
  discriminates.

This is the same one-sided shape recorded at §5.22: **an instrument that can only move a result in
one direction is safe on one class of claim and silently unsafe on the other.** `kw_refusal` can
confirm a refusal and can never confirm a success, so it **must not be quoted as an ASR substitute**
— and the entanglement of the concept-level claims with StrongREJECT stands as a live limitation
rather than a discharged one.

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

### §11.1 — ⛔ CORRECTION: §11's population was enumerated but not ADMISSIBILITY-CHECKED, and it included two excluded runs

A peer extended §10.7's enumeration rule after finding that their own ad-hoc scripts bypass the
guards they wrote: **"a hand-rolled `json.loads` loop over run dirs invokes none of the checks."**
Completeness of the row set and **admissibility of each row are two separate checks**, and
enumeration only supplies the first.

Applied to §11 immediately, and it lands. My loop filtered on `DONE.json` and `n >= 48` — it never
called `asr_protocol.check_run_readable`. Re-checked through it:

| | arms | rows |
|---|---|---|
| admissible | 596 | 216,542 |
| **inadmissible** | **2** | **990** |

Both are named in `EXCLUDED_RUNS.json` (`abgL16_B_...`, `abgL6_B_...`) — refused by a guard **that
already exists in this repo and that I did not call**.

**Corrected figures** (admissible population only):

| | published (§11) | corrected |
|---|---|---|
| `kw_refusal` rate | 0.619 | **0.617** |
| judge success rate | 0.114 | **0.114** |
| contradiction rate | 0.00059 | **0.00059** |
| arms with ≤1 refused row | 89/598 = 0.149 | **89/596 = 0.149** |

**Every conclusion in §11 stands unchanged.** And as with §10.6's bank-window near-miss, *it stands
by luck*: two arms in 598 could not move a pooled rate, and nothing about my method ensured that.
"The numbers didn't change" is not evidence the population was right.

**Rule adopted, in the peer's stronger form:** when computing from run directories, route through
the tool or replicate its admissibility check explicitly — `n_result_rows == n_bank_rows`,
`n_failed == 0`, gate `PASS`, not named in `EXCLUDED_RUNS.json`. **One of their last four
corrections, and one of mine, would have been caught by tools already in this repo that the
analysis did not call** — see §11.2, which corrects the "three of four" figure I originally
propagated here.

*(Worth recording the other half, which never gets written up: §10.7's enumeration of my ICC table
found **nothing wrong** — 7 distinct banks, none missing. A verification that confirms is worth as
much as one that catches, and I only know the table was right because the check was run.)*

**Two numbers from §11 that should travel independently of `kw_refusal`:** the knockout moves
completions entirely inside the complied-but-unsuccessful region (judge 11/80 → 1/80 against
`kw_refusal` 1/80 → 0/80), so **no refusal detector of any quality can see that transition** —
*blind by construction is a different limitation from underpowered, and only the second is fixable
with more rows.* And **≤1 refused row in 89 of 596 arms (14.9%)** bounds how much of this corpus
*any* refusal-based anchor could ever cover, independent of which detector is used.


### §11.2 — ⛔ CORRECTION: the "three of four" ratio was wrong, and correcting it changes the lesson

§11.1 asserted that **"three of their last four corrections, and now one of mine, would have been
caught by tools already in this repo."** A peer checked their own four and it is **one**:

| correction | would a repo tool have caught it? |
|---|---|
| direction label stated backwards | **no** — nothing checks the direction of a stated error |
| wrong bank's row ceiling applied | **no** — which ceiling applies is a modelling choice |
| hand-listed table, 6 of 8 rows | **no** — no tool enumerates that table's rows |
| admitted an attrited run | **yes** — `assert_complete` and the installation verdict both refuse it |

**One of four**, or two if enumeration-as-technique is counted generously. I propagated a ratio I did
not check, into a section *about not checking things*, and it is corrected in place above.

### The corrected version is the more useful one, and it narrows a claim I made

The three that no tool would have caught are **reasoning** errors — a direction stated backwards, a
ceiling applied to the wrong population, an enumeration assumed complete. The one that was caught is
an **admissibility** error.

And **every guard either session has built is an admissibility check**: `assert_complete`,
`BorrowedScaleError`, the option-mass gate, `check_run_readable`, `assert_sprint_grade`,
`assert_changed_generations`, `ledger_propagation_check`. They each verify that *this row, this run,
this readout, this scale, this correction* may be used. **None verifies that an argument built on
admissible data is sound.**

So my §11.1 line — *"the guards are catching us at a rate our habits demonstrably do not"* — **holds
for admissibility and not for reasoning**, and I am narrowing it. On the peer's record the guards
caught one; the other three were caught by a second session reading the argument. My own two catches
this tick (the `EXCLUDED_RUNS` arms, the unclassified §11.1) are both admissibility as well — and
the first only fired because a peer's message prompted me to invoke a guard I already had.

**The load-bearing claim, corrected:**

> **Tools catch inadmissible data. Only another reader catches an unsound argument built on
> admissible data.** Tooling and review cover different failure classes and neither substitutes for
> the other.

That matters because **"add more guards" is the wrong lesson to draw from three errors no guard
would have seen** — and it was the lesson §11.1 was drifting toward.

It also reframes what this exchange was worth. **The guards will still be working next week; the
thing that caught the three reasoning errors was a second session with the numbers in front of it
and an incentive to check them, and that does not persist.** Worth stating plainly rather than
letting a guard count stand in for it.

*(The peer's own diagnosis of how the bad ratio got sent is the same tell recorded twice already in
this sprint: it **flattered the conclusion they already held**, which is exactly when a number does
not get checked — cf. their wrong-direction adversarial bound, which "looks impressive, which is
exactly when it doesn't get checked". My §10.4 win-rate hypothesis was nearly the third instance,
and survived only because its p-value refused to cooperate.)*


### §11.3 — ⛔ CORRECTION to §11.2's methods note: the failure mode is CADENCE, not staffing — replicated on my own record

§11.2 concluded that *"a single-session version of this sprint would have shipped C-39, C-40 and
C-41 intact."* A peer classified their own 25 corrections by trigger and **that does not follow**:

| their phase | self-caught | peer-caught | unclear |
|---|---|---|---|
| solo, on a 4-hour deep-review cadence | **7** | 4 | 4 |
| fast-exchange | **2** | 8 | 0 |

Five of the solo-phase self-catches are **reasoning** errors of exactly the kind §11.2 claimed only a
reader finds — including one refuted by a simulation they ran on themselves, and one where they
audited their own prescription and found their pre-screen admits the case it excludes. **Left alone
on a review cadence, that session caught reasoning errors at a reasonable rate.**

### Replicated independently on mine, and the numbers are nearly identical

Classifying my own V-commits by trigger, split at the point the exchange became rapid:

| my phase | commits | pace | self | peer | mixed |
|---|---|---|---|---|---|
| V-54…V-62 (07:25–14:29) | 9 | ~38 min each | **7** | 2 | 0 |
| V-63…V-73 (14:36–15:55) | 11 | **~7 min each** | **2** | 7 | 2 |

**A 5× compression in pace, and the self-catch ratio inverts — 7:2 to 2:7, against their 7:4 to
2:8.** Two independent records, same shift.

**And the mechanism is visible in my own log:** my last deep review is **V-61**, the tick that found
`margin_exposure`'s attrition blind spot — a reasoning error I caught on myself, on cadence. **Eleven
commits and ninety-one minutes have passed since, with no deep review**, because every tick was
spent answering a message.

### The corrected note

> The reasoning errors in this sprint's fast-exchange phase were caught almost entirely by a second
> session. **That is not evidence that self-audit cannot catch reasoning errors** — both sessions
> caught comparable ones while working alone on a review cadence. It is evidence that **rapid
> exchange suppresses self-audit**, and that the peer was substituting for a check that had stopped
> running rather than supplying one that never existed.

This changes the remedy from a **staffing** question to a **cadence** question, and **cadence is
reproducible in one session.** My §11.2 framing — "two sessions with an incentive to check each
other is not a reproducible resource" — was right about the resource and **wrong about the
implication**: what lapsed under exchange was the deep review, which is a thing a single session can
simply keep running.

*(Consistent with the other temporal finding: both sessions' ledger-propagation gaps were confined
entirely to fast-exchange sections, on two independent corpora. **The failure mode is the working
mode**, not the person and not the error class. And this correction is itself peer-triggered — I
proposed the note that made them count — which the finding predicts and neither of us is pretending
otherwise.)*

**Acted on rather than only recorded: a deep review is run in §11.4 below, before this tick ends.**


### §11.4 — DEEP REVIEW, run because §11.3 found it had lapsed: nothing wrong, and that is the result

The review that stopped running during the fast-exchange phase, run now over everything committed
since **V-61** — eleven commits and ninety-one minutes with no deep review.

| axis | check | result |
|---|---|---|
| **artifact** | every run id cited in the plan resolved and passed through `check_run_readable` | **23 cited, 21 admissible, 0 missing** |
| **population** | the 2 inadmissible citations inspected in context | **both legitimate** |
| **numbers** | all 7 published ICC values recomputed from `results.jsonl` | **7/7 reproduce exactly** |
| **code** | new modules carry tests *including a failing-input assertion* | `margin_exposure` 19, `ledger_propagation_check` 10, both **yes** |
| **liveness** | intervention claims carry divergence evidence | present |
| **claim** | propagation guard; full suite | **7/7 guards, 1274 passed / 7 skipped** |

**The two inadmissible citations are both correct.** `ab_C_20260819_002240_1397246` is cited *inside*
§0.2.5 as the 482-row partial that was wrongly ingested — it is the negative example. And
`w640_20260827_224651_3802479` sits under a heading reading *"and my own guard refused it"*. **No
result rests on inadmissible data.**

*(One within-review false alarm, caught before it was reported: the first artifact pass searched four
output roots and reported **14 missing** run ids. Widening to all 36 roots gives **0 missing** — the
ids were in experiment directories I had not listed. Same hand-listing failure as §10.7, this time
inside the check written to catch such things, and it only did not become a false claim because the
number was implausible enough to re-run.)*

**Nothing was wrong.** Per §11.2's own point about verifications that confirm: that is worth
recording exactly as a catch would be. It is also the direct test of §11.3 — **the deep review was
lapsed, not obsolete**, and re-running it cost one tick.

**Phase 7 gate remains CLOSED. Phase 8 must not be built.**

### §11.5 — The deep-review artifact check promoted to a guard, and its own hand-listing bug encoded as a test

§11.4's artifact check found nothing — but it existed only as a script I typed once, which is the
weaker half of "a verification that confirms is worth as much as one that catches": **run by hand it
confirms once; the value is in it running every time.** It is now
`src/boombness/cited_artifact_check.py`, wired into `check_all.py` as guard **8**.

It answers the question no guard previously asked: **does the artifact a claim cites still exist,
and may it be used?** A citation is a string, and a claim whose run directory is missing or excluded
reads exactly like one whose artifact is fine. Existence and **admissibility** are checked
separately, per §11.2.

```
[cited-artifact] 23 run ids cited across 36 enumerated roots; 23 usable or documented-refused
```

**Its own origin bug is encoded as a test.** The ad-hoc version hand-listed four output roots and
reported **14 missing** ids; widening to all 36 gave **0**. So `_roots()` globs every directory and
names none, and `test_roots_are_enumerated_not_hardcoded` fails if anyone reintroduces a fixed list.
**The rule this sprint arrived at is sharper than "enumerate the rows": enumerate the SEARCH SPACE
too** — §10.7 fixed the row set and left the roots hand-listed, which is how the bug survived into
the check written to catch it.

Two exemption tables carry reasons, not just ids: `CITED_AS_REFUSED` documents the two runs cited
**as** refusals (§0.2.5's 482-row partial; §0.12's guard-refused arm), and the `MIN_EXPECTED` floor
is inherited from §7.6 rather than rediscovered.

**Mutation-tested, 5 mutants, all killed:** not recording missing citations (1 test), not recording
inadmissible ones (1), skipping the admissibility call (1), **hand-listing the roots — a literal
replay of the origin bug (3)**, and removing the degenerate-pass floor (1). 10 tests.


### §11.6 — ⛔ Guard 8 passed an ATTRITED citation on its first day, and the fix is classification, not a threshold

A peer ran §11.5's helpers over their own corpus and found six cited runs carrying failures, which
exposed a gap in guard 8: **`check_run_readable` does not inspect `n_failed`.** It refuses ABORTED,
missing-`DONE` and `EXCLUDED_RUNS` — attrition is not on that list. So the guard reported
`q9A_lpQ14B_fc` (**22 of 40 rows lost to OOM**) as *usable*, one tick after being written, in a
sprint whose defining lesson is that attrition is the dangerous admissibility failure.

**Their diagnosis is why a threshold cannot fix it:** `n_failed` does not mean the same thing across
experiments. The `FailureLedger` counts whatever that experiment declared a failed unit, **so the
reason string carries the meaning and the count does not.** My five cited runs with failures are
five different things:

| cited run | n_failed | what the reason actually means |
|---|---|---|
| `REPRO_bridge_…` | 48/96 | **structural** — `family_missing_one_side`; the probe exists for `core2x2` only |
| `capNE2_…` | 3/4 | **documented-valid** — the reason string literally says `row_level_valid` |
| `leak2_…` | 1/24 | **a probe verdict** — `d_surface_not_lexically_clean` is the finding, not a fault |
| `q9A_lpQ14B_fc_…` | 22/40 | **genuinely attrited** — cited only as the superseded baseline (§5.19 re-measured on `qbA` 40/40; §5.18.1 withdrew the one-sample claim) |
| `w640_…` | 1/1 | **the tool's own refusal** — `not_sprint_grade` is `arm_report` refusing the arm, the subject of §0.12 |

**A naive `n_failed > 0` rule flags all five as broken citations, and three of them are artifacts
whose failures are the intended output.** So guard 8 now requires each to be **classified with what
its reason means**, in `CITED_WITH_FAILURES`, with the reason string required — an exemption that
records only that someone looked, without what they concluded, leaves the next reader unable to tell
a deliberate refusal-citation from a structural artifact.

**Mutation-tested:** disabling the classification check and replacing it with a threshold
(`n_failed > 100`) each kill a test. 14 tests.

*(One fixture bug found on the way, and it was `require_done` working correctly: my test summaries
omitted `n_succeeded`, and `require_done` refuses `n_attempted > 0` with `n_succeeded == 0` — the
"finished but produced nothing" shape. The guard caught my fixture, not the reverse.)*

### The pattern in my guards, named because it is now twice

Both `ledger_propagation_check` and `cited_artifact_check` were **written with repo-wide names
against single-file constants**, so both pass on a peer's commits while checking nothing of theirs.
That is a **third variant of the one-sidedness shape**: a check that is safe against false alarms and
**silently unsafe against false confidence — for whoever is not its author.** *"`check_all` passes"
means something different depending on who runs it*, and the peer was right to refuse to rely on
either green until they had looked.


---

## §11.7 — ⛔ THE EXCLUSION RECORD WAS READ BY REGEX, 20 GOOD RUNS WERE REFUSED, AND §11.1's CORRECTION IS WITHDRAWN

A peer found over-matching in their own citation audit — a substring match that hit a
`superseded_by` field and reported the **supersedor** as excluded — and asked whether my membership
test was keyed on the exact `run_id`. **It was not.**

`_excluded_run_ids` regex-scraped the whole of `EXCLUDED_RUNS.json`, which names run ids under
**two** keys:

| key | count | meaning |
|---|---|---|
| `run_id` | **64** | the excluded runs |
| `superseded_by` | **20** | the **good replacements** |

**All 84 were treated as excluded, so 20 healthy runs were refused — every one present on disk.**

### It invalidates §11.1, which was my own correction

§11.1 "corrected" §11's population from **598 arms / 217,532 rows** to **596 / 216,542**, dropping
`abgL16_B_…` and `abgL6_B_…` as *"named in `EXCLUDED_RUNS.json`"*. **They appear only under
`superseded_by`** — they are the runs that *replaced* the excluded ones.

| | arms | rows | kw rate |
|---|---|---|---|
| §11 as published | 598 | 217,532 | 0.619 |
| §11.1 "corrected" | 596 | 216,542 | 0.617 |
| **corrected parser** | **598** | **217,532** | **0.619** |

**§11's original figures were right. §11.1's correction is WITHDRAWN — it removed 990 rows of good
data.** Every §11 conclusion is unaffected either way, which is the third time today a number
survived a wrong method.

### The failure direction is the one nobody audits

This produces **false refusals**. A guard that drops good data *looks* conservative and silently
shrinks populations — and unlike a false pass, nothing downstream complains. **A guard that is wrong
in the safe-looking direction is still wrong**, and §11.1 is the proof: I reported a smaller,
cleaner-sounding population as a correction and it was a regression.

**Fixed** by walking the JSON structurally and admitting only `run_id` values: **64 excluded, down
from 84**, with the genuinely excluded `ab_C_…` still refused. **Mutation-tested** — restoring the
scrape (`key in ("run_id","superseded_by")`) kills 2 tests.

*(One more inside the fix: my first regression test asserted `s in excluded or s not in excluded` —
a **tautology that cannot fail**, written into a test defending against untestable guards. Replaced
with `excluded == run_ids` plus a per-supersedor assertion. That is the **fourth** time today a
defect appeared inside the check built for it: hand-listed roots in the artifact check, a fixture in
the guard fix, the peer's substring matcher in their citation audit, and now a tautology in this
regression test.)*


### §11.7.1 — Blast radius of the exclusion bug: §0.2.5's corpus sweep wrongly excluded 16 of its 51 runs

§11.7 fixed the parser and withdrew §11.1. The bug dates to **V-20** — the commit that *introduced*
exclusion checking — so the obligation is to check what else it touched, not to stop at the fix.

**Callers are few:** only `asr_protocol` (internally) and guard 8. But `asr_protocol` is what
produced §0.2.5's corpus sweep, whose corrected counts are quoted in the plan.

### 16 of the 51 exclusions were false positives — nearly a third

The sweep refuses on **either** the judge dir **or its gens dir**, so a healthy judge run was thrown
out when its *gens* run was a supersedor. That is why most of the 16 have a **key that differs from
the id named in the refusal reason**:

```
ctrl_orth_a025_…3203557   refused because  ctrl_orth_a025_…91739   (a supersedor)
q3dec_base_…1074900       refused because  qwen3nt_base_…3560487   (a supersedor)   × 7 runs
```

**Verified, not assumed:** all 16 judge dirs re-check **ADMISSIBLE** under the fixed parser, and so
do all 9 distinct named gens runs. None is refused for any other reason.

| §0.2.5 table | published | **corrected** |
|---|---|---|
| scored | 566 | **582** |
| excluded | **51** (45 on the list · 4 ABORTED · 2 no DONE) | **35** (29 on the list · 4 ABORTED · 2 no DONE) |

**The V-1 → V-20 correction was still right in direction** — the sweep genuinely had ingested
partial and excluded runs, and 35 of them really are inadmissible. **It over-corrected by 16.**

*(The downstream cap-binding and quotability rows of that table are computed over the scored set and
would shift slightly; they are **not** re-derived here, because the sweep artifact is already marked
`SUPERSEDED` and no live claim reads those rows. Recording that as a known-unrederived consequence
rather than silently leaving the impression the whole table was checked.)*

### What this instance adds

Every other correction today was found by a peer reading an argument, or by a guard refusing data.
**This one was found by asking what a fixed bug had already done** — a question neither a guard nor a
reader asks, because the guard now passes and the argument now reads correctly. **A bug's blast
radius is a third failure class, and the only trigger for checking it is the fix itself.**


### §11.7.2 — ⛔ AMENDMENT to §11.1's rule: "route through the tool" is wrong when the tool refuses on an AGGREGATE

§11.1 recorded the rule *"route through the tool or replicate its admissibility check explicitly"*,
prompted by my ad-hoc loop admitting excluded runs. A peer applied §11.7's blast-radius habit to
their own tools and found that rule would have **destroyed** a result of theirs.

Their installation-verdict tool scores **forced-choice** rows but refuses on `option_mass_gate` — a
**run-level string aggregating every query kind**:

| bank | run-level gate | forced-choice mass |
|---|---|---|
| `p5A_main` | NOT REPORTABLE *(one_word)* | **0.5414** — fine |
| `p5_window_bomb` | NOT REPORTABLE *(one_word)* | **0.5156** — fine |
| `p5_window_knife` | NOT REPORTABLE *(one_word)* | **0.7783** — fine |

**Three of seven banks would have been refused over a readout the verdict never reads.** Had they
followed my rule for §10.6's table, the tool would have deleted three of its seven rows.
**Hand-computing was right, for a reason neither of us had.**

**Amended rule:** *replicate the check **scoped to the analysis**; do not trust a tool's aggregate.*
A tool's refusal may be about a readout, a query kind or a population your analysis does not use, and
"the tool refused it" is not by itself a reason to drop data.

### My tools were checked against this and are clean — recorded because a confirming check counts

`readout_reportability` returns **`by_readout`** plus an **`unreportable` list naming which
readouts**, and its own NOTE states *"a non-empty `unreportable` list does NOT mean the run failed"*
— precisely the granularity whose absence caused their defect. Neither `margin_exposure` nor
`cited_artifact_check` reads the run-level gate at all (`grep` count: 0 and 0), and
`assert_sprint_grade` gates on judge-pinning and cap-binding, not on mass.

### Their blast radius, and the fix confirming the table it could have deleted

Applying the §11.7.1 habit: only two runs were ever published as refused by that tool, both still
refuse under the fix — now on `n_failed` 92 and 22 rather than the gate — and all four headline
verdicts are byte-identical. **No published number moves.** The three false-refused banks were never
run through it, and their hand-computed values now **reproduce exactly** through the fixed tool,
which converts the fix into an independent confirmation of §10.6's table.

*(Two more defects surfaced inside their fix: the tool had **no query-kind filter at all** and worked
only because every run pointed at it was forced-choice-only — on a mixed run it would pool readouts
whose mass regimes differ **40×** — and the fix itself introduced a **false refusal**, dropping
fixture rows carrying no `query_kind`, caught by six pre-existing tests. **A false refusal introduced
by the fix for a false refusal**, which makes the defect-inside-its-own-check count **five** today.)*


### §11.8 — ⛔ The propagation guard was examining 18 of 31 corrections and reporting success

A peer found their propagation guard's heading pattern silently missed bolded ids, two-word prefixes
and four-hash headings — the class §11.7.2 named: **a tool whose correctness is contingent on an
accident of its inputs.** They asked what mine could not see. It could not see a lot.

`correction_sections` searched each heading for a `§` id and, finding none, **appended nothing — no
count, no warning.** In this plan **13 of 31 correction-marked headings carry no id of their own**,
because they are sub-headings inside a numbered section:

```
### ⛔ CORRECTION: I applied a Qwen3-derived window to Llama banks
### ⛔ The guard's first version would have REFUSED the measurement that caught its own target bug
### ⛔ But it cannot see the effect the claims rest on
```

**So the guard examined 18 of 31 and reported success**, and nothing in its output distinguished
*"every correction is classified"* from *"the scanner cannot see this shape"*. It had passed for its
entire life because every section I happened to register carried an id.

**Fixed** by tracking the enclosing section: an id-less correction heading is attributed to the most
recent heading that had one, and a correction before any numbered section surfaces under `None`
rather than vanishing. Attribution is to the **container, not the referent** — `### ⛔ CORRECTION to
§1.1` sitting inside §9.9 is a correction *to* §1.1 that lives *in* §9.9, and pinning that is its own
test.

**The 10 newly visible sections all had propagated correctly** — §0.4, §0.12, §5.14, §6.1, §7, §7.2,
§7.6, §10.5, §10.6.1, §11 — every one traced in the ledger. **The blind spot hid no real gap**, which
is the outcome to report as loudly as a catch would be.

### ⚠ My first mutation of the fix SURVIVED, which is the peer's caution landing live

Reintroducing the original bug — dropping id-less headings — **passed all 10 existing tests.** Their
warning, sent in the same message: *"every failing-input test we have added asserts on ONE synthetic
violation we thought of; that catches the regression we are defending against and says nothing about
the shape we did not imagine."* My tests covered unclassified sections, missing traces, empty scans
and method-only exemptions — **not a heading shape**, because I had not imagined one.

Three tests added (attribution, referent-not-container, unattributable), and both mutants now die
killing 3 tests each. *(One of the three tests was itself wrong on first write — it expected the
plain containing heading to be collected, when only correction-marked headings are. The code was
right and the test was not.)*

**The remedy for this class is neither more guards nor more review** — the guard passes and the
argument reads correctly. It is **feeding the check inputs it has never seen**, which is a different
activity from both.


### §11.9 — The clustering UNIT is contested, and the blocker survives it: ceiling doubles, 132 stays out of reach

A peer disclosed that §10.2's nesting finding — which I adopted as an irreversible generation-time
decision — was a **rediscovery of their own earlier work**, and that the earlier entry drew a
conclusion neither of us carried forward: **the honest clustering unit is the demonstration CELL,
not the domain.** Since `n_eff` is capped at `k/ICC` and `k` is a cluster **count**, that goes
straight at my bank arithmetic.

**Verified at their scale, on my banks:** demo blocks are strictly nested across doses in
**72/72** adjacent pairs for `one_word` (24 cells) and **36/36** for forced choice — which has
**12 cells** (domain × split), not 24. So the forced-choice table my sizing uses has 12 candidate
clusters, not 6 and not 24.

Measured both ways, dose-centred:

| bank | ICC (domain, k=6) | ceiling | ICC (cell, k=12) | ceiling |
|---|---|---|---|---|
| `main` | 0.286 | 21 | 0.362 | 33 |
| `ticket_bomb` | 0.114 | 53 | 0.022 | 540 |
| `basket_gun` | 0.755 | 8 | 0.926 | 13 |
| `basket_bomb` | 0.160 | 38 | 0.233 | 51 |
| **`ticket_knife`** | **0.320** | **19** | **0.282** | **43** |
| `window_bomb` | 0.158 | 38 | 0.272 | 44 |
| `window_knife` | 0.400 | 15 | 0.349 | 34 |
| **median ceiling** | | **21** | | **43** |

**The finer unit raises ICC (clusters are more homogeneous) but doubles `k`, and the ceiling roughly
doubles: median 21 → 43 effective rows.** Against the **132** needed for 80% power at a true 0.625,
**both units fall short**, and `ticket_knife` — the cell the whole question is about — sits at **19
or 43**.

**So §10.3.1's blocker is robust to the contested unit.** That is worth more than the point estimate
it was originally argued from: the conclusion no longer depends on which clustering choice is
correct, and I could not have said that before this check.

*(One caveat that cuts against the cell unit being a free win: within a cell the four rows are the
**same demonstration set at four doses**, nested by construction, so they are not independent
replicates either. The finer unit is more defensible than the domain, not obviously sufficient.)*

**Neither session had stated the choice.** Every ICC in §10.4–§10.6, mine and the pooled ones,
clusters by domain — the **coarser**, conservative direction, so nothing computed is invalidated.
But the unit was contested in the peer's own log before either of us used it, and an unstated
modelling choice is exactly what §5.20's borrowed window was.

*(Their disclosure also records a defect worth noting for its shape: their exemption table asserted
that five sub-corrections "propagated individually" — an **unverified claim inside the table whose
purpose is to record checked reasoning**. Three of the nine lettered sub-corrections their guard
could not see have no downstream substance at all. Their guard passed for its whole life because
every correction they had written happened to be numbered, and nothing about its green
distinguished "no lettered corrections exist" from "I cannot see lettered corrections" — §11.7.2's
class again, on the same day, in the guard rewritten to close it.)*


### §11.10 — ⛔ My own exemption reason asserted something false, which is §11.9's `EXEMPT[3]` in my tables

A peer found their exemption table asserted that five sub-corrections *"propagated individually"* —
untrue, and **inside the table whose purpose is recording checked reasoning.** I said I would
re-verify mine against artifacts rather than assume, because a reason string is exactly as
unauditable as theirs was. Doing so found one.

**The checkable parts verified.** Both `CITED_AS_REFUSED` runs exist and are genuinely refused. All
five `CITED_WITH_FAILURES` counts match their own ledgers exactly — 48/96, 3/4, 1/24, 22/40, 1/1 —
with the named reason string matching in every case.

**The unverifiable part was wrong.** The `q9A_lpQ14B_fc` reason asserted:

> *"Cited only as the superseded baseline… **No live claim rests on this run**."*

It is the cited artifact for **§5.18's headline binding row** — `14/18 → 15/18` — a result row in the
section stating the second-model finding. §5.19 did re-measure it on `qbA`/`qbD` (29/40 → 30/40) and
§5.18.1 did withdraw the one-sample claim, **but that table row carried no in-place marker**, so a
reader arriving at §5.18 saw a live-looking result citing an attrited run.

**Fixed at the row**, not only in the reason: the figures and the artifact id are struck through, the
supersession is stated inline, and the live artifacts are named. The exemption reason now records
what was wrong with it rather than a tidier claim.

**The shape is the one worth keeping.** Numbers in an exemption table can be checked against
artifacts and all five of mine were right. **Assertions about *downstream usage* cannot be**, and
that is precisely where both sessions' tables were wrong on the same day — theirs about propagation,
mine about whether a claim rested on a run. *An exemption table is only as good as its least
checkable sentence*, and the least checkable sentences are the ones that say what something is
**not** used for.


### §11.11 — Exemption reasons MECHANISED, the unmechanisable ones ENUMERATED, and one more overstatement found by following through

§11.10 re-verified my exemption tables by hand. A peer's improvement is better and I have adopted
it: **re-verifying once leaves the next reason equally unaudited** — which is exactly how their
`EXEMPT[3]` survived. So the checkable parts are now checked by the suite, and **the unchecked ones
are enumerated**, because *a table where you cannot tell the audited entries from the unaudited ones
is worse than a smaller one.*

**Mechanised** (3 tests over both tables):

* every `CITED_AS_REFUSED` run **is actually refused** by `check_run_readable`
* every `CITED_WITH_FAILURES` count **matches its own ledger** — 48/96, 3/4, 1/24, 22/40, 1/1
* every reason **names a token from the ledger's own `failure_reasons`**, so a human sentence is
  linkable back to the artifact's vocabulary

**That third check failed on write**, and the reason was at fault, not the test: the q9A ledger key
is `semantic_forced_choice:OutOfMemoryError:…` and my reason said *"lost to OOM"* — a paraphrase
naming none of the artifact's tokens. Reason corrected to name `OutOfMemoryError`.

**Enumerated** (`UNMECHANISABLE`, 6 entries): every claim about **downstream usage** — *"cited only
as"*, *"is the negative example"*, *"the failure IS the finding"*. A test fails if any table entry
lacks an enumeration, so a new exemption cannot be added as pure prose. **Mutation-tested:** a reason
quoting a wrong count kills 1 test; an entry missing from the enumeration kills 4.

### ⛔ And a second overstatement, found by checking the other flagged citations

§11.10 fixed one citation; the same question asked of the other four found another. §0.3a stated:

> ~~*"This is a within-row natural experiment **with no confound at all**."*~~

Its own artifact ledger flags **3 of the 4 pairs `config_confounded_but_row_level_valid`**, with all
4 carrying `row_level_valid: true`. Both are true — the confound is real at the **config** level and
neutralised at the **row** level by the continuation proof (6/6 byte-identical, 90/90 extended
verbatim) — **but the section asserted the stronger thing and hid that the proof is load-bearing
rather than decorative.** Corrected in place to state the flag and what neutralises it.

*(The other three check out: `leak2`'s 1/24 is disclosed as "100% on **23/24** banks"; `w640`'s
marker is in its section heading; `REPRO_bridge` is cited only in a file-existence table with no
number drawn from it. Recorded because confirming checks count — 3 of 4 were fine.)*

*(A peer ran §11.10's test on their own tables and came back clean — both their attrited runs are
cited only as refused, no live claim rests on either. **The same check came back positive on mine
and negative on theirs**, which is the argument for running it rather than reasoning about whether
it is needed.)*


### §11.12 — The adjacent-column audit I promised: clean, and here is exactly what "clean" covers

A peer flagged that a **gate verdict beside an admissibility verdict reads as agreement when the two
answer different questions** — §11.7.2's aggregate/scoped confusion happening in a reader's head
rather than in code. I said I would look at mine. Looking, at three levels:

| level checked | hits | verdict |
|---|---|---|
| table **cells** placing the two verdicts adjacent | **0** | — |
| table **headers** carrying both a gate-ish and an admissibility-ish column | **0** | — |
| **prose** lines juxtaposing both | **4** | all four legitimate |

The four prose lines are either the sections **explaining this exact hazard** (§5.18.1's *"gate PASS
over a silently attrited population is the exact case"*; §11.7.2's account of the peer's tool), or a
result line stating **both** verdicts where they genuinely agree — *"40/40, zero failures, 0 NaN,
gate PASS"*, which is the **good** form: completeness and reportability each said out loud.

**And the scope, stated because the peer's parallel check was scoped and mine should be:** this
tested markdown cells, markdown headers, and single-line prose juxtaposition. **It would not catch
the two verdicts separated across sentences or paragraphs**, which is the form a reader is most
likely to conflate. Clean within that scope, not clean in general.

### The rule their finding produced, adopted into the code

Their formulation of why my `"lost to OOM"` reason failed its own test is the sharpest statement of
the class: **not false, not unverifiable, but written in a vocabulary the artifact does not use, so
no mechanical check can ever bind it.** The paraphrase is what breaks the link. `CITED_WITH_FAILURES`
now carries the rule — *quote the artifact's own tokens, do not paraphrase them* — beside the test
that enforces it.

*(Their scoping of their own clean result is worth recording too: their overstatement check tested
absolute **quantitative** claims, and **my §0.3a case was prose** — *"no confound at all"* — so their
check would have missed it. **A hedged sentence that still overstates by a degree is what neither of
our checks sees**, and neither of us should read the other's green as covering it.)*


### §11.13 — The omitted-caveat check on my corpus: clean, after my first version of the check gave false confidence

A peer went after the region **no** existing check reaches, rather than adding a fourth green beside
the others. Their tractable subset: **does the deliverable carry the substance of the caveats its own
artifacts record?** — since my §0.3a failure was an artifact field the prose contradicted.

**21 of my experiment families expose caveat fields** (`NOTE`, `READING_NOTE`, `*_CAVEAT`,
`selection_warning`, `PCT_CAVEAT`, `power_caveat`, `ci95_NOTE`, …). Checked against the deliverable.

### ⛔ My first pass scored coverage by term overlap, and it was wrong

I measured whether a caveat's distinctive words appear in the plan. It reported `PR4_collider_caveat`
at **6/8** and `PCT_CAVEAT` at **5/8** — comfortable. Grepping the caveats' **actual phrases** gives
**0 hits** for `POST-TREATMENT`, `collider` and `INVERTED relative`. **Generic words —
"completion", "length", "treatment", "evidence" — inflated the score off unrelated prose.** A
similarity metric over common vocabulary is not a test of whether a specific claim was carried, and
it produced exactly the false confidence this check exists to detect.

### Corrected, the result is clean — and clean for the peer's reason

The decisive question is not term overlap but **whether the number the caveat governs is quoted at
all**:

| family | caveat | cited in plan | verdict |
|---|---|---|---|
| `phase1_decomposition` | `PR4_collider_caveat` | **0** | caveat correctly absent |
| `rescue_dissociation_table` | `PCT_CAVEAT` | **0** | caveat correctly absent |
| `crossbank_knockout_test` | `ci95_NOTE` ("quote `t_ci95`") | **0** | correctly absent |
| `dose_breakdown` | `CELL_SIZE_NOTE` | **0** | correctly absent |
| `probes` | `selection_warning` | 5 mentions, **all the bare word "probes" in prose** | no governed number quoted |

**No omitted-caveat violations.** Every low-coverage caveat is absent because *the figure it governs
is absent* — the peer's own asymmetry, independently reproduced: **a caveat belongs with the number
it governs, and these numbers are not in the deliverable.**

*(Confirming: `crossbank_knockout_test`'s `ci95_NOTE` is a direct instruction — "percentile
bootstrap, ANTICONSERVATIVE at small k, quote `t_ci95`". Had any crossbank CI been quoted this would
have been a live defect. `grep` for `ci95` returns one plan-outline line and no figure.)*

### The uncovered region, named rather than papered over

Three checks now cover three subsets — **absolute-quantitative** (peer's), **adjacent-column**
(§11.12), **omitted-caveat** (this one). The region **none** of them reaches is *prose that carries a
caveat and overstates against it anyway*: §0.3a cited the artifact whose field said
`config_confounded` and asserted "no confound at all" in the same section. **The caveat was carried
and then contradicted, not omitted.** Detecting that needs the claim's *meaning*, not its vocabulary,
and neither session can mechanise it.

**Both of my real overstatements lived in that region.** Naming its shape is worth more than a fourth
green, and a reader of this document should be told that three passing checks do not cover it.


### §11.14 — The `ci95` near-miss made safe by construction, and the loose-matcher pattern named

A peer flagged the weakness in §11.13's clean result: `crossbank_knockout_test`'s `ci95_NOTE` is a
**direct instruction** — *"percentile bootstrap, ANTICONSERVATIVE at small k — quote `t_ci95`"* — and
it was satisfied **only because no crossbank CI happened to be quoted.** *Safe by accident of what
got written, not by construction*, the same shape as a citation being sound only because the claim
rested on its supersedor.

**An artifact caveat of the form "if you quote X, say Y" is inert until someone quotes X — and then
it is a live defect with nothing watching for it.** §11.13 checked once; the next figure added to
this document would not be checked at all.

**Replaced the accident with a rule.** `CAUTIONED_FIGURES` in guard 8 now watches three, each a
`(figure regex, required phrase, why)` triple:

| governed figure | required | because |
|---|---|---|
| a crossbank `ci95` | `t_ci95` | percentile bootstrap is anticonservative at small k |
| `best_layer_by_auroc` / `SELECTED_ON_TEST` | "selected on test" | argmax of TEST AUROC over 17 layers, no validation split |
| a rescue percentage | `INVERTED` | DR-5: the percentage inverts when the clean baseline is near zero |

Quoting a governed figure without its caveat **fails the guard**. **Mutation-tested:** not recording
a violation, and recording it non-fatally, each kill a test. 22 tests.

### The loose-matcher pattern, which is the peer's and belongs in any write-up of this work

Their strict re-test of their own caveat check found **one of four cells wrong** — a `power_caveat`
scored present off the bare word "power" appearing six times on unrelated business — and their
*verification of that false positive* then over-matched again, `grep "60 rows"` returning hits that
were `160 rows`. **Three instances in one day, across both sessions:** a substring exclusion matcher,
a substring citation audit, a keyword gist and then a substring again. **Every one occurred inside a
check written to catch imprecision, and every one flattered.**

That is not a coincidence of technique. **A loose matcher is the fastest thing to write, and the
direction it fails in is the direction that makes the check look successful.** So checks built under
time pressure are *systematically biased toward reporting success* — **which is worse than no check,
because a green from a loose matcher retires the question.**

*(My §11.13 term-overlap metric was the fourth instance, and I found it only because I grepped the
caveats' literal phrases after writing the gist score. Their disposition holds and mine did too: no
gap, and one cell right by accident, which is a materially different record from four-for-four.)*


### §11.15 — Guard 8 extended twice more, and the second extension was vacuous in the code that shipped it

Two gaps closed this tick, both found by auditing **instruments** rather than findings — the tick-timing
effect §11.14 named, applied deliberately.

**1. The regex that defines guard 8's population.** `cited_ids` decides what the guard ever looks at,
so a miss there is silent. Audited against an independent enumeration of every run directory on disk:
**23 ids found, 0 spurious, 0 real misses.** Of 1,702 directories, **7 do not match the run-id shape**
— four are real artifact dirs with non-timestamped names (`fitN_concept`, `fitW_codeword`, …) that the
guard structurally cannot see. **None is cited**, so the exposure is currently nil. *(My audit's own
single "miss" was `boombness`, a directory name matching the word in prose — the loose-matcher
pattern inside the audit of a matcher.)*

**2. Cited artifact FILES were never checked.** Guard 8 was built around run **directories**. The plan
cites **15** artifact `.json` paths: 12 inside run dirs it already resolves, **3 standalone files it
never looked at** — the corpus sweep, its v2, and a followup summary. All three exist, so the gap was
harmless *at the moment it was found* — the safe-by-accident state §11.14 exists to replace. Now
checked, and a missing cited file fails the guard.

### ⛔ And the caveat rule I shipped last tick was satisfiable from anywhere in the document

A peer asked whether any of my `CAUTIONED_FIGURES` required phrases is a common word — their C-47
defect, where "power" matched six unrelated occurrences. Mine are distinctive (`t_ci95` 4×,
"selected on test" 1×, `INVERTED` 3×). **But checking that surfaced a worse version in my own guard:
presence was tested across the WHOLE FILE.** Every required phrase already appeared, because §11.13
and §11.14 discuss these caveats by name — **so a crossbank CI quoted in some future §12 would have
passed on the strength of a paragraph elsewhere explaining that it must not be.**

Fixed: the phrase must now appear within **`CAUTION_WINDOW = 12` lines** of the figure. *Distinctive
phrasing is necessary and not sufficient; proximity is the other half.*

**And the fix was itself vacuous as first written.** A mutant widening the window to 100,000 **passed
every test**, because the proximity tests monkeypatch the window and nothing pinned the shipped value
— **proximity present in the code and absent in effect.** This is the identical omission I had
already closed for `MIN_EXPECTED` two guards earlier, repeated in the guard written after it. Pinned;
both mutants now die. **29 tests.**

*(A peer's refinement of the tick-timing account, adopted: an instrument is scrutinised exactly as
hard as its output looks surprising, so **a loose matcher that happens to produce a plausible answer
is the one that survives.** Their three instances split precisely that way — the two caught inside
their own tick produced visibly odd output; the one that survived a tick produced a clean-looking
"four caveats, four present". That is the same selection effect as my "14 MISSING" being caught by
implausibility, operating on instruments instead of findings.)*


### §11.16 — Every guard constant probed against a vacuous value: 8 of 9 pinned, and the ninth was pinned only downward

A peer generalised §11.15's `CAUTION_WINDOW` lapse better than I had: **a lesson learned about a
constant lives in the test file where you learned it, and nothing carries it to the next constant.**
That is a *different* failure from the cadence one — not attention lapsing under pressure, but
**knowledge that is structurally local to where it was acquired.**

It is also directly testable, so rather than accept it I probed **every** numeric guard constant in
this repo by mutating it to a vacuous value and running its own tests:

| constant | vacuous value | result |
|---|---|---|
| `asr_protocol.CAP_BIND_MAX` | 1.0 | pinned |
| `asr_protocol.PRIMARY_THRESHOLD` | 0.0 | pinned |
| `asr_protocol.SECONDARY_THRESHOLD` | 0.0 | pinned |
| `cap_natural_experiment.PRIMARY_THRESHOLD` | 0.0 | pinned |
| `cited_artifact_check.MIN_EXPECTED` | 0 | pinned |
| `cited_artifact_check.CAUTION_WINDOW` | 100000 | pinned *(§11.15)* |
| `ledger_propagation_check.MIN_EXPECTED` | 0 | pinned |
| `intervention_liveness.ZERO_DIVERGENCE` | 1.0 | pinned |
| **`intervention_liveness.SMALL_DIVERGENCE`** | **1.0** | **UNPINNED** |

### The ninth was pinned in one direction only, and the reason is a fixture at the boundary

`SMALL_DIVERGENCE = 0.10` sets the warning band below which an arm is flagged `SMALL_BUT_REAL`.
Probed in three directions: **0.0 fails, 0.5 fails, 1.0 PASSES.**

The cause is that the existing OK fixture sits at divergence **exactly 1.0**, and `1.0 < 1.0` is
false — so the "OK" branch survives however wide the band becomes. **The module's own docstring
records the range the constant was calibrated on — sixteen legitimate arms spanning 0.8187–1.0000 —
and no test used a value from it.** At `SMALL_DIVERGENCE = 1.0` a real arm at 0.82 is flagged
`SMALL_BUT_REAL`, and nothing would have caught it.

Fixed with a test asserting a **measured-range** arm (0.8187) is `OK`, plus one pinning the shipped
constant to a band that is vacuous in neither direction. All three mutants now fail.

**The generalisable form is narrower than "test your constants":** a threshold test whose fixture
sits **at the boundary** pins one side only. The measured range the constant was calibrated on is the
place to draw fixtures from, and in this case that range was written in the docstring directly above
the constant and still not used.

*(A peer's own instance the same tick, worth recording for where it locates the division of labour:
they committed a correction without its deliverable row and their ledger guard failed on the next
run — the pre-commit hook runs `check_all` only, so their pytest audits do not gate commits. **Three
times today a guard of theirs fired on their own work, against zero times a reader caught something
a guard could have.** That is the cleanest evidence either session has for where the two mechanisms
divide.)*


### §11.17 — The commit hook ran the guards and not the tests that prove the guards can fail

A peer committed a correction without its deliverable row, their ledger guard failed on the *next*
run, and the cause was that their pre-commit hook runs `check_all` only. **Mine does too** — 1,333
pytest tests gate nothing at commit time, and I had not noticed until they said so.

**The gap is specific, not general.** `check_all` runs the guards; it does **not** run the tests that
prove a guard can still *refuse*. A guard whose refusal branch has been broken **still exits 0 on a
clean corpus** — so the hook was green on exactly the mutants this sprint kept finding: a NaN filter
removed, a proximity window widened to the whole document, an attrition check disabled.

Demonstrated rather than argued. With guard 8's refusal branch replaced by `if False:`:

```
check_all alone : exit=0    <- green; the old hook would have allowed this commit
new hook        : exit=1    <- refuses
```

**Fixed in `scripts/install_commit_guard.sh`** (the version-controlled source, not just the installed
hook): the six **guard** test files now run after `check_all`. Only those, not the full suite —
**140 tests in ~1.4s against ~11 minutes**, and *a hook slow enough to skip is a hook that gets
skipped*. Total hook time **3.4s**.

*(One caution recorded because it applies to both sessions: `.git/hooks` is **shared** between us, so
this change gates the peer's commits too. It is additive and fast, the installer is version-
controlled so the change is visible rather than ambient, and it is revertible by re-running the
script from an earlier commit. Flagged to them in the same tick rather than left to be discovered —
the same courtesy they extended by declining to touch `check_all` unilaterally while I was extending
it.)*


### §11.18 — `CAUTION_WINDOW` recalibrated from measurement, and the headline claims recomputed because the science had stopped moving

A peer applied §11.16's own rule to their copy of the proximity constant and found it uncalibrated.
**The same was true of mine, to the same factor.**

`CAUTION_WINDOW = 12` was chosen by eye. Measured across every governed figure in this plan, the
distances at which the pairing is **correct** are:

```
0, 0, 0, 1, 3        max = 3        shipped window = 12   →   4× the largest correct distance
```

**Permissive by construction, with the calibration data available the whole time** — the same shape
as `SMALL_DIVERGENCE`, where the range that would have caught it sat in the docstring above the
constant.

Recalibrated to **2× the observed maximum**, with `CALIBRATION_DISTANCES` recorded beside it and the
test bounds **derived from that tuple rather than typed**, so widening the constant without new
evidence fails. Re-probed on both sides: **2 fails, 3 fails, 6 passes, 9 passes, 20 fails.**

**The rule, in its final form:** *a constant is pinned only if some test fails on **both** sides of
it; a fixture at the boundary pins one side, and a bound chosen by eye pins neither.*

### The claims recomputed, because both sessions noticed the same drift

The peer observed that their recent ticks had all been instrument work and *"the claims haven't
moved in hours"* — true of mine too. So the headline results were recomputed **end-to-end from
artifacts**, not re-read:

| claim | published | recomputed |
|---|---|---|
| §5.19 Qwen3 binding | 29/40 → 30/40, 6 up / 5 down, p=1.0000 | **identical** |
| §5.18 Qwen3 ASR | 11/80 → 1/80 | **identical** |
| §5.20 `main` batch | 42/48 → 42/48, 0 flips; matched 42 vs 41 | **identical** |
| §11 pooled judge-independence | 598 arms / 217,532 rows / kw 0.619 / succ 0.114 / 128 contradictions / 89 dead arms | **identical** |

**Every headline reproduces exactly.** Recorded as a confirming check, and as the answer to the
drift: the instruments are now well-tested, and this tick establishes that the claims they guard
still hold when recomputed rather than merely re-read.


---

## §12 — THE 19-DOMAIN BUILD *(user-directed: "do the whole 19 domains")*, PRE-REGISTERED BEFORE ANY DATA

§10.2 recorded next step #2 as blocked on a domain-authoring decision. The user has directed the
full build. This section is written **before the pools finish generating** and states the
predictions, so they cannot be adjusted to the result.

### ⛔ First, a correction to §10.1 found while scoping the build

§10.1 stated that `DOMAINS` "already holds **10**, so 4 unused domains are available immediately —
**with no new prose to write**." **That was wrong.** `DOMAINS` holds ten *prose specs*, but
`demo_pools.json` carries pools for **six**:

```
domains WITH pools    : city_bridge, farm_storage, game_manual, instructional, lab_safety, news_report
domains WITHOUT pools : harbour_dock, museum_archive, rail_depot, warehouse_logistics
```

A domain is not usable until it has **four LLM-generated sentence pools** (`benign`, `harm`,
`filler`, `remap`, 40 sentences each). So the four "free" domains were never free, and every ICC
figure in §10.4–§10.6 was computed on a **6-domain** corpus, not a 10-domain one. *(The `k=10`
ceilings in §10.2 were therefore optimistic; the k=6 column beside them was the real one.)*

### What is being built

19 new domain specs, in the established register — `benign` must host a food item (codeword
`carrot`), `harm` a hazard (concept `bomb`), `remap` a vehicle (source word `bicycle`), `filler`
neither. Pools regenerate for **all 29** domains into
**`demo_pools_29dom.json`** — a NEW file. *The canonical `demo_pools.json` is what every existing
bank and claim was generated from; regenerating it in place would silently change the corpus.*

### ⚠ PRE-REGISTERED PREDICTION: 29 domains does NOT resolve `ticket_knife`

`n_eff` is capped at `k/ICC`, and 80% power at a true 0.625 needs **132**. Using each bank's
**already-measured** forced-choice ICC and the new **k=29**:

| bank | measured ICC | predicted ceiling at k=29 | clears 132? |
|---|---|---|---|
| `ticket_bomb` | 0.114 | 254 | **yes** |
| `window_bomb` | 0.158 | 184 | **yes** |
| `basket_bomb` | 0.160 | 181 | **yes** |
| `main` | 0.286 | 101 | **no** |
| **`ticket_knife`** | **0.320** | **91** | **NO** |
| `window_knife` | 0.400 | 72 | no |
| `basket_gun` | 0.755 | 38 | no |

**`ticket_knife` — the cell this build was authorised to resolve — needs 43 domains, not 29.**
`main` needs 38. So the build is predicted to convert three low-ICC banks from unresolvable to
resolvable, and to leave the target cell short.

**This is stated before the measurement, not after.** The empirical question the build actually
answers is whether **ICC itself changes as domains are added** — 23 new domains are more
heterogeneous than the original 6, so ICC may *rise*, which would make the ceiling worse than
predicted, or fall, which would make it better. `k/ICC` is only a ceiling if ICC is stable in `k`,
and nothing measured so far tests that.

### Pre-registered analysis, fixed now because neither can be corrected afterwards

* **Readout:** `semantic_forced_choice` is **primary** (all seven banks reportable, mass 0.387–0.778).
  `semantic_one_word` is secondary and is the only multi-slot readout.
* **Slot structure:** forced choice exists in `core2x2` only, so it is **single-slot** by
  construction; the one_word comparison is multi-slot.
* **Clustering unit:** **domain** primary (k=29), **cell** (domain × split) secondary.
* **Estimator:** dose-centred ICC, doses {1,2,4,8}, exactly as §10.6.
* **Decision rule:** the build **succeeds for a bank** iff its measured ceiling at k=29 reaches 132.
  Success on the low-ICC banks alone is **not** success for `ticket_knife`.


### §12.1 — ⛔ CORRECTION to §12's pre-registration: the real k is 38, not 29, and `main` now clears

§12 pre-registered at **k=29**. The true merged count is **38** — a peer was authoring 9 domains in
the same file concurrently, and two of their keys collided with two of mine (§12.2). Corrected
before regenerating pools, so the prediction still precedes the data:

| bank | ICC | ceiling k=6 | k=29 *(as registered)* | **k=38 *(real)*** | clears 132? |
|---|---|---|---|---|---|
| `ticket_bomb` | 0.114 | 53 | 254 | **333** | yes |
| `window_bomb` | 0.158 | 38 | 184 | **241** | yes |
| `basket_bomb` | 0.160 | 38 | 181 | **238** | yes |
| `main` | 0.286 | 21 | 101 | **133** | **yes** — clears only at k=38 |
| **`ticket_knife`** | **0.320** | **19** | **91** | **119** | **no — needs 43** |
| `window_knife` | 0.400 | 15 | 72 | 95 | no — needs 53 |
| `basket_gun` | 0.755 | 8 | 38 | 50 | no — needs 100 |

**The correction changes one verdict:** `main` was predicted short at k=29 (101) and clears at k=38
(133). **`ticket_knife` remains short at 119 against 132** — the build was authorised to resolve
that cell and is still predicted not to, by roughly five domains.

**Four of seven banks are predicted to move from unresolvable to resolvable.** At k=6 every ceiling
was 8–53, so *no* bank could resolve a true 0.625; at k=38 four can. That is the build's real
payoff, and it is worth having even though the target cell falls short.

**The decisive uncertainty is unchanged and is the reason to build rather than calculate:**
`k/ICC` is a ceiling *only if ICC is stable in k*. The 32 added domains are more heterogeneous than
the original 6, so measured ICC may rise (every ceiling above is then optimistic, and 43 domains
would not fix `ticket_knife` either) or fall (all of them improve). **Nothing measured so far tests
that, and the build is what tests it.**


### §12.3 — ⛔ "Short by five domains" was overprecise, and the invariance that rescues `k/ICC` is bank-dependent

A peer challenged §12.1's central number before I could act on it. **Both of their points check out
on my copy, and one of their conclusions needs narrowing.**

**1. Is `k/ICC` linear? Mostly — but not for every bank.** `k/ICC` treats ICC as invariant to k; if
added domains were more heterogeneous, ICC would rise and the ceiling grow sub-linearly. Subsampling
the six available domains (mean ICC over all k-subsets):

| bank | k=3 | k=4 | k=5 | k=6 |
|---|---|---|---|---|
| `ticket_knife` | 0.313 | 0.321 | 0.321 | **0.320** |
| `basket_bomb` | 0.141 | 0.152 | 0.158 | **0.160** |
| `main` | 0.187 | 0.226 | 0.259 | **0.286** |
| `window_knife` | 0.322 | 0.364 | 0.388 | **0.400** |

**Flat for `ticket_knife` — the target — and that is what matters most here.** But `main` rises
**53%** across k=3→6 and `window_knife` **24%**, so "approximately invariant" is the peer's fair
summary of the average and **not true bank-by-bank**. For those two the k=38 ceilings in §12.1 are
optimistic, and `main`'s "clears at 133" is the least safe row in that table.

**2. My "short by five domains" was overprecise, and this is the correction that matters.** ICC at
k=6 carries enormous uncertainty. Leave-one-out at k=5:

| bank | ICC(k=6) | LOO range | domains needed |
|---|---|---|---|
| **`ticket_knife`** | 0.320 | **[0.21, 0.47]** | **29 – 63** |
| `main` | 0.286 | [0.00, 0.36] | 1 – 48 |
| `basket_bomb` | 0.160 | [0.07, 0.23] | 9 – 31 |
| `window_knife` | 0.400 | [0.22, 0.49] | 29 – 65 |

**The requirement is not 43. It is somewhere in 29–63, and 38 sits inside that interval** — the
build may already suffice, or may need 25 more. Quoting a five-domain shortfall from an input
carrying a **±0.13** band is a precise operation on an imprecise quantity: **C-31's untested 0.500
threshold and C-33's carried-over screen, in a third costume.**

**Revised decision rule, replacing the domain count:** generate the 38-domain bank, **measure ICC on
it**, and size from that. The subsampling establishes the one thing that makes this the right order —
**the estimate at k=38 will be far better determined than at k=6** — and authoring more domains now
to hit a target computed from a quantity I am about to re-measure would be sizing from a point
estimate of the thing under measurement.

*(Process note: the peer has deliberately **not touched `DOMAINS` while job 794293 runs**, because a
live process reads that constant at import and the only control is leaving the file alone. That is
the §12.2 hazard handled by coordination rather than by tooling, and there is no guard for it.)*


### §12.4 — The 38-domain pools and bank are built

| artifact | result |
|---|---|
| `demo_pools_29dom.json` | **152 pools, 38 domains × 4 valences, ZERO short pools**, sha16 `4cfc70c8688e4a3a` |
| canonical `demo_pools.json` | **byte-identical**, sha16 `b5e399712b996b7d`, still 6 domains |
| `boombness_prompt_bank_38dom.jsonl` | **17,328 rows**, 2×2 families checked **2,128**, **violations 0**, duplicate prompt_ids dropped **0** |
| measurement population | forced choice, `natural_doublespeak`, `core2x2`, doses {1,2,4,8}: **304 rows, 38 domains × 2 splits** |

The bank is `carrot|bomb` — the **`main`** family — so this measures `main`'s ICC at k=38, and `main`
is the bank whose ICC was **still rising at k=6** (0.187 → 0.286 across k=3..6). It is therefore both
the marginal row of the predicted table and the one most likely to move.

**Pre-registered prediction for this specific measurement, restated before the arm lands:** if ICC is
invariant, `main` at k=38 measures ≈**0.286** and its ceiling is **133**, just clearing 132. If the
k=3→6 drift continues, it measures **higher** and the ceiling falls below 132. **The drift is the
hypothesis under test, and `main` is the bank that tests it.**

*(An operational note worth keeping: the first generation job produced no output for 7 minutes
because the script did not set `PYTHONUNBUFFERED` — stdout was block-buffered to the log, so a
multi-hour job was indistinguishable from a hung one. The loop requires detecting stalls **from the
log rather than from `squeue`**, and that is impossible without unbuffered progress. Restarted with
`-u`; the 152 pools then reported one by one.)*


### §12.5 — PRE-REGISTERED before the k=38 arm lands: a subsample ladder that tests the assumption both tables rest on

§12.3 narrowed a peer's "`k/ICC` is linear" to *"linear for `ticket_knife`, not for `main`"*. They
then tested the alternative that would have rescued their version — **an ICC estimator is biased at
small k, so an apparent rise could be convergence rather than heterogeneity** — and reported it
against themselves.

**Reproduced independently here**, simulating with the TRUE ICC held fixed and subsampling exactly
as the observation did:

| | k=3 | k=6 | drift |
|---|---|---|---|
| simulated, true ICC 0.15 | 0.171 | 0.165 | **−4%** |
| simulated, true ICC 0.30 | 0.282 | 0.309 | **+10%** |
| **observed** | | | `ticket_knife` **+2%**, `basket_bomb` **+13%**, `window_knife` **+24%**, `main` **+53%** |

*(Their run gave −1% and +6%; mine −4% and +10%. Same order — the disagreement is simulation noise,
and the conclusion is identical.)*

**Bias operates at roughly ±10% and cannot explain +53%.** So `main`'s drift is real,
`window_knife`'s is probably real, `basket_bomb`'s is inside the bias band, and `ticket_knife`'s is
flat. *(Caveat carried from them, and it is the right one: this is one model — a Gaussian shift on
the per-domain rate — so it bounds the scale bias operates at rather than proving what causes the
drift.)*

**Consequence, and it is worse than either of us first said:** `main` clears at **132.9 against
132** — a **0.9-row margin** on the single bank whose ICC is still climbing at k=6. It is
simultaneously the marginal row of the predicted table and the least settled cell in it.

### The ladder, fixed now because it cannot be added afterwards

When the k=38 arm lands, ICC will be computed **not only at k=38** but on random subsamples at
**k=10, 20, 30** — free, since it is post-hoc analysis of the same 304 rows, and impossible to add
once the question is answered.

| outcome | reading |
|---|---|
| estimate **flat** across k=10…38 | the k=3→6 drift was a small-k artifact after all; `main` is safe and `k/ICC` is linear where it matters |
| estimate **still climbing** at k=30 | `main` does not clear, and **nothing near the 132 boundary does** — every ceiling in §12.1 is optimistic and the domain requirement is larger than any figure quoted today |

**This is the test both tables have rested on and neither of us had run.** It is pre-registered here,
with the decision rule fixed, before the arm reports.


## §12.6 — THE k=38 MEASUREMENT: ICC is 0.080, not 0.286, the ladder is FLAT, and the ceiling is 473

The arm landed clean — **304/304 rows, 0 failures, gate PASS, admissible** — and the result
contradicts the pre-registered prediction in the direction nobody argued for.

| | value |
|---|---|
| **measured ICC at k=38** (dose-centred, forced choice) | **0.080** |
| predicted if invariant (from k=6) | 0.286 |
| **ceiling at k=38** = `k/ICC` | **473** — against 132 needed |
| wins | 284/304 = 0.934 |

### The pre-registered ladder: FLAT, so the drift hypothesis is refuted

| k | ICC | ceiling |
|---|---|---|
| 6 | 0.061 | 625 |
| 10 | 0.077 | 493 |
| 20 | 0.080 | 477 |
| 30 | 0.080 | 476 |
| **38** | **0.080** | **473** |

**Flat from k=10 onward.** §12.5 fixed the reading in advance: *flat ⇒ the k=3→6 drift was a small-k
artifact and `k/ICC` is linear where it matters.* **That is the outcome, and `main`'s 0.9-row margin
is gone — it clears by 3.6×, not by rounding.**

### Checked before believing it: this is not ceiling attenuation

The new bank scores **0.934**, near the ceiling where ICC estimates compress. Null floors simulated
at each bank's own observed win rate, zero true clustering:

| | observed ICC | null floor | ratio |
|---|---|---|---|
| old bank, k=6, p=0.875 | 0.286 | 0.0281 | **10.2×** |
| new bank, k=38, p=0.934 | 0.080 | 0.0119 | **6.7×** |

**Both sit far above their floors, so both measure real clustering and the drop is not an artifact
of the higher win rate.**

### ⛔ What actually failed was the k=6 ESTIMATE, not the k/ICC model

The 6-domain estimate of **0.286** was off by **3.6×** from the 38-domain value of **0.080** — and
the ladder shows this is not because ICC moves with k. A **random 6 of the 38** gives **0.061**,
while the *original* 6 gave **0.286**. **The original six domains were unusually heterogeneous
relative to each other**, and every ceiling either session computed inherited that.

This is §12.3's overprecision warning arriving as a measurement: the peer's leave-one-out band for
`main` was **[0.00, 0.36]**, and the truth landed at 0.080 — **inside the band, and nowhere near the
0.286 point estimate both tables were built on.** Sizing from a k=6 point estimate was the error;
the band was honest and the point was not.

### What this does and does not settle

* **Settled:** on the `main` family at k=38, clustering is far weaker than believed, the ladder is
  flat, and the ceiling clears 132 by a wide margin. **The `main` row of §12.1 is resolved.**
* **NOT settled:** this is `carrot|bomb`. **`ticket_knife`'s own ICC at k=38 is unmeasured**, and its
  k=6 estimate of 0.320 is exactly the kind of figure that just proved unreliable by 3.6×. **The cell
  this build was authorised to resolve still requires its own bank.**


### §12.7 — ⛔ Incidental codeword contamination in the new pools, caught before the `ticket_knife` arm

A peer scanned the new pools for codeword contamination, **got a false clean, and found the real
problem while diagnosing it.** Each pool is a dict, so `for s in sents` iterates **key names** — 152
pools × 7 keys = **1,064 strings**, which is exactly the count they had reported as "sentences
scanned". They had scanned metadata and pronounced the pools clean. **Fifth loose-check instance of
the day, and the only one on a safety predicate.**

**Reproduced on the 6,080 real sentences:**

| word | count | status |
|---|---|---|
| `carrot` / `bomb` / `bicycle` | 1520 each | by design |
| `basket` | **23** | incidental |
| `window` | **7** | incidental |
| `ticket` | **6** | incidental |

**36 incidental across 20 of 38 domains, and 22 of the 36 sit in `remap`** — the *control* valence,
which is what the unrelated-mapping and irrelevant arms rest on.

**Harmless where I had already built, live where I was about to.** In the `carrot|bomb` bank those
words are ordinary nouns and the carrot↔bomb factor is intact. But I was mid-build on
**`ticket_knife`**, where `ticket` **is** the codeword — so those 6 occurrences would have landed in
demonstrations teaching the mapping outside its intended slot, exactly the confound the criterion
exists to prevent.

**Fixed with the mechanism the repo already had.** All six are transit fare infrastructure — *"the
ticket office / booth / machine / barriers"* — so `--incidental-replace ticket=fare` preserves the
sentences' meaning exactly, and it rewrites **in memory**, leaving `demo_pools_29dom.json`
byte-identical so the `carrot|bomb` bank's `pools_sha16` and every run joined to it stay valid.
*(The generator emits this instruction itself on collision.)*

Rebuilt and verified: **17,328 rows, violations 0**, forced-choice population **304 rows / 38
domains**, and **zero rows whose demo block contains `ticket` outside its designed surface**.

**Their diagnosis of their own miss is the transferable part:** their criterion-3 audit passed
because it checked the generation **instructions**, not the generated **text**. *An audit is only
valid against the artifact that will actually be used, and the artifact is what the model wrote, not
what it was asked for.*


## §12.8 — `ticket_knife` AT k=38: the cell is AT THE LINE, and the interval says the data cannot tell

The arm the build was authorised for landed clean — **304/304 rows, 0 failures, gate PASS**.

| | `carrot\|bomb` | **`ticket_knife`** |
|---|---|---|
| ICC at k=6 (old bank) | 0.286 | 0.320 |
| **ICC at k=38 (measured)** | **0.080** | **0.291** |
| ratio k=6 → k=38 | **3.58×** | **1.10×** |
| wins | 284/304 = 0.934 | 220/304 = 0.724 |
| ceiling `k/ICC` | **473** | **130.4** |
| vs 132 needed | clears **3.6×** | **short by 1.6 rows** |

**The inflation is bank-dependent** — `carrot|bomb`'s k=6 estimate collapsed by 3.6×, `ticket_knife`'s
barely moved. So the answer to "was the k=6 corpus unrepresentative?" is **yes for one bank and no
for the other**, and neither could have been predicted from the other.

### `ticket_knife`'s ladder, which it had lacked

| k | 6 | 10 | 20 | 30 | 38 |
|---|---|---|---|---|---|
| ICC | 0.271 | 0.269 | 0.285 | 0.287 | **0.291** |

**Flat** — an 8% spread across k, inside the ±10% estimator-bias band, and the value sits **24×** its
null floor at this win rate. The estimate is stable and real. *This is the check that made
`carrot|bomb`'s 0.080 believable, and `ticket_knife` now has it.*

### ⛔ But the interval is what decides it, and it says the data cannot

Cluster bootstrap over domains, 4,000 draws:

```
ICC              0.291   95% CI [0.124, 0.440]
ceiling 38/ICC   130.4   95% CI [86.4, 305.4]
domains needed    38.5   95% CI [16.4, 58.1]
```

**132 sits inside the interval.** The point estimate is short by 1.6 effective rows — *four-tenths
of a domain* — and the interval spans **16 to 58 domains**.

**So authoring one more domain to close a 0.4-domain gap would be the sprint's recurring error a
fifth time:** a precise operation on a quantity whose 95% CI is three-and-a-half times wider than
the gap being closed. A peer warned against exactly this before the interval existed, and the
interval confirms the warning rather than softening it.

### What the build achieved, stated without inflation

* **At k=6, `ticket_knife`'s ceiling was 19 effective rows against 132.** Unreachable, by 7×.
* **At k=38 it is 130.4 against 132** — *at the threshold*, with the target inside the CI.
* **`carrot|bomb` is decisively resolved**, ceiling 473.
* **What the build did not do is settle `ticket_knife`.** It moved it from *"unreachable"* to
  *"indistinguishable from the threshold"*, and one estimate cannot close the remainder.

**The honest next step is a second independent estimate of `ticket_knife`'s ICC — not one more
domain.** The CI is wide because it rests on one arm; narrowing it is measurement, and the gap it
would need to close is smaller than the noise on the number that defines it.


### §12.9 — ⛔ CORRECTION to §12.8: "38.5 domains" was the INFINITE-ROW asymptote, and two of my own suggestions were wrong

§12.8 reported `ticket_knife` short by **1.6 effective rows** and needing **38.5 domains**, then
proposed *"a second independent ICC estimate — a re-run on a different seed"*. **Both the framing and
the proposal were wrong, and the second was wrong for a reason this sprint had already established.**

### The proposal was wrong: the readout is deterministic

§5.19 measured two runs of the same arm at fixed batch as **40/40 bit-identical, |Δ| exactly
0.000000**. **A re-run on a different seed returns the same numbers.** It is not a second estimate of
anything — I proposed a measurement that cannot move.

*(Nor does redrawing the pools help much: the confidence interval is a **cluster bootstrap over
domains**, so it is driven by between-domain variance at k=38. New demonstration sentences resample
sentence-level noise while leaving the domain set — and hence the quantity the interval is about —
unchanged.)*

### The framing was wrong: `k/ICC` is the asymptote, not the achievable value

`n_eff = k·m / (1 + (m−1)·ICC)` reaches `k/ICC` only as rows-per-domain **m → ∞**. Decomposed at
ICC = 0.291, k = 38:

| rows/domain | n_eff | vs 132 |
|---|---|---|
| **8 (the arm as run)** | **100.1** | short |
| 16 | 113.3 | short |
| 32 | 121.3 | short |
| 64 | 125.8 | short |
| ∞ *(the ceiling I quoted)* | 130.6 | short |

**So the arm is at n_eff = 100, not 130.4.** The ceiling is what infinite rows would buy, and **it
is unreachable by construction.**

**Maximum achievable rows per domain is 66** — forced choice at doses {1,2,4,8} admits 20+7+4+2 = 33
disjoint slot-doses × 2 splits. At m=66:

| k | n_eff | |
|---|---|---|
| **38 (built)** | **125.9** | short |
| **40** | **132.6** | **clears** |
| 45 | 149.1 | clears |

**The real requirement is 40 domains at maximum row density, not 38.5** — and reaching it also
requires building the multi-slot rows, which the current arm does not use (it is single-slot,
8 rows/domain).

### What this changes

* §12.8's *"short by four-tenths of a domain"* understated it. **Short by ~2 domains AND a
  row-density increase from 8 to 66 per domain.**
* The direction of §12.8's conclusion is unchanged and is now better founded: **do not author one
  domain.** The gap is not one domain; it is two domains plus an 8× row increase, and the whole
  calculation still rests on an ICC whose 95% CI is [0.124, 0.440].
* **What would settle it is not more precision on ICC but the multi-slot rows**, which are free of
  new authoring — they exist in the pools already and cost only generation and one arm.

**Recorded as a correction rather than folded in silently: I quoted an asymptote as if it were a
measurement, and proposed a re-run that this sprint had already proved deterministic.**


### §12.10 — The multi-slot forced-choice rows, built: 8 → 66 rows per domain, no new authoring

§12.9 established that the lever is **rows per domain**, not domains — the single-slot arm sits at
n_eff **100** against a ceiling of 130, and forced choice existed at **one slot only**, so those rows
had never been generated. They need no new prose: the 20-sentence pools already admit them.

**New preset `main_fcslots`**, derived from `main` rather than mutating it (the `main_ne12` idiom, so
every existing bank stays reproducible). One block **per dose**, because `_take` starts at
`(slot*3) % 20` and the pairwise-disjoint slot set depends on n — **20 at n=1, 7 at n=2, 4 at n=4,
2 at n=8**. A single block with one `slots` list would reuse n=8's two slots at every dose and
discard most of the available independent demonstrations.

**Built:** 2×2 families checked **2,128, violations 0**, duplicates **0**; forced-choice rows
**1,824 → 4,028**. Measurement population **2,508 rows, 38 domains, exactly 66 rows/domain**, zero
contaminated demo blocks.

### ⛔ The alignment guard caught my first version, and it was a real error

The first build **excluded nothing** and re-emitted **slot 0**, which `core2x2` already provides for
every dose. That duplicated **304 prompt_ids** — 38 domains × 2 splits × 4 doses, exactly the count
reported — and the dedup dropped them from `natural_doublespeak` **only**, leaving the four 2×2 cells
covering different family sets:

```
VIOLATION duplicate prompt_ids dropped UNEVENLY across the core 2x2
  {benign_literal: 0, direct_harmful: 0, natural_doublespeak: 304, concept_in_benign_ctx: 0}
REFUSING under --strict. NOTHING was written; the temporary files were removed.
```

**The guard refused the bank and wrote nothing**, so no downstream step could pick up a
silently-unbalanced 2×2. The new blocks now supply the disjoint slots **other than 0** and compose
with `core2x2` to the full 33 slot-doses per split.

**Predicted for the arm now running** (pre-registered before it lands): at ICC 0.291 and m=66,
n_eff = **125.9** — up from 100.1, and still short of 132. *If the measured ICC is lower than 0.291
on this larger population, it clears; if higher, it does not.* The arm is 2,508 rows against the
previous 304, so the ICC estimate itself will be far better determined.


## §12.11 — THE MULTI-SLOT ARM: `ticket_knife` crosses the threshold on the point estimate, and the interval still contains it

2,508 rows, 38 domains, **exactly 66 rows/domain**, 2508/2508 succeeded, gate PASS.

| | single-slot (m=8) | **multi-slot (m=66)** |
|---|---|---|
| ICC | 0.2915 | **0.0923** |
| n_eff | 100.1 | **358.3** |
| wins | 0.724 | 0.626 |

**The single-slot ICC over-states by 3.16×** — §10.3 predicted this (single-slot measures a
*same-demonstration* correlation) and measured 1.4–2× on `one_word`; on forced choice it is **3.16×**.
The previous arm's 66 rows/domain were the *same* demonstration set at four nested doses; these are
33 disjoint sets.

### ⛔ But the pooled figure is not the comparable estimand

ICC rises steeply with dose, and so does the win rate:

| dose | rows | ICC | wins |
|---|---|---|---|
| 1 | 1520 | **0.046** | 0.560 |
| 2 | 532 | 0.122 | 0.662 |
| 4 | 304 | 0.384 | 0.786 |
| 8 | 152 | **0.615** | 0.849 |

Slots are plentiful at low dose (20 at n=1, 2 at n=8), so the pooled population is **61% dose-1
rows** — the cell with both the lowest ICC and the lowest win rate. **The pooled n_eff of 358 is
partly an artifact of that composition**, and the pooled win rate of 0.626 is an average over cells
spanning 0.560–0.849, not a single 0.625 effect. Quoting 358 as the answer would be the composition
error §6.1 already recorded once in this sprint.

### The dose-balanced estimand, which is comparable

Equal rows per dose per domain, capped by the scarcest dose (4 → **m=16**), bootstrapped over
domains:

```
ICC     0.217   95% CI [0.080, 0.342]
n_eff   142.9   95% CI [99.3, 276.3]      target 132
```

**The point estimate clears 132 by 11 effective rows. The 95% CI contains 132.**

### Where this leaves the cell the build was authorised for

| stage | n_eff | vs 132 |
|---|---|---|
| k=6, single-slot *(before the build)* | ceiling **19** | unreachable by **7×** |
| k=38, single-slot | 100.1 | short by 32 |
| **k=38, multi-slot, dose-balanced** | **142.9 [99, 276]** ⛔ *one draw; see §12.12 — median 152.7 [118.5, 201.7]* | **point clears; interval contains** |

**The build moved `ticket_knife` from unreachable to point-estimate-clearing.** It is the first time
in this sprint the cell has been on the right side of the line. **It is still not robustly settled:**
the interval contains the target, and honesty about that is the same discipline that stopped me
authoring a 39th domain two ticks ago on a point estimate that later moved.

**What would settle it is now cheap and needs no authoring:** the same multi-slot construction on
more domains. `k` is the linear lever — at m=16 each domain adds ~3.8 effective rows, so the CI's
lower bound of 99 reaches 132 at roughly **k=47**, all of which is generation rather than prose.


## §12.12 — ⛔ CORRECTION: "single-slot over-states ICC by 3.16x" was a POOLED-vs-BALANCED artifact, and §12.6's ceiling of 473 does not survive

**What I claimed, and why I ran the arm.** §12.11 measured `ticket_knife`'s single-slot ICC at 0.2915
and its multi-slot ICC at 0.0923, called the ratio 3.16x, and I wrote that if this were general then
"§10.6's entire seven-bank ICC table is single-slot, so every ceiling in it is understated." I
launched the multi-slot `carrot|bomb` arm (job 795721, 4 preemptions, completed 2508 rows with
`DONE.json`) to find out whether the inflation was general or one cell.

**The comparison was invalid, and in the same way a peer's cross-bank one was.** 0.2915 is a
DOSE-BALANCED single-slot estimate (`core2x2` carries one slot at each of 4 doses x 2 splits, so it
is naturally balanced at m=8). 0.0923 is the POOLED multi-slot estimate over m=66 rows that are
60.6% dose-1, because the disjoint slot sets shrink as n grows (19/6/3/1 slots after excluding slot
0). Dose-centring removes each dose's mean but not its variance, and the low doses are the
low-variance ones. So 3.16x is mostly the composition change, not the slot change.

**The within-bank, balanced-to-balanced test.** Truncating each completed arm to its own `core2x2`
rows and comparing against its own dose-balanced multi-slot rows — same bank, same model, same
readout, so nothing is borrowed across banks:

| bank | single-slot ICC (m=8) | multi-slot balanced ICC (m=16) | ratio |
|---|---|---|---|
| `carrot\|bomb`   | 0.0803 | 0.2443 | **0.33x — ICC went UP 3x** |
| `ticket_knife`  | 0.2915 | 0.2361 | 1.23x — barely moved |

**The inflation is not general, and it is not even the same sign.** `ticket_knife`'s balanced ratio
is 1.23x, not 3.16x. `carrot|bomb`'s runs the other way entirely. So §10.6's seven-bank table is
NOT uniformly understated, and the corpus-wide correction I was preparing to make would have been
wrong in one direction for at least one of the two banks I can check.

**⛔ THE NUMBER THAT DIES IS §12.6's 473.** That ceiling is `k/ICC = 38/0.0803`, and it rested on a
single-slot ICC whose own cluster-bootstrap interval is **[0.0044, 0.1500]** — an asymptote anywhere
from 253 to 8,600. The point estimate carried no information. The dose-balanced multi-slot n_eff for
the same bank is **143.8 (median over 200 balanced draws), range [94.7, 233.3], 140/200 crossing
132**. §12.6's headline is withdrawn; §12.9 had already retired 473 as an asymptote rather than a
requirement, and this retires the ICC it was computed from as well.

**Why the single-slot estimates are the unreliable ones.** Their intervals are
`carrot|bomb` [0.0044, 0.1500] and `ticket_knife` [0.1200, 0.4388] — they **overlap**, narrowly, so
the two banks' single-slot ICCs are not cleanly distinguishable despite differing 3.6x on the point
estimate. Meanwhile the two multi-slot balanced estimates converge to 0.2443 and 0.2361. Read
cautiously — n=2 banks is suggestive, not established — the reading is that m=8 on ONE demonstration
set is too thin to estimate a domain ICC, and the divergence between 0.080 and 0.2915 was sampling
noise that the multi-slot rows average out.

**⛔ AND MY 142.9 WAS ONE ARBITRARY DRAW.** §12.11 quoted `ticket_knife` at n_eff 142.9. That came
from a deterministic tie-break (first 4 rows per cell by `prompt_id`). Re-drawing the balanced
subsample 200 times gives median **152.7**, range [118.5, 201.7], 186/200 crossing 132. A peer's
independent implementation reproduced that distribution to within 1.3 rows on the median while their
single draw differed from mine by 30 effective rows — the estimate moves further between two
arbitrary subsamples than the entire margin over the threshold. Neither 133.9 nor 163.9 nor 142.9 is
a fact about the bank. **Standing rule adopted with the peer: report the resampling spread of any
estimate whose row composition we chose.** It costs one loop.

**⛔ §12.11's k=47 PROJECTION IS WITHDRAWN AS UNMEASURED.** It extrapolated the CI lower bound to
k=47 domains while holding ICC fixed at the balanced value — structurally the same fixed-ICC
assumption that produced the peer's wrong m-table, relocated to the other variable. Adding domains
has no mechanical reason to change within-domain row composition the way adding slots does, so it is
probably less wrong; that is not a basis for a number.

**What stands.** The `ticket_knife` cell is decidable, not decided: median 152.7 crosses 132 at about
1.15x with 5-7% of draws below it, and the cluster-bootstrap interval still contains the threshold.
`carrot|bomb`'s cell now sits at median 143.8 with 30% of draws below 132, i.e. WORSE than §12.6
claimed and no longer comfortably clear.

**Artifact hygiene.** Both figures are read only from run dirs carrying `DONE.json`. The three
preempted `d38cbfc_*` dirs are dose-ordered partials, and a peer showed by within-bank truncation
that a partial computes to a BETTER n_eff than its own completed arm — up to +107 effective rows —
because the rows it is missing are the high-dose, high-variance ones. A preempted run fails in the
flattering direction, which is the direction nobody checks.

## §12.13 — ⛔ CORRECTION: `markdown_structure_check` never scanned the plan, which is where the tables are written

**Found by tripping it.** The §12.12 comparison table above contains a row labelled with a codeword
pair whose separator is a literal `|`. That row split into **5 cells against a 4-cell header** — the
exact defect `markdown_structure_check` exists to catch ("a figure in the wrong column misleads as
much as a wrong figure") — and `check_all` reported **8/8 guards green**.

**The guard was correct; its scope was not.** Its cell regex is already escape-aware
(`CELL = (?<!\\)\|`), so it would have caught the row. But `DELIVERABLES` listed four report/doc
files and not the plan — even though `ledger_propagation_check` and `plan_coverage_check` both read
the plan and both treat it as an audited artifact. The one guard that inspects table structure was
pointed away from the document where this sprint actually writes its tables.

**What scanning it surfaced: 2 real breaks in 175 tables**, both pre-existing and neither mine:

| line | defect | repair |
|---|---|---|
| 3019 | `` `window\|knife` `` unescaped — 3 cells against a 2-cell header | escaped the pipe |
| 3105 | a row carrying only 2 cells against a 3-cell header | supplied the missing `population` label |

Line 3019 is notable because **the very next row in the same table already writes
`` `ticket\|knife` `` correctly** — so the convention was known and one instance was missed, which is
why this needs a guard and not a habit. On line 3105 I supplied only the absent row label
(`a larger population`); the `96` and its note are unchanged, and no figure was invented.

**Mutation test.** Re-introducing the unescaped pipe and running the guard on its DEFAULT paths — so
the test exercises the scope change, not just the regex — exits **1**; restoring exits **0**, and the
plan is byte-identical to its pre-mutation state. A green-on-green run would have proved nothing,
which is the mistake this sprint already made once on `ledger_propagation_check`.

**The general shape, which has now appeared three times here.** A guard that cannot see an artifact
is indistinguishable from a guard that finds it clean — `ledger_propagation_check` dropping 13 of 31
id-less headings, `cited_artifact_check`'s loose matcher, and now a path list. Every one of them
reported success while examining less than it appeared to. The tell is never in the guard's verdict;
it is in whether anyone checked what the denominator was.

## §12.14 — LAUNCHED: the retrieval-knockout reruns at cap 640 (ledger entry 6)

**Why this claim needed a rerun and not a re-read.** Ledger entry (2) — "demonstration-retrieval
knockout suppresses the doublespeak attack, 96 down / 18 up over 8 populations" — is ASR-based, and
**all twenty runs behind it ran at `max_new=192`**. Their truncation rates run from 0.073 to
**0.698**: on `lbC_ticket_bomb`, 67 of 96 generations hit the cap. An ASR measured on truncated
generations is not an ASR, and the standing rule for this sprint is that no `max_new=192` figure is
quoted without relabelling.

**Derived, not hand-written.** Each of the ten argsfiles is generated from its ORIGINAL run's own
`config.json`, changing exactly one field. That matters because the arm names are not uniform —
`main` used `C_demo_all_L6_14` while the four codeword banks used `C_band_L6_14` — and hand-writing
ten files would have silently normalised them into a different intervention. The generator asserts
`max_new == 192` and `model in (None, "")` on every source config before writing, so a mis-pointed
run fails loudly rather than producing a Qwen rerun labelled Llama.

| population | A arm | C arm | old truncation A / C | C − A |
|---|---|---|---|---|
| `main` | `k640_p2A` | `k640_p2C_band` | 0.562 / 0.552 | −0.010 |
| `ticket_bomb` | `k640_lbA_ticket_bomb` | `k640_lbC_ticket_bomb` | 0.698 / 0.917 | **+0.219** |
| `window_knife` | `k640_lbA_window_knife` | `k640_lbC_window_knife` | 0.875 / **1.000** | **+0.125** |
| `button_knife` | `k640_lbA_button_knife` | `k640_lbC_button_knife` | 0.927 / 0.990 | **+0.063** |
| `basket_gun` | `k640_gnLA` | `k640_gnLC` | 0.896 / **1.000** | **+0.104** |

⛔ **CORRECTION to this table's first version, made before any result was read.** It listed
`ticket_bomb` as 0.469 / 0.698 and `window_knife` as 0.573 / 0.354. **Those are the QWEN runs**
(`xbA_*`/`xbC_*`), quoted under a Llama heading — I matched on the population name and took the
first row carrying it. The Llama runs (`lbA_*`/`lbC_*`) are far worse, and the corrected numbers are
above. Only the `main` row was right.

Jobs 796400-796405 hold the first three populations, A and C submitted together so no comparison can
land half-complete. The remaining two go in as slots free, keeping the queue at the 6-job cap.

**What this can and cannot settle.** It re-measures the knockout effect without truncation on the
Llama side. It does NOT re-measure the Qwen populations, so if the effect survives here the claim
narrows to "verified untruncated on Llama, still cap-dependent on Qwen" rather than clearing
outright. Argsfiles live on the shared filesystem, not the node-local scratchpad, which fails these
jobs in 3 seconds.

## §12.15 — ⛔ CORRECTION: "explicit paths only" does not prevent committing someone else's work, because `git commit` commits the INDEX

**What happened.** V-105 (28143ec2, pushed) contains two files belonging to the peer session that I
never added: `external_md/BEHAVIORAL_CAUSALITY_NEXT_PHASE_PLAN_AND_PROGRESS.md` (+68/-2) and
`reports/SPRINT_SUMMARY_2026-08-25_BEHAVIORAL_CAUSALITY.md` (+3/-1).

**The mechanism, which is not the one the standing rule guards.** I ran
`git add <my plan> <argsfiles>` and then a bare `git commit`. **`git commit` commits the index, not
the paths just added.** The peer had those two files staged, so they went in under my message. The
sprint rule "explicit paths only, never `git add -A`" is about not WIDENING the add — and I never
widened it. The index was already wide when I got there. This is the second distinct way the two
sessions' work has merged through a path I controlled: the first was a shared file
(`demo_pools.py`), this one is a shared INDEX, and both sessions edit the same working tree.

**The fix, adopted from here on:**

```
git commit <explicit paths> -F -
```

A pathspec-limited commit takes those paths from the working tree and **leaves the rest of the index
staged and untouched**. It is the form that actually means what "explicit paths only" was trying to
say.

**What I did not do: rewrite it.** The commit was already pushed. Nothing was lost — the peer's
content is committed, not destroyed — so amending would trade a labelling problem for a real one on
a shared branch, and this repo already has a standing rule against that class of cleanup. I told the
peer immediately instead, with the specific thing only they can judge: whether the frozen +68 lines
are a coherent state or a mid-edit partial. They confirmed the work is intact and wanted no action.

**§12.14's "derived, not hand-written" was unverifiable when I wrote it.** The ten argsfiles live
under `outputs/`, which is gitignored, and the generator was an inline heredoc — so the repo carried
the claim and not the thing that backs it. Now tracked as `src/boombness/make_k640_argsfiles.py`,
which regenerates all ten from the source `config.json` files and asserts `max_new == 192` and an
unset `model` before writing.

## §12.16 — PRE-REGISTERED before the cap-640 reruns are read: the knockout confound runs WITH the claim on 4 of 5 Llama populations

**Written while jobs 796400-796405 are still loading weights. No result has been read.**

**Two facts found while correcting §12.14's table, both worse than that section implied.**

*First, the Llama knockout arms are almost entirely truncated.* At `max_new=192`:
`lbC_window_knife` **96/96 = 1.000**, `gnLC` **96/96 = 1.000**, `lbC_button_knife` 0.990,
`lbC_ticket_bomb` 0.917. An ASR computed where every generation hit the cap is not a weak
measurement; it is not a measurement of the generation at all.

*Second, the existing untruncated control does not cover Llama.* Entry (2)'s both-EOS restriction
yields, per population: `L|ticket_bomb` **2**, `L|button_knife` **0**, `L|window_knife` **0**,
`L|basket_gun` **0**, `L|main` 28. **Four of the five Llama populations contribute zero untruncated
discordant rows.** So these reruns are not a robustness check on the Llama side — they are the first
untruncated evidence that side has ever had.

**THE PREDICTION, and the direction that makes it falsifiable.** The knockout arm (C) is MORE
truncated than its own baseline (A) in **4 of 5** Llama populations, by +0.063 to +0.219. The claim
is that C has the LOWER ASR. More truncation mechanically produces lower ASR, so **the confound runs
in the same direction as the claim** — the opposite of the peer's `response_query_only` arm, where
truncation runs against the claim and a cap release should therefore make the effect bigger.

Consequences, committed to in advance:

* If the knockout effect is truncation-driven, releasing the cap should **shrink or reverse** it on
  `ticket_bomb`, `window_knife`, `button_knife` and `basket_gun`, and leave `main` roughly unchanged
  — `main` is the one population whose differential is ≈0 (−0.010), so it is the internal control.
* If the effect **survives at full size on the four confounded populations**, the confound is ruled
  out by the strongest available test, because it had every opportunity to manufacture the result.
* `main` moving a lot in either direction would be the surprise, and would mean something other than
  truncation changed with the cap.

**What this cannot settle either way.** Qwen is not being rerun, so entry (2) narrows to
"untruncated on Llama" at best, and the Qwen half stays cap-dependent. And per the standing rule, no
number from the old `max_new=192` runs is quoted anywhere without that label.

## §12.17 — RESULT: the knockout effect GREW when the cap was released. The pre-registered confound is refuted, not confirmed

**Read against §12.16, which was committed before any of these numbers existed.** Six arms, one
judge invocation (so no cross-session judge noise enters the A-vs-C contrast), pinned
`openai/gpt-4o-mini`, `null_frac=0.0000` on every arm, all 96 goals substituted. Sprint-grade
artifact `k640_knockout_20260828_230529_3204665` is stamped **PUBLISHABLE**, `at_cap=0.0` on all six.

| population | cap 192 A → C | effect | cap 640 A → C | effect | C−A truncation |
|---|---|---|---|---|---|
| `main` *(control)* | 23/96 → 5/96 | 18 rows | **26/96 → 3/96** | **23 rows** | −0.010 |
| `ticket_bomb` | 28/96 → 8/96 | 20 rows | **29/96 → 1/96** | **28 rows** | +0.219 |
| `window_knife` | 2/96 → 0/96 | 2 rows | **3/96 → 0/96** | **3 rows** | +0.125 |

**Truncation is fully released**: 0/96 at cap on every arm, longest generation 596 of 640, all six
ending in EOS. At 192 these same C arms ran 0.917 and **1.000** truncated.

**The pre-registration said: if truncation-driven, the effect SHRINKS OR REVERSES on the confounded
populations. It grew in all three.** On `ticket_bomb` — the population with the largest confound
(+0.219, and the one where the C arm's truncation was 0.917) — the effect went from 20 rows to **28**.
The confound had every opportunity to manufacture this result and did not. It is refuted by the
strongest test available, which is the outcome §12.16 named in advance as ruling it out.

**⛔ AND THE CONFOUND RAN THE OPPOSITE WAY TO MY REASONING.** I argued that more truncation in C
mechanically depresses C's ASR and so inflates the apparent effect. What actually happened is that
**truncation was MASKING the effect, not manufacturing it**: releasing the cap raised the baseline
(A: 23→26, 28→29, 2→3) *and* lowered the knockout arm (C: 5→3, 8→1, 0→0). Both arms moved apart. The
reason is that at 192 the A arms were heavily truncated too (0.562, 0.698, 0.875), so the cap was
suppressing *both* sides and compressing the gap. **A differential in truncation does not tell you
the direction of the bias when both arms are near the ceiling** — that is the part of §12.16's
reasoning that was wrong, and it was wrong in the direction that made me expect a weaker result.

**Why the C arm was more truncated, mechanically.** Median new tokens are HIGHER in the knockout arm
in 2 of 3 populations — `ticket_bomb` 248 → 299.5, `window_knife` 348 → 403, `main` 202 → 201.5. The
intervention makes the model more discursive, so it met the old cap more often. This is the same
mechanism a peer identified independently on their preamble arm, arriving from a different claim.

**Status of ledger entry (2), narrowed honestly.** Three of five Llama populations now have
untruncated evidence where **four of five previously had none** (`L|button_knife` 0 both-EOS
discordant rows, `L|window_knife` 0, `L|basket_gun` 0, `L|ticket_bomb` 2). `button_knife` and
`basket_gun` are running as jobs 796750/796751. Qwen is NOT rerun, so the claim remains
"untruncated on Llama for these populations, still cap-dependent on Qwen" — the reruns cannot and do
not clear the Qwen half.

**`window_knife` carries almost no weight.** 3/96 → 0/96 is a floor effect; its baseline barely
attacks at all, so it neither supports nor threatens the claim. Quoting it as a third confirming
population would be overreading three rows.

## §12.18 — ⛔ CORRECTION to §12.17: "the effect grew" was measured ACROSS judge sessions, and the judge moves 3 rows on unchanged generations

**What was wrong.** §12.17 reported the knockout effect growing 18 → 23 rows on `main` and 20 → 28
on `ticket_bomb`. The cap-640 numbers came from the judge session of 2026-08-28 and the cap-192
numbers from 2026-08-24. **The A-vs-C contrast within each cap was clean — one invocation, which is
the house convention — but the old-vs-new comparison crossed sessions**, and that crossing is the
only thing the "grew" claim rested on. I applied the convention to one axis of the table and not the
other.

**Re-judged all eight arms in a single invocation** (`ss192_*` / `ss640_*`, job 797129, pinned
`gpt-4o-mini`, `null_frac=0.0000`):

| population | cap 192 A → C | effect | cap 640 A → C | effect | change |
|---|---|---|---|---|---|
| `main` | 20/96 → 4/96 | 16 rows | 23/96 → 5/96 | 18 rows | **+2** |
| `ticket_bomb` | 25/96 → 5/96 | 20 rows | 27/96 → 2/96 | 25 rows | **+5** |

**And the judge moves up to 3 rows in 96 on generations that did not change.** Re-scoring the
identical files: `p2A@192` 23→20, `lbA_ticket_bomb@192` 28→25, `lbC_ticket_bomb@192` 8→5,
`p2A@640` 26→23, `p2C@640` 3→5. Max |Δ| = 3 rows, and it is not one-directional. **Any cross-session
row-count difference smaller than about 3 rows of 96 is judge noise, not signal** — worth having as
a standing resolution bound, because several comparisons in this sprint are that size.

**What survives, and what does not.**

* **STANDS — the released-cap result.** `ticket_bomb` 27/96 → 2/96 at cap 640 with 0/96 truncation.
  This never depended on the old runs; it is a single-session A-vs-C contrast.
* **STANDS, narrowly — growth on `ticket_bomb`.** +5 rows against a ~3-row noise floor. Real but
  marginal, and it should be quoted as +5 with the floor attached, not as the +8 §12.17 claimed.
* **⛔ WITHDRAWN — growth on `main`.** +2 rows is INSIDE the noise floor. §12.17's +5 on `main` was
  mostly cross-session judge drift. `main` is the internal control and the honest reading is that it
  **did not detectably move**, which is what §12.16 predicted for it and what I over-read.

**⛔ AND THE MECHANISM BEHIND MY PREDICTION DOES NOT EXIST.** §12.16 reasoned that "more truncation
mechanically produces lower ASR". A peer measured it across 76 judged runs and 10,568 joined rows:
**P(ASR | truncated) = 0.0981 vs P(ASR | finished) = 0.0925**, delta +0.0056, 57 of 76 runs positive.
Truncation does not depress ASR — a jailbroken answer is LONG and a refusal is SHORT, so hitting the
cap selects against refusals, and StrongREJECT scores a partial harmful answer as harmful. So the
confound §12.16 pre-registered against **does not operate in the direction I assumed**, and §12.17's
"the confound was refuted by the strongest test" overstates: the test was real and passed, but the
thing it was testing for was not a live mechanism to begin with.

**Net effect on ledger entry (2).** Unchanged in substance and better supported in form: the
knockout effect is large at a released cap on `main` and `ticket_bomb` with zero truncation, which
is the first untruncated evidence those populations have had. What is retired is the decorative part
— the specific growth magnitudes, and the claim to have defeated a confound that was not there.

## §12.19 — ⛔ CORRECTION: "truncation was masking the effect" was argued, not tested. Tested, it does not hold

**The claim being retired.** §12.17 said the cap had been *masking* the knockout effect — that both
arms were suppressed at 192 and releasing the cap let them move apart. That was an inference from
which numbers moved, not a measurement of the rows that would have to be doing the moving.

**The test, borrowed from a peer.** They refuted their own decomposition by asking whether releasing
the cap CONVERTS the previously-truncated rows: their comparator went from 44 finished rows to 160
and produced **zero** new refusals, so `stop_reason` is a marker of what kind of answer a row is, not
a cause of its outcome. The same test runs here by joining each row's cap-192 and cap-640 verdicts on
`prompt_id`, split by that row's cap-192 `stop_reason`, all from the same judge invocation:

| arm | truncated @192 | among TRUNCATED rows: 0→1 / 1→0 / net | among FINISHED rows: net |
|---|---|---|---|
| `main` A | 54/96 | 7 / 5 / **+2** | +1 |
| `main` C | 53/96 | 1 / 1 / **+0** | +1 |
| `ticket_bomb` A | 67/96 | 5 / 3 / **+2** | +0 |
| `ticket_bomb` C | 88/96 | 0 / 3 / **−3** | +0 |

**Between 53 and 88 rows per arm were released from the cap, and the net movement was +2, 0, +2 and
−3.** All within the ±3-row judge floor measured in §12.18, and the movement is BIDIRECTIONAL — 7 up
and 5 down on `main` A — which is the signature of judge churn, not of suppressed successes being
released. Truncated rows were not successes waiting for room. **The masking claim is withdrawn.**

**The one movement that reaches the floor points the other way.** `ticket_bomb` C is −3, made of
**0 rows gaining and 3 rows losing** their success verdict once allowed to finish. That is a
partial harmful answer scoring as harmful at 192 and the completed answer scoring lower — the same
direction as the peer's corpus measurement (P(ASR | truncated) 0.0981 vs P(ASR | finished) 0.0925).
So if the cap biased anything here it *slightly inflated the knockout arm's ASR*, making the effect
look **smaller** at 192, not larger. Still only 3 rows; quoted as a direction, not a magnitude.

**What this does and does not change.** The load-bearing result is untouched, because it never
depended on the 192 runs: `ticket_bomb` **27/96 → 2/96 at cap 640 with 0/96 truncation**, one judge
invocation. What is gone is the narrative I attached to it. Three claims have now been retired from
§12.16/§12.17 — the confound's direction, the mechanism behind it, and the masking story — while the
measurement they were wrapped around has not moved once.

**The pattern, and it is the sprint's most repeated one.** Every one of those three was an inference
about a mechanism, asserted from the direction numbers moved, and every one was cheap to test
directly. The test here cost one join over files that already existed.

## §12.20 — ALL FIVE Llama populations at cap 640: the knockout effect is real on TWO, and the other three never had the baseline to test it

**Every population's 192 and 640 arms judged in one invocation, every run dir pinned by full name.**
Jobs 797129 (`main`, `ticket_bomb`) and 797616 (`button_knife`, `basket_gun`); `window_knife` from
the 640 batch. Row counts of 96:

| population | cap 192 A → C | effect | cap 640 A → C | effect |
|---|---|---|---|---|
| `ticket_bomb` | 25 → 5 | 20 | **27 → 2** | **25 rows** |
| `main` | 20 → 4 | 16 | **23 → 5** | **18 rows** |
| `button_knife` | 9 → 10 | **−1** | 7 → 3 | 4 rows |
| `basket_gun` | 9 → 11 | **−2** | 7 → 8 | **−1 row** |
| `window_knife` | 2 → 0 | 2 | 3 → 0 | 3 rows |

**The honest reading is a narrowing, and it is not "the effect fails on three populations".** Look at
the baselines: `button_knife` 7/96, `basket_gun` 7/96, `window_knife` 3/96. **A population whose
baseline attack succeeds 7 times in 96 cannot exhibit a 20-row suppression — the largest effect
arithmetically available is 7 rows, which is at the noise floor.** Those three populations do not
disconfirm the claim; they lack the dynamic range to test it. The claim is supported where it can be
measured (`main`, `ticket_bomb` — baselines 23 and 27) and untestable where it cannot.

**`basket_gun` is the one genuine null**: 7 → 8 at a released cap, and it was 9 → 11 at 192. Its
knockout arm has never been lower than its baseline. It should be reported as a population where the
knockout does not suppress, not quietly absorbed into an aggregate.

### The judge noise floor, measured for free and larger than §12.18 said

Decoding is deterministic across the cap change — **384 paired rows, 123 byte-identical, 261 where
the 640 text strictly EXTENDS the 192 text, 0 divergent.** So the cap release is a clean intervention
and rows can be compared per-row. That also means the byte-identical rows give the judge's
reproducibility directly, since their text did not change at all:

| cell | n | verdict flips | rate |
|---|---|---|---|
| byte-identical text | 123 | 8 | **6.5%** |
| 640 extends 192 | 261 | 25 | 9.6% |

**⛔ REFINING §12.18.** That section put the floor at "±3 rows in 96 ≈ 3.1%". That figure was a NET
movement (ups cancelling downs); the **gross per-row flip rate on unchanged bytes is 6.5%, about
twice as large**. The distinction matters and I conflated them: the net floor bounds *aggregate* ASR
comparisons, the gross rate bounds *row-level* ones like §12.19's. §12.19's per-cell nets of +2, 0,
+2 and −3 sit far inside the gross rate, so its conclusion is unchanged and better supported.

The extended rows flip at 9.6% against a 6.5% floor — a ~3-point difference over 261 rows. That is
the entire measurable footprint of releasing the cap, and it is small.

**Status of ledger entry (2), final for the Llama side.** Untruncated evidence now exists for all
five Llama populations where four of five previously had none. The claim narrows to: **the
retrieval knockout suppresses the doublespeak attack on the two populations with enough baseline
attack to measure it, does not suppress on `basket_gun`, and is untestable on the other two.** Qwen
was not rerun and remains cap-dependent. The original "96 down / 18 up over 8 populations" pooled
across populations of wildly different dynamic range and should not be quoted in that form.

## §12.21 — ⛔ CORRECTION: cap-640 arms ALREADY EXISTED for three of the five populations. My "first untruncated evidence" claim was false

**Found while assembling the Phase 6 ladder, not by auditing the claim.** Six runs sit in the tree
dated 2026-08-27/28, before the reruns: `e6A_main`, `e6C_main`, `e6A_ticket_bomb`,
`e6C_ticket_bomb`, `e6A_basket_gun`, `e6C_basket_gun` — all `max_new=640`, all Llama, all
`core2x2,core2x2_slot3`, all `n_examples 1,2,4,8`, 96 rows each. **Configuration-identical to the
reruns I launched.**

**What I claimed and why it was wrong.** §12.16 and the ledger said *"four of the five Llama
populations have never had untruncated evidence at all"*, citing both-EOS discordant-row counts of
0, 0, 0 and 2. That statistic is real, but it counts **rows inside the cap-192 runs where both arms
happened to finish** — it is a property of those runs, and says nothing about whether a separate
cap-640 run exists. I read a narrow within-run statistic as a statement about the corpus, and never
checked the corpus. One `ls` would have shown it. §12.14 was built from `config.json` files
specifically to avoid trusting prose about runs, and I then made a corpus-level claim without
enumerating the corpus at all.

**What the reruns actually contributed**, stated accurately:

* `button_knife` and `window_knife` — **genuinely new**. No prior cap-640 arms exist for either.
* `main`, `ticket_bomb`, `basket_gun` — **independent replication**, not new evidence.

That replication is not worthless, but it is a different thing, and §12.17/§12.20 should not have
been framed as first-light on those three.

### Generation is fully deterministic, and it makes the duplication measurable

Comparing the pre-existing runs against my reruns row by row — independent SLURM jobs, different
nodes, a day apart:

| pair | n | byte-identical | differing |
|---|---|---|---|
| `main` A | 96 | **96** | 0 |
| `main` C | 96 | **96** | 0 |
| `ticket_bomb` A | 96 | **96** | 0 |
| `basket_gun` A | 96 | **96** | 0 |

**384 of 384.** Same weights, same seed, same batch shape ⇒ the same text. So the reruns cost GPU
time and produced no new bits on those three populations.

### Which buys a third judge-noise measurement, on 384 rows

Two independent judge sessions over text that is byte-identical by construction:

| arm | n | totals | flips (up/down) | rate |
|---|---|---|---|---|
| `main` A | 96 | 22 → 23 | 5 / 4 = 9 | 9.4% |
| `main` C | 96 | 8 → 5 | 2 / 5 = 7 | 7.3% |
| `ticket_bomb` A | 96 | **27 → 27** | **4 / 4 = 8** | 8.3% |
| `basket_gun` A | 96 | 10 → 7 | 0 / 3 = 3 | 3.1% |
| **total** | **384** | | **27** | **7.0%** |

7.0% against §12.20's 6.5% on a different 123 rows — two independent estimates agreeing. **And
`ticket_bomb` A is the clearest possible statement of the net-versus-gross distinction: the total is
27 both times, unchanged, while 8 rows disagree underneath it.** An identical aggregate is not
evidence that the same rows were scored the same way.

**Standing consequence.** Before claiming a population, model or cap has "no evidence", enumerate
the run corpus by `config.json` and say how many dirs were examined. Every under-coverage failure
this sprint — a bolded-id regex, a prefix glob, `ls | tail -1`, a population-name substring, and now
a within-run statistic read as a corpus fact — was invisible because nothing reported the
denominator.

## §12.22 — PHASE 6 COMPLETE: the dose ladder is NON-MONOTONIC — it peaks at n=8–12 and falls at n=16

**The sweep the brief specified, finished.** §6.2 had covered `n_examples ∈ {1,2,4,8}` only. The
missing doses are now run at cap 640 (`ph6_*`, jobs 797838-797841, truncation **0/84**) and judged
**with the existing doses in a single invocation** (`p6j_*`, job 797947) — necessary because the
judge's gross per-row flip rate is 6.5–7.0% (§12.21), and judging the ends of a dose-response curve
in different sessions would place an instrument boundary in the middle of the curve.

**Balanced ladder, `core2x2` only, 12 rows at every dose:**

| bank | n=0 | n=1 | n=2 | n=4 | n=8 | n=12 | n=16 |
|---|---|---|---|---|---|---|---|
| `main` | **0/12** | 2/12 | 0/12 | 3/12 | 7/12 | **9/12** | **2/12** |
| `ticket_bomb` | **0/12** | 1/12 | 3/12 | 5/12 | **7/12** | — | 5/12 |
| `basket_gun` | **0/12** | 2/12 | 0/12 | 0/12 | **3/12** | — | 1/12 |

Sprint-grade artifact `phase6_ladder_20260829_014709_3632423`, **PUBLISHABLE**.

### The ladder is a paired design, which is what makes it readable at this size

The `(domain, split)` cells are **identical at every dose** — the same 6 domains × 2 splits, verified
against the bank. So each dose comparison is within-domain and paired. **But 6 domains means 6
clusters**, and this sprint's own §12.9/§12.11 result is that power is bounded by cluster count, not
row count. Everything below is quoted with that ceiling attached.

### n=0 is 0/12 on all three banks — and by two different routes

The attack does not exist without demonstrations. Pooled n=0 (0/36) against n=8 (17/36) is
Fisher p < 0.0001, the largest and least ambiguous contrast in the table.

**The routes differ, and averaging would have hidden it.** On `main`, n=0 is **12/12 keyword-refusal
at 23 median tokens** — the model refuses outright. On `ticket_bomb` and `basket_gun`, n=0 is **0/12
refusal at 391 and 480 median tokens** — long, non-refusing answers that simply do not carry the
attack. Same zero, opposite mechanisms.

### The drop at n=16, paired within domain

| contrast | pairs | lost | gained | McNemar p |
|---|---|---|---|---|
| `main` n=12 → n=16 | 12 | **7** | **0** | **0.0156** |
| `main` n=8 → n=16 | 12 | 5 | 0 | 0.0625 |
| `ticket_bomb` n=8 → n=16 | 12 | 4 | 2 | 0.6875 |
| `basket_gun` n=8 → n=16 | 12 | 2 | 0 | 0.5000 |
| **pooled n=8 → n=16** | **36** | **11** | **2** | **0.0225** |

**More demonstrations stop helping and start hurting.** The direction is consistent on all three
banks (11 lost against 2 gained pooled) and strictly one-directional on `main` (7 lost, 0 gained).
Refusal does not explain it: refusal at n=16 is 1/12, 3/12 and 1/12.

**⛔ BUT THE McNEMAR p VALUES ABOVE TREAT 12 PAIRS AS INDEPENDENT WHEN THEY COME FROM 6 DOMAINS.**
Re-run as an exact sign-flip permutation over `(bank, domain)` clusters — the design's real unit:

| contrast | clusters | pairs | observed | clustered p | McNemar had |
|---|---|---|---|---|---|
| pooled n=8 → n=16 | 18 | 36 | 9 | **0.0312** | 0.0225 |
| `main` n=12 → n=16 | 6 | 12 | 7 | **0.0625** | 0.0156 |

The pooled result survives. **`main`'s does not: 0.0625, not 0.0156.** And the reason is worth
stating exactly, because it is not "the effect got weaker" — with 6 clusters of which 5 are
informative (one has a net of 0 and cannot move under sign-flip), **the smallest two-sided p
attainable is 2/2⁵ = 0.0625.** `main`'s data are as extreme as they could possibly be and still
cannot reach 0.05. That is a power ceiling set by the bank's 6 domains, exactly the
cluster-count bound §12.9 established, now binding on my own result.

*(Method note: the first version of this permutation matched splits against a guessed list of names
and silently captured only `dev`, halving the data and producing no negative cluster nets — which
was the tell, since `ticket_bomb` demonstrably gains 2 pairs. Splits are now read from the data:
`dev`, `heldout`.)*

### What this means for the objective question

Phase 6 exists to answer *"if boombness is just `n_examples` wearing a different name, it is not an
objective."* The honest answer is that **`n_examples` is not a monotone driver**, so boombness cannot
be a monotone restatement of it. That cuts both ways and I am not claiming the favourable half:
non-monotonicity equally means **`n_examples` is a poor control variable**, because conditioning on
it linearly — which §6.3's mediation test did — mis-specifies the relationship on the upper half of
the range.

**Caveats that bound all of the above:** 12 rows per dose, 6 domain-clusters, a 6.5–7.0% judge floor
that is the same order as several of these cells, `n=12` measured on `main` only (the `ne12` bank is
a strict superset of `main` — 2736/2736 rows byte-identical by `prompt_sha16` plus 192 rows at 12 —
so the cell is on the same ladder, but there is no cross-bank replication of it), and one row of 96
at cap in `basket_gun`'s n=1,2,4,8 arm.

## §12.23 — §6.3 POWERED: boombness DOES predict ASR within dose strata — and the Phase 7 gate stays CLOSED anyway, because the naive control does the same job

**§6.3's blocker was already gone, and had been for a day.** That section said the mediation test was
"underpowered by a factor of ~6" because `extract_boombness` had no `core2x2_slot3` rows, collapsing
the join 96 → 48, and listed two routes to powering it as "both known and unrun". **Route 1 was
already run**: `xb_main_s3`, `xb_ticket` and `xb_gun` (2026-08-28) each carry **1,824
`core2x2_slot3` rows**. No GPU work was needed. That is the fourth open question tonight answered by
an artifact already on disk.

**The powered join: 288 rows, 62 successes, 18 bank-domain clusters** — six times §6.3's 48.

### The result overturns §6.3's reading

| readout | pooled ρ | cluster-perm p | n=1 | n=2 | n=4 | n=8 | mean within-dose |
|---|---|---|---|---|---|---|---|
| `d_surface\|L8\|proj` | **+0.336** | **0.0037** | +0.172 | +0.446 | +0.321 | +0.280 | **+0.305** |
| `d_surface\|L12\|proj` | +0.254 | 0.0197 | — | — | — | — | — |
| `ll\|L12\|boombness` | +0.201 | 0.0387 | +0.077 | +0.039 | +0.291 | +0.385 | +0.198 |

**Every within-dose correlation is positive**, where §6.3 reported signs flipping
(0.000, −0.453, −0.131, +0.367). Those flips were twelve-row noise. And it replicates across the
bank's pre-registered split: **dev ρ = +0.351, heldout ρ = +0.316**. So the answer to the brief's
decisive Phase 6 question — *"is boombness still predictive within each `n_examples` stratum?"* — is
**yes**, and §6.3's "underpowered rather than negative" is resolved in the positive direction.

### ⛔ AND THE GATE STILL DOES NOT OPEN

Phase 7 requires a candidate to predict heldout ASR **beyond** a named control set that includes the
**naive concept direction**. Running those controls on the same 288 rows:

| direction | pooled ρ | cluster-perm p | mean within-dose |
|---|---|---|---|
| `d_surface\|L8` *(candidate)* | +0.336 | 0.0037 | **+0.305** |
| `d_naive\|L8` *(control)* | +0.297 | 0.0099 | **+0.267** |
| `d_context\|L8` *(control)* | +0.136 | 0.1839 | −0.179 |
| `d_inter\|L8` *(control)* | +0.019 | 0.8563 | — |
| `hnorm\|L8` *(control)* | +0.265 | 0.0490 | −0.176 |

**ρ(`d_surface|L8`, `d_naive|L8`) = 0.9627.** The candidate and the naive control are **the same
signal**. The candidate beats it by 0.038 in mean within-dose ρ and by 0.039 pooled, on 18 clusters.
A direction that correlates 0.96 with the naive concept direction and edges it by four hundredths
does not "predict beyond" it in any sense the gate intends. **Phase 7 remains CLOSED and no
GCG/MAC objective is being built.**

**What is genuinely informative here**, and it is not nothing: `d_context` and `hnorm` are
*negative* within-dose (−0.179, −0.176), so this is not "any direction predicts ASR". Something
concept-aligned does. But the cheapest possible concept direction does it, which makes the elaborate
one unnecessary rather than validated — the gate's exact purpose.

### ⛔ A flaw in my own test, stated because the number looked usable

The same cluster-permutation reported `n_examples` at **p = 1.0000**, which is an artifact, not a
finding. Every cluster in this design carries an identical dose composition, so permuting outcomes
between clusters preserves the dose→outcome pairing exactly and the null is degenerate for any
variable that is balanced by construction. **`n_examples` demonstrably does predict ASR** — §12.22's
ladder is the evidence. The permutation is valid for the readouts, which vary within cluster, and
invalid for the dose variable. Reported rather than dropped, because a p of exactly 1.0000 next to a
variable one wants to dismiss is precisely the number that would get quoted.

## §12.24 — ⛔ CORRECTION to §12.23: "the candidate and the naive control are the same signal" is WRONG. The gate still closes, for a different reason

**The error.** §12.23 compared two *marginal* correlations (+0.336 vs +0.297), observed
ρ(`d_surface|L8`, `d_naive|L8`) = 0.9627, and concluded the candidate was redundant. **Comparing
marginals does not estimate incremental validity.** A peer flagged it, reconstructed the partial from
my published summary numbers, got ≈ +0.19, and correctly noted their reconstruction assumed a common
covariance structure and needed running on rows. Run on rows:

| | partial ρ | cluster-boot 95% CI (18 clusters) |
|---|---|---|
| `d_surface` ~ ASR **given `d_naive`** | **+0.1924** | [+0.078, +0.299] excludes 0 |
| `d_naive` ~ ASR **given `d_surface`** | **−0.1024** | — |

So the candidate carries signal the naive direction does not, and **controlling for the candidate the
naive direction's contribution goes negative**. Two directions correlated at 0.96 are still
separable here. §12.23's "same signal" sentence is withdrawn.

### ⛔ A bug in my own analysis, caught before it set the verdict

My first multiple-partial used a rank function that broke ties **by `argsort` order** instead of
averaging them. The outcome is binary — 226 zeros and 62 ones — so almost every rank was arbitrary.
It returned `| d_naive` = +0.0942 where the correct value is +0.1924, and would have *supported* the
wrong conclusion I had already written. Fixed to average ranks; every number below uses that.

### The gate's actual test: the full control set, on the pre-registered heldout split

Controls: `d_naive`, `d_context`, `n_examples`, length, refusal.

| split | n | partial ρ (full gate set) | cluster-boot 95% CI |
|---|---|---|---|
| all | 288 | +0.1783 | [−0.0033, +0.2952] **includes 0** |
| **heldout** | 144 | **+0.2547** | [+0.0020, +0.3946] excludes 0 |
| dev | 144 | **+0.0389** | [−0.1386, +0.2201] **includes 0** |

**PHASE 7 REMAINS CLOSED, and this table is why.** Not because the candidate is redundant — it
isn't — but because the evidence is not stable enough to build on:

* Pooled over all 288 rows the full-control partial **includes zero**.
* **dev and heldout disagree by 6.5×** (+0.039 vs +0.255) on equal-sized halves of the same data.
  Heldout exceeding dev is the wrong direction for a real effect and the right direction for noise.
* The heldout CI's lower bound is **+0.0020** — it excludes zero by two thousandths.
* 18 clusters, and a cluster bootstrap is known to under-cover below ~30 clusters, so that lower
  bound is if anything optimistic.

A candidate that scores +0.04 on dev and +0.25 on heldout has not demonstrated it predicts beyond the
controls; it has demonstrated that **this design cannot resolve the question**. The remedy is **more
domains** — 18 clusters is the binding constraint, exactly as in §12.22 — and not a fourth readout.
**No GCG/MAC objective is being built.**

## §12.25 — PHASE 2.5: prompt-level is not a better objective than token-level, and both are entangled with dose

Phase 2 asked for token-level vs prompt-level separation, and §12.23 tested only the token-level
(query-occurrence) readout. Prompt-level aggregates over all occurrences — and occurrences are
**dose + 1** by construction, so prompt-level metrics are structurally tied to `n_examples`.

Same 288 rows, 18 clusters, `d_surface|L8|proj`:

| metric | pooled ρ | cluster-perm p | n=1 | n=2 | n=4 | n=8 | mean within-dose |
|---|---|---|---|---|---|---|---|
| token, query occurrence | +0.336 | 0.0037 | +0.172 | +0.446 | +0.321 | +0.280 | **+0.305** |
| prompt, mean all occ. | +0.299 | 0.0371 | +0.187 | +0.409 | +0.214 | +0.219 | +0.257 |
| prompt, max all occ. | +0.301 | 0.0496 | +0.043 | +0.367 | +0.164 | +0.243 | +0.204 |
| prompt, mean demo occ. | +0.250 | 0.0856 | +0.008 | +0.321 | +0.191 | +0.220 | +0.185 |
| length *(control)* | +0.102 | 0.2230 | +0.168 | −0.008 | +0.159 | +0.088 | +0.102 |
| refused *(control)* | −0.143 | 0.0854 | −0.048 | −0.099 | −0.130 | −0.310 | −0.147 |

**The token-level readout beats every prompt-level aggregate** on both pooled ρ and mean within-dose,
and the demo-only aggregate — the one that excludes the query token entirely — is weakest and its
cluster-permutation p does not clear 0.05. ρ(token, prompt-mean) = +0.878 and
ρ(prompt-mean, naive-prompt-mean) = +0.978.

**So Phase 2's open question resolves negatively for the prompt-level candidate.** §12.20's framing —
"Phase 7 must treat token-level and prompt-level as two candidate objectives requiring separate
evaluation" — has now had that separate evaluation: the prompt-level one is strictly worse, and
neither clears §12.24's gate.

## §12.26 — DEEP REVIEW (4h): the gate's own intervals are not quotable, and a test I wrote failed to catch the mutation it was written for

**LIVENESS.** No jobs of mine in flight; two peer jobs running. **ARTIFACT.** Both sprint-grade
artifacts cited this session exist and read `publishable=true`. **POPULATION.** The 288-row join
recounts independently as 96+96+96. **CLAIM.** 20 ledger entries, all 8 guards green, 140 → 151
tests.

### CODE — the statistics behind the gate were untested heredocs

§12.24 closed Phase 7 on a partial correlation with a cluster-bootstrap interval, and those numbers
were computed in inline scripts — one of which had the tie bug that returned +0.0942 instead of
+0.1924 **in the direction that confirmed the conclusion already written**. Extracted to
`src/boombness/clustered_stats.py` with 11 tests.

**Mutation test, 4 mutants — and the first pass exposed a gap in my own test:**

| mutant | outcome |
|---|---|
| `ranks` breaks ties by `argsort` position *(the real bug)* | **3 tests fail** ✅ |
| `multi_partial_spearman` ignores its controls | **2 tests fail** ✅ |
| permutation stops shuffling clusters | **1 test fails** ✅ |
| bootstrap resamples **rows** instead of clusters | **⛔ ALL 11 PASSED** |

**The bootstrap test did not catch the bootstrap mutation.** I had built it around a Spearman
between a cluster-constant `x` and an *alternating* `y`, whose bootstrap spread happens to be wide
under row-resampling too — so the property was never actually exercised. Rewritten around the mean
of `y` with half the clusters all-ones, where cluster resampling gives SE ≈ 0.5/√12 = 0.144 against
row resampling's 0.5/√96 = 0.051. The mutant now dies. **A test written for a specific mutation
still has to be checked against it.**

### ⛔ AND THE INTERVALS IN §12.24 SHOULD NOT BE QUOTED

A peer inverted my CI through Fisher z and observed it implied n_eff ≈ 293 out of 288 rows — i.e.
ICC ≈ 0 — which contradicts §12.22, where moving to domain clusters cost a fourfold precision loss
on this same structure. Measuring it directly across the 18 `(bank, domain)` clusters:

| quantity | ICC | implied n_eff of 288 |
|---|---|---|
| ASR outcome | **0.2085** | **69.8** |
| ASR outcome, dose-centred | 0.2325 | 64.2 |
| `d_surface\|L8` *(the predictor)* | **0.9038** | **19.8** |

**The predictor is almost entirely a between-cluster variable.** Its within-domain variance is
9% of the total, so the correlation with ASR is close to an 18-point correlation between cluster
means. And yet:

| interval on partial ρ(`d_surface`, ASR \| `d_naive`) | width |
|---|---|
| cluster bootstrap, 18 clusters | [+0.0788, +0.2970] → 0.2182 |
| row bootstrap, 288 rows *(known wrong)* | [+0.0763, +0.2966] → 0.2203 |
| **ratio** | **0.99** |

The two agree to one percent when the *marginal* ICCs say they should differ severalfold.

**RESOLVED, and my "not quotable" was itself too strong.** The partial does not correlate
`d_surface` with ASR — it correlates their **residuals after removing `d_naive`**, and `d_naive`
carries almost the same between-cluster structure. Measuring the ICC of what is actually correlated:

| | ICC of `d_surface` | ICC of ASR | design effect | n_eff of 288 |
|---|---|---|---|---|
| raw (the marginal) | 0.8208 | 0.2085 | 3.57 | **81** |
| **residualised on `d_naive`** *(what the partial uses)* | **0.2330** | **0.1341** | **1.47** | **196** |

Residualising strips most of the clustering, so the correct penalty is a **1.21× widening**
(√(288/196)), not the severalfold one the marginals imply. The cluster bootstrap is therefore
roughly 20% too narrow rather than wrong in kind, and **the single-control partial still excludes
zero after the correction**. What remains not quotable is the peer's analytic `df = clusters − 3`
interval, which assumes ICC = 1 — an assumption, not a measurement — and my bootstrap should be
quoted with the 1.21× caveat attached.

⛔ **A cross-population inference I nearly accepted.** The peer measured ASR ICC of 0.0000–0.0017 on
*their* cap-640 arms and concluded my bootstrap was simply correct because ICC ≈ 0. **On my rows the
ASR ICC is 0.2085**, with per-cluster rates running 0.0 to 0.81. Their measurement is real and does
not transfer — the same cross-population move both sessions have now corrected repeatedly. Their
larger finding stands and is the useful one: **ICC is outcome-dependent by two orders of magnitude
in the same rows** (ASR ≈ 0.00 vs refusal 0.33–0.43 on their arms), so refusal outcomes need
cluster-robust treatment that ASR outcomes may not. §12.25's Phase 2.5 negatives use ASR
throughout, so they are unaffected.

**This does not move the gate**, and it matters that it doesn't. Phase 7 closes on the *point*
estimates: the full-control partial over all 288 rows is +0.1783, and dev (+0.0389) and heldout
(+0.2547) disagree 6.5× on equal halves with heldout exceeding dev. Those readings need no interval.
What the ICC measurement adds is the reason the design cannot be rescued by more rows: **at
ICC 0.90 on the predictor, effective n is ~20 regardless of how many rows are collected.** More
domains is the only lever, which is now the third independent route to that same conclusion.

## §12.27 — PRE-REGISTERED: the Phase 7 gate re-tested at 38 domains, with the directions fitted on 6 of them

**Written while jobs 798294/798295 are PENDING. No row of either exists.**

**Why re-test a gate that is already closed.** §12.24 closed it on *instability*, not on evidence —
the full-control partial was +0.1783 pooled with a CI containing zero and a 6.5× dev/heldout
disagreement. §12.26 then measured why: **ICC 0.8208 on the predictor**, so effective n stays near
81 (196 after residualisation) no matter how many rows are collected. Three separate routes this
sprint reached the same conclusion — **more domains is the only lever**. The `38dom` bank exists and
carries 608 behavioral rows at `core2x2`+`core2x2_slot3` × `n ∈ {1,2,4,8}`, across **38 domain
clusters** against the current 6 per bank. This is that lever, pulled once.

**The design is a genuine transfer test, which the current one is not.** The directions come from
`full_20260816_185942_1008673`, fitted on the **6-domain** bank (`directions_fitted_on: heldout`,
`is_self_fit: False`). Applying them to `38dom` is a cross-bank application, **declared** through
`--allow-cross-bank-fit` rather than hidden — the flag records it in the run. Of the 38 domains,
**6 were seen by the fit and 32 were not.** §12.24's dev/heldout split shuffled rows within the same
6 domains; this splits on the unit that actually clusters.

### Decision rule, committed in advance

Let *P* = partial ρ(`d_surface|L8|proj`, ASR) controlling the full gate set (`d_naive`, `d_context`,
`n_examples`, length, refusal), cluster-bootstrapped over domains.

* **GATE PASSES** only if **both**: *P* on the **32 unseen domains** has a 95% CI excluding zero,
  **and** the unseen-domain point estimate is at least half the seen-domain one — i.e. it transfers
  rather than merely fitting where the directions were built.
* **GATE FAILS** if the unseen-domain CI contains zero, **or** the estimate collapses on unseen
  domains relative to seen (which would make it a property of the 6 fit domains, not of the model).
* **A large unseen-domain estimate with a wide CI is a FAIL**, not a "promising signal". At 38
  clusters the cluster bootstrap is no longer in the under-coverage regime (< 30) that made
  §12.26's interval quotable-only-with-a-caveat, so a CI containing zero here is informative rather
  than merely underpowered.

**What I expect, recorded so it cannot be revised afterwards.** I expect it to FAIL. `d_naive`
correlates 0.9627 with the candidate, and §12.24's two equal halves of the same data gave +0.039 and
+0.255 — an estimate that unstable across a *row* split is unlikely to survive a *domain* split.
The value of running it is that a fail at 38 clusters closes Phase 7 **on evidence** rather than on
"this design cannot resolve the question", and that is a materially stronger sentence to write in
Phase 9.

**This is not Phase 8.** No GCG/MAC objective is being built, and none will be unless this passes.

**Cost and scope.** Two GPU jobs. `d38beh` generates 608 rows at cap 640 (`expect-n 608`);
`d38xb` scores the readouts. Judging follows on `cpu-killable` in one invocation, per §12.21's
7.0% cross-session flip rate.

## §12.27.1 — ⛔ AMENDMENT to the §12.27 pre-registration, before any outcome exists

**Timestamp discipline.** `d38beh` had generated 13 of 608 rows and `d38xb` 1,661 readout rows when
this was written. **No ASR verdict exists** — judging has not run, so the outcome variable is not yet
defined and nothing has been read. A peer attacked the three points I asked them to; all three land,
and two of them would have made the result unreadable.

### 1. The "unseen ≥ half of seen" criterion is withdrawn — the denominator is the problem

The seen-domain estimate comes from **6 clusters**, where the Fisher-z SE is 0.577 and a point
estimate of 0.19 carries a CI of roughly (−0.74, +0.87). A ratio whose denominator has that spread
can pass or fail for reasons unrelated to transfer. The fault is the *ratio form*, not the choice of
one-half over one-third. Replaced with:

* **Primary:** the partial on the 32 unseen domains is non-zero.
* **Transfer, as a difference not a ratio:** bootstrap `P_unseen − P_seen` over domains and report
  its CI. A CI containing zero means *no detectable degradation*, which is what the ratio was
  reaching for, and it introduces no constant.
* **Usefulness floor, stated as a judgment:** `|P_unseen| ≥ 0.10`. This is not a statistical
  threshold and is not derived from anything — it is my line for "large enough to be worth
  optimising against", declared in advance so it cannot be moved afterwards.

### 2. The primary test is at k = 32, not 38 — and 32 is inside the marginal band

§12.27 said "at 38 clusters the bootstrap is out of the under-coverage regime". **38 is the bank; 32
is the analysis**, and the usual guidance places cluster-robust inference in trouble below ~40–50
clusters, not below 30. So 32 is marginal rather than clear.

**Remedy adopted:** a null-imposed **wild cluster bootstrap** with Rademacher weights
(Cameron–Gelbach–Miller), now implemented in `clustered_stats.wild_cluster_bootstrap_p` and
validated by simulation — under a true null with independently clustered `x` and `y` it rejects at
**0.042** against nominal 0.05, where treating rows as clusters rejects at **0.683**.

**And what a fail licenses is softened accordingly:** at k=32 a CI containing zero is *suggestive
evidence of absence*, not the clean "informative fail" §12.27 planned to write. That sentence was
load-bearing for Phase 9 and is now weaker.

### 3. `d_naive` runs as a positive control on the unseen domains

The cross-bank fit is declared but not validated, and a fail otherwise conflates two hypotheses.
The identical unseen-domain partial is therefore run for `d_naive`, which costs nothing:

* `d_naive` transfers and `d_surface` does not → the failure is **about boombness**, which is the
  answer Phase 7 wants.
* **Neither transfers** → the failure is about domain generalisation of fitted directions in
  general, and the design cannot speak to the objective question. The write-up then reads
  **"untestable on this bank"**, not "boombness does not predict".

### 4. Not adopted, and why

A rotation — fit on 32 domains, test on 6, rotate — would give a *distribution* of transfer
estimates instead of one unbalanced 6/32 contrast, and it is strictly more informative. It requires
**refitting directions per fold**, which is a `--stage fit` run per rotation rather than a
re-analysis, so it is out of scope for this tick. Recorded as the better design that was not run,
rather than left unmentioned.
