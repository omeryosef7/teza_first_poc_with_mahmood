# ADVERSARIAL REVIEW #8 (h), 2026-10-15: P6 G2, DEV draw, P3 VOID handling, overclaims S-166 to S-178, pending risks

Reviewer: independent subagent. Read-only on existing files. No commits, no SLURM jobs, no P4 eval outputs read (none exist).
Scratch scripts: `$SCRATCH/review8/g2_recompute.py` (independent G2 recompute + provenance checks) and
`$SCRATCH/review8/dev_dry.py` (DEV-draw dry runs). Both run with poc_stage2 python `-I`.
Severity: BUG-M > RISK-M > OVERCLAIM-M > BUG-L > RISK-L > OK.

## Summary (ranked)

1. **RISK-M: the DEV draw has no driver and no guards.** It can be run on a partial or unverified survivor set, and it can be run more than once.
   - `research/heretic_csi/p6_dev_draw.py:32-63`: `draw(install_strength, survivors)` accepts any dict and list. It does not read manifests. It does not check G1 (ci95[0] > 0.05), G2 == PASS or G3 == PASS. It does not check that all 20 untouched codewords have a terminal gate status. It has no write-once output.
   - The docstring (`:4`) says "applied AFTER Stage-0 covariates exist". Under AMENDMENT_5 it must say after **G2** for all 20 untouched codewords.
   - Dry runs show the draw is deterministic and independent of input order. It drops non-pool words (candle, basket) silently. The fill rule works (2 of 5 filled in a sparse case). It raises SystemExit for fewer than 5 survivors. It uses only pre-rescue covariates (Zipf and TRAIN C−A); no outcome is used.
   - The draw is sensitive to the survivor set. A run on today's 9 known survivors gave a different DEV than a run on 20 (the 5th pick changed: ladder vs whistle). Perturbing a single codeword's G1 changed DEV in 13 of 20 cases, because G1 moves the median.
   - A NaN strength is accepted silently and corrupts the median. A missing strength raises a bare KeyError.
   - No status field encodes G1 or G2: every manifest still says `status: G3_PASS`, including the 4 that passed G2.
   - **Fix:** add `p6_dev_draw_run.py`, committed before use. It should:
     - read all 20 `stage0_<cw>.json` manifests;
     - refuse unless every one is terminal (G3_FAIL, ERROR, or G1 and G2 evaluated);
     - take strength = `g1.install_strength_C_minus_A`, and survivors = G1 ci95[0] > 0.05 ∧ g2.G2 == PASS ∧ g3 PASS;
     - reject NaN and missing values;
     - write `reports/heretic_csi/hcsi_p6_dev_draw.json` with the input manifest sha256s, refusing if the file already exists;
     - be committed and logged before any rescue arm.
   - The draw procedure itself (frozen tertiles 7/7/6 with ZIPF equal to `hcsi_p6_codeword_table.json` for all 20 words, median split, seed, fill) is correctly specified under AMENDMENT_5. Candle is not in the 20-word pool, so the maximum confirmation n stays 15.

2. **RISK-M: hardware for the P6 rescue stage is not pinned.** No P6 rescue slurm exists yet. PREREG_P6 `stage0.hardware` allows "a5000/l40s/3090".
   - Everything P6 so far ran on **L40S**: all Stage-0 readouts and extractions (12 G3-passers plus candle), all 16 G2 arms (job 1041401, t-806), and G2 job 1041561 (n-805), which also requests `l40s:1`.
   - The incumbents ran on different hardware: the basket/button VAL rescue on **A5000**, the TRAIN rescue on 3090 and L40S.
   - S-062 and the P4/P3 checks already found that cross-GPU readouts differ at the row level.
   - **Fix (pre-registration-grade, before any rescue arm):** run every P6 rescue job (liveness plus candidate plus 56 controls, per codeword) as one job on `l40s:1`. VOID any codeword whose arms span more than one job or GPU type; this is the same rule as the new P4 analyzer. Record the GPU type per codeword in the H6a table. Comparisons with basket/button (A5000) are cross-hardware and descriptive only.

3. **RISK-M: power and dependence.** 12 of 20 untouched codewords are G3-passing so far, and 8 are still pending (jacket, ribbon, sponge, whistle, yogurt, banana, chair, balloon).
   - A **single** attrition anywhere puts n_conf below 15, which pre-labels H6a "UNDERPOWERED for ρ<0.8" (AMENDMENT_2/3).
   - Even at n = 15, IUT power at ρ = 0.7 is only 0.57–0.72.
   - Sources of shared noise that inflate or mask H6a:
     - the rank-1 random controls are byte-identical across codewords (S-167);
     - lamp cand_rank1 · basket cand_rank1 = 0.63 (review g), a shared codeword-general component;
     - probe and outcome share the VAL domains (declared, AMENDMENT_3c).
   - **Fix:** keep these three dependencies in the H6a write-up. Precommit (now) the exact sentence for n_conf < 15, and the rule that a non-pass is never a null.

