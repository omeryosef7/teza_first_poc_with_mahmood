# Handoff — session `f135d5e1` (Omer's loop), closed 2026-08-29

**The `/loop` driving this session is STOPPED** (cron `ce4c48a4` deleted). Nothing of mine is
queued, running, or scheduled. This file is the record of what that session did, for whoever picks
the work up.

---

## 1. State of the sprint at handoff

| | |
|---|---|
| SLURM queue (mine) | **0 jobs**. Nothing pending, nothing to resubmit. |
| Runs awaiting judge/score | **none** |
| Guards | **9/9** (`check_all.py`) |
| Commit hook | **274 tests**, 14 guard-test files, list is sorted so hook order == `pytest tests/` order |
| Full suite | **1444 passed, 7 skipped, 0 failed** |
| Remote | in sync on `behavioral-causality-sprint` |
| Claim ledger | **zero actionable items** |
| Phase 7 gate | **CLOSED — no GCG/MAC objective was built, and none should be without a passing gate** |

All four plan items the loop named were verified **against artifacts, not from memory**:
`cap_natural_experiment.py` + Phase 0.3 `capNE_`/`capC_` runs present; knockout cap≥640 at exactly
**10 run dirs** (5 Llama populations × A and C); Phase 6's `{0,1,2,4,8,16}` ladder complete across
all three banks; Phase 2 at 20 `p2_`/`q2_` dirs.

⚠ **Phase 6's endpoints are 12-row cells.** `basket_gun` and `ticket_bomb` carry 12 rows at n=0 and
12 at n=16 against 336–528 per middle dose — a 28–44× gap. The recorded *"n=0 is 0/12 on all three
banks"* was never overstated, but **the same 12-row weight sits under the n=16 end of the
non-monotonic ladder**. Carry that caveat wherever the ladder's shape is quoted.

## 2. Substantive findings this session

- **The quarantined run `d38beh_20260829_022027_2389958` must never be analysed.** Corruption is in
  *which rows exist*, not row content: 16 results rows scored with no generation, 4 generations
  never scored, and all 527 surviving intersection rows agree field-for-field. Of the 81 designed
  rows absent, only 20 are one-sided — **61 are in neither file**, invisible to any file comparison.
  Four of the 11 damaged domains are untouched by the divergence entirely.
