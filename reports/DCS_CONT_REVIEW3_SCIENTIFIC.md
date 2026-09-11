# DCS continuation — REVIEW-3, SCIENTIFIC dimension

**Reviewer brief.** Adversarial review of the science only — do the conclusions follow, are they
interesting, are they honestly stated. Scope is **what landed since REVIEW-2**: `CONT-ENTRY 068–082`
and the rebuilt `reports/DCS_CONT_CLAIM_TABLE.md`. `reports/DCS_CONT_REVIEW2_SCIENTIFIC.md` was read
first so its findings are not re-reported; where I extend one I say so.

**Discipline observed.** No experiment run, no SLURM job submitted, no GPU used, no FROZEN config
edited. Everything below is derived from the record, from four committed artifacts
(`reports/DCS_CONT_S15_{MATCHED_REFERENCE,CROSS_CODEWORD,GUN_CONTROL,KNIFE_CONTROL}.json`), from
`outputs/boombness/g1_wholeanswer_sow.json`, from three `score_behavior` readout runs, and from
`src/boombness/aggressive_patching.py` / `signals.py`.

⚠️ **One disclosure.** My first pass over the readout runs filtered on the row field `split`, which in
those files carries `dev`/`heldout` (the demonstration pool), **not** the domain split — so that pass
included test-domain rows. Every number reported below is recomputed against
`data/boombness_prompts/dcs_ts116_domain_split.json`, restricted to the **93 non-test domains**. The
quantity involved is `option_mass`, an instrument-health diagnostic on a pre-existing readout run from
an earlier phase; it selects no candidate and confirms no hypothesis, which is the category
`CONT-ENTRY 066` already adjudicated as permissible for the C-209 re-score. Recording it anyway.

---

## VERDICT

This is the strongest stretch of the phase and it contains its first genuinely interesting positive
result, and both of those facts make the overclaims in it more dangerous rather than less. `A13` — the
§15 matched reference — is a real finding with a coherent mechanistic reading, better controlled than
`F5` in the one way that matters (its `A` reference correlates *negatively*, so this is not "any
function of the demonstrations predicts its own outcome"), and it deserves to be the phase's headline.
But **its three most quotable numbers are not robust to choices the record made silently and never
justified.** The headline `+0.4053` is `ρ_B − ρ_ctx` where `ctx = mean(A,E)` and `ρ_A = −0.192`,
`ρ_E = +0.223`: the baseline sits near zero by *cancellation of two opposite-signed references*, not
because the context carries no signal. Recompute the same effect as the pure surface contrast
`ρ_E − ρ_A` — both references benign-context, differing only in whether the concept word or the
codeword occupies the position, which is the comparison §15 actually names — and bomb gives `+0.4148`,
knife `+0.1867`, gun `+0.0829`. The bomb/knife ratio that `CONT-ENTRY 082` reports as **6.5×** is
**2.2×** under that contrast and **3.4×** under `ρ_B − ρ_A`. Against a 1.63× variance deficit, the
residual "bomb is special" factor is therefore somewhere between **1.4× and 4.0× depending on which of
four equally-available contrasts you report**, and the record reports the one that maximises it while
asserting *"Variance loss of 1.6× cannot produce an effect loss of 6.5×."* Worse, under `ρ_E − ρ_A`
the effect is almost exactly proportional to each concept's within-domain installation sd (ratios
1.11 / 0.81 / 0.98 for bomb / knife / gun), which is the *concept-general* reading `CONT-ENTRY 082`
rejected. The A13 conclusion — "concept-DEPENDENT, not concept-specific and not general" — is not
wrong, but it is not established at the strength stated, and the entry's own framing ("my prediction
was wrong in both directions, which is the useful outcome") converts a contrast-selection artifact into
a discovery. Second: **`A2`'s "POWERED NULL" is not powered in the only units that matter, and the
phase's own `C-CONT-038` is what makes it so.** With 63/100 button kept-positives spurious, the
content-true control rate is ≈0.040–0.051; the button MDE of 0.0531 is then **103–132 % of the entire
genuine attack-success rate**, and on basket the 95 % interval `[−0.0254, +0.0090]` against a
content-true base of ≈0.025 **does not exclude elimination of all genuine attack success**. REVIEW-2
asked for exactly this restatement (its ranked item 4); the `CONT-ENTRY 073` rebuild did not make it,
and `C-CONT-038` — which landed *after* REVIEW-2 wrote that item — makes the hedge stronger, not
weaker. Third, on process: `CONT-ENTRY 065` wrote *"DR-072 will not execute until `F5` has passed the
controls below"* and named four; two were run; the read was spent; and `CONT-ENTRY 075`, titled *"F5
passes its controls"*, does not mention the two that were not. Fourth, and the one that should change
what gets run next: **a demonstration-side full-state sufficiency test already exists in this
repository and the continuation has never cited it.** `outputs/boombness/g1_wholeanswer_sow.json`
carries `harm_ctx` (B→C) `demos_only` transplants at `+0.80` of span at L13–16 — and its matched
benign control `benign_ctx` (E→A) at `+1.10`. The demonstration-side upper bound *works* and is
*not doublespeak-specific*. That both refutes REVIEW-2's *"No sufficiency test has ever been run at the
site where the information is"* and pre-empts the obvious next experiment, which is the single most
useful thing in this review. Credit where due: `CONT-ENTRY 079`'s recorded-then-refuted prediction,
`080`'s self-correction against its own printed table, `082`'s refusal to argue away the
installability confound, and `077`'s refusal to take §46's conclusion with all eight boxes ticked are
all exemplary, and the `A11` prohibition in section B is stated exactly right.