4. **OVERCLAIM-M: S-176 interprets a VOID read.** The log says the numbers are "MEASURED, NOT QUOTABLE", and the VOID report labels them correctly. But S-176 then adds "Pattern (descriptive only): a rank-1-dominated operator whose effect follows its leading component — consistent with the P3 shared mean-gap write direction."
   - That is the forbidden S-176 addendum claim ("effectively rank-1") in softer words, drawn from an invalid read. It is also confounded by design: TOP1 keeps 0.915 of the norm, and the null is random edits only.
   - The "Diagnosis: float32 SVD re-expression perturbs factors slightly; the readout amplifies it" is stated as fact in both S-176 and `P3_TRUNC_READ_VOID.md` (Lesson 1), but it was not tested. Factor-level REEXP vs CAND differs by only 3.7e-8 (rel). An equally plausible mechanism is bf16 re-rounding of W+ΔW. Run-to-run nondeterminism was not excluded either: own KO == ref KO exactly, but that arm has no weight edit.
   - **Fix:** append a correction striking the "Pattern" sentence, and relabel the diagnosis "untested hypothesis". Also add a top-level `"not_quotable": true` to the `truncation_tests`, `removal` and `recovery` blocks of `reports/heretic_csi/p3_basket_r4_validation.json`; the JSON currently carries those numbers with only `void`/`minimal_sufficient_k` set.

5. **OK: P3 stays VOID, and that is correct under the frozen rules.**
   - The 0.01 per-row tolerance was frozen in PREREG_P3_TRUNC_ERRATUM (`reexp_vs_cand`) before the read. Max |Δ| = 0.072, so the read is VOID.
   - Re-preregistering on the seen VAL data would be outcome-informed, and S-176 rightly refuses it.
   - The measured table in the log is labelled "MEASURED, NOT QUOTABLE (invalid read)", which is adequate apart from item 4.
   - Residual note: the tolerance was frozen after job 1041078 started (70/133 arms done) but before any read. This is disclosed and acceptable.

6. **OK (verified independently): P6 G2 for lamp, kettle, pencil and ladder.** I wrote my own code (numpy, 20,000 domain-cluster resamples, a different seed from the in-job evaluator) and read the raw run dirs of job 1041401:

   | cw | KO−BASE | KO_FULL−KO | KO_SELF−KO |
   |---|---|---|---|
   | lamp | −0.2268 [−0.2569, −0.1972] | +0.1339 [0.1153, 0.1528] | −0.0009 [−0.0018, 0.0000] |
   | kettle | −0.2250 [−0.2483, −0.2014] | +0.1425 [0.1262, 0.1587] | −0.0004 [−0.0014, 0.0004] |
   | pencil | −0.2480 [−0.2781, −0.2179] | +0.1468 [0.1269, 0.1674] | +0.0005 [−0.0001, 0.0011] |
   | ladder | −0.1106 [−0.1360, −0.0869] | +0.0484 [0.0366, 0.0606] | +0.0000 [−0.0003, 0.0004] |

   - The points match `hcsi_p6_g2_*.json` to 1e-5 and the CIs to ≤0.001. All four PASS, far from the boundary. The manifest `g2` equals the report minus its `validation` block.
   - **Population:** every arm has exactly 670 rows and 67 domains. The prompt-id set equals, exactly, the population computed from each codeword's own bank (sow / natural_doublespeak / n4 / cds_n4_sow minus `exclude_<cw>_bomb_sow_train.txt`). All rows are in TRAIN under the frozen split file. The domain set is identical to the incumbent basket TRAIN rescue. No logp is missing, and no hook liveness violation occurred. The rescue fired on all rows of KO_SELF and KO_FULL and on none of BASE or KO.
   - **Invocation:** the RUNMETA argv, ignoring bank/model/exclude/tag, is **identical** to the incumbent basket liveness arms (`hcsi_p2a_basket_{BASE,KO,KO_SELF,KO_FULL}_*_2469285`). It uses seed 20260913, bf16, eager, readout-max-batch 1, KO `demo_all:attn_knockout:6-14:1.0` with `target_surface_row_only`, and rescue at query positions with `--rescue-layer 18` and donor self/clean. It also matches `research/heretic_csi/slurm/rescue_sweep.slurm:83-99` line for line.
   - **Wrong codeword: none.** For each codeword, the bank and exclusion paths contain cw, every row has `target_surface == cw`, and `surface_span_tokens == [' cw']`. In metadata, `readout_ids.codeword.primary_id` equals the PREREG token_id (29062, 73418, 47218, 36865), and the concept id is 13054 ' bomb'.
   - **Code:** the code snapshot sha256s equal AMENDMENT_5 (`p6_g2.py` 1920a5a7…, `p6_g2.slurm` c36ebec8…).
   - **PASS rule:** `p6_g2.py:58` (CI upper < 0 ∧ CI lower > 0) equals the frozen G2 text (PREREG_P6 `gates_mechanical.G2`) as implemented in AMENDMENT_5.

