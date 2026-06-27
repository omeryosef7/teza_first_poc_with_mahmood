# Correction Sprint Final Report

**Date:** 2026-06-25  
**Sprint goal:** Make the MSc research scientifically defensible before presenting to Mahmood.  
**Status:** All planned corrections COMPLETE. Jobs pending (G condition, RD replication Phase A).

---

## Summary

Eight methodological corrections were identified and applied on 2026-06-25. The sprint does NOT change the core Sprint 2 findings (P4/P4b/P7 non-causal, n=11/4 respectively). It corrects the methodology in Sprint 3 experiments, fixes factorial design gaps, and resolves labelling errors. The updated `docs/RESEARCH_MASTER.md` reflects all changes.

**Correction sprint artifacts** are listed in §5. **What changed** (claims) is in §3. **What is now established vs unresolved** is in §4.

---

## 1. The Eight Corrections

### C1: Timing-based success label override — REMOVED

**Problem:** All four Sprint 3 analysis scripts contained:
```python
if not sr_success and elapsed_s > 200:
    return True   # scientifically invalid
```
This caused ~50-100% of Sprint 3 results to be labelled "success" based on generation time, not content evaluation.

**Fix:** Removed from `analyze_head_ablation.py`, `analyze_causal_tracing.py`, `analyze_generation_patching.py`, `analyze_block_ablation.py`. Renamed `_timing_correct_success` → `_raw_sr_success` in each. `elapsed_s` is retained as metadata only.

**Impact:** Sprint 3 smoke ASR values change significantly (see §2). Sprint 2 is unaffected (P4/P4b/P7 had no timing corrections — all natural compliance at 500-800s).

**Status:** COMPLETE.

---

### C2: Replication discrepancy labelled UNRESOLVED

**Problem:** `RESEARCH_MASTER.md` declared Gate C "hypothesis does not hold" based on a 0/160 sweep that had 4 implementation bugs versus the Arditi et al. protocol.

**Four bugs in `replicate_standard_refusal_direction.py`:**
1. **Single-layer ablation** (critical): applied hooks to 1 layer instead of all 40 (3×40=120 hooks)
2. **KL with wrong hook type**: used activation-addition hooks, not ablation hooks
3. **Steering coefficient α=20.0** instead of upstream coeff=1.0
4. **Layer pruning inverted**: pruned first 20% (layers 0-7) instead of last 20% (layers 32-39)

**Fix:** Gate C relabelled UNRESOLVED. Fixed implementation written at `poc_stage4/replicate_qwen_rd_exact.py`. Hook correctness verified by `poc_stage4/validate_intervention_hooks.py` (9/9 unit tests pass).

**Status:** COMPLETE (code ready). Phase A smoke job submittable (see §6).

---

### C3: Pure-hijack definition requires G condition

**Problem:** `classify_attack_mechanisms.py` defined `pure_cot_hijack` without condition G (bare harmful + thinking OFF). Without G, we cannot distinguish "puzzle+thinking synergy" from "just needs thinking."

**Fix:** All current examples relabelled `candidate_pure_cot_hijack` in `RESEARCH_MASTER.md`. Strict definition of `confirmed_pure_cot_hijack` added: requires G to fail (p_G < θ).

**Status:** COMPLETE (labelling). G data pending (see §6).

---

### C4: A−D contrast mislabelled as "thinking causally required"

**Problem:** A=puzzle+thinking ON, D=bare harmful+thinking ON. Both have thinking enabled. A−D measures the puzzle effect under thinking, NOT whether thinking is required.

**Fix:** All references to "thinking causally required" replaced. Correct labels:
- A−D = "puzzle effect with thinking ON"
- A−E = "thinking effect within puzzle" (correct thinking contrast)
- D−G = "thinking effect on bare harmful" (requires G, pending)

**Status:** COMPLETE.

---

### C5: Factorial interaction formula corrected

**Problem:** `analyze_factorial_attack_effects.py` used `(p_A − p_D) − (p_E − p_F)` — F is a length-matched benign control, not a thinking-off/no-puzzle cell.

**Fix:** Correct formula is `(p_A − p_E) − (p_D − p_G)`. Flagged as INCOMPLETE until G data is available. Script updated in `analyze_factorial_attack_effects.py`.

