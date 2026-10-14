# P2b analysis commands (EXACT) — frozen before any P2b TRAIN/VALIDATION endpoint read

Pre-registration chain: `outputs/heretic_csi/p2b/prod/PREREG_P2B.json` → `_AMENDMENT_1` → `_AMENDMENT_2` →
`PREREG_P2B_VALIDATION.json` → `_AMENDMENT_3` → `_AMENDMENT_4` → `_AMENDMENT_5` (sha256s in AMENDMENT_5).
Run from the repo root with `PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`.
**Order (amendment 3/5): the TRAIN read waits until the TRAIN add-on jobs and the overlap jobs are DONE.**
**VALIDATION decides outcomes A–E (amendment 5); TRAIN-K4 is in-sample/descriptive.**

## Code these commands assume (sha256; verify with `sha256sum` before running — a mismatch means re-review)

| file | sha256 |
|---|---|
| research/heretic_csi/p2b_analyze.py | `0104b4544ba6907424f2ca47d291f9163f2ae89e93d850a2da0b2e4268d4f399` |
| research/heretic_csi/p2b_overlap_check.py | `4552d70fd6aec349fdb66f65b521d6f452776f35cfdfecd6df550a843513a490` |
| research/heretic_csi/p2b_deployed_residual.py | `ba2057bdcec9d4256540bc74c0482f78d1d6db58bb97a101c03d53ca518ce533` |
| scripts/dcs_csi_subspace_analyze.py (reused helpers) | `8a9e16944cc4dbc41bcec72e54c6162389dfe9f3eba4a4f852b134d9c09d556e` |
| scripts/dcs_csi_rederive_patch.py | `99aef3c2de5038c15fd54bb4a8e991af249d25b58acc07058933451635b509b0` |
| scripts/dcs_cont_layerpos_map.py | `0ee17c99ae55b4c3e47753979c0303d265bb3d1a65d1ceba1434852ed476aa22` |

## Overlap files (amendment 5) — produced by the jobs; use EXACTLY these (if a job is resubmitted the attempt suffix changes: use the file whose job DONE_MARKER rc=0 and verdict OVERLAP_OK)

- basket r1 resume (n-501 vs preempted 1023012 n-503): `outputs/heretic_csi/p2b/prod/overlap_basket_1035278_r0.json`
- button r1 resume (in-allocation vs preempted 1023264): `outputs/heretic_csi/p2b/prod/overlap_button_1035131_r0.json`
- add-on TRAIN (in-allocation KO vs the liveness job): `outputs/heretic_csi/p2b/prod/overlap_addon_<cw>_k4_<ATTEMPT>.json`
- Button r4 mixes n-503 (liveness, 1023264) and n-501 (1023509): covered by the basket overlap file (n-501 vs n-503
  host equivalence, cross-codeword evidence — stated in the report); both files are passed.

## TRAIN (K4: 268 rows / 67 domains; in-sample, DESCRIPTIVE) — primary + secondary + add-on

```
$PY research/heretic_csi/p2b_analyze.py --codeword basket --prefix hcsi_p2b_basket_k4 --split train --expect-n 268 \
  --ranks 1,4 --nrand 61 --nshuf 5 --nder 15 --capop --cw-nrand 61 --cw-nder 15 --addon \
  --overlap outputs/heretic_csi/p2b/prod/overlap_basket_1035278_r0.json,outputs/heretic_csi/p2b/prod/overlap_addon_basket_k4_<ATTEMPT>.json \
  --out reports/heretic_csi/p2b_basket_primary_train.json

$PY research/heretic_csi/p2b_analyze.py --codeword button --prefix hcsi_p2b_button_k4 --split train --expect-n 268 \
  --ranks 1,4 --nrand 61 --nshuf 5 --nder 15 --capop --cw-nrand 61 --cw-nder 15 --addon \
  --overlap outputs/heretic_csi/p2b/prod/overlap_button_1035131_r0.json,outputs/heretic_csi/p2b/prod/overlap_basket_1035278_r0.json,outputs/heretic_csi/p2b/prod/overlap_addon_button_k4_<ATTEMPT>.json \
  --out reports/heretic_csi/p2b_button_primary_train.json
```

## VALIDATION (230 rows / 23 domains; DECIDES A–E) — primary + secondary + add-on

```
$PY research/heretic_csi/p2b_analyze.py --codeword basket --prefix hcsi_p2b_basket_val --split validation --expect-n 230 \
  --ranks 1,4 --nrand 61 --nshuf 5 --nder 15 --capop --cw-nrand 61 --cw-nder 15 --addon \
  --overlap <every overlap JSON produced by the val/addon_val jobs if they span >1 host> \
  --out reports/heretic_csi/p2b_basket_primary_validation.json

$PY research/heretic_csi/p2b_analyze.py --codeword button --prefix hcsi_p2b_button_val --split validation --expect-n 230 \
  --ranks 1,4 --nrand 61 --nshuf 5 --nder 15 --capop --cw-nrand 61 --cw-nder 15 --addon \
  --overlap <as above> --out reports/heretic_csi/p2b_button_primary_validation.json
```
(If the VALIDATION arms all ran on one host, `--overlap` may be empty; the analyzer VOIDs any cross-host cell lacking coverage.)

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
