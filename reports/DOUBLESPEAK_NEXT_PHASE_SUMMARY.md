# Doublespeak next phase — concept-specific Boombness and surgical demonstration causality

**Self-contained.** Reading this requires no other document. Full append-only log:
`external_md/DOUBLESPEAK_CONCEPT_SPECIFIC_BOOMBNESS_AND_SURGICAL_CAUSALITY_PLAN_AND_PROGRESS_20260902.md`
(id namespace `DCS-`). Branch `behavioral-causality-sprint`, `c8263888..`.
Dates 2026-09-02 → 2026-09-03. Model **Llama-3.1-8B-Instruct** unless stated.

---

## The one-paragraph truth

The phase was asked whether an intuitive, **concept-specific** measure of "the codeword is becoming
the harmful concept" can be built and validated, and whether the demonstration-processing
computation that produces it is causally responsible for the attack. **The answer to the first is
no, to the second is half-yes, and the two together are the result.** A codeword→concept movement
exists and is **causally demonstration-dependent** — blocking the query span from the demonstrations
takes the model's own forced-choice reading of `button` from +5.19 to **−2.76** log-odds, a **sign
flip away from the harmful concept**, replicated on a second codeword, against a dose-matched control
that does nothing. That path is **remapping-specific**: the identical intervention barely moves the
cell where the word already *is* the concept (DiD −9.89 and −9.35 on two codewords, 37/38 domains,
p = 2.8e-10). But the representation is **not specific to the harmful concept** (knife/gun/club
match or exceed bomb) and **does not accumulate** across demonstrations.
**And the same intervention reduces the attack** — a
conclusion reached only after two reversals. The first control induced refusal (a channel `KO-3`
annihilates to zero), which masked the effect and produced a false null; against the one
**refusal-neutral** control of the three that exist, `KO-3` removes attacks with the direction
confirmed across two independent judgings, domain clustering (p = 0.0089), 24 of 34 non-tied
domains, and a composition-free endpoint on which `KO-3` sits below every control and the baseline.
⚠ **The magnitude is ≈ −30 of 153 rows, consistent across 3 near-refusal-neutral controls × 2 seeds × 4
judgings (−41, −21, −28)** — but ⛔ **at the domain level, the independence unit this project
declared for itself, it does not reach significance** (sign p = 0.061 / 0.150 / 0.136; pooled
p = 0.405; only a magnitude-aware clustered permutation reaches p = 0.032). The design is genuinely
underpowered at that unit, and **38 domains is the ceiling that exists** — fixing it needs new
demonstration pools, not more rows, judgings or seeds. The `dev`/`heldout` asymmetry was tested
directly and is **not** distinguishable from chance (p = 0.14 / 0.23); **91 % of the endpoint is
off-goal text**. So: the mechanism is real,
demonstration-built, remapping-specific, and **behaviorally causal in direction**; gate `R5` is
passed at the query-span scope and **fails at the codeword-row scope**, and the magnitude awaits
replicate judging (`DCS-PR-005`).

---

## What was preregistered before any forward pass

