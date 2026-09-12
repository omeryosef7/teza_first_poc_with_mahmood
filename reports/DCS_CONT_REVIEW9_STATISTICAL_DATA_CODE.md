# DCS-CONT REVIEW-9 — STATISTICAL / DATA / CODE

**Target:** claim **A17**, entered in `CONT-ENTRY 143`–`145` of
`external_md/DCS_BOMBNESS_REPRESENTATION_TO_CAUSAL_ASR_CONTINUATION_20260910.md` and recorded in
`reports/DCS_CONT_CLAIM_TABLE.md`. Script `scripts/dcs_cont_oneswitch.py`; artifacts
`reports/DCS_CONT_ONESWITCH_button.json`, `reports/DCS_CONT_ONESWITCH_basket.json`.

**Method.** Every number below was recomputed from `results.jsonl` + `gens.jsonl` with independent
code that does **not** import `dcs_cont_oneswitch.py`, `dcs_cont_scope.py` or
`dcs_succ_concept_presence.py` (the 44-term lexicon was re-transcribed by hand and the CR-002 regexes
read from the frozen config). Python:
`/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`. Nothing is taken from the
entries' prose.

---

## SUMMARY OF FINDINGS

**Headline verdict: A17's *proposition* survives. A17's *numbers, its confound analysis and its
replication rhetoric* do not.**

The strictly-proportional one-switch account is excluded on button and basket under every test I
could construct — percentile bootstrap, log-scale bootstrap, exact conditional binomial on discordant
pairs, cluster-robust ratio-of-ratios, six alternative content rules, slot leave-one-out, domain
leave-one-out. That part is real and I could not break it.

But the **1.333 / 1.357 excess that the entries lead with is entirely mechanical.** `CONT-ENTRY 145`
identified one mechanical channel (refusal opportunity, factor 1.081 / 1.011) and declared A17
survived it. There is a **second, larger channel it never looked at**: the CR-002 `SCOPE` clause is a
disclaimer detector, and the knockout suppresses disclaimers. Removing **both** channels leaves
**button 28/28 = 1.000 [0.633, 1.632]** and **basket 18/17 = 1.059 [0.583, 1.917]**.

### CONFIRMED DEFECTS

