# Slack draft — Matan & Mahmood (§47)

⛔ **DRAFT ONLY. NOT SENT.** No Slack integration is configured and none was used. Send only on
explicit instruction from Omer.

---

## Message 1 — the update

> Following up on the Sep 2 discussion. Short version: we built the concept-specific measurement you
> asked for, and the honest answer is that the representation is real and demonstration-caused but
> **not** concept-specific, and whether it drives the attack is still open.
>
> **What we changed after the discussion.** Dropped `d_surface` as the object of study and went back
> to the 2×2 as you suggested. The primary candidate was your `C − A` (same codeword `button`, only
> the demonstration context changes). Everything was preregistered before any forward pass, and the
> log is append-only with every retraction kept in place.
>
> **Did the concept-specific Boombness work?** Partly, and the negative is the interesting half.
> A codeword→concept movement exists and is **causally demonstration-dependent**: blocking the
> query span from attending to the demonstrations (L6–14) takes the model's own forced-choice
> reading of `button` from **+5.19 to −2.76** log-odds — a sign flip back to the *literal* meaning —
> against a dose-matched control that does nothing. It **replicates on `basket`** (+6.79 → −3.80),
> and it is **remapping-specific**: the same intervention barely moves the cell where the word
> already *is* `bomb` (DiD −9.89 and −9.35, 37/38 domains, p = 2.8e-10).
> ⛔ **But it is not specific to the harmful concept.** Running the identical geometry on
> `knife`/`gun`/`club` banks, three of four comparisons go the *other* way — every difference sits
> inside the measured noise band. So it should not be called "Boombness"; it is a property of the
> demonstration paradigm, not of `bomb`. It also **does not accumulate**: one demonstration does
> essentially all the work, and the effect is flat in `n_examples`.
>
> **The surgical final-`button`→demos knockout.** Null on everything we care about. The mapping
> stays intact (+0.28) and attack is unchanged (+11 rows, McNemar p = 0.38) — with a control we
> verified is refusal-neutral (refusal 42 vs 42, zero attack→refusal conversions). What it *does* do
> is **halve refusal**. So cutting that one token off the demonstrations changes neither the
> representation nor the attack.
>
> **The direct-`bomb` control.** ⛔ On the ASR endpoint it **cannot answer** — `direct_harmful`
> baseline is 10/380, so the largest possible effect is smaller than the judge's own noise band.
> That was my planning error; I moved the specificity test to the semantic readout, where the cell
> is not at floor, and that is where the DiD above comes from.
>
> **Is it Doublespeak-specific or generic context disruption?** Specific — but at the *path* level,
> not the single-token level. The whole-query-span knockout is remapping-specific on two codewords;
> the single-codeword-row knockout is a clean null. Both are true and the difference is the result.
>
> **The one thing I do not have.** Whether destroying the mapping moves the attack. We ran it, I
> reported a null, and an adversarial audit **retracted it**: I used a domain sign test on
> row-paired data (its MDE was a 43 % reduction), and the dose-matched control turned out to
> suppress attack *by inducing refusal* — a channel the treatment annihilates to zero, so the
> subtraction removes a mechanism the treatment cannot express. Corrected, the estimate is bounded
> on **[−15, −40] rows**, defensible point estimate **−34 (McNemar p = 0.005)**. Status:
> **cannot answer** until we have a control verified refusal-neutral at that dose. Three more draws
> are running; the diagnostic says the induction is a *dose* effect, so a neutral control may not
> exist in that pool — which would itself be the answer.
>
> **Two decisions I would like your view on.**
> 1. If no refusal-neutral control exists at that dose, do we (a) accept a refusal-stratified
>    estimate with its assumption stated, or (b) redesign the control (e.g. block a random *subset
>    of demonstration* keys rather than non-demonstration keys)? I lean (b).
> 2. The representational half replicates **Yona et al., ACL 2026** — they already show the
>    convergence with logit lens and Patchscopes, and their Appendix D anticipates the
>    codeword-generality point. Our novelty is the **causal** half (no internal intervention in that
>    paper). Do we frame this as a causal follow-up to them, or hold for the mediation answer?

## Message 2 — scheduling

> Could we get 30 minutes this week to decide the mediation-control design and how we position this
> against the ACL 2026 paper?

---

## Notes for Omer before sending

* Every number above is in `reports/DOUBLESPEAK_NEXT_PHASE_SUMMARY.md` with its artifact path.
* ⚠ The message deliberately leads with the negative (`not concept-specific`) and states the
  retraction in the middle rather than burying it. If you would rather it opened with the
  replication, that is a presentation choice, not a factual one.
* ⛔ Do not let the `−34 rows, p = 0.005` figure travel without the sentence that follows it. On its
  own it reads as a positive mediation result, which is exactly what is **not** established.
* Scope line if asked: 38 domains × 2 codewords × 1 concept × 1 model (Llama-3.1-8B-Instruct) ×
  one layer band. That is 38 contexts for a single mapping, not 38 mappings.
