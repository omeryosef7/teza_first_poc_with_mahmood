# Results Freeze Audit — prior sprint, before the causal core builds on it

**CAUSAL_CORE_PLAN §16.1 (S0).** Produced 2026-07-29 by a four-way independent audit of
`PAPER_DRAFT.md`, `SPRINT_REPORT.md`, the results docs, and the artefact/registry
inventory. Each auditor verified doc-level numbers against the on-disk JSON that produces
them, then a synthesis pass consolidated them.

Scope: this audits the PRIOR sprint only. The new fixed-pair causal work is tracked live in
[`CAUSAL_CORE_PROGRESS.md`](CAUSAL_CORE_PROGRESS.md).

Headline: ~85% of claims VERIFIED and every headline interval reproduced exactly from raw
artefacts. The defects that matter are (a) a handful of stale/mistranscribed cells,
(b) two claims with **no backing artefact**, (c) a **provenance** gap, and (d) one framing
issue — the central causal story is an *inference*, not yet a demonstrated chain. See
"Overclaims" and "Freeze recommendation" below; every item is tracked in
`CAUSAL_CORE_PROGRESS.md` under S0.

---

## Verdict

The prior sprint is **safe to build on numerically, but not yet safe to call "frozen."** Across four independent audits covering ~100 distinct quantities, every headline interval reproduced exactly from on-disk raw artefacts — the TOCTOU gradient (+0.846 [+0.787, +0.899], n=169), its two cross-model replications, the seed-averaged necessity triple (0.549 / 0.399 / 0.181, n=23), the sufficiency contrasts (mid −0.393, late −0.064), the predictor AUCs (0.732 CV / 0.668 held-out-concept), the GCG repr_loss trajectories, and the held-out ASR/refusal table. Roughly 85% of claims are VERIFIED. The defects are of three kinds, none of which invalidates a headline: (a) a small number of stale or mistranscribed cells propagated across docs (early-window malicious rate 0.10 vs 0.123 on disk; lex-tight final task_loss 16.4 vs 16.1; direction-flipped univariate AUCs in `MECHANISTIC_OBJECTIVE.md`); (b) two claims with **no backing artefact at all** — a random control for behavioral sufficiency that was never run, and a 126×/8181× random-control ratio that is not reproducible under any interpretation and in fact points the opposite way; and (c) a serious **provenance** gap — `outputs/` and `data/behavioral_benchmark/` are gitignored (confirmed via `git check-ignore`), `EXPERIMENT_REGISTRY.csv` holds 39 rows all dated ≤ 2026-07-27 and covers none of the behavioral half of the sprint, and the output tree is still being written into (81 → 83 → 84 → 100 directories observed across the audit window). Separately, the paper's central causal story is an **inference, not a demonstrated chain**: the timing experiment injects the raw harmful concept at varying depth and never manipulates the emergence depth of the hijacked representation. Fix the ~12 wording items below, materialise the three missing summary JSONs, capture a checksum manifest against a named commit, and this is a solid base.

## Claim ledger

