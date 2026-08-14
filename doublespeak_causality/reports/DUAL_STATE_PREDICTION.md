# DUAL-STATE PREDICTION — Phase 3

Required deliverable (plan §7.2-§7.3, §20). Which pre-generation latent state predicts
**which Doublespeak prompts jailbreak** — the decodable semantic identity (Bombness),
or the refusal state (Refusalness)?

**Headline: Refusalness predicts; Bombness does not.** This is the sprint's central
representation≠behavior dissociation in latent-state-prediction form (Story A, §22).

| | |
| --- | --- |
| Extraction | `outputs/probe_bombness_full_clearharm_20260814_150624_757886/` (job 757886) |
| Outcomes | `refdecpatch_clearharm_20260807_194210_732388/raw.jsonl` (ds_base, n=170) |
| Outcome def | DS jailbreak = ds_base StrongREJECT ≥ 0.5 (D2). Success rate 0.247 (pooled), 0.167 (holdout) |
| Bombness | Gate-1 probe score @ query codeword, L11 (fit on train doublespeak-vs-benign) |
| Refusalness | projection of the decision-token residual onto the **frozen** validated refusal_L18 (manifest §6.1; not refit) |
| Split | v3: train 85 / dev 43 / test 42 (codeword- & concept-disjoint) |
| Analysis | `src/probes/dual_state_predict.py` (CPU, no GPU) |

Outcome is stable across behavioural runs: three independent n=170 runs agree 94–96%
on binary@0.5 (ds_base ASR 0.24–0.28).

---

## 1. Nested models (holdout AUC, n=42, fit train / select C on dev / eval test)

| model | holdout AUC | log-loss |
| --- | --- | --- |
| **A. Bombness only** | **0.592** | 0.475 |
| **B. Refusalness only** | **0.976** | 0.471 |
| C. Bombness + Refusalness | 0.959 | 0.331 |
| D. + interaction | 0.955 | 0.316 |

Incremental AUC:
- Refusalness over Bombness: **+0.384**
- Both over Refusalness: **−0.016** (Bombness adds nothing to discrimination)
- Interaction over both: **−0.004** (no interaction)

Adding Bombness improves log-loss (0.47→0.33) — a small calibration gain — but not
discrimination (AUC does not rise). The C-model coefficients (standardized) are
Bombness +0.11, **Refusalness −0.78**: Refusalness dominates (high refusal → low
success), Bombness is near-zero.

## 2. Univariate holdout AUC with bootstrap 95% CI (10k, resampled examples)

| feature | oriented AUC | 95% CI |
| --- | --- | --- |
| Refusalness | **0.976** | [0.921, 1.000] |
| Bombness | 0.592 | [0.506, 0.855] |
| **Refusalness − Bombness** | **+0.384** | **[0.114, 0.482]** (excludes 0) |

(Pooled n=170 for reference: Refusalness AUC 0.849, Bombness directional AUC 0.509.)

The oriented Bombness AUC (max(auc, 1−auc)) sits at 0.59 with a CI touching chance; its
*directional* AUC is 0.41 — i.e. below chance, consistent with "no predictive signal."

## 3. Quantile success curves (§7.2, pooled n=170, 5 bins)

| bin (low→high) | by **Bombness** | by **Refusalness** |
| --- | --- | --- |
| 0 | 0.21 | **0.50** |
| 1 | 0.27 | 0.53 |
| 2 | 0.24 | 0.21 |
| 3 | 0.35 | 0.00 |
| 4 | 0.18 | **0.00** |

Refusalness is strongly monotone (low refusal → 50% jailbreak, high refusal → 0%).
Bombness is flat (no relationship with success).

## 4. Interpretation

Combined with Gate 1 (Bombness is near-perfectly **decodable**, holdout AUC 0.997) this
gives the clean latent-state dissociation:

> Doublespeak induces a strong, decodable semantic-identity confusion — the codeword
> becomes internally BOMB-like (Gate 1) — that is **orthogonal to refusal** at the
> codeword (cos 0.09) and carries **no predictive information** about which prompts
> actually jailbreak (AUC 0.59, ΔAUC vs refusal −0.38). The **refusal state** at the
> decision token predicts jailbreak almost perfectly (AUC 0.98). Being placed in the
> adversarial latent identity is real but is **not** the behavioral security failure;
> a separable refusal-suppressed state is.

This extends the role-confusion result: *latent confusion tracking attack success* is
not automatic — here the semantic-confusion axis does **not** track success, while a
distinct control axis does.

## 5. What this does and does NOT establish

**Establishes (predictive):** Refusalness, not Bombness, predicts held-out DS jailbreak;
the two are separable (orthogonal geometry + independent predictive value). This is the
latent-state form of the representation≠behavior dissociation.

**Does NOT establish (causal):** prediction is not causation. That Bombness does not
*predict* success is strong evidence it is not the driver, but the decisive test is
**Phase 4** — directly manipulating Bombness (necessity/sufficiency) and the 2×2
Bombness × refusal factorial. The project's prior causal work (§1.3) already shows
refusal is causally potent; Phase 4 asks whether Bombness is causally inert (Story A) or
conditionally causal (Story B).

## 6. Limitations

- Holdout n=42 (7 successes): the Refusalness AUC CI is wide at the top; the pooled
  n=170 (0.849) is the more stable estimate. The **direction** of the dissociation is
  robust across pooled/holdout and across the three outcome runs.
- Refusalness uses the frozen refusal_L18 direction, fit cross-distribution on
  carrot_bomb (B17); it nonetheless predicts clearharm DS success at 0.85–0.98, which
  further validates it.
- Refusalness is a frozen projection (not refit), so its predictive power is not
  inflated by fitting; Bombness is a train-fit probe score (fit to separate
  doublespeak/benign, never on the jailbreak outcome), so no outcome leak.
- clearharm cohort only; the generated cohort is a held-out replication (extract with
  `COHORT=generated`).

## 7. Reproduce

```
python -m src.probes.dual_state_predict \
  --run <full_extraction_dir> \
  --outcomes outputs/refdecpatch_clearharm_20260807_194210_732388/raw.jsonl \
  --out <run_dir>/dual_state_predict.json
```
