# SELF-REVIEW 2026-08-06 — adversarial code review of the tick41–tick48 changes

Scope: `scripts/validate_refusal_directions.py` (--induce-eval / --harmless-holdout),
`scripts/validate_all_outputs.py` (`expect_refval`), `scripts/analyze_rep_predicts_behavior.py`
(`--sweep`), `scripts/build_claim_audit.py` (`_dig` list paths, boolean identity).

Method: read the current source, `git show` on 85a23d76 / 251e5050 / 7e0e1b8e / c8d54f91, and
**empirical verification** — re-ran the reconciler on the committed refval run, re-derived the Holm
implementation against a reference over 3000 random p-vectors with ties, simulated the fold
stratifier at small class counts, and cross-checked the hard-coded P7 layer list against
`outputs/refval_clearharm_20260806_054117_722611/summary.json`. No script was modified, no job
submitted, nothing committed.

**Two things the author got right and should not re-litigate:** the Holm implementation is exactly
correct (D20), and the `both_gains_positive` / `valid` distinction in `expect_refval` faithfully
reproduces `validate_refusal_directions.py:560-562` (D13). Every induce-side list is
length-consistent and every paired McNemar pairs equal-length, correctly-ordered lists (D7 — the
zip audit **passes**).

**The four things that should change a conclusion, not just a line of code:**

| # | Sev | One line |
|---|-----|----------|
| D1 | **HIGH** | The harmless holdout is **vacuous for the `existing` family** — its induce arm is scored entirely on its own fit set. The two families are therefore not measured under the same protocol, and four claim revisions (BR-08, RP-01, TR-01, RP-04) rest on the between-family difference. |
| D14 | **HIGH** | RP-04's "L16 AUC 0.888 **HIGHER** than L21's 0.874" is a max-over-32 selection compared against a fixed layer, with no paired test and a gap (0.014) inside the script's own measured noise (fold sd 0.055). |
| D15 | **HIGH** | "cross-validated" names two different things twenty lines apart. The sense supporting the headline is "validated in both direction families", not cross-validation. **There is no cross-validated 0.888** — the 5-fold is computed only at L21. |
| D12 | **HIGH** | The refval branch of the split-disjointness step is **near-vacuous**: it compares two argparse strings to each other, touches no data, and is structurally blind to the only contamination risk this session introduced. A `--harmless-holdout 0` run — which the script's own docstring calls "induce refusal by construction" — passes it green. |

---

## 1. `scripts/validate_refusal_directions.py`

### D1 — [HIGH] The harmless holdout is vacuous for the `existing` family
`validate_refusal_directions.py:388-393` (split), `:397` (`H_harmless` = fit half only), `:459`
(induce arm = eval half). Docstring `:45-49` claims the split stops "the refit direction … scored on
its own fit set".

That is true for `clearharm` and **false for `existing`**. The shipped directions in
`outputs/refusal_alllayers/` were fit with the *entire* 20-item `HARMLESS_INSTRUCTIONS` as their
negative class — verified: `outputs/refusal_alllayers/refusal_direction_llama_L16.json` →
`"n_harmless": 20`, and `build_refusal_direction_llama.py:287` iterates the whole list. So
`HARMLESS_EVAL` ⊂ the `existing` fit set, item for item.

**Failure scenario.** `existing` is evaluated on 10 benign prompts that its own diff-of-means was
optimised to push to the low end of `v`; `clearharm` is evaluated on 10 it has never seen. Adding
`+alpha*v` to an in-sample negative is the easiest possible induce test. Any per-family difference
in `induce_gain` is confounded with this asymmetry — and the between-family difference is exactly
what tick47/tick48 turned into four claim revisions:
`existing` L21 induce `+0.300` vs `clearharm` L21 `+0.000` is the sole evidence for RP-01's rewritten
`abstract_block`, and BR-08/TR-01 are qualified on the mirror pattern.

**Fix.** Either refit `existing` on `HARMLESS_FIT` and validate that (a third family), or state
plainly in P7 §4c and in every claim that quotes a family split that the `existing` induce arm is
in-sample and the `clearharm` one is not. Do not compare the two `n_valid` counts (12 vs 15) as if
they were commensurable.

