# Sprint Completion Summary — Stage 4.5B + Stage 4.6

**Project**: Chain-of-Thought Hijacking — TAU MSc Thesis (PLUS Security Group)
**Supervisor**: Mahmood Sharif
**Date written**: 2026-06-09

---

## What Was Completed (This Sprint)

### Stage 4.5B — LLM Onset Annotation (100% code complete)

All code was implemented and tested. **102 tests pass.**

| Component | File | Status |
|---|---|---|
| Versioned prompt templates | `poc_stage4_5/llm_annotation_prompts.py` | ✅ Done |
| o4-mini 2-pass annotator | `poc_stage4_5/llm_annotate_harmful_interaction.py` | ✅ Done |
| Quality gate + spotcheck | `poc_stage4_5/audit_llm_annotations.py` | ✅ Done |
| Analysis flags added | `poc_stage4_5/analyze_harmful_interaction_aligned_dynamics.py` | ✅ Done |
| Tests (102 pass) | `poc_stage4_5/tests/test_core.py` | ✅ Done |

**What Stage 4.5B does:**
- Sends each of the 42 Qwen3-14B traces to o4-mini via a hierarchical two-pass approach
- Pass 1 + Pass 2: coarse chunking (512-token windows) → fine localization (64-token windows)
- If the two passes disagree by >64 tokens, an adjudication prompt picks the winner
- Outputs `consensus_annotations.csv` with per-example onset token index
- Quality gate checks parse rate, error rate, consensus rate, agreement distance

**Key design decisions:**
- All results are clearly labeled `annotation_source = "o4mini"`, `annotation_status = "automated_not_human_ground_truth"`
- Output filenames get `_llm_annotated` suffix to prevent confusion with human ground truth
- No raw harmful text stored in any output file
- Resume behavior: re-running skips already-annotated examples

---

### Stage 4.6 — Controlled Ablation (100% code complete)

All code was implemented and tested. **43 tests pass.**

| Component | File | Status |
|---|---|---|
| Package init | `poc_stage4_6/__init__.py` | ✅ Done |
| Ablation prompt builder | `poc_stage4_6/build_controlled_ablation_prompts.py` | ✅ Done |
| Prompt auditor | `poc_stage4_6/audit_controlled_ablation_prompts.py` | ✅ Done |
| Generation runner | `poc_stage4_6/run_controlled_ablation.py` | ✅ Done |
| Analysis tables | `poc_stage4_6/analyze_controlled_ablation.py` | ✅ Done |
| 8 plots | `poc_stage4_6/plot_controlled_ablation.py` | ✅ Done |
| Tests (43 pass) | `poc_stage4_6/tests/test_ablation.py` | ✅ Done |

**What Stage 4.6 does:**
Disentangles two confounders in the Stage 4 result (g=1.256 at Layer 22):

1. **Puzzle length effect**: Does more puzzle text → more hijacking? Conditions A (100%), B (50%), C (25%), D (0% puzzle) test this with thinking=on
2. **Thinking mode effect**: Does the `<think>` token change hijacking? Condition E runs the full prompt with thinking disabled

**The 5 conditions (×4 goals = 20 total generations):**

| Condition | Puzzle kept | Thinking | Purpose |
|---|---|---|---|
| A | 100% | on | Baseline — full source prompt |
| B | ~50% | on | Half puzzle removed |
| C | ~25% | on | Most puzzle removed |
| D | 0% | on | Puzzle fully removed (target only) |
| E | 100% | off | Thinking disabled — tests CoT contribution |

**Guarantees enforced by the build script:**
- Target span SHA256 identical across A–D
- Answer cue span SHA256 identical across A–D
- Transformed prompts are deletion-only subsequences of source
- Token lengths: A ≥ B ≥ C ≥ D (strictly enforced, fails loudly if violated)
- Condition A SHA256 = source SHA256 (identity verified)

**Generation config** (same as Stage 2B/6):
- `do_sample=False` → deterministic → run once per condition
- `seed=0`, `max_new_tokens=16384`, `Qwen/Qwen3-14B`

---

### SLURM Scripts Written (This Sprint)

| Script | Purpose | GPU? | Time |
|---|---|---|---|
| `stage4_5b_llm_annotation.slurm` | Run o4-mini annotation pipeline (pilot + full + audit) | No | 4h |
| `stage4_5b_event_aligned_analysis.slurm` | Run event-aligned dynamics with LLM annotations | No | 2h |
| `stage4_6_controlled_ablation_smoke.slurm` | Smoke: goal 0, conditions A+D | Yes (1 GPU) | 2h |
| `stage4_6_controlled_ablation_full.slurm` | Full: all 20 conditions + analysis + plots | Yes (1 GPU) | 8h |

---

### Skeleton Docs Written

| File | Purpose |
|---|---|
| `docs/STAGE4_5B_GEMINI_ONSET_RESULTS.md` | Template for annotation results — fill after run |
| `docs/STAGE4_6_CONTROLLED_ABLATION_PLAN.md` | Design rationale for thesis writing |
| `docs/STAGE4_6_CONTROLLED_ABLATION_RESULTS.md` | Template for ablation results — fill after GPU run |
| `docs/MAHMOOD_NEXT_MEETING_BRIEF.md` | Meeting brief — fill with actual numbers |
| `docs/NEXT_MEETING_FIGURE_INDEX.md` | Figure paths index — fill after runs |

