# VERIFY_S084 — independent re-computation of PR-HCSI-S084 (+AMENDMENT 1): button r4 VALIDATION vs 200 controls

**Verifier:** F3 (2026-10-14). **Code:** `research/heretic_csi/verify/verify_s084.py` (own; frozen analyzer and
`p2a_powered_*` NOT used). **JSON:** `reports/heretic_csi/VERIFY_S084_powered.json`.

## Dir selection (independent: RUNMETA `slurm_job_id` ∈ {1022698, 1027577, 1032110}, tag `hcsi_p2a_button_*`)
- **Exactly one complete dir per arm** for all 205 pool+liveness arms (BASE, KO, KO_SELF, KO_FULL, KO_CAND_r4,
  KO_RAND_r4_0..189, KO_SHUF_r4_0..9): 61 from 1022698 (n-501), 72 + 72 from 1027577/1032110 (n-503). No missing or
  duplicate arms; no unexpected arms; every selected dir is log-referenced; every DONE `ok`; every arm 230 rows.
- **GPU: NVIDIA RTX A5000 for all 205** (RUNMETA). Each new job has a single STAGE_IN (single attempt), DONE_MARKER rc=0.
- OVL_* arms (4) found and **excluded from the pool**. Same-tag dirs from other jobs (TRAIN 966157/8, K4 969087/8,
  VAL r1/r16 968534/5, smokes) correctly ignored.
- Population: 230 rows / 23 domains, all `validation`; **TEST absent**.

## Primary (BASE-referenced 0.05 floor, common rows across all 205 arms)
| quantity | F3 | frozen record (S-084) |
|---|---|---|
| common rows | **203** | 203 |
| candidate statistic (mean_d cand−KO, unrounded) | 0.0129158 | 0.0129158 |
| rank among exactly 200 controls (ties against cand) | **1/201** (5-dp rounded: also 1) | 1/201 |
| p | **0.004975** | 0.004975 |
| Holm over {r1 0.2456, r16 0.1754, r4} | **r4 adj 0.0149 < 0.05** | 0.0149 |
| beats every SHUF | **yes** (max SHUF 0.009244 < 0.012916) | yes |
| best RAND (of 190) | 0.008075 | — |
| margin over best control | +0.00367 (1.14 control-SD; control mean 0.00065, SD 0.00322) | — |
| candidate − KO, domain bootstrap 95% | 0.01292 [0.00654, 0.01898] | 0.01292 [0.00651, 0.01895] |
| domains positive | 20/23 | 20/23 |
| recovery | 0.0909 | 0.0909 |
| liveness | KO−BASE −0.302; FULL−KO +0.142; SELF−KO −0.0005 | — |
| LODO (drop each domain) | **rank 1 in 23/23** | — |

**Sensitivity:** strict paired floor (BASE ∧ KO ∧ KO_FULL) keeps the same 203 rows → identical result, LODO 23/23 rank 1.
No floor (230 rows): rank 1/201, beats every SHUF, CI [0.0058, 0.0172], LODO 23/23 rank 1. Using F3's own r1 recount
(18/57, p 0.316) instead of the recorded 0.2456 does not change Holm (r4 is smallest ⇒ adj = 3p = 0.0149).

## Control matching
- 200/200 controls have matrix_rank 4 and are orthonormal (|BBᵀ−I| < 1e-5); 56 from `hcsi_ranksweep_button.pt`,
  144 from `hcsi_ranksweep_button_r4ext.pt` (sha256 a3d1c7b0…5af9e = prereg); all 200 bases distinct; none equals the
  candidate. All controls norm-matched to `cand_pls4` (written-norm rel. err ≤ 5.1e-16); every row's rescue rank = 4.
- `cand_pls4` in r4ext.pt is **byte-identical** to the original; the candidate arm uses the original file, key
  `cand_pls4`, no norm-match (as prereg).

## Overlap (cross-job licence)
OVL_BASE / OVL_KO / OVL_CAND_r4 / OVL_RAND_r4_0 (job 1027577) vs BASE / KO / KO_CAND_r4 / KO_RAND_r4_0 (job 1022698):
identical 230-id sets, **max |Δlogp| = 0.0 (bit-exact)** for all four.

## Mutation tests (BASE-ref)
Swap candidate with a random control (30 draws): median p 0.60. Within-domain shuffle of arm identity across the 201-arm
pool (30 draws): median p 0.50; 0/30 reach p ≤ 0.0149. The pipeline can fail its own positive.

## Verdict
**AGREES — PASS** on every component of the amended rule (Holm 0.0149 < 0.05; beats all 10 SHUF; CI lower bound > 0;
203 rows; a5000 only; overlap bit-exact; no VOID) and the unrounded and 5-dp-rounded ranks agree (both 1), so the
parent binding rule is satisfied. Caveats: margin over the best control is ~1.1 control-SD (specific but not large);
the SHUF null remains n=10 (beats all 10, not a 200-strong SHUF family); single codeword, single layer (L18), PLS
activation-space family — not the ARA weight operator.
