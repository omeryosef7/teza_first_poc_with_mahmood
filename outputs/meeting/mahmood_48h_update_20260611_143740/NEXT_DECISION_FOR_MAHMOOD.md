# Next Decisions for Mahmood

_June 2026 | Omer Yosef_

---

## Decision 1 — Submit Stage 4.8 Extension (LOW EFFORT, HIGH VALUE)

**Context:** Currently 3 matched-outcome cells; need ≥4 for behavior-conditioned
direction extraction. Extension is ready: manifest created, SLURM script ready.

**Ask:**
> Approve submission of Stage 4.8 extension job targeting goals 0 and 2,
> seeds 106–115 (60 additional stochastic generations, ~4–8h cluster time).

**Command:**
```bash
RUN_DIR=outputs/stage4_8/runs/run_array_extension_20260611_143945
sbatch --array=0,2 --export=ALL,RUN_DIR="$RUN_DIR" \
    slurm_scripts/stage4_8_repeated_generations_array.slurm
```

**Outcome if approved:** Likely ≥4 matched cells → enables behavior-conditioned
direction extraction.

---

## Decision 2 — Prioritize Manual Onset Annotation (MEDIUM EFFORT, HIGH VALUE)

**Context:** Onset proxy shows 92% "early" classification, which is likely partly
artefactual. Manual validation would tell us if the timing hypothesis is real.

**Ask:**
> Allocate 1–2 days of researcher time to annotate 20–50 examples from
> `manual_onset_review_packet.csv`. Labels: `first_target_engagement / before_target /
> after_target / no_engagement / unclear`.

**Outcome if approved:**
- If validated: strong new contribution "onset timing predicts attack success"
- If invalidated: important null result; heuristic proxy abandoned; alternative
  onset measurement designed (token-level attention patterns instead of keyword overlap)

---

## Decision 3 — Confirm Paper Framing (DISCUSSION, STRATEGIC)

**Context:** Two possible framings:

**Option A: Attack Characterization Paper**
> "We systematically characterize the puzzle-wrapper attack on thinking models,
> providing the first controlled evidence with a length-matched baseline (F condition),
> and ruling out the simple linear-direction mechanism."
>
> Contribution: behavioral evidence + mechanistic null

**Option B: Reasoning-Path Hijacking Mechanism Paper**
> "We propose Delayed Safety Commitment as the mechanism of thinking-model jailbreaks,
> validated by onset timing analysis and grounded in three related papers."
>
> Contribution: behavioral evidence + mechanism theory + timing evidence
> (requires onset validation before submission)

**Recommendation:** Option A is publishable now. Option B is stronger but requires
2–4 more weeks for onset validation and analysis.

**Ask:**
> Which framing aligns with Mahmood's vision? Option A for earlier submission,
> or Option B if we have time for the mechanism story?

---

## What Does NOT Need a Decision

- The Layer-22 null result is settled (do NOT revisit causal interventions without
  a new approach)
- The RL implementation is NOT the immediate next step (see RL_NOT_YET_RATIONALE.md)
- Stage 4.6 data is complete and needs no further work
- The SLURM infrastructure is working; no changes needed

---

## Recommended Sequence

```
NOW:
  Submit Stage 4.8 extension (Decision 1, ~10 minutes)

THIS WEEK:
  Manual onset annotation (Decision 2, ~1–2 days)
  Analyze extension results when cluster job completes

NEXT MEETING:
  Report onset annotation findings
  Decide on paper framing (Decision 3) with full data
```

---

## Decision 4 (NEW): Approve Constrained Online AutoInject-Style Run

**What we've done:** Inspected AutoInject (GRPO-based RL), built a safe offline adapter,
and ran offline replay showing Condition A dominates all policies and reward definitions.

**The decision:** Approve a small online AutoInject-style experiment:
- Actions = {A, D, F, E} structural wrapper choices
- Prompts = same 12 existing research prompts from Stage 4.7 (no new harmful content)
- Reward = sr_success (primary), sr_score (secondary)
- Budget = ~40 evaluations (2 goals × 4 conditions × 5 seeds)
- Infrastructure = same Slurm pipeline as Stage 4.7/4.8

**What this would add:**
1. Validate that A is robust to variation (not just a dataset artifact)
2. Generate matched success/failure pairs for behavior-conditioned direction extraction
3. First real test of whether AutoInject reward framing guides efficient search in our domain

**Template:** See `autoinject_poc/safe_autoinject_candidate_template.jsonl` for exact plan.

**If yes:** Run immediately using existing infrastructure.  
**If no:** Offline POC stands as a complete feasibility demonstration for the thesis.

---

## Recommended Sequence (Updated)

```
DONE (this sprint):
  ✅ Submitted Stage 4.8 extension (Job 538360)
  ✅ AutoInject code audit + offline POC
  ✅ Manual onset annotation subset (35 rows) ready

THIS WEEK:
  Manual onset annotation (~30-45 min)
  Wait for Stage 4.8 extension results

NEXT MEETING:
  Decision 4: Approve/reject online AutoInject run
  Report Stage 4.8 extension outcome
  Report onset annotation findings

FRAMING:
  Option A — Attack characterization / publishable now
  Option B — Mechanism paper: delayed safety commitment (2-4 more weeks)
```
