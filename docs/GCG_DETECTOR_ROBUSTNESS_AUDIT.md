# GCG Detector Robustness Audit

**Scope:** validates the position-0 hidden-state logistic-regression detector used throughout Phases 4-7, using only existing `hidden_states/*.pt` artifacts (no new GPU inference). Rerun script: `scripts/detector_groupkfold_audit.py` (must run under the `poc_stage2` conda env, which has torch+sklearn; the base env used for `python-pptx` does not). Raw per-run outputs: `outputs/stage_gcg_ablation/detector_groupkfold/*.json`.

## 1. Exact methodology (from `poc_stage_gcg_early/train_realtime_detector.py`)

1. **One sample** = one free-generation row (`task_id` x `seed` x `condition_label`), represented by its hidden state at one relative generated-token position (default `pos=0`, the first generated token after the prompt).
2. **Feature**: at that position, hidden states from **all available transformer layers are mean-pooled** into a single `d_model`-dim vector (5120 for Qwen3-14B, 2560 for Gemma4-E4B). This is layer-averaging, not per-layer concatenation, not a single fixed layer.
3. **Label**: class 1 if `condition_label` contains the substring `"optimized"`; class 0 if `condition_label == "neutral_control"`. **`random_spaces` and `task_only` rows are silently excluded** from detector training/eval entirely (not "used as negatives," just dropped).
4. **Classifier**: `StandardScaler` + `LogisticRegression(C=1.0, class_weight="balanced")`.
5. **Original cross-validation**: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` — stratified only on the binary label. **No grouping by `task_id`, suffix, or generation seed** — the same behavior (and even the same generation seed) can land in both the train and validation fold of a given split. This is the leakage risk flagged in the original audit request.

## 2. Bug found and fixed in this pass

`outputs/stage_gcg_ablation/detector_cot_disabled/DETECTOR_REPORT.md` reads:

> **AUC=0.5067:** Near-perfect separation at position 0.

This is wrong: 0.5067 is chance-level (a coin flip), not near-perfect. Root cause is a templating bug at `poc_stage_gcg_early/train_realtime_detector.py:257`:

```python
{'**PERFECT DETECTION:** ...' if metrics["auc_mean"] >= 0.999 else f'**AUC={metrics["auc_mean"]:.4f}:** Near-perfect separation at position {pos}.'}
```

The `else` branch's prose ("Near-perfect separation") is hardcoded and fires for *any* AUC below 0.999 — including exactly-chance or below-chance results. **Any claim sourced from this report's prose (rather than its raw 0.5067 number) is factually wrong.** Not fixing the original script (out of scope — would touch shared pipeline code); flagging here and in the corrected docs so the number, not the auto-generated sentence, is what gets cited going forward.

## 3. Regrouped rerun — does the leakage risk actually change the answer?

For every run with a `hidden_states/` directory, we reran with:
- **GroupKFold(groups=task_id)** — no behavior appears in both train and validation.
- **Leave-one-generation-seed-out** — train on 2 of {42,43,44}, test on the 3rd (generation seed, not optimization seed).

against the original StratifiedKFold baseline, all at position 0:

| Run | Original StratifiedKFold AUC | GroupKFold-by-behavior AUC | Leave-one-seed-out AUC (42/43/44) |
|---|---|---|---|
| standard GCG (qwen3_weighted) | 1.000 | 1.000 | 1.000 / 1.000 / 1.000 |
| 4A CoT-disabled | 0.507 | 0.427 | 0.539 / 0.539 / 0.519 |
| 4B lambda_repr=0 | 0.500 | 0.500 | 0.500 / 0.500 / 0.500 |
| 4C Gemma4 standard | 0.690 | 0.703 | 0.711 / 0.596 / 0.750 |
| 5A CoT-target (`cot_target`) | 1.000 | 1.000 | 1.000 / 1.000 / 1.000 |
| 5B CoT-position repr loss | 1.000 | 1.000 | 1.000 / 1.000 / 1.000 |
| 5C quick-ASR | 1.000 | 1.000 | 1.000 / 1.000 / 1.000 |
| 6A-Q refusal-dir (Qwen3) | 1.000 | 1.000 | 1.000 / 1.000 / 1.000 |
| 6A-G refusal-dir (Gemma4) | 1.000 | 1.000 | 1.000 / 1.000 / 1.000 |
| 6B Gemma4 CoT-target | 1.000 | 1.000 | 1.000 / 1.000 / 1.000 |
| 6C CoT+refusal-dir (Qwen3) | 1.000 | 1.000 | 1.000 / 1.000 / 1.000 |
| 7C Gemma4 nothink | 1.000 | 1.000 | 1.000 / 1.000 / 1.000 |

n=150 per run (75 optimized + 75 neutral, 25 behaviors x 3 generation seeds), so each fold/held-out split is small — treat exact decimal digits past ~2 places as noise, not as evidence GroupKFold and StratifiedKFold are meaningfully different here.

**Finding: for this dataset, grouping by behavior or holding out a whole generation seed does not change the qualitative answer.** Where the original ungrouped AUC was 1.000, it stays 1.000 under both stricter splits; where it was chance-level (4A, 4B) or intermediate (4C, ~0.70), it stays there too. This is **not what a memorization-driven detector would look like** — if the classifier were exploiting per-behavior surface features seen in both train and test, GroupKFold (which removes exactly that leakage path) would be expected to *drop* the AUC relative to the ungrouped baseline, and it doesn't, anywhere in this table.

**Correct claim going forward:** "AUC=1.000 for the standard/CoT-prefix/refusal-direction Qwen3 suffixes and for Gemma4's thinking-disabled and CoT-target and refusal-direction variants, holding under both behavior-grouped and generation-seed-held-out cross-validation on the evaluated data (25 behaviors x 3 generation seeds, n=150 per run)." This is stronger than the pre-audit claim (which only had the ungrouped number) but is still scoped to: position 0, these 25 development behaviors, these 3 generation seeds, this classifier family. It is not validated against unseen optimization seeds (7B) or the full 495 held-out behaviors — see below.

**4C Gemma4-standard is a genuine partial exception**, worth surfacing on its own: AUC ~0.70 (not 1.000, not chance) and seed-sensitive (0.60-0.75 across held-out generation seeds) — this was already correctly reported in `GCG_ABLATION_PIPELINE_LOG.md:17` (AUC=0.698 pos-0) prior to this audit; the regrouped rerun confirms that number rather than contradicting it, and additionally shows it isn't an artifact of the leakage risk either.

## 4. Extended tests (2026-07-13 follow-up — all three previously-deferred items turned out to be CPU-feasible)

The three items below were originally marked "unresolved, needs new GPU work" — that assumption was wrong. Hidden-state replay `.pt` files already existed for all four 7B optimization seeds (42/43/44/45) and for the full 520-behavior 7A evaluation (6,240 files, all conditions including `random_spaces`), so all three tests were run using only existing data. Script: `scripts/detector_extended_audit.py`. Raw output: `outputs/stage_gcg_ablation/detector_groupkfold/{leave_one_optimization_seed_out,dev25_vs_495_behaviors,random_spaces_ood_check}.json`.

**4.1 Leave-one-optimization-seed-out (7B):** train on optimized-vs-neutral samples from 3 of the 4 optimization seeds (42=the 5A/`cot_target` run, 43, 44, 45), test on the entirely unseen 4th seed's suffix.

| Held-out optimization seed | AUC |
|---|---|
| 42 | 1.0000 |
| 43 | 1.0000 |
| 44 | 1.0000 |
| 45 | 1.0000 |

**Result: AUC=1.000 holds even when the test suffix comes from a completely unseen optimization run** (n_train=450, n_test=150 per fold). This directly answers the "does it generalize to unseen suffixes, not just unseen behaviors/seeds of the same suffix" question — yes, on this data.

**4.2 Dev-25-vs-495-behavior split (7A):** train on the 25 original development behaviors' optimized-vs-neutral samples (from the 7A full-520 hidden states), test on the remaining 495 behaviors never used during GCG development.

- Dev set: 75 optimized + 75 neutral (25 behaviors x 3 generation seeds).
- Held-out set: 1,485 optimized + 1,485 neutral (495 behaviors x 3 generation seeds).
- **Result: AUC = 1.0000.** The detector trained on only the 25 tuning behaviors generalizes perfectly to the 495 behaviors it never saw.

**4.3 `random_spaces` as a false-positive / specificity check:** a classifier trained only on `optimized_weighted` vs `neutral_control` was evaluated on the (never-trained-on) `random_spaces` condition — a real, non-optimized but visually odd control — to test whether the detector is specific to genuine GCG optimization or just flags "anything unusual."

| Run | mean P(optimized) on random_spaces | fraction flagged as optimized (P>=0.5) |
|---|---|---|
| `gcg_full_qwen3_weighted` (standard GCG) | 0.0001 | 0.0% |
| `gcg_full_qwen3_cot_target` (5A) | 0.0000 | 0.0% |
| `gcg_full_gemma4_weighted` (4C) | 0.5052 | 42.7% |

**This is a genuinely informative, non-obvious result.** For Qwen3 (where the detector achieves AUC=1.000), it is essentially perfectly *specific* — random, non-optimized garbled-ish text is not mistaken for the real thing (0% false-positive rate on this control). This directly supports the "detects adversarial optimization specifically, not generic anomalous text" framing recommended in §5, at least for Qwen3. For Gemma4 (where overall AUC was already only ~0.70, the weakest of any run tested), the same classifier is confused by `random_spaces` roughly as often as chance (42.7% flagged) — consistent with Gemma4's detector never having a clean decision boundary to begin with, rather than a new failure mode.

## 5b. Remaining not done this pass (explicitly unresolved)

- **Constructed synthetic OOD controls** (random-token suffixes, rarity-matched benign garbled text, Unicode/multilingual suffixes specifically designed to probe the detector): still not done — no such data was ever generated, and `random_spaces` (used above) is a real but different control (uniform whitespace, not rarity/token-distribution-matched to the actual GCG suffixes). Constructing true matched controls would need new suffix generation (GPU). **Unresolved.**

## 5. Corrected claim language

- Do not say "production-ready detector" or "universally detectable" — production deployment testing (e.g. on genuinely benign natural traffic beyond `neutral_control`/`random_spaces`, latency/throughput at scale, adversarial evasion attempts against the detector itself) was not done.
- "Zero false positives" is now **partially supported for Qwen3 specifically**: §4.3 shows 0% of `random_spaces` samples were flagged as optimized for the two Qwen3 runs tested (standard GCG and 5A), though this is one specific non-optimized control, not an exhaustive false-positive-rate study, and does NOT hold for Gemma4 (42.7% flagged).
- Do say: "for Qwen3, AUC=1.000 at position 0, holding under behavior-grouped cross-validation, generation-seed-held-out evaluation, held-out-behavior evaluation (25 dev vs 495 unseen behaviors), AND held-out-optimization-seed evaluation (train on 3 seeds' suffixes, test on a 4th, entirely unseen suffix) — this is a genuinely broad generalization result, not just an in-distribution one. The classifier is also specific to GCG-optimized text rather than a generic anomaly detector, at least for Qwen3 (0% of a real non-optimized `random_spaces` control was flagged)."
- For Gemma4: AUC is lower to begin with (~0.70 for the standard run) and the same classifier does not reliably separate `random_spaces` from optimized suffixes either — do not extend the strong Qwen3 claims above to Gemma4.
- Detection AUC and attack-success ASR are different quantities measured on different label definitions — a suffix can be AUC=1.000 detectable and simultaneously 0% successful (e.g., 7C Gemma4-nothink: AUC=1.000, ASR=0%) or highly successful and equally detectable (5A: AUC=1.000, ASR=10.7%). Detectability says nothing about jailbreak success and vice versa.
