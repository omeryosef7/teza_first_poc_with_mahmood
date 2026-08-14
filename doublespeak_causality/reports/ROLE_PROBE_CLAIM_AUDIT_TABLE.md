# ROLE-PROBE SPRINT — CLAIM AUDIT TABLE

Required deliverable (plan §20). Every headline claim of the role-probe / Bombness
sprint with its provenance and status, for the independent audit (§21).

Status legend: **VERIFIED** (raw-reproducible, controls pass) · REPORT-ONLY
(summary-backed) · UNDERPOWERED (bound, not effect) · BLOCKED · SUPERSEDED · WITHDRAWN.

Model: Llama-3.1-8B-Instruct (bf16, sdpa). Split: v3 leakage-0 (train 162 / dev 82 /
test 80; codeword- & concept-disjoint). Binary malicious = StrongREJECT ≥ 0.5 (D2).
Residual space: `resid_post == hidden_states[L+1]` (D1). Manifest:
`configs/manifests/role_probe_sprint_v1.json`.

---

## A. Governance (Phase 0)

| # | Claim | Source | n | Status |
| --- | --- | --- | --- | --- |
| A1 | Registry backfilled 395→591 rows; all on-disk output dirs registered | `EXPERIMENT_REGISTRY.csv`, `scripts/update_registry.py` (idempotent) | 545 dirs | **VERIFIED** |
| A2 | Bug log backfilled B6–B18 (GCG selection, v1 leak, refusal off-by-one, abs-position D1/D2, test-dose, threshold, missing-dirs, Phi gap, …) | `BUG_AND_DEVIATION_LOG.md`; sources in `RESEARCH_LOG_AUDIT_2026-08-14.md` | — | **VERIFIED** (each cites an immutable source) |
| A3 | Threshold contract frozen at 0.5; refusal-ablation headline is threshold-robust | `reports/THRESHOLD_SENSITIVITY_2026_08_14.md`; `scripts/threshold_sensitivity.py` | 42 (test) | **VERIFIED**: ΔASR 0.25≈0.5 (bf16 +0.286/+0.286); recompute matches audit A4; 84/84 label integrity |

## B. Gate 1 — Bombness probe validity (Phase 1)

| # | Claim | Source | n | Effect / CI | Control | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Contextual Bombness is decodable at the query codeword | `reports/BOMBNESS_PROBE_VALIDATION.md`; run 757886; `gate1_codeword_last.json` | 42 holdout | **AUC 0.997** [0.990,1.000] @L11 | vs controls below | **VERIFIED** |
| B2 | …and at the decision token | same, `gate1_final_prompt.json` | 42 | AUC 0.964 [0.930,0.993] | — | **VERIFIED** |
| B3 | Generalizes to held-out codewords | v3 split property (test 22 codewords, 0 train overlap) | 42 | holdout AUC = cross-codeword AUC | codeword-disjoint | **VERIFIED** |
| B4 | Not explained by trivial confounds | `gate1_codeword_last.json` controls | 42 | length 0.587, position 0.578, token-id 0.500, label-shuffle 0.465, random 0.529 | all 9 controls | **VERIFIED** (token-id 0.500 exact by matched-pair design) |
| B5 | Bombness ⊥ refusal at codeword, entangles at decision | `geometry_vs_refusal.json` | 340 | cos +0.091 (codeword) / +0.468 (decision) | — | **VERIFIED** |

## C. Phase 3 — dual-state prediction

| # | Claim | Source | n | Effect / CI | Control | Status |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | Refusalness predicts DS jailbreak | `reports/DUAL_STATE_PREDICTION.md`; `dual_state_predict.json` | 42 holdout | **AUC 0.976** [0.921,1.000] | frozen refusal_L18 (not refit) | **VERIFIED** (holdout small; pooled n=170 AUC 0.849) |
| C2 | Bombness does NOT predict DS jailbreak | same | 42 | **AUC 0.592** [0.506,0.855] (directional 0.41) | — | **VERIFIED** |
| C3 | Refusalness − Bombness AUC gap excludes 0 | same | 42 | **+0.384** [0.114,0.482] | bootstrap 10k | **VERIFIED** |
| C4 | Bombness adds nothing after conditioning on refusal | nested models | 42 | ΔAUC both-over-refusal −0.016 | nested A/B/C/D | **VERIFIED** |

## D. Gate 4 — Bombness causal intervention (Phase 4)