| # | finding | magnitude |
|---|---|---|
| **D1** | **A second mechanical confound, larger than the one `CONT-ENTRY 145` analysed, is unstated.** CR-002's `SCOPE` veto (`mock\|fake\|prop\|scene\|film\|…\|harmless\|non-explosive\|not a real\|disposal\|containment`) fires **7× on control candidates and once on knockout candidates** (pooled Fisher **p = 0.023**). Before the veto the ratios are **33/28 = 1.179** (button) and **19/17 = 1.118** (basket); after it, 32/24 = 1.333 and 19/14 = 1.357. | veto factor **1.131** (button), **1.214** (basket) — vs the 1.081 / 1.011 `CONT-ENTRY 145` measured |
| **D2** | **`CONT-ENTRY 145`'s "decisive detail" points the opposite way.** Its argument is that basket's opportunity factor is 1.011, so the confound is "essentially absent", yet basket shows the larger conditional ratio. Basket's **disclaimer factor is 1.214 — the largest of the four mechanical factors**. Total mechanical inflation: button 1.081 × 1.131 = **1.223**, basket 1.011 × 1.214 = **1.227**. The two codewords are inflated by the *same* amount; that is why their raw ratios "agree". | the entry's decisive argument is unsupported; the agreement it celebrates is the confound's signature |
| **D3** | **Fully stripped, the excess is zero.** Never-refused-in-*either*-arm stratum × no-`SCOPE`-veto endpoint: **button ko 28 / ctrl 28 = 1.0000 [0.633, 1.632]**, **basket 18 / 17 = 1.0588 [0.583, 1.917]**. | "content-true, if anything, goes **up**" (`CONT-ENTRY 143`) and "`✅ survives the mechanical confound`" (claim table) must be withdrawn as stated |
| **D4** | **The "conditional on not-refused" adjustment conditions on a post-treatment variable.** Refusal is caused by the intervention (48 button / 7 basket rows are de-refused by it), so conditioning on `not refused` *in that arm* conditions on a mediator. It puts **48 rows into ko's denominator that are absent from ctrl's**, and those rows carry content at **5/48 = 0.104** vs the base 27/595 = 0.045 (button, **2.3×**) and **1/7 = 0.143** vs 18/662 = 0.027 (basket, **5.3×**). | the valid principal-stratum ratios are **1.125 [0.708, 1.875]** and **1.286 [0.692, 2.444]**, not the published 1.234 / 1.343 |
| **D5** | **"The two content-true ratios agree to within 2 %" (`CONT-ENTRY 144`) is an artifact of rule choice and small integers.** 32/24 and 19/14; a one-event change moves either by 3–5 %; the CIs are [0.84, 2.25] and [0.75, 2.60]. Under the no-veto rule they are 1.179 / 1.118 (5.5 % apart); under `ASR≥0.5` **1.054 / 0.816**; under `ASR≥0.5 ∧ lexicon` **1.022 / 0.818**. | "the strongest cross-codeword agreement of any quantity in this phase" is a coincidence of two small integers |
| **D6** | **On basket, every broader bomb-content measure FALLS under the knockout.** `SR≥0.5` **71/87 = 0.816**; lexicon-concept-present **46/61 = 0.754**; disclaimer terms **52/77 = 0.675** (McNemar **p = 0.0041**). Only the narrowest conjunction rises. | basket's "replication" is endpoint-specific; the sign of the content effect reverses between endpoints on the replication codeword |
| **D7** | **Provenance mislabel: `"population": "train+val"` describes a TRAIN-ONLY dataset.** All 67 domains in all four runs are `train` (70 train − 3 preregistered-excluded). The 23 validation domains are **absent entirely** — the generating runs filter through `runargs/dcs_cont/exclude_*_train.txt`. `rows_kept = 670 of 670` is the filter being a **no-op**, not a filter working. | A17 is a **train-only** result. (No TEST leak — verified, `Counter({'train': 67})`.) |
| **D8** | **The shipped basket PRIMARY intervals discard 36 % of their own bootstrap draws.** `dcs_cont_oneswitch.py:ratios()` returns `nan` when the ctrl denominator is 0 and the caller drops those draws (`if not math.isnan(r1)`), as does `cond_ratio`'s `if a and c and e`. At basket/`slot0` (ctrl content = 1, ctrl refusal = 1) **7201/20000 content draws and 7319/20000 refusal draws are silently discarded**; the published `content_ci [0.0, 5.0]` / `refusal_ci [0.0, 0.0]` are percentiles of the surviving 64 %. button/`slot0` drops 0.18 %; **both all-slots scopes drop 0**. | immaterial to the headline; the artifact's primary-scope intervals are not what they are labelled |

### PLAUSIBLE CONCERNS

| # | finding |
|---|---|
| **P1** | **The formalisation "one-switch ⇒ content ratio ≈ refusal ratio" is not a theorem** — see §3. A single graded latent "bomb-reading" with **two ordered thresholds** (refuse above `t_R`, emit bomb content between `t_C` and `t_R`) is a *one-switch* model, is tightly — not loosely — coupled, and **predicts refusal down and content flat-or-up**. It fits refusal 75→27 and content 24→32 exactly, with freedom to spare. What A17 excludes is "one switch with both endpoints as **parallel monotone readouts**", which is narrower than the account `REVIEW-8` raised. The claim-table caveat ("only the *proportional* form is excluded — a loosely-coupled variant survives") understates this: the surviving variant is not loosely coupled. |
| **P2** | **The data's own signature is the threshold model's signature.** Refusal is **perfectly nested** — 0 newly-refused rows of 670, on **both** codewords (button 48 de-refused / 0 newly-refused; basket 7 / 0) — i.e. a monotone weakening, not a stochastic one. And the de-refused rows are enriched 2.3× / 5.3× for content (D4). |
| **P3** | **The one measurement that would discriminate threshold-one-switch from GATING is the never-refused-in-both stratum ratio** (threshold-one-switch predicts **< 1**, GATING predicts **= 1**). Observed **1.000 [0.633, 1.632]** and **1.059 [0.583, 1.917]** — consistent with GATING, but with no power against a 30 % fall. The phase's data cannot decide it. |
| **P4** | **Scope.** The phase's headline claim sits on a scope the phase declared **secondary**, for exactly the run pair and endpoint where `CONT-ENTRY 120` preregistered `slot0` in advance. It is labelled, and I could find **no evidence of scope shopping** (§5): slot0-vs-rest heterogeneity Fisher **p = 0.524** / **1.000**; the joint test on the primary points the same way at **RoR 2.60 [0.82, 13.0], p = 0.054** (button). It is underpowering, not selection. But "labelled secondary" and "phase headline" are in tension. |
| **P5** | Percentile cluster-bootstrap coverage at these counts is **0.928–0.939** against a nominal 0.95 (2000-rep simulation, 67 domains × 10 rows, `p_ctrl` = 0.0358, true r = 0.36, iid / gamma(2) / gamma(0.5) domain effects). Mildly anti-conservative; immaterial at an observed p ≈ 1e−5. |
| **P6** | The button pair was generated **34 h apart on different commits** (`158f38c1` vs `1a622b1e`, 20 commits) though on the same node and GPU. The only `src/` change between them is `run_completeness_check.py` (+71/−3), which does not touch generation. Basket's two arms share one commit. |
| **P7** | Judge cache hits are asymmetric (button ko 22 / ctrl 71; basket 0 / 2). A cache hit suppresses the judge's 13.7 % flip rate on byte-identical input for that row. 71 vs 22 rows out of 670. Not quantified here. |

