# HERETIC × Causal Semantic Installation — INTERIM final report (v2)

**Status:** INTERIM v2 (2026-10-15). Supersedes v1 (`HERETIC_CSI_FINAL_REPORT_INTERIM.md`, kept unmodified) by applying every item of adversarial review #9 (`REVIEW_ADVERSARIAL_20261015_i.md`) and log entries through S-200. P4 evaluation and P6 rescue are **PENDING**; nothing below anticipates them.
**Source of truth:** `external_md/HERETIC_CAUSAL_SEMANTIC_INSTALLATION_PLAN_AND_PROGRESS_20261001.md` (S-entries cited;
later entries and CORRECTIONS supersede earlier ones). Mandate: `external_md/HERETIC_CSI_SPRINT_MANDATE_VERBATIM.md`.
**Pins:** Heretic `662e4ba2…`; Llama-3.1-8B-Instruct rev `0e9e39f2…`, bf16, eager; domain split seed 202609061
(70 TRAIN domains in the file; 3 whole domains advance-excluded ⇒ **67 effective TRAIN**; 23 VAL; TEST never used). Registry: `reports/heretic_csi/EXPERIMENT_REGISTRY_v2.json`.

Evidence labels: **CONFIRMED** (preregistered, held-out, corrected, independently verified) · **PASS** (preregistered
test passed; caveats stated) · **DESCRIPTIVE** · **VOID** · **CANNOT ANSWER** · **PENDING** · **WITHDRAWN**.

---

## Answers to the §28.2 questions

### 1. What parts of Heretic were useful?
- **Plugin/infrastructure ideas, audited from source (S-002, §9):** ARA's preserve/steer/overcorrect objective over module
  I/O, LoRA operator ΔW = B·A on `o_proj`/`down_proj`, Optuna multi-objective TPE with JournalStorage resume. ARA captures
  module I/O at the **last prefill position `[:, -1, :]`** (`model.py:665-666`) — confirmed; no per-position support.
- **What actually carried over to the headline P2b operator:** Heretic's ΔW = B·A parameterisation on
  `o_proj`/`down_proj`, its preserve/steer structure, and the surrounding infrastructure. The steer term was chosen by
  TRAIN-only CV among {kNN, MSE, cos, whiten}: **paired MSE (steer 0.3) won; ARA's own kNN-steer objective lost**
  (pooled held-out net 0.650 vs kNN 0.38; S-074). The headline operator therefore does *not* use ARA's objective.
