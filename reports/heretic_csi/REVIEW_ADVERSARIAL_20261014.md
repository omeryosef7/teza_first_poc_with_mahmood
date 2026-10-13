# HERETIC-CSI — Adversarial review of P2b / Phase-A/B / P6-probe code and log S-051…S-063

**Reviewer:** independent adversarial subagent, 2026-10-14 ~00:30. **Mode:** read-only on code and data. No commits and
no SLURM submissions. The CPU checks were throwaway scripts in the session scratchpad.
**Scope:** p2b_{operator,fit,runner,emit,analyze,freeze}.py, lora_utils.py, slurm/p2b_job.slurm, tests; positions.py,
operator_ara.py; phaseA/phaseB/semantic_installation_scorer; p6_heldout_probe.py; verify_s049.py (skimmed only); the
running outputs of jobs 1023012, 1023251 and the smoke 1022701.

## Severity-ranked findings

### CRITICAL-1 (BUG, imminent production failure): SHUF domain derangement cannot be built on the full TRAIN population
`p2b_fit.py:85-95` `shuffle_plan` uses rejection sampling. It reshuffles all 670 rows up to 1000 times and stops when
no row is paired with a row from its own domain. With 67 domains × 10 rows, each row has a ~10/670 chance of a
same-domain partner, so P(no collisions) ≈ e^-10 ≈ 4.5e-5 per draw and ≈4% per seed over 1000 draws.
**Reproduced on the real production row order** (from the KO run dirs `hcsi_p2b_cap_{basket,button}_KO_*`) with the
real seeds `1000*r+j`. **Only 7 of 35 (rank, j) seeds succeed for each codeword. Seed 1000 (r=1, SHUF0) FAILS for both.**
- Consequence: job **1023012** will `SystemExit("could not build a domain derangement")` in the basket final fit at
  r=1 right after the CAND+NEUT fit. `set -euo pipefail` then aborts the plan, so no factors are saved for any rank
  and evalA never runs.
- Job **1023264** (`job2_evalA_button.sh`) will then hold a GPU while it polls for up to 4 h (120×120 s) before it
  `exit 3`.
- The unit test (`tests/test_p2b_operator.py:135`) uses 6 domains × 4 rows, and the smoke used 12 rows, so neither
  could trigger this.
- **Fix:** build the derangement constructively. For example, permute the domain list, map domain k → k+1
  cyclically (a domain-level derangement), then pair rows across the mapped domains (all domains have 10 rows).
  Add a test at the 67×10 scale.
- The CV outputs (`cv_*.json`, `freeze_pooled.json`) survive the crash, so a rerun can use `--freeze <obj:w>` and skip
  the ~2.5 h of CV.

### CRITICAL-2 (BUG + design): the analyzer can return PASS for an operator that makes installation *worse*. The rank family is a damage null, not a rescue null.
- **The prereg pass rule is not implemented.** PREREG_P2B `pass_rule` = "rank p < 0.05 AND recovery CI lower bound > 0".
  `p2b_analyze.py:106-108` decides PASS on `rp["p"] < 0.05` alone. `recovery_CAND["ci95"]` is computed (l.90) but never
  gated.
- **Why this matters (smoke 1022701, 12 rows, plumbing only, n_steps 5; numbers from the run dirs):**

  | arm | KO | KO_CAND_r4 | KO_RAND_r4_0 | KO_RAND_r4_1 | KO_SHUF_r4_0 | KO_FULL |
  |---|---|---|---|---|---|---|
  | y | 0.399 | 0.332 | 0.230 | 0.148 | 0.116 | 0.587 |

  Norm-matched random and shuffled operators at ‖ΔW‖≈172 do heavy damage (Δy −0.17 to −0.28). The candidate has
  *negative* recovery (≈ −0.36) yet is the strictly largest of the 4 controls. Under the current analyzer that pattern
  scales to "PASS rank 1/52".
