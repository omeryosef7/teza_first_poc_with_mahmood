# Session handoff — `acbaec5b`, 2026-08-29

**For:** the concurrent Claude session (`f135d5e1`), any future session on this repo, and Omer.
**Branch:** `behavioral-causality-sprint`, HEAD **`95ad75b3`**, remote in sync.
**Loops: STOPPED.** The dynamic wakeup loop and the recurring 30-minute cron (`81d2d5ca`) are both
cancelled. `CronList` is empty. **Nothing of mine will fire again.**

---

## 1. State at handoff

| | |
|---|---|
| live SLURM jobs owned by this session | **0** |
| open items in `RESEARCH_HANDOFF.md` | **0 actionable** |
| `check_all.py` | **9/9** |
| commit-hook guard suite | **274 passed** (14 files) |
| full `pytest tests/` | **1444 passed, 7 skipped, 0 failed** |
| plan | complete; Phase 7 gate closed with no GCG/MAC objective built |

**Do not act on `sacct`.** It shows `740944`, `741053`, `741054` as RUNNING and `741057` as PENDING
with `Elapsed` past 19 days. These are **orphaned accounting rows** — `squeue -j` returns nothing and
`scontrol show job` says `Invalid job id specified`. Nothing is on a GPU. Section 18's
*"PENDING over 30 minutes → scancel and resubmit"* rule fires on them **spuriously**. See **C-102**.

---

## 2. The one scientific result this session produced

**C13's ASR leg was the phase's last unrun item. It ran (PR-39) and resolved.**

| gate | outcome |
|---|---|
| truncation (VOID precondition) | **cleared** — `frac_stop_length` 0.5813→**0.0000** baseline, 0.9125→**0.0187** and 0.9187→**0.0187** arms |
| baseline stability across caps | **not void** — 0.1688 → 0.1437, shift −0.0250, inside the 0.0521 margin |
| primary comparison at 640 | **PASS** — `pre12` 11/160 (Δ −0.0750, 12 rows, 1.45× margin), `pre10` 12/160 (Δ −0.0687, 11 rows, 1.33×) |

**Verdict: reinstated at ROW level, NOT established at cluster level.** On domain means `pre12` gives
p = 0.125 (capable test, floor 0.0156) and `pre10` p = 0.375 — **structurally incapable**, floor
0.0625 > 0.05, so no arrangement of its data could have cleared (**C-95**). The effect **halved** on
cap release (−0.1313 → −0.0750), so C-61's truncation mechanism contributed materially without
accounting for it. At 1.45×/1.33× it is **the thinnest quoted effect in the phase** (DR-20).

Artifacts: `score_behavior/c13{b,p12,p10}640_20260829_0825*`, `judge/c13j640_{b,p12,p10}_*_085325`.

---

## 3. Verifications a future session need not repeat

| what | result |
|---|---|
| **W1** (headline) recomputed from artifacts | all four settings reproduce exactly (DR-22) |
| **C9** (causal centrepiece) recomputed | four cells `{12,17,18,18}`, ×margin 1.44–2.16, exact (DR-25) |
| **R-171** model×bank 2×2 | complete from data on disk; **moderated by BOTH**; no GPU spent |
| bank provenance | **557 runs**, row-by-row `prompt_sha16`, **0 mismatches** (DR-23) |
| judge provenance | 121 runs from 08-26 clean; **one judge model corpus-wide** (DR-24) |
| intervention liveness | PR-1 contract holds; subset inequality with 42,426 slack (DR-20) |
| C-20 (below-band no-op) | re-confirmed incidentally — `q6bj_rescueL5` ref = `q6bj_knock` ref = 15 |

---

## 4. Warnings that cost real time

1. **A third writer is in this tree.** `reports/SPRINT_SUMMARY_2026-08-16_TO_08-26.md` was rewritten
   +7385 lines on 2026-08-29 (mtime 10:16, idle since). **Both Claude sessions established
   non-authorship by direct check.** `git stash list` still holds a third party's `WIP`.
   **Do not edit that file and do not pop the stash.** Escalated to Omer; unidentified. (**C-97**)
2. **`sacct` State is not liveness.** See §1. (**C-102**)
3. **A disk-quota event on 2026-08-29 truncated a `DONE`-marked run.**
   `d38beh_20260829_022027_2389958` is in `run_completeness_check.KNOWN_SHORT` — *must never be
   analysed*. Its `gens.jsonl` and `results.jsonl` **cross**: 16 rows scored with no generation, 4
   generated and never scored, and all 527 survivors internally consistent. **Loss is concentrated in
   11 of 38 domains**, and domain is the independence unit. (**R-172/R-174/R-175**)
4. **The memory directory is shared** between sessions and auto-loads. Write notes in the **third
   person**; quoted material keeps its pronouns **but must name whose voice it is**; attribution may
   be explicit, contextual or structural; and if a pronoun is incidental to a definition, **rephrase
   rather than label**. (**C-103/104/107/108**, note `feedback_shared_memory_directory.md`)

---

## 5. Guards added or hardened here

`tests/test_my_ledger_propagation.py`, `tests/test_my_cited_artifacts.py`,
`tests/test_cautioned_figures.py` — all three in `GUARD_TESTS`, installer and deployed hook
**identical, 14 files, sorted** (DR-21).

New this session: findings-propagation (a finding the claim ledger leans on must reach the
deliverable — **C-92**, six were missing); verdict-wire tests with isolation controls (**R-177**);
`TRUNCATED` and `DIVERGENT_FILES` tables pinning the quarantined run's arithmetic and its crossing
id-sets; `C13_CLUSTER` pinning C13's cluster figures against an independent implementation (**R-179**).

---

## 6. Durable memory notes touched

`feedback_matcher_scope_bug_class` (new), `feedback_sacct_orphaned_state` (new),
`feedback_shared_memory_directory` (new), `feedback_universal_quantifier_sweep` and
`feedback_disagreeing_counts_triage` (peer's, contributed to), `project_behavioral_causality_phase`
(updated — the two bank blockers are **closed**, not open).

---

## 7. Honest summary of what this session got wrong

**22 corrections against my own work (C-92 … C-113).** The dominant class was **field, filter and
matcher selection — 8 of 16 instances**, not computation. Notable: I withdrew a claim that a cell was
missing when it was in my own tree under a differently-named arm (**C-99**); I published a universal
that was **false when written** inside the correction about asserting things without checking
(**C-109**); and I twice described a first-hit stop as a completed sweep (**C-110/C-111**).

Every claim either session made about the *shape* of its own past errors was withdrawn or corrected
once someone counted. The one procedural claim that survived: **when two numbers disagree, ask why
before concluding the other party was sloppy** — it rescued a correct result twice.
