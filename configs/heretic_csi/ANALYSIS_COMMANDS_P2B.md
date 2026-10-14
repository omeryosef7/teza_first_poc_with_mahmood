# P2b analysis commands (EXACT) — frozen before any P2b TRAIN/VALIDATION endpoint read

Pre-registration chain: `outputs/heretic_csi/p2b/prod/PREREG_P2B.json` → `_AMENDMENT_1` → `_AMENDMENT_2` →
`PREREG_P2B_VALIDATION.json` → `_AMENDMENT_3` → `_AMENDMENT_4` → `_AMENDMENT_5` (sha256s in AMENDMENT_5).
Run from the repo root with `PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`.
**Order (amendment 3/5): the TRAIN read waits until the TRAIN add-on jobs and the overlap jobs are DONE.**
**VALIDATION decides outcomes A–E (amendment 5); TRAIN-K4 is in-sample/descriptive.**

## Code these commands assume (sha256; verify with `sha256sum` before running — a mismatch means re-review)

| file | sha256 |
|---|---|
| research/heretic_csi/p2b_analyze.py | `5bafd09223526ca5d34f9a1f3b4dfc88726bff13700b5e174606e92a2985a62a` (supersedes c1b11327…: amendment-7 `--neutpos` block + review-5 DESCRIPTIVE fields `fraction_of_BASE_minus_KO_restored`, `CAND_minus_mean_DER`, `CAND_minus_KO_ci`; no verdict logic changed; the TRAIN read S-135 ran c1b11327…) |
| research/heretic_csi/p2b_overlap_check.py | `4552d70fd6aec349fdb66f65b521d6f452776f35cfdfecd6df550a843513a490` |
| research/heretic_csi/p2b_deployed_residual.py | `ba2057bdcec9d4256540bc74c0482f78d1d6db58bb97a101c03d53ca518ce533` |
| scripts/dcs_csi_subspace_analyze.py (reused helpers) | `8a9e16944cc4dbc41bcec72e54c6162389dfe9f3eba4a4f852b134d9c09d556e` |
| scripts/dcs_csi_rederive_patch.py | `99aef3c2de5038c15fd54bb4a8e991af249d25b58acc07058933451635b509b0` |
| scripts/dcs_cont_layerpos_map.py | `0ee17c99ae55b4c3e47753979c0303d265bb3d1a65d1ceba1434852ed476aa22` |

## Overlap files (amendment 5) — produced by the jobs; use EXACTLY these (if a job is resubmitted the attempt suffix changes: use the file whose job DONE_MARKER rc=0 and verdict OVERLAP_OK)

- basket r1 resume (n-501 vs preempted 1023012 n-503): `outputs/heretic_csi/p2b/prod/overlap_basket_1035278_r0.json`
- button r1 resume (in-allocation vs preempted 1023264): `outputs/heretic_csi/p2b/prod/overlap_button_1035131_r0.json`
- add-on TRAIN (in-allocation KO vs the liveness job): `outputs/heretic_csi/p2b/prod/overlap_addon_<cw>_k4_<ATTEMPT>.json`
- button n-501 vs preempted 1023264 n-503 (CODEWORD-SPECIFIC, parent S-117; covers button r4 = n-501 arms + n-503
  liveness): `outputs/heretic_csi/p2b/prod/overlap_buttonn501_1035278_r0.json` (job 1035278, pinned n-501, tags
  hcsi_p2b_button_k4ovln501_*). The basket overlap file is NOT used for button.
- REVISION 2026-10-14 (before any TRAIN read): this replaced the earlier cross-codeword coverage of button r4.

## TRAIN (K4: 268 rows / 67 domains; in-sample, DESCRIPTIVE) — primary + secondary + add-on

```
$PY research/heretic_csi/p2b_analyze.py --codeword basket --prefix hcsi_p2b_basket_k4 --split train --expect-n 268 \
  --ranks 1,4 --nrand 61 --nshuf 5 --nder 15 --capop --cw-nrand 61 --cw-nder 15 --addon \
  --overlap outputs/heretic_csi/p2b/prod/overlap_basket_1035278_r0.json,outputs/heretic_csi/p2b/prod/overlap_addon_basket_k4_<ATTEMPT>.json \
  --out reports/heretic_csi/p2b_basket_primary_train.json

$PY research/heretic_csi/p2b_analyze.py --codeword button --prefix hcsi_p2b_button_k4 --split train --expect-n 268 \
  --ranks 1,4 --nrand 61 --nshuf 5 --nder 15 --capop --cw-nrand 61 --cw-nder 15 --addon \
  --overlap outputs/heretic_csi/p2b/prod/overlap_button_1035131_r0.json,outputs/heretic_csi/p2b/prod/overlap_buttonn501_1035278_r0.json,outputs/heretic_csi/p2b/prod/overlap_addon_button_k4_<ATTEMPT>.json \
  --out reports/heretic_csi/p2b_button_primary_train.json
```

