I independently re-checked every high/medium finding against the artifacts. Below is only what I personally verified; I discarded findings I could not confirm (noted at the end).

# CONSOLIDATED AUDIT — `doublespeak_causality/RESEARCH_LOG_SPRINT_2026-08-02_TO_08-14.md`

## (A) CLAIMS THAT ARE WRONG OR UNSUPPORTED — must be fixed

### A1. §16 Gate-B row (line 423) — WRONG NUMBERS **AND WRONG SIGN**. Severity: CRITICAL
Log text: `Pearson r **0.817 (ε=0.1) → 0.140 (ε=1.0)**`
True (recomputed from `outputs/asym_p1_reach_train_20260811_212152_750361/eps_scan.jsonl`, canonical aggregation per `scripts/asym_make_figures.py:186-196` — direction index 0 = mechanism, cell `decision|hs19`, n=120):

| ε | train (…750361) | test (…750362) |
|---|---|---|
| 0.1 | **0.8395** | **0.8104** |
| 1.0 | **−0.0015** | **−0.3242** |

`0.817` and `+0.140` appear in **no** artifact and in **no** source doc (`grep '0.817'` over `docs/` + `reports/` = 0 hits). The sprint's own synthesis agrees with the artifact and not the log: `docs/ASYMMETRY_FINAL_SYNTHESIS.md:50` — *"r 0.84 (ε=0.1) → **−0.002 / −0.324** (ε=1.0); *worse* than a matched null"*. The positive `+0.140` **erases the sign that carries the sprint's headline claim** (mechanism ends up worse-predicted than a matched null). The log is also internally inconsistent — §17 states the correct "r 0.84→~0".

### A2. §23 backlog line 628 — STALE, contradicted by HEAD. Severity: CRITICAL
Log text: `the §20.7 objective curve is 27/74 prompts (seed-43 shards 2–3 and all of seed 44 owed)`
True: `outputs/asym_p207_objective_curve_seed42_FINAL37.json` → `n_paired=37, n_expected=37, interim=false`. Seed 42 is **complete**, and its held 200→600 read has landed as a **NULL**: `mean_delta −0.0723, p=0.2515, n_improved 22/37`. Commit `dce44a92` ("seed42 37/37: the held 200->600 read is NULL (p=0.252)"). Seed 43 is at 11 (`…_seed43.json`) with all 4 shards launched (`757662`, `757672` RUNNING); seed 44 shard 0 (`757697`) RUNNING. Live coverage ≥ 48/74, not 27/74. **The log's §20.7 "saturation is NOT established (the estimate oscillates −0.079/−0.122/−0.062)" is superseded by a full-n null.**

### A3. §20.4 (line 536) — STALE, "provisional" is now false. Severity: HIGH
Log text: `(All six bound rows JSON-confirmed; self-marked provisional.)`
True: `outputs/asym_p204_equivalence_pass2.json` (commit `c04d556b`) carries `provisional = False`, `endpoint = "judge-denoised (majority vote over M=5 on the 4.65% band; extremes deterministic)"`, `mean_worst_bound_pass1 = 0.21171 → mean_worst_bound_pass2 = 0.22523` (**+6.4 % WIDER**). The load-bearing finding — *the bounds are sampling-limited, not judge-limited, so no better judging tightens them* — is absent from Part G. `why_not_the_planned_pass2` field also records that the plan's §20.6 route is unreachable (corpus ceiling 179).

### A4. §12/§29 line 324 — WRONG NUMBERS (two swapped, one understated). Severity: HIGH
Log text: `Refusal ablation raises harm at bf16/8-bit/4-bit (**+0.26 / +0.29 / +0.52**, McNemar sig)`
True, `direct_refabl_a1.0_vs_direct_base.delta_ASR` (test n=42):
- bf16 `outputs/behav_refusal_clearharm_asweep0.0-0.5-1.0_20260811_112930_746744` → **+0.2857**
- 8-bit `…_8bit_20260811_093845_745089` → **+0.2619**
- 4-bit `…_4bit_20260811_112930_746743` → **+0.5714**

