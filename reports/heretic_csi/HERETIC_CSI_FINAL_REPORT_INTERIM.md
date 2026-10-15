# HERETIC × Causal Semantic Installation — INTERIM final report

**Status:** INTERIM (2026-10-15). P4 evaluation and P6 rescue are **PENDING**; nothing below anticipates them.
**Source of truth:** `external_md/HERETIC_CAUSAL_SEMANTIC_INSTALLATION_PLAN_AND_PROGRESS_20261001.md` (S-entries cited;
later entries and CORRECTIONS supersede earlier ones). Mandate: `external_md/HERETIC_CSI_SPRINT_MANDATE_VERBATIM.md`.
**Pins:** Heretic `662e4ba2…`; Llama-3.1-8B-Instruct rev `0e9e39f2…`, bf16, eager; domain split seed 202609061
(67 TRAIN / 23 VAL domains; TEST never used). Registry: `reports/heretic_csi/EXPERIMENT_REGISTRY.json`.

Evidence labels: **CONFIRMED** (preregistered, held-out, corrected, independently verified) · **PASS** (preregistered
test passed; caveats stated) · **DESCRIPTIVE** · **VOID** · **CANNOT ANSWER** · **PENDING** · **WITHDRAWN**.

---

## Answers to the §28.2 questions

### 1. What parts of Heretic were useful?
- **Plugin/infrastructure ideas, audited from source (S-002, §9):** ARA's preserve/steer/overcorrect objective over module
  I/O, LoRA operator ΔW = B·A on `o_proj`/`down_proj`, Optuna multi-objective TPE with JournalStorage resume. ARA captures
  module I/O at the **last prefill position `[:, -1, :]`** (`model.py:665-666`) — confirmed; no per-position support.
- The headline operator experiments used a **clean-room reimplementation** of ARA's objective in the frozen CSI stack
  (S-005/S-006), because the Heretic env could not be built under the quota at the time; native Heretic was then run
  as shipped in an isolated venv for P0 and Phase B (S-062, S-077).
- **Upstream findings about Heretic itself (P0 Phase A, S-062/S-077):**
  - `reset_model` zeroes only `lora_B`; `lora_A` keeps the previous trial's values ⇒ re-applying identical params after a
    reset gave ΔW rel diff 1.08, max |Δlogit| 4.2; Optuna trial-0 value 0.0706 vs replay 0.0513 ⇒ shipped trials are
    history-dependent / not exactly replayable. Restoring `lora_A` makes replay bit-exact.
  - With the default `preserve_row_magnitudes=True`, ARA's loss uses `normalize(W+BA)·‖W‖_row` but PEFT deploys `W+BA`
    (per-module relative gap 1–30%, max 0.298).
  - Resuming a study re-draws trial 0's exact parameters (re-seeded TPE).
  - Reset to identity itself is exact (ΔW = 0; greedy-16 identical to base).
  - Not reported upstream (outward-facing; user's decision).

### 2. Did native ARA work? — **No (MEASURED control; scoped).**
Native last-position ARA (Heretic objective as shipped; TRAIN-tuned, VAL read once) raised y_install on VAL not-installed
cell A by +0.925 (basket) / +0.796 (button), rank 1/43 vs rank-matched controls (floor), but lowered it on installed
cell C (−0.124 / −0.111), transferred across codewords (+0.995), and pushed "bomb" in knife/gun contexts more than the
correct concept (S-077). **Scoped (S-083):** some specificity reads were on collapsed readouts and P(knife)/P(gun) also
rose, so the defensible wording is "a largely context-insensitive answer-position bias toward 'bomb', not
codeword-specific installation" — not "context-free".

### 3. Did position-aware ARA work? — **Yes for rescue magnitude; specificity is largely generic (VAL, verified).**
Weight operator ΔW = B·A on `o_proj` + `down_proj`, L6–18, fit on TRAIN at the per-example codeword row (KO→clean),
applied as a weight edit (S-074, S-135, S-156/S-157):
- Rescues semantic installation under the knockout far beyond random edits of equal rank and norm (CAND rank 1/62 vs
  RAND everywhere; VAL, verified S-157).
- Preregistered VAL outcome **D** (amendment 5): basket specific at r4 only (**PASS, marginal**: Holm 0.0488 at rank
  2/82, beaten by the same deranged control as on TRAIN, loses the pass in 9/23 leave-one-domain-out drops); button
  specific at neither r1 nor r4 (S-156/S-157).
- Most of the rescue is reproduced by **any operator fit to map KO→clean states**, regardless of domain pairing (fitted
  deranged controls rival it; S-136, S-157); correct pairing adds at most +0.018 [0.009, 0.028] (basket r4 only, VAL).
- **Not a constant shift (DESCRIPTIVE):** at matched injected norm, a constant TRAIN-mean-gap bias recovers only
  0.32–0.63 vs CAND 1.20–1.73; CAND − MEANBIAS_NM = +0.12 to +0.20 (CI-lo > 0) in all 4 VAL cells (S-191). The
  full-norm mean-bias comparator collapsed the readout ⇒ VOID ⇒ "input-conditional" wording **SUSPENDED** (S-122, S-131).
- **Where it acts (DESCRIPTIVE, TRAIN):** the codeword-row-fit operator acts through the codeword row (codeword-row-only
  application ≈ full; last-row-only ≈ 0); an operator fit at the last row reaches a statistically indistinguishable
  rescue only when applied at all rows (codeword-row-only or last-row-only < 10% of its effect) — where it acts is
  untested (S-136, S-140, S-157). Most robust basket weight-level result: **codeword-row-only application PASSES on
  VAL at r1 and r4 (1/77, Holm 0.026, LODO 23/23)** — secondary test with forking-path disclosure (S-069, S-157).

### 4. What rank was required?
- **Activation space (P2a, L18 rel-6, PLS family):** basket's rank-1 direction passes on VAL (1/57, p 0.0175;
  floor-sensitive, S-052); **button's rank-1 fails (VAL 14/57) but button's rank-4 subspace is CONFIRMED** — rank 1/201
  vs 200 rank- and norm-matched controls, p = 0.004975, Holm over the 3 button VAL looks = 0.0149, beats every shuffled
  control, LODO 23/23, independently verified (S-125/S-126). Rank 16: neither codeword specific (10/57 both; S-049).
