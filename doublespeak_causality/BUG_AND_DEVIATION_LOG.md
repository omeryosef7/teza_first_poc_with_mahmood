# Bug & Deviation Log — NEXT_CAUSAL_SPRINT

Chronological. Each entry: what, evidence, impact, resolution.

---

## B1 — Stage 2 smoke floored: bench/reps provenance mismatch (2026-07-30)

**What.** The Stage 2 transplant SMOKE (job 694383) ran end-to-end and the pipeline was mechanically perfect (self-transplant faithfulness *exactly* 0.0, n=140; all 6 arms resolved), BUT the primary `p_concept` readout was floored: the entire 2×3 table sat at ~0.000–0.010, including the `Neutral|h_Direct` positive control and the DS baseline.

**Evidence.** Compared arm-level mean `p_concept` between the prior canonical replace run (`...221157_693597`, git 6ee794e1) and my smoke (`...151840_694383`):
- Prior `DS_from_Neutral` mean **0.2187** (max 0.85), `identity` max **0.82**.
- Mine `DS_from_Neutral` mean **0.0048** (max 0.013), `identity` max **0.013** — floored.
- The `identity` arm uses **no reps** (just `semantic_score` of the bench prompt), yet it too was floored → the *current bench prompts* read ~0 concept under the cloze readout.

**Root cause.** `pair_carrot_bomb.json` on disk has mtime **Jul 30 01:25** (a benchmark rewrite), but the reps I reused were captured **Jul 29 21:53** — i.e. the bench file was overwritten *after* the reps (and after the prior consistent run). Feeding the Jul-30 bench prompts with Jul-29 reps is a bench/reps mismatch; the receiver forward runs the new (different) prompts while `source_vec` indexes the old reps, flooring the readout. The Jul-29 readout-validation artifact (`pair_readout_...215216`) shows `gate_pass_any: true` on the pair *as it was then*, confirming the pair itself produces signal.

**Impact.** No committed scientific claim is affected (the smoke was a pre-flight check, explicitly n=4/THIN/uncommitted). The Stage 2 transplant simply needs a **consistent** (bench, reps, directions) triple.

**Resolution.** New gated chain `slurm_scripts/ds_rebuild_transplant.slurm`: rebuild reps (32) + directions (33) from the **current** bench, **gate on the readout validator (31, `gate_pass_any`)** before spending compute, then run the transplant (34) + mediation (43). If the current bench fails the gate, fall back to a fresh bench build (30, API) — which is also where Stage-1 SHUFFLED will be added. The mismatch is a data-hygiene lesson: **immutable, provenance-stamped bench/reps/dir triples** (the bench should never be overwritten in place).

**Follow-up.** Stage-1 SHUFFLED_OR_INCONSISTENT_MAPPING will be added in a fresh bench build and re-run as an extra control; it is off the Stage-2 critical path.
