# Stage 4.8 Extension — Submission Record

## Submission

**Status:** SUBMITTED  
**Date/Time:** Thu 11 Jun 2026, 20:54:44 IDT  
**Job ID:** 538360  
**Array tasks:** 538360_0 (goal index 0) and 538360_2 (goal index 2)  

**Exact command:**
```bash
sbatch --array=0,2 \
  --export=ALL,RUN_DIR=outputs/stage4_8/runs/run_array_extension_20260611_143945 \
  slurm_scripts/stage4_8_repeated_generations_array.slurm
```

**Output directory:** `outputs/stage4_8/runs/run_array_extension_20260611_143945/`

---

## What This Extension Is Designed to Unlock

### Background
The main Stage 4.8 run (Job 534979, completed 2026-06-11 01:08–02:48) generated 30 examples
across seeds 101–105, goals 0 and 2, conditions A/D/F. The analysis found only **3 matched
outcome cells** (example × condition pairs where both sr_success=True and sr_success=False
outcomes were observed across seeds). The downstream behavior-conditioned direction extraction
requires **≥4 matched cells**.

### What the Extension Adds
- **Seeds:** 106–115 (10 additional seeds per example/condition cell)
- **Goals covered:** 0 and 2 (the two goals with best existing cell coverage)
- **Conditions:** A (full puzzle + thinking), D (bare target + thinking), F (length-matched benign + no thinking)
- **Planned generations:** 60 total (2 goals × 3 conditions × 10 seeds)
- **Expected row count in run_summary.jsonl after completion:** 30 (existing) + 60 = 90 rows

### Why More Seeds Help
With only 5 seeds per cell, a cell where P(success) ≈ 0.5 may show all-success or all-failure
by chance, failing to qualify as a matched cell. Adding seeds 106–115 increases the probability
that marginal cells reveal mixed outcomes. Even one additional matched cell would push from 3
to 4 and unlock the downstream representations job.

### What Becomes Possible at ≥4 Matched Cells
- Behavior-conditioned direction extraction: compare Layer-22 hidden states on success vs.
  failure runs within the same example and condition
- "Provisional harmful-vs-harmless contrast direction" becomes computable
- Downstream `stage4_8_compute_representations.slurm` auto-submits (per the SLURM script logic)

### Expected Contribution to Mechanistic Analysis
- More matched success/failure cells for behavior-conditioned analysis
- Better variance decomposition (within-example vs. between-example variance in sr_score)
- Stronger empirical basis for the "delayed safety commitment" narrative

---

## SLURM Script Details

**Script:** `slurm_scripts/stage4_8_repeated_generations_array.slurm`  
**Resources per task:** 8 CPUs, 64 GB RAM, 1 GPU, 4 h runtime  
**Partition:** killable  
**Nodes:** n-802, n-803, n-804, n-805  
**Resume-safe:** Yes — skips already-present run_ids  

Array index mapping in script:
- index 0 → goal_index 0
- index 2 → goal_index 2

---

## Pre-Submission Check

Before submission, verified:
- No Stage 4.8 jobs were running (`squeue -u $USER` returned empty)
- Most recent prior run (534979) completed successfully at 2026-06-11T02:48 IDT
- Extension run directory `run_array_extension_20260611_143945/` already exists with manifest
- Extension status.json showed `planned_not_started`
- Slurm script exists at correct path

---

## Post-Run Update (21:10 IDT, 2026-06-11)

**Job 538360 completed at 21:04 IDT — but 0 new generations were produced.**

Both array tasks (538360_0 and 538360_2) completed in ~10 minutes. All 30 generation
tasks were skipped because seeds 101-105 were already present in the extension run
directory from a previous prepare step.

**Root cause:** The SLURM script generates run_ids with seeds 101-105. These were
already present in `run_summary.jsonl`. The extension manifest targets seeds 106-115,
but the script does not read the manifest's seed parameter.

**Next action required:** Modify SLURM script to accept a SEED_START/SEED_END parameter
and resubmit with seeds 106-115. See STAGE48_EXTENSION_STATUS.md for full details.

**Impact on meeting:** The extension is infrastructure-ready but needs a 1-line fix
to actually produce new seeds. This is an honest null result to report.
