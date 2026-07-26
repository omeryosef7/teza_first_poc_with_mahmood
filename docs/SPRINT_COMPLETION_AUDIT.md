# Sprint Completion Audit — §A3 Run-Integrity Audit

Scope: read-only verification of every row in `results/EXPERIMENT_REGISTRY.csv`.
Working dir: `/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood`
Audit date: 2026-07-25. Read-only (ls/test/find/grep/git/python-json). No files other than this one were written; the CSV was NOT edited.

## 0. Repo state (verified)

- Git branch: `main` (`git branch --show-current`)
- HEAD commit: `f646dd4121dd59f2bf67a688c00b91a9fe7fc211` (`git rev-parse HEAD`), dated 2026-07-25 15:47 +0300.
- The entire distilling-jailbreaks pipeline is a fresh line of work: the first plan commit is `e21172e` "Phase 0 freeze + Phase 1 disjoint 25/495 split" on 2026-07-21 00:50 +0300. Every registry `code_commit` (`354749e`, `389170c`, `1de34e8`=current-family "HEAD") is dated 2026-07-21 or later — all strictly AFTER the 2026-07-19 GCG suffix-placement fix. No row is from the v1 placement-bug era. (Fact, from `git log`.)

## 1. Cross-cutting invariants (verified once, apply to all rows)

| Check | Result | Evidence |
|---|---|---|
| dev_25 vs heldout_495 task_ids disjoint | PASS — 0 overlap (25 and 495 unique ids) | `comm -12` on col1 of `data/manifests/dev_25.csv` vs `heldout_495.csv` |
| dev_train_20 vs heldout_495 disjoint | PASS — 0 overlap | same method on `dev_train_20.csv` |
| phase3_tropt used suffix_placement=user | PASS | `poc_stage_gcg_early/config.py:56` → `suffix_placement: str = "user"`. Driver `scripts/phase3_tropt_optimize.py:120` builds `template = f"{instruction} {{{{OPTIMIZED_TRIGGER}}}}"` — trigger appended to the **user** instruction, then TROPT applies the chat template. Suffix is optimized and evaluated in the user turn (no assistant-turn placement bug). |
| Position-extraction fix `THINK_START_IN_PREFILL_BY_FAMILY` present | PASS | `poc_stage4/model_family_utils.py:93` (dict) + `:106` (accessor) |
| Phi-4 `"<think>\n"` marker fix present | PASS | `poc_stage4/model_family_utils.py:72` → `"phi4": {"start": "<think>\n", ...}` with documented BPE-merge rationale (lines 63–74) |
| Judge = StrongREJECT, threshold 0.5, consistent | PASS | `poc_stage3/strongreject_scoring.py:20` → `DEFAULT_STRONGREJECT_THRESHOLD = 0.5`; all inspected `*_strongreject_summary.json` report `"threshold": 0.5` |

## 2. Per-row PASS / FAIL / CANT-VERIFY

Legend: (1) artifact exists on disk; (2) ASR == n_success/n_total where an ASR column is populated; (3) code_commit post-2026-07-19. "n/a-ASR" = row reports a discriminability/LOGO-AUC or causal-null metric with no ASR column, so check (2) is not applicable.

