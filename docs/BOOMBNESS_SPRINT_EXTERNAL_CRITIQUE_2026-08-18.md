# External critique — Boombness Objective Sprint

**Date:** 2026-08-18 · **Reviewer:** adversarial audit (47 agents, 2-stage find→refute) plus direct
verification in the main loop.
**Scope:** `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` vs the shipped code, outputs and both reports.
**Method:** 102 candidate findings; the 40 non-minor ones were each handed to an independent verifier
prompted to *refute* it. 31 confirmed, 9 refuted. Everything below is a confirmed finding; the ones
marked ✔verified-here I re-derived myself from the committed artifacts.

---

## Verdict

The engineering discipline is genuinely above the norm for this kind of project: the 2×2
identification design is real, the tokenization audit is complete and correct on both models, the
failure ledger is mandatory and 130/130 runs carry it, provenance is recorded at 130/130, the probe
splits are domain-grouped with shuffled-label controls, and the sprint self-retracted seven claims
before I got here.

But **three defects each independently break a load-bearing claim**, and the report has drifted into
a state where its own executive summary states the opposite of its conclusion. None of the three is
in the retraction log.

---

## Tier 1 — breaks a published claim. Fix before this goes to Mahmood or Matan.

### 1. The §2.6 comprehension control does not measure comprehension ✔verified-here
`src/boombness/score_behavior.py:308`

`readout_ids` computes the whole-word id set for each answer option and then `primary` mode throws it
away, keeping only the **leading-space** token (`' literal'`=24016, `' coded'`=47773). The readout
position is immediately after `<|start_header_id|>assistant<|end_header_id|>\n\n`, where the model
emits the **no-leading-space** form (36885 / 66630). So the "forced choice" is scored on tokens the
model is not about to emit.

Measured on the committed baseline run (`base_20260816_203355_3985444`, 288 comprehension rows):

| statistic | value |
|---|---|
| mass on the two answer options, median | **4.4e-05** |
| p90 | 2.1e-04 |
| max | 1.2e-03 |
| rows where the pair holds >1% of next-token mass | **0 / 288** |

Every §2.6 verdict in report §4b is a log-ratio inside that 1e-5 tail. That includes
**"`project_out` is the only arm that leaves comprehension unchanged (p=0.681)"** — the sentence the
report uses to justify calling the project_out ASR result *"the sprint's cleanest causal test"*. An
intervention that genuinely destroyed comprehension while leaving the far-tail ordering intact would
be certified "preserved" by this code.

The repo already ran the diagnostic that finds this (progress log :767 — a properly forced framing
puts 0.979 on the answer vs 1.4e-2 as-is) and applied the fix only to `semantic_forced_choice`.
Separately: `semantic_forced_choice`, the 288-row framing built to fix exactly this, **was generated
into the bank and never scored by any run**.

*Fix:* score the summed `full_word_ids`, or move the readout behind a forced prefix. Then re-run §4b.
Note the option sets are asymmetric (4 variants for "literal", 2 for "coded"), so summing needs care.

### 2. `analyze_steering.py` crashes at HEAD, so the G4 artifact the report cites is pre-fix ✔verified-here
`src/boombness/analyze_steering.py:139` writes `wilson95_IID_UNDERSTATES`; `:151` reads `r['wilson95']`.
`rows` always contains the baseline arm, so this is an unconditional `KeyError` **before** the
coherence gate, the paired contrasts, the control band, the sign test, and before any JSON is written.

Commit `accfa714` ("clustered ASR intervals") therefore **has never executed**. The committed
`outputs/boombness/steering_analysis.json` (Aug 17 09:36) contains only the old `wilson95` key and no
`ci95_domain_clustered` — I checked. The report's §4 G4 table and the appendix both cite this file as
current evidence, and the commit message itself says the iid intervals understate by 1.32×.

Related, same class: `analyze_steering.py:66` enforces `require_done` on the baseline only, never on
the intervention arms, despite commit `b093e50d` claiming "require_done across all analyzers".

### 3. Retraction #3 was only half-applied — the edge *ranking* still sits at the retracted token ✔verified-here
`src/boombness/surgical_knockout.py:271`

```python
dsts = sorted({last[-1], readout_pos})
dst  = dsts[0]                        # for ranking/reporting
```