| id | quantity | value in doc | verdict | source file |
|---|---|---|---|---|
| eligible-bases-llama | eligible bases, Llama primary screen (PAPER_DRAFT §4.1, SPRINT_REPORT §3.1) | 37/40 | VERIFIED | `outputs/behavioral_screen_curated_v1/screen_summary_corrected.json` |
| clean-successes-42 | clean-success DS conditions, strict cut | 42 | VERIFIED | `outputs/behavioral_screen_curated_v1/per_condition_corrected.json` |
| clean-successes-14-concepts | distinct concepts among the 42 (3 docs) | 14 | VERIFIED | `data/behavioral_benchmark/screening_matrix_curated_v1.json` + per_condition_corrected.json |
| necessity-delta | seed-avg early-window flip rate (PAPER_DRAFT §4.2, SPRINT_REPORT §3.2, BEHAVIORAL_CAUSALITY_RESULTS §1b) | 0.549 [0.362, 0.737] | VERIFIED (no summary JSON) | `outputs/beh_necessity_Llama-3.1-8B-Instruct_20260729_0732*_early_6926{98,99,700}/necessity_raw.jsonl` |
| necessity-minus-identity | necessity − identity control | 0.399 [0.177, 0.617] | VERIFIED (no summary JSON) | same three necessity dirs |
| necessity-minus-random | necessity − norm-matched random | 0.181 [−0.021, 0.383] | VERIFIED, correctly labelled NS | same three necessity dirs |
| necessity-unit-description | unit count / replication structure | "23 base×codeword units, seed-averaged over three seeds" | MISMATCH | same three necessity dirs |
| nec-early-window-n20 | single-run early necessity table + CI (n=20) | 0.50 [0.30, 0.70]; controls 0.05 / 0.25 | VERIFIED | `outputs/beh_necessity_..._20260727_204515/necessity_summary.json`, `outputs/behavioral_causality_cis.json` |
| toctou-refusal-per-window | refusal by injection depth, Llama (3 docs + abstract) | 0.87 / 0.25 / 0.02 | VERIFIED (0.866 / 0.246 / 0.017) | `outputs/behavioral_causality_llama_37base.json` |
| toctou-malicious-per-window | malicious rate by depth, early cell | early 0.10 | MISMATCH (disk 0.123) | `outputs/behavioral_causality_llama_37base.json` |
| toctou-early-late-gap | paired early−late refusal (all docs) | +0.846 [+0.787, +0.899], n=169 | VERIFIED | `outputs/behavioral_causality_llama_37base.json` |
| toctou-early-mid / mid-late | intermediate paired diffs | +0.631 [+0.562,+0.699] n=176; +0.214 [+0.156,+0.277] n=173 | VERIFIED | `outputs/behavioral_causality_llama_37base.json` |
| toctou-qwen3 | early−late refusal, Qwen3-14B | +0.854 [+0.732, +0.951], n=41 | VERIFIED (no summary JSON) | `outputs/beh_sufficiency_Qwen3-14B_20260728_09{1747,1938}/sufficiency_raw.jsonl` |
| toctou-phi4 | early−late refusal, Phi-4-mini | +0.250 [+0.056, +0.444], n=36 | VERIFIED (no summary JSON) | `outputs/beh_sufficiency_Phi-4-mini-reasoning_20260728_14{1555,1903}/sufficiency_raw.jsonl` |
| layer-windows | early/mid/late layer ranges (PAPER_DRAFT §3) | 0–9 / 10–19 / 20–31 for all models | MISMATCH | `outputs/beh_sufficiency_Qwen3-14B_*/sufficiency_summary.json` |
| suff-early-ds-minus-direct | DS−Direct malicious rate, early | −0.061 [−0.123, 0.000] n=179 (SPRINT_REPORT); omitted in PAPER_DRAFT | VERIFIED / UNVERIFIABLE (omission) | `outputs/behavioral_causality_llama_37base.json` |
| suff-mid-ds-minus-direct | DS−Direct, mid | −0.393 [−0.470, −0.311], n=183 | VERIFIED | `outputs/behavioral_causality_llama_37base.json` |
| suff-late-ds-minus-direct | DS−Direct, late | −0.064 [−0.116, −0.012], n=173 | VERIFIED | `outputs/behavioral_causality_llama_37base.json` |
| suff-12base-corroboration | 12-base clean per-condition contrasts | mid −0.295 / late −0.161 / early +0.032 | VERIFIED | `outputs/behavioral_causality_llama_clean.json` |
| suff-crossmodel-rows | cross-model DS−Direct rows | Qwen3 late −0.349; Phi-4 early −0.263, late −0.167 | VERIFIED | Qwen3/Phi-4 `sufficiency_raw.jsonl` dirs |
| suff-qwen3-early-omitted | Qwen3 EARLY DS−Direct | NOT REPORTED anywhere | MISMATCH (on disk +0.190 [+0.071,+0.310] n=42) | `outputs/beh_sufficiency_Qwen3-14B_20260728_091747/sufficiency_raw.jsonl` |
| suff-late-below-random-control | "falls below its random control" | asserted | **SOURCE_MISSING** | no random arm exists in any sufficiency run |
| ds-injection-refusal-counts | DS-injection refusal counts quoted in 37-base section | early 6/63, mid 4/63, late 0 | MISMATCH (stale 12-base) | `outputs/beh_sufficiency_..._20260729_014456_*` (disk: 0.284 / 0.216 / 0.162) |
| late-never-refused | late refusal in prose | "never refused (0%)" | MISMATCH (0.017 [0.000,0.040]) | `outputs/behavioral_causality_llama_37base.json` |
| deepseek-eligible | DeepSeek eligible bases | 27/40 | VERIFIED | `outputs/behavioral_screen_curated_deepseek_r1/screen_summary_reclassified.json` |
| deepseek-66-malicious | DeepSeek DS_MALICIOUS conditions | 66 | VERIFIED as a count, MISMATCH as evidence (37 on eligible bases; 0 under the strict cut) | `outputs/behavioral_screen_curated_deepseek_r1/{screen_summary.json, per_condition_corrected.json}` |
| deepseek-timing-deferred | DeepSeek timing run | deferred | VERIFIED (dirs empty) | `outputs/beh_sufficiency_DeepSeek-R1-Distill-Llama-8B_20260729_09094{5,6}_*` |
| four-model-families | models screened | four | VERIFIED | four `behavioral_screen_curated_*` dirs |
| heldout-concept-auc | GroupKFold AUC (3 docs) | 0.668 ± 0.089 | VERIFIED | `outputs/features_llama8b/success_predictors.json` |
| cv5-auc | 5-fold CV AUC | 0.732 (± 0.060) | VERIFIED | same |
| late-align-inert | univariate AUC, late_align | 0.502 | VERIFIED | same |
| predictor-aucs-flipped | univariate AUCs early/mid/peak/auc_align | 0.651 / 0.657 / 0.517 / 0.609 | MISMATCH (disk 0.349 / 0.343 / 0.483 / 0.391) | same (`univariate_abs_power`) |
| codeword-selection-gain | temporal vs random codeword selection | +0.09 [−0.037, +0.225], n=40, NS | VERIFIED (artefact found; PAPER_DRAFT mislabels it "ASR") | `outputs/features_cw6/codeword_selection.json` |
| gcg-suffix-length / config | suffix length, steps, seed | 16 tokens, 200 steps, seed 42 | VERIFIED | `outputs/gcg/opt_qwen3_temporal/CONFIG.json` |
| gcg-train-val-split | train / held-out bases | 25 / 13 | VERIFIED | `data/gcg/curated_qwen3_neutral.jsonl` |
| gcg-reprloss-weighted | repr/task trajectory, weighted | 0.446→0.446→0.565; 59.6→3.8 | VERIFIED | `outputs/gcg/opt_qwen3_temporal/ITERATION_LOG.jsonl` |
| gcg-reprloss-lextight | repr/task trajectory, lex-tight | 0.480→0.463→0.535; 63.4→**16.4** | MISMATCH (task_loss 16.11 on disk) | `outputs/gcg/opt_qwen3_temporal_lex/ITERATION_LOG.jsonl` |
| gcg-reprloss-lexwide | repr/task trajectory, lex-wide | 0.454→0.450→0.452; 77.7→71.1 | VERIFIED | `outputs/gcg/opt_qwen3_temporal_lexwide/ITERATION_LOG.jsonl` |
| gcg-heldout-asr | held-out ASR by arm | temporal 0, baseline 0 (none 0.077 omitted in PAPER_DRAFT) | VERIFIED | `outputs/gcg/gcg_asr_summary.json` |
| gcg-refusal-backfire | refusal under temporal suffix | 0.615 (8×), n=13, no CI | VERIFIED arithmetically | `outputs/gcg/gcg_asr_summary.json` |
| gcg-judge-noise-none-arm | single none-arm success | one val base | VERIFIED | `outputs/gcg/gcg_asr_raw.jsonl` |
| mixed-cache-wiring | mixed cache = benign early / harmful late | verified | VERIFIED (holds from layer 5 on; layer 0 identical) | `outputs/gcg/cache_qwen3_{mixed,neutral,direct}/*.pt` |
| thinking-paired-rates | Qwen3 think vs nothink, n=90 | 0.222 vs 0.244; refusal 0.067 vs 0.000 | VERIFIED | `outputs/behavioral_screen_curated_qwen3_think/thinking_comparison.json` |
| thinking-dose-response | dose-response by demo count | 0.14/0.23/0.36 vs 0.09/0.16/0.16 | MISMATCH (unmatched base sets) | `outputs/behavioral_screen_curated_{qwen3_think,qwen3_nothink}/screen_summary_reclassified.json` |
| multiconcept-3model | 3-model panel (hijack, peak gap, necessity, suff) | Llama/Qwen3/Phi-4 rows | VERIFIED | `outputs/multiconcept_aggregate_{llama8b,qwen3,phi4}.json` |
| knockout-crossmodel | knockout table, C3-gen | 12/12, 12/12, 6/6 | VERIFIED but pre-fix condition (`demos_all`) | `outputs/ko_gen_{llama8b,qwen3,phi4}/stage4_knockout_results.json` |
| knockout-8of8-fixed | confound-free demo-only knockout | 8/8, P_harm→0 | VERIFIED | `outputs/ko_gen_llama8b_fixed/stage4_knockout_results.json` |
| codeword-panel-embedding | 18-codeword panel, Pearson r | 16/18 hijack; r=−0.18 | VERIFIED (fp16 login run; bf16 rerun gives −0.189) | `outputs/codeword_study_login/codeword_study_results.json` |
| defense-tpr-fpr | probe detector | TPR 1.00 / FPR 0.00 | VERIFIED (n=9, fp16/TITAN Xp) | `outputs/defense_login/defense_results.json` |
| ko-gen-phi4 | Phi-4 knockout CI | 0.139→0.000, 6/6, [0.060,0.220] | VERIFIED | `outputs/ko_gen_phi4/stage4_knockout_results.json` |
| random-control-126x-8181x | random patch "weaker than" necessity drop | 126× / 8181× | MISMATCH / not reproducible | `outputs/stage2_patching_..._20260727_001943/stage2_results.json` |
| patchscopes-necessity-baseline | virus_muffin baseline P_harm | 0.102 (RESULTS_SYNTHESIS) vs 0.078 (CAUSAL_RESULTS_SUMMARY) | MISMATCH (disk 0.0997 fp16 / 0.0351 bf16) | `outputs/stage2b_fixeddecoder_validate/stage2b_results.json` |
| bootstrap-config | CI method | 10k resamples, fixed seed | VERIFIED | `analyze_behavioral_causality.py` (`stats.paired_bootstrap_ci`, n_boot=10000, seed=0) |
| judge-threshold | judge rule | ≥0.25 → MALICIOUS, precedence | VERIFIED (rule name `MALICIOUS_first_v2` in every screen summary; threshold lives in code) | `17_validate_behavioral_triplets.py` |
| models-hardware | run environment | L40S, bf16 | VERIFIED | `outputs/beh_sufficiency_..._014456_early_692637/sufficiency_summary.json` meta |
| figures-exist | four cited figures | present | VERIFIED (only git-tracked artefacts) | `figures/` |
| registry-row-count | registry rows | 39 | VERIFIED | `EXPERIMENT_REGISTRY.csv` |
| registry-panel07-ci | panel07 suff CI 0.037 [0.027,0.047] | cited COMPLETE | **SOURCE_MISSING** | row points at bare `outputs/` |
| registry-qwen3-generality-ci | timing 33.5 [32.6,34.0]; suff 0.133 [0.089,0.184] | cited COMPLETE | **SOURCE_MISSING** | row points at bare `outputs/` |
| appendix-all-committed | "key output files (all committed)" | asserted | MISMATCH (0 tracked; `.gitignore:12` ignores `outputs/`) | `.gitignore` |
| experiment-registry-coverage | registry as provenance index | implied complete | **SOURCE_MISSING** | `EXPERIMENT_REGISTRY.csv` (no behavioral/gcg rows) |
| suff-vs-timing-independence | §3.3 and §3.4 as two results | presented as independent | MISMATCH (same generations, two label projections) | `analyze_behavioral_causality.py::timing_cis` |
| screen-v1-stale-summary | primary screen file in cited dir | dir cited, not file | HAZARD | `outputs/behavioral_screen_curated_v1/screen_summary.json` (pre-fix: 4 eligible / 1 success) |