- The Frobenius-matched controls therefore test "is CAND less destructive than a random edit of the same size?". That is
  not a test of rescue (see also RISK-6).
- **Fix (must land before any eval read):** enforce `recovery_CAND.status=="ok" and ci95[0] > 0` in the verdict. Report
  `stat_CAND_minus_KO` against 0 next to the rank.

### HIGH-3 (RISK): option-mass collapse under an operator is not screened, so y_install becomes meaningless
- `p2b_analyze.py:56` builds the key set once, from **BASE** option mass only. That choice is correct for pre-treatment
  attrition, but nothing flags an operator arm whose readout collapses.
- Smoke example: `KO_NEUT_r4` had option mass 7.9e-5 and y = 0.992, which reads as a "rescue" of 1.5× KO_FULL. That is a
  degenerate ratio of two near-zero probabilities.
- A random control at matched norm can collapse the same way and fake a high or low y in either direction.
- **Fix:** keep the BASE key set as the primary rule, but add a declared per-arm validity gate. For example, the median
  option mass of the arm must be ≥ 0.05 on the common keys, or the arm is reported as INVALID-READOUT (not dropped
  silently).

### HIGH-4 (RISK, interpretation): "position-aware" applies only to the fit. The edit acts at every position, including the readout row.
- `OperatorHooks` (`p2b_operator.py:223-249`) adds ΔW·x at all positions, including the "Answer:" and readout rows. The
  prereg declares this (`caveats_declared[1]`), so it is consistent with the claim as written.
- Any "the codeword row carries it" reading is unsupported, though. The fit's preserve set (`p2b_fit.py:109-111`) covers
  clean cw, last and 6 random rows, never the readout/"Answer:" rows. So the operator is unconstrained exactly where
  y_install is read. A rescue can come from editing the readout row, for example by suppressing the " basket"/" button"
  logit, which is lexical, not semantic.
- **Required diagnostic before any mechanism language:**
  1. A position-restricted application of the same factors (hook adds ΔW·x only at the codeword row).
  2. A split of logp_concept versus logp_codeword. A rescue driven by a *drop* in logp_codeword is codeword
     suppression, not installation.

### HIGH-5 (RISK): NEUT is not a valid position control. It contrasts norm, not position.
- NEUT is fit at the last row with its own norm: ‖ΔW‖ 2.6 versus CAND 172 in the prereg, about 1.5% of CAND's size.
  `CAND − NEUT` is then mostly a norm difference.
- Excluding NEUT from the rank family is acceptable *only* if it is never quoted as a position contrast. S-060 and the
  prereg call it a "position control". It should be labelled "MEASURED, norm-confounded".
- A defensible position control needs a matched *effect* rather than matched Frobenius norm. Either fit both sites to
  the same achieved gap-closure fraction, or match ‖ΔW·x‖ on held-out rows.
- This applies to the mandate §10 item "neutral-position optimization", which is currently unmet in substance.

### HIGH-6 (RISK): unmatched norm confounds remain within the rank family
- Frobenius-norm matching (`rescale_to`, exact; norm guard 1e-3 at `p2b_analyze.py:82`) is correct as implemented:
  rank, modules, layers and #params all match.
- But CAND's A rows align with the high-variance input subspace at these modules, while RAND's A is isotropic. The two
  therefore differ in *functional* magnitude ‖ΔW·x‖ on real activations.
- **Recommendation:** record ‖ΔW·x‖ on the preserve and eval inputs per arm (the sidecar already stores
  `mean_last_pos_delta_norm`; extend it to the codeword and readout rows). Report recovery against that norm.
- SHUF adds a per-prompt **role swap** with p=0.5 (`p2b_fit.py:106-107`). This pushes half the rows clean→KO, so the
  fitted direction approximately cancels the mean KO→clean shift. That makes SHUF a deliberately weak null and not the
  mandate's "shuffled source↔target domain pairing". Run a pure domain-deranged KO→clean SHUF as the specificity
  control, since it is the one that tests domain-matching.