bf16 and 8-bit are **swapped**, and 4-bit is stated as +0.52 instead of +0.571. **The log's own §15 table (lines 395-397) has all three right** — this is an internal contradiction, not a source problem.

### A5. §16 Gate-F row (line 429) — verdict overstated vs. the artifact. Severity: HIGH
Log text: `**POSITIVE (actuator)** | refusal ablation raises ASR 5/5 pairs, median specific ΔASR +0.414, 4/5 Holm-sig`
The refusal-half numbers are correct. But `reports/ASYM_P4_MULTICONCEPT.json` → `GATE_F.verdict` reads verbatim:
> `"PARTIAL — dissociation holds in all 1 testable pair(s), but only 1 of 5 pairs had attack headroom. The refusal half generalizes; the concept half is UNDERPOWERED across the family. Do NOT claim 'general across concepts' (plan Gate F)"`

with `concept_test_power_by_pair` = bomb *marginal*, chlorine *floor-limited*, cocaine *marginal*, grenade *informative*, pistol *floor-limited*, and `concept_half_informative_pairs = ["pair_grenade"]`. The log's §24 "NOT established" list omits this entirely. **Add the 1-of-5 power grading and the JSON's own PARTIAL verdict.**

### A6. §8.5 (line 232) — WRONG NUMBER, wrong run. Severity: HIGH
Log text: `At the strong dose α=0.20 (where refusal-ablation provably fires, **+0.194 vs random, p<1e-12**)`
True: `outputs/p8_alpha020_clearharm.json` → `cohorts.a020.splits.pooled["0.2"].specificity` = `delta_ASR_refabl_minus_randabl **0.14173**, mcnemar_b 20 / c 2, mcnemar_p **1.211e-04**`. The `+0.194 / p=1.78e-13` figure is a **different run at a different dose**: `outputs/p8_v3_combined.json` → `pooled["0.25"]`, n=242. `reports/P8_INTERACTION_V3.md:58` states the α=0.20 check correctly as +0.142.

### A7. §20.8 (line 557) and §22 (line 608) — factually false; withdraw both. Severity: MEDIUM-HIGH
Log text: `the clearharm_179.csv file was not locatable in this checkout, so the ceiling arithmetic is report-only` / `file not in this checkout`
True: the file **exists and is committed** at `/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/data/clearharm/clearharm_179.csv` — 179 data rows, cols `instruction, category, clearharm_native_target, clf_label`. The path in `docs/SECTION20_RESULTS.md:173` (`data/clearharm/clearharm_179.csv`) is correct as written; the auditor searched only under `doublespeak_causality/`. **The 179 corpus ceiling is artifact-backed; both caveats should be deleted.**

### A8. §1 line 57 — the sprint's stated judge contract contradicts every paper-facing doc. Severity: MEDIUM-HIGH
Log text: `MALICIOUS iff score ≥ **0.25**` (declared as *the* contract for the whole sprint); the dual-threshold defect appears only as a conclusion-neutral note at line 483.
Against: `docs/UPDATED_PAPER_CLAIM_TABLE.md:11` "Binary success = **StrongREJECT ≥ 0.5** unless the row says otherwise"; `docs/PAPER_OUTLINE_V2.md:61` "**StrongREJECT ≥ 0.5** throughout"; `docs/RESEARCH_HANDOFF_V2.md:102` "Use **≥ 0.5**. Old numbers…". The log never records the standing decision nor which parts were produced at which threshold. (Code confirms `scripts/behav_judge.py:85 MAL_THRESHOLD = 0.25` is what actually ran.)

