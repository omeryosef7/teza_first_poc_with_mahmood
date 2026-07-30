# Next Causal Sprint — Progress Log

**Plan:** `doublespeak_causality/NEXT_CAUSAL_SPRINT_PLAN.md`
**Started:** 2026-07-30
**Primary model:** Llama-3.1-8B-Instruct · **Primary pair:** CARROT ↔ BOMB
**Branch:** behavioral-causality-sprint

Status legend: `TODO` · `RUNNING` · `DONE` · `BLOCKED` · `SKIPPED(reason)`
Claim labels: `CONFIRMATORY` · `EXPLORATORY` · `NEGATIVE` · `INVALIDATED` · `UNVERIFIED` · `BLOCKED`

---

## Live status board

| Stage | Item | Status | Notes |
|---|---|---|---|
| Recon | Repo + defect map + code catalog | DONE | 5-agent audit; all C1–C10 confirmed STILL PRESENT (commit 8a9b91b did not fix them) |
| S0 | C1 patch-sweep bound (07) | DONE | `ds_common.patch_layer_sweep(R)` → `range(R)`; test green |
| S0 | C2 pair aggregation (41) | DONE | signed-max install; missing d_DS never affirms inert; 5/5 tests green |
| S0 | C3 readout contamination (05) | TODO | same class as C1 — exclude final block |
| S0 | C4 timing dead patchscope (06) | TODO | `ps` never called |
| S0 | C5+C6 knockout controls (09/10) | TODO | pool before cw_last; record req_located; mask-dim guard |
| S0 | C7 malicious_rate/judge health (14) | TODO | scored partition + health gate |
| S0 | C8 empty-completion guard (18) | TODO | port EMPTY guard from 19 |
| S0 | C9 axis leakage (21/22) | TODO | fit axis inside fold |
| S0 | C10 classify_answer first-match (31) | TODO | p_concept unaffected (safe); label bias only |
| S1 | Matched dataset — add SHUFFLED_OR_INCONSISTENT_MAPPING | TODO | all other 5 conditions already exist in 30_build_pair_benchmark.py |
| S2 | **PRIMARY** State × receiver-context transplant | TODO | run_replace already covers 3/6 cells; add DS_from_Direct + 2 self-transplant diagonals |
| S3 | Context/KV mediation + path patching | TODO | Gated on S2 |
| S4 | Concept × refusal factorial (TOCTOU causal test) | TODO | |
| S5 | Generalization (≥3 pairs, +1 arch) | TODO | Gated on primary |
| S6 | Optimization (conditional) | TODO | Gated on 5 optimization gates |

---

## Reconnaissance findings

### Known code defects (from MERGED_MASTER_PLAN.md §II.1)

| ID | Sev | Location | Defect | Stage 0 mapping |
|---|---|---|---|---|
| C1 | 🔴 | `07_patchscope_readout.py:135` | Sweep `range(R+1)` includes readout layer R → overwrites readout vector; `max` over L incl. R inflates false positives | Patch sweep bounds |
| C2 | 🔴 | `41_aggregate_pairs.py:80,59` | `None→0<0.05` counts missing cell as inert; `max(abs)` masks real +install | Pair aggregation |
| C3 | 🟠 | `05_run_activation_patching.py:113` | Same readout-layer contamination as C1 | Patch sweep bounds |
| C4 | 🟠 | `06_run_timing.py:114` | Patchscopes instantiated but never called; only refusal stored | Judge/readout health |
| C5 | 🟠 | `09_attention_knockout.py:125` | `rand_demos_matched` draws positions after codeword → fewer keys, n recorded equal | Control matching |
| C6 | 🟠 | `09:113` / `10:42` | Silent fallback / silent no-op on locate/mask failure | Hook-fire verification |
| C7 | 🟠 | `14_behavioral_eval.py:103,96` | `malicious_rate` on different partition than `labels`; no judge-health gate; status always COMPLETE | Behavioral labeling/judge health |
| C8 | 🟠 | `18_run_behavioral_necessity.py:197` | No empty-completion guard; empty gen scored BENIGN → counted as necessity flip | Empty generations |
| C9 | 🟠 | `21_extract_behavioral_features.py:96` | Harmful axis from all concepts, then GroupKFold claims out-of-concept | CV leakage |
| C10 | 🟠 | `31_validate_readouts.py:81` | `classify_answer` returns first matched word (biases toward null); `p_concept` unaffected | Token localization/readout |

Remediation recipe (MERGED_MASTER_PLAN.md lines 155–163) already specifies fixes. **Open question resolved by audit:** which are already applied (commit 8a9b91b applied some) vs still open.

