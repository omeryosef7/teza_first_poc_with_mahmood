# HERETIC-CSI P5/P6: codeword provenance, held-out probe quality, frozen staged design + power

**Workstream F4. 2026-10-13. CPU only (no GPU job launched).** Machine-readable companions:
`reports/heretic_csi/hcsi_p6_codeword_table.json` (40-word table), `hcsi_p6_power.json` (power sim),
`hcsi_p6_heldout_probe_{basket,button}.json` (held-out probe). The design below is a **proposal to freeze**,
written before any P6 GPU number exists. Nothing in it has been run on new codewords.

Helpers (new, small): `research/heretic_csi/p6_codeword_table.py`, `p6_install_strength.py`,
`p6_heldout_probe.py` (+ `slurm/p6_heldout_probe.slurm`, job 1022696 cpu-killable), `p6_power.py`.
The frequency source is **wordfreq 3.1.1** (English Zipf), installed to an isolated `--target` dir
(`outputs/heretic_csi/pylib_wordfreq`), so the frozen `poc_stage2` env is untouched. PR-CSI-008 screened
**no** frequency criterion, so frequency is a **new covariate** for P6, declared here.

---

## 1. The codeword screen (PR-CSI-008), recovered

- Prereg `configs/dcs_csi_pr008_codeword_screen.json` (frozen 2026-09-21; pre-GPU lexical only).
- Result `reports/DCS_CSI_PR008_LEXICAL_SCREEN.json`: 40 candidates → **25 survivors**. Criteria: L1 single
  token with leading space (a hard rule, because the KO masks exactly one codeword row), L2 incidental incidence
  ≤ 0.005 (button exempt), L3 concept-disjoint, L5 nesting.
- The CSI log (S-151 and later) says the GPU screen **never ran**: "a third codeword still does not exist —
  UNBUILT". So no survivor besides basket/button has a GPU readout under the ts116m design.

### Survivors with frequency and contamination status (Zipf from wordfreq; Llama id of " "+word)

| word | Zipf | status |
|---|---|---|
| chair | 4.69 | untouched |
| bottle | 4.57 | untouched |
| **button** | 4.56 | **CONTAMINATED**: incumbent; all CSI + HERETIC-CSI selection on TRAIN+VAL |
| jacket | 4.32 | untouched |
| **basket** | 4.07 | **CONTAMINATED**: incumbent; head set selected on basket VALIDATION |
| blanket | 4.07 | untouched |
| bucket | 4.07 | untouched |
| lamp | 4.05 | untouched |
| ladder | 4.03 | untouched (its 92 log hits are the word "ladder" as a metaphor: dose/rank/position ladders) |
| banana | 4.00 | untouched |
| pillow | 3.96 | untouched |
| pencil | 3.95 | untouched |
| wagon | 3.90 | untouched |
| balloon | 3.90 | untouched |
| candle | 3.88 | **PARTIAL**: `rbd_candle_missile` banks from an earlier phase (concept=missile); no ts116m readout. Usable as DEV only |
| whistle | 3.88 | untouched |
| curtain | 3.86 | untouched |
| envelope | 3.86 | untouched |
| ribbon | 3.81 | untouched |
| saddle | 3.73 | untouched |
| yogurt | 3.63 | untouched |
| **carrot** | 3.62 | **EXCLUDE**: (a) early-DCS GPU runs (`cds1A_carrot`, `cds2dp_carrot`, 2026-09-01; measured ICC) and the literature example; (b) **structural**: the word "carrot" occurs **9,396×** in `demo_pools_116dom_tsm_bomb.json`, where it is the pool placeholder/benign concept. As a codeword it would collide with the pool text |
| sponge | 3.59 | untouched |
| cushion | 3.58 | untouched |
| kettle | 3.54 | untouched |

Non-survivors (L1 multi-token: napkin, teapot, mitten, stapler, thimble, trolley, crayon, muffin, tulip; L2
incidence: ticket, mirror, apple, table, window, garden) are out. ticket, window and apple also have earlier-phase
banks.

**Usable untouched pool = 21 words**, plus candle (DEV-only) = 22.
⚠ **Restricted frequency range:** the survivors span Zipf 3.54–4.69, about 1.15 log10 units. Basket (4.07)
and button (4.56) sit inside it. A frequency effect has to show up within a narrow band, which costs power
(§4). We cannot fix this without relaxing PR-CSI-008, which we will not do.

## 2. On-disk availability and what a new codeword costs

Only basket and button have the full chain. For a new codeword W, every step reuses an existing script
(**no new science code**):

