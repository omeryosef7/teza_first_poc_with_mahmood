# P4 v2 — head-restricted operator after adversarial review #2 (supersedes P4_HEAD_RESTRICTED_DESIGN.md, kept)

## What changed and why
1. **CRITICAL-1 (control handicap).** v1 rescaled each fitted random-8-head control (RH8) to TOP8's per-module norm
   after fitting. TOP8 needs ≈1.8–2.3× the norm of an all-head fit, so the rescale pushed controls far off their
   optimum. **Fitting-side finding (in-sample, not an endpoint):** at their own optimum, random disjoint 8-head sets
   close the codeword-row KO→clean gap as well as TOP8:

   | | TOP8 net | RH8_0 raw | RH8_0 rescaled | RH8_10 raw | RH8_10 rescaled |
   |---|---|---|---|---|---|
   | basket r1 | 0.568 | 0.568 | 0.460 | – | – |
   | basket r4 | 0.615 | 0.618 | 0.581 | 0.611 | 0.579 |
   | button r1 | 0.622 | 0.621 | **0.147** | 0.623 | 0.479 |
   | button r4 | 0.651 | 0.659 | 0.586 | – | – |

   v1 jobs 1023554–7 were cancelled before saving factors (logs `outputs/heretic_csi/logs/p3p4_102355{4..7}.out`).
   **v2** (`research/heretic_csi/p4_head_fit_v2.py`) fits TWO control families per rank: **RAW** (own optimum, raw
   norms reported) and **NC** (same head sets REFIT under ‖BA‖_F = ‖TOP8‖_F per module by reparametrisation
   ΔW = c·BA/‖BA‖_F, initialised at the RAW optimum — so it can only improve on v1's rescaled point; unit-tested).
2. **Decision rule** (`PREREG_P4_AMENDMENT_1.json`, analyzer `p4_analyze_v2.py`): per rank p_r = max(p_RAW, p_NC)
   (intersection-union: TOP8 must beat both); Holm over ranks {1,4}; PASS iff Holm p < 0.05 AND recovery CI-lo > 0
   AND gates, no VOID. Strict Holm over all 4 tests is reported but cannot reach 0.05 with 60 controls per family
   (floor 4/61 = 0.066 ⇒ CANNOT ANSWER as a decisive rule; would need ≥ 81 per family, ≈ +40 GPU-h).
3. **HIGH-2 (incomplete Holm family).** Both `p4_analyze.py` (v1) and `p4_analyze_v2.py` now return
   "INCOMPLETE FAMILY" for every rank if a primary rank is missing/not analyzable; regression tests in
   `tests/test_p3_p4.py`. (`p2b_analyze.py` has the same issue per the review — not my file; flagged to parent.)
4. New VOID checks from the factors file: A exactly zero outside declared heads; control heads disjoint from TOP8;
   NC norms == TOP8; arms applied the declared factors file.
5. **MEDIUM-9.** Added descriptive **TOP8_L6_14** (TOP8 heads, o_proj L6–14 = nomination band). Caveat: the primary
   TOP8 ties heads across L6–18; at L15–18 the head identity has no nomination basis (symmetric for controls).

## Jobs (cpu-killable, 32 CPUs, 2-day limit)
fit: 1023752 basket r1 · 1023754 basket r4 · 1023756 button r1 · 1023758 button r4 → `outputs/heretic_csi/p2b/prod/p4/
factors_p4v2_<cw>_r<R>.pt` + `p4v2_fit_<cw>_r<R>.json` (log `P4V2_FIT_DONE`, trailer `DONE_MARKER p3p4 rc=0`).
cv: 1023753 / 1023755 / 1023757 / 1023759 → `p4v2_cv_<cw>_r<R>.json` (5-fold domain-grouped TRAIN CV, TOP8 vs
RH8RAW_0..19 and RH8NC_0..19; fitting side only).
Before any P4 endpoint: report `_summary.TOP8_rank_among_RAW` / `_NC` and the CV ranks; if TOP8 is not first
among RAW on the fitting side, say so in the log BEFORE the eval.

## GPU eval (written, NOT submitted)
`outputs/heretic_csi/p2b/plans/p4v2_<cw>_r<R>_{train,val}.sh` → `p4v2_template.sh` → `p3p4_emit.py --what p4v2`
(128 arms: TOP8, BASE_TOP8, 6 descriptive, 60 RAW, 60 NC; + 4 liveness at r1) → `p2b_runner.py`.
Estimate: TRAIN-K4 ≈ 9.4 GPU-h, VALIDATION ≈ 8.1 GPU-h per (cw, rank) ⇒ **≈ 70 GPU-h** total (v1 plan ≈ 37).
v1 plans `p4_*` are marked SUPERSEDED. Analyzer: `p4_analyze_v2.py --codeword <cw> --prefix hcsi_p4v2_<cw>_<split>
--split <train|validation> --expect-n <268|230> --ranks 1,4 --out reports/heretic_csi/p4v2_<cw>_<split>.json`.

## Caveats that travel with any P4 result
Head set certified on basket VALIDATION (D32) ⇒ a basket VALIDATION read is not a fresh test of the nomination.
TRAIN-K4 eval is in-sample for TOP8 and for both control families (all fitted on TRAIN).

## Update (2026-10-14, before any P4 endpoint)
- Review #3 finding 3 fixed: VOID / gate-failed / recovery-degenerate primary ranks count as MISSING in Holm ⇒ INCOMPLETE
  (`p4_analyze_v2.valid()`; PREREG_P4_AMENDMENT_2.json).
- CV diagnostic reduced to 10 control sets per family (PREREG_P4_AMENDMENT_3.json; CPU cost; parent decision; fitting-side
  only, not used for any decision). CV jobs: 1024034 basket r1 · 1024035 basket r4 · 1024036 button r1 · 1024037 button r4.
- Partial fitting-side summary (6–8 controls per family; `reports/heretic_csi/P4V2_FIT_SUMMARY_partial.json`): TOP8 is not
  distinctive in-sample — rank among RAW 3/8, 5/7, 2/8, 7/7 and among NC 1/7, 4/6, 3/8, 7/7 (basket r1, basket r4,
  button r1, button r4); the NC refit recovers RAW-level fit (e.g. button r1 RH8NC_0 0.622 vs v1-rescaled 0.147).
  Final ranks: rerun `research/heretic_csi/p4v2_fit_summary.py` when the fit jobs finish.
