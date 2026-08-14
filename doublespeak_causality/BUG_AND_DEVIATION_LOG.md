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

---

# BACKFILL 2026-08-14 — Asymmetry / Section 20 sprint (2026-08-08 → 08-14)

The log stopped being maintained after the 2026-08-08 Gate-7 entry while the
Asymmetry (Part F) and Section 20 (Part G) sprint ran. This block backfills the
load-bearing bugs, deviations, and self-corrections of that window, reconstructed
from immutable docs. Each entry cites its source; none was fabricated. Ordered by
severity within theme, not by date. Governance report:
`reports/GOVERNANCE_REPAIR_2026_08_14.md`. Also see `RESEARCH_LOG_AUDIT_2026-08-14.md`
(independent recompute audit, findings A1–A17 / B1–B15) and the Role-Probe sprint
plan §2A / Appendix A (upstream-code review findings that become our own regression
tests).

## B6 — GCG candidate-selection bug (P9.0): objective in gradient only, never in selection
**Date:** discovered/fixed ~2026-08-05/06 (fix commits `84bf7a1e`, `76acb44a`).
The mechanism/refusal objective term entered the GCG *gradient* but was never
included in *candidate selection*, so it never influenced which suffix was kept
at each step. **Every pre-fix "mechanism-derived GCG is net-negative" statement
was made with the objective disabled in selection** and is non-citable.
**Source:** RESEARCH_LOG_SPRINT_2026-08-02_TO_08-14.md §8.7 (:306-312), §21 item 9;
RESEARCH_LOG_AUDIT_2026-08-14.md B11 (:138); CONTINUATION_PROGRESS.md:193.
**Affects:** all pre-fix Gate-7 / attack-objective negatives. **First-class
regression test for the new sprint** (plan §13.2): any new mechanism objective must
be verified to influence *both* gradient proposal and candidate selection.

## B7 — v1 split has ~90% train/test leakage
**Date:** found 2026-08-09→11 (`reports/P1B_V3_SPLIT.md`).
The v1 ClearHarm doublespeak split hashed per-instruction, so 77/86 rows,
14/43 concepts, and 17/21 codewords straddle train/test. The frozen 16-arm GCG
matrix was specced on v1. Superseded by v3 (`clearharm_doublespeak_v3.json`,
leakage-0: 0 straddling concepts/codewords/clusters across all split pairs).
**Source:** RESEARCH_LOG_SPRINT §Part E (:431-435); reports/P1B_V3_SPLIT.md.
**Affects:** every v1-split GCG/Gate-7 number, including the 2026-08-08 Gate-7
entry above (ran on v1). **New sprint uses v3 or a freshly constructed holdout
only** (plan §3.5, D4).

## B8 — Refusal-direction layer off-by-one (hidden_states[L+1] vs [L])
**Date:** 2026-08-09→11.
Direction builders store `hidden_states[L+1]` but label it L, while
`gcg_optimizer.py:173` read `hidden_states[layer]` directly — a one-block shift
between where a refusal direction was fitted and where the GCG objective read it.
**Source:** RESEARCH_LOG_SPRINT (:436-438).
**Affects:** any GCG arm optimized toward a refusal direction before the fix.
Confirms the hidden-state indexing convention now frozen for the new sprint:
`hidden_states[L+1]` == post-block-L residual == LayerPatch/directions row L
(ds_common.py:869/972, build_refusal_direction_llama.py:19). **Regression test**
(plan §3.9, App. §A3).

## B9 — GCG DEFECT D1: objective used one absolute token index from train_tasks[0]
**Date:** 2026-08-11 (`ASYMMETRY_SPRINT_EXECUTION_LOG.md` Phase 0, :54-80).
`gcg_optimizer.py:680-687` computed `refusal_dir_positions` once from
`train_tasks[0]` and applied it as an absolute token index for every task
(gradients :812, selection :433/:440). Prompt lengths vary across the 40-item
pool, so the objective read the wrong position for most tasks. This is the
project's recurring **absolute-position-index bug class** (now hit ≥3×).
**Source:** ASYMMETRY_SPRINT_EXECUTION_LOG.md:54-80; ASYMMETRY_FINAL_SYNTHESIS.md:49.
**Affects:** the published Gate-E / token-objective negative (refusal-vs-random
stays apples-to-apples; both arms misaligned identically). **First-class
regression test** (plan §3.9, App. §A9.2 — the same class threatens Gate 1).

## B10 — GCG DEFECT D2: fit-position vs use-position mismatch
**Date:** 2026-08-11 (ASYMMETRY_SPRINT_EXECUTION_LOG.md:82-99).
Even for task 0 the objective read the last suffix token (index 233, inside the
user turn) while the refusal direction was fitted and validated at the last token
after the assistant header (index 238) — a five-token template offset.
**Source:** ASYMMETRY_SPRINT_EXECUTION_LOG.md:82-99. **Affects:** same as B9;
constrains how §7.5 per-prompt arms compare to legacy universal arms.

