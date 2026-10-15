# ADVERSARIAL REVIEW #7 (g), 2026-10-15: P6 G3 / Stage-0 / axisfit / G1, P3 truncation code, S-140 to S-165

Reviewer: independent subagent. Read-only on existing files. No commits, no SLURM jobs.
Not read: any `hcsi_p3_*` endpoint (y values), any P4 eval output (none exist).
CPU scratch scripts: `$SCRATCH/review7/{cmp.py,p3chk.py}`, run with poc_stage2 python.

Severity order: BUG-M (medium) > RISK-M > BUG-L > RISK-L > OK.

## Summary (ranked)

1. **RISK-M: P6 DEV draw hard-codes candle, which failed G3.** `research/heretic_csi/p6_dev_draw.py:13,61` always returns `["candle"] + dev`. PREREG_P6 `gates_mechanical.attrition` says "gates applied before any rescue arm is run", and candle is G3_FAIL (`outputs/heretic_csi/p6/stage0_candle.json`). Run as written, the draw puts a gated-out codeword into DEV and so schedules rescue arms for it. **Fix:** before the draw, add a pre-draw implementation note (amendment 5): "DEV = the 5 drawn survivors; candle is a DEV-forced point gated out by G3, kept in the denominator, and gets no rescue arms". Alternatively, make `draw()` take `candle_survives` and drop candle when it is false.
2. **RISK-M: G2 (KO liveness) is not implemented and has no planned job.** PREREG_P6 G2 needs "KO−BASE<0 and KO_FULL−KO>0, CI excl. 0 (TRAIN)". Nothing in `research/heretic_csi/p6_*` or `slurm/p6_*` computes it, and the log keeps calling G3 passers "survivors" (S-146, S-162). The DEV draw takes G1–G3 survivors. **Fix:** write the G2 job and analyzer and run them on G3∩G1 passers before the draw. Until then, call these codewords "G3-passing", not "survivors".
3. **RISK-M: G3 is a coin flip at the threshold for candle and blanket.** The implementation follows the frozen point rule (see item 7). However, the domain-bootstrap 95% CIs of the G3 median (my calculation, 2000 resamples over 67 TRAIN domains) are:
   - candle 0.048 [0.037, 0.063], P(median>0.05)=0.32
   - blanket 0.056 [0.039, 0.066], P=0.75
   - lamp 0.075 [0.058, 0.101], P≈1.00

   Candle sits 9 rows away from flipping: 48.7% of its rows are >0.05. Batched vs batch-1 readout noise also moves the same 670-row median by ~0.001–0.003 (item 7). S-142's headline "candle FAILS frozen gate G3 (genuine)" therefore overstates it. **Fix:** report "candle G3 FAIL by point rule (0.0481; domain CI includes 0.05)" and do the same for blanket. Do not change the gate.
4. **BUG-M (P3): the REEXP≡CAND sanity check is claimed but not implemented.** `research/heretic_csi/p3_analyze.py:13` (docstring) and the template header say "REEXP must reproduce the frozen CAND (checked via sidecar factors and |stat(REEXP)−stat(KO_CAND_ref)|)". The code has no such argument or check. It also never checks that the sidecar `factors_sha16` equals the trunc file. In the prereg, `gates_and_void` does not list it either, so this is a doc-vs-code mismatch, not a rule breach.
   - Factor-level check (mine): REEXP vs CAND dense ΔW max relative difference is 3.7e-8 over the 26 modules (fp32 re-expression, not bitwise).
   - The trunc file is the one recorded in `sha_basket_r4_validation_1041078_r0.txt` (5cab94e2…).
   - The job's code snapshot equals the current analyzer and generator.

   **Fix:** before the read, add `--cand-ref-stat` = P2b VAL basket r4 KO_CAND stat. Report |Δstat| descriptively (cross-job, same GPU type), and assert that `sidecar.factors_sha16` matches the trunc file. Alternatively, delete the docstring claim.
