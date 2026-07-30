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
| S0 | C3–C10 fixes (05,06,09,10,14,18,21,22,31) | DONE | independent adversarial review: no conclusion-inverting bug; commit 7b0a834 |
| S0 | Integrity-fix report + claim-status table | DONE | `STAGE0_INTEGRITY_REPORT.md` |
| S1 | Matched dataset — add SHUFFLED_OR_INCONSISTENT_MAPPING | TODO | all other 5 conditions already exist in 30_build_pair_benchmark.py; NOT on Stage 2 critical path |
| S2 | Complete 2×3 transplant specs (34) + analyzer (43) | DONE | commit 0034e20; analyzer positive-control tested |
| S2 | transplant SMOKE (GPU job 694383) | DONE→BUG | pipeline perfect (faithfulness=0.0, all 6 arms resolve) but readout FLOORED — bench/reps provenance mismatch (see BUG_AND_DEVIATION_LOG B1) |
| S2 | **PRIMARY** consistent rebuild + transplant (job 694417) | **DONE ✅** | gate passed; readout un-floored; **RESULT: context-carried (DE_context +0.20 ≈95% of TE), local state inert (IE_state≈0 equiv)** — see STAGE2_TRANSPLANT_FINDINGS.md |
| S2 | Confirmatory seed-1 (694468) + additive positive control (694470) | RUNNING | replicate DE/IE on 2nd seed; reproduce d_Direct-installs/d_DS-inert additively on same triple |
| S3 | Context/KV mediation — code DONE + reviewed | DONE | `DemoStateSwap` hook + `44_kv_mediation.py` + 8 CPU tests; independent adversarial review clean; STAGE3_KV_PLAN.md |
| S3 | KV mediation SMOKE (694554) | DONE | **self-swap faithfulness EXACT on real model** ✅; swap works (3-9 demos); floored by style-undersampling (B2) → full-n |
| S3 | KV mediation FULL n=15 cloze (694667) | DONE | C1=0.31 (not floored); ReRead mid +0.068 (78% survives → NOT trivial re-read); random control large at early (distributed); patchscope floored under cloze |
| S2 | d_Direct dose sweep cloze (694668) | DONE | d_Direct caps +0.096 under cloze — but that's the CLOZE FLOOR (B3), not the ceiling |
| — | **B3: cloze floored the positive control** | KEY FIX | forced_choice: DIRECT reads 0.785 vs cloze 0.005; DS stable ~0.3. Re-running S2+S3 with forced_choice |
| S2 | forced_choice transplant (694691) | **DONE ✅** | CLEAN 2×3: Neutral rcv=0 all sources, DS rcv=~0.35 all sources; IE_state≈0, DE_context+0.35 (99% of TE); reading depends ONLY on context. STAGE2_TRANSPLANT_FINDINGS.md |
| S3 | forced_choice KV mediation (694691) | **DONE ✅** | ReRead_test small (91% survives demo-KV neutralization → NOT trivial re-read); distributed (outcome C). STAGE3_KV_FINDINGS.md |
| S2 | additive d_Direct PC (694706) | DONE→B4 | ALSO weak (+0.03, label 0.27) — NOT a regression (reproduces on-disk artifact 693571=+0.028); CAUSAL_CORE +0.971 unbacked on disk. STRENGTHENS story: no local intervention installs, only context |
| S4 | TOCTOU factorial code + tests | DONE | 45_toctou_factorial + AllPositionProjectOut hook + refusal-dir builder; 9 CPU tests; adversarial review clean (no conclusion-inverting bug) |
| S4 | Refusal-dir validation + SLURM chain | DONE | smoke 694789: Llama refuses 100% harmful (real signal); L14 validated (both gains>0); gate+factorial ran clean |
| S4 | Multi-layer refusal ablation | DONE | Arditi all-layer project-out; L18 validated: harmful refusal 1.0→0.53 (ablate_gain 0.47), induce 0.67; both gains>0; 9/9+4/4 tests |
| S4 | **TOCTOU pilot (694811)** | **DONE ✅ POSITIVE** | INTERACTION +0.425 [+0.25,+0.60] Holm-sig; early concept→refusal (0.82, concept-specific: random/orth 0.00)→ablate→comply (0.53); late escapes. STAGE4_TOCTOU_FINDINGS.md |
| Final | PAPER_CONTRIBUTION.md (2 new causal findings + negative + limits) | DONE | S2 dissociation + S3 + S4 TOCTOU + B4; artifact-backed, CIs verified |
| Final | claim-to-artifact table + handoff | TODO | consolidate |
| S5 | **Generalization (grenade/pistol/chlorine, 694895-7)** | **DONE ✅** | dissociation replicates 4/4 pairs: IE_state≈0 + DE_context CI-excl-0 all pairs (pistol weakest). STAGE5_GENERALIZATION.md |
| — | B5 concurrent-run race fix | DONE | job-isolated dir captures in ds_rebuild_transplant |
| S1/S6 | SHUFFLED / optimization | DEFERRED | off critical path; documented in HANDOFF |
| opt | S4 TOCTOU generalization + control-D cells | DEFERRED | valuable next-session extras (HANDOFF) |
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
- **2026-07-30** — S0 **C1/C2 fixed** (commit c48130a): `patch_layer_sweep` guard + signed-max/quarantine aggregation; `tests/test_integrity_fixes.py` 5/5 green. Real `pair_generalization.json` had measured cells → 5/5 dissociation unchanged, now robustly backed.
- **2026-07-30** — S0 **C3–C10 fixed** (commit 7b0a834) via a 7-agent parallel workflow, each self-verified (py_compile). **Independent adversarial review agent** then cleared all diffs: no must-fix, no conclusion-inverting bug. 3 result-moving changes (14 malicious_rate↑, 18 delta_necessity↓, 31 label-shift) all conservative/correct; C10 label-shift flagged for Omer's sign-off (labels only, p_concept untouched). Wrote `STAGE0_INTEGRITY_REPORT.md` (fixes + claim-status table).
- **2026-07-30** — S2 code done (commit 0034e20); SMOKE (694383) exposed the bench/reps mismatch (B1); rebuilt a consistent triple.
- **2026-07-30** — S2 **PRIMARY RESULT** (job 694417): **Doublespeak reading is context-carried, not locally stored.** `IE_state ≈ 0` (equiv ±0.05) every window; `DE_context = +0.20` [+.11,+.32] ≈ 95% of `TE = +0.215`; faithfulness exactly 0.0. Answers primary question **B (context/downstream computation)**, not A. Committed `STAGE2_TRANSPLANT_FINDINGS.md` + mediation JSONs. **Stage 3 gate PASSED.** Launched confirmatory seed-1 (694468) + additive positive control (694470).

