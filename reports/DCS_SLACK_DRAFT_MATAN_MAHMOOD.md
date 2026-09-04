# Slack draft — Matan & Mahmood (§47)

⛔ **DRAFT ONLY. NOT SENT.** No Slack integration is configured and none was used. Send only on
explicit instruction from Omer. Rewritten 2026-09-04 after the Qwen wave and both layer sweeps.

---

## Message 1 — the update

> Following up on the Sep 2 discussion. Headline: **the mechanism you asked about is real, causal and
> replicates across models — and it is not the thing the attack runs on.** Full log is append-only
> with every retraction kept in place; one figure summarises it.
>
> **What we changed after the discussion.** Dropped `d_surface` as the object of study and went back
> to the 2×2, with your `C − A` (same codeword, only the demonstrations change) as the primary
> candidate. Everything preregistered before any forward pass.
>
> **Did concept-specific Boombness work? No — and that's the first result.** Running the identical
> geometry on `knife`/`gun`/`club` banks, three of four comparisons go the *other* way, all inside
> the measured noise band. So it should not be called "Boombness": it is a property of the
> demonstration paradigm, not of `bomb`. It also **does not accumulate** — roughly one demonstration
> does the work, and the effect is flat in `n_examples`.
>
> **What is real is the causal path.** Blocking the query span from attending to the demonstrations
> takes the model's own forced-choice reading of `button` from **+5.19 to −2.76** log-odds — a sign
> flip back to the *literal* meaning — against a dose-matched control that does nothing. It
> **replicates on `basket`** and **on Qwen3-14B at ~3× the magnitude** (there `frac>0` collapses
> 0.813 → 0.021). And it is **remapping-specific**: the same cut barely moves the cell where the word
> already *is* `bomb`. DiD −9.9 / −9.4 / −22.2. ⚠ One caveat we put on the figure itself: all three
> share the same 1+/37− sign pattern, so those identical p-values are **one pattern replicated, not
> three independent tests**.
>
> **Where in the network.** We ran the layer sweep we'd been missing. At equal dose the effect is
> **distributed across layers 0–14, peaks at 10–14, and is absent above 14**. The L6–14 band we
> inherited from the last sprint contains the peak but is **not** the mechanism's boundary — layers
> 0–5 contribute substantially too.
>
> **Which token?** Neither the final `button` nor the readout row matters on its own (both null at
> the same dose). A **threshold of ~3–8 query rows** does, after which it saturates. So no single
> position carries the mapping.
>
> **The behavioural link is where we're stuck, and I want to be straight about it.** On Llama, cutting
> the path reduces attack **in direction** (≈ −30 of 153, consistent across 3 refusal-neutral controls
> × 2 seeds × 4 judgings) — but it **does not reach significance at the domain independence unit**,
> and 38 domains is **all that exists** in our pools, so no amount of further judging fixes it. On
> Qwen we **cannot answer at all**: 0 of 6 control draws meet refusal-neutrality, because our ±17-row
> band is an *absolute* judge-noise figure and Qwen's baseline is 150 refusals rather than 42 — a
> 3.6× stricter relative test. That is a limitation of our criterion, **not** evidence that Qwen shows
> no effect; we never computed an attack contrast there.
>
> **One thing that replicates everywhere:** refusal. Llama 42 → 0, Qwen **150 → 0** — and that is the
> same 150 the earlier sprint removed with a *different* scope. Two models, four scopes.
>
> **Two decisions I'd like your view on.**
> 1. **New demonstration pools.** The only way to certify the behavioural effect at our own
>    independence unit. New data, own preregistration, API budget. Worth it?
> 2. **Positioning.** The representational half **replicates Yona et al., ACL 2026** — they already
>    show the convergence with logit lens and Patchscopes, and their Appendix D anticipates the
>    codeword-generality point. Ours that is new is the **causal** half: they perform no internal
>    intervention. Frame as a causal follow-up to them, or hold?

## Message 2 — scheduling

> Could we get 30 minutes this week to decide the demonstration-pool question and how we position
> against the ACL 2026 paper?

---

## Notes for Omer before sending

* Every number is in `reports/DOUBLESPEAK_NEXT_PHASE_SUMMARY.md` with its artifact path; the figure
  is `reports/DCS_FIGURES.png` and carries its own scope card.
* ⚠ The message leads with the **negative** and states the behavioural limitation plainly. If you'd
  rather open with the cross-model replication, that's a presentation choice, not a factual one.
* ⛔ Do not let *"≈ −30 of 153"* travel without the sentence after it — alone it reads as an
  established behavioural effect, which is exactly what it is **not**.
* ⛔ Do not let the three DiD p-values travel as three independent results.
* Scope line if asked: **38 domains × 2 codewords × 1 concept × 2 model families.** That is 38
  *contexts* for a single mapping, not 38 mappings.
* If asked "what would change your mind": new pools (for the behavioural claim), a second harmful
  concept (for generality), and a relative refusal-neutrality band declared **in advance** (for Qwen).
