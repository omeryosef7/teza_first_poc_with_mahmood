# HERETIC × CSI — interim update, v2 (2026-10-15)

Only defensible results. Scope caveats are part of each claim. Full detail: `HERETIC_CSI_FINAL_REPORT_INTERIM_v2.md`;
verification: `VERIFICATION_INDEX_v2.md`. (v1 of this update is superseded.)

## Headline (new, confirmed)

**Button has a specific rank-4 semantic-installation carrier at L18, where its rank-1 direction has none.**
Preregistered, held out (23 validation domains), ranked 1st of 201 rank- and norm-matched controls (p = 0.005),
Holm-corrected over all three declared validation looks (0.0149), beats every shuffled-label control, keeps rank 1 in
all 23 leave-one-domain-out drops, and was independently recomputed from the raw runs. The effect is small in
absolute terms: it restores 9% of what a whole-state rescue restores (candidate−KO 0.013 [0.007, 0.019]) — the claim is
specificity, not magnitude.
*Scope:* one codeword, one layer, the PLS activation-space family, semantic installation only. It re-analyses the same
validation split with a larger null — not a fresh population. Rank 4 was chosen on TRAIN, and ranks 2–3 were never
tested on validation, so this is **not** "button needs exactly 4 dimensions".

Basket's rank-1 carrier passes on validation and is robust to the option-mass rule, but it was never corrected for
basket's own three validation looks (corrected p 0.0525), so it is **suggestive, not confirmed**; a powered re-test is
preregistered and pending. The two codewords therefore differ in **whether a specific carrier is detected at rank 1**.
We **cannot** claim a dimensionality *contrast* between them: the corrected interaction changes sign depending on which
control family is used.

## The weight-level operator (Heretic's LoRA-operator idea, position-aware; MSE objective)

Fitting ΔW = B·A on attention/MLP write matrices at the codeword row rescues installation far beyond random edits of
equal rank and norm, and acts through the codeword row. (We kept Heretic's operator form and preserve/steer structure;
its own kNN steering objective lost our TRAIN cross-validation to plain paired MSE.) But on validation the preregistered outcome is **D**: basket is
specific only at rank 4 (a **marginal** pass — it loses the pass in 9 of 23 single-domain drops), button at neither rank.
Most of the rescue is reproduced by *any* operator fit to map knocked-out states to clean ones, regardless of domain
pairing; correct pairing adds at most +0.018. The rescue is flat from rank 1 to 50 while parameters grow 50× (TRAIN, in-sample, descriptive).
The most robust basket result is the codeword-row-only application (1st of 77, Holm 0.026, stable under
leave-one-domain-out), reported with its forking-path disclosure.

## Negative and null results (first-class)

- **Native Heretic ARA, as shipped, is not sufficient for codeword-specific installation** — it buys a largely
  context-insensitive answer-position bias (measured control).
- **"Basket just has a better probe" does not survive held-out testing** (and whether the two differ at all is
  cannot-answer with two codewords).
- **No detectable alignment** between the learned operators and the refusal direction, d_surface or the probe axes, at
  the sensitivity of a calibrated null.
- **The minimal-subspace (truncation) test is VOID** under its own preregistered reproduction check; we kept it void
  rather than re-preregister on data we had already seen.
- **The downstream behavioural question is CANNOT ANSWER / UNDERPOWERED**, declared before spending GPU: the validation
  split resolves ~0.09 while the plausible effect is ≤ 0.002 (~43k domains would be needed).

## Heretic itself (useful by-product)

Three findings from auditing the pinned release: its reset leaves one LoRA factor in place (so trials are
history-dependent and not exactly replayable), resuming a study re-draws trial 0, and with the default row-norm option
the deployed edit is not the one optimised (1–30% per module). Not reported upstream — your call.

## In flight

Head-restricted operators (fit-side, in-sample, 13–16 of 60 controls so far — not an endpoint; the preregistered
evaluation has not run and may differ) and the codeword-scaling stage (14 of 21 prepared codewords pass
the option-mass gate; 4 so far pass knockout liveness). Power there is tight by design: with ~15 confirmation
codewords — the ceiling — the population test has 0.57–0.72 power at ρ = 0.7. It is pre-labelled underpowered for
ρ < 0.8 if fewer than 15 survive and cannot-answer below 12; one more gate failure triggers the former.
