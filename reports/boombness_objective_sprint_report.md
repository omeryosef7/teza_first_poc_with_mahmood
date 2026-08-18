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
| **G2** (§9) | Does Boombness predict attack success? | **In Llama-3.1-8B only — does NOT replicate on Qwen3-14B** (there the pooled ρ is +0.364 but collapses to +0.015 when one of six domains is dropped; 3/6 domains positive; clustered p=0.206). In Llama: **modestly.** ρ = +0.307 at L12, +0.302 norm-partialled, n=234, 6/6 domains positive (two essentially null), **p < 5e-4** (within-domain permutation, at its resolution floor). |
| **G3** (§10) | Can it be removed surgically? | **No — it is massively redundant.** Cutting 6.25% of demo→query edges does nothing *however distributed*; cutting 100% recovers 84% of the deletion ceiling. |
| **G4** (§12) | Is it a usable objective? | **No.** Both signs of `d_surface` suppress ASR, so ASR does not follow the axis. Only `+0.25` exceeds a 4-draw random-control band, and it does so by **triggering refusal**. |
| **§0.3 / §10.4-B** | Does surgical REMOVAL reduce ASR without destroying comprehension? | **NO — removal RAISES ASR** (0.219 → 0.300; vs norm-matched controls +0.104/+0.109, clustered p=0.020/0.025; vs baseline alone p=0.117). Comprehension preserved (p=0.68), refusal unchanged, coherence OK. **The sign is opposite to the hypothesis.** |
| **FINAL** (§18) | outcome label | **B — mechanistic but not causal** for the *additive* axis; but see §0.3 above — the *projection* arm gives a directional effect against controls, so this label is under active revision. |

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
only at L1, L4 and L31** — none of them in the mid-band. (Corrected 2026-08-18: the file previously
corrected over the 10 *displayed* layers while its docstring claimed 32. The honest family is every
layer with a `d_surface|L*|cos` column in `results.jsonl`, all 32, each actually tested and entered
into the step-down; that rule *adds* L1 and leaves L4 and L31 rejected. The external critique
predicted L4 would stop being rejected at m=32 — that holds only if the 10 displayed p-values are
ranked against `alpha/(32-i)` without testing the other 22, which is not Holm. Sensitivity table and
all three rejection sets are in `outputs/boombness/reanalyze_corrected_d_surface_cos.json`
under `holm_rejected_by_family`.) So the defensible claim is that the naive direction inflates ~2× where both
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

## 2b. Token-level Boombness, kept separate from prompt-level (§7)

The plan insists these not be merged, and the reason turns out to be load-bearing: the token-level
result **inverts** the intuition the prompt-level one invites.

### Does the final codeword occurrence become more concept-like than earlier ones? **No — less.**
Within-prompt paired contrast: same prompt, same surface word, only the occurrence position differs.
Domain-clustered over 6 domains, n=246 doublespeak behavioural prompts with ≥2 occurrences:

| L | 4 | 8 | 12 | 16 | 20 | 24 | 31 |
|---|---|---|---|---|---|---|---|
| Δ(final − earlier) | −0.025 | −0.082 | −0.090 | **−0.154** | −0.123 | −0.119 | −0.080 |
| t_clustered | −5.0 | −6.2 | −7.1 | **−10.5** | −8.3 | −6.3 | −3.7 |
| p_clustered | 0.004 | 0.002 | 0.001 | **0.0001** | 0.0004 | 0.001 | 0.014 |

### And the control is what makes it interpretable
The identical comparison in `benign_literal` — where there is **no** concept meaning at all — gives the
**same sign and comparable magnitude** (n=162: L16 −0.105, L31 −0.131, all p < 0.004). At some layers
doublespeak is more negative, at others benign is; there is **no consistent doublespeak-specific
excess**.

**So this is a POSITION effect, not a semantic one:** the last occurrence of a word sits differently on
the axis than earlier occurrences regardless of what it means. ⛔ The earlier
"later-carrot-is-more-bomb-like" claim is retracted, and this is its replacement — computed with the
control the retracted version lacked. That claim read a within-prompt gradient as accumulating concept
content without asking whether a prompt containing no concept content shows the same gradient. It does.

