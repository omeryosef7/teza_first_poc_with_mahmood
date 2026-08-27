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

**This is a within-row natural experiment with no confound at all.** The right test is McNemar on
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

### Result —  is lexically clean

**23 of 24 banks pass**, on 384–640 complete families each. The 24th, `phase_d`, has **0 core-2×2
rows by construction** (it is the single-condition aggressiveness bank), so it is not a failure.

| measurement | result | reading |
|---|---|---|
| ** pairs byte-identical after masking** | **100 % on 23/24 banks** | the contrast carries no topic, domain or valence |
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
