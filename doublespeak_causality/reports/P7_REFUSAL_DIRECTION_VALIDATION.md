# P7 — Generation-validating the per-layer refusal directions

**Status: ✅ COMPLETE, all 32 layers.** Three runs: `720463` (840 rows) = the ablate arm;
**`721957` (630 rows) = the corrected bidirectional re-run** of the headline layers; and
**`722611` (3870 rows) = the full 32-layer sweep** (§4c), which reconciles at 1348 values / 0 mismatched.

**Verdict: L9 is NOT a refusal axis. It fails BOTH arms under BOTH independently-fit direction families —
ablating it does not reduce refusal, and adding it to benign prompts induces zero refusal against a full
+1.000 of headroom. L16 and L18 validate strongly and unambiguously in both families; L18, the direction
every downstream behavioral arm uses, is the strongest. Across all 32 layers, only **11 validate in both
families (L13-L20, L24, L28, L29)**; L0-L12 fail in both without exception. Of the layers carrying
published claims, **only L18 is in that cross-validated set** - L21, L22 and L30 each validate in exactly
one family (§4c).**

Run dirs: `outputs/refval_clearharm_20260806_033340_720463` (ablate; its induce arm is defective, §5),
`outputs/refval_clearharm_20260806_051728_721957` (**corrected headline layers - cite this one**), and
`outputs/refval_clearharm_20260806_054117_722611` (**full 32-layer sweep**).

---

## 1. Why this run existed

`outputs/refusal_alllayers/` ships 32 `refusal_direction_llama_L*.pt` whose `.json` files carry **no
`validation` key**. They were built without `--validate`, so the only number they ship is `separation` —
which is **tautologically ≥ 0**, being the fit objective evaluated on the fit set. Every per-layer refusal
claim in the project, including the calibrated depth-localization result, rested on axes that had never
been shown to *do* anything.

The specific risk, recorded before the run: the depth claim is *"the refusal decision is read mid-late
(L22 significant) and NOT early (L9 ns)"*. **If the L9 direction is not a valid refusal direction then
"L9 ns" is uninformative** — you cannot conclude refusal is absent early by injecting something that
isn't refusal — and the contrast that gives the depth claim its force disappears.

## 2. Design

Per (family, layer), 20 held-out ClearHarm items, `max_new=64`, keyword refusal judge shared with
`phase_behav_refusal` and `build_refusal_direction_llama`:

| arm | prompts | intervention | want |
|---|---|---|---|
| `ablate` | harmful (`direct`) | project the axis out at **all layers**, α=1.0 | refusal **down** |
| `ablate_rand` | harmful | same, norm-matched **random** direction | no change |
| `induce` | see §5 | add the axis at layer L | refusal **up** |
| `induce_rand` | see §5 | same, norm-matched random | no change |

`ablate_specific = (base − ablate) − (base − ablate_rand)`. **A direction whose random control moves the
outcome just as much has demonstrated nothing**, which is why the specificity contrast — not the raw
drop — is the reported quantity.

Two **independent** direction families:
- **`existing`** — the shipped vectors, fit on `pair_carrot_bomb`. This re-validates what the paper cites.
- **`clearharm`** — a **refit from scratch** on a ClearHarm-native contrast (positive = `direct` over the
  fit split; negative = `HARMLESS_INSTRUCTIONS`). Refit vectors are written into this run's dir;
  `outputs/refusal_alllayers/` is never touched.

## 3. Result — the ablate arm

`base_harmful` refusal = **0.950**. n = 20 per cell, so **one item = 0.05**.

| family | L9 | L16 | L18 | L22 | L28 |
|---|---|---|---|---|---|
| `existing` (carrot/bomb fit) | **−0.050** ✗ | +0.450 | **+0.600** | +0.250 | +0.250 |
| `clearharm` (native refit) | **−0.100** ✗ | +0.350 | **+0.900** | +0.450 | +0.300 |

Raw rates behind the two extremes:
- **L9 `existing`**: ablate 1.00 vs random 0.95 vs base 0.95 — ablation moved refusal **up**, i.e. nothing.
- **L18 `clearharm`**: ablate **0.05** vs random 0.95 vs base 0.95 — ablation removed refusal almost
  entirely while the norm-matched control did nothing.

**L9 is the only failure, and it fails in both families.**

## 4. Reading — this strengthens the depth claim rather than undermining it