| step | existing script | where it runs | measured cost (basket) |
|---|---|---|---|
| 1 bank | `src/boombness/prompt_families.py --preset main_longpre_cds_ts --codeword W --concept bomb --pools data/boombness_prompts/demo_pools_116dom_tsm_bomb.json` (+ `--incidental-replace` if the L2 repair needs it) | CPU | minutes (the bank meta records `cuda_available=None`) |
| 2 exclusions | `scripts/dcs_ts_make_exclusions.py` → `runargs/dcs_cont/exclude_W_bomb_{sow,behavioral}_{train,validation}.txt` | CPU | seconds |
| 3 base readout | `score_behavior.py` (semantic_one_word + forced_choice; n_examples 0,4; ND + benign) | GPU | **34 min** on L40S (5,552 rows) |
| 4 behavioral corpus | `scripts/dcs_extract_under_ko.py --no-knockout --only-query-kind behavioral --only-n-examples 4 --position codeword_last` | GPU | **33 min** (basket ran on a **V100**; new codewords MUST run on L40S/3090/a5000). Slim it to `--layers 18` (+ needed sites): the full grid is **12 GB per codeword** (`multiposition_reps.pt` 11.5 GB), and 22 of those would break the 200 GB cap |
| 5 axis + controls | `scripts/dcs_csi_axis.py` via `axisfit_ranksweep.slurm` | CPU | 6 min |
| 6 rescue sweep | `research/heretic_csi/slurm/rescue_sweep.slurm` (61 arms, one model load) | GPU | VALIDATION 230 rows: about 3–3.5 h/rank (a5000); TRAIN K4 268 rows: 4.3–5.8 h/rank |
| 7 analysis | `analyze_sweep.py` → `scripts/dcs_csi_subspace_analyze.py` | CPU | minutes |

The edits needed are small: `axisfit_ranksweep.slurm` and `rescue_sweep.slurm` **hard-code `case basket|button`**
for the corpus/readout paths, so they need a generic `W)` branch taking paths as arguments. That is a few lines,
and nothing frozen changes.

**Per-codeword GPU budget (rank-1 only, scored on VALIDATION):** about 0.6 + 0.6 + 3.5 ≈ **4.7 GPU-h**.
- 22 codewords: about 105 GPU-h, roughly 18–20 h wall at the 6-job cap.
- Adding the full rank curve {1,2,4,8,16} for every codeword is about 5×, roughly 380 GPU-h. **Not recommended**;
  see the design.

## 3. Split and provenance table (mandate §19)

| population | domains | codewords | prompt families | rows used per codeword | influenced selection? |
|---|---|---|---|---|---|
| TRAIN (split seed 202609061, unit = domain) | 70 assigned, **67 effective** (3 whole-population exclusions) | basket, button | ts116m `cds_n4_sow`, cell C, `semantic_one_word` readout; axis fit on `behavioral` n4 | full rows (r1/r16 headline); 268 (K4 subset) for r4/r8 | **YES**: axis fit, rank choice, all HERETIC-CSI P2a selection |
| VALIDATION | 23 | basket, button | same | 230 (23 × 10) | **YES**: certifying reads S-047…S-049; the basket head set was selected on basket VALIDATION (CSI) |
| TEST | 23 | — | — | — | **SPENT** (read 2026-09-08, AM-39). Never used |
| **New codewords (P6)** | same 67 TRAIN / 23 VAL domains | 21 untouched + candle | identical banks/preset | identical | **NO** for the 21; candle partial (different concept) |

Prompt families per bank: 22,272 rows. Each condition (benign_literal / concept_in_benign_ctx / direct_harmful /
natural_doublespeak) has 5,568 rows. Each query_kind (behavioral / semantic_forced_choice / semantic_one_word)
has 7,424 rows. 192 rows per domain over 116 domains.

⚠ **The domains are not fresh.** New codewords reuse the same 67/23 domain split. The confirmation unit is
the **codeword**: the codeword is new, the domains are not. Domain-level conclusions are already
contaminated for basket/button only through the codeword. State this every time a P6 result is written.

## 4. Proposed frozen staged design

**Covariates (per codeword, all measured before the outcome):**
- (a) **Zipf frequency** (wordfreq 3.1.1, lexical; zero GPU).
- (b) **Held-out probe quality:** PLS rank-1 fit on TRAIN, Spearman on VALIDATION, L18, site rel-6
  (`p6_heldout_probe.py`).
- (c) **Installer strength:** domain-mean of y_install(cell C) − y_install(cell A), semantic_one_word,
  n_examples = 4, TRAIN (`p6_install_strength.py`).