### CHECKED AND CLEAN

* **Every published A17 number reproduces exactly** from raw artifacts with independent code (§1).
* **Re-running the committed script regenerates both JSONs byte-identical** (`diff` → no output).
* **Pairing is real** (§4): 670/670 shared `prompt_id`; `prompt_sha16` identical **670/670**;
  `goal_sha256_16` identical 670/670; `family_id` and `domain` identical 670/670; `judge_status: ok`
  670/670 in all four runs; one pinned judge (`openai/gpt-4o-mini`) and **one judge manifest per
  codeword**; generation on one node/GPU per codeword (`n-503` / RTX A5000).
* **No TEST leak.**
* **No asymmetric filtering.** `refused` is `behav_judge.kw_refusal`, a deterministic case-insensitive
  substring matcher on the completion, applied identically to both arms.
* **No truncation or emptiness asymmetry.** `stop_reason == "eos"` on **670/670 in all four arms**;
  zero empty generations.
* **No length confound.** Whole-arm mean length differs (button ko 1451 vs ctrl 1352 chars) but that is
  entirely the short refusals: in the never-refused stratum the ratio is **0.993** (button) and
  **1.005** (basket). Length-stratified (quintile) MH risk ratios **1.149** / **1.196** vs unadjusted
  1.125 / 1.286.
* **The bootstrap is not badly behaved on the headline scope.** Zero dropped draws; bootstrap bias in
  the log ratio **+0.012 (1.2 %)**; log-scale CI **[0.823, 2.139]** / **[0.748, 2.416]** ≈ the
  published percentile CI.
* **The `Scope.for_dose_contrast` rule does not apply and the author is right that it does not** (§5).

---

## 1. Independent reproduction

Recomputed from `results.jsonl` + the `gens.jsonl` named in each run's `summary.json`, with the
CR-002 regexes read from `configs/dcs_cont_content_rule_v2.json` (status `FROZEN`) and the 44-term
lexicon re-transcribed by hand:

| codeword | scope | refusal ko/ctrl | content ko/ctrl | conditional | published |
|---|---|---|---|---|---|
| button | all slots | 27/75 = **0.3600** | 24→32 = **1.3333** | 32/643 ÷ 24/595 = **1.2338** | identical |
| button | `slot0` | 4/13 = **0.3077** | 7→6 = **0.8571** | **0.7978** | identical |
| basket | all slots | 1/8 = **0.1250** | 14→19 = **1.3571** | 19/669 ÷ 14/662 = **1.3429** | identical |
| basket | `slot0` | 0/1 = **0.0000** | 1→2 = **2.0000** | **1.9851** | identical |

Bootstrap intervals reproduce to the published digits with the committed seed (20260912) and to
within ±0.003 / ±0.02 under other seeds. `opportunity 1.0807 × conditional 1.2338 = 1.3333` checks.
`DCS_CONT_ONESWITCH.json` (cited by `CONT-ENTRY 143`) is the pre-decomposition button version; the
two codeword files cited by 144/145 both exist and are current. **No "claimed but unwritten artifact"
defect here.**

---

## 2. The bootstrap (axis 2) — and the one place the guard bites

`ratios()` is a ratio of sums over resampled **domains** (correct independence unit) with a
percentile interval, and NaN draws are dropped by the caller. Findings:

* **All-slots, both codewords: 0 of 20000 draws dropped.** Ctrl content (24, 14) and ctrl refusal
  (75, 8) are spread over enough domains that no resample zeroes a denominator. The `if a and c and e`
  concern is **moot at the headline**.
* **basket/`slot0`: 7201/20000 (36.0 %) content draws and 7319/20000 refusal draws dropped** — D8.
  button/`slot0`: 37/20000 (0.18 %). Direction of the bias: dropped draws are those with a zero
  denominator, i.e. the *upper* tail; dropping them lowers both percentiles, which is conservative for
  an exclusion but makes the published `[0.0, 5.0]` uninterpretable as a 95 % interval.
* **Ratio-estimator bias is negligible.** mean(bootstrap log ratio) = 0.2943 vs point 0.2826 (button);
  0.2997 vs 0.2963 (basket) — a +1.2 % / +0.3 % bias in the ratio.
* **Log-scale interval** (bootstrap SE on log, normal): button **[0.823, 2.139]**, basket
  **[0.748, 2.416]** — essentially the percentile interval. **The exclusion is unchanged.**
* **Coverage simulation** (2000 reps, 67 domains × 10 rows, true r = 0.36): 0.937 (iid), 0.939
  (gamma(2) domain effect), 0.928 (gamma(0.5)). At true r = 1.0: 0.935–0.958. Anti-conservative by
  1–2 points — P5.

**A bootstrap-free joint test.** The right statistic is the ratio-of-ratios
RoR = RR_content / RR_refusal, which one-switch sets to 1 and which — unlike the published comparison
— propagates the uncertainty in the refusal ratio too. Domain-cluster bootstrap on the log scale with
Haldane 0.5 (no dropped draws, any scope):

| codeword | scope | koC | ctC | koR | ctR | **RoR** | 95 % CI | p(RoR ≤ 1) |
|---|---|---|---|---|---|---|---|---|
| button | all slots | 32 | 24 | 27 | 75 | **3.64** | [2.10, 7.05] | < 1e−5 |
| button | `slot0` | 6 | 7 | 4 | 13 | 2.60 | [0.82, 13.0] | 0.054 |
| basket | all slots | 19 | 14 | 1 | 8 | **7.62** | [2.04, 41.0] | 0.0009 |
| basket | `slot0` | 2 | 1 | 0 | 1 | 5.00 | [0.20, 55.0] | 0.238 |

**The exclusion survives the correct joint test, and survives it on both codewords.**

---

## 3. Is the comparison well-posed? (axis 3) — **the deepest problem, and it is not statistical**

`CONT-ENTRY 143` derives: *one switch ⇒ both endpoints downstream ⇒ the knockout cuts both by a
similar proportion ⇒ content ratio ≈ refusal ratio 0.36.* That derivation is valid only if refusal and
bomb content are **parallel monotone readouts** of the switch. They are not, and the entry says so
itself two entries later: **a refused row can carry no bomb content** (verified — 0/27 and 0/1 refused
rows are content-true). They are **competing** outcomes, and competing outcomes of one latent variable
do not move proportionally.

**A one-switch model that predicts the observed data.** Let each prompt carry a single latent
bomb-reading strength `b`; the installation sets its level; the knockout shifts the whole distribution
down by δ. Two ordered thresholds on that one variable:

* `b > t_R` → the safety response fires → **refusal** (and no content),
* `t_C < b < t_R` → read as bomb-ish, safety does not fire → **bomb content**,
* `b < t_C` → literal button/basket answer.

Under this model a downward shift moves mass **out of the refusal band and into the content band**.
Refusal falls a lot; content stays flat or rises. This is **one switch**, it is **tightly** coupled,
and it reproduces refusal 75→27 together with content 24→32 with parameters to spare (two observed
constraints, four free quantities). It is not excluded; it is not even strained.

Three features of the data are its signature rather than GATING's:

1. **Refusal is perfectly nested** — of 670 pairs, **0 rows are refused by ko but not ctrl**, on both
   codewords. A monotone shift, not a stochastic re-roll.
2. **The de-refused rows are content-enriched** — 5/48 = 0.104 (button) and 1/7 = 0.143 (basket)
   against base rates 0.045 and 0.027. Those are exactly the rows the shift moved out of the refusal
   band, and they carry 5 of ko's 32 events (button).