The feared outcome was "L9's direction is invalid, so 'L9 ns' proves nothing." What actually happened is
better: **L9 fails under two independently-fit directions** — the original carrot/bomb fit *and* a
ClearHarm-native refit built from different data by a different recipe. Two independent fits failing at
the same layer, while both succeed at L16–L28, is not a measurement accident.

So the defensible claim is **not** "we injected at L9 and nothing happened" (uninformative) but:

> **No linearly-decodable refusal axis exists at L9.** Refusal becomes linearly available at **L13** and
> is strongest around L15-L18, remaining available through L20.

*(This sentence originally read "becomes linearly available at L16", which was an artifact of the headline
layer set containing no layer between 9 and 16. The full 32-layer sweep, §4c, puts the boundary at
**L13** and shows L0-L12 failing in both families without exception.)*

That is a positive claim about depth, and it is the framing the paper should use. **The prose "L9 ns"
should be replaced wherever it appears.**

Secondary but load-bearing: **L18 validates strongly in both families (+0.600 / +0.900)**. Every
behavioral refusal arm in this project ablates the L18 direction, so the artifact those results depend on
is now generation-validated rather than assumed.

## 4b. The corrected induce arm (job `721957`) — L9 fails BOTH directions, in BOTH families

The induce arm of 720463 was uninterpretable (§5). Job **`721957`** re-ran the same 10 cells with
`--induce-eval harmless`. The fix is visible in the log:

```
harmless set: 20 total -> fit/alpha n=10, induce-eval n=10, disjoint=True
baselines: harmful refusal=0.950  induce-base (harmless) refusal=0.000  [headroom for induce_gain = 1.000]
```

**The induce base went from 0.750 to 0.000** — a real test instead of a 0.25-capped one. n_harmful = 20,
n_benign = 10 (so one induce item = 0.10).

| family | layer | `ablate_spec` | `induce_spec` | valid (both arms) |
|---|---|---|---|---|
| `existing` | **9** | −0.050 | **+0.000** | **✗ FAILS BOTH** |
| `existing` | 16 | +0.450 | **+1.000** | ✅ |
| `existing` | 18 | +0.600 | **+1.000** | ✅ |
| `existing` | 22 | +0.250 | **+0.000** | ✗ (ablate only) |
| `existing` | 28 | +0.250 | +0.100 | ✅ |
| `clearharm` | **9** | −0.100 | **+0.000** | **✗ FAILS BOTH** |
| `clearharm` | 16 | +0.300 | +0.900 | ✅ |
| `clearharm` | 18 | +0.900 | +0.800 | ✅ |
| `clearharm` | 22 | +0.350 | +0.100 | ✅ |
| `clearharm` | 28 | +0.300 | +0.400 | ✅ |

**Why the `clearharm` ablate numbers differ slightly from §3.** The `existing` column is **byte-identical
across the two runs** (−0.050 / +0.450 / +0.600 / +0.250 / +0.250), as it must be — those vectors are
loaded, not fitted. The `clearharm` column moved a little (L16 +0.350→+0.300, L22 +0.450→+0.350, L9/L18/L28
unchanged) because `--harmless-holdout` halves that family's negative class from 20 to 10 so the induce arm
is not scored on its own fit set. That is the intended cost of the holdout: a slightly weaker refit in
exchange for an induce arm that means something. **No cell changes sign or validity status.**

**Controls are clean:** `induce_gain_rand` = 0.000 in **all ten** cells, `ablate_gain_rand` ∈ {0.00, 0.05},
`empty_induced` = 0.0 everywhere. The random directions do nothing, so the specificity contrasts are not
being carried by generic perturbation damage.

**L9 is the only layer invalid in both families, and it now fails on both arms.** With a full +1.000 of
headroom available, adding the L9 direction to benign prompts induces **zero** refusal — while the same
operation at L16/L18 flips 8–10 of 10 benign prompts into refusals. This is much stronger than the ablate
arm alone: L9 is not merely *unnecessary* for refusal, it is *insufficient* to produce it.

**A caveat that must travel with the depth claim.** Under the strict bidirectional criterion the two
families disagree at **L22**: `existing` L22 passes ablate (+0.250) but induces **nothing** (+0.000), so it
is **not** a validated refusal axis; the ClearHarm refit at L22 passes both but only weakly (+0.100 induce
= 1 of 10 items). Since the published depth-localization result leans on *"L22 significant"*, that claim
rests on a direction which is validated in only one of two families. **L16 and L18 are the only layers
that validate strongly and unambiguously in both.** Any depth statement should be anchored there and
should state the L22 asymmetry rather than average over it.