`DCS-PR-001` (the `KO-1`/`KO-2` arms, the DiD estimand, and the decision rules) · `DCS-PR-001a` (the
DiD pairs by domain, not by prompt — recorded when the constraint was discovered, before outcomes) ·
`DCS-PR-002` (the specificity test moved to the readout channel, with its gates) · `DCS-PR-003` (the
`basket` bank's 3-row defect and its handling, written while the arms were still running) ·
`DCS-PR-004` (the mediation test, **with its power checked in advance** and both admissible outcomes
declared). The §1 preregistration itself was committed before any extraction, generation or outcome
column existed.

---

## ESTABLISHED RESULTS

| # | result | evidence | verdict |
|---|---|---|---|
| `R-010`/`R-011` | **The demonstration→query path is necessary for the remapping and specific to it.** `KO-3` (whole query span ↛ demonstrations, L6–14) drives the codeword cell from **+5.19 → −2.76** (`button`) and **+6.79 → −3.80** (`basket`) — a sign flip **away from the concept reading** — while barely moving the cell where the word *is* the concept. ⚠ `R-032` decoded what the model actually **says**: the concept answer is destroyed on both models (Llama ` Bomb` **345→19**; Qwen ` bomb` **306→8**), but the **replacement is model-dependent** — Qwen restores the literal codeword cleanly (` button` **97.9 %**, `option_mass` 1.000), while Llama mostly answers ` Neither` (**67.1 %**, only **26.8 %** ` Button`) with `option_mass` collapsing **0.877→0.353**. ⛔ *"Flips back to the literal meaning"* is therefore true of **Qwen**, not of Llama. **DiD −9.889 and −9.352, both 1+/37− domains, both p = 2.838e-10**, floor 7.28e-12 | 2 codewords × 6 arms × ~380 rows × 38 domains; dose-matched controls negligible; adversarially audited (`DCS-A-002`) | **REPLICATED, remapping-specific** |
| `R-012b` | **Refusal is annihilated by `KO-3`**: 42 → **0**, while the dose-matched control moves it the *other* way (42 → **75**). −75 rows vs control, **0+/26− domains, p = 2.98e-08** | as above | **STRONG, and endpoint-scoped** |
| `R-016`/`R-019` | **`KO-3` reduces attack against refusal-neutral controls — in DIRECTION.** All 3 qualifying controls negative (−41, −21, −28; mean **−30** of 153), across 2 seeds and 4 judgings. Composition-free endpoint: `KO-3` attack rate among non-refused rows **0.313** vs every control 0.384–0.473 and baseline 0.453. ✅ The prospective prediction held — a **rejected** draw (+32 refusals) shows no contrast (−16, p = 0.221) | 6 arms × 380; audited (`DCS-A-004`) | **DIRECTION ONLY.** ⛔ Not significant at the domain independence unit (0.061/0.150/0.136; pooled 0.405) |
| `R-021`/`R-022` | **No single query position carries the mapping, but ~¼ of the span suffices.** Five-point row ladder, each rung against its own dose-matched control: K=1 **−0.013**, K=2 **−0.012**, K=8 **−6.616** (0+/38−, p=7.28e-12), K=16 −7.888, K=32 −8.081. A **step** between 2 and 8 rows, then saturation (K=16 already 97.6 % of full). ⚠ Controls are **inert across a 32× dose range** (+5.16…+5.38 vs baseline +5.188), so the step is about *which* keys are cut, not how many cells | 10 arms × 380 × 38 domains | **THRESHOLD, not distributed** |
| `R-024` | **`KO-3` REPLICATES ON QWEN3-14B at ~3× the magnitude.** Cell `C` baseline +10.140 → `KO-3` **−13.080** (frac > 0 collapses **0.813 → 0.021**), control inert at +10.357. **−23.437 vs control, 1+/37− domains, p = 2.838e-10** — the *identical* domain split as Llama. Band 7–17 (same relative depth as 6–14 on 40 layers), `--enable-thinking false`, capability gate passed first (`R-023`) | 4 arms × 380 × 38 domains | **CROSS-MODEL** |
| `R-025` | **The specificity DiD replicates on Qwen3-14B.** Cell `C` −23.437 vs its control, cell `B` **−1.238 (p = 0.256)**; **DiD −22.198, 1+/37−, p = 2.838e-10**. ⚠ The three settings share the *same* 1+/37− sign pattern, so the identical p-values are **one pattern replicated, not three independent tests** | 4 arms × 380 × 38 domains | **CROSS-MODEL SPECIFICITY** |
| `R-026` | **Qwen `KO-3` removes ALL 150 refusals** (judge-free). ⚠ `TSC-R-006` reported the same 150 removed at a *different* scope — so Qwen's refusal behaviour on this population is 150 rows and **both** demonstration-cutting scopes annihilate it | n = 380 | **refusal, 2 models × 4 scopes** |
| `R-030`/`R-031` | **The effect lives in layers 0–14, peaks at 10–14, and is absent above 14.** Equal-dose 5-layer bands: 0–4 **−3.39**, 5–9 **−2.99**, **10–14 −5.65** (0+/38−) — **no band null**; coarse sweep adds 15–23 **+0.15**, 24–31 **+0.75** | 14 arms × 380 × 38 domains | **GRADED, not bounded at 6–14** ⚠ the inherited window contains the peak but layers 0–5 also contribute |
| `R-041`/`R-043` ✅ **settled by `PR-023`/`R-055`** | **The demonstration knockout removes more where more was installed — CATEGORICALLY.** Fully-installed domains lose more than partially-installed ones. ρ<sub>KO</sub> **−0.693 / −0.594 / −0.444 / −0.734** across **three populations, two models, three doses**; robust to leave-one-out and to three operationalisations on all of them. ⛔ **There is NO continuous dose-response within the partially-installed range** — attack `C` fails on all three (13 dom **p=0.343**, 30 dom **p=0.504**, **33 dom p=0.210** on a bank built specifically to provide the range). ✅ **The apparent within-range gradient is REGRESSION TO THE MEAN, shown within a single arm**: on `cds_n1` the *control's* ρ goes **−0.086 → −0.338** purely by conditioning on the varying subrange, with no knockout applied | 4 populations × 38 domains; audited 3× through one committed code path (`A-009`, `PR-022`, `PR-023`) | ✅ **CATEGORICAL, settled**; ⚠ correlational, and dose is confounded with population in the low-dose bank |
| `PR-013`/`R-035` | ⚠ **Generality across harmful concepts: MIXED.** Same pipeline, preregistered band 6–14, on two concepts already in-repo. `lantern`→`poison` **PASSES** the declared primary (Δ **−7.760**, **0+/20−**, p = **1.907e-06**, at floor). `candle`→`missile` **FAILS** (−2.333, 6+/14−, p = **0.115**) — its mapping is weak *before* any intervention (concept-answer **0.400** vs 0.887/0.908 elsewhere). ⛔ Dose-matched control **structurally impossible** in these banks (`R-033`: no preamble ⇒ prompt is ~85 % demonstration, `match_ratio` 0.000), confirmed on **both** concepts ⇒ generic damage **not excluded here**, only inherited from `bomb`. ⚠ `R-037`: the layer placebo (identical keys at 15–23) is **not inert** — it is **13.6 % / 17.2 %** of the 6–14 magnitude with the **opposite sign**, so generic damage is **partially** excluded, not excluded. ⛔ `R-038`: the *weak-mapping* explanation offered for `candle` is **NOT supported** — doubling demonstrations raised installation 0.400→0.525 and grew the effect 47 %, while the sign split stayed **bit-identical** (6+/14−, p = 0.115). `R-039`/`R-041` supply the explanation instead: `candle`'s domains **span** the installation range while `lantern`/`button` sit at the ceiling | 2 concepts × 160 rows × 20 domains, + 4 arms at n=16 and 2 layer-placebo arms | **MIXED — 1 of 2; may NOT be stated as "generalises"** |
| `R-029` (corrected by `C-023`) | ⛔ **Qwen behavioral = `CANNOT ANSWER` by comparator selection.** 0 of 6 draws meet the ±17 tolerance at a 150 baseline. ⚠ `R-029`'s *explanation* is **WITHDRAWN**: it blamed an absolute-vs-relative band, but `refused` is `kw_refusal` — deterministic, **measured judge band = 0** — so there was never a noise band to rescale. The ±17 is a tolerance borrowed from `malicious_at_0.5`. ⇒ Re-analysed by **bounding**, not selection (`PR-014`) | 6 draws × 380 | **criterion limitation, NOT a null** |
| `R-050` | ✅ **The paradigm installs whatever the demonstrations say.** With **benign** demonstrations (*"a large crate of button puree"*) the model resolves `button` to the **food** sense — ` Mushroom` **22**/380, ` Vegetable` 2, ` Salad` 1, concentrated in `instructional` 6/10 — and answers ` Bomb` in **3/380**. ⇒ `R-002`'s negative ("the geometry is not `bomb`-specific") shown **positively**: swap the demonstrations and a benign remapping appears by the same route | 1 arm × 380 × 38 domains; ⛔ says nothing about the *causal* results, all measured on the harmful mapping | **mechanism, not harm-specific** |
| `R-002` | **The movement is NOT concept-specific.** Against `knife`/`gun`/`club`, three of four comparisons run the *other* way and every difference is inside the measured split-to-split band (median 0.015, p90 0.044) | 10 banks, dev + heldout | **evaluated negative** |
| `R-003` | **The shift does not accumulate.** Final occurrence > first in 32/32 cells, but demonstrations-only ρ **disagrees in sign between banks** (−0.048 vs +0.278) and the effect is flat in `n_examples` (7.01/7.25/7.10/6.54) | 2 banks × 32 layers, per-row, cross-fit | **evaluated negative** |
| `R-004` | **Null control fires exactly:** at `n_examples = 0` the paired `C−A` is `0.000e+00` at all 96 cells — correct, since A and C are byte-identical without demonstrations | 2 banks | **positive control** |
| `R-006` | `KO-1` (final codeword row ↛ demonstrations) is a **well-powered null on attack** (+11 rows, p = 0.597, floor 4.66e-10) and **halves refusal** (−21, 0+/13−, p = 2.44e-04 = its floor) | 6 arms × 380 | **null + refusal effect** |
| `R-005` | `KO-1` leaves the **mapping intact** (+0.278, 25+/13−, p = 0.073 on the preregistered sign test) | 3 arms × 380; audited (`DCS-A-001`) | **null** |

### The dissociation — ⚠ NARROWED by `C-015`

All **three** knockout scopes tested move **refusal** by a large, well-powered margin:
`TSC-R-006` (Qwen3, `demo_processing_only`: all 150 refusals removed) ·
`DCS-R-007` (Llama, `target_surface_row_only`: refusal halved, p = 2.44e-04) ·
`DCS-R-012b` (Llama, `query_prefill_only`: refusal 42 → **0**, control 42 → **75**, p = 2.98e-08).

⛔ **But "and attack is not" is now FALSE at the scope that matters.** It holds for `KO-1`
(`R-006`/`R-014`: +11 rows on a control verified refusal-neutral, Δ = 0, zero attack→refusal
conversions — the mapping was never destroyed there either). It does **NOT** hold for `KO-3`:
against the refusal-neutral control the attack **does** fall (`R-016`, direction established).
⇒ **The dissociation is scope-dependent, and that is the finding.** Cutting the demonstrations off
the *codeword row* changes neither representation nor attack; cutting them off the *whole query
span* changes **both**. Refusal moves under all three scopes tested.

---

## EXPLORATORY / NOT CONFIRMATORY

* The `KO-1` readout **increase** (+0.363, p = 0.034 on the preregistered sign test) is a point
  estimate. Magnitude-aware tests over the same domains give p ≈ 2e-04 and clear Holm×7 — but the
  sign test is what `PR-001` registered, and ⛔ switching statistics because one returns a smaller p
  is the shopping this phase forbids.
* `R-009`: specificity at the `KO-1` scope is a **capable null** (DiD +0.503, p = 0.073), but it is
  a weak test of a weak effect and must not be read as evidence against specificity.
* `R-039`: the **reversal** at installation ≈ 0 — domains where the mapping never installed move the *other*
  way under the knockout (+1.14 … +3.20) — is **`candle`-only and exploratory**. ⛔ It is `CANNOT_ANSWER` on both
  headline populations, which contain **1** low-installation domain each, and the analyzer emits that rather than
  running a split at n < 3.
* `R-042`: `cds_n8` (a never-before-run block) makes the effect grow — mean per-domain Δ **−7.944 → −9.025**,
  **34/38** domains, p = **6.04e-07**. ⛔ **VOID as evidence about installation**, by `PR-018`'s own declared rule:
  installation barely moved (0.908 → 0.928, 25/38 domains already at ceiling), so this is a **dose** effect of the
  kind `R-022`'s row ladder already established, and it is **not** counted as support for `R-041`.
* The hypothesis that `basket`'s cell-`B` ceiling (+10.67 vs `button`'s +6.27) explains the failed
  "opposite directions" replication. **Not tested.**

