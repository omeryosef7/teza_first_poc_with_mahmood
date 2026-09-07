# DCS PR-050 / PR-051 — the blocking pre-analysis items W3, Z1, Z2

Generated 2026-09-07 · `scripts/dcs_ts_pr050_pr051_blockers.py` · **CPU only, no model weights, no
GPU, no SLURM, no network.** The Llama-3.1-8B-Instruct **tokenizer** is loaded from the local HF
cache with `HF_HUB_OFFLINE=1` to tokenize prompt text; nothing else about the model is touched.

Three items are cleared here, all of them marked `blocking: true, done: false` in their frozen
configs:

| item | config | question |
|---|---|---|
| **W3** | `configs/dcs_ts_pr051.json` | is `--position last` (`rel_end = -1`) a usable control site, and what token is it? |
| **Z1** | `configs/dcs_ts_pr050.json` | can any stratification drive the surface classifier to chance with usable n? |
| **Z2** | `configs/dcs_ts_pr050.json` | is a within-stratum estimator adequately powered at n=23 test domains? |

## The test-set rule, and how it is enforced

**No test label is read and no test-set outcome is computed anywhere in this document.** The
PR-048 primary has not been run. Z1 fits on the **68 TRAIN domains** and evaluates on the
**23 VALIDATION domains**; Z2 is arithmetic on the stratum sizes Z1 produces. A hard guard,
`GUARD-TEST`, is evaluated on every row set that reaches a fit or an evaluation and **raises**
rather than warns; the mutation `read_test` puts test rows in front of it and the run REFUSES
before a single feature is computed, so no test-set number exists even inside the mutation run.

W3 is **prompt-only**: it reads prompt TEXT across the whole 6840-row population, test prompts
included. Reading a prompt is not reading a label or an outcome, and the distinction is stated
here rather than assumed.

## Population, re-derived from the raw banks

Bound from the six raw `ts116m` bank JSONL files, on the FIELD `cell == "C"` (not `condition` —
A-039), `query_kind == "semantic_one_word"`, `n_examples == 4`, with both whole-population
preregistered exclusions applied (`restaurant_kitchen` C-082, `subway_station` C-087):

| quantity | value |
|---|---|
| rows | **6840** = 114 domains × 2 codewords × 3 concepts × 10 family slots |
| domains analysed | **114** (both excluded domains sit in TRAIN; 120 rows dropped) |
| arms | bomb 2280 / knife 2280 / gun 2280 |
| split (`dsplit`) | **68 train / 23 validation / 23 test** |
| rows by split | 4080 train / 1380 validation / 1380 test |

`POP-01` and `POP-02` PASS. Both preregistrations load through `scripts/dcs_ts_prereg.py`, which
verifies FROZEN status and every pinned `*_sha16` against the file on disk (`PRE-frozen` PASS).

The 17 surface features, the population loader, the split loader and the check ledger are
**imported from `scripts/dcs_ts_pr049_blockers.py`**, and the power estimators from
`scripts/dcs_ts_power.py`. No feature is invented here. A difference between these numbers and
PR-049's is therefore a difference of design, not of arithmetic.

---

# W3 — the control site `--position last`

## What was actually verified, and against what

`reports/DCS_TS116M_TOKEN_ROLE_MAP.md` verified `rel_end = -9` (PR-048 checklist X2) and listed
`rel_end = -1` only as rank 9 of a candidate table. It was computed on **115 domains / 6900
prompts**, before C-087 excluded `subway_station`. Everything below is **re-derived on the
114-domain / 6840-prompt population from a real tokenization**, by reproducing the extractor's own
path line for line —

```
templated = dc.apply_template(tok, row["full_prompt"], enable_thinking=None)
ids       = tok(templated, add_special_tokens=False)["input_ids"]
pos       = len(ids) - 1            # src/boombness/extract_boombness.py, --position last
```

— so the site verified is the site that would be extracted, not a site inferred from a table.
(`W3-tok` PASS, 6840 prompts.)

## The four criteria, with denominators

| criterion | count | denominator | verdict |
|---|---|---|---|
| **(a)** token-identical across the three concepts at matched `(codeword, prompt_id)` | **2280** | 2280 complete triples | PASS |
| **(b)** strictly after every codeword occurrence | **6840** | 6840 prompts | PASS |
| **(c)** decoding contains no `bomb` / `knif*` / `knive*` / `gun` | **6840** | 6840 prompts, **1** distinct decoding | PASS |
| **(d)** exists in every matched prompt; every key carries all three arms | **6840** present / **2280** complete triples | 6840 prompts / 2280 keys | PASS |

Criterion (b) is re-derived by locating **every** codeword occurrence in the templated text with
the offset-based finder (left-strict, right-permissive), not by trusting the bank's
`n_codeword_occurrences` — the field the token-role map showed disagrees with two other counters
on 11/6900 rows.