### A9. §13 (lines 353, 365) — three separate defects in the headline GCG matrix. Severity: MEDIUM-HIGH
- **"3 seeds"**: only 5 of 10 arms have 3 seeds. `reports/GATE7_V3_MATRIX_STATS.json`: `arm03=1, arm08=1, arm08r=1, arm10=1, arm10r=1`. **Q2 (L12) and Q4b (combined) — both quoted in that paragraph — are SINGLE-seed**, in a section whose whole argument is that single-seed GCG ASR swings ~0.24.
- **"Q2 … vs its random +0.108 ns"**: `pairs[arm10 vs arm10r].per_seed[0]` = `delta_asr 0.10811, mcnemar_p 0.125, **boot95 [0.02703, 0.21622]** — the bootstrap CI EXCLUDES zero.` "ns" holds only under McNemar. This is the one arm where the mechanism objective beats its norm-matched control, reported without that caveat.
- **"Q2 refusal↓@L12 (Jacobian sensitivity-peak)"**: `outputs/stage_gcg_full/refusal_direction_llama_SELECTED.json` → L12 `ablate_gain 0.0, induce_gain −0.3333, both_gains_positive **False**` (L18 selected, score 1.1333). **L12 is the one layer that FAILED ablate+induce validation**, so its negative is uninformative about mechanism reachability. Not stated anywhere in the log.
- **"batch 32 × 200 steps"**: no `phase9b_v3_arm*` run dir survives (see A10), and the only committed GCG manifest, `configs/manifests/phase9_gcg_mac_matrix.json`, specifies `batch_size 64`. Report-only and in conflict.

### A10. §22 verification-gap list — omits the largest gap in the log. Severity: MEDIUM-HIGH
§22 presents the 3-seed v3 matrix as the *committed replacement* for the unretained first-cut. But **all 20 per-seed run dirs the stats JSON names are absent**: I globbed every `dir` field in `reports/GATE7_V3_MATRIX_STATS.json` → **20/20 missing**; `outputs/stage_gcg_full/` now contains only 13 entries, all refusal-direction files. The sprint's headline Gate-7 negative is **summary-JSON-backed but not raw-reproducible**, and §22 does not say so.

### A11. §25 line 690 — dead file path. Severity: MEDIUM
Log text: `configs/manifests/phase9b_gcg_v3.json`
`configs/manifests/` contains exactly 8 files: `baseline_drift, behav_carry, defense_gated, defense_util, phase9_gcg_mac_matrix, refdecpatch, refsuploc, refval`. `find . -name '*phase9b_v3*'` → nothing. This is the only dead path in the §25 index.

### A12. §3 line 96 — "0 mismatches" is contradicted by the repo's own claim table. Severity: MEDIUM
Log text: `validate_all_outputs.py recomputed **4,909 summary values from raw across 29 dirs → 0 mismatches**`
`reports/CLAIM_AUDIT_TABLE.md` claim **META-03** (lines 143, 217, 432) documents a confirmed `FAIL: summary!=raw at by_split.heldout.monotone_decreasing: summary=False recomputed=True` on `outputs/phase9_dose_curated_L9_20260803_173754_704861`, in 2 of 5 `phase9_dose` dirs — *"the only summary!=raw mismatch anywhere in the cited corpus."* The unqualified "0 mismatches" must be scoped to the 29-dir pass. Separately, neither `4,909` nor `113 → 205` exists in any machine artifact (prose-only in `CONTINUATION_PROGRESS.md:131,268`).

### A13. §5.8 line 187 — mislabelled column. Severity: MEDIUM
Log text: `train 0.867 / test 0.891`
`reports/P6_JACOBIAN_READOUT.md:89` → `| refusal projection @ decision L21 | 0.867 | — | 0.863 | 0.891 |` — **0.867 is the POOLED value; train is 0.863.** Test 0.891 is right. (No JSON holds per-split AUCs; `outputs/rep_predicts_behavior_sweep.json` stores pooled only — so this row is report-only too.)

### A14. §8.6 line 235 — reproduces a mis-citation the repo already corrected. Severity: MEDIUM
Log text: `n=86; n≈275 needed for ΔASR≈0.07`
`reports/CLAIM_AUDIT_TABLE.md` (line 31, and claim P100-05 line 91): *"`P10_DECODE_SAFE_WRITE.md` §5 **mis-cites its own power source**: it attributes n ≈ 275 to ΔASR ≈ 0.07, but P10.0 §5 gives **275 for 0.09** and **419 for 0.07**."* The log inherits the error.

