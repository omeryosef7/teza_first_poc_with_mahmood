# Boombness sprint — short update

**For:** Matan, Mahmood · **From:** Omer · **Date:** 2026-08-17
**Full log:** `docs/BOOMBNESS_SPRINT_PROGRESS.md` · **Plan:** `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md`
**Branch:** `behavioral-causality-sprint` · all four gates answered.

> **This is revision 5. Read only this one.**
> - Revision 1's headline "Boombness beats refusalness 3.7×" is **retracted** — the two predictors
>   were read at different tokens. That retraction stands.
> - Revision 3 then claimed refusalness *wins* at matched position and moved the label to **C**.
>   **That was also wrong**: it rested on a cell that was never measured (a wiring bug meant the
>   "last token" run moved the direction-fitting position but not the readout). Rerun on real cells,
>   **neither probe dominates** — both confidence intervals straddle 1.
> - **§18 settles at B.** The surviving positive finding is about *position*, not direction.
>
> - Revision 4 passed independent verification on all ten claim clusters, but the verifier found
>   **two wrong tables and thirteen disclosure gaps**, fixed here. The two that mattered: the
>   condition table was still on a mixed population (one cell's **sign** flipped), and the
>   "like for like" increment bullet was itself built on the mixed footing this report retracts.
>
> Corrections ⚠, retractions ⛔.

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

On the corrected direction, **Boombness predicts attack success within the doublespeak arm**:
Spearman **ρ = +0.307** at L12 (`d_surface|L12|proj`), **+0.302 after partialling out the
residual-stream norm**, n = 234, 100% prompt coverage.

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
  mismatch retracted 30 lines above, presented under the words "like for like". At matched footing
  (both probes at one position, refusalness as all 5 layers jointly):

  | | Boombness adds over refusalness | refusalness adds over Boombness |
  |---|---|---|
  | @ codeword_last | **+0.028** | **+0.144** |
  | @ last token | **+0.025** | **+0.091** |

  **Refusalness adds more at both positions**; revision 4's bullet implied the opposite. This does
  not change §18 = B — on single-predictor R² neither probe dominates and both ratio CIs straddle
  1 — but the increment comparison, done correctly, favours refusalness.

## Where the mechanism lives

- **Not in the codeword token.** The **single-layer L18** demonstration transplant, harm-context pair,
  moves the model's reported meaning **+84% of the baseline→ceiling span, 95% CI [+57%, +105%]**;
  transplanting the *query codeword* moves it the **wrong way** (−0.58 to −0.81). Meaning is retrieved
  from the demonstrations at answer time, not stored in the codeword.
  ⚠ **Arm-selection exposure, disclosed:** this is one arm of ~130 in the pilot, and it is not
  uniform — in the *same* context pair the **all-layer** demonstration transplant moves the readout
  strongly the **wrong way** (−0.76, CI [−1.49, −0.21]). "Transplanting the demonstrations moves the
  meaning +84%" is true of the L18 window, not of demonstration transplants in general.
  ⚠ Revision 1's "[+23%, +135%]" was a **chimera** — one arm's lower bound welded to another's. The
  interval above is a paired bootstrap over families; the old delta-method interval was too *wide*
  (it propagated the span as if baseline and ceiling were independent, when they correlate +0.63).
  **n = 8 families drawn from only 2 domains** — the effective number of independent units is closer
  to 2 than to 8, and this is a pilot.
- ⚠ **Attention-carried and massively redundant — but the redundancy is in the EDGE SET, not in
  depth. I had this wrong and the matched experiment corrected it.** Cutting query→demo attention at
  all 32 layers recovers **84%** (CI [62%, 110%]) of the effect of deleting the demonstrations; the
  same cut at 2 layers recovers **0.07%** (CI [−6.7%, +8.2%]). I read that as depth-distribution,
  but the 32-layer arm also cut **16× more edges**, so the comparison moved two things at once. The
  matched arm settles it: **3,552 edges spread over 32 layers moves the readout +0.09 — the same
  nothing as 3,552 edges at 2 layers (−0.01).** Layer spread is not the operative variable.
  What is true: removing **6.25%** of the demo edges does nothing *however they are distributed*,
  while removing 100% recovers 84%. That is why every localized knockout (top-k, bottom-k, random,
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
They land within 0.010 of each other — band mean **−0.0366, between-draw sd 0.0049** — so generic
perturbation at this dose is highly reproducible. Against that band:

| arm | diff vs band | t | p | verdict |
|---|---|---|---|---|
| **+0.25** | −0.0778 ± 0.0241 | −3.23 | **0.0014** | **clears the band** |
| −0.25 | −0.0375 ± 0.0206 | −1.82 | 0.070 | **does not clear** |

So "the axis is not inert" holds for **+0.25 only**. The −0.25 arm sits essentially *on* the band —
revision 1's blended "2–3× the controls" overstated it. One line: **adding concept-ness to the
codeword triggers refusal; removing it just damages the model like any other perturbation of that
size.**

Separately, an earlier arm at α=1 showed ASR 0.219 → 0.759 and was an **artifact**: the intervention
broke generation (55% of trigrams repeated) and the judge scored the loop as harmful. **We nearly
reported it.** The usable dose window is narrow, which matters for §12 — an optimizer maximizing
this projection has no reason to stop at 0.25.

**§18 label: outcome B — mechanistic but not causal.**
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
3. **Process.** Five retractions and five corrections, every one from independent audit, and all
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

## Suggested next

- **Do not build the GCG objective on this axis.** §12 is closed as a documented negative. If an
  objective is still wanted, target the demonstration-retrieval pathway, not the codeword's position
  on `d_surface`.
- Second model (Qwen3-14B) and second concept pair — everything here is Llama-3.1-8B, carrot↔bomb.
- G1/G3 are measured on `semantic_one_word` prompts while G2/G4's ASR claims are on `behavioral`
  ones. Each is internally consistent, but joining them into one causal story is the same
  manipulated-≠-measured pattern one level up. Worth closing with a behavioural-prompt knockout.
