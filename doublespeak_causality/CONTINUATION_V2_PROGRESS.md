# CONTINUATION MASTER PLAN V2 — EXECUTION PROGRESS TRACKER

Dedicated, append-only tracker for executing `CONTINUATION_MASTER_PLAN_V2.md`. Ticks in the big
`CONTINUATION_PROGRESS.md` (ticks 1–87) remain the historical log; this file tracks the V2 sprint only so
progress is easy to follow across `/loop` iterations. Corrections/deviations go to `BUG_AND_DEVIATION_LOG.md`.

**Rules in force:** every test train/test(+dev) split + ≥20/cell (§0.6); representational ≠ behavioral
(§0.2); positive+specificity controls (§0.4); v3 = confirmatory (§0.5); engineering Appendix A
(≤6–7 parallel, ≤2 model-load/node, --nodelist not --exclude, GPU guard, RUNMETA-first/DONE-last,
judge score≥0.25, --no-filter-cand); status ∈ {VERIFIED·NULL·UNDERPOWERED·SUPERSEDED·WITHDRAWN·PENDING·UNVERIFIED}.

---

## STATUS DASHBOARD (updated 2026-08-07)

| plan | phase | status | evidence / next |
|---|---|---|---|
| §1.1 | refusal-validation BR-09/WR-02 + depth fig | ✅ **DONE** | audit regen (VERIFIED=72, UNVERIFIED=0, PENDING=0, 145 checks 0-fail); `figures/fig_depth_validated.png` |
| §1.2 | GPU baseline / drift envelope | ☐ NOT DONE | queued |
| §1.3 | v3 confirmatory validator + audit | ✅ **DONE** | `scripts/validate_dataset_v3.py` PASS; `reports/V3_CONFIRMATORY_DATA_AUDIT.md` |
| §3 | refusal-suppression coarse localization | ◐ **IN FLIGHT** | harness+controls done; smoke 732151; full v3 next |
| §12 | Jacobian readout | ✅ **DONE + closed** | peak-layer test VERIFIED (concept L16/refusal L12 mid-peak, MID−LATE p≈0); curated join NULL/UNDERPOWERED (n=51, 11 mal) |
| §14–18 | Gate-7 attack objective | ☐ NOT DONE (0/13 arms) | unit tests first (§16) |
| others | §4–§11, §19–§29 | ☐ NOT DONE | scheduled by priority |

---

## LOG

### 2026-08-07 — loop resume (this session)
- **Assessed frontier.** Prior loop iters (commits 31a4dd9b, 502325fd) pre-registered §3 and implemented
  `scripts/phase_refusal_suppression_localize.py` + `slurm/run_refusal_localize.sh`; smoke 732100 ran on
  real GPU (3090), self-swap gate = 4.68e-06 (~0 ✓), and showed a **strong preliminary hit**: patching
  Direct→DS at resid_pre/resid_post ~L16–18 restores ~90% of the refusal gap (train & test). n=2 (smoke,
  not evidence).
- **§1.3 DONE.** Ran `validate_dataset_v3.py` (PASS, 324 eligible); wrote `reports/V3_CONFIRMATORY_DATA_AUDIT.md`.
- **§3 harness hardened (self code-review):**
  - Added `neutral` donor (necessity via neutral context) + **norm-matched random `rand` donor**
    (the §0.4 specificity control the docstring promised but did not implement).
  - Added a per-split **Gate-A specificity_top** table to summary.json + printout (direct vs rand vs neutral
    frac at each top cell).
  - Fixed a repro bug in my own edit: replaced PYTHONHASHSEED-salted `hash()` with `zlib.crc32` for the
    per-item random-donor seed (provenance/reproducibility).
  - Switched wrapper defaults to **v3** (`behavioral_v3/beh_clearharm.json`), `splits=train,dev,test`,
    `donors=direct,neutral,rand,self`; fixed the stale pasted-Jacobian header comment.
- **Launched §3 smoke 732151** (n=2, new donor paths) before the full run (mandatory dry-run §37).
- **Next:** on smoke pass → launch full v3 clearharm + generated (2 GPU jobs); analyze coarse band; then
  refine + behavioral confirmation of any passing cell.