### D2 — [MEDIUM] The gap alpha is fit-set-derived and differently biased per family
`:437-438` — `alpha = raw_proj(H_eval_direct).mean() - raw_proj(H_harmless).mean()`, where
`H_harmless` is the **fit** half (`:397`).

For `clearharm`, `v` is the diff-of-means fit on exactly those 10 vectors, so
`mean raw_proj(H_harmless)` is minimised by construction → the gap is inflated → the eval half is
over-dosed. For `existing`, both halves are in-sample, so no such inflation. The dose is therefore
biased in *different* directions for the two families, on top of D1.

**Failure scenario.** Over-dosing degrades generations; `score()` (`:217`) returns
`refused = bool(s) and kw_refusal(...)`, so an empty completion counts as *not refused* and
suppresses `induce_gain`. A direction can fail its induce arm purely from an alpha derived from its
own fit set. `empty_induced` is recorded but nothing gates on it, and the reconciler does not check
it against a threshold (only against raw, D10).

### D3 — [MEDIUM] `plan` misreports the fit set size and the generation budget, and omits the two new flags
- `:342` `"n_harmless_fit": len(brd.HARMLESS_INSTRUCTIONS)` → hard-codes 20. Under the default
  holdout the fit and the alpha see **10**. Verified on the committed run:
  `summary["plan"]["n_harmless_fit"] == 20` while `summary["rows"][0]["n_benign"] == 10`.
- `:350-351` `generations_planned = len(fams)*len(layers)*4*len(eval_conds) + 2*len(eval_conds)`
  assumes both induce arms have `len(eval_conds)` rows. Verified: plan says **5160**,
  `DONE.json.raw_rows` is **3870** — a 33 % overestimate baked into PLAN.json, which is the file a
  dry-run is supposed to budget from.
- `plan` records **neither `induce_eval` nor `harmless_holdout`** (verified absent). They exist only
  in `RUNMETA.json`'s args blob, which neither `expect_refval` nor `build_claim_audit` reads.

**Failure scenario.** `summary.json` is the only artifact the reconciler and the claim audit read.
Reconstructing the protocol from it gives you a 20-item fit set and a 5160-generation budget, both
wrong, and gives you **no way at all to tell a `--harmless-holdout 0` run from a clean one**. This is
the enabling defect for D12.

### D4 — [MEDIUM] `plan` is frozen against the provisional 32-layer list and never refreshed
`:325` builds `layers` provisionally as `range(32)`; `:337-352` stores `plan["layers"] = layers`,
`plan["existing_pt_present"]`, `plan["generations_planned"]`; `:368` **rebinds** `layers` to a new
list from `lm.num_layers`. `plan` keeps a reference to the stale object.

**Failure scenario.** Run `--layers all` on a non-32-layer model — which `plan["layers_source"]`
explicitly anticipates ("provisional 32; re-resolved from lm.num_layers"). `summary["layers"]` would
be `0..27` while `summary["plan"]["layers"]` says `0..31`, and `existing_pt_present` reports on four
layers that were never touched. Worse, `proj_alpha` (`:335`) is keyed on the provisional list, so
`--induce-alpha-mode projsummary` on a >32-layer model raises `KeyError` at `:434` after the model is
already loaded. Currently masked only because Llama-3.1-8B is exactly 32.

### D5 — [MEDIUM] `--val-n-items` above the held-out harmless count silently caps the induce arm
`:459` `src = HARMLESS_EVAL[:len(eval_conds)]`. `HARMLESS_EVAL` is **always 10** (the source list has
20 entries). So `--val-n-items 40` yields ablate n=40, induce n=10, with no warning — the only
warning in the arm (`:477`) fires on the base *rate*, not on n. `--val-n-items 0` ("all") is also
capped at 10.

**Consequences that reach the paper.** `induce_gain` and `induce_specificity` are quantised to 0.1,
so "specificity > 0" in the `valid` predicate (`:561-562`) means *at least one of ten items flipped*.
`score = ablate_gain + induce_gain` (`:559`) then sums two arms whose resolution differs 2× (n=20 vs
n=10) with no weighting, and `best_layer` is the argmax of that sum. The audit's own P7-32 note
already flags that L22 and L30 "clear the bar on clearharm by exactly one item" — but the script that
produces the verdict never says so, and `best_layer` inherits the imbalance silently.