---

## 1. A CONFIRMED PREDICTOR THAT CANNOT MEDIATE — is the pair coherent?

### 1.1 The pair is coherent. The imprecision is in one word, and it is in the paper-facing table.

There is no contradiction. `F5` reads `cw_demo_mean` — the mean residual at the codeword's
*demonstration* occurrences. `target_surface_row_only` edits one row inside the *query* span. Under
causal attention a query-position edit cannot change a demonstration-position state, so `F5`'s input is
bit-identical across `ko` and `ctrl` (`C-CONT-040`). A variable can predict Y, be causally upstream of
Y, and be invariant to an intervention that also changes Y through a different path. That is the
textbook picture of a **common cause measured before the fork**, and REVIEW-2 §2.3 already named it.
Nothing in `A11 ∧ C-CONT-040` is incoherent.

What is imprecise is the generalisation. `CONT-ENTRY 075` states it correctly:

> `F5` is a confirmed *predictor* that is provably incapable of mediating **the one intervention this
> phase owns**.

`CONT-ENTRY 071 §3` also states it correctly ("*structurally incapable of mediating this cut*"). The
**claim table does not**:

> **A11** … **CONFIRMED ON TEST** — but it **cannot be a mechanism** (`C-CONT-040`)

and section G repeats it: *"a candidate that cannot be a mechanism (A11)."* "Cannot mediate this cut"
and "cannot be a mechanism" are different claims. `F5`'s site could still be causally necessary or
sufficient for installation under an intervention *at its own site* — which is precisely the experiment
`CONT-ENTRY 076` found unbuildable in the within-domain form, and which (see §5.1) exists in another
form nobody has cited. The record has swung from one overclaim to its mirror image: a categorical
negative that its evidence also does not support. **The row should read: "cannot mediate `A1`; its
causal status at its own site is untested."**

### 1.2 What a confirmed predictor that cannot mediate *is*, and what it is worth

Stated at full strength and no further: *within a domain, which of ten demonstration draws produces a
stronger codeword→BOMB reading is linearly decodable at ρ ≈ 0.60–0.68 from the mean residual at the
demonstration codeword occurrences at L24 — before the query has been read at all.* Two things make
that non-trivial rather than tautological, and the phase earned both after REVIEW-2 raised the
determinism objection: `cw_demo_rand_mean`, a size-matched random pool from the same span, reaches only
`+0.2819` (`CONT-ENTRY 075`), and `raw_B` reaches `+0.4933` (`CONT-ENTRY 066`). So it is **not** "any
rich encoding of these demonstrations predicts their own outcome" — the codeword rows specifically
carry it. `C-CONT-055`, which records the author's own intuition being refuted by his own ordered
control, is the best single moment in these fifteen entries.