- With 46 RAND and only 5 SHUF, the family is dominated by random directions. Also report `rank_test_fitted_only`, which
  is already computed and has a 1/6 floor, so readers see that the fitted-null comparison is FLOOR-LIMITED.

### HIGH-7 (RISK, power/multiplicity): the prereg cannot support a multiplicity-corrected rank claim
- The design is 7 ranks × 2 codewords with "min sufficient rank = smallest passing r" and no correction. That gives
  P(at least one false pass among 7 ranks under the null) ≈ 1 − 0.95^7 ≈ 30% per codeword. The minimum rank is also
  biased downward.
- A Bonferroni threshold over 7 ranks is 0.0071, which is below the 51-control floor of 0.0192. By plan §5 (P-rule) a
  corrected claim is **FLOOR-LIMITED as designed**.
- Fix: either ≥140 controls per rank on VALIDATION, or a single preregistered primary rank per codeword (as S-051 did).

### MEDIUM-8 (RISK): fit/deploy mismatch (teacher forcing) and a selection criterion that favours mse
- Every module is fit on inputs captured with **no upstream edit**, but all 26 modules are deployed jointly. Corrections
  compound across layers (overshoot), and the CV criterion (`gap_closure` on captured I/O) is blind to this.
- The criterion is itself an MSE gap, so it structurally favours `mse`/`whiten` over `cos`/`knn`. The "comparison of
  formulations" (mandate §8) is not neutral.
- Cheap check: capture module I/O *under* the deployed operator and report the deployed gap closure per layer.

### MEDIUM-9 (RISK): provenance — running jobs use code that is not committed
- `p2b_operator.py` was modified at 23:41, after 1023012 started at 22:46. The change makes `random_norm_matched` rescale
  in float64. It is uncommitted in `git status`, and every later python invocation in the job (button CV, fits, the
  runner's RAND generation) imports the new version.
- `phaseB_native_ara.py` was modified at 23:38 (adds `--cross-codeword`) and is also uncommitted. 1023251 started at
  23:42 and runs it.
- The fix itself is correct. Without it, the analyzer's 1e-3 norm guard would have VOIDed every RAND arm (smoke: 172.25
  vs 171.9). **Commit before any eval read**, and record the code sha that the runs actually used.

### MEDIUM-10 (RISK): design changes after reading the smoke endpoint
- Two changes were made after F2 saw the smoke's y and option mass on TRAIN-K4 rows, which are the same population as
  the TRAIN eval: the preserve set was widened to 6 extra rows (smoke BASE_CAND_r4 y fell 0.732 → 0.417), and NEUT was
  dropped from norm-matching (smoke NEUT option mass 8e-5).
- This is TRAIN-side tuning and allowed by plan §5. But the prereg's statement that the smoke "had been read [as]
  plumbing-only" is inaccurate. Declare it, and treat TRAIN-K4 P2b results as non-quotable (VALIDATION decides).
- Separately, smoke BASE_CAND_r4 Δy = −0.32 on clean prompts is a large preservation failure. Watch `BASE_CAND_minus_BASE`
  in production.

### MEDIUM-11 (Phase B / scorer)
- `semantic_installation_scorer.py`: `Settings.option_mass_floor` is declared but **never applied**; `domain_mean` uses
  all rows. Phase B therefore *maximizes* y_install on opt_A (cell A, base y ≈ 0.0002) with no readout-validity floor.
- The cheapest way to raise y = σ(logp_bomb − logp_button) on A-cell prompts is a global "bomb > button" lexical bias.
  The cross-codeword read added today is the right check, but it is MEASURED and was added mid-run (MEDIUM-9).
- Any Phase-B "ARA installs" reading must show option mass and the logp_concept versus logp_codeword split.

