# DCS thesis-scale — SECOND review, CODE lens

**Window** `e4d78bf0..b5359329` (12 commits). The first review (`A-042`) covered
`b80db84d..e4d78bf0` and is not re-reviewed; its findings are cited where they recur.
**Read-only review.** No file was edited, no job submitted, no probe run, no test split read.

Environment used for every measurement below:
`/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python` — **scikit-learn 1.9.0**, numpy 2.4.6.

Files read in full: `scripts/dcs_ts_pr048_analysis.py`, `scripts/dcs_ts_prereg.py`,
`scripts/dcs_ts_extract_multi.py`, `scripts/dcs_ts_verify_ts116n.py`,
`scripts/dcs_ts_length_match_pools.py`, `scripts/dcs_ts_gen_concept_harm_pools.py`,
`scripts/dcs_ts_build_ts116n.sh`, `scripts/dcs_ts_preflight.sh`,
`src/boombness/slurm/run_boombness.sh`, `configs/dcs_ts_pr048.json`, `configs/dcs_ts_pr049.json`,
plus `scripts/dcs_extract_under_ko.py` (the producer) and the four `ts116m_full_*` run dirs.

---

## SUMMARY TABLE

| # | Rank | Finding | Anchor |
|---|------|---------|--------|
| 1 | **CRITICAL** | The frozen analyzer cannot execute: `multi_class=` was removed from sklearn, and 1.9.0 is installed. `TypeError` on the first fit. | `dcs_ts_pr048_analysis.py:301,344` |
| 2 | **CRITICAL** | The permutation null and the observed statistic are fit by **different estimators** (`max_iter=200` vs `2000`) and no convergence is recorded. Any binding of the 200-iteration budget biases the headline p **downward**. | `:301` vs `:344` |
| 3 | **CRITICAL** | Running the PR-049 co-primary with default `--out` **silently overwrites the PR-048 primary result file**. | `:162` |
| 4 | **MAJOR** | Steps 5 and 6 of the analyzer's own docstring do not exist: **not one of nulls N1–N8 is implemented**, no secondary is implemented, and **no Holm correction is computed** although `multiplicity` mandates it across the two primaries. | `:26-28`, `:350-360` |
| 5 | **MAJOR** | The domain exclusion filter is **prose matching on a free-text field** (`"ENTIRE" in scope`) with a silent `.get(..., [])` default — the exact `C-086` shape the loader was rewritten to eliminate. | `:103-104` |
| 6 | **MAJOR** | `--selftest` reports **13/13 guards reachable** while `run_probe()` is dead on arrival (finding 1). The selftest exercises zero lines of the function that produces the headline. | `:377-439` |
| 7 | **MAJOR** | The mutation harness of `dcs_ts_verify_ts116n.py` has **no mutation for either gate added in this window** (`exactly-one-substitutable`, `COMPOUND`), yet prints "every gate must be demonstrably falsifiable / 4/4". This is the seventh unfalsifiable check. | `dcs_ts_verify_ts116n.py:352-354` |
| 8 | **MAJOR** | Selection over the 36-point grid is **not repeated inside the permutation loop**; the null therefore does not price the selection step. | `:314-348` |
| 9 | **MAJOR** | Nothing verifies the bound test set is the preregistered **23 domains / 68 train domains**. The analyzer prints `70 train` from the manifest while `split.n_train` says `68`. | `:118-126,188-190` |
| 10 | **MAJOR** | `load_split` verifies the manifest against **the manifest's own self-declared `manifest_sha16`** — a check that reads the same source it is checking. | `:120-123` |
| 11 | **MAJOR** | The analyzer verifies 3 of ~8 available provenance fields. It never checks `knockout_applied`, `layer_convention`, `model`, `activation_dtype`, `layers`, or `skip_reasons` — all present in `summary.json`. | `:258-263` |
| 12 | **MAJOR** | `has_compound()` (the `C-087` fix, copied into three files) is **blind to prefix compounds** — `gunfire`, `bombardment`, `knifepoint` — which `str.replace` rewrites just as happily as `handgun`. Measured: **0 of 13 920** shipped harm sentences hit it, so latent, not live. | `dcs_ts_verify_ts116n.py:98-103` + 2 copies |
| 13 | **MAJOR** | `Q-012`'s resolution states "the bank carries 30 rows per domain per concept per codeword, so m=60 is arithmetically TWO codewords." **Measured: 10, not 30.** The conclusion survives on other evidence; the stated derivation does not compute. | `configs/dcs_ts_pr048.json` `primary._codeword_scope_reading` |
| 14 | **MAJOR** | `dcs_ts_build_ts116n.sh` prints, as its own required-next-step, a command that gates the **superseded ts116n family** (no env vars). | `dcs_ts_build_ts116n.sh:78-79` |
| 15 | **MAJOR** | Wall clock: the permutation loop alone is **4.6–7.6 h** measured at the real data shape, against `#SBATCH --time=06:00:00`, and results are written only after the last permutation. | `:335-348`, `run_boombness.sh:8` |
| 16 | MINOR | `sign_test_two_sided` is one-sided-doubled: a *below*-chance majority returns `p = 1.0`. | `:60-73` |
| 17 | MINOR | Per-domain accuracies exactly at chance are counted as failures rather than dropped. | `:327` |
| 18 | MINOR | `preflight`'s ts116m bank check compares each bank to **its own build's meta file**, never to the PR-048 pin. | `dcs_ts_build_ts116n.sh:59-66` |
| 19 | MINOR | Three live scripts still hardcode the superseded `configs/dcs_ts_pr046.json`. | `dcs_ts116n_audit_leakage.py:56` +2 |
| 20 | MINOR | `${BOOMB_ARGS// /}` strips spaces only; a tab-only args value defeats the new guard. `_analyzer_status` says "Selftest: 11/11"; it is 13/13. | `run_boombness.sh:113` |

