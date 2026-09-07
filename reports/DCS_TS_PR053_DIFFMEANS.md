# DCS-PR-053 — thesis-scale difference-in-means: the remapping axis and the concept-identity axis

**Preregistration**: `configs/dcs_ts_pr053.json` (FROZEN 2026-09-07), loaded and enforced at runtime.
**Analyzer**: `scripts/dcs_ts_pr053_diffmeans.py` (this run: `--mutate`, CPU only, no GPU, no new forward passes).
**Extraction**: shared with `PR-048` — `outputs/boombness/extract_boombness/ts116m_full_{button,basket}_{bomb,knife,gun}_*`, six runs, all with `DONE.json`, all six `bank_rows_sha16` verified against the pin before a single row was used.
**Population**: 113 analysed domains (116 minus the three preregistered whole-population exclusions `restaurant_kitchen`, `subway_station`, `school_campus`), split 67 train / 23 validation / 23 test.

---

## 0. The one-paragraph answer

The estimator works, the gate it depends on holds exactly, and the primary contrast is enormous:
`v_bomb_specific` separates cell-C bomb from the cell-C hard negatives at **band-mean AUROC 0.9764**
on the 23 untouched test domains, 23/23 domains above chance, far above the measured surface floor
of 0.7479. **But the separability claim fails.** The same residual axis is *not* weak on remapping:
it separates `C_bomb` from the shared cell-A baseline at **0.8236**, and it separates
`C_knife`/`C_gun` from cell A at **0.1691**, i.e. **0.8309 polarity-free** — both above the same
surface floor that the identity contrast is judged against. **CLAIM B (remapping and identity are
separable axes) is UNSUPPORTED on this evidence**: residualising `v_bomb` against the mean of
`v_knife` and `v_gun` produces one axis that does both jobs, not a second axis that does only
identity. Reporting C without D would have read as a clean positive; that is exactly the error the
raw-vs-residual framing exists to avoid, and the frozen design caught it.

A second, separate caution on the primary: its domain-level permutation p is **0.0454** — under
alpha, but only just, and it does **not** survive the preregistered Holm correction across the
PRIMARY family unless `PR-048` returns a p below 0.0454 (see §5.3).

---

## 1. V2 — THE BLOCKING GATE: does the cell-A term cancel exactly?

The whole estimator rests on `v_bomb − v_knife = mean[h(C_bomb)] − mean[h(C_knife)]`, which is true
only if the two cell-A terms are the *same prompts*. Verified inside the **analysed** population
(113 domains), at matched `prompt_id`, per codeword and per dose:

| codeword | n_examples | per-arm rows | matched prompt_id | byte-identical `full_prompt` | byte-identical `final_query_text` | domains | result |
|---|---|---|---|---|---|---|---|
| button | 0 | 226 / 226 / 226 | 226 / 226 | **226 / 226** | 226 / 226 | 113 | PASS |
| button | 4 | 1130 / 1130 / 1130 | 1130 / 1130 | **1130 / 1130** | 1130 / 1130 | 113 | PASS |
| button | 8 | 452 / 452 / 452 | 452 / 452 | **452 / 452** | 452 / 452 | 113 | PASS |
| basket | 0 | 226 / 226 / 226 | 226 / 226 | **226 / 226** | 226 / 226 | 113 | PASS |
| basket | 4 | 1130 / 1130 / 1130 | 1130 / 1130 | **1130 / 1130** | 1130 / 1130 | 113 | PASS |
| basket | 8 | 452 / 452 / 452 | 452 / 452 | **452 / 452** | 452 / 452 | 113 | PASS |

**V2 PASSES: 3616 / 3616 byte-identical, denominator = the union of prompt_ids across the three
arms (not the intersection), and the intersection equals the union in every cell.** Every analysed
cell-A row carries `condition == benign_literal`; a row that did not would have refused.