### LOW-12 (requeue/DONE)
- `p2b_job.slurm` uses `--no-requeue` and prints `DONE_MARKER … rc=$RC` unconditionally. That is fine, provided
  validators require `rc=0`.
- The runner's skip-if-done (`--expect-n`) calls `strict_run_dir` without `allow_short`. A legitimately short arm is
  therefore re-run, which creates a second dir, and analysis will then refuse.
- A capture arm skipped on resume does not re-create a missing `.pt` if the kill landed between DONE.json and
  `torch.save`. The fit would fail loudly in that case, which is safe.
- `job2_evalA_button.sh` holds a GPU while sleep-polling for up to 4 h (a waste of GPU time).

## Answers to the 10 questions

| # | Verdict | Evidence |
|---|---|---|
| 1 Positions | **OK** (capture) / **RISK** (claim) | `p2b_runner.py:111-131` strips the "Answer:" ids (refuses if the tail mismatches) and resolves bare rel_end −10 with `require_codeword_match` (LOUD decode). `signals.py:720-725` right-pads, so batch-row-0 prefix positions are exact. `p2b_fit.py:66-72` cross-checks KO `seq_len == bare_len` and `surface_span_positions == [anchor]` per row, so the KO site and the capture site coincide. The −10/−12 issue from S-005 is handled. Application is at all positions (declared), but the unconstrained readout row means "codeword-row operator" language is unsupported (HIGH-4). |
| 2 Pairing/leakage | **OK** for leakage, **BUG** for SHUF | CAND pairs the KO and clean versions of the *same prompt*, so it is domain-matched. `p2b_fit.py:73` refuses any non-train row per row via `dcs_ts116_domain_split.json` (`lpm.SPLIT_MANIFEST`). CV folds are domain-grouped (l.128-131). RAND norms come from the TRAIN CAND. No VAL/TEST in fit, CV or controls. SHUF derangement crashes (CRITICAL-1) and has a role swap (HIGH-6). |
| 3 Controls | rank/norm/#params **OK**. SHUF **BUG/RISK**. NEUT **RISK**. p-floor **OK**. | `rescale_to` is exact (test l.159). Per-module 1e-3 guard and rank guard at `p2b_analyze.py:79-86`. `p = (1+#{ctrl ≥ cand})/(N+1)` with ties counted against the candidate, floor 1/52 (l.95-98). The NEUT exclusion hides a norm confound if NEUT is quoted as a position control (HIGH-5). SRC2SRC/TGT2TGT and KO_IDENT are zero **by construction** (B=0 has zero gradient at a perfect match), so they verify plumbing only and do not count as the mandate's "source→source" control in substance. |
| 4 Freeze | **OK** | `p2b_fit.py` reads only `domain/seq_len/surface_span_positions/prompt_id` from results.jsonl. CV uses `gap_closure` on module I/O. `p2b_freeze.py` reads `cv[*].net` only. No y_install on the selection path (caveat: MEDIUM-10). |
| 5 Statistic | **OK**, with one **BUG** | Domain means over the common keys. `rederive.recovery_fraction` uses a domain-cluster bootstrap, a \|den\| ≥ 0.01 guard, ≥3 moving domains, and a sign guard in `effect_fraction`. KO_FULL−KO ≈ 0.11-0.14 historically, so not degenerate. The CI>0 rule is missing (CRITICAL-2). |
| 6 Norm confound | **RISK, not excluded** | Smoke: matched-norm random edits move y by −0.17 to −0.25 and option mass from 0.23 to 0.41. Size alone moves the endpoint strongly, so the rank test against the norm-matched family partly measures damage (CRITICAL-2, HIGH-6). |
| 7 Held-out probe | statistic **OK**, wording **overclaim** | Re-ran rank 1 with 400 within-domain shuffles (scratch; reproduces real ρ exactly). basket ρ=0.533, null mean 0.005, **SD 0.26**, q95 0.434, max 0.497 (p=1/401). button ρ=0.574, null SD 0.261, q95 0.428, max 0.512 (p=1/401). The shuffle is not too constrained and the centring does not leak: X and y are centred per domain on their own split and the fit is TRAIN-only. The wide null is real: a rank-1 PLS on permuted labels picks directions biased toward the top PCs, and y_install correlates with single train PCs on VAL (\|ρ\| up to 0.40 basket PC2, 0.37 button PC3). It shrinks with rank (null max 0.06-0.2 at r≥8). The real rank-1 margin over the null is therefore modest, and with only 20 shuffles p = 0.048 (floor). "C1 not supported" is fair *only* as "no evidence of a basket advantage". "Equal held-out decodability" is not shown: there is no paired difference test, the CIs are ±0.1 and cannot resolve the S-043 +12% (~0.06) gap, and ρ comparisons across codewords are confounded by different y variance (button installs more strongly). The correct label is CANNOT ANSWER (underpowered for the difference). |
| 8 Requeue/DONE | **OK / LOW** | See LOW-12. |
| 9 Overclaims | **RISK** | S-054 "occurs at equal held-out decodability ⇒ C1 not supported" overstates (Q7). S-060 and the prereg call NEUT a "position control" (HIGH-5) and SHUF a "shuffled pairing" (it is role-swap + derangement and currently crashes). The prereg says "the smoke … plumbing-only, never quoted", but design choices were driven by smoke y/option mass (MEDIUM-10). S-058 "KO_IDENT == KO exactly" is true but vacuous (zero B). S-051/S-052 handle the TRAIN r4 pass correctly (labelled not-a-finding, prereg'd). S-062 #1 (lora_A persists after reset) is **verified** in source: `heretic/model.py:313` zeros only `lora_B`, and `ara.py:320-321` L-BFGS mutates `[lora_A, lora_B]` in place. |
| 10 Tests | 23 pass (poc_stage2) + 5 pass (heretic_csi env) | `pytest research/heretic_csi/tests -q` **fails collection** in poc_stage2: `test_lora_utils_and_scorer.py` imports `heretic` (ModuleNotFoundError). Excluding that file gives 23 passed in 4.7 s. That file passes 5/5 under `/specific/scratches/.../envs/heretic_csi/bin/python`. Suggest `pytest.importorskip("heretic")`. |

## Proposed mutation tests (would the current code catch them?)
1. **Real-scale derangement:** call `shuffle_plan` on 67 domains × 10 rows with seeds `1000*r+j`. **Not caught today.**
   It fails 28 of 35 seeds; this is CRITICAL-1.
2. **Damage-only candidate:** in a synthetic `analyze_rank`, set the CAND arm to y = KO − 0.05 and all controls to
   KO − 0.2. The expected verdict is DOES NOT PASS (recovery CI < 0). **Not caught today**: the analyzer returns PASS
   1/52 (CRITICAL-2).
3. **Codeword-row off-by-one:** set `REL_END_CODEWORD_ROW` to −9 or −12, or drop the "Answer:" strip. **Caught**:
   `anchor_from_rel_end` raises on the decode mismatch, and `load_pairs` refuses on `surface_span_positions !=` anchor.
   A VALIDATION-domain row injected into a capture is also **caught** (`p2b_fit.py:73`).
(Also add: an arm with collapsed option mass, which should be flagged and is **not caught** today; see HIGH-3.)

## Bottom line
- No leakage and no position bug in the capture path. The freeze is clean.
- **P2b production will crash** at the SHUF derangement (CRITICAL-1).
- **Even when fixed, a "PASS" from the current analyzer would not mean rescue** (CRITICAL-2, HIGH-3), and the matched
  controls cannot isolate position or specificity (HIGH-4/5/6).
- Fix 1-3 and commit the working-tree code before any P2b endpoint is read. Treat any P2b rank claim as FLOOR-LIMITED
  under multiplicity unless the control count is raised or one rank per codeword is preregistered.