## FAILED / PARTIAL REPLICATIONS

* ⛔ **"The two cells move in opposite directions" does NOT replicate.** On `button`, cell `B` moved
  **up** (+1.808); on `basket` it moves **down** (−1.466, 5+/33−). The general claim is about
  **magnitude, not sign**. `R-010`'s strongest rhetorical form — *"generic damage cannot selectively
  improve one cell"* — holds **only on `button`**, as does the argmax evidence (4→104 vs 21→6).

## UNDERPOWERED / CANNOT ANSWER

* ⛔ **`KO-2` on the ASR endpoint.** Cell `B` baseline is **10/380 = 0.0263**, so the maximum
  removable is 10 rows against a 17-row judge band. No outcome could have reached significance.
  The registered DiD reports `UNINFORMATIVE BY CONSTRUCTION, k_informative = 1`. **This was my
  preregistration error** (`C-007`): `PR-001` fixed everything except whether the control cell could
  move, which twelve committed artifacts would have said for free.
* The concept/topical endpoint throughout: **degenerate on these banks** (one distinctive word,
  values ∈ {0,1}); it is a concept-word presence test, not topicality.

## NARROWED — state only in the qualified form

* ⛔ **"the installation gradient's effect size is −0.907"** — `R-051`: that contrast is inflated by a control
  gradient (+0.312) that does **not** reproduce on three other populations (−0.04, −0.02, −0.33). ⇒ Quote
  **ρ<sub>KO</sub> ≈ −0.44 … −0.73**, and the contrast only with its population named.
