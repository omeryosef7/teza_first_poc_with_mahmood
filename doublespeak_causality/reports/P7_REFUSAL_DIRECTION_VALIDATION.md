# P7 — Generation-validating the per-layer refusal directions

**Status: ✅ COMPLETE for the headline layers** (job `720463`, 840 rows, `DONE.json` present).
**Verdict: L9 is NOT a refusal axis — under either of two independently-fit directions. L16/L18/L22/L28
all validate. L18, the direction every downstream behavioral arm uses, is the strongest.**

Run dir: `outputs/refval_clearharm_20260806_033340_720463`.

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

## 5. ⚠️ The induce arm of THIS run is not interpretable — read the ablate arm only

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