## Mismatches and missing sources

| # | Item | Action |
|---|---|---|
| 1 | **`outputs/` and `data/behavioral_benchmark/` are gitignored**; the appendix says "all committed." Confirmed: `.gitignore:12 → outputs/`, `doublespeak_causality/.gitignore:7 → data/behavioral_benchmark/`. Only `figures/` is tracked. | Blocking for the word "freeze." Either commit the aggregate JSONs + a sha256 manifest, or archive the tree off-node. Fix the appendix wording. |
| 2 | **Registry covers none of the behavioral half.** 39 rows, all ≤ 2026-07-27; ≥30 dirs post-date it. | Backfill rows for every dir cited by a headline number, with job id, git commit, and canonical flag. |
| 3 | **Sufficiency "random control"** cited in `BEHAVIORAL_CAUSALITY_RESULTS.md` §2 — the runs contain only `baseline_neutral`, `suff_DS_<win>`, `suff_Direct_<win>`. | Delete the clause (preferred) or run the arm. Do not carry it forward. |
| 4 | **126× / 8181× random-control ratio** unreproducible; the artefact shows the random patch collapsing P(harm) to ~0 from L6 on, i.e. the control fails rather than passes. | Replace everywhere with the accurate statement already present in `CAUSAL_RESULTS_SUMMARY` C1: specificity vs random holds only at L0–1. |
| 5 | **Seed-averaged necessity triple has no summary JSON** and cannot be regenerated (`--necessity-dir` takes one dir). Also the keying differs between auditors — one reproduced it on `(base_id, codeword)`, one on `(base_id, codeword, context_len)`; both give n=23 and 0.549, but per-run means are 0.378/0.432/0.432 → 0.414, so 0.549 is a re-weighted estimate, not a plain seed mean. | Add multi-dir seed-averaging to the analyzer, emit `necessity_seedavg.json` recording the exact key, and describe the estimator honestly in §4.2. |
| 6 | **Cross-model TOCTOU CIs (Qwen3, Phi-4) have no summary JSON.** | Emit `behavioral_causality_{qwen3,phi4}.json` via `--timing-dir` before freeze. |
| 7 | **Early-window malicious rate 0.10** in PAPER_DRAFT §4.3, SPRINT_REPORT §3.4, BEHAVIORAL_CAUSALITY_RESULTS:178 — disk says 0.123 (22/179); the same doc's §3.3 says 0.12. Related: benign 0.03 vs disk 0.011. | Correct all three docs to 0.123 / 0.011. Likely a leftover from the 12-base run. |
| 8 | **lex-tight final task_loss 16.4** in PAPER_DRAFT §4.5 and GCG_MAC_COMPARISON §6d — disk 16.11. | Correct to 16.1. Cosmetic but it is a table value. |
| 9 | **Direction-flipped univariate AUCs** in `MECHANISTIC_OBJECTIVE.md` §2 (printed = 0.5 + `univariate_abs_power`). | Print the true AUC and the discriminative power in separate columns, labelled "inverted." |
| 10 | **Qwen3 EARLY sufficiency (+0.190 [+0.071,+0.310], n=42) omitted** from a table that closes "Audit fully closed — no pending numbers." It is the only counter-directional significant result. | Add the row and soften the closing line. |
| 11 | **Stale 12-base DS-refusal counts (6/63, 4/63, 0)** quoted inside the 37-base section; current rates are 0.284 / 0.216 / 0.162. | Replace with 37-base numbers; drop "barely triggers refusal." |
| 12 | **Thinking dose-response series are unmatched** (15-base think vs 40-base nothink) under a heading saying "n=90 matched." | Recompute on the 15 matched bases (nothink 0.200/0.267/0.267) and restate. |
| 13 | **Patchscopes virus_muffin baseline: 0.102 vs 0.078 across two docs**, neither matching disk (0.0997 fp16 / 0.0351 bf16). | Pick the canonical run, cite the file, use its value. |
| 14 | **Knockout C3-gen table uses the pre-fix `demos_all` condition** (blocks the request too); the audited rerun is `ko_gen_llama8b_fixed` / `demos_only`, n=8. | Label the condition in the table and cross-reference the fixed rerun. |
| 15 | **Registry rows `panel07_necsuff_20260727` and `qwen3_generality_20260727` cite CIs with no backing file** (bare `outputs/` pointer). | Persist the aggregates or mark the metrics as unverified. |
| 16 | **Canonicality unrecorded**: ~13 `beh_sufficiency_*`, ~6 `beh_necessity_*`, and four top-level aggregates (`behavioral_causality_cis{,_full}.json`, `_llama_37base.json`, `_llama_clean.json`) with no on-disk marker of which is authoritative. | Add a `CANONICAL.md` or a `canonical: true` field; pin each headline number to one named file. |
| 17 | **`outputs/behavioral_screen_curated_v1/screen_summary.json` is the pre-fix file** (4 eligible / 1 success) sitting beside the corrected one; docs cite the directory. | Rename to `screen_summary_PREFIX_SUPERSEDED.json` and cite exact filenames. |
| 18 | **`BEHAVIORAL_BENCHMARK.md` §6 still reads "Curated yield: PENDING SLURM 689373"** yet three docs cite it as the source of 42/14. | Fill it in from `per_condition_corrected.json`. |
| 19 | **Layer-window definitions differ per model** but §3 states one set. | State per-model windows; note Qwen3/Phi-4/DeepSeek ran early+late only. |
| 20 | **§3.3 and §3.4 are two label projections of the same generations.** | Say so; their agreement is not corroboration. |
| 21 | **Two cited-but-unlisted artefacts**: `outputs/behavioral_screen_curated_qwen3_think/thinking_comparison.json`, `outputs/features_cw6/codeword_selection.json`. | Add to the appendix path list. |
| 22 | **Registry hygiene**: 6 rows stuck RUNNING/QUEUED; 12 rows with bare-path `output_dir`; 2 fp16/TITAN-Xp rows (`codeword_study_login`, `defense_login`) not flagged non-canonical though the convention exists elsewhere. | Close statuses, specify dirs, flag fp16 rows. |