- A clean-room reimplementation of the kNN-steer objective was built first (`operator_ara.py`, S-005/S-006) because the
  Heretic env could not be built under the disk quota at the time; native Heretic was then run as shipped in an
  isolated venv for P0 and Phase B (S-062, S-077).
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
cell C (−0.124 / −0.111; **basket's cell-C read is on a collapsed readout**, option mass 0.036 < 0.05) and transferred
across codewords (+0.995, not collapsed). The wrong-concept read is **also on collapsed readouts** (option mass
0.139 → 0.009) and carries no weight (S-077, S-083). **Scoped (S-083):** some specificity reads were on collapsed readouts and P(knife)/P(gun) also
rose, so the defensible wording is "a largely context-insensitive answer-position bias toward 'bomb', not
codeword-specific installation" — not "context-free".

### 3. Did position-aware ARA work? — **Partly (VAL, verified).**
The codeword-row-fit operator rescues far beyond random edits and localises its action to the codeword row; but position-aware *fitting* adds no magnitude, and
specificity against fitted controls is mostly absent (preregistered outcome D).
Weight operator ΔW = B·A on `o_proj` + `down_proj`, L6–18, fit on TRAIN at the per-example codeword row (KO→clean),
applied as a weight edit (S-074, S-135, S-156/S-157):
- Rescues semantic installation under the knockout far beyond random edits of equal rank and norm (CAND rank 1/62 vs
  RAND everywhere; VAL, verified S-157).
- Preregistered VAL outcome **D** (amendment 5): basket specific at r4 only (**PASS, marginal**: Holm 0.0488 at rank
  2/82, beaten by the same deranged control as on TRAIN, loses the pass in 9/23 leave-one-domain-out drops); button
  specific at neither r1 nor r4 (S-156/S-157).
- Most of the rescue is reproduced by **any operator fit to map KO→clean states**, regardless of domain pairing (fitted
  deranged controls rival it; S-136, S-157); correct pairing adds at most +0.018 [0.009, 0.028] (basket r4 only, VAL).
- **Not a constant shift (DESCRIPTIVE; NOT independently verified):** at matched injected norm, a constant
  TRAIN-mean-gap bias recovers only 0.32–0.63 vs CAND 1.20–1.73 (recovery is relative to KO_FULL, which itself restores
  only ~51–56% of the BASE−KO gap, S-136); CAND − MEANBIAS_NM = +0.12 to +0.20 (CI-lo > 0) in all 4 VAL cells (S-191). The
  full-norm mean-bias comparator collapsed the readout ⇒ VOID ⇒ "input-conditional" wording **SUSPENDED** (S-122, S-131).
- **Where it acts (DESCRIPTIVE, TRAIN):** the codeword-row-fit operator acts through the codeword row (codeword-row-only
  application ≈ full — loosely: the difference is ≠ 0 in 3/4 cells, S-136; last-row-only ≈ 0). An operator fit at the
  last row reaches comparable magnitude — on TRAIN the NEUT−CAND CI includes 0 in all cells, but on VAL basket r1 NEUT
  **exceeds** CAND by +0.040 [0.013, 0.067] (button r1 −0.020) — and only when applied at all rows (codeword-row-only
  or last-row-only < 10% of its effect); where NEUT acts is untested (S-136, S-140, S-157). Most robust basket weight-level result: **codeword-row-only application PASSES on
  VAL at r1 and r4 (1/77, Holm 0.026, LODO 23/23)** — secondary test with forking-path disclosure (S-069, S-157).

### 4. What rank was required?
- **Activation space (P2a, L18 rel-6, PLS family):** basket's rank-1 direction passes on VAL (1/57 at the
  56-control floor) but is **SUGGESTIVE, not confirmed** — never corrected for basket's own three VAL looks (Holm
  over {r1, r16, r4} ⇒ 0.0525; S-198); the S-199 powered re-test is preregistered and pending. It is **not**
  floor-sensitive: the corrected re-check gives 1/57 under every floor variant on VAL (strict paired 1/57 on 123 rows),
  while TRAIN is 2/57 BASE-ref (near-tie, Δ ≈ 1e-5) and 4/57 strict (S-200). **Button's rank-1 does not pass (VAL 14/57;
  TRAIN 23/57) while button's rank-4 subspace is CONFIRMED** — rank 1/201 vs 200 rank- and norm-matched
  controls, p = 0.004975, Holm over the 3 button VAL looks = 0.0149, beats every shuffled control, LODO 23/23,
  independently verified (S-125/S-126). **Small absolute effect:** recovery 0.091 [0.051, 0.124] of the whole-state
  rescue, candidate−KO 0.0129 [0.0065, 0.019], margin ≈ 1.1 control-SD — the claim is specificity, not magnitude.
  **Minimal specific rank for button is not identified** (∈ {2, 3, 4}; ranks 2–3 untested on VAL, rank 4 chosen on
  TRAIN). Rank 16: neither codeword specific (10/57 both; S-049).
- **Weight space (P2b):** rescue is **rank-flat** from r1 to r50 (0.70–0.82 of the BASE−KO gap for basket, 0.77–0.87 for
  button) while #params grows 50× (DESCRIPTIVE, TRAIN-K4, S-188). More rank adds no rescue.

### 5. Did basket and button differ?
- They differ in **whether a specific carrier is detected at rank 1** in activation space (basket yes — SUGGESTIVE;
  button no) and button has a CONFIRMED one at rank 4.
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
Against an anisotropic null, **0 of 924 alignment statistics** (66 per cell × 14 cells; min p 0.27) reach p ≤ 0.01
for the refusal direction, d_surface or the P2a probe axes; the null is conservative (detection needs |cos| ≳ 0.25–0.78), so the correct statement is "no alignment
detectable at the null's sensitivity" — H3 stays OPEN (S-089, S-097). The 8-head circuit's share of `o_proj` input-norm
is at the random level (S-079). The earlier "refusal@L16" claim was WITHDRAWN (S-083).

