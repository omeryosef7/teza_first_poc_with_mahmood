# Boombness Objective Sprint — full report

**Author:** Omer · **Date:** 2026-08-17 · **Branch:** `behavioral-causality-sprint`
**Plan:** `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` (20 sections)
**Execution log:** `docs/BOOMBNESS_SPRINT_PROGRESS.md` (phase board, gate table, 5 retractions, 5 corrections, 5 audits)
**Summary for collaborators:** `reports/boombness_objective_sprint_short_update.md` (revision 4)

**Model:** `meta-llama/Llama-3.1-8B-Instruct`, bfloat16. **Concept pair:** carrot ↔ bomb.
**Bank:** 2352 prompts, 240 matched 2×2 families, content sha `71bea179345ed118`.
**Judge:** StrongReject rubric via `gpt-4o-mini`, threshold 0.5, continuous score always persisted.

---

## 0. What the sprint set out to do, and what it found

The plan proposed building a GCG attack objective out of "Boombness" — the degree to which a
codeword token's representation sits on a concept axis — on the hypothesis that doublespeak
jailbreaks work by smuggling concept content into a benign-looking token.

**The answer is no, and the sprint's value is in *why* not.** Four gates were pre-registered. The
first three produced positive mechanistic findings. The fourth — the one the objective actually
requires — returned a directional null, and the plan made §12 explicitly conditional on it.

| gate | question | verdict |
|---|---|---|
| **G1** (§5) | Where does the codeword's meaning live? | **In the demonstrations, not the token.** Transplanting demo states moves the semantic readout +84% of span, CI [+57%, +105%]; transplanting the query codeword moves it the *wrong way*. |
| **G2** (§9) | Does Boombness predict attack success? | **Yes, modestly.** ρ = +0.307 at L12, +0.302 norm-partialled, n=234, 6/6 domains positive (two near-null), **p = 5.0e-04** (within-domain permutation). |
| **G3** (§10) | Can it be removed surgically? | **No — it is massively redundant.** Cutting 6.25% of demo→query edges does nothing *however distributed*; cutting 100% recovers 84% of the deletion ceiling. |
| **G4** (§12) | Is it a usable objective? | **No.** Both signs of `d_surface` suppress ASR, so ASR does not follow the axis. Only `+0.25` exceeds a 4-draw random-control band, and it does so by **triggering refusal**. |
| **FINAL** (§18) | outcome label | **B — mechanistic but not causal.** |

**§12 was therefore not built.** That is a decision forced by data, recorded as a documented
negative rather than left as an unfinished row.

---

## 1. The methodological contribution: the 2×2 identification design (§3–§4)

**This is the most reusable thing here.** The existing benchmark compares a harm-domain arm against
a benign arm that is *a different story*, so the natural direction
`mean(h_bomb) − mean(h_carrot_benign)` is `bombness + explosive-context-ness` — two effects that
cannot be separated by that contrast.

Replaced with a 2×2 over **surface word × demonstration valence**, plus two off-cells:

| cell | condition | surface | context |
|---|---|---|---|
| A | `benign_literal` | carrot | benign |
| B | `direct_harmful` | bomb | harmful |
| C | `natural_doublespeak` | carrot | harmful |
| E | `concept_in_benign_ctx` | bomb | benign |
| D | `direct_codeword` | — | mapping stated outright |
| F | `benign_remap` | — | bicycle remap (surface-change control) |

```
d_surface = ½[(B−C) + (E−A)]     surface-word effect, context matched   ← "Boombness"
d_context = ½[(C−A) + (B−E)]     what the naive direction mostly measures
d_inter   = (B−C) − (E−A)        interaction
d_naive   = B−A = d_surface + d_context
```

**Quantified effect of the confound** (C−A contrast on each direction, cluster-robust p over 6 domains):

| L | 4 | 8 | 12 | 16 | 20 | 24 | 31 |
|---|---|---|---|---|---|---|---|
| `d_surface` | +0.023 | +0.027 | +0.015 | **−0.023** | **−0.029** | **−0.021** | +0.047 |
| p_clustered | 0.002 | 0.022 | 0.043 | **0.028** | **0.009** | 0.053 | 0.000 |
| `d_naive` | +0.043 | +0.048 | +0.037 | −0.006 | −0.016 | −0.005 | +0.094 |
| p_clustered | 0.000 | 0.003 | 0.001 | 0.437 | 0.074 | 0.623 | 0.000 |