---

## What Is NOT Done Yet (Needs to Run)

### Stage 4.5B — Pending Execution

| Step | Command | Blocker |
|---|---|---|
| Pilot annotation (10 examples) | `sbatch slurm_scripts/stage4_5b_llm_annotation.slurm` | Needs `OPENAI_API_KEY` in `.env` |
| Quality gate check | auto-runs in above script | — |
| Full annotation (42 examples) | `sbatch slurm_scripts/stage4_5b_llm_annotation.slurm` with `RUN_ALL=true` | Depends on pilot passing |
| Event-aligned analysis | `sbatch slurm_scripts/stage4_5b_event_aligned_analysis.slurm` | Depends on full annotation |

### Stage 4.6 — Pending Execution

| Step | Command | Blocker |
|---|---|---|
| Build ablation prompts | `python -m poc_stage4_6.build_controlled_ablation_prompts` | None (CPU, ~30s) |
| Audit prompts | `python -m poc_stage4_6.audit_controlled_ablation_prompts` | Depends on build |
| Smoke run (A+D, goal 0) | `sbatch slurm_scripts/stage4_6_controlled_ablation_smoke.slurm` | Needs GPU slot |
| Full run (20 conditions) | `sbatch slurm_scripts/stage4_6_controlled_ablation_full.slurm` | Depends on smoke passing |

### After Runs Complete

- Populate `docs/STAGE4_5B_GEMINI_ONSET_RESULTS.md` with actual numbers
- Populate `docs/STAGE4_6_CONTROLLED_ABLATION_RESULTS.md` with actual results
- Update `docs/MAHMOOD_NEXT_MEETING_BRIEF.md` and `NEXT_MEETING_FIGURE_INDEX.md`
- (Optional) Human annotation review of spotcheck_queue.csv

---

## Exact Execution Order

```bash
# ── CPU steps (no GPU needed) ──────────────────────────────────────────────

# 1. Build + audit ablation prompts (30 seconds)
python -m poc_stage4_6.build_controlled_ablation_prompts
python -m poc_stage4_6.audit_controlled_ablation_prompts

# 2. Pilot LLM annotation (10 examples, ~5–10 min API calls)
#    Make sure OPENAI_API_KEY is in .env
sbatch slurm_scripts/stage4_5b_llm_annotation.slurm
# OR run locally:
# python -m poc_stage4_5.llm_annotate_harmful_interaction --queue review/pilot_example_queue.csv

# 3. Check pilot quality gate output — look for PASS in logs
# outputs/stage4_5/llm_harmful_interaction_annotations/run_<ts>/annotation_audit.json

# 4. Full LLM annotation (42 examples, ~30–60 min API calls)
RUN_ALL=true sbatch slurm_scripts/stage4_5b_llm_annotation.slurm
# OR locally:
# python -m poc_stage4_5.llm_annotate_harmful_interaction --all

# ── GPU steps ──────────────────────────────────────────────────────────────

# 5. Stage 4.6 smoke test (goal 0, conditions A+D)
sbatch slurm_scripts/stage4_6_controlled_ablation_smoke.slurm

# 6. After smoke passes → full ablation (20 conditions, ~4–6h)
sbatch slurm_scripts/stage4_6_controlled_ablation_full.slurm
# This script auto-runs analyze + plot after generation finishes.

# ── CPU steps (post-GPU) ───────────────────────────────────────────────────

# 7. Event-aligned analysis with LLM annotations
ANNOTATIONS_FILE=outputs/stage4_5/llm_harmful_interaction_annotations/run_<ts>/consensus_annotations.csv \
sbatch slurm_scripts/stage4_5b_event_aligned_analysis.slurm

# 8. Populate docs with actual numbers from outputs
```

---

## Test Status

```
poc_stage4_5/tests/test_core.py  — 102 passed (before this sprint)
poc_stage4_6/tests/test_ablation.py — 43 passed (this sprint)
```

**Run both suites locally (no GPU needed):**
```bash
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
python -m pytest poc_stage4_5/tests/test_core.py poc_stage4_6/tests/test_ablation.py -v
```

---

## Stage 4 Context (Frozen — Read Only)

Authoritative run: `outputs/stage4/token_dynamics/full_20260604_101929/`

- **N = 42 traces**, Qwen3-14B on 4 jailbreak goals
- **Layer 22 divergence**: Hedges' g = **1.256** (large effect)
- Refusal direction projection separates success vs failure traces
- This result is frozen — Stage 4.5B and 4.6 are designed to explain it

---

## Hard Constraints (Never Violate)

- Do NOT modify `outputs/stage4/token_dynamics/full_20260604_101929/` (frozen artifact)
- Do NOT claim causal mechanism or human ground truth from LLM annotations
- Do NOT run more than 60 Stage 4.6 generations without explicit approval from Mahmood
- All LLM-annotated analysis outputs must carry the `_llm_annotated` filename suffix