The site is a **constant 9 tokens downstream** of the preregistered primary site: the last codeword
occurrence sits at `rel_end = -10` in **6840/6840** prompts, and the control at `rel_end = -1`, so
the paired contrast is between two fixed offsets, not two moving ones (`W3-gap` PASS). Prompt
length is 230.06 tokens on average (min 192, max 279), which is why an end-relative address is the
only safe one.

## What the token actually is — and it is pure scaffold

**The final prompt position decodes to `'\n\n'`, token id 271, in 6840 of 6840 prompts — one
distinct decoding across the entire population.**

Differencing the chat template with and without `add_generation_prompt` (measured, not
pattern-matched) shows the generation prompt appends exactly

```
'<|start_header_id|>assistant<|end_header_id|>\n\n'   = 4 tokens
```

and `rel_end = -1` is the **last token of that 4-token generation header**, in 6840/6840 prompts
(`W3-scaffold` PASS). The tail of every prompt is:

| rel_end | token id | decoded | role |
|---|---|---|---|
| −6 | 30 | `'?'` | end of the query (content) |
| −5 | 128009 | `'<\|eot_id\|>'` | chat scaffold |
| −4 | 128006 | `'<\|start_header_id\|>'` | generation header |
| −3 | 78191 | `'assistant'` | generation header |
| −2 | 128007 | `'<\|end_header_id\|>'` | generation header |
| **−1** | **271** | **`'\n\n'`** | **generation header — the control site** |

**Said plainly, because PR-051's interpretation depends on it: `--position last` is a GENERATION
HEADER TOKEN. It carries no query content whatsoever.** It is the position the model is about to
generate from, five rungs past the last content token (`'?'` at `rel_end = -6`) and nine past the
codeword.

This is not a defect in the extraction — it is the correct final prompt position — but it changes
what a null there means. PR-051's `_interpretation_fixed_before_the_numbers_exist` reads
`codeword ≈ control` as evidence for **gist**. That reading is only available if the control site
is capable of carrying the gist. A `'\n\n'` inside the assistant header is exactly the position a
decoder-only model uses to aggregate the whole prompt before generating — so it plausibly carries
gist *maximally* — but it is also the position most exposed to the "readout" failure mode the
token-role map already flagged for ranks 5–9: **a null there is a null about the readout, not
about the query.** Concretely:

* `codeword >> control` — under-determined. It is consistent with binding, and equally consistent
  with a content position beating a scaffold position for reasons that have nothing to do with the
  codeword. There is no content-position control in the design to separate these.
* `codeword ≈ control` — the strongest reading PR-051 can support, and it does support GIST:
  identity decodable at a token that shares no content with the query means the identity is not
  localised at the codeword.
* `control >> codeword` — as PR-051 says, the framing is wrong.

**The design gap this exposes: `rel_end = -9` (`' actually'`, id 3604) is a CONTENT position that
passes all four criteria on this population, and the token-role map already nominated it.** Running
the control at `-9` as well as `-1` would cost the same extraction and would separate "the codeword
is special" from "content positions beat scaffold positions". That is a recommendation, recorded
before any hidden state at either control site exists; it is not a change to a frozen file.

## W3's sibling item W1 is NOT satisfiable today, and that is a separate fact

PR-051 `pre_extraction_checklist` W1 requires the control extraction to complete. On disk right
now there is **no `ts116m` run at `--position last` at all**: every `ts116m_*` run under
`outputs/boombness/extract_boombness/` records `"position": "codeword_last"` (four with `DONE.json`
— `button_bomb`, `button_knife`, `button_gun`, `basket_bomb`; `basket_knife` running; `basket_gun`
not started). The two `lastpos_*` runs on disk are from 2026-08-17 and are a different bank family.
Job **860778** is `PENDING (Priority)` in `killable`, submitted 06:22:20, with `StartTime=12:59:03`
— about six and a half hours out.

W3 does not depend on that job and is answered without it. W1 is not, and is still open.

Also recorded, because it is an inconsistency inside a frozen file rather than a measurement:
PR-051 `artifacts.extraction` says *"shared with PR-048 — the SAME rows, no additional forward
passes"*, while `design.sites.control_site` requires an entire second extraction family at
`--position last`. Both cannot be true.

---

# Z1 — can the stratification even work?

## What was fit, on what, and evaluated where

The **17-feature register/surface classifier of R-106 / PR-049 Y3**, imported unchanged from
`scripts/dcs_ts_pr049_blockers.py::register_features` and read off the **demonstration block**
exactly as PR-049 read it: total hedge count (the five narrow families `resembl*`, `simulat*`,
`drill`, `false alarm`, `looks like`), mean sentence length, sentence count, word count,
type-token ratio, mean word length, counts of `, . ; : - ' " ( ?`, digit count, uppercase count.

* fit on the **68 TRAIN domains** (4080 rows), standardiser fit on TRAIN only;
* scored on the **23 VALIDATION domains** (1380 rows); TRAIN/VALIDATION domain disjointness is
  asserted and the assertion is itself mutated;