The naive direction **roughly doubles** the effect where both agree (1.75–2.4× at L4/L8/L12/L31),
and at **L16–L24 it washes out a real negative displacement** that the identified direction detects.
Both rows come from the committed `reanalyze_corrected.py`.

**Bank integrity:** 240 matched families, all target occurrences single-token in both arms,
**0 alignment violations among the 216 families where the exact-swap invariant is defined** (696
forced-choice families cannot satisfy it by construction — the numerator is meaningless without that
denominator).

---

## 2. Where the meaning lives (§5, §7, §10) — G1 and G3

### G1: retrieved from the demonstrations at answer time, not stored in the codeword
Activation transplant on matched fixed pairs, semantic log-odds readout, n=8 families:

| arm | Δ readout | % of baseline→ceiling span | paired-bootstrap CI |
|---|---|---|---|
| transplant demonstrations (L18) | — | **+84%** | **[+57%, +105%]** |
| transplant demonstrations (L8) | — | +71% | [+54%, +88%] |
| transplant query codeword | — | moves the **wrong way** | — |

**Caveats that travel with this:** n=8 families drawn from only **2 domains**, so the effective number
of independent units is nearer 2 than 8. The interval is a paired bootstrap over families; the
delta-method interval originally reported was *too wide* because it propagated the span as if
baseline and ceiling were independent when they correlate +0.63 within family. An earlier quoted
interval of "+23% to +135%" was a **chimera** (one arm's lower bound welded to another's) and is
withdrawn.

### G3: the retrieval is attention-carried and massively redundant — and the redundancy is in the EDGE SET, not depth
6 families, semantic readout, `--dst both --demo-scope block`:

| arm | edges | layers | Δ readout | % of deletion ceiling |
|---|---|---|---|---|
| `no_demo_text` (delete the demos) | — | — | −11.509 | 100% (definition) |
| `all_layers_demo` | 56,832 | 32 | −9.708 | **84%**, CI [62%, 110%] |
| `all_demo` | 3,552 | 2 | −0.008 | **0.07%**, CI [−6.7%, +8.2%] |
| **`subsampled_all_layers_demo`** | **3,552** | **32** | **+0.089** | ≈0 |
| top-k / bottom-k / random / non-demo / same-head | 16 | 2 | ≈0 | ≈0 |

**The matched arm is the decisive one and it corrected my own claim.** I first read the 84%-vs-0.07%
contrast as *depth* distribution. But the 32-layer arm also cuts **16× more edges**, so the
comparison moved two things at once. At an identical 3,552 edges, spreading over 32 layers instead of
2 changes the readout by **+0.10 log-odds — nothing.** **Layer spread is not the operative variable.**

What is true: removing **6.25%** of demo edges does nothing *however distributed*; removing 100%
recovers 84%. That is why every localized knockout — top-k, bottom-k, random, same-head — reads zero:
each removes ~0.03% of a hugely redundant set.

**Identification limit, stated rather than hidden:** the converse arm is *impossible*. At seq_len 114
× 32 heads a layer holds only ~3,648 edges, so any cut above ~7.3k **must** span layers. Edge count
and layer spread cannot be decoupled upward. `dense_two_layer` attempted it and saturated at 7,264 of
56,832 — the code now raises rather than silently under-delivering.

**Movability, restated:** the dynamic-range guard now compares on magnitude against a whitelist of
true null controls (largest 0.078). `readout_movable = True` via `no_demo_text` (−11.5), so nulls here
are interpretable. The separate `dynamic_range_established=False` reflects that the positive control
(+3.53) does not dominate `no_demo_text`, and must **not** be read as "G3 invalid".

### §7: semantics move far more than the representation
The model's *reported meaning* of the codeword travels **59%** of the way from literal to direct
(paired, n=60, monotone in demo count: +7.6 → +16.8) while the token's position on the concept axis
moves a few percent. Domain-clustered t (13.5) ≈ naive t (13.3); bootstrap CI on the ratio ≈ [50%, 68%].

---

## 3. Does Boombness predict attack success? (§9) — G2

**ρ = +0.307** for `d_surface|L12|proj`, **+0.302** after partialling out the residual-stream norm,
n = 234 (`n_examples ≥ 1`), 100% prompt coverage.

**Inference, corrected.** The 234 prompts are 6 domains × 39 and the predictor is strongly clustered
by domain (ICC ≈ 0.45). The i.i.d. p originally reported was overstated by ~3.5 orders of magnitude:

| inference | p |
|---|---|
| i.i.d. (withdrawn) | 1.7e-06 |
| CR1 domain-clustered (G=6, few clusters — indicative) | 1.2e-03 |
| **within-domain permutation, group-demeaned — cite this** | **5.0e-04** |

Per-domain: **6 of 6 positive**, but two are essentially null (`lab_safety` +0.020, `news_report`
+0.062), so "positive in 6/6" reads more uniform than the data is.

### The between-arm story: the attack removes refusal
On the 234-prompt population:

| | refusalness (L18) | ASR | refusal rate |
|---|---|---|---|
| direct harmful request | **+7.30** | 0.042 | 96% |
| doublespeak | **+0.04** | **0.219** | 0.9% |
| mapping stated outright | +0.10 | 0.375 | 0% |

To the refusal direction a doublespeak prompt looks **benign** while the matched direct request sits
at +7.30. (Both figures are on the `n_examples ≥ 1` population; quoting 0.583/7.4% mixes in 36
zero-demo rows that are all ASR=1.0 and carried the entire gap.)

### ⛔ The "Boombness beats refusalness 3.7×" claim is retracted
It compared `d_surface`@`codeword_last` against refusalness@last-token — different tokens. Rebuilt as
a freedom-matched 2×2 (columns available at **both** positions: 20 for `d_surface`, 10 for refusalness):

| single-predictor R² | @ last token | @ codeword_last | position effect |
|---|---|---|---|
| `d_surface` | 0.070 | 0.141 | **2.0×** |
| refusalness | 0.046 | 0.189 | **4.2×** |
| **ratio B/R** | **1.54** [0.64, 3.60] | **0.75** [0.33, 1.13] | |

**Neither probe dominates** — which wins depends on where you read, and both domain-clustered CIs
straddle 1.0. The 3.7× was the most favourable of four possible cross-position pairings.

**What replaces it is a position finding:** both probes are 2–4× more predictive of ASR at the
**codeword token** than at the final prompt token — a larger factor than any difference between the
probes. The attack-relevant state is **localized at the codeword**, consistent with G1 and G3.

**Construct-validity caveat:** the refusal direction was fitted for a last-token readout. At the
codeword position it no longer orders conditions like a refusal probe (`direct_harmful` becomes
indistinguishable from doublespeak, and `benign_literal` reads as *least* refusing). The predictor
comparison is fair — both probes treated identically — but "refusalness at the codeword token" is
**not** a validated refusal measurement, which is why outcome C is not claimed.

---

## 4. Steering (§12) — G4, and why the objective was not built

L8, gap-unit dosing (α=1 = one diff-of-means), common 270-prompt set, all arms coherence-gated:

| arm | ASR | 95% CI | refusal | paired Δscore |
|---|---|---|---|---|
| baseline | 0.219 | [0.173, 0.272] | 0.074 | — |
| **+0.25** | 0.081 | [0.054, 0.120] | **0.696** | **−0.1144 ± 0.0235** |
| **−0.25** | 0.148 | [0.111, 0.195] | 0.067 | **−0.0741 ± 0.0198** |
| random ×4 (band) | — | — | 0.085 | **−0.0366**, between-draw sd 0.0049 |
| orthogonal | 0.189 | [0.147, 0.240] | 0.093 | −0.0306 ± 0.0179 |

**Both signs suppress ASR**, so mean ASR does not follow the sign of the axis. The falsifying branch
was written into the analysis code before the numbers existed, and it fired. **No directional causal
support ⇒ no objective.**

Against a proper 4-draw random-control band (Welch df, not the SE of the band mean):

| arm | diff vs band | t | df | p | verdict |
|---|---|---|---|---|---|
| **+0.25** | −0.0778 ± 0.0241 | −3.23 | 235 | **0.0014** | **clears the band** |
| −0.25 | −0.0375 ± 0.0206 | −1.82 | 203 | 0.070 | does **not** clear |

**The two signs suppress by different routes** — of the prompts each arm suppressed, the fraction
that are keyword refusals:

| +0.25 | −0.25 | random | orthogonal |
|---|---|---|---|
| **0.901** | **0.000** | 0.000 | 0.042 |

So: **adding concept-ness to the codeword triggers refusal; removing it just damages the model like
any other perturbation of that size.** "Pure disturbance" is too strong, and so is "axis-magnitude
effect at both signs" — only the positive sign exceeds a norm-matched perturbation.