5. **RISK-M (P3 design): the null is weak, so "k\*" is close to guaranteed.**
   - TOP1 keeps a mean of 86% of the per-module ΔW norm (min 71%). TOP2 keeps 98% (min 91%). σ1² holds a median 78% of module energy.
   - Random rank-k norm-matched operators are the null CAND already beat everywhere (P2b: 1/62 vs random).
   - The null that made basket r4 marginal (fitted DER controls) is not truncated.

   So "Holm p<0.05 and retention CI-lo≥0.5" at k=1 or 2 is expected from the spectrum alone. **Fix:** add the wording "k\* is vs random edits only; it says nothing about the pairing-specific increment". Optionally (descriptive, CPU-cheap), report the same TOPk truncation of the best DER control, e.g. KO_DER_r4_10. DROP_i losses are confounded with norm loss: DROP1 keeps only 47% of the norm (mean). The prereg already says they are descriptive. Add "norm-confounded".
6. **BUG-L: `p6_g3.py` does not check the codeword or completeness.**
   - `p6_g3.py lamp <candle_readout>` returns a G3 for "lamp" computed on candle's rows (0.04806, my run). prompt_id is 100% shared across banks; score_behavior's M3 guard says so. Fix: assert that every readout row's `target_surface`/RUNMETA `--bank` contains `cw`.
   - Rows with `option_mass=None` are dropped silently. Fix: assert `g3_rows_scored == g3_pop_size` (it is 670 = 670 for all 7 codewords now). Make an empty population `ERROR`, not `G3_FAIL` (`:44,49`).
7. **OK: G3 population and statistic match the frozen text.** `p6_g3.py:24-38`: cell C / one-word / n4 / cds_n4_sow minus the TRAIN exclusion file, with `_occ` used first when present. True median with ties averaged. Candle's two middle values are both <0.05 (0.04797, 0.04815), so the tie definition cannot flip it.
   - Verified on the incumbents: the G3 row IDs equal the rescue BASE-arm IDs exactly (670/67, 335 "dev" + 335 "heldout" bank labels, all TRAIN domains) for basket (965561/965624/965928/966084) and button (965562/965625/966157/966158).
   - The values are not identical. Same readout ids (whole_answer), but Stage-0 uses `readout_max_batch 0`, seed 20260816 and other hardware, while BASE uses batch 1 and seed 20260913. Per-row mean |Δ| is 0.006 (basket) and 0.010 (button), max 0.054. Medians: basket G3 0.0883 vs BASE runs 0.0901/0.0873; button 0.3283 vs 0.3293/0.3295.

   So G3 reproduces the BASE-arm *population* exactly and its median to within ±0.002. AMENDMENT_4's "same population" is correct. Do not claim "same values".
8. **OK with gaps: Stage-0 batch, select_run and axisfit.**
   - `p6_select_run.py` selects by RUNMETA job + DONE and rejects symlinks.
   - HEALTH and G3 are separate (`p6_g3.py:43,52`). rc=4 is accepted only through the DONE-dir selection. Extraction runs only when `STATUS==G3_PASS` (`p6_stage0_batch.slurm:170`) and is moved to scratch with a symlink.
   - Axisfit refuses anything but G3_PASS and verifies each dir against its own job (`p6_axisfit.slurm:226-230`).
   - All 7 manifests (candle FAIL; lamp, kettle, pencil, ladder, blanket, bucket PASS) are consistent: readout job = RUNMETA job, DONE present, 5568/5568 rows, 0 failures, identical readout args, all on n-802. Extract realpath is on scratch (715 MB each) with RUNMETA job = `extract_slurm_job`. Lamp: readout 1040225, extract 1040547, both recorded.

   Gaps (BUG-L):
   - The manifest omits the readout rc (0 vs 4) and the extraction rc, which are only in the log.
   - An `ERROR_NO_READOUT_DIR` path `continue`s without writing or refreshing the manifest, so a stale manifest can survive.
   - Stage-in fell back to the NFS mirror in both batches (/tmp 8 GB). The log reports "no failures", which is fine, but S-142's "one model load" is wrong: score_behavior and the extractor are separate processes per codeword.
   - The axis `.pt` lives only on scratch. Its sha256 is only in `p6axis_<job>.out`, and the manifest has no pointer. Fix: record the axis path and sha in the manifest, or copy it to `configs/heretic_csi/` as was done for the incumbents.