**Status:** COMPLETE (code). G data pending.

---

### C6: 56× attention ratio has near-zero denominator

**Problem:** The `harmful_goal` span is present as literal tokens in only 4.1% of prompts. In the other 95.9%, the denominator of the 56× ratio is near-zero (a few stray tokens or zero).

**Fix:** Attention claim reframed in `RESEARCH_MASTER.md` as exploratory P5a analysis. The 56× ratio is cited with caveat footnote (†). P5a is not cited as causal routing evidence.

**Status:** COMPLETE.

---

### C7: Distributed circuit claim downgraded to "consistent with"

**Problem:** "Distributed circuit established" in Section 9. Failed local interventions (P4/P4b/P7/P11/P14/P16) show no causal effect but cannot prove a mechanism is distributed — the mechanism may simply not have been tested.

**Fix:** Replaced "established" with "consistent with distributed or redundant mechanism." Evidence-level labels added throughout (Established / Preliminary / Exploratory / INVALID / UNRESOLVED).

**Status:** COMPLETE.

---

### C8: Sign flip described as attack mechanism

**Problem:** The Qwen3 residual stream sign flip (prompt→thinking phase reversal) was described as the attack mechanism. However, the sign flip is present in ALL mechanism classes (successes AND failures), so it is not the attack mechanism.

**Fix:** Sign flip described as "descriptive, not mechanism evidence." Comparison against matched failures noted as pending.

**Status:** COMPLETE.

---

## 2. Sprint 3 Rescoring Results

All Sprint 3 smoke results were re-evaluated removing the timing override. See `docs/INTERVENTION_RESCORING_AUDIT.md` for full per-experiment breakdown.

| Experiment | Old ASR (timing-corrected) | New ASR (raw) | Evidence Level |
|-----------|---------------------------|---------------|----------------|
| P5b: head ablation (L10 H33/H19/H2/H4) | 1.000 | 0.500–0.750 | **INVALID** — errors in Run 1, timing flips in Run 2 |
| P6: end-aligned patching L3/L10 | 0.500 | 0.250 | **CONTRADICTORY** — two runs disagree |
| P6: patching L26 | 1.000 | 0.750 | No effect in 2-example pilot |
| P11: full-range patching L3 | 1.000 | 0.000 | Both records timing-corrected — PENDING proper rerun |
| P11: full-range patching L10 | 0.000 | 0.000 | Artifact (context destroyed, 8-13s generation) |
| P11: full-range patching L26 | 0.500 | 0.500 | Inconclusive at n=2 |
| P14: gen thinking L26 | 1.000 | **1.000** | **NON-CAUSAL** (both succeed naturally, no timing correction) |
| P14: gen answer L26 | 1.000 | 0.500 | Preliminary — Ex2 timing-corrected |
| P16: zero attn/MLP L10 | 0.500 | 0.500 | No effect in 2-example pilot |
| **P16: zero attn/MLP L26** | 0.000 | **0.000** | **⚠ UNRESOLVED — raw ASR=0.000; may be causal** |

**Full runs (615190/615191/615192 currently running) will provide n=11 results without timing correction.**

---

## 3. Impact on Scientific Claims

### Claims that survive the correction sprint unchanged (Sprint 2)

- P4 non-causal (n=11, ASR=1.000): ✓ — No timing correction applied; all natural compliance
- P4b non-causal (n=11, ASR=1.000): ✓ — Same
- P7 Gemma4 non-causal (n=4, ASR=1.000): ✓ — Same
- LOGO AUC Qwen3=0.757, Gemma4=0.806: ✓
- 56× attention ratio (caveat: 4.1% prompts): ✓ (with correction of denominator caveat)
- Qwen3/Gemma4 behavioral dichotomy (preliminary): ✓

### Claims that changed

