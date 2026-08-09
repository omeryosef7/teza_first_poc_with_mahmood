# §13 — PROSPECTIVE Frozen-Predictor Attack-Success Prediction (v3, leakage-free)

**Status:** ✅ DONE. **The decision-token refusal projection PROSPECTIVELY predicts which held-out items
jailbreak: a threshold FROZEN on train gives test AUC = 0.971 (accuracy 0.857, fn=0 — every test jailbreak
caught).** This upgrades the committed pooled predictor (RP-01/E4b, AUC 0.874) to a leakage-free prospective
protocol on v3: calibrate on train, freeze, evaluate the untouched test split.

**Run:** projections from `refproj_clearharm_20260809_155851_738761` (v3 clearharm, train n=85 + test n=42,
forward-only, `scripts/phase_refusal_projection.py`); per-item ds_base jailbreak labels from the committed
Gate-B behavioral run `refdecpatch_clearharm_...732560` (StrongREJECT MALICIOUS=1); joined by item id and
scored by `scripts/phase13_prospective_predictor.py` (CPU). Predictor score = −(refusal projection @ L18);
threshold frozen on train by Youden's J.

## Result
| quantity | value |
|---|---|
| n joined (train / test) | 127 (85 / 42) |
| base jailbreak rate (train / test) | 0.282 / 0.167 |
| **train AUC** | 0.802 |
| frozen threshold (train Youden J = 0.565) | −1.9117 |
| **test AUC (frozen predictor)** | **0.9714** |
| **test accuracy @ frozen threshold** | **0.857** |
| test confusion (tp/fp/tn/fn) | 7 / 6 / 29 / **0** |

## Interpretation
1. **Prospective, not just correlational.** With the operating point fixed on train and never touched on test,
   the refusal projection separates held-out jailbreaks from non-jailbreaks at AUC 0.97 and misses none
   (fn=0). The 6 false positives are the conservative cost of a fn=0 operating point.
2. **Leakage-free (v3).** Train/test are cluster-disjoint by v3 construction, so this is a genuine held-out
   generalization of the predictor, resolving the RP-01 pooled-only caveat.
3. Test AUC (0.97) exceeding train AUC (0.80) is sampling variance (test has only 7 positives); the AUC is
   rank-based and threshold-independent, so the frozen-threshold accuracy (0.857) is the conservative headline.

## Caveat
Test n=42 with 7 positives — the point estimates (esp. test AUC) have wide CIs; the load-bearing claims are
(a) the frozen-on-train threshold generalizes (fn=0 on test) and (b) train AUC 0.80 on n=85. Labels are
StrongREJECT ds_base from a committed behavioral run (not re-generated here).

## Verdict
**§13: the refusal projection is a PROSPECTIVE attack-success predictor on v3 — a train-frozen threshold
predicts held-out jailbreak (test AUC 0.97, fn=0).** Related: [[project_causal_circuit_sprint]] (E4b).
