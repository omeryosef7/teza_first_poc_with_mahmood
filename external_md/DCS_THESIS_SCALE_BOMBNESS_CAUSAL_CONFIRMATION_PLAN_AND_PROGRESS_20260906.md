# DCS THESIS-SCALE BOMBNESS CAUSAL CONFIRMATION — PLAN AND PROGRESS

**Opened:** 2026-09-06 (first entries land 2026-09-07 local)
**Branch:** `behavioral-causality-sprint`
**Phase-opening HEAD:** `b80db84d`
**Mandate (frozen, verbatim):** `external_md/DCS_THESIS_SCALE_MANDATE_20260906.md`
**Namespace:** continues DCS. Preregistrations resume at **PR-046**; results at **R-098**;
corrections at **C-072**; audits at **A-034**; blockers at **B-xxx**; human questions
carry forward **Q-001..Q-005** and add **Q-006+**.

---

## HOW TO READ THIS FILE

This log is **append-only**. Entries are never rewritten. When an entry turns out to be
wrong, a later `C-xxx` correction says so and the original stays where it is, marked with a
forward pointer. A reader who has never seen the session should be able to reconstruct what
we believe and why from this file alone.

Every entry carries a timestamp, the commit it was written at, and the artifacts it rests on.

Verdict vocabulary, used strictly:

| verdict | meaning |
|---|---|
| **CONFIRMED** | a preregistered primary statistic cleared its preregistered gate on its preregistered population |
| **NEGATIVE** | a preregistered primary statistic failed its gate, *and* the design had power to detect the effect had it existed |
| **CANNOT ANSWER** | the design could not have answered the question either way — underpowered, degenerate instrument, or the read site could not physically see the intervention. **This is not a null.** |
| **VOID** | the run did not execute the design it claimed to (wrong script, wrong bank, silent no-op, dead hook) |
| **PRELIMINARY** | a real observation on a population too small or too misaligned to defend |

---

# A. CURRENT SCIENTIFIC TRUTH

*(populated at the close of PHASE 1 — see entry `A-034` below. Until then this section is
deliberately empty rather than inherited, because the whole point of PHASE 1 is to re-derive
it from artifacts instead of from prose.)*

# B. CLAIMS THAT ARE ONLY PRELIMINARY BECAUSE OF SMALL / MISALIGNED DATA

*(populated at the close of PHASE 1)*

# C. MECHANISM CLAIMS WHOSE OLD READ SITE WAS INVALID OR DEGENERATE

*(populated at the close of PHASE 1)*

# D. CLOSED ROUTES

*(populated at the close of PHASE 1)*

# E. THIS PHASE'S THESIS-SCALE CLAIM TARGETS

Stated up front, before any data, so that the phase can be judged against what it set out
to do rather than against what it happened to find. Lettering follows mandate §32.

**CLAIM A — concept identity is in the codeword state.**
In a large, aligned, held-out population, the codeword representation carries the *identity*
of the concept installed by the demonstrations, not merely generic remapping or generic
harmfulness.
*Requires:* ≥100 independent TEST-side domains; concepts aligned so that only the harmful
demonstrations differ; leakage controls; hard harmful negatives (knife, gun); an
`n_examples=0` null that fires; button held out; basket transfer by ranking.

**CLAIM B — remapping and identity are separable axes.**
*Requires:* directions estimated on TRAIN only; untouched TEST; both discriminations
measured on the same population; large-domain replication.

**CLAIM C — the concept-specific direction is / is not causally used.**
*Requires:* direct intervention on the concept axis; matched controls; a downstream semantic
outcome; enough domains. A negative here is a result, phrased as *"decodable but not causally
used under this intervention"* — never as *"the representation is meaningless"*.

**CLAIM D — a specific demonstration→query pathway is required for the semantic report.**
*Requires:* a token-role map established before outcomes; no concept-option leakage in the
readout; a read site that is genuinely downstream of the intervention; matched controls.

**CLAIM E — representation destruction predicts behavioural change.**
*Requires:* the same bank for both sides; adequate power at the domain level; valid controls.
Absent those, the honest answer is CANNOT ANSWER, and we will say so.

---

# PHASE 0 — EXCLUSIVE CONTROL

## 2026-09-06 · PHASE-0 · exclusivity established

**Repository state at takeover**