**Fix.** Print a WARNING whenever `len(tmpl_induce) < len(tmpl_direct)`; record `n_harmless_eval` in
`plan`; consider weighting or reporting `score` per-arm.

### D6 — [LOW] `induce_ids` are positional within `HARMLESS_EVAL`, so ids collide across holdout settings
`:460` `induce_ids = [f"harmless_{i}" for i in range(len(src))]`. Under `--harmless-holdout 1`,
`harmless_0` is `_HL[10]`; under `0` it is `_HL[0]`. Two runs' `raw.jsonl` will join on the same id
for different prompts. Index into `_HL` instead.

### D7 — [LOW, latent] `mcnemar_pair` zips without a length assertion — but every current call site is correct
`:239-244`. I traced all four call sites and all five induce-side lists as requested:

| list | length | source |
|---|---|---|
| `src` / `tmpl_induce` | `min(len(HARMLESS_EVAL), len(eval_conds))` | `:459-461` |
| `induce_ids` | same | `:460` |
| `inlen_induce` | same — derived *from* `tmpl_induce` | `:469-470` |
| `base_ben` | same — one score per `tmpl_induce` | `:472` |
| `ind`, `indr` | same — `zip(tmpl_induce, inlen_induce)`, equal lengths | `:504-507` |

`raw.jsonl` labels base-benign rows with `induce_ids[i]` (`:493`), not `eval_conds[i][0]` — correct.
The arms loop (`:508-514`) pairs `("induce", ind, induce_ids)` and `("ablate", abl, eval ids)`
correctly. `induce_p` pairs `base_ben` vs `ind` (both n=10); `ablate_p` pairs `base_harm` vs `abl`
(both n=20); the `_vs_rand` pairs are within-arm. **No zip truncates anything it should not, and
every paired McNemar is equal-length and correctly ordered.** The assert at `:468` covers
`tmpl_induce`/`induce_ids` only.

The defect is latent: `mcnemar_pair` will silently truncate, and this file *just acquired* the
property that two arms have different n. One future edit that pairs `base_harm` against `ind`
produces a meaningless p-value with no error. Add `assert len(a) == len(b)`.

### D8 — [LOW] Harmless-set disjointness is only *printed*, never asserted
`:394-396` prints `disjoint={not (set(FIT) & set(EVAL))}`. If `HARMLESS_INSTRUCTIONS` ever gains a
duplicate the run proceeds with overlap and the only trace is a line in a `.out` file. (Currently
20 entries, 20 unique — verified.) Make it a `raise SystemExit`.

### Answers to the three directed questions
1. **Does the shorter induce arm break any zip / pairing?** No — see D7. Verified exhaustively.
2. **Does the fit half reach the refit and the gap-alpha, with the eval half never leaking in?**
   Yes for `clearharm`: `H_harmless` is built from `HARMLESS_FIT` only (`:397`) and is the sole
   harmless input to `fit_direction` (`:414`), `sep_fit` (`:415-416`) and the gap alpha (`:438`).
   **But the guarantee is worthless for `existing` (D1)**, and the alpha is fit-set-derived (D2).
3. **`--val-n-items` > held-out harmless?** Silently capped at 10 with no warning (D5), and
   `plan.generations_planned` becomes a 33 % overestimate (D3).

---

## 2. `scripts/validate_all_outputs.py` — `expect_refval`

### D12 — [HIGH, LOUD] The refval branch of the split-disjointness step is near-vacuous
`validate_all_outputs.py:1014-1020`. The entire "check" is:

```
f, e = plan.get("fit_split"), plan.get("eval_split")
if f is not None and e is not None and f == e: <issue>
```

It reads two argparse values back out of the plan and compares them **to each other**. It touches no
row, no id, no item. It can fail only if the operator literally typed `--fit-split test --eval-split
test`. Meanwhile `:1023` disables the real id-overlap check for this type entirely
(`for r in ([] if typ == "refval" else rows)`).

**It can be defeated trivially.** Pass `--fit-split "" --eval-split test`. `conditions_for`
(`validate_refusal_directions.py:146`) applies **no filter at all** for a falsy split
(`if split and it.get("split") != split`), so `fit_conds` becomes every item in the bench including
the whole eval split. Total fit/eval contamination — and `f != e`, so the guard passes silently.

