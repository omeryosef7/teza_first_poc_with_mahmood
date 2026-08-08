# Adversarial Audit #2 (2026-08-08) — new results + code (wf_383ca171)

12-agent audit of everything produced since audit #1 (§10, §24, §11, §27 X4/X5, Gate-7, §7 + new/edited code).
Every headline NUMBER reproduces exactly from raw. Findings + fixes:

## Claims
| claim | verdict | action |
|---|---|---|
| §24 orthogonalization | **CONFIRMED** | none (sign correct, not circular, test-null disclosed) |
| §11 joint 2×2 | **CONFIRMED** | none (cells/DiD exact, no interaction valid) |
| §27 X4 (Qwen3 ablation) | **CONFIRMED** | + caveat: DS≈suppression is TRAIN-only (test n=42 doesn't replicate); ablation & random-null DO generalize |
| Gate-7 first-cut | **CONFIRMED** | none (train/test disjoint, negative correctly supported) |
| §7 head/edge (numbers) | **CONFIRMED** | but see code bug 2 (layer-level verdict) |
| §10 powered ablation | CAVEAT (**overclaim**) | "informative-null (MDE≤0.09)" WITHDRAWN — CI upper 0.104 > 0.09; specificity (concept<random) is the valid basis |
| §27 X5 | CAVEAT (**overclaim**) | concept AUC upward-biased (orientation bug); test-split gaps small/overlapping → softened |

## Code bugs found (all in verdict/stat logic; numbers unaffected) — FIXED
1. **phase_x5_concept_qwen3.py (HIGH):** AUC orientation data-chosen (max(AUC,1−AUC)) → inflates null axes ≥0.5. Fixed to a-priori sign. (Direction-safe: true concept AUC ≤ reported → refusal≫concept strengthens.)
2. **phase7_refusal_head_edge.py (HIGH):** `distributed` verdict ignored per-LAYER; L13 alone ≈66% of ceiling → head-distributed but LAYER-CONCENTRATED. Fixed to gate on max_layer; report corrected.
3. **phase10_powered_concept_ablation.py (MED):** "informative-null" from post-hoc MDE (not equivalence). Fixed to require CI-upper < margin (TOST-style); report corrected to specificity basis.

## Clean (no bug)
phase24_orthogonalization.py · phase11_joint_2x2.py · the `--enable-thinking` shared-file edits (Llama byte-identical, Qwen3 thinking-off correct — verified across all 5 files).

## Bottom line
No core conclusion reversed. Every number reproduces from raw. Two overclaims corrected (§10 equivalence, §27-X5
orientation/test-gap), three verdict-logic code bugs fixed, one train-only caveat added (§27-X4). Reports updated;
harness verdict logic hardened for future runs.