* `Z1-leak` re-derives N3 on the fitted text: **0/5460** rows name a concept in whole-word form in
  their demonstration block, so the classifier is not reading the label off the page.

**Unstratified baselines on VALIDATION** (these are the thing a stratification would have to
destroy):

| contrast | chance | accuracy | 95% CI | balanced | domain-mean | between-domain SD | rows / domains |
|---|---|---|---|---|---|---|---|
| 3-way | 0.3333 | **0.5913** | [0.5648, 0.6174] | 0.5913 | 0.5913 | 0.1069 | 1380 / 23 |
| knife-vs-gun | 0.5 | **0.6630** | [0.6315, 0.6936] | 0.6630 | 0.6630 | 0.1263 | 920 / 23 |

The knife-vs-gun figure, 0.6630 on VALIDATION, sits close to PR-049 Y3's **0.7065 on TEST** — the
register confound replicates on a different 23 domains, which is worth knowing before the
confirmatory run and costs no test read.

## The stratifications tried, declared in source before any probability existed

Seventeen candidate stratifications in four families, all reading only the classifier's
predicted-probability vector:

1. equal-frequency bins on **max predicted probability**, Q ∈ {2, 3, 4, 5, 10};
2. equal-frequency bins on the **predicted-class margin** (p₁ − p₂), Q ∈ {2, 3, 4, 5, 10};
3. a single **lower tail** of the margin: bottom 10 %, 25 %, 50 %;
4. **propensity-style** bins on the predicted probability of one fixed reference class (Q ∈ {3, 5},
   one stratification per reference class) and **joint simplex cells** — every coordinate of the
   probability vector coarsened into t tiers and crossed, t ∈ {2, 3}. Family 4 is the strongest
   reading of "stratify by the predicted-probability vector": the whole vector, not a scalar
   summary of it.

**100 strata scored for the 3-way, 74 for knife-vs-gun.** Every stratification is checked to
partition the validation rows exactly once (`Z1-part-*`, all PASS), and a stratum that binds zero
rows raises rather than passing.

Two thresholds, both fixed in source before the numbers existed:

* **AT CHANCE (EQUIV):** |acc − chance| ≤ 0.03 **and** the 95 % Clopper–Pearson upper bound ≤
  chance + 0.05. The weaker tier, **CI-COVERS** (the CI merely contains chance), is reported too,
  but it is satisfied by any stratum small enough to be unmeasurable, which is not what the kill
  condition is asking.
* **USABLE n:** all 23 held-out domains represented, ≥ 4 rows per domain, ≥ 230 rows. A stratum
  whose per-domain unit is broken cannot feed a domain-mean estimator whatever its row count.

## Result on the 3-way (chance 1/3): NO

| | value |
|---|---|
| strata scored | **100** |
| strata with usable n | **34** |
| usable strata at chance (EQUIV) | **0** |
| usable strata at chance (CI-COVERS) | **0** |
| closest stratum of all | `maxprob_q10` bin 1/10 — **acc 0.3333**, CI [0.2554, 0.4186], **138 rows / 21 domains — NOT usable** |
| closest **usable** stratum | `pref_q3` p(bomb) bin 2/3 — **acc 0.4609**, CI [0.4146, 0.5076], 460 rows / 23 domains |

The bottom decile of predicted confidence lands exactly on chance — and its within-stratum refit
lands there too (0.3333) — but it holds 10 % of the population, is missing 2 of 23 domains, and
has a median of 6 rows per domain. Every stratification with enough rows to support a domain-mean
estimator leaves the surface classifier **+0.13 or more above chance**.

## Result on knife-vs-gun (chance 0.5): NO for probability bins, YES for arm-balanced cells

| | value |
|---|---|
| strata scored | **74** |
| strata with usable n | **10** |
| usable strata at chance (EQUIV) | **0** |
| usable strata at chance (CI-COVERS) | **0** |
| closest stratum of all | `maxprob_q5` bin 1/5 — acc 0.4783, CI [0.4042, 0.5530], **184 rows / 22 domains — NOT usable** |
| closest **usable** stratum | `maxprob_q2` bin 1/2 — **acc 0.5826**, CI [0.5360, 0.6281], 460 rows / 23 domains |

For a two-class contrast the max-probability and margin families are the **same** stratification
(margin = 2·maxprob − 1 is monotone), and the tables confirm it bin for bin. That halves the
apparent diversity of PR-050's step 2 and is worth recording.

## Why binning alone cannot work — a defect in PR-050's own premise

`primary.nuisance_floor.source` in `configs/dcs_ts_pr050.json` states:

> *"within a surface-matched stratum the surface classifier is at chance BY CONSTRUCTION — that is
> the point of the stratification, and it is verified rather than assumed"*

**On this corpus that sentence is false, and the measurement shows exactly why.** Two facts:

1. **A partition cannot change pooled accuracy.** Pooled over its strata, every one of the
   ten partitioning stratifications returns the identical accuracy: **0.5913** (3-way) and
   **0.6630** (knife-vs-gun). Binning redistributes where the classifier is right; it removes
   nothing. What does fall is the advantage over the **within-stratum majority class** — from
   +0.1928 (`maxprob_q2`) to **+0.0000** (`simplex_t3`, 3-way) and from +0.1587 to **+0.0000**
   (knife-vs-gun). That limit is arithmetic, not evidence: conditioned on the predicted-probability
   vector the classifier IS the vector's argmax, so of course it adds nothing beyond it.
2. **Conditioning on the score does not balance the arms.** Under `simplex_t3` the pooled
   within-stratum majority rate is **0.5913** (3-way) and **0.6630** (knife-vs-gun) — the concepts
   are heavily unequal inside cells. A probe evaluated in those cells can score far above 1/3 or
   0.5 by reading the cell's class prior, with no representation involved. "At chance by
   construction" holds only if the arms are equally frequent inside the stratum, and bins on a
   predicted score do not make them so.

**Stratification also does not remove surface information, only surface confidence.** Refitting
the same 17 features *inside* the most favourable stratum (the lowest-confidence half,
domain-grouped 5-fold CV over the 23 validation domains):

| contrast | stratum | frozen classifier | **refit within the stratum** | chance |
|---|---|---|---|---|
| 3-way | `maxprob_q2` bin 1/2, 690 rows / 23 domains | 0.4957 | **0.4986** | 0.3333 |
| knife-vs-gun | `maxprob_q2` bin 1/2, 460 rows / 23 domains | 0.5826 | **0.5609** | 0.5 |

`Z1-refit-*` FAIL on both. The low-confidence stratum is not surface-matched; it is merely a
selection of rows this particular fit was unsure about.

## The repair, measured: ARM-BALANCED strata

The honest fix is design option **(a)** of `DCS_TS_REVIEW2_SCIENCE.md` §B.2.3 — subsample so the
arms are equally frequent — applied *inside* every stratum and *within* every domain. Every
(domain × stratum) cell is subsampled to its smallest arm; cells that cannot be balanced are
dropped and counted. The arms are then equal by construction, verified rather than asserted
(`Z1-armbalance-*` PASS: bomb 306 / knife 306 / gun 306 at `maxprob_q2`, knife 400 / gun 400).

| contrast | best arm-balanced stratification | accuracy | 95 % CI | rows (% of population) | domains | refit within | at chance? |
|---|---|---|---|---|---|---|---|
| 3-way | `simplex_t3` | **0.3485** | [0.2677, 0.4363] | 132 (9.6 %) | **13** | 0.3258 | no — CI too wide, and 10 of 23 domains missing |
| knife-vs-gun | `simplex_t3` | **0.5054** | [0.4629, 0.5479] | **552 (60.0 %)** | **23** | **0.5109** | **YES** |

**One construction works, and only for knife-vs-gun: arm-balanced joint simplex cells.** The
surface classifier is driven to **0.5054** on 552 rows over all 23 validation domains, with knife
276 / gun 276, and a classifier *refit inside those rows* reaches only **0.5109** — so the surface
information is genuinely gone, not merely unavailable to the frozen fit. 1 of 17 stratifications
achieves this; 16 do not. For the 3-way, **0 of 17**.

This construction is **not** what PR-050 step 2 preregisters. Step 2 says *"stratify TEST rows by
the surface classifier's predicted-probability vector, into preregistered bins"* — binning, with
no rebalancing. On this corpus binning alone does not reach chance at any usable n, for either
contrast. Reaching chance requires adding the within-cell arm-balancing that PR-050 does not
specify, which is a **change to the frozen design**, not a result of it.

---

# Z2 — power within strata

## The estimator, and why neither PR-048's nor PR-049's power transfers

The primary is a **domain-mean accuracy over 23 TEST domains**. A per-domain accuracy measured on
`m` rows is the domain's true accuracy plus binomial noise, so what the estimator actually sees is

```
sd_observed(m) = sqrt( sd_between² + p(1−p)/m )
```

and it **grows as the strata shrink**. PR-048's power block assumes the full `m = 60` rows per
domain (3-way); PR-049's assumes the full `m = 40` (knife-vs-gun). A stratum holding a quarter of
the rows has `m = 15` or `m = 10`, and the SD term is no longer negligible.

**Is `sd_between = 0.1406` a variance component or an already-observed SD?** It matters — if it
were already observed at `m = 60`, adding `p(1−p)/m` would double count. PR-048's own power block
settles it, and the check re-derives rather than assumes (`Z2-icc` PASS):

| derived from `icc = 0.0884` | value | PR-048 publishes |
|---|---|---|
| `sqrt(icc · p(1−p))`, p = 1/3 | **0.1402** | 0.1406 |
| `deff = 1 + (m−1)·icc` at m = 60 | **6.2156** | 6.22 |
| `n_eff = 23·60 / deff` | **222.02** | 222 |