| Claim | Old | New |
|-------|-----|-----|
| Gate C: hypothesis tested | "does not hold" | **UNRESOLVED** — 4 bugs in replication script |
| pure_cot_hijack (11 Qwen3, 4 Gemma4) | Confirmed | **candidate_pure_cot_hijack** — G pending |
| A−D = thinking causally required | Asserted | **Incorrect** — A−D measures puzzle effect with thinking ON |
| Interaction formula | `(pA−pD)−(pE−pF)` | **`(pA−pE)−(pD−pG)`** — formula corrected |
| 56× attention routing evidence | Cited as causal | **Exploratory only** — denominator invalid 95.9% of time |
| Sprint 3 NON-CAUSAL conclusions | Strong | **Downgraded** — timing correction removed |
| P16 L26: zero attn/MLP | "NON-CAUSAL" | **UNRESOLVED** — raw ASR=0.000 ⚠ may be causal |
| Mechanism "distributed circuit" | "Established" | "Consistent with distributed/redundant" |

---

## 4. Current State: What Is Established vs Unresolved

### Established (robust, no timing correction)

1. Puzzle-wrapped CoT hijacking is a real behavioral effect in both Qwen3-14B and Gemma4-E4B-IT (Sprint 1)
2. P4/P4b: Behavioral refusal direction at L26/rank3 subspace → **zero causal effect** (n=11 Qwen3, full ablation)
3. P7: Same for Gemma4-E4B-IT L17/rank4 direction (n=4)
4. Two behaviorally distinct attack patterns across models (preliminary — confirmation pending G)
5. LOGO decoding reveals direction-aligned geometric structure (AUC>0.75 both models)

### Unresolved (pending jobs or corrected code)

| Item | Blocker | Action needed |
|------|---------|---------------|
| Gate C: Arditi RD replication | 4 bugs in prior script | Run `replicate_qwen_rd_exact.py` Phase A |
| G condition for full factorial | G data missing | Submit G-condition SLURM jobs |
| `candidate_pure_cot_hijack` confirmation | G pending | After G runs, re-run `classify_attack_mechanisms.py` |
| P16 L26 block ablation (full, n=11) | Job 615190 running | Analyze when complete |
| P14 answer-phase injection (full, n=11) | Job 615191 running | Analyze when complete |
| P11 full-range patching (full, n=11) | Job 615192 running | Analyze when complete |
| P6 end-aligned patching | Contradictory at n=2 | Rerun at n=5+ with proper scorer |

### Invalid / cannot conclude from current data

- P5b head ablation (Run 1 errors, timing flips in Run 2)
- Sprint 3 NON-CAUSAL label as a group conclusion (C7 above)

---

## 5. Correction Sprint Artifacts

| File | Purpose | Status |
|------|---------|--------|
| `docs/CORRECTION_SPRINT_INITIAL_STATE.md` | Audit snapshot (git status, squeue) | ✓ Created |
| `docs/RESEARCH_MASTER_CLAIMS_REAUDIT.md` | Claim-by-claim correctness audit | ✓ Created |
| `docs/INTERVENTION_RESCORING_AUDIT.md` | Per-experiment raw vs timing-corrected ASR | ✓ Created |
| `docs/EXACT_QWEN_RD_REPLICATION_SPEC.md` | 4 bugs documented; exact Arditi protocol | ✓ Created |
| `docs/CORRECTION_SPRINT_FINAL_REPORT.md` | This file | ✓ Created |
| `poc_stage4/rescore_timing_affected_outputs.py` | Re-scorer without timing heuristic | ✓ Created |
| `poc_stage4/build_complete_factorial_manifest.py` | G-condition coverage map (44 targets found) | ✓ Created, run |
| `poc_stage4_8/build_manifest_condition_g.py` | G condition manifest builder | ✓ Created, run |
| `poc_stage4/replicate_qwen_rd_exact.py` | Fixed RD replication (all 4 bugs) | ✓ Created |
| `poc_stage4/validate_intervention_hooks.py` | Hook unit tests (9/9 pass) | ✓ Created, passing |
| `slurm_scripts/stage4_8_cond_g_qwen3.slurm` | G condition Qwen3 SLURM job (4 nodes) | ✓ Created |
| `slurm_scripts/stage4_8_cond_g_gemma.slurm` | G condition Gemma4 SLURM job | ✓ Created |
| `slurm_scripts/stage4_standard_rd_exact.slurm` | RD Phase A SLURM job | ✓ Created |
| `outputs/stage4/factorial_balanced/manifest.jsonl` | Full factorial coverage (168 tuples) | ✓ Generated |
| `outputs/stage4/factorial_balanced/g_condition_job_targets.jsonl` | 44 tuples needing G | ✓ Generated |
| `outputs/stage4_8/repeated_generation_manifest_cond_g_qwen3.jsonl` | G manifest rows (32 Qwen3) | ✓ Generated |
| `outputs/stage4_8_gemma/repeated_generation_manifest_cond_g_gemma.jsonl` | G manifest rows (12 Gemma4) | ✓ Generated |
| `outputs/audits/research_master_claims.csv` | Machine-readable claims audit | ✓ Generated |
| `outputs/audits/timing_correction_affected_outputs.csv` | Records where label flipped | ✓ Generated |
| `outputs/audits/manual_review_queue.jsonl` | Flagged for human review | ✓ Generated |