**Numerical corollary, measured not assumed.** Byte-identical text is only half of it: the three
arms were extracted in three *different runs*. At matched `prompt_id`, over 400 prompt_ids per
codeword, the cell-A hidden states agree to **max |diff| = 0.000e+00** on both arms. The A term
cancels in arithmetic, not merely in text. This is the single thing the ts116m rebuild bought, and
it is the reason the old §46.1 / C-060 nuisance term (a partially shared cell A across independently
generated corpora) does not exist here.

---

## 2. V1 — POWER for an AUROC estimator at n = 23 test domains

Neither `PR-048`'s 3-way *accuracy* power nor `PR-049`'s 2-way power transfers: different estimand,
different between-domain variance, and a fixed difference-in-means direction has no fitting variance
at all. What transfers is the design — 23 domains, domain as the independence unit, alpha = 0.05,
n_perm = 10000.

**Attainable floors, stated before any p was computed**

* exact two-sided sign test, n = 23: floor = 2 / 2²³ = **2.384e-07**; critical k = **17/23**.
* group permutation, B = 10000: floor = 1 / (B+1) = **9.999e-05**.
* Both floors are far below alpha, so at this n **the floor is not the binding constraint** — which
  is a change from the old 6-domain instrument, whose 0.03125 floor made any Holm family of size
  ≥ 2 uninformative by construction.

**MDE across a bracket of ASSUMED between-domain SDs** (two-sided alpha = 0.05, 80% power, normal
approximation for the domain-mean). *The SD is an assumption, not a measurement*: no AUROC SD for
this estimand existed before the run. 0.1406 is `power.between_domain_sd_projected`, which is an
*accuracy* SD from six old domains with 5 df; 0.3439 is its 95% upper bound.

| assumed SD | SE | MDE (Δ) | MDE (AUROC) | power @ 0.60 | power @ the 0.7479 floor | MDE clears the floor |
|---|---|---|---|---|---|---|
| 0.0500 | 0.0104 | 0.0292 | 0.5292 | 1.000 | 1.000 | yes |
| 0.0750 | 0.0156 | 0.0438 | 0.5438 | 1.000 | 1.000 | yes |
| 0.1000 | 0.0209 | 0.0584 | 0.5584 | 0.998 | 1.000 | yes |
| 0.1406 *(prereg projection)* | 0.0293 | 0.0821 | 0.5821 | 0.927 | 1.000 | yes |
| 0.2000 | 0.0417 | 0.1168 | 0.6168 | 0.669 | 1.000 | yes |
| 0.2500 | 0.0521 | 0.1460 | 0.6460 | 0.483 | 0.997 | yes |
| 0.3439 *(95% upper bound)* | 0.0717 | 0.2009 | 0.7009 | 0.286 | 0.933 | yes |

Exact sign-test power at per-domain sign rate q: q=0.6 → 0.124, q=0.7 → 0.440, q=0.8 → 0.840,
q=0.9 → 0.994. The sign arm is the weak one: it needs 17 of 23 domains to point the same way.

**REALISED between-domain SD (measured after the run, on the primary): 0.0347**, giving
SE = 0.0072 and a realised MDE of **0.0203 AUROC** — the most favourable point of the entire
bracket.

**V1 VERDICT: the primary is ADEQUATELY POWERED.** Across the whole assumed bracket — including the
pessimistic 95% upper bound — the MDE stays below the delta needed to clear the measured surface
floor (0.2479), and at the realised SD the design resolves differences of 0.02 AUROC. The
preregistered `cannot_answer` condition ("power inadequate at the realised between-domain SD") does
**not** fire. Two caveats that power arithmetic does not cover, and which do bind, are in §5.3 and
§8.

---

## 3. The estimator, and the discipline it was run under

```
v_c(l)             = mean over the 67 TRAIN domains of [ h_l(C_c, f) − h_l(A_shared, f) ]   (paired on family_id)
v_remap(l)         = v_bomb(l)
v_bomb_specific(l) = v_bomb(l) − mean( v_knife(l), v_gun(l) )        (no club — prereg `_no_club`)
```

* **TRAIN only.** Directions and z-standardisation constants come from the 67 train domains.
  Validation and test never enter either. A fit set that intersects the evaluation set refuses
  (`primary.void`), and that refusal was exercised — see §9.
