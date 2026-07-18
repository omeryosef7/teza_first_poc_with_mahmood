# GCG Suffix-Placement Bug — Fix, Re-run & Documentation Plan (2026-07-19)

**Status:** PLAN (nothing executed yet). Prepared via a 4-subagent fan-out (rerun-inventory, fix-design, SLURM-logistics, doc-mapping) + direct verification.

**The bug (proven):** GCG *optimizes* the adversarial suffix in the **assistant turn** (`suffix_token_manager.py::build_suffix_spans` templates the instruction alone with `add_generation_prompt=True`, then appends `suffix + target`), but *evaluates* it in the **user turn** (`evaluate_optimized_suffixes.py:86`, `user_content = instruction + suffix_str`). Rendered proof (real Qwen3 tokenizer):
- OPT: `…<|im_start|>assistant\n {SUFFIX}<think>…` → suffix in assistant turn
- EVAL: `…user\n{instr} {SUFFIX}<|im_end|>\n<|im_start|>assistant\n` → suffix in user turn

Every optimized suffix was trained against a prompt the evaluator never uses. This confounds **all GCG-optimization-dependent ASR numbers** and is the leading root-cause hypothesis for the project's central "loss ≠ ASR / GCG net-negative" finding. It does **not** touch the detector AUC, the CoT classifier, the taxonomy, the Track-2 causal test, or the baseline conditions (those are already user-turn or suffix-independent).

**Guiding principles:**
1. **Non-destructive** — all v1 outputs, scripts, and CSVs stay byte-untouched. v2 lands in a parallel tree.
2. **Provenance-preserving** — the fix is gated by a config flag captured in `config_hash`, so v1 is exactly reproducible and v1/v2 can never cross-contaminate.
3. **SLURM rules** — no job dependencies, ≤6 concurrent, no PENDING tail, `--constraint=l40s`, exclude n-804/n-602/n-301, 8h/job, `/loop 30m` cadence.
4. **Gate before scale** — Tier 0 (one experiment) measures whether the fix changes ASR at all before committing ~187 GPU-h.

---

## PART A — The Code Fix

### A.1 What changes conceptually
Relocate the optimizer's suffix from the assistant turn to the **user turn**, so the optimized prompt is byte-identical to what eval feeds:
`<|im_start|>user\n{instruction}{suffix}<|im_end|>\n<|im_start|>assistant\n{target}`.
Eval is already correct; **only the optimizer side changes.**

### A.2 The core difficulty & the robust locator
Putting the suffix inside the user turn reintroduces the BPE-boundary-merge problem the current (buggy) code sidestepped by ID-concatenation after the assistant header. Recommended locator (validated by rendering with the real Qwen3-14B + Gemma4 tokenizers):