- **Weight space (P2b):** rescue is **rank-flat** from r1 to r50 (0.70–0.82 of the BASE−KO gap for basket, 0.77–0.87 for
  button) while #params grows 50× (DESCRIPTIVE, TRAIN-K4, S-188). More rank adds no rescue.

### 5. Did basket and button differ?
- They differ in **whether a specific carrier exists at rank 1** in activation space (basket yes, button no) and button
  has one by rank 4 (CONFIRMED components above).
- A **basket-vs-button contrast** ("button gains specificity r1→r4 more than basket") is **NOT supported**: the S-085
  estimate was WITHDRAWN (row-set bug) and the corrected interaction's sign depends on the control family (RAND −1.05,
  SHUF +2.96, pooled +6.09; S-097/S-098).
- The inherited explanation "basket simply has a better probe" (C1) is **not supported held-out** (rank-1 probe
  Spearman basket 0.533 [0.434, 0.631] vs button 0.574 [0.497, 0.653]); a decodability difference is CANNOT ANSWER
  (S-054, S-065).
- Weight-operator test (P2b, outcome D) does not detect a button-specific carrier under its stricter fitted-control
  null; this neither confirms nor contradicts P2a (S-157: families not comparable).

### 6. Which layers/components mattered? — **DESCRIPTIVE.**
P3 SVD of the learned operators: `o_proj` holds 59–79% of ‖ΔW‖²; norm concentrates in layers 6–7 and 17–18; effective
(energy-entropy) rank ≈ 1 at r1, ≈ 2 at r4, ≈ 4.8 at r8/r16; ‖ΔW‖/‖W‖ median 2–6% (S-079, S-089). Layer/component
causal necessity was not tested.

### 7. Did head restriction preserve the effect? — **PENDING.**
Fit-side only so far (not an endpoint): at their own optimum and at TOP8's norm, random disjoint 8-head sets fit as
well as the inherited 8-head set (TOP8 not distinctive in any cell); FULLO/MLP-only fit more of the gap but with more
parameters, lower norm and different modules — not like-for-like (S-100, S-113). Evaluation preregistered (PREREG_P4 +
amendments 1–4) and not yet run.