| item | value |
|---|---|
| branch | `behavioral-causality-sprint` |
| HEAD | `b80db84d` — *DCS-C-071: harden the four verifier harnesses, and correct my own over-broad fix* |
| unpushed commits | 0 |
| modified tracked files | none |
| untracked | `reports/SPRINT_SUMMARY_2026-09-05_TO_09-06_PART2.md`, `.claude/settings.local.json` |
| SLURM jobs for `omeryosef` | **none** — `squeue` empty |
| tmux | `C1` (disconnected stub, no work), `C2` (this session) |

**Peer Claude sessions found:** four, all idle.
`Doublespeak mechanistic interpretability continuation`, `c-001-rustling-sedgewick`,
`c-001-smooth-glacier`, `Summary of changes since 2.9`.

**Handoff.** A stand-down request was sent to
*Doublespeak mechanistic interpretability continuation* — the only peer on this research
phase. It confirmed stand-down in writing: nothing in flight, nothing of its own
uncommitted, no further SLURM submissions, and no further edits to `external_md/DCS_*`,
`doublespeak_causality/*`, `scripts/dcs_*`, or commits to this branch. Its deliverables
(`reports/DCS_SPRINT_SUMMARY_20260906.md`,
`reports/DCS_SLACK_DRAFT_MATAN_MAHMOOD_20260906_FINAL.md`) are committed and are preserved.

**Jobs cancelled:** none. There were none to cancel. No artifact was deleted.

**Disputed ownership, resolved.** The peer explicitly disclaimed both untracked paths.
`reports/SPRINT_SUMMARY_2026-09-05_TO_09-06_PART2.md` has mtime 22:28, later than the peer's
last commit at 19:18, and covers work up to `b80db84d`; it is Omer's own earlier-session
deliverable. `.claude/settings.local.json` predates the peer's session. **Neither will be
swept into a commit by this phase** unless Omer asks — per the standing rule that this is a
shared tree and only `git commit -- <explicit paths>` is safe.

**Exclusivity holds from this entry forward.** This session is the single orchestrator.
Its own subagents are read-only, report to this session, and do not launch experiments.

## 2026-09-06 · PHASE-0 · five inherited facts that would cause a false publication

Recorded verbatim in substance from the peer's handoff, because each one is a place where
acting on the prose summary rather than the artifact would put a false sentence in front of
Matan. Each is re-verified independently in PHASE 1 rather than taken on trust.

1. **Gate R6 is CANNOT ANSWER, not a null and not a confirmation** (C-068 §69). It
   reproduced R-093 to sixteen digits because all six folds pick L=6 — the *first* layer of
   the 6–14 band — where `legacy_all_query` and `target_surface_row_only` produce a
   bit-identical tensor at the read row (0 differing fp16 bit patterns over 2520 rows in all
   three banks). *Consequence at R-093's expense:* at L6 its "whole-query" manipulation is
   arithmetically identical to blocking the single codeword row. R5-FAIL stands; the phrase
   *"the whole demonstration→query pathway"* does not.

2. **"Selected on cell B" is false as written** (C-070 §74). The cell-B selection surface is
   `1.000000` at all 36 (layer, C) grid points, so `select()`'s strict `>` returns the first
   grid element and every pick is a tie-break artifact of grid order. §23.6, §50.1, §69.2,
   §70.1, §71.2 all carry the wrong sentence. No reported number changes. Two things cut the
   other way: a constant pick cannot be contaminated by test labels, and the primary is 6/6
   above chance at 36/36 points (range 0.6594–0.7690) — but **that 36-point sweep is post-hoc
   and may not be cited as a preregistered robustness check.**

3. **R8 / PHASE 7 has RUN and returned CANNOT ANSWER** (R-097 §72) — it is not "unrun". No
   behavioural outcome exists on the bank `x` lives on; power under a perfectly monotone
   truth is 0.2501 against a 0.50 bar. Recorded with an explicit process deviation: no
   `PR-xxx` was committed before that analyzer first ran, so R8 may not be promoted on it.
   `rho = +0.60` was computed and **is not citable in either direction**.

4. **Four verifier harnesses contained checks that could not fail**, fixed only at
   `b80db84d` (§75.1). One printed "VERIFIER BREACHED" over zero attacks; one credited a
   zero-byte corruption as a confirmed blind spot; two passed over the empty set;
   `C3_CONFIG_IDENTITY` compared for equality and never for presence. **Every verification
   pass before `b80db84d` ran with those in place** — that qualification travels with the
   whole inherited chain.

5. **The headline permutation `p = 0.004975` has never been independently recomputed.** It
   is `1/201`, the arithmetic floor at `n_perm=200`, checkable only as "no permutation
   reached the observed mean". Two prior reproductions exist; both spent their budget on the
   accuracies instead. Recorded as an open gap, not as closed.