**It is blind to the risk this session actually created.** The new fit/eval boundary is the
`HARMLESS_INSTRUCTIONS` half-split, and `summary.json` records neither `induce_eval` nor
`harmless_holdout` (D3). A run with `--harmless-holdout 0` — which the harness's own docstring
(`:47-49`) says would "induce refusal by construction" — produces byte-identical validator output to
the clean run. **A checker that cannot fail on the thing it was written for is worse than none: it
launders the contaminated run as reconciled.**

Side effect: `res["splits"]` becomes `{"fit": "train", "eval": "test"}` for refval where every other
type stores `{split: row_count}` (`:1034`). The console column at `:1147` therefore stops reporting
per-arm n for precisely the phase that has unequal arm sizes.

**Minimum fix.** Have the harness write `plan.induce_eval`, `plan.harmless_holdout`,
`plan.n_harmless_fit`, `plan.n_harmless_eval`; have `expect_refval` raise an **issue** (not a warn)
when `induce_eval == "harmless" and not harmless_holdout`, and cross-check
`plan.n_harmless_eval == n_benign` recomputed from raw.

### D9 — [MEDIUM] The docstring claims `best_layer` is reconciled. It is not. And it is the one number the claim audit asserts.
`:784` — "plus the `by_family` roll-ups (n_valid / valid_layers / **best_layer**)". The code
(`:860-873`) emits `n_layers`, `n_valid`, `valid_layers[j]`, `invalid_layers[j]`. **`best_layer` and
`best_score` are never put.** Both are present in the committed summary.

Meanwhile `build_claim_audit.py` claim P7-32 checks
`by_family.clearharm.best_layer == 18`. So the single roll-up value the claim audit asserts is the
one the reconciler does not verify against `raw.jsonl`. It is trivially recomputable:
`max(cells, key=lambda L: cells[L]["score"])` with first-max tie-breaking to match
`validate_refusal_directions.py:582`.

### D10 — [MEDIUM] `by_family.*.valid_layers` is recomputed **sorted**; the harness emits it in **row order**
- harness `validate_refusal_directions.py:581` — `ok = [rw["layer"] for rw in fr if rw["valid"]]`,
  i.e. the order of the `for L in layers` loop, i.e. the `--layers` order.
- reconciler `validate_all_outputs.py:863` — `valid = sorted(...)`; same at `:872` for
  `invalid_layers`.

**Failure scenario.** `--layers 20,10,30`. The harness writes `valid_layers: [20, 10]`; the
reconciler expects `[10, 20]` → two spurious `summary != raw` mismatches → the dir goes FAIL for a
non-problem. This is the *same class of bug* the commit was written to fix (the four spurious FAILs
on 720463). Masked today only because the committed run passed an ascending list
(`RUNMETA.args.layers = "0,1,2,…,31"`).

Fix: preserve row order, `valid = [L for L in cell_order if cells[L]["valid"]]`, or sort on both
sides.

### D11 — [MEDIUM] The "1348 values reconciled" headline is inflated ~2.5× by algebraic redundancy, and omits its denominator
I re-ran it: `1348 checked, **778 unchecked**`, WARN (only the missing manifest). The commit note and
claim P7-32's note both quote "1348 summary values recomputed from raw.jsonl, 0 mismatched" with no
denominator — that is 63 % coverage, not 100 %.

Of the 1348, the independent content is much smaller. Per cell there are 20 `exp.put`s
(`:822-852`), but:
- `refusal_base_harmful` and `refusal_base_benign` are the **same two numbers repeated in all 64
  cells** — 128 puts, 2 facts.
- `ablate_specificity`, `induce_specificity`, `induce_gain_ceiling`, `score`,
  `both_gains_positive`, `valid`, and all four `*_gain*` are deterministic functions of the four
  rates and the two baselines already checked.
- Genuinely independent per cell: 4 rates + 2 empty-fractions + 2 counts = **8**, not 20.

Not a correctness bug — but do not cite 1348 as evidence of coverage in the paper or the audit.

