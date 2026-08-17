# Boombness sprint — short update

**For:** Matan, Mahmood · **From:** Omer · **Date:** 2026-08-17
**Full log:** `docs/BOOMBNESS_SPRINT_PROGRESS.md` · **Plan:** `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md`
**Branch:** `behavioral-causality-sprint` · all four gates answered.

> **This is revision 2.** An independent audit on 08-17 found that one retracted quantity was still
> load-bearing in revision 1, that the headline p-value ignored domain clustering, and that the
> §10 depth claim was not identified. All three are corrected below and the affected sentences are
> marked ⚠. Read this version, not the one I sent earlier.

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
| **within-domain permutation — cite this one** | **5.0e-04** |

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
| direct harmful request | **+7.30** | 0.042 | 96% |
| doublespeak | **+0.04** | **0.219** | **0.9%** |
| mapping stated outright | +0.10 | **0.375** | 0% |

⚠ Revision 1 quoted **0.583** and **7.4%** here — those are over *all* rows including the 36
zero-demo prompts that the correlation analysis excludes on principle (no demonstrations ⇒ no
codeword mapping ⇒ not a doublespeak prompt). Those 12 zero-demo `direct_codeword` rows are all
ASR = 1.0 and carried the entire gap. Headline table and headline correlation must be on the same
population; they now are.

⛔ **RETRACTED (this replaces revision 2's claim).** I reported that within the doublespeak arm
Boombness explains ~3.7× more than refusalness (R² 0.141 vs 0.039) and called it the sprint's most
robust number. **It was a position artifact.** The two predictors were read at different tokens —
`d_surface` at `codeword_last`, refusalness at the last prompt token. Re-measured at the same token:

| | refusalness @ last | refusalness @ **codeword_last** |
|---|---|---|
| best single-layer R² | 0.039 | **0.176** |
| all-layers joint R² | 0.073 | **0.257** |
| `d_surface|L12|proj` R² | 0.141 | 0.141 |
| **ratio** | **3.66** | **0.80** |

At matched position **refusalness is the better predictor** (ρ = +0.405 at L18, p = 1.2e-10, vs
Boombness +0.307); Boombness adds only +0.04–0.08 over it, while refusalness jointly adds +0.14 over
Boombness. The 3.7× survived nested CV and leave-one-domain-out — but those resample *rows*, and no
resampling fixes a contrast whose arms sit at different positions.

Two caveats we owe you, both of which revision 1 dropped or half-stated:
- **Range restriction.** Within-arm refusalness sd is 0.74 vs 3.07 pooled, so "refusal doesn't
  matter" is true only *inside* the attack, never generally.
- ⚠ **Footing mismatch.** The two predictors are read at **different token positions** —
  refusalness at the last token, `d_surface` at `codeword_last`. Part of "Boombness beats
  refusalness" is "the codeword position beats the last position." This is not a fair contest until
  refusalness is re-measured at `codeword_last`.
- The increments quoted before were asymmetric (1-vs-1 against 5-vs-1). Like for like: Boombness
  adds **+0.104** over refusalness-L12; all five refusalness layers jointly add **+0.039** over
  Boombness.

## Where the mechanism lives

- **Not in the codeword token.** Transplanting the *demonstration* states moves the model's reported
  meaning **+84% of the baseline→ceiling span, 95% CI [+57%, +105%]**; transplanting the *query
  codeword* moves it the **wrong way**. Meaning is retrieved from the demonstrations at answer time,
  not stored in the codeword.
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

But "pure disturbance" is too strong — the two signs suppress by **different routes**. Of the
prompts each arm suppressed, the fraction that are refusals:

| +0.25 | −0.25 | random | orthogonal |
|---|---|---|---|
| **0.901** | **0.000** | 0.000 | 0.042 |

`+α` is a refusal trigger; `−α` is generic degradation indistinguishable from a norm-matched
control. So: **ASR does not follow the sign** (which is what kills the attack objective), while
**refusal does**. "The axis is not inert" is solid for +0.25 (z = −3.6) and weak for −0.25 (~2σ);
revision 1 blended these into one "2–3×" and overstated the negative arm. Each control is still a
single random draw — four more are running to turn that into a proper band.

Separately, an earlier arm at α=1 showed ASR 0.219 → 0.759 and was an **artifact**: the intervention
broke generation (55% of trigrams repeated) and the judge scored the loop as harmful. **We nearly
reported it.** The usable dose window is narrow, which matters for §12 — an optimizer maximizing
this projection has no reason to stop at 0.25.

**§18 label: outcome B — mechanistic but not causal.**

## What we'd take from this sprint

1. **The 2×2 design is the reusable artifact.** It separates surface identity from context and it
   caught the confound quantitatively. Bank: 2352 prompts, 240 matched families, **0 alignment
   violations among the 216 families where the exact-swap invariant is even defined** (696
   forced-choice families cannot satisfy it by construction — revision 1 gave the numerator without
   the denominator).
2. ⚠ **The naive direction inflates — and in the mid layers it *hides* rather than manufactures.**
   Revision 1 said it "manufactures signal in layers where the identified direction finds none."
   That was sourced to a section this sprint had already retracted, and the corrected data **reverse
   it**:

   | L | 4 | 8 | 12 | 16 | 20 | 24 | 31 |
   |---|---|---|---|---|---|---|---|
   | `d_surface` | +0.023 | +0.027 | +0.015 | **−0.023** | **−0.029** | **−0.021** | +0.047 |
   | `d_naive` | +0.043 | +0.048 | +0.037 | −0.006 | −0.016 | −0.005 | +0.094 |

   It roughly doubles the effect at L4–L12 and L31 (1.75–2.4×), but at L16–L24 the *identified*
   direction finds a real negative displacement (clustered p 0.009–0.053) that the naive direction
   washes out (p 0.22–0.62). Both rows now come from the committed `reanalyze_corrected.py`.
3. **Process.** Four retractions and three corrections, every one from independent audit, and all
   one family: *the manipulated and measured quantities were not the same thing*, or *the best of
   mine was compared against a fixed instance of yours*. Two guards written to prevent exactly this
   were themselves silently inoperative until the 08-17 audit — a coherence gate that never bound,
   and a dynamic-range check that took a max over signed values and so compared against a null
   control. **A guard that is never tested is not a guard.**

## Suggested next

- **Do not build the GCG objective on this axis.** §12 is closed as a documented negative. If an
  objective is still wanted, target the demonstration-retrieval pathway, not the codeword's position
  on `d_surface`.
- Finish the edge-count-matched knockout before anyone repeats the depth-redundancy claim.
- Re-measure refusalness at `codeword_last` so the 3.7× is a fair contest.
- Second model (Qwen3-14B) and second concept pair — everything here is Llama-3.1-8B, carrot↔bomb.
- G1/G3 are measured on `semantic_one_word` prompts while G2/G4's ASR claims are on `behavioral`
  ones. Each is internally consistent, but joining them into one causal story is the same
  manipulated-≠-measured pattern one level up. Worth closing with a behavioural-prompt knockout.