## Overclaims to correct in PAPER_DRAFT.md

| Location | Offending phrase | Why | Suggested rewording |
|---|---|---|---|
| Abstract (iii); §4.3 bold; §7 | "governed by a **causal timing law** … we interpret this as a **time-of-check (TOCTOU)** property — Doublespeak's late-emerging meaning slips past the check" | Correlation as causality + single mechanism generalised. The timing experiment injects the **raw** concept at varying depth; nothing manipulates the depth at which the *hijacked* meaning emerges. The link to Doublespeak is borrowed from prior observational decoding work. **Fix this one first.** | "…(iii) accompanied by a steep depth-dependent refusal effect: injecting the raw harmful concept early is refused 87% of the time vs 2% late (early−late +0.846 [+0.787,+0.899], n=169). This is consistent with refusal acting on early representations, which would explain why a late-emerging meaning is unchecked — but we do not manipulate hijack emergence depth, so the connection remains an inference." |
| Abstract; §4.3 | "late yields refusal only 2% and **compliance** instead" | Reads as "late injection jailbreaks." Disk: late malicious 0.092, **below** early (0.123) and one fifth of mid (0.492); 89% benign. Low refusal at late is as consistent with loss of behavioral effect as with escaping a check. | "…late yields refusal only 2%; note late injection also yields little harmful output (0.09 vs 0.49 at mid; 89% benign), so the refusal drop partly reflects loss of behavioral effect. Harmful output peaks at mid." |
| Abstract; §4.5 heading/bold; §7 | "a mechanism-derived temporal objective **cannot be optimized** into an adversarial suffix … **not suffix-optimizable**" | One optimizer's failure as impossibility: one optimizer (GCG), one model (Qwen3-14B), 16 tokens, 200 steps, one placement, 25 train bases, n=13 val. | "…resisted 16-token GCG optimization on Qwen3-14B across three selection strategies (no sustained repr_loss decrease over 200 steps) and increased refusal rather than success — evidence that it is not readily distillable by this optimizer at this scale; other optimizers, lengths and models untested." |
| §4.5 | "repr_loss **never decreased** across three selection strategies" | Contradicted by the adjacent table and the raw logs: lex-tight 0.480 → min 0.463; lex-wide 0.454 → min 0.450. | "showed no sustained decrease in any of three strategies — largest transient improvement 0.017 (lex-tight); final exceeded initial in two of three runs." |
| Contributions item 3; §4.3 | "a **monotone** early→late refusal gradient, **significant across three architectures**" | Monotonicity needs ≥3 points; only Llama has three windows. Qwen3/Phi-4 ran early+late only, with model-scaled windows differing from the §3 definition. | "a monotone early→mid→late gradient on Llama-3.1-8B, with the early-vs-late difference reproduced on two further architectures (Qwen3 +0.854 [+0.732,+0.951]; Phi-4 +0.250 [+0.056,+0.444]; early/late only, windows scaled per model)." |
| Abstract (ii); §7 | "causally necessary at early layers and **conditionally sufficient**" | "Conditionally sufficient" has no referent — every sufficiency contrast is negative (DS malicious 0.061 / 0.098 / 0.029). Also "causally necessary" omits that the random-control margin (+0.181) crosses zero, which §4.2 and §6 state honestly. | "(ii) causally dependent on the early-layer codeword representation — patching toward its benign counterpart flips harmful→benign (0.549 [0.362,0.737]), significantly above identity (+0.399 [0.177,0.617]) but only non-significantly above norm-matched random (+0.181 [−0.021,0.383]) — while the hijacked state is **not** behaviorally sufficient when transplanted (malicious ≤0.10 at every depth)." |
| Abstract; contributions 3; §5 | "The timing signature is **predictive** … predicts which items jailbreak" | AUC 0.668 ± 0.089 is a fold sd, not a CI; a 2-sd band reaches 0.49 (chance). No test against 0.5 exists. It is a correlational feature listed beside causal results. | "carries modest predictive signal: held-out-concept AUC 0.668 ± 0.089 (GroupKFold, 46 positives of 240; fold spread reaches chance), with late alignment alone at 0.502. This is a correlational association, not further causal evidence." |
| Abstract; §4.4 | "behaviorally we find the opposite, **Direct ≫ DS**, at mid … and late (−0.064)" | "≫" holds at mid (0.098 vs 0.492) but not at late (0.029 vs 0.092, both near floor, CI reaching −0.012). Early (−0.061 [−0.123, 0.000]) is dropped entirely — the paper shows only the two windows excluding zero. | "…Direct is far more potent at mid (0.098 vs 0.492; −0.393 [−0.470,−0.311], n=183). The same sign holds at late between near-floor rates (−0.064 [−0.116,−0.012]) and at early with a CI touching zero (−0.061 [−0.123, 0.000], n=179)." |
| §4.1; contributions 1 | "37/40 bases eligible and **42 DS generations are clean jailbreak successes**… a genuine behavioral attack" | Raw count with no base rate; 240 conditions screened, per-generation rate ≈0.18–0.24, 18/40 bases ever succeed. Also "42" is a stricter cut than the file's own DS_MALICIOUS=46 / MALICIOUS=52, and the cut is unstated. | "37/40 eligible; 42 of 240 screened DS generations are clean successes (Direct refused, Neutral benign, DS malicious), across 18 bases and 14 concepts — roughly 0.18–0.24 per generation. A genuine, if low-rate, behavioral attack." |
| §4.3 final sentence | "reproduces on a fourth model … (27/40 eligible, **66 malicious conditions**)" | 66 spans all 240 conditions including the 13 bases the eligibility gate excludes; eligible-restricted count is 37. DeepSeek's Direct arm is never REJECTED, so the strict cut behind "42" gives 0 — the two numbers are not comparable. | "…DeepSeek-R1-Distill-8B: 27/40 eligible, 37 DS_MALICIOUS conditions on eligible bases across 16 bases. (Its Direct-arm outputs are judged malicious rather than refused, so counts are not directly comparable to Llama's.)" |
| §4.5; abstract | "refusal rises to **0.615 (8× baseline)**" | Multiplier built on one refusal event out of 13, no CI anywhere. One event moves it between 4× and unbounded. | "refusal rises to 0.615 (8 of 13 held-out bases) vs 1 of 13 for baseline GCG and 0 of 13 with no suffix — a clear directional increase, on n=13 with no interval." |
| §6 Limitations | "NS **+0.09 ASR gain** (n=40)" | Magnitude/n/NS verdict are right, but the source measures a jailbreak rate from codeword selection on the 6-codeword screen, not ASR from an optimized attack. | "NS +0.092 [−0.037,+0.225] gain in jailbreak rate from temporal vs random codeword selection (n=40 bases; `outputs/features_cw6/codeword_selection.json`)." |
| Header note; §Reproducibility | "All quantitative claims are copied from **committed**, audited output files" | Provenance overclaim, and freeze-blocking: `outputs/` is gitignored; §4.2, the cross-model §4.3 rows and the §6 codeword result have no summary JSON at all. | "…derived by the scripts in `doublespeak_causality/` from files under `outputs/` (present on disk; not tracked in git). Numbers in §4.2, the cross-model rows of §4.3, and §6's codeword-selection result are recomputed from raw per-generation logs and do not yet have committed summary artefacts." |