## VALIDATION (230 rows / 23 domains; DECIDES A–E) — primary + secondary + add-on

```
$PY research/heretic_csi/p2b_analyze.py --codeword basket --prefix hcsi_p2b_basket_val --split validation --expect-n 230 \
  --ranks 1,4 --nrand 61 --nshuf 5 --nder 15 --capop --cw-nrand 61 --cw-nder 15 --addon --neutpos \
  --overlap outputs/heretic_csi/p2b/prod/overlap_addon_basket_val_1040101_r0.json \
  --out reports/heretic_csi/p2b_basket_primary_validation.json

$PY research/heretic_csi/p2b_analyze.py --codeword button --prefix hcsi_p2b_button_val --split validation --expect-n 230 \
  --ranks 1,4 --nrand 61 --nshuf 5 --nder 15 --capop --cw-nrand 61 --cw-nder 15 --addon --neutpos \
  --overlap outputs/heretic_csi/p2b/prod/overlap_buttonvaln501_1040170_r0.json,outputs/heretic_csi/p2b/prod/overlap_addon_button_val_1040122_r0.json \
  --out reports/heretic_csi/p2b_button_primary_validation.json
```
REVISION 2026-10-14 (before any VALIDATION read): VAL overlap files fixed.
- basket VAL main arms all on n-503 (1023578, 1023579): no main overlap needed. The add-on job 1040101 (n-501)
  carries an in-allocation KO overlap vs 1023578 → `overlap_addon_basket_val_1040101_r0.json`.
- button VAL r1 + liveness on n-503 (1036679), r4 on n-501 (1036680). Required n-501↔n-503 coverage on the VAL
  population comes from job 1040170 (plans/ovl_button_val.sh: KO, KO_CAND_r1, KO_RAND_r1_0, KO_DER_r1_0 re-run on
  n-501 vs 1036679) → `overlap_buttonvaln501_1040170_r0.json`; add-on 1040122 (n-501) → `overlap_addon_button_val_1040122_r0.json`.
- `outputs/heretic_csi/p2b/plans/ovl_template.sh` was generalized to POP=val (POP unset = k4, unchanged); sha256 `d80f283b4e18ec909ad5957d07ef9386e3d75efa056de1b83d250a2c44611763`.
- If an attempt suffix changes (resubmission), use the file whose job DONE_MARKER rc=0 and verdict OVERLAP_OK.

## Amendment 6 — DESCRIPTIVE MEANBIAS_NM (run AFTER the primary read; never unlocks wording)

Same frozen command as the primary read for that split, with `--addon-nm` appended and the add-on-NM overlap file
added to `--overlap` (TRAIN: `outputs/heretic_csi/p2b/prod/overlap_addonnm_<cw>_k4_<ATTEMPT>.json` from the
plans/addon_nm_k4.sh job), written to a separate output, e.g. `reports/heretic_csi/p2b_<cw>_meanbias_nm_train.json`.
Only `out["addon_nm"]` is new; the primary/secondary verdicts must be identical to the primary read's.

## Amendment 7 — DESCRIPTIVE NEUT position arms on TRAIN (separate output; never changes a verdict)

The frozen TRAIN command for that codeword with `--neutpos` appended and the new add-on overlap file from the
plans/neutpos_k4.sh job added to `--overlap`, written to `reports/heretic_csi/p2b_<cw>_neutpos_train.json`.
Only `out["neut_position"]` (+ the review-5 descriptive fields) is new; verdicts must equal the S-135 read's.

## Deployed-vs-fitted residual (descriptive; per codeword × rank ∈ {1,4})

```
$PY research/heretic_csi/p2b_deployed_residual.py --capop outputs/heretic_csi/p2b/prod/capop/capop_<cw>_r<R>.pt \
  --clean outputs/heretic_csi/p2b/prod/cap/cap_<cw>_BASE.pt --ko outputs/heretic_csi/p2b/prod/cap/cap_<cw>_KO.pt \
  --factors outputs/heretic_csi/p2b/prod/fac/factors_<cw>_r<R>.pt --out reports/heretic_csi/p2b_<cw>_r<R>_deployed_train.json
# VALIDATION capop files: outputs/heretic_csi/p2b/prod/capop_val/capop_<cw>_r<R>.pt  (clean/KO captures are TRAIN-only, so the
# validation deployed residual is NOT computable without validation captures -- report TRAIN only; stated, not hidden.)
```

## Outcome mapping (amendment 5) — computed from the VALIDATION JSONs only
"specific at r" = primary verdict starts with `PASS` at r (INCOMPLETE/VOID/CANNOT ⇒ not decidable).
A = basket@1 AND button not@1 but @4 · B = both @1 · C = neither @1, both @4 · D = basket @1 or @4, button neither ·
E = neither codeword at either rank · any VOID/INCOMPLETE/CANNOT ⇒ CANNOT ANSWER · other patterns reported literally.
Minimal specific rank per codeword ∈ {1, 4, ">4 (untested beyond)"}.
