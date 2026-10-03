# Heretic × CSI — short update (defensible results only), 2026-10-03

**One line:** Extending the inherited basket/button codeword dissociation into a full **rank sweep with
rank-matched controls** (using Heretic's ARA machinery as the engine) shows the dissociation is about the
**existence of a specific low-rank causal direction**, **not** about dimensionality — and it **certifies on
held-out validation and across hardware**.

## The experiment (P2a)
For each codeword we fit a rank-r subspace (PLS, the inherited axis method) and, under the frozen CSI attention
knockout, add it back at the codeword row and measure semantic-installation rescue (`y_install`), ranking the
candidate against **46 random + 10 shuffled-label rank-matched controls** (floor 0.0175). Ranks 1 and 16, both
codewords, TRAIN (67 domains, L40S) and VALIDATION (23 held-out domains, a5000). Gates (manipulation / identity /
instrument) pass in every cell.

## Result (certified)
| | rank 1 (VALIDATION) | rank 16 (VALIDATION) |
|---|---|---|
| **basket** | **PASS** — rank 1/57, p=0.0175, recovery 0.036 | FAIL — 10/57, recovery 0.15 |
| **button** | FAIL — 14/57, recovery ≈0 | FAIL — 10/57, recovery 0.12 |

- **basket has a specific, held-out-certifiable rank-1 installation-rescue direction** (also cross-hardware).
- **button has none at rank 1 or rank 16.** Higher rank rescues *neither* codeword beyond generic "dose" that a
  random rank-16 subspace matches equally.
- So the basket-vs-button dissociation is **not** "button needs a higher-dimensional operator" — it is the
  presence (basket) vs absence (button) of a specific low-rank causal direction.

## Two supporting observations
- **Decodability ≠ rescue-specificity:** button's concept is linearly decodable (rank-1 probe ρ≈0.50, rising with
  rank), yet its rescue is never specific at any rank. (basket's rank-1 probe is +12% better — C1 replicated.)
- **Same geometry, different causality:** basket's and button's rank-1 directions are moderately aligned
  (cos 0.56) and their rank-16 subspaces heavily overlap — similar geometry, dissociated causal efficacy.

## What we are NOT claiming (yet)
- This is the PLS/axis **activation-space** candidate; the **ARA-optimized weight operator** (ΔW=BA) is the next
  step (P2b).
- **No behavioral/ASR claim** — this is semantic-installation rescue only.
- Only **2 codewords** so far — a 2-point dissociation, not a population law. Generalizing across the 25
  screen-viable codewords (P6) is the next priority. TEST split remains spent/unused.

## Infra note
Heretic pinned @662e4ba2; its last-prefill ARA capture was insufficient for our codeword-row site, so we ran the
comparable activation-space rescue in the frozen CSI harness (eager/bf16, native-bf16 GPUs) and will use Heretic's
ARA optimizer + Optuna for the weight-operator step.
