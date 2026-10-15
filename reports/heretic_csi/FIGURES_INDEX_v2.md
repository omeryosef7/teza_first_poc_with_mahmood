# Figures & tables index (mandate §28.4) — interim v2, 2026-10-15

Supersedes `FIGURES_INDEX.md` (v1 kept). v2 figures carry per-cell status annotations and gap-fraction units (review #9).

| §28.4 item | File(s) | Status |
|---|---|---|
| Rescue vs rank (weight operator) | `P2B_RANK_CURVE_TRAIN.png` (panel A), `P2B_RANK_CURVE_TRAIN.md/.json` | DESCRIPTIVE (TRAIN-K4, in-sample), S-188 |
| Rescue vs rank (activation space) | **`fig_p2a_val_specificity_v2.png`** (per-cell status: CONFIRMED / SUGGESTIVE / fail / descriptive-fragile; shuffled-label controls shown separately); data: `hcsi_p2a_basket_r1.json`, `hcsi_p2a_basket_r4_validation.json`, `hcsi_p2a_basket_r16.json`, `hcsi_p2a_button_r1.json`, `hcsi_p2a_button_r4ext_validation_analyzer.json`, `hcsi_p2a_button_r16.json` | VALIDATION cells r1/r4/r16 (button r4 = powered 200-control family), S-049/S-073/S-126/S-198. **Do not glob `hcsi_p2a_*.json`** — it also matches the non-production S-013 files `hcsi_p2a_basket_r4.json` / `_r32.json`. `RANK_TABLE_train.md` is stale (10-03, untracked) and is not used |
| Preservation vs rank | **`fig_p2b_preservation_vs_rank_v2.png`** — both panels as a fraction of the BASE−KO gap, labelled axes, explicit rank ticks {1,2,4,8,16,32,50}, ±5%-of-gap band on the deployed panel, "point estimates, no CI" note | DESCRIPTIVE, TRAIN-K4, in-sample, S-188. **KL and refusal were not measured as preservation endpoints** |
| Basket vs button | both v2 figures (side-by-side panels); contrast numbers in `P2A_BUTTON_R4_CONTRAST_v2.json` | contrast NOT supported (sign is control-family dependent), S-097/S-098. Note the unequal common-row counts (basket 133–145 vs button 193–203 on VAL) |
| Singular spectra / effective rank | `P3_SVD_REPORT_v2.md`, `P3_svd_descriptive_v2.json`, `P3_write_direction_v2.json` | DESCRIPTIVE, S-079/S-089 |
| Cumulative SVD rescue (minimal subspace) | `P3_TRUNC_READ_VOID.md`, `p3_basket_r4_validation.NOT_QUOTABLE.md` | **VOID — no figure may be made from these numbers**, S-176/S-180 |
| Layer / component search | `P3_SVD_REPORT_v2.md` (norm by layer and by o_proj/down_proj) | DESCRIPTIVE; no causal layer test run |
| Head-restricted vs full-module edits | `P4V2_FIT_SUMMARY_partial2.json` (partial, 13–16 of 60 controls), `P4_HEAD_RESTRICTED_DESIGN_v2.md` | **PENDING** (fit-side only, in-sample, not an endpoint). Refresh from `P4V2_FIT_SUMMARY_final.json` when the last fit lands |
| Codeword frequency / probe quality vs required rank | `hcsi_p6_codeword_table.json`, `hcsi_p6_heldout_probe_*.json`, `P6_CODEWORD_PROVENANCE_AND_DESIGN.md` | **PENDING** (needs P6 rescue stage) |
| Alignment vs causal circuit | `P3_alignment_aniso.json` | DESCRIPTIVE null result, S-089/S-097 |
| P6 gate table (G1/G2/G3 per codeword) | **`P6_GATE_TABLE_interim.md`** (generated snapshot), plus `hcsi_p6_g2_*.json`, `hcsi_p6_bank_checks.json`, `hcsi_p6_occ_check.json` and the per-codeword manifests | interim snapshot of 16 codewords with a Stage-0 result; regenerate when Stage-0 completes |
| Native ARA control | `phaseB/PHASEB_SUMMARY.md`, `phaseB/PHASEB_{basket,button}.md` | MEASURED control, S-077/S-083 |

Generator: `research/heretic_csi/make_interim_figures.py` (CPU). It reads committed report JSONs for both figures; the
P6 gate table additionally reads the per-codeword manifests under `outputs/heretic_csi/p6/` (a snapshot, not in git).
v1 figures (`fig_p2a_val_specificity.png`, `fig_p2b_preservation_vs_rank.png`) are superseded but kept.