7. **BUG-L: S-178 compares with the wrong incumbent population.** "≈ the incumbents (basket KO −0.30, FULL +0.14)" quotes basket **VAL** numbers (23 domains, A5000; log L1382/L2074/L2456). The matching **TRAIN** 670-row incumbent (jobs 1885463/2629822, L40S) is KO−BASE **−0.235**, FULL−KO **+0.124**. "Ladder about half (weak installer, G1 0.15)" implies a cause. **Fix:** cite the TRAIN incumbent figures, and write "ladder smaller; it also has the lowest G1" (correlational).

8. **BUG-L (process): G2 job 1041401 was submitted (05:22:01) 48 s before its code commit 886bda58 (05:22:49).** The P3 erratum promised that "endpoint-producing jobs are submitted only after the parent confirms the commit". The impact is nil: the job was held, started at 06:53, and its snapshot shas equal the committed files. But the rule was broken again. **Fix:** enforce it in the submit wrapper by refusing to submit if `git status --porcelain` shows the script dirty or the HEAD does not contain the shas.

9. **RISK-L: G2 evaluator and manifest robustness.**
   - `p6_g2.py:34-42` drops rows with a missing logp and intersects keys, but does not assert `n_paired_rows ==` the population size. That matters for bottle/cushion `_occ` (fewer than 670 rows).
   - It has no codeword guard, unlike the hardened `p6_g3.py`.
   - Manifests are updated by non-atomic read-modify-write from three writers (`p6_g2.py:59-60`, `p6_axisfit.slurm:47-53`, `p6_write_manifest.py:12-29`).
     - A concurrent axisfit and G2 on the same codeword can lose `g2` or `axis`.
     - A Stage-0 re-run rewrites the manifest and moves `g2` into `previous_manifest`.
   - **Fix:** assert the row count against the exclusion-derived population; guard `target_surface` and metadata codeword; write via a temp file plus `os.replace` under `flock`; set `status` to `G2_PASS` or `G2_FAIL`.

10. **RISK-L: P4 pre-eval state.** `research/heretic_csi/p4_analyze_v2.py` has an **uncommitted** modification (`git diff`: liveness now per-rank job; VOID on mixed job/GPU). No P4 v2 eval prereg is committed (the newest is `PREREG_P4_AMENDMENT_4.json`, Oct 14). The direction of the diff is right. **Fix:** commit the analyzer, then freeze a prereg pinning its sha256 and the GPU type, and only then submit. Cross-rank curves that span jobs and GPUs are descriptive only.

11. **LOW wording/hygiene (S-166 to S-178):**
    - "P(>0.05) = 0.32" (S-167, from review g) is a bootstrap fraction, not a probability. Write "32% of domain-bootstrap resamples have median > 0.05".
    - S-172 lists blanket as a plain "PASS". Carry "borderline (0.056 [0.039, 0.066])" wherever blanket appears in the attrition table.
    - "Survivors" is now used correctly: only for G1–G3 (S-178), and as a definition in S-168. S-172/S-173 correctly say "G3-passing" or "G3+G1 PASS".
    - "KO_SELF inert everywhere" is fine (|Δ| ≤ 0.0009), but lamp's CI upper bound is +1e-5, so call it "≈0 (≤0.001)".
    - No new P2b claims beyond the verified outcome D and the marginal r4 PASS.
    - Header timestamps again run ahead of the wall clock: S-176, S-177 and S-178 are headed 08:55, 09:00 and 09:15, but were committed at 08:40, 08:43 and 08:44. Clock-check the headers, since they carry pre-read ordering claims.
    - Ops: `nvidia-smi` in `p6g2_1041401.out` lists 8 L40S GPUs. Device cgroup constraint may be off on t-806. torch uses `CUDA_VISIBLE_DEVICES`, so this is not a result issue.

## Concrete fixes before the DEV draw and the P6 rescue stage (in order)
1. Add the DEV-draw driver (item 1) and commit it. Draw only after all 20 untouched codewords are terminal through G2.
2. Pin rescue hardware to L40S, with one job per codeword and VOID on mixing (item 2). Add this as a P6 implementation note before any rescue arm.
3. Add the G2 row-count assert, codeword guard, atomic manifest writes and G2 status (item 9) before evaluating 1041561.
4. Append log corrections for items 4, 7 and 11. Add `not_quotable` flags to the P3 JSON.
5. Make commit-before-submit mechanical (item 8). Commit the P4 analyzer and its prereg before the P4 eval (item 10).
