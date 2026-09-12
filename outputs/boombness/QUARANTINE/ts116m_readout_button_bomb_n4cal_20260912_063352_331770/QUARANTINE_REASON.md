# CANCELLED -- wrong hardware. Kept with provenance (mandate section 53), not deleted.

Job 882126. Cancelled by me at ~30 minutes, after 770 of ~4640 rows, because its RUNMETA showed it
running on a **Tesla V100-SXM2-32GB** (rack-bgw-dgx1) rather than the **Quadro RTX 8000**
(rack-omerl-g01) that job 881787 used for dose 8.

## Why that made it useless rather than merely different

The run exists to supply the OVERLAPPING DOSE the dose ladder lacks: dose 4 measured under the dose-8
configuration, so that `dose4_here - dose4_there` is the cross-run offset (CONT-ENTRY 100, 102). A
third GPU produces a second uncalibrated comparison instead of closing the first.

Cause: the sbatch carried `--exclude=n-801,n-307`, which constrains where the job may NOT run. I had
written it as though it pinned where it SHOULD run.

## What is kept

config.json, RUNMETA.json, the 770 rows it did persist, and this file. The rows are a valid partial
readout on a V100 -- they are simply not the measurement that was wanted, and nothing cites them.

## Superseded by

Job 882136, identical flags plus `--nodelist=rack-omerl-g01`. Verified before resubmission:
`git diff 2c6fbff9a9 HEAD -- src/boombness/score_behavior.py doublespeak_causality/ds_common.py` is
empty, so the readout code is byte-identical and GPU/node is the only difference the calibration has
to absorb.