- **`pre10`'s cluster test is STRUCTURALLY INCAPABLE, not a null.** With k=5 informative clusters the
  attainable two-sided floor is 0.0625 > α, so no arrangement of the data could have cleared.
  Verified three independent ways (closed form, 2^k enumeration, and a peer's scipy run).
- **Judge-MODEL heterogeneity is eliminated corpus-wide** (644 judge runs, 22,256 stamped rows, one
  model). **Judge-SESSION heterogeneity is not**: 6.5–7.0% of rows flip between invocations on
  byte-identical text. Compared arms must be judged in ONE invocation. *An identical aggregate is not
  evidence that the same rows were scored the same way* — `ticket_bomb` A totalled 27 both times with
  8 rows disagreeing underneath.

## 3. Guards added or fixed (all mutation-tested)

- `run_completeness_check` — **check 3, file agreement**, documented as the *complement* of the
  row-count check and never as completeness. Fires on exactly one run corpus-wide. Also splits
  *"not a run"* from *"could not tell"*: no config **and** no rows is a non-run (counted, printed);
  no config **with** rows is `UNCHECKABLE`, a defect.
- `canonical_figures` — **was not wired.** An unresolvable artifact key printed the figure on a
  normal-looking line and returned 0, because `_artifact_value` collapses missing-file, bad-key and
  non-numeric into one silent skip. Fixed; the message now names the figure.
- `tests/test_guard_wiring.py` (new, in the hook) — probes **every** guard's *verdict*, not just its
  scanner, with a passing clean control for each. 8 of 9 demonstrated wired here; the 9th
  (`cited_artifact_check`) was covered by the other session.
- `install_commit_guard.sh` — `GUARD_TESTS` **sorted** so hook order matches the suite's, every
  listed file must exist, and the **deployed** hook must carry every listed file. Pinned in
  `test_commit_guard.py`, which is itself now in the list.
- `clustered_stats.cluster_sign_test` — returns a **verdict**, not a p-value: `can_reach_alpha` is a
  field and `summary()` renders capability in the same string as the p. Pinned against an independent
  2^k enumeration.

## 4. Lessons worth inheriting (the ones that changed work, not the aphorisms)

1. **Testing the check is not testing the guard.** A mutant deleting `problems += fa_problems` left
   the check running, printing findings, and the exit code ignoring them — 20 tests still passed.
2. **A green hook is not a green suite.** File *order* differed between hook and `pytest tests/`;
   4 real failures passed the hook and failed the suite. Now structurally impossible.
3. **Any guard whose "no opinion" and "passed" states share an output line has that defect latent.**
4. **Computing a qualifier is not quoting it** — a p without its floor, a turnover without its n.
5. **When two counts disagree, ask why before assuming sloppiness.** Five instances this session,
   *every one* two correct measurements of different things. Triage: corpus → instrument → population.

Durable versions are in shared memory: `feedback_universal_quantifier_sweep.md`,
`feedback_disagreeing_counts_triage.md`, `feedback_sacct_orphaned_state.md`,
`feedback_shared_memory_directory.md`.

## 5. ⚠ Open items — NOT mine to close

1. **⛔ AN UNACCOUNTED WRITER IS IN THIS WORKING TREE — THREE SESSIONS HAVE NOW EACH RULED
   THEMSELVES OUT.** `reports/SPRINT_SUMMARY_2026-08-16_TO_08-26.md` received **+7,385 / −10 lines
   at 2026-08-29 10:16:32**, working-tree only, and has been idle since. It retitles the document
   and cites this session's commit hashes **38 times** and the other peer's **zero**; its §20–§45
   numbering matches no plan document here. Last *commit* to it is `8441bcd1`, 2026-08-26.

   Non-authorship established independently, each with evidence rather than assertion:

       this session (f135d5e1) ........ never opened the file; 0 commits of mine name it
       "Summary update from 16.8" ..... no commit of theirs names it; verified from their tree
       "Session summary with exact numbers" .. session opened this afternoon; the file was ALREADY
                                        modified at their first `git status`, and their earliest
                                        write anywhere is 15:25:50 against the file's 10:16:32
                                        mtime — verified here from both timestamps

   **So the writer is a FOURTH party and remains unidentified.** An earlier version of this handoff
   called it "a third writer"; that was written before the second peer session had been asked, and
   is corrected here. The stash stack additionally holds `stash@{0}: WIP on
   behavioral-causality-sprint: 3018852e`, disclaimed by all three sessions — **do not pop it.**

   **Escalated to the user by all three sessions. Do not edit that file, and do not add it to
   `canonical_figures.DELIVERABLES`** — gating it would refuse an unidentified party's commits with
   no way for them to learn why.
2. **Four W1 entries are worth adding to `canonical_figures`** once (1) is resolved. The numbers are
   pinnable as-is: judge summaries carry `refusal_rate` directly (`p4bj_A` = 0.05625 = 9/160 at
   `asr_by_arm/0.5/A_baseline/refusal_rate`).
3. **Two option-mass figures are unsourced.** The plan records 0.5695 / 0.1162 beside the
   `ticket_bomb` mapped-wins cell; a 48-combination exhaustive search reproduces neither. The **cell
   itself is sourced and correct** (45/48 across three baselines vs 15/48). Left as a stated negative
   rather than guessed at.
4. **`sacct` shows jobs 741053/741054 RUNNING and 741057 PENDING. They do not exist.** `scontrol`
   returns *Invalid job id*; these are orphaned accounting rows from 08-10. **Do not act on them** —
   the loop's "PENDING > 30 min → scancel and resubmit" rule fires on them spuriously.