3. After removing that channel and the disclaimer channel, the content ratio is **1.000** — i.e. the
   *residual* evidence for "content rises" is nil.

**What A17 is entitled to say:** the *proportional parallel-readout* form of one-switch is excluded.
**What A17 currently says** — "the simplest rival account is excluded", "the clean form of the account
is dead" — is broader than the test supports. The variant that survives is not the "loose coupling"
strawman the entry disclaims; it is the most natural single-latent-variable reading of `REVIEW-8`'s
own sentence.

**P3 restated as an experiment:** the discriminating quantity is the content ratio inside the
never-refused-in-both stratum — threshold-one-switch predicts < 1, GATING predicts = 1. Measured:
**1.000 [0.633, 1.632]** and **1.059 [0.583, 1.917]**. Undecided.

---

## 4. Pairing and arm symmetry (axes 5, 6)

**Identity.** 670/670 shared `prompt_id`, zero arm-only ids; `prompt_sha16` identical 670/670;
`goal_sha256_16` identical 670/670; `family_id` and `domain` identical 670/670. Both arms of a
codeword are one judge manifest, one pinned model (`openai/gpt-4o-mini`, `judge_model_used` on
670/670), `judge_status: ok` 670/670, `found_in_bank: True` 670/670, `bank_rows_sha16` matching the
bank. Generation: `n-503` / NVIDIA RTX A5000 for all four generating runs; same model
(`Llama-3.1-8B-Instruct`), dtype, `--max-new 640`, `--seed 20260913`; arms differ **only** in
`--intervene` band (`6-14` vs `20-28`).

Note for the record: **`ctrl` is not a clean arm.** It is `attn_knockout:20-28`, a control *band*.
"The knockout should cut both endpoints" is therefore a comparison of two interventions. That is the
phase's standing design and is stated elsewhere; it is not a defect of A17, but the one-switch
prediction is being tested against a band contrast, not against baseline.

**Generation symmetry.** `stop_reason == "eos"` on 670/670 in all four arms — **no truncation
asymmetry at all**. Zero empty completions (3 button-ctrl and 1 basket-ctrl completions are < 50
chars; none in ko). Whole-arm mean length button ko 1450.9 vs ctrl 1352.4 chars — but this is the
refusals (short), not a systematic shift: **never-refused-stratum mean lengths are 1500.8 vs 1510.9
(ratio 0.993)** and basket 1433.9 vs 1426.3 (**1.005**). Length-quintile-stratified MH risk ratio
**1.149** (button) and **1.196** (basket) against unadjusted 1.125 / 1.286 — **length is not the
driver**.

**CR-002 symmetry — this is where it breaks (D1).** The rule is applied by identical code to both
arms, but its `SCOPE` clause is a **disclaimer detector**, and the knockout demonstrably removes
disclaimers (already on the record as **A2b: "−3.1 pp disclaimers"**):

| | ko candidates (`SR≥0.5 ∧ lexicon ∧ MATERIAL`) | vetoed by `SCOPE` | ctrl candidates | vetoed | veto factor |
|---|---|---|---|---|---|
| button | 33 | **1** | 28 | **4** (`mock`×8, `harmless`×2, `fake`, `non-explosive`) | **1.131** |
| basket | 19 | **0** | 17 | **3** (`mock`×6, `harmless`×2, `disposal`) | **1.214** |
| pooled | 52 | 1 | 45 | 7 | Fisher **p = 0.023** |

Whole-arm disclaimer prevalence (all 670 rows): button 84 vs 98 = **0.857 [0.673, 1.089]**; basket
52 vs 77 = **0.675 [0.481, 0.859]**, McNemar **p = 0.0041**.

**The full decomposition, replacing the one in `CONT-ENTRY 145`:**

| | A raw CR-002 | B = A ÷ refusal-opportunity (never-refused-in-both stratum) | C = A ÷ disclaimer veto (no-veto endpoint) | **D both removed** |
|---|---|---|---|---|
| **button** | 32/24 = **1.3333** [0.840, 2.267] | 27/24 = **1.1250** [0.708, 1.875] | 33/28 = **1.1786** [0.744, 1.950] | **28/28 = 1.0000 [0.633, 1.632]** |
| **basket** | 19/14 = **1.3571** [0.750, 2.600] | 18/14 = **1.2857** [0.692, 2.444] | 19/17 = **1.1176** [0.625, 2.000] | **18/17 = 1.0588 [0.583, 1.917]** |