---

## 1. THE ANALYZER — `scripts/dcs_ts_pr048_analysis.py`

### 1.1 CRITICAL — `run_probe()` cannot run. `multi_class=` was removed from sklearn.

`dcs_ts_pr048_analysis.py:301` and `:344`:

```python
clf = LogisticRegression(C=C, max_iter=2000, multi_class="multinomial")   # :301
clf = LogisticRegression(C=C_sel, max_iter=200, multi_class="multinomial")# :344
```

`multi_class` was deprecated in scikit-learn 1.5 and **removed in 1.7**. Measured on the
environment named in the task:

```
$ python -c "from sklearn.linear_model import LogisticRegression; LogisticRegression(multi_class='multinomial')"
RAISES TypeError: LogisticRegression.__init__() got an unexpected keyword argument 'multi_class'
```

**Failure scenario, concrete.** All six banks finish. The operator runs
`python3 scripts/dcs_ts_pr048_analysis.py --prereg configs/dcs_ts_pr048.json --reps outputs/boombness/extract_boombness`.
The preregistration loads, the population binds, ~6 840 rows and 9 layers are read from disk
(several minutes of `torch.load`), and the run dies with a `TypeError` on the **first** of 36
selection fits, before writing anything.

This is not merely an inconvenience. `artifacts._freeze_rule` says *"The analyzer is committed
BEFORE the outcome exists. It is not edited to rescue an outcome."* The file therefore has to be
edited after data exist, in the frozen file, at the moment of maximum incentive. The
project-clean framing is: this is a **VOID-adjacent condition** — the frozen analyzer as committed
never could have produced any outcome, so nothing is lost by fixing it, but the fix must be a
recorded, outcome-blind amendment made *before* `--reps` is ever passed, with the diff limited to
removing the removed keyword.

Note the intended semantics are preserved for free: sklearn ≥1.7 uses multinomial
softmax for `solver="lbfgs"` with >2 classes unconditionally. Deleting `multi_class="multinomial"`
is behaviour-preserving for PR-048. **For PR-049 it is not**: with 2 classes the old
`multi_class="multinomial"` forced a 2-class softmax, while the default path is binary
one-vs-rest. For a 2-class logistic these give the same decision boundary up to
parameterisation, but the **regularisation is not identical** (softmax carries two weight vectors,
OvR one), so at a fixed `C` in `{0.01, 0.1, 1.0, 10.0}` the selected model can differ. Whoever
amends this must say which of the two PR-049 fits they mean and record it.

### 1.2 The permutation null — is a per-domain label-map permutation the right null?

The task asks this to be argued concretely. My answer: **the choice of group is correct; three
things about the implementation are not.**

**Why whole-domain relabelling is not available.** A whole-domain permutation is the standard
group-permutation null when the *label is a property of the group*. It is not here. Measured on
the bound population (`data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl`,
filtered to `cell=="C"`, `query_kind=="semantic_one_word"`, `n_examples==4`, minus the two
excluded domains): **1 140 rows over 114 domains, exactly 10 rows in every domain**, and there are
six such banks — so each domain carries `10 × 3 concepts × 2 codewords = 60` rows and **all three
classes occur inside every domain**. There is no whole-domain label to permute. Relabelling whole
domains is not a stricter alternative; it is undefined for this design.

*(Confirmation that 60 is the right m: `power.deff_at_m60 = 6.22` reproduces exactly as
`1 + 59×0.0884 = 6.216`, and `n_eff_test_rows = 23×60/6.22 = 221.9 ≈ 222`.)*

**The group that is implemented is the right one.** `:338-342`:

```python
perm = {d: rng.permutation(len(concepts)) for d in dom_list}
y2 = y.copy()
for d in dom_list:
    m = dom == d
    y2[m] = perm[d][y[m]]
```