9. **OK: lamp axis basis format and TRAIN-only fit.** `/specific/scratches/.../hcsi_p6_axis_lamp.pt` (sha 6937dba6…):
   - It has the same `{meta,bases}` schema and the identical 31 meta keys as `hcsi_ranksweep_basket.pt`.
   - Bases: cand_rank1, cand_pls1..16, ctrl_orth, ctrl_random0-7, ctrl_shuffled0-4, and ctrl_random_r{1,4,16}_0..45 plus ctrl_shuffled_pls{1,4,16}_0..9, 199 in total. All are orthonormal fp32 with the expected ranks.
   - meta: codeword='lamp', selected_layer=18, site='rel-6', fit_prompt='behavioral', bank_sha16=0d603790feda4b9d (the bank sha256 prefix). The score_behavior guards (`score_behavior.py:2372,2382`) will fire, so the r4ext meta gap does not recur.
   - Fit population: split=train, 67 domains, 670 rows. `dcs_csi_axis.py:304-362` enforces TRAIN, refuses VA/TE/EX contamination, and refuses a corpus/readout bank-sha mismatch. VAL rows are in the extract corpus but are not fit.
   - Notes (RISK-L):
     - The layer "argmax" is trivial because only L18 is captured (`layer_grid=[18]`).
     - With the fixed seed, `ctrl_random_r1_*` and `ctrl_random0-7` are byte-identical across all P6 codewords and basket. Random-control noise is therefore shared across codewords in H6a's z, so state this.
     - lamp cand_rank1 · basket cand_rank1 = 0.63. A large shared, codeword-general component means "codeword-specific carrier" wording needs care.
10. **OK: G1** (`p6_install_strength.py`) reproduces lamp 0.5388 [0.4846, 0.5908]. Domain unit, TRAIN via the split file, EX removed, percentile bootstrap 2000 (bs[50], bs[1949]). Minor: `cell not in "AC"` is a substring test (`:15`). The g1 JSON records no readout_dir or sha. Blanket and bucket G1 are not computed yet.
11. **OK: P3 truncation/controls/Holm/minimal-k.**
    - `p3_make_truncations.py` uses an exact SVD of B@A via QR.
    - TOPk/TOPkN/DROPi/REEXP are as preregistered: 9 keys, and 4 + 9 + 40 + 40 + 20 + 20 = 133 arms.
    - Random controls have rank k (rank taken from the key's factors) and are per-module Frobenius-matched to TOPk. My check: max relative norm error 2.9e-8 (TOP1 seed 9000) and 2.6e-8 (TOP2).
    - `rank_p` uses ≥ (ties count against). Holm is over k∈{1,2}. Retention is a domain-bootstrap ratio of means. `minimal_k` = smallest k with Holm<0.05 and CI-lo≥0.5, all as prereg.
    - `p3_gate.py` gives OK for basket r4 and refuses basket r1 (my run).
    - Minor: the template reuses an existing trunc file (`[ -f $TF ] ||`) without checking its source sha, and its header still says "NOT YET SUBMITTED".
12. **Overclaim audit S-140 to S-165.**
    - (a) **PREREG_P3_TRUNC.json `written`: "BEFORE the P3 job is submitted (no hcsi_p3_* score dir exists)" is false.** sacct shows 1041078 submitted 01:35:54, and the commit 83e157b7 is at 01:37:47. S-158 discloses this, but the frozen file still says otherwise. Fix: add an erratum (amendment) to the prereg itself.
    - (b) S-142 "candle FAILS G3 (genuine)": see item 3.
    - (c) S-142 "after one model load": false, see item 8.
    - (d) S-140 "localizes the learned weight edit to the causal site" and "not HOW MUCH" were already corrected in S-157 #4. OK.
    - (e) S-146 "the population the rescue BASE arm scores": true for IDs, not for values (item 7).
    - (f) S-162 and S-146 "survivors" without G2: see item 2.
    - (g) S-156/S-157 P2b VAL wording: the corrections stand, and nothing new was found.

## Concrete fixes (short)
- Before the DEV draw: P6 amendment 5 = candle handling (dropped from DEV rescue, kept in the denominator) plus a G2 implementation and job. G3 verdicts are reported with the domain CI (descriptive).
- `p6_g3.py`: codeword/bank assertion; assert rows_scored == pop_size; empty population → ERROR.
- Manifests: record the readout rc, extraction rc, axis path and sha. Write a manifest on error paths.
- `p3_analyze.py`: implement or drop the REEXP-vs-CAND check, and check the sidecar sha against the trunc file. Add the "vs random only; DER not truncated" and "DROP norm-confounded" wording to the P3 read.
- PREREG_P3_TRUNC: erratum on the `written` field.