**A near-miss worth recording:** an arm at α=1 showed ASR 0.219 → 0.759 and was an **artifact** — the
intervention broke generation (55% of trigrams repeated, 100% truncated) and the judge scored the
degenerate loop as harmful. It was caught by the coherence gate only after being written down. **The
usable dose window is narrow**, which is itself an argument against the objective: an optimizer
maximizing this projection has no reason to stop at 0.25 and will find the degenerate regime.

---

## 5. Role framing (§11)

Six role styles with demonstration content, domain, demo count and final query held **fixed**
(the content-constancy design, following the Role-Confusion codebase's `render_single_message`):

| style | Boombness L12 | ASR (n=36 each) |
|---|---|---|
| system_like_quoted | −0.2807 | **0.035** |
| assistant_like | −0.2876 | 0.160 |
| tool | −0.2858 | 0.163 |
| cot_like | −0.2820 | 0.177 |
| plain | −0.2909 | 0.195 |
| user_like | −0.2888 | **0.233** |

**Boombness is flat, and it is a tight null:** `role → Boombness(L12)` **F = 0.175, p = 0.972**, with
the style-mean spread at **3.6%** of the within-style sd. The design has the resolution to say so.

**The ASR half is not established:** `role → ASR` F = 1.94, **p = 0.087**; the largest pair
(0.035 vs 0.233, a 6.6× ratio) is MW p = 0.007 uncorrected ≈ **0.105 Bonferroni** over 15
comparisons. So §11's answer is **(c)-leaning** — role definitively does not change Boombness, and
whether it changes ASR is unresolved at this n. (I predicted (b) before the powered run; the data
did not support it.)

`role_style` is a **categorical proxy**: no Userness/CoTness probe was fitted on this model, so this
is not a measured role signal.

---

## 6. Demonstration-count dose-response (§8)

C−A contrast on `d_surface|L|cos`, surface held constant at `carrot`, cluster-robust t, n=36/cell:

| band | behaviour |
|---|---|
| **L4–L12** | positive, **strictly monotone** in demo count (4/4 steps); L8 grows **+0.0138 → +0.0449 (3.3×)** from k=1 to k=16 |
| **L16–L24** | **negative**, magnitude dose-dependent, **saturating at k=8** (L20 −0.051, easing to −0.042 at k=16) |
| **L31** | **FLAT** across a 16× dose change (+0.0485/+0.0457/+0.0485/+0.0438/+0.0499; t = +5.9…+10.2) |

**One demonstration achieves the entire output-layer effect**; fifteen more add nothing, while the
mid-layer effects keep scaling to k=8–16. So the quantity reaching the output is **not** a simple
readout of the quantity accumulating mid-stack — independently consistent with G4's directional null.

This also gives the retracted "two humps" observation a proper account: two bands of **opposite
sign** responding differently to dose. The mid band is not null; it is negative *and* dose-dependent.

**Scale caveat:** these are cosines in the 0.01–0.05 range. The sign structure and the dose response
are the findings; the magnitudes are small.

---

## 7. Probes (§6)

**⚠ The original four regimes are uninformative by construction.** All shared one label —
`cell ∈ {B,E}` = "the target token IS the concept", i.e. **the surface word**. `bomb` and `carrot`
are trivially separable, so every regime returns **AUROC = 1.000 at every layer**, shuffled controls
near chance. `d3_hard_negative` is affected too: its C-vs-E test set is also carrot-vs-bomb. **These
1.000s must never be quoted as "Boombness is linearly decodable."**

**New surface-matched regimes**, holding the word constant and varying the meaning:

| layer | d5 (A vs C, both "carrot") | shuffled | d6 (B vs E, both "bomb") | shuffled |
|---|---|---|---|---|
| 0 | 0.960 | 0.561 | 0.974 | 0.376 |
| 12 | 0.982 | 0.571 | 0.985 | 0.408 |
| 31 | 0.983 | 0.657 | 0.979 | 0.594 |

A length/position confound was suspected (A/E average 137.9 tokens vs 129.6 for B/C, tracking
context) and **refuted**: `seq_len` alone gives AUROC 0.472 and `token_pos` alone 0.473, and the
per-family direction is inconsistent (42/72).

**What they establish:** with surface held constant, the codeword token carries strong information
about which context preceded it — a probe-side confirmation of G1's retrieval story.
**What they do not:** that the retrieved content is specifically *bombness*. A and C differ in
demonstration text, so separating them shows context is encoded there, not what it encodes. That is a
projection question, which is why the conclusions rest on the 2×2 projections.

---

## 8. Process — five retractions, five corrections, three dead guards

Every retraction came from independent audit, and they share **one** root cause in two forms:
*the manipulated and the measured quantity were not the same thing*, or *the best of mine was
compared against a fixed instance of yours*.

| # | retracted claim | why |
|---|---|---|
| R1 | tick-7 headline incl. a "null carry band" | pseudo-replication; the band is significantly negative, not null |
| R2 | G2's original negative verdict | predictor read off the *wrong prompt* (semantic, not behavioural) |
| R3 | a §10 null | edges cut into the wrong destination token |
| R4 | "`d_naive` manufactures signal where `d_surface` finds none" | sourced to an already-retracted section; corrected data **reverse** it |
| R5 | "Boombness beats refusalness 3.7×" | the two probes were read at **different tokens** |

Corrections: C1 (L8 norm contamination → L12), C2 (40× → 3.7×, then retracted entirely), C3 ("2–3× the
controls" is sign-dependent), C4 (clustered p, 1.7e-06 → 5.0e-04), C5/C6 (wrong column for the
per-domain count; population mismatch between headline table and headline correlation).

**Three guards were found to have never executed:**
1. the **coherence gate** — keyed on a `score_behavior` dirname while arms were named from judge tags, so every lookup missed and `None` passed as "checked";
2. the **dynamic-range check** — `max` over *signed* deltas returned a null control (+0.031) as "the largest effect" and certified itself;
3. the **control band** — selected `ctrl_rand_s*` while the runs were tagged `ctrlband_s*`; **zero** arms ever matched.

Plus a fourth in my own notes: a phase-board edit addressed rows by **line index**, destroying two
rows and duplicating two others (recovered from git).

**The transferable lessons**, each learned by being wrong:
- **A guard that is never tested against a case it should fail is not a guard.** Every guard now ships with such a test.
- **Address things by identity, not by an incidental property.** All four failures above matched on a filename, a tag prefix, an mtime, or a line number.
- **A robustness check that resamples *rows* cannot rescue a comparison whose arms sit in different *places*.** The 3.7× survived nested CV and leave-one-domain-out, and was still an artifact.
- **When correcting an error, verify the measured thing changed — not just the knob you turned.** The first attempt at the position fix moved the direction-fitting position and left the readout where it was, producing a phantom cell that briefly flipped the sprint's conclusion.
- **A summary that does not know what it skipped will be believed.** A driver reported "complete" having judged 2 of 4 arms.

---

## 9. What we would take forward

1. **The 2×2 design is the reusable artifact** — it separates surface identity from context, and it caught the confound quantitatively rather than rhetorically.
2. **Do not build the GCG objective on this axis.** G4 is a directional null on two independent lines (the sign test, and the refusal-route split). If an objective is wanted, target the **demonstration-retrieval pathway** G1/G3 localized, not the codeword's position on `d_surface`.
3. **The localization result is the finding worth following** — the ASR-predictive state sits at the codeword token, ~2–4× more than at the final prompt token, for both a concept probe and a refusal probe.
4. **Re-measure refusalness properly at the codeword position** before any A-vs-C claim: a direction fitted for the last token does not validate there.
5. **Second model and second concept pair.** Everything here is Llama-3.1-8B, carrot↔bomb, one judge.
6. **G1/G3 are on `semantic_one_word` prompts while G2/G4's ASR claims are on `behavioral` ones.** Each is internally consistent; joining them into one causal story is the same manipulated-≠-measured pattern one level up. A behavioural-prompt knockout would close it.

---

## Appendix — committed artifacts

| file | contents |
|---|---|
| `outputs/boombness/position_2x2.json` | freedom-matched predictor × position table |
| `outputs/boombness/g2_analysis*.json` | G2 + clustered inference + per-domain + mediation |
| `outputs/boombness/g1_g3_analysis.json` | G1 spans, paired-bootstrap CIs, n_domains |
| `outputs/boombness/g3_dstfix.json`, `g3_edgematch.json` | G3 arms incl. the edge-matched pair |
| `outputs/boombness/steering_analysis.json` | G4 arms, paired contrasts, control band, routes |
| `outputs/boombness/role_analysis.json` | §11 by role style |
| `outputs/boombness/reanalyze_d_{surface,naive}_cos.json` | §4 confound + §8 dose-response |
| `outputs/boombness/coherence_steering.json` | coherence records incl. the retracted α=1 arm |

Every gate-bearing number is produced by a committed script under `src/boombness/`; run dirs record
model, revision, dtype, attention implementation, git commit, and (since 2026-08-17) the prompt
bank's **content hash**.
