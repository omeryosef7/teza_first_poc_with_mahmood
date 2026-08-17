# Boombness Objective Sprint — full report

**Author:** Omer · **Date:** 2026-08-17 · **Branch:** `behavioral-causality-sprint`
**Plan:** `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` (20 sections)
**Execution log:** `docs/BOOMBNESS_SPRINT_PROGRESS.md` (phase board, gate table, 5 retractions, 5 corrections, 5 audits)
**Summary for collaborators:** `reports/boombness_objective_sprint_short_update.md` (revision 5)
**Status:** every claim below re-derived by an independent verifier; the 15 gaps it found are fixed and marked ⚠.

**Model:** `meta-llama/Llama-3.1-8B-Instruct`, bfloat16. **Concept pair:** carrot ↔ bomb.
**Bank:** 2352 prompts, 912 families (240 matched 2×2), content sha `71bea179345ed118`.
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
| **G1** (§5) | Where does the codeword's meaning live? | **In the demonstrations, not the token.** The **single-layer L18** demo transplant moves the semantic readout +84% of span, CI [+57%, +105%] (n=8 families, **2 domains**); the query-codeword transplant moves it the *wrong way*. ⚠ One arm of ~130 — the all-layer variant goes the wrong way too (−0.76). |
| **G2** (§9) | Does Boombness predict attack success? | **Yes, modestly.** ρ = +0.307 at L12, +0.302 norm-partialled, n=234, 6/6 domains positive (two essentially null), **p < 5e-4** (within-domain permutation, at its resolution floor). |
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

The naive direction **roughly doubles** the effect where both agree (1.75–2.4× at L4/L8/L12/L31).

⚠ **The mid-layer half of this claim is weaker than it looks, and both weakenings came from the final
verifier.** (a) The naive p range is **0.074–0.62**, not 0.22–0.62 — at L20 the naive direction is
*also* marginally negative. (b) More seriously, **the L16–L24 negative band does not exist in the
behavioural prompts**, the population every ASR claim lives on: split by query kind those layers read
**+0.003 / −0.004 / +0.015 (all n.s.)** for `behavioral` versus ≈−0.035 for `comprehension_usage` and
≈−0.045 for `semantic_one_word`. And `reanalyze_corrected.py`'s own `holm_rejected` field is **True
only at L4 and L31**. So the defensible claim is that the naive direction inflates ~2× where both
agree; the mid-band attenuation is a semantic/comprehension-prompt effect that does not survive
multiplicity correction.

**Bank integrity:** **912 families** total, of which 240 are the matched 2×2 set; all target
occurrences single-token in both arms; **0 alignment violations among the 216 families where the
exact-swap invariant is defined** — the other 696 are forced-choice and cannot satisfy an exact swap
by construction. (Three different denominators, so all three are stated.)

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

⚠ **Arm-selection exposure.** +84% is **one arm of ~130** in this pilot, and the result is not uniform
across windows: in the *same* context pair, `transplant|demos_only|**all**` moves the readout strongly
the **wrong way** (−0.76, CI [−1.49, −0.21]). "Transplanting the demonstrations moves the meaning
+84%" is a statement about the **single-layer L18 window**, not about demonstration transplants in
general. The direction of G1 (demonstrations, not the codeword) is robust; the magnitude is
window-specific.

### G3: the retrieval is attention-carried and massively redundant — and the redundancy is in the EDGE SET, not depth
6 families, semantic readout, `--dst both --demo-scope block`:

| arm | edges | layers | Δ readout | % of deletion ceiling |
|---|---|---|---|---|
| `no_demo_text` (delete the demos) | — | — | −11.509 | 100% (definition) |
| `all_layers_demo` | 56,832 | 32 | −9.708 | **84%**, CI [62%, 110%] |
| `all_demo` | 3,552 | 2 | −0.008 | **0.07%**, CI [−6.7%, +8.2%] |
| **`subsampled_all_layers_demo`** | **3,552** | **32** | **+0.089** | **−0.77%**, CI [−3.1%, +2.0%] |
| top-k / bottom-k / random / non-demo / same-head | 16 | 2 | ≈0 | ≈0 |

⚠ **Units and signs differ between the last two columns** — the percentages are fractions of the
deletion ceiling (which is itself negative), so a **positive** raw Δ maps to a **negative** percentage.
`subsampled_all_layers_demo`'s +0.089 log-odds is −0.77% of span, not +0.089%. The two matched arms
bound the null at roughly **±8% of the ceiling** (CIs [−3.1%,+2.0%] and [−6.7%,+8.2%]), which is worth
stating so the matched null is not read as tighter than it is.

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
does not dominate `no_demo_text`, and must **not** be read as "G3 invalid".

