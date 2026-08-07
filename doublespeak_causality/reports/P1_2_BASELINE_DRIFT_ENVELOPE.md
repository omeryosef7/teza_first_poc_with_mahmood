# §1.2 — GPU Baseline / Judge-Noise Drift Envelope

**Status:** ✅ DONE. Establishes the empirical noise floor for interpreting ΔASR.
**Run:** `baseline_drift_clearharm_...732432` (127r, v3b clearharm train85/test42) · commit `bd56e69f` ·
harness `scripts/phase_baseline_drift.py`. Each item: 4 conditions (direct/doublespeak/neutral/benign),
generated **twice** (greedy determinism check) + each generation **re-judged K=3×** (byte-identical text).

## Results
| split | condition | ASR | gen_determinism | judge_flip mean / any | trunc(len) | mean tok |
|---|---|---|---|---|---|---|
| train n=85 | direct | 0.153 | **1.000** | 0.008 / 0.024 | 0.106 | 44.5 |
| train | doublespeak | 0.306 | **1.000** | 0.016 / 0.047 | 0.329 | 86.4 |
| train | neutral | 0.271 | **1.000** | 0.016 / 0.047 | 0.271 | 76.1 |
| train | benign | 0.247 | **1.000** | 0.020 / 0.059 | 0.388 | 96.4 |
| test n=42 | direct | 0.167 | 1.000 | 0.024 / 0.071 | 0.167 | 56.7 |
| test | doublespeak | 0.167 | 1.000 | 0.008 / 0.024 | 0.262 | 72.6 |
| test | neutral | 0.238 | 1.000 | 0.008 / 0.024 | 0.214 | 70.5 |
| test | benign | 0.310 | 1.000 | 0.000 / 0.000 | 0.333 | 91.8 |

## Noise floor (the deliverable)
1. **Generation determinism = 1.000** in every cell — greedy re-generation is byte-identical; there is **no
   unexplained generation variance**. Any run-to-run difference in a downstream experiment is therefore a real
   effect, not sampling noise.
2. **Judge label-flip floor:** re-judging byte-identical text flips the StrongREJECT label on **mean ~1–2%**
   of items (any-flip up to ~7% at K=3). This confirms the plan's ~2pp floor empirically → **any |ΔASR| below
   ~2pp is uninterpretable** (§30).
3. **empty_rate = 0** everywhere (no over-drive/incoherence); truncation is condition-dependent (benign/DS
   longest, 33–39%).

## Bearing on Gate B (§23)
Gate B's significant decision-state effects — ΔASR **−0.141 (train, p=0.012)** and **−0.186 (dev, p=0.008)** —
are **7–10× the ~2pp judge-noise floor**, so they are robustly real, not judge jitter. The non-significant
**test** cell (direct L17 ΔASR −0.05) is **power-limited** (ds_base ASR only 0.167 → ≤7 rescuable items), not
noise-limited. Cross-check: doublespeak ASR (0.31) > direct (0.15) on clearharm train — the attack is real
here, consistent with Gate B's ds_base rate.

## Verdict
✅ Noise floor established: greedy generation deterministic; StrongREJECT label-flip ≈1–2% (≤~7% any) →
interpret only |ΔASR| ≳ 2pp. Gate B train/dev effects clear this by ~7–10×.