* **No layer selection, no hyperparameter.** Every layer 6–14 is reported; none is picked. The
  C-070 saturated-selection failure and the test-selection FPR inflation (0.4433 vs 0.0467) are
  structurally impossible here because there is nothing to select.
* **Domain is the independence unit everywhere.** Group permutation relabels concepts *within
  train domains*; row-level permutation (measured FPR 0.2000) is not implemented anywhere in the
  file.
* **D1 fixed, not inherited.** `dcs_diffmeans_directions.transfer()` passes *all* domains of the
  fit arm to `_z`, leaking the held-out domain into the standardisation constants. Here `_zconst`
  takes an explicit train set and every call site passes the fit arm's train domains. (AUROC is
  invariant to a positive per-layer affine map, so D1 never moved an AUROC — it moved every printed
  z-projection, which is what a reader compares across arms.) `scripts/dcs_diffmeans_directions.py`
  was not edited; `auroc`, `std_diff`, `unit`, `project` and `band` are imported from it.
* **Missing rows.** button arms: 0 missing. basket arms: exactly 30 missing each, **all
  `school_campus`** — the C-075 `basketball` refusal, a preregistered whole-population exclusion, so
  they are explained (R-108). A single missing row outside the exclusions refuses; that refusal was
  exercised.

---

## 4. PRIMARY

> AUROC of proj(h, `v_bomb_specific`) separating `C_bomb` from {`C_knife`, `C_gun`}, domain-mean over
> the 23 untouched TEST domains, `button`, `semantic_one_word`, `n_examples = 4`.

| quantity | value |
|---|---|
| band-mean AUROC (layers 6–14), domain-mean over 23 test domains | **0.9764** |
| 95% CI over domains | [0.9622, 0.9906] |
| between-domain SD | 0.0347 |
| Cohen's d (band, pooled held-out rows) | 3.03 |
| per-domain sign | **23 / 23** above chance |
| exact two-sided sign test | p = 2.384e-07, **attainable floor 2.384e-07 — the p IS the floor** |
| domain-level group permutation, B = 10000 | **p = 0.0454** [floor 9.999e-05], 453 exceedances |
| permutation null | mean 0.4943, sd 0.4090, q95 0.9757 |
| chance | 0.5 |
| **measured surface floor (the bar)** | **0.7479 macro-AUROC** (R-106) |
| clears the surface floor | **yes**, by 0.2285 |

**Floor comparison, as the preregistration requires.** The bar is not chance. R-106's register/
surface classifier reaches 0.7479 macro-AUROC on this corpus without reading a representation.
0.9764 clears it by 0.2285, and the *lowest* of the 23 per-domain values (0.883) also clears it.

**Two honest qualifications on the p-values, both of which the numbers above already show:**

1. **The sign-test p equals its own attainable floor.** 23/23 is the maximum the design can
   produce; 2.384e-07 is what 23/23 *always* returns. It is a real observation (every domain points
   the same way) but it is not a measurement of *how* significant the result is, and it must not be
   quoted as one — this project has published a headline p that was its own floor before.
2. **The permutation p is 0.0454, and the null is bimodal (sd 0.409, q95 0.9757).** This is not a
   defect of the implementation, it is the shape of the question. A relabelled draw produces a
   *different concept contrast of the same family* — with 67 domains and 3 concepts the permuted
   axis is `Σ_c ε_c·v_c` with `ε_c ~ ±4`, so roughly 4.5% of draws happen to be bomb-favouring and
   then separate bomb about as well as the real axis does. The permutation therefore asks the hard
   question — *is bomb special beyond an arbitrary concept contrast?* — and the answer is a
   marginal yes: **453 of 10000 arbitrary relabellings match or beat the observed 0.9764.** The
   effect size is huge; the *label-permutation evidence that it is specifically about bomb* is thin.

**PRIMARY VERDICT: the statistic is significant at the preregistered alpha (permutation p = 0.0454
< 0.05, sign test 23/23) and clears the measured surface floor by a wide margin — but see §5.3, the
Holm correction across the PRIMARY family is not satisfied on the evidence currently available.**

