# UPDATED PAPER CLAIM TABLE — after the Asymmetry sprint (2026-08-11)

*Deliverable §15.7. Supersedes `docs/PAPER_CLAIM_TABLE.md` for the rows it touches; rows it
does not touch are unchanged and still live in that file.*

**Status vocabulary (the only permitted values):** VERIFIED · NEGATIVE · UNDERPOWERED ·
EXPLORATORY · SUPERSEDED · WITHDRAWN.

Model = `meta-llama/Llama-3.1-8B-Instruct` (bf16, SDPA) unless stated. Data = ClearHarm **v3
leakage-0**; train pool n=40 (frozen), held-out test n=37 (GCG/soft-prompt) or n=42
(behavioural). Binary success = **StrongREJECT ≥ 0.5** unless the row says otherwise.

---

## A. Claims this sprint ADDS

| # | Claim | Experiment | Split / n | Effect | Uncertainty | Control | Status | Limitation |
|---|---|---|---|---|---|---|---|---|
| **A1** | The causal refusal direction is **unusually EASY** to reach from suffix-token perturbations — H1 (input-reachability failure) is rejected | `asym_p1_reachability.py`, `‖Jᵀv‖` at `decision`, hs[19] | train 40 / test 37 | **14.3× / 15.0×** vs 100 isotropic randoms (pct 1.000); **3.4×** vs other-layer refusal dirs (pct 0.983); **4.71×** vs the CORRECTED covariance-matched control (pct 0.990) | mean percentile among controls **1.000 / 0.983** | 100 isotropic + 3 other-layer + 1 foreign. 100 corrected covariance-matched (mean pairwise |cos| 0.094 after dropping the rank-1 massive-activation axis; the original run's family was degenerate at ~0.97 and its 6.74× is superseded by 4.71×) | **VERIFIED** (both splits; replicates under 4-bit NF4; **replicates on Phi-4-mini at 5.56×/4.12×/3.46×, all pct 1.000**) | one base point (init suffix) |
| **A2** | The **first-order surrogate that discrete search relies on is invalid at one-token step size**, and *more so* for the refusal direction than for a typical activation-like direction | ε-scan, `asym_p1_reachability.py` | train 40 / test 37 | r = **0.84 / 0.81** at ε=0.10 → **−0.002 / −0.324** at ε=1.0; strict null retains **+0.204 / +0.334** | 120 probes per ε per split | all four direction families | **VERIFIED on Llama (both splits); CROSS-FAMILY PARTIAL NEGATIVE** | On Phi-4-mini (BOTH splits) the surrogate degrades substantially but does **not** collapse: 0.535→+0.214 (train), 0.567→+0.125 (test), vs Llama's ≈0/−0.32. The **qualitative core** of H2′ (most validity is lost before one-token step size) holds cross-family; the **sharp form** (mechanism ends up worse-predicted than a matched null) is **Llama-only** — on Phi that ordering is unstable across splits and unresolvable at n≈40. Phi's peak r is also lower (0.535 vs 0.840), so a noisier probe remains a live alternative explanation |
| **A3** | A perfect continuous solution **inside the token simplex** retains only a twentieth of its effect after rounding to real tokens | simplex + §19.4 rounding probe | test 37 | relaxed −8.69 → rounded **−0.50**; **retention 5.7 %** | rounded value lies inside the unoptimized-suffix range (−0.18…−1.05) | 20 unoptimized random-token suffixes | **VERIFIED** | seed 42; retention measured on the projection, **not** on ASR |
| **A4** | **Continuous input optimization on the refusal direction is causal, SPECIFIC and behaviourally effective** | `asym_p2_softprompt.py`, budget 0.10, both arms | test 37 | ASR **0.757** vs **0.081**; **ΔASR +0.676**; refusal_rate 0.027 vs 0.460 | McNemar **p = 5.96e-08**, boot95 **[+0.514, +0.811]** | dose-matched, GPU-class-matched norm-matched random direction | **VERIFIED** | **seed 42 only** (≥3 required by plan §6.1) |
| **A5** | The optimal continuous dose is ≈0.10 × mean embedding norm; the ASR/dose relation is an **inverted U** | dose sweep 0.05/0.10/0.25/1.00 | test 37 | 0.162 → **0.757** → (n/a) → 0.000 | ranges reflect judge noise | — | **EXPLORATORY** | the sweep was read on TEST; needs freezing on the untouched `dev` split |
| **A6** | Driving a linear probe far off-manifold **destroys behaviour instead of producing it** — probe displacement is not evidence of mechanism control | budget 1.00 arm | test 37 | Δproj **−20.09**, yet ASR **0.000** *and* refusal_rate **0.000**; per-prompt sd collapses 2.50 → 0.25 | — | — | **VERIFIED** | a methodological result, not a mechanism claim |
| **A7** | Suffix-induced refusal suppression is a **generic late-layer mode**; optimization scales its magnitude, not its shape or location | §19.2 layer sweep + 20 unoptimized suffixes | test 37, L10–L24 | profile correlation **r = 0.985** (unoptimized vs optimized) and **0.9965** (refusal vs random suffix); deepest at **L24**, not the L18 target | — | 20 unoptimized random-token suffixes; GCG init | **VERIFIED** | Llama only |
| **A8** | The universal suffix's refusal suppression **does not overfit** its optimization pool | §19.1(c) | train 40 vs test 37 | transfer ratio **> 1 in all 9 cells** (1.17–2.00) | — | 3 arms × 3 seeds | **VERIFIED** | — |

## B. Claims this sprint CHANGES

| # | Prior claim | What changed | New status |
|---|---|---|---|
| **B1** | Q5 / Gate D clause (ii): *"the mechanism suffix does not move its own internal target more than random"* | Holds at **seed 42 only**. Seeds 43 and 44 reverse it on **37/37** and **35/37** held-out prompts (Δ −1.464, −1.345, both p≈1e-4). Mean drop refusal **−2.013** vs random **−1.204**; the *random* arm is the more variable one (sd 0.810 vs 0.513) — seed 42 drew an unusually effective random direction | **WITHDRAWN** as unsupported (one seed, one random draw). Gate D clause (i) — no ASR advantage — **still stands**, so the dissociation *sharpens* |
| **B2** | Gate D: *"a mechanism-derived token objective fails"* | The objective read a **fixed absolute token index from `train_tasks[0]`**, correct for **1 of 40** training prompts, and silently contributed 0 for one. It also read the *last suffix token*, not the position where the axis was fitted and validated | Numbers **stand**; the *interpretation* is **SUPERSEDED** — "an objective that mostly did not measure the refusal coordinate fails". A position-corrected arm is built and is a real test (Gate B predicts it still fails) |
| **B3** | Q1/Q3: refusal@L18 vs random, 3-seed mean **ΔASR +0.018** | The StrongREJECT judge flips ~**3.4 %** of labels between runs on identical files at `temperature=0` ⇒ ASR uncertainty ±0.03–0.08 at n=37. The effect is **below the judge's own noise floor** | **NEGATIVE, strengthened.** It was never measurable at this n. Part of the ~0.24 between-seed swing is judge variance, not optimization variance |
| **B4** | Q7 quantization ASRs (and Phi X1/X3) | Produced at **MAL_THRESHOLD = 0.25** while the handoff states 0.5 | **VERIFIED, unchanged.** Recomputed from continuous scores at 0.5: **27 contrasts, 0 sign flips, 0 significance flips, max shift 0.071**. bf16 +0.2857, 8-bit +0.2619 at *both* thresholds; 4-bit +0.5714 → +0.5476 (p≈0) |
| **B5** | Q2: refusal@L12 ("Jacobian-peak") is not a useful lever | **L12 is the only layer that FAILED** the ablate+induce validation (ablate 0.0, induce −0.333, `valid=false`) | **NEGATIVE but uninformative** — it never was a validated axis |

## C. Integrity checks that PASSED (report as method, not as findings)

| # | Check | Result |
|---|---|---|
| C1 | All handoff headline numbers traced to raw scalar JSON | **0 mismatches** across 20 GCG arms, the matrix stats, the mech-validity JSON and 3 quantization summaries |
| C2 | Plan §19.3 — is the refusal vector one object across activation ablation, the GCG loss and the readout? | **md5-identical**, cosine 1.0, for L12/14/16/18/20 |
| C3 | Independent reproduction of the shipped Q5 numbers before extending them | baseline **3.4023** (vs 3.40); refusal **−1.664** vs random **−2.045** (vs −1.66 / −2.04) — exact |
| C4 | Cross-script consistency | GCG init suffix effect **+1.015**; no-suffix baseline 3.4023; Phase-2 with-init baseline 4.417. 3.4023 + 1.015 = 4.417, two independently written scripts agreeing to 3 dp |

## D. Known limitations to carry into the paper

1. **Seeds.** A4 rests on seed 42 alone; the plan requires ≥3. Queued.
2. **D3 — intervention scope.** The activation arm is all-position/all-layer; every input arm is 16 suffix positions. Figure A's activation-vs-continuous row is therefore a scope *and* medium comparison. The scope-matched activation arm is specified but not run.
3. **A6 direction-fit cohort.** The L18 axis was fit on `pair_carrot_bomb.json` (n_harmful=60 / n_harmless=20, harmless = 20 generic instructions) and applied to ClearHarm — cross-distribution transfer, not previously flagged.
4. **n = 37 held-out** throughout Phase 1/2; combined with a ±0.03–0.08 judge band, only effects ≳0.10 are resolvable.
5. **One model** for the reachability geometry (Llama-3.1-8B). Cross-family replication of A1/A2 has not been run.
6. **A3** measured retention of the projection, not of ASR.
7. Phases 4 (multi-concept, Gate F), 5 (two-signal defense, Gate G), 6 (Phi power-up) and 7 (quantization reachability) are **in progress or not started**; no claims from them appear above.

---

## The one-paragraph version

> A linear refusal direction in Llama-3.1-8B is causal in activation space, and it is
> **unusually easy** to reach from input embeddings — 6.7× more sensitive to suffix
> perturbations than a direction that merely looks like a real activation direction. A
> continuous 16-token soft prompt targeting it reaches **ASR 0.757** on a locked held-out set
> versus **0.081** for a dose-matched random direction (ΔASR +0.676, p = 6e-8). Yet a discrete
> GCG suffix targeting the *same* direction performs like a random direction (mean ΔASR
> +0.018 — below the judge's own noise floor). The gap is not reachability. It is that **the
> first-order surrogate discrete search depends on is invalid at the granularity of a single
> token** — the gradient predicts the true effect with r ≈ 0.84 at a tenth of a token-step and
> r ≈ 0 (or negative) at a full one, *worse* than for a typical activation direction — and
> that **a perfect solution in the token simplex retains only 5.7 % of its effect once
> rounded to real tokens**. Interpretability-derived directions can be genuine causal handles
> and still be unusable by the discrete optimizers red-teaming actually runs.

### §7.5 per-prompt vs universal (added 2026-08-12 per Mahmood; completed 2026-08-14)

| claim | experiment | model | train/test | n | effect | CI / p | random control | status | limitation |
|---|---|---|---|---|---|---|---|---|---|
| Per-prompt optimization gives **no reliable behavioural advantage** over a matched random direction | per-prompt GCG, 3 arms × 3 seeds, 2 budgets | Llama-3.1-8B | frozen test (attacked in place) | 37/seed | ΔASR graded: −0.003/+0.095/+0.024 (full), +0.085/−0.010/+0.071 (matched) | 0/6 significant | norm-matched random dir | **NEGATIVE** | sign-inconsistent; n=37 gives ~9 % power for these base rates |
| The mechanism objective **does move its internal target** more than random, at full budget | per-prompt projection readout, L18→hs19, decision pos | Llama-3.1-8B | frozen test | 37/seed | mean **−0.354** | 3/3 sign-consistent; 1/3 Holm-surviving (p=0.042) | norm-matched random dir | **VERIFIED** | budget-specific (compute-matched is 2/3 with a reversal) |
| **Representation ≠ behaviour** reproduced in the per-prompt setting | the two rows above, same suffixes/seeds/budget | Llama-3.1-8B | frozen test | 37/seed | projection 3/3 vs behaviour 0/3 | — | same | **VERIFIED** | 3 seeds; behavioural half is a null, not a measured opposite |
| Per-prompt suffixes **transfer** to unseen prompts | transfer matrix, k=5 off-diagonal/source | Llama-3.1-8B | frozen test | 222 gens/arm | off-diagonal ASR 0.173–0.200 vs universal held-out 0.162 | — | random-direction transfer matrix | **VERIFIED** | 2 seeds; subsampled k=5 of 36 |
| Prompt-specificity is **not direction-specific** | gap(mech) − gap(rand) | Llama-3.1-8B | frozen test | 37 sources | +0.000 (s42), +0.108 (s43) | MW p=0.80 / 0.31 | yes | **NEGATIVE** | gap itself not significant in any arm |
| **Compute dominates direction** in per-prompt GCG | matched-random arm, 5 → 200 steps/prompt | Llama-3.1-8B | frozen test | 37 | **+0.216 ASR** | — | n/a (within-arm) | **VERIFIED** | single seed at this contrast |
| The StrongREJECT judge flips **5.4 %** of labels on byte-identical inputs | accidental test–retest via transfer diagonal | Llama-3.1-8B | frozen test | 37 | 2/37 labels flipped; generations 37/37 identical | — | n/a | **VERIFIED** | both flips threshold-adjacent (0.375→0.5/0.625) |
