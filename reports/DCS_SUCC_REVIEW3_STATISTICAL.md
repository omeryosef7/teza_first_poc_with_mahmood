# DCS SUCCESSOR — REVIEW-3, PART 4: STATISTICAL REVIEW

**Reviewer:** adversarial statistical review, PART 4 of REVIEW-3.
**Scope:** progress-log entries **038–047** only (`C-214`, `S-008`, `C-215`, `S-009`, ENTRY 044 claim
table, ENTRY 045 collaborator draft, `C-216`, `R-207`).
REVIEW-1 (entry 024) and REVIEW-2 (entry 039) findings are **not re-reported**; where one is
load-bearing here it is cited by number and marked **unrepaired**, not rediscovered.
**Review window:** 2026-09-10 **06:33 → 07:05 IDT**.
**The working tree is LIVE.** The `basket` K ladder (job 873140) is running: the newest arm
`outputs/boombness/score_behavior/ts116m_sowk_basket_K08_nondemo_matched_d2_20260910_065106_497607`
was created at **06:51 IDT**, during this review. No `basket` K-ladder number exists yet and none is
reviewed. **Nothing was modified; no job was submitted.**

**Method.** Every number below was recomputed with an independent implementation (plain
`torch`/`python`, not the repo's analyzers) from the run directories and the cached representations,
after checking `DONE.json`. Where the repo's loader was reused it is named. Artifacts read:
`outputs/dcs_succ/b1_position_control.json` (02:39), `outputs/dcs_succ/bombness_candidates_train.json`
(03:39), `outputs/dcs_succ/concept_presence.json` (02:34), `outputs/dcs_succ/concept_presence_basket.json`
(06:05), `outputs/dcs_succ/q2_concept_present{,_basket}.json` (03:36 / 06:06),
`outputs/boombness/extract_boombness/ts116m_full_{button,basket}_{bomb,knife,gun}_*/cache/final_occurrence_reps.pt`,
`outputs/boombness/score_behavior/tsb66{,b}_{C_n4,C_n0,B_n4}_*/` (all DONE),
`outputs/boombness/judge/tsb66{,b}j_{C_n4,C_n0,B_n4}_*/` (all DONE),
`configs/dcs_ts_pr066_amendment2.json`, `data/boombness_prompts/dcs_ts116_domain_split.json`,
`data/boombness_prompts/boombness_prompt_bank_ts116m_{button,basket}_bomb.jsonl`,
and the four rendered panels `reports/figures/F{2,3,5,8}_*.png` — **opened and looked at**, per the
new review duty.

---

## SUMMARY TABLE — worst first

| id | severity | one line | status |
|---|---|---|---|
| **S3-01** | **CRITICAL** | `S-008`'s two headline sentences are **falsified by the five layers entry 041 did not print**: at **L6 the codeword is BETTER aligned than `last` on BOTH codewords**, 62/67 and 55/67, surviving Holm at p ≤ 2.2e−06 | VERIFIED |
| **S3-02** | **CRITICAL** | `Q1b`'s sign test **has no null**: basket cell C dose 0 concept-present is exactly **0 in 113/113 domains**, so a negative delta is arithmetically impossible and 42/42 is a tautology. Domain-level p is **0.0082**, not 4.55e−13 | VERIFIED |
| **S3-03** | **CRITICAL** | the concentration ratio is **refuted by its own 3×3**: on the bomb residual axis the **knife** shift concentrates **3.10×** and the **gun** shift **2.03×** against bomb's 1.20. Random-direction null: **P(≥1.20) = 0.132** | VERIFIED |
| **S3-04** | **CRITICAL** | the two `Q2` tests are **not independent** and "replicates more strongly" **fails its own test** (dependent-r p = **0.618**); `x_button` predicts `y_basket` (0.509) **better than `x_basket` does** (0.447) | VERIFIED |
| **S3-05** | **CRITICAL** | the cell-B "replication identical to four decimals" is **the same 1130 rows**: all prompt hashes and **all 1130 generation strings byte-identical** across the two banks | VERIFIED |
| **S3-06** | MAJOR | `C-215`/`C3` was fixed in **one** block; two others still use the in-sample axis, and **F2 publishes 0.10556605** — the number the artifact says "may never be quoted" — under a caption reading "leave-one-domain-out" | VERIFIED |
| **S3-07** | MAJOR | **RENDER-AND-LOOK**: `F3`'s legend paints over L6–L7, the only two layers that contradict its title. `F8` is not a figure — it is a text card with no data. Scope cards still overlap the axes in F2/F3/F5 | VERIFIED |
| **S3-08** | MAJOR | the basket TEST-split ρ = 0.4615 is **p_Holm = 0.222** over the 8 small-split cells printed, is a **subset** of the pooled primary, and the two MDEs quoted beside it use **different power levels** | VERIFIED |
| **S3-09** | MAJOR | `R-207`'s `Q1b`/`Q1d` rows exist in **no script and no artifact** — `C8` recurring in the entry that opens by claiming `C8`'s lesson was applied. `Q1c` and the declared Holm are missing | VERIFIED |
| **S3-10** | MODERATE | the ASR ratio does **not** "track" the installation asymmetry: 0.3734, bootstrap CI **[0.2765, 0.4803]**, which **excludes 0.50** | VERIFIED |
| **S3-11** | MODERATE | the `Q2` outcome takes **5 distinct values** on basket with **71/113 tied at zero**; the Spearman is close to a two-group comparison and the Fisher-z CI is additionally miscalibrated | VERIFIED |
| **S3-12** | MODERATE | precision ledger: **1.202 is not reproducible by any rounding path** (exact 1.20077, from a mis-rounded 0.909); the 7× floor ratio has CI [3.33, 30.0]; five more | VERIFIED |

---

# (a) `S-009`'s concentration ratio — is it the right statistic, and what is its null?

**Answer: no, and it has no usable null. The observed 1.20 is at the 87th percentile of directions
that have nothing to do with `bomb`, and the same statistic applied to the other cells of its own
table ranks the bomb shift LAST.**

## What the statistic is

Entry 043 (lines 4291–4293) defines

```
concentration = (projection retained) / (axis retained)
              = [ <Δ, v̂_resid> / <Δ, v̂_full> ] / [ ‖v_resid‖ / ‖v_full‖ ]
```

with `Δ = mean_d(h_C − h_A)`, `v_full = v_lex(bomb)`, `v_resid` = `v_full` Gram–Schmidted against
`span{v_lex(knife), v_lex(gun)}`. Writing `c = ⟨v̂_full, v̂_resid⟩ = ‖v_resid‖/‖v_full‖`, it is
`⟨Δ, v̂_resid⟩ / (c·⟨Δ, v̂_full⟩)`.

That is a **ratio of two projections of the same vector onto two nearly-parallel directions**
(`c = 0.756` button, `0.708` basket). Its denominator is a **signed** quantity that may be
arbitrarily close to zero. A ratio of two correlated normals with a mean-zero-capable denominator is
Cauchy-like: **no finite mean, no finite variance, no usable null centre.**

## The reductio: the same statistic on the other eight cells of the same table

`outputs/dcs_succ/bombness_candidates_train.json`, `residual_axis_3x3` ÷ `metrics`, TRAIN, 67 domains:

| button L12 | shift bomb | shift knife | shift gun |
|---|---|---|---|
| **resid axis = bomb** | **1.201** | **3.101** | **2.028** |
| resid axis = knife | −0.195 | 3.161 | 1.645 |
| resid axis = gun | −0.520 | 3.074 | **6.019** |

| basket L11 | shift bomb | shift knife | shift gun |
|---|---|---|---|
| **resid axis = bomb** | **1.025** | **−3.213** | **1.698** |
| resid axis = knife | 0.497 | 4.342 | 1.606 |
| resid axis = gun | −0.378 | 2.856 | **−18.080** |

⛔ **On the bomb-specific residual axis, the knife shift concentrates 3.10× and the gun shift 2.03×,
against the bomb shift's 1.20.** If 1.20 licensed the sentence "~20 % concentration in the part knife
and gun cannot express", then the same arithmetic licenses "the *knife* shift concentrates 210 % in
the part knife cannot express" — which is nonsense. **The bomb diagonal is the SMALLEST positive
value in its own column.** No null distribution is needed to see that the statistic is not measuring
what its name says; the −18.08 and +6.02 on the gun diagonals show why (a denominator of −0.0163 and
+0.0051 gap units respectively).

## The null distribution, computed

Two nulls, 5000 draws each, axis geometry and Δ held at their measured values, independent
recomputation from the cached representations (`scratchpad/conc2.py`, `conc4.py`):

**Null A — a random direction in place of `v_lex(bomb)`** (the question as asked). For `r ~ N(0,I)` in
H = 4096, residualising against a 2-dimensional span leaves `axis retained = 0.99975` (mean over
5000 draws; min 0.99747), so the ratio is driven entirely by the projection term.

| quantile | min | 1 % | 5 % | 25 % | **median** | 75 % | 95 % | 99 % | max |
|---|---|---|---|---|---|---|---|---|---|
| **button L12** | −258.0 | −1.540 | 0.393 | 0.900 | **0.991** | 1.084 | 1.562 | 3.961 | +383.1 |
| **basket L11** | −198.6 | −3.855 | −0.184 | 0.772 | **0.961** | 1.146 | 2.165 | 8.116 | +766.8 |

* the null **is** centred near 1 — entry 043's reading of "1.0 = uniform spread" is correct in
  expectation — but the spread is enormous and the tails are Cauchy;
* **P(random ≥ 1.20) = 0.132** on button. The observed 1.201 sits at the **86.8th percentile**.
  One-sided p ≈ **0.13**. It is not significant against a direction chosen at random.
* **P(random ≥ 1.025) = 0.393** on basket — the 61st percentile, dead centre.

**Null B — a random direction matched to `v_lex(bomb)`'s geometry** (forced to `axis retained =
0.7564`, so the residualisation removes the same fraction). Median **0.072**, 5–95 % [−1.964, 1.824],
1–99 % [−8.94, 8.73], min −22208, max +345. **P(≥ 1.188) = 0.075.** Also not significant, and the
null spans four orders of magnitude.

## What *does* have an interval, and what the entry omitted

Entry 043 publishes `1.202` and `1.025` as **bare point estimates with no interval of any kind** —
the headline of `S-009` and of the answer to Matan's §2.1 (entry 044, lines 4344–4347). A domain
bootstrap that rebuilds the axes on each draw (B = 1000):

| | observed | domain bootstrap CI95 | P(boot ≤ 1) |
|---|---|---|---|
| button L12 | 1.2008 | **[1.089, 1.302]** | 0.001 |
| basket L11 | 1.0247 | **[0.927, 1.129]** | 0.341 |

So under *domain* sampling the button ratio does exceed 1 and the basket ratio does not — which is
the entry's qualitative reading. But the domain bootstrap answers "is this stable over domains?",
not "is this axis special?". The question `S-009` poses is the second one, and its answer is the
random-direction null above: **p ≈ 0.13**, not significant.

## And the two-codeword contrast is a layer-selection artefact

Entry 043 reads button at **L12** and basket at **L11** — each codeword's *own* peak-`B1` layer, a
criterion unrelated to concentration. The full layer profile (recomputed from the artifact):

| layer | L6 | L7 | L8 | L9 | L10 | L11 | L12 | L13 | L14 |
|---|---|---|---|---|---|---|---|---|---|
| **button** | 0.975 | 1.073 | 1.017 | 0.885 | 1.017 | 1.185 | **1.201** | 1.157 | 1.156 |
| **basket** | 0.804 | 0.907 | 0.861 | 0.805 | 0.901 | **1.025** | 1.055 | 1.078 | **1.162** |

⛔ At **L14 the two codewords agree — 1.156 vs 1.162.** Read at a common layer the "1.20 vs 1.02, so
it does not replicate" contrast (lines 4292–4300) disappears at L14, halves at L12 (1.201 vs 1.055),
and at L6–L10 both codewords sit *below* 1. The honest summary of the table is: **the ratio hovers
around 1 at every layer on both codewords (0.80–1.20) and drifts up in the late layers**; a single
layer per codeword, chosen by a different criterion, is not a replication test.

**None of this overturns the entry's conclusion — `S-009` concludes "no specificity claim is
licensed", and that conclusion survives, indeed strengthens.** What does not survive is the
arithmetic offered as its support: "~20 % concentration on the development codeword" (line 4298) is
one draw in eight of what an unrelated direction produces, and is smaller than the number the
*knife* shift produces on the same axis.

---

# (b) `S-008`'s position contrasts under Holm

**Answer: the family is 36, not 18; entry 041 printed 16 of them; and the five layers it dropped
contain sign reversals that survive Holm and falsify both headline sentences.**

## The family

`outputs/dcs_succ/b1_position_control.json` holds **9 layers × 2 banks × 2 contrasts = 36** paired
`cos` contrasts. Entry 041 (line 4129) says the grid contains **18**. Even counting one contrast at a
time it is 18 **per contrast**, 36 in total. The entry prints **16** — four layers (L9, L11, L12,
L13) of nine — with **no stated selection rule**; `scripts/dcs_succ_b1_position_control.py` computes
all nine layers (`for L in common_layers`, line 143) and the choice of four was made after the
numbers existed.

Every p below was re-derived independently with an exact two-sided binomial and matches the
artifact's `sign_p` to full precision in all 36 cells.

## Holm over the full 36-cell family, FWER 0.05

**Contrast 2 (codeword − `last`).** 16 of 18 cells survive Holm. Two do not (button L7 p = 0.625,
basket L7 p = 0.328). And **two of the survivors have the OPPOSITE sign**:

| cell | mean cos diff | domains + | raw p | **p_Holm(36)** |
|---|---|---|---|---|
| **button L6 vs last** | **+0.13569** | **62/67** | 1.42e−13 | **3.55e−12** |
| **basket L6 vs last** | **+0.10766** | **55/67** | 1.03e−07 | **2.16e−06** |

⛔ **At L6, on BOTH codewords, the codeword is better aligned with the local button→bomb axis than
the final prompt token is, in 62 and 55 of 67 domains, surviving correction over the whole grid.**
The raw cosines make it unmissable: button L6 codeword **0.1565** vs `last` **0.0208** (7.5×);
basket L6 codeword **0.1486** vs `last` **0.0410** (3.6×).

Entry 041 line 4141: *"A larger fraction of the Doublespeak shift points along the local button→bomb
axis at the FINAL PROMPT TOKEN than at the codeword, in 65–66 of 67 domains, on both codewords, **at
every layer**."* — **at every layer is false for the nine layers measured.** It is false at L6 on both
banks (reversed, significant) and at L7 on both banks (null).

*"in 65–66 of 67 domains"* is also not a property of the printed table. Counting domains where the
codeword is the *worse*-aligned site (67 − `n_positive`), the eight contrast-2 cells entry 041 prints
are: button L9 **66**, L11 **59**, L12 **65**, L13 **62**; basket L9 **65**, L11 **62**, L12 **66**,
L13 **66**. **Three of the eight (59, 62, 62) fall outside the quoted 65–66 range**, and the widest
miss — button L11 at 59/67 — is 8 domains short of the figure the verdict paragraph repeats.

**Contrast 1 (codeword − `following`).** Three cells survive Holm over the full 36 — and over the
18-cell contrast-1 family the entry names, the same three survive:

| cell | mean cos diff | domains + | raw p | p_Holm(36) | p_Holm(18) |
|---|---|---|---|---|---|
| **button L8** | **+0.05754** | 48/67 | 5.22e−04 | **0.0104** | **0.0094** |
| **basket L7** | **−0.05658** | 19/67 | 5.22e−04 | **0.0104** | **0.0094** |
| **button L6** | **+0.07937** | 47/67 | 1.31e−03 | **0.0235** | **0.0209** |
| button L11 | +0.02878 | 44/67 | 0.0139 | 0.237 | 0.209 |
| basket L8 | +0.03204 | 43/67 | 0.0271 | 0.434 | 0.380 |
| basket L14 | −0.05586 | 24/67 | 0.0271 | 0.434 | 0.380 |
| button L12 | +0.01940 | 42/67 | 0.0498 | 0.697 | 0.598 |
| button L13 | +0.01074 | 42/67 | 0.0498 | 0.697 | 0.598 |

⛔ Entry 041 line 4128: *"only one cell of eight reaches p = 0.014 — which would not survive a
correction over the 18 comparisons the grid contains."* Three things are wrong.
1. **Three** of its own eight printed cells are at p ≤ 0.05 (button L11 0.0139, button L12 0.0498,
   button L13 0.0498 — the latter two printed as "p = 0.05", which reads as *not* significant).
2. The grid contains **36**, not 18.
3. **Three cells DO survive Holm** — and none of them is the one quoted. Two of them
   (button L6 +0.079, button L8 +0.058) say the codeword is *better* aligned than its neighbour.

## Does `S-008`'s conclusion survive?

**The direction survives; both published sentences do not.**

* *"statistically indistinguishable from the adjacent neutral token"* (lines 4128 and 4151) —
  **FALSE.** It is distinguishable in 3 of 18 layer×bank cells at FWER 0.05.
* *"the final prompt token carries a higher-aligned shift … on both codewords, at every layer"*
  (4141, 4151) — **FALSE.** Reversed and significant at L6 on both codewords.
* What is defensible after correction: **the codeword's alignment advantage over its neighbour has
  no consistent sign across layers** (+0.079, +0.058, −0.057 among the Holm survivors), and **from
  L8 onward the readout position is better aligned on both codewords**. That is still a negative for
  localisation — but a layer-dependent one, and the entry reached the flat version by dropping the
  layers that argue the other way.

**House-rule note:** entry 041's tables print p with **no attainable floor** beside them (the floor
is 1.355e−20 at n = 67, and the artifact carries it as `sign_p_floor`). Every other table in this
phase carries the floor.

---

# (c) `R-207`: are basket `Q2` and button `Q2` two independent tests?

**Answer: no. They are one sample of 113 domains measured twice, the predictors correlate at 0.726,
and "replicates more strongly" fails a dependent-correlation test at p = 0.618.**

Recomputed from scratch over the 113 analysed domains (both codewords, same domain list):

| | ρ |
|---|---|
| ρ(x_button, y_button) — the frozen `Q2` | **+0.3961** |
| ρ(x_basket, y_basket) — the replication | **+0.4468** |
| **ρ(x_button, x_basket)** — the two predictors | **+0.7256** |
| ρ(y_button, y_basket) — the two raw outcomes | +0.2713 |
| ρ(cp_button, cp_basket) — the two corrected outcomes | +0.3991 |
| **ρ(x_button, y_basket)** — cross | **+0.5090** |
| ρ(x_basket, y_button) — cross | +0.3700 |

## 1. The difference is not significant

Raghunathan–Rosenthal–Rubin test for two **dependent, non-overlapping** correlations on the same
n = 113 units: cov(z) = 0.156, SE = 0.124, **z = 0.498, p = 0.618**. (Even the wrong test — treating
them as independent samples — gives p = 0.647.)

⛔ ENTRY 047's title (*"`Q2` replicates more strongly"*) and line 4512 (*"basket's ρ = 0.4468 exceeds
button's 0.3961"*) assert an ordering that the data do not distinguish from equality. **"Replicates
more strongly" is not defensible; "replicates, with an indistinguishable point estimate" is.**

## 2. The button predictor predicts the basket outcome better than the basket predictor does

**ρ(x_button, y_basket) = 0.509 > ρ(x_basket, y_basket) = 0.447.** Partial correlations:

| partial | ρ | p |
|---|---|---|
| **ρ(x_basket, y_basket \| x_button)** | **+0.131** | **0.170** |
| **ρ(x_button, y_basket \| x_basket)** | **+0.300** | **0.0012** |
| ρ(x_button, y_button \| x_basket) | +0.200 | 0.035 |
| ρ(x_basket, y_button \| x_button) | +0.131 | 0.170 |

⛔ **Once button's installation is controlled, basket's own installation adds nothing to predicting
basket's ASR (p = 0.17).** The reverse is not true. The "installation → attack success" link is
carried by a **domain-level factor common to both codewords** — how answerable the domain is — not by
the codeword-specific installation measurement. Entry 047's ✅ bullet *"Two codewords, two
**independent** behavioural waves"* (line 4519) is **false**: the second wave is statistically nested
in the first.

## 3. Effective n

The house rule says the independence unit is the **domain**. The pair of tests spans **113 domains,
not 226**. If one insisted on pooling, the design effect from ρ(y_button, y_basket) = 0.271 gives
n_eff = 2·113/(1+0.271) = **178**, and from the predictors' ρ = 0.726 it gives 131 — but neither is
the right frame: **the replication buys robustness to the choice of codeword, not additional
domains.** Nothing in entry 047 says otherwise, and nothing should be allowed to imply it.

## 4. And one of the "replicated" arms is literally the same data — see S3-05.

---

# S3-05 (CRITICAL) — the direct-harmful control arm is the SAME 1130 rows on both codewords

Entry 041: *"`basket_bomb` cell B dose 4 judged — ASR@0.5 **0.0088** … *identical to `button`'s
direct-harmful baseline to four decimals*, which is a **clean replication of the control arm**."*
Entry 047, line 4500: *"the direct-harmful control is **identical to four decimals** on both
codewords (0.0071), which is what a control arm should do."*

Recomputed over the two bank files
(`data/boombness_prompts/boombness_prompt_bank_ts116m_{button,basket}_bomb.jsonl`, 22 272 rows each,
keyed by `(cell, prompt_id)`; key sets identical):

| cell | query_kind | dose | full_prompt identical across banks? |
|---|---|---|---|
| A | all | all | **differs, 5568/5568** |
| **B** | **behavioral** | 0 / 4 / 8 | **IDENTICAL, 232 / 1160 / 464** |
| B | semantic_forced_choice | all | differs |
| B | semantic_one_word | all | identical |
| C | all | all | differs, 5568/5568 |
| **E** | **behavioral** | 0 / 4 / 8 | **IDENTICAL** |

And on the generation runs themselves —
`outputs/boombness/score_behavior/tsb66_B_n4_20260909_212431_276958/gens.jsonl` against
`outputs/boombness/score_behavior/tsb66b_B_n4_20260910_020713_3997667/gens.jsonl`, joined on
`(prompt_id, query_kind, family_id)`:

```
key sets equal              : True   (1130 rows each)
prompt_sha16 identical      : 1130 / 1130
generation string identical : 1130 / 1130   (differences: 0)
```

⛔ **The two "control arms" are byte-identical prompts producing byte-identical greedy completions.**
"Identical to four decimals" is not a replication; it is arithmetic. The agreement was never at risk,
and the phrase invites a reader to count it as independent corroboration. It also means the basket
cell-B GPU run re-generated 1130 rows that already existed, and that **`Q1d`'s comparison arm is
shared between the two codewords**, so basket `Q1d` is not independent of button `Q1d` either.

*Correction to this review's own brief*: the brief states the two banks "share cell A byte-identically".
They do not — cell A differs in all 5568 rows (the codeword is in the query and the demos). It is
cells **B and E**, at `behavioral` and `semantic_one_word`, that are shared. The consequence is worse,
not better: cell B is a live arm in `R-207`.

---

# (d) `Q1b` at 42/42 with 71 ties — is the sign test over informative domains the right test?

**Answer: no, and in this instance the test has no null at all. A negative delta is arithmetically
impossible, so 42/42 is a tautology, not a measurement.**

Recomputed from the run directories (concept-present per-domain rates, 113 domains, three exclusions
applied):

| | basket | button |
|---|---|---|
| domains + | **42** | 77 |
| domains − | **0** | 2 |
| ties | **71** | 34 |
| ties that are (0, 0) | **71 of 71** | 34 of 34 |
| **domains with cell C dose-0 concept-present > 0** | **0 of 113** | 2 of 113 |
| domains with cell C dose-4 concept-present > 0 | 42 of 113 | 79 of 113 |

⛔ **The basket dose-0 reference arm is exactly zero in every one of the 113 domains.** Concept-present
ASR is non-negative, so `Δ = cp4 − cp0 = cp4 ≥ 0` **by construction**. `Q1b` on basket is
arithmetically the statement "cell C dose 4 concept-present ASR is greater than zero", and the
informative set is *defined* by the outcome being positive. The sign test's null — P(+) = P(−) = ½
given informative — is **false a priori**, with P(−) = 0. The house rule "a gate that passes on an
empty selection is not a gate" is the same shape: **a test that cannot return a negative is not a
test**, and `p = 4.55e−13 "at its floor"` is the probability of 42 heads from a coin that has no
tails. (Button's version is *not* degenerate — 2 of 79 are negative — so this defect is specific to
the replication entry.)

## What the tie structure actually means

71 of 113 domains are tied at zero because **in 71 domains the basket attack produces no
bomb-semantic content at all**. Those are not "no difference"; they are "the attack does nothing".
`missing != zero` has a mirror here: **zero != uninformative**. A domain where the attack produces
nothing is the most informative kind of evidence about how far the attack generalises, and the
published test discards all 71.

## The right test, and what it gives

The domain is the independence unit and there are 113 of them. Counting ties conservatively against
the hypothesis (Fisher's rule) over all 113:

| | published (informative only) | **domain-level, ties against** |
|---|---|---|
| basket `Q1b` | 42/42, **p = 4.55e−13** (floor 4.55e−13) | 42/113, **p = 0.0082** (floor 1.93e−34) |
| button `Q1b` | 77/79, p = 1.05e−20 | 77/113, p = 1.44e−04 |

⛔ **Eleven orders of magnitude.** The effect is still there and still significant — this is a
correction to the *evidence strength*, not to the direction — but `4.55e−13 "at its floor"` cannot be
published for a contrast whose informative n was chosen by the outcome.

## Three denominators in one row

Entry 047 line 4493 reads: `Δ = +0.0522 | CI [0.0372, 0.0690] | 42/42 | p = 4.55e−13`.
Recomputed: **Δ and the CI are over all 113 domains** (I reproduce +0.0522, bootstrap CI
[0.0372, 0.0690] exactly); **the count and the p are over 42**. Over the 42 informative domains the
mean delta is **0.1405, CI [0.1167, 0.1690]** — 2.7× the printed one. A reader who takes Δ, the CI
and the p as describing one population is misled by the row's own layout.

`Q1d` (basket C dose 4 − B dose 4, +0.0451, CI [0.0301, 0.0611], 41/42, p = 1.96e−11 — all reproduced
exactly) has the same structure: **cell B concept-present is > 0 in 1 of 113 domains**, and 71 ties,
all (0,0). So `Q1b` and `Q1d` are **not two contrasts**; both reduce to "cell C dose 4 concept-present
> 0", measured against two arms that are identically zero. They are reported as two evidence lines.

---

# (e) the basket TEST split, ρ = 0.4615 at n = 23, against an MDE of 0.556

**Answer: neither evidence nor winner's curse — it is an uninformative subgroup readout of the
primary, and its nominal significance does not survive any correction for the eight small-split cells
that were printed.**

## 1. Multiplicity

The small splits printed across the two codewords and two outcomes are eight cells:

| cell | p | **p_Holm(8)** |
|---|---|---|
| **basket test, raw** | **0.0278** | **0.222** ns |
| basket test, concept-present | 0.0340 | 0.238 ns |
| button test, raw | 0.078 | 0.468 ns |
| button test, concept-present | 0.133 | 0.665 ns |
| button val, cp / raw; basket val, cp / raw | 0.462 / 0.508 / 0.659 / 0.737 | 1 ns |

Bonferroni over 8 = 0.222; over the 16 ρ cells printed across entries 042 and 047 = 0.445.
**Nothing in the small splits is significant after correction.**

## 2. It is not an independent test — it is a subgroup of the primary

The pooled `Q2` (n = 113) **contains** those 23 test domains. A significant subgroup of an already
significant whole adds no information; what a held-out split can do is *contradict*, and the other
n = 23 split does exactly that (basket validation **ρ = −0.0733**). Entry 047 bolds the confirming
split and gives the contradicting one a caveat sentence. That is REVIEW-2's **S-03** shape (*"prints
only the split rows where the correlation strengthens"*) — **unrepaired**, recurring on the
replication codeword with the emphasis flipped. Not re-reported here beyond naming it.

## 3. Winner's curse: quantified, and it runs the other way

Fisher-z critical |ρ| at n = 23, α = 0.05 two-sided: **0.4122**. Assuming the pooled ρ = 0.4468 is the
truth:

* **P(significant at n = 23) = 0.575** — a significant test split was *more likely than not*. It is
  not a surprise and it is not a fluke.
* **E[r | significant] = 0.552** against E[r] = 0.4295 — a +0.123 selection inflation. The observed
  **0.4615 is well BELOW that conditional mean**, i.e. it is a *low* draw among the significant ones.

So the number is neither surprising nor especially inflated. What it is, is **uninformative**: it
carries no evidence the pooled test did not already carry, and it cannot survive correction for the
looks that were taken.

## 4. And the two MDEs quoted beside it use different power levels

`configs/dcs_ts_pr066_amendment2.json` lines 198–208 declare both power levels:

```
mde_rho_at_n113  : power_0.80 = 0.2609   power_0.90 = 0.2996   <- declared_mde is the 0.90 number
mde_rho_at_n23   : power_0.80 = 0.5556   power_0.90 = 0.6199
```

Entry 047 line 4512–4514: *"clears the declared MDE of **0.2996** … where the design's own MDE is
**0.556**"*. The first is the **0.90**-power figure, the second the **0.80**-power figure, in one
sentence. At the declared power level the n = 23 MDE is **0.6199**, and 0.4615 is further below it
than the entry states. (The prereg's own prose at line 98 is the source of the mixing: it quotes
"0.556 at 23 domains against 0.261 at 113" — both 0.80 — while `declared_mde` is 0.2996.)

Both MDEs reproduce exactly from `atanh(ρ)·√(n−3) = z_{0.975} + z_{power}`, verified.

---

# S3-06 (MAJOR) — `C-215`/`C3` was fixed in one block; two others still read the axis they may not read

`scripts/dcs_succ_bombness_candidates.py` line 476 now takes the **leave-one-out** axis inside
`interaction_decomposition`, and entry 043 correctly reports that `B1` there matches `B1` proper to
0.00e+00. But the same file still uses `vfull` — the **in-sample** mean axis — in two other blocks
that feed published output:

* **line 505–546, `residual_axis_3x3`**: `resid_axes[target]` is built from `vfull[target]`, and
  `vals = dot(delta_CA[shift_c][d], rhat_c)` uses that same in-sample axis for every domain.
  **This is the numerator of `S-009`'s concentration ratio**, whose denominator (`B1`) is LOO.
  Recomputed on the cached representations:

  | | published (mixed axis) | fully LOO | fully in-sample |
  |---|---|---|---|
  | button L12 | **1.2008** | **1.1927** | 1.1880 |
  | basket L11 | **1.0247** | **1.0179** | — |

  The published headline is **neither** of the two internally consistent quantities.

* **line 557, `cell_coordinates_on_bomb_axis`**: `vb_hat_full = _unit(stack([delta_EA["bomb"][d]…]).mean())`
  — in-sample, and the artifact's own `_reading` says so. Its cell-C value is
  **0.10556605299541143** (button L12) and **0.13749508226099563** (basket L11).

⛔ **0.10556605 is the exact number the same artifact's `leakage_probe` block declares
"may never be quoted as a control that the effect survived"** (the probe's own draws average
0.10560041), and the exact number `C-215`/`C3` identified as the in-sample contamination. It is now
**published in figure F2** (`reports/figures/F2_cell_coordinates.png`, cell-C bar labelled **0.106**)
and in entry 046's panel table (line 4432: *"A 0.000, **C 0.106**, B 0.837, E 1.000"*).

Worse: **F2's scope card states the metric as `v_lex leave-one-domain-out`** —
`scripts/dcs_succ_figures.py:91` hard-codes that string, while line 74 reads
`cell_coordinates_on_bomb_axis`, the in-sample block. **The caption asserts the correction the number
does not have.** The LOO value is 0.10444100 / 0.13658738; the figure shows 0.10557 / 0.13750.

---

# S3-07 (MAJOR) — RENDER AND LOOK: three of the four panels fail on inspection

All four were rendered and opened. `C-216` (entry 046) found a scope card painting over the K10–K14
rungs of F5 and reported the fix as "the scope card now lives **outside the axes**, where it cannot
cover data". **The same defect is present in F3 in a worse form, and the scope card is still inside
the axes in all three plotted panels.**

### F3 — the legend hides the two layers that contradict the title

`reports/figures/F3_position_layer_map.png`, titled *"B1 is NOT localised: the codeword matches its
neighbour and trails the readout position"*.

⛔ **The opaque legend box in the upper-left of each panel sits on top of x = 6 and x = 7.** Those are
exactly the two layers where the finding reverses:

| | codeword | following | last | verdict |
|---|---|---|---|---|
| button **L6** | **0.1565** | 0.0772 | **0.0208** | codeword **largest**, 7.5× `last` |
| basket **L6** | **0.1486** | 0.1448 | **0.0410** | codeword **largest**, 3.6× `last` |
| basket L7 | 0.1829 | **0.2395** | 0.1949 | `following` largest |
| L8–L14, both | — | — | largest | `last` largest (the title's claim) |

The reversals are not noise: they carry p_Holm = 3.55e−12 (button) and 2.16e−06 (basket) over the
full 36-cell family. **A figure asserting "trails the readout position" hides, behind its own legend,
the two layers where it leads it by 3.6–7.5×.** This is `C-216`'s finding one entry later, in the same
figure set, undetected — and unlike `C-216`'s case the hidden data *contradicts* rather than supports
the caption.

Also in F3: the scope card overlaps the axes and **covers the x-axis label** (it renders as "blo…");
the y-axis label `POSITION-PORTABLE` is drawn through the figure title; and roughly 60 % of the canvas
below the axes is empty.

### F8 — not a figure

`reports/figures/F8_installation_vs_asr.png` is **a page of monospaced text**: ρ, p, CI, the predictor
binding and a one-line conclusion. There is **no scatter, no data, no 113 points**. Plan §36 attaches
to each panel *"n independent domains; split; CI; controls; exact metric"* — F8 satisfies the caption
requirements and contains no evidence. `C-216`'s own lesson (*"Every statistic in that panel was
correct; the picture was not"*) applies literally.

This matters statistically: the `Q2` outcome takes **7 distinct values on button and 5 on basket**,
with 30 % and **63 %** of domains at exactly zero (S3-11). A scatter would show at a glance that the
Spearman is close to a zero/non-zero split. A text card cannot.

### F5 and F2 — the scope card is still on the axes

F5's K10–K14 rungs are indeed restored ✓, but the scope card **covers the x-axis label** ("K (the cut
reaches …" is truncated) and the y-axis label is clipped. F2's scope card **covers the `B` and `E`
tick labels entirely** and truncates the `C` label. The card was moved off the *data* and not off the
*axes*, and the axis identity is part of "exact metric".

---

# S3-09 (MAJOR) — `R-207`'s `Q1` numbers exist in no script and no artifact

Entry 047 opens: *"scored by the SAME code as `button` — the scripts were parameterised
(`--gen-prefix`, `--judge-prefix`, `--bank-key`, `--readout-glob`) rather than copied, which is
`C8`'s lesson applied before it could bite again."*

Verified state of the repo:

| script | has the four flags? | computes Q1b/Q1d? | basket artifact |
|---|---|---|---|
| `scripts/dcs_succ_q2_concept_present.py` | **yes** (all four) | no (Q2 only) | `q2_concept_present_basket.json` ✓ |
| `scripts/dcs_succ_concept_presence.py` | `--gen-prefix`, `--judge-prefix` only | **no** — no paired contrast, no CI, no sign test | `concept_presence_basket.json` ✓ (arm rates only) |
| `scripts/dcs_succ_pr066_behaviour.py` — **the Q1 analyzer** | **none** (`--config/--selftest/--mutate/--plan/--train-only/--installation-run/--rejudge-run/--seed/--n-boot/--out-md/--out-json`) | yes | **none** |

There is **no `pr066_behaviour` artifact for basket**; `outputs/dcs_succ/pr066_behaviour.json` is
02:34, three hours before the basket C dose-4 arm completed. A grep for `0.0522`, `0.0451`,
`4.55e-13`, `1.96e-11`, `0.0372`, `0.0690`, `0.0301`, `0.0611` across `outputs/` and `reports/`
returns 34 hits, **none of them in `outputs/dcs_succ/` or `reports/`**.

⛔ **The `Q1b`/`Q1d` row of the phase's replication entry — Δ, 95 % CI, domain count and p — was
computed inline and stored nowhere.** I reproduce every one of the eight numbers exactly from the run
directories, so they are *correct*; the complaint is `C8`'s exactly, in the entry that claims `C8`'s
lesson was applied.

Two further gaps: the frozen analyzer's declared Q1 family is **`Q1b`/`Q1c`/`Q1d` with Holm across
the family** (`dcs_succ_pr066_behaviour.py:1456–1458, 1649`). Entry 047 reports **`Q1b` and `Q1d`
only** — `Q1c` (C − A at dose 4) is absent for basket — and applies **no Holm**. With p = 4.55e−13 and
1.96e−11 Holm would not change the verdicts, but a preregistered family member is missing from a
preregistered family and the correction the design declares was not run.

---

# S3-10 (MODERATE) — the ASR ratio does not "track" the installation asymmetry

Entry 047 line 4496–4498: *"the attack works on the replication codeword and is ~2.7× weaker
(0.0522 vs 0.1398) — against an **installation ratio of 46/92 = 0.50**. Same direction, and the
magnitude gap **tracks** the installation asymmetry."*

Domain bootstrap (B = 20 000, resampling the 113 domains, paired):

```
concept-present ASR ratio basket/button = 0.3734    CI95 [0.2765, 0.4803]
```

⛔ **The CI excludes 0.50.** The attack falls off *faster* than installation does; the two ratios are
distinguishable. And the comparison is between a **thresholded count** (46 vs 92 domains "installing")
and a **continuous mean rate** — different functionals of different variables. Entry 047's ✅ bullet
*"a magnitude difference that is **predicted** by the installation asymmetry rather than unexplained
by it"* (line 4522) is not supported by the numbers in the same entry.

---

# S3-11 (MODERATE) — the `Q2` outcome is 5-valued with a 63 % tie mass

Recomputed over the 113 domains (10 rows per domain, so y ∈ {0, 0.1, …, 1}):

| | zeros | distinct values | modal value |
|---|---|---|---|
| button raw ASR | 9 (8.0 %) | 9 | 0.2 (22 domains) |
| button concept-present | 34 (30.1 %) | 7 | 0.1 (36) |
| basket raw ASR | 23 (20.4 %) | **7** | 0.1 (41) |
| **basket concept-present** | **71 (62.8 %)** | **5** | **0.0 (71)** |
| predictor x (both) | — | 113 (continuous) | — |

The permutation p is valid under this structure (it permutes the observed y and inherits its ties),
and the analyzer's `ranks()` does average ties correctly — verified, and its mutation harness catches
the loss of tie-averaging. Two consequences remain:

1. **ρ = 0.4868 on basket concept-present is largely a two-group statistic.** With 63 % of the
   outcome at a single tied value, the Spearman is close to a rank-biserial comparison of "the attack
   produced concept content" vs "it did not". That is a defensible thing to measure, but it is not the
   graded dose–response the phrase "installation predicts *where it lands*" (entry 044, line 4351)
   implies.
2. The Fisher-z CI (REVIEW-2 **S-09**, unrepaired: `1/√(n−3)` is the *Pearson* SE) is **additionally**
   miscalibrated by the tie mass — the standard SE assumes a continuous bivariate normal. This is a
   new aggravation of an already-reported defect, not a new defect.

---

# (f) S3-12 — quoted at more precision than the design supports

| quoted | where | what the data support |
|---|---|---|
| **`1.202`** (button concentration) | entry 043 L4292; entry 044 | **not reproducible by any path.** Exact from the artifact: **1.20077**. The printed component `0.909` is a mis-rounding of **0.908209** (→ 0.908); `1.202` = 0.909/0.756. Correct to 3 d.p.: **1.201**. Domain bootstrap **[1.089, 1.302]** — four significant figures on a ±0.11 quantity, published with no interval |
| **`1.025`** (basket) | entry 043 L4293 | exact 1.02467 ✓ — but the same line prints its components as `0.725 / 0.708`, whose quotient is **1.024**. The row and the ratio disagree in the last digit |
| **`0.4468` exceeds `0.3961`** | entry 047 L4512 | dependent-r test **p = 0.618**. The Fisher SE at n = 113 is 0.096 in z (≈0.077 in ρ near 0.44); the 4th decimal is two digits past the resolution of the comparison being made |
| **`p = 0.0278`**, `p = 0.034` | entry 047 L4510 | from **10 000** permutations: Monte-Carlo 95 % band **±0.0033** at p = 0.028, from a **single** seed (202609061). Three significant figures is one too many; and at n = 23 with a 5-valued y the permutation lattice is coarse |
| **"7×"** codeword-dependent floor | entries 042, 047 L4526, Slack draft ¶5 | **7.00, domain bootstrap CI [3.33, 30.0]**. The denominator arm has **5 positive rows in 226** (5 domains of 113). A 7× constant is quoted three times with no interval |
| **`4.55e−13` "at its floor"** | entry 047 L4493 | the floor `2/2^42` is set by an **outcome-selected** n (S3-02). The domain-level p is **0.0082** |
| **"~14 sd above random directions"** | entry 043 L4315, entry 044 L4338, claim table row 8, **Slack draft line 29** | REVIEW-1 **O10**, **unrepaired**. It divides by `between_draw_sd_from_12_draws`, the statistic the artifact's own note says *"the analytic value … is the one to quote"*. **NEW:** the analytic values are **12.31 (button)** and **16.37 (basket)** — "~14" is neither, and is not a single figure for the two codewords it is applied to |
| **"identical to four decimals"** | entries 041, 047 L4500 | the arms are byte-identical data (S3-05). Four decimals of agreement were never at risk |
| **MDE `0.2996` vs `0.556`** | entry 047 L4512–4514 | 0.90-power and 0.80-power figures in one sentence; at the declared level the n = 23 MDE is **0.6199** |
| **"p = 0.05"** (button L12, L13 vs following) | entry 041 L4126 | the value is **0.0498** — below α, printed as if at it, in the same table where 0.0139 is printed as "0.014" |
| **"2.7× weaker"** | entry 047 L4496 | 0.1398/0.0522 = 2.678; the ratio's bootstrap CI is [0.277, 0.480] on the inverse, i.e. **2.08× to 3.62×** |

---

# ENTRY 045 — the collaborator draft (`reports/DCS_SUCC_SLACK_DRAFT_MATAN_MAHMOOD_20260910.md`)

Correctly marked **DRAFT ONLY / NOT SENT**, and nothing was transmitted. Statistical content that
should not go out in its present form:

1. **¶3, "sits ~14 sd above random directions"** — S3-12. The analytic figures are 12.3 and 16.4.
2. **¶3, "not localised at the codeword — statistically indistinguishable from the neutral token one
   position later, and *worse* aligned than the final prompt token"** — both clauses are falsified by
   the artifact's own grid under Holm (S3-01). Three neighbour contrasts survive correction, two of
   them positive; and at L6 the codeword is better aligned than the final token on **both** codewords.
3. **¶3, "its concept specificity, measured properly, is 1.02× on the replication codeword. 1.0 means
   no specificity at all"** — the statistic has no usable null, its bomb diagonal is outranked by the
   knife shift on the same axis, and at L14 the two codewords read 1.156 / 1.162 (S3-03). The
   *conclusion* (no specificity licensed) is right; this sentence is not the reason.
4. **¶2, "sign positive in all three splits"** — true for button raw (0.4836 / 0.1435 / 0.3779) ✓, but
   it silently upgrades the prereg's declared criterion, which is "consistent in **at least 2 of 3**"
   (`configs/dcs_ts_pr066_amendment2.json:157`). On the replication codeword the validation split is
   **−0.0733**, so the upgraded phrasing would be false for basket.
5. **¶2, "It strengthens to 0.421"** — 0.3961 → 0.4206 on the same 113 domains with a nested outcome;
   no test is offered and the difference is inside noise. "Is unchanged under the correction" is the
   safe statement and makes the same point against the false-positive objection.
6. **¶5, "it flips 13.7 % of labels, κ = 0.44"** — REVIEW-2 **S-10** (iid over 226 rows when the unit
   is 113 domains; clustered κ CI [0.281, 0.589]), **unrepaired**, and the draft carries the point
   estimates with no interval.
7. **¶5, "The floor is also codeword-dependent — 15.5 % for `button`, 2.2 % for `basket`"** — correct
   point estimates (0.1549 / 0.0221 ✓) but the basket figure rests on **5 positive rows** and the
   ratio's CI is [3.3, 30] (S3-12).

The draft's ¶5 warning about **prior** ASR numbers is correctly hedged ("I would not revise any
published number on this alone") and correctly flagged to Omer in entry 045. The `127 of 461` count is
outside this part's scope and was not verified here.

---

# ENTRY 044 — the claim table

Row 8 (*"~14 sd over 12 random directions"*) carries the REVIEW-1 **O10** defect, unrepaired.
The §2.1 answer block (lines 4338–4347) inherits three of the sentences corrected above:
*"~14 sd"*, *"not localised at the codeword (indistinguishable from the adjacent neutral token;
worse-aligned than the readout position)"*, and *"its concept specificity is 1.02× on the replication
codeword"*. All three are load-bearing in the deliverable and all three need the qualifications in
S3-01 and S3-03. The block's ⛔ conclusions — that `B1` is not bombness, that the codeword row is a
conduit and not a store — are **not** overturned by anything in this review; the supporting arithmetic
is.

---

# `C-214` (entry 040) — assessed, and it holds

The gap-unit denominator artefact is correctly diagnosed and correctly rejected pre-publication. I
confirm the denominators from the artifact: `gap_norm` at button L12 is **3.8598** at the codeword,
**1.8102** at `following` and **0.7214** at `last`, and across L6→L14 the `last` reference gap runs
0.113 → 1.45 against the codeword's 3.33 → 5.20 — a 30× swing, exactly as stated. `cos` is the right
choice: it is scale-free in both terms and it is what I used throughout part (b). The artifact
correctly marks `paired_cos_*` with `_this_is_the_portable_one` and stamps the `_WARNING` on the
gap-unit rows. **No defect found in `C-214`.** Its one downstream cost is that the entry's
"REVIEW-1 `A6` … the same defect biting somewhere it changes a conclusion" is *also* true of the two
blocks in S3-06, which were not swept when `C3` was fixed.

---

# What would settle each of these

1. **S3-01** — publish all nine layers of both contrasts with Holm over 36, or declare a layer *before*
   looking. The L6 reversal is a real result and deserves an entry of its own.
2. **S3-02** — report `Q1b`/`Q1d` as domain-level tests over 113 with ties counted against, and state
   "42 of 113 domains produce any concept content" as the primary descriptive fact.
3. **S3-03** — retire the concentration ratio. The question it was built for is better answered by the
   3×3 column comparison the artifact already computes and entry 043 already reads correctly
   (0.0949 vs 0.0556/0.0607 on button; 0.0991 vs 0.0238/0.0431 on basket) — those are differences of
   projections, not ratios, and they have CIs.
4. **S3-04** — replace "replicates more strongly" with the dependent-r test (p = 0.618) and report the
   partial correlations; they are the interesting result, not a defect to bury.
5. **S3-05** — drop cell B from the replication table or label it "the same 1130 rows".
6. **S3-06** — sweep `vfull` out of `residual_axis_3x3` and `cell_coordinates_on_bomb_axis`, re-render F2.
7. **S3-07** — `bbox_to_anchor` the legends outside the axes as the scope cards were meant to be, and
   draw F8 as a scatter of its 113 domains.

---

*REVIEW-3 PART 4, written 2026-09-10 07:05 IDT. Nothing in the tree was modified; no job was
submitted. The `basket` K ladder was running throughout and is not reviewed.*
