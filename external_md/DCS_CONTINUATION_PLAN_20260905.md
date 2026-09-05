# DCS — continuation plan (2026-09-05)

> Produced by a 14-agent adversarial synthesis over the DCS log: four independent surveys
> (established / retracted / open / methodological assets), six candidate claims put to
> refutation agents, then three independent design angles (mechanistic, statistical,
> scope-and-paper) merged and ranked. **2 of 6 verified claims survived unchanged; 4 were
> corrected** — those corrections are recorded as `C-046` in the main log and have been
> propagated to the summary, the figure and the collaborator draft.
>
> ⚠ This is a PLAN, not a result. Nothing here is preregistered; each item needs its own
> `PR-0xx` before it runs.

# Continuation Plan — DCS / Doublespeak Causality Phase
Date: 2026-09-04. Written against the sprint's terminal state (PR-028/R-075/R-076) and the post-verification claim set.

---

## 1. WHAT THIS SPRINT ESTABLISHED

### 1A. Representation level — STRONG, replicated, defensible now

**N1. The demonstration→query attention path is necessary for the codeword→concept remapping, and the necessity is remapping-specific.**
Llama-3.1-8B-Instruct, bank `cds38`, L6–14, forced-choice `semantic_logodds`, cell C:
- button↔bomb: +5.188 → −2.756; KO-3 − dose-matched control = **−8.081** (1+/37−); DiD vs cell B = **−9.889**, 1+/37−, p = 2.838e-10 (38-domain sign-test floor 7.276e-12).
- basket↔bomb: +6.794 → −3.803; KO-3 − control = **−10.782** (1+/37−); DiD = **−9.352**, 1+/37−, same p. n=377 under the declared PR-003 exclusion (drop-`school_campus` robustness −9.264, 1+/36−).
- Dose-matched controls are negligible in magnitude (|Δ| < 0.31) but **not sign-null** (C-011).

Scope limits that must travel with N1:
- The two p-values are **one sign pattern replicated twice**, not two independent tests.
- Specificity is a **magnitude** claim, not a sign claim: "the cells move in opposite directions" holds on button only (basket cell B moves −1.466, 5+/33−). A-002's argmax evidence (4→104 vs 21→6) is button-specific.
- Necessity is of the **path**, not the span: narrowed to the codeword/readout row the specificity DiD is a clean null (+0.503, 13/38).
- On Llama the post-KO state is **not** a restored literal reading: ` Bomb` 345→19 but ` Neither` = 67.1% of rows and option_mass 0.877→0.353 — cell C's post-intervention measurement regime differs from cell B's (R-032, B-006, Llama-specific).
- 38 domains = **38 contexts for one mapping**, ICC ≈ 0.34. Independence unit = domain.

**N2. The effect is a step, not a gradient, along the query span.**
K=1 −0.013, K=2 −0.012, K=8 **−6.616** (81.9% of full, 0+/38−, at the sign-test floor), K=16 −7.888 (97.6%), K=32 −8.081. Each rung read against its own dose-matched control; the control family is inert across the full 32× dose range (+5.16…+5.38 vs baseline +5.188).
Limits: threshold bracketed only between **3 and 8 rows** (rungs 3–7 never run); row count and cell count rise together, so "K≥8 rows" and "≥16,704 cells" are one observation. "No single row carries it" is a clean null for the readout row (KO-4, −0.013, p=0.256) but **not** for the final codeword row (KO-1: +0.363, p=0.034, 26+/12− — small and opposite in sign). Single model except the K=32 rung (Qwen, R-024).

**N3. Cross-family replication in DIRECTION only.**
Qwen3-14B, band 7–17 (inherited, never swept), `--enable-thinking false`, R-023 capability gate passed, same bank/codeword: C +10.140 → −13.080 (frac>0 0.813 → 0.021), control inert +10.357, KO-3 − control = −23.437 (1+/37−), specificity DiD −22.198 (cell B −1.238, 15+/23−, p=0.256), 6 arms × 380 rows.
**⛔ "~3× Llama's magnitude" is NOT claimable** (verification kill): mean-only cross-model ratio on a scale whose baseline already differs 2×, more bimodal distribution with lower frac>0, and unmatched dose (Qwen 91,872 cells / 11 layers vs Llama 66,816 / 9) on a quantity R-022 showed to be steeply dose-graded.

**N4. Depth profile: destructive effect throughout L0–14, largest at 10–14, no null band.**
Equal dose (37,120 keys/band by construction): 0–4 −3.385 (1+/37−), 5–9 −2.985 (1+/37−), 10–14 −5.647 (0+/38−), all Holm p ≤ 8.5e-10.
**⛔ "Absent above 14" is FALSE.** In R-030's separate coarse sweep (9L/8L, doses 66,816/59,392, **not dose-comparable**), 15–23 = +0.146 (Holm p=5.5e-02, non-significant) and 24–31 = **+0.754 with 38+/0− domains, Holm p=2.9e-11** — the most consistent sign pattern in the sweep. What is absent above 14 is the *destructive* effect. No between-band contrast was tested, so "peaks at 10–14" is descriptive; L6–14 contains the maximum but is not a mechanism boundary (0–5 contributes substantially). C-005 retracted the earlier L6–L12 readout peak: knockout profile and readout profile do not converge.

