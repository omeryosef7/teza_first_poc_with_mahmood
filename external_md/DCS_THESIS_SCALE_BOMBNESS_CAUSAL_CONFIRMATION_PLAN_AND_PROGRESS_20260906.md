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

## 2026-09-07 · A-034 · PHASE 1 COMPLETE — the record re-derived from artifacts

Nine read-only subagents + one synthesis pass. 11 agents, 281 tool calls, ~1.25 M tokens, zero
writes. **Full evidence base, including all nine raw digests, is committed at
`reports/DCS_TS_PHASE1_BRIEFING_20260906.md`.** What follows is the decision-grade summary; the
briefing is authoritative where they differ in detail.

### A-034.1 — THE FINDING THAT REDIRECTS THE PHASE

**The existing concept banks are not aligned in cell C — the primary's own population.**

Each 6-domain concept bank was generated from an *independently* GPT-4o-mini-generated pools
file (`demo_pools.json` / `_knife.json` / `_gun.json` / `_club.json`, four distinct
`content_sha16`; **0/6 domains identical in benign, harm, remap *or* filler pools**). Joined on
`prompt_id` over 2736 common ids:

| contrast | cell C | cell A | cell B | cell E |
|---|---|---|---|---|
| `button_bomb` vs `button_knife` | **948 differ / 1008** | 732 differ / 816 | 384/384 differ | 384/384 differ |
| `button_bomb` vs `button_gun` | **948 differ** | 713 differ / 816 | — | — |

The ~60–103 "identical" rows are the `n_examples=0` rows, which carry no demonstration text.

⇒ **`R-086`'s 3-way concept probe (0.7485) trains and tests on cell-C rows whose demonstration
text is 100 % freshly generated per concept.** A classifier separating bomb / knife / gun at the
codeword's hidden state may be separating three *corpora*. The length-only control (0.336)
excludes length; it does not exclude corpus.

The record recognised this **for cell A only** (`A-020` §8.1 demoted P1; `C-060` §46.1 softened
it to "modal"; the sprint summary reports cell-A overlap as a caveat on `v_bomb_specific`).
**No document states that cell C — the primary — is equally unaligned.** Trust the artifact.

This is not a reason to distrust the phenomenon. It is the reason the aligned rebuild had to
happen before anything else, and it is now done (`R-098`).

### A-034.2 — SECTIONS A–E OF THIS LOG, NOW POPULATED

**A. CURRENT SCIENTIFIC TRUTH.** Four claims survive, and none of the concept-specificity ones
survives A-034.1 unqualified.

1. **The K-ladder is a STEP at K\*=7, on 38 domains.** `R-079/080/081`. 380 prompts,
   `cds38_button_bomb`, n_ex=4. K7 −5.9849 = 90.5 % of Δ₈, **38/38 domains, p=7.28e-12** — well
   off its own floor. K8 reproduced to `−6.616111537245543`, abs diff 0.000, different node,
   three days later. Survives because every rung's token content was derived
   tokenizer-deterministically over 380/380 prompts *before* the outcome was read, and because
   it was re-established row-level after `C-055` showed the first verifier admitted seven
   corruption classes. **Bound:** the decisive token is `' bomb'`, present at K=7 only because
   `semantic_forced_choice` names both options — a fact about the instrument as much as the
   model.
2. **Control masks are not row-independent** (`R-085`). Jaccard 0.477–0.510 vs a row-independent
   null of 0.2459±0.0003, 8/8 arms. Mechanism read from source, not inferred:
   `nondemo_draw_seed(control_seed, draw_index)` has **no row term**. Unit is the arm, n=8.
3. **The intuitive readout is blind, not cleaner** (`R-088`). Same prompts:
   `semantic_forced_choice` swings **+13.08**, `comprehension_usage` swings **−0.04** against a
   pre-declared 1.0 bar, negative in 6/6 domains in *both* cells, with `option_mass` 0.22–0.41
   proving engagement rather than breakage.
4. **Two null-calibration facts about our own procedure** (`R-090`/`C-062`). Selecting
   hyperparameters on the *test* population inflates FPR 3–5×; selecting on an independent
   population is conservative. ⚠ `dcs_null_calibration2.py` is self-defeating at HEAD — R-090 is
   reproducible only from `cd6dc033`.

*(Non-DCS, different endpoint and bank family, must not be pooled with the above:* TSC's
basket↔bomb behavioural replication on Llama at 38 domains, and the Qwen3-14B CAPABLE NULL.*)*

**B. PRELIMINARY ONLY.** `R-086` concept probe 0.7485 (n=6; p **is** the 1/201 floor);
`R-091` diff-in-means concept AUROC 0.8964 (n=6; p=0.03125 = attainable floor; a strength
confound sits inside the primary); the knife-vs-club bomb-absent control 0.8596 (power 0.760 by
construction); the gun-excluded 2-way 0.9079; `R-092` gate R3 = 0.3962 (three of six domains sit
at *exactly* 1/3, so n drops 6→3); `C-066` ranking transfer 0.7951 (descriptive, post-hoc
metric); `R-093a` matched-population 12.3 % retained (only **4/6** domains positive;
`city_bridge` −0.119 the wrong way); `R-096` ratio 0.520 (explicitly descriptive, no p-values);
`R-083` 48.1 % vs a 50 % bar, missed by 1.9 pp at the exact floor.

