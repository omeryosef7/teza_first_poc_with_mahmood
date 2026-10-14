# P6 Stage 0 — READY (CPU prep done; no GPU job submitted)

Prereg: `configs/heretic_csi/PREREG_P6.json` (sha256 998fc25d444c5230c19b11eaf7c5ab9fc01e687d923f83db70b3e13ac8e21022).
Checks: `reports/heretic_csi/hcsi_p6_bank_checks.json` (`research/heretic_csi/p6_check_banks.py`).

## Per-codeword bank table (21 built; envelope excluded mechanically; carrot excluded)

| codeword | role | Zipf | tertile | token id | single-token | rel−10 ok/40 | rows | domains | rescue pop (rows/dom) | repair | collisions after repair | rows_sha16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| candle | DEV-forced | 3.88 | — | 38899 | True | 40 | 22272 | 116 | 1160/116 | taper | 0 | 76b3580ee5863e25 |
| lamp | untouched | 4.05 | high | 29062 | True | 40 | 22272 | 116 | 1160/116 | lantern | 0 | 9879eaffc04516a4 |
| kettle | untouched | 3.54 | low | 73418 | True | 40 | 22272 | 116 | 1160/116 | none | 0 | b3490c1e9c8eac93 |
| pencil | untouched | 3.95 | mid | 47218 | True | 40 | 22272 | 116 | 1160/116 | none | 0 | 033cf40ef996011e |
| ladder | untouched | 4.03 | mid | 36865 | True | 40 | 22272 | 116 | 1160/116 | scaffold | 0 | 7108d9b4340c783d |
| blanket | untouched | 4.07 | high | 39139 | True | 40 | 22272 | 116 | 1160/116 | quilt | 0 | 9d53a98b5386b471 |
| bucket | untouched | 4.07 | high | 15994 | True | 40 | 22272 | 116 | 1160/116 | pail | 0 | 3fa9a573a7026417 |
| pillow | untouched | 3.96 | mid | 43425 | True | 40 | 22272 | 116 | 1160/116 | bolster | 0 | 601a3435666e9508 |
| saddle | untouched | 3.73 | low | 61858 | True | 40 | 22272 | 116 | 1160/116 | harness | 0 | 3d866982d64afb62 |
| wagon | untouched | 3.9 | mid | 61519 | True | 40 | 22272 | 116 | 1160/116 | none | 0 | 32fc853496203ecd |
| cushion | untouched | 3.58 | low | 45738 | True | 40 | 22272 | 116 | 1160/116 | pad | 0 | 8b049a7e9a7c6620 |
| curtain | untouched | 3.86 | low | 46866 | True | 40 | 22272 | 116 | 1160/116 | drape | 0 | ba6f47e83af798b9 |
| bottle | untouched | 4.57 | high | 16893 | True | 40 | 22272 | 116 | 1160/116 | flask | 0 | 54a31ffe91884c1d |
| jacket | untouched | 4.32 | high | 27300 | True | 40 | 22272 | 116 | 1160/116 | coat | 0 | 3dd7e1eafd015f5a |
| ribbon | untouched | 3.81 | low | 45667 | True | 40 | 22272 | 116 | 1160/116 | tape | 0 | 1a2afc40d945039b |
| sponge | untouched | 3.59 | low | 69448 | True | 40 | 22272 | 116 | 1160/116 | none | 0 | e8d5ba09425c8786 |
| whistle | untouched | 3.88 | mid | 40649 | True | 40 | 22272 | 116 | 1160/116 | horn | 0 | 0fb6f476ef3caab2 |
| yogurt | untouched | 3.63 | low | 55575 | True | 40 | 22272 | 116 | 1160/116 | custard | 0 | 212556060ae08261 |
| banana | untouched | 4.0 | mid | 44196 | True | 40 | 22272 | 116 | 1160/116 | mango | 0 | 283be91cce1afdfc |
| chair | untouched | 4.69 | high | 10716 | True | 40 | 22272 | 116 | 1160/116 | seat | 0 | fe5e447bb26fe874 |
| balloon | untouched | 3.9 | mid | 47856 | True | 40 | 22272 | 116 | 1160/116 | kite | 0 | 95474588a2f4a8ea |

All 21: shape identical to basket's bank (22,272 rows; by_block equal; 116 domains). `occurrence_analysis_safe=False` on 7,424 rows per bank — **identical in basket/button** (structural property of the semantic_forced_choice rows), not a defect.

**envelope — EXCLUDED, mechanical, pre-GPU.** Vowel-initial: the generator's exact-word-swap invariant fails ('a bomb' → 'a envelope'), 3,248 alignment violations under `--strict`; nothing written. Fixing it would require changing the generator (articles) for one codeword — not done.

## Reproducibility of the tooling
- Bank builder reproduces basket's ts116m bank exactly (rows_sha16 1e872cd8cd2f63a5, 22,272 rows).
- Exclusion generators reproduce basket's sow_train / sow_validation / behavioral_train / K4 files byte-identically (id lists).
- Per codeword: `runargs/heretic_csi/p6/exclude_<cw>_{bomb_sow_train,bomb_sow_validation,bomb_behavioral_train,K4}.txt` (84 files; counts 490 / 930 / – / 892 identical to basket). TEST exclusions deliberately not built.

## Job plan (not submitted)
1. `sbatch research/heretic_csi/slurm/p6_stage0.slurm <cw>` — ONE allocation per codeword: bank-hash check vs meta → stage model from the verified mirror → base readout (incumbent argv) → SLIM extraction (layer 18 only) → move extraction dir to `/specific/scratches/scratch/omeryosef/hcsi_p6/extract/` + symlink → manifest `outputs/heretic_csi/p6/stage0_<cw>.json` → `DONE_MARKER`. a5000, `--no-requeue`, code snapshot + SHA256SUMS. Dry-run 21/21 OK.
2. `sbatch research/heretic_csi/slurm/p6_axisfit.slurm <cw>` (CPU) — ranks {1,4,16}, 46 random + 10 shuffled controls per rank, seed 20260915, output on scratch. Dry-run OK.
3. Covariates (installer strength from the readout; held-out probe via `p6_heldout_probe.py`) → G1–G3 → `p6_dev_draw.draw()` once, logged → DEV runs → freeze → confirmation.

## Cost
- GPU: readout ~34 min + slim extraction (<33 min; the incumbent's 33 min was 19 layers on V100) + stage-in (5 s warm … ~45 min cold) ⇒ ~1–1.5 GPU-h/codeword ⇒ **~21–32 GPU-h** for 21 codewords. Respect the stage-in stagger rule (S-053): ≤1 cold stage-in at a time, prefer warm nodes.
- Disk: banks 1.5 GB on scratch (home: symlinks + 21 meta files + 84 exclusion files, < 5 MB). Extraction ~0.6 GB/codeword (L18 of a 12 GB 19-layer grid) ⇒ ~13 GB on scratch, transiently ≤0.6 GB on home per running job. Readouts small (home).

## Blockers / caveats
- None blocking. Hardware provenance differs from the incumbents (V100 extraction). Per-codeword pool repairs mean new banks are not byte-aligned to basket/button outside the codeword itself (estimand is per-codeword, so acceptable; declared in the prereg).
- The axis fit on an L18-only corpus is untested end-to-end (code path: `PLATEAU ∩ captured = [18]`, then `--force-layer 18`); first codeword's Stage 0 + axisfit should be inspected before fanning out.
