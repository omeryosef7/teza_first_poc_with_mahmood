# Slack draft — Matan & Mahmood — 2026-09-06 (FINAL)

⛔ **DRAFT ONLY. NOT SENT.** No Slack send was attempted, no email, no calendar event. Send only on
Omer's explicit instruction.

⛔ **Supersedes `reports/DCS_SLACK_DRAFT_MATAN_MAHMOOD_20260906.md`, which is now FALSE and must not
be sent.** That draft says *"`PR-035` is running, we'll have a verdict shortly"*. `PR-035` returned,
was overturned by us on a sign error, and was restored on a measured false-positive rate. It also
predates gates `R3` and `R5` entirely. Full current state:
`reports/DCS_SPRINT_SUMMARY_20260906.md` (revised 2026-09-06, now covering log §§1–71 — it did not
originally carry §§65–71, and §§4.4–4.7 there change what §4.2's headline is allowed to say).

---

## Message 1 — the dissociation

> Two results since we last wrote, and the second one is the interesting one.
>
> **1. The concept probe is positive and holds up.** A linear probe on the codeword's L6–14 hidden
> state says which of bomb / knife / gun the demonstrations installed: **0.7485 vs 0.333 chance,
> 6/6 held-out domains**, permutation p = 0.005 from a test we *measured* to reject noise at 0.030.
> The bomb-absent control (knife vs club, similar install strengths, no bomb anywhere in the
> contrast) also separates, so it is concept **identity**, not just how hard the codeword got
> remapped. Reproduced four independent times — three of them to all 16 digits, the fourth
> (a different permutation seed) matching inside its stated Monte-Carlo band. ⚠ The p = 0.005 **is
> the attainable floor** at 200 permutations, not a measured tail.
>
> **2. Then we knocked the pathway out — and the probe barely moved.** Same bank, same L6–14 band,
> same whole-query `demo_all` knockout:
>
> ```
> readout   (semantic_logodds)   +3.37  ->  -3.02     sign flip, -6.38
> probe     (which concept)      0.7529 ->  0.7047    94% retained
> ```
>
> The knockout **destroys the model's ability to report the mapping and leaves which concept was
> installed decodable from the codeword's hidden state.** Formally `R5-FAIL` — 5/6 domains, drop is
> 11.5% of what was available against a 20% bar. **This is an informative negative:** the floor was
> 0.031 and the design could have cleared it. The bridge validated itself first — knockout-disabled
> reproduces the published 0.7485 at 0.7529, against a 0.10 void bar.
>
> ⚠ **One correction we have to make ourselves, since we found it after writing the above.** At the
> layer this actually reads — every fold picks L6, the **first** layer of the 6–14 band — a
> whole-query knockout and a knockout of *only the codeword's own row* are **arithmetically
> identical at the read site** (we measured it: max elementwise difference 0.000e+00 over 2520
> rows). So the honest sentence is *"blocking the codeword row's own view of the demonstrations
> leaves the representation 94 % decodable"* — the verdict stands, the phrase "the whole pathway"
> does not. Re-read on layers 7–14, where the two scopes genuinely differ, the whole-query knockout
> removes 10.6 % of available accuracy and the codeword-row-only one 5.5 %. **The dissociation
> survives; our description of it needed narrowing.**
>
> Two honest bounds on that. It is **representation vs readout**, not representation vs behaviour —
> the behavioural half (PHASE 7) is still unrun, and those two rows are different instruments at
> different sites (a generated answer vs a probe on hidden states). And **the probe result was never
> causal to begin with**; this is what "decodable" not implying "used" looks like in our own data.
>
> Also worth knowing, both with caveats attached: the remapping axis and the concept axis turn out to
> be **different directions** (raw diff-in-means AUROC 0.9987 for "was it remapped?" but 0.574 for
> "which concept?"; residualize it and that inverts to 0.896) — which retroactively explains our old
> `R-002` negative: it was measuring the wrong axis, not the wrong effect. And the **lexical-transfer
> gate `R3` fails**: a button-trained classifier tested on basket lands at 0.396 vs 0.333 chance.
> ⚠ But the *direction* transfers fine — macro AUROC **0.795** on the same classifier. What does not
> transfer is the decision offset. We are **not** switching to AUROC to rescue the gate; the gate
> fails on the statistic we preregistered. Both halves have to be quoted together or the sentence
> comes out false.

## Message 2 — the ask

> Could we get **30 minutes this week**? Three things are genuinely your calls, not ours:
>
> 1. **Positioning (`Q-002`).** **arXiv 2609.02438 went up on Sep 2** and publishes the
>    representation-vs-behaviour dissociation framing in almost exactly our design shape. It doesn't
>    scoop us — logical validity not concept remapping, no attack, no attention intervention — but if
>    we lead with dissociation it's now a *citation*, not a *contribution*. Do we lead with the causal
>    attention mechanism instead (our K-ladder threshold has no precedent we can find), or with the
>    dissociation and cite them? Related: arXiv 2504.00132 already ablates demo→query edges in ICL, so
>    that novelty sentence is narrowed for the second time.
> 2. **The scratch purge (`Q-003`).** `/vol/scratch/omeryosef` was purged mid-session; the Llama
>    weights lived only there, and the project's `.cache/huggingface` symlink points into it, so every
>    GPU job died on a misleading `mkdir: File exists`. Nothing was invalidated and we re-downloaded —
>    but scratch is purged **by policy**, so this recurs. Move the cache somewhere durable, or add a
>    symlink pre-flight to the shared wrapper? We didn't repoint shared infrastructure on our own.
> 3. **Control draws (`Q-004`).** We found the dose-matched control's masks are **not row-independent**
>    — one RNG seed per arm, so every row of an arm gets literally the same slots (Jaccard 2× the
>    row-independent null, 8/8 arms). Nothing is invalidated, but the spread across the 8 arms is
>    **not an error bar**. Going forward: re-seed per row so arms are exchangeable, or keep it fixed
>    and report the spread as systematic? It changes what "a control draw" means for the whole
>    behavioural half.

---

## ⛔ Sentences that must NOT appear in any message

* ⛔ *"We are the first to causally intervene on demonstration→query attention in ICL."* — **false**;
  arXiv **2504.00132** (Bakalova et al.) does it.
* ⛔ *"The model represents the codeword as BOMB"*, unqualified — it is *the state of **this**
  codeword, in **this** lexical setting, carries which concept was installed*.
* ⛔ *"The concept signal does not transfer across codewords."* — **`C-066` refutes it.** The direction
  transfers (AUROC 0.795); only the decision offset does not.
* ⛔ *"`KO-3` restores the literal meaning."* — **Qwen only** (`R-032`).
* ⛔ **Any causal reading of `R-086`.** It is decodability — and `R-093` shows it **survives** the
  knockout that destroys the readout.
* ⛔ *"The knockout does nothing."* — it flips the semantic readout **+3.37 → −3.02**.
* ⛔ *"`PR-035` is still running."* — it returned, was overturned on our own sign error, and was
  restored (`R-089`).
* ⛔ *"The gates passed."* — `R3` **fails**, `R5` **fails**, `R6` and `R8` are **CANNOT ANSWER**
  (not unrun, and not null); the §12 gate family cannot be reported as fully passed.
* ⛔ *"Gate `R6` passed / was null."* — its instrument was **degenerate at the layer it read**
  (`C-068`), and the layers-7–14 re-read carries **no p-value**.
* ⛔ *"`R8` shows destruction doesn't predict behaviour."* — **no behavioural outcome exists on that
  bank**, and power under a *perfectly monotone* truth is **0.25**. ρ = +0.60 was computed and is
  **not citable in either direction**.
* ⛔ *"Bomb installs ~3× harder than any hard negative."* — **2.03×** against club, which is exactly
  why club is the control.
* ⛔ *"Cell `A` is a different corpus in each concept bank"*, unqualified — it holds modally, not
  universally (`C-060`).
* ⛔ *"K=1 and K=2 show one or two query rows don't matter"* and *"the codeword's query row is not
  necessary"* — both false as stated (`R-079`; `C-054`/`R-083`).
* ⛔ *"48.1 % is essentially 50 %, so it's the codeword row."* — the goalpost move `R-083` refused.
* ⛔ *"Gun does not remap."* — it installs **inconsistently across domains** (4/6).