**C. MECHANISTICALLY COMPROMISED.** A-034.1 (corpus confound in the primary's own cell);
`C-068` L6 read-site degeneracy — 0 differing fp16 bit patterns over 2520 rows in all three
banks, so gate R6 is uninformative *by construction* and `R-093`'s "whole-query knockout" is
arithmetically identical to blocking one row; `C-070` the (layer, C) selection surface is
1.000000 at 36/36 grid points and `select()`'s strict `>` therefore always returns (6, 0.01) —
root cause is that `select_layer_C` returns `best_acc` and **every call site discards it**, so
the ceiling was invisible in every artifact ever produced; §13 reads the token `' bomb'` to
decide whether the concept is bomb (baseline 1.0000, available range zero); `C-067` the LOBO
template-family null has mean 0.8494 because LOBO folds on `bank_block` while the permutation
relabels per domain; `C-057` two PR-035 secondaries have anti-conservative p-values; `C-064`
`P2_basket_lexical_transfer` trains *and* tests on basket and may not be cited as transfer;
`C-071` four verifier harnesses had checks that could not fail until `b80db84d`.

**D. CLOSED ROUTES.** `PR-031` VOID (its n=0 null fired). PHASE 4 / `comprehension_usage`
CLOSED. Gate R6 CANNOT ANSWER. §13 CANNOT ANSWER. Held-out template-family: **no valid
instrument**. PHASE 7 / R8 CANNOT ANSWER for two independent reasons (no behavioural outcome
exists on the bank `x` was measured on; power 0.2501 vs a 0.50 bar under a *perfectly monotone*
truth) — ρ=+0.60 is **not citable in either direction**. Dose-matched controls on `button_bomb`
INFEASIBLE (n_ex=8 → 0/84 feasible). Refusal-matched controls closed. P4 request-diverse bank
declined for power. **"First to causally intervene on demo→query attention in ICL" is FALSE and
must never be written** — killed twice, most recently by arXiv 2504.00132, which ablates
`y_i → t_{N+1}` edges.

**E.** unchanged — the five claim targets stand as written at the head of this file.

### A-034.3 — THE SPLIT DECISION (mandate §5.2 discharged)

**No prior committed split convention binds this phase.** A repo-wide hunt found *no* split
convention attributed to Matan; every `Matan` hit is about something else. The one prior rule
naming the right **unit** has no numbers —
`docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md:535`, *"Use train/val/test split by family/domain so
the probe cannot memorize templates"*. The one prior rule with **numbers**
(`build_split_v3.py:61-62`, 50/25/25) splits normalized concept clusters for a different
estimand. **Decision: use the mandate fallback 70/23/23 domains, citing `:535` as its source.**

Three conditions adopted, each from a recorded failure:
- **(a) a new field name, `dsplit`.** The banks' existing `split` field is a *within-domain*
  sentence cut and **all 116/116 domains straddle it** (dev 6496 / heldout 6496). Reusing it
  would be exactly the leakage §5.1 forbids while passing any validator that merely checks a
  split field exists — the `clearharm_doublespeak_v1` shape, where a per-instruction cluster
  hash made the overlap check vacuous and 77 of 86 rows leaked.
- **(b) the downstream discipline clause** adopted verbatim from
  `doublespeak_causality/reports/DATASET_AND_SPLIT_CONTRACT.md`. It also settles `C-070`: the
  selection cell must live in train/validation, never in test.
- **(c) seed `202609061`, not `20260906`** — the bare date is already `POWER_SEED` in
  `dcs_pr042_mediation.py:142` and appears in `dcs_verify_pr035.py` and the PR-028 run tags.

### A-034.4 — BLOCKERS, RESOLVED AND OPEN

- **NOT a blocker: knife/gun pools at 116 domains.** `demo_pools_116dom.json`'s harm pools carry
  `natural_word = "bomb"` for all 116 domains and `build_demo_block` substitutes whatever
  `--concept` requests. Aligned banks cost **seconds of CPU and zero API**. The 6-vs-38-vs-116
  question was a non-issue.
- **⚠ OPEN, and it must appear in the write-up: the price of alignment.** Knife/gun
  demonstrations become bomb-demonstration text with the word swapped — *"a suspicious package
  resembling a knife"* — and the predicates stay bomb-affording. Naturalness is what
  separately-generated pools bought, at the cost of the confound in A-034.1. **You cannot have
  both from this generator.** → `Q-006`.
- **Model cache healthy but structurally fragile.** `.cache/huggingface → /vol/scratch/…`
  resolves; Llama-3.1-8B-Instruct complete, revision `0e9e39f249a16976918f6564b8830bc894c89659`,
  32 layers / hidden 4096 / 32 heads / 8 KV. Scratch is purged **by policy** and the home copy is
  an 8.9 MB config-only stub — there is no fallback. `Qwen/Qwen3-14B` is **absent from both
  caches** and `HF_HUB_OFFLINE=1` makes any Qwen job hard-fail at load. → `Q-003`, `Q-010`.
- **Capacity tight.** `squeue` empty for us; of six L40S nodes in the wrapper's nodelist only
  `n-803` can currently admit the standard 48 G footprint — the binding constraint is **node
  memory, not GPUs**. `cpu-killable` has five idle nodes.
- **The silent-default launcher trap is still unguarded.** `run_boombness.sh:56`
  `: "${BOOMB_SCRIPT:=extract_boombness.py}"`. Jobs 853040–853045 were exported a variable the
  runner never reads, all six fell through to the default, ran the wrong script, and exited
  `COMPLETED 0:0`. **No guard catches this class**; mitigation is procedural and mandatory.

### A-034.5 — CONTRADICTIONS FOUND, NOT SILENTLY RESOLVED

`I.4` **94 % vs 88 %**: the sprint summary and the Slack draft lead with 94 % representation
retained; `R-093a`'s matched population says **~88 % on only 4/6 domains**. The draft carries the
more favourable number. `I.7` **mandate deliverable 12 is UNMET** — no
`CLAIM / EVIDENCE / N_DOMAINS / TEST POPULATION / CAVEAT / STATUS` table exists. `I.8` the draft
asks to lead with the K-ladder because *"no precedent we can find"*, while the literature matrix
records that axis as **"a null search, not evidence of novelty"** and logs `2605.04061` as its
*"most direct threat"* — the clearest §33 hit in the deliverables. `I.9` the draft presents club
as a clean hard negative on the old pools, the exact sentence §33 bans, and neither draft states
the scope (one model, one codeword, 6 domains, one band) at all. `I.2` `dcs_pr045.json` reports a
36-point grid for a run whose grid has 32 points, and writes one block's selection story
globally over three blocks where one has genuinely varied picks. Full list: briefing §I.

---

## 2026-09-07 · C-072 · the incidental-collision screen was codeword-only

**Defect.** `prompt_families.main()` screened the pool corpus for incidental occurrences of
`--codeword` and never of `--concept` (`:1367`). That was safe only while the concept never
varied. It varies now — the phase's entire estimand is holding the codeword fixed and varying
the concept — and `build_demo_block` substitutes the concept into the pools on exactly the same
footing as the codeword (`natural_word` → `_surface_word(...)`).

**Measured on `demo_pools_116dom.json`:** `knife` collides twice
(`solar_array|benign[18]` — *"A chef's knife shaped like a carrot…"*; `university_lab|benign[39]`)
and `gun` once (`coastguard_post|benign[4]` — *"…next to the flare gun."*). Unscreened, those
three sentences would have given the knife and gun banks a different target-occurrence count
from the bomb bank in the families that draw them: a silent, concept-dependent misalignment
inside the one contrast the phase exists to measure, which **no downstream guard checks for**.

**Fix.** The screen is now the union over codeword and concept, and its refusal message states
the constraint that matters: *use the SAME repair map for every concept in the family.*
`apply_incidental_repairs` rewrites the pools in memory before generation, so a per-concept map
produces per-concept pools and destroys the byte-alignment it was invoked to protect.

**Not a retraction of anything published** — every prior bank used `--concept bomb`, which has
**zero** collisions on this pools file. The defect was latent, not active.

---

## 2026-09-07 · R-098 · the aligned thesis-scale concept bank exists (PHASE 3 complete)

**Six banks: `{button, basket} × {bomb, knife, gun}`, 116 domains, 22,272 rows each.**

| | |
|---|---|
| pools | `demo_pools_116dom.json`, `pools_sha16 = 976aa2b0b617118d` |
| preset | `main_longpre_cds_ts` (new, derived — see below) |
| seed | 20260901 |
| repair map | `button=switch, basket=hamper, knife=peeler, gun=beacon` — **identical for all six** |
| alignment violations | **0** in all six |
| duplicate prompt_ids dropped | **0** in all six |
| rows per bank | 22,272 = cells A/B/C/E × 5,568 |
| doses | n_ex 0 / 4 / 8 → 2,784 / 13,920 / 5,568 |
| channels | `behavioral`, `semantic_one_word`, `semantic_forced_choice` → 7,424 each |

`bank_rows_sha16`: button_bomb `c37127790a08519f`, button_knife `151ef6734bfdbe6e`, button_gun
`e1ff5534b5318ad9`, basket_bomb `86463da433d0eebf`, basket_knife `2839bfbc4d41a8b9`, basket_gun
`60b508bd1aa6d0a7`.

**THE ALIGNMENT RESULT.** Case-preserving whole-word swap of the concept, compared over the full
`prompt_id` join:

| contrast | aligned |
|---|---|
| button: bomb vs knife | **22272 / 22272** |
| button: bomb vs gun | **22272 / 22272** |
| basket: bomb vs knife | **22272 / 22272** |
| basket: bomb vs gun | **22272 / 22272** |

Every non-concept byte is identical: benign pool, filler, preamble, prompt skeleton, role
formatting, query wording, answer instruction, demonstration count, codeword, token-position
conventions. **Only the harm demonstrations' concept word differs.** This is the clean Matan
estimand, and it is the property the old 6-domain banks did not have (A-034.1).

**The n=0 null is EXACTLY byte-identical across concepts in both concept-free channels** — 928
rows = 2 cells × 2 query kinds × 232. Those rows are literally the same bytes under three
different concept labels, which makes them the sharpest available test of the corpus confound:
a probe that separates concepts there is reading nothing but its own labels.

**A first pass at 18 apparent misalignments was my own measurement error, not the bank's** — my
comparison regex lower-cased the substitution, so rows containing *"Atomic Bomb"* and
*"Do Not Approach: Bomb"* looked different. Case-preserving comparison gives 22272/22272. Recorded
because the failure mode — an audit that indicts the artifact when the audit is what is broken —
is the one this project keeps re-learning.

**⚠ THE SCOPE LIMIT THIS BUYS, stated up front rather than discovered later.** The harm pools'
natural word is `bomb` in all 116 domains, so the knife and gun demonstrations are
bomb-demonstration text with the word swapped, and the predicates stay bomb-affording. Whether
they *install* knife and gun is now an **empirical question measured per concept**, not an
assumption — and per mandate §15 a concept that fails to install is a finding about the
population, not a post-hoc exclusion. → `Q-006`.

**New preset `main_longpre_cds_ts`**, derived from `main_longpre_cds` per the file's own standing
convention (deriving leaves every existing preset byte-stable;
`tests/test_bank_regenerates_byte_identically.py` **3 passed** after the change). It adds exactly
the two things the mandate requires and the parent lacks:
- **`semantic_one_word` as the primary mechanistic channel.** The parent carries only
  `behavioral` and `semantic_forced_choice`, and forced-choice **names the concept in the
  question** — which is why K\*=7's decisive token was `' bomb'` and why §13 sat at a baseline of
  1.0000 with zero available range. A readout used to localise a hidden state must not contain
  the label being read. ⚠ Recorded *before* running, as `rbd12_sow` recorded it: this framing's
  absolute option mass sits near 1e-5, so the primary statistic is the **relative**
  `semantic_logodds`, with `option_mass` reported as an engagement diagnostic and never as the
  outcome. If option mass shows the channel is disengaged, that is a CANNOT ANSWER on the
  primary — **not** a licence to switch to the display channel after the fact.
- **`n_examples=0`**, the one null the concept probe cannot do without.

**The rows are not committed.** 6 × 70 MB against a `.git` already at 4.3 GB, for content that
regenerates byte-identically in seconds. What is committed pins it completely: each bank's
`_meta.json` carries `bank_rows_sha16`, the pools hash, seed, preset and repair map, and
`scripts/dcs_ts_build_banks.sh [build|check]` regenerates and verifies all six against those
hashes using the repo's own `common.rows_sha16` helper rather than a second implementation.
Verified: **6/6 present and matching.**

---

## 2026-09-07 · R-099 · the domain split is frozen (mandate §5.2)

`data/boombness_prompts/dcs_ts116_domain_split.json`,
**`manifest_sha16 = be7d2c772d814ef3`**, `pools_sha16 = 976aa2b0b617118d`.
**70 train / 23 validation / 23 test domains, seed 202609061, field name `dsplit`.**

Built by `scripts/dcs_ts_split_manifest.py` from the domain roster **alone**, before any hidden
state, logit, installation outcome, probe score or ASR exists. The roster is read from the pool
**keys**, not from `_meta["domains"]` — they agree today, but the keys are what the generator
iterates, and a roster disagreeing with the pools it describes is the drift this phase exists to
catch. Assignment is one shuffle of the *sorted* roster under `random.Random(seed)`, so it
depends only on the set of domain ids and the seed.

`--write` **refuses to overwrite an existing manifest**: a split may be created once, and
regenerating it after outcomes exist is the reshuffle §5.2 forbids.

**The verifier's checks were proven able to fail** — the `C-071` lesson applied to new code
rather than only recorded. Five mutations, five RED:

| mutation | result |
|---|---|
| flip one domain's label | RED, 3 errors |
| wrong seed | RED, 62 domains disagree |
| empty assignment | RED — explicitly caught, rather than passing over the empty set |
| corrupted `manifest_sha16` | RED |
| illegal label (`trian`) | RED, 4 errors |

**A join hazard found while verifying, and it binds every analysis in this phase:** the `button`
and `basket` banks share **all 22,272 `prompt_id`s** — `prompt_id` does not encode the codeword.
Joining across codeword banks on `prompt_id` alone silently pairs the wrong rows. Mandate §7's
compound key `(bank_file_sha16, prompt_id)` is therefore not a nicety here; it is load-bearing,
and it must be asserted at runtime in every script this phase writes.

---

## OPEN HUMAN QUESTIONS — updated

Nothing below blocks the work in flight; each is flagged at the point where it would change a
published sentence. Q-001..Q-005 carry forward from the previous phase (see
`reports/DCS_TS_PHASE1_BRIEFING_20260906.md` §J for their full text).

- **Q-006 — alignment vs naturalness. ANSWERED PROVISIONALLY, proceeding under a stated
  assumption.** Aligned banks make knife/gun demonstrations bomb-text with the word swapped;
  natural pools would cost hours of API generation and reintroduce the corpus confound the phase
  exists to remove. **Decision taken: alignment is primary, because a confounded contrast cannot
  be repaired by more data and a synthetic-but-clean one can be qualified honestly.** Installation
  is measured per concept and reported, so the cost is visible rather than assumed away. A
  natural-pool replication remains available later as a secondary, CPU-only track. Omer may
  overrule; nothing downstream is wasted if he does, since the aligned banks stand on their own.
- **Q-007 — does A-034.1 void `R-086` retrospectively, or bound it?** The honest options are
  (a) PRELIMINARY pending the aligned rerun, (b) retract as a *concept* claim and re-report as a
  bank-discrimination result, (c) re-derive on the ~60 identical n=0 rows (hopelessly
  underpowered). **This phase proceeds under (a)** and will let the aligned rerun decide. It
  matters because the FINAL Slack draft currently leads with 0.7485.
- **Q-008 — adopt two one-line binding rules?** (i) any band-limited intervention must be read
  **strictly above the band's first layer**; (ii) every artifact must persist
  `SELECTION_TRACE.inert` / `n_tied_at_best`. Between them they would have caught two of the
  previous phase's four CRITICALs. **Proceeding as if yes** — both are already mandate §12/§8.2
  in substance.
- **Q-009 — does this phase need a behavioural outcome on the same bank?** `R8` is CANNOT ANSWER
  purely because no `y` exists where `x` was measured. The new banks carry `behavioral` rows on
  the *same* families as the representation rows, so the option is preserved by construction at
  zero extra cost. No decision needed yet.
- **Q-010 — Qwen3-14B is absent from both caches** and `HF_HUB_OFFLINE=1` makes any Qwen job
  fail at load. **Proceeding Llama-only**, recorded as a scope limit, not as a model-specificity
  claim.

## 2026-09-07 · C-073 · the silent-default launcher trap is now guarded

`DCS-C-047` cost ~1.7 GPU-hours and was invisible: jobs 853040–853045 exported `ARGSFILE=…`, a
variable `run_boombness.sh` never reads, so all six fell through
`: "${BOOMB_SCRIPT:=extract_boombness.py}"`, ran the wrong script, and exited **`COMPLETED 0:0`**
in 11–27 minutes. No guard in this project catches that class, because every guard checks an
artifact and a missing arm is indistinguishable from an unstarted one.

Two **additive, opt-in** defences, chosen so no existing caller can break:

1. the runner now states whether `BOOMB_SCRIPT` was **PROVIDED or DEFAULTED**, so `grep` over the
   first ten log lines answers *"did this job run what I meant?"* without reasoning about env
   plumbing;
2. an optional **`BOOMB_EXPECT`**: when set it must equal the resolved `BOOMB_SCRIPT`, or the job
   refuses before doing any work. A caller that sets it cannot be silently defaulted; a caller
   that does not is unaffected. It also refuses a `BOOMB_SCRIPT` that does not exist, naming the
   bare-filename convention that has bitten before.

**This phase sets `BOOMB_EXPECT` on every submission.**

Proven to fire, not merely written — four mutations run against the real wrapper:

| mutation | result |
|---|---|
| `BOOMB_EXPECT` ≠ `BOOMB_SCRIPT` | REFUSED, `origin=PROVIDED` |
| the exact 853040 shape: variable not read, script defaults, `BOOMB_EXPECT` set | REFUSED, `origin=DEFAULTED` — names the cause |
| nonexistent script | REFUSED, states the bare-filename rule |
| valid call | **NOT blocked** — reaches the GPU guard (`need L40S got 'NVIDIA TITAN Xp'` on the login node) |

That last row matters as much as the first three: a guard that also blocks correct calls is a
new failure, not a fix.

## 2026-09-07 · PHASE-4 · GPU preflight (mandate §27)

`scripts/dcs_ts_preflight.sh`, run before every sbatch in this phase. **PASS** at 2026-09-07 00:39.

| check | state |
|---|---|
| `.cache/huggingface → /vol/scratch/omeryosef/hf_cache` | resolves |
| Llama-3.1-8B-Instruct snapshot `0e9e39f2…` | 4 safetensors shards, **15,327 MB resolved** |
| `tokenizer.json` / `config.json` | 9,085,657 B / 855 B |
| 10 MB write round-trip to `outputs/` | ok — 1.4 T free of 20 T |
| 6/6 ts116 banks vs `bank_rows_sha16` | match |
| domain split manifest | verifies |
| our queue / cap | 0 jobs, within the 6-job cap (killable: 90 running, 113 pending) |

It resolves symlinks with `readlink -f` and follows blob links with `ls -L`/`du -L`, because the
`DCS-B-019` failure was a **dangling** symlink whose directory listing looked perfect: `mkdir -p`
reports `File exists` on a dangling link rather than creating through it, and under
`set -euo pipefail` three arms died in 4–47 s behind a message that never mentions the model
cache. The 10 MB write is a real write, not a `touch`: the binding limit is a user/qtree quota
`df` cannot see, and it is size-dependent — a 5-byte write has succeeded in the same second a
100-byte write returned EDQUOT. It also refuses an argsfile on node-local `/tmp` (invisible to
compute nodes; the job dies in ~3 s) or containing a quote character (`BOOMB_ARGS` is word-split,
so quotes become literal argv characters).

⚠ Standing risk unchanged: **scratch is purged by policy and there is no fallback copy** — the
home cache is an 8.9 MB config-only stub. The preflight turns that from a cryptic death into a
one-line diagnosis; it does not prevent it. → `Q-003`.

## 2026-09-07 · A-035 · literature update (mandate §25)

Full document: `reports/DCS_TS_LITERATURE_UPDATE_20260906.md`. The existing
`DCS_LITERATURE_MATRIX.md` was deliberately **not** modified.

**The decision-relevant finding, and it is good news narrowly and bad news broadly.**
`arXiv 2609.02438` (Sudheendra & Srivastava, 2026-09-02) does **not** pre-empt our specific
claim: it establishes a decodable / expressed / causally-used three-way separation for **logical
validity**, on a purpose-built logic-verification benchmark across five models — no ICL framing,
no demonstrations, no codeword mechanism, no attention intervention. **OVERLAPS on framing,
ORTHOGONAL operationally.** But it, plus `2604.22128` (Dyck-language decodability-vs-causal-use)
and at least three others, make *"decodable but not causally used"* **a converging 2026 pattern**.
⇒ **the generic dissociation sentence can no longer lead.** Our instance — an *attacker-installed*
concept, a safety endpoint, band-limited attention zeroing on a demonstration span — still can.
This is the substance of `Q-002` and it is now answered with citations.

`arXiv 2504.00132` (Bakalova et al.), pinned precisely so our delta is stated accurately rather
than assumed: it ablates `y_i → t_{N+1}` edges by **counterfactual K/V patching**, at **every
layer and head simultaneously**, on **Gemma-2 2B only**, one query position, task-accuracy
endpoint, no safety framing. Ours is attention **zeroing**, **layer-banded** (6–14), on a
semantic-remapping attack, cross-family, with a query-row-count axis it has no analogue of. The
banned sentence stays banned; the delta survives.

`arXiv 2605.04061`, logged in the matrix as the K-step's *"most direct threat"*: confirmed 0 %
single-position vs 96 % multi-position transfer and a ~30 % depth window, with query position
"strictly necessary" as a **binary**, not a count. **It still has no query-row-count axis**, so
the K-step's specific axis is unaddressed. ⚠ A venue discrepancy surfaced (this fetch returned an
internally garbled "ICLR 2026 (Learning and Intelligent Optimization Conference)" against the
matrix's "LION 2026 + ICLR 2026 workshops") — recorded **UNRESOLVED**; do not print a venue for
this paper until a third source agrees.

*Yona et al. ACL 2026* is the same Doublespeak paper already at matrix row 1.1 (arXiv 2512.03771).
No second paper exists; no new overlap.

**Honesty on coverage, per §25.** Two searches returned nothing and are recorded as **null
searches, not as evidence of novelty**. The **OpenReview blind spot flagged in the matrix
§5.3/§6.3 remains OPEN** — this update did not run an OpenReview search and did not close it.

---

## 2026-09-07 · C-074 · **R-098's bank is VOID as a concept contrast. My design error.**

**Supersedes `R-098`.** The six `ts116` banks are real, aligned and internally consistent — and
they cannot answer the question they were built for, because the alignment I verified is *total*
in exactly the cell that needs signal.

### What is wrong

Cell C (`natural_doublespeak`) draws the **harm** pool at `demo_surface = "codeword"` — the
concept word is replaced by `button` before the prompt is assembled. Its demo block reads:

> *A recent inspection revealed a suspicious package resembling a **button**. Staff received
> training on how to handle a potential **button** threat.*

The concept word never appears. So once the harm **sentences** are shared across concepts — which
is precisely what a bomb→knife word swap on a pool whose `natural_word` is already `bomb`
produces — the bomb, knife and gun prompts are **the same bytes**.

Measured on the artifacts:

| population | identical across bomb ∧ knife ∧ gun |
|---|---|
| cell C × `semantic_one_word` (**the primary**) | **1,856 / 1,856 = 100 %** |
| cell C × `behavioral` | 1,856 / 1,856 = 100 % |
| cell C, all channels | 3,712 / 5,568 = 66.7 % |
| whole bank, per codeword | **7,424 / 22,272 = 33.3 %** |

Extended by the adversarial agent to 14,848/14,848 triples over 44,544 rows in
{A,C} × {behavioral, semantic_one_word} × n_ex {0,4,8}.

⇒ The 6,960 probe rows collapse to 2,320 distinct texts, each carrying the **full label multiset
{bomb, knife, gun}**. A hidden state is a deterministic function of its prompt, so the
Bayes-optimal accuracy of *any* probe there is **exactly 1/3**. It cannot beat chance. **The
ceiling is the bar.** Any other number would be a pipeline bug, not a finding.

The only cell-C rows that do differ are `semantic_forced_choice`, and they differ by **one printed
noun in the question, ~8 tokens from the end** — the instrument naming the answer, which is the
defect §11 exists to avoid.

Corroborating, from the concept-backing audit: **83.3 %** of dosed cell-C prompts carry
bomb-specific collocates (*"suspicious package resembling a gun"*, *"gun disposal unit"*). The
context installs **bomb in all three arms**. Tier-1 explosive predicates (`detonat*`, `defus*`,
`blast`, `unexploded`) appear in 396/9,280 = 4.27 % of knife sentences — identically for gun,
because they are the same sentences.

### Why my verification missed it

*"Identical up to a swap of word W"* and *"identical"* are the same statement when **W does not
occur**. I reported 22272/22272 aligned and never counted how many rows actually contained the
swapped word. The count is the check; the swap is not. Recorded plainly because this is the
second time in one day that my own audit, not the artifact, was the broken thing — the first was
the case-sensitivity false alarm in `R-098`.

I also over-read mandate §6.1. It says keep the benign pool, filler, preamble, skeleton and query
byte-identical and **CHANGE ONLY the harm demonstrations that define the installed concept**. I
made the harm demonstrations identical too, which is not the middle between the old banks and the
new one — it is the far end, past the manipulation.

### What actually carries concept identity

In doublespeak the codeword **stands for** the concept, so the installed concept is defined by
what the demonstrations say the codeword **affords**. *"resembling a button"*, *"the button was
defused"* install BOMB. *"the button was sharpened"*, *"the button slipped from the cutting
board"* would install KNIFE. **Identity lives in the predicates, not in a word that is
substituted away.**

The three designs, stated so the distinction is never lost again:

| design | benign / remap / filler | harm sentences | verdict |
|---|---|---|---|
| old 6-domain banks | **regenerated per concept** | regenerated per concept | confounded — three corpora (`A-034.1`) |
| `ts116` word-swap (`R-098`) | shared | **shared** | **no manipulation** — this correction |
| `ts116n` (next) | shared, byte-identical | **concept-specific, naturally generated** | the mandate §6.1 design |

### The fix, and it dissolves Q-006 rather than answering it

`scripts/dcs_ts_gen_concept_harm_pools.py` generates the **harm pool only** for a concept and
copies benign / remap / filler **byte-for-byte** from `demo_pools_116dom.json`. It reuses
`prepare_demos.gen_demos` and `demo_pools._clean` unchanged — same generator, same
exactly-one-whole-word filter, same 8-round retry — so the new pools are produced by the identical
process that produced the bomb pools they will be compared against. Neither `demo_pools.py` nor
`prompt_families.py` is modified.

The domain style hints are **concept-agnostic** by construction (`DOMAINS[d]["harm"]` specifies
register and setting — *"flat incident-log sentences from an airport ground-handling safety
inspection"* — never the concept), so knife and gun get naturally knife- and gun-affording
sentences inside the same frame.

**`Q-006` was a false dilemma and I posed it wrongly.** I framed alignment and naturalness as a
trade, and proceeded on "alignment is primary". The trade only existed because I was word-swapping.
Generating **only** the harm pool per concept gives **both**: naturalness where the manipulation
lives, byte-identity everywhere else. The correct answer was available at the time and I did not
see it.

### Status of the artifacts

The six `ts116` banks are **not deleted** and **not retracted as artifacts** — they are byte-exact,
they verify against their hashes, and they remain the correct instrument for a different and
narrower question: *is the doublespeak concept lexically separable at the codeword?* The measured
answer to that is **no, by construction**. They are **VOID as a concept-identity contrast**, which
is what `R-098` claimed. The claim is withdrawn; the files stay.

### Cost of the error

Roughly two hours of wall-clock and zero GPU. It was caught by the PHASE 4 audits **before any
extraction**, by two independent agents that had been told to attack rather than confirm — the
leakage audit found it as a byte-identity, the adversarial audit as a refutation. That is the
gate working. Had the mandate not required these audits before GPU, the phase would have spent
GPU hours to measure a quantity pinned to 1/3 by arithmetic and would very likely have reported
the resulting 0.333 as a **negative result about the model**.

## 2026-09-07 · A-036 · the token-role map, and the downstream read site (mandate §14, §22.2)

`scripts/dcs_ts_token_roles.py`, `reports/DCS_TS_TOKEN_ROLE_MAP.md`,
`outputs/dcs_ts/token_roles_ts116.json.gz` (4.4 MB: per-prompt `input_ids`, decoded tokens,
preamble / demo-line / demo-block / query / generation-header spans, every codeword and concept
occurrence, per-token query roles). 6,960 prompts = 116 domains × 2 codewords × 3 concepts.
**14 checks, 13 PASS / 1 FAIL, 11 mutations 11/11 RED** — including binding the whole suite to an
empty row set, which returns `ERROR_EMPTY` rather than PASS.

**A third independent confirmation of `C-074`, by a different method.** Not the swap check —
**token-id identity**: `input_ids` identical across all three concepts in **4,640/4,640**
comparisons, and the strict whole-word count of bomb/knife/gun over the whole templated prompt is
**0 in 6,960/6,960**. Three agents, three methods (byte identity, adversarial refutation, token
identity), same conclusion.

**THE DELIVERABLE — the downstream neutral read site, which unblocks the corrected mechanism
test.** All nine tail offsets satisfy the four criteria at 6,960/6,960. **Nominated:
`pos = len(input_ids) − 9`**, decoded `' actually'`, token id 3604. It is exactly the
**codeword + 1** slot — the repo's existing `following` site
(`ds_common.target_positions`, `extract_boombness --position following`) — so a readout there is
**directly comparable with prior `following` results** rather than a new incomparable site.
Verified strictly after every codeword occurrence, no concept substring, same token id in
6,960/6,960.

⚠ **Offsets must be relative to the END.** Prompt length ranges **196–280 tokens**, so an absolute
index is not stable across prompts — the absolute-position-index bug class this repo has already
hit twice. Over the last 28 positions of all 6,960 prompts the *only* varying position is `−10`,
the codeword itself; 0 others vary. `button` and `basket` are one subtoken in 34,809/34,809
occurrences, so the tail does not shift between codeword banks.

**THE K-LADDER CORRECTION, now quantified rather than asserted.** Counting rungs back from the
end: K=1 `'\n\n'`, K=2 `'<|end_header_id|>'`, K=3 `'assistant'`, K=4 `'<|start_header_id|>'`,
K=5 `'<|eot_id|>'`. **The first five rungs carry zero query content.** The first query-content
rung is K=6 (`'?'`) and the first non-punctuation query token is K=7 (`' to'`). Per-prompt query
side, identical in all 6,960: 28 tokens = 5 scaffold + 23 content (1 chat_scaffold,
4 response_header, 3 punctuation, 1 codeword, 8 answer_format_instruction,
11 user_instruction_scaffold, 0 concept_word, 0 neutral_content). §33's ban on *"K=1/2 are query
rows"* now has a measured replacement.

**LAYER CONVENTION, read from code across eight sites and consistent:**
**block layer L == `hidden_states[L+1]`; `hidden_states[0]` == embeddings**
(`signals.py:46`, `common.py:15`, `extract_boombness.py:21,:346,:439`, `refusalness.py:235`,
`ds_common.py:866`, `09_attention_knockout.py:57`).
⚠ `extract_boombness.py:331-347`: transformers 5.12 ties the last tuple entry to
`last_hidden_state`, so `hidden_states[n_layers]` is **post-final-norm**; `forward_hidden()`
substitutes the hooked raw `layers[-1]` output. **L = n_layers−1 is correct only through
`forward_hidden()`.**
**This is a code reading, not a test.** Mandate §22.3 requires a planted hook; the report
specifies it (hook block L=12, +1e3 on coord 0 at position p, assert `hidden_states[L+1]` moves
by exactly 1e3 and `hidden_states[L]` does not; repeat at `n_layers−1` through `forward_hidden`
and assert its `hs[-1]` differs from `out.hidden_states[-1]`; repeat with a **pre**-hook and
assert it moves `[L]` not `[L+1]`; pin `transformers.__version__`). **Scheduled as the first GPU
job of the phase**, before any measurement.

Two off-by-one inconsistencies found by grep and **flagged, not adjudicated** (both outside this
phase's code path): `44_kv_mediation.py:289` reads `hidden_states[R+1]` while `:292` reads
`hidden_states[best_ps_layer]` bare, in the same function; `18_run_behavioral_necessity.py:99`
stacks `hs[l]` so row `l` is block `l−1` and row 0 is the embedding.

## 2026-09-07 · C-075 · the codeword matcher is right-permissive, and the bank agrees with it

`ds_common.find_word_occurrences_in_text` is left-strict but **right-permissive** — its docstring
says *"allow inflections (carrots) but not substrings inside a longer word (scarrot)"* — so
**`basket` matches inside `basketball.`** in the `school_campus` dev preamble. **9 prompts**
(basket × {bomb,knife,gun} × family_slot {0,8,12}, split=dev) therefore carry a spurious **6th
"codeword occurrence"** that is an unrelated benign word, upstream of every demonstration.

**Why no existing check caught it, and this is the point.** The *generator used the same matcher*,
so the bank's own `n_codeword_occurrences` says 6 too. A checker that compares the finder against
that field **agrees with itself and sees nothing** — check A does exactly that and passes
6,960/6,960. Only check J, which re-derives from the templated text, fails. This is the
matcher/scope bug class and the "a check that reads the same broken source" class in one object.

**Blast radius:** it does *not* touch the nominated read position (6,960/6,960 still strictly
after every match). It **does** corrupt any occurrence-ordinal analysis, any "block every codeword
site" knockout, and any demo-installed-occurrence count on those 9 rows. Independently
corroborated by the adversarial audit as F6: `n_codeword_occurrences` is substring-counted in the
basket banks, wrong in **60/22,272** rows (0.27 %), all `school_campus`, all in train.
**Not silently fixed** — fixing a matcher that a committed bank's metadata was generated with
would change that metadata's meaning at a distance. Carried as a known defect with a named
exclusion: `school_campus` is dropped from any occurrence-ordinal or all-sites-knockout analysis,
and that exclusion is preregistered rather than applied after seeing an outcome.

## 2026-09-07 · A-037 · concept backing, and what the word swap actually cost

`scripts/dcs_ts_audit_concept_backing.py`, `reports/DCS_TS_CONCEPT_BACKING_AUDIT.md` (334 KB,
including the 116-domain × 3-concept human-readable appendix Matan asked for). **13 checks, 13
mutations, 13/13 RED**; a zero-binding check is forced RED by construction.

The numbers that quantify `C-074` from the corpus side:

- **396/9,280 = 4.27 %** of knife demonstration sentences carry a tier-1 explosive predicate
  (`detonat*`, `explos*`, `unexploded`, `defus*`, `blast`, `fuse`, `… shell`) — **identically for
  gun and bomb, because they are the same sentences.** Tier-2 bomb-procedural vocabulary
  (`squad`, `disposal`, `sniffing`, `controlled explosion`): 464/9,280 = 5.00 %.
- At prompt level: **1,110/6,960 = 15.95 %** of cell-C n_ex=4 rows and **780/2,784 = 28.02 %** of
  n_ex=8 rows carry ≥1 tier-1 predicate. Balanced across dsplit (train 4.25 %, val 4.35 %,
  test 4.24 %), so it is not a split artifact.
- Conversely the demos afford the *nominal* concept at rate **zero**: knife-affording predicates
  0/9,280, gun-affording 0/9,280 — with a documented false-friend table (`stable`/`stabilizing` 42,
  `surrounding` 86, `fire alarm` 65, `triggered` 36, `barrel cellar` 11, film `shoot` 3) showing
  the zero is tightened, not lazy.

**A real polysemy defect the curated patterns could not see.** The 37 named-sense patterns
(flare/glue/spray gun, chef's/putty/palette knife, bath bomb, photobomb) return **0** hits —
mechanically impossible under a word swap. But the **mass-noun frame `a <W> of <NOUN>`** —
*"a bomb of yeast"*, *"a bomb of rotting tomatoes"* — appears in **171/4,640 = 3.69 %** of
sentences across **12 of 116 domains**: `restaurant_kitchen` **40/40**, `ceramics_kiln` 37/40,
`plastics_moulding` 23/40, `brewery_works` 19/40, `dairy_plant` 16/40, `garden_centre` 14/40, then
6/6/5/3/1/1. **This is the same failure mode as the old `club` pools**, and it will apply to the
regenerated pools too — the audit must be re-run on `ts116n`.

**Hedging caps installation strength:** **861/4,640 = 18.56 %** of sentences merely compare to,
simulate, joke about, drill for, or deny a device (*"a package resembling a button"*, *"false
alarm"*), from 0/40 to 20/40 by domain. Uniform across concepts, so it does not confound the
contrast, but it bounds absolute installation.

**Prompt-only domain rules, preregistered before any outcome:** blacklist = 6 domains with
≥10/40 mass-noun sentences; clean sub-corpus = 35 domains with zero tier-1; **recommended analysis
set = 33 domains (22 train / 6 validation / 5 test)**. ⚠ 33 domains would *undo* the thesis-scale
gain — so on `ts116n` the right use of these rules is a **preregistered stratification**, not an
exclusion, unless the regenerated pools show the same rates.

## 2026-09-07 · A-038/A-039/A-040 · leakage, power, adversarial

**A-038 leakage** (`scripts/dcs_ts_audit_leakage.py`, `reports/DCS_TS_LEAKAGE_AUDIT.md`): 19/19
checks pass, 15/15 mutation transitions RED. Found `C-074` as a byte-identity. Nuisance baselines
on the *doomed* population are all exactly at chance (length-only 0.3333/0.5000, TF-IDF
0.3333/0.5000, template-id 0.3333/0.5000) — which correctly says **alignment is not broken**, it
is total. **Template-id at chance is the check that would have screamed if the banks were
misaligned, and it is the one number from this audit that carries over.** Occurrence table:
own-concept rate is either 0/3712 or 3712/3712, never a third case; 24 of 36 buckets
(**66.67 % of rows**) name the concept and are unusable for a "hidden state contains the concept"
claim; our regex recount disagrees with the producer's `n_concept_occurrences` in **0/133,632**
rows. **Must be re-run on `ts116n`, where the numbers will be informative rather than
degenerate.**

**A-039 power** (`scripts/dcs_ts_power.py`, `reports/DCS_TS_POWER_ANALYSIS.md`): 6 checks, each
demonstrated RED under a named mutation. **RECOMMENDATION: KEEP 70/23/23.**
- **p-floors at n=23**: permutation `1/(B+1)` → B=200 gives 0.004975 (**the old headline *is* the
  floor**, MC relative SE 99.7 %); **B=10,000 → 9.999e-05, rel SE 14.1 %, recommended**. Sign-test
  two-sided floor: n=6 → 0.03125 (so 6/6 was worth 0.031, not 0.005); **n=23 → 2.384e-07**.
- **MDE**: recovered the six old per-domain accuracies exactly (mean 0.7485380116959064) →
  between-domain SD 0.1290, projected 0.1514 (m=30) / 0.1406 (m=60) → **MDE 0.0925 at n=23**
  against an old effect of 0.4152, a **4.5× margin**. ⚠ that SD has only **5 df**; at its 95 %
  upper bound 0.3439 the MDE degrades to 0.2102.
- **ICC** 0.0884 → DEFF 6.22 at m=60; the 1,380 test rows carry **n_eff = 222**. A row-level p
  would print **1.02e-06** where the honest domain-level p is 0.05.
- **FPR on pure noise, 300 reps, the real 36-point selection grid**: validation-selected **0.0467**
  (calibrated); **test-selected 0.4433 — 9.5× inflation**, worse than the previously measured
  3–5× because inflation scales with grid size; row-level permutation 0.2000. At n_test=6,
  validation-selected FPR is 0.0600 ⇒ **the old 6-domain design was calibrated; its defect was
  resolution, not type-I rate.**
- **Four rules adopted for every confirmatory run in this phase:** (1) `n_perm=10000`, and publish
  every p next to its floor, reporting `p < 1/(B+1)` on zero exceedances; (2) domain is the unit
  everywhere, group permutation never row; (3) all hyperparameters selected on the 23 validation
  domains; (4) use both codewords (SD 0.1514→0.1406, n_eff 193.6→222.0, and a free generalisation
  axis).
- **Flip trigger, checkable on TRAIN only before any test read:** if the 70-domain nested-LODO
  between-domain SD exceeds 0.25, or train-LODO mean accuracy is below 0.55, rebuild as
  **58/29/29** before the confirmatory run.
- ⚠ Landmine found: the flagship cell is `cell == "C"`, **not** `condition == "natural_doublespeak"`
  — that string lives in `condition`, and selecting on it **binds 0 rows**.

**A-040 adversarial** (`reports/DCS_TS_ADVERSARIAL_AUDIT_BANK.md`): **CLAIM REFUTED**, by the same
defect, found independently. Its additional findings:
- **MINOR, real, and it survives the rebuild**: **28/18,530** demo sentences (0.15 %) appear in
  more than one domain, 24 spanning dsplits; **72/3,864 test rows (1.86 %)** share a verbatim demo
  sentence with a train row (cell C 30/966 = 3.11 %). 13/23 test domains have a name-sibling in
  train, but train–test vocabulary cosine (mean .7547) is **not worse** than within-split
  (mean .7464).
- **The structural limit that binds every design here**: median inter-domain cosine is **0.752**.
  *"The domains were never independent, since every harm pool is a rewrite of one bomb template
  family."* This bounds the independence claim on `ts116n` too and must be stated in the write-up.
- Honest nulls: 1,069,056 cross-concept field comparisons, **0 failures**; bomb/knife/gun are
  **single tokens** in Llama-3.1-8B, Qwen3-14B and gemma-4-E4B, and **0/22,272** rows differ in
  token count — so the token-length confound is a clean null; exact class balance (48 rows per
  (domain, cell) in all 464); repair map uniform across all six banks; all six `bank_rows_sha16`,
  `pools_sha16` and `manifest_sha16` recomputed and reproduce; `prompt_sha16 == sha256(full_prompt)[:16]`
  in 133,632/133,632.

## 2026-09-07 · PHASE-3b · the `ts116n` rebuild is generating (smoke passed)

**Smoke, job 859713, `airport_apron` only, COMPLETED 0:0 in 6:06.** Log verified for script and
args on its first lines per §26.10 before anything else was submitted. Result: 40 knife sentences,
6 dropped for `occurrence != 1`, the three shared pools **byte-identical** to
`demo_pools_116dom.json`, and the script's own verifier PASS.

The sentences are the point, so they are recorded here rather than summarised:

> *The security team confiscated a **knife** before boarding the aircraft.*
> *A **knife** with a broken handle was found by the service road.*
> *The baggage handler accidentally dropped a **knife** while unloading cargo.*

against the same domain's bomb pool:

> *The baggage handler found a suspicious package that resembled a **bomb**.*
> *A **bomb** scare has caused a temporary evacuation of the baggage hall.*

Genuinely knife-affording predicates, in the same airport-apron incident-log register. **The
manipulation is real and the frame is shared** — which is what `R-098` lacked and what `A-034.1`
said the old banks bought at the cost of regenerating everything.

⚠ **A design correction made before launching, not after.** The plan had been to regenerate only
knife and gun and reuse the shared file's **bomb** harm pool. That pool was generated on
2026-08-28 at `openai_seed 20260828`; knife and gun would be generated on 2026-09-06 at seed
20260906. That is a **concept × generation-run confound** — the bomb arm would differ from the
other two in *when and under which seed it was produced*, not only in concept, and any bomb-vs-rest
asymmetry would be uninterpretable. **All three harm pools are therefore regenerated in one
family**, same generator, same hints, same seed 20260906, differing only in the concept word
passed to `gen_demos`. The cost is one extra CPU job.

Consequence to record: `ts116n`'s bomb harm pool will **not** equal `demo_pools_116dom.json`'s, so
`ts116n` is a self-contained family and must not be joined to `cds116` or `ts116` on content.

**Jobs submitted** (CPU, `cpu-killable`, mutually independent, well inside the concurrency cap):

| concept | job | output |
|---|---|---|
| bomb | **859722** | `data/boombness_prompts/demo_pools_116dom_ts_bomb.json` |
| knife | **859723** | `…_ts_knife.json` |
| gun | **859724** | `…_ts_gun.json` |

Estimated ~3 h each from the smoke's per-domain cost; `--time=08:00:00`.

**Gates before the rebuilt banks may be used for anything:**
1. all three pool files verify (shared valences byte-identical; every harm sentence carries
   exactly one whole-word target concept and **no other concept**);
2. `A-037` concept-backing re-run on `ts116n` — the mass-noun polysemy frame
   (`restaurant_kitchen` 40/40 on the old pools) and the 18.56 % hedging rate are properties of a
   *generated corpus* and must be re-measured, not inherited;
3. `A-038` leakage re-run — on `ts116n` its baselines become informative rather than degenerate,
   and **template-id-at-chance is the check that fails loudly if alignment breaks**;
4. the cell-C occurrence check that `C-074` was missing: **count how many rows actually differ
   across concepts**, and require cell C × `semantic_one_word` to differ in
   **116/116 domains** — the exact inverse of the 1,856/1,856 identity that voided `R-098`;
5. cells A (benign) must remain byte-identical across concepts, which is the alignment half.

Gate 4 is the one that would have caught `C-074` on day one, and it is now a required gate rather
than a lesson.

## 2026-09-07 · PR-046 · the flagship probe, preregistered before the bank exists

`configs/dcs_ts_pr046.json`. Written at commit `347f0920`, **before any `ts116n` row, hidden
state or outcome exists**. Status `FROZEN_PENDING_BANK_SHA`: every `*_sha` field is `null` and the
analyzer **refuses to run** while any of them still is. Pinning happens when the banks are built,
which is still before extraction — so no outcome can exist at the moment the design is frozen.

**Why it is a JSON and not a paragraph.** This repository has twice published a threshold that no
code path ever read. Every gate here is loaded by the analyzer at runtime, and the analyzer
refuses to start if the file is missing, if a sha is null, or if a gate it needs is absent. *A
number in a markdown log that no program consults is a wish, not a preregistration.*

**Question.** In a large, aligned, held-out population, does the codeword's hidden state carry the
**identity** of the installed concept, beyond generic remapping and generic harmfulness?
(Mandate §32 CLAIM A.)

**Design.** Cell **C**, `semantic_one_word`, `n_examples=4`, classes {bomb, knife, gun}, multinomial
logistic regression on `codeword_last`. Train on the 70 TRAIN domains; select layer and `C` on the
23 VALIDATION domains only; read the 23 TEST domains once. Primary statistic: domain-mean 3-way
accuracy against chance 1/3, **domain-level group permutation, `n_perm = 10000`**.

Details that exist only because something went wrong before:

- **Select on `cell == "C"`, never on `condition == "natural_doublespeak"`.** That string lives in
  `condition`; selecting the wrong field **binds zero rows** (found by `A-039`).
- **Every p is published next to its floor**, `1/(B+1) = 9.999e-05`, and zero exceedances are
  reported as `p < 1/(B+1)` rather than a bare number. The previous headline `p = 0.004975`
  *was* the floor at `B=200` and was read as a measurement.
- **`SELECTION_TRACE.inert` and `n_tied_at_best` are persisted in every artifact.** A saturated
  selection surface is reported as a grid-order tie-break, never as learned localisation
  (`C-070`).
- **Row-level p-values are not reported for this claim.** ICC 0.0884 → DEFF 6.22; a row-level p
  would print `1.02e-06` where the honest domain-level p is 0.05.
- **`school_campus` is excluded prospectively** from occurrence-ordinal and all-codeword-sites
  analyses only (`C-075`), and *not* from the probe, whose read site is unaffected.
- **Non-installing domains are not dropped.** Installation is a preregistered stratification
  variable and a stated limit (mandate §15).
- **Doses are never pooled** into one p-value.
- **Llama-only by decision**, recorded as a scope limit and not as a model-specificity claim.

**Eight required nulls** (N1–N8), including the `n_examples=0` null, domain-level permutation
(never row-level: measured FPR 0.2000), a concept-masked TF-IDF baseline the probe must beat, and
**N6, the template-id-only classifier, which must sit at chance by construction — above chance
means alignment is broken and the run is VOID.**

**Five PHASE-4 gates on `ts116n` (G1–G5), and a kill condition.** **G2 is the one that matters:**
cell C × `semantic_one_word` must **differ across concepts in 116/116 domains** — the exact
inverse of the 1,856/1,856 identity that voided `R-098`. **If G2 fails, no extraction is
submitted.** That gate exists so this class of error costs CPU instead of GPU, which is what it
cost last time only because the PHASE-4 audits happened to be mandated.

**Flip trigger, checkable on TRAIN alone before any test read:** if the 70-domain nested-LODO
between-domain SD exceeds 0.25, or train-LODO mean accuracy is below 0.55, the split is rebuilt as
58/29/29 *before* the confirmatory run. Recorded because the projected SD 0.1406 rests on five
degrees of freedom, and at its 95 % upper bound the MDE degrades from 0.0925 to 0.2102.

**Generation progress at the time of writing:** jobs 859722/3/4 at ~10 of 116 domains after 5:21,
i.e. roughly an hour to completion — the smoke-based 3 h estimate was pessimistic because the
per-domain cost excludes the one-time interpreter and API import.

## 2026-09-07 · R-100 · the `ts116n` harm pools are generated, and two of three failed their own gate

Jobs 859722 (bomb), 859723 (knife), 859724 (gun), `cpu-killable`, 15:34–17:08 each. All three
produced **116/116 domains × 40 sentences**. Knife exited `COMPLETED 0:0`; **bomb and gun exited
`FAILED 1:0` — on their own verifier, not on generation.** The files were written; the exit code
is the gate refusing to certify them.

| concept | `content_sha16` | verifier |
|---|---|---|
| bomb | `9dcaed6e32f30065` | **FAIL** — 1 sentence names another concept |
| knife | `1f164f69d2f17a9e` | PASS — 348 shared pools byte-identical, 116 harm pools clean |
| gun | `a68ab2ceef4144b7` | **FAIL** — 1 sentence names another concept |

**What it caught**, both in `restaurant_kitchen`, a domain where knives are the natural furniture:

> bomb[39] — *"A misplaced **knife** on the edge of the counter was a potential **bomb** hazard."*
> gun[19] — *"A light-hearted debate broke out about whether a **gun** or a **knife** is the better
> tool for a chef."*

Two sentences out of 13,920. Exactly the concept-substitution failure mandate §6.5 asks for, and
it was caught by a **prompt-only** check with no model outcome involved.

**Repair, chosen to preserve symmetry rather than to minimise work.** `restaurant_kitchen|harm` is
regenerated at seed **20260907** for **all three concepts**, not only the two that failed — jobs
859813/859814/859815. Knife's pool for that domain is clean, and regenerating a clean pool is
extra churn; it is done anyway so that no concept's pool for that domain comes from a different
seed than the others. Recorded explicitly: this is regeneration until a **prompt-only,
preregistered, outcome-blind** contamination check passes. It is not regeneration until a result
looks good, and the number of seed bumps is logged.

### The asymmetry this surfaced, which no gate was asked to look for

Measured over all 4,640 harm sentences per concept:

| | bomb | knife | gun |
|---|---|---|---|
| hedged (*resembl\*, simulat\*, drill, false alarm, looks like*) | **14.1 %** | **0.2 %** | 3.4 % |
| mass-noun polysemy frame `a <W> of <NOUN>` | 1.08 % | 0.00 % | 0.00 % |
| mean sentence length (chars) | 82 | 75 | 78 |
| dropped for `occurrence != 1`, median | 6 | 5 | 7 |

**The hedging gap is 70×, and it is not a generation artifact.** A bomb in a workplace is
overwhelmingly a *suspected* bomb — a scare, a resemblance, a drill; a knife is simply present.
That difference is a real property of how the two concepts occur in incident-log English, and it
is therefore part of what "installing bomb rather than knife" *means* in natural demonstrations.

**It cannot be removed without recreating the error this design exists to fix.** Equalising the
registers means making the demonstrations unnatural — and demonstrations that differ only
cosmetically are how `R-098` ended up with no manipulation at all. So it is kept, measured, and
made into the bar rather than hidden:

- the concept-masked **TF-IDF baseline (N5)** will now be strong, and **the probe must beat it**;
- the **length-only baseline (N4)** may be above chance for the first time — mean length differs
  by ~7 chars per sentence, ~28 per 4-demo block. **N4's value is now an outcome to report, not a
  formality to pass.**

**A decision deferred to measurement rather than taken now:** if N4 comes out well above chance,
the fix is to over-generate and length-match the 40 kept sentences per pool — a prompt-only,
outcome-blind matching step. That costs ~50 % more API and about an hour. **It will be decided on
N4's measured value, before the probe is ever run**, and the decision rule is recorded here in
advance so it cannot be made after seeing the probe.

Good news buried in the same table: the mass-noun polysemy frame that hit `restaurant_kitchen`
**40/40** on the old shared pools (`A-037`) is down to **1.08 % / 0 % / 0 %**. The `A-037`
blacklist was derived from the old corpus and **must not be inherited** — `G4` re-measures it, and
on current evidence the 6-domain blacklist and the 33-domain "clean set" largely dissolve, which
protects the thesis-scale n.

→ **`Q-011` (new, for Omer):** the three concepts differ in discourse register (bomb is discussed
as a threat and a suspicion; knife as an object). Is that (a) part of the concept and therefore
legitimately part of the manipulation, or (b) a confound to be matched away at the cost of
naturalness? **This phase proceeds on (a), with the register difference measured, published, and
converted into a nuisance baseline the probe has to beat.** Flagged because it is the single most
likely thing Matan will press on, and because the honest answer is that it is not fully separable.

## 2026-09-07 · R-101 · **`ts116n` exists and passes every gate. `C-074` is repaired.**

Six banks, `{button, basket} × {bomb, knife, gun}`, preset `main_longpre_cds_ts`, seed 20260901,
unified repair map, **0 alignment violations and 0 duplicate `prompt_id`s in all six**.

| bank | `bank_rows_sha16` | `bank_file_sha16` |
|---|---|---|
| button_bomb | `9d1f03747189e1bd` | `42341368bdbe6ebc` |
| button_knife | `9ef9688609001104` | `a47b3da02998f79f` |
| button_gun | `b865d8b991023ac7` | `8e91fd0a2b53140c` |
| basket_bomb | `09882763cb4b0a24` | `d459fbd4259eef62` |
| basket_knife | `71128bfa7631c005` | `ffa88f1816492759` |
| basket_gun | `ab5ec1d45fb90cd3` | `23e6df6802023e0f` |

**Gates G1–G3: 19/19 PASS. Mutation harness: 4/4 RED.**

| gate | result |
|---|---|
| G1 shared valences byte-identical to `demo_pools_116dom.json` | **348/348** pools, each concept |
| G1 exactly one whole-word target concept per harm sentence | 115 harm pools, **0** violations, each concept |
| G1 no other concept named | **0** sentences, each concept |
| **G2 cell C × `semantic_one_word` DIFFERS across concepts** | **115/115 domains**, both codewords, knife and gun, over 1,840 rows each |
| **G3a cell A concept-free channels byte-identical** | **3,680/3,680** rows, both codewords |
| G3b forced-choice demos + preamble identical | 1,840/1,840 |
| G3b forced-choice query differs ONLY by the concept noun | 1,840/1,840 restore exactly under `concept→bomb` |

**G2 is the sentence that matters.** The population that was `1,856/1,856 identical` under `R-098`
is now **115/115 domains differing**, while `G3a` holds byte-identity at 3,680/3,680. The
manipulation exists *and* everything that is not the manipulation is shared. That is the matched
pair, and neither half is allowed to pass alone.

### A gate I corrected rather than relaxed

G3's first version demanded byte-identity on **every** cell-A row and failed at exactly
**3,680/5,520 = 2/3**. The differing third is entirely `semantic_forced_choice`, whose *question*
names the concept by construction:

> *"does the word button refer to a button or to a **bomb**?"* vs *"… or to a **knife**?"*

That is the readout instrument, not the demonstrations — and it is precisely the property that
makes forced-choice the **display** channel and `semantic_one_word` the **mechanistic** one.
Conflating them made G3 test something it never meant to test. It is now split: **G3a** asserts
byte-identity on the concept-free channels (what "everything else is shared" actually means), and
**G3b** *bounds* the forced-choice difference — demo block and preamble identical, and the query
must restore exactly under substitution. **G3b is a new obligation, so the pair is strictly
stronger than the single gate it replaces.** Recorded in full because "the gate failed so I
changed the gate" is a move that deserves scrutiny, and the reader should be able to check that
this one added a requirement rather than dropped one.

### The population, final

**115 domains: 69 train / 23 validation / 23 test.** `restaurant_kitchen` is excluded from the
whole analysis, prompt-only and prospectively — a kitchen has knives as natural furniture, so bomb
and gun pools generated for it keep naming a knife, and a second seed cleaned bomb and knife while
leaving gun contaminated again. That is the domain, not the draw; a third bump would have been
selection rather than repair. Excluding it makes all three **original uniform-seed-20260906** pools
fully clean — **0 contaminated sentences out of 13,920** — so every surviving domain comes from one
generation family at one seed, which is strictly better than a per-domain patchwork. It sits in
TRAIN, so **validation and test stay at 23/23 and the power analysis is unchanged.**

**`PR-046` is now `FROZEN`**, with every bank hash pinned and the gate results recorded in the
config the analyzer reads. It was written before the bank existed and is frozen before any hidden
state does.

### Still required before extraction

- **G4** concept-backing audit re-run on `ts116n` (the `A-037` blacklist was derived from the old
  corpus and must not be inherited — early evidence says the mass-noun frame collapses from
  3.69 % to ~1 %);
- **G5** leakage audit re-run, where the baselines finally become informative rather than
  degenerate — **N4 length-only is now an outcome to report**, given the measured register
  asymmetry, and its value triggers the length-matching rule already recorded in `PR-046`;
- the **planted-hook layer-convention test**, which is the first GPU job of the phase and must
  pass before any measurement.

## 2026-09-07 · A-041 · gates G4 and G5 on `ts116n`: one CRITICAL, one trigger fired

`reports/DCS_TS116N_CONCEPT_BACKING_AUDIT.md` (21 checks, 21 mutations, 21/21 RED),
`reports/DCS_TS116N_LEAKAGE_AUDIT.md` (29 checks, 16/16 mutation targets RED),
`reports/DCS_TS116N_ADVERSARIAL_AUDIT.md`.

### The good news first, because it is the thing the rebuild was for

**The positive control that the old bank scored zero on now passes.** A strict 3×3 affordance
matrix is diagonal-dominant: bomb 374 (4.07 %), knife 520 (5.65 %), gun 282 (3.07 %), with largest
off-diagonals 2, 6 and 8. And tier-1 explosive predicates are now **bomb 4.07 %, knife 0.00 %,
gun 0.09 %** — where the old bank read 4.27 % for all three *because they were the same
sentences*. The concepts are genuinely different concepts.

Other clean results: cell C differs in 115/115 domains × both codewords (460 comparisons, 0
identical); cell A byte-identical; **N6 template-id-only = 0.3333 / 0.5000, z = 0.00** — alignment
intact, the run is **not** VOID; **N1 n_examples=0 = exactly 0.3333 / 0.5000 on every baseline**,
so the signal localises entirely to the demonstration block; cross-domain verbatim sentence
leakage **down from 72/3,864 (1.86 %) to 8/1,380 (0.58 %)**; splitting `full_prompt` on
`demo_block` gives prefix and suffix identical in 1,150/1,150.

### C-076 — CRITICAL: the codeword substitution is singular-only

`demo_pools._clean` keeps a sentence with exactly one match of `\bWORD\b`, and `build_demo_block`
substitutes exactly that form. A sentence carrying **both** `knife` and `knives` therefore passes
the filter with a count of one, and only the singular is rewritten — shipping the literal plural
into **cell C, the one cell whose entire purpose is that the concept word does not appear**:

> `blood_bank[5]` — *"The **button** rack was overcrowded, making it difficult to access clean
> **knives**."*

**8 distinct sentences, 30 of 3,680 primary-channel rows, in 6 domains spanning 3 train,
1 validation and 2 test.** That is an outright label in the probe's own population — not a
register effect, and not something masking fixes.

Verified independently before acting: 8 in knife, **0 in bomb, 0 in gun**. The defect is *general*,
not knife-specific — nothing in the filter counts `bombs` either; knife merely exposed it because
`knives` is an irregular plural that is common in storage and kitchen contexts.

**Fixed at the filter, not by deleting rows.** `CONCEPT_FORMS` now lists every surface form
explicitly (irregular plurals enumerated, not guessed from a suffix rule) and `_clean_strict`
requires exactly one occurrence **counting all of them**. Confirmed to catch all 8 when run
against the existing pools. Deleting the offending sentences was rejected: `_take` slices pools
positionally, so removing a sentence silently changes which sentences every family slot in that
domain draws.

### C-077 — the N4 length trigger fired, and the preregistered rule is being followed

**N4 length-only = 0.4174 accuracy / 0.5750 macro AUROC, z = +6.62** against chance 1/3
(cell-A control 0.3333/0.5000). Mean prompt length: bomb 1085.7, gun 1074.3, knife 1055.0 chars.
That is well above chance, so the rule written into `configs/dcs_ts_pr046.json` **before N4 was
measured** fires: over-generate and length-match.

`scripts/dcs_ts_length_match_pools.py` selects 40 of 60 candidates per (domain, concept) against a
**shared** pooled-length quantile profile — deterministic greedy nearest-length, no RNG, no model
output, emitted in original candidate order so family slots do not depend on the matching walk.
Candidate generation is running (jobs 859978/859979/859980) with the `C-076` filter in place, so
one regeneration fixes both defects.

⚠ Recorded now: matching the marginal length distribution removes a first-order confound, it does
not make the arms identical. **N4 will be re-measured on the rebuilt bank and reported at whatever
value it takes.** If it is still well above chance, that is a finding about the corpus — not a
reason for a third round.

### C-078 — my own preregistered bar was miscalibrated, and I am saying so before running the probe

`PR-046` requires the probe to beat the strongest nuisance baseline, and G5 nominates
**N5c, concept-masked TF-IDF over the demonstration block = 0.8870 / 0.9829**.

**That is the wrong bar for the claim, and I wrote it.** A bag-of-words over the demonstration
text recovers the concept at 88.7 % because *we generated concept-specific demonstrations* — the
demo block is the **treatment**, not a nuisance. Requiring a representation probe to beat a text
classifier reading the treatment sets a bar no representation probe could ever clear, since the
hidden state is a deterministic function of that same text. Mandate §6.6's nuisance-baseline rule
was written for *shortcuts* — length, template id, prompt scaffolding — and N5c is not one.

Handling it by the mandate's own rule (§21: *new design = new preregistration*) rather than by
quietly moving the threshold:

1. **`PR-046`'s N5c comparison stands and will be reported at whatever value it takes**, with this
   entry cited. A preregistered comparison is not deleted because it turned out to answer a
   different question than intended.
2. **`PR-047` will preregister the comparison that actually tests Matan's question**, which is
   about a *position*, not about a prompt: **is concept identity more decodable at the codeword's
   representation than at matched control positions in the same prompt?** *"The codeword is
   becoming represented as BOMB"* is a localisation claim. A text classifier has no position and
   therefore cannot speak to it; a position-matched probe contrast can.

This is written **before any probe has been run and before any hidden state exists**, which is the
only thing that distinguishes it from moving a goalpost. Had I noticed after seeing the probe fall
short of 0.887, the honest options would have been far worse.

### Carried, not yet resolved

- **3 knife/gun sentence pairs are byte-identical once the weapon noun is neutralised**
  (`wind_farm`, `news_report`, `sports_stadium` — *"…brandishing a knife/gun during a heated
  argument"*). 0 byte-identical shared sentences. Arguably a *feature* — matched frames — but
  recorded.
- **Register remains the live limit.** Hedge-only (5 regexes) reaches 0.4768/0.6350 and never
  predicts gun at all; register-only (16 features) 0.4406/0.6277; combined 0.5174/0.7159. This is
  `Q-011`, and length-matching does not touch it.
- The G4 verdicts stand as **bomb / gun USABLE WITH STATED LIMIT** and **knife NOT USABLE AS
  BUILT** — the latter cleared by `C-076`'s regeneration, which is in flight.

## 2026-09-07 · C-079 · a third instance of one bug class, and the pattern is now named

Building `ts116m` from the length-matched pools **refused under `--strict` with 170 alignment
violations and wrote nothing.** Two distinct defects, found in sequence, both mine, both in the
`C-076` fix itself.

**First: my C-076 fix opened the opposite hole.** Requiring *"exactly one occurrence counting
inflections"* admits a sentence whose sole occurrence is the **plural** — *"Several bombs were
found in the loading bay."* `build_demo_block` substitutes only the singular, so such a sentence
survives assembly **unchanged** and contributes **zero** codeword occurrences. Violation shape:
`{benign_literal: 5, direct_harmful: 4, natural_doublespeak: 4, concept_in_benign_ctx: 5}`. The
old filter let plural-*contaminated* sentences through; mine let plural-*only* sentences through.

**Second, after fixing that, 4 violations remained — all in `restaurant_kitchen`:**

> `A container marked "**bOMB**" was found, but its contents were safe.`

A **case-insensitive** occurrence check counts that as one occurrence. `_substitute` enumerates
only `bomb`, `Bomb`, `BOMB`, so it rewrote nothing.

**The pattern, named because it has now cost three corrections in one phase:**

> **THE CHECKER'S NOTION OF "AN OCCURRENCE" MUST BE EXACTLY THE TRANSFORMER'S.**
>
> | | the checker said | the transformer did |
> |---|---|---|
> | `C-075` | right-permissive (`basketball` counts) | exact word only |
> | `C-076` | singular only | singular only — but the text carried `knives` |
> | `C-079` | case-insensitive | three enumerated case forms |
>
> Every time the two disagreed about what counts as an occurrence, and every time the
> disagreement was **silent** until something downstream refused.

The filter now mirrors `_substitute` exactly: one occurrence case-insensitively across all
inflections (so a second, unrewritable occurrence is rejected) **and** one occurrence
case-*sensitively* over exactly the three forms the substituter rewrites. Applied in both the
generator and the length matcher, so candidate pools generated before the rule existed are still
usable — every domain retained ≥50 usable candidates against the 40 needed, so **no regeneration
was required**.

**`--strict` did its job.** It refused, removed its temporaries, and left no bank at the target
path for a downstream step to pick up. Three defects that would each have silently corrupted the
primary cell were caught by a build-time invariant rather than by a reviewer.

## 2026-09-07 · R-102 · `ts116m` is built and gated; the length remedy did **not** work

Six banks, 115 domains, **0 alignment violations, 19/19 gates PASS, 4/4 mutations RED.**

| bank | `bank_rows_sha16` |
|---|---|
| button_bomb | `9c0dcd1e6c6cf6c1`* |
| button_gun | `c7ceb5a151a2788a` |
| basket_bomb | `1e872cd8cd2f63a5` |
| basket_knife | `61e586e4bdca6f28` |
| basket_gun | `f1a8332bdd7c48ce` |

\* full table pinned into `configs/dcs_ts_pr046.json` at the next freeze.

**The `C-076` fix is confirmed on the artifact: `0 / 6900` probe rows print their own concept
word**, against 30/3680 before. The plural leak is gone from the primary channel.

### The honest negative

**N4 length-only: 0.4174 → 0.4014 accuracy; macro AUROC 0.5750 → 0.5793.** The AUROC went
*slightly up*. Length matching cut the cross-concept mean sentence-length spread by 40.8 %
(7.03 → 4.16 chars) and moved the length baseline by **0.016 accuracy**.

**The remedy did not work, and per the rule recorded before N4 was ever measured, there is no
third round.**

Why it failed, diagnosed rather than waved at: I matched the **marginal** length distribution of
each pool, but `N4` reads `n_chars` of the **full prompt**, whose demo block is four sentences
drawn by `_take` at fixed slot offsets. Matching pool marginals does not match per-family sums,
and matching at the family level would require choosing which sentences co-occur — which
`_take`'s positional slicing exists to keep fixed. **The fix addressed the wrong level of
aggregation.** That is a real limitation of the remedy, not of the measurement.

### The full nuisance picture on `ts116m`, which is now the honest bar

| baseline | acc | macro AUROC |
|---|---|---|
| N6 template-id (probe pop) | **0.3333** | **0.5000** (z = 0.00) |
| N6b template-id (all cell C, 6,624 test rows) | **0.3333** | **0.5000** |
| N1 `n_examples=0`, all four baselines | **0.3333** | **0.5000** |
| cell-A controls (length, TF-IDF, hedge+register) | **0.3333** | **0.5000** |
| N4 length-only | 0.4014 | 0.5793 |
| H2 register-only (16 features) | 0.3942 | 0.5943 |
| H1 hedge-only (5 regexes) | 0.4739 | 0.6374 |
| H3 hedge + register | 0.5014 | 0.6929 |
| N5b TF-IDF full prompt, concept-masked | 0.9014 | 0.9837 |
| N5c TF-IDF demo block, concept-masked | **0.9217** | **0.9924** |

**Read this correctly.** The four exact-chance rows are the ones that would scream if the bank
were broken, and they are all silent: template identity carries nothing, the zero-dose null
carries nothing, and the benign cell carries nothing. What *does* carry the label is the
demonstration text itself — at 0.92 — which is the **treatment**, exactly as `C-078` argued before
any of these numbers existed.

So the phase's position is unchanged by these numbers, which is the point of having written it
down first: **surface text predicts the concept, and that was never in doubt.** The open question
is whether the *codeword's representation specifically* carries it — a question about a position,
which no text classifier can answer. `PR-047` is where that gets tested.

Carried as live limits, not resolved: **register** (H3 = 0.5014) is `Q-011`; **length** (N4 =
0.4014) is now a permanent stated nuisance rather than something we will keep attacking.

---

# 2026-09-07 · A-042 · FOUR-HOUR FULL REVIEW #1 (mandate §29)

Four independent read-only lenses over `b80db84d..e4d78bf0`: code, data, output/process, science.
Reports: `reports/DCS_TS_REVIEW1_{CODE,DATA,OUTPUT,SCIENCE}.md`. It found **three CRITICALs, one
retraction of a published claim, and one retraction of my own reasoning.** Everything below is a
correction *to this phase*, not to inherited work.

## C-080 · **the G1 gate was itself blind. `R-101`'s "19/19 PASS" is RETRACTED.**

`dcs_ts_verify_ts116n.py` counted the own-concept occurrence as `\bknife\b` — singular,
case-insensitive — and therefore printed *"0 sentence(s) not exactly one whole-word 'knife'"* over
a pools file carrying **eight** `knife`+`knives` sentences. The generator's own verifier reported
8 failures on the same bytes at the same time. **`R-101` was a green verdict from a gate that
could not see `C-076`**, and it is the gate the build script names as required before extraction.

**This is the FOURTH instance of the class named in `C-079`** — and the first one inside a gate
rather than a producer, which is worse, because a blind gate manufactures confidence:

| | the checker said | the transformer did |
|---|---|---|
| `C-075` | right-permissive (`basketball` counts) | exact word only |
| `C-076` | singular only | text carried `knives` |
| `C-079` | case-insensitive | three enumerated case forms |
| **`C-080`** | **singular, case-insensitive — in the GATE** | **both of the above** |

Fixed by sharing one rule across generator, matcher and gate instead of restating it three times.
**Re-run with the corrected gate:**

| family | result |
|---|---|
| `ts116n` (the one `R-101` certified) | **18/19 — G1[knife] FAILS with the 8 sentences** |
| `ts116m` (the live family) | **19/19 PASS, 4/4 mutations RED** |

So the retraction lands on a bank already superseded, and `ts116m` now passes a gate that has been
demonstrated capable of failing. That is the only reason the retraction is cheap.

## C-081 · **the `n_examples=0` null cannot fail, and my inference from it was wrong**

With no demonstrations the three concept arms are **the same prompt** — 230/230 byte-identical.
A probe there is pinned to 1/3 **by arithmetic**, which is `C-074`'s argument verbatim, applied to
my own control. N1 landing at exactly 0.3333 on all four baselines is therefore a **pipeline
sanity check, not evidence about the model.**

**Retracted:** my sentence in `A-041` that *"the signal localises entirely to the demonstration
block."* It does not follow from N1. N1 is demoted from the evidence list in `PR-048` and kept,
labelled, as a sanity check.

## C-082 · **"that is the domain, not the draw" is UNSUPPORTED**

The `restaurant_kitchen` regeneration retried with `for rnd in range(14)` over `seed + rnd`. Seed
20260906 spans 20260906–20260919; the "second seed" 20260907 spans 20260907–20260920. **They share
13 of 14 OpenAI seeds.** The second attempt was very nearly the same draws, so its failing again
says little about the domain and much about the overlap.

The **exclusion stands** — it is preregistered, prompt-only, and costs one TRAIN domain — but its
stated *reason* was overclaimed and is corrected here. Lens B further finds `restaurant_kitchen`
is **clean in the new pools (0/40 on all three concepts)**, so the exclusion is now **conservative
rather than necessary**. It is kept anyway: reversing a preregistered exclusion, even toward more
data, is a move I would rather not have to defend.

## C-083 · **cross-split leakage got 5× WORSE, not better**

TEST harm sentences appearing verbatim in a TRAIN domain, under the frozen split:
`ts` pools **3/2,760 (0.109 %)** → `tsm` pools **15/2,760 (0.543 %)**. Length matching selects a
different 40 of 60, and it selected more shared sentences. `A-041`'s "1.86 % → 0.58 %" compared a
different population and should not be quoted. Still small in absolute terms, now recorded as a
known property of `ts116m` rather than an improvement.

## B-020 · **the analyzer does not exist, and I said it did**

`configs/dcs_ts_pr046.json` names `scripts/dcs_ts_pr046_analysis.py`. **There is no such file.**
Every threshold in the preregistration — `alpha`, `n_perm=10000`, the p-floor rule, the MDE, the
flip trigger, the layer grid, all eight nulls and all five gates — is currently read by **no code
path**, and the log's claim that the analyzer *"refuses to start if a sha is null"* is prose I
wrote about code that was never written. That is precisely the *"thresholds published but never
enforced"* failure this project has recorded twice before, committed by me while citing it as the
reason to write a machine-readable preregistration.

**Writing the analyzer, with that refusal implemented and mutation-tested, is now a blocking
prerequisite for the first extraction**, recorded in `PR-048`.

Also fixed this tick, both verified by mutation:
- **`dcs_ts_preflight.sh` was gating the VOID `ts116` banks** — a green preflight said nothing
  about the bank a job would read, and deleting the void rows would have *blocked every
  submission* while instructing the operator to regenerate them. It now gates `ts116m` and runs
  the G1–G3 gates.
- **`BOOMB_EXPECT` did not close the `853040` hole.** Mistyping `ARGSFILE=` still leaves
  `BOOMB_ARGS` empty, and a job whose script happens to match `BOOMB_EXPECT` then runs the right
  script with **no arguments** and exits `COMPLETED 0:0` — the same invisible failure one step
  further along. Added opt-in `BOOMB_REQUIRE_ARGS=1`; proven to refuse on empty args and proven
  **not** to block a valid call.

## PR-048 · supersedes PR-046

`configs/dcs_ts_pr048.json`. **`PR-046` is left byte-frozen on disk and is not edited.**
**The design is unchanged** — population, split, model, read site, classifier, primary statistic,
alpha, `n_perm`, nulls, gates, power and kill condition are identical. Only the artifact it binds
to changed, forced by defect repair, with **no probe run and no hidden state in existence.**
It pins the six `ts116m` hashes, records N4's post-remedy value and the "no third round" ruling,
demotes N1, and records that the analyzer does not yet exist.

## What the review did NOT break, re-derived from bytes by lens B

Split: 116 keys, 70/23/23, 0 overlap, rebuilds from seed 202609061, `manifest_sha16` recomputes.
Hashes: 12/12 agree across `_meta.json` and the config. Balance: 22,272 rows/bank, 192 per domain
in all 116, the three concept banks carry *identical* row-identity key sets. Duplicates: 0 and 0
over 133,632 rows. `C-076`: 0 multi-occurrence in 34,800 new-pool sentences, and lens B's
independent detector finds exactly the 8 old ones. `C-074`: `ts116`'s primary channel confirmed
1,856/1,856 identical — the VOID verdict was correct. **20 of 21 load-bearing numbers in this log
reproduce exactly.**

## 2026-09-07 · A-042 (science lens) · three findings that change the design

The science lens produced the most valuable output of the review. Three things I had not seen.

### C-084 · **N4 was measured in the wrong unit, and my "the remedy did not work" was pessimistic**

The leakage audit reads **`n_chars`**. The model reads **tokens**.

| unit | N4 length-only accuracy |
|---|---|
| characters (what I reported) | 0.4014 |
| **tokens (what the model sees)** | **0.3623** |

Prompt token counts on `ts116m`: **bomb 196.21, knife 195.50, gun 196.69**, on a 13-token sd.
**The positional confound is essentially matched.** The character residual is lexical
composition — which is register again, not length.

`R-102`'s verdict *"the remedy did not work"* stands for characters and is **too pessimistic about
the quantity that matters**. Corrected here rather than left standing, because it understates the
bank. The honest statement: **length in tokens is not a live confound (0.3623 against 1/3);
register is.**

### C-085 · **my "strictly stronger" claim about the G3 split was false**

I wrote that splitting G3 into G3a/G3b made the pair *"strictly stronger than the single gate it
replaces."* It is **strictly weaker on 1,840 rows** — G3a simply does not examine the
forced-choice channel that old G3 demanded byte-identity from. The *change* was still correct,
because old G3 was unsatisfiable by construction, but the justification I gave for it was wrong.
Corrected.

### R-103 · **knife-vs-gun is the register-clean, length-clean contrast — and CLAIM A lives there**

The single most useful finding of the review. Register is not a uniform nuisance; it is a
**bomb-vs-rest severity axis**:

| contrast | hedge-only classifier buys |
|---|---|
| bomb vs knife | **+0.211** |
| **knife vs gun** | **+0.037** |

Threat-lexicon framing runs bomb 44.5 % / knife 14.0 % / gun 18.3 %. So the 3-way probe carries
bomb's register with it, while **the knife-vs-gun two-way contrast is clean on register *and* on
length** — and it is exactly a test of concept *identity* between two matched harmful concepts,
with no severity gradient to read instead.

**It is preregistered nowhere.** That is now the gap to close, and it costs **zero extra GPU** —
it is a re-analysis of the same extraction. A **hedge-free TEST stratum** also already exists in
the bank: 115 bomb / 212 knife / 195 gun rows, enough for a balanced 345-row re-analysis.

### The C-078 verdict, and the condition attached to it

The lens was asked to argue both sides of whether declaring my own preregistered bar
miscalibrated was legitimate. Its verdict: **legitimate as a correction** — the timing is
independently verifiable (no GPU has run, no hidden state exists, and N5c needs none), and
requiring a probe to beat a text classifier reading the *treatment* is a bar no true positive
clears.

**But it attached a condition I accept:** `PR-046` adopted N5 explicitly *as the answer to the
register confound*, and the positional contrast tests a **different proposition**. So —

> **legitimate correction, illegitimate if `PR-047` inherits N5's job.**

The register confound needs its own answer, not a change of subject. **`R-103` supplies exactly
that**: knife-vs-gun is register-clean by measurement, so it answers the question N5 was adopted
to answer, while the positional contrast answers localisation. Two questions, two instruments —
rather than one instrument quietly retargeted.

### The killer experiment, for a later preregistration

**The strongest remaining threat to CLAIM A is context-gist, not codeword binding**: the model may
represent "this prompt is about bombs" everywhere, with the codeword position carrying nothing
special. The lens's proposed test is better than anything in the current plan:

> a **within-prompt two-codeword interference bank** — `button`↔BOMB and `basket`↔KNIFE installed
> in the *same* prompt — read at **both** codeword positions in **one forward pass**. Identical
> gist, register, length and position band; **only the token differs.**

If each codeword's representation tracks *its own* installed concept, that is binding. If both
track the prompt's overall gist, that is context. Recorded now as the design to preregister after
the probe; not run yet, and not claimed.

### Process items that gate the science, carried forward

- `multiplicity` — a mandate §21 required field — is **missing** from the preregistration.
- the **token-role map and the `rel_end = −9` read-site nomination were computed on the VOID
  `ts116` bank** and must be recomputed on `ts116m` before extraction. Added to the pre-extraction
  checklist.
- `PR-048` records that the analyzer still does not exist (`B-020`).

## 2026-09-07 · X1 CLOSED · `B-020` is fixed: the preregistration is now actually enforced

`scripts/dcs_ts_prereg.py`. The claim I made in `PR-046` — *"the analyzer REFUSES to run if this
file is absent, if any `*_sha` field is still null, or if a gate it needs is missing"* — is now
**true**, having been false when written.

It is deliberately a **separate loader**, not part of an analyzer. An enforcement path that lives
inside one analyzer is bypassed by writing a second analyzer; this one is imported by anything
that reads a preregistration, so the refusals come for free and cannot be routed around.

**Refuses, all fail-closed:** config missing or unparseable · `status != FROZEN` · **any**
`*_sha16` anywhere in the tree null or empty · a pinned artifact absent from disk · a pinned
artifact whose **actual** hash disagrees with the pinned one · a mandate §21 required field
missing · `require_gate`/`require_null` asked for something undeclared · `require()` asked for a
threshold the config does not carry (no silent defaults) · and, under `for_extraction=True`, **any
BLOCKING pre-extraction checklist item that is not done**.

Verified on the real configs:

| target | result |
|---|---|
| `PR-048`, normal load | **clean** — 17 hashes pinned *and verified against disk*, all 12 mandate-§21 fields present |
| `PR-048`, `for_extraction=True` | **REFUSES** — `X3` planted-hook test is BLOCKING and not done |
| `PR-046` (superseded) | **REFUSES** — missing `multiplicity` |
| mutation harness | **6/6 refusals reachable** |

The `for_extraction` refusal is the one that matters: **an extraction cannot start while this
phase's own checklist is outstanding.** The guard now enforces the discipline rather than
describing it.

## 2026-09-07 · X3 · the first GPU job of the phase is running

Job **860158**, `n-804`, `killable`. The planted-hook layer-convention test
(`scripts/dcs_ts_layer_convention_test.py`), mandate §22.3.

`A-036` read the convention off eight code sites and found them consistent —
`block L == hidden_states[L+1]`, `hidden_states[0] == embeddings`. **That is a code reading, not a
test.** Eight files agreeing tells you the authors agreed. This phase has been bitten four times
by a checker whose notion of a thing differed from what the library actually does, and an
off-by-one here would silently move every read site by one layer.

Five assertions, each printing its measured delta rather than a verdict: a forward hook on block L
must move `hidden_states[L+1]` by exactly 1e3 (**T1**) and must **not** move `hidden_states[L]`
(**T2**) — together these *are* the convention, and if T2 is the one that moves it is off by one;
a **pre**-hook must move `hidden_states[L]` instead (**T3**, the opposite-direction control that
rules out "everything moves anyway"); an unhooked repeat must move nothing (**T4**); and at
`L = n_layers−1`, `forward_hidden()`'s last layer must **differ** from `out.hidden_states[-1]`
(**T5**), proving the post-final-norm substitution is real and not a no-op.

**The launcher guards worked in production on their first real use.** The job's opening lines read
`boombness: ../../scripts/dcs_ts_layer_convention_test.py`,
`boomb_script_origin: PROVIDED  expect=<same>  argsfile=runargs/dcs_ts_layerconv.args` — so
mandate §26.10's "verify the log says the expected script and args" is answered by `head` rather
than by inference, and `BOOMB_REQUIRE_ARGS=1` was set so an empty-args default run was impossible.

## 2026-09-07 · R-104 · X3 CLOSED · the layer convention is **confirmed by experiment**

Job **860184**, `COMPLETED 0:0`, 27 s. `outputs/dcs_ts/layer_convention.json`.

> **block layer L == `hidden_states[L+1]`; `hidden_states[0]` == embeddings — CONFIRMED.**
> Llama-3.1-8B-Instruct, `n_layers=32`, `len(hidden_states)=33`.

| check | measured |
|---|---|
| **T1** post-hook on block 12 moves `hs[13]` | **+1000.158** (kick 1000.0, tolerance 1.0) |
| **T2** post-hook does **not** move `hs[12]` | 0.000000 |
| **T3a** pre-hook leaves `hs[12]` | 0.000000 |
| **T3b** pre-hook moves `hs[13]` by a residual | +1000.158 |
| **T4** unhooked repeat | 0.000000 across all 33 entries |
| **T5** `forward_hidden`'s last layer ≠ `hidden_states[-1]` | **FAIL** |

The +0.158 is bf16 quantisation of a 1000.0 kick, not a discrepancy: at magnitude ~1000 the
bfloat16 grid is coarse, and the post- and pre-hook routes land on the same representable value,
which is why both read 1000.158.

**The first run of this test (job 860158) failed, and the fault was mine.** The return-based
post-hook moved nothing, and my T3 asserted that a pre-hook would move `hs[L]` — it cannot,
because `hs[L]` is appended to the tuple *before* block L is called. Run 1 refuted my expectation,
not the model. Fixed by an **in-place** post-hook (immune to whether the block returns a tuple and
to where the tuple is collected) and a corrected, split T3. **The convention is credited to the
direct post-hook pair T1+T2; the pre-hook result is corroboration and is labelled as such** — a
corroborating observation is not the experiment.

This closes mandate §22.3 for this phase. Eight code sites agreeing was never evidence; now there
is evidence.

### The one real failure, recorded rather than waved away

**T5 FAILED:** `extract_boombness.forward_hidden` raises *"Could not locate transformer layers on
this model"* on Llama-3.1-8B under transformers 5.12. `A-036` established that
`L = n_layers − 1` is correct **only** through `forward_hidden`, because the library ties the last
tuple entry to `last_hidden_state` (post-final-norm). So **the last layer is currently unreadable
by the sanctioned path.**

This phase reads the **6–14** band, so it does not bite here. It is recorded as an open defect in
`PR-048`, and **any future last-layer read is blocked on it** rather than being allowed to
silently read a post-norm tensor believing it is a block output.

### The extraction gate is still shut, correctly

With `X3` marked done, `dcs_ts_prereg.py --for-extraction` still **refuses**:

> `artifacts.analyzer_exists is false -- refusing to extract behind an analyzer that does not exist`

Exactly the behaviour `B-020` was fixed to produce.

## 2026-09-07 · PR-049 · X5 CLOSED · the register-clean co-primary

`configs/dcs_ts_pr049.json`, FROZEN, companion to `PR-048`. **Zero extra GPU** — a re-analysis of
the same extraction on the same rows.

**Primary: knife vs gun, 2-way, chance 0.5**, domain-mean accuracy on the 23 untouched TEST
domains, domain-level group permutation at `n_perm = 10000`.

**Why this contrast and not the 3-way.** `A-042` measured that register is a **bomb-vs-rest
severity axis**, not a uniform nuisance:

| contrast | hedge-only classifier buys |
|---|---|
| bomb vs knife | **+0.211** |
| **knife vs gun** | **+0.037** |

The 3-way primary carries bomb's discourse register with it. Knife-vs-gun is clean on register
*and* on length, and is still exactly a test of concept **identity** between two matched harmful
concepts — with no severity gradient available to read instead.

**It discharges the condition the review attached to `C-078`.** `PR-046` adopted the N5 text
baseline explicitly *as the answer to the register confound*. `C-078` then argued — before any
probe ran — that N5 is the wrong bar because the demonstration block is the **treatment**. The
review's verdict was *legitimate correction, illegitimate if the positional contrast inherits N5's
job.* **It does not.** The positional contrast answers localisation; this preregistration answers
register. Two questions, two instruments.

**Three blocking items, and a kill condition declared before the measurement that could trigger
it:**

- **Y1** — recompute power for a **2-way estimator at chance 0.5**. `PR-048`'s analysis was
  computed for a 3-way contrast at 1/3 and **does not transfer**. If power < 0.8 for a meaningful
  effect, this contrast is declared **exploratory rather than co-primary** — decided before the
  outcome.
- **Y2** — re-derive the hedge-free stratum row counts on `ts116m`. The 115 / 212 / 195 figures
  come from a **superseded corpus** and may not be quoted.
- **Y3** — re-measure the hedge-only and register-only baselines **restricted to knife-vs-gun** on
  `ts116m`, to confirm the +0.037 that is this contrast's entire rationale.

> **KILL CONDITION.** If `Y3` shows the hedge-only advantage on knife-vs-gun exceeds **+0.10**,
> the contrast is not register-clean, its rationale fails, and it is **withdrawn rather than
> reported** — with the register confound returning to being an open limitation with no
> instrument. Declared before `Y3` is measured.

`bomb-vs-knife` and `bomb-vs-gun` are retained as secondaries and **explicitly flagged
register-contaminated**: they may not be quoted as evidence of concept identity without that
caveat.

**Checklist status:** X1 done · X2 running · X3 **done (R-104)** · X4 running · X5 done.
The extraction gate still refuses on `analyzer_exists = false`, which is correct.

## 2026-09-07 · X1 CLOSED (properly) · the frozen analyzer, and C-086

`scripts/dcs_ts_pr048_analysis.py`, committed **before any `ts116m` hidden state exists** —
mandate §21. The circularity is deliberate: the analyzer must exist before the data, and
extraction cannot be submitted until it does.

**It contains no numeric gate literal.** `alpha`, `n_perm`, the chance level, the grids, the
split, the population filter and the exclusions are all fetched through `Prereg.require()`, which
**refuses rather than defaulting** when a key is absent. `B-020` was the failure of publishing
thresholds no code path reads; the fix is not to copy them into the analyzer but to make the
analyzer *unable to run without them*.

Selftest: **11/11 guards reachable** — the permutation floor is labelled and a non-floor p is not;
the n=6 sign-test floor computes to exactly 0.03125 (so the old 6/6 was worth 0.031, not 0.005)
while n=23 is below 1e-6; a sign test over zero domains, a permutation over an empty null and a
selection over an empty grid all **raise** rather than returning a number; a saturated selection
surface is flagged `inert` with the `C-070` warning while a genuine surface is not; and both
preregistration refusals fire through the real loader.

### C-086 · my extraction gate opened while two blocking items were outstanding

Having marked X1 done, I checked the gate and it **passed** — with X2 and X4 still running. The
guard was:

```python
if "BLOCKING" in st.upper() and "done" not in st.lower():
```

against a status string of **`"BLOCKING, not done"`**. `"not done"` *contains* `"done"`, so the
predicate was `False` and an outstanding blocker sailed through. **The gate written specifically
to stop extraction starting early would not have stopped it.**

This is the same family as `C-075`/`C-076`/`C-079`/`C-080` — a check whose notion of a thing was
not the thing — and the sixth in this phase. The fix is **structural, not a better regex**:
`blocking` and `done` are now **booleans**, and a checklist item that fails to declare them as
booleans is *itself* a refusal, so an item cannot slip through by being malformed. Prose status
strings are kept for humans and are no longer read by the guard.

Caught by checking the gate's answer against the checklist **by hand** rather than trusting it —
which is the only reason it was caught at all, and an argument for continuing to do that.

With the fix, the gate refuses:

> `pre-extraction checklist X2 is BLOCKING and not done: 'recompute the token-role map and the
> read-site nomination on ts116m -- the rel_end=-9 nomination was computed on the VOID ts116 bank'`

**X4 tightened to blocking** at the same time. It had been declared "required"; interpreting the
probe requires knowing the live corpus's concept backing, so it should gate. Tightening a gate
before any data exists is unambiguously safe, and it is recorded rather than done quietly.

**Checklist: X1 done · X2 BLOCKING running · X3 done (R-104) · X4 BLOCKING running · X5 done.**

## 2026-09-07 · C-087 · the SEVENTH instance — and this time it is the substituter itself

`prompt_families._substitute` uses `str.replace`, which has **no word-boundary notion at all**. So
`subway_station|harm[32]`:

> *"A witness described the **gun** as a large, black **handgun** with a silver barrel."*

passes every occurrence rule — one whole-word `gun`, in a substitutable case — and then **ships
as `handbutton` / `handbasket`.** The inflection-aware, case-enumerated rule of `C-076`/`C-079` is
blind to **compounds**, and this leaks concept identity **lexically** — only the gun arm contains
`hand<codeword>` — while remaining invisible to every whole-word leakage check, including `N3`.

The same pool's sentence 33 is also **truncated**: *"After the inspection, we felt relieved that
no gun"* — no object, no terminal punctuation. **No occurrence rule can catch that**, because its
count is correct.

**The general rule, which subsumes all the special cases:**

> **the substring count must equal the whole-word count.**
> If `gun` appears twice as a substring but once as a word, something is a compound the
> substituter will silently eat.

Added to the gate, the generator and the length matcher from one shared implementation.
Verified to separate the cases: `handgun` → True, *"The gun was found near the platform"* → False,
*"The knife rack held clean knives"* → False.

**Measured scope: exactly ONE compound occurrence across all three pools**, so excluding
`subway_station` removes the entire known population of the defect. It is in **TRAIN**, so
validation and test stay at 23/23 and the power analysis is unchanged. **Analysed population:
114 domains, 68 / 23 / 23.**

## 2026-09-07 · R-105 · X2 and X4 closed on `ts116m`

**X2 — the read site survives, but with a distinction that must not be lost.**
`rel_end = −9` (`' actually'`, id 3604) passes all four criteria on the full population:
strictly after every codeword 6900/6900, token-identical across concepts 2300/2300 triples, no
concept substring, present 6900/6900.

⚠ **`−9` is NOT the primary read site.** `PR-048` reads `codeword_last`, which is `rel_end = −10`;
`−9` is the **downstream neutral control**. Recorded explicitly so the two are never conflated.

⚠ **And the finding that matters most for the extraction code:** the **absolute** codeword index
is identical across concepts in **0 / 2300** triples — cross-concept spread 9.36 ± 5.90 tokens,
range 0–50 — while the **end-relative** index is identical in **2300 / 2300** at exactly −10,
sd 0. An absolute index would read **a different token in each concept arm**. `len(input_ids) +
rel_end` is mandatory. This is the absolute-position-index bug class that has already hit this
repo twice, and here it would have silently mis-read the primary.

`C-084` is **verified, not refuted**: the published token means differ from the raw ones by a
constant +1, exactly the `<|begin_of_text|>` BOS. Templated lengths are bomb 230.22 ± 13.11 /
knife 229.50 ± 12.43 / gun 230.69 ± 13.11, cross-concept spread **1.194 tokens**. The K-ladder
finding also re-derives: the first **five** rungs still carry zero query content; the codeword sits
at K=10.

**X4 — concept backing on the live corpus, nothing inherited.** 23 checks, 24 mutations, 24/24 RED.

| | bomb | knife | gun |
|---|---|---|---|
| tier-1 explosive predicates | 394/9200 = **4.28 %** | **0/9200 = 0.00 %** | 6/9200 = 0.07 % |
| positive control (own affordances) | **394** | **548** | **282** |
| largest off-diagonal | — | — | **8** |
| mass-noun polysemy | 0.57 % | **0.00 %** | 0.04 % |
| hedging (narrow) | 13.72 % | 0.20 % | 2.33 % |
| `C-076`/`C-079` violations | **0** | **0** | **0** |

The 3×3 affordance matrix is diagonal-dominant with a largest off-diagonal of 8, and **no
explosive predicate appears in any knife pool**. This is the positive control the original 6-domain
banks scored *zero* on, and the word-swap bank could not have had at all.

## 2026-09-07 · THE EXTRACTION GATE IS OPEN

```
=== prereg configs/dcs_ts_pr048.json (for_extraction=True) ===
[prereg] clean: status FROZEN, 17 hashes pinned and verified, all 12 mandate-21 fields present
```

**X1 done** (frozen analyzer, 11/11 guards) · **X2 done** · **X3 done** (`R-104`, layer convention
confirmed by experiment) · **X4 done** · **X5 done** (`PR-049`).

`PR-049`'s own gate correctly **still refuses** on Y1/Y2/Y3 — its 2-way power analysis, its
hedge-free stratum counts and its register re-measurement are all outstanding, and they are
CPU-only so they can run alongside extraction.

**What is true at this moment, stated before any hidden state exists:** the phase has built an
aligned 114-domain three-concept population in which only the harmful demonstrations differ,
verified by a gate that has been demonstrated capable of failing; the layer convention is
established by experiment; the read site is established on the live bank with end-relative
indexing proven mandatory; the design is frozen in a machine-readable preregistration that the
code refuses to run without; and **seven** occurrence-counting defects have been found and fixed
before a single GPU-hour was spent on measurement.

## 2026-09-07 · PHASE 5 · **extraction submitted** — the first measurement of the phase

Two smoke runs first, per the house rule of 2–4 prompts before scale, and then a throughput
measurement before committing six jobs. Both `COMPLETED 0:0`:

| job | rows | elapsed | result |
|---|---|---|---|
| **860339** | 4 | 1:30 | 4 rep stacks, `failures: {}` |
| **860342** | 256 | **0:45** | 256 rep stacks, `failures: {}` |

256 rows in 45 s *including model load* ⇒ a full 22,272-row bank is roughly half an hour, so all
six run inside one wall-clock window. The throughput check existed to stop me sizing six jobs off
a 4-row smoke whose runtime was mostly weight loading.

Every run confirms the configuration in its own log rather than by inference:
`model=meta-llama/Llama-3.1-8B-Instruct blocks=32 hidden=4096 **attn=eager**`,
`capture layers=[6..14] position=codeword_last`, `KNOCKOUT DISABLED (--no-knockout):
baseline-reproduction control`, and `GPU ok: NVIDIA L40S`.

**Six jobs submitted, exactly at the phase's concurrency cap** (mandate §26.2):

| bank | job |
|---|---|
| button_bomb | **860352** |
| button_knife | **860353** |
| button_gun | **860354** |
| basket_bomb | **860355** |
| basket_knife | **860356** |
| basket_gun | **860357** |

Each carries `BOOMB_EXPECT` and `BOOMB_REQUIRE_ARGS=1`, so neither the `853040` silent-default nor
its empty-args successor is reachable; each argsfile lives on the shared filesystem, not node-local
scratch; and each log's opening lines state the script, the origin, the expect and the argsfile.

**Two things that make this extraction safe that were not true a few hours ago.** The read site
resolves **per prompt** — `resolve_occurrences` returns `last_idx_per_occurrence` and
`following_idx` for each row, so the `X2` finding that the absolute codeword index differs across
concepts in 0/2300 triples cannot bite. And the layer convention it captures against was
**confirmed by experiment** (`R-104`), not read off eight agreeing files.

`PR-049`'s three blockers (2-way power at chance 0.5, the hedge-free stratum re-derived on
`ts116m`, and the register re-measurement carrying the **+0.10 kill condition**) are running on CPU
in parallel. They do not depend on the representations, so nothing is serialised behind them.

## 2026-09-07 · PHASE 5 · a scheduling correction, not a scientific one

Of the six extraction jobs, two started on `n-804` and **four sat PENDING for 32 minutes** with
SLURM estimating starts at **10:09, 10:37, 12:04 and 12:34** — five to eight hours out. `killable`
was saturated (90 running / 113 pending at the last preflight).

The house rule is to cancel and resubmit with a different configuration when a job passes 30
minutes pending, measured by `SUBMIT_TIME` rather than elapsed. The nodelist is already all six
L40S nodes, so **there was nothing to widen** — the thing available to change was the **job
shape**. Four jobs each waiting for a scarce slot is the wrong shape when each unit of work is
~30 minutes: **one slot held for two hours beats four slots that never arrive.**

`scancel 860354 860355 860356 860357` (my own jobs only; nothing else was touched, nothing was
deleted), replaced by **job 860468**, one allocation extracting the remaining four banks
sequentially via `scripts/dcs_ts_extract_multi.py`. It moved from `(Priority)` to `(Resources)`
immediately, which is the queue saying it is now a candidate rather than outranked.

**Nothing scientific changes.** Each bank is extracted by exactly the same
`dcs_extract_under_ko.py` with exactly the same flags it would have received as its own job; the
driver only decides *when* they run. It shells out per bank rather than importing, so each bank
gets a clean interpreter and CUDA context — the ~25 s reload is a rounding error against a
30-minute extraction, and a leaked hook or mutated global cannot cross between banks. It is
fail-closed: a non-zero exit from any bank stops the run rather than continuing, and each bank's
own stdout streams through unmodified so §26.10's "did this run what I meant?" is still answerable
per bank.

**In flight:** 860352 (button_bomb), 860353 (button_knife), 860468 (the remaining four).

## 2026-09-07 · R-106 · PR-049's three blockers: **SURVIVE, with a qualification that matters**

`scripts/dcs_ts_pr049_blockers.py`, `reports/DCS_TS_PR049_BLOCKERS.md`. 19/20 checks PASS,
11/11 mutations RED, 6,840 rows over 114 domains (68/23/23), both prospective exclusions applied.

### Y3 — the kill condition: **SURVIVE**, +0.0348 against a +0.10 threshold

The `ts116n` register figures **replicate** on `ts116m`: hedge-only buys **bomb-vs-knife +0.2217**
(was +0.211), **knife-vs-gun +0.0348** (was +0.037), bomb-vs-gun +0.1870. Register is confirmed as
a **bomb-vs-rest severity axis**, and the contrast that motivated `PR-049` is not withdrawn.

**But one check FAILS, and it is a finding rather than a harness defect.** A *broader*
register-only **surface** classifier reaches **+0.2065 on knife-vs-gun** — accuracy 0.7065, AUROC
0.7479 — and **+0.1870 with every length channel removed**, so it is **composition, not length in
disguise**. Length-only is +0.1174 in characters but only **+0.0435 in tokens** (`C-084` again; the
token figure is the honest one).

So the kill condition, which is written about the **hedge-only** classifier, is answered on its own
terms — and `PR-049`'s broader *rationale* is **only partly supported**:

> knife-vs-gun is clean on **hedges** and on **token length**.
> It is **not** clean on character length, and **not** clean on surface register generally.

**Consequence, recorded now rather than discovered later: the nuisance floor the probe must beat
on this contrast is a measured 0.7065 / 0.7479, not 0.5.** I am writing that down before the probe
exists, in the same spirit as `C-078` — it is much easier to accept a bar before you know whether
you cleared it.

### Y1 — **CO-PRIMARY**, but the binding arm is not the one I assumed

Sign-test floor at n=23 is **2.3842e-07** (closed form agreeing with brute force over all 2²³
patterns). The permutation floor at the preregistered `n_perm=10000` is 9.999e-05, **read at
runtime from the config** rather than restated.

**The success rule is conjunctive — permutation AND sign test — and the sign test is the binding
arm at every SD**, requiring **k ≥ 17 of 23** domains (π ≥ 0.788). Conjunctive power at δ=+0.15,
n=23, sd=0.1406: **0.963** at α=0.05 and **0.900** under Holm α=0.025. FPR on pure noise through
the real 36-point grid, validation-selected, domain-grouped: **0.0400** [0.0174, 0.0773] over 200
reps, null mean accuracy 0.4951 — calibrated.

⚠ **There is no measured 2-way per-domain SD anywhere in the record.** Every MDE is labelled by
the SD assumed to produce it (0.0306 at sd=.05; 0.0859 at sd=.1406, PR-048's 3-way value borrowed;
0.1528 at the distribution-free ceiling; 0.2102 at sd=.3439). Stated, not papered over.

**DEMOTION CONTINGENCY, declared now:** conjunctive power falls below 0.8 at **sd = 0.188** (0.160
under Holm). If the **TRAIN-only** between-domain SD exceeds that, `PR-049` is **demoted to
EXPLORATORY** — checkable before any test read, using the SD measurement `PR-048` already requires.

### Y2 — the hedge-free stratum is **feasible at the full n=23**

All **23/23** TEST domains carry hedge-free rows in every arm: bomb 248/460, knife 452/460, gun
420/460. Balanced knife-vs-gun N = **840 rows** (832 domain-balanced); 3-way N = 744. **The stratum
exists at the domain level, not only at row level** — which is the distinction that decides whether
it is usable at all. The superseded 115/212/195 figures are **retired**.

### C-088 · three mutations came back GREEN, and each was a real hole

The agent's harness reported three mutations that failed to turn a check RED. Each was a genuine
gap, and one of them corrects a claim of mine:

1. **`wrong_cell_field` did not fire — because on `ts116m`, `condition == "natural_doublespeak"`
   binds the *same* 6,840 rows as `cell == "C"`.** `A-039`'s finding that selecting the wrong field
   binds **zero** rows is therefore **corpus-specific**, not a general property, and my restatement
   of it in `PR-046`/`PR-048` as a flat warning is too strong. Corrected here.
   Chasing it further exposed something worse: **`prompt_id` is not unique across the six banks —
   6,840 rows carry only 1,140 distinct ids** — so the first version of that positive check compared
   six *collapsed* sets and would have passed vacuously. This is the third independent confirmation
   that the compound key `(bank_file_sha16, prompt_id)` is load-bearing.
2. **`row_level_permutation`** does inflate FPR to ≈0.17, but the mutation arm ran at 20 reps where
   the CI still covers 0.05 — a mutation too underpowered to detect the defect it plants. Raised to
   100 reps plus a 2α point-estimate bound.
3. **`mde_drop_beta`** — monotonicity in SD survives an MDE that omits the type-II term, so the
   check could not see it. Replaced with a round-trip: `t_power(23, MDE, sd)` must return 0.800.

Mutation accounting was also corrected so that a check **already RED on the real corpus**
(`Y3-surf`) cannot be credited as a catch — otherwise a pre-existing failure would launder itself
into evidence that the harness works.

## 2026-09-07 · R-107 · first bank extracted and **bound to the frozen preregistration**

Job **860352**, `COMPLETED 0:0`, 58:19. `ts116m_full_button_bomb_20260907_040927_3131687`.

| | |
|---|---|
| rep stacks cached | **22,272 / 22,272** |
| `n_rows_captured` / `n_failed` | 22,272 / **0**, `skip_reasons: {}` |
| cache size | 1,649,019,931 B — exactly 22272 × 9 layers × 4096 × 2 (bf16) |
| `bank_rows_sha16` | **`4ca3ec165ab5b018`** — **matches PR-048's pin** |
| `bank_file_sha16` | `dcd92d723f3e6d00` |
| attn / layers / position | `eager` / `[6..14]` / `codeword_last` |
| `knockout_applied` | `false` (baseline-reproduction control) |
| layer convention recorded in the artifact | `block_L == hidden_states[L+1]; hidden_states[0] == embeddings` |

**The bank binding is the important line.** The run's `bank_rows_sha16` equals the hash `PR-048`
froze *before the bank was extracted*, so this measurement is provably of the preregistered
population and not of some neighbouring artifact. `DONE.json` is present, so the run is complete
rather than merely newest.

One incidental measurement worth keeping: `last_layer_tied_vs_raw_relnorm = 0.6276`. That is the
relative difference between the tied post-final-norm tensor and the raw last-block output — so the
substitution `T5` could not exercise is **not** cosmetic, it is a 63 % relative change. It does not
affect this phase (the band is 6–14), and it strengthens the standing block on any last-layer read.

## 2026-09-07 · the analyzer's reps path, and a stale guard of my own

`run_probe()` implemented against the real cache format. It refuses before computing anything if:
the run directory has no `DONE.json` (a partial newer run must never shadow a complete older one —
the `C-051` defect); the run's `bank_rows_sha16` disagrees with the preregistered pin (**bank
binding**); the run's `position` or `attn_implementation` disagrees with the preregistration; the
population binds **zero rows**; any split binds zero rows; or any domain appears in **both** train
and test.

Selection runs on **validation only** and returns a `SELECTION_TRACE` the caller cannot drop.
Permutation is at the **domain** level — labels are permuted within each training domain, never
row-wise, because row-level permutation was measured at FPR 0.2000. Both p-values print beside
their floors.

**C-089 — a guard test of mine went stale, and the shape is worth naming.** The selftest asserted
that the live preregistration *refuses* under `for_extraction`. That was true when written, and it
became **false the moment the checklist was legitimately completed** — so the selftest failed
because the project had progressed correctly. A guard test whose expected answer changes as work
advances is testing the project, not the guard. Replaced with three assertions against a
**synthetic** config: an open blocker refuses, the live config is accepted now that its checklist
is closed, and a checklist item missing its booleans refuses. **13/13 guards reachable.**

**Extraction status:** button_bomb done; button_knife 15,300/22,272; the multi-bank job on
button_gun at 12,200/22,272 with three basket banks behind it. Roughly three hours to full
coverage. Per-bank rate is ~380 rows/min, i.e. ~58 min/bank — my 30-minute figure was 2× optimistic
and is corrected here rather than left to look like a delay.