**Outcome (primary, per codeword):** **rank-1 rescue specificity z** on VALIDATION domains:
`z = (recovery_cand − mean(recovery_ctrl)) / sd(recovery_ctrl)` over the 56-control rank-matched family
(46 random + 10 shuffled-label). The certified S-049 pipeline is reused unchanged. Secondary: the binary
rank-test PASS at floor 1/57 = 0.0175 < 0.05, which is resolvable per codeword. A continuous z is used for the
across-codeword correlation because rank-p is coarse.

**Stage 0 (cheap screen; covariates only):** steps 1–4 for all 22 words, about 1.2 GPU-h each, roughly 26 GPU-h.
**Mechanical attrition, declared now and applied before any outcome:**
- (G1) installer-strength 95% CI lower bound > 0.05 on TRAIN. A non-installer has nothing to rescue, so it is a
  floor case.
- (G2) KO liveness in the rescue job's own BASE/KO arms: the KO drop has a CI that excludes 0, and KO_FULL
  recovers > 0.
- (G3) option-mass gate PASS.

Every dropped codeword stays in the denominator with its reason. **No ASR-based or outcome-based exclusion.**

**Stage 1 (DEV, method shakedown, no hypothesis test):** **6 codewords**.
- candle (forced into DEV: partial prior use).
- Plus 5 drawn by a seeded stratified rule (seed 20261013) over frequency tertile × installer above/below the
  Stage-0 median, filling a 3×2 grid.
- Basket and button are added as DEV points (contaminated, never confirmatory).
- On DEV only: the rank curve {1,4,16} (minimal-sufficient-rank exploration, about 30 GPU-h), and any pipeline
  fixes. **Nothing in the method may change after DEV:** layer 18, site rel-6, KO band 6–14, PLS rank-1, the
  control family and the outcome are already frozen from S-049.

**Stage 2 (CONFIRMATION):** all remaining **G1–G3 survivors among the other 16** at rank 1 on VALIDATION,
about 75 GPU-h.

**Predeclared confirmatory statistics (unit = codeword, one confirmatory family, Holm over the two primary tests):**
- **H6a (C1, one-sided, positive):** Spearman(held-out probe rho, specificity z) > 0. "A better probe goes with
  a specific rank-1 carrier."
- **H6b (frequency, two-sided):** Spearman(Zipf, specificity z) ≠ 0. Two-sided because basket (lower frequency,
  specific) vs button (higher frequency, not specific) gives a direction from 2 contaminated points, which we
  must not take as a prior.
- **Descriptive (prevalence):** the number of confirmation codewords with rank-1 PASS, against Binomial(n, 0.05).
  This answers "is a specific rank-1 carrier common or rare?"
- **Exploratory only:** installer strength as a covariate. Note: button installs **more strongly** than basket
  (below), so installer strength is a live alternative to probe quality.

## 5. Power (mandate §20)

One-sided permutation Spearman at α = 0.05, 20,000 simulations
(`hcsi_p6_power.json`). "reliability" is the fraction of outcome variance that is signal.

| n codewords | min attainable p | critical ρ | power at ρ=0.6 (rel .7) | ρ=0.7 (rel .7) | ρ=0.8 (rel .7) |
|---|---|---|---|---|---|
| **2 (basket+button)** | 0.5 | — | **0 → CANNOT ANSWER** | 0 | 0 |
| 4 | 0.042 | 0.80 | 0.13 | 0.16 | 0.19 |
| 6 (DEV) | 0.0014 | 0.71 | 0.24 | 0.30 | 0.39 |
| 10 | 2.8e-7 | 0.55 | 0.39 | 0.51 | 0.64 |
| 15 | ~0 | 0.44 | 0.56 | 0.71 | 0.85 |
| **16 (CONF, proposed)** | ~0 | ~0.43 | ~0.60 | ~0.74 | ~0.87 |
| 17 | ~0 | 0.41 | 0.64 | 0.77 | 0.89 |
| 21 | ~0 | 0.37 | 0.71 | 0.85 | 0.94 |

**Verdicts:**
- Any basket-vs-button population claim (n = 2) is **CANNOT ANSWER**, whatever its effect size.
- DEV (n = 6) **cannot test** the hypotheses. It is a shakedown only, by design.
- CONF with n ≈ 16 has **≈ 0.74 power at ρ = 0.7** and **≈ 0.60 at ρ = 0.6** (reliability 0.7). The minimum
  detectable effect at 80% is **ρ ≈ 0.75**.
- If G1–G3 attrition cuts CONF below about 12, the power at ρ = 0.7 falls under 0.6. That must then be
  pre-labelled **UNDERPOWERED for ρ < 0.8** before GPU use, not reported later as a null.