### 10. Did it generalize across codewords? — **PENDING.**
P6 Stage-0 (interim): of 21 prepared codewords (envelope excluded pre-GPU; carrot excluded), G3 (rescue-population
option mass) FAILS for candle (0.0481 [0.037, 0.063], borderline) and PASSES for 14 so far; G1 passes for all G3
passers checked; G2 (KO liveness) PASSES for lamp, kettle, pencil, ladder; others pending (S-146, S-167, S-168, S-178,
S-187). The confirmatory test (H6a, intersection-union over control families) is not yet run. **n = 15 is the ceiling**
(20 untouched − 5 DEV); H6a is pre-labelled UNDERPOWERED for ρ < 0.8 if fewer than 15 confirmation codewords survive and
CANNOT ANSWER if fewer than 12 — **one more gate failure triggers the former** (S-112, S-180). Blanket is a BORDERLINE
G3 pass (0.056 [0.039, 0.066]). Power is tight (n=15 ⇒ 0.57–0.72 at ρ = 0.7). Gate attrition and the declared non-independence of codewords (identical random
controls; r1 axes |cos| 0.33–0.75; shared VAL domains) are recorded in PREREG_P6 amendments 5 (S-168) and 6 (S-181).

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
| H1 — the basket/button dissociation is a **dimensionality** requirement | **Not supported in either family.** Activation space: button passes at r4 and not at r1; basket passes at r1 (SUGGESTIVE); ranks 2–3 untested on VAL; no supported interaction (S-097/098). Weight space: the preregistered VAL outcome is **D**, which plan §3 maps to "H1 falsified for button" — scoped: under amendment 5, D means no button-specific operator vs **fitted** controls at r ∈ {1,4}, not resistance to rescue (CAND still ranks 1/62 vs random edits). The descriptive TRAIN curve shows no rank dependence to r = 50 (S-188). ⇒ falsification is restricted to the weight-operator family at r ∈ {1,4}. |
| H2 — the learned operator's subspace overlaps the independently found head/layer circuit | **OPEN (P4 eval PENDING).** 8-head share of `o_proj` input norm is at the random level (S-079); fit-side TOP8 is not distinctive vs random 8-head sets (S-100/S-113, in-sample, not an endpoint); counter-observation: ΔW norm peaks at L6–7 and L17–18, partly coinciding with circuit layers L6/L18 (descriptive, S-079). |
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
   Its rank-1 direction does not (VAL 14/57). **Small absolute effect:** recovery 0.091 [0.051, 0.124] of the
   whole-state rescue; candidate−KO 0.0129 [0.0065, 0.019]; margin ≈ 1.1 control-SD — specificity, not magnitude
   (S-072/S-126).
