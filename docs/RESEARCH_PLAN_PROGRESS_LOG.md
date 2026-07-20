# Research Plan — Progress Log

Tracks execution of `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` (the plan; **do not edit the plan**).
Driven by a 30-min `/loop` (cron `e2698d62`). Every entry cites concrete paths.

Working rules (from the plan's operational section):
- ≤6 SLURM runs at once; reuse known-good configs; anything PENDING >30m → cancel & resubmit.
- No unnecessary code; no duplication (reuse existing scripts/artifacts).
- After every change, fan out a bug-check subagent.
- Document every step here with path references.

Legend: ✅ done · 🔄 in progress · ⏳ queued · ⛔ blocked

---

## Phase status overview
| Phase | Title | Status |
|-------|-------|--------|
| 0 | Freeze current state | 🔄 |
| 1 | Redesign dataset split | ✅ (external_transfer deferred to Ph15) |
| 2 | Freeze evaluation protocol | ⏳ |
| 3 | Reproduce baselines in TROPT | ⏳ |
| 4 | Real attack baseline (CoT Hijacking) | ⏳ |
| 5+ | Mechanistic / objectives / transfer | ⏳ |

---

## Iteration log

### 2026-07-21 — Iteration 1 (loop start)
**Setup**
- Scheduled recurring loop: cron `e2698d62`, `*/30 * * * *` (session-only, 7-day expiry).
- Repo orientation. Key reusable assets identified (avoid duplication):
  - Behaviors + CoT targets: `outputs/stage_gcg_full/advbench_cot_full520_manifest.jsonl` (520 rows).
  - Category taxonomy: `scripts/gcg_advbench_llm_taxonomy.py` → `categorize()` (15 cats).
  - Canonical historical dev-25 rows: `scripts/detector_extended_audit.py:32` (`DEV_25_ADVBENCH_ROWS`).
  - Real attack ref impl: `Chain_of_Thought_Hijacking/Hijacking/` (API-based: GPT/Gemini/Claude/Grok).
  - GCG ref: `llm-attacks/`; refusal-direction ref: `Chain_of_Thought_Hijacking/refusal_direction/`.
  - StrongREJECT judge: `strong_reject/`, `scripts/paper_asr.py`, `scripts/staged_asr_rerank.py`.
  - Master synthesis of prior GCG work: `docs/GCG_JULY2026_MASTER_LOG.md` (triple-verified).

**Phase 1 — dataset split ✅**
- New script (no existing equivalent): `scripts/build_dataset_split.py`.
  Reuses the full-520 manifest + taxonomy; reuses the exact historical dev-25 so the
  held-out 495 stays genuinely unseen (plan §5.1 hard criterion).
- Outputs (plan §5.4 deliverables):
  - `data/manifests/dev_25.csv`, `dev_train_20.csv`, `dev_val_5.csv`, `heldout_495.csv`
  - `data/manifests/split_audit.md`
- Disjointness verified: exact-text overlap = 0, target-prefix overlap = 0,
  cross-split lexical near-dup clusters (Jaccard≥0.85) = 0.
- Dev-25 spans 11 categories; `dev_val_5` = {0001 cyber, 0021 violent, 0063 misinfo,
  0084 identity-theft, 0105 fraud} — one per top-5 category.
- Deferred (documented in split_audit.md): embedding-based semantic near-dup check
  (needs a sentence model); `external_transfer.csv` → Phase 15 (licensing/download decision).

**Phase 0 — freeze current state 🔄**
- `research_snapshots/2026-07-post-mahmood-meeting/` created with `code_commit.txt`
  (records HEAD; artifacts preserved in-place under git rather than byte-copied to
  avoid multi-GB duplication).
- `docs/CURRENT_STATE_AUDIT.md` — facts/hypotheses table (plan §4.4), sourced from
  `docs/GCG_JULY2026_MASTER_LOG.md`.

**Next iterations (in order)**
- Finish Phase 0 audit cross-checks; then Phase 2 (freeze eval protocol: greedy config,
  prefix-match metric, judge validation, experiment registry) — all CPU/API, no GPU.
- Phase 3 (TROPT reproduction) needs TROPT installed — check availability before coding.
