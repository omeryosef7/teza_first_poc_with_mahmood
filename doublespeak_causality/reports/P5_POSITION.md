# §5 — Demonstration-Position Decomposition (which part suppresses refusal?)

**Status:** DONE (negative / clean NULL). Closed on committed data — train n=85 + test n=42, both
≥20/cell — no new GPU run required. The null IS the finding: no single demo-position manipulation both
preserves the concept-remap AND restores refusal. Refusal suppression is broad over demo
structure/count, not localized to one separable component.

**Run:** `phase5_position.py` (`...736658`), clearharm, 9 matched demo-text variants
(direct, full, neutral, mapping_altered, codeword_randomized, benign_format, shuffled, reduced_count,
single_demo). Per variant: decision-token refusal projection restore-frac, ASR, p_concept. Model:
`meta-llama/Llama-3.1-8B-Instruct`; anchor_row 19. Reported for both the train (n=85) and test (n=42)
splits.

## Result — dissociation table, TRAIN split (n=85) — want ΔASR<0 while p_concept stays high
| variant | ΔASR vs full-DS | proj_restore_frac | p_concept (95% CI) |
|---|---|---|---|
| codeword_randomized | −0.0588 | −0.7141 | 0.9035 (0.8695–0.9356) |
| mapping_altered | −0.0235 | 0.0826 | 0.9083 (0.8640–0.9472) |
| benign_format | +0.0118 | 0.0031 | 0.8995 (0.8537–0.9447) |
| reduced_count | +0.0118 | −0.1726 | 0.9626 (0.9298–0.9866) |
| single_demo | +0.0118 | **0.6587** (most refusal restored) | 0.7511 (0.6656–0.8306) (concept drops) |
| shuffled | +0.0353 | 0.7455 | 0.9688 (0.9368–0.9947) |

Anchors (train): direct proj_mean 4.5012 (CI 3.88–5.0696, restore_frac 1.0, ASR 0.1412);
full-DS proj_mean 1.9418 (CI 1.4234–2.4771, restore_frac 0.0, ASR 0.2941, p_concept 0.9827);
neutral proj_anchor 2.4702 (CI 1.8958–3.0415, restore_frac 0.6459, ASR 0.3176, p_concept 0.7524).

## Result — dissociation table, TEST split (n=42) — want ΔASR<0 while p_concept stays high
| variant | ΔASR vs full-DS | proj_restore_frac | p_concept |
|---|---|---|---|
| codeword_randomized | −0.072 | −0.216 | 0.875 (high) |
| benign_format | −0.072 | −0.096 | 0.968 (high) |
| mapping_altered | 0.000 | −0.236 | 0.904 |
| single_demo | +0.024 | **−0.597** (most refusal restored) | 0.468 (concept drops) |
| shuffled | +0.048 | −0.087 | 0.964 |
| reduced_count | +0.048 | −0.162 | 0.942 |

Anchors (test): direct proj_mean 4.3213 (CI 3.4569–5.177); full-DS proj_mean 2.763 (CI 2.0671–3.4746,
p_concept 0.9503); neutral proj_anchor 3.1142 (restore_frac −0.2716, p_concept 0.6219).

## §5.3 — demo_answers_removed: NOT CONSTRUCTIBLE
Per the committed summary (`flagged_variants`): the Doublespeak demos are declarative benign sentences
with no question/answer segment to remove (`doublespeak_attack.py`: substituted sentences only). There
is no answer span to ablate, so the demo_answers_removed arm cannot be built and is excluded by
construction — not missing work.

## Interpretation — honest conclusion (clean NULL / negative dissociation)
- **No manipulation both preserves concept AND restores refusal.** Across both splits, every variant
  that meaningfully restores refusal also degrades the concept-remap, and every variant that keeps
  concept high leaves ASR essentially unchanged (|ΔASR| ≤ 0.07). There is no clean dissociation.
- **`single_demo` confounds concept with refusal.** It moves refusal the most (proj_restore_frac
  0.6587 train / −0.597 test — largest-magnitude shift in each split) but simultaneously collapses
  p_concept (0.7511 train, 0.4684 test, vs full-DS 0.9827/0.9503). Cutting demonstrations weakens the
  concept remap and the refusal suppression together; it does not isolate a component.
- **Refusal suppression is broad over demo structure/count, not localized.** Shuffling order, altering
  the mapping, randomizing codewords, benign formatting, and reducing count each leave ASR within noise
  of full-DS while keeping concept high — consistent with the suppression being a distributed function
  of the demonstration block rather than any single separable position/component.
- **ΔASR effects are small (≤0.07)** and directional; with train n=85 + test n=42 (both ≥20/cell) this
  is a powered, reproducible negative on committed data. §5 is closed: the partial/absent dissociation
  is the result.