## 4c. The full 32-layer sweep (job `722611`, 3870 rows) — the appendix result

Same design, `--induce-eval harmless`, every layer. **Reconciled by the standard validator: 1348 summary
values recomputed from `raw.jsonl`, 0 mismatched**, 64 cells, 0 duplicate rows, `empty_max` = 0.0.

**Validity counts:** `existing` **12/32**, `clearharm` **15/32**. Best layer: `existing` L15 (score 1.9),
`clearharm` L18 (1.7).

| set | layers |
|---|---|
| **valid in BOTH families** | **13, 14, 15, 16, 17, 18, 19, 20, 24, 28, 29** (n=11) |
| `existing` only | 21 |
| `clearharm` only | 22, 23, 27, 30 |
| **invalid in BOTH** | **0-12**, 25, 26, 31 (n=16) |

**The depth story is a contiguous block, which is what makes it credible.** Layers **0-12 fail in both
families without exception**, and **13-20 pass in both without exception**. A linearly-decodable refusal
axis does not exist in the first thirteen layers; it appears abruptly at L13 and holds through L20. That is
not a threshold artifact of one fit - two independently-built direction families draw the same boundary in
the same place.

### WARNING WARNING - PROTOCOL ASYMMETRY (resolved below by job 724931 - read both)

**The two families are NOT measured under the same induce protocol.** Found by adversarial self-review
*after* this section was first written.

`--harmless-holdout` splits `HARMLESS_INSTRUCTIONS` so the **ClearHarm refit** is never scored on its own
fit set. It does **nothing** for the `existing` family: those directions shipped from
`outputs/refusal_alllayers/`, and every one of their `.json` files records **`n_harmless: 20`**
(`build_refusal_direction_llama.py` iterates the whole list). **So `HARMLESS_EVAL` is a SUBSET of the
`existing` fit set, item for item.**

Concretely: `existing` is induce-tested on 10 benign prompts its own diff-of-means was optimised to push
to the low end of `v`; `clearharm` is induce-tested on 10 it has never seen. **Adding alpha*v to an
in-sample negative is the easiest possible induce test.** Therefore:

- **Do not compare the two `n_valid` counts (12 vs 15) as if they were commensurable.** They are not.
- **Every one-family-only verdict below is confounded with this asymmetry**, including the L21 / L22 / L30
  splits that qualify RP-01, BR-08 and TR-01. Those qualifications stand as *"not established in both
  families"*, but they are **not** evidence that the direction is worse in the failing family.
- **The L9 result is the one conclusion this makes STRONGER.** `existing` had the *easier* in-sample
  induce test at L9 and still induced **+0.000**. A direction that cannot raise refusal even on the very
  prompts it was fit against is not a refusal direction.
- The clean fix is a third family: refit `existing` on `HARMLESS_FIT` only and validate that. Not yet run.

The `clearharm` refit is additionally handicapped by the holdout (negative class 10 rather than 20) --
the intended cost of an honest induce arm, but a second reason the counts are not directly comparable.

### RESOLVED - the one-family verdicts were an artifact (job 724931)

The PROTOCOL ASYMMETRY above said the two families were not comparable because `harmless` is
`existing`'s own fit set. **That is now fixed by measurement, not by caveat.** Job `724931` re-ran
L9/L16/L18/L21/L22/L30 with `--induce-eval benign` -- the v3 `benign` condition, which is in **neither**
family's fit, so both are out-of-sample simultaneously.

| layer | `harmless` population (`existing` IN-SAMPLE) | **`benign` population (both out-of-sample)** |
|---|---|---|
| **9** | NEITHER | **NEITHER** |
| 16 | BOTH | **BOTH** |
| 18 | BOTH | **BOTH** |
| **21** | *existing only* | **BOTH** |
| **22** | *clearharm only* | **BOTH** |
| **30** | *clearharm only* | **BOTH** |

**The one-family-only verdicts at L21, L22 and L30 do not survive**, so the qualifications they forced
onto RP-01, BR-08 and TR-01 are **withdrawn**. Two independent reasons to treat them as artifact:
1. they disappear the moment the induce population stops being `existing`'s fit set, which is exactly
   what D1 predicted; and
2. on the confounded population the splits ran in **opposite directions** (L21 existing-only, L22 and L30
   clearharm-only). A genuine family difference would be *directional*; a coin-flip pattern is not.