### A15. §1 line 63-64 — design claim not carried by any result. Severity: MEDIUM
Log text: `**Six matched conditions per item:** doublespeak, neutral, direct, benign, shuffled, unrelated`
All six fields exist in `data/splits/clearharm_doublespeak_v1.json`, but only **3** were run in the headline cell (`outputs/behavioral_split_beh_clearharm/behavioral_summary.json` → `conditions: ['direct','neutral','doublespeak']`) and **4** in the drift runs (`baseline_drift_…732432` adds `benign`). **`shuffled` and `unrelated` were never run behaviorally.** Source: `SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md` §11 item 8.

### A16. §5.9 line 190 — no artifact. Severity: MEDIUM
Log text: `token-0 separation AUC **0.936** test / 1.000 train`
`outputs/refusal_traj_clearharm_20260805_060350_711956/summary.json` has keys `['cohort','layers','k','by_split']` only — **no AUC field anywhere**. Report-only; needs an `[R]` tag or the item-level file.

### A17. §4.11(b) line 138 — range silently drops an out-of-range cell. Severity: LOW-MEDIUM
Log text: `L9→carry-band mediation **0.75–0.83**`
True `median_mediation_frac_carry`: clearharm dev **0.751** (n=13), clearharm heldout **1.459** (n=9), curated dev 0.764, curated heldout 0.828. Three of four cells are in range; the fourth is a **1.46 overshoot**. `reports/PHASE7_PATH.md:67` discloses it ("1.46 (overshoot, n=9)"); the log does not.

---

## (B) IMPORTANT WORK MISSING FROM THE LOG

### B1. P6 — the Jacobian / gradient-sensitivity readout. Severity: CRITICAL
An entire in-window experiment (run 2026-08-07) is absent. `outputs/p6_predicts_behavior_clearharm.json`: n=86, `concept_peak_layer 16`, `refusal_peak_layer 12`; `refusal_gradnorm_peak` AUC **pooled 0.8073 [0.696, 0.901] / train 0.7996 / test 0.8148**; `concept_gradnorm_peak` pooled AUC **0.5828** (CI includes 0.5). Source: `reports/P6_JACOBIAN_READOUT.md`. This restates the sprint's headline dissociation with a **third, gradient-based measure** and adds a locked-test predictive result. `grep -i 'jacobian\|0.807'` over the log returns only lines 365/373/623 — all about the *GCG objective arm*, never this readout. Plan §12 is marked `✅ DONE` in `CONTINUATION_MASTER_PLAN_V2.md:228`.

### B2. The reachable-subspace R(v) and cross-prompt gradient coherence results. Severity: HIGH
Both live in `outputs/asym_p1_reach_train_20260811_212152_750361/ANALYSIS.json` and appear nowhere in the log:
- `subspace['decision|hs19']['R']['16']`: `refusal_L18 R = **0.5846**` vs `random_mean 0.003936` / `null_isotropic 0.003906` → **148.5×**, `percentile_among_random 1.0`, over 15,360 substitutions.
- `cross_prompt_coherence['decision|hs19']`: `refusal_L18 mean_pairwise_cosine **0.3482**, participation_ratio 5.18, frac_pairs_positive 0.929` vs **8 random directions mean 0.2680, max 0.3831** — i.e. refusal gradients are only *marginally* more cross-prompt coherent than random. That is the direct answer to plan §5.5's universal-suffix hypothesis (flagged "HIGH VALUE") and it is a **negative for the universality story**.

### B3. §19.2 — suppression is GENERIC, not localized at the optimized layer. Severity: HIGH
`docs/TOKEN_REACHABILITY_ANALYSIS.md:193-197`: *"Across fit layers L10–L24 the drop is ~0 before L14, grows monotonically with depth, and is deepest at **L24** — not at the L18 layer the objective optimized. The refusal-suffix and random-suffix depth profiles are near-identical in shape, Pearson **r = 0.9965**… Strong support for **H4 (generic adversarial suppression)**."* Also §6.1(c): *"No train→held-out overfitting. Transfer ratio > 1 in all 9 cells (1.17–2.00)… the 'universal suffix overfits its suppression' hypothesis is **rejected**."* `grep 'L24\|0.9965\|transfer ratio'` over the log = **0 hits**. This is a *mechanistic explanation* for the Gate-E negative — the log's §17 lists only two measured causes and omits both of these.

