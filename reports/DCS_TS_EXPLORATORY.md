# DCS thesis-scale — the two EXPLORATORY re-analyses: `PR-049` and `PR-052`

Generated 2026-09-07 · `scripts/dcs_ts_exploratory.py` · **CPU only. No GPU, no SLURM, no network,
no new forward passes** — both are re-analyses of the `ts116m` extraction the primary already
consumed.

Artifacts: `outputs/dcs_ts/pr049_exploratory_result.json`,
`outputs/dcs_ts/pr052_exploratory_result.json` (distinct paths, and the writer **refuses** to
overwrite a file carrying a different preregistration id — `C-093`).

---

## 0. THE RULE THIS DOCUMENT OBEYS, BEFORE ANY NUMBER

> **Neither result carries confirmatory weight. A null from either is `CANNOT ANSWER`, not evidence
> of absence. Neither enters Holm. Neither may be quoted as support for `CLAIM A`.**

That is not a caution added by the analyst; it is read out of the frozen configurations at runtime.
Both `configs/dcs_ts_pr049.json` and `configs/dcs_ts_pr052.json` carry the identical `multiplicity`
block, which lists

```
EXPLORATORY  members: ["DCS-PR-049: knife-vs-gun (demoted by C-101)",
                       "DCS-PR-052: arm-balanced surface cells"]
             correction: "none -- exploratory results carry no confirmatory weight
                          and are labelled as such"
```

