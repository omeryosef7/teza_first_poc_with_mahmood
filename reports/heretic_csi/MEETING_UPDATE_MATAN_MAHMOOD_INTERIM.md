# HERETIC × CSI — interim update (2026-10-15)

Only defensible results. Scope caveats are part of each claim. Full detail: `HERETIC_CSI_FINAL_REPORT_INTERIM.md`;
verification: `VERIFICATION_INDEX.md`.

## Headline (new, confirmed)

**Button has a specific rank-4 semantic-installation carrier at L18, where its rank-1 direction has none.**
Preregistered, held out (23 validation domains), ranked 1st of 201 rank- and norm-matched controls (p = 0.005),
Holm-corrected over all three declared validation looks (0.0149), beats every shuffled-label control, keeps rank 1 in
all 23 leave-one-domain-out refits, and was independently recomputed from the raw runs.
*Scope:* one codeword, one layer, the PLS activation-space family, semantic installation only. It re-analyses the same
validation split with a larger null — not a fresh population. Rank 4 was chosen on TRAIN.

With basket's rank-1 carrier (validation pass, sensitive to the option-mass rule), the two codewords differ in
**whether a specific carrier exists at rank 1**. We **cannot** claim a dimensionality *contrast* between them: the
corrected interaction changes sign depending on which control family is used.

## The weight-level operator (Heretic's ARA idea, position-aware)

Fitting ΔW = B·A on attention/MLP write matrices at the codeword row rescues installation far beyond random edits of
equal rank and norm, and acts through the codeword row. But on validation the preregistered outcome is **D**: basket is
specific only at rank 4 (a **marginal** pass — it loses the pass in 9 of 23 single-domain drops), button at neither rank.
Most of the rescue is reproduced by *any* operator fit to map knocked-out states to clean ones, regardless of domain
pairing; correct pairing adds at most +0.018. The rescue is flat from rank 1 to 50 while parameters grow 50×.
The most robust basket result is the codeword-row-only application (1st of 77, Holm 0.026, stable under
leave-one-domain-out), reported with its forking-path disclosure.

## Negative and null results (first-class)

- **Native Heretic ARA, as shipped, is not sufficient for codeword-specific installation** — it buys a largely
  context-insensitive answer-position bias (measured control).
- **"Basket just has a better probe" does not survive held-out testing.**
- **No detectable alignment** between the learned operators and the refusal direction, d_surface or the probe axes, at
  the sensitivity of a calibrated null.
- **The minimal-subspace (truncation) test is VOID** under its own preregistered reproduction check; we kept it void
  rather than re-preregister on data we had already seen.
- **The downstream behavioural question is CANNOT ANSWER / UNDERPOWERED**, declared before spending GPU: the validation
  split resolves ~0.09 while the plausible effect is ≤ 0.002 (~43k domains would be needed).

## Heretic itself (useful by-product)

Three defects found by auditing the pinned release: its reset leaves one LoRA factor in place (so trials are
history-dependent and not exactly replayable), resuming a study re-draws trial 0, and with the default row-norm option
the deployed edit is not the one optimised (1–30% per module). Not reported upstream — your call.

## In flight

Head-restricted operators (fit side so far suggests the inherited 8-head set is **not** distinctive versus random
8-head sets; evaluation preregistered, not yet run) and the codeword-scaling stage (14 of 21 prepared codewords pass
the option-mass gate; 4 so far pass knockout liveness). Power there is tight by design: with ~15 confirmation
codewords the population test has 0.57–0.72 power at ρ = 0.7, and it is pre-labelled underpowered below that.
