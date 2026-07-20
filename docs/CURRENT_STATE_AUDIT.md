# Current State Audit (Phase 0)

Deliverable for Phase 0 of `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` (§4).
Freezes the pre-plan state and separates **facts from hypotheses** before new experiments.

- Frozen commit: see `research_snapshots/2026-07-post-mahmood-meeting/code_commit.txt` (HEAD `36b7960`, 2026-07-21).
- Primary source of truth for all prior GCG work: `docs/GCG_JULY2026_MASTER_LOG.md` (triple-verified) and `docs/GCG_RERUN_CAMPAIGN_LOG.md`.
- This audit does **not** re-run anything; it catalogs what exists and its trust level.

## The placement bug (context for everything below)
The v1 GCG suffix was optimized in the **assistant turn** but evaluated in the **user turn**
(`project_gcg_placement_bug_fix`, `docs/GCG_RERUN_CAMPAIGN_LOG.md`). This means v1 headline
ASR numbers were partly a **response-prefill artifact**. The v2 "userfix" campaign
(`outputs/stage_gcg_full_v2_userfix/`) re-runs with canonical user-turn placement.

- **Unaffected by the bug:** the hidden-state **detector** results (they read activations,
  not attack ASR), refusal-direction *artifacts*, dataset/manifest construction, taxonomy.
- **Invalidated / superseded by v2:** v1 headline ASR magnitudes (e.g. 5A "10.7%").
- **v2 complete:** the 5A gate (canonical GCG ≈ 0 uplift), Phase-8 λ0.3, 9A/9B, per-behavior
  **12-behavior pilot** (`outputs/stage_gcg_percot_v2/`).
- **v2 partial / stopped:** the stratified 50-behaviour scale-up — **105/456 opt runs, no
  scale ASR computed**, stopped 2026-07-21 (`docs/GCG_RERUN_CAMPAIGN_LOG.md`).

## Established (fact) / Suggestive / Unproven

### Established — reproducible, sourced
| # | Claim | Source |
|---|-------|--------|
| E1 | Canonical (user-turn) standard target-prefix GCG has ≈**0 uplift** on Qwen3 CoT setup; v1's 5A 10.7% was a prefill artifact (collapses to ~4.0% = baseline). | master log §13.6, `GCG_RERUN_CAMPAIGN_LOG.md` |
| E2 | Standard GCG is **net-negative** on both Qwen3 & Gemma4 in the 25-behavior ablation (4F: 1.9%, −0.5pp). | master log §"Phases 4–6", §4 table |
| E3 | Optimization **loss does not rank suffixes by behavioral ASR**; intermediate checkpoints often beat final/best-loss (per-behavior pilot: winners best-loss×7 / checkpoint×3). | `GCG_RERUN_CAMPAIGN_LOG.md`, master log per-behavior entry |
| E4 | Attack performance is strongly **seed-dependent** (v2 ranking s44 23% > s45 12% > s43 7%, reversing v1). | master log §13.6 |
| E5 | **Gemma4 stays resistant**: 0–1.3% ASR across most configs; only EmptyThink@L31 gives a real but modest 3.91% (520-scale, +1.6pp). | master log §"Sprint 3" |
| E6 | Position-0 hidden-state LR **detector AUC≈1.000 on Qwen3**, robust under GroupKFold-by-behavior, leave-one-opt-seed-out, and 25-vs-495 split. | master log §"Detection", `outputs/stage_gcg_ablation/detector_groupkfold/` |
| E7 | Cross-architecture suffix transfer (Gemma4↔Qwen3) is **null** both directions (random ≥ optimized). | master log §"Cross-architecture" |
| E8 | Per-behavior + **ASR-selection** recovers real attack power on crackable behaviors (12-behavior pilot: mean best-ASR 0.300, mean uplift +0.208, up to 90%). | `GCG_RERUN_CAMPAIGN_LOG.md`, master log |
| E9 | `repr_loss ⟂ task_loss` conflict: repr-alignment loss rises as suffix becomes task-optimized (model-agnostic). | master log §GCG-Early |

### Suggestive — some evidence, not confirmed
| # | Claim | Note |
|---|-------|------|
| S1 | Weak refusal-direction suppression (9A) retains uplift (~15%, +~13pp) under the fix. | v2 partial; not yet isolated to a causal mechanism. |
| S2 | Certain categories (misinfo) are more crackable (advbench_063/209 at 60–90%). | small n; proportional-sample caveat. |
| S3 | Gemma4's greater `v_refusal` representational separation (0.498 vs Qwen3 0.315) may explain its resistance. | paper-reported reference stat, not our independent finding. |

### Unproven — hypotheses the plan must test
| # | Claim | Plan phase |
|---|-------|-----------|
| U1 | The refusal direction is **causally** responsible for attack success. | Ph 7 |
| U2 | The detector represents attack **success**, not merely attack **presence** (it was trained optimized-vs-clean). | Ph 5–6, 17 |
| U3 | CoT Hijacking succeeds via a specific representation-level mechanism. | Ph 4–7 |
| U4 | Any discovered mechanism transfers across models. | Ph 16 |
| U5 | A mechanistic objective beats prefix-CE for discrete triggers. | Ph 8–10 |

## Phase-0 completion criterion
> No new large experiment until every reported number traces to a config, suffix, generation
> file, judge result, and code version.

**Status:** prior numbers are traceable via `GCG_*_SOURCE_OF_TRUTH.{csv,md}` +
`outputs/stage_gcg_*` raw artifacts. The forward-looking guarantee is enforced from Phase 2
onward by the experiment registry (`results/EXPERIMENT_REGISTRY.csv`, to be built). Until that
exists, treat any new number as provisional.