*(Two further overclaims live only in the older docs and should be fixed there, not in the draft: the "126×/8181× random control" in `RESULTS_SYNTHESIS.md` §RQ1 / `CAUSAL_RESULTS_SUMMARY.md` C1, and "architecture-general" in `CAUSAL_RESULTS_SUMMARY.md` B2, whose necessity/sufficiency columns rest on n=8/11/5 items of Patchscopes decoding, not behavior.)*

## Artefact integrity

- **Output directories:** 83 at first snapshot → 84 mid-audit → **100 at final check.** The tree is live; SLURM job 693557 (`ds_pairr`) wrote `pair_reps_*` / `pair_directions_*` during the audit, and the new sprint (S2/S3) is writing into the same tree the freeze is meant to cover. **New work must use a separate prefix.**
- **Completion:** two naming conventions coexist (`*_summary.json` for 2026-07-27..29 runs, `*_results.json` for stage1–4). Gating on `*_summary.json` alone gives 31 dirs (30 with `status == COMPLETE`); gating on any JSON with `status == COMPLETE` gives **67 of 83**. Decomposition: 67 COMPLETE + 13 empty + 3 non-empty-without-status (`features_cw6`, `features_llama8b`, `gcg`).
- **Empty (failed/pre-empted) dirs — 13:** `beh_necessity_Llama-3.1-8B-Instruct_{20260727_190320,195216,202244,203153}`; `beh_sufficiency_Llama-3.1-8B-Instruct_{20260727_184811,200253,203440}`; `beh_sufficiency_DeepSeek-R1-Distill-Llama-8B_{20260729_090945_late_692758,20260729_090946_early_692757}`; `behavioral_screen_curated_cw4x42`; `emergence_Qwen3-14B_20260727_061950`; `stage2_patching_Llama-3.1-8B-Instruct_20260726_232217`; `stage4_layerko_Llama-3.1-8B-Instruct_20260727_041742`. The two DeepSeek ones corroborate the documented deferral.
- **Orphan output dirs:** only **14** dirs are named by any registry row (`behavioral_login`, `codeword_study_login`, `defense_login`, `emergence_panel_login`, `ko_gen_phi4`, `lko_gen_llama8b`, `stage1_gpt4omini_login`, `stage1_repmap_Llama-3.1-8B-Instruct_20260726_231610`, `stage2_login_validate2`, `stage2_patching_Llama-3.1-8B-Instruct_20260727_001943`, `stage2b_login_validate`, `stage2c_login_validate`, `stage4_knockout_login`, `stage4_layerko_login`). **≥67 dirs are orphaned**, including every dir behind a behavioral headline.
- **Orphan registry rows:** 39 rows, none dated after 2026-07-27. **12 rows** have a bare `outputs/` (or repo-root) `output_dir`; 6 of those are COMPLETE with a cited `key_metric` that therefore cannot be traced. **6 rows** are frozen in RUNNING/QUEUED. **Zero dangling paths** — the failure mode is under-specification, not deletion.
- **Loose top-level JSONs (10)**, of which the three `multiconcept_aggregate_*` are registered and the four `behavioral_causality_*` aggregates — the direct backing for `BEHAVIORAL_CAUSALITY_RESULTS.md` — are not, and carry no run dir, job id, or status.
- **Version control:** 0 files under `outputs/` are tracked (`.gitignore:12`); `data/behavioral_benchmark/` is likewise ignored. `figures/` (11 PNGs + `multiconcept/`) are the only tracked artefacts.
- **Judge telemetry:** `n_judge_fail_rows == 0` / `judge_fail_frac == 0.0` across every cited run — clean.

