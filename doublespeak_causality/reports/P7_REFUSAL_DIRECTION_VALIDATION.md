# P7 — Generation-validating the per-layer refusal directions

**Status: ✅ COMPLETE for the headline layers.** Two runs:
`720463` (840 rows) = the ablate arm, and **`721957` (630 rows) = the corrected bidirectional re-run**.

**Verdict: L9 is NOT a refusal axis. It fails BOTH arms under BOTH independently-fit direction families —
ablating it does not reduce refusal, and adding it to benign prompts induces zero refusal against a full
+1.000 of headroom. L16 and L18 validate strongly and unambiguously in both families; L18, the direction
every downstream behavioral arm uses, is the strongest. L22 validates in only one family (see §4b).**

Run dirs: `outputs/refval_clearharm_20260806_033340_720463` (ablate; its induce arm is defective, §5) and
`outputs/refval_clearharm_20260806_051728_721957` (**corrected — cite this one**).

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

> **No linearly-decodable refusal axis exists at L9.** Refusal becomes linearly available at L16 and is
> strongest at L18, remaining available through L28.

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
- **Only 5 layers were run** (L9/16/18/22/28 — the layers our published claims depend on). The full
  32-layer sweep for the appendix has not been done; a DSVALN=3 smoke suggested only ~15/32 validate.
- No per-cell significance test is reported here. The reported quantity is a specificity difference of
  two rates at n=20; a paired test across items is the natural upgrade before publication.
- `validate_all_outputs.py` does **not yet recognise the `refval` row schema**, so these numbers have not
  been machine-reconciled against `summary.json` by the standard validator. Teaching it the schema is a
  prerequisite before any P7 number is marked VERIFIED in `CLAIM_AUDIT_TABLE.md`.

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