**Why keeping the levels separate mattered.** Prompt-level Boombness *rises* with demonstrations
(L8 +0.0138 → +0.0449 over k=1→16) and correlates with ASR. Token-level, the final occurrence is
*lower* than earlier ones. Merged, those two would have been reported as one incoherent trend or —
worse — the prompt-level rise would have been narrated as "the codeword accumulates bombness as the
prompt proceeds", which the token-level data directly contradicts.

This is the third independent place position beat meaning on this axis: the predictor×position 2×2
(2–4×), the surface-matched probes (context decodable at the codeword from block 0), and now the
within-prompt occurrence comparison.

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
| random ×4 (band) | — | — | 0.085 | ⛔ **−0.0366 / sd 0.0049 RETRACTED (#7)** — those four "draws" were byte-identical. Genuine 4-draw band: **−0.0120, between-draw sd 0.0301** |
| orthogonal | 0.189 | [0.147, 0.240] | 0.093 | −0.0306 ± 0.0179 |

**Both signs suppress ASR**, so mean ASR does not follow the sign of the axis. The falsifying branch
was written into the analysis code before the numbers existed, and it fired. **No directional causal
support ⇒ no objective.**

Against a proper 4-draw random-control band (Welch df, not the SE of the band mean):


⛔ **The table that stood here quoted t/p computed from the RETRACTED band** (p=0.0014 on
df=235). Those are downstream of retraction #7 and were withdrawn with it — the sweep missed them
because I had enumerated the band's mean and sd but not the statistics derived FROM it. Against
the GENUINE 4-draw band (n_draws=4, so the Welch df is ~7, not ~235):

| arm | diff vs band | t | df | p | verdict |
|---|---|---|---|---|---|
| **+0.25** | -0.1023 ± 0.0410 | -2.49 | 6.6 | **0.043** | clears the band |
| −0.25 | -0.0620 ± 0.0391 | -1.59 | 5.4 | **0.168** | does **not** clear |

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

## 4b. The §2.6 comprehension control, and what it does to every intervention claim (added 2026-08-17)

The plan's §2.6 forbids reading a lowered ASR as causal without checking the model still understands the
prompt. **That control was missing for the whole sprint** until an independent plan-coverage sweep found
it. It now exists, and it reorders the intervention arms.

Readout: `comprehension_logodds` = log p("coded") − log p("literal") on `comprehension_usage` rows;
positive means the model still reports the codeword as meaning the coded thing. 60 doublespeak prompts
with ≥1 demonstration, common to all arms, domain-clustered over 6 domains:

| arm | Δ comprehension | p | frac still "coded" | verdict |
|---|---|---|---|---|
| `d_surface` **+0.25** | +0.643 | 0.006 | 0.733 | improves |
| **random +0.25** | **+1.065** | 0.001 | 0.800 | improves MORE |
| `d_surface` **−0.25** | **−0.792** | 0.040 | **0.500** | **degrades below zero** |
| **random −0.25** | **−1.470** | 0.004 | **0.383** | degrades MORE |
| **`project_out`** | **+0.088** | **0.681** | 0.683 | **unchanged** |
| arm C (remove refusalness) | +0.207 | 0.001 | 0.717 | improves |
| arm F (add Boombness + remove refusalness) | +0.863 | 0.002 | 0.783 | improves |

**Three consequences, one of them a retraction of my own claim.**

1. **The −0.25 arm is disqualified.** Its ASR suppression (0.219 → 0.148) coincides with comprehension
   falling *below zero* — the model now prefers the literal reading — so that suppression is at least
   partly confusion. It must not be described as "removing concept-ness reduces attack success".
2. **The +0.25 arm is exonerated** in the narrow sense that matters: comprehension did **not** degrade, so
   its ASR drop is not confusion. Combined with refusal rising 0.074 → 0.696, the reading "it triggers
   refusal" stands.
3. ⛔ **But the pattern is NOT axis-specific, which retracts a gloss I added (C10).** The effect is driven
   by the **sign of the dose**: positive steps raise p(coded), negative steps lower it, for `d_surface`
   *and* for a norm-matched random direction — and **random moves comprehension further in both
   directions**. I had claimed "only the negative `d_surface` step degrades comprehension, and no control
   does"; that was untested (no negative random control existed) and is false. Comprehension therefore
   does **not** discriminate `d_surface` from a generic perturbation.

**What survives as genuinely distinctive: `project_out` is the only one of five arms that leaves
comprehension unchanged** while all four additive arms move it by 0.6–1.5. That is what makes it the
surgical condition, and it is why its ASR result (§0.3, above) is the sprint's cleanest causal test.

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

⛔ **RETRACTED (retraction #6) — the "tight null" was an ERROR TERM mistake and the corrected answer is
the opposite.** The arithmetic reproduced exactly (F=0.175, p=0.972 at L12), but the design is perfectly
crossed — 72 complete 6-style stems — and the correct **paired within-stem** test gives
**F(5,355)=20.30, p=8.1e-18** (permutation p<5e-5), with **11 of 15 pairwise style differences surviving
Bonferroni**. Blocking on `query_kind` alone already breaks the null (p=0.016).
The "3.6% of within-style sd" was a **variance-decomposition error** — that denominator (0.110) is almost
entirely *between-stem* variance, which the paired design removes; against the correct within-stem residual
(0.0082) the spread is **53%**. And in the 816-row pool `plain` and the five role styles occupy **disjoint
`bank_block`s with zero family overlap**, so "content, domain, demo count and query held fixed" was **false
for the analysis actually run** — true only inside the 72 stems.
**Corrected: role framing DOES move Boombness — reliably but by a small amount** (largest pairwise gap
0.0116 = **4.1% of the grand mean** at L12). A small, highly reliable effect, not a null.

**The ASR half is suggestive but not established:** `role → ASR` F = 1.94, **p = 0.087** on an
unbalanced omnibus (`plain` n=204 vs 36 each); the largest pair (0.035 vs 0.233, a 6.6× ratio) is
MW p = 0.007 uncorrected ≈ **0.105 Bonferroni** over 15 comparisons.

So §11's answer is: **role DOES move Boombness — reliably, and by ~4% of the grand mean — while whether
it moves ASR is unresolved at this n.** (I predicted (b) before the powered run; the representational
half is supported, the behavioural half is not yet.)

⛔ This sentence previously read "role definitively does not change Boombness", **four lines below the
paragraph retracting exactly that claim** (retraction #6). Caught 2026-08-18 by an independent audit, not
by my own retraction sweep — the sweep scopes to a paragraph and this paragraph contains the word
"corrected", which its marker regex reads as retraction context. A marker word in the block is now known
to be an unreliable exemption; the sweep's own limitation is recorded in `retraction_sweep.py`.

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

## 7b. Which Boombness metric? The three-way comparison (plan §6.4 / §15 item 7) — added 2026-08-18

**This section was missing.** Plan §15 requires it as report item 7, §6.4 was run and closed, and
grepping this report for "metric comparison", "probe_boombness", "direction_boombness" or
"logit_lens" previously returned zero hits. The answer is unflattering, which is the reason it
belongs here rather than the reason to omit it.

Script `src/boombness/analyze_g64.py`; artifact `outputs/boombness/g64_metric_comparison/`
(`correlation_table.csv`, `g64_summary.json`, 3 plots). All numbers below are from that CSV.

### The coverage problem comes first

| population | n |
|---|---|
| judged (ASR available) | 270 |
| with extraction (logit-lens + direction) | 270 |
| with a probe score at the headline layer | **72** |
| **common to all three** | **72 of 270 (27%)** |

`probe_boombness` is out-of-fold margins from the `d5_surface_matched_codeword` regime, whose rep
cache was built on a **1464-row** version of the bank against today's 2352, and whose regime is
hardcoded to the `core2x2` block. So the three metrics are **not** computed on the same prompts
unless they are restricted to the common 72 — which `--common-subset` now does by default. Every
number in this section is on those 72. An earlier comparison that put probe (n=72) beside direction
(n=270) as if like-for-like is **retraction #9**.

### The three metrics disagree about ASR — including in sign

Spearman ρ against the continuous StrongReject score, n=72, 6 domains. `ρ_within` is the
within-domain estimate the permutation p actually tests; `ρ_pooled` is the raw pooled value. (They
were adjacent and unlabelled until 2026-08-18; see the estimand note in the process section.)

| layer | logit_lens ρ_within | direction ρ_within | probe ρ_within |
|---|---|---|---|
| 0 | **+0.274** (p=0.005) | +0.185 (0.099) | **+0.215** (0.034) |
| 4 | −0.211 (0.086) | **+0.324** (0.008) | +0.145 (0.243) |
| 8 | −0.171 (0.154) | **+0.297** (0.015) | +0.087 (0.455) |
| **12** | **−0.026** (0.818) | +0.228 (0.076) | **+0.284** (0.010) |
| 16 | −0.176 (0.093) | −0.151 (0.196) | +0.202 (0.075) |
| 20 | **−0.296** (0.006) | −0.184 (0.127) | +0.186 (0.100) |
| 24 | −0.074 (0.538) | −0.185 (0.120) | +0.132 (0.233) |
| 28 | +0.068 (0.580) | −0.141 (0.256) | +0.123 (0.248) |
| 31 | +0.139 (0.217) | +0.149 (0.210) | +0.082 (0.412) |

**There is no layer at which all three agree.** At L12 — the layer this report headlines for G2 —
they read **−0.026, +0.228, +0.284**: one of the three has the opposite sign, and it is the
logit-lens metric, the most direct readout of "does this token look like *bomb* to the unembedding".
Each metric's strongest ASR association is at a different layer and, for logit_lens, in the opposite
direction: logit_lens peaks **negative** at L20 (−0.296), direction peaks **positive** at L4
(+0.324), probe peaks at L12 (+0.284).

**Multiplicity:** this is 27 metric×layer cells per target, uncorrected. At Holm m=27 only p≤0.0019
survives the first step, so **none of the ASR cells above is individually safe** — the smallest is
p=0.005. Read the table as a disagreement map, not as nine findings.

### On comprehension the three agree much better

Same 72 prompts, target = the §2.6 comprehension log-odds:

| layer | logit_lens | direction | probe |
|---|---|---|---|
| 4 | +0.214 (0.084) | **+0.316** (0.008) | **+0.442** (0.0005) |
| 8 | −0.123 (0.351) | **+0.336** (0.004) | **+0.473** (0.0005) |
| **12** | −0.156 (0.198) | **+0.361** (0.003) | **+0.462** (0.0005) |
| 16 | −0.273 (0.027) | +0.098 (0.429) | **+0.375** (0.002) |
| 31 | **+0.437** (0.001) | +0.127 (0.319) | **+0.396** (0.0005) |

`probe_boombness` is positive and significant at **every** layer tested, and survives Holm at m=27.
`direction_boombness` is positive and significant through the early-mid stack.

### What this section concludes

1. **The axis predicts comprehension far better than it predicts attack success.** That is the
   cleanest statement §6.4 supports, and it is consistent with — and independent evidence for — the
   report's overall position that Boombness is a representational quantity whose behavioural
   consequences are mediated by something else (refusal).
2. **"Boombness" is not one quantity.** Three reasonable operationalisations of the same construct
   disagree in sign about ASR at the sprint's own headline layer. Any claim of the form "Boombness
   predicts X" must name the metric and the layer, and G2's ρ=+0.307 should be read as a statement
   about `direction_boombness` at L12 specifically.
3. **The probe is the strongest metric on both targets but covers 27% of the population.** Fixing
   that means re-fitting the probe on the current 2352-row bank and lifting the `core2x2` hardcode
   in `probes.py:199` — not done, and the honest reason the probe is not promoted to the headline.

### ⚠ Carried caveat, added 2026-08-18

`logit_lens_boombness` and the comprehension target are both computed from single-token readouts
that the whole-answer diagnostic has since shown are measured in the far tail of the next-token
distribution (see the readout note in the process section). The comparison above is internally
consistent — all three metrics are scored the same way — but the **comprehension column will move**
when §4b is re-scored with the corrected readout. This section will be regenerated at that point.

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

## §15.5 Tokenization audit (plan §2.4 — mandatory)

`tokenization_audit/audit_20260817_013432_3151000`, 2352/2352 rows, 0 failures:

| check | result |
|---|---|
| target occurrences that are a **single** token | **2352 / 2352** |
| tokenization flagged ambiguous | **0** |
| `tokenization_ok` | **True on every row** |
| distinct subtoken ids used | 2 — `[75294]` (` carrot`, 1776 rows) and `[13054]` (` bomb`, 576 rows) |

**Why this mattered.** An earlier bank quoted the target as `"{W}"` and placed demonstrations
sentence-initially, which produced **890 of 5808** two-subtoken occurrences (`car`+`rot`,
`Car`+`rot`). A two-subtoken occurrence puts a *different vector* at `codeword_last` — the embedding of
`rot`, not of `carrot` — so any per-token comparison silently mixed two different quantities. The bank
was regenerated to force the leading-space whole-word form; the variant table in the audit summary
records that `carrot` alone is 2 tokens while ` carrot` is 1, which is exactly the trap.

**Alignment:** 0 violations among the **216** of 912 families where the exact-swap invariant is defined
(the other 696 are forced-choice and cannot satisfy it by construction).

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
**Yes, modestly — in Llama-3.1-8B, and only there** (it does not replicate on Qwen3-14B; see §14). ρ = **+0.307** (`d_surface|L12|proj`), **+0.302** norm-partialled, n = 234, 6/6
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
⛔ **RETRACTED — the answer is YES, by a little (retraction #6).** I reported a tight null; the paired
within-stem test gives F(5,355)=20.30, p=8.1e-18 with 11/15 pairwise gaps surviving Bonferroni, and the
"3.6%" statistic used a between-stem denominator where the within-stem residual was correct (53%). The
effect is **small but reliable** — largest pairwise gap 4.1% of the grand mean. The naive one-way test that produced
"F = 0.175, p = 0.972" pooled across design cells and used a between-stem denominator; the paired
within-stem test on the perfectly-crossed design gives **F(5,355) = 20.30, p = 8.1e-18**. The claim that
content, domain, demo count and query were "held fixed" was **false for that pooled analysis** — `plain`
and the five role styles occupy disjoint `bank_block`s with zero family overlap. Whether role framing
changes *ASR* remains unresolved (F = 1.94, p = 0.087; largest pair ≈ 0.105 Bonferroni). `role_style` is a
categorical proxy — no Userness/CoTness probe was fitted.

**9. Can we surgically remove Boombness without destroying comprehension?**
⚠ **UPDATED — the answer depends on which instrument you use, and the two disagree.**
- **By attention-edge knockout: no.** The retrieval is massively redundant — cutting 6.25% of demo→query
  edges does nothing *however distributed across depth*, while cutting 100% recovers 84% of the deletion
  ceiling. Every localized knockout (16 edges, ~0.03%) reads zero. The converse test is impossible by
  construction (a layer holds only ~3,648 edges).
- **By direction projection: YES, and it is measurable.** `project_out d_surface` at L8 leaves comprehension
  **statistically unchanged** (Δ +0.088, p=0.681 — the only one of five arms that does) and coherence intact,
  while beating an inert projection control by **+0.056, p=0.0077**, on harmful conditions only. So a
  *surgical removal that preserves comprehension* does exist — it just is not an edge cut, and its effect is
  to **raise** attack success, not lower it.
⚠ Single-model: this does not replicate on Qwen3-14B (see §14).

**10. Can we turn Boombness into a useful GCG objective?**
⛔ **UPDATED — my earlier "no" was reached by faulty reasoning, and the honest answer is "not as §12.1
specifies; §12.2 is reopened".**
- **§12.1 (maximise Boombness alone): still NO** — but for a *demonstrated* reason rather than the one I
  gave. Adding `+0.25` alone drives refusal 0.057 → **0.676** and ASR *down* to 0.088. My original reason
  ("no directional causal support") was **wrong**: there is directional support, it was masked by refusal.
- **§12.2 (Boombness MINUS refusal): reopened, worth building as an experiment.** Composing the two takes
  ASR 0.243 → **0.548** (p<0.0001), where neither manipulation alone raises it. ⚠ But **not vindicated**:
  the gain is *not conditional on the doublespeak mapping* (+0.267 where the mapping is never taught,
  largest at zero demonstrations) and **does not transfer to explicitly harmful prompts** (+0.000), which is
  what an attack objective would require.
- The 4-draw band figure quoted earlier (p=0.0014) was **retracted** — those four "draws" were one draw
  wearing four labels; on a genuine 4-draw band it is p=0.043.

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

## Limitations and safety scope

**Dual-use scope.** This work studies *why* a known jailbreak family works, in order to characterize it.
It produces no operational harmful instructions. All harmful content is benchmark material behind
project abstractions, and harm labels are automated (StrongReject rubric via `gpt-4o-mini`).

**What is stored.** Judge scores, refusal flags, and scalar degeneracy statistics. Raw generations stay
in local run directories under `outputs/` (git-ignored) and **no completion text appears in any report,
commit message, or analysis artifact**. Every subagent audit in this sprint was explicitly restricted to
numeric fields and source code for the same reason.

**Attack targets.** Only the local open-weight model (`Llama-3.1-8B-Instruct`). No proprietary or
hosted model was attacked; the only API use is the *judge*, which evaluates rather than generates.

### We do NOT claim to have found the mechanism. Plan §13's six criteria, scored honestly:

| # | criterion | met? |
|---|---|---|
| 1 | Boombness predicts ASR across prompts | **YES IN LLAMA ONLY** — ρ=+0.307, p<5e-4 clustered, 6/6 domains positive (2 near-null); on Qwen3-14B the same measurement is carried by 1 of 6 domains (clustered p=0.206) |
| 2 | Adding Boombness increases behaviour or relevant internal scores | **YES, once refusal is removed** — alone it *decreases* ASR by triggering refusal (0.057→0.676), but composed with refusal-removal it takes ASR 0.243→**0.548** (p<0.0001) where neither manipulation alone raises it. The earlier **NO** was a ceiling effect of refusal. ⚠ The gain is not conditional on the doublespeak mapping, so this is scored on behaviour, not on mechanism. |
| 3 | Removing Boombness reduces ASR | **NO — it RAISES it, and this is now controlled.** `project_out` beats an inert projection-type control by +0.056 (p=0.0077) on harmful conditions, ≈0 on benign, comprehension unchanged (p=0.681). ⚠ Single-model — does not replicate on Qwen3. |
| 4 | Comprehension is preserved | **NOW MEASURED (§2.6).** project_out: preserved (p=0.681). +0.25: improves (+0.643). −0.25: **degrades below zero** (−0.792) → disqualified. But the effect is **sign-driven, not axis-specific** — a norm-matched random step moves comprehension MORE in both directions (C10). |
| 5 | Random controls fail | **YES for the projection result, PARTIAL for the additive one.** ⛔ The p=0.0014 figure previously quoted here came from a band whose four "independent draws" were byte-identical (retraction #7); on a **genuine** 4-draw band it is **p=0.043**. Where controls are unambiguous: the **projection control is inert on every condition** (−0.018 vs baseline, p=0.26) while the arm moves harmful conditions by +0.056; and the **composed random control** does nothing on doublespeak (p=0.116) — though it *reverses* on `direct_harmful` (+0.389), so specificity there is scoped, not general. |
| 6 | Replicates across prompt families or models | **PARTIAL, and mostly NO for the causal claims.** Replicates: the ~2× confound (median 1.74 on Qwen3), the token-level positional result, the final-layer effect at matched depth (Llama L31 +0.047 vs Qwen3 L39 +0.052). Does NOT replicate: **G2's correlation** (1 of 6 domains on Qwen3) and **the projection causal result** (mirror-image condition profile). Across *prompt families* the projection result replicates well — it holds on all three harmful conditions. |

**Two of six met, three partial, one no. So the correct description is a documented correlational
finding with a directional null — not a mechanism.** The §18 label is B for exactly this reason, and
§12's objective was not built.

### Specific limits a reader should carry
- **One model, one concept pair, one judge.** Llama-3.1-8B, carrot↔bomb, StrongReject/`gpt-4o-mini`.
- **G1 is a pilot**: n=8 families from **2 domains**, and its headline is one arm of ~130.
- **G3's identification is one-sided by construction** (a layer holds only ~3,648 edges).
- **G1/G3 run on `semantic_one_word` prompts; G2/G4's ASR claims run on `behavioral` ones.** C7 showed
  this is not merely a join hazard — it changes the sign of a reported effect.
- **"Refusalness at the codeword token" is off-label** — the direction was fitted for a last-token
  readout and its condition ordering degrades badly there.

---

## Exact commands to reproduce the main runs

All GPU stages go through one wrapper. **Argsfiles must live on the shared filesystem** — `/tmp` is
node-local and the job dies in 3 seconds (this cost a launch cycle; see the tick log).

```bash
AD=$PWD/outputs/boombness/argsfiles          # shared FS, NOT /tmp
BANK=$PWD/data/boombness_prompts/boombness_prompt_bank.jsonl   # sha 71bea179345ed118

# 1. prompt bank + mandatory audits
python src/boombness/prompt_families.py --out "$BANK"
sbatch --export=ALL,BOOMB_SCRIPT=tokenization_audit.py,BOOMB_ARGSFILE=$AD/tokaudit.txt        src/boombness/slurm/run_boombness.sh

# 2. extraction — BOTH readout positions (the 2x2 needs both; --position last was once wired
#    into stage_fit only, producing a phantom cell)
printf -- '--bank %s --stage both --layers all --position codeword_last --tag full\n'  "$BANK" > $AD/x_cw.txt
printf -- '--bank %s --stage both --layers all --position last          --tag lastpos\n' "$BANK" > $AD/x_last.txt
for f in x_cw x_last; do sbatch --export=ALL,BOOMB_SCRIPT=extract_boombness.py,BOOMB_ARGSFILE=$AD/$f.txt        src/boombness/slurm/run_boombness.sh; done

# 3. behaviour + judge  (judge refuses to start without OPENAI_API_KEY, by design)
printf -- '--bank %s --query-kinds behavioral --arm base --tag base\n' "$BANK" > $AD/base.txt
sbatch --export=ALL,BOOMB_SCRIPT=score_behavior.py,BOOMB_ARGSFILE=$AD/base.txt src/boombness/slurm/run_boombness.sh
set -a; source .env; set +a
python src/boombness/judge_boombness.py --gens <GENS_DIR> --bank "$BANK" --tag base

# 4. refusalness at BOTH positions (matched footing — the 3.7x retraction)
for POS in codeword_last last; do
  printf -- '--bank %s --layers 12,14,16,18,20 --query-kind behavioral --position %s --tag %s\n' \
    "$BANK" "$POS" "$POS" > $AD/ref_$POS.txt
  sbatch --export=ALL,BOOMB_SCRIPT=refusalness.py,BOOMB_ARGSFILE=$AD/ref_$POS.txt src/boombness/slurm/run_boombness.sh
done

# 5. G1 / G3 / G4
sbatch --export=ALL,BOOMB_SCRIPT=aggressive_patching.py,BOOMB_ARGSFILE=$AD/g1.txt src/boombness/slurm/run_boombness.sh
printf -- '--bank %s --fit-dir <FIT> --layers 8,18 --topk 8 --n-families 6 --n-examples 4 \
--query-kind semantic_one_word --dst both --demo-scope block --tag edgematch\n' "$BANK" > $AD/g3.txt
sbatch --export=ALL,BOOMB_SCRIPT=surgical_knockout.py,BOOMB_ARGSFILE=$AD/g3.txt src/boombness/slurm/run_boombness.sh
# steering + a >=3-draw random-control band (one draw cannot support "more than a random direction")
for S in 20260817 20260818 20260819 20260820; do
  printf -- '--bank %s --query-kinds behavioral --fit-dir <FIT> --intervene random:add:8-8:0.25 \
--arm ctrl_rand_s%s --seed %s --tag ctrl_rand_s%s\n' "$BANK" "$S" "$S" "$S" > $AD/ctrl_$S.txt
  sbatch --export=ALL,BOOMB_SCRIPT=score_behavior.py,BOOMB_ARGSFILE=$AD/ctrl_$S.txt src/boombness/slurm/run_boombness.sh
done

# 6. ANALYSIS — all CPU, all committed, every gate-bearing number comes from here
PY=<conda-env>/bin/python     # needs scipy/sklearn; the login shell has neither
$PY src/boombness/analyze_g2.py --judge <JUDGE> --extract <EXTRACT_CW> --score <GENS> \
    --refusalness <REFUSAL_CW> --extract-position codeword_last --cluster-by domain \
    --out outputs/boombness/g2_analysis_cwpos.json
$PY src/boombness/analyze_position.py --judge <JUDGE> \
    --extract-codeword <EXTRACT_CW> --extract-last <EXTRACT_LAST> \
    --refusalness-codeword <REFUSAL_CW> --refusalness-last <REFUSAL_LAST> \
    --out outputs/boombness/position_2x2.json
$PY src/boombness/analyze_g1_g3.py --g1 <PATCH_RUN> --g3 <KNOCKOUT_RUN> --out outputs/boombness/g1_g3_analysis.json
$PY src/boombness/analyze_steering.py --baseline <JUDGE_BASE> --arms <JUDGE_ARMS...> \
    --out outputs/boombness/steering_analysis.json
$PY src/boombness/analyze_role.py --extract <EXTRACT_ROLE> --judge <JUDGE_ROLE> \
    --out outputs/boombness/role_analysis.json
$PY src/boombness/reanalyze_corrected.py --run <EXTRACT_CW> --metric d_surface|cos \
    --out outputs/boombness/reanalyze_d_surface_cos.json
$PY src/boombness/probes.py --run <EXTRACT_CW> \
    --regimes d5_surface_matched_codeword,d6_surface_matched_concept --tag surfmatch
```

**Three refusals are load-bearing and will stop you if inputs are wrong** — this is intended:
`analyze_g2.py` refuses when the two probes' readout positions disagree; `analyze_position.py` refuses
unless every run's readout position is verifiable *from its artifact*; `analyze_steering.py` refuses to
report an arm whose coherence was never assessed.

---

## ★ THE HEADLINE RESULT — Boombness IS causal, and refusal was hiding it (added 2026-08-18)

**This supersedes the §18 = B label and reopens §12.** Everything below is at a matched 512-token budget,
n = 420, every arm complete and coherence-gated on the doublespeak population, domain-clustered over 6
domains.

| arm | ASR | refusal | Δ score vs baseline | p_cl |
|---|---|---|---|---|
| baseline | 0.2429 | 0.0571 | — | — |
| add Boombness `+0.25` | 0.0881 | **0.6762** | −0.1274 | 0.0117 |
| remove refusalness | 0.2690 | **0.0000** | +0.0101 *(0.9× the judge-noise sem — **not measurable to ±0.03**, not "does nothing")* | 0.4746 |
| **add Boombness AND remove refusalness** | **0.5476** | 0.0024 | **+0.2824** | **<0.0001** |
| **RANDOM direction + remove refusalness** *(control)* | **0.2190** | 0.0000 | −0.0321 | 0.1160 |

⚠ **The control is inert only on THIS condition, and reverses elsewhere.** On `direct_harmful` the same
random composition raises score by **+0.389 (p=0.008)** and cuts refusal **0.96 → 0.54**, while arm F stays
at baseline (+0.000, refusal 0.96). On `concept_in_benign_ctx` it gains +0.203. **Specificity is established
for the doublespeak population only, and is reversed where harm is explicit.**

**Neither manipulation alone raises attack success — together they more than double it.**
Interaction contrast (F−A) − (C−base) = **+0.400 continuous, p=0.0001**, and +0.471 / +0.433 / +0.364 at
ASR thresholds 0.25 / 0.50 / 0.75.

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
(L18), and `d_surface` fitted on the same bank it is evaluated on. The Qwen3 replication of the *projection*
arm is running; **G2's correlation did not replicate on Qwen3**, so cross-model generality is an open
question for this result too.

---

## ★ SECOND CAUSAL RESULT — removing the concept component helps attacks, on Llama (added 2026-08-18)

Unlike the interaction above, this one survived every check **including the ones that refuted the
interaction's mechanism**. Llama-3.1-8B, 512 tokens, n=420, all arms gate-passed and length-matched by
construction (163 vs 150 median words), against a **projection-type** control:

| contrast | Δ score | t_cl | p_cl |
|---|---|---|---|
| `project_out d_surface` − baseline | +0.0378 | +5.12 | **0.0037** |
| `project_out RANDOM` − baseline | −0.0182 | −1.27 | 0.260 — **inert, as a control should be** |
| **`d_surface` − RANDOM control** | **+0.0560** | **+4.30** | **0.0077** |

**5× the measured judge-noise floor.**

### The cross-condition profile is what makes it credible
| condition | arm − control |
|---|---|
| `benign_literal` | **+0.0069** |
| `benign_remap` | **+0.0104** |
| `concept_in_benign_ctx` | **+0.0035** |
| `natural_doublespeak` | **+0.0560** |
| `direct_harmful` | **+0.0556** |
| `direct_codeword` | **+0.0590** |

**≈0 on every benign condition, ≈+0.056 on every harmful one.** So the claim is **harm-general, not
doublespeak-specific**:

> Removing the concept component from the codeword position raises attack success **wherever there is an
> attack**, and does nothing where there is not.

That is a stronger statement than "it helps doublespeak" — it generalises across three attack types while
remaining absent on benign inputs. It is also **exactly the shape the arm-F "capability channel" failed to
show**, which is why that one was retracted and this one was not.

### ⛔ It does NOT replicate on Qwen3-14B — and the failure is informative
Same intervention, same fitting procedure, same relative depth (25% vs 27.5%), same bank, **inert control on
both models** — and mirror-image condition profiles:

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

The Qwen3 effect is real and `d_surface`-specific (its random-projection control is inert, −0.004,
p=0.77), but it raises judged harmfulness nearly everywhere.

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