| # | run_id | artifact (verified path under repo) | (1) | (2) ASR recompute | (3) commit | Verdict |
|---|---|---|---|---|---|---|
| 1 | phase4_cot_gpt-o4-mini_dev25 | `outputs/phase4_cot_baseline/phase4_cot_gpt-o4-mini_dev25*` | ✓ | 22/24=0.917 ✓ | 354749e ✓ | PASS |
| 2 | phase4x_cot_deepseek-r1-distill-llama-8b_dev25 | `outputs/phase4_hf_local/phase4_cot_hf_deepseek-ai_DeepSeek-R1-Distill-Llama-8B_dev25*`; clean `outputs/phase4x_clean_baseline/clean_deepseek-ai_*_dev25*` | ✓ | 22/23=0.957 ✓; neutral 0.360, uplift +0.597 ✓ | 389170c ✓ | PASS |
| 3 | phase4x_cot_phi-4-mini-reasoning_dev25 | `outputs/phase4_hf_local/phase4_cot_hf_microsoft_Phi-4-mini-reasoning_dev25*`; clean `outputs/phase4x_clean_baseline/clean_microsoft_*` | ✓ | 17/22=0.773 ✓ | 389170c ✓ | PASS |
| 4 | phase4x_cot_gemma-3-4b-it_dev25 | `outputs/phase4_hf_local/phase4_cot_hf_google_gemma-3-4b-it_dev25*`; clean `outputs/phase4x_clean_baseline/clean_google_*` | ✓ | 25/25=1.000 ✓; neutral 0.000, uplift +1.00 ✓ | 389170c ✓ | PASS |
| 5 | phase3_tropt_gcg_qwen3_devtrain20 | `outputs/phase3_tropt/gcg_qwen3_empty_think_sh0|sh1/`, `outputs/phase3_tropt/eval_greedy/FREE_GENERATION_RESULTS.jsonl` | ✓ | 9/20=0.450 ✓ | 389170c ✓; suffix=user ✓ | PASS |
| 6 | phase3_tropt_mac_qwen3_devtrain20 | `outputs/phase3_tropt/mac_qwen3_empty_think/`, `eval_greedy/` | ✓ | 3/20=0.150 ✓ | 389170c ✓; suffix=user ✓ | PASS |
| 7 | phase5_qwen3_cot_dev25 | `outputs/phase5_qwen3_cot/phase4_cot_hf_Qwen_Qwen3-14B_dev25*` | ✓ | 18/22=0.818 ✓ | 389170c ✓ | PASS |
| 8 | phase6_CvsD_signal_qwen3 | `outputs/phase5_mechanistic/phase6_CvsD_auc.csv`, `phase6_CvsD_confound*.csv`, `phase6_CvsD_projections.jsonl` | ✓ | n/a-ASR (logo_auc=0.906) | 389170c ✓ | PASS |
| 9 | phase6_FvsG_signal_qwen3 | `outputs/phase5_mechanistic/phase6_FvsG_auc.csv` | ✓ | n/a-ASR (logo_auc=0.807) | 389170c ✓ | PASS |
| 10 | phase7_steer_clean_tc1_L20 | `outputs/phase7_causal/steer_pilot__tc1_L20/`, `success_dir__think_content_1__L20/` | ✓ | 0/45=0.000 ✓ | 389170c ✓ | PASS |
| 11 | phase7_steer_clean_pfl_L16 | `outputs/phase7_causal/steer_pilot__pfl_L16/`, `success_dir__prefill_last__L16/` | ✓ | 2/45=0.044 ✓ | 389170c ✓ | PASS |
| 12 | phase7_necessity_Dsucc_tc1_L20 | `outputs/phase7_causal/steer_attacked_necessity__tc1_L20/`, `attack_necessity_Dsucc6.jsonl`, `attack_necessity_Dsucc17.jsonl` | ✓ | n/a-ASR (necessity null; 34/36 baseline retained) | 389170c ✓ | PASS |
| 13 | phase17_detector_CvsD_qwen3 | `outputs/phase17_detect/detector_CvsD.csv`, `detector_CvsD_alllayers.csv`, `detector_CvsD_confound.csv` | ✓ | n/a-ASR (detector-logo) | 389170c ✓ | PASS |
| 14 | phase7_timing_gen_tc1_L20 | `outputs/phase7_causal/steer_timing_gen__tc1_L20/` | ✓ | 1/35=0.029 ✓ | 389170c ✓ | PASS |
| 15 | phase7_timing_prefill_tc1_L20 | `outputs/phase7_causal/steer_timing_prefill__tc1_L20/` | ✓ | 0/35=0.000 ✓ | 389170c ✓ | PASS |
| 16 | phase7scale_cot_heldout25 | `outputs/phase7scale_qwen3_cot_heldout25/ae_gens_for_scoring*`, `phase4_cot_hf_Qwen_Qwen3-14B_smoke25*` | ✓ | gemini 0.560=14/25 ✓ (SR behavior-level noted pending in registry) | 389170c ✓ | PASS |
| 17 | phase7scale_confound_heldout48 | `outputs/phase7scale_qwen3_cot_heldout25/detector_CvsD_confound.csv`, `heldout_mechanistic_manifest.jsonl` | ✓ | n/a-ASR (length-only 0.720) | 389170c ✓ | PASS |
| 18 | phase6_attention_signal_heldout | `outputs/phase7scale_qwen3_cot_heldout25/attention_signal.csv` | ✓ | n/a-ASR (maxconc 0.739) | 389170c ✓ | PASS |
| 19 | phase16_crossmodel_lengthtest | none — note states "reused Phase-4X"; slurm_job_id=none; no dedicated output file | derivable only | n/a-ASR | 389170c ✓ | CANT-VERIFY |
| 20 | phase16_deepseek_confound_heldout | `outputs/phase16_deepseek_cot_heldout25/detector_CvsD_confound.csv`, `success_dir__prefill_last__L25/` | ✓ | n/a-ASR (len-only 0.591) | 389170c ✓ | PASS |
| 21 | phase16_deepseek_think_confound | `outputs/phase16_deepseek_cot_heldout25/detector_CvsD_think_confound.csv`, `phase6_CvsD_auc_fixed.csv`, `extraction_fixed/` | ✓ | n/a-ASR | "HEAD" (=1de34e8, post-fix) ✓ | PASS |
| 22 | c3_length_identifiability | `outputs/phase5_mechanistic/phase6_length_identifiability.json` | ✓ | n/a-ASR (AUC len→success 0.827) | "HEAD" ✓ | PASS |
| 23 | c1_attn_temp_causal_qwen3 | `outputs/phase8_attn_causal/{nec_global,nec_targeted,suff_global,suff_targeted}/` | ✓ | 0/242 (causal null) ✓ | "HEAD" ✓ | PASS |
| 24 | c2_deepseek_dir_causal | `outputs/phase16_deepseek_cot_heldout25/steer_nec_pfl_L25/`, `steer_suff_pfl_L25/` | ✓ | 0/175 (causal null) ✓ | "HEAD" ✓ | PASS |
| 25 | phase9_softopt_gate4_qwen3 | `outputs/phase9_softopt/pfl_L16/` | ✓ | 3/25=0.12 vs neutral 0.08 ✓ | "HEAD" ✓ | PASS |
| 26 | phi4_crossmodel_confound | `outputs/phase_phi4_cot/phi4_CvsD_confound.csv`, `phi4_CvsD_confound_fixed.csv`, `extraction_fixed/` | ✓ | n/a-ASR (len-only 0.837) | "HEAD" ✓ | PASS |
| 27 | phi4_causal_steer | `outputs/phase_phi4_cot/steer_nec_pfl_L7/`, `steer_suff_pfl_L7/` | ✓ | 0/225 (causal null) ✓ | "HEAD" ✓ | PASS |
| 28 | dsllama_causal_steer | `outputs/phase_deepseek_llama_cot/steer_nec_pfl_L2/`, `steer_suff_pfl_L2/` | ✓ | 0/290 (causal null) ✓ | "HEAD" ✓ | PASS |
| 29 | external_transfer_maliciousinstruct | `outputs/phase_external/mech/ext_sr_input*`, `outputs/phase_external/phase4_cot_hf_Qwen_Qwen3-14B_dev100*`, `data/manifests/external_maliciousinstruct.csv` | ✓ | column n_success/n_total=84/99=0.848 matches SR artifact (84 positive/99); but free-text note says "ASR=0.737" — see corrections | "HEAD" ✓ | PASS (note flagged) |

