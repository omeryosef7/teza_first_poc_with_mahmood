# Phase B — native last-position Heretic ARA as a CONTROL (MEASURED baseline; TRAIN-tuned, validation read once)

**Question:** is generic end-of-prompt operator editing (Heretic ARA as shipped, module I/O at `[:, -1, :]`) sufficient
for codeword *installation*? A context-free output bias counts as **NO**.
**Answer: NO.** Native ARA produces a strong, controlled-specific shift in `y_install`, but it is a context-free
"answer *bomb*" output bias, not installation of the concept into the codeword.

Jobs: basket 1023185 (Phase A gate PASS → Phase B), button 1023251, basket-factor replay 1023386 (all L40S, eager bf16,
Heretic 662e4ba2, rank 50). Freeze rule v1 (KL ≤ 1.0 on TRAIN opt_C, max TRAIN opt_A y; NO option-mass clause — see
PROVENANCE_v1_jobs.md). Populations: configs/heretic_csi/phaseB/<cw>/MANIFEST.json (TRAIN 67 domains fit/tune; VALIDATION
23 domains read once; TEST never read). good=TARGET=cell C (natural_doublespeak), bad=SOURCE=cell A (benign_literal).

| | basket | button |
|---|---|---|
| chosen TRAIN trial (layers) | 5 (L6–30) | 13 (L9–31) |
| val_A y base → ARA (dY) | 0.000 → 0.925 (+0.925) | 0.000 → 0.796 (+0.796) |
| rank vs 42 rank-matched controls (39 spectrum-matched random + 3 label-shuffled ARA) | 1/43, p = 0.023 (= floor) | 1/43, p = 0.023 (= floor) |
| control dY range | ≤ 6e-5 | −3e-4 … 3.5e-3 |
| val_C (installed) y base → ARA | 0.402 → 0.279 (−0.124) | 0.673 → 0.562 (−0.111) |
| Δlogp(bomb) / Δlogp(codeword) on val_A | +13.9 / −4.1 | +13.4 / −0.2 |
| median option mass val_A base → ARA | 0.108 → 0.115 | 0.061 → 0.319 |
| median option mass val_C base → ARA | 0.078 → **0.036 (< 0.05)** | 0.265 → 0.213 |
| first-token KL, val_C | 0.85 | 1.02 |
| first-token KL, val_A (benign literal) | **4.55** | — |
| keyword refusal (secondary, 46 behavioral val-C) | 0.065 → 0.022 | 0.196 → 0.087 |
| same params refit at rank 1 / rank 8: dY val_A | 0.000 / +0.426 (val_A med OM 0.032 < floor) | +0.753 / +0.477 |

**Why this is not installation (MEASURED specificity reads):**
1. **Cross-codeword transfer.** The *button*-fit edit applied to *basket* prompts: val_A +0.995, val_C **+0.530**
   (larger than on button's own prompts). The *basket*-fit edit on button prompts: val_A +0.182, val_C −0.542.
2. **Wrong-concept contexts.** Basket edit on basket/**knife**-context installed prompts: P(bomb vs basket) +0.395 >
   P(knife vs basket) +0.289; on **gun** contexts: bomb +0.272 > gun +0.215 — the edit pushes "bomb" regardless of the
   concept the context installed (option mass collapses there: median 0.139 → 0.009, 83–92% of rows below 0.05).
3. **It lowers y on correctly-installed prompts** (val_C −0.12 / −0.11) and degrades the basket val_C readout below the
   option-mass floor.
4. Large distribution damage on benign prompts (first-token KL 4.55 on basket val_A).
5. Mechanistically expected: native ARA's capture site is the last prefill token = the answer position, so the edit
   acts on the output, not on the codeword row where the CSI causal site lives (§9 audit; VOID-2 for any installation
   claim).

**Replay / determinism:** saved basket factors replayed on another L40S node reproduce dY val_A = 0.925265216835395 and
val_C = −0.12379 exactly; the chosen trial's TRAIN objective replays with |diff| = 0 (lora_A restored).

**Caveats:** v1 freeze rule lacked the option-mass clause (chosen trials are not collapsed on val_A, but basket val_C is);
the 42-control family is at its p-floor (0.023) so "rank 1" is the strongest attainable; the controls show only that the
edit is not a generic random perturbation — they do NOT address the answer-bias alternative, which the specificity reads
decide. basket_knife:val_A is byte-identical to basket:val_A (cell A prompts do not depend on the concept) — duplicate read.
Rank-1/8 refits are descriptive.

Per-codeword detail: PHASEB_basket.md, PHASEB_button.md; replay JSON: REPLAY_basket_factors_specificity.json.