**But what the TEST read confirmed is weaker than "CONFIRMED" reads.** On TEST, `F5` was compared
against exactly two things: a within-domain label permutation, and the prespecified "comparator" which
`C-CONT-046` established **is the same ridge at λ→∞** (verified: λ=1e9/1e12/1e15 all give the
comparator's value exactly). The information-matched controls that give the number meaning —
`rand_mean`, `prev`, `next`, `raw_B` — all live on VALIDATION. So `ρ_test = +0.6054` confirms
*reproducibility of a fit*, against a null nobody holds and a comparator that is itself. That is a
legitimate and well-run confirmation of the stated decision rule; it is not a confirmation of any
mechanistic proposition, and the word CONFIRMED beside a row that also says "cannot be a mechanism"
will be read as more than it is.

### 1.3 Is it worth reporting, and as what?

Yes, as **one sentence inside a mechanism paragraph, not as a result of its own**:

> The demonstrations, not the query codeword, determine whether the remapped reading forms: the
> outcome is already linearly decodable (ρ≈0.61 on held-out domains, 23/23 positive) from the residual
> at the demonstration codewords before the query is processed, and it is not recoverable from
> size-matched random positions in the same span (+0.28).

**How a top-venue reviewer reads it, bluntly.** A NeurIPS/ICLR/ACL interp reviewer will ask three
questions in this order. (i) *"Is this a probing result?"* — yes, and the field's standard objection
(Hewitt–Liang; Belinkov's survey) is that probe accuracy without an intervention is not evidence about
mechanism. The record's own `C-CONT-040` hands the reviewer that objection pre-formulated. (ii)
*"What does it predict that the demonstration text does not?"* — REVIEW-2 asked this and the answer is
still missing, because the **within-domain surface floor was never built** (§4.3). The existing surface
floor (0.179) was computed against the discarded domain-mean target. (iii) *"Does it survive another
codeword?"* — `F5` has **never been fitted on basket**, although the basket behavioural corpus exists
and `A13` was replicated on it at zero GPU cost. A reviewer who notices that the phase replicated its
*newer* finding cross-codeword but not its *confirmed* one will not read that charitably.
My honest prediction: as a standalone claim this is desk-level "interesting but not a contribution";
as the opening move of the common-cause mechanism paragraph it is a genuine asset.

---

## 2. §15's MATCHED REFERENCE (A13) — the phase's best result, and its three soft numbers

### 2.1 (a) What the state is doing, mechanistically

The estimand is clean and the alignment claim is real: `B→C` is an exact `button`↔`bomb` word swap,
verified at **99 % on `seq_len`, `token_pos` and demonstration positions in 928/930 slots**
(`CONT-ENTRY 077`). So `sim(h_C, h_B)` at `cw_demo_mean` compares, within one slot and one
demonstration draw, the state at the codeword's demonstration positions against the state the *same
context* produces when the literal concept word sits there instead. The finding is that this similarity
rises with installation, while similarity to the same-position state under the *literal* codeword in
benign context (`A`) falls (`ρ_A = −0.192`).

The mechanistic reading that follows — and it is a good one — is **in-context token rebinding**: across
the demonstration block the codeword's representation is progressively overwritten toward the concept
it is being remapped onto, and the degree of overwriting predicts whether the model will report the
remapping. It coheres with three independent things the phase already has: the recency gradient across
demonstration occurrences (first 0.380 → last 0.616 → mean-of-four 0.698, `CONT-ENTRY 019`), which is
what an accumulating binding looks like; the L22–L30 plateau (`C-CONT-033`), which the depth profile
here reproduces without having been asked to (nothing at L14, peak at L24, decline at L31); and `F5`
sitting at the same site. **This is the program's best positive mechanistic story and it should be the
paper's spine.**

Two limits on what "the state is doing" can currently mean:

* **No localisation test has been run for A13.** `F5` got `cw_demo_prev/next/rand_mean` at L24
  (`CONT-ENTRY 075`); the §15 similarity was computed **only at `cw_demo_mean`**. The 880762 corpus
  holds 23 sites at L24 over all four cells, so running the identical similarity at `prev`, `next` and
  `rand_mean` costs **zero GPU**. If a size-matched random pool inside the demonstration span shows the
  same `B`-ward drift, "the codeword's representation is overwritten" collapses into "the whole demo
  block drifts", which is a much weaker claim. Until that is run, A13's sited language is unearned.
* **It is a similarity, not a direction.** No entry reports what the `B−A` difference vector *is* at
  these positions — its cosine to the concept-word unembedding, its rank, whether it is the same
  direction across domains. That is the difference between "the state moves toward BOMB" and "we can
  name the feature", and it is the difference between a probing paper and a mechanism paper.

### 2.2 (b) The installability confound — and a second confound the record did not find

`CONT-ENTRY 082` concedes the first honestly and I will not manufacture more criticism of it: *"with
n = 3 concepts I cannot separate 'bomb has a special geometry' from 'concepts that install more have a
stronger geometry, and bomb installs most'."* That is the correct statement and it is the limit of the
data.

**How damaging is it? More than the entry allows, because the quantitative claim it is attached to is
contrast-dependent.** From the committed artifacts, all at `cw_demo_mean|L24`, 900 slots / 90 domains:

| | `ρ_B` | `ρ_E` | `ρ_ctx` | `ρ_A` | **B−ctx** (reported) | **B−A** | **E−A** |
|---|---|---|---|---|---|---|---|
| bomb / button | +0.3823 | +0.2225 | −0.0230 | −0.1923 | **+0.4053** | +0.5746 | **+0.4148** |
| bomb / basket | +0.3223 | +0.1520 | −0.0094 | −0.1187 | **+0.3317** | +0.4410 | +0.2708 |
| knife / button | +0.1206 | **+0.1377** | +0.0583 | −0.0491 | **+0.0623** | +0.1697 | **+0.1867** |
| gun / button | +0.0320 | +0.0884 | +0.0515 | +0.0055 | −0.0196 | +0.0264 | +0.0829 |

Four consequences, none of them in the record:

1. **`ρ_ctx` is near zero by cancellation, not by absence of signal.** `ctx` is the mean of `A` and
   `E`, whose correlations are `−0.192` and `+0.222`. §15's criterion — *"exceeds the matched
   context-only prototype"* — is therefore close to automatic once `ρ_A < 0 < ρ_E`, which the depth
   profile shows is true wherever anything is happening at all. The gate that `CONT-ENTRY 077`
   celebrates passing (*"which is the comparison §15 was written to force, and which now goes the other
   way"*) is weaker than it appears.
2. **The bomb-vs-knife ratio is 6.5× / 3.4× / 2.2× under B−ctx / B−A / E−A.** `CONT-ENTRY 082`'s
   load-bearing sentence — *"Variance loss of 1.6× cannot produce an effect loss of 6.5×"* — is
   arithmetically fine and scientifically fragile: under E−A the effect loss is **2.2×** against a
   1.63× variance loss, a residual of **1.36×**, which is comfortably inside what rank-based
   attenuation through ties and floor effects can produce (the entry itself declines to model that
   attenuation, correctly).
3. **Under E−A the effects are nearly proportional to installation variance across all three
   concepts.** effect/sd = 0.4148/0.3739 = **1.11** (bomb/button), 0.1867/0.2295 = **0.81**
   (knife/button), 0.0829/0.0849 = **0.98** (gun/button). That is the *concept-general* reading — the
   one `CONT-ENTRY 078` labelled "reading 3", the one that "would make this finding uninteresting as
   *Bombness*" — reappearing under a contrast the record computed and did not report. It is not proof
   of reading 3 (Spearman is not expected to scale with outcome sd, so the proportionality may be
   coincidence across n=3), but it is exactly the evidence the entry says it does not have.
4. **For knife and gun, `ρ_E > ρ_B`; for bomb, `ρ_B > ρ_E`.** In both non-bomb concepts the state
   drifts toward the explicit concept word **in benign context** at least as much as toward it in
   harmful context; for bomb the ordering reverses. `CONT-ENTRY 078` claims *"the same ordering
   (B > E > ctx > A)"* replicates — true across the two bomb codewords, and **false across concepts**,
   where the record's own knife artifact carries `ρ_E = +0.1377 > ρ_B = +0.1206`. That number appears
   in `DCS_CONT_S15_KNIFE_CONTROL.json` and **not** in `CONT-ENTRY 082`'s table, which prints only `B`
   and `ctx`. If anything, this is the most interesting concept-specificity signal in the data — for
   bomb, and only for bomb, the alignment is with the concept *in harmful context* — and it is stronger
   than the claim the entry actually makes. It needs a statistic before it can be claimed.

None of the alternative contrasts carries a CI, because the committed artifacts store only the
`B − ctx` bootstrap. **Nothing here says A13 is wrong.** It says the *magnitude of concept-dependence*
is a researcher-degree-of-freedom result at present, and the claim table's A13 cell — "**6.5× weaker**,
against only a 1.63× variance deficit" — should not be published as a number until one contrast is
declared in advance and all four are reported with intervals.

### 2.3 (c) Does A13 revive the Bombness hypothesis that earlier phases refuted?

**It is a different claim wearing similar clothes, and it is a better claim — but it is not yet
separated from the refutation on either of the two grounds that killed `B1`.**

The earlier refutation rested on (i) the effect being a token × context interaction rather than
something localised at the codeword, and (ii) 1.02× concept specificity.

* **Different in kind.** `B1` was a *fixed direction* asked to serve as a concept detector at the query
  codeword. A13 is a *per-slot similarity to a matched counterfactual prompt*, correlated with
  installation within domain, at the demonstration codewords. A13 never claims to detect BOMB; it
  claims the state moves toward the BOMB state as the remapping takes hold. That is a weaker and far
  more defensible proposition, and it is the one §15 was written to test. The site also moved — from
  the query codeword (where the transplant null was measured) to the demonstration codewords (where
  every search result in this phase points).
* **Ground (i) is not yet answered.** A13 *is* a token × context interaction by construction — it
  measures how much the codeword's state resembles the concept token's state *in the same context*.
  The thing that would make it more than that is localisation, and **the localisation control has not
  been run for A13** (§2.1). `F5`'s controls do not transfer: `F5` is a fitted probe on cell C alone,
  A13 is a cross-cell similarity, and they can behave differently at `rand_mean`.
* **Ground (ii) is answered, but by how much is unsettled.** 1.02× → 6.5× would be decisive. 1.02× →
  2.2×, which is what the E−A contrast gives, is suggestive and is confounded with installability. So
  A13 moves the concept-specificity question from "refuted" to "open", which is real progress, and not
  to "revived".
* **One respect in which A13 is better controlled than `F5`, and the record does not claim the credit.**
  REVIEW-2's determinism objection (within a domain `y_install` is a deterministic function of the demo
  draw, so any rich encoding of the draw predicts it) applies verbatim to A13's site and population.
  A13 answers it for free: `ρ_A = −0.192`. The same states, the same slots, the same demonstration
  draw, a *different reference* — and the correlation flips sign. "Any function of the demonstrations"
  does not do that. **That is A13's strongest defence and it is not stated anywhere in entries 077–082.**

**Net.** A13 should be reported as: *the codeword's demonstration-side representation moves toward the
explicit-concept representation as the remapping installs, replicated on a second codeword, present but
substantially weaker for a second harmful concept, and confounded with installability across the only
three concepts this bank supports.* That is publishable and it is honest. "6.5×", "concept-DEPENDENT"
as a settled category, and the sited language all need the controls above first.

---

## 3. A12 — the remap installs bomb ~12× more readily than gun

### 3.1 How important is it? Very — it is the phase's most portable claim after the judge result.

A12 is the only finding here that constrains the **attack** rather than the instrument or the
representation, it is measured on 90 domains with domain as the unit, it is signed in 87–89 of 90
domains on two codewords with sign-flip p = 0.00005, and `C-CONT-057` already cut the one part that did
not replicate (the knife/gun ordering). The claim table wording is correct and correctly hedged, and
the correction against the entry's own printed table is exactly the discipline the mandate asks for.

Its importance is mostly **reflexive**, and `CONT-ENTRY 079` says so in the right words:

> It also reframes the phase's own naming: "Bombness" was never tested against a concept that installs
> comparably, because on this bank **no other concept does**.

That is the correct and uncomfortable reading. Every representational result in this program — `A1`,
`A13`, `F5`, the whole `B1` history — is measured on the single concept where the attack works, and the
bank cannot supply a comparison case. It does **not** invalidate those results; it bounds their external
validity, and it explains *why* the §15 harm control could not be built (`CONT-ENTRY 079`) and why the
installability/geometry confound cannot be broken here (`CONT-ENTRY 082`). Those two walls are the same
wall, and A12 is its measurement.

### 3.2 Does it mean the program has been studying the single easiest case? Yes — with one caveat the record does not raise.

**`y_install` is a two-option renormalisation, `p(concept)/(p(concept)+p(codeword))`, and its coverage
of the model's actual answer is 3× worse for gun and knife than for bomb on the exact population A12
and A13 use.** `CONT-ENTRY 079` checks this and clears the instrument:

> The readout is not broken (median option mass 0.1174 vs bomb's 0.2119; the sub-0.05 fraction is 0.30
> vs 0.27 — comparable)

I reproduced both of those figures exactly — **and they are all-rows medians**: every query kind
(including `semantic_forced_choice`, whose prompt *names the two options* and therefore mechanically
inflates option mass), every cell, every dose, every split. On the population that every A12 and A13
number is computed on — `semantic_one_word` × cell C × dose 4 × 93 non-test domains, 930 slots each:

| | median `option_mass` | frac(`option_mass` < 0.05) | mean `y_install` |
|---|---|---|---|
| bomb / button | **0.3241** | **0.126** | 0.6744 |
| knife / button | 0.1017 | 0.196 | 0.1657 |
| gun / button | **0.0933** | **0.270** | 0.0575 |

The deficit is **3.5×**, not 1.8×, and the fraction of rows where the two-option channel captures under
5 % of the answer is **27 % for gun against 12.6 % for bomb** — not "0.30 vs 0.27, comparable". The
top-1 answer token on gun cell-C rows is spread over **147 distinct ids**, with the most common one
being the same id that dominates the *benign literal* cell A. So on ~90 % of gun rows the score is a
ratio between two small numbers describing a channel the model is not using.

This does not overturn A12 — an 11.7× mean ratio is not going to be erased — but it means the ratio
partly measures **lexical coverage of the readout** and not only **strength of installation**. A model
that installed `gun` and reported it as *"a weapon"* or *"a firearm"* would score zero installation
here. The check is free and decisive: `top1_id` is persisted on every row, so decoding the top-1
answers on gun/knife cell-C rows and measuring how often the model names a *synonym* of the concept
settles it in an afternoon with no GPU. Until then, "the remap installs bomb 12× more readily than gun"
should read "…12× more readily **as measured by the two-option concept-free readout, whose coverage is
3.5× lower on gun**".

### 3.3 One overclaim, and it contradicts the program's own headline

`CONT-ENTRY 079` extends A12 from the readout to the attack:

> Whatever makes **this attack work** is not a generic "remap a word onto a forbidden concept"
> mechanism; it is far easier for some concepts than others.

No ASR was measured on gun or knife. The inference runs installation → attack difficulty — and **`A3`,
the phase's own headline, is that installation and behavioural attack success are dissociable under
intervention**. The program cannot simultaneously publish "cutting installation by 31 % does not change
ASR" and "gun installs less, therefore the attack is harder for gun." The claim-table row A12 is worded
correctly ("**installs** far more readily"); the entry's prose is not, and the prose is what will end up
in a paper. The fix is either the hedge or the measurement: a gun/knife behavioural arm is one
generation job and would convert A12 from a readout claim into a genuine attack claim — at which point
it becomes considerably more interesting, because whichever way it lands it says something sharp about
`A3`.

---

## 4. OVERCLAIM AUDIT — defects not yet in the ledger

### 4.1 `A2`/`A3`: "NULL, POWERED" is not powered in content-true units — and `C-CONT-038` is why

This extends REVIEW-2 §1.3b, whose ranked item 4 (*"Restate A2/A3 in relative units against the
content-true base rate"*) was **not implemented** in the `CONT-ENTRY 073` rebuild. Since REVIEW-2 wrote
it, `C-CONT-038` landed and made it worse.

Inputs, all from the claim table itself: button `ctrl` corrected rate 0.1388; primary +0.0030,
CI [−0.030, +0.036], MDE(80 %) 0.0531. Basket `ctrl` 0.0493; primary −0.0090, CI [−0.0254, +0.0090],
MDE 0.0254. And `A7b`: of 100 hand-labelled button kept-positives, **63 contain no bomb content**, 29
genuine, 8 weak; basket 11/22 spurious.

| | content-true `ctrl` | CI lower bound as % of it | MDE as % of it |
|---|---|---|---|
| button (genuine 0.29–0.37) | 0.0403–0.0514 | **58–74 %** | **103–132 %** |
| basket (genuine ≈0.50) | ≈0.0247 | **≈103 %** | **≈103 %** |

So: the button experiment had 80 % power only against an effect **larger than the entire genuine
attack-success rate**, and excludes reductions above roughly 58–74 % of it. The basket interval
**does not exclude elimination of all genuine attack success**. `CONT-ENTRY 071` does give a relative
framing — *"the basket interval excludes a ~55 % reduction while button's excludes ~38 %"* — but both
figures are relative to the **corrected (upper-bound)** rate, which `C-CONT-038` established is inflated
by a factor of roughly 2.7 on button. The claim table's `A2` status, **"NULL, POWERED, REPLICATED
CROSS-CODEWORD"**, is therefore true of an upper-bound endpoint and false of the endpoint anyone cares
about. `A3`'s "the dissociation is now a two-codeword result" inherits the problem: the basket half
contributes no exclusion at all in content-true units.

Two assumptions in my arithmetic, stated so they can be attacked: that the spurious fraction is equal
in `ko` and `ctrl`, and that it is unaffected by the intervention. **Neither is safe** — `A4` reports
that the `ko` arm *halves refusal*, so its completions differ in character from `ctrl`'s, and **no
kept-positive audit has ever been done per arm**. That is a third un-hedged channel and it points the
same way.

This is the most consequential un-caught overclaim in the phase. It is not a criticism of the
experiment, which is well-run; it is that the endpoint the experiment is powered against is not the
quantity the claim is about.

### 4.2 The claim table's own banner contradicts two of its rows

> ⛔ **Everything here is TRAIN-only and EXPLORATORY.** No confirmation freeze has happened and the
> frozen TEST split has not been read.

`A11` reads **CONFIRMED ON TEST**, `ρ_test = +0.6054` on 230 TEST slots, and section E reads
*"✅ **DONE, CONFIRMED** … The single read is spent."* The banner was written for the `CONT-ENTRY 073`
rebuild, which preceded the read in `075`, and was not revisited when `A11` was upgraded. It is the
first thing a reader sees on the paper-facing deliverable and it is false.

### 4.3 `DR-072` was read with two of its four declared gate conditions un-run

`CONT-ENTRY 065`, in bold, as a decision:

> **Decision: `DR-072`'s single TEST read is HELD.** … DR-072 will not execute until `F5` has passed
> the controls below. … **F5 controls to run, all zero-GPU, all on tensors already on disk:** ridge on
> `raw_B`; ridge on `cw_demo_prev_mean` / `cw_demo_next_mean` / `cw_demo_rand_mean` at L24 …; a
> **within-domain** surface floor (the existing 0.179 floor was computed against the discarded
> domain-mean target); and `cos(w_F5, logit-lens direction)`.

`raw_B` ran (`066`). The adjacency/mass controls ran (`075`). **The within-domain surface floor and the
cosine test have not been run** — I grepped entries 068–082 and the whole `scripts/` tree for both and
found neither. `CONT-ENTRY 075` is titled *"F5 passes its controls"* and does not mention them. The
surface floor is not a nicety: mandate §47 lists *"Does the surface text classifier get the same
result?"* as one of the twelve questions a working candidate must answer, and §44's gate item "not
explained by `N_surface`" is currently satisfied by a floor computed against a target the phase
discarded. The read is spent and cannot be un-spent; what is owed is that both controls run anyway and
that the record state plainly that the confirmation preceded them.

### 4.4 The "concept-dependent, not general" conclusion — §2.2 above, in one line

Not robust to contrast choice (6.5× / 3.4× / 2.2×), the largest of the four available contrasts is the
one reported, no CI exists on the ratio, the knife `ρ_E > ρ_B` inversion is in the artifact and not in
the entry, and under `E−A` the three concepts' effects are nearly proportional to their installation sd
— which is the concept-general reading the entry rejects. The *direction* of the conclusion is
defensible; the *strength* and the number are not.

### 4.5 Section G is stale and asserts one thing it has not measured

> The mechanistic results are a **clean two-codeword null** (A2/A3) and a **candidate that cannot be a
> mechanism** (A11).

Written at `CONT-ENTRY 073`; `A12` and `A13` arrived at `079`–`082` and were added to section A without
section G being revisited. So the phase's **best positive finding is absent from the section that tells
a reader what to report**, while that section's summary of the mechanistic results is now incomplete and
its `A11` phrasing carries the §1.1 imprecision. Separately: *"and it generalises beyond this bank"* is
an **argument** (from `judge_boombness.make_goal` substituting codeword→concept on any row carrying
both), not a measurement — the 2.55× was measured on one bank, one judge and one model family. It
should read "the failure mode is not bank-specific by construction; the magnitude is measured here
only."

### 4.6 §46's eight prerequisites — correctly ticked, correctly refused, and one soft tick

`CONT-ENTRY 077` deserves explicit credit and gets it: all eight boxes are ticked and the conclusion is
**refused**, in the right words — *"Writing 'there is no BOMB representation' now would be reading a
checklist instead of the evidence."* The count correction (the claim table said seven, the mandate
lists eight) is right; I counted the mandate's bullets independently and there are eight. Nothing here
is being used to imply more than it should **inside the log**.

One soft tick worth naming: prerequisite 8, *proper validation*, is marked ✅ with *"TRAIN → VALIDATION
→ TEST, `DR-072` confirmed"*. `DR-072` validated **one candidate from one family**; the other seven
families died on TRAIN or VALIDATION and were never taken to TEST — correctly, but that means
"proper validation" is discharged by a single confirmation rather than by the search having been
properly validated. Minor, and it only matters if §46's conclusion is ever taken, at which point the
checklist becomes load-bearing.

### 4.7 Two provenance defects that are recurrences of already-corrected ones

* **A13 and A12 have no generating script.** `reports/DCS_CONT_S15_*.json` are committed but **nothing
  in the repository references them** — no script writes them, and the external MD never cites their
  paths. A12 has no artifact at all. This is precisely `REVIEW-2/CODE-05` and `DATA-10` on `F5`
  (*"entries 059 and 061 committed no script and no artifact, so the phase headline … could not be
  re-derived"*), which was fixed by writing `dcs_cont_f5_probe.py` — and the same defect immediately
  recurred on the two newest claims in the table. Mandate §49 requires an artifact path per claim; A12
  and A13 carry none.
* **A12's `n` cannot be reconciled.** The row says "1080 shared slots / 90 domains"; every other §15
  number on the same population is 900 slots / 90 domains, and the bank is 10 family slots per domain,
  so 1080/90 = 12 slots per domain is not a shape this bank produces. With no artifact the figure
  cannot be re-derived. Given `C-CONT-034`/`035`/`057` — three prior instances of an asserted count
  beside numbers that do not support it — this one should be checked before it is quoted again.
* **Section F is stale**: it omits all four `DCS_CONT_S15_*.json`, `f5_confirmation_TEST.json`, and
  `reports/DCS_CONT_F5_MASS_CONTROLS_L24.json`.

### 4.8 Correctly hedged — recorded so the audit is not one-sided

`CONT-ENTRY 079`'s recording of a prediction **before** the gun job landed and its publication after the
prediction failed; `080`'s `C-CONT-057`, catching an ordering asserted against its own printed table,
and its refusal to let the low-end reversal pass as noise without saying why; `082`'s refusal to argue
away the installability confound; `070`'s conversion of a reviewer's hypothesis into a *measurement*
that refuted the reviewer and produced the hardware noise floor — which is a genuinely valuable piece of
methodology and is correctly framed as bounding rather than weakening the null; `072`'s disclosure of
the 5.1 GB judgment call as a **choice**; `081`'s clock-skew audit closing with "no published number
moves" after checking rather than assuming; and `069`'s counting `len(KNOWN_ZERO)` from the module
instead of the draft. The ⛔ block repeated verbatim at the foot of `077`, `078`, `079` and `082` —
correlational, train+validation, no TEST read, no preregistration, no causal claim — is exactly right
and should stay attached to A13 in any external document.

---

## 5. WHAT NOW

### 5.1 The finding that should change the plan: a demonstration-side sufficiency test already exists

`CONT-ENTRY 076` closed the within-domain demonstration-side patch as *"not constructible on this
bank"*, and REVIEW-2 §3.2 asserted *"No sufficiency test has ever been run at the site where the
information is."* Both statements have shaped everything since. The second is **false**, and the first
is true only of the particular design it tested.

`src/boombness/aggressive_patching.py` defines `PAIRS["harm_ctx"] = ("direct_harmful",
"natural_doublespeak")` — donor cell **B**, recipient cell **C** — with `PAIR_ALIGNMENT["harm_ctx"] =
"absolute"`, and the demonstration-position refusal is scoped to end-relative pairs only
(`END_RELATIVE_SCOPES = ("query_only",)`). `SCOPES` includes `demos_only`, `first_demo`, `last_demo`.
And `outputs/boombness/g1_wholeanswer_sow.json` contains the results, n = 24 per arm, readout
`semantic_logodds`:

| arm | `harm_ctx` (B→C) | `benign_ctx` (E→A), the matched control |
|---|---|---|
| `transplant \| demos_only \| L13-16` | **+0.803** of span | **+1.096** |
| `transplant \| demos_only \| L17-20` | +0.799 | +1.084 |
| `transplant \| demos_only \| L18` | +0.689 | +0.944 |
| `transplant \| query_only \| L18` | **−0.570** | −0.082 |
| `transplant \| first_demo \| L18` | +0.316 | +0.241 |
| `transplant \| last_demo \| L18` | +0.095 | +0.057 |

Three things follow, and all three matter more than anything else in this review:

1. **A full-state intervention at the demonstration codeword positions has causal leverage — 0.69–0.80
   of the span — where the same intervention at the query codeword has none (−0.57).** That is §21's
   question answered, at the site the whole phase's search points to, and it is consistent with A13 and
   with `F5` in a way the record has never assembled.
2. **It is not doublespeak-specific.** The matched benign control moves *more* (+1.10). Transplanting
   the explicit concept token's states into the demonstration positions makes the model report the
   concept whether or not harmful demonstrations are present — which is mandate §2.7's lexical-identity
   objection, realised. So the naive "patch B into C at the demo positions" experiment, which is the
   obvious thing to propose after `CONT-ENTRY 077`'s 99 %-alignment table, **has already been run and
   its control already defeats it.** Proposing it now would burn a week.
3. Caveats that keep it from being a finished result: n = 24, the superseded `boombness_prompt_bank`
   (the `carrot` era, whose codeword was later withdrawn on instrument grounds), `semantic_logodds`
   rather than the concept-free binary readout, and a `harm_ctx` baseline already at +4.05 log-odds.
   It is a pilot, not a claim — but it is a pilot that rules out the obvious design and points at the
   graded one.

### 5.2 Does §47 apply to `A11`? Yes, and it has not been satisfied

§47 opens *"Do NOT immediately celebrate. Attack it,"* lists twelve questions, and closes *"Only then
promote it."* Against `A11`:

| §47 question | status |
|---|---|
| Just prompt length? | not tested |
| Just template? | **no held-out readout template exists** (§7 open since the phase opened) |
| Just final-position state? | ✅ tested — `rel-1` +0.4665 vs `F5` +0.6784 |
| Just codeword anomaly? | ✅ `prev`/`next`/`rand` at L24 (`075`) |
| Generic remapping? | not tested (`raw_E` never fitted at `F5`'s configuration) |
| Harmfulness? | not tested |
| Surface text classifier? | **not run** — the within-domain surface floor (§4.3) |
| Another codeword? | **not run** — `F5` has never been fitted on basket, though the corpus exists |
| Another readout template? | **no** |
| Full-state upper bound at its site? | see §5.1 — a pilot exists, its control defeats it |
| Random/orthogonal controls? | ✅ partially (`rand_mean` +0.2819) |
| Does ASR move? | **structurally untestable with the intervention this phase owns** (`C-CONT-040`) |

Roughly **three and a half of twelve**. `A11` is nevertheless carried in the paper-facing table with
status **CONFIRMED**. §47's instruction is that promotion comes *after* the attack, and the order was
reversed. The remedy is not to withdraw `A11` — the confirmation is real and correctly executed — but
to carry the scorecard beside it. The registry has never had one; `CONT-ENTRY 065` asked for it and it
still does not exist.

### 5.3 RANKED NEXT STEPS

Ordered by value per unit cost, with the cheap-and-decisive first — which is the lesson `DR-072`'s
premature read already taught this phase once.

1. **Rebuild the behavioural endpoint. No GPU.** A new frozen instrument scoring the *materials/steps
   block* rather than term presence, calibrated against the 122 already-hand-labelled kept positives,
   re-scored over the existing generations; then restate `A2`/`A3`/`A5`/`A6`/`A9` in content-true
   units. This is the prerequisite for every behavioural claim the program will ever make: with the
   current endpoint the button MDE is 103–132 % of the genuine attack rate and the basket interval
   excludes nothing (§4.1), so **no future intervention experiment can return an interpretable answer
   until this is fixed**. It also completes section G's contribution — "the judge is broken" becomes
   "here is the repaired measurement and here is what changes", which is a substantially better paper.
2. **The A13 control set. No GPU, hours of CPU, could kill or transform the phase's best finding.**
   (a) the §15 similarity at `cw_demo_prev/next/rand_mean` at L24 on the existing 880762 corpus — the
   localisation test A13 has never had; (b) all four reference contrasts (`B−ctx`, `B−A`, `E−A`, `B`)
   with domain-level bootstrap CIs on each and on the bomb/knife **ratio**, with one contrast declared
   in advance; (c) the knife `ρ_E > ρ_B` inversion tested rather than omitted. Until (a) returns, A13's
   sited language is unearned; until (b) returns, "6.5×" should not be quoted.
3. **`F5` on basket, plus the two un-run gate controls.** Zero GPU — the basket behavioural corpus
   exists and was used for A13's replication. §47's "does it survive another codeword" is unanswered
   for the phase's only confirmed claim, and the within-domain surface floor and `cos(w_F5,
   logit-lens)` are owed from `CONT-ENTRY 065` regardless of how they land. The cosine test has the
   highest upside of the three: if it is high, the phase's leader becomes *"the amount of `bomb`
   already present in the residual at the demonstration codewords predicts installation"*, which names
   a feature instead of reporting a fitted vector, and which would join up with A13 into one mechanism.
4. **THE SINGLE MOST VALUABLE EXPERIMENT — the demonstration-dose ladder, measured jointly on
   installation and content-true ASR, same domains, same prompts.** Cell C behavioural + semantic at
   `n_examples` ∈ {0, 1, 2, 4} (dose-0 rows already exist in the bank, 2,784 of them), 67 domains,
   corrected ASR and `y_install` per domain, one generation job and no new intervention machinery.

   *Why this one.* It is simultaneously the three things the program most needs and has never had.
   **(i) The behavioural positive control.** `A2`'s "powered null" is powered against an endpoint whose
   sensitivity to *any* demonstration-side manipulation is unmeasured; REVIEW-2 raised this as gap 1 and
   it is still open. If corrected ASR does not move when the demonstrations are removed entirely, `A2`
   is uninformative and the phase's headline must be rewritten. **(ii) The common-cause discriminator.**
   The dose ladder manipulates the putative common cause directly — the demonstrations — which is the
   one thing the `ko` intervention provably cannot touch (`C-CONT-040`). If installation and ASR move
   together across doses while the query-row cut moves only installation, the phase gets the positive
   mechanism sentence REVIEW-2 §2.3 proposed, supported by an intervention rather than by a
   correlation. If installation moves and ASR does not, the dissociation deepens into a much stronger
   and more surprising claim. **(iii) It closes `A3`'s template defect for free**: the demonstration
   block is byte-identical across the behavioural and semantic prompts (REVIEW-2 measured 920 shared
   characters), so a demonstration-side manipulation changes the *same bytes* on both, which is exactly
   what "the same cut, at the same site, with the same dose" failed to be (`REVIEW-2/SCIENTIFIC 1.3a`).
   It is also the only route left to §45's "most important causal endpoint" that does not require a new
   bank, given that `CONT-ENTRY 076` blocked the within-domain patch and §5.1 shows the B→C patch is
   defeated by its own control.

   Preregister the direction and the MDE in content-true units **before** running, and note that step 1
   must land first or the ASR half of the ladder will be unreadable.
5. **Graded, direction-level demonstration-side intervention — only if step 4's ladder moves ASR.**
   Instead of transplanting `h_B` (which §5.1 shows the benign control defeats), add `α·(h_B − h_A)` at
   the demonstration codeword positions on a dose ladder, with the matched benign direction
   `(h_E − h_A)`, matched-norm random, orthogonalised, and non-codeword-position controls — the control
   set G1's `add` arms show you need, since at α=1.0 a *random* direction there already moves 0.90 of
   span. This is the minimal-intervention test of A13's geometry and §35's mechanism-derived attack
   objective in one design. It is expensive and it should not be started before steps 1–4.
6. **Bookkeeping that costs nothing and is owed now** (§4.2, §4.5, §4.7): fix the claim-table banner,
   which is false; change `A11` from "cannot be a mechanism" to "cannot mediate `A1`; causal status at
   its own site untested"; add A13 to section G; commit generating scripts and artifact paths for A12
   and A13; reconcile A12's `n`; refresh section F; add the §47 scorecard to the registry.
7. **A12's readout-coverage check.** Decode `top1_id` on gun/knife cell-C rows and measure synonym
   naming (§3.2); attach the coverage caveat to A12's ratio; and strike the installation→attack
   inference from `CONT-ENTRY 079`'s prose (§3.3), or measure it with a gun/knife behavioural arm — the
   cheapest way to make A12 a claim about the attack rather than about the readout.
8. **More concepts that install.** The only way past the installability/geometry confound and the
   missing harmful-non-BOMB reference, both of which are the same wall. A bank-generation task, not an
   analysis one; worth scoping now because two open questions terminate on it.
9. **Template transfer (§7).** Still the one prerequisite standing between "predicts a readout" and
   "semantic", still cheap, still not built, and `F5`'s and A13's target is defined by exactly one
   wording.
10. **The between-domain question** (37.9 % of `y_install` variance, discarded by within-domain centring
    and never revisited) and **the `<|start_header_id|>` scaffold token** (two independent signals put a
    formatting token at or above the codeword, logged twice, never followed up). Both are REVIEW-2
    carry-overs; both remain open; neither is urgent.

---

*Prepared as the SCIENTIFIC dimension of REVIEW-3. No experiment run, no job submitted, no FROZEN
config edited. One disclosure regarding test-domain rows is recorded at the head of this document.
This reviewer reports; it does not fix.*
