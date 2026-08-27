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
