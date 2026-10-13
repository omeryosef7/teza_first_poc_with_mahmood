# Phase B provenance for jobs started BEFORE per-job source snapshots existed (2026-10-14)

Code is in `research/heretic_csi/` (uncommitted while these ran; the parent owns commits). Jobs submitted after
the v2 changes copy every `research/heretic_csi/*.py` + `slurm/*.slurm` into `<workdir>/src_snapshot/` and record
sha256s in the output JSON (`source_sha256`).

| job | started | phaseB_native_ara.py version | semantic_installation_scorer.py version |
|---|---|---|---|
| 1023185 (basket, via phaseAB.slurm) | 2026-10-13 23:16 | v1: freeze rule = KL<=1.0 then max opt_A y (NO option-mass clause); no cross-codeword read; LAST_RECS keyed by set name only (no consequence: no cross read in this job) | `READOUT_IMPL=whole_answer_bs1_logits_to_keep/v2`; no option-mass floor fields |
| 1023251 (button, phaseB_native_ara.slurm, cross=basket) | 2026-10-13 23:42 | v1 + `--cross-codeword` read + LAST_RECS keyed by (codeword, set) | same as above |

Differences v1 -> v2 (later jobs): (1) freeze rule v2 adds "opt_A median option mass >= 0.05 (not collapsed)";
(2) every trial records per-scorer option mass (median, frac < 0.05, collapsed, y on BASE-reference keys);
(3) every read reports base-reference-key floored y + denominators; (4) `opt_A` gets a BASE read so its key set is
fixed before any edit; (5) source snapshot + sha256. The y_install readout itself (and therefore every y / dY value)
is IDENTICAL between v1 and v2; v2 only adds reporting fields and the selection clause.

Consequence: Optuna results of 1023185/1023251 are reportable as a MEASURED baseline; their chosen trial was
selected WITHOUT the option-mass clause. The frozen-read JSON does contain `median_option_mass` for every read and
control (v1 recorded it), so any read with median option mass < 0.05 is flagged at report time.
