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

---

## B3 — Compression was the READOUT (cloze), not the bench (2026-07-30)

**What.** B2 flagged modest magnitudes (d_Direct install capped ~+0.1, patchscope floored). Before treating this as a bench-rebuild fork, checked the readout-validation per-readout table (job 694417 `readout_summary.json`):

| condition | cloze | forced_choice | one_word |
|---|---|---|---|
| NEUTRAL_CODEWORD | 0.000 | 0.000 | 0.000 |
| DOUBLESPEAK | 0.307 | 0.353 | 0.209 |
| **DIRECT_CONCEPT** | **0.005** | **0.785** | 0.007 |

**Root cause.** The **cloze** readout FLOORS `p_concept` for DIRECT_CONCEPT (0.005), which is exactly the source of the `d_Direct`/PORT_Direct positive control — so the positive control looked crippled purely because of the readout, not the mechanism. `forced_choice` (a validated readout, gate-passed, NEUTRAL still clean at 0.000) has full dynamic range (DIRECT 0.785). The DS attack signal itself is stable across readouts (~0.3).

**Resolution.** Re-run Stage 2 transplant + Stage 3 KV mediation with `--readout forced_choice` (parametrized `ds_rebuild_transplant.slurm`, now defaults to forced_choice + appends the 44 KV step; n=15 for all styles). This gives a **working positive control** (d_Direct source decodes 0.785) so IE_state≈0 / PORT_Direct are interpretable against a real installable reference — **without** rebuilding the bench. NOT a consequential fork after all; the cloze Stage-2 result stands (DS signal ~equal), this sharpens the positive control and the KV dynamic range.

**Note on patchscope=0.** Under cloze the confound-free patchscope readout returned 0 for all cells. Re-checking under forced_choice will show whether that was a cloze artifact or a genuine "concept not in the query codeword's local rep" confirmation (which would be consistent with IE_state=0). Verify the patchscope positive control (DIRECT rep must decode >0) in the new run before citing ps_concept.

---

## B4 — CAUSAL_CORE "d_Direct installs +0.971" does NOT reproduce; no regression in current pipeline (2026-07-30)

**What.** The additive `d_Direct` positive control is weak on the current pipeline across readouts (cloze +0.096, forced_choice +0.029, label-flip max 0.27 at α=4), NOT the standing CAUSAL_CORE headline of **+0.971 (late)**.

**Investigation (user asked to check all options).**
- **Bench is identical** to CAUSAL_CORE's: on-disk `pair_carrot_bomb.json` is byte-identical to the git-committed version and `_meta.generated_at = 2026-07-29T21:44` (the Jul-30 mtime was a git touch, not a rewrite — this also corrects B1's "bench rewrite" hypothesis: the *original* smoke floor was old-reps/new-code incompatibility, fixed by rebuilding reps).
- **My pipeline reproduces the on-disk artifact.** The CAUSAL_CORE analysis that actually backs an install curve, `outputs/pair_causal_analysis_one_word_693571.json` (metric p_concept, one_word, codeword_last), reports `add_d_Direct max_effect = 0.0278` — **matching my +0.03**. No on-disk `pair_causal_analysis*.json` has `add_d_Direct > 0.4`.
- **Metric reconciliation fails too:** label-flip (p_concept>p_codeword) install caps at **0.267** (α=4, L4), not 0.97.

**Conclusion.** There is **no computational regression** in the current code — it faithfully reproduces the committed bench and the on-disk CAUSAL_CORE artifact (+0.028). The documented **+0.971 appears unbacked on disk** (deleted run, or a doc-vs-metric mislabel), consistent with the doc-vs-artifact drift class MERGED_MASTER_PLAN already flagged for CAUSAL_CORE. Flagged for Omer.

**Impact on the NEW sprint (positive).** The Stage 2/3 conclusions do NOT depend on d_Direct's magnitude (their validity controls are exact self-transplant faithfulness + a strong DE_context +0.35). This finding *strengthens* the story: on the reproducible pipeline, **no local codeword intervention — full-state transplant OR additive d_Direct — installs the concept in a neutral context; only the surrounding context does.** The positive control for "the machinery can produce concept reading" is DE_context itself (+0.35), not d_Direct. Updated STAGE2 findings accordingly.

---

## B5 — Concurrent-run race in ds_rebuild_transplant.slurm dir capture (2026-07-30)

**What.** Ran S5 generalization as 3 concurrent jobs (grenade/pistol/chlorine, 694882/3/4) sharing `outputs/`. The script captured intermediate dirs with `ls -dt outputs/pair_X_* | head -1` (newest across ALL jobs), so jobs cross-wired each other's reps/dir/rundir (694883 used 694882's reps + 694884's rundir). All 3 results INVALID.

**Root cause.** `ls -dt | head -1` is not job-isolated; the dirs are named with `_${SLURM_JOB_ID}` but the glob didn't filter on it.

**Fix.** Added `TAG="${SLURM_JOB_ID:-}"` and filtered every capture: `ls -dt outputs/pair_X_*${TAG} | head -1`. Concurrent runs are now isolated. Re-ran the 3 pairs. (Same racy pattern exists in ds_kv_mediation/ds_additive_control/ds_stage4_toctou but those were only ever run one-at-a-time; fix before any concurrent use.)

**Lesson.** Single-pair bomb results (694691, run alone) are UNAFFECTED. Only the concurrent S5 batch was hit.

## 2026-08-08 — Gate-7 (§14-18) pre-registration deviation (user-approved)
The frozen manifest `configs/manifests/phase9_gcg_mac_matrix.json` runs the decisive refusal arm (arm07) at
**L22 with an UN-validated `refusal_alllayers` vector on the v1 (leaky) GCG split**. P7 validation (postdating
the freeze) shows L22 validates in only one direction family; the plan §15 mandates anchoring on validated
L16/L18 (never L9), and §0.5 mandates v3 for confirmatory claims. This is a genuine conflict between the frozen
pre-registration and the plan's later mandatory rules.
**Decision (user, 2026-08-08): run BOTH directions.** (a) frozen arm07 at L22 with the unvalidated vector
(honors the original pre-reg), AND (b) corrected arm07 at **validated L18** (`refval_clearharm_20260806_051728_721957/
refusal_direction_clearharm_L18.pt`). This converts the deviation into a measured comparison: does the
layer/validation choice change the Gate-7 conclusion?
**Split caveat:** no v3 GCG manifest exists (`data/gcg/clearharm_llama` is v1 only); building one is out of
first-cut scope. Both direction arms therefore run on the SAME v1 `clearharm_llama_doublespeak.jsonl`, so the
comparison is purely the L18-vs-L22 direction axis (split held at v1). v3-GCG is logged as a future build.
Scale (user): MINIMAL first-cut only (~6-8 GPU-h) to prove the pipeline before any full matrix.
