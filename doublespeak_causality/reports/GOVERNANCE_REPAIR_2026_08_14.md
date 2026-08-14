# GOVERNANCE REPAIR — 2026-08-14

Deliverable of Role-Probe sprint plan §4.2. Repairs the registry + deviation-log
lapse the 2026-08-14 audit found (registry stale since 2026-08-05, bug log since
2026-08-08 — the whole Asymmetry / Section 20 sprint unregistered).

Method: login-node only, no GPU, no data-content reads. Numbers are from
`scripts/update_registry.py`, direct CSV parse, and the seven-agent read-only
audit (`wf_7224d5d8-f29`). Sources: `RESEARCH_LOG_AUDIT_2026-08-14.md`,
`OWED_SUBMISSIONS.md`, immutable `RUNMETA.json`/`DONE.json` artifacts.

---

## 1. Output inventory

| Quantity | Value |
| --- | --- |
| Entries under `outputs/` | 606 (545 directories + 61 loose `.json`) |
| Hidden top-level markers (e.g. `.stage1_llama8b.COMPLETE`) | 18 (not counted in 606) |
| Directories with `RUNMETA.json` | 523 / 545 (96.0%) |
| Directories with `DONE.json` | 507 / 545 (93.0%) |
| Directories with a per-example `*.jsonl` | 371 / 545 (68.1%) |
| Directories with `RUNMETA + DONE + per-example + summary` | 182 / 545 (33.4%) |
| Directories with **no** provenance file at all | 10 |

**Provenance convention (local).** This repo uses exactly two provenance
filenames, flat inside each run dir: `RUNMETA.json` and `DONE.json`. There is
**no** `config.json`/`config.yaml` and **no** `manifest*.json` anywhere under
`outputs/` — config is embedded *inside* `RUNMETA.json` (keys include `script`,
`argv`, `git_commit`, `slurm_job_id`, `seed`, `split`, `dtype`, `model`,
`revision`, `off_by_one_note`, …). So the plan's "config + manifest as separate
files" (plan §3.7) is satisfied by RUNMETA embedding, not by standalone files;
the "complete all five separate files = 0" figure is an artifact of the
convention, not a defect. **Going forward** the new sprint will additionally emit
a standalone `manifest` reference per run (plan §3.7) to match the checklist
literally.

**The 10 no-provenance directories** (candidates for SUPERSEDED marking or
documentation, not deletion):
`asym_p1_reach_train_phismoke_gpua5000_20260812_010716_751402`,
`attn_retrieval_Llama-3.1-8B-Instruct_20260806_172234_728475`,
`…_728476`, `concept_phi`, `concept_qwen3`, `refusal_phi`, `refusal_qwen3`,
`gate7_firstcut`, `gate7_v3_conceptdirs`, `gate7_v3_randdirs`.
The last three (`gate7_*`) are the direction/config dirs behind the Gate-7 v3
matrix whose 20 per-seed run dirs are missing (see §4, B14); `concept_*` /
`refusal_*` are Phi/Qwen direction dirs. `phismoke` is a smoke run.

## 2. Registry repair

| | Before | After |
| --- | --- | --- |
| Registry data rows | 395 | **573** (+178) |
| Latest date | 2026-08-05 | 2026-08-14-era runs now present |
| `asym*` rows | 1 | **47** |
| On-disk dirs registered | 367 / 545 | **545 / 545 (100%)** |
| On-disk dirs NOT registered | 178 | **0** |

Method: `scripts/update_registry.py --apply` (purpose-built, idempotent, dry-run
by default, `.bak` written, existing rows never rewritten). Of 178 added rows,
168 carry a git commit, 150 COMPLETE, 2 INCOMPLETE, 1 EMPTY, 25 UNKNOWN. Re-run
after apply = **0 rows to add** (idempotency confirmed). `key_metric`/`value`
left blank by design (cannot be derived without interpreting a result).

## 3. Deviation-log repair

`BUG_AND_DEVIATION_LOG.md` extended from the 2026-08-08 Gate-7 entry with a
backfill block **B6–B18 + V1** covering the 2026-08-08→14 window. Each required
item from plan §4.2 is captured:

| Plan §4.2 required item | Entry |
| --- | --- |
| GCG candidate-selection bug | **B6** |
| v1 leakage | **B7** |
| refusal-layer indexing bug | **B8** |
| test-selected continuous dose | **B12** |
| missing/pruned GCG raw directories | **B14** |
| threshold conflict | **B13** (resolved for new work) |
| known Section 20 deviations | **B15** (judge-flip), plus §5 below |
| stale/superseded claims (2026-08-14 audit) | **B14, B15, B17**; full list in `RESEARCH_LOG_AUDIT_2026-08-14.md` A1–A17 |