**N5. Installation is CATEGORICAL, not continuous, and the ceiling is a paradigm property** (78 independently authored domains reproduce it). Domain count was never the binding constraint (R-061).

**N6. Layer-specificity is PARTIAL.** On the `rbd` banks, `demo_all` moved to 15–23 is not inert: lantern +1.058 vs −7.760 (13.6%, opposite sign, 20-domain floor p=1.907e-06); candle +0.401 vs −2.333 (17.2%, p=4.025e-04). Corrections: the placebo ran at **n=8 only** (the n=16 rbd banks carry no 15–23 arm); only lantern sits at the floor; candle's 17.2% divides by a **non-significant** 6–14 effect (p=0.115), so it does not quantify a fraction of an established mechanism. ⛔ "Layers 15–23 are inert" may never be said without naming the bank.

### 1B. Behaviour level — NOT ESTABLISHED

**B1. The behavioural link is not established on Llama, and it is UNDERPOWERED, not a clean negative.**
PR-028: KO-3 vs a distribution of K=8 dose-matched control draws — Δ = **−0.0222, t(7) = −0.80, p = 0.449**. Realised between-control sd **0.0783** = 2.65× the 0.0295 the design was sized on. MDE 0.0655 > the −0.0391 sought. K≈24 powers −0.0391; the **observed** −0.0222 needs K≈105 (~240 GPU-h + ~$26).

**B2. THE KEY DISCOVERY — dose-matched controls are not an exchangeable population.**
At *identical* dose (`keys_masked` 522, `match_ratio` 1.000, verified on all 8 draws), induced refusal spans **−7 to +562** (25-fold) and ASR spans **0.126–0.374**. WHICH positions are masked dominates behaviour at constant dose. R-075 verified the extreme arm has no defect. Ordering arms by induced refusal against ASR is close to monotone.

**B3. There is no predictor to match on.** R-076: mask geometry (7 index-summary features) fails within arms (k=8, 0/4 consistent) and between them (best rho 0.238, n=8).

**B4. Judge-session drift is NOT ESTABLISHED** (R-074, arm-level t(4)=−1.69, p=0.166, CI spans zero) — but the judge flips **12.6%** of labels on byte-identical text, with **0** refusal flips in 5,800 re-judged rows (C-023). Refusal is a judge-free endpoint; ASR is not.

**B5. Benign remapping is detectable but weak and is not a symmetric counterpart.** R-050: benign mapping in 25/380 rows (6.6%), against ` Neither` 186 and ` Button` 140 — no remapping installed in ~86% of rows, option_mass 0.877→0.264, `semantic_logodds` −5.495. Registered primary returned CANNOT ANSWER (1/38 vs a gate of 4); the Mushroom finding is an unregistered post-hoc read of an arm preregistered as the *no-mapping* reference. ⛔ "The paradigm installs whatever the demonstrations say" is not claimable as a symmetric statement.

**B6. Concept non-specificity is not a specificity control.** R-002 runs on the x2fit banks (30 families/cell, not cds38/38 domains), `cell_means` are pre-aggregated so there is **no test statistic**, and each concept is a separate bank with its own B anchor — the log itself calls it "a replication across concepts, NOT a specificity control". Of six bomb-vs-other comparisons, four run the other way, one ties, one runs as predicted; all |Δ| ≤ 0.035, above the band's median 0.0151/mean 0.0203 and below only its p90 0.0443. All comparators (knife/gun/club) are themselves harmful concepts.

---

## 2. WHAT IT RULED OUT — closed routes, do not re-propose

1. **More demonstration domains.** R-061: domain count was never the binding constraint on the behavioural endpoint.
2. **Lowering dose to escape the installation ceiling.** The ceiling is a paradigm property (78 domains).
3. **Selecting a refusal-neutral control post hoc** (C-023). Choosing a comparator by its observed post-treatment refusal on the analysis rows conditions on a mediator → collider path into the primary.
4. **Mask geometry as a refusal predictor** (R-076). Index-summary features are dead; a predicted-refusal *control* has no predictor to be built on.
5. **The K ladder past 32.** PR-029's own preregistration stops it there; K=105 at ~240 GPU-h is refused.
6. **Row-noise variance fixes.** Naming them so they are not re-invented: more rows/arm, more generations/prompt, row-level CUPED, a continuous endpoint, domain-blocked or mixed-effects estimators with draw as a random effect. Arithmetic: 1160 rows = 116×10, ICC 0.089–0.112 → design effect 1.9, n_eff ≈ 610; at ASR 0.27 row-sampling sd = 0.018; judge flip term ≈ sqrt(0.126/1160) ≈ 0.010; combined ≈ 0.021. sqrt(0.0783² − 0.021²) = **0.0754 — ~93% of the variance is a genuine draw-level offset.** Every listed fix attacks the other 7%. A domain- or row-level t here is the unit error this phase has made three times wearing a variance-reduction costume.
7. **A layer sweep run until one band rescues the result** (PR-13). Only an exhaustive, preregistered, Bonferroni-corrected partition is admissible.
8. **Reading a criterion/capability failure as a mechanism null** (C-023/R-028 error class).

