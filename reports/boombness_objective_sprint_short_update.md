# Boombness sprint — short update

**For:** Matan, Mahmood · **From:** Omer · **Date:** 2026-08-19, **revision 6 — 2026-08-22**
**Full report:** `reports/boombness_objective_sprint_report.md` ·
**Live log:** `docs/BOOMBNESS_CONTINUATION_LOG.md` · **Plan:** `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md`
**Branch:** `behavioral-causality-sprint`

> ## The result, stated once
>
> **Boombness does not predict attack success — and removing the direction it measures causally
> raises attack success.**
>
> Those are consistent, not contradictory: ablating a direction is a different operation from
> regressing on its magnitude, and a projected scalar is a lossy summary of the direction it comes
> from. But the objective this sprint set out to build assumed the two travel together — maximise the
> axis, get more attack success — and **they do not**. It is dead for two independent reasons.
>
> **What survives, all causal, all on external harmful sets the prompt bank never generated:**
> * Removing `d_surface` alone raises attack success on **AdvBench (495 prompts, 16 clusters)**:
>   **+0.0305 domain-clustered on the CONTINUOUS StrongReject score**, p=0.0089; the **binary ASR** is
>   **+0.0424 pooled / +0.0306 clustered**. ⚠ **Estimand labelled 2026-08-22** —
>   the full report's §0a quotes the *pooled* +0.0424 for the same effect, and comparing the two
>   unlabelled reads as a contradiction. ⛔ "against a matched random projection that is inert
>   (−0.0062)" is **retracted (R-23/R-25)**: a random direction in 4096-d is near-orthogonal to
>   everything and barely perturbs the model, so it is far too weak a null. Against directions inside
>   the *same* rank-3 cell-mean subspace the arm still wins at all four layers, but by
>   **1.80×–3.60×**, not against an inert control.
> * The effect is **localized to a band of layers, ~L6–L14 with a core at L8–L12** (scan-statistic
>   window, permutation p=0.011 under layer-label exchangeability; no single layer survives Holm),
>   with a matched
>   control inert at all eleven depths tested, and **exactly zero at L16** — where the same
>   intervention still changes 29.5% of generations.
> * ⛔ **RETRACTED (R-26, C-12).** Was: *"It is **specific to this direction**: the effect tracks the
>   cosine with `d_surface`. `d_context`, fitted by the same 2×2 on the same rows, changes 34.9% of
>   generations and moves ASR by **zero**."* `d_context` removes only **0.13** of the cell-mean spread
>   against `d_surface`'s **0.84** — a 6× dose gap, and 0.13 sits *inside the range where every
>   in-subspace direction is inert regardless of meaning*. So its near-zero ASR says nothing about
>   specificity. Its clustered delta is **+0.0045**, not zero (the pooled 0.00025 was the estimand
>   switch C-12 retracted twice).
> * Removing `d_surface` **and** refusal together exceeds the sum of the parts by
>   **+0.0268 [+0.0029, +0.0584]** beyond a matched random triple — the two channels interact.
> * **G1** (meaning lives in the demonstrations, not the codeword) and **G3** (the retrieval is
>   attention-carried and massively redundant) both re-derived on a corrected readout.
>
> **§18 outcome label: C, amended** — refusal is the dominant channel on Llama, but `d_surface` is a
> distinct and interacting second channel the label understates, and on Qwen3-14B the picture inverts.
> ⛔ *An earlier revision of this document said "§18 settles at B". That is withdrawn: B requires that
> interventions neither affect ASR nor destroy comprehension, and **both clauses fail.***

> ## Retractions, newest first — read these before any number below
>
> - ⛔ **R-18/R-19 (2026-08-19) — G2 is RETRACTED, and the localization result is half retracted.**
>   `analyze_g2` filtered rows on `condition` and **not** on `bank_block`, so its headline n=234 was
>   31% sibling families sharing demonstrations and 31% rows whose codeword readability was
>   *experimentally manipulated*. Within-domain ρ on clean rows: **−0.083** (n=60), **−0.052** (n=90),
>   **−0.066, p=0.493** (n=108 powered). The published **+0.2618, p=5e-4** is recoverable only by
>   putting the contaminated rows back. The same defect halves the position/localization finding.
>   **Unaffected:** G1, G3 and the probes, which filter on `bank_block`.
> - ⛔ **R-17** — the cross-model *causal* replication claim is withdrawn; Qwen3 complies with 0.8% of
>   AdvBench, so an intervention cannot be measured against that floor.
> - ⛔ **R-16 → reversed** — ClearHarm arm B is n.s. at G=6, but AdvBench's 16 clusters settle it.
> - ⛔ **R-15** — "harm-general, not doublespeak-specific" was **one significant cell of six**; the
>   split tracked sample size, not harm.
> - ⛔ **R-14** — every external-set ASR was judged against an **empty goal**; banks fixed, all arms
>   re-judged, arms moved ≤0.03.
> - ⛔ **R-13** — the "matched footing" incremental table gave refusalness 5 predictors against
>   Boombness's 1.
> - ⛔ **R-12** — the control band was one draw stated three times; the real between-draw sd is
>   0.0129, not 0.0048.
> - Earlier: the 3.7× claim, the mixed-footing increments, the role null, the fake 4-draw band.
>
> Corrections ⚠, retractions ⛔. Every number in the full report is checked against its committed
> artifact by `scripts/verify_report_numbers.py` (17/17 passing).


---

## Current state — 2026-08-22 (revision 6). Read this before the rest.

Five retractions and three corrections have landed since revision 5. The full report's **§0a** is the
authoritative flat version; this is the same content, shorter.