All three reproduce, so **0.1406 is the between-domain COMPONENT** and the inflation below is a
correction, not a double count. `m = 60` (3-way) and `m = 40` (knife-vs-gun) are themselves
re-derived from the raw rows rather than taken from the power block (`Z2-m` PASS).

Planning bar: **δ = +0.15**, PR-049 Y1's bar reused unchanged. Success rule: PR-048/PR-049's
**conjunctive** rule (domain-level permutation AND two-sided sign test); `min()` of the two arms is
reported, which is the *generous* upper bound on the conjunction, so an "underpowered" call cannot
be an artefact of the bound. Holm alpha = 0.025, from PR-050's own two-member primary family.
The MDE carries the type-II term, checked (`Z2-mde` PASS: 0.0937 with it, 0.0663 without).

## The power table

| stratum | m rows/domain | sd_observed | MDE (α=.05) | MDE (Holm) | conj power (α=.05) | conj power (Holm) | verdict |
|---|---|---|---|---|---|---|---|
| **3-way, FULL population** | 60 | 0.1532 | 0.0937 | 0.1045 | 0.931 | 0.838 | POWERED |
| 3-way, closest usable stratum `pref_q3` p(bomb) 2/3 | 20 | 0.1757 | 0.1074 | 0.1199 | 0.850 | **0.709** | UNDERPOWERED |
| 3-way, arm-balanced `simplex_t3` (13 domains only) | 6 | 0.2383 | 0.1457 | 0.1626 | 0.592 | **0.405** | UNDERPOWERED |
| 3-way, ½ of the population | 30 | 0.1649 | 0.1008 | 0.1125 | 0.892 | **0.772** | UNDERPOWERED |
| 3-way, ⅓ | 20 | 0.1757 | 0.1074 | 0.1199 | 0.850 | 0.709 | UNDERPOWERED |
| 3-way, ¼ | 15 | 0.1860 | 0.1137 | 0.1269 | 0.808 | 0.651 | UNDERPOWERED |
| 3-way, ⅕ | 12 | 0.1957 | 0.1196 | 0.1335 | 0.766 | 0.597 | UNDERPOWERED |
| 3-way, 1/10 | 6 | 0.2383 | 0.1457 | 0.1626 | 0.592 | 0.405 | UNDERPOWERED |
| 3-way, FULL @ SD ceiling 0.3439 | 60 | 0.3492 | 0.2135 | 0.2383 | 0.309 | 0.168 | UNDERPOWERED |
| **knife-vs-gun, FULL population** | 40 | 0.1613 | 0.0986 | 0.1101 | 0.905 | **0.793** | UNDERPOWERED |
| **knife-vs-gun, the ONE at-chance stratum** (arm-balanced `simplex_t3`, 552 rows / 23 domains) | **24** | **0.1737** | **0.1062** | **0.1186** | **0.858** | **0.721** | **UNDERPOWERED** |
| knife-vs-gun, closest usable bin `maxprob_q2` 1/2 | 20 | 0.1796 | 0.1098 | 0.1226 | 0.834 | 0.687 | UNDERPOWERED |
| knife-vs-gun, ⅓ | 13 | 0.1975 | 0.1207 | 0.1348 | 0.759 | 0.588 | UNDERPOWERED |
| knife-vs-gun, ¼ | 10 | 0.2116 | 0.1293 | 0.1444 | 0.698 | 0.517 | UNDERPOWERED |
| knife-vs-gun, ⅕ | 8 | 0.2259 | 0.1381 | 0.1541 | 0.640 | 0.454 | UNDERPOWERED |
| knife-vs-gun, 1/10 | 4 | 0.2868 | 0.1753 | 0.1957 | 0.438 | 0.267 | UNDERPOWERED |
| knife-vs-gun, FULL @ SD ceiling | 40 | 0.3529 | 0.2157 | 0.2408 | 0.303 | 0.164 | UNDERPOWERED |

The **binding arm is the sign test in every row** — it needs k ≥ 17 of 23 domains above chance —
exactly as PR-049 Y1 recorded. The permutation/t arm stays above 0.94 down to m = 12.

## What the table says

1. **The one stratification that reaches chance is not adequately powered.** Arm-balanced
   `simplex_t3` on knife-vs-gun retains 60 % of the rows and all 23 domains — `m = 24` instead of
   40 — which lifts the observed SD from 0.1613 to 0.1737 and drops conjunctive power to
   **0.858 at α = 0.05 and 0.721 under the Holm alpha PR-050 itself declares**. The MDE, 0.1062
   (Holm 0.1186), does clear the +0.15 bar; it is the sign arm that fails. So the honest reading is
   *marginal*: adequately powered if this contrast were run alone at α = 0.05, **not** adequately
   powered inside the two-member primary family it is preregistered in.