Additional backfilled: **B9/B10** (absolute-position GCG defects D1/D2 — our
recurring bug class), **B11** (D3 scope-matched arm, still open = Phase 6),
**B16** (Phi concept half missing = Phase 7), **B17** (L18 cross-distribution
fit), **B18** (the lapse itself), **V1** (code-review file folded into plan).

The prior sprint's own execution log (`ASYMMETRY_SPRINT_EXECUTION_LOG.md`)
already recorded a further ~15 in-sprint self-corrections (BUG A/B/C, the
single-seed Gate-E retraction, the covariance-rank-1 control, etc.). These are
cited in the audit and are not re-transcribed here — they were logged *somewhere*
immutable at the time; the failure was that they never reached the top-level bug
log. B18 records that meta-failure.

## 4. Reproducibility classification of headline claims

From the audit's artifact-level recompute (`RESEARCH_LOG_AUDIT_2026-08-14.md`):

**RAW-REPRODUCIBLE** (recomputable from committed per-example artifacts):
- Gate-A/B/C reachability (`asym_p1_reach_train/test/*/ANALYSIS.json`, `eps_scan.jsonl`).
- Refusal-ablation behavioral ΔASR at bf16/8-bit/4-bit (`behav_refusal_clearharm_asweep*`).
- §20.7 seed-42 objective curve (`asym_p207_objective_curve_seed42_FINAL37.json`, n=37, `interim:false`).
- §20.1 CE + soft-prompt ASR (`asym_p201_ce_scores.json`, `asym_p201_softprompt_asr.json`).
- §20.4 equivalence pass-2 (`asym_p204_equivalence_pass2.json`, `provisional:false`).
- P6 Jacobian readout (`p6_predicts_behavior_clearharm.json`).

**SUMMARY-ONLY** (survive via committed `.json`/`.md` summaries; raw per-example
dirs pruned — cite as such, do not re-derive):
- **Gate-7 v3 attack-objective matrix** — 20/20 per-seed run dirs missing (B14).
- **Gate-E position-corrected discrete** (+0.009) and **λ=10 probe** — heldout-ASR
  dirs pruned (B14).

**REPORT-ONLY** (prose/`.md` only, no machine artifact):
- §20.2 modality-specific partial correlations (no `asym_p202` artifact).
- §5.8 per-split refusal-projection AUCs (JSON stores pooled only).
- §5.9 token-0 separation AUC (summary.json has no AUC field).

**DEAD PATHS** (cited but absent): `configs/manifests/phase9b_gcg_v3.json`
(§25 index), `configs/manifests/phase9b_v3.json` — `configs/manifests/` holds 8
files, none a v3 GCG manifest. Logged B14-adjacent; the new sprint's manifest
(below) is the committed replacement going forward.

## 5. Section 20 state (reconciled against artifacts, not prose)

Per `OWED_SUBMISSIONS.md` (current as of 2026-08-14 19:45) and the SLURM
reconcile:

| §20 item | State |
| --- | --- |
| 20.1 (78% CE cost) | RAW; **μ sweep NOT run** — blocks paper use (B15-adjacent, plan §15.2) |
| 20.2 | REPORT-ONLY (no artifact) |
| 20.3 | RAW (`asym_p203_*`) |
| 20.4 | pass-2 RAW, `provisional:false`; §20.6 route unreachable (corpus 179) |
| 20.5 | provisional pool result, **no randtok floor, single-pass judging** (plan §15.4) |
| 20.7 | **seed 42 COMPLETE 37/37, 200→600 NULL** (p=0.252); seeds 43/44 running now |
| 20.6 / 20.9 | blocked by 179-corpus ceiling |
| 2000-step point | deferred; call waits on seed 43 → 37/37 |

**Live jobs (6, at cap):** all `gcg_perprompt` = §20.7/§7.5 per-prompt GCG,
ARM=vanilla, 600 steps, 3090s — seed 43 shards 2,3 (757662, 757672) and seed 44
shards 0,1,2,3 (757697, 757709, 757711, 757741). **All shards of all seeds
submitted; no half-launched set; nothing to relaunch.** Nothing cancelled, no
duplicates.

## 6. Gate 0 status

| §4 Gate 0 requirement | Status |
| --- | --- |
| Current jobs reconciled | ✅ §5 above |
| Threshold contract frozen | ✅ B13 + manifest (score ≥ 0.5, new work) |
| Train/dev/holdout policy explicit | ✅ manifest (v3 leakage-0; fresh holdout for confirmatory) |
| Registry / deviation logs current | ✅ §2, §3 (545/545 registered; B6–B18 logged) |
| New manifest committed | ⏳ `configs/manifests/role_probe_sprint_v1.json` (this commit) |

**GPU science remains blocked** independent of Gate 0: 6/6 SLURM jobs = at the
project concurrency cap. First free slot is the earliest a Phase-0-clean GPU job
(the §2A.5 upstream sanity reproduction) can launch.