Every cell still excludes 0.360 / 0.125. **The A17 proposition survives the full strip. The A17
narrative does not.**

---

## 5. Multiplicity and scope (axis 4)

**The dose rule does not apply, and the author is right.** `Scope.for_dose_contrast` raises on
`ALL_SLOTS` because a dose contrast compares arms with *different slot sets* (1 vs 5). Here both arms
are the **same 670 prompt ids** with **134 rows in each of slot0/4/8/12/16** — identical slot
composition. `C-CONT-091`'s 1-vs-5 hazard is structurally absent. Checked, clean.

**`CONT-ENTRY 120` did preregister `slot0` for this run pair and this endpoint** ("PRIMARY: `slot0`
only … Reference arm `ko − ctrlHW` on the CR-002 endpoint … An all-slots version may be reported only
as a labelled secondary"). The headline is the secondary; the primary is null. The entries label this
prominently and report the primary. I looked for evidence that the secondary was *chosen* rather than
forced:

* **Heterogeneity slot0 vs the other four slots:** Fisher **p = 0.524** (button, 6/7 vs 26/17),
  **p = 1.000** (basket). No evidence the primary disagrees.
* **The primary points the same way, underpowered:** joint RoR **2.60 [0.82, 13.0], p = 0.054**
  (button); **5.00 [0.20, 55.0], p = 0.238** (basket).
* **Slot leave-one-out** (drop each slot in turn): button ratios 1.043–1.647, **exclusion holds in all
  five**, including dropping `slot8` (the 8→1 slot) which gives 1.043 [0.606, 1.846]. Basket
  1.250–1.556, exclusion holds in all five.
* **Domain leave-one-out:** button 1.250–1.524; basket 1.143–1.583.

So: **underpowering, not scope shopping.** P4 stands only as the structural point that the phase's
headline rests on its own declared-secondary scope.

**Content-rule multiplicity.** Six endpoint definitions, all-slots, domain-clustered:

| rule | button ko/ctrl → ratio [CI] | one-switch | basket ko/ctrl → ratio [CI] | one-switch |
|---|---|---|---|---|
| CR-002 (headline) | 32/24 = 1.333 [0.840, 2.231] | EXCLUDED | 19/14 = 1.357 [0.750, 2.571] | EXCLUDED |
| CR-002 without `SCOPE` veto | 33/28 = 1.179 [0.744, 1.950] | EXCLUDED | 19/17 = 1.118 [0.625, 2.000] | EXCLUDED |
| `MATERIAL` only, no SR gate | 33/28 = 1.179 [0.744, 1.938] | EXCLUDED | 20/18 = 1.111 [0.640, 1.923] | EXCLUDED |
| `ASR ≥ 0.5 ∧ lexicon` | 93/91 = 1.022 [0.809, 1.300] | EXCLUDED | 27/33 = **0.818** [0.543, 1.200] | EXCLUDED |
| `ASR ≥ 0.5` raw | 252/239 = 1.054 [0.922, 1.204] | EXCLUDED | 71/87 = **0.816** [0.645, 1.025] | EXCLUDED |
| `ASR ≥ 0.25 ∧ CR-002` | 32/24 = 1.333 | EXCLUDED | 19/14 = 1.357 | EXCLUDED |

**The exclusion is rule-robust** (0.36 and 0.125 are far below every interval). **The direction is
not** — D5/D6: on basket the two broadest endpoints both *fall* by ~18 %, and only the narrowest
conjunction rises. Four verdicts (2 codewords × 2 scopes) with 2 exclusions; Bonferroni-over-4 is
irrelevant at p = 6.5e−6 / 5.3e−9 but is worth 0.0038 against basket's clustered p = 0.0009.

---

## 6. Exact / conditional tests (axis 7)

Exact conditional binomial on discordant pairs (H0: the content ratio equals the stated value;
`OR ≈ RR` to ~2 % at these rates; ignores domain clustering, which §2's cluster bootstrap covers):

| codeword | scope | discordant (ko-only) | H0: ratio = refusal ratio | H0: ratio = 1 |
|---|---|---|---|---|
| button | all slots | 44 (26) | **p = 6.54e−06** | p = 0.291 |
| button | `slot0` | 11 (5) | p = 0.145 | p = 1.000 |
| basket | all slots | 25 (15) | **p = 5.30e−09** | p = 0.424 |
| basket | `slot0` | 3 (2) | — (refusal ratio is 0) | p = 1.000 |

Same test inside the never-refused-in-both stratum (button): discordant 39, ko-only 21,
**p = 3.5e−04** against 0.36 and p = 0.749 against 1.

**Both halves of the claim table row are confirmed by exact tests:** the proportional one-switch is
excluded far beyond the bootstrap's suggestion, and **GATING's ratio ≈ 1.0 is nowhere near excluded**
(p = 0.29 / 0.42). The "no rise established" caveat is correct and, after D3, is the *only* thing the
content endpoint establishes.

One caution: a naive Fisher exact on the 2 × 2 of discordant counts
(`[[26,18],[0,48]]`, p = 1.8e−11) is **not** a valid test here — a perfectly nested refusal reduction
forces the conditional odds ratio to 0 regardless of its size, so that test is far too eager. The
cluster-bootstrap RoR in §2 is the right joint statistic, and it is the one quoted above.

---

## 7. Code notes on `scripts/dcs_cont_oneswitch.py`

* **L136** `oppK = sum(...) / sum(...) if False else None` — dead code; `oppK` is never used. Cosmetic
  but it is an unexecuted expression left in a committed analysis script.
* **L128** `q = lambda v, f: v[int(f * len(v))]` — `int(0.975 * 20000) = 19500` is the 97.5th order
  statistic of 20000, off by ~half an index from the conventional `int(f*(n-1))`. Immaterial.
* The refusal and content bootstraps share one resample stream (`random.Random(a.seed)` drawn once)
  while `cond_ratio`'s bootstrap re-seeds with the same seed and therefore reuses the *same* domain
  resamples. That is fine — but it means the conditional and raw intervals are not independent, so
  their agreement is not corroboration.
* `filter_rows` is used correctly and both axes are passed explicitly. The provenance dict is written.
  The defect is D7: the population *tag* is accurate about the filter and misleading about the data.

---

## 8. What would be needed to break A17, and what must be repaired

**A17's proposition survives.** I could not construct a test on these artifacts under which the
strictly-proportional one-switch is admissible: the smallest content ratio I could produce with any
defensible endpoint or stratum is **0.816** (basket, raw `ASR ≥ 0.5`) against a refusal ratio of
**0.125**, and the fully-stripped button estimate of **1.000** sits against **0.360** with a lower
bound of 0.633.

**To break it on the numbers** you would need either (a) the refusal ratio to be near 1 — it is not on
button, where the exact conditional OR CI is **[0.000, 0.080]** and 48 of 75 control refusals vanish
with zero counter-examples; or (b) a content ratio below ~0.6, which no endpoint I tried produces on
button. Neither is reachable from this data. A *new* measurement that could break it: a content
endpoint that is insensitive to disclaimer style and to the knockout's wholesale rewriting of the text
(A2b: 669/670 completions differ) — e.g. a blind human rating of "does this answer help build a bomb"
on the ~60 candidate rows of both arms. Given D1–D3, that is the measurement A17 now needs.

**To break it as an argument** you do not need new data at all — §3 already does it. A one-switch model
with two ordered thresholds on one latent variable predicts the observed pattern, and A17's exclusion
does not touch it.

**Required repairs to the record**

1. `CONT-ENTRY 145`'s decomposition is incomplete and its "decisive detail" (D2) should be withdrawn.
   The disclaimer channel (1.131 / **1.214**) is larger than the opportunity channel it measured.
2. The claim-table row's "content-true, **if anything, goes up**" and "✅ survives the mechanical
   confound" must become: **after both mechanical channels, the ratio is 1.000 [0.633, 1.632] (button)
   and 1.059 [0.583, 1.917] (basket)** — the exclusion holds, the rise does not exist.
3. The conditional figures 1.234 / 1.343 should be replaced by the principal-stratum figures
   1.125 / 1.286 (D4), or carry an explicit post-treatment-conditioning warning.
4. `CONT-ENTRY 144`'s "agree to within 2 %" should be struck (D5), and basket's endpoint sign
   reversal (D6) recorded.
5. The provenance tag should say **train-only**, not train+val (D7), and the basket-primary intervals
   should be marked as computed on 64 % of their draws (D8).