## B11 — DEFECT D3: intervention-scope asymmetry (scope-matched arm NOT RUN) — OPEN
**Date:** identified 2026-08-11; **still not run as of 2026-08-14.**
The activation-space causal result ablates the direction at all positions, all
decode steps, and (multilayer) all layers, while the token/soft-prompt objective
touches 16 input positions at one layer. The "activation-space causal but
token-space unoptimizable" hierarchy is therefore **not budget-matched.**
**Source:** ASYMMETRY_SPRINT_EXECUTION_LOG.md:100-108; RESEARCH_LOG_AUDIT B5.
**Affects:** the §17 "activation > continuous > discrete" hierarchy.
**This is Phase 6 / D3 of the new sprint (plan §10) — the reviewer-critical gap.**

## B12 — Gate D continuous dose (budget_rel=0.10) selected on the test split
**Date:** 2026-08-11 run; flagged through 08-14.
The headline continuous ASR (0.784 vs 0.153) uses budget 0.10, chosen by reading
the dose sweep **on test**. The response is inverted-U: at full budget the prompt
drives refusal projection −20.09 yet yields ASR 0.000, refusal_rate 0.000 — "the
model is neither refusing nor complying." Methodological lesson: **probe
displacement is not evidence of mechanism control.**
**Source:** RESEARCH_LOG_SPRINT §17 (:600-624); CONTINUOUS_VS_DISCRETE.md §5/§7;
RESEARCH_LOG_AUDIT B4. **Affects:** Gate D "POSITIVE" → must be labelled
EXPLORATORY. **New sprint re-confirms this dose on an untouched split (plan §10.2)
and carries the lesson into Phase 4 (a manipulation check ≠ a behavioral effect).**

## B13 — StrongREJECT threshold conflict (0.25 vs 0.5) — RESOLVED for new work
**Date:** identified 2026-08-12; contract frozen for the new sprint 2026-08-14.
`scripts/behav_judge.py:85` sets `MAL_THRESHOLD = 0.25` (what actually ran for the
legacy behavioral harness and the numbered scripts 14/17/18/40 and `phase_behav_*`),
while every paper-facing doc and the newer asym scripts (`asym_p2_judge.py`,
`asym_p201_judge_softprompt.py`, `26_eval_p9_gcg_heldout_asr.py`) use ≥ 0.5 and
persist the continuous score.
**Resolution (new sprint, plan §3.6):** freeze **binary malicious = score ≥ 0.5**
for all new work via the 0.5 judge path; **do NOT flip `behav_judge.py`'s constant**
— `scripts/validate_experiment_coverage.py` guards `(score≥MAL_THRESHOLD)==(label==MALICIOUS)`
and would fire on every historical run. Continuous scores are persisted, so a
0.25/0.5/continuous sensitivity table for historical claims is rebuildable offline
with no GPU. **Source:** ASYMMETRY_FINAL_SYNTHESIS.md:62,99-101; RESEARCH_LOG_AUDIT A8.
**Affects:** potentially every ASR/ΔASR number in the prior sprint.

## B14 — Gate-7 v3 matrix raw run-dirs missing (20/20); Gate-E / λ=10 dirs pruned
**Date:** discovered 2026-08-14.
All 20 per-seed run dirs named in `reports/GATE7_V3_MATRIX_STATS.json` are absent
from `outputs/`; the heldout-ASR dirs for the position-corrected Gate-E result
(+0.009) and the λ=10 probe (+0.622/−0.162/+0.189) were also pruned. Those numbers
survive only via committed summary `.md`/`.json`, not raw-reproducibly.
**Source:** RESEARCH_LOG_AUDIT A10 (:60-61), §18/§22. **Affects:** §13 fair GCG
matrix / Gate-7 negative and Gate-E negative are **summary-backed only**. Marks
them REPORT-ONLY in the claim audit; the immutability rule (plan §3.7) exists to
stop this recurring.

## B15 — Judge-flip rate superseded twice (5.4% → 3.4% → 0.62%/1.65%)
**Date:** 2026-08-14.
The judge noise floor was quoted as 5.4% (n=37), then ~3.4% (an n≈148 hand-count,
report-only), then measured via an M=5 band-only replicate design:
`asym_p203_judge_replicates.json` gives 35.48% flips *inside the contested band*
but 1.65% corpus-wide. The ±0.03–0.08 floor used to retire effects derived from
the retired 3.4% figure. **Source:** SECTION20_RESULTS.md §4; RESEARCH_LOG_AUDIT
staleness item 4. **Affects:** every effect retired "below the judge floor."