* ⛔ **"the effect is GRADED by installation" / any CONTINUOUS dose-response reading** — `R-053`: within the
  varying subrange the control reproduces most of the knockout's gradient (Qwen ρ<sub>ctrl</sub> −0.428 vs
  ρ<sub>KO</sub> −0.601), which is what RTM predicts. ⇒ The supported claim is **categorical**: *fully-installed
  domains lose more than partially-installed ones.*
* ⛔ **"attack `C` only failed for lack of power"** — run at **13, 30 and 33** domains across two models and
  three doses; p = 0.343 / 0.504 / 0.210. `PR-023` built a bank specifically to supply the range and it still
  failed. ⛔ **Dead.**
* ⛔ **"the within-range gradient is real but underpowered"** — `R-055`: on `cds_n1` the *control's* ρ moves
  **−0.086 → −0.338** by conditioning on the varying subrange **alone**, with no knockout applied. That is RTM,
  demonstrated within one arm.
* ⛔ **"installation predicts the effect size" as an unqualified gradient** — `A-009` attack `C`: on the 13
  domains that actually vary the contrast is **−0.503, p = 0.343**. ⇒ Say *"across the full range, dominated by
  the contrast between fully-installed domains and the rest."*
* ⛔ **"the dose-matched control is inert"** as a general statement — it is near-inert **on average across
  populations**, and it is **not** inert in the headline one.

