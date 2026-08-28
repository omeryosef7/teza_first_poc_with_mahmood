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
| **`window|knife` installs and still scores 0.042** | established on **one** bank (§5.13) |
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
| **96** | **does not exist** on this bank/condition |

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
