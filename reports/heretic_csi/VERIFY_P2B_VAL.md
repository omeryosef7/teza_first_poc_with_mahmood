# VERIFY — P2b VALIDATION read (S-156) — independent recomputation (review #6) — 2026-10-15

Code: `research/heretic_csi/verify/verify_p2b_val.py` (own code, written from the prereg text; extends my review-5
`verify_p2b_train.py`; does NOT import or copy `p2b_analyze.py`). sha256 `f68002c4…0c34d`.
Output: `reports/heretic_csi/VERIFY_P2B_VAL.json`. CPU only (poc_stage2 python), B = 10 000 domain-bootstrap draws.

**Verdict: AGREES in all 8 primary + secondary cells, all gates, no VOIDs, outcome mapping ⇒ D.**

## Selection / population / provenance
- Strict regex `hcsi_p2b_<cw>_val_<ARM>_<YYYYMMDD>_<HHMMSS>_<pid>`, DONE.json status ok, rows_written 230. Exactly one
  complete dir for every arm; no partial dirs; `*valovl*` / `*valaovl*` overlap dirs never match.
- Jobs/hosts (all NVIDIA RTX A5000): basket 1023578 (167 arms) + 1023579 (163), n-503; add-on 1040101 (46), n-501.
  button 1036679 (167) n-503 + 1036680 (163) n-501; add-on 1040122 (46) n-501. Button r4 primary cell mixes n-501
  arms with n-503 liveness arms; `overlap_buttonvaln501_1040170_r0.json` = OVERLAP_OK, max |Δy| 0.0 (read).
- Every arm: bank `ts116m_<cw>_bomb.jsonl`, `--exclude-prompt-ids runargs/dcs_cont/exclude_<cw>_bomb_sow_validation.txt`,
  attn eager, bf16 — 0 config violations.
- Population: 230 rows, 23 domains × 10; all 23 domains are `validation` in the frozen `dcs_ts116_domain_split.json`.
  **0** VAL domains in TRAIN-K4; **0** VAL domains and **0** VAL prompt_ids in the TRAIN fit captures (670 rows, 67
  domains) ⇒ no row-level or domain-level leakage into the operator fits.
- Factor files: CAND/CWONLY/SHUF/DER/CWDER arms all carry the same `factors_sha16` per (cw, r), equal to the TRAIN-K4
  CAND arm's (basket r1 9c2d453a…, r4 96e3af94…; button r1 7a5ba79d…, r4 94060fd0…) ⇒ frozen, no refit.
- Norm match: max relative per-module Frobenius deviation of all 81 primary controls vs CAND ≤ 6.0e-8; rank and
  n_params equal for all RAND/SHUF/DER/CWRAND/CWDER arms; every arm's hook_calls = 23 920 (> 0).
- **Key definition (important for anyone re-implementing):** VAL family_ids contain both `dev|slotN` and
  `heldout|slotN` per domain; keying by `slotN` alone collides (my first run asserted on this). Key = (domain,
  family_id minus domain and query_kind) — same as the frozen analyzer's `family_slot` (which documents the D-001
  precedent). The analyzer's 145 / 203 keys are therefore correct.

## Gates (agree)
| | basket | button |
|---|---|---|
| keys (BASE om ≥ 0.05) / domains | 145 / 23 | 203 / 23 |
| KO − BASE | −0.27996 | −0.30203 |
| FULL − KO | +0.14018 | +0.14212 |
| KO_IDENT ≡ KO (max \|Δy\|) | 0.0 | 0.0 |
| KO_CAPOP replays KO_CAND (r1, r4) | 0.0, 0.0 | 0.0, 0.0 |
| collapse screen (median om < 0.05 on BASE/KO/FULL/IDENT/CAND/CWONLY) | none | none |
| preservation BASE_CAND − BASE (r1, r4) | −0.038, −0.010 | −0.003, −0.012 |
KO_MEANBIAS median om 1.1e-3 / 2.4e-6 ⇒ collapsed (VOID per amendment 4; descriptive only).