With `--dst both` (the mode both reported G3 runs used) `last[-1] < readout_pos`, so `dst` is always
the **final codeword occurrence** — the exact destination retraction #3 called "FATAL to all of §10".
The *knockout* was fixed (`query_positions=dsts` cuts into both); the ranking was not. `dst` feeds
`dominance_at(..., dst=dst)` at :296, which defines `topk_demo` / `bottomk_demo` / `same_head_random`
— i.e. the entire "surgical, not ablate-everything" claim ranks edges by flow into token ~104 while
the readout is at ~113.

It also silently truncates the demo set: `:288` filters `i < dst`, so with `--dst both` every demo
token between the codeword and the readout is dropped.

Consequence: the observed topk/bottomk near-null (−0.078 vs −0.00004) **cannot distinguish** "the
ranking is real and these edges don't matter" from "the ranking was measured at the wrong token".
G3's headline is not established.

---

## Tier 2 — statistical machinery that changes published numbers

### 4. `t_sf` is numerically wrong for small |t|, and it is the whole sprint's t reference ✔verified-here
`src/boombness/analyze_g8.py:52`. The `_betainc` Lentz continued fraction omits the symmetry transform
`I_x(a,b) = 1 − I_{1−x}(b,a)`, required when `x > (a+1)/(a+b+2)`. At df=5 that threshold is 0.636, so
the CF runs outside its convergence region for **all |t| < 1.69**.

Proof from the published artifact alone, no recomputation needed —
`outputs/boombness/g9_three_predictor_lastpos.json`, term `refusalness`:

```
t = 0.01138   df = 5
p_cr1                          = 0.7656      <- published
p_cr1_normal_ANTICONSERVATIVE  = 0.9909
```

t(5) has heavier tails than the normal, so `p_t ≥ p_normal` always. **0.766 < 0.991 is impossible.**
The true value is 0.9914. The error is always in the anticonservative direction.

`analyze_g9` imports this as `t_sf_2sided` for every `p_cr1`; `reanalyze_corrected` imports `t_crit`.
So every clustered p in the sprint at small |t| is wrong, and the direction of the error is the
dangerous one. Replace with `scipy.stats.t` (the analysis env has scipy; the login shell does not).

### 5. The "cite this one" permutation p tests a different quantity than the ρ printed beside it
`analyze_g64.py:275`, `analyze_g2.py:316`, `analyze_g9.py:374`. `rho` is the **raw pooled** Spearman;
`p_within_domain_perm` demeans x and y within domain first. They are adjacent columns with no
distinguishing label. In `qwen3_g2_analysis.json` the file quantifies its own mismatch: ρ=+0.3638
beside `within_domain_slope`=+0.1381 (2.6× smaller), with the cited p=0.0050 attached to the +0.364
headline. In `g2_analysis_lastpos.json` the cited p is "significant" (0.0235) for a quantity that is
never reported as the estimate, while the reported ρ=+0.086 is n.s.

In `g64_metric_comparison/correlation_table.csv` the p column is not even monotone in |ρ| — a reader
ranking metrics by p gets the ordering backwards.

### 6. Layer selection is uncorrected for G2, while the identical exposure is flagged for G1 ✔verified-here
`g2_analysis_cwpos.json` scans **20 predictor columns** (10 layers × {cos, proj}); L12|proj is the
headline. The report flags "one arm of ~130" for G1 but attaches no selection caveat to
ρ=+0.307 / p<5e-4. `probes.py:393` has the same shape — `best_layer_by_auroc` maximised on the test
set with no validation split.

`reanalyze_corrected.py:185` compounds it: the docstring says Holm corrects the 32 layers tested, but
`pv` is built over the 10 layers on the command line. At m=32, L4's p=0.001631 exceeds the 0.001613
threshold and **stops being rejected** — and the report cites "holm_rejected True only at L4 and L31"
twice as its multiplicity backstop.

### 7. `surgical_knockout` abandons cross-fitting for ~54% of rows
`:239` takes the first of `('dev','heldout')` and breaks, then uses that one direction for every row
regardless of `row['split']`. 1272/2352 rows are dev, so for those the edge ranking is chosen
**in-sample** — while the `all_demo`/random control arms are direction-independent. That is an
in-sample advantage handed to exactly the targeted arm in the G3 contrast. No `is_self_fit` field is
emitted, so it can't be filtered post hoc either.

