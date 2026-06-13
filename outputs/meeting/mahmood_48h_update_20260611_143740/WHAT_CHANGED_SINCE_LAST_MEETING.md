# What Changed Since Last Meeting

_Prepared June 11, 2026_

---

## Major New Results

### Stage 4.7 — Multi-Prompt Replication with Length-Matched Control

**What's new:** 12 diverse source prompts under greedy decoding; includes condition F
(benign wrapper matching condition A's token count). This is the first controlled test
ruling out prompt length as the explanation.

**Key result:** A=83.3%, F=27.3% ASR (sign test p=0.016). Length is not the confound.

### Stage 4.8 — Stochastic Replication

**What's new:** 4 source prompts × 3 conditions × 5 seeds = 60 generations at
temperature=0.7. Independent replication under stochastic sampling.

**Key result:** A=60% > D=50% > F=40%. Ordering preserved under stochastic decoding.
Gaps are smaller (higher baseline variance at temperature=0.7).

Only 3 matched-outcome cells (need ≥4 for behavior-conditioned direction extraction).

---

## New Analyses

### Paper-Style ASR Report (this package)

Formatted like CoT Hijacking paper: ASR percentages, Wilson 95% CIs, paired sign tests,
complete-case handling, thinking token distribution.

### Onset Proxy Analysis (new contribution)

First attempt to measure "when does the model first engage with the harmful target"
in the thinking trace. Heuristic (LLM approach blocked by safety filters). Results
show 92% early-onset classification — likely requires validation. 66 examples prepared
for manual review.

### RL Readiness Report (new contribution)

First explicit mapping of reward components to data readiness. Defines primary reward
(StrongREJECT), secondary rewards (think tokens, onset delay), action space (wrapper type
and structural features), and explains why Layer-22 is NOT a valid primary reward.

### Literature Bridge (new contribution)

Connects our results to CoT Hijacking, Doublespeak, and Safety-before-CoT under the
unified "Delayed Safety Commitment / Reasoning-Path Hijacking" hypothesis.

---

## Mechanistic Insight Crystallized

The Layer-22 refusal direction **anti-correlates** with attack success across Stage 4.7.
This is now clearly documented with data and is the key mechanistic null result.
The direction tracks thinking depth (more thinking → lower projection), not compliance.

This shifts the story from "we found a refusal direction" to "we ruled out a mechanism
and can now focus on the right one (timing / commitment)."

---

## Pending Items (from Last Meeting)

| Item | Status |
|------|--------|
| Run Stage 4.7 with F control | ✅ Done |
| Analyze Layer-22 across conditions | ✅ Done (null result) |
| Stochastic replication (Stage 4.8) | ✅ Done |
| Onset/timing analysis | ⚠️ Heuristic only; validation needed |
| Stage 4.8 extension (≥4 matched cells) | 🔲 Ready to submit |
| Manual onset annotation | 🔲 Packet prepared; annotation not started |
| RL prototype | 🔲 Plan written; implementation not started |

---

## Infrastructure Created

- `poc_meeting/mahmood_48h_update/` — 10 new analysis scripts
- `docs/LITERATURE_BRIDGE_DELAYED_SAFETY_COMMITMENT.md`
- `docs/LITERATURE_WATCH_ALERTS.md`
- Stage 4.8 extension manifest at `outputs/stage4_8/runs/run_array_extension_20260611_143945/`
- This meeting package at `outputs/meeting/mahmood_48h_update_20260611_143740/`

---

## NEW: AutoInject-Based Optimization POC

| Item | Status |
|------|--------|
| AutoInject code audit | ✅ Done — GRPO-based RL; documented reusable components |
| Offline replay POC | ✅ Done — 108 candidate cells, 8 policies, 3 rewards |
| Reward sensitivity grid | ✅ Done — 64 weight combinations, A dominates all |
| Safe candidate template | ✅ Done — 40-run plan for online experiment |
| AutoInject adapter package | ✅ Done — poc_meeting/mahmood_48h_update/autoinject_poc/ |
| Online AutoInject run | 🔲 Pending Mahmood approval |

## NEW: Stage 4.8 Extension Submitted

Stage 4.8 extension submitted as SLURM job 538360 at 20:54 IDT on 2026-06-11.
Goals 0 and 2, seeds 106-115, conditions A/D/F. Expected: 60 new generations.
Target: push matched outcome cells from 3 to ≥4.

## NEW: Manual Onset Annotation Support Ready

- 35-row stratified subset prepared: manual_onset_review_subset_30_40.csv
- Annotation instructions written: MANUAL_ONSET_ANNOTATION_INSTRUCTIONS_SHORT.md
- Analysis script ready: analyze_manual_onset_annotations.py (run after annotating)