## Primary and secondary cells — mine vs analyzer
| cell | stat (mine = analyzer) | rank | Holm p | recovery [CI] mine | analyzer CI | verdict |
|---|---|---|---|---|---|---|
| basket prim r1 | 0.16824 | 11/82 | 0.1341 | 1.200 [0.983, 1.459] | [0.984, 1.452] | not pass = |
| basket prim r4 | 0.21043 | 2/82 | 0.0488 | 1.501 [1.212, 1.821] | [1.222, 1.831] | **PASS** = |
| button prim r1 | 0.24612 | 14/82 | 0.3415 | 1.732 [1.526, 1.952] | [1.521, 1.942] | not pass = |
| button prim r4 | 0.23026 | 15/82 | 0.3415 | 1.620 [1.439, 1.815] | [1.439, 1.813] | not pass = |
| basket CWONLY r1 | 0.19996 | 1/77 | 0.0260 | 1.427 [1.224, 1.680] | [1.222, 1.684] | **PASS** = |
| basket CWONLY r4 | 0.19708 | 1/77 | 0.0260 | 1.406 [1.197, 1.652] | [1.202, 1.658] | **PASS** = |
| button CWONLY r1 | 0.23796 | 9/77 | 0.2338 | 1.674 [1.511, 1.852] | [1.511, 1.844] | not pass = |
| button CWONLY r4 | 0.23358 | 12/77 | 0.2338 | 1.644 [1.492, 1.801] | [1.491, 1.797] | not pass = |
Stats, ranks, Holm p's and verdicts identical; CIs differ in the 3rd decimal only (bootstrap seeds). All 81 / 76
per-control stats feed the same ranks. Sub-family ranks reproduce: RAND 1/62 (all cells), SHUF 1/6, DER 11, 2, 14,
15 /16; DER at RAW norm 16, 7, 16, 16 /16. CAND − mean(DER): basket r1 −0.0039 [−0.027, 0.011], r4 **+0.0184
[0.0086, 0.0282]**, button r1 −0.0054 [−0.0135, 0.0014], r4 −0.0170 [−0.032, −0.0045] (= analyzer).

**Outcome (amendment 5, VALIDATION only):** specific = {basket: r1 no, r4 yes; button: r1 no, r4 no}, no VOID /
INCOMPLETE cell ⇒ **D**. Minimal specific rank: basket 4, button ">4 (untested)". AGREES with S-156.

## Robustness (descriptive; does not change the preregistered verdict)
basket primary r4 (PASS, Holm 0.0488 = 2/82):
- Beaten by exactly one control, **KO_DER_r4_10** (0.22030 vs 0.21043; margin −0.0099) — the SAME DER fit beats it
  on TRAIN. Next control below (KO_DER_r4_7, 0.21034) is only **0.00009** below CAND ⇒ rank 2 vs rank 3 (Holm 0.073)
  rests on a 9e-5 difference in y.
- **LODO over 23 VAL domains: rank 2 in 14/23, rank 3 in 8/23, rank 4 in 1/23 ⇒ Holm ≥ 0.05 in 9/23 drops**
  (canal_lock, catering_unit, coal_yard, coastguard_post, hospital_supply, parks_yard, shipyard_slip, toy_factory,
  water_treatment; max Holm 0.098). (TRAIN: rank 2 in 63/63.)
- Strict paired floors: CAND+KO floor rank 2/82 (Holm 0.0488, 135 keys/22 doms); all-arms floor rank 2 (121/22). Holds.
- Row-level (not domain-level) statistic: rank 3/82 ⇒ Holm 0.073 (would not pass).
- DER replaced by DERRAW (raw fitted norms) in the family: rank 7/82 (p 0.085). DER-only at raw norm 7/16.
- CAND − best DER paired: −0.0099 [−0.023, +0.002]; CAND z vs the 15 DER = +1.36 SD.
basket secondary CWONLY r1 / r4 (PASS, 1/77):
- LODO rank 1 in 23/23 at both ranks; strict floors rank 1; margin to best CWDER +0.0040 / +0.0036 (CI of the paired
  difference includes 0: [−0.004, 0.010] / [−0.006, 0.012]); CWONLY − mean(CWDER) +0.020 [0.014, 0.025] / +0.019
  [0.013, 0.025]. More robust than the primary r4 PASS.

## Position / NEUT (amendment 7; reproduce S-156 numbers; fraction of BASE−KO gap)
| cell | CAND all | CAND cw-only | CAND last-only | NEUT all | NEUT cw-only | NEUT last-only |
|---|---|---|---|---|---|---|
| basket r1 | 0.60 | 0.71 | 0.000 | 0.74 | 0.028 | 0.010 |
| basket r4 | 0.75 | 0.70 | −0.003 | 0.69 | 0.035 | 0.012 |
| button r1 | 0.81 | 0.79 | 0.007 | 0.75 | 0.073 | 0.045 |
| button r4 | 0.76 | 0.77 | 0.008 | 0.75 | 0.062 | 0.051 |
Not in S-156: basket r1 NEUT − CAND = **+0.040 [0.013, 0.067]** and CWONLY − CAND = +0.032 [0.017, 0.051]; NEUT
(last-row fit, ~0.43× CAND's summed module norm, not norm-matched) ranks 1/82 against the basket r1 primary family.
button r1 NEUT − CAND −0.020 [−0.042, −0.0002].