**What is robust across all three populations tested** (`neutral`, `harmless`, `benign`): **L9 fails in
both families every time, and L16/L18 pass in both families every time.** The headline does not depend on
the population choice.

**Caveat that must travel with this table.** The v3 `benign` condition is **not a clean floor** -- the
model refuses **45 %** of it, so induce headroom is **0.55**, not the 1.000 the harmless set offered.
`benign`-based induce gains are therefore **not comparable** to `harmless`-based ones and must never be
pooled with them. n = 20 per cell throughout, so one induce item = 0.05.

### ~~WARNING - consequence for three published claims~~ (SUPERSEDED - see the RESOLVED section above)

**The table below is retained as the record of what the `harmless`-population run showed, and is NO
LONGER the operative verdict.** Its three one-family-only rows (L21, L22, L30) were artifacts of scoring
`existing` on its own fit set; on the out-of-sample `benign` population all three validate in BOTH
families. Only the L9 row below still stands, and it stands on all three populations.



Of the layers our headline results are read at, **only L18 is in the cross-validated set**:

| layer | carries | `existing` | `clearharm` | status |
|---|---|---|---|---|
| **L18** | every behavioral refusal-ablation arm | PASS (+0.600/+1.000) | PASS (+0.900/+0.800) | **safe** |
| L21 | the rep->behavior AUC result | PASS (+0.300/+0.100) | FAIL (induce **+0.000**) | **one family only** |
| L22 | the depth-localization claim | FAIL (induce **+0.000**) | PASS (+0.350/+0.100) | **one family only** |
| L30 | the trajectory result | FAIL (induce **+0.000**) | PASS (+0.350/+0.100) | **one family only** |
| L9 | the "refusal not read early" contrast | FAIL (-0.050/+0.000) | FAIL (-0.100/+0.000) | **invalid in both - as claimed** |

L21, L22 and L30 each fail the induce arm in exactly one family, and in each case it is a *hard* zero, not
a near miss. **Each of those three results should be reported with the family it validates in named**, or
re-read at a layer inside 13-20. The L9 claim is unaffected - L9 failing in both families IS the finding.

### Per-layer detail

| L | existing abl / ind | ok | clearharm abl / ind | ok | both |
|---|---|---|---|---|---|
| 0 | +0.050 / +0.000 | · | +0.000 / +0.000 | · |  |
| 1 | +0.000 / +0.000 | · | +0.000 / +0.000 | · |  |
| 2 | +0.050 / +0.000 | · | +0.050 / +0.000 | · |  |
| 3 | +0.050 / +0.000 | · | +0.000 / +0.000 | · |  |
| 4 | -0.050 / +0.000 | · | -0.050 / +0.000 | · |  |
| 5 | -0.100 / +0.000 | · | -0.050 / +0.000 | · |  |
| 6 | -0.050 / +0.000 | · | -0.050 / +0.000 | · |  |
| 7 | -0.050 / +0.000 | · | -0.050 / +0.000 | · |  |
| 8 | +0.000 / +0.000 | · | -0.050 / +0.000 | · |  |
| 9 | -0.050 / +0.000 | · | -0.100 / +0.000 | · |  |
| 10 | -0.050 / +0.300 | · | -0.050 / +0.400 | · |  |
| 11 | -0.100 / +0.300 | · | -0.050 / +0.600 | · |  |
| 12 | -0.100 / +0.000 | · | -0.050 / +0.300 | · |  |
| 13 | +0.350 / +1.000 | ✓ | +0.250 / +1.000 | ✓ | **✔** |
| 14 | +0.350 / +1.000 | ✓ | +0.250 / +0.400 | ✓ | **✔** |
| 15 | +0.850 / +1.000 | ✓ | +0.700 / +0.900 | ✓ | **✔** |
| 16 | +0.450 / +1.000 | ✓ | +0.300 / +0.900 | ✓ | **✔** |
| 17 | +0.250 / +1.000 | ✓ | +0.650 / +0.700 | ✓ | **✔** |
| 18 | +0.600 / +1.000 | ✓ | +0.900 / +0.800 | ✓ | **✔** |
| 19 | +0.200 / +0.800 | ✓ | +0.600 / +0.700 | ✓ | **✔** |
| 20 | +0.300 / +0.800 | ✓ | +0.550 / +0.300 | ✓ | **✔** |
| 21 | +0.300 / +0.100 | ✓ | +0.350 / +0.000 | · |  |
| 22 | +0.250 / +0.000 | · | +0.350 / +0.100 | ✓ |  |
| 23 | +0.200 / +0.000 | · | +0.300 / +0.200 | ✓ |  |
| 24 | +0.150 / +0.100 | ✓ | +0.300 / +0.200 | ✓ | **✔** |
| 25 | +0.200 / +0.000 | · | +0.350 / +0.000 | · |  |
| 26 | +0.200 / +0.000 | · | +0.250 / +0.000 | · |  |
| 27 | +0.200 / +0.000 | · | +0.350 / +0.100 | ✓ |  |
| 28 | +0.250 / +0.100 | ✓ | +0.300 / +0.400 | ✓ | **✔** |
| 29 | +0.300 / +0.200 | ✓ | +0.350 / +0.300 | ✓ | **✔** |
| 30 | +0.250 / +0.000 | · | +0.350 / +0.100 | ✓ |  |
| 31 | +0.150 / +0.000 | · | +0.300 / +0.000 | · |  |