## RETRACTED — never revive

| # | retracted claim | why |
|---|---|---|
| `C-010` | "The mapping is **constructed during demonstration processing**, not retrieved at the final codeword token" | The knocked-out token sits 10 tokens before the end and the readout is scored *after* it; every downstream position kept unblocked demonstration attention at all 32 layers. `KO-1` licenses only *"the final codeword token's own L6–14 demonstration attention is not necessary."* |
| `C-005` | `R-001`'s **L6–L12 peak** | Absent from the per-row standardized effect size, which is largest at L0 and declines. The peak exists only in a between-cell-mean distance ratio. |
| `C-008` | `R-005`'s **option-mass caveat** | Algebraically impossible: `logodds` is a difference of logsumexps over the full vocabulary, verified mass-invariant to 1.8e-15. The caveat *understated* the result. |
| `C-009`/`C-011` | "**The controls are inert**" | Negligible in magnitude (|Δ| < 0.31) but **not sign-null**: 31+/7− and 6+/32−. |
| `C-015` | **`R-012`'s null — "the mapping can be destroyed without the attack changing"** | Two independent defects. (a) Reported via a **domain sign test on row-paired data**; the correct McNemar gives p = 0.235, not 0.860, and the sign test's MDE is a **43 % reduction** — a 30 % reduction had power 0.10. (b) The dose-matched control suppresses attack **by inducing refusal** (19 direct `ATTACK→REFUSE`, refusal +33, p = 9.5e-07), a channel `KO-3` annihilates to **zero**, so the comparator is **not exchangeable**. Refusal-discounted: **−34 rows, McNemar p = 0.0051**. Status: **CANNOT ANSWER** |
| `C-016a` | "**All six `B-008` arms were judged in one invocation**" | **False.** Six processes, two batches, two commits. `d1` (batch A) 117 attacks vs `capped_d1` (batch B) **135** on **byte-identical text** — an +18 drift in the direction that inflates the headline contrast |
| `C-016b` | "**Four controls**" / "a family of six draws" | **False.** `capped_dK ≡ matched_dK` by construction here (`min(pool − demo) = +57`); verified 380/380 byte-identical. **Three** distinct draws exist. The promised six-point correlation would have been a fabrication |
| `C-016c` | `R-016`'s "**−36 attacks, p = 0.0034**" as a magnitude | Direction survives; **magnitude does not**. Selection favours the highest-attack control (r = −0.97), judge re-run spread reaches 18 rows, effect absent in `dev` |
| `C-004` | `R-003(b)`'s ρ figures | Quoted from the series *including* the query occurrence at 4 sampled layers; the demonstrations-only series over all 288 is the correct statistic. |
| `C-002` | "The `basket` replication is partly an illusion" | Measured exactly: cells `A` and `C` are **0.000** byte-identical across lexical banks. Only `B`/`E` share behavioral rows, and those are the cells with no codeword. `TSC-R-004` stands. |
| *inherited* | `d_surface` as validated, or as a GCG/MAC objective | Still **BLOCKED**. `R-012` closes the door for the new representation too. |

## NOVELTY — what is ours and what is not

`reports/DCS_LITERATURE_MATRIX.md`. ⛔ **The representation-convergence phenomenon is
Yona et al., "In-Context Representation Hijacking", ACL 2026 (arXiv 2512.03771)** — logit lens and
Patchscopes over 29 harmful requests. `R-001`/`R-010`'s *representational* half is a **replication
with a different instrument**, never a discovery, and their Appendix D (varying the codeword, ASR
flat) partly anticipates `R-002`. **What they have no version of is any internal causal
intervention** — their only causal manipulation is at the prompt level. Method provenance for the
knockout is Geva et al. 2023 (arXiv 2304.14767) and Ben-Tov, Geva & Sharif (TACL 2026).
"Representation ≠ behavior" is a 2026 consensus (Walsh & Barkett arXiv 2605.25151; Yin, Han & Li
ICML 2026), novel here only **as an instance**.
⇒ **The defensible novelty is the causal combination**: demonstration-block knockout **+** a
preregistered `intervention × condition` interaction with dose-matched controls **+** a *capable*
cross-family null **+** a CI-backed negative for a mechanistically derived attack objective.