---

## 3. THE CENTRAL UNRESOLVED TENSION

The representation-level result is large, replicated across two codewords and two model families, and causally clean against its own dose-matched control — yet the comparator that makes it clean is behaviourally worthless: at *identical* dose the control family's induced refusal spans 25-fold and its ASR spans 0.126–0.374, so the between-control sd (0.0783, ~93% of it a genuine per-draw offset) is three times the effect being sought, and the geometry features that would let us match or predict that offset do not exist. The consequence is not "the attack does not run on the mechanism" — it is that the only instrument we have for asking (arm-level ASR against a distribution of draws) has an error term dominated by an unmodelled property of *which* positions a mask happens to hit, and the phase must either find that property somewhere nobody has looked (attention mass, activation space, off-sample behaviour), integrate it away by changing how the control is constructed (per-row seeding), remove the channel that generates it (a refusal-free endpoint), or stop asking the mean-contrast question and ask a within-arm covariance question instead.

---

## 4. RANKED NEXT EXPERIMENTS

Ranked by information gained per (GPU-h + $). Total for the top five: **~16 GPU-h, $0.** Experiments 1–2 must run before any new GPU is bought — they decide whether 7 and 8 are purchasable at all.

---

### #1 — Is the draw offset reproducible? Split-half reliability + variance decomposition
**0 GPU-h, $0, ~1–2 CPU-h. Gating.**

**Question.** The 0.0783 is a stable, prompt-independent property of the mask: an arm's ASR on a random half of the 116 domains predicts its ASR on the other half, Spearman-Brown-corrected rho ≥ 0.7 across arms. If false, the 0.0783 is not a draw property and the whole K ladder is mis-specified.

**Design.** All CPU, no generation, no judging. (a) **Split-half**: per arm, split 116 domains by fixed seed, correlate half-A vs half-B *across arms* (unit = arm, n=8 today, n=32 when PR-029 lands); 200 random splits, report the distribution, not one estimate; permutation CI by shuffling arm labels. (b) **Variance decomposition** of ASR over 8 arms × 116 domains into constant arm offset / arm×domain interaction / Bernoulli residual, with the **judge term measured empirically** from R-074's 5×1160 byte-identical re-judge (the arm-ASR sd across two judgings of identical text *is* the judge floor) — not from a formula. Report all three as fractions of 0.0783² with domain bootstrap CIs. (c) **Within-arm mask structure**: regenerate each arm's per-row positions (`dcs_verify_draw_regenerable.py`; R-066 identity-verified 200/200, seed+1 mutant 0/200) and measure mean pairwise Jaccard of normalised positions across the 1160 rows against a null in which each row samples independently from its own recorded pool. This is R-070's explicitly un-run hypothesis ("the draw seed is per arm, not per row … Recorded as a hypothesis; not investigated").
**Independence unit:** the arm for (a); domains bootstrapped for (b).

**Kill.** Split-half < 0.5 with a CI containing zero AND < half the between-arm variance in the constant offset ⇒ no stable draw-level quantity: #7 cannot average it out, #8 cannot predict it, and R-063's arm-level calibration loses its footing. Then stop buying draws entirely. Separately, if (c) returns cross-row similarity at the independent-sampling null, the "one seed = one mask pattern" mechanism is dead and #7 must not be bought on that rationale.

**Honest expectation.** (a) probably positive given R-075's near-monotone refusal/ASR ordering; (b) is the deliverable that matters regardless — the phase has quoted 0.0295 → 0.0586 → 0.0783 as if each were pure draw heterogeneity, never subtracting the row and judge floors.

---

### #2 — The dissociation as a positive result: per-domain representation damage vs per-domain attack change
**0 GPU-h, $0. Rides PR-029's already-committed 55 GPU-h.**

**Question.** If the attack runs on the remapping, the domains where KO-3 destroys the remapping most must lose the most attack. Falsifiable: rho(per-domain Δ`semantic_logodds`, per-domain Δattack rate) has a CI that **excludes the rho implied by full mediation**, simulated at the measured base rate and ~10 rows/domain.

**Design.** Analysis only. n = 38 domains (declared unit, ICC≈0.34). x_d = per-domain paired Δ`semantic_logodds`, cell C, KO-3 − baseline (exists at full precision from R-010). y_d = per-domain attack rate under KO-3 minus the per-domain mean over **all 32** PR-029 control draws — averaging over 32 divides exactly the sd 0.0783 that killed the primary by √32. Spearman rho, domain-permutation p, domain bootstrap CI. **Frozen before any PR-029 outcome is read:** simulate the full-mediation rho distribution (monotone mediation model calibrated to the measured baseline rate and row count) — this power computation is the first deliverable. Declared outcomes: (A) CI excludes mediation-rho and contains zero ⇒ **dissociation established at the domain unit, a positive claim**; (B) rho significantly negative ⇒ behavioural claim rescued by a statistic the control variance does not touch; (C) mediation-rho inside the achievable CI ⇒ **CANNOT ANSWER**, declared, cost zero.
Sensitivities: rho on the K=8 subset (does adding 24 draws move it as the √32 argument predicts?); rho with the +562-refusal draw excluded (leverage point, no defect).