2. **A caution that is not about stratification at all.** PR-049's published conjunctive power for
   knife-vs-gun is 0.963 / 0.900, computed by putting `sd = 0.1406` straight into the estimator.
   `0.1406` is a between-domain *component*; the per-domain accuracies the estimator averages also
   carry `p(1−p)/m = 0.25/40` of binomial noise. Including it gives sd = 0.1613 and
   **0.905 / 0.793** — i.e. the knife-vs-gun co-primary is *already* a hair under 0.80 at the Holm
   alpha before any stratification is applied. This is derived from PR-048's own ICC/deff model, it
   is checkable on TRAIN alone, and it is recorded here because PR-049's `DEMOTION_CONTINGENCY`
   asks for exactly this kind of pre-test check. It is an observation about an arithmetic
   assumption, not a re-measurement: no per-domain SD has been measured on ts116m.

3. **Stratification buys cleanliness at a price that is quantified.** Every halving of the rows per
   domain costs roughly 0.06–0.09 of conjunctive power at the Holm alpha. Below `m ≈ 24` there is
   no stratified design left worth running: at ¼ of the population the Holm-corrected power is
   0.65 (3-way) and 0.52 (knife-vs-gun), and at 1/10 it is 0.41 and 0.27.

---

# What was NOT read, and what these three items do not settle

**No hidden state was read.** W3 is tokenizer-only; Z1 reads demonstration-block TEXT; Z2 is
arithmetic. None of the three items needs a representation, which is why all three are answerable
today while the extraction is still in flight. For the record, the extraction state at the time of
writing: `ts116m_full_button_bomb`, `ts116m_full_button_knife`, `ts116m_full_button_gun` and
`ts116m_full_basket_bomb` carry `DONE.json`; `basket_knife` is running; `basket_gun` has not
started; **every one of them is `--position codeword_last`**, and no `ts116m` run at
`--position last` exists.

**Z1 and Z2 are measured on VALIDATION and are a feasibility statement, not the analysis.** PR-050
step 2 stratifies TEST rows. Validation and test are 23 domains each, drawn from the same
114-domain pool by the same frozen manifest, so validation feasibility is the best available
prospective estimate of test feasibility — but it is an estimate. The direction of the error is
unknowable without reading test, and reading test is what the design forbids.

**No per-domain SD has been measured on ts116m.** Every power number above is labelled by the SD it
assumes: 0.1406 is PR-048's projected between-domain component, 0.3439 its 95 % upper bound on 5
df. PR-048 already requires a TRAIN-only nested-LODO SD measurement before the confirmatory run;
that measurement, not this table, is what should settle the demotion question.

**Z1's "at chance" is a threshold, not a fact of nature.** Under the weaker CI-COVERS tier the
answer for knife-vs-gun would still be no at usable n, and the 3-way's exact-0.3333 stratum would
count — at 138 rows over 21 domains. Both tiers are reported so the reader can apply their own.

# Appendix A — every arm-balanced stratification, both contrasts

Accuracy of the TRAIN-fit surface classifier on the arm-balanced VALIDATION rows. `frac` is the
share of the contrast's validation rows retained after balancing; `refit` is a classifier refit on
the same 17 features inside those rows, domain-grouped 5-fold. USABLE = 23 domains, ≥ 4 rows per
domain, ≥ 230 rows. AT CHANCE = |acc − chance| ≤ 0.03 and CI upper ≤ chance + 0.05.

### 3-way (chance 0.3333) — 0 of 17 at chance

| stratification | rows | frac | domains | acc | 95 % CI | refit | usable | at chance |
|---|---|---|---|---|---|---|---|---|
| `maxprob_q2` | 918 | 0.665 | 23 | 0.5741 | [0.5413, 0.6063] | 0.5458 | yes | no |
| `maxprob_q3` | 726 | 0.526 | 23 | 0.5455 | [0.5084, 0.5821] | 0.5289 | yes | no |
| `maxprob_q4` | 660 | 0.478 | 23 | 0.5470 | [0.5081, 0.5854] | 0.5061 | yes | no |
| `maxprob_q5` | 558 | 0.404 | 23 | 0.5538 | [0.5114, 0.5955] | 0.5179 | yes | no |
| `maxprob_q10` | 336 | 0.243 | 23 | 0.5506 | [0.4957, 0.6046] | 0.4792 | yes | no |
| `margin_q2` | 912 | 0.661 | 23 | 0.5779 | [0.5450, 0.6102] | 0.5669 | yes | no |
| `margin_q3` | 738 | 0.535 | 23 | 0.5339 | [0.4971, 0.5703] | 0.5271 | yes | no |
| `margin_q4` | 654 | 0.474 | 23 | 0.5596 | [0.5206, 0.5981] | 0.5566 | yes | no |
| `margin_q5` | 612 | 0.443 | 23 | 0.5539 | [0.5135, 0.5938] | 0.5033 | yes | no |
| `margin_q10` | 336 | 0.243 | 21 | 0.5119 | [0.4571, 0.5665] | 0.4792 | no | no |
| `margin_lo10` | 18 | 0.013 | 3 | 0.1667 | [0.0358, 0.4142] | — | no | no |
| `margin_lo25` | 186 | 0.135 | 18 | 0.4194 | [0.3476, 0.4938] | 0.4409 | no | no |
| `margin_lo50` | 456 | 0.330 | 22 | 0.5219 | [0.4750, 0.5686] | 0.5417 | no | no |
| `pref_q3` | 962 | 0.697 | 23 | 0.5125 | [0.4804, 0.5445] | 0.5042 | yes | no |
| **`pref_q5`** | **819** | 0.593 | **23** | **0.4896** | [0.4549, 0.5245] | 0.4371 | **yes** | no — +0.156 |
| `simplex_t2` | 324 | 0.235 | 21 | 0.3981 | [0.3445, 0.4537] | 0.3580 | no | no |
| **`simplex_t3`** | 132 | 0.096 | **13** | **0.3485** | [0.2677, 0.4363] | 0.3258 | **no** | no — CI too wide |

