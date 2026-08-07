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
| §1.1 | refusal-validation BR-09/WR-02 | ◐ resolved, audit regen pending | flip in build_claim_audit.py + depth figure |
| §1.2 | GPU baseline / drift envelope | ☐ NOT DONE | queued |
| §1.3 | v3 confirmatory validator + audit | ✅ **DONE** | `scripts/validate_dataset_v3.py` PASS; `reports/V3_CONFIRMATORY_DATA_AUDIT.md` |
| §3 | refusal-suppression coarse localization | ◐ **IN FLIGHT** | harness+controls done; smoke 732151; full v3 next |
| §12 | Jacobian readout | ✅ DONE (both cohorts+decisive) | remaining: curated join + peak-layer test |
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

### Pending PRIORITY-A closeouts (CPU, parallel)
- Regenerate `build_claim_audit.py` to flip BR-09/WR-02 → VERIFIED, recompute BR-12/FIN-03/META-03, fix
  RP-03 prose staleness (`REP_PREDICTS_BEHAVIOR.md` withdrawn CV-AUC 0.887).
- Corrected depth figure built only from validated refusal directions (feeds Figure 2/4).
- §1.2 GPU baseline / judge-noise drift envelope.