and `check_exploratory_declared()` **refuses to run** unless the preregistration it was handed
places its own id in that family and in no confirmatory family. Point this analyzer at `PR-048` or
`PR-053` and it raises rather than producing a number. That is what makes the label load-bearing
instead of decorative: a config that later promoted itself out of `EXPLORATORY` would stop being
analysable by this file (selftest case: *"a config that promotes itself out of EXPLORATORY is
REFUSED"*).

`assert_no_verdict()` then scans the artifact for the strings a confirmatory analyzer emits
(`SUPPORTS THE CLAIM`, `NOT SIGNIFICANT`, …) and refuses to leave any of them in it. There is no
code path in this script that prints a verdict.

**Why each is exploratory, in its own words:**

| | why |
|---|---|
| `PR-049` | **DEMOTED by `C-101`.** Its conjunctive power is **0.793** at the Holm α the config itself declares — below the 0.80 bar. The config still carries the superseded 0.963/0.900; the artifact records both, with `C-101` naming the correction. The demotion fired by an arithmetic correction to the power, not by the `SD > 0.188` route the config anticipated. |
| `PR-052` | **Declared exploratory before it was run, not after it disappointed.** `Z2` measured conjunctive power in the stratum at **0.721** against an MDE of 0.1062–0.1186 for a +0.15 bar. `primary.success` and `primary.negative` both read `NOT AVAILABLE` in the frozen file. |

---

## 1. Population, identical for both contrasts

Bound from the raw `ts116m` bank JSONL on the **field** `cell == "C"` (not `condition` — `A-039`),
`query_kind == "semantic_one_word"`, `n_examples == 4`, concepts `{knife, gun}`, with all three
preregistered whole-population exclusions applied.

| quantity | value |
|---|---|
| rows | **4,520** = 113 domains × 2 codewords × 2 concepts × 10 family slots |
| domains analysed | **113** (`restaurant_kitchen` C-082, `subway_station` C-087, `school_campus` C-075/R-108 excluded; all three sit in TRAIN) |
| arms | knife 2,260 / gun 2,260 — exactly balanced |
| codewords | button 2,260 / basket 2,260 |
| split | **67 train / 23 validation / 23 test** domains → 2,680 / 920 / 920 rows |
| missing rows | `basket_gun` 30, `basket_knife` 30, **0 unexplained** — all `school_campus`, the `C-075` occurrence refusal, and that domain is a preregistered exclusion |
| bank shas | all four verified against the pin (`65eb4fa533890eff`, `c7ceb5a151a2788a`, `61e586e4bdca6f28`, `f1a8332bdd7c48ce`) |
| read site | `codeword_last`, attn `eager`, `knockout_applied=False`, layers 6–14 |

Selection ran on **VALIDATION only** in both contrasts; `SELECTION-NOTEST` asserts that not one
test domain entered the selection set, and the mutation `select_on_test` turns it RED.

---

## 2. `PR-049` — knife vs gun, unstratified. **EXPLORATORY**

Probe: multinomial logistic regression on the codeword hidden state, standardiser and classifier
fit on the 67 train domains, `(layer, C)` chosen on the 23 validation domains over the frozen
9 × 4 grid, TEST read once.

| | |
|---|---|
| **estimate, domain-mean accuracy on 23 untouched test domains** | **0.9446** |
| 95 % t-interval over domains | **[0.9267, 0.9624]** |
| 95 % bootstrap (10,000 resamples **of domains**) | [0.9283, 0.9609] |
| between-domain SD | 0.0413 |
| per-domain range | 0.875 → 1.000; 5 of 23 domains at 1.000; **23/23 above chance**, 0 exact ties |
| `SELECTION_TRACE` | layer **9**, C **0.01**, best val 0.9109, `n_tied=1/36`, **`inert=False`, `saturated=False`** — not the `C-070` degenerate surface |
| sign test | k = 23/23, p = 2.38419e-07 **[floor 2.384e-07 — this p IS its own floor and is not a measurement]** |
| domain-level group permutation, 10,000 draws | **p < 9.999e-05 (FLOOR, 0 exceedances)**; null mean 0.4994, sd 0.0740, centred on chance |
| **preregistered nuisance floor** | **0.7065** (`R-106` Y3, register-only 17-feature surface classifier on this contrast) |
| **floor RE-DERIVED on this run's test rows** | **0.7065**, CI [0.6759, 0.7358], domain-mean 0.7065, 920 rows / 23 domains |
| estimate − floor | **+0.2381** |

**The floor reproduces to four decimals.** The 17-feature surface classifier was re-fit on TRAIN
and re-scored on the 920 test rows of this run and returned 0.7065217…, byte-for-byte `R-106` Y3's
number. That is a replication of the bar, not a coincidence: `fit_surface()` here and
`fit_eval_2way()` there are the same estimator on the same rows. It also settles a wording question
— `R-106` Y3's 0.7065 was measured **train→test**, so quoting it as the bar for a test-set estimate
is like-for-like.

**How to read it.** Concept identity between two matched harmful concepts is decodable from the
codeword hidden state at 0.9446, 23/23 held-out domains, and that is **0.2381 above what a bag of
17 surface counts achieves on the same rows**. Both p-values sit **at their arithmetic floors** and
are reported as floors, not as measurements — the design cannot resolve below 2.384e-07 (sign) or
9.999e-05 (permutation), and `C-069` exists because this project once published a floor as a
finding.

**What it does not establish.** Power 0.793 < 0.80 at its own Holm α, so a *null* here would have
been uninterpretable. This estimate is not a null, but the demotion still stands: the design was
not adequately powered to be confirmatory, and a positive from an underpowered design does not
retroactively become confirmatory. It enters no family and corrects no p-value.

---

## 3. `PR-052` — knife vs gun inside arm-balanced surface cells. **EXPLORATORY**

### 3.1 How the cells are built

Reproduced from `scripts/dcs_ts_pr050_pr051_blockers.py` — the `simplex_t3` construction `C-100`
identified as the *one* stratification that reaches chance, chosen on VALIDATION before the test
split existed:

1. the 17-feature surface classifier is fit on the **TRAIN** demonstration blocks;
2. its predicted-probability **vector** is computed on the split being analysed, and each
   coordinate is coarsened into 3 equal-frequency tiers; the cross-product cells are taken.
   **No label enters this step** — `simplex_cells()` takes no `y` argument, which is what makes the
   cells constructible on TEST without reading a test label (`PR-052`'s own `void` clause);
3. every **(domain × cell)** is subsampled to its smallest arm, so the concepts are equally
   frequent inside every cell **by construction** rather than by assumption (`C-100`: conditioning
   on a score does *not* balance the arms, and binning alone cannot change pooled accuracy);
4. a cell that cannot be balanced is **dropped and counted**.

| | validation | test |
|---|---|---|
| cells realised | 5 | 5 |
| domain × cell units | 68 | 71 |
| dropped (unbalanceable) | 16 | 16 |
| rows retained | **552 / 920 (60.0 %)** | **524 / 920 (57.0 %)** |
| arm counts | gun 276 / knife 276 | gun 262 / knife 262 |
| domains retained | 23 / 23 | **23 / 23** |

The validation reproduction lands at **552 rows over 23 domains — exactly `Z1`'s figure.**

### 3.2 THE FINDING THAT MATTERS: the preregistered floor does not replicate on TEST

`PR-052` preregisters the floor **0.5054, CI [0.4629, 0.5479]**, and preregisters the *rule* that
the floor is *"the measured surface accuracy in the SAME cells, verified per run, never the nominal
chance level"*. The rule was obeyed, and it fired:

| surface classifier, arm-balanced `simplex_t3` cells | accuracy | 95 % CI | covers 0.5? |
|---|---|---|---|
| `Z1`, validation, 114-domain population | 0.5054 | [0.4629, 0.5479] | yes |
| **this run, validation, 113-domain population** | **0.5199** | [0.4773, 0.5623] | **yes** |
| **this run, TEST, 113-domain population** | **0.5573** | **[0.5135, 0.6003]** | **NO** |

`SURFACE-FLOOR-VERIFIED` is the **one FAILED check across both contrasts**, and it failed for the
right reason. Two things follow, and they must travel together:

1. **The validation figure replicates.** 0.5199 against `Z1`'s 0.5054, same construction, same
   552 rows, same 23 domains; the small gap is explained by the TRAIN set differing by one domain
   (`school_campus` was still in `Z1`'s 114-domain population and is now a preregistered
   exclusion). The construction is reproducible.
2. **The at-chance property does not transfer to the test split.** On the 524 test rows the surface
   classifier reaches 0.5573 with a CI that **excludes 0.5**. `PR-052`'s premise — *"a point
   estimate of concept decodability where surface information is verifiably absent"* — therefore
   **does not hold on the rows the estimate is computed over.** Surface information is *reduced*
   there (0.5573 against 0.7065 on the unstratified test rows) but it is **not verifiably absent**.

**Consequence for how the number is read: the bar for this contrast is the run-verified 0.5573, not
the frozen 0.5054.** `one_line()` prints both, with the re-derived figure marked as the bar. This is
the `B-020` failure mode caught by the one mechanism that can catch it — a floor that is
re-measured on the rows actually analysed rather than quoted from the split where it was chosen.

### 3.3 The estimate

| | |
|---|---|
| **estimate, domain-mean accuracy inside the cells, 23 test domains** | **0.9294** |
| 95 % t-interval over domains | **[0.9058, 0.9530]** |
| 95 % bootstrap over domains | [0.9073, 0.9519] |
| between-domain SD | 0.0546 |
| per-domain range | 0.844 → 1.000; 6 of 23 at 1.000; **23/23 above chance**, 0 exact ties |
| rows analysed | 524 of 920 (57.0 %), arms exactly 262 / 262, all 23 domains present |
| `SELECTION_TRACE` | layer **9**, C **0.01**, best val 0.9038, `n_tied=1/36`, `inert=False`, `saturated=False` |
| sign test | k = 23/23, p = 2.38419e-07 **[floor 2.384e-07 — AT THE FLOOR]** |
| domain-level group permutation, 10,000 draws | **p < 9.999e-05 (FLOOR, 0 exceedances)**; null mean 0.4997, sd 0.0735 |
| preregistered floor | 0.5054 → estimate − floor = +0.4240 |
| **run-verified floor (the bar)** | **0.5573** → **estimate − floor = +0.3721** |

**How to read it.** Restricting to cells where the surface classifier is *much weaker* costs the
probe very little: 0.9294 inside the cells against 0.9446 on all test rows, a drop of 0.0152, while
the surface classifier drops 0.1492 (0.7065 → 0.5573) over the same restriction. That contrast is
the informative part of this analysis, and it is a **descriptive** contrast between two accuracies
measured on overlapping-but-different row sets — not a test, and not corrected for anything.

**What it does not establish.** Power in this stratum is 0.721. `primary.success` and
`primary.negative` are `NOT AVAILABLE` by design. And the stratum is **not** the surface-free
stratum it was preregistered to be (§3.2), so even the descriptive reading above must say *reduced
surface information*, never *absent*.

---

## 4. Guards, and the mutation harness

Every check binds a **counted** set; `Checks.add()` records a check that bound zero rows as a
**FAIL**, never a PASS. Analyzer selftest: **24/24 guards reachable, no data required.**

| contrast | checks | mutations |
|---|---|---|
| `PR-049` | **17/17 PASS** | **11/11 RED** |
| `PR-052` | **19/20 PASS** (the one FAIL is `SURFACE-FLOOR-VERIFIED`, §3.2) | **12/12 RED** |

Each mutation names the **specific** check it must break (`C-095`: a harness whose mutations all
return GREEN is itself unfalsifiable):

| mutation | check it turns RED | what it demonstrates |
|---|---|---|
| `empty_population` | `POP-BIND` | a filter binding nothing raises, never returns a statistic (`C-074`) |
| `keep_excluded_domains` | `EXCLUSIONS-APPLIED` | the three whole-population exclusions are actually applied |
| `corrupt_split` | `SPLIT-DISJOINT` | a domain the manifest does not place falls out of every mask uncounted |
| `wrong_bank_sha` | `RUN-BINDING` | a run extracted from unpinned rows is VOID, not a result |
| `forge_missing` | `MISSING-ROWS` | an **unexplained** missing row refuses; explained ones (the 60 `school_campus` rows) do not |
| `empty_test` | `BIND-TEST` | a split binding zero rows raises |
| `select_on_test` | `SELECTION-NOTEST` | selection reading test (measured FPR 0.4433 vs 0.0467) |
| `inert_grid` | `SELECTION-NOT-INERT` | a saturated surface is a grid-order tie-break, not localisation (`C-070`) |
| `row_level_perm` | `PERM-DOMAIN-LEVEL` | row-level permutation breaks per-domain class marginals (measured FPR 0.2000) |
| `null_true_labels` | `PERM-CENTRED` | a null that is not centred on chance is not a null |
| `drop_floor` | `FLOOR-DECLARED` | a preregistration with no nuisance floor cannot be analysed at all (`B-020`) |
| `unbalanced_subsample` *(PR-052)* | `ARM-BALANCE` | the arms really are equal by construction, not by assumption |

The mutation runs use a reduced grid and `n_perm = 30`; they exercise **guards**, not the null. The
reported statistics use the preregistered `n_perm = 10000` with no override.

---

## 5. Corrections and discrepancies recorded by this run

1. **`PR-052`'s floor does not replicate on TEST** — 0.5573 CI [0.5135, 0.6003] against the frozen
   0.5054. §3.2. The bar for the estimate is the run-verified figure.
2. **"552 rows, all 23 *test* domains" is a mis-transcription** that appears in both
   `configs/dcs_ts_pr052.json` (`_why_exploratory_from_the_outset`) and the plan log's `PR-052`
   entry. `Z1` never read a test label — `reports/DCS_TS_PR050_PR051_BLOCKERS.md` says *"552 rows
   … over all 23 **validation** domains"*, and the script that produced it raises on any test row.
   The 0.5054 floor is a **validation** measurement. Corrected here; the frozen configs are not
   edited.
3. **`PR-049`'s power block in the frozen config is superseded.** It still reads 0.963 / 0.900;
   `C-101` corrected it to 0.905 / 0.793 after the freeze. The artifact carries the frozen block
   under `as_frozen_in_the_config` and the correction under `superseded_by`, so neither silently
   replaces the other.
4. **`Z1`'s population was 114 domains, this run's is 113.** `school_campus` became a
   whole-population exclusion (`R-108`) after `Z1` ran. It sits in TRAIN, so validation and test
   are unaffected in size; the surface classifier's train set differs by 40 rows, which is the
   likely source of the 0.5054 → 0.5199 validation gap.
5. **A first mutation-harness configuration put `C = 10` in the reduced grid** and a single
   mutation ran over twenty minutes at 4096 features — a guard demonstration turning into a
   scheduling problem. Fixed to the two smallest `C` values, which is the right end of the grid for
   exercising guards. Recorded because the run was killed and restarted, not silently retried.

---

## 6. What may and may not be said

**May be said, with the label attached:**

- *"In an exploratory re-analysis of the same held-out 23 test domains, concept identity between
  two matched harmful concepts (knife vs gun) is decodable from the codeword hidden state at
  0.9446 (95 % CI [0.9267, 0.9624]), 23/23 domains, against a re-derived surface floor of 0.7065
  measured on the same rows. This is exploratory and carries no confirmatory weight."*
- *"Restricting to arm-balanced surface cells, where the surface classifier falls from 0.7065 to
  0.5573, the probe falls only from 0.9446 to 0.9294. Exploratory, and the cells are not
  surface-free on the test split."*

**Must not be said:**

- ❌ *"PR-049 confirms CLAIM A"* — it is not in the confirmatory family and is underpowered at its
  own α.
- ❌ *"the probe beats the surface baseline, p < 0.0001"* — both p-values are **at their design
  floors**; the design cannot resolve below them.
- ❌ *"surface information is absent in the PR-052 cells"* — measured 0.5573, CI excluding 0.5.
- ❌ *"knife-vs-gun answers the register confound"* — it does not. `C-101` and the structural
  conclusion behind `PR-050`'s withdrawal stand: **register is CANNOT ANSWER on this corpus**, and
  the fix is a register-matched regeneration, not a re-analysis. Nothing here changes that.
- ❌ any statement that these numbers alter Holm, `PR-048`, `PR-053` or `PR-051`. They do not enter
  the correction; the `EXPLORATORY` family's declared correction is `none`.

---

## 7. The two lines

> **`DCS-PR-049` knife-vs-gun, unstratified: estimate 0.9446, 95 % t-interval [0.9267, 0.9624],
> bootstrap [0.9283, 0.9609], measured nuisance floor 0.7065 (re-derived on the same test rows) —
> EXPLORATORY.**

> **`DCS-PR-052` knife-vs-gun inside arm-balanced surface cells: estimate 0.9294, 95 % t-interval
> [0.9058, 0.9530], bootstrap [0.9073, 0.9519], preregistered nuisance floor 0.5054 but
> **re-derived on the analysed test rows as 0.5573, CI [0.5135, 0.6003] — that is the bar, and it
> excludes chance** — EXPLORATORY.**

A null from either would have been **CANNOT ANSWER**, not evidence of absence. Neither is a null;
neither is confirmatory either.