### 8. What did the learned SVD/subspace look like? — **DESCRIPTIVE; truncation VOID.**
At low rank the candidate and every fitted control write along the same per-module direction — the mean KO→clean output
gap (|cos| ≈ 1.00), true largely by construction; basket and button gaps overlap strongly at L6–14 (|cos| 0.84–0.94),
less at L18 (0.50); r1 write subspaces overlap (median cos² 0.76) (S-079, S-089, S-097). The truncation/removal test
(minimal sufficient subspace) is **VOID** — its preregistered reproduction check failed (S-176); its numbers are not
quotable and the "rank-1-dominated" reading was struck (S-180).

### 9. Did it align with our existing causal circuit? — **No detectable alignment (DESCRIPTIVE).**
Against an anisotropic null, 0 of 66 alignment statistics reach p ≤ 0.01 for refusal direction, d_surface, or the P2a
probe axes; the null is conservative (detection needs |cos| ≳ 0.25–0.78), so the correct statement is "no alignment
detectable at the null's sensitivity" — H3 stays OPEN (S-089, S-097). The 8-head circuit's share of `o_proj` input-norm
is at the random level (S-079). The earlier "refusal@L16" claim was WITHDRAWN (S-083).

### 10. Did it generalize across codewords? — **PENDING.**
P6 Stage-0 (interim): of 21 prepared codewords (envelope excluded pre-GPU; carrot excluded), G3 (rescue-population
option mass) FAILS for candle (0.0481 [0.037, 0.063], borderline) and PASSES for 14 so far; G1 passes for all G3
passers checked; G2 (KO liveness) PASSES for lamp, kettle, pencil, ladder; others pending (S-146, S-167, S-168, S-178,
S-187). The confirmatory test (H6a, intersection-union over control families) is not yet run; power is tight (n=15 ⇒
0.57–0.72 at ρ = 0.7). Gate attrition and the declared non-independence of codewords (identical random
controls; r1 axes |cos| 0.33–0.75; shared VAL domains) are recorded in PREREG_P6 amendments 5–6 (S-181).

### 11. Did semantics change without downstream behavior? — **CANNOT ANSWER (pre-declared, no GPU spent).**
P7 design (S-193): the one fully qualifying intervention (P2a button r4) moves installation by 6.0% of what the
knockout moves, and the knockout itself did not move the content-gated downstream endpoint (+0.0030 [−0.0299, +0.0358],
p = 0.844, inherited, 67 domains). VAL (23 domains) resolves 0.0907 at 80% power; the plausible effect is ≤ 0.0021
(≈ 42,900 domains needed). Per mandate §20 the primary is pre-labelled **CANNOT ANSWER / UNDERPOWERED** rather than run
and reported as a null. A descriptive secondary (refusal, button only — basket is at floor) remains optional
(≈18 GPU-h). Consistent with, and not an independent test of, the inherited representation/behavior dissociation.

### 12. Which hypotheses were killed or revised?
| Hypothesis | Outcome |
|---|---|
| H1 — the basket/button dissociation is a **dimensionality** requirement | **Not supported as a contrast.** Activation space: button needs r4 where basket passes at r1 (both CONFIRMED/PASS separately), but no supported interaction (S-097/098). Weight space: rescue rank-flat r1–50 (S-188). |
| H2 — the learned operator's subspace overlaps the independently found head/layer circuit | **Not supported so far.** No detectable alignment (S-089/S-097); 8-head share at random level (S-079); P4 eval PENDING. |
| H3 — the operator distils into an interpretable low-dim subspace better than d_surface | **OPEN.** No detectable alignment with d_surface/refusal/probe axes at the null's sensitivity; the truncation test that would have identified a minimal subspace is VOID (S-176/S-180). |
| C1 — "basket simply has a better probe" | **Not supported held-out** (S-054, S-065). |
| "Button has no specific carrier" (S-049 wording) | **Superseded** — button has one at r4 (S-073, S-126). |
| Native end-of-prompt ARA suffices for installation | **No** (S-077, scoped S-083). |
| "Position-aware fitting is necessary for the rescue magnitude" | **No** — a last-row fit reaches an indistinguishable magnitude; it differs in *where* the edit acts (S-140, corrected S-157). |

