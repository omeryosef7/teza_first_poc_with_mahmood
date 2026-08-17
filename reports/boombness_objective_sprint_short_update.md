# Boombness sprint — short update

**For:** Matan, Mahmood · **From:** Omer · **Date:** 2026-08-17
**Full log:** `docs/BOOMBNESS_SPRINT_PROGRESS.md` · **Plan:** `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md`
**Branch:** `behavioral-causality-sprint` · one gate (G4) still resolving.

---

## Main finding

**The plan's confound is real, and fixing it changes the measurement.** The existing benchmark
compares a harm-domain arm against a benign arm that is *a different story* (string similarity
0.33), so the natural "Boombness" direction — `mean(h_bomb) − mean(h_carrot_benign)` — is
`bombness + explosive-context-ness`. We replaced it with a 2×2 (surface word × demo valence) that
identifies the two separately:

```
d_surface = ½[(B−C) + (E−A)]     the surface-word effect, context matched  ← Boombness
d_context = ½[(C−A) + (B−E)]     what the naive direction mostly measures
```

On the corrected direction, **Boombness predicts attack success within the doublespeak arm**:
Spearman **ρ = +0.307** at L12 (`d_surface|L12|proj`), **+0.302 after partialling out the
residual-stream norm**, p = 2.6e-06, n = 234, positive in 5 of 6 domains, Holm-corrected, 100%
prompt coverage.

## The attack works by removing refusal — but that is not what varies *within* it

| | mean refusalness (L18) | ASR | refusal rate |
|---|---|---|---|
| direct harmful request | **+7.30** | 0.042 | 96% |
| doublespeak | **+0.04** | **0.219** | **7%** |
| mapping stated outright | +0.10 | **0.583** | **0%** |

To the refusal direction a doublespeak prompt looks **benign** (+0.04 vs benign −0.15) while the
matched direct request sits at +7.30. That is the between-arm story.

*Within* the doublespeak arm, though, refusalness explains almost nothing and Boombness explains
~3.7× more (R² 0.141 vs 0.038; Boombness adds +0.104 over refusalness, refusalness adds +0.039 over
Boombness). Caveat we owe you: that low refusal R² is **range restriction** (within-arm sd 0.74 vs
pooled 3.07), so "refusal doesn't matter" is true only *inside* the attack, never generally.

## Where the mechanism lives

- **Not in the codeword token.** Transplanting the *demonstration* states moves the model's reported
  meaning strongly toward the direct-prompt ceiling (95% CI +23% to +135% of span); transplanting
  the *query codeword* moves it the **wrong way**. The meaning is retrieved from the demonstrations
  at answer time, not stored in the codeword.
- **Attention-carried, but distributed.** Cutting query→demo-block attention at **all** layers
  recovers **84%** of the effect of deleting the demonstrations; the same cut at **two** layers
  recovers **0.1%**. It is redundant across depth, which is why every localized knockout reads zero.
- **Semantics move far more than the representation.** The model's reported meaning of the codeword
  travels **59%** of the way from literal to direct (paired, n=60, monotone in demo count:
  +7.6 → +16.8), while the token's position on the concept axis moves only a few percent.

## What we cannot say yet

**G4 (is this a usable GCG objective) is unresolved.** Steering `d_surface` at L8:

| dose | ASR | note |
|---|---|---|
| baseline | 0.219 | |
| α=0.10 | 0.241 | indistinguishable from baseline |
| α=0.25 | **0.082** | refusal 7% → 70% |
| α=1.0 | (0.759) | **model degenerate** — 55% of trigrams repeated |

The α=1 arm looked like a 3.5× ASR win and is an artifact: the intervention broke generation and the
judge scored the loop as harmful. **We nearly reported it.** The usable dose window is narrow, which
itself matters for §12 — an optimizer maximizing this projection has no reason to stop at 0.25 and
will find the degenerate regime.

Sign-flip and norm-matched controls at α=0.25 are judging now. If both signs suppress ASR, the
α=0.25 effect is disturbance, not direction.

## What we'd take from this sprint

1. **The 2×2 design is the reusable artifact.** It separates surface identity from context and it
   caught the confound quantitatively. Bank: 2352 prompts, 240 matched families, 0 alignment
   violations, all target occurrences single-token in both arms.
2. **The naive direction inflates and misleads** — it roughly doubles the apparent effect and
   manufactures signal in layers where the identified direction finds none.
3. **Process:** three retractions and two magnitude corrections, all from independent audit, all one
   family — *the manipulated and measured quantities were not the same thing*, or *the best of mine
   was compared against a fixed instance of yours*. Every gate-bearing number now comes from a
   committed script, and interventions are gated on generation coherence.

## Suggested next

- Finish G4 (controls landing), then decide §12 on the sign test rather than the correlation.
- Second model (Qwen3-14B) and second concept pair — everything here is Llama-3.1-8B, carrot↔bomb.
- The distributed-retrieval result deserves a proper layer sweep: where between 2 and 32 layers does
  it appear, and is it graded or threshold?
