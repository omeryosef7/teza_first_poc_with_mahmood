# Slack draft — Matan & Mahmood — 2026-09-06

⛔ **DRAFT ONLY. NOT SENT.** No Slack send was attempted, no email, no calendar change. Send only on
Omer's explicit instruction.

⚠ **Written while the concept-specificity primary (`PR-035`) is still running** as job `854173`.
Every number below is from a *completed and independently verified* result. ⛔ There is **no**
Bombness verdict in this draft, because there is not yet one to report — and §38's question 1 is
answered *"still running"*, not guessed.

Supersedes `reports/DCS_SLACK_DRAFT_MATAN_MAHMOOD.md` (2026-09-05). ⛔ That draft is **not** to be
sent: its K-ladder paragraph is superseded by `R-079`/`R-080` below.

---

## Message 1 — the update

> Quick update, and one ask at the end.
>
> **The surgical knockout you asked for is done, and it landed somewhere more interesting than we
> expected.** We ran the missing rungs K=3…7 and then found something that reframes the whole
> ladder: `query_last_k_rows` counts back from the end of the **whole chat-templated prompt**, so
> the rungs we had been calling "one or two query rows" were cutting **Llama's own generation-header
> scaffold** — `\n\n`, `<|end_header_id|>`, `assistant`, `<|start_header_id|>`, `<|eot_id|>`. That's
> K=1 through K=5. Verified over all 380 prompts with zero variation.
>
> With that in hand the profile is very clean:
>
> ```
> K=1..5  scaffold only        ≤ 1.1 % of the full effect
> K=6     '?'                    7.6 %
> K=7     ' bomb'               90.5 %      <- 82.9 points in one token
> K=8                          100 %
> ```
>
> So: **the demonstration→query pathway is not needed by the template scaffold at all; the
> requirement appears exactly where the cut reaches the question's content, and it is a step, not a
> ramp.** We preregistered that prediction *before* reading K=4…7 and it held on all three parts.
>
> **The honest catch, which we wrote down before seeing the numbers:** the token at K=7 is `' bomb'`
> only because the forced-choice question names both options. So this is not yet a statement about
> the codeword — it may be a statement about the readout template. We ran the same ladder on a
> question that never names the concept (`semantic_one_word`, where the codeword sits at K=10).
> Result: adding the codeword's own row takes the effect from 47 % to 95 %, **6/6 domains, at the
> exact p-floor the design allows** — but our preregistered bar was 50 % of the full-query effect and
> we measured **48.1 %**. So it is formally **CANNOT ANSWER**, by 1.9 points. We are not moving the
> bar.
>
> That result also **corrects one of our own**: we had said the codeword's query row isn't necessary
> (`KO-1`). That's true on the forced-choice template and **false** on this one — the codeword row
> alone carries a third of the effect there. `KO-1`'s null is now bounded to its template.
>
> **Concept-specific Bombness (`PR-035`) is running now.** Before we could run it we had to throw a
> lot away: the analyzer didn't actually implement its own preregistration, it joined hidden states
> on an ID that collides across all eight banks, and the blocking null wasn't computing the declared
> statistic. All fixed and frozen before the run. We'll have a verdict for you shortly.
>
> **Two literature items you should see, one of them urgent-ish.** First, arXiv 2504.00132
> (Bakalova et al.) already ablates demonstration→query attention edges in ICL — so "first to
> causally intervene on that pathway" is off the table, and we've narrowed the novelty sentence
> accordingly. Second, **arXiv 2609.02438 went up on Sep 2** and publishes the
> representation-vs-behaviour dissociation framing in almost exactly our design shape (probe
> generalises across held-out templates/domains; interventions along the probe direction no stronger
> than random controls). It doesn't scoop us — different property, no attack, no attention
> intervention — but if we lead with dissociation, that's now a citation rather than a contribution.

## Message 2 — the ask

> Could we get **30 minutes this week**? Two decisions are genuinely yours, not ours:
>
> 1. **Which half leads.** Given 2609.02438, does the paper lead with the *causal attention
>    mechanism* (where our K-ladder threshold has no precedent we can find) or with
>    *representation vs behaviour* (where we'd now be one voice among several)?
> 2. **Whether to fund the aligned rebuild.** The concept-specificity question keeps running into the
>    same wall — cell `A` is a different corpus in every concept bank, and cells `C` and `F` sit in
>    disjoint template blocks. A properly aligned bank would fix it; it's real GPU time and it
>    changes the population, so we're not starting it unilaterally.

---

## The seven questions in §38, answered directly

| # | question | answer as of 2026-09-06 |
|---|---|---|
| 1 | Did we get a genuinely concept-specific Bombness measure? | ⚠ **UNKNOWN — `PR-035` is running (job 854173).** Not guessed. |
| 2 | Which validation gates passed/failed? | Of §12's `R1`–`R8`: none are yet adjudicated for Bombness. The `PR-034` **installation gate** passed for `bomb`/`knife`/`club` and was **PARTIAL** for `gun` (4/6 domains). |
| 3 | What happened under `KO-3`? | Unchanged and inherited: `+5.19 → −2.76`, replicated on `basket`, direction-replicated on Qwen. ⛔ Not re-run this session. |
| 4 | What happened under the surgical K=3…7 test? | ✅ **`R-080`/`R-081`, independently verified.** `K* = 7`, `shape = STEP`, and rungs 1–5 cut only chat scaffold. |
| 5 | Does Bombness destruction predict mapping use / ASR? | ⛔ **Not addressed this session** — it is gated behind `PR-035`. Inherited status stands: `R-075` is an **underpowered negative**, never "no effect". |
| 6 | What do we recommend next? | (a) finish `PR-035` + its primary-recomputing verifier; (b) put the §34.4 content-word hypothesis in its **own** preregistration or drop it; (c) get a decision on the aligned rebuild. |
| 7 | New overlapping literature? | ✅ **Yes, five works** (`A-025`). Two matter: **2504.00132** narrows the intervention novelty; **2609.02438** (Sep 2) publishes the dissociation framing. |

## ⛔ Sentences that must NOT appear in any message

* *"We are the first to causally intervene on demonstration→query attention in ICL."* — **false**
  (`2504.00132`).
* *"The codeword's query row is not necessary."* — **template-bounded** (`C-054`), false as stated.
* *"K=1 and K=2 show one or two query rows don't matter."* — **false** (`R-079`); those are scaffold.
* *"48.1 % is essentially 50 %, so it's the codeword row."* — the goalpost move `R-083` refused.
* *"`KO-3` restores the literal meaning."* — **Qwen only** (`R-032`).
* Any Bombness verdict at all, until `PR-035` returns **and** its primary is independently recomputed.
