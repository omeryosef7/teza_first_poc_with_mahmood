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

---

## B2 — Stage 3 KV smoke floored by style-undersampling; modest bench magnitudes (2026-07-30)

**What.** The Stage 3 KV-mediation SMOKE (job 694554, n=4) returned all cells ~0.01–0.03 → `ReRead_test`≈0, uninformative. Investigated before any full run.

**Diagnosis (NOT a bug).**
- **`DemoStateSwap` works end-to-end:** the real-model **self-swap faithfulness is exact** (`C1_selfswap`==`C1`=0.0146), and C3/C4 actually swapped **3–9** demonstration codewords (`n_demo_swapped`). `find_word_occurrences` correctly finds all codewords (12 in the academic|12 prompt). The `n_demo_swapped=0` first seen was on C1/C2, which do not swap by design.
- **The floor is style-undersampling.** DS concept reading is strongly **style-dependent**: academic=0.004, dialogue=0.045 in the smoke; the 694417 full-set average of **0.21** is carried by the other styles (narrative/news/technical; max single-prompt 0.85). The n=4 smoke (first-by-sid) is academic/dialogue-heavy → floored. Fix: **run full-n (all 5 styles)** — no code change. → job 694667 (n=15).
- The current bench is a **legitimate gpt-4o-mini API build** (`_meta.offline=False`, seed 7), not an offline/template build.

**Scientific note (magnitudes; for Omer's awareness).** On this bench absolute effects are **modest and style-dependent**: DS natural reading ~0.2–0.3 (gate DS−Neutral p_concept +0.31), and the additive `d_Direct` at α=1.0 installs only **+0.019** (peak L4) — vs CAUSAL_CORE's near-ceiling +0.97 on the (now-overwritten) Jul-29 bench. The +0.02 is likely a **dose** effect (α=1.0 single point) not a bench defect, since the DS attack itself gives +0.31 and `d_Direct` still *exceeds all 60 matched controls* (specific, just small). → job 694668 runs a **dose sweep** (α=1,2,4,8) to get the install curve as a convincing positive control. The **dissociation is relative and holds regardless of scale**: context transplant (+0.20) vs local-state transplant (0). If a larger absolute effect is wanted for the paper, a stronger/higher-signal bench or readout (e.g. featuring the patchscope `ps_concept` readout 44 already records) is the lever — flagged, not blocking.