`:225` additionally head-truncates a **domain-prefixed** alphabetical list (the A11-10 defect fixed in
`aggressive_patching` and never ported), and `--n-families` counts *prompts*: `--n-families 6` with
`--n-examples 4,8` gives 6 prompts over 3 families, all from the first 3 alphabetical domains. So
G3's "n=6 families" is 3 domains × 2 splits, effective G=3.

### 8. `--fit-dir` consumers never validate what the directions were fitted on
`extract_boombness.py:484` (plus `score_behavior.py:293`, `aggressive_patching.py:404`,
`surgical_knockout.py:240`) `torch.load` the direction payload and never read `payload["meta"]`,
which records `position`, `model` and `layers`. The 2026-08-17 fix added a *per-row readout* assert —
that proves where **h** was read, not where **d** was fitted. So the phantom-cell combination
(fit at one position, read at another) passes every current guard.

Latent, not active: I enumerated all 63 runs carrying a `fit_dir` and every one matches on both
sides. But `extract_boombness.py:361` makes the layer half silent by design — `d = payload[name].get(L); if d is None: continue` drops the column, writes the row, calls `ledger.ok()`, and reports
`n_failed=0` for a run in which the headline metric does not exist at 22 of 32 layers.

### 9. Single-draw controls presented as control *bands*
`aggressive_patching.py:461` seeds `random` and `orthogonal` with `args.seed + L` — one vector per
layer, reused across all 24 families and 6 domains. The domain bootstrap then resamples that one
vector 24 times, so the control CI contains prompt- and domain-level variance and **zero
direction-level variance**. The report already learned this lesson for the G4 steering band
(retraction #7, between-draw sd 0.0301) and did not propagate it to §5.4.

`probes.py:236` is the same shape: one shuffled permutation per layer, re-drawn identically in every
fold, presented as a null. probes' own stated stopping rule ("shuffled AUROC meaningfully above 0.5
means the split is leaking") is violated at layers 8/24/28/31 and no code enforces it.

### 10. `aggressive_patching` readouts are tautological at any patched layer
`:188` — `readout_layers` (default {8,12,16,18,20,24,28,31}) overlap the patched `windows` (singletons
L8/L12/L18/L24, every band, and `all`). At a readout layer inside the patched window the captured
vector **is** what the intervention just wrote: zero propagation, 100% of span by construction. The
house helper `ds_common.patch_layer_sweep` exists specifically to forbid this ("the sweep must stop at
R−1") and is not called. In `g1strat_20260818_133953_3374345`, `boombness|L18|proj` under
`transplant|query_only|L18` equals the donor ceiling bit-for-bit on all 48 prompts.

These are plan §5.3's required "direction projection score" and "logit lens bomb score" per
intervention — so the plan's own metric is uninterpretable for ~1/3 of the transplant cells,
unflagged. (`semantic_logodds`, which the headlines actually use, is unaffected.)

---

## Tier 3 — the report contradicts itself

### 11. The executive summary states the conclusion the report withdraws 800 lines later ✔verified-here
The gate table (L23–37) plus L306, L534, L662, L698 assert:

- "G4 … **No.** Both signs of `d_surface` suppress ASR"
- "**§12 was therefore not built.** That is a decision forced by data"
- "**Do not build the GCG objective on this axis.**"
- FINAL §18 = **B, mechanistic but not causal**

L785 and L841–843, added 2026-08-18, say: *"This supersedes the §18 = B label and reopens §12"*,
*"⛔ §18 = B is WITHDRAWN"*, *"§12.2 is REOPENED"*. No retraction marker or forward pointer on any of
the five stale passages. A reader who reads the gate table — the intended use of a gate table — leaves
with the retracted conclusion. The short update handles this correctly at its L256; the full report
does not.

**`§0.3` is also a dangling reference.** L31 and L382 both cite "§0.3, above". No section 0.3 exists.

### 12. The gate table's one causal row is a superseded run, and mixes two outcome scales
L31 quotes ASR 0.219 → 0.300 with "controls +0.104/+0.109, p=0.020/0.025". Those reproduce, from a
**192-token, n=270** run — but (a) +0.104/+0.109 are *continuous strongreject score* deltas, not ASR
(the ASR deltas are +0.111/+0.122), and the row calls them ASR points; (b) the controls are
**additive** `d_surface:add` arms compared against a **projection** arm; (c) L862 reports the same
intervention at 512 tokens / n=420 as +0.0378 **p=0.0037 against baseline**, while L31 says
"vs baseline alone p=0.117". Same arm, reported as both n.s. and highly significant, no reconciliation.

### 13. G1's headline is superseded by the project's own committed replication ✔verified-here
Report L27/L99: **+84% of span, CI [+57%, +105%], n=8 families, 2 domains.**
`outputs/boombness/g1_stratified.json` (git-tracked, written 2026-08-18 14:45 — five minutes after the
report's last edit), same design, **24 families across 6 domains**:

| pair | frac_of_span | CI95 |
|---|---|---|
| harm_ctx | **0.681** | [0.499, 0.945] |
| benign_ctx | 0.726 | [0.559, 0.930] |

Commit `b66e9484`'s own message says *"Honest headline is +68%"*. Neither report says it. The report is
16 span-points high, and its most prominent caveat ("effective n is nearer 2 than 8") is obsolete.

### 14. The "matched footing" incremental-R² gives refusalness 5 predictors and Boombness 1
L272's "+0.144 vs +0.028" is `R²(5 refusalness cols + boombness) − R²(boombness)` against
`R²(joint refusalness + boombness) − R²(joint refusalness)`. Every "refusalness adds" cell is a
5-column block; every "Boombness adds" cell is one column. At genuinely matched df the @last cell
flips the comparison. §19 Q7 and the short update's "the increment comparison, done correctly" both
rest on this, and it is what keeps the §18=B label alive.

### 15. The second causal result's "harmful yes, benign no" split is one significant cell out of six
Recomputing L874–879 from `judge/len_B` vs `len_Bctrl` (n=960, domain-clustered) reproduces every
point estimate and adds the inference the table omits: `natural_doublespeak` +0.0560 **p=0.0077**
(n=420); `direct_harmful` +0.0556 **p=0.363** (n=72); `direct_codeword` +0.0590 **p=0.438** (n=36).
All six CIs overlap. Eleven lines later the report annotates *Qwen3's* equivalents "(n.s.)" — two
different evidentiary standards in adjacent tables. Drop the n.s. cells and the claim reduces to
"it helps doublespeak", the weaker statement L884 says it has surpassed.

### 16. The Llama-vs-Qwen3 non-replication compares 512 tokens against 192
L892 enumerates what is matched and omits generation budget. `len_B`/`len_Bctrl` are max_new=512;
`q3_projout`/`q3_projctrl` are max_new=192. The progress log (:4864) records that this exact variable
halved the Llama effect (+0.0736@192 → +0.0378@512). At Qwen3's budget Llama's own benign cells move
too (benign_remap +0.042, concept_in_benign_ctx +0.040) — the pattern the report treats as
disqualifying for Qwen3.

### 17. §5's corrected role result has no committed artifact
F(5,355)=20.30, p=8.1e-18, "11 of 15 pairwise surviving Bonferroni" (L403, L618, L622, §19 Q8) exists
only as prose in the progress log. `role_analysis.json` — the file the appendix assigns to §11 —
contains per-style means and a mediation block, no F test. Meanwhile `g11_role_full.json` runs the
*identified* version on 36 crossed stems and its own `identifiability` field says `plain` is not
identified against any role style — yet `plain` is one of the 6 levels in the F test. This is the
"no script regenerates this" provenance failure the report elsewhere says caused an earlier retraction.

---

## Tier 4 — plan sections not done, or done and not reported

**Not built at all** (plan §16): `example_count_sweep.py`, `prompt_level_correlation.py`,
`role_confusion_variants.py`, `gcg_objectives.py`, `run_boombness_gcg.py`, `plotting.py`, `utils.py`.
The first three have functional equivalents (`analyze_g8`, `analyze_g2`/`g9`, the role block); the
GCG pair is legitimately gated off by §12's conditional.

**All 9 `configs/boombness/*.yaml` are missing** — only `args_*.txt` argfiles exist. Per-run
`config.json` covers plan §2.1's intent, so this is bookkeeping, not a claim risk.

**Named outputs never produced:** `correlation_summary.json`, `regression_summary.md` (both plan §9),
and 9 of the 12 named plots — every §8 plot (`boombness/asr/refusal/comprehension_vs_n_examples`,
`boombness_and_asr_by_strength`) and every §9 plot (`boombness_vs_asr_scatter`, `_binned`,
`boombness_by_condition`, `asr_by_condition`).

**Plan §15's 18 required report sections:** items 2 (what was implemented), 6 (aggressive patching
results), **7 (Boombness metric comparison)**, 14 (negative results), 15 (failure modes), 16
(recommended next experiments) have no section. Item 7 is the substantive one: §6.4 was run and closed
(`g64_metric_comparison/`), and grepping both reports for "metric comparison", "probe_boombness",
"direction_boombness", "logit_lens" returns **zero hits**. The answer it would report is unflattering
— `common_all_three` is 72 of 270 — which is exactly why it belongs in the deliverable.

**Plan §10.4 arm D (remove both) is absent from both reports** despite being run, judged, and called
the sharpest causal result in `causal_claims.md`. On `direct_harmful`, removing d_surface + refusal
gives +0.681 while *adding* it gives +0.000 — a sign flip that depends on harm type, i.e. directly
relevant to whether §12 has an objective.

**Plan §14 / ClearHarm:** it is integrated in this repo (`data/clearharm/`,
`scripts/build_clearharm_manifests.py`, five manifests under `data/manifests/`). Zero mentions across
`src/boombness/*.py`, the progress log and both reports. Every ASR number comes from the sprint's own
generator. Given the report already concedes the arm-F gain is "largest where the doublespeak mapping
is weakest" and "+0.267 on `benign_remap`, where carrot→bomb is never taught" — the signature of a
bank artifact — an external harmful set is the discriminating experiment, and it is sitting in-repo.
The "Specific limits a reader should carry" list names one model, one pair, one judge, and no dataset
limitation.

**Plan §5.2's alpha sweep** ran 4 of 6 doses, and **0.25 — the dose carrying every behavioural claim
— is not among them.**

**Plan §5.4's `decision_gate.md`** answers all eight questions (well), but Q8's verdict rests on the
withdrawn G4 negative and Q5 promises an update that never came. It is the artifact the plan
designates as authoritative for the §12 go/no-go, and it currently says the opposite of the project's
position. The newer §5 run (`g1strat_...`) has no gate file.

**Plan §4.1's designed variance was generated and then never analysed.** `strength`,
`consistency` and `example_position` exist in the bank exactly as specified and appear in no analysis
script — only pass-through copies. G2 is computed on 234 core2x2 rows. Plan §8 asked for the strength
sweep explicitly. Three of the axes are also confounded as built:

- `example_position`: `near` gets 0 filler sentences, `far`/`distributed` get 6 → 403 vs 792 chars, a
  96% length increase, from a filler pool used nowhere else. And the `position` block emits no `near`
  row, so the baseline must come from `core2x2` — the cross-block comparison that caused retraction #6.
- `consistency='conflicting'`: the demo block stays fully consistent and one counter-mapping sentence
  is appended before the query. Plan §4.1 says "examples disagree". The appended sentence adds a
  codeword occurrence in the closest-to-query position — the one position the sprint reads from.
- `strength`: `strong`/`aggressive` inject the **concept token** into a codeword-surface prompt, and
  `aggressive` repeats it 3×. A monotone "Boombness rises with strength" curve would be fully
  explained by literal `bomb` tokens in context plus occurrence count.

Only 12 rows per `example_position` level, below plan §14's "preferably ≥20 per condition".

**Reproducibility manifest (plan §2.1):** 130/130 runs record git_commit, git_dirty, command, argv,
slurm_job_id, gpu, hostname, torch/transformers. Two required fields are recorded **nowhere**:
`seed` (0 of 145 config.json, 0 of 130 metadata.json — recoverable via `argv` + `git_commit` only) and
`tokenizer_revision` (0 of 145).

**The bank sha is two different functions under one key name.** `prompt_families.py:568` sets
`bank_content_sha16` = sha over concatenated per-prompt shas (`7002854cf834e9f9`). `common.py:235`
sets `bank_content_sha16` = sha over the file bytes (`71bea179345ed118`). The report header quotes
the second, the progress log quotes the first, as if they were the same identifier. **Nothing in the
repo ever compares them** — I grepped; there are three references and no comparison. The docstring at
`common.py:215` states the purpose is "a content hash makes a mismatched join detectable instead of
invisible". It is a fourth guard that never executes, of exactly the class §8 says are all now fixed.

**Also silent by construction:** `score_behavior.py:425` — the query-kind dispatch has no `else`, so
an unhandled kind falls through to `ledger.ok()`. `--query-kinds semantic_forced_choice` produces
`counts: {}`, `n_failed: 0`, and a `DONE.json` — indistinguishable from a complete run to
`require_done`. `judge_boombness.py:199` writes `DONE.json` before the null-judgement abort gate;
`:92` never checks the generation run it judges actually finished. `coherence_gate.py:99` returns
`coherent=True` for an empty or all-short sample.

---

## What is actually solid, and should be defended

- **The 2×2 surface × context design.** It separates surface identity from context, and it quantified
  the confound rather than arguing about it. This is the reusable contribution and it survives.
- **Prompt alignment — Matan's original objection is answered.** Over the 288 four-cell families:
  `n_target_occurrences` identical across all four cells in **288/288**; per-condition mean length
  528/500/512/516 chars; median within-family relative length spread **9.8%**. (Caveat: report says
  "240 matched 2×2" and "216 where the invariant is defined"; the bank has **288** families carrying
  all four cells. Three denominators, none of which is the data's.)
- **Tokenization audit.** Complete, correct, and it caught a real trap (890/5808 two-subtoken
  occurrences in an earlier bank). Verified for both Llama-3.1-8B and Qwen3-14B, 2352/2352, 0
  ambiguous. The one limitation: the plan asked for multi-token span *handling*; the sprint forced
  single-token by construction instead. Fine here, blocks a second concept pair.
- **Probes.** Domain group-k-fold, 6 regimes covering the plan's 4 datasets, AUROC/AUPRC/accuracy/
  Brier, shuffled-label controls. Modulo finding 9, this is done properly.
- **`analyze_g9`'s role-identifiability refusal** is the right instinct — a script that declines to
  fit an unidentifiable term. (It is currently unfalsifiable: `:207` tests family overlap on a
  `family_id` string that *embeds the style name*, so overlap is 0 by construction and the gate would
  refuse even after the design is fixed. Worth repairing precisely because the instinct is right.)
- **The retraction culture.** Seven self-caught retractions with root causes is more than most
  published work manages. The failure mode is not dishonesty, it is that the *deliverable* has not
  been re-derived from the current state of the evidence.

---

## Recommended order of work

1. **Fix `t_sf`** (use scipy). It is 3 lines and it touches every clustered p in the sprint.
2. **Fix the comprehension readout**, re-run §4b. Until then no intervention can be called
   non-destructive, which means the second causal result has no comprehension control.
3. **Fix `analyze_steering.py:151`**, re-run, replace `steering_analysis.json`. The G4 table is
   currently backed by a file the fix commit was supposed to overwrite.
4. **Fix `surgical_knockout` `dst`** (rank at `readout_pos`), re-run G3. Retraction #3 is not closed.
5. **Rewrite the report head.** One conclusion, stated once, at the top. Merge the two ★ sections into
   the body; put the withdrawn verdicts in a retraction table, not in the gate table. Fix `§0.3`.
   Promote `g1_stratified` (+68%, 24 families, 6 domains) to the G1 headline.
6. **Add the missing §15 sections**, especially item 7 (metric comparison) and §10.4 arm D.
7. **Run one arm on ClearHarm.** It is the cheapest experiment that discriminates "real mechanism"
   from "bank artifact", and the report's own `benign_remap` +0.267 result is why it is needed.
8. Decide explicitly whether the strength / consistency / position axes get analysed or get deleted
   from the bank. Right now they are generated, confounded, and unexamined — the worst of the three.