## Freeze recommendation

Take the freeze against a **named git commit plus a checksum manifest** (path, mtime, sha256) of the following, captured while no SLURM job is writing:

**Behavioral screens (4 models)**
- `outputs/behavioral_screen_curated_v1/{screen_summary_corrected.json, screen_summary_reclassified.json, per_condition_corrected.json, eligible_bases_corrected.json, screen_raw.jsonl}` — and rename `screen_summary.json` to mark it superseded
- `outputs/behavioral_screen_curated_qwen3_nothink/`, `.../qwen3_think/` (incl. `thinking_comparison.json`), `.../phi4/`, `.../deepseek_r1/` — summary + per-condition files
- `data/behavioral_benchmark/screening_matrix_curated_v1.json`, `data/curated_concepts.json`

**Necessity (3 seeds)**
- `outputs/beh_necessity_Llama-3.1-8B-Instruct_20260729_073233_early_692698/necessity_raw.jsonl`
- `outputs/beh_necessity_Llama-3.1-8B-Instruct_20260729_073223_early_692699/necessity_raw.jsonl`
- `outputs/beh_necessity_Llama-3.1-8B-Instruct_20260729_073223_early_692700/necessity_raw.jsonl`
- `outputs/beh_necessity_Llama-3.1-8B-Instruct_20260727_204515/necessity_summary.json` (n=20 single-run table)
- **NEW, to be generated before freeze:** `outputs/necessity_seedavg.json`

