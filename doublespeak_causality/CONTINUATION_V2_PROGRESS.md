# CONTINUATION MASTER PLAN V2 — EXECUTION PROGRESS TRACKER

Dedicated, append-only tracker for executing `CONTINUATION_MASTER_PLAN_V2.md`. Ticks in the big
`CONTINUATION_PROGRESS.md` (ticks 1–87) remain the historical log; this file tracks the V2 sprint only so
progress is easy to follow across `/loop` iterations. Corrections/deviations go to `BUG_AND_DEVIATION_LOG.md`.

**Rules in force:** **SLURM job PENDING >30 min → scancel + resubmit with a different config (widen nodelist;
measure via SUBMIT_TIME not %M; generation stays strict-L40S; never kill a progressing RUNNING job)** —
enforce every loop tick; every test train/test(+dev) split + ≥20/cell (§0.6); representational ≠ behavioral
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
| §3 | refusal-suppression coarse localization | ✅ **Gate A PASS (repr)** | clearharm residual L15–18 restores refusal frac≈0.93 (Holm≈0), replicated train/dev/**test**; NULL on generated. Behavioral (Gate B) next. `reports/P_REFUSAL_SUPPRESSION_LOCALIZATION.md` |
| §4 | carry vs write vs origin | ◐ partial | §3 shows residual-CARRY (attn/mlp barely restore); origin=§5 |
| §23 | decision-state counterfactual patch (behavioral) | ☐ NEXT | Gate B: patch DS decision resid←Direct during generation, ΔASR |
| §12 | Jacobian readout | ✅ **DONE + closed** | peak-layer test VERIFIED (concept L16/refusal L12 mid-peak, MID−LATE p≈0); curated join NULL/UNDERPOWERED (n=51, 11 mal) |
| §14–18 | Gate-7 attack objective | ◐ **§16 tests PASS** | objective-in-selection verified (12 CPU tests, sign+gradient gaps filled, no bug); GPU arms 0/13 still pending |
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

### 2026-08-07 — loop tick +1 (§3 running; analyzer prepped; calinj closure launched)
- §3 full 732161(clearharm)/732162(generated) RUNNING on n-802, weights loaded clean (~6min), ~compute phase, ~4h.
- **§3 analyzer ready** (`scripts/analyze_refsuploc.py`): ratio-of-means frac, one-sided Wilcoxon (§0.6, not
  permutation), Holm per-component+pooled, Gate-A hit = Holm-sig ∧ direct−rand CI excludes 0 (reliability-gated)
  ∧ frac≥thr. Tested on smoke → correctly 0 hits at n=2. The loop applies it the moment 732161/732162 land.
- **Calinj closure launched (732204):** re-ran the proven calibrated-inject rescue over the FULL P7-validated
  layer set {13–20,24,28,29} (was {9,16,22,28}) on beh_clearharm — closes depth Panel B at L18 (feeds Fig 2/4).

### 2026-08-07 — loop tick +2: §3 LANDED, Gate A PASS (clearharm)
- Both §3 runs completed clean (170/154 rows, DONE.json). Ran `analyze_refsuploc.py`.
- **clearharm: Gate A PASS, replicated train/dev/TEST** — residual overwrite (Direct→DS) at L15–18 restores
  the refusal projection frac≈0.93 at L18 (Holm-p≈0 train/dev, 0.005 test), specific vs norm-random,
  self-swap≤5e-6; robust at anchor L24 (frac 0.83 patching L20, 6 layers upstream). **attn_out/mlp_out barely
  restore (0.04–0.25) → residual CARRY, not sub-block write.** Onset ~L13 (matches P7).
- **generated: NULL** — no cell beats the norm-random control in any split (non-exchangeable, expected).
- **Self code-review caught a real bug in my analyzer:** the specificity gate accepted "CI excludes 0" in
  EITHER direction, so a generated-cohort cell where random restored MORE than direct was wrongly flagged a
  hit. Fixed to require direct−rand lower bound > 0 (donor restores MORE than control). Re-ran → generated
  correctly shows 0 hits.
- Report: `reports/P_REFUSAL_SUPPRESSION_LOCALIZATION.md`.

### 2026-08-07 — loop ticks +2/+3: Gate B harness + validator §36
- Built + committed Gate B harness (`phase_refusal_decision_patch_behav.py` + wrapper); smoke 732264 queued
  (PENDING on fair-share — GPU is priority-bound not capacity-bound; not launching more to avoid diluting).
- **§36 validators extended** (subagent, verified): refsuploc + refdecpatch schemas added to
  `validate_experiment_coverage.py` + `validate_all_outputs.py`; refsuploc recompute **3079 values, 0 mismatch**
  (independent provenance check of the §3 Gate A summary); regression sweep over 457 dirs, no prior schema broke.
- **Backlog surfaced:** `configs/manifests/` still empty (§36 expected-cell manifests) — every phase warns
  "no manifest"; needed to distinguish "cell ran and produced null" from "cell never launched". Schedule.

### 2026-08-07 — loop tick +4: §36 manifests done; §1.2 harness ready; 30m rule live
- **§36 manifests committed** (subagent + my verify): `configs/manifests/{refsuploc,refdecpatch,refval,behav_carry}.json`.
  Note: the "no manifest" warning is CWD-sensitive (`--manifest-dir` default is CWD-relative `configs/manifests`) —
  validator must run from `doublespeak_causality/`; from there refsuploc → **ok, 0 warn**. Never-launched-cell
  detection intact (2-row smoke correctly FAILs).
- **§1.2 drift harness ready** (`phase_baseline_drift.py`+wrapper), held from submit (fair-share).
- **30m-pending rule live** and applied (732264→732295).

### Pending PRIORITY-A / next
- **§23 / Gate B (decisive):** patch DS decision-token residual←Direct at L18 (+L15–17 band) DURING
  generation, measure ΔASR vs rand/self controls → converts the repr localization to behavioral causality.
- §1.2 GPU baseline / judge-noise drift envelope (reuse dc.load_model+behav_judge; drift = re-judge K×).
- Rebuild depth Panel B with the new calinj validated layers once 732204 lands.
- On §3 full landing (732161/732162): analyze coarse band (ratio-of-means frac, Wilcoxon+Holm over the
  full 32-layer family per §0.6), then refine + behavioral confirmation of any passing (L,C) cell.