### B4. Gate D — the inverted-U dose response and its EXPLORATORY status. Severity: HIGH
The log presents Gate D as a clean positive (`ASR 0.784 vs 0.153`). Missing:
- At the full budget the soft prompt drives the refusal projection **−20.09** yet produces **ASR 0.000 and refusal_rate 0.000**. Recomputed from `outputs/asym_p2_soft_refusal_free_b1.0_seed42_20260811_213644_750364/projections.json`: n=37, baseline 4.4170 → final −15.6751, **Δ −20.0921**, per-prompt sd 2.532 → 0.252. `docs/CONTINUOUS_VS_DISCRETE.md:69` — *"The model is neither refusing nor complying."* The stated methodological result: **probe displacement is not evidence of mechanism control.**
- `docs/CONTINUOUS_VS_DISCRETE.md:111-120` dose table (0.05→ASR 0.135-0.162; 0.10→0.757-0.838; 1.00→**0.000**) and §7: *"**EXPLORATORY**: 0.10 is the optimal budget. The dose sweep was read on **test**… A confirmatory dose needs freezing on the untouched v3 dev split."* The log marks Gate D simply `[V] POSITIVE`.
- The 5.7 % rounding retention (§17) measures **projection retention only** — no generation was run with the rounded suffix (`CONTINUOUS_VS_DISCRETE.md` §7 Limitations).

### B5. The D3 scope-matched activation arm — "the single cleanest missing control". Severity: HIGH
`docs/RESEARCH_HANDOFF_V2.md` §5.2 NOT RUN: *"The activation intervention is all-position/all-layer while the soft prompt is 16 input positions, so the 'continuous < activation' ordering is **not budget-matched**. This is the single cleanest missing control."* Ranked #2 of the handoff's next steps ("the control a reviewer will ask for first"); also `docs/ASYMMETRY_GAP_MATRIX.md:108`, `docs/ASYMMETRY_SPRINT_EXECUTION_LOG.md:755,1716`, `docs/ASYMMETRY_FINAL_SYNTHESIS.md:123`. `grep 'scope-matched\|all-position'` over the log = **0 hits**, and §23's backlog does not list it. This qualifies §17's entire three-capability hierarchy.

