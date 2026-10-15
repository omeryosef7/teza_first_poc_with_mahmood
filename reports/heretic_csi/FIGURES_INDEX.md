# Figures & tables index (mandate §28.4) — interim, 2026-10-15

| §28.4 item | File(s) | Status |
|---|---|---|
| Rescue vs rank (weight operator) | `P2B_RANK_CURVE_TRAIN.png` (panel A), `P2B_RANK_CURVE_TRAIN.md/.json` | DESCRIPTIVE (TRAIN-K4, in-sample), S-188 |
| Rescue vs rank (activation space) | `fig_p2a_val_specificity.png`, `RANK_TABLE_train.md`, `hcsi_p2a_*.json` | VALIDATION cells r1/r4/r16 (button r4 = powered 200-control family), S-049/S-073/S-126 |
| Preservation vs rank | `fig_p2b_preservation_vs_rank.png` (fit-side damage; clean-prompt Δy) | DESCRIPTIVE, S-188 |
| Basket vs button | both figures above (side-by-side panels); contrast numbers in `P2A_BUTTON_R4_CONTRAST_v2.json` | contrast NOT supported (sign is control-family dependent), S-097/S-098 |
| Singular spectra / effective rank | `P3_SVD_REPORT_v2.md`, `P3_svd_descriptive_v2.json`, `P3_write_direction_v2.json` | DESCRIPTIVE, S-079/S-089 |
| Cumulative SVD rescue (minimal subspace) | `P3_TRUNC_READ_VOID.md`, `p3_basket_r4_validation.NOT_QUOTABLE.md` | **VOID — no figure may be made from these numbers**, S-176/S-180 |
| Layer / component search | `P3_SVD_REPORT_v2.md` (norm by layer and by o_proj/down_proj) | DESCRIPTIVE; no causal layer test run |
| Head-restricted vs full-module edits | `P4V2_FIT_SUMMARY_partial2.json`, `P4_HEAD_RESTRICTED_DESIGN_v2.md` | **PENDING** (fit-side only; evaluation not run) |
| Codeword frequency / probe quality vs required rank | `hcsi_p6_codeword_table.json`, `hcsi_p6_heldout_probe_*.json`, `P6_CODEWORD_PROVENANCE_AND_DESIGN.md` | **PENDING** (needs P6 rescue stage) |
| Alignment vs causal circuit | `P3_alignment_aniso.json` | DESCRIPTIVE null result, S-089/S-097 |
| P6 gate table (G1/G2/G3 per codeword) | `hcsi_p6_g2_*.json`, `hcsi_p6_bank_checks.json`, `hcsi_p6_occ_check.json`, manifests | interim; consolidated table deferred until Stage-0 completes |
| Native ARA control | `phaseB/PHASEB_SUMMARY.md`, `phaseB/PHASEB_{basket,button}.md` | MEASURED control, S-077/S-083 |

Generator for the two new figures: `research/heretic_csi/make_interim_figures.py` (CPU, reads committed report JSONs only).