**Sufficiency / timing**
- `outputs/beh_sufficiency_Llama-3.1-8B-Instruct_20260729_014456_early_692637/{sufficiency_raw.jsonl,sufficiency_summary.json}`
- `outputs/beh_sufficiency_Llama-3.1-8B-Instruct_20260729_014456_mid_692638/{...}`
- `outputs/beh_sufficiency_Llama-3.1-8B-Instruct_20260728_230505/{...}` (late)
- `outputs/beh_sufficiency_Qwen3-14B_20260728_09{1747,1938}/sufficiency_raw.jsonl`
- `outputs/beh_sufficiency_Phi-4-mini-reasoning_20260728_14{1555,1903}/sufficiency_raw.jsonl`
- `outputs/behavioral_causality_llama_37base.json` (**mark canonical**), `outputs/behavioral_causality_llama_clean.json`, `outputs/behavioral_causality_cis.json`, `outputs/behavioral_causality_cis_full.json` (mark the last two superseded or scope-limited)
- **NEW:** `outputs/behavioral_causality_qwen3.json`, `outputs/behavioral_causality_phi4.json`

**Predictors / codeword selection**
- `outputs/features_llama8b/{features.json, success_predictors.json}`
- `outputs/features_cw6/{features.json, codeword_selection.json}`

