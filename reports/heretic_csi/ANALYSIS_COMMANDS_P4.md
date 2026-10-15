# P4 v2 — exact eval + analysis commands (bundle for commit; nothing submitted before the parent's "committed")

Prereg set: PREREG_P4_DRAFT + AMENDMENTS 1–5 (`outputs/heretic_csi/p2b/prod/p4/`; Amendment 5 = per-rank liveness,
single-job/GPU rule, order, pinning, provenance). Frozen operators: `outputs/heretic_csi/p2b/prod/p4/factors_p4v2_<cw>_r<R>.pt`.
Fit-side summary (committed S-203): `reports/heretic_csi/P4V2_FIT_SUMMARY_final.json` — TOP8 mid-pack vs random head sets
in all four cells ⇒ a P4 null is the expected outcome.

## Submission (one job per codeword × rank × split; a5000; ≤3 concurrent P4 jobs; global GPU cap 6)
```
sbatch [-w n-501|n-503 only if a matching GPU is free] research/heretic_csi/slurm/p2b_job.slurm \
       outputs/heretic_csi/p2b/plans/p4v2_<cw>_r<R>_<train|val>.sh
```
Order: (1) basket TRAIN-K4: `p4v2_basket_r1_train.sh`, `p4v2_basket_r4_train.sh`; analyse + log. (2) button TRAIN-K4 (secondary
transfer): `p4v2_button_r1_train.sh`, `p4v2_button_r4_train.sh`; analyse + log. (3) VALIDATION (`..._val.sh`, same frozen
factors) only after the matching TRAIN read is logged. Each wave only after the parent's "committed". Each job: 132 arms
(4 liveness BASE/KO/KO_FULL/KO_IDENT + TOP8 + BASE_TOP8 + 6 descriptive + 60 RAW + 60 NC), `--no-requeue`, DONE_MARKER +
`P4V2_PLAN_DONE`, `[p2b] arms ok 132/132`, one attempt.

## Analysis (run only after BOTH ranks of a codeword×split have DONE + 132/132)
TRAIN-K4 (population 268 rows):
```
python research/heretic_csi/p4_analyze_v2.py --codeword <cw> --prefix hcsi_p4v2_<cw>_train_k4 --split train \
   --expect-n 268 --ranks 1,4 --n-rh8 60 --out reports/heretic_csi/p4v2_<cw>_train_k4.json
```
VALIDATION (230 rows / 23 domains):
```
python research/heretic_csi/p4_analyze_v2.py --codeword <cw> --prefix hcsi_p4v2_<cw>_validation --split validation \
   --expect-n 230 --ranks 1,4 --n-rh8 60 --out reports/heretic_csi/p4v2_<cw>_validation.json
```
Decision rule (frozen): per rank p = max(p_RAW, p_NC) (TOP8 must beat BOTH 60-control families); Holm over ranks {1,4};
PASS iff Holm p < 0.05 AND recovery CI-lo > 0 AND gates; VOID / gate-failed / degenerate rank ⇒ the other rank is
INCOMPLETE (never PASS); VOID unless every arm of a rank is from one job and one GPU type, factor sha256 matches the frozen
file, hooks fired on all operator arms incl. TOP8 and KO_IDENT, A is zero outside declared heads, controls disjoint from TOP8,
NC norms == TOP8. Floors: p_r ≥ 1/61 = 0.0164; Holm over 2 ⇒ attainable PASS requires TOP8 strictly first against both
families at one rank. Strict Holm over 4 tests is reported only (cannot reach 0.05 with 60 controls).

## Code shas (to be recorded again in each job's code snapshot)
- research/heretic_csi/p4_analyze_v2.py  bfee75ec1de5b396144fda39a06df1dfaced6a7dbcbb0d2c9e70fb9e557a313a
- research/heretic_csi/p3p4_emit.py      3d6b438f64ad8c686edc05c96ba2389ba731d9b5f1940d1cea2f7583d5fe7f70
- research/heretic_csi/p4_head_fit_v2.py 1c559ed93ef9bdef4b47403a2202905914ee6bbe30a73fbf09d06c3b68bf793d
- research/heretic_csi/slurm/p2b_job.slurm (job wrapper, unchanged since P2b) + research/heretic_csi/p2b_runner.py / p2b_emit.py (P2b, committed)

## Cost
≈72 GPU-h total: TRAIN-K4 ≈ 9.7 GPU-h per job, VALIDATION ≈ 8.3 GPU-h per job (≈227 s/230-row arm, ≈ +0.2 h stage-in).
First wave (basket TRAIN-K4 r1+r4) ≈ 19.4 GPU-h on 2 GPUs.