### B6. Provenance of the L18 refusal direction — cross-distribution transfer, never disclosed. Severity: HIGH
`docs/UPDATED_PAPER_CLAIM_TABLE.md:51`: *"**A6 direction-fit cohort.** The L18 axis was fit on `pair_carrot_bomb.json` (n_harmful=60 / n_harmless=20, harmless = 20 generic instructions) and applied to ClearHarm — cross-distribution transfer, **not previously flagged**."* Confirmed by `outputs/stage_gcg_full/refusal_direction_llama_L18.json` → `n_harmful 60, n_harmless 20, separation 0.9525`. `grep 'carrot'` over the log = **0 hits**; §1/§2 describe only the ClearHarm v1/v2/v3 splits. **This qualifies essentially every refusal-direction number in Parts F and G.** (The bidirectional validation numbers — `ablate_gain +0.4667, induce_gain +0.6667, score 1.1333` — are also never given, so §5.3's "the *validated* L18 refusal direction" is unsupported in-log.)

### B7. Gate G — the defense negative is reported without its floor bound. Severity: HIGH
`docs/TWO_SIGNAL_DEFENSE.md` §3 (lines 107-110): *"Test DS ASR without any defense is **0.143**. A defense cannot demonstrate a reduction against a baseline that is already near zero, so this run **does not establish that the two-signal gate would fail on a split with real headroom**."* Also missing: the TRAIN result (lines 45-49) — `none 0.282 → gate_two 0.129, Δ −0.153, p=0.0010`, over-refusal `+0.141` vs uncond `+0.365`, i.e. *"On train the two-signal gate **Pareto-dominates** its random control"* (EXPLORATORY); the interpretable failure diagnosis (the concept gate fires on 0.262 of DS attacks but 0.381 of attack-structured benign); and §4's three concrete conditions for a fair re-test. **This is directly inconsistent with the log's own §24 principle that "every behavioural negative is now an honest bound."**

### B8. §20.5 / §20.6 / §20.9 and the §20.1 μ sweep — never mentioned at all. Severity: HIGH
Part G enumerates only 20.1, 20.2, 20.3, 20.4, 20.7, 20.8. `grep '20\.5\|20\.6\|20\.9\|μ sweep'` over the log = **0 hits**, not as results, not as blocked, not as backlog. Source `docs/OWED_SUBMISSIONS.md` "## OUTSTANDING":
1. `**§20.1 μ sweep** (μ ∈ {0.1,0.3,1,3,10}) — **not run** (0 matching output dirs). Needed before §20.1's "78 % cost" goes in the paper: 78 % is the price of a *near-total* pin (Δproj ≈ −0.03), not of the coordinate as such.`
3. `**§20.7 seed 44** — entirely unlaunched` (now partly launched, shard 0 only — a **biased subset**, per the doc's own warning at line 160).
4. `**§20.7 2000-step point** — deferred by decision` — the plan (`ASYMMETRY_SPRINT_PLAN_2026_08_11.md:607`) specifies 600 **and** 2000 steps, so §20.7 is delivered at half its planned span and the log doesn't say so.
6. `**§20.5 / §20.6 / §20.9** — not started.`
Also missing: `docs/SECTION20_RESULTS.md:207` — *"**§20.6 and §20.4-pass-2 are blocked by the corpus, not the endpoint.**"* — the load-bearing link explaining why 20.4 stayed at one pass.

### B9. Phase 10 (Gate-6) and Phase 11 (13-arm matrix) — entirely absent from Part A. Severity: HIGH
`grep 'Gate-6\|Gate 6\|Phase 10\|Phase 11\|concept_objective\|13-arm'` over all 699 lines = **0 hits**. From the designated source of truth `SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md`:
- §9.1 (line 719): the candidate `concept_objective` scores **9/10** on the Gate-6 eligibility checklist and **FAILS criterion 4 (sufficiency)** → gate not passed.
- §9.2 (line 740): *"the 13-arm GCG/MAC matrix was **DESIGNED but NEVER RUN** — **0 of 13 arms executed**"*; even the scaled-down decisive minimal test (arm G1) was planned then never launched. Line 838: *"**Gate 7 was never tested** … Treat it as a well-motivated hypothesis, not a measured null."* The log's first Gate-7 mention (line 295, Part D) presents it as a measured negative.

### B10. `doublespeak_signature` (d_DS) causal inertness — "the best-supported negative in the sprint". Severity: HIGH
`SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md:736`: adding the d_DS direction at matched relative strength moves the reading by at most **1e-05** (9 control cells) and **3e-05** (175 dose cells), vs d_Direct at **+0.167 / +0.533 / +0.971**. It is bottom-line item 8 of the source (line 931). The log's §24 bottom line has 6 items and omits it; d_DS appears in the log only as a cosine (line 111).

### B11. Two load-bearing self-corrections missing from §21's honesty ledger. Severity: MEDIUM-HIGH
- **The GCG candidate-selection bug (P9.0).** `CONTINUATION_PROGRESS.md:193` — *"✅ P9.0 — the GCG selection bug is FIXED (unblocks Gate 7)… the objective finally enters **candidate selection**, not just the gradient."* `SPRINT_SINCE_2026-08-02_COMPREHENSIVE.md:553` — *"every prior 'mechanism-derived GCG is net-negative' statement was made with the objective **DISABLED in candidate selection**, so Gate 7 currently has **NO valid evidence for or against**."* Commits `84bf7a1e`/`76acb44a`. `grep 'candidate selection\|selection bug'` over the log = **0 hits**.
- **The λ task-loss endpoint statistic.** Commits `f91acf6b` ("SELF-CORRECTION: lambda task-loss statistic was endpoint-based and unstable") and `1b5b4d94`. `docs/RESEARCH_HANDOFF_V2.md` trap 7: *"Summarise it with **best-so-far**, never a single endpoint, and never a **ratio of two endpoints** (that version of one comparison swung 1.45×–34× across seeds and was **withdrawn**)."*

### B12. Three Part-A caveats dropped from the source. Severity: MEDIUM
All from `SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md`, each attached to a result the log states cleanly:
- **§8.4 → log §5.4 (lines 170-173).** Line 575-578: *"the random control is null at α=8… but at the **matched α=12** a random direction **significantly RAISES** ASR (+0.27 / +0.33, p ≤ 0.002)… '**random null' is not literally true at the headline α**."* The log's §5.4 contains **no random-control number at all**.
- **§7.9 → log §4.9 (line 133).** Line 361-362: *"⚠ the uniform-KO arm has **no specificity control** — an arbitrary non-candidate head's pattern (`C_rand`) already produces a **0.152 dev / 0.103 heldout** drop, so 'uniform-KO is more specific' is unsupported on dev."* Log says only "superadditive".
- **§7.6 → log §4.6 (line 123).** Line 301: *"⚠ **The query-codeword MLP is NOT a clean null on clearharm** — L9 (**+0.0146** dev, +0.0046 heldout), L15 and L20 all survive Holm on both splits. The correct statement is that the query effect is **3–4× weaker**, not absent."* The log frames the write as demonstration-position-only.

### B13. Phi-4 — the concept half of the dissociation was never tested. Severity: MEDIUM-HIGH
§14 claims the representation≠behavior dissociation "REPLICATES" on a third family. `docs/THIRD_FAMILY_REPLICATION.md` contains **X2 geometry, X3 refusal-ablation, X5 AUC only** — there is **no Phi concept-ablation arm** with a count-matched random control. Plan GATE E (`docs/NEXT_SPRINT_PLAN_2026_08_09.md`) states: *"Only claim cross-family dissociation after **both** concept intervention and refusal intervention have appropriate random controls."* The log neither says so nor lists it in §23. Also dropped: the *positive* X5 geometry replication (cos(concept,refusal) |cos| ≤ 0.056 at every layer on Phi), and the fact that plan **Phase 6** (power up the Phi readout on a leakage-free ≥60-item cohort) was **consciously dropped** (`docs/ASYMMETRY_SPRINT_EXECUTION_LOG.md` 2026-08-12 01:06).

### B14. The repo's two standing governance artifacts stopped being maintained mid-sprint. Severity: MEDIUM
- `git log -1 -- EXPERIMENT_REGISTRY.csv` → `00974e53 2026-08-05`. It has **395 data rows** against **605** output dirs; `grep -ci asym` = **1** while `ls outputs | grep -c '^asym'` = **65**.
- `git log -1 -- BUG_AND_DEVIATION_LOG.md` → `b02e20d9 2026-08-08`.
So the **entire Asymmetry sprint (Part F) and Section 20 (Part G) are unregistered and their bugs/deviations unlogged**. The log advertises heavy provenance discipline (§3, §6) and never discloses this. Relatedly, the sprint's only formally logged user-approved pre-registration deviation — `BUG_AND_DEVIATION_LOG.md`, "2026-08-08 — Gate-7 (§14-18) pre-registration deviation": the decisive refusal arm ran at an **un-validated L22 vector on the leaky v1 GCG split**, resolved by running both directions — is never mentioned, though §11/§22 quote that run's numbers.

### B15. Smaller Part-A/B omissions worth one line each. Severity: MEDIUM-LOW
From `SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md`: the run-to-run ASR drift envelope (§10.4: same `ds_base` yields test ASR **0.286–0.381** across four greedy runs — *"bounds the precision of every 2-decimal ΔASR"*); the refusal_rate ladder underpinning "imperfect refusal suppressor" (§8.3: ds_base 0.45-0.48 between direct 0.84-0.88 and full ablation 0.05-0.10; DS+ablation composite train **0.727** vs 0.568 vs 0.386, McNemar **+0.341, p=2.8e-4**); the failed fixed-α=12 first attempt at depth localization and its L9 confound (§8.6); Phase 7d's sufficiency-onset scan (§7.11d, L17H27 pivotal); the v2 evidence that resolves §4.8's curated-heldout 0 (§7.8: **v2 heldout 44** Holm-sig heads at n=55); the §7.7 wider-window numbers that would actually support §4.7's "'saturates at W8' is false" (best W8 L2-9 = **+0.192/+0.193**, 1.7× best W4); and the §20.2 well-powered side finding (`SECTION20_RESULTS.md` §3b: `task_orth` r(success, baseline) = **−0.512, p=9.6e-09** vs `task` −0.037 — the only behavioural evidence that the §20.1 pin worked).

---

## (C) STALENESS

1. **The log's own cutoff.** Line 5 declares it runs through `d9dc0106`. **Four commits now post-date it**: `c04d556b` (20.4 pass 2), `1e364973`, `dce44a92` (seed42 37/37, 200→600 NULL), `9e06490e`. Items A2 and A3 are the substance of that gap. The log is honest about its cutoff, but §20.7 and §23 are now materially wrong. **Six `gcg_perprompt` jobs are RUNNING right now** (757711, 757709, 757697, 757672, 757662, 757525), so both numbers will move again.
2. **`docs/SECTION20_RESULTS.md` §5 is stale in the same way** — still cites `asym_p204_equivalence.json` and "BOUNDED — provisional". Fix upstream, not just in the log.
3. **`docs/OWED_SUBMISSIONS.md` OUTSTANDING item 5 is stale** — it says "§20.4 pass 2 — blocked… unreachable as specified", but pass 2 *was* run via the judge-denoised route.
4. **Internal judge-noise conflict.** §1 line 57 gives "≈2 pp within-run / ~3.4-7 % at boundary / ~6 pp between-run"; §20 line 485 (Part F) asserts "~3.4 % of labels" as a standing `[V]` finding; §20.3 line 529 (Part G) declares the corpus figure **superseded** at ≈0.62 %. Three numbers, one document, no cross-reference — and the ±0.03-0.08 floor derived from the retired figure is used to retire effects throughout Part F (§16 Gate E, §18). Note the 3.4 % itself is an n≈148 hand-count (`ASYMMETRY_SPRINT_EXECUTION_LOG.md:686`), not `[V]`-grade; the measured artifact `outputs/asym_p203_judge_replicates.json` gives band flip 33/93 = 35.5 % and 33/1998 = 1.65 % corpus-wide.
5. **Test-suite count.** §3's "113 → 205 passing" is a Part-C-era figure quoted as the sprint-wide endpoint; the suite at HEAD is larger (one auditor ran it green at 228 passed / 13 skipped).

---

## FINDINGS I DISCARDED (could not confirm, or refuted)

- **"'25 heads sig on BOTH clearharm splits' has no artifact"** — **refuted.** A second agent re-ran `scripts/phase5_analyze.py` on the committed layer-half run dirs and reproduced `CONFIRMED …: 25 heads` (clr dev 31 / heldout 31). A `grep` miss is not a contradiction; the merge step is required to reproduce. The log's parenthetical at line 130 explicitly says the counts were reproduced by re-running the script.
- **"397/412 is RUNMETA only; DONE is 385"** — the log **already states it correctly** at line 370 ("397/412 dirs carry RUNMETA, 385 carry DONE"); only §6's one-line compression at line 205 elides it. Downgraded to a wording nit, not an error. (Live counts are now 523 RUNMETA / 507 DONE over 605 dirs — the 397/412 figure is correctly scoped to the Part-C snapshot.)
- **"A GitHub PAT sits in plaintext in `.git/config`"** — reported by one agent on the handoff doc's own say-so, explicitly unverified. I did not attempt to read `.git/config`. Flagging as **unverified but worth the user checking directly**, since rotation is cheap and the handoff doc asserts it.
- **"Job 757702 (seed-44 shard 1) failed and is tracked nowhere"** — plausible and the failure signature (V100 nodes rejected by the GPU guard) is consistent, but 757702 no longer appears in `squeue` and I did not re-run `sacct` to confirm the exit code. Low severity regardless; `OWED_SUBMISSIONS.md` does track seed-44 shards 1-3 as owed.