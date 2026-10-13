# VERIFY_S049 — independent re-computation of the HERETIC-CSI P2a headline (S-049) + S-050 K4 r4/r8

**Verifier:** F3 fork (2026-10-13). **Code:** `research/heretic_csi/verify/verify_s049.py`, `research/heretic_csi/verify/check_quarantine.py`
(written from scratch, no reuse of `dcs_csi_subspace_analyze.py` / `analyze_sweep.py`; analyzer read ONLY after numbers to diff).
**Raw data:** score_behavior run dirs referenced by the `[score] ... -> <dir>` lines of `outputs/heretic_csi/logs/sweep_<job>.out`.
**Machine-readable:** `reports/heretic_csi/VERIFY_S049_independent.json`, `reports/heretic_csi/VERIFY_S049_quarantine_check.json`.

## Method (independent)
y_install = logistic(logp_concept − logp_codeword) per row → per-DOMAIN mean per arm → recovery = Σ_d(cand−KO)/Σ_d(FULL−KO)
(equal domain weight), 2000× domain-cluster bootstrap CI. Rank statistic = mean over domains of (arm−KO); rank = 1 + #controls
strictly greater; p = rank/(n+1), n = 56 rank-matched controls (46 random + 10 shuffled-PLS), floor 0.0175.
Option-mass floor 0.05 in three variants: **BASE-ref** (prompt kept iff BASE option_mass ≥ 0.05, held fixed across arms — the
analyzer's rule), **strict** (BASE ∧ KO ∧ KO_FULL ≥ 0.05), **none**.

## Results (rank/57, p, recovery [95% CI])

| cell | split | BASE-ref (≈ analyzer) | strict paired floor | no floor | S-049/S-050 record |
|---|---|---|---|---|---|
| basket r1 | TRAIN (67 dom) | **1/57 p=.0175** rec .029 [.009,.047] | 5/57 p=.088 | 2/57 p=.035 | 2/57 p=.035 rec .028 |
| basket r16 | TRAIN | 10/57 p=.175 rec .167 | 10/57 | 10/57 | 10/57 rec .167 |
| button r1 | TRAIN | 25/57 p=.44 rec −.001 | 23/57 | 23/57 | 23/57 rec −.001 |
| button r16 | TRAIN | 10/57 p=.175 rec .118 | 10/57 | 10/57 | 10/57 rec .118 |
| basket r1 | VAL (23 dom) | **1/57 p=.0175** rec .036 [.013,.065] | 2/57 p=.035 | 1/57 | 1/57 p=.0175 rec .036 |
| basket r16 | VAL | 10/57 p=.175 rec .152 | 10/57 | 10/57 | 10/57 rec .152 |
| button r1 | VAL | 18/57 p=.32 rec .006 | 18/57 | 13/57 | 14/57 rec .008 |
| button r16 | VAL | 10/57 p=.175 rec .118 | 10/57 | 10/57 | 10/57 rec .118 |
| basket r4 | TRAIN-K4 | 3/57 p=.053 rec .132 | 4/57 | 4/57 | analyzer 3/57 rec .1315 |
| basket r8 | TRAIN-K4 | 4/57 p=.070 rec .131 | 5/57 | 5/57 | analyzer 4/57 rec .1306 |
| **button r4** | TRAIN-K4 | **1/57 p=.0175** rec .090 [.068,.114] | 1/57 | 1/57 | analyzer 1/57 rec .0903 |
| button r8 | TRAIN-K4 | 3/57 p=.053 rec .102 | 3/57 | 3/57 | analyzer 3/57 rec .1019 |

## Integrity checks (all cells)
- Populations: BASE rows 670 (TRAIN, 67 dom) / 230 (VAL, 23 dom) / 268 (K4, 67 dom). Every domain in the intended split per
  `dcs_ts116_domain_split.json`; **TEST present: NO** in any cell. Exclusion files = `exclude_<cw>_bomb_sow_{train,validation}.txt`
  / `runargs/heretic_csi/exclude_<cw>_K4.txt`. Codeword surface correct in every row.
- Controls truly rank-matched: matrix_rank of every candidate and all 56 controls in `hcsi_ranksweep_<cw>.pt` = r (r ∈ {1,4,8,16});
  per-row `rescue_liveness.rank` = r for all 57 pool arms; no foreign-rank arms in any pool; all 57 basis keys distinct.
- Norm matching: control written norm vs candidate written norm per prompt, max rel. error ≤ 6e-16 (exact).
- Seed: single seed 20260913 for all arms (controls differ by basis draw, not seed — distinct keys confirmed).
- Short arms: only rank-1 controls lose 1–6 rows (DONE `INCOMPLETE`, reason "norm-match DEGENERATE" refusal) — mechanical,
  declared (S-037 allow-short). r≥4 arms complete.
- Liveness: KO−BASE = −0.21 to −0.30 (manipulation fires); KO_FULL−KO = +0.11 to +0.14; **|KO_SELF−KO| ≤ 0.0008 (inert)**.
- Mutation tests (20 draws each): swap candidate with a random control → median p 0.32–0.54 (typical, as expected);
  shuffle arm identity within domain → median p 0.27–0.66 (signal vanishes). Pipeline can fail its own positive.
- Preemption quarantine (969085, 969088; 14 + 35 dirs moved to `_preempted_attempts/`): independently verified against the
  job logs (which were overwritten on requeue, so they list only the final attempt). For all 12 jobs, the live same-jobid
  dir set == the 61 dirs referenced in the log, 0 quarantined dirs are log-referenced, no duplicate arms. **Rule correct.**

## Agreements / disagreements
- **AGREE (all verdicts):** every S-049 PASS/FAIL is reproduced; recoveries match to ≤0.002 under the BASE-ref floor.
- **Minor rank differences** in rank-1 cells (basket r1 TRAIN 1 vs 2; button r1 TRAIN 25 vs 23; VAL 18 vs 14): traced to rank-1
  controls with norm-match-dropped rows (different domain subsets per arm) and the analyzer ranking on per-control recovery
  ratio with `>=` ties vs my mean-Δ statistic. No verdict changes.
- **ROBUSTNESS CAVEAT (new):** basket r1 is **floor-handling-sensitive**. Under the stricter paired floor (drop a prompt if
  BASE, KO **or** KO_FULL option mass < 0.05; basket loses 42% of TRAIN rows) TRAIN → 5/57 p=0.088 (fail) and VAL → 2/57
  p=0.035 (pass, not strictly largest). The VAL pass survives every variant; "strictly largest" does not. Note the strict
  variant conditions on post-treatment arms (KO, KO_FULL) — the analyzer's R2-B1 argument for BASE-ref is sound — so this is a
  sensitivity, not a refutation.
- **NEW SIGNAL (S-050 K4): button r4 TRAIN-K4 = 1/57, p=0.0175, rec 0.090 [0.068,0.114], under all three floor variants.**
  This contradicts S-049's "button has no specific carrier at any tested rank" for rank 4. Scope: TRAIN, K4 subset, 1 of 4
  ranks tested per codeword (Bonferroni α/4 = 0.0125 < floor 0.0175 → cannot survive multiplicity correction with 56 controls);
  needs validation-split replication before any claim.
- **Artifact hygiene:** the per-cell analyzer JSONs for r1/r16 exist only as un-split `hcsi_p2a_<cw>_r{1,16}.json` (the
  pre-fix split collision); the TRAIN-vs-VAL per-cell files are not both on disk — S-049 TRAIN numbers survive only in the log.
  This verification regenerates both independently.