### 4.1 Per-layer profile — every layer reported, none selected

| contrast | L6 | L7 | L8 | L9 | L10 | L11 | L12 | L13 | L14 | band |
|---|---|---|---|---|---|---|---|---|---|---|
| **C** `v_spec`: C_bomb vs {C_kn, C_gun} | 0.9639 | 0.9687 | 0.9735 | 0.9746 | 0.9793 | 0.9809 | 0.9824 | 0.9830 | 0.9813 | **0.9764** |
| **D** `v_spec`: {C_kn, C_gun} vs A | 0.1428 | 0.1343 | 0.1598 | 0.1859 | 0.1626 | 0.1807 | 0.1791 | 0.1915 | 0.1852 | **0.1691** |
| `v_spec`: C_bomb vs A | 0.7070 | 0.7209 | 0.8552 | 0.8665 | 0.8261 | 0.8587 | 0.8370 | 0.8704 | 0.8704 | **0.8236** |
| **A** `v_bomb`: C_bomb vs A | 0.9913 | 0.9896 | 0.9983 | 1.0000 | 0.9996 | 0.9991 | 0.9987 | 0.9987 | 0.9970 | **0.9969** |
| **B** `v_bomb`: C_bomb vs {C_kn, C_gun} | 0.8167 | 0.8174 | 0.9263 | 0.9457 | 0.9054 | 0.8909 | 0.8833 | 0.8998 | 0.8850 | **0.8856** |

Cohen's d for the primary is flat across the band (2.81 → 3.15). The profile is monotone-ish and
featureless: there is no layer at which the identity contrast switches on, and nothing here supports
a localisation claim.

Mean z-projections on `v_bomb_specific` (units of the train cell-A pooled spread, layer 6 → 14):
`C_bomb` +0.41…+1.20, `A_shared` −0.27…−0.24, `C_gun` −1.19…−0.93, `C_knife` −1.94…−1.80. The
baseline sits *between* bomb and the negatives — which is the geometry that makes D fail.

---

## 5. SECONDARY — the six questions of mandate 9.1, each with a number

All on `button`, `semantic_one_word`, dose 4, 23 test domains, directions from train only.

| # | question | statistic | 95% CI | per-domain sign | permutation p [floor 9.999e-05] | null mean |
|---|---|---|---|---|---|---|
| **A** | does `v_bomb` separate C_bomb from A? *(the remapping axis)* | **0.9969** | [0.9920, 1.0018] | 23/23 | p < 9.999e-05 (0 exceedances) | 0.8794 ⚠ |
| **B** | does `v_bomb` separate C_bomb from C_knife/C_gun? *(identity, raw axis)* | **0.8856** | [0.8348, 0.9365] | 22/23 | p < 9.999e-05 (0 exceedances) | 0.2230 ⚠ |
| **C** | does `v_bomb_specific` separate C_bomb from the hard negatives? | **0.9764** | [0.9622, 0.9906] | 23/23 | p = 0.0454 (453 exceedances) | 0.4943 ✓ |
| **D** | does `v_bomb_specific` stay **WEAK** on generic C-vs-A remapping? | **0.1691** (= **0.8309** polarity-free) | [0.0982, 0.2400] | 2/23 | p = 0.8442 (8442 exceedances) | 0.5065 ✓ |
| — | companion: `v_bomb_specific`, pooled C vs A | 0.3873 | [0.3207, 0.4539] | 4/23 | descriptive, no p | — |
| **E** | does it transfer button → basket by ranking? | **0.9747** | — | 23/23 | p = 0.0437 | — |
| **F** | does the n_examples = 0 null fire exactly? | **exactly 0.5000**, ‖v_bomb_specific‖ = 0.0 | — | 0/23 | — | — |

⚠ **Which of these p-values are calibrated, stated as a property of the null and not as an excuse.**
The permutation relabels *which concept plays the bomb role* in each train domain. Writing
`u_j = Dm_j` and `w_j = 1.5·Dm_j − 0.5·(Dm_bomb + Dm_knife + Dm_gun)`:

* mean over j of `w_j` is **exactly zero**, so a permuted `v_bomb_specific` is a random residual
  axis with no expected remapping component. **C and D have properly centred nulls** (0.4943 and
  0.5065) — the primary and its separability partner are the two contrasts the instrument tests
  correctly.
* mean over j of `u_j` is the **grand mean** of the three C−A differences, which is not zero. So a
  permuted `v_bomb` still separates C from A (null mean 0.8794) and still anti-favours bomb against
  the negatives (null mean 0.2230). **A's and B's permutation p-values are not calibrated tests of
  their own contrasts** and are not quoted as evidence; the instruments for A and B are the effect
  size and the exact sign test.

**A — the remapping axis is real and very strong.** 0.9969, 23/23 domains, essentially at ceiling
in layers 8–14. Whatever `v_bomb` is, it separates a doublespeak-installed prompt from its
byte-identical benign baseline almost perfectly.

**B — the raw axis DOES read identity here, and that reverses the old finding.** The
preregistration records the old work at ~0.574 ("it does not"). At thesis scale on the aligned bank
`v_bomb` separates C_bomb from the hard negatives at **0.8856** with 22/23 domains. The most likely
reason is exactly the thing V2 verified: on ts116m the cell-A term is byte-identical across arms and
cancels, so `v_bomb` is a clean C_bomb − A contrast rather than a difference between two
independently generated corpora. **This should be read as a correction to the old estimate, not as a
new mechanism.**

**C and D together — see §6. This is the finding.**

**E — transfer is essentially perfect.** Directions fitted on `button` TRAIN only, scored on
`basket` TEST: band-mean AUROC **0.9747** (own-arm `basket` fit: 0.9768), 23/23 domains, and the
Spearman rank correlation of the 23 per-domain AUROCs between the transferred and own-arm
directions is **ρ = 0.9921**. The axis is not lexical to the codeword. ⚠ The two arms are not
independent samples — they share domains, harm pools and preamble text — so this is a lexical
replication, not a second experiment.

**F — the null fires exactly.** At `n_examples = 0` cells A and C are the same prompt, so
‖`v_bomb_specific`‖ = **0.0000e+00** (ratio to the dose-4 norm 1.6872: **0.000e+00**) and every
contrast is **exactly 0.5000** — A, B, C and D all 0.5000, 0/23 domains above chance. Bitwise zero,
not "approximately". ⚠ Per `nulls_required` N1 / C-081 this is **DEGENERATE BY CONSTRUCTION**: with
no demonstrations the three concept arms are the same prompt, so this is a pipeline sanity check and
*not* evidence about the model. "The signal localises entirely to the demonstration block" does not
follow from it.

### 5.3 Multiplicity

**SECONDARY family, Holm within the family** (A, B, C, D, E):

| q | p | p_Holm | reject at 0.05 |
|---|---|---|---|
| A | 9.999e-05 | 5.000e-04 | yes |
| B | 9.999e-05 | 5.000e-04 | yes |
| E | 4.370e-02 | 1.311e-01 | **no** |
| C | 4.540e-02 | 1.311e-01 | **no** |
| D | 8.442e-01 | 8.442e-01 | no |

**PRIMARY family** = {`PR-048` 3-way probe, `PR-053` identity AUROC}, Holm at family-wise 0.05.
**`PR-048` has not been run** — there is no result file under `outputs/dcs_ts/` — so the family
cannot be completed. The two branches are:

* if `PR-048`'s p < 0.0454, then `PR-053` is the *larger* of the two and its Holm-adjusted p is
  0.0454 → **rejects**;
* if `PR-048`'s p > 0.0454, then `PR-053` is the *smaller* and needs p < 0.025 → **does not
  reject** (worst-case adjusted p = 0.0908).

**So the primary's confirmatory status is contingent on a result that does not yet exist.** The
effect size and the floor comparison are not contingent on it; the *p* is.

---