**RESEARCH_MASTER.md** updated with all corrections (807→877 lines, 27 ⚠/correction markers added).

---

## 6. Next Jobs to Submit

All three jobs below are ready to submit. They do NOT conflict with running jobs 615190–615192.

### G-condition smoke — Qwen3 (1 node)

```bash
RUN_DIR=outputs/stage4_8/runs/run_cond_g_qwen3_smoke \
sbatch --array=0 slurm_scripts/stage4_8_cond_g_qwen3.slurm
```

- Manifest: `outputs/stage4_8/repeated_generation_manifest_cond_g_qwen3.jsonl` (32 rows)
- Array index 0 = 8 examples (first goal, all seeds)
- Expected time: ~2h on L40S
- Purpose: Smoke test G condition plumbing before full run

### G-condition smoke — Gemma4 (1 node)

```bash
RUN_DIR=outputs/stage4_8_gemma/runs/run_cond_g_gemma_smoke \
sbatch --array=0 slurm_scripts/stage4_8_cond_g_gemma.slurm
```

- Manifest: `outputs/stage4_8_gemma/repeated_generation_manifest_cond_g_gemma.jsonl` (12 rows)
- Array index 0 = 3 examples
- Expected time: ~1h on L40S

### RD replication Phase A smoke (1 node)

```bash
sbatch slurm_scripts/stage4_standard_rd_exact.slurm
```

- Targets (pos=-1, layer=26) exactly — single candidate
- Requires GPU node with 80GB VRAM (L40S)
- Expected time: ~3h (direction extraction on 256 examples + KL/steering evaluation)
- Purpose: Validate all 4 bugs are fixed; confirm or deny refusal direction at L26

---

## 7. After Running Jobs Complete

### When 615190 (P16 full) completes

```bash
python -m poc_stage4.analyze_block_ablation --run-dir outputs/stage4_X/runs/block_ablation_full/
```
Focus: zero_attn/mlp_L26 raw ASR. If < baseline, this is the first potential causal evidence.

### When 615191 (P14 full) completes

```bash
python -m poc_stage4.analyze_generation_patching --run-dir outputs/stage4_X/runs/gen_patch_full/
```
Focus: gen_answer_L26 raw ASR at n=11 (smoke was ambiguous).

### When 615192 (P11 full) completes

```bash
python -m poc_stage4.analyze_causal_tracing --run-dir outputs/stage4_X/runs/causal_trace_full/
```
Focus: patch_L26_full_range vs patch_L3/L10.

### When G jobs complete

1. `python -m poc_stage4.build_factorial_attack_dataset --cond-g-run-dir <dir>`
2. `python -m poc_stage4.analyze_factorial_attack_effects` (now with G, full interaction)
3. `python -m poc_stage4.classify_attack_mechanisms` (confirm/upgrade `candidate_pure_cot_hijack`)

---

## 8. What to Tell Mahmood

The correction sprint does not undermine the research — it strengthens it:

- **Core finding preserved:** Both models show robust non-causal behavior under the tested direction ablations (P4/P4b/P7, n=11/4, no timing correction needed).
- **New open question:** P16 L26 block ablation raw ASR=0.000 under the keyword scorer. Full run (n=11, job 615190) will either establish this as causal or show it was a scorer artifact.
- **Methodology is now honest:** The timing-based label override has been removed. The G condition gap and RD replication bug are documented rather than hidden.
- **Next hard result:** Either G condition confirms/denies pure_cot_hijack classifications, or RD Phase A finds/fails to find the refusal direction. Either outcome is publishable if cleanly reported.