**Why it is immune to C-015.** PR-004/R-012's mediation test was arm-level and died because the dose-matched comparator suppressed attack by inducing refusal. Here the control enters only as a per-domain **average over 32 draws** — nothing is chosen, so the between-control variance is a term to be divided, not a term to be tested against.

**Kill.** Outcome (C), known in advance and free. Second kill, checkable from committed artifacts before anything runs: if x_d has no usable variance (R-010 is 1+/37−; if the 37 negatives bunch at a floor there is nothing to correlate) the test **excludes** rather than counting as a null — R-076's "rho = 0.0000 / no variance to correlate is not no effect" trap.

**Honest expectation.** (C) is a live risk at n=38 with ~10 rows/domain. But it costs nothing and the power simulation tells us so before we look.

---

### #3 — M1: the dose is attention mass, not key count
**~1 GPU-h, $0.**

**Question.** A draw's induced refusal is a monotone increasing function of the pre-intervention attention probability mass its masked keys receive from the query rows in L6–14. Operationally: Spearman rho(mean removed mass, induced refusal) ≥ +0.35 at n=32 arms; within-arm prompt-demeaned row-level rho sign-consistent in ≥ 24/32 arms.

**Why now.** R-075's "identical dose" is `keys_masked` = 522 — a **count**. `nondemo_control_draw` (score_behavior.py:816) samples those 522 uniformly from the protected complement, and attention is heavy-tailed (sinks, BOS-adjacent, delimiters, template scaffolding), so two uniform 522-key draws can remove attention mass differing by an order of magnitude. R-076's seven features are pure functions of the sorted position list — the model is never run. This is the first candidate that asks what the masked positions were **carrying**.

**Design.** No generation. One **clean, unhooked** prefill per prompt over the fixed 1160-prompt set, eager attention (already the forced path for knockout arms, score_behavior.py:1632). Hook-and-reduce per layer: accumulate a [9 × seq_len] vector of attention mass received by each key position summed over query-span destination rows, in three head reductions (head-mean, head-max, per-layer-max). Removed mass = dot(mask indicator, that vector), read from persisted `control_draw.positions` (R-066: every behavioural row persists its positions verbatim).
**Primary:** between-arm Spearman rho, n=32 arms, arm = independence unit, permutation null over arm labels, Bonferroni over 3 reductions (α=0.0167 ⇒ |rho| ≥ 0.41). **Secondary:** R-076's exact estimand verbatim — prompt-demeaned within-arm rho, arm label permuted within prompt, 32-arm sign test (floor 4.7e-10).
**Declared limitation, pre-data:** mass is measured on the clean distribution, so this is a **first-order** predictor — masking at L6 changes what L7–14 attend to. The per-layer-under-own-mask variant costs 32× the forward passes and is deferred unless this clears.

**Kill.** |rho| < 0.35 on all three reductions AND ≤ 20/32 within-arm sign-consistent. Report as a **bound** (|rho| < 0.35), not "mass is irrelevant". Second kill: if removed mass is near-constant across draws (between-arm CV < 0.1) the hypothesis is **vacuous, not false** — the DEGENERATE-feature lesson from R-067's `min_dist_to_query`.

---

### #4 — G1: a refusal-free behavioural endpoint (`mapping_use`), eight draws replayed
**≤ 5 GPU-h, $0 — and only 0.9 GPU-h before the gate decides. The only live route to any behavioural claim.**

**Question.** (a) On an endpoint with no refusal channel, the dose-matched control family becomes exchangeable — between-control sd at least 2× smaller *relative to the effect* than 0.0783; (b) KO-3 reduces mapping use against the control distribution, p<0.05, t(7). If (a) fails, non-exchangeability is a property of position-matched masking as such and **changing endpoints is dead for every endpoint**.

**Design.** `cds38`, button↔bomb, Llama, L6–14 — every setting inherited from PR-028 so the two endpoints sit in one table. Readout: the `mapping_use` free-generation probe already implemented (`scripts/rah_verify_phase1.py:66`, `scripts/rbd_deliverables.py:86`), scored deterministically. **No judge**, so C-023/R-074's flip rate and session drift do not exist on this endpoint.
- **Stage 1 (gate, 2 arms):** `natural_doublespeak` vs `benign_literal` on the same 38 domains. Gate frozen before the arms run: mapping-use rate must exceed the no-mapping floor by ≥ 0.15, domain-clustered McNemar p<0.05, n=38. This gate exists because **RBD-C-016 measured exactly this contrast on Llama and got 24/80 vs 32/80, p=0.215 — a null** — on the lantern bank. cds38 at installation 0.908 is a hope, not a result.
- **Stage 2 (only if gated, 9 arms):** KO-3 + the 8 replayed draws. B-007 is closed (R-066): masked positions are persisted per row on 46/46 behavioural arms and regeneration is identity-verified 200/200 with the seed+1 mutant at 0/200 — so this is the *identical* control population R-075 characterised, not a fresh one.
**Primary:** identical estimator to PR-028 — arm-level mapping-use rate, KO-3 vs control distribution, between-control sd as error, t(7), two-sided. Independence unit: domain, n=38, ICC≈0.34.
**Secondary, delivers regardless of the primary:** the realised between-control sd on this endpoint and its correlation with each draw's already-measured induced refusal on the ASR endpoint — the direct test of whether refusal is what makes the control family non-exchangeable.