- **Alternative (flag for the parent/user):** shrink DEV to candle + 3 and put 18 into CONF (≈0.80 at
  ρ = 0.7). The cost is a thinner frequency × installer grid in DEV.
- Per-codeword resolvability is fine: 56 controls give a floor of 0.0175 < 0.05.

## 6. Held-out probe quality (fills the S-043 gap: until now only TRAIN LOO rho existed)

L18, site rel-6, PLS fit on 67 TRAIN domains and scored on 23 VALIDATION domains. Statistic: Spearman over
within-domain-centred VALIDATION rows. CI: 95% domain-cluster bootstrap. Null: 20 within-domain label shuffles
on TRAIN, which gives a rank-p floor of 1/21 = 0.048.

| rank | basket val ρ [CI] | button val ρ [CI] |
|---|---|---|
| 1 | 0.533 [0.434, 0.631] (shuf max 0.42) | 0.574 [0.497, 0.653] (shuf max 0.52) |
| 2 | 0.642 [0.570, 0.712] (shuf max 0.36) | 0.626 [0.522, 0.713] (shuf max 0.23) |
| 3 | 0.636 [0.549, 0.718] (shuf max 0.36) | 0.576 [0.454, 0.685] (shuf max 0.29) |
| 4 | 0.638 [0.541, 0.721] (shuf max 0.27) | 0.624 [0.529, 0.704] (shuf max 0.22) |
| 8 | 0.635 [0.562, 0.702] (shuf max 0.21) | 0.578 [0.470, 0.676] (shuf max 0.13) |
| 16 | 0.603 [0.534, 0.666] (shuf max 0.09) | 0.534 [0.424, 0.629] (shuf max 0.22) |
| 32 | 0.568 [0.489, 0.638] (shuf max 0.06) | 0.550 [0.450, 0.639] (shuf max 0.21) |
| ridge (full) | 0.652 [0.577, 0.729] | 0.647 [0.561, 0.724] |
| rows / domains | train 670/67, val 230/23 | train 670/67, val 230/23 |

**Installer strength** (C − A, semantic_one_word, n4; 95% domain bootstrap):

| | basket | button |
|---|---|---|
| TRAIN (67 domains) | 0.475 [0.420, 0.530] | **0.678 [0.624, 0.729]** |
| VALIDATION (23 domains) | 0.403 [0.341, 0.465] | **0.672 [0.600, 0.739]** |

**INTERPRETATION (MEASURED; descriptive geometry, not causal):**
- **On held-out VALIDATION, button's rank-1 probe is NOT worse than basket's.** Button 0.574 [0.497, 0.653]
  vs basket 0.533 [0.434, 0.631]: the CIs overlap almost completely and the point estimate favours button.
  The **+12% TRAIN-LOO advantage for basket (S-043: 0.563 vs 0.504) does not survive held-out.**
- Ridge (full-dimensional) is identical: 0.653 vs 0.647.
- Both codewords beat the within-domain shuffle null at every rank (all rank-p = 0.048 = the 1/21 floor of a
  20-shuffle family). One rank-1 shuffle per codeword reached 0.42/0.52, so the rank-1 null tail is heavy.
  Use a larger shuffle family before quoting a p-value.
- **Consequence for C1** ("basket simply has a better probe"): **not supported held-out.**
  - The certified dissociation (basket r1 PASS on VAL p = 0.0175; button r1 FAIL) happens with
    **equal held-out decodability.**
  - Button also **installs more strongly** (0.67 vs 0.40 on VAL).
  - So the codeword whose rank-1 direction is the *better* (or equal) predictor and the *stronger* installer is
    the one **without** a specific rank-1 rescue carrier.
- Status: MEASURED on n = 2 codewords. It **kills C1 as stated for this pair** (held-out probe quality does not
  differ). It **cannot** establish any population relationship (n = 2 → CANNOT ANSWER, §5). That is H6a's job
  on fresh codewords.
- Scope: L18, rel-6, behavioral-prompt fit, VALIDATION domains already read by S-047–S-049 (the read is
  representational, not selection, but the domains are not fresh).

## 7. Caveats found in passing
- The basket/button behavioral corpora used for every axis fit (`cont1_behavioral_*`) were extracted on a
  **Tesla V100** (emulated bf16). The CSI log already records and adjudicates this (line ~11744). New-codeword
  extraction must run on native-bf16 hardware, which makes it **not identical** in hardware provenance to the
  incumbents. Record that as a known mismatch.
- `wordfreq`'s `regex` dependency sits in the isolated target dir only; never add that dir to PYTHONPATH for
  frozen jobs.