*(`abl`/`ind` are the specificity contrasts against norm-matched random directions; `valid` requires both
raw gains AND both specificities strictly positive.)*

## 5. ⚠️ The induce arm of run `720463` is not interpretable — read its ablate arm only

The induce arm was evaluated on `neutral`, and **`neutral` is not benign**: it is the harmful request with
the harmful word swapped for the codeword (`ds_common.build_conditions:797`), i.e. a *disguised harmful*
prompt. Measured here it refuses at **0.750**. Two consequences:

1. **Ceiling.** `induce_gain` cannot exceed **+0.25**, so a perfectly good direction can fail the induce
   criterion from the ceiling alone.
2. **Dose/population mismatch.** `alpha_induce` is calibrated as
   `mean_proj(direct) − mean_proj(HARMLESS_INSTRUCTIONS)` but was applied to a population whose projection
   is already elevated.

**The ablate arm is unaffected** — it always ran on `direct` (base 0.950, full headroom to drop) — so
everything in §3 stands. The fix (`--induce-eval harmless`, default as of 2026-08-06, with
`--harmless-holdout` so the induce arm is not scored on the refit's own fit set) is implemented and job
**721957** re-runs the headline layers with it.

## 6. Honest limitations

- **n = 20 per cell**, so one item = 0.05. L9's −0.050 / −0.100 are **1–2 items and are not
  distinguishable from zero on their own.** The claim rests on the **contrast** with L16–L28 (whose
  specificity spans **5 to 18 items** of 20) and on its replication across two independent fits — not on
  the L9 point estimate.
- ~~**Only 5 layers were run.**~~ **DONE — §4c, job `722611`, all 32 layers.** The DSVALN=3 smoke's
  "~15/32 validate" guess turned out close for `clearharm` (15/32) but optimistic for `existing` (12/32);
  more importantly the smoke could not have identified the *cross-family* set, which is the number that
  actually matters (11/32).
- No per-cell significance test is reported here. The reported quantity is a specificity difference of
  two rates at n=20; a paired test across items is the natural upgrade before publication.
- ~~`validate_all_outputs.py` does not recognise the `refval` row schema.~~ **FIXED 2026-08-06.** Both
  validators now know the schema; every completed refval dir reconciles (1702 + 1348 values recomputed,
  **0 mismatched**), and the reconciler is negative-controlled.
- **Induce n is 10, not 20** (the held-out half of `HARMLESS_INSTRUCTIONS`), so one induce item = 0.10 and
  a `+0.100` induce specificity is a **single item**. L22 and L30 clear the bar on `clearharm` by exactly
  that margin — they are *technically* valid but should not be described as strongly validated. A larger
  benign eval set is the cheapest way to firm this up.

## 7. Reproduce

```
sbatch --time=03:00:00 --nodelist=n-801,n-802,n-804,n-805,t-806 \
  --export=ALL,DSLAYERSET=headline,DSVALN=20,DSMAXNEW=64 \
  doublespeak_causality/slurm/run_refusal_validate.sh
```
(Do **not** pass `--exclude`; it nullifies the wrapper's `#SBATCH --nodelist` and the job can land on a
non-L40S node — see the wrapper header.)

Run dir: `outputs/refval_clearharm_20260806_033340_720463` (git `26542e5d`). To reproduce the *induce*
numbers of that run exactly, add `--induce-eval neutral`.