2. **Basket has a rank-1 carrier on VAL — SUGGESTIVE, not confirmed** (1/57, p = 0.0175 = the 56-control floor;
   TRAIN 2/57, a near-tie passing only under AM-48). It is **robust to the option-mass floor** (1/57 under every floor
   variant on VAL; S-200 corrected S-052's "2/57 under the strict floor", now WITHDRAWN), but it is **not corrected for
   basket's own VAL looks** {r1, r16, r4} (Holm 0.0525), unlike button r4. Mitigating (descriptive): its specificity z
   is 3.9–8.7 in every control family (S-098). The powered re-test (PR-HCSI-S199, preregistered) is pending
   (S-049, S-198, S-199, S-200).
3. **Neither codeword is specific at rank 16** (10/57 both; S-049).
4. **A learned low-rank weight operator rescues installation far beyond random edits of equal rank and norm, and acts
   through the codeword row** (VAL, verified). For basket, codeword-row-only application beats 76 codeword-row controls
   including fitted deranged-pairing fits (Holm 0.026, LODO 23/23) — secondary test, forking-path disclosed (S-157).
5. **Most of the weight-level rescue is generic:** any operator fit to map KO→clean states reproduces it; correct domain
   pairing adds at most +0.018 [0.009, 0.028] (basket r4, VAL) (S-136, S-157).
6. **It is not a constant shift:** at matched injected norm a mean-gap bias recovers 0.32–0.63 vs CAND 1.20–1.73,
   CAND − MEANBIAS_NM > 0 in all four VAL cells (DESCRIPTIVE, S-191; **not independently verified**).
7. **Native last-position ARA is not sufficient for codeword-specific installation** (MEASURED control, S-077/S-083).
8. **C1 ("better probe") is not supported held-out** (S-054, S-065).
9. **Heretic upstream findings** (reset keeps `lora_A`; deployed ≠ optimized under `preserve_row_magnitudes`; resume
   re-draws trial 0). Only the `lora_A` reset finding was **independently** confirmed in source (review #1,
   `model.py:313`, S-065); the other two were confirmed by the implementer (S-062/S-077).
10. **P7's primary is CANNOT ANSWER / UNDERPOWERED**, declared before any GPU spend (S-193).

## WHAT WE MUST NOT SAY

- "Basket's rank-1 carrier is CONFIRMED / certified / cross-hardware" — SUGGESTIVE: floor-limited (p sits at the
  56-control floor) and uncorrected over basket's 3 VAL looks (Holm 0.0525); TRAIN was 2/57 (S-198, S-200).
- "Basket r1 is option-mass-floor-sensitive" — WITHDRAWN: it is 1/57 under every floor variant on VAL (S-200).
- "The P2b operator uses ARA's objective" — it uses ARA's operator form with an MSE steer chosen by TRAIN CV (S-074).
- "Button requires (exactly) 4 dimensions" — it passes at r4 and not at r1; ranks 2–3 are untested on VAL and r4 was
  chosen on TRAIN (S-073, S-198).
- "The operator overshoots the rescue" — recovery is relative to KO_FULL, which restores only ~51–56% of the BASE−KO
  gap; quote the gap fraction (S-136).
- Any outcome letter (A–E) read off TRAIN — outcomes are decided on VALIDATION only (amendment 5, S-136).
- "Large effect" for button r4 — recovery 0.091 of whole-state rescue (S-073).
- "Button r1 fails at 18/57" — the corrected count is 14/57 on VAL (23/57 TRAIN) (S-200).
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

---

## Known inconsistencies and caveats (listed, not silently resolved)

From the F9 compilation (log S-196) plus review #9 (S-198) and the paired-floor re-check (S-200):

1. **Registry entry for Phase B** pointed at a directory (`configs/heretic_csi/phaseB`) with no hash. v2 points at the
   five per-config `MANIFEST.json` files instead.
2. **S-entry sub-numbering is uneven** (some ticks have `b`/`c`/`d` sub-entries, most have none) and a few header times
   in the clock-corrected window are not monotone with their commit times (S-169, S-182 note this). Content is
   unaffected.
3. **Two "incumbent basket" liveness baselines circulate:** TRAIN (KO−BASE −0.235 / FULL−KO +0.124) and VAL
   (−0.30 / +0.14). S-180 corrected S-178 to the TRAIN pair for TRAIN comparisons; the superseded numbers remain
   visible in S-178 because the log is append-only. Quote the split-matched pair.
4. **Common-row counts differ by codeword**: P2a K4 TRAIN 179 (basket) vs 239 (button); VAL 133–145 vs 193–203. This is
   the declared option-mass attrition (basket's bank has more degraded rows, inherited caveat) and matters for any
   cross-codeword comparison of absolute effect sizes.
5. **Early reduced-sweep artifacts share the production prefix**: `hcsi_p2a_basket_r4.json` and `_r32.json` (S-013 era;
   14 common rows, 8 controls) are **not** production results. The figures index now lists production files explicitly
   instead of globbing.
6. **Two verification reports are superseded for rank-1 cells.** `VERIFY_S049_independent.*` and
   `VERIFY_S072_r4_validation.*` averaged each arm over its own surviving rows rather than the keys common to all arms;
   `VERIFY_PAIRED_FLOOR_RECHECK.*` (S-200) supersedes them for basket r1 and button r1. Their other cells stand.
7. **The v1 report was written in two passes** (its first write was truncated mid-Q10); v2 is a single patched file.
8. **Provenance gaps disclosed in the log** (not re-litigated here): two P6 jobs called repo scripts that were
   committed only afterwards (S-181; outputs re-validated or the jobs were preempted before producing results), and two
   preregistrations were committed shortly after their job was submitted (S-158/S-167 erratum, S-198) — in both cases no
   endpoint existed at commit time.