### D14b — [MEDIUM] The four McNemar p-values are unchecked although they are fully recomputable
`ablate_p`, `ablate_vs_rand_p`, `induce_p`, `induce_vs_rand_p` are item-paired McNemar tests over
booleans that are all in `raw.jsonl` with an `item` field that pairs them. `expect_refval` never
touches them. A sign or orientation error in `mcnemar_pair` (note `ablate_vs_rand_p` passes
`(ablr, abl)`, so `flip_up`/`flip_down` are labelled backwards relative to the ablate hypothesis —
harmless today because only the two-sided `p` is consumed) would sail straight through the
reconciler. Also unchecked: `induce_eval`, `ablate_scope`, `induce_scope`, and the whole `plan` node.

### D13 — [NOT A DEFECT] `both_gains_positive` vs `valid` is correct
Source of truth `validate_refusal_directions.py:560-562`:
```
both_gains_positive = ab_gain > 0 and in_gain > 0
valid               = ab_gain > 0 and in_gain > 0 and (ab_gain-ab_rand) > 0 and (in_gain-in_rand) > 0
```
Reconciler `validate_all_outputs.py:847-849` reproduces both exactly, including the specificity
conjunct. Verified.

I also checked the float-path risk, since the two sides compute the rates differently
(`np.mean` over a list of bools vs `sum(v)/len(v)`): for n ≤ 2^53 both produce the exact same
float64 rational, so the strict `> 0` comparisons agree bit-for-bit. No hidden mismatch.

One caveat that is a *reporting* problem, not a code problem: `valid` applies a strict `> 0` to a
quantity whose grain on the induce side is 1/10 (D5), so `induce_specificity > 0` means "one of ten
items flipped". That belongs in the summary and in every claim that cites `n_valid`.

Two smaller notes on `expect_refval`:
- Every `exp.put` is gated on `if k in sr` (`:840-841`, `:851-852`). If a field is renamed or dropped
  upstream, its check silently disappears with no warning (the `missing_groups` machinery only fires
  for groups that were *put*). A dropped `valid` field means the verdict stops being reconciled.
- `if not cells: continue` (`:861-862`) silently skips a whole family's roll-up when every cell was
  skipped by the `an arm has no rows` warn at `:817-819`.

---

## 3. `scripts/analyze_rep_predicts_behavior.py` — `--sweep`

### D14 — [HIGH] "L16 0.888 HIGHER than L21's 0.874" is a selected maximum with no paired test
`:93-94` — `best = max(rows, key=auc)`, `best_cv = max(cv, key=auc)`. For clearharm **both are
L16**, i.e. 0.8883 is the argmax over all 32 layers, not a pre-registered readout.

Three problems, all of which cut the same way:
1. **Selection.** Under H0 (equal true AUC across the 11 bidirectionally-validated layers) the
   expected max of 11 correlated estimates exceeds any single one of them. "HIGHER, and the result
   got STRONGER" is exactly what selection manufactures.
2. **No paired test.** The two AUCs come from the **same 86 items** with strongly correlated features
   (adjacent residual layers). A difference of correlated AUCs needs DeLong or a paired
   item-bootstrap. `stats.paired_bootstrap_ci` already exists in this repo and is used by
   `validate_refusal_directions.py:522` — it is not used here. **No AUC in the sweep carries a CI.**
3. **The gap is inside the noise the script itself measured.** ΔAUC = 0.0139. The script's own 5-fold
   spread at L21 is sd 0.055. Neighbouring layers: L16 0.8883, L17 0.8837, L18 0.8819, L19 0.8811 —
   a 0.007 spread across four adjacent layers. The "improvement" is the same order as layer jitter.

RP-04 is marked **VERIFIED** on this.

**Fix.** Report `AUC(L16) − AUC(L21)` with a paired item-bootstrap CI. If the CI straddles 0 — which
it almost certainly does at n=86 — the correct claim is "L16 is *at least as good as* L21 and is
validated in both families", which is still a perfectly good result and does not need the superlative.

### D15 — [HIGH] "cross-validated" is used for two different things twenty lines apart
`:92` — `cv = [x for x in rows if x["p7_valid_both"]]`. **`cv` here means "P7-validated in both
direction families"**, nothing to do with cross-validation. `:94` `best_cv` → the output field
`best_layer_p7_valid`.

The actual 5-fold CV (`cv_auc_at_headline_layer`) is computed **only at `--cv-layer 21`** (`:74-91`),
i.e. **not at L16**. So:
- tick48's headline, "RP-01's caveat RESOLVED at a cross-validated layer (AUC 0.888 > 0.874)",
- RP-04's claim text, "re-anchored on a CROSS-VALIDATED axis",
- and RP-01's rewritten `abstract_block`, "the axis it is read on is not cross-validated",