## 3. Missing / underspecified artifacts

- Row 19 `phase16_crossmodel_lengthtest`: no dedicated artifact and `slurm_job_id=none`. The note says it reuses the Phase-4X per-model outputs (rows 2–4, which exist), so the numbers are re-derivable, but there is no standalone file to point an auditor at. Marked CANT-VERIFY (not a failure — a provenance gap).
- No row cites a path that is absent from disk. Every other cited phase directory and its key files were located.

## 4. Proposed registry corrections (DESCRIBED ONLY — CSV not edited)

1. **Literal `HEAD` in `code_commit` (rows 21–29).** Nine rows record the string `HEAD` rather than a pinned SHA. `HEAD` is a moving reference (currently `f646dd4`); at run time these jobs (slurm 677xxx–681xxx) sat on the `1de34e8` family. Replace `HEAD` with the concrete SHA (`1de34e8`) for reproducibility. All are post-2026-07-19, so this is a hygiene fix, not an integrity failure.
2. **Row 29 external_transfer note vs columns.** The note says "ASR=0.737" while the populated columns give `n_success/n_total = 84/99 = 0.848`, which is exactly the StrongREJECT row-level positive count in `ext_sr_input_strongreject_summary.json` (84 positive of 99, threshold 0.5). The 0.737 headline in the note cannot be reconciled with either the columns or the artifact. Recommend either correcting the note to 0.848 (row-level SR) or documenting what 0.737 refers to (e.g., a behavior-level/dedup or gemini figure) with its own numerator/denominator.
3. **Add an artifact-path column.** The registry has no explicit output-path field; mapping run_id→artifact required inference from `notes`/`slurm_job_id`. Adding a `artifact_path` column (and a concrete path for row 19) would make future audits deterministic.
4. **Row 16 SR-behavior-level pending.** Note says "SR pending manifest" while `ae_gens_for_scoring_strongreject_summary.json` exists; if the behavior-level SR ASR has since been computed, update the row from the gemini-only 0.560.

