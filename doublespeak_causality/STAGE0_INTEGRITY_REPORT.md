# Stage 0 — Integrity-Fix Report

**Sprint:** NEXT_CAUSAL_SPRINT · **Date:** 2026-07-30 · **Branch:** behavioral-causality-sprint
**Scope:** Repair the load-bearing defects C1–C10 (MERGED_MASTER_PLAN.md §II.1) before any new scientific claim.

**Verification:** every defect was confirmed STILL PRESENT by an independent audit agent (commit 8a9b91b had not fixed them), fixed, then all C3–C10 diffs were cleared by a second independent adversarial review agent: **"No must-fix items. No conclusion-inverting bug found."** C1/C2 additionally carry unit tests (`tests/test_integrity_fixes.py`).

Commits: `c48130a` (C1+C2), `7b0a834` (C3–C10).

---

## Fixes applied

| ID | File | Fix | Verified by |
|---|---|---|---|
| C1 | `ds_common.py` + `07_patchscope_readout.py` | New `patch_layer_sweep(R)` (single source of truth) enforces `L ≤ R-1`; 07 routed through it (was `range(R+1)`, patched the readout layer → zero-propagation contamination). | unit test + review |
| C2 | `41_aggregate_pairs.py` | Install arm selected by **signed** max (was `max(abs)` → could store a large negative and mask a real +install); a **missing** d_DS window is quarantined (`pairs_d_DS_incomplete`) and can no longer affirm "inert". | unit test + review |
| C3 | `05_run_activation_patching.py` | Sweep excludes the final/readout block via `patch_layer_sweep(n_layers-1)` (was `range(n_layers)`; readout is `hidden_states[-1]`). | review |
| C4 | `06_run_timing.py` | Removed dead `ps=Patchscopes(...)`; docstring corrected to state only behavioral refusal + gen_len are recorded (no semantic P(harm) is computed here). No metric fabricated. | review |
| C5 | `09_attention_knockout.py` | Count-matched random pool restricted to `range(0, cw_last)` (was `range(0,seq)` → drew causally-invisible post-codeword keys, blocking fewer real keys while recording equal counts). | review |
| C6 | `09` / `10_layerwise_knockout.py` | 09 records `request_located` (was silently using the confounded fallback boundary); 10 warns + sets `mask_4d_applied=False` when the attention mask is not 4-D (was a silent no-op → false "attention has no effect"). | review |
| C7 | `14_behavioral_eval.py` | `malicious_rate` computed over the **scored** partition (`mal/n_scored`), not `mal/n`; judge-health gate (`max_judge_fail_frac`, threshold 0.10) sets `status=JUDGE_UNHEALTHY`; `refusal_rate` correctly stays over full `n`. | review |
| C8 | `18_run_behavioral_necessity.py` | EMPTY guard (mirrors 19): an empty generation is a **distinct** state, excluded from both `n_stay_mal` and the flip denominator `n_base_mal` (was scored BENIGN → counted as a necessity flip, inflating `delta_necessity`). | review |
| C9 | `21_extract_behavioral_features.py` + `22_fit_success_predictors.py` | Held-out-concept AUC now refits the harmful axis **inside each GroupKFold fold** on training concepts only (was one global axis spanning all concepts → axis leakage); 21 writes `features_raw.npz`; column order of the rebuilt features verified against FEATS. Graceful flagged fallback for pre-fix artifacts. | review |
| C10 | `31_validate_readouts.py` | `classify_answer` prefers the concept lexicon over the earliest positional match (was biased toward the null when a filler/codeword word preceded the concept word). **Discrete label only** — the continuous `p_concept` used by every intervention is untouched. | review |

---

## Result-moving changes (flagged for the record)

Three fixes legitimately change committed numbers; all move in the methodologically-correct / conservative direction and are each surfaced in the script output:

1. **C7 (14)** — `malicious_rate` *rises* when judge failures exist (unscored ≠ benign is the correct estimator; gated by judge health).
2. **C8 (18)** — `delta_necessity` *falls* (drops false empty-generation flips → strengthens the honest "not strictly necessary" negative).
3. **C10 (31)** — discrete `reads_as_concept`/`answer_label` shift *toward* concept when the concept word appears. This is the **only** change that moves a number toward the hypothesis. It is principled (de-biases the null-favoring first-match rule) and affects **labels only**; `p_concept` is unchanged, so no intervention/dissociation number is affected. **→ SIGNED OFF by Omer (2026-07-30): keep the fix.** Any label-based number recomputed with it will be marked as using the de-biased classifier.

