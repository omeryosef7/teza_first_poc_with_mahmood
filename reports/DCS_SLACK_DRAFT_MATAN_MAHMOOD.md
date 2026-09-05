# Slack draft — Matan & Mahmood (§47)

⛔ **DRAFT ONLY. NOT SENT.** No Slack integration is configured and none was used. Send only on
explicit instruction from Omer. Rewritten **2026-09-05 evening**, after the `K = 8`
control-distribution experiment finished (`PR-028`), the ten-arm single-session re-judge closed the
drift question, and the predicted-refusal route was closed. ⚠ Every earlier draft predates **all** of
that; in particular the previous one's central ask has since been **answered in the negative** and
must not be sent.

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
> a dose-matched control that does nothing; it **replicates on `basket`** and **on Qwen3-14B** — in
> sign and in the identical 1+/37− domain split — and it is **remapping-specific**. ⚠ I previously
> wrote "at ~3× the magnitude"; **that ratio is not claimable** and our own gate said so before we
> measured it: Qwen's baseline is ~2× Llama's over a more bimodal distribution, and the two runs are
> not dose-matched (91,872 mask cells over 11 layers vs 66,816 over 9). Cross-family in **direction**,
> not in size. ⚠ Same caveat as before, on the figure itself: all
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
> **The decision I asked about last time is now answered, and not the way either of us framed it.**
> I ran it: **78 new demonstration domains**, taking us from 38 to **116**, about 13.5 GPU-hours.
> Power at the domain unit went from **0.31 to a planned 0.81**. ⛔ **It still did not resolve**, and
> the reason is the useful part.
>
> We preregistered the strict version — significance against **all three** dose-matched controls, no
> picking. It came back **1 of 3**: p = **0.175 / 0.0096 / 0.466**. ⚠ I'm not quoting the middle one
> on its own; that is exactly the error we corrected earlier in the sprint.
>
> **Why it failed is not what I expected.** The clustering came in *better* than I assumed (ICC 0.09
> vs 0.16), but the baseline attack rate came in **20 % lower** than the number I sized on, so real
> power was **0.65 / 0.35 / 0.05** against the three observed effects — which is precisely the
> pattern we got. ⇒ **Domain count was never the binding constraint.**
>
> **What is — and we have now measured it properly, which changed the picture again.** The controls
> induce very different refusal loads, so each control's ASR is depressed by a different amount, and
> which control you pick decides your p-value (0.01 to 0.47 on identical data). On three draws that
> spread looked like 0.059 against an effect of 0.039. ⇒ So we stopped picking a comparator at all:
> we ran **eight** dose-matched draws and tested `KO-3` against the control **distribution**, with
> the between-control sd as the error term. **~10 GPU-hours, and all ten arms re-judged in a single
> session** so no cross-session offset could land on it.
>
> **Result: δ = −0.0222, t(7) = −0.80, p = 0.449 — and it is an UNDERPOWERED negative, not a clean
> one.** The realised between-control sd came in at **0.0783**, **2.65×** what we sized on, so the
> minimum effect we could have detected (**0.0655**) is **larger than the effect we were looking for**
> (0.0391). Real power was **0.23**. ⛔ So this is **not evidence of absence** and we are not
> reporting it as one.
>
> **The reason is the finding, and I think it's the most interesting thing in the sprint.**
> **Dose-matched controls are not an exchangeable population.** At *identical* dose — same number of
> masked keys (522), same match ratio (1.000), verified on all eight — induced refusal ranges from
> **−7 to +562**, a **25-fold** spread, and ASR from **0.126 to 0.374**. We checked the extreme arm
> for a defect and it has none. ⇒ **Which positions you mask dominates behaviour at constant dose.**
> The "dose-matched control" is not one intervention with noise; it is a **family of very different
> interventions**.
>
> **On the direction, I went back and forth twice, so here is the settled version.** Our
> refusal-adjusted bracket credits the control with **every** induced refusal as a would-be attack —
> but the conversion we actually measure is **6–35 %**, so that end over-credits by 3–17×. The
> face-value end has the opposite fault: it never debits `KO-3` for clearing **all 144** refusals,
> which by the same mechanism handed it attacks. ⇒ **Both ends are biased, in opposite directions.**
> Applying the measured conversion **symmetrically** gives **[−147, −66] / [−140, −87] / [−129, −29]**
> — entirely negative for all three controls and half the width of the original bracket. ⇒ The
> direction is **well supported**; ⛔ it is still **not** the certified result, because our
> preregistration ties that to the primary, which is 1 of 3.
>
> ⇒ **Last time I said the question was "can we build controls matched on induced refusal?" We tried,
> and that route is now closed — so the ask has changed.** Selecting on *observed* refusal is post-hoc
> (we retracted that once already). Matching on *predicted* refusal needs a predictor, and we went
> looking: mask geometry predicts induced refusal neither **within** draws (7 features, 8 draws, sign
> test that could have concluded — 0 of 4 consistent) nor **between** them (best ρ = 0.24, n = 8).
> ⚠ Bounded honestly: at n = 8 we could only have caught |ρ| ≳ 0.71, so this closes *that feature
> set*, not the idea.
>
> ⇒ **The real question, and what I'd like the 30 minutes for: do we keep buying draws, or change the
> estimand?** I have **24 more draws running now** (K = 32, ~55 GPU-h), which is powered **0.78** for
> the effect we hypothesised (−0.039) but only **0.34** for the one we actually observed (−0.022).
> Detecting −0.022 would need **K ≈ 105**, roughly 240 GPU-hours — which I don't think is a
> proportionate spend. ⇒ So either the behavioural claim rests on a test we can afford to run, or we
> attack the **variance** rather than the sample size, or we reframe the paper around the
> **representation/behaviour dissociation** — which is what the data actually supports.
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
* If asked "what would change your mind": ⛔ **not new pools** (we ran 116 domains; `k` was never the
  constraint) and ⛔ **no longer "controls matched on induced refusal"** — we tried and there is no
  predictor to match on (mask geometry fails within and between draws). What remains: **a second
  harmful concept at adequate power** (generality was mixed, 1 of 2), and **an estimator that
  differences out the refusal nuisance** rather than averaging over it. ⚠ The low-dose question is
  **closed**: we built the bank, both gates passed, and the continuous gradient still failed.
* ⛔ **Do not let the K = 8 null travel as "the attack doesn't work."** It is an *underpowered*
  negative — our own minimum detectable effect was larger than the effect sought. The correct
  sentence is "the behavioural effect is **not established**, and is bounded below ~0.066."
* ⚠ One methods note worth adding if they ask about the judge: re-judging **5800 byte-identical rows**
  flips **12.6 %** of attack labels but the **net** is −54, i.e. session drift is **not established**
  (arm-level p = 0.17, CI spans zero). The **refusal** label flipped **0 of 5800**.