### 2026-08-07 — PRIORITY-A closeout landed (2 parallel subagents, independently re-verified)
- **Claim audit regenerated (§1.1).** BR-09 PENDING→VERIFIED (reframed: refusal axis first causally
  manipulable ~L13; anchor L16/L18; L22 caveat kept); WR-02 PENDING→VERIFIED (frac_of_gap ≤|0.05|, ≤|0.025|
  clearharm on validated layers); BR-12/FIN-03/META-03 UNVERIFIED→VERIFIED (all recomputed from on-disk
  outputs, no fabrication); RP-03 stale CV-AUC 0.887 struck in `REP_PREDICTS_BEHAVIOR.md`. Regenerated
  `reports/CLAIM_AUDIT_TABLE.md`: **90 claims — VERIFIED 72 / WITHDRAWN 8 / SUPERSEDED 4 / UNDERPOWERED 6 /
  UNVERIFIED 0 / PENDING 0; 145 numeric checks, 0 CHECK-FAIL** (re-ran the script myself to confirm).
  Honest residual: TR-01 flagged AT RISK (readout L30 invalid in one family — must re-read at L18/L22).
- **Corrected depth figure (§1.1).** `figures/fig_depth_validated.png` + `scripts/make_depth_validated_figure.py`;
  all per-layer values recomputed from raw refval (722611) + refinject_cal rows, 0 mismatch vs summaries.
  L0–L12 hatched "no validated axis"; validated-both {13–20,24,28,29} shaded; anchors L16/L18/L22 marked.
  **Gap found:** calibrated rescue only injected at {9,16,22,28} → no ΔASR at L18 → queue a calibrated-inject
  sweep over the full validated set to close Panel B.

### 2026-08-07 — §3 smoke PASS → full v3 launched
- Smoke 732151 (n=2, v3 clearharm, all splits/donors) PASS: self-swap max|restore|=4.67e-06 (~0 ✓);
  new donor paths execute; **specificity confirmed** — at resid_pre|L18 direct restores ~92–97% of the
  refusal gap while the norm-matched random donor does not (rand_frac negative/erratic); neutral donor
  partially restores (~0.74). (n=2 → frac_mean noisy; restore_ci is the robust primary; use ratio-of-means
  downstream.)
- **Launched FULL §3 v3:** 732161 clearharm (train85/dev43/test42), 732162 generated (77/39/38), on
  nodelist n-802..t-806 (avoid slow n-801). Endpoint = validated refusal projection. ~4h each.
- **Note for analysis:** the harness `frac_mean` = mean of per-item ratios is unstable at small |gap|;
  headline frac downstream should be ratio-of-means (mean restore / mean gap). restore_ci already robust.

### 2026-08-07 — §12 closed (subagent, verified)
- **Peak-layer inferential test — VERIFIED both cohorts/targets** (`scripts/analyze_jacobian_peaklayer.py`,
  `reports/P6_PEAKLAYER_AND_CURATED_JOIN.md`): bootstrapped argmax concept modal **L16** (96.9% in mid band
  L12-17), refusal modal **L12** (CI [L12,L12]); MID(L12-17)−LATE(L28-30) contrast all four positive, CI
  clear of 0, sign test p≈0. Readout |proj| peaks late (L30/L25) → mid-causal/late-readout dissociation now
  inferential, not point-estimate. Feeds Figure 3.
- **Curated behavioral join — NULL/UNDERPOWERED** (honest): n=51, 11 MALICIOUS; refusal−concept paired AUC
  diff −0.05 [−0.24,0.16] includes 0; floor effect (curated uniformly suppresses refusal). Not a
  contradiction of the clearharm headline (AUC 0.807, reproduced exactly by the subagent before extending).

### Pending PRIORITY-A / next
- §1.2 GPU baseline / judge-noise drift envelope (queue when a generation L40S slot is free).
- Calibrated-inject rescue over validated layers {13–20,24,28,29} (closes depth Panel B at L18).
- On §3 full landing (732161/732162): analyze coarse band (ratio-of-means frac, Wilcoxon+Holm over the
  full 32-layer family per §0.6), then refine + behavioral confirmation of any passing (L,C) cell.
