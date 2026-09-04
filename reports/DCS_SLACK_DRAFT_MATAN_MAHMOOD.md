# Slack draft — Matan & Mahmood (§47)

⛔ **DRAFT ONLY. NOT SENT.** No Slack integration is configured and none was used. Send only on
explicit instruction from Omer. Rewritten **2026-09-04 evening**, after the generality run closed,
the Qwen behavioural analysis completed, and the installation result was audited three times and
narrowed. ⚠ The previous draft (09:49) predates **all** of that and must not be sent.

---

## Message 1 — the update

> Following up on the Sep 2 discussion. Headline unchanged: **the mechanism you asked about is real,
> causal and replicates across models — and it is not the thing the attack runs on.** What's new is
> that we spent today attacking our own results, and two of them got smaller. Full log is
> append-only with every retraction kept in place; one figure summarises it.
>
> **Did concept-specific Boombness work? No — and that's still the first result.** On
> `knife`/`gun`/`club` three of four comparisons go the *other* way, all inside the measured noise
> band. New this week, the same point **positively**: run the identical paradigm with **benign**
> demonstrations ("a large crate of *button* puree") and the model installs a **benign** remapping —
> it answers ` Mushroom` on 22 of 380 rows and ` Bomb` on 3. ⇒ The paradigm installs **whatever the
> demonstrations say**. Nothing about it is specific to harm.
>
> **The causal path is the solid result.** Blocking the query span from attending to the
> demonstrations takes the forced-choice reading of `button` from **+5.19 → −2.76** log-odds against
> a dose-matched control that does nothing; it **replicates on `basket`** and **on Qwen3-14B at ~3×**
> the magnitude, and it is **remapping-specific**. ⚠ Same caveat as before, on the figure itself: all
> three share the 1+/37− sign pattern, so those identical p-values are **one pattern replicated, not
> three independent tests**. We also now have the missing reference cell: with the codeword present
> but **no** remapping installed, the reading sits at **−5.50**, so the demonstrations move it
> **+10.7 log-odds**. That's the first measurement of *installation* rather than its removal.
>
> **Generality across harmful concepts: MIXED, 1 of 2 — and we're reporting it as mixed.**
> `lantern`→`poison` **passes** the preregistered test (0+/20− domains, p at the attainable floor);
> `candle`→`missile` **fails** (6+/14−, p = 0.115). ⛔ Neither bank can carry a dose-matched control
> — they have no preamble, so the prompt is ~85 % demonstration and the control has nothing to draw
> from. So generic attention damage is **excluded on `bomb` and inherited, not re-verified, there.**
>
> **The result we spent the day on, and how it shrank.** We found that the knockout's effect is
> bigger in domains where more of the remapping was installed to begin with. Initially that looked
> like a clean dose-response. ⚠ **It isn't, and we broke it ourselves.** Three audits later:
> * ✅ **What survives:** the effect is **larger in fully-installed domains than in
>   partially-installed ones** — categorical, robust to leave-one-out and to three different ways of
>   measuring "installed", across **4 settings and 2 models**.
> * ⛔ **What doesn't:** there is **no continuous gradient within the partially-installed range**. We
>   tested it three times (13, 30 and **33** domains) and it fails every time — the last on a bank we
>   **built specifically** to supply that range.
> * ✅ **And we can say why**, which is the part worth reading: on that new bank the *control* arm's
>   gradient moves **−0.09 → −0.34** purely by restricting to the varying domains, **with no knockout
>   applied at all.** That's regression to the mean, shown inside a single arm. Within that range both
>   arms are measuring RTM; across the full range they diverge because the knockout does something
>   the control doesn't.
>
> **Qwen behavioural — answered, and the answer is "confound-limited".** All 8 arms judged in one
> invocation. Face value says `KO-3` has *more* attacks than every control (+23…+45, all
> significant); correcting for the fact that every control induces ~50 extra refusals says *fewer*
> (−11…−32). **All six brackets straddle zero.** ⛔ So we cannot sign the effect — and note that is
> **not** "Qwen shows no behavioural effect", which remains unsupported. ✅ One judge-free fact does
> survive intact and I think it's the interesting one: `KO-3` removes **all 150** refusals and buys
> only **+21** attacks. **86 % of removed refusals do not become attacks.**
>
> **Two methods notes you'll want if you use the same judge.** (1) `temperature 0` is **not
> deterministic** on the OpenAI endpoint — we caught it because a refactor made us re-run a published
> result and it came back different. (2) We measured the judge's own noise floor on the attack rubric:
> **18 of 380 labels** flip on a byte-identical re-judge (net +6), while the **refusal** label flips
> **0 of 380**. Small enough that it doesn't explain the Qwen result.
>
> **One decision I'd like your view on** (the other one from last time is now closed — we built the
> low-dose bank ourselves and it settled the question). **New demonstration pools.** Still the only
> way to certify the behavioural effect at our own independence unit: 38 domains is **all that
> exists** in our pools, so no amount of further judging fixes it. Cost is **GPU time and a design
> decision**, not money — judging is ~**$0.08 per 380-row arm**. The real question is whether new
> domains should extend to a **second harmful concept** (generality + power together) or just deepen
> `bomb` (power only). Given `candle`→`missile` failed, I lean toward generality — but that's exactly
> what I'd like to argue about.
>
> **Positioning, unchanged.** The representational half **replicates Yona et al., ACL 2026**; ours
> that's new is the **causal** half — they perform no internal intervention. Frame as a causal
> follow-up, or hold?

## Message 2 — scheduling

> Could we get 30 minutes this week to decide the demonstration-pool question and how we position
> against the ACL 2026 paper?

---

## Notes for Omer before sending

* Every number is in `reports/DOUBLESPEAK_NEXT_PHASE_SUMMARY.md` with its artifact path; the figure
  is `reports/DCS_FIGURES.png` and carries its own scope card.
* ⚠ The message leads with the **negative** and states both live limitations plainly. Opening with
  the cross-model replication instead is a presentation choice, not a factual one.
* ⛔ **Do not let the installation result travel as a "dose-response" or a "gradient."** It is
  **categorical**. The continuous version was tested three times, including on a bank built to
  provide it, and is explained by regression to the mean. ⚠ An earlier version of this draft would
  have quoted a contrast of −0.907; that number is **population-specific and inflated** and must not
  be sent.
* ⛔ Do not let *"≈ −30 of 153"* (Llama attack) travel without the sentence after it.
* ⛔ Do not let the three DiD p-values travel as three independent results.
* ⛔ Do not let *"86 % of removed refusals do not become attacks"* be read as an attack **contrast** —
  it is a baseline-vs-`KO-3` count inside one judging invocation, which is precisely why it survives
  the confound that kills the contrast.
* Scope line if asked: **38 domains × 2 codewords × 1 concept × 2 model families × 4 doses.** That is
  38 *contexts* for a single mapping, not 38 mappings.
* If asked "what would change your mind": **new pools** (the behavioural claim) and **a second
  harmful concept at adequate power** (generality — the one we ran was mixed). ⚠ The low-dose
  question is **closed**: we built the bank, both pre-registered gates passed, and the continuous
  gradient still failed. That one is settled, not pending.