⚠ **The "positive control" does not behave like one, and the name should probably go.** It is
**+3.534** in `g3_dstfix`/`g3_edgematch` but **−1.135** in `g3_dynrange` — it changes **sign** between
two runs of the same design — and it recovers roughly **−31%** of the deletion span, i.e. it moves
*opposite* to the effect it is meant to bracket. Anyone opening those artifacts will also find
`dynamic_range_established: false` and `edge_count_confound.identified: false`; both are definitional
(the first compares against the deletion ceiling rather than an arm, the second predates the matched
arm being added) but neither is self-explanatory in the file. Do not cite the positive control as
validating anything until its intended direction is pinned down.

### §7: semantics move far more than the representation
The model's *reported meaning* of the codeword travels **59%** of the way from literal to direct
(paired, n=60, monotone in demo count: +7.6 → +16.8) while the token's position on the concept axis
moves a few percent. Domain-clustered t (13.5) ≈ naive t (13.3); bootstrap CI on the ratio ≈ [50%, 68%].

---

## 3. Does Boombness predict attack success? (§9) — G2

**ρ = +0.307** for `d_surface|L12|proj`, **+0.302** after partialling out the residual-stream norm,
n = 234. "100% coverage" means all 270 judged doublespeak rows had a representation row — it does not
mean nothing was dropped: 36 zero-demo prompts are excluded on principle (no demonstrations ⇒ no
codeword mapping), leaving 234.

**Inference, corrected.** The 234 prompts are 6 domains × 39 and the predictor is strongly clustered
by domain (ICC ≈ 0.45). The i.i.d. p originally reported was overstated by ~3.5 orders of magnitude:

| inference | p |
|---|---|
| i.i.d. (withdrawn) | 1.7e-06 |
| CR1 domain-clustered (G=6, few clusters — indicative) | 1.2e-03 |
| **within-domain permutation, group-demeaned — cite this** | **< 5e-4** (resolution floor: 0 of 2000 draws reached the observed value) |

Per-domain: **6 of 6 positive**, but two are essentially null (`lab_safety` +0.020, `news_report`
+0.062), so "positive in 6/6" reads more uniform than the data is.

### The between-arm story: the attack removes refusal
On the 234-prompt population:

| | refusalness (L18) | ASR | refusal rate |
|---|---|---|---|
| direct harmful request | **+7.06** | 0.050 | 95.0% |
| doublespeak | **−0.15** | **0.214** | 0.85% |
| mapping stated outright | +0.01 | 0.375 | 0% |
| benign literal | −0.30 | 0.031 | 1.85% |

To the refusal direction a doublespeak prompt looks **benign** — it sits at −0.15, next to
`benign_literal`'s −0.30 and **7.2 units below** the matched direct request. Every figure above is on
the `n_examples ≥ 1` population; an earlier draft mixed the all-rows numbers in and had the
doublespeak cell at **+0.04**, i.e. the wrong sign.

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

**This table is now regenerable.** `src/boombness/analyze_position.py` produces it from a committed
command, records the run paths, and **verifies that each of the four cells actually read where it
claims to** — the check that caught the phantom cell. It refused to run until the `@last` refusalness
cell had an artifact recording its position (job 761697), rather than accepting the source code as
evidence.

**Stated at its least favourable framing, deliberately.** The 2.0×/4.2× above uses each probe's *best*
column. On *median* columns the position effect is far larger — `d_surface` 0.0076 → 0.0847 (**11×**)
and refusalness 0.0033 → 0.1643 (**50×**) — so the localization finding is stronger than the headline
number suggests. The best-column version is quoted because it is the conservative one.

⚠ **Two things about the freedom in that table.** (a) It is matched *within* each probe across
positions but **not between probes**: `d_surface` draws its best column from 20 candidates,
refusalness from 10, and both are max-of-k statistics, so the ratios are biased **toward Boombness**.
Re-selecting the column inside each bootstrap resample gives [0.84, 2.88] and [0.38, 1.12] — same
conclusion, wider. (b) On **incremental** R² at matched footing, refusalness wins at both positions:

| | Boombness adds over refusalness | refusalness adds over Boombness |
|---|---|---|
| @ codeword_last | +0.028 | **+0.144** |
| @ last token | +0.025 | **+0.091** |