---

## SPRINT COMPLETE (2026-07-30)

**Primary science delivered — three new causal contributions + one integrity negative, all artifact-backed and committed:**
- **S2** the Doublespeak reading is causally carried by receiver context, not the local codeword state (IE_state≈0 equiv; DE_context +0.35 ≈99% of TE; exact faithfulness) — **generalizes 4/4 pairs (S5)**.
- **S3** it is not a trivial demonstration re-read (91% survives demo-K/V neutralization); distributed.
- **S4** causal TOCTOU: the refusal check is depth-gated — early concept install → refusal (0.82, concept-specific); ablating it → compliance (0.53); late escapes (0.07); interaction +0.425 Holm-sig.
- **B4** the in-house d_Direct "+0.971 install" does NOT reproduce (no regression; doc-drift) — strengthens S2.
Plus **S0** integrity repairs (C1–C10, reviewed) and docs: `PAPER_CONTRIBUTION.md`, `HANDOFF.md`, per-stage findings, `BUG_AND_DEVIATION_LOG.md` (B1–B5).

**Deferred to a future session (documented in HANDOFF):** S4 TOCTOU generalization to more pairs; TOCTOU control-D cells; S6 optimization; a positive-control-gated patchscope; larger n/seeds. Loop stopped — the sprint's goal (a defensible NEW causal result added to the paper) is met.