---

## WHAT WE CAN DEFEND

1. **Button has a specific rank-4 activation-space rescue carrier at L18 (CONFIRMED).** Preregistered, held-out (23 VAL
   domains, 203 shared rows), rank 1/201 vs 200 rank- and norm-matched controls, p = 0.004975, Holm over all three
   declared button VAL looks = 0.0149, beats every shuffled-label control, rank 1 in all 23 leave-one-domain-out drops,
   bit-exact overlap with the original job, independently recomputed (S-125, S-126; `VERIFY_S084_powered.md`).
   Its rank-1 direction does not (VAL 14/57).
2. **Basket has a rank-1 carrier on VAL** (1/57, p = 0.0175, cross-hardware), **floor-sensitive** under a stricter
   option-mass rule (S-049, S-052).
3. **Neither codeword is specific at rank 16** (10/57 both; S-049).
4. **A learned low-rank weight operator rescues installation far beyond random edits of equal rank and norm, and acts
   through the codeword row** (VAL, verified). For basket, codeword-row-only application beats 76 codeword-row controls
   including fitted deranged-pairing fits (Holm 0.026, LODO 23/23) — secondary test, forking-path disclosed (S-157).
5. **Most of the weight-level rescue is generic:** any operator fit to map KO→clean states reproduces it; correct domain
   pairing adds at most +0.018 [0.009, 0.028] (basket r4, VAL) (S-136, S-157).
6. **It is not a constant shift:** at matched injected norm a mean-gap bias recovers 0.32–0.63 vs CAND 1.20–1.73,
   CAND − MEANBIAS_NM > 0 in all four VAL cells (DESCRIPTIVE, S-191).
7. **Native last-position ARA is not sufficient for codeword-specific installation** (MEASURED control, S-077/S-083).
8. **C1 ("better probe") is not supported held-out** (S-054, S-065).
9. **Heretic upstream findings** (reset keeps `lora_A`; deployed ≠ optimized under `preserve_row_magnitudes`; resume
   re-draws trial 0), each confirmed from source (S-062, S-077).
10. **P7's primary is CANNOT ANSWER / UNDERPOWERED**, declared before any GPU spend (S-193).

## WHAT WE MUST NOT SAY

- "Button r4 is a fresh confirmation" — same VAL data with a larger null; rank 4 was chosen on TRAIN; the shuffled-label
  family is only n = 10; margin ≈ 1.1 control-SD (S-125, S-126).
- "The dissociation is a dimensionality difference" / any basket-vs-button specificity-gain contrast — S-085 WITHDRAWN;
  corrected interaction's sign is control-family dependent (S-097, S-098).
- "Basket has a robust rank-4 weight-level carrier" — marginal (Holm 0.0488, rank 2/82), not LODO-stable on VAL
  (9/23 drops lose it), fails under a row-level statistic and under raw-norm deranged controls (S-157).
- "The P2b operator is pairing-specific / input-conditional" — pairing adds ≤ +0.018 (basket r4 only); the
  input-conditional wording is SUSPENDED because the full-norm comparator collapsed (S-131, S-157).
- "P2a and P2b disagree about button" — the two tests are not comparable (sites, null families, effect sizes,
  multiplicity) (S-157).
- "The learned operator is effectively rank-1" / "the minimal sufficient subspace is k = 1 or 2" — the truncation read
  is VOID; its numbers are not quotable (S-176, S-180; `p3_basket_r4_validation.NOT_QUOTABLE.md`).
- "The operator does not align with refusal / d_surface" — only "no alignment detectable at the null's sensitivity";
  the earlier refusal@L16 claim was WITHDRAWN (S-083, S-089, S-097).
- "Native ARA produces a context-free bias" — context-insensitive on non-collapsed reads; scoped to the shipped
  objective (S-083).
- "Position-aware fitting is unnecessary" — magnitude is matched by a last-row fit, but where that fit acts is untested
  (S-157).
- Any statement about the downstream behavioural endpoint from this sprint (CANNOT ANSWER, S-193), any head-restriction
  result (PENDING), any cross-codeword population law (PENDING; 2 codewords only so far), or any use of the TEST split
  (never used).
- "Survivors" for codewords that have only passed G3 (G1/G2 may be undecided) (S-167).