**GCG**
- `outputs/gcg/{gcg_asr_summary.json, gcg_asr_summary_temporal_lex.json, gcg_asr_raw.jsonl, gcg_suffixes_used.json}`
- `outputs/gcg/opt_qwen3_{baseline,temporal,temporal_lex,temporal_lexwide}/{CONFIG.json, ITERATION_LOG.jsonl}`
- `outputs/gcg/cache_qwen3_{neutral,direct,mixed}/` (or their checksums only, given size)
- `data/gcg/curated_qwen3_neutral.jsonl`

**Representation-level (cited by the older docs)**
- `outputs/multiconcept_aggregate_{llama8b,qwen3,phi4}.json`
- `outputs/ko_gen_llama8b_fixed/stage4_knockout_results.json` (**canonical**), `outputs/ko_gen_{llama8b,qwen3,phi4}/stage4_knockout_results.json` (**mark pre-fix**)
- `outputs/codeword_study_login/codeword_study_results.json` (flag fp16/Pascal), `outputs/defense_login/defense_results.json` (flag fp16/Pascal, n=9)
- `outputs/stage2_patching_Llama-3.1-8B-Instruct_20260727_001943/stage2_results.json`, `outputs/stage2b_fixeddecoder_validate/stage2b_results.json` (needed to settle the 0.102/0.078 discrepancy)

**Code and provenance**
- `analyze_behavioral_causality.py`, `stats.py`, `17_validate_behavioral_triplets.py`, `19_run_behavioral_sufficiency.py`, `24_codeword_selection.py`
- `EXPERIMENT_REGISTRY.csv` — **backfilled** with rows for every dir above, statuses closed, bare-path pointers resolved, fp16 rows flagged
- `SPRINT_EXECUTION_LOG.md`, `PAPER_DRAFT.md`, `SPRINT_REPORT.md`, `BEHAVIORAL_CAUSALITY_RESULTS.md`, `GCG_MAC_COMPARISON.md`, `THINKING_VS_NONTHINKING.md`, `MECHANISTIC_OBJECTIVE.md`, `RESULTS_SYNTHESIS.md`, `CAUSAL_RESULTS_SUMMARY.md`, `BEHAVIORAL_BENCHMARK.md` (all after the corrections above)
- `figures/fig_{toctou_timing,sufficiency_depth,necessity_windows,crossmodel_behavioral}.png`
- **NEW:** `CANONICAL.md` mapping each headline number → exactly one file, and `FREEZE_MANIFEST.sha256`
