# Doublespeak Causal Circuit — Implementation Progress Log

Tracking execution of `CAUSAL_CIRCUIT_MASTER_PLAN.md`.
Model: Llama-3.1-8B-Instruct (bf16 for causal claims). Branch: `behavioral-causality-sprint`.

**Legend:** ☐ not started · ◐ in progress · ☑ done · ⚠ blocked/needs-decision · ✗ null/negative result

---

## Live status (most recent first)

- **2026-08-02 (iter 1)** — **Phase 0 audit COMPLETE.** 7-lane parallel audit finished (0 errors,
  367k tok). Wrote `reports/CAUSAL_PATCHING_AUDIT.md` (full repo map, reusable primitives,
  provenance, reproducible-vs-not values, gap list, 10 footguns). Wrote
  `scripts/validate_data_integrity.py` (train/test overlap, intent-cluster leakage, dup prompts,
  codeword-occurrence & multi-token checks, output-row dup/metadata checks) — syntax-ok, dry-run
  graceful (no split yet). **Key priors captured:** d_DS causally inert (d_Direct is the lever);
  temporal/repr GCG objective backfires (ASR 0.0, refusal 0.615) — attack is demonstration-bound;
  N7-M all-layer edge knockout degenerate → **surgical per-head edge knockout (Phase 4.2) is the
  flagged next step**; mechanism distributed (no single-head/layer bottleneck). Novel EV =
  ClearHarm generalization + locked-split/Holm rigor + full 4-loc/all-layer/all-head coverage +
  surgical knockout. **Consulting Omer on ClearHarm→Doublespeak mapping (§7 of audit).**
- **2026-08-02** — Session start. Wrote master plan. Oriented repo: found mature existing
  infra (`ds_common.py`, `pair_common.py`) already implementing LayerPatch, AttentionKnockout,
  ZHeadPatch/Capture, DemoStateSwap, SubmodulePatch, project-out/add hooks (single+multilayer),
  norm-matched/orthogonal/in-subspace random controls, all-occurrence `find_word_occurrences`,
  templating, `EXPERIMENT_REGISTRY.csv` (45 runs), `tests/` (17 tests). Created `reports/`,
  `configs/manifests/`, `scripts/`. Launched **Phase 0 audit workflow** (7 parallel code auditors).

---

## Phase checklist

| Phase | Description | Status | Notes |
|------|-------------|--------|-------|
| 0 | Repo & result audit → `reports/CAUSAL_PATCHING_AUDIT.md` + validation checks | ☑ | audit report + data-integrity validator done; Gate 1 satisfiable from artifacts |
| 1 | ClearHarm locked split → `data/splits/clearharm_doublespeak_v1.json` (≥20 train/≥20 test) | ☐ | clearharm data present at `data/clearharm/` |
| 2 | Baseline reproduction + concept/refusal directions | ☐ | reuse 33_build_directions, build_refusal_direction_llama |
| 3 | Exhaustive all-occurrence residual patching (L0–31 × 4 loc × 10 pos × 2 dir) | ☐ | reuse LayerPatch/SubmodulePatch |
| 4 | Exhaustive attention: all-head scan + edge knockout + edge sufficiency | ☐ | reuse AttentionKnockout, ZHeadPatch |
| 5 | Exhaustive all-head activation patching (Q/K/V/z/pattern/result) | ☐ | reuse ZHeadCapture/Patch |
| 6 | Exhaustive MLP write-location analysis | ☐ | reuse 51_mlp_attribution, SubmodulePatch |
| 7 | Head→MLP path patching (every downstream receiver) | ☐ | reuse 50_path_patching |
| 8 | Jacobian/projection readout all layers | ☐ | reuse 07_patchscope, 46_forced_choice |
| 9 | Intervention-strength dose-response sweeps | ☐ | reuse 34_intervention_sweep |
| 10 | Distill causal optimization objective | ☐ | gated on 3-7; reuse MECHANISTIC_OBJECTIVE |
| 11 | GCG / MAC / TROPT evaluation | ☐ | gated on 10; reuse 25_eval_gcg_asr, TROPT skill |

## Granularity coverage (per major intervention)
A single-layer · B canonical windows · C sliding (w2/4/8) · D cumulative prefix · E cumulative suffix · F mechanism-derived · G all-layers. Tracked per experiment once Phase 3 begins.

## Gates
- G1 Reproduction ☐ · G2 Layer coverage ☐ · G3 Attention causality ☐ · G4 Write location ☐ · G5 Path mediation ☐ · G6 Objective ☐ · G7 Behavioral improvement ☐

## Deliverable reports (status)
`CAUSAL_PATCHING_AUDIT` ◐ · `DATASET_AND_SPLIT_CONTRACT` ☐ · `ALL_OCCURRENCE_PATCHING` ☐ ·
`ATTENTION_EDGE_KNOCKOUT` ☐ · `ALL_HEAD_ACTIVATION_PATCHING` ☐ · `ALL_LAYER_MLP_PATCHING` ☐ ·
`HEAD_TO_MLP_PATH_PATCHING` ☐ · `JACOBIAN_READOUT` ☐ · `CAUSAL_OBJECTIVE` ☐ ·
`GCG_MAC_EVALUATION` ☐ · `FINAL_CAUSAL_CIRCUIT_REPORT` ☐ · `SLACK_UPDATE` ☐

## Decisions / open questions for Omer
- (none yet)

## Known constraints (from project memory)
- SLURM: no deps, max 6 parallel, L40S only, no trimming. bf16 + default SDPA (don't disable flash). GCG always `--no-filter-cand`.
- Cyber-safeguard kills subagents that read ClearHarm/jailbreak **text**; keep harmful-text handling in main loop, delegate code/scalar work only.