all describe an **in-sample AUC at a selected layer**. There is no cross-validated 0.888 anywhere in
the repo. Twenty lines above, RP-03's note discusses the real 5-fold number (0.869 ± 0.055) under the
same word. A reader — or a reviewer — will conflate them.

**Fix.** Rename the local to `p7ok`, say "bidirectionally validated" everywhere, and compute the
5-fold at `best_layer_p7_valid` as well as at the historical layer.

### D16 — [MEDIUM] `P7_VALID_BOTH_DECODER` is a hand-copied constant with no provenance check, and a re-calibration run is in flight
`:29`. I verified it is **currently correct**: it equals
`set(existing.valid_layers) & set(clearharm.valid_layers)` from
`outputs/refval_clearharm_20260806_054117_722611/summary.json` = `[13,14,15,16,17,18,19,20,24,28,29]`.

But that summary is machine-readable and on disk, and jobs 724551/724552 (the low-alpha
re-calibration) are in the queue. If the refval verdict moves, `p7_valid_both`,
`n_holm_sig_p7_valid`, `best_layer_p7_valid` and RP-04's whole premise become silently wrong — and
**RP-03/RP-04's machine checks would still pass**, because they compare the sweep JSON to itself
(D24).

Related: `P7_VALID_BOTH_HS` (`:30`) is computed and never used anywhere. Dead code that invites
exactly the indexing confusion the comment above it warns about.

**Fix.** Derive the list from the refval `summary.json`, and record the source run dir in the output
report.

### D17 — [MEDIUM] `--layer` is hs-indexed; `--cv-layer` is decoder-indexed. Same script, no naming distinction.
- `:120` `--layer` default `"22"`, used **directly as a dict key** into `proj[i]["doublespeak"]`
  (`:134`) → an hs row. The figure's y-label hard-codes `"(L21)"` (`:146`).
- `:121` `--cv-layer` default `21`, converted at `:75` with `h = str(hl_dec + 1)` → a decoder layer.
- `--layer` is a `str`; `--cv-layer` is an `int`.

**Failure scenario.** Someone acts on RP-04's recommendation to re-anchor at L16, runs
`--layer 16`, and silently reads **decoder L15** — while the figure is still titled "(L21)". The
sweep path uses the mapping consistently (`:63` `decoder_layer = int(h)-1`, `:65` and `:75` agree);
the single-layer path does not participate in the convention at all.

**Fix.** Rename to `--hs-row`, or take a decoder layer everywhere and convert once. Delete
`P7_VALID_BOTH_HS` or use it.

### D18 — [MEDIUM] The stated fold guarantee is FALSE, and the failure mode writes invalid JSON
`:72-73`: "folds are deterministic (seed 0), stratified by label **so a fold cannot end up
single-class** (which would make AUC undefined)."

The stratifier (`:79-82`) round-robins each class over 5 buckets. If a class has k < 5 members, only
k folds receive it and the remaining 5−k are single-class → skipped at `:86-87`. Simulated:

| n | n_malicious | folds kept | sd |
|---|---|---|---|
| 86 | 32 | 5 | ok |
| 51 | 11 | 5 | ok |
| 40 | 4 | 4 | ok |
| 40 | 2 | 2 | ok |
| **40** | **1** | **1** | **nan** (`np.std([x], ddof=1)`) |

`json.dump` then writes `{"sd": NaN}` — verified: `json.dumps` emits a bare `NaN`, which is **not
valid JSON**; any strict (non-Python) consumer of
`outputs/rep_predicts_behavior_sweep.json` fails to parse the file. If a cohort has zero of one class
all five folds are skipped, `np.mean([])`/`np.std([])` return nan with a RuntimeWarning, and the same
NaN is written.

Safe today only because clearharm n_mal=32 and curated n_mal=11 both give 5 folds. The guarantee is
stated absolutely and is not.

Compounding: the print at `:115` says **"5-fold CV AUC"** regardless of what `n_folds` actually is,
so a degraded run reports itself as a 5-fold.

**Fix.** `n_folds = min(5, min(class counts))`; assert it; emit `None` rather than NaN; print
`n_folds`.