---

## 5-line status summary

1. Audited all 29 registry rows: 28 PASS, 0 FAIL, 1 CANT-VERIFY (phase16_crossmodel_lengthtest — no dedicated artifact, `slurm_job_id=none`, reuses Phase-4X outputs).
2. Every cited artifact path exists on disk except the one CANT-VERIFY row; no missing/broken paths elsewhere.
3. All rows with a populated ASR column recompute exactly to `n_success/n_total`; LOGO-AUC / causal-null rows correctly carry no ASR.
4. Every `code_commit` is post the 2026-07-19 placement fix (the whole pipeline began 2026-07-21); no v1 placement-bug rows. HEAD=`f646dd4`, branch `main`.
5. Invariants verified: dev_25↔heldout_495 disjoint (0 overlap), phase3 suffix_placement=user, THINK_START_IN_PREFILL_BY_FAMILY + Phi-4 `<think>\n` fixes present, StrongREJECT threshold 0.5 consistent. Only note-level flags: literal `HEAD` commits (rows 21–29) and external_transfer note 0.737 vs column 84/99=0.848.

---

## Integrity finding (2026-07-26 bug-hunt) — stage-4 `enable_thinking=False` silent no-op — severity MISLABELS

**Bug:** `poc_stage4/qwen3_model.py::format_prompts` passed the `enable_thinking` kwarg to
`apply_chat_template` ONLY when True; `=False` omitted it, so Qwen3's thinking-ON template default silently
applied. Qwen3-only (Gemma reuses the wrapper but its template ignores the kwarg → `except TypeError`
fallback → no-op either way, so Gemma runs are unaffected). **FIXED 2026-07-26** (pass the flag explicitly
for both values; `tests/test_qwen3_format_prompts.py` 4/4).

**Blast radius (agent-assessed, config/code/docs only):**
- **Affected artifacts** (configured `ENABLE_THINKING=false`, actually ran thinking-ON):
  `outputs/stage4/qwen3-14b/{refusal_direction*, refusal_dampening*, direction_subspace* over the base
  refusal_direction input}`. Their metadata carries `"enable_thinking": false` but they were computed
  thinking-ON — the intended EOI / empty-`<think>` extraction position was never realized (captured at
  `assistant\n` instead).
- **NOT affected:** the entire phase5–9 pipeline (the **predictive-but-not-causal HEADLINE**), all
  `stage4a1_*` variant extractors (hardcode `enable_thinking=True`), `stage4_standard_rd_replication`
  (explicit True), and all Gemma stage-4 runs.

**Severity = MISLABELS (invalidates NO reported number).** No headline depends on the affected outputs; the
affected stage-4 refusal-direction pipeline's own reported conclusion is a robust **negative** (0/160
causal candidates survived) that holds regardless of think-condition, and its reports self-describe as
`enable_thinking=True`. The only analysis the bug would actually corrupt — an explicit thinking-OFF vs
thinking-ON comparison — was **never run** (listed as future work only).

**Remediation (low priority):** before any future think-vs-no-think comparison, either correct the
`enable_thinking` metadata field in the affected artifacts or re-extract the EOI direction under genuine
thinking-OFF (now possible post-fix). Not required for any current conclusion.