---

## Claim-status table (post-fix)

| Claim | Sprint | Status | Effect of the fix | Needs GPU re-run? |
|---|---|---|---|---|
| `d_Direct` installs concept (dose-monotone, beats controls, 4/5 pairs) | CAUSAL_CORE | **STANDS** (CONFIRMATORY) | none — derives from 34/35, not the fixed scripts | No |
| `d_DS` causally inert 5/5 pairs | CAUSAL_CORE / S16 | **STANDS** (CONFIRMATORY-negative) | C2 hardens it: real `pair_generalization.json` had measured cells, so 5/5 unchanged — now cannot be manufactured from absence | No (recompute is CPU, cheap) |
| Causal objective anti-predicts held-out ASR; behavior wins | S12 | **STANDS** (NEGATIVE) | none | No |
| Embedding distance does not predict hijack strength (r=−0.189) | Sprint 1 | **STANDS** (NEGATIVE) | none | No |
| P3 patchscope necessity/sufficiency **magnitudes** (0.135; 126×/8181×) | Sprint 1 · P3 | **UNVERIFIED → direction stands, magnitude was C1-contaminated** | C1 fix removes the readout-layer contamination; magnitude must be **re-measured** | **Yes** — re-run `07` (+`05`) |
| Behavioral necessity headline (`delta_necessity` 0.549/0.399) | Sprint 2 · B | **UNVERIFIED (multi-seed CIs off disk) + C8-inflatable** | C8 removes empty-gen inflation; must re-run to commit a clean number | **Yes** — re-run `18` |
| Held-out-concept predictive AUC (0.668) | Sprint 2 · E | **STANDS (moderate) but C9-leakage-bounded** | C9 removes axis leakage; true AUC is bounded ≤ old; must re-run to report the leakage-free value | **Yes** — re-run `21`+`22` |
| Attention knockout demonstration-specificity | Sprint 1 · P6 (already overturned S8) | **STANDS as NEGATIVE** | C5/C6 make the control honest; corroborates the existing not-specific result | Optional |
| "Semantic P(harm) by injection layer" from timing (Stage 3) | Sprint 1 · P4 | **RETRACTED as never-computed** | C4: no such metric exists; do not cite | N/A (deferred to Stage 4) |
| Readout-validation labels (`reads_as_concept`) | S3 | **CHANGED (label de-biased)** | C10; p_concept-based numbers unaffected | Optional (CPU) |

**Load-bearing conclusion:** the *dissociation* story (`d_Direct` installs / `d_DS` inert) and the *causal-objective negative* are unaffected by every fix and stand. The weak points that the fixes touch (P3 magnitude, behavioral necessity CI, held-out AUC) were already self-flagged as unverified/bounded; they now require cheap re-runs to commit clean numbers, but none is on the critical path for the NEW Stage 2 transplant science.

---

## Tests

`tests/test_integrity_fixes.py` (5) — C1 sweep-excludes-readout + degenerate-R raise; C2 missing-cell-not-inert, signed-max-install, genuine-inert-recognized.
`tests/test_transplant_mediation.py` (4) — Stage 2 analyzer positive control (estimands vs hand-computed, faithfulness, verdicts, equivalence).
Existing `tests/test_layerpatch_synthetic.py` (6), `tests/test_pair_benchmark.py` (23), `tests/test_localization.py` (3+skips) — all still green after the `ds_common` change.

## Deviations / notes
- **C4** quarantined rather than implemented (no semantic timing readout fabricated). A *validated* timing semantic readout is deferred to Stage 4 where it is scientifically needed and can carry proper controls.
- **C8** excludes an EMPTY necessity generation from that item's identity/random control tallies too (keeps the denominator identical across delta_necessity/identity/random). Conservative and consistent; empties should be rare.
- **GPU re-runs** for P3 magnitude (C1), necessity CI (C8), and leakage-free AUC (C9) are queued as follow-ups; they validate the repaired code on the *secondary* claims and are not blockers for Stage 2.