**Cost.** max-new ≈ 64 ⇒ ~0.84 s/row ⇒ ~0.45 GPU-h/arm. Stage 1 = 0.9; Stage 2 = 4.1.

**Kill.** (1) Gate fails ⇒ RBD-C-016 replicated on a second bank; report "no exposure-clean behavioural readout with headroom exists in this paradigm on Llama"; cost 0.9 GPU-h. (2) Gate passes but sd is not materially below 0.0783 relative to a comparable effect **and** does not correlate with induced refusal ⇒ non-exchangeability is a property of position-matched attention masking as such; every endpoint inherits it; the endpoint-change route is dead. State that as a finding, do not bury it.

**Honest expectation.** The Stage-1 gate is a coin flip given RBD-C-016.

---

### #5 — G3: widen the half that works — constructible-control concept rebuild + a third model family (readout only)
**~4 GPU-h, $0.**

**Question.** The remapping-specific DiD is a property of the **paradigm**, not of bomb/button or the Llama/Qwen pair. It fails if a rebuilt concept fails its preregistered per-domain sign test *with a valid control*, or if a third family shows the effect **without** the specificity DiD (generic damage, not remapping-specific necessity).

**Why now.** Two of the three scope limits on the paper's strongest result are cheap and untouched. Generality is currently MIXED 1-of-2 (R-035: lantern→poison 0+/20−; candle→missile 6+/14−, p=0.115) **and control-free** — R-033/R-033a: those banks carry no preamble, prompts are ~85% demonstration, `match_ratio` 0.000, max attainable 0.54/0.56 in tokens. So generic attention damage is only *inherited* from bomb outside bomb, and N6 shows the inheritance is partial. R-033's finding is about the banks' **format**, not their concepts, and the pools are concept-agnostic and rebuildable at zero pool-generation cost. Readout arms cost minutes (max-new 8), not 2.3 GPU-h.

**Design.**
- **Track A (2 GPU-h, 8 arms):** rebuild lantern↔poison and candle↔missile in the cds38 prompt format (preamble present, demonstration share matched). **Pre-flight gate, zero GPU:** compute `match_ratio` from tokens alone on the rebuilt prompts, require ≥ 0.9 — the exact quantity R-033 measured at 0.000. Then per concept: cell C baseline, cell C KO-3, cell C dose-matched control, cell B KO-3. Primary borrowed verbatim from PR-013: per-domain paired Δ`semantic_logodds`, two-sided sign test, plus the C−B DiD. Report `option_mass` beside every logodds (phase-wide readout limit, R-032) and per-domain baseline installation **first** — R-038/R-039 showed candle's failure tracks its domains spanning the installation range rather than sitting at ceiling; if installation is again ~0.4, that is the answer and it is recorded as such.
- **Track B (2 GPU-h, 4 arms):** third model family on button↔bomb, outside Llama/Qwen. Run R-023's capability gate **first**; place the band at matched relative depth (6–14/32, 7–17/40); same 4 arms, same primary and DiD.
No behavioural arms, no judge, either track.

**Kill.** Track A dies **free** at the pre-flight if `match_ratio` < 0.9 — the control stays unconstructible for a stated token-level reason. Track A dies **informatively** if candle fails again *with* a valid control and adequate installation: generality is not a paradigm property, the claim narrows to high-installation mappings, consistent with N5. Track B dies at the capability gate as a **capability limit**, never as "the mechanism does not generalise". Track B also dies if the effect appears **without** the specificity DiD — that would weaken the headline claim on all three families.

**Note.** Do **not** re-run the Qwen magnitude comparison as evidence of anything: per the verification kill, cross-model magnitude is not claimable without dose- and band-matching.

---

### #6 — M3: judge-free, generation-free assay of the control spread in the refusal direction
**~6 GPU-h, $0.**

**Question.** The 25-fold spread is already present prompt-side. rho(arm-mean Δrefusalness at the final prompt token under the arm's mask, arm's judged induced refusal) ≥ +0.35 across 32 arms; within arm, row-level Δrefusalness predicts that row's judged refusal (prompt-demeaned, sign-consistent ≥ 24/32).

**Why now.** Every measurement of the spread so far ran through 1160 generations plus a judge. If the spread is legible in one prefill, screening a draw costs ~0.001 of an arm and the K ladder stops being an arms race (~12 GPU-h to screen 100 candidate draws, against the 240 GPU-h K=105 route). Tooling exists: `refusalness.py` scores ⟨h[final prompt token, L], unit(v_refusal[L])⟩ against the house `refusal_direction_llama_L{12,14,16}.pt`. And Continuation V2's conclusion — refusal-suppression, not concept content, is the causal locus — makes this the sharpest place to look.

