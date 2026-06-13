# Onset Analysis Results

_Generated: 2026-06-11T14:39:35.855229Z_

**Total examples:** 94  **High+medium confidence:** 94 (100%)

> **Caveat:** The onset proxy is a heuristic based on keyword overlap.
> It approximates the first position where target-specific terms appear
> in the thinking trace. Results should be treated as directional signals,
> not ground truth. Manual validation is recommended before strong claims.
> See `manual_onset_review_packet.csv`.

## 1. Is onset usually early, middle, late, or unavailable?

| onset_bucket | n | ASR% |
|-------------|---|-----|
| early | 92 | 52.2% |
| middle | 0 | nan% |
| late | 2 | 0.0% |
| none | 0 | nan% |
| unavailable | 0 | nan% |

## 2. Does condition A delay onset relative to D/F?

| Condition | n | Mean onset% | Median onset% | Mean tokens before | n_early | n_late |
|-----------|---|------------|--------------|------------------|---------|--------|
| A | 32 | 0.0% | 0.0% | 0 | 32 | 0 |
| D | 31 | 0.0% | 0.0% | 0 | 31 | 0 |
| F | 31 | 7.4% | 0.0% | 42 | 29 | 2 |

## 3. Do successful runs have earlier or later onset?

| sr_success | n | Mean onset% | Median onset% | Mean tokens before |
|-----------|---|------------|--------------|------------------|
| True | 48 | 0.1% | 0.0% | 1 |
| False | 46 | 4.9% | 0.0% | 28 |

## 4. Statistical tests (high+medium confidence only)

- Spearman ρ(onset% vs SR score): r = -0.2167, p = 0.0359
- Spearman ρ(onset% vs think tokens): r = -0.371, p = 0.0002
- Mann-Whitney U (success vs failure onset%): U = 912.0, p = 0.0309
- Kruskal-Wallis (onset% across conditions): H = 29.276, p = 0.0

## 5. Uncertainties (because proxy is heuristic)

- Keyword extraction from condition D prompt may include non-target structural words
  that also appear in puzzle wrapper. This biases onset toward earlier positions.
- Word-level tokenization does not match model tokenization. Onset position in tokens
  is approximate.
- For condition A, puzzle text occurs before the target span. If puzzle words happen to
  match target keywords (unlikely but possible), onset will be falsely early.
- Confidence tier 'medium' (1 match) may reflect coincidental overlap.
- The onset proxy is computed on think_text word tokens, not the model's actual token
  sequence. Onset_token_idx should be interpreted as a rough proportional measure.

## 6. Manual annotations needed

See `manual_onset_review_packet.csv` for examples prepared for human review.
Before making strong claims about onset timing, at minimum 20 examples (stratified
by condition and outcome) should be manually annotated.

Recommended annotation process: reviewer reads the redacted_snippet in context of
the full (non-redacted) thinking trace (researcher access only), and assigns:
`before_target / first_target_engagement / after_target / no_engagement / unclear`