### D19 — [the suspicious condition] `:86` is REDUNDANT, not wrong
```python
if m.all() or (~m).any() == False or m.sum() == 0:
```
Term by term, for a boolean fold-label array `m`:
- `m.all()` → all malicious. **Correct guard.**
- `(~m).any() == False` → "no non-malicious exists" → **all malicious**. *Identical to term 1.* It is
  written in the double-negative form that reads like `(~m).all()` ("all non-malicious"), which is
  what term 3 already checks. Pure duplication in misleading clothing.
- `m.sum() == 0` → all benign. **Correct guard.**

So the condition reduces to `all-malicious OR all-malicious OR all-benign`. It **does** correctly
skip every single-class fold, so it is not a bug. The `== False` against a numpy bool
(`np.True_ == False` → `np.False_`) also evaluates correctly, so no hidden truthiness trap.
Edge case, accidentally correct: an empty fold gives `np.array([]).all() == True`, so it is skipped.

**Verdict: correct but nonsense as written.** Replace with
`if m.sum() == 0 or m.sum() == m.size: continue`.

The real problem is not this line — it is that reaching it silently degrades `n_folds` (D18) and
nothing downstream notices.

### D20 — [NOT A DEFECT] `holm()` is correct
`:40-47`. Verified against a `np.maximum.accumulate(sorted_p * (m - arange(m)))` reference over 3000
random p-vectors with p-values rounded to 1–3 decimals to *force ties*: **0 mismatches**. The
running max reproduces Holm's step-down monotonicity, ties get identical adjusted values (checked:
`[0.02]*4 → [0.08]*4`), and the 0-based `(len(ps) - k)` multiplier is the correct `m − j + 1`.
Hand check: `[0.01, 0.04, 0.03, 0.005] → [0.03, 0.06, 0.06, 0.02]` ✓.

Two scope notes, not bugs, that should be stated where the number is quoted:
- The family is **per cohort** (2 × 32), not the 64 tests actually run. Defensible, but say so.
- The p-values are **one-sided** (`alternative="less"`, `:35`), so the correction inherits a
  directional hypothesis. `n_holm_sig = 20/32` means 20 one-sided tests.

### D21 — [MEDIUM] The sweep output records no provenance
`join()` (`:18-24`) picks `sorted(glob(...))[-1]` — whichever run dir sorts last. The report dict
(`:53-54`, `:95-103`) records the index convention and the P7 list but **never the two source run
dirs**. So `outputs/rep_predicts_behavior_sweep.json` — the file RP-03 and RP-04 are checked against
— does not say what it was computed from, and a new `refproj_clearharm_*` landing on disk silently
changes what those two claims mean. Add `rp`/`rf` paths to `report`.

Minor: `ids = [i for i in proj if i in out]` (`:23`) has no non-degeneracy check; `hs_rows` is read
from `proj[ids[0]]` only (`:58`), so an empty intersection is an `IndexError` rather than a message.
`for hl_dec in (args.cv_layer,):` (`:74`) is a one-iteration loop whose body defines `cv_auc` used
after it — harmless, but it would `NameError` if the tuple were ever emptied.

---

## 4. `scripts/build_claim_audit.py`

### D22 — [LOW] `_dig` list-path support is right for the dotted-key problem, but raises an uncaught exception class
`:121-134`. The motivation (keys like `"0.25"` containing a literal dot) is real and the list form
solves it. Two rough edges:

- `:130-131` `if isinstance(cur, list): cur = cur[int(part)]`. `int("auc")` raises **`ValueError`**,
  which is in **neither** caller's except tuple — `chk_summary:165` and `chk_json_path:300` both
  catch only `(KeyError, IndexError, TypeError)`.
  It does not crash the build: the harness's blanket `except Exception` at `:1097` converts it to
  `(False, "json_path raised ValueError: …")`. But two consequences remain:
  **(a)** the diagnostic says "raised ValueError" instead of the intended "path ABSENT";
  **(b)** an `expect_present=False` check **false-positives**. Concretely
  `dict(kind="json_path", path=["cohorts","clearharm","layers","nope"], expect_present=False)` should
  pass (the path genuinely is absent) and instead reports CHECK-FAIL, because the ValueError never
  reaches the `return (c.get("expect_present") is False)` line. Add `ValueError` to both tuples.