## SCOPE — the line that accompanies every number

**38 domains × 2 codewords × 1 concept (`bomb`) × one layer band per model × one dose.**
✅ **The full installation swing is now measured against a genuine no-mapping cell (`R-050`).**
`benign_literal` — codeword present, remapping absent, same 38 domains — sits at **−5.495** against cell C
baseline's **+5.188**, so the doublespeak demonstrations move the reading **+10.68 log-odds**. ⚠ Every other
number in this phase measures *removal* of an installed mapping; this is the only measurement of *installation*.
⛔ **And it carries a readout limit that now applies phase-wide:** `option_mass` collapses **0.877 → 0.264**
when the mapping is absent ⇒ the forced-choice options only capture the model's answer **when a remapping is
installed**, so on any weakly-mapped population `semantic_logodds` contrasts two options the model largely
rejects. ⚠ Report `option_mass` beside it. (`R-032`'s mass-invariance point, now quantified at the extreme.)

⚠ **The installation gradient (`R-041`/`R-043`) has its own scope and it is narrower**: one bank, one codeword pair,
two doses of the *same* 38 domains — a second **dose**, not a second **sample**, so the two contrasts are ⛔ **not**
two independent p-values. Only the **graded** half is tested anywhere; the low-vs-high split is `CANNOT_ANSWER` on
every population with a control.
⚠ The **mechanism** (`KO-3`) is now measured on **two model families** — Llama-3.1-8B-Instruct
(L6–14) and Qwen3-14B (L7–17, same relative depth) — and replicates on both. The **behavioral**
half remains **Llama-only**. That is 38 *contexts for a single mapping*, **not** 38 mappings. Measured
ICC ≈ 0.34, so domain is the correct independence unit.

## OPEN QUESTIONS

0a. ⚠ **ANSWERED — `CONFOUND-LIMITED` (`R-048`).** All 8 Qwen arms judged in one invocation, 380 rows each.
   Face value gives `KO-3 − control` = **+23…+45**, significant on **all six** draws; the refusal adjustment gives
   **−11…−32**. ⛔ **All six brackets straddle zero and 0 of 6 directional claims survive** ⇒ `PR-014`'s second
   declared branch verbatim. ⛔ Forbidden in **both** directions: *"`KO-3` increases attack on Qwen"* is the face
   value and is exactly what the confound predicts (`KO-3` refuses **0**, controls ~200) — note it is the **opposite
   sign to Llama** (`R-016`), which is why it may not be reported before the confound is excluded; *"`KO-3` reduces
   attack"* is the adjusted end, significant on 2 of 6; and *"Qwen shows no behavioral effect"* remains forbidden
   because a straddling bracket is **undetermined**, not null. ⇒ `R-029` is **superseded, not vindicated**: the
   contrast has now been computed on all six draws with no comparator selection, and the statement moves from
   *"never measured"* to *"measured, and the confound is larger than the effect it would have to survive."*
   ✅ **The noise floor is now measured and does not rescue it (`R-049`).** One arm re-judged at byte-identical
   settings in a fresh invocation flips **18 of 380** attack labels (net **+6**) — order **±6–8** on McNemar's
   `ko_only − ctrl_only`, against observed deltas of **+23…+45**, a **3–6×** margin. ⇒ ⛔ Both of `R-048`'s ends
   are **real signals that disagree**; the limitation is the **confound**, not judge noise. ✅ And **`refused`
   flipped 0 of 380**, so `C-023` holds on new data and `R-048`'s bounding construction — which counts induced
   refusals — rests on a verified-deterministic quantity.
0b. ⛔ **Is the installation gradient CAUSAL?** `R-041`/`R-043` are correlational across domains. `PR-018`'s attempt
   to manipulate installation failed for lack of headroom (`R-042`: 0.908 at n=4, 25/38 domains at ceiling), and
   `cds38` carries no **low-dose** block — `{cds_n4, cds_n8}` is the whole block set. ⇒ Answering it needs a new
   `n_examples ∈ {1,2}` block, i.e. **bank construction and a separate preregistration**, not a re-run.
0c. ⛔ **The Qwen behavioral interaction is BLOCKED BY ITS OWN CRITERION** (`R-028`). 0 of 4
   completed draws qualify as refusal-neutral (+39, +47, +67, +56 against a ±17 band). The band is
   an **absolute** judge-noise figure used as a **relative** qualification rule: Qwen's controls
   perturb refusal by **26–45 %** of a 150 baseline and are rejected, while Llama's *rejected*
   draws perturbed **76–124 %** of a 42 baseline. ⇒ A 0/6 outcome is a limitation of the
   **criterion**, ⛔ never "Qwen shows no behavioral effect".
0. ⛔ **THE PHASE'S TOP OPEN EXPERIMENT (`DCS-PR-005`): what is the MAGNITUDE?** Direction is
   established across **four independent judgings** (`R-016`, `R-017`). The size is ≈ **−30** with a
   measured within-batch noise floor of **±7**, but remains inflated by a selection criterion that
   provably favours the highest-attack control (r = −0.97). ⚠ The `dev`/`heldout` objection was
   tested directly and is **not established** (`C-017`, permutation p = 0.14 / 0.23). What is still
   open: a **second refusal-neutral draw** to break the selection dependence, and an endpoint that
   is not 91 % off-goal.
1. ✅ **ANSWERED (`R-021`/`R-022`).** Neither the codeword row nor the readout row carries the
   mapping (both null at K=1); a threshold set of 3–8 query rows does, after which it saturates.
   ⚠ Row count and dose rise together by construction, so "≥8 rows" and "≥16 704 cells" are the
   same observation — the ladder separates *graded from step*, not rows from cells.
2. **Where do the 75 rows go?** `KO-3` eliminates refusal without buying attack success. What that
   text *is* has not been characterised.
3. **Does `R-010` hold on a second concept?** Not run. ✅ **On Qwen3 it does** (`R-024`) — the
   mechanism replicates cross-family at ~3× the magnitude, which makes the standing dissociation
   sharper: **the mechanism is cross-model; only its link to behavior is model-specific**
   (`TSC-R-005` is a capable null on Qwen's *attack* endpoint). ⛔ Not yet a formal interaction —
   that needs Qwen behavioral arms at this scope.
4. **Is the `basket` ceiling the reason "opposite directions" failed?** Untested.

## THE REFUSAL/ATTACK GAP — replicated on a second model, judge-free

✅ **`R-048`: `KO-3` removes ALL 150 Qwen refusals and buys only +21 attacks** (74 → 95). ⇒ **86 % of the removed
refusals did not become attacks.** ⚠ This is the Qwen counterpart of open question 2 on Llama (*"`KO-3` eliminates
refusal without buying attack success — where do the rows go?"*), now seen on **two model families**, at 150-row
scale, and it requires **no between-arm judge comparison** to state — only a baseline-vs-`KO-3` count within one
invocation. ⛔ It does **not** rescue the directional contrast, which stays `CONFOUND-LIMITED`.

## KNOWN DEFECTS

* `DCS-B-007`: per-row control-draw **positions** are not persisted, so control/demonstration
  disjointness is a **code guarantee, not an artifact fact**.
* `DCS-B-006`: after `KO-3` the two cells are not in comparable measurement regimes (cell `C` leaves
  the option set on 257/380 rows). The defense — the dose-matched control on the *same* prompts
  keeps mass at 0.798 — is strong but **must be argued in the text**.
* `DCS-B-003`: the L18 transplant result is neither retracted nor re-affirmed; **not citable**.
* `DCS-B-014` → ✅ **CLOSED by `R-049`**: judge nondeterminism on the **attack** rubric is now measured —
  **18 / 380** labels, net **+6**, `refused` **0 / 380**. ⛔ Scope: *same arm, same configuration, second
  invocation*, so it is an **upper bound** containing cross-invocation drift, measured on **one** arm — not "the
  judge's intrinsic noise".
* `DCS-B-013`: ⛔ the per-row **control match ratio is not persisted**, although the artifact's own
  `control_draw_note` states that *"every row carries its own ratio in `control_draw_match_ratio`"*. Only the
  aggregate survives, in `metadata.json`. ⚠ It blocked `PR-018a`'s declared secondary; recovered from
  `hook_n_keys_masked` (control ÷ knockout per `prompt_id`), and the recovery was **validated against the metadata
  count before use** — but the workaround assumes the two arms are row-aligned, which is not true in general.
* `DCS-B-009` → ⚠ **RUN AND NOT RESOLVED (`R-061`)**, and the limit has moved. 78 new domains took
  `k` from 38 to **116** at a measured cost of ~13.5 GPU-h. The declared conjunction (significance
  against **all three** dose-matched controls) came back **1 of 3**: p = 0.175 / **0.0096** / 0.466.
  ⛔ The `d2` value may not be quoted alone. ⚠ Realised ICC **0.089–0.112** (better than the 0.158
  assumed) but realised base rate **0.32** (not `R-016`'s 0.403) ⇒ recomputed power **0.65 / 0.35 /
  0.05**, which is exactly the observed pattern. ⇒ ⛔ **Domain count was not the binding constraint.**
  The controls induce refusal loads of **+35 / +133 / +200**, and the **between-control spread
  (0.0586) exceeds the effect (0.0391)** — the comparator draw matters more than the intervention.
  ⛔ **`PR-014`'s bracket is wrong at BOTH ends** (`R-062`, `R-063`). Its adjusted end assumes every
  induced refusal is a would-be attack (conversion **1.000**) against a measured **0.057–0.350**, so
  it **over-credits the control by 3–17×**; its face end **fails to debit `KO-3`** for clearing all
  **144** baseline refusals, which by the same mechanism gifted it attacks. ✅ Applying the measured
  conversion **symmetrically to both arms** gives **[−147, −66] / [−140, −87] / [−129, −29]** —
  entirely negative for all three, and **half the width**. ⚠ On `d3` the face value (**−9**) lies
  **outside** that interval, so "nearer the face value" would be wrong too. `PR-024a` binds the
  verdict to the primary in any case. ⇒ **More domains will not fix this; controls matched on induced
  refusal would**, and `C-023` showed those cannot be selected post hoc.
* `DCS-B-009` (original statement, superseded above): ⛔ **the behavioral design is underpowered at its own independence unit.** 38 domains
  cannot resolve a ~20 % relative effect by a clustered sign test (`k_inf` 36, floor 2.9e-11 — a
  true underpowering, not a floor limitation). **38 is the maximum that exists** in any
  demonstration-pool file in the repo; the other 38-domain files are the *same* 38 under different
  lexical pairs. Resolving it requires **generating new pools**, a new-data task for a separate
  preregistration.

## VERIFICATION

**Three** headline findings each carry an independent adversarial audit (`DCS-A-001`, `DCS-A-002`,
`DCS-A-004`). All three reproduced every published *number* to the digit; ⚠ the third nonetheless
**falsified two published claims** (`C-016a`, `C-016b`) and halved a third — reproducing the
arithmetic is not the same as confirming the sentences around it. The
`run_completeness_check` pre-commit guard **refused two commits** during the phase (377-vs-380 rows,
then non-uniform domain loss); ⛔ `--no-verify` was never used. All 9 deliverable guards and 341
guard tests pass at every commit. Three bugs were caught **before** they produced a result: a
position resolver that returned an empty span on 1032/1032 real rows, a pre-flight that declared the
new scope universally dead, and `CDS-R-020` reproduced exactly (ledgered in a baseline arm, fatal in
an intervened one).

## ARTIFACT AVAILABILITY

⚠ **Read this before treating any number above as recomputable.** For most of the phase **none** of
its outputs were in version control — `.gitignore` carries a bare `outputs/`, so `git status` cannot
list them and their absence was invisible (`DCS-031`). **0 of 674** artifact files were tracked, while
**1166** from earlier sprints were.

**In the repo now.** Every run's `config.json`, `RUNMETA.json`, `metadata.json`, `summary.json` and
`DONE.json` (**503 files, 5.0M**), the analysis outputs this report cites (`dcs_geom_all.json`,
`dcs_geom_button_bomb.json`, `dcs_ko1_ko2_did.json`, `audit.json`, `attrition.json`), and — added in
`C-021` — the **argsfile for every submission**, including the full layer sweep behind the graded-layer
finding. So the **exact command and configuration** behind every number here is retrievable.

⛔ **Not in the repo, deliberately.** `results.jsonl` (**49M**), `gens.jsonl` (**24M**) and
`dcs_rowwise_*.json` (**136M**). This follows the repo's own stated rule — `.gitignore:19` omits large
artifacts as *"reproducible from the run config"* — but it has a consequence worth stating plainly
rather than leaving to be discovered:

> Phase headlines are **reproducible by rerunning** the committed configs on GPU. They are **not
> recomputable from the repository alone.** `results.jsonl` is what the DiD scripts read, and it is
> not here.

Whether to track it is `B-013` — a shared-tree footprint decision (it would nearly double tracked
outputs), pending, and **not** a scientific judgement to be made unilaterally.