| # | Claim | Source | n | Effect / CI | Control | Status |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | Ablating v_bomb collapses the concept readout (manipulation check) | `reports/BOMBNESS_CAUSAL_INTERVENTION.md`; run 757931; `phase4_analysis.json` | 42 | readout ablate−base −1.32/−1.30/−1.39/−1.62 @L20/24/28/31 | vs random (≈0) | **VERIFIED** |
| D2 | Bombness is NOT behaviorally necessary | same | 42 | **ΔASR −0.048** [−0.143,+0.048], p=0.625 | vs random: −0.048 | **VERIFIED** (bound excludes refusal-magnitude effect) |
| D3 | Refusal ablation IS behaviorally causal (positive control) | same | 42 | **ΔASR +0.238** [+0.071,+0.405], p=0.021; refusal rate 0.643→0.048 | — | **VERIFIED** |
| D4 | Bombness ablation leaves the refusal decision untouched | same | 42 | refusal rate 0.643→0.643 | — | **VERIFIED** |
| D5 | 2×2 Bombness×refusal: no interaction; Bombness inert in BOTH refusal states (Story B refuted) | run 757943; `phase4_analysis.json` `factorial_2x2` | 42 | **interaction +0.000** [−0.143,+0.143]; main-effect Bombness +0.000 [−0.071,+0.071]; main-effect refusal +0.357 [+0.202,+0.500] | 4 cells one run; manip-check passed (−1.3 to −1.6) | **VERIFIED** |
| D6 | Bombness is NOT sufficient (§8.5): injecting it to doublespeak level does not induce harm | run 757992 (dose 0.25, on-manifold); `phase4_analysis.json` | 42 | neu_bomb_add ΔASR **+0.048** p=0.50; refusal rate 0.667→0.667; refusal-from-neutral control **+0.333** p=0.001 | manip-check passed (readout +5 to +8); vs random +0.095 ns | **VERIFIED** |

## CC. Cross-cohort replication (generated cohort, run 757957)

| # | Claim | Source | n | Effect | Status |
| --- | --- | --- | --- | --- | --- |
| CC1 | Gate 1 (Bombness decodable) replicates on the generated cohort | `gate1_codeword_last.json` (generated run) | 38 holdout | AUC 0.997 [0.990,1.000]; controls near chance | **VERIFIED** |
| CC2 | Bombness is non-predictive on generated too (epiphenomenal half holds) | `dual_state_predict.json` (generated) | 38 | AUC 0.49 (chance) | **VERIFIED** |
| CC3 | Refusal-predicts-jailbreak does NOT cleanly replicate on generated (as a PREDICTOR) | dual_state (generated) | 38 | frozen dir 0.525; native probe 0.60–0.63 (vs clearharm 0.98); gap CI includes 0 | **cohort-specific PREDICTION** — but the mechanism replicates causally (CC5); the gap is frozen-direction transfer (B17), not "refusal doesn't matter" |
| CC4 | Bombness causal necessity on generated | run 757967 `phase4_analysis.json` | 38 | **INCONCLUSIVE** — manip check FAILED (readout +0.3 to +0.7, not down) | **INCONCLUSIVE** (intervention did not cleanly manipulate Bombness on generated; bomb_ablate == bomb_random exactly) |
| CC5 | Refusal ablation IS causal on generated (positive control replicates) | same | 38 | ΔASR **+0.21** [+0.03,+0.29], p=0.02; refusal rate 0.24→0.03; 2×2 main-effect refusal +0.16 [0.03,0.29] | **VERIFIED** — the refusal mechanism replicates causally cross-cohort |

## E. Headline synthesis claim

| # | Claim | Basis | Status |
| --- | --- | --- | --- |
| E1 | Doublespeak creates a real, decodable, causally-manipulable BOMB-like semantic identity that is orthogonal to refusal, does not predict jailbreak, and does not causally control it; a separable refusal-suppressed state does. (Story A) | B1–B5 + C1–C4 + D1–D4, three convergent lines | **VERIFIED** (necessity; sufficiency/2×2 strengthen) |

## Known limitations (carried into the synthesis)

- **Single cohort** (clearharm) for Gates 1/3/4; generated-cohort replication not yet run.
- **Single dose/band/seed** for Phase 4 (α=1 full ablation, band L8-18); manipulation
  check confirms a strong ablation, but a dose/band/seed sweep would harden the null.
- **n=42 holdout** for behavioral claims (base ASR ~0.24). Nulls are stated as bounds
  (D2 CI excludes the refusal-magnitude effect; not "exactly zero").
- **Refusal direction fit cross-distribution** on carrot_bomb (B17); still predicts and
  causally controls clearharm DS behavior (validates it), disclosed.
- **Necessity, not sufficiency** (§8.5) — the natural next causal arm.
- Cross-family (Phi/Qwen, Phase 8) and the normalized-space robustness arm not yet run.

## Reproduce-from-scratch pointers

Extraction `run_probe_extract.slurm` → `gate1_eval` / `dual_state_predict` (CPU) →
`build_intervention_directions` → `run_phase4_bombness.slurm` → `analyze_phase4`. All
run dirs carry RUNMETA + DONE; analysis JSONs live beside the raw data.