The closest the 3-way ever gets to 1/3 is `simplex_t3` at 0.3485, and it keeps 9.6 % of the rows
and only 13 of 23 domains. The best **usable** arm-balanced stratum is `pref_q5` at 0.4896 —
**+0.156 above chance**, on 819 rows across all 23 domains.

### knife-vs-gun (chance 0.5) — 1 of 17 at chance

| stratification | rows | frac | domains | acc | 95 % CI | refit | usable | at chance |
|---|---|---|---|---|---|---|---|---|
| `maxprob_q2` = `margin_q2` | 800 | 0.870 | 23 | 0.6425 | [0.6082, 0.6758] | 0.6350 | yes | no |
| `maxprob_q3` = `margin_q3` | 684 | 0.743 | 23 | 0.6418 | [0.6046, 0.6778] | 0.6418 | yes | no |
| `maxprob_q4` = `margin_q4` | 652 | 0.709 | 23 | 0.6319 | [0.5936, 0.6690] | 0.6104 | yes | no |
| `maxprob_q5` = `margin_q5` | 576 | 0.626 | 23 | 0.6337 | [0.5929, 0.6731] | 0.6424 | yes | no |
| `maxprob_q10` = `margin_q10` | 448 | 0.487 | 23 | 0.6161 | [0.5693, 0.6613] | 0.5848 | yes | no |
| `margin_lo10` | 40 | 0.043 | 8 | 0.5500 | [0.3849, 0.7074] | 0.5000 | no | no |
| `margin_lo25` | 152 | 0.165 | 19 | 0.5329 | [0.4503, 0.6142] | 0.5461 | no | no |
| `margin_lo50` | 400 | 0.435 | 22 | 0.5750 | [0.5249, 0.6240] | 0.5450 | no | no |
| `pref_q3` | 653 | 0.710 | 23 | 0.5620 | [0.5230, 0.6005] | 0.5712 | yes | no |
| `pref_q5` | 581 | 0.632 | 23 | 0.5439 | [0.5024, 0.5849] | 0.5077 | yes | no |
| `simplex_t2` | 592 | 0.643 | 23 | 0.5186 | [0.4775, 0.5595] | 0.5236 | yes | no |
| **`simplex_t3`** | **552** | **0.600** | **23** | **0.5054** | **[0.4629, 0.5479]** | **0.5109** | **yes** | **YES** |

**Balancing the arms RAISES the classifier on the scalar bins** — `maxprob_q2` goes from 0.5826
unbalanced to 0.6425 balanced — which is the second measurement of the same point: the unbalanced
low-confidence bin looked closer to chance partly because its class prior had shifted, not because
the surface signal had gone. Only conditioning on the **whole** probability vector *and* balancing
the arms removes it, and only for knife-vs-gun.

# Appendix B — check ledger and mutations

**52 checks, 45 PASS, 7 FAIL.** Every FAIL is a MEASUREMENT, not a harness defect:

| failing check | what it means |
|---|---|
| `Z1-refit-3way` / `Z1-refit-knife_vs_gun` | the lowest-confidence half is not surface-matched: a refit inside it is at 0.4986 / 0.5609 |
| `Z1-balanced-3way` | no arm-balanced stratification reaches chance 1/3 with usable n |
| `Z1-answer-3way` / `Z1-answer-knife_vs_gun` | **PR-050's kill condition**: no probability-vector BINNING with usable n reaches chance, on either contrast |
| `Z2-answer-3way` / `Z2-answer-knife_vs_gun` | the within-stratum estimator does not clear 0.80 conjunctive power at the Holm alpha |

`Z1-balanced-knife_vs_gun` PASSES — the single construction that works.

**16 of 16 mutations turned their target check RED.** A mutation that does not go RED means the
check cannot fail, so each is listed with the check it is supposed to break:

| mutation | what it does | target | result |
|---|---|---|---|
| `w3_perturb_final_token` | change one knife prompt's final token id | `W3-a` | **RED** |
| `w3_codeword_at_end` | move one prompt's last codeword occurrence onto the final position | `W3-b` | **RED** |
| `w3_concept_at_end` | make one prompt's final position decode to `' bomb'` | `W3-c` | **RED** |
| `w3_drop_arm` | drop the gun arm of one `(codeword, prompt_id)` | `W3-d` | **RED** |
| `w3_no_generation_prompt` | claim the template appends no generation prompt | `W3-scaffold` | **RED** |
| `empty_population` | bind every check to an EMPTY row set | `W3-d` | **RED** (REFUSED, zero rows) |
| `keep_excluded_domains` | keep `restaurant_kitchen` and `subway_station` | `POP-01` | **RED** (6960 rows) |
| `pool_doses` | pool `n_examples` 4 and 8 into one population | `POP-01` | **RED** (9576 rows) |
| `corrupt_split` | declare five TEST domains TRAIN as well | `POP-02` | **RED** |
| `read_test` | put TEST domains in front of the guard | `GUARD-TEST` | **RED** (REFUSED before any feature) |
| `plant_concept_in_demo` | plant the literal word `gun` in one demonstration block | `Z1-leak` | **RED** |
| `shuffle_labels` | permute the TRAIN labels against their own features | `Z1-fit-3way` | **RED** |
| `strat_one_bin` | collapse every stratification to one bin | `Z1-part-3way-maxprob_q2` | **RED** |
| `mde_no_beta` | drop the type-II term from the MDE | `Z2-mde` | **RED** |
| `no_binomial_noise` | ignore the binomial component of the per-domain SD | `Z2-inflation` | **RED** |
| `unbalanced_subsample` | subsample each cell to its LARGEST arm instead of its smallest | `Z1-armbalance-knife_vs_gun` | **RED** |

An earlier version of the label mutation permuted the feature ROWS instead of the labels; it left
enough residual structure that `Z1-fit-3way` stayed GREEN. That is recorded because a GREEN
mutation is supposed to mean the check cannot fail, and here it meant the mutation was too weak —
the same class of error the harness exists to catch, committed inside the harness.

Reproduce: `python scripts/dcs_ts_pr050_pr051_blockers.py --mutate` (254 s, CPU only).

---

# Verdicts

> ### **W3 — `--position last` IS a usable control site: it passes all four criteria on the full 6840-prompt population (token-identical across concepts 2280/2280 triples; strictly after every codeword occurrence 6840/6840; no concept surface, 1 distinct decoding; present 6840/6840). It is PURE CHAT SCAFFOLD, not content: it decodes to `'\n\n'` (token id 271) in 6840/6840 prompts, the last of the 4 tokens `<|start_header_id|>assistant<|end_header_id|>\n\n` that `add_generation_prompt` appends — a generation-header token nine positions downstream of `codeword_last` and five past the last content token. A null there is weaker evidence than a null at a content position, and `rel_end = -9` (`' actually'`) is an available content control that passes the same four criteria.**

> ### **Z1 — NO for the design as preregistered. Across 100 strata (3-way) and 74 (knife-vs-gun) from 17 candidate stratifications of the predicted-probability vector, ZERO usable strata reach chance on either contrast — not even under the weaker CI-covers rule. The closest usable are 0.4609 (3-way, +0.128 above 1/3) and 0.5826 (knife-vs-gun, +0.083 above 0.5). ONE construction does reach chance, and it is not the one PR-050 preregisters: arm-balanced joint simplex cells on knife-vs-gun give 0.5054, 95 % CI [0.4629, 0.5479], on 552 rows (60 % of the population) over all 23 domains, with a within-stratum refit at 0.5109. For the 3-way, 0 of 17 arm-balanced stratifications reach chance and the best usable one sits at 0.4896. PR-050's premise that "within a surface-matched stratum the surface classifier is at chance BY CONSTRUCTION" is false as written: binning cannot change pooled accuracy (0.5913 / 0.6630 under every partition) and does not balance the arms.**

> ### **Z2 — NO, not adequately powered. The one stratification that reaches chance retains m = 24 rows per domain instead of 40, lifting the observed per-domain SD from 0.1613 to 0.1737 and giving conjunctive power 0.858 at α = 0.05 but 0.721 at the Holm alpha PR-050 itself declares — below the 0.80 bar (MDE 0.1062, Holm 0.1186, against a bar of +0.15). Every coarser stratum is worse: ½ of the rows gives 0.687, ¼ gives 0.517, 1/10 gives 0.267. Stratification buys cleanliness at roughly 0.06–0.09 of Holm-corrected power per halving, and on this corpus the only clean stratum is not powered. Separately, and not caused by stratification: including the binomial component that PR-048's own ICC/deff model implies puts the UNSTRATIFIED knife-vs-gun contrast at 0.905 / 0.793 rather than PR-049's published 0.963 / 0.900 — already a hair under 0.80 at the Holm alpha before any stratum is taken.**