**Still standing — but only L12 survives multiplicity.** Projecting out `d_surface` raises AdvBench
attack success: L8 **+0.0424** (21 flips), L12 +0.0364, L10 +0.0323, L6 +0.0182, n=495 — all
**binary ASR at threshold 0.5, pooled**; the L8 binary domain-clustered figure is **+0.0306**. ⚠ The
**+0.0305 / p_cl=0.0089** quoted elsewhere is the **continuous StrongReject** clustered mean, a
*different estimand* that agrees to three decimals by coincidence (audit #8). Under a **cluster sign-flip test** (the honest one — see R-27): **L12 p=0.0039,
Holm over the 11-layer family 0.043 → survives**; L8 p=0.0078 (Holm 0.078) and L10 p=0.0156 are
significant *only uncorrected*; **L6 p=0.0625 is not significant at all**. The four layers were
themselves the **top four of eleven** by this same statistic, which is why Holm uses m=11. The arm
beats every direction in the same rank-3 cell-mean subspace (1.80× / 2.33× / 3.60× at L6/L8/L12;
undefined at L10, where every control is ≤0). The gain is real refusal→compliance flips, not longer
refusals (+0.0000 on the 440–451 both-refused rows, verified at all four layers). The dose-response is
**saturating** (and monotone except at the top rung, where it falls by one flip).

**The caveat that must travel with it (R-25).** `d_surface` is essentially **PC1** of the bank's
cell-mean structure (cos 0.9998–1.0000), so projecting it out removes **0.81–0.88** of that spread
while any in-subspace control removes **≤0.132**. The effect is therefore **not shown to be about the
direction's content** rather than about how much variance it removes — and in this bank the two
**cannot** be separated: reaching 70% dose forces \|cos\| ≥ **0.88–0.91** with `d_surface`. That needs
a different design, not more compute.

**Retracted since revision 5.** **R-23/R-24** — the concept-transfer experiment failed both of its
pre-committed controls, so `d_surface` is **not** shown to name a concept (details already in the
"Honest limits" section below). **R-25** — the "content, not magnitude" reading above. **R-26** —
§14-D's specificity conclusion: `d_context` moves ASR by ~zero because its dose is **6× lower**, which
says nothing about meaning. **R-27** — an entire dose-ladder inference chain of mine, including a
geometric bound that was **algebraically false**.

**Not established, and not shown absent either.** A follow-up comparison returned no cluster-level
significance at any of five layers — but that design's **minimum detectable effect is ≈+0.03** and the
largest effect it produced was **+0.0222**, so those nulls are uninformative about absence.

**Two things worth knowing before you act on any of this.** At matched dose, **`d_naive` beats
`d_surface` by 38%** (+0.0586 / 29 flips vs +0.0424 / 21) — the 2×2's identification step moved *off*
the stronger direction. And the scope is **one model, one concept pair**: the Qwen3-14B replication is
**retracted (R-17)** and the concept swap failed both pre-committed controls (R-23/R-24).

**The objective.** Unchanged: **do not build it.** R-26 is fresh evidence against, not for.

---

---

## Main finding

**The plan's confound is real, and fixing it changes the measurement.** The existing benchmark
compares a harm-domain arm against a benign arm that is *a different story*, so the natural
"Boombness" direction — `mean(h_bomb) − mean(h_carrot_benign)` — is
`bombness + explosive-context-ness`. We replaced it with a 2×2 (surface word × demo valence) that
identifies the two separately:

```
d_surface = ½[(B−C) + (E−A)]     the surface-word effect, context matched  ← Boombness
d_context = ½[(C−A) + (B−E)]     what the naive direction mostly measures
```

⛔ **THE CORRELATION BELOW IS RETRACTED (R-18, 2026-08-19).** An earlier revision called it *"robust in
Llama — survives dropping any domain, 6/6 domains positive"*. It is not robust; it is an artifact of
which rows were in it. `analyze_g2` filtered on `condition` and not on `bank_block`, so 31% of its
n=234 were **sibling families sharing demonstrations** and 31% were rows whose codeword readability had
been **experimentally manipulated**. On clean rows the within-domain ρ is **−0.052** (n=90) and
**−0.066, p=0.493** (n=108 powered) against a published **+0.2618, p=5e-4**.

*(It also never replicated on Qwen3-14B — pooled +0.364 but +0.015 after dropping one domain, 3/6
domains positive, clustered p=0.206. That non-replication now reads as the earlier signal, not the
anomaly.)*

**The 2×2 identification design below is unaffected and remains the sprint's reusable contribution** —
it is what made `d_surface` and `d_context` separable, and the causal results in the head of this
document all rest on it.

⛔ **RETRACTED 2026-08-19 (R-18) — read this before the numbers below.** The claim was
*"Boombness predicts attack success within the doublespeak arm: ρ = +0.307 at L12, n = 234"*.
`analyze_g2` filtered rows on `condition` alone, so that n=234 was **31% sibling families sharing
demonstrations** (pseudo-replication) and **31% rows whose codeword readability was experimentally
manipulated**. On the **90 independent, unmanipulated prompts the within-domain ρ is −0.0518
(p = 0.658)**, against a published +0.2618 (p = 5e-4); `core2x2` alone (n=60) gives −0.0832
(p = 0.572). **Not established** — n=90 cannot exclude a small effect, so this is a null, not a proof
of absence. G1, G3 and the probes filter on `bank_block` and are **unaffected**. The numbers below are
the retracted analysis, kept for the record.

⚠ **The p-value in revision 1 was wrong by ~3.5 orders of magnitude.** The 234 prompts are 6 domains
× 39 and the predictor is strongly clustered by domain (ICC ≈ 0.45); I reported the i.i.d. p. The
association survives, but the honest numbers are:

| inference | p |
|---|---|
| i.i.d. (what I sent before) | 1.7e-06 |
| CR1 domain-clustered (G=6, few clusters — indicative) | 1.2e-03 |
| **within-domain permutation — cite this one** | **< 5e-4** (0 of 2000 draws reached the observed value, i.e. the resolution floor) |

⚠ **"Positive in 5 of 6 domains" was the wrong column.** For the quoted `proj` predictor it is
**6 of 6**, but that reads more uniform than the data is — two domains are essentially null:

| domain | ρ | | domain | ρ |
|---|---|---|---|---|
| farm_storage | +0.410 | | instructional | +0.234 |
| city_bridge | +0.344 | | news_report | **+0.062** |
| game_manual | +0.330 | | lab_safety | **+0.020** |

Both are now produced by the committed `analyze_g2.py` (`--cluster-by domain`), which previously
computed no per-domain breakdown at all — the same "no script regenerates this" provenance failure
that caused an earlier retraction.

## The attack works by removing refusal — but that is not what varies *within* it

On the 234 prompts the correlation uses (`n_examples ≥ 1`):

| | mean refusalness (L18) | ASR | refusal rate |
|---|---|---|---|
| direct harmful request | **+7.06** | 0.050 | 95.0% |
| doublespeak | **−0.15** | **0.214** | 0.85% |
| mapping stated outright | +0.01 | 0.375 | 0% |
| benign literal | −0.30 | 0.031 | 1.85% |

⚠ **Revision 4 got four of these cells wrong.** It mixed the all-rows population into a paragraph
that claimed it did not. On the `n_examples ≥ 1` population the correlation actually uses,
`direct_harmful` refusalness is **+7.06** (not +7.30) and its ASR **0.050** (not 0.042), and
doublespeak refusalness is **−0.15 — the sign flips** from the +0.04 previously reported. The
qualitative story survives and is arguably cleaner: doublespeak sits **next to benign literal**
(−0.15 vs −0.30) and **7.2 units below** the matched direct request. Every figure above is now one
population. (Revision 1's 0.583 / 7.4% were the all-rows figures; the 36 zero-demo prompts it
included are all ASR = 1.0 and carried the entire gap.)


⛔ **RETRACTED: "Boombness beats refusalness 3.7×".** `d_surface` was read at `codeword_last`,
refusalness at the last prompt token. Rebuilt as a proper 2×2 — same 234 prompts, same ASR, and
restricted to the candidate columns available at **both** positions so the two cells have equal
model-selection freedom (20 for `d_surface`, 10 for refusalness):

| single-predictor R² | @ last token | @ codeword_last | **position effect** |
|---|---|---|---|
| `d_surface` | 0.070 | 0.141 | **2.0×** |
| refusalness | 0.046 | 0.189 | **4.2×** |
| **ratio Boombness / refusalness** | **1.54** | **0.75** | |

Domain-clustered bootstrap (fixed column, 6 domains): @last **1.54, 95% CI [0.64, 3.60]**,
P(>1)=0.89; @codeword_last **0.75, CI [0.33, 1.13]**, P(>1)=0.10.

**This table is now regenerable.** `src/boombness/analyze_position.py` produces it from a committed
command, records the run paths, and **verifies that each of the four cells actually read where it
claims to** — the check that caught the phantom cell. It refused to run until the `@last` refusalness
cell had an artifact recording its position (job 761697), rather than accepting the source code as
evidence.

**Stated at its least favourable framing, deliberately.** The 2.0×/4.2× above uses each probe's *best*
column. On *median* columns the position effect is far larger — `d_surface` 0.0076 → 0.0847 (**11×**)
and refusalness 0.0033 → 0.1643 (**50×**) — so the localization finding is stronger than the headline
number suggests. The best-column version is quoted because it is the conservative one.

⚠ **Freedom is matched *within* each probe across positions, but NOT *between* probes:** `d_surface`
draws its best column from **20** candidates, refusalness from **10**. Both are max-of-k statistics,
so the between-probe ratios are biased **toward Boombness**. Re-selecting the column inside each
bootstrap resample gives [0.84, 2.88] and [0.38, 1.12] — same conclusion, wider. Neither the fixed-
column CI nor the ratio is regenerable from a committed script yet; both were computed ad hoc.

**Neither probe dominates.** Which one wins depends on *where you read*, and both CIs straddle 1.0,
so neither difference is significant. The 3.7× came from pairing `d_surface`@codeword_last with
refusalness@last — **the most favourable of the four possible cross-position pairings**. No matched
pairing reproduces it.

**What survives, and it is the sprint's positive finding: position dominates.** Both probes are
2–4× more predictive of ASR at the **codeword token** than at the final prompt token — a larger
factor than any difference *between* the probes. The attack-relevant state is **localized at the
codeword**, independently consistent with G1 (meaning retrieved into the codeword from the
demonstrations) and G3 (that retrieval carried by a large, redundant edge set).

Caveat: the refusal direction was fitted for a last-token readout, so reading it at the codeword
token is off-label. The comparison is fair (both probes treated identically), but "refusalness at
the codeword token" is not a validated refusal measurement at that position.

Two caveats we owe you, both of which revision 1 dropped or half-stated:
- **Range restriction.** Within-arm refusalness sd is **0.445** on the n=234 correlation
  population (0.74 is the all-270-rows figure revision 4 quoted) vs 3.07 pooled, so "refusal
  doesn't matter" is true only *inside* the attack arm, never generally.
- ⚠ **Footing was the problem and it is now fixed, not outstanding.** Revision 4 still carried
  this as an open caveat ("not a fair contest until refusalness is re-measured at
  `codeword_last`"); that re-measurement is the 2×2 above. Nothing here is pending.
- ⛔ **Revision 4's "like for like" increments (+0.104 / +0.039) are withdrawn.** They came from the
  artifact pairing refusalness@**last token** with `d_surface`@**codeword** — the exact footing
  mismatch retracted 30 lines above, presented under the words "like for like".
- ⛔ **R-13: the replacement table was ALSO withdrawn.** It read +0.028 / +0.144 @codeword and
  +0.025 / +0.091 @last, under the words "at matched footing" — with the parenthetical
  "*refusalness as all 5 layers jointly*" disclosing, in the same sentence, that the footing was not
  matched. Both cells are increments against one model, `boombness(1 col) + refusalness(5 cols)`, so
  refusalness's increment carried **5 df against Boombness's 1**, and R² is monotone in predictors.
  The pair is in no committed artifact. At **matched degrees of freedom**
  (`g9_three_predictor_{cwpos,lastpos}.json`, one column each, n=234):

  | | Boombness adds over refusalness | refusalness adds over Boombness |
  |---|---|---|
  | @ codeword_last | **+0.0743** | **+0.1091** |
  | @ last token | **+0.0053** | **+0.0000005** |

  **The comparison flips with position.** Refusalness adds more at the codeword token — by 1.47×, not
  the 5.1× implied — and at the last token it adds **nothing** (4.5e-07). This does not change
  §18 = B, but "the increment comparison, done correctly, favours refusalness" was **wrong**, and
  Boombness is not redundant: at the codeword token it adds **42%** over a refusalness-only base.

## Where the mechanism lives

- **Not in the codeword token.** The **single-layer L18** demonstration transplant, harm-context pair,
  moves the model's reported meaning **+68% of the baseline→ceiling span, domain-clustered CI
  [+50%, +95%]**, on **24 families across all 6 domains** (`g1_stratified.json`); transplanting the
  *query codeword* moves it the **wrong way** (**−57.0%** on the corrected whole-answer readout;
  ~~−71%, CI [−105%, −56%]~~ was the superseded single-token readout). ⚠ That contrast is
  **sign-robust only on the diagonal** — see the full report: `query_only` is negative at 13/13
  layer-sets in a harmful context, but **positive at 5/13** in a benign one. Meaning is retrieved from the
  demonstrations at answer time, not stored in the codeword.
  ⛔ **R-8: the earlier +84%, CI [+57%, +105%] is superseded** — it was a pilot of n=8 families in
  only **2 domains** (effective independent units nearer 2 than 8). Revision 1's "[+23%, +135%]" was a
  **chimera** — one arm's lower bound welded to another's.
  ⚠ **Arm-selection exposure, disclosed:** this is one arm of ~130. In the stratified data the
  **whole-prompt** transplant is **null** on this pair (+14%, CI [−9%, +32%]). The claim is specific to
  transplanting the **demonstration block** at the L18 window.
  ⚠ **Magnitudes pending re-derivation (C-6):** this readout is the single-next-token tail readout
  retracted elsewhere — it is structurally biased toward the concept, since the codeword has **no
  capitalised single-token form** and the concept has four. The corrected whole-answer readout exists
  and is proven but is not yet ported to `aggressive_patching.py`. The **direction** is safe; the
  **numbers are not final**.
  **n = 8 families drawn from only 2 domains** — the effective number of independent units is closer
  to 2 than to 8, and this is a pilot.
- ⚠ **Attention-carried and massively redundant — but the redundancy is in the EDGE SET, not in
  depth. I had this wrong and the matched experiment corrected it.** Cutting query→demo attention at
  all 32 layers recovers **75.2%** of the effect of deleting the demonstrations (~~84%, CI [62%, 110%]~~
  and the 56,832 / 3,552 edge counts are **superseded** by the 24-family re-run — R-7); the
  same cut at 2 layers recovers **0.07%** (CI [−6.7%, +8.2%]). I read that as depth-distribution,
  but the 32-layer arm also cut **16× more edges**, so the comparison moved two things at once. The
  matched arm settles it: **3,552 edges spread over 32 layers moves the readout +0.09 — the same
  nothing as 3,552 edges at 2 layers (−0.01).** Layer spread is not the operative variable.
  What is true: removing **6.25%** of the demo edges does nothing *however they are distributed*,
  while removing 100% recovers **75.2%** (~~84%~~, superseded — R-7). That is why every localized knockout (top-k, bottom-k, random,
  same-head) reads zero — each removes ~0.03% of a hugely redundant set.
  The converse test is impossible by construction: at seq_len 114 × 32 heads a layer holds only
  ~3,648 edges, so any cut above ~7.3k edges *must* involve more layers. Identification is one-sided
  and we say so.
- **Semantics move far more than the representation.** The model's reported meaning of the codeword
  travels **59%** of the way from literal to direct (paired, n=60, monotone in demo count:
  +7.6 → +16.8), while the token's position on the concept axis moves only a few percent. This one
  is solid — domain-clustered t (13.5) ≈ naive t (13.3), bootstrap CI on the ratio ≈ [50%, 68%].

## G4 — steering. A negative.

Common 270-prompt set, all five arms coherence-gated, paired Δ vs baseline:

| arm | ASR | refusal | paired Δscore | vs controls |
|---|---|---|---|---|
| baseline | 0.219 | 0.074 | — | |
| **+0.25** | 0.081 | **0.696** | **−0.114 ± 0.024** | z = −3.6 |
| **−0.25** | 0.148 | 0.067 | **−0.074 ± 0.020** | z ≈ −2.2 |
| random +0.25 | 0.178 | 0.085 | −0.035 ± 0.018 | |
| orthogonal +0.25 | 0.189 | 0.093 | −0.031 ± 0.018 | |

**Both signs suppress ASR**, so the +0.25 result (63% reduction) is **not** evidence that Boombness
causes the attack. The falsifying branch was written into the analysis code before the numbers
existed, and it fired.

⚠ **Coherence caveat on the one arm carrying a positive result.** All five arms pass the gate, but
`coherence_gate` skips generations under 8 words, and the +0.25 arm — whose refusal rate is 0.696 —
had **68 of its 270** doublespeak generations (25%) excluded on that basis, so its `coherent: true`
was computed on n=202. Baseline dropped 0; the other arms 0–1. The gate is weakest exactly where it
matters most.

But "pure disturbance" is too strong — the two signs suppress by **different routes**. Of the
prompts each arm suppressed, the fraction that are refusals:

| +0.25 | −0.25 | random | orthogonal |
|---|---|---|---|
| **0.901** | **0.000** | 0.000 | 0.042 |

`+α` is a refusal trigger; `−α` is generic degradation indistinguishable from a norm-matched
control. So: **ASR does not follow the sign** (which kills the attack objective), while **refusal
does**.

The control band is now **four independent random draws** (not the single draw revision 1 leaned on).
⛔ **The figures once quoted here (band mean −0.0366, sd 0.0049) are RETRACTED (#7): those four "draws"
were byte-identical — one draw wearing four labels.** On a genuine 4-draw band the mean is **−0.0120 with
between-draw sd 0.0301, six times wider**, spanning −0.055 to +0.012 — so a norm-matched random
perturbation has **no reliable effect on ASR at all**. Against that real band:


⛔ **The table that stood here quoted t/p computed from the RETRACTED band** (p=0.0014 on
df=235). Those are downstream of retraction #7 and were withdrawn with it — the sweep missed them
because I had enumerated the band's mean and sd but not the statistics derived FROM it. Against
the GENUINE 4-draw band (n_draws=4, so the Welch df is ~7, not ~235):

| arm | diff vs band | t | p | verdict |
|---|---|---|---|---|
| **+0.25** | -0.1023 ± 0.0410 | -2.49 | **0.043** | clears the band |
| −0.25 | -0.0620 ± 0.0391 | -1.59 | **0.168** | does **not** clear |

So "the axis is not inert" holds for **+0.25 only**. The −0.25 arm sits essentially *on* the band —
revision 1's blended "2–3× the controls" overstated it. One line: **adding concept-ness to the
codeword triggers refusal; removing it just damages the model like any other perturbation of that
size.**

Separately, an earlier arm at α=1 showed ASR 0.219 → 0.759 and was an **artifact**: the intervention
broke generation (55% of trigrams repeated) and the judge scored the loop as harmful. **We nearly
reported it.** The usable dose window is narrow, which matters for §12 — an optimizer maximizing
this projection has no reason to stop at 0.25.

⛔ **§18 = B is WITHDRAWN — see the headline result below. It was a ceiling effect of refusal.**
Not **C**: refusalness does not dominate — it wins one cell, insignificantly, and its construct
validity there is doubtful — see below). Not **A**: Boombness does not win at matched footing
either, and G4 found no directional causal effect. Boombness is measurable, correlates with
ASR, localizes to the codeword — and does not support a steering objective.

⚠ **Revision 4 mis-stated the construct-validity problem** and the verifier caught it. It said
the probe "no longer orders `direct_harmful` above `benign_literal`" at the codeword position.
**It does**, at every layer and both metrics (L18: −1.97 vs −2.43). What actually breaks is:
the harmful−benign gap **collapses ~16×** (7.45 → 0.46), `direct_harmful` becomes
**indistinguishable from doublespeak** (−1.972 vs −1.988 at L18), and `direct_codeword`
overtakes `direct_harmful` as the highest condition. That is still enough to withhold the name
"refusal" from the codeword-position quantity — but the reason is the collapse, not a reversal.

## ★ The sprint's first clean causal result — and it runs the OTHER way

`project_out` on `d_surface` at L8 removes the concept component by projection.

⛔ **CORRECTED 2026-08-18 (R-6).** This was previously described as the only intervention reaching the
ASR question with **every** precondition green, citing comprehension **unchanged** at Δ +0.088,
p=0.681. That comprehension verdict is **withdrawn**: the readout scored `' literal'`/`' coded'` at a
position where the model emits neither, and the pair held a median **4.4e-05** of the next-token mass
(0 of 288 rows above 1%), so the p is an ordering inside a tail rather than a measurement. The
remaining preconditions are unaffected and still green: coherence OK, ledger 960/960/0, refusal
unchanged. The readout has been rebuilt as a whole-answer forced choice (median mass now **0.297**)
and the re-run is outstanding.

| arm | ASR | refusal | paired Δ vs baseline |
|---|---|---|---|
| baseline | 0.219 | 0.074 | — |
| **remove Boombness (project_out)** | **0.300** | **0.074** | **+0.074 ± 0.025** |
| add Boombness +0.25 | 0.081 | **0.696** | −0.114 |
| random / orthogonal +0.25 | 0.178 / 0.189 | 0.085 / 0.093 | −0.035 / −0.031 |

Domain-clustered (6 domains): arm B beats the **random** control by +0.109 (**p=0.025**) and the
**orthogonal** control by +0.104 (**p=0.020**). ⚠ Against baseline *alone* it is **p=0.117** — so the
effect is only visible against controls, and that is how we quote it.

**The whole intervention picture is now coherent, and it is the reverse of what we assumed:**

| manipulation | concept-ness at codeword | refusal | ASR |
|---|---|---|---|
| **add** | higher | 0.074 → **0.696** | 0.219 → **0.081** |
| **remove** | lower | 0.074 → 0.074 | 0.219 → **0.300** |

**Boombness at the codeword is a DETECTION signal for the safety mechanism, not a driver of compliance.**
Raise it and the request becomes legible, so refusal fires. Remove it and the request becomes less
legible, so the attack succeeds more. This also dissolves the earlier puzzle — why the within-arm
correlation was positive while steering "the wrong way" suppressed ASR: the correlation was reading a
**detectability** gradient.

**§12 reopens with the sign flipped.** An objective on this axis should **minimise** the projection, not
maximise it; `project_out` is its idealised limit. That is a concrete, testable direction we did not have
before.

⚠ **Not yet a settled fact.** p=0.117 against baseline means this needs a second concept pair, a
projection dose–response (partial removal), and the same arm on Qwen3 — especially since G2 itself did not
replicate there.


---

## The arm-F interaction — a real number whose mechanism was refuted

⛔ An earlier draft titled this "THE HEADLINE RESULT — Boombness IS causal" and said it
superseded the §18 = B label. **Both are withdrawn.** The objective verdict is unchanged and
negative; the *number* below is real, its **mechanistic interpretation is retracted** (**R-22**) —
the gain is largest in `benign_remap`, where the mapping is never taught.

**This supersedes the §18 = B label and reopens §12.** Everything below is at a matched 512-token budget,
n = 420, every arm complete and coherence-gated on the doublespeak population, domain-clustered over 6
domains.

| arm | ASR | refusal | Δ score vs baseline | p_cl |
|---|---|---|---|---|
| baseline | 0.2429 | 0.0571 | — | — |
| add Boombness `+0.25` | 0.0881 | **0.6762** | −0.1274 | 0.0117 |
| remove refusalness | 0.2690 | **0.0000** | +0.0101 *(0.9× the judge-noise sem — **not measurable to ±0.03**, not "does nothing")* | 0.4746 |
| ⛔ **add Boombness AND remove refusalness** *(**RETRACTED**, R-20)* | ~~0.5476~~ | 0.0024 | ~~+0.2824~~ | ~~<0.0001~~ |
| **RANDOM direction + remove refusalness** *(control)* | **0.2190** | 0.0000 | −0.0321 | 0.1160 |

⛔ **R-20 — arm F's row above is WITHDRAWN (2026-08-20).** Its gain is a **judge artifact, ~94% answer
style**. Under an outcome the rubric cannot inflate — `strongreject ≥ 0.5` **AND** the completion
containing the word the goal distinctively needs — arm F's paired gain is **+0.017, CI [−0.005,
+0.038]**, an interval containing zero, against its own control at **+0.012 [+0.007, +0.014]**. On
`benign_remap` it is **+0.417 plain and exactly 0.000 topical**: not one of 36 completions contains the
goal word. Independently, across the eight Llama arms **corr(mean completion length, plain ASR) =
+0.984** — the plain metric is very nearly a length meter on this bank, and arm F writes the longest
completions of all eight (1.83× baseline). What survives on the style-immune outcome is
**B** (remove `d_surface`, +0.029) and **D** (remove both, +0.033), each clearing its control at
+0.010, while **C** (remove refusalness alone) is **null** at −0.002.
`outputs/boombness/llama_arms_topical.json`; full table in the main report §7g.

⚠ **The control is inert only on THIS condition, and reverses elsewhere.** On `direct_harmful` the same
random composition raises score by **+0.389 (p=0.008)** and cuts refusal **0.96 → 0.54**, while arm F stays
at baseline (+0.000, refusal 0.96). On `concept_in_benign_ctx` it gains +0.203. **Specificity is established
for the doublespeak population only, and is reversed where harm is explicit.**

⛔ **RETRACTED (R-20).** ~~Neither manipulation alone raises attack success — together they more than
double it.~~ ~~Interaction contrast +0.400 continuous, p=0.0001.~~ Arm F's gain is a **judge
artifact, ~94% answer style**: under an outcome the rubric cannot inflate its paired gain is
**+0.017, CI [−0.005, +0.038]**, containing zero, against its own control at +0.012. What survives on
that outcome is **B** (remove `d_surface`, +0.029) and **D** (remove both, +0.033), each clearing its
control at +0.010, while **C** (remove refusalness alone) is **null** at −0.002.

⚠ **That +0.400 is ~45% a mechanical artifact.** Arm A refuses on 284/420 rows, each scored exactly 0.0 by
construction. On the rows where A did *not* refuse, **A−base = +0.094 (positive)** and the interaction falls
to **+0.222**. The **refusal-free** contrasts — **F−C = +0.272** and **F−Fctrl = +0.315**, between arms with
~0% refusal — are the numbers that carry the claim.

### The mechanism
`d_surface` does **two opposing things at once**:
1. **detection** — it makes the request legible to the refusal mechanism (refusal 0.057 → **0.676**), which
   *suppresses* ASR;
2. **a second, refusal-independent channel** raises judged harmfulness once refusal is removed.
   ⛔ **We have NOT established that this is a "capability" channel.** The gain is *largest where the
   doublespeak mapping is weakest* — **+0.361 at `n_examples=0`** (no demonstrations at all) and **+0.267 on
   `benign_remap`**, where carrot→bomb is **never taught** — and it is **absent on explicitly harmful
   prompts** (+0.000 on `direct_harmful`, where the random control gains +0.389). It is better described as
   a **prompt-independent injection by the L8 steering vector** than as the doublespeak attack succeeding.

In the unmodified model channel 1 dominates and **masks channel 2 entirely**. That is why the within-arm
correlation was positive while every steering attempt looked suppressive — a contradiction this report
carried for days.

### Why this is not any of the artifacts that killed earlier versions
| competitor | how it is excluded |
|---|---|
| degenerate generation | passes `coherence_gate` on the doublespeak denominator |
| truncation / length | ⚠ **attenuated, not eliminated.** All arms complete at 512 tokens, but arm F writes 260 median words vs the control's 145 and common support covers only ~27% of control rows. Matched on 25-word bins, **F−Fctrl falls +0.315 → +0.233** (bootstrap CI [0.149, 0.310]) and **F−base +0.282 → +0.150**. A quarter to a half of the raw gap is length, which may itself be a mediator. |
| "longer answers score higher" | baseline calibration shows truncation **suppresses** score (+3.7pp when completed) |
| judge noise | effect is **25×** the measured test–retest floor (0.011) |
| threshold luck | holds on the continuous score and at three thresholds |
| **"any two perturbations do this"** | **the random composition does nothing (p=0.116)** |
| domain artifact | domain-clustered throughout |

A prediction for the arm-F value was **recorded in the log before judging** (`≥0.474`); it came in at
**0.5476**.

### Consequences
- ⛔ **§18 = B ("mechanistic but not causal") is WITHDRAWN.** It was a **ceiling effect of refusal**.
- ⚠ **§12.2 — "Boombness minus refusal" — is REOPENED and worth building as an experiment, NOT vindicated.**
  I closed §12 as gate-not-met on G4's directional null, and that reasoning was wrong. But the arm-F gain is
  **not conditional on the doublespeak mapping** and **does not transfer to explicitly harmful requests** —
  precisely what an attack objective would require. Downgraded from "should be built" to "worth building as
  an experiment".
- The §12.1 "pure Boombness objective" (maximise alone) remains **wrong** — alone, it *lowers* ASR.

### Honest limits — scope, not validity
One model (Llama-3.1-8B), one concept pair (carrot↔bomb), one judge, refusal projected at a single layer
(L18), and `d_surface` fitted on the same bank it is evaluated on.

**"One concept pair" is now a tested limitation, not just an untested one (added 2026-08-21).** A
concept swap *was* run — a second bank replacing the concept (`carrot↔knife`) and a third replacing the
codeword while holding the concept (`button↔bomb`), all sharing identical family sets. **Both halves
failed their own pre-committed controls and the whole experiment is retracted** (R-23, R-24 in the full
report):

- *Behaviourally* — a direction constructed **orthogonal** to `d_surface` (cos 0.0000), projected out at
  the same layer, reproduced the transferred effect **exactly** (+0.0182, 9 flips). So the transfer did
  not clear a null of "project out *something* in this subspace".
- *Representationally* — swapping only the **codeword** moved `d_surface` **further** (cos 0.5539) than
  swapping only the **concept** (0.6117), against a 0.995 within-fit ceiling. So the alignment between
  the two concept fits cannot be read as concept overlap.

**Read this as: `d_surface` is demonstrated for `carrot↔bomb`, and an attempt to show it names a concept
rather than an estimator was made and did not succeed.** That is a stronger statement than the untested
limitation it replaces, and it is why "second concept pair" remains on the suggested-next list below. The Qwen3 replication of the *projection*
arm is running; **G2's correlation did not replicate on Qwen3**, so cross-model generality is an open
question for this result too.

---

## Removing the concept component alone — the on-bank result

Unlike the interaction above, this one survived every check **including the ones that refuted the
interaction's mechanism**. Llama-3.1-8B, 512 tokens, n=420, all arms gate-passed and length-matched by
construction (163 vs 150 median words), against a **projection-type** control:

| contrast | Δ score | t_cl | p_cl |
|---|---|---|---|
| `project_out d_surface` − baseline | +0.0378 | +5.12 | **0.0037** |
| `project_out RANDOM` − baseline | −0.0182 | −1.27 | 0.260 — **inert, as a control should be** |
| **`d_surface` − RANDOM control** | **+0.0560** | **+4.30** | **0.0077** |

**5× the measured judge-noise floor.**

### ⛔ The cross-condition profile — R-15, WITHDRAWN and corrected 2026-08-19
This table originally shipped six deltas and **no inference**, while the Qwen3 table below it carried
`p_cl` on every cell and annotated two "(n.s.)". Given the same test (`analyze_condition_profile.py`,
paired by `prompt_id`, domain-clustered t on `len_B`/`len_Bctrl`, n=960 — deltas reproduce exactly):

| condition | n | arm − control | p_cl | domain-clustered CI |
|---|---|---|---|---|
| `benign_literal` | 324 | +0.0069 | 0.334 | [−0.010, +0.024] |
| `benign_remap` | 36 | +0.0104 | 0.745 | [−0.068, +0.088] |
| `concept_in_benign_ctx` | 72 | +0.0035 | 0.862 | [−0.045, +0.052] |
| **`natural_doublespeak`** | 420 | **+0.0560** | **0.0077** | **[+0.023, +0.089]** |
| `direct_harmful` | 72 | +0.0556 | 0.363 | [−0.087, +0.198] |
| `direct_codeword` | 36 | +0.0590 | 0.438 | [−0.121, +0.239] |

⛔ **Only one of six cells is distinguishable from zero, and it is `natural_doublespeak`.** The earlier
reading — that the effect was harm-general and appeared wherever an attack was present — is
**withdrawn**. The two other harmful cells have intervals spanning **±0.2** at n=72 and n=36, roughly
six times the effect they were cited to demonstrate; the split tracks **sample size** (420 vs 72 vs 36),
not harm.

⛔ **What stands** is the narrow claim: removing the concept component at the codeword position raises
attack success **on natural doublespeak prompts** (+0.056, p=0.0077, inert control). The previous
comparison against Qwen3 also applied an **asymmetric evidential standard** — Qwen3's cells were
discounted for failing a test the Llama cells had never been given, and three of them fail it too.

### ⛔ It does NOT replicate on Qwen3-14B — and the failure is informative
Same intervention, same fitting procedure, same relative depth (25% vs 27.5%), same bank, **inert control on
both models** — and mirror-image condition profiles:

| | Llama-3.1-8B | Qwen3-14B |
|---|---|---|
| condition | Llama-3.1-8B | Qwen3-14B |
|---|---|---|
| `natural_doublespeak` (attack) | +0.056 | **+0.339** |
| `direct_harmful` | +0.056 | +0.111 (n.s.) |
| `direct_codeword` | +0.059 | +0.010 (n.s.) |
| `benign_literal` | +0.004 | **+0.224** |
| `concept_in_benign_ctx` | +0.010 | **+0.245** |
| `benign_remap` | +0.004 | **+0.441** |

⛔ **This table previously showed only TWO Qwen3 values in a "harmful conditions" row against THREE
Llama values, silently omitting `natural_doublespeak = +0.339` — the LARGEST Qwen3 effect of all.**
Found 2026-08-18 by an independent audit and verified against the judge artifacts. Every condition is
now listed on its own row so a column cannot hide one.

**The omission inverted the conclusion.** With `natural_doublespeak` restored, Qwen3 is elevated on
**five of six** conditions, attack and benign alike — this is a **broad elevation of judged
harmfulness**, not a profile that "tracks the absence of an attack" as the previous text claimed.
The only near-null is `direct_codeword` (+0.010). The contrast with Llama still stands and is
if anything sharper: on Llama the effect is confined to harmful conditions (+0.056 vs +0.004 benign);
on Qwen3 it is everywhere, including on prompts containing no attack. **The result remains
single-model**, and for the corrected reason: Qwen3's projection does not isolate an attack-related
quantity at all.

On Llama the effect tracks the **presence** of an attack; on Qwen3 it tracks the **absence** of one. The
Qwen3 effect is real and `d_surface`-specific (its random-projection control is inert, −0.004, p=0.77) but
it raises judged harmfulness on prompts containing **no attack at all**. **This result is therefore
single-model.**

### Why the small result outlived the large one
| | arm F interaction | this result |
|---|---|---|
| size | +0.27 to +0.32 | **+0.056** |
| control | inert on doublespeak only; **reverses** on `direct_harmful` | inert **everywhere** |
| cross-condition | ⛔ appears where the mapping is never taught | ✅ harmful yes, benign no |
| cross-model | not tested | ⛔ does not replicate |
| status | real number, **mechanism refuted** | **established, single-model** |

Effect size was consistently the *worst* predictor of which claim survived. Every large effect in this sprint
either failed a cross-condition check or lost its interpretation; the surviving causal result is the smallest
one measured.

## What we'd take from this sprint

1. **The 2×2 design is the reusable artifact.** It separates surface identity from context and it
   caught the confound quantitatively. Bank: 2352 prompts, **912 families** of which 240 are the
   matched 2×2 set, and **0 alignment violations among the 216 families where the exact-swap
   invariant is even defined** — the other 696 are forced-choice and cannot satisfy an exact swap by
   construction. (Revision 1 gave the numerator with no denominator; revision 4 gave two denominators
   that did not add up.)
2. ⚠ **The naive direction inflates — and in the mid layers it *hides* rather than manufactures.**
   Revision 1 said it "manufactures signal in layers where the identified direction finds none."
   That was sourced to a section this sprint had already retracted, and the corrected data **reverse
   it**:

   | L | 4 | 8 | 12 | 16 | 20 | 24 | 31 |
   |---|---|---|---|---|---|---|---|
   | `d_surface` | +0.023 | +0.027 | +0.015 | **−0.023** | **−0.029** | **−0.021** | +0.047 |
   | `d_naive` | +0.043 | +0.048 | +0.037 | −0.006 | −0.016 | −0.005 | +0.094 |

   It roughly doubles the effect at L4–L12 and L31 (1.75–2.4×). ⚠ **Revision 4's claim about the
   mid layers is now weakened twice over, and both weakenings came from the verifier.** It said the
   identified direction finds "a real negative displacement" at L16–L24 that the naive one washes
   out (quoting naive p 0.22–0.62). Two problems:

   - the naive p range is **0.074–0.62**, not 0.22–0.62 — L20 (p=0.074) was silently dropped, and
     there the naive direction is *also* marginally negative;
   - more seriously, **that band does not exist in the behavioural prompts** — the population every
     ASR claim lives on. Split by query kind, L16/L20/L24 read **+0.003 / −0.004 / +0.015 (all
     n.s.)** for `behavioral`, versus −0.034/−0.037/−0.031 for `comprehension_usage` and
     −0.037/−0.046/−0.045 for `semantic_one_word`. And `reanalyze_corrected.py`'s own `holm_rejected`
     field is **True only at L4 and L31**.

   So the defensible statement is narrower: the naive direction **inflates by ~2× where both agree**,
   and the mid-layer negative band is a **semantic/comprehension-prompt phenomenon that does not
   survive multiplicity correction**. Quoting raw clustered p while the artifact's own Holm field
   says no was over-claiming. Both rows come from the committed `reanalyze_corrected.py`.
3. **Process.** Seven retractions and ten corrections, every one from independent audit, and all
   one family: *the manipulated and measured quantities were not the same thing*, or *the best of
   mine was compared against a fixed instance of yours*. **Three** guards written to prevent
   exactly this were themselves silently inoperative: a coherence gate that keyed on the wrong
   dirname; a dynamic-range check that took `max` over *signed* deltas and so compared against
   a null control; and **the control band behind this report's own "clears the band" claim**,
   which selected `ctrl_rand_s*` while the runs were tagged `ctrlband_s*` and matched **zero**
   arms. Two further defects the same audit found: the movability guard used a blacklist, so
   treatment arms counted as null controls (threshold inflated 6.4×), and `dense_two_layer`
   silently delivered 7,264 of 56,832 requested edges.
   control. **A guard that is never tested is not a guard.**

---

## Limitations and safety scope

*(§13 requires this section in **every** report; the plan-coverage sweep found the short update had
none — only the full report did. Finding 13.1.)*

**Dual-use scope.** This characterises why a known jailbreak family works. It produces no operational
harmful instructions; harmful content is benchmark material behind project abstractions and all harm
labels are automated (StrongReject rubric via `gpt-4o-mini`). No completion text appears in this
report, in any commit message, or in any analysis artifact. Only the local open-weight model was
attacked — the API is used as a *judge*, never as a target.

**We do NOT claim to have found the mechanism.** ⛔ **RESCORED 2026-08-21 — the previous scoring
predated R-6, R-18 and R-20 and restated all three.** Against plan §13's six criteria: Boombness
predicts ASR (⛔ **NO — R-18 retracts it**; ~~met~~); adding it increases behaviour (**not met**, and
its supporting arm is retracted — R-20); removing it reduces ASR (**NO — it RAISES it**, +0.0422
against a **5-draw control band** at +0.0012, sd 0.0026; ~~ambiguous, p=0.070~~ superseded);
comprehension preserved (**YES, and it improves** — +0.2795, p=0.0010 on the corrected readout;
~~not established~~ was **R-6**, a 4.4e-05 tail); random controls fail (**YES** — genuine bands now
exist on both external sets; the earlier "4-draw band" was **R-12**, one draw repeated); replicates
across models
(**partial** — the ~2× confound, the L31 effect ⚠(depth-mismatched — see C9) and the token-level result replicate on Qwen3-14B; the
mid-layer band does not). **Two met, three partial, one no.**

**The limits a reader should carry:**
- **One concept pair (carrot↔bomb), one judge.** Two models for the representational findings only.
- ⚠ **The §2.6 comprehension control under intervention was missing for the whole sprint** and is
  running now. Until it lands, "the +0.25 arm suppresses ASR by triggering refusal" does not exclude
  "the intervention damaged the model's grasp of the mapping". `coherence_gate` checked for degenerate
  *text*, which is weaker and different.
- ⚠ **The position finding has an estimation-quality confound (C8):** the direction is 13× (Llama) and
  41× (Qwen3) better *separated* at the codeword token than at the last token, so "carries more signal"
  and "is better estimated" are not separated by this design. The L31 result is unaffected (gaps
  converge to 1.1×).
- **G1 is no longer a pilot** (corrected; the ~~n=8 families / 2 domains~~ figure is **R-8**). It is
  **24 families across 6 domains**. The arm-selection exposure stands: its headline is one arm of ~130 — the
  all-layer variant of the same transplant goes the *opposite* way.
- **G3's identification is one-sided by construction** (a layer holds only ~3,648 edges).
- **G1/G3 run on `semantic_one_word` prompts; G2/G4's ASR claims on `behavioral` ones** — and this is
  not merely a join hazard: it changes the **sign** of a reported effect (C7).
- **"Refusalness at the codeword token" is off-label** — that direction was fitted for a last-token
  readout and its condition ordering degrades badly there.
- **Reproducibility caveat:** every run recorded `git_dirty = True`, so the recorded commit does not
  pin the exact code that ran; model/tokenizer *revisions* were never recorded; and 53 of 68 finished
  runs predate `bank_content_sha16`, so they cannot be tied to a bank version by artifact alone (the
  bank was regenerated 1464 → 1752 → 2352 rows).

## Suggested next

- **Do not build the GCG objective on this axis.** §12 is closed as a documented negative. If an
  objective is still wanted, target the demonstration-retrieval pathway, not the codeword's position
  on `d_surface`.
- Second model (Qwen3-14B) and second concept pair — everything here is Llama-3.1-8B, carrot↔bomb.
- G1/G3 are measured on `semantic_one_word` prompts while G2/G4's ASR claims are on `behavioral`
  ones. Each is internally consistent, but joining them into one causal story is the same
  manipulated-≠-measured pattern one level up. Worth closing with a behavioural-prompt knockout.