**Design.** Prefill only, no decoding, no judge. **Fixed 300-prompt subsample** of the 1160, drawn once, seeded, frozen before any measurement, identical across arms × 33 conditions (baseline + 32 draws), each masked exactly as its behavioural arm (`--intervene nondemo_matched_*:attn_knockout:6-14:1.0`, same seed, eager). Capture resid_post at L12/L14/L16 at the final prompt token; endpoint = Δrefusalness vs unmasked baseline.
**Primary:** between-arm Spearman rho against induced refusal recomputed on **the same 300 prompts** from PR-029's existing labels (not all 1160 — that mismatches populations), n=32 arms, Bonferroni over 3 layers. **Secondary:** row-level, prompt-demeaned, within-arm, 32-arm sign test. **Tertiary, only if #3 also clears:** mediation — does Δrefusalness screen off removed attention mass from judged refusal (drop in the mass coefficient, bootstrapped by arm)? That gives mask → removed mass → refusal-direction shift → refusal.
Frozen before data: the subsample, the three layers, the decision rule.

**Not C-023.** Refusalness is a prompt-side quantity measured before any token is generated — exactly the circularity argument `refusalness.py`'s own docstring makes. Nothing is selected, dropped or reweighted.

**Kill.** |rho| < 0.35 across all three layers AND ≤ 20/32 within-arm consistency ⇒ the cheap-screening route is closed, and the honest report is a representation/behaviour dissociation **on the control side**, plus a caution against the refusal-direction assay generally. Sharper kill: if Δrefusalness correlates strongly with induced refusal **and** > 0.9 with #3's removed mass, the two proposals measured one quantity twice and only the cheaper one (#3) survives — so run #3 first.

---

### #7 — S2: row-randomised controls — average the draw nuisance out INSIDE each arm
**18.4 GPU-h + ~$2.50. Conditional on #1.**

