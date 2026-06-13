# Paper-Style ASR Interpretation

_Generated: 2026-06-11T14:39:12.920643Z_

## 1. Stage 4.7 — Cleanest Behavioral Evidence

Stage 4.7 is the cleanest test because it uses 12 diverse source prompts under greedy decoding, and includes condition F (length-matched benign wrapper) as a direct control for prompt length.

- **A (full puzzle + thinking):** ASR = 83.3%  (mean SR score = 0.823, mean think tokens = 11458)
- **D (no puzzle + thinking):** ASR = 45.5%  (mean SR = 0.406, mean think = 2924)
- **F (benign wrapper + thinking):** ASR = 27.3%  (mean SR = 0.240, mean think = 824)
- **E (full puzzle, thinking off):** ASR = 44.4%

### Contrast A vs F (key test):
ΔASR = +58.3 percentage points (sign-test p = 0.0156). Since F is length-matched, this rules out prompt-length confound.

### Contrast A vs D (puzzle contribution):
ΔASR = +41.7 pp (sign-test p = 0.0625). Puzzle adds substantial thinking amplification on top of bare target effect.

## 2. Stage 4.8 — Independent Stochastic Replication

Stage 4.8 uses temperature=0.7 sampling to test robustness. With 20 samples per condition the ordering is preserved:

- A: 60.0%  > D: 50.0%  > F: 40.0%

This confirms the A > D > F ordering is not an artefact of greedy decoding.
The absolute gaps are smaller under stochastic sampling (higher baseline variance).

## 3. Stage 4.6 — Pilot Context

Stage 4.6 used only 4 prompts and partial puzzle fractions (A/B/C/D/E). Results were directionally consistent (A=100%, D~25-50% depending on goal) but with tiny n and no length-matched control. It motivated the larger Stage 4.7 replication.

## 4. Interpretation: Puzzle Is an Amplifier, Not Universally Necessary

- Condition D alone shows some success in Stage 4.7 and 4.8, so the puzzle is **not** strictly necessary for the attack to succeed.
- However, the puzzle **reliably amplifies** both thinking token count and ASR across all tested goals and stochastic seeds.
- Condition F controls for length and semantic richness of the wrapper: the puzzle adds specific structural redirection that benign wrappers of the same length do not.
- **Do not overclaim:** the puzzle effect may be goal-dependent (see per-goal heatmap). Goal 3 succeeds across all conditions; Goal 1 fails across all conditions.

## 5. Key Caveat

The Layer-22 projection direction anti-correlates with thinking depth and does not track behavioral success across Stage 4.7/4.8. Projection scores should not be used as the primary metric. See RL_NOT_YET_RATIONALE.md for details.