An earlier draft quoted +0.104 / +0.039 here; those came from the mixed-footing artifact and pointed
the other way.

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

⚠ **Coherence caveat on the arm carrying the only positive G4 result.** All five arms pass the gate,
but `coherence_gate` skips generations under 8 words, and the +0.25 arm — refusal rate 0.696 — had
**68 of its 270** doublespeak generations (25%) excluded on that basis, so `coherent: true` was
computed on n=202. Baseline dropped 0; the others 0–1. The gate is weakest exactly where it matters.

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

**Boombness is flat, and it is a tight null:** `role → Boombness` gives **F = 0.175, p = 0.972** at
L12, and **p = 0.60 (L8) / 0.75 (L31)** — so the null holds across all three tested layers, not just
the most favourable one. The **sd of the six style means** is 3.6% of the pooled within-style sd (the
*range* is 9.3% — "spread" should not be read as range). The design has the resolution to say so.

**The ASR half is suggestive but not established:** `role → ASR` F = 1.94, **p = 0.087** on an
unbalanced omnibus (`plain` n=204 vs 36 each); the largest pair (0.035 vs 0.233, a 6.6× ratio) is
MW p = 0.007 uncorrected ≈ **0.105 Bonferroni** over 15 comparisons. So §11's answer is **(c)-leaning** — role definitively does not change Boombness, and
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

⚠ **This table is POOLED over three query kinds, and the mid-layer band is not a behavioural-prompt
effect** (correction C7). Split out, L16/L20/L24 read **+0.003 / −0.004 / +0.015 (all n.s.)** for
`behavioral` versus ≈−0.035 for `comprehension_usage` and ≈−0.045 for `semantic_one_word`. For the
behavioural prompts — the population all ASR claims live on — the picture is simpler: **early positive
band (L8 +0.048 t=+2.1, L12 +0.036 t=+2.2), no mid-layer band, and a large L31 effect (+0.133,
t=+9.8)**. The pooled negative band also fails the artifact's own Holm correction, which rejects only
L4 and L31.

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

⚠ **"Shuffled controls at chance" is too clean a description.** Per layer they span **0.354–0.657**
(d5) and **0.350–0.716** (d6); the *means* are ≈0.52 but the scatter is ±0.2 at n=432. The lift over
shuffle is large and the conclusion holds — the description does not.