### Prior verified state (do not re-run as new)
- `d_Direct` causally installs concept reading — dose-monotone, near-ceiling late (+0.971), beats 180 controls, reverses under projection, generalizes 5 pairs / 4 harm cats (inert 5/5, installs 4/5), replicates Qwen3-14B. **CONFIRMATORY.**
- `d_DS` causally inert 5/5 pairs. **CONFIRMATORY (negative).**
- Causal objective anti-predicts held-out ASR; behavioral selection beats it. **NEGATIVE.**
- Embedding distance does not predict hijack strength (r=−0.189). **NEGATIVE.**

### What is genuinely NEW in this sprint
Stage 2 **state × receiver-context transplant**: patch h_source into a *different* receiver context. AUDIT UPDATE: `34_intervention_sweep.py::run_replace()` (`--mode replace`) ALREADY does cross-context full state-replacement for 3 of 6 cells: **Neutral←h_DS** (Neutral_from_DS), **Neutral←h_Direct** (Neutral_from_Direct), **DS←h_N** (DS_from_Neutral), each with a `*_SHUFFLED` donor control. **Missing cells to add** (small, additive edit to the `specs` list, lines ~366–370): `DS_from_Direct` (DS←h_Direct), and the two self-transplant diagonal controls `Neutral_from_Neutral` (Neutral←h_N) and `DS_from_DS` (DS←h_DS) — the current `identity` arm is an alpha=0 no-patch baseline, NOT a cross-forward self-replacement, so it does not control the transplant machinery. `05_run_activation_patching.py` has the true diagonal self-transplant (DS←DS) for reference.

### Engineering conventions (audit)
- **Env:** `source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate poc_stage2` (python has numpy 2.4.6, torch 2.7.1+cu126). PROJECT_DIR = repo root.
- **SLURM:** `--account=gpu-research --partition=killable` + **L40S nodelist pin** + runtime `nvidia-smi` L40S guard (`exit 1` if not L40S); `--gpus=1 --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=64G --time=04:00:00–06:00:00`; logs `logs/<job>_%j.out`. Submit from PROJECT_DIR: `sbatch slurm_scripts/<name>.slurm`. Config via `${VAR:-default}` env overrides (avoid comma-lists in `--export`). Project rules: no SLURM deps, ≤6 parallel, L40S only, no trimming.
- **Existing tests:** `tests/test_layerpatch_synthetic.py` (LayerPatch, no GPU), `tests/test_localization.py`, `tests/test_pair_benchmark.py`, and new `tests/test_integrity_fixes.py` (C1/C2).

### Dataset conditions (audit)
Builder `30_build_pair_benchmark.py` emits: `DIRECT_CONCEPT(+NODEMO)`, `NEUTRAL_CODEWORD(+NODEMO)`, `DOUBLESPEAK`, `BENIGN_REMAP` (=BENIGN_ICL), `UNRELATED_TARGET`, `REPEATED_CODEWORD` (=REPETITION_ONLY). Maps cleanly to the plan's conditions **except** SHUFFLED_OR_INCONSISTENT_MAPPING (UNRELATED_TARGET is a *consistent* remap of a different concept — isolates target identity, not mapping coherence). Stage 1 = add the scrambled/inconsistent-mapping condition.

---

## Execution log

- **2026-07-30** — Wrote plan `NEXT_CAUSAL_SPRINT_PLAN.md`. Reconnaissance: mapped repo, extracted C1–C10 from MERGED_MASTER_PLAN.md.
- **2026-07-30** — Ran 5-agent audit workflow (`ds-causal-recon`): confirmed all C1–C10 STILL PRESENT; cataloged `ds_common` utilities; found `run_replace` covers 3/6 transplant cells; dataset missing only SHUFFLED; extracted SLURM/env conventions.
- **2026-07-30** — S0 **C1 fixed**: added `ds_common.patch_layer_sweep(R)` (single source of truth for C1+C3), routed `07_patchscope_readout.py` through it (`range(R)`, L≤R-1). S0 **C2 fixed**: `41_aggregate_pairs.py` uses signed-max for install arm, abs-max only for the inert challenge, and a missing d_DS window is now quarantined (`pairs_d_DS_incomplete`) instead of silently affirming inert. Added `tests/test_integrity_fixes.py` (5 tests, all green); existing layerpatch/localization tests still green. NOTE: real `pair_generalization.json` had measured cells, so the 5/5 dissociation claim is unchanged — now robustly backed. Next: C3–C10.
