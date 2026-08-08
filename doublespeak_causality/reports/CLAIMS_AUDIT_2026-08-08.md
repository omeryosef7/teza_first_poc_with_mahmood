# Adversarial Claims + Code Audit (2026-08-08)

12-agent adversarial audit (Workflow `wf_8333d36e-5a8`): 7 agents independently recomputed each headline claim
**from raw** (not summaries) and checked the statistical method + wording; 5 agents reviewed the harness code
for correctness bugs. Scalar-only (no generation text read).

## Headline: every reported NUMBER reproduces exactly from raw; methods are sound.
No claim was REFUTED. All 7 verified as CONFIRMED (1) or CAVEAT (6, numbers exact + method sound, wording/
provenance tightened). Two latent code bugs found (neither affected any committed result) and fixed.

## Claim verdicts
| claim | verdict | recompute vs report | action taken |
|---|---|---|---|
| §12 Jacobian (AUC 0.807/0.815, diff +0.225) | **CONFIRMED** | exact to 4dp; no train-on-test; generic-‖J‖ caveat present | none |
| RS-01 Gate A (residual L15–18 restores refusal, frac 0.93, test) | CAVEAT | exact (test 0.9255; attn/mlp 0.10/0.21; self-swap ~5e-6; direct≫rand) | regenerated local L18 analysis file (committed evidence=summary.json was already anchor-18); test Holm-p=0.005 (not ~0) |
| GB-01 Gate B (ΔASR −0.14 p=0.012; self~0; rand opposite; reproduced) | CAVEAT | **exact match** (ΔASR, McNemar b/c, p, reproduction) | scoped Interpretation to forward-necessity (comply direction is NULL); noted 0.27→0.13 not zero |
| GB-02 bidirectional (reverse NULL; random fragility +0.34) | CAVEAT | exact (reverse ns; rand +0.341 p=3e-8 train) | flagged the fragility as TRAIN-only (test +0.095 ns) |
| NF-01 noise floor (determinism 1.0; ~6pp between-run) | CAVEAT | exact | flagged ~6pp as n=1-pair rule-of-thumb (observed gap 3.5pp) |
| DEF-01 defense non-selective (no dose/gate is selective) | CAVEAT (**overclaim fixed**) | exact numbers; core conclusion holds | **fixed the "ratio ≈const 0.5" overclaim** (real ratios 0.15/0.47/0.38/0.50) |
| Claim-audit totals (95/77, 173 checks, 0 CHECK-FAIL) | CAVEAT | exact (0 CHECK-FAIL confirmed) | validate_all_outputs had 2 schema-coverage FAILs (baseline_drift, dose-sweep) → schema being added (§36) |

## Code-audit findings
| script | verdict | affected results? | fix |
|---|---|---|---|
| phase_refusal_decision_patch_behav.py | NONE | — | decode-guard, McNemar, reverse-arm all correct |
| phase_defense_utility.py | NONE | — | correct (one mislabeled comment only) |
| phase_refusal_suppression_localize.py | NONE | — | readout-row indexing, rand norm-match, self no-op all correct |
| **phase_defense_gated.py** | **CONFIRMED (medium)** | **NO** — every run used `--splits train,test` (train present) so T=train_direct_mean was correct | reordered: explicit `--threshold` now wins before the empty-train fallback |
| **analyze_refsuploc.py** | **PLAUSIBLE (low)** | **NO** — all 170 rows carry a uniform donor keyset, so positional pairing == item pairing | specificity bootstrap now pairs direct/rand by ITEM (re-ran: identical results) |

## Bottom line
Every experiment-backed number is reproducible from raw and every statistical method is sound. The only false
statement in the reports was DEF-01's "ratio ≈constant" (now corrected). The two code bugs were latent
(untriggered by any actual run) and are now fixed. Remaining housekeeping: two `validate_all_outputs` schema
gaps (baseline_drift, dose-sweep manifest) being closed (§36). **What we claim, we can stand behind.**