A length/position confound was suspected (A/E average 137.9 tokens vs 129.6 for B/C, tracking
context) and **refuted**: on the full cell populations `seq_len` alone gives AUROC **0.430** (d5) /
0.437 (d6) and `token_pos` **0.454** / 0.475 — chance-level, though `seq_len` is a little further from
0.5 than the "~0.47" quoted earlier, in the unhelpful direction. The per-family direction is also
inconsistent (A's codeword is later in only 42/72 families).

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

## §19 — the eleven questions, answered directly

The plan asks these to be answered directly, so they are, each with its status and its caveat.

**1. Does Natural Doublespeak create the same kind of internal `bomb` representation as Direct prompts?**
**Partly, and much less than the model's own behaviour suggests.** On the identified axis the doublespeak
codeword moves only a few percent toward the concept (C−A ≈ +0.015 to +0.027 at L4–L12), while the
model's *reported meaning* of that codeword travels **59%** of the way from literal to direct. So the
semantics move far more than the representation. It is not the same representation, and the gap between
"what the model says the word means" and "where the token sits on the axis" is the sprint's most robust
qualitative finding.

**2. Does the final `carrot` become more `bomb`-like than earlier `carrot`s?**
**NO — it becomes LESS so, and the effect is positional rather than semantic.** Within-prompt paired
(same prompt, same word, only position differs), domain-clustered, n=246 doublespeak prompts:
Δ(final − earlier) is **negative at every layer** (L16 **−0.154**, t_cl = −10.5, p = 0.0001; L8 −0.082,
p = 0.0016; L31 −0.080, p = 0.014). **The control is what settles the interpretation:** the same
comparison in `benign_literal` — where there is no bomb meaning at all — gives effects of the **same
sign and comparable size** (L16 −0.105, L31 −0.131, all p < 0.004). So the last occurrence of a word
simply sits differently on the axis than earlier occurrences, regardless of meaning. There is no
consistent doublespeak-specific excess. ⛔ The earlier "later-carrot-more-bomb-like" claim (P4.3) stays
retracted; this is its replacement, computed with the control it lacked.

**3. How many examples are needed before Boombness rises?**
**One, for the output layer; eight to sixteen for the middle.** L31 is **flat** across a 16× dose change
(+0.0485 → +0.0499, t = +5.9…+10.2) — one demonstration achieves the whole output-layer effect. L4–L12
grow strictly monotonically (L8 +0.0138 → +0.0449, 3.3×). The mid-layer bands keep scaling to k=8 and
then saturate. ⚠ Pooled over query kinds; see C7.

**4. Does Boombness vary enough across prompts to support optimization?**
**It varies, but the usable dose window is narrow enough to be a problem.** Within-arm sd is non-trivial
and the correlation with ASR is real. But steering at α=1 destroys generation (55% trigram repeats,
100% truncated) and the judge scores the degenerate loop as harmful — an artifact we nearly reported. An
optimizer maximizing this projection has no reason to stop at 0.25.

**5. Does Boombness predict ASR?**
**Yes, modestly.** ρ = **+0.307** (`d_surface|L12|proj`), **+0.302** norm-partialled, n = 234, 6/6
domains positive though two are essentially null, **p < 5e-4** (within-domain permutation; the i.i.d.
1.7e-06 is withdrawn as pseudo-replication).

**6. Does Boombness predict ASR better than refusalness?**
**No.** ⛔ The 3.7× is retracted — it compared the two probes at *different tokens*. At matched footing
neither dominates: ratio **1.54** [0.64, 3.60] @last and **0.75** [0.33, 1.13] @codeword_last, both CIs
straddling 1. ⚠ And the between-probe selection freedom is not matched (20 vs 10 candidate columns),
which biases those ratios toward Boombness.

**7. Does Boombness add predictive power beyond refusalness?**
**A little, and less than refusalness adds beyond it.** At matched footing Boombness adds **+0.028**
(@codeword) and **+0.025** (@last) in R²; refusalness adds **+0.144** and **+0.091** the other way. An
earlier draft had this backwards from a mixed-footing artifact.

**8. Do user-like / CoT-like framings increase Boombness?**
**No — and this is a tight null, not an underpowered one.** Across six role styles with content, domain,
demo count and query held fixed: `role → Boombness` **F = 0.175, p = 0.972** at L12 (and p = 0.60/0.75
at L8/L31), with the sd of style means at **3.6%** of the within-style sd. Whether role framing changes
*ASR* is unresolved (F = 1.94, p = 0.087; largest pair p ≈ 0.105 Bonferroni). `role_style` is a
categorical proxy — no Userness/CoTness probe was fitted.

**9. Can we surgically remove Boombness without destroying comprehension?**
**No — it is massively redundant, so there is nothing "surgical" to remove.** Cutting **6.25%** of
demo→query edges does nothing *however distributed across depth*; cutting 100% recovers 84% of the
deletion ceiling. Every localized knockout (top-k, bottom-k, random, same-head — 16 edges, ~0.03%) reads
zero. ⚠ The converse test is impossible by construction: a layer holds only ~3,648 edges, so any cut
above ~7.3k must span layers.

**10. Can we turn Boombness into a useful GCG objective?**
**No, and §12 was therefore not built.** Both signs of `d_surface` suppress ASR, so ASR does not follow
the axis. Only **+0.25** clears a 4-draw random-control band (p = 0.0014) and it does so by **triggering
refusal** (90.1% of its suppressed prompts); **−0.25** is indistinguishable from a random perturbation
(p = 0.070). Adding concept-ness triggers refusal; removing it just damages the model.

**11. What exactly should Matan/Mahmood take from this sprint?**
Four things, in order of durability:
1. **The 2×2 identification design** — it separates surface identity from context and quantifies the
   confound (~2× inflation) instead of arguing about it. Reusable for any codeword/concept pair.
2. **The localization result** — the ASR-predictive state sits at the **codeword token**, 2–4× more than
   at the final prompt token (11–50× on median columns), for a concept probe *and* a refusal probe. This
   is the finding worth following.
3. **A documented negative on the objective**, with the specific reason: correlation without
   sign-following intervention. Do not build on this axis; target the demonstration-retrieval pathway.
4. **The failure catalogue** — five retractions, three guards that never executed, and four transferable
   rules: test guards against cases they should fail; address things by identity not by
   filename/tag/mtime/line-number; resampling *rows* cannot rescue a comparison whose arms sit in
   different *places*; and when correcting an error verify the *measured thing* changed, not just the
   knob you turned.

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