1. **Primary path — "render what eval renders, then locate":** build `prompt_ids = tok(apply_chat_template(instruction + suffix_text))` (literally eval's prompt, guaranteed in-distribution), then `_find_subsequence(prompt_ids, suffix_ids)` to get `suffix_slice`. Rendering confirmed the suffix ids appear contiguously for round-trippable suffixes and this equals ID hand-assembly byte-for-byte.
2. **Fallback — ID hand-assembly with an in-distribution assertion:** for suffixes that BPE-merge at a boundary (letter-start suffix merging leftward), fall back to `header_ids + suffix_ids + trailer_ids`, assert the neutral round-trip reproduces `apply_chat_template` byte-for-byte, and emit a warning. This exact boundary slippage already exists in both the current optimizer and eval, so the fix does not introduce it; it fails **loudly**, never silently.
3. Header/trailer are **derived from `apply_chat_template`**, never hardcoded (Gemma4 injects `<bos>` + a system turn; Qwen3 does not — hardcoding would corrupt Gemma4).

### A.3 The one structural break
`SuffixSpans.verify()` currently asserts `suffix_slice.stop == target_slice.start` (suffix immediately precedes target — true only for assistant placement). Relax to `suffix_slice.stop <= target_slice.start` (a template trailer `<|im_end|>\n<assistant hdr>` now sits between suffix and target). The suffix-content, target-content, and `loss_slice == slice(target_start-1, target_stop-1)` assertions are unchanged and still hold.

### A.4 Config flag (provenance isolation)
Add `suffix_placement: str = "user"` to **`GCGHyperparams`** (`config.py`) — placing it inside the hashed sub-dict means v1 (assistant) and v2 (user) get different `config_hash`, so old checkpoints/caches cannot resume into new runs (they abort safely rather than corrupt).
- `"user"` = the fix (default for all new work).
- `"assistant"` = byte-exact reproduction of the old buggy layout (for A/B and v1 replay).
- `run_optimization.py`: add `--suffix-placement {user,assistant}` (default `user`) and write it into `CONFIG.json`.
- **Pin legacy `run_gcg_full_*.slurm` to `--suffix-placement assistant`** only if ever re-run; we otherwise leave them untouched and create new `_userfix.slurm` copies.

### A.5 Files to change (none edited yet) + downstream-consumer verdicts
| File | Change |
|---|---|
| `suffix_token_manager.py` | New "user" path in `build_suffix_spans`; 2 helpers (`_split_user_turn`, `_assert_in_distribution`); relax `verify()` adjacency `==`→`<=` |
| `config.py` | `GCGHyperparams.suffix_placement="user"` |
| `run_optimization.py` | `--suffix-placement` CLI arg → thread into `GCGHyperparams`; record in CONFIG.json |
| `gcg_optimizer.py` | Pass the flag to all ~12 `build_suffix_spans(...)` call sites (476,500,531,559,598,650,686,735,802,830,864,903) — cleanest via a local `_spans(...)` partial |
| `reference_cache.py` / `build_reference_cache.py` | Thread the flag into `build_and_store`/`get_or_build` so repr positions align |
| `tests/test_suffix_manager.py` | Add fix unit tests (below) |

**Position-agnostic — NO change needed** (all slice-based): `_token_gradients` embed stitching, CE loss over `loss_slice`, `_evaluate_candidates`/`composite_loss`, `replace_suffix`, quick-ASR gen prompt (`input_ids[:target_slice.start]`), channel-token logging, `evaluate_optimized_suffixes.locate_positions` (already user-turn), all `analyze_*`/PARETO/FINAL logs. repr/refusal positions recompute automatically from `suffix_slice.stop` and stay consistent as long as cache and optimizer share the flag (stale v1 caches are auto-rejected by the cache key).

### A.6 Verification of the fix
**Unit (no GPU, `poc_stage2` env):**
1. In-distribution equality: `build_suffix_spans(...,"user").input_ids[:target_slice.start] == tok(apply_chat_template(instruction+suffix))` for round-trippable suffixes, Qwen3 + Gemma4, think on/off.
2. Span correctness: `input_ids[suffix_slice]==suffix_ids`, `input_ids[target_slice]==target_ids`, `loss_slice==slice(target_start-1,target_stop-1)`, suffix strictly precedes the turn-closing token.
3. Fallback path: a boundary-merge suffix takes the hand-assembly branch, warns, still passes `verify()`.
4. Legacy parity: `"assistant"` reproduces current `input_ids` byte-for-byte (regression guard).

**Behavioral (Tier 0, GPU):** re-optimize 5A (25 behaviors) with `--suffix-placement user` into a v2 dir, eval it, compare to v1's 10.7%. This is both the fix's behavioral proof and the decision gate for the rest of the campaign.

---

## PART B — Re-run Campaign

### B.1 Output scheme (non-destructive) — **Option A: parallel root**
All v2 runs write to `outputs/stage_gcg_full_v2_userfix/<same_run_name>/`. v1 tree is never touched.
- `build_gcg_source_of_truth.py`: add a 3-line env override (`BASE`, CSV path L237, MD path L257) defaulting to v1 values, then emit a **separate** `GCG_PHASE4_7_SOURCE_OF_TRUTH_v2.csv` / `_v2.md` via `GCG_BASE=outputs/stage_gcg_full_v2_userfix …`.
- `compute_canonical_asr.py` needs no change (takes explicit `--runs`).

### B.2 Scope: 46 optimization runs (~187 GPU-h) + ~20 eval-only runs
Full inventory (run dir · label · type · model · seed · key params · measured v1 wall-h) is in **Appendix 1**. Two-phase structure per experiment: **re-optimize** (produces new `FINAL_CANDIDATES.jsonl`), then **re-eval** the consumers. Dependency DAG (Appendix 2) — the eval-only runs that consume a re-optimized suffix:
- `5A cot_target` → 7A (520 seeded+unseeded, ~11 shard evals) + Track-2 causal intervention
- `8_rd_lambda03` → 9A(+unseeded); `7b_seed45` → 9B(+unseeded); `9c_seed45` → 9C(+unseeded)
- `gemma4_9g_emptythink_L31` → 10A + 10G transfer; `qwen3_weighted` → 4F + 4E transfer

### B.3 Tiers & the decision gate
| Tier | Scope | Opt jobs | Opt GPU-h |
|---|---|---|---|
| **0 (GATE)** | 5A re-opt (25 beh) + eval — *does the fix change ASR at all?* | 1 | 4.2 |
| **1** | Headlines: Standard GCG, 5A(=T0), Gemma4-4C, 7B-43/44/45, Phase8 λ=0.3(+seed43) → then 7A/9B/4F evals | 8 (7 new) | 31.6 |
| **2** | Sprint-3 scaling + ablations: 9C-opt, 9E, 9G-Q×4, 9D/9D2, 9G-G×3, 10B×3, 10C×3, Phase8 layer20/30/λ3, 6B2, track4/4b, 6A-Q/6A-G/6B/6C/7C → 9A/9C/10A evals | 28 | 107.3 |
| **3** | Low-value negatives: 5B, 5C, multimodel, 10D, 10E, 4A, 4B, DeepSeek×2, early repr×6 → transfers, Track-2 | ~10 | 47.7 |

**GATE rule:** after Tier 0, compare v2 vs v1 5A ASR. If materially higher (fix works, results were confounded) → run Tiers 1–3. If ≈unchanged → the bug, though real, did not drive the numbers; document that in §13 and **stop** (saving ~180 GPU-h). This is the "smart" part of the plan.

### B.4 SLURM script strategy — `*_userfix.slurm` copies
`cp` each needed script to `*_userfix.slurm` and make exactly 3–4 mechanical edits (never touch originals):
1. `RUN_DIR`/`EVAL_RUN_DIR`/`SOURCE_RUN_DIR` → the v2 root.
2. Add `--suffix-placement user` to the `run_optimization` call (opt scripts only).
3. Fix the stale `#SBATCH --nodelist` (current scripts list broken `n-804` and non-existent `t-806`) → `n-801,n-802,n-803,n-805`, add `--constraint=l40s`.
4. Add a grep-able banner: `echo "SUFFIX_PLACEMENT: user (FIXED)"`.

Generic eval (`run_gcg_full_free_generation.slurm`) already reads `RUN_DIR` from env — reusable via `--export=ALL,RUN_DIR=…v2…`. The hardcoded eval scripts (`run_gcg_full_7a_5a_full520.slurm`, `run_gcg_full_9a_lambda03_full520.slurm`, etc.) need edited copies.

### B.5 Wave schedule — rolling 6-slot scheduler under `/loop 30m`
No fixed batches; a rolling scheduler enforces the opt→eval ordering manually (the no-dependency rule):
- **t=0:** submit first ≤6 opt jobs, Tier 0 first.
- **Each `/loop` cycle:** (a) reap finished jobs; (b) verify their gate file; (c) `free = 6 − RUNNING`; submit ≤`free` new jobs, **preferring verified evals over new opts** so the pipeline drains; (d) if any job goes PENDING, `scancel` it (no-pending-tail rule).
- **Gate files:** opt→eval eligible when `…/FINAL_CANDIDATES.jsonl` exists **and** `CONFIG.json` shows `suffix_placement=user`. Eval done: 25-beh → all condition×seed rows present; 520-beh → rowcount ≥6200 or `DONE` sentinel (needs ~4 resubmitted passes).
- **Calendar estimate:** opt phase ≈ 30 jobs / 6 slots × ~8h ≈ 40h wall, with evals overlapping into freed slots; 520-beh evals dominate the tail. End-to-end **~3.5–5 days** (~7–10 acting `/loop` cycles).

### B.6 Guardrails (every cycle)
- **Fixed path ran:** `CONFIG.json.gcg.suffix_placement == "user"` (load-bearing) + banner grep + run-dir path contains `stage_gcg_full_v2_userfix`.
- **≤6 concurrent / no PENDING tail:** `squeue -u $USER -h -t RUNNING | wc -l` ≤6; `-t PENDING` empty; no job on `n-804|n-602|n-301`.
- **Aggregation integrity:** after all `DONE`, run v2 aggregator, diff v2 CSV vs v1 (v1 untouched; every v2 row under the v2 root; counts match).

### B.7 NOT affected — no re-run needed
Refusal-direction vectors (`refusal_direction_*.json`, suffix-independent), `ADVBENCH_LLM_TAXONOMY.json`, the CoT-mechanism classifier code, all baseline conditions (`neutral_control`/`task_only`/`random_spaces` — already user-turn; recomputed free as an eval byproduct), manifests & reference caches (suffix-independent; caches rebuild cheaply). **Affected but low-priority:** the GCG detector (trained on assistant-turn hidden states from buggy Standard-GCG — re-derive after Tier 1) and Track-2 (consumes 5A — re-run in Tier 3).

---

## PART C — Documentation Plan (in `GCG_JULY2026_MASTER_LOG.md`)

Two parts, per the request: (1) inline `⚠ audit note` at **every** place a bug affects a claim, and (2) a new dedicated section.

### C.1 Inline annotations — full anchor map
The complete Bug→Section→verbatim-quote→annotation map (23 B1 anchors + B2–B9) is in **Appendix 3**. Every ASR-bearing sentence/table row in §1, §3, §4, §5, §7, §8 gets a `⚠ audit note (§13/B1)` marking it confounded/provisional. Special call-out: **§4's "loss does not predict ASR" (line ~101)** gets a `⚠ CANDIDATE ROOT CAUSE` note — the placement bug is the leading explanation for that finding.

### C.2 New section — `## 13. Code-Correctness Audit (2026-07-19) & Re-run Campaign`
Insert after §12 (before "Verification Status"). Skeleton:
- **13.1 Audit method** — 9-subagent fan-out; CONFIRMED vs PLAUSIBLE; relation to the 07-13 numbers-audit (which couldn't catch this — it checked values against artifacts that already carried the bug).
- **13.2 Classified bug table** — one row per B1–B9: severity · defect · status · claims affected · fix · re-run tier.
- **13.3 The suffix-placement bug (B1) — proof** — side-by-side rendered opt vs eval prompts; why it confounds optimization-dependent ASR but leaves AUC/baselines intact.
- **13.4 Fix design & config flag** — Part A summary.
- **13.5 Tiered re-run plan & status** — Part B tiers + live QUEUED/RUNNING/DONE + job IDs.
- **13.6 v1-vs-v2 results comparison** — table (Claim · §ref · v1 ASR · v2 ASR · Δ · conclusion holds?), filled as re-runs complete.
- **13.7 Non-B1 fixes & residual caveats** — B2 baseline dedup, B3 judge-noise tolerance, B4 as-designed note, B5–B9.

### C.3 Cross-references to add
- **§1 Exec Summary:** lead caveat bullet — all GCG-optimization-dependent ASR under re-run; uplift directions & AUC expected to survive; magnitudes provisional (§13).
- **§10 Known Discrepancies:** new row 17 pointing to §13.
- **§12 Provenance Index:** `P-13.*` rows + a `[AUDIT-2026-07-19]` tag in the legend.
- **Verification Status:** new "Code-correctness audit (2026-07-19)" paragraph distinguishing it from passes 1–4 (code-path audit, not number-recompute).
- **§6:** forward pointer noting the 07-13 audit couldn't catch a code-level bug.

---

## PART D — Execution Order & Decision Gates

**Phase 0 — Implement (no GPU):** apply the A.5 code changes → run A.6 unit tests → add the 3-line aggregator env override → create Tier-0/1 `_userfix.slurm` copies. Land the **inline doc annotations (C.1) + §13 skeleton (C.2)** now, since B1–B9 are already proven (the fix/results columns fill in later).

**Phase 1 — Tier 0 GATE:** submit 5A `_userfix` opt → verify CONFIG flag → eval → record v2 vs v1 5A ASR in §13.6. **Decide:** proceed (fix matters) or stop (fix immaterial).

**Phase 2 — Tiers 1→3** (if gate passes): rolling 6-slot scheduler under `/loop 30m`, opt-then-eval, guardrails every cycle; update §13.5 status + §13.6 comparison as runs finish.

**Phase 3 — Close-out:** v2 source-of-truth CSV; fill §13.6; convert each inline `⚠ provisional` note to the final v2 number where the conclusion holds, or a correction where it doesn't; update memory.

---

## Appendix 1 — Full run inventory
See subagent "rerun-inventory" output (46 OPT + ~20 EVAL, per-run params & measured wall-h). Key headline roots: `gcg_full_qwen3_cot_target` (5A), `_8_rd_lambda03` (Phase 8), `_7b_seed45`, `_weighted` (Standard), `gemma4_weighted` (4C), `gemma4_9g_emptythink_L31` (Gemma4 best).

## Appendix 2 — Dependency DAG (opt → eval)
`5A → {7A seeded/unseeded shards, Track-2}` · `8_rd_lambda03 → 9A(+unseeded)` · `7b_seed45 → 9B(+unseeded)` · `9c_seed45 → 9C(+unseeded)` · `gemma4_9g_emptythink_L31 → {10A, 10G}` · `qwen3_weighted → {4F, 4E}`. All other OPT runs are self-contained (own 25/300-row eval in the same job).

## Appendix 3 — Full inline documentation anchor map (B1–B9)
See subagent "doc-mapping" output: 23 B1 anchors (§1 L19–25; §3 table L46–60, L71, L75, L77; §4 L87–101; §5 L114–121; §7.3–7.4 L161–172; §8.1–8.10 L184–256), plus B2 (§3 L42, §4 L92/L96), B3 (§8.5 L231, §4 L95/L96), B4 (§9 L272, §5 L121, §3 L75), B5 (§8.1 L185/L188, §1 L24), B6 (§3 L71), B7 (§3 L53), B8 (§4 L87, §1 L21), B9 (§8.4 L218, §8.5 L231) — each with verbatim quote + ready annotation text.