**Two further inherited instrument failures**, flagged by the peer and carried here so they
are not silently re-inherited:

- **§13 has no valid instrument.** Baseline is 1.0000 in 6/6 domains on both grids, because
  the capture site *is* the token `' bomb'` — it reads lexical identity, not concept content.
  This is exactly why mandate §13 demands the intervene-at-concept-row /
  read-downstream redesign.
- **The template-family claim has no valid instrument** (C-067). LOBO's null mean is 0.8494,
  not chance, because LOBO folds on `bank_block` while the permutation relabels per domain.
  The peer deliberately did *not* fix that null, per §33 and the C-062 precedent, and flagged
  it for a conscious decision rather than inheritance. **→ raised as Q-006 below.**

**Drafts only.** Nothing has been sent to Matan or Mahmood. No email, no Slack, no calendar
event. That remains true for this phase unless Omer says otherwise (mandate §34).

---

# OPEN HUMAN QUESTIONS

Carried forward and added to. None of these blocks PHASE 1; several block GPU spend.

- **Q-001 .. Q-005** — inherited from the previous phase; restated verbatim in PHASE 1's
  audit entry once re-read from the source log.
- **Q-005** (inherited, restated here because it bears directly on this phase): should a
  selection whose surface is *saturated* be VOIDed?
- **Q-006** *(new, 2026-09-06)* — **the LOBO template-family null.** Its null mean is 0.8494
  rather than chance because the fold unit (`bank_block`) and the permutation unit (domain)
  disagree. Options: (a) leave it unfixed and never claim template generalisation, which is
  what mandate §5.4 already implies; (b) rebuild it with fold unit == permutation unit; or
  (c) construct a genuinely independent CONFIRMATION template family before extraction, per
  mandate §5.4, and retire LOBO entirely. **This phase's default is (c) if the templates can
  support it, else (a) — no template-generalisation claim.** Flagged for Omer.

---

# PHASE 1 — READ THE COMPLETE SCIENTIFIC RECORD

## 2026-09-06 · PHASE-1 · ingest launched

Nine independent **read-only** subagents were fanned out over disjoint slices of the record,
followed by one synthesis pass. No agent may write, commit, or submit. Slices:

| slice | scope |
|---|---|
| `dcs-log-A` | first half of `DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md` |
| `dcs-log-B` | second half of the same, with §§65–75 emphasised |
| `reports` | `DCS_SPRINT_SUMMARY_20260906`, the FINAL Slack draft, `DOUBLESPEAK_NEXT_PHASE_SUMMARY`, `DCS_LITERATURE_MATRIX` |
| `doublespeak-log` | `DOUBLESPEAK_CONCEPT_SPECIFIC_..._20260902.md` + the readout-instrument definitions |
| `tsc-log` | `THESIS_SCALE_CONFIRMATORY_SPRINT_PLAN_AND_PROGRESS.md` + `TSC_SPRINT_SUMMARY.md` |
| `split-rule-hunt` | repo-wide hunt for Matan's / any prior committed train-test split convention |
| `bank-code` | bank + demo-pool generation, `prompt_families.py`, sidecar, and an empirical inventory of banks on disk |
| `analysis-code` | `dcs_bombness_specificity`, `dcs_diffmeans_directions`, `dcs_extract_under_ko`, `dcs_pr041_lexical_transfer`, `dcs_kladder_analysis`, `dcs_pr045_analysis`, `extract_boombness`, `score_behavior` |
| `intervention-code` | `surgical_knockout`, position resolvers, the attention hook, `refusalness`, control draws, SLURM wrappers |
| `infra` | SLURM account/partitions/wrapper defaults, model-cache symlink health, python env, cluster capacity |

Two questions were made explicit to the bank slice because the whole phase turns on them:

1. **Is any existing bank actually aligned?** For a matched
   `(domain, family, codeword, n_examples)`, are the benign demonstrations, prompt skeleton
   and query wording *byte-identical* across bomb / knife / gun? To be answered by diffing
   real rows, not by reading the generator's intent.
2. **Do knife and gun harmful-demonstration pools exist at 116-domain scale**, or only at
   6 / 38? This is the gate on whether mandate §6.2's preferred 116-domain target is
   reachable, and if it is not, it is a **B-xxx blocker** to be documented rather than a
   reason to quietly ship n=38.

*(results appended below as they land)*