The null hypothesis the primary is testing is *"there is no **domain-general** concept code at the
read site."* Under that H0, which physical class a given domain calls `bomb` is arbitrary and
independent across domains — i.e. the 6 label maps (K=3; 2 maps for PR-049) are exchangeable
across domains. That is exactly the group being sampled. The null preserves within-domain
separability perfectly (each domain's three classes stay perfectly distinguishable, just renamed),
which is right: within-domain separability is *not* the claim. What it destroys is the
cross-domain alignment of the code, which *is* the claim.

**Is the marginal class distribution changed?** No, and this is a point in the design's favour.
Because the bound population is exactly balanced — 10 rows per (domain, concept, codeword),
measured, not assumed — permuting the label *map* within a domain permutes three equal counts and
leaves the marginal class distribution **exactly** unchanged, both per-domain and globally. So the
classifier under the null cannot exploit a shifted prior. Had the design been unbalanced the null
would leak a per-domain prior signal; it is not.

Two further reassurances: the support is `6^68` configurations, so 10 000 draws are nowhere near
exhausting the group (no coarse-null artefact); and the maps are applied per *domain*, not per
`(domain, codeword)`, which correctly leaves the button/basket pairing intact inside a domain so
the null does not accidentally destroy the lexical-transfer structure as well.

**So the group is right. Here is what is wrong with the implementation of it.**

#### 1.2a CRITICAL — the observed statistic and the null are computed by different estimators.

`:301` (observed and selection) uses `max_iter=2000`. `:344` (null) uses `max_iter=200`. A
permutation test is only valid if the *only* difference between the observed value and each null
draw is the label assignment. Here the estimator differs too, so `obs` and `nulls` are not
comparable quantities and `group_permutation_p(obs, nulls)` at `:348` is not a permutation p-value.

**Direction of the bias, concretely.** Under a permuted label map the optimisation problem is
strictly harder — lbfgs has to fit 68 mutually inconsistent within-domain codes — so if the budget
binds anywhere, it binds on the null draws and not on the observed fit. An under-fit null
classifier generalises worse to the test domains, so `nulls` sit lower than they should, fewer of
them clear `obs`, `n_exceed` falls, and `p = (1+n_exceed)/(1+B)` comes out **too small**. The
headline is anti-conservative, and by an amount nothing in the artifact records.

**How binding is it?** I timed the exact shape (68 train domains × 60 rows = 4 080 × 4 096,
standardised) on random labels:

| C | max_iter | wall | `n_iter_` | converged |
|---|---|---|---|---|
| 10.0 | 200 | 1.7 s | 9 | yes |
| 10.0 | 2000 | 1.5 s | 9 | yes |
| 0.01 | 200 | 2.7 s | 14 | yes |

On *noise* the budget is not binding — 9–14 iterations against 200. That is reassuring but it is
not evidence about the real reps, where the within-domain structure is real and lbfgs will take
more steps. The defect that survives regardless is: **nothing in the code records `clf.n_iter_`,
nothing catches `ConvergenceWarning`, and nothing asserts the null fits converged.** If the budget
does bind on the real data, the artifact will contain no trace of it and the p-value will look
identical to a valid one. The fix is one line — use the same `max_iter` in both places and persist
`max(n_iter_)` over the null draws into the result JSON.

#### 1.2b MAJOR — the observed value is not recomputed through the null code path.

Related but separable: `obs` is produced by `fit_score(...)` at `:325`, the nulls by an inlined
copy of the same three statements at `:343-347`. The clean construction computes the observed value
as the identity permutation *inside* the loop, using byte-identical code. As written, any future
divergence between the two code paths (a second estimator kwarg, a different scaler) is invisible.

#### 1.2c MAJOR — selection is outside the permutation loop.

`:314-321` picks `(L_sel, C_sel)` from 36 grid points to maximise **validation** accuracy under the
**true** labels; `:344` then reuses that fixed pair for all 10 000 null draws. The null therefore
prices "how well does a classifier at layer `L_sel`, `C_sel` transfer?" and not "how well does
*the whole procedure, including a 36-point search*, transfer?".

This is much less bad than the `A-039` test-selection failure — selection reads validation only,
and the split manifest's `_fpr_evidence` records validation-selection FPR at 0.0467, calibrated.
But it is not nothing: validation and test domains are drawn from the same 114-domain pool and
share whatever domain-level nuisance structure exists, so a grid point picked to suit validation is
mildly pre-adapted to test. The bias is again in the anti-conservative direction. The honest
options are (a) redo selection inside each null draw — at 36× the cost this is out of reach given
finding 15 — or (b) state in the artifact that the reported p is conditional on the selected grid
point and cite the 0.0467 measurement as the calibration evidence. **(b) is defensible; saying
nothing is not.**

#### 1.2d Correct, for the record.
* `group_permutation_p` at `:81` uses `>=` for exceedance and `(1+n_exceed)/(1+B)` — both correct
  and conservative.
* The permutation is applied to `y2` but only `y2[tr]` is consumed at `:345`; test labels at `:347`
  are the true `y[te]`. That is right, not a bug — the null perturbs the *training* signal.
* `dom_list = sorted(set(dom[tr]))` at `:333` means validation and test rows are never relabelled.
  Harmless, since neither is used with `y2`.
* `rng` is seeded from `pr.require("split","seed")` at `:332`, so the null is reproducible.

### 1.3 CRITICAL — the PR-049 co-primary overwrites the PR-048 primary.

`:162`:
```python
ap.add_argument("--out", default="outputs/dcs_ts/pr048_result.json")
```
`configs/dcs_ts_pr049.json` names `artifacts.analyzer = "scripts/dcs_ts_pr048_analysis.py"` — the
same file runs both preregistrations. **Failure scenario:** the operator runs PR-048, gets a
headline, then runs `--prereg configs/dcs_ts_pr049.json` (the documented co-primary invocation) and
forgets `--out`. `pr048_result.json` is now the knife-vs-gun 2-way result at chance 0.5, with
`"prereg": "configs/dcs_ts_pr049.json"` buried inside it and no backup. Given that Holm across
the two primaries is mandated, both files must exist simultaneously. The default should be derived
from the prereg `id`, or refused when `--prereg` is not the default.

### 1.4 Does the analyzer touch TEST before selection is frozen? — **No. Traced clean.**

Full data-flow trace:
* `:264-281` loads every bound row into `X_by_layer` / `meta` regardless of split. Test *features*
  are in memory from the start, but memory residence is not selection.
* `:291` builds the three boolean masks. `:292-294` asserts each is non-empty — this reads
  `msk.sum()`, a count, not a label-outcome.
* `:295` `set(dom[tr]) & set(dom[te])` — domain identifiers only, no `y`, no `X`.
* `:299-304` `fit_score` fits `StandardScaler` and `LogisticRegression` **on `fit_mask` only**.
* `:314-320` the selection loop calls `fit_score(L, C, tr, va)` — fit `tr`, evaluate `va`. `te` does
  not appear.
* `:321-322` `select_hparams` reads only the validation `scores` dict.
* `:325` is the **first and only** use of `te` as an evaluation set, after `L_sel, C_sel` are bound.
* `:346-347` the null reuses the frozen `(L_sel, C_sel)`.

**Verdict: no test leakage into selection.** This is the part of the file that is right, and it is
the part `A-039` was about.

### 1.5 StandardScaler — fit on TRAIN only, everywhere, including the null. **Correct.**

`:300` `StandardScaler().fit(Xs[L][fit_mask])` where `fit_mask` is `tr` at every call site
(`:317` selection, `:325` test). `:343` in the null loop: `StandardScaler().fit(Xs[L_sel][tr])`.
Three call sites, three train-only fits, and `transform` is applied to the eval split rather than
a second `fit_transform`. This matches `classifier.standardisation` in the preregistration.

One inefficiency worth naming only because of finding 15: `:343` re-fits the *identical* scaler
10 000 times — the scaler does not depend on the labels. Hoisting it out of the loop is
behaviour-identical and removes ~10–20% of the runtime.

### 1.6 MAJOR — steps 5 and 6 of the docstring are not implemented.

`:26-28` promises:
> 5. domain-level group permutation, reporting every p NEXT TO ITS FLOOR
> 6. **the nulls the preregistration declares, each labelled with whether it can fail**

Step 6 does not exist. `grep -n "require_null\|nulls_required\|N1\|N4\|Holm\|AUROC\|lexical"
scripts/dcs_ts_pr048_analysis.py` returns **nothing**. `Prereg.require_null()` is defined at
`dcs_ts_prereg.py:107-111` and is called from **no file**. The eight nulls that
`configs/dcs_ts_pr048.json` declares as mandatory — N2 domain permutation, N3 full-prompt leakage,
N4 length-only classifier, N5–N8 — are not computed.

Likewise absent: every `SECONDARY` family member (macro OvR AUROC, per-class AUROC, lexical
transfer button→basket, the `n_examples=8` replication, the hedge-free stratum), and **the Holm
correction itself**, although `multiplicity` declares `"correction": "Holm across the two
primaries, alpha=0.05 family-wise"` and `_absent_members_enter_at_p_1` prescribes how absent
members enter it. The result dict at `:350-360` has no field for any of this.

**Failure scenario.** The headline p is computed and published. `alpha=0.05` is compared against a
raw p that was never Holm-adjusted against the PR-049 co-primary, and none of the eight declared
gates ran. This is `B-020` recurring one layer up: the preregistration is now machine-read for
*thresholds* while its *required analyses* remain uncoded. Note that `nulls_required` entries carry
no `can_fail` field either — so even the metadata the docstring promises to print ("labelled with
whether it can fail") is not in the config to print.

### 1.7 MAJOR — the exclusion filter is prose matching, with a silent default.

`:103-104`:
```python
excluded = {e["domain"] for e in pop.get("preregistered_exclusions", [])
            if "ENTIRE" in str(e.get("scope", "")).upper()}
```

Two problems in two lines, in the file whose header says *"There is not a single numeric gate
literal below … `Prereg.require()`, which REFUSES rather than defaulting when a key is absent."*

1. **`pop.get(..., [])` is a silent default.** Every other field in `bind_population` goes through
   `pr.require()`. If `preregistered_exclusions` were renamed or dropped, this binds zero
   exclusions, `restaurant_kitchen` (`C-082`) and `subway_station` (`C-087`) re-enter the analysis
   population, and **no error is raised** — the run just analyses 116 domains and reports 70/23/23.
2. **`"ENTIRE" in scope.upper()` is prose matching on a free-text field.** This is the `C-086`
   shape verbatim: `dcs_ts_prereg.py:161-172` was rewritten *in this window* precisely to replace
   `"BLOCKING" in status and "done" not in status` with structured booleans, and the lesson written
   there — *"the fix is not a better regex, it is structural"* — was not carried across to the
   analyzer's own filter.

It works **today**: I checked all three entries. `restaurant_kitchen` and `subway_station` carry
`"the ENTIRE analysis population, all concepts, all cells"`; `school_campus` carries
`"occurrence-ordinal and all-codeword-sites knockout analyses only"` and is correctly *not*
excluded. Running `--prereg configs/dcs_ts_pr048.json` with no `--reps` prints
`excluded: ['restaurant_kitchen', 'subway_station']`. **Verified correct as of `b5359329`.**

**Failure scenario.** A future exclusion is written with `"scope": "the whole analysis population,
all cells"` or `"scope": "global"`. It is silently ignored, a contaminated domain enters the
primary, and mandate §15 — which `:37` swears this file refuses to violate — is violated with a
green run. The correct shape is a boolean `"scope_entire_population": true`, refused when absent,
exactly as the loader now does for `blocking`/`done`.

### 1.8 MAJOR — the selftest is 13/13 green over code that cannot run.

I ran it (`--selftest`, no data, read-only):

```
[selftest] 13/13 guards reachable
```

Every one of the 13 cases exercises `sign_test_two_sided`, `group_permutation_p`, `fmt_p`,
`select_hparams`, or `dcs_ts_prereg.validate`. **Not one line of `run_probe()` is executed**, and
`sklearn` is never imported — which is why finding 1 does not surface. `artifacts._analyzer_status`
in the frozen config advertises "Selftest: 11/11 guards reachable" as evidence the analyzer is
sound; it is now 13/13, and it is evidence about the five helpers, not about the probe.

The specific hole: `fit_score`, `domain_mean_acc`, `run_probe`, `load_bank_rows` and `_find_run`
have **zero** test coverage. All five are reachable with a synthetic 3-domain, 3-class, 6-feature
fixture and a fake `reps` directory in under 40 lines, which would have caught finding 1 the moment
it was written.

Two smaller notes inside the selftest itself. `:435-438` accumulates passes into a variable named
`n_red` — a copy from the mutation harness, where RED means "the guard fired"; here it means the
opposite, and reading the code the two senses collide. And `:423-424`
(`"for_extraction accepts the live config now that the checklist is closed"`) is the `C-089`
stale-selftest shape with the polarity flipped: it asserts a property of the live project, not of
the guard, and it will go red the day a legitimate blocker is reopened.

### 1.9 MAJOR — provenance verification is 3 fields out of 8 available.

`:254-263` verifies `bank_rows_sha16`, `position`, `attn_implementation`. I read the four
`ts116m_full_*` run directories; `summary.json` also carries, unread:

```
knockout_applied: False        layer_convention: 'block_L == hidden_states[L+1]; ...'
model: 'meta-llama/Llama-3.1-8B-Instruct'   activation_dtype: 'torch.bfloat16'
layers: [6..14]                n_rows_attempted/captured/cached: 22272/22272/22272
skip_reasons: {}
```

Every one is currently correct — the three complete button banks match their PR-048 pins exactly
(`4ca3ec165ab5b018`, `65eb4fa533890eff`, `c7ceb5a151a2788a`), zero skips, `eager`, `codeword_last`.
So this is a *guard* defect, not a live data defect. But:

* **`knockout_applied` is unchecked.** `_find_run` at `:200-216` selects a directory by tag prefix
  and `DONE.json` alone. A knockout run submitted under the same `--tag` would carry the same
  `bank_rows_sha16`, the same `position`, the same `eager`, and the analyzer would accept its
  representations as the baseline. `primary.void` names exactly this ("dead hook") as a VOID
  condition; the analyzer cannot detect it.
* **`layer_convention` is unchecked** — and this is the field `R-104` spent GPU job `860184` to
  confirm. `dcs_extract_under_ko.py:141` implements `hs[L+1, pos, :]` and records the convention
  string in both `summary.json` and the `.pt` cache (`:625`). The analyzer reads
  `cache["layers"]` at `:266` and never reads `cache["layer_convention"]`. Comparing it to
  `read_site.layer_convention` is one line and would bind the experimentally confirmed fact to the
  analysis.
* **`skip_reasons` / `n_rows_captured` are unchecked.** `capture()` drops rows on
  `no_occurrence_at_position` (`dcs_extract_under_ko.py:471-473`). Currently 0/22 272 on all three
  finished banks. If a future bank drops rows unevenly, the domain-mean is computed over a silently
  truncated set — and `:37` lists "silently drop non-installing domains — mandate §15" among the
  things this file refuses to do.

### 1.10 MAJOR — nothing checks the bound population against the preregistered counts.

`load_split` (`:118-126`) verifies the manifest's sha and its `field_name`, then returns
`m["assign"]`. It does **not** compare against `split.n_train/n_validation/n_test`. Running the
no-`--reps` branch prints:

```
split:      70 train / 23 val / 23 test
```

against `configs/dcs_ts_pr048.json` `split.n_train: 68`. The disagreement is *explained* — the
manifest assigns 70 and two train domains are excluded downstream, per `split._exclusion_note` —
but nothing in code closes the loop, and the analyzer's own summary line prints the number that
contradicts the preregistration.

Worse, after binding there is **no assertion that `nd == pr.require("primary","n_test_domains")`**.
`nd` at `:328` is whatever came out of the data. **Failure scenario:** one basket bank's extraction
silently loses a handful of domains (finding 1.9), `nd` becomes 21, `sign_test_two_sided(k, 21)`
returns a p against a different floor (`2/2^21` rather than `2/2^23`), the sign test is now
underpowered relative to the frozen `power` block, and the artifact reports it as if it were the
preregistered 23-domain test. Three assertions — `len(set(dom[tr])) == 68`,
`nd == 23`, `len(set(dom[va])) == 23` — cost nothing and are required by
`primary.n_test_domains` already being in the config.

### 1.11 MAJOR — the split manifest verifies itself.

`:120-123`:
```python
m = json.load(open(mpath))
want = pr.require("split", "manifest_sha16")
if m.get("manifest_sha16") != want:
```
`manifest_sha16` is a **field inside the manifest**, not a hash recomputed from its `assign` block.
Editing one domain's assignment and leaving `manifest_sha16` alone passes this check silently.
This is `feedback_check_reads_same_broken_source` exactly. `dcs_ts_split_manifest.py --check`
(invoked by preflight) may recompute it, but the *frozen analyzer* — the one thing that must be
self-sufficient — does not. `dcs_ts_prereg.py:75-80` already has `_file_sha16`; the manifest could
be hashed for real in one line.

Note the same asymmetry in the loader: `dcs_ts_prereg.py:129-131` checks that **every** `*_sha16`
in the tree is non-null, but `:133-159` recomputes only two kinds — `banks[*].bank_file_sha16`
(against the file) and `pools[*].content_sha16` (against a field *inside* the pool file, same
self-verification shape). The docstring at `:24` claims "any pinned artifact's ACTUAL hash
disagrees with the pinned one" is a refusal. For `split.manifest_sha16`, `bank_rows_sha16` and the
rest, it is not — those are only checked for non-emptiness.

### 1.12 MINOR — the sign test is not two-sided, and ties count as failures.

`:60-73` sums `comb(n,i)` for `i in range(k, n+1)` and doubles. For `k < n/2` this exceeds 1 and is
clipped, returning `p = 1.0`. `primary.success` describes it as a "two-sided sign test".

**Failure scenario:** the probe is *below* chance in 20 of 23 test domains — a real, interesting,
publishable negative. `sign_test_two_sided(3, 23)` returns `p = 1.0` and the artifact records "not
significant" where the correct two-sided p is `2·P(K≤3) = 0.0026`. Given `primary.negative`
requires a powered null, mis-reporting the direction matters.

Separately, `:327` `k = sum(1 for v in per_dom.values() if v > chance)` counts a domain at exactly
`1/3` as a failure. Standard practice drops ties and reduces `n`. With 60 rows per test domain an
exact tie needs exactly 20 correct, so the impact is small — but `20/60 == 1/3` is exact in IEEE
754 float, so it is reachable, and it is the conservative direction.

### 1.13 MAJOR — runtime. The frozen `n_perm` may not fit the wall clock.

`primary.n_perm = 10000`. Measured at the exact train shape (4 080 rows × 4 096 features,
standardised, lbfgs, 3 classes):

| C | seconds/fit | × 10 000 |
|---|---|---|
| 10.0 | 1.7 | **4.6 h** |
| 0.01 | 2.7 | **7.6 h** |

Plus 36 selection fits and ~6 GB of `torch.load`. `src/boombness/slurm/run_boombness.sh:8` sets
`#SBATCH --time=06:00:00`, and the partition is `killable`. The result JSON is written at
`:361-363`, **after** the last permutation — a preemption or a wall-clock kill at hour 5.9 loses
the entire run and leaves no partial null distribution. Two banks-worth of preregistrations
(PR-048 and PR-049) doubles it.

Concrete mitigations that change no science: hoist the scaler out of the loop (§1.5), set
`n_jobs`/thread count deliberately, checkpoint `nulls` to disk every 500 draws, and request a
longer `--time` on the analysis job specifically. None of these require touching the frozen
statistics.

---

## 2. `scripts/dcs_ts_extract_multi.py` — item 6

### 2.1 Fail-closed: **correct.**
`:72-78` calls `subprocess.call` per bank and `return rc` on the first non-zero exit — it never
continues past a failure, and `:80` prints "all N completed" only after the loop. `:52-54` refuses
an empty `--banks`. `:62-64` refuses a missing bank file *before* spending GPU time. It shells out
per bank so no CUDA state crosses banks. No defect.

### 2.2 Effective command vs the per-bank `runargs/*.args`: **identical.**
Diffed by hand. `:65-68` builds

```
<python> -u scripts/dcs_extract_under_ko.py --bank <REPO>/data/boombness_prompts/boombness_prompt_bank_ts116m_<name>.jsonl
         --no-knockout --layers 6,7,8,9,10,11,12,13,14 --position codeword_last --tag ts116m_full_<name>
```

`runargs/dcs_ts116m_full_basket_bomb.args` (and the other five) contain exactly
`--bank … --no-knockout --layers 6,…,14 --position codeword_last --tag ts116m_full_basket_bomb`.
Same flags, same order, same values; the only difference is an absolute vs repo-relative `--bank`
path, and `cwd=REPO` at `:72` makes them equivalent. `runargs/dcs_ts116m_rest.args` requests
`button_gun,basket_bomb,basket_knife,basket_gun` with `--family ts116m --tag-prefix ts116m_full`.
**The claim in the docstring — "exactly the same flags it would have received as its own job" — is
true.**

### 2.3 MINOR — nothing binds the driver to the preregistration.
`--layers` and `--position` are argparse **defaults** (`:47-48`), not values fetched from
`configs/dcs_ts_pr048.json`. They happen to match `read_site.layer_grid` and `read_site.position`
today. A caller who passes `--layers 6,8,10` produces runs the analyzer will crash on at `:278`
(`run_layers.index(L)` → `ValueError`), which is loud but late — after the GPU time is spent. The
driver could `load(prereg)` and read both, which is the pattern the rest of the phase adopted.

---

## 3. Gates, generators and shell — items 5 and 7

### 3.1 MAJOR (the seventh unfalsifiable check) — the new G1 gates have no mutation.

`dcs_ts_verify_ts116n.py:352-354`:
```python
muts = [f"g1_share_{CONCEPTS[1]}", f"g1_other_{CONCEPTS[1]}",
        f"g2_{CODEWORDS[0]}", f"g3_{CODEWORDS[0]}"]
```
and `:365-367` prints *"A MUTATION THAT DOES NOT GO RED MEANS THAT GATE CANNOT FAIL"* and exits
non-zero unless `n_red == len(muts)`.

This window **added two new gate conditions** at `:199-205` — the inflection-aware,
case-enumerated `occurrence_counts` check (`C-076`/`C-079`) and the `has_compound` check
(`C-087`). It added **no mutation for either**. `g1_other_{cc}` injects
`"A gun was found next to the {cc}."`, which trips the *other-concept* gate, not the
substitutable-occurrence gate. So the harness prints `4/4 mutations turned a gate RED` and the two
checks the phase spent `C-079`, `C-080` and `C-087` building are the two with no falsifiability
evidence.

**Failure scenario.** A refactor of `occurrence_counts` inverts a condition — say `n_all != 1 or
n_sub != 1` becomes `and` — and the gate stops seeing plural-only sentences. `--mutate` still
prints 4/4 RED, the preflight still prints "ts116m gates G1-G3 pass", and the corpus that reaches
the probe carries demos contributing zero codeword occurrences. Two one-line mutations fix this:
inject `"Several bombs were found in the loading bay."` (plural-only) and
`"...a large, black handgun..."` (compound), each of which must turn `G1[cc]
exactly-one-substitutable-{cc}` red.

This is the seventh instance the task predicted, and it is the same shape as `C-080`: the gate that
guards the corpus was itself never shown to be able to fail.

### 3.2 MAJOR — `has_compound()` is blind to prefix compounds.

`dcs_ts_verify_ts116n.py:98-103`, copied verbatim into
`scripts/dcs_ts_gen_concept_harm_pools.py` and `scripts/dcs_ts_length_match_pools.py`:

```python
def has_compound(sentence, concept):
    n_sub  = len(re.findall(re.escape(concept), sentence, flags=re.I))
    n_word = len(re.findall(r"\b" + re.escape(concept) + r"\w*\b", sentence, flags=re.I))
    return n_sub != n_word
```

`\bgun\w*\b` matches `gunfire`, so `n_sub == n_word == 1` and the sentence is **not flagged** —
yet `str.replace("gun", "button")` rewrites it to `buttonfire` just as it rewrote `handgun` to
`handbutton`. The rule the comment states — *"THE SUBSTRING COUNT MUST EQUAL THE WHOLE-WORD
COUNT"* — is implemented as "substring count equals **prefix-word** count", which is a weaker
rule that catches only suffix compounds. Measured:

```
has_compound("A witness described the gun as a large, black handgun.", "gun") -> True   (caught)
has_compound("The gunfire stopped and the gun was recovered.",         "gun") -> False  (MISSED)
has_compound("A bombardment followed the bomb threat.",               "bomb") -> False  (MISSED)
has_compound("He held the knife at knifepoint.",                     "knife") -> False  (MISSED)
```

I scanned every shipped harm sentence in the three pinned pools
(`demo_pools_116dom_tsm_{bomb,knife,gun}.json`) for prefix compounds the guard misses:

```
scanned 13920 shipped harm sentences; 0 prefix-compounds MISSED by has_compound
```

**So the live corpus is clean and no result is affected.** The defect is in the guard, and it is
the eighth instance of the class the guard was written to close. Correct predicate:
`re.search(rf"\w{re.escape(concept)}|{re.escape(concept)}\w", s, re.I)`. Note also the three
copies are byte-identical duplicates — the comment in `dcs_ts_build_ts116n.sh:39-41` argues
against exactly this ("parameterised rather than copied so the two families cannot drift apart"),
and here the same function is triplicated across three files, so a fix has to land three times.

### 3.3 MAJOR — the build script prints an instruction that gates the superseded family.

`dcs_ts_verify_ts116n.py:129-130` now defaults `BANK_TAG=ts116n`, `POOLS_TAG=ts` — the
**superseded** family, whose `19/19` was retracted by `C-080`. `dcs_ts_preflight.sh:92,95`
correctly passes `POOLS_TAG=tsm BANK_TAG=ts116m`. But `dcs_ts_build_ts116n.sh:77-79` prints, as
its own "NEXT, and required before any extraction":

```
  python3 scripts/dcs_ts_verify_ts116n.py --mutate     # gates G1-G3 + falsifiability
  (then re-run the G4 concept-backing and G5 leakage audits against ts116n)
```

with no environment variables. An operator who follows the script's own instruction after building
ts116m gates **ts116n**, gets a green report, and believes the live family was gated. The script
already knows the tags (`$BANK_TAG`, `$POOLS_TAG` are in scope at `:42-43`); interpolating them
into the printed command is a one-line fix. The safer form is to make the tags **required** rather
than defaulted, so a bare invocation refuses.

### 3.4 MINOR — the ts116m bank check does not bind to the PR-048 pin.

`dcs_ts_build_ts116n.sh:59-66` reads `want` from `${out%.jsonl}_meta.json` — the meta file the
build itself wrote — and compares it to a recomputation from the `.jsonl`. This detects a bank
edited after its build; it does **not** detect a bank *rebuilt* (meta and jsonl both change
together) away from the hashes frozen in `configs/dcs_ts_pr048.json`. `dcs_ts_preflight.sh:93`
then reports `OK "6/6 ts116m banks match bank_rows_sha16"`, which reads as binding to the
preregistration and is not.

Mitigating: the analyzer *does* check the prereg pin against `summary.json` at `:252-257`, and the
loader checks `bank_file_sha16` against disk at `dcs_ts_prereg.py:142-147`. So the binding exists
— just not where preflight claims it. The honest wording is "match the hashes their own build
recorded".

### 3.5 MINOR — live scripts still read the superseded PR-046.

`grep -rln "dcs_ts_pr046" scripts/` →
`dcs_ts116n_audit_leakage.py`, `dcs_ts_verify_ts116n.py`, `dcs_ts116n_audit_concept_backing.py`,
`dcs_ts_length_match_pools.py`, `dcs_ts_prereg.py` (docstring only).
`dcs_ts116n_audit_leakage.py:56,213` hardcodes `PREREG_PATH = configs/dcs_ts_pr046.json` and opens
it at runtime. `dcs_ts_length_match_pools.py` — the tool that **produced the tsm pools pinned in
PR-048** — also cites it. PR-046 is byte-frozen and superseded by PR-048/PR-049 per
`configs/dcs_ts_pr048.json` `supersedes`. Nothing is currently wrong (the exclusion lists agree),
but the G5 leakage audit is reading its population definition from a superseded document. These
should take the prereg path as an argument.

Nothing in the window references the **VOID `ts116`** family as a live target: the only hits are
`dcs_ts116_domain_split.json` (a filename, correct — the split is over the 116 *domains*, not the
void bank) and the historical notes in `dcs_ts_preflight.sh:87-91` and
`configs/*.json:401`, which describe the fix. **Item 5 verdict: the void family is fully retired;
the superseded ts116n family is not.**

### 3.6 `src/boombness/slurm/run_boombness.sh` — the new args guard.

`:113` `[ "${BOOMB_REQUIRE_ARGS:-0}" = "1" ] && [ -z "${BOOMB_ARGS// /}" ]`. The guard is
**live, not dead code** — the phase log records `BOOMB_REQUIRE_ARGS=1` on the extraction
submissions (log lines 1688, 1965) and `scripts/dcs_ts_layer_convention_test.py:44` carries it in
its documented submit line. It correctly closes the stated hole: a mistyped `ARGSFILE=` leaves both
`BOOMB_ARGSFILE` and `BOOMB_ARGS` empty and the job refuses.

Two MINOR gaps:
* `${BOOMB_ARGS// /}` strips **spaces only**. An argsfile containing a single tab or a lone
  newline survives `$(cat)` (which strips only *trailing* newlines) and defeats the guard.
  `[ -z "$(echo "$BOOMB_ARGS" | tr -d '[:space:]')" ]` is the portable form.
* `dcs_ts_preflight.sh:126-127` prints the recommended submit line **without**
  `BOOMB_REQUIRE_ARGS=1`. The guard the phase relies on is not in the phase's own printed
  boilerplate, so it depends on the operator remembering it every time.

---

## 4. What I checked and found CORRECT

Recorded so the next reviewer does not repeat it.

* **No test leakage into selection** — full trace in §1.4.
* **Scaler fit on train only at all three call sites**, including inside the permutation loop (§1.5).
* **The permutation group is the right one** for a design where all three classes occur inside every
  domain; whole-domain relabelling is undefined here, not merely stricter (§1.2).
* **The permutation preserves the marginal class distribution exactly**, because the bound
  population is exactly balanced at 10 rows per (domain, concept, codeword) — measured (§1.2).
* **`(1+n_exceed)/(1+B)` with `>=`** — correct and conservative (`:81`).
* **The p-floor discipline** (`fmt_p`, `:85-90`) does what `C-069` demanded, for both statistics.
* **`_find_run` requires `DONE.json`** (`:211`) and `run_id` is `tag_%Y%m%d_%H%M%S_pid`
  (`common.py:433-435`), so the fixed-width stamp makes `sorted(...)[-1]` genuinely newest.
* **`extract_multi` fails closed and matches the runargs exactly** (§2.1, §2.2).
* **The three complete button banks** carry `bank_rows_sha16` matching their PR-048 pins,
  `position=codeword_last`, `attn_implementation=eager`, `knockout_applied=False`,
  `layers=[6..14]`, `22272/22272` rows captured, `skip_reasons={}`.
* **`dcs_extract_under_ko.py:141`** implements `hs[L+1, pos, :]`, matching
  `read_site.layer_convention` and `R-104`'s job `860184`.
* **`dcs_ts_prereg.py:161-192`** — the `C-086` fix is structural (boolean `blocking`/`done`, with a
  refusal for malformed items) and its mutation is genuinely exercised at
  `dcs_ts_pr048_analysis.py:416-428`.
* **`_clean_strict`** (`dcs_ts_gen_concept_harm_pools.py`) now correctly requires both directions —
  exactly one occurrence across inflections **and** exactly one in a substitutable case form.

---

## 5. RECOMMENDED ORDER OF WORK, before `--reps` is ever passed

1. **Finding 1.** Remove `multi_class="multinomial"` from `:301` and `:344`, in a commit that says
   plainly it is an outcome-blind amendment to a frozen analyzer, and that records the PR-049
   binary-fit semantics question (§1.1). Nothing else can be tested until this is done.
2. **Finding 2.** Make `max_iter` identical at `:301` and `:344`, and persist `max(clf.n_iter_)`
   over the null draws into `res["permutation"]`.
3. **Finding 3.** Derive `--out` from the prereg `id`.
4. **Findings 9, 11.** Add three count assertions and one `layer_convention` / `knockout_applied`
   check — five lines, all cheap, all currently satisfied by the real data.
5. **Finding 6.** Write the synthetic-fixture selftest for `run_probe`. It would have caught 1.
6. **Finding 4.** Decide explicitly and in writing whether N1–N8, the secondaries and Holm are in
   scope for this phase's headline. If they are not, say so in the artifact; do not leave a
   docstring promising step 6.
7. **Finding 7.** Two mutations in `dcs_ts_verify_ts116n.py`.
8. **Finding 15.** Time one real fit before submitting; checkpoint the null distribution.

## 6. UNKNOWN

* Whether `max_iter=200` binds on the **real** representations. It does not on noise at the real
  shape (9–14 iterations); nothing about the real reps is knowable without running the probe,
  which this review must not do.
* Whether the three basket banks will land with the same `0` skip count as the button banks. They
  were still running at review time (`ts116m_full_basket_bomb_20260907_054404_4164227` has no
  `DONE.json` and no `summary.json`).
* Whether any of N1–N8 are implemented in a file outside the eight named in the task. I grepped
  the analyzer and the loader only; `require_null` has no caller anywhere in `scripts/`.