- `:128-129` `if part == "": continue` silently normalises `"a..b"` → `"a.b"` and makes an
  empty-string dict key unaddressable. Cosmetic.
- `float(got)` at `:168` and `:311` sits **outside** the try. A JSON `null` (e.g. `separation_fit`
  for a layer with no sidecar `.json` — refval emits exactly that, `validate_refusal_directions.py:411-412`)
  gives `float(None)` → `TypeError` → again only the blanket handler, reported as "raised TypeError"
  instead of a clean "value is null".

### D23 — [LOW, correct as designed] The boolean-identity comparison is right
`:309-310` `if isinstance(exp, bool) or isinstance(got, bool): return got is exp`. `json.load`
returns the real `True`/`False` singletons, so `is` is safe. The stated purpose — stop `expect=False`
being satisfied by `0` / `0.0` — is achieved.

Two things to know before relying on it:
- It is strict in **both** directions: a check written `expect=1` against a stored `true` now FAILS.
  Intended, but it is a behaviour change; I grepped CLAIMS and found no such check today.
- It does **not** guard `chk_summary`, which still does `abs(float(got) - float(expect))` (`:168`),
  where `float(False) == float(0)` conflation survives. If this is a policy, apply it in both
  checkers.

### D24 — [MEDIUM] RP-04's single machine check cannot fail on the claim's actual content
`:930-931`. RP-04's only check is
`cohorts.clearharm.best_layer_p7_valid.decoder_layer == 16`. That asserts **the argmax is 16** —
which is precisely the selection step that makes the claim doubtful (D14). It does not check 0.888,
does not check 0.874, and there is no machine expression of "HIGHER than". The claim's load-bearing
verb has zero checks, and it renders as **VERIFIED, 1/1 ok**.

The same pattern in RP-03 (`:906-919`): the claim sentence is "AUC stable **0.844–0.884 across
decoder L17–L31**", but the JSON's `auc_range_all` is the range over **all 32** layers
(verified: `[0.4896, 0.8883]`), and **no field and no check holds the L17–L31 range**. I verified the
range by hand — 0.8438–0.8837, so the sentence is true — but nothing in the audit would catch it
becoming false. Its three checks assert `n_holm_sig_p7_valid`, the best AUC, and `curated
n_holm_sig == 0`; none of them is the stability sentence.

**Fix.** Emit `auc_range_p7_valid` / `auc_range_L17_L31` from the sweep and check it. For RP-04, emit
a paired-bootstrap CI on `AUC(L16) − AUC(L21)` and check the CI, not the point estimate.

### D25 — [LOW] The "negative control" tests the comparator, not the claim
RP-03 and RP-04 both check `outputs/rep_predicts_behavior_sweep.json` — a file the same script wrote
in the same tick. That is a legitimate regression lock. But tick48's "Negative-controlled (CHECK-FAIL
RP-04 on a perturbed expectation)" only demonstrates that the *comparator* works; perturbing an
expectation must fail. A real negative control perturbs the **data**: shuffle `mal` and confirm AUC
collapses to ~0.5 and `n_holm_sig` → 0. That costs no GPU and is not present. The same applies to
P7-32's control (perturbing `n_valid` to 99).

---

## Recommended order of work

1. **D1** — decide and document what the `existing` induce arm actually measures, before any further
   claim revision leans on a family split. This one changes the interpretation of four claims.
2. **D14 / D15** — put a paired-bootstrap CI on ΔAUC(L16, L21) and stop calling a family-validated
   layer "cross-validated". RP-04 should be downgraded from VERIFIED until one or the other lands.
3. **D12 / D3** — write `induce_eval`, `harmless_holdout`, `n_harmless_fit`, `n_harmless_eval` into
   `plan`, and make `expect_refval` fail on a contaminated induce arm. Until then the refval
   disjointness check is decoration.
4. **D9 / D10** — reconcile `best_layer`; fix the sorted-vs-row-order roll-up before anyone runs a
   non-ascending `--layers`.
5. **D16 / D18 / D17** — derive `P7_VALID_BOTH_DECODER` from disk, bound `n_folds`, unify the layer
   index convention.
6. Cosmetic / latent: D2, D4, D5, D6, D7, D8, D11, D19, D21, D22, D24, D25.