**Question.** The control mask is seeded once per arm (`nondemo_draw_seed(control_seed, draw_index)`, no row term), so the ~0.075 offset never averages down within an arm. Seed it per row — `f(control_seed, prompt_id)` — and the estimand is unchanged (PR-028's numerator already targets the mean over draws) while the error term collapses to the row-sampling floor. Prediction: between-arm sd over 8 row-randomised arms ≤ **0.030**, vs 0.0783.

**Design.** 8 new arms `nondemo_matched_rowrand_d1..d8`, **new names** so no existing artifact silently changes meaning; identical in every respect (protected query span, per-row count-match to that row's demo block, L6–14, `cds116`, n_examples=4, 1160 rows = 116×10) except per-row seed derivation. Plus KO-3 and baseline re-judged with the 8 in **one session** (PR-028b), keyed on `slurm_job_id` (A-017). **Do not land the code change while PR-029's 24 arms are in flight against the old path**; the old arms stay untouched and valid.
**Contracts, checked on full data before any ASR is read (R-069):** 1160 rows, 116 domains × exactly 10, `decode_edits` max 0, `control_draw_match_ratio` 1.000 on every row, `keys_masked` median 522.0, 0 liveness violations, per-row seeds read back and confirmed distinct across rows and arms.
**Primary, unchanged in form:** t = (ASR_KO3 − mean_k ASR_ctrl_k) / (sd_k/√K), df = 7. **Independence unit = the arm (the seed), n=8** — the row/domain structure is NOT used for the primary error term. Domain-level contrasts are a labelled secondary only.
**Pre-registered gate read BEFORE the p-value:** report realised between-arm sd first and declare the design failed if it exceeds **0.040**, whatever the primary says (R-075's "gate on realised sd, not on K" defect, fixed in advance). **Staging:** submit 4 arms, read only the realised sd, then submit the remaining 4; the analyzer refuses to compute the primary until all 8 exist.
**Power from the estimator actually in use (non-central t, df=7, not a normal approximation — C-045):** sd 0.020 ⇒ SE 0.0071, power ~0.72 vs the observed −0.0222 and ~0.99 vs −0.0391; sd 0.030 ⇒ SE 0.0106, MDE(80%) 0.036, i.e. the hypothesised effect only. Report raw and R-063-calibrated, carrying PR-028a's shrinkage caveat.

**Cost.** 8 × 2.3 = 18.4 GPU-h, 6 concurrent ⇒ ~2 wall-days; 10 arms × 1160 rows judged in one session ≈ $2.50, ~6 h on cpu-killable (raise `--time`). Versus ~240 GPU-h + ~$26 for K=105.

**Kill.** Realised sd > 0.040 (< 2× reduction) ⇒ the nuisance is not a position lottery that averages over rows, no re-randomisation scheme fixes it, and the phase is left with K alone — report and stop. Secondary kills: (i) realised dose moves (`keys_masked` median off 522, or any row `match_ratio` < 1.000) ⇒ arms are **void, not reinterpreted**; (ii) #1(c) shows within-arm cross-row mask similarity already at the independent-sampling null ⇒ the mechanism this rests on is absent and the 18 GPU-h must not be spent on this rationale (it could still be bought on #1(a) alone — the preregistration must say which justification is standing).

---

### #8 — S3: off-sample draw covariate, cross-fitted out of the K=32 arms
**~12 GPU-h, $0. Conditional on #1 and a cap-invariance pilot.**

**Question.** The draw nuisance is a transportable property of the mask: each draw's refusal rate on a **held-out** prompt set correlates with its ASR on the cds116 analysis rows at |rho| ≥ 0.7 across draws. If so, cross-fitted ANCOVA shrinks residual sd 0.0783 → ≤ 0.055 and turns PR-029's already-purchased K=32 from power 0.34 into ~0.8 against the observed −0.0222, with no new main-arm generation.

**Design.** Auxiliary set ~29 domains × 10 = 290 rows from domains **disjoint** from cds116's 116 (78 independently authored domains already exist; disjointness asserted by `prompt_sha16` against every cds116 row). Run all 32 PR-029 draws + KO-3 + baseline on it at a short cap. Covariate = `kw_refusal`, deterministic (DR-10: 0 disagreements on 160 rows; C-023: 0 refusal flips in 5800 rows) and cap-invariant in this repo's one measurement (81/96 completions changed between a 192- and 640-token cap while 0 refusal decisions moved) — **no judge call, $0, no session-drift exposure**. That cap-invariance is imported from another bank/model, so **verify it on ONE arm at both caps before submitting the other 33.**
**Estimator.** x_k = auxiliary refusal rate (a pre-outcome property of the mask, on rows disjoint from the analysis rows); y_k = that draw's analysis-bank ASR from PR-029's single session. Fit y = a + b·x over K=32 with **leave-one-draw-out cross-fitting** so the slope residualising draw k is fitted without draw k. Primary: t = (y_KO3 − â − b̂·x_KO3 − mean_k residual_k) / (sd_k(residual)/√K), df = 30. **Independence unit = the draw, n=32**; the 290 auxiliary rows are an instrument for x_k, never a second sample of the outcome, and are never pooled with the 1160. **KO-3 is adjusted by the same rule as every control**, using its own auxiliary rate — the symmetry R-063 established and PR-014's one-sided bracket violated. Analyzer frozen before PR-029's labels exist; raw unadjusted primary always reported beside it. **Success read on shrinkage first, p second:** cross-fitted R² and residual sd before the t.

**Why not C-023 and why R-076 does not reach it.** Nothing is selected, dropped or reweighted — all K stay in and the point estimate's numerator is untouched; the covariate is measured on units disjoint from the analysis rows, so it cannot be a collider on those outcomes, and cross-fitting means it cannot be tuned to the contrast. R-076 refuted mask *geometry* (7 hand-built features, needing |rho| ≥ 0.71 at n=8); a behavioural measurement of the same mask on other prompts is not a feature set and needs no hypothesis about which positions matter. R-076 closed a control *matched* on predicted refusal — a selection — not an adjustment. At n=32 the detectable |rho| falls to ~0.35.

**Cost.** 34 arms × 290 rows at ~128-token cap ≈ 0.35 GPU-h/arm ⇒ ~12 GPU-h, 6 concurrent. $0. If |rho| = 0.8: residual sd 0.047, SE at K=32 = 0.0083, MDE(80%, df=30) ≈ 0.024 — roughly what K=105 (~240 GPU-h) would have bought, for 12.

**Kill.** Cross-fitted R² ≤ 0.2 (shrinkage < 15%) ⇒ no off-sample draw covariate exists; drop the adjustment, the raw PR-029 primary stands alone. That is a real finding: it would say the nuisance is prompt-set-specific, which independently undermines R-063's calibration (whose conversion c is an arm-level constant measured on controls, with KO-3's own conversion unobservable) and justifies retiring the calibrated arm. Second kill, before the other 33 arms: refusal decisions not cap-invariant on the two-cap pilot ⇒ the cheap instrument is void (pay ~30 GPU-h for full-length auxiliary generation, or abandon). Third, validity kill: any auxiliary domain colliding with a cds116 domain by `prompt_sha16` ⇒ the covariate is no longer off-sample and the design is **void, not patched**.

---

### #9 — M2: exhaustive L6–14 sub-band partition on the two extreme draws
**~28 GPU-h + ~$3. Lowest info/cost; run only if #4 and #7 both fail.**

**Question.** Is the induced refusal computed in the same sub-band as the mapping destruction? Powered alternative: one of {L6–8, L9–11, L12–14} induces < 25% of the full-band refusal while KO-3 in that same band retains ≥ 50% of the full-band DiD — which would give a band where the behavioural test is powerable without buying draws.

**Why it is worth stating.** L6–14 has been applied whole in all 39 intervention arms and deliberately never swept for the **behavioural** endpoint (§1.14; R-030/R-031 explicitly forbid reading a per-layer profile off the representation sweep). R-076 refuted geometry along the sequence axis; depth is orthogonal and untested behaviourally. The extreme draws are identified and judged (`s0906_d1` +562, ASR 0.126; `s0905_d2` −7, ASR 0.374) and R-075 verified the extreme arm has no defect.

**Design.** 12 arms, 6 concurrent: 2 extreme draws × 3 sub-bands (6); KO-3 × 3 sub-bands (3); full-band L6–14 replications of KO-3 and both extreme draws in this session (3). Same frozen 1160-prompt set, same seeds, eager. **Dual endpoint on every arm** — induced refusal + ASR from generation, and the forced-choice `semantic_logodds` on the same forward path. **Statistic: within a draw ACROSS bands on the SAME prompts** — unit = prompt, paired (McNemar on refusal; paired bootstrap over 1160 prompts on ASR and logodds). This deliberately sidesteps the between-arm variance that made PR-028 underpowered: no step compares a treated arm to a distribution of controls. **Multiplicity declared:** the partition is exhaustive, preregistered, family of 3, Bonferroni α=0.0167, all three reported whatever they show; **no band may be promoted to the phase's headline band without an independent confirmation run on a held-out draw.** This is not PR-13's forbidden sweep-until-one-rescues. All 12 judged in one session; refusal read judge-free where possible.
If #3 and #6 both clear, run this with draws constructed at the extremes of the *validated* predictor instead of the two observed extremes — a stronger version at the same cost.

**Kill.** All three sub-bands induce refusal roughly proportionally (each 25–45% of the L6–14 total, no pair separated at Bonferroni) AND the band ordering for refusal matches that for the representation DiD ⇒ refusal induction and mapping destruction are the same computation at the same depth; the depth-separation repair is dead. **Second kill, a real risk:** if the sub-bands are individually near-inert on **both** endpoints (the L6–14 effect being a conjunction requiring the full band — which the K-row step shape hints at), the partition cannot answer the question and the result is "the band does not decompose", not a separation.

**Honest expectation.** The conjunction outcome is the modal one. At 28 GPU-h this is the only item on the list whose likeliest result is uninformative, which is why it is last.

---

## 5. WHAT TO DO IF EVERYTHING RETURNS NULL

The paper does not depend on the behavioural link, and it should stop being written as if it does.

**The claim to defend:**
> In-context doublespeak installs a codeword→concept remapping whose construction is causally localised to demonstration→query attention in a low-layer band — necessary, remapping-specific, threshold-shaped, replicating across two model families and two codewords — and the harmful behaviour the paradigm is credited with does not measurably depend on that construction.

**Why the second clause is worth more than the failed positive.** DCS_LITERATURE_MATRIX places Yona et al. (ACL 2026) as having the phenomenon with **no internal causal intervention**. This work has the intervention. A measured dissociation between a large, replicated representational effect and a behavioural endpoint that is provably insensitive to it is a stronger contribution than "the attack is caused by the mechanism", *provided* the second clause is stated as a **measured bound with a positive test behind it** rather than as a failure to reject.

**What must be in the paper for the second clause to be honest:**
1. **The bound, not the p-value.** "Δ = −0.0222, t(7) = −0.80, p = 0.449, MDE 0.0655 at realised between-control sd 0.0783" — with the explicit statement that this is underpowered, not a clean negative, and that K≈105 (~240 GPU-h) would be needed for the observed effect.
2. **R-075 as a finding in its own right**, and probably the paper's second-most-interesting result: at identical dose (522 keys, match_ratio 1.000, all 8 draws) induced refusal spans −7 to +562 and ASR spans 0.126–0.374 — **which positions are masked dominates behaviour at constant dose**. This is a methodological result about attention-knockout controls that generalises beyond this paradigm, and it should be written for that audience.
3. **R-076 as its companion**: the obvious repair does not exist — no index-summary geometry feature predicts the refusal, within (0/4 consistent, k=8) or between (best rho 0.238, n=8) arms. Plus whichever of #3/#6/#8 ran, as bounds on the mass / activation / off-sample predictor families.
4. **#2's positive dissociation** if it lands in outcome (A) — this is what converts "we could not detect it" into "we tested a necessary implication of mediation at the declared independence unit and excluded it". If it lands in (C), say CANNOT ANSWER and print the power simulation.
5. **The variance decomposition (#1)** — publish the split of 0.0783² into draw offset / arm×domain / row Bernoulli / judge, with the judge term measured from the byte-identical re-judge. It retires the "just run more rows" reviewer objection in one table.
6. **Every scope correction from verification, stated in the text, not the appendix:** no cross-model magnitude ratio; "no *destructive* effect above L14", bank-named, with 24–31's unexplained +0.754 (38+/0−) reported as exploratory; L6–14 contains the maximum but is not a boundary (L0–5 contributes); specificity is a magnitude not a sign claim; R-002 is a replication across concepts, not a specificity control, with no test statistic; R-050's benign install is 6.6% of rows with option_mass collapsed and its registered primary CANNOT ANSWER; the p-values are one sign pattern replicated, not independent tests.
7. **A limitations section that names the paradigm ceiling** (N5) and states that 38 domains = 38 contexts for one mapping, ICC ≈ 0.34.

**What the null world costs.** If #1, #2, #3, #4, #6 all return null, the total spend is ~12 GPU-h and $0, and every one of them contributes a stated bound to item 3 above. Only #7, #8 and #9 risk real GPU on an outcome that would not appear in the paper — which is why they sit behind gates that read realised sd, cross-fitted R², and a two-cap pilot **before** the primary.