## 6. SEPARABILITY — CLAIM B needs C **and** D

A direction that discriminates identity *and* remapping equally well is one axis doing both, not a
separate axis. D is reported here as prominently as C, and it is judged by the same two instruments
C is judged by: its own domain-level permutation and the same measured surface floor.

| | value | above the 0.7479 surface floor? |
|---|---|---|
| **C** — identity: `v_bomb_specific`, C_bomb vs {C_knife, C_gun} | **0.9764** (Δ = +0.4764) | **yes** |
| **D** — generic remapping: `v_bomb_specific`, {C_knife, C_gun} vs A | **0.1691**, polarity-free **0.8309** (Δ = −0.3309) | **yes** |
| — the same residual axis, C_bomb vs A | **0.8236** | **yes** |
| — the same residual axis, pooled C vs A | 0.3873 (polarity-free 0.6127) | no |
| B — raw axis identity | 0.8856 (Δ = +0.3856) | yes |
| A — raw axis remapping | 0.9969 (Δ = +0.4969) | yes |

|D| / |C| = **0.695**. Per-domain, D is below chance in **21 of 23** domains (values 0.000 → 0.589),
so the reversal is systematic, not an average over a mixture.

**AUROC is a directed statistic: 0.169 and 0.831 are the same amount of discrimination with opposite
polarity, and "stays weak" is a claim about the amount.** Two independent readings of the same
failure:

1. `C_knife`/`C_gun` project *far below* the shared baseline on the residual axis (mean z −1.9 and
   −1.0 against A's −0.27). Part of this is arithmetic — `v_bomb_specific` contains
   `−0.5(v_knife + v_gun)` by construction — and that is precisely the point: the construction that
   is supposed to remove remapping instead installs a remapping-sensitive term with the sign flipped.
2. The reading that is *not* by construction: `C_bomb` vs A **on the residual axis** is **0.8236**.
   Removing the mean of the two negatives did not remove bomb's own C-vs-A signal. A pure identity
   axis would put `C_bomb` and A at the same place; this one separates them well above the surface
   floor.

**CLAIM B (a remapping axis and a concept-identity axis exist as separable directions) is
UNSUPPORTED on this evidence.** It is not "cannot answer": the design is adequately powered (§2),
the gate it depends on is exact (§1), the primary contrast is unambiguous, and D's departure from
chance is large, systematic across domains, replicated at both doses, on both codewords and on
validation as well as test. What the evidence supports is **one axis that carries both remapping and
concept identity**, with the residualisation changing the mixture but not decomposing it.

---

## 7. Replication and specification curve

Doses are separate preregistered cells and are never pooled into one p-value.

| cell | C (identity) | D (remapping, directed) | A | B | sign(C) |
|---|---|---|---|---|---|
| button, n4 *(primary)* | 0.9764 | 0.1691 | 0.9969 | 0.8856 | 23/23 |
| button, n8 | 0.9881 | 0.1410 | 0.9985 | 0.9346 | 23/23 |
| button, n4, **validation** | 0.9750 | 0.0820 | 0.9982 | 0.8349 | 23/23 |
| basket, n4 | 0.9768 | 0.1728 | 0.9981 | 0.9300 | 23/23 |
| basket, n8 | 0.9887 | 0.1437 | 0.9997 | 0.9543 | 23/23 |
| basket, n4, **validation** | 0.9747 | 0.1200 | 0.9997 | 0.9245 | 23/23 |
| **transfer** button→basket, n4 | 0.9747 | 0.1805 | 0.9967 | 0.8940 | 23/23 |
| button, n0 **NULL** | **0.5000** | **0.5000** | **0.5000** | **0.5000** | 0/23 |

Nothing here moves. C sits in [0.9747, 0.9887] across every cell and D in [0.082, 0.181] — the
separability failure replicates everywhere the primary does. Validation is reported because it was
computed, not because anything was selected on it: this analyzer has no selection step at all.

---

## 8. Controls, nulls and the mutation harness

**Random-direction reference (200 draws, the negative control for the readout itself)**: mean
**0.4937**, sd 0.0646, q99.5 0.6441; the observed 0.9764 is exceeded by **0 / 200** random axes.
*(The first version of this control drew a single random direction, got 0.4112, and went red.
Correctly — one draw is not a distribution. It is now the whole distribution, and its mean is at
chance.)*

**Mutation harness** — `9 / 9 mutations turned a check RED; 13 / 13 cases behaved as declared`
(four of the thirteen are GREEN-by-design controls):

| mutation | result | how it failed |
|---|---|---|
| `bank_rows_sha16` pin corrupted | **RED** | run/pin mismatch, refuses before any row is read |
| `read_site.position` pin corrupted | **RED** | run position ≠ preregistered |
| a cache row missing from a **non-excluded** domain | **RED** | R-108 rule: unexplained shrinkage of the population |
| a cache row missing from an **excluded** domain | GREEN *(by design)* | correctly tolerated — the 30 basket `school_campus` rows |
| one cell-A prompt byte-flipped | **RED** | V2 fails; the estimator's premise is checked, not assumed |
| selecting on `condition` instead of `cell` (A-039) | **RED** | binds zero rows and refuses |
| permutation over an empty null | **RED** | raises rather than returning a number |
| sign test over zero domains | **RED** | raises |
| z-standardisation over zero train cell-A rows | **RED** | raises (a silently-identity z-map is D1 in disguise) |
| directions fitted on the evaluation domains | **RED** | `primary.void`; refuses to compute the statistic |
| zero exceedances print `p < 1/(B+1)` | GREEN *(control)* | never a bare number at the floor |
| random direction lands at chance | GREEN *(control)* | 0.4937 over 200 draws |
| batch AUROC == the reused scalar AUROC | GREEN *(control)* | agree to 1e-12 |

Analyzer selftest (no data required): **12 / 12** guards reachable.

---

## 9. What this does not show

1. **A direction is not a cause.** This is decodability. No knockout, no steering, no ablation was
   run. A perfect readout is compatible with the model not using the axis at all.
2. **The permutation instrument is weak for the primary even though the effect is huge** (453/10000
   arbitrary relabellings match it). With three concepts there is a small space of label maps, and
   this is a property of the design, not of the implementation.
3. **A and B carry no calibrated p** (their nulls are structurally off-centre; §5). Their evidence
   is effect size plus the sign test.
4. **One model** (Llama-3.1-8B-Instruct, by decision — Qwen3-14B is absent from the caches), **one
   read site** (`codeword_last`), **one channel** (`semantic_one_word`), **one band** (L6–14).
   `basket` is a lexical replication, not an independent sample.
5. **Register is a live nuisance and length is not** (prereg `_register_asymmetry`, C-084): bomb
   hedges at 14.1% against knife 0.2%. That is why the bar is the 0.7479 measured surface floor and
   not chance — and it is also why the D failure matters, since a register-carrying axis would
   separate C from A exactly as D shows it does.
6. **Non-installing domains are included** (mandate §15). Installation is a stratification variable
   and a stated descriptive limit, never a post-hoc filter.
7. **`PR-048` is missing**, so the PRIMARY family's Holm correction cannot be completed (§5.3).

---

## 10. Reproduction

```
python3 scripts/dcs_ts_pr053_diffmeans.py --selftest         # guards, no data
python3 scripts/dcs_ts_pr053_diffmeans.py --v1-v2-only       # the two blocking items, banks only
python3 scripts/dcs_ts_pr053_diffmeans.py --mutate           # the full run reported here
```

The run reported here read the six `ts116m_full_*` caches directly (no derived-array cache), with
every run re-verified against the preregistration first. Preregistration state is unchanged: this
report does not edit `configs/dcs_ts_pr053.json`, so `pre_extraction_checklist` V1 and V2 still read
`done: false` on disk. **V1 and V2 are answered here — V2 PASSES 3616/3616 and V1 concludes
ADEQUATELY POWERED — and the config's checklist should be closed by whoever owns the freeze, not by
the analyzer that answers it.**