## B16 — Phi-4 cross-family claim is missing its concept half
**Date:** drop decided 2026-08-12; flagged 2026-08-14.
§14 claims the representation≠behavior dissociation replicates on Phi-4, but
`THIRD_FAMILY_REPLICATION.md` contains only X2 geometry, X3 refusal-ablation, X5
AUC — **no Phi concept-ablation arm with a count-matched random control.** The
refusal half replicated; the concept half was never tested.
**Source:** RESEARCH_LOG_AUDIT B13; THIRD_FAMILY_REPLICATION.md. **Affects:** §14.
**This is Phase 7 of the new sprint (plan §11).**

## B17 — L18 refusal direction fitted on a different distribution than applied to
**Date:** disclosed 2026-08-14.
The L18 refusal axis used throughout Parts F/G was fitted on `pair_carrot_bomb.json`
(n_harmful 60 / n_harmless 20, separation 0.9525) and applied to ClearHarm — a
cross-distribution transfer never previously flagged. Its bidirectional validation
(`ablate_gain +0.4667, induce_gain +0.6667, score 1.1333`) qualifies the word
"validated." **Source:** RESEARCH_LOG_AUDIT B6; UPDATED_PAPER_CLAIM_TABLE.md:51;
outputs/stage_gcg_full/refusal_direction_llama_L18.json. **Affects:** essentially
every refusal-direction number in Parts F/G. New sprint freezes and re-uses this
exact validated direction (plan §6.1) and records the fit cohort explicitly.

## B18 — Governance artifacts lapsed 2026-08-08 → 08-14 (this backfill)
**Date:** lapse 2026-08-08→14; repaired 2026-08-14.
`EXPERIMENT_REGISTRY.csv` last updated 2026-08-05 (395 rows vs 545 output dirs;
1 asym match against 65 asym dirs); `BUG_AND_DEVIATION_LOG.md` last entry
2026-08-08. The entire Asymmetry (Part F) and Section 20 (Part G) work was
unregistered and its deviations unlogged, while the sprint log advertised heavy
provenance discipline. **Repair:** `scripts/update_registry.py --apply` added 178
rows (395→573; asym 1→47, idempotent re-run = 0 to add) from immutable RUNMETA.json;
this backfill block (B6–B18); `reports/GOVERNANCE_REPAIR_2026_08_14.md`.
**Source:** RESEARCH_LOG_AUDIT B14 (:150-153). **Affects:** provenance claims in the
prior sprint log §3/§6 — now repaired.

## V1 (deviation) — code review deliverable folded into the plan as Appendix A
**Date:** 2026-08-14.
Plan §2A.2 names the upstream code-review deliverable
`docs/ROLE_CONFUSION_CODE_REVIEW.md`; per user request for a single tracking file
it was folded into `docs/ROLE_PROBE_NEXT_SPRINT_PLAN.md` as Appendix A and the
separate file deleted. Documentation location only; no scientific effect.

## B19 — v3 corpus `codeword_occurrences_templated` spans are stale vs the stored `*_prompt`
**Date:** found 2026-08-14 (role-probe sprint, launching the generated-cohort replication).
The corpus per-example `codeword_occurrences_templated` spans (and `n_codeword_occurrences_templated`)
were computed on a DIFFERENT rendering than the stored `doublespeak_prompt` field: occurrence
counts differ for ~65% of clearharm (26/40) and ~50% of generated (20/40) examples (e.g.
generated_0173: stored prompt 9 codeword tokens, corpus says 13; corpus query-last 213 vs the
stored-prompt query-last 182). The stored `doublespeak_prompt` is the REAL attack — the behavioural
harness generates `ds_base_score` from it, and the Bombness extraction reads from it.
**Impact: NONE on results.** Extraction is correct by construction: `pair_common.capture_components`
locates the codeword via `resolve_positions` on the actual (templated stored) prompt, so it reads at
the true query-codeword position regardless of the stale spans. Gate 1's clean result (holdout AUC
0.997, token-identity control exactly 0.500, cross-codeword generalization) confirms the positions
were correct. The corpus-span anchor was only an external cross-check.
**Fix:** `preflight_positions` downgraded — HARD check that the codeword resolves to a real
prompt-body position (0 <= codeword_last < final_prompt), and the corpus-span match becomes a SOFT
reported rate (warn if <0.5, never abort). The B9 absolute-position bug class is structurally
impossible here anyway (positions are resolved per example, never reused). Regression test
`test_generated_cohort_resolves` locks that the generated cohort now passes. This UNBLOCKS the
generated-cohort replication; the clearharm Gates 1-4 are unaffected.
